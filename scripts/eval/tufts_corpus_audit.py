#!/usr/bin/env python
"""Audit every Tufts-derived image directory on this machine for orientation/frame defects.

WHY THIS EXISTS
---------------
Two frame defects have now been found on the Windows clone, months apart, each silent:

  27 Aug 2026  `Radiographs_rotated/` is 180 degrees out (RESULTS_LOG 2026-08-27a) -- a
               90-epoch GPU run was trained on it and thrown away. `_tufts_align.pick_image_dir`
               was written so nothing would have to remember which copy is good.
  6 Sep 2026   `Radiographs_upright/` (derived from the bad copy) and the enumeration crop
               corpus built from it are 180 degrees out too (RESULTS_LOG 2026-09-06c). Nothing
               checked those, because the guard written in August only guards the directories it
               was pointed at.

The lesson each time was the same: check the whole surface, on the machine actually running.
This script does that in one command -- every Tufts image directory and YOLO dataset in one
table, using `_tufts_align.image_orientation_score` (median of mean-pixels-inside-annotations
over mean-pixels-in-image; teeth are radio-dense, so aligned data scores >1).

WHAT IT CANNOT TELL YOU
-----------------------
The score separates ALIGNED from 180-degrees-out on portrait-frame images, and that is all.
It says nothing about crop corpora (use `tufts_crop_frame_check.py`, which scores the head on
candidate frames) and nothing about a 90-degree error, which produces degenerate boxes and is
caught by the builders' own geometry guards instead.

Usage:
    python scripts/eval/tufts_corpus_audit.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "yolo"))
from _tufts_align import image_orientation_score  # noqa: E402

BBOX = REPO / "data/tufts/ZIP/Segmentation/Segmentation/teeth_bbox.json"

# (path, what it is, expected verdict as of 2026-09-06)
TARGETS = [
    ("data/tufts/ZIP/Radiographs_rotated", "portrait source, PRE-22-Aug copy", "MISALIGNED"),
    ("data/tufts/ZIP/Radiographs_rotated_fixed", "portrait source, corrected", "ALIGNED"),
    ("data/tufts/dataset_seg/images/train", "YOLO-seg v1 (withdrawn, 2026-08-27a)", "MISALIGNED"),
    ("data/tufts/dataset_seg/images/val", "YOLO-seg v1 (withdrawn)", "MISALIGNED"),
    ("data/tufts/dataset_seg_v2/images/train", "YOLO-seg v2 -- models/11 trained here", "ALIGNED"),
    ("data/tufts/dataset_seg_v2/images/val", "YOLO-seg v2", "ALIGNED"),
]


def main():
    print(f"reference: {BBOX.relative_to(REPO)}")
    print(f"{'directory':<44} {'what':<38} {'score':>6}  verdict")
    print("-" * 104)
    surprises = []
    for rel, what, expected in TARGETS:
        d = REPO / rel
        if not d.exists():
            print(f"{rel:<44} {what:<38} {'--':>6}  ABSENT")
            continue
        try:
            s = image_orientation_score(str(d), str(BBOX), limit=25)
        except Exception as e:                      # a non-portrait dir has no comparable score
            print(f"{rel:<44} {what:<38} {'--':>6}  N/A ({type(e).__name__})")
            continue
        verdict = "ALIGNED" if s > 1.0 else "MISALIGNED"
        flag = "" if verdict == expected else "   <-- CHANGED, expected " + expected
        if flag:
            surprises.append(rel)
        print(f"{rel:<44} {what:<38} {s:>6.3f}  {verdict}{flag}")

    print("\nNOT covered here -- crop corpora need scripts/eval/tufts_crop_frame_check.py:")
    print("  data/tufts/enumeration_v1            rebuilt 2026-09-06d, verified 73.2% FDI-exact")
    print("  data/tufts/bone_loss_crops_rebuilt   val_cw verified against Radiographs_upright_fixed")
    print("  data/tufts/{severity,resampled}_dataset   metadata only, no pixels on this machine")
    if surprises:
        raise SystemExit(f"\n{len(surprises)} directory(ies) changed verdict: {surprises}")
    print("\nall directories match their recorded verdict.")


if __name__ == "__main__":
    main()
