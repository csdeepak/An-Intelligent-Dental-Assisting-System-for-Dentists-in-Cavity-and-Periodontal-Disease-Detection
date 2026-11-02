#!/usr/bin/env python
"""Stability of the fitted image-blind constant, and the image-blind operating curve (DENTEX).

Review round 1, items 15 and 16 (paper/ieee/review/2026-11-02_panel_round1.md); RESULTS_LOG
2026-11-02d. Post hoc; labels and saved predictions only, no model is run.

1. Stability. The constant is fitted by rule (3) of the ten-page draft on 78 held-out images. Here
   those 78 images are resampled with replacement (10,000 resamples, seed 42), the rule is refitted
   on each resample, and every refitted constant is scored on the same 164 scored images. This
   measures how much the floor depends on which fit images happened to be available.
2. Operating curve. Constants of size k = 1..16, each the k most prevalent codes on the fit images
   (the order a deployable floor uses), scored on the 164 images, with the oracle order (prevalence
   on the scored images) as an optimistic envelope.
3. Matched volume. A system that names more codes than the constant can buy F1 with volume. Each
   system is compared with an image-blind answer that names the same number of codes: S_k on some
   images and S_{k+1} on the rest, a mixture chosen without looking at any image, whose true
   positives and named codes are linear in the mixing fraction. Paired cluster bootstrap over the
   164 images (10,000 resamples, seed 42), mixing fraction fixed from the full data.

    python scripts/eval/constant_stability_and_curve.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "eval"))
from c1_constant_baseline import best_constant, score_sets  # noqa: E402
from c1_vlm_baseline import load_exemplars, load_gt  # noqa: E402

DENTEX = Path.home() / "Downloads/Capstone/DENTEX/disease"
OUT = REPO / "outputs/review_round1/constant_stability_and_curve.json"
CONSTANT = {"16", "17", "26", "27", "36", "37", "46", "47"}
CODES = [str(q * 10 + p) for q in (1, 2, 3, 4) for p in range(1, 9)]
SYSTEMS = {  # name -> (saved predictions, Table 4 precision, recall, F1)
    "pipeline_lesion_detector": ("outputs/stage1_switch/D_fdiset_lesion-detector_arm3c/arm_pipeline_lesion_detector.json", 0.439, 0.574, 0.498),
    "pipeline_crop_classifier": ("outputs/stage1_switch/D_fdiset_gate_arm3c/arm_pipeline.json", 0.237, 0.765, 0.362),
    "qwen25vl_32b_zero_shot": ("outputs/c1_vlm/arm_vlm_32b_0shot.json", 0.250, 0.243, 0.246),
    "qwen25vl_7b_zero_shot": ("outputs/c1_vlm/arm_vlm_7b_0shot_rerun.json", 0.248, 0.107, 0.149),
}
B, SEED = 10_000, 42


def matrix(gt, stems):
    return np.array([[c in gt[s] for c in CODES] for s in stems], dtype=np.int64)


def rule3(counts, n_images):
    """Rule (3): walk the codes by prevalence; add code c while 2(A+n_c)/((k+1)N+P) > 2A/(kN+P)."""
    p_total = int(counts.sum())
    order = sorted(range(len(CODES)), key=lambda j: (-counts[j], CODES[j]))
    chosen, a = [], 0
    for j in order:
        n = int(counts[j])
        k = len(chosen)
        if n == 0 or 2 * (a + n) * (k * n_images + p_total) <= 2 * a * ((k + 1) * n_images + p_total):
            break
        chosen.append(j)
        a += n
    return frozenset(CODES[j] for j in chosen)


def f1_of(set_idx, scored_counts, n_scored, p_scored):
    tp = int(scored_counts[list(set_idx)].sum()) if set_idx else 0
    return 2 * tp / (len(set_idx) * n_scored + p_scored)


def main():
    scored = load_gt(DENTEX)
    fit = {s: set(c) for s, c in load_exemplars(DENTEX, 10_000)}
    assert len(scored) == 164 and sum(map(len, scored.values())) == 477
    assert len(fit) == 78 and not set(fit) & set(scored)
    s_stems, f_stems = sorted(scored), sorted(fit)
    Ms, Mf = matrix(scored, s_stems), matrix(fit, f_stems)
    ns, ps = len(s_stems), int(Ms.sum())
    sc = Ms.sum(0)
    idx = {c: j for j, c in enumerate(CODES)}

    # ---- 1. stability of the fitted constant
    base = rule3(Mf.sum(0), len(f_stems))
    assert base == CONSTANT == best_constant(fit)[0], base
    base_f1 = f1_of([idx[c] for c in base], sc, ns, ps)
    assert abs(base_f1 - 0.3197) < 5e-5
    rng = np.random.default_rng(SEED)
    sets, f1s, agree_greedy, ties = [], [], 0, 0
    for b in range(B):
        r = rng.integers(0, len(f_stems), len(f_stems))
        s = rule3(Mf[r].sum(0), len(f_stems))
        if b < 200:   # rule (3) and the evaluation's greedy F1 search must agree on resamples too
            boot = {f"{f_stems[i]}#{t}": fit[f_stems[i]] for t, i in enumerate(r)}
            g_set, g_f1 = best_constant(boot, max_size=16)
            if set(g_set) == set(s):
                agree_greedy += 1
            else:   # a disagreement must be a tie: same fit-sample F1, different codes
                assert abs(score_sets(boot, {k: set(s) for k in boot})["f1"] - g_f1) < 1e-4, (s, g_set)
                ties += 1
        sets.append(s)
        f1s.append(f1_of([idx[c] for c in s], sc, ns, ps))
    f1s = np.array(f1s)
    sizes = Counter(len(s) for s in sets)
    incl = Counter(c for s in sets for c in s)
    top_sets = Counter(tuple(sorted(s, key=int)) for s in sets).most_common(5)

    # ---- 2. operating curve
    fit_order = sorted(CODES, key=lambda c: (-int(Mf.sum(0)[idx[c]]), c))
    orc_order = sorted(CODES, key=lambda c: (-int(sc[idx[c]]), c))
    assert set(fit_order[:8]) == CONSTANT

    def curve(order):
        rows = []
        for k in range(1, 17):
            j = [idx[c] for c in order[:k]]
            tp = int(sc[j].sum())
            named = k * ns
            rows.append({"k": k, "codes": order[:k], "named": named, "tp": tp,
                         "precision": round(tp / named, 4), "recall": round(tp / ps, 4),
                         "f1": round(2 * tp / (named + ps), 4)})
        return rows

    fit_curve, orc_curve = curve(fit_order), curve(orc_order)
    assert fit_curve[7]["f1"] == 0.3197   # the frozen constant; the curve need not peak here on scored data

    # ---- 3. matched-volume comparison
    tp_k = np.stack([Ms[:, [idx[c] for c in fit_order[:k]]].sum(1) for k in range(0, 18)], 1)  # per image
    systems = {}
    rng = np.random.default_rng(SEED)
    boot_rows = rng.integers(0, ns, (B, ns))
    for name, (path, p_ref, r_ref, f_ref) in SYSTEMS.items():
        pred = {k: set(v) for k, v in json.loads((REPO / path).read_text())["predictions"].items()}
        pred = {s: pred.get(s, set()) for s in s_stems}
        r = score_sets(scored, pred)
        assert (round(r["precision"], 3), round(r["recall"], 3), round(r["f1"], 3)) == (p_ref, r_ref, f_ref), (name, r)
        tp_img = np.array([len(scored[s] & pred[s]) for s in s_stems])
        nm_img = np.array([len(pred[s]) for s in s_stems])
        per_img = nm_img.sum() / ns
        k = int(np.floor(per_img))
        frac = per_img - k
        c_tp_img = (1 - frac) * tp_k[:, k] + frac * tp_k[:, k + 1]
        c_named = per_img * ns
        c_f1 = 2 * c_tp_img.sum() / (c_named + ps)
        sys_f1 = 2 * tp_img.sum() / (nm_img.sum() + ps)
        g = Ms.sum(1)
        bt_sys = 2 * tp_img[boot_rows].sum(1) / (nm_img[boot_rows].sum(1) + g[boot_rows].sum(1))
        bt_con = 2 * c_tp_img[boot_rows].sum(1) / (per_img * ns + g[boot_rows].sum(1))
        d = 100 * (bt_sys - bt_con)
        systems[name] = {
            "named": int(nm_img.sum()), "named_per_image": round(per_img, 3), "tp": int(tp_img.sum()),
            "f1": round(sys_f1, 4),
            "matched_constant": {"mix": f"S_{k} on {1 - frac:.3f} of images, S_{k + 1} on {frac:.3f}",
                                 "f1": round(c_f1, 4), "precision": round(c_tp_img.sum() / c_named, 4)},
            "diff_pp": round(100 * (sys_f1 - c_f1), 2),
            "diff_ci95_pp": [round(float(np.percentile(d, 2.5)), 2), round(float(np.percentile(d, 97.5)), 2)],
            "frac_resamples_le_0": round(float((d <= 0).mean()), 4)}

    out = {
        "method": "post hoc; rule (3) refitted on 10,000 resamples (seed 42) of the 78 fit images and "
                  "scored on the 164 scored images; operating curve over constants of size 1-16; "
                  "matched-volume image-blind mixture with a paired cluster bootstrap over the 164 "
                  "images (10,000, seed 42).",
        "n_scored": ns, "n_carious_teeth": ps, "n_fit": len(f_stems),
        "stability": {
            "frozen_constant": sorted(base, key=int), "frozen_f1_scored": round(base_f1, 4),
            "rule3_equals_greedy_on_first_200_resamples": f"{agree_greedy}/200",
            "disagreements_that_are_ties_at_equal_fit_f1": ties,
            "frac_exactly_the_eight_molars": round(sum(s == CONSTANT for s in sets) / B, 4),
            "size_distribution": {str(k): round(v / B, 4) for k, v in sorted(sizes.items())},
            "inclusion_frequency": {c: round(incl[c] / B, 4) for c in sorted(incl, key=lambda c: -incl[c])},
            "most_common_sets": [{"set": list(s), "share": round(n / B, 4)} for s, n in top_sets],
            "scored_f1": {"median": round(float(np.median(f1s)), 4),
                          "p2_5": round(float(np.percentile(f1s, 2.5)), 4),
                          "p97_5": round(float(np.percentile(f1s, 97.5)), 4),
                          "min": round(float(f1s.min()), 4), "max": round(float(f1s.max()), 4),
                          "frac_within_0.01_of_frozen": round(float((np.abs(f1s - base_f1) <= 0.01).mean()), 4)}},
        "operating_curve_fit_order": fit_curve,
        "operating_curve_oracle_order": orc_curve,
        "matched_volume": systems,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    st = out["stability"]
    print(json.dumps({k: st[k] for k in ("frac_exactly_the_eight_molars", "size_distribution", "scored_f1",
                                         "rule3_equals_greedy_on_first_200_resamples", "most_common_sets")}, indent=1))
    print("curve (fit order):", [(r["k"], r["f1"]) for r in fit_curve])
    print("curve (oracle):  ", [(r["k"], r["f1"]) for r in orc_curve])
    print(json.dumps(systems, indent=1))


if __name__ == "__main__":
    # Self-check: one code carious in every image, nothing else -> rule (3) picks exactly that code.
    toy = np.zeros(len(CODES), dtype=np.int64); toy[CODES.index("36")] = 10
    assert rule3(toy, 10) == {"36"}
    main()
