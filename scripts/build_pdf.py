"""Render report/REPORT.md into a PDF that follows the Apart submission template layout.

Template elements: centered title with a footnote marker, centered author block, "With Apart Research",
an "Abstract" heading with the abstract in a shaded box, the hackathon footnote, numbered sections in a
serif face, and orphan-free headings. Run: uv run --with fpdf2 --with pillow python scripts/build_pdf.py
"""
import re
from pathlib import Path

from fpdf import FPDF
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LINES = (ROOT / "report/REPORT.md").read_text().split("\n")
CW = 215.9 - 2 * 20
BODY = 4.8
FOOTNOTE = "Research conducted at the Apart Research Swarm Alignment Hackathon, November 2026."


class PDF(FPDF):
    def footer(self):
        self.set_y(-14)
        self.set_font("Times", "I", 8)
        self.set_text_color(130)
        self.cell(0, 8, f"{self.page_no()}", align="C")
        self.set_text_color(0)


pdf = PDF(format="letter", unit="mm")
pdf.set_margins(22, 18, 22)
pdf.set_auto_page_break(True, 18)
pdf.alias_nb_pages()
pdf.add_page()


def clean(s):
    return s.replace("`", "")


def room(mm):
    if pdf.get_y() + mm > pdf.page_break_trigger:
        pdf.add_page()


def para(s, size=10, style="", gap=1.4, align="J", fill=None):
    pdf.set_font("Times", style, size)
    if fill:
        pdf.set_fill_color(*fill)
    pdf.multi_cell(0, BODY, clean(s), markdown=True, align=align, fill=bool(fill), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(gap)


def heading(text, size, before, keep):
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
        h = 4.0 * max(1, *[len(pdf.multi_cell(w, 4.0, c, dry_run=True, output="LINES")) for c in r])
        room(h + 2)
        y0 = pdf.get_y()
        for ci, c in enumerate(r):
            pdf.set_xy(22 + ci * w, y0)
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
    w = min(CW, 140)
    h = w * ih / iw
    room(h + 4)
    pdf.image(str(p), x=(215.9 - w) / 2, w=w)
    pdf.ln(3)


def title_block(title):
    pdf.set_font("Times", "B", 17)
    pdf.ln(4)
    pdf.multi_cell(0, 7.2, clean(title), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def author_block(author_line):
    s = author_line.replace("**Author:**", "").strip()
    left, _, _ = s.partition("With Apart Research")
    left = left.strip().rstrip(".").strip()
    name, _, affil = left.partition(",")
    pdf.set_font("Times", "B", 11)
    pdf.multi_cell(0, 5.4, name.strip(), align="C", new_x="LMARGIN", new_y="NEXT")
    if affil.strip():
        pdf.set_font("Times", "", 10)
        pdf.multi_cell(0, 5.0, affil.strip(), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 10)
    pdf.multi_cell(0, 5.0, "With Apart Research", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)


i = 0
abstract_done = False
footnote_placed = False
while i < len(LINES):
    line = LINES[i]
    if line.startswith("# "):
        title_block(line[2:])
        i += 1
        continue
    if line.startswith("**Author:**"):
        author_block(line)
        i += 1
        continue
    if line.startswith("## Abstract"):
        pdf.set_font("Times", "B", 12)
        pdf.cell(0, 6, "Abstract", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        # gather abstract body until the next --- or heading
        i += 1
        body = []
        while i < len(LINES) and not LINES[i].startswith("## ") and LINES[i].strip() != "---":
            if LINES[i].strip():
                body.append(LINES[i].strip())
            i += 1
        pdf.set_fill_color(255, 244, 214)
        pdf.set_font("Times", "", 9.6)
        pdf.multi_cell(0, 4.6, clean(" ".join(body)), align="J", fill=True,
                       new_x="LMARGIN", new_y="NEXT", padding=2)
        pdf.ln(1)
        # hackathon footnote under the abstract (template places it at the page foot)
        pdf.set_font("Times", "I", 8)
        pdf.set_text_color(120)
        pdf.multi_cell(0, 4, FOOTNOTE, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0)
        pdf.ln(1)
        footnote_placed = True
        continue
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
    if line.startswith("## "):
        heading(line[3:], 12.5, before=2.2, keep=28)
        i += 1
        continue
    if line.startswith("### "):
        heading(line[4:], 10.5, before=1.0, keep=20)
        i += 1
        continue
    if line.startswith("> "):
        para(line[2:], size=9, fill=(236, 240, 245), gap=0.3)
        i += 1
        continue
    if re.match(r"^\d+\. ", line):
        room(12)
        pdf.set_font("Times", "", 10)
        pdf.multi_cell(0, BODY, clean("   " + line), markdown=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)
        i += 1
        continue
    if line.startswith("- "):
        room(10)
        pdf.set_font("Times", "", 10)
        pdf.multi_cell(0, BODY, clean("   -  " + line[2:]), markdown=True, new_x="LMARGIN", new_y="NEXT")
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
    para(line)
    i += 1

OUT = ROOT / "report/final/Whispering-Through-the-Package-Cache.pdf"
pdf.output(str(OUT))
print("wrote", OUT, "pages:", pdf.page_no())
