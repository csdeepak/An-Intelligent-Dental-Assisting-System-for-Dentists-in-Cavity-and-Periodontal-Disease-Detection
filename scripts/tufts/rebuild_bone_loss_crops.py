#!/usr/bin/env python
"""
Regenerate the bone-loss VALIDATION crops from Tufts source, with the geometry verified.

WHY THIS EXISTS
---------------
`models/03_bone_loss_model_training_notebook_models/` ships a model but this machine has only
`data/tufts/resampled_dataset/metadata/*.csv` -- `filename,label,stem` and no pixels. Without
crops there is no calibration analysis, no confidence interval and no crop-geometry ablation for
the bone-loss branch, which is why three items in `PAPER_MATERIAL.md` §9 are stuck.

WHAT CAN AND CANNOT BE REPRODUCED -- read this before quoting anything built here
---------------------------------------------------------------------------------
**49.6% of the val rows (773 of 1,558) are jittered** -- filenames carry `_jit_`, and §6.5's
±15% coordinate jitter was applied at dataset-construction time with **offsets that were never
saved**. Those crops are therefore *irreproducible by construction*: the pixels depended on draws
from an unrecorded RNG.

So this script rebuilds only the **785 deterministic, non-jittered val crops** (750 normal /
35 diseased) straight from `teeth_bbox.json` with the documented 1.5x/2.0x expansion. Anything
measured on them is a **new measurement on a clean subset**, NOT a reproduction of the reported
0.9233 macro-F1 -- that number was computed on the full 1,558 including jittered crops and cannot
be recomputed here. Saying otherwise would be comparing two different sets.

GEOMETRY IS MEASURED, NOT ASSUMED
----------------------------------
The Tufts radiographs exist in two orientations on this machine (`Radiographs_rotated` and
`Radiographs_rotated_fixed`, after the 180° defect found on 27 Aug), and a silent orientation
error is exactly what voided the R1 run. The correct directory is therefore chosen by
`scripts/yolo/_tufts_align.pick_image_dir`, which *measures* each candidate against
`teeth_bbox.json` rather than trusting its name.

Usage:
    python scripts/tufts/rebuild_bone_loss_crops.py
    python scripts/tufts/rebuild_bone_loss_crops.py --split val --limit 50
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "yolo"))

DEF_ZIP = REPO_ROOT / "data/tufts/ZIP"
DEF_META = REPO_ROOT / "data/tufts/resampled_dataset/metadata"
DEF_OUT = REPO_ROOT / "data/tufts/bone_loss_crops_rebuilt"

# Tooth ids are Universal numbering: 1-32 for permanent teeth AND A-T for DECIDUOUS ones.
# A digits-only pattern rejected 49 val rows (TA, TC, TH, TK ...) which are perfectly valid
# primary teeth -- verified against teeth_bbox.json, whose title vocabulary is exactly
# 32 numeric + 20 lettered. The guard refusing to guess is what surfaced this.
NAME_RE = re.compile(r"^(?P<stem>\d+)_T(?P<tooth>[0-9A-Z]+)(?P<jit>_jit)?_(?P<uid>\d+)\.png$")


def rotate_image_and_boxes(img, boxes, direction):
    """Rotate an image 90 degrees and carry its boxes into the new frame.

    Returns (img, {title: [x1, y1, x2, y2]}). `boxes` maps title -> box in the ORIGINAL frame.
    Rotating the pixels without rotating the boxes is the classic silent failure here, so the
    two are deliberately done by one function that cannot do one without the other.
    """
    import cv2
    if direction == "none":
        return img, boxes
    H, W = img.shape[:2]
    if direction == "cw":
        out = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        # (x, y) -> (H - 1 - y, x)
        conv = lambda b: [H - 1 - b[3], b[0], H - 1 - b[1], b[2]]
    else:
        out = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # (x, y) -> (y, W - 1 - x)
        conv = lambda b: [b[1], W - 1 - b[2], b[3], W - 1 - b[0]]
    return out, {t: conv(b) for t, b in boxes.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip-root", type=Path, default=DEF_ZIP)
    ap.add_argument("--meta", type=Path, default=DEF_META)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--split", default="val")
    ap.add_argument("--limit", type=int, default=None)
    # The Tufts radiographs on disk are the OPG turned 90 degrees (840x1615 portrait), and
    # teeth_bbox.json is in that same frame -- so crops land on the right teeth but LYING
    # SIDEWAYS. The bone-loss model was trained on upright teeth, and the 1.5xW/2.0xH expansion
    # assumes a tooth ~3x taller than wide, so in the portrait frame it expands along the wrong
    # axes. _tufts_align.pick_image_dir only distinguishes 180 degrees, not 90, which is why it
    # passed. Rotating the image AND the boxes together fixes both problems at once.
    ap.add_argument("--rotate", choices=["none", "cw", "ccw"], default="none",
                    help="rotate image and boxes into the upright-tooth frame")
    args = ap.parse_args()

    import cv2
    import pandas as pd

    from _tufts_align import pick_image_dir
    from src.crop_generator import compute_expanded_bbox

    bbox_json = next(args.zip_root.rglob("teeth_bbox.json"))
    print(f"bbox annotations: {bbox_json}")

    candidates = [d for d in (args.zip_root / "Radiographs_rotated",
                              args.zip_root / "Radiographs_rotated_fixed") if d.exists()]
    if not candidates:
        raise SystemExit("no radiograph directory found under the ZIP root")
    print("choosing the correctly-oriented radiographs BY MEASUREMENT, not by name …")
    picked = pick_image_dir(candidates, bbox_json)
    # pick_image_dir returns (path, score, per-candidate detail lines), not a bare path.
    img_dir, align_score, align_detail = picked if isinstance(picked, tuple) else (picked, None, [])
    for line in align_detail:
        print(line)
    print(f"  -> {img_dir}" + (f"  (alignment score {align_score:.3f})" if align_score else ""))

    entries = json.loads(Path(bbox_json).read_text(encoding="utf-8"))
    by_stem = {}
    for e in entries:
        stem = Path(e["External ID"]).stem
        by_stem[stem] = {o["title"]: o["bounding box"] for o in e["Label"]["objects"]}
    print(f"  {len(by_stem)} annotated images indexed")

    meta = pd.read_csv(args.meta / ("val_metadata.csv" if args.split == "val"
                                    else "train_resampled_metadata.csv"))
    parsed = meta["filename"].str.extract(NAME_RE)
    meta = meta.assign(tooth=parsed["tooth"], jit=parsed["jit"].notna())
    bad = meta["tooth"].isna().sum()
    if bad:
        raise SystemExit(f"{bad} filenames did not parse -- refusing to guess")

    clean = meta[~meta["jit"]].reset_index(drop=True)
    print(f"\n{args.split}: {len(meta)} rows, {int(meta['jit'].sum())} jittered "
          f"({meta['jit'].mean():.1%}) -- IRREPRODUCIBLE, offsets never saved")
    print(f"  rebuilding the {len(clean)} deterministic rows "
          f"({dict(clean['label'].value_counts())})")
    if args.limit:
        clean = clean.head(args.limit)

    out_root = args.out / args.split if args.rotate == "none" \
        else args.out / f"{args.split}_{args.rotate}"
    for lab in ("0", "1"):
        (out_root / lab).mkdir(parents=True, exist_ok=True)

    written = missing_img = missing_box = 0
    rows = []
    for _, r in clean.iterrows():
        stem, tooth = str(r["stem"]), str(r["tooth"])
        boxes = by_stem.get(stem)
        if boxes is None or tooth not in boxes:
            missing_box += 1
            continue
        ip = img_dir / f"{stem}.jpg"
        if not ip.exists():
            ip = img_dir / f"{stem}.JPG"
        if not ip.exists():
            missing_img += 1
            continue
        img = cv2.imread(str(ip), cv2.IMREAD_COLOR)
        if img is None:
            missing_img += 1
            continue
        img, boxes_r = rotate_image_and_boxes(img, boxes, args.rotate)
        H, W = img.shape[:2]
        x1, y1, x2, y2 = boxes_r[tooth]
        cx1, cy1, cx2, cy2 = compute_expanded_bbox(x1, y1, x2 - x1, y2 - y1, W, H, 1.5, 2.0)
        crop = img[cy1:cy2, cx1:cx2]
        if crop.size == 0:
            missing_box += 1
            continue
        crop = cv2.resize(crop, (224, 224), interpolation=cv2.INTER_LINEAR)
        dst = out_root / str(r["label"]) / r["filename"]
        cv2.imwrite(str(dst), crop)
        rows.append({"filename": r["filename"], "label": int(r["label"]), "stem": stem,
                     "tooth": tooth, "path": str(dst.relative_to(REPO_ROOT))})
        written += 1

    print(f"\n  written {written}   missing image {missing_img}   missing/empty box {missing_box}")
    man = (args.out / f"manifest_{args.split}.csv" if args.rotate == "none"
           else args.out / f"manifest_{args.split}_{args.rotate}.csv")
    pd.DataFrame(rows).to_csv(man, index=False)
    print(f"  manifest -> {man}")
    print("\nREMINDER: this is the NON-JITTERED subset. Any metric measured on it is a new"
          "\nmeasurement on a clean subset, not a reproduction of the reported 0.9233 macro-F1,"
          "\nwhich was computed over all 1,558 val crops including irreproducible jittered ones.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
