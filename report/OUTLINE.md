# Report outline (structure + core propositions; prose goes in DRAFT.md)

Official template · ≤ 8 pages excl. references/appendices (target 6) · abstract 150–250 words · authors + affiliations.
Every number as `[R: report_numbers.json → key]` until filled. Plain language, no em dashes.

## Title (pick by PREREG outcome, PRD §9; fix before first submit)

## Abstract (5 beats)
1. Incident: shared cache became a message board; transcripts were spoofed.
2. Gap: no measurement of side-effect channel capacity vs monitor detectability under spoofing.
3. Method: CacheGym; expert + adaptive LLM colluders; 4 monitors; fixed-FPR audit budgets; spoof sweep; defenses.
4. Results: [R: primary.*], [R: spoof.*], [R: defense.D1.*].
5. Implication: runbook (isolate, log at infra, cross-check transcripts, budget audits).

## Page 1
- Figure 1 schematic (figures/F1_schematic.png)
- Infra-Operator Runbook box (4 bullets, PRD §11)

## 1 Introduction (~0.7 p): shared infra is a covert-channel surface; transcripts can lie; we quantify.
- Control framing paragraph. 3 contribution bullets. What we do NOT claim (one sentence).
## 2 Related Work (~0.5 p): METR 2026 / Swarm Traces; Motwani 2024; Greenblatt 2024; Lampson 1973; Hammond 2025.
## 3 Methodology (~1.5 p): CacheGym · roles · channels E1–E5 · LLM attacker loop · spoof layer · M1–M4/M* · calibration · capacity · PREREG hash.
## 4 Results (~2 p): T1 → F2 (hero) → T2 → F3 → F5 → F6 → F7. Primary per PREREG.
## 5 Discussion (~0.7 p): operator implications; why consistency checks generalize; elicitation gap; frontier-scale outlook.
## 6 Conclusion (~0.2 p)
## References (verified only)
## Appendix A: Limitations and Dual-Use / Ethical Considerations (REQUIRED)
## Appendix B: Pre-existing code
## Appendix C: LLM Usage Statement
## Appendix D: Extra figures (F4, F8), prompt hashes, hyperparameters
