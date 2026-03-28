# import json
# import os
# from pathlib import Path
# from typing import Any, Dict, List

# import instructor
# import requests
# from dotenv import load_dotenv
# from fuzzywuzzy import fuzz
# from openai import OpenAI
# from pydantic import BaseModel, Field

# load_dotenv()


# # --- Pydanticスキーマ ---
# class ActorRolePair(BaseModel):
#     role_name: str = Field(
#         ..., description="劇中の呼称。あらすじで使用されている名前に合わせる"
#     )
#     actor_name: str = Field(..., description="俳優のフルネーム")


# class EnhancedCast(BaseModel):
#     pairs: List[ActorRolePair]


# # --- Step1. LLM抽出関数 ---
# def extract_refined_cast(
#     movie_title: str, cast_hints: str, plot_summary: str
# ) -> EnhancedCast:
#     openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#     client = instructor.patch(openai_client)
#     return client.chat.completions.create(
#         model="gpt-4o",
#         response_model=EnhancedCast,
#         messages=[
#             {
#                 "role": "system",
#                 "content": "Wikipediaのキャスト情報から、役名と俳優のペアを抽出してください。劇中の呼称(role_name)を正確に特定することが重要です。",
#             },
#             {
#                 "role": "user",
#                 "content": f"Title: {movie_title}\nCast Info: {cast_hints}\nPlot Summary: {plot_summary}",
#             },
#         ],
#     )  # type: ignore


# # --- Step2. TMDBによる検証と補完 ---
# def enhance_with_tmdb(
#     movie_title: str, release_year: int, extracted_pairs: List[ActorRolePair]
# ) -> List[Dict[str, str]]:
#     token = os.getenv("TMDB_READ_TOKEN")
#     headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

#     # 1. 映画検索
#     search_url = "https://api.themoviedb.org/3/search/movie"
#     params = {"query": movie_title, "year": release_year}

#     try:
#         res = requests.get(search_url, headers=headers, params=params).json()
#         if not res.get("results"):
#             # TMDBに映画がない場合はLLMの結果をそのまま辞書形式で返す
#             return [
#                 {
#                     "role_name": p.role_name,
#                     "actor_name": p.actor_name,
#                     "source": "llm_only",
#                 }
#                 for p in extracted_pairs
#             ]

#         # 2. キャスト一覧(Credits)を取得
#         movie_id = res["results"][0]["id"]
#         credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
#         credits = requests.get(credits_url, headers=headers).json()
#         tmdb_cast = credits.get("cast", [])

#         refined_results = []
#         for p in extracted_pairs:
#             best_match = None
#             highest_score = 0

#             # TMDBのキャストリストと照合
#             for t_member in tmdb_cast:
#                 # 俳優名の類似度を計算
#                 score = fuzz.token_sort_ratio(p.actor_name, t_member["name"])
#                 if score > 80 and score > highest_score:
#                     highest_score = score
#                     best_match = t_member

#             if best_match:
#                 # 【補完】俳優名はTMDBの公式名を採用し、役名はLLMが特定した劇中呼称を優先
#                 refined_results.append(
#                     {
#                         "role_name": p.role_name,  # あらすじ内での名前 (LLM)
#                         "actor_name": best_match["name"],  # 正式な俳優名 (TMDB)
#                         "tmdb_character": best_match[
#                             "character"
#                         ],  # TMDB上の公式役名 (参考用)
#                         "source": "verified",
#                     }
#                 )

#         return refined_results

#     except Exception as e:
#         print(f"  TMDB Error: {e}")
#         return [
#             {
#                 "role_name": p.role_name,
#                 "actor_name": p.actor_name,
#                 "source": "error_fallback",
#             }
#             for p in extracted_pairs
#         ]


# # --- Main. ---
# def main():
#     src = Path(__file__).parent.resolve() / "cleaned_dataset.json"
#     dst = Path(__file__).parent.resolve() / "enhanced_dataset.json"

#     if not src.exists():
#         print(f"Error: {src} が見つかりません。")
#         return

#     with open(src, "r", encoding="utf-8") as f:
#         movies = json.load(f)

#     enhanced_movies = []
#     print(f"全 {len(movies)} 件のエンハンスを開始します...")

#     for i, movie in enumerate(movies):
#         print(
#             f"[{i+1}/{len(movies)}] {movie['title']} ({movie['metadata']['year']}) 処理中..."
#         )

#         # 必須データの欠損チェック
#         if not movie.get("plot_full") or not movie.get("cast_hints_raw"):
#             movie["low_quality_flag"] = True
#             enhanced_movies.append(movie)
#             continue

#         try:
#             # 1. LLMで役名と俳優のペアを抽出
#             extracted = extract_refined_cast(
#                 movie["title"], movie["cast_hints_raw"], movie["plot_full"]
#             )

#             # 2. TMDBデータで補完・正規化
#             # metadata['year'] が文字列の場合を考慮して int にキャスト
#             year = int(movie["metadata"]["year"])
#             refined_cast = enhance_with_tmdb(movie["title"], year, extracted.pairs)

#             # 3. データの更新
#             movie["refined_cast"] = refined_cast
#             movie["low_quality_flag"] = len(refined_cast) == 0

#         except Exception as e:
#             print(f"  Critical Error: {e}")
#             movie["low_quality_flag"] = True

#         enhanced_movies.append(movie)

#         # 10件ごとに中間保存(長時間実行時のケア)
#         if (i + 1) % 10 == 0:
#             with open(dst, "w", encoding="utf-8") as f:
#                 json.dump(enhanced_movies, f, ensure_ascii=False, indent=2)

#     # 最終保存
#     with open(dst, "w", encoding="utf-8") as f:
#         json.dump(enhanced_movies, f, ensure_ascii=False, indent=2)

#     print(f"エンハンス完了！ 出力先: {dst}")


# if __name__ == "__main__":
#     main()
