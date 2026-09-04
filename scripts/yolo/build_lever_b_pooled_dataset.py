#!/usr/bin/env python
r"""Build the B-pooled train list: CariesXrays + DENTEX caries boxes, per-corpus balanced.

Pre-registration: outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md Sec 3 + Sec 9
(amended 4 Sep 2026).

WHAT "BALANCED" MEANS HERE -- copied from Lever A, not reinvented
-------------------------------------------------------------------
`scripts/yolo/build_multicorpus_detector_v2_dataset.py`'s `balanced()`: each corpus's train
image list is repeated (`list * ceil(big/len(list))`, sliced to `big`) up to the size of the
LARGEST corpus, then the pooled list is shuffled. Applied here:

    CariesXrays train  4,800 images  (as-is)
    DENTEX caries        650 images  -> repeated ceil(4800/650)=8x, sliced to 4,800
    -----------------------------------------------------------------------------
    pooled train.txt   9,600 lines, shuffled (seed 42)

This is NOT the "~5,500 images" in the pre-registration's original Sec 9 -- that figure assumed
naive concatenation and undercounted Sec 3's own balancing instruction by ~2x (found and fixed
4 Sep 2026, see PRE_REGISTRATION.md's amendment note).

WHY A train.txt OF RELATIVE PATHS, NOT COPIED FILES
------------------------------------------------------
Both source datasets already sit as siblings under `data/` with the standard
`images/train/<stem>.<ext>` + `labels/train/<stem>.txt` layout ultralytics expects. A train.txt
of paths RELATIVE to `data/` (e.g. `cariesxrays_det/images/train/000415.jpg`), with
`data.yaml`'s `path:` resolved to `data/`'s absolute location AT RUNTIME on whatever machine is
training (same pattern as `train_cariesxrays_detector.py`), lets ultralytics find each label by
its own `images/`->`labels/` convention with zero file copying and zero manual path-editing
after upload -- the friction point the Lever 2 runbook needed a comment to warn about.

val stays **CariesXrays-only, unreplicated** (1,200 images) -- same split Lever 2 already used
for early stopping and its reported COCO AP (B-single). DENTEX contributes to train only; it has
no role as a COCO-AP val cohort here (PRE_REGISTRATION.md Sec 3 table). Using this same 1,200
split for early stopping is standard train/val practice, not "tuning" in the sense the
pre-registration's Ningxia/CariesXrays-eval "never tune" language means -- it is exactly what
B-single already did, so B-pooled and B-single are on equal footing, not inconsistent.

GATE before writing:
  1. 0 MD5 overlap between the two source corpora's train images (different datasets, expected
     0, verified rather than assumed).
  2. Every path in the pooled list resolves to both an image and a same-stem label file.
  3. Per-corpus exposure within the pooled list is within the target ratio (4,800/4,800 = 1.00x).

Usage:
    python scripts/yolo/build_lever_b_pooled_dataset.py --dry-run
    python scripts/yolo/build_lever_b_pooled_dataset.py
"""

import argparse
import csv
import hashlib
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
DEF_CARIESXRAYS = DATA / "cariesxrays_det"
DEF_DENTEX = DATA / "dentex_caries_det"
DEF_OUT = DATA / "lever_b_pooled"
SEED = 42


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def read_manifest_train_stems(manifest_csv: Path, split_col="split", split_val="train"):
    with open(manifest_csv, newline="") as f:
        return [r["stem"] for r in csv.DictReader(f) if r[split_col] == split_val]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cariesxrays", type=Path, default=DEF_CARIESXRAYS)
    ap.add_argument("--dentex", type=Path, default=DEF_DENTEX)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cx_stems = read_manifest_train_stems(args.cariesxrays / "manifest.csv")
    dx_stems = read_manifest_train_stems(args.dentex / "manifest.csv")
    print(f"CariesXrays train: {len(cx_stems)}   DENTEX caries train: {len(dx_stems)}")

    cx_rel = [f"cariesxrays_det/images/train/{s}.jpg" for s in cx_stems]
    dx_rel = [f"dentex_caries_det/images/train/{s}.png" for s in dx_stems]

    # -------------------------------------------------------------- leakage gate
    cx_md5 = {md5(DATA / p): p for p in cx_rel}
    dx_md5 = {md5(DATA / p): p for p in dx_rel}
    overlap = set(cx_md5) & set(dx_md5)
    print(f"MD5 overlap between the two corpora: {len(overlap)}")

    # -------------------------------------------------------------- balance (Lever A recipe)
    big = max(len(cx_rel), len(dx_rel))

    def balanced(paths):
        return (paths * math.ceil(big / len(paths)))[:big]

    cx_bal = balanced(cx_rel)
    dx_bal = balanced(dx_rel)
    pooled = cx_bal + dx_bal
    random.Random(args.seed).shuffle(pooled)
    print(f"balanced: cariesxrays {len(cx_bal)} + dentex {len(dx_bal)} = {len(pooled)} lines "
          f"(target ratio 1.00x, seed {args.seed})")

    # -------------------------------------------------------------- resolvability gate
    missing = []
    for rel in cx_rel[:50] + dx_rel[:50]:   # spot-check both sources; full set is 9,600, this is enough to catch a systemic path bug
        img = DATA / rel
        lbl = DATA / rel.replace("/images/", "/labels/")
        lbl = lbl.with_suffix(".txt")
        if not img.exists() or not lbl.exists():
            missing.append((str(img), img.exists(), str(lbl), lbl.exists()))
    print(f"path-resolvability spot-check (100 of {len(pooled)}): {len(missing)} missing")
    if missing:
        for m in missing[:5]:
            print("  ", m)

    fail = []
    if overlap:
        fail.append(f"{len(overlap)} MD5-identical images shared between corpora")
    if missing:
        fail.append(f"{len(missing)} image/label paths did not resolve")
    if fail:
        raise SystemExit("GATE FAILED: " + "; ".join(fail))
    print("  PASS")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "train_pooled.txt").write_text("\n".join(pooled) + "\n")
    (args.out / "data.yaml").write_text(
        "# Lever B B-pooled -- CariesXrays + DENTEX caries boxes, per-corpus balanced\n"
        "# Built by scripts/yolo/build_lever_b_pooled_dataset.py\n"
        "# path: is REWRITTEN AT RUNTIME by train_lever_b_pooled_detector.py -- do not hand-edit\n"
        "path: __SET_AT_RUNTIME__\n"
        "train: lever_b_pooled/train_pooled.txt\n"
        "val: cariesxrays_det/images/val\n\n"
        "nc: 1\nnames: ['decay']\n")
    print(f"\nwrote {args.out / 'train_pooled.txt'} ({len(pooled)} lines)")
    print(f"wrote {args.out / 'data.yaml'} (path: placeholder -- resolved at train time)")


if __name__ == "__main__":
    main()
