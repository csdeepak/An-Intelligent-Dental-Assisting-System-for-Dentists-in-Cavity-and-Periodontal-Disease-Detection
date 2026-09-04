"""
Stage 3/4 disease classifiers: caries cascade and bone-loss cascade.

THE CROP CONTRACT — THE THING MOST LIKELY TO BE SILENTLY WRONG
--------------------------------------------------------------
The four classifiers here were trained by three different people in three different notebooks,
and **they do not share a crop convention**. Feeding a model the wrong crop degrades it without
raising anything: the tensor shape is identical, the values are plausible, the output is
confident and wrong. Every convention below was read out of the artefact that defines it, not
inferred:

  caries gate / severity   1.0x TIGHT crop (raw detector box, no expansion)
                           WHY: caries is a crown-surface finding; surrounding bone is pure
                           distractor. Source: scripts/dentex/build_dentex_crops.py docstring,
                           itself verified pixel-for-pixel against the original notebook output.

  bone-loss binary /       1.5x WIDTH, 2.0x HEIGHT expansion
  bone-loss severity       WHY: bone loss is read at the alveolar crest, below the crown. Teeth
                           are ~3x taller than wide, so symmetric expansion would bleed in the
                           neighbours while still missing the peri-apical bone.
                           Source: PAPER_MATERIAL.md 6.1 and configs/dataset_config.yaml
                           (expand_width 1.5, expand_height 2.0).

  (the Stage-2 enumeration head uses 1.5x/1.5x -- a THIRD convention. It lives in
   src/fdi_head_inference.py and is not touched here.)

All four then resize to 224x224 and normalise with ImageNet statistics.

CLASS ORDER — likewise read out, not assumed
--------------------------------------------
An inverted class index is the other silent failure: it reports every healthy tooth as diseased
and still looks like a working pipeline.

  caries gate       {'caries': 0, 'no_caries': 1}      from the checkpoint's own class_to_idx
  caries severity   {'caries': 0, 'deep_caries': 1}    from the checkpoint's own class_to_idx
  bone-loss binary  {normal: 0, diseased: 1}           DERIVED, see below
  bone-loss severity ['Mild', 'Moderate', 'Severe']    notebooks/bone_loss/04_*.ipynb cell 3,
                                                       used by the label-generating function in
                                                       cell 6 (`return 0  # Mild`)

The bone-loss binary checkpoint is a bare state_dict with no class_to_idx. Its order is
recovered from the FocalLoss alpha recorded in its training summary, alpha = [0.642, 2.258],
against the recorded class counts (normal 2500, diseased 711, total 3211):
    N / (K * n_i)  ->  3211/(2*2500) = 0.642   and   3211/(2*711) = 2.258
Both match to three decimals, so index 0 is the majority class (normal) and index 1 the
minority (diseased). Arithmetic, not a guess -- but it is an inference, and it is flagged as
such in the report metadata.

THE CARIES GATE: FIXED ONCE, STILL NOT RELIABLE
-----------------------------------------------
The original gate's `no_caries` class was Impacted + Periapical Lesion and contained **no
healthy teeth at all**, because every annotation in its source file is a diseased tooth. Fed
every tooth the detector finds, it called **84.9%** of them carious (RESULTS_LOG 2026-08-24f).

That is fixed. `caries-gate-resnet18-v3.0` is trained on a rebuilt negative class of **5,366
real healthy teeth**, recovered by MD5-joining the enumeration and disease subsets, and calls
**19.1%** against an 11.7% annotated floor -- 1.6x rather than 7.3x (RESULTS_LOG 2026-08-25a).

**It is improved, not solved, and this module does not pretend otherwise.** Held-out precision
on caries is **0.40**: roughly six of every ten positives are wrong. Its healthy class rests on
treating any tooth without a disease annotation as healthy, which is absence of evidence rather
than evidence of absence. So every caries prediction -- positive AND negative -- still carries
`caries_uncalibrated`, and the report metadata states both limits. Do not read a caries field
as a diagnosis, and do not quote pipeline caries rates as clinical performance.

**Calibrated confidence, added 27 Aug 2026.** The gate's raw probabilities were measured as
systematically overconfident (test ECE 0.136; a predicted 0.85 corresponds to an observed 0.26).
An isotonic calibrator fitted on the validation split brings that to **ECE 0.043**, and it is
applied to the REPORTED confidence only -- `gate_confidence_calibrated`. **The verdict is still
`argmax` on the raw logits and has not changed**, because remapping the score axis would flip 18%
of decisions and invalidate every downstream caries number. `gate_confidence` remains raw and
unchanged for the same reason. RESULTS_LOG 2026-08-27q/r/s.
"""

import numpy as np

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
CROP_SIZE = 224

# (width factor, height factor) per branch -- see the module docstring.
CARIES_EXPAND = (1.0, 1.0)
BONE_LOSS_EXPAND = (1.5, 2.0)

CARIES_GATE_CLASSES = ["caries", "no_caries"]
CARIES_SEVERITY_CLASSES = ["caries", "deep_caries"]
BONE_LOSS_CLASSES = ["normal", "bone_loss"]
BONE_LOSS_SEVERITY_CLASSES = ["Mild", "Moderate", "Severe"]


def _resnet18(n_classes):
    import torch.nn as nn
    from torchvision.models import resnet18
    m = resnet18(weights=None)
    m.fc = nn.Linear(m.fc.in_features, n_classes)
    return m


def load_classifier(weights, n_classes, device):
    """
    Load one ResNet18 head. Accepts both artefact shapes present in this repo: a bare
    state_dict, and a bundle {'model_state_dict', 'class_to_idx'}.

    Returns (model, class_to_idx_or_None). `strict=True` is deliberate -- a silently partial
    load is exactly the failure this pipeline cannot detect downstream.
    """
    import torch
    ck = torch.load(weights, map_location="cpu", weights_only=False)
    class_to_idx = None
    if isinstance(ck, dict) and "model_state_dict" in ck:
        class_to_idx, sd = ck.get("class_to_idx"), ck["model_state_dict"]
    else:
        sd = ck
    model = _resnet18(n_classes)
    model.load_state_dict(sd, strict=True)
    # eval() is load-bearing: ResNet18 carries BatchNorm, and in train mode each tooth's
    # prediction would depend on which other teeth happened to share its batch.
    return model.to(device).eval(), class_to_idx


def crop_batch(img_bgr, boxes, expand, device):
    """
    Crops for every box under one branch's expansion factor, as a normalised NCHW tensor.

    `expand` is (fw, fh) -- the two factors differ for bone loss and must not be collapsed.
    Mirrors src/fdi_head_inference._batch: cv2 resize, explicit BGR->RGB, ImageNet normalise.
    """
    import cv2
    import torch
    from torchvision import transforms
    from src.crop_generator import compute_expanded_bbox

    import math
    tf = transforms.Compose([transforms.ToTensor(),
                             transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
    H, W = img_bgr.shape[:2]
    fw, fh = expand
    out = []
    for x1, y1, x2, y2 in boxes:
        x, y, w, h = x1, y1, x2 - x1, y2 - y1
        if (fw, fh) == (1.0, 1.0):
            # The tight-crop contract is floor the near corner, CEIL the far edge -- not
            # compute_expanded_bbox's int() on both, which would shave up to a pixel off the
            # distal edge. Matches scripts/dentex/build_dentex_crops.py, whose output was
            # verified pixel-for-pixel against the original caries notebooks.
            cx1, cy1 = max(0, math.floor(x)), max(0, math.floor(y))
            cx2, cy2 = min(W, math.ceil(x + w)), min(H, math.ceil(y + h))
        else:
            cx1, cy1, cx2, cy2 = compute_expanded_bbox(x, y, w, h, W, H, fw=fw, fh=fh)
            cx1, cy1, cx2, cy2 = int(cx1), int(cy1), int(cx2), int(cy2)
        cx2, cy2 = max(cx2, cx1 + 1), max(cy2, cy1 + 1)
        patch = img_bgr[cy1:cy2, cx1:cx2]
        if patch.size == 0:
            patch = np.zeros((CROP_SIZE, CROP_SIZE, 3), np.uint8)
        patch = cv2.resize(patch, (CROP_SIZE, CROP_SIZE))
        out.append(tf(cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)))
    return torch.stack(out).to(device)


def _probs(model, batch):
    import torch
    with torch.no_grad():
        return torch.softmax(model(batch), dim=1).cpu().numpy()


_ISOTONIC = "unloaded"          # sentinel: distinguishes "not tried" from "absent"


def _isotonic_knots():
    """Load the caries gate's isotonic calibrator, or None if it is not on disk.

    CONFIDENCE ONLY -- never the verdict. Isotonic remaps the score axis, so applying it to the
    decision would flip 18% of verdicts (155 of 863 on the held-out test set) and invalidate
    every downstream caries number: the in-pipeline caries rate, the DENTEX lesion agreement,
    and the four Ningxia hospital figures, the last of which would cost another touch on locked
    external data. Reporting a calibrated probability alongside an unchanged verdict buys the
    calibration (test ECE 0.136 -> 0.043) for free. RESULTS_LOG 2026-08-27s.

    Absent file is not an error: the pipeline then reports raw confidence, exactly as before.
    """
    global _ISOTONIC
    if _ISOTONIC == "unloaded":
        import json
        from pathlib import Path
        f = Path(__file__).resolve().parents[1] / "models/09_caries_gate_v3/isotonic_calibrator.json"
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            _ISOTONIC = (np.asarray(d["x"], dtype=float), np.asarray(d["y"], dtype=float))
        except Exception:
            _ISOTONIC = None
    return _ISOTONIC


def run_caries(gate, severity, img_bgr, boxes, device):
    """
    Caries cascade on TIGHT crops. Gate first; the severity head only sees teeth the gate
    called positive, which is what it was trained on (both its classes are carious).

    Returns one dict per box. `label` is the reported finding; `no_caries` teeth are not
    passed to severity and carry severity None -- running it anyway would put out-of-domain
    input through a model whose two classes are both caries grades.
    """
    if len(boxes) == 0:
        return []
    batch = crop_batch(img_bgr, boxes, CARIES_EXPAND, device)
    pg = _probs(gate, batch)
    idx_caries = CARIES_GATE_CLASSES.index("caries")

    positives = [i for i in range(len(boxes)) if int(pg[i].argmax()) == idx_caries]

    # Calibrated P(caries) for REPORTING. The verdict above is already decided from the raw
    # argmax and is deliberately not recomputed here -- that ordering is the whole point.
    knots = _isotonic_knots()
    p_caries_cal = (np.interp(pg[:, idx_caries], knots[0], knots[1])
                    if knots is not None else None)
    ps = _probs(severity, batch[positives]) if positives else np.empty((0, 2))
    sev_of = {i: ps[k] for k, i in enumerate(positives)}

    results = []
    for i in range(len(boxes)):
        r = {
            # The cascade's outcome is three-way: the gate rejects, or the severity head
            # grades what the gate passed. Reporting the gate label separately as well would
            # be two fields that can only ever agree.
            "finding": "no_caries",
            # RAW, unchanged. scripts/eval/lesion_localization.py reads this field, and every
            # published caries number was measured against it, so its meaning must not move.
            "gate_confidence": round(float(pg[i].max()), 4),
            "severity": None,
            "severity_confidence": None,
            # Stated on EVERY tooth, positive or not. Precision is 0.40, and the negative
            # class rests on the presumed-negative assumption, so a negative here is no more
            # trustworthy than a positive. See the module docstring.
            # `caries_uncalibrated` stays on every tooth even when a calibrated confidence is
            # reported: it carries the precision-0.40 and presumed-negative caveats, which
            # calibration does not touch. `caries_confidence_isotonic` marks the separate fact
            # that gate_confidence_calibrated exists and which transform produced it.
            "flags": ["caries_uncalibrated"],
        }
        if p_caries_cal is not None:
            pc = float(p_caries_cal[i])
            # Confidence in the REPORTED finding, so it is 1-p for a negative verdict.
            r["gate_confidence_calibrated"] = round(pc if i in sev_of or
                                                    int(pg[i].argmax()) == idx_caries
                                                    else 1.0 - pc, 4)
            r["flags"].append("caries_confidence_isotonic")
        if i in sev_of:
            p = sev_of[i]
            r["finding"] = CARIES_SEVERITY_CLASSES[int(p.argmax())]   # caries | deep_caries
            r["severity"] = r["finding"]
            r["severity_confidence"] = round(float(p.max()), 4)
        results.append(r)
    return results


def lesion_preds_to_tooth_idx(lesion_boxes, tooth_boxes):
    """
    Map lesion-DETECTOR predictions onto tooth boxes for a Stage-3 verdict (Lever B, adopted
    4 Sep 2026 -- RESULTS_LOG 2026-09-04b; pre-registration
    `outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md` Sec 4 / Sec 7 risk 3).

    Each predicted lesion box is assigned to the SINGLE tooth box with the greatest overlap
    (intersection area / lesion-box area -- "argmax containment"), not centroid-in-ANY-box: a
    lesion box straddling two adjacent, slightly-overlapping tooth boxes must mark exactly one
    tooth positive, not both, or predicted-positive-rate is inflated past the pre-reg's Sec 6
    cond. 2 cap. A lesion with 0 overlap with every tooth box (a spurious detection outside all
    detected teeth) maps to nothing -- it cannot manufacture a positive tooth from thin air.

    Moved here from `scripts/eval/ningxia_external.py` on adoption -- this is now a Stage-3
    production primitive (used by `run_caries_lesion_detector` below), not an eval-only helper,
    so it belongs beside `run_caries`, not upstream of it. The three eval scripts
    (`ningxia_external.py`, `cariesxrays_external.py`, `lesion_localization.py`) import it from
    here now.

    Returns (positive tooth indices, best-overlap confidence per positive index) -- the
    confidence dict lets the Stage-3 report cite a real per-tooth score instead of inventing one.
    """
    best = {}   # tooth idx -> (best_frac, lesion_conf)
    for (lx1, ly1, lx2, ly2), lconf in lesion_boxes:
        larea = max(0.0, lx2 - lx1) * max(0.0, ly2 - ly1)
        if larea <= 0:
            continue
        best_i, best_frac = None, 0.0
        for i, (tx1, ty1, tx2, ty2) in enumerate(tooth_boxes):
            ix1, iy1 = max(lx1, tx1), max(ly1, ty1)
            ix2, iy2 = min(lx2, tx2), min(ly2, ty2)
            inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
            frac = inter / larea
            if frac > best_frac:
                best_i, best_frac = i, frac
        if best_i is not None and (best_i not in best or lconf > best[best_i][1]):
            best[best_i] = (best_frac, lconf)
    return sorted(best), {i: v[1] for i, v in best.items()}


def run_lesion_detector_raw(lesion_model, img_bgr, conf=0.25):
    """
    Run the caries-LESION detector on the plain upright image -- NO rotation.

    `src.orientation.detect_upright()` is hardcoded to the tooth DETECTOR's convention (always
    rotate 90 deg CCW before inference, always un-rotate the output -- DEFAULT = CCW, no
    identity/no-op direction exists). The lesion model was trained on CariesXrays + DENTEX
    images fed NATIVELY UPRIGHT, no rotation anywhere in their dataset builders. Reusing
    `detect_upright` here would silently rotate every image 90 deg before the lesion model sees
    it -- geometrically wrong predictions that would still produce a plausible-looking number.
    `img_bgr` here is already the upright frame `run_pipeline` works in throughout (Stage 1's
    boxes are already un-rotated back to it), so no transform is needed -- just don't add one.

    Returns [(xyxy_box, confidence), ...] in the image's own (upright) pixel frame.
    """
    r = lesion_model.predict(img_bgr, imgsz=1024, conf=conf, iou=0.50, verbose=False)[0]
    boxes = r.boxes.xyxy.cpu().numpy().tolist()
    confs = r.boxes.conf.cpu().numpy().tolist()
    return list(zip(boxes, confs))


def run_caries_lesion_detector(lesion_model, severity, img_bgr, boxes, device, conf=0.25):
    """
    Caries Stage 3, LESION-DETECTOR path -- the pipeline default since 4 Sep 2026 (Lever B,
    RESULTS_LOG 2026-09-04b). Localises the lesion directly instead of classifying the tooth
    crop, which escapes the base-rate dominance the crop classifier (`run_caries`, retained
    below and still selectable via `--caries-method gate`) could not
    (`PAPER_MATERIAL.md` Sec 8.22/8.24/8.25): across this project's six cohorts, an image-blind
    constant tied or beat the gate everywhere. The lesion detector decisively beats both the
    gate and that constant on CariesXrays (+37/+12 pp) and Ningxia (+9/+10 pp, both CI excluding
    zero); on DENTEX it is a statistical TIE with both (CI including zero) -- not a third win,
    recorded as such rather than rounded up.

    Mechanism: run the lesion detector ONCE on the whole image (a detection model, not a
    per-crop classifier -- there is no "gate crop" here), map each predicted lesion box to the
    tooth box it overlaps most (`lesion_preds_to_tooth_idx`, argmax containment), then grade
    severity on flagged teeth with the SAME severity classifier and tight-crop convention
    `run_caries` used -- severity was never part of what Lever B tested or replaced, so it is
    reused unchanged rather than reinvented.

    Confidence threshold is FROZEN at 0.25 (the ultralytics default) per the pre-registration --
    not tuned on any cohort, including this one.

    Returns one dict per box, matching `run_caries`'s exact shape (`finding`, `gate_confidence`,
    `severity`, `severity_confidence`, `flags`) so `build_report` and every downstream consumer
    (the CLI, the Streamlit app, the report schema) need no change to consume either path.
    """
    if len(boxes) == 0:
        return []
    lesion_preds = run_lesion_detector_raw(lesion_model, img_bgr, conf=conf)
    positives, conf_of = (lesion_preds_to_tooth_idx(lesion_preds, boxes)
                          if lesion_preds else ([], {}))

    batch = crop_batch(img_bgr, boxes, CARIES_EXPAND, device) if positives else None
    ps = _probs(severity, batch[positives]) if positives else np.empty((0, 2))
    sev_of = {i: ps[k] for k, i in enumerate(positives)}

    results = []
    for i in range(len(boxes)):
        r = {
            "finding": "no_caries",
            # A DETECTION confidence (the best-overlap lesion box's own score), not a softmax
            # over {caries, no_caries} the way the gate's gate_confidence was -- there is no
            # natural "confidence of absence" for a model that only ever emits positive boxes.
            # 0.0 on a negative tooth means "no lesion box mapped here", not "0% confidence
            # healthy". Flagged below so this is never misread as the old field's semantics.
            "gate_confidence": round(float(conf_of.get(i, 0.0)), 4),
            "severity": None,
            "severity_confidence": None,
            "flags": ["lesion_detector_v1.0", "gate_confidence_is_detection_not_softmax"],
        }
        if i in sev_of:
            p = sev_of[i]
            r["finding"] = CARIES_SEVERITY_CLASSES[int(p.argmax())]   # caries | deep_caries
            r["severity"] = r["finding"]
            r["severity_confidence"] = round(float(p.max()), 4)
        results.append(r)
    return results


def run_bone_loss(binary, severity, img_bgr, boxes, device):
    """
    Bone-loss cascade on 1.5xW / 2.0xH crops. Binary first; severity only on positives, which
    is how it was trained (all three of its classes are degrees of bone loss).
    """
    if len(boxes) == 0:
        return []
    batch = crop_batch(img_bgr, boxes, BONE_LOSS_EXPAND, device)
    pb = _probs(binary, batch)
    idx_pos = BONE_LOSS_CLASSES.index("bone_loss")

    positives = [i for i in range(len(boxes)) if int(pb[i].argmax()) == idx_pos]
    ps = _probs(severity, batch[positives]) if positives else np.empty((0, 3))
    sev_of = {i: ps[k] for k, i in enumerate(positives)}

    results = []
    for i in range(len(boxes)):
        r = {
            "finding": BONE_LOSS_CLASSES[int(pb[i].argmax())],
            "confidence": round(float(pb[i].max()), 4),
            "severity": None,
            "severity_confidence": None,
            "flags": [],
        }
        if i in sev_of:
            p = sev_of[i]
            r["severity"] = BONE_LOSS_SEVERITY_CLASSES[int(p.argmax())]
            r["severity_confidence"] = round(float(p.max()), 4)
            # n=6 in the Mild training class (T0.5, still open). Reported, not suppressed.
            if r["severity"] == "Mild":
                r["flags"].append("severity_class_low_support")
        results.append(r)
    return results
