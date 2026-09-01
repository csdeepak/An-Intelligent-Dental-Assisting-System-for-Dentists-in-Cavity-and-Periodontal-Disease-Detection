# 2026-09-01b — §8.25 into the manuscript, a DOI audit, Lever 1 built (and caught void once), GPU rented then aborted

Continues the same calendar day as `2026-09-01-cariesxrays-sixth-cohort.md`, which ended with the
CariesXrays result folded into `PAPER_MATERIAL.md` §8.25. This file covers everything after that:
getting §8.25 into `main.tex`, a citation-integrity audit, and the first execution attempt on the
score-improvement track.

## Session goal

Turn the 1 Sep decisions into moving parts: fold the sixth-cohort result into the LaTeX
manuscript, set up cloud GPU access, and pre-register + build + run **Lever 1** (the multi-corpus
detector retrain). Standing constraint from the user: *"Before Training always check logic which
follows standard ML Principles and rules"* and *"cross-verify facts 2–3 times, never hallucinate."*

## What was done

**§8.25 folded into `paper/main.tex`** (`RESULTS_LOG.md` 2026-09-01c). New corpus-table row +
footnote c for CariesXrays; a new `\label{tab:cohorts}` three-cohort comparison (DENTEX +4.6,
Ningxia −0.9, CariesXrays +25.2 [+23.2, +27.3]); abstract and external-validation prose updated
("six independent cohorts", "four hospitals and a second public benchmark"). `chen2024cariesxrays`
added to `source.bib`. One transcription error self-caught by `verify_paper_numbers.py`: I wrote
the constant match rate as 0.207; the artefact is 0.2065 → 0.206. Fixed to the artefact.
`verify_paper_numbers.py` now asserts **90** claims (was 82). **Not compile-verified — no LaTeX
toolchain on this Mac.**

**An 8th citation error found and fixed** (`RESULTS_LOG.md` 2026-09-01c). `chen2024cariesxrays`
initially pointed at DOI `...30197` — an unrelated AAAI fairness paper. The user supplied the
GitHub link; cross-checking against AAAI OJS / ACM DL / DBLP gave the correct `...30196`. The
28 Aug `audit_citations.py` pass missed it because that script makes no network call.

**Full DOI audit against the registry** (`RESULTS_LOG.md` 2026-09-01d, `outputs/citation_audit/FINDINGS.md`).
New script `scripts/verify_citations_crossref.py` dereferences every DOI in `source.bib` via
doi.org content negotiation + `doi.org/doiRA/` agency lookup (the first version was Crossref-only
and threw 16 false failures — arXiv DOIs are registered with DataCite; self-caught by being
suspicious of a 43% failure rate). Result: **of 63 checkable DOIs, 22 are broken** — 11 resolve to
a demonstrably different paper (e.g. `karamuftuo2025panoramic` → *Foundations of Pediatric
Lifestyle Medicine*), 11 are registered with no agency. 19 further entries carry no DOI. This does
not prove fabrication — a real paper can carry a mistyped ID — but **every one needs a manual title
lookup before submission.** `scripts/audit_citations.py` also had a hardcoded Windows path
(`C:\Users\csdee\...`) — fixed to `Path(__file__).resolve().parents[1]`.

**GPU access set up on the Mac.** The user ran `jl setup --token …` themselves (**I never saw or
handled the token**). `jl` CLI 0.2.17 confirmed working; this machine's SSH key registered as
`macos-m4pro`; live JarvisLabs pricing recorded in `docs/research/GPU_SETUP.md` §0 (A100-40GB
₹84.24/hr, A100-80GB ₹140.94, A30 ₹38.88; the Windows Unicode-crash note does not apply to macOS).

**Lever 1 pre-registered** (`outputs/detector_multicorpus/PRE_REGISTRATION.md` + a two-arm
amendment). Primary: FDI exact end-to-end on the 164 leak-free images, paired cluster bootstrap
over images (10,000 resamples, seed 42) vs a **same-day control**; succeeds iff the 95% CI excludes
zero. Guard: Tufts frozen test box mAP@0.5 ≥ 0.75. Adoption needs both. Two arms so the effect is
attributable: **Control B** = Tufts-only `detect` (isolates the seg→detect head change, since
DENTEX ships no polygons), **Arm** = Tufts + DENTEX `detect` (isolates the data). Same-day control
measured: recall 0.7083, of-detected 0.8250, **end-to-end 0.5844** — reproduces the 27 Aug
published 0.5833 to within noise.

**`src/orientation.py` gained `rot_box` / `rot_boxes`** — the inverse of the existing `unrot_box`,
needed to rotate DENTEX's upright boxes *into* the detector's portrait frame. 37 property tests
(`tests/test_orientation_roundtrip.py`) assert `unrot_box(rot_box(b)) == b` exactly across four
frame sizes and edge cases. Suite 122 → **159**.

**Lever 1 dataset built — and its first build was VOID, caught before renting** (`RESULTS_LOG.md`
2026-09-01e/f). A pre-training GT-aspect check showed Tufts boxes 90° off the dentition: the build
had sourced Tufts from `data/tufts/dataset_seg/`, which is the **withdrawn pre-fix corpus from the
void 26 Aug R1 run**; the corrected `dataset_seg_v2` was never built on this machine. Rebuilt from
`_repo_archive/datasets_workspace/Segmentation/teeth_bbox.json` + `Radiographs_rotated/` (the
annotation the canonical 0.7824 detector trained on). The rebuild now **reproduces the frozen
detector's val/test box counts exactly (3,794 / 3,924)** and aborts if it does not; DENTEX boxes
re-scored against source COCO at median IoU 1.0000; MD5 leakage guard vs the 164 eval images.
Final: train 1,334 img / 36,316 boxes, val 150 / 3,794, test 150 / 3,924. `data/detector_multicorpus/`,
816 MB, gitignored.

**GPU rented, then aborted mid-upload** (`RESULTS_LOG.md` 2026-09-01g). `jl create --gpu A100`
returned "not available" (both cards), so an **A30 24 GB** was used. `jl upload` of the 3,268-file
dataset ran as a slow rsync (~19 MB/min) and nested the tree one level deep. **The user terminated
the instance before the upload finished — ₹21.45 spent, nothing trained.** Balance
₹1,105.99 → **₹1,084.54**, nothing running.

**Documentation sweep (this session's tail).** `transfer.md` rewritten (head block, §1, §3 split
into Track A / Track B, §6, §8); `README.md`, `tests/README.md`, `src/README.md`,
`scripts/README.md`, `scripts/eval/README.md`, `scripts/yolo/README.md`, `scripts/dentex/README.md`,
`data/README.md`, `docs/README.md` updated for the 159 tests, 90 paper numbers, the CariesXrays
cohort, the DOI blocker, and the Lever 1 scripts/dataset.

## Decisions made

- **Two arms, not one.** DENTEX has no polygons, so Lever 1 is necessarily a `detect` run while
  the current default is `-seg`. Without Control B, an end-to-end delta could be the head change
  rather than the data. `Arm − Control B` isolates the data; `Arm − Control A` (the frozen seg
  detector) is the acceptance number.
- **Rebuild Tufts, don't transpose it.** The void corpus's centroids cluster in a sub-region;
  x/y transpose does not repair that. Only re-deriving from `teeth_bbox.json` does, and exact
  reproduction of two independent integers (3,794 / 3,924) is the proof, not an aspect heuristic.
- **Canonical-count gate over the aspect-ratio heuristic.** The heuristic is what *caught* the
  void build; the *gate* that now blocks it is exact integer reproduction.
- **DOI fixes deferred, by explicit user instruction** ("Save it and we will do it after"). The
  audit output travels with the repo as a submission blocker.
- **Nothing on the score track was adopted** — no model trained. The pre-registration and the
  same-day control are in place so the next attempt is a clean execution.
- **The lesson, logged twice today:** *a gate that only checks the half you already suspect is not
  a gate.* The build script's own docstring had asserted "the only new geometry risk is the DENTEX
  side" — that assumption was the bug. Twin of the DOI lesson (an offline structural check is not
  a check that the DOI resolves).

## Open questions

- **Does `dataset_seg_v2` need rebuilding on this machine?** `dataset_seg/` is void and anything
  reading it inherits the defect. Lever 1 no longer touches it, but a future seg job would.
- **`validate_fdi_assignment.py --head-weights` still defaults to head v1.0** while the pipeline
  default is v2.0 — a live trap for the next re-run. Pass `models/10_.../enumeration_head_best.pth`
  explicitly. (Caught and worked around once already this session.)
- **The AAAI CariesXrays paper's FPCL baselines are still unread.** Lever 2 cannot be scoped, and
  no number from that paper may be quoted, until they are.
- **`main.tex` is unverified since 28 Aug** — §8.25 + the cohort table were added blind. Needs a
  compile on a machine with LaTeX.
- **22 broken DOIs + 19 DOI-less entries** — manual, per-entry, not yet started.

## Next steps

1. **Re-tar `data/detector_multicorpus/` and upload one file**, then train Control B then Arm on
   an A30 (or A100 if available), ~150 epochs each, batch 32, imgsz 1024, seed 42, ~₹210 total.
   Re-run the geometry gate *on the rented box* before launching.
2. Score both arms against the same-day control (0.5844) per the pre-registration; check the
   guard (Tufts test box mAP@0.5 ≥ 0.75).
3. Compile `main.tex` somewhere with LaTeX; re-measure page count against ISBI's 4.
4. Start the manual DOI fixes (`outputs/citation_audit/FINDINGS.md`).
5. Lever 2 (caries lesion detector on CariesXrays) — only after reading the AAAI baselines, with
   its own pre-registration.
6. Unchanged critical path: venue-length cut, the four compliance blockers, uploading
   `models/11_yolo_seg_tufts_r1/best.pt` to Drive.
