import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

# Collections mapping to Postgres table names
COLLECTIONS = ["works", "performances"]

# Dimension size (OpenAI text-embedding-3-small)
VECTOR_SIZE = 1536

def init_qdrant():
    """Initializes Qdrant collections with defined vector parameters."""
    print(f"Connecting to Qdrant... ({QDRANT_HOST}:{QDRANT_PORT})")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    for collection_name in COLLECTIONS:
        if client.collection_exists(collection_name=collection_name):
            print(f"Collection '{collection_name}' already exists. Skipping.")
            continue

        print(f"Creating collection '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    print("Qdrant initialization complete.")

if __name__ == "__main__":
    init_qdrant()
