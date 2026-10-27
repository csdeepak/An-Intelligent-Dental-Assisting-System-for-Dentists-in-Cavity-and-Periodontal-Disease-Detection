#!/usr/bin/env python
"""Three interval measurements for the caries tables: M1, M2 and M3.

Pre-registration: outputs/caries_intervals/PRE_REGISTRATION.md, frozen at commit 1fd20b5 before
this file existed, with Amendment 1 (commit 33c1340, M3's control gate) committed before M3's
detector arm was run. Every comparison, harness gate and reading rule below is fixed there; read
it before changing anything here.

  M1  interval on the headline FDI-set F1 gap, constant vs pipeline     (saved predictions)
  M2  Lever B per Ningxia hospital, lesion detector vs constant / gate  (saved outputs)
  M3  the adopted lesion detector on the M1 metric                      (two arm files, below)

Nothing here runs a model. Each measurement first reproduces a published number exactly and
stops if it cannot. M3 reads two files that `c1_vlm_baseline.py --arm pipeline` writes and is
skipped, with a message, until they exist:

    python scripts/eval/c1_vlm_baseline.py --arm pipeline --caries-method gate \
        --out outputs/caries_intervals --out-name arm_pipeline_gate_control.json
    python scripts/eval/caries_intervals.py        # the control must pass before the next line
    python scripts/eval/c1_vlm_baseline.py --arm pipeline --caries-method lesion-detector \
        --out outputs/caries_intervals --out-name arm_pipeline_lesion_detector.json
    python scripts/eval/caries_intervals.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
from bootstrap_ci import cluster_bootstrap, paired_bootstrap, ratio  # noqa: E402
from c1_vlm_baseline import DEF_DISEASE, load_gt, score  # noqa: E402
from lever_b_bootstrap import LESION_RUN_SOURCES, SOURCES, load_normalised  # noqa: E402

OUT = REPO_ROOT / "outputs" / "caries_intervals"
C1 = REPO_ROOT / "outputs" / "c1_vlm"
N_BOOT, SEED = 10000, 42
CONSTANT = {"16", "17", "26", "27", "36", "37", "46", "47"}

# Published tp / fp / fn -- the M1 harness gate (c1_comparison.json, c1_constant_arm_*.json).
PUBLISHED_C1 = {"constant": (286, 1026, 191), "pipeline": (186, 604, 291),
                "vlm_32b": (116, 348, 361), "vlm_7b": (51, 155, 426)}
# Published pooled Ningxia deltas in pp -- the M2 harness gate (acceptance_rule_B-pooled.json).
PUBLISHED_NINGXIA = {"constant-molars": (10.17, [6.27, 14.02]), "pipeline": (9.28, [5.31, 13.29])}


def f1(rows):
    """Micro FDI-set F1 over `score()`'s per-image rows: 2*hit / (pred + gt)."""
    den = sum(r["n_pred"] + r["n_gt"] for r in rows)
    return 2 * sum(r["n_hit"] for r in rows) / den if den else None


def delta(a_rows, b_rows, stat):
    """b - a in percentage points: paired cluster bootstrap over images, fresh seeded rng."""
    import numpy as np
    pt, lo, hi, frac = paired_bootstrap(a_rows, b_rows, stat, N_BOOT, np.random.default_rng(SEED))
    return {"delta_pp": round(pt * 100, 2), "ci95_pp": [round(lo * 100, 2), round(hi * 100, 2)],
            "excludes_zero": bool(lo > 0 or hi < 0), "frac_resamples_le_0": round(frac, 4)}


def show(label, d):
    print(f"  {label:44s} {d['delta_pp']:+7.2f} pp  [{d['ci95_pp'][0]:+7.2f}, {d['ci95_pp'][1]:+7.2f}]"
          f"  {'excludes 0' if d['excludes_zero'] else 'INCLUDES 0'}")


def load_arm(path, gt):
    pred = {k: set(v) for k, v in json.loads(path.read_text())["predictions"].items()}
    if set(pred) != set(gt):
        raise SystemExit(f"{path.name}: covers {len(pred)} images, ground truth has {len(gt)}")
    return pred


def prf(s):
    return {k: s[k] for k in ("precision", "recall", "f1", "tp", "fp", "fn")}


def m1(gt):
    print("\nM1 -- FDI-set F1, 164 leak-free DENTEX images")
    arms = {"constant": {stem: CONSTANT for stem in gt},
            "pipeline": load_arm(C1 / "arm_pipeline.json", gt),
            "vlm_32b": load_arm(C1 / "arm_vlm_32b_0shot.json", gt),
            "vlm_7b": load_arm(C1 / "arm_vlm_7b_0shot_rerun.json", gt)}
    scored = {name: score(gt, pred, name) for name, pred in arms.items()}
    for name, want in PUBLISHED_C1.items():
        got = (scored[name]["tp"], scored[name]["fp"], scored[name]["fn"])
        if got != want:
            raise SystemExit(f"M1 HARNESS GATE FAILED: {name} tp/fp/fn {got} != published {want}")
    print("  harness gate: tp/fp/fn reproduce for all four arms")
    res = {"arms": {n: prf(s) for n, s in scored.items()}, "deltas": {}}
    for hi, lo in (("constant", "pipeline"), ("constant", "vlm_32b"),
                   ("constant", "vlm_7b"), ("pipeline", "vlm_32b")):
        d = delta(scored[lo]["per_image"], scored[hi]["per_image"], f1)
        res["deltas"][f"{hi}_minus_{lo}"] = d
        show(f"F1  {hi} - {lo}", d)
    return res, scored


def m2():
    import numpy as np
    print("\nM2 -- Lever B per Ningxia hospital, lesion agreement (saved outputs, no inference)")
    src = {**SOURCES, **LESION_RUN_SOURCES["B-pooled"]}
    names = ("lesion-detector", "constant-molars", "pipeline")
    arms = {a: load_normalised(*src[("ningxia", a)])[0] for a in names}
    ids = [r["image"] for r in arms["lesion-detector"]]
    for a in names:                                    # pair every arm on (category/split/image)
        by = {r["image"]: r for r in arms[a]}
        if len(by) != len(arms[a]) or set(by) != set(ids):
            raise SystemExit(f"M2: arm {a} does not pair one-to-one with the lesion detector")
        arms[a] = [by[i] for i in ids]
    stat = ratio("n_matched", "n_lesions")
    groups = {"pooled": list(range(len(ids)))}
    for i, img in enumerate(ids):
        groups.setdefault(img.split("/")[1], []).append(i)
    res = {}
    for g in ["pooled"] + sorted(k for k in groups if k != "pooled"):
        idx = groups[g]
        sub = {a: [arms[a][i] for i in idx] for a in names}
        out = {"n_images": len(idx), "arms": {}, "deltas": {}}
        for a in names:
            pt, lo, hi, _ = cluster_bootstrap(sub[a], stat, N_BOOT, np.random.default_rng(SEED))
            out["arms"][a] = {"lesion_agreement": round(pt, 4), "ci95": [round(lo, 4), round(hi, 4)]}
        for comp in ("constant-molars", "pipeline"):
            out["deltas"][f"lesion-detector_minus_{comp}"] = delta(sub[comp], sub["lesion-detector"], stat)
        res[g] = out
    for comp, (want_pt, want_ci) in PUBLISHED_NINGXIA.items():
        d = res["pooled"]["deltas"][f"lesion-detector_minus_{comp}"]
        if (d["delta_pp"], d["ci95_pp"]) != (want_pt, want_ci):
            raise SystemExit(f"M2 HARNESS GATE FAILED: pooled vs {comp} {d['delta_pp']} "
                             f"{d['ci95_pp']} != published {want_pt} {want_ci}")
    print("  harness gate: pooled deltas reproduce the published intervals")
    for g, out in res.items():
        a = out["arms"]
        print(f"  {g} (n={out['n_images']}): detector {a['lesion-detector']['lesion_agreement']:.3f}"
              f"  constant {a['constant-molars']['lesion_agreement']:.3f}"
              f"  gate {a['pipeline']['lesion_agreement']:.3f}")
        for k, d in out["deltas"].items():
            show(f"  {k.replace('_minus_', ' - ')}", d)
    return res


def m3(gt, scored):
    print("\nM3 -- the adopted lesion detector on the M1 metric")
    ctl_f, det_f = OUT / "arm_pipeline_gate_control.json", OUT / "arm_pipeline_lesion_detector.json"
    if not ctl_f.exists():
        print(f"  skipped: {ctl_f.name} not written yet (see the module docstring)")
        return None
    for f, method in ((ctl_f, "gate"), (det_f, "lesion-detector")):
        if f.exists() and json.loads(f.read_text()).get("caries_method") != method:
            raise SystemExit(f"M3: {f.name} was not produced with caries_method={method}")
    # Amendment 1 (commit 33c1340): the control is gated against the 322f787 code on THIS
    # machine, not against the published number, which came from a different machine. The
    # cross-machine difference is recorded, not gated.
    ctl_pred, old_pred = load_arm(ctl_f, gt), load_arm(OUT / "arm_pipeline_gate_code322f787.json", gt)
    ctl, pub = score(gt, ctl_pred, "gate_control"), scored["pipeline"]
    ok = ctl_pred == old_pred
    res = {"gate_control": prf(ctl), "control_identical_to_code_322f787": ok,
           "cross_machine_drift": {
               "published_gate": prf(pub), "f1_difference": round(ctl["f1"] - pub["f1"], 4),
               "images_identical": sum(ctl_pred[k] == p for k, p in load_arm(C1 / "arm_pipeline.json", gt).items()),
               "codes_differing": sum(len(ctl_pred[k] ^ p) for k, p in load_arm(C1 / "arm_pipeline.json", gt).items())}}
    print(f"  control (gate, this machine): F1 {ctl['f1']:.4f}; identical to the 322f787 code's "
          f"predictions: {'PASS' if ok else 'FAIL'}")
    d = res["cross_machine_drift"]
    print(f"  vs published (other machine) F1 {pub['f1']:.4f}: {d['f1_difference']:+.4f}, "
          f"{d['images_identical']}/164 images identical, {d['codes_differing']} codes differ -- recorded")
    if not ok:
        raise SystemExit("M3 CONTROL FAILED: do not run or read the detector arm; investigate first")
    if not det_f.exists():
        print(f"  control passed; {det_f.name} not written yet -- run the detector arm once")
        return res
    det = score(gt, load_arm(det_f, gt), "lesion_detector")
    res["lesion_detector"] = prf(det)
    print(f"  lesion-detector pipeline: P {det['precision']:.4f}  R {det['recall']:.4f}  "
          f"F1 {det['f1']:.4f}   (tp/fp/fn {det['tp']}/{det['fp']}/{det['fn']})")
    res["deltas"] = {
        "lesion_detector_minus_constant": delta(scored["constant"]["per_image"], det["per_image"], f1),
        "lesion_detector_minus_gate_control": delta(ctl["per_image"], det["per_image"], f1)}
    for k, d in res["deltas"].items():
        show(f"F1  {k.replace('_minus_', ' - ')}", d)
    return res


def main():
    toy = score({"a": {"16", "17"}, "b": set()}, {"a": {"16"}, "b": {"26"}}, "toy")
    assert f1(toy["per_image"]) == 0.5 == toy["f1"], "f1() disagrees with score()"

    gt = load_gt(DEF_DISEASE)
    if len(gt) != 164:
        raise SystemExit(f"expected 164 leak-free images under {DEF_DISEASE}, found {len(gt)}")
    r1, scored = m1(gt)
    results = {"pre_registration": "outputs/caries_intervals/PRE_REGISTRATION.md",
               "frozen_at_commit": "1fd20b5", "amendment_1_commit": "33c1340",
               "n_boot": N_BOOT, "seed": SEED,
               "method": "paired cluster bootstrap over images, 95% percentile interval",
               "m1_f1_gap": r1, "m2_ningxia_per_hospital": m2(), "m3_detector_f1": m3(gt, scored)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "caries_intervals.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"\n-> {OUT / 'caries_intervals.json'}")


if __name__ == "__main__":
    main()
