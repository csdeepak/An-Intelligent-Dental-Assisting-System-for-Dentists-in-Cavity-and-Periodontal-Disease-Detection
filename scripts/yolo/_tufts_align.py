"""
Shared Tufts geometry checks — the guard that stops a misaligned dataset being built.

WHY THIS MODULE EXISTS
----------------------
On 26 Aug 2026 a full 90-epoch GPU run was completed, and then thrown away, because every
instance mask in its training data was misaligned with its image. Two independent defects had
to line up to cause it (`RESULTS_LOG.md` 2026-08-27a), and **neither produced an error** —
losses fell smoothly, throughput was healthy, checkpoints were written. A detector trains
perfectly happily on wrong geometry. It cost a GPU rental and most of a day.

The lesson was not "document the two defects". It was: **geometry must be machine-checked
before training, against an independent reference, on whatever machine is actually running.**
That is what this module is for. Prose in a README cannot enforce anything; an assertion can.

This project is worked on from two machines with different local data (see `transfer.md` §8).
Everything here is therefore machine-agnostic by construction: nothing depends on a directory
name, a hostname, or which laptop generated a file — only on measured agreement with
`teeth_bbox.json`.

THE REFERENCE
-------------
`teeth_bbox.json` is the ground truth the canonical bbox detector
(`tooth-detector-a100-1024-v1.0`, test mAP@0.5 **0.7824**) was trained against. That score is
itself the proof it is correctly oriented: misaligned data scores ~0.25 on this task, as the
withdrawn run demonstrated. So agreement with `teeth_bbox.json` is a sound, independent test
of any other Tufts geometry.

THE TWO CHECKS
--------------
`polygon_agreement()` — validates the *annotation transform*. `teeth_polygon.json` stores
points as ``[y, x]`` while `teeth_bbox.json` uses ``[x1, y1, x2, y2]``; established over 6,006
title-paired objects (transpose 2.06 px median centre-distance vs 175-442 px for every
rotation candidate). Machine-independent — it is a property of the data files.

`image_orientation_score()` — validates the *images*. Teeth are radio-dense, so a correctly
aligned annotation mask sits on brighter-than-average pixels. Returns a ratio; >1.0 means
aligned. This is machine-*dependent*: the Windows copy of `Radiographs_rotated/` was generated
before the 22 Aug rotation-direction fix and is 180 degrees out, while the macOS copy is
correct. `pick_image_dir()` resolves that automatically rather than making anyone remember it.
"""

import json
import os
import statistics
from pathlib import Path

# Portrait frame — the orientation teeth_bbox.json and every trained model use.
IMG_WIDTH = 840
IMG_HEIGHT = 1615

# Below this, a dataset is misaligned badly enough that training on it is meaningless.
# The correct pipeline measures ~0.837 median IoU / ~99.4% agreement; the broken one measured
# 0.000 / 1.6%. Anything in between means something new is wrong and needs a human.
MIN_MEDIAN_IOU = 0.70
MIN_AGREEMENT_PCT = 90.0


def polygon_points_to_xy(fragment):
    """
    Convert one teeth_polygon.json fragment to (x, y) pairs.

    THE SWAP THAT WAS MISSING. Points ship as [y, x]; everything downstream expects (x, y).
    Use this rather than re-deriving it — re-deriving it is how it was got wrong the first time.
    """
    return [(p[1], p[0]) for p in fragment]


def _load_bbox_index(bbox_json):
    with open(bbox_json, encoding="utf-8") as fh:
        return {e["External ID"].lower(): e for e in json.load(fh) if e.get("External ID")}


def _real_boxes(entry):
    """Non-degenerate boxes only — the source has some corrupt 1x1/1x2 px entries."""
    out = []
    for o in entry.get("Label", {}).get("objects", []):
        b = o.get("bounding box")
        if b and len(b) == 4 and b[2] - b[0] >= 2 and b[3] - b[1] >= 2:
            out.append(b)
    return out


def _iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def label_agreement(labels_dir, bbox_json, limit=120):
    """
    Compare a BUILT YOLO-seg label dir against teeth_bbox.json.

    This reads the labels YOLO will actually load — not the source JSON, not what the code
    intended — so it catches transform bugs, bad normalisation and corrupted transfers alike.

    Returns (median_iou, agreement_pct, n_instances). (None, None, 0) if nothing comparable.
    """
    bb = _load_bbox_index(bbox_json)
    ious, matched, total = [], 0, 0

    for fn in sorted(os.listdir(labels_dir))[:limit]:
        if not fn.endswith(".txt"):
            continue
        entry = bb.get(Path(fn).stem.lower() + ".jpg")
        if not entry:
            continue
        gt = _real_boxes(entry)
        if not gt:
            continue
        with open(Path(labels_dir) / fn, encoding="utf-8") as fh:
            for line in fh:
                c = [float(v) for v in line.split()[1:]]
                if len(c) < 6:
                    continue
                xs = [c[i] * IMG_WIDTH for i in range(0, len(c), 2)]
                ys = [c[i + 1] * IMG_HEIGHT for i in range(0, len(c), 2)]
                best = max((_iou((min(xs), min(ys), max(xs), max(ys)), g) for g in gt), default=0.0)
                ious.append(best)
                total += 1
                if best >= 0.5:
                    matched += 1

    if not ious:
        return None, None, 0
    return statistics.median(ious), matched / total * 100.0, total


def image_orientation_score(img_dir, bbox_json, limit=40, rotate180=False):
    """
    Median of mean(pixels inside teeth_bbox annotations) / mean(whole image).

    Teeth are radio-dense: aligned annotations land on brighter-than-average pixels (>1.0),
    misaligned ones on soft tissue and air (<1.0). Cheap, needs no trained model.
    """
    from PIL import Image, ImageDraw
    import numpy as np

    bb = _load_bbox_index(bbox_json)
    ratios = []
    for fn in sorted(os.listdir(img_dir))[:limit]:
        entry = bb.get(fn.lower())
        if not entry:
            continue
        boxes = _real_boxes(entry)
        if not boxes:
            continue
        im = Image.open(Path(img_dir) / fn).convert("L")
        if rotate180:
            im = im.rotate(180)
        arr = np.array(im).astype(float)
        mask = Image.new("L", im.size, 0)
        draw = ImageDraw.Draw(mask)
        for x1, y1, x2, y2 in boxes:
            draw.rectangle([x1, y1, x2, y2], fill=255)
        m = np.array(mask) > 0
        if m.sum():
            ratios.append(arr[m].mean() / arr.mean())
    return statistics.median(ratios) if ratios else float("nan")


def pick_image_dir(candidates, bbox_json):
    """
    Choose the correctly-oriented Tufts image directory from several candidates.

    Exists so neither machine needs configuring and nobody has to remember which local copy is
    the good one: the macOS `Radiographs_rotated/` is correct, the Windows one is 180 degrees
    out and its corrected copy lives beside it. Measures rather than trusts the name.

    Returns (chosen_path, score, report_lines). chosen_path is None if none qualify.
    """
    report, best, best_score = [], None, 0.0
    for cand in candidates:
        p = Path(cand)
        if not p.is_dir():
            report.append(f"  {p}  -- not present, skipped")
            continue
        score = image_orientation_score(p, bbox_json)
        verdict = "ALIGNED" if score > 1.0 else "MISALIGNED"
        report.append(f"  {p}  ratio={score:.3f}  {verdict}")
        if score > best_score:
            best, best_score = p, score
    if best is not None and best_score <= 1.0:
        return None, best_score, report
    return best, best_score, report
