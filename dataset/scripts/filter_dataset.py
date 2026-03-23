import json
import sys
from pathlib import Path

# --- パス設定 ---
SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = SCRIPT_DIR.parent
INPUT_FILE = DATASET_DIR / "enhanced_dataset.json"
OUTPUT_FILE = DATASET_DIR / "final_dataset.json"


def is_valid_movie(movie: dict) -> bool:
    """映画データが品質基準（特徴量として使えるか）を満たしているか判定する"""

    # 1. あらすじの長さチェック（最低500文字）
    plot = movie.get("plot_full", "")
    if len(plot) < 500:
        return False

    # 2. キャスト情報の有無チェック
    cast = movie.get("cast_mapping", [])
    if not cast:
        return False

    # 3. 興行収入の有無チェック（特徴量として必須）
    box_office = movie.get("metadata", {}).get("box_office")
    if box_office is None or box_office <= 0:
        return False

    return True


def main():
    if not INPUT_FILE.exists():
        print(f"エラー: 入力ファイルが見つかりません: {INPUT_FILE}")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        enhanced_data = json.load(f)

    print(f"全 {len(enhanced_data)} 件のフィルタリングを開始します...\n")

    final_data = []
    dropped_count = 0

    for movie in enhanced_data:
        if is_valid_movie(movie):
            # 完全に品質基準を満たしたデータは low_quality_flag を外す（またはFalse確定）
            movie["low_quality_flag"] = False
            final_data.append(movie)
        else:
            dropped_count += 1

    # 結果の保存
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print("=" * 40)
    print("フィルタリング処理が完了しました。")
    print(f"入力データ件数: {len(enhanced_data)} 件")
    print(f"除外データ件数: {dropped_count} 件")
    print(f"★ 最終出力件数: {len(final_data)} 件")
    print(f"出力先: {OUTPUT_FILE}")
    print("=" * 40)


if __name__ == "__main__":
    main()
