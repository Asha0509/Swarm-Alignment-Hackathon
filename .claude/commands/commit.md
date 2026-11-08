---
description: Commit the finished task with a plain-English message (CLAUDE.md §9)
---
1. Run `bash scripts/check.sh`. If it fails, fix it first (or say clearly in the message why it can't pass yet).
2. Run `git status` and `git diff --stat`. Make sure no `.env`, `results/raw/**/protocols/`, `logs/runs/` or a hand-edited `README.md` is staged.
3. Stage only the files for this one task (logs included).
4. Write the message per CLAUDE.md §9: a short, plain-English subject starting with a verb (≤ 72 chars), plus a short body if the change isn't obvious: what changed, why, anything a reader must know. Show me the message, then commit.
5. If this finishes a milestone or gate, `git push`.
