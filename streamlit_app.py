import streamlit as st
from self_dialogue_core import run_dialogue

st.set_page_config(page_title="Simple AI Dialogue", layout="wide")
st.title("🧠 Simple AI Dialogue (質問役⇄回答役)")

# ---------- サイドバー設定 ----------
with st.sidebar:
    init_q  = st.text_input("初期質問", "幸福とは何か？")
    rounds  = st.slider("ラウンド数", 1, 50, 5)
    model   = st.selectbox("モデル", ["gpt-4.1-nano", "gpt-3.5-turbo"])
    tok_lim = st.number_input("最大トークン (0=∞)", 0, 100_000, 0, step=1000)
    usd_lim = st.number_input("最大料金 USD (0=∞)", 0.0, 20.0, 0.0, step=0.5)

    role_q  = st.text_input("質問役", "質問者")
    role_a  = st.text_input("回答役", "回答者")

    run_btn = st.button("▶ 実 行", use_container_width=True)

# ---------- 実行 ----------
if run_btn:
    st.session_state.log = []             # 実行のたびにログをリセット

    def ui_out(line: str):
        st.session_state.log.append(line)
        st.write(line)

    total_tok = run_dialogue(
        init_question=init_q,
        rounds=rounds,
        role_q=role_q,
        role_a=role_a,
        model=model,
        ui=ui_out,
        max_tokens=(tok_lim or None),
        max_usd=(usd_lim  or None),
    )

    st.success(f"✅ Finished | {total_tok:,} tokens")

    # ---------- Markdown ダウンロード ----------
    md = ["# 対話ログ\n"] + st.session_state.log + [f"\n**Total**: {total_tok:,} tok"]
    st.download_button("💾 Markdown ダウンロード",
                       "\n".join(md),
                       file_name="dialogue.md",
                       mime="text/markdown")
