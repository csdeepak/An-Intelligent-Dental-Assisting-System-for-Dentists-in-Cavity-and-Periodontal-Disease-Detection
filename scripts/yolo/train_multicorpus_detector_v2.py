#!/usr/bin/env python
"""Train the Lever A detector arms. Config is R1's / the canonical bbox run's, unchanged.

Pre-registration: outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md

    --arm controlB   YOLOv11l-detect, Tufts only          (isolates seg -> detect head)
    --arm arm3c      YOLOv11l-detect, Tufts+DENTEX+Kaggle  (PRIMARY -- isolates multi-corpus data)
    --arm arm4c      YOLOv11l-detect, + UFBA-425           (additive -- the aspect-distorted corpus)

Every hyperparameter below is copied verbatim from `train_multicorpus_detector.py` (Lever 1),
which copied `train_yolo_seg.py`, which reproduces the canonical bbox run's `train_args.yaml`.
The ONLY things that vary between arms: the `train:` list, and nothing else. `yolo11l.pt` (detect)
is forced for all -- DENTEX/Kaggle carry no polygons.

The train list is one of the balanced `train*.txt` files the builder wrote (verified 2 Sep that
ultralytics 8.4.127 keeps duplicate paths -> the per-corpus balancing is real). val is the frozen
Tufts val dir; test is `test_tufts.txt` (150 Tufts test images) -- the pre-registered Guard 2.

data_<arm>.yaml is written at runtime from the resolved dataset path, so the "fix the absolute
path on the rented box" step cannot be forgotten.

Usage (on the GPU box, from data/detector_multicorpus_v2's parent or with --data-root):
    python train_multicorpus_detector_v2.py --arm controlB
    python train_multicorpus_detector_v2.py --arm arm3c
    python train_multicorpus_detector_v2.py --arm arm4c
"""

import argparse
from pathlib import Path

ARM_TRAIN = {"controlB": "train_tufts.txt", "arm3c": "train_3corpus.txt", "arm4c": "train.txt"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=list(ARM_TRAIN), required=True)
    ap.add_argument("--data-root", type=Path, default=Path("detector_multicorpus_v2"))
    ap.add_argument("--project", type=Path, default=Path("runs_leverA"))
    args = ap.parse_args()

    import torch
    from ultralytics import YOLO

    root = args.data_root.resolve()
    train_list = root / ARM_TRAIN[args.arm]
    for p in (root / "images/val", train_list, root / "test_tufts.txt"):
        if not p.exists():
            raise SystemExit(f"missing: {p}")

    n_train = sum(1 for _ in open(train_list))
    n_val = len(list((root / "images/val").iterdir()))
    n_test = sum(1 for _ in open(root / "test_tufts.txt"))
    print(f"ARM={args.arm}  train={n_train} lines ({train_list.name})  val={n_val}  test={n_test}")
    if n_val != 150 or n_test != 150:
        raise SystemExit(f"val/test must be 150/150 Tufts, got {n_val}/{n_test}")
    expect = {"controlB": 700, "arm3c": 2100, "arm4c": 2800}[args.arm]
    if n_train != expect:
        raise SystemExit(f"{args.arm} train list has {n_train} lines, expected {expect}")

    yaml_path = root / f"data_{args.arm}.yaml"
    yaml_path.write_text(
        f"# Lever A, arm={args.arm}. Written at runtime from the resolved path.\n"
        f"path: {root}\ntrain: {train_list.name}\nval: images/val\ntest: test_tufts.txt\n\n"
        f"nc: 1\nnames: ['tooth']\n")
    print(f"wrote {yaml_path}")

    if not torch.cuda.is_available():
        raise SystemExit("no CUDA device -- refusing to train on CPU")
    p = torch.cuda.get_device_properties(0)
    print(f"GPU: {p.name} ({p.total_memory / 1e9:.1f} GB)")

    model = YOLO("yolo11l.pt")
    results = model.train(
        data=str(yaml_path),
        project=str(args.project),
        name=args.arm,
        exist_ok=False,

        # --- identical to train_multicorpus_detector.py / train_yolo_seg.py / the canonical run ---
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

    # --- Guard 2 immediately, same box/env, on best.pt: Tufts frozen TEST box mAP@0.5 ---
    best = Path(results.save_dir) / "weights" / "best.pt"
    print(f"\n=== ARM {args.arm}: Tufts frozen test (Guard 2) on {best} ===")
    m = YOLO(str(best)).val(data=str(yaml_path), split="test",
                            project=str(args.project), name=f"{args.arm}_test_tufts")
    print(f"ARM {args.arm}  Tufts TEST  box mAP@0.5 = {m.box.map50:.4f}   "
          f"mAP@0.5:0.95 = {m.box.map:.4f}   P = {m.box.mp:.4f}  R = {m.box.mr:.4f}")
    print(f"ARM {args.arm} DONE  ({best})")


if __name__ == "__main__":
    main()
