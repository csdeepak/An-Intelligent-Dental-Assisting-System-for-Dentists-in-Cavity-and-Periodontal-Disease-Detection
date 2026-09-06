"""
Build FDI-labelled tooth crops from Tufts — a second training source for the Stage-2 head.

WHY THIS EXISTS
---------------
The Stage-2 enumeration head currently trains on DENTEX `quadrant_enumeration` alone: 634
images, 18,095 teeth. Tufts carries per-tooth numbering that no script in this repo has ever
used — `Segmentation/teeth_bbox.json`, 1,000 images, **25,201 usable permanent teeth**, 1.4x
DENTEX's count from a different continent and a different machine population. The existing
`convert_tufts_to_yolo.py` (archived) read the same file but threw the numbering away
(`nc: 1, names: ['tooth']`), because it was building a detector, not an enumerator.

THREE THINGS ABOUT THIS DATA THAT ARE EASY TO GET WRONG
-------------------------------------------------------
1. **The numbering is left-right MIRRORED** relative to standard Universal. Tufts "1" is the
   upper-LEFT third molar (FDI 28), not the upper-right (18). Established three independent
   ways — see `src.utils.fdi_converter.tufts_title_to_fdi` and RESULTS_LOG 2026-08-25h.
   Reading the titles as plain Universal would train the head on systematically side-swapped
   labels, which is worse than not training on it at all.

2. **The annotations are in PORTRAIT coordinates**, matching `Radiographs_rotated/`
   (840x1615), not the upright `Radiographs/` (1615x840). Crops here are cut from the
   UPRIGHT image, because Stage 2 reasons about upright anatomy — feeding it rotated boxes
   scored 5.9% quadrant accuracy, below the 25% of guessing (`src/orientation.py`). The
   inverse transform is CCW's, verified pixelwise across all 1,000 pairs.

3. **Degenerate 1x1 boxes mean "tooth absent"**, not "tooth at this pixel" — 66 of them.
   They are dropped, exactly as the archived converter dropped them.

SPLIT — reuse the frozen one, do not re-randomise
--------------------------------------------------
`split_v1.csv` (700/150/150, image-level) is the split `tooth-detector-a100-1024-v1.0` was
trained on. Re-shuffling here would put images from the detector's *test* set into the head's
*train* set, quietly contaminating every end-to-end Tufts number this pipeline reports. So
the frozen split is reused verbatim.

Two byte-identical duplicate pairs exist inside Tufts, and one of them (`590.JPG` test /
`591.JPG` train) straddles the split — a real, previously-undocumented leak in split_v1.
Within each duplicate group one representative is kept, preferring the most protected split
(test > val > train), and the rest are dropped.

Deciduous teeth (738, in 82 mixed-dentition images) are excluded: the head's output space is
the 32 permanent codes. Their images are still used for the permanent teeth they contain, and
flagged in the manifest so the choice can be ablated later rather than silently baked in.

Usage:
    python scripts/tufts/build_enumeration_crops.py --dry-run
    python scripts/tufts/build_enumeration_crops.py
"""

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.crop_generator import apply_bbox_jitter, compute_expanded_bbox  # noqa: E402
from src.utils.fdi_converter import is_deciduous, tufts_title_to_fdi     # noqa: E402

ARCHIVE = REPO_ROOT / "_repo_archive/datasets_workspace"
DEF_IMAGES = ARCHIVE / "Radiographs"                      # UPRIGHT 1615x840
DEF_BBOX = REPO_ROOT / "data/tufts/ZIP/Segmentation/Segmentation/teeth_bbox.json"
DEF_SPLIT = ARCHIVE / "outputs/eda_tufts/split_v1.csv"
DEF_OUT = REPO_ROOT / "data/tufts/enumeration_v1"

# Above this share of degenerate crops the source images are in the wrong coordinate frame.
# Observed: 0.04% correct vs 23% rotated 90deg. Anything near the upper figure is unusable.
MAX_DEGENERATE_RATE = 0.02
CROP = 224
SEED = 42
MIN_BOX = 2                       # below this a box is a placeholder, not a tooth
SPLIT_RANK = {"test": 3, "val": 2, "train": 1}


def upright_box(bbox_portrait, img_w):
    """Tufts portrait (x1,y1,x2,y2) -> upright (x, y, w, h).

    `Radiographs_rotated` was produced by rotating `Radiographs` 90 deg COUNTER-clockwise
    (verified: 1000/1000 pairs, mean|diff| ~0.3 = JPEG noise). The CCW inverse from
    `src/orientation.py` is (x, y) -> (W-1-y, x), where W is the UPRIGHT width. Both corners
    are mapped then min/max'd — a 90 deg rotation sends the top-left corner elsewhere, so
    reusing the original corner order yields an inverted box.
    """
    x1, y1, x2, y2 = bbox_portrait
    ax, ay = (img_w - 1) - y1, x1
    bx, by = (img_w - 1) - y2, x2
    X1, X2 = min(ax, bx), max(ax, bx)
    Y1, Y2 = min(ay, by), max(ay, by)
    return X1, Y1, X2 - X1, Y2 - Y1


def load_split(path):
    split_of = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            split_of[Path(row["filename"]).stem] = row["split"].strip()
    return split_of


def resolve_duplicates(stems, images_dir, split_of):
    """Byte-identical images -> keep one representative, preferring the protected split."""
    groups = defaultdict(list)
    for stem in stems:
        p = images_dir / f"{stem}.JPG"
        if p.exists():
            groups[hashlib.md5(p.read_bytes()).hexdigest()].append(stem)
    dropped = {}
    for members in groups.values():
        if len(members) < 2:
            continue
        keep = sorted(members, key=lambda s: (-SPLIT_RANK.get(split_of.get(s), 0), s))[0]
        for m in members:
            if m != keep:
                dropped[m] = keep
    return dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=Path, default=DEF_IMAGES)
    ap.add_argument("--bbox", type=Path, default=DEF_BBOX)
    ap.add_argument("--split", type=Path, default=DEF_SPLIT)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--expand", type=float, default=1.5)
    ap.add_argument("--jitter-copies", type=int, default=1,
                    help="extra jittered copies per training tooth (0 = none)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for p in (args.images, args.bbox, args.split):
        if not p.exists():
            sys.exit(f"missing input: {p}")

    records = json.loads(args.bbox.read_text())
    split_of = load_split(args.split)
    stems = [Path(r["External ID"]).stem for r in records]

    missing_split = [s for s in stems if s not in split_of]
    if missing_split:
        sys.exit(f"{len(missing_split)} images have no split entry, e.g. {missing_split[:5]}")

    dropped = resolve_duplicates(stems, args.images, split_of)
    if dropped:
        print("byte-identical duplicates resolved (dropped -> kept):")
        for d, k in sorted(dropped.items()):
            print(f"  {d}.JPG ({split_of[d]})  ->  {k}.JPG ({split_of[k]})")

    # -- plan the build before writing anything -------------------------------
    planned = defaultdict(Counter)
    skipped = Counter()
    mixed_dentition = set()
    for rec in records:
        stem = Path(rec["External ID"]).stem
        if stem in dropped:
            skipped["duplicate_image"] += 1
            continue
        split = split_of[stem]
        for o in rec["Label"]["objects"]:
            x1, y1, x2, y2 = o["bounding box"]
            if x2 - x1 < MIN_BOX or y2 - y1 < MIN_BOX:
                skipped["degenerate_absent_tooth"] += 1
                continue
            title = str(o["title"]).strip()
            if is_deciduous(title):
                skipped["deciduous"] += 1
                mixed_dentition.add(stem)
                continue
            fdi = tufts_title_to_fdi(title)
            if fdi is None:
                skipped["unmappable_title"] += 1
                continue
            planned[split][fdi] += 1

    print(f"\nimages: {len(records)}  (dropped {len(dropped)} duplicate)")
    for s in ("train", "val", "test"):
        c = planned[s]
        if not c:
            continue
        print(f"  {s:5s}: {sum(c.values()):6,} teeth, {len(c)}/32 classes, "
              f"min/max per class {min(c.values())}/{max(c.values())}")
    print("  skipped:", dict(skipped))
    print(f"  mixed-dentition images (contain deciduous): {len(mixed_dentition)}")

    all_codes = {q * 10 + p for q in (1, 2, 3, 4) for p in range(1, 9)}
    for s in ("train", "val", "test"):
        if not planned[s]:
            continue
        miss = sorted(all_codes - set(planned[s]))
        if miss:
            print(f"  WARNING {s}: {len(miss)} FDI classes absent: {miss}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    random.seed(args.seed)        # apply_bbox_jitter draws from the global RNG
    args.out.mkdir(parents=True, exist_ok=True)
    rows, stats = [], Counter()

    for n, rec in enumerate(records, 1):
        stem = Path(rec["External ID"]).stem
        if stem in dropped:
            continue
        split = split_of[stem]
        img_path = args.images / f"{stem}.JPG"
        img = cv2.imread(str(img_path))
        if img is None:
            stats["image_unreadable"] += 1
            continue
        H, W = img.shape[:2]

        for idx, o in enumerate(rec["Label"]["objects"]):
            bx = o["bounding box"]
            if bx[2] - bx[0] < MIN_BOX or bx[3] - bx[1] < MIN_BOX:
                continue
            title = str(o["title"]).strip()
            fdi = tufts_title_to_fdi(title)
            if fdi is None:
                continue
            x, y, w, h = upright_box(bx, W)
            if w < MIN_BOX or h < MIN_BOX:
                stats["degenerate_after_rotation"] += 1
                continue

            variants = [(x, y, w, h, "")]
            if split == "train" and args.jitter_copies:
                for k in range(args.jitter_copies):
                    variants.append(apply_bbox_jitter(x, y, w, h, W, H) + (f"_j{k}",))

            for vx, vy, vw, vh, tag in variants:
                cx1, cy1, cx2, cy2 = compute_expanded_bbox(
                    vx, vy, vw, vh, W, H, fw=args.expand, fh=args.expand)
                cx1, cy1, cx2, cy2 = int(cx1), int(cy1), int(cx2), int(cy2)
                if cx2 - cx1 < 4 or cy2 - cy1 < 4:
                    stats["degenerate_crop"] += 1
                    continue
                crop = cv2.resize(img[cy1:cy2, cx1:cx2], (CROP, CROP))
                d = args.out / split / str(fdi)
                d.mkdir(parents=True, exist_ok=True)
                name = f"{stem}_t{idx}{tag}.png"
                if not cv2.imwrite(str(d / name), crop):
                    stats["write_failed"] += 1
                    continue
                stats[split] += 1
                rows.append({
                    "crop": name, "split": split, "source_image": f"{stem}.JPG",
                    "tufts_title": title, "fdi": fdi,
                    "quadrant": fdi // 10, "position": fdi % 10,
                    "jittered": int(bool(tag)),
                    "mixed_dentition_image": int(stem in mixed_dentition),
                    # Positional features, normalised in the UPRIGHT frame so they mean the
                    # same thing as DENTEX's. Taken from the JITTERED box, not the clean one:
                    # at inference the crop and these features both come from the same
                    # detector box, so clean features beside a jittered crop would teach the
                    # head to trust a precision the pipeline never delivers.
                    "cx": round((vx + vw / 2) / W, 5), "cy": round((vy + vh / 2) / H, 5),
                    "bw": round(vw / W, 5), "bh": round(vh / H, 5),
                })
        if n % 200 == 0:
            print(f"  {n}/{len(records)} images…", flush=True)

    if not rows:
        sys.exit("no crops written — refusing to write an empty manifest")

    man = args.out / "enumeration_manifest.csv"
    with open(man, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    (args.out / "meta.json").write_text(json.dumps({
        "source_images": str(args.images), "source_annotations": str(args.bbox),
        "split_source": str(args.split), "split_by": "image (frozen split_v1, reused)",
        "expand": args.expand, "crop": CROP, "seed": args.seed,
        "jitter_copies": args.jitter_copies,
        "fdi_mapping": ("tufts_title_to_fdi = mirror_quadrant(universal_to_fdi(title)); "
                        "Tufts numbering is left-right mirrored, RESULTS_LOG 2026-08-25h"),
        "coordinate_transform": ("annotations are portrait (840x1615); crops cut from upright "
                                 "1615x840 via the CCW inverse (x,y)->(W-1-y,x)"),
        "excluded": {"deciduous_teeth": skipped["deciduous"],
                     "degenerate_absent_tooth": skipped["degenerate_absent_tooth"],
                     "duplicate_images": sorted(dropped)},
        "mixed_dentition_images": len(mixed_dentition),
        "counts": dict(stats),
    }, indent=2) + "\n")

    print("\nwrite stats:", dict(stats))
    print(f"manifest: {man}  ({len(rows):,} rows)")

    # ---------------------------------------------------------------- geometry guard
    # Added 28 Aug 2026 after this script silently produced a misaligned dataset.
    #
    # Every Tufts radiograph on the Windows machine is 840x1615 -- rotated 90 degrees from the
    # 1615x840 frame teeth_bbox.json uses. Cropping with the wrong orientation does NOT error:
    # it wrote 28,171/2,249 train/val instead of the documented 35,248/3,721 and rejected
    # **10,087 crops (23%)** as degenerate. The run looked normal.
    #
    # `_tufts_align.image_orientation_score` did not catch it and cannot: it scores mean
    # brightness inside the annotation boxes, and because teeth sit centrally BOTH orientations
    # score above 1.0 (1.040 rotated vs 1.021 upright). It was built to catch a 180 degree flip,
    # where that signal does work.
    #
    # The degenerate rate separates the two cases by three orders of magnitude -- 23% vs 0.04% --
    # so that is what is enforced here. It is agnostic to the *cause*: any future geometry
    # mismatch, whatever its origin, trips the same wire.
    n_written = sum(stats[s] for s in ("train", "val", "test") if s in stats)
    n_degen = stats.get("degenerate_crop", 0) + stats.get("degenerate_after_rotation", 0)
    rate = n_degen / max(n_written + n_degen, 1)
    print(f"geometry guard: {n_degen:,} degenerate of {n_written + n_degen:,} ({rate:.2%})")
    if rate > MAX_DEGENERATE_RATE:
        raise SystemExit(
            f"\nGEOMETRY GUARD FAILED: {rate:.1%} of crops are degenerate "
            f"(limit {MAX_DEGENERATE_RATE:.0%}).\n"
            f"The images in --images are almost certainly not in the coordinate frame "
            f"teeth_bbox.json uses.\n"
            f"Pass the UPRIGHT copy (1615x840) that matches teeth_bbox.json. On this clone "
            f"that is data/tufts/ZIP/Radiographs_upright_fixed -- NOT Radiographs_upright, "
            f"which is 180 degrees out and produced a corpus scoring 11.5% FDI-exact where the "
            f"published figure is 71.5% (RESULTS_LOG 2026-09-06c). Verify with "
            f"scripts/eval/tufts_crop_frame_check.py after building.\n"
            f"Nothing written here should be trained on. See RESULTS_LOG.md 2026-08-28c.")


if __name__ == "__main__":
    main()
