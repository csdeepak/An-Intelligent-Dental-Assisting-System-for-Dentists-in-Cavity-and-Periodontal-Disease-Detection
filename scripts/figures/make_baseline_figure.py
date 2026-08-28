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
(a) Set-prediction F1 -- the ordering is inverted with respect to information given.
(b) Lesion localisation -- a second, unrelated metric that demands spatial
    correspondence, with the flag-everything ceiling shown so the reader can see
    that the metric is recall-shaped and what its upper bound costs.
(c) The external cohort -- where the development-set result does NOT replicate,
    per hospital, because the pooled figure conceals a 26-point swing.

The constant is coloured distinctly in every panel: it is the object of the paper.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs/results/figures/paper/00_baseline_comparison.png"
PAPER = REPO / "paper/fig_baselines.png"

C_CONST = "#c1121f"      # the constant -- red, the thing the paper is about
C_OURS = "#264653"       # our pipeline
C_VLM = "#8d99ae"        # the VLMs
C_CEIL = "#adb5bd"       # degenerate ceiling arm


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
    a_rows = [
        ("Constant\n(image never read)", held["f1"], C_CONST),
        ("Our pipeline", comp["pipeline"]["f1"], C_OURS),
        ("Qwen2.5-VL-33B", comp["vlm_32b_0shot"]["f1"], C_VLM),
        ("Qwen2.5-VL-8B", comp["vlm_7b_0shot_rerun"]["f1"], C_VLM),
    ]

    # ---------------------------------------------------------------- panel (b)
    def lesion(tag):
        j = load(REPO / f"outputs/lesion_loc_{tag}/lesion_localization.json")
        return j["lesion_localization_agreement"], j["n_predicted_positive_teeth"]
    b_const, f_const = lesion("constant-molars")
    b_pipe, f_pipe = lesion("pipeline")
    b_all, f_all = lesion("all-teeth")
    b_rows = [("Constant", b_const, f_const, C_CONST),
              ("Our pipeline", b_pipe, f_pipe, C_OURS),
              ("Flag every tooth\n(ceiling)", b_all, f_all, C_CEIL)]

    # ---------------------------------------------------------------- panel (c)
    def ext(d):
        return load(REPO / f"outputs/{d}/ningxia_external.json")["by_category_split"]
    ep, ec = ext("ningxia_pipeline"), ext("ningxia_constant-molars")
    sites = sorted(ep)
    labels = [s.split("/")[-1] for s in sites]
    pipe_v = [ep[s]["lesion_agreement_covered"] for s in sites]
    const_v = [ec[s]["lesion_agreement_covered"] for s in sites]
    tot_l = sum(ep[s]["lesions"] for s in sites)
    labels.append("pooled")
    pipe_v.append(sum(ep[s]["lesions_covered"] for s in sites) / tot_l)
    const_v.append(sum(ec[s]["lesions_covered"] for s in sites) / tot_l)

    # ---------------------------------------------------------------- draw
    fig, ax = plt.subplots(1, 3, figsize=(13.2, 3.9))

    a = ax[0]
    ys = [r[1] for r in a_rows]
    a.bar(range(len(a_rows)), ys, color=[r[2] for r in a_rows], width=0.62)
    for i, v in enumerate(ys):
        a.text(i, v + 0.008, f"{v:.3f}", ha="center", fontsize=9,
               fontweight="bold" if i == 0 else "normal")
    a.set_xticks(range(len(a_rows)))
    a.set_xticklabels([r[0] for r in a_rows], fontsize=8)
    a.set_ylabel("F1 (tooth-level FDI set)")
    a.set_ylim(0, max(ys) * 1.25)
    a.set_title("(a) Set prediction, development data", fontsize=10)

    b = ax[1]
    ys = [r[1] for r in b_rows]
    b.bar(range(len(b_rows)), ys, color=[r[3] for r in b_rows], width=0.62)
    for i, (lab, v, f, _) in enumerate(b_rows):
        b.text(i, v + 0.012, f"{v:.3f}", ha="center", fontsize=9,
               fontweight="bold" if i == 0 else "normal")
        b.text(i, v / 2, f"{f:,}\nteeth flagged", ha="center", va="center",
               fontsize=7.5, color="white")
    b.set_xticks(range(len(b_rows)))
    b.set_xticklabels([r[0] for r in b_rows], fontsize=8)
    b.set_ylabel("lesion-localisation agreement")
    b.set_ylim(0, max(ys) * 1.25)
    b.set_title("(b) Localisation, development data", fontsize=10)

    c = ax[2]
    x = range(len(labels))
    w = 0.38
    c.bar([i - w / 2 for i in x], pipe_v, w, label="Our pipeline", color=C_OURS)
    c.bar([i + w / 2 for i in x], const_v, w, label="Constant", color=C_CONST)
    c.set_xticks(list(x))
    c.set_xticklabels(labels, fontsize=8)
    c.set_ylabel("lesion agreement")
    c.set_ylim(0, max(max(pipe_v), max(const_v)) * 1.3)
    c.axvline(len(labels) - 1.5, color="grey", lw=0.8, ls=":")
    c.legend(fontsize=8, loc="upper right")
    c.set_title("(c) External cohort — no replication", fontsize=10)

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
    print(f"panel (b) agree  : const={b_const:.3f} pipe={b_pipe:.3f} ceiling={b_all:.3f}")
    print(f"panel (c) pooled : pipe={pipe_v[-1]:.3f} const={const_v[-1]:.3f}")
    print(f"-> {OUT}\n-> {PAPER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
