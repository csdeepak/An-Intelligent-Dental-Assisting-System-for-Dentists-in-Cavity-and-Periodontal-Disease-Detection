"""Four-index citation triangulation (Crossref, OpenAlex, Semantic Scholar, arXiv) using the
academic-research-skills resolver clients unmodified, plus a Crossref retraction/correction check
and a metadata comparison against the .bib entry.

Classification follows ARS v3.11 C-V6: `matched` if any resolver matches; `false` only when an
ID-keyed lookup (DOI / arXiv ID) is unmatched and nothing matched; otherwise `unresolvable`.

usage: python -I verify_refs.py <bibfile> [<bibfile> ...] <out.json>
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

# The academic-research-skills clone (commit a41f3b2) is not vendored here (CC BY-NC 4.0);
# point ARS_SCRIPTS at its scripts/ folder.
ARS = Path(os.environ.get("ARS_SCRIPTS", Path(__file__).resolve().parent / "repo" / "scripts"))
sys.path.append(str(ARS))
from crossref_client import CrossrefClient, CrossrefUnavailable          # noqa: E402
from openalex_client import OpenAlexClient, OpenAlexUnavailable          # noqa: E402
from semantic_scholar_client import SemanticScholarClient                 # noqa: E402
from arxiv_client import ArxivClient, ArxivUnavailable                    # noqa: E402
from _text_similarity import _similarity                                  # noqa: E402


def parse_bib(text):
    out = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        typ, key, i, depth = m.group(1).lower(), m.group(2), m.end(), 1
        j = i
        while depth and j < len(text):
            depth += {"{": 1, "}": -1}.get(text[j], 0); j += 1
        body, fields = text[i:j - 1], {}
        for f in re.finditer(r"(\w+)\s*=\s*", body):
            k, s = f.group(1).lower(), f.end()
            if s < len(body) and body[s] == "{":
                d, e = 1, s + 1
                while d and e < len(body):
                    d += {"{": 1, "}": -1}.get(body[e], 0); e += 1
                fields.setdefault(k, body[s + 1:e - 1])
            else:
                v = re.match(r'"([^"]*)"|(\w+)', body[s:])
                if v: fields.setdefault(k, v.group(1) or v.group(2))
        out.append({"type": typ, "key": key, **fields})
    return out


def clean(s):
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s or "")
    return re.sub(r"\s+", " ", s.replace("{", "").replace("}", "")).strip()


def arxiv_id(e):
    blob = " ".join(str(e.get(k, "")) for k in ("eprint", "howpublished", "note", "url", "journal", "doi"))
    m = re.search(r"(?:arXiv[:\s]*|arxiv\.org/abs/|10\.48550/arXiv\.)(\d{4}\.\d{4,5})", blob, re.I)
    return m.group(1) if m else None


def first_surname(authors):
    a = clean(authors).split(" and ")[0].strip()
    return (a.split(",")[0] if "," in a else a.split(" ")[-1]).strip().lower()


def retraction_notices(doi):
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"filter": f"updates:{doi}", "rows": "20"})
    req = urllib.request.Request(url, headers={"User-Agent": "ARS-v3.9.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            items = json.loads(r.read().decode())["message"]["items"]
    except Exception as ex:
        return {"status": "unreachable", "error": str(ex)[:120]}
    notes = []
    for it in items:
        for u in it.get("update-to", []):
            if u.get("DOI", "").lower() == doi.lower():
                notes.append({"type": u.get("type"), "notice_doi": it.get("DOI")})
    return {"status": "checked", "notices": notes}


def main():
    *bibs, outp = sys.argv[1:]
    entries, seen = [], set()
    for b in bibs:
        for e in parse_bib(Path(b).read_text(encoding="utf-8")):
            if e["key"] not in seen:
                seen.add(e["key"]); entries.append(e)
    cr, oa, s2, ax = CrossrefClient(), OpenAlexClient(), SemanticScholarClient(), ArxivClient()
    results = []
    for n, e in enumerate(entries, 1):
        title, year = clean(e.get("title")), e.get("year")
        year = int(re.sub(r"\D", "", year)[:4]) if year and re.search(r"\d{4}", year) else None
        doi = (e.get("doi") or "").strip() or None
        axid = arxiv_id(e)
        r = {"key": e["key"], "title": title, "year": year, "doi": doi, "arxiv": axid,
             "first_author": first_surname(e.get("author", "")), "venue": clean(e.get("journal") or e.get("booktitle") or e.get("howpublished") or ""),
             "resolvers": {}, "records": {}}
        def run(name, fn, keyed):
            try:
                hit = fn()
                r["resolvers"][name] = {"outcome": "matched" if hit else "unmatched", "query": keyed}
                if hit: r["records"][name] = hit
            except Exception as ex:
                r["resolvers"][name] = {"outcome": "unreachable", "query": keyed, "error": str(ex)[:120]}
        if doi:
            run("crossref", lambda: cr.doi_lookup_with_title_check(doi, title), "doi")
        if "crossref" not in r["records"] and title:
            run("crossref_title", lambda: cr.title_search(title, year), "title")
        if doi:
            run("openalex", lambda: oa.doi_lookup_with_title_check(doi, title), "doi")
        if "openalex" not in r["records"] and title:
            run("openalex_title", lambda: oa.title_search(title, year), "title")
        run("semantic_scholar", lambda: (lambda x: x if x.get("matched") else None)(s2.lookup({"doi": doi, "title": title, "year": year})), "doi+title" if doi else "title")
        if axid:
            run("arxiv", lambda: ax.arxiv_id_lookup(axid, title), "arxiv_id")
        matched = any(v["outcome"] == "matched" for v in r["resolvers"].values())
        id_unmatched = any(v["outcome"] == "unmatched" and v["query"] in ("doi", "arxiv_id") for v in r["resolvers"].values())
        r["lookup_verified"] = "true" if matched else ("false" if id_unmatched else "unresolvable")
        # metadata comparison against the best record (Crossref first)
        rec = r["records"].get("crossref") or r["records"].get("crossref_title")
        if rec:
            ry = None
            for k in ("issued", "published-print", "published-online"):
                dp = (rec.get(k) or {}).get("date-parts")
                if dp and dp[0] and dp[0][0]: ry = dp[0][0]; break
            au = (rec.get("author") or [{}])[0]
            r["crossref_meta"] = {"title": (rec.get("title") or [""])[0], "year": ry,
                                  "first_author": (au.get("family") or au.get("name") or "").lower(),
                                  "venue": (rec.get("container-title") or [""])[0], "doi": rec.get("DOI"),
                                  "volume": rec.get("volume"), "page": rec.get("page"), "type": rec.get("type")}
            r["title_sim"] = round(_similarity(r["crossref_meta"]["title"], title), 3)
            r["year_match"] = (ry == year) if (ry and year) else None
            r["author_match"] = (r["first_author"] and r["first_author"] in r["crossref_meta"]["first_author"]) or None
            if not doi and rec.get("DOI"):
                r["doi_found"] = rec.get("DOI")
        d = doi or r.get("doi_found")
        if d:
            r["retraction"] = retraction_notices(d)
        r.pop("records")
        results.append(r)
        print(f"[{n}/{len(entries)}] {e['key']}: {r['lookup_verified']}  "
              + " ".join(f"{k}={v['outcome'][0]}" for k, v in r["resolvers"].items()), flush=True)
    Path(outp).write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
