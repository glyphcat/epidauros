import os
import uuid
import logging
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from langchain_openai import OpenAIEmbeddings

from src.core.database import SessionLocal
from src.models.db_orm import Work, Performance

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

# Initialize Embeddings model
embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

def embed_data(db: Session, limit: int = None):
    logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # --- 1. Process Works (作品のベクトル化) ---
    works = db.query(Work).all()
    if limit:
        works = works[:limit]
        
    logger.info(f"Embedding {len(works)} works...")
    
    for work in works:
        if not work.scenario_graph_data:
            continue
            
        nodes_desc = "; ".join([f"{n.get('role_name', n.get('actor_name'))} ({n.get('archetype', 'Unknown')})" for n in work.scenario_graph_data.get('nodes', [])])
        edges_desc = "; ".join([f"{e.get('source_node_id')} -> {e.get('target_node_id')} [{e.get('situation_id', 'Unknown')}] reason: {e.get('reason', '')}" for e in work.scenario_graph_data.get('edges', [])])
        
        # 意味を捉えやすいようにシリアライズしたテキスト
        text_to_embed = f"""Title: {work.title}
Period: {work.setting_period}
Location: {work.setting_location}
Genre: {work.genre}
Characters: {nodes_desc}
Plot Dynamics: {edges_desc}
Full Plot Preview: {work.plot_full[:500]}..."""
        
        # UUIDがなければ新規発行（既にあれば更新）
        if not work.plot_embedding_id:
            work.plot_embedding_id = str(uuid.uuid4())
            
        vector = embeddings_model.embed_query(text_to_embed)
        
        qdrant.upsert(
            collection_name="works",
            points=[
                PointStruct(
                    id=str(work.plot_embedding_id),
                    vector=vector,
                    payload={
                        "work_id": str(work.id),
                        "title": work.title,
                        "release_year": work.release_year,
                        "genre": work.genre
                    }
                )
            ]
        )
        
    db.commit()
    logger.info("Finished embedding works.")

    # --- 2. Process Performances (役柄のベクトル化) ---
    performances = db.query(Performance).all()
    if limit:
        performances = performances[:limit * 10]  # rough limit scaling
        
    logger.info(f"Embedding {len(performances)} performances...")
    
    for perf in performances:
        if not perf.work.scenario_graph_data:
            continue
            
        # シナリオグラフからこの役柄の性格（Archetype, Description）を抜き出す
        char_desc = ""
        archetype = ""
        for n in perf.work.scenario_graph_data.get('nodes', []):
            if n.get('actor_name') == perf.actor.name or n.get('role_name') == perf.character_name:
                char_desc = n.get('description', '')
                archetype = n.get('archetype', '')
                break
                
        sources = ", ".join(perf.source_situation_ids) if perf.source_situation_ids else "None"
        targets = ", ".join(perf.target_situation_ids) if perf.target_situation_ids else "None"
        
        text_to_embed = f"""Role: {perf.character_name}
Work Title: {perf.work.title}
Archetype: {archetype}
Description: {char_desc}
Taking action (Source of): {sources}
Receiving action (Target of): {targets}"""

        if not perf.character_vector_id:
            perf.character_vector_id = str(uuid.uuid4())
            
        vector = embeddings_model.embed_query(text_to_embed)
        
        qdrant.upsert(
            collection_name="performances",
            points=[
                PointStruct(
                    id=str(perf.character_vector_id),
                    vector=vector,
                    payload={
                        "performance_id": str(perf.id),
                        "work_id": str(perf.work_id),
                        "actor_id": str(perf.actor_id),
                        "actor_name": perf.actor.name,
                        "character_name": perf.character_name,
                        "success_score": float(perf.success_score) if perf.success_score else 0.0
                    }
                )
            ]
        )

    db.commit()
    logger.info("Finished embedding performances.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        embed_data(db, limit=args.limit)
    finally:
        db.close()
