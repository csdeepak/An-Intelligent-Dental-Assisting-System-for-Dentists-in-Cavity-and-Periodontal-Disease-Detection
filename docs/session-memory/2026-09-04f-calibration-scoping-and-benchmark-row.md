# 2026-09-04f — Scoping calibration to the gate variant, and the Lever 2 benchmark row

## Session goal

Two follow-ups from `2026-09-04e`: scope the calibration and selective-prediction results to the
Stage-3a gate variant, and fold the Lever 2 CariesXrays benchmark row into Related Work.

## What was done

No model trained, no evaluation re-run. Both tasks were `paper/main.tex` edits with their
documentation trail. Numeric detail in `RESULTS_LOG.md` **2026-09-04j**.

**Task (a) — calibration and abstention scoped.** §"What the constant cannot do" reported ECE
0.136 → 0.043, AP 0.550, and +14.25 pp caries abstention, all measured on the per-crop gate that
`2026-09-04h` demoted to a variant. Both figure captions now name the gate; the subsection opens
with the scoping and its consequence; the §Discussion axis list distinguishes numbering from
caries; and a new **first item in §Limitations** states that the adopted detector has no
calibrator and no coverage–accuracy curve, and that the pre-registered 0.30 threshold was located
on the gate's curve and does not transfer to a detection score.

**Task (b) — Lever 2 benchmark row.** New `\subsection{A published benchmark, and what a stock
detector reaches on it}` (`sec:benchmarkrow`) with `tab:fpcl`, in Related Work. Its stated
precondition — re-verify the FPCL table against the AAAI PDF — was done first and **found two
errors** in the 2 Sep transcription:

- **A "DINO 37.8 / 75.3 / 29.4" row that does not exist in the AAAI table.** Nothing published
  corresponds to it; the nearest row is FCOS at 35.9 / 75.6 / 29.5.
- **"~8 AP above every off-the-shelf baseline" is ~6.** The transcription had omitted
  Conditional-DETR (42.2 AP), which is their strongest baseline, so the gap was being measured
  against YOLOx at 40.5. The authors' own text gives both numbers explicitly.

A third discrepancy turned up on the dataset size: the AAAI paper says **13,778** caries
instances, the authors' GitHub README says **13,783**, and this project counts **13,784** in the
release. The 1 Sep "+1 counting-convention difference" had compared against the README, not the
paper. `main.tex` now reports our own count and names all three.

Checks after all edits: `verify_paper_numbers.py` 117/117, `audit_citations.py` 28 commands /
26 keys resolved, `pytest` 159/159, 14 pages, 0 errors, 0 undefined refs, 2 overfull hboxes
(both pre-existing).

## Decisions made

- **Scope in writing rather than re-measure.** Computing a reliability diagram and a
  coverage–accuracy curve for the lesion detector is feasible CPU work, but the 0.30 abstention
  threshold was *pre-registered against the gate's curve*. Choosing a new threshold after seeing
  the detector's curve is precisely what this paper criticises, so that work needs its own
  pre-registration and is named as follow-up rather than done quietly.
- **Reverted my own overreach.** A first draft added *Localisation* as a fifth axis to the
  Discussion's proposed-reporting list. That is the "four things vs five" thesis change reserved
  for Deepak on 04i, not a scoping edit. Backed out; the list is still four.
- **Kept DVCTNet out of the manuscript.** Its numbers come from arXiv 2508.20813 and were never
  verified. Including an unverified third-party row in the same table as freshly verified ones
  would defeat the point of verifying. It stays in `PAPER_MATERIAL.md` §8.26, marked unverified.
- **Reported our own instance count, not either of the authors'.** When a source contradicts
  itself, adopting one of its figures means silently picking a side. Nothing downstream depends
  on the published count, so reporting our measurement and naming all three costs nothing.
- **Corrected `models/14/run_summary.txt` by appending, not editing.** Same pattern as
  `models/16` yesterday: the original transcription block is left exactly as written and a dated
  `>>> CORRECTION` block below it carries the verified table. Rule 1 — never rewrite a logged
  result, even a wrong one.
- **Renumbered the Lever B section to §8.27.** Both 4 Sep sessions wrote a "§8.26".

## Open questions

- The abstract's "four things a constant cannot do" — four or five? Still Deepak's.
- **The manuscript is now 14 pages**, up from 12 before this session's work began. If the venue
  ends up being ISBI (4-page cap), the cut is materially larger than when it was scoped. The
  journal-primary decision of 2 Sep makes this fine, but the venue is still uncommitted.
- Should the detector's calibration/abstention actually be measured, or is the honest answer that
  a detection score is not the kind of quantity abstention is defined on? Not resolved; the
  Limitations item states the gap without prejudging it.
- Numbers taken from other people's papers are the one claim class with **no automated guard** —
  `verify_paper_numbers.py` asserts against our artefacts only. Worth thinking about whether
  anything cheap covers it, or whether "verify against the PDF before quoting" stays a manual
  discipline.

## Next steps

1. Deepak's call on title / thesis / the four-vs-five list, and the venue.
2. CI coverage gaps (`transfer.md` §3 item 7) — Ningxia periodontitis, detection mAP, both
   ResNet18s. Cheap CPU, no GPU, and it is the last "every number has an interval" gap.
3. `source.bib` `url` sweep + the 19 DOI-less entries.
4. Retire or mark-superseded `docs/paper/{manuscript.md,draft_spine.md}`.
5. Docker rebuild — but `docker build` has never executed on this machine, so scope it as an
   unknown rather than a task.
