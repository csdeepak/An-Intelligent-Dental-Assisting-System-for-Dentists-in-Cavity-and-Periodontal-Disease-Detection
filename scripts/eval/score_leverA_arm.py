#!/usr/bin/env python
"""Score one Lever A detector arm against the same-day Control A, per the pre-registration.

`outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md` §5:

  PRIMARY   FDI exact end-to-end on the 164 leak-free DENTEX images, method=head, head=models/10.
            Paired cluster bootstrap over images (10k, seed 42). PASS iff the 95% CI excludes
            zero AND its lower bound >= +5 pp.  (Applied to Arm 3C.)
  GUARD 1   Pooled external caries lesion agreement (Ningxia 4 hospitals + CariesXrays), frozen
            caries gate v3.0. Paired bootstrap of Δ (arm - Control A). PASS iff the CI lower
            bound is >= -2 pp.
  GUARD 2   Arm Tufts frozen TEST box mAP@0.5 >= (Control B's Tufts test box mAP@0.5) - 4 pp.
            (Both measured on the GPU box, passed in as --guard2-arm / --guard2-controlB.)
  ADOPT     PRIMARY and GUARD 1 and GUARD 2 all pass. Otherwise ABLATION (bar not moved).

Reuses paired_bootstrap / load_stage2 / load_per_image / ratio from bootstrap_ci.py.

    python scripts/eval/score_leverA_arm.py --label arm3c \
        --arm-stage2   outputs/lever_A_multicorpus_detector_v2/arm3c/stage2_rows_head.json \
        --ctrlA-stage2 outputs/lever_A_multicorpus_detector_v2/controlA/stage2_rows_head.json \
        --arm-caries   outputs/lever_A_multicorpus_detector_v2/arm3c/ningxia_caries.json \
                       outputs/lever_A_multicorpus_detector_v2/arm3c/cariesxrays_caries.json \
        --ctrlA-caries outputs/lever_A_multicorpus_detector_v2/controlA/ningxia_caries.json \
                       outputs/lever_A_multicorpus_detector_v2/controlA/cariesxrays_caries.json \
        --guard2-arm 0.79 --guard2-controlB 0.74
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "eval"))
from bootstrap_ci import load_per_image, load_stage2, paired_bootstrap, ratio  # noqa: E402

PRIMARY_MIN_PP = 5.0      # pre-reg: lower bound >= +5 pp
GUARD1_MIN_PP = -2.0      # pre-reg: lower bound >= -2 pp
GUARD2_DROP_PP = 4.0      # pre-reg: arm >= controlB - 4 pp


def align(a_rows, b_rows, key="image"):
    b = {r[key]: r for r in b_rows}
    a = [r for r in a_rows if r[key] in b]
    return a, [b[r[key]] for r in a]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--arm-stage2", type=Path, required=True)
    ap.add_argument("--ctrlA-stage2", type=Path, required=True)
    ap.add_argument("--arm-caries", type=Path, nargs="+", required=True)
    ap.add_argument("--ctrlA-caries", type=Path, nargs="+", required=True)
    ap.add_argument("--guard2-arm", type=float, required=True,
                    help="this arm's Tufts frozen TEST box mAP@0.5 (from the GPU box)")
    ap.add_argument("--guard2-controlB", type=float, required=True,
                    help="Control B's Tufts frozen TEST box mAP@0.5 (from the GPU box)")
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    out = {"label": args.label, "n_boot": args.n_boot, "seed": args.seed}

    # ---------------------------------------------------------------- PRIMARY
    arm2 = load_stage2(args.arm_stage2)
    ctl2 = load_stage2(args.ctrlA_stage2)
    a, c = align(arm2, ctl2)
    if len(a) != len(arm2) or len(c) != len(ctl2):
        print(f"WARNING: primary alignment kept {len(a)} of arm {len(arm2)} / ctrlA {len(ctl2)}")
    e2e = lambda r: sum(x["exact"] for x in r) / sum(x["gt"] for x in r)  # noqa: E731
    pt, lo, hi, fle0 = paired_bootstrap(c, a, ratio("exact", "gt"), args.n_boot, rng)
    primary_ok = lo * 100 >= PRIMARY_MIN_PP
    out["primary"] = {"n_images": len(a), "gt_teeth": sum(x["gt"] for x in c),
                      "control_e2e": round(e2e(c), 4), "arm_e2e": round(e2e(a), 4),
                      "delta_pp": round(pt * 100, 2), "ci95_pp": [round(lo * 100, 2), round(hi * 100, 2)],
                      "frac_resamples_le_0": round(fle0, 4),
                      "rule": f"lower bound >= +{PRIMARY_MIN_PP} pp", "pass": bool(primary_ok)}
    print(f"\nLEVER A -- arm '{args.label}'   ({len(a)} images, {sum(x['gt'] for x in c)} GT teeth)")
    print(f"  PRIMARY  FDI e2e   control {e2e(c):.4f}  ->  arm {e2e(a):.4f}")
    print(f"           Δ {pt*100:+.2f} pp  [{lo*100:+.2f}, {hi*100:+.2f}]   "
          f"{'PASS' if primary_ok else 'FAIL'} (need lower >= +{PRIMARY_MIN_PP})")

    # ---------------------------------------------------------------- GUARD 1
    def load_caries(paths):
        rows = []
        for p in paths:
            r, _ = load_per_image(p, None)
            rows += r
        return rows
    ac = load_caries(args.arm_caries)
    cc = load_caries(args.ctrlA_caries)
    ac, cc = align(ac, cc)
    agr = lambda r: sum(x["covered"] for x in r) / sum(x["lesions"] for x in r)  # noqa: E731
    pt1, lo1, hi1, fle01 = paired_bootstrap(cc, ac, ratio("covered", "lesions"), args.n_boot, rng)
    guard1_ok = lo1 * 100 >= GUARD1_MIN_PP
    out["guard1"] = {"n_images": len(ac), "n_lesions": sum(x["lesions"] for x in cc),
                     "control_agreement": round(agr(cc), 4), "arm_agreement": round(agr(ac), 4),
                     "delta_pp": round(pt1 * 100, 2), "ci95_pp": [round(lo1 * 100, 2), round(hi1 * 100, 2)],
                     "rule": f"lower bound >= {GUARD1_MIN_PP} pp", "pass": bool(guard1_ok)}
    print(f"  GUARD 1  ext caries agreement   control {agr(cc):.4f}  ->  arm {agr(ac):.4f}  "
          f"({sum(x['lesions'] for x in cc)} lesions)")
    print(f"           Δ {pt1*100:+.2f} pp  [{lo1*100:+.2f}, {hi1*100:+.2f}]   "
          f"{'PASS' if guard1_ok else 'FAIL'} (need lower >= {GUARD1_MIN_PP})")

    # ---------------------------------------------------------------- GUARD 2
    floor = args.guard2_controlB - GUARD2_DROP_PP / 100
    guard2_ok = args.guard2_arm >= floor
    out["guard2"] = {"arm_tufts_test_map50": args.guard2_arm,
                     "controlB_tufts_test_map50": args.guard2_controlB,
                     "floor": round(floor, 4), "rule": f"arm >= controlB - {GUARD2_DROP_PP} pp",
                     "pass": bool(guard2_ok)}
    print(f"  GUARD 2  Tufts test box mAP@0.5   arm {args.guard2_arm:.4f}  vs  "
          f"controlB {args.guard2_controlB:.4f} - {GUARD2_DROP_PP}pp = {floor:.4f}   "
          f"{'PASS' if guard2_ok else 'FAIL'}")

    # ---------------------------------------------------------------- VERDICT
    if primary_ok and guard1_ok and guard2_ok:
        verdict = "ADOPT -- primary and both guards pass"
    elif primary_ok:
        failed = [g for g, ok in (("Guard 1", guard1_ok), ("Guard 2", guard2_ok)) if not ok]
        verdict = f"ABLATION -- primary passes but {', '.join(failed)} FAILED (bar not moved)"
    else:
        verdict = "NULL -- primary CI lower bound below +5 pp; reported as a result, bar not moved"
    out["verdict"] = verdict
    print(f"\n  VERDICT: {verdict}\n")

    dst = args.out or (REPO / "outputs/lever_A_multicorpus_detector_v2" / f"{args.label}_scored.json")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=2) + "\n")
    print(f"  wrote {dst}")


if __name__ == "__main__":
    main()
