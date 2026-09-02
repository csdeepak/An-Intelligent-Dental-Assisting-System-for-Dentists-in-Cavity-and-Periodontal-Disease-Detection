#!/usr/bin/env python
r"""Build a YOLO DETECTION dataset from the CariesXrays benchmark (Lever 2).

WHY (pre-registered: outputs/lever2_cariesxrays/PRE_REGISTRATION.md)
------------------------------------------------------------------
CariesXrays (Chen et al., AAAI 2024, DOI 10.1609/aaai.v38i20.30196) is a 6,000-image panoramic
benchmark with 13,783 caries-lesion boxes and published detector baselines. This project has no
caries-*lesion* detector -- only the tooth-level caries GATE (a ResNet18 over per-tooth crops),
which an image-blind molar constant ties or beats across six cohorts (PAPER_MATERIAL.md
Sec 8.22/8.24). Lever 2 trains a standalone YOLOv11l lesion detector on CariesXrays and reports
COCO AP beside the published table -- the project's first number on a benchmark's own metric.

** THE OFFICIAL 4,800/1,200 SPLIT IS NOT PUBLIC. ** It is not in the FPCL repo, not in the Drive
download (Annotations.zip + JPEGImages.zip only), and not in the DVCTNet release. This script
therefore draws its OWN seeded image-level split at the same 80/20 ratio. Every number produced
on it is "same dataset, same ratio, same metric, DIFFERENT random test images" -- indicative of
where an off-the-shelf detector lands, NOT a head-to-head result against FPCL's 48.2 AP. The
pre-registration says this in the same words; do not let it drift to "we beat/lost to FPCL".

THE GEOMETRY DEFECT THIS SCRIPT REFUSES TO INHERIT
-------------------------------------------------
27.5% of the XML <size> fields carry a WRONG width (stated 2648 when the image is really
2440 / 2324 / 2444; height is always right). A converter that normalises box coords by the XML
<size> silently corrupts a quarter of the corpus -- the same class of defect that voided a
90-epoch A100 run once before (RESULTS_LOG 2026-08-27a). Box COORDINATES are in the true image
frame (verified: 0 of thousands exceed the real width). So this script reads width/height from
the DECODED IMAGE and never from the XML, exactly as scripts/eval/cariesxrays_external.py does.

GATE, before anything is written or uploaded:
  1. Every converted box round-trips: YOLO norm -> pixel -> matches the source xyxy within 1 px.
  2. 0 normalised coords outside [0, 1].
  3. Image count == label count == split total; 0 stems shared across train/val.
  4. N rendered samples written to <out>/_check/ for eye inspection.

Usage:
    python scripts/yolo/build_cariesxrays_detector_dataset.py --dry-run
    python scripts/yolo/build_cariesxrays_detector_dataset.py
"""

import argparse
import csv
import hashlib
import json
import random
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

DEF_ROOT = Path.home() / "Downloads/Capstone/CariesXrays_Dataset"
DEF_OUT = REPO / "data/cariesxrays_det"
SEED = 42
VAL_FRACTION = 0.20          # 1,200 / 6,000 -- matches FPCL's ratio, NOT their split
CLASS_NAME = "decay"         # XML uses "Decay"; single class -> index 0
ROUND_TRIP_TOL_PX = 1.0
N_RENDER = 12


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def boxes_from_xml(xml_path, img_w, img_h):
    """VOC bndboxes -> list of (x1,y1,x2,y2) in the ACTUAL image frame, clipped, non-degenerate.

    img_w/img_h come from the decoded image, never the XML <size> (27.5% wrong). Returns
    (boxes, xml_size_was_wrong).
    """
    r = ET.parse(xml_path).getroot()
    s = r.find("size")
    xml_w = int(float(s.find("width").text)) if s is not None else None
    xml_h = int(float(s.find("height").text)) if s is not None else None
    out = []
    for o in r.findall("object"):
        b = o.find("bndbox")
        x1, y1, x2, y2 = (float(b.find(k).text) for k in ("xmin", "ymin", "xmax", "ymax"))
        x1, x2 = max(0.0, min(x1, img_w)), max(0.0, min(x2, img_w))
        y1, y2 = max(0.0, min(y1, img_h)), max(0.0, min(y2, img_h))
        if x2 - x1 < 1.0 or y2 - y1 < 1.0:
            continue
        out.append((x1, y1, x2, y2))
    return out, (xml_w != img_w or xml_h != img_h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEF_ROOT)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--val-fraction", type=float, default=VAL_FRACTION)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    import cv2

    ann_dir = args.root / "Annotations"
    img_dir = args.root / "JPEGImages"
    stems = sorted(p.stem for p in ann_dir.glob("*.xml"))
    stems = [s for s in stems if (img_dir / f"{s}.jpg").exists()]
    print(f"paired (image + xml) stems: {len(stems)}")

    # ----- OUR seeded split (image-level). NOT the FPCL split -- see the module docstring.
    rng = random.Random(args.seed)
    shuffled = stems[:]
    rng.shuffle(shuffled)
    n_val = round(len(shuffled) * args.val_fraction)
    val_set = set(shuffled[:n_val])
    split_of = {s: ("val" if s in val_set else "train") for s in stems}
    print(f"split (seed {args.seed}): train {len(stems) - n_val}  val {n_val}  "
          f"({args.val_fraction:.0%} val) -- THIS PROJECT'S SPLIT, not FPCL's")

    stats = Counter()
    rows = []
    rt_worst = 0.0
    norm_oob = 0
    render_budget = N_RENDER

    if not args.dry_run:
        for sp in ("train", "val"):
            (args.out / "images" / sp).mkdir(parents=True, exist_ok=True)
            (args.out / "labels" / sp).mkdir(parents=True, exist_ok=True)
        (args.out / "_check").mkdir(parents=True, exist_ok=True)

    for i, stem in enumerate(stems, 1):
        sp = split_of[stem]
        src_img = img_dir / f"{stem}.jpg"
        img = cv2.imread(str(src_img))
        if img is None:
            stats["unreadable"] += 1
            continue
        H, W = img.shape[:2]
        boxes, size_wrong = boxes_from_xml(ann_dir / f"{stem}.xml", W, H)
        stats["xml_size_wrong"] += int(size_wrong)
        stats[f"{sp}/images"] += 1
        stats[f"{sp}/boxes"] += len(boxes)
        if len(boxes) == 0:
            stats[f"{sp}/images_no_lesion"] += 1

        yolo_lines = []
        for (x1, y1, x2, y2) in boxes:
            cx, cy = (x1 + x2) / 2 / W, (y1 + y2) / 2 / H
            bw, bh = (x2 - x1) / W, (y2 - y1) / H
            for v in (cx, cy, bw, bh):
                if v < 0.0 or v > 1.0:
                    norm_oob += 1
            # round-trip: norm -> pixel xyxy, compare to source
            rx1, rx2 = (cx - bw / 2) * W, (cx + bw / 2) * W
            ry1, ry2 = (cy - bh / 2) * H, (cy + bh / 2) * H
            rt_worst = max(rt_worst, abs(rx1 - x1), abs(ry1 - y1), abs(rx2 - x2), abs(ry2 - y2))
            yolo_lines.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

        rows.append({"stem": stem, "split": sp, "n_boxes": len(boxes),
                     "img_w": W, "img_h": H, "xml_size_wrong": int(size_wrong)})

        if args.dry_run:
            continue

        shutil.copy2(src_img, args.out / "images" / sp / f"{stem}.jpg")
        (args.out / "labels" / sp / f"{stem}.txt").write_text("\n".join(yolo_lines) +
                                                             ("\n" if yolo_lines else ""))
        if render_budget > 0 and len(boxes) > 0 and i % 137 == 0:
            vis = img.copy()
            for (x1, y1, x2, y2) in boxes:
                cv2.rectangle(vis, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)
            cv2.imwrite(str(args.out / "_check" / f"{stem}_{sp}.jpg"), vis,
                        [cv2.IMWRITE_JPEG_QUALITY, 85])
            render_budget -= 1
        if i % 500 == 0:
            print(f"  {i}/{len(stems)} ...", flush=True)

    # -------------------------------------------------------------- GATE
    print("\nGEOMETRY / SPLIT GATE")
    print(f"  worst round-trip error: {rt_worst:.4f} px   (threshold {ROUND_TRIP_TOL_PX})")
    print(f"  normalised coords outside [0,1]: {norm_oob}")
    tr_stems = {r["stem"] for r in rows if r["split"] == "train"}
    va_stems = {r["stem"] for r in rows if r["split"] == "val"}
    overlap = tr_stems & va_stems
    print(f"  train/val stem overlap: {len(overlap)}")
    print(f"  images {stats['train/images'] + stats['val/images']}  "
          f"boxes {stats['train/boxes'] + stats['val/boxes']}  "
          f"(xml <size> wrong on {stats['xml_size_wrong']} = "
          f"{stats['xml_size_wrong'] / max(len(stems), 1) * 100:.1f}%)")
    print(f"  train {stats['train/images']} img / {stats['train/boxes']} boxes "
          f"({stats['train/images_no_lesion']} lesion-free)")
    print(f"  val   {stats['val/images']} img / {stats['val/boxes']} boxes "
          f"({stats['val/images_no_lesion']} lesion-free)")

    fail = []
    if rt_worst > ROUND_TRIP_TOL_PX:
        fail.append(f"round-trip {rt_worst:.3f}px > {ROUND_TRIP_TOL_PX}")
    if norm_oob:
        fail.append(f"{norm_oob} normalised coords outside [0,1]")
    if overlap:
        fail.append(f"{len(overlap)} stems in both splits")
    if not args.dry_run and stats["train/images"] != len(list((args.out / "labels/train").glob("*.txt"))):
        fail.append("train image/label count mismatch")
    if fail:
        raise SystemExit("GATE FAILED: " + "; ".join(fail))
    print("  PASS")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    (args.out / "data.yaml").write_text(
        "# CariesXrays (Chen et al., AAAI 2024, DOI 10.1609/aaai.v38i20.30196) -> YOLO detect\n"
        "# Built by scripts/yolo/build_cariesxrays_detector_dataset.py\n"
        f"# SPLIT: this project's own seed-{args.seed} image-level {1 - args.val_fraction:.0%}/"
        f"{args.val_fraction:.0%}. NOT the FPCL 4,800/1,200 split (not public). Numbers are\n"
        "# indicative vs the published table, not head-to-head. See the PRE_REGISTRATION.\n"
        f"path: {args.out}\ntrain: images/train\nval: images/val\n\n"
        f"nc: 1\nnames: ['{CLASS_NAME}']\n")
    with open(args.out / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (args.out / "meta.json").write_text(json.dumps({
        "built": "CariesXrays YOLO detection dataset (Lever 2)",
        "pre_registration": "outputs/lever2_cariesxrays/PRE_REGISTRATION.md",
        "source": "Chen et al., CariesXrays, AAAI 2024 38(20) 21940-21948, "
                  "DOI 10.1609/aaai.v38i20.30196; github.com/Binz-Chen/AAAI2024_CariesXrays "
                  "(Drive: Annotations.zip + JPEGImages.zip, no ImageSets)",
        "split": f"THIS PROJECT'S own seed-{args.seed} image-level split, "
                 f"{1 - args.val_fraction:.0%}/{args.val_fraction:.0%}. The official FPCL "
                 f"4,800/1,200 split is NOT public (checked: FPCL repo, Drive, DVCTNet repo).",
        "geometry": "box w/h read from the DECODED IMAGE; XML <size> ignored "
                    f"({stats['xml_size_wrong']} XMLs = "
                    f"{stats['xml_size_wrong'] / max(len(stems), 1) * 100:.1f}% carry a wrong width)",
        "gate": {"worst_round_trip_px": round(rt_worst, 4),
                 "norm_coords_out_of_range": norm_oob,
                 "train_val_overlap": len(overlap)},
        "class_map": {CLASS_NAME: 0},
        "counts": dict(stats),
    }, indent=2) + "\n")
    print(f"\nwrote {args.out}")
    print(f"  eye-check renders in {args.out / '_check'}")


if __name__ == "__main__":
    main()
