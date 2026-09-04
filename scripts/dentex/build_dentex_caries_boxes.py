#!/usr/bin/env python
r"""Build a YOLO DETECTION dataset of DENTEX caries/deep-caries boxes (Lever B, domain adapter).

WHY (pre-registered: outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md Sec 3)
-----------------------------------------------------------------------------
B-pooled trains the lesion detector on CariesXrays (lesion boxes) + this DENTEX subset (TOOTH
boxes carrying a caries/deep_caries label) so the detector is not CariesXrays-domain-only. These
are coarser than lesion boxes -- recorded as expected, not a defect (Sec 3, Sec 7 risk 2).

SOURCE
------
`train_quadrant_enumeration_disease.json` -- 705 images, 650 with >=1 caries/deep_caries box,
2,767 such boxes (verified directly against the file, 4 Sep 2026). Category filter reuses
`CARIES_CLASSES = {1, 3}` from `build_dentex_crops.py` rather than redefining it -- same
constant, one place it could be wrong. Image dims come from the JSON `images` block (`width`/
`height`), not from decoding the image -- this is COCO JSON, not the CariesXrays VOC-XML with
the 27.3%-wrong `<size>` bug (PRE_REGISTRATION.md Sec 8.1 note); still cross-checked against the
decoded image below as a free assertion, because "trust the metadata" is exactly the class of
assumption that voided a 90-epoch run once (RESULTS_LOG 2026-08-27a).

LEAKAGE -- CHECKED DIRECTLY, NOT ASSUMED
-----------------------------------------
This corpus and the DENTEX `disease/` eval release (164 leak-free of 250, used by
`lesion_localization.py`) are BOTH DENTEX-native PNG releases and DO share at least one
byte-identical image: `disease/input/test_181.png` == `.../quadrant-enumeration-disease/xrays/
train_332.png` (MD5-verified 4 Sep 2026). `test_181` is already in
`data/dentex/disease_leaked_images.json`'s `all_excluded` (for an unrelated reason -- it also
leaked into the tooth detector's training data), so the CURRENT 164-image eval cohort is already
clean of it. This script re-verifies that fact live against the CURRENT leak-free eval list
(never hardcodes it) and refuses to write a training image that is byte-identical to any
currently-scored eval image, so the gate holds even if the eval exclusion list changes later.

OUTPUT
------
Single class **"decay"** (index 0) -- same name as `build_cariesxrays_detector_dataset.py`'s
class, on purpose: these boxes get pooled with CariesXrays' into one nc=1 detector. Every box
is tagged by source in `manifest.csv` (`src=dentex_qed`) so a later per-source ablation is
possible without re-deriving provenance.

Only images carrying >=1 caries/deep_caries box are written (650 of 705) -- this builds a caries
training pool, not a general DENTEX tooth detector.

GATE, before anything is written or uploaded (mirrors build_cariesxrays_detector_dataset.py):
  1. Every box round-trips: YOLO norm -> pixel -> matches source COCO xywh within 1 px.
  2. 0 normalised coords outside [0, 1].
  3. JSON `images` width/height == decoded image shape, every image (else abort).
  4. 0 MD5 overlap between written training images and the CURRENT DENTEX disease/ leak-free
     eval cohort (live-checked, see above).
  5. N rendered samples written to <out>/_check/ for eye inspection.

Usage:
    python scripts/dentex/build_dentex_caries_boxes.py --dry-run
    python scripts/dentex/build_dentex_caries_boxes.py
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "dentex"))

from build_dentex_crops import CARIES_CLASSES, DEEP_CARIES  # noqa: E402  -- reused, not redefined

DEF_JSON = Path.home() / "Downloads/Capstone/DENTEX/training_data/quadrant-enumeration-disease/train_quadrant_enumeration_disease.json"
DEF_XRAYS = Path.home() / "Downloads/Capstone/DENTEX/training_data/quadrant-enumeration-disease/xrays"
DEF_DISEASE_DIR = Path.home() / "Downloads/Capstone/DENTEX/disease"
DEF_LEAKED = REPO / "data/dentex/disease_leaked_images.json"
DEF_OUT = REPO / "data/dentex_caries_det"
CLASS_NAME = "decay"
SRC_TAG = "dentex_qed"
ROUND_TRIP_TOL_PX = 1.0
N_RENDER = 12


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def current_eval_md5s(disease_dir: Path, leaked_path: Path) -> set:
    """MD5s of the CURRENTLY-SCORED (leak-free) disease/ eval images -- live, not hardcoded."""
    excluded = set()
    if leaked_path.exists():
        excluded = set(json.loads(leaked_path.read_text())["all_excluded"])
    input_dir = disease_dir / "input"
    scored = [p for p in input_dir.glob("*.png") if p.stem not in excluded]
    return {md5(p) for p in scored}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=DEF_JSON)
    ap.add_argument("--xrays-dir", type=Path, default=DEF_XRAYS)
    ap.add_argument("--disease-dir", type=Path, default=DEF_DISEASE_DIR,
                    help="the eval release, only used here to verify 0 leakage against it")
    ap.add_argument("--leaked", type=Path, default=DEF_LEAKED)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    import cv2

    d = json.loads(args.json.read_text())
    assert "categories_3" in d, f"{args.json}: no categories_3 block -- wrong DENTEX subset?"
    cat3_names = {c["id"]: c["name"] for c in d["categories_3"]}
    print(f"categories_3: {cat3_names}")
    assert CARIES_CLASSES == {1, 3}, "CARIES_CLASSES drifted from build_dentex_crops.py"

    id2img = {im["id"]: im for im in d["images"]}
    by_image = {}  # image_id -> list of (x,y,w,h)
    for a in d["annotations"]:
        if a["category_id_3"] not in CARIES_CLASSES:
            continue
        by_image.setdefault(a["image_id"], []).append(tuple(a["bbox"]))

    n_total_imgs = len(d["images"])
    n_caries_imgs = len(by_image)
    n_caries_boxes = sum(len(v) for v in by_image.values())
    print(f"images: {n_total_imgs}  with >=1 caries/deep_caries box: {n_caries_imgs}  "
          f"boxes: {n_caries_boxes}")

    eval_md5s = current_eval_md5s(args.disease_dir, args.leaked)
    print(f"current leak-free eval cohort: {len(eval_md5s)} images "
          f"(from {args.disease_dir} minus {args.leaked.name})")

    if not args.dry_run:
        (args.out / "images" / "train").mkdir(parents=True, exist_ok=True)
        (args.out / "labels" / "train").mkdir(parents=True, exist_ok=True)
        (args.out / "_check").mkdir(parents=True, exist_ok=True)

    stats = Counter()
    rows = []
    rt_worst = 0.0
    norm_oob = 0
    dim_mismatches = []
    eval_leak_skipped = []
    render_budget = N_RENDER

    for i, (image_id, boxes) in enumerate(sorted(by_image.items()), 1):
        im = id2img[image_id]
        fname, jw, jh = im["file_name"], im["width"], im["height"]
        src_img = args.xrays_dir / fname
        img = cv2.imread(str(src_img))
        if img is None:
            stats["unreadable"] += 1
            continue
        H, W = img.shape[:2]
        if (W, H) != (jw, jh):
            dim_mismatches.append((fname, (jw, jh), (W, H)))
            continue

        file_md5 = md5(src_img)
        if file_md5 in eval_md5s:
            eval_leak_skipped.append(fname)
            continue

        yolo_lines = []
        for (x, y, w, h) in boxes:
            x1, y1, x2, y2 = x, y, x + w, y + h
            x1, x2 = max(0.0, min(x1, W)), max(0.0, min(x2, W))
            y1, y2 = max(0.0, min(y1, H)), max(0.0, min(y2, H))
            if x2 - x1 < 1.0 or y2 - y1 < 1.0:
                stats["degenerate_box"] += 1
                continue
            cx, cy = (x1 + x2) / 2 / W, (y1 + y2) / 2 / H
            bw, bh = (x2 - x1) / W, (y2 - y1) / H
            for v in (cx, cy, bw, bh):
                if v < 0.0 or v > 1.0:
                    norm_oob += 1
            rx1, rx2 = (cx - bw / 2) * W, (cx + bw / 2) * W
            ry1, ry2 = (cy - bh / 2) * H, (cy + bh / 2) * H
            rt_worst = max(rt_worst, abs(rx1 - x1), abs(ry1 - y1), abs(rx2 - x2), abs(ry2 - y2))
            yolo_lines.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

        if not yolo_lines:
            continue
        stem = Path(fname).stem
        stats["images"] += 1
        stats["boxes"] += len(yolo_lines)
        rows.append({"stem": stem, "src": SRC_TAG, "split": "train", "n_boxes": len(yolo_lines),
                     "img_w": W, "img_h": H})

        if args.dry_run:
            continue

        import shutil
        shutil.copy2(src_img, args.out / "images" / "train" / f"{stem}.png")
        (args.out / "labels" / "train" / f"{stem}.txt").write_text("\n".join(yolo_lines) + "\n")
        if render_budget > 0 and i % 50 == 0:
            vis = img.copy()
            for (x, y, w, h) in boxes:
                cv2.rectangle(vis, (int(x), int(y)), (int(x + w), int(y + h)), (0, 0, 255), 3)
            cv2.imwrite(str(args.out / "_check" / f"{stem}.jpg"), vis,
                        [cv2.IMWRITE_JPEG_QUALITY, 85])
            render_budget -= 1

    # -------------------------------------------------------------- GATE
    print("\nGEOMETRY / LEAKAGE GATE")
    print(f"  worst round-trip error: {rt_worst:.4f} px   (threshold {ROUND_TRIP_TOL_PX})")
    print(f"  normalised coords outside [0,1]: {norm_oob}")
    print(f"  JSON/decoded-image dimension mismatches: {len(dim_mismatches)}")
    if dim_mismatches:
        for fname, jdim, idim in dim_mismatches[:5]:
            print(f"    {fname}: json={jdim} decoded={idim}")
    print(f"  training images skipped as byte-identical to a scored eval image: "
          f"{len(eval_leak_skipped)}  {eval_leak_skipped}")
    print(f"  written: {stats['images']} images / {stats['boxes']} boxes "
          f"(of {n_caries_imgs} candidate images / {n_caries_boxes} candidate boxes)")

    fail = []
    if rt_worst > ROUND_TRIP_TOL_PX:
        fail.append(f"round-trip {rt_worst:.3f}px > {ROUND_TRIP_TOL_PX}")
    if norm_oob:
        fail.append(f"{norm_oob} normalised coords outside [0,1]")
    if dim_mismatches:
        fail.append(f"{len(dim_mismatches)} JSON/decoded-image dimension mismatches")
    if not args.dry_run and stats["images"] != len(list((args.out / "labels/train").glob("*.txt"))):
        fail.append("image/label count mismatch")
    if fail:
        raise SystemExit("GATE FAILED: " + "; ".join(fail))
    print("  PASS")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    with open(args.out / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (args.out / "meta.json").write_text(json.dumps({
        "built": "DENTEX quadrant-enumeration-disease -> YOLO caries-box dataset (Lever B domain adapter)",
        "pre_registration": "outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md Sec 3",
        "source": str(args.json),
        "category_filter": "category_id_3 in CARIES_CLASSES={1,3} (Caries, Deep Caries), "
                           "imported from scripts/dentex/build_dentex_crops.py",
        "box_granularity": "WHOLE TOOTH, not lesion -- coarser than CariesXrays boxes, expected "
                           "(PRE_REGISTRATION.md Sec 3, Sec 7 risk 2)",
        "geometry": "box coords from COCO bbox [x,y,w,h]; dims from JSON images block, "
                    "cross-checked against the decoded image shape (0 mismatches required)",
        "leakage": f"{len(eval_leak_skipped)} candidate training image(s) excluded as "
                  f"byte-identical to a currently-scored DENTEX disease/ eval image "
                  f"(checked live against {args.leaked}): {eval_leak_skipped}",
        "gate": {"worst_round_trip_px": round(rt_worst, 4), "norm_coords_out_of_range": norm_oob,
                 "dimension_mismatches": len(dim_mismatches)},
        "class_map": {CLASS_NAME: 0},
        "counts": dict(stats),
    }, indent=2) + "\n")
    print(f"\nwrote {args.out}")
    print(f"  eye-check renders in {args.out / '_check'}")


if __name__ == "__main__":
    main()
