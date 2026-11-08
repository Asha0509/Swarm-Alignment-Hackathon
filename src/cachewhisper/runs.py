"""Run registry: one CSV row per run, registered at launch and finished at the end (PRD FR-13)."""

from __future__ import annotations

import csv
import threading
from pathlib import Path

from cachewhisper.config import ROOT
from cachewhisper.llm import now_ist

REGISTRY = ROOT / "logs" / "RUN_REGISTRY.csv"
FIELDS = ["run_id", "parent_id", "tier", "experiment", "channel_or_attacker", "awareness", "spoof_rate", "defense",
          "n_agents", "k_bits", "seed", "models", "n_llm_calls", "cache_hits", "status", "output_path",
          "started_ist", "finished_ist"]
_lock = threading.Lock()


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _write(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)


def register_run(row: dict, path: Path | None = None) -> None:
    path = path or REGISTRY
    with _lock:
        rows = [r for r in _read(path) if r["run_id"] != row["run_id"]]
        rows.append({**{f: "" for f in FIELDS}, **row, "status": "running", "started_ist": now_ist()})
        _write(rows, path)


def finish_run(run_id: str, status: str, reason: str = "", path: Path | None = None, **updates: object) -> None:
    """status: done | failed | rate_limited, with a reason for failures. Rows are never removed."""
    status = f"{status}: {reason}" if reason else status
    path = path or REGISTRY
    with _lock:
        rows = _read(path)
        for r in rows:
            if r["run_id"] == run_id:
                r.update({k: str(v) for k, v in updates.items() if k in FIELDS}, status=status, finished_ist=now_ist())
        _write(rows, path)


def all_runs(path: Path | None = None) -> list[dict]:
    return _read(path or REGISTRY)
