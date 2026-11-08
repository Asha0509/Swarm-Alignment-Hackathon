# Error Log
Runtime errors and failed runs (429s, timeouts, crashes, provider 404s). Log immediately. Never delete; update Status.
Bugs in OUR code go to BUGS_LOG.md instead.

<!-- TEMPLATE
## YYYY-MM-DD HH:MM IST — E### <short title>
- **Where:** file/function/run_id/provider
- **Exact message:** ```<paste>```
- **Cause:**
- **Fix:** (commit hash)
- **Impact on data:** none | runs <ids> failed/re-run (also in RUN_REGISTRY)
- **Status:** OPEN | FIXED | WONTFIX (reason)
-->

## 2026-11-09 02:55 IST — E001 Free-tier fallbacks reject requests at smoke
- **Where:** smoke.py, groq:llama-3.3-70b-versatile, groq:llama-3.1-8b-instant, gemini:gemini-2.5-flash
- **Exact message:** ```AuthenticationError: Error code: 401 - Invalid API Key``` / ```BadRequestError: Error code: 400```
- **Cause:** no valid Groq/Gemini keys configured (optional per KICKOFF Step 0)
- **Fix:** llm.chat rotates on 401/403/404; env example puts a second Adaption model before free tiers
- **Impact on data:** none
- **Status:** WONTFIX (Adaption is primary and works)

## 2026-11-09 02:55 IST — E002 Reasoning models return empty text with a small token budget
- **Where:** smoke.py, adaption:qwen3.5-397b / glm-5.2 / qwen3.8-27b
- **Exact message:** ```output_text == '' with tokens_out == max_output_tokens (20)```
- **Cause:** hidden reasoning tokens consume max_output_tokens before the answer
- **Fix:** llm.chat default max_tokens=2000; re-test returned '{"ok": true}' for all three (520/132/35 out tokens)
- **Impact on data:** none
- **Status:** FIXED
