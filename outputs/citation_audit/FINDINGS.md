# DOI verification against the registry — 1 September 2026

**Read-only audit. No citation was changed.** Produced by
`scripts/verify_citations_crossref.py`; raw log in `doi_verification_report.txt`.

## Why this was run

`audit_citations.py` prints each claim beside the entry it cites, for human review. It makes
**no network call**, so it cannot tell whether a DOI resolves to the paper being claimed. That
gap let `chen2024cariesxrays` through a full citation audit on 2026-08-28 with a DOI pointing at
the *adjacent* AAAI article (RESULTS_LOG 2026-09-01c). This audit dereferences every DOI.

Two defects in the old script were fixed first: it had a **hardcoded Windows path** (so it could
not run on this machine at all — which is why it had not been re-run), and it had no verification
step.

## Method

Each DOI is resolved twice, against the registry rather than one agency:

1. `doi.org/doiRA/<doi>` — which agency registered it. **"DOI does not exist"** is decisive.
2. `doi.org/<doi>` with `Accept: application/vnd.citationstyles.csl+json` — **content
   negotiation**, so DOIs registered with DataCite (all arXiv DOIs) resolve as well as Crossref
   ones. An earlier Crossref-only version reported 16 false failures for exactly this reason.

Title comparison is Jaccard over content words after stripping LaTeX. Author comparison strips
LaTeX accent macros (`G{\"u}ner` → `Guner`). Year gaps of 1 are treated as notes, not errors,
because online-first and issue years routinely differ.

**Validated against a known answer before use:** the corrected `chen2024cariesxrays` DOI scores
title overlap **1.00**; the previously-wrong DOI scores **0.05** and correctly names the paper it
actually resolves to. The tool catches the error that survived the manual audit.

## Result — 63 entries carry a DOI, 19 do not

| category | count | meaning |
|---|---|---|
| clean | **40** | DOI resolves to the paper claimed |
| **resolves to a DIFFERENT paper** | **11** | DOI is real but identifies unrelated work |
| **DOI not registered with any agency** | **11** | the DOI string does not exist |
| author notation only | 1 | cosmetic (`Yalım` vs `Yalim`), not an error |
| not checkable | 19 | no DOI in the entry — absence of a check is not a pass |

### **22 of 63 checkable entries (35%) have a broken DOI.**

**Resolves to a different paper** — the DOI is valid but points elsewhere:

| key | DOI in bib | actually resolves to |
|---|---|---|
| `adnan2024orthopantomogram` | 10.1016/j.dib.2024.110654 | a COVID/CHAMPS HDSS household survey dataset |
| `bonfanti2025deep` | 10.1186/s12903-025-05939-x | 3D-printed micro-osteoperforations, canine retraction |
| `cerda2024determining` | 10.1186/s12903-024-04795-5 | MMP levels in pulpitis |
| `delamare2024panoramic` | 10.1093/dmfr/twad010 | ultra-low-dose photon-counting CT of sinuses |
| `karamuftuo2025panoramic` | 10.3390/children12030304 | *Foundations of Pediatric Lifestyle Medicine* |
| `kong2024integrating` | 10.3390/bioengineering11121192 | OCT-guided femtosecond laser keratoplasty |
| `lim2024dual` | 10.1016/j.prosdent.2023.10.028 | — |
| `vannistelrooij2024combining` | 10.1186/s12903-024-04170-4 | — |
| `waqas2025synthetic` | 10.1016/j.identj.2024.09.027 | — |
| `zancan2025ai` | 10.1371/journal.pdig.0000744 | clinical validation of a hand-dexterity device |
| `zanini2024systematic` | 10.1007/s10278-024-01112-y | super-resolution cervical-spine MRI |

**DOI not registered with any agency** — the string does not exist:

`ameli2025automated` · `asadi2024detection` · `bhoopalan2026self` · `bilal2024pdcnet` ·
`ferrara2025applications` · `khuwaja2024ai` · `kim2024unsupervised` · `lee2025evaluation` ·
`mathur2025comparative` · `tian2025development` · `zhang2025reliable`

## What this does and does not establish

**Does:** these 22 DOIs do not identify the works the bibliography claims. Verified against
doi.org itself, which is agency-agnostic, so this is not an artefact of querying one provider.

**Does not:** it does not establish that the *cited papers* are fake. A real paper can carry a
mistyped or hallucinated DOI. Each of the 22 needs a manual lookup by title to decide whether the
reference is real with a wrong identifier, or does not exist at all. **That distinction has to be
made by hand and is not attempted here.**

**Also unverified:** the 19 entries with no DOI were not checked by any means. Several are arXiv
or web sources where that is expected, but it is not a pass.

## Priority

**This blocks submission.** A reviewer who dereferences one bad DOI will check the rest, and a
bibliography where a third of the identifiers are wrong invites the conclusion that the references
were not read. It is the same failure class the 2026-08-28 audit found (7 errors, including two
invented titles) and did not fully clear.

Re-run any time: `python scripts/verify_citations_crossref.py`
