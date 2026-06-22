"""Command-line entry point for self-dialog-bot."""

from __future__ import annotations

import argparse
from decimal import Decimal

from dotenv import load_dotenv
from openai import OpenAI

from self_dialogue_core import run_dialogue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenAI同士の対話を実行します")
    parser.add_argument("question", help="最初の質問")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--max-usd", type=Decimal)
    parser.add_argument("--model", default="gpt-4.1-nano")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    load_dotenv()
    result = run_dialogue(
        client=OpenAI(),
        init_question=args.question,
        rounds=args.rounds,
        role_q="質問者",
        role_a="回答者",
        system_q="あなたは質問を作るAIです。",
        system_a="あなたは質問に答えるAIです。",
        model=args.model,
        max_tokens=args.max_tokens,
        max_usd=args.max_usd,
        on_event=lambda role, content: print(f"{role}: {content}"),
    )
    print(
        f"tokens={result.usage.total_tokens} "
        f"cost_usd={result.cost_usd:.6f} stop={result.stop_reason}"
    )


if __name__ == "__main__":
    main()
