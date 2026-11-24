#!/usr/bin/env bash
# Rebuild research_paper/.rcs in the right order and keep the live citation verification.
# Run from the repo root. Re-verify any new source afterwards with verify_citations.py --online --only SRC-xxx.
set -e
P=C:/venvs/dental312/Scripts/python.exe
$P research_paper/tools/build_rcs.py
$P research_paper/tools/build_registry.py
$P - <<'PYEOF'
import json
reg = "research_paper/.rcs/corpus/source_registry.json"
new = json.load(open(reg, encoding="utf-8"))
old = {s["cite_key"]: s for s in json.load(open("research_paper/audit_runs/source_registry_verified_2026-11-23.json", encoding="utf-8"))["sources"]}
miss = []
for s in new["sources"]:
    if s["cite_key"] in old: s["verification"] = old[s["cite_key"]]["verification"]
    else: miss.append(s["id"])
json.dump(new, open(reg, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("live verification carried over; not yet verified:", miss)
PYEOF
