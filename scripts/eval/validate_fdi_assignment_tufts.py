"""
Stage-2 validation on TUFTS — the end-to-end FDI number the pipeline never had.

`validate_fdi_assignment.py` measures detector + enumeration head against DENTEX `disease/`.
This is its Tufts twin: same detector, same head (`models/10`, DENTEX+Tufts), same greedy
IoU-0.30 + centroid matcher, same Hungarian one-to-one head assignment — but scored against
the **complete** Tufts per-tooth numbering (`Segmentation/teeth_bbox.json`, ~25k permanent
teeth), so this is a real recall AND a real end-to-end accuracy, not the GT-only-teeth
partial number DENTEX gives.

WHY IT MATTERS
--------------
The paper decomposes DENTEX stage-by-stage (58.3% end-to-end FDI) and has NO equivalent for
Tufts. With the deployed detector (`models/11`, Tufts-trained) this is the pipeline on its
home turf; with a multi-corpus detector it is the other half of the Lever A / A2 story
(box mAP fell, but what happens end-to-end?).

THREE THINGS FROM `scripts/tufts/build_enumeration_crops.py`, REUSED VERBATIM
---------------------------------------------------------------------------
1. Numbering is left-right MIRRORED. `tufts_title_to_fdi` applies the mirror and returns
   None for deciduous (A-T) and unmappable titles. Verified three ways, RESULTS_LOG 2026-08-25h.
2. `teeth_bbox.json` boxes are PORTRAIT (840x1615, = `Radiographs_rotated/`). Crops and all
   Stage-2 geometry are UPRIGHT (`Radiographs/`, 1615x840). `upright_box` is the CCW inverse.
3. Degenerate <2px boxes = "tooth absent" -> dropped.

LEAKAGE — the frozen split_v1 train (700) is the detector's and the head's training set.
Any test image byte-identical to a train image is excluded (MD5), exactly as
`validate_fdi_assignment.py` excludes `test_181` on DENTEX.

Usage:
    python scripts/eval/validate_fdi_assignment_tufts.py --limit 8 --save-viz     # eyeball
    python scripts/eval/validate_fdi_assignment_tufts.py                          # deployed detector
    python scripts/eval/validate_fdi_assignment_tufts.py --weights models/15_detector_multicorpus_leverA/arm3c_best.pt --out outputs/stage2_tufts_arm3c

`--ufba DIR` scores UFBA-425 instead (outputs/stage1_switch/PRE_REGISTRATION.md, Amendment 3,
row P): same detector call, head, matcher and report; only the image list and the ground-truth
loader change. Without it nothing here differs from the Tufts run.
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).parent))
from validate_fdi_assignment import draw_viz, iou, match_gt_to_detections  # noqa: E402,F401
from src.fdi_head_inference import (ASSIGNMENTS, assign_from_scores,       # noqa: E402
                                    head_joint_scores, load_head)
from src.fdi_structural_repair import (has_detected_gap,                   # noqa: E402
                                       repair_diagnostics)
from src.orientation import detect_upright                                 # noqa: E402
from src.utils.fdi_converter import tufts_title_to_fdi                     # noqa: E402

DEF_IMAGES = REPO / "_repo_archive/datasets_workspace/Radiographs"          # upright 1615x840
DEF_BBOX = REPO / "data/tufts/ZIP/Segmentation/Segmentation/teeth_bbox.json"
DEF_SPLIT = REPO / "outputs/eda_tufts/split_v1.csv"
DEF_WEIGHTS = REPO / "models/11_yolo_seg_tufts_r1/best.pt"
DEF_HEAD = REPO / "models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth"
DEF_OUT = REPO / "outputs/stage2_tufts"
MIN_BOX = 2


def upright_box(bbox_portrait, img_w):
    """Tufts portrait (x1,y1,x2,y2) -> upright (x1,y1,x2,y2). CCW inverse (x,y)->(W-1-y,x),
    img_w = UPRIGHT width. Copied from scripts/tufts/build_enumeration_crops.py."""
    x1, y1, x2, y2 = bbox_portrait
    ax, ay = (img_w - 1) - y1, x1
    bx, by = (img_w - 1) - y2, x2
    return min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)


def leaked_test_stems(images_dir, split_of):
    """Test stems byte-identical to a train image (the detector's / head's training set)."""
    md5 = {}
    for stem, sp in split_of.items():
        p = images_dir / f"{stem}.JPG"
        if p.exists():
            md5.setdefault(hashlib.md5(p.read_bytes()).hexdigest(), []).append((stem, sp))
    leaked = set()
    for members in md5.values():
        splits = {sp for _, sp in members}
        if "train" in splits and len(splits) > 1:
            leaked |= {s for s, sp in members if sp != "train"}
    return leaked


def load_tufts_gt(objects, img_w):
    """teeth_bbox.json objects for one image -> [{fdi, bbox(upright x1y1x2y2), centroid}]."""
    out = []
    for o in objects:
        bx = o.get("bounding box")
        if not bx or bx[2] - bx[0] < MIN_BOX or bx[3] - bx[1] < MIN_BOX:
            continue
        fdi = tufts_title_to_fdi(str(o["title"]).strip())   # mirror-corrected; None if deciduous/bad
        if fdi is None:
            continue
        x1, y1, x2, y2 = upright_box(bx, img_w)
        out.append({"fdi": fdi, "bbox": [x1, y1, x2, y2],
                    "centroid": [(x1 + x2) / 2, (y1 + y2) / 2]})
    return out


def load_ufba_gt(label_path, img_w, img_h):
    """UFBA-425 YOLO label file -> [{fdi, bbox(x1y1x2y2), centroid}], in img_w x img_h pixels.
    Class c is FDI (c // 8 + 1) * 10 + (c % 8 + 1). Five of the 11,591 lines are polygons
    (class, then x y pairs); those take the polygon's bounding box.

    A line too short to parse, or a class outside 0-31, raises (14 Oct 2026): it used to be skipped
    or turned into an impossible FDI code silently. All 11,591 lines of the 425 files pass."""
    out = []
    for line in Path(label_path).read_text().splitlines():
        p = line.split()
        if not p:
            continue
        if len(p) < 5:
            raise ValueError(f"{label_path}: line too short to parse: {line!r}")
        c, v = int(p[0]), [float(x) for x in p[1:]]
        if not 0 <= c <= 31:
            raise ValueError(f"{label_path}: class {c} is outside 0-31")
        if len(v) == 4:
            xs, ys = (v[0] - v[2] / 2, v[0] + v[2] / 2), (v[1] - v[3] / 2, v[1] + v[3] / 2)
        else:
            xs, ys = v[0::2], v[1::2]
        x1, y1, x2, y2 = min(xs) * img_w, min(ys) * img_h, max(xs) * img_w, max(ys) * img_h
        out.append({"fdi": (c // 8 + 1) * 10 + (c % 8 + 1), "bbox": [x1, y1, x2, y2],
                    "centroid": [(x1 + x2) / 2, (y1 + y2) / 2]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=Path, default=DEF_IMAGES)
    ap.add_argument("--bbox", type=Path, default=DEF_BBOX)
    ap.add_argument("--split", type=Path, default=DEF_SPLIT)
    ap.add_argument("--weights", type=Path, default=DEF_WEIGHTS)
    ap.add_argument("--head-weights", type=Path, default=DEF_HEAD)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--det-iou", type=float, default=0.50)   # same a-priori choice as the DENTEX eval
    ap.add_argument("--imgsz", type=int, default=1024)
    ap.add_argument("--min-iou", type=float, default=0.30)
    ap.add_argument("--split-name", default="test",
                    help="which split_v1 split to score. 'test' is the frozen evaluation set; "
                         "'val' exists so a change can be sanity-checked without touching it.")
    ap.add_argument("--assignment", default="hungarian",
                    help="comma-separated assignment strategies to score, e.g. "
                         "'hungarian,structural-sort,structural-dp'. Every arm scores the SAME "
                         "detector boxes and the SAME head forward pass, so a paired bootstrap "
                         "over images measures the assignment and nothing else (Lever C, "
                         "outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md).")
    ap.add_argument("--ufba", type=Path, default=None,
                    help="score UFBA-425 under this directory (numbering_xrays/ + boundinng_boxes/) "
                         "instead of Tufts")
    ap.add_argument("--exclude", type=Path, default=None,
                    help="with --ufba: JSON list of image stems to leave out (the leak gate's output)")
    ap.add_argument("--aspect", type=float, default=0.0,
                    help="with --ufba: widen each image to this width/height before anything runs. "
                         "0 scores the 640x640 export as distributed")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--save-viz", action="store_true")
    ap.add_argument("--viz-n", type=int, default=12)
    args = ap.parse_args()
    if args.aspect and not args.ufba:
        ap.error("--aspect applies only with --ufba")   # it used to be ignored without a word

    import torch
    from ultralytics import YOLO
    from scripts.run_inference import load_yolo_pinned

    if args.ufba:
        leaked = set(json.loads(args.exclude.read_text())) if args.exclude else set()
        test_stems = sorted(p.stem for p in (args.ufba / "numbering_xrays").glob("*.jpg")
                            if p.stem not in leaked)
    else:
        split_of = {Path(r["filename"]).stem: r["split"].strip()
                    for r in csv.DictReader(open(args.split))}
        leaked = leaked_test_stems(args.images, split_of)
        records = {Path(r["External ID"]).stem: r["Label"]["objects"]
                   for r in json.loads(args.bbox.read_text())}
        test_stems = sorted(s for s, sp in split_of.items()
                            if sp == args.split_name and s not in leaked and s in records)
    if args.limit:
        test_stems = test_stems[:args.limit]
    print(f"{'UFBA-425' if args.ufba else 'Tufts ' + args.split_name} images: {len(test_stems)}  "
          f"({len(leaked)} excluded as train duplicates: {sorted(leaked) or 'none'})")

    dev = torch.device("cuda" if torch.cuda.is_available()
                       else "mps" if torch.backends.mps.is_available() else "cpu")
    model = load_yolo_pinned(args.weights)
    head = load_head(args.head_weights, dev)
    print(f"detector: {args.weights.name}   head: {args.head_weights.parent.name}   device={dev}")
    args.out.mkdir(parents=True, exist_ok=True)
    viz_dir = args.out / "viz"
    if args.save_viz:
        viz_dir.mkdir(exist_ok=True)

    arms = [a.strip() for a in args.assignment.split(",") if a.strip()]
    for a in arms:
        if a not in ASSIGNMENTS:
            raise SystemExit(f"unknown --assignment {a!r}; choose from {ASSIGNMENTS}")
    print(f"assignment arms: {', '.join(arms)}")

    rows = {a: [] for a in arms}
    per_image = {a: [] for a in arms}
    struct_diag = {}
    n_viz = 0
    for i, stem in enumerate(test_stems, 1):
        img = cv2.imread(str(args.ufba / "numbering_xrays" / f"{stem}.jpg" if args.ufba
                             else args.images / f"{stem}.JPG"))
        if img is None:
            print(f"  WARNING unreadable: {stem}")
            continue
        if args.ufba and args.aspect:
            img = cv2.resize(img, (round(img.shape[0] * args.aspect), img.shape[0]))
        H, W = img.shape[:2]
        gt = (load_ufba_gt(args.ufba / "boundinng_boxes" / f"{stem}.txt", W, H) if args.ufba
              else load_tufts_gt(records[stem], W))
        if not gt:
            continue
        boxes, confs = detect_upright(model, img, imgsz=args.imgsz, conf=args.conf,
                                      iou=args.det_iou, verbose=False)
        dets = [{"bbox": b, "conf": c} for b, c in zip(boxes, confs)]
        matches = match_gt_to_detections(gt, dets, args.min_iou)
        # ONE forward pass, shared by every arm -- that is what makes the arms exactly paired.
        lq = lp = joint = None
        gap_img = False
        if len(boxes):
            lq, lp, joint = head_joint_scores(head, img, boxes, dev)
            gap_img = bool(has_detected_gap(boxes, lq, W, H))
            diag = repair_diagnostics(boxes, lq, lp, W, H)
            for k, v in diag.items():
                struct_diag[k] = struct_diag.get(k, 0) + v

        for arm in arms:
            assigns = (assign_from_scores(joint, lq, lp, boxes, W, H, one_to_one=True,
                                          assignment=arm) if len(boxes) else [])
            for gi, g in enumerate(gt):
                hit = gi in matches
                a = assigns[matches[gi][0]] if hit else None
                rows[arm].append({"image": stem, "gt_fdi": g["fdi"], "detected": hit,
                                  "pred_fdi": a["fdi"] if a else None,
                                  "iou": round(matches[gi][1], 3) if hit else 0.0,
                                  "flags": a["flags"] if a else [],
                                  "image_has_gap": gap_img})
            codes = [a["fdi"] for a in assigns if a.get("fdi")]
            per_image[arm].append({"image": stem, "n_gt": len(gt), "n_det": len(dets),
                                   "n_duplicate_fdi": len(codes) - len(set(codes)),
                                   "image_has_gap": gap_img})
            if args.save_viz and arm == arms[0] and n_viz < args.viz_n:
                draw_viz(img, gt, dets, assigns, matches, viz_dir, stem)
                n_viz += 1
        if i % 25 == 0:
            print(f"  {i}/{len(test_stems)} ...", flush=True)

    # ---------------- report, one block per arm ----------------
    for arm in arms:
        arows, aimgs = rows[arm], per_image[arm]
        suffix = "" if arm == "hungarian" else f"__{arm}"
        n = len(arows)
        det = [r for r in arows if r["detected"]]
        exact = [r for r in det if r["pred_fdi"] == r["gt_fdi"]]
        quad = [r for r in det if r["pred_fdi"] and r["pred_fdi"] // 10 == r["gt_fdi"] // 10]
        obo = [r for r in det if r["pred_fdi"] and r["pred_fdi"] // 10 == r["gt_fdi"] // 10
               and abs(r["pred_fdi"] % 10 - r["gt_fdi"] % 10) == 1]
        dup = sum(pi["n_duplicate_fdi"] for pi in aimgs)
        mean_det = float(np.mean([pi["n_det"] for pi in aimgs])) if aimgs else 0.0
        flag_counts = Counter(f for r in det for f in r["flags"])

        print("\n" + "=" * 70)
        print(f"TUFTS STAGE-2 -- {args.weights.name} + head({args.head_weights.parent.name}), "
              f"assignment={arm}")
        print("=" * 70)
        print(f"  GT teeth (permanent, mirror-corrected)  : {n}  across {len(aimgs)} images")
        print(f"  detected (recall)                       : {len(det)}  ({len(det)/n:.1%})")
        if det:
            print(f"  FDI exact (of detected)                 : {len(exact)}  ({len(exact)/len(det):.1%})")
            print(f"  quadrant correct (of detected)          : {len(quad)}  ({len(quad)/len(det):.1%})")
            print(f"  right quadrant, off-by-one              : {len(obo)}  ({len(obo)/len(det):.1%})")
            print(f"  FDI exact (of ALL GT teeth)             : {len(exact)}  ({len(exact)/n:.1%})   <- END-TO-END")
            ant = [r for r in det if r["gt_fdi"] % 10 <= 3]
            post = [r for r in det if r["gt_fdi"] % 10 >= 4]
            for lbl, sub in (("anterior (pos 1-3)", ant), ("posterior (pos 4-8)", post),
                             ("images with a detected gap",
                              [r for r in det if r["image_has_gap"]]),
                             ("images contiguous", [r for r in det if not r["image_has_gap"]])):
                if sub:
                    hits = sum(1 for r in sub if r["pred_fdi"] == r["gt_fdi"])
                    print(f"    {lbl:<28}: {hits/len(sub):.1%}  (n={len(sub)})")
        print(f"  duplicate FDI codes emitted             : {dup}")
        print(f"  mean detections / image                 : {mean_det:.1f}   (full dentition 28-32)")
        if arm != "hungarian" and struct_diag:
            g, ov, na = struct_diag["n_groups"], struct_diag["n_overfull"], struct_diag["n_no_anchor"]
            anc, mov, tot = (struct_diag["n_anchor_teeth"], struct_diag["n_movable_teeth"],
                             struct_diag["n_teeth"])
            print(f"  quadrant groups                         : {g}  "
                  f"({ov} over-full >8 boxes, {na} with no anchor -> both keep the Hungarian)")
            print(f"  detections the repair COULD move        : {mov}/{tot} ({mov/max(tot,1):.1%}) "
                  f"-- {anc} are anchors, the rest sit in groups it cannot touch")
        if flag_counts:
            print(f"  flags                                   : {dict(flag_counts)}")

        summary = {"n_gt_teeth": n, "n_images": len(aimgs),
                   "recall": len(det) / n if n else 0,
                   "fdi_exact_of_detected": len(exact) / len(det) if det else 0,
                   "fdi_exact_of_all": len(exact) / n if n else 0,
                   "quadrant_correct_of_detected": len(quad) / len(det) if det else 0,
                   "mean_detections_per_image": mean_det, "duplicate_fdi_codes": dup,
                   "flag_counts": dict(flag_counts),
                   "structural_diagnostics": struct_diag,
                   "detector": str(args.weights), "head": str(args.head_weights),
                   "assignment": arm,
                   "conf": args.conf, "det_nms_iou": args.det_iou, "imgsz": args.imgsz,
                   "min_iou": args.min_iou, "one_to_one": True,
                   "excluded_leaked": sorted(leaked),
                   **({"corpus": "ufba425", "aspect": args.aspect} if args.ufba else {})}
        (args.out / f"stage2_rows_head{suffix}.json").write_text(json.dumps(arows, indent=1) + "\n")
        (args.out / f"stage2_per_image_head{suffix}.json").write_text(json.dumps(aimgs, indent=1) + "\n")
        (args.out / f"stage2_summary_head{suffix}.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(f"\n  wrote {args.out}/stage2_*_head{suffix}.json"
              + (f"  +  {n_viz} overlays" if args.save_viz else ""))


if __name__ == "__main__":
    main()
