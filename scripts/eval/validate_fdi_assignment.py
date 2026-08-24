"""
Stage-2 validation: does positional FDI assignment produce the right tooth numbers?

Measures the frozen detector + `src/fdi_assignment.py` against the only per-tooth FDI ground
truth this project has: the 250-image `DENTEX/disease/` set (1,600 LabelMe polygons, labels
`{id}-{Turkish name}-{FDI}`). This is the project's first real Stage-2 number, and the
substrate for C3's stage-wise error-propagation decomposition.

ORIENTATION — the step that makes or breaks this
------------------------------------------------
The frozen detector was trained on Tufts' portrait-space annotations, i.e. **sideways**
panoramics; DENTEX ships upright. Measured on 60 images against this same ground truth, with
everything else held constant:

    upright : recall  7.5%,  FDI exact end-to-end  0.0%   (mean 3.2 detections/image)
    CW      : recall 73.7%,  FDI exact end-to-end 21.8%
    CCW     : recall 71.5%,  FDI exact end-to-end 26.1%   <- correct

**Counter-clockwise**, confirmed independently by comparing all 1,000 Tufts
`Radiographs/` vs `Radiographs_rotated/` pairs: 1000/1000 consistent with
ROTATE_90_COUNTERCLOCKWISE, 0/1000 with clockwise. An earlier version of this script used CW,
inferred from a visual overlay without checking how the rotated files were produced — it still
"worked" because a tooth detector is fairly robust to a 180 deg flip, which is exactly why the
error survived a visual check. See `src/orientation.py`.

Detection runs through `src.orientation.detect_upright`, which rotates and un-rotates as one
call: the ground truth here is NOT rotated, because all geometry downstream of the detector
lives in the upright frame.

WHAT IS AND IS NOT MEASURED
---------------------------
DENTEX `disease/` annotation is **not exhaustive** — only teeth carrying a finding are marked
(plus 91 explicitly healthy ones). A typical image has ~6 annotated teeth but ~28-32 real ones.
So this evaluates **GT -> detection**: for each tooth we have ground truth for, was it detected,
and was it numbered correctly? It cannot measure detector precision (an unmatched detection may
be a perfectly real tooth that simply carries no annotation), and no precision number is
reported here for exactly that reason.

`test_181.png` is EXCLUDED — it is byte-identical to `train_332.png` in the detector's own
training set (RESULTS_LOG 2026-08-22). Leaving it in would leak.

Usage:
    python scripts/eval/validate_fdi_assignment.py --limit 8 --save-viz    # eyeball first
    python scripts/eval/validate_fdi_assignment.py                          # full 249
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.fdi_assignment import arch_summary, assign_fdi  # noqa: E402
from src.fdi_head_inference import assign_fdi_head, load_head  # noqa: E402
from src.orientation import detect_upright  # noqa: E402

DEF_DISEASE_DIR = Path.home() / "Downloads/Capstone/DENTEX/disease"
DEF_WEIGHTS = REPO_ROOT / "models/06_yolo_detection_a100_run/best.pt"
DEF_OUT = REPO_ROOT / "outputs/stage2_validation"

def _load_leaked():
    """
    Images excluded from evaluation because they are byte-identical (MD5) to an image the
    pipeline was TRAINED on. There are two independent sources, and missing either inflates
    the result:
      * test_181 -> train_332.png, in the DETECTOR's training set (found 22 Aug).
      * 85 images -> DENTEX quadrant_enumeration, the ENUMERATION HEAD's training set
        (found 22 Aug, after a first run reported 52.2% on the contaminated set).
    The second was easy to miss: quadrant_enumeration and the disease *subset* (705) cover
    disjoint patients, which is true and was verified — but `disease/` is a different folder
    again, and 34% of it is shared with the enumeration images.
    """
    import json
    f = REPO_ROOT / "data/dentex/disease_leaked_images.json"
    if f.exists():
        return set(json.loads(f.read_text())["all_excluded"])
    return {"test_181"}


LEAKED = _load_leaked()
LABEL_RE = re.compile(r"^(\d+)-(.+)-(\d+)$")


def load_gt(label_path):
    """GT teeth in UPRIGHT coordinates, grouped by FDI (one tooth may carry several findings)."""
    d = json.loads(Path(label_path).read_text())
    by_fdi = defaultdict(lambda: {"pts": [], "findings": []})
    for s in d.get("shapes", []):
        m = LABEL_RE.match(s["label"])
        if not m:
            continue
        fdi = int(m.group(3))
        if not (11 <= fdi <= 48):
            continue
        pts = [(px, py) for px, py in s["points"]]
        by_fdi[fdi]["pts"].extend(pts)
        by_fdi[fdi]["findings"].append(m.group(2))
    out = []
    for fdi, v in by_fdi.items():
        a = np.array(v["pts"], dtype=float)
        out.append({"fdi": fdi, "findings": v["findings"],
                    "bbox": [a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max()],
                    "centroid": [a[:, 0].mean(), a[:, 1].mean()]})
    return out


def iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def match_gt_to_detections(gt, dets, min_iou=0.30):
    """
    Greedy one-to-one, best IoU first. Falls back to centroid-containment for a GT tooth whose
    polygon is much smaller than the detected tooth box (a caries lesion polygon can be a
    fraction of the crown), where IoU understates a correct match.
    """
    pairs = sorted(((iou(g["bbox"], d["bbox"]), gi, di)
                    for gi, g in enumerate(gt) for di, d in enumerate(dets)),
                   key=lambda t: -t[0])
    used_g, used_d, out = set(), set(), {}
    for v, gi, di in pairs:
        if v < min_iou or gi in used_g or di in used_d:
            continue
        used_g.add(gi); used_d.add(di); out[gi] = (di, v)
    for gi, g in enumerate(gt):
        if gi in used_g:
            continue
        cx, cy = g["centroid"]
        for di, d in enumerate(dets):
            if di in used_d:
                continue
            b = d["bbox"]
            if b[0] <= cx <= b[2] and b[1] <= cy <= b[3]:
                used_g.add(gi); used_d.add(di)
                out[gi] = (di, iou(g["bbox"], b))
                break
    return out


def draw_viz(img_upright, gt, dets, assigns, matches, out_path, stem):
    v = img_upright.copy()
    for d, a in zip(dets, assigns):
        b = [int(t) for t in d["bbox"]]
        ok_flags = not a["flags"]
        col = (0, 200, 0) if ok_flags else (0, 165, 255)
        cv2.rectangle(v, (b[0], b[1]), (b[2], b[3]), col, 2)
        cv2.putText(v, str(a["fdi"] if a["fdi"] else "?"), (b[0], max(14, b[1] - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2)
    for gi, g in enumerate(gt):
        b = [int(t) for t in g["bbox"]]
        hit = gi in matches
        pred = assigns[matches[gi][0]]["fdi"] if hit else None
        correct = hit and pred == g["fdi"]
        col = (255, 0, 0) if correct else (0, 0, 255)       # blue = correct, red = wrong/missed
        cv2.rectangle(v, (b[0], b[1]), (b[2], b[3]), col, 3)
        tag = f"GT{g['fdi']}" + ("" if correct else f"->{pred if hit else 'MISS'}")
        cv2.putText(v, tag, (b[0], min(v.shape[0] - 6, b[3] + 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
    cv2.putText(v, "green/orange = detection+assigned FDI (orange=flagged) | blue = GT correct"
                   " | red = GT wrong or missed",
                (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
    cv2.imwrite(str(out_path / f"{stem}.jpg"), v, [cv2.IMWRITE_JPEG_QUALITY, 88])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disease-dir", type=Path, default=DEF_DISEASE_DIR)
    ap.add_argument("--weights", type=Path, default=DEF_WEIGHTS)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--det-iou", type=float, default=0.50,
                    help="NMS IoU for the detector. The frozen run's recorded default is 0.70 "
                         "(train_args.yaml), which leaves duplicate boxes: 31 detections on a "
                         "sample image with 14 pairs overlapping >0.5 IoU, versus 21 with zero "
                         "at 0.50. Duplicates are corrosive here specifically because every "
                         "spurious box shifts positional numbering for the whole quadrant. "
                         "0.50 is chosen A PRIORI on anatomy — real teeth in a panoramic do "
                         "not overlap by half their area — NOT by sweeping this threshold "
                         "against the evaluation set, which would contaminate it.")
    ap.add_argument("--imgsz", type=int, default=1024)
    ap.add_argument("--min-iou", type=float, default=0.30)
    ap.add_argument("--limit", type=int, default=0, help="only the first N images")
    ap.add_argument("--method", choices=["positional", "head"], default="positional",
                    help="positional = rank-order sorting (the 28.0%% baseline); "
                         "head = the learned per-tooth enumeration classifier")
    ap.add_argument("--head-weights", type=Path,
                    default=REPO_ROOT / "outputs/enumeration_head/enumeration_head_best.pth")
    ap.add_argument("--no-one-to-one", action="store_true",
                    help="head only: plain argmax instead of Hungarian one-to-one assignment. "
                         "Use it to MEASURE the duplicate-FDI rate rather than assume it.")
    ap.add_argument("--save-viz", action="store_true")
    ap.add_argument("--viz-n", type=int, default=12)
    args = ap.parse_args()

    import torch
    from ultralytics import YOLO
    model = YOLO(str(args.weights))
    head = None
    if args.method == "head":
        dev = torch.device("cuda" if torch.cuda.is_available()
                           else "mps" if torch.backends.mps.is_available() else "cpu")
        head = load_head(args.head_weights, dev)
        print(f"enumeration head: {args.head_weights}  device={dev}  "
              f"one-to-one={'off' if args.no_one_to_one else 'on'}")
    args.out.mkdir(parents=True, exist_ok=True)
    viz_dir = args.out / "viz"
    if args.save_viz:
        viz_dir.mkdir(exist_ok=True)

    labels = sorted((args.disease_dir / "label").glob("*.json"))
    labels = [p for p in labels if p.stem not in LEAKED]
    if args.limit:
        labels = labels[:args.limit]
    print(f"images: {len(labels)}  ({len(LEAKED)} excluded as training duplicates — "
          f"see data/dentex/disease_leaked_images.json)")

    rows, per_image, n_viz = [], [], 0
    for i, lp in enumerate(labels, 1):
        stem = lp.stem
        ip = args.disease_dir / "input" / f"{stem}.png"
        img = cv2.imread(str(ip))
        if img is None:
            print(f"  WARNING unreadable: {ip}")
            continue
        gt = load_gt(lp)
        if not gt:
            continue

        # rotate for the detector, un-rotate immediately: src/orientation.py explains why
        # rotated coordinates must never reach Stage 2.
        boxes, confs = detect_upright(model, img, imgsz=args.imgsz, conf=args.conf,
                                      iou=args.det_iou, verbose=False)
        dets = [{"bbox": b, "conf": c} for b, c in zip(boxes, confs)]
        if args.method == "head":
            assigns = assign_fdi_head(head, img, boxes, dev,
                                      one_to_one=not args.no_one_to_one)
        else:
            assigns = assign_fdi(boxes, img.shape[1], img.shape[0])
        matches = match_gt_to_detections(gt, dets, args.min_iou)

        for gi, g in enumerate(gt):
            hit = gi in matches
            a = assigns[matches[gi][0]] if hit else None
            rows.append({
                "image": stem, "gt_fdi": g["fdi"], "findings": g["findings"],
                "detected": hit,
                "pred_fdi": a["fdi"] if a else None,
                "iou": round(matches[gi][1], 3) if hit else 0.0,
                "flags": a["flags"] if a else [],
                "confidence": a["confidence"] if a else 0.0,
            })
        codes = [a["fdi"] for a in assigns if a.get("fdi")]
        summary = (arch_summary(assigns) if args.method == "positional"
                   else {"n_teeth": len(assigns),
                         "per_quadrant": {q: sum(1 for c in codes if c // 10 == q)
                                          for q in (1, 2, 3, 4)},
                         "n_flagged": sum(1 for a in assigns if a["flags"]),
                         "mean_confidence": round(
                             sum(a["confidence"] for a in assigns) / max(len(assigns), 1), 3)})
        per_image.append({"image": stem, "n_gt": len(gt), "n_det": len(dets),
                          "n_duplicate_fdi": len(codes) - len(set(codes)), **summary})

        if args.save_viz and n_viz < args.viz_n:
            draw_viz(img, gt, dets, assigns, matches, viz_dir, stem)
            n_viz += 1
        if i % 25 == 0:
            print(f"  {i}/{len(labels)} …", flush=True)

    # ---------------- report ----------------
    n = len(rows)
    det = [r for r in rows if r["detected"]]
    exact = [r for r in det if r["pred_fdi"] == r["gt_fdi"]]
    quad = [r for r in det if r["pred_fdi"] and r["pred_fdi"] // 10 == r["gt_fdi"] // 10]
    off_by_one = [r for r in det if r["pred_fdi"] and r["pred_fdi"] // 10 == r["gt_fdi"] // 10
                  and abs(r["pred_fdi"] % 10 - r["gt_fdi"] % 10) == 1]

    print("\n" + "=" * 74)
    print(f"STAGE-2 VALIDATION — detector + {args.method.upper()} FDI assignment vs DENTEX GT")
    print("=" * 74)
    print(f"  GT teeth evaluated            : {n}  across {len(per_image)} images")
    print(f"  detected (recall)             : {len(det)}  ({len(det)/n:.1%})")
    if det:
        print(f"  FDI exact (of detected)       : {len(exact)}  ({len(exact)/len(det):.1%})")
        print(f"  quadrant correct              : {len(quad)}  ({len(quad)/len(det):.1%})")
        print(f"  right quadrant, off-by-one    : {len(off_by_one)}  ({len(off_by_one)/len(det):.1%})")
        print(f"  FDI exact (of ALL GT teeth)   : {len(exact)}  ({len(exact)/n:.1%})  <- end-to-end")

        clean = [r for r in det if not r["flags"]]
        flagged = [r for r in det if r["flags"]]
        if clean:
            print(f"\n  unflagged assignments         : {len(clean)}  exact "
                  f"{sum(1 for r in clean if r['pred_fdi']==r['gt_fdi'])/len(clean):.1%}")
        if flagged:
            print(f"  flagged assignments           : {len(flagged)}  exact "
                  f"{sum(1 for r in flagged if r['pred_fdi']==r['gt_fdi'])/len(flagged):.1%}"
                  "   <- does flagging predict error?")
        fc = Counter(f for r in det for f in r["flags"])
        if fc:
            print(f"  flag frequency                : {dict(fc)}")

    dup = sum(p.get("n_duplicate_fdi", 0) for p in per_image)
    print(f"\n  duplicate FDI codes emitted   : {dup}   "
          f"({'impossible by construction' if args.method == 'positional' else 'a real risk for a per-tooth classifier'})")
    mean_det = np.mean([p["n_det"] for p in per_image]) if per_image else 0
    print(f"\n  mean detections per image     : {mean_det:.1f}  (a full dentition is 28-32)")
    print(f"  mean GT teeth per image       : {np.mean([p['n_gt'] for p in per_image]):.1f}")

    (args.out / f"stage2_rows_{args.method}.json").write_text(json.dumps(rows, indent=1) + "\n")
    (args.out / f"stage2_per_image_{args.method}.json").write_text(json.dumps(per_image, indent=1) + "\n")
    summary = {"n_gt_teeth": n, "n_images": len(per_image), "recall": len(det)/n if n else 0,
               "fdi_exact_of_detected": len(exact)/len(det) if det else 0,
               "fdi_exact_of_all": len(exact)/n if n else 0,
               "quadrant_correct_of_detected": len(quad)/len(det) if det else 0,
               "mean_detections_per_image": float(mean_det),
               "method": args.method, "one_to_one": not args.no_one_to_one,
               "duplicate_fdi_codes": dup,
               "conf": args.conf, "imgsz": args.imgsz, "min_iou": args.min_iou,
               "det_nms_iou": args.det_iou,
               "excluded": sorted(LEAKED)}
    (args.out / f"stage2_summary_{args.method}.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\n  wrote {args.out}/stage2_*_{args.method}.json")
    if args.save_viz:
        print(f"  wrote {n_viz} overlays to {viz_dir}/")


if __name__ == "__main__":
    main()
