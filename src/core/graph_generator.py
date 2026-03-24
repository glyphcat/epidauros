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

import re
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

# v2プロンプトの読み込みを追加
from src.core.prompts.extract_scenario_graph import build_full_extraction_prompt
from src.models.character_archetypes import ALL_CHARACTER_ARCHETYPES
from src.models.scenario_structure import CharacterNode, ScenarioGraph
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

    def _build_archetypes_str(self) -> tuple[str, str]:
        """プロンプト用のアーキタイプ文字列を生成"""
        char_lines = [
            f"- **{arch.id}**: {arch.short_summary}"
            for arch in ALL_CHARACTER_ARCHETYPES
        ]
        sit_lines = [
            f"- **{sit.id}** ({sit.name_jp}): {sit.short_summary}"
            for sit in ALL_SITUATIONS_ARCHETYPES
        ]
        return "\n".join(char_lines), "\n".join(sit_lines)

    def generate(
        self, title: str, plot_text: str, cast_mapping: List[Dict[str, Any]]
    ) -> ScenarioGraph:
        """
        与えられた作品情報からグラフ構造を生成する。
        """
        # --- 1. 前処理：メンションマッピングとあらすじの置換 ---
        mention_mapping = {}
        isolated_casts = []
        processed_plot = plot_text
        active_mentions = []

        for i, cast in enumerate(cast_mapping):
            # $c{number} 形式に固定
            mention_id = f"$c{i+1}"
            role_name = cast.get("role", "Unknown")
            actor_name = cast.get("actor", "Unknown")

            # あらすじに役名が含まれるか確認（簡易的な文字列マッチ）
            if role_name != "Unknown" and role_name in processed_plot:
                processed_plot = processed_plot.replace(role_name, mention_id)
                mention_mapping[mention_id] = {
                    "role": role_name,
                    "actor": actor_name,
                    "original_cast": cast,
                }
                active_mentions.append(f"- {mention_id} (Actor: {actor_name})")
            else:
                isolated_casts.append(cast)

        actor_list_str = (
            "\n".join(active_mentions)
            if active_mentions
            else "No characters found in plot."
        )

        # --- 2. プロンプト生成 ---
        char_arch_str, sit_arch_str = self._build_archetypes_str()
        full_prompt = build_full_extraction_prompt(
            character_archetypes_str=char_arch_str,
            situation_archetypes_str=sit_arch_str,
            actor_list_str=actor_list_str,
            plot_text=processed_plot,
        )

        try:
            # --- 3. LLM呼び出し ---
            result = self.structured_llm.invoke(full_prompt)
            graph = (
                result
                if isinstance(result, ScenarioGraph)
                else ScenarioGraph.model_validate(result)
            )

            # --- 4. 後処理：メンションの復元と孤立ノードの結合 ---
            # 抽出されたノードのメンションを元の名前に復元
            for node in graph.nodes:
                mention = node.role_name
                if mention in mention_mapping:
                    node.role_name = mention_mapping[mention]["role"]
                    node.actor_name = mention_mapping[mention]["actor"]

            # 重複を避けるための次の連番IDを取得
            existing_ids = []
            for n in graph.nodes:
                match = re.search(r"\d+", n.node_id)
                if match:
                    existing_ids.append(int(match.group()))
            next_id_num = max(existing_ids) + 1 if existing_ids else 1

            # 孤立ノード（あらすじ未登場キャラ）をグラフに追加
            for cast in isolated_casts:
                isolated_node = CharacterNode(
                    node_id=f"char_{next_id_num:02d}",  # CharacterNodeのバリデータに合わせた形式
                    role_name=cast.get("role", "Unknown"),
                    actor_name=cast.get("actor", "Unknown"),
                    archetype_id="UNKNOWN",  # アーキタイプ定義に存在しない場合は適宜変更してください
                    description="Not explicitly mentioned in the plot summary.",
                )
                graph.nodes.append(isolated_node)
                next_id_num += 1

            return graph
        except Exception as e:
            print(f"Error during graph extraction for '{title}': {e}")
            raise e
