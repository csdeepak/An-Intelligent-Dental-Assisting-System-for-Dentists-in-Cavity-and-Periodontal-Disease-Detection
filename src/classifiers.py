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
    ps = _probs(severity, batch[positives]) if positives else np.empty((0, 2))
    sev_of = {i: ps[k] for k, i in enumerate(positives)}

    results = []
    for i in range(len(boxes)):
        r = {
            # The cascade's outcome is three-way: the gate rejects, or the severity head
            # grades what the gate passed. Reporting the gate label separately as well would
            # be two fields that can only ever agree.
            "finding": "no_caries",
            "gate_confidence": round(float(pg[i].max()), 4),
            "severity": None,
            "severity_confidence": None,
            # Stated on EVERY tooth, positive or not. Precision is 0.40, and the negative
            # class rests on the presumed-negative assumption, so a negative here is no more
            # trustworthy than a positive. See the module docstring.
            "flags": ["caries_uncalibrated"],
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
