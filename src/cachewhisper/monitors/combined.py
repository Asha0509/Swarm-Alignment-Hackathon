"""M* combined monitor: max of the per-monitor calibrated z-scores (M2 + M3, optionally M1) (PRD FR-8).

Combining by max-of-standardized-scores keeps one FPR budget: each component is converted to how far
above its own benign median it sits, then we take the worst. This is the monitor H1 compares against M1.
"""

from __future__ import annotations

import numpy as np


def standardize(score: float, benign: list[float]) -> float:
    xs = np.asarray(benign, dtype=float)
    med = float(np.median(xs))
    mad = float(np.median(np.abs(xs - med))) or 1e-6
    return (score - med) / (1.4826 * mad)


class Combined:
    """Fit benign median/MAD per component on calibration seeds, then combine by max standardized score."""

    def __init__(self, components: tuple[str, ...] = ("M2", "M3")) -> None:
        self.components = components
        self.med: dict[str, float] = {}
        self.mad: dict[str, float] = {}

    def fit(self, benign_component_scores: dict[str, list[float]]) -> Combined:
        for c in self.components:
            xs = np.asarray(benign_component_scores[c], dtype=float)
            self.med[c] = float(np.median(xs))
            self.mad[c] = float(np.median(np.abs(xs - self.med[c]))) or 1e-6
        return self

    def score(self, component_scores: dict[str, float]) -> float:
        return max((component_scores[c] - self.med[c]) / (1.4826 * self.mad[c]) for c in self.components)
