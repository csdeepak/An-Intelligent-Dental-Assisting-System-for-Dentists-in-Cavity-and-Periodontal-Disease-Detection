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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--disease-dir", type=Path,
                    default=Path.home() / "Downloads/Capstone/DENTEX/disease")
    args = ap.parse_args()

    from c1_vlm_baseline import load_gt
    gt = load_gt(args.disease_dir)

    vlm = json.loads((args.out / "arm_vlm.json").read_text())
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

    vr = score_sets(gt, vpred)
    print(f"\n  {'Qwen2.5-VL-7B (actual)':40s} P {vr['precision']:.3f}  "
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
    (args.out / "c1_constant_baseline.json").write_text(json.dumps(res, indent=2) + "\n")
    print(f"\n-> {args.out / 'c1_constant_baseline.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
