# Build Log
One entry per module/function built or changed. Newest at bottom. IST timestamps.

<!-- TEMPLATE
## YYYY-MM-DD HH:MM IST — <module/function>
- **PRD ref:** FR-#
- **File:lines:** src/cachewhisper/<file>.py:12-88
- **Tests:** tests/test_<x>.py: PASS/FAIL (what was checked)
- **Test types used:** unit / invariant / determinism / integration / contract / statistical / leakage (CLAUDE.md §3)
- **Real run:** scripted episode summary, or live LLM smoke for LLM-facing code only; LLM calls used: N (cache hits: M)
- **Prompt check:** logs/prompts/<role>_<cond>.txt reviewed by <name> | n/a
- **Review:** self / gstack review; issues found + fixed
- **Built by:** <human> with Claude Code
- **Open issues / follow-ups:**
-->

## 2026-11-09 02:55 IST — FR-10 LLM client (config.py, llm.py, smoke.py)
- **PRD ref:** FR-10
- **File:lines:** src/cachewhisper/config.py:1-80, src/cachewhisper/llm.py:1-150, src/cachewhisper/smoke.py:1-65
- **Tests:** tests/test_llm.py: PASS (8 tests: allowlist refusal incl. non-:free openrouter, cache hit = no call, seed changes key, 429 backoff x3 then rotation, all-503 raises RateLimited, 400 propagates, 401 rotates, credit arithmetic + logging, hard cap)
- **Test types used:** unit, contract (fake _call)
- **Real run:** live smoke via scripts/smoke.sh: 7/7 Adaption hosted models listed, 6/6 configured Adaption models answered; groq 401, gemini 400 (no valid keys). Reasoning models (qwen3.5-397b, glm-5.2, qwen3.8-27b) return empty text at max_tokens=20; default raised to 2000. LLM calls used: ~16, credits ≈ 0.001
- **Prompt check:** n/a
- **Review:** self; smoke row-offset bug found and fixed before commit
- **Built by:** team with Claude Code
- **Open issues / follow-ups:** fallbacks need valid free keys if Adaption fails
