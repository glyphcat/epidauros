import json
import time
from pathlib import Path
from typing import List, TypedDict, cast

import wikipediaapi
from SPARQLWrapper import JSON, SPARQLWrapper

# --- 設定 ---
USER_AGENT = "MovieCastAgentCollector/1.1 (your-email@example.com)"
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
    try:
        raw = sparql.query().convert()
        data = cast(SparqlResponse, raw)
        return data["results"]["bindings"]
    except Exception as e:
        print(f"SPARQL Error: {e}")
        return []


def sparql_value(row: SparqlRow, key: str) -> str:
    binding = row.get(key)
    if not binding:
        return ""
    return binding.get("value", "")


def main():
    wiki = wikipediaapi.Wikipedia(USER_AGENT, WIKI_LANG)
    movie_list = []
    # ターゲット年代（母数確保のため範囲を調整）
    decades = [(1960, 1980), (1980, 2000), (2000, 2027)]

    print("Step 1: Wikidataから映画リスト（母体）を取得中...")
    for start, end in decades:
        # 興行収入をOPTIONALにし、Wikipedia英語版がある米国映画を抽出
        query = f"""
        SELECT DISTINCT ?movie ?wikipediaTitle ?year WHERE {{
          ?movie wdt:P31 wd:Q11424; wdt:P495 wd:Q30; wdt:P577 ?date.
          BIND(YEAR(?date) AS ?year)
          FILTER(?year >= {start} && ?year < {end})
          ?article schema:about ?movie; schema:isPartOf <https://en.wikipedia.org/>; schema:name ?wikipediaTitle.
        }} ORDER BY DESC(?year) LIMIT 1000
        """
        results = get_sparql_results(query)
        movie_list.extend(results)
        print(f"  > {start}-{end}: {len(results)}件取得")
        time.sleep(1)

    final_dataset = []
    print(f"Step 2: 詳細データとWikipedia本文を収集（全 {len(movie_list)} 件）...")

    for i, item in enumerate(movie_list):
        m_uri = sparql_value(item, "movie")
        w_title = sparql_value(item, "wikipediaTitle")
        if not m_uri or not w_title:
            continue

        # 詳細メタデータ取得（BoxOfficeは後で外部API補完するためここではOPTIONAL）
        detail_query = f"""
        SELECT ?title ?year ?boxOffice ?directorLabel ?genreLabel WHERE {{
          BIND(<{m_uri}> AS ?m)
          ?m rdfs:label ?title. FILTER(LANG(?title) = "en")
          ?m wdt:P577 ?date. BIND(YEAR(?date) AS ?year)
          OPTIONAL {{ ?m wdt:P2142 ?boxOffice. }}
          OPTIONAL {{ ?m wdt:P57 ?dir. ?dir rdfs:label ?directorLabel. FILTER(LANG(?directorLabel) = "en") }}
          OPTIONAL {{ ?m wdt:P136 ?gen. ?gen rdfs:label ?genreLabel. FILTER(LANG(?genreLabel) = "en") }}
        }}
        """
        details = get_sparql_results(detail_query)
        if not details:
            continue
        title = sparql_value(details[0], "title")
        year_str = sparql_value(details[0], "year")
        box_office_str = sparql_value(details[0], "boxOffice")
        if not title or not year_str:
            continue

        # Wikipediaページ取得
        page = wiki.page(w_title)
        if not page.exists():
            continue

        # セクション取得（名称の揺れに対応）
        def get_sec_text(titles):
            for t in titles:
                sec = page.section_by_title(t)
                if sec:
                    return sec.text
            return ""

        plot_text = get_sec_text(["Plot", "Synopsis", "Story", "Summary"])
        cast_text = get_sec_text(["Cast", "Characters", "Casting"])

        # キャスト情報の構築（Wikidataのキャストをベースにするが、N/A排除は次工程で実施）
        cast_query = f"""
        SELECT ?actorName ?roleName WHERE {{
          <{m_uri}> p:P161 ?s.
          ?s ps:P161 ?actor. ?actor rdfs:label ?actorName. FILTER(LANG(?actorName) = "en")
          OPTIONAL {{ ?s pq:P453 ?role. ?role rdfs:label ?roleName. FILTER(LANG(?roleName) = "en") }}
        }}
        """
        casts = get_sparql_results(cast_query)

        movie_entry = {
            "title": title,
            "metadata": {
                "year": int(year_str),
                "box_office": (float(box_office_str) if box_office_str else None),
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
            },
            "cast_mapping": [
                {
                    "actor": sparql_value(c, "actorName"),
                    "role": sparql_value(c, "roleName") or "N/A",
                }
                for c in casts
            ],
            "cast_hints_raw": cast_text,
            "lead_text": page.summary,
            "plot_full": plot_text,
            "low_quality_flag": len(plot_text) < 500 or not cast_text,
        }

        final_dataset.append(movie_entry)
        if (i + 1) % 50 == 0:
            print(f"進捗: {i+1}/{len(movie_list)} 完了")
        time.sleep(0.5)

    # 保存
    fp = Path(__file__).parent.parent.resolve() / "raw_dataset.json"
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)
    print(f"\n完了: {len(final_dataset)}件のデータを保存しました。")


if __name__ == "__main__":
    main()
