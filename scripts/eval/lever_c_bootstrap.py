#!/usr/bin/env python
"""Lever C acceptance-rule numbers: paired cluster bootstrap, structural arms vs the Hungarian.

Pre-registration: `outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md` §4 (evaluation)
and §5 (acceptance rule) -- both frozen 6 Sep 2026, commit `e9270a3`, before any Lever C code
existed. This script only *applies* that rule; it does not decide anything.

    PRIMARY     Tufts FDI-exact-of-detected, delta (arm - hungarian), 95% CI lower bound >= +2.0 pp
    GUARD       DENTEX FDI-exact-of-detected AND end-to-end, lower bound >= -1.0 pp on both
    STRATIFIED  Tufts anterior (position 1-3) delta, point estimate >= -2.0 pp

Reuses `paired_bootstrap` / `ratio` from `bootstrap_ci.py` rather than reimplementing: the same
10,000-resample, seed-42, resample-IMAGES-not-teeth cluster bootstrap every other paired delta in
this project uses. Teeth inside one radiograph are not independent, and a mis-numbered quadrant
mis-numbers several at once -- bootstrapping over teeth would report intervals that are far too
narrow.

The arms are paired by construction, not by alignment after the fact: every arm was scored in one
pass off the SAME detector boxes and the SAME head forward pass
(`validate_fdi_assignment{,_tufts}.py --assignment a,b,c`), so per-image payloads line up
image-for-image and the difference isolates the assignment.

Usage:
    python scripts/eval/lever_c_bootstrap.py
    python scripts/eval/lever_c_bootstrap.py --n-boot 20000 --seed 7      # robustness only
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
from bootstrap_ci import paired_bootstrap, ratio  # noqa: E402

LC = REPO_ROOT / "outputs/lever_C_fdi_structural_postproc"
ARMS = ("structural-sort", "structural-dp")

# The frozen bars, in percentage points. Named here so a reader can check them against §5
# without leaving the file -- and so changing one is a visible diff, not a quiet edit.
PRIMARY_MIN_LB = 2.0
GUARD_MIN_LB = -1.0
ANTERIOR_MIN_POINT = -2.0


def rows_path(cohort_dir, method, arm):
    suffix = "" if arm == "hungarian" else f"__{arm}"
    return cohort_dir / f"stage2_rows_{method}{suffix}.json"


def payloads(path, subset=None):
    """Per-tooth rows -> per-image count payloads, in a stable image order."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    by_img = defaultdict(lambda: {"gt": 0, "det": 0, "exact": 0})
    for r in rows:
        if subset is not None and not subset(r):
            continue
        d = by_img[r["image"]]
        d["gt"] += 1
        if r.get("detected"):
            d["det"] += 1
            if r.get("pred_fdi") is not None and r["pred_fdi"] == r["gt_fdi"]:
                d["exact"] += 1
    return [by_img[k] for k in sorted(by_img)]


def delta(control_rows, arm_rows, num, den, n_boot, seed, subset=None):
    """Paired delta (arm - control) on num/den, cluster-bootstrapped over images."""
    import numpy as np
    a = payloads(control_rows, subset)
    b = payloads(arm_rows, subset)
    assert len(a) == len(b), f"arms disagree on image count: {len(a)} vs {len(b)}"
    rng = np.random.default_rng(seed)
    point, lo, hi, frac_le0 = paired_bootstrap(a, b, ratio(num, den), n_boot, rng)
    base = ratio(num, den)(a)
    return {"control": base, "arm": base + point, "delta_pp": point * 100,
            "lo_pp": lo * 100, "hi_pp": hi * 100, "frac_resamples_le_0": frac_le0}


def point_only(control_rows, arm_rows, num, den, subset):
    """A stratified point estimate -- no interval, exactly as §4 specifies for the strata."""
    a, b = payloads(control_rows, subset), payloads(arm_rows, subset)
    f = ratio(num, den)
    ca, cb = f(a), f(b)
    if ca is None or cb is None:
        return None
    return {"control": ca, "arm": cb, "delta_pp": (cb - ca) * 100,
            "n_teeth": sum(p[den] for p in a)}


def fmt(d):
    return (f"{d['control']:.3%} -> {d['arm']:.3%}   delta {d['delta_pp']:+.2f} pp"
            + (f"  [{d['lo_pp']:+.2f}, {d['hi_pp']:+.2f}]" if "lo_pp" in d else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tufts", type=Path, default=LC / "tufts_test")
    ap.add_argument("--dentex", type=Path, default=LC / "dentex")
    ap.add_argument("--out", type=Path, default=LC / "lever_c_bootstrap.json")
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    res = {"n_boot": args.n_boot, "seed": args.seed,
           "bars": {"primary_lower_bound_pp": PRIMARY_MIN_LB,
                    "guard_lower_bound_pp": GUARD_MIN_LB,
                    "anterior_point_pp": ANTERIOR_MIN_POINT},
           "arms": {}}

    t_ctl = rows_path(args.tufts, "head", "hungarian")
    d_ctl = rows_path(args.dentex, "head", "hungarian")

    for arm in ARMS:
        t_arm, d_arm = rows_path(args.tufts, "head", arm), rows_path(args.dentex, "head", arm)
        if not t_arm.exists() or not d_arm.exists():
            print(f"  {arm}: SKIP (missing {t_arm if not t_arm.exists() else d_arm})")
            continue
        a = {
            "tufts_of_detected": delta(t_ctl, t_arm, "exact", "det", args.n_boot, args.seed),
            "tufts_end_to_end": delta(t_ctl, t_arm, "exact", "gt", args.n_boot, args.seed),
            "dentex_of_detected": delta(d_ctl, d_arm, "exact", "det", args.n_boot, args.seed),
            "dentex_end_to_end": delta(d_ctl, d_arm, "exact", "gt", args.n_boot, args.seed),
            "strata": {
                "tufts_anterior_pos_1_3": point_only(t_ctl, t_arm, "exact", "det",
                                                     lambda r: r["gt_fdi"] % 10 <= 3),
                "tufts_posterior_pos_4_8": point_only(t_ctl, t_arm, "exact", "det",
                                                      lambda r: r["gt_fdi"] % 10 >= 4),
                "tufts_images_with_gap": point_only(t_ctl, t_arm, "exact", "det",
                                                    lambda r: r.get("image_has_gap")),
                "tufts_images_contiguous": point_only(t_ctl, t_arm, "exact", "det",
                                                      lambda r: not r.get("image_has_gap")),
            },
        }
        primary_ok = a["tufts_of_detected"]["lo_pp"] >= PRIMARY_MIN_LB
        guard_ok = (a["dentex_of_detected"]["lo_pp"] >= GUARD_MIN_LB
                    and a["dentex_end_to_end"]["lo_pp"] >= GUARD_MIN_LB)
        ant = a["strata"]["tufts_anterior_pos_1_3"]
        strat_ok = ant is not None and ant["delta_pp"] >= ANTERIOR_MIN_POINT
        a["verdict"] = {"primary": primary_ok, "guard": guard_ok, "stratified": strat_ok,
                        "adopt": bool(primary_ok and guard_ok and strat_ok)}
        res["arms"][arm] = a

        print("\n" + "=" * 78)
        print(f"LEVER C -- {arm} vs hungarian   ({args.n_boot} resamples, seed {args.seed})")
        print("=" * 78)
        print(f"  PRIMARY  Tufts of-detected : {fmt(a['tufts_of_detected'])}")
        print(f"           Tufts end-to-end  : {fmt(a['tufts_end_to_end'])}")
        print(f"  GUARD    DENTEX of-detected: {fmt(a['dentex_of_detected'])}")
        print(f"           DENTEX end-to-end : {fmt(a['dentex_end_to_end'])}")
        for k, v in a["strata"].items():
            if v:
                print(f"  STRATUM  {k:<26}: {fmt(v)}   (n={v['n_teeth']} detected)")
        print(f"\n  primary    (LB >= {PRIMARY_MIN_LB:+.1f} pp)  : {'PASS' if primary_ok else 'FAIL'}")
        print(f"  guard      (LB >= {GUARD_MIN_LB:+.1f} pp)  : {'PASS' if guard_ok else 'FAIL'}")
        print(f"  stratified (anterior >= {ANTERIOR_MIN_POINT:+.1f} pp) : "
              f"{'PASS' if strat_ok else 'FAIL'}")
        print(f"  ==> {'ADOPT' if a['verdict']['adopt'] else 'DO NOT ADOPT'} (frozen rule §5)")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
