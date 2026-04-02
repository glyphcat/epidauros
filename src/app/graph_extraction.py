
import json
import tempfile
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from src.core import GraphGenerator


# --- Visualization helper ---
def visualize_graph(scenario_graph):
    """ScenarioGraphオブジェクトをPyvisで可視化し表示する"""
    net = Network(height="500px", width="100%", directed=True)

    for node in scenario_graph.nodes:
        net.add_node(node.node_id, label=label, title=title, shape="ellipse")

    for edge in scenario_graph.edges:
        net.add_edge(edge.source_node_id, edge.target_node_id,
                     label=edge.situation_id, title=edge.reason, arrows="to")

    net.barnes_hut()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, 'r', encoding='utf-8') as f:
            html_string = f.read()

    components.html(html_string, height=550)

# --- UI Construction ---
st.set_page_config(page_title="Graph Extraction Test", layout="wide")
st.title("🎬 Scenario Graph Extraction Test")
st.info("Extracts character archetypes and dramatic situations from plot summaries.")


with st.sidebar:
    st.header("LLM Settings")
    model_name = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini"], index=0)
    temp = st.slider("Temperature", 0.0, 1.0, 0.0)

col_input, col_config = st.columns([2, 1])

with col_input:
    title = st.text_input("Project Title", value="Star Wars: A New Hope")
    plot_text = st.text_area(
        "Plot / Synopsis",
        height=400,
        value="帝国軍の巨大要塞デス・スターによって滅ぼされようとしている銀河。農場育ちの青年ルークは、隠遁者オビ＝ワンから父がジェダイであったことを知らされ、旅に出る。...",
        placeholder="あらすじを入力してください...",
        )

with col_config:
    st.subheader("Cast List")
    st.caption("抽出対象とする俳優と役名をJSON形式で指定します。")
    default_cast = [
        {"actor": "Mark Hamill", "role": "Luke Skywalker"},
        {"actor": "Alec Guinness", "role": "Obi-Wan Kenobi"},
        {"actor": "Harrison Ford", "role": "Han Solo"},
        {"actor": "Carrie Fisher", "role": "Princess Leia"},
        {"actor": "James Earl Jones", "role": "Darth Vader"},
    ]
    cast_input = st.text_area("Cast JSON", value=json.dumps(default_cast, indent=2), height=350)


# --- Execution logic ---
# State initialization
if "extraction_result" not in st.session_state:
    st.session_state.extraction_result = None

if st.button("Generate Graph Structure", type="primary", use_container_width=True):
    if not plot_text or not cast_input:
        st.warning("Please provide both plot and cast list.")
    else:
        try:
            generator = GraphGenerator(model_name=model_name, temperature=temp)
            with st.spinner("Analyzing scenario structure with LLM..."):
                cast_mapping = json.loads(cast_input)
                result = generator.generate(title, plot_text, cast_mapping)
                st.session_state.extraction_result = result

        except Exception as e:
            st.error(f"Error: {e}")

# Display results if available in session
if st.session_state.extraction_result:
    result = st.session_state.extraction_result

    st.success("Extraction Successful!")

    # 1. グラフ可視化
    st.subheader("Visualized Scenario Graph")
    visualize_graph(result)

    # 2. 詳細テーブル
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.subheader("Nodes: Character Archetypes")
        st.table([n.model_dump() for n in result.nodes])
    with res_col2:
        st.subheader("Edges: Dramatic Situations")
        st.table([e.model_dump() for e in result.edges])

    # PydanticモデルをJSON文字列に変換
    json_string = json.dumps(result.model_dump(), indent=4, ensure_ascii=False)

    # ダウンロードボタンの設置
    st.download_button(
        label="📥 Download Graph JSON",
        data=json_string,
        file_name=f"graph_{title.replace(' ', '_')}.json",
        mime="application/json",
        key="download_button_result" # keyを指定して状態を安定させる
    )

    with st.expander("View Raw Output"):
        st.json(result.model_dump())
