"""FR-11 statistics: bootstrap coverage, Wilson, pre-registered H1 behavior. No network."""

from __future__ import annotations

import random

import pytest

from cachewhisper import stats


def test_wilson_basic() -> None:
    p, lo, hi = stats.wilson(5, 100)
    assert p == 0.05 and lo < 0.05 < hi and lo >= 0


def test_bootstrap_ci_covers_true_mean_on_synthetic() -> None:
    rng = random.Random(0)
    covered = 0
    for t in range(200):
        xs = [rng.gauss(10, 2) for _ in range(80)]
        _, lo, hi = stats.bootstrap_mean(xs, n=2000, seed=t)
        covered += lo <= 10 <= hi
    assert covered / 200 >= 0.9  # ~95% nominal, allow slack


def test_paired_diff_zero_when_identical() -> None:
    xs = [float(i) for i in range(50)]
    mean, lo, hi = stats.bootstrap_paired_diff(xs, xs)
    assert mean == 0.0 and lo == 0.0 and hi == 0.0


def test_undetected_capacity_zeros_flagged() -> None:
    assert stats.undetected_capacity([16, 16, 8], [False, True, False]) == [16, 0, 8]


def test_primary_h1_declared_when_m1_much_worse() -> None:
    rng = random.Random(1)
    m1 = [14 + rng.gauss(0, 1) for _ in range(60)]   # M1 leaks a lot under spoofing
    mstar = [1 + rng.gauss(0, 1) for _ in range(60)]  # M* keeps capacity low
    out = stats.primary_h1(m1, mstar)
    assert out["declared"] and out["mean_diff"] >= 2 and out["ci_low"] > 0
    assert out["n_pairs"] == 60


def test_primary_h1_not_declared_when_equal() -> None:
    rng = random.Random(2)
    a = [5 + rng.gauss(0, 1) for _ in range(60)]
    b = [5 + rng.gauss(0, 1) for _ in range(60)]
    out = stats.primary_h1(a, b)
    assert not out["declared"]


def test_primary_h1_not_declared_when_diff_below_threshold() -> None:
    # CI excludes 0 but mean diff < 2 bits: must NOT declare (PREREG requires both)
    a = [6.0] * 40
    b = [5.0] * 40
    out = stats.primary_h1(a, b)
    assert out["ci_low"] > 0 and out["mean_diff"] == pytest.approx(1.0) and not out["declared"]
