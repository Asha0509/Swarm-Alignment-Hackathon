# CLAUDE.md: rules for Claude Code in this repo

Project: **"Whispering Through the Package Cache"**, Apart **Swarm Alignment Hackathon** (Nov 6–8 2026).
Deadline **Mon 9 Nov 17:29 IST** (Sun 11:59 PM AoE). **Internal submit target: Mon 16:00 IST.** Report writing starts **13:00 IST** no matter what.

- `docs/PRD.md` is the source of truth for **what** to build (FR-#, E#, F#, tiers). This file governs **how** to work.
- `PREREG.md` is **frozen** once committed and tagged `prereg-frozen`.
- `docs/KICKOFF.md` holds the ordered prompts the human pastes. Do one prompt at a time.
- **Repo:** https://github.com/Asha0509/Swarm-Alignment-Hackathon (branch `main`). It is **public**, so treat every commit as published (no keys, no evolved attacker protocols).
- **README:** do NOT create or edit `./README.md` during the sprint. The README lives in `docs/README_TEMPLATE.md` and is filled and committed **once** at the end (§6).

## 0. Golden rules
1. **Never fabricate.**
   - Every number in RESULTS, the final README or the report comes from `results/processed/report_numbers.json`, produced by a script.
   - Every citation is verified (arXiv page, DOI or publisher) and recorded in `report/CITATIONS.md` with a ✔ before use.
   - Made-up results or references **disqualify** the team.
2. **$0 cash; Adaption credits first.**
   - **Adaption** (sponsor credits) is the primary provider for every LLM role, plus Invent and AutoScientist (PRD FR-10, FR-12). Free tiers (`groq:`, `gemini:`, `openrouter:*:free`, `cerebras:`, `ollama:`) are fallback only.
   - Estimate credits before each batch. Above 100 credits, ask the human. Hard cap: 900 credits on inference.
   - `config.py` must refuse any model not in `ALLOWED_MODELS`. Never add a cash-paid endpoint, even "just for a test".
3. **Tier discipline.**
   - Build the **Must** tier end to end (sandbox → monitors → E0–E3 → F1–F5, T1–T2) before any **Should**.
   - No **Could** before 09:30 IST.
   - Anything not in the PRD needs a `logs/PLANNING_LOG.md` entry and the human's OK.
4. **Simplicity.**
   - Reuse before writing. One module per FR. No frameworks (no LangChain, no agent SDKs). Plain Python + `openai` client.
   - Functions < 60 lines where possible. Type hints everywhere.
5. **Pre-registration is frozen.** After the `prereg-frozen` tag, never change the primary metric, contrast, thresholds or frozen prompts. Deviations go in PLANNING_LOG and the report.
6. **Report prose:** Claude drafts, and the human edits every section.
   - Plain language, short sentences, **no em dashes**, no hype words ("groundbreaking", "novel" more than once).
   - Record every AI assist in `logs/LLM_USAGE.md`.
7. **Secrets.** Never read, print, grep or edit `.env`; a hook blocks it. Code loads keys via `python-dotenv`. Only `.env.example` is editable.
8. **Dual-use hygiene.** The LLM attacker's evolved protocols go to `results/raw/<run>/protocols/`, which is **gitignored**. Only category summaries go into the report or repo (PRD §11).

## 1. Environment facts
- Python ≥ 3.11 via `uv`. Run everything as `uv run …` from the repo root.
- Package: `src/cachewhisper/`. Entry points live in `scripts/`.
- **Primary: `adaption:<model>`** via the `adaption` SDK: `Adaption().responses.create(model, instructions, input, temperature, max_output_tokens)` → `.output_text`. No seed parameter. List the models your key can use with `client.models.list(type="hosted")` at smoke; the price table is in PRD FR-10.
- Fallback providers (OpenAI-compatible base URLs live in `src/cachewhisper/config.py`; **verify model ids at smoke time, replace any that 404 and log it**):
  - `groq:` → `https://api.groq.com/openai/v1`
  - `gemini:` → `https://generativelanguage.googleapis.com/v1beta/openai/`
  - `openrouter:` → `https://openrouter.ai/api/v1` (only ids ending `:free`)
  - `cerebras:` → `https://api.cerebras.ai/v1`
  - `ollama:` → `http://localhost:11434/v1`
- Roles and models come from `.env`: `ATTACKER_MODELS`, `STRATEGIST_MODELS`, `MONITOR_MODELS` (trusted-weaker), `BENIGN_MODELS`. Each is a comma list giving the **rotation order**.
- Every LLM call goes through `cachewhisper.llm.chat()`: disk cache, backoff on 429, rotation, and a row in `logs/API_USAGE.csv`. **No direct client calls anywhere else.**
- Credits are cheap, but wall-clock time and rate limits are not. Prefer scripted agents wherever the PRD allows. Never loop on 429s more than 5 times; rotate to the next model/provider or fail the episode with `status=rate_limited`.
- Adaption Invent and AutoScientist jobs run **through the SDK** from `src/cachewhisper/adaption_jobs.py` and `scripts/adaption_*.py`, in the background. Log every job ID. AutoScientist go/no-go is at 11:00 IST, and it never blocks the Must tier.

## 2. Repo layout
```
README.md (GitHub stub until the end)  CLAUDE.md  PREREG.md  PREEXISTING.md  setup.sh  pyproject.toml  Makefile  .env.example
docs/       PRD.md  KICKOFF.md  TASKS.md  README_TEMPLATE.md  PROJECT_BOOK.md|.html (generated)
src/cachewhisper/
            config.py llm.py registry.py infralog.py agents.py episode.py channels.py
            attacker.py benign.py spoof.py defenses.py metrics.py stats.py runs.py figures.py
            monitors/ transcript.py metadata.py consistency.py learned.py combined.py calibrate.py
configs/    e0_calibration.yaml e1_expert.yaml e2_spoof.yaml e3_attacker.yaml e4_defenses.yaml ...
data/       tactics.yaml  adaption/ (exports + imports)  swarmtraces/ (gitignored raw)
scripts/    check.sh smoke.sh run_experiment.py analyse.py make_figures.py trace_numbers.py
            build_book.py export_adaption.py log_test_run.sh
tests/      free tests only; anything that calls an API is @pytest.mark.slow
results/    raw/<run_id>/ (infra.jsonl, transcripts.jsonl, episode.json; never hand-edited)
            processed/ (tables, report_numbers.json)   RESULTS.md (generated)
figures/    F1..F8 .png + .svg, T1/T2 .md (generated)
report/     OUTLINE.md DRAFT.md CITATIONS.md FIGURES.md VIDEO_SCRIPT.md final/
logs/       see §5
.claude/    settings.json, hooks/, commands/ (/check /log /bug /gate /book /trace)
```

## 3. Build loop and testing (testing fits THIS project, not a fixed recipe)

This is a **research sandbox + measurement** project. What can go wrong is mostly *silent*: a wrong formula, a seed leak, a monitor that only looks good because benign traffic is too easy. So most tests check **correctness, invariants and statistics**, not "does it run". A smoke run is used **only where real LLM calls are involved**. Pick the test types that fit each module from the table; don't add ceremony that doesn't catch real bugs.

| Test type | What it catches here | Where it applies | Cost |
|---|---|---|---|
| **Unit (exact)** | wrong math, wrong parsing | metrics (BER, capacity, bits/op), JSON tool parser, feature extraction, calibration thresholds | free |
| **Invariant / property** | rules that must always hold, over many random seeds | registry (listing order, policy enforcement), infra log (every op logged once, chain breaks on any edit), spoof layer (infra log never changes), channels (encode → decode round-trips for random secrets) | free |
| **Determinism** | hidden randomness that kills reproducibility | same seed → byte-identical infra log and transcripts (registry, episode, benign generator, scripted channels) | free |
| **Integration (scripted episode)** | modules that work alone but not together | full episode with ScriptedAgents + benign traffic + all monitors, no LLM | free |
| **Contract (FakeLLM)** | LLM-facing logic breaking on odd outputs | attacker loop, strategist feedback, LLM agents, M1 parsing: malformed JSON, empty reply, refusal text, 429s | free |
| **Statistical sanity** | measurement bugs that look like results | calibration hits target FPR on held-out benign seeds (±2 pts); a pure-noise "channel" gets capacity ≈ 0 and AUROC ≈ 0.5; shuffled labels give AUROC ≈ 0.5; bootstrap CI covers the true value on synthetic data | free |
| **Leakage** | optimistic results from reused data | calibration/train/test seed sets disjoint; M4 never sees test seeds; thresholds fit only on calibration seeds | free |
| **Data integrity** | corrupted or partial runs entering analysis | every registry row has an output dir; every analysed run's infra chain verifies; failed runs are excluded *and* listed, never silently dropped | free |
| **Analysis regression** | numbers changing without anyone noticing | `analyse.py` on a small frozen fixture run → exact expected `report_numbers.json` subset; `trace_numbers.py` passes on RESULTS/report | free |
| **Smoke (live LLM)** | wrong model ids, key problems, real-output format surprises | **only** `llm.py` providers, LLM agents/attacker, M1. ≤ 30 calls, marked `@pytest.mark.slow` or run via `scripts/smoke.sh` | a few Adaption credits |

**Minimum per module** (more if a bug shows up; every bug fixed gets a regression test):
- **llm:** unit (allowlist refusal, cache key), contract (fake 429 → backoff → rotation; cache hit = no call), smoke once per provider at G0.
- **registry / infralog:** invariant + determinism.
- **channels:** invariant round-trip for random secrets, k ∈ {8, 16, 32}; bits_per_op honored.
- **benign:** determinism; distribution check (hash-like names actually appear; op mix within configured ranges).
- **episode:** integration (scripted); parse failures are counted and logged, never swallowed.
- **attacker / LLM agents:** contract tests with FakeLLM; one live smoke after the prompts are approved.
- **spoof:** invariant (infra log byte-identical; spoofed share ≈ s over many ops).
- **monitors + calibration:** statistical sanity + leakage; M2 ranks a known channel above benign fixtures; M3 flags a spoofed fixture and not an honest one.
- **metrics / stats:** unit against hand-computed cases (BER 0 → k bits; BER 0.5 → 0; BER 0.11 → ≈ 0.5·k) + bootstrap coverage on synthetic data.
- **analyse / figures:** analysis regression on the fixture; figures render without error (files exist, non-empty). No pixel tests.

**Loop for every module (don't move on until each step passes):**
1. **Tests first**, choosing types from the table. Free tests only in the default suite.
2. **Run it for real, the cheap way:** scripted modules run one scripted episode and print a summary table. LLM-facing modules run the live smoke (≤ 30 calls) and check: zero silent parse failures, rows in API_USAGE, infra log verifies.
3. **Prompt dump** (LLM-facing modules only): one rendered prompt per role/condition in `logs/prompts/`; the human approves attacker, strategist and monitor prompts once.
4. **Regression:** `bash scripts/check.sh` (ruff + pyright + `pytest -m "not slow"`), which appends to `logs/TEST_LOG.md`.
5. **Log:** `/log`. Bugs in our code → `logs/BUGS_LOG.md` (`/bug`) with a regression test.
6. **Commit:** one commit for the finished task, logs included, message per §9.

## 4. Experiment rules
- **Seeds:** calibration seeds 0–199, test seeds 1000+, LLM attacker seeds 5000+. Never reuse a seed across splits (tested).
- **Registry first:** every run calls `runs.register_run(...)` at launch and `runs.finish_run(...)` at the end. Failed and rate-limited runs stay in the registry with a reason.
- **Before each batch:** print and log the estimated LLM calls per provider (API_USAGE.csv, `kind=estimate`). If the estimate is > 1,000 calls, ask the human first.
- **Long runs:** `nohup uv run python scripts/run_experiment.py configs/<file>.yaml > logs/runs/<name>.log 2>&1 &`. Report the PID. Check progress with `tail`, never by re-running.
- **Frozen artifacts:** M1 prompt, M2 feature config, strategist template. Their sha256 goes into PREREG.md via `uv run python -m cachewhisper.monitors.calibrate --hashes`.
- **Report everything:** every arm, every sign. Nulls go in CHALLENGES_LOG and the report.
- **Primary analysis** is computed **only** by `stats.primary_h1()` called from `scripts/analyse.py`, exactly as PREREG.md states.

## 5. Logs (append-only, IST timestamps `YYYY-MM-DD HH:MM IST`, newest at bottom; never delete, strike through to correct)

| File | What | When |
|---|---|---|
| `logs/BUILD_LOG.md` | Each module/function: what, file:lines, tests, smoke result, calls used | After each build step |
| `logs/ERROR_LOG.md` | Every runtime error or failed run: exact message, cause, fix, data impact, status | Immediately |
| `logs/BUGS_LOG.md` | Bugs **in our code** (logic/stat/data bugs found by tests, review or analysis): symptom, root cause, fix commit, which results were affected and re-run | When found |
| `logs/CHALLENGES_LOG.md` | Threats to validity, surprises, nulls, design trade-offs, and how we handled them. Feeds Limitations, Discussion, the video | When it happens |
| `logs/PLANNING_LOG.md` | Decisions (D###), gate outcomes, scope changes, PREREG deviations | At each decision |
| `logs/TEST_LOG.md` | Auto-appended by `scripts/check.sh`: timestamp, commit, pass/fail counts | Every check |
| `logs/RUN_REGISTRY.csv` | One row per run (PRD FR-13) | At launch, then update |
| `logs/API_USAGE.csv` | `ts_ist,provider,model,role,kind(estimate/actual/cache_hit/429),calls,tokens_in,tokens_out,credits` | Automatic via `llm.chat()`; Adaption rows by hand |
| `logs/LLM_USAGE.md` | AI assistance, for the LLM Usage Statement | Continuously |
| `logs/prompts/` | Rendered prompts per role/condition | After each prompt change |
| `logs/runs/` | stdout of background runs (gitignored) | — |

**Error vs bug:** an *error* is something that failed when it ran (429, timeout, crash). A *bug* is our code being wrong (wrong BER formula, seed leak, off-by-one in Δ). Bugs must state **which results were affected** and confirm they were re-run.

## 6. Results, figures, README rules
- `scripts/analyse.py` → `results/processed/*.csv`, `report_numbers.json`, `results/RESULTS.md` (all figures embedded with relative paths, every table generated).
- `scripts/make_figures.py` → `figures/F*.png|svg`. Use `cachewhisper.figures` helpers:
  - one color per monitor, everywhere: M1 transcript, M2 metadata, M3 consistency, M4 learned, M\* combined;
  - lines labeled directly; plain-language axis titles with units ("Hidden bits per episode", "Caught at 5% false-alarm rate");
  - 95% CI bands/bars on every estimate; n stated in the caption.
- **README = template until the end.** During the sprint, `./README.md` stays as GitHub's one-line stub. Never edit it. All README content lives in `docs/README_TEMPLATE.md`; edit the template only if the *structure* must change.
- **Filling the README (once, KICKOFF Prompt 10, after final results):**
  - copy `docs/README_TEMPLATE.md` to `./README.md`;
  - remove the template comment at the top and fill every `{{…}}` and every `GENERATED` block from `report_numbers.json`, `figures/T2_main.md` and the real figure files (F1, F2, F3, F6);
  - tick only the deliverable rows that are true;
  - test every link and the reproduction commands from a fresh clone, run `trace_numbers.py` on it;
  - commit it **alone** in one commit (§9).
- `scripts/trace_numbers.py report/DRAFT.md results/RESULTS.md` (plus `README.md` once filled) must pass: every number with ≥ 2 significant digits must exist in `report_numbers.json` (or be on the allowlist in the script, e.g. years, section numbers).
- `scripts/build_book.py` regenerates `docs/PROJECT_BOOK.{md,html}`. Run at each milestone (`/book`).

## 7. Claude Code usage notes
- Slash commands in `.claude/commands/`:
  - `/check`: lint, types, tests, then log;
  - `/log`: build-log entry;
  - `/bug`: bug-log entry;
  - `/gate`: evaluate a PRD §10 gate and write a D### entry;
  - `/book`: build the Project Book;
  - `/trace`: number tracing.
- Optional extras if installed: gstack `/investigate` (any traceback/NaN/implausible metric: state the root cause before fixing), `/review` on each finished module, `/careful` before deleting `results/`. Never `/ship`, `/qa`, or design skills.
- Subagents: at most one at a time, for read-only work (citation checks, cold-read critique). Never parallel LLM-heavy subagents (they burn the free tiers).
- On any traceback, NaN, a parse-failure spike, or a metric that looks too good (AUROC ≥ 0.99, TPR = 1.0 everywhere): **stop and investigate first.** Suspect leakage or weak benign traffic before celebrating, and log it in CHALLENGES_LOG.

## 8. Final submission checklist (15:30–16:00 IST; Claude verifies, humans confirm)
**Official (sprint page):**
- [ ] Official template (copy link on sprint page) used; PDF exported
- [ ] ≤ 8 pages excluding references and appendices (target 6)
- [ ] Title + abstract **150–250 words** (`wc -w` printed)
- [ ] Author names and affiliations
- [ ] Sections: Introduction, Related Work, Methodology, Results, Discussion, Limitations & Dual-Use/Ethical, References
- [ ] **Appendix A "Limitations and Dual-Use / Ethical Considerations"** present and specific (PRD §11)
- [ ] Pre-existing code marked (final README, PREEXISTING.md, Appendix B)
- [ ] No fabricated numbers (`trace_numbers.py` passes) or references (every CITATIONS.md entry ✔)
- [ ] Submitted via the sprint form; tracks 4 (+1); team registered on the Apart page; confirmation email saved
- [ ] Title is final (resubmission must reuse the **same** title)

**Ours (quality bar):**
- [ ] Page 1: F1 schematic + Infra-Operator Runbook box
- [ ] Primary result reported exactly per PREREG (commit hash cited); deviations disclosed
- [ ] T1 positive controls + calibration shown before any headline claim
- [ ] Every figure regenerates via `make figures`; CIs and n on all
- [ ] LLM Usage Statement (Appendix C) built from `logs/LLM_USAGE.md`
- [ ] Final README filled from `docs/README_TEMPLATE.md` (no `{{` left: `grep -c '{{' README.md` = 0), deliverables matrix ticked honestly, figures embedded, reproduction commands tested from a fresh clone, committed once
- [ ] `results/RESULTS.md` regenerated after the final run
- [ ] Project Book built; everything pushed to `main`; repo links tested in incognito
- [ ] Evolved attacker protocols NOT in the public repo (`git ls-files | grep protocols` is empty)
- [ ] Cold read by someone outside the team (or a fresh Claude subagent with only the PDF)

## 9. Git and commits
Repo: https://github.com/Asha0509/Swarm-Alignment-Hackathon · branch `main` · public.

**When to commit**
- **After every finished task:** each module + its tests, each script, each config, each log batch, each figure set. A KICKOFF prompt usually produces 2–5 commits, never one giant commit at the end.
- **After every milestone or gate:** G0–G3, PREREG freeze, each experiment finished, results analysed, report draft, final checks. Milestone commits are followed by `git push`.
- **Before anything risky:** a big refactor, re-running analysis that overwrites `results/processed/`, or deleting files.
- Only commit when `bash scripts/check.sh` is green. If it can't be green yet, say why in the message ("tests for X still failing, fixing next").
- Never commit: `.env`, `results/raw/**/protocols/`, `logs/runs/`, big raw data. Run `git status` before every commit and look at what is staged.
- `./README.md` is committed exactly once, at the end (§6).

**How to write the message: human, simple, self-explanatory**
- A reader who has never seen the code should understand **what changed and why** from the message alone.
- **Subject line:** plain English, ≤ 72 characters, starts with a verb in the present tense ("Add", "Fix", "Run", "Update", "Remove"). No jargon-only subjects, no emojis, no ticket codes, no "WIP", "misc", "updates", or "fix stuff".
- **Body (when the change is not obvious):** a blank line, then 1–5 short lines or bullets: what it does, why, and anything a reader must know (numbers changed, tests added, known limits). Mention the PRD ref in brackets at the end if useful, e.g. `(PRD FR-2)`.
- Keep it as easy as talking to a teammate. Be detailed only when the change needs it.

**Good examples**
```
Add the shared package registry that all agents use

Agents can list, publish, fetch and delete packages in one shared space,
like the cache the agents abused in the Hugging Face incident.
Listing is reverse-alphabetical on purpose (same as the real system).
Tests cover listing order, permissions and same-seed reproducibility. (PRD FR-1)
```
```
Fix wrong bit error rate when the receiver gives up early

Missing bits were counted as correct instead of wrong, which made
capacity look higher than it was. Re-ran E1; frontier figure updated.
Logged as B003 in the bugs log.
```
```
Freeze the pre-registration before the main experiments
```
```
Run the spoofing experiment and save raw results

150 episodes across 5 spoof rates. 2 runs hit rate limits and are
marked failed in the run registry (not dropped).
```

**Bad examples (never)**
- `update` · `fixes` · `WIP` · `misc changes` · `feat(core): impl FR-1..FR-7 w/ tests` · `final final v2`
