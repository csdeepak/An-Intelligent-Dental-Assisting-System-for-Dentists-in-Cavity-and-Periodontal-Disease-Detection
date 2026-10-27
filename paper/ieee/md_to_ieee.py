"""Faithful conversion of paper/paper.md to IEEEtran LaTeX + references.bib (run from the repo root).
No content is added: text, numbers and markers are carried verbatim; only markup is translated.
Bibliography entries are generated ONLY from .rcs/corpus/source_registry.json."""
import json, re, subprocess
from pathlib import Path

MD = Path("paper/paper.md").read_text(encoding="utf-8")
OUT = Path("paper/ieee")
REG = json.load(open(".rcs/corpus/source_registry.json", encoding="utf-8"))["sources"]

# ---------------- bibliography
def surname_match(src, name):
    return any(name.lower() in a.lower() for a in src["authors"][:1])

def bibentry(s):
    k = s["cite_key"]
    au = " and ".join(s["authors"]).replace("Cerda Mardini", "{Cerda Mardini}")
    f = {"title": "{" + s["title"] + "}", "author": au, "year": str(s["year"])}
    if s.get("doi"): f["doi"] = s["doi"]
    if s.get("url"): f["url"] = s["url"]
    v = s.get("venue") or ""
    if s["publication_status"] == "DOCUMENTATION":
        typ = "misc"; f["howpublished"] = "Software, " + (s.get("url") or "")
    elif s["publication_status"] == "PREPRINT":
        typ = "misc"; f["howpublished"] = "arXiv preprint"
    elif re.search(r"Proceedings|Conference|CVPR|KDD", v):
        typ = "inproceedings"; f["booktitle"] = v
    else:
        typ = "article"; f["journal"] = v
    esc = lambda x: x.replace("&", r"\&").replace("_", r"\_")
    body = ",\n".join(f"  {a} = {{{esc(b) if a not in ('url','doi') else b}}}" for a, b in f.items())
    return f"@{typ}{{{k},\n{body}\n}}\n"

cited = set()

def cite(m):
    parts = [p.strip() for p in m.group(1).split(";")]
    keys = []
    for p in parts:
        mm = re.match(r"(.+?)(?: et al\.)?, (\d{4})$", p)
        if not mm: return m.group(0)
        name, yr = mm.group(1).split()[-1], int(mm.group(2))
        cand = [s for s in REG if s["year"] == yr and surname_match(s, name)]
        if len(cand) != 1: raise SystemExit(f"citation {p!r} resolves to {len(cand)} sources")
        keys.append(cand[0]["cite_key"]); cited.add(cand[0]["cite_key"])
    return r"~\cite{" + ",".join(keys) + "}"

CITE_RE = re.compile(r"\s*\(((?:[A-Z][A-Za-z\- ]+?(?: et al\.)?, \d{4})(?:; [A-Z][A-Za-z\- ]+?(?: et al\.)?, \d{4})*)\)")

def esc(t):
    t = t.replace("\\", r"\textbackslash{}")
    for a, b in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("$", r"\$"), ("{", r"\{"), ("}", r"\}")):
        t = t.replace(a, b)
    t = t.replace("~", r"\textasciitilde{}")
    return t

def inline(t):
    t = esc(t)
    t = CITE_RE.sub(cite, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", t)
    t = re.sub(r"(?<![\w*])\*(.+?)\*(?!\w)", r"\\emph{\1}", t)
    t = re.sub(r"\bFigure (\d)\b", r"Fig.~\\ref{fig:\1}", t)
    t = re.sub(r"\bTable (\d)\b", r"Table~\\ref{tab:\1}", t)
    t = t.replace('"none"', "``none''").replace(' -', ' $-$').replace('[-', '[$-$').replace('(-', '($-$')
    t = t.replace(">= ", r"$\geq$ ")
    return t

FIG_H = {}
for p in Path(".rcs/plan/figures").glob("*.svg"):
    s = p.read_text(encoding="utf-8")
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', s) or re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s)
    FIG_H[p.stem] = (float(m.group(1)), float(m.group(2)))

lines = MD.splitlines()
title = lines[0].lstrip("# ").strip()
body, i = [], 1
abstract = keywords = ""
pending_fig = None
while i < len(lines):
    ln = lines[i]
    if ln.startswith("## Abstract"):
        i += 2; abstract = inline(lines[i]); i += 1; continue
    if ln.startswith("**Index Terms**"):
        keywords = inline(ln.split(":", 1)[1].strip()); i += 1; continue
    if ln.startswith("## References"):
        break
    if ln.startswith("## Acknowledgment"):
        body.append(r"\section*{Acknowledgment}"); i += 1; continue
    m = re.match(r"^## ([IVX]+)\. (.+)$", ln)
    if m: body.append(r"\section{" + inline(m.group(2)) + "}"); i += 1; continue
    m = re.match(r"^### ([A-Z])\. (.+)$", ln)
    if m: body.append(r"\subsection{" + inline(m.group(2)) + "}"); i += 1; continue
    m = re.match(r"^!\[Figure (\d)\]\(figures_rce/(.+?)\.svg\)$", ln)
    if m: pending_fig = (m.group(1), m.group(2)); i += 1; continue
    m = re.match(r"^\*\*Figure (\d)\.\*\* (.+)$", ln)
    if m and pending_fig:
        n, stem = pending_fig; w, h = FIG_H[stem]
        trim = f"trim=0 {792 - 0.75 * h:.1f}bp {612 - 0.75 * w:.1f}bp 0, clip"
        cap = inline(m.group(2))
        body.append("\\begin{figure*}[t]\n\\centering\n\\includegraphics[" + trim + r",width=0.82\textwidth]{figures/" + stem + ".pdf}\n"
                    "\\caption{" + cap + "}\n\\label{fig:" + n + "}\n\\end{figure*}")
        pending_fig = None; i += 1; continue
    m = re.match(r"^\*\*Table (\d)\.\*\* (.+)$", ln)
    if m:
        n, cap = m.group(1), inline(m.group(2)); i += 1
        while not lines[i].startswith("|"): i += 1
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            if not re.match(r"^\|[-| ]+\|$", lines[i]): rows.append([inline(c.strip()) for c in lines[i].strip("|").split("|")])
            i += 1
        ncol = len(rows[0]); env = "table*" if ncol > 4 else "table"
        numeric = [all(re.match(r"^[\d$+\-\[(]", r[c].strip() or "0") for r in rows[1:] if r[c].strip()) for c in range(ncol)]
        width = {3: "2.05cm", 4: "1.6cm"}.get(ncol, "2.6cm")
        spec = "".join("r" if numeric[c] else (r">{\raggedright\arraybackslash}p{" + width + "}") for c in range(ncol))
        tb = [f"\\begin{{{env}}}[t]", r"\centering", r"\caption{" + cap + "}", r"\label{tab:" + n + "}", r"\footnotesize",
              r"\begin{tabular}{" + spec + "}", r"\toprule", " & ".join(rows[0]) + r" \\", r"\midrule"]
        tb += [" & ".join(r) + r" \\" for r in rows[1:]] + [r"\bottomrule", r"\end{tabular}", f"\\end{{{env}}}"]
        body.append("\n".join(tb)); continue
    if re.match(r"^- ", ln):
        items = []
        while i < len(lines) and lines[i].startswith("- "):
            items.append(r"\item " + inline(lines[i][2:])); i += 1
        body.append("\\begin{itemize}\n" + "\n".join(items) + "\n\\end{itemize}"); continue
    if re.match(r"^\d\. ", ln):
        items = []
        while i < len(lines) and re.match(r"^\d\. ", lines[i]):
            items.append(r"\item " + inline(lines[i][3:])); i += 1
        body.append("\\begin{enumerate}\n" + "\n".join(items) + "\n\\end{enumerate}"); continue
    if ln.strip() == "":
        i += 1; continue
    if ln.startswith("[ASK AUTHOR: author names"):
        i += 1; continue
    body.append(inline(ln)); i += 1

tex = r"""\documentclass[conference]{IEEEtran}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{array}
\usepackage{cite}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
\begin{document}
\title{""" + esc(title).replace(": ", ":\\\\ ", 1) + r"""}
\author{\IEEEauthorblockN{[ASK AUTHOR: author names]}
\IEEEauthorblockA{[ASK AUTHOR: affiliations and e-mail addresses]}}
\maketitle
\begin{abstract}
""" + abstract + r"""
\end{abstract}
\begin{IEEEkeywords}
""" + keywords + r"""
\end{IEEEkeywords}

""" + "\n\n".join(body) + r"""

\bibliographystyle{IEEEtran}
\bibliography{references}
\end{document}
"""
(OUT / "main.tex").write_text(tex, encoding="utf-8")
(OUT / "references.bib").write_text("".join(bibentry(s) for s in REG if s["cite_key"] in cited), encoding="utf-8")
unused = [s["cite_key"] for s in REG if s["cite_key"] not in cited]
print("cited", len(cited), "unused registry entries (not written to bib):", unused)
