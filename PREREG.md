# Pre-registration: NOT YET FROZEN

> Written by Claude in KICKOFF Prompt 5 from docs/PRD.md §6, approved by the human, then committed
> ALONE and tagged `prereg-frozen` BEFORE the E1–E3 main runs. After that, this file never changes.
> Deviations go to logs/PLANNING_LOG.md and the report.

## Design (fill)
- Models (attacker / strategist / monitor / benign / second):
- Seeds and sample sizes per experiment:
- Defaults: k = 16, T = 10, n_benign = 3, Δ = 6, α ∈ {1%, 5%}
- Call-budget estimate:

## Primary outcome and contrast (H1)
- Undetected capacity at 5% FPR (bits/episode), per monitor.
- Contrast at spoof rate s = 1: M1 − M* (M* = M2+M3), paired bootstrap over all E1+E3 attack episodes,
  10,000 resamples, seed 0. Declared iff 95% CI lower bound > 0 AND mean difference ≥ 2 bits/episode.
- Computed ONLY by `cachewhisper.stats.primary_h1()` via `scripts/analyse.py`.

## Secondary (reported regardless of sign)
- H2 spoof · H3 awareness · H4 defense (D1 ≥ 80% capacity cut at ≤ 20-pt utility loss) · H5 elicitation gap

## Frozen artefacts (sha256)
- M1 prompt:
- M2 feature config:
- Strategist template:

**All results are reported regardless of sign.**
