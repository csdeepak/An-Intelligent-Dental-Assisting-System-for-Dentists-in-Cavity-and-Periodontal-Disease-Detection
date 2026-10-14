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
    Stage 4  abnormality flag + severity   -> normal | bone_loss; severity withheld unless
                                               --bone-severity-grade             (1.5x/2.0x)
    Stage 5  fusion, flags, assessability
    Stage 6  structured JSON (+ optional overlay)

EACH STAGE GETS ITS OWN CROP. That is not an implementation detail -- the three conventions
(1.0x tight, 1.5x/1.5x, 1.5x/2.0x) come from three different training pipelines, and crossing
them produces confident, plausible, wrong output with no error. See src/classifiers.py.

WHAT THIS REPORT IS NOT
-----------------------
Composing four independently-trained stages does not produce a clinically validated system,
and the numbers here are not a performance claim. Three limitations are structural and are
written into every report rather than left to a footnote:

  * ERROR PROPAGATION. With the default detector (multi-corpus, adopted 11 Oct 2026) detector
    recall is 99.6% and Stage-2 FDI accuracy 92.8% end-to-end on the 164 held-out DENTEX images
    (RESULTS_LOG 2026-10-11g). DENTEX IS IN-DOMAIN FOR THAT DETECTOR -- it was trained on
    Tufts, DENTEX and a third corpus -- and on the held-out Tufts test split the same pipeline
    scores 89.3% / 63.5%. No numbering figure exists for it on a source it was not trained on.
    The previous Tufts-only seg detector scored 70.6% / 58.3% on DENTEX, cross-domain
    (RESULTS_LOG 2026-08-27e). A tooth that is missed is absent from the report entirely, and
    a tooth numbered wrongly attaches correct findings to the wrong tooth.
    `stage2_fdi_exact_end_to_end` is the authority, and its `interpretation` says where it holds.
  * THE CARIES BRANCH IS AN ADOPTED LESION DETECTOR, NOT A SOLVED PROBLEM. Adopted 4 Sep 2026
    (Lever B, RESULTS_LOG 2026-09-04h) because it decisively beats both the old per-crop gate
    AND an image-blind constant baseline -- on this project's six cohorts, that constant had
    tied or beaten the gate EVERYWHERE (`PAPER_MATERIAL.md` Sec 8.22/8.24/8.25). Pre-registered
    acceptance: beats the constant + the gate, CI excluding zero, on >=2 of 3 external cohorts
    at <=1.5x the constant's flagging rate. It cleared that on CariesXrays (+37/+12 pp) and
    Ningxia (+9/+10 pp). On DENTEX it is a statistical TIE with both (CI including zero) -- not
    a third win, and not reported as one. CORRECTED 14 Oct 2026: CariesXrays is this
    detector's own validation split (`best.pt` was chosen on it), so it is not an external
    cohort; Ningxia is external but informed the adoption; and both were measured under an
    earlier tooth detector. With the default detector, on DENTEX: FDI-set F1 0.498 against the
    constant's 0.320, and lesion agreement not separated from the constant (RESULTS_LOG
    2026-10-13d). **This is real, measured progress on a problem five
    prior fix attempts on the gate could not move -- it is not "solved everywhere."** The
    retained gate path (`--caries-method gate`) still calls 19.1% of detected teeth carious
    against an 11.7% annotated floor at 0.40 held-out precision; pass it for reproducibility of
    every pre-4-Sep number.
  * THE "BONE LOSS" FIELD IS AN ABNORMALITY-PROXIMITY FLAG, NOT A PERIODONTAL FINDING (found
    10 Oct 2026, RESULTS_LOG 2026-10-10). Stage 4 is trained to flag tooth crops that overlap
    a Tufts expert ABNORMALITY mask, and the radiographs behind that label are described as
    apical lesions, sclerosis and cysts -- none as periodontal bone loss. Since 13 Oct 2026 the
    default binary model is one retrained with the split made by radiograph: on 143 Tufts test
    radiographs three training runs of one recipe found 11.0%, 16.5% and 27.5% of the teeth
    carrying its label (18.3% pooled); the shipped run is the 27.5% one, at 95.9% specificity
    (RESULTS_LOG 2026-10-13b, -c, -d). The severity grade was trained on crop contrast, not on the
    mask, and is withheld unless `--bone-severity-grade` (RESULTS_LOG 2026-10-13d, 2026-10-14).
    The model it replaced, whose
    0.923 macro-F1 was validation on its own training radiographs and which finds 7.6% held
    out, is retained: pass `--bone-loss models/03_bone_loss_model_training_notebook_models/
    bone_loss_resnet18_best.pth` for any Stage-4 number published before that date. The field
    names are unchanged so consumers do not break; the report's `limitations` block says what
    they mean, for whichever checkpoint ran.

Neither branch is fixable-to-perfect at this layer, and neither field is a diagnosis. They are
surfaced so the report cannot be quoted as more than it is.
"""

import argparse
import functools
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# 1.1 (27 Aug 2026): per-tooth caries records gained `gate_confidence_calibrated` and the
# `caries_confidence_isotonic` flag. Additive only -- `gate_confidence` and every verdict
# are unchanged, so 1.0 consumers keep working. RESULTS_LOG 2026-08-27s.
# 1.2 (11 Oct 2026): `limitations` gained `bone_loss_label_and_validation`, the text of
# `bone_loss_domain_shift` was corrected, and `models.bone_loss` gained `label_definition` and
# `validation_split`. Additive only -- nothing was renamed or removed and every per-tooth record
# is unchanged, so 1.1 consumers keep working. RESULTS_LOG 2026-10-10 (the finding), 2026-10-11b.
# 1.3 (11 Oct 2026): `models.detector` gained `sha256`, and the detector's tag and the two
# accuracy figures in `limitations` now follow the weights actually loaded (DETECTOR_PROFILES
# below). For a detector with no profile those two figures are null -- the one change a
# consumer can notice, and only on a non-default `--detector`. RESULTS_LOG 2026-10-11e.
# 1.4 (13 Oct 2026): `models.bone_loss` gained `sha256_binary`, and its `tag_binary`,
# `validation_split` and `class_order_note`, with the two bone-loss texts in `limitations`, now
# follow the binary weights actually loaded (BONE_LOSS_PROFILES below). Additive: nothing was
# renamed or removed. The Stage-4a default changed the same day, so the per-tooth `bone_loss`
# VALUES differ from a 1.3 report of the same image. RESULTS_LOG 2026-10-13c.
# 1.5 (14 Oct 2026): `limitations` gained `bone_severity_not_evaluated` and
# `caries_severity_not_evaluated`; `models.fdi_head` gained `sha256` and its `tag` now follows the
# weights (it said v1.0 while v2.0 ran); `models.caries` gained `sha256`, `sha256_severity`,
# `tag_severity` (and `tag_gate` in gate mode); `models.bone_loss` gained `sha256_severity` and
# `severity_reported`. The Stage-4 severity grade is withheld by default: a flagged tooth carries
# `severity: null` and the flag `severity_withheld_contrast_proxy` unless --bone-severity-grade.
# The caries and Stage-4 texts were corrected. Nothing renamed or removed. RESULTS_LOG 2026-10-14.
# 1.6 (15 Oct 2026): `image` gained `warnings` (input checks: portrait, aspect, resolution, size,
# bit depth -- warn only, the pipeline still runs); `models` gained `runtime` (python, library
# versions, git commit, and the device each component actually ran on); in lesion-detector mode
# `models.caries` gained `lesion_boxes_detected` and `lesion_boxes_unmapped`. The caries-severity
# limitation text was corrected. Every per-tooth record is unchanged. RESULTS_LOG 2026-10-15b.
SCHEMA_VERSION = "opg-report/1.6"

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
# RESULTS_LOG 2026-08-27e. These are the seg detector's numbers -- the default until 11 Oct 2026.
# The current default's figures live in its DETECTOR_PROFILES entry below.
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
#
# SUPERSEDED AS THE DEFAULT 11 Oct 2026 by the Lever A multi-corpus DETECT model (arm3c: Tufts +
# DENTEX + Kaggle), by explicit user decision AGAINST two pre-registered ablation verdicts.
# Lever 1 and Lever A each passed their primary (+34 pp end-to-end FDI on DENTEX) and failed a
# Tufts box-mAP guard, and both pre-registrations say a failed guard leaves the default alone.
# NEITHER BAR WAS MOVED AND NEITHER GUARD IS CLAIMED MET; the change is a later, dated human
# decision (RESULTS_LOG 2026-10-11f), re-measured under outputs/stage1_switch/PRE_REGISTRATION.md
# (RESULTS_LOG 2026-10-11g), whose one stop rule did not fire.
#
# Given up: Tufts test box mAP@0.5 0.810 -> 0.585, and instance masks (arm3c has none). The seg
# detector above stays selectable, unchanged and hash-pinned, and every pipeline number
# published between 27 Aug and 11 Oct 2026 used it:
#   --detector models/11_yolo_seg_tufts_r1/best.pt
DEF_DETECTOR = REPO_ROOT / "models/15_detector_multicorpus_leverA/arm3c_best.pt"
DETECTOR_TAG = "tooth-detector-seg-tufts-1024-v1.0"   # the seg detector's tag, not the default's

# What is known about each Stage-1 detector, keyed by the sha256 of its weights, so that the tag
# and the accuracy stamped into a report belong to the detector that produced it. Until
# 11 Oct 2026 they were the module constants above, and `--detector <anything else>` wrote a
# report carrying this detector's name and its 70.6% / 58.3%. A detector with no entry gets an
# "unregistered" tag and no accuracy claim -- add its entry only from a measurement of it.
DETECTOR_PROFILES = {
    "271316c46caaf4029ea707fa77b6fe30697795e46632e1f6fcae3498c48781ba": {
        "tag": DETECTOR_TAG,
        "recall": STAGE1_DETECTOR_RECALL,
        "fdi_exact_end_to_end": STAGE2_FDI_EXACT_END_TO_END,
        "interpretation": (
            "Detection recall and FDI accuracy are measured on DENTEX disease/ "
            "(164 leak-free images, 936 GT teeth) against the CURRENT seg detector, "
            "re-measured 27 Aug 2026 (RESULTS_LOG 2026-08-27e). The superseded bbox "
            "detector scored 67.3% / 46.3% on the same harness. "
            "A missed tooth is absent "
            "from this report; a misnumbered tooth carries correct findings under the "
            "wrong FDI code. Expect roughly half the codes in this report to be wrong."),
    },
    # arm3c, the default since 11 Oct 2026. Row B of outputs/stage1_switch/, measured on the
    # macOS clone: 932 of 936 teeth detected, 869 numbered correctly.
    "5d301f13fb48da5c74e7ef01bd0f91226f9b6800cb433dee5aebc8f8db8f161e": {
        "tag": "tooth-detector-multicorpus-1024-v1.0",
        "recall": 0.996,
        "fdi_exact_end_to_end": 0.928,
        "interpretation": (
            "Detection recall and FDI accuracy are measured on DENTEX disease/ (164 held-out "
            "images, 936 GT teeth), 11 Oct 2026 (RESULTS_LOG 2026-10-11g). DENTEX is "
            "IN-DOMAIN for this detector, which was trained on Tufts, DENTEX and a third "
            "corpus. On the held-out Tufts test split the same pipeline scores 89.3% / 63.5%. On "
            "UFBA-425, the one corpus neither this detector nor the numbering head trained on, "
            "it scores 66.6% / 44.5% on the square 640x640 export as distributed and 95.6% / "
            "77.2% with each image widened to a panoramic aspect ratio (RESULTS_LOG "
            "2026-10-12b) -- do not read 92.8% as what to expect on a new radiograph. A missed "
            "tooth is absent from this report; a "
            "misnumbered tooth carries correct findings under the wrong FDI code."),
    },
}
UNREGISTERED_DETECTOR = {
    "recall": None,
    "fdi_exact_end_to_end": None,
    "interpretation": (
        "No detection recall or FDI accuracy has been measured for the detector that produced "
        "this report: its weights have no entry in DETECTOR_PROFILES. Figures quoted elsewhere "
        "for this pipeline belong to a different detector and do not apply here. A missed tooth "
        "is absent from this report; a misnumbered tooth carries correct findings under the "
        "wrong FDI code."),
}


@functools.lru_cache(maxsize=None)
def file_sha256(path):
    """sha256 of a weight file. Cached: run_pipeline asks once per image."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
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
# bootstrap, 10k resamples, RESULTS_LOG 2026-09-04h):
#     cohort        gate v3.0   constant   lesion detector (this model)
#     DENTEX          44.3%      48.9%     45.5% [40.9,50.1] -- TIE (CI incl. 0), fails Sec 6
#     CariesXrays      31.7%      56.2%     68.4% [66.4,70.4] -- PASS (CI excl. 0, both deltas)
#     Ningxia          40.8%      39.9%     50.0% [46.3,53.9] -- PASS (CI excl. 0, both deltas)
# 2 of 3 -> Sec 6 met. Trained on CariesXrays + DENTEX-domain caries boxes, per-corpus balanced
# (`models/16_lever_b_pooled/`, RESULTS_LOG 2026-09-04h) -- the DENTEX data is what closed the
# out-of-domain gap the CariesXrays-only arm (B-single, `models/14`) could not (it lost DENTEX
# decisively, -40/-36 pp, and lost Ningxia too, -16/-17 pp -- see RESULTS_LOG 2026-09-04h).
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
        "the DEF_CARIES_LESION_MODEL comment above and RESULTS_LOG 2026-09-04h for the full "
        "pre-registered verdict. That evidence was measured under an earlier tooth detector. "
        "Of its three cohorts, CariesXrays (1,200 images) is this detector's own validation "
        "split, so it is not external; Ningxia is external and also informed the adoption: "
        "+9.28 points of lesion agreement over an image-blind constant, pooled interval "
        "+4.72 to +13.73. On DENTEX with the default tooth detector it reaches tooth-level "
        "F1 0.498 against the constant's 0.320, but on lesion agreement it is not separated "
        "from the constant (-3.55 points, interval -10.11 to +2.64) and sits 20.67 points "
        "below the retained gate, which flags 2.4 times as many teeth. 43.9% of the tooth "
        "codes it flags are annotated carious; no false-positive rate can be given, because "
        "no cohort on hand labels a tooth healthy. IMPROVED, NOT SOLVED. Do not read a "
        "caries field here as a diagnosis. Figures: docs/results/model_metrics.md, Stage 3a."),
    "gate": (
        "The gate is caries-gate-resnet18-v3.0, retrained with a real negative class "
        "(5,366 healthy teeth). In-pipeline it calls 19.1% of detected teeth carious "
        "against an 11.7% annotated floor -- 1.6x, down from 7.3x for the legacy gate "
        "(RESULTS_LOG 2026-08-25a). It is IMPROVED, NOT SOLVED: precision on the "
        "held-out test split is 0.40, so roughly six of every ten positives are wrong. "
        "Do not read a caries field here as a diagnosis. Superseded as the pipeline default "
        "4 Sep 2026 by the lesion detector (RESULTS_LOG 2026-09-04h); retained via "
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
DEF_BONE_LOSS = REPO_ROOT / "models/18_bone_loss_radiograph_split/seed42_best.pth"
DEF_BONE_SEVERITY = REPO_ROOT / "models/04_bone_loss_severity_notebook_models/bone_loss_severity_resnet18_best.pth"

# The sha256 each DEFAULT checkpoint must have -- the hash its run_summary.txt records and
# scripts/eval/verify_invariants.py pins. load_models() checks a default path against it BEFORE
# unpickling the file, so a replaced or corrupted default stops the run instead of only being
# stamped into the report afterwards (14 Oct 2026). Any other path is loaded as given and tagged
# by its own hash, as before. Keyed by resolved path, so a default reached through a symlink is
# checked too.
DEFAULT_SHA256 = {path.resolve(): sha for path, sha in {
    DEF_DETECTOR: "5d301f13fb48da5c74e7ef01bd0f91226f9b6800cb433dee5aebc8f8db8f161e",
    DEF_FDI_HEAD: "6c675fa014551a0f184cf87a52d55ea26d21f23ae84dd5df1f7efce78a43004b",
    DEF_CARIES_GATE: "8f4a99ba412c5562e0bc444fef9b856af091d3d1c8b5ba74876735e616357a76",
    DEF_CARIES_SEVERITY: "aa0a8a7ebf47a8acab0d24a6ecd948542c220196d1c71cbebbf56952beacbc86",
    DEF_CARIES_LESION_MODEL: "029018dbe37a92d1fd764322fa1c38b229698750e34d36c533b4338793e870ed",
    DEF_BONE_LOSS: "e4bc874423e7c17752bb949d510862e4b4fd618f9a7602a95743663a3c27a0b2",
    DEF_BONE_SEVERITY: "fa93a5201833d8137bd2ae328d3afd63c2c1f9e4ac82a621d1b430a51eba8a4a",
}.items()}

# Tags of the checkpoints without a profile, keyed by the sha256 of their weights -- each hash
# copied from that model's run_summary.txt -- so a report names the weights that actually ran.
# Until 14 Oct 2026 the numbering head's tag was a literal "v1.0" while v2.0 loaded. A file with
# no entry is tagged "unregistered-<8 hex>".
CHECKPOINT_TAGS = {
    "e6abf1cd959c36824ef0061db84a5fbc8793af314099cb3cc72027662445cc5a": "fdi-enumeration-head-resnet18-v1.0",
    "6c675fa014551a0f184cf87a52d55ea26d21f23ae84dd5df1f7efce78a43004b": "fdi-enumeration-head-resnet18-v2.0",
    "8f4a99ba412c5562e0bc444fef9b856af091d3d1c8b5ba74876735e616357a76": "caries-gate-resnet18-v3.0",
    "aa0a8a7ebf47a8acab0d24a6ecd948542c220196d1c71cbebbf56952beacbc86": "caries-cascade-resnet18-v1.0",
    "029018dbe37a92d1fd764322fa1c38b229698750e34d36c533b4338793e870ed": "caries-lesion-detector-yolo11l-leverb-bpooled-v1.0",
    "fa93a5201833d8137bd2ae328d3afd63c2c1f9e4ac82a621d1b430a51eba8a4a": "bone-loss-severity-resnet18-v1.0",
}


def checkpoint_tag(sha):
    return CHECKPOINT_TAGS.get(sha, f"unregistered-{sha[:8]}")


# Two severity grades no held-out set can test, stated in every report (RESULTS_LOG 2026-10-13d).
BONE_SEVERITY_NOT_EVALUATED = (
    "The Stage-4 severity head ('Mild' / 'Moderate' / 'Severe', models/04) was trained on the "
    "standard deviation of each crop's grey levels -- a stand-in its notebook built because the "
    "expert-mask overlap was missing -- so its classes are low, middle and high image contrast, "
    "not degrees of anything clinical. It has no test. It is withheld by default: a flagged "
    "tooth then carries severity null and the flag severity_withheld_contrast_proxy, and "
    "models.bone_loss.severity_reported says whether this report carries the grade "
    "(--bone-severity-grade). RESULTS_LOG 2026-10-13d.")
CARIES_SEVERITY_NOT_EVALUATED = (
    "The caries / deep_caries distinction comes from a severity head (models/07) validated on "
    "133 crops (macro-F1 0.77, tuned and reported on the same crops) and never tested on held-out "
    "data. An image-level DENTEX test split that labels deep caries exists "
    "(data/dentex/splits_v2.json), but this head predates it and has not been scored on it. Read "
    "deep_caries as unvalidated.")

# What is known about each Stage-4a (binary) checkpoint, keyed by the sha256 of its weights, so
# that the tag and the figures stamped into a report belong to the model that produced it -- the
# arrangement DETECTOR_PROFILES already gives Stage 1. The default changed on 13 Oct 2026
# (RESULTS_LOG 2026-10-13b, -c). The checkpoint it replaced is retained, and every Stage-4 number
# published before that date used it:
#   --bone-loss models/03_bone_loss_model_training_notebook_models/bone_loss_resnet18_best.pth
# A checkpoint with no entry gets an "unregistered" tag and no figure -- add its entry only from a
# measurement of it.
BONE_LOSS_PROFILES = {
    "e4bc874423e7c17752bb949d510862e4b4fd618f9a7602a95743663a3c27a0b2": {
        "tag": "abnormality-flag-resnet18-radiograph-split-v2.0",
        "label_and_validation": (
            "Read every 'bone_loss' field in this report as an ABNORMALITY-PROXIMITY FLAG, not as "
            "a periodontal finding. Stage 4 is trained to flag tooth crops that overlap a Tufts "
            "expert abnormality mask, and the radiographs behind that label are described by that "
            "expert as apical lesions, sclerosis and cysts -- none as periodontal bone loss. This "
            "checkpoint was trained with the split made by radiograph and scored once on 143 "
            "Tufts test radiographs that this model did not train on (the Stage-4 severity head "
            "trained on two of them, and one is a re-rendered copy of a training radiograph that "
            "holds no positive tooth): it found 27.5% of the teeth carrying its label (50 of 182; "
            "95% interval 18.3 to 38.0, which covers the sampling of radiographs, not the "
            "training run) at 95.9% specificity -- about one labelled tooth in four, about one "
            "false flag per radiograph, and one flag in four correct. Two further training runs "
            "of the same recipe gave 16.5% and 11.0% (18.3%, 100 of 546, over the three), so the "
            "operating point depends on the run. These figures were scored on crops cut at "
            "annotated tooth boxes, not at this pipeline's detections. Its 'confidence' is the "
            "softmax of a model trained with negatives undersampled to 3.5 per positive and a "
            "class-weighted focal loss, applied at about 5% prevalence: read it as a ranking "
            "score, not a probability. Expect this "
            "flag to miss most of what it is trained to mark and to be wrong more often than "
            "right. The field names are kept so existing consumers do not break. RESULTS_LOG "
            "2026-10-13b, -13d, 2026-10-14; 2026-10-10 and 2026-10-13 for the checkpoint it "
            "replaced."),
        "transfer": (
            "This Stage-4 model was trained on TUFTS radiographs and is applied here to whatever "
            "image is supplied. It has no figure with ground truth on any other source. On 164 "
            "DENTEX images it flags 6.1% of detected teeth (274 of 4,512; the checkpoint it "
            "replaced flagged 0.75%) -- a firing rate, not a sensitivity, because DENTEX carries "
            "no ground truth for this label. The 2.2% affected-tooth sensitivity against the "
            "Ningxia periodontitis masks belongs to the checkpoint it replaced, and Ningxia has "
            "not been scored with this one. A "
            "'normal' field is weak evidence, not a negative finding, and says nothing about "
            "periodontal status. RESULTS_LOG 2026-10-13c."),
        "validation_split": (
            "binary: the frozen split_v1 by radiograph -- trained on 678 Tufts radiographs, "
            "checkpoint chosen on 145 others, scored once on 143 test radiographs: sensitivity "
            "0.275 (50/182), specificity 0.959 (3558/3710); 0.165 and 0.110 for two further "
            "training runs of the same recipe. RESULTS_LOG 2026-10-13b. "
            "severity: image-level, 32 training / 9 validation radiographs; its labels were a "
            "crop-contrast stand-in, not mask overlap (RESULTS_LOG 2026-10-13d)."),
        "class_order_note": (
            "binary class order [normal, bone_loss]: index 1 is the positive label by "
            "construction (scripts/tufts/train_bone_loss_v2.py trains on labels 0/1) and the "
            "test pass scored it as such. The checkpoint is a bare state_dict and carries no "
            "class_to_idx. See models/18_bone_loss_radiograph_split/run_summary.txt."),
    },
    "c52f7f484076a2a2c3c144c3351912b118b6b0d56fc51ba1b4296e6ce6213db1": {
        "tag": "bone-loss-binary-resnet18-v1.0",
        "label_and_validation": (
            "Read every 'bone_loss' field in this report as an ABNORMALITY-PROXIMITY FLAG, "
            "not as a periodontal finding. Stage 4 was trained to flag tooth crops that "
            "overlap a Tufts expert abnormality mask, and the radiographs behind its "
            "positive class are described by that expert as apical lesions, sclerosis and "
            "cysts -- none as periodontal bone loss. Its reported in-domain score (macro-F1 "
            "0.923) is not a held-out estimate: the validation crops came from the same "
            "radiographs as the training crops. Scored once on 821 Tufts radiographs that "
            "supplied no training crop, it found 7.6% of the teeth carrying its own label "
            "(72 of 946; 95% interval 5.2 to 10.5) at 98.7% specificity -- so expect this "
            "flag to miss most of what it was trained to mark, on any image. The field "
            "names are kept so existing consumers do not break. RESULTS_LOG 2026-10-10, "
            "2026-10-13."),
        "transfer": (
            "The Stage-4 models were trained on TUFTS radiographs and are applied here to "
            "whatever image is supplied; on DENTEX they fire on 0.7% of teeth (2/299) with "
            "0.93-0.999 confidence in 'normal', and against the Ningxia periodontitis masks "
            "they reach 2.4% affected-tooth sensitivity. That was first read as domain "
            "shift. It is at least partly a label mismatch, and since 13 Oct 2026 the model "
            "is known to miss 92% of its own label on held-out Tufts radiographs as well -- "
            "see bone_loss_label_and_validation -- so a 'normal' field is weak evidence, "
            "not a negative finding, and says nothing about periodontal status."),
        "validation_split": (
            "binary: crop-level 20% split, all 143 validation radiographs also "
            "supply training crops, so 0.9233 is not a held-out estimate. Held "
            "out, 821 Tufts radiographs outside training (13 Oct 2026): "
            "sensitivity 0.076 (72/946), specificity 0.987. "
            "severity: image-level, 32 training / 9 validation radiographs."),
        "class_order_note": (
            "binary class order [normal, bone_loss] confirmed two independent "
            "ways (27 Aug 2026): FocalLoss alpha ratio 2.258/0.642 = 3.5171 "
            "matches the class-count ratio 2500/711 = 3.5162 to 0.03%, so index "
            "0 is the majority class; and training_summary.txt labels its own "
            "scores 'F1 Normal (cls 0)' / 'F1 Diseased (cls 1)'. The checkpoint "
            "still carries no class_to_idx -- the order is corroborated, not "
            "stored. See models/03_.../run_summary.txt."),
    },
}
UNREGISTERED_BONE_LOSS = {
    "tag": None,
    "label_and_validation": (
        "Read every 'bone_loss' field in this report as an ABNORMALITY-PROXIMITY FLAG, not as a "
        "periodontal finding. No sensitivity or specificity has been measured for the binary "
        "checkpoint that produced this report: its weights have no entry in BONE_LOSS_PROFILES. "
        "Figures quoted elsewhere for Stage 4 belong to a different checkpoint and do not apply "
        "here."),
    "transfer": (
        "No figure exists for this Stage-4 checkpoint on any source. A 'normal' field is weak "
        "evidence, not a negative finding, and says nothing about periodontal status."),
    "validation_split": "binary: unknown -- unregistered checkpoint.",
    "class_order_note": "binary class order assumed [normal, bone_loss]; not verified for this checkpoint.",
}

# A tooth is reported as assessable only if Stage 2 is confident about WHICH tooth it is.
# Findings on a misnumbered tooth are worse than no findings, so this gates the whole record.
#
# Deliberately the SAME value as src.fdi_head_inference.LOW_CONFIDENCE, not a second knob
# tuned here: a tooth the numbering head calls low-confidence is exactly a tooth whose
# findings cannot be attributed. Introducing an independent threshold would mean two numbers
# to justify instead of one. Like that one, it is fixed a priori and must not be swept
# against an evaluation set.
ASSESSABILITY_MIN_FDI_CONFIDENCE = 0.30


def build_report(image_path, img_bgr, boxes, confs, fdi_assign, caries, bone, meta,
                 input_warnings=()):
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
        # `not >=`, not `<`: a NaN confidence must fail the gate, and `nan < 0.30` is False.
        c = a.get("confidence", 0.0)
        if c is None or not c >= ASSESSABILITY_MIN_FDI_CONFIDENCE:
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
    det_profile = DETECTOR_PROFILES.get(meta.get("detector", {}).get("sha256"),
                                        UNREGISTERED_DETECTOR)
    bone_profile = BONE_LOSS_PROFILES.get(meta.get("bone_loss", {}).get("sha256_binary"),
                                          UNREGISTERED_BONE_LOSS)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "image": {"path": str(image_path), "width": W, "height": H,
                  "warnings": list(input_warnings)},
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
            "stage1_detector_recall": det_profile["recall"],
            "stage2_fdi_exact_end_to_end": det_profile["fdi_exact_end_to_end"],
            "interpretation": det_profile["interpretation"],
            "caries_method_caveat": (
                CARIES_METHOD_CAVEATS["lesion-detector"] if meta["caries"].get("method") ==
                "lesion-detector" else CARIES_METHOD_CAVEATS["gate"]),
            "caries_presumed_negative_assumption": (
                CARIES_NEGATIVE_ASSUMPTION["lesion-detector"] if meta["caries"].get("method") ==
                "lesion-detector" else CARIES_NEGATIVE_ASSUMPTION["gate"]),
            "bone_loss_label_and_validation": bone_profile["label_and_validation"],
            "bone_loss_domain_shift": bone_profile["transfer"],
            "bone_severity_not_evaluated": BONE_SEVERITY_NOT_EVALUATED,
            "caries_severity_not_evaluated": CARIES_SEVERITY_NOT_EVALUATED,
            "not_clinically_validated": True,
        },
    }


# Overlay colours, BGR. Grey, not red, for "not assessable" (14 Oct 2026): red read as the most
# urgent tooth when it meant the pipeline could not say. Orange and blue stay apart under
# red-green colour blindness. A thin line marks less: no assessment, or a numbering doubt.
OVERLAY_NOT_ASSESSABLE, OVERLAY_FINDING, OVERLAY_NO_FINDING = (160, 160, 160), (0, 165, 255), (200, 120, 0)


def draw_overlay(img_bgr, report, out_path=None):
    """Orange = a finding (caries, or the Stage-4 abnormality flag); blue = no finding, thin when
    the numbering is uncertain; grey, thin = not assessable. Label: FDI code ('?' when uncertain)
    + findings. Returns the annotated image; writes it only when `out_path` is given."""
    import cv2
    viz = img_bgr.copy()
    for t in report["teeth"]:
        x1, y1, x2, y2 = [int(v) for v in t["bbox_xyxy"]]
        finding = t["caries"]["finding"] != "no_caries" or t["bone_loss"]["finding"] == "bone_loss"
        if not t["assessable"]:
            colour, width = OVERLAY_NOT_ASSESSABLE, 1
        elif finding:
            colour, width = OVERLAY_FINDING, 2
        else:
            colour, width = OVERLAY_NO_FINDING, 1 if t["fdi_flags"] else 2
        cv2.rectangle(viz, (x1, y1), (x2, y2), colour, width)
        bits = [(str(t["fdi"]) if t["fdi"] else "??") + ("?" if t["fdi_flags"] else "")]
        if t["caries"]["finding"] != "no_caries":
            bits.append(t["caries"]["finding"][:4].upper())
        if t["bone_loss"]["finding"] == "bone_loss":
            # "ABN", not "BL": Stage 4 flags proximity to an abnormality, not bone loss. The
            # contrast-band grade is appended only when it was asked for.
            sev = t["bone_loss"]["severity"]
            bits.append("ABN-" + sev[:3] if sev else "ABN")
        cv2.putText(viz, " ".join(bits), (x1, max(14, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 1, cv2.LINE_AA)
    if out_path is not None:
        cv2.imwrite(str(out_path), viz)
    return viz


# Input checks, warn only (15 Oct 2026). The detector trained on landscape panoramics: DENTEX
# aspect 1.60-2.33, Tufts 1.92, shorter side at least 840 px (measured on every training image).
# On UFBA-425's square export end-to-end numbering is 44.5%, against 77.2% widened. The bounds sit
# outside every training image and were not tuned on any result. A warning changes no finding.
INPUT_ASPECT_BAND = (1.5, 2.6)
INPUT_MIN_SHORT_SIDE = 600
INPUT_MAX_PIXELS = 50_000_000


def check_input(img_bgr, source_dtype=None):
    """-> warnings about an input unlike the radiographs the models trained on; [] when it is like
    them. `source_dtype` is the file's own sample type (OpenCV reduces 16-bit to 8 on reading)."""
    h, w = img_bgr.shape[:2]
    warn = []
    if h >= w:
        warn.append(f"portrait or square image ({w}x{h}): the pipeline expects a landscape "
                    "panoramic radiograph and rotates it 90 degrees for the detector")
    elif not INPUT_ASPECT_BAND[0] <= w / h <= INPUT_ASPECT_BAND[1]:
        warn.append(f"aspect ratio {w / h:.2f} is outside {INPUT_ASPECT_BAND[0]}-"
                    f"{INPUT_ASPECT_BAND[1]}, the range of the training radiographs; detection "
                    "and numbering degrade")
    if min(h, w) < INPUT_MIN_SHORT_SIDE:
        warn.append(f"low resolution ({w}x{h}): the shorter side is under {INPUT_MIN_SHORT_SIDE} px")
    if h * w > INPUT_MAX_PIXELS:
        warn.append(f"very large image ({w}x{h}); expect slow processing")
    if source_dtype is not None and str(source_dtype) != "uint8":
        warn.append(f"{source_dtype} source reduced to 8 bits on reading; contrast may be lost")
    return warn


def load_yolo_pinned(path):
    """YOLO(path), after a hash check -- the one place a YOLO .pt is unpickled (15 Oct 2026). A
    default must match its pin; any other file is loaded with a warning unless its hash is
    registered, because unpickling runs whatever code the file carries."""
    from ultralytics import YOLO
    p = Path(path)
    sha = file_sha256(str(p))
    pinned = DEFAULT_SHA256.get(p.resolve())
    if pinned and sha != pinned:
        raise SystemExit(f"{p} is a default checkpoint, but its sha256 is not the pinned "
                         f"{pinned[:12]}...; refusing to load it")
    if sha not in DETECTOR_PROFILES and sha not in CHECKPOINT_TAGS:
        print(f"WARNING: {p} (sha256 {sha[:12]}...) is not a registered checkpoint; loading it "
              "unpickles it -- do this only for files you trust", file=sys.stderr)
    return YOLO(str(p))


@functools.lru_cache(maxsize=None)
def _git_commit():
    import subprocess
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                             text=True, timeout=5)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _yolo_device(model):
    """Where ultralytics actually ran: it picks CUDA or the CPU unless MPS is named, so on Apple
    silicon the detectors run on the CPU while the classifiers run on MPS."""
    predictor = getattr(model, "predictor", None)
    return str(predictor.device) if predictor is not None and predictor.device is not None else "not run"


def runtime_info(models, device):
    """What produced a report, beyond the weights: versions, commit and per-component device."""
    import platform

    import cv2
    import numpy
    import torch
    import torchvision
    import ultralytics
    return {"python": platform.python_version(), "platform": platform.platform(),
            "torch": torch.__version__, "torchvision": torchvision.__version__,
            "ultralytics": ultralytics.__version__, "numpy": numpy.__version__,
            "opencv": cv2.__version__, "git_commit": _git_commit(),
            "classifier_device": str(device),
            "detector_device": _yolo_device(models["detector"]),
            "lesion_detector_device": _yolo_device(models["caries_lesion_model"])}


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
        pinned = DEFAULT_SHA256.get(p.resolve())
        if pinned and file_sha256(str(p)) != pinned:
            raise SystemExit(f"{p} is a default checkpoint, but its sha256 is not the pinned "
                             f"{pinned[:12]}...; refusing to load it")

    device = device or pick_device()
    m = {
        "detector": load_yolo_pinned(paths["detector"]),
        "head": load_head(paths["fdi_head"], device),
        "caries_lesion_model": load_yolo_pinned(paths["caries_lesion_model"]),
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
                 caries_lesion_conf=CARIES_LESION_CONF, assignment="hungarian",
                 bone_severity_grade=False, source_dtype=None):
    """
    Stages 1-6 on an already-loaded image, using already-loaded models. This is the function
    both `main()` and the Streamlit app call -- one code path, so a fix or a limitation update
    reaches both automatically. Returns the report dict; writes nothing to disk.

    `caries_method` -- "lesion-detector" (the pipeline default since 4 Sep 2026, Lever B,
    RESULTS_LOG 2026-09-04h) or "gate" (the retained per-crop classifier, for reproducing any
    number measured before that date). See the DEF_CARIES_LESION_MODEL comment above.

    `bone_severity_grade` -- False (default since 14 Oct 2026): the Stage-4 severity head is not
    run and a flagged tooth says so; its classes are crop-contrast bands (RESULTS_LOG 2026-10-13d).
    True restores the grade, flagged as not evaluated.

    `source_dtype` -- the image file's own sample type, if the caller read it (for the bit-depth
    warning in `check_input`).
    """
    from src.classifiers import (BONE_LOSS_SEVERITY_CLASSES, run_bone_loss, run_caries,
                                 run_caries_lesion_detector)
    from src.fdi_head_inference import assign_fdi_head
    from src.orientation import detect_upright

    def log(msg):
        if verbose:
            print(msg)

    input_warnings = check_input(img_bgr, source_dtype)
    for w in input_warnings:
        log(f"  input warning: {w}")

    log("stage 1 — detection …")
    boxes, confs = detect_upright(models["detector"], img_bgr, imgsz=imgsz, conf=conf,
                                  iou=det_iou, verbose=False)
    log(f"  {len(boxes)} teeth detected")
    if not boxes:
        log("  no teeth detected — writing an empty report")

    log("stage 2 — FDI enumeration …")
    fdi_assign = assign_fdi_head(models["head"], img_bgr, boxes, device,
                                 one_to_one=one_to_one, assignment=assignment)

    if caries_method == "gate":
        log("stage 3 — caries GATE (tight crops, retained pre-4-Sep default) …")
        caries = run_caries(models["gate"], models["csev"], img_bgr, boxes, device)
        gate_sha = file_sha256(str(paths["caries_gate"]))
        caries_meta = {
            "method": "gate", "weights": str(paths["caries_gate"]), "sha256": gate_sha,
            "severity_weights": str(paths["caries_severity"]),
            # `tag` has always named the severity cascade in gate mode; kept, and the gate's own
            # tag added beside it.
            "tag": checkpoint_tag(file_sha256(str(paths["caries_severity"]))),
            "tag_gate": checkpoint_tag(gate_sha), "crop_expand": [1.0, 1.0],
            "confidence_calibration": (
                "isotonic, fitted on the crops_v3_phase1 val split; applied to "
                "gate_confidence_calibrated ONLY. Verdicts remain argmax on raw "
                "logits. Test ECE 0.136 -> 0.043. RESULTS_LOG 2026-08-27s."),
        }
    elif caries_method == "lesion-detector":
        log("stage 3 — caries LESION DETECTOR (whole image, adopted 4 Sep 2026) …")
        lesion_stats = {}
        caries = run_caries_lesion_detector(models["caries_lesion_model"], models["csev"],
                                            img_bgr, boxes, device, conf=caries_lesion_conf,
                                            stats=lesion_stats)
        lesion_sha = file_sha256(str(paths["caries_lesion_model"]))
        caries_meta = {
            "method": "lesion-detector", "weights": str(paths["caries_lesion_model"]),
            "sha256": lesion_sha,
            "severity_weights": str(paths["caries_severity"]),
            "tag": checkpoint_tag(lesion_sha),
            "lesion_conf": caries_lesion_conf,
            "adopted": "4 Sep 2026, Lever B Sec 6 -- RESULTS_LOG 2026-09-04h",
            "confidence_calibration": (
                "NOT applied -- the isotonic calibrator was fit for the gate's score "
                "distribution. gate_confidence here is a raw detection score, not a softmax."),
            "lesion_boxes_detected": lesion_stats.get("lesion_boxes", 0),
            "lesion_boxes_unmapped": lesion_stats.get("lesion_boxes_unmapped", 0),
        }
    else:
        raise ValueError(f"unknown caries_method: {caries_method!r} (expected "
                         f"'lesion-detector' or 'gate')")

    csev_sha = file_sha256(str(paths["caries_severity"]))
    caries_meta.update(sha256_severity=csev_sha, tag_severity=checkpoint_tag(csev_sha))

    log("stage 4 — abnormality flag (1.5x/2.0x crops) …")
    bone = run_bone_loss(models["bbin"], models["bsev"] if bone_severity_grade else None,
                         img_bgr, boxes, device)

    det_sha = file_sha256(str(paths["detector"]))
    fdi_sha = file_sha256(str(paths["fdi_head"]))
    bone_sha = file_sha256(str(paths["bone_loss"]))
    bsev_sha = file_sha256(str(paths["bone_severity"]))
    bone_profile = BONE_LOSS_PROFILES.get(bone_sha, UNREGISTERED_BONE_LOSS)
    meta = {
        "detector": {"weights": str(paths["detector"]), "sha256": det_sha,
                     "tag": (DETECTOR_PROFILES[det_sha]["tag"] if det_sha in DETECTOR_PROFILES
                             else f"unregistered-{det_sha[:8]}"),
                     "imgsz": imgsz, "conf": conf, "nms_iou": det_iou,
                     "input_rotation": "90 deg counter-clockwise (src/orientation.py)"},
        "fdi_head": {"weights": str(paths["fdi_head"]), "sha256": fdi_sha,
                     "tag": checkpoint_tag(fdi_sha),
                     "one_to_one": one_to_one, "assignment": assignment,
                     "crop_expand": [1.5, 1.5]},
        "caries": caries_meta,
        "bone_loss": {"binary": str(paths["bone_loss"]), "sha256_binary": bone_sha,
                      "severity": str(paths["bone_severity"]), "sha256_severity": bsev_sha,
                      "severity_reported": bool(bone_severity_grade),
                      "crop_expand": [1.5, 2.0], "severity_classes": BONE_LOSS_SEVERITY_CLASSES,
                      "tag_binary": bone_profile["tag"] or f"unregistered-{bone_sha[:8]}",
                      "tag_severity": checkpoint_tag(bsev_sha),
                      "label_definition": (
                          "positive = the tooth crop overlaps a Tufts expert ABNORMALITY mask "
                          "(overlap > 0.01). Not a periodontal bone-loss label; the field names "
                          "and the severity tag are historical. RESULTS_LOG 2026-10-10."),
                      "validation_split": bone_profile["validation_split"],
                      "class_order_note": bone_profile["class_order_note"]},
        "runtime": runtime_info(models, device),
    }

    log("stage 5–6 — fusion and report …")
    return build_report(image_label, img_bgr, boxes, confs, fdi_assign, caries, bone, meta,
                        input_warnings=input_warnings)


from src.fdi_head_inference import ASSIGNMENTS  # noqa: E402


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
                         "4 Sep 2026 (Lever B, RESULTS_LOG 2026-09-04h); gate = the retained "
                         "pre-4-Sep per-crop classifier, for reproducing older numbers.")
    ap.add_argument("--caries-lesion-conf", type=float, default=CARIES_LESION_CONF,
                    help="frozen per the pre-registration -- not tuned on any cohort")
    ap.add_argument("--assignment", choices=list(ASSIGNMENTS), default="hungarian",
                    help="Stage-2 assignment. hungarian = the deployed default; structural-dp / "
                         "structural-sort = the Lever C arch-order post-processor "
                         "(outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md). The "
                         "default moves only if that pre-registration's acceptance rule is met.")
    ap.add_argument("--bone-loss", type=Path, default=DEF_BONE_LOSS)
    ap.add_argument("--bone-severity", type=Path, default=DEF_BONE_SEVERITY)
    ap.add_argument("--bone-severity-grade", action="store_true",
                    help="also report the Stage-4 severity grade. Off by default: its classes "
                         "are crop-contrast bands, not degrees (RESULTS_LOG 2026-10-13d)")
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
    raw = cv2.imread(str(args.image), cv2.IMREAD_UNCHANGED)
    source_dtype = raw.dtype if raw is not None else None

    models, device, paths = load_models(
        detector=args.detector, fdi_head=args.fdi_head, caries_gate=args.caries_gate,
        caries_severity=args.caries_severity, caries_lesion_model=args.caries_lesion_model,
        bone_loss=args.bone_loss, bone_severity=args.bone_severity)
    print(f"device={device}   image={args.image.name}  {img.shape[1]}x{img.shape[0]}"
          f"   caries_method={args.caries_method}")

    report = run_pipeline(img, models, device, paths, image_label=str(args.image),
                          imgsz=args.imgsz, conf=args.conf, det_iou=args.det_iou,
                          one_to_one=not args.no_one_to_one, caries_method=args.caries_method,
                          caries_lesion_conf=args.caries_lesion_conf,
                          assignment=args.assignment, bone_severity_grade=args.bone_severity_grade,
                          source_dtype=source_dtype)
    for w in report["image"]["warnings"]:
        print(f"WARNING (input): {w}", file=sys.stderr)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    s = report["summary"]
    print(f"\n  teeth detected {s['teeth_detected']}   assessable {s['teeth_assessable']}"
          f"   distinct FDI {s['distinct_fdi_codes']}   duplicates {s['duplicate_fdi_codes']}")
    print(f"  caries-positive {s['caries_positive']}   "
          f"stage-4 abnormality flags {s['bone_loss_positive']} (not a periodontal finding)")
    print(f"  -> {args.output}")
    if args.overlay:
        draw_overlay(img, report, args.overlay)
        print(f"  -> {args.overlay}")
    # DERIVED from the constant, never hardcoded: this line still said "46.5%" a full day
    # after STAGE2_FDI_EXACT_END_TO_END was set to 0.583 on 27 Aug, so the deployed demo
    # printed a superseded number to users while the JSON it wrote beside it was correct.
    # A literal in a print() is a second source of truth. RESULTS_LOG 2026-08-27m.
    # Read from the report, not the constant: the figure belongs to the detector that ran.
    _e2e = report["limitations"]["stage2_fdi_exact_end_to_end"]
    print("")
    if _e2e is None:
        print(f"  NOTE: no FDI accuracy has been measured for this detector "
              f"({report['models']['detector']['tag']}). Caries "
              f"({args.caries_method}) is improved, not solved -- see report['limitations'].")
    else:
        print(f"  NOTE: Stage-2 numbering is {_e2e:.1%} end-to-end on this detector's DENTEX "
              f"benchmark; report['limitations']['interpretation'] says how far that carries. "
              f"Caries ({args.caries_method}) is improved, not solved.")


if __name__ == "__main__":
    main()
