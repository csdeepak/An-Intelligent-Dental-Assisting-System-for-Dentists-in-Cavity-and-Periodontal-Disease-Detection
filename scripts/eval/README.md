# `scripts/eval/` — evaluation and error-propagation

Scripts that measure the pipeline rather than build or train it. This is where contribution
**C3** (system-level metrics + stage-wise error-propagation decomposition,
`MASTER_PLAN_2026H2.md` §2.3) is produced.

| Script | Measures | Status |
|---|---|---|
| `validate_fdi_assignment.py` | Stage 1 → Stage 2: does the pipeline give each tooth the right FDI number? | ✅ run for both methods |
| `analyze_stage2_ceiling.py` | Why rank-order assignment has a ceiling, and by how much the head clears it | ✅ run on `outputs/stage2_clean` |
| `ablate_head_inputs.py` | Which input carries which FDI digit — tests the architecture's stated rationale | ✅ run on the 2,729-crop val split |
| `compare_caries_gates.py` | Before/after for the caries gate, through the pipeline, same boxes and crops | ✅ 84.9% → 19.1% |
| **`verify_invariants.py`** | **Re-checks the facts the documentation depends on.** Run after changing data, swapping a checkpoint, or before trusting a number in a draft | ✅ 7/7 hold |
| **`lesion_localization.py`** | Do predicted-diseased teeth spatially overlap a real expert lesion? §4.3.4's primary EXTERNAL number for C2 (Ningxia-ready — no negatives needed) and the T1.5 XAI metric | ✅ **44.3%** on DENTEX (seg detector, 27 Aug; old detector 42.0%) |
| **`ningxia_external.py`** | **C2 external validation** — the three §4.3.4 measurements on Ningxia, stratified by centre. Metric differs by category (focal vs diffuse) | ✅ caries 22.6–43.3%, periodontitis 0.8–5.4% |
| **`crop_eval.py`** | **Crop-level** Stage-2 evaluation on a held-out manifest split — GT boxes, plain argmax, no detector in the loop. Used to compare Stage-2 heads **across corpora** (e.g. a DENTEX-trained head measured on Tufts), which `validate_fdi_assignment.py` cannot do since it always runs against `DENTEX/disease/`. Imports `ToothSet` from `scripts/dentex/train_enumeration_head.py` rather than reimplementing preprocessing. | ✅ produced the v1.0-vs-v2.0-vs-Tufts-only 2×2, `RESULTS_LOG.md` 2026-08-25j |

## `validate_fdi_assignment.py`

Runs the frozen detector plus either Stage-2 method against `DENTEX/disease/` — the only
per-tooth FDI ground truth this project has (LabelMe polygons labelled
`{id}-{Turkish name}-{FDI}`).

**`--head-weights` still defaults to Stage-2 head v1.0** (`models/08_fdi_enumeration_head/`),
not the pipeline's current default (v2.0, `models/10_fdi_head_dentex_tufts_v2/`). This is
deliberate: this script is the reproducibility harness for the historical 46.5% end-to-end
number, and changing its default would make a bare re-run silently reproduce a different
figure than every number already written into `docs/results/*.md`. Pass
`--head-weights models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` explicitly to
evaluate the currently-deployed head this way — or use `crop_eval.py` below, which is what
actually produced the v1.0-vs-v2.0 comparison.

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

A **2.0× improvement**. On teeth in complete (8-detection) quadrants — rank-order's best case —
positional tops out at **66.3%** while the head reaches **80.2%**, a **+13.9 point** margin on an
identical population (n=101); the head wins in every completeness bucket, because it does not
depend on rank order. **End-to-end is now capped by detection**, not numbering — at 67.0% recall
that is the maximum available.

> *Corrected 24 Aug 2026:* this previously read "tops out at 67.0% … the head reaches 69.4%".
> **67.0% is the detector's recall, not the ceiling**, and 69.4% is over *all* detected teeth,
> not the complete-quadrant subset — two different populations. Recompute with
> `analyze_stage2_ceiling.py`; see RESULTS_LOG 2026-08-24a.

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

Measured on the clean 164-image set, 24 Aug 2026 (both rows, identical settings):

| | FDI/detected | End-to-end | Quadrant | Duplicate codes |
|---|---|---|---|---|
| Hungarian one-to-one | **69.4%** | **46.5%** | 94.7% | **0** |
| Plain argmax | 65.1% | 43.6% | **96.8%** | **679** |

Plain argmax emits **679 anatomically impossible duplicate codes** — a mouth has at most one
tooth 16. The constraint removes **all** of them and gains **+4.3 points** of-detected /
**+2.9 end-to-end**, while *costing* **2.1 points of raw quadrant accuracy**: satisfying the
global one-to-one constraint sometimes moves a tooth across a quadrant boundary. That trade is
worth taking — a duplicate code is not a slightly-wrong answer, it is an impossible one that a
downstream report cannot render.

*(Supersedes the earlier 72.7 / 52.2 vs 70.6 / 50.7 / 1,013 figures, which were measured on the
pre-leak-fix 249-image set. The clean numbers show a **larger** benefit than the contaminated
ones did. RESULTS_LOG 2026-08-24b.)*

**Re-run this after any Stage-1 or Stage-2 change.** It is the before/after on a held-out set
that has never been tuned on. Full record: `docs/results/RESULTS_LOG.md` 2026-08-22c, 22f, 22i
and **22j (the leakage correction)**.


## `verify_invariants.py` — why it exists

Every correction in `RESULTS_LOG.md` has the same shape: **an inference that was never tested
was written down as fact, then propagated into other documents until it read as known.**

| Correction | The untested inference |
|---|---|
| 21f | checkpoints "presumably lost" → they were on Kaggle |
| 21m | filenames overlap → assumed same patient (they were different people) |
| 22d | the rotated files "look right" → rotation was the other way |
| 22j | two folders are disjoint → a **third** folder was never tested; 34% leaked |
| 24a | two numbers both read ~67% → one was recall, not the ceiling |
| 24e | a shuffle ablation → assumed it models detector noise; it does not |
| 25a | "healthy teeth NOT derivable" → derivable by MD5, just not by filename |

Every one was catchable by a cheap direct test, and each took minutes once actually attempted.
The failure was never difficulty — it was that the check felt unnecessary.

This script runs those checks. It proves the specific things the docs assert are still true of
the files on disk; it does not prove the project correct. It needs no GPU and no model
inference — `--skip-slow` drops the two MD5 corpus joins and finishes in seconds. Since
26 Aug 2026 it pins **both** Stage-2 head hashes (v1.0 and v2.0) — a model swap is only ever
an addition here, never an overwrite, so both must stay reproducible.

---

**Publication target and grading criteria:** `../../transfer.md` §5.
