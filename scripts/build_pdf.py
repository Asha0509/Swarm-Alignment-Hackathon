import re, sys
from pathlib import Path
from fpdf import FPDF

ROOT = Path("/home/asha/Swarm-Alignment-Hackathon/Swarm-Alignment-Hackathon")
md = (ROOT / "report/REPORT.md").read_text().split("\n")
CW = 215.9 - 2*20  # content width, letter, 20mm margins

class PDF(FPDF):
    def footer(self):
        self.set_y(-15); self.set_font("Helvetica", "I", 8); self.set_text_color(130)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="C")
        self.set_text_color(0)

pdf = PDF(format="letter", unit="mm")
pdf.set_margins(20, 18, 20); pdf.set_auto_page_break(True, 18); pdf.alias_nb_pages()
pdf.add_page()

def txt(s):  # strip inline md fpdf won't render
    return s.replace("`", "")

def para(s, size=10, style="", gap=1.6, align="J", fill=False):
    pdf.set_font("Helvetica", style, size)
    if fill:
        pdf.set_fill_color(255, 247, 214)
    pdf.multi_cell(0, 5, txt(s), markdown=True, align=align, fill=fill, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(gap)

def table(rows):
    cells = [r.split("|")[1:-1] for r in rows]
    cells = [[c.strip().replace("**","") for c in r] for r in cells if not all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in r.split("|")[1:-1])]
    if not cells: return
    ncol = max(len(r) for r in cells); w = CW/ncol
    pdf.set_font("Helvetica", "", 8)
    for ri, r in enumerate(cells):
        r = r + [""]*(ncol-len(r))
        hs = [pdf.get_string_width(c)//w + 1 for c in r]
        h = 4.2 * max(1, *( [len(pdf.multi_cell(w, 4.2, c, split_only=True)) for c in r] ))
        y0 = pdf.get_y()
        if y0 + h > pdf.page_break_trigger: pdf.add_page(); y0 = pdf.get_y()
        for ci, c in enumerate(r):
            x = 20 + ci*w
            pdf.set_xy(x, y0)
            pdf.set_font("Helvetica", "B" if ri == 0 else "", 8)
            if ri == 0: pdf.set_fill_color(232,232,232)
            pdf.multi_cell(w, 4.2, c, border=1, align="L", fill=(ri==0), max_line_height=4.2, new_x="RIGHT", new_y="TOP")
        pdf.set_y(y0 + h)
    pdf.ln(2)

i = 0
while i < len(md):
    l = md[i]
    if re.match(r"^\|.*\|", l):
        rows=[]
        while i < len(md) and re.match(r"^\|.*\|", md[i]): rows.append(md[i]); i+=1
        table(rows); continue
    m = re.match(r"^!\[.*?\]\((.+?)\)", l)
    if m:
        p = (ROOT/"report"/m.group(1)).resolve()
        if p.exists():
            from PIL import Image
            iw, ih = Image.open(p).size
            w = min(CW, 150); h = w*ih/iw
            if pdf.get_y()+h > pdf.page_break_trigger: pdf.add_page()
            pdf.image(str(p), x=(215.9-w)/2, w=w); pdf.ln(2)
        i+=1; continue
    if l.startswith("# "):
        pdf.set_font("Helvetica","B",16); pdf.multi_cell(0,7,txt(l[2:]),align="C",new_x="LMARGIN",new_y="NEXT"); pdf.ln(2); i+=1; continue
    if l.startswith("## "):
        pdf.ln(1); para(l[3:], size=12, style="B", gap=1); i+=1; continue
    if l.startswith("### "):
        para(l[4:], size=10, style="B", gap=0.6); i+=1; continue
    if l.startswith("> "):
        para(l[2:], size=9, fill=True, gap=0.4); i+=1; continue
    if l.startswith("- "):
        pdf.set_font("Helvetica","",10); pdf.multi_cell(0,5,txt("  -  "+l[2:]),markdown=True,new_x="LMARGIN",new_y="NEXT"); pdf.ln(0.6); i+=1; continue
    if re.fullmatch(r"\s*", l) or l.strip()=="---": i+=1; continue
    if l.startswith("*") and l.endswith("*") and not l.startswith("**"):
        para(l.strip("*"), size=9, style="I", align="C", gap=1); i+=1; continue
    para(l); i+=1

out = ROOT/"report/final/Whispering-Through-the-Package-Cache.pdf"
pdf.output(str(out))
print("wrote", out, "pages:", pdf.page_no())
