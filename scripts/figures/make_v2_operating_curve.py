# -*- coding: utf-8 -*-
"""Paper v2, new figure: the image-blind operating curve (round-1 review item 16).

F1 of the k most prevalent fit-set codes, k = 1..16, against the number of codes named on the
164 scored DENTEX images, with each system placed as a point at its own volume. Every value is
read from outputs/review_round1/constant_stability_and_curve.json; nothing is recomputed or typed.
The script asserts the values the paper quotes before drawing.

Run from the repo root: python scripts/figures/make_v2_operating_curve.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "outputs/review_round1/constant_stability_and_curve.json"
OUT = REPO / "paper/v2/figures/V2_operating_curve.pdf"

d = json.loads(SRC.read_text(encoding="utf-8"))
curve = d["operating_curve_fit_order"]
mv = d["matched_volume"]

# Quoted in the paper: assert, never draw a figure that disagrees with the text.
assert [c["k"] for c in curve] == list(range(1, 17))
assert curve[7]["named"] == 1312 and curve[7]["f1"] == 0.3197
assert min(c["f1"] for c in curve[5:9]) == 0.2984 and max(c["f1"] for c in curve[5:9]) == 0.3249
assert mv["pipeline_lesion_detector"]["f1"] == 0.4977 and mv["pipeline_lesion_detector"]["named"] == 624
assert mv["pipeline_crop_classifier"]["f1"] == 0.3625 and mv["pipeline_crop_classifier"]["named"] == 1537

systems = [  # key, label, marker, colour (Okabe-Ito)
    ("pipeline_lesion_detector", "Pipeline, lesion detector", "D", "#0072B2"),
    ("pipeline_crop_classifier", "Pipeline, crop classifier", "s", "#E69F00"),
    ("qwen25vl_32b_zero_shot", "Qwen2.5-VL-32B", "^", "#009E73"),
    ("qwen25vl_7b_zero_shot", "Qwen2.5-VL-7B", "v", "#CC79A7"),
]

plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.linewidth": 0.6})
fig, ax = plt.subplots(figsize=(3.45, 2.45))
x = [c["named"] for c in curve]
y = [c["f1"] for c in curve]
ax.plot(x, y, "-o", color="#555555", ms=2.6, lw=1.0, label="Image-blind list of $k$ codes")
ax.scatter([curve[7]["named"]], [curve[7]["f1"]], s=40, facecolors="none", edgecolors="#000000",
           linewidths=0.9, zorder=4, label="Eight molars ($k$=8)")
for key, label, mk, col in systems:
    r = mv[key]
    ax.scatter([r["named"]], [r["f1"]], marker=mk, s=26, color=col, zorder=5, label=label)
    ax.plot([r["named"], r["named"]], [r["matched_constant"]["f1"], r["f1"]], ":", color=col, lw=0.8)
ax.set_xlabel("Tooth codes named over 164 images")
ax.set_ylabel("FDI-set F1")
ax.set_xlim(0, 2750)
ax.set_ylim(0, 0.55)
ax.grid(alpha=0.25, lw=0.4)
ax.legend(loc="lower right", fontsize=6.2, frameon=True, framealpha=0.9, edgecolor="none",
          handletextpad=0.3, borderaxespad=0.2)
fig.tight_layout(pad=0.3)
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT)
print("wrote", OUT.relative_to(REPO))
