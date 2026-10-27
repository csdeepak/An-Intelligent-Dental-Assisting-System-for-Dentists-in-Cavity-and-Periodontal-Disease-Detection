# 2026-10-14g — Is every stage publishable? A council, then six manuscript and two code fixes

**Session goal:** the user asked whether each stage's metrics and implementation are good enough
to publish, and what can still be fixed (`/council`); then said to apply the verified edit-only
manuscript fixes (E1–E6) and two code fixes (C1, C2), re-run the checks, and not commit.

Same session and worktree as `2026-10-14f-stage4b-retrain-result.md`, after `c3d024c` was pushed.
Record in `RESULTS_LOG` 2026-10-14e.

## What was done

- **An implementation audit first** (read-only): every code task of the 14 Oct plans (T0–T8,
  V1–V2, F1–F3, F7, W1–W2) and the manuscript rows S2–S5, S9 checked in code and text — done. Open:
  S1 the six-page cut, S6 authors and statements, S7 CLAIM 2024, S8 a referee read, F4–F6, S10,
  and the owner tasks O1–O5.
- **Council**, brief in the session scratchpad: three independent `Plan` seats — referee (Opus),
  ML-evaluation engineer (Sonnet), scope strategist (Opus) — read-only, nothing run, no Ningxia.
  All three reported. The chair checked each finding used against the repo (the abstract's gate
  headline, `main.tex` 582–589, 806, 1592; no hash check before loading; no tests of the Stage-3a
  mapping; the CariesXrays image-level split in `models/14`; the DENTEX perceptual-hash records
  in the log; `arm4c`'s 382 UFBA images).
- **C1:** `DEFAULT_SHA256` in `scripts/run_inference.py`; `load_models` refuses a default whose
  sha256 is not its pin, before unpickling it. Two tests in `tests/test_report.py`: the pins
  match the files, and a mismatched default is refused (a control without the pin let the file
  reach the unpickler). The real defaults load through it.
- **C2:** five tests in `tests/test_classifiers.py` for `lesion_preds_to_tooth_idx` and
  `run_caries_lesion_detector` — straddling lesion to the tooth holding most of it, lesions
  outside every tooth or of zero area, two lesions on one tooth, grading only flagged teeth, and
  no severity call without a detection. One test was wrong at first (my arithmetic, not the
  code) and was corrected.
- **E1–E6** in `paper/main.tex`, patched as CRLF bytes: test count; Table IV caption; the
  abstract's "had all failed"; a perceptual-hash sentence; the CariesXrays split by image (two
  places); the Ningxia cohort's role in the abstract and the fixed-site interval in
  `sec:leverb`. One new checker claim (650 DENTEX images from `models/16`'s run summary).
- **Checks:** pytest 204 passed; invariants 12 hold; 207 claims, no drift; tectonic 0 errors, 0
  undefined references, **16 pages** (the 16th holds four references); `paper/main.pdf` replaced.
- **Records:** `RESULTS_LOG` 2026-10-14e; `PAPER_MATERIAL.md` §8.41 and a §9 item;
  `SUBMISSION_TODO.md` note; `model_metrics.md` Stages 5–6 line; `transfer.md` top line, §1, §3,
  §8; `README.md` and `tests/README.md` counts.

## Decisions made

- **C1 checks the seven defaults only.** The pipeline deliberately runs unregistered weights and
  tags them by hash (`DETECTOR_PROFILES`, `CHECKPOINT_TAGS`); refusing those would break that
  design and every ablation path. A default that has been swapped or corrupted is the case the
  council named.
- **E4 is stated without numbers.** The two perceptual-hash comparisons in the log (min 37 and
  42 bits) were counted in-session and never saved; the checker can assert nothing about them.
- **Declined a confidence sweep** on DENTEX and CariesXrays validation: earlier councils refused
  threshold studies, it adds a figure a six-page paper cannot carry, and it is off the critical
  path.
- **The Stage-3b grade stays in the report** with its "not evaluated" line: the decision owner
  chose that on 14 Oct (D1); one seat proposed hiding it.
- **Not adopted:** the referee's "700/150/150 against 678/145/143" mismatch — the same split
  file less twins and box-less radiographs.
- **The abstract rewrite is left to the cut.** Building it around the shipped system changes the
  paper's lead; that belongs to the authors and the mentor, and the cut rewrites the abstract
  anyway.
- **The page went from 15 to 16** for four reference lines; not trimmed, since the cut replaces
  the length question.

## Open questions

- Whether Stage 4 appears in the six-page cut at all (council: one sentence on 4a, none on 4b).
- A fallback date for the Kaggle licence, and what the paper reports if none arrives.
- Whether abstention under shift (Tufts and UFBA coverage at τ 0.30, from saved rows) is worth a
  logged line — one seat's arithmetic suggests about 85% and 74% coverage, not recomputed here.
- Whether to freeze code now rather than on 20 Oct.

## Next steps

1. The user commits these changes (proposed at the end of the session) and decides on a push.
2. The mentor meeting (O1): venue, authors, front end, Stage 4 in the cut, what "secured" means.
3. The six-page cut (S1), abstract built around the shipped lesion detector, no "domain shift",
   no periodontal opening; then S6, S8, S7; the pdfLaTeX build on Windows.
