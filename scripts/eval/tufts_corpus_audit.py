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

# (path, what it is, expected verdict as of 2026-09-06f)
#
# The three misaligned copies were ARCHIVED on 6 Sep 2026 (RESULTS_LOG 2026-09-06f) precisely so
# the inviting short name would stop existing on this machine -- a stale reference now fails
# loudly instead of silently reading 180-degrees-out pixels. So ABSENT is the CORRECT state for
# them here, and their reappearance under those names is what this table is watching for.
TARGETS = [
    ("data/tufts/ZIP/Radiographs_rotated", "portrait, PRE-22-Aug copy -- archived", "ABSENT"),
    ("data/tufts/ZIP/Radiographs_rotated_fixed", "portrait source, corrected", "ALIGNED"),
    ("data/tufts/ZIP/Radiographs_upright", "upright, 180 out -- archived", "ABSENT"),
    # UPRIGHT frame: teeth_bbox.json boxes are portrait, so this metric does not apply to it at
    # all -- it returns a low number rather than raising, which would read as MISALIGNED and cry
    # wolf. Listed so a reader can see it was considered, scored by tufts_crop_frame_check.py.
    ("data/tufts/ZIP/Radiographs_upright_fixed", "upright, correct (enumeration source)", "SKIP"),
    ("data/tufts/dataset_seg/images/train", "YOLO-seg v1 (withdrawn) -- archived", "ABSENT"),
    ("data/tufts/dataset_seg/images/val", "YOLO-seg v1 (withdrawn) -- archived", "ABSENT"),
    ("data/tufts/dataset_seg_v2/images/train", "YOLO-seg v2 -- models/11 trained here", "ALIGNED"),
    ("data/tufts/dataset_seg_v2/images/val", "YOLO-seg v2", "ALIGNED"),
]

# Where the archived copies went. They are kept (rule 3) as the evidence for 2026-09-06c/e and as
# the negative control for scripts/eval/tufts_crop_frame_check.py.
ARCHIVE = REPO.parent / "_repo_archive/misaligned_tufts_frames_2026-09-06"


def main():
    print(f"reference: {BBOX.relative_to(REPO)}")
    print(f"{'directory':<44} {'what':<38} {'score':>6}  verdict")
    print("-" * 104)
    surprises = []
    for rel, what, expected in TARGETS:
        d = REPO / rel
        if expected == "SKIP":
            print(f"{rel:<44} {what:<38} {'--':>6}  not scoreable here (upright frame)")
            continue
        if not d.exists():
            verdict, score = "ABSENT", "--"
        else:
            try:
                s = image_orientation_score(str(d), str(BBOX), limit=25)
                verdict, score = ("ALIGNED" if s > 1.0 else "MISALIGNED"), f"{s:.3f}"
            except Exception as e:      # the upright frame is not comparable to portrait boxes
                verdict, score = "N/A", "--"
                if expected != "N/A":
                    verdict = f"N/A ({type(e).__name__})"
        flag = ""
        if verdict.split(" ")[0] != expected:
            flag = "   <-- CHANGED, expected " + expected
            surprises.append(rel)
        print(f"{rel:<44} {what:<38} {score:>6}  {verdict}{flag}")

    print(f"\narchived misaligned copies: {ARCHIVE}"
          + ("  (present)" if ARCHIVE.exists() else "  (NOT FOUND -- see ARCHIVE_MANIFEST.md)"))

    print("\nNOT covered here -- crop corpora need scripts/eval/tufts_crop_frame_check.py:")
    print("  data/tufts/enumeration_v1            rebuilt 2026-09-06d, verified 73.2% FDI-exact")
    print("  data/tufts/bone_loss_crops_rebuilt   val_cw verified against Radiographs_upright_fixed")
    print("  data/tufts/{severity,resampled}_dataset   metadata only, no pixels on this machine")
    if surprises:
        raise SystemExit(f"\n{len(surprises)} directory(ies) changed verdict: {surprises}\n"
                         f"A misaligned copy reappearing under an inviting name is exactly how "
                         f"the enumeration corpus was built wrong -- do not proceed until this "
                         f"is understood.")
    print("\nall directories match their recorded verdict.")


if __name__ == "__main__":
    main()
