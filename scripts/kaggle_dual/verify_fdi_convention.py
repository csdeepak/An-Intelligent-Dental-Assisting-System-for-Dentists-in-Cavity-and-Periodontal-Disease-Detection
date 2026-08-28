#!/usr/bin/env python
"""
Is the Kaggle dual-labeled corpus numbered in standard FDI, or MIRRORED?

WHY THIS RUNS BEFORE ANY TRAINING
----------------------------------
Tufts looked like plain Universal notation and was not: its "1" is the upper-LEFT third molar
(FDI 28), not the upper-right (18). Reading it naively would have trained the Stage-2 head on
systematically side-swapped labels -- worse than not using the corpus at all. That took three
independent checks to establish (`RESULTS_LOG.md` 2026-08-25h).

This corpus *presents* as native FDI: its vocabulary is exactly the 32 codes 11-18/21-28/31-38/
41-48. But "the labels look like FDI" says nothing about which side of the patient quadrant 1 is
on, and that is precisely the error Tufts contained. So it is measured, not assumed.

THE ARBITER
-----------
`models/10_fdi_head_dentex_tufts_v2` is a head trained on two corpora whose orientation is
established, scoring 82.6% FDI-exact on detected teeth. Run it over crops cut from this corpus
and compare its predictions against the labels read two ways:

    direct    -- the label as written
    mirrored  -- quadrants swapped left/right (1<->2, 3<->4)

The correct reading should agree far better. On Tufts this test returned 91.7% mirrored vs 6.1%
direct -- not a close call, which is what a real convention mismatch looks like.

A NOTE ON WHAT "AGREEMENT" MEANS HERE
--------------------------------------
The arbiter is imperfect (~83%), so neither number will be ~100%. What matters is the *gap*.
If the two readings come out close together, this test is inconclusive and the corpus must not
be used until a different check settles it -- report that rather than picking the larger number.

Usage:
    python scripts/kaggle_dual/verify_fdi_convention.py --limit 60
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DEF_IMAGES = REPO_ROOT / "data/kaggle_dual/images1"
DEF_LABELS = REPO_ROOT / "data/kaggle_dual/labels"
DEF_HEAD = REPO_ROOT / "models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth"

VALID = {f"{q}{p}" for q in (1, 2, 3, 4) for p in range(1, 9)}


def mirror_fdi(code):
    """Swap the arch left/right: quadrant 1<->2 (upper), 3<->4 (lower). Position is unchanged."""
    q, p = int(code[0]), code[1]
    return f"{ {1: 2, 2: 1, 3: 4, 4: 3}[q] }{p}".replace(" ", "")


def poly_bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=Path, default=DEF_IMAGES)
    ap.add_argument("--labels", type=Path, default=DEF_LABELS)
    ap.add_argument("--head", type=Path, default=DEF_HEAD)
    ap.add_argument("--limit", type=int, default=60)
    args = ap.parse_args()

    import cv2
    import torch

    from src.fdi_head_inference import assign_fdi_head, load_head

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_head(args.head, device)
    print(f"arbiter: {args.head.name} on {device}")

    stems = sorted({p.stem for p in args.images.glob("*.png")})[:args.limit]
    direct = mirrored = total = 0
    for stem in stems:
        lab = args.labels / f"{stem}.json"
        if not lab.exists():
            continue
        img = cv2.imread(str(args.images / f"{stem}.png"), cv2.IMREAD_COLOR)
        if img is None:
            continue
        boxes, gts = [], []
        for sh in json.loads(lab.read_text()).get("shapes", []):
            code = str(sh["label"]).strip()
            if code not in VALID:                     # drops '91' and any other non-FDI token
                continue
            x, y, w, h = poly_bbox(sh["points"])
            if w < 2 or h < 2:
                continue
            boxes.append([x, y, x + w, y + h])
            gts.append(code)
        if not boxes:
            continue
        assigns = assign_fdi_head(model, img, boxes, device, one_to_one=True)
        for a, gt in zip(assigns, gts):
            pred = a.get("fdi")
            if pred is None:
                continue
            pred = str(pred)
            total += 1
            direct += int(pred == gt)
            mirrored += int(pred == mirror_fdi(gt))

    if not total:
        sys.exit("no comparable teeth -- cannot decide the convention")

    d, m = direct / total, mirrored / total
    print(f"\nteeth compared: {total:,}  (over {len(stems)} images)")
    print(f"  agreement, labels read DIRECT   : {d:.1%}")
    print(f"  agreement, labels read MIRRORED : {m:.1%}")
    gap = abs(d - m)
    print()
    if gap < 0.15:
        print(f"  INCONCLUSIVE (gap {gap:.1%}). Do NOT train on this corpus on the strength of")
        print("  this test -- a real convention mismatch is not a close call (Tufts: 91.7 vs 6.1).")
    elif d > m:
        print(f"  VERDICT: labels are STANDARD FDI, read them as written (gap {gap:.1%}).")
    else:
        print(f"  VERDICT: labels are MIRRORED -- apply mirror_fdi() before use (gap {gap:.1%}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
