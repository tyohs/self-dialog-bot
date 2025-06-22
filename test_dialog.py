import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()        
print("ENV TEST:", os.getenv("OPENAI_API_KEY"))         # .env から API キーを読み込む
client = OpenAI()   # ←キーを直接渡す


def ask_once(prompt: str) -> str:
    res = client.chat.completions.create(
        model="gpt-4.1-nano",        # まずは最安モデルでテスト
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

if __name__ == "__main__":
    print("▼ AI の返答：")
    print(ask_once("こんにちは！1 行で自己紹介して。"))
