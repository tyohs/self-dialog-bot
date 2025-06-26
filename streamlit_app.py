import streamlit as st, random
from pathlib import Path
from datetime import datetime
from self_dialogue_core import run_dialogue, _call   # _call を要約で再利用

# ── Obsidian 保存先 ────────────────────────────
OBSIDIAN_VAULT = r"C:\Users\iniad\Documents\Obsidian Vault"

# ── Streamlit 設定 ─────────────────────────────
st.set_page_config(page_title="AI Dialogue Plus", layout="wide")
st.title("🧠 AI Dialogue – Extended Edition")

# ── Sidebar：役割・プロンプト設定 ───────────────
with st.sidebar:
    st.header("🛠 役割・プロンプト")
    role_q    = st.text_input("質問役 (名前)", "質問者")
    system_q  = st.text_area( "質問役 System Prompt",
                              "あなたは質問を作るAIです。", height=90)

    role_a    = st.text_input("回答役 (名前)", "回答者")
    system_a  = st.text_area( "回答役 System Prompt",
                              "あなたは質問に答えるAIです。", height=90)

    st.header("📋 初期設定")
    init_question = st.text_input("初期質問", "幸福とは何か？")
    tok_lim       = st.number_input("最大トークン (0=∞)",
                                    0, 100_000, 0, step=1000)

# ── セッションステート初期化 ─────────────────────
if "log" not in st.session_state:
    st.session_state.log: list[str] = []
if "engine" not in st.session_state:
    st.session_state.engine = dict(question=init_question,
                                   turn=0,
                                   total_tok=0)

engine = st.session_state.engine

# ── ボタン配置 ────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1: next_btn    = st.button("▶ 次ターン", use_container_width=True)
with col2: summary_btn = st.button("📝 要約",    use_container_width=True)
with col3: spice_btn   = st.button("🌶️ スパイス", use_container_width=True)
with col4: save_btn    = st.button("💾 Save→Obsidian", use_container_width=True)

# ── 共通 UI 出力関数 ───────────────────────────
def ui_out(line: str):
    st.session_state.log.append(line)
    st.write(line)

# ── 次ターン実行 ────────────────────────────
def run_one_turn(q_prompt: str,
                 sys_q: str = system_q,
                 sys_a: str = system_a):
    tok, next_q = run_dialogue(
        init_question=q_prompt,
        rounds=1,
        role_q=role_q,
        role_a=role_a,
        system_q=sys_q,
        system_a=sys_a,
        model="gpt-4.1-nano",
        ui=ui_out,
        max_tokens=(tok_lim or None),
    )
    engine["total_tok"] += tok
    engine["question"]   = next_q

# ▶ 次ターン
if next_btn:
    engine["turn"] += 1
    run_one_turn(engine["question"])

# 📝 要約
if summary_btn and st.session_state.log:
    summary, _ = _call(
        model="gpt-3.5-turbo",
        system="あなたは優秀なサマライザーAIです。150字以内で要約してください。",
        user="\n".join(st.session_state.log)
    )
    st.markdown("### ✨ 要約")
    st.info(summary)

# 🌶️ スパイス
SPICES = [
    "回答を俳句で！", "次の問いはラップ調で！", "例え話を1つ入れて！",
    "絵文字を3個だけ使え！", "シェイクスピア調で！"
]
if spice_btn:
    spice_cmd = random.choice(SPICES)
    st.warning(f"🌶️ スパイス指令: **{spice_cmd}**")
    run_one_turn(
        engine["question"],
        sys_q=system_q + f"\n# 追加指令: {spice_cmd}",
        sys_a=system_a + f"\n# 追加指令: {spice_cmd}",
    )

# 乱入フォーム
with st.form("user_form"):
    usr_msg = st.text_input("🙋 乱入メッセージ")
    exec_usr = st.form_submit_button("送信")
if exec_usr and usr_msg:
    st.write(f"**あなた**: {usr_msg}")
    st.session_state.log.append(f"**あなた**: {usr_msg}")
    engine["turn"] += 1
    run_one_turn(usr_msg)

# 💾 Obsidian 保存
def save_markdown(lines: list[str]) -> Path:
    Path(OBSIDIAN_VAULT).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    path = Path(OBSIDIAN_VAULT) / f"dialog_{ts}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

if save_btn and st.session_state.log:
    md_lines = ["# 対話ログ"] + st.session_state.log + \
               [f"\n**Total**: {engine['total_tok']:,} tok"]
    saved = save_markdown(md_lines)
    st.success(f"🪄 Saved to Obsidian: {saved}")
