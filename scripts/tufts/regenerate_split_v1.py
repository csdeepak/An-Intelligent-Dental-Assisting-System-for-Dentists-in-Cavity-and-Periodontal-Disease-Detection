"""
Regenerate `outputs/eda_tufts/split_v1.csv` — the frozen Tufts 70/15/15 image-level split —
byte-for-byte, on any machine, from the raw data.

WHY THIS EXISTS
---------------
`split_v1.csv` is the split behind every reported detector number
(`tooth-detector-a100-1024-v1.0`, test mAP@0.5 0.7824) and every downstream Tufts crop
builder. It is gitignored (`.gitignore:63`, `outputs/`), so it does not travel with the repo.
That has already cost this project real time twice:

  - 20 Aug 2026: declared "lost after an exhaustive search" and treated as a hard blocker on
    R1. It was not lost — the search ran over a Windows filesystem while the file sat on the
    macOS machine (`docs/research/T0.6_detector_reconciliation.md` §3.3).
  - 26 Aug 2026: genuinely absent on the Windows machine, which has the raw Tufts data and
    the frozen detector but never had `_repo_archive/datasets_workspace/outputs/`.

The split was always *reproducible* — it is a seeded shuffle, and the notebook that made it
says so in its own header ("Rule 2: Split is deterministic and write-once, random seed FIXED
to 42"). Nobody had extracted that into runnable code, so the file kept being treated as an
irreplaceable artefact instead of a derived one. This script closes that: the split is now a
function of the data, not a file somebody has to carry between laptops.

PROVENANCE — this is a faithful extraction, not a reimplementation
------------------------------------------------------------------
The logic below is lifted verbatim from `week1_tufts_eda_v2.ipynb` (archived at
`_repo_archive/datasets_workspace/week1_tufts_eda_v2.ipynb`), which is the notebook that
originally wrote the file:

  - cell 6  — the image inventory (`rglob`, the image-extension filter)
  - cell 12 — `empty_images` (entries in teeth_bbox.json with zero `Label.objects`)
  - cell 24 — the split itself

The shuffle uses `np.random.RandomState(42)`, NumPy's *legacy* generator, whose stream is
guaranteed stable across NumPy versions — which is why this reproduces exactly on NumPy 2.x
today despite having been written under NumPy 1.x.

VERIFIED, NOT ASSUMED
---------------------
Run on the Windows machine 26 Aug 2026 against the raw Tufts data, checked on four
independent invariants recorded elsewhere in this repo *before* this script existed:

  1. split counts       700 train / 150 val / 150 test   (EDA notebook's saved output cell)
  2. empty per split     21 train /   5 val /   6 test   (EDA notebook's saved output cell)
  3. the documented leak  590.JPG -> test, 591.JPG -> train
                                     (`RESULTS_LOG.md` 2026-08-24, `build_enumeration_crops.py`)
  4. SHA-256             6de8cef2af1e73ff843f0353dccc0f93ddac34f33422c418f8ac07c67accb58b
                                     (`T0.6_detector_reconciliation.md` §3.3)

All four passed, including the byte-exact hash. `--verify` re-runs those checks and exits
non-zero on any mismatch, so this can be used as a guard and not just a generator.

NOTE ON LINE ENDINGS: the original was written on macOS, so the CSV is written with `\n`
explicitly. Letting pandas default to `os.linesep` on Windows produces `\r\n` and a different
hash for an identical split — the content would be right and the hash check would still fail.

Usage:
    python scripts/tufts/regenerate_split_v1.py            # write the split
    python scripts/tufts/regenerate_split_v1.py --verify   # check invariants, write nothing
    TUFTS_ZIP=<path> python scripts/tufts/regenerate_split_v1.py   # data elsewhere
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# =============================================================================
# CONFIGURATION — env-var overridable, so this runs unmodified on a GPU box
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]

TUFTS_ZIP = Path(os.environ.get("TUFTS_ZIP", REPO_ROOT / "data" / "tufts" / "ZIP"))


def _default_img_dir(zip_root):
    """Prefer an orientation-corrected copy when one exists beside the canonical name.

    This script only needs the FILE INVENTORY (which stems exist), not the pixels, so a
    misaligned copy would still produce a correct split -- but defaulting to the directory this
    machine knows is 180 degrees out is how a wrong frame spreads. The macOS copy is correct
    under the canonical name and has no `_fixed` beside it, so this resolves correctly on both
    machines without anyone having to remember which is which. RESULTS_LOG 2026-08-27a, 2026-09-06c.
    """
    fixed = zip_root / "Radiographs_rotated_fixed"
    return fixed if fixed.exists() else zip_root / "Radiographs_rotated"


IMG_DIR = Path(os.environ.get("TUFTS_IMG_DIR") or _default_img_dir(TUFTS_ZIP))
BBOX_JSON = Path(
    os.environ.get("TUFTS_BBOX_JSON", TUFTS_ZIP / "Segmentation" / "Segmentation" / "teeth_bbox.json")
)
OUT_CSV = Path(os.environ.get("TUFTS_SPLIT_CSV", REPO_ROOT / "outputs" / "eda_tufts" / "split_v1.csv"))

# LOCKED — these three reproduce the frozen split. Changing any of them produces a
# *different* split, which would silently invalidate every reported Tufts number.
RANDOM_SEED = 42
SPLIT_RATIOS = (0.70, 0.15, 0.15)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

EXPECTED_SHA256 = "6de8cef2af1e73ff843f0353dccc0f93ddac34f33422c418f8ac07c67accb58b"
EXPECTED_COUNTS = {"train": 700, "val": 150, "test": 150}
EXPECTED_EMPTY = {"train": 21, "val": 5, "test": 6}
EXPECTED_LEAK = {"590.JPG": "test", "591.JPG": "train"}


def _norm_fname(name):
    """Match the EDA notebook's filename normalisation (cell 24)."""
    return Path(str(name)).name.strip().lower()


def build_split():
    """Rebuild the split DataFrame. Faithful to week1_tufts_eda_v2.ipynb cells 6/12/24."""
    assert IMG_DIR.exists(), (
        f"Rotated radiographs missing: {IMG_DIR}\n"
        "Run scripts/yolo/rotate_tufts_radiographs.py first (mind its 22 Aug direction fix)."
    )
    assert BBOX_JSON.exists(), f"teeth_bbox.json missing: {BBOX_JSON}"

    # --- cell 6: inventory ---
    filenames = [
        p.name for p in IMG_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
    assert len(filenames) >= 990, f"Expected ~1000 rotated images, found {len(filenames)}"

    # --- cell 12: which images carry no annotated objects at all ---
    with open(BBOX_JSON, encoding="utf-8") as fh:
        bbox_data = json.load(fh)
    empty_images = [
        entry["External ID"]
        for entry in bbox_data
        if entry.get("External ID") and len(entry.get("Label", {}).get("objects", [])) == 0
    ]

    # --- cell 24: the seeded shuffle ---
    all_images = sorted(pd.Series(filenames).unique())
    rng = np.random.RandomState(RANDOM_SEED)
    indices = np.arange(len(all_images))
    rng.shuffle(indices)

    n_total = len(indices)
    n_train = int(n_total * SPLIT_RATIOS[0])
    n_val = int(n_total * SPLIT_RATIOS[1])

    train_idx = set(indices[:n_train])
    val_idx = set(indices[n_train:n_train + n_val])

    split_labels = [
        "train" if i in train_idx else "val" if i in val_idx else "test"
        for i in range(len(all_images))
    ]

    df = pd.DataFrame({"filename": all_images, "split": split_labels})
    empty_set = {_norm_fname(f) for f in empty_images}
    df["is_empty"] = df["filename"].map(lambda f: _norm_fname(f) in empty_set)
    return df


def check_invariants(df, csv_bytes):
    """Return a list of (name, ok, detail). Empty failures list == reproduction confirmed."""
    results = []

    counts = df["split"].value_counts().to_dict()
    results.append((
        "split counts", counts == EXPECTED_COUNTS,
        f"{counts} (expected {EXPECTED_COUNTS})",
    ))

    empties = df.groupby("split")["is_empty"].sum().astype(int).to_dict()
    results.append((
        "empty per split", empties == EXPECTED_EMPTY,
        f"{empties} (expected {EXPECTED_EMPTY})",
    ))

    leak_ok, leak_detail = True, []
    for fname, expected in EXPECTED_LEAK.items():
        row = df[df["filename"] == fname]
        got = row["split"].iloc[0] if len(row) else "MISSING"
        leak_ok &= (got == expected)
        leak_detail.append(f"{fname}->{got}")
    results.append((
        "documented 590/591 leak", leak_ok,
        f"{', '.join(leak_detail)} (expected 590->test, 591->train)",
    ))

    digest = hashlib.sha256(csv_bytes).hexdigest()
    results.append((
        "SHA-256", digest == EXPECTED_SHA256,
        f"{digest}\n                    expected {EXPECTED_SHA256}",
    ))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument(
        "--verify", action="store_true",
        help="check the invariants and exit; do not write the CSV",
    )
    ap.add_argument(
        "--force", action="store_true",
        help="overwrite an existing split CSV (default: refuse, the split is write-once)",
    )
    args = ap.parse_args()

    print("=" * 68)
    print("Tufts frozen split — regenerate / verify")
    print("=" * 68)
    print(f"  images:  {IMG_DIR}")
    print(f"  bboxes:  {BBOX_JSON}")
    print(f"  output:  {OUT_CSV}")
    print()

    df = build_split()
    csv_text = df.to_csv(index=False, lineterminator="\n")
    csv_bytes = csv_text.encode("utf-8")

    results = check_invariants(df, csv_bytes)
    failures = [name for name, ok, _ in results if not ok]

    for name, ok, detail in results:
        print(f"  [{'OK' if ok else 'FAIL'}] {name:<24} {detail}")
    print()

    if failures:
        print(f"REPRODUCTION FAILED on: {', '.join(failures)}")
        print()
        print("This means the regenerated split is NOT the frozen split. Do NOT train on it.")
        print("Most likely cause: the image inventory differs (wrong Radiographs_rotated/,")
        print("missing files, or extra files), since the split is a function of the sorted")
        print("filename list. Check the image count and directory before anything else.")
        sys.exit(1)

    print("All four invariants hold — this IS the frozen split_v1.")

    if args.verify:
        print("(--verify: nothing written)")
        return

    if OUT_CSV.exists() and not args.force:
        existing = hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()
        if existing == EXPECTED_SHA256:
            print(f"\n{OUT_CSV} already present and correct — nothing to do.")
        else:
            print(f"\nREFUSING to overwrite existing {OUT_CSV} (hash {existing[:16]}…).")
            print("The split is write-once. Re-run with --force only if you are certain.")
            sys.exit(1)
        return

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.write_bytes(csv_bytes)
    print(f"\nWrote {OUT_CSV} ({len(csv_bytes)} bytes)")


if __name__ == "__main__":
    main()
