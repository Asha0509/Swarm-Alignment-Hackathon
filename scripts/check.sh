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
