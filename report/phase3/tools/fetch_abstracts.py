"""Fetch the abstracts of cited sources that have none saved, for the GL gate's support quotes.

Public bibliographic metadata only: OpenAlex by DOI (inverted-index abstract), Semantic Scholar by DOI as
a fallback, arXiv by ID, and an OpenAlex title search for entries with no identifier (accepted only when
the returned title matches). Writes .rcs/corpus/p3c_abstracts.json with the service and date of each.

    python -I tools/fetch_abstracts.py      (needs network; after tools/rcs_build.py)
"""
import difflib
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
CORPUS = HERE / ".rcs" / "corpus"
OUT = CORPUS / "p3c_abstracts.json"
ROOT = HERE.parents[1]
SAVED = [ROOT / "outputs/citation_audit/2026-11-02_ars/claim_abstracts.json",
         ROOT / "outputs/citation_audit/2026-11-02_ars/new_abstracts.json",
         CORPUS / "p2_abstracts.json", CORPUS / "p3_abstracts.json", CORPUS / "p3b_abstracts.json"]
ARXIV = {"geifman2017selective": "1705.08500", "guo2017calibration": "1706.04599", "bai2025qwen25vl": "2502.13923",
         "geirhos2020shortcut": "2004.07780"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "RCE-report-check/1.0 (mailto:none)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def from_inverted(inv):
    words = sorted((p, w) for w, ps in (inv or {}).items() for p in ps)
    return " ".join(w for _, w in words)


def openalex_doi(doi):
    d = json.loads(get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="")
                       + "?select=title,publication_year,abstract_inverted_index"))
    return d.get("title"), from_inverted(d.get("abstract_inverted_index"))


def s2_doi(doi):
    d = json.loads(get("https://api.semanticscholar.org/graph/v1/paper/DOI:" + urllib.parse.quote(doi, safe="")
                       + "?fields=title,abstract"))
    return d.get("title"), d.get("abstract") or ""


def crossref_doi(doi):
    d = json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")))["message"]
    return (d.get("title") or [None])[0], re.sub(r"<[^>]+>", " ", d.get("abstract") or "")


def pubmed_doi(doi):
    q = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    ids = json.loads(get(q + "esearch.fcgi?db=pubmed&retmode=json&term=" + urllib.parse.quote(doi + "[doi]")))
    ids = ids["esearchresult"]["idlist"]
    if not ids:
        return None, ""
    root = ET.fromstring(get(q + "efetch.fcgi?db=pubmed&retmode=xml&id=" + ids[0]))
    t = root.find(".//ArticleTitle")
    return ("".join(t.itertext()) if t is not None else None,
            " ".join("".join(a.itertext()) for a in root.findall(".//AbstractText")))


def arxiv(aid):
    x = ET.fromstring(get("https://export.arxiv.org/api/query?id_list=" + aid))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = x.find("a:entry", ns)
    return " ".join(e.find("a:title", ns).text.split()), " ".join(e.find("a:summary", ns).text.split())


def openalex_title(title):
    d = json.loads(get("https://api.openalex.org/works?per-page=3&select=title,abstract_inverted_index&search="
                       + urllib.parse.quote(title)))
    for r in d.get("results", []):
        if difflib.SequenceMatcher(None, (r.get("title") or "").lower(), title.lower()).ratio() > 0.9:
            return r.get("title"), from_inverted(r.get("abstract_inverted_index"))
    return None, ""


have = set()
for f in SAVED:
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        have |= {k for k, v in d.items() if isinstance(v, dict) and (v.get("abstract") or "").strip()}
out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
sources = json.loads((CORPUS / "source_registry.json").read_text(encoding="utf-8"))["sources"]
for s in sources:
    k = s["key"]
    if not s.get("cited_in_report") or k in have or (out.get(k) or {}).get("abstract"):
        continue
    rec = {"title": None, "abstract": "", "service": None, "retrieved": date.today().isoformat()}
    tries = ([("arxiv", lambda: arxiv(ARXIV[k]))] if k in ARXIV else []) + \
            ([("openalex", lambda: openalex_doi(s["doi"])), ("crossref", lambda: crossref_doi(s["doi"])),
              ("pubmed", lambda: pubmed_doi(s["doi"])),
              ("semantic_scholar", lambda: (time.sleep(3), s2_doi(s["doi"]))[1])]
             if s.get("doi") and not s["doi"].startswith("10.48550") else []) + \
            [("openalex_title_search", lambda: openalex_title(re.sub(r"[{}]", "", s.get("title") or "")))]
    for name, fn in tries:
        try:
            title, abstract = fn()
        except Exception as exc:                     # network or parse error: try the next service
            rec.setdefault("errors", []).append(f"{name}: {type(exc).__name__}")
            time.sleep(1)
            continue
        if abstract and len(abstract.split()) > 20:
            rec.update(title=title, abstract=" ".join(abstract.split()), service=name)
            break
        time.sleep(1)
    out[k] = rec
    print(f"{k:<28} {rec['service'] or 'NONE':<22} {len(rec['abstract'].split())} words")
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
