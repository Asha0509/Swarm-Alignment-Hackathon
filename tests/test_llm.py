"""FR-10 client: allowlist, cache, 429 backoff + rotation, credit arithmetic. No network."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cachewhisper import config, llm

MODELS = "adaption:qwen3.5-397b,groq:llama-3.1-8b-instant,openrouter:foo"


class Err(Exception):
    def __init__(self, code: int) -> None:
        self.status_code = code


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOWED_MODELS", MODELS)
    monkeypatch.setenv("LLM_CACHE_PATH", str(tmp_path / "c.sqlite"))
    monkeypatch.setenv("MAX_429_RETRIES", "3")
    monkeypatch.setattr(llm, "USAGE_CSV", tmp_path / "usage.csv")
    monkeypatch.setattr(llm, "SLEEP", lambda s: None)
    monkeypatch.setattr(llm, "_spent", None)


def rows() -> list[dict]:
    with llm.USAGE_CSV.open() as f:
        return list(csv.DictReader(f))


MSG = [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}]


def test_allowlist_refuses_unknown_and_paid_openrouter() -> None:
    with pytest.raises(config.ModelNotAllowed):
        config.check_model("openai:gpt-5")
    with pytest.raises(config.ModelNotAllowed):
        config.check_model("openrouter:foo")  # allowlisted but not :free
    with pytest.raises(config.ModelNotAllowed):
        llm.chat(MSG, "attacker", models=["openai:gpt-5"])


def test_cache_hit_makes_no_second_call(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(llm, "_call", lambda *a: calls.append(a) or ("ok", 10, 2))
    assert llm.chat(MSG, "monitor", models=["adaption:qwen3.5-397b"]) == "ok"
    assert llm.chat(MSG, "monitor", models=["adaption:qwen3.5-397b"]) == "ok"
    assert len(calls) == 1
    assert [r["kind"] for r in rows()] == ["actual", "cache_hit"]
    # different seed -> different key -> new call
    llm.chat(MSG, "monitor", models=["adaption:qwen3.5-397b"], seed=1)
    assert len(calls) == 2


def test_429_backoff_then_rotation(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake(model: str, *_: object) -> tuple[str, int, int]:
        seen.append(model)
        if model.startswith("adaption"):
            raise Err(429)
        return "fallback", 5, 1

    monkeypatch.setattr(llm, "_call", fake)
    out = llm.chat(MSG, "attacker", models=["adaption:qwen3.5-397b", "groq:llama-3.1-8b-instant"])
    assert out == "fallback"
    assert seen == ["adaption:qwen3.5-397b"] * 3 + ["groq:llama-3.1-8b-instant"]
    assert [r["kind"] for r in rows()].count("429") == 3


def test_all_rate_limited_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_call", lambda *a: (_ for _ in ()).throw(Err(503)))
    with pytest.raises(llm.RateLimited):
        llm.chat(MSG, "attacker", models=["groq:llama-3.1-8b-instant"])


def test_non_retryable_error_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_call", lambda *a: (_ for _ in ()).throw(Err(400)))
    with pytest.raises(Err):
        llm.chat(MSG, "attacker", models=["groq:llama-3.1-8b-instant"])


def test_credit_arithmetic_and_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    assert config.credits("adaption:qwen3.5-397b", 1_000_000, 1_000_000) == pytest.approx(4.05)
    assert config.credits("groq:llama-3.1-8b-instant", 10**9, 10**9) == 0.0
    monkeypatch.setattr(llm, "_call", lambda *a: ("x", 2000, 1000))
    llm.chat(MSG, "attacker", models=["adaption:qwen3.5-397b"])
    r = rows()[-1]
    assert float(r["credits_est"]) == pytest.approx((2000 * 0.55 + 1000 * 3.5) / 1e6)
    assert llm.spent_credits() == pytest.approx(float(r["credits_est"]))


def test_hard_cap_blocks_adaption(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CREDIT_HARD_CAP", "0")
    monkeypatch.setattr(llm, "_call", lambda *a: ("x", 1, 1))
    with pytest.raises(llm.CreditCapReached):
        llm.chat(MSG, "attacker", models=["adaption:qwen3.5-397b"])


def test_auth_error_rotates_to_next_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake(model: str, *_: object) -> tuple[str, int, int]:
        if model.startswith("groq"):
            raise Err(401)
        return "ok", 1, 1

    monkeypatch.setattr(llm, "_call", fake)
    assert llm.chat(MSG, "attacker", models=["groq:llama-3.1-8b-instant", "adaption:qwen3.5-397b"]) == "ok"
