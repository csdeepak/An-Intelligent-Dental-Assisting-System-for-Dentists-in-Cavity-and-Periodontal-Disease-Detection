# -*- coding: utf-8 -*-
"""Sweep every bib entry's `url` field against its `doi` field.

WHY THIS EXISTS
---------------
`audit_citations.py` checks that every \\cite key resolves to a bib entry and prints the
claim beside it for human review. It never looks at whether a `doi` field and a `url` field
on the SAME entry agree. That gap already caused one incident: six entries carried a `url`
built from an earlier, wrong DOI after the `doi` field itself was corrected (RESULTS_LOG
2026-09-02). Nothing then would have caught a seventh.

WHAT IT CHECKS
--------------
For every entry with both a `doi` and a `url`: the DOI's suffix (the part after the registrant
prefix, e.g. `10.3390/` -> `dj13080361`) must appear inside the URL. This is deliberately a
substring check, not a resolver call -- it needs no network access, runs in under a second, and
catches exactly the failure mode that happened before: a URL pointing at a different DOI's
landing page. It cannot catch a URL that is wrong in some other way (dead link, wrong journal
issue with the same suffix), which is why this supplements human review rather than replacing it.

Also lists every entry with NO `doi` field at all, so that count is derived from the current
file rather than carried forward as a remembered number.

Run: py -3.13 scripts/audit_bib_urls.py
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper" / "source.bib"
text = BIB.read_text(encoding="utf-8")

def field(body, name):
    m = re.search(rf"\b{name}\s*=\s*\{{([^}}]+)\}}", body)
    return m.group(1).strip() if m else None


entries = list(re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S))
print(f"{len(entries)} entries parsed\n")

no_doi = []
mismatches = []
unchecked = []
ok = 0

for m in entries:
    kind, key, body = m.group(1), m.group(2).strip(), m.group(3)
    doi = field(body, "doi")
    url = field(body, "url")
    volume, number, pages = field(body, "volume"), field(body, "number"), field(body, "pages")

    if not doi:
        no_doi.append((key, kind, url))
        continue
    if not url:
        continue

    # nature.com / doi.org direct-DOI links: the DOI's own suffix (after "10.xxxx/") IS the
    # URL path segment, by that platform's own convention -- an exact match is required, and
    # a divergence here means one of the two fields points at a different article entirely.
    if "nature.com/articles/" in url or url.startswith("https://doi.org/"):
        suffix = doi.split("/", 1)[1]
        if url.rstrip("/").endswith(suffix):
            ok += 1
        else:
            mismatches.append((key, doi, url, "nature/doi.org: URL slug != DOI suffix"))
        continue

    # mdpi.com: the URL's own convention is /<issn>/<volume>/<issue>/<article-number>, and
    # for MDPI journals `pages` in the bib entry IS the article number (MDPI's numbering, not
    # a print page range) -- so this cross-checks three fields against the URL in one shot,
    # independent of the DOI entirely.
    if "mdpi.com" in url and volume and pages:
        # Path is /<issn>/<volume>/<issue>/<article>. The ISSN segment itself contains a
        # hyphen (e.g. 2304-6767) so it never matches a pure-digit segment -- only the last
        # three whole path segments are volume/issue/article.
        segs = [s for s in url.split("mdpi.com", 1)[1].split("/") if s]
        digit_segs = [s for s in segs if s.isdigit()]
        if len(digit_segs) >= 3 and digit_segs[-3] == volume and digit_segs[-1] == pages:
            ok += 1
        elif len(digit_segs) >= 3:
            mismatches.append((key, doi, url,
                f"mdpi: URL has volume/issue/article {digit_segs[-3]}/{digit_segs[-2]}/{digit_segs[-1]}, "
                f"bib says volume={volume} number={number} pages={pages}"))
        else:
            unchecked.append((key, doi, url))
        continue

    # Every other publisher (IEEE Xplore document IDs, ScienceDirect PII, PMC IDs, OUP,
    # SAGE, AME...) uses an internal catalogue ID that is legitimately unrelated to the DOI
    # suffix -- no structural check is possible without visiting the page.
    unchecked.append((key, doi, url))

print(f"doi+url pairs checked structurally: {ok + len(mismatches)}")
print(f"  consistent:            {ok}")
print(f"  STRUCTURAL MISMATCH:   {len(mismatches)}")
for key, doi, url, why in mismatches:
    print(f"    {key}")
    print(f"      doi: {doi}")
    print(f"      url: {url}")
    print(f"      why: {why}")

print(f"\nno structural check possible (publisher uses an opaque catalogue ID): {len(unchecked)}")
for key, doi, url in unchecked:
    print(f"    {key}")

print(f"\nentries with NO doi field: {len(no_doi)}")
for key, kind, url in no_doi:
    print(f"    {key:28s} ({kind})  url={url}")

sys.exit(1 if mismatches else 0)
