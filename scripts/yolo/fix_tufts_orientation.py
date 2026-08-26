"""
Produce correctly-oriented Tufts portrait radiographs on a machine whose
`Radiographs_rotated/` was generated with the PRE-22-Aug-2026 (wrong-direction) rotation.

WHY THIS EXISTS
---------------
`scripts/yolo/rotate_tufts_radiographs.py` used `Image.ROTATE_270` (90 deg CW) until it was
corrected to `Image.ROTATE_90` (90 deg CCW) on 22 Aug 2026. The Windows machine's
`data/tufts/ZIP/Radiographs_rotated/` has an mtime of **20 Aug 2026** — it predates that fix,
so it holds the wrong-direction output. CW and CCW rotations of the same landscape source
differ by exactly 180 degrees, so the correction is a single 180-degree rotation; the raw
landscape `Radiographs/` folder is not present on this machine and is not needed.

This was NOT assumed from the timestamp. It was established by measurement — see below.

HOW THE 180 WAS ESTABLISHED (2026-08-27)
----------------------------------------
`teeth_bbox.json` is the annotation file the canonical bbox detector
(`tooth-detector-a100-1024-v1.0`, test mAP@0.5 0.7824) was trained against, so it defines the
correct portrait frame. Teeth are radio-dense and therefore bright, so a correctly-aligned
annotation mask should sit on brighter-than-average pixels:

    mean(pixels inside annotation) / mean(whole image), median over 57 images

    current images  0.986      <- annotations land on darker-than-average tissue
    rot180          1.062      <- annotations land on teeth

Confirmed visually on 3 radiographs (dense arch, sparse arch, restored arch): after the
180-degree rotation every polygon traces a real tooth outline — crowns, roots, both arches.
Before it, polygons floated over sinus/bone with the real teeth left uncovered.

WHAT THIS SCRIPT DOES *NOT* FIX
-------------------------------
The `[y, x]` point ordering inside `teeth_polygon.json` — that is a separate, independent
defect fixed in `convert_tufts_to_yolo_seg.py`. Both were required; fixing either alone still
produces misaligned masks. See `RESULTS_LOG.md` 2026-08-27a.

CAVEAT, STATED RATHER THAN BURIED: the output is a second JPEG generation (raw -> rotated ->
rotated-again), where the macOS machine's canonical copy is a first generation. The pixel
content is identical modulo JPEG re-encode noise, which is far below X-ray sensor noise and
irrelevant to training. If exact byte-parity with the canonical dataset is ever required,
re-download the raw landscape `Radiographs/` and run `rotate_tufts_radiographs.py` instead.
Quality is set to 95 to keep that re-encode negligible.

The input directory is left untouched (CLAUDE.md rule 3 — never destroy a research artefact);
output goes to a new directory.

Usage:
    python scripts/yolo/fix_tufts_orientation.py
    python scripts/yolo/fix_tufts_orientation.py --verify   # check only, write nothing
"""

import argparse
import os
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SRC_DIR = Path(os.environ.get(
    "TUFTS_SRC_IMG_DIR", REPO_ROOT / "data" / "tufts" / "ZIP" / "Radiographs_rotated"))
OUT_DIR = Path(os.environ.get(
    "TUFTS_FIXED_IMG_DIR", REPO_ROOT / "data" / "tufts" / "ZIP" / "Radiographs_rotated_fixed"))
BBOX_JSON = Path(os.environ.get(
    "TUFTS_BBOX_JSON",
    REPO_ROOT / "data" / "tufts" / "ZIP" / "Segmentation" / "Segmentation" / "teeth_bbox.json"))

EXPECTED_SIZE = (840, 1615)   # portrait
JPEG_QUALITY = 95


def alignment_ratio(img_dir, bbox_json, limit=60):
    """
    Median of mean(pixels inside teeth_bbox boxes) / mean(whole image).

    Teeth are radio-dense, so correctly-aligned boxes sit on brighter-than-average pixels
    and this lands above 1.0. Misaligned boxes land on soft tissue / air and fall below it.
    """
    import json
    from PIL import Image, ImageDraw
    import numpy as np

    with open(bbox_json, encoding="utf-8") as fh:
        bb = {e["External ID"].lower(): e for e in json.load(fh) if e.get("External ID")}

    ratios = []
    for fname in sorted(os.listdir(img_dir))[:limit]:
        entry = bb.get(fname.lower())
        if not entry:
            continue
        boxes = [
            o["bounding box"] for o in entry.get("Label", {}).get("objects", [])
            if o.get("bounding box") and len(o["bounding box"]) == 4
            and o["bounding box"][2] - o["bounding box"][0] >= 2
            and o["bounding box"][3] - o["bounding box"][1] >= 2
        ]
        if not boxes:
            continue
        im = Image.open(Path(img_dir) / fname).convert("L")
        arr = np.array(im).astype(float)
        mask = Image.new("L", im.size, 0)
        draw = ImageDraw.Draw(mask)
        for x1, y1, x2, y2 in boxes:
            draw.rectangle([x1, y1, x2, y2], fill=255)
        m = np.array(mask) > 0
        if m.sum():
            ratios.append(arr[m].mean() / arr.mean())
    return (statistics.median(ratios), len(ratios)) if ratios else (float("nan"), 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="report alignment for source and (if present) output; write nothing")
    args = ap.parse_args()

    from PIL import Image
    from tqdm import tqdm

    assert SRC_DIR.exists(), f"Source images missing: {SRC_DIR}"
    assert BBOX_JSON.exists(), f"teeth_bbox.json missing: {BBOX_JSON}"

    print("=" * 70)
    print("Tufts orientation fix — 180 degrees")
    print("=" * 70)
    print(f"  source: {SRC_DIR}")
    print(f"  output: {OUT_DIR}")
    print()

    src_ratio, n = alignment_ratio(SRC_DIR, BBOX_JSON)
    print(f"  SOURCE alignment ratio: {src_ratio:.3f}  (n={n})   [>1.0 == aligned]")

    if args.verify:
        if OUT_DIR.exists():
            out_ratio, n2 = alignment_ratio(OUT_DIR, BBOX_JSON)
            print(f"  OUTPUT alignment ratio: {out_ratio:.3f}  (n={n2})")
        else:
            print("  OUTPUT: not built yet")
        return

    if src_ratio > 1.0:
        print()
        print("  Source images already appear correctly aligned (ratio > 1.0).")
        print("  Refusing to rotate — that would BREAK a correct dataset.")
        print("  If you believe this is wrong, verify visually before overriding.")
        sys.exit(1)

    files = sorted(p for p in SRC_DIR.iterdir()
                   if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    assert len(files) >= 990, f"Expected ~1000 images, found {len(files)}"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src in tqdm(files, desc="Rotating 180"):
        img = Image.open(src)
        assert img.size == EXPECTED_SIZE, f"{src.name}: {img.size} != {EXPECTED_SIZE}"
        img.rotate(180).save(OUT_DIR / src.name, quality=JPEG_QUALITY)

    print()
    out_ratio, n2 = alignment_ratio(OUT_DIR, BBOX_JSON)
    print(f"  OUTPUT alignment ratio: {out_ratio:.3f}  (n={n2})")
    print()
    if out_ratio > 1.0 and out_ratio > src_ratio:
        print(f"PASS — {len(files)} images written to {OUT_DIR}")
        print("Point TUFTS_IMG_DIR at this directory when converting.")
    else:
        print("FAIL — output is not better aligned than the source. Do NOT train on this.")
        sys.exit(1)


if __name__ == "__main__":
    main()
