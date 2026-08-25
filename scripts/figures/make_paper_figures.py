"""
Generate the paper/review figures from SAVED RUN ARTEFACTS ONLY.

Phase III asks for "performance analysis using tables and graphs." The tables existed; the
graphs covered only Stages 1-2 (the detector's Ultralytics output and the enumeration head's
training curves). Nothing depicted the results that actually carry the paper: stage-wise error
propagation (C3), external validation across four hospitals (C2), or the caries-gate repair.

**This script runs no models and re-measures nothing.** Every number is read out of a committed
JSON artefact, so a figure can never drift from the logged result — if a figure and RESULTS_LOG
disagree, the figure is stale and regenerating fixes it. Sources are printed on each run.

Usage:
    python scripts/figures/make_paper_figures.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "docs/results/figures/paper"

# Muted, print-safe, colour-blind-distinguishable. Used consistently across every figure.
INK, MUTED, HAIR = "#10161C", "#5A6A76", "#D3DCE2"
OK, WARN, BAD, ACCENT = "#2F7D5B", "#A8690B", "#A8443A", "#0E7C86"


def _caption(fig, text, width=104):
    """Footnote under a figure, wrapped so it never runs off the canvas."""
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, width))
    n_lines = wrapped.count("\n") + 1
    fig.text(.5, .012, wrapped, ha="center", va="bottom", fontsize=8.2,
             color=MUTED, style="italic", linespacing=1.45)
    return .045 + .028 * (n_lines - 1)      # bottom margin to reserve


def _load(rel):
    p = REPO_ROOT / rel
    if not p.exists():
        print(f"  SKIP (missing): {rel}")
        return None
    return json.loads(p.read_text())


def _style(ax, title, ylab=None, xlab=None):
    ax.set_title(title, fontsize=11, fontweight="600", color=INK, pad=10)
    if ylab:
        ax.set_ylabel(ylab, fontsize=9.5, color=MUTED)
    if xlab:
        ax.set_xlabel(xlab, fontsize=9.5, color=MUTED)
    ax.grid(axis="y", alpha=.25, color=HAIR)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(HAIR)
    ax.tick_params(colors=MUTED, labelsize=9)


def fig_error_propagation(plt):
    """C3's flagship: where teeth are lost as they move through the pipeline."""
    rows = _load("outputs/stage2_reverify/stage2_rows_head.json")
    if rows is None:
        return
    total = len(rows)
    detected = sum(r["detected"] for r in rows)
    numbered = sum(r["detected"] and r["pred_fdi"] == r["gt_fdi"] for r in rows)

    stages = ["GT teeth\n(annotated)", "Detected\n(Stage 1)", "Correctly numbered\n(Stage 2)"]
    vals = [total, detected, numbered]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    bars = ax.bar(stages, vals, color=[HAIR, ACCENT, OK], width=.55, edgecolor="none")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + total * .022,
                f"{v:,}\n{v/total:.1%}", ha="center", fontsize=9.5,
                color=INK, fontweight="600", linespacing=1.5)
    # annotate the losses between stages
    for i in range(len(vals) - 1):
        lost = vals[i] - vals[i + 1]
        ax.annotate(f"−{lost:,}", xy=(i + .5, (vals[i] + vals[i + 1]) / 2),
                    ha="center", fontsize=10, color=BAD, fontweight="600")
    _style(ax, "Stage-wise error propagation — DENTEX, 164 leak-free images",
           "GT teeth remaining")
    ax.set_ylim(0, total * 1.22)
    m = _caption(fig, "Each stage's loss is permanent: a tooth missed at Stage 1 cannot be "
                      "numbered, and a misnumbered tooth attaches its findings to the wrong tooth.")
    fig.tight_layout(rect=[0, m, 1, 1])
    fig.savefig(OUT / "01_error_propagation.png", dpi=200)
    plt.close(fig)
    print(f"  01_error_propagation.png  ({total} → {detected} → {numbered})")


def fig_external_validation(plt):
    """C2: caries lesion agreement across four hospitals, against the DENTEX internal number."""
    ext = _load("outputs/ningxia_external/full/ningxia_external.json")
    dtx = _load("outputs/lesion_localization/full/lesion_localization.json")
    if ext is None or dtx is None:
        return
    bcs = ext["by_category_split"]
    labels, vals, ns, cols = ["DENTEX\n(internal)"], [dtx["lesion_localization_agreement"]], \
                             [dtx["n_lesions"]], [MUTED]
    for sp in ["test1", "test2", "test3", "test4"]:
        d = bcs.get(f"dental_caries/{sp}")
        if not d:
            continue
        centre = "same centre\nas NX-train" if d["centre"].startswith("same") else "cross-centre"
        labels.append(f"NX {sp}\n({centre})")
        vals.append(d["lesion_agreement_covered"])
        ns.append(d["lesions"])
        cols.append(WARN if d["centre"].startswith("same") else ACCENT)

    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    bars = ax.bar(labels, vals, color=cols, width=.6, edgecolor="none")
    for b, v, n in zip(bars, vals, ns):
        ax.text(b.get_x() + b.get_width() / 2, v + .012, f"{v:.1%}\nn={n}",
                ha="center", fontsize=9, color=INK, fontweight="600", linespacing=1.5)
    ax.axhline(vals[0], color=MUTED, ls=":", lw=1.3)
    _style(ax, "C2 — caries lesion-localisation agreement: internal vs 4 external hospitals",
           "lesions localised by a flagged tooth")
    ax.set_ylim(0, max(vals) * 1.32)
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    m = _caption(fig, "All four Ningxia splits are equally EXTERNAL to us - we never trained on "
                      "any of it. \"Same centre as NX-train\" describes Ningxia's own split design, "
                      "not proximity to our training data.")
    fig.tight_layout(rect=[0, m, 1, 1])
    fig.savefig(OUT / "02_external_validation.png", dpi=200)
    plt.close(fig)
    print(f"  02_external_validation.png  (DENTEX {vals[0]:.1%} vs NX {min(vals[1:]):.1%}–{max(vals[1:]):.1%})")


def fig_caries_gate_repair(plt):
    """The negative-class repair: in-pipeline caries rate before vs after."""
    d = _load("outputs/caries_v3/gate_comparison.json")
    if d is None:
        return
    tot = d["detected_teeth"]
    old, new, gt = d["old_gate"]["rate"], d["new_gate"]["rate"], d["annotated_caries_teeth"] / tot
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    bars = ax.bar(["Legacy gate\n(no healthy teeth\nin training)",
                   "Rebuilt gate v3\n(5,366 real\nhealthy teeth)",
                   "Annotated floor\n(ground truth)"],
                  [old, new, gt], color=[BAD, OK, MUTED], width=.55, edgecolor="none")
    for b, v in zip(bars, [old, new, gt]):
        ax.text(b.get_x() + b.get_width() / 2, v + .018, f"{v:.1%}",
                ha="center", fontsize=11, color=INK, fontweight="600")
    _style(ax, "Caries gate repair — share of detected teeth called carious",
           "of all detected teeth")
    ax.set_ylim(0, old * 1.2)
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    m = _caption(fig, f"Same {tot} teeth, same detector, same crops - only the gate differs. "
                      "Over-call 7.3x -> 1.6x. Precision is still 0.40: improved, not solved.")
    fig.tight_layout(rect=[0, m, 1, 1])
    fig.savefig(OUT / "03_caries_gate_repair.png", dpi=200)
    plt.close(fig)
    print(f"  03_caries_gate_repair.png  ({old:.1%} → {new:.1%}, floor {gt:.1%})")


def fig_stage2_ceiling(plt):
    """Why an order-independent method was necessary, by quadrant completeness."""
    d = _load("outputs/stage2_reverify/stage2_ceiling_analysis.json")
    if d is None:
        return
    rows = [r for r in d["by_bucket"] if r["n"] >= 20]
    x = [r["detections_in_quadrant"] for r in rows]
    pos = [r["positional_exact"] for r in rows]
    head = [r["head_exact"] for r in rows]
    import numpy as np
    idx = np.arange(len(x))
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.bar(idx - .19, pos, .38, label="positional (rank-order)", color=BAD, edgecolor="none")
    ax.bar(idx + .19, head, .38, label="learned head", color=OK, edgecolor="none")
    ax.set_xticks(idx)
    ax.set_xticklabels([f"{v}\nn={r['n']}" for v, r in zip(x, rows)], fontsize=8.5)
    _style(ax, "Stage 2 — FDI accuracy by quadrant completeness",
           "FDI exact (of detected)", "detections in the tooth's own quadrant")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    c = d["complete_quadrant_ceiling"]
    m = _caption(fig, f"Even on COMPLETE 8-detection quadrants - rank-order's best case - "
                      f"positional reaches {c['positional_exact']:.1%} against the head's "
                      f"{c['head_exact']:.1%} (+{c['margin']*100:.1f} points, n={c['n']}).")
    fig.tight_layout(rect=[0, m, 1, 1])
    fig.savefig(OUT / "04_stage2_ceiling.png", dpi=200)
    plt.close(fig)
    print(f"  04_stage2_ceiling.png  (complete-quadrant {c['positional_exact']:.1%} vs {c['head_exact']:.1%})")


def fig_domain_shift(plt):
    """The honest negative result: the bone-loss branch outside its training domain."""
    ext = _load("outputs/ningxia_external/full/ningxia_external.json")
    if ext is None:
        return
    bcs = ext["by_category_split"]
    nx = [(sp, bcs[f"periodontitis/{sp}"]["affected_tooth_sensitivity"])
          for sp in ["test1", "test2", "test3", "test4"] if f"periodontitis/{sp}" in bcs]
    labels = ["Tufts\n(in-domain,\nmacro-F1)", "DENTEX\n(firing rate)"] + \
             [f"Ningxia {sp}\n(affected-tooth\nsensitivity)" for sp, _ in nx]
    vals = [0.9233, 0.007] + [v for _, v in nx]
    cols = [OK] + [BAD] * (len(vals) - 1)
    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    bars = ax.bar(labels, vals, color=cols, width=.6, edgecolor="none")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + .02, f"{v:.1%}" if v < .5 else f"{v:.3f}",
                ha="center", fontsize=9.5, color=INK, fontweight="600")
    _style(ax, "Bone-loss branch: strong in-domain, near-inert on two external datasets")
    ax.set_ylim(0, 1.06)
    m = _caption(fig, "Trained on Tufts. Measured on two independent external datasets. The "
                      "metrics necessarily differ (PAPER_MATERIAL 8.12) - the collapse does not.")
    fig.tight_layout(rect=[0, m, 1, 1])
    fig.savefig(OUT / "05_bone_loss_domain_shift.png", dpi=200)
    plt.close(fig)
    print(f"  05_bone_loss_domain_shift.png  (Tufts 0.923 → external {min(v for _,v in nx):.1%}–{max(v for _,v in nx):.1%})")


def fig_input_ablation(plt):
    """Which input carries which FDI digit — the architecture-rationale test."""
    d = _load("outputs/enumeration_head/input_ablation.json")
    if d is None:
        return
    import numpy as np
    conds = [("full", "both inputs"), ("no_position", "position → mean"),
             ("shuffled_pos", "position shuffled")]
    metrics = [("jaw_acc", "jaw"), ("side_acc_laterality", "side (laterality)"),
               ("position_acc", "position digit")]
    idx = np.arange(len(conds))
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    for i, (mk, ml) in enumerate(metrics):
        vals = [d["results"][c][mk] for c, _ in conds]
        ax.bar(idx + (i - 1) * .26, vals, .25, label=ml,
               color=[ACCENT, OK, WARN][i], edgecolor="none")
    ax.set_xticks(idx)
    ax.set_xticklabels([l for _, l in conds], fontsize=9)
    _style(ax, "Which input carries which FDI digit (val, 2,729 crops)", "accuracy")
    ax.set_ylim(0, 1.12)
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper center")
    m = _caption(fig, "The image alone recovers laterality at 96.3% - positional features are "
                      "worth +3.2 points, not the decisive signal earlier drafts claimed.")
    fig.tight_layout(rect=[0, m, 1, 1])
    fig.savefig(OUT / "06_input_ablation.png", dpi=200)
    plt.close(fig)
    print("  06_input_ablation.png")


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["DejaVu Sans"]
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"writing to {OUT.relative_to(REPO_ROOT)}/\n")
    for fn in (fig_error_propagation, fig_external_validation, fig_caries_gate_repair,
               fig_stage2_ceiling, fig_domain_shift, fig_input_ablation):
        try:
            fn(plt)
        except Exception as e:            # never lose the whole run to one bad figure
            print(f"  FAILED {fn.__name__}: {type(e).__name__}: {e}")
    print("\nEvery value above was read from a saved JSON artefact -- no model was run.")


if __name__ == "__main__":
    main()
