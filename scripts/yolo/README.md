# `scripts/yolo/` — Stage 1 tooth-detection scripts

**Last verified: 22 August 2026.**

Three of these were recovered from the ad-hoc `DataSets/` exploration workspace that used to
sit at the repo root (relocated to `_repo_archive/datasets_workspace/`, a sibling of this repo
— nothing was deleted). Two more were added in August 2026 for the **R1 bbox → instance-mask
upgrade** (`docs/research/MASTER_PLAN_2026H2.md` §3 R1).

They are the **Stage 1 (YOLOv11 tooth detection)** toolchain and are kept separate from the
scripts in `scripts/` one level up, which belong to the **Stage 2–5 crop/classifier**
toolchain. Both sets are live; they simply serve different halves of the pipeline.

## The two toolchains here

| | bbox (current canonical) | seg (R1 upgrade, prepared not run) |
|---|---|---|
| convert | `convert_tufts_to_yolo.py` | `convert_tufts_to_yolo_seg.py` |
| train | `train_yolo.py` | `train_yolo_seg.py` |
| evaluate | `evaluate_yolo.py` | — (use Ultralytics val) |
| dataset | `_repo_archive/datasets_workspace/dataset/` | `data/tufts/dataset_seg/` (built, 26,005 instances) |
| status | **frozen**, `tooth-detector-a100-1024-v1.0` | **needs GPU only** — data ready, criterion pre-registered in `T0.6_detector_reconciliation.md` §2 |

`rotate_tufts_radiographs.py` sits upstream of both: the raw Tufts release ships **landscape
1615×840**, and every converter expects portrait 840×1615. That rotation is **90° counter-clockwise** —
undocumented tribal knowledge until Aug 2026, then recorded as *clockwise* until 22 Aug, when
comparing all 1,000 raw/rotated pairs settled it (1000/1000 CCW, 0/1000 CW). The visual check
that originally set the direction could not have caught the error: CW and CCW differ by 180°,
and tooth detection is largely indifferent to a 180° flip.

| Script | What it does |
|--------|--------------|
| `convert_tufts_to_yolo.py` | Converts Tufts annotations to YOLO format. Reads `Radiographs_rotated/` (portrait 840×1615), `Segmentation/teeth_bbox.json` and the frozen 70/15/15 split CSV; writes `dataset/images/{train,val,test}`, `dataset/labels/{train,val,test}` (`0 cx cy w h`, normalised) and `dataset/data.yaml`. Single-class detection (`tooth`), primary/letter teeth **included**, degenerate boxes (w<2 or h<2) dropped, unlabelled images skipped. |
| `train_yolo.py` | Fine-tunes YOLOv11l on the converted dataset. Locked config: imgsz 1024, AdamW, cosine LR 1e-3 → 1e-5, 150 epochs with early-stopping patience 30, clinically-valid augmentation only (no vertical flip, no mosaic). Writes `runs/detect/<name>/weights/{best,last}.pt`, `results.csv` and training curves. |
| `evaluate_yolo.py` | Runs the trained `best.pt` against the held-out **test** split, writes an eval run directory with metric plots, prediction visualisations on 20 test images, and an `eval_summary.txt`. |

## Relationship to the rest of the repo

- The run these scripts produced (A100, imgsz 1024, 150 epochs) is the **frozen canonical
  detector**, tag `tooth-detector-a100-1024-v1.0` — see `models/06_yolo_detection_a100_run/`
  and `docs/results/figures/yolo_detection_a100/`. T0.6 is closed.
- The notebooks that actually executed the two competing runs live in
  `notebooks/yolo_detection/`.

## Caveats before re-running

- **`convert_tufts_to_yolo.py` silently drops 66 real teeth.** Its degenerate-box guard
  (`w < 2 or h < 2`) fires on 66 objects whose `bounding box` field in the source JSON is
  corrupt (1×1 / 1×2 px) while their polygon is intact and full-size — verified, and three
  were rendered to confirm they are real teeth. So the bbox dataset is missing 47 train / 13
  val / 6 test teeth, and the frozen detector's numbers were scored against test ground truth
  holding 3,924 of 3,930 real instances. **Left unfixed on purpose** — changing it would
  invalidate the frozen detector's reproducibility. `convert_tufts_to_yolo_seg.py` keeps all
  66. Full analysis: `docs/research/T0.6_detector_reconciliation.md` §3.5.
- Paths at the top of `convert_tufts_to_yolo.py` are **hard-coded to the original macOS
  workspace** (`/Users/.../Downloads/Capstone/DataSets`, which no longer exists). Edit
  `TUFTS_ROOT`, `SPLIT_CSV` and `DATASET_DIR` before use. The **seg** converter does not have
  this problem — its paths are environment-overridable (`TUFTS_ROOT`, `TUFTS_IMG_DIR`,
  `TUFTS_POLY_JSON`, `TUFTS_SPLIT_CSV`, `TUFTS_SEG_DATASET_DIR`), so the script that runs is
  the script under review.
- The docstring targets in `train_yolo.py` / `evaluate_yolo.py` (mAP@0.5 ≥ 0.90) were
  copied from published Tufts benchmarks and are **not** what this project achieved.
  Actual numbers: val mAP@0.5 = 0.834, test mAP@0.5 = 0.782. See
  `docs/results/model_metrics.md`.
- `RUN_NAME` in the scripts is `tufts_v1`; the executed run was named `tufts_clean_v1`.
