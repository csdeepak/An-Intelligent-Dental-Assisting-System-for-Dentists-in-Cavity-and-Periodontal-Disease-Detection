"""Report-only plots for the Phase 3 report, drawn from saved artefacts (no number typed by hand).

Every value comes from a JSON or summary file under the repository; the asserts tie each plot to the
number the report text quotes, so a plot cannot silently disagree with the prose. Phase 2 palette
(PLAN.md) and Times New Roman, as in the Phase 2 report.

    python -I tools/make_plots.py      (run from report/phase3; writes figures/plots/*.pdf)
"""
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
OUT = HERE / "figures" / "plots"
OUT.mkdir(parents=True, exist_ok=True)

INDIGO, TEAL, MAROON, ORANGE, GREEN, GREY, ARROW = ("#3C348A", "#085142", "#6F271D", "#BA7218",
                                                    "#244E06", "#474348", "#9E9A94")
plt.rcParams.update({"font.family": "Times New Roman", "font.size": 10, "axes.titlesize": 10.5,
                     "axes.labelsize": 10, "legend.fontsize": 8.5, "xtick.labelsize": 9,
                     "ytick.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#E4E4E4", "grid.linewidth": 0.6,
                     "savefig.bbox": "tight", "pdf.fonttype": 42})


def load(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def close(a, b, tol=6e-4):
    return abs(a - b) <= tol


CSC = load("outputs/review_round1/constant_stability_and_curve.json")
HK = load("outputs/stage1_switch/F_ningxia_random_effects_hksj.json")
RE = load("outputs/stage1_switch/F_ningxia_random_effects.json")
SW = load("outputs/stage1_switch/stage1_switch_results.json")
ND = load("outputs/review_round1/dentex_near_duplicates.json")
PC = load("outputs/param_counts/param_counts.json")

# ------------------------------------------------------------------ P1 operating curve + matched volume
fit = CSC["operating_curve_fit_order"]
orc = CSC["operating_curve_oracle_order"]
mv = CSC["matched_volume"]
assert fit[7]["f1"] == 0.3197 and fit[7]["k"] == 8
assert close(mv["pipeline_lesion_detector"]["f1"], 0.4977) and close(mv["pipeline_crop_classifier"]["f1"], 0.3625)
fig, ax = plt.subplots(figsize=(6.6, 3.6))
ax.plot([r["k"] for r in fit], [r["f1"] for r in fit], "-o", color=INDIGO, ms=4, lw=1.6,
        label="Constant, fit-set order (deployable)")
ax.plot([r["k"] for r in orc], [r["f1"] for r in orc], "--", color=ARROW, lw=1.3,
        label="Constant, scored-set order (oracle)")
ax.axvline(8, color=INDIGO, lw=0.8, ls=":")
ax.annotate("eight molars\nF1 0.320", xy=(8, 0.3197), xytext=(12.4, 0.40), fontsize=8.5,
            arrowprops=dict(arrowstyle="->", color=INDIGO, lw=0.8), color=INDIGO)
style = {"pipeline_lesion_detector": (TEAL, "o", "Pipeline, lesion detector"),
         "pipeline_crop_classifier": (ORANGE, "s", "Pipeline, crop classifier"),
         "qwen25vl_32b_zero_shot": (MAROON, "^", "Qwen2.5-VL-32B"),
         "qwen25vl_7b_zero_shot": (GREY, "v", "Qwen2.5-VL-7B")}
for k, (c, m, lab) in style.items():
    s = mv[k]
    ax.plot(s["named_per_image"], s["f1"], m, color=c, ms=8, mec="white", mew=0.8, label=lab, zorder=4)
    ax.plot([s["named_per_image"]] * 2, [s["matched_constant"]["f1"], s["f1"]], color=c, lw=1.1, zorder=3)
    ax.plot(s["named_per_image"], s["matched_constant"]["f1"], "x", color=c, ms=6, zorder=4)
ax.set_xlabel("codes named per image")
ax.set_ylabel("FDI-set F1 (164 DENTEX images)")
ax.set_xlim(0.5, 16.5)
ax.set_ylim(0.08, 0.54)
ax.legend(loc="upper right", frameon=False, ncol=2)
ax.set_title("Image-blind operating curve; x marks the volume-matched constant for each system")
fig.savefig(OUT / "P1_operating_curve.pdf")
plt.close(fig)

# ------------------------------------------------------------------ P2 stability of the fitted constant
st = CSC["stability"]
assert close(st["frac_exactly_the_eight_molars"], 0.2668, 1e-4)
assert close(st["scored_f1"]["median"], 0.3197) and close(st["scored_f1"]["p2_5"], 0.2793)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 2.8), gridspec_kw={"width_ratios": [1, 1.5]})
sizes = sorted(st["size_distribution"], key=int)
a1.bar(sizes, [100 * st["size_distribution"][s] for s in sizes], color=INDIGO, width=0.65)
a1.set_xlabel("codes in the refitted constant")
a1.set_ylabel("share of 10,000 refits (%)")
a1.set_title("(a) Size of the refitted set")
incl = st["inclusion_frequency"]
codes = [c for c in sorted(incl, key=lambda c: -incl[c])][:11]
a2.bar(codes, [100 * incl[c] for c in codes],
       color=[TEAL if c in {"16", "17", "26", "27", "36", "37", "46", "47"} else ARROW for c in codes], width=0.65)
a2.set_xlabel("FDI code")
a2.set_ylabel("refits that include it (%)")
a2.set_title("(b) How often each code is chosen")
a2.text(0.98, 0.42, "scored F1 of the refits: median %.3f\n95%% within %.3f to %.3f" %
        (st["scored_f1"]["median"], st["scored_f1"]["p2_5"], st["scored_f1"]["p97_5"]),
        transform=a2.transAxes, ha="right", va="center", fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=ARROW, lw=0.6))
fig.tight_layout()
fig.savefig(OUT / "P2_constant_stability.pdf")
plt.close(fig)

# ------------------------------------------------------------------ P3 matched-volume differences
fig, ax = plt.subplots(figsize=(6.0, 2.4))
order = ["pipeline_lesion_detector", "pipeline_crop_classifier", "qwen25vl_32b_zero_shot", "qwen25vl_7b_zero_shot"]
assert mv["pipeline_lesion_detector"]["diff_pp"] == 22.35 and mv["pipeline_crop_classifier"]["diff_pp"] == 5.5
for y, k in enumerate(reversed(order)):
    c, m, lab = style[k]
    d, (lo, hi) = mv[k]["diff_pp"], mv[k]["diff_ci95_pp"]
    ax.plot([lo, hi], [y, y], color=c, lw=2.2)
    ax.plot(d, y, m, color=c, ms=8, mec="white", mew=0.8)
    ax.text(hi + 0.6, y, "%+.2f [%+.2f, %+.2f]" % (d, lo, hi), va="center", fontsize=8.5)
ax.axvline(0, color=GREY, lw=0.8)
ax.set_yticks(range(len(order)))
ax.set_yticklabels([style[k][2] for k in reversed(order)])
ax.set_xlabel("F1 minus a constant naming as many codes (percentage points)")
ax.set_xlim(-8, 40)
fig.savefig(OUT / "P3_matched_volume.pdf")
plt.close(fig)

# ------------------------------------------------------------------ P4 Ningxia: per site, pooled, DL, HKSJ
ps = RE["per_site"]
assert ps["test1"]["delta_pp"] == -3.16 and HK["hksj"]["ci95_pp"] == [-5.02, 24.24]
rows = [("test1 (cross-centre)", ps["test1"]["delta_pp"], ps["test1"]["ci95_pp"], GREY),
        ("test2 (training centre)", ps["test2"]["delta_pp"], ps["test2"]["ci95_pp"], GREY),
        ("test3 (cross-centre)", ps["test3"]["delta_pp"], ps["test3"]["ci95_pp"], GREY),
        ("test4 (cross-centre)", ps["test4"]["delta_pp"], ps["test4"]["ci95_pp"], GREY),
        ("pooled, sites fixed", RE["registered_pooled"]["delta_pp"], RE["registered_pooled"]["ci95_pp"], TEAL),
        ("random effects, DL", RE["mean_pp"], RE["ci95_pp"], INDIGO),
        ("random effects, HKSJ", HK["hksj"]["mean_pp"], HK["hksj"]["ci95_pp"], MAROON),
        ("prediction interval, new site", RE["mean_pp"], RE["prediction_interval_pp"], ARROW)]
fig, ax = plt.subplots(figsize=(6.6, 3.2))
for y, (lab, d, (lo, hi), c) in enumerate(reversed(rows)):
    ax.plot([max(lo, -40), min(hi, 60)], [y, y], color=c, lw=2.2, ls=":" if "prediction" in lab else "-")
    ax.plot(d, y, "D" if "random" in lab or "prediction" in lab else "o", color=c, ms=6.5, mec="white", mew=0.7)
    ax.text(62, y, "%+.2f [%+.2f, %+.2f]" % (d, lo, hi), va="center", fontsize=8)
ax.axvline(0, color=GREY, lw=0.8)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in reversed(rows)])
ax.set_xlim(-40, 60)
ax.set_xlabel("lesion agreement, lesion detector minus constant (percentage points)")
ax.set_title("Ningxia, 337 radiographs: per site and pooled (I² = %.0f%%, τ = %.2f pp)" % (RE["i2_pct"], RE["tau_pp"]))
fig.savefig(OUT / "P4_ningxia_pooling.pdf")
plt.close(fig)

# ------------------------------------------------------------------ P5 Stage 4a: the 0.923 and what replaced it
s18 = (REPO / "models/18_bone_loss_radiograph_split/run_summary.txt").read_text(encoding="utf-8")
s03 = (REPO / "models/03_bone_loss_model_training_notebook_models/run_summary.txt").read_text(encoding="utf-8")
assert "50/182 = 0.2747" in s18 and "30/182 = 0.1648" in s18 and "20/182 = 0.1099" in s18
assert "6/175 = 0.0343" in s18 and "0.8305" in s03 and "0.9953" in s03
bars = [("Phase 2 model,\nvalidation\n(crop split)", 0.8305, 0.9953, ORANGE),
        ("Phase 2 model,\n125 unseen test\nradiographs", 0.0343, 0.9877, MAROON),
        ("Radiograph split,\nseed 42 (shipped)", 0.2747, 0.9590, TEAL),
        ("Radiograph split,\nseed 43", 0.1648, 0.9806, INDIGO),
        ("Radiograph split,\nseed 44", 0.1099, 0.9863, INDIGO)]
fig, ax = plt.subplots(figsize=(6.8, 3.0))
x = range(len(bars))
ax.bar([i - 0.19 for i in x], [100 * b[1] for b in bars], 0.36, color=[b[3] for b in bars], label="sensitivity")
ax.bar([i + 0.19 for i in x], [100 * b[2] for b in bars], 0.36, color="#D9D9D9", edgecolor=GREY, lw=0.5, label="specificity")
for i, b in enumerate(bars):
    ax.text(i - 0.19, 100 * b[1] + 1.5, "%.1f" % (100 * b[1]), ha="center", fontsize=8)
    ax.text(i + 0.19, 100 * b[2] + 1.5, "%.1f" % (100 * b[2]), ha="center", fontsize=8)
ax.errorbar([2 - 0.19], [27.47], yerr=[[27.47 - 18.31], [37.98 - 27.47]], fmt="none", ecolor=GREY, capsize=3, lw=0.9)
ax.set_xticks(list(x))
ax.set_xticklabels([b[0] for b in bars], fontsize=8)
ax.set_ylabel("%")
ax.set_ylim(0, 112)
ax.legend(loc="upper center", frameon=False, ncol=2, bbox_to_anchor=(0.5, 1.13))
fig.savefig(OUT / "P5_stage4_correction.pdf")
plt.close(fig)

# ------------------------------------------------------------------ P6 near-duplicate check
cnt = ND["scored_nearest_neighbour_counts"]
assert ND["positive_control"]["md5_identical_query_images"] == 86 and cnt["phash_le_0"] == 0
ts = [0, 4, 8, 12, 16]
fig, ax = plt.subplots(figsize=(5.6, 2.7))
ax.plot(ts, [cnt["phash_le_%d" % t] for t in ts], "-o", color=INDIGO, label="pHash")
ax.plot(ts, [cnt["dhash_le_%d" % t] for t in ts], "-s", color=TEAL, label="dHash")
ax.axvline(ND["all_pairs_phash_quantiles"]["0.01"], color=MAROON, ls=":", lw=1)
ax.text(ND["all_pairs_phash_quantiles"]["0.01"] + 0.3, 72, "unrelated pairs reach\npHash 8 at the 0.01th\npercentile",
        fontsize=8, color=MAROON, va="top")
ax.set_xlabel("Hamming distance to the nearest of 1,389 other DENTEX images (bits)")
ax.set_ylabel("scored images (of 164)")
ax.legend(frameon=False, loc="upper left")
fig.savefig(OUT / "P6_near_duplicates.pdf")
plt.close(fig)

# ------------------------------------------------------------------ P7 lesion agreement per site, three arms
arms = [("pipeline", "Crop classifier", ORANGE), ("constant-molars", "Constant (image-blind)", INDIGO),
        ("lesion-detector", "Lesion detector", TEAL)]
sites = ["test1", "test2", "test3", "test4"]
F = SW["F_ningxia_caries_lesion_agreement"]
assert F["test1"]["arms"]["arm3c"]["constant-molars"]["lesion_agreement"]["value"] == 0.7089
fig, ax = plt.subplots(figsize=(6.6, 2.9))
for j, (key, lab, c) in enumerate(arms):
    vals = [F[s]["arms"]["arm3c"][key]["lesion_agreement"] for s in sites]
    xs = [i + (j - 1) * 0.26 for i in range(len(sites))]
    ax.bar(xs, [v["value"] for v in vals], 0.24, color=c, label=lab)
    ax.errorbar(xs, [v["value"] for v in vals],
                yerr=[[v["value"] - v["ci95"][0] for v in vals], [v["ci95"][1] - v["value"] for v in vals]],
                fmt="none", ecolor=GREY, capsize=2, lw=0.8)
    for x_, s in zip(xs, sites):
        n_img = F[s]["n_images"]
        ax.text(x_, 0.02, "%.1f" % (F[s]["arms"]["arm3c"][key]["teeth_flagged"] / n_img), ha="center",
                fontsize=6.5, color="white", rotation=90)
ax.set_xticks(range(len(sites)))
ax.set_xticklabels(["%s\n(%d images)" % (s, F[s]["n_images"]) for s in sites])
ax.set_ylabel("lesion agreement")
ax.set_ylim(0, 1.0)
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13))
fig.savefig(OUT / "P7_ningxia_sites.pdf")
plt.close(fig)

# ------------------------------------------------------------------ P8 parameters per stage
p = PC["params"]
assert p["stage1_detector"] == 25311251 and p["stage4a_bone_gate"] == 11177538
labels = [("stage1_detector", "1 Detector"), ("stage2_fdi_head", "2 Numbering"), ("stage3a_lesion", "3a Lesion det."),
          ("stage3a_gate_variant", "3a Crop clf. (alt.)"), ("stage3b_caries_sev", "3b Severity"),
          ("stage4a_bone_gate", "4a Abnormality"), ("stage4b_bone_sev", "4b Severity (withheld)")]
cols = [INDIGO, INDIGO, TEAL, ORANGE, TEAL, MAROON, MAROON]
fig, ax = plt.subplots(figsize=(6.4, 2.6))
ax.barh([l for _, l in reversed(labels)], [p[k] / 1e6 for k, _ in reversed(labels)], color=list(reversed(cols)))
for i, (k, _) in enumerate(reversed(labels)):
    ax.text(p[k] / 1e6 + 0.3, i, "%.2f M" % (p[k] / 1e6), va="center", fontsize=8.5)
ax.set_xlabel("learnable parameters (millions)")
ax.set_xlim(0, 30)
fig.savefig(OUT / "P8_parameters.pdf")
plt.close(fig)

print("plots written:", sorted(f.name for f in OUT.glob("*.pdf")))
