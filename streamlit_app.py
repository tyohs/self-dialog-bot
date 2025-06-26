import streamlit as st
from self_dialogue_core import run_dialogue

st.set_page_config(page_title="AI Dialogue", layout="wide")
st.title("🧠 AI Dialogue Customizer")

# ---------- サイドバー設定 ----------
with st.sidebar:
    st.header("🛠 役割とプロンプト")
    role_q = st.text_input("質問役 (名前)", "質問者")
    system_q = st.text_area("質問役 System Prompt",
                            "あなたは質問を作るAIです。", height=90)

    role_a = st.text_input("回答役 (名前)", "回答者")
    system_a = st.text_area("回答役 System Prompt",
                            "あなたは質問に答えるAIです。", height=90)

    st.header("📋 実行パラメータ")
    init_question = st.text_input("初期質問", "幸福とは何か？")
    rounds = st.slider("ラウンド数", 1, 20, 5)
    tok_lim = st.number_input("最大トークン (0=無制限)", 0, 100_000, 0, step=1000)

    run_btn = st.button("▶ 実 行", use_container_width=True)

# ---------- 実行 ----------
if run_btn:
    st.session_state.log = []

    def ui(line: str):
        st.session_state.log.append(line)
        st.write(line)

    total = run_dialogue(
        init_question=init_question,
        rounds=rounds,
        role_q=role_q,
        role_a=role_a,
        system_q=system_q,
        system_a=system_a,
        model="gpt-4.1-nano",
        ui=ui,
        max_tokens=(tok_lim or None),
    )

    st.success(f"✅ 完了 | 合計トークン: {total:,}")
    md = ["# 対話ログ\n"] + st.session_state.log + [f"\n**Total**: {total:,} tok"]
    st.download_button("💾 Markdown ダウンロード",
                       "\n".join(md),
                       file_name="dialogue.md",
                       mime="text/markdown")

# ---------- 乱入フォーム ----------
with st.form("user_form"):
    usr_msg = st.text_input("🙋 乱入メッセージ")
    exec_usr = st.form_submit_button("送信")

if exec_usr and usr_msg:
    if "log" not in st.session_state:
        st.session_state.log = []

    st.write(f"**あなた**: {usr_msg}")
    st.session_state.log.append(f"**あなた**: {usr_msg}")

    run_dialogue(
        init_question=usr_msg,
        rounds=1,
        role_q=role_q,
        role_a=role_a,
        system_q=system_q,
        system_a=system_a,
        model="gpt-4.1-nano",
        ui=lambda x: (st.session_state.log.append(x), st.write(x)),
    )
    """streamlit run streamlit_app.py"""
