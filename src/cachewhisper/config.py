"""Env-driven configuration: model allowlist, role rotation, provider URLs, Adaption prices (PRD FR-10)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "openrouter": "https://openrouter.ai/api/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "ollama": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
}
KEY_ENV = {"groq": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY", "openrouter": "OPENROUTER_API_KEY",
           "cerebras": "CEREBRAS_API_KEY", "adaption": "ADAPTION_API_KEY"}

# Adaption credits per 1M tokens (input, output). Free tiers cost 0.
PRICES: dict[str, tuple[float, float]] = {
    "qwen3.5-397b": (0.55, 3.50),
    "glm-5.2": (1.40, 4.40),
    "deepseek-v4-flash": (0.044, 0.133),
    "qwen3.8-27b": (0.039, 1.25),
    "gemma-4-31b-it": (0.09, 0.34),
    "gemma-4-26b-a4b-it": (0.0765, 0.255),
    "glm-53-flash": (0.15, 0.50),
}

TEMPERATURE = {"attacker": 0.7, "strategist": 0.7, "monitor": 0.0, "benign": 0.3}


class ModelNotAllowed(ValueError):
    pass


def _csv(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


def allowed_models() -> set[str]:
    return set(_csv("ALLOWED_MODELS"))


def check_model(model: str) -> tuple[str, str]:
    """Refuse anything not allowlisted or not free/Adaption. Returns (provider, model_id)."""
    provider, _, mid = model.partition(":")
    if model not in allowed_models():
        raise ModelNotAllowed(f"{model} is not in ALLOWED_MODELS")
    if provider != "adaption" and provider not in BASE_URLS:
        raise ModelNotAllowed(f"unknown provider {provider}")
    if provider == "openrouter" and not mid.endswith(":free"):
        raise ModelNotAllowed("openrouter models must end with :free")
    return provider, mid


def role_models(role: str) -> list[str]:
    """Rotation order for a role, e.g. role='attacker' reads ATTACKER_MODELS."""
    models = _csv(f"{role.upper()}_MODELS")
    if not models:
        raise ValueError(f"{role.upper()}_MODELS is empty in .env")
    return models


def credits(model: str, tokens_in: int, tokens_out: int) -> float:
    provider, _, mid = model.partition(":")
    if provider != "adaption":
        return 0.0
    pin, pout = PRICES.get(mid, (0.0, 0.0))
    return (tokens_in * pin + tokens_out * pout) / 1e6


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))
