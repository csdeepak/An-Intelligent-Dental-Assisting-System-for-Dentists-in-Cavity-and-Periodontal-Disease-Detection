#!/usr/bin/env python
"""
The paper's key figure: the constant-baseline argument in one image.

WHY THIS IS GENERATED, NOT DRAWN
---------------------------------
Every value is read from the saved evaluation JSONs at render time. A figure with
hand-typed numbers drifts silently the moment any arm is re-run, and a figure that
disagrees with its own results table is the kind of error a reviewer finds and an
author cannot explain.

THREE PANELS, ONE ARGUMENT
---------------------------
(a) Set-prediction F1 -- the constant outscores both VLMs; the pipeline sits above it,
    by an amount that depends on its caries stage (in-domain for the tooth detector).
(b) Lesion localisation -- a second, unrelated metric that demands spatial
    correspondence, with the flag-everything ceiling shown so the reader can see
    that the metric is recall-shaped and what its upper bound costs.
(c) The external cohort -- where the development-set lead does NOT replicate,
    per hospital, because the pooled figure conceals a 31-point swing.

Rebuilt 11 Oct 2026 on the current Stage-1 detector: the pipeline arms are read from
outputs/stage1_switch/ (RESULTS_LOG 2026-10-11g). The constant and the VLMs do not depend
on the detector for panel (a) and are read from outputs/c1_vlm/ as before.

The constant is coloured distinctly in every panel: it is the object of the paper.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs/results/figures/paper/00_baseline_comparison.png"
PAPER = REPO / "paper/fig_baselines.png"

C_CONST = "#e15759"      # the constant -- red, the thing the paper is about. Lighter than the
                         # #c1121f used until 14 Oct 2026, which printed as the same grey as navy.
C_OURS = "#264653"       # our pipeline
C_VLM = "#8d99ae"        # the VLMs
C_CEIL = "#adb5bd"       # degenerate ceiling arm
# The retained gate is drawn in the pipeline's navy, hatched: same system, other caries stage.
# Until 14 Oct 2026 both caries stages were plain navy and swapped order between panels, so the
# bar above the constant in (b) -- the retired gate -- read as the shipped default.
GATE_HATCH = "///"
L_LESION, L_GATE, L_CONST = "Lesion\ndetector\n(default)", "Per-crop\ngate\n(retained)", "Constant\n(image\nnever read)"


def _hatch(bars, rows, k):
    for bar, r in zip(bars, rows):
        if r[k]:
            bar.set_hatch(r[k])
            bar.set_edgecolor("white")
            bar.set_linewidth(0)


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # ---------------------------------------------------------------- panel (a)
    comp = {r["arm"]: r for r in load(REPO / "outputs/c1_vlm/c1_comparison.json")["results"]}
    const = load(REPO / "outputs/c1_vlm/c1_constant_arm_vlm_32b_0shot.json")
    held = next(b for b in const["constant_baselines"] if b["baseline"].startswith("held-out"))
    # Model labels use the RELEASED names (Qwen2.5-VL-32B/7B-Instruct), not the measured
    # parameter counts (33.45 B / 8.29 B). An earlier draft labelled these "33B" and "8B",
    # which names two models that do not exist. Parameter counts belong in the table.
    SW = REPO / "outputs/stage1_switch"
    d = load(SW / "stage1_switch_results.json")["D_fdi_set_f1"]

    def f1(method):                      # from the counts, never from a rounded field
        a = d[method]["arm3c"]
        return 2 * a["tp"] / (2 * a["tp"] + a["fp"] + a["fn"])
    a_rows = [
        (L_LESION, f1("lesion-detector"), C_OURS, None),
        (L_GATE, f1("gate"), C_OURS, GATE_HATCH),
        (L_CONST, held["f1"], C_CONST, None),
        ("Qwen2.5\nVL-32B", comp["vlm_32b_0shot"]["f1"], C_VLM, None),
        ("Qwen2.5\nVL-7B", comp["vlm_7b_0shot_rerun"]["f1"], C_VLM, None),
    ]

    # ---------------------------------------------------------------- panel (b)
    def lesion(tag):
        j = load(SW / f"C_dentex_{tag}_arm3c/lesion_localization.json")
        return j["n_lesions_matched"] / j["n_lesions"], j["n_predicted_positive_teeth"]
    b_const, f_const = lesion("constant-molars")
    b_pipe, f_pipe = lesion("pipeline")
    b_les, f_les = lesion("lesion-detector")
    b_all, f_all = lesion("all-teeth")
    b_rows = [(L_LESION, b_les, f_les, C_OURS, None),
              (L_GATE, b_pipe, f_pipe, C_OURS, GATE_HATCH),
              (L_CONST, b_const, f_const, C_CONST, None),
              ("Flag every tooth\n(ceiling)", b_all, f_all, C_CEIL, None)]
    assert [r[0] for r in a_rows[:3]] == [r[0] for r in b_rows[:3]], \
        "panels (a) and (b) must list the caries stages and the constant in one order"

    # ---------------------------------------------------------------- panel (c)
    def ext(dec):
        return load(SW / f"F_ningxia_caries_{dec}_arm3c/ningxia_external.json")["by_category_split"]
    ep, ec = ext("pipeline"), ext("constant-molars")
    sites = sorted(ep)
    labels = [s.split("/")[-1] for s in sites]
    pipe_v = [ep[s]["lesions_covered"] / ep[s]["lesions"] for s in sites]
    const_v = [ec[s]["lesions_covered"] / ec[s]["lesions"] for s in sites]
    tot_l = sum(ep[s]["lesions"] for s in sites)
    labels.append("pooled")
    pipe_v.append(sum(ep[s]["lesions_covered"] for s in sites) / tot_l)
    const_v.append(sum(ec[s]["lesions_covered"] for s in sites) / tot_l)

    # ---------------------------------------------------------------- draw
    fig, ax = plt.subplots(1, 3, figsize=(13.2, 3.9))

    a = ax[0]
    ys = [r[1] for r in a_rows]
    _hatch(a.bar(range(len(a_rows)), ys, color=[r[2] for r in a_rows], width=0.62), a_rows, 3)
    for i, v in enumerate(ys):
        a.text(i, v + 0.008, f"{v:.3f}", ha="center", fontsize=9,
               fontweight="bold" if a_rows[i][2] == C_CONST else "normal")
    a.set_xticks(range(len(a_rows)))
    a.set_xticklabels([r[0] for r in a_rows], fontsize=7)
    a.set_ylabel("F1 (tooth-level FDI set)")
    a.set_ylim(0, max(ys) * 1.25)
    a.set_title("(a) Set prediction, development data", fontsize=10)

    b = ax[1]
    ys = [r[1] for r in b_rows]
    _hatch(b.bar(range(len(b_rows)), ys, color=[r[3] for r in b_rows], width=0.62), b_rows, 4)
    for i, (lab, v, f, col, hatch) in enumerate(b_rows):
        b.text(i, v + 0.012, f"{v:.3f}", ha="center", fontsize=9,
               fontweight="bold" if col == C_CONST else "normal")
        b.text(i, v / 2, f"{f:,}\nteeth\nflagged", ha="center", va="center",
               fontsize=7.5, color="white" if col == C_OURS else "#1b1b1b",
               bbox=dict(facecolor=col, edgecolor="none", pad=1.5) if hatch else None)
    b.set_xticks(range(len(b_rows)))
    b.set_xticklabels([r[0] for r in b_rows], fontsize=7)
    b.set_ylabel("lesion-localisation agreement")
    b.set_ylim(0, max(ys) * 1.25)
    b.set_title("(b) Localisation, development data", fontsize=10)

    c = ax[2]
    x = range(len(labels))
    w = 0.38
    c.bar([i - w / 2 for i in x], pipe_v, w, label="Per-crop gate (retained)", color=C_OURS,
          hatch=GATE_HATCH, edgecolor="white", linewidth=0)
    c.bar([i + w / 2 for i in x], const_v, w, label="Constant", color=C_CONST)
    c.set_xticks(list(x))
    c.set_xticklabels(labels, fontsize=8)
    c.set_ylabel("lesion agreement")
    c.set_ylim(0, max(max(pipe_v), max(const_v)) * 1.3)
    c.axvline(len(labels) - 1.5, color="grey", lw=0.8, ls=":")
    c.legend(fontsize=8, loc="upper right")
    c.set_title("(c) External cohort, per-crop gate — no replication", fontsize=10)

    for axis in ax:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.25)
        axis.set_axisbelow(True)

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PAPER.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=300, bbox_inches="tight")
    fig.savefig(PAPER, dpi=300, bbox_inches="tight")
    print(f"panel (a) F1     : " + "  ".join(f"{r[0].splitlines()[0]}={r[1]:.3f}" for r in a_rows))
    print(f"panel (b) agree  : const={b_const:.3f} gate={b_pipe:.3f} lesion={b_les:.3f} ceiling={b_all:.3f}")
    print(f"panel (c) pooled : pipe={pipe_v[-1]:.3f} const={const_v[-1]:.3f}")
    print(f"-> {OUT}\n-> {PAPER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
