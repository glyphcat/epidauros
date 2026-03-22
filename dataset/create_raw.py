import json
import re
import time
from pathlib import Path

import wikipediaapi
from SPARQLWrapper import JSON, SPARQLWrapper

# --- 設定 ---
USER_AGENT = "MovieCastAgentCollector/1.1 (your-email@example.com)"
WIKI_LANG = "en"


def get_sparql_results(query):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        return sparql.query().convert()["results"]["bindings"]  # type: ignore
    except Exception as e:
        print(f"SPARQL Error: {e}")
        return []


def main():
    wiki = wikipediaapi.Wikipedia(USER_AGENT, WIKI_LANG)

    # 1. 各年代ごとに小分けにしてインデックスを取得（タイムアウト対策）
    print("Step 1: 年代別にインデックスを取得中...")
    movie_list = []
    decades = [
        (1960, 1970),
        (1970, 1980),
        (1980, 1990),
        (1990, 2000),
        (2000, 2010),
        (2010, 2027),
    ]

    for start, end in decades:
        print(f"  > {start}年代のリストを取得中...")
        # ハリウッド映画（wdt:P495 wd:Q30）に限定
        query = f"""
        SELECT DISTINCT ?movie ?wikipediaTitle ?year ?boxOffice WHERE {{
          ?movie wdt:P31 wd:Q11424;
                 wdt:P495 wd:Q30;
                 wdt:P2142 ?boxOffice;
                 wdt:P577 ?date.
          BIND(YEAR(?date) AS ?year)
          FILTER(?year >= {start} && ?year < {end})

          ?article schema:about ?movie;
                   schema:isPartOf <https://en.wikipedia.org/>;
                   schema:name ?wikipediaTitle.
        }} ORDER BY ?date LIMIT 400
        """
        results = get_sparql_results(query)
        movie_list.extend(results)
        print(f"    - {len(results)}件取得")
        # wikiサーバーへの負荷軽減
        time.sleep(1)

    print(f"合計 {len(movie_list)} 件のインデックスを確保しました。")

    final_dataset = []
    print(f"Step 2: 各映画の詳細データを収集（全 {len(movie_list)} 件）...")
    for i, item in enumerate(movie_list):
        m_uri = item["movie"]["value"]
        w_title = item["wikipediaTitle"]["value"]

        # 個別映画のメタデータ取得（要件3: 収入、年、監督、ジャンル）
        # timeout対策に一件ずつ
        detail_query = f"""
        SELECT ?title ?year ?boxOffice ?directorLabel ?genreLabel WHERE {{
          BIND(<{m_uri}> AS ?m)
          ?m rdfs:label ?title. FILTER(LANG(?title) = "en")
          ?m wdt:P577 ?date. BIND(YEAR(?date) AS ?year)
          ?m wdt:P2142 ?boxOffice.
          OPTIONAL {{ ?m wdt:P57 ?dir. ?dir rdfs:label ?directorLabel. FILTER(LANG(?directorLabel) = "en") }}
          OPTIONAL {{ ?m wdt:P136 ?gen. ?gen rdfs:label ?genreLabel. FILTER(LANG(?genreLabel) = "en") }}
        }}
        """
        details = get_sparql_results(detail_query)
        if not details:
            continue

        # 役名・キャストのペア取得
        cast_query = f"""
        SELECT ?actorName ?roleName WHERE {{
          <{m_uri}> p:P161 ?s.
          ?s ps:P161 ?actor. ?actor rdfs:label ?actorName. FILTER(LANG(?actorName) = "en")
          OPTIONAL {{ ?s pq:P453 ?role. ?role rdfs:label ?roleName. FILTER(LANG(?roleName) = "en") }}
        }}
        """
        casts = get_sparql_results(cast_query)

        # Wikipediaテキスト取得
        page = wiki.page(w_title)
        if not page.exists():
            continue

        plot_sec = page.section_by_title("Plot") or page.section_by_title("Synopsis")
        cast_sec = page.section_by_title("Cast") or page.section_by_title("Characters")

        plot_text = plot_sec.text if plot_sec else ""

        # データ統合
        movie_entry = {
            "title": details[0]["title"]["value"].split(" (")[0],  # type: ignore
            "metadata": {
                "year": int(details[0]["year"]["value"]),  # type: ignore
                "box_office": float(details[0]["boxOffice"]["value"]),  # type: ignore
                "directors": list(
                    set(
                        d["directorLabel"]["value"]  # type: ignore
                        for d in details
                        if "directorLabel" in d
                    )
                ),
                "genres": list(
                    set(g["genreLabel"]["value"] for g in details if "genreLabel" in g)  # type: ignore
                ),
            },
            "cast_mapping": [
                {
                    "actor": c["actorName"]["value"],  # type: ignore
                    "role": c.get("roleName", {}).get("value", "N/A"),  # type: ignore
                }
                for c in casts
            ],
            "cast_hints_raw": cast_sec.text if cast_sec else "",
            "lead_text": page.summary,
            "plot_full": plot_text,
            # plot品質のフィルタリング
            "low_quality_flag": len(plot_text) < 500,
        }

        final_dataset.append(movie_entry)
        print(f"[{i+1}/{len(movie_list)}] {movie_entry['title']} 完了")

        # 負荷軽減
        time.sleep(0.5)

    try:
        op = Path(__file__).parent / "raw_dataset.json"
        with open(op, "w", encoding="utf-8") as f:
            json.dump(final_dataset, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("\nファイル出力に失敗しました。")

    print("\nすべての処理が正常に完了しました。")


if __name__ == "__main__":
    main()
