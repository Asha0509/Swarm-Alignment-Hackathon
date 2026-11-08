#!/usr/bin/env bash
# Smoke: 1 scripted + 1 LLM episode (<= 30 calls). Implemented in KICKOFF Prompt 1/2 as cachewhisper.smoke.
set -euo pipefail
cd "$(dirname "$0")/.."
if ! uv run python -c "import cachewhisper.smoke" 2>/dev/null; then
  echo "cachewhisper.smoke not built yet (KICKOFF Prompt 1)."; exit 1
fi
uv run python -m cachewhisper.smoke "$@"
