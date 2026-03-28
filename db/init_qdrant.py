import os

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# 環境変数からQdrantのホストを取得（Docker Compose環境に合わせる）
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

# 作成するコレクション（Postgresのテーブル名に合わせる）
COLLECTIONS = ["works", "performances"]

# 使用するEmbeddingモデルの次元数（例: OpenAI(text-embedding-3-small)=1536, Gemini=768）
VECTOR_SIZE = 1536


def init_qdrant():
    print(f"Qdrantに接続中... ({QDRANT_HOST}:{QDRANT_PORT})")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    for collection_name in COLLECTIONS:
        if client.collection_exists(collection_name=collection_name):
            print(
                f"コレクション '{collection_name}' は既に存在します。スキップします。"
            )
            continue

        print(f"コレクション '{collection_name}' を作成しています...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    print("Qdrantの初期化が完了しました。")


if __name__ == "__main__":
    init_qdrant()
