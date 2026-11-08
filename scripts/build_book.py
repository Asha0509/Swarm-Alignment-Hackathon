#!/usr/bin/env python3
"""Build the Project Book: every project MD file in one page (PRD FR-16).

Outputs docs/PROJECT_BOOK.md and a self-contained docs/PROJECT_BOOK.html (TOC sidebar, figures inlined).
Usage: python scripts/build_book.py [--out docs]
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER = [
    ("Overview (README)", "README.md"),  # falls back to docs/README_TEMPLATE.md until filled
    ("Product Requirements (PRD)", "docs/PRD.md"),
    ("How We Work (CLAUDE.md)", "CLAUDE.md"),
    ("Build Prompts (KICKOFF)", "docs/KICKOFF.md"),
    ("Pre-registration", "PREREG.md"),
    ("Pre-existing Code", "PREEXISTING.md"),
    ("Results", "results/RESULTS.md"),
    ("Report Draft", "report/DRAFT.md"),
    ("Figure Captions", "report/FIGURES.md"),
    ("Citations", "report/CITATIONS.md"),
    ("Tasks", "docs/TASKS.md"),
    ("Planning Log", "logs/PLANNING_LOG.md"),
    ("Build Log", "logs/BUILD_LOG.md"),
    ("Test Log", "logs/TEST_LOG.md"),
    ("Error Log", "logs/ERROR_LOG.md"),
    ("Bugs Log", "logs/BUGS_LOG.md"),
    ("Challenges Log", "logs/CHALLENGES_LOG.md"),
    ("LLM Usage", "logs/LLM_USAGE.md"),
]
IMG_MD = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
IMG_HTML = re.compile(r'(<img[^>]*src=")([^"]+)(")')
COMMENT = re.compile(r"<!--.*?-->", re.S)
CSS = """body{font-family:-apple-system,Segoe UI,Inter,sans-serif;margin:0;display:flex;color:#1d1d1f}
nav{position:sticky;top:0;height:100vh;overflow:auto;width:270px;flex:none;background:#f5f5f7;
padding:20px;box-sizing:border-box;border-right:1px solid #ddd;font-size:14px}
nav a{display:block;color:#333;text-decoration:none;padding:4px 0}nav a:hover{color:#0a58ca}
main{max-width:980px;padding:32px 48px;line-height:1.55}
h1{border-bottom:2px solid #eee;padding-bottom:6px;margin-top:56px}
table{border-collapse:collapse;margin:12px 0;font-size:14px}td,th{border:1px solid #ddd;padding:6px 9px}
th{background:#fafafa}code{background:#f3f3f3;padding:1px 4px;border-radius:4px}
pre{background:#f6f8fa;padding:12px;overflow:auto;border-radius:6px}img{max-width:100%}
.part{color:#888;font-size:12px;text-transform:uppercase;letter-spacing:.08em}"""


def shift_headings(md: str) -> str:
    out, fence = [], False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
        out.append("#" + line if (not fence and line.startswith("#")) else line)
    return "\n".join(out)


def rebase(md: str, src: Path, out_dir: Path) -> str:
    def fix(path: str) -> str:
        if re.match(r"^(https?:|data:|#)", path):
            return path
        return os.path.relpath((src.parent / path).resolve(), out_dir.resolve())
    md = IMG_MD.sub(lambda m: f"![{m.group(1)}]({fix(m.group(2))})", md)
    return IMG_HTML.sub(lambda m: m.group(1) + fix(m.group(2)) + m.group(3), md)


def inline_images(html: str, base: Path) -> str:
    def sub(m: re.Match[str]) -> str:
        p = (base / m.group(2)).resolve()
        if m.group(2).startswith("data:") or not p.exists():
            return m.group(0)
        mime = "image/svg+xml" if p.suffix == ".svg" else f"image/{p.suffix.lstrip('.')}"
        return f'{m.group(1)}data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}{m.group(3)}'
    return re.sub(r'(<img[^>]*src=")([^"]+)(")', sub, html)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "docs"))
    out_dir = Path(ap.parse_args().out)
    out_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M IST")
    parts, toc = [], []
    for i, (title, rel) in enumerate(ORDER, 1):
        src = ROOT / rel
        if rel == "README.md" and (not src.exists() or src.stat().st_size < 500):
            src = ROOT / "docs" / "README_TEMPLATE.md"  # README is filled once at the end
        if not src.exists():
            continue
        anchor = f"part-{i}"
        body = rebase(COMMENT.sub("", src.read_text()), src, out_dir)
        parts.append(f'<a id="{anchor}"></a>\n\n# {i}. {title}\n\n<p class="part">{rel}</p>\n\n'
                     + shift_headings(body))
        toc.append((anchor, f"{i}. {title}"))
    header = f"# Project Book: Whispering Through the Package Cache\n\n*Built {now} from {len(parts)} files.*\n"
    md = header + "\n\n---\n\n".join([""] + parts)
    (out_dir / "PROJECT_BOOK.md").write_text(md)
    import markdown  # noqa: PLC0415

    html_body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    html_body = inline_images(html_body, out_dir)
    nav = "".join(f'<a href="#{a}">{t}</a>' for a, t in toc)
    html = (f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Project Book</title>"
            f"<style>{CSS}</style></head><body><nav><b>Project Book</b><br><small>{now}</small><hr>{nav}"
            f"</nav><main>{html_body}</main></body></html>")
    (out_dir / "PROJECT_BOOK.html").write_text(html)
    print(f"✔ {out_dir/'PROJECT_BOOK.md'} and .html ({len(parts)} parts)")


if __name__ == "__main__":
    main()
