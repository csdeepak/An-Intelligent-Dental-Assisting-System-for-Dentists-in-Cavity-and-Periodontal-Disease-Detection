#!/usr/bin/env python
"""The one test pass of the retrained Stage-4a models (radiograph-level split).

Pre-registration: outputs/bone_loss_eval/v2_retrain/PRE_REGISTRATION.md, Sec 5 (what is reported)
and Sec 6 (the eligibility rule E1 and E2). Nothing here changes a default.

    python scripts/eval/bone_loss_v2_eval.py score    # the 143 test radiographs; refuses twice
    python scripts/eval/bone_loss_v2_eval.py report   # recompute the summary from the saved rows
    python scripts/eval/bone_loss_v2_eval.py dentex   # Amendment 1: Stage-4 firing on DENTEX, once
"""

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "tufts"))
from bone_loss_heldout import N_BOOT, SEED, load_scorer, load_sources, stats, summarise  # noqa: E402
from train_bone_loss_v2 import OUT as MODELS, SEEDS, WANT, build, split_stems            # noqa: E402

OUT = REPO_ROOT / "outputs/bone_loss_eval/v2_retrain"
SHIP = 42          # the seed whose checkpoint would be considered for shipping (Sec 2)


def best_f1_threshold(y, p):
    """The threshold maximising diseased-class F1; ties go to the higher threshold."""
    best, at = -1.0, 0.5
    for t in np.unique(p):
        f = p >= t
        tp, fp, fn = int((f & (y == 1)).sum()), int((f & (y == 0)).sum()), int((~f & (y == 1)).sum())
        f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0.0
        if f1 >= best:
            best, at = f1, float(t)
    return at, best


def score():
    rows_file = OUT / "test_rows.json"
    if rows_file.exists():
        raise SystemExit(f"REFUSED: {rows_file} exists; the test pass is made once (Sec 9)")
    hist = {s: json.loads((MODELS / f"seed{s}_history.json").read_text()) for s in SEEDS}
    for s in SEEDS:
        got = hashlib.sha256((MODELS / f"seed{s}_best.pth").read_bytes()).hexdigest()
        if got != hist[s]["sha256"]:
            raise SystemExit(f"seed {s}: the checkpoint is not the one its history recorded")
    stems, records = split_stems()
    if {k: len(v) for k, v in stems.items()} != WANT:
        raise SystemExit("the split is not the registered 678 / 145 / 143")
    _, old_trained_on, _ = load_sources()
    prior = json.loads((MODELS / "tooth_prior.json").read_text())

    xte, _, rows = build(stems["test"], records, with_jitter=False)
    xva, yva, _ = build(stems["val"], records, with_jitter=False)
    for r in rows:
        r["prior"] = prior["share_by_tooth"].get(r["tooth"], prior["overall_share"])
        r["old_trained_on"] = r["stem"] in old_trained_on
    for r, p in zip(rows, load_scorer()(xte), strict=True):        # the shipped, pinned checkpoint
        r["p_old"] = round(p, 6)
    for s in SEEDS:
        scorer = load_scorer(MODELS / f"seed{s}_best.pth", sha256=hist[s]["sha256"])
        for r, p in zip(rows, scorer(xte), strict=True):
            r[f"p_{s}"] = round(p, 6)
        if s == SHIP:
            thr, val_f1 = best_f1_threshold(yva, np.array(scorer(xva)))
    rows_file.write_text(json.dumps({"validation_threshold": {"seed": SHIP, "threshold": thr,
                                                              "validation_f1_diseased": round(val_f1, 4)},
                                     "sha256": {str(s): hist[s]["sha256"] for s in SEEDS},
                                     "rows": rows}) + "\n")
    print(f"scored {len(rows)} teeth of {len(stems['test'])} test radiographs -> {rows_file}")
    return report()


def with_p(rows, key):
    return [dict(r, p=r[key]) for r in rows]


def paired(rows, key_a, key_b):
    """Model a minus model b on the same teeth: point values and a radiograph-cluster interval."""
    y = np.array([r["label"] for r in rows])
    a, b = (np.array([r[k] for r in rows]) for k in (key_a, key_b))
    q = np.array([r["prior"] for r in rows])
    keys = ("sensitivity", "specificity", "ppv", "f1_diseased", "macro_f1", "average_precision", "roc_auc")

    def diff(idx):
        sa, sb = stats(y[idx], a[idx], q[idx])[0], stats(y[idx], b[idx], q[idx])[0]
        return {k: sa[k] - sb[k] for k in keys if k in sa and k in sb}

    members = defaultdict(list)
    for i, r in enumerate(rows):
        members[r["stem"]].append(i)
    members = [np.array(v) for v in members.values()]
    rng = np.random.default_rng(SEED)
    draws = defaultdict(list)
    for _ in range(N_BOOT):
        idx = np.concatenate([members[j] for j in rng.integers(0, len(members), len(members))])
        for k, v in diff(idx).items():
            draws[k].append(v)
    out = {}
    for k, v in diff(np.arange(len(rows))).items():
        d = np.array(draws[k], dtype=float)
        out[k] = {"value": round(v, 4), "ci95": [round(float(np.nanpercentile(d, 2.5)), 4),
                                                 round(float(np.nanpercentile(d, 97.5)), 4)]}
    return out


def line(name, s):
    c = s["confusion"]
    g = lambda k: f"{s[k]['value']:.4f} {s[k].get('ci95', '')}" if k in s and s[k]["value"] is not None else "-"
    print(f"  {name}: {s['radiographs']} radiographs, {s['teeth']} teeth, {s['positive_teeth']} positive | "
          f"TP {c['tp']} FN {c['fn']} FP {c['fp']} TN {c['tn']} | "
          f"false flags per radiograph {s['false_flags_per_radiograph']}")
    for k in ("sensitivity", "specificity", "ppv", "f1_diseased", "macro_f1", "average_precision",
              "roc_auc", "prior_average_precision", "ap_model_minus_prior"):
        print(f"      {k:24s} {g(k)}")


def report():
    saved = json.loads((OUT / "test_rows.json").read_text())
    rows = saved["rows"]
    pops = {"all": rows, "mask_non_empty": [r for r in rows if not r["mask_empty"]],
            "unseen_by_shipped": [r for r in rows if not r["old_trained_on"]]}

    def summary(sub, key):
        # summarise() looks the prior up by r["tooth"]; these rows carry it, so key it by row
        s = summarise([dict(r, tooth=i) for i, r in enumerate(with_p(sub, key))],
                      {i: r["prior"] for i, r in enumerate(sub)}, 0.0)
        s["false_flags_per_radiograph"] = round(s["confusion"]["fp"] / s["radiographs"], 3)
        return s

    res = {"pre_registration": "outputs/bone_loss_eval/v2_retrain/PRE_REGISTRATION.md",
           "committed_at": ["0993d4a", "d8dff27"], "sha256": saved["sha256"],
           "label": "crop overlaps a Tufts expert abnormality mask by more than 1% -- not periodontal bone loss",
           "method": f"radiograph-cluster bootstrap, {N_BOOT} resamples, seed {SEED}, percentile",
           "test_radiographs": len({r["stem"] for r in rows}),
           "test_radiographs_the_shipped_model_trained_on": len({r["stem"] for r in rows if r["old_trained_on"]})}

    print("\nShipped model, on the test radiographs it never trained on")
    res["shipped"] = {"unseen_by_shipped": summary(pops["unseen_by_shipped"], "p_old")}
    line("unseen_by_shipped", res["shipped"]["unseen_by_shipped"])

    for s in SEEDS:
        print(f"\nRetrained, seed {s}" + ("  <- the one that would ship" if s == SHIP else ""))
        res[f"seed_{s}"] = {name: summary(sub, f"p_{s}") for name, sub in pops.items()}
        for name in pops:
            line(name, res[f"seed_{s}"][name])
        d = paired(pops["unseen_by_shipped"], f"p_{s}", "p_old")
        e1 = d["f1_diseased"]["ci95"][0] > 0
        ap = res[f"seed_{s}"]["mask_non_empty"].get("ap_model_minus_prior", {})
        e2 = bool(ap.get("ci95")) and ap["ci95"][0] > 0
        res[f"seed_{s}"]["minus_shipped_on_unseen"] = d
        res[f"seed_{s}"]["E1_f1_above_shipped"] = bool(e1)
        res[f"seed_{s}"]["E2_ap_above_prior_in_masked"] = bool(e2)
        print("  minus shipped, same teeth: " + "  ".join(f"{k} {v['value']:+.4f} {v['ci95']}" for k, v in d.items()))
        print(f"  E1 (F1 above shipped): {'pass' if e1 else 'FAIL'}   "
              f"E2 (average precision above the prior, masked radiographs): {'pass' if e2 else 'FAIL'}")

    ship = res[f"seed_{SHIP}"]
    res["eligible"] = bool(ship["E1_f1_above_shipped"] and ship["E2_ap_above_prior_in_masked"])
    res["other_seeds_agree"] = all(res[f"seed_{s}"]["E1_f1_above_shipped"]
                                   and res[f"seed_{s}"]["E2_ap_above_prior_in_masked"] for s in SEEDS)

    thr = saved["validation_threshold"]
    y = np.array([r["label"] for r in rows])
    f = np.array([r[f"p_{SHIP}"] for r in rows]) >= thr["threshold"]
    tp, fp, fn, tn = (int((f & (y == 1)).sum()), int((f & (y == 0)).sum()),
                      int((~f & (y == 1)).sum()), int((~f & (y == 0)).sum()))
    res["validation_threshold_on_test"] = dict(thr, tp=tp, fp=fp, fn=fn, tn=tn,
                                               sensitivity=round(tp / (tp + fn), 4),
                                               specificity=round(tn / (tn + fp), 4),
                                               f1_diseased=round(2 * tp / (2 * tp + fp + fn), 4),
                                               note="secondary; not shipped -- the pipeline decides by argmax")
    print(f"\nSecondary: validation-chosen threshold {thr['threshold']:.4f} (seed {SHIP}) on test -> "
          f"sensitivity {tp}/{tp + fn}, specificity {tn}/{tn + fp}, F1 {res['validation_threshold_on_test']['f1_diseased']}")
    print(f"\nELIGIBLE to replace the shipped model (seed {SHIP}, E1 and E2): {res['eligible']}"
          f"   | all three seeds agree: {res['other_seeds_agree']}")
    (OUT / "test_summary.json").write_text(json.dumps(res, indent=2) + "\n")
    print(f"-> {OUT / 'test_summary.json'}")
    return 0


def dentex():
    """Amendment 1: Stage-4 flags on the 164 DENTEX images through the pipeline as shipped, the
    previous checkpoint first (it must reproduce 34 of 4,512), then the adopted default. A firing
    rate: DENTEX has no ground truth for this label."""
    out = OUT / "dentex_firing.json"
    if out.exists():
        raise SystemExit(f"REFUSED: {out} exists; this is run once")
    from collections import Counter

    import cv2
    import torch
    from bone_loss_heldout import WEIGHTS as PREVIOUS
    from bootstrap_ci import cluster_bootstrap, ratio
    from c1_vlm_baseline import DEF_DISEASE, load_gt
    from caries_intervals import delta
    from scripts.run_inference import DEF_BONE_LOSS, load_models, run_pipeline

    stems = sorted(load_gt(DEF_DISEASE))                      # the 164 leak-free images
    reports = {}
    for name, weights in (("previous", PREVIOUS), ("default", DEF_BONE_LOSS)):
        models, device, paths = load_models(bone_loss=weights, device=torch.device("cpu"))
        reports[name] = {}
        for stem in stems:
            img = cv2.imread(str(DEF_DISEASE / "input" / f"{stem}.png"), cv2.IMREAD_COLOR)
            # bone_severity_grade=True: the severity counts below were measured with the grade
            # computed, before it became opt-in (14 Oct 2026).
            reports[name][stem] = run_pipeline(img, models, device, paths, image_label=stem,
                                               verbose=False, bone_severity_grade=True)
        got = (sum(r["summary"]["bone_loss_positive"] for r in reports[name].values()),
               sum(r["summary"]["teeth_detected"] for r in reports[name].values()))
        print(f"{name}: {got[0]} of {got[1]} detected teeth flagged, {len(stems)} images "
              f"({reports[name][stems[0]]['models']['bone_loss']['tag_binary']})", flush=True)
        if name == "previous" and got != (34, 4512):
            raise SystemExit(f"STOP -- the control gives {got}, not the 34 of 4,512 of 11 Oct")

    rest = lambda rep: [{k: v for k, v in t.items() if k != "bone_loss"} for t in rep["teeth"]]
    untouched = all(rest(reports["previous"][s]) == rest(reports["default"][s]) for s in stems)
    rows = {name: [{"image": s, "teeth_detected": r["summary"]["teeth_detected"],
                    "flagged": r["summary"]["bone_loss_positive"]} for s, r in reps.items()]
            for name, reps in reports.items()}
    rate = ratio("flagged", "teeth_detected")
    res = {"pre_registration": "outputs/bone_loss_eval/v2_retrain/PRE_REGISTRATION.md, Amendment 1",
           "n_images": len(stems), "device": "cpu", "control_reproduces_34_of_4512": True,
           "every_field_outside_bone_loss_identical": bool(untouched)}
    for name, rws in rows.items():
        pt, lo, hi, _ = cluster_bootstrap(rws, rate, N_BOOT, np.random.default_rng(SEED))
        flagged_teeth = [t for r in reports[name].values() for t in r["teeth"]
                         if t["bone_loss"]["finding"] == "bone_loss"]
        res[name] = {"sha256": reports[name][stems[0]]["models"]["bone_loss"]["sha256_binary"],
                     "tag": reports[name][stems[0]]["models"]["bone_loss"]["tag_binary"],
                     "teeth_detected": sum(r["teeth_detected"] for r in rws),
                     "flagged": sum(r["flagged"] for r in rws),
                     "images_with_a_flag": sum(r["flagged"] > 0 for r in rws),
                     "firing_rate": {"value": round(pt, 4), "ci95": [round(lo, 4), round(hi, 4)]},
                     "severity_of_flagged_teeth": dict(Counter(t["bone_loss"]["severity"] for t in flagged_teeth))}
    res["default_minus_previous"] = delta(rows["previous"], rows["default"], rate)
    res["per_image"] = [{"image": a["image"], "teeth_detected": a["teeth_detected"],
                         "flagged_previous": a["flagged"], "flagged_default": b["flagged"]}
                        for a, b in zip(rows["previous"], rows["default"])]
    out.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "per_image"}, indent=2))
    return 0 if untouched else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("score", "report", "dentex"))
    sys.exit({"score": score, "report": report, "dentex": dentex}[ap.parse_args().step]())
