# `data/` — datasets

**Last verified: 22 August 2026 (enumeration data added)** against the working tree. Everything of size here is
git-ignored; what *is* tracked is the small, high-value metadata that makes a run
reproducible — split manifests and index CSVs.

> The previous version of this file described a single `processed_dataset_tufts/` layout that
> does not exist, and said the Tufts raw data "should be stored on Google Drive". Both were
> stale. Corrected below.

## What is actually here

```
data/
├── tufts/                     765 MB   Stage 1 detection + Stage 4 bone loss
│   ├── ZIP/                   291 MB   raw Tufts release (teeth_polygon.json, teeth_bbox.json, …)
│   ├── dataset_seg/           474 MB   [R1] YOLO-seg training set — 26,005 instances, 700/150/150
│   ├── resampled_dataset/     140 KB   bone-loss binary crop metadata
│   └── severity_dataset/      148 KB   bone-loss severity crop metadata
├── dentex/                    2.9 GB   Stages 2 and 3
│   ├── splits_v2.json          56 KB   ** TRACKED ** — the frozen image-level 70/15/15 split
│   ├── disease_leaked_images.json      ** TRACKED ** — the 86 evaluation images that must be
│   │                                   excluded as training duplicates. Read this before
│   │                                   reporting any Stage-2 number.
│   ├── raw/                   6.9 MB   COCO annotation JSONs (gitignored, re-downloadable)
│   ├── crops_v2/              1.2 GB   Stage-3 caries crops + manifest
│   └── enumeration_v1/        1.7 GB   Stage-2 enumeration-head crops (33,461) + manifest
└── ningxia/                   1.7 MB   primary EXTERNAL validation
    └── manifest.csv           1.7 MB   ** TRACKED ** — 13,160 rows; the images are NOT here
```

## Where the bulk data actually lives

| Dataset | Location | Note |
|---|---|---|
| **Tufts** raw radiographs | `_repo_archive/datasets_workspace/Radiographs{,_rotated}/` | 1,000 each; `_rotated` is portrait 840×1615, which every script expects |
| **Tufts** frozen split | `_repo_archive/datasets_workspace/outputs/eda_tufts/split_v1.csv` | The split behind every reported detector number. Gitignored, which is why a previous search declared it lost. |
| **DENTEX** full release | `~/Downloads/Capstone/DENTEX/` | Outside the repo. See below. |
| **Ningxia** images | `~/Downloads/Capstone/ningxia_local/` (test splits only, 2.4 GB) | **Connected and evaluated 25 Aug.** Train split (11.2 GB) deliberately left on the pen drive — Ningxia is locked external test data, never trained on. Zero leakage verified against all 5 other corpora, each checked separately. `docs/EXTERNAL_DRIVE.md` has the drive links; `RESULTS_LOG.md` 2026-08-25d has the numbers. |
| **Clinic (SDH)** | Not on this machine | Governance-blocked — `docs/research/clinical_dataset_provenance.md` §4a. |

## The DENTEX release, mapped

`~/Downloads/Capstone/DENTEX/` — full, verified 22 Aug 2026. **The subsets number their files
independently and cover disjoint patients**: `train_0.png` under `quadrant_enumeration/` is a
different person's scan from `train_0.png` under `quadrant-enumeration-disease/`. Joining them
on filename is invalid and has already caused one bug (`RESULTS_LOG.md` 2026-08-21m).

| Path | Images | Annotations | Used for |
|---|---|---|---|
| `training_data/quadrant-enumeration-disease/xrays/` | 705 | 3,529 disease boxes, 4 classes | **The caries cascade.** Source of `splits_v2.json` and `crops_v2/`. |
| `validation_data/quadrant_enumeration_disease/xrays/` | 50 | 182 | `extern50` — an independent second eval set. Disjoint from the 705 (verified). |
| `training_data/quadrant_enumeration/xrays/` | 634 | 18,095 teeth with quadrant + position | **Trains the Stage-2 enumeration head.** Not usable for a *healthy* class — disjoint patients from the 705 disease subset. **But it overlaps `disease/` by 85 images**, which is a separate fact and the source of a leakage bug: two folders being disjoint says nothing about a third. |
| `training_data/quadrant/xrays/` | 693 | quadrant only | Unused. |
| `training_data/unlabelled/xrays/` | 1,572 | none | Unused. |
| `disease/{input,label}/` | 250 | 1,600 polygons, **8 classes, FDI-keyed** | **Stage-2 evaluation set** — but only 164 of the 250 are usable: 85 are byte-identical to `quadrant_enumeration` images (the head's training data) and 1 to a detector training image. See `disease_leaked_images.json`. |

## Tracked vs ignored — the rule

Tracked: split manifests (`splits_v2.json`), the leakage exclusion list
(`disease_leaked_images.json`), index CSVs (`ningxia/manifest.csv`).
Ignored: every image, crop, archive and raw annotation dump.

Rationale: a split manifest is what makes a result reproducible and is a few tens of KB; the
pixels are re-derivable from the source release. `crops_v2/` regenerates with
`scripts/dentex/build_dentex_crops.py`, `dataset_seg/` with
`scripts/yolo/convert_tufts_to_yolo_seg.py`.
