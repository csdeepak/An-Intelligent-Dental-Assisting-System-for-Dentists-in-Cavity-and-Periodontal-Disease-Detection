"""
T0.2: Carve a held-out DENTEX test split from the existing val/ folder.

UNTESTED against real data as of 19 Aug 2026 — the DENTEX processed dataset
(BASE_PATH below) lives on Kaggle, not on this machine (see
docs/research/PUBLICATION_TODO.md T0.2 and the phase-1.ipynb notebooks, which read
it via a Kaggle input path). This script is written from that notebook's known
directory/filename conventions and must be run where the data actually is (Kaggle,
or a local copy), then its output splits.json committed back into this repo.

WHY carving from val, not a fresh three-way split from raw DENTEX:
There is no patient/study identifier anywhere in this repo's DENTEX pipeline, and no
raw (pre-crop) DENTEX copy to rebuild train/val/test from scratch. The train/val
split was pre-baked into an externally-uploaded Kaggle dataset. Per-image IDs ARE
recoverable from crop filenames ("{image_id}_{crop_id}.png" convention — confirmed
in phase-1.ipynb, e.g. "13_49.png"), so this script groups by that ID to avoid
crop-level leakage (two crops of the same source OPG never land in different
splits), but it can only split the current val/ pool into a new val + test. This is
a WEAKER independence guarantee than a fully independent three-way split built from
raw data — document this explicitly in the paper's methods section, do not present
it as equivalent to a from-scratch held-out set. If val was ever used to select
among model variants before this split was carved (it was, repeatedly — see
docs/results/RESULTS_LOG.md's caries entries), that is a soft leak into whichever
half becomes "test," and should be named as a limitation, not glossed over.

Grouping is by image_id only (not by class), because a single source OPG can
contribute crops of different classes (e.g. one caries tooth and one healthy tooth
from the same image) and those must not be split across val/test either.

Usage:
    python split_dentex_holdout.py --base-path /kaggle/input/.../processed_dataset \\
        --classes caries no_caries --test-fraction 0.5 --seed 42

    python split_dentex_holdout.py --dry-run   # preview the split, move nothing

Output:
    <base-path>/test/<class>/*.png   (moved out of val/)
    <base-path>/val/<class>/*.png    (what remains)
    A splits.json manifest written to --manifest-out (default: this repo's
    data/dentex/splits.json — copy/commit it back here after running on Kaggle).
"""

import argparse
import json
import random
import shutil
from collections import defaultdict
from pathlib import Path


DEFAULT_BASE_PATH = "/kaggle/input/datasets/gunadeepchennupati/dentex-processed-data/processed_dataset"
DEFAULT_MANIFEST_OUT = Path(__file__).resolve().parents[2] / "data" / "dentex" / "splits.json"


def parse_image_id(filename: str) -> str:
    """'{image_id}_{crop_id}.png' -> image_id. Matches phase-1.ipynb's crop naming."""
    stem = Path(filename).stem
    return stem.split("_")[0]


def collect_val_files(base_path: Path, classes):
    """Returns dict: image_id -> list of (class_name, Path) for every file in val/."""
    by_image = defaultdict(list)
    for class_name in classes:
        class_dir = base_path / "val" / class_name
        if not class_dir.exists():
            print(f"WARNING: {class_dir} does not exist, skipping")
            continue
        for f in sorted(class_dir.iterdir()):
            if not f.is_file():
                continue
            image_id = parse_image_id(f.name)
            by_image[image_id].append((class_name, f))
    return by_image


def split_image_ids(image_ids, test_fraction, seed):
    """Deterministic shuffle-and-split of unique image IDs. Fixed seed per T0.2."""
    ids = sorted(image_ids)  # sort first so shuffle is reproducible regardless of
                              # filesystem iteration order
    rng = random.Random(seed)
    rng.shuffle(ids)
    n_test = round(len(ids) * test_fraction)
    test_ids = set(ids[:n_test])
    val_ids = set(ids[n_test:])
    return val_ids, test_ids


def move_files(by_image, test_ids, base_path: Path, dry_run: bool):
    moved = []
    for image_id, entries in by_image.items():
        if image_id not in test_ids:
            continue
        for class_name, src in entries:
            dst_dir = base_path / "test" / class_name
            dst = dst_dir / src.name
            moved.append(str(src.relative_to(base_path)))
            if not dry_run:
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
    return moved


def build_manifest(by_image, val_ids, test_ids, test_fraction, seed, base_path, dry_run):
    def class_counts(ids):
        counts = defaultdict(int)
        for image_id in ids:
            for class_name, _ in by_image[image_id]:
                counts[class_name] += 1
        return dict(counts)

    return {
        "task": "T0.2 — DENTEX held-out test split",
        "methodology": (
            "Carved from the pre-existing Kaggle-processed val/ pool, grouped by "
            "image_id parsed from crop filenames ('{image_id}_{crop_id}.ext'), NOT a "
            "fully independent three-way split from raw DENTEX (no patient ID or raw "
            "data available in this repo). See module docstring in "
            "scripts/dentex/split_dentex_holdout.py for the full caveat — report this "
            "distinction explicitly in the paper's methods section."
        ),
        "base_path": str(base_path),
        "seed": seed,
        "test_fraction": test_fraction,
        "dry_run": dry_run,
        "n_images_val": len(val_ids),
        "n_images_test": len(test_ids),
        "class_counts_val": class_counts(val_ids),
        "class_counts_test": class_counts(test_ids),
        "val_image_ids": sorted(val_ids),
        "test_image_ids": sorted(test_ids),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-path", default=DEFAULT_BASE_PATH,
                         help="Root of the processed DENTEX dataset (contains train/, val/)")
    parser.add_argument("--classes", nargs="+", default=["caries", "no_caries"],
                         help="Class subfolder names under val/. Use ['caries', 'deep_caries'] "
                              "for the severity split instead.")
    parser.add_argument("--test-fraction", type=float, default=0.5,
                         help="Fraction of val/ IMAGES (not crops) to move into test/")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--manifest-out", default=str(DEFAULT_MANIFEST_OUT),
                         help="Where to write the splits.json manifest")
    parser.add_argument("--dry-run", action="store_true",
                         help="Compute and report the split without moving any files")
    args = parser.parse_args()

    base_path = Path(args.base_path)
    assert base_path.exists(), f"base path does not exist: {base_path}"

    by_image = collect_val_files(base_path, args.classes)
    print(f"Found {len(by_image)} unique image IDs in val/ "
          f"({sum(len(v) for v in by_image.values())} total crops)")

    val_ids, test_ids = split_image_ids(list(by_image.keys()), args.test_fraction, args.seed)
    print(f"Split: {len(val_ids)} images -> val, {len(test_ids)} images -> test "
          f"(seed={args.seed}, test_fraction={args.test_fraction})")

    moved = move_files(by_image, test_ids, base_path, args.dry_run)
    print(f"{'Would move' if args.dry_run else 'Moved'} {len(moved)} files "
          f"{'(dry run — nothing changed)' if args.dry_run else 'into test/'}")

    manifest = build_manifest(by_image, val_ids, test_ids, args.test_fraction,
                               args.seed, base_path, args.dry_run)
    manifest_out = Path(args.manifest_out)
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written to {manifest_out}")
    print("Class balance — val:", manifest["class_counts_val"])
    print("Class balance — test:", manifest["class_counts_test"])
    if not args.dry_run:
        print("\nNext steps: re-run the caries cascade (notebooks/caries/phase-1.ipynb) "
              "against the new val/, then evaluate once — and only once — on test/. "
              "Commit the manifest at", manifest_out, "back into this repo.")


if __name__ == "__main__":
    main()
