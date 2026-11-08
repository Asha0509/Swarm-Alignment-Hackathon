#!/usr/bin/env bash
# PostToolUse: report-only ruff check on the edited .py file (real bugs only).
input=$(cat)
f=$(jq -r '.tool_input.file_path // empty' <<<"$input" 2>/dev/null)
[[ "$f" == *.py && -f "$f" ]] || exit 0
out=$(uvx ruff check -q --isolated --select F,E9,B --output-format concise "$f" 2>/dev/null) && exit 0
jq -n --arg m "ruff found real bugs in $f. Fix before moving on:
$out" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$m}}'
exit 0
