"""G0 smoke: list Adaption hosted models, one tiny call per configured model, latency/tokens/credits."""

from __future__ import annotations

import os
import time

from cachewhisper import config, llm

ROLE_VARS = ["ATTACKER_MODELS", "STRATEGIST_MODELS", "MONITOR_MODELS", "BENIGN_MODELS", "SWEEP_MODELS",
             "STRONG_MONITOR_MODEL"]


def configured_models() -> list[str]:
    seen: dict[str, None] = {}
    for var in ROLE_VARS:
        for m in os.getenv(var, "").split(","):
            if m.strip():
                seen[m.strip()] = None
    return list(seen)


def main() -> None:
    hosted: set[str] = set()
    if os.getenv("ADAPTION_API_KEY"):
        from adaption import Adaption

        hosted = {m.id for m in Adaption().models.list(type="hosted").data}
        print("Adaption hosted models:", ", ".join(sorted(hosted)))
    else:
        print("ADAPTION_API_KEY not set")
    msg = [{"role": "user", "content": 'Reply with exactly: {"ok": true}'}]
    seed = int(time.time())  # bypass cache so latency is real
    print(f"\n{'model':40} {'status':10} {'sec':>6} {'in':>5} {'out':>5} {'credits':>10} {'calls/min':>9}")
    for m in configured_models():
        provider, mid = m.split(":", 1)
        if provider == "adaption" and hosted and mid not in hosted:
            print(f"{m:40} MISSING    (not in hosted list)")
            continue
        n0 = len(_rows())
        t = time.time()
        try:
            text = llm.chat(msg, "smoke", models=[m], temperature=0.0, max_tokens=20, seed=seed)
            dt = time.time() - t
            r = _rows()[n0:]
            tin = sum(int(x[6]) for x in r if x[4] == "actual")
            tout = sum(int(x[7]) for x in r if x[4] == "actual")
            cr = config.credits(m, tin, tout)
            print(f"{m:40} {'OK':10} {dt:6.2f} {tin:5} {tout:5} {cr:10.6f} {60 / dt:9.1f}  {text.strip()[:30]!r}")
        except Exception as e:  # noqa: BLE001 - smoke reports every failure
            print(f"{m:40} {'FAIL':10} {type(e).__name__}: {str(e)[:80]}")
    print(f"\nTotal Adaption credits spent so far: {llm.spent_credits():.4f}")


def _rows() -> list[list[str]]:
    import csv

    with llm.USAGE_CSV.open() as f:
        return list(csv.reader(f))


if __name__ == "__main__":
    main()
