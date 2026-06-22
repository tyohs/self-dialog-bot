from decimal import Decimal
from types import SimpleNamespace

import pytest

from self_dialogue_core import (
    DialogueError,
    DialogueResponseError,
    TokenUsage,
    calculate_cost,
    run_dialogue,
)


def response(text: str | None, prompt: int = 10, completion: int = 5):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        usage=SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion),
    )


class FakeCompletions:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = next(self.responses)
        if isinstance(item, Exception):
            raise item
        return item


def client_with(*responses):
    completions = FakeCompletions(responses)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


def defaults(client, **overrides):
    values = {
        "client": client,
        "init_question": "first question",
        "rounds": 2,
        "role_q": "questioner",
        "role_a": "answerer",
        "system_q": "ask deeply",
        "system_a": "answer clearly",
    }
    values.update(overrides)
    return values


def test_dialogue_sequence_and_events():
    client, completions = client_with(
        response("first answer"), response("second question"), response("second answer")
    )
    events = []

    result = run_dialogue(
        **defaults(client), on_event=lambda role, text: events.append((role, text))
    )

    assert [(turn.question, turn.answer) for turn in result.turns] == [
        ("first question", "first answer"),
        ("second question", "second answer"),
    ]
    assert events == [
        ("questioner", "first question"),
        ("answerer", "first answer"),
        ("questioner", "second question"),
        ("answerer", "second answer"),
    ]
    assert "first answer" in completions.calls[1]["messages"][1]["content"]
    assert len(completions.calls) == 3


def test_usage_and_cost_are_accounted_by_api_fields():
    client, _ = client_with(response("answer", 100, 20))
    result = run_dialogue(**defaults(client, rounds=1))

    assert result.usage == TokenUsage(prompt_tokens=100, completion_tokens=20)
    assert result.usage.total_tokens == 120
    assert result.cost_usd == Decimal("0.000036")
    assert calculate_cost("gpt-4.1-nano", result.usage) == result.cost_usd


def test_token_limit_stops_before_next_question_call():
    client, completions = client_with(response("answer", 6, 4))
    result = run_dialogue(**defaults(client, rounds=5, max_tokens=10))

    assert result.stop_reason == "max_tokens"
    assert len(result.turns) == 1
    assert len(completions.calls) == 1


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"rounds": 0}, "rounds"),
        ({"init_question": "  "}, "init_question"),
        ({"model": "unknown"}, "Unsupported model"),
        ({"max_tokens": 0}, "max_tokens"),
        ({"max_usd": Decimal("0")}, "max_usd"),
    ],
)
def test_invalid_configuration(overrides, message):
    client, _ = client_with()
    with pytest.raises(ValueError, match=message):
        run_dialogue(**defaults(client, **overrides))


@pytest.mark.parametrize("bad_response", [response(""), response(None), SimpleNamespace()])
def test_empty_or_incomplete_response_is_rejected(bad_response):
    client, _ = client_with(bad_response)
    with pytest.raises(DialogueResponseError):
        run_dialogue(**defaults(client, rounds=1))


def test_api_error_is_wrapped_without_live_request():
    client, _ = client_with(RuntimeError("network detail"))
    with pytest.raises(DialogueError, match="OpenAI request failed"):
        run_dialogue(**defaults(client, rounds=1))
