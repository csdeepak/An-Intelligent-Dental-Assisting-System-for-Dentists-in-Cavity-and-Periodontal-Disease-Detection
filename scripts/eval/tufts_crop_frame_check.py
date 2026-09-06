#!/usr/bin/env python
"""Is a machine's enumeration crop corpus cut from the frame the head was trained on?

WHY THIS EXISTS
---------------
On 6 Sep 2026 the Option B diagnostic was re-run on the Windows clone to close a traceability
gap (`RESULTS_LOG` 2026-09-06 cites a JSON that was never committed). DENTEX reproduced the
published numbers to a tenth of a point. **Tufts did not: FDI-exact 18.1% against a published
71.5%.**

The labels were not the problem -- the Tufts manifest is internally consistent and matches
DENTEX's conventions exactly (Q1/Q4 image-left, Q1/Q2 upper, |cx-0.5| rising monotonically with
the position digit). Nor was it a rotated crop: all eight dihedral transforms of the stored
crops were scored, and the best (a vertical flip) reached 37.2%. The crops are cut from the
WRONG SOURCE FRAME -- each one shows a different tooth than its label, so no transform of the
crop recovers it. Re-cutting the same boxes from the 180-degree frame scores 73.5%.

This is a machine-local data defect, not a code defect: `data/tufts/enumeration_v1/meta.json`
records that this corpus was built from a scratchpad directory (`.../scratchpad/tufts_ccw`) that
no longer exists, and the same clone's `data/tufts/ZIP/Radiographs_upright/` is likewise 180
degrees from the frame `upright_box()` maps annotations into. Anything crop-level run here --
a diagnostic, an ablation, a retrain -- silently produces garbage until the corpus is rebuilt.

WHAT IT DOES
------------
Cuts each sampled manifest row's crop straight out of a candidate source directory, using the
manifest's own [cx, cy, bw, bh] and the head's 1.5x crop contract, and scores the head on it.
The candidate that reproduces the published accuracy is the frame the corpus SHOULD have been
built from; the stored crops are scored alongside as the control.

Usage:
    python scripts/eval/tufts_crop_frame_check.py
    python scripts/eval/tufts_crop_frame_check.py --corpus data/dentex/enumeration_v1 \
        --candidates ~/Downloads/Capstone/DENTEX/quadrant_enumeration/xrays --n 400
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from src.crop_generator import compute_expanded_bbox  # noqa: E402
from src.fdi_head_inference import (CROP, EXPAND, IMAGENET_MEAN,  # noqa: E402
                                    IMAGENET_STD, load_head)

DEF_CORPUS = REPO / "data/tufts/enumeration_v1"
DEF_HEAD = REPO / "models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth"
DEF_CANDIDATES = [REPO / "data/tufts/ZIP/Radiographs_upright",
                  REPO / "data/tufts/ZIP/Radiographs_upright_fixed"]
DEF_OUT = REPO / "outputs/tufts_fdi_pos_diagnostic/crop_frame_check.json"


def sample_rows(corpus, split, n):
    rows = [r for r in csv.DictReader(open(corpus / "enumeration_manifest.csv"))
            if r["split"] == split and r["jittered"] == "0"]
    return rows[:n] if n else rows


def score(head, tf, imgs, feats, rows):
    import torch
    with torch.no_grad():
        oq, op = head(torch.stack(imgs), torch.tensor(feats, dtype=torch.float32))
    q, p = oq.argmax(1).numpy(), op.argmax(1).numpy()
    qt = np.array([int(r["quadrant"]) - 1 for r in rows])
    pt = np.array([int(r["position"]) - 1 for r in rows])
    return {"n": len(rows), "quadrant": float((q == qt).mean()),
            "position": float((p == pt).mean()),
            "fdi_exact": float(((q == qt) & (p == pt)).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=DEF_CORPUS)
    ap.add_argument("--split", default="test")
    ap.add_argument("--head-weights", type=Path, default=DEF_HEAD)
    ap.add_argument("--candidates", type=Path, nargs="*", default=DEF_CANDIDATES,
                    help="source-image directories to re-cut the same boxes from")
    ap.add_argument("--n", type=int, default=400, help="rows to sample (0 = all)")
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    args = ap.parse_args()

    import torch
    from torchvision import transforms
    tf = transforms.Compose([transforms.ToTensor(),
                             transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
    head = load_head(args.head_weights, torch.device("cpu"))
    rows = sample_rows(args.corpus, args.split, args.n)
    print(f"corpus {args.corpus}  split={args.split}  n={len(rows)}  head={args.head_weights.parent.name}")

    results = {}

    # control: the crops as they sit on disk
    imgs, keep = [], []
    for r in rows:
        p = args.corpus / args.split / r["fdi"] / r["crop"]
        im = cv2.imread(str(p))
        if im is None:
            continue
        imgs.append(tf(cv2.cvtColor(cv2.resize(im, (CROP, CROP)), cv2.COLOR_BGR2RGB)))
        keep.append(r)
    if imgs:
        results["stored_crops"] = score(head, tf, imgs,
                                        [[float(r[k]) for k in ("cx", "cy", "bw", "bh")]
                                         for r in keep], keep)

    # candidates: the same boxes, re-cut from each source frame
    for cand in args.candidates:
        imgs, keep, cache = [], [], {}
        for r in rows:
            src = r["source_image"]
            if src not in cache:
                cache[src] = cv2.imread(str(Path(cand) / src))
            img = cache[src]
            if img is None:
                continue
            H, W = img.shape[:2]
            cx, cy, bw, bh = (float(r[k]) for k in ("cx", "cy", "bw", "bh"))
            x, y, w, h = (cx - bw / 2) * W, (cy - bh / 2) * H, bw * W, bh * H
            x1, y1, x2, y2 = (int(v) for v in
                              compute_expanded_bbox(x, y, w, h, W, H, fw=EXPAND, fh=EXPAND))
            patch = img[y1:max(y2, y1 + 1), x1:max(x2, x1 + 1)]
            if patch.size == 0:
                continue
            imgs.append(tf(cv2.cvtColor(cv2.resize(patch, (CROP, CROP)), cv2.COLOR_BGR2RGB)))
            keep.append(r)
        if imgs:
            results[Path(cand).name] = score(head, tf, imgs,
                                             [[float(r[k]) for k in ("cx", "cy", "bw", "bh")]
                                              for r in keep], keep)

    width = max(len(k) for k in results)
    print()
    for k, v in results.items():
        print(f"  {k:<{width}}  quadrant {v['quadrant']:6.1%}  position {v['position']:6.1%}  "
              f"FDI exact {v['fdi_exact']:6.1%}   (n={v['n']})")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"corpus": str(args.corpus), "split": args.split,
                                    "head": str(args.head_weights), "results": results},
                                   indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
