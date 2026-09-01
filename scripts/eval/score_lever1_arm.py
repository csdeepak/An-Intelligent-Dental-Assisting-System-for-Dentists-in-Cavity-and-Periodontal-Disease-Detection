#!/usr/bin/env python
"""Score one Lever-1 detector arm against the same-day control, per the pre-registration.

`outputs/detector_multicorpus/PRE_REGISTRATION.md`:
  PRIMARY   FDI exact end-to-end on the 164 leak-free DENTEX images; paired cluster bootstrap
            over images (10,000 resamples, seed 42); SUCCEEDS iff the 95% CI excludes zero.
  GUARD     Tufts frozen test box mAP@0.5 >= 0.75  (measured separately on the GPU box, passed in).
  ADOPT     primary significant AND guard met. Primary-only -> reported as an ablation.

Reuses `paired_bootstrap` / `load_stage2` from bootstrap_ci.py -- no reimplementation.

    python scripts/eval/score_lever1_arm.py \
        --arm-rows   outputs/detector_multicorpus/multicorpus/stage2_rows_head.json \
        --guard-map50 0.81 --label multicorpus
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "eval"))
from bootstrap_ci import load_stage2, paired_bootstrap, ratio  # noqa: E402

DEF_CTRL = REPO / "outputs/detector_multicorpus/control_sameday/stage2_rows_head.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm-rows", type=Path, required=True)
    ap.add_argument("--control-rows", type=Path, default=DEF_CTRL)
    ap.add_argument("--label", required=True)
    ap.add_argument("--guard-map50", type=float, required=True,
                    help="Tufts frozen test box mAP@0.5 for this arm, from `yolo val ... split=test`")
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    ctrl = {c["image"]: c for c in load_stage2(args.control_rows)}
    arm_all = load_stage2(args.arm_rows)
    # align by image, same order for both -- the paired design needs identical clusters
    arm = [c for c in arm_all if c["image"] in ctrl]
    con = [ctrl[c["image"]] for c in arm]
    assert len(arm) == len(con) and arm, f"alignment failed: {len(arm)} arm vs {len(con)} control"
    if len(arm) != len(arm_all):
        print(f"WARNING: {len(arm_all) - len(arm)} arm images not in control -- dropped from pairing")

    rng = np.random.default_rng(args.seed)
    tot = lambda rows, k: sum(r[k] for r in rows)  # noqa: E731
    e2e = lambda rows: tot(rows, "exact") / tot(rows, "gt")  # noqa: E731
    rec = lambda rows: tot(rows, "detected") / tot(rows, "gt")  # noqa: E731
    ofd = lambda rows: tot(rows, "exact_of_det") / tot(rows, "detected")  # noqa: E731

    out = {"label": args.label, "n_images": len(arm),
           "n_gt_teeth": tot(con, "gt"), "n_boot": args.n_boot, "seed": args.seed,
           "control": {"e2e": round(e2e(con), 4), "recall": round(rec(con), 4),
                       "of_detected": round(ofd(con), 4)},
           "arm": {"e2e": round(e2e(arm), 4), "recall": round(rec(arm), 4),
                   "of_detected": round(ofd(arm), 4)},
           "deltas": {}, "guard_map50": args.guard_map50}

    print(f"\nLEVER 1 -- arm '{args.label}' vs same-day control   ({len(arm)} images, "
          f"{tot(con, 'gt')} GT teeth)")
    print(f"  {'':22s} {'control':>10s} {'arm':>10s}")
    for name, fn in (("FDI exact end-to-end", e2e), ("detection recall", rec),
                     ("FDI exact of detected", ofd)):
        print(f"  {name:22s} {fn(con):>10.4f} {fn(arm):>10.4f}")

    print("\n  paired cluster bootstrap over images (arm - control):")
    for name, num, den in (("e2e", "exact", "gt"), ("recall", "detected", "gt"),
                           ("of_detected", "exact_of_det", "detected")):
        point, lo, hi, frac_le0 = paired_bootstrap(con, arm, ratio(num, den), args.n_boot, rng)
        sig = "excludes 0" if (lo > 0 or hi < 0) else "INCLUDES 0"
        out["deltas"][name] = {"point_pp": round(point * 100, 2),
                               "ci95_pp": [round(lo * 100, 2), round(hi * 100, 2)],
                               "frac_resamples_le_0": round(frac_le0, 4), "verdict": sig}
        print(f"    Δ {name:14s} {point*100:+6.2f} pp  [{lo*100:+6.2f}, {hi*100:+6.2f}]  {sig}")

    primary_ok = out["deltas"]["e2e"]["verdict"] == "excludes 0" and out["deltas"]["e2e"]["point_pp"] > 0
    guard_ok = args.guard_map50 >= 0.75
    if primary_ok and guard_ok:
        verdict = "ADOPT -- primary CI excludes zero (positive) AND guard met"
    elif primary_ok and not guard_ok:
        verdict = f"ABLATION -- primary significant but guard FAILED (mAP@0.5 {args.guard_map50} < 0.75)"
    else:
        verdict = "NULL -- primary CI includes zero; reported as a result, bar not moved"
    out["verdict"] = verdict
    print(f"\n  GUARD  Tufts test box mAP@0.5 = {args.guard_map50}  ({'PASS' if guard_ok else 'FAIL'} >= 0.75)")
    print(f"  VERDICT: {verdict}\n")

    dst = args.out or (REPO / "outputs/detector_multicorpus" / f"{args.label}_scored.json")
    dst.write_text(json.dumps(out, indent=2) + "\n")
    print(f"  wrote {dst}")


if __name__ == "__main__":
    main()
