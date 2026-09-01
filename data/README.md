# `data/` — datasets

**Last verified: 1 September 2026** against the working tree (added the Lever 1 multi-corpus
detector dataset and the CariesXrays external cohort; earlier: 26 Aug, Tufts enumeration corpus).
Everything of size here is git-ignored; what *is* tracked is the small, high-value metadata
that makes a run reproducible — split manifests and index CSVs.

**⚠️ Tufts licence note.** The Tufts Dental Database's release agreement forbids reproducing
or posting it "into any webpage or any other storage means." `docs/EXTERNAL_DRIVE.md` has the
full warning and the required citation — read it before sharing anything under `tufts/` beyond
this machine.

> The previous version of this file described a single `processed_dataset_tufts/` layout that
> does not exist, and said the Tufts raw data "should be stored on Google Drive". Both were
> stale. Corrected below.

## What is actually here

```
data/
├── tufts/                     2.2 GB   Stage 1 detection + Stage 4 bone loss + Stage 2 (second corpus)
│   ├── ZIP/                   291 MB   raw Tufts release (teeth_polygon.json, teeth_bbox.json, …)
│   ├── dataset_seg/           474 MB   ⚠️ SUPERSEDED, labels 90° off (the withdrawn pre-fix R1
│   │                                   corpus). NOT what the adopted detector trained on — see §1a
│   │                                   of transfer.md. `dataset_seg_v2/` (the corrected build R1
│   │                                   actually used) is regenerable but NOT on this machine.
│   ├── enumeration_v1/        1.5 GB   [Stage 2] FDI-labelled crops (42,755) + manifest — Tufts'
│   │                                   numbering is left-right MIRRORED and corrected before use;
│   │                                   see scripts/tufts/README.md before touching this data
│   ├── resampled_dataset/     140 KB   bone-loss binary crop metadata
│   └── severity_dataset/      148 KB   bone-loss severity crop metadata
├── dentex/                    3.2 GB   Stages 2 and 3
│   ├── splits_v2.json          56 KB   ** TRACKED ** — the frozen image-level 70/15/15 split
│   ├── disease_leaked_images.json      ** TRACKED ** — the 86 evaluation images that must be
│   │                                   excluded as training duplicates. Read this before
│   │                                   reporting any Stage-2 number.
│   ├── raw/                   6.9 MB   COCO annotation JSONs (gitignored, re-downloadable)
│   ├── crops_v2/              1.2 GB   Stage-3 caries crops + manifest
│   ├── crops_v3_phase1/                pinned v3.0 caries-gate corpus (gitignored)
│   ├── crops_v4_phase1/                31 Aug — v3 + 444 disease-only images (negative result; gitignored)
│   ├── crops_clahe_phase1/             31 Aug — CLAHE arm (gitignored)
│   ├── crops_exp125_phase1/            31 Aug — 1.25× crop arm (gitignored)
│   └── enumeration_v1/        1.7 GB   Stage-2 enumeration-head crops (33,461) + manifest
├── detector_multicorpus/     816 MB   [Lever 1 / B1] Tufts + DENTEX YOLO-detect set — 1,334/150/150,
│                                      val+test Tufts-only + canonical. Built + geometry-gated 1 Sep.
│                                      Gitignored; rebuild with scripts/yolo/build_multicorpus_detector_dataset.py
└── ningxia/                   1.7 MB   primary EXTERNAL validation
    └── manifest.csv           1.7 MB   ** TRACKED ** — 13,160 rows; the images are NOT here
```

**Caries crop variants (`crops_v3` … `crops_exp125`):** the default `build_caries_phase1_v3.py`
path reproduces `crops_v3_phase1` exactly; the other three are opt-in experiment builds from
31 Aug and are **not** part of any shipped model (`RESULTS_LOG.md` 2026-08-31 / 08-31b).

## Where the bulk data actually lives

| Dataset | Location | Note |
|---|---|---|
| **Tufts** raw radiographs | `_repo_archive/datasets_workspace/Radiographs{,_rotated}/` | 1,000 each; `_rotated` is portrait 840×1615, which every script expects |
| **Tufts** frozen split | `_repo_archive/datasets_workspace/outputs/eda_tufts/split_v1.csv` | The split behind every reported detector number. Gitignored, which is why a previous search declared it lost. |
| **DENTEX** full release | `~/Downloads/Capstone/DENTEX/` | Outside the repo. See below. |
| **Ningxia** images | `~/Downloads/Capstone/ningxia_local/` (test splits only, 2.4 GB) | **Connected and evaluated 25 Aug.** Train split (11.2 GB) deliberately left on the pen drive — Ningxia is locked external test data, never trained on. Zero leakage verified against all 5 other corpora, each checked separately. `docs/EXTERNAL_DRIVE.md` has the drive links; `RESULTS_LOG.md` 2026-08-25d has the numbers. |
| **CariesXrays** (AAAI 2024, Chen et al.) | `~/Downloads/Capstone/CariesXrays_Dataset/` (~2 GB) | 6,000 panoramic images + Pascal-VOC per-lesion boxes. Used **frozen-pipeline only** as the 6th external cohort (a seed-42 random 1,500-image draw scored; `scripts/eval/cariesxrays_external.py`). No LICENSE file ships with it — flagged in `main.tex` §8.25. Never trained on. Constant beats pipeline by **+0.252 [+0.232, +0.273]** — the strongest form of the paper's central claim. |
| **Clinic (SDH)** | On the **Windows** machine, `D:\` (struck 30 Aug — not the macOS machine) | Consent obtained 30 Aug; `docs/research/SDH_EXECUTION_PLAN.md`. Metrics-only artefacts tracked at `data/sdh/`; no pixel leaves `D:`. |

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
`scripts/yolo/convert_tufts_to_yolo_seg.py`, `tufts/enumeration_v1/` with
`scripts/tufts/build_enumeration_crops.py`.

---

**Publication target and grading criteria:** `../transfer.md` §5.
