import json
import logging
import os
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TMDB_READ_TOKEN = os.getenv("TMDB_READ_TOKEN")
HEADERS = {"accept": "application/json", "Authorization": f"Bearer {TMDB_READ_TOKEN}"}
STRUCTURED_FILE = "data/processed/structured_dataset.jsonl"
TEMP_FILE = "data/processed/structured_dataset_temp.jsonl"

def fetch_person_data(actor_id_str):
    if not actor_id_str or not actor_id_str.startswith("tmdb_"):
        return actor_id_str, None
        
    person_id = actor_id_str.replace("tmdb_", "")
    url = f"https://api.themoviedb.org/3/person/{person_id}?language=en-US"
    for _ in range(3):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return actor_id_str, {"gender": data.get("gender"), "birth_date": data.get("birthday")}
            elif res.status_code == 429:
                time.sleep(1)
            else:
                break
        except Exception:
            time.sleep(1)
    return actor_id_str, None

def main():
    logger.info("Starting high-speed demographics patch process via TMDB API...")

    if not os.path.exists(STRUCTURED_FILE):
        logger.error(f"Structured dataset not found: {STRUCTURED_FILE}")
        return

    # Extract all unique actor IDs from the JSONL
    actor_ids = set()
    records = []
    with open(STRUCTURED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            records.append(record)
            for cast in record.get("original_cast_mapping", []):
                ext_id = cast.get("external_id")
                if ext_id and ext_id.startswith("tmdb_"):
                    # 性別がまだ埋まっていないものだけ対象にする
                    if "gender" not in cast or cast["gender"] is None:
                        actor_ids.add(ext_id)

    logger.info(f"Identified {len(actor_ids)} unique actors needing demographic data.")
    
    actor_cache = {}
    if actor_ids:
        # Fetch Actor Data concurrently (max 20 workers for TMDB limits)
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_id = {executor.submit(fetch_person_data, aid): aid for aid in actor_ids}
            completed = 0
            for future in as_completed(future_to_id):
                aid, data = future.result()
                if data:
                    actor_cache[aid] = data
                completed += 1
                if completed % 100 == 0:
                    logger.info(f"Fetched {completed}/{len(actor_ids)} actors...")
                    
    # Patch the records and write out
    patched_count = 0
    with open(TEMP_FILE, "w", encoding="utf-8") as f_out:
        for record in records:
            updated = False
            for cast in record.get("original_cast_mapping", []):
                ext_id = cast.get("external_id")
                if ext_id in actor_cache:
                    pdata = actor_cache[ext_id]
                    cast["gender"] = pdata["gender"]
                    cast["birth_date"] = pdata["birth_date"]
                    updated = True
            
            if updated: patched_count += 1
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

    os.replace(TEMP_FILE, STRUCTURED_FILE)
    logger.info(f"Successfully patched {patched_count} movies with demographics.")

if __name__ == "__main__":
    main()
