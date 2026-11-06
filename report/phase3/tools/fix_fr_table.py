"""One-off: turn the functional-requirements longtable in ch04 into a tabularx table (it fits one page)."""
from pathlib import Path

p = Path("chapters/ch04_prs.tex")
t = p.read_text(encoding="utf-8")
start = t.index(r"\begin{longtable}")
end = t.index(r"\end{longtable}") + len(r"\end{longtable}")
lt = t[start:end]
rows = lt[lt.index(r"\endfoot") + len(r"\endfoot"):lt.index(r"\end{longtable}")].strip()
new = "\n".join([
    r"\begin{table}[!htbp]",
    r"\centering",
    r"\caption[Functional requirements]{Functional requirements and where each is implemented.}",
    r"\label{tab:fr}",
    r"\small",
    r"\begin{tabularx}{\textwidth}{@{}L{1.4cm}YL{4.0cm}@{}}",
    r"\toprule",
    r"ID & Requirement & Implemented in\\",
    r"\midrule",
    rows,
    r"\bottomrule",
    r"\end{tabularx}",
    r"\end{table}",
])
p.write_text(t[:start] + new + t[end:], encoding="utf-8", newline="\n")
print("converted")
