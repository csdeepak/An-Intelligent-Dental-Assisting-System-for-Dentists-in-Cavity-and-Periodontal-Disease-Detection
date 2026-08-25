# `scripts/` — runnable entry points

Three families. The library they call is `src/`; see `src/README.md`.

| Path | Stage | See |
|---|---|---|
| `yolo/` | 1 — tooth detection (bbox + the R1 seg upgrade) | `yolo/README.md` |
| `dentex/` | 2 and 3 — the enumeration head, plus caries data + training | `dentex/README.md` |
| `eval/` | evaluation and error propagation (C3) | `eval/README.md` |
| *(top level)* | Stage 4 bone-loss dataset/training, and the full-pipeline entry point | below |

## Top-level scripts

| Script | What it does | Status |
|---|---|---|
| `build_dataset.py` | Builds the bone-loss training crops from Tufts | ✅ used |
| `train_model.py` | Trains the bone-loss ResNet18 | ✅ used |
| `run_inference.py` | **The full-pipeline entry point: OPG in → per-tooth JSON + overlay out** | ✅ **Built 24 Aug** — all six stages; see `src/classifiers.py` for Stages 3–4 |

`run_inference.py`'s `main()` now delegates to `load_models()` + `run_pipeline()` (refactored
25 Aug, verified byte-identical) so the CLI and `../app.py` (the Streamlit deployment demo,
root of the repo) share one code path — no second implementation to drift. `../Dockerfile`
builds the same app as a CPU-only container. Neither is under `scripts/`; both are listed here
because they exist entirely to expose what this directory builds. Use
`src.fdi_head_inference.assign_fdi_head`, not the superseded positional module.

## If you are running anything on a non-Tufts image

Rotate it. The frozen detector consumes **90° counter-clockwise** panoramics; DENTEX, Ningxia
and the clinic data all ship upright, and feeding them as-is gives 7.5% recall and 0% FDI
accuracy. Use `src.orientation.detect_upright`, which handles the rotate/un-rotate pair.
