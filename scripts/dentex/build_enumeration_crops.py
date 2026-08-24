"""
Build the training set for the Stage-2 enumeration head: tooth crops labelled with FDI.

WHY THIS EXISTS
---------------
Positional (rank-order) FDI assignment was measured at **22.9% end-to-end exact accuracy** on
the clean 164-image set (936 teeth), with a ceiling of **66.3%** even when a quadrant is fully
detected (RESULTS_LOG 2026-08-22j, 2026-08-24a; the earlier 28.0%/68.7% figures came from a
leaked evaluation set). The ceiling is structural: eight detected teeth are not
positions 1-8, they are eight teeth that survived extraction, and no amount of sorting or
detector improvement can recover which is which. The replacement is a per-tooth classifier
that does not assume a contiguous arch.

DATA — and why this subset is the right one
-------------------------------------------
DENTEX `training_data/quadrant_enumeration/`: 634 images, **18,095 teeth**, each labelled with
quadrant and position. Verified before use rather than assumed, exactly as the disease subset
was: FDI = (category_id_1 + 1) * 10 + (category_id_2 + 1), confirmed spatially —
Q1 mean x=0.400 vs Q2 x=0.606 (patient-right on image-left), Q1 above Q3, and mean |x-0.5|
rising monotonically 0.015 -> 0.227 across positions 1-8. All 32 classes present,
341-630 examples each.

**These are NOT disjoint from `disease/`.** An earlier version of this docstring claimed they
were, generalising a verified fact about the disease *subset* (705 images, RESULTS_LOG
2026-08-21m) to `disease/`, which is a different folder. **85 of its 250 images are
byte-identical to images here.** They are listed in `data/dentex/disease_leaked_images.json`
and excluded by `scripts/eval/validate_fdi_assignment.py`; evaluation runs on the remaining
164. See RESULTS_LOG 2026-08-22j.

CROP GEOMETRY
-------------
1.5x expansion around the tooth box. Context is not optional for this task: distinguishing a
first from a second molar depends partly on its neighbours, and a tight crop discards that.
Expansion is clipped at the image edge, so crops near the arch ends are not padded.

At inference the crops come from *detector* boxes, not ground-truth boxes, so training crops
get +/-15% jitter (`src.crop_generator.apply_bbox_jitter`) to emulate that shift. Without it
the head would be trained on a box distribution it never sees in the pipeline.

Splitting is **by image**, never by tooth: two crops from the same radiograph must not land on
opposite sides of a split.

Usage:
    python scripts/dentex/build_enumeration_crops.py --dry-run
    python scripts/dentex/build_enumeration_crops.py
"""

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.crop_generator import apply_bbox_jitter, compute_expanded_bbox  # noqa: E402

DEF_ROOT = Path.home() / "Downloads/Capstone/DENTEX/training_data/quadrant_enumeration"
DEF_OUT = REPO_ROOT / "data/dentex/enumeration_v1"
CROP = 224
SEED = 42
FRACTIONS = {"train": 0.85, "val": 0.15}     # test comes from disease/, not from here


def fdi_from(ann):
    """Verified mapping — see module docstring."""
    return (ann["category_id_1"] + 1) * 10 + (ann["category_id_2"] + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEF_ROOT)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--expand", type=float, default=1.5)
    ap.add_argument("--jitter-copies", type=int, default=1,
                    help="extra jittered copies per training tooth (0 = none)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    coco = json.loads((args.root / "train_quadrant_enumeration.json").read_text())
    id2f = {i["id"]: i["file_name"] for i in coco["images"]}
    dims = {i["id"]: (i["width"], i["height"]) for i in coco["images"]}

    # sanity-check the label mapping rather than trusting it
    assert len(coco["categories_1"]) == 4 and len(coco["categories_2"]) == 8, \
        "unexpected category structure — re-verify the FDI mapping before building"

    by_image = defaultdict(list)
    for a in coco["annotations"]:
        by_image[a["image_id"]].append(a)

    rng = random.Random(args.seed)
    imgs = sorted(by_image)
    rng.shuffle(imgs)
    n_tr = int(len(imgs) * FRACTIONS["train"])
    split_of = {i: ("train" if k < n_tr else "val") for k, i in enumerate(imgs)}

    counts = defaultdict(Counter)
    for iid, anns in by_image.items():
        for a in anns:
            counts[split_of[iid]][fdi_from(a)] += 1
    print(f"images {len(imgs)}  ->  train {n_tr}  val {len(imgs)-n_tr}")
    for s in ("train", "val"):
        c = counts[s]
        print(f"  {s:5s}: {sum(c.values()):6,} teeth, {len(c)} classes, "
              f"min/max per class {min(c.values())}/{max(c.values())}")
    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    stats = Counter()
    for n, (iid, anns) in enumerate(sorted(by_image.items()), 1):
        split = split_of[iid]
        img = cv2.imread(str(args.root / "xrays" / id2f[iid]))
        if img is None:
            stats["image_missing"] += 1
            continue
        H, W = img.shape[:2]
        for a in anns:
            x, y, w, h = a["bbox"]
            fdi = fdi_from(a)
            variants = [(x, y, w, h, "")]
            if split == "train" and args.jitter_copies:
                for k in range(args.jitter_copies):
                    variants.append(apply_bbox_jitter(x, y, w, h, W, H) + (f"_j{k}",))
            for vx, vy, vw, vh, tag in variants:
                cx1, cy1, cx2, cy2 = compute_expanded_bbox(
                    vx, vy, vw, vh, W, H, fw=args.expand, fh=args.expand)
                cx1, cy1, cx2, cy2 = int(cx1), int(cy1), int(cx2), int(cy2)
                if cx2 - cx1 < 4 or cy2 - cy1 < 4:
                    stats["degenerate"] += 1
                    continue
                crop = cv2.resize(img[cy1:cy2, cx1:cx2], (CROP, CROP))
                d = args.out / split / str(fdi)
                d.mkdir(parents=True, exist_ok=True)
                name = f"{Path(id2f[iid]).stem}_a{a['id']}{tag}.png"
                if not cv2.imwrite(str(d / name), crop):
                    stats["write_failed"] += 1
                    continue
                stats[f"{split}"] += 1
                rows.append({
                    "crop": name, "split": split, "source_image": id2f[iid],
                    "ann_id": a["id"], "fdi": fdi,
                    "quadrant": a["category_id_1"] + 1, "position": a["category_id_2"] + 1,
                    "jittered": int(bool(tag)),
                    # positional features — worth +3.2 points of laterality and +2.8 FDI
                    # exact (measured, RESULTS_LOG 2026-08-24c). NOT the decisive signal an
                    # earlier comment here claimed: the image alone recovers side at 96.3%.
                    # These come from the JITTERED box (vx,vy,vw,vh), not the ground-truth
                    # one: at inference both the crop and these features are derived from the
                    # same detector box, so pairing a jittered crop with clean features would
                    # train the head to trust a precision the pipeline never delivers.
                    "cx": round((vx + vw / 2) / W, 5), "cy": round((vy + vh / 2) / H, 5),
                    "bw": round(vw / W, 5), "bh": round(vh / H, 5),
                })
        if n % 100 == 0:
            print(f"  {n}/{len(by_image)} images…", flush=True)

    man = args.out / "enumeration_manifest.csv"
    with open(man, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    (args.out / "meta.json").write_text(json.dumps({
        "source": str(args.root), "expand": args.expand, "crop": CROP, "seed": args.seed,
        "jitter_copies": args.jitter_copies, "split_by": "image",
        "fdi_mapping": "(category_id_1+1)*10 + (category_id_2+1), verified spatially",
        "counts": dict(stats),
    }, indent=2) + "\n")
    print("\nwrite stats:", dict(stats))
    print(f"manifest: {man}  ({len(rows):,} rows)")


if __name__ == "__main__":
    main()
