"""
Lesion-localisation agreement: do the pipeline's predicted-diseased teeth spatially overlap a
real, expert-annotated lesion?

WHY THIS EXISTS
----------------
`MASTER_PLAN_2026H2.md` §4.3.4 promotes this to the **primary external number** for Ningxia,
specifically because it needs no negatives at all: it only asks, of every real lesion, was a
diseased tooth flagged near it? Unlike a caries rate or a precision/recall table, it cannot be
corrupted by Ningxia's missing healthy-control problem (RESULTS_LOG, `MASTER_PLAN_2026H2.md`
§4.4). It also doubles as the T1.5 quantified XAI metric.

**No code for this existed anywhere in the repo before this file.** Built and validated here
against DENTEX first, deliberately, so that connecting Ningxia later is "point this script at
a different folder" rather than a week of new code written under time pressure.

SCOPE — DENTEX ONLY, AND WHY
-----------------------------
DENTEX `disease/label/*.json` ships real expert lesion polygons (LabelMe format, verified
directly: `shape_type: "polygon"`, e.g. 12 points for `test_0`'s first shape). Ningxia ships
raster segmentation masks instead -- a different ground-truth format this project has not yet
inspected (the drive is disconnected). Guessing that encoding (binary? multi-class? RLE?)
before seeing a real file would be exactly the kind of imagined-not-verified code this project
has spent this whole session correcting. `load_lesion_gt` below is deliberately the one
function that would need a Ningxia-specific sibling; nothing else in this file assumes the
DENTEX format.

GROUND-TRUTH SCOPING -- verified against the raw label files, not assumed
---------------------------------------------------------------------------
`disease/label/*.json` labels are `<finding_id>-<turkish_name>-<FDI>`. All 8 finding types,
re-extracted directly from source for this file (counts match the parse `compare_caries_gates.py`
already relies on for its "annotated caries teeth" floor):

    id  name      meaning                          in scope for CARIES localisation?
    1   çürük     caries                            YES -- the only category the caries
                                                     branch actually predicts
    2   küretaj   periodontal curettage (procedure) no  -- a treatment marker, not a lesion
    3   kanal     root canal (procedure)             no  -- the tooth has ALREADY been treated;
                                                     scoring a treated tooth as a missed caries
                                                     lesion would be wrong in the other direction
    5   çekim     extraction (status marker)         no
    6   gömülü    impacted                           no  -- a position anomaly, not caries
    7   lezyon    lesion (periapical)                no  -- a different clinical entity
                                                     (root-apex infection, not a crown-surface
                                                     caries finding); no branch of this pipeline
                                                     targets it
    8   kırık     fracture                           no  -- structural, not caries
    0   saglam    healthy                            n/a -- this is the negative, not a lesion

Only `çürük` is used as ground truth here. This is a narrower, more defensible scope than
"any finding" -- it means every unmatched GT lesion is unambiguously a caries lesion the
pipeline's caries branch should have flagged, not a küretaj or kanal marker the branch was
never trained to recognise.

**Each matching polygon is treated as one independent lesion instance** (not merged by FDI/
tooth the way `validate_fdi_assignment.py`'s `load_gt` does for numbering evaluation) -- two
çürük polygons on the same tooth are two lesions to localise, not one.

WHAT "AGREEMENT" MEANS HERE, PRECISELY
-----------------------------------------
The detector emits whole-tooth boxes; the caries branch classifies each whole-tooth crop.
There is no finer-grained localisation happening inside this pipeline than "which tooth".
So this metric is a TOOTH-LEVEL spatial correspondence check -- is the caries-positive verdict
on the tooth that actually has a lesion -- not a pixel-level segmentation-quality metric. That
is exactly the question §4.3.4 asks ("do the predicted diseased teeth spatially overlap the
expert lesion mask"), and it is stated plainly here so the number is never read as claiming
more than that.

MATCHING -- reused, not reimplemented
--------------------------------------
`iou()` and `match_gt_to_detections()` are imported directly from `validate_fdi_assignment.py`.
That greedy-IoU-with-centroid-fallback logic already solves the exact problem this task has --
a small lesion polygon inside a much larger tooth box, where plain IoU understates a correct
match -- and reusing it here means one proven implementation, not two independently-written
ones that could quietly disagree. `min_iou=0.30` is inherited from there, not re-tuned for
this script: it was chosen a priori on anatomy, and this file must not sweep it against this
evaluation set either.

THE ONE THING THIS METRIC CANNOT TELL YOU
--------------------------------------------
An UNMATCHED predicted-positive tooth is NOT evidence of a false positive. `disease/` labels
only teeth carrying a finding of SOME kind -- roughly 6 of ~30 teeth per image
(`compare_caries_gates.py`) -- so most teeth in any image are simply unannotated, not verified
healthy. A predicted-positive tooth with no nearby çürük polygon could be a real caries lesion
DENTEX never got around to annotating, or a genuine false positive, or a tooth carrying one of
the excluded finding types above. This script reports the unmatched-positive count as a
diagnostic, explicitly labelled as such, never as a precision figure -- that number already
exists, honestly caveated the same way, in `compare_caries_gates.py`.

Usage:
    python scripts/eval/lesion_localization.py
    python scripts/eval/lesion_localization.py --n 12 --save-viz
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.eval.validate_fdi_assignment import (  # noqa: E402
    LABEL_RE, iou, match_gt_to_detections)

DEF_DISEASE_DIR = Path.home() / "Downloads/Capstone/DENTEX/disease"
DEF_DETECTOR = REPO_ROOT / "models/06_yolo_detection_a100_run/best.pt"
DEF_CARIES_GATE = REPO_ROOT / "models/09_caries_gate_v3/caries_gate_v3.pth"
DEF_CARIES_SEVERITY = REPO_ROOT / "models/07_caries_cascade/phase2_final_bundle.pth"
DEF_OUT = REPO_ROOT / "outputs/lesion_localization"

TARGET_FINDING_ID = "1"  # çürük -- see the module docstring for why only this one


def _load_leaked():
    """Same exclusion list and key as validate_fdi_assignment.py / compare_caries_gates.py --
    this evaluates the same disease/ images, so the same leakage applies."""
    f = REPO_ROOT / "data/dentex/disease_leaked_images.json"
    return set(json.loads(f.read_text())["all_excluded"]) if f.exists() else set()


def load_lesion_gt(label_path):
    """
    DENTEX-specific. Returns one dict per çürük POLYGON (not merged by tooth), each with a
    bbox and centroid in the same UPRIGHT pixel coordinates the detector output is un-rotated
    into -- so no transform is needed before matching.

    Uses LABEL_RE (imported from validate_fdi_assignment.py) rather than a hand-rolled split,
    on purpose: that regex is the already-validated parser for this exact label format (0
    failures across 1,600 shapes, RESULTS_LOG), and every other DENTEX GT loader in this repo
    uses it. A second, independently-written parser here would be a second place for the two
    to quietly disagree.
    """
    import numpy as np
    d = json.loads(Path(label_path).read_text())
    lesions = []
    for s in d.get("shapes", []):
        m = LABEL_RE.match(s["label"])
        if not m or m.group(1) != TARGET_FINDING_ID:
            continue
        pts = np.array(s["points"], dtype=float)
        lesions.append({
            "fdi": m.group(3),
            "bbox": [float(pts[:, 0].min()), float(pts[:, 1].min()),
                     float(pts[:, 0].max()), float(pts[:, 1].max())],
            "centroid": [float(pts[:, 0].mean()), float(pts[:, 1].mean())],
        })
    return lesions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disease-dir", type=Path, default=DEF_DISEASE_DIR)
    ap.add_argument("--detector", type=Path, default=DEF_DETECTOR)
    ap.add_argument("--caries-gate", type=Path, default=DEF_CARIES_GATE)
    ap.add_argument("--caries-severity", type=Path, default=DEF_CARIES_SEVERITY)
    ap.add_argument("--min-iou", type=float, default=0.30,
                    help="inherited from validate_fdi_assignment.py, not re-tuned here")
    ap.add_argument("--n", type=int, default=None, help="limit to first N non-leaked images")
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    args = ap.parse_args()

    import cv2
    import torch
    from ultralytics import YOLO

    from src.classifiers import load_classifier, run_caries
    from src.orientation import detect_upright

    leaked = _load_leaked()
    labels = sorted(p for p in args.disease_dir.glob("label/*.json") if p.stem not in leaked)
    if args.n:
        labels = labels[:args.n]
    print(f"images: {len(labels)}  ({len(leaked)} excluded as training duplicates)")

    device = torch.device("cuda" if torch.cuda.is_available()
                          else "mps" if torch.backends.mps.is_available() else "cpu")
    det = YOLO(str(args.detector))
    gate, gate_cls = load_classifier(args.caries_gate, 2, device)
    sev, sev_cls = load_classifier(args.caries_severity, 2, device)
    if gate_cls and gate_cls != {"caries": 0, "no_caries": 1}:
        raise SystemExit(f"caries gate class order changed: {gate_cls}")
    if sev_cls and sev_cls != {"caries": 0, "deep_caries": 1}:
        raise SystemExit(f"caries severity class order changed: {sev_cls}")
    print(f"device={device}  gate={args.caries_gate.name}")

    n_lesions = n_matched = n_pred_pos = n_pred_pos_matched = n_images_with_lesions = 0
    per_image, flag_counts = [], Counter()

    for lp in labels:
        stem = lp.stem
        ip = args.disease_dir / "input" / f"{stem}.png"
        img = cv2.imread(str(ip))
        if img is None:
            continue
        gt = load_lesion_gt(lp)
        if not gt:
            continue
        n_images_with_lesions += 1

        boxes, _ = detect_upright(det, img, imgsz=1024, conf=0.25, iou=0.50, verbose=False)
        caries = run_caries(gate, sev, img, boxes, device) if boxes else []

        pos_idx = [i for i, c in enumerate(caries) if c["finding"] != "no_caries"]
        pos_dets = [{"bbox": boxes[i]} for i in pos_idx]

        matches = match_gt_to_detections(gt, pos_dets, min_iou=args.min_iou)
        matched_det_local = {di for di, _ in matches.values()}

        n_lesions += len(gt)
        n_matched += len(matches)
        n_pred_pos += len(pos_idx)
        n_pred_pos_matched += len(matched_det_local)

        # NOT "which findings went unmatched" -- that list would just repeat "caries" /
        # "deep_caries" by construction, since pos_idx is already filtered to exactly those.
        # Confidence is the informative field: a cluster of unmatched positives at high
        # confidence looks more like real, unannotated caries; at low confidence, more like
        # noise. Either way this is a hint for manual review, not a verdict -- see the
        # module docstring on why an unmatched positive is never a confirmed false positive.
        unmatched_conf = [round(caries[pos_idx[i]]["gate_confidence"], 3)
                          for i in range(len(pos_idx)) if i not in matched_det_local]
        per_image.append({
            "image": stem, "n_lesions": len(gt), "n_matched": len(matches),
            "n_predicted_positive": len(pos_idx),
            "n_predicted_positive_unmatched": len(unmatched_conf),
            "unmatched_positive_gate_confidence": unmatched_conf,
        })
        for c in caries:
            flag_counts.update(c["flags"])

    agreement = n_matched / n_lesions if n_lesions else 0.0
    pos_match_rate = n_pred_pos_matched / n_pred_pos if n_pred_pos else 0.0

    res = {
        "n_images": len(labels), "n_images_with_caries_lesions": n_images_with_lesions,
        "n_lesions": n_lesions, "n_lesions_matched": n_matched,
        "lesion_localization_agreement": round(agreement, 4),
        "n_predicted_positive_teeth": n_pred_pos,
        "n_predicted_positive_matched_to_a_lesion": n_pred_pos_matched,
        "predicted_positive_match_rate_DIAGNOSTIC_NOT_PRECISION": round(pos_match_rate, 4),
        "min_iou": args.min_iou, "target_finding": "çürük (caries) only, see module docstring",
        "caveat": "unmatched predicted-positive teeth are NOT confirmed false positives -- "
                 "disease/ annotates only ~6 of ~30 teeth per image (compare_caries_gates.py); "
                 "an unmatched positive may be real, unannotated caries.",
        "flag_counts": dict(flag_counts),
        "per_image": per_image,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "lesion_localization.json").write_text(json.dumps(res, indent=2) + "\n")

    print(f"\n{'='*66}")
    print(f"lesions (çürük polygons): {n_lesions}  across {n_images_with_lesions} images")
    print(f"lesion-localisation agreement: {n_matched}/{n_lesions} = {agreement:.1%}")
    print(f"predicted-positive teeth: {n_pred_pos}  "
          f"({n_pred_pos_matched} land on an annotated lesion = {pos_match_rate:.1%})")
    print("  ^ diagnostic only -- see 'caveat' in the JSON, this is not a precision figure")
    print(f"{'='*66}")
    print(f"-> {args.out}/lesion_localization.json")


if __name__ == "__main__":
    main()
