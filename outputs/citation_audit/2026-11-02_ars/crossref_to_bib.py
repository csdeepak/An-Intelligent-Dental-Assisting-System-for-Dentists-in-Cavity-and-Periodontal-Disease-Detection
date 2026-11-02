"""BibTeX from Crossref records (authors, title, container, volume, issue, pages, year, DOI).
usage: python -I crossref_to_bib.py key=doi ... > out.bib"""
import json, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
LATEX = {"é": "{\\'e}", "è": "{\\`e}", "ö": '{\\"o}', "ü": '{\\"u}', "ä": '{\\"a}', "á": "{\\'a}",
         "í": "{\\'i}", "ó": "{\\'o}", "ñ": "{\\~n}", "ç": "{\\c{c}}"}


def tex(s):
    s = " ".join((s or "").split())
    for k, v in LATEX.items():
        s = s.replace(k, v)
    return s.replace("&", "\\&")


for arg in sys.argv[1:]:
    key, doi = arg.split("=", 1)
    req = urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe=""),
                                 headers={"User-Agent": "ARS-v3.9.0"})
    m = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["message"]
    typ = "inproceedings" if m.get("type") == "proceedings-article" else "article"
    authors = " and ".join(f"{tex(a.get('family'))}, {tex(a.get('given'))}" if a.get("given") else tex(a.get("family") or a.get("name"))
                           for a in m.get("author", []))
    year = (m.get("issued") or {}).get("date-parts", [[None]])[0][0]
    title = tex((m.get("title") or [""])[0])
    cont = tex((m.get("container-title") or [""])[0])
    f = [("author", authors), ("title", "{" + title + "}"),
         ("booktitle" if typ == "inproceedings" else "journal", cont)]
    for fk, ck in (("volume", "volume"), ("number", "issue")):
        if m.get(ck): f.append((fk, m[ck]))
    if m.get("page"): f.append(("pages", m["page"].replace("-", "--")))
    elif m.get("article-number"): f.append(("pages", m["article-number"]))
    f += [("year", str(year)), ("doi", m.get("DOI"))]
    w = max(len(k) for k, _ in f)
    print(f"@{typ}{{{key},\n" + ",\n".join(f"  {k.ljust(w)} = {{{v}}}" for k, v in f) + "\n}\n")
    time.sleep(0.3)
