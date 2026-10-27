#!/usr/bin/env python
"""
Near-duplicate radiographs across the Tufts split (train / val / test of
`outputs/eda_tufts/split_v1.csv`).

The split is by radiograph. A near-twin of a test radiograph on the training side leaks the way
the crop-level split behind the old 0.923 did (RESULTS_LOG 2026-10-10). `bone_loss_heldout.py`
ran this check for one pair of sets -- the previous Stage-4a model's 145 radiographs against the
other 853 -- and found none; nobody had compared the three splits with each other.

Same hash and threshold as that check: a 256-bit difference hash (`bone_loss_heldout.dhash`) and
`NEAR_DUP_BITS`. Reads radiographs only: no label, no mask, no model.

    python scripts/eval/tufts_split_near_duplicates.py

Writes `outputs/eda_tufts/near_duplicates.json`, which `verify_invariants.py` reads.
"""

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
from bone_loss_heldout import NEAR_DUP_BITS, SRC, dhash  # noqa: E402

SPLIT = REPO_ROOT / "outputs/eda_tufts/split_v1.csv"
OUT = REPO_ROOT / "outputs/eda_tufts/near_duplicates.json"
REVIEW_BITS = 20          # pairs up to here are listed for a person to look at
# Pairs already accounted for. A new pair under the threshold is a finding, not a pass.
RECORDED = {
    ("590", "591"): "byte-identical; 590 dropped from Stage-4a training and scoring "
                    "(scripts/tufts/train_bone_loss_v2.py, DROP)",
    ("1008", "1007"): "byte-identical; 1008 dropped likewise",
    ("248", "1017"): "found by this script on 14 Oct 2026 at 7 bits: 248 (test) is a lighter "
                     "re-rendering of 1017 (train), same patient. Kept in the test split and "
                     "disclosed: 27 Stage-4a test teeth, none positive (RESULTS_LOG 2026-10-14)",
}


def main():
    rows = list(csv.DictReader(open(SPLIT)))
    split = {Path(r["filename"]).stem: r["split"].strip() for r in rows}
    stems = list(split)
    h = np.array([dhash(SRC / "Radiographs" / f"{s}.JPG") for s in stems])   # (N, 256) bool

    nearest, pairs = [], []
    for i, s in enumerate(stems):
        d = (h != h[i]).sum(1)
        d[i] = h.shape[1] + 1
        nearest.append(int(d.min()))
        for j in np.flatnonzero(d <= REVIEW_BITS):
            if j > i and split[s] != split[stems[j]]:
                pairs.append({"a": s, "split_a": split[s], "b": stems[j],
                              "split_b": split[stems[j]], "bits": int(d[j])})
    pairs.sort(key=lambda p: (p["bits"], p["a"]))

    known = {frozenset(k) for k in RECORDED}
    unexplained = [p for p in pairs
                   if p["bits"] <= NEAR_DUP_BITS and frozenset((p["a"], p["b"])) not in known]
    res = {
        "method": "256-bit difference hash (scripts/eval/bone_loss_heldout.py dhash), Hamming distance",
        "threshold_bits": NEAR_DUP_BITS,
        "review_bits": REVIEW_BITS,
        "n_radiographs": len(stems),
        "split_counts": {k: sum(v == k for v in split.values()) for k in ("train", "val", "test")},
        "nearest_neighbour_bits_all_radiographs": {
            "min": int(np.min(nearest)), "p5": float(np.percentile(nearest, 5)),
            "median": float(np.median(nearest))},
        "recorded_pairs": [{"a": a, "b": b, "note": n} for (a, b), n in RECORDED.items()],
        "cross_split_pairs_within_review_bits": pairs,
        "unexplained_at_threshold": unexplained,
    }
    OUT.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(f"{len(stems)} radiographs; nearest-neighbour bits {res['nearest_neighbour_bits_all_radiographs']}")
    print(f"cross-split pairs <= {REVIEW_BITS} bits: {len(pairs)}; "
          f"unexplained <= {NEAR_DUP_BITS} bits: {len(unexplained)}")
    for p in pairs[:15]:
        print(f"  {p['bits']:3d} bits  {p['a']} ({p['split_a']})  {p['b']} ({p['split_b']})")
    print(f"-> {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
