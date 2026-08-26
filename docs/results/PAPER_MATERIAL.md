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

**Last updated:** 2026-08-22

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
- **Why YOLOv11, not a newer YOLO generation:** verified against
  [Mutlu et al., "Comparison of YOLOv11 and YOLOv12," *Odontology* (2026)](https://doi.org/10.1007/s10266-026-01333-3),
  a head-to-head benchmark on 13 dental conditions from panoramic radiographs (2,297 images,
  internal + external Roboflow test sets). YOLOv11 beat YOLOv12 on both splits (mAP@0.5 0.857
  internal / 0.806 external) and was named the more robust architecture for multi-class dental
  detection. The same paper independently reports weaker performance on subtle pathology (bone
  loss, caries) versus well-defined objects (crowns, implants) — the identical asymmetry this
  project's own evaluation plan is built around (see `../research/MASTER_PLAN_2026H2.md` §2.2).
  This is external validation of the backbone choice, not just internal justification.

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

These seven decisions are the methodological contribution of the project. Keep the exact
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

### 6.6 Mask-aware cropping (R2) — soft attenuation, not hard masking

Implemented 19 Aug 2026 (`extract_mask_aware_crop`, `rasterize_polygon`,
`extend_mask_below_root`, `apply_soft_mask_attenuation` in `src/crop_generator.py`,
tested in `tests/test_crop_generator.py`), ahead of having real Tufts instance masks to run
it against. **Update, 20 Aug 2026:** real masks (`teeth_polygon.json`) are now available and
verified (§6.7/T0.6 status, `docs/research/T0.6_detector_reconciliation.md` §3) — this
function has not yet been re-run against them (that requires wiring it into the bone-loss
crop pipeline, not attempted today), but the blocker that motivated "ahead of having" is
resolved. The design problem: a rectangular expanded crop
(Section 6.1) pulls in neighbouring teeth, which the asymmetric 1.5×/2.0× ratio only
*mitigates*, not eliminates. Once per-tooth instance masks exist (T0.6/R1), neighbouring-tooth
pixels can be suppressed directly — but **soft** attenuation (default: dim to 50% outside the
mask, never zero), not a hard cutout, for two reasons: (1) a noisy mask edge degrades
gracefully instead of erasing real signal, and (2) the periodontal branch needs bone context
*below* the tooth root, which a raw instance mask does not cover (masks stop at the tooth
surface). `extend_mask_below_root` explicitly extends the kept region downward, within the
tooth's own column span, before attenuation is applied, so this bone context is preserved
rather than treated as "background." This becomes ablation C5's fourth cell (rectangular vs.
mask-aware crop) once masks and a retrained instance-segmentation detector exist.

### 6.7 Uniform model-selection criterion and operating threshold across all four classifiers (T0.3)

**Checkpoint-selection criterion, made uniform 19 Aug 2026:** all four classifiers — caries
gate, caries severity, bone-loss binary, bone-loss severity — now select their "best" epoch
by **validation macro-F1**, not raw accuracy. Bone-loss binary and severity already did this
correctly (`f1_score(..., average='macro')`, unchanged this session). The caries notebook
(`notebooks/caries/phase-1.ipynb`) did not — all five of its training-loop cells compared on
`val_acc`, which on an imbalanced problem rewards a model that leans toward the majority
class. Fixed by making every `validate()` definition in that notebook also compute and
return macro-F1, and every checkpoint condition compare on it instead. This is the same
criterion `configs/dataset_config.yaml` already declared
(`training.early_stop_metric: "val_f1_macro"`) but the caries notebook never actually read
that config file. Not chosen as an alternative: minority-class recall alone — macro-F1 was
picked to keep one consistent, documented criterion across all four models rather than a
different one per model, and because it already matched three of the four before this fix.

**Operating threshold, as it stands today:** every classifier here is a softmax network read
out with `torch.argmax`, not a calibrated, tunable decision threshold. For the three binary
classifiers (caries gate, caries `caries`-vs-`deep_caries`, bone-loss present/absent), argmax
on a 2-class softmax is mathematically equivalent to a **fixed 0.5 probability threshold on
the positive class** — not chosen for a) any particular precision/recall trade-off, or b)
picked by any search over val; it is simply what falls out of using
`CrossEntropyLoss` + argmax with no further calibration step. For bone-loss severity
(3-class), there is no single scalar threshold in the same sense — argmax picks whichever of
the three classes has the highest predicted probability. **No threshold search or
calibration has been run on any of the four models.** This is a real, named gap, not an
oversight to paper over: `docs/research/MASTER_PLAN_2026H2.md` §3 R3 (temperature scaling +
an explicit `not_assessable` abstention output, reported as a coverage–accuracy curve) is the
already-planned fix, scheduled for Week 6, not Week 2. Report the current threshold as
"uncalibrated 0.5-equivalent argmax" wherever these models are described until R3 lands.

---

## 7. Results

All figures for Stage 1 are in `docs/results/figures/yolo_detection_a100/`
(`val_*` = training/validation run, `test_*` = held-out test evaluation).

### 7.1 Stage 1 — YOLOv11l tooth detection (reconciled and frozen, A100 run canonical)

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
- **Reconciliation status (19–20 Aug 2026, T0.6):** the A100 config above is now formally
  declared canonical going forward (data-justified — see
  `docs/research/T0.6_detector_reconciliation.md`), and `scripts/yolo/train_yolo.py` was
  corrected to reproduce it exactly (it had drifted: batch 16 vs. the real run's 32). **The
  weights are now frozen** (20 Aug 2026) — `best.pt`/`last.pt` located in
  `_repo_archive/yolo_a100_run_workspace/`, verified (byte-identical `args.yaml`/`results.csv`
  against the committed copies, loads cleanly under Ultralytics with the documented param
  count), and copied into `models/06_yolo_detection_a100_run/`. Version tag
  `tooth-detector-a100-1024-v1.0`, SHA-256 in `docs/research/T0.6_detector_reconciliation.md`
  §1 and `model_metrics.md`. This table's heading can drop "unreconciled" now — updated below.
  A YOLOv11l-seg retrain (R1) is still planned with a pre-registered acceptance criterion
  (same document). **Update, later on 20 Aug 2026:** `teeth_polygon.json` and all 1,000 raw
  Tufts radiographs were located (Google Drive) and the conversion pipeline
  (`scripts/yolo/convert_tufts_to_yolo_seg.py`) was run end-to-end against them successfully
  — see `docs/research/T0.6_detector_reconciliation.md` §3. **Update, 21 Aug 2026:** the
  frozen `outputs/eda_tufts/split_v1.csv` — reported missing on 20 Aug and treated as the
  last blocker — was found on the macOS machine and verified to be the split behind this
  table's numbers (its per-split filename lists diff to zero against the built dataset the
  A100 run trained on). The real `dataset_seg/` has now been built from it: 26,005 instances
  over the same 700/150/150 images. **R1 has no remaining data blockers, only GPU access.**
  That build also surfaced a data-quality defect in the bbox dataset underlying this very
  table — 66 real teeth silently dropped on corrupt `bounding box` fields, 6 of them in the
  test set; see §8.9, which is where it should be reported in the paper. Crop re-derivation
  from the frozen detector is separately still blocked — it needs the raw images too, which
  are now available, but no inference has been run yet.

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

**Status (19 Aug 2026, T0.2/T0.3):** two of the five items above have code fixes prepared but
**not yet re-run**, so every number in Section 7.2 still describes the old, uncorrected
training: (1) checkpoint selection in `notebooks/caries/phase-1.ipynb` now computes and
selects on macro-F1 rather than raw accuracy (all `validate()` definitions and training-loop
cells updated); (2) `scripts/dentex/split_dentex_holdout.py` carves a held-out test split
from the existing val/ pool, grouped by source-image ID to avoid crop-level leakage — but
since no patient ID or raw DENTEX exists in this repo, it is a split *of val*, not an
independent three-way split, and that distinction must be stated in the paper's methods, not
glossed over. Augmentation and LR-scheduler gaps remain untouched. The cascade needs an
actual re-run (Kaggle/H100, not available in the environment these fixes were written in)
before Section 7.2's numbers can be replaced.

**Update (21 Aug 2026) — the held-out-split item is now structurally fixed, and the
carve-from-val compromise above is withdrawn.** The raw disease-labelled DENTEX subset (705
source X-rays, original COCO annotations) turned out to be available, so the split was rebuilt
from scratch instead: `scripts/dentex/build_dentex_split_from_raw.py` draws a 70/15/15
**image-level** split (train 495 / val 103 / test 107), stratified on each image's 4-bit
disease presence-vector so the rare Periapical Lesion class (158 annotations) is spread
115/21/22 rather than landing by luck. Because the split is drawn on source images *before any
crop is generated*, crop-level leakage is structurally impossible rather than merely avoided —
every crop inherits its source image's split. Verified: zero overlap on all three pairs,
705/705 images and 3,529/3,529 annotations accounted for, manifest byte-identical on re-run.
`scripts/dentex/split_dentex_holdout.py` is retired.

Two honest qualifications remain. **First, DENTEX ships no patient or study identifier**, so
one image is treated as one patient; if the source data contains multiple radiographs of the
same patient, that grouping cannot be recovered and a residual leak is possible. This is the
strongest guarantee the data supports and the paper should say so in exactly those terms.
**Second, nothing has been retrained yet** — §7.2's numbers still describe the old,
uncorrected training on the old split. The manifest (`data/dentex/splits_v2.json`) is an
input, not a result. The remaining §8.1 items — augmentation never applied, no LR scheduler,
no early stopping, unsaved Phase 1 gate metrics — are all untouched and all still need the
re-run.

### 8.2 Severity model support is too small to trust

52 validation crops total, **6 of them mild**. Macro F1 0.7208 sits exactly on the 0.72
target. Any conclusion about per-class severity performance from 6 samples is not
statistically meaningful. Needs either more annotated positives or k-fold cross-validation
before it can carry weight in a paper.

### 8.3 CEJ estimation is a negative result, not a component

15.1% exact agreement with the primary label; not integrated into the pipeline; no ground
truth CEJ landmarks exist in the dataset to validate against. Report as exploratory.

A further iteration exists in the codebase — `notebooks/bone_loss/06_cej_estimation_v3.ipynb`
("v3, calibrated": strongest-gradient boundary detection, tighter search zone, left/right
asymmetric bone analysis, artifact-column exclusion, and overlap-label calibration). **It has
never actually run against real data** — its last saved execution shows `Crops to analyze: 0`
(the Colab Drive path it reads, `/content/drive/MyDrive/tufts/severity_dataset`, was empty or
unmounted at run time), so every downstream number in it is `N/A`. Triaged and committed
2026-08-20 as prepared-but-unexecuted future work, not a second data point — do not cite it
as having improved on, matched, or failed to match the 15.1% figure above; it simply hasn't
been run.

### 8.4 The pipeline has never been run end to end

**RESOLVED 24 August 2026.** `scripts/run_inference.py` now runs all six stages
(RESULTS_LOG 2026-08-24f) — this is R4 / paper claim C3. The specific claims below describe
the state as of 22 August and are kept for the audit trail; **the heading and first sentence
are no longer true.** What replaced each point: an end-to-end metric exists (299-tooth batch
run, 0 duplicate FDI codes; 25 Aug's lesion-localization run below); error propagation is now
partially measured (the caries gate's 84.9%→19.1% in-pipeline correction, RESULTS_LOG
2026-08-25a, is itself an error-propagation number); Grad-CAM remains design-only, unlike the
JSON report which now exists. Text below unedited except this note, per the project's
never-rewrite-a-past-claim convention.

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
| Crops from wrong locations | Assumed `[x, y, w, h]`; actual format is corner points, not offset+size | swap + subtract corners | every crop wrong; models learn nothing |
| U-Net severity plan invalid | Assumed masks encode severity; they encode **per-lesion instance IDs** | pivot to ResNet18 classification | architecture built on a false premise |
| PIL DecompressionBombError | large composite figures rejected | `MAX_IMAGE_PIXELS = None` | reporting blocked |
| Font download 404 | `wget` returned HTML, not TTF | `apt-get install fonts-dejavu-core` | PDF generation blocked |

**Which frame those corner points live in — corrected 25 Aug 2026.** The row above previously
wrote the format as `[y1, x1, y2, x2]`, which is how
`notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb` reads it against the **landscape**
`Radiographs/` images. That is the exact horizontal **mirror** of the correct reading: the
numbers are `[x1, y1, x2, y2]` in the **portrait** frame (840×1615, `Radiographs_rotated/`),
which is what the detector's own converter used and what `src/orientation.py` documents.
Measured against detector boxes over 1,022 teeth, the portrait reading scores mean IoU **0.611**
against the landscape reading's **0.489**; and drawing the raw numbers on the portrait image
with no conversion at all places every box tightly on a tooth, which is only possible in the
portrait frame. The bone-loss models are unaffected — that notebook cuts image and mask from
the same frame at the same coordinates, so each crop carries the label of the tooth actually
inside it, and its only identity-derived use of `tooth_id` (`is_deciduous`) is mirror-invariant.
RESULTS_LOG 2026-08-25h.

### 8.8b Tufts' tooth numbering is mirrored — and it is now a usable second FDI corpus

Tufts `title` values look like Universal numbers and their within-arch ordering is correct, but
**which side of the patient each denotes is inverted**: Tufts `"1"` is FDI **28** (upper left),
not 18. Reading them as plain Universal would have trained the Stage-2 head on systematically
side-swapped labels — silently, with no error anywhere. Established three independent ways (an
`L` side-marker; a DENTEX-trained arbiter scoring 91.7% mirrored vs 6.1% direct over 1,188
matched teeth; and a DENTEX control at 98.6% direct proving the arbiter itself is sound), then
confirmed dataset-wide: after correction, Q1 mean cx **0.390** vs Q2 **0.603**, against DENTEX's
0.400/0.606, with |cx−0.5| rising monotonically 0.015→0.236 across positions 1–8.

Worth reporting as methodology: it is a concrete case where a public dataset's labels are
self-consistent and anatomically plausible yet globally reflected, and where no
single check — not anatomy (the jaw is symmetric), not a visual overlay (a mirrored box still
lands on a tooth) — could have caught it alone.

The corrected corpus is built (**42,755 crops, 25,201 usable permanent teeth vs DENTEX's
18,095**) but **no model has been retrained on it**; that remains an open experiment, with two
known hazards: a covariate shift in the positional features (median normalised tooth height
0.177 vs DENTEX's 0.231) and Tufts contributing 2.0× DENTEX's training rows.
RESULTS_LOG 2026-08-25h; `scripts/tufts/README.md`.

### 8.9 The detection ground truth itself is missing 66 annotated teeth

Found 21 August 2026, while building the segmentation dataset on the same frozen split as
the detector. `teeth_polygon.json` and `teeth_bbox.json` describe the **same objects** for
all 1,000 Tufts images — verified, no image differs in object count. But for 66 of those
objects the `bounding box` field is corrupt, recorded as 1×1 or 1×2 px, while the polygon for
the same object is intact and full-size (1,617–13,425 px², up to 682 vertices, ordinary
Universal tooth titles spread across both arches; three were rendered over the radiograph and
are unmistakably real teeth). Our bbox converter drops objects under 2 px on a side as
degenerate — a reasonable guard that, on this data, silently removes 66 correctly annotated
teeth: **47 from train, 13 from val, 6 from test.**

Two consequences worth stating plainly in the paper:

1. The reported Stage-1 numbers (§7.1) were measured against test ground truth containing
   3,924 of the 3,930 annotated teeth. At 0.15% of instances this cannot meaningfully move
   mAP@0.5 = 0.7824 — but any tooth the detector correctly found among those 6 was scored as
   a false positive.
2. The segmentation dataset built for R1 **keeps** all 66, because they are valid
   annotations. Its test ground truth therefore holds 3,930 instances against the bbox
   set's 3,924, so the seg-vs-bbox box-mAP comparison in R1's pre-registered criterion is
   near-like-for-like rather than exactly like-for-like. This was recorded in
   `docs/research/T0.6_detector_reconciliation.md` §2 *before* the retrain was run, and the
   acceptance bar was not adjusted for it.

The bbox converter was deliberately left unfixed: correcting it would invalidate the frozen
canonical detector's reproducibility. The right framing for the paper is a public-dataset
annotation-quality finding, not a bug we introduced — it argues for deriving boxes from
polygons where both exist, which is what the seg pipeline effectively does.

---

### 8.10 FDI numbering was the pipeline's weakest link — measured, then fixed

Measured 22 August 2026 against the 1,534 FDI-labelled teeth in DENTEX `disease/` — the first
Stage-2 evaluation this project has ever run. **End-to-end FDI exact accuracy is 28.0%.**

> **Both figures in that sentence are superseded.** 34% of those 250 images turned out to be
> training duplicates (§8.10 continues below; RESULTS_LOG 2026-08-22j). On the clean 164-image
> subset the same positional method scores **22.9% on 936 teeth**. The 1,534-teeth denominator
> and the 28.0% belong to the contaminated set and are kept here only because the *diagnosis*
> in this paragraph — that the position digit is what breaks — was derived from them and still
> holds. **Quote 22.9%, not 28.0%.**

The failure is specific, not diffuse. Quadrant assignment is reliable (93.0% of detected
teeth): the jaw split works and the image-left/patient-right convention holds. The **position
digit** is what breaks, and asymmetrically — 40.2% of position errors are too low against
20.6% too high. The cause is a clean propagation from Stage 1: detector recall falls sharply
toward the posterior arch, and positional assignment numbers teeth by rank order from the
midline, so every missed premolar or molar shifts each tooth distal to it one place inward.

(Numbers corrected 22 Aug 2026: a first run rotated the detector input clockwise when the
detector was trained on counter-clockwise. Fixing it moved end-to-end accuracy 26.3% → 28.0%
and quadrant 90.2% → 93.0% — better, but not enough to change the conclusion, which is the
substantive point. `RESULTS_LOG.md` 2026-08-22d.)

This is the stage-wise error-propagation decomposition the paper needs (C3), and it says
something sharper than "accuracy compounds": **losing a tooth at detection does not merely
reduce coverage, it corrupts the labels of teeth that were detected correctly.** A per-tooth
report at 26.3% numbering accuracy is not clinically usable — a finding attributed to the
wrong tooth is worse than an unattributed finding.

Two routes forward, and the second looks stronger: raise posterior detector recall, or replace
rank-order assignment with a learned per-tooth enumeration head. The training data for the
latter already exists — DENTEX's `quadrant_enumeration` subset labels 18,095 teeth with
quadrant and position across 634 images. (**The disjointness assumed here was later
disproved** — 85 of `disease/`'s 250 images are byte-identical to enumeration images; see §8.10
and RESULTS_LOG 2026-08-22j. Evaluation uses the 164 that remain.)

**RESOLVED 22 August 2026.** The learned enumeration head reaches **46.5% end-to-end** (69.4%
of detected teeth) against **22.9%** for positional assignment — a **2.0× improvement** — on
**164 leak-free images**. On teeth in complete (8-detection) quadrants — rank-order's best
case — positional reaches **66.3%** and the head **80.2%**, clearing the ceiling by
**+13.9 points** (n=101, identical population), and the head wins in every completeness bucket.
That is the substantive point: not a better sorter, but a method not subject to the constraint
at all. The bottleneck has moved to Stage 1 — at 67.0% recall that is the end-to-end maximum,
and the head achieves 69.4% of it.

> *Corrected 24 Aug 2026:* earlier drafts quoted a 67.0% ceiling and a +2.4-point margin.
> 67.0% is the detector's **recall**; the ceiling is 66.3%, and the +2.4 compared two different
> populations. RESULTS_LOG 2026-08-24a.

**Prior art and framing (added 22 Aug 2026, after reading both papers directly).**
DPML (Cao et al., *Expert Systems With Applications* 254:124446, 2024) §3.4 independently
argues for exactly this design — *"dentists typically identify tooth categories by considering
the relative position of the target tooth… we have developed a mechanism to provide the model
with positional information"* — and is the citation for spatial priors in tooth classification.
DPML classifies into **8** classes, justified by bilateral symmetry, which sidesteps the
left/right problem; FDI's 32 classes cannot, so we supply positional features to help
disambiguate mirrored pairs. (It also explains why DPML can flip images in augmentation and we
must not: flipping preserves their labels and inverts ours — a fact about the *labels*, so it
holds regardless of what the model can recover.)

**How much those features actually contribute — measured, and less than we first claimed.**
An input ablation on the 2,729-crop val split (`scripts/eval/ablate_head_inputs.py`) replaced
the positional features with their dataset mean: laterality fell only **99.5% → 96.3%** and the
position digit did not move at all (92.1%). **The image alone recovers laterality at 96.3%**,
not the 50% of guessing — a 1.5×-expanded crop carries its neighbours and the local arch
curvature, so mirrored teeth sit in mirrored contexts. Earlier drafts of this section asserted
laterality was "not recoverable from crop pixels"; that is **false** and is withdrawn. The
honest claim is that positional features are worth **+3.2 points of laterality / +2.8 FDI
exact** — real, cheap, and worth keeping, but a refinement rather than the load-bearing
element. What the image is load-bearing for is the **position digit**, which collapses without
it, and that is exactly where rank-order geometry fails.

**A sensitivity that turns out not to matter — and the reason it does not.** Supplying
*shuffled* positional features (another tooth's) costs **22.9 points of laterality**, which
invites the conclusion that the head is fragile to detector-box error. **It is not, and that
conclusion is withdrawn.** A shuffle teleports a coordinate to a different tooth, frequently
across the midline, and crossing the midline is what inverts laterality. Realistic box error is
a small *local* displacement: perturbing the centre by **±15% of box size** — the training
jitter magnitude — leaves side, position and FDI exact unchanged to within 0.1 points, and even
**±100% of box size** costs only 0.2 points of side accuracy. The geometry explains it: a tooth
occupies ~4.5% of image width, so a full-box displacement shifts the normalised centre by at
most 0.045, while the median tooth sits 0.091 from the midline. Report the shuffle result as an
*attribution* diagnostic — it shows the head genuinely uses the coordinate — not as a
robustness weakness. RESULTS_LOG 2026-08-24c, corrected by 2026-08-24e.

DentFound (Zhu et al., *Nature Biomedical Engineering*, 2026) reports **73.58% accuracy /
84.78% F1** on aligning tooth positions with disease findings across 56,351 teeth, and states
that where its reports were judged inferior to human ones this was *"primarily owing to
misalignment between tooth position and disease annotation."* **A 101,000-patient frontier VLM
names our Stage-2 problem as its own weak link.** That makes this section a contribution to a
documented open problem rather than a confession. Do not draw a numeric comparison — different
task, corpus and denominator.

**Report the leakage episode in the methods section.** A first run scored 52.2% before it was
found that **86 of the 250 evaluation images were byte-identical to training images** (85 from
the enumeration corpus, 1 from the detector's). The inflation was 5.7 points. It arose from
generalising a verified disjointness between two folders to a third that had never been
tested. Stating this is worth more than hiding it: it demonstrates the evaluation discipline
the rest of the paper claims.

Report both numbers. The 22.9% → 46.5% progression, with the ceiling argument explaining *why*
a better sorter could never have got there, is a cleaner methodological narrative than the
final figure alone — and the ceiling measurement is what licenses the architectural claim.
`RESULTS_LOG.md` 2026-08-22c, 22f and 22i; figures in
`docs/results/figures/enumeration_head/`.

---

### 8.11 Lesion-localisation agreement — a first number, built to survive contact with Ningxia

`MASTER_PLAN_2026H2.md` §4.3.4 promotes this to the **primary external number** for C2: it
needs no negative class at all — it only asks, of every real lesion, was a diseased tooth
flagged near it — so it cannot be corrupted by Ningxia's missing-healthy-controls problem
(§4.4). No code for it existed before 25 August 2026 (`scripts/eval/lesion_localization.py`).
Built and validated against DENTEX first, deliberately, so connecting Ningxia later is
"point the script at a different folder" rather than new code under deadline pressure.

**What it measures.** The detector emits whole-tooth boxes; the caries branch classifies each
crop. There is no finer localisation inside this pipeline than "which tooth" — so this is a
**tooth-level spatial correspondence check**, not a pixel-level segmentation-quality metric:
is the caries-positive verdict on the tooth that actually has a lesion. That is exactly what
§4.3.4 asks, stated here so the number is never read as claiming more than that.

**Ground truth, scoped deliberately narrow.** DENTEX `disease/label/*.json` carries 8 Turkish
finding types. Only **çürük** (caries) is used as ground truth — küretaj (curettage) and kanal
(root canal) are procedure/treatment markers, not active lesions; gömülü (impacted), lezyon
(periapical — a different clinical entity from periodontal bone loss) and kırık (fracture) are
outside what any branch of this pipeline predicts. Using only çürük means every unmatched GT
lesion is unambiguously something the caries branch should have caught, not a category it was
never trained to recognise.

**Matching is reused, not reimplemented**: `iou()` and `match_gt_to_detections()` (greedy IoU
with a centroid-containment fallback for a lesion polygon much smaller than its tooth box) are
imported directly from `validate_fdi_assignment.py`, `min_iou=0.30` inherited unchanged — one
proven implementation rather than a second one that could quietly disagree.

**Result — 164 leak-free images, clean pipeline default (`caries-gate-resnet18-v3.0`):**

| | |
|---|---|
| Images with ≥1 çürük lesion | 148 / 164 |
| Lesions (çürük polygons) | 479 |
| **Lesion-localisation agreement** | **204/479 = 42.6%** |
| Predicted-positive teeth | 772 |
| — of which land on an annotated lesion | 204 (26.4%, diagnostic only, see caveat) |

Sanity-checked against the two known stage recalls rather than trusted on its own: detector
recall 0.670 × caries test recall 0.74 (arm B, RESULTS_LOG 2026-08-25b) gives a naive compound
estimate of 0.496 — different population and method, but the right order of magnitude next to
the measured 42.6%, which is what compounding two ~65–75% stages should look like.

**The one thing this number cannot tell you**: an unmatched predicted-positive tooth is not a
confirmed false positive. `disease/` annotates only teeth carrying *some* finding — roughly 6
of ~30 per image — so most teeth in any image are simply unannotated, not verified healthy.
`predicted_positive_match_rate` is reported as an explicit diagnostic for this reason, never as
a precision figure (that number, honestly caveated the same way, already exists in
`compare_caries_gates.py`).

**Verified, not assumed, before trusting the aggregate**: `load_lesion_gt` hand-checked against
`test_0`'s raw label file (3 çürük shapes expected, 3 returned, exact FDI match); every
per-image count summed against the top-level aggregate (4/4 exact); 0 images with an
impossible value (matched > lesions, or unmatched-positive > positive).

**Not yet built**: a Ningxia loader. Ningxia ships raster segmentation masks, a different
ground-truth format this project has not inspected (the drive was disconnected when this was
written) — guessing that encoding in advance would be exactly the kind of imagined-not-verified
code this project's corrections this session have all been about. `load_lesion_gt` is the one
function designed to be swapped for a mask-reading sibling; nothing else here assumes DENTEX's
polygon format. Source: `outputs/lesion_localization/full/lesion_localization.json`,
RESULTS_LOG 2026-08-25c.

---

### 8.12 C2 external validation — Ningxia, and a metric that had to differ by disease

**The headline C2 result.** 25 Aug 2026, four hospitals, `scripts/eval/ningxia_external.py`.
Ningxia is LOCKED external test data (§4.2): evaluated once, no tuning of any kind against it.
**Zero leakage** against Tufts, DENTEX `disease/`, `quadrant_enumeration`,
`quadrant-enumeration-disease` and `quadrant`, each checked separately (0 / 2,912 unique test
hashes).

| Split | Centre | Caries lesions | Covered | Strict (1:1) |
|---|---|---|---|---|
| test1 | cross-centre | 316 | **26.6%** | 23.7% |
| test2 | same-centre-as-*Ningxia*-train | 349 | **43.3%** | 36.4% |
| test3 | cross-centre | 162 | **37.0%** | 29.0% |
| test4 | cross-centre | 186 | **22.6%** | 18.8% |

DENTEX internal was 42.6% (§8.11); Ningxia sits at or below it across four independent
institutions. **Write this carefully in the paper:** "same-centre-as-train" describes
*Ningxia's own* split design. We never trained on any Ningxia data, so all four splits are
equally external to us, and the spread reflects genuine inter-centre scanner and population
variation rather than distance from our training set. Describing test2 as "in-domain" would be
wrong.

**Periodontitis — affected-tooth sensitivity**: test1 3.7%, test2 0.8%, test3 1.5%, test4 5.4%
(172/6,222 pooled). With Tufts in-domain at 0.92 macro-F1 and DENTEX firing on 0.7% of teeth,
the bone-loss branch's collapse outside its training domain is now measured on **two
independent external datasets**. That is a genuine, reportable negative result — and a stronger
one than a single dataset could support.

**A withdrawn number, and the methodological point worth putting in the paper.** The first pass
applied the caries metric (lesion-centroid containment) to periodontitis too, and reported
0.7–4.0%. **Those figures are withdrawn as a measurement artefact.** Measured on real masks:

| | blobs/image | median blob area |
|---|---|---|
| caries | 2.5 | 731 px (focal spots on crowns) |
| periodontitis | 1.0 | **365,680 px** (~500× larger) |

Periodontitis masks are not lesions but a *single continuous band* spanning the alveolar ridge,
~8% of the radiograph. The centroid of such a band falls in the gap between teeth, inside no
tooth box — so that metric returns ~0% **by construction, independent of model quality**.
Reporting it would have produced a true-sounding conclusion from a broken instrument.
Periodontitis is therefore scored by **affected-tooth sensitivity**: a tooth counts as affected
if ≥50% of its box lies inside the marked region, and sensitivity is the fraction of those the
pipeline flagged.

The same class of error was caught once more before it ran: Ningxia caries lesions (89–3,090 px)
against ~25,000 px tooth boxes score **IoU 0.015–0.124** — every true match below the 0.30
threshold DENTEX uses. Reusing the DENTEX matcher unchanged would have reported ~0% caries
agreement too. **The general lesson, worth one sentence in the methods: a spatial-agreement
metric is only meaningful when the ground-truth annotation granularity matches the prediction
granularity.** Focal-lesion masks, whole-region masks and tooth-level predictions are three
different granularities, and a metric that silently spans them measures nothing.

Not computed and not computable here: specificity and AUC — Ningxia has no healthy controls
(§4.3). Those come from Tufts. Negatives were **not** synthesised from the other disease
categories, per §4.3's explicit prohibition. Image-level caries sensitivity is ~96% and
effectively saturated (the gate over-calls, and with ~22 teeth/image it nearly always flags
one) — report it as the weak metric §4.3.4 predicted, not as a strength.
RESULTS_LOG 2026-08-25d.

---

## 9. What's not yet written — checklist

For whoever drafts the actual paper. Tick items off here as they land.

**Blocking — must be done before submission**

- [ ] Re-run the caries notebook and **save** the Phase 1 gate classification report
      (`caries` vs `no_caries`), plus the `Counter` cell confirming DENTEX class counts.
- [ ] Carve a held-out **test** split for caries and re-report on it (current numbers are
      validation-only and tuned-on). *(19 Aug 2026: split script written and tested against
      a synthetic fixture — `scripts/dentex/split_dentex_holdout.py` — but not yet run
      against the real DENTEX data or followed by a re-run + re-report. Not done.)*
      **21 Aug 2026: the split half is done and done better** — rebuilt from the raw 705-image
      source as an independent image-level 70/15/15 split
      (`scripts/dentex/build_dentex_split_from_raw.py`, manifest
      `data/dentex/splits_v2.json`, train 495 / val 103 / test 107, verified disjoint and
      reproducible). The **re-run and re-report half is still open** and needs GPU access —
      that is what keeps this item unticked.
- [x] Freeze one canonical detector (A100/1024) and record its weight hash + exact config;
      retire the H200/768 run in writing. **Done 20 Aug 2026** — version tag
      `tooth-detector-a100-1024-v1.0`, SHA-256 recorded in
      `docs/research/T0.6_detector_reconciliation.md` §1 and `model_metrics.md`; H200 run
      documented as superseded in both files and `notebooks/yolo_detection/README.md`.
- [x] Fix the Universal→FDI mapping defect for the lower arch in
      `configs/dataset_config.yaml` (23→32, 24→31, 25–28→41–44, 29–32→45–48), re-verify
      `src/utils/fdi_converter.py` against it, and cover it in `tests/test_fdi_converter.py`.
      **Already done in `f8b31f8`; confirmed 21 Aug 2026** — config and converter match each
      other and the correct table, and the tests name the historical bug (shifted lower arch,
      duplicated FDI 33/34) explicitly. This item, and the matching warnings in the root
      `README.md`, had stayed open in writing after the fix landed.
- [ ] Build Stages 5–6 (integration) and report at least one end-to-end example, or state
      unambiguously in the abstract that the system is evaluated stage-wise only.

**Content still to write**

- [ ] Write up §8.9 (66 annotated teeth missing from the detection ground truth, from
      corrupt `bounding box` fields in the source data) as a short data-quality paragraph —
      it is both an honest limitation of our Stage-1 numbers and a reusable finding about
      the public dataset.
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
