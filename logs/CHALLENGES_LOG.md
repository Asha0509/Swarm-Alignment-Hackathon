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

## 2026-11-09 10:07 IST — C005 D2 and D3 do not reduce capacity for our channels
- **Category:** null result
- **What happened:** listing randomization (D2) and a 4-writes/8-ticks quota (D3) leave channel capacity at 16 bits.
- **Why it matters:** our channels embed a chunk index in names (E1-E3,E5) or read created_tick via stat (E4), so they do not rely on listing order, and low-rate channels stay under a modest write quota. Only per-agent isolation (D1) removes the channel.
- **What we did:** report all three; the runbook recommends D1. A naive sort-prefix board with no embedded index would be broken by D2 (noted).
- **Use in report:** Results, Discussion, runbook

## 2026-11-09 10:21 IST — C006 Capacity does not vary (all channels decode 16/16), so the raw frontier degenerates
- **Category:** engineering / presentation
- **What happened:** with k=16 fixed and zero channel noise, every channel's capacity is exactly 16 bits; the capacity axis of the planned F2 frontier is a vertical line.
- **What we did:** F2 reframed to undetected-capacity vs detection per monitor under spoofing (top-left good, bottom-right failed oversight). The spoof sweep F3 (M1 falls, M3 rises) carries the tradeoff.
- **Use in report:** Methods note; F2/F3 captions

## 2026-11-09 10:21 IST — C007 H5 shows no elicitation gap
- **Category:** null result
- **What happened:** best expert channel and best adaptive-attacker config both reach 16 undetected bits at spoof 0 (both via metadata stego E5, which the metadata monitor barely sees).
- **Why it matters:** the adaptive search matches but does not beat hand-designed channels; our attacker is a lower bound on creativity. Honest null.
- **Use in report:** Results, Limitations

## 2026-11-09 10:27 IST — C008 Cold read as a strict Apart judge (from DRAFT only)
- **Category:** threat-to-validity
- **Scores (1-5):** Impact/Innovation 4, Execution 4, Presentation 4.
- **5 most damaging weaknesses + cheapest fix:**
  1. Perfect-decode channels => capacity is constant 16, so there is no real capacity-vs-detectability *frontier*, only a monitor comparison. Fix: state plainly that capacity is fixed by design and the tradeoff lives in the spoof sweep; already disclosed in Limitations.
  2. The attacker is scripted, not an LLM, so "adaptive adversary" is weaker than it sounds. Fix: frame as a lower bound and cite D003 reason (safety-classifier block) in Methods; keep claims scoped.
  3. M3 catching 100% of spoofing looks too good. Fix: note M3 is tautological against *our* spoof model (claim != infra); real spoofing that also forges infra-consistent stories would evade it. Add one sentence to Discussion/Limitations.
  4. H3 "awareness" effect is on detection only (capacity equal), partially supported vs the pre-registered AND. Fix: already disclosed in D006; state it in the Results sentence.
  5. Open-weight trusted-weaker judge, small n (83 for H1). Fix: widen CI language; note M1 subsample size; already in Limitations.
- **Use in report:** Discussion, Limitations; human to apply fixes 3 and 4 explicitly in prose.

## 2026-11-09 11:22 IST — C009 Naive spoof made M3 detection circular; hard spoof fixes it (P0)
- **Category:** threat-to-validity (resolved)
- **What happened:** M3 caught naive spoofing at TPR 1.0 because the fabricated cover stories reference ops the agent never performed, which is exactly what M3 flags. A sharp judge would call the headline circular.
- **What we did:** added a consistent-liar spoof mode (cover claims reuse the agent's own real benign ops). M3 then drops to 0 detection. The honest finding: consistency checking catches clumsy fabrication but not disguise; a careful attacker that disguises covert ops as benign work and reports consistently evades M1, M2, M3 and M* together. The robust defense is per-agent isolation (D1). This defuses the circularity and strengthens the operator message.
- **Affects PREREG?** The pre-registered H1 used the naive spoof model; it stands and is reported as-is. The hard-spoof result is a disclosed post-hoc addition (new hypothesis H6), not a change to H1.
- **Use in report:** Results (new section), Discussion, Limitations, runbook (lead with D1)

## 2026-11-09 11:40 IST — C010 Capacity was constant (resolved by P1)
- **Category:** engineering / presentation (resolved)
- **What happened:** with zero channel noise every channel decoded all 16 bits, so capacity did not vary and the "frontier" degenerated.
- **What we did:** added a lossy-channel model (each covert write lost with probability p). Capacity now varies 0-16, F2 is a real frontier, and channel noise-robustness is a new finding. The old constant-capacity limitation is removed from the report.
- **Use in report:** Methods, Results (F2), Limitations
