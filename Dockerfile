# 開発用builder
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
# 仮想環境を構築
RUN uv sync --frozen --no-cache --no-group dataset --no-group dev --no-install-project

# 実際のApp用環境
FROM python:3.13-slim-bookworm AS runner
WORKDIR /app

# 警告を消すために git をインストール
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# builder から仮想環境をコピー
COPY --from=builder /app/.venv /app/.venv

# パスと環境変数の設定
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

COPY src/ ./src/

CMD ["streamlit", "run", "src/app/casting_board.py", "--server.address", "0.0.0.0"]
