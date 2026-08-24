# `scripts/eval/` — evaluation and error-propagation

Scripts that measure the pipeline rather than build or train it. This is where contribution
**C3** (system-level metrics + stage-wise error-propagation decomposition,
`MASTER_PLAN_2026H2.md` §2.3) is produced.

| Script | Measures | Status |
|---|---|---|
| `validate_fdi_assignment.py` | Stage 1 → Stage 2: does the pipeline give each tooth the right FDI number? | ✅ run for both methods |

## `validate_fdi_assignment.py`

Runs the frozen detector plus either Stage-2 method against `DENTEX/disease/` — the only
per-tooth FDI ground truth this project has (LabelMe polygons labelled
`{id}-{Turkish name}-{FDI}`).

```bash
python scripts/eval/validate_fdi_assignment.py --method positional   # the baseline
python scripts/eval/validate_fdi_assignment.py --method head         # the current method
python scripts/eval/validate_fdi_assignment.py --method head --no-one-to-one   # ablation
python scripts/eval/validate_fdi_assignment.py --method head --save-viz        # overlays
```

## Results — 164 leak-free images, 936 GT teeth, identical settings

| | Positional | **Head** |
|---|---|---|
| Detection recall | 67.0% | 67.0% |
| Quadrant correct (of detected) | 92.3% | **94.7%** |
| FDI exact (of detected) | 34.1% | **69.4%** |
| **FDI exact, end-to-end** | 22.9% | **46.5%** |

A **2.0× improvement**. Positional assignment tops out at **67.0%** even on fully-detected
quadrants; the head reaches 69.4% because it does not depend on rank order. **End-to-end is now
capped by detection**, not numbering — at 67.0% recall that is the maximum available.

Writes `stage2_{summary,rows,per_image}_{method}.json`, plus annotated overlays with
`--save-viz` (blue = GT numbered correctly, red = wrong or missed, orange = flagged).

## Four things that make this evaluation honest — and are easy to get wrong

- **86 images are excluded as training duplicates.** 85 are byte-identical to
  enumeration-head training images; 1 to a detector training image. The list lives in
  `data/dentex/disease_leaked_images.json` and is loaded automatically. **A first run reported
  52.2% before this was caught — an inflation of 5.7 points.** The cause is worth remembering:
  `quadrant_enumeration` and the disease *subset* (705) genuinely are disjoint patients, and
  that was verified — but `disease/` is a *third* folder sharing a third of its images. A
  verified fact about one pair was generalised to a pair never measured.
- **Check leakage against every training corpus separately.** When Ningxia arrives, test it
  against Tufts, DENTEX *and* the enumeration corpus independently. Do not infer from a
  neighbouring pair; that is exactly the mistake above.
- **GT → detection only; no precision is reported.** `disease/` annotates only teeth carrying a
  finding (~6 of ~30 per image), so an unmatched detection is usually a real tooth with no
  annotation. A precision figure here would be meaningless.
- **NMS IoU is 0.50, not the frozen run's recorded 0.70.** Chosen *a priori* on anatomy — real
  teeth do not overlap by half their area — **not** by sweeping it against this evaluation set.

## Ablation: one-to-one assignment

| | FDI/detected | End-to-end | Duplicate codes |
|---|---|---|---|
| Hungarian one-to-one | **72.7%** | **52.2%** | **0** |
| Plain argmax | 70.6% | 50.7% | **1,013** |

*(Measured on the pre-leak-fix 249-image set, so the absolute values are inflated; the
comparison between the two is unaffected and directionally valid.)* Plain argmax emits 1,013
anatomically impossible duplicate codes — a mouth has at most one tooth 16. The constraint
removes all of them and gains ~1.5 points, costing ~1.6 points of raw quadrant accuracy.

**Re-run this after any Stage-1 or Stage-2 change.** It is the before/after on a held-out set
that has never been tuned on. Full record: `docs/results/RESULTS_LOG.md` 2026-08-22c, 22f, 22i
and **22j (the leakage correction)**.
