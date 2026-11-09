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
> uv run python scripts/trace_numbers.py report/REPORT.md results/RESULTS.md
book:
> uv run python scripts/build_book.py
all: check analyse figures trace book
