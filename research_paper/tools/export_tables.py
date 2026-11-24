"""Export every table of research_paper/paper_clean.md to research_paper/tables/table_<N>.csv and .md (run from the repo root)."""
import csv, re
from pathlib import Path
md = Path("research_paper/paper_clean.md").read_text(encoding="utf-8").splitlines()
out = Path("research_paper/tables"); out.mkdir(exist_ok=True)
i, n = 0, 0
while i < len(md):
    m = re.match(r"^\*\*Table (\d+)\*?\.\*\* (.+)$", md[i])
    if m:
        num, cap = m.group(1), m.group(2); i += 1
        while not md[i].startswith("|"): i += 1
        rows = []
        while i < len(md) and md[i].startswith("|"):
            if not re.match(r"^\|[-| ]+\|$", md[i]): rows.append([c.strip() for c in md[i].strip("|").split("|")])
            i += 1
        with open(out / f"table_{num}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow([f"# Table {num}. {cap}"]); w.writerows(rows)
        lines = [f"**Table {num}.** {cap}", "", "| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])] + ["| " + " | ".join(r) + " |" for r in rows[1:]]
        (out / f"table_{num}.md").write_text("\n".join(lines) + "\n", encoding="utf-8"); n += 1
    else:
        i += 1
print("tables exported:", n)
