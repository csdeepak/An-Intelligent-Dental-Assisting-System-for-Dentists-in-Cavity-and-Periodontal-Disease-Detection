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
| `run_inference.py` | **The full-pipeline entry point: OPG in → per-tooth report out** | ❌ **38-line placeholder** |

`run_inference.py` is Stages 5–6 — the project's largest gap and its central paper claim (C3).
All four trained models are on local disk and **Stage 2 is now fixed** (46.5% end-to-end, up
from 22.9% — `eval/README.md`), so this is buildable and its output is meaningful. Use
`src.fdi_head_inference.assign_fdi_head`, not the superseded positional module.

## If you are running anything on a non-Tufts image

Rotate it. The frozen detector consumes **90° counter-clockwise** panoramics; DENTEX, Ningxia
and the clinic data all ship upright, and feeding them as-is gives 7.5% recall and 0% FDI
accuracy. Use `src.orientation.detect_upright`, which handles the rotate/un-rotate pair.
