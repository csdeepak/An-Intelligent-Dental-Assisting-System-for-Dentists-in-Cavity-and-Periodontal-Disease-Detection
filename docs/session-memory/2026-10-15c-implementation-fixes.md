# 2026-10-15c — The implementation council's ten fixes, applied with no output changed

**Session goal:** the user said to apply implementation fixes 1–10 of
`2026-10-15b-implementation-council.md` (no output change on valid inputs), with tests; re-run every
check; log it; not commit; and ask before committing any image as a test fixture.

Same worktree, from `da67b4b`. Record in `RESULTS_LOG` 2026-10-15b.

## What was done

- **Parity baseline first:** six reports saved before any edit — DENTEX training images
  `train_0.png`, `train_1.png` and Tufts training radiograph `1.JPG`, each in the default mode and in
  gate mode with the Stage-4 grade. Two runs of one image were identical, so differences after the
  edit could only be the edit's.
- **Training-image shape measured** before fixing the input-check bounds: DENTEX aspect 1.60–2.33,
  Tufts 1.92, shorter side at least 840 px, no portrait image.
- **Fixes** (all edits as byte patches, each file keeping its line endings):
  `scripts/run_inference.py` — `check_input`, `load_yolo_pinned`, `runtime_info`, the NaN-safe
  gate, `image.warnings`, `models.runtime`, lesion counts, an in-memory `draw_overlay`,
  `allow_nan=False`, the corrected caries-severity text, schema 1.6; `src/classifiers.py` — finite
  outputs, the calibrator's `FileNotFoundError`, the unmapped-lesion count; `src/fdi_head_inference.py`
  — finite head scores; seven eval scripts through `load_yolo_pinned`, two of them no longer
  skipping unreadable images; `verify_invariants.py` — `weights_only=True`; `app.py` — the overlay
  in memory, a lock, error not cached, messages, the `None` guard; `Dockerfile` — the lock, Python
  3.12.12, a build-time load of the defaults; `requirements.txt` — `ultralytics>=8.3,<9`.
- **Tests:** `tests/test_pipeline_e2e.py` (synthetic radiograph and a Tufts golden summary,
  `tests/golden/tufts_1_cpu.json`), four report tests, two classifier tests; the schema test moved
  to 1.6.
- **Verified:** all six before/after reports identical per tooth, summary, limitation and model
  field, apart from the intended additions; pytest 213, invariants 12, claims 214; a portrait input
  warns on the CLI; the app starts headless with no exception and its changed Streamlit calls
  validate in bare mode; the pinned loader warns on an unregistered checkpoint and not on a
  registered one; every lock pin has a Linux cp312 wheel (PyPI metadata).
- **Records:** `RESULTS_LOG` 2026-10-15b; `model_metrics.md` Stages 5–6; `README.md` row 6;
  `tests/README.md`; `transfer.md` top line, §1, §8; paper notes items 16–17.

## Decisions made

- **Warn, never refuse.** Refusing an input changes what the system outputs; that is the decision
  owner's call.
- **Schema 1.6** for the additive fields, as the file's changelog does for every field added.
- **The `from ultralytics import YOLO` lines stay where they were** in the eval scripts: the import
  patches `cv2.imread` globally, and moving it would move that patch.
- **No device forced.** Forcing one would change numerics; the report records each component's
  device instead.
- **The golden fixture is a summary, not an image,** and it comes from a Tufts training
  radiograph that stays local. The test skips where the raw data is absent. Whether to commit the
  JSON is left to the user, since it is derived from licensed data.

## Open questions

- Whether to commit `tests/golden/tufts_1_cpu.json` (derived predictions, no pixels).
- Whether the Docker image builds from the lock on Windows (not built here).

## Next steps

1. The user commits; a proposed split is in the session's closing message.
2. Build and smoke-test the Docker image on Windows (`docker build`, then the build-time load).
3. The after-20-Oct list in `2026-10-15b-implementation-council.md`.
