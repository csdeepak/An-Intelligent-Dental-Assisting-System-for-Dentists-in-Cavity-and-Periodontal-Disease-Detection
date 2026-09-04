#!/usr/bin/env python
"""Is the Tufts Guard-2 failure caused by the Tufts GT boxes being ~1.5x too TIGHT?

Decisive check: run each detector on the 150 Tufts frozen-test images, then compute
box mAP@0.5 against the GT with the GT boxes SCALED about their centre by
s in {1.0, 1.15, 1.3, 1.5, 1.7}. If a detector's mAP jumps as the GT is loosened,
its predictions are the "natural" tooth size and the tight GT is the problem.
If mAP is flat, box size is not the cause (Phase 0's conclusion).

Also reports mAP at IoU-match {0.3, 0.5} -- 0.3 is what the pipeline's FDI head
actually needs.
"""
import csv
from pathlib import Path

import numpy as np
from ultralytics import YOLO

ROOT = Path("data/detector_multicorpus_v2")
MAN = [r for r in csv.DictReader(open(ROOT / "manifest.csv"))
       if r["corpus"] == "tufts" and r["split"] == "test"]
MODELS = [
    ("Control B (Tufts-only)", "models/15_detector_multicorpus_leverA/controlB_best.pt"),
    ("arm3c (Lever A)",         "models/15_detector_multicorpus_leverA/arm3c_best.pt"),
    ("A2 (Tufts head FT)",      "models/16_detector_leverA2_finetune/a2_best.pt"),
]
SCALES = [1.0, 1.15, 1.3, 1.5, 1.7]
IOUS = [0.3, 0.5]


def load_gt(stem):
    out = []
    for ln in (ROOT / "labels/test" / f"{stem}.txt").read_text().splitlines():
        p = ln.split()
        if len(p) >= 5:
            out.append([float(x) for x in p[1:5]])  # cx cy w h (norm)
    return np.array(out) if out else np.zeros((0, 4))


def scale_boxes(cxcywh, s):
    b = cxcywh.copy()
    b[:, 2:] *= s
    return b


def to_xyxy(cxcywh):
    x = np.empty_like(cxcywh)
    x[:, 0] = cxcywh[:, 0] - cxcywh[:, 2] / 2
    x[:, 1] = cxcywh[:, 1] - cxcywh[:, 3] / 2
    x[:, 2] = cxcywh[:, 0] + cxcywh[:, 2] / 2
    x[:, 3] = cxcywh[:, 1] + cxcywh[:, 3] / 2
    return x


def iou_mat(a, b):
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    tl = np.maximum(a[:, None, :2], b[None, :, :2])
    br = np.minimum(a[:, None, 2:], b[None, :, 2:])
    inter = np.clip(br - tl, 0, None).prod(-1)
    aa = (a[:, 2:] - a[:, :2]).prod(-1)
    ab = (b[:, 2:] - b[:, :2]).prod(-1)
    return inter / (aa[:, None] + ab[None, :] - inter + 1e-9)


def ap_at(all_scores, all_tp, n_gt):
    """single-class AP (VOC-style, all-points) from sorted detections."""
    order = np.argsort(-all_scores)
    tp = np.array(all_tp)[order].astype(float)
    fp = 1 - tp
    ctp, cfp = np.cumsum(tp), np.cumsum(fp)
    rec = ctp / max(n_gt, 1)
    prec = ctp / np.maximum(ctp + cfp, 1e-9)
    mrec = np.concatenate([[0], rec, [1]])
    mpre = np.concatenate([[0], prec, [0]])
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


preds = {}
for tag, w in MODELS:
    m = YOLO(w)
    per_img = []
    for r in MAN:
        img = ROOT / "images/test" / f"{r['stem']}.JPG"
        if not img.exists():
            continue
        rr = m.predict(str(img), imgsz=1024, conf=0.001, iou=0.7, verbose=False)[0]
        xyxyn = rr.boxes.xyxyn.cpu().numpy() if rr.boxes is not None else np.zeros((0, 4))
        conf = rr.boxes.conf.cpu().numpy() if rr.boxes is not None else np.zeros((0,))
        per_img.append((r["stem"], xyxyn, conf))
    preds[tag] = per_img
    print(f"predicted {tag}: {sum(len(c) for _, _, c in per_img)} boxes over {len(per_img)} imgs")

print(f"\n{'model':24} " + "  ".join(f"s={s:<4}" for s in SCALES) + "     (mAP@0.5 vs scaled GT)")
for tag, _ in MODELS:
    for iou_t in IOUS:
        row = []
        for s in SCALES:
            scores, tps, n_gt = [], [], 0
            for stem, pb, pc in preds[tag]:
                gt = load_gt(stem)
                if len(gt):
                    gt = to_xyxy(scale_boxes(gt, s))
                n_gt += len(gt)
                if len(pb) == 0:
                    continue
                M = iou_mat(pb, gt)
                oc = np.argsort(-pc)
                used = set()
                for pi in oc:
                    if M.shape[1] and (gi := int(np.argmax(M[pi]))) not in used and M[pi, gi] >= iou_t:
                        used.add(gi); scores.append(pc[pi]); tps.append(1)
                    else:
                        scores.append(pc[pi]); tps.append(0)
            row.append(ap_at(np.array(scores), tps, n_gt))
        print(f"{tag:20}@{iou_t}  " + "  ".join(f"{v:.3f}" for v in row))
