"""
Graph Generator Module
Extracts character nodes and dramatic situation edges from natural language plot summaries.
"""

import re
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

# v2プロンプトの読み込みを追加
from src.core.prompts.extract_scenario_graph import build_full_extraction_prompt
from src.models.character_archetypes import (
    ALL_CHARACTER_ARCHETYPES,
    NOT_MENTIONED_ARCHETYPE_ID,
)
from src.models.scenario_structure import CharacterNode, ScenarioGraph
from src.models.situation_archetypes import ALL_SITUATIONS_ARCHETYPES


class GraphGenerator:
    """
    Extracts a ScenarioGraph from plot summaries and cast information using LLM structured output.
    """

    def __init__(self, model_name="gpt-4o", temperature=0.0):
        # OpenAIの初期化
        # structured_outputに対応したモデルを使用
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)

        # ScenarioGraphスキーマをLLMにバインドし、構造化出力を強制
        self.structured_llm = self.llm.with_structured_output(ScenarioGraph)

    def _build_archetypes_str(self) -> tuple[str, str]:
        """Generates archetype description strings for the prompt."""
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
        self, title: str, plot_text: str, cast_mapping: List[Dict[str, Any]], pre_mentioned: bool = False
    ) -> ScenarioGraph:
        """
        Generates a graph structure from the given plot and cast mapping.
        If pre_mentioned is True, the plot_text is assumed to contain mention IDs like $c1.
        """
        # --- 1. 前処理：メンションマッピングとあらすじの置換 ---
        mention_mapping = {}
        isolated_casts = []
        processed_plot = plot_text
        active_mentions = []

        for i, cast in enumerate(cast_mapping):
            mention_id = cast.get("id", f"$c{i+1}")
            role_name = cast.get("role", "Unknown")
            actor_name = cast.get("actor", "Unknown")

            if pre_mentioned:
                # UIから直接 $c1 などが入れられている場合
                if mention_id in processed_plot:
                    mention_mapping[mention_id] = {
                        "role": role_name,
                        "actor": actor_name,
                        "original_cast": cast,
                    }
                    active_mentions.append(f"- {mention_id} (Role: {role_name}, Actor: {actor_name})")
                else:
                    isolated_casts.append(cast)
            else:
                # 従来の自然言語置換方式
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
            extracted_roles = set()
            for node in graph.nodes:
                mention = node.role_name
                if mention in mention_mapping:
                    node.role_name = mention_mapping[mention]["role"]
                    node.actor_name = mention_mapping[mention]["actor"]
                    extracted_roles.add(node.role_name)

            # node_idの連番管理
            # 重複を避けるための次の連番IDを取得
            existing_ids = []
            for n in graph.nodes:
                match = re.search(r"\d+", n.node_id)
                if match:
                    existing_ids.append(int(match.group()))
            next_id_num = max(existing_ids) + 1 if existing_ids else 1

            # 孤立ノード（あらすじ未登場キャラ）をグラフに追加
            for cast in cast_mapping:
                role = cast.get("role", "Unknown")
                if role not in extracted_roles:
                    isolated_node = CharacterNode(
                        node_id=f"char_{next_id_num:02d}",
                        role_name=role,
                        actor_name=cast.get("actor", "Unknown"),
                        archetype_id=NOT_MENTIONED_ARCHETYPE_ID,
                        description="Character present in cast list but not mentioned in the analyzed plot summary.",
                    )
                    graph.nodes.append(isolated_node)
                    next_id_num += 1

            return graph
        except Exception as e:
            print(f"Error during graph extraction for '{title}': {e}")
            raise e
