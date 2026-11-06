"""Report-level checks the RCE tools do not make: the college guidelines and the TeX build.

  abstract        at most 150 words (guideline 5) and at most two paragraphs (template)
  chapters        the required chapters, in the guideline's order
  acknowledgement the guideline's order of names
  floats          every figure, table, algorithm and listing is referred to in the text
  citations       every \\cite key is in references.bib
  claim tags      every {C###}/{L###} tag in the TeX is in the claim map, and every claim is tagged
  build log       no errors, undefined references or overfull boxes

    python -I tools/check_report.py      (after tools/build.sh); exit 1 on any FAIL
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
B = "\\"
results = []


def check(name, ok, detail):
    results.append((name, ok, detail))


def read(rel):
    return (HERE / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


main = read("main.tex")
files = ["frontmatter/" + f + ".tex" for f in ("cover", "certificate", "declaration", "acknowledgement", "abstract")]
files += [m + ".tex" for m in re.findall(r"\\input\{((?:chapters|appendices)/[^}]+)\}", main)]
tex = {f: read(f) for f in files}
body = "\n".join(tex[f] for f in files if not f.startswith("frontmatter/") or f.endswith("abstract.tex"))

# ---- abstract
a = re.search(r"% RCE-ABSTRACT-BEGIN\n(.*?)% RCE-ABSTRACT-END", tex["frontmatter/abstract.tex"], re.S).group(1)
a = re.sub(r"(?<!\\)%[^\n]*", "", a)
paras = [p for p in re.split(r"\n\s*\n", a) if p.strip()]
words = len(re.sub(r"\\[a-zA-Z]+|[{}]", " ", a).replace("\\%", "%").split())
check("abstract", words <= 150 and len(paras) <= 2, f"{words} words, {len(paras)} paragraphs (limits 150, 2)")

# ---- chapters, in the guideline's order
want = ["introduction", "problem statement", "literature", "requirements", "high-level design", "low-level design",
        "system design", "methodology", "implementation", "results", "conclusion"]
got = [re.search(r"\\chapter\{([^}]+)\}", tex[f]).group(1).lower() for f in files if f.startswith("chapters/")]
order_ok = len(got) == len(want) and all(w in g for w, g in zip(want, got))
apps = [re.search(r"\\chapter\{([^}]+)\}", tex[f]).group(1) for f in files if f.startswith("appendices/")]
refs_before_apps = main.index("\\bibliography{") < main.index("\\appendix")
check("chapters", order_ok and refs_before_apps and len(apps) == 2,
      f"{len(got)} chapters in order; references before {len(apps)} appendices: " + "; ".join(apps))

# ---- acknowledgement order
ack = re.sub(r"(?<!\\)%[^\n]*", "", tex["frontmatter/acknowledgement.tex"])
names = ["Mamatha", "Chaitra", "Shylaja", "Sridhar", "Suryaprasad", "Jawahar", "parents"]
pos = [ack.find(n) for n in names]
ack_paras = [p for p in re.split(r"\n\s*\n", ack) if any(n in p for n in names)]
one_each = all(sum(n in p for n in names) == 1 for p in ack_paras)
check("acknowledgement", all(p >= 0 for p in pos) and pos == sorted(pos) and one_each,
      "guideline order (guide, coordinator, chairperson, registrar, Vice-Chancellor, Chancellor, parents, family), "
      "one paragraph each")
results.append(("acknowledgement CEO", None, "the guideline puts the CEO between the Vice-Chancellor and the Chancellor; "
                "the name is not in the college template: author to supply"))

# ---- floats referenced (a range \ref{a}--\ref{b} covers the floats numbered between)
aux = (HERE / "build" / "main.aux").read_text(encoding="utf-8", errors="replace")
num = {m.group(1): m.group(2) for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux)}
labels = re.findall(r"\\label\{((?:fig|tab|alg|lst):[^}]+)\}", body)
lst = re.findall(r"label=((?:lst):[^,\]]+)", body)
labels += lst
refd = set(re.findall(r"\\(?:ref|eqref|autoref)\{([^}]+)\}", body))


def key(n):
    return tuple(int(x) for x in re.findall(r"\d+", n))


for a_, b_ in re.findall(r"\\ref\{([^}]+)\}\s*(?:--|-|to)\s*\\ref\{([^}]+)\}", body):
    if a_ in num and b_ in num and a_.split(":")[0] == b_.split(":")[0]:
        lo, hi = key(num[a_]), key(num[b_])
        refd |= {l for l in labels if l.split(":")[0] == a_.split(":")[0] and l in num and lo <= key(num[l]) <= hi}
subfig = {l for l in labels if l in num and re.search(r"[a-z]\)?$", num[l])}      # subfigure labels
missing = [l for l in labels if l not in refd and l not in subfig]
check("floats", not missing, f"{len(labels)} labelled floats; not referred to: {', '.join(missing) or 'none'}")

# ---- citations
bib = (HERE / "build" / "references.bib").read_text(encoding="utf-8", errors="replace")
bibkeys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib))
cites = set()
for grp in re.findall(r"\\cite\{([^}]+)\}", body):
    cites |= {k.strip() for k in grp.split(",")}
check("citations", cites <= bibkeys, f"{len(cites)} keys cited; not in references.bib: {sorted(cites - bibkeys) or 'none'}")

# ---- claim tags
cm = json.loads((HERE / ".rcs" / "claims" / "claim_evidence_map.json").read_text(encoding="utf-8"))
ids = {c["id"] for c in cm["claims"]} | {l["id"] for l in cm["limitations"]}
tags = set(re.findall(r"\{([CL]\d{3,})\}", "\n".join(l for l in body.split("\n") if "%" in l)))
check("claim tags", tags <= ids and ids <= tags,
      f"{len(tags)} tags in the TeX, {len(ids)} entries in the claim map; unknown: {sorted(tags - ids) or 'none'}; "
      f"untagged: {sorted(ids - tags) or 'none'}")

# ---- build log
log = (HERE / "build" / "main.log").read_text(encoding="utf-8", errors="replace")
errs = len(re.findall(r"^! ", log, re.M))
undef = len(re.findall(r"undefined", log, re.I)) - len(re.findall(r"Package rerunfilecheck", log))
over = len(re.findall(r"^Overfull", log, re.M))
pages = re.search(r"Output written on .*?\((\d+) pages", log, re.S)
check("build log", errs == 0 and over == 0 and not re.search(r"(Reference|Citation).*undefined", log),
      f"{pages.group(1) if pages else '?'} pages; {errs} errors; {over} overfull boxes; "
      f"undefined references: {len(re.findall(r'(Reference|Citation).*undefined', log))}")

w = max(len(n) for n, _, _ in results)
for n, ok, d in results:
    print(f"{'OPEN' if ok is None else 'PASS' if ok else 'FAIL'}  {n:<{w}}  {d}")
sys.exit(0 if all(ok is not False for _, ok, _ in results) else 1)
