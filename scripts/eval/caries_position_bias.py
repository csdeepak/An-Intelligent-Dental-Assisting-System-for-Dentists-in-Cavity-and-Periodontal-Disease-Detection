#!/usr/bin/env python
"""
Does the caries gate read the LESION, or does it read WHICH TOOTH it is looking at?

WHY THIS EXISTS
---------------
`PAPER_MATERIAL.md` SS8.22 establishes that an image-blind constant -- "the eight first and
second molars are carious", emitted without reading a pixel -- scores F1 0.320 against this
pipeline's 0.294. SS8.17 separately shows the gate over-calls healthy teeth (19.2%) at the same
rate as impacted ones (19.0%), i.e. it is not confusing pathology-for-pathology.

Neither result says WHY. The obvious mechanism -- that the gate has itself absorbed the same
molar prior the constant encodes -- had never been measured. This script measures it.

WHAT IT MEASURES
----------------
1. **The prior.** Mean P(caries) on teeth that are genuinely HEALTHY, stratified by tooth type,
   against the training-set caries base rate for that type. If the gate reads lesions, this is
   flat near the base rate. If it reads position, it tracks the base rate.
2. **Per-type precision / recall / FP-rate** at the shipped operating point, with support
   counts, so a rate on 8 incisor positives is never read as one on 83 molar positives.
3. **Within-type ranking (AUC).** The decisive number: pooled AUC is inflated by the prior,
   because ranking a molar above an incisor is free. Within a single tooth type that shortcut
   is unavailable, so within-type AUC isolates real lesion signal. 0.5 means none.
4. **A position-only baseline.** AP of a predictor that outputs each tooth type's training base
   rate and never sees the image -- the constant baseline of SS8.22, at crop level.

WHAT IT DOES NOT CLAIM
----------------------
A high within-type AUC does not make the gate clinically useful, and this is a DENTEX-internal
measurement on 863 crops from 34 source images. Confidence intervals are cluster-bootstrapped
over those source images, not over crops, because crops from one radiograph are not independent.

Read-only: loads the frozen `caries-gate-resnet18-v3.0` and writes JSON. No model is modified.

Usage:
    python scripts/eval/caries_position_bias.py
    python scripts/eval/caries_position_bias.py --split val
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DEF_CROPS = REPO_ROOT / "data/dentex/crops_v3_phase1"
DEF_WEIGHTS = REPO_ROOT / "models/09_caries_gate_v3/caries_gate_v3.pth"
DEF_OUT = REPO_ROOT / "outputs/caries_position_bias"

# Tooth type from the FDI position digit. Grouping is anatomical, chosen before looking at any
# result: incisors (1,2), canine (3), premolars (4,5), molars (6,7,8).
TYPES = [(lambda p: p <= 2, "1 incisor"), (lambda p: p == 3, "2 canine"),
         (lambda p: p in (4, 5), "3 premolar"), (lambda p: p >= 6, "4 molar")]


def tooth_type(fdi):
    pos = fdi % 10
    for test, name in TYPES:
        if test(pos):
            return name
    raise ValueError(f"FDI {fdi} has no position digit in 1-8")


def prf(y, pred):
    tp = sum(1 for a, b in zip(y, pred) if a == 1 and b == 1)
    fp = sum(1 for a, b in zip(y, pred) if a == 0 and b == 1)
    fn = sum(1 for a, b in zip(y, pred) if a == 1 and b == 0)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0), tp, fp, fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", type=Path, default=DEF_CROPS)
    ap.add_argument("--weights", type=Path, default=DEF_WEIGHTS)
    ap.add_argument("--split", default="test")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--resamples", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    args = ap.parse_args()

    import numpy as np
    import torch
    from PIL import Image
    from sklearn.metrics import average_precision_score, roc_auc_score
    from torchvision import transforms
    from torchvision.models import resnet18

    bundle = torch.load(args.weights, map_location="cpu", weights_only=False)
    state = bundle["model_state_dict"] if "model_state_dict" in bundle else bundle
    c2i = bundle.get("class_to_idx", {"caries": 0, "no_caries": 1})
    model = resnet18(weights=None)
    model.fc = torch.nn.Linear(512, 2)
    model.load_state_dict(state)
    model.eval()

    tf = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    man = list(csv.DictReader(open(args.crops / "manifest.csv")))
    rows = [r for r in man if r["split"] == args.split]
    if not rows:
        raise SystemExit(f"no crops in split {args.split!r}")

    probs = []
    with torch.no_grad():
        for i in range(0, len(rows), 64):
            batch = rows[i:i + 64]
            ims = [tf(Image.open(args.crops / args.split / r["label"] / r["crop"]).convert("RGB"))
                   for r in batch]
            probs += torch.softmax(model(torch.stack(ims)), 1)[:, c2i["caries"]].tolist()

    probs = np.array(probs)
    y = np.array([1 if r["label"] == "caries" else 0 for r in rows])
    ttype = np.array([tooth_type(int(r["fdi"])) for r in rows])
    img = np.array([r["source_image_md5"] for r in rows])
    pred = (probs >= args.threshold).astype(int)

    n_img = len(set(img))
    print(f"{args.split}: {len(rows)} crops, {int(y.sum())} positive, {n_img} source images")
    P, R, F1, TP, FP, FN = prf(y, pred)
    print(f"overall @ {args.threshold}:  P {P:.4f}  R {R:.4f}  F1 {F1:.4f}   "
          f"TP {TP} FP {FP} FN {FN} TN {len(y) - TP - FP - FN}")

    # training base rate per tooth type -- what a position-only model would learn
    base = defaultdict(lambda: [0, 0])
    for r in man:
        if r["split"] != "train":
            continue
        b = base[tooth_type(int(r["fdi"]))]
        b[1] += 1
        b[0] += r["label"] == "caries"

    print(f"\n{'tooth type':<12} {'n':>5} {'pos':>4} {'prec':>6} {'rec':>6} {'FPrate':>7} "
          f"{'P|healthy':>10} {'trainbase':>10} {'withinAUC':>10}")
    per_type, aucs, weights = {}, [], []
    for t in sorted(set(ttype)):
        m = ttype == t
        yt, pt, prt = y[m], probs[m], pred[m]
        p, r, f1, tp, fp, fn = prf(yt, prt)
        n_neg = int((yt == 0).sum())
        healthy_mean = float(pt[yt == 0].mean()) if n_neg else float("nan")
        br = base[t][0] / base[t][1] if base[t][1] else float("nan")
        auc = float(roc_auc_score(yt, pt)) if 0 < yt.sum() < len(yt) else float("nan")
        if auc == auc:
            aucs.append(auc)
            weights.append(int(m.sum()))
        per_type[t] = {
            "n": int(m.sum()), "n_positive": int(yt.sum()), "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f1, 4), "tp": tp, "fp": fp, "fn": fn,
            "fp_rate_on_negatives": round(fp / n_neg, 4) if n_neg else None,
            "mean_p_caries_on_healthy": round(healthy_mean, 4),
            "train_base_rate": round(br, 4), "within_type_auc": round(auc, 4),
        }
        print(f"{t:<12} {m.sum():>5} {int(yt.sum()):>4} {p:>6.3f} {r:>6.3f} "
              f"{fp / n_neg if n_neg else float('nan'):>7.3f} {healthy_mean:>10.3f} "
              f"{br:>10.3f} {auc:>10.3f}")

    within = float(np.average(aucs, weights=weights))
    pooled = float(roc_auc_score(y, probs))
    pos_only = np.array([base[t][0] / base[t][1] for t in ttype])
    ap_model = float(average_precision_score(y, probs))
    ap_pos = float(average_precision_score(y, pos_only))

    print(f"\nwithin-type AUC (support-weighted) {within:.4f}   <- lesion signal, prior removed")
    print(f"pooled AUC, all types together     {pooled:.4f}   <- inflated by the prior")
    print(f"AP model {ap_model:.4f}   AP position-only {ap_pos:.4f}   AP chance {y.mean():.4f}")

    # Cluster bootstrap over SOURCE IMAGES for the two headline quantities.
    rng = np.random.default_rng(args.seed)
    uimg = np.unique(img)
    idx_by_img = {u: np.where(img == u)[0] for u in uimg}
    bs_within, bs_pooled = [], []
    for _ in range(args.resamples):
        pick = rng.choice(uimg, len(uimg), replace=True)
        idx = np.concatenate([idx_by_img[u] for u in pick])
        yb, pb, tb = y[idx], probs[idx], ttype[idx]
        if 0 < yb.sum() < len(yb):
            bs_pooled.append(roc_auc_score(yb, pb))
        a, w = [], []
        for t in np.unique(tb):
            m = tb == t
            if 0 < yb[m].sum() < m.sum():
                a.append(roc_auc_score(yb[m], pb[m]))
                w.append(int(m.sum()))
        if a:
            bs_within.append(np.average(a, weights=w))
    ci = lambda v: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]
    print(f"  within-type AUC 95% CI {ci(bs_within)}")
    print(f"  pooled     AUC 95% CI {ci(bs_pooled)}")
    print(f"  cluster bootstrap over {n_img} source images, {args.resamples} resamples, "
          f"seed {args.seed}")

    args.out.mkdir(parents=True, exist_ok=True)
    dest = args.out / f"caries_position_bias_{args.split}.json"
    dest.write_text(json.dumps({
        "split": args.split, "n": len(rows), "n_positive": int(y.sum()),
        "n_source_images": n_img, "threshold": args.threshold,
        "weights": str(args.weights), "class_to_idx": c2i,
        "overall": {"precision": round(P, 4), "recall": round(R, 4), "f1": round(F1, 4),
                    "tp": TP, "fp": FP, "fn": FN, "tn": len(y) - TP - FP - FN},
        "per_tooth_type": per_type,
        "within_type_auc": round(within, 4), "within_type_auc_ci95": ci(bs_within),
        "pooled_auc": round(pooled, 4), "pooled_auc_ci95": ci(bs_pooled),
        "average_precision": {"model": round(ap_model, 4),
                              "position_only_baseline": round(ap_pos, 4),
                              "chance": round(float(y.mean()), 4)},
        "ci_method": f"cluster bootstrap over source images (n={n_img}), "
                     f"{args.resamples} resamples, seed {args.seed}",
        "reading": "mean_p_caries_on_healthy tracking train_base_rate is the position prior. "
                   "within_type_auc above 0.5 is lesion signal that survives removing it.",
    }, indent=2) + "\n")
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
