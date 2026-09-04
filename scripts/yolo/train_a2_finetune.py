#!/usr/bin/env python
"""Lever A2 — fine-tune the Lever A 3-corpus detector on Tufts-only, backbone frozen.

Pre-registration: outputs/lever_A2_detector_finetune/PRE_REGISTRATION.md

Loads models/15_detector_multicorpus_leverA/arm3c_best.pt (the frozen 3-corpus Lever A
checkpoint), freezes the backbone (freeze=11), and fine-tunes the neck + detection head on
`train_tufts.txt` (700 Tufts images) for 40 epochs. Hypothesis: re-specialise the Tufts
confidence distribution (Phase 0 diagnosed a calibration collapse) while the frozen backbone
keeps the DENTEX / external-cohort gains.

Every hyperparameter is byte-identical to train_multicorpus_detector_v2.py EXCEPT the four
recorded in PRE_REGISTRATION.md §3: freeze=11, epochs=40, patience=12, warmup_epochs=1.
freeze=11 freezes YOLOv11l layers 0-10 (full backbone, 50.7% of params); neck 11-22 + Detect
head 23 train (verified locally on arm3c_best.pt).

Usage (on the GPU box, from data/detector_multicorpus_v2's parent or with --data-root):
    python train_a2_finetune.py --weights /home/arm3c_best.pt --data-root /home/detector_multicorpus_v2
"""

import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", type=Path, required=True,
                    help="models/15_detector_multicorpus_leverA/arm3c_best.pt (sha256 5d301f13...)")
    ap.add_argument("--data-root", type=Path, default=Path("detector_multicorpus_v2"))
    ap.add_argument("--project", type=Path, default=Path("runs_leverA2"))
    args = ap.parse_args()

    import hashlib

    import torch
    from ultralytics import YOLO

    EXPECT_SHA = "5d301f13fb48da5c74e7ef01bd0f91226f9b6800cb433dee5aebc8f8db8f161e"
    got = hashlib.sha256(args.weights.read_bytes()).hexdigest()
    if not got.startswith(EXPECT_SHA):
        raise SystemExit(f"weights sha256 {got} != expected {EXPECT_SHA} (arm3c_best.pt)")

    root = args.data_root.resolve()
    train_list = root / "train_tufts.txt"
    for p in (root / "images/val", train_list, root / "test_tufts.txt"):
        if not p.exists():
            raise SystemExit(f"missing: {p}")

    n_train = sum(1 for _ in open(train_list))
    n_val = len(list((root / "images/val").iterdir()))
    n_test = sum(1 for _ in open(root / "test_tufts.txt"))
    print(f"A2  train={n_train} lines (train_tufts.txt)  val={n_val}  test={n_test}")
    if (n_train, n_val, n_test) != (700, 150, 150):
        raise SystemExit(f"expected 700/150/150, got {n_train}/{n_val}/{n_test}")

    yaml_path = root / "data_a2.yaml"
    yaml_path.write_text(
        "# Lever A2. Written at runtime from the resolved path.\n"
        f"path: {root}\ntrain: train_tufts.txt\nval: images/val\ntest: test_tufts.txt\n\n"
        "nc: 1\nnames: ['tooth']\n")
    print(f"wrote {yaml_path}")

    if not torch.cuda.is_available():
        raise SystemExit("no CUDA device -- refusing to train on CPU")
    gp = torch.cuda.get_device_properties(0)
    print(f"GPU: {gp.name} ({gp.total_memory / 1e9:.1f} GB)")

    model = YOLO(str(args.weights))
    results = model.train(
        data=str(yaml_path),
        project=str(args.project),
        name="a2",
        exist_ok=False,

        # --- the four knobs recorded in PRE_REGISTRATION.md §3 ---
        freeze=11,
        epochs=40,
        patience=12,
        warmup_epochs=1,

        # --- identical to train_multicorpus_detector_v2.py ---
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
        cos_lr=True,

        box=7.5, cls=0.5, dfl=1.5,

        hsv_h=0.0, hsv_s=0.0, hsv_v=0.2,
        degrees=10.0, translate=0.1, scale=0.2,
        shear=0.0, perspective=0.0,
        fliplr=0.5,
        flipud=0.0,
        mosaic=0.0,
        mixup=0.0, copy_paste=0.0,

        save=True, save_period=-1, plots=True,
    )

    # --- Guard 2 immediately, same box/env, on best.pt: Tufts frozen TEST box mAP@0.5 ---
    best = Path(results.save_dir) / "weights" / "best.pt"
    print(f"\n=== A2: Tufts frozen test (Guard 2) on {best} ===")
    m = YOLO(str(best)).val(data=str(yaml_path), split="test",
                            project=str(args.project), name="a2_test_tufts")
    print(f"A2  Tufts TEST  box mAP@0.5 = {m.box.map50:.4f}   "
          f"mAP@0.5:0.95 = {m.box.map:.4f}   P = {m.box.mp:.4f}  R = {m.box.mr:.4f}")
    print(f"A2 DONE  ({best})")


if __name__ == "__main__":
    main()
