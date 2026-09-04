#!/usr/bin/env python
"""
Bootstrap 95% confidence intervals for every headline metric that has saved per-item outputs.

WHY THIS EXISTS
---------------
Until 27 Aug 2026 **not one number in this project carried a confidence interval**. Every
headline figure was a bare point estimate: 58.3% end-to-end, 44.3% lesion agreement, 40.8%
external caries. `PAPER_MATERIAL.md` §9 lists "confidence intervals or k-fold for every headline
metric" as a blocking item, and a reviewer meeting a table of bare proportions on 936 teeth and
148 images will ask for them before reading anything else.

UPDATE, 4 Sep 2026 -- the Ningxia periodontitis gap below is CLOSED
---------------------------------------------------------------------
`ningxia_external.py` now writes `n_affected`/`n_affected_flagged` into each periodontitis
per-image record (they were computed all along, just discarded before being written out). No
new evaluation logic; a re-run against the locked cohort, weights unchanged from the deployed
default, reproduces the existing aggregate numbers exactly (2.4/1.4/5.6/4.6% per split) before
anything is bootstrapped. See the new section below. The "Detection mAP" and "two ResNet18s"
gaps remain -- see `scripts/eval/tufts_detector_ap_bootstrap.py` for the former (new, same day);
the bone-loss classifiers' own per-item dump would need the original un-rotated Tufts
radiographs, confirmed still absent from every machine checked (RESULTS_LOG 2026-09-04l).

THE ONE METHODOLOGICAL CHOICE THAT MATTERS: RESAMPLE IMAGES, NOT TEETH
----------------------------------------------------------------------
Teeth are **not independent**. The 936 Stage-2 teeth come from 164 radiographs; teeth in one
radiograph share a patient, a scanner, an exposure and an operator, and the pipeline's errors are
correlated within an image (a mis-numbered quadrant mis-numbers several teeth at once -- measured:
off-by-one errors cluster, RESULTS_LOG 2026-08-27e). Bootstrapping over **teeth** would treat 936
correlated observations as 936 independent ones and produce intervals that are far too narrow --
a real and common way to overstate precision.

So this is a **cluster bootstrap**: resample IMAGES with replacement, take all teeth belonging to
each drawn image, recompute the metric. n = the number of images, not the number of teeth. That is
the honest unit of independence here.

PAIRED DELTAS
-------------
Where a control arm exists (the pre-27-Aug bbox detector), the same resampled image set is used
for both arms and the DIFFERENCE is bootstrapped. A CI on the delta answers "is this improvement
real?", which is the question the +12.0 and +7.7 point claims actually make. Unpaired CIs on the
two endpoints would be a weaker and slightly wrong way to ask it, since the arms share images.

WHAT IS NOT COVERED, AND WHY
-----------------------------
**Ningxia periodontitis has no interval here.** `ningxia_external.py` records affected-tooth
counts only in the per-split aggregate, never per image, so there is no cluster to resample. The
script has been noted for that; recomputing it would mean re-evaluating locked external data,
which is not worth spending a touch on for a logging omission.

Usage:
    python scripts/eval/bootstrap_ci.py
    python scripts/eval/bootstrap_ci.py --n-boot 20000 --seed 7
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "outputs" / "bootstrap_ci"


def cluster_bootstrap(clusters, stat, n_boot, rng):
    """clusters: list of per-image payloads. stat: payload-list -> float (or None if undefined)."""
    import numpy as np
    keys = list(range(len(clusters)))
    point = stat([clusters[k] for k in keys])
    draws = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(keys), len(keys))
        v = stat([clusters[i] for i in idx])
        if v is not None:
            draws.append(v)
    draws = np.array(draws)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return point, float(lo), float(hi), len(draws)


def paired_bootstrap(clusters_a, clusters_b, stat, n_boot, rng):
    """Same resampled images for both arms; bootstrap the difference b - a."""
    import numpy as np
    assert len(clusters_a) == len(clusters_b)
    n = len(clusters_a)
    point = stat(clusters_b) - stat(clusters_a)
    draws = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        va = stat([clusters_a[i] for i in idx])
        vb = stat([clusters_b[i] for i in idx])
        if va is not None and vb is not None:
            draws.append(vb - va)
    draws = np.array(draws)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    # Fraction of resamples on the wrong side of zero -- a bootstrap two-sided p-ish value.
    frac_le0 = float((draws <= 0).mean())
    return point, float(lo), float(hi), frac_le0


def ratio(num_key, den_key):
    def f(payloads):
        num = sum(p[num_key] for p in payloads)
        den = sum(p[den_key] for p in payloads)
        return num / den if den else None
    return f


def load_stage2(path):
    """936 per-tooth rows -> per-image payloads of counts."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    by_img = defaultdict(lambda: {"gt": 0, "detected": 0, "exact": 0, "exact_of_det": 0})
    for r in rows:
        d = by_img[r["image"]]
        d["gt"] += 1
        if r.get("detected"):
            d["detected"] += 1
            if r.get("pred_fdi") is not None and r.get("pred_fdi") == r.get("gt_fdi"):
                d["exact"] += 1
                d["exact_of_det"] += 1
    return [dict(v, image=k) for k, v in sorted(by_img.items())]


def load_per_image(path, keys):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = d["per_image"] if isinstance(d, dict) else d
    return rows, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    import numpy as np
    rng = np.random.default_rng(args.seed)

    results = {"n_boot": args.n_boot, "seed": args.seed,
               "method": "cluster bootstrap over IMAGES (percentile 95% CI); "
                         "teeth within an image are not independent",
               "metrics": [], "deltas": []}

    def add(name, unit, n_clusters, point, lo, hi, note=""):
        results["metrics"].append({"metric": name, "unit": unit, "n_images": n_clusters,
                                   "point": round(point, 4), "ci95": [round(lo, 4), round(hi, 4)],
                                   "note": note})
        print(f"  {name:46s} {point:7.1%}  [{lo:6.1%}, {hi:6.1%}]   n={n_clusters} images")

    def add_delta(name, point, lo, hi, frac_le0, note=""):
        results["deltas"].append({"delta": name, "point_pp": round(point * 100, 2),
                                  "ci95_pp": [round(lo * 100, 2), round(hi * 100, 2)],
                                  "frac_resamples_le_0": frac_le0, "note": note})
        sig = "excludes 0" if lo > 0 or hi < 0 else "INCLUDES 0"
        print(f"  {name:46s} {point*100:+6.1f} pp [{lo*100:+6.1f}, {hi*100:+6.1f}]  {sig}")

    # ---------------------------------------------------------------- Stage 2
    seg = REPO_ROOT / "outputs/stage2_segdet/stage2_rows_head.json"
    ctl = REPO_ROOT / "outputs/stage2_control_olddet/stage2_rows_head.json"
    if seg.exists():
        print("\nSTAGE 2 — FDI numbering (DENTEX, 164 leak-free images)")
        cs = load_stage2(seg)
        add("detection recall", "tooth", len(cs), *cluster_bootstrap(
            cs, ratio("detected", "gt"), args.n_boot, rng)[:3])
        add("FDI exact, end-to-end", "tooth", len(cs), *cluster_bootstrap(
            cs, ratio("exact", "gt"), args.n_boot, rng)[:3])
        add("FDI exact, of detected", "tooth", len(cs), *cluster_bootstrap(
            cs, ratio("exact_of_det", "detected"), args.n_boot, rng)[:3])
        if ctl.exists():
            ca = load_stage2(ctl)
            ia = {c["image"]: c for c in ca}
            paired_a = [ia[c["image"]] for c in cs if c["image"] in ia]
            paired_b = [c for c in cs if c["image"] in ia]
            if len(paired_a) == len(paired_b) and paired_a:
                add_delta("Δ FDI exact end-to-end (seg − bbox)", *paired_bootstrap(
                    paired_a, paired_b, ratio("exact", "gt"), args.n_boot, rng))
                add_delta("Δ detection recall (seg − bbox)", *paired_bootstrap(
                    paired_a, paired_b, ratio("detected", "gt"), args.n_boot, rng))

    # ---------------------------------------------------------------- lesion localisation
    seg = REPO_ROOT / "outputs/lesion_localization_segdet/lesion_localization.json"
    ctl = REPO_ROOT / "outputs/lesion_localization_control_olddet/lesion_localization.json"
    if seg.exists():
        print("\nLESION LOCALISATION — DENTEX internal")
        rows, _ = load_per_image(seg, None)
        add("lesion agreement (DENTEX)", "lesion", len(rows), *cluster_bootstrap(
            rows, ratio("n_matched", "n_lesions"), args.n_boot, rng)[:3])
        if ctl.exists():
            rc, _ = load_per_image(ctl, None)
            ic = {r["image"]: r for r in rc}
            pb = [r for r in rows if r["image"] in ic]
            pa = [ic[r["image"]] for r in pb]
            if pa:
                add_delta("Δ lesion agreement (seg − bbox)", *paired_bootstrap(
                    pa, pb, ratio("n_matched", "n_lesions"), args.n_boot, rng))

    # ---------------------------------------------------------------- Ningxia caries
    seg = REPO_ROOT / "outputs/ningxia_caries_segdet/ningxia_external.json"
    ctl = REPO_ROOT / "outputs/ningxia_caries_control_olddet/ningxia_external.json"
    if seg.exists():
        print("\nNINGXIA CARIES — external, per hospital (never pooled for inference)")
        rows, _ = load_per_image(seg, None)
        by_split = defaultdict(list)
        for r in rows:
            by_split[r["split"]].append(r)
        for sp in sorted(by_split):
            add(f"caries agreement — {sp}", "lesion", len(by_split[sp]), *cluster_bootstrap(
                by_split[sp], ratio("n_covered", "n_lesions"), args.n_boot, rng)[:3])
        add("caries agreement — pooled (scale only)", "lesion", len(rows), *cluster_bootstrap(
            rows, ratio("n_covered", "n_lesions"), args.n_boot, rng)[:3],
            note="pooled across hospitals for scale; report per-centre for inference")
        if ctl.exists():
            rc, _ = load_per_image(ctl, None)
            # Key on (category, split, image), NOT image alone. Ningxia filenames REPEAT across
            # splits -- test1/1.png and test2/1.png are both "1.png" -- so keying by name
            # collapses four hospitals into one and silently mis-pairs the arms. Caught because
            # the paired delta came out +10.9 pp against a known measured +7.7 (RESULTS_LOG
            # 2026-08-27h): a number that disagrees with a reference is a bug, not a finding.
            key = lambda r: (r["category"], r["split"], r["image"])
            ic = {key(r): r for r in rc}
            pb = [r for r in rows if key(r) in ic]
            pa = [ic[key(r)] for r in pb]
            assert len(pa) == len(pb)
            if pa:
                add_delta("Δ caries agreement, pooled (seg − bbox)", *paired_bootstrap(
                    pa, pb, ratio("n_covered", "n_lesions"), args.n_boot, rng))

    # ---------------------------------------------------------------- Ningxia periodontitis
    perio = REPO_ROOT / "outputs/ningxia_periodontitis_ci/ningxia_external.json"
    if perio.exists():
        print("\nNINGXIA PERIODONTITIS — external, per hospital (affected-tooth sensitivity)")
        rows, _ = load_per_image(perio, None)
        rows = [r for r in rows if r["category"] == "periodontitis"]
        by_split = defaultdict(list)
        for r in rows:
            by_split[r["split"]].append(r)
        for sp in sorted(by_split):
            add(f"periodontitis sensitivity — {sp}", "tooth", len(by_split[sp]),
                *cluster_bootstrap(by_split[sp], ratio("n_affected_flagged", "n_affected"),
                                    args.n_boot, rng)[:3])
        add("periodontitis sensitivity — pooled (scale only)", "tooth", len(rows),
            *cluster_bootstrap(rows, ratio("n_affected_flagged", "n_affected"),
                                args.n_boot, rng)[:3],
            note="pooled across hospitals for scale; report per-centre for inference")

    results["not_covered"] = [
        "Detection mAP@0.5 (Tufts Stage-1 detector, frozen split_v1 test): no per-item "
        "prediction dump was saved by the original evaluation. NOW COVERED SEPARATELY -- see "
        "scripts/eval/tufts_detector_ap_bootstrap.py, which reimplements AP@0.5 from scratch "
        "(not ultralytics' own validator) specifically so it can be bootstrapped, and reports "
        "its own point estimate alongside the published 0.8100 rather than silently presenting "
        "the interval as wrapped around ultralytics' exact number.",
        "The two bone-loss ResNet18 classifiers (gate + severity): the headline 0.923 macro-F1 "
        "has no per-item dump, and the only alternative dataset on this machine "
        "(outputs/bone_loss_eval/bone_loss_val_nonjittered.json) is explicitly flagged by its "
        "own creator as 'DIVERGENT -- suspect crop geometry, do not use these crops' and scores "
        "a very different 0.537 macro-F1 on a disqualified subset. The original un-rotated "
        "Tufts radiographs needed to redo this properly are confirmed absent from every machine "
        "checked (RESULTS_LOG 2026-09-04l) -- genuinely blocked, not merely undone.",
    ]

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "bootstrap_ci.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"\n-> {args.out / 'bootstrap_ci.json'}")
    print("\nNOT COVERED:")
    for n in results["not_covered"]:
        print("  -", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
