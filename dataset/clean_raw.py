import json
from pathlib import Path

try:
    fp = Path(__file__).resolve().parent / "raw_dataset.json"
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)

    # タイトル（またはWikidata URIなど）をキーにして重複を排除
    unique_data = {item["title"]: item for item in data}.values()

    op = Path(__file__).resolve().parent / "cleaned_dataset.json"
    with open(op, "w", encoding="utf-8") as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=2)

    print(f"元データ: {len(data)}件 -> 重複排除後: {len(unique_data)}件")
except Exception as e:
    print(f"重複除去に失敗しました（Error: {e}）")

# 元データ: 2149件 -> 重複排除後: 1187件
