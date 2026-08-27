#!/usr/bin/env python
"""
Regenerate the Stage-3 (caries) and Stage-4 (bone loss) figures from TRACKED artifacts.

WHY REGENERATE RATHER THAN RECOVER
-----------------------------------
`PAPER_MATERIAL.md` §9 asks to "recover them into `docs/results/figures/` or regenerate". The
original PNGs do exist in `_repo_archive/pes_capstone_report/figures/`, but copying them in would
put pictures in the repo whose provenance is a notebook nobody can re-run and whose numbers
nobody can check. Every figure here is instead drawn from a **committed** artifact:

  models/03_bone_loss_model_training_notebook_models/training_history.json   32 epochs, full curves
  models/03_.../training_summary.txt                                        confusion TN/FP/FN/TP
  models/09_caries_gate_v3/results.json                                     val + test confusion

so the figures are reproducible by anyone with the repo, and any number in them can be traced.

WHAT CANNOT BE REGENERATED, AND IS THEREFORE NOT DRAWN
-------------------------------------------------------
* **Caries training curves.** `results.json` records `best_epoch` and the final metrics but **no
  per-epoch history**, so there is nothing to plot. Drawing a curve would mean inventing it.
* **Bone-loss SEVERITY confusion matrix.** `severity_summary.txt` records per-class F1 only
  (Mild 0.80 / Moderate 0.67 / Severe 0.70) and no matrix. The 52-crop support makes this the
  figure least worth faking.

Both gaps are printed at the end so the checklist records what is genuinely still missing.

Usage:
    python scripts/figures/make_stage34_figures.py
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEF_FIG = REPO_ROOT / "docs/results/figures/paper"

BL_DIR = REPO_ROOT / "models/03_bone_loss_model_training_notebook_models"
GATE = REPO_ROOT / "models/09_caries_gate_v3/results.json"


def confusion_panel(ax, cm, labels, title, note=""):
    import numpy as np
    cm = np.asarray(cm, dtype=float)
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_title(title, fontsize=9)
    mx = cm.max() if cm.max() else 1
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f"{int(cm[i, j])}", ha="center", va="center", fontsize=11,
                    color="white" if cm[i, j] > mx * 0.55 else "black")
    if note:
        ax.text(0.5, -0.28, note, transform=ax.transAxes, ha="center", fontsize=7, color="#555")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig", type=Path, default=DEF_FIG)
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    args.fig.mkdir(parents=True, exist_ok=True)
    made, skipped = [], []

    # ---------------------------------------------------------------- Stage 4a curves
    hp = BL_DIR / "training_history.json"
    if hp.exists():
        h = json.loads(hp.read_text(encoding="utf-8"))
        ep = range(1, len(h["train_loss"]) + 1)
        best = int(max(range(len(h["val_f1_macro"])), key=lambda i: h["val_f1_macro"][i])) + 1
        fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
        ax[0].plot(ep, h["train_loss"], label="train", color="#264653")
        ax[0].plot(ep, h["val_loss"], label="val", color="#e76f51")
        ax[0].set_xlabel("epoch"); ax[0].set_ylabel("focal loss"); ax[0].legend(fontsize=8)
        ax[0].set_title("Stage 4a — loss")
        ax[1].plot(ep, h["val_f1_macro"], color="#2a9d8f", label="macro-F1")
        ax[1].plot(ep, h["val_f1_class1"], color="#e63946", ls="--", label="F1 diseased (cls 1)")
        ax[1].plot(ep, h["val_f1_class0"], color="#adb5bd", ls=":", label="F1 normal (cls 0)")
        ax[1].axvline(best, color="#555", lw=1, ls="-.", label=f"best epoch {best}")
        ax[1].set_xlabel("epoch"); ax[1].set_ylabel("F1"); ax[1].legend(fontsize=7)
        ax[1].set_title("Stage 4a — validation F1 (selection metric: macro)")
        ax[2].plot(ep, h["lr"], color="#6a4c93")
        ax[2].set_xlabel("epoch"); ax[2].set_ylabel("learning rate")
        ax[2].set_yscale("log"); ax[2].set_title("Stage 4a — LR (ReduceLROnPlateau)")
        fig.suptitle("Bone-loss binary — training history "
                     f"({len(h['train_loss'])} epochs, from models/03/training_history.json)",
                     fontsize=10)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        f = args.fig / "stage4a_training_curves.png"
        fig.savefig(f, dpi=160); made.append(f)
        print(f"  {f.name}  ({len(h['train_loss'])} epochs, best epoch {best})")
    else:
        skipped.append("Stage 4a curves: training_history.json missing")

    # ---------------------------------------------------------------- confusion matrices
    cms = []
    tsum = (BL_DIR / "training_summary.txt")
    if tsum.exists():
        t = tsum.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"TN=(\d+)\s+FP=(\d+)\s*\n?\s*FN=(\d+)\s+TP=(\d+)", t)
        if m:
            tn, fp, fn, tp = (int(x) for x in m.groups())
            cms.append(([[tn, fp], [fn, tp]], ["normal", "bone_loss"],
                        "Stage 4a — bone loss (val, real prevalence)",
                        f"n={tn+fp+fn+tp} · sens {tp/(tp+fn):.3f} · spec {tn/(tn+fp):.3f}"))
        else:
            skipped.append("Stage 4a confusion: TN/FP/FN/TP not parseable from training_summary")

    if GATE.exists():
        r = json.loads(GATE.read_text(encoding="utf-8"))
        for split in ("val", "test"):
            d = r["phase1"].get(split)
            if not d or "confusion_matrix" not in d:
                continue
            cm = d["confusion_matrix"]        # rows: [caries, no_caries]
            tp_, fn_ = cm[0][0], cm[0][1]
            fp_, tn_ = cm[1][0], cm[1][1]
            note = (f"n={d['n']} · precision {tp_/(tp_+fp_):.3f} · recall {tp_/(tp_+fn_):.3f}"
                    f" · macro-F1 {d['macro_f1']:.3f}")
            cms.append((cm, ["caries", "no_caries"],
                        f"Stage 3 — caries gate v3 ({split})", note))

    if cms:
        fig, axes = plt.subplots(1, len(cms), figsize=(4.3 * len(cms), 4.3))
        if len(cms) == 1:
            axes = [axes]
        for ax_, (cm, labs, title, note) in zip(axes, cms):
            confusion_panel(ax_, cm, labs, title, note)
        fig.suptitle("Stage 3 / Stage 4a confusion matrices — regenerated from committed artifacts",
                     fontsize=10)
        fig.tight_layout(rect=[0, 0.04, 1, 0.93])
        f = args.fig / "stage34_confusion_matrices.png"
        fig.savefig(f, dpi=160); made.append(f)
        print(f"  {f.name}  ({len(cms)} panels)")

    skipped.append("Stage 3 caries training curves: results.json records best_epoch and final "
                   "metrics but NO per-epoch history -- nothing to plot without inventing it")
    skipped.append("Stage 4b severity confusion matrix: severity_summary.txt records per-class F1 "
                   "only (Mild 0.80 / Moderate 0.67 / Severe 0.70), no matrix; 52-crop support")

    print(f"\n  {len(made)} figure(s) written to {args.fig}")
    print("  NOT regenerated (recorded rather than faked):")
    for s in skipped:
        print(f"    - {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
