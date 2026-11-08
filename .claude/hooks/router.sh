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
