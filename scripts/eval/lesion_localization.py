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
raster segmentation masks instead.

**CORRECTED 27 Aug 2026 -- the paragraph that used to stand here was wrong, and it is kept
in corrected form rather than deleted because the error is instructive.** It claimed
`load_lesion_gt` was "deliberately the one function that would need a Ningxia-specific
sibling; nothing else in this file assumes the DENTEX format." **Two things assume it, and
the second is the substantive one:**

  1. the GT format (polygons vs raster masks) -- which is what that sentence anticipated; and
  2. **the matching criterion**, which it did not. Ningxia caries lesions are tiny focal blobs,
     89-3,090 px, against a ~25,000 px tooth box: a lesion sitting ENTIRELY inside the correct
     tooth scores IoU 0.015-0.124, **every one of them below this file's 0.30 threshold**.
     Reusing this matcher unchanged on Ningxia would have reported ~0% agreement and read as
     catastrophic domain-shift failure, when it would have been a pure artefact of the
     criterion.

Ningxia is therefore served by `ningxia_external.py`, which matches caries by **centroid
containment** and scores periodontitis by affected-tooth sensitivity instead -- a diffuse band
of ~365,000 px is not the same kind of object as a focal spot and cannot share a metric.
`RESULTS_LOG.md` 2026-08-25d. The lesson worth carrying: **a claim about what does and does not
transfer is a hypothesis until a real file from the other dataset has been opened.** That
correction was written into `ningxia_external.py` on 25 Aug but not back into this file, so the
disproven sentence survived here for two days.

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
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scripts.eval.validate_fdi_assignment import (  # noqa: E402
    LABEL_RE, iou, match_gt_to_detections)

DEF_DISEASE_DIR = Path.home() / "Downloads/Capstone/DENTEX/disease"
# Tracks the live pipeline rather than a frozen snapshot -- same fix as ningxia_external.py
# (27 Aug 2026). This default was models/06 (the superseded bbox detector), which is why the
# 42.6% agreement figure quietly became an old-detector number when the Stage-1 default
# changed. To reproduce the original, pass it explicitly:
#   --detector models/06_yolo_detection_a100_run/best.pt
from run_inference import DEF_DETECTOR  # noqa: E402
DEF_CARIES_GATE = REPO_ROOT / "models/09_caries_gate_v3/caries_gate_v3.pth"
DEF_CARIES_SEVERITY = REPO_ROOT / "models/07_caries_cascade/phase2_final_bundle.pth"
DEF_FDI_HEAD = REPO_ROOT / "models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth"
DEF_OUT = REPO_ROOT / "outputs/lesion_localization"

TARGET_FINDING_ID = "1"  # çürük -- see the module docstring for why only this one


def _sha256(path):
    """Hash a weight file so a results JSON can never be confused with another run's."""
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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
    ap.add_argument("--decision", choices=["pipeline", "constant-molars", "all-teeth",
                                           "lesion-detector"],
                    default="pipeline",
                    help="what decides a tooth is diseased. See CONSTANT ARMS below. "
                         "lesion-detector runs a caries-lesion YOLO model instead of the gate "
                         "(Lever B), scored via argmax-containment onto detected tooth boxes.")
    ap.add_argument("--fdi-head", type=Path, default=DEF_FDI_HEAD,
                    help="only used by --decision constant-molars, to know which teeth are molars")
    ap.add_argument("--lesion-model", type=Path, default=None,
                    help="required for --decision lesion-detector (Lever B)")
    ap.add_argument("--lesion-conf", type=float, default=0.25,
                    help="frozen per PRE_REGISTRATION.md Sec 7 risk 4 -- not tuned on any cohort")
    args = ap.parse_args()

    # ------------------------------------------------------------------ CONSTANT ARMS
    # Added 28 Aug 2026, because the C1 comparison found that an image-blind constant -- a fixed
    # list of the eight first and second molars -- scores F1 0.320 on tooth-level FDI-set
    # prediction against this pipeline's 0.294 (RESULTS_LOG 2026-08-28b). Caries in DENTEX is
    # overwhelmingly molar, so that metric is base-rate dominated.
    #
    # The obvious hope was that THIS metric is immune because it requires spatial correspondence.
    # That hope is not self-evidently true and is therefore tested rather than asserted: a
    # constant that flags eight real detected tooth boxes does localise, in the only sense this
    # pipeline localises anything (tooth-level). So the constant is run through the identical
    # matcher and reported beside the pipeline.
    #
    # `all-teeth` is the stress test that matters. `lesion_localization_agreement` is RECALL over
    # lesions with no negative class, so flagging more teeth can only help it -- flagging every
    # detected tooth is its ceiling. If the pipeline does not clearly beat that ceiling on the
    # PAIR (agreement AND predicted-positive match rate), then this metric is no better than the
    # one it was meant to replace, and the paper must say so.
    MOLAR_CONSTANT = {"16", "17", "26", "27", "36", "37", "46", "47"}

    import cv2
    import torch
    from ultralytics import YOLO

    from src.classifiers import (lesion_preds_to_tooth_idx, load_classifier, run_caries,
                                 run_lesion_detector_raw)
    from src.fdi_head_inference import assign_fdi_head
    from src.orientation import detect_upright

    leaked = _load_leaked()
    labels = sorted(p for p in args.disease_dir.glob("label/*.json") if p.stem not in leaked)
    if args.n:
        labels = labels[:args.n]
    print(f"images: {len(labels)}  ({len(leaked)} excluded as training duplicates)")

    device = torch.device("cuda" if torch.cuda.is_available()
                          else "mps" if torch.backends.mps.is_available() else "cpu")
    det = YOLO(str(args.detector))

    lesion_model = gate = sev = None
    if args.decision == "lesion-detector":
        if not args.lesion_model:
            raise SystemExit("--decision lesion-detector requires --lesion-model")
        lesion_model = YOLO(str(args.lesion_model))
        print(f"device={device}  lesion_model={args.lesion_model.name} "
              f"conf={args.lesion_conf} (frozen)")
    else:
        gate, gate_cls = load_classifier(args.caries_gate, 2, device)
        sev, sev_cls = load_classifier(args.caries_severity, 2, device)
        if gate_cls and gate_cls != {"caries": 0, "no_caries": 1}:
            raise SystemExit(f"caries gate class order changed: {gate_cls}")
        if sev_cls and sev_cls != {"caries": 0, "deep_caries": 1}:
            raise SystemExit(f"caries severity class order changed: {sev_cls}")
        print(f"device={device}  gate={args.caries_gate.name}")
    fdi_head = None
    if args.decision == "constant-molars":
        from src.fdi_head_inference import assign_fdi_head, load_head
        fdi_head = load_head(args.fdi_head, device)
        print(f"  constant arm: flagging {sorted(MOLAR_CONSTANT)} on every image")
    elif args.decision == "all-teeth":
        print("  constant arm: flagging EVERY detected tooth (metric ceiling)")

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
        caries = run_caries(gate, sev, img, boxes, device) if (boxes and gate) else []

        if args.decision == "pipeline":
            pos_idx = [i for i, c in enumerate(caries) if c["finding"] != "no_caries"]
        elif args.decision == "all-teeth":
            pos_idx = list(range(len(boxes)))
        elif args.decision == "lesion-detector":
            # Lever B: NOT detect_upright -- see run_lesion_detector_raw's docstring
            # (src/classifiers.py) -- the lesion model expects the plain upright image.
            lesion_preds = run_lesion_detector_raw(lesion_model, img, conf=args.lesion_conf) if boxes else []
            pos_idx, _ = lesion_preds_to_tooth_idx(lesion_preds, boxes) if lesion_preds else ([], {})
        else:                                    # constant-molars -- the image is never read
            assigns = assign_fdi_head(fdi_head, img, boxes, device, one_to_one=True) if boxes else []
            pos_idx = [i for i, a in enumerate(assigns)
                       if str(a.get("fdi")) in MOLAR_CONSTANT]
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
        # Only meaningful for the gate arm (pipeline) -- the other arms have no per-tooth
        # confidence score to report (a constant reads no pixels; the lesion detector's score
        # lives on the lesion box, not the tooth verdict), so the field is left empty for them.
        unmatched_conf = ([round(caries[pos_idx[i]]["gate_confidence"], 3)
                           for i in range(len(pos_idx)) if i not in matched_det_local]
                          if args.decision == "pipeline" else [])
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

    weights = {"detector": str(args.detector), "detector_sha256": _sha256(args.detector)}
    if args.decision == "lesion-detector":
        weights["lesion_model"] = str(args.lesion_model)
        weights["lesion_model_sha256"] = _sha256(args.lesion_model)
        weights["lesion_conf"] = args.lesion_conf
    else:
        weights["caries_gate"] = str(args.caries_gate)
        weights["caries_severity"] = str(args.caries_severity)

    res = {
        "decision": args.decision,
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
        # Which weights produced this file. Added 27 Aug 2026: without it, two result
        # files are structurally identical and distinguishable only by the output
        # directory someone happened to name -- the same provenance gap that let the
        # 42.6% figure become a stale old-detector number without anyone noticing.
        "weights": weights,
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
