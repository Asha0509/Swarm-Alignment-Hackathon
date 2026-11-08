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
