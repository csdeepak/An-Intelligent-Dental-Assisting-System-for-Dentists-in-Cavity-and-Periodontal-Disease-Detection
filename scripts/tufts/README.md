# `scripts/tufts/` — Tufts as a second FDI-numbering corpus

**Written 25 August 2026.** Until now Tufts was used for two things: training the tooth
detector (single-class, no numbering) and the bone-loss cascade. Its **per-tooth numbering
was never used by anything** — `convert_tufts_to_yolo.py` read the same annotation file and
threw the labels away (`nc: 1, names: ['tooth']`) because it was building a detector.

| Script | Status | What it does |
|---|---|---|
| `build_enumeration_crops.py` | ✅ run — 42,755 crops | FDI-labelled tooth crops from `Segmentation/teeth_bbox.json` (1,000 images, 25,201 usable permanent teeth). Reuses the frozen `split_v1` (700/150/150); 1.5× expansion; ±15% jitter on train only. Output `data/tufts/enumeration_v1/` (gitignored). |

Train the head on both corpora at once:

```bash
python scripts/dentex/train_enumeration_head.py --data data/dentex/enumeration_v1 data/tufts/enumeration_v1
```

`--data` accepts several roots; each row keeps its own resolved path and a `corpus` tag, so
the trees are never merged on disk and per-corpus counts appear in the run log. A single root
behaves exactly as before.

---

## The one thing you must not get wrong: the numbering is MIRRORED

Tufts titles look like Universal numbers (`'1'`–`'32'`), and their **within-arch ordering is
genuinely correct**. What is inverted is **which side of the patient each number denotes**.
Tufts `"1"` is the upper-**LEFT** third molar — FDI **28**, not 18.

Reading the titles as plain Universal would train the head on systematically side-swapped
labels. That is worse than not using Tufts at all: the head would learn to invert laterality,
the one thing `ToothSet` already refuses to let augmentation do ("NO horizontal flip: it would
swap left/right and invert the quadrant label").

Established three independent ways — **not** inferred from documentation, and not from any one
of these alone (RESULTS_LOG 2026-08-25h):

1. **Lead side-marker.** The radiographs carry an `L` marker on the viewer's right, i.e. the
   standard convention (patient's left on the viewer's right). Tufts `"1"` falls on the
   viewer's right → the patient's LEFT. Standard Universal `1` is the patient's upper-RIGHT.
2. **Independent model arbiter.** The Stage-2 head is trained on DENTEX (spatially verified
   FDI: Q1 mean x=0.400 vs Q2 x=0.606) and has never seen Tufts. Over **1,188** IoU≥0.5-matched
   teeth in 60 Tufts images it agreed **6.1%** read directly and **91.7%** read mirrored, with
   a clean anti-diagonal quadrant confusion matrix.
3. **Control, to prove the arbiter is not itself the mirrored component.** Same head, detector
   and matching code on 841 DENTEX teeth: **98.6% direct, 0.7% mirrored** — a clean diagonal.

The conversion lives in `src/utils/fdi_converter.tufts_title_to_fdi()` and is regression-tested
in `tests/test_fdi_converter.py`. **Never call `universal_to_fdi()` on a Tufts title directly.**

**Nothing already trained is affected.** The detector is single-class and emits no numbering;
the bone-loss models use the Tufts title only as an identifier and a deciduous flag, never
deriving laterality from it (verified: zero mentions of FDI/quadrant/universal in
`notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`).

## Two more traps in this data

- **Annotations are in PORTRAIT coordinates** (840×1615), matching `Radiographs_rotated/`, not
  the upright `Radiographs/` (1615×840). Crops here are cut from the **upright** image, because
  Stage 2 reasons about upright anatomy — rotated boxes reaching `assign_fdi` scored 5.9%
  quadrant accuracy, below the 25% of guessing (`src/orientation.py`). The inverse transform is
  CCW's, `(x, y) → (W-1-y, x)`, verified pixelwise on all 1,000 pairs. Independent confirmation:
  converted boxes have median aspect **0.371**, matching DENTEX's 0.347 and the ~0.35 documented
  in `src/crop_generator.py`. Left in portrait it would have been ~2.7.
- **Degenerate 1×1 boxes mean "tooth absent"**, not "tooth at this pixel" — 66 of them, dropped.

## Split discipline, and a leak found in `split_v1`

`split_v1.csv` is the split `tooth-detector-a100-1024-v1.0` was trained on, so it is reused
verbatim rather than re-randomised — otherwise images from the detector's *test* set would land
in the head's *train* set and quietly contaminate every end-to-end Tufts number.

Two byte-identical duplicate pairs exist inside Tufts, and one straddles the split:

| duplicate | splits | handling |
|---|---|---|
| `590.JPG` / `591.JPG` | **test / train** — a real, previously-undocumented leak in `split_v1` | keep `590` (test), drop `591` |
| `1007.JPG` / `1008.JPG` | train / train — no leak, but double-weights one image | keep `1007`, drop `1008` |

Within each group one representative is kept, preferring the most protected split
(test > val > train). **This means the existing detector trained on one of its own test
images** — a small effect (1 of 150 test images), recorded rather than quietly corrected.

Tufts is **disjoint from DENTEX**: zero overlap by MD5 *and* by perceptual hash (dHash) against
both `quadrant_enumeration` (634) and `quadrant-enumeration-disease` (705).

## Deciduous teeth are excluded

738 deciduous teeth (letters A–T) across 82 mixed-dentition images are dropped: the head's
output space is the 32 permanent codes. Their images are still used for the permanent teeth
they contain, and every row carries `mixed_dentition_image` so the choice can be ablated later
rather than silently baked in. Their handedness was *not* covered by the evidence above, which
concerns permanent teeth only — so `tufts_title_to_fdi()` returns `None` for letters rather
than guessing.

## What this is NOT

The crops are built and verified; **no model has been retrained on them.** Whether the combined
corpus actually improves the head is an open experiment, not a claim — see `transfer.md` §4.
Two things to watch when it is run:

- Teeth occupy a smaller fraction of the frame in Tufts (median normalised height **0.177** vs
  DENTEX's **0.231**), so the `cy`/`bh` positional features have different distributions across
  the two corpora. That is a genuine covariate shift feeding a feature the head consumes.
- Tufts contributes 2.0× DENTEX's training rows (35,248 vs 17,619 after jitter), so a naive
  concatenation lets it dominate the loss.
