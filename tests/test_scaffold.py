"""Scaffold self-tests: repo structure and the doc/trace tooling work before any sprint code exists."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_package_imports() -> None:
    import cachewhisper

    assert cachewhisper.__version__


def test_required_files_exist() -> None:
    for p in ["CLAUDE.md", "docs/PRD.md", "PREREG.md", "PREEXISTING.md", "logs/BUGS_LOG.md",
              "logs/RUN_REGISTRY.csv", "logs/API_USAGE.csv", "report/CITATIONS.md"]:
        assert (ROOT / p).exists(), p


def test_trace_numbers_flags_unknown(tmp_path: Path) -> None:
    nums = tmp_path / "n.json"
    nums.write_text(json.dumps({"primary": {"diff": 3.41, "ci": [1.2, 5.6]}, "tpr": 0.873}))
    good = tmp_path / "good.md"
    good.write_text("Difference 3.41 bits (CI 1.2 to 5.6), TPR 87.3%.\n")
    bad = tmp_path / "bad.md"
    bad.write_text("Difference 9.99 bits.\n")
    script = ROOT / "scripts" / "trace_numbers.py"
    ok = subprocess.run([sys.executable, str(script), "--numbers", str(nums), str(good)], capture_output=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    ko = subprocess.run([sys.executable, str(script), "--numbers", str(nums), str(bad)], capture_output=True)
    assert ko.returncode == 1


def test_build_book_runs(tmp_path: Path) -> None:
    out = tmp_path / "book"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_book.py"), "--out", str(out)],
                       capture_output=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (out / "PROJECT_BOOK.md").stat().st_size > 1000
    html = (out / "PROJECT_BOOK.html").read_text()
    assert "<nav" in html and "PRD" in html
