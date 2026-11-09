---
description: Check every number in report/README/RESULTS traces to report_numbers.json
---
Run `uv run python scripts/trace_numbers.py report/REPORT.md results/RESULTS.md` (add README.md only after it is filled at the end). For each untraced number, find its true source in results/processed/ and fix the text; never add numbers to report_numbers.json by hand.
