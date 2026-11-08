#!/usr/bin/env python3
"""Fail if a document contains a number that is not in report_numbers.json (anti-fabrication, PRD NFR-5).

Checks decimals (3.41), percentages (87.3%) and integers >= 100 that are not years.
Percent values are also matched as fractions (87.3% <-> 0.873). Skips fenced code and lines containing
`notrace`. Extra allowed literals: scripts/trace_allowlist.txt (one per line).

Usage: python scripts/trace_numbers.py [--numbers results/processed/report_numbers.json] FILE [FILE ...]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NUM = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(%?)(?![\w])")


def flatten(x: object) -> list[float]:
    if isinstance(x, bool):
        return []
    if isinstance(x, int | float):
        return [float(x)]
    if isinstance(x, dict):
        return [v for val in x.values() for v in flatten(val)]
    if isinstance(x, list | tuple):
        return [v for val in x for v in flatten(val)]
    return []


def matches(tok: str, pct: bool, pool: list[float]) -> bool:
    val = float(tok)
    dec = len(tok.split(".")[1]) if "." in tok else 0
    cands = [val, val / 100] if pct else [val]
    for c in cands:
        d = dec + (2 if (pct and c != val) else 0)
        tol = 0.5 * 10 ** (-d) + 1e-12
        if any(abs(p - c) <= tol for p in pool):
            return True
    return False


def needs_check(tok: str, pct: bool) -> bool:
    if pct or "." in tok:
        return True
    v = abs(int(tok))
    return v >= 100 and not (1900 <= v <= 2100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--numbers", default="results/processed/report_numbers.json")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    npath = Path(a.numbers)
    if not npath.exists():
        print(f"✘ {npath} not found. Run scripts/analyse.py first.")
        return 1
    pool = flatten(json.loads(npath.read_text()))
    allow_f = Path(__file__).with_name("trace_allowlist.txt")
    allow = set(allow_f.read_text().split()) if allow_f.exists() else set()
    bad: list[str] = []
    for f in a.files:
        p = Path(f)
        if not p.exists():
            continue
        in_code = False
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or "notrace" in line:
                continue
            for m in NUM.finditer(line):
                tok, pct = m.group(1), bool(m.group(2))
                if tok in allow or not needs_check(tok, pct):
                    continue
                if not matches(tok, pct, pool):
                    bad.append(f"{f}:{i}: {tok}{'%' if pct else ''}  | {line.strip()[:90]}")
    if bad:
        print(f"✘ {len(bad)} untraced number(s):")
        print("\n".join(bad))
        return 1
    print(f"✔ all numbers traced ({len(a.files)} file(s), {len(pool)} source values)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
