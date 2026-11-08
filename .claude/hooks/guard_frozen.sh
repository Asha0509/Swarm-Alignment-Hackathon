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
