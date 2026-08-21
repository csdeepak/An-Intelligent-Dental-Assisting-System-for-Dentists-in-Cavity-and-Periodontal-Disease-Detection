"""
T0.1/T0.2: Regenerate the DENTEX caries crops, honouring data/dentex/splits_v2.json.

WHY THIS EXISTS
---------------
The crops the caries cascade was trained on were built by three notebooks that lived only in
Google Drive (now committed at notebooks/caries/dataset_construction/). They are keyed to
DENTEX's own pre-baked train/val release split, so they cannot produce the independent
image-level split in data/dentex/splits_v2.json. Nothing in this repo could regenerate them
at all. This script replaces those notebooks.

THE CROP CONTRACT — verified, not assumed
-----------------------------------------
Reproduced from the original notebooks and checked against their real output on 21 Aug 2026:
four crops were regenerated from the source X-rays and compared pixel-for-pixel with the
originals downloaded from Drive. Three were BIT-IDENTICAL. The fourth differed by exactly
+/-1 grey level on ~20% of subpixels -- it is the only sample where both dimensions downscale
(243x300 -> 224x224), and the deviation is a cv2 version difference in the bilinear downscale
path (this repo verified under cv2 5.0.0; the notebooks ran a 4.x). No logic difference.

  - crop = raw COCO bbox [x, y, w, h]: floor the near corner, ceil the far edge, clip to the
    image. NO EXPANSION AT ALL -- unlike the bone-loss track's 1.5xW/2.0xH (PAPER_MATERIAL §6.1).
  - cv2.resize(crop, (224, 224)) with default INTER_LINEAR. No aspect preservation, no padding.
  - read and written with OpenCV, so BGR 3-channel PNG.
  - degenerate crops (x2<=x1 or y2<=y1, or empty) are skipped and counted.

Regenerated crops will NOT be byte-identical to the Kaggle dataset on downscaled crops, for
the cv2 reason above. Since the split, the labels and the class definitions all change here
anyway, bit-identity was never achievable; correctness of the logic was, and is verified.

THE NEGATIVE-CLASS PROBLEM THIS SCRIPT FIXES
--------------------------------------------
The original Phase-1 rule is `category_id_3 in [1,3] -> caries, else -> no_caries`, applied to
an annotation file in which EVERY annotation is a diseased tooth. So `no_caries` was exactly
Impacted + Periapical Lesion (762 train / 49 val) and contained NO HEALTHY TEETH, while the
assembled pipeline feeds the gate every tooth the detector finds -- overwhelmingly healthy.
Full record: docs/results/RESULTS_LOG.md 2026-08-21j.

  phase1_legacy -- the original rule, unchanged. Directly comparable to the reported accuracy
                   0.81 / macro-F1 0.77, so a re-run on it isolates the effect of the split +
                   selection-criterion + LR-schedule + augmentation fixes.
  phase2        -- caries vs deep_caries. Unaffected by the above (both classes are diseased);
                   regenerated only so it honours splits_v2.

A `phase1_corrected` variant WAS attempted, adding "healthy" teeth derived from
train_quadrant_enumeration.json by treating any enumerated tooth with no disease annotation as
healthy. **That was wrong and has been removed.** DENTEX's three training subsets
(quadrant / quadrant_enumeration / quadrant-enumeration-disease) NUMBER THEIR FILES
INDEPENDENTLY and cover DISJOINT sets of patients. `train_0.png` in the enumeration subset is a
different radiograph, of a different person, from `train_0.png` in the disease subset --
622 of 634 shared filenames differ in dimensions, and a visual check shows plainly different
patients. Joining the two on file_name matched teeth across unrelated patients. Full record:
docs/results/RESULTS_LOG.md 2026-08-21m.

**Healthy teeth are therefore NOT derivable from DENTEX's labelled data.** The disease subset
annotates only diseased teeth; the enumeration subset has no disease labels at all, so an
un-tagged tooth there is unknown, not healthy. The negative-class defect described above is
real and remains OPEN -- see the RESULTS_LOG entry for the detector-based alternative (run the
frozen tooth detector over the 705 disease images and treat detections not matching any
disease box as not-diseased, which stays inside one image and one coordinate space).

FILE NAMING
-----------
`{image_stem}_{d|e}{annotation_id}.png`, e.g. `train_673_d3.png` (disease annotation 3),
`train_673_e1042.png` (enumeration annotation 1042). The original notebooks used
`{image_id}_{annotation_id}.png`, which is ambiguous in two ways this fixes: `image_id` is a
COCO id local to each annotation file (so train's `1_3.png` and val's `1_3.png` are unrelated
crops), and the disease and enumeration files have independent annotation-id sequences that
would otherwise collide. Every crop here names its source image directly.

Usage:
    python scripts/dentex/build_dentex_crops.py --dry-run     # counts only, touches no image
    python scripts/dentex/build_dentex_crops.py --xrays <dir> --out <dir>
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEF_DISEASE = REPO_ROOT / "data/dentex/raw/train_quadrant_enumeration_disease.json"
DEF_ENUM = REPO_ROOT / "data/dentex/raw/train_quadrant_enumeration.json"
DEF_VAL50 = REPO_ROOT / "data/dentex/raw/validation_triple.json"
DEF_SPLITS = REPO_ROOT / "data/dentex/splits_v2.json"
DEF_OUT = REPO_ROOT / "data/dentex/crops_v2"

CROP_SIZE = 224
CARIES_CLASSES = {1, 3}   # Caries, Deep Caries
DEEP_CARIES = 3


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_coco(path: Path, need_disease=True):
    with open(path) as f:
        d = json.load(f)
    assert "images" in d and "annotations" in d, f"{path}: not a COCO file"
    if need_disease:
        assert any("category_id_3" in a for a in d["annotations"]), f"{path}: no disease labels"
    return d


def index_records(disease, enum, splits, val50):
    """
    Build the full crop list before touching any image, so --dry-run reports real numbers.

    Each record: (source_image, split, src_tag, ann_id, bbox, phase1_legacy,
                  phase1_corrected, phase2, disease_class, quadrant, tooth)
    """
    d_id2f = {i["id"]: i["file_name"] for i in disease["images"]}
    dname = {c["id"]: c["name"] for c in disease["categories_3"]}

    split_of = {}
    for split in ("train", "val", "test"):
        for row in splits["splits"][split]:
            split_of[row["file_name"]] = split
    assert len(split_of) == splits["n_images"], "splits_v2 manifest is inconsistent"

    # tooth identity -> disease classes present, for the healthy-tooth join
    diseased_teeth = defaultdict(list)
    for a in disease["annotations"]:
        diseased_teeth[(d_id2f[a["image_id"]], a["category_id_1"], a["category_id_2"])].append(
            a["category_id_3"]
        )

    records = []

    # --- diseased teeth, from the 705-image disease file ---
    for a in disease["annotations"]:
        f = d_id2f[a["image_id"]]
        c3 = a["category_id_3"]
        legacy = "caries" if c3 in CARIES_CLASSES else "no_caries"
        records.append({
            "source_image": f, "split": split_of[f], "src": "d", "ann_id": a["id"],
            "bbox": a["bbox"],
            "phase1_legacy": legacy,
            "phase2": ("deep_caries" if c3 == DEEP_CARIES else
                       "caries" if c3 in CARIES_CLASSES else ""),
            "disease_class": dname[c3],
            "quadrant": a["category_id_1"], "tooth": a["category_id_2"],
            "pool": "main",
        })

    # --- enumeration file: REFUSED as a healthy-tooth source, with proof ---
    # Kept as an active guard rather than a comment, because the filenames overlap so
    # convincingly that this looks joinable and is not.
    if enum is not None:
        e_dims = {i["file_name"]: (i["width"], i["height"]) for i in enum["images"]}
        d_dims = {i["file_name"]: (i["width"], i["height"]) for i in disease["images"]}
        shared = set(e_dims) & set(d_dims)
        mismatched = [f for f in shared if e_dims[f] != d_dims[f]]
        raise SystemExit(
            "REFUSING to derive healthy teeth from the enumeration subset.\n"
            f"  {len(shared)} filenames appear in both subsets, but {len(mismatched)} of them "
            "have DIFFERENT image dimensions.\n"
            "  DENTEX's training subsets number their files independently and cover disjoint\n"
            "  patients: enumeration/train_0.png is not the same scan as disease/train_0.png.\n"
            "  Joining them on file_name matches teeth across unrelated people.\n"
            "  See this script's docstring and docs/results/RESULTS_LOG.md 2026-08-21m.\n"
            "  Re-run without --enum."
        )

    # --- the separate 50-image DENTEX validation release ---
    # Zero overlap with the 705 (verified), and no enumeration counterpart exists, so no
    # healthy teeth are derivable here. Kept as an independent second evaluation set rather
    # than merged into splits_v2, which would destroy that independence.
    v_id2f = {i["id"]: i["file_name"] for i in val50["images"]}
    assert not (set(v_id2f.values()) & set(d_id2f.values())), "val50 overlaps the 705!"
    for a in val50["annotations"]:
        f = v_id2f[a["image_id"]]
        c3 = a["category_id_3"]
        legacy = "caries" if c3 in CARIES_CLASSES else "no_caries"
        records.append({
            "source_image": f, "split": "extern50", "src": "d", "ann_id": a["id"],
            "bbox": a["bbox"],
            "phase1_legacy": legacy,
            "phase2": ("deep_caries" if c3 == DEEP_CARIES else
                       "caries" if c3 in CARIES_CLASSES else ""),
            "disease_class": dname[c3],
            "quadrant": a["category_id_1"], "tooth": a["category_id_2"],
            "pool": "extern50",
        })

    for r in records:
        r["crop_name"] = f"{Path(r['source_image']).stem}_{r['src']}{r['ann_id']}.png"
    names = [r["crop_name"] for r in records]
    assert len(names) == len(set(names)), "crop filename collision — naming scheme is unsafe"
    return records


def summarise(records, splits):
    print("\n" + "=" * 78)
    print("PLANNED OUTPUT")
    print("=" * 78)
    for variant, key in (("phase1_legacy", "phase1_legacy"), ("phase2", "phase2")):
        print(f"\n{variant}:")
        per = defaultdict(Counter)
        for r in records:
            if r[key]:
                per[r["split"]][r[key]] += 1
        for split in ("train", "val", "test", "extern50"):
            if per[split]:
                total = sum(per[split].values())
                bits = "  ".join(f"{k}={v}" for k, v in sorted(per[split].items()))
                print(f"  {split:9s} {total:6d} crops   {bits}")

    # Images that yield nothing at all. Reported explicitly: without this, the per-split image
    # counts above silently disagree with splits_v2.json and the next reader loses an hour to it.
    produced = {r["source_image"] for r in records if r["pool"] == "main"}
    barren = defaultdict(list)
    for split in ("train", "val", "test"):
        for row in splits["splits"][split]:
            if row["file_name"] not in produced:
                barren[split].append(row["file_name"])
    total_barren = sum(len(v) for v in barren.values())
    print(f"\nImages contributing ZERO crops: {total_barren}")
    if total_barren:
        for split, files in sorted(barren.items()):
            n_split = len(splits["splits"][split])
            print(f"  {split:5s}: {len(files)} of {n_split} — {', '.join(sorted(files))}")
        print("  (these images carry no disease annotations at all, so there is nothing to crop.")
        print("   This is why the per-split image counts above are lower than splits_v2.json's.)")


def generate(records, xrays_dir: Path, out_dir: Path, val50_xrays: Path | None):
    import cv2
    import numpy as np

    variants = {"phase1_legacy": "phase1_legacy", "phase2": "phase2"}
    by_image = defaultdict(list)
    for r in records:
        by_image[(r["pool"], r["source_image"])].append(r)

    stats = Counter()
    manifest_rows = []
    for (pool, fname), recs in sorted(by_image.items()):
        src_dir = val50_xrays if (pool == "extern50" and val50_xrays) else xrays_dir
        path = src_dir / fname
        img = cv2.imread(str(path))
        if img is None:
            stats["image_missing"] += 1
            print(f"  WARNING: cannot read {path}")
            continue
        stats["images_read"] += 1

        for r in recs:
            x, y, w, h = r["bbox"]
            x1 = max(int(np.floor(x)), 0)
            y1 = max(int(np.floor(y)), 0)
            x2 = min(int(np.ceil(x + w)), img.shape[1])
            y2 = min(int(np.ceil(y + h)), img.shape[0])
            if x2 <= x1 or y2 <= y1:
                stats["skipped_degenerate"] += 1
                continue
            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                stats["skipped_empty"] += 1
                continue
            crop = cv2.resize(crop, (CROP_SIZE, CROP_SIZE))

            wrote_any = False
            for variant, key in variants.items():
                label = r[key]
                if not label:
                    continue
                dst = out_dir / variant / r["split"] / label
                dst.mkdir(parents=True, exist_ok=True)
                if cv2.imwrite(str(dst / r["crop_name"]), crop):
                    stats[f"{variant}/{r['split']}/{label}"] += 1
                    wrote_any = True
                else:
                    stats["write_failed"] += 1
            if wrote_any:
                manifest_rows.append(r)

    return stats, manifest_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disease", type=Path, default=DEF_DISEASE)
    ap.add_argument("--enum", type=Path, default=None,
                    help="DO NOT USE — see docstring; the script refuses and explains why")
    ap.add_argument("--val50", type=Path, default=DEF_VAL50)
    ap.add_argument("--splits", type=Path, default=DEF_SPLITS)
    ap.add_argument("--xrays", type=Path, help="dir with the 705 train_*.png source X-rays")
    ap.add_argument("--val50-xrays", type=Path, help="dir with the 50 val_*.png X-rays")
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--dry-run", action="store_true",
                    help="report exact planned counts without reading or writing any image")
    args = ap.parse_args()

    disease = load_coco(args.disease)
    enum = load_coco(args.enum, need_disease=False) if args.enum else None
    val50 = load_coco(args.val50)
    splits = json.loads(args.splits.read_text())

    assert splits["source_sha256"] == sha256_of(args.disease), (
        "splits_v2.json was built from a DIFFERENT disease annotation file than the one given "
        "(--disease). Refusing to build crops against a split that does not match its source."
    )

    records = index_records(disease, enum, splits, val50)
    print(f"Indexed {len(records):,} crops from {len(disease['images'])} + {len(val50['images'])} images")
    summarise(records, splits)

    if args.dry_run:
        print("\n--dry-run: nothing read, nothing written")
        return
    if not args.xrays:
        ap.error("--xrays is required unless --dry-run")

    args.out.mkdir(parents=True, exist_ok=True)
    stats, written = generate(records, args.xrays, args.out, args.val50_xrays)

    man = args.out / "crops_manifest.csv"
    cols = ["crop_name", "source_image", "split", "pool", "src", "ann_id", "disease_class",
            "quadrant", "tooth", "phase1_legacy", "phase2"]
    with open(man, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(written)

    meta = {
        "created": date.today().isoformat(),
        "crop_contract": "raw COCO bbox, floor/ceil, clipped, no expansion; "
                         "cv2.resize to 224x224 INTER_LINEAR; BGR PNG",
        "splits_manifest": str(args.splits.relative_to(REPO_ROOT)),
        "disease_sha256": sha256_of(args.disease),
        "val50_sha256": sha256_of(args.val50),
        "counts": {k: v for k, v in sorted(stats.items())},
    }
    (args.out / "crops_meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    print("\nWrite stats:")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"\nManifest: {man}")
    print(f"Metadata: {args.out / 'crops_meta.json'}")


if __name__ == "__main__":
    main()
