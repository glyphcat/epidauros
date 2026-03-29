import json
import logging
import os
import time
from typing import Set

from dotenv import load_dotenv

from src.core.graph_generator import GraphGenerator

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INPUT_FILE = "dataset/final_dataset.json"
OUTPUT_FILE = "data/processed/structured_dataset.jsonl"
MAX_RETRIES = 5
BASE_DELAY_SEC = 2.0


def get_processed_ids(output_path: str) -> Set[str]:
    """既に処理済みのデータのIDを取得する。"""
    processed_ids = set()
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if "external_id" in data:
                        processed_ids.add(data["external_id"])
                except json.JSONDecodeError:
                    pass
    return processed_ids


def run_extraction(max_records: int = None):
    logger.info("Starting LLM extraction batch...")

    # 1. データの読み込み
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            datasets = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {INPUT_FILE}")
        return

    # 2. 処理済みIDの確認
    processed_ids = get_processed_ids(OUTPUT_FILE)
    logger.info(f"Loaded {len(datasets)} records. Already processed: {len(processed_ids)}.")

    # 出力先ディレクトリの確保
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # 3. モデルの初期化 (gpt-4o)
    extractor = GraphGenerator(model_name="gpt-4o", temperature=0.0)

    # 4. 未処理レコードの処理
    processed_count = 0
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f_out:
        for item in datasets:
            if max_records and processed_count >= max_records:
                logger.info(f"Reached max_records limit of {max_records}. Stopping.")
                break

            ext_id = item.get("external_id")
            if not ext_id or ext_id in processed_ids:
                continue

            title = item.get("title", "Unknown Title")
            logger.info(f"Processing: {title} (ID: {ext_id})")

            plot_text = item.get("plot_full", "")
            if not plot_text:
                logger.warning(f"No plot_full found for {title}. Skipping.")
                continue
                
            cast_mapping = item.get("cast_mapping", [])

            # リトライ処理
            success = False
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    # GraphGenerator.generate() を呼び出し構造化データを取得
                    graph_result = extractor.generate(
                        title=title, plot_text=plot_text, cast_mapping=cast_mapping
                    )

                    # 成果物を1つのJSON形式（dict）にまとめる
                    result_data = {
                        "external_id": ext_id,
                        "title": title,
                        "metadata": item.get("metadata", {}),
                        "setting_period": getattr(graph_result, "setting_period", "Unknown"),
                        "setting_location": getattr(graph_result, "setting_location", "Unknown"),
                        "scenario_graph_data": graph_result.model_dump(),
                        "original_cast_mapping": cast_mapping,
                    }

                    # JSONLとして1行追記
                    f_out.write(json.dumps(result_data, ensure_ascii=False) + "\n")
                    f_out.flush()
                    
                    success = True
                    logger.info(f"Successfully extracted structure for: {title}")
                    processed_count += 1
                    break

                except Exception as e:
                    logger.warning(f"Attempt {attempt} failed for '{title}': {e}")
                    if attempt < MAX_RETRIES:
                        sleep_time = BASE_DELAY_SEC * (2 ** (attempt - 1))
                        time.sleep(sleep_time)
                    else:
                        logger.error(f"Failed to process '{title}' after {MAX_RETRIES} attempts.")

            # APIのレート制限(RPM)を考慮して少し待機
            time.sleep(1.0)

    logger.info(f"Batch completed. Newly processed records: {processed_count}.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract structured scenario graph from LLM")
    parser.add_argument("--limit", type=int, default=None, help="最大処理件数（テスト用）")
    args = parser.parse_args()
    
    run_extraction(max_records=args.limit)
