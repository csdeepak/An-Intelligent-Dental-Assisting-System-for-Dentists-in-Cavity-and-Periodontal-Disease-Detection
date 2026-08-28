#!/usr/bin/env python
"""
Paper version of the bone-loss domain-shift figure.

WHY A SEPARATE SCRIPT
---------------------
`make_paper_figures.py:fig_domain_shift` renders a docs-facing variant with an
explanatory caption and a descriptive title burned into the image. Both are correct
there and wrong in a paper, where the LaTeX \\caption carries that text and the
duplication reads as an unedited screenshot.

AND ONE SUBSTANTIVE CORRECTION
------------------------------
That figure reads `outputs/ningxia_external/full/`, which on this machine resolves to
the **superseded bbox detector** run: per-hospital sensitivities 3.7 / 0.8 / 1.5 / 5.4 %.
The pipeline default has been the YOLOv11l-seg detector since 27 Aug 2026, whose run
gives **2.4 / 1.4 / 5.6 / 4.6 %**. A paper figure must show the configuration the paper
describes, so this script reads the seg run explicitly and fails loudly if it is absent
rather than silently falling back to whatever else is on disk.

The conclusion is unchanged either way -- the branch is near-inert out of domain under
both detectors -- but the numbers on the axis must be the ones the text claims.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "outputs/ningxia_external_segdet/ningxia_external.json"
OUT_PAPER = REPO / "paper/fig_boneloss.png"
OUT_DOCS = REPO / "docs/results/figures/paper/05b_bone_loss_domain_shift_paper.png"

TUFTS_MACRO_F1 = 0.9233        # models/03 run_summary, PAPER_MATERIAL 7.3
DENTEX_FIRING = 0.007          # PAPER_MATERIAL 8.13

OK = "#2a9d8f"
BAD = "#c1121f"
INK = "#22333b"


def main():
    if not SRC.exists():
        sys.exit(f"missing {SRC}\nThis figure must be built from the SEG detector run, "
                 f"which is the pipeline default. Refusing to substitute another run.")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    bcs = json.loads(SRC.read_text(encoding="utf-8"))["by_category_split"]
    nx = [(sp, bcs[f"periodontitis/{sp}"]["affected_tooth_sensitivity"])
          for sp in ("test1", "test2", "test3", "test4")
          if f"periodontitis/{sp}" in bcs]
    if len(nx) != 4:
        sys.exit(f"expected 4 external hospitals, found {len(nx)}")

    labels = ["Tufts\n(in-domain,\nmacro-F1)", "DENTEX\n(firing rate)"] + \
             [f"Ningxia {sp}\n(affected-tooth\nsensitivity)" for sp, _ in nx]
    vals = [TUFTS_MACRO_F1, DENTEX_FIRING] + [v for _, v in nx]
    cols = [OK] + [BAD] * (len(vals) - 1)

    fig, ax = plt.subplots(figsize=(9.0, 3.4))
    bars = ax.bar(labels, vals, color=cols, width=0.6, edgecolor="none")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02,
                f"{v:.1%}" if v < 0.5 else f"{v:.3f}",
                ha="center", fontsize=9.5, color=INK, fontweight="600")

    ax.set_ylim(0, 1.06)
    ax.set_ylabel("score / firing rate", fontsize=9.5, color=INK)
    ax.tick_params(labelsize=8.5, colors=INK)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    # No suptitle and no burned-in caption: the LaTeX \caption carries both.

    fig.tight_layout()
    for p in (OUT_PAPER, OUT_DOCS):
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("source:", SRC.relative_to(REPO))
    print("  Tufts in-domain macro-F1 :", TUFTS_MACRO_F1)
    print("  DENTEX firing rate       :", f"{DENTEX_FIRING:.1%}")
    for sp, v in nx:
        print(f"  Ningxia {sp} sensitivity  : {v:.1%}")
    print(f"  external range           : {min(v for _, v in nx):.1%}-{max(v for _, v in nx):.1%}")
    print("->", OUT_PAPER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
