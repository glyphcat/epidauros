import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# --- 設定 ---
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

TMDB_READ_TOKEN = os.getenv("TMDB_READ_TOKEN")
if not TMDB_READ_TOKEN:
    print("エラー: 環境変数 'TMDB_READ_TOKEN' が設定されていません。")
    sys.exit(1)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {"accept": "application/json", "Authorization": f"Bearer {TMDB_READ_TOKEN}"}


SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = SCRIPT_DIR.parent
INPUT_FILE = DATASET_DIR / "raw_dataset.json"
OUTPUT_FILE = DATASET_DIR / "enhanced_dataset.json"


def get_rank(order: int) -> str:
    """TMDBのクレジット順（order）からギャランティランクを判定"""
    if order in [0, 1]:
        return "A"
    elif order in [2, 3, 4]:
        return "B"
    else:
        return "C"


def search_tmdb_movie(title: str, year: int) -> int | None:
    """映画タイトルと公開年からTMDBの映画IDを取得"""
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {"query": title, "primary_release_year": year, "language": "en-US"}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            return results[0]["id"]
    return None


def get_tmdb_details_and_credits(movie_id: int) -> dict:
    """TMDBから映画の詳細（興行収入やあらすじ）とキャストを取得"""
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {"append_to_response": "credits", "language": "en-US"}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    return {}


def main():
    if not INPUT_FILE.exists():
        print(f"エラー: 入力ファイルが見つかりません: {INPUT_FILE}")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"全 {len(raw_data)} 件のエンハンスとクリーニングを開始します...\n")

    enhanced_data = []
    skipped_tmdb_not_found = 0
    skipped_low_quality = 0

    for i, movie in enumerate(raw_data):
        title = movie.get("title", "")
        year = movie.get("metadata", {}).get("year")

        print(f"[{i+1}/{len(raw_data)}] 処理中: {title} ({year})", end=" ... ")

        # 1. TMDBで映画を検索
        tmdb_id = search_tmdb_movie(title, year)
        if not tmdb_id:
            print("スキップ (TMDBで特定不可)")
            skipped_tmdb_not_found += 1
            time.sleep(0.1)  # APIレートリミット配慮
            continue

        # TMDBのIDをexternal_id として追加
        movie["external_id"] = f"tmdb_{tmdb_id}"

        # 2. TMDBから詳細情報とキャストを取得
        tmdb_data = get_tmdb_details_and_credits(tmdb_id)
        if not tmdb_data:
            print("スキップ (詳細取得失敗)")
            skipped_tmdb_not_found += 1
            time.sleep(0.1)
            continue

        # --- エンハンス処理 ---
        # A. 興行収入の補完
        current_revenue = movie.get("metadata", {}).get("box_office")
        if not current_revenue or current_revenue == 0:
            tmdb_revenue = tmdb_data.get("revenue", 0)
            if tmdb_revenue > 0:
                movie["metadata"]["box_office"] = tmdb_revenue

        # B. あらすじの補完（Wikipediaが500文字未満で、TMDBにOverviewがある場合、末尾に追記）
        current_plot = movie.get("plot_full", "")
        if len(current_plot) < 500:
            tmdb_overview = tmdb_data.get("overview", "")
            if tmdb_overview:
                movie["plot_full"] = f"{current_plot}\n\n{tmdb_overview}".strip()

        # C. キャストの完全上書きとランク付与
        cast_list = tmdb_data.get("credits", {}).get("cast", [])
        new_cast_mapping = []
        for cast in cast_list:
            # 役名が特定できないエキストラなどは除外
            role_name = cast.get("character", "").strip()
            if not role_name or role_name.lower() in [
                "",
                "uncredited",
                "himself",
                "herself",
            ]:
                continue

            # 俳優のTMDB IDを取得
            actor_id = cast.get("id")

            new_cast_mapping.append(
                {
                    "actor": cast.get("name"),
                    "external_id": f"tmdb_{actor_id}" if actor_id else None,
                    "role": role_name,
                    "guarantee_rank": get_rank(cast.get("order", 99)),
                }
            )

        movie["cast_mapping"] = new_cast_mapping

        # --- 最終クリーニング ---
        # キャストが取得できなかった、またはあらすじがまだ500文字未満のものは捨てる
        if not movie["cast_mapping"] or len(movie.get("plot_full", "")) < 500:
            print("スキップ (品質基準未達: キャストなし or あらすじ不足)")
            skipped_low_quality += 1
            continue

        # 品質フラグを強制的に false にして保存対象に追加
        movie["low_quality_flag"] = False
        enhanced_data.append(movie)
        print("補完完了")

        # TMDB API のレートリミットを考慮して少し待機
        time.sleep(0.1)

        # 100件ごとに途中保存（クラッシュ対策）
        if len(enhanced_data) % 100 == 0:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(enhanced_data, f, ensure_ascii=False, indent=2)

    # 最終結果の保存
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 40)
    print("処理がすべて完了しました！")
    print(f"元データ件数: {len(raw_data)} 件")
    print(f"TMDB特定不可によるスキップ: {skipped_tmdb_not_found} 件")
    print(f"品質基準未達によるスキップ: {skipped_low_quality} 件")
    print(f"★ 最終的な高品質データ件数: {len(enhanced_data)} 件")
    print(f"出力先: {OUTPUT_FILE}")
    print("=" * 40)


if __name__ == "__main__":
    main()
