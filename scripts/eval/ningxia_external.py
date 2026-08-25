"""
Ningxia external validation — the three §4.3.4 measurements, stratified by centre.

This is contribution **C2**: the first time this pipeline is measured on data from institutions
it has never seen. Ningxia is LOCKED external test data (`MASTER_PLAN_2026H2.md` §4.2): no
threshold tuning, no checkpoint selection, no preprocessing tuning against it. Touched once,
reported as-is.

WHY THIS IS A SEPARATE SCRIPT FROM `lesion_localization.py`
-----------------------------------------------------------
That script's docstring claimed only its GT loader would need a Ningxia sibling, and that
"nothing else in this file assumes the DENTEX format." **That claim was wrong, and it was
written before any real Ningxia mask had been inspected.** Two things do not transfer:

1. **GT format** — DENTEX ships LabelMe polygons; Ningxia ships binary raster masks
   (verified: uint8, values {0,255}, same HxW as the image, one PNG per image).
2. **The matching criterion, which is the substantive one.** DENTEX lesion polygons are
   roughly tooth-sized, so IoU@0.30 against a tooth box works. Ningxia caries lesions are
   *tiny focal blobs* — measured on real masks: 89 to 3,090 px, versus a ~25,000 px tooth box.
   A lesion sitting ENTIRELY inside the correct tooth would score IoU 0.015–0.124 — **every
   one of them below the 0.30 threshold.** Reusing the DENTEX matcher unchanged would have
   reported ~0% agreement and looked like catastrophic domain-shift failure, when it would
   have been a pure artefact of the matching criterion.

So for CARIES this script matches by **centroid containment**: is a lesion's centroid inside
the box of a tooth the pipeline flagged? For a small focal lesion on a tooth, that is precisely
the question §4.3.4 asks, and it is decisive where any-pixel-overlap would double-count a
lesion straddling two adjacent teeth.

THE METRIC MUST DIFFER BY CATEGORY -- caries and periodontitis are not the same kind of object
-------------------------------------------------------------------------------------------
A first version of this script applied centroid containment to BOTH categories and reported
0.7-4.0% agreement for periodontitis. **Those numbers were a measurement artefact and are
withdrawn.** Measured on real masks:

    caries        2.5 blobs/image, median blob    731 px   (focal spots on crowns)
    periodontitis 1.0 blob /image, median blob 365,680 px  (~500x larger)

Periodontitis masks are not lesions at all -- they are a SINGLE continuous band spanning the
whole alveolar ridge, ~8% of the entire radiograph, visually confirmed
(`outputs/ningxia_check/periodontitis_mask.jpg`). The centroid of such a band lands in the gap
between teeth, inside no tooth box, so centroid matching scores ~0% BY CONSTRUCTION no matter
how good the model is. Reporting that as "the bone-loss branch fails externally" would have
been a false conclusion drawn from a broken metric.

Periodontitis is therefore scored by **affected-tooth sensitivity**: a detected tooth counts as
affected if >=50% of its box lies inside the expert-marked region, and sensitivity is the
fraction of those teeth the pipeline flagged. That is a per-tooth question the pipeline can
actually answer, and it is the honest analogue of the caries metric for a diffuse condition.

VERIFIED PROPERTIES OF THIS DATASET (checked directly, not assumed)
-------------------------------------------------------------------
* **Upright already.** All sampled images are landscape (W>H) and visually confirmed as
  upright panoramics — maxilla above, mandible below. **No rotation is applied here.** Tufts
  needs 90° CCW; DENTEX and Ningxia do not. That difference is per-dataset and was checked,
  not inferred (getting it wrong for Tufts cost this project a full correction — RESULTS_LOG
  2026-08-22d).
* **Per-centre heterogeneity is real and visible**: test1 2893×1480 single-channel with
  burned-in annotation arrows/stars; test2 2440×1292 3-channel; test3 2440×1280; test4
  2424×1328 with a burned-in letter marker. `cv2.imread` (IMREAD_COLOR) normalises the
  channel difference; the resolution and artefact differences are exactly the domain shift
  C2 exists to measure.
* **Centre stratification is safe**: no image appears in more than one segmentation split
  (checked by MD5 over all 1,640 segmentation test images). 549 images legitimately appear
  under more than one *disease category* — multi-condition patients, each with its own mask —
  which is why results are reported per category, never pooled across categories.
* **Zero leakage** against Tufts, DENTEX `disease/`, `quadrant_enumeration`,
  `quadrant-enumeration-disease` and `quadrant`, each checked separately (0/2,912 unique
  Ningxia test hashes). Ningxia is genuinely external.

WHAT IS AND IS NOT EVALUATED
-----------------------------
`impacted_teeth` is skipped: this pipeline has no impaction branch, so there is nothing to
score against those masks. `dental_caries` masks are scored against caries-positive teeth;
`periodontitis` masks against bone-loss-positive teeth — **the first external test of the
bone-loss branch this project has ever had** (DENTEX carries no periodontal ground truth).

Specificity/AUC are NOT computed and cannot be: Ningxia has no healthy controls
(`MASTER_PLAN_2026H2.md` §4.3, corrected 18 Aug). Those come from Tufts. Per the same section:
**never synthesise negatives from the other disease categories.**

Usage:
    python scripts/eval/ningxia_external.py --limit 20      # smoke
    python scripts/eval/ningxia_external.py                 # full
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DEF_ROOT = Path.home() / "Downloads/Capstone/ningxia_local"
DEF_OUT = REPO_ROOT / "outputs/ningxia_external"

# Only the categories this pipeline actually predicts. impacted_teeth has no branch.
CATEGORY_BRANCH = {"dental_caries": "caries", "periodontitis": "bone_loss"}
SPLITS = ["test1", "test2", "test3", "test4"]
# From the dataset's own ReadMe: test2 shares a centre with train; the rest are cross-centre.
SPLIT_CENTRE = {"test1": "cross_centre", "test2": "same_centre_as_train",
                "test3": "cross_centre", "test4": "cross_centre"}
MIN_LESION_PX = 20   # ignore specks; the smallest real blob measured was 89 px


def lesions_from_mask(mask_path, min_px=MIN_LESION_PX):
    """
    Ningxia GT loader. Each connected component of the binary mask is ONE lesion instance,
    mirroring how each DENTEX polygon is one instance. Returns centroid + bbox in the image's
    own pixel coordinates (masks are the same HxW as their image -- verified).
    """
    import cv2
    import numpy as np
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        return None
    n, _, stats, cent = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8), connectivity=8)
    out = []
    for i in range(1, n):                       # 0 is background
        if stats[i, cv2.CC_STAT_AREA] < min_px:
            continue
        x, y = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP]
        w, h = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        out.append({"centroid": [float(cent[i][0]), float(cent[i][1])],
                    "bbox": [float(x), float(y), float(x + w), float(y + h)],
                    "area_px": int(stats[i, cv2.CC_STAT_AREA])})
    return out


def affected_tooth_sensitivity(mask_path, all_boxes, positive_idx, min_frac=0.50):
    """
    The RIGHT metric for a DIFFUSE condition (periodontitis), where centroid containment is
    meaningless -- see the module docstring.

    Periodontitis masks are not focal lesions: measured on real data they are a SINGLE band
    of ~365,000 px (median) spanning the whole alveolar ridge, versus ~731 px focal spots for
    caries. The centroid of such a band lands in the gap between teeth, inside no tooth box,
    so centroid matching scores ~0% by construction regardless of model quality.

    Instead: a detected tooth counts as AFFECTED if at least `min_frac` of its box area lies
    inside the expert-marked region. Sensitivity is then the fraction of affected teeth the
    pipeline actually flagged -- a per-tooth question the pipeline can genuinely answer.

    Returns (n_affected, n_affected_flagged).
    """
    import cv2
    import numpy as np
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        return 0, 0
    mb = (m > 0)
    H, W = mb.shape
    pos = set(positive_idx)
    n_aff = n_hit = 0
    for i, b in enumerate(all_boxes):
        x1, y1 = max(0, int(b[0])), max(0, int(b[1]))
        x2, y2 = min(W, int(b[2])), min(H, int(b[3]))
        if x2 <= x1 or y2 <= y1:
            continue
        sub = mb[y1:y2, x1:x2]
        if sub.size and sub.mean() >= min_frac:
            n_aff += 1
            if i in pos:
                n_hit += 1
    return n_aff, n_hit


def match_by_centroid(lesions, boxes):
    """
    Returns (covered, strict) -- two counts that BOUND the answer, because the right
    lesion→tooth cardinality is genuinely ambiguous and picking one silently would be a
    choice disguised as a fact.

      covered (many-to-one, PRIMARY): a lesion is localised if its centroid falls inside ANY
        flagged tooth box. This is the faithful reading of §4.3.4's per-lesion question -- if
        one tooth carries two carious lesions (mesial + distal surfaces, entirely normal) and
        we flagged that tooth, BOTH lesions are genuinely localised.
      strict (one-to-one, SECONDARY): each flagged tooth may claim at most one lesion, greedy
        by lesion area. This under-counts a multi-lesion tooth on purpose, and so caps
        agreement at the number of flagged teeth -- a conservative floor.

    Matching is by centroid containment, not IoU: see the module docstring for the measured
    reason (Ningxia lesions are 89-3,090 px against ~25,000 px tooth boxes, so every true
    match would score IoU well below any sane threshold).
    """
    covered = 0
    for l in lesions:
        cx, cy = l["centroid"]
        if any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in boxes):
            covered += 1

    used, strict = set(), 0
    for li in sorted(range(len(lesions)), key=lambda i: -lesions[i]["area_px"]):
        cx, cy = lesions[li]["centroid"]
        for bi, b in enumerate(boxes):
            if bi in used:
                continue
            if b[0] <= cx <= b[2] and b[1] <= cy <= b[3]:
                used.add(bi)
                strict += 1
                break
    return covered, strict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEF_ROOT)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--limit", type=int, default=None, help="first N images per category/split")
    args = ap.parse_args()

    import cv2
    import torch
    from ultralytics import YOLO

    from src.classifiers import load_classifier, run_bone_loss, run_caries
    from src.fdi_head_inference import assign_fdi_head, load_head
    from src.orientation import detect_upright

    device = torch.device("cuda" if torch.cuda.is_available()
                          else "mps" if torch.backends.mps.is_available() else "cpu")
    det = YOLO(str(REPO_ROOT / "models/06_yolo_detection_a100_run/best.pt"))
    head = load_head(REPO_ROOT / "models/08_fdi_enumeration_head/enumeration_head_best.pth", device)
    gate, gate_cls = load_classifier(REPO_ROOT / "models/09_caries_gate_v3/caries_gate_v3.pth", 2, device)
    csev, csev_cls = load_classifier(REPO_ROOT / "models/07_caries_cascade/phase2_final_bundle.pth", 2, device)
    bbin, _ = load_classifier(REPO_ROOT / "models/03_bone_loss_model_training_notebook_models/bone_loss_resnet18_best.pth", 2, device)
    bsev, _ = load_classifier(REPO_ROOT / "models/04_bone_loss_severity_notebook_models/bone_loss_severity_resnet18_best.pth", 3, device)
    if gate_cls and gate_cls != {"caries": 0, "no_caries": 1}:
        raise SystemExit(f"caries gate class order changed: {gate_cls}")
    if csev_cls and csev_cls != {"caries": 0, "deep_caries": 1}:
        raise SystemExit(f"caries severity class order changed: {csev_cls}")
    print(f"device={device}")

    agg = defaultdict(lambda: defaultdict(int))
    per_image = []

    for category, branch in CATEGORY_BRANCH.items():
        for split in SPLITS:
            img_dir = args.root / "segmentation" / category / split / "img"
            msk_dir = args.root / "segmentation" / category / split / "mask"
            files = sorted(img_dir.glob("*.png"))
            if args.limit:
                files = files[:args.limit]
            for f in files:
                img = cv2.imread(str(f), cv2.IMREAD_COLOR)   # normalises 1- vs 3-channel
                if img is None:
                    agg[(category, split)]["unreadable"] += 1
                    continue
                lesions = lesions_from_mask(msk_dir / f.name)
                if lesions is None:
                    agg[(category, split)]["mask_missing"] += 1
                    continue

                # NOTE: no rotation. Ningxia and DENTEX are upright; only Tufts needs CCW.
                boxes, _ = detect_upright(det, img, imgsz=1024, conf=0.25, iou=0.50,
                                          verbose=False)
                fdi = assign_fdi_head(head, img, boxes, device) if boxes else []
                if branch == "caries":
                    preds = run_caries(gate, csev, img, boxes, device) if boxes else []
                    pos = [i for i, p in enumerate(preds) if p["finding"] != "no_caries"]
                else:
                    preds = run_bone_loss(bbin, bsev, img, boxes, device) if boxes else []
                    pos = [i for i, p in enumerate(preds) if p["finding"] == "bone_loss"]

                k = (category, split)
                if branch == "caries":
                    # focal lesions -> centroid containment is the right question
                    covered, strict = (match_by_centroid(lesions, [boxes[i] for i in pos])
                                       if pos else (0, 0))
                    agg[k]["lesions"] += len(lesions)
                    agg[k]["lesions_covered"] += covered
                    agg[k]["lesions_strict"] += strict
                else:
                    # diffuse region -> per-tooth "was an affected tooth flagged"
                    covered = strict = 0
                    n_aff, n_hit = affected_tooth_sensitivity(
                        msk_dir / f.name, boxes, pos)
                    agg[k]["affected_teeth"] += n_aff
                    agg[k]["affected_teeth_flagged"] += n_hit
                agg[k]["images"] += 1
                agg[k]["teeth_detected"] += len(boxes)
                agg[k]["predicted_positive"] += len(pos)
                # measurement 2: image-level sensitivity -- did we flag >=1 diseased tooth?
                agg[k]["images_flagged"] += 1 if pos else 0
                # measurement 3: numbering sanity
                codes = [a["fdi"] for a in fdi if a.get("fdi") is not None]
                agg[k]["duplicate_fdi"] += len(codes) - len(set(codes))

                per_image.append({
                    "category": category, "split": split, "centre": SPLIT_CENTRE[split],
                    "image": f.name, "n_lesions": len(lesions),
                    "n_covered": covered, "n_strict": strict, "n_teeth": len(boxes),
                    "n_predicted_positive": len(pos),
                })
            print(f"  {category:15s} {split}  done ({agg[(category,split)]['images']} images)")

    results = {"root": str(args.root), "note": "LOCKED external test data -- evaluated once, "
                                               "no tuning of any kind against it",
               "matching": "centroid containment (NOT IoU -- see module docstring)",
               "rotation_applied": "none (Ningxia is upright, verified)",
               "by_category_split": {}, "per_image": per_image}

    print(f"\n{'='*82}")
    print(f"{'category':16s}{'split':7s}{'centre':22s}{'imgs':>5}{'lesion agree':>14}{'img sens':>10}")
    print("-" * 82)
    for (category, split), d in sorted(agg.items()):
        isens = d["images_flagged"] / d["images"] if d["images"] else 0.0
        entry = {"centre": SPLIT_CENTRE[split], **dict(d),
                 "image_level_sensitivity": round(isens, 4),
                 "mean_teeth_per_image": round(d["teeth_detected"] / max(d["images"], 1), 2)}
        if d["lesions"]:
            la = d["lesions_covered"] / d["lesions"]
            entry["metric"] = "focal lesion centroid containment"
            entry["lesion_agreement_covered"] = round(la, 4)
            entry["lesion_agreement_strict_1to1"] = round(d["lesions_strict"] / d["lesions"], 4)
            shown = f"{d['lesions_covered']:>5}/{d['lesions']:<5}{la:>7.1%}"
        else:
            aff = d["affected_teeth"]
            la = d["affected_teeth_flagged"] / aff if aff else 0.0
            entry["metric"] = "affected-tooth sensitivity (diffuse region)"
            entry["affected_tooth_sensitivity"] = round(la, 4)
            shown = f"{d['affected_teeth_flagged']:>5}/{aff:<5}{la:>7.1%}"
        results["by_category_split"][f"{category}/{split}"] = entry
        print(f"{category:16s}{split:7s}{SPLIT_CENTRE[split]:22s}{d['images']:>5}{shown}{isens:>10.1%}")
    print("=" * 82)
    print("Reported per category and per split, never pooled (§4.3.2).")
    print("Specificity/AUC are NOT computable here -- Ningxia has no healthy controls.")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "ningxia_external.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"-> {args.out}/ningxia_external.json")


if __name__ == "__main__":
    main()
