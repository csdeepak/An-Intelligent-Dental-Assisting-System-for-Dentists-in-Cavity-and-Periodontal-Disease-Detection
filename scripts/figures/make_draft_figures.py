#!/usr/bin/env python
"""
Data figures for the ten-page mentor draft (`paper/ieee/`), written 28 Oct 2026 beside
`make_opg_figures.py`, which renders the radiographs. Nothing here runs a model. Every value is
read from a saved evaluation file, or recomputed from the DENTEX expert labels with the loaders the
evaluation itself used, and each figure asserts that its numbers equal the saved ones before it
draws anything.

  R05_positional_prior.pdf       the caries prior over the 32 FDI positions, and the constant it implies
  R06_architecture.pdf           the six stages as they ship: default checkpoints, crops, thresholds
  R07_paired_differences.pdf     system minus constant, per cohort and per Ningxia site
  R08_numbering_reliability.pdf  numbering outcomes, coverage-accuracy, the gate's reliability
  R_draft_figures_facts.json     every number the figures and their captions quote

    python scripts/figures/make_draft_figures.py
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "eval"))

DENTEX = Path.home() / "Downloads/Capstone/DENTEX/disease"
SWITCH = REPO / "outputs/stage1_switch/stage1_switch_results.json"
RE = REPO / "outputs/stage1_switch/F_ningxia_random_effects.json"
TAXO = REPO / "outputs/stage1_switch/I_taxonomy_arm3c/stage2_failure_taxonomy.json"
COVER = REPO / "outputs/stage1_switch/J_coverage_arm3c/c4_coverage_accuracy.json"
ROWS = REPO / "outputs/stage1_switch/B_dentex_arm3c/stage2_rows_head.json"
CALIB = REPO / "outputs/calibration/caries_gate_calibration_test.json"
ISO = REPO / "outputs/calibration/caries_gate_isotonic.json"
OUT = REPO / "paper/ieee/figures"

CONSTANT = {"16", "17", "26", "27", "36", "37", "46", "47"}
# Okabe-Ito, as in make_opg_figures.py.
C_FIT, C_SCORED, C_CONST = "#999999", "#E69F00", "#CC79A7"
C_GATE, C_LESION, C_NUM = "#E69F00", "#0072B2", "#009E73"
UPPER = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
LOWER = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]

facts = {}


def close(a, b, tol=6e-4):
    return abs(a - b) <= tol


# ---------------------------------------------------------------- R05: the positional prior
def micro_f1(gt, const):
    tp = sum(len(g & const) for g in gt.values())
    return 2 * tp / (len(const) * len(gt) + sum(len(g) for g in gt.values()))


def fig_prior(plt):
    from c1_constant_baseline import best_constant, score_sets
    from c1_vlm_baseline import load_exemplars, load_gt

    scored = load_gt(DENTEX)
    fit = {s: set(c) for s, c in load_exemplars(DENTEX, 10_000)}
    assert len(scored) == 164 and sum(map(len, scored.values())) == 477
    assert len(fit) == 78 and not set(fit) & set(scored)

    const, fit_f1 = best_constant(fit)
    assert const == CONSTANT and close(fit_f1, 0.392, 5e-4), (const, fit_f1)
    r = score_sets(scored, {k: const for k in scored})
    assert (r["tp"], r["fp"], r["fn"], r["f1"]) == (286, 1026, 191, 0.3197), r
    oracle, oracle_f1 = best_constant(scored)
    assert oracle == {"16", "26", "36", "37", "46", "47"} and close(oracle_f1, 0.3299)
    # The closed form F1 = 2 TP / (|S| N + P) is the scorer's own micro-F1, not an approximation.
    assert close(micro_f1(scored, const), 0.3197) and close(micro_f1(fit, const), fit_f1)

    def prev(gt):
        return {c: sum(c in g for g in gt.values()) / len(gt) for c in map(str, UPPER + LOWER)}

    p_fit, p_sc = prev(fit), prev(scored)
    order = sorted(p_fit, key=lambda c: -p_fit[c])
    # Adding code c to a constant S raises F1 iff p_c > F1(S)/2 (derivation in the paper, Sec. III).
    # The greedy search therefore takes codes in order of prevalence and stops at the first that
    # fails the test; check that rule reproduces the fitted constant exactly.
    S, f = set(), 0.0
    for c in order:
        if p_fit[c] <= f / 2:
            break
        S.add(c); f = micro_f1(fit, S)
    assert S == CONSTANT and close(f, fit_f1)
    k_fit = [micro_f1(fit, set(order[:k])) for k in range(1, 17)]
    k_sc = [micro_f1(scored, set(order[:k])) for k in range(1, 17)]
    facts["prior"] = {
        "n_fit_images": 78, "n_scored_images": 164, "scored_positives": 477,
        "fit_f1": round(fit_f1, 4), "half_fit_f1": round(fit_f1 / 2, 4),
        "scored": r, "oracle_codes": sorted(oracle), "oracle_f1": round(oracle_f1, 4),
        "prevalence_fit": {c: round(p_fit[c], 4) for c in order},
        "prevalence_scored": {c: round(p_sc[c], 4) for c in order},
        "ninth_code_fit": order[8], "ninth_prevalence_fit": round(p_fit[order[8]], 4),
        "lowest_constant_prevalence_fit": round(min(p_fit[c] for c in CONSTANT), 4),
        "constant_mass_scored": round(sum(p_sc[c] for c in CONSTANT) /
                                      sum(p_sc.values()), 4),
        "topk_f1_fit": [round(x, 4) for x in k_fit],
        "topk_f1_scored": [round(x, 4) for x in k_sc],
    }

    fig = plt.figure(figsize=(7.16, 2.15))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.55, 1], hspace=0.62, wspace=0.17,
                          left=0.055, right=0.99, top=0.9, bottom=0.17)
    for row, (codes, name) in enumerate(((UPPER, "upper arch"), (LOWER, "lower arch"))):
        ax = fig.add_subplot(gs[row, 0])
        x = range(len(codes))
        ax.bar([i - 0.2 for i in x], [p_fit[str(c)] for c in codes], 0.4, color=C_FIT,
               label="fit set (78 excluded images)")
        ax.bar([i + 0.2 for i in x], [p_sc[str(c)] for c in codes], 0.4, color=C_SCORED,
               label="scored set (164 images)")
        ax.axhline(fit_f1 / 2, color="black", lw=0.7, ls="--")
        ax.set_xticks(list(x)); ax.set_xticklabels([str(c) for c in codes], fontsize=6)
        for t, c in zip(ax.get_xticklabels(), codes):
            if str(c) in CONSTANT:
                t.set_color(C_CONST); t.set_fontweight("bold")
        ax.axvline(7.5, color="0.6", lw=0.6)
        ax.set_ylim(0, 0.62); ax.set_yticks([0, 0.2, 0.4, 0.6])
        ax.tick_params(labelsize=6, length=2)
        ax.set_ylabel("share of images", fontsize=6)
        ax.text(0.003, 0.97, f"{name}: patient's right | left", transform=ax.transAxes,
                fontsize=6, va="top")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        if row == 0:
            ax.set_title("(a) Share of images in which each FDI tooth carries expert-marked caries",
                         fontsize=6.8, loc="left", pad=2)
            ax.text(15.6, fit_f1 / 2 + 0.015, f"F1/2 = {fit_f1 / 2:.3f}", fontsize=5.5,
                    ha="right", va="bottom")
            ax.legend(fontsize=5.5, frameon=False, loc="upper center", ncol=2,
                      bbox_to_anchor=(0.62, 1.04))
    ax = fig.add_subplot(gs[:, 1])
    ks = range(1, 17)
    ax.plot(ks, k_fit, "-o", ms=2.2, lw=0.9, color=C_FIT, label="fit set")
    ax.plot(ks, k_sc, "-o", ms=2.2, lw=0.9, color=C_SCORED, label="scored set")
    ax.axvline(8, color=C_CONST, lw=0.8, ls="--")
    ax.annotate(f"k = 8: {fit_f1:.3f} fit,\n{r['f1']:.3f} scored", (8, k_sc[7]),
                xytext=(9.3, 0.215), fontsize=5.5,
                arrowprops=dict(arrowstyle="-", lw=0.5, color="0.3"))
    ax.set_xlabel("k most prevalent codes (fit order)", fontsize=6)
    ax.set_ylabel("FDI-set F1 of the constant", fontsize=6)
    ax.set_ylim(0.10, 0.42); ax.set_xticks([1, 4, 8, 12, 16])
    ax.tick_params(labelsize=6, length=2)
    ax.legend(fontsize=5.5, frameon=False, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("(b) F1 of the top-k constant", fontsize=6.8, loc="left", pad=2)
    fig.savefig(OUT / "R05_positional_prior.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- R06: architecture
def fig_architecture(plt):
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig = plt.figure(figsize=(7.16, 2.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(-2.2, 36); ax.axis("off")

    def box(x, y, w, h, head, body, colour, dashed=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8",
                                    fc="white", ec=colour, lw=1.1, ls="--" if dashed else "-"))
        ax.add_patch(FancyBboxPatch((x, y + h - 0.35), w, 0.35, boxstyle="square,pad=0",
                                    fc=colour, ec="none"))
        ax.text(x + 0.8, y + h - 1.1, head, fontsize=6.3, fontweight="bold", va="top")
        ax.text(x + 0.8, y + h - 3.6, body, fontsize=5.6, va="top", linespacing=1.25)

    def arrow(a, b, style="-|>", **kw):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=7, lw=0.8,
                                     color="0.25", shrinkA=0, shrinkB=0, **kw))

    ink, cari, abn, fuse = "#56B4E9", C_LESION, C_NUM, "0.45"
    box(0.8, 22, 14, 12.5, "Input", "panoramic radiograph\n(OPG), any size;\nFig. 4: 2,829 ×\n1,316 pixels", "0.6")
    box(18, 22, 23.5, 12.5, "Stage 1: tooth detection",
        "YOLOv11l, 25.31 M parameters\n1,024 px input, conf. 0.25,\nNMS IoU 0.50; trained on Tufts,\n"
        "DENTEX enumeration and a\nthird corpus in equal shares", ink)
    box(44.5, 22, 24.5, 12.5, "Stage 2: FDI numbering",
        "ResNet18 + 4 box-position features,\n11.19 M; crop 1.5 × the tooth box\n"
        "→ a score for each of 32 codes;\nHungarian assignment gives one\ncode per tooth, none used twice", ink)
    box(72, 22, 27.2, 12.5, "Stages 5–6: fusion and report",
        "findings joined on the FDI code;\ntooth 'assessable' only if numbering\nconfidence ≥ 0.30 (fixed in code)\n"
        "→ per-tooth JSON record (Sec. IV)\n→ overlay image (Fig. 4f)", fuse)
    box(0.8, 3.5, 26, 14.8, "Stage 3a (default): lesion detector",
        "YOLOv11l, 25.31 M, whole image at\n1,024 px; conf. 0.25 fixed before\n"
        "training; 4,800 CariesXrays + 650\nDENTEX images at equal weight;\n"
        "lesion box → tooth that contains most", cari)
    box(29.5, 3.5, 20.5, 14.8, "Stage 3a (retained variant)",
        "per-crop caries classifier,\nResNet18, 11.18 M\ntight tooth crop → P(caries);\n"
        "the comparison arm\nthroughout the paper", C_GATE, dashed=True)
    box(53, 3.5, 17.5, 14.8, "Stage 3b: severity",
        "ResNet18, 11.18 M,\ntight crop of each\nflagged tooth →\ncaries or deep caries", cari)
    box(74.2, 3.5, 25, 14.8, "Stage 4: abnormality flag",
        "4a: ResNet18, 11.18 M; crop 1.5 ×\nwide, 2.0 × tall; Tufts, split by\n"
        "radiograph; label = crop overlaps\nan expert abnormality mask;\n"
        "4b severity withheld by default", abn)
    arrow((15.1, 28.2), (17.7, 28.2)); arrow((41.8, 28.2), (44.2, 28.2)); arrow((69.3, 28.2), (71.7, 28.2))
    arrow((7.5, 21.7), (7.5, 18.6))                       # input image -> lesion detector
    arrow((29.7, 21.7), (29.7, 20.2), style="-")          # tooth boxes bus
    arrow((22, 20.2), (87, 20.2), style="-")
    for x in (22, 39.7, 87):
        arrow((x, 20.2), (x, 18.6))
    ax.text(31, 20.6, "tooth boxes", fontsize=5.3, color="0.3")
    arrow((13.8, 3.2), (13.8, 1.2), style="-"); arrow((13.8, 1.2), (61.75, 1.2), style="-")
    arrow((39.7, 3.2), (39.7, 1.2), style="-", ls="--")
    arrow((61.75, 1.2), (61.75, 3.2))
    ax.text(42, -1.4, "flagged teeth (from whichever Stage 3a runs)", fontsize=5.3, color="0.3")
    arrow((66, 18.6), (75.5, 21.7))                       # severity -> fusion
    arrow((95, 18.6), (95, 21.7))                         # stage 4 -> fusion
    fig.savefig(OUT / "R06_architecture.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- R07: paired differences
def fig_forest(plt):
    sw = json.loads(SWITCH.read_text(encoding="utf-8"))
    re_ = json.loads(RE.read_text(encoding="utf-8"))

    def d(sec, key, site="pooled"):
        node = sw[sec][site] if site != "pooled" else sw[sec]["pooled"]
        v = node["deltas"][key]
        return v["delta_pp"], v["ci95_pp"]

    G, L = "arm3c: pipeline_minus_constant-molars", "arm3c: lesion-detector_minus_constant-molars"
    cohorts = [("DENTEX (development)", "C_dentex_lesion_agreement"),
               ("CariesXrays (lesion det. val.)", "E_cariesxrays_lesion_agreement"),
               ("Ningxia, 4 sites (external)", "F_ningxia_caries_lesion_agreement")]
    rows_a = [(n, d(s, G), d(s, L)) for n, s in cohorts]
    assert rows_a[2][2] == (9.28, [4.72, 13.73]) and rows_a[1][1][0] == -22.42
    F = "F_ningxia_caries_lesion_agreement"
    sites = []
    for t in ("test1", "test2", "test3", "test4"):
        a = sw[F][t]["arms"]["arm3c"]["lesion-detector"]
        sites.append((f"{t} ({sw[F][t]['n_images']} img, {a['lesions']} les.)", d(F, G, t), d(F, L, t)))
        assert d(F, L, t) == (re_["per_site"][t]["delta_pp"], re_["per_site"][t]["ci95_pp"])
    facts["paired"] = {"cohorts": rows_a, "sites": sites,
                       "random_effects": {k: re_[k] for k in ("mean_pp", "ci95_pp",
                                                              "prediction_interval_pp", "i2_pct",
                                                              "tau_pp", "q", "q_p", "k")}}

    fig, axes = plt.subplots(2, 1, figsize=(3.45, 3.55), gridspec_kw=dict(height_ratios=[3, 6.6]))
    fig.subplots_adjust(left=0.40, right=0.97, top=0.94, bottom=0.12, hspace=0.42)

    def draw(ax, rows, extra=()):
        n = len(rows) + len(extra)
        for i, (name, g, l) in enumerate(rows):
            y = n - 1 - i
            for (v, (lo, hi)), off, col, mk in ((g, +0.14, C_GATE, "s"), (l, -0.14, C_LESION, "o")):
                ax.plot([lo, hi], [y + off] * 2, color=col, lw=1.1)
                ax.plot(v, y + off, mk, color=col, ms=3.2)
        names = [r[0] for r in rows] + [e[0] for e in extra]
        ax.set_yticks(range(n)); ax.set_yticklabels(names[::-1], fontsize=5.6)
        ax.axvline(0, color="black", lw=0.6)
        ax.set_xlim(-30, 30); ax.tick_params(labelsize=5.8, length=2)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    draw(axes[0], rows_a)
    axes[0].set_title("(a) Three cohorts", fontsize=6.6, loc="left", pad=2)
    pooled = ("pooled, sites fixed", d(F, G), d(F, L))
    extra = [("random effects (lesion det.)",)]
    draw(axes[1], sites + [pooled], extra)
    m, (lo, hi), (plo, phi) = re_["mean_pp"], re_["ci95_pp"], re_["prediction_interval_pp"]
    ax = axes[1]
    ax.annotate("", xy=(30, -0.14), xytext=(-30, -0.14),
                arrowprops=dict(arrowstyle="<->", lw=0.6, color=C_LESION, ls=":"))
    ax.plot([lo, hi], [0, 0], color=C_LESION, lw=2.2)
    ax.plot(m, 0, "D", color="white", mec=C_LESION, ms=3.6)
    ax.text(29.5, 0.3, f"prediction interval [{plo:.0f}, {phi:.0f}]", fontsize=5, ha="right",
            color=C_LESION)
    ax.axhline(0.55, color="0.75", lw=0.5)
    ax.set_title(f"(b) Ningxia per site; I$^2$ = {re_['i2_pct']:.0f}%", fontsize=6.6,
                 loc="left", pad=2)
    ax.set_xlabel("lesion agreement, system minus constant (points)", fontsize=6)
    h = [plt.Line2D([], [], color=C_GATE, marker="s", ms=3, lw=1.1),
         plt.Line2D([], [], color=C_LESION, marker="o", ms=3, lw=1.1)]
    fig.legend(h, ["crop classifier − constant", "lesion detector − constant"], fontsize=5.6,
               frameon=False, loc="lower center", ncol=2, bbox_to_anchor=(0.6, -0.01))
    fig.savefig(OUT / "R07_paired_differences.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- R08: numbering and reliability
def fig_reliability(plt):
    tx = json.loads(TAXO.read_text(encoding="utf-8"))
    cov = json.loads(COVER.read_text(encoding="utf-8"))
    rows = json.loads(ROWS.read_text(encoding="utf-8"))
    cal = json.loads(CALIB.read_text(encoding="utf-8"))
    iso = json.loads(ISO.read_text(encoding="utf-8"))

    cat = tx["categories"]
    assert sum(cat.values()) == 936 and cat["correct"] == 869 and cat["off_by_one"] == 51
    det = [r for r in rows if r["detected"]]
    assert len(rows) == 936 and len(det) == 932
    det.sort(key=lambda r: -r["confidence"])
    ok = [int(r["pred_fdi"] == r["gt_fdi"]) for r in det]
    run, curve = 0, []
    for i, o in enumerate(ok, 1):
        run += o; curve.append((i / len(ok), run / i))
    s2 = cov["stage2"]
    assert close(curve[-1][1], s2["accuracy_full_coverage"], 1e-4)
    assert close(curve[s2["at_75"]["n_retained"] - 1][1], s2["at_75"]["accuracy"], 1e-3)
    kept = [o for r, o in zip(det, ok) if r["confidence"] >= 0.30]
    op = (len(kept) / len(det), sum(kept) / len(kept))
    assert close(op[0], s2["operating_point"]["coverage"], 1e-4) and close(op[1], s2["operating_point"]["accuracy"], 1e-4)
    gate = cov["caries_gate"]
    gpts = [(gate[k]["coverage"], gate[k]["accuracy"]) for k in ("at_50", "at_75", "at_90")] + \
           [(1.0, gate["accuracy_full_coverage"])]
    pos = {}
    for p, c in tx["by_position"].items():
        n_det = sum(v for k, v in c.items() if k != "not_detected")
        pos[int(p)] = (n_det - c.get("correct", 0)) / n_det
    facts["numbering"] = {"categories": cat, "wrong_rate_by_position": {k: round(v, 4) for k, v in sorted(pos.items())},
                          "operating_point": [round(op[0], 4), round(op[1], 4)],
                          "gate_points": gpts, "ece_raw_iso": iso["test"]["ece"],
                          "ap_raw_iso": iso["test"]["average_precision"],
                          "flipped": iso["verdicts_flipped_at_0.5"]}

    fig, ax = plt.subplots(1, 4, figsize=(7.16, 1.95), gridspec_kw=dict(width_ratios=[1.15, 0.9, 1.05, 1.0]))
    fig.subplots_adjust(left=0.105, right=0.985, top=0.86, bottom=0.22, wspace=0.45)
    names = [("correct", "correct"), ("off_by_one", "adjacent"), ("same_quadrant_far", "same quad., far"),
             ("wrong_arch", "wrong arch"), ("mirror_lr", "L-R mirror"), ("other", "other"),
             ("not_detected", "not detected")]
    vals = [cat[k] for k, _ in names]
    a = ax[0]
    a.barh(range(len(vals))[::-1], vals, color=[C_NUM] + ["#D55E00"] * 5 + ["0.6"], height=0.7)
    a.set_xscale("log"); a.set_xlim(1, 2500)
    a.set_yticks(range(len(vals))[::-1]); a.set_yticklabels([n for _, n in names], fontsize=5.6)
    for i, v in enumerate(vals):
        a.text(v * 1.15, len(vals) - 1 - i, str(v), fontsize=5.5, va="center")
    a.set_xlabel("teeth (log scale), n = 936", fontsize=6)
    a.set_title("(a) Numbering outcome per tooth", fontsize=6.6, loc="left", pad=2)
    a = ax[1]
    a.bar(list(pos), [100 * pos[k] for k in sorted(pos)], color="#D55E00", width=0.7)
    a.set_xticks(range(1, 9)); a.set_xlabel("position (1 incisor ... 8 third molar)", fontsize=6)
    a.set_ylabel("% of detected teeth\ngiven a wrong code", fontsize=6)
    a.set_title("(b) Errors by position", fontsize=6.6, loc="left", pad=2)
    a = ax[2]
    a.plot([100 * c for c, _ in curve], [100 * v for _, v in curve], color=C_NUM, lw=1.0,
           label="numbering (932 teeth)")
    a.plot([100 * c for c, _ in gpts], [100 * v for _, v in gpts], ":s", color=C_GATE, ms=2.6,
           lw=0.9, label="crop classifier (863 crops)")
    a.plot(100 * op[0], 100 * op[1], "o", mfc="white", mec="black", ms=3.4)
    a.annotate("threshold 0.30", (100 * op[0], 100 * op[1]), xytext=(42, 86), fontsize=5.3,
               arrowprops=dict(arrowstyle="-", lw=0.5, color="0.3"))
    a.set_xlim(0, 101); a.set_ylim(78, 101)
    a.set_xlabel("coverage (% of items answered)", fontsize=6)
    a.set_ylabel("accuracy on answered (%)", fontsize=6)
    a.legend(fontsize=5.2, frameon=False, loc="lower left")
    a.set_title("(c) Selective prediction", fontsize=6.6, loc="left", pad=2)
    a = ax[3]
    rel = [b for b in cal["reliability"] if b["n"]]
    a.plot([0, 1], [0, 1], color="0.6", lw=0.6, ls="--")
    a.plot([b["mean_pred"] for b in rel], [b["observed"] for b in rel], "-", color=C_GATE, lw=0.8)
    a.scatter([b["mean_pred"] for b in rel], [b["observed"] for b in rel],
              s=[3 + b["n"] / 6 for b in rel], color=C_GATE, zorder=3)
    a.text(0.03, 0.95, f"ECE {iso['test']['ece'][0]:.3f} raw\n{iso['test']['ece'][1]:.3f} isotonic",
           fontsize=5.4, va="top", transform=a.transAxes)
    a.set_xlim(0, 1); a.set_ylim(0, 1); a.set_xticks([0, 0.5, 1]); a.set_yticks([0, 0.5, 1])
    a.set_xlabel("stated P(caries)", fontsize=6); a.set_ylabel("observed share carious", fontsize=6)
    a.set_title("(d) Crop classifier reliability", fontsize=6.6, loc="left", pad=2)
    for a in ax:
        a.tick_params(labelsize=5.8, length=2)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    fig.savefig(OUT / "R08_numbering_reliability.pdf")
    plt.close(fig)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
    fig_prior(plt)
    fig_architecture(plt)
    fig_forest(plt)
    fig_reliability(plt)
    (OUT / "R_draft_figures_facts.json").write_text(json.dumps(facts, indent=1) + "\n",
                                                    encoding="utf-8")
    print("wrote R05-R08 and R_draft_figures_facts.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
