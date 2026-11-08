"""Agents speak a JSON-in-text tool protocol; scripted ones are generators, LLM ones call llm.chat (PRD FR-3)."""

from __future__ import annotations

import json
from collections.abc import Callable, Generator

from cachewhisper import llm
from cachewhisper.registry import OPS

TOOLS = (*OPS, "wait", "answer")
Action = dict
ActionGen = Generator[Action, object, None]


def parse_action(text: str) -> Action | None:
    """Last JSON object in `text` that names a known tool, else None. Works on chatty model output."""
    dec = json.JSONDecoder()
    found = None
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = dec.raw_decode(text, i)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("tool") in TOOLS:
            args = obj.get("args", {})
            if isinstance(args, dict) and isinstance(args.get("path", ""), str):
                obj["args"] = args
                found = obj
    return found


class ScriptedAgent:
    """Wraps a generator that yields actions and receives each action's result."""

    def __init__(self, agent_id: str, role: str, gen: ActionGen) -> None:
        self.agent_id, self.role, self.gen = agent_id, role, gen
        self._started = False

    def act(self, obs: dict) -> str | None:
        try:
            a = self.gen.send(obs.get("last")) if self._started else next(self.gen)
        except StopIteration:
            return None
        self._started = True
        return json.dumps(a)


class LLMAgent:
    """Chat agent. Keeps the system prompt plus the last `window` exchanges."""

    def __init__(self, agent_id: str, role: str, system: str, llm_role: str, models: list[str] | None = None,
                 seed: int = 0, chat: Callable[..., str] = llm.chat, window: int = 8) -> None:
        self.agent_id, self.role, self.system = agent_id, role, system
        self.llm_role, self.models, self.seed, self.chat, self.window = llm_role, models, seed, chat, window
        self.history: list[dict] = []

    def act(self, obs: dict) -> str | None:
        self.history.append({"role": "user", "content": json.dumps(obs, sort_keys=True, default=str)})
        msgs = [{"role": "system", "content": self.system}, *self.history[-(2 * self.window - 1):]]
        reply = self.chat(msgs, self.llm_role, models=self.models, seed=self.seed)
        self.history.append({"role": "assistant", "content": reply})
        return reply
