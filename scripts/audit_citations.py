# -*- coding: utf-8 -*-
"""Audit every citation in main.tex: what claim does it support, and what is it?

Prints the ~190 characters preceding each \\cite so the claim is visible next to the
entry it points at. Reviewing this by eye is the point -- a citation can be perfectly
well-formed and still support nothing.
"""
import re
from pathlib import Path

D = Path(r"C:\Users\csdee\PESU\capstone\An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection\paper")
tex = (D / "main.tex").read_text(encoding="utf-8")
bib = (D / "source.bib").read_text(encoding="utf-8")

ent = {}
for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", bib, re.S):
    key, body = m.group(1).strip(), m.group(2)
    t = re.search(r"title\s*=\s*\{(.+?)\},?\s*\n", body, re.S)
    j = re.search(r"(?:journal|booktitle)\s*=\s*\{(.+?)\}", body)
    y = re.search(r"year\s*=\s*\{(\d+)\}", body)
    title = re.sub(r"\s+", " ", re.sub(r"[{}]", "", t.group(1))).strip() if t else "?"
    ent[key] = (title, j.group(1) if j else "?", y.group(1) if y else "?")

body = tex[tex.index("section{Introduction}"):]
seen = {}
n = 0
for m in re.finditer(r"\\cite\{([^}]+)\}", body):
    n += 1
    ctx = re.sub(r"\s+", " ", body[max(0, m.start() - 320):m.start()]).strip()[-200:]
    print(f"[{n}] CLAIM: ...{ctx}")
    for k in [x.strip() for x in m.group(1).split(",")]:
        seen[k] = seen.get(k, 0) + 1
        title, jrn, yr = ent.get(k, ("*** NOT IN BIB ***", "", ""))
        print(f"      -> {k}  ({jrn}, {yr})")
        print(f"         {title[:104]}")
    print()

print("=" * 70)
print(f"{n} citation commands, {len(seen)} distinct keys")
missing = [k for k in seen if k not in ent]
print("keys not in bib:", missing or "none")
