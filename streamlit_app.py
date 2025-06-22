import streamlit as st, glob, os
from self_dialogue_core import run_template

st.set_page_config(page_title="AI Dialogue (Template)", layout="wide")
st.title("🧠 Template-driven AI Dialogue")

tpl_files = [os.path.basename(p)[:-5] for p in glob.glob("templates/*.toml")]

if not tpl_files:
    st.error("templates フォルダに *.toml がありません。")
    st.stop()

tpl_name = st.sidebar.selectbox("テンプレを選択", tpl_files)
rounds   = st.sidebar.slider("Max Turns", 1, 100, 10)
tok_lim  = st.sidebar.number_input("Tok Limit (0=∞)", 0, 100_000, 0, step=1000)

if st.sidebar.button("▶ 実 行", use_container_width=True):
    st.session_state.log = []

    def ui(line: str):
        st.session_state.log.append(line)
        st.write(line)

    total = run_template(
        tpl_name=tpl_name,
        model="gpt-4.1-nano",
        rounds=rounds,
        ui=ui,
        max_tokens=(tok_lim or None),
    )

    st.success(f"✅ Finished | {total:,} tokens")

    md = ["# 対話ログ\n"] + st.session_state.log + [f"\n**Total**: {total:,} tok"]
    st.download_button("💾 Markdown ダウンロード",
                       "\n".join(md),
                       file_name=f"{tpl_name}.md",
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

    run_template(
        tpl_name=tpl_name,
        model="gpt-4.1-nano",
        rounds=1,
        ui=lambda x: (st.session_state.log.append(x), st.write(x)),
        max_tokens=(tok_lim or None),
        extra_state={"user_msg": usr_msg}
    )
