#!/usr/bin/env python
"""
Paper figure for Stage 4a as it ships: the held-out Tufts test split, three training runs.

Replaces `make_boneloss_paper_figure.py` in the manuscript (14 Oct 2026, RESULTS_LOG 2026-10-14).
That figure set the previous model's 0.923 -- a crop-level split with radiograph leakage -- in a
"success" colour beside "failure" bars from other cohorts and metrics. It and its script are kept,
unchanged, for the record.

What this one shows, from `outputs/bone_loss_eval/v2_retrain/test_summary.json` only:
sensitivity and specificity of the three runs of the radiograph-split recipe on 143 test
radiographs, each with its radiograph-cluster bootstrap interval, beside the previous model on
the 125 of those radiographs it had not trained on. One neutral ink for every run: no colour
says good or bad. Every count is asserted against the manuscript's before anything is drawn.
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "outputs/bone_loss_eval/v2_retrain/test_summary.json"
OUT_PAPER = REPO / "paper/fig_stage4a.png"
OUT_DOCS = REPO / "docs/results/figures/paper/07_stage4a_heldout.png"

INK, PREV = "#22333b", "#8d99ae"


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ts = json.loads(SRC.read_text(encoding="utf-8"))
    rows = [(f"seed\n{s}" + ("\n(default)" if s == 42 else ""), ts[f"seed_{s}"]["all"], INK)
            for s in (42, 43, 44)]
    rows.append(("first\nmodel$^{*}$", ts["shipped"]["unseen_by_shipped"], PREV))

    # The counts the manuscript states (Section sec:stage4); a changed artefact stops here.
    tp = [r[1]["confusion"]["tp"] for r in rows]
    pos = [r[1]["positive_teeth"] for r in rows]
    assert tp == [50, 30, 20, 6] and pos == [182, 182, 182, 175], (tp, pos)
    assert [r[1]["radiographs"] for r in rows] == [143, 143, 143, 125]

    fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.95))
    for ax, key, title, lim in ((axes[0], "sensitivity", "(a) Sensitivity", (0, 45)),
                                (axes[1], "specificity", "(b) Specificity", (94, 100))):
        for i, (_, m, col) in enumerate(rows):
            v, (lo, hi) = m[key]["value"] * 100, [x * 100 for x in m[key]["ci95"]]
            ax.errorbar(i, v, yerr=[[v - lo], [hi - v]], fmt="o", color=col, ms=3.5,
                        elinewidth=1, capsize=2)
            ax.annotate(f"{v:.1f}", (i, hi), textcoords="offset points", xytext=(0, 2),
                        ha="center", fontsize=5.5, color=col)
        ax.set_xticks(range(len(rows)))
        ax.set_xticklabels([r[0] for r in rows], fontsize=5.5)
        ax.set_xlim(-0.6, len(rows) - 0.4)
        ax.set_ylim(*lim)
        ax.set_ylabel(f"{key} (%)", fontsize=6.5)
        ax.tick_params(axis="y", labelsize=6)
        ax.set_title(title, fontsize=7)
        ax.axvline(2.5, color="grey", lw=0.6, ls=":")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
    fig.text(0.01, 0.005, "$^{*}$ on the 125 test radiographs it had not trained on",
             fontsize=5, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1), w_pad=1.2)
    for p in (OUT_PAPER, OUT_DOCS):
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=300, bbox_inches="tight")
        print(f"-> {p.relative_to(REPO)}")
    for label, m, _ in rows:
        print(f"  {label.replace(chr(10), ' '):24s} sens {m['sensitivity']['value']:.4f} "
              f"spec {m['specificity']['value']:.4f}")


if __name__ == "__main__":
    main()
