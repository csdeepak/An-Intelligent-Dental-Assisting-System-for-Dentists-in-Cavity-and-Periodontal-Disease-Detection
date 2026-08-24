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
    Stage 3  caries cascade                -> no_caries | caries | deep_caries   (TIGHT crop)
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

  * ERROR PROPAGATION. Detector recall is 67.0% and Stage-2 FDI accuracy is 46.5% end-to-end
    (RESULTS_LOG 2026-08-22j). A tooth that is missed is absent from the report entirely, and
    a tooth numbered wrongly attaches correct findings to the wrong tooth. Roughly half the
    FDI codes in any report are expected to be wrong. `stage2_fdi_exact_end_to_end` says so.
  * THE CARIES GATE IS OUT OF DISTRIBUTION HERE. Its `no_caries` class contains no healthy
    teeth (it is Impacted + Periapical Lesion), while this pipeline feeds it every tooth the
    detector finds. It will over-call. Every caries prediction carries
    `gate_out_of_distribution`.

Neither is fixable at this layer. They are surfaced so the report cannot be quoted as more
than it is.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

SCHEMA_VERSION = "opg-report/1.0"

# Measured Stage-1/Stage-2 performance, stamped into every report's "limitations" block so a
# report always carries the accuracy of the pipeline that produced it.
#
# ** UPDATE THESE IF STAGE 1 OR STAGE 2 IS RETRAINED. ** They are constants, not live
# measurements, so nothing here will notice if they go stale -- every report would then
# understate or overstate its own reliability, silently. Current source of truth:
#   scripts/eval/validate_fdi_assignment.py --method head
#   -> outputs/stage2_reverify/stage2_summary_head.json   (recall, fdi_exact_of_all)
#   RESULTS_LOG 2026-08-22j (measurement), 2026-08-24b (byte-identical re-verification).
STAGE1_DETECTOR_RECALL = 0.670        # = 0.6699, 164 leak-free DENTEX images, 936 GT teeth
STAGE2_FDI_EXACT_END_TO_END = 0.465   # = 0.4647, same run

DEF_DETECTOR = REPO_ROOT / "models/06_yolo_detection_a100_run/best.pt"
DEF_FDI_HEAD = REPO_ROOT / "models/08_fdi_enumeration_head/enumeration_head_best.pth"
DEF_CARIES_GATE = REPO_ROOT / "models/07_caries_cascade/final_model.pth"
DEF_CARIES_SEVERITY = REPO_ROOT / "models/07_caries_cascade/phase2_final_bundle.pth"
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
                "(164 leak-free images, RESULTS_LOG 2026-08-22j). A missed tooth is absent "
                "from this report; a misnumbered tooth carries correct findings under the "
                "wrong FDI code. Expect roughly half the codes in this report to be wrong."),
            "caries_gate_out_of_distribution": (
                "The caries gate's negative class is Impacted + Periapical Lesion and contains "
                "no healthy teeth, while this pipeline feeds it every detected tooth. MEASURED "
                "over 12 leak-free DENTEX images (299 detected teeth, RESULTS_LOG 2026-08-24f): "
                "it calls 84.9% of teeth carious against 35 annotated carious teeth -- roughly a "
                "7x over-call. An 85% caries rate is not clinically plausible. Treat every "
                "caries field in this report as uncalibrated."),
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


def main():
    ap = argparse.ArgumentParser(description="Run the full OPG pipeline on one radiograph")
    ap.add_argument("--image", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("report.json"))
    ap.add_argument("--overlay", type=Path, default=None, help="also write an annotated JPG")
    ap.add_argument("--detector", type=Path, default=DEF_DETECTOR)
    ap.add_argument("--fdi-head", type=Path, default=DEF_FDI_HEAD)
    ap.add_argument("--caries-gate", type=Path, default=DEF_CARIES_GATE)
    ap.add_argument("--caries-severity", type=Path, default=DEF_CARIES_SEVERITY)
    ap.add_argument("--bone-loss", type=Path, default=DEF_BONE_LOSS)
    ap.add_argument("--bone-severity", type=Path, default=DEF_BONE_SEVERITY)
    ap.add_argument("--conf", type=float, default=0.25, help="detector confidence threshold")
    ap.add_argument("--imgsz", type=int, default=1024, help="detector input size (frozen at 1024)")
    ap.add_argument("--det-iou", type=float, default=0.50, help="detector NMS IoU")
    ap.add_argument("--no-one-to-one", action="store_true",
                    help="ablation: plain argmax FDI, which can emit duplicate codes")
    args = ap.parse_args()

    import cv2
    import torch
    from ultralytics import YOLO

    from src.classifiers import (BONE_LOSS_SEVERITY_CLASSES, load_classifier, run_bone_loss,
                                 run_caries)
    from src.fdi_head_inference import assign_fdi_head, load_head
    from src.orientation import detect_upright

    img = cv2.imread(str(args.image))
    if img is None:
        raise SystemExit(f"cannot read image: {args.image}")
    for p in (args.detector, args.fdi_head, args.caries_gate, args.caries_severity,
              args.bone_loss, args.bone_severity):
        if not Path(p).exists():
            raise SystemExit(f"missing model weights: {p}")

    device = torch.device("cuda" if torch.cuda.is_available()
                          else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"device={device}   image={args.image.name}  {img.shape[1]}x{img.shape[0]}")

    detector = YOLO(str(args.detector))
    head = load_head(args.fdi_head, device)
    gate, gate_cls = load_classifier(args.caries_gate, 2, device)
    csev, csev_cls = load_classifier(args.caries_severity, 2, device)
    bbin, _ = load_classifier(args.bone_loss, 2, device)
    bsev, _ = load_classifier(args.bone_severity, 3, device)

    # The two caries checkpoints carry their own class_to_idx. Assert it matches the order
    # src/classifiers.py assumes, rather than trusting that it does -- an inverted index here
    # would report every healthy tooth as carious and still look like a working pipeline.
    if gate_cls and gate_cls != {"caries": 0, "no_caries": 1}:
        raise SystemExit(f"caries gate class_to_idx changed: {gate_cls}")
    if csev_cls and csev_cls != {"caries": 0, "deep_caries": 1}:
        raise SystemExit(f"caries severity class_to_idx changed: {csev_cls}")

    print("stage 1 — detection …")
    boxes, confs = detect_upright(detector, img, imgsz=args.imgsz, conf=args.conf,
                                  iou=args.det_iou, verbose=False)
    print(f"  {len(boxes)} teeth detected")
    if not boxes:
        print("  no teeth detected — writing an empty report")

    print("stage 2 — FDI enumeration …")
    fdi_assign = assign_fdi_head(head, img, boxes, device,
                                 one_to_one=not args.no_one_to_one)
    print("stage 3 — caries cascade (tight crops) …")
    caries = run_caries(gate, csev, img, boxes, device)
    print("stage 4 — bone-loss cascade (1.5x/2.0x crops) …")
    bone = run_bone_loss(bbin, bsev, img, boxes, device)

    meta = {
        "detector": {"weights": str(args.detector), "tag": "tooth-detector-a100-1024-v1.0",
                     "imgsz": args.imgsz, "conf": args.conf, "nms_iou": args.det_iou,
                     "input_rotation": "90 deg counter-clockwise (src/orientation.py)"},
        "fdi_head": {"weights": str(args.fdi_head), "tag": "fdi-enumeration-head-resnet18-v1.0",
                     "one_to_one": not args.no_one_to_one, "crop_expand": [1.5, 1.5]},
        "caries": {"gate": str(args.caries_gate), "severity": str(args.caries_severity),
                   "tag": "caries-cascade-resnet18-v1.0", "crop_expand": [1.0, 1.0]},
        "bone_loss": {"binary": str(args.bone_loss), "severity": str(args.bone_severity),
                      "crop_expand": [1.5, 2.0], "severity_classes": BONE_LOSS_SEVERITY_CLASSES,
                      "class_order_note": (
                          "binary class order derived from the FocalLoss alpha [0.642, 2.258] "
                          "against counts (2500 normal / 711 diseased); the checkpoint carries "
                          "no class_to_idx. Inferred, not read.")},
    }

    print("stage 5–6 — fusion and report …")
    report = build_report(args.image, img, boxes, confs, fdi_assign, caries, bone, meta)
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
    print("\n  NOTE: ~half the FDI codes are expected wrong (Stage 2 = 46.5% end-to-end), and")
    print("  the caries gate is out of distribution here. See report['limitations'].")


if __name__ == "__main__":
    main()
