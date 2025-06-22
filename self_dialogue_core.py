from __future__ import annotations
import time
from typing import Callable

from dotenv import load_dotenv
from openai import OpenAI

# ----------------- API 初期化 -----------------
load_dotenv()           # .env から OPENAI_API_KEY を読み込む
client = OpenAI()

# モデルごとの参考単価（入力, 出力）USD / 1M tokens
PRICE = {
    "gpt-4.1-nano":  (0.20, 0.80),
    "gpt-3.5-turbo": (0.50, 1.50),
}

# ----------------- 1 回問い合わせ -----------------
def _chat(model: str, role_prompt: str, user_msg: str) -> tuple[str, int]:
    """
    system に role_prompt, user に user_msg を入れて呼び出し。
    戻り値 = (テキスト, 使用トークン数)
    """
    rsp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user",   "content": user_msg},
        ]
    )
    return rsp.choices[0].message.content.strip(), rsp.usage.total_tokens

# ----------------- メインループ -----------------
def run_dialogue(
        init_question: str = "幸福とは何か？",
        rounds: int = 5,
        role_q: str = "質問者",
        role_a: str = "回答者",
        model: str = "gpt-4.1-nano",
        ui: Callable[[str], None] = print,
        max_tokens: int | None = None,
        max_usd: float  | None = None,
) -> int:
    """
    role_q が質問を生成し、role_a が回答。
    ui コールバックに対話ログを流しつつ、最後に総トークン数を返す。
    """
    in_tok = out_tok = 0
    price_in, price_out = PRICE.get(model, (0.0, 0.0))
    question = init_question

    for turn in range(1, rounds + 1):
        ui(f"🟡 問い{turn}: {question}")

        # ---- 回答側 ----
        answer, tok_out = _chat(model, f"あなたは{role_a}です。", question)
        ui(f"🔵 {role_a}: {answer}")
        out_tok += tok_out

        # ---- 次の問いを作成 (質問側) ----
        question, tok_in = _chat(
            model,
            f"あなたは{role_q}です。",
            f"上の答えを踏まえ、さらに深い問いを1つだけ立ててください。\n答え:{answer}"
        )
        in_tok += tok_in

        # ---- 自動停止判定 ----
        total_tok = in_tok + out_tok
        usd = in_tok/1e6*price_in + out_tok/1e6*price_out
        if (max_tokens and total_tok >= max_tokens) or \
           (max_usd and usd >= max_usd):
            ui(f"🚨 Stop (Tok {total_tok:,} / ${usd:.3f})")
            break

        time.sleep(0.2)   # 速すぎ防止

    return in_tok + out_tok
