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
