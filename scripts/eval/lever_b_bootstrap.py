#!/usr/bin/env python
"""Lever B acceptance-rule numbers: paired cluster bootstrap, lesion-detector vs each comparator.

Pre-registration: outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md Sec 5 (metric),
Sec 6 (acceptance rule, fixed BEFORE these numbers were seen).

Reuses `cluster_bootstrap` / `paired_bootstrap` / `ratio` from `bootstrap_ci.py` rather than
reimplementing -- same 10,000-resample, seed-42, resample-IMAGES-not-teeth cluster bootstrap
every other headline number in this project uses (teeth/lesions within one image are not
independent -- see that module's docstring).

The two source scripts use DIFFERENT per_image key names for the same quantities (lesion count,
matched count) -- `lesion_localization.py` (DENTEX) writes `n_lesions`/`n_matched`;
`cariesxrays_external.py` writes `lesions`/`covered`. This script normalises both to one shape
rather than editing either producer (each name is right for its own file's other readers).

Usage:
    python scripts/eval/lever_b_bootstrap.py
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
from bootstrap_ci import cluster_bootstrap, paired_bootstrap, ratio  # noqa: E402

DEF_OUT = REPO_ROOT / "outputs" / "lever_b_eval"

# (cohort, arm) -> (json path, per_image lesion-count key, per_image matched-count key,
#                    per_image predicted-positive-count key). pipeline/constant-molars are the
# SAME run regardless of which lesion-detector arm is being scored (they don't touch the lesion
# model) -- only the "lesion-detector" row switches between B-single and B-pooled's output dir.
SOURCES = {
    ("dentex", "pipeline"): (DEF_OUT / "dentex_pipeline/lesion_localization.json",
                              "n_lesions", "n_matched", "n_predicted_positive"),
    ("dentex", "constant-molars"): (DEF_OUT / "dentex_constant/lesion_localization.json",
                                     "n_lesions", "n_matched", "n_predicted_positive"),
    ("cariesxrays", "pipeline"):
        (REPO_ROOT / "outputs/cariesxrays_external_lever_b_b_single/cariesxrays_external_pipeline.json",
         "lesions", "covered", "flagged"),
    ("cariesxrays", "constant-molars"):
        (REPO_ROOT / "outputs/cariesxrays_external_lever_b_b_single/cariesxrays_external_constant-molars.json",
         "lesions", "covered", "flagged"),
    ("ningxia", "pipeline"): (DEF_OUT / "ningxia_pipeline/ningxia_external.json",
                              "n_lesions", "n_covered", "n_predicted_positive"),
    ("ningxia", "constant-molars"): (DEF_OUT / "ningxia_constant/ningxia_external.json",
                                      "n_lesions", "n_covered", "n_predicted_positive"),
}

LESION_RUN_SOURCES = {
    "B-single": {
        ("dentex", "lesion-detector"):
            (DEF_OUT / "dentex_lesion_b_single/lesion_localization.json",
             "n_lesions", "n_matched", "n_predicted_positive"),
        ("cariesxrays", "lesion-detector"):
            (REPO_ROOT / "outputs/cariesxrays_external_lever_b_b_single/cariesxrays_external_lesion-detector.json",
             "lesions", "covered", "flagged"),
        ("ningxia", "lesion-detector"):
            (DEF_OUT / "ningxia_lesion_b_single/ningxia_external.json",
             "n_lesions", "n_covered", "n_predicted_positive"),
    },
    "B-pooled": {
        ("dentex", "lesion-detector"):
            (DEF_OUT / "dentex_lesion_b_pooled/lesion_localization.json",
             "n_lesions", "n_matched", "n_predicted_positive"),
        ("cariesxrays", "lesion-detector"):
            (REPO_ROOT / "outputs/cariesxrays_external_lever_b_b_pooled/cariesxrays_external_lesion-detector.json",
             "lesions", "covered", "flagged"),
        ("ningxia", "lesion-detector"):
            (DEF_OUT / "ningxia_lesion_b_pooled/ningxia_external.json",
             "n_lesions", "n_covered", "n_predicted_positive"),
    },
}


def load_normalised(path, lkey, mkey, pkey):
    """
    Ningxia filenames REPEAT across splits (test1/1.png and test2/1.png are both "1.png" --
    ningxia_external.py's own docstring, and the reason bootstrap_ci.py keys Ningxia rows on
    (category, split, image) rather than image alone). Build the same composite id here so a
    plain "image" dict key in the paired-comparison step below can't silently collapse two
    different images from different hospitals onto each other. DENTEX/CariesXrays rows have no
    "split"/"category" fields, so this degrades to plain "image" for them -- unchanged behaviour.
    """
    d = json.loads(Path(path).read_text())
    rows = d["per_image"]
    out = []
    for r in rows:
        img_id = "/".join(str(r[k]) for k in ("category", "split", "image") if k in r)
        out.append({"image": img_id, "n_lesions": r[lkey], "n_matched": r[mkey],
                    "n_pos": r[pkey]})
    return out, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--arm-tag", default="B-single", choices=list(LESION_RUN_SOURCES),
                    help="which lesion-detector run to score -- selects its source files")
    ap.add_argument("--out", type=Path, default=None,
                    help="defaults to outputs/lever_b_eval/acceptance_rule_<arm-tag>.json")
    args = ap.parse_args()
    if args.out is None:
        args.out = DEF_OUT / f"acceptance_rule_{args.arm_tag}.json"

    import numpy as np
    SOURCES.update(LESION_RUN_SOURCES[args.arm_tag])
    results = {"n_boot": args.n_boot, "seed": args.seed, "arm": args.arm_tag,
               "pre_registration": "outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md Sec 5/6",
               "method": "cluster bootstrap over IMAGES, reused from bootstrap_ci.py",
               "cohorts": {}}

    missing = [k for k, (p, *_) in SOURCES.items() if not p.exists()]
    if missing:
        print("NOT YET AVAILABLE (run the eval scripts first):")
        for k in missing:
            print(f"  {k} -> {SOURCES[k][0]}")
        if len(missing) == len(SOURCES):
            raise SystemExit("no eval outputs found -- nothing to bootstrap")

    for cohort in ("dentex", "cariesxrays", "ningxia"):
        arms = {}
        for arm in ("pipeline", "constant-molars", "lesion-detector"):
            key = (cohort, arm)
            if key not in SOURCES or not SOURCES[key][0].exists():
                continue
            path, lkey, mkey, pkey = SOURCES[key]
            rows, raw = load_normalised(path, lkey, mkey, pkey)
            arms[arm] = rows
        if "lesion-detector" not in arms:
            continue

        print(f"\n{'='*70}\n{cohort.upper()}  (n_images={len(arms['lesion-detector'])})\n{'='*70}")
        cohort_res = {"n_images": len(arms["lesion-detector"]), "arms": {}, "acceptance": {}}

        rng = np.random.default_rng(args.seed)
        for arm, rows in arms.items():
            pt, lo, hi, n = cluster_bootstrap(rows, ratio("n_matched", "n_lesions"),
                                              args.n_boot, rng)
            mean_pos = sum(r["n_pos"] for r in rows) / len(rows)
            cohort_res["arms"][arm] = {
                "lesion_agreement": round(pt, 4), "ci95": [round(lo, 4), round(hi, 4)],
                "mean_predicted_positive_per_image": round(mean_pos, 3),
            }
            print(f"  {arm:18s} agreement {pt:.1%} [{lo:.1%},{hi:.1%}]   "
                  f"mean flagged/image {mean_pos:.2f}")

        ld = arms["lesion-detector"]
        for comparator in ("constant-molars", "pipeline"):
            if comparator not in arms:
                continue
            comp = arms[comparator]
            by_img = {r["image"]: r for r in comp}
            paired_ld = [r for r in ld if r["image"] in by_img]
            paired_comp = [by_img[r["image"]] for r in paired_ld]
            if not paired_ld:
                continue
            rng = np.random.default_rng(args.seed)
            dpt, dlo, dhi, frac = paired_bootstrap(
                paired_comp, paired_ld, ratio("n_matched", "n_lesions"), args.n_boot, rng)
            excludes_zero = dlo > 0 or dhi < 0
            ld_rate = sum(r["n_pos"] for r in paired_ld) / len(paired_ld)
            comp_rate = sum(r["n_pos"] for r in paired_comp) / len(paired_comp)
            rate_ratio = ld_rate / comp_rate if comp_rate else float("inf")
            cohort_res["acceptance"][f"lesion-detector_minus_{comparator}"] = {
                "delta_pp": round(dpt * 100, 2), "ci95_pp": [round(dlo * 100, 2), round(dhi * 100, 2)],
                "excludes_zero": excludes_zero, "beats_comparator": excludes_zero and dpt > 0,
                "predicted_positive_rate_ratio": round(rate_ratio, 3),
                "rate_ratio_le_1.5x": rate_ratio <= 1.5,
            }
            print(f"  Delta (lesion-detector - {comparator}): {dpt*100:+.2f} pp "
                  f"[{dlo*100:+.2f},{dhi*100:+.2f}]  "
                  f"{'excludes 0' if excludes_zero else 'INCLUDES 0'}  "
                  f"rate ratio {rate_ratio:.2f}x {'OK' if rate_ratio <= 1.5 else 'OVER 1.5x CAP'}")

        results["cohorts"][cohort] = cohort_res

    # ---- Sec 6 acceptance rule, applied mechanically, not narratively ----
    print(f"\n{'='*70}\nSEC 6 ACCEPTANCE RULE (bar fixed before these numbers existed)\n{'='*70}")
    winning_cohorts = []
    for cohort, cres in results["cohorts"].items():
        acc = cres.get("acceptance", {})
        vs_const = acc.get("lesion-detector_minus_constant-molars", {})
        vs_gate = acc.get("lesion-detector_minus_pipeline", {})
        cond1 = vs_const.get("beats_comparator", False)
        cond2 = vs_const.get("rate_ratio_le_1.5x", False)
        cond3 = vs_gate.get("beats_comparator", False)
        all_pass = cond1 and cond2 and cond3
        if all_pass:
            winning_cohorts.append(cohort)
        print(f"  {cohort:14s} cond1(beats constant)={cond1}  cond2(rate<=1.5x)={cond2}  "
              f"cond3(beats gate)={cond3}  => {'PASS' if all_pass else 'fail'}")
    results["sec6_winning_cohorts"] = winning_cohorts
    results["sec6_rule_met"] = len(winning_cohorts) >= 2
    print(f"\n  cohorts passing all 3 conditions: {winning_cohorts} "
          f"({len(winning_cohorts)} of {len(results['cohorts'])} scored)")
    print(f"  Sec 6 requires >=2 of 3 cohorts => rule met: {results['sec6_rule_met']}")
    if len(results["cohorts"]) < 3:
        missing_cohorts = sorted({"dentex", "cariesxrays", "ningxia"} - set(results["cohorts"]))
        print(f"  NOTE: {missing_cohorts} not scored this run -- see PRE_REGISTRATION.md "
              f"fallback (2 of the available cohorts). Final call needs all available cohorts.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(f"\n-> {args.out}")


if __name__ == "__main__":
    main()
