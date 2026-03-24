"""
graph_generator.py

description:
このモジュールは、自然言語で与えられたシナリオ情報について以下の処理を行う。

- 入力: あらすじ(text) + 配役(Actor/Roleペアのリスト)
- プロンプト作成：グラフ構造抽出のためのプロンプトを組み立てる。
- ノード同定: 配役リストの各人物を、8つの CharacterArchetype のいずれかに分類。
- エッジ抽出: 人物間の関係を、36の SituationArchetype のいずれかに分類。
- 出力: Pydanticでバリデーションされた、JSONB格納用の構造化データ。
"""

from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

from src.models.character_archetypes import ALL_CHARACTER_ARCHETYPES
from src.models.scenario_structure import ScenarioGraph
from src.models.situation_archetypes import ALL_SITUATIONS_ARCHETYPES


class GraphGenerator:
    """
    あらすじとキャスト情報から、物語のグラフ構造（ScenarioGraph）を抽出するクラス。
    """

    def __init__(self, model_name="gpt-4o", temperature=0.0):
        # OpenAIの初期化
        # structured_outputに対応したモデルを使用
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)

        # ScenarioGraphスキーマをLLMにバインドし、構造化出力を強制
        self.structured_llm = self.llm.with_structured_output(ScenarioGraph)

    def _build_archetype_definition_header(self) -> str:
        """
        プロンプトキャッシュ効率を最大化するための固定ヘッダーを構築する。
        1024トークン以上のボリュームを確保し、キャラクターとシチュエーションの定義を含める。
        """
        lines = [
            "# SCENARIO ANALYSIS FRAMEWORK: ARCHETYPE DEFINITIONS",
            "This framework uses Joseph Campbell's and Christopher Vogler's Hero's Journey archetypes ",
            "combined with Georges Polti's 36 Dramatic Situations to analyze narrative structures.",
            "The following definitions are fixed and must be used as the objective criteria for extraction.",
            "\n",
        ]

        # 1. キャラクターアーキタイプの定義（アーキタイプ特定精度向上のため推奨シチュエーションを追加）
        lines.append("## Part 1: Character Archetype Definitions")
        for arch in ALL_CHARACTER_ARCHETYPES:
            # related_dramatic_situations (例: [10, 22]) を SIT_10, SIT_22 の形式に変換
            related_sits = ", ".join(
                [f"SIT_{str(s).zfill(2)}" for s in arch.related_dramatic_situations]
            )
            lines.append(f"- **{arch.id}**: {arch.short_summary}")
            lines.append(f"  - Primary Situations: {related_sits}")

        lines.append("\n")

        # 2. シチュエーションアーキタイプの定義
        lines.append("## Part 2: Dramatic Situation Definitions")
        for sit in ALL_SITUATIONS_ARCHETYPES:
            # ID, 日本語名, ショートサマリーをセットで渡すことで抽出精度を高める
            lines.append(f"- **{sit.id}** ({sit.name_jp}): {sit.short_summary}")

        # これらを結合した文字列が1024トークンを超えている場合、
        # 次回以降のリクエストでこの部分はキャッシュされ、料金と速度に貢献します。
        return "\n".join(lines)

    def _generate_extraction_prompt(self, plot_text: str, actor_list_str: str) -> str:
        """
        最終的な抽出プロンプトを組み立てる。
        キャッシュ効率のため、[固定ヘッダー] -> [固定指示] -> [動的データ] の順序を厳守する。
        """
        # 冒頭に固定定義（キャッシュ対象）を配置
        header = self._build_archetype_definition_header()

        # 抽出指示
        # キャラクターのPrimary Situationsを参考にしつつ、事実を優先するようガードレールを設置
        instruction = (
            "\n\n## Extraction Instructions\n"
            "Analyze the provided movie plot and cast information based on the definitions above.\n"

            # --- 追加：ソースへの忠実性と孤立ノードの制約 ---
            "### [CRITICAL RULE: SOURCE FIDELITY]\n"
            "1. ONLY extract relationships and edges that are **explicitly described** in the provided 'Movie Plot'.\n"
            "2. If a character in the 'Cast List' does NOT appear or has no direct interaction described in the Plot, they must remain as an **isolated node** (no edges connected to/from them).\n"
            "3. DO NOT use external knowledge or general fame of the movie to 'fill in' missing interactions. If it's not in the text, it doesn't exist for this graph.\n\n"

            # --- 既存の指示を整理・統合 ---
            "### [Analysis Steps]\n"
            "1. Identify the most fitting CharacterArchetype for each actor from the Cast List.\n"
            "2. Identify the SituationArchetypes that represent the relationships or key events between characters.\n"
            "   * Important Guideline: Refer to the 'Primary Situations' listed under each archetype as likely candidates, but the specific actions in the Plot ALWAYS take precedence.\n"
            "3. For the 'reason' field in the edges, explicitly state the factual evidence from the plot that justifies the selected SituationArchetype.\n"
            "4. Output the result strictly in the specified JSON format matching the ScenarioGraph schema."
        )

        # 動的部分（キャストリストとプロット）は必ず最後に配置
        # これにより、上記までのヘッダーと指示がキャッシュヒットの対象になります。
        data_section = (
            f"\n\n## Input Data\n"
            f"### Cast List\n{actor_list_str}\n\n"
            f"### Movie Plot to Analyze\n{plot_text}"
        )

        return header + instruction + data_section

    def generate(
        self, title: str, plot_text: str, cast_mapping: List[Dict[str, Any]]
    ) -> ScenarioGraph:
        """
        与えられた作品情報からグラフ構造を生成する。
        """
        # プロンプト用にキャストリストを整形
        actor_list_str = "\n".join(
            [
                f"- Actor: {c['actor']}, Role: {c.get('role', 'Unknown')}"
                for c in cast_mapping
            ]
        )

        # 固定ヘッダーを含むフルプロンプトを生成
        # PromptTemplateを使わず直接文字列を組み立てることでキャッシュ順序を制御
        full_prompt = self._generate_extraction_prompt(plot_text, actor_list_str)

        try:
            # 構造化出力LLMを直接呼び出し
            # これにより、PromptTemplateの変数埋め込みによる順序破綻を防ぎます
            result = self.structured_llm.invoke(full_prompt)

            if isinstance(result, ScenarioGraph):
                return result
            return ScenarioGraph.model_validate(result)
        except Exception as e:
            print(f"Error during graph extraction for '{title}': {e}")
            raise e
