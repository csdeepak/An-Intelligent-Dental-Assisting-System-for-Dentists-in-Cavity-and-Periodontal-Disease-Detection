#!/usr/bin/env python3
"""
R4 -- Stages 5-6: the integration layer. One OPG in, one per-tooth JSON report out.

    python scripts/run_inference.py --image opg.png --output report.json
    python scripts/run_inference.py --image opg.png --output report.json --overlay viz.jpg

WHAT THIS IS
------------
The single entry point the project did not have. Four trained stages existed and were only
ever run in isolation, on their own curated crops; nothing composed them, so the pipeline's
end-to-end behaviour had never been observed. This is paper claim C3.

    Stage 1  YOLOv11l detection            -> tooth boxes, upright coordinates
    Stage 2  learned enumeration head      -> FDI code per tooth, one-to-one constrained
    Stage 3  caries LESION detector        -> no_caries | caries | deep_caries   (whole-image
                                               detection + argmax-containment onto tooth boxes;
                                               severity still graded on a TIGHT crop of flagged
                                               teeth. `--caries-method gate` reverts to the
                                               retained per-crop classifier -- see below)
    Stage 4  bone-loss cascade             -> normal | bone_loss + severity      (1.5x/2.0x)
    Stage 5  fusion, flags, assessability
    Stage 6  structured JSON (+ optional overlay)

EACH STAGE GETS ITS OWN CROP. That is not an implementation detail -- the three conventions
(1.0x tight, 1.5x/1.5x, 1.5x/2.0x) come from three different training pipelines, and crossing
them produces confident, plausible, wrong output with no error. See src/classifiers.py.

WHAT THIS REPORT IS NOT
-----------------------
Composing four independently-trained stages does not produce a clinically validated system,
and the numbers here are not a performance claim. Two limitations are structural and are
written into every report rather than left to a footnote:

  * ERROR PROPAGATION. Detector recall is 70.6% and Stage-2 FDI accuracy is 58.3% end-to-end
    (RESULTS_LOG 2026-08-27e, seg detector + head v2.0; it was 67.0% / 46.5% on the superseded
    bbox detector). A tooth that is missed is absent from the report entirely, and a tooth
    numbered wrongly attaches correct findings to the wrong tooth. Roughly two FDI codes in
    five are still expected to be wrong. `stage2_fdi_exact_end_to_end` is the authority.
  * THE CARIES BRANCH IS AN ADOPTED LESION DETECTOR, NOT A SOLVED PROBLEM. Adopted 4 Sep 2026
    (Lever B, RESULTS_LOG 2026-09-04b) because it decisively beats both the old per-crop gate
    AND an image-blind constant baseline -- on this project's six cohorts, that constant had
    tied or beaten the gate EVERYWHERE (`PAPER_MATERIAL.md` Sec 8.22/8.24/8.25). Pre-registered
    acceptance: beats the constant + the gate, CI excluding zero, on >=2 of 3 external cohorts
    at <=1.5x the constant's flagging rate. It cleared that on CariesXrays (+37/+12 pp) and
    Ningxia (+9/+10 pp). On DENTEX it is a statistical TIE with both (CI including zero) -- not
    a third win, and not reported as one. **This is real, measured progress on a problem five
    prior fix attempts on the gate could not move -- it is not "solved everywhere."** The
    retained gate path (`--caries-method gate`) still calls 19.1% of detected teeth carious
    against an 11.7% annotated floor at 0.40 held-out precision; pass it for reproducibility of
    every pre-4-Sep number.

Neither branch is fixable-to-perfect at this layer, and neither field is a diagnosis. They are
surfaced so the report cannot be quoted as more than it is.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# 1.1 (27 Aug 2026): per-tooth caries records gained `gate_confidence_calibrated` and the
# `caries_confidence_isotonic` flag. Additive only -- `gate_confidence` and every verdict
# are unchanged, so 1.0 consumers keep working. RESULTS_LOG 2026-08-27s.
SCHEMA_VERSION = "opg-report/1.1"

# Measured Stage-1/Stage-2 performance, stamped into every report's "limitations" block so a
# report always carries the accuracy of the pipeline that produced it.
#
# ** UPDATE THESE IF STAGE 1 OR STAGE 2 IS RETRAINED. ** They are constants, not live
# measurements, so nothing here will notice if they go stale -- every report would then
# understate or overstate its own reliability, silently. Current source of truth:
#   scripts/eval/validate_fdi_assignment.py --method head
#   -> outputs/stage2_reverify/stage2_summary_head.json   (recall, fdi_exact_of_all)
#   RESULTS_LOG 2026-08-22j (measurement), 2026-08-24b (byte-identical re-verification).
# RE-MEASURED 27 Aug 2026 against the seg detector, on the same 164 leak-free DENTEX images /
# 936 GT teeth, same conf 0.25 / NMS IoU 0.50 / imgsz 1024 / CCW rotation, same v2.0 head.
# RESULTS_LOG 2026-08-27e. These are the current pipeline's numbers.
STAGE1_DETECTOR_RECALL = 0.706        # = 661/936, seg detector
STAGE2_FDI_EXACT_END_TO_END = 0.583   # = 546/936, seg detector + head v2.0, Hungarian 1-to-1

# The superseded bbox detector, kept because every number published before 27 Aug used it.
# NOTE the control re-run of that same configuration on THIS machine gave 67.3% / 46.3%, not
# the 67.0% / 46.5% originally recorded — a ~3-tooth drift consistent with CPU-vs-GPU float
# differences and well inside the ~1-point run-to-run noise floor this project already measured
# (identical configs once differed by 9 teeth of 936, RESULTS_LOG 2026-08-25i). The +12-point
# gain above is an order of magnitude larger than that drift.
SUPERSEDED_STAGE1_RECALL = 0.670      # as originally published; 0.673 on this machine's re-run
SUPERSEDED_STAGE2_END_TO_END = 0.465  # as originally published; 0.463 on this machine's re-run

# Stage-1 detector — YOLOv11l-SEG, adopted 27 Aug 2026 by explicit user decision.
#
# ADOPTED FOR THE BOX GAIN, NOT BECAUSE THE PRE-REGISTERED BAR WAS MET. T0.6 §2 required BOTH
# box mAP@0.5 >= 0.75 AND mask mAP@0.5 >= 0.65 on the held-out test split. Box PASSED (0.8100,
# vs the superseded bbox detector's 0.7824 — +2.76 points on the same frozen split with an
# otherwise identical config). Mask FAILED (0.6383, short by 0.0117). The bar was NOT changed;
# adoption is a separate, dated human decision, recorded as such. RESULTS_LOG 2026-08-27b/d.
#
# Consequences, stated here because they are easy to miss:
#   - masks are NOT validated to the standard §2 asked for, so R2 (mask-aware cropping) stays
#     unwired; this model is used for its BOXES only, exactly like its predecessor;
#   - every DENTEX-measured downstream number is now stale — see the constants above.
# The bbox detector is retained, unchanged and hash-pinned, at models/06_yolo_detection_a100_run/.
DEF_DETECTOR = REPO_ROOT / "models/11_yolo_seg_tufts_r1/best.pt"
DETECTOR_TAG = "tooth-detector-seg-tufts-1024-v1.0"
# v2.0 = DENTEX + Tufts. Adopted 26 Aug 2026 for ROBUSTNESS, not in-domain accuracy:
# in-domain it is +0.11pp (inside the ~1pt noise floor), out-of-domain +21.5pp on Tufts.
# v1.0 (models/08_fdi_enumeration_head/) is retained unchanged — it is the head every
# Stage-2 number before this date was measured on. RESULTS_LOG 2026-08-25j.
DEF_FDI_HEAD = REPO_ROOT / "models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth"
# Caries Stage 3 -- LESION DETECTOR, adopted 4 Sep 2026 by the pre-registered Lever B rule.
#
# ADOPTED BECAUSE THE PRE-REGISTERED BAR WAS MET, not just because it looked better. Sec 6 of
# outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md (frozen BEFORE any of these numbers
# existed) required: beats an image-blind molar constant AND the gate, CI excluding zero, on
# >=2 of 3 external cohorts, at <=1.5x the constant's flagging rate. Measured (paired cluster
# bootstrap, 10k resamples, RESULTS_LOG 2026-09-04b):
#     cohort        gate v3.0   constant   lesion detector (this model)
#     DENTEX          44.3%      48.9%     45.5% [40.9,50.1] -- TIE (CI incl. 0), fails Sec 6
#     CariesXrays      31.7%      56.2%     68.4% [66.4,70.4] -- PASS (CI excl. 0, both deltas)
#     Ningxia          40.8%      39.9%     50.0% [46.3,53.9] -- PASS (CI excl. 0, both deltas)
# 2 of 3 -> Sec 6 met. Trained on CariesXrays + DENTEX-domain caries boxes, per-corpus balanced
# (`models/16_lever_b_pooled/`, RESULTS_LOG 2026-09-04b) -- the DENTEX data is what closed the
# out-of-domain gap the CariesXrays-only arm (B-single, `models/14`) could not (it lost DENTEX
# decisively, -40/-36 pp, and lost Ningxia too, -16/-17 pp -- see RESULTS_LOG 2026-09-04).
#
# Mechanism differs from every other stage here: this is a DETECTOR (whole image in, lesion
# boxes out), not a per-crop classifier. `src.classifiers.run_caries_lesion_detector` maps each
# lesion box to the tooth box it overlaps most (argmax containment), then reuses the existing
# severity classifier on flagged teeth only -- severity was never part of what Lever B tested.
#
# Consequences, stated here because they are easy to miss:
#   - single-class ("decay") -- it has no native severity signal of its own; `gate_confidence`
#     on a positive tooth is a DETECTION score, not a softmax over {caries, no_caries}, and is
#     0.0 (not "0% confidence healthy") on a negative tooth. See the flag
#     `gate_confidence_is_detection_not_softmax`.
#   - DENTEX is a statistical TIE, not a win -- do not read this as beating the gate everywhere.
#   - the isotonic confidence calibrator (models/09/isotonic_calibrator.json) was fit for the
#     GATE's score distribution and is not applied here; `gate_confidence_calibrated` is absent
#     from lesion-detector reports (present, as before, under --caries-method gate).
# The gate is RETAINED, unchanged and fully functional, via --caries-method gate -- every
# pre-4-Sep caries number in this project was measured on it and remains reproducible.
DEF_CARIES_LESION_MODEL = REPO_ROOT / "models/16_lever_b_pooled/lever_b_pooled_yolo11l-2/weights/best.pt"
CARIES_LESION_CONF = 0.25   # frozen per the pre-registration -- never tuned on any cohort
DEF_CARIES_GATE = REPO_ROOT / "models/09_caries_gate_v3/caries_gate_v3.pth"
DEF_CARIES_SEVERITY = REPO_ROOT / "models/07_caries_cascade/phase2_final_bundle.pth"

# Report-limitations text, keyed by which caries mechanism actually ran -- read by build_report
# so a report never carries the OTHER method's caveat by accident.
CARIES_METHOD_CAVEATS = {
    "lesion-detector": (
        "Stage 3 is the lesion detector (models/16_lever_b_pooled), adopted 4 Sep 2026 -- see "
        "the DEF_CARIES_LESION_MODEL comment above and RESULTS_LOG 2026-09-04b for the full "
        "pre-registered verdict. It decisively beats both the retained gate and an image-blind "
        "constant on 2 of 3 external cohorts (CariesXrays, Ningxia); on DENTEX it is a "
        "statistical TIE with both, not a win. IMPROVED ON TWO COHORTS, NOT SOLVED EVERYWHERE. "
        "Do not read a caries field here as a diagnosis."),
    "gate": (
        "The gate is caries-gate-resnet18-v3.0, retrained with a real negative class "
        "(5,366 healthy teeth). In-pipeline it calls 19.1% of detected teeth carious "
        "against an 11.7% annotated floor -- 1.6x, down from 7.3x for the legacy gate "
        "(RESULTS_LOG 2026-08-25a). It is IMPROVED, NOT SOLVED: precision on the "
        "held-out test split is 0.40, so roughly six of every ten positives are wrong. "
        "Do not read a caries field here as a diagnosis. Superseded as the pipeline default "
        "4 Sep 2026 by the lesion detector (RESULTS_LOG 2026-09-04b); retained via "
        "--caries-method gate for reproducibility of every number measured before that date."),
}
CARIES_NEGATIVE_ASSUMPTION = {
    "lesion-detector": (
        "A negative tooth here means no lesion box was DETECTED overlapping it -- bounded by "
        "the detector's own recall, not by a training-label assumption the way the gate's "
        "negative class was. A lesion the detector missed is a false negative exactly like any "
        "other detection miss; unmeasurable per-tooth without an exhaustively-annotated cohort."),
    "gate": (
        "The gate's healthy class comes from teeth carrying no disease annotation in "
        "DENTEX, which annotates only diseased teeth. That is absence of evidence: any "
        "lesion the annotators missed is a false negative in training and in the "
        "reported precision. Unmeasurable inside DENTEX."),
}
DEF_BONE_LOSS = REPO_ROOT / "models/03_bone_loss_model_training_notebook_models/bone_loss_resnet18_best.pth"
DEF_BONE_SEVERITY = REPO_ROOT / "models/04_bone_loss_severity_notebook_models/bone_loss_severity_resnet18_best.pth"

# A tooth is reported as assessable only if Stage 2 is confident about WHICH tooth it is.
# Findings on a misnumbered tooth are worse than no findings, so this gates the whole record.
#
# Deliberately the SAME value as src.fdi_head_inference.LOW_CONFIDENCE, not a second knob
# tuned here: a tooth the numbering head calls low-confidence is exactly a tooth whose
# findings cannot be attributed. Introducing an independent threshold would mean two numbers
# to justify instead of one. Like that one, it is fixed a priori and must not be swept
# against an evaluation set.
ASSESSABILITY_MIN_FDI_CONFIDENCE = 0.30


def build_report(image_path, img_bgr, boxes, confs, fdi_assign, caries, bone, meta):
    """Stage 5-6: fuse the per-stage outputs into one record per detected tooth."""
    # Every stage returns one entry per box, in box order, and this function fuses them
    # positionally. If any stage ever returns a filtered list instead, the fusion would
    # silently attach one tooth's findings to another -- checked rather than assumed.
    n = len(boxes)
    if not (len(confs) == len(fdi_assign) == len(caries) == len(bone) == n):
        raise ValueError(
            f"stage outputs misaligned: boxes={n} confs={len(confs)} "
            f"fdi={len(fdi_assign)} caries={len(caries)} bone={len(bone)}")
    teeth = []
    for i in range(len(boxes)):
        a = fdi_assign[i]
        flags = list(a.get("flags", []))
        assessable, reasons = True, []
        if a.get("fdi") is None:
            assessable = False
            reasons.append("no_fdi_code_assigned")
        if a.get("confidence", 0.0) < ASSESSABILITY_MIN_FDI_CONFIDENCE:
            assessable = False
            reasons.append("fdi_confidence_below_threshold")
        teeth.append({
            "detection_index": i,
            "bbox_xyxy": [round(float(v), 1) for v in boxes[i]],
            "detection_confidence": round(float(confs[i]), 4),
            "fdi": a.get("fdi"),
            "quadrant": a.get("quadrant"),
            "position": a.get("position"),
            "fdi_confidence": a.get("confidence"),
            "fdi_flags": flags,
            "caries": caries[i],
            "bone_loss": bone[i],
            "assessable": assessable,
            "not_assessable_reasons": reasons,
        })
    teeth.sort(key=lambda t: (t["fdi"] is None, t["fdi"] or 0))

    H, W = img_bgr.shape[:2]
    codes = [t["fdi"] for t in teeth if t["fdi"] is not None]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "image": {"path": str(image_path), "width": W, "height": H},
        "summary": {
            "teeth_detected": len(teeth),
            "teeth_assessable": sum(t["assessable"] for t in teeth),
            "distinct_fdi_codes": len(set(codes)),
            "duplicate_fdi_codes": len(codes) - len(set(codes)),
            "caries_positive": sum(t["caries"]["finding"] != "no_caries" for t in teeth),
            "bone_loss_positive": sum(t["bone_loss"]["finding"] == "bone_loss" for t in teeth),
        },
        "teeth": teeth,
        "models": meta,
        "limitations": {
            "stage1_detector_recall": STAGE1_DETECTOR_RECALL,
            "stage2_fdi_exact_end_to_end": STAGE2_FDI_EXACT_END_TO_END,
            "interpretation": (
                "Detection recall and FDI accuracy are measured on DENTEX disease/ "
                "(164 leak-free images, 936 GT teeth) against the CURRENT seg detector, "
                "re-measured 27 Aug 2026 (RESULTS_LOG 2026-08-27e). The superseded bbox "
                "detector scored 67.3% / 46.3% on the same harness. "
                "A missed tooth is absent "
                "from this report; a misnumbered tooth carries correct findings under the "
                "wrong FDI code. Expect roughly half the codes in this report to be wrong."),
            "caries_method_caveat": (
                CARIES_METHOD_CAVEATS["lesion-detector"] if meta["caries"].get("method") ==
                "lesion-detector" else CARIES_METHOD_CAVEATS["gate"]),
            "caries_presumed_negative_assumption": (
                CARIES_NEGATIVE_ASSUMPTION["lesion-detector"] if meta["caries"].get("method") ==
                "lesion-detector" else CARIES_NEGATIVE_ASSUMPTION["gate"]),
            "bone_loss_domain_shift": (
                "The bone-loss models were trained on TUFTS radiographs and are applied here to "
                "whatever image is supplied; on DENTEX they fire on 0.7% of teeth (2/299) with "
                "0.93-0.999 confidence in 'normal'. The branch is close to inert out of its "
                "training domain -- the opposite failure to the caries gate. A 'normal' "
                "bone-loss field is therefore weak evidence, not a negative finding."),
            "not_clinically_validated": True,
        },
    }


def draw_overlay(img_bgr, report, out_path):
    """Blue = assessable, orange = flagged, red = not assessable. Label is FDI + findings."""
    import cv2
    viz = img_bgr.copy()
    for t in report["teeth"]:
        x1, y1, x2, y2 = [int(v) for v in t["bbox_xyxy"]]
        if not t["assessable"]:
            colour = (60, 60, 220)
        elif t["fdi_flags"] or t["caries"]["finding"] != "no_caries" or \
                t["bone_loss"]["finding"] == "bone_loss":
            colour = (0, 165, 255)
        else:
            colour = (200, 120, 0)
        cv2.rectangle(viz, (x1, y1), (x2, y2), colour, 2)
        bits = [str(t["fdi"]) if t["fdi"] else "??"]
        if t["caries"]["finding"] != "no_caries":
            bits.append(t["caries"]["finding"][:4].upper())
        if t["bone_loss"]["finding"] == "bone_loss":
            bits.append("BL-" + (t["bone_loss"]["severity"] or "?")[:3])
        cv2.putText(viz, " ".join(bits), (x1, max(14, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 1, cv2.LINE_AA)
    cv2.imwrite(str(out_path), viz)


def pick_device():
    import torch
    return torch.device("cuda" if torch.cuda.is_available()
                        else "mps" if torch.backends.mps.is_available() else "cpu")


def load_models(detector=DEF_DETECTOR, fdi_head=DEF_FDI_HEAD, caries_gate=DEF_CARIES_GATE,
                caries_severity=DEF_CARIES_SEVERITY, caries_lesion_model=DEF_CARIES_LESION_MODEL,
                bone_loss=DEF_BONE_LOSS, bone_severity=DEF_BONE_SEVERITY, device=None):
    """
    Load all seven checkpoints once. Both the CLI and any other caller (the Streamlit app) use
    this SAME function -- loading is the slow, one-time part (~seconds), and a second
    independently-written loader would be a second place for the class_to_idx safety check
    below to be forgotten.

    Loads BOTH caries mechanisms (lesion detector + the retained gate) unconditionally, same as
    every other stage here -- run_pipeline's `caries_method` picks which one actually runs, and
    a caller can switch methods without a second, separate load_models() call.

    Returns (models_dict, device, weight_paths_dict) -- weight_paths is kept separately so
    build_report's `meta` can cite exactly what was loaded, unchanged from before this
    refactor.
    """
    import torch  # noqa: F401  (imported here so callers need not import torch themselves)
    from ultralytics import YOLO

    from src.classifiers import load_classifier
    from src.fdi_head_inference import load_head

    paths = {"detector": Path(detector), "fdi_head": Path(fdi_head),
             "caries_gate": Path(caries_gate), "caries_severity": Path(caries_severity),
             "caries_lesion_model": Path(caries_lesion_model),
             "bone_loss": Path(bone_loss), "bone_severity": Path(bone_severity)}
    for name, p in paths.items():
        if not p.exists():
            raise SystemExit(f"missing model weights: {p}")

    device = device or pick_device()
    m = {
        "detector": YOLO(str(paths["detector"])),
        "head": load_head(paths["fdi_head"], device),
        "caries_lesion_model": YOLO(str(paths["caries_lesion_model"])),
    }
    m["gate"], gate_cls = load_classifier(paths["caries_gate"], 2, device)
    m["csev"], csev_cls = load_classifier(paths["caries_severity"], 2, device)
    m["bbin"], _ = load_classifier(paths["bone_loss"], 2, device)
    m["bsev"], _ = load_classifier(paths["bone_severity"], 3, device)

    # The two caries CLASSIFIER checkpoints carry their own class_to_idx. Assert it matches the
    # order src/classifiers.py assumes, rather than trusting that it does -- an inverted index
    # here would report every healthy tooth as carious and still look like a working pipeline.
    # (The lesion detector has no class_to_idx to check -- it is single-class.)
    if gate_cls and gate_cls != {"caries": 0, "no_caries": 1}:
        raise SystemExit(f"caries gate class_to_idx changed: {gate_cls}")
    if csev_cls and csev_cls != {"caries": 0, "deep_caries": 1}:
        raise SystemExit(f"caries severity class_to_idx changed: {csev_cls}")

    return m, device, paths


def run_pipeline(img_bgr, models, device, paths, image_label="image", imgsz=1024, conf=0.25,
                 det_iou=0.50, one_to_one=True, verbose=True, caries_method="lesion-detector",
                 caries_lesion_conf=CARIES_LESION_CONF):
    """
    Stages 1-6 on an already-loaded image, using already-loaded models. This is the function
    both `main()` and the Streamlit app call -- one code path, so a fix or a limitation update
    reaches both automatically. Returns the report dict; writes nothing to disk.

    `caries_method` -- "lesion-detector" (the pipeline default since 4 Sep 2026, Lever B,
    RESULTS_LOG 2026-09-04b) or "gate" (the retained per-crop classifier, for reproducing any
    number measured before that date). See the DEF_CARIES_LESION_MODEL comment above.
    """
    from src.classifiers import (BONE_LOSS_SEVERITY_CLASSES, run_bone_loss, run_caries,
                                 run_caries_lesion_detector)
    from src.fdi_head_inference import assign_fdi_head
    from src.orientation import detect_upright

    def log(msg):
        if verbose:
            print(msg)

    log("stage 1 — detection …")
    boxes, confs = detect_upright(models["detector"], img_bgr, imgsz=imgsz, conf=conf,
                                  iou=det_iou, verbose=False)
    log(f"  {len(boxes)} teeth detected")
    if not boxes:
        log("  no teeth detected — writing an empty report")

    log("stage 2 — FDI enumeration …")
    fdi_assign = assign_fdi_head(models["head"], img_bgr, boxes, device, one_to_one=one_to_one)

    if caries_method == "gate":
        log("stage 3 — caries GATE (tight crops, retained pre-4-Sep default) …")
        caries = run_caries(models["gate"], models["csev"], img_bgr, boxes, device)
        caries_meta = {
            "method": "gate", "weights": str(paths["caries_gate"]),
            "severity_weights": str(paths["caries_severity"]),
            "tag": "caries-cascade-resnet18-v1.0", "crop_expand": [1.0, 1.0],
            "confidence_calibration": (
                "isotonic, fitted on the crops_v3_phase1 val split; applied to "
                "gate_confidence_calibrated ONLY. Verdicts remain argmax on raw "
                "logits. Test ECE 0.136 -> 0.043. RESULTS_LOG 2026-08-27s."),
        }
    elif caries_method == "lesion-detector":
        log("stage 3 — caries LESION DETECTOR (whole image, adopted 4 Sep 2026) …")
        caries = run_caries_lesion_detector(models["caries_lesion_model"], models["csev"],
                                            img_bgr, boxes, device, conf=caries_lesion_conf)
        caries_meta = {
            "method": "lesion-detector", "weights": str(paths["caries_lesion_model"]),
            "severity_weights": str(paths["caries_severity"]),
            "tag": "caries-lesion-detector-yolo11l-leverb-bpooled-v1.0",
            "lesion_conf": caries_lesion_conf,
            "adopted": "4 Sep 2026, Lever B Sec 6 -- RESULTS_LOG 2026-09-04b",
            "confidence_calibration": (
                "NOT applied -- the isotonic calibrator was fit for the gate's score "
                "distribution. gate_confidence here is a raw detection score, not a softmax."),
        }
    else:
        raise ValueError(f"unknown caries_method: {caries_method!r} (expected "
                         f"'lesion-detector' or 'gate')")

    log("stage 4 — bone-loss cascade (1.5x/2.0x crops) …")
    bone = run_bone_loss(models["bbin"], models["bsev"], img_bgr, boxes, device)

    meta = {
        "detector": {"weights": str(paths["detector"]), "tag": DETECTOR_TAG,
                     "imgsz": imgsz, "conf": conf, "nms_iou": det_iou,
                     "input_rotation": "90 deg counter-clockwise (src/orientation.py)"},
        "fdi_head": {"weights": str(paths["fdi_head"]), "tag": "fdi-enumeration-head-resnet18-v1.0",
                     "one_to_one": one_to_one, "crop_expand": [1.5, 1.5]},
        "caries": caries_meta,
        "bone_loss": {"binary": str(paths["bone_loss"]), "severity": str(paths["bone_severity"]),
                      "crop_expand": [1.5, 2.0], "severity_classes": BONE_LOSS_SEVERITY_CLASSES,
                      "tag_binary": "bone-loss-binary-resnet18-v1.0",
                      "tag_severity": "bone-loss-severity-resnet18-v1.0",
                      "class_order_note": (
                          "binary class order [normal, bone_loss] confirmed two independent "
                          "ways (27 Aug 2026): FocalLoss alpha ratio 2.258/0.642 = 3.5171 "
                          "matches the class-count ratio 2500/711 = 3.5162 to 0.03%, so index "
                          "0 is the majority class; and training_summary.txt labels its own "
                          "scores 'F1 Normal (cls 0)' / 'F1 Diseased (cls 1)'. The checkpoint "
                          "still carries no class_to_idx -- the order is corroborated, not "
                          "stored. See models/03_.../run_summary.txt.")},
    }

    log("stage 5–6 — fusion and report …")
    return build_report(image_label, img_bgr, boxes, confs, fdi_assign, caries, bone, meta)


def main():
    ap = argparse.ArgumentParser(description="Run the full OPG pipeline on one radiograph")
    ap.add_argument("--image", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("report.json"))
    ap.add_argument("--overlay", type=Path, default=None, help="also write an annotated JPG")
    ap.add_argument("--detector", type=Path, default=DEF_DETECTOR)
    ap.add_argument("--fdi-head", type=Path, default=DEF_FDI_HEAD)
    ap.add_argument("--caries-gate", type=Path, default=DEF_CARIES_GATE)
    ap.add_argument("--caries-severity", type=Path, default=DEF_CARIES_SEVERITY)
    ap.add_argument("--caries-lesion-model", type=Path, default=DEF_CARIES_LESION_MODEL)
    ap.add_argument("--caries-method", choices=["lesion-detector", "gate"],
                    default="lesion-detector",
                    help="Stage-3 mechanism. lesion-detector = the pipeline default since "
                         "4 Sep 2026 (Lever B, RESULTS_LOG 2026-09-04b); gate = the retained "
                         "pre-4-Sep per-crop classifier, for reproducing older numbers.")
    ap.add_argument("--caries-lesion-conf", type=float, default=CARIES_LESION_CONF,
                    help="frozen per the pre-registration -- not tuned on any cohort")
    ap.add_argument("--bone-loss", type=Path, default=DEF_BONE_LOSS)
    ap.add_argument("--bone-severity", type=Path, default=DEF_BONE_SEVERITY)
    ap.add_argument("--conf", type=float, default=0.25, help="detector confidence threshold")
    ap.add_argument("--imgsz", type=int, default=1024, help="detector input size (frozen at 1024)")
    ap.add_argument("--det-iou", type=float, default=0.50, help="detector NMS IoU")
    ap.add_argument("--no-one-to-one", action="store_true",
                    help="ablation: plain argmax FDI, which can emit duplicate codes")
    args = ap.parse_args()

    import cv2

    img = cv2.imread(str(args.image))
    if img is None:
        raise SystemExit(f"cannot read image: {args.image}")

    models, device, paths = load_models(
        detector=args.detector, fdi_head=args.fdi_head, caries_gate=args.caries_gate,
        caries_severity=args.caries_severity, caries_lesion_model=args.caries_lesion_model,
        bone_loss=args.bone_loss, bone_severity=args.bone_severity)
    print(f"device={device}   image={args.image.name}  {img.shape[1]}x{img.shape[0]}"
          f"   caries_method={args.caries_method}")

    report = run_pipeline(img, models, device, paths, image_label=str(args.image),
                          imgsz=args.imgsz, conf=args.conf, det_iou=args.det_iou,
                          one_to_one=not args.no_one_to_one, caries_method=args.caries_method,
                          caries_lesion_conf=args.caries_lesion_conf)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")

    s = report["summary"]
    print(f"\n  teeth detected {s['teeth_detected']}   assessable {s['teeth_assessable']}"
          f"   distinct FDI {s['distinct_fdi_codes']}   duplicates {s['duplicate_fdi_codes']}")
    print(f"  caries-positive {s['caries_positive']}   bone-loss-positive {s['bone_loss_positive']}")
    print(f"  -> {args.output}")
    if args.overlay:
        draw_overlay(img, report, args.overlay)
        print(f"  -> {args.overlay}")
    # DERIVED from the constant, never hardcoded: this line still said "46.5%" a full day
    # after STAGE2_FDI_EXACT_END_TO_END was set to 0.583 on 27 Aug, so the deployed demo
    # printed a superseded number to users while the JSON it wrote beside it was correct.
    # A literal in a print() is a second source of truth. RESULTS_LOG 2026-08-27m.
    _wrong = 1.0 - STAGE2_FDI_EXACT_END_TO_END
    print("")
    print(f"  NOTE: ~{_wrong:.0%} of FDI codes are expected wrong "
          f"(Stage 2 = {STAGE2_FDI_EXACT_END_TO_END:.1%} end-to-end). Caries "
          f"({args.caries_method}) is improved, not solved -- see report['limitations'].")


if __name__ == "__main__":
    main()
