#!/usr/bin/env python
"""
Is the VLM's C1 score explainable by a CONSTANT guess? (It is.)

WHY THIS EXISTS
---------------
The C1 smoke test returned near-identical answers across different radiographs, so a control was
run on the GPU box: the same prompt against a real radiograph, a **blank grey image**, and a
**random-noise image**. The blank and the noise both produced `26,36` -- a confident,
dental-specific answer identical to one produced for a real radiograph. A grey rectangle contains
no teeth.

That means the reported VLM F1 may not measure dental reading ability at all. This script settles
it the only way that is fair to the model: by asking whether a **fixed answer, ignoring the image
entirely**, scores as well. If it does, the VLM's number is a property of the prior, not of
perception, and the paper must say so rather than presenting it as a like-for-like model result.

Everything here is CPU and reads the already-downloaded predictions; no GPU, no re-run.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

DEF_OUT = REPO_ROOT / "outputs" / "c1_vlm"


def score_sets(gt, pred):
    tp = fp = fn = exact = 0
    for stem, g in gt.items():
        p = set(pred.get(stem, set()))
        tp += len(g & p); fp += len(p - g); fn += len(g - p)
        exact += int(g == p)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4),
            "exact_rate": round(exact / len(gt), 4), "tp": tp, "fp": fp, "fn": fn}


def best_constant(gt, max_size=12):
    """The STRONGEST possible image-blind answer, found greedily on the evaluation set itself.

    The hand-picked constants below ({26,36} and friends) answer "is this model's score
    explainable by a prior?". This answers the harder version: "could ANY fixed answer have done
    this well?" It is deliberately fitted on the same data it is scored on, which makes it an
    optimistic upper bound on image-blind performance -- that is the point. A model that beats it
    is provably using the image for something; a model that loses to it has not demonstrated it
    is, however plausible its outputs look.

    Label it as an oracle wherever it appears. It is not a baseline anyone could deploy.
    """
    chosen, best_f1 = set(), 0.0
    pool = {c for v in gt.values() for c in v}
    for _ in range(max_size):
        cand = max((c for c in pool - chosen),
                   key=lambda c: score_sets(gt, {k: chosen | {c} for k in gt})["f1"],
                   default=None)
        if cand is None:
            break
        f1 = score_sets(gt, {k: chosen | {cand} for k in gt})["f1"]
        if f1 <= best_f1:
            break
        chosen, best_f1 = chosen | {cand}, f1
    return chosen, best_f1


def heldout_constant(disease_dir, gt):
    """The constant a person could ACTUALLY deploy: fitted on held-out images, scored on the test set.

    `best_constant` is fitted on the evaluation set, so it is an oracle and cannot be claimed as a
    baseline anyone could build. This version fits the same greedy search on the 86
    leakage-excluded images -- disjoint from the 164 scored ones -- and then applies the frozen
    answer to the test set. Nothing is tuned on the data it is scored on.

    This is the number that actually matters. If a six-stage pipeline cannot beat a fixed list of
    tooth codes chosen without ever seeing a radiograph, that is a finding about the task, and it
    belongs in the paper whether or not it flatters the system.
    """
    from c1_vlm_baseline import load_exemplars
    pool = load_exemplars(disease_dir, 10_000)          # every excluded image, with its codes
    fit_gt = {stem: set(codes) for stem, codes in pool}
    assert not (set(fit_gt) & set(gt)), "held-out fit set overlaps the scored set"
    const, fit_f1 = best_constant(fit_gt)
    return const, fit_f1, len(fit_gt), score_sets(gt, {k: const for k in gt})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--disease-dir", type=Path,
                    default=Path.home() / "Downloads/Capstone/DENTEX/disease")
    ap.add_argument("--arm-file", default="arm_vlm.json",
                    help="which VLM arm to characterise (several now exist)")
    args = ap.parse_args()

    from c1_vlm_baseline import load_gt
    gt = load_gt(args.disease_dir)

    vlm = json.loads((args.out / args.arm_file).read_text())
    vpred = {k: set(v) for k, v in vlm["predictions"].items()}
    gt = {k: v for k, v in gt.items() if k in vpred}

    # 1. How much variety is there in the model's output at all?
    sig = Counter(tuple(sorted(v)) for v in vpred.values())
    print(f"VLM output diversity over {len(vpred)} images:")
    print(f"  distinct answers: {len(sig)}")
    for ans, n in sig.most_common(6):
        print(f"    {n:4d}x  {list(ans)}")
    top_share = sig.most_common(1)[0][1] / len(vpred)
    print(f"  most common answer covers {top_share:.1%} of all images")

    # 2. Constant baselines that never look at the image.
    print("\nCONSTANT BASELINES (image ignored entirely):")
    rows = []
    consts = {
        "{26,36} (what a BLANK image produced)": {"26", "36"},
        "{26,37}": {"26", "37"},
        "{26}": {"26"},
        "VLM's own most common answer": set(sig.most_common(1)[0][0]),
        "empty set (predict nothing)": set(),
    }
    for name, c in consts.items():
        r = score_sets(gt, {k: c for k in gt})
        rows.append({"baseline": name, **r})
        print(f"  {name:40s} P {r['precision']:.3f}  R {r['recall']:.3f}  F1 {r['f1']:.3f}")

    bc_set, bc_f1 = best_constant(gt)
    rows.append({"baseline": f"ORACLE best constant {sorted(bc_set)}", "oracle": True,
                 **score_sets(gt, {k: bc_set for k in gt})})
    print(f"  {'ORACLE best constant (fitted on TEST)':40s} "
          f"F1 {bc_f1:.3f}   {sorted(bc_set)}")

    ho_set, ho_fit, ho_n, ho_r = heldout_constant(args.disease_dir, gt)
    rows.append({"baseline": f"held-out constant {sorted(ho_set)} (fitted on {ho_n} excluded images)",
                 "oracle": False, **ho_r})
    print(f"  {'HELD-OUT constant (deployable)':40s} P {ho_r['precision']:.3f}  "
          f"R {ho_r['recall']:.3f}  F1 {ho_r['f1']:.3f}   {sorted(ho_set)}")

    vr = score_sets(gt, vpred)
    print(f"\n  {vlm.get('model', 'VLM') + ' (actual)':40s} P {vr['precision']:.3f}  "
          f"R {vr['recall']:.3f}  F1 {vr['f1']:.3f}")

    best_const = max(rows, key=lambda r: r["f1"])
    print()
    if vr["f1"] <= best_const["f1"] + 1e-9:
        print(f"  VERDICT: the VLM does NOT beat a constant guess "
              f"({best_const['baseline']}, F1 {best_const['f1']:.3f}).")
        print("           Its score is a property of the prior, not of reading the radiograph.")
    else:
        print(f"  VERDICT: the VLM beats the best constant guess by "
              f"{vr['f1'] - best_const['f1']:+.3f} F1 -- it extracts SOME image information.")

    res = {"n_images": len(gt), "vlm": vr, "vlm_distinct_answers": len(sig),
           "vlm_top_answer_share": round(top_share, 4),
           "constant_baselines": rows,
           "control": "on the GPU box, a blank grey image and a random-noise image both produced "
                      "'26,36' -- the same confident dental answer as a real radiograph",
           "reading": "a VLM score at or below a constant guess is not evidence of dental "
                      "perception and must not be reported as a like-for-like model comparison"}
    (args.out / f"c1_constant_{args.arm_file}").write_text(json.dumps(res, indent=2) + "\n")
    print(f"\n-> {args.out / 'c1_constant_baseline.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
