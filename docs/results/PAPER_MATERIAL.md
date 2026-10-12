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

*(§2.1 below now carries the comparison table and the validation-landscape count, added 27 Aug 2026. The remaining thin part is narrative prose, reusable from the archived `02_literature.tex`.)*

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

### 2.1 Related work — the comparison table, built from this project's own review sheet

**Extracted 27 Aug 2026** from `docs/reports/literature/Dental X-Ray Capstone Literature
Review.xlsx` (Sheets 3 and 5) with `scripts/eval/` tooling; the machine-readable extract is
`outputs/related_work_extract.csv`. Of 117 reviewed papers, **49 are task-relevant** (tooth
detection/numbering, caries, or periodontal bone loss on radiographs) after de-duplication.

#### 2.1.1 The validation landscape — the gap this project actually fills

The review sheet records a `Validation` field per paper. Classifying those 49:

| Validation design | n | % |
|---|---|---|
| **Genuine external / multi-centre validation** | **2** | **4%** |
| Explicitly states it has **none** | 10 | 20% |
| Internal split, cross-validation, or unstated | 37 | 76% |

> ⚠️ **Read the field, not the keyword.** A naive search for "external" returns 13 papers, but
> most of those contain the phrase only in the form *"no external validation"*. Counting them as
> externally validated would invert the finding. The two that genuinely qualify are named below.

**The two that do validate externally:**

- **Advancing Dental Caries Detection in Panoramic X-rays: A Two-Step Deep Learning Approach**
  (*Informatica Medica Slovenica*, 2024) — DENTEX internally, plus a Slovenian clinical set.
- **A novel AI-powered radiographic analysis surpasses specialists in stage II–IV periodontitis**
  — multicentre internal plus two external cohorts; the strongest validation design in the review.

**This is the claim to make, and it is now evidenced rather than asserted:** external validation
is near-absent in this subfield. Our four-hospital Ningxia evaluation with per-corpus leakage
checks (§8.12, §8.12a) puts this work in a group of roughly three.

#### 2.1.2 Head-to-head on the datasets we actually use

| Work | Year | Task / dataset | Their reported result | Their validation | Ours |
|---|---|---|---|---|---|
| Two-Step YOLOv8 (*Inform Med Slov*) | 2024 | Enumeration + caries, **DENTEX** | Enumeration mAP@0.5 **0.95**; caries lesion sensitivity **0.70** internal → **0.67** external | DENTEX + external clinic | Detection mAP@0.5 **0.810** (Tufts); caries lesion agreement **44.3%** internal → **40.8%** external (4 hospitals) |
| AI-powered precision (*PLOS Digit Health*) | 2025 | Tooth numbering + caries, **DENTEX** + private | Numbering accuracy **0.9988**, F1 0.9788; caries accuracy 0.94 | 5-fold CV, internal | FDI **82.6%** of detected teeth; **58.3%** end-to-end |
| Reliable Multi-Stage System | 2025 | Instance segmentation + numbering, **Tufts** | mAP **66.2%**, AP50 **97.3%** | Train/val/test split | Detection mAP@0.5 **0.810**, AP50-equivalent |
| Comparative DL architectures | 2026 | Tooth segmentation, **Tufts** | EfficientNet-B7 best Dice | Internal only, 5-fold CV | (segmentation not our reported task) |
| ML for Periodontal Bone Loss (*BMC Oral Health*) | 2024 | Periodontal bone loss, **Tufts** + Chile | Weighted F1 **0.29**; **severe PBL F1 = 0** | Internal, vs 5 clinicians | Bone loss **0.9233** in-domain → **2.4%** external (§8.13) |
| DPML (Cao et al., *ESWA*) | 2024 | Caries detection | **95.06** mAP own data → **61.83** on public DENTEX | Own single-centre + public | The same in/out-of-domain gap we measure |

#### 2.1.3 How to read that table honestly — three traps

1. **"Numbering accuracy 0.9988" is not our 58.3%.** That figure classifies an *already-cropped,
   correctly-detected* tooth. Our directly comparable number is **82.6% of detected teeth**;
   **58.3%** is end-to-end and *includes* the detector's 70.6% recall. Comparing 0.9988 against
   58.3% would be dishonest in our favour if reversed, and dishonest against us as written. State
   both of ours, and state which one is comparable to what.
2. **Our absolute numbers are lower than several published ones, and the paper should say so
   plainly.** Detection 0.810 against a reported 0.95–0.97 on similar tasks. The contribution here
   is not peak accuracy; it is that the numbers survive an external test, carry confidence
   intervals (§8.14), and come with a stage-wise error attribution (§8.16).
3. **The bone-loss comparator is the most useful row in the table.** An independent group reports
   **weighted F1 0.29 and severe-PBL F1 = 0 on Tufts**, with clinician comparison. Periodontal
   bone loss on this data is *hard for everyone*, which is important context for §8.13's honest
   report of our own out-of-domain collapse — it makes ours a measured limitation of the task,
   not a uniquely bad model.

**Source:** `outputs/related_work_extract.csv`, regenerable from the review sheet.
Prose for the fuller narrative is reusable from
`_repo_archive/pes_capstone_report/chapters/02_literature.tex`.


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

> **11 Oct 2026 — the pipeline default is no longer the Tufts-only model described below.** It
> is the Lever A multi-corpus detect model (arm3c: Tufts + DENTEX `quadrant_enumeration` + Kaggle
> "dual", per-corpus balanced sampling, otherwise this section's configuration), made the
> default by a decision against two pre-registered ablation verdicts. §8.30 has the numbers and
> how to write them. What follows describes the Tufts-only detectors, which are retained.

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

> **CORRECTED 10 Oct 2026 — this section describes the design, not what the bone-loss run did**
> (`RESULTS_LOG` 2026-10-10, §8.28). The run that produced the shipped Stage-4a checkpoint found
> no `val/` on disk and fell back to a crop-level `train_test_split(test_size=0.2)`, stratified by
> label and not grouped by radiograph. All 143 validation radiographs also supply training crops.
> The frozen 70/15/15 split is the detector's; the bone-loss models never used it.

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

### 7.1 Stage 1 — tooth detection (two frozen Tufts-only detectors; the **seg** model was the pipeline default 27 Aug – 11 Oct 2026)

> The default since 11 Oct 2026 is the multi-corpus detector — §8.30, and `model_metrics.md`
> for its numbers. Its Tufts test box mAP@0.5 is 0.585 against the seg model's 0.810 below.

| Run | GPU | imgsz | Epochs | Split | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|-----|-----|-------|--------|-------|-----------|--------|---------|--------------|
| **A100** | A100 80GB PCIe | 1024 | 150 req. / 128 run / best ep. 98 | val (150 img, 3,794 inst) | 0.788 | 0.772 | **0.834** | 0.367 |
| **A100** | A100 80GB PCIe | 1024 | " | **test** (150 img, 3,924 inst) | 0.7643 | 0.7421 | **0.7824** | 0.3351 |
| H200 | H200 143GB | 768 | 50 | val (150 img, 3,794 inst) | 0.609 | 0.678 | 0.678 | 0.282 |

**Superseded as the default on 27 August 2026 by a YOLOv11l-*seg* retrain (R1).** Same frozen
700/150/150 Tufts split, same imgsz 1024 / batch 32, only the model and the label geometry
changed — the comparison was pre-registered in `T0.6_detector_reconciliation.md` §2 before any
number was seen.

| Run | Task | Split | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|-----|------|-------|-----------|--------|---------|--------------|
| **YOLOv11l-seg** (135 ep, best ep. 105) | **Box** | **test** (150 img, 3,930 inst) | 0.7666 | 0.7751 | **0.8100** | 0.3411 |
| **YOLOv11l-seg** | Mask | **test** | 0.6270 | 0.6339 | **0.6383** | — |

- **Box detection improved +2.76 points** over the bbox detector (0.8100 vs 0.7824) on the same
  split. Training with mask supervision produced a *better box detector*, which is the number
  that matters downstream — Stage 2 is capped by detector recall, not mask quality.
- **The pre-registered mask bar (≥0.65) was NOT met** (0.6383, short by 0.0117). Per the
  pre-registration the bar was **not moved after seeing the number**. The model was adopted
  anyway on 27 Aug **by explicit human decision, for the box gain alone** — adoption is a dated
  judgement call, not the bar being satisfied. Both facts are on the record.
- **Consequence: the model is used for its BOXES ONLY, and R2 (mask-aware cropping, §6.6)
  stays unwired**, because the masks are not validated to the standard §2 set for them.
- Caveat, pre-registered: the seg test GT has 3,930 instances vs the bbox run's 3,924 (+0.15%),
  so this is near-, not exactly, like-for-like.
- Version tag `tooth-detector-seg-tufts-1024-v1.0`; SHA-256 in `model_metrics.md`.
  Source: `models/11_yolo_seg_tufts_r1/run_summary.txt`, RESULTS_LOG 2026-08-27b/d.
- **A first R1 run was withdrawn, not reported** — it trained 90 clean epochs on masks that were
  spatially misaligned by two independent data defects (`teeth_polygon.json` stores `[y,x]`; the
  Windows `Radiographs_rotated/` was 180° out). Caught by comparing val mAP 0.258 against the
  bbox detector's 0.834 and treating the gap as a defect to explain rather than a number to
  report. Median label IoU against the independent `teeth_bbox.json` ground truth went
  **0.000 → 0.837** after the fix. Worth one methods sentence: *a falling loss curve is not
  evidence of correct data.* RESULTS_LOG 2026-08-27a/c.

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
  A YOLOv11l-seg retrain (R1) was pre-registered in the same document and **has since been run
  and adopted — see the seg table above** (27 Aug 2026). **Update, later on 20 Aug 2026:** `teeth_polygon.json` and all 1,000 raw
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

Test mAP@0.5 = **0.8100** (the seg detector, pipeline default since 27 Aug 2026; the superseded
bbox detector scored 0.7824) vs ≥ 0.90 reported for Tufts in the surveyed literature. The gap
has narrowed but has not closed, and it should be stated rather than elided.

> *Corrected 27 Aug 2026:* this section previously read "0.782 … two competing runs exist and no
> canonical detector has been frozen", which was stale in both halves. Two detectors are now
> frozen, tagged and hash-pinned (`tooth-detector-a100-1024-v1.0`,
> `tooth-detector-seg-tufts-1024-v1.0`); the 768 px H200 run was retired in writing on
> 20 Aug 2026. RESULTS_LOG 2026-08-27b/d.

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

**Two more Tufts box-label findings, surfaced by the Lever A multi-corpus build (Sep 2026,
`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` §1.5).** (1) The multi-corpus
builder applies its degenerate-box guard only to the rotated corpora; Tufts passes through
unfiltered, so ~21 of the sub-2 px boxes re-entered the Tufts training slice and a handful the
Guard-2 test ground truth — an asymmetry with the other three corpora, though at < 0.1 % of the
test GT it does not move the metric. (2) On matched predictions, *every* model — including one
trained only on Tufts — draws Tufts boxes 17–36 % wider in the narrow (mesial-distal) direction
than the ground truth, while matching its crown-to-root extent to within 5 %. The Tufts
`teeth_bbox.json` boxes are drawn tighter mesial-distally than a detector naturally converges to;
because the boxes are ~5:1 thin, that alone holds matched-pair IoU near 0.62 and mAP@0.5:0.95
near 0.27 for any model trained on them — a property of the label convention, not of any model,
that caps the box-mAP headroom on this corpus.

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

> **Updated 27 Aug 2026 — the prediction in this section was tested, and it held.** This
> section argued Stage 1 was the binding constraint. Replacing the detector with the seg model
> (§7.1) and re-measuring Stage 2 on the identical 164-image leak-free DENTEX set moved
> **end-to-end FDI exact from 46.3% to 58.3% (+12.0 points)** — the largest single jump this
> project has recorded, and the head itself was not retrained.
>
> | | bbox (control) | **seg (adopted)** | Δ |
> |---|---|---|---|
> | Detection recall | 67.3% | **70.6%** | +3.3 pp |
> | FDI exact (of detected) | 68.7% | **82.6%** | +13.9 pp |
> | **FDI exact, end-to-end** | 46.3% | **58.3%** | **+12.0 pp** |
>
> **Recall rose 3.3 points but end-to-end rose 12.0**, and that asymmetry is the interesting
> result. Detections per image *fell* (23.7 → 22.0) while recall *rose*: the seg detector emits
> fewer spurious boxes, and every spurious box perturbs the Hungarian assignment across a whole
> quadrant. Off-by-one errors nearly halved (22.7% → 13.5%). **Precision in the detector is
> worth more to Stage 2 than recall is** — a claim about pipeline coupling, not about either
> model, and one most stage-wise evaluations cannot see. A control on the old detector was run
> first so the delta is attributable to the detector alone. RESULTS_LOG 2026-08-27e.
>
> The bottleneck is still Stage 1 (70.6% recall caps end-to-end), but it is a looser one.

**Updated 4 September 2026 — the Tufts end-to-end number, which the pipeline never had.**
`validate_fdi_assignment_tufts.py` runs the same detector → head → Hungarian assignment against
the *complete* Tufts per-tooth numbering (3,760 permanent teeth on 149 frozen-test images,
mirror-corrected via `tufts_title_to_fdi`), so it is a real recall and a real end-to-end
accuracy, not the GT-only-teeth partial that DENTEX gives. With the deployed detector:
**recall 82.4 %, FDI exact of detected 78.6 %, end-to-end 64.8 %** (`RESULTS_LOG` 2026-09-04d).
Tufts end-to-end is *above* DENTEX's 58.3 % — the detector is in-domain here — on a harder
test (every tooth, including the ambiguous posteriors, not just the ~6 pathological teeth per
image DENTEX annotates). Two things this measurement settles. **(a)** The Lever A / A2
multi-corpus detector, which fails the Tufts box-mAP guard (0.724 → 0.585), gives *the same*
end-to-end Tufts FDI: 64.8 % → 63.5 % (arm3c) → 63.7 % (A2). A 14-point box-mAP@0.5 drop is a
1-point end-to-end drop — box mAP@0.5 is not a proxy for pipeline accuracy, and the ablation's
deployment cost on Tufts is ~1 point (see §8.16). **(b)** The superseded bbox detector
(`models/06`) *beats* the deployed seg detector on Tufts end-to-end — 71.5 % vs 64.8 %, driven
by recall (91 % vs 82 % at the conf-0.25 operating point; lowering conf makes the seg detector
worse, not better, because spurious boxes flood the assignment). The 27 Aug bbox → seg swap
gained +12 points on DENTEX *cross-domain* and costs 6.7 points on Tufts *in-domain*: a higher
box mAP did not buy higher pipeline accuracy on the detector's home corpus, because Stage 2 is
sensitive to the recall/precision operating point, not the PR-curve area. This is a
detector–Stage-2 coupling nuance, not a reason to revert — `models/11` was adopted on its box
result and the DENTEX gain, a dated decision (§7.1).

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
| **Lesion-localisation agreement** (seg detector, current) | **212/479 = 44.3%** |
| Lesion-localisation agreement (old bbox detector, same-machine control) | 201/479 = 42.0% |
| *(25 Aug published figure, old detector)* | *204/479 = 42.6%* |
| Predicted-positive teeth | 772 |
| — of which land on an annotated lesion | 204 (26.4%, diagnostic only, see caveat) |

Sanity-checked against the two known stage recalls rather than trusted on its own: detector
recall 0.670 × caries test recall 0.74 (arm B, RESULTS_LOG 2026-08-25b) gives a naive compound
estimate of 0.496 — different population and method, but the right order of magnitude next to
the measured **44.3%**, which is what compounding two ~65–75% stages should look like. (On the
seg detector the recall term rises to 0.706, giving 0.522 against a measured 44.3% — the same
modest over-estimate, so the sanity check still holds after the swap.)

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

> **RE-MEASURED 27 Aug 2026 on the seg detector — read §8.12a below before quoting anything in
> this section.** Caries agreement improved on all four hospitals (+7.7 points pooled); the
> bone-loss branch did not move at all. The 25 Aug numbers in the rest of this section were
> measured on the superseded bbox detector + FDI head v1.0 and are kept as the comparison
> baseline, not as current figures.

**The original C2 result.** 25 Aug 2026, four hospitals, `scripts/eval/ningxia_external.py`.
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

### 8.12a The detector swap, re-measured externally — and the stage it did not help

**27 Aug 2026.** After adopting the seg detector (§7.1) the whole of C2 was re-run against it,
with a **control on the old detector + head v1.0 executed first on the same machine** so the
delta is attributable to the models rather than to library drift. The control reproduced 25 Aug
(caries 27.2 / 43.3 / 35.2 / 22.0% vs 26.6 / 43.3 / 37.0 / 22.6%), which is what licenses the
comparison. `RESULTS_LOG.md` 2026-08-27h.

**Caries — improved on all four hospitals. No caries model changed; only the detector.**

| Split | Lesions | old detector | **seg detector** | Δ |
|---|---|---|---|---|
| test1 | 316 | 27.2% | **28.8%** | +1.6 pp |
| test2 | 349 | 43.3% | **51.3%** | +8.0 pp |
| test3 | 162 | 35.2% | **40.1%** | +4.9 pp |
| test4 | 186 | 22.0% | **41.9%** | +19.9 pp |
| *(pooled, scale only)* | 1,013 | 33.1% | **40.8%** | **+7.7 pp** |

This denominator is GT-derived and model-independent, so it is a straight read. External caries
agreement now sits just below the DENTEX internal figure (§8.11) rather than well below it —
i.e. much of the apparent internal/external gap was a *detection* gap, not a caries model gap.
**RESOLVED 27 Aug 2026** — §8.11 has been re-measured on the seg detector (44.3%, with a
same-machine control at 42.0%), so the comparison below IS like-for-like:

| | internal (DENTEX) | external (Ningxia, pooled) | gap |
|---|---|---|---|
| old detector (control) | 42.0% | 33.1% | **8.9 pp** |
| **seg detector** | **44.3%** | **40.8%** | **3.5 pp** |

**The internal/external gap more than halved, and the external number moved further than the
internal one** (+7.7 vs +2.3 pts — and with intervals added 27 Aug, only the external gain is
statistically real: **+7.7 pp [+3.3, +12.0]** vs internal **+2.3 pp [−3.4, +7.9]**, §8.14) — so much of what read as caries domain shift was a detection
problem. That is the same shape as the head-v2.0 result (§8.8b): a change worth ~0 in-domain was
worth +21.5 points out-of-domain. **Do not write this up as "caries generalises well."** 40.8%
pooled is weak in absolute terms, three of four hospitals remain below the internal figure, and
test2 exceeding it is one centre. `RESULTS_LOG.md` 2026-08-27i.

**Periodontitis — unchanged, and this is the more interesting half.**

| Split | Affected (ctl → seg) | Flagged (ctl → seg) | Sensitivity |
|---|---|---|---|
| test1 | 3,278 → 3,285 | 121 → 79 | 3.7% → **2.4%** |
| test2 | 2,068 → 2,462 | 16 → 34 | 0.8% → **1.4%** |
| test3 | 349 → 411 | 4 → 23 | 1.1% → **5.6%** |
| test4 | 534 → 633 | 27 → 29 | 5.1% → **4.6%** |
| *(pooled)* | 6,229 → 6,791 (+9.0%) | **168 → 165** | 2.7% → **2.4%** |

Across 736 images the pipeline flagged **168 affected teeth before and 165 after** while the
denominator grew 9%. Movement is in both directions and test3's 1.1% → 5.6% is 4 → 23 teeth on
50 images — noise, and it must not be written up as a win.

**The claim worth making in the paper, because it needs three measurements and we now have all
three.** One intervention — replacing the detector — was applied and measured across three
downstream stages:

| Stage | Effect of the detector swap |
|---|---|
| Stage 2, FDI numbering (DENTEX, internal) | **+12.0 pts** end-to-end (§8.10) |
| Stage 3, caries (Ningxia, external ×4) | **+7.7 pts** pooled agreement |
| Stage 4a, bone loss (Ningxia, external ×4) | **no change** (168 → 165 teeth flagged) |

Stages whose errors were dominated by *which teeth got cropped* improved substantially. The
bone-loss branch did not, because its failure is domain shift **inside the Stage-4a classifier**
— it flags essentially the same absolute set of teeth no matter what feeds it. This is a
stage-wise error-attribution result of the kind [C3] promises, and it **falsifies** the standing
hypothesis that the detector and the bone-loss branch misbehaved out-of-domain for a shared
reason because both were Tufts-trained. They do not. The untried lever for bone loss remains the
DENTEX+Tufts combined-training trick that fixed Stage 2's generalisation (§8.8b).

⚠️ **Methodological caveat that belongs in the text, not a footnote.** Affected-tooth sensitivity
has a **model-dependent denominator** — affected teeth are counted from *detected* boxes, so a
detector that finds different teeth moves numerator and denominator together. It is not a plain
sensitivity and cannot be compared across detectors without the control. Caries agreement has no
such problem. Detections/image rose 15–20% in test2–4 but *fell* in test1 (25.2 → 22.7), the
split carrying burned-in annotation arrows and stars.

---

### 8.13 The bone-loss branch does not generalise — reported as a measured limitation, not fixed

**This is the project's one open technical failure, and it is deliberately reported rather than
patched.** Decision taken 27 Aug 2026; the reasoning is below, because a reviewer is entitled to
ask why a known weakness was not addressed.

**What was measured.** Stage 4a (ResNet18, 1.5×/2.0× expanded crops, Tufts) is strong in domain
and collapses outside it:

| Domain | Result | Support |
|---|---|---|
| **Tufts** (in-domain, validation, real prevalence) | **0.9233 macro-F1**, sens 83.1%, spec 99.5% | 1,558 crops (1,499 normal / 59 diseased) |
| **DENTEX** (external) | fires on **0.7%** of detected teeth | 164 leak-free images |
| **Ningxia** (external, 4 hospitals) | **2.4%** affected-tooth sensitivity, pooled | 6,791 affected teeth over 736 images |

Per-Ningxia-centre: 2.4 / 1.4 / 5.6 / 4.6% (test1–test4). The spread is small-n noise, not a
gradient — test3's 5.6% is 23 teeth of 411 on 50 images and must not be quoted as a better result.

**Two independent external datasets agree**, with different ground-truth formats (LabelMe
polygons vs raster masks) and different metrics (firing rate vs affected-tooth sensitivity). That
is what makes this a finding rather than a bug report: a single external failure could be a
harness artefact, and this project has already withdrawn one number for exactly that reason
(§8.12, the centroid-containment artefact). Two, measured independently, is a property of the model.

**The causal hypothesis was tested and FALSIFIED — this is the part worth writing up.** The
standing explanation was that the detector and the bone-loss branch were the project's two
Tufts-trained stages and misbehaved out-of-domain for a shared reason. On 27 Aug the detector was
replaced (§7.1) and every downstream stage re-measured against a control:

| Stage | Effect of the same detector swap |
|---|---|
| Stage 2, FDI numbering (DENTEX) | **+12.0 pts** end-to-end |
| Stage 3, caries (Ningxia, ×4 hospitals) | **+7.7 pts** pooled agreement |
| **Stage 4a, bone loss** (Ningxia, ×4 hospitals) | **no change** |

Bone loss flagged **168 affected teeth before the swap and 165 after**, while the denominator grew
9% — i.e. the branch flags essentially the same absolute set of teeth regardless of which
detector feeds it. **The failure is inside the Stage-4a classifier, not upstream of it.** That
rules out an entire class of explanations (crop quality, detection recall, box geometry) and is a
stage-wise error-attribution result of the kind contribution [C3] promises.

**Why no fix was attempted, stated plainly.** The obvious lever — the DENTEX+Tufts combined
training that fixed Stage 2's cross-domain behaviour (§8.8b, +21.5 points out-of-domain) — **does
not transfer, because DENTEX carries no bone-loss labels.** Stage 2 could be trained on two
corpora because both label FDI codes; there is no second corpus in this project with periodontal
bone-loss annotation. The remaining options were all substantial research programmes rather than
fixes: domain-generalisation training on Tufts alone, weak supervision from DENTEX's `küretaj`
(periodontal curettage) treatment markers — a noisy proxy, not a label — or acquiring an annotated
second periodontal corpus. **None fits inside the remaining schedule, and attempting one badly
would produce a weaker paper than reporting the measurement honestly.**

**Also inherited by Stage 4b.** The severity head only sees teeth 4a flagged, so out of domain it
is effectively never exercised; its in-domain 0.7208 macro-F1 rests on **52 validation crops with
Mild at n=6** (§8.2) and says nothing about external behaviour.

**Contributing factors, already documented and not re-argued here:** labels are weak supervision
derived by intersecting a per-image expert mask with per-tooth boxes (§8.6); training data is a
single institution, one scanner population, one annotation protocol (§8.7); and the positive class
was resampled from a 23.8× imbalance down to 2,500 normal / 711 diseased (§6.4), so the model saw
711 real positive teeth in total.

**How to write this in the paper.** Not as an apology and not buried. The honest framing is that
an in-domain macro-F1 of 0.92 on a periodontal task is **not evidence of a usable periodontal
model**, and this work demonstrates that with external measurement on four hospitals plus a
second public dataset — then localises the cause to the classifier rather than the pipeline
around it. Published comparators show the same shape: DPML reports 95.06 mAP on its own
single-centre data and 61.83 on public DENTEX (§8.12). **A reader's takeaway should be that
single-dataset periodontal results in this literature are not transferable, evidenced rather than
asserted.** The pipeline correspondingly reports bone-loss findings with the domain-shift caveat
attached in `report["limitations"]["bone_loss_domain_shift"]` on every single inference, which is
the operational consequence of taking this seriously.

---

### 8.14 Confidence intervals — and the two claims that do not survive them

**Added 27 Aug 2026.** Every headline metric with saved per-item outputs now carries a
**cluster-bootstrap 95% CI** (10,000 resamples, seed 42, `scripts/eval/bootstrap_ci.py`).

**Resampling is over IMAGES, not teeth, and this is the choice to defend in the methods.** The
936 Stage-2 teeth come from 164 radiographs. Teeth within one image share a patient, a scanner,
an exposure and an operator, and the pipeline's errors are correlated within an image — a
mis-numbered quadrant mis-numbers several teeth at once, which §8.10 measured directly. Treating
936 correlated teeth as 936 independent observations would produce intervals that are far too
narrow. **n = 164 images, not 936 teeth.**

| Metric | Point | 95% CI | n (images) |
|---|---|---|---|
| Detection recall | 70.6% | [66.5, 74.6] | 164 |
| **FDI exact, end-to-end** | **58.3%** | **[53.9, 62.8]** | 164 |
| FDI exact, of detected | 82.6% | [79.1, 85.8] | 164 |
| Lesion agreement (DENTEX internal) | 44.3% | [39.0, 49.3] | 148 |
| Caries agreement — Ningxia test1 / 2 / 3 / 4 | 28.8 / 51.3 / 40.1 / 41.9% | [23.3, 34.6] / [44.0, 58.5] / [31.9, 48.3] / [33.1, 50.8] | 134 / 110 / 40 / 53 |

**Paired deltas for the detector swap** — same resampled images, both arms:

| Delta (seg − bbox) | Point | 95% CI | Verdict |
|---|---|---|---|
| **FDI exact, end-to-end** | **+12.1 pp** | **[+6.8, +17.2]** | **real** |
| **Caries agreement, Ningxia pooled** | **+7.7 pp** | **[+3.3, +12.0]** | **real** |
| Detection recall | +3.3 pp | [−1.5, +8.0] | **not significant** |
| Lesion agreement (DENTEX internal) | +2.3 pp | [−3.4, +7.9] | **not significant** |

**Two numbers reported earlier the same day do not survive their intervals, and the paper must
not claim them:** the +3.3 pp detection-recall gain and the +2.3 pp internal lesion-agreement
gain. Both point estimates stand; neither supports an inference.

**This strengthens the central claim rather than weakening it.** §8.10 argued the end-to-end
improvement came from *fewer spurious boxes* rather than *more teeth found* — inferred at the
time from detections/image falling while recall rose. The intervals now support it from both
sides: **the end-to-end gain is real and the recall gain is not.** The mechanism is a precision
effect, evidenced rather than reasoned. The same asymmetry appears across domains: the swap
demonstrably helped **out-of-domain** caries (+7.7 pp, real) and demonstrably did **not** help
in-domain lesion agreement (+2.3 pp, n.s.) — echoing §8.8b, where a change worth ~0 in-domain was
worth +21.5 points out-of-domain.

⚠️ **Coverage is partial, and the paper should say which numbers lack intervals.** Ningxia
**periodontitis** has none — `ningxia_external.py` stores affected-tooth counts per split, not per
image, so no cluster exists to resample, and recomputing would spend a touch on locked external
data for a logging omission. **Detection mAP@0.5 and both ResNet18 classifiers** have none — no
per-item prediction dumps are saved. Those need an evaluation pass that writes per-image scores.

---

### 8.15 Calibration — the caries gate's probabilities are not probabilities

**Measured 27 Aug 2026** on the frozen `caries-gate-resnet18-v3.0` over its held-out test split
(863 crops, 14.7% prevalence). `run_inference.py` stamps every tooth with a `caries_uncalibrated`
flag; this section replaces that assertion with a number.

| | |
|---|---|
| Average precision | **0.550** [0.445, 0.660] |
| Chance (prevalence) | 0.147 |
| **Expected calibration error** | **0.136** |
| Max calibration error | 0.596 |
| Brier score | 0.137 |

CI by cluster bootstrap over source images, 10,000 resamples (§8.14's argument).
Figure: `figures/paper/caries_gate_calibration_test.png`.

**The finding is that the model is systematically OVERCONFIDENT, not merely imprecise.** Every
reliability bin lies **below** the diagonal: at a predicted P(caries) of 0.85, the observed
frequency is **0.26**. That is a stronger and more useful statement than "precision 0.40" — it says
the *scores* are broken rather than only the *decisions*, and it implies a fix that needs no
retraining (temperature scaling or Platt on the validation split).

**State the AP alongside the precision.** 0.550 against a 0.147 chance line is **3.7x chance** —
the ranking the model produces is genuinely informative, and quoting "precision 0.40" alone
understates it. What fails is calibration and the operating point, not discrimination.

**Report the threshold sweep, not one operating point.** The pipeline uses `argmax` (threshold
0.50), which the sweep shows is near F1-optimal — previously an inherited default, now a defended
choice:

| Threshold | Flagged | Precision | Recall | F1 |
|---|---|---|---|---|
| 0.30 | 319 | 0.339 | 0.850 | 0.484 |
| 0.40 | 266 | 0.376 | 0.787 | 0.509 |
| **0.50 — pipeline default (argmax)** | **236** | **0.398** | **0.740** | **0.518** |
| 0.60 | 195 | 0.420 | 0.646 | 0.509 |
| 0.75 | 116 | 0.534 | 0.488 | 0.510 |
| 0.90 | 65 | 0.692 | 0.354 | 0.469 |
| 0.95 | 27 | 0.778 | 0.165 | 0.273 |

Moving to 0.90 buys **precision 0.40 → 0.69** for **recall 0.74 → 0.35**. For a screening aid
that is a design decision the paper should show rather than pre-empt.

**Temperature scaling was tried and does NOT fix it (27 Aug).** T = 1.377 fitted on val,
evaluated once on test: **ECE 0.136 → 0.152 (worse)**, MCE 0.596 → 0.433, Brier 0.137 → 0.132,
AP unchanged at 0.550. **Not adopted.** The failure is informative: temperature scaling assumes a
uniform *scale* error, but the reliability curve is a *shape* error — observed frequency is flat
at ~0.27 across predicted 0.50–0.85, then jumps to 0.69. One scalar cannot re-bend that, and
softening drags the already-decent low bins off the diagonal. **Write this as "the miscalibration
is structural, not a temperature effect"** — evidence against the cheapest fix, not an untested
assumption. Isotonic or Platt (both still monotonic, so still decision- and AP-preserving) are the
honest next candidates. Figure: `figures/paper/caries_gate_temperature_scaling.png`.

**Isotonic regression does fix it, at a price (27 Aug).** Fitted on val, evaluated once on test:
**ECE 0.136 → 0.043 (−68%)**, MCE 0.596 → 0.334, Brier 0.137 → 0.098 — confirming the diagnosis
above that the error was structural and needed a method able to fit a shape. But **AP drops
0.550 → 0.500** (isotonic is only weakly monotonic; ties collapse ranking to 46 distinct values)
and **155 of 863 verdicts flip at threshold 0.5 — 18% of decisions**.

**The adoption decision, and its reasoning, belong in the paper.** Applying isotonic to the
*verdict* would invalidate every downstream caries number — the in-pipeline caries rate, the
DENTEX lesion agreement, and the four Ningxia hospital figures, the last of which would cost
another touch on locked external data. Applying it only to the *reported confidence*, leaving the
verdict as `argmax` on raw logits, keeps every published number exactly as measured and still
delivers ECE 0.043. **The full arc — miscalibrated → temperature insufficient → isotonic recovers
it at a measurable cost — is a stronger methods section than any single calibration number**,
because it documents a trade-off rather than presenting a fix as free.
Figure: `figures/paper/caries_gate_isotonic.png`.

⚠️ **The bone-loss classifier has no calibration analysis**, which §9's checklist specifically
asks for. Its metadata carries `filename,label,stem` and **no bounding boxes**, so the 1.5x/2.0x
crops would need reconstructing by hand from tooth ids against `teeth_bbox.json`; a silent
crop-geometry mismatch is exactly what voided the R1 run (§7.1) and would corrupt a calibration
curve while looking plausible. It needs a geometry-verified rebuild first.

---

### 8.16 Stage-2 failure taxonomy — what the 41.7% of wrong codes actually are

**Added 27 Aug 2026** from the saved 936-tooth evaluation; no inference re-run.
Figure: `figures/paper/stage2_failure_taxonomy.png`.

| Outcome | n | % of 936 GT teeth |
|---|---|---|
| **correct** | 546 | **58.3%** |
| **not_detected** (Stage 1 never found it) | 275 | **29.4%** |
| off_by_one (right quadrant, adjacent position) | 89 | 9.5% |
| same_quadrant_far (counting slip, 2+ positions) | 10 | 1.1% |
| mirror_lr (right arch + position, wrong SIDE) | 8 | 0.9% |
| wrong_arch (upper called lower, or vice versa) | 6 | 0.6% |
| other | 2 | 0.2% |

**The single most important reframing in this section: 58.3% is a detection-bound number.**
275 teeth (29.4%) are never detected and cannot be numbered. **Of the 661 teeth Stage 1 finds,
Stage 2 numbers 82.6% correctly.** Report both — the composite is the honest end-to-end figure,
and the conditional is the honest assessment of the numbering method itself. §8.10 already argued
the detector was the binding constraint; this is the direct evidence.

**The errors that remain are overwhelmingly benign.** Of 115 wrong codes, **89 (77.4%) are
off-by-one** — right quadrant, adjacent position, usually the same tooth type. Only **16 of 661
detected teeth (2.4%)** are category errors: wrong arch (6), mirrored side (8), other (2). For a
screening aid these are not interchangeable failures, and this distinction should be stated
plainly rather than buried in an aggregate. The off-by-one drift splits **53 mesial / 36 distal**,
which is *not* the one-sided lean an indexing bug would produce — a check worth reporting as
having been made.

**Difficulty is not where intuition puts it.** Wrong-code rate by position: first premolars
**41.7%** (24 detected — small support, do not over-read), second premolars 26.9%, incisors and
canines ~18–20%, and **molars 13.0–14.9%** on the largest support (215/159/244 GT teeth). Molars
are the *easiest*: large, distinctive and terminal, so they anchor arch ordering.

**The detector swap changed the shape of the errors, not just the count:**

| Category | bbox control | seg detector | Δ |
|---|---|---|---|
| correct | 46.3% | **58.3%** | **+12.1 pp** |
| not_detected | 32.7% | 29.4% | −3.3 pp |
| off_by_one | 15.3% | 9.5% | −5.8 pp |
| same_quadrant_far | 2.1% | 1.1% | −1.1 pp |
| mirror_lr | 1.1% | 0.9% | −0.2 pp |
| **wrong_arch** | **2.4%** | **0.6%** | **−1.7 pp (a 75% reduction)** |

**`wrong_arch` fell 75%.** Combined with §8.14's finding that the recall gain alone was **not**
statistically significant, this says the seg detector's contribution is box *quality*, not box
*quantity* — fewer spurious detections perturbing the Hungarian assignment across a quadrant.
That is a mechanism claim with evidence behind it, and it is the kind of stage-wise error
attribution contribution [C3] promises.

**The same taxonomy on TUFTS (4 Sep 2026, `RESULTS_LOG` 2026-09-04d).** Now that there is a
Tufts end-to-end eval (§8.10), the identical seven-bucket taxonomy runs on it —
`stage2_failure_taxonomy.py --rows outputs/stage2_tufts/...`, 3,760 permanent teeth, no
inference re-run. Figure `figures/paper/stage2_failure_taxonomy_tufts.png`.

| Outcome | DENTEX (936) | **Tufts (3,760)** |
|---|---|---|
| correct | 58.3 % | **64.8 %** |
| not_detected | 29.4 % | **18.2 %** |
| off_by_one | 9.5 % | 12.6 % |
| same_quadrant_far | 1.1 % | 2.0 % |
| mirror_lr | 0.9 % | 1.3 % |
| wrong_arch | 0.6 % | 0.5 % |
| other | 0.2 % | 0.6 % |

The extra 6.5 points of "correct" on Tufts is entirely the lower miss rate (18.2 % vs 29.4 %) —
the detector is in-domain. Among *detected* teeth the wrong-code rate is slightly *higher* on
Tufts (20.7 % vs 17.4 %), because Tufts scores every tooth including the crowded anterior
region, where DENTEX mostly annotates posterior pathology. The error *shape* is the same:
**74 % of Tufts numbering errors are benign off-by-one neighbours, 3.2 % are category mistakes**
(wrong_arch + mirror_lr — vs 12.2 % for DENTEX, and 43 of the 49 Tufts `mirror_lr` errors are
central incisors, i.e. midline teeth, not a systematic mirror-correction fault). Molars are the
easiest position (9–11 % wrong) and premolars/incisors the hardest (22–31 %), the same rank
order as DENTEX. Off-by-one leans distal on Tufts (285 : 188) where it leaned mesial on DENTEX
(53 : 36) — both ~1.5 : 1, opposite directions, consistent with the different failure modes
(DENTEX under-detects posteriorly → anterior teeth number too low; Tufts detects densely and
the head miscounts in crowded regions).

**And the detector swap's effect on Tufts is the reverse of its effect on DENTEX.** Running the
taxonomy with the *bbox* detector (`models/06`) as the control: on Tufts the seg swap moved
`correct` 71.5 % → 64.8 %, and the entire delta is `not_detected` 9.6 % → 18.2 % — every error
bucket (off_by_one, mirror_lr, wrong_arch) is unchanged to within a point. On DENTEX the same
swap *improved* the error shape (`wrong_arch` −75 %, FDI-exact-of-detected +13.9 pp) because it
suppressed the spurious boxes that perturb the Hungarian assignment. The seg detector's
box-quality benefit is a **cross-domain** benefit — it mattered where the bbox detector was
noisy (DENTEX); on its home corpus, where the bbox detector was already clean, the swap only
cost recall. This is a concrete illustration of the paper's point that box mAP does not capture
detector–Stage-2 coupling.

**Direct confirmation that detection DOMAIN is the ceiling (1 Sep 2026, `RESULTS_LOG` 2026-09-01h).**
Lever 1 re-trained the detector on Tufts **+ DENTEX** `quadrant_enumeration` (disjoint patients
from the 164-image benchmark — leakage ruled out by MD5, filename and perceptual hash). Against
a same-day control and with the identical frozen head, primary metric FDI exact end-to-end on the
164, paired cluster bootstrap over images:

| detector | recall | of detected | **end-to-end** | Tufts frozen test box mAP@0.5 |
|---|---|---|---|---|
| deployed seg (Tufts only) | 70.8% | 82.5% | **58.4%** | **0.810** |
| Tufts-only, detect head | 83.1% | 72.4% | 60.1% | 0.724 |
| **Tufts + DENTEX, detect head** | 99.5% | 93.9% | **93.4%** | **0.647** |

Δ end-to-end vs the deployed detector **+34.9 pp [+30.8, +39.0]** (CI excludes zero); the seg→detect
head change on its own is not significant (+1.7 pp [−3.4, +6.8]), so the entire gain is the added
data. **This is the strongest evidence in the paper that the 58.3% headline is
detector-*domain*-limited, not numbering-limited** — put a same-domain detector in front of the
same head and end-to-end nearly doubles.

**Two things must be stated with it, and neither is optional.** (1) 93.4% is an **in-domain**
number — detector and head both trained on DENTEX-style data, evaluated on held-out DENTEX —
whereas 58.3% is a **cross-domain** number for the detector (trained on Tufts, tested on DENTEX).
They answer different questions and 93.4% is not "the pipeline now works everywhere." (2) The
multi-corpus detector was **pre-registered as an ablation and stays one**: it fails the
pre-registered Tufts guard (test box mAP@0.5 0.810 → 0.647), which is the "domain dilution" risk
the pre-registration named in advance. Adopting it would trade the Tufts benchmark every earlier
number rests on. `models/13_detector_multicorpus_lever1/run_summary.txt`.

**Lever A replicated this and sharpened it (3 Sep 2026, `RESULTS_LOG` 2026-09-03).** The same
experiment run with **four** pooled public tooth-box corpora (Tufts + DENTEX + Kaggle "dual" +
UFBA-425) and per-corpus balanced sampling — an attempt to *fix* the domain dilution — reproduced
the end-to-end gain almost exactly: **Δ +34.4 pp [+30.3, +38.5]** on the primary, 58.4% → 92.8%,
with a 4th aspect-distorted corpus (UFBA-425) adding nothing (Arm 3C = Arm 4C = 92.8%). So the
"the ceiling is detector domain, not numbering" decomposition is now a **replicated** result, not
a single run. The pre-registered fix failed its Tufts guard, but *how* it failed is the finding:
the Tufts frozen-test box mAP fell **monotonically as domains were added** — Tufts-only 0.724 →
+DENTEX+Kaggle 0.585 → +UFBA 0.552 — *further* than Lever 1's 0.647, because balanced sampling
dropped Tufts to 33% of the training mix (Lever 1: 52%). A single-class tooth detector's held-out
box mAP on any one corpus scales with that corpus's *training share*.

**And the tradeoff is bidirectional, which is what makes it a result rather than a failed
attempt.** Guard 1 — pooled caries lesion agreement on Ningxia (4 hospitals) + CariesXrays-1500
with the *frozen* gate, each arm's detector swapped in — **passed strongly**: Ningxia caries
agreement 0.407 → **0.600** (Arm 3C, +19.3 pp, up on all four splits), CariesXrays 0.309 →
**0.370** (+6.1 pp), pooled Δ **+9.11 pp [+7.49, +10.81]**. So the multi-corpus detector is
**worse on Tufts test by ~14–17 pp and better on DENTEX by +34 and on every external cohort by
+6 to +19**. For a pipeline whose contribution is 6-cohort external validation, it is better on
5 of 6 cohorts and worse only on the one it is benchmarked against. **The pre-registered Guard 2
(Tufts-test ≥ Control B − 4 pp) protects the reproducibility of this project's earlier Tufts
numbers, not the deployment goal — a limitation of our own adoption criterion, stated plainly
rather than used to move the bar.** The pipeline default detector stays `models/11` for
benchmark continuity; the paper reports the multi-corpus detector's full 6-cohort table as
"what a deployment-optimised detector choice costs and buys", clearly labelled.
`models/15_detector_multicorpus_leverA/run_summary.txt`, `RESULTS_LOG` 2026-09-03b.

**Phase 0 (4 Sep 2026, `RESULTS_LOG` 2026-09-04) pinned the mechanism of the Guard-2 failure, and
it is not what it looks like.** A greedy GT-match on the 150 Tufts frozen-test images, all three
arms × confidence ∈ {0.10, 0.25, 0.40}: **matched-pair IoU is flat across the whole sweep**
(0.62 / 0.64 / 0.68 — the multi-corpus arms localise if anything slightly *better*), and at
confidence 0.10 the multi-corpus arms find as many Tufts teeth as the Tufts-only control or more
(Arm 4C recall 0.80 vs 0.77). What breaks is **confidence calibration on the minority domain**:
the score no longer separates real teeth from spurious boxes, so raising the threshold to clear
the false positives also removes the true positives (recall drop from confidence 0.10 to 0.40:
control −0.11, Arm 3C −0.29, Arm 4C −0.45). mAP@0.5 is a ranking metric, so it is exactly what
this degrades — 0.724 → 0.585 → 0.552, monotonic in Tufts training share (100 % / 33 % / 25 %;
Lever 1 at 52 % scored 0.647). The tested-and-refuted alternative was a box-annotation-convention
clash (the Tufts GT boxes really are ~1.5× tighter in area than DENTEX's — visible in the
overlays, `models/15_.../repro/diagnostics/gt_overlay.py`), but the trained arms adapt to it:
their predicted Tufts boxes are *closer* to Tufts GT than the control's. **A separate, structural
ceiling sits underneath all of this:** every detection model here — including the Tufts-only
control — scores ≤ 0.724 on this metric, while the deployed *segmentation* Stage-1 scores
**0.810** on the identical split (§7.1). The seg→detect conversion, forced because
DENTEX/Kaggle/UFBA ship no masks, costs ~9 points of box mAP before a single extra corpus is
added; Guard 2 compares each arm to the detect-head control, which is the right control for the
*data* question but means "0.585 vs 0.810 deployed" overstates the multi-corpus penalty and
"0.585 vs 0.724" is the honest figure. `outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md`.

**Lever A2 (4 Sep 2026, `RESULTS_LOG` 2026-09-04b) tested the fix the diagnosis implies, and
closed the question.** If the failure is head calibration, then freezing the multi-corpus
backbone and fine-tuning only the neck + detection head on Tufts should recover it. It does not.
Starting from the Lever A 3-corpus checkpoint with the backbone frozen (`freeze=11`, layers 0–10,
50.7 % of parameters), 40 epochs of Tufts-only fine-tuning moved the Tufts **test** box mAP@0.5
by **+0.8 points** (0.585 → 0.593) — even though the Tufts **validation** mAP recovered
(0.54 → 0.62). The validation gain did not transfer, and the result stays far below the
from-scratch Tufts detector (0.593 vs 0.724). What the fine-tune *did* keep is the multi-corpus
gains — DENTEX end-to-end +29 pp (vs +34 for Lever A) and pooled external caries +8.6 pp (vs
+9.1) — confirming those live in the frozen backbone. So the tradeoff is not catastrophic
forgetting; it is that a Control-B-quality Tufts detector is simply **not reachable from the
frozen 3-corpus features by the head alone**. The Lever 1 → A → A2 sequence therefore reads as
one clean methodological result: a single-class multi-corpus tooth detector cannot be made to
serve both the Tufts benchmark and the external cohorts — naively it fails the Tufts guard, with
four balanced corpora it fails harder (monotonic in Tufts training share), the mechanism is a
confidence-calibration collapse rather than a localisation failure, and it does not respond to
head fine-tuning. The one lever left is multi-corpus **segmentation** (Tufts masks plus
box-prompted pseudo-masks for the box-only corpora), which we scope as future work rather than a
change to this submission. `models/17_detector_leverA2_finetune/run_summary.txt`,
`outputs/lever_A2_detector_finetune/PRE_REGISTRATION.md`.

**How much of the Guard-2 failure is the metric, and how much is a real deployment cost (GT-scale
probe, `RESULTS_LOG` 2026-09-04c).** Guard 2 is box mAP@**0.5**; it was pre-registered and it
failed, and that verdict stands. But the pipeline never asks the detector for IoU-0.5 boxes — the
Stage-2 FDI head assigns a detection to a tooth at **IoU 0.3** (with a centroid fall-back), and
the Stage-3 lesion matcher is looser still. Re-scoring the 150 Tufts test images at IoU-match
0.3: the multi-corpus detector (Lever A / A2) holds **0.84** on Tufts box mAP against the
Tufts-only control's 0.90 — a ~6-point gap, versus the ~14-point gap at IoU 0.5. Two effects
account for the difference between the headline and this number. First, the recorded Tufts
`teeth_bbox.json` boxes are ~15 % tighter than what a detector converges to (box mAP@0.5 peaks
when the ground-truth boxes are dilated ×1.15, for *every* model including the Tufts-only one),
so ~5–8 points of the mAP@0.5 gap is an annotation-tightness artefact shared by all detectors and
not specific to the multi-corpus mix. Second, IoU 0.5 is simply a stricter bar than the pipeline
needs. What survives both corrections is a genuine ~6-point deficit that is *box-independent* —
the Tufts-only control beats the multi-corpus detector by a roughly constant margin at every IoU
threshold and every ground-truth scale, which is the confidence-calibration / frozen-feature gap
the diagnosis identified and cannot be closed by redrawing boxes. **The honest framing for the
paper: the multi-corpus detector fails the pre-registered Tufts benchmark metric, but its cost on
the matching threshold the pipeline actually uses is about 6 points on Tufts, not the ~22 the
headline box-mAP drop (0.585 vs 0.810 deployed) implies** — while it gains 29–34 points on DENTEX
end-to-end and 6–19 on every external cohort. `models/15_detector_multicorpus_leverA/repro/diagnostics/gt_scale_probe.py`.

**Improvement options for the Tufts numbering result — analysed 5 Sep 2026, none started**
(`docs/session-memory/2026-09-05b-tufts-fdi-improvement-council.md`). The 64.8% end-to-end /
78.6%-of-detected decomposes cleanly: quadrant is already 96.3% correct on detected teeth, so the
failure is the position digit — `off_by_one` + `same_quadrant_far` are 14.6 pp and **74% of all
Tufts numbering errors**, and the Hungarian assignment in `assign_fdi_head` enforces uniqueness
but not anatomical sequence consistency. A literature pass (firecrawl) found the field's
consistent answer is an explicit structural prior — a sequence-repair pass, a graph over teeth,
or a spatial-prior transformer — plus a first-class missing-tooth stage: **Zhang et al.,
*A Reliable Multi-Stage System*, IEEE JBHI 2025** (the `zhang2025reliable` we already cite —
evaluated *on Tufts*, with a symmetry-aware segmentor + a dedicated missing-tooth detector and
post-hoc FDI index completion; code at github.com/qklee-lz/SADP-Net); **Lin et al.,
*Structure-Guided Tooth Numbering*, J Imaging 2026** (an anchor-and-extend post-processor,
weighted F1 0.687 → 0.813); **Li et al., *Spatial Prior-Guided Bi-Directional Cross-Attention
Transformers*, IEEE TMI 2024**; **van Nistelrooij et al., BMC Oral Health 2024** (numbering
costs ~0 mAP given a large FDI corpus — and OdontoAI, 2,000 FDI+mask panoramics, plus MICCAI STS
2024, 2,380 OPGs, are unused public corpora). **The positional-feature-shift diagnostic was run 6 Sep 2026** (`RESULTS_LOG` 2026-09-06,
`scripts/eval/tufts_pos_feat_diagnostic.py`) and **falsified that hypothesis**: rescaling every
Tufts positional feature to the DENTEX-train distribution (the `bh` 0.175 vs 0.233 shift and the
rest) moves crop-level FDI-exact by **+0.1 pp**. The Tufts weakness is the **image-derived
position digit** — 73.5% on GT-box crops vs DENTEX's 91.9%, while SIDE (97.8 vs 99.1) and
quadrant (97.4 vs 99.0) nearly match — concentrated in the crowded anterior region Tufts scores
and DENTEX mostly does not. This *confirms* an anatomical sequence / arch-order post-processor
(the "Option A" above) as the right lever — it corrects the off-by-one / position-digit class
without needing the head to tell position 4 from 5 by appearance — and *weakens* a plain
multi-corpus head retrain (more data of the same anterior-crowding difficulty is unlikely to
move an image-pathway limit). A better image-pathway position encoder (higher-resolution crops,
wider context, or a spatial-prior transformer) is the post-submission lever that would attack
the 73.5% directly. **The pre-registration for the post-processor ("Lever C") is drafted 6 Sep**
(`outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md`,
`docs/session-memory/2026-09-06b`): two arms (a simple monotonic re-sort and an anchored
max-log-prob DP), primary bar = Tufts FDI-exact-of-detected Δ 95%-CI lower bound ≥ +2 pp, a
DENTEX no-regression guard, one frozen threshold (τ = the existing `LOW_CONFIDENCE` 0.30), zero
GPU, a 3-day box. **It ran on 6 Sep and it is a null** (`RESULTS_LOG` 2026-09-06b,
`outputs/lever_C_fdi_structural_postproc/run_summary.txt`): Tufts FDI-exact-of-detected
**+0.29 pp [−0.07, +0.69]** for the DP arm and +0.16 pp [−0.22, +0.58] for the cheap
sort arm, against a pre-registered +2.0 pp lower-bound bar, with DENTEX slightly down
(−0.30 pp [−1.27, +0.61] of-detected). Both arms are retained behind `--assignment`; the
default stays the Hungarian assignment and no current-best number moves. The mechanism was
measured rather than assumed: of 3,489 Tufts test detections, **72.6% are anchors** (immovable
by construction, because τ = 0.30 — frozen to the codebase's existing `LOW_CONFIDENCE` so the
lever would add no tunable — is permissive enough that the head clears it on most teeth,
*including* teeth it is confidently wrong about), **13.4% sit in over-full quadrant groups**
(more than 8 detections, where no strictly increasing labelling of 1..8 exists), and only
**13.9% are movable at all**. The one stratum where the constraint does what it was designed
for is the contiguous-arch subset: **+2.36 pp on 296 detected teeth**, 9.5% of the cohort.
**Two levers are now excluded from opposite directions** — the positional features (Option B,
+0.1 pp) and the assignment's missing sequence constraint (Lever C, +0.29 pp) — which leaves
the image-derived position digit itself (73.5% vs DENTEX 91.9%) as the only remaining
explanation, and makes the case for it by elimination rather than by assertion. **For the manuscript, lead the Tufts numbering discussion with of-detected
78.6%** (detector-independent, and the number directly comparable to prior work's pre-cropped
accuracies) **and present 64.8% end-to-end as detection-bound**, with the `models/06` bbox
detector's 71.5% as the same-domain operating-point reference.

---

### 8.17 Caries failure panel — what the 0.40 precision is actually made of

**Added 27 Aug 2026**, held-out test split (863 crops, 127 positive), at the pipeline's own
operating point. Precision 0.398 / recall 0.740 reproduces the documented figure exactly.
TP 94 · FP 142 · FN 33 · TN 594. Figure: `figures/paper/caries_failure_panel_test.png`.

**The question this settles.** The negative class is 5,366 healthy + 179 impacted + 22 periapical,
and it has never been established whether the low precision comes from confusing *other pathology*
for caries or from over-calling *healthy* teeth:

| Negative subtype | n | false positives | FP rate |
|---|---|---|---|
| healthy | 714 | 137 | **19.2%** |
| impacted | 21 | 4 | **19.0%** |
| periapical | 1 | 1 | *100% (n=1, meaningless)* |

**19.2% on healthy against 19.0% on impacted is the same number**, and **137 of 142 false
positives (96.5%) are healthy teeth**. The gate is not confusing pathology-for-pathology. Write
this explicitly — it rules out the obvious remedy (a third negative label) and redirects the
problem to what the model treats as caries-like texture.

**An observation for a clinician to confirm before it becomes a claim.** All eight
highest-confidence false positives are `healthy` teeth at raw 0.95–0.99, and **several visibly
carry restorations or root-canal fillings**. If that holds, it bears directly on §8.1's
presumed-negative assumption: DENTEX "healthy" means *no disease annotation*, and **a restored
tooth has already been treated for caries** — so it is not a clean negative, and the gate may be
right about the tooth while wrong about the label. **That would make the negative-class
definition, not the classifier, the defect worth reporting.** It is not yet verified.

**False negatives run counter to intuition:**

| Positive subtype | n | missed | FN rate |
|---|---|---|---|
| caries | 108 | 27 | 25.0% |
| deep_caries | 19 | 6 | **31.6%** |

`deep_caries` is missed **more** often than ordinary caries. Support is 19 crops, so this is a
flag rather than a finding, and it must be reported with that support attached.

---

### 8.18 Training dynamics — the bone-loss model overfits, and its headline is a noisy maximum

**Regenerated 27 Aug 2026** from committed artifacts (`models/03/training_history.json`, 32
epochs). Figures: `figures/paper/stage4a_training_curves.png`,
`figures/paper/stage34_confusion_matrices.png`.

**Train loss falls 0.126 → ~0.002 while validation loss flattens near 0.05 from about epoch 5 and
never improves again** — a ~25x gap. The Stage-4a model **overfits heavily**. With 711 positive
training crops, themselves partly augmented duplicates of the same teeth, that is expected; it had
simply never been shown.

**The 0.9233 is the maximum of a noisy curve, and should be reported as such.** Diseased-class
validation F1 oscillates between roughly **0.40 and 0.85 from epoch to epoch**. There are only
**59 validation positives**, so one tooth moves F1 by ~1.7 points and those swings are sampling
noise rather than learning. Selecting the best of 32 such draws is **optimistically biased** — the
reported figure is a peak, not a stable estimate, and a bootstrap or repeated-split estimate would
almost certainly sit lower.

**This is corroborating evidence for §8.13, not a separate complaint.** A model that memorises its
training positives and is then selected on the peak of a noisy validation curve is precisely the
model one expects to collapse out of domain — and it does, on two independent external datasets.
The training dynamics and the domain-shift measurement tell the same story from different ends.

**The caries gate degrades val → test**: precision 0.515 → **0.398**, macro-F1 0.735 → 0.695. The
test figure is the one to quote.

⚠️ **Two figures cannot be regenerated and are not faked.** Caries training curves —
`results.json` records `best_epoch` and final metrics but no per-epoch history. Stage-4b severity
confusion matrix — only per-class F1 was saved, on 52 crops. Both gaps are printed by
`make_stage34_figures.py` itself.

---

### 8.19 Dataset ethics, licensing and de-identification — with two unresolved compliance items

**Written 27 Aug 2026.** ISBI requires an ethics statement, and this section is the material for
it. It is deliberately blunt about what is **not** yet cleared, because two items here can block a
submission and one of them is a licence breach that is live today.

#### 8.19.1 Per-corpus status

| Corpus | Role | Licence / terms | De-identified? | Status |
|---|---|---|---|---|
| **Tufts Dental Database** | detector + bone-loss training | **Restrictive, read verbatim from `tdd.ece.tufts.edu` (26 Aug 2026)** — see below | Yes, by the provider | ⚠️ **BREACH TO RESOLVE** |
| **DENTEX** | caries + FDI-head training, Stage-2 eval | ✅ **VERIFIED 4 Sep 2026 — CC-BY-NC-SA-4.0.** Confirmed on the dataset's Hugging Face README: "all elements of the DENTEX dataset are released under a Creative Commons Attribution (CC-BY-NC-SA) license... freely used for non-commercial research purposes... provided that the original work is properly cited and any derivative works are shared under similar terms." Non-commercial research use, attribution and share-alike are all satisfied by this project (research use, cited as `hamamci2023dentex`, no redistribution of the data itself). | Public challenge release (MICCAI 2023, `github.com/ibrahimethemhamamci/DENTEX`) | ✅ compliant |
| **Ningxia** | locked external test (4 hospitals) | ✅ **VERIFIED 4 Sep 2026 — no formal licence, informal non-commercial request only.** The source repo (`github.com/qinxin99/qinxini`) carries no LICENSE file and no CC/OSI licence text; the only stated term is "we kindly request that you do not use it for any commercial purposes." Weaker than DENTEX's formal licence, but this project's use (non-commercial research, no redistribution) satisfies it. The source paper (Li et al. 2024, `li2024multicenter`, now added to `source.bib` and cited in `main.tex` — it was not cited before this pass despite the repo requesting citation on use) requests citation on use. | Public release, `Journal of Imaging Informatics in Medicine` 37(2):831-841 | ✅ compliant, weaker terms noted |
| **SDH clinic (3,219 images)** | not used in any result | Institutional; no data-use agreement recorded | **Images yes, mapping file NO** | ⛔ **IRB not started; de-identification void** |

#### 8.19.2 Tufts — the terms, and the breach

The release agreement states, verbatim:

> *"No permission is granted to reproduce the database or post into any webpage or any other
> storage means."*
> *"The Researcher may not provide research associates and colleagues with access to the Database."*
> *"The distribution of this database to any parties that have not read and agreed to the terms and
> conditions of usage is strictly prohibited."*
> *"Failure to follow the above steps will invite legal prosecution."*

**Two separate problems follow from that, and they need different remedies.**

1. **A Google Drive folder holding the raw `ZIP/` release was found browsable without signing in**
   (`docs/EXTERNAL_DRIVE.md`) — i.e. link-accessible to anyone. That is squarely what the
   agreement forbids. **Remedy: restrict the folder, keep Tufts local-only, and share the release
   *form* rather than the files.** Account-owner action; unresolved as of this writing.
2. **Real Tufts radiograph pixels are embedded as base64 output in 7 tracked notebooks, already
   pushed to `origin/main`** (RESULTS_LOG 2026-08-26b). The repository is confirmed **private**, so
   this is deferred risk rather than an active disclosure — an explicit user decision on 26 Aug —
   but **it must be resolved before this repo, or any fork, is ever made public**, and before any
   artefact derived from it is distributed. Remedy: strip outputs going forward, or rewrite
   history (destructive, needs a force-push).

**Consequence for the paper:** figures may show Tufts-derived *crops and overlays* as analysis
output, which is normal scholarly use, but **no part of the database may be redistributed** and the
paper must not link to any copy of it. Cite the source and point readers at the release form.

#### 8.19.3 DENTEX and Ningxia — honestly unestablished

Neither licence is recorded in this repo. `docs/EXTERNAL_DRIVE.md` says of DENTEX only that it
"is a separate matter … check its own licence", and that check has never been done and written
down. **This section will not guess at terms.** Before submission, someone must read and record,
for each: the licence name, whether redistribution is permitted, whether commercial use is
restricted, and the required citation form. Both are widely used public datasets, so the expected
answer is permissive — but *expected* is not *verified*, and an ethics statement asserting a
licence nobody read is exactly the kind of claim that should not appear in a paper from this
project.

Ningxia carries an additional, self-imposed constraint that **is** documented and honoured: it is
locked external test data, never trained or tuned on (`MASTER_PLAN_2026H2.md` §4.1). Sections
§8.12/§8.12a record how many times it has been evaluated.

#### 8.19.4 The clinic dataset — not used, and not usable yet

The SDH set (3,219 enhanced radiographs) **contributes to no result in this work** and must not,
until two things are true:

1. **The de-identification is currently void for the shared copy.**
   `metadata/index.csv` — the 267 KB re-identification mapping — sits as a **sibling of
   `images/`** under the same shared Drive folder. `clinical_dataset_provenance.md` §4 forbids
   exactly this: *"`index.csv` must never travel with `images/` … If both move together, the
   de-identification is void."* §4a records that it had already happened. Sharing is
   account-to-account, not a public link, so this is a protocol breach rather than a public
   disclosure — but the file-structure de-identification provides **no protection** for that copy.
   **Remedy: move the mapping out of the shared tree and keep it offline.**
2. **IRB approval has not been started.** Zero progress, and it has the longest lead time of
   anything open in this project.

**Write it this way in the paper:** the clinic data is described as future work with governance
pending, and **no clinic-derived number appears anywhere**. That is accurate today and keeps the
paper clean.

#### 8.19.5 Pre-submission checklist

- [ ] Restrict the Tufts Drive folder; confirm it is no longer link-accessible
- [x] Read and record the DENTEX licence, redistribution terms and citation form.
      **Done 4 Sep 2026** — CC-BY-NC-SA-4.0, compliant. See §8.19.1.
- [x] Read and record the Ningxia licence and citation form.
      **Done 4 Sep 2026** — no formal licence, informal non-commercial request; source paper
      added to `source.bib` and cited in `main.tex` (was missing). See §8.19.1.
- [ ] Move SDH `metadata/index.csv` out of the shared Drive tree
- [ ] Decide on the embedded Tufts pixels in the 7 notebooks **before** any public release
- [ ] Start IRB paperwork if clinic data is ever to be used
- [x] Confirm no figure in the submitted paper redistributes any part of a restricted database.
      **Done 4 Sep 2026.** All five figures the manuscript includes (`fig_baselines.png`,
      `fig_calibration.png`, `fig_coverage.png`, `fig_stage2.png`, `fig_boneloss.png`) were
      opened and inspected directly, not just traced to a generator script (several of the
      original generator scripts predate the 28 Aug rebuild and could not be located). Every one
      is a matplotlib bar/line chart built from aggregate JSON metrics -- no panel contains a
      reproduced radiograph, a crop, or an overlay of one. No figure carries any Tufts, DENTEX or
      Ningxia pixel data. `RESULTS_LOG` 2026-09-04k.

---

### 8.20 C1 — the VLM baseline, and why its score must be reported with a control

**Run 27 Aug 2026** on the 164 leak-free DENTEX images, zero-shot, one scorer for both arms.
Model: **Qwen2.5-VL-7B-Instruct** (open-weight, so another lab can rerun this — the same
reproducibility argument the survey makes).

**Task choice, decided by measuring the data first.** "Does this radiograph show caries?" is
degenerate on this set: **148 of 164 images (90.2%) contain caries**, so a model answering "yes"
always scores 90.2% and specificity rests on 16 images. C1 therefore asks **which teeth, by FDI
code** — 477 affected teeth — scoring both arms on the per-image FDI set.

| Arm | Precision | Recall | **F1** | exact-set | latency |
|---|---|---|---|---|---|
| **Our six-stage pipeline** | 0.235 | **0.390** | **0.294** | 1.2% | 2.39 s/img (CPU) |
| Constant guess `{26,36}` — **image ignored** | 0.250 | 0.172 | **0.204** | — | 0 |
| Qwen2.5-VL-7B-Instruct, zero-shot | 0.236 | 0.103 | **0.143** | 5.5% | 1.08 s/img (A100) |

**The headline is not "we beat the VLM by 2x". It is that the VLM does not beat a constant.**
A fixed answer of `{26,36}`, ignoring the image entirely, scores **F1 0.204** against the model's
**0.143**.

**The control that establishes it.** The same prompt was run against a real radiograph, a **blank
grey image**, and a **random-noise image**. Blank and noise both returned `26,36` — the identical
confident dental answer given for a real radiograph. Across all 164 radiographs the model emitted
only **6 distinct answers**, two of which cover 110 images. 26, 36 and 37 are among the most
common caries sites: **the model is reciting a prior, not reading the image.**

**Efficiency, which is the other half of C1's brief.** The VLM is **8.29 B parameters, 18.01 GB
peak VRAM, 1.08 s/image on an A100-80GB**. This pipeline is **83.6 M parameters across six
models (61.2 M on the caries path)** — corrected 28 Aug 2026 by counting the checkpoints; the
earlier "~25 M" was the superseded bbox detector alone. It runs at **2.39 s/image on CPU with no GPU at all**, and scores **2.1x the F1**. The
"small specialist beats large generalist, at a fraction of the compute" claim is now measured
rather than assumed.

⚠️ **State the limits, or a reviewer will.** One model, zero-shot, one prompt, one task. This does
**not** show VLMs cannot read radiographs — it shows this model, prompted this way, does not, and
that its score reflects a prior rather than perception. A larger, few-shot, or domain-tuned VLM
could differ. **Always publish the constant-guess control beside the number:** 0.143 alone reads
as "slightly worse"; with the control it reads correctly as "not performing the task".

---

### 8.21 C4 — abstention: the system knows when to decline

**Run 28 Aug 2026**, CPU only. `MASTER_PLAN_2026H2.md` R3 asks for an explicit `not_assessable`
output with a calibrated threshold, reported as a coverage-accuracy curve. The flag has existed
since R4; **the curve had never been drawn**, so C4 was at zero while appearing complete.

| Coverage | Stage 2 - FDI numbering | Caries gate (calibrated) |
|---|---|---|
| 100% (no abstention) | 0.826 | 0.797 |
| 90% | 0.849 | 0.857 |
| 75% | **0.885** | **0.940** |
| 50% | 0.918 | 0.970 |
| gain at 75% coverage | **+5.91 pp [+3.88, +7.68]** | **+14.25 pp [+11.32, +16.63]** |
| same, confidences shuffled | +0.03 pp | +0.00 pp |

Stage 2 is scored on 661 detected teeth (FDI exact match); the caries gate on 863 held-out crops
using **isotonic-calibrated** confidence in the reported class — an abstention rule built on scores
known to be overconfident would decline the wrong cases.

**The control.** Shuffling the confidences collapses both gains to zero (+0.03 / +0.00 pp). The
improvement therefore comes from the confidence ranking carrying real information about
correctness, not from the arithmetic of discarding items. Report it beside the curve, for the same
reason C1's constant-guess control is reported beside its F1.

**The pre-registered threshold holds up, and was not tuned.** `ASSESSABILITY_MIN_FDI_CONFIDENCE =
0.30` was fixed a priori. On this curve it retains **90.8% of detected teeth at 0.847** — within
0.2 pp of the empirical 90%-coverage point. No "optimal" threshold is reported: choosing one on
the evaluation set is precisely the error the constant was written to prevent.

**Why the caries branch gains 2.4x more.** Stage 2 needs confidence >= 0.962 to reach 75% coverage
— the numbering head saturates near 1.0 on most teeth, leaving little to rank by. The
overconfidence measured in 8.15 shows up here as a limit on how much abstention can buy.

**Caveat that must survive into the paper.** Stage-2 coverage is over *detected* teeth. Abstention
cannot recover the 29.4% Stage 1 never finds: 75% coverage is 75% of 70.6% — **53.0% of teeth
actually present**. Never write coverage as "share of the mouth reported". Both curves are also
internal (DENTEX) — there is no external abstention curve — and the caries curve below ~10%
coverage is small-n noise.

Figure: `docs/results/figures/paper/c4_coverage_accuracy.png`.

---

### 8.22 C1 hardened — scale, prompting, and the constant that beats us

**Run 28 Aug 2026**, H100 80GB, 59 min. Answers the three obvious objections to §8.20's
one-model/zero-shot/one-prompt baseline, and adds the baseline that should have been there first.

| System | P | R | **F1** | params | hardware |
|---|---|---|---|---|---|
| **Held-out constant** `{16,17,26,27,36,37,46,47}` — **image never read** | 0.218 | 0.600 | **0.320** | 0 | none |
| Our six-stage pipeline | 0.235 | 0.390 | **0.294** | 61.2 M† | CPU, 2.39 s/img |
| Qwen2.5-VL-32B-Instruct, zero-shot | 0.250 | 0.243 | **0.246** | 33.45 B | H100, 70.1 GB, 1.46 s/img |
| Qwen2.5-VL-7B-Instruct, zero-shot | 0.248 | 0.107 | **0.149** | 8.29 B | H100, 0.69 s/img |
| Qwen2.5-VL-7B, **2-shot** | 0.196 | 0.040 | **0.066** | 8.29 B | H100, 1.93 s/img |
| Qwen2.5-VL-7B, **4-shot** | 0.150 | 0.019 | **0.034** | 8.29 B | H100, 3.36 s/img |

**Reproducibility.** The 7B zero-shot number reproduces at **0.149 vs 0.143** across different
hardware *and* a different transformers major version. The library version is now recorded in every
arm file.

**Scale helps; §8.20's claim must be narrowed.** 7B 0.149 -> 32B 0.246. The statement "the VLM does
not beat a constant guess" was measured against a *hand-picked* constant (0.204) and on the **7B**.
The 32B clears that constant. State the model and the constant, or the claim is not falsifiable.

**Few-shot degrades it monotonically** — 0.149 -> 0.066 (2-shot) -> 0.034 (4-shot), with exemplars
drawn only from leakage-excluded images. The mechanism is abstention, not perception: empty answers
rise 56 -> 113 -> **123 of 164**. Exact-set match *rises* over the same sweep purely because 16
images contain no caries; **never report that column alone.**

**⚠️ The finding that constrains how C1 may be written up.** A fixed answer of the eight first and
second molars — fitted on the 78 leakage-excluded images, frozen, and never tuned on the scored set
— scores **F1 0.320**, above our pipeline's **0.294**. It wins on recall (0.600 vs 0.390) and loses
on precision (0.218 vs 0.235).

Caries in DENTEX is overwhelmingly molar, so **tooth-level FDI-set F1 is base-rate dominated and
cannot on its own demonstrate clinical value.** Consequences for the paper, all mandatory:

1. Publish this constant as a row in the C1 table, beside every model arm.
2. Do **not** headline C1 as "small specialist beats large generalist" without it.
3. The efficiency argument survives intact and is worth keeping: 33.45 B parameters and 70.1 GB of
   H100 VRAM still lose to **61.2 M** parameters on a CPU († caries path; 83.6 M for all six
   models). Counted from the checkpoints 28 Aug 2026 — the earlier "~25 M" was the detector alone.
4. This bears on C1 only. Stage-2 numbering, detection, abstention (§8.21) and external validation
   (§8.12) are measured on other metrics and are untouched.

**Controls still fire for both models.** 7B: blank and noise both return `26,36`, identical to a
real radiograph. 32B: blank correctly returns `NONE`, but noise returns the full eight-molar list,
identical to its answer for a real radiograph.

---

### 8.23 A third FDI corpus — what it buys, and what it does not

**Run 28 Aug 2026.** The Stage-2 head trained on DENTEX + Tufts; this adds the Kaggle
*dual-labeled* corpus (499 images, 13,166 teeth) as a third source. Two corpora make
"it generalises" an assertion with one degree of freedom; three make it a claim.

Compared against a **control trained the same day** on the same rebuilt DENTEX+Tufts crops — same
code, seed, epochs, machine — so the corpus is the only variable. Crop-level, GT boxes, plain
argmax, FDI exact. Deltas paired, bootstrapped over source images, exact McNemar alongside.

| corpus (split) | n | v2 control | v3 | delta | 95% CI | verdict |
|---|---|---|---|---|---|---|
| **DENTEX** val | 2,729 | 91.4% | **92.5%** | **+1.14 pp** | [+0.33, +1.95] | **significant** (p=0.013) |
| **Tufts** test | 3,786 | 75.0% | 75.8% | +0.74 pp | [-0.37, +1.89] | **not significant** (p=0.25) |
| **Kaggle** test | 1,994 | 77.7% | **93.2%** | +15.45 pp | [+12.79, +18.28] | significant, but see below |

**The honest reading, which the paper must carry:**

* The **Kaggle +15.45 pp is not evidence of generalisation.** v3 trained on that corpus; the
  control had never seen it. Report it, but never as the headline.
* The **result is DENTEX +1.14 pp** — a third corpus improved accuracy on a corpus it added no
  data to, and the gain survives its interval.
* **Tufts is flat** (+0.74 pp, CI crosses zero). Not a gain.
* **Nothing regressed**, on any corpus or metric.
* **Pooled val is not comparable** across the two heads (different val mixtures) and inflates the
  effect roughly threefold. Use the per-corpus table.

**Adoption:** v3 stays a reported ablation. The pipeline default remains v2, because swapping it
invalidates the 58.3%/82.6% Stage-2 headline, the §8.21 coverage-accuracy curves and the §8.16
taxonomy, all measured against v2.

**Two data corrections worth stating in the paper's dataset section:** this corpus is **500
images, not the 2,000** the plan assumed, and its numbering was **verified as standard FDI by an
independent arbiter** (80.3% direct vs 1.7% mirrored) rather than taken on trust — Tufts presented
as plain Universal and was left-right mirrored.

### 8.24 Why the caries score is what it is — the gate has partially become the constant

§8.22 reports that an image-blind molar constant beats this pipeline on tooth-level caries
(F1 0.320 vs 0.294), and frames it as a property of the metric. **This section supplies the
mechanism, and it is a stronger version of the same argument:** the caries gate itself scores
teeth partly by *which tooth it is*, not by whether a lesion is present.

**The measurement** (`scripts/eval/caries_position_bias.py`, held-out test, 863 crops from 34
source images; the script reproduces the published confusion matrix TP 94 / FP 142 / FN 33 /
TN 594 before reporting anything, so the analysis path is anchored to a known reference):

| tooth type | n | pos | precision | recall | FP rate | mean P(caries) on *healthy* teeth | train base rate | within-type AUC |
|---|---|---|---|---|---|---|---|---|
| incisor | 266 | 8 | 0.091 | **0.125** | 0.039 | 0.075 | 0.017 | 0.681 |
| canine | 129 | 5 | 0.333 | **0.200** | 0.016 | 0.087 | 0.023 | 0.748 |
| premolar | 221 | 31 | 0.292 | 0.677 | 0.268 | 0.273 | 0.157 | 0.781 |
| molar | 247 | 83 | 0.473 | 0.855 | **0.482** | **0.478** | **0.343** | 0.781 |

Two readings, and both belong in the paper:

1. **The prior is doing visible work.** The gate's mean score on teeth that are *genuinely
   healthy* tracks the training base rate for that position almost monotonically — 0.075 on
   healthy incisors against a 0.017 base rate, 0.478 on healthy molars against 0.343. The
   operational cost: **48.2% of healthy molars are flagged carious**, and 79 of the 142 false
   positives are healthy molars. That is where precision 0.398 comes from. Symmetrically, the
   gate finds **1 of 8 incisor lesions**.
2. **There is nonetheless real lesion signal.** Ranking *within* one tooth type removes the
   shortcut, and **within-type AUC is 0.7454, 95% CI [0.6604, 0.8420]** — excluding 0.5. Pooled
   AUC (0.8548) is inflated because ranking a molar above an incisor is free. A position-only
   predictor that never sees an image reaches **AP 0.2962**, against the model's 0.5503 and a
   chance line of 0.1472.

So the honest statement is neither "the model works" nor "the model is a lookup table". It is
**a model with modest genuine lesion discrimination, whose reported score is substantially
inflated by an anatomical prior that a constant baseline captures for free.** That is exactly why
§8.22's constant is competitive, and it converts that finding from an observation about a metric
into a measured statement about the system.

**Two fixes were tried and neither worked. Both are reported.**

- **Per-tooth-type decision thresholds** (fitted on val, applied once to test): F1 **+0.006,
  95% CI [−0.034, +0.041]** — not significant, and no better than re-fitting one global
  threshold. The shipped 0.50 is already F1-optimal across a 19-point sweep. The decision rule
  cannot be tuned into a better one.
- **2.67× more caries training data** (gate v4, `outputs/caries_v4/`): DENTEX carries 2,767
  caries-family annotations and the training corpus used 1,049, so **62% of the available
  supervision was unused**. Adding it lifted train positives 723 → 1,928. On the *same* 863-crop
  test set, **average precision went 0.5503 → 0.5496**, paired delta **−0.0015, 95% CI
  [−0.0886, +0.0821]**; every other paired delta also spans zero. **v4 was not adopted.**

**What that negative result licenses the paper to say:** the caries branch's ceiling on this data
is not set by how many labelled lesions it has seen. Combined with the reading above, the
constraint is the discriminability of the task as posed — a tight per-tooth crop, a binary label,
and a negative class built on the presumption that an unannotated tooth is healthy.

⚠ **A trap to document rather than fall into.** v4's report shows caries P 0.71 / R 0.80 on v4's
*own* test split, against v3's published 0.398 / 0.740. That is not an improvement: v4's split has
**2.2× the caries prevalence** (0.324 vs 0.147), and precision is a function of prevalence.
Specificity, which is model-intrinsic, is essentially unchanged (0.853 vs 0.843). This is worth a
sentence in the paper's evaluation-protocol section, because it is the same class of error the
constant baseline exists to catch: **a number that rises because the denominator changed.**

**Also ruled out by measurement:** raising input resolution. The median tooth box is 170×287 px
against the 224×224 the model already receives — a 1.04× linear resize, with 58% of boxes already
upsampled. There is no detail left to recover at this crop geometry.

**Three further arms were then pre-registered and run, and none met the bar.** CLAHE contrast
equalisation, a 1.25× crop expansion (interproximal caries sits at the contact point a tight box
cuts through), and position-balanced sampling, each against a same-day control whose val macro-F1
reproduced v3's published 0.7350 exactly. Acceptance was fixed in advance — paired ΔAP with a 95%
CI excluding zero — in `outputs/caries_arms/PRE_REGISTRATION.md`:

| arm | AP | ΔAP vs control | verdict |
|---|---|---|---|
| control | 0.5503 | — | — |
| **CLAHE** | 0.5977 | **+0.0488 [−0.0031, +0.0993]** | **misses by 0.0031** |
| crop 1.25× | 0.5684 | +0.0198 [−0.0367, +0.0810] | not significant |
| position-balanced | 0.5943 | +0.0432 [−0.0328, +0.1157] | not significant |

**The bar was not moved.** One real secondary effect survives: **CLAHE buys precision (+5.6 pp,
CI [+0.011, +0.101]) with no significant recall cost**, cutting the false-positive rate in every
stratum. The 1.25× arm's precision gain is cancelled by a *real* recall loss — a slide along the
curve, which the flat AP confirms. A pre-registered prediction that position-balancing would
*lower* AP (because the population genuinely carries 3.4× more caries in molars) was **falsified**.

**Five independent attempts have now failed to lift this curve** — threshold tuning, per-stratum
thresholds, 2.67× the training positives, CLAHE, crop expansion and position balancing. **That the
caries branch has reached its headroom on DENTEX is now the supported reading**, and the paper can
state it as such. The binding limitation on settling the remaining candidate is statistical, not
methodological: the test split has 863 crops but only **34 source images**, and intervals are
clustered over images because teeth within a radiograph are not independent. A +0.049 AP effect
cannot be separated from zero at n=34.

Source: `RESULTS_LOG.md` 2026-08-31 and 2026-08-31b, `outputs/caries_position_bias/`,
`outputs/caries_v4/run_summary.txt`, `outputs/caries_arms/run_summary.txt`.

### 8.25 A sixth cohort, and the strongest form of the paper's central claim

§8.22 showed an image-blind constant beating this pipeline on DENTEX by 4.6 pp; §8.12/2026-08-28e
showed the two **indistinguishable** across four Ningxia hospitals. A third, independent
6,000-image caries corpus was then evaluated with the **frozen** pipeline — nothing trained, no
checkpoint changed, same centroid-containment matcher imported from the Ningxia script.

| cohort | n | pipeline | constant | constant − pipeline | verdict |
|---|---|---|---|---|---|
| DENTEX | 164 img / 479 lesions | 0.443 | 0.489 | +0.046 [+0.006, +0.089] | constant wins |
| Ningxia, 4 hospitals | 337 img / 1,013 lesions | 0.408 | 0.399 | −0.009 [−0.049, +0.030] | indistinguishable |
| **CariesXrays** | **1,500 img / 3,421 lesions** | **0.309** | **0.561** | **+0.252 [+0.232, +0.273]** | **constant wins decisively** |

**This is the largest lesion count of any cohort in the paper — more than DENTEX and Ningxia
combined — and the largest margin.** Paired cluster bootstrap over images, 10,000 resamples,
seed 42. A prefix draw (first 600 by file id) gave +0.240 [+0.211, +0.269]; the randomised draw
reproduces it, so the sample carries no ordering bias.

**The mechanism is measured, not inferred.** Mapping each lesion to the detected tooth containing
it: **72.0% of lesions are on molars** (premolar 20.5%, canine 3.7%, incisor 3.7%), and **60.2%
fall on exactly the eight teeth the constant emits**. The constant's 0.561 sits near its
structural ceiling of ~0.60 on this cohort. It is not out-diagnosing the pipeline; it is
exploiting an extremely molar-concentrated disease distribution — which is precisely the claim
§8.24 makes about the gate itself, now demonstrated at cohort scale.

**And the brute-force defence fails here.** On DENTEX the constant flagged only 14% more teeth at
the same match rate, so volume did not explain its win. On this cohort it flags **64% more teeth
(6.45 vs 3.94 per image) *and* has the higher match rate (0.207 vs 0.190)** — it wins on both
axes. That defence should not be reused without checking it per cohort.

**A ceiling worth stating:** **22.1% of lesions fall inside no detected tooth at all**, which
bounds every tooth-level arm on this cohort, ours included.

**The cohort is a published, peer-reviewed benchmark.** Chen et al., *CariesXrays: Enhancing Caries Detection in Hospital-Scale Panoramic Dental X-rays via Feature Pyramid Contrastive Learning*, **AAAI 2024**, 38(20) 21940–21948, DOI 10.1609/aaai.v38i20.30196; code and data at
`github.com/Binz-Chen/AAAI2024_CariesXrays`. It is described by its authors as hospital-scale,
"meticulously annotated by dental professionals", and it ships its own FPCL baselines. Identity
was verified against AAAI's OJS, ACM DL, DBLP and AAAI's Underline session page rather than the
repository README alone. Their stated 6,000 images matches exactly.

**Corrected 4 Sep 2026 (`RESULTS_LOG` 2026-09-04j).** The instance count was recorded on 1 Sep as
"their stated 13,783 against 13,784 measured here, a +1 (0.007%) counting-convention difference".
The 13,783 came from the **GitHub README**. The **AAAI paper states 13,778** (p. 21942, verified
against the PDF). So the authors publish two different figures, and ours is a third:

| source | caries instances |
|---|---|
| AAAI paper, p. 21942 | 13,778 |
| authors' GitHub README | 13,783 |
| **counted here, non-degenerate boxes in the release** | **13,784** (13,785 raw `<object>` entries) |

`main.tex` now reports **our own 13,784** and names all three, rather than adopting one of theirs.
Nothing downstream depends on which is right — no number in this project is derived from the
published count. **Licence is not stated** — there is no LICENSE
file and the GitHub API reports none — so the Data Availability statement should say "released
publicly by the authors alongside the AAAI paper; no explicit licence stated; cited as requested."

**The caveat that does remain:** the corpus's annotation *exhaustiveness* is not documented, so
`match_rate` is reported as a diagnostic and a flagged tooth carrying no annotated lesion is **not**
a confirmed false positive — the same restraint §8.11 applies to DENTEX.

**A methodological point worth one sentence in the paper.** 27.3% of this corpus's annotation
files carry a wrong image width, and a converter normalising by the stated size rather than the
decoded image would corrupt a quarter of it silently — the same class of defect that voided a
90-epoch training run here (§8.8). The coordinates were verified to be in the true frame two ways
before anything was measured.

Source: `RESULTS_LOG.md` 2026-09-01, `scripts/eval/cariesxrays_external.py`,
`outputs/cariesxrays_external_rand/`.

---

### 8.26 Lever 2 — an off-the-shelf detector reaches the CariesXrays benchmark ceiling

§8.25 evaluated the *frozen pipeline* on CariesXrays as a sixth external cohort. This is a
separate, opt-in experiment: **train a standalone caries-lesion detector on CariesXrays' own
training data and report COCO AP beside its published table** — the project's first number on a
public benchmark's own metric, the kind a reviewer can place against prior work. It is **not
wired into the six-stage pipeline**, adopts no checkpoint, and changes no pipeline default. This
does not touch §8.22/§8.24 — those concern the *tooth-level* caries score, a different quantity
from lesion-level detection AP.

**⚠️ The comparison is indicative, not head-to-head.** The official FPCL 4,800/1,200 split is not
public (the FPCL repo ships only a 0.5% sample; the data download is images + annotations with no
`ImageSets`; DVCTNet obtained the split privately). This run used **our own seed-42 image-level
80/20 split** matching only their ratio, so it is scored on different random test images. The
manuscript must say this in these words and must not read as "we beat / matched FPCL".

**Table re-verified against the AAAI PDF, 4 Sep 2026** (Table 1, p. 21945 — `RESULTS_LOG`
2026-09-04j). Two rows of the 2 Sep transcription were wrong and are struck through below.

| method (their split) | AP | AP50 | AP75 | |
|---|---|---|---|---|
| RetinaNet R50 | 13.0 | 30.5 | 10.2 | ✅ verified |
| ~~DINO~~ | ~~37.8~~ | ~~75.3~~ | ~~29.4~~ | ❌ **no DINO row exists in their table** |
| Faster R-CNN R50 | 39.9 | 78.0 | 37.8 | ✅ verified |
| YOLOX | 40.5 | 81.3 | 36.1 | ✅ verified |
| **Conditional-DETR** | **42.2** | **80.6** | **40.4** | ⬅ **was missing; it is their strongest baseline** |
| FPCL (their method) | 48.2 | 84.1 | 50.6 | ✅ verified |
| DVCTNet (MICCAI 2025) | 48.9 | 84.7 | 52.2 | ⚠️ from arXiv 2508.20813, **not** verified — kept out of `main.tex` |
| **YOLOv11l, our split (Lever 2)** | **48.2** | **84.5** | **50.0** | ours |

Their full table has ten baselines (SSD 12.7, RetinaNet 13.0, DETR 25.7, EfficientDet 34.1,
FCOS 35.9, YOLOv7 39.3, YOLOv8 40.3, YOLOx 40.5, Conditional-DETR 42.2, Faster R-CNN 39.9) —
the five strongest are in `models/14_cariesxrays_lever2/run_summary.txt`'s correction block.
Their split is confirmed **4,800 train / 1,200 test** (p. 21942), so our seed-42 80/20 draw
matches their ratio.

**A generic 2024 one-stage detector with no caries-specific design reaches ~48 AP on this
benchmark's data** — level with the task-specific FPCL contrastive-learning method and **about
six** AP above the strongest of their ten baselines. *(The 2 Sep note said "~8 AP above every
off-the-shelf baseline". That compared against YOLOx at 40.5 because Conditional-DETR at 42.2
had been dropped from the transcription. The authors' own text gives both gaps: +7.7 over the
best CNN baseline, +6.0 over the best transformer one.)* The reading for the paper: this benchmark
does not appear to require a specialised architecture to reach its reported ceiling. (COCO AP@
[.5:.95] via `ultralytics val`, which uses the same 101-point definition as the `pycocotools`
`CocoEvaluator` the FPCL repo uses. `best.pt`, epoch 61 of 86, early-stopped. `batch` auto-reduced
32→16 after OOM at 1024 px on an A100-40GB; `mosaic=0` per this project's medical-imaging house
rule, which likely costs a few AP on small objects — recorded, not excused. Predictions track the
ground truth with no geometry error, `models/14_cariesxrays_lever2/val_batch*_pred.jpg`.)

**✅ DONE 4 Sep 2026 — this is now in `main.tex`** as `\subsection{A published benchmark, and
what a stock detector reaches on it}` (`sec:benchmarkrow`) in Related Work, with
Table~`tab:fpcl`, the split caveat in the authors' own terms, and no claim of matching or
beating FPCL. The FPCL / baseline numbers were re-verified against the AAAI PDF first, which is
what caught the two errors struck through above. DVCTNet is omitted from the manuscript because
it was never verified. One connective fact was added that was not in this section: **the
checkpoint behind our 48.2 AP is the same `models/14` that serves as Lever B's single-corpus
arm** — the arm that reaches 0.694 tooth-level agreement on this corpus and falls to 0.086 on
DENTEX. A strong benchmark number and a failure to transfer are the same model, which is the
paper's own argument turned on its own result.

Source: `RESULTS_LOG.md` 2026-09-02b, `models/14_cariesxrays_lever2/run_summary.txt`,
`outputs/lever2_cariesxrays/PRE_REGISTRATION.md`,
`scripts/yolo/{build_cariesxrays_detector_dataset,train_cariesxrays_detector}.py`.

---

### 8.27 The caries-constant problem, resolved on 2 of 3 cohorts — Lever B adopted

*(Renumbered from §8.26 on 4 Sep 2026: the two parallel sessions each wrote a "§8.26", this one
and the Lever 2 benchmark row above. This is the later of the two, so it moved. Anything citing
"§8.26" for Lever B before 4 Sep means this section.)*

§8.22 and §8.24 diagnosed *why* the tooth-level caries gate loses to an image-blind constant:
it "scores teeth partly by which tooth they are," its mean score on genuinely healthy teeth
tracking the training base rate for that position. §8.25 showed the same pattern generalises to
a sixth cohort, at cohort scale, with the constant winning outright. **Five direct attempts to
fix the gate — threshold tuning, per-tooth-type thresholds, a 2.67×-larger positive set (gate
v4), CLAHE, a 1.25× crop, position-balanced sampling — all returned effects with confidence
intervals spanning zero** (§8.24). Every prior number in §8.22/§8.24/§8.25 stands unchanged;
this section is the resolution, not a correction to them.

**Lever B changed the task rather than the model.** Instead of classifying a per-tooth crop
(where the position prior lives), a single-class YOLOv11l detector localises the lesion
directly — a mechanism with no per-tooth prior to lean on, tested against the *exact* metric
the constant was winning on: does the pipeline flag the tooth an expert-annotated lesion is
actually on? Pre-registered acceptance (`outputs/lever_B_lesion_caries_path/
PRE_REGISTRATION.md` Sec 6, frozen before any of the numbers below existed): beats the constant
**and** the gate, 95% CI excluding zero, on **≥2 of 3 external cohorts**, at ≤1.5× the
constant's flagging rate.

Two arms were tested. **B-single** (trained on CariesXrays only, `models/14`, reused zero-cost
from §8.25's Lever 2) won CariesXrays decisively but **lost DENTEX decisively** (8.6% vs. the
gate's 44.3% / constant's 48.9%, both deltas excluding zero the wrong way) and lost Ningxia too
— exactly the domain-transfer failure this project's whole external-validation thesis
(§8.1–§8.13) would predict from a single-corpus model. **B-pooled** added DENTEX-domain caries
boxes to the training data (whole-tooth granularity, a domain adapter, not a second lesion-box
source — `scripts/dentex/build_dentex_caries_boxes.py`) and recovered DENTEX to a **statistical
tie** with both comparators, at negligible cost to the still-decisive CariesXrays win:

| cohort | gate v3.0 | image-blind constant | **lesion detector (B-pooled)** | Sec 6 |
|---|---|---|---|---|
| DENTEX (148 img, 479 çürük) | 44.3% | 48.9% | 45.5% [40.9, 50.1] — tie, CI incl. 0 | fail |
| CariesXrays-val (1,200 img) | 31.7% | 56.2% | **68.4% [66.4, 70.4]**, Δ+12.2/+36.7 pp, CI excl. 0 | **PASS** |
| Ningxia (337 img, 1,013 lesions) | 40.8% | 39.9% | **50.0% [46.3, 53.9]**, Δ+10.2/+9.3 pp, CI excl. 0 | **PASS** |

Paired cluster bootstrap over images, 10,000 resamples, identical to every other CI in this
document. **2 of 3 cohorts pass all three conditions — Sec 6 is met.** Predicted-positive rate
stays at 0.6–0.7× the constant's on the winning cohorts, so neither win is a volume effect.

**Adopted as the Stage-3 pipeline default 4 Sep 2026** (`src/classifiers.py`
`run_caries_lesion_detector`; `scripts/run_inference.py` `DEF_CARIES_LESION_MODEL`). The gate
is retained, unchanged, selectable via `--caries-method gate` — every number in §8.22/§8.24/§8.25
and every table elsewhere in this document that does not explicitly say otherwise was measured
on the gate and remains reproducible on it. **Parameter count changed**: the lesion detector is
25.3 M params against the gate's 11.2 M, moving the caries-path total from 61.2 M to **75.3 M**
and the whole-pipeline total from 83.6 M to **97.7 M** (`docs/results/model_metrics.md`
"Pipeline size"). The C1 efficiency comparison (§8.20/§8.22, "61.2 M vs. Qwen's 33.45 B") should
be re-quoted as **75.3 M vs. 33.45 B, ~444×** wherever it appears in `main.tex` — still an
overwhelming efficiency advantage, a smaller multiple than the 550× figure computed against the
retained gate's parameter count, not a different conclusion.

**How to write this honestly.** This is real, first-of-its-kind progress on the base-rate
dominance problem central to this paper's caries story — not a claim that caries scoring is
solved. DENTEX is a tie, and the pre-registration's own outcome table anticipated a cleaner
"wins in-domain, fails to transfer" bin that this result does not fall into; say so rather than
rounding a tie up to a win. Ningxia was the deciding cohort and was scored exactly once, frozen,
no tuning — consistent with every other Ningxia number in this document. The gate's diagnosis in
§8.24 (position as a partial confound) is not shown to be *wrong* by this result, only shown to
be a property specific to the per-crop-classification framing, not to caries detection in general.

Source: `RESULTS_LOG.md` 2026-09-04f, 2026-09-04g, 2026-09-04h (labels reassigned on merging the
parallel Mac-side session, which used `2026-09-04`/`04b`/`04c` first for its own entries);
`outputs/lever_B_lesion_caries_path/
PRE_REGISTRATION.md` (frozen, commit `ef3f453`); `outputs/lever_b_eval/acceptance_rule_B-pooled.json`;
`models/16_lever_b_pooled/run_summary.txt`; `docs/session-memory/2026-09-04a-lever-b-build-and-both-arms.md`.

### 8.28 The bone-loss branch, audited — a crop-level validation split, and a label that is not bone loss

Found 10 Oct 2026 by a review council and recomputed by its chair; `RESULTS_LOG` 2026-10-10. No
model was run. These are two facts about Stage 4a that §6.3, §8.13, §8.18 and the manuscript get
wrong.

**1. The validation set shares every radiograph with the training set.** §6.3 describes an
image-level split. The run that produced the shipped checkpoint did not use one: the training
notebook found no `val/` on disk and fell back to a label-stratified, crop-level
`train_test_split(test_size=0.2)`. Its saved output says so in one line.

| | |
|---|---|
| validation radiographs that also supply training crops | **143 of 143** |
| validation crops whose tooth is also in training | 543 of 1,558 (34.9%) |
| validation positives whose tooth is a training positive's tooth | **46 of 59** |
| distinct diseased teeth in the whole build | 153 (145 in training, 54 in validation) |

The shared teeth are not duplicate files. They are the clean crop and the ±15%-jittered crop of
one tooth, on opposite sides of the split. So 0.9233, and the 83.05% / 99.53% beside it, is
validation on the training radiographs. It reproduces (§9, 7 Sep) and it is not a held-out
estimate. How far it exceeds one is unmeasured.

**2. The positive class is "a tooth crop that overlaps a Tufts expert abnormality mask".** That
is the rule in the construction notebook (`overlap > 0.01`), and §6.2 treats the overlap as a
proxy for bone lost. The Tufts expert masks mark *abnormalities* of any kind. Every diseased crop
comes from 41 radiographs, and their expert descriptions are apical rarefying osteitis and apical
radiolucencies (26 mention "apical"), cysts (9), sclerosis and dense bone islands (9). Four
contain a periodontal or alveolar word, and each is an apical finding ("apical periodontitis",
"widening of apical PDL"). Across all 1,000 Tufts descriptions, three describe periodontal bone
loss or periodontal disease outright — **and none of those three radiographs supplies a diseased
crop.** This is a keyword reading of free text, per radiograph. It is not a clinician's reading,
and it was not done per mask.

**What this does to §8.13.** §8.13 reads 0.923 in-domain against 2.4% external sensitivity as a
branch that "does not generalise", and places the failure inside the Stage-4a classifier. Both
halves of that comparison change. The in-domain half is inflated by an amount nobody has
measured. The external half scores the model against Ningxia's periodontitis masks — a continuous
band along the bone ridge — which is a target it was never trained on. A label mismatch predicts
near-zero sensitivity with no domain shift at all. The detector-swap experiment still shows what
it showed: the cause is not upstream. It no longer shows that the cause is shift.

**Statements that are now false and must not reach a reviewer:**

- "Splits are image-level throughout" — `main.tex` Table I caption and §Data; §6.3 here
  (corrected in place); the root `README.md` (corrected 10 Oct).
- Tufts "700/150/150 frozen" given as the split for "Detection, bone loss" — it is the
  detector's split only.
- "The bone-loss branch under domain shift" (the bone-loss figure caption), "did not transfer"
  (Conclusion), and the abstract's 0.923-against-1.4–5.6% sentence, as written.

**How to write this honestly.** There are two defensible options, and the choice belongs to the
authors and the mentor, because the capstone's title names periodontal disease. *Cut:* remove the
branch from the manuscript and keep one Limitations sentence saying that a second branch exists,
was trained on Tufts abnormality masks, and was not validated as a periodontal classifier.
*Keep:* describe it as what it is — an abnormality-proximity classifier, validated at crop
level, whose external result is a label mismatch — and, only if kept, measure it once on Tufts
radiographs that supplied no training crop. The masks, the boxes and all 1,000 original
radiographs are on the macOS clone; that run needs its own pre-registration. What is not
defensible is the current text. The same crops feed Stage 4b, whose split was not audited.

*Update, 11 Oct 2026.* Stage 4b's split was audited that evening and **is** image-level: 32
training radiographs, 9 validation, none shared. Its label source is the same abnormality masks.
The pipeline's own output was corrected the same day (`RESULTS_LOG` 2026-10-11b): from report
schema 1.2 every report and the demo app describe the Stage-4 field as an abnormality-proximity
flag, not a periodontal finding, and the overlay prints `ABN` where it printed `BL`.

Source: `RESULTS_LOG.md` 2026-10-10; `data/tufts/resampled_dataset/metadata/`;
`notebooks/bone_loss/{02_bone_loss_dataset_construction,03_bone_loss_model_training}.ipynb`;
`docs/session-memory/2026-10-10-state-review-council.md`.

### 8.29 Three intervals — what the caries tables can and cannot say

Measured 11 Oct 2026 under a pre-registration frozen before any code
(`outputs/caries_intervals/PRE_REGISTRATION.md`, `RESULTS_LOG` 2026-10-11). Nothing was trained
or tuned. Each measurement first reproduced a published number exactly.

**1. The constant and the gate pipeline are not separable on FDI-set F1.** The gap the abstract
leads with, 0.320 against 0.294, is **+2.61 pp [−0.64, +5.99]**. The constant does separate from
both vision–language models (+7.32 pp [+3.42, +11.23] and +17.04 pp [+12.66, +21.22]); the gate
pipeline does not separate from the larger one (+4.71 pp [−0.22, +9.44]). "Outscored" has to go.
The argument does not: a system that cannot be told apart from an image-blind constant has not
shown that it reads the image, and that is a sharper sentence than the one it replaces.

**2. Lever B's external result is uneven by hospital.**

| hospital | images | detector | constant | detector − constant |
|---|---|---|---|---|
| test1 | 134 | 0.462 | 0.446 | +1.58 pp [−4.43, +7.74] — includes 0 |
| test2 | 110 | 0.576 | 0.407 | +16.91 pp [+10.48, +23.35] |
| test3 | 40 | 0.494 | 0.377 | +11.73 pp [+1.29, +21.58] |
| test4 | 53 | 0.430 | 0.323 | +10.75 pp [+0.60, +20.18] |
| pooled | 337 | 0.500 | 0.399 | +10.17 pp [+6.27, +14.02] |

The detector is separated from the constant at test2, test3 and test4 and not at test1 — the
hospital where the constant is strongest and the old gate was weakest. This was estimation, not
a test: the point estimates had been seen, so no bar was set and the 4 Sep verdict is not
reopened. The manuscript asks others to report per institution; it now can.

**3. The adopted detector beats the constant on the headline metric.** Table I has only ever
scored the gate. Run once over the same 164 images, the lesion-detector pipeline scores
**P 0.353 / R 0.403 / F1 0.376** against the constant's 0.218 / 0.600 / 0.320:
**+5.64 pp [+1.74, +9.47]**. Against a same-day gate control it is +7.59 pp [+4.47, +10.70]. It
flags 544 teeth where the constant names 1,312.

**How to write this honestly.**

- DENTEX is *development* data for the detector — a corpus it trained on, scored on images held
  out from it. The hold-out was re-checked: no scored image is byte-identical to any of the 705
  source images, and on a perceptual hash each one's nearest training image is no closer than
  training images are to each other. Say "development", not "external".
- It is one training run, on one machine. The gate control scored 0.300 here against the
  published 0.294 from the Windows machine, with identical predictions from the August and the
  current code — a cross-machine difference of 0.0066 that Table I should either state or
  remove by restating both rows from one machine.
- It does not overturn the tie on lesion agreement on these same images (0.455 against 0.489).
  That metric is recall-shaped; F1 pays for precision, and precision is where the detector
  wins. Both belong in the paper, side by side.
- **The thesis shifts, and that is the authors' call, not an engineering one.** The paper's
  claim was that a tooth-level score cannot show a system is reading the radiograph, because a
  constant matches the system. That is still true of the gate and of both language models. It
  is no longer true of the system the pipeline ships. The floor did its job: it is what the
  detector's result is measured against.

Source: `outputs/caries_intervals/caries_intervals.json`; `scripts/eval/caries_intervals.py`;
`docs/session-memory/2026-10-11b-caries-interval-measurements.md`.

### 8.30 The tooth detector was changed against two pre-registered verdicts — what the pipeline measures now

On 11 Oct 2026 the Stage-1 default became the Lever A multi-corpus detector (arm3c: Tufts +
DENTEX + Kaggle "dual"), replacing the Tufts-only seg detector. **Lever 1 (1 Sep) and Lever A
(3 Sep) had each been recorded as an ablation, because each failed a pre-registered Tufts
box-mAP guard, and both rules say a failed guard leaves the default alone. Neither bar was moved
and neither guard is claimed met.** The change is a later human decision, recorded as that
(`RESULTS_LOG` 2026-10-11f), and the pipeline was then re-measured under a pre-registration
frozen before any run (`outputs/stage1_switch/PRE_REGISTRATION.md`, `RESULTS_LOG` 2026-10-11g).
Both detectors were run on one machine; differences are paired over images.

**Numbering.**

| Cohort | Previous detector | arm3c | Difference |
|---|---|---|---|
| Tufts test, 3,760 teeth, end to end | 64.8% | 63.5% | −1.30 pp [−4.64, +2.26] — not separable |
| — recall | 82.4% | 89.3% | +6.89 pp [+4.94, +9.00] |
| — accuracy on detected teeth | 78.6% | 71.1% | −7.52 pp [−10.79, −4.16] |
| DENTEX, 936 teeth, end to end | 58.4% (cross-domain) | 92.8% (**in-domain**) | +34.40 pp [+30.29, +38.54] |

**Caries.** Lesion agreement of the default caries path (the lesion detector) rose on all three
cohorts — DENTEX 0.457 → 0.595, CariesXrays 0.682 → 0.757, Ningxia 0.500 → 0.684 — and the
image-blind constant rose by about as much, because in that metric the constant is placed with
the pipeline's own boxes and codes. FDI-set F1, where the constant is fixed at 0.320: the
default pipeline 0.376 → **0.498**, **+17.80 pp [+13.48, +22.02]** above the constant.

**The paper's development-data headline depends on the front end** (`RESULTS_LOG`
2026-10-11i; a comparison added after the matrix, from the same runs, not pre-registered).
`main.tex` says the image-blind constant "scored highest" and "outscored a six-stage pipeline …
under two unrelated metrics". Gate pipeline minus constant:

| | Previous front end | Current front end |
|---|---|---|
| DENTEX, FDI-set F1 | −2.61 pp [−5.99, +0.64], not separable (published arm, other machine; −1.95 pp on this one) | **+4.27 pp [+1.58, +7.05]** |
| DENTEX, lesion agreement | −4.18 pp [−8.42, −0.21] | **+17.12 pp [+12.15, +21.89]** |
| CariesXrays, lesion agreement | −24.44 pp [−26.56, −22.36] | −22.42 pp [−24.62, −20.18] |
| Ningxia pooled, lesion agreement | +0.79 pp [−3.27, +4.71] | +0.89 pp [−3.86, +5.57] |
| Ningxia test1 / test2 | −15.51 / +10.89 pp | −18.99 / +12.32 pp |

On DENTEX the order reverses: with the multi-corpus detector the pipeline is above the constant
on both metrics, and on F1 the ladder reads lesion-detector pipeline 0.498, gate pipeline 0.362,
constant 0.320, then the two language models. On the external cohorts nothing moves — the gate
and the constant are still not separated on Ningxia, with the same swing between hospitals, and
the constant still leads the gate by 22 pp on CariesXrays. So a manuscript on the new front end
cannot open with "the constant scored highest". It can say something narrower and arguably
stronger: *a pipeline that clears the image-blind floor on its development corpus still cannot
be told from it at external hospitals — and clearing it at home took an in-domain detector, not
a better caries model.* A manuscript on the previous front end keeps its headline, on an
interval that excludes zero by one lesion on this machine, and must say the released default
differs. Either way the claim is the authors' to choose.

**How to write this honestly.**

- **Say that it was a decision against the registered rule.** The manuscript's credibility
  rests on reporting pre-registered outcomes as they fell; this one fell "ablation" twice and
  the default was changed anyway. One sentence stating that, with what was given up (Tufts test
  box mAP@0.5 0.810 → 0.585; instance masks), is the price of using the result.
- **92.8% is in-domain.** The 164 images are held out from the detector's training data, but
  DENTEX is one of its training corpora. The previous 58% was a Tufts-only detector on DENTEX —
  a cross-domain figure, and the two must never share a row unlabelled. **With arm3c the
  pipeline has no cross-domain numbering figure**: both cohorts with tooth labels are in its
  training distribution. That is a limitation the previous front end did not have.
- **Tufts is "not separable", not "no cost".** The interval reaches −4.64 pp, and under it the
  detector finds more teeth and numbers them worse. Teeth matched to a box but given no code
  rose from 26 to 65: the one-to-one assignment stops at 32 boxes and cannot reject a surplus
  one.
- **Most of the caries rise is the front end, not the caries model.** The constant moved with
  it on every cohort (+13.99, +4.12, +19.25 pp). What the lesion detector adds over the constant
  is about what it added before: not separated on DENTEX (−3.55 pp [−10.11, +2.64]), separated
  on CariesXrays (+15.38 pp) and Ningxia (+9.28 pp [+4.72, +13.73]); per hospital it is again
  not separated at test1.
- **One result got worse and must be printed.** On DENTEX lesion agreement under arm3c the
  retired gate scores 0.802 against the lesion detector's 0.595 (−20.67 pp [−26.39, −15.06]);
  under the previous front end they were tied. The gate gets there by flagging 1,439 teeth to
  the detector's 603, and on FDI-set F1, which charges for that, the order reverses (0.362
  against 0.498). Both tables belong side by side, with the flagged counts.
- **Lever B was adopted under the previous front end.** Its rule was not re-run and is not
  claimed for this one. If the paper reports the new front end, the adoption evidence is
  labelled with the front end it was scored on.
- **Ningxia is no longer blind to the choice of detector.** The default was chosen after this
  detector's gate-path Ningxia result was known, and the cohort was used once more as a veto
  (the one stop rule: lesion-detector agreement must not fall by more than 2 pp; it rose
  +10.40 pp [+8.71, +12.09]). Nothing was fitted on it.
- **Two open items a reviewer can raise:** the Kaggle "dual-labeled" set, part of arm3c's
  training data, states no licence; and the Tufts box-mAP guard figures were not re-measured.

**Measured afterwards for the rebuild** (`RESULTS_LOG` 2026-10-11j). Numbering errors under
the current detector are still mostly benign — 51 of 63 wrong codes off by one, 6 of 932
detected teeth in a wrong quadrant. Declining the least-confident quarter still raises numbering
accuracy, 0.932 → 0.980 (+4.76 pp [+3.29, +6.54]), and the registered 0.30 threshold now keeps
96.1% of detected teeth. Stage 4 fires on 0.75% of DENTEX teeth. **The Tufts cost, like for
like, is −13.6 pp of box mAP** (0.723 for a Tufts-only control → 0.587, one label frame, one
machine); the 0.810 → 0.585 used above compares two protocols and should not be quoted.

Source: `outputs/stage1_switch/stage1_switch_results.json`;
`scripts/eval/stage1_switch_intervals.py`;
`docs/session-memory/2026-10-11g-detector-switch-matrix-and-flip.md`.

---

### 8.31 What kind of evidence each stage has — and one cohort that was mis-described

*12 Oct 2026, second council and an ML-engineering review. `RESULTS_LOG` 2026-10-12. No new
number.*

**The 1,200 CariesXrays images are the lesion detector's validation split.** The detector was
not trained on them, but its training stopped early on them and its `best.pt` was chosen on
them (`scripts/yolo/train_lever_b_pooled_detector.py`; `models/16_lever_b_pooled/run_summary.txt`
has said so since 4 Sep). The manuscript rebuilt on 11 Oct says the detector "was kept away
from" them. For the gate and for the constant, which never saw them, the cohort is external
and the −22.42 pp row stands. For the lesion detector the 0.757 is a validation-split figure.
That leaves **Ningxia as the only cohort the lesion detector neither trained nor selected on**,
and Ningxia was one of the cohorts that decided its adoption.

| Stage | Evidence | A claim it supports |
|---|---|---|
| 1 | Held out, in-domain; default chosen against two registered verdicts | It is the front end |
| 2 | In-domain on DENTEX, 63.5% on Tufts test, nothing off-corpus | A caveated accuracy |
| 3a lesion detector | In-domain (DENTEX), validation (CariesXrays), adoption-conditioned external (Ningxia) | The direction of the lead over the constant |
| 3a gate | Held-out crops; external on two cohorts; unchanged by the detector swap | Not separable from the constant externally |
| 3b | 133 validation crops | None |
| 4a, 4b | Not held out; label is not bone loss | None |

**No held-out test of Stage 3b can be built from data on hand.** The 164 leak-free DENTEX
images carry a caries class and no deep-caries class.

**What no further implementation removes:** no caries cohort untouched by a decision and none
with healthy controls; one training run per model; a default adopted with outcomes in view;
no clinician reference.

---

## 9. What's not yet written — checklist

For whoever drafts the actual paper. Tick items off here as they land.

**Blocking — must be done before submission**

- [ ] **Decide whether the bone-loss branch stays in the manuscript, then remove the three false
      statements about it** (§8.28, found 10 Oct 2026): "splits are image-level throughout";
      Tufts 700/150/150 given as the bone-loss split; and "domain shift" / "did not transfer" as
      the reading of the external periodontitis result. Authors and mentor.
- [ ] **Add the mandatory statements — none is in `main.tex`** (checked 10 Oct 2026): authors and
      affiliations, ethics, data availability with licences, code availability, funding, conflict
      of interest, author contributions, and acknowledgments including the AI-use disclosure IEEE
      requires.
- [x] **Decide which front end the manuscript reports, and make every table say so** (§8.30,
      11 Oct 2026). **Decided 11 Oct: the current one. `main.tex` was rebuilt the same day**
      (`RESULTS_LOG` 2026-10-11k): every table and the headline re-stated, the override of the
      registered guard written into §Data, 191 numbers asserted, 15 pages under tectonic. Left:
      a pdfLaTeX build and `paper.txt` on the Windows machine. The original item read: **This decides whether the abstract's first result is true of the system
      described:** on DENTEX the constant no longer leads the pipeline under the new front end
      (`RESULTS_LOG` 2026-10-11i). The table-by-table list is in
      `docs/paper/SUBMISSION_TODO.md`. `main.tex` describes the Tufts-only seg detector throughout; the pipeline
      default is now the multi-corpus detector. Either the paper is rebuilt on the new front end
      — every pipeline table re-stated from `outputs/stage1_switch/`, the decision against the
      registered rule stated, 92.8% labelled in-domain, the parameter total 95.34 M — or it
      reports the previous front end and says the released default differs. Authors and mentor;
      not an engineering call. Until one is done the manuscript and the code disagree.
- [ ] **Bring three statements in `main.tex` into line with their intervals** (§8.29, measured
      11 Oct 2026): "the constant scored highest" → not separable from the gate pipeline on F1;
      "it replicates on the one cohort that is genuinely external" → a pooled statement, printed
      beside the per-hospital table; and Table I gains the adopted detector's row
      (0.353 / 0.403 / 0.376), labelled as development data. Decide whether Table I restates
      both pipeline rows from one machine.
- [x] **Fold §8.27 (Lever B; §8.26 at the time this box was written) into `main.tex`.
      Done 4 Sep 2026** (RESULTS_LOG 2026-09-04i). Table I now
      reports both Stage-3a paths under one counting rule; §System gained
      `\subsection{Stage 3a: two formulations of the same clinical question}` (`sec:lesiondet`);
      §Results gained `\subsection{Changing the task, not the architecture}` (`sec:leverb`) with
      the three-cohort table, the not-a-volume-effect check and the B-single transfer collapse;
      §Discussion's Main finding and "Why the floor is high" were reframed — the paper's claim
      that *architectural* work cannot raise the ceiling is **confirmed** by Lever B, which moved
      the task instead, so the result is additive rather than contradictory. The abstract gained
      one factual sentence. `verify_paper_numbers.py` grew from 90 to 117 asserted claims,
      covering every Lever B figure and all four parameter totals.
      *Not done, deliberately, and left to the author:* the title and the paper's central thesis
      are unchanged, and the abstract's closing "four things a constant cannot do" is still a
      list of four — localising the finding is arguably a fifth, but adding it changes the
      paper's prescription, which is not a call to make while reconciling numbers.
- [x] **Scope the calibration and selective-prediction results to the gate variant.
      Done 4 Sep 2026** (RESULTS_LOG 2026-09-04j). §"What the constant cannot do" reported ECE
      0.136→0.043 and +14.25 pp caries abstention, both measured on the per-crop gate that
      §8.27 demoted to a variant — so the paper was, for caries, demonstrating two of its own
      four proposed axes on a component that no longer ships. Both figure captions now name the
      gate, the subsection opens with the scoping and its consequence, the §Discussion axis list
      distinguishes numbering from caries, and **a new first Limitations item** states plainly
      that the adopted detector has no calibrator and no coverage–accuracy curve, that the
      pre-registered 0.30 threshold was located on the gate's curve and does not transfer to a
      detection score, and that closing this needs its own pre-registration. Numbering is
      unaffected and demonstrates all four axes.
- [x] **Fold the Lever 2 benchmark row (§8.26) into Related Work. Done 4 Sep 2026**
      (RESULTS_LOG 2026-09-04j) — `sec:benchmarkrow` + `tab:fpcl`. Its stated precondition,
      re-verifying the FPCL table against the AAAI PDF, was done first and **caught two errors**
      in the 2 Sep transcription (a DINO row that does not exist in their table, and "~8 AP"
      which should be ~6 once the omitted Conditional-DETR row is restored). See §8.26.
- [x] Re-run the caries notebook and **save** the Phase 1 gate classification report
      (`caries` vs `no_caries`), plus the `Counter` cell confirming DENTEX class counts.
      **Done 25 Aug 2026** — `scripts/dentex/train_caries_cascade.py` replaced the notebook and
      writes the report to disk; it is in `models/09_caries_gate_v3/run_summary.txt` (held-out
      test, 863 teeth, accuracy 0.80, macro-F1 0.69). RESULTS_LOG 2026-08-25a/b.
      *(Ticked 27 Aug — the work landed on the 25th and this box was never updated.)*
- [x] Carve a held-out **test** split for caries and re-report on it. **CLOSED 25 Aug 2026 —
      both halves.** The split was rebuilt 21 Aug from the raw 705-image source as an
      independent image-level 70/15/15 split (`build_dentex_split_from_raw.py`,
      `data/dentex/splits_v2.json`, train 495 / val 103 / test 107, verified disjoint and
      reproducible). The **re-run and re-report half landed 25 Aug**: both T0.1 arms ran on
      `crops_v3_phase1` with checkpoint selection on **val macro-F1** (T0.3) and a cosine
      schedule (T0.4), and the **test split is reported separately, touched once, after
      checkpoint selection** (T0.2) — arm A test macro-F1 0.7212, arm B 0.6948; the shipped
      `caries-gate-resnet18-v3.0` is arm B. RESULTS_LOG 2026-08-25b.
      *(Ticked 27 Aug. `PUBLICATION_TODO.md`'s status block still called this open because it is
      dated 21 Aug — four days before the work landed — and reading it as current nearly cost a
      GPU session.)*
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
- [x] Build Stages 5–6 (integration) and report at least one end-to-end example, or state
      unambiguously in the abstract that the system is evaluated stage-wise only.
      **Done 24 Aug 2026** — `scripts/run_inference.py` runs all six stages, image → per-tooth
      JSON + overlay (R4, paper claim C3); `app.py` + `Dockerfile` wrap it unchanged for a
      browser demo (25 Aug). RESULTS_LOG 2026-08-24f, 2026-08-25f. *(This item stayed unticked
      in writing for three days after it landed — noted because it is this repo's recurring
      failure mode, not because the work was late.)*
- [x] Re-measure C2 (Ningxia external validation) against the adopted detector. **Done 27 Aug
      2026** — §8.12a. Caries +7.7 pts pooled across four hospitals; bone loss unchanged. Control
      on the old detector run first and reproduces 25 Aug.
- [x] Decide the bone-loss domain-shift disposition. **Done 27 Aug 2026 — reported as a measured
      limitation (§8.13), not fixed.** The combined-training lever that worked for Stage 2 does
      not transfer (DENTEX has no bone-loss labels), and the causal hypothesis that it shared a
      root cause with the detector was falsified by measurement. **Write §8.13 into the paper as a
      finding, not an apology.**
- [x] Re-measure §8.11 lesion localisation on the adopted detector, so internal and external are
      comparable. **Done 27 Aug 2026** — 42.0% → 44.3%; internal/external gap 8.9 → 3.5 pp.
      **No pipeline number remains on the superseded detector.**
- [x] Run and report the pre-registered YOLOv11l-seg retrain (R1). **Done 27 Aug 2026** — box
      bar passed (0.8100 ≥ 0.75), **mask bar missed** (0.6383 < 0.65), adopted as the Stage-1
      default by explicit human decision for the box gain; Stage 2 re-measured end-to-end
      46.3% → 58.3%. §7.1 and §8.10 above. **Write both halves — the missed bar is part of
      the result, and the adoption was a judgement call, not a pass.**

**Content still to write**

- [ ] Write up §8.9 (66 annotated teeth missing from the detection ground truth, from
      corrupt `bounding box` fields in the source data) as a short data-quality paragraph —
      it is both an honest limitation of our Stage-1 numbers and a reusable finding about
      the public dataset.
- [x] Decide whether the Tufts end-to-end FDI number (64.8% e2e / 78.6% of detected) needs
      strengthening before submission, or ships as an honestly-decomposed detection-bound
      number. **Settled 6 Sep 2026: it ships as it stands.** Option B falsified the
      positional-feature hypothesis (+0.1 pp) and Lever C — pre-registered, run, and reported
      as a null (+0.29 pp against a +2.0 pp bar, `RESULTS_LOG` 2026-09-06b) — excluded the
      assignment. Nothing in `main.tex` changes; it never claimed the Tufts end-to-end number. Improvement options A–F are councilled in
      `docs/session-memory/2026-09-05b-tufts-fdi-improvement-council.md` and summarised at the
      end of §8.16. Recommended first step is a zero-GPU positional-feature diagnostic, then an
      anatomical sequence post-processor as a pre-registered ablation (data / architecture
      levers are post-submission). Whichever way it goes, write §8.16's Tufts paragraph
      leading with **of-detected 78.6%**, not the end-to-end figure.
- [x] Related Work section — **comparison table DONE 27 Aug 2026** (§2.1): 117 reviewed papers,
      49 task-relevant after de-duplication, head-to-head table on Tufts/DENTEX with our result
      beside each, plus the validation-landscape count (**only 2 of 49 validate externally**) that
      evidences this project's central differentiator. Machine-readable extract at
      `outputs/related_work_extract.csv`. **Still to write: the narrative prose**, reusable from
      the archived `02_literature.tex`.
- [x] Formal dataset ethics + licensing statement for Tufts and DENTEX (usage terms,
      de-identification, IRB status). **Done 27 Aug 2026** — §8.19, covering all four corpora with
      a pre-submission checklist. **It records two UNRESOLVED compliance items** (the
      link-accessible Tufts Drive folder; SDH's `index.csv` sharing a folder with `images/`) and
      **two unverified licences** (DENTEX, Ningxia — deliberately not guessed at). The statement
      cannot be finalised until those four are closed.
- [ ] Precise definition of the overlap-ratio severity thresholds as a *proxy* measure,
      with an argument for why 0.05 / 0.15 were chosen (currently undocumented — were they
      tuned or picked by eye?).
- [ ] Ablation: overlap threshold 0.005 / 0.01 / 0.02 on bone-loss binary F1.
- [ ] Ablation: with vs without ±15% bbox jitter, evaluated on **real detector crops**.
- [ ] Ablation: symmetric vs asymmetric (1.5×/2.0×) crop expansion.
- [ ] Runtime/efficiency table for the full pipeline (per-OPG latency, per stage).
- [x] **Failure taxonomy for Stage 2** (`MASTER_PLAN` W7's "bucketed by confounder") — **Done
      27 Aug 2026**, §8.16: 58.3% shown to be detection-bound (82.6% correct on detected teeth),
      77.4% of numbering errors are benign off-by-one, only 2.4% of detected teeth suffer a
      category error, and the detector swap cut `wrong_arch` by 75%.
- [x] **Caries failure panel** — **Done 27 Aug 2026**, §8.17: errors bucketed by negative
      subtype, showing the gate over-calls healthy teeth (19.2%) at the same rate as impacted
      ones (19.0%), so it is not confusing pathology-for-pathology; plus a visual panel of the
      highest-confidence false positives and most-missed false negatives.
- [ ] Failure-case figure panel: the 10 false negatives and 7 false positives from the
      bone-loss confusion matrix, with Grad-CAM. **Blocked** on the bone-loss crop rebuild
      (RESULTS_LOG 2026-08-27u). A caries failure panel is buildable from `crops_v3_phase1`.
- [~] **UPDATED 4 Sep 2026 — 2 of 3 remaining gaps closed** (`RESULTS_LOG` 2026-09-04k/04l).
      Original: cluster-bootstrap 95% CIs over images for Stage-2 (recall, FDI exact ×2), DENTEX
      lesion agreement, and Ningxia caries per hospital, plus paired CIs on the detector-swap
      deltas — done 27 Aug (§8.14). Of the three gaps that remained after that pass:
      - [x] **Ningxia periodontitis** — `ningxia_external.py` was discarding the per-image
        affected-tooth counts it already computed; now writes them, and `bootstrap_ci.py`
        bootstraps them. Pooled sensitivity 2.4% [95% CI 2.0, 2.9], n=736 images; per-site CIs
        also computed. `main.tex` updated, `verify_paper_numbers.py` asserts it.
      - [x] **Detection mAP** (Tufts Stage-1, frozen `split_v1` test) — reported instead as box
        detection recall at the deployed confidence (conf=0.25): **69.1% [95% CI 65.5, 72.6]**,
        n=150 images (`scripts/eval/tufts_detector_ap_bootstrap.py`, new). This is a *different*,
        disclosed statistic, not a CI on the published 0.8100 AP figure — see that script's
        docstring for why: an independent from-scratch AP reimplementation, built specifically
        to bootstrap the exact published number, hit two real bugs (a ground-truth
        coordinate-frame mismatch, then an NMS setting) and even after both fixes would not
        converge closely enough to trust (0.593 → 0.701 → 0.672, moving *away* from 0.810 on the
        second, config-correct fix) — the AP attempt is kept in the output artefact as a labelled
        diagnostic, never asserted or quoted as a number. This same measurement closed the
        `split_v1` 590/591 leak decision in §1/§4 of `transfer.md`: recall excluding the leaked
        image is 69.0%, a $-0.15$-point shift — within noise, so "document and move on."
      - [ ] **Both bone-loss ResNet18 classifiers** — genuinely blocked, not merely undone. The
        only candidate per-item dataset on this machine
        (`outputs/bone_loss_eval/bone_loss_val_nonjittered.json`) is explicitly flagged by its
        own creator `"DIVERGENT -- suspect crop geometry, do not use these crops"` and scores a
        very different 0.537 macro-F1 on a disqualified 785-crop subset — using it would put a
        wrong number behind a real-looking interval. The original un-rotated Tufts radiographs
        needed to redo this properly were searched for directly (every drive letter, OneDrive)
        and confirmed absent from this machine, not merely assumed absent.
- [x] Figures for Stages 3/4: training curves and confusion matrices. **Done 27 Aug 2026** —
      **regenerated** from committed artifacts rather than recovered from the archive, so both
      figure and numbers are reproducible from the repo (§8.18):
      `stage4a_training_curves.png`, `stage34_confusion_matrices.png`.
      **Still missing, recorded not faked:** caries training curves (no per-epoch history was
      ever saved) and the Stage-4b severity confusion matrix (per-class F1 only, 52 crops).

**Nice to have**

- [x] **C1 — VLM baseline. DONE 27 Aug 2026** (§8.20): Qwen2.5-VL-7B zero-shot on the 164
      leak-free images, F1 0.143 vs our 0.294 — and **below a constant guess (0.204)** that
      ignores the image. Control: blank and noise images produce the same confident answer.
      Cost ₹37.93.
- [ ] Reader study or comparison against a junior clinician baseline (the motivating claim
      of the paper is currently unquantified).
- [x] Calibration analysis (reliability diagram) **for the caries gate** — **Done 27 Aug 2026**,
      §8.15: ECE 0.136, MCE 0.596, Brier 0.137, AP 0.550 [0.445, 0.660] against 0.147 chance;
      systematically overconfident at every confidence level.
- [ ] Calibration analysis (reliability diagram) for the **bone-loss** classifier. **Still open,
      and the blocker is now exact (27 Aug, RESULTS_LOG 2026-08-27u):** the crops were built from
      **`Radiographs/Radiographs/` — the ORIGINAL un-rotated Tufts radiographs** (confirmed by
      reading `02_bone_loss_dataset_construction.ipynb`), which are **not on this machine**; only
      the 90°-turned copies are. A rebuild from those reaches sensitivity 0.40 against a
      documented 0.83 and was **rejected by its own geometry check**. Additionally **49.6% of the
      val crops carry unsaved jitter offsets and are irreproducible by anyone**, so the reported
      0.9233 can never be recomputed — any future bone-loss number is on a 785-crop subset and
      must say so.

      > **CORRECTED 7 Sep 2026 — the paragraph above is wrong about availability**
      > (`RESULTS_LOG` 2026-09-07, 2026-09-07b). The reasoning is sound about *regeneration* and
      > was read as being about *access*: the original crops, **including all 773 jittered ones**,
      > were sitting in the project Drive the whole time, and nobody looked. Recovered, they
      > reproduce the reported figure **exactly on the complete diseased class — TP 49 / FN 10,
      > sensitivity 0.8305** (clean 29/35, jittered 20/24). The 27 Aug rebuild's 0.40 was a
      > **defect in the rebuild**, not evidence against the number: it reads `teeth_bbox.json` as
      > `[x1,y1,x2,y2]` portrait-then-rotate while the source notebook reads `[y1,x1,y2,x2]`
      > landscape — a horizontal mirror, so it cut a different region per tooth. Using the
      > notebook's convention, 187/187 crops regenerate **bit-for-bit**.
      > **Still outstanding:** the full macro-F1 0.9233 needs all 1,499 negatives (934 recovered;
      > Drive throttles the rest), so the whole-set figure is verified for sensitivity only so far.
      > What survives unchanged is the *selection-bias* limitation — best of 32 epochs on 59
      > positives — which is a separate point and is not touched by any of this.

      > **SUPERSEDED 10 Oct 2026 — do not run this on the current validation set** (§8.28,
      > `RESULTS_LOG` 2026-10-10). That set shares all 143 of its radiographs with training, so a
      > reliability diagram, a PR sweep or an interval computed on it would describe a leaked
      > split. The remaining 565-crop pull is not worth finishing for the same reason. If the
      > branch stays in the paper, calibrate on radiographs that supplied no training crop.
- [x] Threshold sweep **for the caries gate**, reported as a PR curve — **Done 27 Aug 2026**,
      §8.15. argmax/0.50 confirmed near F1-optimal; precision 0.40 → 0.69 purchasable at
      recall 0.74 → 0.35.
- [ ] Threshold sweep for the bone-loss decision boundary, reported as a PR curve rather
      than a single operating point.

---

## 10. The manuscript — written 28 Aug 2026, and the five things this document got wrong

**`paper/main.tex` is now a complete manuscript** that compiles clean (0 errors, 0 overfull
boxes, 0 undefined references, 12 pages) with all five figures. The full audit that preceded
it — research story, 20-item problem audit, numerical audit, storyboard, citation audit and
five title options — is `docs/paper/REBUILD_AUDIT.md`. History: `RESULTS_LOG.md` 2026-08-28.
Narrative: `docs/session-memory/2026-08-28-manuscript-rebuild.md`.

**The title is now "What a Tooth-Level Score Cannot Tell You: Constant Baselines, External
Validation and Domain Shift in Automated Panoramic Dental Screening."** The previous title
anchored on 44.3 %, which is the *pipeline's own* lesion-localisation agreement (212/479) —
one row of one table, and not the finding. A title asserting the constant wins would also
have overclaimed, since the result does not replicate externally.

**Five defects in the draft, four of which originated in the draft and one here.** They are
listed in full in `RESULTS_LOG.md` 2026-08-28; the ones that touch *this* document:

1. **The "~25 M parameters" figure was wrong and it came from here.** §8.20 and §8.22 both
   carried it. It is the *superseded bbox detector alone*. The pipeline is **83.56 M across
   six models, 61.19 M on the caries path** — counted from the checkpoints, per-stage table
   now in `model_metrics.md`. Corrected in this file, `model_metrics.md` and the three
   `docs/paper/` drafts; `RESULTS_LOG.md` records rather than edits it.
2. The draft named two models that do not exist ("Qwen2.5-VL-33B", "-8B"). **This document
   was right** — §8.22 uses the released names. Keep using them.
3. The draft claimed *both* VLMs answer a blank grey image with a dental answer. **This
   document was right** — §8.22 records that the 32 B model returns `NONE` to the blank and
   only fails on noise. Keep that distinction; the precise version is the stronger result,
   because the 32 B model's answer to *noise* is exactly the eight-molar constant.
4. The draft said isotonic calibration leaves every verdict unchanged. **This document was
   right** — §8.15 records 155 of 863 verdicts flipping and AP 0.550 → 0.500, and explains
   that the invariance is our *deployment choice*, not a property of the method.
5. "No paper in the survey reports an image-blind baseline" was written as a counted census.
   **It is not counted anywhere** — `related_work_extract.csv` has a validation-design field,
   not a baseline field. The **2-of-49 external count is verified** (recomputed 28 Aug). State
   the baseline claim as an observation.

**Newly established during the audit, and worth keeping:**

- **477 vs 479 is not an error.** 479 çürük *polygons* over the 164 scored images fall on
  **477 distinct teeth**; exactly two teeth carry two lesions each (`test_101` tooth 36,
  `test_25` tooth 46). Different units. Say so wherever both appear.
- **The constant reproduces exactly** — the greedy fit re-run from scratch on the 78 fitting
  images returns `{16,17,26,27,36,37,46,47}`. It scores **F1 0.392 on its fitting set and
  0.320 on the scored set**, i.e. it transfers *downwards*. That is the answer to "the
  constant was fitted, so it is not uninformed".
- **The 86 → 78 arithmetic:** 250 DENTEX `disease/` images; 86 excluded by MD5 byte-identity
  (85 via the numbering head, 1 via the detector); 164 scored; of the 86, **78 carry ≥1 caries
  annotation** and those are the fitting set. (`c1_constant_baseline.py:78`'s docstring still
  says 86 — stale comment.)
- **Internal and external lesion agreement are NOT comparable to each other.** Different
  matchers, forced by the ~200x lesion-to-tooth area ratio. §8.12 knew this; the manuscript
  now states it, because 0.443 → 0.408 reads as a degradation figure and is not one.

**Left for the next session:** the manuscript is **12 pages against ISBI's 4**. It was written
as a complete, self-explaining document by request; the cut is venue-specific and should not
be done by re-compressing prose written to be clear. Decide the venue first.
