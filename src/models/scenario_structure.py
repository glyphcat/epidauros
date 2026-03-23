import re
from typing import List

from pydantic import BaseModel, Field, field_validator


class CharacterNode(BaseModel):
    """
    登場人物（ノード）の構造定義
    """

    node_id: str = Field(
        ..., description="一意のノードID。形式は 'char_XX'（例: char_01, char_02）"
    )
    role_name: str = Field(
        ..., description="劇中の役名（例: ルーク・スカイウォーカー）"
    )
    actor_name: str = Field(
        ..., description="演じる俳優名。入力されたキャストリストと完全一致させること"
    )
    archetype_id: str = Field(
        ..., description="CharacterArchetypeのID（HERO, MENTOR, SHADOW等）"
    )
    description: str = Field(
        ...,
        description="この役柄がそのアーキタイプに選定された理由。あらすじに基づく簡潔な説明",
    )

    @field_validator("node_id")
    @classmethod
    def validate_node_id_format(cls, v: str) -> str:
        """
        LLMが 'c1' や '1' と出力しても 'char_01' に強制変換するバリデータ
        """
        if not re.match(r"^char_\d+$", v):
            digit_match = re.search(r"\d+", v)
            if digit_match:
                # 数字を抜き出して2桁ゼロ埋めに整形
                return f"char_{int(digit_match.group()):02d}"
            raise ValueError("node_id の形式が不正です。数字を含めてください。")
        return v


class RelationEdge(BaseModel):
    """
    キャラクター間の劇的状況（エッジ）の構造定義
    """

    source_node_id: str = Field(
        ..., description="関係の起点となるnode_id（例: char_01）"
    )
    target_node_id: str = Field(
        ..., description="関係の対象となるnode_id（例: char_02）"
    )
    situation_id: str = Field(
        ..., description="SituationArchetypeのID（SIT_01〜SIT_36）"
    )
    reason: str = Field(
        ...,
        description="この状況が発生している根拠となる具体的なエピソードや関係性の説明",
    )

    @field_validator("source_node_id", "target_node_id")
    @classmethod
    def validate_node_refs(cls, v: str) -> str:
        """エッジの参照先IDも形式を統一"""
        digit_match = re.search(r"\d+", v)
        if digit_match:
            return f"char_{int(digit_match.group()):02d}"
        return v


class ScenarioGraph(BaseModel):
    """
    シナリオ全体のグラフ構造
    """

    scenario_title: str = Field(..., description="作品タイトル")
    nodes: List[CharacterNode] = Field(
        ..., description="主要登場人物（ノード）のリスト"
    )
    edges: List[RelationEdge] = Field(
        ..., description="キャラクター間の劇的状況（エッジ）のリスト"
    )
