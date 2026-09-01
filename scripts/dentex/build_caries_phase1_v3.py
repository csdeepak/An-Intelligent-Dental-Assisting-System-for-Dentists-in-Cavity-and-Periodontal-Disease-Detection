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

--include-disease-only: THE 62% OF CARIES SUPERVISION THIS BUILD LEAVES ON THE FLOOR
------------------------------------------------------------------------------------
The MD5 join is what makes healthy teeth derivable, and only 260 of the disease subset's 705
images have an enumeration twin. The other **445 images are dropped entirely** -- including
their caries annotations, which need no enumeration twin to be usable as POSITIVES. Measured:
2,767 Caries + Deep Caries annotations exist in the disease subset; the default build uses
1,049. **62% of the available caries supervision is unused** (RESULTS_LOG 2026-08-31).

`--include-disease-only` adds those 445 images, contributing:
    Caries | Deep Caries      -> `caries`      (positives)
    Impacted | Periapical     -> `no_caries`   (genuinely not-caries, as in phase1_legacy)
and **no healthy teeth**, because without the enumeration twin there is no list of which teeth
are present. That asymmetry is deliberate: the alternative is to run the detector over these
images and call every unannotated box healthy, which would inject detector false positives into
the negative class. The negative class stays exactly as the default build produced it.

The consequence to report: this shifts the class ratio, it does not add healthy negatives, and
the `basis` column records which images each crop came from so the two can be analysed apart.

LEAKAGE. Any image whose MD5 matches one in `--eval-pool` (the 250-image `DENTEX/disease/`
evaluation pool) is refused, in BOTH modes. Exactly one collides -- `train_332.png` in the
training pool is byte-identical to `test_181.png` in the eval pool, already recorded in
`data/dentex/disease_leaked_images.json` as `leaked_into_detector_training`. The default
260-image build never contained it; this guard is what keeps the expansion clean too.

Usage:
    python scripts/dentex/build_caries_phase1_v3.py --dry-run
    python scripts/dentex/build_caries_phase1_v3.py
    python scripts/dentex/build_caries_phase1_v3.py --include-disease-only \
        --out data/dentex/crops_v4_phase1 --dry-run
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
DEF_EVAL_POOL = Path.home() / "Downloads/Capstone/DENTEX/disease/input"

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


def tight_crop(img, bbox, expand=1.0):
    """The caries crop contract: floor the near corner, ceil the far edge, clip, resize 224.

    `expand` > 1.0 grows the box about its centre BEFORE that rule is applied. 1.0 is the
    shipped contract and leaves this function bit-for-bit as it was.
    """
    H, W = img.shape[:2]
    x, y, w, h = bbox
    if expand != 1.0:
        cx, cy = x + w / 2.0, y + h / 2.0
        w, h = w * expand, h * expand
        x, y = cx - w / 2.0, cy - h / 2.0
    x1, y1 = max(0, math.floor(x)), max(0, math.floor(y))
    x2, y2 = min(W, math.ceil(x + w)), min(H, math.ceil(y + h))
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None
    return cv2.resize(img[y1:y2, x1:x2], (CROP, CROP))


def apply_clahe(img, clip=2.0, tiles=8):
    """Contrast-limited adaptive histogram equalisation on the source radiograph.

    Caries is a low-contrast radiolucency, so local equalisation is the standard dental-imaging
    preprocessing for it. DENTEX crops are true greyscale (B==G==R, verified), so the
    grey -> CLAHE -> 3-channel round trip loses nothing and keeps the ResNet input shape.
    """
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tiles, tiles)).apply(g)
    return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enum-root", type=Path, default=DEF_ENUM)
    ap.add_argument("--disease-root", type=Path, default=DEF_DISEASE)
    ap.add_argument("--splits", type=Path, default=DEF_SPLITS)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--include-disease-only", action="store_true",
                    help="also emit positives (and impacted/periapical negatives) from the 445 "
                         "disease images with no enumeration twin; adds NO healthy teeth")
    ap.add_argument("--eval-pool", type=Path, default=DEF_EVAL_POOL,
                    help="images here are never trained on; matched by MD5, both modes")
    ap.add_argument("--clahe", action="store_true",
                    help="CLAHE the source radiograph before cropping (signal arm A)")
    ap.add_argument("--crop-expand", type=float, default=1.0,
                    help="grow each box about its centre before cropping; 1.0 = shipped "
                         "contract (signal arm B)")
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

    # Never train on anything byte-identical to an evaluation image. Applied in both modes.
    eval_hashes = set()
    if args.eval_pool.is_dir():
        eval_hashes = {md5(p) for p in sorted(args.eval_pool.iterdir())
                       if p.suffix.lower() in (".png", ".jpg", ".jpeg")}
    refused = set(di_by_hash) & eval_hashes
    print(f"  eval pool {args.eval_pool.name}: {len(eval_hashes)} images   "
          f"REFUSED from training: {len(refused)}"
          + (f" ({', '.join(sorted(di_by_hash[h]['file_name'] for h in refused))})" if refused else ""))
    shared = [h for h in shared if h not in refused]

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
        if img is not None and args.clahe:
            img = apply_clahe(img)
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
                         "source_image_md5": h, "basis": "enum_join",
                         "enum_file": ei["file_name"], "disease_file": dii["file_name"],
                         "ann_id": e["id"], "iou_to_disease": round(best_iou, 4),
                         "fdi": (e["category_id_1"] + 1) * 10 + (e["category_id_2"] + 1)})
            if args.dry_run:
                continue
            crop = tight_crop(img, e["bbox"], args.crop_expand)
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

    # ---- the 445 disease images with no enumeration twin: POSITIVES ONLY ----
    # No enumeration twin means no list of which teeth are present, so no healthy tooth can be
    # derived here. Only the annotated (diseased) teeth are emitted. See the module docstring.
    disease_only = sorted(set(di_by_hash) - set(en_by_hash) - refused) \
        if args.include_disease_only else []
    if disease_only:
        print(f"\ndisease-only images (no enumeration twin): {len(disease_only)}")
        for n, h in enumerate(disease_only, 1):
            dii = di_by_hash[h]
            split = split_of_name.get(dii["file_name"])
            if split is None:
                stats["image_unsplit"] += 1
                continue
            img = None if args.dry_run else cv2.imread(
                str(args.disease_root / "xrays" / dii["file_name"]))
            if not args.dry_run and img is None:
                stats["image_unreadable"] += 1
                continue
            if img is not None and args.clahe:
                img = apply_clahe(img)
            for d in di_anns[dii["id"]]:
                subtype = DISEASE[d["category_id_3"]]
                label = "caries" if subtype in CARIOUS else "no_caries"
                stats[f"{split}/{label}"] += 1
                stats[f"subtype/{subtype}"] += 1
                stats["disease_only_crops"] += 1
                name = f"{Path(dii['file_name']).stem}_d{d['id']}.png"
                rows.append({"crop": name, "split": split, "label": label, "subtype": subtype,
                             "source_image_md5": h, "basis": "disease_only",
                             "enum_file": "", "disease_file": dii["file_name"],
                             "ann_id": d["id"], "iou_to_disease": 1.0,
                             "fdi": (d["category_id_1"] + 1) * 10 + (d["category_id_2"] + 1)})
                if args.dry_run:
                    continue
                crop = tight_crop(img, d["bbox"], args.crop_expand)
                if crop is None:
                    stats["degenerate"] += 1
                    rows.pop()
                    continue
                d_out = args.out / split / label
                d_out.mkdir(parents=True, exist_ok=True)
                if not cv2.imwrite(str(d_out / name), crop):
                    stats["write_failed"] += 1
                    rows.pop()
            if n % 100 == 0:
                print(f"  {n}/{len(disease_only)} disease-only images …", flush=True)

    # An image must never contribute crops to two different splits.
    by_img = defaultdict(set)
    for r in rows:
        by_img[r["source_image_md5"]].add(r["split"])
    spanning = {h for h, s in by_img.items() if len(s) > 1}
    if spanning:
        raise SystemExit(f"{len(spanning)} images span multiple splits — refusing to write")
    print(f"\nsplit hygiene: {len(by_img)} source images, 0 span multiple splits")

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
        "include_disease_only": args.include_disease_only,
        "disease_only_images": len(disease_only),
        "clahe": args.clahe,
        "crop_expand": args.crop_expand,
        "eval_pool": str(args.eval_pool),
        "eval_pool_images": len(eval_hashes),
        "refused_as_eval_leakage": sorted(di_by_hash[h]["file_name"] for h in refused),
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
