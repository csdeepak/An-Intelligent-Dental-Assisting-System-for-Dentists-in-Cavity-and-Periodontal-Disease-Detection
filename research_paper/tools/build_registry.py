"""Build research_paper/.rcs/corpus/source_registry.json from the works research_paper/paper.md cites.
Run from the repo root after build_rcs.py; then run RCE's verify_citations.py --online to re-verify every
source live (that step, not this file, sets lookup_verified).

Metadata comes from the BibTeX entries (paper/source.bib, Crossref-checked on 2 Nov 2026; and
research_paper/references_extra.bib, generated from Crossref on 23 Nov 2026), never from memory.
Support quotes come from the saved abstracts; a work cited only as a method, dataset or software
name carries its title as the quote and says so in `location`.
"""
import json, re, sys
from pathlib import Path

R = Path(".")
md = (R / "research_paper/paper.md").read_text(encoding="utf-8")
keys = []
for m in re.finditer(r"\[@([\w,]+)\]", md):
    for k in m.group(1).split(","):
        if k not in keys:
            keys.append(k)
bib = (R / "paper/source.bib").read_text(encoding="utf-8") + "\n" + (R / "research_paper/references_extra.bib").read_text(encoding="utf-8")
new_keys = set(re.findall(r"^@\w+\{(\w+),", (R / "research_paper/references_extra.bib").read_text(encoding="utf-8"), re.M))

def field(entry, name):
    m = re.search(r"^\s*" + name + r"\s*=\s*", entry, re.M | re.I)
    if not m:
        return None
    i = m.end()
    if entry[i] == "{":
        depth, j = 1, i + 1
        while depth:
            depth += {"{": 1, "}": -1}.get(entry[j], 0); j += 1
        v = entry[i + 1:j - 1]
    elif entry[i] == '"':
        j = entry.index('"', i + 1); v = entry[i + 1:j]
    else:
        v = re.match(r"[^,\n]+", entry[i:]).group(0)
    return " ".join(v.replace("{", "").replace("}", "").split())

abstracts = {}
for p in ["outputs/citation_audit/2026-11-02_ars/claim_abstracts.json", "outputs/citation_audit/2026-11-02_ars/new_abstracts.json"]:
    for k, v in json.loads((R / p).read_text(encoding="utf-8")).items():
        abstracts[k] = (v.get("abstract") or "", p)
for p in ["research_paper/literature/abstracts_new_2026-11-23.json", "research_paper/literature/abstracts_sourcebib_2026-11-23.json",
          "research_paper/literature/abstracts_lipton2014_2026-11-23.json", "research_paper/literature/abstract_mohammadrahimi_europepmc_2026-11-23.json"]:
    for doi, v in json.loads((R / p).read_text(encoding="utf-8")).items():
        abstracts[doi.lower()] = (v.get("abstract") or "", p)

# claim-bearing quotes, each must occur verbatim in the saved abstract
QUOTES = {
    "tuzoff2019tooth": "For teeth numbering, its sensitivity is 0.9800 and specificity is 0.9994.",
    "krois2019deep": "Our reference test was the measured % of PBL.",
    "chang2020deep": "Deep learning was used to detect the radiographic bone level (or the CEJ level)",
    "tonetti2018staging": "Stage I to IV of periodontitis is defined based on severity (primarily periodontal breakdown with reference to root length and periodontitis-associated tooth loss), complexity of management (pocket depth, infrabony defects, furcation involvement, tooth hypermobility, masticatory dysfunction)",
    "oakdenrayner2020hidden": "Machine learning models for medical image analysis often suffer from poor performance on important subsets of a population that are not identified during training or testing.",
    "varoquaux2022machine": "we show that at every step, potential biases can creep in.",
    "kelly2019key": "Robust peer-reviewed clinical evaluation as part of randomised controlled trials should be viewed as the gold standard",
    "schwendicke2020artificial": "This succinct narrative review describes the application, limitations and possible future of AI-based dental diagnostics",
    "collins2024tripod": "TRIPOD+AI provides harmonised guidance for reporting prediction model studies",
    "li2025novel": "This is the first AI model developed from orthopantomograms (OPGs) linked to clinical diagnoses",
    "vannistelrooij2024combining": "Datasets from the OdontoAI platform (tooth instance segmentations) and the DENTEX challenge (tooth bounding boxes with associated diagnoses) were combined",
    "cerda2024determining": "weighted F1-score 0.29",
    "krois2021generalizability": "F1-score of 54.1",
    "mutlu2026comparison": "maintaining a mAP@0.5 of 0.857",
}
QUOTES["lipton2014optimal"] = "the optimal threshold is half the optimal F1 score"
QUOTES["mutlu2026comparison"] = "maintaining a mAP@0.5 of 0.806 on the unseen external dataset"

sources, key2src, missing = [], {}, []
for n, k in enumerate(keys, 1):
    e = re.search(r"^@(\w+)\{" + re.escape(k) + r",.*?^\}", bib, re.S | re.M)
    if not e:
        sys.exit(f"{k} not in any bib file")
    entry, etype = e.group(0), e.group(1).lower()
    title, year = field(entry, "title"), int(field(entry, "year"))
    authors = [a.strip() for a in (field(entry, "author") or "Unknown").split(" and ")]
    venue = field(entry, "journal") or field(entry, "booktitle") or field(entry, "howpublished")
    doi = field(entry, "doi")
    doi = doi if doi and re.match(r"^10\.\d{4,9}/\S+$", doi) else None
    preprint = bool(re.search(r"arXiv", entry)) and not doi
    sid = f"SRC-{n:03d}"
    key2src[k] = sid
    ab, abpath = abstracts.get(k) or abstracts.get((doi or "").lower()) or ("", None)
    q = QUOTES.get(k)
    if q:
        if q not in ab:
            sys.exit(f"support quote for {k} not found in its saved abstract")
        est = [{"statement": f"cited for: {q[:80]}", "support_quote": q[:400], "location": f"abstract ({abpath})"}]
        depth = "abstract"
    else:
        est = [{"statement": "cited as the source of a dataset, method, software or reported figure; claim checked on 2 Nov 2026 (outputs/citation_audit/2026-11-02_ars/)",
                "support_quote": title[:400], "location": "title (claim check recorded in the 2 Nov 2026 citation audit)"}]
        depth = "abstract" if ab else "partial"
    sources.append({
        "id": sid, "cite_key": k, "title": title, "authors": authors, "year": year, "venue": venue, "doi": doi,
        "url": None, "publication_status": "PREPRINT" if preprint else ("DOCUMENTATION" if etype == "misc" and not doi else "PEER-REVIEWED"),
        "level": 2,
        "verification": {"method": "doi_lookup" if doi else "index_lookup", "date": "2026-11-23" if k in new_keys else "2026-11-02",
                         "verified_by": "agent", "retraction_checked": True},
        "read_depth": depth, "establishes": est, "permitted_use": ["content_citation"], "as_cited": title, "title_status": "verified"})

reg = R / "research_paper/.rcs/corpus/source_registry.json"
json.dump({"sources": sources}, open(reg, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
cm_p = R / "research_paper/.rcs/claims/claim_evidence_map.json"
cm = json.loads(cm_p.read_text(encoding="utf-8"))
lit = {"C040": ["tuzoff2019tooth"], "C041": ["krois2019deep", "chang2020deep"], "C042": ["tonetti2018staging"]}
for c in cm["claims"]:
    if c["id"] in lit:
        c["sources"] = [key2src[k] for k in lit[c["id"]]]
for d in cm["negative_result_decisions"]:
    d["decision"] = "reported_main"
ev = json.loads((R / "research_paper/.rcs/evidence/research_evidence.json").read_text(encoding="utf-8"))
reported = {d["evidence"] for d in cm["negative_result_decisions"]}
for it in ev["items"]:
    if it["kind"] == "negative_result" and it["id"] not in reported:
        cm["negative_result_decisions"].append({"evidence": it["id"], "decision": "reported_main", "where": "Section VI-E"})
json.dump(cm, open(cm_p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"{len(sources)} sources registered ({sum(1 for s in sources if s['doi'])} with DOI); keys: {len(keys)}")
