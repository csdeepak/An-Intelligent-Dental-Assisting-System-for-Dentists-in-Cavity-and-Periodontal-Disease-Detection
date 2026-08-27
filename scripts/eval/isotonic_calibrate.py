#!/usr/bin/env python
"""
Isotonic calibration for the frozen caries gate -- the fix with enough capacity for a shape.

WHY THIS AFTER TEMPERATURE SCALING FAILED
------------------------------------------
2026-08-27r fitted a single temperature and it made ECE **worse** (0.136 -> 0.152). The diagnosis
was that the gate's miscalibration is a *shape* error, not a *scale* one: observed frequency is
flat at ~0.27 across predicted 0.50-0.85 and then jumps to 0.69. One scalar cannot re-bend that.
Isotonic regression fits an arbitrary non-decreasing step function and therefore *can*.

TWO THINGS THAT DIFFER FROM TEMPERATURE SCALING, AND BOTH MATTER
-----------------------------------------------------------------
1. **AP is no longer guaranteed identical.** Temperature scaling is *strictly* monotonic, so
   ranking -- and therefore average precision -- is invariant, and 27r used that as a correctness
   check. Isotonic is only *weakly* monotonic: it produces flat regions, which turn distinct
   scores into ties and genuinely reduce ranking resolution. So AP may move slightly, and a small
   drop is a real cost of the method rather than a bug. This script reports it instead of
   asserting invariance.
2. **Decisions CAN change.** Temperature scaling cannot move `argmax`; isotonic remaps the score
   axis, so the 0.5 cut lands somewhere else in raw-score space. The number of flipped verdicts is
   measured and reported, because it means published decision-based numbers would need re-checking
   before this could be adopted.

OVERFITTING IS THE REAL RISK
-----------------------------
Isotonic has far more freedom than one scalar, and it is fitted on 1,003 val crops of which only
199 are positive. In sparse score regions it can fit noise. The script therefore reports the
in-sample (val) calibration alongside the out-of-sample (test) one: **a large val-vs-test gap is
the signature of overfitting**, and is the thing that decides whether this is adoptable.

Discipline unchanged: **fitted on VAL, evaluated once on TEST.**

Usage:
    python scripts/eval/isotonic_calibrate.py
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

DEF_CROPS = REPO_ROOT / "data/dentex/crops_v3_phase1"
DEF_WEIGHTS = REPO_ROOT / "models/09_caries_gate_v3/caries_gate_v3.pth"
DEF_OUT = REPO_ROOT / "outputs/calibration"
DEF_FIG = REPO_ROOT / "docs/results/figures/paper"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", type=Path, default=DEF_CROPS)
    ap.add_argument("--weights", type=Path, default=DEF_WEIGHTS)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--fig", type=Path, default=DEF_FIG)
    args = ap.parse_args()

    import numpy as np
    import torch
    from sklearn.isotonic import IsotonicRegression
    from sklearn.metrics import average_precision_score

    from src.classifiers import load_classifier
    # Reused, not reimplemented: the preprocessing is the risky part and must be identical to
    # 27q/27r or the comparison is between two different models.
    from temperature_scale import ece_mce, logits_for

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, cls = load_classifier(args.weights, 2, device)
    if cls and cls != {"caries": 0, "no_caries": 1}:
        raise SystemExit(f"unexpected class order: {cls}")
    pos = (cls or {"caries": 0})["caries"]

    print("scoring val (isotonic is FITTED here) …")
    zv, yv, _ = logits_for("val", args.crops, model, device)
    print("scoring test (evaluated once) …")
    zt, yt, _ = logits_for("test", args.crops, model, device)

    def softmax_pos(z):
        e = np.exp(z - z.max(axis=1, keepdims=True))
        return (e / e.sum(axis=1, keepdims=True))[:, pos]

    pv, pt = softmax_pos(zv), softmax_pos(zt)
    print(f"  val n={len(yv)} ({yv.mean():.1%} pos)   test n={len(yt)} ({yt.mean():.1%} pos)")

    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(pv, yv)
    pv_cal, pt_cal = iso.predict(pv), iso.predict(pt)

    e0, m0, rel0 = ece_mce(pt, yt)
    e1, m1, rel1 = ece_mce(pt_cal, yt)
    ev0, _, _ = ece_mce(pv, yv)
    ev1, _, _ = ece_mce(pv_cal, yv)
    b0 = float(np.mean((pt - yt) ** 2)); b1 = float(np.mean((pt_cal - yt) ** 2))
    ap0 = float(average_precision_score(yt, pt)); ap1 = float(average_precision_score(yt, pt_cal))
    flipped = int(((pt >= 0.5) != (pt_cal >= 0.5)).sum())
    n_unique = int(len(np.unique(pt_cal)))

    print(f"\n  TEST (n={len(yt)}), before -> after isotonic")
    d = "IMPROVED" if e1 < e0 else "WORSE"
    print(f"    ECE     {e0:.4f} -> {e1:.4f}   {d} by {abs(e1-e0)/e0:.0%}")
    print(f"    MCE     {m0:.4f} -> {m1:.4f}")
    print(f"    Brier   {b0:.4f} -> {b1:.4f}")
    print(f"    AP      {ap0:.4f} -> {ap1:.4f}   (may drop: isotonic creates ties)")
    print(f"    distinct calibrated values on test: {n_unique} (fewer = more ranking collapsed)")
    print(f"    verdicts flipped at threshold 0.5: {flipped} of {len(yt)}")
    print(f"\n  OVERFITTING CHECK  val ECE {ev0:.4f} -> {ev1:.4f} (in-sample)")
    print(f"                     test ECE {e0:.4f} -> {e1:.4f} (out-of-sample)")
    gap = abs(ev1 - e1)
    print(f"                     val-vs-test gap after fitting: {gap:.4f}"
          f"   {'LARGE - suspect overfitting' if gap > 0.05 else 'small'}")

    res = {"method": "isotonic regression", "fitted_on": "val", "evaluated_on": "test",
           "n_val": int(len(yv)), "n_test": int(len(yt)),
           "test": {"ece": [round(e0, 4), round(e1, 4)], "mce": [round(m0, 4), round(m1, 4)],
                    "brier": [round(b0, 4), round(b1, 4)],
                    "average_precision": [round(ap0, 4), round(ap1, 4)]},
           "val_ece": [round(ev0, 4), round(ev1, 4)],
           "val_test_ece_gap_after": round(gap, 4),
           "verdicts_flipped_at_0.5": flipped,
           "distinct_calibrated_values_test": n_unique,
           "caveats": ["isotonic is only weakly monotonic, so AP can drop through ties -- that is "
                       "a real cost, not a bug",
                       "decisions CAN change, unlike temperature scaling; flipped count above",
                       "fitted on 1,003 val crops with 199 positives -- overfitting risk is the "
                       "reason val and test calibration are both reported"]}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "caries_gate_isotonic.json").write_text(json.dumps(res, indent=2) + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axx = plt.subplots(1, 1, figsize=(5.8, 5.2))
        axx.plot([0, 1], [0, 1], "--", color="grey", lw=1, label="perfect calibration")
        for rel, lab, col in ((rel0, f"raw (ECE {e0:.3f})", "#c1121f"),
                              (rel1, f"isotonic (ECE {e1:.3f})", "#264653")):
            pts = [v for v in rel if v]
            axx.plot([c for c, _, _ in pts], [o for _, o, _ in pts], "o-", color=col, label=lab)
        axx.set_xlabel("mean predicted P(caries)"); axx.set_ylabel("observed fraction")
        axx.set_title(f"Caries gate — isotonic calibration, test (n={len(yt)})")
        axx.legend(fontsize=8); axx.set_xlim(0, 1); axx.set_ylim(0, 1)
        fig.tight_layout()
        args.fig.mkdir(parents=True, exist_ok=True)
        fp = args.fig / "caries_gate_isotonic.png"
        fig.savefig(fp, dpi=160)
        print(f"  figure -> {fp}")
    except Exception as exc:
        print(f"  (figure skipped: {exc})")

    print(f"\n-> {args.out / 'caries_gate_isotonic.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
