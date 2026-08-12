# `notebooks/yolo_detection/` — Stage 1 tooth detection runs

Two YOLOv11l fine-tuning runs were executed on the same Tufts dataset and the same
70/15/15 image-level split. They were never reconciled into a single canonical model, so
both notebooks are kept here side by side.

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

## Open item

Pick one canonical detector and freeze it (weights hash + config recorded in
`docs/results/model_metrics.md`) before the full-pipeline integration in Stage 5/6.
