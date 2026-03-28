import json
import time
import urllib.parse
from pathlib import Path
from typing import List, TypedDict, cast

import wikipediaapi
from SPARQLWrapper import JSON, SPARQLWrapper

# --- 設定 ---
USER_AGENT = "EpidaurosDataCollector/1.0 (glyphcat13@gmail.com)"
WIKI_LANG = "en"


class SparqlBinding(TypedDict, total=False):
    type: str
    value: str


class SparqlRow(TypedDict, total=False):
    movie: SparqlBinding
    wikipediaTitle: SparqlBinding
    year: SparqlBinding
    boxOffice: SparqlBinding
    title: SparqlBinding
    wikiTitle: SparqlBinding  # 追加: Wikipediaの正確な記事名
    directorLabel: SparqlBinding
    genreLabel: SparqlBinding
    actorName: SparqlBinding
    roleName: SparqlBinding


class SparqlResults(TypedDict):
    bindings: List[SparqlRow]


class SparqlResponse(TypedDict):
    results: SparqlResults


def get_sparql_results(query: str) -> List[SparqlRow]:
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.agent = USER_AGENT

    for attempt in range(3):
        try:
            raw = sparql.query().convert()
            data = cast(SparqlResponse, raw)
            return data["results"]["bindings"]
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                wait_time = (attempt + 1) * 15
                print(
                    f"\n[429 Too Many Requests] {wait_time}秒待機して再試行します... ({attempt + 1}/3)"
                )
                time.sleep(wait_time)
            else:
                print(f"SPARQL Error: {e}")
                time.sleep(5)

    return []


def sparql_value(row: SparqlRow, key: str) -> str:
    binding = row.get(key)
    if not binding:
        return ""
    return binding.get("value", "")


def get_movie_base_list() -> List[dict]:
    print("Step 1: Wikidataから映画リスト（母体）を取得中...")
    all_movies = []
    seen = set()

    periods = [(1960, 1980), (1981, 2000), (2001, 2025)]

    for start_year, end_year in periods:
        # 重複排除で減る分を見越して SPARQL側では2000件要求する
        query = f"""
        SELECT DISTINCT ?movie ?year ?title ?wikiTitle WHERE {{
          ?movie wdt:P31 wd:Q11424.
          ?movie wdt:P577 ?date.
          BIND(YEAR(?date) AS ?year).
          FILTER(?year >= {start_year} && ?year <= {end_year})

          ?movie rdfs:label ?title.
          FILTER(LANG(?title) = "en").

          ?sitelink schema:about ?movie;
                    schema:isPartOf <https://en.wikipedia.org/>.
          # WikipediaのURLから正確な記事名を抽出
          BIND(REPLACE(STR(?sitelink), "https://en.wikipedia.org/wiki/", "") AS ?wikiTitle)
        }}
        LIMIT 2000
        """
        print(f"  > {start_year}-{end_year}: ", end="", flush=True)
        results = get_sparql_results(query)

        period_movies = []
        for r in results:
            qid = sparql_value(r, "movie").split("/")[-1]

            # まだ追加されていないユニークな作品だけを処理
            if qid not in seen:
                seen.add(qid)

                # URLエンコードされた文字（%20など）を元に戻す
                raw_wiki = sparql_value(r, "wikiTitle")
                wiki_title = urllib.parse.unquote(raw_wiki)

                period_movies.append(
                    {
                        "qid": qid,
                        "title": sparql_value(r, "title"),
                        "year": sparql_value(r, "year"),
                        "wiki_title": wiki_title,  # 正確なWikipediaタイトルを保持
                    }
                )

            # 各年代、ぴったり1200件取得できた時点でループを終了
            if len(period_movies) >= 1200:
                break

        print(f"ユニーク {len(period_movies)}件確保")
        all_movies.extend(period_movies)

    return all_movies


def main():
    wiki = wikipediaapi.Wikipedia(user_agent=USER_AGENT, language=WIKI_LANG)
    movie_list = get_movie_base_list()

    print(f"\nStep 2: 詳細データとWikipedia本文を収集（全 {len(movie_list)} 件）...")
    final_dataset = []

    for i, m in enumerate(movie_list):
        qid = m["qid"]
        title = m["title"]
        year_str = m["year"]
        wiki_title = m.get("wiki_title", title)  # 取得した正確なタイトルを使用

        details_query = f"""
        SELECT ?directorLabel ?genreLabel WHERE {{
          VALUES ?movie {{ wd:{qid} }}
          OPTIONAL {{ ?movie wdt:P57 ?director. ?director rdfs:label ?directorLabel. FILTER(LANG(?directorLabel) = "en") }}
          OPTIONAL {{ ?movie wdt:P136 ?genre. ?genre rdfs:label ?genreLabel. FILTER(LANG(?genreLabel) = "en") }}
        }}
        """
        details = get_sparql_results(details_query)

        cast_query = f"""
        SELECT ?actorName ?roleName WHERE {{
          VALUES ?movie {{ wd:{qid} }}
          ?movie p:P161 ?statement.
          ?statement ps:P161 ?actor.
          ?actor rdfs:label ?actorName.
          FILTER(LANG(?actorName) = "en").
          OPTIONAL {{ ?statement pq:P453 ?role. ?role rdfs:label ?roleName. FILTER(LANG(?roleName) = "en") }}
        }}
        """
        casts = get_sparql_results(cast_query)

        # 曖昧なタイトルではなく、正確な記事名で検索するため確実にヒットする
        page = wiki.page(wiki_title)
        if not page.exists():
            continue

        plot_text = ""
        sections = page.sections
        for s in sections:
            if s.title.lower() in ["plot", "synopsis", "story"]:
                plot_text = s.text
                break
        if not plot_text:
            plot_text = page.summary

        movie_entry = {
            "title": title,
            "metadata": {
                "year": int(year_str) if year_str else 0,
                "box_office": 0,
                "directors": list(
                    set(
                        sparql_value(d, "directorLabel")
                        for d in details
                        if "directorLabel" in d
                    )
                ),
                "genres": list(
                    set(
                        sparql_value(g, "genreLabel")
                        for g in details
                        if "genreLabel" in g
                    )
                ),
                "wikidata_id": qid,  # 既存のデータ構造を維持
            },
            "cast_mapping": [
                {
                    "actor": sparql_value(c, "actorName"),
                    "role": sparql_value(c, "roleName") or "N/A",
                }
                for c in casts
            ],
            "plot_full": plot_text,
            "low_quality_flag": len(plot_text) < 500 or not casts,
        }

        final_dataset.append(movie_entry)
        if (i + 1) % 50 == 0:
            print(f"進捗: {i+1}/{len(movie_list)} 完了 (現在 {len(final_dataset)} 件)")
            fp = Path(__file__).parent.parent.resolve() / "raw_dataset.json"
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(final_dataset, f, ensure_ascii=False, indent=2)

        time.sleep(1.0)

    fp = Path(__file__).parent.parent.resolve() / "raw_dataset.json"
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)

    print(f"\n取得完了: {len(final_dataset)} 件を保存しました。")


if __name__ == "__main__":
    main()
