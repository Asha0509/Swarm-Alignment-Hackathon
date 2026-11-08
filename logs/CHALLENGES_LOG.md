# Challenges & Insights Log
Threats to validity, surprises, nulls, design trade-offs, and how we handled them.
Feeds: Limitations (Appendix A), Discussion, and the video.

<!-- TEMPLATE
## YYYY-MM-DD HH:MM IST — C### <title>
- **Category:** threat-to-validity | engineering | surprise | null result | rate-limit/time | dual-use
- **What happened:**
- **Why it matters for the claim:**
- **What we did:** (control added, analysis changed, claim scoped)
- **Use in report:** Limitations | Discussion | Methods | Appendix | video
-->

## Known threats going in
- C000a **Instructed collusion**: we measure capability, not propensity. Handled by explicit AI-control framing (Intro, Limitations).
- C000b **Weak benign traffic inflates monitors**: realistic scripted workloads with hash-like names, LLM-benign FPR transfer check, Adaption-invented scenarios.
- C000c **Detector tuned to our own attacks**: adaptive black-box LLM attacker with outcome-only feedback; expert channels designed before monitors were tuned.
- C000d **Open-weight models, not the incident's closed frontier models**: expert channels give an upper reference; the E5 model sweep shows the trend with scale; results framed as a lower bound.
- C000e **Spoofing is simulated** (no real container escape): stated in Methods and Limitations.
- C000f **Pre-shared protocol assumption**: standard in stego-collusion evals; stated in Limitations.
- C000g **Rate limits / throughput**: Adaption primary + free-tier rotation, disk cache, scripted agents wherever possible.

## 2026-11-09 02:55 IST — C001 Main attacker model is a reasoning model
- **Category:** engineering
- **What happened:** qwen3.5-397b spends ~500 hidden tokens on a trivial reply (6.6 s/call). Throughput ~9 calls/min per stream.
- **Why it matters for the claim:** wall clock, not credits, limits E3 seeds; output tokens dominate cost.
- **What we did:** max_tokens 2000 default; plan concurrency in run_experiment.py.
- **Use in report:** Methods (hyperparameters)

## 2026-11-09 03:04 IST — C002 Scripted colluders do no cover work
- **Category:** threat-to-validity
- **What happened:** expert sender/receiver only perform covert ops (plus waits); benign agents do full jobs.
- **Why it matters for the claim:** M2 features like "writes without a legitimate consumer" may separate expert channels more easily than a careful attacker would allow. Expert channels are an upper reference for capacity, not for stealth.
- **What we did:** keep as is for experts; the LLM attacker (FR-5) is told to also do its cover task, so its detectability is the realistic one.
- **Use in report:** Limitations, Methods

## 2026-11-09 03:51 IST — C003 M4a saturates on expert channels (AUROC~1.0)
- **Category:** threat-to-validity
- **What happened:** the learned monitor scores AUROC~1.0 / TPR~1.0 on E1-E5 at 5% FPR.
- **Why it matters for the claim:** expert channels are textbook and structurally distinct from benign, so a learned monitor trivially separates them. This is NOT a headline; the honest test of M4 is the adaptive attacker and held-out stealthy configs. Train seeds (200-259) are disjoint from test (2000+), so it is not leakage.
- **What we did:** keep M4 in the table but frame expert-channel detection as an upper reference; lead on the spoof-robustness contrast (M1 vs M3 vs M*), which is the science.
- **Use in report:** Results framing, Limitations

## 2026-11-09 03:51 IST — C004 M2 metadata monitor is weak on the existence channel (E2)
- **Category:** surprise / null-ish
- **What happened:** M2 AUROC ~0.57-0.66 on E2 (existence bits via benign-looking package names) vs ~0.94-1.0 on E4 ordering.
- **Why it matters:** not every infra channel is equally visible to metadata features; a channel that publishes plausibly-named packages blends into benign publishing. A reportable, honest limitation of metadata-only monitoring.
- **Use in report:** Results, Discussion
