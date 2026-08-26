# 🦷 Dental AI Pipeline — Automated OPG Analysis

> **Caries Detection & Periodontal Bone Loss Detection from Panoramic Dental X-rays**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-6%2F6%20Stages%20Running-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-65%20passing-brightgreen.svg)]()
[![External](https://img.shields.io/badge/external%20validation-4%20hospitals-blue.svg)]()

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
> | **Publication target and grading criteria** | [`transfer.md`](transfer.md) §5 |
> | **Setting this up on a new machine — what's in git vs what needs a manual Drive fetch** | [`transfer.md`](transfer.md) §8, [`docs/EXTERNAL_DRIVE.md`](docs/EXTERNAL_DRIVE.md) |
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
- [Publication Target & Grading Criteria](#publication-target--grading-criteria)
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

> ✅ **This output format is shipped, not just a design target.** `scripts/run_inference.py`
> joins all six stages into one runnable inference: OPG in, per-tooth JSON + annotated overlay
> out. There is also a browser demo — `streamlit run app.py`, or `docker build` from the
> repo's `Dockerfile`. See [Usage](#usage) and [Pipeline Stages](#pipeline-stages) below.
> ⚠️ What "shipped" does **not** mean: validated to clinical standard. Every generated report
> carries a `limitations` field naming exactly what is still weak — see that table below.

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
│              Stage 2: FDI Assignment (learned head)             │
│              ResNet18 + position → quadrant/position → FDI      │
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
│      Stage 5: Fusion, flags, assessability   ✅ BUILT           │
│      Per-tooth fusion + confidence gating                       │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│      Stage 6: Per-tooth JSON + overlay   ✅ BUILT (no Grad-CAM) │
└─────────────────────────────────────────────────────────────────┘
```

> Diagrams: [`docs/architecture/`](docs/architecture/) —
> `corrected_opg_pipeline_architecture.svg` is the authoritative version.

---

## Pipeline Stages

| Stage | Component | Input | Output | Status |
|-------|-----------|-------|--------|--------|
| 1 | Tooth Detection (YOLOv11l) | Full OPG | Tooth bboxes | ✅ **Complete** — test mAP@0.5 **0.782**; canonical run **frozen** as `tooth-detector-a100-1024-v1.0` (T0.6, 20 Aug 2026) |
| 2 | Sorting + FDI assignment | Tooth bboxes | FDI-keyed tooth list | ✅ **Complete — learned enumeration head** ([validated](scripts/eval/README.md) on 164 leak-free images): quadrant 94.7%, FDI exact **46.5% end-to-end**, up from 22.9% for the positional method it replaced. Universal→FDI table correct (`f8b31f8`). **Pipeline default is now v2.0** (DENTEX+Tufts, adopted for cross-domain robustness — +21.5pp on a second machine population, same 46.5% in-domain). See [`models/README.md`](models/README.md) "Which FDI head to use". |
| 3 | Caries cascade (ResNet18 ×2) | Tight 1.0× crop | caries / deep_caries | ✅ **Complete, gate rebuilt 25 Aug** — `caries-gate-resnet18-v3.0` is the pipeline default, trained on a repaired negative class (5,366 real healthy teeth). In-pipeline caries rate **84.9% → 19.1%**. Held-out precision **0.40** — improved, not solved. |
| 4a | Bone Loss binary (ResNet18) | Expanded 1.5×W/2.0×H crop | Present / Absent | ✅ **Complete** — macro F1 **0.9233** |
| 4b | Bone Loss severity (ResNet18) | Expanded crop | Mild / Moderate / Severe | ✅ **Complete** — macro F1 0.7208 (only 52 val crops) |

| — | CEJ bone-level estimation | Expanded crop | bone loss % | 🔬 Exploratory — 15.1% agreement, **not in the pipeline** |
| 5 | Fusion, flags, assessability | All tooth outputs | Fused per-tooth record | ✅ **Built 24 Aug** — `src/classifiers.py` + `run_inference.py`; positional-alignment guard, confidence gating |
| 6 | Per-tooth JSON + overlay | Fused findings | Report + annotated image | ✅ **Built 24 Aug** — Grad-CAM remains design-only |

> **"Complete" means trained and running end to end — not validated to clinical standard.**
> Tier-0 (T0.1–T0.4) closed 25 Aug. What is still honestly weak, and is written into every
> generated report under `["limitations"]`: caries precision is **0.40**; the bone-loss branch
> **collapses outside Tufts** (fires on 0.7% of DENTEX teeth, 0.8–5.4% affected-tooth
> sensitivity on Ningxia); detector recall **67.0%** caps Stage-2 end-to-end at 46.5%.
> Current state: [`transfer.md`](transfer.md), then
> `docs/research/PUBLICATION_TODO.md` status block.

---

## Current Results

Full tables and provenance: [`docs/results/model_metrics.md`](docs/results/model_metrics.md).

| Model | Dataset | Split | Headline metric |
|-------|---------|-------|-----------------|
| YOLOv11l tooth detection (A100, imgsz 1024, 150 ep) | Tufts | val / **test** | mAP@0.5 0.834 / **0.782** |
| YOLOv11l tooth detection (H200, imgsz 768, 50 ep) — superseded | Tufts | val | mAP@0.5 0.678 |
| FDI enumeration head v2.0 (DENTEX+Tufts, **pipeline default**) | DENTEX / Tufts | 164 leak-free / held-out | end-to-end **46.6%** DENTEX, **71.5%** Tufts (v1.0 DENTEX-only: 46.5% / 50.0%) |
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
| Bbox coordinate format | Corner points, frame-dependent — `[y1,x1,y2,x2]` landscape (bone-loss path) or `[x1,y1,x2,y2]` portrait (FDI numbering path); see `docs/exploration/README.md` Bug 2's note |
| Tooth numbering | Universal (1-32) — converted to FDI, and **left-right mirrored** in the raw data (Tufts "1" = FDI 28, not 18); see `scripts/tufts/README.md` |
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
├── transfer.md                     ← ★ START HERE for a cold session — living state snapshot
├── CLAUDE.md                       ← Working rules for AI/automation sessions in this repo
├── LICENSE  ·  requirements.txt  ·  setup.py  ·  .gitignore
├── app.py                          ← Streamlit deployment demo (wraps run_inference.py)
├── Dockerfile  ·  .dockerignore    ← CPU-only container for the same demo
│
├── configs/
│   └── dataset_config.yaml         ← All paths, hyperparameters, Universal→FDI table
│
├── src/
│   ├── orientation.py              ← Detector input-rotation contract
│   ├── fdi_head_inference.py       ← Stage 2 — the learned enumeration head (current method)
│   ├── classifiers.py              ← Stages 3/4 — caries + bone-loss cascades
│   ├── data_loader.py              ← JSON parsing, coordinate conversion
│   ├── crop_generator.py           ← Expanded crop, jitter, resize
│   ├── label_assigner.py           ← Pixel-overlap ratio, thresholding
│   └── utils/                      ← fdi_converter (incl. Tufts mirror correction), visualization, constants
│
├── scripts/
│   ├── run_inference.py            ← ★ CLI: full six-stage pipeline, OPG in → JSON + overlay out
│   ├── build_dataset.py            ← CLI: build the crop training dataset (legacy bone-loss path)
│   ├── train_model.py              ← CLI: train the bone loss model (legacy bone-loss path)
│   ├── yolo/                       ← Stage 1 detection toolchain (+ its own README)
│   │   ├── convert_tufts_to_yolo.py
│   │   ├── train_yolo.py
│   │   └── evaluate_yolo.py
│   ├── dentex/                     ← Stage 2 head (DENTEX) + Stage 3 caries toolchain (+ README)
│   ├── tufts/                      ← Stage 2 — Tufts as a second FDI corpus (+ README)
│   └── eval/                       ← Evaluation, error propagation, invariant checks (+ README)
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
├── models/                         ← Trained checkpoints + training summaries (see models/README.md)
│   ├── 03_bone_loss_model_training_notebook_models/
│   ├── 04_bone_loss_severity_notebook_models/
│   ├── 05_cej_estimation_v2_models/
│   ├── 06_yolo_detection_a100_run/ ← best.pt/last.pt (git-ignored), args, results.csv
│   ├── 08_fdi_enumeration_head/    ← Stage-2 head v1.0 (DENTEX) — retained, hash-pinned
│   ├── 09_caries_gate_v3/          ← caries gate — current pipeline default
│   └── 10_fdi_head_dentex_tufts_v2/← Stage-2 head v2.0 (DENTEX+Tufts) — current pipeline default
│
├── data/                           ← Datasets and metadata (large files git-ignored)
└── tests/                          ← 65 tests — test_data_loader, test_crop_generator,
                                       test_label_assigner, test_fdi_converter, test_orientation,
                                       test_classifiers, test_fdi_assignment
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

**Just want to run inference?** You don't need any of the dataset layout below — see
[Setting up on a new machine](#setting-up-on-a-new-machine-checkpoints-only) further down.
The Google-Drive layout here is only for **retraining** the bone-loss branch from the original
notebooks (`notebooks/bone_loss/`), which is one specific path through this repo, not the
default one.

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
>
> **⚠️ Tufts licence note:** the dataset's own release agreement forbids re-posting it
> anywhere, including a shared Drive folder without access controls. See
> [`docs/EXTERNAL_DRIVE.md`](docs/EXTERNAL_DRIVE.md) before setting one up.

### Setting up on a new machine (checkpoints only)

To just **run the pipeline** — `run_inference.py`, `app.py`, or the Docker demo — none of the
raw datasets above are needed. Only two model checkpoints are not in git (everything else,
including the current Stage-2 head, is committed):

```bash
git clone <this repo>
pip install -r requirements.txt
# fetch these two from docs/EXTERNAL_DRIVE.md's links — everything else is already in git:
#   models/06_yolo_detection_a100_run/best.pt        (Tufts drive)
#   models/09_caries_gate_v3/caries_gate_v3.pth      (DENTEX drive)
python scripts/eval/verify_invariants.py   # should print "all invariants hold"
python scripts/run_inference.py --image path/to/opg.png --output report.json
```

Full checklist, including what to do if a step fails: [`transfer.md`](transfer.md) §8.

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

### 4. Full pipeline inference

```bash
python scripts/run_inference.py --image path/to/opg.jpg --output report.json
```

**Or the interactive demo** — upload an OPG, see the report and overlay in a browser:

```bash
pip install -r requirements.txt   # includes streamlit
streamlit run app.py
```

`Dockerfile` builds the same app as a container (CPU-only, no GPU needed). Both are a thin
wrapper around `run_inference.py` — no second implementation, so they inherit every limitation
and fix automatically.

This runs all six stages and writes a per-tooth JSON report (add `--overlay viz.jpg` for an
annotated image). Two checkpoints are not in git — see
[`docs/EXTERNAL_DRIVE.md`](docs/EXTERNAL_DRIVE.md) for where to get them.

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
| Phase 5 | Full pipeline integration (Stages 5–6) | Both | ✅ **Complete** — `run_inference.py` runs all six stages; `app.py`/`Dockerfile` deployment demo |
| Phase 6 | Paper writing | Both | ⬜ **Deliberately last** — `PAPER_MATERIAL.md` is structured and ready, but drafting has not started per explicit project sequencing |

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

Tufts *labels look like* Universal numbering (1–32); the clinical report requires FDI. This is
the **standard Universal→FDI table**, and it is correct for standard Universal input — **but
Tufts' own labels are left-right mirrored relative to it** (Tufts "1" is FDI 28, the upper-left
third molar, not FDI 18). Apply `src.utils.fdi_converter.tufts_title_to_fdi()` to Tufts titles,
never this table directly — see `scripts/tufts/README.md` for how that was established.
**Correct** mapping, for genuine Universal input:

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

## Publication Target & Grading Criteria

**Grading rubric for this course project:**

| Grade | Requirement |
|---|---|
| **S** | Publication in a journal, or a conference in its **10th edition or later** |
| **A** | Mid-tier conference, **5th–10th edition** |
| **B** | Newer/lower-tier conference, **1st–5th edition** |
| **C** | No publication secured |

**Senior guidance:** target an IEEE conference with good Scopus indexing for S/A grades.
Verify Scopus coverage on the official Scopus source list before submitting to any specific
venue — a call-for-papers page claiming indexing is not the same as being on that list.

**Named target: IEEE ISBI 2027** — the **24th** International Symposium on Biomedical Imaging,
paper submission deadline **26 Oct 2026** (verified against the official conference site). That
edition count clears the **S**-grade bar. `MASTER_PLAN_2026H2.md` schedules W8 as the
submission window.

**Where this project stands toward that, honestly:** not on the strength of any single model
swap, but on cross-corpus generalisation measured with paired significance tests (something
comparable published work in this space does not do), external validation on four hospitals
never trained on, and a visibly-corrected result (a leaked evaluation set found and fixed
before publication, not after). The current weak point — Stage-2 end-to-end at 46.5%,
capped by detector recall — is the reason R1 (detector retrain) is the top implementation
priority; a second published paper's own numbers independently show the same in-domain/
out-of-domain gap this project measured, which supports the framing rather than undermining it.

**Full assessment, kept current, not duplicated here:** [`transfer.md`](transfer.md) §5.

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
