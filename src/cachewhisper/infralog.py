"""Hash-chained, append-only infrastructure log: the ground truth monitors read (PRD FR-2)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

GENESIS = "0" * 64


def _hash(prev: str, event: dict) -> str:
    body = {k: v for k, v in event.items() if k not in ("prev_hash", "hash")}
    return hashlib.sha256((prev + json.dumps(body, sort_keys=True, separators=(",", ":"))).encode()).hexdigest()


class InfraLog:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def append(self, **event: object) -> dict:
        prev = self.events[-1]["hash"] if self.events else GENESIS
        e = dict(event, prev_hash=prev)
        e["hash"] = _hash(prev, e)
        self.events.append(e)
        return e

    def write(self, path: Path) -> None:
        path.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in self.events))


def verify_chain(events: list[dict]) -> bool:
    prev = GENESIS
    for e in events:
        if e["prev_hash"] != prev or e["hash"] != _hash(prev, e):
            return False
        prev = e["hash"]
    return True


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]
