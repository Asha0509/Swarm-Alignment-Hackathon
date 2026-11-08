#!/usr/bin/env bash
# =====================================================================================
# One-shot setup for "Whispering Through the Package Cache"
# Apart Research · Swarm Alignment Hackathon (Nov 2026)
#
#   bash setup.sh                  # full setup
#   SKIP_PLUGINS=1 bash setup.sh   # skip Claude Code plugins / MCP
#   FETCH_DATA=1 bash setup.sh     # also download Swarm Traces + METR report into data/
#   FORCE=1 bash setup.sh          # overwrite scaffold files (NEVER touches README*/CLAUDE/PRD/KICKOFF,
#                                  #   results/, logs content, .env)
#
# Idempotent. Needs: git, curl. macOS / Linux / WSL. Cash cost: $0.
# Run from the root of a clone of https://github.com/Asha0509/Swarm-Alignment-Hackathon
# after copying in CLAUDE.md, docs/PRD.md, docs/KICKOFF.md, docs/README_TEMPLATE.md.
# ./README.md stays GitHub's stub until the end (filled once from docs/README_TEMPLATE.md).
# =====================================================================================
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
REPO_URL="https://github.com/Asha0509/Swarm-Alignment-Hackathon.git"

g=$'\033[32m'; r=$'\033[31m'; y=$'\033[33m'; b=$'\033[1m'; n=$'\033[0m'
ok()   { echo "  ${g}✔${n} $*"; }
warn() { echo "  ${y}!${n} $*"; }
bad()  { echo "  ${r}✘${n} $*"; }
step() { echo; echo "${b}== $* ==${n}"; }
have() { command -v "$1" >/dev/null 2>&1; }
TODO=()
CREATED=0; KEPT=0

# put <path>  (content on stdin). Creates parent dirs. Keeps existing files unless FORCE=1.
put() {
  local f="$1"
  mkdir -p "$(dirname "$f")"
  if [[ -e "$f" && "${FORCE:-0}" != "1" ]]; then cat >/dev/null; KEPT=$((KEPT+1)); return 0; fi
  cat > "$f"; CREATED=$((CREATED+1))
}
# append-only files (logs) are never overwritten, even with FORCE=1
put_log() {
  local f="$1"; mkdir -p "$(dirname "$f")"
  if [[ -e "$f" ]]; then cat >/dev/null; KEPT=$((KEPT+1)); return 0; fi
  cat > "$f"; CREATED=$((CREATED+1))
}

# ---------------------------------------------------------------------------------- 1
step "1. Prerequisites"
for t in git curl; do have "$t" && ok "$t" || { bad "$t missing: install it first"; exit 1; }; done
for f in CLAUDE.md docs/PRD.md docs/KICKOFF.md docs/README_TEMPLATE.md; do
  [[ -f "$f" ]] && ok "$f present" || warn "$f missing (put the planning files in the repo root first)"
done
if ! have jq; then
  warn "jq missing (Claude hooks need it). Trying to install…"
  if have brew; then brew install jq >/dev/null
  elif have apt-get; then sudo apt-get install -y jq >/dev/null 2>&1 || true
  fi
fi
have jq && ok "jq" || TODO+=("Install jq (https://jqlang.org/download/): the Claude hooks need it")
if ! have uv; then
  warn "uv missing. Installing (free, astral.sh)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi
have uv && ok "uv $(uv --version | awk '{print $2}')" || { bad "uv install failed"; exit 1; }
have claude && ok "Claude Code CLI" || TODO+=("Install Claude Code, then re-run setup.sh for plugins")
have ollama && ok "ollama (offline fallback model)" || warn "ollama not found (optional offline fallback: https://ollama.com)"
have gh && ok "gh CLI" || warn "gh not found (optional, for creating the GitHub repo)"

# ---------------------------------------------------------------------------------- 2
step "2. Folder structure"
DIRS=(
  docs src/cachewhisper/monitors configs data/adaption data/swarmtraces
  scripts tests results/raw results/processed figures
  report/final logs/prompts logs/runs .claude/hooks .claude/commands
)
for d in "${DIRS[@]}"; do mkdir -p "$d"; done
for d in results/raw results/processed figures report/final data/adaption logs/prompts; do
  [[ -e "$d/.gitkeep" ]] || touch "$d/.gitkeep"
done
ok "created ${#DIRS[@]} directories"

# ---------------------------------------------------------------------------------- 3
step "3. Project config files"

put .gitignore <<'EOF'
# secrets
.env
**/.env
# envs / caches
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.pyright/
# run stdout + big raw data
logs/runs/
data/swarmtraces/*
!data/swarmtraces/.gitkeep
data/metr_report.pdf
# dual-use hygiene: evolved attacker protocols are never published (CLAUDE.md §0.8)
results/raw/**/protocols/
# LLM cache: commit only if < 50 MB (see PRD NFR-1); default ignored
results/raw/llm_cache.sqlite
# local template copies
Copy of *
*:Zone.Identifier
.DS_Store
EOF

put .env.example <<'EOF'
# Copy to .env and fill in. NEVER commit .env. Claude Code is blocked from reading it.
# PRIMARY: Adaption (sponsor credits). Fallbacks below are free tiers. No cash-paid endpoints (CLAUDE.md §0.2).
ADAPTION_API_KEY=
# Fallbacks (optional)
GROQ_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
CEREBRAS_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434/v1

# Allowlist: config.py refuses any model not listed here. Verify ids in `make smoke`;
# replace any that 404 with a current free model and log it in PLANNING_LOG.
ALLOWED_MODELS=adaption:qwen3.5-397b,adaption:glm-5.2,adaption:deepseek-v4-flash,adaption:qwen3.8-27b,adaption:gemma-4-31b-it,adaption:gemma-4-26b-a4b-it,adaption:glm-53-flash,groq:llama-3.3-70b-versatile,groq:llama-3.1-8b-instant,gemini:gemini-2.5-flash,gemini:gemini-2.5-flash-lite,ollama:qwen2.5:7b-instruct

# Role -> rotation order (comma list). Monitor should be the trusted-WEAKER model (control framing).
ATTACKER_MODELS=adaption:qwen3.5-397b,groq:llama-3.3-70b-versatile
STRATEGIST_MODELS=adaption:qwen3.5-397b,gemini:gemini-2.5-flash
MONITOR_MODELS=adaption:gemma-4-26b-a4b-it,groq:llama-3.1-8b-instant
STRONG_MONITOR_MODEL=adaption:qwen3.5-397b
BENIGN_MODELS=adaption:deepseek-v4-flash,groq:llama-3.1-8b-instant
SWEEP_MODELS=adaption:qwen3.5-397b,adaption:glm-5.2,adaption:deepseek-v4-flash,adaption:qwen3.8-27b,adaption:gemma-4-31b-it

# Safety valves
MAX_CALLS_PER_RUN=5000
CREDIT_ASK_THRESHOLD=100
CREDIT_HARD_CAP=900
MAX_429_RETRIES=5
LLM_CACHE_PATH=results/raw/llm_cache.sqlite
EOF

put pyproject.toml <<'EOF'
[project]
name = "cachewhisper"
version = "0.1.0"
description = "Whispering Through the Package Cache: capacity vs detectability of covert agent coordination through shared infrastructure (Apart Swarm Alignment Hackathon 2026)"
requires-python = ">=3.11"
dependencies = [
  "numpy>=1.26",
  "pandas>=2.2",
  "scipy>=1.13",
  "scikit-learn>=1.5",
  "matplotlib>=3.8",
  "openai>=1.40",
  "adaption>=0.16",
  "python-dotenv>=1.0",
  "pyyaml>=6.0",
  "markdown>=3.6",
  "tqdm>=4.66",
]

[dependency-groups]
dev = ["ruff>=0.6", "pytest>=8", "pytest-asyncio>=0.23", "pyright>=1.1.380"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cachewhisper"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["slow: hits the network / uses free-tier quota"]
addopts = "-ra"
asyncio_default_fixture_loop_scope = "function"

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "B", "I", "NPY", "PD", "UP"]
ignore = ["PD901"]

[tool.pyright]
include = ["src", "tests", "scripts"]
typeCheckingMode = "basic"
EOF

put Makefile <<'EOF'
# Uses '>' instead of TAB so the file survives copy/paste.
.RECIPEPREFIX = >
.PHONY: setup check smoke experiments must should analyse figures book trace all

setup:
> bash setup.sh
check:
> bash scripts/check.sh
smoke:
> bash scripts/smoke.sh
experiments: must
must:
> uv run python scripts/run_experiment.py configs/e0_calibration.yaml
> uv run python scripts/run_experiment.py configs/e1_expert.yaml
> uv run python scripts/run_experiment.py configs/e2_spoof.yaml
> uv run python scripts/run_experiment.py configs/e3_attacker.yaml
should:
> uv run python scripts/run_experiment.py configs/e4_defenses.yaml
> uv run python scripts/run_experiment.py configs/e5_second_model.yaml
analyse:
> uv run python scripts/analyse.py
figures:
> uv run python scripts/make_figures.py
trace:
> uv run python scripts/trace_numbers.py report/DRAFT.md results/RESULTS.md
book:
> uv run python scripts/build_book.py
all: check analyse figures trace book
EOF

put PREEXISTING.md <<'EOF'
# Pre-existing code (disclosure required by sprint rules)

**None.** All code in this repository was written during the Swarm Alignment Hackathon
(Nov 6–8 2026). The scaffold commit ("Set up the project skeleton…") contains only planning
documents and empty scaffolding produced by `setup.sh`.

Third-party open-source libraries are used as dependencies only (see `pyproject.toml` / `uv.lock`);
none are vendored or modified. Public data used (not ours): METR Hugging Face incident report (2026),
Swarm Traces redacted payloads (swarmtraces.org). Both are cited in the report.

The repository's very first commit ("Initial commit") is GitHub's auto-generated one-line README.
Sprint work = everything after it: `git log --stat`.
EOF

put PREREG.md <<'EOF'
# Pre-registration: NOT YET FROZEN

> Written by Claude in KICKOFF Prompt 5 from docs/PRD.md §6, approved by the human, then committed
> ALONE and tagged `prereg-frozen` BEFORE the E1–E3 main runs. After that, this file never changes.
> Deviations go to logs/PLANNING_LOG.md and the report.

## Design (fill)
- Models (attacker / strategist / monitor / benign / second):
- Seeds and sample sizes per experiment:
- Defaults: k = 16, T = 10, n_benign = 3, Δ = 6, α ∈ {1%, 5%}
- Call-budget estimate:

## Primary outcome and contrast (H1)
- Undetected capacity at 5% FPR (bits/episode), per monitor.
- Contrast at spoof rate s = 1: M1 − M* (M* = M2+M3), paired bootstrap over all E1+E3 attack episodes,
  10,000 resamples, seed 0. Declared iff 95% CI lower bound > 0 AND mean difference ≥ 2 bits/episode.
- Computed ONLY by `cachewhisper.stats.primary_h1()` via `scripts/analyse.py`.

## Secondary (reported regardless of sign)
- H2 spoof · H3 awareness · H4 defense (D1 ≥ 80% capacity cut at ≤ 20-pt utility loss) · H5 elicitation gap

## Frozen artefacts (sha256)
- M1 prompt:
- M2 feature config:
- Strategist template:

**All results are reported regardless of sign.**
EOF

put docs/TASKS.md <<'EOF'
# TASKS: living checklist (mirror of PRD tiers; tick as you go)

## Must
- [ ] G0 smoke: ≥1 free provider works (FR-10)
- [ ] FR-1 registry · FR-2 infra log · FR-3 agents/episode · FR-4 channels E1–E5 · FR-6 benign · FR-7 spoof · FR-11 metrics · FR-13 runs
- [ ] G1 channels decode 100% at zero noise; chain verifies
- [ ] FR-5 LLM attacker loop + tactic cards
- [ ] FR-8 monitors M1 M2 M3 M4a M* + calibration
- [ ] G2 benign FPR within ±2 pts
- [ ] PREREG frozen + tagged
- [ ] E0 · E1 · E2 · E3
- [ ] analyse.py · figures F1–F5 · T1 · T2 · RESULTS.md
- [ ] G3 trace_numbers passes

## Should
- [ ] FR-9 defenses D1 D2 D3 · E4 · F6
- [ ] E5 model sweep · F7 · F9
- [ ] FR-12 Adaption: A1 inference (Must) · A2 model sweep E5 · A3 Invent → benign · A4 AutoScientist → M4b (start 07:00, go/no-go 11:00)

## Could
- [ ] E6 scaling · F8

## Report & submit
- [ ] DRAFT.md per PRD §11 · human edit · template · PDF
- [ ] CLAUDE.md §8 checklist · cold read · fill README.md from docs/README_TEMPLATE.md (ONE commit) · Project Book · push · SUBMIT 16:00
- [ ] (opt) video
EOF

# ---------------------------------------------------------------------------------- 4
step "4. Logs (append-only templates)"

put_log logs/BUILD_LOG.md <<'EOF'
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
EOF

put_log logs/ERROR_LOG.md <<'EOF'
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
EOF

put_log logs/BUGS_LOG.md <<'EOF'
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
EOF

put_log logs/CHALLENGES_LOG.md <<'EOF'
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
EOF

put_log logs/PLANNING_LOG.md <<'EOF'
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
EOF

put_log logs/TEST_LOG.md <<'EOF'
# Test Log
Auto-appended by `scripts/check.sh`. Do not edit by hand.

| Time (IST) | Commit | Ruff | Pyright | Pytest (passed/failed/skipped) |
|---|---|---|---|---|
EOF

put_log logs/LLM_USAGE.md <<'EOF'
# LLM Usage (source for the report's LLM Usage Statement, Appendix C)

| Date/time IST | Tool | Used for | Human review |
|---|---|---|---|
| 2026-11-09 02:00 | Claude (claude.ai) | Read sprint page, idea generation and critique, PRD/CLAUDE.md/KICKOFF/setup.sh drafting | Team reviewed |
EOF

put_log logs/RUN_REGISTRY.csv <<'EOF'
run_id,parent_id,tier,experiment,channel_or_attacker,awareness,spoof_rate,defense,n_agents,k_bits,seed,models,n_llm_calls,cache_hits,status,output_path,started_ist,finished_ist
EOF

put_log logs/API_USAGE.csv <<'EOF'
ts_ist,provider,model,role,kind,calls,tokens_in,tokens_out,credits_est,job_id,note
EOF

touch logs/prompts/.gitkeep

# ---------------------------------------------------------------------------------- 5
step "5. Report scaffolding"

put report/OUTLINE.md <<'EOF'
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
EOF

put report/DRAFT.md <<'EOF'
# DRAFT: written in KICKOFF Prompt 9 (13:00 IST). Do not start before results exist.
EOF

put report/CITATIONS.md <<'EOF'
# Citations: verified list (only ✔ entries may appear in the report)

Status: ✔ verified (link + authors + year + the claim we use checked) · ☐ unverified · ✘ rejected

| Status | Key | Reference | Link | Claim we use it for |
|---|---|---|---|---|
| ☐ | metr2026 | METR (2026). Hugging Face incident investigation report. | https://metr.org/hugging-face-incident-report-aug-2026.pdf | channel via Artifactory dir creation; "zz" prefix; ~7% spoofed transcripts |
| ☐ | swarmtraces2026 | Swarm Traces (2026). Reassembled attack payloads. | https://swarmtraces.org/ | 80k+ payloads; tactics (C2, log deletion, cache poisoning) |
| ☐ | openai2026 | OpenAI (2026). Hugging Face incident and misalignment. | https://openai.com/hugging-face-incident-and-misalignment/ | official disclosure |
| ☐ | greenblatt2024 | Greenblatt et al. (2024). AI Control: Improving Safety Despite Intentional Subversion. | https://arxiv.org/abs/2312.06942 | control framing; trusted monitoring |
| ☐ | motwani2024 | Motwani et al. (2024). Secret Collusion among AI Agents. NeurIPS. | (sprint page link) | text steganography collusion |
| ☐ | hammond2025 | Hammond et al. (2025). Multi-Agent Risks from Advanced AI. | https://arxiv.org/abs/2502.14143 | multi-agent risk taxonomy |
| ☐ | lampson1973 | Lampson (1973). A Note on the Confinement Problem. CACM. | (find DOI) | covert/storage channels |
| ☐ | cover2006 | Cover & Thomas (2006). Elements of Information Theory. | (book) | BSC capacity |
| ☐ | chan2024ids | Chan et al. (2024). IDs for AI Systems. | https://arxiv.org/abs/2406.12137 | agent identity (related work) |
| ☐ | leetiwari2024 | Lee & Tiwari (2024). Prompt Infection. | https://arxiv.org/abs/2410.07283 (verify) | spread of compromise (related work) |
EOF

put report/FIGURES.md <<'EOF'
# Figure captions (final wording; n and CI stated in every caption)

| Fig | File | Caption (draft) |
|---|---|---|
| F1 | figures/F1_schematic.png | CacheGym. Agents share one package registry. The infrastructure log (ground truth) and agent transcripts (may be spoofed) feed four monitors. |
| F2 | figures/F2_frontier.png | Hidden bits per episode vs probability of being caught at a 5% false-alarm budget, per monitor. |
| F3 | figures/F3_spoof_sweep.png | Detection at 5% false alarms as the share of spoofed transcript entries rises. |
| F4 | figures/F4_roc.png | ROC curves per monitor, honest vs fully spoofed transcripts. |
| F5 | figures/F5_adaptation.png | Adaptive LLM attacker over rounds: capacity and detection, aware vs unaware. |
| F6 | figures/F6_defenses.png | Capacity removed vs honest work lost for each defense. |
| F7 | figures/F7_gap.png | Expert channels vs LLM attacker: undetected capacity. |
| F8 | figures/F8_scaling.png | Undetected capacity vs number of receivers. |
EOF

put report/VIDEO_SCRIPT.md <<'EOF'
# Video script (3–5 min): drafted by Claude on request after results exist
0:00–0:30 Hook: the HF incident, a cache turned message board, transcripts that lied.
0:30–1:30 Demo: one CacheGym episode; infra log vs spoofed transcript side by side; monitors light up.
1:30–3:00 Results: F2 frontier, F3 spoof sweep, F6 defenses (one sentence each, numbers from report_numbers.json).
3:00–3:30 Runbook: four bullets.
3:30–3:45 Repo + paper link.
EOF

put results/RESULTS.md <<'EOF'
# RESULTS (auto-generated by `scripts/analyse.py`; do not hand-edit)

No results yet. Run `make analyse figures` after the experiments finish.
EOF

# ---------------------------------------------------------------------------------- 6
step "6. Python package + tests scaffolding"

put src/cachewhisper/__init__.py <<'EOF'
"""CacheGym / cachewhisper: covert coordination through shared infrastructure (Apart Swarm Alignment 2026)."""

__version__ = "0.1.0"
EOF

put src/cachewhisper/monitors/__init__.py <<'EOF'
"""Monitors M1 (transcript), M2 (metadata), M3 (consistency), M4 (learned), M* (combined)."""
EOF

put tests/conftest.py <<'EOF'
"""Shared fixtures. FakeLLM lets every test run with zero API calls."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pytest


@dataclass
class FakeLLM:
    """Deterministic stand-in for cachewhisper.llm.chat(). Script responses or pass a function."""

    responses: list[str] = field(default_factory=list)
    fn: Callable[[list[dict]], str] | None = None
    calls: list[list[dict]] = field(default_factory=list)

    def __call__(self, messages: list[dict], **_: object) -> str:
        self.calls.append(messages)
        if self.fn is not None:
            return self.fn(messages)
        if not self.responses:
            raise RuntimeError("FakeLLM ran out of scripted responses")
        return self.responses.pop(0)


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()
EOF

put tests/test_scaffold.py <<'EOF'
"""Scaffold self-tests: repo structure and the doc/trace tooling work before any sprint code exists."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_package_imports() -> None:
    import cachewhisper

    assert cachewhisper.__version__


def test_required_files_exist() -> None:
    for p in ["CLAUDE.md", "docs/PRD.md", "PREREG.md", "PREEXISTING.md", "logs/BUGS_LOG.md",
              "logs/RUN_REGISTRY.csv", "logs/API_USAGE.csv", "report/CITATIONS.md"]:
        assert (ROOT / p).exists(), p


def test_trace_numbers_flags_unknown(tmp_path: Path) -> None:
    nums = tmp_path / "n.json"
    nums.write_text(json.dumps({"primary": {"diff": 3.41, "ci": [1.2, 5.6]}, "tpr": 0.873}))
    good = tmp_path / "good.md"
    good.write_text("Difference 3.41 bits (CI 1.2 to 5.6), TPR 87.3%.\n")
    bad = tmp_path / "bad.md"
    bad.write_text("Difference 9.99 bits.\n")
    script = ROOT / "scripts" / "trace_numbers.py"
    ok = subprocess.run([sys.executable, str(script), "--numbers", str(nums), str(good)], capture_output=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    ko = subprocess.run([sys.executable, str(script), "--numbers", str(nums), str(bad)], capture_output=True)
    assert ko.returncode == 1


def test_build_book_runs(tmp_path: Path) -> None:
    out = tmp_path / "book"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_book.py"), "--out", str(out)],
                       capture_output=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (out / "PROJECT_BOOK.md").stat().st_size > 1000
    html = (out / "PROJECT_BOOK.html").read_text()
    assert "<nav" in html and "PRD" in html
EOF

# ---------------------------------------------------------------------------------- 7
step "7. Scripts"

put scripts/check.sh <<'EOF'
#!/usr/bin/env bash
# Lint + types + free tests. Appends a row to logs/TEST_LOG.md. Run before every commit.
set -uo pipefail
cd "$(dirname "$0")/.."
ts=$(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST')
commit=$(git rev-parse --short HEAD 2>/dev/null || echo "none")
uv run ruff check . >/tmp/cw_ruff.txt 2>&1; ruff_rc=$?
uv run pyright >/tmp/cw_pyright.txt 2>&1; pyright_rc=$?
uv run pytest -q -m "not slow" >/tmp/cw_pytest.txt 2>&1; pytest_rc=$?
summary=$(tail -n 1 /tmp/cw_pytest.txt)
p=$(grep -Eo '[0-9]+ passed' <<<"$summary" | grep -Eo '[0-9]+' || echo 0)
f=$(grep -Eo '[0-9]+ failed' <<<"$summary" | grep -Eo '[0-9]+' || echo 0)
s=$(grep -Eo '[0-9]+ skipped' <<<"$summary" | grep -Eo '[0-9]+' || echo 0)
mark() { [[ $1 -eq 0 ]] && echo "✔" || echo "✘"; }
echo "| $ts | $commit | $(mark $ruff_rc) | $(mark $pyright_rc) | ${p:-0}/${f:-0}/${s:-0} |" >> logs/TEST_LOG.md
cat /tmp/cw_ruff.txt; tail -n 3 /tmp/cw_pyright.txt; tail -n 15 /tmp/cw_pytest.txt
if [[ $ruff_rc -ne 0 || $pyright_rc -ne 0 || ($pytest_rc -ne 0 && $pytest_rc -ne 5) ]]; then
  echo "CHECK FAILED (ruff=$ruff_rc pyright=$pyright_rc pytest=$pytest_rc)"; exit 1
fi
echo "CHECK OK"
EOF

put scripts/smoke.sh <<'EOF'
#!/usr/bin/env bash
# Smoke: 1 scripted + 1 LLM episode (<= 30 calls). Implemented in KICKOFF Prompt 1/2 as cachewhisper.smoke.
set -euo pipefail
cd "$(dirname "$0")/.."
if ! uv run python -c "import cachewhisper.smoke" 2>/dev/null; then
  echo "cachewhisper.smoke not built yet (KICKOFF Prompt 1)."; exit 1
fi
uv run python -m cachewhisper.smoke "$@"
EOF

put scripts/trace_numbers.py <<'EOF'
#!/usr/bin/env python3
"""Fail if a document contains a number that is not in report_numbers.json (anti-fabrication, PRD NFR-5).

Checks decimals (3.41), percentages (87.3%) and integers >= 100 that are not years.
Percent values are also matched as fractions (87.3% <-> 0.873). Skips fenced code and lines containing
`notrace`. Extra allowed literals: scripts/trace_allowlist.txt (one per line).

Usage: python scripts/trace_numbers.py [--numbers results/processed/report_numbers.json] FILE [FILE ...]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NUM = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(%?)(?![\w])")


def flatten(x: object) -> list[float]:
    if isinstance(x, bool):
        return []
    if isinstance(x, int | float):
        return [float(x)]
    if isinstance(x, dict):
        return [v for val in x.values() for v in flatten(val)]
    if isinstance(x, list | tuple):
        return [v for val in x for v in flatten(val)]
    return []


def matches(tok: str, pct: bool, pool: list[float]) -> bool:
    val = float(tok)
    dec = len(tok.split(".")[1]) if "." in tok else 0
    cands = [val, val / 100] if pct else [val]
    for c in cands:
        d = dec + (2 if (pct and c != val) else 0)
        tol = 0.5 * 10 ** (-d) + 1e-12
        if any(abs(p - c) <= tol for p in pool):
            return True
    return False


def needs_check(tok: str, pct: bool) -> bool:
    if pct or "." in tok:
        return True
    v = abs(int(tok))
    return v >= 100 and not (1900 <= v <= 2100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--numbers", default="results/processed/report_numbers.json")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    npath = Path(a.numbers)
    if not npath.exists():
        print(f"✘ {npath} not found. Run scripts/analyse.py first.")
        return 1
    pool = flatten(json.loads(npath.read_text()))
    allow_f = Path(__file__).with_name("trace_allowlist.txt")
    allow = set(allow_f.read_text().split()) if allow_f.exists() else set()
    bad: list[str] = []
    for f in a.files:
        p = Path(f)
        if not p.exists():
            continue
        in_code = False
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or "notrace" in line:
                continue
            for m in NUM.finditer(line):
                tok, pct = m.group(1), bool(m.group(2))
                if tok in allow or not needs_check(tok, pct):
                    continue
                if not matches(tok, pct, pool):
                    bad.append(f"{f}:{i}: {tok}{'%' if pct else ''}  | {line.strip()[:90]}")
    if bad:
        print(f"✘ {len(bad)} untraced number(s):")
        print("\n".join(bad))
        return 1
    print(f"✔ all numbers traced ({len(a.files)} file(s), {len(pool)} source values)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
EOF

put scripts/trace_allowlist.txt <<'EOF'
0.05
EOF

put scripts/build_book.py <<'EOF'
#!/usr/bin/env python3
"""Build the Project Book: every project MD file in one page (PRD FR-16).

Outputs docs/PROJECT_BOOK.md and a self-contained docs/PROJECT_BOOK.html (TOC sidebar, figures inlined).
Usage: python scripts/build_book.py [--out docs]
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER = [
    ("Overview (README)", "README.md"),  # falls back to docs/README_TEMPLATE.md until filled
    ("Product Requirements (PRD)", "docs/PRD.md"),
    ("How We Work (CLAUDE.md)", "CLAUDE.md"),
    ("Build Prompts (KICKOFF)", "docs/KICKOFF.md"),
    ("Pre-registration", "PREREG.md"),
    ("Pre-existing Code", "PREEXISTING.md"),
    ("Results", "results/RESULTS.md"),
    ("Report Draft", "report/DRAFT.md"),
    ("Figure Captions", "report/FIGURES.md"),
    ("Citations", "report/CITATIONS.md"),
    ("Tasks", "docs/TASKS.md"),
    ("Planning Log", "logs/PLANNING_LOG.md"),
    ("Build Log", "logs/BUILD_LOG.md"),
    ("Test Log", "logs/TEST_LOG.md"),
    ("Error Log", "logs/ERROR_LOG.md"),
    ("Bugs Log", "logs/BUGS_LOG.md"),
    ("Challenges Log", "logs/CHALLENGES_LOG.md"),
    ("LLM Usage", "logs/LLM_USAGE.md"),
]
IMG_MD = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
IMG_HTML = re.compile(r'(<img[^>]*src=")([^"]+)(")')
COMMENT = re.compile(r"<!--.*?-->", re.S)
CSS = """body{font-family:-apple-system,Segoe UI,Inter,sans-serif;margin:0;display:flex;color:#1d1d1f}
nav{position:sticky;top:0;height:100vh;overflow:auto;width:270px;flex:none;background:#f5f5f7;
padding:20px;box-sizing:border-box;border-right:1px solid #ddd;font-size:14px}
nav a{display:block;color:#333;text-decoration:none;padding:4px 0}nav a:hover{color:#0a58ca}
main{max-width:980px;padding:32px 48px;line-height:1.55}
h1{border-bottom:2px solid #eee;padding-bottom:6px;margin-top:56px}
table{border-collapse:collapse;margin:12px 0;font-size:14px}td,th{border:1px solid #ddd;padding:6px 9px}
th{background:#fafafa}code{background:#f3f3f3;padding:1px 4px;border-radius:4px}
pre{background:#f6f8fa;padding:12px;overflow:auto;border-radius:6px}img{max-width:100%}
.part{color:#888;font-size:12px;text-transform:uppercase;letter-spacing:.08em}"""


def shift_headings(md: str) -> str:
    out, fence = [], False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
        out.append("#" + line if (not fence and line.startswith("#")) else line)
    return "\n".join(out)


def rebase(md: str, src: Path, out_dir: Path) -> str:
    def fix(path: str) -> str:
        if re.match(r"^(https?:|data:|#)", path):
            return path
        return os.path.relpath((src.parent / path).resolve(), out_dir.resolve())
    md = IMG_MD.sub(lambda m: f"![{m.group(1)}]({fix(m.group(2))})", md)
    return IMG_HTML.sub(lambda m: m.group(1) + fix(m.group(2)) + m.group(3), md)


def inline_images(html: str, base: Path) -> str:
    def sub(m: re.Match[str]) -> str:
        p = (base / m.group(2)).resolve()
        if m.group(2).startswith("data:") or not p.exists():
            return m.group(0)
        mime = "image/svg+xml" if p.suffix == ".svg" else f"image/{p.suffix.lstrip('.')}"
        return f'{m.group(1)}data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}{m.group(3)}'
    return re.sub(r'(<img[^>]*src=")([^"]+)(")', sub, html)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "docs"))
    out_dir = Path(ap.parse_args().out)
    out_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M IST")
    parts, toc = [], []
    for i, (title, rel) in enumerate(ORDER, 1):
        src = ROOT / rel
        if rel == "README.md" and (not src.exists() or src.stat().st_size < 500):
            src = ROOT / "docs" / "README_TEMPLATE.md"  # README is filled once at the end
        if not src.exists():
            continue
        anchor = f"part-{i}"
        body = rebase(COMMENT.sub("", src.read_text()), src, out_dir)
        parts.append(f'<a id="{anchor}"></a>\n\n# {i}. {title}\n\n<p class="part">{rel}</p>\n\n'
                     + shift_headings(body))
        toc.append((anchor, f"{i}. {title}"))
    header = f"# Project Book: Whispering Through the Package Cache\n\n*Built {now} from {len(parts)} files.*\n"
    md = header + "\n\n---\n\n".join([""] + parts)
    (out_dir / "PROJECT_BOOK.md").write_text(md)
    import markdown  # noqa: PLC0415

    html_body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    html_body = inline_images(html_body, out_dir)
    nav = "".join(f'<a href="#{a}">{t}</a>' for a, t in toc)
    html = (f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Project Book</title>"
            f"<style>{CSS}</style></head><body><nav><b>Project Book</b><br><small>{now}</small><hr>{nav}"
            f"</nav><main>{html_body}</main></body></html>")
    (out_dir / "PROJECT_BOOK.html").write_text(html)
    print(f"✔ {out_dir/'PROJECT_BOOK.md'} and .html ({len(parts)} parts)")


if __name__ == "__main__":
    main()
EOF

put scripts/make_placeholders.py <<'EOF'
#!/usr/bin/env python3
"""Write 'pending' placeholder PNGs so the README template/RESULTS render before real figures exist.
Real figures from scripts/make_figures.py overwrite them. Never overwrites an existing figure."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

NAMES = {
    "F1_schematic": "F1 · System schematic",
    "F2_frontier": "F2 · Capacity vs detection frontier",
    "F3_spoof_sweep": "F3 · Detection vs spoof rate",
    "F6_defenses": "F6 · Defenses: capacity removed vs utility lost",
}
out = Path(__file__).resolve().parents[1] / "figures"
out.mkdir(exist_ok=True)
for stem, title in NAMES.items():
    p = out / f"{stem}.png"
    if p.exists():
        continue
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axis("off")
    ax.text(0.5, 0.58, title, ha="center", fontsize=18, weight="bold", color="#333")
    ax.text(0.5, 0.40, "pending: generated by scripts/make_figures.py", ha="center", fontsize=12, color="#888")
    fig.patch.set_facecolor("#f5f5f7")
    fig.savefig(p, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print(f"placeholder {p.name}")
EOF

put scripts/export_adaption.py <<'EOF'
#!/usr/bin/env python3
"""Placeholder: implemented during the sprint (PRD FR-12). Writes data/adaption/*.jsonl for the Adaption web app."""

raise SystemExit("export_adaption.py not built yet: see docs/KICKOFF.md 'Adaption track'.")
EOF

chmod +x scripts/*.sh scripts/*.py

# ---------------------------------------------------------------------------------- 8
step "8. Claude Code config (.claude/)"

put .claude/settings.json <<'EOF'
{
  "permissions": {
    "allow": [
      "Bash(uv run pytest *)", "Bash(uv run ruff *)", "Bash(uv run pyright *)",
      "Bash(bash scripts/check.sh)", "Bash(bash scripts/smoke.sh*)",
      "Bash(uv run python scripts/*)", "Bash(make *)",
      "Bash(git status)", "Bash(git diff *)", "Bash(git log *)", "Bash(git add *)", "Bash(git commit *)", "Bash(git push)", "Bash(git push origin main)",
      "Bash(tail *)", "Bash(wc *)", "Bash(ls *)"
    ],
    "deny": [
      "Read(./.env)", "Read(./**/.env)", "Edit(./.env)", "Edit(./**/.env)", "Write(./.env)",
      "Bash(rm -rf *)", "Bash(git push --force*)", "Bash(git tag -d *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash|Read|Edit|Write|Grep|Glob",
        "hooks": [{ "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/guard_secrets.sh", "timeout": 5 }] },
      { "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/guard_frozen.sh", "timeout": 5 }] }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/ruff_after_edit.sh", "timeout": 30 }] }
    ],
    "UserPromptSubmit": [
      { "hooks": [{ "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/router.sh", "timeout": 5 }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/stop_gate.sh", "timeout": 180,
                    "statusMessage": "fast tests + log check" }] }
    ]
  }
}
EOF

put .claude/hooks/guard_secrets.sh <<'EOF'
#!/usr/bin/env bash
# PreToolUse: refuse any tool call that names .env (.env.example allowed).
input=$(cat)
s=$(jq -r '[.tool_input.command, .tool_input.file_path, .tool_input.path, .tool_input.pattern, .tool_input.glob]
           | map(select(. != null)) | join(" ")' <<<"$input" 2>/dev/null)
if grep -Eq '(^|[[:space:]/"'"'"'=])\.env($|[^.[:alnum:]_])' <<<"$s"; then
  echo "Blocked: .env holds API keys. Do not read, print, grep or edit it; code loads it via python-dotenv." >&2
  exit 2
fi
exit 0
EOF

put .claude/hooks/guard_frozen.sh <<'EOF'
#!/usr/bin/env bash
# PreToolUse: once the prereg-frozen tag exists, PREREG.md cannot be edited.
input=$(cat)
f=$(jq -r '.tool_input.file_path // empty' <<<"$input" 2>/dev/null)
[[ "$f" == *PREREG.md ]] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
if git rev-parse -q --verify refs/tags/prereg-frozen >/dev/null 2>&1; then
  echo "Blocked: PREREG.md is frozen (tag prereg-frozen). Log deviations in logs/PLANNING_LOG.md instead." >&2
  exit 2
fi
exit 0
EOF

put .claude/hooks/ruff_after_edit.sh <<'EOF'
#!/usr/bin/env bash
# PostToolUse: report-only ruff check on the edited .py file (real bugs only).
input=$(cat)
f=$(jq -r '.tool_input.file_path // empty' <<<"$input" 2>/dev/null)
[[ "$f" == *.py && -f "$f" ]] || exit 0
out=$(uvx ruff check -q --isolated --select F,E9,B --output-format concise "$f" 2>/dev/null) && exit 0
jq -n --arg m "ruff found real bugs in $f. Fix before moving on:
$out" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$m}}'
exit 0
EOF

put .claude/hooks/router.sh <<'EOF'
#!/usr/bin/env bash
# UserPromptSubmit: inject checkpoint reminders from CLAUDE.md when the prompt matches.
p=$(jq -r '.prompt // empty' 2>/dev/null | tr '[:upper:]' '[:lower:]')
if grep -Eq '\b(batch|sweep|launch|main run|experiments?|e[0-6])\b' <<<"$p"; then
  echo "Checkpoint (CLAUDE.md §4): log a call estimate per provider in logs/API_USAGE.csv (kind=estimate); >1000 calls needs the human's OK; register every run; PREREG must be frozen before E1–E3 main runs."
fi
if grep -Eq '\b(error|traceback|exception|nan|wrong|weird|broken|fails?|failing|crash(ed)?|bug|429)\b' <<<"$p"; then
  echo "Checkpoint: state the root cause before proposing a fix. Runtime failure → logs/ERROR_LOG.md. Our code was wrong → logs/BUGS_LOG.md with affected results."
fi
if grep -Eq '\b(report|draft|abstract|paper)\b' <<<"$p"; then
  echo "Checkpoint (PRD §11, CLAUDE.md §8): numbers only from report_numbers.json, citations only ✔ from CITATIONS.md, no em dashes, run trace_numbers.py."
fi
exit 0
EOF

put .claude/hooks/stop_gate.sh <<'EOF'
#!/usr/bin/env bash
# Stop: block on failing fast tests; nudge for log entries. Loop-guarded.
input=$(cat)
[[ "$(jq -r '.stop_hook_active // false' <<<"$input" 2>/dev/null)" == "true" ]] && exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
git status --porcelain 2>/dev/null | grep -q . || exit 0
rc=0
if git status --porcelain 2>/dev/null | grep -q '\.py$'; then
  out=$(timeout 150 uv run -q pytest -x -q -m "not slow" 2>&1); rc=$?
fi
if [[ $rc -ne 0 && $rc -ne 5 ]]; then
  jq -n --arg r "Fast tests fail (pytest exit $rc). Fix or explain before finishing:
$(tail -n 25 <<<"$out")" '{decision:"block", reason:$r}'
  exit 0
fi
log=logs/BUILD_LOG.md
if [[ -n $(find src scripts -name '*.py' -newer "$log" -print -quit 2>/dev/null) ]]; then
  jq -n '{hookSpecificOutput:{hookEventName:"Stop",additionalContext:"Append a dated IST entry to logs/BUILD_LOG.md (template in header). Runtime errors → ERROR_LOG.md; bugs in our code → BUGS_LOG.md; validity threats → CHALLENGES_LOG.md; AI assistance → LLM_USAGE.md. Then commit the finished task (/commit, CLAUDE.md §9) and finish."}}'
  exit 0
fi
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  jq -n '{hookSpecificOutput:{hookEventName:"Stop",additionalContext:"Tests pass and there are uncommitted changes. If a task is finished, commit it now with a plain-English message (/commit, CLAUDE.md §9); push if it was a milestone."}}'
fi
exit 0
EOF

put .claude/commands/check.md <<'EOF'
---
description: Lint, type-check, run free tests, log the result
---
Run `bash scripts/check.sh` (it appends to logs/TEST_LOG.md). If anything fails: state the root cause first, fix, re-run. Runtime failures go in logs/ERROR_LOG.md; logic bugs in our code go in logs/BUGS_LOG.md.
EOF

put .claude/commands/log.md <<'EOF'
---
description: Append log entries for the work just done
---
Append a dated IST entry to logs/BUILD_LOG.md using the template in its header (PRD ref, file:lines, tests, smoke result, LLM calls used). Also: errors → logs/ERROR_LOG.md; bugs in our code → logs/BUGS_LOG.md; anything surprising or validity-threatening → logs/CHALLENGES_LOG.md; decisions → logs/PLANNING_LOG.md; AI assistance → logs/LLM_USAGE.md. Update docs/TASKS.md checkboxes.
EOF

put .claude/commands/bug.md <<'EOF'
---
description: Record a bug in our code with its blast radius
---
Add a B### entry to logs/BUGS_LOG.md (template in header): severity, how found, symptom, root cause file:line, fix + regression test, and which runs/figures/tables were affected. If any reported number was affected, regenerate it (analyse + figures) and say so in the entry.
EOF

put .claude/commands/gate.md <<'EOF'
---
description: Evaluate a PRD §10 gate (G0–G3) and record the decision
---
Evaluate the gate named in my message exactly as docs/PRD.md §10 defines it, using real outputs (tests, registry, calibration numbers). Write the outcome as the next D### in logs/PLANNING_LOG.md with the evidence. If it fails, propose the PRD §10 fallback; do not change PREREG thresholds.
EOF

put .claude/commands/commit.md <<'EOF'
---
description: Commit the finished task with a plain-English message (CLAUDE.md §9)
---
1. Run `bash scripts/check.sh`. If it fails, fix it first (or say clearly in the message why it can't pass yet).
2. Run `git status` and `git diff --stat`. Make sure no `.env`, `results/raw/**/protocols/`, `logs/runs/` or a hand-edited `README.md` is staged.
3. Stage only the files for this one task (logs included).
4. Write the message per CLAUDE.md §9: a short, plain-English subject starting with a verb (≤ 72 chars), plus a short body if the change isn't obvious: what changed, why, anything a reader must know. Show me the message, then commit.
5. If this finishes a milestone or gate, `git push`.
EOF

put .claude/commands/book.md <<'EOF'
---
description: Build the one-page Project Book
---
Run `uv run python scripts/build_book.py`, then report the part count and the file sizes of docs/PROJECT_BOOK.md and docs/PROJECT_BOOK.html.
EOF

put .claude/commands/trace.md <<'EOF'
---
description: Check every number in report/README/RESULTS traces to report_numbers.json
---
Run `uv run python scripts/trace_numbers.py report/DRAFT.md results/RESULTS.md` (add README.md only after it is filled at the end). For each untraced number, find its true source in results/processed/ and fix the text; never add numbers to report_numbers.json by hand.
EOF

chmod +x .claude/hooks/*.sh
echo "  files: ${CREATED} created, ${KEPT} kept (existing; FORCE=1 to overwrite scaffold)"

# ---------------------------------------------------------------------------------- 9
step "9. Python environment"
if uv sync -q 2>/tmp/cw_uv.txt; then ok "uv sync (numpy, pandas, scipy, sklearn, matplotlib, adaption, openai, dotenv, yaml, markdown, ruff, pytest, pyright)"
else bad "uv sync failed:"; tail -n 20 /tmp/cw_uv.txt; fi
uv run -q python scripts/make_placeholders.py >/dev/null 2>&1 && ok "placeholder figures (README template renders now)"
if uv run -q pytest -q -m "not slow" >/tmp/cw_t.txt 2>&1; then ok "scaffold self-tests pass ($(tail -n1 /tmp/cw_t.txt))"
else warn "scaffold self-tests failed:"; tail -n 20 /tmp/cw_t.txt; fi
uv run -q python scripts/build_book.py >/dev/null 2>&1 && ok "Project Book built (docs/PROJECT_BOOK.html)"

# ---------------------------------------------------------------------------------- 10
step "10. Data (optional; FETCH_DATA=1)"
if [[ "${FETCH_DATA:-0}" == "1" ]]; then
  [[ -f data/swarmtraces/redacted.jsonl.gz ]] || curl -fsSL -o data/swarmtraces/redacted.jsonl.gz \
     https://swarmtraces.org/data/final/redacted.jsonl.gz && ok "Swarm Traces → data/swarmtraces/" || warn "Swarm Traces download failed"
  [[ -f data/metr_report.pdf ]] || curl -fsSL -o data/metr_report.pdf \
     https://metr.org/hugging-face-incident-report-aug-2026.pdf && ok "METR report → data/metr_report.pdf" || warn "METR download failed"
else
  warn "skipped (FETCH_DATA=1 bash setup.sh to download Swarm Traces + METR report, both gitignored)"
fi

# ---------------------------------------------------------------------------------- 11
step "11. Git (repo: Swarm-Alignment-Hackathon; scaffold = one readable commit)"
GITC=(git -c user.name="$(git config user.name || echo sprint)" -c user.email="$(git config user.email || echo sprint@localhost)")
if [[ ! -d .git ]]; then
  warn "not a clone; connecting this folder to $REPO_URL"
  git init -q -b main 2>/dev/null || git init -q
  git remote add origin "$REPO_URL"
  if git fetch -q origin main 2>/dev/null; then
    git reset -q origin/main                       # keep our files, adopt the remote history
    [[ -f README.md ]] || git checkout -q origin/main -- README.md 2>/dev/null
    ok "linked to origin/main ($(git rev-parse --short origin/main))"
  else
    warn "could not fetch $REPO_URL (offline?); local repo only"
  fi
else
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REPO_URL"
  ok "git repo exists (origin: $(git remote get-url origin))"
fi
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  if git diff --cached --name-only | grep -Eq '(^|/)[.]env$|/protocols/'; then
    bad "refusing to commit: .env or protocols staged"; git reset -q
  else
    "${GITC[@]}" commit -qm "Set up the project skeleton: folders, logs, tests and tooling" \
      -m "Adds the plan (PRD, CLAUDE.md, build prompts, README template) and everything setup.sh creates:
empty logs, report outline, test scaffold, helper scripts and Claude Code hooks.
No experiment code yet. README.md stays GitHub's stub until the final results are in."
    ok "committed scaffold: $(git log -1 --format='%h %s')"
  fi
else ok "nothing new to commit"; fi
TODO+=("Push the scaffold:  git push -u origin main   (then Claude commits after every task, pushes at milestones)")

# ---------------------------------------------------------------------------------- 12
step "12. Claude Code plugins + MCP (optional)"
if [[ "${SKIP_PLUGINS:-0}" == "1" ]] || ! have claude; then
  warn "skipped"
else
  claude plugin install pyright-lsp@claude-plugins-official >/dev/null 2>&1 \
    && ok "plugin pyright-lsp" || TODO+=("(optional) In Claude Code: /plugin install pyright-lsp@claude-plugins-official")
  claude mcp add --transport stdio --scope user arxiv -- uvx arxiv-mcp-server >/dev/null 2>&1 \
    && ok "arXiv MCP (citation checks)" || warn "arXiv MCP already added or failed (optional)"
fi

# ---------------------------------------------------------------------------------- done
[[ -f .env ]] && ok ".env exists (not read by this script)" || TODO+=("Adaption: https://adaptionlabs.ai/app (sprint email) → Settings → API keys → create key; check credit balance")
TODO+=("cp .env.example .env  and paste ADAPTION_API_KEY (+ optional free fallback keys)")
TODO+=("Copy the official report template (link on the sprint page); fill title/authors/affiliations")
step "DONE: remaining manual steps"
i=1; for t in "${TODO[@]}"; do echo "  $i. $t"; i=$((i+1)); done
cat <<EOF

${b}Next:${n}
  1) claude                         # open Claude Code in this folder
  2) paste Prompt 1 from docs/KICKOFF.md
  Deadline: Mon 9 Nov 17:29 IST · submit target 16:00 IST · writing starts 13:00 IST
EOF
