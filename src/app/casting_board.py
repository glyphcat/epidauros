import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

from src.core.graph_generator import GraphGenerator
from src.core.casting_agent import CastingAgent
from src.core.database import SessionLocal
from streamlit_agraph import agraph, Node, Edge, Config

load_dotenv()

st.set_page_config(page_title="Epidauros AI Casting Agent", layout="wide", page_icon="🎬")

# --- UI Header ---
st.title("🎬 Epidauros (AI-Casting Board Agent)")
st.markdown("""
シナリオやプロットを入力し、登場人物の関係性を抽出して最適なキャストを提案するAIボードです。
**あらすじ本文では、役名ではなく `$c1`, `$c2` といったIDを使って人物間の関係を記述してください。**
""")

# --- State Init ---
if "scenario_graph" not in st.session_state:
    st.session_state.scenario_graph = None
if "casting_results" not in st.session_state:
    st.session_state.casting_results = None

# --- Visualization Function ---
def render_graph(graph):
    nodes = []
    edges = []
    
    # ユーザーリクエストに合わせて全体を黒・オレンジ・グレーを基調としたクールな配色に変更
    color_map = {
        "HERO": "#FF7F00",                # 鮮やかなオレンジ
        "MENTOR": "#FFA500",              # オレンジ
        "SHADOW": "#333333",              # 黒/ダークグレー
        "ALLY": "#FFB347",                # パステル系オレンジ
        "HERALD": "#FFCC80",              # 淡いオレンジ
        "THRESHOLD_GUARDIAN": "#CC6600",  # 深めのオレンジ
        "SHAPESHIFTER": "#E68A00",        # 黄土色がかったオレンジ
        "TRICKSTER": "#B37400",           # 暗めのブラウンオレンジ
        "NOT_MENTIONED": "#555555"        # グレー
    }
    
    for n in graph.nodes:
        color = color_map.get(n.archetype_id, "#bdc3c7")
        nodes.append(Node(
            id=n.node_id,
            label=f"{n.role_name}\n({n.archetype_id})",
            title=n.description,
            size=25,
            color=color,
            shape="dot"
        ))
        
    for e in graph.edges:
        edges.append(Edge(
            source=e.source_node_id, 
            label=e.situation_id, 
            target=e.target_node_id,
            title=e.reason,
            color="#FF9900" 
        ))
        
    config = Config(
        width='100%',
        height=500,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#FFB347"
    )
    
    return agraph(nodes=nodes, edges=edges, config=config)

# --- Main Layout ---
tab1, tab2, tab3 = st.tabs(["1. Scenario Setup", "2. Character Graph", "3. Casting Proposals"])

with tab1:
    col_plot, col_cast = st.columns([1.2, 1])
    
    with col_plot:
        st.subheader("Story Plot", help="物語のあらすじを入力します。AIが関係性を正確に抽出できるよう、具体的な役名ではなく「$c1 は $c2 を裏切った」のようにID記法を用いて記述してください。")
        title_input = st.text_input("Project Title", value="Untitled Project")
        plot_input = st.text_area(
            "Plot Text", 
            height=300,
            value="$c1 は平和な農村に暮らす若者。ある日、$c2 が現れ、$c1 に秘められた力があることを伝える。",
            help="登場人物は名前そのものではなく、$c1や$c2という表記を使って関係性を書いてください。"
        )
        
    with col_cast:
        st.subheader("Characters List", help="登場人物の定義一覧です。AIからの配役提案が欲しいキャラクターは「Suggest?」にチェックを入れてください。")
        st.caption("登場人物を定義し、キャスティング提案の要否を指定します。")
        
        # --- 超強力なカスタムCSS注入 ---
        st.markdown("""
        <style>
        /* 1. 行間の徹底的な圧縮 (Gapゼロ化 ＆ マージン削減) */
        div[data-testid="column"]:has(.char-list-container) div[data-testid="stVerticalBlock"] {
            gap: 0px !important;
        }
        div[data-testid="column"]:has(.char-list-container) div[data-testid="stHorizontalBlock"] {
            gap: 2px !important;
            margin-bottom: -15px !important;
            align-items: end !important; /* マイナスボタンを下揃えにし、テキストボックスと縦位置を合わせる */
        }
        div[data-testid="column"]:has(.char-list-container) .stTextInput,
        div[data-testid="column"]:has(.char-list-container) .stCheckbox {
            margin-bottom: 0px !important;
        }

        /* 2. ベーススタイル: リストコンテナ内のSecondaryボタンはすべて【赤色（➕ボタン用）】にする */
        html body div[data-testid="column"]:has(.char-list-container) button[kind="secondary"] {
            background-color: #FF4B4B !important;
            color: white !important;
            border: none !important;
            width: 32px !important;
            min-height: 32px !important;
            height: 32px !important;
            padding: 0px !important;
            margin-top: 10px !important; /* 表本体から少し離す */
        }

        /* 3. 上書きスタイル: 横並びブロック（行）の中にあるSecondaryボタンは【青色（➖ボタン用）】にする */
        html body div[data-testid="column"]:has(.char-list-container) div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
            background-color: #1E90FF !important;
            margin-top: 0px !important;
            margin-bottom: 8px !important; /* テキストボックスの高さとの微細なズレを調整 */
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="char-list-container" style="display:none;"></div>', unsafe_allow_html=True)
        
        # リスト型でのステート管理に変更
        if "char_list" not in st.session_state:
            st.session_state.char_list = [
                {"id": "$c1", "role": "主人公", "suggest_casting": True, "already_cast": ""},
                {"id": "$c2", "role": "賢者", "suggest_casting": True, "already_cast": ""}
            ]
            
        # 表のヘッダー風レイアウト
        h_cols = st.columns([1.5, 3, 2, 3, 1])
        h_cols[0].markdown("**ID**")
        h_cols[1].markdown("**Role Name**")
        h_cols[2].markdown("**Suggest?**")
        h_cols[3].markdown("**Already Cast**")
        
        # 各行の描画
        for i, char in enumerate(st.session_state.char_list):
            cols = st.columns([1.5, 3, 2, 3, 1])
            cols[0].text_input("id", value=char["id"], disabled=True, key=f"id_{i}", label_visibility="collapsed")
            char["role"] = cols[1].text_input("role", value=char["role"], key=f"role_{i}", label_visibility="collapsed")
            char["suggest_casting"] = cols[2].checkbox("Yes", value=char["suggest_casting"], key=f"sugg_{i}")
            char["already_cast"] = cols[3].text_input("already", value=char["already_cast"], key=f"cast_{i}", label_visibility="collapsed")
            
            # 削除ボタン
            if cols[4].button("➖", key=f"del_{i}"):
                st.session_state.char_list.pop(i)
                st.rerun()
                
        # 追加ボタン (※StreamlitのテーマCSS干渉を避けるため、typeをPrimaryからあえて外す)
        if st.button("➕", key="add_char"):
            next_id = f"$c{len(st.session_state.char_list) + 1}"
            st.session_state.char_list.append(
                {"id": next_id, "role": "", "suggest_casting": True, "already_cast": ""}
            )
            st.rerun()
            
        # Analysis用に df 形式に変換しておく
        edited_df = pd.DataFrame(st.session_state.char_list)
        
    st.divider()
    
    with st.expander("Casting Preferences", expanded=True):
        st.info("💡 候補を絞り込むための物理的な条件（Constraints）と、AIに期待する提案の方向性（Intentions）を設定します。")
        st.markdown("##### Constraints", help="検索候補から完全に条件外の俳優を除外するための「物理的な制約」です。")
        # スライダーを半分程度の長さに短く見せるため、カラムで幅を制限する
        col_budget, _ = st.columns([1, 1])
        with col_budget:
            budget_cap_m = st.slider(
                "Budget Cap (Per Actor)", 
                min_value=1, max_value=50, value=50, step=1, format="$%dM",
                help="提案される各俳優の推定予算上限を設定します。このゲージを下げることで、予算オーバーの極端な高額A級スターを候補から弾くことができます。"
            )
        # バックエンドには(0.0, 1.0)の比率で渡す
        guarantee_range = (0.0, budget_cap_m / 50.0)
        
        st.divider()
        st.markdown("##### Intentions", help="AIが推薦ランキングを作成する際の「思考バイアス（意向）」です。複数を組み合わせることも可能です。")
        
        # 縦並びに変更
        unexpected_casting = st.checkbox(
            "Unexpected", 
            help="過去に今回の役柄タイプ（Archetype）を演じた履歴を持つ俳優を【強制的に除外】して検索します。結果として「普段はこんなタイプの役をやらない俳優」が意外なハマり役として提案されやすくなります。"
        )
        blockbuster_focus = st.checkbox(
            "Blockbuster",
            help="役柄テキストの類似度よりも、俳優の過去の興行・実績スコアを最優先して選定します。\\n※「Unexpected」と同時にONにすることで、『超大物スター俳優を、彼らが普段絶対にやらないような異常な役回りにアサインする』といったユニークなキャスティングも可能です！"
        )
            
    if st.button("Analyze Graph & Generate Casting Proposals", type="primary", use_container_width=True):
        if not plot_input or edited_df.empty:
            st.warning("Please provide both plot and character list.")
        else:
            with st.spinner("Analyzing Narrative Graph with LLM..."):
                try:
                    cast_mapping = edited_df.to_dict(orient="records")
                    
                    generator = GraphGenerator(model_name="gpt-4o", temperature=0.0)
                    graph = generator.generate(
                        title=title_input,
                        plot_text=plot_input,
                        cast_mapping=cast_mapping,
                        pre_mentioned=True
                    )
                    
                    st.session_state.scenario_graph = graph
                    
                    with st.spinner("Searching Vector Database & Calculating Scores..."):
                        db = SessionLocal()
                        try:
                            agent = CastingAgent(db)
                            results = agent.suggest_casting(
                                graph=graph,
                                cast_constraints=cast_mapping,
                                work_title=title_input,
                                unexpected_casting=unexpected_casting,
                                blockbuster_focus=blockbuster_focus,
                                target_guarantee_range=guarantee_range
                            )
                            st.session_state.casting_results = results
                        finally:
                            db.close()
                            
                    st.success("Analysis Complete.")
                except Exception as e:
                    st.error(f"Error during processing: {e}")

# --- Tab 2: Graph ---
with tab2:
    if st.session_state.scenario_graph:
        st.subheader("Narrative Structure")
        render_graph(st.session_state.scenario_graph)
        
        with st.expander("Raw Graph JSON Data"):
            st.json(st.session_state.scenario_graph.model_dump())
    else:
        st.info("「1. Scenario Setup」タブで「Analyze Graph & Generate Casting Proposals」を実行してください。")

# --- Tab 3: Proposals ---
with tab3:
    if st.session_state.casting_results is not None:
        results = st.session_state.casting_results
        if not results:
            st.warning("キャスティング提案が見つかりませんでした。条件設定（Casting Constraints）を見直してください。")
        else:
            for role_label, data in results.items():
                st.subheader(f"{role_label}")
                
                candidates = data.get("candidates", [])
                rationale = data.get("rationale", "")
                
                if rationale:
                    st.info(f"💡 **AI Agent Recommendation Rationale:**\\n\\n{rationale}")
                
                if not candidates:
                    st.warning("条件に合致する俳優が見つかりませんでした。")
                    st.divider()
                    continue
                    
                cols = st.columns(len(candidates))
                for i, c_data in enumerate(candidates):
                    with cols[i]:
                        st.markdown(f"### #{i+1} **{c_data['actor_name']}**")
                        
                        # Match score progress
                        prog_val = min(1.0, max(0.0, float(c_data['final_score'])))
                        st.progress(prog_val, text=f"Match Score: {c_data['final_score']:.2f}")
                        
                        st.caption("Score Breakdown")
                        st.markdown(f"""
                        - **Similarity**: {c_data['similarity']:.3f}
                        - **Past Success**: {c_data['success_score']:.3f}
                        - **Guarantee**: {c_data['guarantee_score']:.3f}
                        """)
                        
                        past_arch_str = f" ({c_data['past_archetype']})" if c_data.get('past_archetype') else ""
                        st.markdown(f"**Past Role**: `{c_data['past_role']}`{past_arch_str}<br>in *\"{c_data['past_work_title']}\"*", unsafe_allow_html=True)
                st.divider()
    else:
        st.info("AIからのキャスティング提案がここに表示されます。")
