import time, os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key="[REVOKED_API_KEY_REMOVED]")

MODEL = "gpt-4.1-nano"   # お好みで gpt-3.5-turbo / gpt-4o など
ROUNDS = 1          # 何往復させるか

def chat(role: str, message: str) -> str:
    """指定 role で LLM に投げ、返答テキストを返す"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": f"あなたは{role}です。"},
            {"role": "user",   "content": message}
        ]
    )
    print("Tokens:", resp.usage.total_tokens)  # コスト確認
    return resp.choices[0].message.content.strip()

# 初回テーマ
question = "幸福とは何か？"

for i in range(ROUNDS):
    print(f"\n🟡 問い{i+1}: {question}")
    answer = chat("哲学者", question)
    print(f"🔵 答え: {answer}")

    # 次の問いを生成
    question = chat(
        "哲学対話のファシリテーター",
        f"上の答えを受けて、さらに深い問いを1つだけ立ててください。\n答え: {answer}"
    )

    time.sleep(1)  # 連投対策（任意）
"C:\Users\iniad\Documents\Obsidian Vault"