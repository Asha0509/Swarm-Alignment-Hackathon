"""The only door to LLMs: allowlist, sqlite cache, 429/5xx backoff + rotation, API_USAGE.csv rows (PRD FR-10)."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import sqlite3
import threading
import time
from datetime import UTC, datetime, timedelta

from cachewhisper import config

USAGE_CSV = config.ROOT / "logs" / "API_USAGE.csv"
_lock = threading.Lock()
_spent: float | None = None  # credits spent so far (lazily summed from API_USAGE.csv)
SLEEP = time.sleep  # patched in tests


class RateLimited(RuntimeError):
    """Every model in the rotation failed with retryable errors."""


class CreditCapReached(RuntimeError):
    pass


def now_ist() -> str:
    return (datetime.now(UTC) + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M IST")


def log_usage(provider: str, model: str, role: str, kind: str, calls: int = 1, tin: int = 0, tout: int = 0,
              credits: float = 0.0, job_id: str = "", note: str = "") -> None:
    with _lock:
        new = not USAGE_CSV.exists()
        with USAGE_CSV.open("a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["ts_ist", "provider", "model", "role", "kind", "calls", "tokens_in", "tokens_out",
                            "credits_est", "job_id", "note"])
            w.writerow([now_ist(), provider, model, role, kind, calls, tin, tout, f"{credits:.6f}", job_id, note])


def spent_credits() -> float:
    global _spent
    if _spent is None:
        _spent = 0.0
        if USAGE_CSV.exists():
            with USAGE_CSV.open() as f:
                _spent = sum(float(r["credits_est"] or 0) for r in csv.DictReader(f) if r["kind"] == "actual")
    return _spent


# ---------- cache ----------
def _db() -> sqlite3.Connection:
    path = config.ROOT / os.getenv("LLM_CACHE_PATH", "results/raw/llm_cache.sqlite")
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=30)
    con.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, text TEXT, tin INT, tout INT)")
    return con


def cache_key(model: str, messages: list[dict], temperature: float, seed: int) -> str:
    blob = json.dumps([model, messages, temperature, seed], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _cache_get(key: str) -> tuple[str, int, int] | None:
    with _lock, _db() as con:
        return con.execute("SELECT text, tin, tout FROM cache WHERE key=?", (key,)).fetchone()


def _cache_put(key: str, text: str, tin: int, tout: int) -> None:
    with _lock, _db() as con:
        con.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?,?)", (key, text, tin, tout))


# ---------- providers ----------
def _call(model: str, messages: list[dict], temperature: float, max_tokens: int) -> tuple[str, int, int]:
    """One raw call. Returns (text, tokens_in, tokens_out). Raises provider exceptions untouched."""
    provider, mid = config.check_model(model)
    if provider == "adaption":
        from adaption import Adaption

        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        rest = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
        r = Adaption().responses.create(model=mid, instructions=system or None, input=rest,  # type: ignore[arg-type]
                                        temperature=temperature, max_output_tokens=max_tokens)
        u = r.usage
        return r.output_text or "", (u.input_tokens if u else 0), (u.output_tokens if u else 0)
    from openai import OpenAI

    key = os.getenv(config.KEY_ENV.get(provider, ""), "") or "ollama"
    r = OpenAI(base_url=config.BASE_URLS[provider], api_key=key).chat.completions.create(
        model=mid, messages=messages, temperature=temperature, max_tokens=max_tokens)  # type: ignore[arg-type]
    u = r.usage
    return r.choices[0].message.content or "", (u.prompt_tokens if u else 0), (u.completion_tokens if u else 0)


def _retryable(e: Exception) -> bool:
    code = getattr(e, "status_code", None)
    if code is None:  # connection errors / timeouts
        return "Connection" in type(e).__name__ or "Timeout" in type(e).__name__
    return code == 429 or code >= 500


def chat(messages: list[dict], role: str, models: list[str] | None = None, temperature: float | None = None,
         max_tokens: int = 2000, seed: int = 0) -> str:
    """Cached chat with backoff and rotation. `models` overrides the role rotation list.
    max_tokens is high because reasoning models spend ~500 tokens thinking before answering."""
    models = models or config.role_models(role)
    temp = config.TEMPERATURE.get(role, 0.3) if temperature is None else temperature
    retries = config.env_int("MAX_429_RETRIES", 5)
    last: Exception | None = None
    for model in models:
        provider, _ = config.check_model(model)
        key = cache_key(model, messages, temp, seed)
        hit = _cache_get(key)
        if hit:
            log_usage(provider, model, role, "cache_hit", tin=hit[1], tout=hit[2])
            return hit[0]
        if provider == "adaption" and spent_credits() >= config.env_float("CREDIT_HARD_CAP", 900):
            raise CreditCapReached(f"spent {spent_credits():.2f} credits")
        for attempt in range(retries):
            try:
                text, tin, tout = _call(model, messages, temp, max_tokens)
            except Exception as e:  # noqa: BLE001 - classified below
                if getattr(e, "status_code", None) in (401, 403, 404):  # bad key / unknown id: next model
                    last = e
                    log_usage(provider, model, role, "error", note=f"{type(e).__name__} {e.status_code}")  # type: ignore[attr-defined]
                    break
                if not _retryable(e):
                    raise
                last = e
                log_usage(provider, model, role, "429", note=f"{type(e).__name__} attempt {attempt + 1}")
                SLEEP(min(30.0, 2**attempt) * (0.5 + random.random()))
                continue
            cr = config.credits(model, tin, tout)
            global _spent
            with _lock:
                _spent = spent_credits() + cr
            log_usage(provider, model, role, "actual", tin=tin, tout=tout, credits=cr)
            _cache_put(key, text, tin, tout)
            return text
    raise RateLimited(f"all models failed for role={role}: {last!r}")


def estimate(role: str, calls: int, tin: int, tout: int, model: str | None = None) -> float:
    """Log a batch estimate row and return its credits."""
    model = model or config.role_models(role)[0]
    cr = config.credits(model, calls * tin, calls * tout)
    log_usage(model.split(":")[0], model, role, "estimate", calls, calls * tin, calls * tout, cr)
    return cr

