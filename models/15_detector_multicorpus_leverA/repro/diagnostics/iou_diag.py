#!/usr/bin/env python
"""Decisive Guard-2 diagnostic: WHERE does Arm 3C lose vs Control B on Tufts test?

For each model: predict on the 150 Tufts frozen-test images, greedily match preds
to GT by IoU (per image), then report:
  - matched-pair IoU distribution  -> localization quality
  - FN (unmatched GT) and FP (unmatched pred) counts at conf 0.25
  - pred vs GT width/height ratio   -> systematic box-shape error
  - mAP@0.5 from ultralytics val (ground truth cross-check)
"""
import csv
import statistics as st
from pathlib import Path

import numpy as np
from ultralytics import YOLO

ROOT = Path("data/detector_multicorpus_v2")
man = [r for r in csv.DictReader(open(ROOT / "manifest.csv"))
       if r["corpus"] == "tufts" and r["split"] == "test"]

def load_gt(stem):
    lp = ROOT / "labels" / "test" / f"{stem}.txt"
    out = []
    for ln in lp.read_text().splitlines():
        p = ln.split()
        if len(p) < 5:
            continue
        cx, cy, w, h = map(float, p[1:5])
        out.append([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2])
    return np.array(out) if out else np.zeros((0, 4))

def iou_mat(a, b):
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    tl = np.maximum(a[:, None, :2], b[None, :, :2])
    br = np.minimum(a[:, None, 2:], b[None, :, 2:])
    inter = np.clip(br - tl, 0, None).prod(-1)
    aa = (a[:, 2:] - a[:, :2]).prod(-1)
    ab = (b[:, 2:] - b[:, :2]).prod(-1)
    return inter / (aa[:, None] + ab[None, :] - inter + 1e-9)

def diag(weights, conf=0.25):
    m = YOLO(weights)
    ious, fn, fp, tp = [], 0, 0, 0
    wr, hr = [], []
    for r in man:
        stem = r["stem"]
        img = ROOT / "images" / "test" / f"{stem}.JPG"
        if not img.exists():
            continue
        gt = load_gt(stem)
        pr = m.predict(str(img), imgsz=1024, conf=conf, iou=0.5, verbose=False)[0]
        pb = pr.boxes.xyxyn.cpu().numpy() if pr.boxes is not None else np.zeros((0, 4))
        M = iou_mat(pb, gt)
        used_g = set()
        order = np.argsort(-pr.boxes.conf.cpu().numpy()) if len(pb) else []
        for pi in order:
            if M.shape[1] == 0:
                fp += 1
                continue
            gi = int(np.argmax(M[pi]))
            if M[pi, gi] >= 0.5 and gi not in used_g:
                used_g.add(gi)
                ious.append(float(M[pi, gi]))
                tp += 1
                pw, ph = pb[pi, 2] - pb[pi, 0], pb[pi, 3] - pb[pi, 1]
                gw, gh = gt[gi, 2] - gt[gi, 0], gt[gi, 3] - gt[gi, 1]
                wr.append(pw / gw); hr.append(ph / gh)
            else:
                fp += 1
        fn += len(gt) - len(used_g)
    a = sorted(ious)
    q = lambda p: a[min(len(a) - 1, int(p * len(a)))] if a else 0
    print(f"  matched pairs (IoU>=.5): {tp:5d}   FN: {fn:4d}   FP: {fp:4d}   "
          f"P={tp/(tp+fp):.3f} R={tp/(tp+fn):.3f}")
    print(f"  matched IoU: median {st.median(a):.3f}  p10 {q(.1):.3f}  p25 {q(.25):.3f}  "
          f"frac in [.5,.6): {sum(x<.6 for x in a)/len(a):.2f}")
    print(f"  pred/GT width ratio  median {st.median(wr):.3f}   height ratio median {st.median(hr):.3f}")

for tag, w in [("Control B (Tufts-only)", "models/15_detector_multicorpus_leverA/controlB_best.pt"),
               ("Arm 3C (Tufts+DENTEX+Kaggle)", "models/15_detector_multicorpus_leverA/arm3c_best.pt")]:
    print(f"\n=== {tag} ===")
    diag(w)
