# 2026-09-04b — Ningxia scored, Sec 6 met, B-pooled adopted as Stage 3

**Session goal:** continuation of `2026-09-04a` (same day, same session). Score the third
pre-registered cohort (Ningxia) once it became available, apply the frozen Sec 6 acceptance
rule for real, and — since it passed — carry out the adoption the rule itself calls for.

## What was done

### Ningxia located and scored
The user pointed to `D:\nangxia_dataset` — already in the exact
`segmentation/{category}/{split}/{img,mask}` layout `ningxia_external.py` expects, no copy
needed (explicitly asked not to, limited C: space). Ran all 4 required arms (pipeline,
constant-molars, B-single lesion-detector, B-pooled lesion-detector) on the full `dental_caries`
category, 337 images / 1,013 lesions across 4 hospital splits — matches the pre-registered count
exactly. `lever_b_bootstrap.py` extended to fold Ningxia in as a third cohort: a third distinct
`per_image` key-naming scheme, and a real latent bug avoided — Ningxia filenames repeat across
splits (`test1/1.png` and `test2/1.png` are both `"1.png"`), so the pairing key was built as
`category/split/image`, not `image` alone, or two different hospitals' rows would have silently
collapsed onto each other in the paired bootstrap.

**Result:** B-single loses Ningxia too (24.0% vs. gate 40.8% / constant 39.9%) — same
domain-transfer failure as DENTEX. **B-pooled wins Ningxia decisively** (50.0% [46.3,53.9],
both deltas CI-excluding-zero) — not a tie like its own DENTEX result. **Sec 6: 2 of 3 cohorts
pass (CariesXrays, Ningxia) — rule met.**

### Adoption
The pre-registration's own Sec 6 text says what happens when the rule is met: "wire the lesion
detector in as the Stage-3 caries path... pipeline Stage 3 updated." Did that:

- **Refactored the lesion→tooth mapping out of eval code and into production code.**
  `lesion_preds_to_tooth_idx` and the raw-detector call moved from
  `scripts/eval/ningxia_external.py` to `src/classifiers.py` (now `run_lesion_detector_raw`),
  because `src.classifiers.run_caries_lesion_detector` (new) depends on them and production
  code should not import from an eval-only script. The three eval scripts now import from
  `src.classifiers` instead. Regression-checked: reproduces the pre-refactor smoke-test numbers
  byte-for-byte.
- **New Stage-3 function**, `run_caries_lesion_detector`, matches `run_caries`'s exact output
  shape (`finding`/`gate_confidence`/`severity`/`severity_confidence`/`flags`) so nothing
  downstream (report schema, `app.py`) needs to change to consume either path. Runs the lesion
  detector once on the whole image (not per-crop — it's a detector, not a classifier), maps
  predictions to teeth via argmax containment, then reuses the EXISTING severity classifier on
  flagged teeth only — severity was never part of what Lever B tested or replaced.
- **`run_inference.py`**: added `DEF_CARIES_LESION_MODEL`, `--caries-method
  {lesion-detector,gate}` (default `lesion-detector`), `--caries-lesion-conf` (frozen 0.25).
  `load_models()` loads both mechanisms unconditionally, same pattern as every other stage. The
  gate is fully retained and functional via `--caries-method gate` — every pre-4-Sep number
  stays reproducible on it, nothing was deleted.
- Renamed the report schema's `limitations.caries_gate_precision` key to
  `caries_method_caveat` (content now depends on which method actually ran — the old text would
  have been actively misleading under the new default). Updated `app.py`'s one reference.
  `gate_confidence` on a lesion-detector report is a raw detection score, not a softmax
  probability over two classes the way it was for the gate; flagged
  (`gate_confidence_is_detection_not_softmax`) so it's never misread as the old field's meaning.
- **End-to-end tested**, not just unit-tested: ran `run_inference.py` on a real image under both
  `--caries-method` values, inspected the actual JSON output. **159/159 tests pass**,
  `verify_invariants.py` all-hold.

### Documentation
- `RESULTS_LOG.md` — new entry (2026-09-04c) with the full Ningxia numbers, the complete 3-cohort
  Sec 6 table, and the adoption decision.
- `model_metrics.md` — Stage 3 restructured (current default = lesion detector, gate retained
  below it, mirroring how Stage 1 already presents "current default" vs. "superseded"). Pipeline
  parameter counts **recomputed, not estimated**: the lesion detector is 25.3 M params vs. the
  gate's 11.2 M (`ultralytics.YOLO(...).model.parameters()`, summed `numel()`, same method the
  original 83.6 M figure used) — caries-path total moves 61.2 M → **75.3 M**, whole-pipeline
  83.6 M → **97.7 M**.
- `PAPER_MATERIAL.md` — new §8.26 documenting the resolution, explicitly NOT rewriting
  §8.22/§8.24/§8.25 (those diagnoses remain true of the retained gate; §8.26 cross-references
  rather than overwrites). New §9 checklist item: fold §8.26 into `main.tex`, re-check every
  "61.2 M"/"550×" occurrence there against the new counts.

## Decisions made

- **Adopt on the rule as written, not on a judgment call.** The rule was frozen before any of
  these numbers existed (`ef3f453`) specifically so this moment would not require one. 2 of 3
  passed; adopted.
- **DENTEX's tie does not count as a pass, and is not reported as one anywhere** (RESULTS_LOG,
  model_metrics.md, PAPER_MATERIAL.md, and the live report's own limitations text all say "tie,"
  not "win" or "solved"). *Reason:* the pre-registered condition is "beats," CI excluding zero;
  a tie is a real, positive result (recovered from a decisive loss) but a different claim, and
  conflating the two is exactly the kind of overclaim this project's whole methodology exists to
  avoid.
- **Retain the gate rather than delete it.** *Reason:* `CLAUDE.md` rule 3 (never delete research
  artifacts) plus every pre-4-Sep caries number in this project's history was measured on it —
  deleting it would make those numbers unreproducible, not just historical.
- **Move the shared primitive to `src/classifiers.py` rather than leave it in the eval script.**
  *Reason:* once `run_inference.py` (production) depends on it, having production import from
  `scripts/eval/*` (research/eval-only) is a layering violation — eval code should depend on
  production primitives, never the reverse.
- **Recompute the parameter counts rather than reuse the old figure with a footnote.**
  *Reason:* the old "61.2 M caries path" was itself a correction of a previously-wrong,
  propagated number (`RESULTS_LOG` 2026-08-28) — the exact failure mode this project has been
  burned by twice. Recomputing with the same method used the first time avoids repeating it a
  third time.

## Open questions

1. `main.tex` itself is untouched — §8.26 is staged in `PAPER_MATERIAL.md` but not drafted into
   the manuscript. Every "61.2 M" / "~550×" mention there needs a decision: relabel as the
   retained-gate figure, or re-quote as the new default's 75.3 M / ~444×.
2. The Docker image predates this change (and already predated the isotonic-calibration wiring
   from 27 Aug) — needs a rebuild before any demo.
3. `app.py`'s "Caries conf (cal.)" column shows "—" for every tooth under the new default (no
   calibration exists for a detection score). Not broken, just less informative than before —
   a future session could design a lesion-detector-appropriate confidence display.
4. C4 abstention curves and any other number computed from the caries branch's confidence
   distribution were not re-run against the new mechanism — explicitly out of scope this pass.

## Next steps

1. Fold §8.26 into `main.tex`; resolve every stale parameter-count mention.
2. Rebuild the Docker image before any demo.
3. Commit + push this session's work (pending).
4. Decide whether C4 / other confidence-distribution-derived numbers need a re-run for the paper,
   or whether they can stay scoped to the gate with a note.
