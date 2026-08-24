# `src/` — the pipeline library

**Last verified: 22 August 2026 (Stage 2 replaced by a learned head).** Importable modules that implement pipeline stages. The
runnable entry points live in `scripts/`; these are the pieces they call. Everything here is
covered by `tests/` (46 tests, all passing).

## Modules, by pipeline stage

| Module | Stage | What it does | Status |
|---|---|---|---|
| `orientation.py` | 1 (input) | **The detector's input-orientation contract.** Rotate 90° CCW for the detector, un-rotate immediately. | ✅ tested |
| `utils/fdi_converter.py` | 2 | Universal ↔ FDI lookup *table* (32 permanent teeth). Not positional logic. | ✅ tested, bug fixed `f8b31f8` |
| `fdi_assignment.py` | 2 | Positional (rank-order) FDI assignment | ⚠️ **SUPERSEDED** — kept as the measured baseline, not the pipeline default |
| `fdi_head_inference.py` | 2 | **The current method** — runs the learned enumeration head over detector boxes, with Hungarian one-to-one assignment | ✅ **use this** |
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

### 2. Stage 2 uses the learned head, not the positional module

Both are measured on the **same 164 leak-free `DENTEX/disease/` images** (936 teeth), same
detector, same matching rule:

| | `fdi_assignment.py` (positional) | **`fdi_head_inference.py` (head)** |
|---|---|---|
| Quadrant correct | 92.3% | **94.7%** |
| FDI exact (of detected) | 34.1% | **69.4%** |
| **FDI exact, end-to-end** | 22.9% | **46.5%** |
| Duplicate FDI codes | 0 (by construction) | **0** (via Hungarian) |

**A 2.0× improvement on both measures.** Positional assignment has a hard ceiling — it reaches
only **66.3%** even on fully-detected quadrants, because eight detected teeth are not positions
1–8, they are eight teeth that survived extraction, and rank order cannot tell those apart. On
that same population the head reaches **80.2%** — a **+13.9 point** margin (n=101) — because it
is **order-independent**: it judges each tooth on its own appearance and absolute position, so a
missing neighbour no longer shifts it. It wins in every completeness bucket.

*(Corrected 24 Aug 2026: this previously read "67.0% … margin is +2.4 points". 67.0% is the
detector's **recall**, not the ceiling, and 69.4% is over all detected teeth rather than the
complete-quadrant subset. See RESULTS_LOG 2026-08-24a.)*

**86 of the original 250 evaluation images are excluded as training duplicates** (85
byte-identical to enumeration-head training images, 1 to a detector training image). An earlier
run reported 52.2% before this was found — inflated by 5.7 points. Exclusion list:
`data/dentex/disease_leaked_images.json`, loaded automatically by the validation script.

**End-to-end is now capped by Stage 1, not Stage 2.** At 67.0% detector recall, 67.0% is the
maximum; the head captures 69.4% of it. Detector recall is the binding constraint.

Prior art: DPML (Cao et al., *ESWA* 254:124446, 2024) §3.4 argues the same design independently
— dentists identify teeth by relative position, and ML models rarely get that signal. Its
8-class formulation, justified by bilateral symmetry, sidesteps the left/right problem that FDI
cannot, so positional features are supplied to help disambiguate mirrored pairs. Horizontal flip
stays excluded from augmentation because it **inverts a quadrant label** — a fact about the
labels, independent of the model.

**Measured contribution** (`scripts/eval/ablate_head_inputs.py`): replacing the positional
features with their dataset mean costs **3.2 points of laterality** (99.5% → 96.3%) and nothing
at all on the position digit. *(This previously called them "load-bearing rather than merely
helpful"; the image alone recovers laterality at 96.3%, so that was overstated.)* Feeding
*shuffled* features costs 22.9 points, but that is a misleading worst case: a shuffle teleports
the coordinate to another tooth, often across the midline. **Realistic detector-box error costs
essentially nothing** — ±15% of box size changes FDI exact by <0.1pp, ±100% by 0.2pp, because a
tooth is only ~4.5% of image width. RESULTS_LOG 2026-08-24c, corrected by 2026-08-24e.
Full record: `docs/results/RESULTS_LOG.md` 2026-08-22i, 22j (leakage) and 22k (prior art).

## Conventions

- Coordinates are **upright-frame pixels** everywhere except inside `orientation.py`.
- The head's inference preprocessing is **verified identical** to its training preprocessing —
  200/200 predictions agree on the same teeth via both paths. If you change crop geometry,
  colour handling or the positional features in one place, change both.
- FDI quadrants: 1 upper-right, 2 upper-left, 3 lower-left, 4 lower-right — **patient** sides,
  so quadrants 1 and 4 appear on the **image left**.
- Crop geometry differs by branch on purpose: caries uses the raw bbox with **no expansion**,
  bone loss uses 1.5×W / 2.0×H (`PAPER_MATERIAL.md` §6.1).
