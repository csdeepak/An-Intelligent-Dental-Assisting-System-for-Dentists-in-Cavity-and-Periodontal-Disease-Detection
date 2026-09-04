# 2026-09-04g — Five-item open-work pass: bibliography, figures, licences, and the last two CI gaps

## Session goal

A full scan of what was still open project-wide, filtered to what could be done without a
human decision or new GPU spend, scoped down to five items for one clean session: bibliography
hygiene, a figure-redistribution compliance check, licence recording for DENTEX and Ningxia, and
the two remaining bootstrap-CI gaps (Ningxia periodontitis, Stage-1 detector).

## What was done

Continuation of `2026-09-04{e,f}`. No model trained. Full detail and exact numbers in
`RESULTS_LOG.md` **2026-09-04k** (items 1–3) and **2026-09-04l** (items 4–5).

**1. Bibliography sweep.** Built `scripts/audit_bib_urls.py` — a publisher-aware structural
check (MDPI URLs cross-checked against the entry's own volume/issue/pages; nature.com URLs
against the DOI suffix directly), after a naive substring check produced 26 false positives.
Found and fixed **5 genuine defects**: two entries' `url` fields pointed at entirely different
Nature articles (right DOI, wrong URL); two entries had a **wrong conference name recorded** in
the bib itself, caught by author-list cross-checking against Crossref rather than trusting a
title match alone. Corrected the "19 DOI-less entries" figure carried in two docs (true count
was 12, now 3, all justified). Added 9 missing DOIs and one missing citation — the Ningxia
source paper (`li2024multicenter`) was never cited despite its own README requesting it.

**2. Figure-redistribution audit.** Three of five figure-generator scripts predate the 28 Aug
rebuild and couldn't be located, so opened and inspected all five PNGs directly instead of
tracing provenance by script. All are derived charts; none reproduces raw radiograph pixels.

**3. Licence recording.** DENTEX: CC-BY-NC-SA-4.0, compliant. Ningxia: no formal licence,
informal non-commercial request only, compliant but weaker — and its source paper was missing
from the bibliography entirely (fixed as part of item 1's DOI work, cross-referenced here).

**4. Ningxia periodontitis CI.** `ningxia_external.py` was computing per-image affected-tooth
counts and discarding them before writing the per-image record. Added the two missing fields,
re-ran, reproduced the existing published per-split numbers exactly, then bootstrapped: pooled
sensitivity 2.4% [95% CI 2.0, 2.9], n=736 images. Closed with no surprises.

**5. Stage-1 detector CI + the `split_v1` leak decision.** This is the one worth reading in
full if this area gets touched again — see "Decisions made" below and `RESULTS_LOG` 2026-09-04l
for the complete debugging trail. Three attempts at reproducing the published Box mAP@0.5 =
0.8100 from scratch failed (0.593 → 0.701 → 0.672, the last fix moving *away* from the target
despite matching the detector's own recorded config exactly), so the approach was abandoned in
favour of a different, simpler, correctly-bootstrappable statistic: box detection recall at the
deployed confidence, 69.1% [95% CI 65.5, 72.6]. This also answered the standing question of
whether the documented `590.JPG`/`591.JPG` train-test leak needed a full re-measurement: its
effect is $-0.15$ points against a $\pm$3.5-point CI half-width — negligible.

Checks after all edits: `verify_paper_numbers.py` 117 → **127** claims, all passing;
`pytest` 159/159; manuscript recompiles clean, 14 pages, 0 errors, 0 undefined refs, the same 2
pre-existing overfull hboxes as before.

## Decisions made

- **Stopped chasing the AP reproduction after the third attempt, on a specific signal, not a
  time limit.** The second fix (NMS IoU 0.5→0.7) was not a guess — it matched the detector's own
  recorded training config exactly, which is normally strong evidence a fix is correct — and it
  made the reimplementation's accuracy *worse*, not better. A config-correct change producing a
  worse result is evidence the remaining error lives in the reimplementation's own logic (COCO-
  style AP has real subtlety: interpolation convention, tie-breaking, box-vs-mask handling), not
  in any further `predict()` parameter worth guessing at. That is the point to stop iterating on
  parameters and question the approach, not the point to try a fourth variant with no new
  evidence about why the first three didn't converge.
- **Reported a different, disclosed statistic rather than force the original one.** Detection
  recall at the deployed confidence is a plain per-image ratio — the same kind of quantity as
  the paper's existing DENTEX 70.6% detection figure — and bootstraps correctly using primitives
  already proven throughout this project. It does not replace or revise the published 0.8100 AP
  figure; it answers the same underlying question (how good is this detector on this split) with
  a statistic that could actually be trusted with a CI attached. The failed AP attempt is kept in
  the artefact, clearly labelled, rather than deleted — a failed verification is itself a fact
  worth keeping, not noise to clean up.
- **Did not silently reuse the disqualified bone-loss diagnostic dataset.** A CI for the two
  bone-loss ResNet18 classifiers was in scope, but the only per-item dataset on this machine
  carries its own creator's explicit `"DIVERGENT -- do not use"` flag and a very different score
  (0.537 vs the headline 0.923) on a different, smaller subset. Using it to manufacture an
  interval would have put a real-looking number behind a disqualified measurement. Re-checked
  "the original radiographs aren't on this machine" directly (every drive letter, OneDrive)
  rather than trusting the existing note, given today's pattern of stale absence-claims (see
  Ningxia and the SDH dataset in `2026-09-04{e,f}`) — this one held up. Reported as genuinely
  blocked, not attempted.
- **Corrected the "19 DOI-less entries" figure by recounting, not by trusting the carried
  number.** It had drifted (true count was 12 even before this session's fixes) — the same class
  of staleness this project keeps re-discovering elsewhere.
- **Did not chase Xplore document-URL guesses.** When adding a DOI for `kaushik2025densenet201`,
  the first instinct was to construct an IEEE Xplore URL from the DOI's own numeric suffix — but
  an earlier check in the same session (`khuwaja2024ai`) showed DOI suffixes and Xplore document
  IDs are frequently different internal identifiers. Used the DOI resolver link instead of a
  fabricated Xplore URL.

## Open questions

- The two bone-loss ResNet18 classifiers' CI gap: closing it needs either the original Tufts
  radiographs (location unknown, not found on this machine or any checked drive) or an explicit
  decision to publish 0.923 macro-F1 without an interval, stated as such in the Limitations
  section (it currently is, via the existing "selected maximum, not reproducible" item — worth
  checking whether a fifth Limitations bullet naming the missing CI specifically is warranted,
  or whether that's redundant with the existing one).
- `docs/paper/{manuscript.md,draft_spine.md}` still describe a gate-only pipeline and carry the
  old 0.488/61.2M-era numbers — flagged repeatedly across recent sessions, never actioned.
  Worth a decision: retire, or mark superseded with a pointer to `main.tex`.

## Next steps

1. Deepak's calls, unchanged from prior sessions: venue, title/thesis, the "four things" list,
   authors/affiliations, IRB, the two live compliance items (Tufts Drive link, SDH `index.csv`
   placement).
2. If the bone-loss branch's CI gap is worth closing, locate the original Tufts radiographs
   first — nothing else unblocks it.
3. Docker rebuild — still not attempted; Docker Desktop is installed on this machine but its
   daemon was not running when checked.
