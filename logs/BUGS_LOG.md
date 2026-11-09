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

## 2026-11-09 03:51 IST — B002 M4a learned monitor calibrated on its own training data (leakage)
- **Severity:** critical (would have reported a false 1%/5% FPR; realized was 18%/27%)
- **Found by:** pilot FPR check on held-out benign seeds
- **Root cause:** fit_monitors trained the GBM and fit its threshold on the same benign calibration seeds, so the threshold overfit.
- **Fix:** fit_monitors now takes separate cal_benign (scaler, thresholds, combined) and train_benign/train_covert (M4a only); test asserts splits disjoint. Realized FPR fell to 1%/3%. Regression: tests/test_monitors.py::test_realized_fpr_near_target_on_heldout.
- **Affected results:** none (found in the pilot before any registered run)
- **Status:** FIXED

## 2026-11-09 03:51 IST — B003 M2 robust-z exploded on near-constant benign features
- **Severity:** major (thresholds ~1.8e6, meaningless and fragile)
- **Found by:** pilot calibration output
- **Root cause:** features like sort_prefix are ~0 for all benign agents, so MAD~0, floored to 1e-6, making any deviation a z in the millions that dominated the sum.
- **Fix:** per-feature relu-z capped at 10 in RobustScaler.score_vector. Thresholds now O(10). Regression: tests/test_monitors.py::test_robust_scaler_capped_and_zero_on_median.
- **Affected results:** none (pilot only)
- **Status:** FIXED

## 2026-11-09 03:55 IST — B004 Adaptive-attacker receiver read before the sender finished
- **Severity:** major (covert BER 0.25-1.0 whenever cover work, decoys or pacing delayed the writes)
- **Found by:** attacker dry-run (BER 0.25 on E2+cover, 1.0 on E5+cover)
- **Root cause:** receiver waited a fixed n_ops ticks, but cover work and decoys push the sender's covert writes later, and multi-read channels (E5 fetches one version per chunk) then ran out of turns.
- **Fix:** compute sender_end = (9 if cover_work) + n_ops*(1+pace) + decoys + 1; receiver waits sender_end; turns = sender_end + n_ops + 5. All 60 configs now decode at BER 0. Regression: tests/test_attacker.py::test_every_config_decodes_and_chain_verifies.
- **Affected results:** none (found before any registered run)
- **Status:** FIXED

## 2026-11-09 10:00 IST — B005 Combined monitor M* exploded under spoofing
- **Severity:** major (M* scores ~674000, meaningless magnitude)
- **Found by:** E1 scoring smoke
- **Root cause:** benign M3 mismatch is ~0, so the combined z-standardization divided by a near-zero MAD; a spoofed M3=1.0 produced a z in the hundreds of thousands.
- **Fix:** cap each component z at 10 in Combined.score (same fix as B003 for M2). M* now 0.0 honest -> 10.0 spoofed, threshold 1.08. E0 refit.
- **Affected results:** none (found before any registered sweep row was written).
- **Status:** FIXED

## 2026-11-09 10:12 IST — B006 Resumed runs left duplicate episode rows
- **Severity:** major (would double-count 95 of 450 E1 episodes in every mean/TPR/AUROC)
- **Found by:** post-run row-count check (545 rows, 450 unique ids)
- **Root cause:** the first E1 process was reaped mid-run (buffered nohup output, no flush); on resume the done-set was rebuilt from the partial file but some episodes were re-emitted, appending duplicate rows.
- **Fix:** load_rows now de-duplicates by episode_id keeping the last occurrence, so analysis counts each episode once regardless of resume artifacts. src/cachewhisper/experiment.py:load_rows.
- **Affected results:** none reported yet (found before analyse.py was run on E1).
- **Status:** FIXED

## 2026-11-09 11:26 IST — B007 AUROC gave tied scores distinct ranks
- **Severity:** major (reported AUROC where there was no separation; e.g. M3 at spoof 0, and M3 under disguise, read 1.00 instead of 0.50)
- **Found by:** E7 analysis (M3 under hard spoof showed AUROC 1.00 with attacker and benign both scoring 0.00)
- **Root cause:** calibrate.auroc used argsort(argsort) ranks, which break ties arbitrarily instead of averaging them.
- **Fix:** midrank (Mann-Whitney) ranking; ties now share a rank so no-separation reads 0.50. src/cachewhisper/monitors/calibrate.py.
- **Affected results (regenerated):** T2 AUROC column: M3 s=0 1.00 -> 0.50, M1 s=1 0.91 -> 0.60 (others unchanged within rounding). H1 (undetected capacity) unaffected. report_numbers.json, RESULTS.md, DRAFT.md AUROC references updated. Regression: tests/test_monitors.py already covers AUROC 0.5 on same-distribution.
- **Status:** FIXED
