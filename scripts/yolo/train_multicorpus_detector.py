#!/usr/bin/env python
"""Train the Lever-1 detector arms. Config is R1's, with ONE variable changed per arm.

Pre-registration: outputs/detector_multicorpus/PRE_REGISTRATION.md (+ its two-arm amendment).

    --arm tuftsonly    YOLOv11l-detect on Tufts only      (Control B: isolates seg -> detect)
    --arm multicorpus  YOLOv11l-detect on Tufts + DENTEX  (Arm: isolates the added data)

Every hyperparameter below is copied from `train_yolo_seg.py`, which itself reproduces the
canonical bbox run's `train_args.yaml`. The ONLY deliberate differences are:
  - `yolo11l.pt` instead of `yolo11l-seg.pt` -- forced, DENTEX has no polygons
  - the train split, which is the variable under test

Both arms share byte-identical val/test. The Tufts-only train split is derived here from the
same uploaded tree by filename (`dentex_` prefix marks DENTEX), so there is no second conversion
and no opportunity for the arms to differ anywhere except the train set.

The data.yaml is written at runtime from the resolved dataset path, so the "fix the absolute
path for the rented machine" step in GPU_SETUP.md 2b does not apply and cannot be forgotten.

Usage (on the GPU box):
    python train_multicorpus_detector.py --arm tuftsonly
    python train_multicorpus_detector.py --arm multicorpus
"""

import argparse
import shutil
from pathlib import Path


def build_tufts_only_split(root: Path):
    """images/train_tufts + labels/train_tufts, Tufts files only. Idempotent."""
    ti, tl = root / "images/train_tufts", root / "labels/train_tufts"
    if ti.is_dir() and any(ti.iterdir()):
        print(f"  train_tufts already present: {len(list(ti.iterdir()))} images")
        return
    ti.mkdir(parents=True, exist_ok=True)
    tl.mkdir(parents=True, exist_ok=True)
    n = 0
    for img in sorted((root / "images/train").iterdir()):
        if img.name.startswith("dentex_"):
            continue
        lab = root / "labels/train" / (img.stem + ".txt")
        if not lab.exists():
            continue
        shutil.copy2(img, ti / img.name)
        shutil.copy2(lab, tl / lab.name)
        n += 1
    print(f"  built train_tufts: {n} images (expect 700)")
    if n != 700:
        raise SystemExit(f"train_tufts has {n} images, expected 700 -- refusing to train")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["tuftsonly", "multicorpus"], required=True)
    ap.add_argument("--data-root", type=Path, default=Path("detector_multicorpus"))
    ap.add_argument("--project", type=Path, default=Path("runs_lever1"))
    args = ap.parse_args()

    import torch
    from ultralytics import YOLO

    root = args.data_root.resolve()
    if not (root / "images/val").is_dir():
        raise SystemExit(f"dataset not found at {root}")

    if args.arm == "tuftsonly":
        build_tufts_only_split(root)
        train_dir = "images/train_tufts"
    else:
        train_dir = "images/train"

    n_train = len(list((root / train_dir).iterdir()))
    n_val = len(list((root / "images/val").iterdir()))
    n_test = len(list((root / "images/test").iterdir()))
    print(f"ARM={args.arm}  train={n_train}  val={n_val}  test={n_test}")
    if (n_val, n_test) != (150, 150):
        raise SystemExit(f"val/test must be 150/150, got {n_val}/{n_test}")

    yaml_path = root / f"data_{args.arm}.yaml"
    yaml_path.write_text(
        f"# Lever 1, arm={args.arm}. Written at runtime from the resolved path.\n"
        f"path: {root}\ntrain: {train_dir}\nval: images/val\ntest: images/test\n\n"
        f"nc: 1\nnames: ['tooth']\n")
    print(f"wrote {yaml_path}")

    if torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        print(f"GPU: {p.name} ({p.total_memory/1e9:.1f} GB)")
    else:
        raise SystemExit("no CUDA device -- refusing to train on CPU")

    model = YOLO("yolo11l.pt")
    model.train(
        data=str(yaml_path),
        project=str(args.project),
        name=args.arm,
        exist_ok=False,

        # --- identical to train_yolo_seg.py / the canonical bbox run ---
        epochs=150,
        patience=30,
        batch=32,
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
        flipud=0.0,      # NEVER vertical flip (breaks maxilla/mandible)
        mosaic=0.0,      # OFF -- corrupts spatial context in medical imaging
        mixup=0.0, copy_paste=0.0,

        save=True, save_period=-1, plots=True,
    )
    print(f"ARM {args.arm} DONE")


if __name__ == "__main__":
    main()
