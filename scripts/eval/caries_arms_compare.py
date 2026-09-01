#!/usr/bin/env python
"""
Score the caries signal arms against a same-day control, under the rule fixed in advance.

The acceptance rule, the primary metric and the comparator were all written down BEFORE any arm
was trained, in `outputs/caries_arms/PRE_REGISTRATION.md`. This script only applies them.

  primary metric   average precision on the 863-crop held-out test split
  comparator       a same-day control: v3 config, frozen crops_v3_phase1, this environment
  success          paired delta in AP vs the control with a 95% CI EXCLUDING zero
  interval         paired cluster bootstrap over the 34 source images, 5,000 resamples, seed 42

WHY AVERAGE PRECISION, AND NOT PRECISION OR RECALL
--------------------------------------------------
The v4 experiment (RESULTS_LOG 2026-08-31) is the reason. There, precision rose 3.6 pp and recall
fell 8.7 pp while **AP did not move**: the operating point had slid along an unchanged curve. AP is
threshold-independent and is the only one of the four that answers "did the curve lift". P/R/F1 at
0.50 are reported alongside, never instead.

WHY EACH ARM IS SCORED ON ITS OWN CROPS
---------------------------------------
Arms A and B change the pixels (CLAHE; a 1.25x window), so each model is evaluated on the input
distribution it was trained for. That is only a fair comparison because the crop SETS are
identical -- same crop names, same labels, same FDI, same source images, verified before training
and re-asserted here. Only the pixels differ, so the pairing is item-for-item.

Usage:
    python scripts/eval/caries_arms_compare.py
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# (arm name, crops variant it was trained on). Matches how the runs were launched.
ARMS = [
    ("control", "crops_v3_phase1"),
    ("clahe", "crops_clahe_phase1"),
    ("exp125", "crops_exp125_phase1"),
    ("balance", "crops_v3_phase1"),
]

DEF_ROOT = REPO_ROOT / "outputs/caries_arms"
DEF_CROPS = REPO_ROOT / "data/dentex"


def tooth_type(fdi):
    pos = fdi % 10
    return "incisor" if pos <= 2 else "canine" if pos == 3 else \
           "premolar" if pos in (4, 5) else "molar"


def prf(y, p, t=0.5):
    pd = (p >= t)
    tp = int((pd & (y == 1)).sum()); fp = int((pd & (y == 0)).sum())
    fn = int((~pd & (y == 1)).sum())
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return pr, rc, (2 * pr * rc / (pr + rc) if pr + rc else 0.0), tp, fp, fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEF_ROOT)
    ap.add_argument("--crops-root", type=Path, default=DEF_CROPS)
    ap.add_argument("--split", default="test")
    ap.add_argument("--resamples", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    import numpy as np
    import torch
    from PIL import Image
    from sklearn.metrics import average_precision_score, roc_auc_score
    from torchvision import transforms
    from torchvision.models import resnet18

    tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                             transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    # ---- reference item order, taken from the control's corpus ----
    ref_variant = dict(ARMS)["control"]
    ref = [r for r in csv.DictReader(open(args.crops_root / ref_variant / "manifest.csv"))
           if r["split"] == args.split]
    ref.sort(key=lambda r: r["crop"])
    names = [r["crop"] for r in ref]
    y = np.array([1 if r["label"] == "caries" else 0 for r in ref])
    ttype = np.array([tooth_type(int(r["fdi"])) for r in ref])
    img = np.array([r["source_image_md5"] for r in ref])
    print(f"{args.split}: {len(ref)} crops, {int(y.sum())} positive, {len(set(img))} source images")

    scores, missing = {}, []
    for name, variant in ARMS:
        w = args.root / name / "arm_b" / "phase1_best.pth"
        if not w.exists():
            missing.append(name)
            continue
        # assert the item set matches the reference exactly -- the precondition the whole
        # paired comparison rests on
        m = {r["crop"]: r for r in csv.DictReader(
            open(args.crops_root / variant / "manifest.csv")) if r["split"] == args.split}
        assert set(m) == set(names), f"{name}: crop set differs from control — cannot pair"
        for r in ref:
            assert m[r["crop"]]["label"] == r["label"], f"{name}: label differs on {r['crop']}"

        b = torch.load(w, map_location="cpu", weights_only=False)
        st = b["model_state_dict"] if "model_state_dict" in b else b
        ci = b.get("class_to_idx", {"caries": 0, "no_caries": 1})["caries"]
        model = resnet18(weights=None); model.fc = torch.nn.Linear(512, 2)
        model.load_state_dict(st); model.eval()

        out = []
        with torch.no_grad():
            for i in range(0, len(ref), 64):
                batch = ref[i:i + 64]
                ims = [tf(Image.open(args.crops_root / variant / args.split /
                                     r["label"] / r["crop"]).convert("RGB")) for r in batch]
                out += torch.softmax(model(torch.stack(ims)), 1)[:, ci].tolist()
        scores[name] = np.array(out)

    if missing:
        print(f"\n!! not yet trained, skipped: {', '.join(missing)}")
    if "control" not in scores:
        raise SystemExit("control is required")

    print(f"\n{'arm':<10} {'P':>7} {'R':>7} {'F1':>7} {'AP':>7} {'AUC':>7} {'withinAUC':>10}")
    summary = {}
    for name, _ in ARMS:
        if name not in scores:
            continue
        p = scores[name]
        pr, rc, f1, tp, fp, fn = prf(y, p)
        a, w_ = [], []
        for t in np.unique(ttype):
            mm = ttype == t
            if 0 < y[mm].sum() < mm.sum():
                a.append(roc_auc_score(y[mm], p[mm])); w_.append(int(mm.sum()))
        wauc = float(np.average(a, weights=w_))
        summary[name] = {"precision": round(pr, 4), "recall": round(rc, 4), "f1": round(f1, 4),
                         "average_precision": round(float(average_precision_score(y, p)), 4),
                         "roc_auc": round(float(roc_auc_score(y, p)), 4),
                         "within_type_auc": round(wauc, 4),
                         "tp": tp, "fp": fp, "fn": fn}
        print(f"{name:<10} {pr:>7.4f} {rc:>7.4f} {f1:>7.4f} "
              f"{summary[name]['average_precision']:>7.4f} {summary[name]['roc_auc']:>7.4f} "
              f"{wauc:>10.4f}")

    # ---- paired cluster bootstrap vs the control ----
    rng = np.random.default_rng(args.seed)
    uimg = np.unique(img)
    idx_by = {u: np.where(img == u)[0] for u in uimg}
    draws = []
    for _ in range(args.resamples):
        pick = rng.choice(uimg, len(uimg), replace=True)
        idx = np.concatenate([idx_by[u] for u in pick])
        if 0 < y[idx].sum() < len(idx):
            draws.append(idx)

    print(f"\nPAIRED DELTAS vs control — cluster bootstrap over {len(uimg)} source images, "
          f"{len(draws)} usable resamples, seed {args.seed}")
    print("acceptance rule (pre-registered): AP delta 95% CI must EXCLUDE zero")
    print(f"\n{'arm':<10} {'metric':<20} {'point':>9} {'95% CI':>22}   verdict")
    deltas = {}
    for name, _ in ARMS:
        if name == "control" or name not in scores:
            continue
        deltas[name] = {}
        for metric, fn_ in [("average precision", lambda yy, pp: average_precision_score(yy, pp)),
                            ("F1 @0.5", lambda yy, pp: prf(yy, pp)[2]),
                            ("precision @0.5", lambda yy, pp: prf(yy, pp)[0]),
                            ("recall @0.5", lambda yy, pp: prf(yy, pp)[1])]:
            d = [fn_(y[i], scores[name][i]) - fn_(y[i], scores["control"][i]) for i in draws]
            lo, hi = np.percentile(d, [2.5, 97.5])
            pt = float(np.mean(d))
            sig = lo > 0 or hi < 0
            verdict = ("REAL (excludes 0)" if sig else "not significant")
            if metric == "average precision":
                verdict += "  <- PRIMARY" + ("  ** ARM SUCCEEDS **" if sig else "")
            deltas[name][metric] = {"point": round(pt, 4),
                                    "ci95": [round(float(lo), 4), round(float(hi), 4)],
                                    "significant": bool(sig)}
            print(f"{name:<10} {metric:<20} {pt:>+9.4f}   [{lo:>+7.4f}, {hi:>+7.4f}]   {verdict}")

    args.root.mkdir(parents=True, exist_ok=True)
    dest = args.root / "arms_comparison.json"
    dest.write_text(json.dumps({
        "split": args.split, "n": len(ref), "n_positive": int(y.sum()),
        "n_source_images": int(len(uimg)),
        "primary_metric": "average precision on the 863-crop held-out test split",
        "acceptance_rule": "paired AP delta vs control, 95% CI excluding zero "
                           "(pre-registered in PRE_REGISTRATION.md before any arm was trained)",
        "ci_method": f"paired cluster bootstrap over {len(uimg)} source images, "
                     f"{len(draws)} usable resamples, seed {args.seed}",
        "arms": summary, "deltas_vs_control": deltas,
    }, indent=2) + "\n")
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
