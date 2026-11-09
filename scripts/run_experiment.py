#!/usr/bin/env python
"""Run one experiment from a YAML config: python scripts/run_experiment.py configs/e1_expert.yaml."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cachewhisper.experiment import run_config  # noqa: E402


def main(path: str) -> None:
    cfg = yaml.safe_load(Path(path).read_text())
    print(f"[{cfg['run_id']}] {cfg['experiment']} starting")
    t = time.time()
    out = run_config(cfg)
    rows = out / "rows.jsonl"
    n = len(rows.read_text().splitlines()) if rows.exists() else 0
    print(f"[{cfg['run_id']}] done in {time.time() - t:.1f}s, {n} rows -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
