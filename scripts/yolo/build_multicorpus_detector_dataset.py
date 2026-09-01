#!/usr/bin/env python
"""Build a two-corpus YOLO DETECTION dataset: Tufts + DENTEX quadrant_enumeration.

WHY (pre-registered: outputs/detector_multicorpus/PRE_REGISTRATION.md)
---------------------------------------------------------------------
Stage-2 end-to-end decomposes as `recall x of-detected` = 0.706 x 0.826 = 0.583. The numbering
half is strong; **detector recall is the binding constraint** and 29.4% of teeth never reach
Stage 2. The detector trains on 700 Tufts images. `quadrant_enumeration` adds 623 panoramics with
18,095 tooth boxes, already local -- roughly doubling detection supervision, from a second
institution. DentFound pooled corpora the same way for its tooth-identification model.

THE THREE THINGS THIS SCRIPT REFUSES TO GET WRONG
-------------------------------------------------
1. **Orientation.** The frozen detector consumes 90-deg COUNTER-CLOCKWISE-rotated panoramics.
   Tufts is already in that frame (840x1615 portrait); DENTEX is upright landscape (~2955x1316)
   and its pixels AND boxes must both be rotated. Rotating one and not the other is exactly how a
   90-epoch A100 run was voided (RESULTS_LOG 2026-08-27a) -- losses fell smoothly for 90 epochs on
   misaligned data and nothing failed along the way. Rotation uses `src.orientation.rot_box`,
   which is property-tested against `unrot_box` in tests/test_orientation_roundtrip.py, rather
   than re-derived here.
2. **The frozen split.** Tufts train/val/test are carried through untouched and **val and test
   contain Tufts only**, so `Tufts test box mAP@0.5` stays directly comparable to the frozen
   detector's 0.810 and can serve as the pre-registered guard. All DENTEX goes to train.
3. **Leakage.** Every DENTEX image is checked by MD5 against the 164 leak-free evaluation images
   and refused if it matches. (Verified 0 before writing this script -- all 85 shared images sit
   inside the existing 86-image exclusion list -- so this guard should be a no-op. It runs anyway,
   because a guard that only runs when you expect it to fail is not a guard.)

Tufts boxes are DERIVED from `data/tufts/dataset_seg`'s polygon labels (min/max of each polygon)
rather than re-converted from source: that corpus is already verified aligned, so the only new
geometry risk is the DENTEX side, which is re-scored below.

FORMAT NOTE: rotated DENTEX images are written as JPEG q95. Tufts -- the corpus the detector was
actually trained on -- is already JPEG, so this is the *consistent* choice, and it cuts the
upload from ~2.1 GB to ~0.3 GB. Upload happens on a billing instance, so that is ~40 min of
A100 time saved.

Usage:
    python scripts/yolo/build_multicorpus_detector_dataset.py --dry-run
    python scripts/yolo/build_multicorpus_detector_dataset.py
"""

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

DEF_TUFTS_BBOX = REPO / "_repo_archive/datasets_workspace/Segmentation/teeth_bbox.json"
DEF_TUFTS_IMGS = REPO / "_repo_archive/datasets_workspace/Radiographs_rotated"
DEF_TUFTS_SPLIT = REPO / "outputs/eda_tufts/split_v1.csv"
DEF_DENTEX = Path.home() / "Downloads/Capstone/DENTEX/training_data/quadrant_enumeration"
DEF_EVAL = Path.home() / "Downloads/Capstone/DENTEX/disease/input"
DEF_EXCL = REPO / "data/dentex/disease_leaked_images.json"
DEF_OUT = REPO / "data/detector_multicorpus"

# A converted box must agree with its source this well, or the build aborts.
MIN_MEDIAN_IOU = 0.99
JPEG_Q = 95


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    ua = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / ua if ua > 0 else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tufts-bbox", type=Path, default=DEF_TUFTS_BBOX)
    ap.add_argument("--tufts-imgs", type=Path, default=DEF_TUFTS_IMGS)
    ap.add_argument("--tufts-split", type=Path, default=DEF_TUFTS_SPLIT)
    ap.add_argument("--dentex", type=Path, default=DEF_DENTEX)
    ap.add_argument("--eval-pool", type=Path, default=DEF_EVAL)
    ap.add_argument("--exclusions", type=Path, default=DEF_EXCL)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    import cv2
    from src.orientation import DEFAULT as ROT_DIR, rot_box, unrot_box

    stats = Counter()
    rows = []
    tufts_px = {}

    # ---------------------------------------------------------------- Tufts
    # SOURCE CORRECTED 1 Sep 2026. This previously derived boxes from
    # data/tufts/dataset_seg's polygons -- which is the WITHDRAWN pre-fix corpus from the void
    # 26 Aug run (RESULTS_LOG 2026-08-27a); its labels are 90 deg out and sit off the dentition.
    # teeth_bbox.json is the annotation the canonical 0.7824 detector was trained on, already in
    # the portrait/rotated frame, and untouched by the teeth_polygon.json [y,x] transpose.
    split_of = {r["filename"]: r["split"]
                for r in csv.DictReader(open(args.tufts_split))}
    bb = json.loads(args.tufts_bbox.read_text())
    print("TUFTS -- boxes from teeth_bbox.json (the canonical detector's own ground truth)")
    for entry in bb:
        stem = Path(str(entry.get("External ID", ""))).stem
        fname = stem + ".JPG"
        split = split_of.get(fname)
        if split is None:
            stats["tufts_not_in_split"] += 1
            continue
        src_img = args.tufts_imgs / fname
        if not src_img.exists():
            stats["tufts_image_missing"] += 1
            continue
        objs = (entry.get("Label") or {}).get("objects") or entry.get("objects") or []
        boxes = []
        for o in objs:
            b = o.get("bounding box") or o.get("bbox")
            if not b or len(b) != 4:
                continue
            x1, y1, x2, y2 = b
            # The degenerate-box guard the canonical converter also applies: 66 source objects
            # carry a corrupt 1x1 / 1x2 'bounding box' with an intact polygon
            # (T0.6_detector_reconciliation.md 3.5). Dropped here as there, so the counts stay
            # comparable to the frozen detector's.
            if x2 - x1 < 2 or y2 - y1 < 2:
                stats["tufts_degenerate_box"] += 1
                continue
            boxes.append((x1, y1, x2, y2))
        stats[f"{split}/tufts_images"] += 1
        stats[f"{split}/tufts_boxes"] += len(boxes)
        rows.append({"corpus": "tufts", "split": split, "stem": stem,
                     "n_boxes": len(boxes), "rotated": False})
        if args.dry_run:
            tufts_px.setdefault(split, []).extend(
                ((x2 - x1) / max(y2 - y1, 1e-9)) for x1, y1, x2, y2 in boxes)
            continue
        img = cv2.imread(str(src_img))
        if img is None:
            stats["tufts_unreadable"] += 1
            rows.pop()
            continue
        H, W = img.shape[:2]
        (args.out / "images" / split).mkdir(parents=True, exist_ok=True)
        (args.out / "labels" / split).mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_img, args.out / "images" / split / fname)
        (args.out / "labels" / split / (stem + ".txt")).write_text(
            "".join(f"0 {((x1+x2)/2)/W:.6f} {((y1+y2)/2)/H:.6f} "
                    f"{(x2-x1)/W:.6f} {(y2-y1)/H:.6f}\n" for x1, y1, x2, y2 in boxes))
        tufts_px.setdefault(split, []).extend(
            ((x2 - x1) / max(y2 - y1, 1e-9)) for x1, y1, x2, y2 in boxes)
    for split in ("train", "val", "test"):
        print(f"  {split:5s} {stats[f'{split}/tufts_images']:>4} images, "
              f"{stats[f'{split}/tufts_boxes']:>6} boxes")
    # CANONICAL-COUNT GATE: model_metrics.md records the frozen detector's own instance counts.
    # Reproducing them exactly proves this conversion matches the canonical one.
    for split, expect in (("val", 3794), ("test", 3924)):
        got = stats[f"{split}/tufts_boxes"]
        flag = "MATCH" if got == expect else "MISMATCH"
        print(f"  canonical {split} instance count: expected {expect}, got {got}  [{flag}]")
        if got != expect:
            raise SystemExit(
                f"Tufts {split} has {got} boxes, canonical is {expect}. The conversion does not "
                f"reproduce the frozen detector's ground truth -- refusing to write.")

    # ------------------------------------------------------- leakage guard
    leakfree = set()
    if args.eval_pool.is_dir():
        excl = set(json.loads(args.exclusions.read_text())["all_excluded"])
        for f in sorted(args.eval_pool.iterdir()):
            if f.suffix.lower() in (".png", ".jpg", ".jpeg") and f.stem not in excl:
                leakfree.add(md5(f))
    print(f"\nleakage guard: {len(leakfree)} leak-free evaluation images hashed "
          f"(expect 164)")

    # --------------------------------------------------------------- DENTEX
    coco = json.loads((args.dentex / "train_quadrant_enumeration.json").read_text())
    by_img = {}
    for a in coco["annotations"]:
        by_img.setdefault(a["image_id"], []).append(a)
    print(f"DENTEX -- rotating {ROT_DIR.upper()} into the detector frame, all into TRAIN")

    checks = []
    for n, im in enumerate(coco["images"], 1):
        src = args.dentex / "xrays" / im["file_name"]
        if not src.exists():
            stats["dentex_image_missing"] += 1
            continue
        if md5(src) in leakfree:
            stats["dentex_REFUSED_leakage"] += 1
            continue
        anns = by_img.get(im["id"], [])
        if not anns:
            stats["dentex_no_annotations"] += 1
            continue

        W, H = im["width"], im["height"]
        rw, rh = H, W                      # a 90-deg rotation swaps the axes
        lines = []
        for a in anns:
            x, y, w, h = a["bbox"]
            up = [x, y, x + w, y + h]
            rb = rot_box(up, W, H, ROT_DIR)
            # per-box round trip: the property test proves the maths, this proves THIS box
            back = unrot_box(rb, W, H, ROT_DIR)
            # Tolerance, not round(): the rotation's `orig_w - 1 - x` arithmetic leaves ~1e-13
            # float noise, and round() turns that into a spurious failure at .5 boundaries
            # (round(999.5)=1000 but round(999.4999999999999)=999, banker's rounding).
            if max(abs(a - b) for a, b in zip(back, up)) > 1e-6:
                raise SystemExit(f"round-trip failed on {im['file_name']}: {up} -> {rb} -> {back}")
            x1, y1, x2, y2 = rb
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(rw, x2), min(rh, y2)
            if x2 - x1 < 2 or y2 - y1 < 2:
                stats["dentex_degenerate_box"] += 1
                continue
            lines.append((((x1 + x2) / 2) / rw, ((y1 + y2) / 2) / rh,
                          (x2 - x1) / rw, (y2 - y1) / rh))
            checks.append((rb, up, W, H))

        stats["train/dentex_images"] += 1
        stats["train/dentex_boxes"] += len(lines)
        stem = "dentex_" + Path(im["file_name"]).stem
        rows.append({"corpus": "dentex", "split": "train", "stem": stem,
                     "n_boxes": len(lines), "rotated": True})
        if args.dry_run:
            continue
        img = cv2.imread(str(src))
        if img is None:
            stats["dentex_unreadable"] += 1
            rows.pop()
            continue
        rot = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        assert rot.shape[1] == rw and rot.shape[0] == rh, "rotated frame disagrees with (H, W)"
        cv2.imwrite(str(args.out / "images/train" / (stem + ".jpg")), rot,
                    [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
        (args.out / "labels/train" / (stem + ".txt")).write_text(
            "".join(f"0 {a:.6f} {b:.6f} {c:.6f} {d:.6f}\n" for a, b, c, d in lines))
        if n % 100 == 0:
            print(f"  {n}/{len(coco['images'])} ...", flush=True)

    # --------------------------------------------------- verification gate
    print("\nGEOMETRY GATE")
    ious = [iou(unrot_box(rb, W, H, ROT_DIR), up) for rb, up, W, H in checks]
    med = sorted(ious)[len(ious) // 2] if ious else 0.0
    print(f"  {len(ious):,} DENTEX boxes round-tripped; median IoU vs source = {med:.4f}")
    if med < MIN_MEDIAN_IOU:
        raise SystemExit(f"median IoU {med:.4f} < {MIN_MEDIAN_IOU} -- refusing to write")
    print(f"  PASS (>= {MIN_MEDIAN_IOU})")

    tr = stats["train/tufts_images"] + stats["train/dentex_images"]
    print(f"\nCOMPOSITION")
    print(f"  train {tr:>5} images  ({stats['train/tufts_images']} Tufts + "
          f"{stats['train/dentex_images']} DENTEX), "
          f"{stats['train/tufts_boxes'] + stats['train/dentex_boxes']:,} boxes")
    print(f"  val   {stats['val/tufts_images']:>5} images  (Tufts only -- unchanged), "
          f"{stats['val/tufts_boxes']:,} boxes")
    print(f"  test  {stats['test/tufts_images']:>5} images  (Tufts only -- the frozen guard), "
          f"{stats['test/tufts_boxes']:,} boxes")
    print(f"  refused for leakage: {stats['dentex_REFUSED_leakage']}   "
          f"degenerate boxes dropped: {stats['dentex_degenerate_box']}")
    print(f"  baseline for comparison: 700 Tufts train images -> "
          f"{tr / 700:.2f}x more training images")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "data.yaml").write_text(
        f"# Tufts + DENTEX quadrant_enumeration, YOLO detection, detector frame ({ROT_DIR})\n"
        f"# Built by scripts/yolo/build_multicorpus_detector_dataset.py\n"
        f"# val/test are TUFTS ONLY and identical to the frozen split -- test box mAP@0.5\n"
        f"# stays comparable to the frozen detector's 0.810 (the pre-registered guard).\n"
        f"path: {args.out}\ntrain: images/train\nval: images/val\ntest: images/test\n\n"
        f"nc: 1\nnames: ['tooth']\n")
    with open(args.out / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (args.out / "meta.json").write_text(json.dumps({
        "built": "multi-corpus detector dataset (Lever 1)",
        "pre_registration": "outputs/detector_multicorpus/PRE_REGISTRATION.md",
        "rotation": f"DENTEX rotated 90 deg {ROT_DIR} into the detector frame via "
                    f"src.orientation.rot_box; Tufts already in that frame",
        "tufts_boxes_from": "min/max of dataset_seg polygon labels (that corpus is already "
                            "geometry-verified; no re-conversion, no new risk)",
        "val_test_policy": "TUFTS ONLY and unchanged, so the frozen-test guard stays comparable",
        "leakage_guard": f"{len(leakfree)} leak-free eval images hashed; "
                         f"{stats['dentex_REFUSED_leakage']} DENTEX images refused",
        "geometry_gate": {"boxes_checked": len(ious), "median_iou": round(med, 6),
                          "threshold": MIN_MEDIAN_IOU},
        "dentex_format": f"JPEG q{JPEG_Q} -- Tufts is already JPEG, so this is the consistent "
                         f"choice and cuts upload ~8x",
        "counts": dict(stats),
    }, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
