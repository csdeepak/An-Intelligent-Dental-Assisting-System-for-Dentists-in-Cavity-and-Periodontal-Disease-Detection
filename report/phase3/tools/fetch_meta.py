"""Fetch OpenAlex metadata for the cited sources: the full author list and the retraction flag.

Used by tools/rcs_build.py where the bibliography truncates the authors ("and others") and where the
2 Nov audit left the retraction status unchecked. Public bibliographic metadata only, by DOI.
Writes .rcs/corpus/openalex_meta.json.

    python -I tools/fetch_meta.py      (needs network; after tools/rcs_build.py)
"""
import json
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
CORPUS = HERE / ".rcs" / "corpus"
OUT = CORPUS / "openalex_meta.json"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "RCE-report-check/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def surname(display_name):
    n = display_name.split()[-1] if display_name.split() else display_name
    return "".join(c for c in unicodedata.normalize("NFKD", n) if not unicodedata.combining(c))


out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
for s in json.loads((CORPUS / "source_registry.json").read_text(encoding="utf-8"))["sources"]:
    doi = s.get("doi")
    if not doi or doi.startswith("10.48550") or s["key"] in out:
        continue
    try:
        w = get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="")
                + "?select=display_name,authorships,is_retracted")
    except Exception as exc:                          # record the failure; rcs_build keeps the bib's list
        out[s["key"]] = {"error": type(exc).__name__, "retrieved": date.today().isoformat()}
        continue
    out[s["key"]] = {"authors": [surname(a["author"]["display_name"]) for a in w.get("authorships") or []],
                     "is_retracted": w.get("is_retracted"), "retrieved": date.today().isoformat()}
    time.sleep(0.2)
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{len(out)} records; retracted: {[k for k, v in out.items() if v.get('is_retracted')]}; "
      f"errors: {[k for k, v in out.items() if v.get('error')]}")
