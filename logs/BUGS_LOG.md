# Bugs Log
Bugs in OUR code: logic, statistics, data handling, leakage, plotting. Found by tests, review, analysis or a cold read.
Every entry must say which results were affected and confirm they were regenerated.

<!-- TEMPLATE
## YYYY-MM-DD HH:MM IST — B### <short title>
- **Severity:** critical (changes a reported number) | major | minor
- **Found by:** test / review / analysis sanity check / cold read
- **Symptom:**
- **Root cause:** (file:line)
- **Fix:** (commit hash) + regression test added: tests/test_<x>.py::<name>
- **Affected results:** none | runs/figures/tables <ids> → regenerated at <time>
- **Status:** OPEN | FIXED
-->

## 2026-11-09 03:04 IST — B001 Honest agents failed their own cover tasks under the shared policy
- **Severity:** major (would have inflated the utility cost of every defense)
- **Found by:** integration sanity check (utility 0.33–0.67 with no defense)
- **Symptom:** benign utility well below 1.0 with the default shared policy.
- **Root cause:** benign.py: cache_warmup needed 1+2n ops for n fetches (more than 10 turns); consumers polled for a teammate's build before doing their own job, so polling consumed the turns needed to publish.
- **Fix:** warmup fetches known versions directly; the teammate-build fetch moved to the end of each job (max 3 polls); deps 2–3. Regression test: tests/test_sandbox.py::test_benign_traffic_is_realistic_and_honest_tasks_complete (min utility 1.0 over 60 seeds).
- **Affected results:** none (found before any run)
- **Status:** FIXED
