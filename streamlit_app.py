from decimal import Decimal

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from self_dialogue_core import DialogueError, run_dialogue

load_dotenv()
st.set_page_config(page_title="AI Dialogue", layout="wide")
st.title("🧠 AI Dialogue Customizer")

with st.sidebar:
    st.header("🛠 役割とプロンプト")
    role_q = st.text_input("質問役（名前）", "質問者")
    system_q = st.text_area("質問役 System Prompt", "あなたは質問を作るAIです。")
    role_a = st.text_input("回答役（名前）", "回答者")
    system_a = st.text_area("回答役 System Prompt", "あなたは質問に答えるAIです。")
    st.header("📋 実行パラメータ")
    init_question = st.text_input("初期質問", "幸福とは何か？")
    rounds = st.slider("ラウンド数", 1, 20, 5)
    token_limit = st.number_input("最大トークン（0=無制限）", 0, 100_000, 0, step=1000)
    usd_limit = st.number_input("最大料金 USD（0=無制限）", 0.0, 10.0, 0.0, step=0.01)
    run_button = st.button("▶ 実行", use_container_width=True)

if run_button:
    log: list[str] = []

    def show_event(role: str, content: str) -> None:
        line = f"**{role}**: {content}"
        log.append(line)
        st.markdown(line)

    try:
        result = run_dialogue(
            client=OpenAI(),
            init_question=init_question,
            rounds=rounds,
            role_q=role_q,
            role_a=role_a,
            system_q=system_q,
            system_a=system_a,
            max_tokens=token_limit or None,
            max_usd=Decimal(str(usd_limit)) if usd_limit else None,
            on_event=show_event,
        )
    except (DialogueError, ValueError) as exc:
        st.error(str(exc))
    else:
        usage = result.usage
        st.success(
            f"完了 ({result.stop_reason}) | "
            f"入力 {usage.prompt_tokens:,} / 出力 {usage.completion_tokens:,} / "
            f"合計 {usage.total_tokens:,} | ${result.cost_usd:.6f}"
        )
        markdown = ["# 対話ログ", *log, f"\n**Stop reason**: {result.stop_reason}"]
        st.download_button("💾 Markdown ダウンロード", "\n\n".join(markdown), "dialogue.md")
