"""Review-round analysis (23 Nov 2026), post hoc, development data only (164 scored DENTEX images).

Two questions raised by the independent reviewers of research_paper/paper.md:

 A (Reviewer A, CRITICAL 1): the image-blind constant names its eight molar codes on every image,
   present tooth or not, while the pipeline can only name teeth its front end detected. What does a
   constant score if it names the eight molars only where the shipped front end (Stages 1-2)
   detected and numbered them? Paired cluster bootstrap (images, 10,000 resamples, seed 42) of
   each pipeline arm minus that constant, on FDI-set F1.
 B (Reviewer B, CRITICAL 1): are DENTEX caries ("curuk") annotations lesion outlines or
   whole-tooth outlines? For each caries polygon: its bounding-box area divided by the area of the
   detected tooth box that contains most of it, and its IoU with that box.

Nothing is trained or tuned. The shipped default pipeline is run once per image on CPU.
Control: the lesion-detector caries codes this run flags are compared with the saved predictions
in outputs/stage1_switch/D_fdiset_lesion-detector_arm3c/arm_pipeline_lesion_detector.json (made on
the macOS clone). The first run (23 Nov) stopped on 12 differing images; this version records the
differences and scores the saved run and this rerun side by side.
Writes research_paper/audit_runs/review_round_analyses.json. Run from the repo root.
"""
import json, re, sys, time
from pathlib import Path

import numpy as np

REPO = Path(".").resolve()
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts" / "eval"))
DIS = Path.home() / "Downloads/Capstone/DENTEX/disease"
OUT = REPO / "research_paper/audit_runs/review_round_analyses.json"
MOLARS = {"16", "17", "26", "27", "36", "37", "46", "47"}
LABEL_RE = re.compile(r"^(\d+)-(.+)-(\d+)$")

from c1_vlm_baseline import load_gt  # noqa: E402

saved_ld = {k: set(v) for k, v in json.loads((REPO / "outputs/stage1_switch/D_fdiset_lesion-detector_arm3c/arm_pipeline_lesion_detector.json").read_text(encoding="utf-8"))["predictions"].items()}
saved_gate = {k: set(v) for k, v in json.loads((REPO / "outputs/stage1_switch/D_fdiset_gate_arm3c/arm_pipeline.json").read_text(encoding="utf-8"))["predictions"].items()}
gt = {k: v for k, v in load_gt(DIS).items() if k in saved_ld}
assert len(gt) == 164, len(gt)

import cv2, torch  # noqa: E402
from scripts.run_inference import load_models, run_pipeline  # noqa: E402
models, device, paths = load_models(device=torch.device("cpu"))

detected, flagged, boxes, t0 = {}, {}, {}, time.time()
for n, stem in enumerate(sorted(gt)):
    img = cv2.imread(str(DIS / "input" / f"{stem}.png"))
    rep = run_pipeline(img, models, device, paths, image_label=stem, verbose=False)
    teeth = [t for t in rep["teeth"] if t.get("fdi") is not None]
    detected[stem] = {str(t["fdi"]) for t in teeth}
    flagged[stem] = {str(t["fdi"]) for t in teeth if t["caries"]["finding"] != "no_caries"}
    boxes[stem] = [(str(t["fdi"]), t["bbox_xyxy"]) for t in teeth]
    if n % 20 == 0:
        print(f"{n}/164 {time.time() - t0:.0f}s", flush=True)

json.dump({"detected": {k: sorted(v) for k, v in detected.items()}, "flagged_lesion_detector": {k: sorted(v) for k, v in flagged.items()},
           "boxes": boxes}, open(REPO / "research_paper/audit_runs/dentex_rerun_windows_2026-11-23.json", "w"), indent=0)
mism = {s: {"saved_only": sorted(saved_ld[s] - flagged[s]), "rerun_only": sorted(flagged[s] - saved_ld[s])} for s in gt if flagged[s] != saved_ld[s]}
print("control: images whose lesion-detector codes differ from the saved (macOS) run:", len(mism))
# 23 Nov 2026, second run: the first run stopped here on 12 mismatches. Both runs are now scored side by side
# and the mismatch is reported, so the comparison does not depend on which machine's run is used.

def per_image(pred):
    return [(len(gt[s] & pred[s]), len(pred[s]), len(gt[s])) for s in sorted(gt)]

def f1(rows):
    h = sum(r[0] for r in rows); p = sum(r[1] for r in rows); g = sum(r[2] for r in rows)
    return 2 * h / (p + g)

arms = {"constant_all_images": {s: set(MOLARS) for s in gt},
        "constant_detected_molars": {s: MOLARS & detected[s] for s in gt},
        "pipeline_lesion_detector": saved_ld, "pipeline_lesion_detector_rerun": flagged, "pipeline_crop_classifier": saved_gate}
rows = {a: per_image(p) for a, p in arms.items()}
res = {"n_images": 164, "n_boot": 10000, "seed": 42, "control": {"images_differing_from_saved_run": len(mism), "diffs": mism}, "arms": {}}
for a, r in rows.items():
    h = sum(x[0] for x in r); p = sum(x[1] for x in r); g = sum(x[2] for x in r)
    res["arms"][a] = {"tp": h, "named": p, "gt": g, "precision": round(h / p, 4), "recall": round(h / g, 4), "f1": round(f1(r), 4)}
rng = np.random.default_rng(42)
idx = [rng.integers(0, 164, 164) for _ in range(10000)]
base = rows["constant_detected_molars"]
res["paired_minus_detected_constant_pp"] = {}
for a in ("pipeline_lesion_detector", "pipeline_lesion_detector_rerun", "pipeline_crop_classifier", "constant_all_images"):
    d = [100 * (f1([rows[a][i] for i in ix]) - f1([base[i] for i in ix])) for ix in idx]
    res["paired_minus_detected_constant_pp"][a] = {"point": round(100 * (f1(rows[a]) - f1(base)), 2),
                                                   "ci95": [round(float(np.percentile(d, 2.5)), 2), round(float(np.percentile(d, 97.5)), 2)]}

# B: caries polygon size against its tooth box
ratios, ious = [], []
for s in sorted(gt):
    lab = json.loads((DIS / "label" / f"{s}.json").read_text(encoding="utf-8"))
    for sh in lab.get("shapes", []):
        m = LABEL_RE.match(sh["label"])
        if not (m and m.group(1) == "1"):
            continue
        pts = np.array(sh["points"], float)
        x0, y0, x1, y1 = pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()
        la = max((x1 - x0) * (y1 - y0), 1.0)
        best = None
        for code, (a0, b0, a1, b1) in boxes[s]:
            ix0, iy0, ix1, iy1 = max(x0, a0), max(y0, b0), min(x1, a1), min(y1, b1)
            inter = max(ix1 - ix0, 0) * max(iy1 - iy0, 0)
            ta = (a1 - a0) * (b1 - b0)
            cand = (inter / la, la / ta, inter / (la + ta - inter))
            if best is None or cand[0] > best[0]:
                best = cand
        if best and best[0] > 0:
            ratios.append(best[1]); ious.append(best[2])
q = lambda v: [round(float(x), 3) for x in np.percentile(v, [10, 25, 50, 75, 90])]
res["caries_polygon_vs_tooth_box"] = {"n_polygons_matched": len(ratios),
    "area_ratio_polygon_bbox_over_tooth_box_p10_25_50_75_90": q(ratios),
    "iou_with_tooth_box_p10_25_50_75_90": q(ious),
    "share_with_area_ratio_above_0.5": round(float(np.mean(np.array(ratios) > 0.5)), 3)}
res["runtime_s"] = round(time.time() - t0, 1)
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1)
print(json.dumps(res, indent=1))
