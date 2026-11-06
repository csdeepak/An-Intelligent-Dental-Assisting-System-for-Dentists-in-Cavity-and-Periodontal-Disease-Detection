"""One-off layout fixes for the overfull boxes of the first full build (6 Nov 2026). Idempotent."""
import re
from pathlib import Path


def edit(path, pairs):
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    for a, b in pairs:
        if b in t and a not in t:
            continue                       # already applied
        assert t.count(a) == 1, (path, a[:60])
        t = t.replace(a, b)
    p.write_text(t, encoding="utf-8", newline="\n")


def paths_to_urls(path, start_marker, end_marker):
    """Inside one table, turn \\texttt{a/b\\_c.py} cells that hold file paths into breakable \\nolinkurl."""
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    i = t.index(start_marker)
    j = t.index(end_marker, i)
    block = t[i:j]
    new = re.sub(r"\\texttt\{([A-Za-z0-9_./\\<>*-]*?(?:/|\.py|\.pt|\.pth)[A-Za-z0-9_./\\<>*-]*)\}",
                 lambda m: r"\nolinkurl{" + m.group(1).replace(r"\_", "_").replace(r"\dots", "...") + "}",
                 block)
    p.write_text(t[:i] + new + t[j:], encoding="utf-8", newline="\n")


edit("frontmatter/certificate.tex", [(r"\begin{tabular}{@{}C{5.4cm}C{5.4cm}C{5.4cm}@{}}",
                                      r"\begin{tabular}{@{}C{5.3cm}C{5.3cm}C{5.3cm}@{}}")])
edit("chapters/ch03_literature.tex", [
    (r"\subsection{AI-Driven Approaches for Enhancing Early Detection of Dental Caries~\cite{sastika2025ai}}",
     r"\subsection[AI-Driven Approaches for Enhancing Early Detection of Dental Caries]{AI-Driven Approaches for Enhancing Early Detection of\\ Dental Caries~\cite{sastika2025ai}}"),
    (r"\begin{tabular}{@{}L{4.2cm}C{1.35cm}C{1.35cm}C{1.2cm}C{1.5cm}C{1.5cm}C{1.65cm}@{}}",
     r"\begin{tabular}{@{}L{3.9cm}C{1.35cm}C{1.35cm}C{1.2cm}C{1.85cm}C{1.5cm}C{1.65cm}@{}}"),
])
edit("chapters/ch08_methodology.tex", [(r"\begin{tabularx}{\textwidth}{@{}L{2.3cm}L{3.4cm}YL{2.9cm}@{}}",
                                        r"\begin{tabularx}{\textwidth}{@{}L{2.7cm}L{3.3cm}YL{2.8cm}@{}}")])
edit("chapters/ch10_results.tex", [
    ("Tooth type & Crops & Carious & Base rate & Mean score, healthy & Healthy flagged & Within-type AUC\\\\",
     "Tooth type & Crops & Carious & \\makecell{Base\\\\rate} & \\makecell{Mean score,\\\\healthy} & "
     "\\makecell{Healthy\\\\flagged} & \\makecell{Within-type\\\\AUC}\\\\"),
])
edit("diagrams/pipeline_p2style.tex", [(r"\node[soft=p2teal,text width=30mm,left=4mm of c2,font=\sffamily\tiny]",
                                        r"\node[soft=p2teal,text width=21mm,left=3mm of c2,font=\sffamily\tiny]")])
paths_to_urls("chapters/ch06_lld.tex", r"\label{tab:modules}", r"\end{tabularx}")
paths_to_urls("chapters/ch06_lld.tex", r"\label{tab:registry}", r"\end{tabularx}")
print("layout fixes applied")
