# 2026-08-27 — R1: a void run, two data defects, and a partial result

## Session goal

Run R1 (the YOLOv11l-seg retrain) on rented GPU. It ran twice: the first result was withdrawn
after the training data turned out to be corrupt, and the second produced a documented partial
result.

## What was done

### 1. Ran R1, then found the result was void

The first run (26 Aug, instance 482754) completed cleanly — 90 epochs, early-stopped, healthy
GPU, every hyperparameter matching the pre-registration. Final val mAP@0.5 was **0.258**
against the canonical bbox detector's **0.834** on the same split. A ~0.58 gap is far too large
for a bbox→mask change, so I treated it as a defect to explain rather than a number to report.

Investigating found **two independent data defects**, both required to produce the failure:

| # | Defect | How established |
|---|---|---|
| 1 | `teeth_polygon.json` stores points as `[y, x]`; `teeth_bbox.json` uses `[x1,y1,x2,y2]`. The seg converter inherited the bbox converter's "no transform" assumption. | Matched **6,006 title-paired objects** across both files against 5 candidate transforms. Transpose: **2.06 px** median centre-distance. Identity 442, CCW 289, CW 176, anti-transpose 391. |
| 2 | This machine's `Radiographs_rotated/` is **180° out** — mtime 20 Aug, predating the 22 Aug rotation-direction fix in `rotate_tufts_radiographs.py`. | Annotation-brightness test (teeth are radio-dense, so aligned annotations sit on brighter pixels): **0.967 → 1.056** after rotating 180°. |

Fixing either alone still yields garbage — that is why the earlier T0.6 §3.5 spot-check
(7 images, 20–21 Aug) passed while both defects were live.

### 2. Fixed and verified, entirely on CPU, before spending anything further

- **`scripts/yolo/fix_tufts_orientation.py`** (new) — corrects the 180°, and **refuses to run
  on an already-aligned source** so it can never silently break a correct dataset on the macOS
  machine. Writes to a new directory; the original is untouched (rule 3).
- **`convert_tufts_to_yolo_seg.py`** — one-line `[y,x]`→`(x,y)` swap, with the full measurement
  table in the comment so the next reader does not have to re-derive it.
- **Verification against `teeth_bbox.json`** — the ground truth the 0.7824 detector was trained
  on, over 3,225 train instances:

  | dataset | median IoU | agreement @ IoU≥0.5 |
  |---|---|---|
  | broken (used by the withdrawn run) | **0.000** | **1.6 %** |
  | `dataset_seg_v2` | **0.837** | **99.4 %** |

  Corroborated by brightness-inside-built-labels (0.987 → 1.072) and visual overlay on dense,
  sparse and restored arches. Instance counts unchanged at 26,005 — the fix moves coordinates,
  it does not add or drop objects.
- **Local CPU smoke-train** on a 12-image subset: 0 corrupt labels, 165 instances over 6 val
  images (~27.5/image, matching expected density), 3 epochs, no crash.

### 3. Re-ran R1 (instance 482810) — partial result

135 epochs, early stop, best epoch 105, 47 min. Held-out test touched **exactly once**, after
checkpoint selection on val:

| | P | R | mAP@0.5 | bar | verdict |
|---|---|---|---|---|---|
| **Box** | 0.7666 | 0.7751 | **0.8100** | ≥0.75 | **PASS** |
| **Mask** | 0.6270 | 0.6339 | **0.6383** | ≥0.65 | **FAIL** (−0.0117) |

Bar not moved. Bbox detector stays canonical; R2 stays unwired. **Box detection nonetheless
improved +2.76 points over the bbox detector (0.8100 vs 0.7824)** on the same split.

Documented in `RESULTS_LOG.md` 2026-08-27a/b, `model_metrics.md`,
`models/11_yolo_seg_tufts_r1/run_summary.txt`, `transfer.md` §1a.

## Decisions made

- **Withdrew the first run rather than reporting it.** Its numbers were real outputs of a real
  process, but the process was measuring against corrupt ground truth. Reporting it, even
  caveated, would have put a meaningless number into the record.
- **Did not touch the test set on the void run.** As soon as the result looked wrong I stopped
  and investigated instead of evaluating. That preserved T0.6 §2's one-shot test discipline —
  had I "just checked" the test split, R1 would have been unrepeatable without an asterisk.
- **Did not move the mask bar.** 0.6383 vs 0.65 is a 1.2-point miss and it would have been easy
  to argue the floor was arbitrary (it was — §2 says so explicitly). That is exactly why it
  could not be adjusted after seeing the number.
- **Did not adopt the seg model on the strength of the box gain either.** +2.76 points is a
  real result, but §2's bar was written to govern a *mask-driven* replacement. Reinterpreting
  it post-hoc to admit a box-driven one is the same failure mode as lowering the bar. Flagged
  as an open decision instead.
- **Rebuilt into `dataset_seg_v2` rather than overwriting `dataset_seg`.** The broken dataset is
  the evidence for the withdrawn run (rule 3).
- **Paused the GPU the moment the anomaly surfaced**, before any investigation, then destroyed
  it once artifacts were down and checksum-verified.

## Open questions

- **The macOS machine's `dataset_seg/` and `Radiographs_rotated/` are very likely affected by
  the same two defects.** Its `Radiographs_rotated/` may be correct (the 22 Aug fix was made
  there), but defect 1 is machine-independent — it is in the converter — so **anything derived
  from its polygon data is suspect.** `fix_tufts_orientation.py --verify` and the IoU check
  will settle it in minutes. Not checkable from here.
- **T0.6 §3.5's "verified end-to-end against real data" claim is not reliable** and should be
  annotated. A 7-image visual spot-check passed with both defects live.
- **Adopt the seg detector for its +2.76-point box gain, or not?** Open, deliberately.
- **Chase the 1.2-point mask gap?** Only with a fresh pre-registration first. Untuned levers:
  `mask_ratio` (4) and `overlap_mask` (True) were inherited defaults; the
  largest-fragment-per-object heuristic caps achievable mask quality by discarding smaller
  fragments of multi-fragment teeth.

## Next steps

1. **Re-verify the macOS machine** for both defects — highest priority, cheap, and it
   determines whether other Tufts-derived results are affected.
2. **Annotate `T0.6` §3.5** to record that its verification claim did not catch these.
3. **Decide on adoption** of the seg detector (box gain vs missed mask bar).
4. If adopted, **re-measure Stage-2 end-to-end** — detector recall changing moves the ceiling,
   and that must be measured, not assumed.
5. Unchanged zero-compute items: T0.5, tag the bone-loss weights, `docker build`, the Tufts
   Drive permissions fix, IRB paperwork.

## Cost

₹249.19 of ₹900 across both runs (₹130.38 for the successful one). Balance ₹650.81, nothing
left running.
