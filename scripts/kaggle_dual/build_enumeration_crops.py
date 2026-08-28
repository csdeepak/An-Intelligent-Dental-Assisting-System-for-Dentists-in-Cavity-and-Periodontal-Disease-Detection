#!/usr/bin/env python
"""
Build FDI-labelled tooth crops from the Kaggle *dual-labeled* corpus — a THIRD training source.

WHY A THIRD CORPUS
------------------
The Stage-2 head currently trains on DENTEX + Tufts. Two corpora make "it generalises" an
assertion with one degree of freedom; three make it a claim. This set adds **500 images /
13,192 annotated teeth** at ~26.4 teeth per image (near-full dentitions), from a different
population again.

WHAT WAS VERIFIED BEFORE WRITING THIS
--------------------------------------
1. **The numbering is standard FDI, read as written.** Not assumed — measured. Tufts *looked*
   like plain Universal and was left-right mirrored, which would have trained side-swapped
   labels. `verify_fdi_convention.py` ran the v2 head over 915 teeth as an independent arbiter:
   **80.3% agreement direct vs 1.7% mirrored**. 80.3% is essentially the arbiter's own ceiling
   (82.6% FDI-exact on detected teeth), so this is both a convention check and a quality check.
2. **`transfer.md` says this corpus is 2,000 images. It is 500.** The Kaggle dataset publishes
   2,066 label files but only 500 images (2,566 files total, confirmed by full API pagination —
   the download is complete, the images simply are not all there). 1,566 labels have no image
   and are unusable. The plan's figure was wrong and is corrected here.
3. **Images vary in size** (2940x1435, 2440x1280, 943x473 seen), unlike DENTEX and Tufts. Every
   box is therefore scaled against its own image, never a constant.

CROP CONTRACT — identical to the other two corpora, deliberately
-----------------------------------------------------------------
1.5x symmetric expansion, 224x224, `<split>/<fdi>/` layout, +/-15% jitter on train only. The
head must see one input distribution; a third corpus cropped to a different contract would
train a head that is worse, in a way that looks like the new data being unhelpful.

Label `91` (24 of 13,192, 0.18%) is not a valid FDI code and is dropped.

Usage:
    python scripts/kaggle_dual/build_enumeration_crops.py --dry-run
    python scripts/kaggle_dual/build_enumeration_crops.py
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

DEF_IMAGES = REPO_ROOT / "data/kaggle_dual/images1"
DEF_LABELS = REPO_ROOT / "data/kaggle_dual/labels"
DEF_OUT = REPO_ROOT / "data/kaggle_dual/enumeration_v1"

CROP = 224
SEED = 42
MIN_BOX = 2
MAX_DEGENERATE_RATE = 0.02          # same guard as the Tufts builder; see RESULTS_LOG 2026-08-28c
VALID = {f"{q}{p}" for q in (1, 2, 3, 4) for p in range(1, 9)}


def poly_bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def make_split(stems, seed=SEED, frac=(0.70, 0.15)):
    """Image-level split, fixed seed. Image-level because two crops from one radiograph are not
    independent -- a tooth-level split would leak the same mouth across train and test."""
    r = random.Random(seed)
    s = sorted(stems)
    r.shuffle(s)
    n = len(s)
    n_tr, n_va = int(n * frac[0]), int(n * frac[1])
    out = {}
    for i, stem in enumerate(s):
        out[stem] = "train" if i < n_tr else ("val" if i < n_tr + n_va else "test")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=Path, default=DEF_IMAGES)
    ap.add_argument("--labels", type=Path, default=DEF_LABELS)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--expand", type=float, default=1.5)
    ap.add_argument("--jitter-copies", type=int, default=1)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for p in (args.images, args.labels):
        if not p.exists():
            sys.exit(f"missing input: {p}")

    stems = sorted({p.stem for p in args.images.glob("*.png")}
                   & {p.stem for p in args.labels.glob("*.json")})
    if not stems:
        sys.exit("no image/label pairs found")

    # Byte-identical duplicates would leak across the split, as one pair did in Tufts split_v1.
    seen, dupes = {}, {}
    for stem in stems:
        h = hashlib.md5((args.images / f"{stem}.png").read_bytes()).hexdigest()
        if h in seen:
            dupes[stem] = seen[h]
        else:
            seen[h] = stem
    if dupes:
        print(f"byte-identical duplicate images dropped: {len(dupes)}")
    stems = [s for s in stems if s not in dupes]

    split_of = make_split(stems, args.seed)
    planned, skipped = defaultdict(Counter), Counter()
    for stem in stems:
        d = json.loads((args.labels / f"{stem}.json").read_text())
        for sh in d.get("shapes", []):
            code = str(sh["label"]).strip()
            if code not in VALID:
                skipped["invalid_label"] += 1
                continue
            x, y, w, h = poly_bbox(sh["points"])
            if w < MIN_BOX or h < MIN_BOX:
                skipped["degenerate_box"] += 1
                continue
            planned[split_of[stem]][code] += 1

    print(f"images {len(stems)}  ->  " + "  ".join(
        f"{s} {sum(planned[s].values()):,} teeth / {len(planned[s])} classes"
        for s in ("train", "val", "test")))
    print("  skipped:", dict(skipped))
    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    stats = Counter()
    rows = []
    for i, stem in enumerate(stems, 1):
        img = cv2.imread(str(args.images / f"{stem}.png"), cv2.IMREAD_COLOR)
        if img is None:
            stats["image_unreadable"] += 1
            continue
        H, W = img.shape[:2]
        split = split_of[stem]
        d = json.loads((args.labels / f"{stem}.json").read_text())
        for k, sh in enumerate(d.get("shapes", [])):
            code = str(sh["label"]).strip()
            if code not in VALID:
                continue
            x, y, w, h = poly_bbox(sh["points"])
            if w < MIN_BOX or h < MIN_BOX:
                continue
            variants = [(x, y, w, h, "")]
            if split == "train" and args.jitter_copies:
                for j in range(args.jitter_copies):
                    variants.append(apply_bbox_jitter(x, y, w, h, W, H) + (f"_j{j}",))
            for vx, vy, vw, vh, tag in variants:
                cx1, cy1, cx2, cy2 = compute_expanded_bbox(
                    vx, vy, vw, vh, W, H, fw=args.expand, fh=args.expand)
                cx1, cy1, cx2, cy2 = int(cx1), int(cy1), int(cx2), int(cy2)
                if cx2 - cx1 < 4 or cy2 - cy1 < 4:
                    stats["degenerate_crop"] += 1
                    continue
                crop = cv2.resize(img[cy1:cy2, cx1:cx2], (CROP, CROP))
                od = args.out / split / code
                od.mkdir(parents=True, exist_ok=True)
                name = f"{stem}_a{k}{tag}.png"
                if not cv2.imwrite(str(od / name), crop):
                    stats["write_failed"] += 1
                    continue
                stats[split] += 1
                rows.append({"crop": name, "split": split, "source_image": f"{stem}.png",
                             "ann_id": k, "fdi": code, "quadrant": code[0], "position": code[1],
                             "jittered": int(bool(tag)),
                             "cx": round((x + w / 2) / W, 5), "cy": round((y + h / 2) / H, 5),
                             "bw": round(w / W, 5), "bh": round(h / H, 5)})
        if i % 100 == 0:
            print(f"  {i}/{len(stems)} images", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    man = args.out / "enumeration_manifest.csv"
    with open(man, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    (args.out / "build_meta.json").write_text(json.dumps({
        "source_images": str(args.images), "source_labels": str(args.labels),
        "images_used": len(stems), "duplicates_dropped": len(dupes),
        "expand": args.expand, "crop": CROP, "seed": args.seed,
        "fdi_convention": "standard, verified 80.3% direct vs 1.7% mirrored by the v2 head",
        "counts": dict(stats), "skipped": dict(skipped),
    }, indent=2) + "\n")

    print("\nwrite stats:", dict(stats))
    print(f"manifest: {man}  ({len(rows):,} rows)")

    n_written = sum(stats[s] for s in ("train", "val", "test") if s in stats)
    n_degen = stats.get("degenerate_crop", 0)
    rate = n_degen / max(n_written + n_degen, 1)
    print(f"geometry guard: {n_degen:,} degenerate of {n_written + n_degen:,} ({rate:.2%})")
    if rate > MAX_DEGENERATE_RATE:
        raise SystemExit(f"GEOMETRY GUARD FAILED: {rate:.1%} degenerate (limit "
                         f"{MAX_DEGENERATE_RATE:.0%}) -- boxes and images disagree, do not train.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
