#!/usr/bin/env python
"""
Caries failure panel: WHICH teeth the gate gets wrong, bucketed by the confounder that explains it.

WHY THE SUBTYPE BUCKET IS THE POINT
------------------------------------
`caries-gate-resnet18-v3.0`'s negative class is not one thing. `crops_v3_phase1` records a
`subtype` per crop, and the negatives are **5,366 healthy + 179 impacted + 22 periapical**. The
gate's known weakness is precision 0.40, and the standing question this repo has never answered
is *which* negatives it trips on: ordinary healthy teeth, or the other pathology it was never
trained to distinguish from caries.

Those imply different fixes. If false positives concentrate on impacted/periapical teeth, the
gate is confusing pathology-for-pathology and the negative class needs a third label. If they are
spread evenly over healthy teeth, it is simply an over-sensitive detector of surface texture.
`MASTER_PLAN_2026H2.md` W7 asks for a taxonomy "bucketed by confounder"; `subtype` is the
confounder that was recorded and never used.

WHAT THIS PRODUCES
------------------
* FP / FN rates **per subtype**, with support counts, so a rate on 22 periapical crops is never
  read as if it were a rate on 5,366 healthy ones.
* A visual panel of the highest-confidence false positives and the lowest-confidence false
  negatives -- the cases a reader should look at to judge whether the model is being stupid or
  the label is ambiguous.
* Both raw and isotonic-calibrated confidence on every example, since 2026-08-27s showed the raw
  numbers are systematically overconfident and a panel captioned with raw scores would overstate
  how sure the model was.

Evaluated on the **held-out test split (863 crops, 127 positive)** at the pipeline's operating
point (argmax == 0.50).

Usage:
    python scripts/eval/caries_failure_panel.py
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DEF_CROPS = REPO_ROOT / "data/dentex/crops_v3_phase1"
DEF_WEIGHTS = REPO_ROOT / "models/09_caries_gate_v3/caries_gate_v3.pth"
DEF_OUT = REPO_ROOT / "outputs/caries_failure_panel"
DEF_FIG = REPO_ROOT / "docs/results/figures/paper"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", type=Path, default=DEF_CROPS)
    ap.add_argument("--weights", type=Path, default=DEF_WEIGHTS)
    ap.add_argument("--split", default="test")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--n-show", type=int, default=8)
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
    device = torch.device("cpu")
    model, cls = load_classifier(args.weights, 2, device)
    if cls and cls != {"caries": 0, "no_caries": 1}:
        raise SystemExit(f"unexpected class order: {cls}")
    pos_idx = (cls or {"caries": 0})["caries"]

    tf = transforms.Compose([transforms.ToTensor(),
                             transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
    probs, batch, paths = [], [], []
    for i, r in man.iterrows():
        fp = args.crops / args.split / r["label"] / r["crop"]
        img = cv2.imread(str(fp), cv2.IMREAD_COLOR)
        if img is None:
            raise SystemExit(f"cannot read {fp}")
        paths.append(fp)
        batch.append(tf(cv2.cvtColor(cv2.resize(img, (224, 224)), cv2.COLOR_BGR2RGB)))
        if len(batch) == 64 or i == len(man) - 1:
            with torch.no_grad():
                p = torch.softmax(model(torch.stack(batch).to(device)), 1).cpu().numpy()
            probs.extend(p[:, pos_idx].tolist())
            batch = []

    man = man.assign(p_caries=probs, path=[str(x) for x in paths])
    man["y"] = (man["label"] == "caries").astype(int)
    man["pred"] = (man["p_caries"] >= args.threshold).astype(int)

    # calibrated confidence for the captions -- raw scores overstate certainty (27s)
    knots = None
    kp = REPO_ROOT / "models/09_caries_gate_v3/isotonic_calibrator.json"
    if kp.exists():
        d = json.loads(kp.read_text(encoding="utf-8"))
        knots = (np.asarray(d["x"], float), np.asarray(d["y"], float))
        man["p_cal"] = np.interp(man["p_caries"], knots[0], knots[1])
    else:
        man["p_cal"] = np.nan

    tp = man[(man.y == 1) & (man.pred == 1)]
    fp_ = man[(man.y == 0) & (man.pred == 1)]
    fn = man[(man.y == 1) & (man.pred == 0)]
    tn = man[(man.y == 0) & (man.pred == 0)]
    print(f"CARIES FAILURE PANEL — {args.split} split, n={len(man)}, threshold {args.threshold}")
    print(f"  TP {len(tp)}   FP {len(fp_)}   FN {len(fn)}   TN {len(tn)}")
    print(f"  precision {len(tp)/max(len(tp)+len(fp_),1):.3f}   "
          f"recall {len(tp)/max(len(tp)+len(fn),1):.3f}")

    print("\n  FALSE POSITIVES BY SUBTYPE — the confounder question:")
    print(f"    {'subtype':14s} {'n neg':>7s} {'FP':>5s} {'FP rate':>9s}")
    rows = []
    for st, grp in man[man.y == 0].groupby("subtype"):
        f = int((grp.pred == 1).sum())
        rows.append({"subtype": st, "n_negative": int(len(grp)), "false_positives": f,
                     "fp_rate": round(f / len(grp), 4)})
        print(f"    {st:14s} {len(grp):7d} {f:5d} {f/len(grp):9.1%}")
    print("    (read the support column: a rate on tens of crops is not a rate on thousands)")

    print("\n  FALSE NEGATIVES BY SUBTYPE:")
    for st, grp in man[man.y == 1].groupby("subtype"):
        f = int((grp.pred == 0).sum())
        print(f"    {st:14s} {len(grp):7d} {f:5d} {f/len(grp):9.1%}")

    res = {"split": args.split, "n": int(len(man)), "threshold": args.threshold,
           "tp": len(tp), "fp": len(fp_), "fn": len(fn), "tn": len(tn),
           "fp_by_subtype": rows,
           "worst_false_positives": fp_.nlargest(args.n_show, "p_caries")[
               ["crop", "subtype", "fdi", "p_caries", "p_cal"]].to_dict("records"),
           "worst_false_negatives": fn.nsmallest(args.n_show, "p_caries")[
               ["crop", "subtype", "fdi", "p_caries", "p_cal"]].to_dict("records")}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"caries_failure_{args.split}.json").write_text(json.dumps(res, indent=2) + "\n")

    # ---------------------------------------------------------------- panel
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        show_fp = fp_.nlargest(args.n_show, "p_caries")
        show_fn = fn.nsmallest(args.n_show, "p_caries")
        k = max(len(show_fp), len(show_fn))
        fig, axes = plt.subplots(2, k, figsize=(1.7 * k, 4.4))
        if k == 1:
            axes = axes.reshape(2, 1)
        for row, (grp, title) in enumerate(((show_fp, "FALSE POSITIVE"), (show_fn, "FALSE NEGATIVE"))):
            for c in range(k):
                ax = axes[row, c]
                ax.axis("off")
                if c >= len(grp):
                    continue
                r = grp.iloc[c]
                im = cv2.cvtColor(cv2.imread(r["path"]), cv2.COLOR_BGR2RGB)
                ax.imshow(im)
                cal = "" if np.isnan(r["p_cal"]) else f"\ncal {r['p_cal']:.2f}"
                ax.set_title(f"{r['subtype']}\nraw {r['p_caries']:.2f}{cal}", fontsize=7)
                for sp in ax.spines.values():
                    sp.set_visible(False)
            axes[row, 0].set_ylabel(title)
        fig.suptitle(f"Caries gate failures — {args.split} (threshold {args.threshold}). "
                     f"Top: highest-confidence false positives. Bottom: most-missed false negatives.",
                     fontsize=9)
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        args.fig.mkdir(parents=True, exist_ok=True)
        out_fig = args.fig / f"caries_failure_panel_{args.split}.png"
        fig.savefig(out_fig, dpi=160)
        print(f"\n  panel -> {out_fig}")
    except Exception as exc:
        print(f"  (panel skipped: {exc})")

    print(f"-> {args.out / f'caries_failure_{args.split}.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
