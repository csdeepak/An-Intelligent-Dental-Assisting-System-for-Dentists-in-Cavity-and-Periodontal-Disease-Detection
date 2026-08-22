# `notebooks/yolo_detection/` — Stage 1 tooth detection runs

Two YOLOv11l fine-tuning runs were executed on the same Tufts dataset and the same
70/15/15 image-level split. They were **reconciled on 20 August 2026 (T0.6)** — the A100 run
is the frozen canonical detector, tag `tooth-detector-a100-1024-v1.0`, and the H200 run is
formally superseded. Both notebooks are kept side by side as the record of that comparison.

| Notebook | GPU | imgsz | Epochs | Val mAP@0.5 | Test mAP@0.5 | Verdict |
|----------|-----|-------|--------|-------------|--------------|---------|
| `a100_1024px_150ep.ipynb` | NVIDIA A100 80GB PCIe | **1024** | 150 requested, 128 run (early stop, patience 30), best epoch 98 | **0.834** | **0.782** | **Current best — use this one** |
| `h200_768px_50ep.ipynb` | NVIDIA H200 143 GB | 768 | 50 | 0.678 | not evaluated | Superseded |

Both notebooks contain several exploratory cells at other resolutions/epoch counts; the
table above reflects the run whose **output cells were actually executed and saved** in
each notebook (identified by the `CUDA:0 (...)` device banner and the final validation
block in the saved outputs).

## Which one is real, and how we know

Filenames alone were ambiguous — both notebooks were originally called `YOLO_trained.ipynb`
(one at the repo root, one inside `A100_150/`). They were disambiguated by reading the
saved output cells rather than the code cells:

- `a100_1024px_150ep.ipynb` → `CUDA:0 (NVIDIA A100 80GB PCIe, 81038MiB)`, `imgsz=1024`,
  `128 epochs completed in 0.592 hours`, final `all 150 3794 0.788 0.772 0.834 0.367`,
  plus a test-set pass `all 150 3924 0.764 0.742 0.782 0.335`.
- `h200_768px_50ep.ipynb` → `CUDA:0 (NVIDIA H200, 143072MiB)`, `imgsz=768`,
  `50 epochs completed in 0.093 hours`, final `all 150 3794 0.609 0.678 0.678 0.282`.

## Takeaway

Input resolution is the dominant factor for this task. Teeth on an 840×1615 OPG are dense,
thin and highly overlapping; downsampling to 768 costs ~15 mAP@0.5 points relative to 1024.
Any future detection work should start at imgsz ≥ 1024 and budget the longer schedule.

## Artifacts

- Checkpoints + full training config + per-epoch CSV: `models/06_yolo_detection_a100_run/`
- Curves, confusion matrices, qualitative predictions: `docs/results/figures/yolo_detection_a100/`
- Reusable CLI versions of the same pipeline: `scripts/yolo/`

## Open item — CLOSED 20 August 2026

~~Pick one canonical detector and freeze it before the full-pipeline integration.~~ Done:
`best.pt`/`last.pt` located, verified (loads under Ultralytics, byte-identical
`args.yaml`/`results.csv` against the committed copies), copied into
`models/06_yolo_detection_a100_run/`, tagged `tooth-detector-a100-1024-v1.0`, SHA-256 recorded
in `docs/results/model_metrics.md` and `docs/research/T0.6_detector_reconciliation.md` §1.

**What replaced it as the open item:** the R1 retrain to `YOLOv11l-seg`. Its dataset is built
(`data/tufts/dataset_seg/`, 26,005 instances on the same frozen split) and its acceptance
criterion is pre-registered in T0.6 §2. It needs GPU time and nothing else.
