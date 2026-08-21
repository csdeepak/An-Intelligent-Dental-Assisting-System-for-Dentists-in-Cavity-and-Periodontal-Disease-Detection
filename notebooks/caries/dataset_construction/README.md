# DENTEX crop construction — the notebooks that built the caries datasets

Recovered from Google Drive on 21 August 2026 and committed here because they are the
**provenance of every caries number in this project** and existed nowhere in the repo. They
ran on a local machine (`/Users/chennupatigunadeep/Downloads/Capstone/DENTEX/...`), not on
Kaggle; the resulting `processed_dataset/` and `severity_data/` were uploaded to Kaggle as
datasets and consumed by `notebooks/caries/phase-1.ipynb`.

| Notebook | Builds | Source annotations |
|---|---|---|
| `phase_1_Training_Processed_datasets.ipynb` | `processed_dataset/train/{caries,no_caries}` | `train_quadrant_enumeration_disease.json` (705 images, 3,529 anns) |
| `phase_1_Validation_Processed_datasets.ipynb` | `processed_dataset/val/{caries,no_caries}` | `validation_triple.json` (50 images, 182 anns) |
| `phase_2_Training_Processed_datasets.ipynb` | `severity_data/{train,val}/{caries,deep_caries}` | both of the above |

## The crop contract — identical in all three, verified line by line

- Crop is the **raw COCO `bbox = [x, y, w, h]`**, `floor` on the corner, `ceil` on the far
  edge, clipped to image bounds. **No expansion of any kind** — unlike the bone-loss track,
  which uses 1.5x width / 2.0x height (`PAPER_MATERIAL.md` §6.1).
- `cv2.resize(crop, (224, 224))`, no aspect-ratio preservation, no padding.
- Read and written with OpenCV, so **BGR** 3-channel PNG.
- Filename `{image_id}_{annotation_id}.png` — the `13_49.png` convention `phase-1.ipynb`
  relies on. Note `image_id` is the **COCO id within its own file**, not the `train_NNN.png`
  number, and the ids in the train and validation files are independent sequences.
- Degenerate/unreadable crops are skipped. Both notebooks reported `Skipped: 0`.

## Two things these notebooks reveal — read before regenerating anything

**1. `no_caries` contains no healthy teeth.** The label rule is
`category_id_3 in [1, 3] -> 'caries', else -> 'no_caries'`, applied over an annotation file in
which *every annotation is a diseased tooth*. So `no_caries` is precisely
**Impacted + Periapical Lesion** — 604 + 158 = 762 in train, 40 + 9 = 49 in val. The Phase-1
gate is therefore "caries/deep-caries vs impacted/periapical-lesion", never
"caries vs healthy". See `docs/results/RESULTS_LOG.md` 2026-08-21j.

> **And it cannot be fixed from `train_quadrant_enumeration.json`,** despite that file sharing
> 634 filenames with this subset. DENTEX's training subsets number their files independently
> and cover **disjoint patients** — `enumeration/train_0.png` is a different person's scan than
> `disease/train_0.png` (622 of 634 shared names differ in dimensions; a visual check settles
> it). An attempt to derive healthy teeth that way produced 15,531 crops of the wrong patients
> before the error was caught. Correction: `RESULTS_LOG.md` 2026-08-21m.

**2. train and val are different DENTEX releases, not a split.** 705 `train_*.png` images vs
50 `val_*.png` images, **zero overlap**. Phase 2's val is 101 + 32 = 133 crops — the "133
validation crops" every caries metric in this project is measured on.

All counts above were re-derived from the annotation files and match these notebooks' saved
output cells exactly.
