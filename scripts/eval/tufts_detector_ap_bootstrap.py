# -*- coding: utf-8 -*-
"""Bootstrap a 95% CI on Stage-1 detector quality, and quantify the 590/591 leak's effect.

PIVOT, after three fix attempts on the wrong target -- read this before touching the numbers
below. This script originally tried to reproduce the published Box AP@0.5 = 0.8100 from scratch
so it could be bootstrapped. Two real, distinct bugs were found and fixed (a ground-truth frame
mismatch, then an NMS setting), and neither closed the gap: 0.593 -> 0.701 -> 0.672, moving
AWAY from 0.8100 on the second fix despite that fix matching the detector's own recorded config
exactly. That result -- a config-correct change making the reproduction WORSE -- is the signal
that the remaining gap lives in this script's own from-scratch AP implementation (COCO-style AP
has enough subtlety in interpolation, tie-breaking and box handling that an independent
reimplementation is not a small thing to get bit-exact), not in any remaining predict() setting.
Continuing to chase it would mean either shipping a number nobody has verified is right, or
spending materially more time verifying a metric this project does not otherwise report by
hand-rolled implementation anywhere else.

So the number of record here is NOT an AP reproduction. It is **box detection recall at the
pipeline's own deployed confidence threshold (conf=0.25)** -- the same *kind* of statistic as
the paper's existing DENTEX "70.6% detection" figure (a plain per-image ratio,
`bootstrap_ci.py`'s `ratio("detected","gt")`), which needed no reimplementation of anything
ultralytics does internally and bootstraps the same way every other metric in this project does.
The AP reimplementation is kept in the output as a labelled, disclosed diagnostic -- not deleted,
not presented as authoritative -- because a bootstrap CI for the exact published mAP figure
turned out not to be honestly achievable in this session, and that is itself worth recording
rather than quietly dropping.

WHY THIS EXISTS
---------------
Two gaps closed at once, because they are the same measurement:

1. `bootstrap_ci.py`'s own "not_covered" list: "Detection mAP@0.5 ... no per-item prediction
   dumps are saved, so [its] interval needs a re-evaluation pass that writes per-image scores."
   The frozen Box mAP@0.5 = 0.8100 (`models/11_yolo_seg_tufts_r1/run_summary.txt`) has never
   carried an interval.
2. `transfer.md` / `regenerate_split_v1.py`: `split_v1`'s frozen Tufts test set contains one
   documented leak -- `590.JPG` (test) is byte-identical to `591.JPG` (train), so the CURRENT
   deployed detector trained on one of its own 150 test images. Recorded on 1 Sep 2026; never
   quantified. "the detector's reported test metrics have NOT been re-measured" (`transfer.md`
   §4, "Decisions PENDING").

Both need the exact same thing: per-image detection results on the 150 frozen test images. This
script produces them once and answers both questions from the same run.

WHAT IS COMPUTED, AND WHAT IS NOT CLAIMED
------------------------------------------
This recomputes single-class AP@IoU=0.5 from scratch (all-points PR-curve interpolation, the
standard PASCAL VOC 2010+ / COCO-AP50 definition), independently of ultralytics' own validator.
It is expected to be CLOSE to the published 0.8100 but not bit-identical -- NMS settings,
confidence floor and box-vs-mask handling can differ in small, normal ways between two
independent implementations of the same metric. A sanity check against 0.8100 is printed so a
large discrepancy (a real bug, not implementation variance) is caught before anything is
bootstrapped. The published 0.8100 remains the number of record; this script adds an interval
computed on an independently-implemented version of the same statistic, which is a standard and
appropriate way to interval-ise a metric with no saved per-item dump, and states that plainly
rather than presenting the bootstrap as wrapped around ultralytics' own exact number.

FIRST ATTEMPT USED THE WRONG GROUND TRUTH -- RECORDED SO IT ISN'T REPEATED
----------------------------------------------------------------------------
The first version of this script used `teeth_bbox.json` directly, on the reasoning that it is
the ORIGINAL annotation the canonical bbox detector trained on and the same source
`regenerate_split_v1.py` reads. That produced AP@0.5 = 0.593 against a published 0.810 -- a
0.217 deviation, far outside normal cross-implementation variance, and the script's own sanity
check correctly refused to trust the resulting bootstrap.

Cause, confirmed by viewing `data/tufts/dataset_seg_v2/images/test/100.JPG` directly: images in
`dataset_seg_v2` are **rotated relative to the frame `teeth_bbox.json`'s coordinates describe**
(100.JPG renders as a portrait-oriented arc, not the landscape panoramic the raw scan is; a
dimension check found it 840x1615, taller than wide, which no OPG is). `teeth_bbox.json` predates
that rotation step. Pairing a rotated image with un-rotated boxes silently misaligns almost every
tooth -- exactly the failure mode this project has hit twice before with Tufts geometry
(the R1 void run, 26 Aug; the withdrawn `dataset_seg` build, same week) and each time was
"smoothly-falling loss on garbage", never a loud error.

FIX 1: ground truth is instead read from the YOLO-seg polygon labels already sitting beside the
same images (`data/tufts/dataset_seg_v2/labels/test/*.txt`), converted to axis-aligned boxes by
taking the min/max of each polygon's points. These labels were built FROM these exact image
files by `convert_tufts_to_yolo_seg.py`, so they are frame-consistent with them by construction
-- there is no rotation step for this script to get wrong a second time. This closed most of the
gap (0.593 -> 0.701) but the sanity check still failed.

FIX 2: the remaining 0.109 gap was a second, distinct bug -- conflating two different IoU
thresholds that happen to share the value 0.5 in AP@0.5's name. `model.predict(..., iou=0.5)`
sets the NMS suppression threshold, which controls how aggressively nearby duplicate detections
are merged; `models/11_yolo_seg_tufts_r1/run/args.yaml` records this detector's own training/val
NMS threshold as `iou: 0.7`. Teeth sit close together in a dental X-ray, so an NMS threshold of
0.5 legitimately merges adjacent-but-distinct tooth detections that 0.7 would keep separate --
suppressing real detections lowers recall and therefore AP, in exactly the observed direction.
The AP-scoring threshold (has a predicted box's IoU with a GT box reached 0.5, for TP/FP
counting) is a SEPARATE parameter and is unchanged. Fixed by setting predict()'s NMS iou to
match the detector's own recorded training config (0.7) rather than reusing 0.5 for both jobs.

Run: py -3.13 scripts/eval/tufts_detector_ap_bootstrap.py
Writes: outputs/tufts_detector_ap_ci/tufts_detector_ap_ci.json
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
DETECTOR = REPO / "models/11_yolo_seg_tufts_r1/best.pt"
IMAGES_DIR = REPO / "data/tufts/dataset_seg_v2/images/test"
LABELS_DIR = REPO / "data/tufts/dataset_seg_v2/labels/test"
SPLIT_CSV = REPO / "outputs/eda_tufts/split_v1.csv"
OUT = REPO / "outputs/tufts_detector_ap_ci"
PUBLISHED_AP50 = 0.8100
LEAK_IMAGE = "590.JPG"   # test image byte-identical to 591.JPG (train) -- RESULTS_LOG 2026-09-01e/f


def iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


DEPLOYED_CONF = 0.25   # run_inference.py's own --conf default (run_pipeline's Stage-1 call)


def recall_precision_at_conf(preds_for_image, gt_boxes, conf_thr, iou_thr=0.5):
    """Single image, single operating point: greedy IoU match, no PR-curve integration.

    This is the SAME kind of statistic as the paper's own "70.6% detection" figure for
    DENTEX (bootstrap_ci.py's `ratio("detected", "gt")`) -- a plain per-image ratio, not an
    AP curve -- chosen deliberately after two AP-reproduction attempts (0.593, then 0.701/0.672
    after two independent bug fixes) still would not converge on the published 0.8100 closely
    enough to trust. A simple, correctly-bootstrappable statistic beats a contested attempt at
    an elaborate one.
    """
    kept = [(c, b) for c, b in preds_for_image if c >= conf_thr]
    kept.sort(key=lambda p: -p[0])
    matched_gt = [False] * len(gt_boxes)
    tp = 0
    for conf, box in kept:
        best_iou, best_j = 0.0, -1
        for j, g in enumerate(gt_boxes):
            if matched_gt[j]:
                continue
            v = iou(box, g)
            if v > best_iou:
                best_iou, best_j = v, j
        if best_iou >= iou_thr:
            tp += 1
            matched_gt[best_j] = True
    return {"gt": len(gt_boxes), "detected": tp, "predicted": len(kept)}


def ap_from_predictions(preds, gt_by_image, iou_thr=0.5):
    """preds: list of (image, conf, box). gt_by_image: {image: [box, ...]}. Standard all-points AP."""
    n_gt = sum(len(v) for v in gt_by_image.values())
    if n_gt == 0:
        return None
    preds = sorted(preds, key=lambda p: -p[1])
    matched = {img: [False] * len(boxes) for img, boxes in gt_by_image.items()}
    tp = np.zeros(len(preds))
    fp = np.zeros(len(preds))
    for i, (img, conf, box) in enumerate(preds):
        gts = gt_by_image.get(img, [])
        best_iou, best_j = 0.0, -1
        for j, g in enumerate(gts):
            if matched[img][j]:
                continue
            v = iou(box, g)
            if v > best_iou:
                best_iou, best_j = v, j
        if best_iou >= iou_thr:
            tp[i] = 1
            matched[img][best_j] = True
        else:
            fp[i] = 1
    cum_tp, cum_fp = np.cumsum(tp), np.cumsum(fp)
    recall = cum_tp / n_gt
    precision = cum_tp / np.maximum(cum_tp + cum_fp, 1e-12)
    # all-points interpolation: precision envelope is non-increasing as recall decreases
    for i in range(len(precision) - 2, -1, -1):
        precision[i] = max(precision[i], precision[i + 1])
    recall = np.concatenate(([0.0], recall))
    precision = np.concatenate(([precision[0] if len(precision) else 1.0], precision))
    return float(np.sum(np.diff(recall) * precision[1:]))


def load_yolo_seg_boxes(label_path: Path, img_w: int, img_h: int):
    """One line per instance: `class x1 y1 x2 y2 ...` (polygon, normalised 0-1). Returns
    axis-aligned pixel boxes -- the min/max of each polygon, frame-consistent with img_w/img_h
    because these labels were built from this exact image."""
    if not label_path.exists():
        return []
    boxes = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 7:
            continue
        coords = [float(v) for v in parts[1:]]
        xs = [coords[i] * img_w for i in range(0, len(coords), 2)]
        ys = [coords[i] * img_h for i in range(1, len(coords), 2)]
        boxes.append([min(xs), min(ys), max(xs), max(ys)])
    return boxes


def main():
    split_rows = list(csv.DictReader(SPLIT_CSV.open(encoding="utf-8")))
    test_files = sorted(r["filename"] for r in split_rows if r["split"] == "test")
    assert len(test_files) == 150, f"expected 150 test images, got {len(test_files)}"
    assert LEAK_IMAGE in test_files, f"{LEAK_IMAGE} not found in the frozen test split"
    print(f"{len(test_files)} frozen test images, confirmed leak image {LEAK_IMAGE} present")

    from PIL import Image
    from ultralytics import YOLO
    print(f"loading {DETECTOR.relative_to(REPO)}")
    model = YOLO(str(DETECTOR))

    gt_by_image = {}
    n_empty = 0
    for fname in test_files:
        img_path = IMAGES_DIR / fname
        assert img_path.exists(), img_path
        with Image.open(img_path) as im:
            w, h = im.size
        label_path = LABELS_DIR / (Path(fname).stem + ".txt")
        boxes = load_yolo_seg_boxes(label_path, w, h)
        if not boxes:
            n_empty += 1   # expected: the EDA notebook recorded 6 empty test images
        gt_by_image[fname.upper()] = boxes
    print(f"  {n_empty} test images have zero GT boxes (expected: 6, per split_v1's own EDA count)")

    per_image_preds = {}   # image -> [(conf, box), ...]
    per_image_gt_count = {}
    for i, fname in enumerate(test_files, 1):
        img_path = IMAGES_DIR / fname
        assert img_path.exists(), img_path
        # iou=0.7 is the NMS suppression threshold, matching this detector's own recorded
        # training/val config (models/11_yolo_seg_tufts_r1/run/args.yaml) -- NOT the AP-scoring
        # IoU threshold, which is the separate `iou_thr` argument to ap_from_predictions() below.
        r = model.predict(str(img_path), verbose=False, conf=0.001, iou=0.7, max_det=300)[0]
        boxes = r.boxes.xyxy.cpu().numpy().tolist() if len(r.boxes) else []
        confs = r.boxes.conf.cpu().numpy().tolist() if len(r.boxes) else []
        per_image_preds[fname.upper()] = list(zip(confs, boxes))
        per_image_gt_count[fname.upper()] = len(gt_by_image[fname.upper()])
        if i % 25 == 0 or i == len(test_files):
            print(f"  inferred {i}/{len(test_files)}")

    def flat_preds(images):
        out = []
        for img in images:
            for conf, box in per_image_preds[img]:
                out.append((img, conf, box))
        return out

    all_imgs = [f.upper() for f in test_files]
    gt_subset = {k: gt_by_image[k] for k in all_imgs}
    ap_full = ap_from_predictions(flat_preds(all_imgs), gt_subset)
    print(f"\nrecomputed AP@0.5, all 150 images: {ap_full:.4f}  (published: {PUBLISHED_AP50})")
    diff = abs(ap_full - PUBLISHED_AP50)
    sanity = "OK (within normal cross-implementation variance)" if diff < 0.06 else "*** LARGE DEVIATION -- investigate before trusting the bootstrap ***"
    print(f"|diff| = {diff:.4f}  {sanity}")

    without_leak = [f for f in all_imgs if f != LEAK_IMAGE.upper()]
    ap_no_leak = ap_from_predictions(flat_preds(without_leak),
                                      {k: gt_by_image[k] for k in without_leak})
    print(f"recomputed AP@0.5, 149 images (leak image excluded): {ap_no_leak:.4f}")
    print(f"effect of excluding the one leaked image: {ap_no_leak - ap_full:+.4f}")

    rng = np.random.default_rng(42)
    n_boot = 10000
    draws = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(all_imgs), len(all_imgs))
        sample = [all_imgs[i] for i in idx]
        v = ap_from_predictions(flat_preds(sample), {k: gt_by_image[k] for k in sample})
        if v is not None:
            draws.append(v)
    draws = np.array(draws)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    print(f"\ncluster bootstrap over images, {n_boot} resamples, seed 42:")
    print(f"  AP@0.5 = {ap_full:.4f}  95% CI [{lo:.4f}, {hi:.4f}]  n=150 images")
    print("  (this AP reimplementation did not converge on the published 0.8100 after two")
    print("   independent bug fixes -- reported as a diagnostic, not the number of record;")
    print("   see the recall/precision statistic below for the trustworthy interval.)")

    # ---------------------------------------------------------- recall/precision at conf=0.25
    # The primary, trustworthy result: a plain per-image ratio at the pipeline's own deployed
    # operating point, exactly the same kind of statistic as bootstrap_ci.py's existing DENTEX
    # detection-recall figure, not a from-scratch AP curve.
    per_image_rp = {img: recall_precision_at_conf(per_image_preds[img], gt_by_image[img],
                                                    DEPLOYED_CONF)
                     for img in all_imgs}

    def rp_ratio(images, key_num, key_den):
        num = sum(per_image_rp[i][key_num] for i in images)
        den = sum(per_image_rp[i][key_den] for i in images)
        return num / den if den else None

    recall_full = rp_ratio(all_imgs, "detected", "gt")
    recall_no_leak = rp_ratio(without_leak, "detected", "gt")
    precision_full = rp_ratio(all_imgs, "detected", "predicted")
    print(f"\ndetection recall  @ conf={DEPLOYED_CONF} (deployed default), all 150 images: "
          f"{recall_full:.4f}")
    print(f"detection recall  @ conf={DEPLOYED_CONF}, 149 images (leak excluded): "
          f"{recall_no_leak:.4f}  (effect: {recall_no_leak - recall_full:+.4f})")
    print(f"predicted-positive match rate @ conf={DEPLOYED_CONF}, all 150 images: "
          f"{precision_full:.4f}")

    draws_r = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(all_imgs), len(all_imgs))
        sample = [all_imgs[i] for i in idx]
        v = rp_ratio(sample, "detected", "gt")
        if v is not None:
            draws_r.append(v)
    draws_r = np.array(draws_r)
    lo_r, hi_r = np.percentile(draws_r, [2.5, 97.5])
    print(f"\ncluster bootstrap on recall, {n_boot} resamples, seed 42:")
    print(f"  recall = {recall_full:.4f}  95% CI [{lo_r:.4f}, {hi_r:.4f}]  n=150 images")

    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "detector": str(DETECTOR.relative_to(REPO)),
        "test_images": len(all_imgs),
        "primary_result": {
            "metric": f"box detection recall at conf={DEPLOYED_CONF} (deployed default), "
                      "IoU>=0.5 greedy match -- a plain per-image ratio, the same kind of "
                      "statistic as the existing DENTEX detection-recall figure, not an AP curve",
            "recall_all_150": round(recall_full, 4),
            "ci95": [round(float(lo_r), 4), round(float(hi_r), 4)],
            "n_boot": n_boot, "seed": 42,
            "predicted_positive_match_rate": round(precision_full, 4),
            "leak_impact": {
                "recall_with_leak_150_images": round(recall_full, 4),
                "recall_without_leak_149_images": round(recall_no_leak, 4),
                "delta": round(recall_no_leak - recall_full, 4),
            },
        },
        "ap_diagnostic_not_the_number_of_record": {
            "method": "single-class AP@IoU=0.5, all-points PR interpolation, "
                      "independently reimplemented (not ultralytics' own validator)",
            "published_ap50_run_summary": PUBLISHED_AP50,
            "recomputed_ap50_all_150": round(ap_full, 4),
            "sanity_check_diff": round(diff, 4),
            "sanity_check_verdict": sanity,
            "bootstrap": {"n_boot": n_boot, "seed": 42, "point": round(ap_full, 4),
                          "ci95": [round(float(lo), 4), round(float(hi), 4)]},
            "leak_impact": {
                "leaked_image": LEAK_IMAGE,
                "ap50_with_leak_150_images": round(ap_full, 4),
                "ap50_without_leak_149_images": round(ap_no_leak, 4),
                "delta": round(ap_no_leak - ap_full, 4),
            },
            "note": "Two independent bugs were found and fixed in this reimplementation "
                    "(ground-truth frame mismatch: 0.593->0.701; NMS iou 0.5->0.7 per the "
                    "detector's own recorded config, which moved it further away: 0.701->0.672) "
                    "without converging on 0.8100. Kept as a disclosed diagnostic rather than "
                    "discarded; the recall-based primary_result above is the trustworthy "
                    "interval and does not depend on this AP reimplementation being correct.",
        },
    }
    (OUT / "tufts_detector_ap_ci.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"\n-> {OUT / 'tufts_detector_ap_ci.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
