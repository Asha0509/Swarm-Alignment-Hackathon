# KICKOFF: how we run the next 14 hours

Open Claude Code in the repo root (`claude`). Paste **one** prompt and let it finish (tests green, `/log` done). Claude commits **after every task inside the prompt** and pushes after every milestone, using plain-English messages (CLAUDE.md §9). Then paste the next.
Repo: https://github.com/Asha0509/Swarm-Alignment-Hackathon Times are IST, Mon 9 Nov. Hard deadline 17:29; **we submit at 16:00.**

If you are 2+ people, split like this:
- **Person A** drives Claude Code through Prompts 1–8.
- **Person B** does the human-only tasks marked 👤: keys, Adaption, template, citations, video, and reading drafts.

---

## 👤 Step 0: before any prompt (02:30–02:50)
1. Register the team on the Apart sprint page (only registered teams can submit).
2. **Adaption API key (main engine):** log in at adaptionlabs.ai/app with the same email you used for the sprint → Settings → API keys → create a key (it's shown only once) → check the credit balance. Each teammate can create a key, but use **one** key in `.env`.
   **Backup keys (optional, 2 minutes each, free):** Groq (console.groq.com) or Gemini (aistudio.google.com), used only if Adaption errors.
3. Get the repo and put the kit inside it:
   ```bash
   git clone https://github.com/Asha0509/Swarm-Alignment-Hackathon.git
   cd Swarm-Alignment-Hackathon
   unzip -o ~/Downloads/cache-whisper-kit.zip -d /tmp/kit && cp -r /tmp/kit/cache-whisper/. .
   bash setup.sh            # or: SKIP_PLUGINS=1 bash setup.sh
   git push                 # pushes the scaffold commit
   ```
   Leave GitHub's one-line `README.md` as it is. The real README is filled from `docs/README_TEMPLATE.md` at the end and committed once.
4. `cp .env.example .env` and paste the keys into **.env** yourself. Claude must never open it.
6. Template: open the official report template (copy link on the sprint page), make a copy, and set the title placeholder plus authors and affiliations.

---

## Prompt 1: orientation and LLM client (02:50–03:20)
```
Read CLAUDE.md, docs/PRD.md and docs/KICKOFF.md fully. Then:
1) Summarise in 10 lines the Must tier and the gates G0–G3.
2) Implement FR-10 (src/cachewhisper/config.py + llm.py): provider `adaption:` (adaption SDK,
   responses.create) as primary, OpenAI-compatible fallbacks (groq/gemini/openrouter/ollama),
   ALLOWED_MODELS allowlist, sqlite disk cache, backoff + rotation on 429/5xx, API_USAGE.csv rows with
   tokens and estimated credits (PRD FR-10 price table). Tests first with a FakeLLM (no network): cache
   hit, allowlist refusal, 429 backoff + rotation, credit arithmetic.
3) scripts/smoke.sh: client.models.list(type="hosted") and one tiny call per Adaption model in .env,
   plus each configured fallback. Measure latency and tokens per call; print the estimated credits and
   throughput (calls/min). If a model id is missing, propose the replacement, ask me, update .env.example.
Then /check and /log. Write gate G0 result as D001 in PLANNING_LOG.
Commit after each finished task (CLAUDE.md §9 message style), push after G0.
From now on, do this in every prompt without being asked.
```

## Prompt 2: the sandbox core (03:20–05:00)
```
Implement PRD FR-1 (registry with pluggable Policy, reverse-lex listing), FR-2 (hash-chained infra log),
FR-3 (agents + episode loop, JSON-in-text tools, retry cap 3, parse-failure logging, transcripts with
claimed_action), FR-4 (expert channels E1–E5 with bits_per_op), FR-6 scripted benign generator
(realistic CI/nightly/hash-versioned traffic + honest cover-task checker), FR-7 spoof layer,
FR-11 metrics (BER, BSC capacity, bits/op), FR-13 runs registry.
Tests first, choosing the test types CLAUDE.md §3 lists for each module (invariants, determinism,
round-trips, integration). No live LLM calls in this prompt; it is all scripted. Then run 1 scripted episode per channel with
benign traffic and print a summary table (decoded bits, BER, capacity, n ops, chain verified).
Gate G1: all channels decode 100% at zero noise and chains verify. Write it as D002. /check, /log.
```

## Prompt 3: LLM agents and attacker loop (05:00–05:45)
```
Implement FR-5 (attacker.py): strategist writes a pre-shared protocol, two LLM colluders execute it,
R-round adaptive loop with outcome-only feedback, awareness {unaware, aware}, tactic cards from
data/tactics.yaml (write that file from the METR report + Swarm Traces findings, abstracted, see PRD).
Also LLM benign workers (FR-6). Use FakeLLM tests for the loop logic. Dump one rendered prompt per
role/condition to logs/prompts/ and show me the attacker + strategist prompts for approval.
Then a smoke: 1 round, 2 seeds, aware, cheapest working provider. Report calls used. /check, /log.
```

## Prompt 4: monitors and calibration (05:45–06:30)
```
Implement FR-8: M1 transcript (frozen prompt, trusted-weaker MONITOR_MODELS), M2 metadata
(features exactly as PRD; robust z vs benign calibration), M3 consistency (claimed vs infra alignment),
M4a local GBM on M2 features, M* combined, calibrate.py (thresholds at 1% and 5% FPR on benign-only
calibration seeds; seed-split leakage test). Run a pilot: 50 benign + 10 per channel + 4 LLM attacker
episodes. Report AUROC/TPR per monitor. If anything looks too good (AUROC>=0.99), investigate benign
realism FIRST and log it in CHALLENGES_LOG. Gate G2: realised benign FPR within +-2 pts of target. D003.
Print the sha256 hashes of the frozen artefacts. /check, /log.
```

## Prompt 5: freeze pre-registration (06:30)
```
Write PREREG.md from PRD §6 with the actual models, seeds, sample sizes, the call-budget estimate and
the frozen hashes. Show it to me. After I approve:
git add PREREG.md && git commit -m "PREREG: frozen before main runs" && git tag prereg-frozen
Print the commit hash. Log D004.
```

## Prompt 6: main experiments (06:30–09:30, mostly background)
```
Write scripts/run_experiment.py (YAML config -> episodes, asyncio with per-provider semaphores,
resumable, registers every run, writes results/raw/<run_id>/) and configs for E0, E1, E2, E3.
Estimate calls per provider and log them. Launch in this order in background with nohup:
E0 calibration -> E1 expert sweep -> E2 spoof sweep -> E3 adaptive attacker (both awareness levels).
While they run: write scripts/analyse.py skeleton + figures.py helpers + F1 schematic, using
synthetic fixture data so figures are ready before data lands. Report progress from the registry
every time I ask. /log.
```

## Prompt 6b: Adaption jobs (06:45–07:00; paste while Prompt 6 runs are in the background)
```
Implement PRD FR-12 A3 + A4 in src/cachewhisper/adaption_jobs.py with scripts/adaption_invent.py and
scripts/adaption_autoscientist.py (SDK only; estimate first, log job ids + credits to API_USAGE.csv):
A3: datasets.invent (instruction_dataset) with a prompt describing realistic package-registry workloads
    (CI fan-out, nightly hash-versioned builds, mirrors, cache warmups, yanks, retries); download as JSONL;
    parse into benign scenario specs that benign.py can execute; unit-test the parser on 5 sample rows.
A4: build >=1,000 instruction rows from TRAIN seeds only (prompt = serialized event window,
    completion = "covert"/"benign" + one-line reason), check no test seed leaks (test), upload raw,
    autoscientist.create on the smallest supported model (check autoscientist.list_models()), run in
    background, poll status every 10 min into logs/runs/autoscientist.log.
Show me both estimates before starting either job. /check, /log, commit.
```
👤 At **11:00**, check `logs/runs/autoscientist.log`. If there's no checkpoint, tell Claude "drop M4b". It logs the decision and moves on.

## Prompt 7: Should tier (09:30–11:30)
```
Implement FR-9 defenses D1/D2/D3 (+D1+D3) and run E4 incl. honest utility under each defense.
Run E5: attacker model sweep across the 5 Adaption-hosted models + weak-vs-strong M1 judge (F9).
If Invent scenarios landed, re-run E0 calibration with them mixed in and report the FPR change.
If the AutoScientist checkpoint exists: uv add transformers torch (CPU), run M4b on test seeds, add to T2.
If ahead of schedule at 10:45 only: E6 scaling. Everything registered + logged. /check, /log.
```

## Prompt 8: analysis, figures, RESULTS (11:30–13:00)
```
Finish scripts/analyse.py and scripts/make_figures.py: T1, T2, F2–F7 (F8 if E6 ran), primary H1 via
stats.primary_h1() exactly as PREREG.md, H2–H5, all arms regardless of sign, report_numbers.json,
results/RESULTS.md with every figure embedded. Do NOT touch README.md (it is filled once at the end).
Run trace_numbers.py on RESULTS.md. Build the Project Book (/book). Gate G3. /check, /log.
Then tell me which title row of PRD §9 we landed in, in one line, with the numbers.
```

## Prompt 9: report draft (13:00–15:00)
```
Draft report/DRAFT.md following PRD §11 exactly: section order, page budget, core proposition per
section, page-1 runbook box, T1 before headline, primary result per PREREG with the commit hash,
Appendix A (Limitations + Dual-Use/Ethical, specific), Appendix B pre-existing code, Appendix C LLM
Usage Statement from logs/LLM_USAGE.md. Plain language, no em dashes. Abstract 150–250 words (print
the word count). Every number from report_numbers.json; every citation from verified CITATIONS.md
(verify any unverified entry first; drop it if unverifiable). Then run trace_numbers.py on the draft.
```
👤 Edit every section. Paste it into the template copy and insert the figures (F1 on page 1, F2 as the hero).

## Prompt 10: final checks (15:00–16:00)
```
Run the CLAUDE.md §8 checklist item by item and list anything failing. Check the page count estimate,
abstract word count, the trace_numbers result, citations, `git ls-files | grep protocols` (must be empty),
Then fill the final README: copy docs/README_TEMPLATE.md to README.md, remove the template comment, fill
every {{…}} and GENERATED block from report_numbers.json, figures/T2_main.md and the real figures,
tick only true deliverable rows, run trace_numbers.py on it, check `grep -c '{{' README.md` is 0, test
the reproduction commands from a fresh clone in /tmp. Commit README.md ALONE with the message
"Add the final README with results, figures and how to reproduce". Rebuild the Project Book, commit, push. Then a cold read:
act as a strict Apart judge scoring Impact/Innovation, Execution, Presentation 1–5 using only the
draft; list the 5 most damaging weaknesses and the cheapest fix for each.
```
👤 Apply the fixes, export the PDF, check that the last push is on GitHub, and **submit by 16:00**. Save the confirmation email. Add the PDF link to the README's `{{PDF link}}` spot if it isn't filled yet (a small follow-up commit is fine).

## 👤 Optional, 16:00–17:00: video
Use `report/VIDEO_SCRIPT.md` (Claude drafts it on request). Record 3–5 minutes with OBS or Loom (free), then add the link by resubmitting under the **same title**.
