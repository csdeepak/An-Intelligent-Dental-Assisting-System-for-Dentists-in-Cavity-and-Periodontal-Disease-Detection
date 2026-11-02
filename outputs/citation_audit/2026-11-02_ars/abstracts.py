"""Fetch abstracts for claim-faithfulness checking: OpenAlex by DOI (inverted index), arXiv by ID.
usage: python -I abstracts.py out.json key=doi:<doi>|arxiv:<id> ..."""
import json, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ARS-v3.9.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def openalex(doi):
    d = json.loads(get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="")
                       + "?select=title,publication_year,abstract_inverted_index,primary_location"))
    inv = d.get("abstract_inverted_index") or {}
    words = sorted((p, w) for w, ps in inv.items() for p in ps)
    return {"title": d.get("title"), "year": d.get("publication_year"), "abstract": " ".join(w for _, w in words)}


def arxiv(aid):
    x = ET.fromstring(get("https://export.arxiv.org/api/query?id_list=" + aid))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = x.find("a:entry", ns)
    return {"title": " ".join(e.find("a:title", ns).text.split()), "abstract": " ".join(e.find("a:summary", ns).text.split())}


out = {}
for arg in sys.argv[2:]:
    key, spec = arg.split("=", 1)
    kind, ident = spec.split(":", 1)
    try:
        out[key] = (openalex if kind == "doi" else arxiv)(ident)
    except Exception as ex:
        out[key] = {"error": str(ex)[:200]}
    time.sleep(0.4 if kind == "doi" else 3.1)
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in out.items():
    print(f"== {k}: {v.get('title')}\n{(v.get('abstract') or v.get('error') or '')[:1500]}\n")
