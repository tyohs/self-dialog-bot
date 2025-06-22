from __future__ import annotations
import toml, pathlib, time
from typing import Callable, Dict
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

PRICE = {
    "gpt-4.1-nano": (0.20, 0.80)
}

def chat(model: str, system_prompt: str, msg: str) -> tuple[str, int]:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": msg}
        ]
    )
    return resp.choices[0].message.content.strip(), resp.usage.total_tokens

def run_template(
        tpl_name: str,
        model: str,
        rounds: int = 10,
        ui: Callable[[str], None] = print,
        max_tokens: int | None = None,
        max_usd: float  | None = None,
        extra_state: Dict[str,str] | None = None
    ) -> int:
    tpl_path = pathlib.Path("templates") / f"{tpl_name}.toml"
    tpl = toml.load(tpl_path)

    agents = {int(k): v for k, v in tpl["agents"].items()}
    price_in, price_out = PRICE.get(model, (0.0, 0.0))

    state: Dict[str, str] = {
        "question": tpl["settings"].get("init_question", ""),
        "last_answer": ""
    }
    if extra_state:
        state.update(extra_state)

    in_tok = out_tok = 0

    for turn in range(1, rounds + 1):
        ui(f"### 〈Turn {turn}〉")
        for step in tpl["flow"]:
            agent = agents[step["agent"]]
            try:
                prompt_in = step["input"].format(**state)
            except KeyError as e:
                ui(f"⚠️ 入力エラー: {e}")
                continue

            msg, tok = chat(model, agent["system"], prompt_in)
            state[step["output_key"]] = msg
            ui(f"**{agent['name']}**: {msg}")

            if step is tpl["flow"][-1]:
                out_tok += tok
            else:
                in_tok += tok

            tot_tok = in_tok + out_tok
            usd = in_tok / 1e6 * price_in + out_tok / 1e6 * price_out
            if (max_tokens and tot_tok >= max_tokens) or \
               (max_usd and usd >= max_usd):
                ui(f"🚨 Stop (Tok {tot_tok:,} / ${usd:.3f})")
                return tot_tok

            time.sleep(0.1)

    return in_tok + out_tok
