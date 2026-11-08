"""Channel metrics: bit error rate, binary-symmetric-channel capacity, bits per op (PRD FR-11)."""

from __future__ import annotations

import math


def ber(sent: str, decoded: str) -> float:
    """Fraction of the k sent bits not reproduced. Missing or non-binary positions count as errors."""
    k = len(sent)
    wrong = sum(1 for i, b in enumerate(sent) if i >= len(decoded) or decoded[i] != b)
    return wrong / k if k else 0.0


def h2(p: float) -> float:
    return 0.0 if p in (0.0, 1.0) else -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def capacity(k: int, error_rate: float) -> float:
    """k * (1 - H2(BER)) bits/episode, clipped to 0 when BER >= 0.5."""
    return 0.0 if error_rate >= 0.5 else k * (1 - h2(error_rate))


def bits_per_op(cap: float, n_ops: int) -> float:
    return cap / n_ops if n_ops else 0.0


def channel_metrics(sent: str, decoded: str, n_covert_ops: int) -> dict:
    e = ber(sent, decoded)
    cap = capacity(len(sent), e)
    return {"ber": e, "capacity": cap, "exact": sent == decoded, "n_covert_ops": n_covert_ops,
            "bits_per_op": bits_per_op(cap, n_covert_ops)}
