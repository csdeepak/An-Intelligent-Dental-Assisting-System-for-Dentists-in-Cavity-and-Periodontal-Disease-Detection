"""Faithful conversion of paper/paper.md to IEEEtran LaTeX + references.bib (run from the repo root).
No content is added: text, numbers and markers are carried verbatim; only markup is translated.
Bibliography entries come from .rcs/corpus/source_registry.json for "(Author et al., Year)"
citations and from paper/source.bib for "[@key]" citations; since 2 Nov 2026 the draft cites
everything by key, so paper/source.bib is its single bibliography source."""
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

# 28 Oct 2026: a source outside the RCE registry is cited by key, `[@key]` or `[@a,b]`, and its
# entry is copied verbatim from the maintained manuscript's bibliography (paper/source.bib,
# Crossref-checked), never written by hand here.
SRC_BIB = Path("paper/source.bib").read_text(encoding="utf-8")
KEY_RE = re.compile(r"\s*\[@([\w,]+)\]")
bib_extra = {}

INTERNAL_NOTE = re.compile(r"verif|Corrected|Distinct from|No DOI|confirm|caution", re.I)

def drop_internal_notes(entry):
    """source.bib keeps curation notes in `note` ("No DOI found -- checked Crossref ...") that
    IEEEtran.bst prints in the reference list. Drop those; keep notes that are citation data."""
    out, pos = [], 0
    for m in re.finditer(r"^\s*note\s*=\s*\{", entry, re.M):
        if m.start() < pos: continue
        depth, j = 1, m.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(entry[j], 0); j += 1
        if INTERNAL_NOTE.search(entry[m.end():j - 1]):
            out.append(entry[pos:m.start()])
            pos = j + (1 if entry[j:j + 1] == "," else 0)
    return "".join(out) + entry[pos:]

def keycite(m):
    keys = m.group(1).split(",")
    for k in keys:
        e = re.search(r"^@\w+\{" + re.escape(k) + r",.*?^\}", SRC_BIB, re.S | re.M)
        if not e: raise SystemExit(f"[@{k}] is not in paper/source.bib")
        bib_extra[k] = drop_internal_notes(e.group(0)) + "\n"
    return r"~\cite{" + ",".join(keys) + "}"

def esc(t):
    t = t.replace("\\", r"\textbackslash{}")
    for a, b in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("$", r"\$"), ("{", r"\{"), ("}", r"\}")):
        t = t.replace(a, b)
    t = t.replace("~", r"\textasciitilde{}")
    return t

def inline(t):
    # 28 Oct 2026: `$...$` is LaTeX math, carried through untouched; only the text between the
    # math spans is escaped and marked up.
    parts = re.split(r"(\$[^$]+?\$)", t)
    return "".join(p if p.startswith("$") and p.endswith("$") and len(p) > 1 else inline_text(p)
                    for p in parts)

def inline_text(t):
    t = esc(t)
    t = CITE_RE.sub(cite, t)
    t = KEY_RE.sub(keycite, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", t)
    t = re.sub(r"(?<![\w*])\*(.+?)\*(?!\w)", r"\\emph{\1}", t)
    t = re.sub(r"\bFigure (\d+)([a-f])\b", r"Fig.~\\ref{fig:\1}(\2)", t)
    t = re.sub(r"\bFigures (\d+) and (\d+)\b", r"Figs.~\\ref{fig:\1} and~\\ref{fig:\2}", t)
    t = re.sub(r"\bFigure (\d+)\b", r"Fig.~\\ref{fig:\1}", t)
    t = re.sub(r"\bTable (\d+)\b", r"Table~\\ref{tab:\1}", t)
    t = t.replace('"none"', "``none''").replace(' -', ' $-$').replace('[-', '[$-$').replace('(-', '($-$')
    t = re.sub(r"(?<![\w$])-(?=\d)", r"$-$", t)   # a minus opening a table cell
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
    # 28 Oct 2026: raster/PDF figures. `![Figure N*](path)` spans both columns; without the star
    # it is one column wide. The path is relative to paper/ieee/.
    # `![Figure N*0.9](...)`: an optional scale after the star sets the width as a fraction.
    m = re.match(r"^!\[Figure (\d+)(\*?)(0\.\d+)?\]\(((?:figures/|\.\./).+?\.(?:pdf|png))\)$", ln)
    if m: pending_fig = (m.group(1), m.group(4), (m.group(2) == "*", m.group(3) or "")); i += 1; continue
    # Display math: a `$$` line opens and closes a numbered equation, carried verbatim.
    if ln.strip() == "$$":
        i += 1; eq = []
        while lines[i].strip() != "$$":
            eq.append(lines[i]); i += 1
        body.append("\\begin{equation}\n" + "\n".join(eq) + "\n\\end{equation}")
        i += 1; continue
    m = re.match(r"^\*\*Figure (\d+)\.\*\* (.+)$", ln)
    if m and pending_fig and len(pending_fig) == 3:
        n, path, (wide, scale) = pending_fig
        env, width = ("figure*", scale + r"\textwidth") if wide else ("figure", scale + r"\columnwidth")
        body.append(f"\\begin{{{env}}}[t]\n\\centering\n\\includegraphics[width={width}]{{{path}}}\n"
                    "\\caption{" + inline(m.group(2)) + "}\n\\label{fig:" + n + f"}}\n\\end{{{env}}}")
        pending_fig = None; i += 1; continue
    if ln.startswith("```"):
        i += 1; code = []
        while not lines[i].startswith("```"):
            code.append(lines[i]); i += 1
        # A minipage keeps the listing in one column instead of splitting it across two.
        body.append("\\par\\noindent\\begin{minipage}{\\columnwidth}\\footnotesize\n\\begin{verbatim}\n"
                    + "\n".join(code) + "\n\\end{verbatim}\n\\end{minipage}\\par")
        i += 1; continue
    if m and pending_fig:
        n, stem = pending_fig; w, h = FIG_H[stem]
        trim = f"trim=0 {792 - 0.75 * h:.1f}bp {612 - 0.75 * w:.1f}bp 0, clip"
        cap = inline(m.group(2))
        body.append("\\begin{figure*}[t]\n\\centering\n\\includegraphics[" + trim + r",width=0.82\textwidth]{figures/" + stem + ".pdf}\n"
                    "\\caption{" + cap + "}\n\\label{fig:" + n + "}\n\\end{figure*}")
        pending_fig = None; i += 1; continue
    # 28 Oct 2026: `**Table N*.**` spans both columns; without the star a table is one column wide.
    m = re.match(r"^\*\*Table (\d+)(\*?)\.\*\* (.+)$", ln)
    if m:
        n, env, cap = m.group(1), ("table*" if m.group(2) else "table"), inline(m.group(3)); i += 1
        while not lines[i].startswith("|"): i += 1
        raw = []
        while i < len(lines) and lines[i].startswith("|"):
            if not re.match(r"^\|[-| ]+\|$", lines[i]): raw.append([c.strip() for c in lines[i].strip("|").split("|")])
            i += 1
        rows = [[inline(c) for c in r] for r in raw]
        ncol = len(rows[0])
        NUM = r"^(—|[-+]?[\d.,]+(?: ?[M%])?(?: \[[-+]?[\d.,]+, [-+]?[\d.,]+\])?)$"
        numeric = [all(re.match(NUM, r[c]) for r in raw[1:] if r[c]) for c in range(ncol)]
        # Numeric columns take their natural width, estimated from their longest cell at
        # \footnotesize; text columns share what is left of the column (8.4 cm) or page (17.4 cm).
        numw = sum(0.14 * max(len(r[c]) for r in raw) + 0.05 for c in range(ncol) if numeric[c])
        # Text columns share the rest in proportion to their longest cell, so a short "Verdict"
        # column does not take the width a long "Evidence" column needs.
        txt = [c for c in range(ncol) if not numeric[c]]
        free = (17.4 if env == "table*" else 8.4) - numw - 0.22 * ncol
        need = {c: max(len(r[c]) for r in raw) ** 0.75 for c in txt}
        widths = {c: max(1.65, free * need[c] / sum(need.values())) for c in txt}
        spec = "".join("r" if numeric[c] else (r">{\raggedright\arraybackslash}p{" + f"{widths[c]:.2f}cm" + "}") for c in range(ncol))
        tb = [f"\\begin{{{env}}}[t]", r"\centering", r"\caption{" + cap + "}", r"\label{tab:" + n + "}", r"\footnotesize",
              r"\setlength{\tabcolsep}{3pt}",
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
\renewcommand{\topfraction}{0.9}
\renewcommand{\dbltopfraction}{0.9}
\renewcommand{\textfraction}{0.07}
\renewcommand{\floatpagefraction}{0.85}
\renewcommand{\dblfloatpagefraction}{0.85}
\setcounter{dbltopnumber}{2}
\begin{document}
\bstctlcite{IEEEexample:BSTcontrol}
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
bib = "".join(bibentry(s) for s in REG if s["cite_key"] in cited) + "".join(bib_extra[k] for k in sorted(bib_extra))
# 28 Oct 2026: the reference list prints no URLs (they cost the ten-page draft a third of a
# page); every entry keeps its venue, volume and pages, and paper/source.bib keeps the links.
bib = re.sub(r"^\s*url\s*=\s*\{[^\n]*\},?\n", "", bib, flags=re.M)
# 2 Nov 2026: IEEE reference style abbreviates journal and proceedings names (ISO 4 / IEEE
# reference guide); paper/source.bib keeps the full names.
ABBR = {
    "IEEE Journal of Biomedical and Health Informatics": "IEEE J. Biomed. Health Inform.",
    "Proceedings of the AAAI Conference on Artificial Intelligence": "Proc. AAAI Conf. Artif. Intell.",
    "Journal of Imaging Informatics in Medicine": "J. Imaging Inform. Med.",
    "Journal of the Royal Statistical Society Series B: Statistical Methodology": "J. R. Stat. Soc. B",
    "2017 IEEE Conference on Computer Vision and Pattern Recognition (CVPR)": "Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)",
    "2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition": "Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)",
    "IEEE Conference on Computer Vision and Pattern Recognition (CVPR)": "Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)",
    "Proceedings of the 34th International Conference on Machine Learning (ICML)": "Proc. 34th Int. Conf. Mach. Learn. (ICML)",
    "Proceedings of the 8th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining": "Proc. 8th ACM SIGKDD Int. Conf. Knowl. Discov. Data Min.",
    "Proceedings of the Seventh Joint Conference on Lexical and Computational Semantics": "Proc. 7th Joint Conf. Lexical Comput. Semantics",
    "Advances in Neural Information Processing Systems": "Adv. Neural Inf. Process. Syst.",
    "Naval Research Logistics Quarterly": "Naval Res. Logist. Q.",
    "Nature Machine Intelligence": "Nat. Mach. Intell.",
    "Radiology: Artificial Intelligence": "Radiol. Artif. Intell.",
    "Statistics in Medicine": "Stat. Med.",
    "Controlled Clinical Trials": "Control. Clin. Trials",
    "Korean Journal of Radiology": "Korean J. Radiol.",
    "Journal of Prosthetic Dentistry": "J. Prosthet. Dent.",
    "Informatica Medica Slovenica": "Inform. Med. Slov.",
    "Nature Communications": "Nat. Commun.",
    "Scientific Reports": "Sci. Rep.",
    "Journal of Dentistry": "J. Dent.",
    "PLOS Medicine": "PLoS Med.",
    "PLOS Digital Health": "PLOS Digit. Health",
    "BMC Oral Health": "BMC Oral Health",
    "Expert Systems with Applications": "Expert Syst. Appl.",
}
for full, short in ABBR.items():
    bib = re.sub(r"((?:journal|booktitle)\s*=\s*\{)" + re.escape(full) + r"\}", lambda m: m.group(1) + short + "}", bib)
bib = re.sub(r"^\s*(?:series|publisher)\s*=\s*\{[^\n]*\},?\n", "", bib, flags=re.M)
bib = re.sub(r",?\n\s*note\s*=\s*\{Introduces the UFBA-425 dataset\}", "", bib)
# 2 Nov 2026: IEEE reference style lists at most six authors, then "et al." (IEEEtran.bst
# control entry, activated by \bstctlcite in the preamble).
bib = ('@IEEEtranBSTCTL{IEEEexample:BSTcontrol,\n  CTLuse_forced_etal = "yes",\n'
       '  CTLmax_names_forced_etal = "6",\n  CTLnames_show_etal = "1"\n}\n\n') + bib
(OUT / "references.bib").write_text(bib, encoding="utf-8")
unused = [s["cite_key"] for s in REG if s["cite_key"] not in cited]
print("cited", len(cited), "unused registry entries (not written to bib):", unused)
