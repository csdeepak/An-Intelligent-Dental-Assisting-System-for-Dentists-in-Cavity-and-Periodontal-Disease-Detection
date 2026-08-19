"""
Week 2 Day 2-3: Train YOLOv11l on Tufts

Input:
  - dataset/data.yaml  (from convert_tufts_to_yolo.py)
  - dataset/images/{train,val,test}/*.jpg
  - dataset/labels/{train,val,test}/*.txt

Output:
  - runs/detect/tufts_v1/weights/best.pt   (best model by val mAP)
  - runs/detect/tufts_v1/weights/last.pt   (final epoch model)
  - runs/detect/tufts_v1/results.csv       (per-epoch metrics)
  - runs/detect/tufts_v1/*.png             (training curves)

Training config — reconciled 19 Aug 2026 (T0.6) to match the actual canonical run
exactly, args-for-args, against models/06_yolo_detection_a100_run/train_args.yaml
(this script had drifted: batch was 16 here vs. 32 in the real run). Do not edit
without updating that reconciliation record too — see
docs/research/T0.6_detector_reconciliation.md.
  - Model: YOLOv11l (detection — not segmentation; see train_yolo_seg.py for R1)
  - Image size: 1024 (downsampled from 1615 portrait)
  - Batch: 32
  - Epochs: 150 with early stopping patience 30
  - Optimizer: AdamW
  - Learning rate: 0.001 → 0.00001 (cosine)
  - Seed: 42, deterministic: True (reproducibility)
  - Augmentations: clinically valid only (no vertical flip, no mosaic)

Usage (on E2E H100):
    # One-time setup
    pip install ultralytics

    # Run training
    python train_yolo.py

Expected runtime: 4-6 hours on H100 at batch 32.
Achieved by the canonical A100 run (test set, 150/150→128 early stop):
mAP@0.5 0.7824, mAP@0.5:0.95 0.3351 — see docs/results/RESULTS_LOG.md
2026-04-23 entry. The original ≥0.90 target below this line was the paper-derived
acceptance bar, not an achieved result; kept for context, not as a claim.
Original target context: mAP@0.5 ≥ 0.90 (based on Papers 42, 45 Tufts results).
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

DATASET_YAML = Path("dataset/data.yaml")
RUN_NAME = "tufts_clean_v1"  # matches the canonical A100 run's name for traceability
PROJECT_DIR = "runs/detect"


# =============================================================================
# VALIDATE
# =============================================================================

def validate_setup():
    assert DATASET_YAML.exists(), f"Dataset YAML missing: {DATASET_YAML}. Run convert_tufts_to_yolo.py first."
    
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
    # Load COCO-pretrained YOLOv11l (standard transfer learning, NOT dental-specific)
    model = YOLO("yolo11l.pt")  # auto-downloads on first run
    
    results = model.train(
        data=str(DATASET_YAML),
        
        # Run management
        project=PROJECT_DIR,
        name=RUN_NAME,
        exist_ok=False,  # don't overwrite — fail loudly if run already exists
        
        # Core training
        epochs=150,
        patience=30,           # early stop if no val improvement for 30 epochs
        batch=32,              # matches canonical A100 run; reduce if OOM
        imgsz=1024,            # downsample from 1615 portrait
        device=0,              # GPU 0
        workers=8,             # dataloader workers
        seed=42,
        deterministic=True,

        # Optimizer
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,              # final lr = lr0 * lrf
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        cos_lr=True,           # cosine schedule
        
        # Loss weights (YOLO defaults)
        box=7.5,
        cls=0.5,
        dfl=1.5,
        
        # CLINICAL AUGMENTATIONS — stay here
        hsv_h=0.0,             # no hue shift (grayscale)
        hsv_s=0.0,             # no saturation shift
        hsv_v=0.2,             # brightness ±20% (scanner variation)
        degrees=10.0,          # ±10° rotation (patient head tilt)
        translate=0.1,
        scale=0.2,             # ±20% scale
        shear=0.0,
        perspective=0.0,
        fliplr=0.5,            # horizontal flip OK (anatomy roughly symmetric)
        flipud=0.0,            # NEVER vertical flip (breaks maxilla/mandible)
        mosaic=0.0,            # OFF — corrupts spatial context in medical imaging
        mixup=0.0,             # OFF
        copy_paste=0.0,        # OFF for v1
        
        # Saving
        save=True,
        save_period=-1,        # only save best + last
        plots=True,            # training curves
        
        # Verbose
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
    print("YOLOv11l Training — Tufts v1")
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
    print(f"Next step: run evaluate_yolo.py")


if __name__ == "__main__":
    main()
