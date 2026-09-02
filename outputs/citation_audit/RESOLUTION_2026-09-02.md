# DOI blocker — resolution, 2 September 2026

Companion to `FINDINGS.md` (the 1 Sep read-only audit). This file records what was
**changed** in `paper/source.bib` and how each correction was verified.

## Outcome

| | 1 Sep audit | after this pass |
|---|---|---|
| checkable DOIs | 63 | 63 |
| clean | 40 | **62** |
| resolves to a different paper | 11 | 0 |
| DOI not registered | 11 | 0 |
| cosmetic author-notation flag | 1 (`yalim2026comparative`) | 1 (unchanged — not an error) |
| DOI-less entries (not checkable) | 19 | 19 (unchanged — separate task) |

**All 22 broken entries were real, published papers carrying a wrong identifier. No entry
was found to be fabricated.**

## Method

1. Each of the 22 was looked up by **title** (web search + publisher sites + Crossref
   `query.bibliographic`).
2. The candidate DOI was dereferenced against `doi.org` with CSL-JSON content negotiation;
   accepted only when title-overlap (Jaccard over content words) was **1.00** against the
   registry record.
3. The registry record's `volume` / `issue` / `page` / `year` were taken as authoritative
   and the bib fields corrected to match — 19 of 22 had at least one of these wrong too.
4. `url` fields that embedded the old DOI were rewritten to `https://doi.org/<correct-doi>`.

## Corrections (key → old DOI → new DOI)

### Group 1 — was resolving to a different paper

| key | old (wrong) DOI | corrected DOI | also fixed |
|---|---|---|---|
| adnan2024orthopantomogram | 10.1016/j.dib.2024.110654 | 10.1016/j.dib.2024.111152 | vol 55→57, pp 110654→111152 |
| bonfanti2025deep | 10.1186/s12903-025-05939-x | 10.1186/s12903-025-06349-9 | pp 977→1280; url |
| cerda2024determining | 10.1186/s12903-024-04795-5 | 10.1186/s12903-023-03819-w | pp 1023→100; url |
| delamare2024panoramic | 10.1093/dmfr/twad010 | 10.1093/dmfr/twae002 | — |
| karamuftuo2025panoramic | 10.3390/children12030304 | 10.3390/children12111517 | pp 304→1517 |
| kong2024integrating | 10.3390/bioengineering11121192 | 10.3390/bioengineering11111130 | pp 1192→1130 |
| lim2024dual | 10.1016/j.prosdent.2023.10.028 | 10.1016/j.prosdent.2025.09.040 | year 2024→2026, vol→135, pp→403.e1–403.e8; url |
| vannistelrooij2024combining | 10.1186/s12903-024-04170-4 | 10.1186/s12903-024-04129-5 | pp 426→387; url |
| waqas2025synthetic | 10.1016/j.identj.2024.09.027 | 10.1016/j.identj.2025.103878 | pp 1020–1030→103878 |
| zancan2025ai | 10.1371/journal.pdig.0000744 | 10.1371/journal.pdig.0001074 | art e0000744→e0001074 |
| zanini2024systematic | 10.1007/s10278-024-01112-y | 10.1007/s10278-024-01054-5 | pp 2488–2517→1824–1845; url |

### Group 2 — was unregistered

| key | old (nonexistent) DOI | corrected DOI | also fixed |
|---|---|---|---|
| ameli2025automated | 10.5624/isd.20240141 | 10.5624/isd.20240232 | pp e12→175 |
| asadi2024detection | 10.1145/3704000.3704017 | 10.1145/3691521.3691522 | proceedings title, pp→40–47, url |
| bhoopalan2026self | 10.1038/s41598-025-88069-y | 10.1038/s41598-026-36672-2 | pp 3175→5914 |
| bilal2024pdcnet | 10.1109/ACCESS.2024.3352398 | 10.1109/ACCESS.2024.3472012 | pp 10261–10275→150147–150168 |
| ferrara2025applications | 10.21037/jmai-24-187 | 10.21037/jmai-24-241 | — |
| khuwaja2024ai | 10.1109/INMIC63993.2024.10815494 | 10.1109/INMIC64792.2024.11004399 | pp→1–6 |
| kim2024unsupervised | 10.1038/s41598-024-57430-6 | 10.1038/s41598-024-73665-5 | pp 6718→23237 |
| lee2025evaluation | 10.1186/s12903-025-05618-1 | 10.1186/s12903-025-05677-0 | pp 365→329; url |
| mathur2025comparative | 10.3390/engproc2025082026 | 10.3390/engproc2025087080 | pp 26→80 |
| tian2025development | 10.1186/s12903-025-05525-3 | 10.1186/s12903-025-05714-y | pp 188→417; url |
| zhang2025reliable | 10.1109/JBHI.2025.3526198 | 10.1109/JBHI.2025.3643805 | early-access: dropped vol/issue, pp→1–13, note added; url |

## Still open (tracked in `transfer.md` §3)

- **`url`-field sweep** across all 63 DOI-bearing entries — the audit script only checks
  `doi`, so a `url` pointing at a stale/wrong DOI is invisible to it. 6 were fixed here (the
  ones on entries already being touched); the rest are unchecked.
- **19 DOI-less entries** — mostly arXiv / web sources where that is expected, but "no DOI"
  is not the same as "verified". Decide per entry whether to add an identifier or leave it.
- **`verify_citations_crossref.py`** dies mid-render on Windows (`cp1252` console cannot
  encode `İ`/`ı`); run with `PYTHONIOENCODING=utf-8`. Not a data problem.
