CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- 1. 俳優テーブル (actors)
-- ==========================================
CREATE TABLE actors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    -- TMDBのIDなど。インポート時の同姓同名・同一人物判定の根拠として使用
    external_id TEXT UNIQUE,
    gender INTEGER,
    birth_date DATE,
    -- ギャランティスコア。直近作品のキャスティング順から想定し、加重平均で算出。
    current_guarantee_score NUMERIC(6, 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 2. 作品テーブル (works)
-- ==========================================
CREATE TABLE works (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    -- TMDBまたはWikidataのID(現在のところwikipediaIDを想定)
    external_id TEXT UNIQUE,
    release_year INTEGER,
    -- プロットの生テキスト
    plot_full TEXT NOT NULL,

    -- メタデータ（JSON化せず、シンプルなテキスト・数値として格納）
    -- 複数いる場合はカンマ区切り文字列を想定
    director TEXT,
    genre TEXT,
    box_office NUMERIC,
    setting_period TEXT,
    setting_location TEXT,

    -- Qdrant上の参照ID。プロット構造の類似度検索用
    plot_embedding_id UUID,

    -- LLMで抽出するシナリオグラフ構造の格納用
    scenario_graph_data JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 3. 配役実績テーブル (performances)
-- ==========================================
CREATE TABLE performances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id UUID REFERENCES works(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES actors(id) ON DELETE CASCADE,

    character_name TEXT NOT NULL,
    -- その作品での出演順位（S, A, B, C）
    expected_guarantee_rank TEXT CHECK (expected_guarantee_rank IN ('S', 'A', 'B', 'C', 'N/A')),

    -- 後から算出するその役柄の成功度スコア
    -- 将来的に演技賞受賞歴やレビューより個別に重み付けする予定のためPerformancesに配置
    success_score NUMERIC(6, 5),

    -- Qdrant上の参照ID。キャラクターの性質による類似検索用
    character_vector_id UUID,

    -- 36の劇的場面のID。主体となったものと客体となったものを分離
    source_situation_ids TEXT[],
    target_situation_ids TEXT[],

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- 同一作品内で同じ俳優が同じ役を複数回登録されるのを防ぐ
    UNIQUE(work_id, actor_id, character_name)
);

-- インデックス
CREATE INDEX idx_actors_name ON actors(name);
CREATE INDEX idx_performances_work_id ON performances(work_id);
CREATE INDEX idx_performances_actor_id ON performances(actor_id);
