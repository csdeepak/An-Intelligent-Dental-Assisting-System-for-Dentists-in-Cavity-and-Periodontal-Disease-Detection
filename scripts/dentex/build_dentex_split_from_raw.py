"""
T0.2 (redone): Build an INDEPENDENT three-way DENTEX split from the raw source data.

WHY THIS REPLACES split_dentex_holdout.py
------------------------------------------
split_dentex_holdout.py (19 Aug 2026) carves a test set out of the existing val/ pool,
because at the time no raw (pre-crop) DENTEX copy was reachable and the train/val split
was pre-baked into an externally-uploaded Kaggle dataset. That fallback carries a real
weakness, stated plainly in its own docstring: val had already been used repeatedly to
select among model variants, so whichever half becomes "test" inherits a soft leak.

That constraint no longer holds. The raw disease-labelled subset — 705 source X-rays and
the original COCO annotation file train_quadrant_enumeration_disease.json — is available,
so the split can be drawn ONCE, at image level, before any crop is generated and before
any model sees anything. That is what this script does. Decision recorded in
docs/results/RESULTS_LOG.md (2026-08-21b entry).

split_dentex_holdout.py is kept, not deleted (repo rule 3), and marked superseded.

METHOD
------
- **Unit of splitting is the source image**, never the crop. DENTEX ships no patient or
  study identifier, so one image is treated as one patient — the strongest grouping the
  data supports. Every crop derived from an image inherits that image's split, which makes
  crop-level leakage structurally impossible rather than merely avoided.
- **Stratified on the disease presence-vector.** Each image gets a 4-bit signature
  (has_impacted, has_caries, has_periapical, has_deep_caries) from its annotations —
  images with no annotations get the all-zero signature and are kept, not dropped. Images
  are grouped by signature and each group is dealt out across train/val/test in proportion,
  so rare combinations (e.g. periapical-only, 158 annotations total) cannot land entirely
  in one split by luck.
- **Deterministic.** Fixed seed, sorted inputs, stable tie-breaking. Re-running reproduces
  the split byte-for-byte; the manifest records the source file's SHA-256 so a changed
  input cannot silently produce a different split under the same name.
- 70/15/15, matching the Tufts convention already used for detection.

OUTPUT
------
data/dentex/splits_v2.json — the manifest, committed to this repo. Contains per-split
image lists (id + file_name), the per-split per-class annotation counts, and provenance.
This file is the authority: crop generation must read it and place each crop by its source
image's split. It does not move any file itself — nothing to move yet, since crops are
regenerated downstream from the raw X-rays.

Usage:
    python scripts/dentex/build_dentex_split_from_raw.py
    python scripts/dentex/build_dentex_split_from_raw.py --dry-run
"""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COCO = REPO_ROOT / "data/dentex/raw/train_quadrant_enumeration_disease.json"
DEFAULT_OUT = REPO_ROOT / "data/dentex/splits_v2.json"

SEED = 42
FRACTIONS = {"train": 0.70, "val": 0.15, "test": 0.15}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_coco(path: Path):
    with open(path) as f:
        d = json.load(f)
    for key in ("images", "annotations", "categories_3"):
        assert key in d, f"{path} is not the expected DENTEX COCO file: missing {key!r}"
    return d


def disease_names(coco):
    """category_id_3 -> disease name."""
    return {c["id"]: c["name"] for c in coco["categories_3"]}


def signature_for_images(coco, n_classes):
    """image_id -> tuple of 0/1 flags, one per disease class. No annotations => all zeros."""
    present = defaultdict(set)
    for ann in coco["annotations"]:
        present[ann["image_id"]].add(ann["category_id_3"])
    return {
        img["id"]: tuple(1 if c in present.get(img["id"], ()) else 0 for c in range(n_classes))
        for img in coco["images"]
    }


def assign_splits(signatures, seed=SEED, fractions=FRACTIONS):
    """
    Deal each stratum out across the splits in proportion.

    Within a stratum the images are shuffled with a seeded RNG, then walked in order while
    a running quota decides where each one lands. Largest-remainder allocation gives every
    stratum its exact proportional counts, so a 2-image stratum contributes to two
    different splits rather than being rounded entirely into train.
    """
    import random

    rng = random.Random(seed)
    by_sig = defaultdict(list)
    for image_id, sig in signatures.items():
        by_sig[sig].append(image_id)

    assignment = {}
    for sig in sorted(by_sig):  # sorted: stratum order must not depend on dict iteration
        members = sorted(by_sig[sig])
        rng.shuffle(members)
        n = len(members)

        exact = {s: n * f for s, f in fractions.items()}
        counts = {s: int(v) for s, v in exact.items()}
        remainder = n - sum(counts.values())
        # Largest fractional part wins the leftovers; split name breaks exact ties.
        order = sorted(fractions, key=lambda s: (-(exact[s] - counts[s]), s))
        for i in range(remainder):
            counts[order[i % len(order)]] += 1

        i = 0
        for split in ("train", "val", "test"):
            for image_id in members[i:i + counts[split]]:
                assignment[image_id] = split
            i += counts[split]
    return assignment


def summarise(coco, assignment, names):
    per_split_images = Counter(assignment.values())
    per_split_ann = defaultdict(Counter)
    for ann in coco["annotations"]:
        split = assignment[ann["image_id"]]
        per_split_ann[split][names[ann["category_id_3"]]] += 1
    return per_split_images, per_split_ann


def verify(coco, assignment):
    """Fail loudly rather than emit a quietly-broken manifest."""
    ids = {img["id"] for img in coco["images"]}
    assert set(assignment) == ids, "every image must be assigned exactly once"
    seen = Counter(assignment.values())
    assert sum(seen.values()) == len(ids), "assignment count mismatch"
    assert set(seen) == {"train", "val", "test"}, f"unexpected splits: {sorted(seen)}"
    file_names = [img["file_name"] for img in coco["images"]]
    assert len(set(file_names)) == len(file_names), "duplicate file_name in source COCO"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coco", type=Path, default=DEFAULT_COCO)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--dry-run", action="store_true", help="print the split, write nothing")
    args = ap.parse_args()

    coco = load_coco(args.coco)
    names = disease_names(coco)
    signatures = signature_for_images(coco, len(names))
    assignment = assign_splits(signatures, seed=args.seed)
    verify(coco, assignment)

    per_split_images, per_split_ann = summarise(coco, assignment, names)
    by_id = {img["id"]: img["file_name"] for img in coco["images"]}

    print(f"Source: {args.coco}")
    print(f"  {len(coco['images'])} images, {len(coco['annotations'])} annotations, "
          f"{len(names)} disease classes")
    n_unannotated = sum(1 for s in signatures.values() if not any(s))
    print(f"  {len(set(signatures.values()))} distinct disease signatures; "
          f"{n_unannotated} images carry no disease annotation (kept, not dropped)")
    print(f"\nSplit (seed {args.seed}, {FRACTIONS}):")
    for split in ("train", "val", "test"):
        n = per_split_images[split]
        print(f"  {split:5s}: {n:3d} images ({n / len(coco['images']):.1%})  "
              + "  ".join(f"{k}={v}" for k, v in sorted(per_split_ann[split].items())))

    manifest = {
        "version": "splits_v2",
        "created": date.today().isoformat(),
        "method": "image-level stratified three-way split of the raw DENTEX "
                  "quadrant-enumeration-disease subset; strata are the 4-bit disease "
                  "presence-vector; largest-remainder proportional allocation per stratum",
        "supersedes": "scripts/dentex/split_dentex_holdout.py (carve-from-val fallback)",
        "source_file": str(args.coco.relative_to(REPO_ROOT)),
        "source_sha256": sha256_of(args.coco),
        "seed": args.seed,
        "fractions": FRACTIONS,
        "n_images": len(coco["images"]),
        "n_annotations": len(coco["annotations"]),
        "disease_classes": [names[i] for i in sorted(names)],
        "counts": {
            s: {"images": per_split_images[s], "annotations": dict(sorted(per_split_ann[s].items()))}
            for s in ("train", "val", "test")
        },
        "splits": {
            s: [{"image_id": i, "file_name": by_id[i]}
                for i in sorted(k for k, v in assignment.items() if v == s)]
            for s in ("train", "val", "test")
        },
    }

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nWrote {args.out.relative_to(REPO_ROOT)} "
          f"({args.out.stat().st_size:,} bytes)")
    print("This manifest is the authority for DENTEX splits. Crop generation must read it "
          "and place every crop by its SOURCE IMAGE's split.")


if __name__ == "__main__":
    main()
