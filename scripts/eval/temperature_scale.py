#!/usr/bin/env python
"""
Temperature-scale the frozen caries gate, and measure whether it actually helps.

WHAT THIS IS
------------
2026-08-27q measured the gate as **systematically overconfident** -- ECE 0.136, every reliability
bin below the diagonal, a predicted 0.85 corresponding to an observed 0.26. Temperature scaling
(Guo et al., 2017) fits ONE scalar T and reports softmax(z / T). It is the cheapest possible
calibration fix: no retraining, no architecture change, one parameter.

TWO PROPERTIES THAT MAKE THIS SAFE TO ADOPT
-------------------------------------------
1. **It cannot change any decision.** For a two-class softmax, argmax(z/T) == argmax(z) for any
   T > 0 -- dividing both logits by the same positive number cannot reorder them. So every
   `caries` / `no_caries` verdict this pipeline has ever produced stays identical, and no
   published number that depends on the decisions moves. Only the *confidences* change.
2. **It cannot change ranking-based metrics.** T is a strictly monotonic transform of the score,
   so average precision, the PR curve and any AUC are invariant by construction. AP staying at
   exactly 0.550 is therefore a CORRECTNESS CHECK on this script, not a disappointing result --
   if AP moves, the implementation is wrong.

DISCIPLINE
----------
**T is fitted on the VALIDATION split and evaluated on TEST.** Fitting it on test would be
tuning on the test set -- the same error this project refuses to make with Ningxia, at a smaller
scale. The val split (1,003 crops) is what the checkpoint was already selected on, so it is
already "spent" for this purpose; test (863 crops) stays clean and is touched once.

Usage:
    python scripts/eval/temperature_scale.py
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DEF_CROPS = REPO_ROOT / "data/dentex/crops_v3_phase1"
DEF_WEIGHTS = REPO_ROOT / "models/09_caries_gate_v3/caries_gate_v3.pth"
DEF_OUT = REPO_ROOT / "outputs/calibration"
DEF_FIG = REPO_ROOT / "docs/results/figures/paper"


def logits_for(split, crops, model, device, batch_size=64):
    import cv2
    import numpy as np
    import pandas as pd
    import torch
    from torchvision import transforms
    from src.classifiers import IMAGENET_MEAN, IMAGENET_STD

    man = pd.read_csv(crops / "manifest.csv")
    man = man[man["split"] == split].reset_index(drop=True)
    tf = transforms.Compose([transforms.ToTensor(),
                             transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
    out, labels, groups, batch = [], [], [], []
    for i, r in man.iterrows():
        img = cv2.imread(str(crops / split / r["label"] / r["crop"]), cv2.IMREAD_COLOR)
        if img is None:
            raise SystemExit(f"cannot read crop {r['crop']}")
        img = cv2.resize(img, (224, 224), interpolation=cv2.INTER_LINEAR)
        batch.append(tf(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
        labels.append(1 if r["label"] == "caries" else 0)
        groups.append(r["source_image_md5"])
        if len(batch) == batch_size or i == len(man) - 1:
            with torch.no_grad():
                out.append(model(torch.stack(batch).to(device)).cpu().numpy())
            batch = []
    return np.concatenate(out), np.array(labels), np.array(groups)


def ece_mce(p, y, bins=10):
    import numpy as np
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    ece = mce = 0.0
    rel = []
    for b in range(bins):
        m = idx == b
        if not m.any():
            rel.append(None)
            continue
        conf, obs, n = float(p[m].mean()), float(y[m].mean()), int(m.sum())
        ece += n / len(p) * abs(conf - obs)
        mce = max(mce, abs(conf - obs))
        rel.append((conf, obs, n))
    return ece, mce, rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", type=Path, default=DEF_CROPS)
    ap.add_argument("--weights", type=Path, default=DEF_WEIGHTS)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--fig", type=Path, default=DEF_FIG)
    args = ap.parse_args()

    import numpy as np
    import torch
    from scipy.optimize import minimize_scalar
    from sklearn.metrics import average_precision_score

    from src.classifiers import load_classifier

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, cls = load_classifier(args.weights, 2, device)
    if cls and cls != {"caries": 0, "no_caries": 1}:
        raise SystemExit(f"unexpected class order: {cls}")
    pos = (cls or {"caries": 0})["caries"]
    print(f"device={device}  positive index={pos}")

    print("scoring val (T is FITTED here) …")
    zv, yv, _ = logits_for("val", args.crops, model, device)
    print("scoring test (T is EVALUATED here, touched once) …")
    zt, yt, gt = logits_for("test", args.crops, model, device)
    print(f"  val n={len(yv)} ({yv.mean():.1%} pos)   test n={len(yt)} ({yt.mean():.1%} pos)")

    def probs(z, T):
        e = np.exp((z - z.max(axis=1, keepdims=True)) / T)
        return (e / e.sum(axis=1, keepdims=True))[:, pos]

    def nll(T):
        if T <= 0:
            return 1e9
        q = np.clip(probs(zv, T), 1e-12, 1 - 1e-12)
        return float(-np.mean(yv * np.log(q) + (1 - yv) * np.log(1 - q)))

    r = minimize_scalar(nll, bounds=(0.05, 20.0), method="bounded")
    T = float(r.x)
    print(f"\n  fitted T = {T:.4f}   (val NLL {nll(1.0):.4f} -> {nll(T):.4f})")
    if T > 1:
        print("  T > 1 => the model was OVERCONFIDENT and is being softened, as 27q predicted.")

    p_before, p_after = probs(zt, 1.0), probs(zt, T)
    e0, m0, rel0 = ece_mce(p_before, yt)
    e1, m1, rel1 = ece_mce(p_after, yt)
    b0 = float(np.mean((p_before - yt) ** 2)); b1 = float(np.mean((p_after - yt) ** 2))
    ap0 = float(average_precision_score(yt, p_before)); ap1 = float(average_precision_score(yt, p_after))
    dec_same = bool(((p_before >= 0.5) == (p_after >= 0.5)).all())

    print(f"\n  TEST (n={len(yt)}), before -> after temperature scaling")
    # Print the direction in words. "(-12%)" for an ECE that ROSE is exactly the kind of
    # label that gets copied into a table as an improvement.
    _dir = "IMPROVED" if e1 < e0 else "WORSE"
    print(f"    ECE     {e0:.4f} -> {e1:.4f}   {_dir} by {abs(e1-e0)/e0:.0%}")
    print(f"    MCE     {m0:.4f} -> {m1:.4f}")
    print(f"    Brier   {b0:.4f} -> {b1:.4f}")
    print(f"    AP      {ap0:.4f} -> {ap1:.4f}   (MUST be identical -- monotonic transform)")
    print(f"    decisions identical at threshold 0.5: {dec_same}")
    if abs(ap0 - ap1) > 1e-9:
        print("    !! AP MOVED -- implementation bug, temperature scaling cannot change ranking")

    res = {"temperature": round(T, 4), "fitted_on": "val", "evaluated_on": "test",
           "n_val": int(len(yv)), "n_test": int(len(yt)),
           "val_nll_before": round(nll(1.0), 4), "val_nll_after": round(nll(T), 4),
           "test": {"ece": [round(e0, 4), round(e1, 4)], "mce": [round(m0, 4), round(m1, 4)],
                    "brier": [round(b0, 4), round(b1, 4)],
                    "average_precision": [round(ap0, 4), round(ap1, 4)]},
           "decisions_unchanged_at_0.5": dec_same,
           "note": "argmax(z/T) == argmax(z) for T>0, so no verdict and no decision-based "
                   "published number changes; only reported confidences do. AP is invariant "
                   "by construction and is used here as a correctness check."}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "caries_gate_temperature.json").write_text(json.dumps(res, indent=2) + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axx = plt.subplots(1, 1, figsize=(5.6, 5.0))
        axx.plot([0, 1], [0, 1], "--", color="grey", lw=1, label="perfect calibration")
        for rel, lab, col in ((rel0, f"before (T=1, ECE {e0:.3f})", "#c1121f"),
                              (rel1, f"after (T={T:.2f}, ECE {e1:.3f})", "#2a9d8f")):
            xs = [c for c, _, _ in (v for v in rel if v)]
            ys = [o for _, o, _ in (v for v in rel if v)]
            axx.plot(xs, ys, "o-", color=col, label=lab)
        axx.set_xlabel("mean predicted P(caries)"); axx.set_ylabel("observed fraction")
        axx.set_title(f"Caries gate calibration — test (n={len(yt)})")
        axx.legend(fontsize=8); axx.set_xlim(0, 1); axx.set_ylim(0, 1)
        fig.tight_layout()
        args.fig.mkdir(parents=True, exist_ok=True)
        fp = args.fig / "caries_gate_temperature_scaling.png"
        fig.savefig(fp, dpi=160)
        print(f"  figure -> {fp}")
    except Exception as exc:
        print(f"  (figure skipped: {exc})")

    print(f"\n-> {args.out / 'caries_gate_temperature.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
