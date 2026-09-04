#!/usr/bin/env python
"""Phase 0 (step 0.3) — is the Guard-2 loss monotonic in training share and NOT a
confidence-threshold artefact?

Extends iou_diag.py to all three arms x conf in {0.10, 0.25, 0.40}. Same greedy
GT-match on the 150 Tufts frozen-test images. Reports TP / FN / FP / P / R and the
matched-pair IoU median per (arm, conf).

Expectation (the diagnosis, RESULTS_LOG 2026-09-03c): at every conf, FN and FP rise
Control B -> Arm 3C -> Arm 4C, while matched-pair IoU stays flat -> the loss is
detection/confidence (capacity dilution scaling with Tufts training share:
100% -> 33% -> 25%), not localisation, and not an artefact of picking conf 0.25.
"""
import csv
import statistics as st
from pathlib import Path

import numpy as np
from ultralytics import YOLO

ROOT = Path("data/detector_multicorpus_v2")
MAN = [r for r in csv.DictReader(open(ROOT / "manifest.csv"))
       if r["corpus"] == "tufts" and r["split"] == "test"]

ARMS = [
    ("Control B (Tufts only, 100% share)", "models/15_detector_multicorpus_leverA/controlB_best.pt"),
    ("Arm 3C (Tufts+DENTEX+Kaggle, 33%)",  "models/15_detector_multicorpus_leverA/arm3c_best.pt"),
    ("Arm 4C (+ UFBA-425, 25%)",           "models/15_detector_multicorpus_leverA/arm4c_best.pt"),
]
CONFS = [0.10, 0.25, 0.40]


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


def diag(model, conf):
    ious, fn, fp, tp = [], 0, 0, 0
    for r in MAN:
        stem = r["stem"]
        img = ROOT / "images" / "test" / f"{stem}.JPG"
        if not img.exists():
            continue
        gt = load_gt(stem)
        pr = model.predict(str(img), imgsz=1024, conf=conf, iou=0.5, verbose=False)[0]
        pb = pr.boxes.xyxyn.cpu().numpy() if pr.boxes is not None else np.zeros((0, 4))
        order = np.argsort(-pr.boxes.conf.cpu().numpy()) if len(pb) else []
        M = iou_mat(pb, gt)
        used = set()
        for pi in order:
            if M.shape[1] == 0:
                fp += 1
                continue
            gi = int(np.argmax(M[pi]))
            if M[pi, gi] >= 0.5 and gi not in used:
                used.add(gi)
                ious.append(float(M[pi, gi]))
                tp += 1
            else:
                fp += 1
        fn += len(gt) - len(used)
    return tp, fn, fp, (st.median(ious) if ious else 0.0)


print(f"{'arm':34} {'conf':>5} {'TP':>5} {'FN':>5} {'FP':>5} {'P':>6} {'R':>6} {'IoU~':>6}")
rows = {}
for tag, w in ARMS:
    m = YOLO(w)
    for c in CONFS:
        tp, fn, fp, iou = diag(m, c)
        p, r = tp / (tp + fp), tp / (tp + fn)
        rows[(tag, c)] = (tp, fn, fp, p, r, iou)
        print(f"{tag:34} {c:>5.2f} {tp:5d} {fn:5d} {fp:5d} {p:6.3f} {r:6.3f} {iou:6.3f}")

print("\nmonotonic check (FN and FP should each rise ControlB -> Arm3C -> Arm4C at every conf):")
tags = [t for t, _ in ARMS]
for c in CONFS:
    fns = [rows[(t, c)][1] for t in tags]
    fps = [rows[(t, c)][2] for t in tags]
    mono_fn = fns[0] <= fns[1] <= fns[2]
    mono_fp = fps[0] <= fps[1] <= fps[2]
    print(f"  conf {c:.2f}:  FN {fns}  {'MONO' if mono_fn else 'NOT-MONO'}   "
          f"FP {fps}  {'MONO' if mono_fp else 'NOT-MONO'}")
