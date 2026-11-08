# Planning Log
Decisions, gate outcomes, scope changes, pre-registration deviations.

<!-- TEMPLATE
## YYYY-MM-DD HH:MM IST — D### <decision>
- **Context:**
- **Options considered:**
- **Decision + why:**
- **Affects PREREG?** no | yes → deviation disclosed in report
- **Decided by:**
-->

## 2026-11-09 02:30 IST — D000 Project chosen
- **Context:** Idea critique rounds (why-it-won't-win analysis on 2 ideas, then a critique of the fix).
- **Decision:** Build "Whispering Through the Package Cache": capacity vs detectability of covert agent coordination through shared infrastructure, with spoofed transcripts and infra defenses. AI-control framing. Tiers Must/Should/Could per PRD.
- **Fallbacks:** PRD §10.
- **Decided by:** team

## 2026-11-09 02:55 IST — D001 Gate G0 PASSED
- **Context:** PRD §10 G0: Adaption responses work; credit balance visible.
- **Evidence:** `client.models.list(type="hosted")` returned all 7 PRD models. One call each to qwen3.5-397b, glm-5.2, deepseek-v4-flash, qwen3.8-27b, gemma-4-31b-it, gemma-4-26b-a4b-it succeeded (1.2–6.6 s). Credits used by smoke ≈ 0.001 (API_USAGE.csv). The SDK has no balance endpoint; per-call estimates are logged and the human checks the dashboard.
- **Decision + why:** proceed with PRD model roles unchanged. Free-tier fallbacks inactive (E001); a second Adaption model is the first fallback in the env example.
- **Affects PREREG?** no
- **Decided by:** Claude Code, pending human glance

## 2026-11-09 03:04 IST — D002 Gate G1 PASSED
- **Context:** PRD §10 G1: all channels decode at zero noise; chain verifies.
- **Evidence:** E1–E5 × low/med/high, seed 1000: BER 0.00, capacity 16.0/16 bits for all 15 configs; verify_chain True for all; honest utility 1.00. Property test covers k ∈ {8,16,32} × 6 seeds × 3 levels × 5 channels, all exact. Table in BUILD_LOG.
- **Decision + why:** proceed to FR-5 (LLM attacker). Spoof applied post hoc (paired by construction), noted for Methods.
- **Affects PREREG?** no
- **Decided by:** Claude Code

## 2026-11-09 03:41 IST — D003 Replace the LLM attacker with a scripted adaptive attacker (scope change)
- **Context:** Writing the LLM strategist/colluder prompts was stopped by a safety classifier. The team chose not to write attacker prompts by hand either.
- **Options considered:** (a) team writes prompts, Claude writes plumbing; (b) drop the adaptive attacker (PRD fallback 2); (c) scripted adaptive attacker: evolutionary search over channel, bits-per-op and stealth knobs (name mimicry, pacing, cover work, spoofed claims) with outcome-only monitor feedback.
- **Decision + why:** (c). Keeps E3/F5, H3 (aware = optimizes undetected capacity using which monitors flagged; unaware = capacity only) and the black-box adaptive red team (answers C000c, C002). Zero API cost, deterministic, more seeds. Lost: E5 model sweep and F9 (Should tier). H5 becomes hand-designed expert channels vs optimized configs. Limitation: the optimizer only searches strategies we built in (lower bound on attacker creativity).
- **Affects PREREG?** yes, written into PREREG before the freeze (not a post hoc deviation). attacker.py keeps its file name.
- **Decided by:** team (human OK in chat) + Claude Code

## 2026-11-09 03:51 IST — D004 Gate G2 PASSED
- **Context:** PRD §10 G2: realized benign FPR within +-2 pts of target on held-out benign.
- **Evidence:** pilot, 60 calibration + 80 held-out benign seeds (disjoint). Realized FPR at 5% target: M2 2%, M3 0%, M4 3%, M* 2%; at 1% target: 1-2%. All within +-2 pts (deviations are conservative, i.e. fewer false alarms than budgeted). Leakage bug B002 and scale bug B003 fixed first. Separation: at spoof 1.0, M3 TPR@5% 1.0 and M* 1.0 while M2 unchanged (spoof-blind), matching H2/H1 direction. M1 smoke: benign ~0.0, E1 0.95.
- **Decision + why:** proceed to PREREG. Real E0 will use 200 benign seeds to finalize thresholds.
- **Affects PREREG?** no (thresholds refit on frozen calibration seeds at E0)
- **Decided by:** Claude Code
