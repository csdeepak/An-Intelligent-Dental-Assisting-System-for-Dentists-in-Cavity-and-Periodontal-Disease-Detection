#!/usr/bin/env python
"""Resolve every DOI in source.bib against Crossref and compare it to what we claim.

WHY THIS EXISTS
---------------
`audit_citations.py` prints each claim beside the entry it cites, for a human to read. That
catches a citation supporting the wrong claim. It does **not** verify that the DOI resolves to
the paper we say it does, because it makes no network call at all.

That gap has cost this project twice. The 2026-08-28 audit found 7 citation errors including
4 wrong DOIs. It still missed `chen2024cariesxrays`, whose title and pages were right but whose
DOI pointed at `10.1609/aaai.v38i20.30197` -- the *adjacent* AAAI article, "Referee-Meta-Learning
for Fast Adaptation of Locational Fairness", pp. 21949-21957, an unrelated paper. The correct id
is 30196. An off-by-one in an article id is invisible to any check that does not dereference it
(RESULTS_LOG 2026-09-01c).

WHAT IT CHECKS
--------------
For every bib entry carrying a DOI, fetch `api.crossref.org/works/<doi>` and compare against
what the entry asserts:

  * **title**   -- token overlap after normalising case, LaTeX braces and punctuation. A low
                   score is the signal that matters: it is what an off-by-one id produces.
  * **year**    -- exact, against Crossref's issued/published-print date.
  * **author**  -- first author's surname.

Crossref is the DOI registration agency for these publishers, so its record *is* the publisher
record. Entries without a DOI are listed as unverifiable rather than silently passed -- absence
of a check is not a pass.

This is READ-ONLY. It never edits source.bib; it prints what disagrees and exits non-zero.

Usage:
    python scripts/verify_citations_crossref.py --key chen2024cariesxrays   # one entry
    python scripts/verify_citations_crossref.py --limit 5                   # first 5
    python scripts/verify_citations_crossref.py                             # full sweep
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper" / "source.bib"
# Crossref asks for a contact address in the UA so they can reach you about traffic.
UA = "dental-ai-capstone-citation-audit/1.0 (mailto:gunadeep19082005@gmail.com)"

STOP = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "via", "with", "using", "from"}


ACC = {"\\\"a": "a", "\\\"o": "o", "\\\"u": "u", "\\'e": "e", "\\`e": "e",
       "\\'a": "a", "\\'o": "o", "\\~n": "n", "\\c c": "c", "\\v s": "s"}


def delatex(s):
    """G{\"u}ner -> Guner. Accent macros are a notation difference, not a citation error."""
    if not s:
        return ""
    for k, v in ACC.items():
        s = s.replace(k, v)
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = s.replace("{", "").replace("}", "")
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))
    return s


def norm_tokens(s):
    s = re.sub(r"\{|\}|\$|\\[a-zA-Z]+", " ", s or "")
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return [w for w in s.split() if w and w not in STOP]


def title_overlap(a, b):
    """Jaccard over content words. Robust to LaTeX braces, casing and subtitle punctuation."""
    A, B = set(norm_tokens(a)), set(norm_tokens(b))
    return len(A & B) / len(A | B) if A | B else 0.0


def parse_bib(text):
    out = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        key, body = m.group(2).strip(), m.group(3)
        def field(name):
            f = re.search(name + r"\s*=\s*\{(.+?)\}\s*,?\s*\n", body, re.S)
            return re.sub(r"\s+", " ", f.group(1)).strip() if f else None
        out[key] = {
            "type": m.group(1), "title": field("title"), "year": field("year"),
            "author": field("author"), "doi": field("doi"),
            "venue": field("journal") or field("booktitle"),
        }
    return out


def registration_agency(doi, timeout=15):
    """Ask doi.org who registered this DOI. 'DOI does not exist' is the decisive answer."""
    url = "https://doi.org/doiRA/" + doi
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.load(r)
    return (j[0].get("RA") or j[0].get("status") or "?") if j else "?"


def fetch_meta(doi, timeout=25):
    """Metadata via doi.org CONTENT NEGOTIATION, not the Crossref API.

    Crossref only knows Crossref-registered DOIs, so an arXiv DOI (registered with DataCite)
    404s there and looks like an error when it is perfectly valid. Content negotiation against
    doi.org returns CSL JSON whichever agency registered it.
    """
    req = urllib.request.Request(
        "https://doi.org/" + doi,
        headers={"User-Agent": UA, "Accept": "application/vnd.citationstyles.csl+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib", type=Path, default=BIB)
    ap.add_argument("--key", help="check a single bib key")
    ap.add_argument("--limit", type=int, help="check only the first N entries with a DOI")
    ap.add_argument("--title-threshold", type=float, default=0.55,
                    help="Jaccard below this is reported as a title mismatch")
    ap.add_argument("--delay", type=float, default=0.4, help="seconds between requests")
    args = ap.parse_args()

    ents = parse_bib(args.bib.read_text(encoding="utf-8"))
    if args.key:
        if args.key not in ents:
            raise SystemExit(f"{args.key} is not in {args.bib.name}")
        ents = {args.key: ents[args.key]}

    with_doi = {k: v for k, v in ents.items() if v["doi"]}
    without = sorted(set(ents) - set(with_doi))
    keys = sorted(with_doi)[:args.limit] if args.limit else sorted(with_doi)

    print(f"{len(ents)} entries | {len(with_doi)} with a DOI | checking {len(keys)}")
    print(f"unverifiable (no DOI): {len(without)}" + (f" -> {', '.join(without)}" if without else ""))
    print("=" * 72)

    bad, errors, nonexistent = [], [], []
    for i, k in enumerate(keys, 1):
        e = with_doi[k]
        doi = e["doi"].strip()
        try:
            ra = registration_agency(doi)
        except Exception:
            ra = "?"
        if ra == "DOI does not exist":
            nonexistent.append((k, doi))
            print(f"[{i}/{len(keys)}] GONE {k}\n        DOI IS NOT REGISTERED WITH ANY AGENCY: {doi}")
            time.sleep(args.delay)
            continue
        try:
            msg = fetch_meta(doi)
        except Exception as ex:
            errors.append((k, doi, f"{type(ex).__name__} (agency={ra})"))
            print(f"[{i}/{len(keys)}] ERR  {k}  {doi}  metadata unavailable (agency={ra})")
            time.sleep(args.delay)
            continue

        ttl = msg.get("title")
        cr_title = ttl[0] if isinstance(ttl, list) else (ttl or "")
        parts = ((msg.get("issued") or {}).get("date-parts") or [[None]])
        cr_year = str(parts[0][0]) if parts and parts[0] and parts[0][0] else None
        auths = msg.get("author") or []
        cr_first = (auths[0].get("family") or "") if auths else ""

        ov = title_overlap(e["title"], cr_title)
        bib_first = ""
        if e["author"]:
            bib_first = re.split(r"\s+and\s+", e["author"])[0]
            bib_first = bib_first.split(",")[0].strip() if "," in bib_first else bib_first.split()[-1]
            bib_first = delatex(bib_first)

        issues, notes = [], []
        if ov < args.title_threshold:
            issues.append(f"TITLE overlap {ov:.2f}\n        bib: {e['title'][:88]}\n        DOI: {cr_title[:88]}")
        if cr_year and e["year"] and cr_year != e["year"]:
            # online-first vs issue year routinely differs by one; flag >1 as an error and
            # 1 as a note, so a real mis-citation is not buried among harmless offsets.
            gap = abs(int(cr_year) - int(e["year"])) if cr_year.isdigit() and e["year"].isdigit() else 9
            (issues if gap > 1 else notes).append(f"YEAR bib={e['year']} DOI={cr_year}")
        if cr_first and delatex(bib_first) and delatex(cr_first).lower() != bib_first.lower():
            issues.append(f"FIRST AUTHOR bib={bib_first} DOI={cr_first}")

        status = "OK  " if not issues else "BAD "
        print(f"[{i}/{len(keys)}] {status}{k}  (title overlap {ov:.2f})")
        for x in issues:
            print(f"        {x}")
        for x in notes:
            print(f"        note: {x}")
        if issues:
            bad.append((k, doi, issues))
        time.sleep(args.delay)

    print("=" * 72)
    print(f"checked {len(keys)}  |  clean {len(keys)-len(bad)-len(errors)-len(nonexistent)}  |  "
          f"WRONG PAPER {len(bad)}  |  DOI NOT REGISTERED {len(nonexistent)}  |  "
          f"metadata unavailable {len(errors)}")
    for k, doi in nonexistent:
        print(f"  NOT REGISTERED  {k}  {doi}")
    if without:
        print(f"NOT CHECKED (no DOI): {len(without)} -- absence of a check is not a pass")
    for k, doi, _ in bad:
        print(f"  MISMATCH  {k}  {doi}")
    for k, doi, why in errors:
        print(f"  ERROR     {k}  {doi}  {why}")
    sys.exit(1 if (bad or errors or nonexistent) else 0)


if __name__ == "__main__":
    main()
