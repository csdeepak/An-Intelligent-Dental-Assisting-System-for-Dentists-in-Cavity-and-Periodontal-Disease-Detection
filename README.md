# 🦷 Dental AI Pipeline — Automated OPG Analysis

> **Caries Detection & Periodontal Bone Loss Detection from Panoramic Dental X-rays**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-4%2F6%20Stages%20Trained-yellow.svg)]()

---

> ## 📍 START HERE
>
> **Picking this up cold — human or AI session? Read [`transfer.md`](transfer.md) first.**
> It is the living snapshot: where we are against the 8-week plan, what is verified done,
> what is next with the actual blocker named, and which decisions are pending. It is
> rewritten in place every substantial session (`CLAUDE.md` rule 5), so it is current in a
> way this README cannot be.
>
> Then, depending on what you need:
>
> | Question | File |
> |---|---|
> | What are the current numbers? | [`docs/results/model_metrics.md`](docs/results/model_metrics.md) |
> | Full technical story + honest limitations (the paper is written from this) | [`docs/results/PAPER_MATERIAL.md`](docs/results/PAPER_MATERIAL.md) |
> | Why is it like this? What happened when? | [`docs/results/RESULTS_LOG.md`](docs/results/RESULTS_LOG.md) (append-only) |
> | What should I work on? | [`docs/research/PUBLICATION_TODO.md`](docs/research/PUBLICATION_TODO.md) status block, sequenced by [`MASTER_PLAN_2026H2.md`](docs/research/MASTER_PLAN_2026H2.md) |
> | How is the documentation laid out? | [`docs/README.md`](docs/README.md) |
> | What does the code do? | [`src/README.md`](src/README.md), [`scripts/README.md`](scripts/README.md) |
>
> ⚠️ **Before running the pipeline on any non-Tufts image, rotate it 90° counter-clockwise**
> — the frozen detector was trained on sideways panoramics. Upright input gives 7.5% recall
> and 0% FDI accuracy. Use `src.orientation.detect_upright`. See [`src/README.md`](src/README.md).

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Pipeline Stages](#pipeline-stages)
- [Current Results](#current-results)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Phase Status](#phase-status)
- [Key Design Decisions](#key-design-decisions)
- [Known Bugs & Fixes](#known-bugs--fixes)
- [Evaluation Targets](#evaluation-targets)
- [Risks & Mitigations](#risks--mitigations)
- [Universal to FDI Conversion](#universal-to-fdi-conversion)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project builds a **fully automated dental diagnostic system** that takes a single
**OPG (Orthopantomogram) X-ray** as input and produces a **structured per-tooth clinical
report** identifying:

- **Caries** — presence (Yes/No) and depth (shallow `caries` vs `deep_caries`)
- **Bone Loss** — presence (Present/Absent) and severity (Mild / Moderate / Severe)

Each finding is mapped to the affected tooth using **FDI numbering** (international
standard). Only affected teeth appear in the final report.

### Final Output Format

```
Tooth [FDI Number]
  → Caries: Yes | Depth: Deep
  → Bone Loss: Present | Severity: Moderate

Tooth [FDI Number]
  → Caries: No
  → Bone Loss: Present | Severity: Mild
```

> ⚠️ **This output format is the design target, not a shipped feature.** The four
> classification/detection models are trained and evaluated independently; the code that
> joins them into one runnable inference (Stages 5–6) **does not exist yet**. See
> [Pipeline Stages](#pipeline-stages).

---

## System Architecture

The system processes an OPG through a **six-stage pipeline**, with two parallel analysis
branches (caries and bone loss) running on different crop types from the same tooth
bounding box.

```
┌─────────────────────────────────────────────────────────────────┐
│                        OPG X-ray Input                          │
│                        (840 × 1615 px)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stage 1: Tooth Detection (YOLOv11l)                │
│              Output: Per-tooth bounding boxes                   │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stage 2: Sorting & FDI Assignment                  │
│              Left→Right sort, jaw split, Universal→FDI          │
└──────────┬───────────────────────────────────────┬──────────────┘
           ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────────┐
│   CARIES PATH        │              │   BONE LOSS PATH         │
│                      │              │                          │
│  Tight Crop (1.0×)   │              │  Expanded Crop           │
│  Crown-focused       │              │  (1.5× W, 2.0× H)        │
│       │              │              │  Crown + root + bone     │
│       ▼              │              │       ▼                  │
│  Resize 224×224      │              │  Resize 224×224          │
│  ImageNet normalize  │              │  ImageNet normalize      │
│       ▼              │              │       ▼                  │
│  ResNet18 Gate       │              │  ResNet18 Binary         │
│  (caries / no)       │              │  (Bone Loss Yes/No)      │
│       ▼ (if caries)  │              │       ▼ (if present)     │
│  ResNet18 Depth      │              │  ResNet18 Severity       │
│  (caries/deep)       │              │  (Mild/Mod/Severe)       │
└──────────┬───────────┘              └──────────┬───────────────┘
           └──────────────┬───────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│      Stage 5: Filter & Report Assembly   ⬜ NOT BUILT           │
│      Keep only: caries=YES OR bone_loss=PRESENT                 │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│      Stage 6: JSON + PDF report (Grad-CAM)  ⬜ NOT BUILT        │
└─────────────────────────────────────────────────────────────────┘
```

> Diagrams: [`docs/architecture/`](docs/architecture/) —
> `corrected_opg_pipeline_architecture.svg` is the authoritative version.

---

## Pipeline Stages

| Stage | Component | Input | Output | Status |
|-------|-----------|-------|--------|--------|
| 1 | Tooth Detection (YOLOv11l) | Full OPG | Tooth bboxes | ✅ **Complete** — test mAP@0.5 **0.782**; canonical run **frozen** as `tooth-detector-a100-1024-v1.0` (T0.6, 20 Aug 2026) |
| 2 | Sorting + FDI assignment | Tooth bboxes | FDI-keyed tooth list | ⚠️ **Implemented, measured, INADEQUATE** — quadrant 93.0% but FDI exact **28.0% end-to-end** ([validated](scripts/eval/README.md) on 1,534 teeth). Universal→FDI table is correct (`f8b31f8`); *positional* numbering needs replacing. |
| 3 | Caries cascade (ResNet18 ×2) | Tight 1.0× crop | caries / deep_caries | ✅ **Complete** — val acc 81%, macro F1 0.77; weights retrieved and tagged `caries-cascade-resnet18-v1.0` (21 Aug 2026). **Re-run pending** — see the note below the table. |
| 4a | Bone Loss binary (ResNet18) | Expanded 1.5×W/2.0×H crop | Present / Absent | ✅ **Complete** — macro F1 **0.9233** |
| 4b | Bone Loss severity (ResNet18) | Expanded crop | Mild / Moderate / Severe | ✅ **Complete** — macro F1 0.7208 (only 52 val crops) |

> **"Complete" means trained, not validated to publication standard.** As of 22 Aug 2026 the
> Tier-0 re-run block is prepared but unrun: the caries numbers above are validation-only,
> from accuracy-selected checkpoints, on a split that has since been replaced by an
> independent one (`data/dentex/splits_v2.json`). `scripts/dentex/train_caries_cascade.py`
> is the re-run that fixes T0.1–T0.4 in one GPU session. Stages 5–6 (integration) do not
> exist yet — `scripts/run_inference.py` is a 38-line placeholder. Current state:
> `docs/research/PUBLICATION_TODO.md` status block.
| — | CEJ bone-level estimation | Expanded crop | bone loss % | 🔬 Exploratory — 15.1% agreement, **not in the pipeline** |
| 5 | Filter + report assembly | All tooth outputs | Filtered findings | ⬜ **Not built — next milestone** |
| 6 | JSON / PDF report + Grad-CAM | Filtered findings | Clinical report | ⬜ **Not built** |

---

## Current Results

Full tables and provenance: [`docs/results/model_metrics.md`](docs/results/model_metrics.md).

| Model | Dataset | Split | Headline metric |
|-------|---------|-------|-----------------|
| YOLOv11l tooth detection (A100, imgsz 1024, 150 ep) | Tufts | val / **test** | mAP@0.5 0.834 / **0.782** |
| YOLOv11l tooth detection (H200, imgsz 768, 50 ep) — superseded | Tufts | val | mAP@0.5 0.678 |
| Caries cascade Phase 2 (caries vs deep_caries) | DENTEX | val (133) | acc **0.81**, macro F1 **0.77** |
| Bone loss binary | Tufts | val (1,558, real prevalence) | macro F1 **0.9233**, sens 83.05%, spec 99.53% |
| Bone loss severity (3-class) | Tufts | val (52) | macro F1 **0.7208** |
| CEJ estimation (exploratory) | Tufts | 296 crops | 15.1% agreement with primary label |

---

## Dataset

### Tufts Dental OPG Dataset — detection + bone loss

| Component | Count | Description |
|-----------|-------|-------------|
| Radiographs | 1,000 | OPG X-rays (840 × 1615 px, uniform) |
| Tooth Bounding Boxes | 26,005 | Per-tooth annotations across 968 images |
| Expert Reports | 1,000 | Free-text radiology diagnoses |
| Expert Pathology Masks | 439 | 285 empty (normal) + 154 annotated |
| Working Training Pool | 423 | Images with full annotation overlap |
| Detection split | 700 / 150 / 150 | Frozen image-level 70/15/15 train/val/test |
| Bone-loss crops built | 22,806 | 23.84× class imbalance (96% normal / 4% diseased) |

### DENTEX — caries

| Split / class | Count |
|---------------|-------|
| Phase 1 train — `caries` / `no_caries` | 2,767 / 762 |
| Phase 2 val — `caries` / `deep_caries` | 101 / 32 (133 total) |

### Dataset Characteristics

| Metric | Value |
|--------|-------|
| Image size | 840 × 1615 px (uniform) |
| Avg teeth per image | 26.9 |
| Tooth aspect ratio | ~0.35 (3× taller than wide) |
| Michelson contrast | 0.999 (high quality) |
| Bbox coordinate format | `[y1, x1, y2, x2]` corner points |
| Tooth numbering | Universal (1-32) — converted to FDI |
| Join key | `External ID` field in JSON records |

### Crop Strategy

| Model | Crop Factor | Region | Rationale |
|-------|-------------|--------|-----------|
| Caries (ResNet18) | 1.0× (tight) | Crown only | Caries appears on enamel/dentin |
| Bone Loss (ResNet18) | 1.5× W / 2.0× H | Crown + root + bone | Bone level visible below root; asymmetric because teeth are tall |

---

## Project Structure

```
An-Intelligent-Dental-Assisting-System-.../
│
├── README.md                       ← You are here
├── CLAUDE.md                       ← Working rules for AI/automation sessions in this repo
├── LICENSE  ·  requirements.txt  ·  setup.py  ·  .gitignore
│
├── configs/
│   └── dataset_config.yaml         ← All paths, hyperparameters, Universal→FDI table
│
├── src/
│   ├── data_loader.py              ← JSON parsing, coordinate conversion
│   ├── crop_generator.py           ← Expanded crop, jitter, resize
│   ├── label_assigner.py           ← Pixel-overlap ratio, thresholding
│   └── utils/                      ← fdi_converter, visualization, constants
│
├── scripts/
│   ├── build_dataset.py            ← CLI: build the crop training dataset
│   ├── train_model.py              ← CLI: train the bone loss model
│   ├── run_inference.py            ← CLI: pipeline inference (stub — Stage 5/6 not built)
│   └── yolo/                       ← Stage 1 detection toolchain (+ its own README)
│       ├── convert_tufts_to_yolo.py
│       ├── train_yolo.py
│       └── evaluate_yolo.py
│
├── notebooks/
│   ├── yolo_detection/             ← Stage 1 — the two competing runs (+ README)
│   │   ├── a100_1024px_150ep.ipynb ← current best detector
│   │   └── h200_768px_50ep.ipynb   ← superseded
│   ├── caries/                     ← Stage 3 — DENTEX cascade
│   │   ├── phase-1.ipynb
│   │   └── approach.txt            ← method + the author's own critique of it
│   └── bone_loss/                  ← Stage 4 — Tufts (renamed from "Bone Loss")
│       ├── 01_tufts_data_exploration_v2.ipynb
│       ├── 02_bone_loss_dataset_construction.ipynb
│       ├── 03_bone_loss_model_training.ipynb
│       ├── 04_bone_loss_severity.ipynb
│       └── 05_cej_estimation_v2.ipynb
│
├── docs/                           ← ★ documentation system — start at docs/README.md
│   ├── README.md                   ← index of everything below
│   ├── architecture/               ← pipeline diagrams (+ drawio source)
│   ├── results/
│   │   ├── PAPER_MATERIAL.md       ← ★ master paper-writing document
│   │   ├── RESULTS_LOG.md          ← append-only milestone journal
│   │   ├── model_metrics.md        ← one-page scoreboard
│   │   └── figures/                ← result plots (detector curves, confusion matrices)
│   ├── reports/
│   │   ├── project_report.pdf  ·  data_exploration_v2.pdf
│   │   │                              (pes_capstone_report/ archived 2026-08-15 →
│   │   │                               _repo_archive/, see ARCHIVE_MANIFEST.md)
│   │   ├── literature/             ← survey paper + literature review sheet
│   │   └── legacy/                 ← original all-in-one analysis document
│   ├── exploration/README.md       ← dataset quirks + the 5 critical bugs caught
│   ├── session-memory/             ← one dated file per working session
│   └── research/                   ← maintained by a separate workstream
│
├── models/                         ← Trained checkpoints + training summaries
│   ├── 03_bone_loss_model_training_notebook_models/
│   ├── 04_bone_loss_severity_notebook_models/
│   ├── 05_cej_estimation_v2_models/
│   └── 06_yolo_detection_a100_run/ ← best.pt/last.pt (git-ignored), args, results.csv
│
├── data/                           ← Datasets and metadata (large files git-ignored)
└── tests/                          ← test_data_loader, test_crop_generator,
                                       test_label_assigner, test_fdi_converter
```

> Bulky untracked material (a stale nested clone, the 2.2 GB raw-data workspace, the YOLO
> run directory, duplicate diagrams) was **relocated, not deleted**, to `_repo_archive/`,
> a sibling folder outside this repo. See `_repo_archive/ARCHIVE_MANIFEST.md` for the full
> inventory and one-line restore commands.

---

## Setup & Installation

### Prerequisites

- Python 3.8+
- CUDA-compatible GPU (recommended for training)
- Google Colab / Kaggle (with GPU runtime) — most notebooks were run this way

### Local Setup

```bash
git clone https://github.com/csdeepak/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection.git
cd An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection

python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### Dataset Setup

The Tufts Dental Dataset is expected in Google Drive:

```
Google Drive/
  tufts/
    ZIP/
      Radiographs/Radiographs/     ← OPG images (.JPG)
      Segmentation/Segmentation/   ← teeth_bbox.json, teeth_polygon.json
      Expert/Expert/               ← expert.json
      Expert/Expert/mask/          ← Expert pathology masks (.JPG)
```

> Update the `paths.base` value in `configs/dataset_config.yaml` to match your mount.
> The YOLO scripts in `scripts/yolo/` still carry hard-coded macOS paths — edit them
> before use (noted in `scripts/yolo/README.md`).

---

## Usage

### 1. Stage 1 — tooth detection

```bash
python scripts/yolo/convert_tufts_to_yolo.py   # Tufts → YOLO format + data.yaml
python scripts/yolo/train_yolo.py              # fine-tune YOLOv11l (imgsz 1024)
python scripts/yolo/evaluate_yolo.py           # evaluate best.pt on the test split
```

### 2. Stage 4 — bone loss crop dataset + model

Run `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb` (crop construction,
overlap labelling, image-level split), then
`notebooks/bone_loss/03_bone_loss_model_training.ipynb`. Equivalent CLI entry points:

```bash
python scripts/build_dataset.py --config configs/dataset_config.yaml
python scripts/train_model.py   --config configs/dataset_config.yaml
```

**Critical review points during dataset construction:** inspect the overlap-ratio
distribution before accepting `overlap_threshold`, and inspect the visual validation grid
before trusting the labels. If the labels do not match the pathology, adjust the threshold
and rebuild.

### 3. Stage 3 — caries

`notebooks/caries/phase-1.ipynb` (Kaggle, DENTEX pre-processed crops). Read
`notebooks/caries/approach.txt` first — it documents both the method and its gaps.

### 4. Full pipeline inference — not available yet

```bash
python scripts/run_inference.py --image path/to/opg.jpg --output report.json
```

Stages 5–6 are not implemented; this entry point is a stub.

---

## Phase Status

| Phase | Description | Owner | Status |
|-------|-------------|-------|--------|
| Phase 0 | Literature review & survey paper | Deepak | ✅ Complete |
| Phase 1 | Caries — gate (ResNet18 binary) | Collaborator | ✅ Complete (Phase 1 metrics not saved) |
| Phase 2 | Caries — depth (caries vs deep_caries) | Collaborator | ✅ Complete — val acc 81%, macro F1 0.77 |
| Phase 3 | Tooth Detection (YOLOv11l) | Deepak | ✅ Complete — test mAP@0.5 0.782; canonical run **frozen + tagged** 20 Aug 2026 |
| Phase 4a | Bone Loss — data exploration | Deepak | ✅ Complete |
| Phase 4b | Bone Loss — dataset construction | Deepak | ✅ Complete — 22,806 crops |
| Phase 4c | Bone Loss — model training | Deepak | ✅ Complete — macro F1 0.9233 |
| Phase 4d | Bone Loss — evaluation + severity | Deepak | ✅ Complete — severity macro F1 0.7208 (52 val crops) |
| Phase 4e | CEJ bone-level estimation | Deepak | 🔬 Exploratory — negative result, not integrated |
| Phase 5 | Full pipeline integration (Stages 5–6) | Both | ⬜ **Not started — current milestone** |
| Phase 6 | Paper writing | Both | 🟡 In progress — see `docs/results/PAPER_MATERIAL.md` |

---

## Key Design Decisions

### 1. Pixel-Overlap Ratio Instead of IoU

```
overlap = mask_pixels_inside_crop / crop_area
```

**Why not IoU?** Expert mask blobs are tiny sparse lesion annotations (0.5–2% of an
expanded crop). IoU = intersection / union ≈ tiny / large ≈ 0, so even true positives get
IoU ≈ 0 and every crop is labelled negative.

**Threshold:** 0.01 (1%), defensible range 0.005–0.02. The same quantity is reused as the
severity axis: mild ≤ 0.05, moderate 0.05–0.15, severe > 0.15.

### 2. Asymmetric Crop Expansion (1.5× W, 2.0× H)

Teeth have a mean aspect ratio of ~0.35 (3× taller than wide). Equal expansion in both
directions bleeds into adjacent teeth horizontally while under-covering vertically. More
vertical expansion captures the alveolar bone below the root, which is exactly where bone
loss is visible.

### 3. Binary Classification Instead of Severity Segmentation

U-Net severity segmentation was ruled out because expert masks encode **per-lesion instance
IDs**, not severity classes; no pixel-level mild/moderate/severe annotation exists; only
154 annotated samples; and CEJ ground-truth points do not exist in the dataset.

### 4. Image-Level (Patient-Level) Train/Val Split

All crops from the same radiograph — including jittered copies — stay in the same split.
A crop-level split leaks patient-specific exposure and anatomy between train and val.

### 5. Bbox Jitter for Detector Noise Simulation

Training crops come from ground-truth boxes; inference crops come from YOLO predictions
with small localisation errors. ±15% random jitter during training teaches robustness to
imperfect crop boundaries. **Not yet validated on real detector output** — the integration
that would test it does not exist.

### 6. Clinically-Valid Augmentation Only (detector)

Horizontal flip, ±10° rotation, small translate/scale, HSV-value jitter. **No vertical
flip** (an inverted jaw is anatomically meaningless), **no mosaic**, **no mixup** — both
destroy the global jaw geometry that tooth ordering depends on.

---

## Known Bugs & Fixes

Discovered during data exploration and **already fixed** in all code
(full detail: [`docs/exploration/README.md`](docs/exploration/README.md)):

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Coverage matrix showed 0 matches | Compared filename stems against dict keys; actual join field is nested `External ID` | Extract `Path(item['External ID']).stem` as join key |
| All crops extracted from wrong locations | Assumed bbox format `[x, y, w, h]`; actual format is `[y1, x1, y2, x2]` | Convert: `w = x2-x1`, `h = y2-y1`, swap x and y |
| U-Net architecture selected prematurely | Assumed expert masks encode severity; pixel values are per-lesion instance IDs | Changed to binary ResNet18 classifier |
| PIL DecompressionBombError | PIL rejected large composite figures | `PILImage.MAX_IMAGE_PIXELS = None` |
| Font download 404 | wget from GitHub returned HTML instead of TTF | `apt-get install fonts-dejavu-core` |

### Closed bug — Universal→FDI lower-arch mapping

**Fixed in `f8b31f8`.** This section previously said the bug was open and deliberately
left unfixed. Re-verified 21 Aug 2026 against the actual files: `configs/dataset_config.yaml`
and `src/utils/fdi_converter.py` both match the correct table below, agree with each other,
and `tests/test_fdi_converter.py` carries regression tests naming the historical bug
explicitly. Nothing to do here.

---

## Evaluation Targets

| Metric | Target | Achieved (bone loss binary) |
|--------|--------|------------------------------|
| Class 0 F1 (normal) | ≥ 0.75 | **0.9943** ✅ |
| Class 1 F1 (bone loss) | ≥ 0.70 | **0.8522** ✅ |
| Macro F1 | ≥ 0.72 | **0.9233** ✅ |
| Accuracy | Secondary | 98.91% (misleading at 4% prevalence) |

Severity model: macro F1 **0.7208** against the same 0.72 target — met, but on 52
validation crops, so treat as provisional. Detection: test mAP@0.5 **0.782** against a
literature benchmark of ≥ 0.90 — **not met**.

### Training Configuration (bone loss binary)

| Parameter | Value |
|-----------|-------|
| Architecture | ResNet18 pretrained (ImageNet), FC 512 → 2 |
| Loss | Focal Loss (γ=2.0, α=[0.642, 2.258]) |
| Optimizer | Adam, lr=1e-4, wd=1e-4 |
| Scheduler | ReduceLROnPlateau (patience=5) |
| Batch size | 32 |
| Epochs | 50 budgeted / 32 run, best epoch 22 (early stopping on val macro-F1, patience 10) |
| Augmentation | H-flip, brightness jitter, rotation ±10°, bbox jitter ±15% |
| Normalization | ImageNet mean/std |

---

## Risks & Mitigations

| Risk | Level | Mitigation |
|------|-------|------------|
| Small training set (423 annotated images) | HIGH | Heavy augmentation, transfer learning from ImageNet |
| Image-level labels → noisy per-crop assignment | MEDIUM | Spatial overlap with expert mask (not blanket labelling) |
| Detector recall 0.74 → missed teeth never classified | HIGH | Freeze the 1024 px model; measure error propagation once Stage 5 exists |
| YOLO crop variability at inference | MEDIUM | ±15% bbox jitter during training (unvalidated end-to-end) |
| Class imbalance 23.8× (bone loss) | HIGH | Undersampling + minority augmentation + Focal Loss; untouched val set |
| Universal vs FDI numbering mismatch | HIGH | Conversion at detector output — fixed and regression-tested (`f8b31f8`) |
| Domain shift (Tufts vs real OPGs) | MEDIUM | CLAHE normalisation at inference (untested) |
| No external clinical validation | HIGH | Acknowledged limitation; out of scope for the capstone |

---

## Universal to FDI Conversion

Tufts uses Universal numbering (1–32); the clinical report requires FDI. **Correct**
mapping:

| Universal | FDI | Universal | FDI | Universal | FDI | Universal | FDI |
|-----------|-----|-----------|-----|-----------|-----|-----------|-----|
| 1 | 18 | 9 | 21 | 17 | 38 | 25 | 41 |
| 2 | 17 | 10 | 22 | 18 | 37 | 26 | 42 |
| 3 | 16 | 11 | 23 | 19 | 36 | 27 | 43 |
| 4 | 15 | 12 | 24 | 20 | 35 | 28 | 44 |
| 5 | 14 | 13 | 25 | 21 | 34 | 29 | 45 |
| 6 | 13 | 14 | 26 | 22 | 33 | 30 | 46 |
| 7 | 12 | 15 | 27 | 23 | 32 | 31 | 47 |
| 8 | 11 | 16 | 28 | 24 | 31 | 32 | 48 |

> ✅ **`configs/dataset_config.yaml` matches this table.** Checked entry-by-entry on
> 21 Aug 2026, along with `src/utils/fdi_converter.py` (identical table, and the two agree)
> and `tests/test_fdi_converter.py` (regression tests that name the historical bug — the
> shifted lower arch, and the duplicated FDI 33/34 that collapsed the reverse lookup).
> The fix landed in `f8b31f8`; this warning had outlived it.

---

## Contributing

This is a capstone project. Contributions follow this workflow:

1. Create a feature branch: `git checkout -b feature/pipeline-integration`
2. Make changes and test
3. Commit with descriptive messages
4. Push and open a pull request

**Automation note:** [`CLAUDE.md`](CLAUDE.md) at the repo root defines the standing rules
for AI-assisted sessions — every result gets logged to `docs/results/RESULTS_LOG.md`, every
session leaves a `docs/session-memory/` file, and nothing is ever deleted (only relocated
to `_repo_archive/`).

### Commit Message Convention

```
feat:     New feature (e.g., "feat: add visual validation step")
fix:      Bug fix (e.g., "fix: correct bbox coordinate conversion")
data:     Dataset changes (e.g., "data: update overlap threshold to 0.015")
docs:     Documentation (e.g., "docs: add exploration findings")
refactor: Code refactoring without functional change
test:     Adding or updating tests
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgments

- **Tufts Dental Dataset** — multi-annotator OPG radiograph collection
- **DENTEX** — dental enumeration and diagnosis dataset (caries)
- **PyTorch** / **torchvision** — model architecture and training
- **Ultralytics** — YOLOv11 for tooth detection

---

<p align="center">
  <strong>Dental AI Pipeline</strong> — Capstone Project 2026
</p>
