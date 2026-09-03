#!/usr/bin/env python
"""Decisive check for the 'blended box convention' hypothesis.

If Arm 3C fails Guard 2 because it learned a box size between Tufts-tight and
DENTEX-loose, then on Tufts TEST images its PREDICTED boxes should be
systematically LARGER than both (a) Control B's predictions and (b) the Tufts GT.
"""
import csv
import statistics as st
from pathlib import Path

from ultralytics import YOLO

ROOT = Path("data/detector_multicorpus_v2")
man = [r for r in csv.DictReader(open(ROOT / "manifest.csv"))
       if r["corpus"] == "tufts" and r["split"] == "test"]
imgs = [str(ROOT / "images" / "test" / f"{r['stem']}.JPG") for r in man]
imgs = [p for p in imgs if Path(p).exists()]
print(f"{len(imgs)} Tufts test images")

# GT box areas (normalized, fraction of image) from the frozen test labels
gt_area, gt_n = [], []
for r in man:
    lp = ROOT / "labels" / "test" / f"{r['stem']}.txt"
    if not lp.exists():
        continue
    a = [float(x.split()[3]) * float(x.split()[4])
         for x in lp.read_text().splitlines() if x.strip()]
    gt_area += a
    gt_n.append(len(a))

def pred_stats(weights, conf=0.25, iou=0.5):
    m = YOLO(weights)
    areas, npi = [], []
    for p in imgs:
        r = m.predict(p, imgsz=1024, conf=conf, iou=iou, verbose=False)[0]
        wh = r.boxes.xywhn.cpu().numpy() if r.boxes is not None else []
        a = [float(w) * float(h) for _, _, w, h in wh]
        areas += a
        npi.append(len(a))
    return areas, npi

print(f"\n{'source':28} {'boxes':>7} {'box/img':>8} {'med area %img':>13} {'p25':>7} {'p75':>7}")
def line(tag, areas, npi):
    a = sorted(areas)
    q = lambda p: a[min(len(a) - 1, int(p * len(a)))] if a else 0
    print(f"{tag:28} {len(a):7d} {st.mean(npi):8.1f} "
          f"{100*st.median(a):13.3f} {100*q(.25):7.3f} {100*q(.75):7.3f}")

line("Tufts GT (frozen test)", gt_area, gt_n)
for tag, w in [("Control B (Tufts-only detect)", "models/15_detector_multicorpus_leverA/controlB_best.pt"),
               ("Arm 3C (Tufts+DENTEX+Kaggle)", "models/15_detector_multicorpus_leverA/arm3c_best.pt"),
               ("Arm 4C (+UFBA)",                "models/15_detector_multicorpus_leverA/arm4c_best.pt")]:
    areas, npi = pred_stats(w)
    line(tag, areas, npi)
