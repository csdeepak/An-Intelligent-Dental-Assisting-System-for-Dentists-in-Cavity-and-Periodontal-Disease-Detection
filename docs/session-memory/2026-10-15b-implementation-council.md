# 2026-10-15b — Implementation council: is each stage's code sound, and what to fix or improve

**Session goal:** the user asked again whether all six stages are publishable, this time scoped to
the implementation — fixes, issues and improvements — with published practice for each, and paper
changes only noted in a file (`docs/paper/paper_change_notes_2026-10-15.md`).

Same worktree, HEAD `da67b4b` (= origin/main). Nothing was changed in code, models or the paper.

## What was done

- Checks at `da67b4b`: pytest 205, invariants 12 (two in part on the Mac), 214 claims.
- Implementation facts gathered by the chair (devices, tests, silent paths, input handling, pins).
- Literature by WebSearch — Firecrawl again had no tools in the session: ML Test Score (Breck et
  al. 2017), detector calibration with position and scale (Küppers et al., CVPRW 2020), heuristic
  numbering post-processing (Karaoglu et al. 2023; Tuzoff et al. 2019), OOD/invalid-input screening
  in medical imaging (e.g. DIsoN 2025), pickle vs safetensors loading.
- Council: three `Plan` seats — MLOps reliability (Opus), per-stage modelling (Sonnet),
  robustness red team (Opus); read-only. All reported. The chair verified: ultralytics uses MPS
  only when named (`torch_utils.py:290-322`), so on the Mac both YOLO models ran on CPU while the
  classifiers ran on MPS; a NaN FDI confidence passes `< 0.30` (`run_inference.py:498`);
  `json.dumps` allows NaN (`:826`); the Dockerfile installs `requirements.txt` ranges
  (`Dockerfile:68-69`); `verify_invariants.py:168` unpickles with `weights_only=False`; the app
  writes every upload's overlay to `outputs/_app_overlays/` (`app.py:109`); and **a DENTEX
  image-level test split with 84 deep-caries annotations exists** (`data/dentex/splits_v2.json`,
  test 107 images) — the 15 Oct manuscript sentence and the report text saying none exists are
  wrong (paper notes item 1).
- Paper notes saved: `docs/paper/paper_change_notes_2026-10-15.md` (15 items).

## Verdict per stage (implementation)

| Stage | Verdict | Why |
|---|---|---|
| Data | sound, with fixes | Split, leakage and class-order invariants; eval loops skip unreadable images silently |
| 1 Detector | sound, with fixes | Hash-checked before load; no input guard; device implicit; always rotates 90° CCW |
| 2 Numbering | sound, ceiling | Hungarian correct; Lever C null; the 0.30 gate weak under shift |
| 3a Lesion detector | sound, with fixes | Mapping tested; no calibration or abstention; unmapped lesions not counted |
| 3b Caries severity | code sound, evidence weak | Validated on 133 crops; a held-out split exists and is unused |
| 4a | sound, with fixes | Crop-parity test skips on a fresh clone |
| 4b | sound | Withheld by default, enforced by an invariant |
| 5–6 | sound, with fixes | No end-to-end test; no device/version provenance; NaN paths; app hygiene |

## Fix list — before 20 Oct, no change to any output on valid inputs (ranked)

1. **Input guard, warn only** — aspect outside the training band, H > W, non-8-bit source,
   oversized image; an additive report field and an app warning. Basis: OOD-screening practice;
   UFBA 44.5% square vs 77.2% widened. ~2 h.
2. **End-to-end test** — `load_models` + `run_pipeline` on CPU against a committed golden report
   (exact codes and findings, boxes ±2 px), plus stub-model edge cases (0, 1, 33 boxes; NaN).
   Needs a fixture image whose licence allows committing it — check first. ~3 h. Basis: ML Test Score.
3. **Silent paths** — count unreadable images and raise unless allowed
   (`lesion_localization.py:274`, `c1_vlm_baseline.py:208`); narrow `src/classifiers.py:197` to
   `FileNotFoundError`; count lesion boxes that map to no tooth. ~1.5 h.
4. **Pins everywhere** — one `load_yolo_pinned()` for the eval scripts' direct `YOLO()` loads;
   `weights_only=True` at `verify_invariants.py:168` if the bundle allows. ~1 h.
5. **Provenance** — record each component's device, torch/ultralytics/numpy versions and the git
   commit in the report (additive, schema 1.6). Do not force a device: that changes numerics. ~1.5 h.
6. **NaN guards** — `np.isfinite` asserts in `_probs` and the head scores; `not (conf >= T)` at
   `run_inference.py:498`; `allow_nan=False`. ~0.5 h.
7. **App hygiene** — overlay encoded in memory instead of written to disk (privacy); clear a cached
   load error; correct the stale Drive messages (`app.py:43,64`); guard a `None` recall
   (`app.py:154`); a lock around `run_pipeline` for concurrent sessions. ~1.5 h.
8. **Docker from the lock** — install `requirements-lock.txt` (minus jupyter), pin the Python
   patch version, `load_models(device="cpu")` at build time; build and test on Windows. ~1 h.
9. **Report text** — correct `CARIES_SEVERITY_NOT_EVALUATED` (a held-out split exists, the head was
   never evaluated on it). Text only. ~0.2 h.
10. `requirements.txt`: `ultralytics>=8.3,<9` (YOLO11 floor). ~0.2 h.

## After 20 Oct, or before it with a pre-registration and the decision owner's go

- **Stage 3b: retrain on `splits_v2` train, test once on its 107 test images** — the first held-out
  severity figure. Small ResNet18 job; MPS would do, as for Stage 4b.
- Aspect-restoring front end, validated by synthetically squashing held-out images (UFBA's true
  aspect is unverified).
- Assessability under shift: temperature scaling checked on Tufts and UFBA; an image-level
  declined-fraction flag (Ovadia et al. 2019).
- Lesion-detector calibration with box position and scale (Küppers et al. 2020), fitted and tested
  on halves of CariesXrays validation.
- Two more seeds of the numbering head (cheapest multi-seed estimate; Bouthillier et al. 2021).
- A reject option for false-positive boxes (621 Tufts boxes on no labelled tooth).
- Explicit YOLO device and a CPU/MPS parity check; safetensors or torch ≥ 2.6 for safe loading.

## Decisions made

- **Nothing applied.** The user asked to check; the fix list waits for a go.
- **Paper notes kept out of the manuscript**, as asked, including the correction of my own 15 Oct
  Stage-3b sentence.
- **Seat figures not re-verified are marked so** (the abstention counts and the Stage-2 ECE).

## Open questions

- Whether a DENTEX or other OPG may be committed as a golden-test fixture (licence).
- Whether the Stage-3b retrain on `splits_v2` is wanted before the 20 Oct stop.

## Next steps

1. The user picks which fixes to apply (1–10 need no new measurement).
2. Paper notes go into the cut or the 15-page text with the usual checks.
