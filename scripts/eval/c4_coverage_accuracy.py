#!/usr/bin/env python
"""
C4 — abstention: coverage–accuracy curves for Stage 2 and the caries gate.

WHAT R3/C4 ASKS FOR
-------------------
`MASTER_PLAN_2026H2.md` §R3: "an explicit `not_assessable` output with a calibrated threshold,
reported as a coverage–accuracy curve (accuracy at 100% / 90% / 75% coverage)". The pipeline has
emitted an `assessable` flag since R4, and calibration landed on 27 Aug — but the curve itself was
never produced, so C4 has been sitting at zero while looking done.

The clinical argument is the one HC-Net+ and DentiAsk both document: a system that silently
returns a confident wrong answer on a hard case is worse than one that declines. A coverage–
accuracy curve is how you show a model knows when to stop.

THE DISCIPLINE THAT GOVERNS THIS SCRIPT
----------------------------------------
`run_inference.py` fixes `ASSESSABILITY_MIN_FDI_CONFIDENCE = 0.30`, and its comment is explicit:
*"fixed a priori and must not be swept against an evaluation set."*

**So this script does NOT tune the threshold.** It draws the curve and marks where the existing,
pre-registered 0.30 lands on it. Reporting "we swept the threshold and 0.42 was best on the test
set" would be selecting an operating point on the data it is then evaluated on — precisely the
error the constant in that file was written to prevent. If 0.30 turns out to sit badly, that is a
finding to report, not a number to quietly replace.

TWO CURVES
----------
* **Stage 2 (FDI numbering)** — the headline stage. Confidence is the numbering head's own score;
  correctness is `pred_fdi == gt_fdi`. Computed from the saved 936-row evaluation, no re-run.
* **Caries gate** — confidence is the ISOTONIC-CALIBRATED probability (27 Aug), because an
  abstention rule built on scores known to be systematically overconfident would abstain in the
  wrong places. This one re-scores the 863 held-out crops (~1 min, CPU).

Usage:
    python scripts/eval/c4_coverage_accuracy.py
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DEF_OUT = REPO_ROOT / "outputs" / "c4_abstention"
DEF_FIG = REPO_ROOT / "docs/results/figures/paper"
OPERATING_POINT = 0.30          # ASSESSABILITY_MIN_FDI_CONFIDENCE -- pre-registered, not tuned


def curve(items):
    """items: list of (confidence, correct). Returns coverage/accuracy sweep, most-confident first."""
    items = sorted(items, key=lambda x: -x[0])
    n = len(items)
    out = []
    correct = 0
    for i, (c, ok) in enumerate(items, 1):
        correct += int(ok)
        out.append({"coverage": i / n, "n_retained": i, "accuracy": correct / i,
                    "threshold_at_this_coverage": c})
    return out


def at_coverage(cv, target):
    best = min(cv, key=lambda r: abs(r["coverage"] - target))
    return best


def gain_stats(items, groups, target=0.75, n_boot=1000, seed=0):
    """Is the accuracy gain from abstaining REAL, and does it come from the confidence ranking?

    Two things a coverage-accuracy curve cannot show on its own:

    1. **Is the rise bigger than sampling noise?** Bootstrapped CI on (acc@target - acc@100%),
       resampling IMAGES not teeth -- teeth within one radiograph are not independent, the same
       correction as everywhere else in this project (RESULTS_LOG 2026-08-27n).
    2. **Does the rise come from the confidence being informative, or would ANY abstention rule
       do as well?** The control shuffles the confidences, breaking the confidence-correctness
       link while preserving both marginals. A shuffled curve is flat at the base rate. This is
       the same move as C1's constant-guess control: show what the number looks like when the
       mechanism is removed.
    """
    import numpy as np
    rng = np.random.default_rng(seed)
    conf = np.array([c for c, _ in items], float)
    ok = np.array([bool(o) for _, o in items])
    g = np.asarray(groups)
    base = float(ok.mean())

    def acc_at(c, o, t):
        idx = np.argsort(-c, kind="stable")
        k = max(1, int(round(t * len(c))))
        return float(o[idx[:k]].mean())

    observed = acc_at(conf, ok, target) - base

    uniq = np.unique(g)
    idx_by = {u: np.flatnonzero(g == u) for u in uniq}
    deltas = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        sel = np.concatenate([idx_by[u] for u in pick])
        c, o = conf[sel], ok[sel]
        deltas.append(acc_at(c, o, target) - float(o.mean()))
    lo, hi = np.percentile(deltas, [2.5, 97.5])

    shuf = [acc_at(rng.permutation(conf), ok, target) - base for _ in range(200)]
    return {"target_coverage": target, "accuracy_full_coverage": round(base, 4),
            "gain_pp": round(observed * 100, 2),
            "ci95_pp": [round(float(lo) * 100, 2), round(float(hi) * 100, 2)],
            "n_images": int(len(uniq)),
            "shuffled_control_gain_pp": round(float(np.mean(shuf)) * 100, 2),
            "shuffled_control_note": "confidence shuffled -> abstention carries no information; "
                                     "a real gain must clear this"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--fig", type=Path, default=DEF_FIG)
    ap.add_argument("--crops", type=Path, default=REPO_ROOT / "data/dentex/crops_v3_phase1")
    args = ap.parse_args()

    import numpy as np
    results = {}

    # ---------------------------------------------------------------- Stage 2
    rows = json.loads((REPO_ROOT / "outputs/stage2_segdet/stage2_rows_head.json")
                      .read_text(encoding="utf-8"))
    det = [r for r in rows if r.get("detected") and r.get("pred_fdi") is not None]
    s2 = [(float(r.get("confidence", 0.0)), r["pred_fdi"] == r["gt_fdi"]) for r in det]
    cv2_ = curve(s2)
    base2 = sum(ok for _, ok in s2) / len(s2)
    # Where does the PRE-REGISTERED threshold land? (not chosen here, only located)
    kept = [(c, ok) for c, ok in s2 if c >= OPERATING_POINT]
    op2 = {"threshold": OPERATING_POINT, "coverage": len(kept) / len(s2),
           "accuracy": (sum(ok for _, ok in kept) / len(kept)) if kept else None}

    print(f"STAGE 2 — FDI numbering, {len(det)} detected teeth (of {len(rows)} GT)")
    print(f"  accuracy at 100% coverage : {base2:.3f}   <- the 82.6% of-detected figure")
    for t in (0.90, 0.75, 0.50):
        r = at_coverage(cv2_, t)
        print(f"  accuracy at {t:.0%} coverage  : {r['accuracy']:.3f}"
              f"   (confidence >= {r['threshold_at_this_coverage']:.3f})")
    print(f"  PRE-REGISTERED threshold {OPERATING_POINT}: coverage {op2['coverage']:.1%}, "
          f"accuracy {op2['accuracy']:.3f}")
    g2 = gain_stats(s2, [r["image"] for r in det])
    print(f"  gain at 75% coverage      : {g2['gain_pp']:+.2f} pp "
          f"[{g2['ci95_pp'][0]:+.2f}, {g2['ci95_pp'][1]:+.2f}]  "
          f"(shuffled control {g2['shuffled_control_gain_pp']:+.2f} pp)")
    results["stage2"] = {"n": len(s2), "accuracy_full_coverage": round(base2, 4),
                         "gain_at_75": g2,
                         "operating_point": {k: (round(v, 4) if isinstance(v, float) else v)
                                             for k, v in op2.items()},
                         "at_90": at_coverage(cv2_, 0.90), "at_75": at_coverage(cv2_, 0.75),
                         "at_50": at_coverage(cv2_, 0.50)}

    # ---------------------------------------------------------------- caries gate
    cv3_ = None
    man_p = args.crops / "manifest.csv"
    if man_p.exists():
        import cv2 as cv
        import pandas as pd
        import torch
        from torchvision import transforms

        from src.classifiers import IMAGENET_MEAN, IMAGENET_STD, load_classifier
        man = pd.read_csv(man_p)
        man = man[man["split"] == "test"].reset_index(drop=True)
        model, cls = load_classifier(
            REPO_ROOT / "models/09_caries_gate_v3/caries_gate_v3.pth", 2, torch.device("cpu"))
        pos = (cls or {"caries": 0})["caries"]
        tf = transforms.Compose([transforms.ToTensor(),
                                 transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
        probs, batch = [], []
        for i, r in man.iterrows():
            im = cv.imread(str(args.crops / "test" / r["label"] / r["crop"]), cv.IMREAD_COLOR)
            batch.append(tf(cv.cvtColor(cv.resize(im, (224, 224)), cv.COLOR_BGR2RGB)))
            if len(batch) == 64 or i == len(man) - 1:
                with torch.no_grad():
                    p = torch.softmax(model(torch.stack(batch)), 1).numpy()
                probs.extend(p[:, pos].tolist()); batch = []
        p = np.array(probs)
        y = (man["label"] == "caries").astype(int).to_numpy()

        # Calibrated confidence -- an abstention rule built on overconfident scores abstains
        # in the wrong places (RESULTS_LOG 2026-08-27q/s).
        kp = REPO_ROOT / "models/09_caries_gate_v3/isotonic_calibrator.json"
        d = json.loads(kp.read_text(encoding="utf-8"))
        p_cal = np.interp(p, np.asarray(d["x"], float), np.asarray(d["y"], float))
        pred = (p >= 0.5).astype(int)                      # verdict stays raw argmax
        conf = np.where(pred == 1, p_cal, 1.0 - p_cal)     # confidence IN THE REPORTED CLASS
        c3 = list(zip(conf.tolist(), (pred == y).tolist()))
        cv3_ = curve(c3)
        base3 = float((pred == y).mean())
        print(f"\nCARIES GATE — {len(c3)} held-out crops (calibrated confidence)")
        print(f"  accuracy at 100% coverage : {base3:.3f}")
        for t in (0.90, 0.75, 0.50):
            r = at_coverage(cv3_, t)
            print(f"  accuracy at {t:.0%} coverage  : {r['accuracy']:.3f}"
                  f"   (confidence >= {r['threshold_at_this_coverage']:.3f})")
        g3 = gain_stats(c3, man["source_image_md5"].tolist())
        print(f"  gain at 75% coverage      : {g3['gain_pp']:+.2f} pp "
              f"[{g3['ci95_pp'][0]:+.2f}, {g3['ci95_pp'][1]:+.2f}]  "
              f"(shuffled control {g3['shuffled_control_gain_pp']:+.2f} pp)")
        results["caries_gate"] = {"n": len(c3), "accuracy_full_coverage": round(base3, 4),
                                  "gain_at_75": g3,
                                  "at_90": at_coverage(cv3_, 0.90),
                                  "at_75": at_coverage(cv3_, 0.75),
                                  "at_50": at_coverage(cv3_, 0.50),
                                  "confidence": "isotonic-calibrated, in the reported class"}

    results["discipline"] = ("ASSESSABILITY_MIN_FDI_CONFIDENCE = 0.30 is pre-registered in "
                             "run_inference.py and was NOT tuned here; the curve only locates it")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "c4_coverage_accuracy.json").write_text(json.dumps(results, indent=2) + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2 if cv3_ else 1, figsize=(11 if cv3_ else 6, 4.4))
        axes = ax if cv3_ else [ax]
        for a, cvx, title, base in ((axes[0], cv2_, "Stage 2 — FDI numbering", base2),
                                    *(((axes[1], cv3_, "Caries gate (calibrated)", base3),)
                                      if cv3_ else ())):
            a.plot([r["coverage"] * 100 for r in cvx], [r["accuracy"] * 100 for r in cvx],
                   color="#264653")
            a.axhline(base * 100, ls="--", lw=1, color="grey",
                      label=f"full-coverage accuracy {base:.3f}")
            a.set_xlabel("coverage (% of teeth retained)")
            a.set_ylabel("accuracy on retained (%)")
            a.set_title(title); a.set_xlim(0, 100); a.legend(fontsize=8)
        axes[0].axvline(op2["coverage"] * 100, color="#e76f51", lw=1.2,
                        label=f"pre-registered 0.30")
        axes[0].legend(fontsize=8)
        fig.suptitle("C4 — coverage–accuracy (abstention). Threshold NOT tuned here.", fontsize=10)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        args.fig.mkdir(parents=True, exist_ok=True)
        fp = args.fig / "c4_coverage_accuracy.png"
        fig.savefig(fp, dpi=160)
        print(f"\n  figure -> {fp}")
    except Exception as exc:
        print(f"  (figure skipped: {exc})")

    print(f"-> {args.out / 'c4_coverage_accuracy.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
