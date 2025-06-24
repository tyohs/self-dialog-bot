from __future__ import annotations
import time
from typing import Callable, Dict
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

PRICE = {"gpt-4.1-nano": (0.20, 0.80)}          # (input, output) USD/1M tok

def _call(model: str, system: str, user: str) -> tuple[str, int]:
    """OpenAI Chat を 1 回呼び出して (text, tokens) を返す"""
    rsp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ]
    )
    return rsp.choices[0].message.content.strip(), rsp.usage.total_tokens


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
) -> int:
    """
    1ターン目:  init_question を 質問役(role_q) が提示 → 回答役が答える
    2ターン目～: 回答役の答えを元に 質問役 が次の問いを生成 → 回答役が答える
    """
    q = init_question
    in_tok = out_tok = 0
    price_in, price_out = PRICE.get(model, (0, 0))

    for turn in range(1, rounds + 1):
        # 質問を表示
        ui(f"🟡 **{role_q}**: {q}")

        # 回答役が答える
        ans, t_out = _call(model, system_a, q)
        ui(f"🔵 **{role_a}**: {ans}")
        out_tok += t_out

        # 次ターンの質問を生成（最終ターンなら不要）
        if turn < rounds:
            q, t_in = _call(
                model,
                system_q,
                f"上の答えを踏まえ、さらに深い問いを1つだけ立ててください。\n答え:{ans}"
            )
            in_tok += t_in

        # コスト制御
        tot_tok = in_tok + out_tok
        usd = in_tok/1e6*price_in + out_tok/1e6*price_out
        if (max_tokens and tot_tok >= max_tokens) or \
           (max_usd and usd >= max_usd):
            ui(f"🚨 Stop (Tok {tot_tok:,} / ${usd:.3f})")
            break

        time.sleep(0.2)

    return in_tok + out_tok
