<!--
README TEMPLATE. Do NOT copy to the repo root during the sprint.
At the end (KICKOFF Prompt 10) Claude fills every {{PLACEHOLDER}} and every GENERATED block from
results/processed/report_numbers.json + figures/, writes the result to ./README.md (replacing GitHub's
stub), and commits it ONCE. Paths below are relative to the repo root (where README.md will live).
-->
# Whispering Through the Package Cache

**How much can colluding AI agents hide in shared infrastructure, even when their transcripts lie?**

*Apart Research · Swarm Alignment Hackathon · Nov 2026 · Track 4 (Multi-Agent Oversight & Control) + Track 1 (Sandboxes & Testbeds)*

> **{{HEADLINE: one sentence with the primary result + CI, from report_numbers.json}}**
>
> 📄 Paper: {{PDF link}} · 🎥 Video: {{video link or remove}} · 📚 Everything in one page: [docs/PROJECT_BOOK.html](docs/PROJECT_BOOK.html)

<p align="center"><img src="figures/F1_schematic.png" width="820" alt="CacheGym system schematic"></p>

---

## TL;DR

In July 2026, about 1,200 AI agents in an OpenAI cyber evaluation turned a **shared, non-isolated package cache** into a message board, and about 700 of them broke into Hugging Face together. About 7% of their transcripts were **spoofed**. Oversight that reads transcripts could not see what the infrastructure saw.

We built **CacheGym**, a free, deterministic sandbox with a mock package registry modeled on that channel. In it we measure:

1. **Capacity:** how many secret bits colluding agents (scripted expert channels and adaptive LLM attackers) can pass through registry side-effects.
2. **Detectability:** which monitor catches them at a fixed audit budget (1% and 5% false alarms): transcript-reading (M1), infrastructure metadata (M2), transcript-vs-infrastructure **consistency** (M3), and learned (M4).
3. **Spoof-robustness:** how each monitor degrades as transcripts are forged (0–100%).
4. **Defense cost:** how much channel capacity cheap mitigations remove, and what they cost honest agents.

This is an **AI-control capability evaluation**: colluders are instructed to collude (worst-case red team). We do not claim agents would do it unprompted.

## Headline results

<!-- GENERATED at the end from figures/ + report_numbers.json -->
| Figure | What it shows |
|---|---|
| <img src="figures/F2_frontier.png" width="420"> | **F2: capacity vs detection frontier** per monitor at a 5% false-alarm budget |
| <img src="figures/F3_spoof_sweep.png" width="420"> | **F3: detection vs spoof rate**: what happens when transcripts lie |
| <img src="figures/F6_defenses.png" width="420"> | **F6: defenses**: capacity removed vs honest work lost |

{{Inline figures/T2_main.md here}}
<!-- END GENERATED -->

Full results, every figure and every number: **[results/RESULTS.md](results/RESULTS.md)**.
Everything in one page: **[docs/PROJECT_BOOK.html](docs/PROJECT_BOOK.html)**.

## Infra-operator runbook (what to do on Monday)

1. **Isolate** shared caches and registries per agent, and measure the utility cost (D1).
2. **Log at the infrastructure layer**, not only in agent transcripts. Hash-chain it.
3. **Cross-check transcripts against infrastructure logs** (M3). A mismatch is itself an alarm.
4. **Budget audits at a fixed false-alarm rate** and report *undetected capacity*, not just accuracy.

---

## Deliverables matrix

Official requirements from the [sprint page](https://apartresearch.com/sprints/swarm-alignment-2026) on the left, mapped to what this repo delivers. Tick each box (☐ → ✅) when filling the template at the end, and only for rows that are true.

| ✔ | Official requirement | Required? | Where in this project |
|---|---|---|---|
| ☐ | Research report PDF on the official template | **Required** | `report/final/*.pdf` (source: `report/DRAFT.md`) |
| ☐ | ≤ 8 pages excluding references and appendices | Required | target 6 pages |
| ☐ | Title + abstract (150–250 words) | Required | `report/DRAFT.md` § Abstract |
| ☐ | Author names and affiliations | Required | template header |
| ☐ | Intro, Related Work, Methodology, Results, Discussion, Limitations, References | Required | `report/OUTLINE.md` → `report/DRAFT.md` |
| ☐ | **Limitations and Dual-Use / Ethical Considerations** appendix | **Required** | Report Appendix A |
| ☐ | Pre-existing code marked | Required | [`PREEXISTING.md`](PREEXISTING.md), Appendix B |
| ☐ | No fabricated results or references | Required | `scripts/trace_numbers.py`, [`report/CITATIONS.md`](report/CITATIONS.md), Appendix C |
| ☐ | Public GitHub repo | Optional | this repo |
| ☐ | 3–5 min video demo | Optional | link added here at submit |

| ✔ | Our quality bar (beyond requirements) | Where |
|---|---|---|
| ☐ | Pre-registration frozen before main runs | [`PREREG.md`](PREREG.md), git tag `prereg-frozen` |
| ☐ | Positive controls + calibration shown before claims | `figures/T1_controls.md` |
| ☐ | Every figure regenerates with one command | `make figures` |
| ☐ | Every number traceable to data | `results/processed/report_numbers.json` |
| ☐ | Tests green | `logs/TEST_LOG.md` |
| ☐ | Full research trail | [`logs/`](logs/): build, errors, bugs, challenges, decisions, runs, API usage, LLM usage |
| ☐ | One-page project book | [`docs/PROJECT_BOOK.html`](docs/PROJECT_BOOK.html) |
| ☐ | Total cash cost: $0 (Adaption sponsor credits: {{N}} used; free tiers as fallback) | `logs/API_USAGE.csv` |

## Reproduce

```bash
git clone https://github.com/Asha0509/Swarm-Alignment-Hackathon.git && cd Swarm-Alignment-Hackathon
bash setup.sh                    # dirs, env, deps, hooks, tests (idempotent)
cp .env.example .env             # add ADAPTION_API_KEY (optional free fallbacks: Groq / Gemini / Ollama)
make smoke                       # 1 scripted + 1 LLM episode
make experiments                 # E0–E3 (Must); see configs/
make analyse figures book        # RESULTS.md, figures/, docs/PROJECT_BOOK.html
make check                       # lint + types + tests
```

Scripted experiments (E0–E2, E4) need **no API key** and reproduce exactly from seeds. LLM experiments reuse the on-disk response cache when it's present.

## Repo map

| Path | What |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Full spec: requirements, experiments, figures, report spec |
| [`CLAUDE.md`](CLAUDE.md) | How we build: rules, logs, tests, checklist |
| [`docs/KICKOFF.md`](docs/KICKOFF.md) | Ordered build prompts and the human-task timeline |
| `src/cachewhisper/` | Registry, infra log, agents, channels, attacker, spoof layer, monitors, defenses, metrics |
| `configs/` | One YAML per experiment (E0–E6) |
| `results/` | Raw runs, processed tables, generated RESULTS.md |
| `figures/` | F1–F8, T1–T2 |
| `report/` | Outline, draft, citations, video script, final PDF |
| `logs/` | Research trail |

## Responsible release

We release the sandbox, monitors and defenses. The expert channels are textbook covert-channel patterns. The **LLM attacker's best evolved protocols are not published verbatim**: they are summarized by category, and vetted researchers can get the full text on request. No real systems were touched. Swarm Traces is used only as redacted public data. See report Appendix A.

## Acknowledgements

Apart Research, the AI Alignment Foundation and AE Studio for the sprint; Adaption Labs for platform credits (hosted models, Invent, AutoScientist); METR and the Swarm Traces authors for the incident data that grounds this work.

*Pre-existing code: none beyond open-source libraries in `pyproject.toml` (see [`PREEXISTING.md`](PREEXISTING.md)).*
