import logging
from sqlalchemy import func
from src.core.database import SessionLocal
from src.models.db_orm import Work, Actor, Performance

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Constants for Score calculations
RANK_MULTIPLIER = {
    'S': 1.0,
    'A': 0.8,
    'B': 0.4,
    'C': 0.1,
    'N/A': 0.2
}
RANK_POINTS = {
    'S': 1.0,
    'A': 0.75,
    'B': 0.40,
    'C': 0.10,
    'N/A': 0.20
}
# Weights for up to 5 most recent works
WEIGHTS = [1.0, 0.8, 0.6, 0.4, 0.2]


def calculate_scores(db):
    logger.info("Starting scoring calculation...")
    
    # --- 1. Calc Decade Box Office Baselines ---
    works = db.query(Work).all()
    decade_box_office = {}
    
    for w in works:
        if w.release_year and w.box_office:
            decade = (w.release_year // 10) * 10
            if decade not in decade_box_office:
                decade_box_office[decade] = []
            decade_box_office[decade].append(float(w.box_office))
            
    decade_baselines = {}
    for decade, box_offices in decade_box_office.items():
        if not box_offices:
            continue
        max_box_office = max(box_offices)
        decade_baselines[decade] = max_box_office
        
    logger.info(f"Calculated baselines for {len(decade_baselines)} decades.")

    # --- 2. Update Performance success_score ---
    performances = db.query(Performance).all()
    for p in performances:
        work = p.work
        decade = (work.release_year // 10) * 10 if work.release_year else -1
        
        base_score = 0.5  # default/median baseline
        if work.box_office and decade in decade_baselines and decade_baselines[decade] > 0:
            # 正規化: Maxの半分を平均的ヒットと考え 0.5~1.0 にスケーリング
            ratio = float(work.box_office) / (decade_baselines[decade] * 0.5)
            base_score = min(1.0, ratio) * 0.5 + 0.5
            
        rank = p.expected_guarantee_rank
        rank_weight = RANK_MULTIPLIER.get(rank, 0.2)
        
        success_score = base_score * rank_weight
        p.success_score = round(success_score, 5)
        
    db.commit()
    logger.info(f"Updated success_score for {len(performances)} performances.")

    # --- 3. Update Actor current_guarantee_score ---
    actors = db.query(Actor).all()
    for actor in actors:
        # Get actor performances ordered by work release_year desc (most recent first)
        actor_perfs = (
            db.query(Performance)
            .join(Work)
            .filter(Performance.actor_id == actor.id)
            .order_by(Work.release_year.desc().nullslast())
            .limit(5)
            .all()
        )
        
        if not actor_perfs:
            actor.current_guarantee_score = 0.0
            continue
            
        total_score = 0.0
        total_weight = 0.0
        
        for i, perf in enumerate(actor_perfs):
            weight = WEIGHTS[i] if i < len(WEIGHTS) else 0.0
            point = RANK_POINTS.get(perf.expected_guarantee_rank, 20)
            total_score += point * weight
            total_weight += weight
            
        if total_weight > 0:
            actor.current_guarantee_score = round((total_score / total_weight), 5)
        else:
            actor.current_guarantee_score = 0.0
            
    db.commit()
    logger.info(f"Updated current_guarantee_score for {len(actors)} actors.")
    
if __name__ == "__main__":
    db = SessionLocal()
    try:
        calculate_scores(db)
    finally:
        db.close()
