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
