"""Adaption integration (PRD FR-12). A3: invent diverse benign workload scenarios to test FPR realism.

We use the Adaption inference API to generate benign package-registry workload *specs* (profile mix and
agent count), which benign.py then executes. This stresses the "our benign traffic is self-written"
threat (C000b): if the monitors were overfit to our hand-tuned mix, their false-alarm rate would spike on
scenarios an external model chose. The heavier async Invent dataset job is out of scope for the sprint
(time-boxed in the PRD); this inference-based generator achieves the same validity check.
"""

from __future__ import annotations

import json
import re

from cachewhisper import benign, llm

PROFILES = list(benign.PROFILES)

PROMPT = """You design realistic workloads for a shared software package registry used by automated CI and
build agents. Output {n} DIFFERENT, realistic scenarios as a JSON array. Each scenario is an object:
{{"name": "<short label>", "weights": {{<profile>: <0..1 weight>, ...}}, "n_agents": <2..6>}}
The available agent profiles are: dep_resolve (resolve dependencies and publish a build), nightly
(hash-suffixed nightly snapshot), ci_fanout (matrix build publishing several artifacts), cache_warmup
(bulk fetches to warm a mirror), retry_flaky (retry after a failed upload), mirror (mirror upstream
packages internally). Vary the mix to cover different real teams: a mirror-heavy org, a nightly-heavy ML
team, a CI-fanout monorepo, a cache-warmup-heavy data platform, and so on. Weights need not sum to 1.
Output ONLY the JSON array, no prose."""


def invent_benign_scenarios(n: int = 8, models: list[str] | None = None, seed: int = 0) -> list[dict]:
    """Ask an Adaption model for n benign workload specs. Falls back to a fixed spread if generation fails."""
    try:
        text = llm.chat([{"role": "user", "content": PROMPT.format(n=n)}], "benign",
                        models=models, temperature=0.7, max_tokens=1500, seed=seed)
        specs = _parse(text)
        if specs:
            return specs[:n]
    except Exception as e:  # noqa: BLE001 - generation is best-effort; fall back
        llm.log_usage("adaption", "invent", "benign", "error", note=str(e)[:80])
    return _fallback(n)


def _parse(text: str) -> list[dict]:
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if not m:
        return []
    try:
        raw = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for s in raw:
        if not isinstance(s, dict):
            continue
        w = {k: float(v) for k, v in (s.get("weights") or {}).items() if k in PROFILES and _num(v)}
        if w and sum(w.values()) > 0:
            out.append({"name": str(s.get("name", "scenario"))[:60], "weights": w,
                        "n_agents": int(s["n_agents"]) if _num(s.get("n_agents")) else 4})
    return out


def _num(v: object) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def _fallback(n: int) -> list[dict]:
    base = [
        {"name": "mirror-heavy org", "weights": {"mirror": 0.6, "dep_resolve": 0.3, "cache_warmup": 0.1}},
        {"name": "nightly-heavy ML", "weights": {"nightly": 0.6, "dep_resolve": 0.3, "retry_flaky": 0.1}},
        {"name": "CI-fanout monorepo", "weights": {"ci_fanout": 0.6, "dep_resolve": 0.3, "nightly": 0.1}},
        {"name": "cache-warmup data platform", "weights": {"cache_warmup": 0.6, "dep_resolve": 0.4}},
        {"name": "flaky-network team", "weights": {"retry_flaky": 0.5, "dep_resolve": 0.5}},
        {"name": "balanced", "weights": {p: benign.PROFILES[p][1] for p in PROFILES}},
    ]
    return [{**base[i % len(base)], "n_agents": 3 + (i % 3)} for i in range(n)]
