# 🦷 Dental AI Pipeline — Automated OPG Analysis

> **Caries Detection & Bone Loss Detection from Panoramic Dental X-rays**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-In%20Progress-yellow.svg)]()

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Pipeline Stages](#pipeline-stages)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Phase Status](#phase-status)
- [Key Design Decisions](#key-design-decisions)
- [Known Bugs & Fixes](#known-bugs--fixes)
- [Evaluation Targets](#evaluation-targets)
- [Risks & Mitigations](#risks--mitigations)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project builds a **fully automated dental diagnostic system** that takes a single **OPG (Orthopantomogram) X-ray** as input and produces a **structured per-tooth clinical report** identifying:

- **Caries** — presence (Yes/No) and severity (Mild / Moderate / Severe)
- **Bone Loss** — presence (Present / Absent)

Each finding is mapped to the affected tooth using **FDI numbering** (international standard). Only affected teeth appear in the final report.

### Final Output Format

```
Tooth [FDI Number]
  → Caries: Yes | Severity: Moderate
  → Bone Loss: Present

Tooth [FDI Number]
  → Caries: No
  → Bone Loss: Present
```

---

## System Architecture

The system processes an OPG through a **six-stage pipeline**, with two parallel analysis branches (caries and bone loss) running on different crop types from the same tooth bounding box.

```
┌─────────────────────────────────────────────────────────────────┐
│                        OPG X-ray Input                         │
│                        (840 × 1615 px)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stage 1: Tooth Detection (YOLOv8/v11)             │
│              Output: Per-tooth bounding boxes                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stage 2: Sorting & FDI Assignment                 │
│              Left→Right sort, jaw split, Universal→FDI         │
└──────────┬───────────────────────────────────────┬──────────────┘
           │                                       │
           ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────────┐
│   CARIES PATH        │              │   BONE LOSS PATH         │
│                      │              │                          │
│  Tight Crop (1.0×)   │              │  Expanded Crop           │
│  Crown-focused       │              │  (1.5× W, 2.0× H)       │
│       │              │              │  Crown + root + bone     │
│       ▼              │              │       │                  │
│  Resize 224×224      │              │       ▼                  │
│  ImageNet normalize  │              │  Resize 224×224          │
│       │              │              │  ImageNet normalize      │
│       ▼              │              │       │                  │
│  ResNet18 Binary     │              │       ▼                  │
│  (Caries Yes/No)     │              │  ResNet18 Binary         │
│       │              │              │  (Bone Loss Yes/No)      │
│       ▼ (if Yes)     │              │                          │
│  ResNet18 Severity   │              │                          │
│  (Mild/Mod/Severe)   │              │                          │
└──────────┬───────────┘              └──────────┬───────────────┘
           │                                      │
           └──────────────┬───────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stage 5: Filter & Report Assembly                 │
│              Keep only: caries=YES OR bone_loss=PRESENT        │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Structured Dental Report                     │
└─────────────────────────────────────────────────────────────────┘
```

> See [`docs/flowcharts/`](docs/flowcharts/) for the full visual pipeline flowchart.

---

## Pipeline Stages

| Stage | Component | Input | Output | Status |
|-------|-----------|-------|--------|--------|
| 1 | Tooth Detection | Full OPG | Tooth bboxes + position index | 🟡 In Progress |
| 2 | Tight Crop | Tooth bbox × 1.0 | 224×224 crown crop | ✅ Complete |
| 3 | Caries Model | Tight crop | Caries Yes/No + Severity | ✅ Complete |
| 4 | Expanded Crop | Tooth bbox × 1.5W/2.0H | 224×224 bone-visible crop | ✅ Complete |
| 5 | Bone Loss Model | Expanded crop | Bone loss Present/Absent | 🟡 In Progress |
| 6 | Filter + Report | All tooth outputs | Final structured report | ⬜ Planned |

---

## Dataset

### Tufts Dental OPG Dataset

| Component | Count | Description |
|-----------|-------|-------------|
| Radiographs | 1,000 | OPG X-rays (840 × 1615 px, uniform) |
| Tooth Bounding Boxes | 26,005 | Per-tooth annotations across 968 images |
| Expert Reports | 1,000 | Free-text radiology diagnoses |
| Expert Pathology Masks | 439 | 285 empty (normal) + 154 annotated |
| Working Training Pool | 423 | Images with full annotation overlap |

### Dataset Characteristics

| Metric | Value |
|--------|-------|
| Image size | 840 × 1615 px (uniform) |
| Avg teeth per image | 26.9 |
| Tooth aspect ratio | ~0.35 (3× taller than wide) |
| Michelson contrast | 0.999 (high quality) |
| Class imbalance | 1.85× (moderate) |
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
dental-ai-pipeline/
│
├── README.md                          ← You are here
├── LICENSE
├── requirements.txt                   ← Python dependencies
├── .gitignore
├── setup.py                           ← Package setup (optional)
│
├── configs/
│   └── dataset_config.yaml            ← All hyperparameters & paths
│
├── notebooks/
│   ├── 01_data_exploration.ipynb      ← Tufts dataset exploration (Phase 4)
│   ├── 02_dataset_construction.ipynb  ← Build training dataset (current step)
│   ├── 03_model_training.ipynb        ← ResNet18 training (next step)
│   └── 04_evaluation.ipynb            ← Model evaluation & analysis
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py                 ← JSON parsing, coordinate conversion
│   ├── crop_generator.py              ← Expanded crop, jitter, resize
│   ├── label_assigner.py              ← Pixel-overlap ratio, thresholding
│   ├── dataset_builder.py             ← Main construction pipeline
│   ├── validation.py                  ← Visual validation, integrity checks
│   ├── model.py                       ← ResNet18 architecture
│   ├── train.py                       ← Training loop
│   ├── evaluate.py                    ← Metrics, confusion matrix
│   ├── inference.py                   ← Single-image inference
│   └── utils/
│       ├── __init__.py
│       ├── fdi_converter.py           ← Universal → FDI tooth numbering
│       ├── visualization.py           ← Plotting utilities
│       └── constants.py               ← Shared constants
│
├── scripts/
│   ├── build_dataset.py               ← CLI: build training dataset
│   ├── train_model.py                 ← CLI: train bone loss model
│   └── run_inference.py               ← CLI: run full pipeline on OPG
│
├── docs/
│   ├── reports/
│   │   ├── project_report.pdf         ← Full project report
│   │   └── data_exploration.pdf       ← Tufts exploration report
│   ├── flowcharts/
│   │   └── pipeline_flowchart.svg     ← System architecture diagram
│   └── exploration/
│       └── README.md                  ← Notes on dataset quirks & bugs
│
├── models/                            ← Trained model checkpoints
│   ├── .gitkeep
│   └── README.md
│
├── data/                              ← Processed datasets (git-ignored)
│   ├── .gitkeep
│   └── README.md
│
├── outputs/                           ← Inference outputs (git-ignored)
│   ├── .gitkeep
│   └── README.md
│
└── tests/
    ├── test_data_loader.py
    ├── test_crop_generator.py
    ├── test_label_assigner.py
    └── test_fdi_converter.py
```

---

## Setup & Installation

### Prerequisites

- Python 3.8+
- CUDA-compatible GPU (recommended for training)
- Google Colab / Kaggle (with GPU runtime)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/dental-ai-pipeline.git
cd dental-ai-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Colab Setup

```python
# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Clone repo into Colab
!git clone https://github.com/<your-username>/dental-ai-pipeline.git
%cd dental-ai-pipeline
!pip install -r requirements.txt
```

### Dataset Setup

The Tufts Dental Dataset should be placed in your Google Drive:

```
Google Drive/
  tufts/
    ZIP/
      Radiographs/Radiographs/     ← OPG images (.JPG)
      Segmentation/Segmentation/   ← teeth_bbox.json, teeth_polygon.json
      Expert/Expert/               ← expert.json
      Expert/Expert/mask/          ← Expert pathology masks (.JPG)
```

> Update the `BASE` path in `configs/dataset_config.yaml` to match your drive mount.

---

## Usage

### 1. Build Training Dataset

Open `notebooks/02_dataset_construction.ipynb` in Colab and run all cells sequentially:

```
Cell 1-2:   Mount drive, configure paths
Cell 3-5:   Load expert labels, bboxes, masks
Cell 6:     Join sources, clean bboxes
Cell 7:     Define core functions
Cell 8:     Build dataset (main loop)
Cell 9:     Analyze overlap threshold ← REVIEW THIS
Cell 10:    Stratified train/val split
Cell 11:    Save to disk
Cell 12:    Visual validation ← REVIEW THIS
Cell 13-14: Integrity checks
Cell 15:    Final summary
```

**Critical checkpoints:**
- After Cell 9: Review overlap distribution plots. Adjust `OVERLAP_THRESHOLD` if needed.
- After Cell 12: Review visual validation. If labels don't match pathology, adjust threshold and rerun from Cell 8.

### 2. Train Model (Next Phase)

```python
# After dataset construction is validated
python scripts/train_model.py --config configs/dataset_config.yaml
```

### 3. Run Inference (Future)

```python
# Full pipeline inference on a single OPG
python scripts/run_inference.py --image path/to/opg.jpg --output report.json
```

---

## Phase Status

| Phase | Description | Owner | Status |
|-------|-------------|-------|--------|
| Phase 1 | Caries Detection (ResNet18 binary) | Collaborator | ✅ Complete |
| Phase 2 | Caries Severity (ResNet18 3-class) | Collaborator | ✅ Complete |
| Phase 3 | Tooth Detection (YOLO) | Separate | 🟡 In Progress |
| Phase 4a | Bone Loss — Data Exploration | Deepak | ✅ Complete |
| Phase 4b | Bone Loss — Dataset Construction | Deepak | 🟡 In Progress |
| Phase 4c | Bone Loss — Model Training | Deepak | ⬜ Planned |
| Phase 4d | Bone Loss — Evaluation | Deepak | ⬜ Planned |
| Phase 5 | Full Pipeline Integration | Both | ⬜ Planned |

---

## Key Design Decisions

### 1. Pixel-Overlap Ratio Instead of IoU

```
overlap = mask_pixels_inside_crop / crop_area
```

**Why not IoU?** Expert mask blobs are tiny sparse lesion annotations. Expanded crop bboxes are large (crown + root + bone). IoU = intersection / union ≈ tiny / large ≈ near zero. Even true positives get IoU ≈ 0, causing systematic false negatives.

**Threshold:** 0.005–0.02 (0.5%–2%). Even a genuine lesion occupies only a small fraction of the expanded crop area.

### 2. Asymmetric Crop Expansion (1.5× W, 2.0× H)

Teeth have a mean aspect ratio of ~0.35 (3× taller than wide). Equal expansion in both directions causes horizontal over-expansion that bleeds into adjacent teeth. More vertical expansion captures the alveolar bone below the root, which is exactly where bone loss is visible.

### 3. Binary Classification Instead of Severity Segmentation

U-Net severity segmentation was ruled out because:
- Expert masks encode **per-lesion instance IDs**, not severity classes
- No pixel-level mild/moderate/severe annotation exists in the dataset
- Only 154 annotated samples — insufficient for U-Net from scratch
- CEJ estimation requires ground truth points that don't exist

### 4. Image-Level Train/Val Split

All crops from the same radiograph (including jittered copies) stay in the same split. Splitting at the crop level would leak information between train and val through augmented copies of the same tooth.

### 5. Bbox Jitter for YOLO Noise Simulation

During training, crops come from ground-truth bounding boxes. At inference, they come from YOLO predictions with slight position errors. Adding ±15% random jitter during training teaches the model to be robust to imperfect crop boundaries.

---

## Known Bugs & Fixes

These bugs were discovered during data exploration and are **already fixed** in all code:

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Coverage matrix showed 0 matches | Code compared filename stems against dict keys; actual join field is nested `External ID` | Extract `Path(item['External ID']).stem` as join key |
| All crops extracted from wrong locations | Assumed bbox format `[x, y, w, h]`; actual format is `[y1, x1, y2, x2]` | Convert: `w = x2-x1`, `h = y2-y1`, swap x and y |
| U-Net architecture selected prematurely | Assumed expert masks encode severity classes; pixel values are actually per-lesion instance IDs | Changed to binary ResNet18 classifier |
| PIL DecompressionBombError | PIL rejected large composite figures as security threats | Set `PILImage.MAX_IMAGE_PIXELS = None` |
| Font download 404 | wget from GitHub returned HTML page instead of TTF binary | Use `apt-get install fonts-dejavu-core` |

---

## Evaluation Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Class 0 F1 (normal) | ≥ 0.75 | Avoid false positives in clinical report |
| Class 1 F1 (bone loss) | ≥ 0.70 | Clinical sensitivity requirement |
| Macro F1 | ≥ 0.72 | Overall model quality |
| Accuracy | Secondary | Misleading with imbalanced data |

### Training Configuration

| Parameter | Value |
|-----------|-------|
| Architecture | ResNet18 pretrained (ImageNet) |
| Final layer | FC: 512 → 2 (binary) |
| Loss | CrossEntropyLoss with class weights |
| Optimizer | Adam, lr=1e-4 |
| Scheduler | ReduceLROnPlateau (patience=5) |
| Batch size | 16 |
| Epochs | 50 (early stopping on val F1, patience=10) |
| Augmentation | H-flip, brightness jitter, rotation ±10°, bbox jitter ±15% |
| Normalization | ImageNet mean/std |

---

## Risks & Mitigations

| Risk | Level | Mitigation |
|------|-------|------------|
| Small training set (423 images) | HIGH | Heavy augmentation, transfer learning from ImageNet |
| Image-level labels → noisy per-crop assignment | MEDIUM | Spatial overlap with expert mask (not blanket labeling) |
| YOLO crop variability at inference | MEDIUM | ±15% bbox jitter during training |
| Moderate class imbalance (1.85×) | LOW-MED | Weighted loss, stratified split, per-class F1 monitoring |
| Universal vs FDI numbering mismatch | HIGH | Conversion table at YOLO output stage |
| Domain shift (Tufts vs real OPGs) | MEDIUM | CLAHE normalization at inference |

---

## Universal to FDI Conversion

The Tufts dataset uses Universal numbering (1-32). The final report requires FDI. Conversion is applied at the YOLO output stage:

| Universal | FDI | Universal | FDI | Universal | FDI | Universal | FDI |
|-----------|-----|-----------|-----|-----------|-----|-----------|-----|
| 1 | 18 | 9 | 21 | 17 | 38 | 25 | 45 |
| 2 | 17 | 10 | 22 | 18 | 37 | 26 | 46 |
| 3 | 16 | 11 | 23 | 19 | 36 | 27 | 47 |
| 4 | 15 | 12 | 24 | 20 | 35 | 28 | 48 |
| 5 | 14 | 13 | 25 | 21 | 34 | 29 | 31 |
| 6 | 13 | 14 | 26 | 22 | 33 | 30 | 32 |
| 7 | 12 | 15 | 27 | 23 | 43 | 31 | 33 |
| 8 | 11 | 16 | 28 | 24 | 44 | 32 | 34 |

---

## Contributing

This is a capstone project. Contributions follow this workflow:

1. Create a feature branch: `git checkout -b feature/bone-loss-training`
2. Make changes and test
3. Commit with descriptive messages: `git commit -m "Add overlap threshold analysis"`
4. Push and open a pull request

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

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **Tufts Dental Dataset** — Multi-annotator OPG radiograph collection
- **PyTorch** and **torchvision** — Model architecture and training
- **Ultralytics** — YOLOv8/v11 for tooth detection

---

<p align="center">
  <strong>Dental AI Pipeline</strong> — Capstone Project 2026
</p>
