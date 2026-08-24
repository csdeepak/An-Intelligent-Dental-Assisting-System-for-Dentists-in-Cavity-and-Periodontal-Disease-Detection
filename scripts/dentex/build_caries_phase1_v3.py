"""
Rebuild the caries Phase-1 gate's training set WITH A REAL NEGATIVE CLASS.

THE DEFECT THIS FIXES
---------------------
The gate in `models/07_caries_cascade/` was trained on `phase1_legacy`, whose rule is
`category_id_3 in [1,3] -> caries, else -> no_caries`, applied to an annotation file in which
**every annotation is a diseased tooth**. So `no_caries` was exactly Impacted + Periapical
Lesion (762 train / 49 val) and contained **NO HEALTHY TEETH**. The assembled pipeline feeds
the gate every tooth the detector finds -- overwhelmingly healthy -- a population it has never
seen. Measured in situ (RESULTS_LOG 2026-08-24f): it calls **84.9%** of 299 detected teeth
carious against 35 annotated, a ~7x over-call. No pipeline caries number means anything until
this is fixed.

WHY THE PREVIOUS ATTEMPT FAILED, AND WHY THIS ONE DOES NOT
-----------------------------------------------------------
A `phase1_corrected` tree was built once by joining `quadrant_enumeration` to the disease
subset **on file_name**. That was invalid: the subsets number their files independently, so
`train_0.png` in one is a different patient from `train_0.png` in the other. All 15,531 crops
were meaningless (RESULTS_LOG 2026-08-21m).

That entry then concluded the subsets "cover disjoint sets of patients" and that healthy teeth
are "NOT derivable from DENTEX". **The first half is right; the second half is too strong.**
The subsets share **260 byte-identical images under DIFFERENT filenames**. Joining on
**MD5 of the image bytes** -- not on filename -- recovers them exactly, and for those 260 both
annotation sets describe the same pixels in the same coordinate frame.

THE JOIN IS VERIFIED BY A FALSIFIABLE TEST, NOT BY ASSERTION
------------------------------------------------------------
For a shared image, a disease annotation and an enumeration annotation covering the same tooth
must carry the **same (quadrant, position)**. Measured over all 260:

    agree 1255   disagree 22   ->  98.28% FDI agreement
    image dimensions match on 260/260

If these were different patients, agreement would sit near chance (~3% over 32 classes). This
is the check the filename join would have failed, and it is why that join was caught only
after the crops were built.

LABELLING RULE
--------------
Tooth boxes come from `quadrant_enumeration` (the COMPLETE dentition, ~28.7 teeth/image).
Disease status comes from the disease subset, matched by IoU:

    IoU >= 0.50   take the disease label:  Caries | Deep Caries -> `caries`
                                           Impacted | Periapical -> `no_caries`
    0.10 < IoU < 0.50   AMBIGUOUS -> EXCLUDED (856 teeth, 11.5%). Not called healthy.
    IoU <= 0.10   no disease annotation touches it -> `no_caries` (healthy)

The middle band is dropped rather than resolved. A partially-overlapped tooth is exactly the
case where "healthy" would be a guess, and a diseased tooth mislabelled healthy is the error
this whole script exists to remove.

THE ASSUMPTION THIS RESTS ON, STATED PLAINLY
--------------------------------------------
**A tooth with no disease annotation is PRESUMED not-diseased.** DENTEX's disease subset
annotates only diseased teeth, so absence of an annotation is the only healthy signal
available -- but it is absence of evidence. If the annotators missed a lesion, that tooth
enters the negative class as a false negative. This is label noise of unknown size, it cannot
be measured inside DENTEX, and it must be reported with any result from this dataset.

Splits are INHERITED from `data/dentex/splits_v2.json` via the same MD5 map, so this tree's
test set is a subset of `phase1_legacy`'s test set and the two remain comparable.

Usage:
    python scripts/dentex/build_caries_phase1_v3.py --dry-run
    python scripts/dentex/build_caries_phase1_v3.py
"""

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DEF_ENUM = Path.home() / "Downloads/Capstone/DENTEX/training_data/quadrant_enumeration"
DEF_DISEASE = Path.home() / "Downloads/Capstone/DENTEX/training_data/quadrant-enumeration-disease"
DEF_SPLITS = REPO_ROOT / "data/dentex/splits_v2.json"
DEF_OUT = REPO_ROOT / "data/dentex/crops_v3_phase1"

CROP = 224
IOU_MATCH = 0.50        # >= this: the disease annotation describes this tooth
IOU_AMBIGUOUS = 0.10    # between the two: excluded, never called healthy
DISEASE = {0: "impacted", 1: "caries", 2: "periapical", 3: "deep_caries"}
CARIOUS = {"caries", "deep_caries"}


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def iou_xywh(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def tight_crop(img, bbox):
    """The caries crop contract: floor the near corner, ceil the far edge, clip, resize 224."""
    H, W = img.shape[:2]
    x, y, w, h = bbox
    x1, y1 = max(0, math.floor(x)), max(0, math.floor(y))
    x2, y2 = min(W, math.ceil(x + w)), min(H, math.ceil(y + h))
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None
    return cv2.resize(img[y1:y2, x1:x2], (CROP, CROP))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enum-root", type=Path, default=DEF_ENUM)
    ap.add_argument("--disease-root", type=Path, default=DEF_DISEASE)
    ap.add_argument("--splits", type=Path, default=DEF_SPLITS)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    en = json.loads((args.enum_root / "train_quadrant_enumeration.json").read_text())
    di = json.loads((args.disease_root / "train_quadrant_enumeration_disease.json").read_text())

    print("hashing images to join the two subsets (filenames are NOT comparable) …")
    en_by_hash = {md5(args.enum_root / "xrays" / i["file_name"]): i for i in en["images"]
                  if (args.enum_root / "xrays" / i["file_name"]).exists()}
    di_by_hash = {md5(args.disease_root / "xrays" / i["file_name"]): i for i in di["images"]
                  if (args.disease_root / "xrays" / i["file_name"]).exists()}
    shared = sorted(set(en_by_hash) & set(di_by_hash))
    print(f"  enumeration {len(en_by_hash)}   disease {len(di_by_hash)}   SHARED {len(shared)}")
    if not shared:
        raise SystemExit("no shared images — the join produced nothing; do not proceed")

    en_anns, di_anns = defaultdict(list), defaultdict(list)
    for a in en["annotations"]:
        en_anns[a["image_id"]].append(a)
    for a in di["annotations"]:
        di_anns[a["image_id"]].append(a)

    # Re-run the falsifiable check every build. If a future DENTEX release changes either file,
    # this is what catches it — silently building on a bad join is the failure mode here.
    agree = disagree = 0
    for h in shared:
        E, D = en_anns[en_by_hash[h]["id"]], di_anns[di_by_hash[h]["id"]]
        for d in D:
            best = max(E, key=lambda e: iou_xywh(e["bbox"], d["bbox"]), default=None)
            if best is None or iou_xywh(best["bbox"], d["bbox"]) < IOU_MATCH:
                continue
            same = (best["category_id_1"], best["category_id_2"]) == \
                   (d["category_id_1"], d["category_id_2"])
            agree += same
            disagree += not same
    rate = agree / max(agree + disagree, 1)
    print(f"  join check — FDI agreement on matched teeth: {agree}/{agree+disagree} = {rate:.2%}")
    if rate < 0.90:
        raise SystemExit(f"FDI agreement {rate:.2%} is too low — the MD5 join is not sound; stop")

    split_of_name = {e["file_name"]: sp
                     for sp, lst in json.loads(args.splits.read_text())["splits"].items()
                     for e in lst}
    split_of_hash = {h: split_of_name[di_by_hash[h]["file_name"]] for h in shared
                     if di_by_hash[h]["file_name"] in split_of_name}
    print(f"  splits inherited from {args.splits.name}: "
          f"{dict(Counter(split_of_hash.values()))}")

    rows, stats = [], Counter()
    for n, h in enumerate(shared, 1):
        ei, dii = en_by_hash[h], di_by_hash[h]
        split = split_of_hash.get(h)
        if split is None:
            stats["image_unsplit"] += 1
            continue
        D = di_anns[dii["id"]]
        img = None if args.dry_run else cv2.imread(str(args.enum_root / "xrays" / ei["file_name"]))
        if not args.dry_run and img is None:
            stats["image_unreadable"] += 1
            continue
        for e in en_anns[ei["id"]]:
            best_iou, best_d = 0.0, None
            for d in D:
                v = iou_xywh(e["bbox"], d["bbox"])
                if v > best_iou:
                    best_iou, best_d = v, d
            if best_iou >= IOU_MATCH:
                subtype = DISEASE[best_d["category_id_3"]]
                label = "caries" if subtype in CARIOUS else "no_caries"
            elif best_iou > IOU_AMBIGUOUS:
                stats["excluded_ambiguous"] += 1
                continue
            else:
                subtype, label = "healthy", "no_caries"
            stats[f"{split}/{label}"] += 1
            stats[f"subtype/{subtype}"] += 1
            name = f"{Path(ei['file_name']).stem}_e{e['id']}.png"
            rows.append({"crop": name, "split": split, "label": label, "subtype": subtype,
                         "source_image_md5": h,
                         "enum_file": ei["file_name"], "disease_file": dii["file_name"],
                         "ann_id": e["id"], "iou_to_disease": round(best_iou, 4),
                         "fdi": (e["category_id_1"] + 1) * 10 + (e["category_id_2"] + 1)})
            if args.dry_run:
                continue
            crop = tight_crop(img, e["bbox"])
            if crop is None:
                stats["degenerate"] += 1
                rows.pop()
                continue
            d_out = args.out / split / label
            d_out.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(d_out / name), crop):
                stats["write_failed"] += 1
                rows.pop()
        if n % 50 == 0:
            print(f"  {n}/{len(shared)} images …", flush=True)

    print("\ncomposition:")
    for split in ("train", "val", "test"):
        pos, neg = stats[f"{split}/caries"], stats[f"{split}/no_caries"]
        tot = pos + neg
        if tot:
            print(f"  {split:5s} {tot:6,}   caries {pos:5,} ({pos/tot:5.1%})   "
                  f"no_caries {neg:5,} ({neg/tot:5.1%})")
    print("  negative-class make-up:")
    for k in ("healthy", "impacted", "periapical"):
        print(f"     {k:11s} {stats['subtype/'+k]:6,}")
    print(f"  excluded as ambiguous: {stats['excluded_ambiguous']:,}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (args.out / "meta.json").write_text(json.dumps({
        "built": "caries phase-1 v3 — real negative class",
        "join": "MD5 of image bytes between quadrant_enumeration and "
                "quadrant-enumeration-disease; filenames are NOT comparable",
        "join_verified_fdi_agreement": round(rate, 4),
        "shared_images": len(shared),
        "iou_match": IOU_MATCH, "iou_ambiguous_floor": IOU_AMBIGUOUS,
        "crop": "1.0x tight, floor near / ceil far, 224x224 (the caries contract)",
        "splits_inherited_from": str(args.splits),
        "assumption": "a tooth with no disease annotation is PRESUMED not-diseased. DENTEX "
                      "annotates only diseased teeth, so this is absence of evidence: any "
                      "lesion the annotators missed enters the negative class as a false "
                      "negative. Unmeasurable inside DENTEX; report it with any result.",
        "counts": dict(stats),
    }, indent=2) + "\n")
    print(f"\nmanifest: {args.out/'manifest.csv'}  ({len(rows):,} rows)")


if __name__ == "__main__":
    main()
