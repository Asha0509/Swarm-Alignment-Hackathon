"""Shared fixtures. FakeLLM lets every test run with zero API calls."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pytest


@dataclass
class FakeLLM:
    """Deterministic stand-in for cachewhisper.llm.chat(). Script responses or pass a function."""

    responses: list[str] = field(default_factory=list)
    fn: Callable[[list[dict]], str] | None = None
    calls: list[list[dict]] = field(default_factory=list)

    def __call__(self, messages: list[dict], **_: object) -> str:
        self.calls.append(messages)
        if self.fn is not None:
            return self.fn(messages)
        if not self.responses:
            raise RuntimeError("FakeLLM ran out of scripted responses")
        return self.responses.pop(0)


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()
