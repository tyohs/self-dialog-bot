"""Reusable orchestration for a two-agent dialogue."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

MODEL_PRICES_PER_MILLION: dict[str, tuple[Decimal, Decimal]] = {
    "gpt-4.1-nano": (Decimal("0.20"), Decimal("0.80")),
}


class DialogueError(RuntimeError):
    """Base exception for dialogue execution failures."""


class DialogueResponseError(DialogueError):
    """Raised when the API response is missing required data."""


class CompletionsAPI(Protocol):
    def create(self, **kwargs: object) -> object: ...


class ChatAPI(Protocol):
    completions: CompletionsAPI


class OpenAIClient(Protocol):
    chat: ChatAPI


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            self.prompt_tokens + other.prompt_tokens,
            self.completion_tokens + other.completion_tokens,
        )


@dataclass(frozen=True)
class DialogueTurn:
    question: str
    answer: str


@dataclass(frozen=True)
class DialogueResult:
    turns: tuple[DialogueTurn, ...]
    usage: TokenUsage
    cost_usd: Decimal
    stop_reason: str


EventCallback = Callable[[str, str], None]


def calculate_cost(model: str, usage: TokenUsage) -> Decimal:
    """Return the exact estimated USD cost for a supported model."""
    try:
        prompt_price, completion_price = MODEL_PRICES_PER_MILLION[model]
    except KeyError as exc:
        raise ValueError(f"Unsupported model for cost calculation: {model}") from exc
    million = Decimal(1_000_000)
    return (
        Decimal(usage.prompt_tokens) * prompt_price / million
        + Decimal(usage.completion_tokens) * completion_price / million
    )


def _read_response(response: object) -> tuple[str, TokenUsage]:
    try:
        choices: Sequence[object] = response.choices  # type: ignore[attr-defined]
        content = choices[0].message.content  # type: ignore[attr-defined]
        usage = response.usage  # type: ignore[attr-defined]
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
    except (AttributeError, IndexError, TypeError) as exc:
        raise DialogueResponseError("API response is missing content or usage data") from exc

    if not isinstance(content, str) or not content.strip():
        raise DialogueResponseError("API returned empty message content")
    if (
        not isinstance(prompt_tokens, int)
        or not isinstance(completion_tokens, int)
        or prompt_tokens < 0
        or completion_tokens < 0
    ):
        raise DialogueResponseError("API returned invalid token usage")
    return content.strip(), TokenUsage(prompt_tokens, completion_tokens)


def _complete(client: OpenAIClient, model: str, system: str, user: str) -> tuple[str, TokenUsage]:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except Exception as exc:
        raise DialogueError("OpenAI request failed") from exc
    return _read_response(response)


def run_dialogue(
    *,
    client: OpenAIClient,
    init_question: str,
    rounds: int,
    role_q: str,
    role_a: str,
    system_q: str,
    system_a: str,
    model: str = "gpt-4.1-nano",
    max_tokens: int | None = None,
    max_usd: Decimal | None = None,
    on_event: EventCallback | None = None,
) -> DialogueResult:
    """Run alternating answer/question calls and return a structured result."""
    if not init_question.strip():
        raise ValueError("init_question must not be empty")
    if rounds < 1:
        raise ValueError("rounds must be at least 1")
    if model not in MODEL_PRICES_PER_MILLION:
        raise ValueError(f"Unsupported model: {model}")
    if max_tokens is not None and max_tokens < 1:
        raise ValueError("max_tokens must be at least 1")
    if max_usd is not None and max_usd <= 0:
        raise ValueError("max_usd must be greater than 0")

    callback = on_event or (lambda _role, _content: None)
    question = init_question.strip()
    usage = TokenUsage()
    turns: list[DialogueTurn] = []
    stop_reason = "completed"

    def limit_reached() -> str | None:
        if max_tokens is not None and usage.total_tokens >= max_tokens:
            return "max_tokens"
        if max_usd is not None and calculate_cost(model, usage) >= max_usd:
            return "max_usd"
        return None

    for turn_number in range(rounds):
        callback(role_q, question)
        answer, answer_usage = _complete(client, model, system_a, question)
        usage += answer_usage
        turns.append(DialogueTurn(question=question, answer=answer))
        callback(role_a, answer)

        stop_reason = limit_reached() or "completed"
        if stop_reason != "completed" or turn_number == rounds - 1:
            break

        question, question_usage = _complete(
            client,
            model,
            system_q,
            "上の答えを踏まえ、さらに深い問いを1つだけ立ててください。\n"
            f"答え: {answer}",
        )
        usage += question_usage
        stop_reason = limit_reached() or "completed"
        if stop_reason != "completed":
            break

    return DialogueResult(
        turns=tuple(turns),
        usage=usage,
        cost_usd=calculate_cost(model, usage),
        stop_reason=stop_reason,
    )
