#!/usr/bin/env python
"""Phase 0 (step 0.2) — draw the GT tooth boxes for a sample of Tufts and DENTEX
test images, so the box-size difference from box_conv.py (DENTEX GT boxes ~1.5x
Tufts area, longer along the tooth axis) can be eyeballed.

This is illustration, not evidence: the box-convention hypothesis was already
refuted at the model level (TUFTS_GUARD2_DIAGNOSIS.md §1.3). Output is a set of
panels in data/detector_multicorpus_v2/_check/gt_overlay/ (local-only, gitignored);
two representative ones are kept tracked in docs/results/figures/lever_a_guard2/.
"""
import csv
from pathlib import Path

import cv2

ROOT = Path("data/detector_multicorpus_v2")
OUT = ROOT / "_check" / "gt_overlay"
OUT.mkdir(parents=True, exist_ok=True)
N_PER_CORPUS = 12

man = [r for r in csv.DictReader(open(ROOT / "manifest.csv")) if r["split"] == "test"]
by_corpus = {}
for r in man:
    by_corpus.setdefault(r["corpus"], []).append(r["stem"])

EXT = {"tufts": ".JPG", "dentex": ".jpg", "kaggle": ".jpg", "ufba": ".jpg"}


def draw(stem, corpus):
    img_p = ROOT / "images" / "test" / f"{stem}{EXT[corpus]}"
    lbl_p = ROOT / "labels" / "test" / f"{stem}.txt"
    im = cv2.imread(str(img_p))
    if im is None:
        return None
    H, W = im.shape[:2]
    areas = []
    for ln in lbl_p.read_text().splitlines():
        p = ln.split()
        if len(p) < 5:
            continue
        cx, cy, w, h = (float(x) for x in p[1:5])
        x1, y1 = int((cx - w / 2) * W), int((cy - h / 2) * H)
        x2, y2 = int((cx + w / 2) * W), int((cy + h / 2) * H)
        cv2.rectangle(im, (x1, y1), (x2, y2), (0, 255, 0), 2)
        areas.append(w * h)
    med = sorted(areas)[len(areas) // 2] if areas else 0
    cv2.putText(im, f"{corpus}  {stem}  n={len(areas)}  med box area={100*med:.2f}% img",
                (12, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
    return im


for corpus in ("tufts", "dentex"):
    stems = sorted(by_corpus[corpus])[:N_PER_CORPUS]
    for stem in stems:
        im = draw(stem, corpus)
        if im is not None:
            cv2.imwrite(str(OUT / f"{corpus}_{stem}.jpg"), im,
                        [cv2.IMWRITE_JPEG_QUALITY, 82])
print(f"wrote {len(list(OUT.glob('*.jpg')))} panels to {OUT}")
