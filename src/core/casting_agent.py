import os
import logging
import datetime
from typing import List, Dict, Any, TypedDict
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from src.models.db_orm import Performance, Actor
from src.models.scenario_structure import ScenarioGraph

logger = logging.getLogger(__name__)

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

class AgentState(TypedDict):
    # Context
    work_title: str
    char_id: str
    char_role: str
    char_archetype: str
    char_description: str
    char_dynamics: str
    
    # Constraints & Intentions
    min_budget: float
    max_budget: float
    target_gender: int  # 0=Any, 1=Female, 2=Male, 3=Non-binary
    target_age_min: int # 0=Any
    target_age_max: int
    unexpected_casting: bool
    blockbuster_focus: bool
    
    # Internal agent tracking
    fetch_limit: int
    iteration: int
    
    # Results
    filtered_candidates: List[Dict[str, Any]]
    final_proposals: List[Dict[str, Any]]
    rationale: str

class CastingAgent:
    """
    Casting Agent that suggests actors based on scenario graphs and user constraints.
    Uses LangGraph for iterative reasoning involving Qdrant (Vector) and PostgreSQL (Relational).
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)
        
        builder.add_node("retrieve", self._retrieve_node)
        builder.add_node("observe", self._observe_node)
        builder.add_node("generate", self._generate_node)
        
        builder.add_edge(START, "retrieve")
        builder.add_edge("retrieve", "observe")
        builder.add_conditional_edges("observe", self._router, {"retrieve": "retrieve", "generate": "generate"})
        builder.add_edge("generate", END)
        
        return builder.compile()

    def _retrieve_node(self, state: AgentState) -> dict:
        """Qdrantから取得し、DBメタデータで後処理フィルターにかける"""
        text_to_embed = f"Role: {state['char_role']}\\nWork Title: {state['work_title']}\\nArchetype: {state['char_archetype']}\\nDescription: {state['char_description']}\\n{state['char_dynamics']}"
        
        vector = self.embeddings.embed_query(text_to_embed)
        search_res = self.qdrant.query_points(
            collection_name="performances",
            query=vector,
            limit=state["fetch_limit"]
        ).points
        
        valid_candidates = []
        seen_actors = set()
        
        for point in search_res:
            perf_id = point.payload.get("performance_id")
            perf = self.db.query(Performance).filter(Performance.id == perf_id).first()
            if not perf or not perf.actor:
                continue
                
            actor = perf.actor
            if actor.name in seen_actors:
                continue

            # Hard Constraint (Budget only - the ONLY true hard filter)
            actor_score = float(actor.current_guarantee_score) if actor.current_guarantee_score else 0.0
            if not (state["min_budget"] <= actor_score <= state["max_budget"]):
                continue
                
            # Soft Assessment: Demographic Match Score (0.0 ~ 1.0)
            # Gender: check affinity but never hard-exclude
            gender_score = 1.0
            tg = state.get("target_gender", 0)
            if tg != 0 and actor.gender is not None:
                if actor.gender == tg:
                    gender_score = 1.0       # perfect match
                elif actor.gender == 3 or tg == 3:
                    gender_score = 0.8       # non-binary: partial affinity
                else:
                    gender_score = 0.2       # mismatch: heavy penalty, NOT exclusion
            
            # Age: Buffer-based distance penalty
            age_score = 1.0
            age = None
            if actor.birth_date is not None:
                age = (datetime.date.today() - actor.birth_date).days // 365
                age_min = state.get("target_age_min", 0)
                age_max = state.get("target_age_max", 150)
                if age_min != 0:  # only apply if a target age was specified
                    # Allow a natural casting buffer: +10 above range, -5 below
                    buffered_min = max(0, age_min - 5)
                    buffered_max = age_max + 10
                    if buffered_min <= age <= buffered_max:
                        age_score = 1.0      # within buffer: no penalty
                    else:
                        gap = min(abs(age - buffered_min), abs(age - buffered_max))
                        age_score = max(0.1, 1.0 - (gap * 0.05))
            
            demographic_score = (gender_score + age_score) / 2.0

            # Soft Intent: Unexpectedness filter
            past_archetype = ""
            if state["unexpected_casting"]:
                if perf.work and perf.work.scenario_graph_data:
                    for n in perf.work.scenario_graph_data.get("nodes", []):
                        if n.get("actor_name") == actor.name or n.get("role_name") == perf.character_name:
                            past_archetype = n.get("archetype", "")
                            break
                if past_archetype == state["char_archetype"]:
                    continue
                    
            seen_actors.add(actor.name)
            
            sim_score = point.score
            succ_score = float(perf.success_score) if perf.success_score else 0.5
            
            valid_candidates.append({
                "actor_name": actor.name,
                "similarity": sim_score,
                "success_score": succ_score,
                "guarantee_score": actor_score,
                "demographic_score": demographic_score,
                "gender_score": gender_score,
                "age_score": age_score,
                "actor_gender": actor.gender,
                "actor_age": age,
                "past_role": perf.character_name,
                "past_work_title": perf.work.title,
                "past_archetype": past_archetype
            })
            
        return {"filtered_candidates": valid_candidates}


    def _observe_node(self, state: AgentState) -> dict:
        """Updates search parameters if candidates are scarce."""
        cands = state["filtered_candidates"]
        iteration = state["iteration"] + 1
        
        # 候補が枯渇している場合、まだループ限界に達していなければ再検索へ
        if len(cands) < 3 and iteration < 3:
            return {"iteration": iteration, "fetch_limit": state["fetch_limit"] + 50}
            
        # スコア計算: 類似度・興行スコアにDemographic Softスコアを乗算
        # Demographic mismatch reduces the overall score.
        w_sim = 0.2 if state["blockbuster_focus"] else 0.6
        w_succ = 0.7 if state["blockbuster_focus"] else 0.25
        w_demo = 0.1 if state["blockbuster_focus"] else 0.15
            
        for c in cands:
            c["final_score"] = (
                c["similarity"] * w_sim
                + c["success_score"] * w_succ
                + c.get("demographic_score", 1.0) * w_demo
            )
            
        cands.sort(key=lambda x: x["final_score"], reverse=True)
        return {"iteration": iteration, "final_proposals": cands[:3]}

    def _router(self, state: AgentState) -> str:
        """Routes to next phase or retry search."""
        if state.get("final_proposals") is not None and len(state["final_proposals"]) >= 0:
            return "generate"
        if state["iteration"] >= 3:
            return "generate"
        return "retrieve"

    def _generate_node(self, state: AgentState) -> dict:
        """Generates recommendation rationale using RAG."""
        if not state.get("final_proposals"):
            return {"rationale": "事前設定された予算（Guarantee Score）により、検索範囲内で適合する俳優が見つかりませんでした。制約を緩和して再度お試しください。"}
            
        cand_text = ""
        for idx, c in enumerate(state["final_proposals"]):
            cand_text += f"{idx+1}. {c['actor_name']} (過去作: '{c['past_work_title']}' の {c['past_role']})\\n"
            
        prompt = f'''あなたは独創的で論理的なハリウッドのキャスティングディレクターAIです。
以下のキャラクターとキャスティング候補データに基づき、なぜこの候補が配役として完璧なのかを推論し、2〜3文の完結な日本語で推薦理由を書き上げてください。

【キャラクター情報】
名前/役割: {state['char_role']}
アーキタイプ: {state['char_archetype']}
物語上のダイナミズム: {state['char_dynamics']}

【ユーザー意向】
意外性重視: {'はい' if state['unexpected_casting'] else 'いいえ'}
興行収入重視: {'はい' if state['blockbuster_focus'] else 'いいえ'}

【候補者トップ3（スコア上位）】
{cand_text}

出力ルール: 
- リスト形式ではなく、短いパラグラフで構造的にマッチしている理由を説明してください。
- 俳優Aと過去作Xに言及し、単なる演技の巧拙ではなく「過去のシチュエーション（動学）が物語の構造にピタリとハマるから」というプロ的な視座を必ず入れてください。
- 入力プロットが名作のリメイク設定を含んでいる場合は、元の役柄（例：コルレオーネの威厳）が、今回の俳優のどの資質と共鳴しているかを具体的に言語化してください。
- 実年齢や性別がキャラクターの設定と異なる場合：それが逆に「リアリティを超えた演技的化学反応」を生む理由を積極的に説明してください。
- 「意外性重視」がONの場合は、過去に似た役をやっていないのに選ばれたという抜擢感を出してください。
'''
        msg = self.llm.invoke([HumanMessage(content=prompt)])
        return {"rationale": msg.content}
        
    def suggest_casting(
        self, 
        graph: ScenarioGraph, 
        cast_constraints: List[Dict[str, Any]], 
        work_title: str,
        unexpected_casting: bool = False,
        blockbuster_focus: bool = False,
        target_guarantee_range: tuple = (0.0, 1.0)
    ) -> Dict[str, Dict[str, Any]]:
        """Returns casting proposals and rationales for each character."""
        results = {}
        target_casts = { c.get("id"): c for c in cast_constraints if c.get("suggest_casting", False) }
        if not target_casts:
            return results
            
        for node in graph.nodes:
            cast_info = None
            for cast in target_casts.values():
                if cast['role'] == node.role_name or cast['id'] == node.role_name:
                    cast_info = cast
                    break
                    
            if not cast_info:
                continue
                
            sources = [e.situation_id for e in graph.edges if e.source_node_id == node.node_id]
            targets = [e.situation_id for e in graph.edges if e.target_node_id == node.node_id]
            dynamics = f"Taking action (Source of): {', '.join(sources) if sources else 'None'}\\nReceiving action (Target of): {', '.join(targets) if targets else 'None'}"
            
            # --- Parse Target Constraints ---
            req_gender = 0
            g_str = cast_info.get("target_gender", "Any")
            if g_str == "Female": req_gender = 1
            elif g_str == "Male": req_gender = 2
            elif g_str == "Non-binary": req_gender = 3
            
            req_age_min = 0
            req_age_max = 150
            a_str = cast_info.get("target_age", "Any")
            if a_str == "Teen": req_age_min, req_age_max = 10, 19
            elif a_str == "20s": req_age_min, req_age_max = 20, 29
            elif a_str == "30s": req_age_min, req_age_max = 30, 39
            elif a_str == "40s": req_age_min, req_age_max = 40, 49
            elif a_str == "50s": req_age_min, req_age_max = 50, 59
            elif a_str == "60s+": req_age_min, req_age_max = 60, 150
            
            initial_state = {
                "work_title": work_title,
                "char_id": cast_info["id"],
                "char_role": cast_info["role"],
                "char_archetype": node.archetype_id,
                "char_description": node.description,
                "char_dynamics": dynamics,
                "min_budget": target_guarantee_range[0],
                "max_budget": target_guarantee_range[1],
                "target_gender": req_gender,
                "target_age_min": req_age_min,
                "target_age_max": req_age_max,
                "unexpected_casting": unexpected_casting,
                "blockbuster_focus": blockbuster_focus,
                "fetch_limit": 50,
                "iteration": 0,
                "filtered_candidates": [],
                "final_proposals": [],
                "rationale": ""
            }
            
            logger.info(f"Agent Loop Started for: {cast_info['role']}")
            final_state = self.graph.invoke(initial_state)
            
            results[f"{cast_info['id']} ({cast_info['role']})"] = {
                "candidates": final_state.get("final_proposals", []),
                "rationale": final_state.get("rationale", "")
            }
            
        return results
