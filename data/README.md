# `data/` — datasets

**Last verified: 22 August 2026** against the working tree. Everything of size here is
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
├── dentex/                    1.2 GB   Stage 3 caries
│   ├── splits_v2.json          56 KB   ** TRACKED ** — the frozen image-level 70/15/15 split
│   ├── raw/                   6.9 MB   COCO annotation JSONs (gitignored, re-downloadable)
│   └── crops_v2/              1.2 GB   generated crops + manifest
└── ningxia/                   1.7 MB   primary EXTERNAL validation
    └── manifest.csv           1.7 MB   ** TRACKED ** — 13,160 rows; the images are NOT here
```

## Where the bulk data actually lives

| Dataset | Location | Note |
|---|---|---|
| **Tufts** raw radiographs | `_repo_archive/datasets_workspace/Radiographs{,_rotated}/` | 1,000 each; `_rotated` is portrait 840×1615, which every script expects |
| **Tufts** frozen split | `_repo_archive/datasets_workspace/outputs/eda_tufts/split_v1.csv` | The split behind every reported detector number. Gitignored, which is why a previous search declared it lost. |
| **DENTEX** full release | `~/Downloads/Capstone/DENTEX/` | Outside the repo. See below. |
| **Ningxia** images | External drive — **not currently connected** | 6,580 images, 3 hospitals. `MASTER_PLAN_2026H2.md` §4.4 records the original download at `D:\nangxia_dataset` on the Windows machine. |
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
| `training_data/quadrant_enumeration/xrays/` | 634 | 18,095 teeth, no disease labels | **Not usable** for a healthy class — disjoint patients. |
| `training_data/quadrant/xrays/` | 693 | quadrant only | Unused. |
| `training_data/unlabelled/xrays/` | 1,572 | none | Unused. |
| `disease/{input,label}/` | 250 | 1,600 polygons, **8 classes, FDI-keyed** | Not yet used — see `RESULTS_LOG.md` 2026-08-22. |

## Tracked vs ignored — the rule

Tracked: split manifests (`splits_v2.json`), index CSVs (`ningxia/manifest.csv`).
Ignored: every image, crop, archive and raw annotation dump.

Rationale: a split manifest is what makes a result reproducible and is a few tens of KB; the
pixels are re-derivable from the source release. `crops_v2/` regenerates with
`scripts/dentex/build_dentex_crops.py`, `dataset_seg/` with
`scripts/yolo/convert_tufts_to_yolo_seg.py`.
