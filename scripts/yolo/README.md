# `scripts/yolo/` — Stage 1 tooth-detection scripts

These three scripts were recovered from the ad-hoc `DataSets/` exploration workspace that
used to sit at the repo root (that workspace has since been relocated to
`_repo_archive/datasets_workspace/`, a sibling of this repo — nothing was deleted).

They are the **Stage 1 (YOLOv11 tooth detection)** toolchain and are kept separate from the
scripts in `scripts/` one level up, which belong to the **Stage 2–5 crop/classifier**
toolchain. Both sets are live; they simply serve different halves of the pipeline.

| Script | What it does |
|--------|--------------|
| `convert_tufts_to_yolo.py` | Converts Tufts annotations to YOLO format. Reads `Radiographs_rotated/` (portrait 840×1615), `Segmentation/teeth_bbox.json` and the frozen 70/15/15 split CSV; writes `dataset/images/{train,val,test}`, `dataset/labels/{train,val,test}` (`0 cx cy w h`, normalised) and `dataset/data.yaml`. Single-class detection (`tooth`), primary/letter teeth **included**, degenerate boxes (w<2 or h<2) dropped, unlabelled images skipped. |
| `train_yolo.py` | Fine-tunes YOLOv11l on the converted dataset. Locked config: imgsz 1024, AdamW, cosine LR 1e-3 → 1e-5, 150 epochs with early-stopping patience 30, clinically-valid augmentation only (no vertical flip, no mosaic). Writes `runs/detect/<name>/weights/{best,last}.pt`, `results.csv` and training curves. |
| `evaluate_yolo.py` | Runs the trained `best.pt` against the held-out **test** split, writes an eval run directory with metric plots, prediction visualisations on 20 test images, and an `eval_summary.txt`. |

## Relationship to the rest of the repo

- The run these scripts produced (A100, imgsz 1024, 150 epochs) is the current best
  detector — see `models/06_yolo_detection_a100_run/` and
  `docs/results/figures/yolo_detection_a100/`.
- The notebooks that actually executed the two competing runs live in
  `notebooks/yolo_detection/`.

## Caveats before re-running

- Paths at the top of `convert_tufts_to_yolo.py` are **hard-coded to the original macOS
  workspace** (`/Users/.../Downloads/Capstone/DataSets`). Edit `TUFTS_ROOT`, `SPLIT_CSV`
  and `DATASET_DIR` before use.
- The docstring targets in `train_yolo.py` / `evaluate_yolo.py` (mAP@0.5 ≥ 0.90) were
  copied from published Tufts benchmarks and are **not** what this project achieved.
  Actual numbers: val mAP@0.5 = 0.834, test mAP@0.5 = 0.782. See
  `docs/results/model_metrics.md`.
- `RUN_NAME` in the scripts is `tufts_v1`; the executed run was named `tufts_clean_v1`.
