# Model metrics — scoreboard

Current best numbers only. One table per model, nothing else. For how a number was
obtained see `PAPER_MATERIAL.md`; for when and why it changed see `RESULTS_LOG.md`.

**Last updated:** 2026-08-22 (Stage 2 replaced)

---

## Stage 1 — Tooth detection · YOLOv11l · Tufts

Best run: A100, imgsz 1024, 150 epochs requested / 128 run, best epoch 98.

| Split | Images | Instances | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|-------|--------|-----------|-----------|--------|---------|--------------|
| Validation | 150 | 3,794 | 0.788 | 0.772 | **0.834** | 0.367 |
| Test (held out) | 150 | 3,924 | 0.7643 | 0.7421 | **0.7824** | 0.3351 |

Superseded run (H200, imgsz 768, 50 ep): val mAP@0.5 **0.678**. Not test-evaluated.
Inference ~3.1 ms/image (A100). Weights: `models/06_yolo_detection_a100_run/best.pt`
(git-ignored, local only). **Canonical detector: FROZEN, 20 Aug 2026 — version tag
`tooth-detector-a100-1024-v1.0`, SHA-256 `4d9f099fb90bb03446fd1d81f2a509cd1589bdc0d4de83269894d9128e4b3a2b`.**
Verified by loading under Ultralytics (task=detect, 1 class, 25.3M params) and by
byte-identical `args.yaml`/`results.csv` against the copies already committed here — see
`docs/research/T0.6_detector_reconciliation.md` §1 for the full verification record.

**Ground-truth caveat (found 21 Aug 2026, numbers above unchanged):** the instance counts in
this table are the counts the model was actually scored against, but the Tufts source data
holds **66 more annotated teeth** than this dataset contains — objects with a corrupt
`bounding box` field (1×1 / 1×2 px) but an intact full-size polygon, dropped by the
converter's degenerate-box guard. Test ground truth is therefore 3,924 of 3,930 real
instances (0.15% missing); val is 3,794 of 3,807. Too small to move mAP@0.5 = 0.7824
materially, and the numbers above are **not** being restated — but the R1 seg dataset keeps
all 66, so its instance counts will legitimately differ. Analysis:
`docs/research/T0.6_detector_reconciliation.md` §3.5; paper framing: `PAPER_MATERIAL.md` §8.9.

---

## Stage 2 — FDI numbering · learned enumeration head · ResNet18 + positional features

**Current method as of 22 Aug 2026.** Evaluated on **164 leak-free `DENTEX/disease/` images**
(936 FDI-labelled teeth) with detector boxes (`tooth-detector-a100-1024-v1.0`, imgsz 1024,
conf 0.25, NMS IoU 0.50, rotated 90° CCW), Hungarian one-to-one assignment over the 32 codes.

**86 of the original 250 images are excluded as training duplicates** — 85 byte-identical to
enumeration-head training images, 1 to a detector training image. An earlier version of this
table reported 52.2% on the contaminated 249-image set; that figure was inflated by 5.7 points
and is withdrawn. Exclusion list: `data/dentex/disease_leaked_images.json`.

| Metric | Positional (superseded) | **Learned head** |
|--------|------------------------|------------------|
| Detection recall | 67.0% | 67.0% |
| Quadrant correct (of detected) | 92.3% | **94.7%** |
| FDI exact (of detected) | 34.1% | **69.4%** |
| **FDI exact, end-to-end** | 22.9% | **46.5%** |
| Duplicate FDI codes | 0 | **0** |

**A 2.0× improvement on both measures**, on data the head has never seen.

**It clears the positional ceiling decisively.** On teeth in complete (8-detection)
quadrants — the population where rank-order assignment is at its best — positional reaches
**66.3%** and the head **80.2%**, a margin of **+13.9 points** (n=101, same population for both).
The head wins in **every** completeness bucket. An order-independent method exceeds what
rank-order can reach, and not marginally.

> Corrected 24 Aug 2026. This was previously quoted as a 67.0% ceiling and a +2.4-point margin.
> **67.0% is the detector's recall, not the ceiling**, and the +2.4 compared the ceiling
> (complete quadrants only) against the head's accuracy over all detected teeth — two different
> populations. See RESULTS_LOG 2026-08-24a; recompute with
> `scripts/eval/analyze_stage2_ceiling.py`.

**End-to-end is capped by Stage 1.** At 67.0% recall, perfect numbering gives 67.0%; the head
reaches 69.4% of that maximum. Detector recall is now the binding constraint.

One-to-one ablation (clean 164-image set, 24 Aug 2026): plain argmax emits **679 anatomically
impossible duplicate codes** and scores 65.1% / 43.6%; Hungarian one-to-one removes **all** of
them for **69.4% / 46.5%** — **+4.3 points of-detected, +2.9 end-to-end** — at a cost of 2.1
points of raw quadrant accuracy (94.7% vs 96.8%), because the global constraint sometimes moves
a tooth across a quadrant boundary. Supersedes the contaminated-set figures.

**Input ablation** (val, 2,729 crops, `scripts/eval/ablate_head_inputs.py`) — quadrant split
into jaw and side, since *side* is the laterality claim:

| Condition | jaw | side (laterality) | position | FDI exact |
|---|---|---|---|---|
| full | 99.9% | **99.5%** | 92.1% | 91.6% |
| positional features → mean | 99.9% | **96.3%** | 92.1% | 88.8% |
| positional features shuffled | 99.8% | **76.6%** | 92.2% | 70.8% |

Positional features are worth **+3.2 points of laterality / +2.8 FDI exact** — not the decisive
signal earlier docs claimed, since the image alone recovers laterality at 96.3%. The image *is*
decisive for the **position digit**. Feeding *shuffled* coordinates costs 22.9 points, but that
is a worst case that does not occur: a shuffle teleports the coordinate to another tooth, often
across the midline. **Realistic box error is a small local jitter and costs ~nothing** — ±15% of
box size leaves FDI exact unchanged to 0.1pp, ±100% costs 0.2pp (RESULTS_LOG 2026-08-24e).
RESULTS_LOG 2026-08-24c.

Training-time val (GT boxes, **selection-biased — a diagnostic, not a result**): quadrant
99.4%, position 92.1%, FDI exact 91.6%; per-position accuracy 0.886–0.963, essentially flat,
unlike the detector's collapse from 98.3% (position 1) to 61.0% (position 8).

Weights **frozen and tracked**: `models/08_fdi_enumeration_head/`, tag
**`fdi-enumeration-head-resnet18-v1.0`**, SHA-256
`e6abf1cd959c36824ef0061db84a5fbc8793af314099cb3cc72027662445cc5a`. That directory also holds
the training config and per-epoch log, the full 33,461-row crop manifest, both evaluation
summaries and the leakage exclusion list. Figures: `docs/results/figures/enumeration_head/`.
Full record: `RESULTS_LOG.md` 2026-08-22i and **22j (the leakage correction)**.

---

## Stage 3 — Caries cascade · ResNet18 · DENTEX

**Phase 1 gate (caries vs no_caries) — `caries-gate-resnet18-v3.0`, pipeline default.**
Retrained 25 Aug 2026 with a rebuilt negative class (5,366 real healthy teeth, MD5-joined
from DENTEX's enumeration and disease subsets — RESULTS_LOG 2026-08-25a). Both T0.1 arms now
exist; arm B is frozen as the shipped model (val macro-F1 selected it, narrowly):

| | val macro-F1 | test macro-F1 | test caries P/R/F1 | test no_caries P/R/F1 |
|---|---|---|---|---|
| Arm A (no augmentation) | 0.7210 | 0.7212 | 0.47 / 0.62 / 0.54 | 0.93 / 0.88 / 0.91 |
| **Arm B (augmented, frozen)** | **0.7350** | 0.6948 | 0.40 / 0.74 / 0.52 | 0.95 / 0.81 / 0.87 |

**The A/B gap is not a finding.** Both arms swing ~0.27 in val macro-F1 across their own 15
epochs; the between-arm gap is 0.014–0.026 — 10–20&times; smaller than that noise floor.
Do not read this as "augmentation helps/hurts" (RESULTS_LOG 2026-08-25b).

**In-pipeline effect, same 12 images/detector/boxes, only the gate swapped**
(`scripts/eval/compare_caries_gates.py`): caries rate **84.9% &rarr; 19.1%** against an 11.7%
annotated floor (7.3&times; &rarr; 1.6&times; over-call). **Improved, not solved** — precision
0.40 means roughly six of ten positives are still wrong, and the healthy class rests on
presumed-negative labelling (RESULTS_LOG 2026-08-25a).

Weights: `models/09_caries_gate_v3/caries_gate_v3.pth` (gitignored, 43 MB — see
`docs/EXTERNAL_DRIVE.md`), sha256 `8f4a99ba412c…`, verified loadable and reproduced live
through `scripts/run_inference.py` (not just structurally checked).

**Phase 2 severity (caries vs deep_caries), validation, 133 crops — unchanged, still
`phase1_legacy`-era:**

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|----|---------|
| caries | 0.94 | 0.80 | 0.87 | 101 |
| deep_caries | 0.57 | 0.84 | 0.68 | 32 |
| **Accuracy** | | | **0.81** | 133 |
| **Macro F1** | | | **0.77** | |
| Weighted F1 | | | 0.82 | |

**Weights: `models/07_caries_cascade/phase2_final_bundle.pth`, version tag
`caries-cascade-resnet18-v1.0`.** Loaded and reproduced live via `run_inference.py`
(`DEF_CARIES_SEVERITY`) — the "structurally only, no torch available" caveat that used to sit
here no longer applies; this machine's environment was fixed 24 Aug 2026. Still trained on
`phase1_legacy`-era crops and not re-run this session — **only the gate was rebuilt**, not the
severity head. Validation-only; no held-out test split for Phase 2 exists yet.

---

## Stage 4a — Bone loss binary · ResNet18 + Focal Loss · Tufts

Validation, 1,558 crops at real-world prevalence (1,499 normal / 59 diseased).

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Macro F1 | **0.9233** | ≥ 0.72 | PASS |
| F1 normal (class 0) | 0.9943 | ≥ 0.75 | PASS |
| F1 diseased (class 1) | 0.8522 | ≥ 0.70 | PASS |
| Precision / Recall diseased | 0.8750 / 0.8305 | — | — |
| Sensitivity | 83.05% | — | — |
| Specificity | 99.53% | — | — |
| Accuracy | 98.91% | — | misleading at 4% prevalence |

Confusion matrix: TN 1,492 · FP 7 · FN 10 · TP 49.

---

## Stage 4b — Bone loss severity 3-class · ResNet18 + Focal Loss · Tufts

Validation, 52 crops. **Low support — treat as provisional.**

| Class (overlap ratio) | Precision | Recall | F1 | Support |
|-----------------------|-----------|--------|----|---------|
| Mild (≤ 0.05) | 1.00 | 0.67 | 0.80 | 6 |
| Moderate (0.05–0.15) | 0.80 | 0.57 | 0.6667 | 28 |
| Severe (> 0.15) | 0.57 | 0.89 | 0.6957 | 18 |
| **Macro F1** | | | **0.7208** | 52 |

Accuracy 69.23%. Target macro F1 0.72 — met by 0.0008 on 52 samples.

---

## Exploratory — CEJ bone level estimation (classical CV, not in pipeline)

| Metric | Value |
|--------|-------|
| Crops processed | 296 / 296 (100% completion, **not** accuracy) |
| Flagged reliable | 185 (62.5%) |
| Exact agreement with overlap-based severity | **15.1%** |
| Agreement within ±1 class | 61.6% |

Not integrated. Reported as a negative result.

---

## Stages 5–6 — Pipeline integration + report

**Implemented 24 Aug 2026** (`scripts/run_inference.py`, RESULTS_LOG 2026-08-24f — R4, paper
claim C3). Image in, per-tooth JSON + overlay out, through all six stages.

**In-pipeline batch result, 12 leak-free DENTEX images, 299 detected teeth:**

| | |
|---|---|
| Caries-positive (pipeline default, v3 gate) | 57 (19.1%), was 254 (84.9%) pre-fix |
| Bone-loss-positive | 2 (0.7%) — near-inert off-Tufts, domain shift |
| Duplicate FDI codes | 0 / 299 |

**Lesion-localisation agreement — 25 Aug 2026** (`scripts/eval/lesion_localization.py`,
RESULTS_LOG 2026-08-25c), 164 leak-free images: of 479 real çürük (caries) lesions,
**204 have a predicted-diseased tooth spatially overlapping them — 42.6%**. This is a
tooth-level correspondence check (the pipeline has no finer localisation than "which tooth"),
not a pixel-level segmentation-quality metric. Built against DENTEX first specifically so it
generalises to Ningxia's masks later without new code under deadline pressure — see
`PAPER_MATERIAL.md` §8.11 for the full scoping and caveats.

Both are pure inference; neither needed a GPU rental.

---

## External validation (C2) — Ningxia, 4 hospitals · 25 Aug 2026

**Zero leakage** against Tufts, DENTEX `disease/`, `quadrant_enumeration`,
`quadrant-enumeration-disease` and `quadrant` — each checked separately (0 / 2,912 unique
Ningxia test hashes). LOCKED data: evaluated once, no tuning of any kind against it.

**Caries — focal-lesion centroid containment, stratified (never pooled):**

| Split | Centre | Lesions | Covered | Strict (1:1) |
|---|---|---|---|---|
| test1 | cross-centre | 316 | **26.6%** | 23.7% |
| test2 | same-centre-as-*Ningxia*-train | 349 | **43.3%** | 36.4% |
| test3 | cross-centre | 162 | **37.0%** | 29.0% |
| test4 | cross-centre | 186 | **22.6%** | 18.8% |

DENTEX internal was 42.6%; Ningxia sits at or below it across four independent hospitals.
*All four splits are equally external to us* — we never trained on Ningxia, so "same-centre-as-train"
describes Ningxia's own split design, not proximity to our training data.

**Periodontitis — affected-tooth sensitivity** (of teeth ≥50% inside the expert-marked region,
how many were flagged): test1 3.7%, test2 0.8%, test3 1.5%, test4 5.4% (pooled 172/6,222 = 2.8%).
Combined with Tufts in-domain (0.92 macro-F1) and DENTEX (0.7% firing), the bone-loss branch's
domain-shift failure is now measured on **two** independent external datasets.

**Specificity/AUC are not computable on Ningxia** — it has no healthy controls. They come from
Tufts. See `PAPER_MATERIAL.md` §8.12 for the withdrawn first-pass periodontitis figures and why
the metric had to differ by category.
