#!/usr/bin/env python
"""Gates, point estimates and paired intervals for the Stage-1 detector re-measurement.

Pre-registration: outputs/stage1_switch/PRE_REGISTRATION.md, frozen at commit c139779 before any
run was made, with Amendment 1 (commit 85df6ff, row G's control gate) committed before any
Ningxia run, and Amendment 2 (rows I to M, for rebuilding the manuscript) before any of those. Every gate, comparison and the one stop rule below is fixed there; read it before
changing anything here.

Nothing here runs a model -- `outputs/stage1_switch/run_matrix.sh <row>` does. A row is reported
once both detectors have run it. Its arm3c files are not opened until the models/11 control has
passed its gate (Sec 3), and a failed gate stops the script.

    python scripts/eval/stage1_switch_intervals.py
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
from bootstrap_ci import cluster_bootstrap, load_stage2, ratio  # noqa: E402
from c1_vlm_baseline import DEF_DISEASE, load_gt, score  # noqa: E402
from caries_intervals import CONSTANT, N_BOOT, SEED, delta, f1, load_arm, prf, show  # noqa: E402
from lever_b_bootstrap import load_normalised  # noqa: E402

OUT = REPO_ROOT / "outputs" / "stage1_switch"
M3 = REPO_ROOT / "outputs" / "caries_intervals"      # this morning's same-machine arm files
DETS = ("m11", "arm3c")
SHA = {"m11": "271316c46caaf4029ea707fa77b6fe30697795e46632e1f6fcae3498c48781ba",
       "arm3c": "5d301f13fb48da5c74e7ef01bd0f91226f9b6800cb433dee5aebc8f8db8f161e"}
WEIGHTS = {"m11": "11_yolo_seg_tufts_r1/best.pt", "arm3c": "arm3c_best.pt"}
TOL_PP = 1.5        # Sec 3: tolerance against a figure produced on the other machine
S1_MARGIN_PP = -2.0  # Sec 5

# Sec 4, "Control must give". `exact` = produced on this machine; `other_machine` = recorded
# beside the control and held to TOL_PP.
LESION_ROWS = {
    "C": {"cohort": "DENTEX, 164 images", "dir": "C_dentex_{dec}_{det}",
          "file": "lesion_localization.json",
          "keys": ("n_lesions", "n_matched", "n_predicted_positive"),
          "decisions": ("pipeline", "constant-molars", "lesion-detector", "all-teeth"),
          "n_images": 164, "n_lesions": 479, "exact": {},
          # per_image lists only the 148 images that carry a caries lesion; the cohort is n_images
          "images_scored": lambda raw: raw["n_images"],
          "other_machine": {"pipeline": 212, "constant-molars": 234, "lesion-detector": 218}},
    "E": {"cohort": "CariesXrays, 1,200 held-out images", "dir": "E_cariesxrays_{dec}_{det}",
          "file": "cariesxrays_external_{dec}.json", "keys": ("lesions", "covered", "flagged"),
          "decisions": ("pipeline", "constant-molars", "lesion-detector"),
          "n_images": 1200, "n_lesions": 2815, "exact": {},
          "images_scored": lambda raw: raw["counts"]["images"],
          "other_machine": {"pipeline": 892, "constant-molars": 1582, "lesion-detector": 1926}},
    "F": {"cohort": "Ningxia caries, 337 images", "dir": "F_ningxia_caries_{dec}_{det}",
          "file": "ningxia_external.json",
          "keys": ("n_lesions", "n_covered", "n_predicted_positive"),
          "decisions": ("pipeline", "constant-molars", "lesion-detector"),
          "n_images": 337, "n_lesions": 1013, "exact": {"pipeline": 412},
          "images_scored": lambda raw: sum(v["images"] for v in raw["by_category_split"].values()),
          "other_machine": {"constant-molars": 404, "lesion-detector": 507}},
}
AGREEMENT = ratio("n_matched", "n_lesions")


def gate(ok, what):
    if not ok:
        raise SystemExit(f"\nSTOP -- {what}\nDo not read this row's arm3c result until it is explained.")


def est(rows, stat):
    """Point estimate and 95% cluster-bootstrap interval, fresh seeded generator."""
    import numpy as np
    pt, lo, hi, _ = cluster_bootstrap(rows, stat, N_BOOT, np.random.default_rng(SEED))
    return {"value": round(pt, 4), "ci95": [round(lo, 4), round(hi, 4)]}


def paired(base, rows):
    """`rows` in `base`'s image order; both must cover the same images exactly once."""
    by = {r["image"]: r for r in rows}
    if len(by) != len(rows) or len(base) != len(rows) or set(by) != {r["image"] for r in base}:
        raise SystemExit("two arms do not cover the same images one-to-one")
    return [by[r["image"]] for r in base]


def numbering(row, cohort, want):
    """Rows A and B. want = (images, teeth, teeth the control must number correctly)."""
    d = {det: OUT / f"{row}_{cohort}_{det}" for det in DETS}
    if not all((p / "stage2_summary_head.json").exists() for p in d.values()):
        return None
    print(f"\nRow {row} -- {cohort} numbering")

    def load(det):
        gate(WEIGHTS[det] in json.loads((d[det] / "stage2_summary_head.json").read_text())["detector"],
             f"row {row}: {d[det].name} was not produced by {det}")
        raw = json.loads((d[det] / "stage2_rows_head.json").read_text())
        return load_stage2(d[det] / "stage2_rows_head.json"), \
            sum(1 for r in raw if r["detected"] and r["pred_fdi"] is None)

    ctl, ctl_uncoded = load("m11")
    got = (len(ctl), sum(r["gt"] for r in ctl), sum(r["exact"] for r in ctl))
    gate(got == want, f"row {row} control: images/teeth/correct {got} != {want}")
    print(f"  control gate: {got[2]} of {got[1]} teeth correct on {got[0]} images -- reproduces")
    new, new_uncoded = load("arm3c")
    new = paired(ctl, new)
    stats = {"end_to_end": ratio("exact", "gt"), "recall": ratio("detected", "gt"),
             "exact_of_detected": ratio("exact", "detected")}
    res = {"control_gate": {"images": got[0], "teeth": got[1], "correct": got[2]}, "deltas": {}}
    for det, rows, uncoded in (("m11", ctl, ctl_uncoded), ("arm3c", new, new_uncoded)):
        res[det] = {"teeth": sum(r["gt"] for r in rows), "detected": sum(r["detected"] for r in rows),
                    "correct": sum(r["exact"] for r in rows), "matched_teeth_given_no_code": uncoded,
                    **{k: est(rows, s) for k, s in stats.items()}}
        print(f"  {det:6s} end-to-end {res[det]['end_to_end']['value']:.4f}  recall "
              f"{res[det]['recall']['value']:.4f}  of detected {res[det]['exact_of_detected']['value']:.4f}"
              f"  ({res[det]['correct']} correct, {uncoded} matched teeth given no code)")
    for k, s in stats.items():
        res["deltas"][f"{k}_arm3c_minus_m11"] = delta(ctl, new, s)
        show(f"{k}  arm3c - m11", res["deltas"][f"{k}_arm3c_minus_m11"])
    return res


def lesion_row(row):
    """Rows C, E and F. Returns (results, lesion-detector rows per detector for S1)."""
    c = LESION_ROWS[row]

    def path(dec, det):
        return OUT / c["dir"].format(dec=dec, det=det) / c["file"].format(dec=dec)

    if not all(path(dec, det).exists() for dec in c["decisions"] for det in DETS):
        return None, None
    print(f"\nRow {row} -- lesion agreement, {c['cohort']}")

    def load(dec, det):
        rows, raw = load_normalised(path(dec, det), *c["keys"])
        gate((raw.get("weights") or raw)["detector_sha256"] == SHA[det] and raw["decision"] == dec,
             f"row {row}: {path(dec, det).parent.name} is not {det} / {dec}")
        gate(c["images_scored"](raw) == c["n_images"],
             f"row {row} {det} {dec}: {c['images_scored'](raw)} images scored, expected {c['n_images']}")
        return rows

    ctl = {dec: load(dec, "m11") for dec in c["decisions"]}
    base = ctl[c["decisions"][0]]
    ctl = {dec: paired(base, rows) for dec, rows in ctl.items()}
    gates = {}
    for dec, rows in ctl.items():
        n_les, n_hit = sum(r["n_lesions"] for r in rows), sum(r["n_matched"] for r in rows)
        gate(n_les == c["n_lesions"],
             f"row {row} control {dec}: {n_les} lesions, expected {c['n_lesions']}")
        gates[dec] = {"lesions_matched": n_hit}
        if dec in c["exact"]:
            gate(n_hit == c["exact"][dec],
                 f"row {row} control {dec}: {n_hit} matched != {c['exact'][dec]} on this machine")
            gates[dec]["this_machine_reference"] = c["exact"][dec]
        if dec in c["other_machine"]:
            diff = 100 * (n_hit - c["other_machine"][dec]) / n_les
            gates[dec].update(other_machine=c["other_machine"][dec], difference_pp=round(diff, 2))
            gate(abs(diff) <= TOL_PP, f"row {row} control {dec}: {n_hit} matched vs "
                 f"{c['other_machine'][dec]} on the other machine, {diff:+.2f} pp > {TOL_PP}")
    print("  control gate: counts reproduce; " + ", ".join(
        f"{dec} {g['lesions_matched']}" + (f" (other machine {g['other_machine']})"
                                           if "other_machine" in g else "")
        for dec, g in gates.items()))
    arms = {"m11": ctl, "arm3c": {dec: paired(base, load(dec, "arm3c")) for dec in c["decisions"]}}

    groups = {"pooled": list(range(len(base)))}
    if row == "F":                                   # per hospital: id is category/split/image
        for i, r in enumerate(base):
            groups.setdefault(r["image"].split("/")[1], []).append(i)
    res = {"control_gate": gates}
    for g, idx in groups.items():
        out = {"n_images": len(idx), "arms": {det: {} for det in DETS}, "deltas": {}}
        sub = {det: {dec: [rows[i] for i in idx] for dec, rows in arms[det].items()} for det in DETS}
        for det in DETS:
            for dec, rows in sub[det].items():
                out["arms"][det][dec] = {
                    "lesion_agreement": est(rows, AGREEMENT),
                    "lesions": sum(r["n_lesions"] for r in rows),
                    "lesions_matched": sum(r["n_matched"] for r in rows),
                    "teeth_flagged": sum(r["n_pos"] for r in rows)}
            for comp in ("constant-molars", "pipeline"):
                out["deltas"][f"{det}: lesion-detector_minus_{comp}"] = delta(
                    sub[det][comp], sub[det]["lesion-detector"], AGREEMENT)
            # Added after the matrix (RESULTS_LOG 2026-10-11i) and NOT among the comparisons
            # PRE_REGISTRATION.md Sec 7 lists: the manuscript's own gate-vs-constant comparison
            # (its Tables IV-VII), from the same saved runs. A description; no rule reads it.
            out["deltas"][f"{det}: pipeline_minus_constant-molars"] = delta(
                sub[det]["constant-molars"], sub[det]["pipeline"], AGREEMENT)
        for dec in c["decisions"]:
            out["deltas"][f"{dec}: arm3c_minus_m11"] = delta(
                sub["m11"][dec], sub["arm3c"][dec], AGREEMENT)
        res[g] = out
        print(f"  {g} (n={len(idx)})")
        for det in DETS:
            print(f"    {det:6s} " + "   ".join(
                # the stored value is already rounded to 4 places: print all four, and the counts.
                # Printed to 3 it read 0.499 for 506/1013, which is 0.500 (RESULTS_LOG 2026-10-11h).
                f"{dec} {a['lesion_agreement']['value']:.4f} "
                f"({a['lesions_matched']}/{a['lesions']}; {a['teeth_flagged']} flagged)"
                for dec, a in out["arms"][det].items()))
        for k, d in out["deltas"].items():
            show(f"  {k.replace('_minus_', ' - ')}", d)
    return res, {det: arms[det]["lesion-detector"] for det in DETS}


def row_d():
    """FDI-set F1, both caries methods. The constant does not depend on the detector."""
    name = {"gate": "arm_pipeline.json", "lesion-detector": "arm_pipeline_lesion_detector.json"}
    morning = {"gate": M3 / "arm_pipeline_gate_control.json",
               "lesion-detector": M3 / "arm_pipeline_lesion_detector.json"}

    def path(method, det):
        return OUT / f"D_fdiset_{method}_{det}" / name[method]

    if not all(path(m, det).exists() for m in name for det in DETS):
        return None
    print("\nRow D -- FDI-set F1, 164 leak-free DENTEX images")
    gt = load_gt(DEF_DISEASE)
    gate(len(gt) == 164, f"row D: {len(gt)} leak-free images under {DEF_DISEASE}, expected 164")
    const = score(gt, {stem: CONSTANT for stem in gt}, "constant")
    gate((const["tp"], const["fp"], const["fn"]) == (286, 1026, 191), "row D: the constant moved")
    res = {"constant": prf(const)}
    for m in name:
        def load(det):
            raw = json.loads(path(m, det).read_text())
            gate(raw["detector_sha256"] == SHA[det] and raw["caries_method"] == m,
                 f"row D: {path(m, det).parent.name} is not {det} / {m}")
            return load_arm(path(m, det), gt), raw["mean_latency_s"]

        ctl_pred, ctl_lat = load("m11")
        gate(ctl_pred == load_arm(morning[m], gt),
             f"row D control {m}: predictions differ from {morning[m].name}")
        ctl = score(gt, ctl_pred, f"{m}_m11")
        new_pred, new_lat = load("arm3c")
        new = score(gt, new_pred, f"{m}_arm3c")
        res[m] = {"control_identical_to_this_morning": True,
                  "m11": {**prf(ctl), "mean_latency_s": ctl_lat},
                  "arm3c": {**prf(new), "mean_latency_s": new_lat},
                  "deltas": {"arm3c_minus_constant": delta(const["per_image"], new["per_image"], f1),
                             "arm3c_minus_m11": delta(ctl["per_image"], new["per_image"], f1)}}
        print(f"  {m}: control reproduces this morning's sets (tp/fp/fn {ctl['tp']}/{ctl['fp']}/{ctl['fn']})")
        for det, s, lat in (("m11", ctl, ctl_lat), ("arm3c", new, new_lat)):
            print(f"    {det:6s} P {s['precision']:.4f}  R {s['recall']:.4f}  F1 {s['f1']:.4f}  "
                  f"(tp/fp/fn {s['tp']}/{s['fp']}/{s['fn']})  {lat:.2f} s/image")
        for k, d in res[m]["deltas"].items():
            show(f"  F1  {k.replace('_minus_', ' - ')}", d)
    return res


def row_g():
    """Ningxia Stage-4 flag rate: affected teeth flagged / affected teeth."""
    path = {det: OUT / f"G_ningxia_stage4_{det}" / "ningxia_external.json" for det in DETS}
    if not all(p.exists() for p in path.values()):
        return None
    print("\nRow G -- Ningxia Stage-4 abnormality-proximity flag rate")
    rate = ratio("n_affected_flagged", "n_affected")

    def load(det):
        raw = json.loads(path[det].read_text())
        gate(raw["weights"]["detector_sha256"] == SHA[det], f"row G: {path[det].parent.name} is not {det}")
        return [dict(r, image=f"{r['category']}/{r['split']}/{r['image']}") for r in raw["per_image"]]

    # Amendment 1: an affected tooth is a DETECTED box, so 6,791 is the other machine's figure,
    # not a dataset count. The exact gate is the image count.
    ctl = load("m11")
    aff, hit = sum(r["n_affected"] for r in ctl), sum(r["n_affected_flagged"] for r in ctl)
    diff = 100 * (hit / aff - 165 / 6791)
    gate(len(ctl) == 736, f"row G control: {len(ctl)} images, expected 736")
    gate(abs(aff - 6791) <= 0.015 * 6791, f"row G control: {aff} affected teeth vs 6,791 on the other machine")
    gate(abs(diff) <= TOL_PP, f"row G control: {hit} flagged vs 165 on the other machine, {diff:+.2f} pp")
    print(f"  control gate: 736 images; {aff} affected teeth (other machine 6,791); "
          f"{hit} flagged (other machine 165)")
    new = paired(ctl, load("arm3c"))
    res = {"control_gate": {"images": len(ctl), "affected_teeth": aff, "flagged": hit,
                            "other_machine_affected_teeth": 6791, "other_machine_flagged": 165,
                            "flag_rate_difference_pp": round(diff, 2)}}
    for det, rows in (("m11", ctl), ("arm3c", new)):
        res[det] = {"images": len(rows), "affected_teeth": sum(r["n_affected"] for r in rows),
                    "affected_teeth_flagged": sum(r["n_affected_flagged"] for r in rows),
                    "teeth_detected": sum(r["n_teeth"] for r in rows),
                    "teeth_flagged": sum(r["n_predicted_positive"] for r in rows),
                    "flag_rate": est(rows, rate)}
        print(f"  {det:6s} {res[det]['affected_teeth_flagged']} of {res[det]['affected_teeth']} "
              f"affected teeth flagged = {res[det]['flag_rate']['value']:.4f}")
    res["delta_arm3c_minus_m11"] = delta(ctl, new, rate)
    show("flag rate  arm3c - m11", res["delta_arm3c_minus_m11"])

    # Row L (Amendment 2): the same files split by hospital. Ningxia is not scored again.
    other = {"test1": (79, 3285, 320), "test2": (34, 2462, 297), "test3": (23, 411, 50),
             "test4": (29, 633, 69)}                 # flagged, affected, images -- other machine
    res["per_hospital"] = {}
    for split, (o_hit, o_aff, o_img) in other.items():
        idx = [i for i, r in enumerate(ctl) if r["split"] == split]
        c, n = [ctl[i] for i in idx], [new[i] for i in idx]
        c_hit, c_aff = sum(r["n_affected_flagged"] for r in c), sum(r["n_affected"] for r in c)
        gap = 100 * (c_hit / c_aff - o_hit / o_aff)
        gate(len(c) == o_img, f"row L control {split}: {len(c)} images, expected {o_img}")
        gate(abs(gap) <= TOL_PP, f"row L control {split}: {c_hit}/{c_aff} vs {o_hit}/{o_aff} "
             f"on the other machine, {gap:+.2f} pp")
        out = {"images": len(c), "control_vs_other_machine_pp": round(gap, 2),
               "delta_arm3c_minus_m11": delta(c, n, rate)}
        for det, rows in (("m11", c), ("arm3c", n)):
            out[det] = {"affected_teeth": sum(r["n_affected"] for r in rows),
                        "affected_teeth_flagged": sum(r["n_affected_flagged"] for r in rows),
                        "flag_rate": est(rows, rate)}
        res["per_hospital"][split] = out
        print(f"  {split} (n={len(c)}): " + "   ".join(
            f"{det} {out[det]['affected_teeth_flagged']}/{out[det]['affected_teeth']} = "
            f"{out[det]['flag_rate']['value']:.4f}" for det in DETS))
    return res


def row_h():
    path = {det: OUT / f"H_params_{det}" / "param_counts.json" for det in DETS}
    if not all(p.exists() for p in path.values()):
        return None
    print("\nRow H -- parameter counts")
    res = {}
    for det in DETS:
        raw = json.loads(path[det].read_text())
        gate(WEIGHTS[det] in raw["checkpoints"]["stage1_detector"], f"row H: {path[det]} is not {det}")
        res[det] = {"stage1_detector": raw["params"]["stage1_detector"], **raw["totals"]}
        if det == "m11":
            gate((res[det]["stage1_detector"], res[det]["total_default"]) == (27617459, 97649753),
                 f"row H control: {res[det]}")
        print(f"  {det:6s} Stage 1 {res[det]['stage1_detector']:,}   pipeline total "
              f"{res[det]['total_default']:,}")
    return res


# ---- Amendment 2 (PRE_REGISTRATION.md): rows for rebuilding the manuscript ---------------------

TAXONOMY_OTHER_MACHINE = {"correct": 546, "not_detected": 275, "off_by_one": 89,
                          "same_quadrant_far": 10, "mirror_lr": 8, "wrong_arch": 6, "other": 2}


def row_i():
    """Numbering failure taxonomy, from the rows row B saved."""
    path = {det: OUT / f"I_taxonomy_{det}" / "stage2_failure_taxonomy.json" for det in DETS}
    if not all(p.exists() for p in path.values()):
        return None
    print("\nRow I -- numbering failure taxonomy, DENTEX, 936 teeth")

    def load(det):
        raw = json.loads(path[det].read_text())
        gate(f"B_dentex_{det}" in raw["source"], f"row I: {path[det].parent.name} did not read {det}'s rows")
        return {k: raw["categories"].get(k, 0) for k in TAXONOMY_OTHER_MACHINE}

    ctl = load("m11")
    gate((sum(ctl.values()), ctl["correct"], ctl["not_detected"]) == (936, 547, 273),
         f"row I control: {ctl}")
    worst = max(abs(ctl[k] - v) for k, v in TAXONOMY_OTHER_MACHINE.items())
    gate(worst <= 14, f"row I control: a bucket is {worst} teeth from the other machine's")
    print(f"  control gate: 936 / 547 / 273 reproduce; largest bucket gap to the other machine {worst} teeth")
    res = {"control_gate": {"other_machine": TAXONOMY_OTHER_MACHINE, "largest_bucket_gap_teeth": worst}}
    for det, cats in (("m11", ctl), ("arm3c", load("arm3c"))):
        detected = 936 - cats["not_detected"]
        wrong = detected - cats["correct"]
        wrong_quadrant = cats["mirror_lr"] + cats["wrong_arch"] + cats["other"]
        res[det] = {**cats, "detected": detected, "wrong_code": wrong,
                    "off_by_one_share_of_wrong_codes": round(cats["off_by_one"] / wrong, 4),
                    "wrong_quadrant": wrong_quadrant,
                    "wrong_quadrant_share_of_detected": round(wrong_quadrant / detected, 4)}
        print(f"  {det:6s} " + "  ".join(f"{k} {v}" for k, v in cats.items())
              + f"   | {cats['off_by_one']}/{wrong} wrong codes off by one; "
                f"{wrong_quadrant}/{detected} detected in a wrong quadrant")
    return res


def row_j():
    """Coverage-accuracy for numbering, from the same rows. The 0.30 threshold is located, not tuned."""
    path = {det: OUT / f"J_coverage_{det}" / "c4_coverage_accuracy.json" for det in DETS}
    if not all(p.exists() for p in path.values()):
        return None
    print("\nRow J -- coverage-accuracy for numbering, DENTEX")
    other = {"full": 0.826, "at_75": 0.8851, "gain_pp": 5.91, "op_coverage": 0.9077, "op_accuracy": 0.8467}

    def load(det):
        s2 = json.loads(path[det].read_text())["stage2"]
        gate(f"B_dentex_{det}" in s2["rows"], f"row J: {path[det].parent.name} did not read {det}'s rows")
        return s2

    def view(s2):
        op = s2["operating_point"]
        return {"teeth": s2["n"], "accuracy_full_coverage": s2["accuracy_full_coverage"],
                **{f"accuracy_at_{c}": round(s2[f"at_{c}"]["accuracy"], 4) for c in (90, 75, 50)},
                "gain_at_75_pp": s2["gain_at_75"]["gain_pp"], "gain_at_75_ci95_pp": s2["gain_at_75"]["ci95_pp"],
                "shuffled_control_gain_pp": s2["gain_at_75"]["shuffled_control_gain_pp"],
                "threshold": op["threshold"], "coverage_at_threshold": op["coverage"],
                "accuracy_at_threshold": op["accuracy"],
                "retained_at_threshold_of_936_present": round(op["coverage"] * s2["n"] / 936, 4),
                "retained_at_75_of_936_present": round(0.75 * s2["n"] / 936, 4)}

    ctl = view(load("m11"))
    gate((ctl["teeth"], round(ctl["accuracy_full_coverage"] * ctl["teeth"])) == (663, 547),
         f"row J control: {ctl['teeth']} teeth at {ctl['accuracy_full_coverage']}")
    gaps = {"full": ctl["accuracy_full_coverage"] - other["full"], "at_75": ctl["accuracy_at_75"] - other["at_75"],
            "op_coverage": ctl["coverage_at_threshold"] - other["op_coverage"],
            "op_accuracy": ctl["accuracy_at_threshold"] - other["op_accuracy"],
            "gain": (ctl["gain_at_75_pp"] - other["gain_pp"]) / 100}
    gate(max(abs(v) for v in gaps.values()) <= TOL_PP / 100,
         f"row J control is more than {TOL_PP} pp from the other machine: {gaps}")
    print("  control gate: 663 teeth / 547 correct reproduce; largest gap to the other machine "
          f"{100 * max(abs(v) for v in gaps.values()):.2f} pp")
    res = {"control_gate": {"other_machine": other, "gaps_pp": {k: round(100 * v, 2) for k, v in gaps.items()}},
           "m11": ctl, "arm3c": view(load("arm3c"))}
    for det in DETS:
        v = res[det]
        print(f"  {det:6s} full {v['accuracy_full_coverage']:.4f}  90% {v['accuracy_at_90']:.4f}  "
              f"75% {v['accuracy_at_75']:.4f}  50% {v['accuracy_at_50']:.4f}   gain@75 {v['gain_at_75_pp']:+.2f} pp "
              f"{v['gain_at_75_ci95_pp']} (shuffled {v['shuffled_control_gain_pp']:+.2f})   "
              f"at 0.30: coverage {v['coverage_at_threshold']:.4f}, accuracy {v['accuracy_at_threshold']:.4f}")
    return res


def row_k():
    """Stage-4 flags over detected teeth on DENTEX: a firing rate, not a sensitivity."""
    path = {det: OUT / f"K_dentex_stage4_{det}" / "dentex_stage4.json" for det in DETS}
    if not all(p.exists() for p in path.values()):
        return None
    print("\nRow K -- Stage-4 firing rate on DENTEX, 164 images")
    rate = ratio("stage4_flagged", "teeth_detected")
    subset = {p.stem for p in (REPO_ROOT / "outputs/r4_batch_v3").glob("*.json")}   # the 12 of 24-25 Aug

    def load(det):
        raw = json.loads(path[det].read_text())
        gate(raw["detector_sha256"] == SHA[det] and raw["n_images"] == 164,
             f"row K: {path[det].parent.name} is not {det} over 164 images")
        return raw["per_image"]

    ctl = load("m11")
    new = paired(ctl, load("arm3c"))
    res = {"manuscript_figure_not_a_gate": "2 of 299 teeth on 12 images, bbox detector, 24-25 Aug 2026"}
    for det, rows in (("m11", ctl), ("arm3c", new)):
        sub = [r for r in rows if r["image"] in subset]
        res[det] = {"images": len(rows), "teeth_detected": sum(r["teeth_detected"] for r in rows),
                    "stage4_flagged": sum(r["stage4_flagged"] for r in rows),
                    "images_with_a_flag": sum(r["stage4_flagged"] > 0 for r in rows),
                    "firing_rate": est(rows, rate),
                    "subset_of_12_images": {"images": len(sub),
                                            "teeth_detected": sum(r["teeth_detected"] for r in sub),
                                            "stage4_flagged": sum(r["stage4_flagged"] for r in sub)}}
        print(f"  {det:6s} {res[det]['stage4_flagged']} of {res[det]['teeth_detected']} detected teeth flagged "
              f"= {res[det]['firing_rate']['value']:.4f}   (the 12 images: "
              f"{res[det]['subset_of_12_images']['stage4_flagged']} of {res[det]['subset_of_12_images']['teeth_detected']})")
    res["delta_arm3c_minus_m11"] = delta(ctl, new, rate)
    show("firing rate  arm3c - m11", res["delta_arm3c_minus_m11"])
    return res


def row_m():
    """Tufts test box mAP@0.5 in the Lever A label frame: Control B first, then arm3c."""
    ref = {"controlB": (0.7243, "d3aa1e388fc41da1a449d2dd39b1e6c0764e8dd541edbc91c6cf896ac0145757"),
           "arm3c": (0.5852, SHA["arm3c"])}
    path = {w: OUT / f"M_tufts_map_{w}" / "tufts_test_map.json" for w in ref}
    if not all(p.exists() for p in path.values()):
        return None
    print("\nRow M -- Tufts test box mAP@0.5, 150 images, detector label frame")
    res = {}
    for w, (want, sha) in ref.items():
        raw = json.loads(path[w].read_text())
        gap = 100 * (raw["box_map50"] - want)
        gate(raw["sha256"] == sha, f"row M: {path[w].parent.name} is not {w}")
        gate(abs(gap) <= TOL_PP, f"row M {w}: {raw['box_map50']:.4f} vs {want} on the training machine, {gap:+.2f} pp")
        res[w] = {"box_map50": round(raw["box_map50"], 4), "training_machine": want,
                  "difference_pp": round(gap, 2), "box_map50_95": round(raw["box_map50_95"], 4),
                  "precision": round(raw["precision"], 4), "recall": round(raw["recall"], 4)}
        print(f"  {w:8s} mAP@0.5 {raw['box_map50']:.4f}   (training machine {want}, {gap:+.2f} pp)")
    res["arm3c_minus_controlB_pp"] = round(100 * (res["arm3c"]["box_map50"] - res["controlB"]["box_map50"]), 2)
    return res


def main():
    toy = [{"image": "a", "n_lesions": 2, "n_matched": 1}, {"image": "b", "n_lesions": 2, "n_matched": 2}]
    assert paired(toy, toy[::-1]) == toy and delta(toy, toy, AGREEMENT)["delta_pp"] == 0.0

    # This script's own two outputs are tracked, and a shell redirect into the .log modifies it
    # before the first line here runs -- so they are exempt; every other tracked output is not.
    # run_matrix.sh is exempt too: it is the command list, not a result, and it grows when an
    # amendment adds rows (it stopped the first read of rows I-M, RESULTS_LOG 2026-10-11j).
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", "outputs",
                            ":(exclude)outputs/stage1_switch/stage1_switch_results.json",
                            ":(exclude)outputs/stage1_switch/stage1_switch_results.log",
                            ":(exclude)outputs/stage1_switch/run_matrix.sh"],
                           cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    gate(not dirty.strip(), f"tracked files under outputs/ are modified:\n{dirty}")

    results = {"pre_registration": "outputs/stage1_switch/PRE_REGISTRATION.md",
               "frozen_at_commit": "c139779", "amendment_1_commit": "85df6ff",
               "amendment_2_commit": "d78f502",
               "n_boot": N_BOOT, "seed": SEED,
               "method": "paired cluster bootstrap over images, 95% percentile interval; every "
                         "difference between detectors is against the same-machine models/11 control",
               "A_tufts_numbering": numbering("A", "tufts", (143, 3760, 2438)),
               "B_dentex_numbering": numbering("B", "dentex", (164, 936, 547))}
    s1_rows = {}
    for row, key in (("C", "C_dentex_lesion_agreement"), ("E", "E_cariesxrays_lesion_agreement"),
                     ("F", "F_ningxia_caries_lesion_agreement")):
        results[key], s1_rows[row] = lesion_row(row)
    results.update(D_fdi_set_f1=row_d(), G_ningxia_stage4_flag=row_g(), H_parameter_counts=row_h())
    results.update(I_dentex_numbering_taxonomy=row_i(), J_dentex_numbering_coverage=row_j(),
                   K_dentex_stage4_firing=row_k(), M_tufts_test_box_map=row_m())

    print("\nS1 -- the one result that stops the switch (Sec 5)")
    if s1_rows["E"] and s1_rows["F"]:
        d = delta(s1_rows["E"]["m11"] + s1_rows["F"]["m11"],
                  s1_rows["E"]["arm3c"] + s1_rows["F"]["arm3c"], AGREEMENT)
        d.update(margin_pp=S1_MARGIN_PP, fires=bool(d["ci95_pp"][0] < S1_MARGIN_PP),
                 n_images=len(s1_rows["E"]["m11"]) + len(s1_rows["F"]["m11"]))
        results["S1"] = d
        show("lesion-detector path, arm3c - m11, E + F", d)
        print(f"  lower bound {d['ci95_pp'][0]:+.2f} pp against {S1_MARGIN_PP:+.1f} pp: "
              f"{'S1 FIRES -- DEF_DETECTOR is not changed' if d['fires'] else 'S1 does not fire'}")
    else:
        results["S1"] = None
        print("  pending: needs rows E and F")

    pending = [k for k, v in results.items() if v is None]
    print(f"\nrows not yet run: {', '.join(pending) or 'none'}")
    (OUT / "stage1_switch_results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"-> {OUT / 'stage1_switch_results.json'}")


if __name__ == "__main__":
    main()
