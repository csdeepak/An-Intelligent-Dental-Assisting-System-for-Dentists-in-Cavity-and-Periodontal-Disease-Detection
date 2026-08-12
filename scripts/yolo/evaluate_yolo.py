"""
Week 2 Day 4: Evaluate trained YOLO on Tufts test set

Input:
  - runs/detect/tufts_v1/weights/best.pt   (trained model)
  - dataset/data.yaml

Output:
  - runs/detect/tufts_v1_eval/              (validation metrics)
  - runs/detect/tufts_v1_eval/predictions/  (visualizations on 20 test images)
  - eval_summary.txt                        (single-file numeric summary)

Targets based on Papers 42, 45 (Tufts benchmarks):
  - mAP@0.5      ≥ 0.90  (acceptable v1)
  - mAP@0.5      ≥ 0.95  (publication-grade)
  - mAP@0.5:0.95 ≥ 0.65
  - Precision    ≥ 0.90
  - Recall       ≥ 0.90

If below acceptable thresholds → investigate before Phase 2.
If above acceptable thresholds → freeze Stage 1, move to caries work.

Usage:
    python evaluate_yolo.py
"""

import sys
from pathlib import Path
import random

try:
    from ultralytics import YOLO
except ImportError:
    print("ERROR: ultralytics not installed. Run: pip install ultralytics")
    sys.exit(1)

import matplotlib.pyplot as plt
from PIL import Image


# =============================================================================
# CONFIGURATION
# =============================================================================

WEIGHTS_PATH = Path("runs/detect/tufts_v1/weights/best.pt")
DATASET_YAML = Path("dataset/data.yaml")
EVAL_DIR = Path("runs/detect/tufts_v1_eval")
N_VISUALIZATIONS = 20


# =============================================================================
# RUN VAL METRICS (test set)
# =============================================================================

def run_validation():
    assert WEIGHTS_PATH.exists(), f"Weights missing: {WEIGHTS_PATH}. Train first."
    
    model = YOLO(str(WEIGHTS_PATH))
    
    print("Running validation on TEST split...")
    metrics = model.val(
        data=str(DATASET_YAML),
        split="test",
        project=str(EVAL_DIR.parent),
        name=EVAL_DIR.name,
        exist_ok=True,
        imgsz=1024,
        batch=16,
        device=0,
        plots=True,
        save_json=True,
        verbose=True,
    )
    
    # Extract key metrics
    mp = metrics.box.mp          # mean precision
    mr = metrics.box.mr          # mean recall
    map50 = metrics.box.map50    # mAP@0.5
    map50_95 = metrics.box.map   # mAP@0.5:0.95
    
    return {
        "precision": float(mp),
        "recall": float(mr),
        "mAP_50": float(map50),
        "mAP_50_95": float(map50_95),
    }


# =============================================================================
# VISUALIZE PREDICTIONS ON TEST IMAGES
# =============================================================================

def visualize_predictions():
    model = YOLO(str(WEIGHTS_PATH))
    
    test_img_dir = Path("dataset/images/test")
    test_imgs = sorted(test_img_dir.glob("*.jpg")) + sorted(test_img_dir.glob("*.JPG"))
    
    if len(test_imgs) == 0:
        print(f"No test images found in {test_img_dir}")
        return
    
    random.seed(42)
    sample_imgs = random.sample(test_imgs, min(N_VISUALIZATIONS, len(test_imgs)))
    
    vis_dir = EVAL_DIR / "predictions"
    vis_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGenerating predictions on {len(sample_imgs)} test images...")
    
    for img_path in sample_imgs:
        results = model.predict(
            str(img_path),
            imgsz=1024,
            conf=0.25,
            iou=0.5,
            device=0,
            verbose=False,
        )
        
        # Save the annotated image (Ultralytics built-in)
        result = results[0]
        annotated = result.plot()  # numpy array with boxes drawn
        
        # Convert BGR→RGB and save via matplotlib for consistent style
        import cv2
        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        
        fig, ax = plt.subplots(figsize=(8, 14))
        ax.imshow(annotated_rgb)
        n_detections = len(result.boxes)
        ax.set_title(f"{img_path.name} — {n_detections} teeth detected")
        ax.axis("off")
        
        out_path = vis_dir / f"{img_path.stem}_pred.png"
        plt.savefig(out_path, dpi=80, bbox_inches="tight")
        plt.close()
    
    print(f"Saved predictions to {vis_dir}")


# =============================================================================
# WRITE SUMMARY
# =============================================================================

def write_summary(metrics):
    summary = [
        "=" * 60,
        "YOLOv11l — Tufts v1 — Evaluation Summary",
        "=" * 60,
        "",
        f"Weights: {WEIGHTS_PATH}",
        f"Test set: dataset/images/test/ ({len(list(Path('dataset/images/test').glob('*')))} images)",
        "",
        "METRICS",
        "-" * 60,
        f"  Precision:     {metrics['precision']:.4f}",
        f"  Recall:        {metrics['recall']:.4f}",
        f"  mAP@0.5:       {metrics['mAP_50']:.4f}",
        f"  mAP@0.5:0.95:  {metrics['mAP_50_95']:.4f}",
        "",
        "DECISION",
        "-" * 60,
    ]
    
    if metrics["mAP_50"] >= 0.95:
        summary.append("  ✓ PUBLICATION-GRADE — freeze Stage 1, move to caries work.")
    elif metrics["mAP_50"] >= 0.90:
        summary.append("  ✓ ACCEPTABLE — freeze Stage 1, move to caries work.")
        summary.append("    Consider retuning in Phase 4 if time permits.")
    elif metrics["mAP_50"] >= 0.80:
        summary.append("  ⚠ MARGINAL — investigate failures before freezing.")
        summary.append("    Check predictions/ for systematic errors.")
    else:
        summary.append("  ✗ INSUFFICIENT — re-examine data quality or training config.")
        summary.append("    Do NOT proceed to Phase 2 with this model.")
    
    summary.extend([
        "",
        "NEXT STEPS",
        "-" * 60,
        f"  Review: {EVAL_DIR}/predictions/ (20 test-set visualizations)",
        f"  Review: {EVAL_DIR}/ (PR curves, confusion matrix)",
        f"  If acceptable: tag this model as stage1-v1 in git",
        "",
    ])
    
    out_path = Path("eval_summary.txt")
    out_path.write_text("\n".join(summary))
    
    print("\n".join(summary))
    print(f"\nSummary saved to: {out_path.resolve()}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("YOLOv11l — Evaluation")
    print("=" * 60)
    
    metrics = run_validation()
    visualize_predictions()
    write_summary(metrics)


if __name__ == "__main__":
    main()
