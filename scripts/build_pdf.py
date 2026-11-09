"""Render report/REPORT.md into a template-style academic PDF (serif, letter) with orphan-free headings.

Run: uv run --with fpdf2 --with pillow python scripts/build_pdf.py
Excluded from ruff/pyright (optional dependency, one-off build utility).
"""
import re
from pathlib import Path

from fpdf import FPDF
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LINES = (ROOT / "report/REPORT.md").read_text().split("\n")
CW = 215.9 - 2 * 20  # content width, letter, 20mm side margins
BODY_H = 4.8         # body line height


class PDF(FPDF):
    def footer(self):
        self.set_y(-14)
        self.set_font("Times", "I", 8)
        self.set_text_color(130)
        self.cell(0, 8, f"{self.page_no()} of {{nb}}", align="C")
        self.set_text_color(0)


pdf = PDF(format="letter", unit="mm")
pdf.set_margins(20, 18, 20)
pdf.set_auto_page_break(True, 16)
pdf.alias_nb_pages()
pdf.add_page()


def clean(s):
    return s.replace("`", "")


def room(mm):
    """Start a new page if less than `mm` of vertical space remains (keeps headings with their text)."""
    if pdf.get_y() + mm > pdf.page_break_trigger:
        pdf.add_page()


def para(s, size=10, style="", gap=1.4, align="J", fill=False):
    pdf.set_font("Times", style, size)
    if fill:
        pdf.set_fill_color(255, 247, 214)
    pdf.multi_cell(0, BODY_H, clean(s), markdown=True, align=align, fill=fill, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(gap)


def heading(text, size, before, keep):
    """Render a heading, but only after ensuring `keep` mm of room so it never sits alone at a page foot."""
    room(keep)
    pdf.ln(before)
    pdf.set_font("Times", "B", size)
    pdf.multi_cell(0, size * 0.42, clean(text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.2)


def table(rows):
    cells = [[c.strip().replace("**", "") for c in r.split("|")[1:-1]] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r"\s*:?-+:?\s*", c or " ") for c in r)]
    if not cells:
        return
    ncol = max(len(r) for r in cells)
    w = CW / ncol
    for ri, r in enumerate(cells):
        r = r + [""] * (ncol - len(r))
        pdf.set_font("Times", "B" if ri == 0 else "", 8.5)
        heights = [len(pdf.multi_cell(w, 4.0, c, dry_run=True, output="LINES")) for c in r]
        h = 4.0 * max(1, *heights)
        room(h + 2)
        y0 = pdf.get_y()
        for ci, c in enumerate(r):
            pdf.set_xy(20 + ci * w, y0)
            pdf.set_font("Times", "B" if ri == 0 else "", 8.5)
            if ri == 0:
                pdf.set_fill_color(230, 230, 230)
            pdf.multi_cell(w, 4.0, c, border=1, align="L", fill=(ri == 0),
                           max_line_height=4.0, new_x="RIGHT", new_y="TOP")
        pdf.set_y(y0 + h)
    pdf.ln(2)


def image(rel):
    p = (ROOT / "report" / rel).resolve()
    if not p.exists():
        return
    iw, ih = Image.open(p).size
    w = min(CW, 145)
    h = w * ih / iw
    room(h + 4)
    pdf.image(str(p), x=(215.9 - w) / 2, w=w)
    pdf.ln(3)


i = 0
while i < len(LINES):
    line = LINES[i]
    if re.match(r"^\|.*\|", line):
        rows = []
        while i < len(LINES) and re.match(r"^\|.*\|", LINES[i]):
            rows.append(LINES[i])
            i += 1
        table(rows)
        continue
    m = re.match(r"^!\[.*?\]\((.+?)\)", line)
    if m:
        image(m.group(1))
        i += 1
        continue
    if line.startswith("# "):
        pdf.set_font("Times", "B", 15)
        pdf.multi_cell(0, 6.4, clean(line[2:]), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        i += 1
        continue
    if line.startswith("## "):
        heading(line[3:], 13, before=2.0, keep=26)   # keep heading + ~4 body lines together
        i += 1
        continue
    if line.startswith("### "):
        heading(line[4:], 10.5, before=1.0, keep=20)
        i += 1
        continue
    if line.startswith("> "):
        para(line[2:], size=9, fill=True, gap=0.3)
        i += 1
        continue
    if re.match(r"^\d+\. ", line):
        room(12)
        pdf.set_font("Times", "", 10)
        pdf.multi_cell(0, BODY_H, clean("   " + line), markdown=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)
        i += 1
        continue
    if line.startswith("- "):
        room(10)
        pdf.set_font("Times", "", 10)
        pdf.multi_cell(0, BODY_H, clean("   -  " + line[2:]), markdown=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)
        i += 1
        continue
    if re.fullmatch(r"\s*", line) or line.strip() == "---":
        i += 1
        continue
    if line.startswith("*") and line.endswith("*") and not line.startswith("**"):
        para(line.strip("*"), size=9, style="I", align="C", gap=1)
        i += 1
        continue
    if line.startswith("**Author:**"):
        para(line.replace("**Author:**", "Author:"), size=10, align="C", gap=0.5)
        i += 1
        continue
    para(line)
    i += 1

OUT = ROOT / "report/final/Whispering-Through-the-Package-Cache.pdf"
pdf.output(str(OUT))
print("wrote", OUT, "pages:", pdf.page_no())
