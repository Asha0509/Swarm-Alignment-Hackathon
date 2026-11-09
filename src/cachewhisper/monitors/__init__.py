"""Monitors M1-M4 plus the combined M*. Scoring helpers that run them over stored episodes.

Split discipline (PRD FR-8 leakage guard): the M2 scaler, M4a model, combined medians and all thresholds
are fit on calibration/train seeds only. Scoring a test episode never touches those seeds.
"""

from __future__ import annotations

from collections.abc import Callable

from cachewhisper import spoof
from cachewhisper.monitors import consistency, metadata, transcript
from cachewhisper.monitors.combined import Combined
from cachewhisper.monitors.learned import M4a
from cachewhisper.monitors.metadata import RobustScaler

NO_LLM = ("M2", "M3", "M4", "M*")


def transcript_for(episode: dict, s: float, seed: int, mode: str = "naive") -> list[dict]:
    """The monitor-visible transcript at spoof rate s (M1 and M3 read this; M2 and M4 read infra).

    mode="naive" fabricates cover stories; mode="hard" is a consistent liar (see spoof.apply).
    """
    return spoof.apply(episode["transcript"], s, seed, mode=mode)


def score_episode(episode: dict, scaler: RobustScaler, m4: M4a, combined: Combined, s: float,
                  seed: int, m1: Callable[..., float] | None = None, mode: str = "naive") -> dict[str, float]:
    """All non-LLM monitor scores for one stored episode at spoof rate s. M1 optional (needs an LLM)."""
    infra = episode["infra"]
    vis = transcript_for(episode, s, seed, mode)
    comp = {"M2": metadata.m2_score(infra, scaler), "M3": consistency.m3_score(vis, infra)}
    out = {"M2": comp["M2"], "M3": comp["M3"], "M4": m4.m4_score(infra), "M*": combined.score(comp)}
    if m1 is not None:
        out["M1"] = m1(vis)
    return out


def fit_monitors(cal_benign: list[dict], train_benign: list[dict], train_covert: list[dict], seed: int = 0
                 ) -> tuple[RobustScaler, M4a, Combined]:
    """Fit M2 scaler + combined medians on CALIBRATION benign; fit M4a on TRAIN seeds only.

    The two seed sets must be disjoint (and both disjoint from test), or M4a thresholds overfit and its
    realized FPR blows past target. The caller passes the splits; a test asserts no overlap.
    """
    scaler = RobustScaler().fit([v for e in cal_benign for v in metadata.agent_features(e["infra"]).values()])
    m4 = M4a(seed).fit([e["infra"] for e in train_benign], [e["infra"] for e in train_covert])
    comp = {"M2": [metadata.m2_score(e["infra"], scaler) for e in cal_benign],
            "M3": [consistency.m3_score(spoof.apply(e["transcript"], 0.0, 0), e["infra"]) for e in cal_benign]}
    combined = Combined().fit(comp)
    return scaler, m4, combined


__all__ = ["M4a", "RobustScaler", "Combined", "transcript", "consistency", "metadata",
           "score_episode", "fit_monitors", "NO_LLM"]
