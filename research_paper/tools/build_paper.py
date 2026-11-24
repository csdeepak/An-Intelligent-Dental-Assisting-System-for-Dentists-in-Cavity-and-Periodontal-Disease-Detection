"""Build research_paper/final_research_paper.pdf from research_paper/paper.md (run from the repo root).
1. strip RCE claim/limitation tags -> research_paper/paper_clean.md (markers such as [ASK AUTHOR] stay)
2. md_to_ieee_rp.py -> research_paper/paper.tex + references.bib
3. pdflatex, bibtex, pdflatex x2 in research_paper/ -> paper.pdf, copied to final_research_paper.pdf
"""
import re, shutil, subprocess, sys
from pathlib import Path
R = Path("research_paper")
md = (R / "paper.md").read_text(encoding="utf-8")
clean = re.sub(r"(\s*\{[CL]\d{3,}\})+", "", md)
(R / "paper_clean.md").write_text(clean, encoding="utf-8")
subprocess.run([sys.executable, str(R / "tools/md_to_ieee_rp.py")], check=True)
def run(cmd):
    p = subprocess.run(cmd, cwd=R, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout
for cmd in (["pdflatex", "-interaction=nonstopmode", "paper.tex"], ["bibtex", "paper"],
            ["pdflatex", "-interaction=nonstopmode", "paper.tex"], ["pdflatex", "-interaction=nonstopmode", "paper.tex"]):
    rc, out = run(cmd)
    print(" ".join(cmd), "->", rc)
log = (R / "paper.log").read_text(encoding="utf-8", errors="replace")
pages = re.search(r"Output written on paper.pdf \((\d+) pages", log)
print("pages:", pages.group(1) if pages else "?")
print("errors:", len(re.findall(r"^! ", log, re.M)), "| undefined refs/cites:", len(re.findall(r"undefined", log)),
      "| overfull hbox:", len(re.findall(r"Overfull \\hbox", log)))
blg = (R / "paper.blg").read_text(encoding="utf-8", errors="replace")
print("bibtex warnings:", len(re.findall(r"^Warning", blg, re.M)))
if pages: shutil.copy(R / "paper.pdf", R / "final_research_paper.pdf")
