#!/usr/bin/env python
"""Train the Lever-B B-pooled caries-lesion detector (YOLOv11l, detect).

Pre-registration: outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md Sec 3, Sec 9 (amended
4 Sep 2026).

Every hyperparameter is copied from `train_cariesxrays_detector.py` (Lever 2 / B-single's own
recipe, itself copied from `train_multicorpus_detector.py`), so this trains a detector the way
this project already does. The ONLY deliberate differences: the TRAIN set is the per-corpus
BALANCED pool (`data/lever_b_pooled/train_pooled.txt`, built by
`build_lever_b_pooled_dataset.py` -- CariesXrays 4,800 + DENTEX-caries replicated to 4,800 =
9,600 lines/epoch, not a single corpus), val stays CariesXrays-only (1,200, unreplicated -- same
split B-single already used for early stopping, see the pool-builder's docstring).

`data.yaml`'s `path:` is a placeholder written by the pool builder (`__SET_AT_RUNTIME__`) and is
REWRITTEN HERE from `--data-root`, resolved on whatever machine is training -- so "fix the
absolute path on the rented box" is one flag, not a manual edit (the friction point
`train_cariesxrays_detector.py`'s own docstring flags).

BATCH SIZE DEFAULTS TO 16, NOT 32 -- LEARNED FROM B-SINGLE'S OWN RUN, NOT GUESSED
------------------------------------------------------------------------------------
Lever 2 (B-single, this exact model/resolution/dataset scale) hit CUDA OOM at batch=32 on an
A100-40GB and fell back to batch=16 (RESULTS_LOG.md 2026-09-02b) -- that IS the recipe that
produced the frozen 0.482 AP checkpoint, not a batch=32 run. Per-step VRAM depends on batch size
and image resolution, not on dataset length, so B-pooled's larger (9,600 vs 4,800 images/epoch)
but same-batch training has the same per-step footprint and would hit the identical OOM at 32.
Defaulting to 16 both avoids repeating a known failure on a billed instance and keeps B-pooled's
realised recipe identical to B-single's realised recipe (not just its nominal pre-fallback one)
-- the comparison this whole lever rests on is "same recipe, different training data".

Usage (on the GPU box, after the geometry gate re-passes there):
    python train_lever_b_pooled_detector.py --data-root .
"""

import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("."),
                    help="parent directory containing cariesxrays_det/, dentex_caries_det/ and "
                         "lever_b_pooled/ as siblings (matches this repo's data/ layout)")
    ap.add_argument("--project", type=Path, default=Path("runs_lever_b"))
    ap.add_argument("--name", default="lever_b_pooled_yolo11l")
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--batch", type=int, default=16,
                    help="B-single's realised batch after its own OOM fallback at 32 on an "
                         "A100-40GB, 1024px (RESULTS_LOG.md 2026-09-02b) -- not a guess")
    args = ap.parse_args()

    import torch
    from ultralytics import YOLO

    root = args.data_root.resolve()
    pooled_dir = root / "lever_b_pooled"
    cx_dir = root / "cariesxrays_det"
    dx_dir = root / "dentex_caries_det"
    for p in (pooled_dir / "train_pooled.txt", cx_dir / "images/val", dx_dir / "images/train"):
        if not p.exists():
            raise SystemExit(f"dataset incomplete: missing {p}")

    train_lines = (pooled_dir / "train_pooled.txt").read_text().splitlines()
    n_val = len(list((cx_dir / "images/val").iterdir()))
    print(f"pooled train lines={len(train_lines)}  cariesxrays val images={n_val}")
    if len(train_lines) != 9600:
        raise SystemExit(f"expected 9,600 balanced train lines (4,800 CariesXrays + 4,800 "
                         f"replicated DENTEX-caries, PRE_REGISTRATION.md Sec 9), got "
                         f"{len(train_lines)} -- rebuild with build_lever_b_pooled_dataset.py "
                         f"before training on a stale or partial pool")
    if n_val != 1200:
        raise SystemExit(f"expected 1,200 CariesXrays val images (this project's seed-42 split, "
                         f"unreplicated -- also Lever B's frozen eval cohort), got {n_val}")

    # ultralytics' get_img_files() only rewrites a line starting with "./" (substituting the
    # TXT FILE'S OWN parent dir); a bare relative line like "cariesxrays_det/images/train/x.jpg"
    # is used as-is, resolved against the training PROCESS'S CWD -- not against data.yaml's
    # `path:`, and not against the txt file's location either. Verified against
    # ultralytics/data/base.py's get_img_files source directly (not assumed) after it crashed
    # with "No labels found" on the first launch attempt. Fix: rewrite the list to ABSOLUTE
    # paths here, at train time, from the already-resolved `root` -- same "resolve at runtime,
    # never bake in a host path at build time" principle this script already applies to
    # data.yaml's `path:` field, just extended to the file list too.
    resolved_path = pooled_dir / "train_pooled_resolved.txt"
    resolved_path.write_text("\n".join(str(root / line) for line in train_lines) + "\n")
    print(f"wrote {resolved_path} (absolute paths, {len(train_lines)} lines)")

    yaml_path = pooled_dir / "data_lever_b.yaml"
    yaml_path.write_text(
        "# Lever B B-pooled -- CariesXrays + DENTEX caries boxes, per-corpus balanced 1.00x\n"
        "# path:/train: written at runtime by train_lever_b_pooled_detector.py from --data-root\n"
        "# train: points at the ABSOLUTE-path-rewritten list (see train_pooled_resolved.txt "
        "note above) -- a plain relative txt-file list resolves against the training "
        "process's CWD in ultralytics, not against `path:` (verified against "
        "ultralytics/data/base.py get_img_files).\n"
        f"path: {root}\ntrain: {resolved_path}\nval: cariesxrays_det/images/val\n\n"
        "nc: 1\nnames: ['decay']\n")
    print(f"wrote {yaml_path}  path={root}  train={resolved_path}")

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

        # --- identical to train_cariesxrays_detector.py (Lever 2 / B-single's proven recipe),
        #     except the train set is the balanced pool (this file's whole point) ---
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

    # COCO AP on the CariesXrays val split -- reported alongside the tooth-level frozen eval
    # (Sec 4/6), NOT a substitute for it. Comparable to B-single's own val-split AP.
    print("\n=== FINAL VAL (COCO AP, CariesXrays val split) ===")
    m = model.val(data=str(yaml_path), split="val", imgsz=1024, iou=0.5, conf=0.001,
                  project=str(args.project), name=args.name + "_val", plots=True)
    print(f"AP@[.5:.95] = {m.box.map:.4f}")
    print(f"AP50        = {m.box.map50:.4f}")
    print(f"AP75        = {m.box.map75:.4f}")
    print("LEVER B B-POOLED DONE")


if __name__ == "__main__":
    main()
