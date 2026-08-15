# 2026-08-13 — Survey paper literature update (47 → 70 references) + Excel sheet

**Session goal:** Bring the survey paper's literature review up to date with 2026
research, expand the reference corpus, integrate every change directly into the
LaTeX/BibTeX source and the literature-review Excel sheet, and ship a recompiled PDF.

## What was done

- Deployed research agents (a Literature Scout covering categories C1/C3/C6, plus a
  second scout covering additional categories) to search the current literature and
  return fully-verified new papers with complete bibliographic detail.
- Integrated 23 new papers (references 48–70) into `Survey Paper Latex folder/conference_101719.tex`:
  abstract, introduction, taxonomy, search methodology, all six C1–C6 sections plus six
  new "2026 Update" subsections, Table IV, Table I (System Taxonomy), Cross-Study Trends,
  Critical Analysis, Gap Analysis items 1–5, Research Roadmap, and Conclusion.
- Grew `source.bib` from 47 to 70 `@`-entries (864 lines). Converted `wimalasiri2025ai`
  from `@misc` (arXiv preprint) to `@article` citing its now-published Scientific Reports
  version.
- Verified the second scout's 10 papers' bibliographic metadata independently via live
  Crossref/publisher fetches (author lists, volume/issue/pages, DOIs) rather than trusting
  paraphrased summaries, because the exact BibTeX for that batch did not survive a
  mid-session context compaction.
- Compiled clean: `pdflatex → bibtex → pdflatex ×2`, 0 undefined references/citations,
  20 pages. All 70 `\cite{}` keys confirmed to have a matching `.bib` entry and vice versa.
- Updated `docs/reports/literature/Dental X-Ray Capstone Literature Review.xlsx`: added
  23 new rows (rows 49–71, "Paper 48"–"Paper 70") to `Sheet3` via a one-off script,
  preserving the exact original 18-column schema (SNO, Paper, Journal/Conference, Year,
  Authors, Link, Model, Dataset, Dataset Size, Metric, Best Result, Validation, XAI,
  Limitations, Research Gap, How Our Project is Better, Where Our Project Lags, Category).
- Caught and fixed a self-introduced fabrication bug before it shipped: several new prose
  passages implied the survey contained the capstone team's own experimental results
  (e.g. an invented "our own DENTEX-based detection stage" and a `\ref{sec:results}` that
  does not exist anywhere in the document). Caught by grepping the original, untouched
  `.tex` for "our system"/"our pipeline"/"our own" and finding zero pre-existing hits —
  confirming this convention was never part of the paper and was purely a drafting error.
  All 8 instances rewritten as third-party literature commentary.
- Fixed a genuine content-loss bug: a Table I `\multicolumn` footnote did not wrap and was
  being cut off mid-word in the compiled PDF (confirmed visually via a rendered PNG).
  Fixed by splitting it into two shorter footnote lines; re-render confirmed the fix.
- Fixed an orphaned `.bib` entry (`lee2025radiographic` defined but never `\cite{}`d) by
  adding a citing sentence in the C2 "2026 Update" subsection.
- Committed locally as `ebf8807`: "survey: integrate August 2026 literature update
  (47 -> 70 refs) + add publication research docs". **Not pushed as of this file.**

## Decisions made

1. **Used live Crossref/publisher verification instead of trusting paraphrased summaries**
   for the second scout's 10 papers, because the exact BibTeX did not survive a context
   compaction mid-session. Slower, but the alternative was guessing author lists —
   unacceptable for a document that will be submitted somewhere.
2. **Limited Table IV corrections to the 3 rows personally cross-checked against the
   paper's own body text** (Zancan, Zhang, Van Nistelrooij), rather than leaving a failed
   forensic-audit agent's gap silently unaddressed or fabricating verification for rows
   never actually checked.
3. **Used the better-sourced figure for MMOral's GPT-4o accuracy** — 43.31% from a direct
   fetch of the official NeurIPS proceedings PDF — over a second, summary-derived figure of
   41.45%, and flagged the discrepancy explicitly rather than averaging or silently
   picking one.
4. **Did not attempt to reconcile a pre-existing mismatch** between the xlsx `Category`
   column tallies and the survey's own stated per-category counts (discovered while
   verifying this session's own additions). Out of scope for this session; disclosed
   rather than silently left.

## Open questions

1. **Table IV is only partially audited.** Of its ~25 rows, only 3 (Zancan, Zhang, Van
   Nistelrooij) have been personally cross-checked against each paper's own reported
   numbers this session. The other ~22 rows are unverified — a dedicated forensic-audit
   agent was attempted earlier and failed (hit a session limit) and was never re-run.
   **This is the single biggest academic-integrity risk left in the survey.** Do not cite
   Table IV as fact-checked until this is closed.
2. **MMOral GPT-4o accuracy has two different sourced values in circulation**: 43.31%
   (official NeurIPS proceedings PDF, used in the current text) vs. 41.45% (a different
   agent's summary of the same paper). Not reconciled beyond picking the better-sourced
   one — worth a direct re-check of the proceedings PDF page.
3. **The xlsx literature-review sheet's `Category` column tallies don't match the survey's
   own stated per-category counts** — e.g. the original 47 rows tag out to C1=19/C2=14/
   C3=6/C5=4/C6=4, while the survey text itself says "18 C1 papers / Fifteen C2 / Seven C3
   / Four C6". Confirmed pre-existing (present before this session); this session's own 23
   new rows are internally consistent between `.tex` and `.xlsx`, but the older mismatch
   was not touched.
4. **No session-memory file existed for this session until now.** Everything above
   previously lived only in the commit message and an external chat transcript — neither
   of which a future session (in particular a teammate's separate Claude session reading
   this repo cold) would automatically see. This file exists specifically to close that gap.

## Next steps

1. Run a real Table IV audit — all ~25 rows checked against each source paper's own
   reported numbers — before treating the table as trustworthy.
2. Resolve the MMOral 43.31% vs 41.45% discrepancy definitively.
3. Reconcile, or at minimum annotate in both files, the xlsx-vs-`.tex` category count
   mismatch.
4. Push this session's commits (`ebf8807` and the three restructuring commits before it)
   to `origin/main` — as of this file, nothing from this repo's local history has reached
   the remote yet.
5. *(Carried over from the restructuring session, still open)* Fix the lower-arch
   Universal→FDI mapping bug in `configs/dataset_config.yaml`.
