from __future__ import annotations
import time
from typing import Callable
from dotenv import load_dotenv
from openai import OpenAI

# ── OpenAI 初期化 ──────────────────────────────
load_dotenv()                    # .env から OPENAI_API_KEY を取得
client = OpenAI()

# 入力／出力単価  (USD / 1M tokens)
PRICE = {"gpt-4.1-nano": (0.20, 0.80)}

# ── 1 回問い合わせヘルパ ───────────────────────
def _call(model: str, system: str, user: str) -> tuple[str, int]:
    """
    ChatCompletion を 1 回呼び出して
    戻り値 => (テキスト, 使用トークン数)
    """
    rsp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ]
    )
    return rsp.choices[0].message.content.strip(), rsp.usage.total_tokens


# ── メイン対話エンジン ─────────────────────────
def run_dialogue(
        init_question: str,
        rounds: int,
        role_q: str,
        role_a: str,
        system_q: str,
        system_a: str,
        model: str,
        ui: Callable[[str], None],
        max_tokens: int | None = None,
        max_usd:    float | None = None
) -> tuple[int, str]:
    """
    指定ラウンド分だけ AI⇄AI を実行し、
    戻り値 ⇒ (累計トークン数, 最終ラウンドで生成した次の質問)
    """
    question = init_question
    answer   = ""
    in_tok = out_tok = 0
    price_in, price_out = PRICE.get(model, (0, 0))

    for turn in range(1, rounds + 1):
        ui(f"🟡 **{role_q}**: {question}")

        # ── 回答フェーズ ──
        answer, t_out = _call(model, system_a, question)
        ui(f"🔵 **{role_a}**: {answer}")
        out_tok += t_out

        # ── 次の質問を生成（最終ターンは生成しない） ──
        if turn < rounds:
            prompt_q = (
                "上の答えを踏まえ、さらに深い問いを1つだけ立ててください。\n"
                f"答え:{answer}"
            )
            question, t_in = _call(model, system_q, prompt_q)
            in_tok += t_in

        # ── コスト制御 ──
        total_tok = in_tok + out_tok
        usd = in_tok/1e6*price_in + out_tok/1e6*price_out
        if (max_tokens and total_tok >= max_tokens) or \
           (max_usd    and usd       >= max_usd):
            ui(f"🚨 Stop (Tok {total_tok:,} / ${usd:.3f})")
            break

        time.sleep(0.2)

    return in_tok + out_tok, question