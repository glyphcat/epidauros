import json
import logging
import os
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func
from pydantic import ValidationError

from src.core.database import SessionLocal
from src.models.db_orm import Work, Actor, Performance
from src.models.etl_schemas import ExtractedRecordSchema

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INPUT_FILE = "data/processed/structured_dataset.jsonl"

def load_data(db: Session, limit: int = None, dry_run: bool = False):
    logger.info("Starting Postgres ETL...")
    
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file {INPUT_FILE} not found.")
        return

    processed_count = 0
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if limit and processed_count >= limit:
                logger.info(f"Reached limit of {limit} records.")
                break
                
            if not line.strip():
                continue
            
            try:
                data_dict = json.loads(line)
                # Pydanticバリデーション
                record = ExtractedRecordSchema(**data_dict)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Validation error on line {line_num}: {e}")
                continue

            # --- 1. Work Upsert ---
            director_str = ", ".join(record.metadata.directors) if record.metadata and record.metadata.directors else None
            genre_str = ", ".join(record.metadata.genres) if record.metadata and record.metadata.genres else None
            box_office_val = record.metadata.box_office if record.metadata else None
            release_year_val = record.metadata.year if record.metadata else None

            # Works -> external_id
            work_stmt = insert(Work).values(
                title=record.title,
                external_id=record.external_id,
                release_year=release_year_val,
                plot_full=record.plot_full,
                director=director_str,
                genre=genre_str,
                box_office=box_office_val,
                setting_period=record.setting_period,
                setting_location=record.setting_location,
                scenario_graph_data=record.scenario_graph_data.model_dump()
            )
            # Update on conflict
            work_stmt = work_stmt.on_conflict_do_update(
                index_elements=['external_id'],
                set_={
                    'title': work_stmt.excluded.title,
                    'release_year': work_stmt.excluded.release_year,
                    'plot_full': work_stmt.excluded.plot_full,
                    'director': work_stmt.excluded.director,
                    'genre': work_stmt.excluded.genre,
                    'box_office': work_stmt.excluded.box_office,
                    'setting_period': work_stmt.excluded.setting_period,
                    'setting_location': work_stmt.excluded.setting_location,
                    'scenario_graph_data': work_stmt.excluded.scenario_graph_data,
                    'updated_at': func.now()
                }
            ).returning(Work.id)
            
            result = db.execute(work_stmt)
            inserted_work_id = result.scalar()
            
            # --- 2. Actors & Performances Upsert ---
            for cast_data in record.original_cast_mapping:
                # 2.A Actor Upsert
                actor_stmt = insert(Actor).values(
                    name=cast_data.actor,
                    external_id=cast_data.external_id,
                    gender=cast_data.gender,
                    birth_date=cast_data.birth_date,
                    current_guarantee_score=0.0 # Will be updated in Phase 3
                )
                actor_stmt = actor_stmt.on_conflict_do_update(
                    index_elements=['external_id'],
                    set_={
                        'name': actor_stmt.excluded.name,
                        'gender': actor_stmt.excluded.gender,
                        'birth_date': actor_stmt.excluded.birth_date,
                        'updated_at': func.now()
                    }
                ).returning(Actor.id)
                
                actor_result = db.execute(actor_stmt)
                inserted_actor_id = actor_result.scalar()
                
                # 2.B Extract Situation IDs based on Source/Target logic
                source_situations = []
                target_situations = []
                
                # 役名を元に graph のノードIDを探す
                node_id = None
                for node in record.scenario_graph_data.nodes:
                    if node['actor_name'] == cast_data.actor or node['role_name'] == cast_data.role:
                        node_id = node['node_id']
                        break
                        
                if node_id:
                    for edge in record.scenario_graph_data.edges:
                        if edge['source_node_id'] == node_id:
                            source_situations.append(edge['situation_id'])
                        if edge['target_node_id'] == node_id:
                            target_situations.append(edge['situation_id'])
                            
                # 重複排除
                source_situations = list(set(source_situations))
                target_situations = list(set(target_situations))
                
                # 2.C Performance Upsert
                # N/A などのバリデーション（テーブル制約への対応）
                g_rank = cast_data.guarantee_rank
                if g_rank not in ('S', 'A', 'B', 'C', 'N/A'):
                    g_rank = 'N/A'
                    
                perf_stmt = insert(Performance).values(
                    work_id=inserted_work_id,
                    actor_id=inserted_actor_id,
                    character_name=cast_data.role,
                    expected_guarantee_rank=g_rank,
                    source_situation_ids=source_situations,
                    target_situation_ids=target_situations
                )
                perf_stmt = perf_stmt.on_conflict_do_update(
                    index_elements=['work_id', 'actor_id', 'character_name'],
                    set_={
                        'expected_guarantee_rank': perf_stmt.excluded.expected_guarantee_rank,
                        'source_situation_ids': perf_stmt.excluded.source_situation_ids,
                        'target_situation_ids': perf_stmt.excluded.target_situation_ids,
                        'updated_at': func.now()
                    }
                )
                db.execute(perf_stmt)
            
            if dry_run:
                db.rollback()
                processed_count += 1
                logger.info(f"[DRY-RUN] Record processed and rolled back: {record.title}")
            else:
                try:
                    db.commit()
                    processed_count += 1
                    if processed_count % 100 == 0:
                        logger.info(f"Processed {processed_count} records")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error committing record {record.title}: {e}")

    mode_str = " (DRY-RUN)" if dry_run else ""
    logger.info(f"ETL completed. Successfully processed {processed_count} records{mode_str}.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load structured data into Postgres")
    parser.add_argument("--limit", type=int, default=None, help="最大処理件数（テスト用）")
    parser.add_argument("--dry-run", action="store_true", help="DBを更新せずにロールバックする")
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        load_data(db, limit=args.limit, dry_run=args.dry_run)
    finally:
        db.close()
