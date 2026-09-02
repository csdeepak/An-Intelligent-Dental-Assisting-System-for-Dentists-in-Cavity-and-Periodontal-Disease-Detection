#!/usr/bin/env python
"""Train the Lever-2 CariesXrays caries-lesion detector (YOLOv11l, detect).

Pre-registration: outputs/lever2_cariesxrays/PRE_REGISTRATION.md

Every hyperparameter is copied from `train_multicorpus_detector.py` (which reproduces the
canonical bbox run's `train_args.yaml`), so Lever 2 trains a detector the way this project
already does. The ONLY deliberate differences: `nc=1` class `decay`, this project's CariesXrays
seed-42 split, and epochs/patience trimmed 150/30 -> 120/25 to cap cost.

** The split is THIS PROJECT'S, not FPCL's ** (the official 4,800/1,200 split is not public).
The result is indicative vs the published table, not head-to-head. See the pre-registration.

The data.yaml is written at runtime from the resolved path, so "fix the absolute path on the
rented box" cannot be forgotten.

Usage (on the GPU box, after the geometry gate re-passes there):
    python train_cariesxrays_detector.py --data-root cariesxrays_det
"""

import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("cariesxrays_det"))
    ap.add_argument("--project", type=Path, default=Path("runs_lever2"))
    ap.add_argument("--name", default="cariesxrays_yolo11l")
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()

    import torch
    from ultralytics import YOLO

    root = args.data_root.resolve()
    for sub in ("images/train", "images/val", "labels/train", "labels/val"):
        if not (root / sub).is_dir():
            raise SystemExit(f"dataset incomplete: missing {root / sub}")

    n_train = len(list((root / "images/train").iterdir()))
    n_val = len(list((root / "images/val").iterdir()))
    print(f"train={n_train}  val={n_val}")
    if (n_train, n_val) != (4800, 1200):
        raise SystemExit(f"expected 4800/1200 (this project's seed-42 split), got {n_train}/{n_val}")

    yaml_path = root / "data_lever2.yaml"
    yaml_path.write_text(
        "# Lever 2 -- CariesXrays, THIS PROJECT'S seed-42 4800/1200 split (NOT FPCL's).\n"
        "# Written at runtime from the resolved path.\n"
        f"path: {root}\ntrain: images/train\nval: images/val\n\nnc: 1\nnames: ['decay']\n")
    print(f"wrote {yaml_path}")

    if not torch.cuda.is_available():
        raise SystemExit("no CUDA device -- refusing to train on CPU")
    p = torch.cuda.get_device_properties(0)
    print(f"GPU: {p.name} ({p.total_memory / 1e9:.1f} GB)")

    model = YOLO("yolo11l.pt")
    model.train(
        data=str(yaml_path),
        project=str(args.project),
        name=args.name,
        exist_ok=False,

        # --- identical to train_multicorpus_detector.py / the canonical bbox run,
        #     except epochs/patience (150/30 -> 120/25, cost cap; pre-registered) ---
        epochs=args.epochs,
        patience=25,
        batch=args.batch,
        imgsz=1024,
        device=0,
        workers=8,
        seed=42,
        deterministic=True,

        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        cos_lr=True,

        box=7.5, cls=0.5, dfl=1.5,

        hsv_h=0.0, hsv_s=0.0, hsv_v=0.2,
        degrees=10.0, translate=0.1, scale=0.2,
        shear=0.0, perspective=0.0,
        fliplr=0.5,
        flipud=0.0,       # NEVER vertical flip (breaks maxilla/mandible)
        mosaic=0.0,       # OFF -- house rule, corrupts spatial context in medical imaging
        mixup=0.0, copy_paste=0.0,

        save=True, save_period=-1, plots=True,
    )

    # COCO AP on the held-out val split -- the pre-registered primary metric.
    print("\n=== FINAL VAL (COCO AP) ===")
    m = model.val(data=str(yaml_path), split="val", imgsz=1024, iou=0.5, conf=0.001,
                  project=str(args.project), name=args.name + "_val", plots=True)
    print(f"AP@[.5:.95] = {m.box.map:.4f}")
    print(f"AP50        = {m.box.map50:.4f}")
    print(f"AP75        = {m.box.map75:.4f}")
    print("CariesXrays LEVER 2 DONE")


if __name__ == "__main__":
    main()
