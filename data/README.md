# `data/` — datasets

**Last verified: 2 September 2026** against the working tree (added `cariesxrays_det/` — the
Lever-2 YOLO training set — and downloaded the full CariesXrays benchmark to the Windows
machine; earlier: 1 Sep, the Lever 1 multi-corpus detector dataset + the CariesXrays external
cohort; 26 Aug, Tufts enumeration corpus). Everything of size here is git-ignored; what *is*
tracked is the small, high-value metadata that makes a run reproducible — split manifests and
index CSVs.

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
├── kaggle_dual/              ~1.7 GB  Stage-2 THIRD FDI corpus — Kaggle "dual-labeled". ALL gitignored.
│   ├── labels/                219 MB  2,066 raw LabelMe polygon JSONs (FDI 11–48 + label 91).
│   │                                  Only 500 have a matching image; 1,566 are label-only, unusable.
│   ├── images1/               533 MB  500 panoramics, variable size (2940×1435 / 2440×1280 / 943×473)
│   └── enumeration_v1/       1012 MB  regenerable crops — scripts/kaggle_dual/build_enumeration_crops.py
├── detector_multicorpus/     816 MB   [Lever 1 / B1] Tufts + DENTEX YOLO-detect set — 1,334/150/150,
│                                      val+test Tufts-only + canonical. Built + geometry-gated 1 Sep.
│                                      Gitignored; rebuild with scripts/yolo/build_multicorpus_detector_dataset.py
├── cariesxrays_det/          ~4 GB    [Lever 2] CariesXrays VOC→YOLO detect set — 4,800/1,200,
│                                      THIS PROJECT'S seed-42 split (the FPCL split is not public).
│                                      Single class "decay". Gitignored; rebuild with
│                                      scripts/yolo/build_cariesxrays_detector_dataset.py from the
│                                      benchmark at ~/Downloads/Capstone/CariesXrays_Dataset/.
├── ningxia/                   1.7 MB   primary EXTERNAL validation
│   └── manifest.csv           1.7 MB   ** TRACKED ** — 13,160 rows; the images are NOT here
└── sdh/                       ~700 KB  clinic set — METRICS ONLY, never pixels
    ├── quality_metrics_enhanced.csv    ** TRACKED ** — 3,213 rows, per-image quality metrics
    │                                   keyed by opaque image ID. The generating script never
    │                                   opens metadata/index.csv (the re-identification map).
    └── pilot_inference_n24.csv         ** TRACKED ** — the 24-image label-free pilot,
                                        RESULTS_LOG.md 2026-08-30. These 24 images are BURNED
                                        for evaluation and must land in SDH-DEV.
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
| **Kaggle "dual-labeled"** (3rd FDI corpus) | `data/kaggle_dual/` (~1.7 GB) — **entirely gitignored**, local working dir | The **third** Stage-2 FDI training source, added in `33f8b6e` for **head v3** (`models/12`, ablation only — `RESULTS_LOG.md` 2026-08-28c, `PAPER_MATERIAL.md` §8.23). Kaggle "Dual-labeled Panoramic Radiographs": 2,066 LabelMe polygon JSONs but only **500 images with a matching label** (1,566 are label-only, unusable) → **499 usable images / 13,166 teeth**, 33 classes (FDI 11–48 + label 91; 24 label-91 teeth dropped). **Numbering verified standard FDI, read as written** — the v2 head as arbiter scored 80.3% direct vs 1.7% mirrored (`scripts/kaggle_dual/verify_fdi_convention.py`). Cited in the paper's Data Availability. Not tracked: `labels/` + `images1/` are a re-downloadable raw annotation dump; `enumeration_v1/` crops rebuild with `scripts/kaggle_dual/build_enumeration_crops.py` (1.5× symmetric, 224², same contract as the other two corpora). `scripts/kaggle_dual/` **is** tracked. |
| **CariesXrays** (AAAI 2024, Chen et al.) | `~/Downloads/Capstone/CariesXrays_Dataset/` — **full download, ~4 GB** on the Windows machine (`Annotations/` 6,000 XML + `JPEGImages/` 6,000 JPG; the zips were deleted after extraction, re-downloadable from the Drive folder `1qWL2f0A-…`). Also on the macOS machine. | 6,000 panoramic images + Pascal-VOC per-lesion boxes, single class. No LICENSE file — flagged in `main.tex` §8.25. **(1)** Used **frozen-pipeline** as the 6th external cohort — constant beats pipeline by **+0.252 [+0.232, +0.273]** (`scripts/eval/cariesxrays_external.py`, §8.25). **(2) Lever 2, 2 Sep:** a *standalone* YOLOv11l lesion detector was trained on it (this project's own seed-42 4,800/1,200 split → `data/cariesxrays_det/`, `models/14_cariesxrays_lever2/`) — **benchmark row only, not wired into the pipeline; the pipeline still never trains on it.** 27.3% of the XMLs carry a wrong `<size>` width — always read dims from the decoded image. |
| **Clinic (SDH)** | On the **Windows** machine, `D:\` (struck 30 Aug — not the macOS machine): `D:\SDH dataset\dataset\images\` (3,219 enhanced 8-bit PNGs, of which **3,213 decode**; six truncated), `D:\dataset_audit\` (Stage-1 + audit CSVs), `D:\raw data\` (4,433 `.pano`) | Consent obtained 30 Aug; no longer governance-blocked. Plan: `docs/research/SDH_EXECUTION_PLAN.md`; Drive `index.csv` exposure: `docs/research/clinical_dataset_provenance.md` §4a. Metrics-only artefacts tracked at `data/sdh/`; no pixel leaves `D:`. |

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
`scripts/tufts/build_enumeration_crops.py`, `kaggle_dual/enumeration_v1/` with
`scripts/kaggle_dual/build_enumeration_crops.py`, `detector_multicorpus/` with
`scripts/yolo/build_multicorpus_detector_dataset.py`, and `cariesxrays_det/` with
`scripts/yolo/build_cariesxrays_detector_dataset.py`. The `kaggle_dual/labels/` polygon JSONs
are a **raw annotation dump** (re-downloadable from Kaggle), not a manifest — hence ignored,
same as `dentex/raw/`.

---

**Publication target and grading criteria:** `../transfer.md` §5.
