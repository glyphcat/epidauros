import os

import psycopg2
import streamlit as st
from qdrant_client import QdrantClient

st.title("Epidauros Dashboard")

# 1. PostgreSQL 接続確認
st.header("1. PostgreSQL Connection")
try:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    st.success("PostgreSQL: Connected!")
    conn.close()
except Exception as e:
    st.error(f"PostgreSQL Error: {e}")

# 2. Qdrant 接続確認
st.header("2. Qdrant Connection")
try:
    client = QdrantClient(host="qdrant", port=6333)
    # 疎通確認のための軽い呼び出し
    client.get_collections()
    st.success("Qdrant: Connected!")
except Exception as e:
    st.error(f"Qdrant Error: {e}")

st.divider()
st.info("これが表示されていれば、フロントエンドコンテナの動作も正常です。")
