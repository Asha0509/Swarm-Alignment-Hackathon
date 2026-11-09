import re
from pathlib import Path
from fpdf import FPDF
from PIL import Image

ROOT = Path("/home/asha/Swarm-Alignment-Hackathon/Swarm-Alignment-Hackathon")
lines = (ROOT / "report/REPORT.md").read_text().split("\n")
CW = 215.9 - 2*20

class PDF(FPDF):
    def footer(self):
        self.set_y(-14); self.set_font("Times", "I", 8); self.set_text_color(130)
        self.cell(0, 8, f"{self.page_no()} of {{nb}}", align="C"); self.set_text_color(0)

pdf = PDF(format="letter", unit="mm")
pdf.set_margins(20, 18, 20); pdf.set_auto_page_break(True, 16); pdf.alias_nb_pages()
pdf.add_page()
def clean(s): return s.replace("`", "")

def para(s, size=10, style="", gap=1.4, align="J", fill=False, font="Times"):
    pdf.set_font(font, style, size)
    if fill: pdf.set_fill_color(255, 247, 214)
    pdf.multi_cell(0, 4.8, clean(s), markdown=True, align=align, fill=fill, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(gap)

def table(rows):
    cells = [[c.strip().replace("**","") for c in r.split("|")[1:-1]] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r"\s*:?-+:?\s*", c or " ") for c in r)]
    if not cells: return
    ncol = max(len(r) for r in cells); w = CW/ncol
    for ri, r in enumerate(cells):
        r = r + [""]*(ncol-len(r))
        pdf.set_font("Times", "B" if ri==0 else "", 8.5)
        h = 4.0*max(1, *[len(pdf.multi_cell(w, 4.0, c, split_only=True)) for c in r])
        if pdf.get_y()+h > pdf.page_break_trigger: pdf.add_page()
        y0 = pdf.get_y()
        for ci, c in enumerate(r):
            pdf.set_xy(20+ci*w, y0)
            pdf.set_font("Times", "B" if ri==0 else "", 8.5)
            if ri==0: pdf.set_fill_color(230,230,230)
            pdf.multi_cell(w, 4.0, c, border=1, align="L", fill=(ri==0), max_line_height=4.0, new_x="RIGHT", new_y="TOP")
        pdf.set_y(y0+h)
    pdf.ln(2)

i = 0; title_done = False
while i < len(lines):
    l = lines[i]
    if re.match(r"^\|.*\|", l):
        rows=[]
        while i < len(lines) and re.match(r"^\|.*\|", lines[i]): rows.append(lines[i]); i+=1
        table(rows); continue
    m = re.match(r"^!\[.*?\]\((.+?)\)", l)
    if m:
        p = (ROOT/"report"/m.group(1)).resolve()
        if p.exists():
            iw, ih = Image.open(p).size; w = min(CW, 145); h = w*ih/iw
            if pdf.get_y()+h+4 > pdf.page_break_trigger: pdf.add_page()
            pdf.image(str(p), x=(215.9-w)/2, w=w); pdf.ln(3)
        i+=1; continue
    if l.startswith("# "):
        pdf.set_font("Times","B",15); pdf.multi_cell(0,6.4,clean(l[2:]),align="C",new_x="LMARGIN",new_y="NEXT"); pdf.ln(1)
        i+=1; continue
    if l.startswith("## "):
        pdf.ln(1.5); para(l[3:], size=12, style="B", gap=1.2); i+=1; continue
    if l.startswith("### "):
        para(l[4:], size=10.5, style="B", gap=0.6); i+=1; continue
    if l.startswith("> "):
        para(l[2:], size=9, fill=True, gap=0.3); i+=1; continue
    if re.match(r"^\d+\. ", l):
        pdf.set_font("Times","",10); pdf.multi_cell(0,4.8,clean("   "+l),markdown=True,new_x="LMARGIN",new_y="NEXT"); pdf.ln(0.5); i+=1; continue
    if l.startswith("- "):
        pdf.set_font("Times","",10); pdf.multi_cell(0,4.8,clean("   -  "+l[2:]),markdown=True,new_x="LMARGIN",new_y="NEXT"); pdf.ln(0.5); i+=1; continue
    if re.fullmatch(r"\s*", l) or l.strip()=="---": i+=1; continue
    if l.startswith("*") and l.endswith("*") and not l.startswith("**"):
        para(l.strip("*"), size=9, style="I", align="C", gap=1)
        if not title_done:  # add hackathon footnote right after the affiliation italic line
            pass
        i+=1; continue
    # author line with **Author:** -> center it, and add 'With Apart Research' footnote after abstract handled in md
    if l.startswith("**Author:**"):
        para(l.replace("**Author:**","Author:"), size=10, align="C", gap=0.5); i+=1; continue
    para(l); i+=1

out = ROOT/"report/final/Whispering-Through-the-Package-Cache.pdf"
pdf.output(str(out)); print("wrote", out, "pages:", pdf.page_no())
