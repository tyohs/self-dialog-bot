"""
self_dialogue_obsidian.py
---------------------------------
AI 同士の自動対話ログを
1. Obsidian Vault に Markdown 保存
2. 感情スコア推移グラフ(PNG)を Vault に出力
3. トークン数と概算コストも記録

デフォルトを「爆発的ブレスト」モードにセット
"""

import argparse
import time
import datetime
import textwrap
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

# ── アマテラス概要 ─────────────────────────────────────
AMATERASU_OVERVIEW = textwrap.dedent("""
アマテラスプロトコル概要:
- 信頼の概念を数式化し暗号署名で検証可能にする
- オフラインでも端末間で信頼性の高い通信を確立
- 完全分散型で中央管理者が存在しない
- 量子計算耐性を含む強固なセキュリティとプライバシー保護
""").strip()
# ── CLI 引数 ───────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="AI×AI 対話→Obsidian 保存 (爆発的ブレストモード)")
parser.add_argument("--model", default="gpt-4.1-nano",
                    help="OpenAI モデル ID")
parser.add_argument("--rounds", type=int, default=1,
                    help="対話ターン数（推奨10〜20）")
parser.add_argument("--role_a", default="ディスラプター",
                    help="アイデアを爆発的に生み出す側のロール名")
parser.add_argument("--role_b", default="インキュベーター",
                    help="さらなる発散質問を行うロール名")
parser.add_argument(
    "--question",
    default=f"{AMATERASU_OVERVIEW}\n\n上記を踏まえ、アマテラスで解決できる『信頼欠如』を 1 つ挙げよ",
    help="初期質問 (アマテラス概要付き)"
)
parser.add_argument(
    "--vault",
    default=r"C:\Users\iniad\Documents\Obsidian Vault",  # ← ここを自分の Vault パスに
    help="Obsidian Vault の絶対パス"
)

args = parser.parse_args()

# ── OpenAI 初期化 ─────────────────────────────────────────
load_dotenv()
client = OpenAI()

# 4.1‑nano 単価（USD / 1M tokens）
IN_PRICE, OUT_PRICE = 0.20, 0.80
USD2JPY = 158

# ── Obsidian ファイル名など ─────────────────────────────
now = datetime.datetime.now()
stamp = now.strftime("%Y-%m-%d_%H-%M")
vault = Path(args.vault)
vault.mkdir(parents=True, exist_ok=True)

md_path = vault / f"AI対話_{stamp}.md"
png_path = vault / f"AI対話_{stamp}_感情.png"

# ── ユーティリティ ─────────────────────────────────────
analyzer = SentimentIntensityAnalyzer()
dialogue_pairs = []  # [(質問, 提案)]
sent_scores = []     # 各ターンの compound スコア

def yen(usd: float) -> int:
    return int(usd * USD2JPY)


def chat(role: str, msg: str):
    """指定ロールで質問を投げ、返答テキストと総トークン数を返す"""
    resp = client.chat.completions.create(
        model=args.model,
        messages=[
            {"role": "system", "content": f"あなたは{role}です。"},
            {"role": "user", "content": msg}
        ]
    )
    content = resp.choices[0].message.content.strip()
    tokens = resp.usage.total_tokens
    return content, tokens

# ── 対話ループ ─────────────────────────────────────────
q = args.question

tok_in = tok_out = 0

for turn in range(1, args.rounds + 1):
    print(f"\n🟡 アイデア{turn}: {q}")
    a, t_out = chat(args.role_a, q)
    print(f"🔵 提案(冒頭): {a[:120]}…")
    tok_out += t_out

    dialogue_pairs.append((q, a))
    sent_scores.append(analyzer.polarity_scores(a)["compound"])

    incubator_prompt = textwrap.dedent(f"""
        上記アイデアを踏まえ、これを**より独創的・大胆**に発展させる、
        あるいは**全く新しい角度**のアイデアを引き出す質問を 1 つだけ作ってください。
        アイデア: {a}
    """).strip()

    q, t_in = chat(args.role_b, incubator_prompt)
    tok_in += t_in
    time.sleep(1)

# ── 感情グラフ描画 (matplotlib) ─────────────────────────
plt.plot(range(1, len(sent_scores) + 1), sent_scores, marker="o")
plt.title("AI 対話 感情スコア推移 (VADER compound)")
plt.xlabel("ターン")
plt.ylabel("Score (-1〜1)")
plt.grid(True)
plt.savefig(png_path, dpi=160, bbox_inches="tight")
plt.close()

# ── Markdown 生成 & 書き込み ──────────────────────────
usd_cost = tok_in / 1e6 * IN_PRICE + tok_out / 1e6 * OUT_PRICE
lines = [
    f"# AI ブレストログ ({stamp})\n",
    f"- **モデル**: `{args.model}`  ",
    f"- **総トークン**: {tok_in + tok_out:,}  (入力 {tok_in:,} / 出力 {tok_out:,})  ",
    f"- **料金見積**: ${usd_cost:.4f} ≒ {yen(usd_cost):,} 円  ",
    f"- **感情グラフ**: ![[{png_path.name}]]\n",
]

for idx, (q_, a_) in enumerate(dialogue_pairs, 1):
    score = sent_scores[idx - 1]
    lines += [
        f"\n## アイデア {idx}\n{q_}\n",
        f"**提案**  (感情スコア: {score:+.3f})\n\n{a_}\n",
    ]

md_path.write_text("\n".join(lines), encoding="utf-8")
print("✅ Obsidian に Markdown & グラフを保存:", md_path.name)

# ── 完 ────────────────────────────────────────────────
