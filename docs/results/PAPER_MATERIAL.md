# PAPER MATERIAL — master source document

**Purpose.** This is the single document to write the paper from. Everything here is
traceable to a notebook output, a training summary file, or a config in this repo. It is
organised in paper-shaped sections, not in the order the work happened (for chronology see
`RESULTS_LOG.md`).

**Provenance.** Seeded from `docs/reports/legacy/DENTAL_AI_ANALYSIS_REPORT.md` (originally
written as a placement/interview reference), re-verified against the notebooks and
`models/*/`*summary*`.txt` files, and reorganised. Where the legacy document and the raw
artifacts disagreed, the raw artifacts win and the discrepancy is flagged inline.

**Rules for editing this file.** Every number must cite where it came from. If a number is
not in a saved notebook output or a summary file, mark it `[UNVERIFIED]`. Never soften a
limitation to make the work look better — Section 8 exists precisely so reviewers'
questions are answered before they are asked.

**Last updated:** 2026-08-12

---

## Table of contents

1. [Problem Statement](#1-problem-statement)
2. [Related Context](#2-related-context)
3. [Dataset Descriptions](#3-dataset-descriptions)
4. [System Architecture](#4-system-architecture)
5. [Methods](#5-methods)
6. [Key Engineering Decisions](#6-key-engineering-decisions)
7. [Results](#7-results)
8. [Known Limitations](#8-known-limitations--write-these-in-the-paper)
9. [What's not yet written — checklist](#9-whats-not-yet-written--checklist)

---

## 1. Problem Statement

Orthopantomograms (OPGs, panoramic dental radiographs) are the routine first-line imaging
modality in general dentistry: one exposure captures the full dentition, both jaws and the
surrounding alveolar bone. Their interpretation, however, is strongly reader-dependent.
Early enamel/dentin caries and early-to-moderate periodontal bone loss are low-contrast,
small-area findings distributed across ~32 teeth in a single image. Reported consequences
in routine practice are (a) high inter-examiner variability, and (b) systematic
under-detection by junior clinicians and students, who are exactly the readers most likely
to be operating without a specialist second opinion.

Two properties make this a good target for automation:

- The clinical output is **structured and per-tooth**, not per-image. A useful report says
  "tooth 36: caries present, deep; bone loss present, moderate", keyed to the FDI World
  Dental Federation notation that every dentist already uses.
- The two pathologies of interest are visible in **different spatial supports** of the same
  tooth: caries in the crown, bone loss in the alveolar bone apical to the cemento-enamel
  junction. A single whole-image classifier discards that structure; a tooth-centric
  pipeline preserves it.

**Objective.** Given one OPG, automatically localise every tooth, assign FDI numbers, and
emit a filtered per-tooth report of caries (presence, and shallow vs deep) and periodontal
bone loss (presence, and mild/moderate/severe), listing only teeth with findings.

**Constraint that shaped the whole design.** No single public dataset annotates teeth,
caries and bone loss together. The pipeline is therefore deliberately modular, with each
stage trained on the dataset that actually carries its label (Tufts for detection and bone
loss, DENTEX for caries) and joined at inference on the FDI key.

---

## 2. Related Context

*(This section is the thinnest part of the document — see the checklist in Section 9.)*

Source material available in the repo:

- `docs/reports/literature/Survey_paper.pdf` — the survey drafted from the reviewed
  papers (commit `af3b8f6`, 2026-01-31: "reviewed all these research papers to prepare a
  survey paper").
- `docs/reports/literature/Dental X-Ray Capstone Literature Review.xlsx` — the structured
  review sheet; this is the source for the related-work table.
- `_repo_archive/pes_capstone_report/chapters/02_literature.tex` — the literature chapter of
  the LaTeX capstone report, already prose-formatted and reusable. **Archived 2026-08-15**
  out of the tracked tree; also recoverable from git at `6310790`.

Anchors that already influenced this project's design decisions:

- Published Tufts tooth-detection benchmarks (referred to in `scripts/yolo/train_yolo.py`
  and `evaluate_yolo.py` as "Papers 42, 45") report **mAP@0.5 ≥ 0.90** on the Tufts
  detection task. Our A100 run reaches 0.834 val / 0.782 test, i.e. **below** the published
  benchmark — this gap must be stated explicitly in the paper, not omitted.
- CEJ-to-bone-crest distance normalised by root length is the accepted clinical measure of
  periodontal bone loss, but it is defined for periapical radiographs, not OPGs. This
  directly motivated our overlap-based severity proxy (Section 6.2) and is the reason the
  CEJ module stayed exploratory (Section 5.6).

---

## 3. Dataset Descriptions

### 3.1 Tufts Dental Dataset — used for tooth detection and bone loss

| Component | Count | Notes |
|-----------|-------|-------|
| Radiographs | 1,000 | OPG X-rays, **840 × 1615 px, uniform** across the whole set |
| Tooth bounding boxes | 26,005 | across 968 images (`Segmentation/teeth_bbox.json`) |
| Expert free-text reports | 1,000 | radiology diagnoses (`Expert/expert.json`) |
| Expert pathology masks | 439 | 285 empty (normal) + 154 with annotated lesions |
| Working pool with full annotation overlap | 423 images | images where bbox + expert label + mask all join |

Measured dataset characteristics (from `notebooks/bone_loss/01_tufts_data_exploration_v2.ipynb`):

| Property | Value | Consequence for the method |
|----------|-------|----------------------------|
| Image size | 840 × 1615 px, uniform | no pre-crop resizing needed |
| Mean teeth per image | 26.9 | dense scene; detector resolution matters |
| Mean tooth aspect ratio | ~0.35 (≈3× taller than wide) | motivates **asymmetric** crop expansion |
| Michelson contrast | 0.999 | high quality; no global contrast filtering needed |
| Degenerate bboxes | 102 (1 px in one dimension) | filtered before training (`min_bbox_dim: 3`) |
| Deciduous teeth (A–T) | present | pediatric cases in the set; kept for detection |
| Bbox coordinate format | `[y1, x1, y2, x2]` corner points | **not** `[x, y, w, h]` — see bug 2, Section 8.5 |
| Expert mask encoding | per-lesion **instance IDs** | **not** severity classes — killed the U-Net plan |
| Join key across JSONs | nested `External ID` field | not the filename stem — see bug 1, Section 8.5 |
| Tooth numbering | Universal (1–32) | converted to FDI at the detector output |

Derived bone-loss crop dataset (from `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`):

- **22,806** expanded tooth crops built in total.
- Native class imbalance **23.84×** (≈96% normal, ≈4% bone loss).
- After resampling: train = 2,500 normal (undersampled from 17,473) + 711 diseased
  (originals + 2× augmented copies) = **3,211** crops, ratio 3.52×.
- Validation set left **completely untouched** at the real-world distribution:
  1,499 normal + 59 diseased = **1,558** crops.

Derived severity subset (3-class, from `notebooks/bone_loss/04_bone_loss_severity.ipynb`):
**976** train crops / **52** val crops, built only from positive (bone-loss) crops and
labelled by expert-mask overlap ratio.

CEJ experiment subset: **296** positive crops
(`notebooks/bone_loss/05_cej_estimation_v2.ipynb`).

### 3.2 DENTEX — used for caries

Pre-processed per-tooth crop dataset, consumed through `torchvision.ImageFolder`
(`notebooks/caries/phase-1.ipynb`, run on Kaggle from
`dentex-processed-data/processed_dataset`).

| Split / class | Count | Notes |
|---------------|-------|-------|
| Phase 1 train — `caries` | 2,767 | class index 0 |
| Phase 1 train — `no_caries` | 762 | class index 1; class weights `[0.6377, 2.3156]` |
| Phase 2 val (`caries` vs `deep_caries`) | 133 | 101 `caries` + 32 `deep_caries` |

> ⚠️ **Provenance caveat.** The DENTEX train/val counts above come from
> `docs/reports/legacy/DENTAL_AI_ANALYSIS_REPORT.md`. The `Counter(...)` cell that would
> confirm them has **no saved output** in the committed notebook, and the Phase 1 gate's
> own classification report is likewise not present in the saved outputs — only the
> Phase 2 (`caries` vs `deep_caries`) reports survived. Re-run and capture these before
> quoting them in the paper. See Section 9.

---

## 4. System Architecture

Six stages, two parallel analysis branches operating on **different crops of the same
detected tooth box**.

```
                     Input OPG (840 x 1615 px)
                                |
              Stage 1: Tooth detection — YOLOv11l (Tufts)
                                |
              Stage 2: L->R sort, jaw split, Universal->FDI
                    /                             \
        CARIES PATH                                BONE LOSS PATH
   Tight crop (1.0x box)                    Expanded crop (1.5x W, 2.0x H)
   crown region only                        crown + root + alveolar bone
        224x224, ImageNet norm                   224x224, ImageNet norm
              |                                          |
   Stage 3a: ResNet18 gate                  Stage 4a: ResNet18 binary
   caries vs no_caries                      bone loss present/absent
              | (if caries)                            | (if present)
   Stage 3b: ResNet18 severity              Stage 4b: ResNet18 3-class
   caries vs deep_caries                    mild / moderate / severe
                    \                             /
              Stage 5: clinical filter (drop healthy teeth)
                                |
              Stage 6: per-tooth JSON + PDF report (+ Grad-CAM)
```

Authoritative diagram: `docs/architecture/corrected_opg_pipeline_architecture.svg`.

**Stages 5 and 6 are not implemented yet.** The stage boxes above describe the design; the
code that joins the four trained models into one runnable inference does not exist in this
repo. This is the project's actual next milestone.

### Universal → FDI mapping

Tufts uses Universal numbering (1–32); the clinical report requires FDI. Conversion is
applied at the detector output. Full table in `configs/dataset_config.yaml`
(`universal_to_fdi`) and in the root `README.md`.

> ⚠️ **Known defect in the mapping.** `configs/dataset_config.yaml` is wrong for the whole
> lower arch from Universal 23 onward. Correct: 23→32, 24→31, 25–28→41–44, 29–32→45–48.
> Config currently has: 23→43, 24→44, 25–28→45–48, 29–32→31,32,33,34 — which also
> duplicates FDI 33 and 34 (already used by Universal 22 and 21). Every lower-jaw finding
> would be attributed to the wrong tooth. Fix before the pipeline integration and before
> any per-tooth results table goes into the paper. The correct table is in the root
> `README.md`.

---

## 5. Methods

### 5.1 Stage 1 — Tooth detection (YOLOv11l)

- Single-class detection (`tooth`), primary/letter teeth included.
- Annotations converted from Tufts `[y1, x1, y2, x2]` corner boxes to normalised YOLO
  `cx cy w h` (`scripts/yolo/convert_tufts_to_yolo.py`); boxes with w<2 or h<2 dropped;
  unlabelled images skipped.
- Frozen **image-level** 70/15/15 split: 700 train / 150 val / 150 test.
- Backbone `yolo11l.pt` (25.28 M params, 86.6 GFLOPs), AdamW, lr 1e-3 → 1e-5 cosine,
  batch 32, 150 epochs with patience 30, AMP, seed 42.
- **Clinically-valid augmentation only:** horizontal flip 0.5, rotation ±10°, translate
  0.1, scale 0.2, HSV-value 0.2, random erasing 0.4. **No vertical flip** (a flipped jaw is
  anatomically meaningless), **no mosaic**, **no mixup** (both destroy the global jaw
  geometry the detector relies on for tooth ordering).
- Two runs were executed and never reconciled — A100/1024/150ep and H200/768/50ep.
  Details: `notebooks/yolo_detection/README.md`.

### 5.2 Stage 2 — Sorting, jaw split and FDI assignment

Detections are sorted left→right, split into upper/lower jaw, indexed within quadrant, and
mapped Universal→FDI. Implementation: `src/utils/fdi_converter.py`, table in
`configs/dataset_config.yaml`. (See the mapping defect flagged in Section 4.)

### 5.3 Stage 3 — Caries cascade (ResNet18, DENTEX)

A coarse-to-fine **two-stage cascade** rather than one 3-way classifier:

- **Phase 1 (gate):** `caries` vs `no_caries`. ResNet18 pretrained on ImageNet, final FC
  replaced by 512→2, class-weighted `CrossEntropyLoss` (weights `[0.6377, 2.3156]`), Adam,
  images resized to 224×224 with ImageNet normalisation, checkpoint saved on best
  validation **accuracy**.
- **Phase 2 (severity head):** `caries` vs `deep_caries`, reached only if Phase 1 fires.
  Three-step transfer protocol:
  - **A — warm start:** load Phase 1 weights into a fresh ResNet18, then *reset the FC*
    (Phase 1's decision boundary is useless for the new task; only the convolutional
    feature extractor carries over).
  - **B — FC-only training:** freeze the entire backbone, train just the new head for
    5 epochs at lr 1e-3, so a randomly-initialised FC cannot blow up the pretrained
    features with large first-batch gradients.
  - **C — full fine-tune:** unfreeze everything, drop lr to 3e-5, fine-tune end-to-end;
    iterate while re-balancing class weights (`[0.5, 3.5]` → `[0.6, 3.0]`) to trade
    precision against recall on `deep_caries`.
- Rationale for the cascade: on a small dataset, the gate never has to learn the subtle
  shallow-vs-deep boundary and the severity head never spends capacity separating healthy
  from diseased teeth.
- Full narrative, including the author's own honest critique: `notebooks/caries/approach.txt`.

### 5.4 Stage 4a — Bone loss binary (ResNet18, Tufts)

- Input: expanded crop (1.5× W, 2.0× H) resized to 224×224, ImageNet normalisation.
- Labels assigned by **pixel-overlap ratio** against the expert pathology mask
  (Section 6.2), threshold 0.01.
- ResNet18 pretrained, FC 512→2, **Focal Loss** (γ = 2.0, α = `[0.642, 2.258]`),
  Adam (lr 1e-4, wd 1e-4), batch 32, ReduceLROnPlateau (patience 5), early stopping on
  val macro-F1 (patience 10).
- Trained 32/50 epochs, best at epoch 22, 14.8 min wall clock.

### 5.5 Stage 4b — Bone loss severity (3-class ResNet18, Tufts)

- Built only from positive crops. Severity defined by the same overlap ratio:
  **mild** ≤ 0.05, **moderate** 0.05–0.15, **severe** > 0.15.
- ResNet18 pretrained, FC 512→3, Focal Loss (γ = 2.0, per-class α = `[1.694, 0.72, 0.98]`).
- Best at **epoch 2**, 1.6 min wall clock — the model converges (and then overfits) almost
  immediately on 976 training crops.

### 5.6 Exploratory — CEJ-based bone level estimation (classical CV, not in the pipeline)

Deterministic image-processing attempt to approximate the clinical gold standard
(CEJ→bone-crest distance as a fraction of root length), v2 improvements over v1:

1. CLAHE adaptive contrast normalisation + Gaussian blur.
2. Tooth-region isolation (trim top/bottom 10%).
3. Column-wise CEJ detection via intensity valleys, aggregated by median (robust to tilt).
4. Column-wise root-apex detection via local minima (handles curved/cropped roots).
5. Bone-crest search restricted to a narrow window, CEJ → CEJ + 40% root height, to exclude
   molar furcations and the mandibular border.
6. IQR outlier removal across per-column crest estimates.
7. Confidence scoring to flag unreliable estimates for manual review.

Clinical mapping used for comparison: mild < 33% bone loss, moderate 33–50%, severe > 50%.

**This module is not wired into the pipeline and must not be presented as a validated
component** — see Section 7.5 and Section 8.3.

### 5.7 Stages 5–6 — Filtering and report assembly

Designed, not built. Intended behaviour: join the four model outputs on the FDI key, drop
teeth with no finding, and emit a structured JSON plus a PDF summary with Grad-CAM overlays
showing where each classifier looked.

---

## 6. Key Engineering Decisions

These five decisions are the methodological contribution of the project. Keep the exact
numbers — they are what makes each argument checkable.

### 6.1 Asymmetric crop expansion — 1.5× width, 2.0× height

Permanent teeth in this dataset have a **mean aspect ratio of ~0.35**, i.e. roughly three
times taller than wide. Symmetric expansion of the detected box (e.g. 2.0× in both
dimensions) over-expands horizontally and bleeds neighbouring teeth into the crop, while
still under-covering the vertical extent where the alveolar bone level sits. Expanding
**1.5× in width and 2.0× in height** captures crown + root + peri-apical bone with minimal
horizontal contamination. The caries branch, by contrast, uses a **1.0× tight crop**,
because caries is a crown-surface finding and surrounding bone is pure distractor.
Implementation: `compute_expanded_bbox` in
`notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`; parameters
`expand_width: 1.5`, `expand_height: 2.0` in `configs/dataset_config.yaml`.

### 6.2 Pixel-overlap ratio instead of IoU

```
overlap = (expert-mask pixels inside crop) / (crop area)
```

IoU fails structurally here. Expert lesion masks are sparse — a genuine lesion covers only
**0.5–2%** of an expanded crop. With IoU, the union is dominated by crop area, so even true
positives score ≈ 0 and every crop is labelled negative. The overlap ratio removes the
union term entirely. Threshold chosen by plotting the overlap distribution and separating
annotation noise from pathology: **0.01 (1%)**, with a defensible range of 0.005–0.02
(`overlap_threshold` in `configs/dataset_config.yaml`). The same quantity is then reused as
the **severity axis** in Stage 4b (≤0.05 / 0.05–0.15 / >0.15) — the extent of the expert's
annotation is treated as a proxy for how much bone was lost.

### 6.3 Patient-level (image-level) splitting

One OPG yields up to 32 crops sharing exposure, contrast, bone density and acquisition
noise. A crop-level random split puts crops of the *same patient* on both sides of the
train/val boundary, and the model memorises patient-specific appearance instead of
pathology. All crops from one radiograph — **including their jittered and augmented
copies** — are therefore kept in the same split, grouped by the source image stem, with
stratification applied at the image level. The same 70/15/15 image-level split is frozen
and reused for detection.

### 6.4 Resampling for a 23.8× class imbalance

The native bone-loss distribution is ~96% normal / ~4% diseased. Trained as-is, the model
collapses to predicting "normal" and still scores 96% accuracy. Strategy:

- Undersample normal crops to **2,500** (from 17,473), stratified to preserve patient diversity.
- Keep all positive crops and augment (flips, rotations, colour jitter, translations) to
  **711** train positives.
- **Leave the validation set completely untouched** at the real 1,499 / 59 distribution, so
  validation numbers describe clinical reality rather than a rebalanced fiction.
- Add Focal Loss (γ = 2.0) with α = `[0.642, 2.258]` on top, to keep pushing gradient mass
  toward the hard positive cases.

### 6.5 Bounding-box jitter (±15%) to emulate detector noise

The classifiers are trained on crops from ground-truth boxes but will be fed crops from
YOLO predictions, which are systematically a few pixels off. Applying **±15% random
coordinate jitter** at dataset-construction time (`jitter_fraction: 0.15`) forces the
ResNet to learn translation-tolerant features and closes that train/inference distribution
gap. This is the one decision that is **designed for** the not-yet-built integration and
has therefore never been validated end-to-end — see Section 8.4.

---

## 7. Results

All figures for Stage 1 are in `docs/results/figures/yolo_detection_a100/`
(`val_*` = training/validation run, `test_*` = held-out test evaluation).

### 7.1 Stage 1 — YOLOv11l tooth detection (two runs, unreconciled)

| Run | GPU | imgsz | Epochs | Split | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|-----|-----|-------|--------|-------|-----------|--------|---------|--------------|
| **A100** | A100 80GB PCIe | 1024 | 150 req. / 128 run / best ep. 98 | val (150 img, 3,794 inst) | 0.788 | 0.772 | **0.834** | 0.367 |
| **A100** | A100 80GB PCIe | 1024 | " | **test** (150 img, 3,924 inst) | 0.7643 | 0.7421 | **0.7824** | 0.3351 |
| H200 | H200 143GB | 768 | 50 | val (150 img, 3,794 inst) | 0.609 | 0.678 | 0.678 | 0.282 |

- Training wall-clock: A100 0.592 h; H200 0.093 h. Inference ~3.1 ms/image on A100.
- The val→test drop is ~5 mAP@0.5 points — modest, consistent with an honestly held-out split.
- **Insight:** input resolution dominates. 1024 vs 768 is worth ~15 mAP@0.5 points on this
  dense, thin-object scene. Epoch count is secondary to resolution.
- Source: `notebooks/yolo_detection/{a100_1024px_150ep,h200_768px_50ep}.ipynb`,
  `models/06_yolo_detection_a100_run/{run_summary.txt,results.csv,train_args.yaml}`.

### 7.2 Stage 3 — Caries cascade (DENTEX, ResNet18)

**Phase 2 — `caries` vs `deep_caries`, validation (133 crops).** Three successive
fine-tuning attempts are preserved in the notebook outputs; reporting all three is more
honest than reporting only the best.

| Attempt | Accuracy | Macro F1 | `caries` P/R/F1 (n=101) | `deep_caries` P/R/F1 (n=32) |
|---------|----------|----------|--------------------------|------------------------------|
| 1 (cells 106) | 0.80 | 0.73 | 0.87 / 0.86 / 0.87 | 0.58 / 0.59 / 0.58 |
| 2 (cells 114) | 0.77 | 0.72 | 0.92 / 0.76 / 0.83 | 0.51 / 0.78 / 0.62 |
| **3 — best (cells 119)** | **0.81** | **0.77** | 0.94 / 0.80 / 0.87 | 0.57 / **0.84** / 0.68 |

Weighted F1 of the best run: **0.82**. Confusion matrix (best run): `[[81, 20], [5, 27]]`.
The progression is a deliberate precision→recall trade on `deep_caries` driven by the class
weights (`[0.5, 3.5]` → `[0.6, 3.0]`): recall on deep caries rises 0.59 → 0.84 while its
precision stays ~0.57, i.e. the model over-calls deep caries. In a screening tool that is
the correct direction of error, but it must be stated.

**Phase 1 (gate) results are not available** — the saved notebook contains no
classification report for `caries` vs `no_caries`. See Section 9.

### 7.3 Stage 4a — Bone loss binary (Tufts, ResNet18 + Focal Loss)

Validation set: 1,558 crops at the **untouched real-world distribution** (1,499 normal / 59 diseased).

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Accuracy | 98.91% | — | (misleading at 4% prevalence — do not lead with this) |
| **Macro F1** | **0.9233** | ≥ 0.72 | PASS |
| F1 normal (class 0) | 0.9943 (P 0.9933 / R 0.9953) | ≥ 0.75 | PASS |
| **F1 diseased (class 1)** | **0.8522** (P 0.8750 / R 0.8305) | ≥ 0.70 | PASS |
| Sensitivity (diseased recall) | **83.05%** | — | 10 missed positives |
| Specificity (normal recall) | **99.53%** | — | 7 false alarms |

Confusion matrix: TN 1,492 | FP 7 | FN 10 | TP 49. Best epoch 22 of 32 run (of 50 budgeted),
14.8 min training. Source: `models/03_bone_loss_model_training_notebook_models/training_summary.txt`.

This is the strongest result in the project and the one to lead the results section with.

### 7.4 Stage 4b — Bone loss severity, 3-class (Tufts, ResNet18 + Focal Loss)

Validation set: **52 crops**. Best epoch 2, 1.6 min training.

| Severity (overlap ratio) | Precision | Recall | F1 | Support |
|--------------------------|-----------|--------|----|---------|
| Mild (≤ 0.05) | 1.00 | 0.67 | 0.80 | **6** |
| Moderate (0.05–0.15) | 0.80 | 0.57 | 0.67 | 28 |
| Severe (> 0.15) | 0.57 | 0.89 | 0.70 | 18 |
| **Macro F1** | | | **0.7208** | 52 |

Overall accuracy 69.23%. Macro F1 0.7208 clears the 0.72 target by 0.0008 — this is a
**coin-flip margin on 52 samples** and must be reported as "at target", never as "exceeds
target". With 6 mild samples, the mild-class F1 of 0.80 has a confidence interval wide
enough to be uninformative.

> Minor discrepancy for the record: `severity_summary.txt` lists F1 severe = 0.6957 while
> the legacy report rounds it to 0.70. Use 0.6957.

### 7.5 Exploratory — CEJ-based bone level estimation

| Metric | Value |
|--------|-------|
| Crops analysed | 296 (all positive) |
| Processing success rate | **100.0%** (296/296, 0 failures) |
| Flagged "reliable" by confidence score | 185 (**62.5%**) |
| Bone loss % on reliable crops | min 1%, median 2%, mean 5%, max 30% |
| **Exact agreement with overlap-based severity** | **15.1%** |
| Agreement within ±1 severity class | 61.6% |

**How to report this.** "100% success" measures only that the algorithm returned a number
for every crop — it is a **completion rate, not an accuracy**. The meaningful number is
**15.1% exact agreement** with the primary severity label, which is at or below chance for
a 3-class problem. The honest framing is: OPG projection geometry, overlapping anatomy,
crowns/restorations and low local resolution make heuristic CEJ landmark detection
unreliable on panoramic images, which is *why* the overlap-based proxy is used as the
primary severity signal. CEJ estimation stays as a documented negative result and a
motivation for future work (periapical radiographs, or a learned landmark detector).

### 7.6 Summary scoreboard

Single-glance current-best numbers live in `docs/results/model_metrics.md`. Keep the two
files consistent: any change to a metric here must be mirrored there.

---

## 8. Known Limitations — write these in the paper

Reviewers will find these anyway. Stating them first is cheaper than defending them later.

### 8.1 Caries evaluation discipline is thin

From the project's own critique in `notebooks/caries/approach.txt`:

- **Augmentation was defined but never applied.** A `RandomRotation` / `HorizontalFlip` /
  `ColorJitter` pipeline exists in the Phase 2 code, but the dataloaders were built with the
  plain resize+normalise transform. The reported caries numbers come from training on a
  small fixed dataset with **no augmentation**.
- **No learning-rate scheduler.** LR was hand-dropped between stages (1e-3 → 3e-5); no
  StepLR / cosine / ReduceLROnPlateau.
- **No held-out test set.** Tuning and reporting both happen on the same 133-crop validation
  split. The caries numbers are therefore optimistically biased and are *not* comparable to
  the bone-loss numbers, which do come from an untouched split.
- **No early stopping**; fixed epoch counts with "save best val accuracy" as a proxy.
- **Model selection by accuracy on an imbalanced problem** — macro-F1 or minority-class
  recall would be the honest criterion.
- **Phase 1 gate metrics were never saved**, so the cascade's end-to-end error is unknown.

### 8.2 Severity model support is too small to trust

52 validation crops total, **6 of them mild**. Macro F1 0.7208 sits exactly on the 0.72
target. Any conclusion about per-class severity performance from 6 samples is not
statistically meaningful. Needs either more annotated positives or k-fold cross-validation
before it can carry weight in a paper.

### 8.3 CEJ estimation is a negative result, not a component

15.1% exact agreement with the primary label; not integrated into the pipeline; no ground
truth CEJ landmarks exist in the dataset to validate against. Report as exploratory.

### 8.4 The pipeline has never been run end to end

Stages 5 and 6 do not exist as code. Consequently:

- No end-to-end metric exists — only four independently-evaluated stages.
- Error propagation is unmeasured: the classifiers were trained on ground-truth boxes, and
  the detector misses ~23% of teeth on the test split (recall 0.742). The ±15% bbox jitter
  (Section 6.5) is a *mitigation designed for* this, but its effectiveness has never been
  measured on real detector output.
- The Grad-CAM / JSON / PDF report described in the architecture is design, not
  implementation.
- **Any claim of an integrated system in the paper would be unsupported by this repo.**

### 8.5 Detection is below the published benchmark

Test mAP@0.5 = 0.782 vs ≥ 0.90 reported for Tufts in the surveyed literature. Two competing
runs exist and no canonical detector has been frozen. The 768 px run should be retired
explicitly rather than left as an ambiguous alternative.

### 8.6 Label noise from image-level supervision

Bone-loss labels are derived by intersecting a **per-image** expert mask with per-tooth
crops. A tooth crop is called positive when ≥1% of its area overlaps annotated pathology,
but the expert annotated the *lesion*, not the *tooth*. Crops adjacent to a lesion can pick
up a positive label. The spatial overlap criterion is a large improvement over blanket
image-level labelling, but it is still weak supervision.

### 8.7 Small, single-source data and no external validation

423 usable annotated images from a single institution (Tufts), one scanner population, one
annotation protocol; caries from a different dataset (DENTEX) with a different acquisition
distribution. **No external clinical validation, no prospective evaluation, no clinician
reader study.** Domain shift to real clinic OPGs is expected; CLAHE normalisation at
inference is proposed as a mitigation but is untested.

### 8.8 Corrected bugs worth reporting as methodology

These were caught during exploration and are already fixed — they are worth a short
"data engineering" paragraph because each one would have silently destroyed the results
(full detail in `docs/exploration/README.md`):

| Bug | Root cause | Fix | Impact if missed |
|-----|-----------|-----|------------------|
| Zero annotation matches | Join attempted on filename stems; real key is the nested `External ID` field | `Path(item["External ID"]).stem` | zero training samples |
| Crops from wrong locations | Assumed `[x, y, w, h]`; actual format is `[y1, x1, y2, x2]` | swap + subtract corners | every crop wrong; models learn nothing |
| U-Net severity plan invalid | Assumed masks encode severity; they encode **per-lesion instance IDs** | pivot to ResNet18 classification | architecture built on a false premise |
| PIL DecompressionBombError | large composite figures rejected | `MAX_IMAGE_PIXELS = None` | reporting blocked |
| Font download 404 | `wget` returned HTML, not TTF | `apt-get install fonts-dejavu-core` | PDF generation blocked |

---

## 9. What's not yet written — checklist

For whoever drafts the actual paper. Tick items off here as they land.

**Blocking — must be done before submission**

- [ ] Re-run the caries notebook and **save** the Phase 1 gate classification report
      (`caries` vs `no_caries`), plus the `Counter` cell confirming DENTEX class counts.
- [ ] Carve a held-out **test** split for caries and re-report on it (current numbers are
      validation-only and tuned-on).
- [ ] Freeze one canonical detector (A100/1024) and record its weight hash + exact config;
      retire the H200/768 run in writing.
- [ ] Fix the Universal→FDI mapping defect for the lower arch in
      `configs/dataset_config.yaml` (23→32, 24→31, 25–28→41–44, 29–32→45–48), re-verify
      `src/utils/fdi_converter.py` against it, and cover it in `tests/test_fdi_converter.py`.
- [ ] Build Stages 5–6 (integration) and report at least one end-to-end example, or state
      unambiguously in the abstract that the system is evaluated stage-wise only.

**Content still to write**

- [ ] Related Work section — extract from
      `docs/reports/literature/Dental X-Ray Capstone Literature Review.xlsx` and
      `_repo_archive/pes_capstone_report/chapters/02_literature.tex` (archived); build a comparison
      table (paper / dataset / task / reported metric / our result).
- [ ] Formal dataset ethics + licensing statement for Tufts and DENTEX (usage terms,
      de-identification, IRB status).
- [ ] Precise definition of the overlap-ratio severity thresholds as a *proxy* measure,
      with an argument for why 0.05 / 0.15 were chosen (currently undocumented — were they
      tuned or picked by eye?).
- [ ] Ablation: overlap threshold 0.005 / 0.01 / 0.02 on bone-loss binary F1.
- [ ] Ablation: with vs without ±15% bbox jitter, evaluated on **real detector crops**.
- [ ] Ablation: symmetric vs asymmetric (1.5×/2.0×) crop expansion.
- [ ] Runtime/efficiency table for the full pipeline (per-OPG latency, per stage).
- [ ] Failure-case figure panel: the 10 false negatives and 7 false positives from the
      bone-loss confusion matrix, with Grad-CAM.
- [ ] Statistical treatment: confidence intervals or k-fold for every headline metric —
      especially the 52-crop severity model.
- [ ] Figures for Stages 3/4: training curves and confusion matrices are referenced in the
      training summaries as saved to Google Drive but are **not** in this repo. Recover
      them into `docs/results/figures/` or regenerate.

**Nice to have**

- [ ] Reader study or comparison against a junior clinician baseline (the motivating claim
      of the paper is currently unquantified).
- [ ] Calibration analysis (reliability diagram) for the bone-loss classifier.
- [ ] Threshold sweep for the bone-loss decision boundary, reported as a PR curve rather
      than a single operating point.
