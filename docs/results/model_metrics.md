# Model metrics — scoreboard

Current best numbers only. One table per model, nothing else. For how a number was
obtained see `PAPER_MATERIAL.md`; for when and why it changed see `RESULTS_LOG.md`.

**Last updated:** 2026-08-22

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

## Stage 2 — FDI numbering · positional assignment · evaluated on DENTEX `disease/`

First measured 22 Aug 2026. Frozen detector (`tooth-detector-a100-1024-v1.0`, imgsz 1024,
conf 0.25, NMS IoU 0.50) + `src/fdi_assignment.py`, against 1,534 FDI-labelled teeth across
249 images. `test_181.png` excluded (byte-identical to a training image).

| Metric | Value |
|--------|-------|
| Detection recall | 74.6% (1,144 / 1,534) |
| Quadrant correct (of detected) | 90.2% |
| **FDI exact (of detected)** | **35.3%** |
| **FDI exact, end-to-end** | **26.3%** |
| Within ±1 position (correct quadrant) | 78.0% |

**This is a negative result and should be reported as one.** Quadrant assignment works; the
position digit does not. Errors are asymmetric — 40.2% too low vs 20.6% too high — because
detector recall decays toward the back of the arch (98.3% at position 1, **61.0% at position
8**), and each missed tooth shifts every tooth distal to it one place inward. At 26.3%
end-to-end, ~3 of 4 teeth in a per-tooth report would carry the wrong number.

Assignment confidence is calibrated in the right direction: 41.2% exact at confidence 1.0,
27.5% in [0.30, 0.60), 22.7% below 0.30 — so Stage-5 filtering can act on it.

Evaluates **GT → detection** only; detector precision is not reported because DENTEX
`disease/` annotates only teeth carrying a finding (~6 of ~30 per image). Full analysis:
`RESULTS_LOG.md` 2026-08-22c.

---

## Stage 3 — Caries cascade · ResNet18 · DENTEX

**Phase 1 gate (caries vs no_caries):** metrics not recorded — the classification report
was never saved in the notebook. Outstanding.

**Phase 2 severity (caries vs deep_caries), validation, 133 crops:**

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|----|---------|
| caries | 0.94 | 0.80 | 0.87 | 101 |
| deep_caries | 0.57 | 0.84 | 0.68 | 32 |
| **Accuracy** | | | **0.81** | 133 |
| **Macro F1** | | | **0.77** | |
| Weighted F1 | | | 0.82 | |

**Weights: `models/07_caries_cascade/`, version tag `caries-cascade-resnet18-v1.0`**
(retrieved from Kaggle and recorded 21 Aug 2026 — until then this was the only trained stage
with no local weight, no tag and no hash). The numbers above come from
**`phase2_final_bundle.pth`**, identified by matching this table against the saved
`classification_report` in cell 119 of `notebooks/caries/phase-1.ipynb`. SHA-256s, the
verified checkpoint lineage, and the retrieval history are in that directory's
`run_summary.txt`. The weights were verified **structurally only** — no torch exists on the
machine that recorded them, so they have not been loaded and cell 119's result has not been
reproduced; do that on the GPU box before trusting inference. These weights have never been
evaluated against the independent image-level test split that now exists,
`data/dentex/splits_v2.json`.

Validation-only — no held-out test split exists for caries. These numbers are also from
accuracy-selected checkpoints; as of 19 Aug 2026 the notebook selects on macro-F1 instead
(T0.3) and a held-out split script exists (T0.2), but neither fix has been re-run yet — see
`docs/results/RESULTS_LOG.md` 2026-08-19 entries. This table stays as-is until the re-run
produces new numbers to replace it with.

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

**Not implemented.** No end-to-end metric exists.
