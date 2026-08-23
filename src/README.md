# `src/` — the pipeline library

**Last verified: 22 August 2026.** Importable modules that implement pipeline stages. The
runnable entry points live in `scripts/`; these are the pieces they call. Everything here is
covered by `tests/` (46 tests, all passing).

## Modules, by pipeline stage

| Module | Stage | What it does | Status |
|---|---|---|---|
| `orientation.py` | 1 (input) | **The detector's input-orientation contract.** Rotate 90° CCW for the detector, un-rotate immediately. | ✅ tested |
| `utils/fdi_converter.py` | 2 | Universal ↔ FDI lookup *table* (32 permanent teeth). Not positional logic. | ✅ tested, bug fixed `f8b31f8` |
| `fdi_assignment.py` | 2 | **Positional FDI assignment** — given N unlabelled boxes, which tooth is each? | ⚠️ **works but is not accurate enough — see below** |
| `crop_generator.py` | 3/4 | Expanded-bbox geometry, ±15% jitter, mask-aware cropping (R2). | ✅ tested; mask-aware path **unwired** (needs R1 masks) |
| `label_assigner.py` | 4 (training) | Pixel-overlap-ratio labelling for bone-loss crops. **Not** inference numbering. | ✅ tested |
| `data_loader.py` | — | Tufts expert/bbox/mask JSON parsing and joining. | ✅ tested |
| `utils/constants.py` | — | ImageNet normalisation, crop size, Tufts dimensions, deciduous IDs. | — |
| `utils/visualization.py` | — | Plotting helpers. | — |

## Two things to read before using any of this

### 1. `orientation.py` is not optional

The frozen detector was trained on Tufts' portrait-space annotations — *sideways* panoramics.
DENTEX, Ningxia and the clinic data all ship upright. Measured against ground truth:

| Detector input | Recall | End-to-end FDI |
|---|---|---|
| upright, as shipped | 7.5% | **0.0%** |
| 90° CW | 73.7% | 21.8% |
| **90° CCW (correct)** | 71.5% | **26.1%** |

Direction confirmed by comparing all 1,000 Tufts `Radiographs/` ↔ `Radiographs_rotated/`
pairs: **1000/1000 counter-clockwise, 0/1000 clockwise**. It was recorded as clockwise until
22 Aug 2026 — a visual check cannot separate the two, because they differ by 180° and a
flipped dental arch still looks like a dental arch.

**Call `orientation.detect_upright(model, img)`.** It rotates, predicts, and un-rotates as one
operation, so the pair cannot be separated by accident — which is exactly the failure that
produced a 5.9% quadrant score (worse than guessing) when rotated boxes reached Stage 2.

### 2. `fdi_assignment.py` is measured, and it is not good enough

Validated against 1,534 FDI-labelled teeth in `DENTEX/disease/`
(`scripts/eval/validate_fdi_assignment.py`):

| Metric | Value |
|---|---|
| Quadrant correct | **93.0%** ✅ |
| **FDI exact, end-to-end** | **28.0%** ❌ |

Quadrant assignment works — the jaw split and the image-left/patient-right convention are
sound, the latter derived from the 1,600 GT annotations rather than assumed. **The position
digit is what fails**, and it has a measured ceiling: even with a *complete* 8-tooth quadrant
it reaches only 68.7%, because eight detected teeth are not positions 1–8 — they are eight
teeth that survived extraction. Rank-order numbering cannot tell an absent tooth from a
compressed arch.

So this module is a **working interface with an inadequate implementation**. It returns
`fdi`, `quadrant`, `position`, `confidence` and `flags` per tooth, and flags every failure
mode rather than assigning silently through it (`suspected_gap_before`, `position_overflow`,
`off_arch`, `sparse_quadrant`; duplicate codes impossible by construction). Downstream code
can be written against that contract now and the implementation swapped for a learned
enumeration head later. Full analysis: `docs/results/RESULTS_LOG.md` 2026-08-22c/d/f.

## Conventions

- Coordinates are **upright-frame pixels** everywhere except inside `orientation.py`.
- FDI quadrants: 1 upper-right, 2 upper-left, 3 lower-left, 4 lower-right — **patient** sides,
  so quadrants 1 and 4 appear on the **image left**.
- Crop geometry differs by branch on purpose: caries uses the raw bbox with **no expansion**,
  bone loss uses 1.5×W / 2.0×H (`PAPER_MATERIAL.md` §6.1).
