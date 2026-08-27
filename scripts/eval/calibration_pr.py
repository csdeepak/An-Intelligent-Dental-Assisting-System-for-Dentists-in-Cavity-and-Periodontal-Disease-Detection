#!/usr/bin/env python
"""
Calibration and precision-recall analysis for the frozen caries gate.

WHY THE CARIES GATE, WHEN §9's CHECKLIST ASKS FOR BONE LOSS
------------------------------------------------------------
Both need per-item probabilities against labels, and neither was ever saved. The difference is
how safely each can be reconstructed:

* **Caries** rebuilds exactly. `build_caries_phase1_v3.py` is the committed script that produced
  the shipped gate's own training data, and re-running it reproduces the documented composition
  to the crop (98.28% MD5-join agreement, train 723/4,027, test 863, 5,366 healthy). The crops
  under test here are the same crops the model was evaluated on.
* **Bone loss does not.** Its metadata CSVs carry `filename,label,stem` and **no bounding boxes**,
  so the 1.5x/2.0x crops would have to be reconstructed by hand from tooth ids against
  `teeth_bbox.json`. A silent crop-geometry mismatch is precisely what voided the R1 run
  (RESULTS_LOG 2026-08-27a), and a mismatch here would corrupt the calibration curve while
  looking perfectly plausible. Bone-loss calibration therefore needs a geometry-verified
  rebuild first and is deliberately not attempted here.

The caries gate is also the branch that most needs this: `run_inference.py` stamps every tooth
with a `caries_uncalibrated` flag, and the gate's 0.40 precision is a headline weakness. This
script replaces the flag's assertion with a measurement.

WHAT IS REPORTED
----------------
* **Reliability diagram + ECE / MCE / Brier** -- is a predicted 0.8 actually right 80% of the time?
* **Precision-recall curve + average precision** -- PR, not ROC: the test split is 14.7% positive,
  and ROC-AUC flatters a classifier on imbalanced data by rewarding true negatives it gets for
  free.
* **A threshold sweep**, so the operating point is a choice with visible consequences rather than
  an inherited `argmax`. The pipeline currently uses argmax, i.e. threshold 0.5.
* **A cluster-bootstrap CI on average precision**, resampling by SOURCE IMAGE (`source_image_md5`)
  rather than by crop -- teeth from one radiograph are not independent, same argument as
  `bootstrap_ci.py`.

Usage:
    python scripts/eval/calibration_pr.py
    python scripts/eval/calibration_pr.py --split val --n-boot 5000
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", type=Path, default=DEF_CROPS)
    ap.add_argument("--weights", type=Path, default=DEF_WEIGHTS)
    ap.add_argument("--split", default="test")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--bins", type=int, default=10)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--fig", type=Path, default=DEF_FIG)
    args = ap.parse_args()

    import cv2
    import numpy as np
    import pandas as pd
    import torch
    from torchvision import transforms

    from src.classifiers import IMAGENET_MEAN, IMAGENET_STD, load_classifier

    man = pd.read_csv(args.crops / "manifest.csv")
    man = man[man["split"] == args.split].reset_index(drop=True)
    if man.empty:
        raise SystemExit(f"no rows for split={args.split}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, cls = load_classifier(args.weights, 2, device)
    # Class order comes from the checkpoint, never assumed. verify_invariants pins it.
    if cls and cls != {"caries": 0, "no_caries": 1}:
        raise SystemExit(f"unexpected gate class order: {cls}")
    pos_idx = (cls or {"caries": 0})["caries"]
    print(f"device={device}  split={args.split}  n={len(man)}  positive class index={pos_idx}")

    tf = transforms.Compose([transforms.ToTensor(),
                             transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])

    probs, labels, groups = [], [], []
    batch = []
    for i, r in man.iterrows():
        # Same preprocessing as src.classifiers.crop_batch: cv2 read (BGR), resize 224,
        # BGR->RGB, ToTensor, ImageNet normalise. A different transform here would measure
        # the calibration of a model that never ran.
        img = cv2.imread(str(args.crops / args.split / r["label"] / r["crop"]), cv2.IMREAD_COLOR)
        if img is None:
            img = cv2.imread(str(args.crops / r["crop"]), cv2.IMREAD_COLOR)
        if img is None:
            raise SystemExit(f"cannot read crop: {r['crop']}")
        img = cv2.resize(img, (224, 224), interpolation=cv2.INTER_LINEAR)
        batch.append(tf(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
        labels.append(1 if r["label"] == "caries" else 0)
        groups.append(r["source_image_md5"])
        if len(batch) == args.batch_size or i == len(man) - 1:
            with torch.no_grad():
                p = torch.softmax(model(torch.stack(batch).to(device)), dim=1).cpu().numpy()
            probs.extend(p[:, pos_idx].tolist())
            batch = []
            if (i + 1) % 256 < args.batch_size:
                print(f"  {i+1}/{len(man)}", flush=True)

    p = np.array(probs)
    y = np.array(labels)
    g = np.array(groups)
    print(f"  scored {len(p)} crops, {y.sum()} positive ({y.mean():.1%} prevalence)")

    # ---------------------------------------------------------------- calibration
    bins = np.linspace(0.0, 1.0, args.bins + 1)
    idx = np.clip(np.digitize(p, bins) - 1, 0, args.bins - 1)
    rel = []
    ece = mce = 0.0
    for b in range(args.bins):
        m = idx == b
        if not m.any():
            rel.append({"bin": [round(float(bins[b]), 2), round(float(bins[b + 1]), 2)],
                        "n": 0, "mean_pred": None, "observed": None})
            continue
        conf, obs, n = float(p[m].mean()), float(y[m].mean()), int(m.sum())
        gap = abs(conf - obs)
        ece += n / len(p) * gap
        mce = max(mce, gap)
        rel.append({"bin": [round(float(bins[b]), 2), round(float(bins[b + 1]), 2)],
                    "n": n, "mean_pred": round(conf, 4), "observed": round(obs, 4),
                    "gap": round(conf - obs, 4)})
    brier = float(np.mean((p - y) ** 2))

    # ---------------------------------------------------------------- PR + sweep
    from sklearn.metrics import average_precision_score, precision_recall_curve
    ap_score = float(average_precision_score(y, p))
    pr, rc, th = precision_recall_curve(y, p)

    sweep = []
    for t in np.round(np.arange(0.05, 1.00, 0.05), 2):
        pred = p >= t
        tp = int((pred & (y == 1)).sum()); fp = int((pred & (y == 0)).sum())
        fn = int((~pred & (y == 1)).sum())
        prec = tp / (tp + fp) if tp + fp else None
        recl = tp / (tp + fn) if tp + fn else None
        f1 = (2 * prec * recl / (prec + recl)) if prec and recl else None
        sweep.append({"threshold": float(t), "n_flagged": int(pred.sum()),
                      "precision": round(prec, 4) if prec is not None else None,
                      "recall": round(recl, 4) if recl is not None else None,
                      "f1": round(f1, 4) if f1 is not None else None})

    # ---------------------------------------------------------------- cluster bootstrap on AP
    rng = np.random.default_rng(args.seed)
    uniq = np.unique(g)
    draws = []
    for _ in range(args.n_boot):
        pick = rng.choice(uniq, len(uniq), replace=True)
        sel = np.concatenate([np.flatnonzero(g == u) for u in pick])
        if len(np.unique(y[sel])) < 2:
            continue
        draws.append(average_precision_score(y[sel], p[sel]))
    lo, hi = (float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))) if draws else (None, None)

    res = {"split": args.split, "n": int(len(p)), "n_positive": int(y.sum()),
           "prevalence": round(float(y.mean()), 4),
           "weights": str(args.weights), "class_to_idx": cls,
           "average_precision": round(ap_score, 4),
           "average_precision_ci95": [round(lo, 4), round(hi, 4)] if lo else None,
           "ci_method": "cluster bootstrap over source images (n=%d), %d resamples, seed %d"
                        % (len(uniq), args.n_boot, args.seed),
           "brier": round(brier, 4), "ece": round(ece, 4), "mce": round(mce, 4),
           "reliability": rel, "threshold_sweep": sweep,
           "operating_point": "argmax == threshold 0.50 (what run_inference.py uses)"}

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"caries_gate_calibration_{args.split}.json").write_text(
        json.dumps(res, indent=2) + "\n")

    # ---------------------------------------------------------------- figure
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
        cx = [r["mean_pred"] for r in rel if r["n"]]
        cy = [r["observed"] for r in rel if r["n"]]
        ax[0].plot([0, 1], [0, 1], "--", color="grey", lw=1, label="perfect calibration")
        ax[0].plot(cx, cy, "o-", color="#c1121f", label="caries gate v3")
        ax[0].set_xlabel("mean predicted P(caries)"); ax[0].set_ylabel("observed fraction")
        ax[0].set_title(f"Reliability — {args.split} (n={len(p)})\nECE {ece:.3f} · Brier {brier:.3f}")
        ax[0].legend(fontsize=8); ax[0].set_xlim(0, 1); ax[0].set_ylim(0, 1)
        ax[1].plot(rc, pr, color="#003049")
        ax[1].axhline(float(y.mean()), ls="--", color="grey", lw=1,
                      label=f"chance = prevalence {y.mean():.3f}")
        ax[1].set_xlabel("recall"); ax[1].set_ylabel("precision")
        ax[1].set_title(f"Precision–Recall — AP {ap_score:.3f}"
                        + (f" [{lo:.3f}, {hi:.3f}]" if lo else ""))
        ax[1].legend(fontsize=8); ax[1].set_xlim(0, 1); ax[1].set_ylim(0, 1)
        fig.tight_layout()
        args.fig.mkdir(parents=True, exist_ok=True)
        fp = args.fig / f"caries_gate_calibration_{args.split}.png"
        fig.savefig(fp, dpi=160)
        print(f"  figure -> {fp}")
    except Exception as exc:
        print(f"  (figure skipped: {exc})")

    print(f"\n  average precision {ap_score:.4f}"
          + (f"  95% CI [{lo:.4f}, {hi:.4f}]" if lo else ""))
    print(f"  ECE {ece:.4f}   MCE {mce:.4f}   Brier {brier:.4f}")
    print("\n  threshold sweep (precision / recall / F1):")
    for r in sweep:
        if r["precision"] is not None:
            print(f"    t={r['threshold']:.2f}  flagged {r['n_flagged']:4d}  "
                  f"P {r['precision']:.3f}  R {r['recall']:.3f}  F1 {r['f1']:.3f}")
    print(f"\n-> {args.out / f'caries_gate_calibration_{args.split}.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
