"""Build a citation-free copy of the paper for a similarity (plagiarism) check, e.g. Turnitin.
Run from the repo root after build_paper.py. Writes research_paper/turnitin/ only; the real paper is untouched.

Removes every in-text citation marker ([@key] -> nothing) and the reference list; text, numbers,
tables and figures are otherwise identical to research_paper/paper_clean.md.
"""
import re, subprocess, sys
from pathlib import Path

R = Path("research_paper"); T = R / "turnitin"; T.mkdir(exist_ok=True)
md = (R / "paper_clean.md").read_text(encoding="utf-8")
md = re.sub(r"\s*\[@[\w,]+\]", "", md)
md = re.sub(r"\n## References\s*$", "\n", md.rstrip() + "\n")
assert "[@" not in md
(T / "paper_no_citations.md").write_text(md, encoding="utf-8")

src = (R / "tools/md_to_ieee_rp.py").read_text(encoding="utf-8")
src = src.replace('Path("research_paper/paper_clean.md")', 'Path("research_paper/turnitin/paper_no_citations.md")')
src = src.replace('OUT = Path("research_paper")', 'OUT = Path("research_paper/turnitin")')
src = src.replace('(OUT / "paper.tex")', '(OUT / "paper_no_citations.tex")')
src = src.replace('(OUT / "references.bib")', '(OUT / "_unused.bib")')
exec(compile(src, "md_to_ieee_rp(no-citations)", "exec"), {"__name__": "__main__"})

tex_p = T / "paper_no_citations.tex"
tex = tex_p.read_text(encoding="utf-8")
tex = tex.replace("\\bstctlcite{IEEEexample:BSTcontrol}\n", "")
tex = tex.replace("\\bibliographystyle{IEEEtran}\n\\bibliography{references}\n", "")
tex = tex.replace("\\usepackage{graphicx}", "\\usepackage{graphicx}\n\\graphicspath{{../}}")
assert "\\cite" not in tex and "\\bibliography" not in tex
tex_p.write_text(tex, encoding="utf-8")
(T / "_unused.bib").unlink(missing_ok=True)
(T / "IEEEtran.cls").write_bytes((R / "IEEEtran.cls").read_bytes())
for _ in range(2):
    p = subprocess.run(["pdflatex", "-interaction=nonstopmode", "paper_no_citations.tex"], cwd=T, capture_output=True, text=True, encoding="utf-8", errors="replace")
log = (T / "paper_no_citations.log").read_text(encoding="utf-8", errors="replace")
pages = re.search(r"Output written on paper_no_citations.pdf \((\d+) pages", log)
print("pages:", pages.group(1) if pages else "?", "| errors:", len(re.findall(r"^! ", log, re.M)),
      "| undefined:", len(re.findall(r"undefined", log)))
for f in T.glob("paper_no_citations.*"):
    if f.suffix in (".aux", ".log", ".out"): f.unlink()
