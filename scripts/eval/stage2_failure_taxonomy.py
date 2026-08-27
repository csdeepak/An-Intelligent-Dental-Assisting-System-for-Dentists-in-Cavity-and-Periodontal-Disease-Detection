#!/usr/bin/env python
"""
Failure taxonomy for Stage 2 (FDI numbering) -- WHERE the 41.7% of wrong codes come from.

WHY THIS MATTERS MORE THAN THE HEADLINE NUMBER
-----------------------------------------------
"58.3% end-to-end" says how often the pipeline is right and nothing about how it is wrong.
A reviewer -- and a dentist -- care whether the errors are harmless neighbours (tooth 26 called
27, same quadrant, adjacent position) or category mistakes (an upper-right molar called a
lower-left incisor). Those have completely different clinical consequences and completely
different fixes. `MASTER_PLAN_2026H2.md` W7 asks for exactly this: a taxonomy bucketed by
confounder.

Everything here is computed from `outputs/stage2_segdet/stage2_rows_head.json`, the 936 per-tooth
rows already saved by the 27 Aug evaluation. **No inference is re-run and no test data is
re-touched** -- this is analysis of a measurement that already happened.

THE BUCKETS, and why these
--------------------------
FDI codes are two digits: quadrant (1 upper-right, 2 upper-left, 3 lower-left, 4 lower-right)
and position (1 central incisor ... 8 third molar). Every wrong code is therefore wrong in the
quadrant, the position, or both, and those decompose into failures with different meanings:

  not_detected        Stage 1 never found the tooth. Not a numbering error at all, and it caps
                      everything downstream -- reported separately so the two are never conflated.
  correct             exact FDI match.
  off_by_one          right quadrant, position off by exactly 1. The benign neighbour error:
                      an adjacent tooth of usually the same type.
  same_quadrant_far   right quadrant, position off by 2+. A counting slip within an arch.
  mirror_lr           right arch and position, wrong SIDE (1<->2, 3<->4). Left-right confusion,
                      the error this dataset's mirrored Tufts labelling makes worth watching.
  wrong_arch          upper called lower or vice versa (1,2 <-> 3,4). The category mistake.
  other               wrong quadrant and wrong position, not fitting the above.

Usage:
    python scripts/eval/stage2_failure_taxonomy.py
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DEF_ROWS = REPO_ROOT / "outputs/stage2_segdet/stage2_rows_head.json"
DEF_CTL = REPO_ROOT / "outputs/stage2_control_olddet/stage2_rows_head.json"
DEF_OUT = REPO_ROOT / "outputs/stage2_taxonomy"
DEF_FIG = REPO_ROOT / "docs/results/figures/paper"

UPPER = {1, 2}
LOWER = {3, 4}
MIRROR = {1: 2, 2: 1, 3: 4, 4: 3}


def classify(gt, pred, detected):
    if not detected or pred is None:
        return "not_detected"
    if pred == gt:
        return "correct"
    gq, gp = gt // 10, gt % 10
    pq, pp = pred // 10, pred % 10
    if gq == pq:
        return "off_by_one" if abs(gp - pp) == 1 else "same_quadrant_far"
    if MIRROR.get(gq) == pq and gp == pp:
        return "mirror_lr"
    if (gq in UPPER) != (pq in UPPER):
        return "wrong_arch"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=Path, default=DEF_ROWS)
    ap.add_argument("--control", type=Path, default=DEF_CTL)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--fig", type=Path, default=DEF_FIG)
    args = ap.parse_args()

    rows = json.loads(args.rows.read_text(encoding="utf-8"))
    n = len(rows)
    cats = Counter()
    by_pos = defaultdict(Counter)
    by_quad = defaultdict(Counter)
    drift = Counter()
    for r in rows:
        gt, pred, det = r["gt_fdi"], r.get("pred_fdi"), bool(r.get("detected"))
        c = classify(gt, pred, det)
        cats[c] += 1
        by_pos[gt % 10][c] += 1
        by_quad[gt // 10][c] += 1
        if c == "off_by_one":
            drift["distal (+1)" if (pred % 10) > (gt % 10) else "mesial (-1)"] += 1

    print(f"STAGE 2 FAILURE TAXONOMY — {n} ground-truth teeth, 164 leak-free DENTEX images")
    print(f"source: {args.rows.name} (already-saved evaluation; nothing re-run)\n")
    order = ["correct", "not_detected", "off_by_one", "same_quadrant_far",
             "mirror_lr", "wrong_arch", "other"]
    for c in order:
        v = cats.get(c, 0)
        print(f"  {c:20s} {v:5d}  {v / n:6.1%}")

    detected = n - cats.get("not_detected", 0)
    wrong = detected - cats.get("correct", 0)
    print(f"\n  of the {detected} DETECTED teeth, {wrong} carry a wrong code ({wrong/detected:.1%}):")
    for c in order[2:]:
        v = cats.get(c, 0)
        if v:
            print(f"     {c:20s} {v:5d}  {v/wrong:6.1%} of all numbering errors")

    if drift:
        print(f"\n  off-by-one direction: {dict(drift)}"
              "   (a systematic lean would point at an indexing bug, not model noise)")

    print("\n  error rate by TOOTH POSITION (1 central incisor .. 8 third molar):")
    print("    pos    n   correct   wrong-code%")
    for pos in sorted(by_pos):
        cc = by_pos[pos]
        tot = sum(cc.values()); det = tot - cc.get("not_detected", 0)
        w = det - cc.get("correct", 0)
        print(f"     {pos}   {tot:4d}   {cc.get('correct',0):5d}   "
              f"{(w/det if det else 0):8.1%}")

    print("\n  error rate by QUADRANT (1 UR, 2 UL, 3 LL, 4 LR):")
    for q in sorted(by_quad):
        cc = by_quad[q]
        tot = sum(cc.values()); det = tot - cc.get("not_detected", 0)
        w = det - cc.get("correct", 0)
        print(f"     Q{q}  n={tot:4d}  detected={det:4d}  wrong-code={w/det if det else 0:.1%}")

    res = {"n_gt_teeth": n, "source": str(args.rows), "categories": dict(cats),
           "n_detected": detected, "n_wrong_code": wrong,
           "off_by_one_direction": dict(drift),
           "by_position": {str(k): dict(v) for k, v in sorted(by_pos.items())},
           "by_quadrant": {str(k): dict(v) for k, v in sorted(by_quad.items())},
           "note": "computed from an already-saved evaluation; no inference re-run, no test "
                   "data re-touched"}

    # control arm, if present -- did the detector swap change the SHAPE of the errors?
    if args.control.exists():
        crows = json.loads(args.control.read_text(encoding="utf-8"))
        ccats = Counter(classify(r["gt_fdi"], r.get("pred_fdi"), bool(r.get("detected")))
                        for r in crows)
        print(f"\n  SHAPE OF ERRORS, bbox control -> seg detector (n={len(crows)} vs {n}):")
        print(f"    {'category':20s} {'control':>9s} {'seg':>9s} {'delta':>8s}")
        for c in order:
            a, b = ccats.get(c, 0), cats.get(c, 0)
            print(f"    {c:20s} {a/len(crows):8.1%} {b/n:9.1%} {(b/n - a/len(crows)):+8.1%}")
        res["control_categories"] = dict(ccats)
        res["control_n"] = len(crows)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "stage2_failure_taxonomy.json").write_text(json.dumps(res, indent=2) + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
        labs = [c for c in order if cats.get(c)]
        vals = [cats[c] / n for c in labs]
        colors = ["#2a9d8f" if c == "correct" else "#adb5bd" if c == "not_detected" else "#e76f51"
                  for c in labs]
        ax[0].barh(labs[::-1], [v * 100 for v in vals][::-1], color=colors[::-1])
        ax[0].set_xlabel("% of all ground-truth teeth")
        ax[0].set_title(f"Stage-2 outcome taxonomy (n={n} teeth)")
        for i, v in enumerate(vals[::-1]):
            ax[0].text(v * 100 + 0.6, i, f"{v:.1%}", va="center", fontsize=8)
        poss = sorted(by_pos)
        rates = []
        for p_ in poss:
            cc = by_pos[p_]; det = sum(cc.values()) - cc.get("not_detected", 0)
            rates.append(100 * (det - cc.get("correct", 0)) / det if det else 0)
        ax[1].bar([str(p_) for p_ in poss], rates, color="#e76f51")
        ax[1].set_xlabel("tooth position (1 central incisor → 8 third molar)")
        ax[1].set_ylabel("% of detected teeth given a wrong FDI code")
        ax[1].set_title("Numbering error rate by tooth position")
        fig.tight_layout()
        args.fig.mkdir(parents=True, exist_ok=True)
        fp = args.fig / "stage2_failure_taxonomy.png"
        fig.savefig(fp, dpi=160)
        print(f"\n  figure -> {fp}")
    except Exception as exc:
        print(f"  (figure skipped: {exc})")

    print(f"-> {args.out / 'stage2_failure_taxonomy.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
