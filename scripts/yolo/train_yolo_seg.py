"""
T0.6 / R1: Train YOLOv11l-seg on Tufts (instance segmentation)

STILL UNRUN as of 20 Aug 2026 — no GPU in any environment this has been prepared in.
Upstream of this script is now solid, though: teeth_polygon.json and all 1,000 raw Tufts
radiographs were located and downloaded 20 Aug 2026, and convert_tufts_to_yolo_seg.py (this
script's data source) was run end-to-end against them with zero errors — see
docs/research/T0.6_detector_reconciliation.md §3 for the full verification record. What
remains unverified is training itself (this script) and the frozen split
(outputs/eda_tufts/split_v1.csv is still missing — do not point dataset_seg/ at data built
from a substitute split without reading that doc section first).

This is the R1 upgrade (bbox -> instance mask) from the reconciled canonical detector
config. Every arg below is IDENTICAL to the canonical bbox run
(models/06_yolo_detection_a100_run/train_args.yaml, reproduced faithfully by
train_yolo.py after the 19 Aug 2026 drift fix) except:
  - model: yolo11l-seg.pt instead of yolo11l.pt
  - data: dataset_seg/data.yaml (polygon labels) instead of dataset/data.yaml (bbox labels)
This keeps the comparison in docs/research/T0.6_detector_reconciliation.md §2 clean —
any metric difference is attributable to the architecture/label change, not a confound
from a drifted hyperparameter.

Input:
  - dataset_seg/data.yaml  (from convert_tufts_to_yolo_seg.py)
  - dataset_seg/images/{train,val,test}/*.jpg
  - dataset_seg/labels/{train,val,test}/*.txt  (YOLO-seg polygon format)

Output:
  - runs/segment/tufts_seg_v1/weights/best.pt
  - runs/segment/tufts_seg_v1/weights/last.pt
  - runs/segment/tufts_seg_v1/results.csv
  - runs/segment/tufts_seg_v1/*.png

Training config (must match the canonical bbox run except model/data — see header):
  - Model: YOLOv11l-seg
  - Image size: 1024
  - Batch: 32
  - Epochs: 150, patience 30
  - Optimizer: AdamW, lr0 0.001, cosine schedule
  - Seed: 42, deterministic: True
  - Augmentations: clinically valid only (no vertical flip, no mosaic) — identical to the
    bbox run

Acceptance criterion (pre-registered BEFORE this script is ever run — do not edit after
seeing results): docs/research/T0.6_detector_reconciliation.md §2.
  - Test box mAP@0.5 >= 0.75
  - Test mask mAP@0.5 >= 0.65

Usage (on E2E H100):
    pip install ultralytics
    python train_yolo_seg.py

Expected runtime: similar order of magnitude to the bbox run (~35 min at 128 epochs on an
A100 at this batch/imgsz); seg heads are somewhat heavier per-step than detect heads, budget
more like 1-2 hours to be safe.
"""

import sys
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    print("ERROR: ultralytics not installed. Run: pip install ultralytics")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_YAML = Path("dataset_seg/data.yaml")
RUN_NAME = "tufts_seg_v1"
PROJECT_DIR = "runs/segment"


# =============================================================================
# VALIDATE
# =============================================================================

def validate_setup():
    assert DATASET_YAML.exists(), (
        f"Dataset YAML missing: {DATASET_YAML}. Run convert_tufts_to_yolo_seg.py first — "
        "and see docs/research/T0.6_detector_reconciliation.md §3 if teeth_polygon.json "
        "isn't available yet."
    )

    import torch
    if not torch.cuda.is_available():
        print("WARNING: CUDA not available. Training will run on CPU and be VERY slow.")
        print("If on E2E Networks H100, check driver installation.")
    else:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"GPU: {gpu_name} ({gpu_mem:.1f} GB)")


# =============================================================================
# TRAIN
# =============================================================================

def train():
    # Load COCO-pretrained YOLOv11l-seg (standard transfer learning, NOT dental-specific)
    model = YOLO("yolo11l-seg.pt")  # auto-downloads on first run

    results = model.train(
        data=str(DATASET_YAML),

        # Run management
        project=PROJECT_DIR,
        name=RUN_NAME,
        exist_ok=False,  # don't overwrite — fail loudly if run already exists

        # Core training — identical to the canonical bbox run
        epochs=150,
        patience=30,
        batch=32,
        imgsz=1024,
        device=0,
        workers=8,
        seed=42,
        deterministic=True,

        # Optimizer — identical to the canonical bbox run
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        cos_lr=True,

        # Loss weights (YOLO defaults, unchanged)
        box=7.5,
        cls=0.5,
        dfl=1.5,

        # CLINICAL AUGMENTATIONS — identical to the canonical bbox run
        hsv_h=0.0,
        hsv_s=0.0,
        hsv_v=0.2,
        degrees=10.0,
        translate=0.1,
        scale=0.2,
        shear=0.0,
        perspective=0.0,
        fliplr=0.5,
        flipud=0.0,             # NEVER vertical flip (breaks maxilla/mandible)
        mosaic=0.0,             # OFF — corrupts spatial context in medical imaging
        mixup=0.0,
        copy_paste=0.0,

        # Saving
        save=True,
        save_period=-1,
        plots=True,

        verbose=True,
    )

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("YOLOv11l-seg Training — Tufts (R1)")
    print("=" * 60)

    validate_setup()

    run_dir = Path(PROJECT_DIR) / RUN_NAME
    if run_dir.exists():
        print(f"\nERROR: Run directory already exists: {run_dir}")
        print("Either delete it or rename RUN_NAME in this script.")
        sys.exit(1)

    results = train()

    print(f"\nResults saved to: {run_dir.resolve()}")
    print(f"Best weights:     {run_dir.resolve()}/weights/best.pt")
    print("Next step: evaluate on the held-out test split and check against the")
    print("pre-registered acceptance criterion in docs/research/T0.6_detector_reconciliation.md §2")
    print("BEFORE deciding anything about this run's quality.")


if __name__ == "__main__":
    main()
