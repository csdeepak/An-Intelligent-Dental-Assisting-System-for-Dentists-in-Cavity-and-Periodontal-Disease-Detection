#!/usr/bin/env python
"""
Real-radiograph figures for the paper: what an OPG looks like, what each stage does to one, what
the output is against the expert's annotation, and how each trained stage's training went.

Written 28 Oct 2026 for the mentor draft (`paper/ieee/`), whose figures until then were charts
only -- a reader could not see a radiograph, a detection or an output anywhere in it.

EVERY PIXEL OF A PREDICTION HERE COMES FROM THE SHIPPED CODE PATH, not a re-implementation:
`run_inference.load_models` + `run_inference.run_pipeline` (Stages 1-6, default checkpoints,
hash-pinned), `classifiers.run_lesion_detector_raw` (the lesion boxes Stage 3a maps onto teeth,
which the report does not store) and `run_inference.draw_overlay` (the overlay the CLI and the app
write). Before anything is drawn, each image's count of caries-flagged teeth is asserted equal to
the saved evaluation of the same detector (`outputs/stage1_switch/C_dentex_lesion-detector_arm3c/`),
so a figure cannot show a different model from the one the paper scores.

Images: DENTEX `disease/` only (CC BY-NC-SA 4.0; attribute in every caption), and only from the
164 leakage-free scored images. No Tufts, Ningxia or CariesXrays pixels: Tufts' licence forbids
redistribution, the other two state no licence.

Which images: chosen by a rule written before rendering, from the saved per-image evaluation of the
148 scored images that carry a caries lesion -- (a) the most lesions, all matched; (b) the most
lesions, none matched; (c) `test_0`, matched 2 of 3, near the cohort's 0.595. Not chosen by eye.

Training curves: read from the run artefacts in `models/` (results.csv / training_results.json /
seed*_history.json). They are training- and validation-split curves, not test results.

    python scripts/figures/make_opg_figures.py            # writes paper/ieee/figures/R0*.pdf
"""

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

DENTEX = Path.home() / "Downloads/Capstone/DENTEX/disease"
EVAL = REPO / "outputs/stage1_switch/C_dentex_lesion-detector_arm3c/lesion_localization.json"
LEAK = REPO / "data/dentex/disease_leaked_images.json"
OUT = REPO / "paper/ieee/figures"

WALK = "test_0"
CONSTANT = {16, 17, 26, 27, 36, 37, 46, 47}

# Okabe-Ito, readable under red-green colour-vision deficiency and on a grey radiograph.
C_EXPERT, C_LESION, C_FLAG = "#F0E442", "#D55E00", "#E69F00"
C_TOOTH, C_CONST, C_ABN = "#56B4E9", "#CC79A7", "#009E73"
ATTRIB = "Radiographs: DENTEX (Hamamci et al.), CC BY-NC-SA 4.0."


def expert_caries(stem):
    """DENTEX labels are `<finding id>-<turkish name>-<FDI>`; id 1 (curuk) is caries -- the only
    finding the caries evaluation scores (`scripts/eval/lesion_localization.py`)."""
    lab = json.loads((DENTEX / "label" / f"{stem}.json").read_text(encoding="utf-8"))
    out = []
    for s in lab["shapes"]:
        fid, _, fdi = s["label"].split("-", 2)
        if fid == "1":
            out.append((int(fdi), s["points"]))
    return out


def pick_images():
    leak = set(json.loads(LEAK.read_text(encoding="utf-8"))["all_excluded"])
    pi = json.loads(EVAL.read_text(encoding="utf-8"))["per_image"]
    assert not leak & {p["image"] for p in pi}, "a leaked image is in the scored set"
    full = max((p for p in pi if p["n_matched"] == p["n_lesions"]), key=lambda p: p["n_lesions"])
    none = max((p for p in pi if p["n_matched"] == 0), key=lambda p: p["n_lesions"])
    walk = next(p for p in pi if p["image"] == WALK)
    return {"full": full, "none": none, "walk": walk}


def run(models, device, paths, stem):
    import cv2
    from run_inference import run_pipeline
    from src.classifiers import run_lesion_detector_raw
    img = cv2.imread(str(DENTEX / "input" / f"{stem}.png"))
    rep = run_pipeline(img, models, device, paths, image_label=stem, verbose=False)
    raw = run_lesion_detector_raw(models["caries_lesion_model"], img, conf=0.25)
    return img, rep, raw


def roi(rep, img, pad=0.05):
    b = [t["bbox_xyxy"] for t in rep["teeth"]]
    x1, y1 = min(v[0] for v in b), min(v[1] for v in b)
    x2, y2 = max(v[2] for v in b), max(v[3] for v in b)
    h, w = img.shape[:2]
    px, py = (x2 - x1) * pad, (y2 - y1) * pad
    return max(0, int(x1 - px)), max(0, int(y1 - py)), min(w, int(x2 + px)), min(h, int(y2 + py))


def show(ax, img_bgr, box=None):
    """Draw the image -- only the cropped region, placed at its original pixel coordinates, so
    every box and polygon is drawn in image coordinates and the PDF embeds no hidden pixels."""
    import cv2
    h, w = img_bgr.shape[:2]
    x1, y1, x2, y2 = box or (0, 0, w, h)
    rgb = cv2.cvtColor(img_bgr[y1:y2, x1:x2], cv2.COLOR_BGR2RGB)
    ax.imshow(rgb, extent=(x1, x2, y2, y1), interpolation="lanczos")
    ax.set_xlim(x1, x2)
    ax.set_ylim(y2, y1)
    ax.set_xticks([])
    ax.set_yticks([])


def rect(ax, b, colour, lw=0.8, ls="-", alpha=1.0):
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec=colour,
                           lw=lw, ls=ls, alpha=alpha))


def polys(ax, exp, lw=1.0):
    from matplotlib.patches import Polygon
    for _, pts in exp:
        ax.add_patch(Polygon(pts, closed=True, fill=False, ec=C_EXPERT, lw=lw))


def label(ax, x, y, s, colour, size=4.5):
    ax.text(x, y, s, color=colour, fontsize=size, ha="left", va="bottom",
            bbox=dict(boxstyle="square,pad=0.05", fc="black", ec="none", alpha=0.55))


def tag(ax, s):
    """Panel title above the image, so it hides no label inside it."""
    ax.set_title(s, fontsize=6.8, loc="left", pad=1.5)


def legend(fig, items, y):
    from matplotlib.lines import Line2D
    h = [Line2D([0], [0], color=c, lw=1.4, ls=ls) for _, c, ls in items]
    fig.legend(h, [n for n, _, _ in items], loc="lower center", ncol=len(items), fontsize=6.5,
               frameon=False, bbox_to_anchor=(0.5, y), handlelength=2.0)


def fig_primer(img, rep, exp, path):
    """Fig: how to read an OPG -- orientation, quadrants, FDI codes, the expert's caries and the
    eight teeth the image-blind constant names."""
    import matplotlib.pyplot as plt
    teeth = rep["teeth"]
    up = [t for t in teeth if t["quadrant"] in (1, 2)]
    lo = [t for t in teeth if t["quadrant"] in (3, 4)]
    # Occlusal plane and midline placed from the detected teeth: the median upper-tooth bottom
    # and lower-tooth top, and the gap between quadrants 1/4 and 2/3.
    occl = (sorted(t["bbox_xyxy"][3] for t in up)[len(up) // 2]
            + sorted(t["bbox_xyxy"][1] for t in lo)[len(lo) // 2]) / 2
    q1 = [t["bbox_xyxy"][2] for t in teeth if t["quadrant"] in (1, 4)]
    q2 = [t["bbox_xyxy"][0] for t in teeth if t["quadrant"] in (2, 3)]
    mid = (max(q1) + min(q2)) / 2
    fig, ax = plt.subplots(figsize=(3.5, 1.95))
    box = roi(rep, img, pad=0.10)
    show(ax, img, box)
    ax.axvline(mid, color="white", lw=0.6, ls=":")
    ax.axhline(occl, color="white", lw=0.6, ls=":")
    x1, y1, x2, y2 = box
    for q, (fx, fy) in {1: (0.04, 0.10), 2: (0.90, 0.10), 4: (0.04, 0.84), 3: (0.90, 0.84)}.items():
        ax.text(x1 + fx * (x2 - x1), y1 + fy * (y2 - y1), f"Q{q}", color="white", fontsize=7,
                fontweight="bold", ha="left", va="top",
                bbox=dict(boxstyle="square,pad=0.15", fc="black", ec="none", alpha=0.6))
    for t in teeth:
        b = t["bbox_xyxy"]
        if t["fdi"] in CONSTANT:
            rect(ax, b, C_CONST, lw=0.9, ls="--")
        label(ax, b[0] + 2, b[1] if t["quadrant"] in (1, 2) else b[3] + 60, str(t["fdi"]),
              C_CONST if t["fdi"] in CONSTANT else "white", size=3.8)
    polys(ax, exp)
    ax.text(x1 + 0.01 * (x2 - x1), y2 - 0.02 * (y2 - y1), "patient's right", color="white",
            fontsize=5, va="bottom")
    ax.text(x2 - 0.01 * (x2 - x1), y2 - 0.02 * (y2 - y1), "patient's left", color="white",
            fontsize=5, va="bottom", ha="right")
    legend(fig, [("expert caries", C_EXPERT, "-"), ("constant's 8 molars", C_CONST, "--")], -0.01)
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.09)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def fig_walkthrough(img, rep, raw, exp, path):
    """Fig: one held-out OPG through every stage, panels (a)-(f)."""
    import matplotlib.pyplot as plt
    from run_inference import draw_overlay
    box = roi(rep, img)
    teeth = rep["teeth"]
    fig, axs = plt.subplots(3, 2, figsize=(7.16, 5.6))
    ax = axs.ravel()

    show(ax[0], img)
    rect(ax[0], box, "white", lw=0.8, ls="--")
    tag(ax[0], "(a) input OPG, 2829x1316 px")

    show(ax[1], img, box)
    for t in teeth:
        rect(ax[1], t["bbox_xyxy"], C_TOOTH, lw=0.7)
        label(ax[1], t["bbox_xyxy"][0] + 2, t["bbox_xyxy"][1], f"{t['detection_confidence']:.2f}",
              C_TOOTH, size=3.6)
    tag(ax[1], f"(b) Stage 1: {len(teeth)} tooth boxes (confidence)")

    show(ax[2], img, box)
    for t in teeth:
        b = t["bbox_xyxy"]
        rect(ax[2], b, C_TOOTH, lw=0.7, alpha=0.6)
        label(ax[2], b[0] + 2, b[1] if t["quadrant"] in (1, 2) else b[3] + 55,
              f"{t['fdi']}" + ("?" if t["fdi_flags"] else ""), "white", size=4.3)
    tag(ax[2], "(c) Stage 2: FDI code per tooth, one-to-one")

    show(ax[3], img, box)
    for t in teeth:
        rect(ax[3], t["bbox_xyxy"], C_TOOTH, lw=0.5, alpha=0.4)
    for (lb, c) in raw:
        rect(ax[3], lb, C_LESION, lw=1.1)
        label(ax[3], lb[0], lb[1], f"{c:.2f}", C_LESION, size=4.0)
    tag(ax[3], f"(d) Stage 3a: {len(raw)} lesion boxes, whole image")

    show(ax[4], img, box)
    for t in teeth:
        b = t["bbox_xyxy"]
        if t["caries"]["finding"] != "no_caries":
            rect(ax[4], b, C_FLAG, lw=1.2)
            label(ax[4], b[0] + 2, b[1], f"{t['fdi']} {t['caries']['finding'].replace('_', ' ')}",
                  C_FLAG, size=4.3)
        if t["bone_loss"]["finding"] == "bone_loss":
            rect(ax[4], b, C_ABN, lw=1.1, ls="--")
            label(ax[4], b[0] + 2, b[3] + 55, f"{t['fdi']} stage-4 flag", C_ABN, size=4.3)
    n_c = sum(t["caries"]["finding"] != "no_caries" for t in teeth)
    n_a = sum(t["bone_loss"]["finding"] == "bone_loss" for t in teeth)
    tag(ax[4], f"(e) Stages 3-4: {n_c} teeth flagged for caries, {n_a} stage-4 flags")

    viz = draw_overlay(img, rep)
    show(ax[5], viz, box)
    polys(ax[5], exp, lw=1.2)
    tag(ax[5], f"(f) shipped overlay vs expert caries ({len(exp)} lesions)")

    legend(fig, [("tooth box", C_TOOTH, "-"), ("lesion box (Stage 3a)", C_LESION, "-"),
                 ("tooth flagged for caries", C_FLAG, "-"), ("Stage-4 flag", C_ABN, "--"),
                 ("expert caries polygon", C_EXPERT, "-")], 0.0)
    fig.subplots_adjust(left=0.005, right=0.995, top=0.975, bottom=0.045, wspace=0.02,
                        hspace=0.10)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def fig_outcomes(cases, path):
    """Fig: real outputs against the expert, three rule-chosen images; left the lesion detector,
    right the constant placed by the same front end."""
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(3, 2, figsize=(7.16, 4.9))
    for r, (title, img, rep, raw, exp, p) in enumerate(cases):
        box = roi(rep, img)
        a, b = axs[r]
        show(a, img, box)
        show(b, img, box)
        for t in rep["teeth"]:
            bb = t["bbox_xyxy"]
            if t["caries"]["finding"] != "no_caries":
                rect(a, bb, C_FLAG, lw=1.0)
                label(a, bb[0] + 2, bb[1], str(t["fdi"]), C_FLAG, size=4.3)
            if t["fdi"] in CONSTANT:
                rect(b, bb, C_CONST, lw=1.0, ls="--")
                label(b, bb[0] + 2, bb[1], str(t["fdi"]), C_CONST, size=4.3)
        for (lb, _) in raw:
            rect(a, lb, C_LESION, lw=1.0)
        polys(a, exp)
        polys(b, exp)
        n_flag = sum(t["caries"]["finding"] != "no_caries" for t in rep["teeth"])
        n_const = sum(t["fdi"] in CONSTANT for t in rep["teeth"])
        tag(a, f"{title}  lesion detector: {p['n_matched']}/{p['n_lesions']} lesions, "
               f"{n_flag} teeth flagged")
        tag(b, f"constant: {n_const} teeth named, the same in every image")
    legend(fig, [("expert caries polygon", C_EXPERT, "-"), ("lesion box", C_LESION, "-"),
                 ("tooth flagged by the pipeline", C_FLAG, "-"),
                 ("tooth named by the constant", C_CONST, "--")], 0.0)
    fig.subplots_adjust(left=0.005, right=0.995, top=0.97, bottom=0.05, wspace=0.02,
                        hspace=0.12)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return [{k.strip(): float(v) for k, v in r.items()} for r in csv.DictReader(f)]


def fig_training(path):
    """Fig: the four trained stages' own training logs -- the evidence that each converged, and
    where its checkpoint was taken. Validation splits, not test."""
    import matplotlib.pyplot as plt
    det = read_csv(REPO / "models/15_detector_multicorpus_leverA/arm3c_results.csv")
    les = read_csv(REPO / "models/16_lever_b_pooled/lever_b_pooled_yolo11l-2/results.csv")
    fdi = json.loads((REPO / "models/10_fdi_head_dentex_tufts_v2/training_results.json")
                     .read_text(encoding="utf-8"))
    s4 = {s: json.loads((REPO / f"models/18_bone_loss_radiograph_split/seed{s}_history.json")
                        .read_text(encoding="utf-8")) for s in (42, 43, 44)}

    fig, axs = plt.subplots(1, 4, figsize=(7.16, 1.75))
    for ax, rows, name in ((axs[0], det, "(a) Stage 1 tooth detector"),
                           (axs[1], les, "(b) Stage 3a lesion detector")):
        ep = [r["epoch"] for r in rows]
        ax.plot(ep, [r["train/box_loss"] for r in rows], color="#444444", lw=0.9, label="train box loss")
        ax.plot(ep, [r["val/box_loss"] for r in rows], color="#444444", lw=0.9, ls="--",
                label="val box loss")
        tw = ax.twinx()
        m = [r["metrics/mAP50(B)"] for r in rows]
        tw.plot(ep, m, color="#0072B2", lw=1.1, label="val mAP@0.5")
        k = max(range(len(m)), key=m.__getitem__)
        tw.plot(ep[k], m[k], "o", color="#0072B2", ms=3)
        tw.text(0.97, 0.05, f"best {m[k]:.3f} (epoch {int(ep[k])})", transform=ax.transAxes,
                fontsize=5.5, color="#0072B2", ha="right", va="bottom",
                bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.85))
        tw.set_ylim(0, 1.05)
        tw.set_ylabel("val mAP@0.5", fontsize=6, color="#0072B2")
        tw.tick_params(labelsize=5.5, colors="#0072B2")
        ax.set_title(name, fontsize=6.5)
        ax.set_xlabel("epoch", fontsize=6)
        ax.tick_params(labelsize=5.5)

    log = fdi["epoch_log"]
    ep = [e["epoch"] for e in log]
    ax = axs[2]
    ax.plot(ep, [e["train_loss"] for e in log], color="#444444", lw=0.9)
    tw = ax.twinx()
    fx = [e["fdi_exact"] for e in log]
    tw.plot(ep, fx, color="#0072B2", lw=1.1)
    tw.plot(ep, [e["quadrant_acc"] for e in log], color="#56B4E9", lw=0.9, ls="--")
    b = fdi["best_epoch"]
    tw.plot(b, fx[ep.index(b)], "o", color="#0072B2", ms=3)
    tw.text(0.97, 0.45, f"best {fx[ep.index(b)]:.3f} (epoch {b})", transform=ax.transAxes,
            fontsize=5.5, color="#0072B2", ha="right", va="bottom")
    tw.set_ylim(0, 1.05)
    tw.set_ylabel("val FDI-exact", fontsize=6, color="#0072B2")
    tw.tick_params(labelsize=5.5, colors="#0072B2")
    ax.set_title("(c) Stage 2 FDI head", fontsize=6.5)
    ax.set_xlabel("epoch", fontsize=6)
    ax.tick_params(labelsize=5.5)

    ax = axs[3]
    for s, ls in ((42, "-"), (43, "--"), (44, ":")):
        e = s4[s]["epochs"]
        ax.plot([x["epoch"] for x in e], [x["macro_f1"] for x in e], color="#0072B2", lw=0.9,
                ls=ls, label=f"seed {s}")
        bb = s4[s]["best_epoch"]
        ax.plot(bb, s4[s]["best_val_macro_f1"], "o", color="#0072B2", ms=2.5)
    ax.set_ylim(0, 1)
    ax.set_title("(d) Stage 4a flag, 3 seeds", fontsize=6.5)
    ax.set_xlabel("epoch", fontsize=6)
    ax.tick_params(labelsize=5.5)
    ax.legend(fontsize=5, frameon=False, loc="upper right")
    axs[0].set_ylabel("loss", fontsize=6)
    axs[3].set_ylabel("val macro-F1", fontsize=6)
    from matplotlib.lines import Line2D
    fig.legend([Line2D([0], [0], color="#444444", lw=0.9), Line2D([0], [0], color="#444444", lw=0.9, ls="--"),
                Line2D([0], [0], color="#0072B2", lw=1.1), Line2D([0], [0], color="#56B4E9", lw=0.9, ls="--"),
                Line2D([0], [0], color="#0072B2", ls="none", marker="o", ms=3)],
               ["train loss", "val loss", "val metric (right axis)", "val quadrant accuracy (c)",
                "selected checkpoint"], loc="lower center", ncol=5, fontsize=5.8, frameon=False,
               bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(pad=0.3, w_pad=0.6, rect=(0, 0.08, 1, 1))
    fig.savefig(path)
    plt.close(fig)
    return {"det_best": max((r["metrics/mAP50(B)"], r["epoch"]) for r in det),
            "les_best": max((r["metrics/mAP50(B)"], r["epoch"]) for r in les),
            "det_epochs": len(det), "les_epochs": len(les),
            "fdi_best": (fdi["best_epoch"], fdi["val"]["fdi_exact"], fdi["val"]["n"]),
            "fdi_val_quadrant_position_acc": (fdi["val"]["quadrant_acc"], fdi["val"]["position_acc"]),
            "s4": {s: (s4[s]["best_epoch"], s4[s]["best_val_macro_f1"], len(s4[s]["epochs"]))
                   for s in s4}}


def main():
    import matplotlib
    matplotlib.use("Agg")
    from run_inference import load_models

    OUT.mkdir(parents=True, exist_ok=True)
    picks = pick_images()
    models, device, paths = load_models()
    done = {}
    for key, p in picks.items():
        img, rep, raw = run(models, device, paths, p["image"])
        flagged = sum(t["caries"]["finding"] != "no_caries" for t in rep["teeth"])
        assert flagged == p["n_predicted_positive"], \
            f"{p['image']}: {flagged} flagged now vs {p['n_predicted_positive']} in the saved eval"
        exp = expert_caries(p["image"])
        assert len(exp) == p["n_lesions"], f"{p['image']}: lesion count differs from the eval"
        done[key] = (img, rep, raw, exp, p)

    img, rep, raw, exp, p = done["full"]
    fig_primer(img, rep, exp, OUT / "R01_opg_primer.pdf")
    img, rep, raw, exp, p = done["walk"]
    fig_walkthrough(img, rep, raw, exp, OUT / "R02_walkthrough.pdf")
    fig_outcomes([("(a)",) + done["full"], ("(b)",) + done["walk"], ("(c)",) + done["none"]],
                 OUT / "R03_outcomes.pdf")
    tr = fig_training(OUT / "R04_training.pdf")

    facts = {k: {"image": v[4]["image"], "lesions": v[4]["n_lesions"], "matched": v[4]["n_matched"],
                 "flagged": v[4]["n_predicted_positive"], "teeth": len(v[1]["teeth"]),
                 "lesion_boxes": len(v[2]),
                 "stage4_flags": sum(t["bone_loss"]["finding"] == "bone_loss" for t in v[1]["teeth"]),
                 "constant_teeth": sum(t["fdi"] in CONSTANT for t in v[1]["teeth"]),
                 "expert_on_constant_codes": sum(f in CONSTANT for f, _ in v[3]),
                 "image_size": [v[0].shape[1], v[0].shape[0]],
                 "expert_caries_fdi": sorted(f for f, _ in v[3]),
                 "flagged_fdi": sorted([t["fdi"], t["caries"]["finding"]] for t in v[1]["teeth"]
                                       if t["caries"]["finding"] != "no_caries"),
                 "stage4_flag_fdi": sorted(t["fdi"] for t in v[1]["teeth"]
                                           if t["bone_loss"]["finding"] == "bone_loss"),
                 "uncertain_fdi": [t["fdi"] for t in v[1]["teeth"] if t["fdi_flags"]],
                 "lesion_box_confidences": sorted(round(c, 2) for _, c in v[2]),
                 "constant_codes_present": sorted(t["fdi"] for t in v[1]["teeth"]
                                                  if t["fdi"] in CONSTANT)}
             for k, v in done.items()}
    facts["training"] = tr
    # The walkthrough's full report, so the paper's JSON excerpt traces to a saved file. Local
    # absolute paths are reduced to repo-relative / file names; nothing else is changed.
    rep = done["walk"][1]
    rep["image"]["path"] = Path(rep["image"]["path"]).name
    for m in rep["models"].values():
        for k, v in list(m.items()) if isinstance(m, dict) else []:
            if isinstance(v, str) and str(REPO) in v:
                m[k] = Path(v).relative_to(REPO).as_posix()
    (OUT / "R02_test_0_report.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    (OUT / "R_figures_facts.json").write_text(json.dumps(facts, indent=1, default=str) + "\n",
                                              encoding="utf-8")
    print(json.dumps(facts, indent=1, default=str))


if __name__ == "__main__":
    main()
