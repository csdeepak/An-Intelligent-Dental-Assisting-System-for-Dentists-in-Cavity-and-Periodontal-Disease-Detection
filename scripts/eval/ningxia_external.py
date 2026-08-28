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

# CONSTANT ARM -- added 28 Aug 2026.
# On DENTEX an image-blind constant (the eight first and second molars) beats this pipeline on
# BOTH metric families tried: FDI-set F1 0.320 vs 0.294 (RESULTS_LOG 2026-08-28b) and
# lesion-localisation agreement 0.488 vs 0.443, +4.59 pp [+0.60,+8.89] (2026-08-28d).
#
# Whether that holds EXTERNALLY is the open question that decides how strongly the paper can
# state it. Ningxia is a different population with a different caries distribution, so the
# constant is not guaranteed to transfer -- which is exactly why this is worth one of this
# dataset's rationed touches. If the constant also wins here, the finding is cross-dataset
# rather than a DENTEX quirk; if it loses, that is equally informative and must be reported.
MOLAR_CONSTANT = {"16", "17", "26", "27", "36", "37", "46", "47"}

# WEIGHTS ARE NO LONGER HARDCODED (changed 27 Aug 2026).
# They were, and that is exactly why the 25 Aug C2 numbers went stale silently the moment the
# Stage-1 default changed: this script kept loading models/06 (the bbox detector) and models/08
# (FDI head v1.0) with no way to say otherwise and no record in its output of what it had used.
# Defaults now track the live pipeline by importing run_inference's DEF_* constants, so the
# script describes the pipeline instead of a frozen snapshot of it.
#
# To reproduce the ORIGINAL 25 Aug numbers (RESULTS_LOG 2026-08-25d), pass them explicitly:
#   --detector models/06_yolo_detection_a100_run/best.pt
#   --fdi-head models/08_fdi_enumeration_head/enumeration_head_best.pth
# The resolved paths and their SHA-256 go into the output JSON either way, so any results file
# can be traced to the exact weights that produced it.
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from run_inference import (DEF_BONE_LOSS, DEF_BONE_SEVERITY, DEF_CARIES_GATE,
                           DEF_CARIES_SEVERITY, DEF_DETECTOR, DEF_FDI_HEAD)

# Only the categories this pipeline actually predicts. impacted_teeth has no branch.
CATEGORY_BRANCH = {"dental_caries": "caries", "periodontitis": "bone_loss"}
SPLITS = ["test1", "test2", "test3", "test4"]
# From the dataset's own ReadMe: test2 shares a centre with train; the rest are cross-centre.
SPLIT_CENTRE = {"test1": "cross_centre", "test2": "same_centre_as_train",
                "test3": "cross_centre", "test4": "cross_centre"}
MIN_LESION_PX = 20   # ignore specks; the smallest real blob measured was 89 px


def read_mask_2d(mask_path):
    """Read a binary GT mask as a strictly 2-D boolean array. Returns None if unreadable.

    WHY THIS EXISTS -- `cv2.imread` is not the function you think it is here.
    `import ultralytics` MONKEYPATCHES cv2.imread globally, replacing it with
    ultralytics.utils.patches.imread, which ends with:

        return im[..., None] if im.ndim == 2 else im

    so a cv2.IMREAD_GRAYSCALE read returns (H, W, 1), not (H, W). Measured on this machine
    with ultralytics 8.4.123:
        before `import ultralytics`:  cv2.imread(mask, IMREAD_GRAYSCALE).shape == (1480, 2893)
        after:                        (1480, 2893, 1)
    Every mask read in this file happens after the pipeline's `from ultralytics import YOLO`,
    so the patched version is always the one that runs. `affected_tooth_sensitivity` unpacked
    `H, W = mb.shape` and died with "too many values to unpack" on the very first image.

    That is an environment-dependent landmine, not a data problem: the two machines run
    different ultralytics versions (8.4.123 here, 8.4.127 on the macOS box), the patch is
    applied by an unrelated import, and the failure mode for code that *doesn't* unpack the
    shape is silent rather than loud. Normalising in one place is the only safe fix.
    """
    import cv2
    import numpy as np
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        return None
    m = np.asarray(m)
    if m.ndim == 3:
        # (H, W, 1) from the patched reader, or (H, W, 3) if a mask was saved as RGB.
        m = m[..., 0] if m.shape[2] == 1 else m.max(axis=2)
    if m.ndim != 2:
        raise ValueError(f"mask {mask_path} has unusable shape {m.shape}")
    return m > 0


def lesions_from_mask(mask_path, min_px=MIN_LESION_PX):
    """
    Ningxia GT loader. Each connected component of the binary mask is ONE lesion instance,
    mirroring how each DENTEX polygon is one instance. Returns centroid + bbox in the image's
    own pixel coordinates (masks are the same HxW as their image -- verified).
    """
    import cv2
    import numpy as np
    mb = read_mask_2d(mask_path)
    if mb is None:
        return None
    n, _, stats, cent = cv2.connectedComponentsWithStats(mb.astype(np.uint8), connectivity=8)
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
    mb = read_mask_2d(mask_path)
    if mb is None:
        return 0, 0
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
    ap.add_argument("--detector", type=Path, default=DEF_DETECTOR)
    ap.add_argument("--fdi-head", type=Path, default=DEF_FDI_HEAD)
    ap.add_argument("--decision", choices=["pipeline", "constant-molars"], default="pipeline",
                    help="constant-molars flags the eight first/second molars on every image, "
                         "never reading the pixels. See CONSTANT ARM below.")
    ap.add_argument("--caries-gate", type=Path, default=DEF_CARIES_GATE)
    ap.add_argument("--caries-severity", type=Path, default=DEF_CARIES_SEVERITY)
    ap.add_argument("--bone-loss", type=Path, default=DEF_BONE_LOSS)
    ap.add_argument("--bone-severity", type=Path, default=DEF_BONE_SEVERITY)
    ap.add_argument("--categories", nargs="+", default=list(CATEGORY_BRANCH),
                    choices=list(CATEGORY_BRANCH),
                    help="subset to evaluate; a branch's models load only if it is selected")
    ap.add_argument("--tag", default=None,
                    help="label written into the results file, e.g. segdet or control_olddet")
    args = ap.parse_args()

    import cv2
    import torch
    from ultralytics import YOLO

    from src.classifiers import load_classifier, run_bone_loss, run_caries
    from src.fdi_head_inference import assign_fdi_head, load_head
    from src.orientation import detect_upright

    device = torch.device("cuda" if torch.cuda.is_available()
                          else "mps" if torch.backends.mps.is_available() else "cpu")
    categories = {c: CATEGORY_BRANCH[c] for c in args.categories}
    branches = set(categories.values())

    def _need(path, what):
        path = Path(path)
        if not path.exists():
            raise SystemExit(
                f"missing {what}: {path}\n"
                f"  This machine does not have it -- see docs/EXTERNAL_DRIVE.md.\n"
                f"  To evaluate only the branch that IS runnable here, pass e.g.\n"
                f"    --categories periodontitis")
        return path

    def _sha(path):
        import hashlib
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    det = YOLO(str(_need(args.detector, "detector")))
    head = load_head(_need(args.fdi_head, "FDI head"), device)
    used = {"detector": str(args.detector), "detector_sha256": _sha(args.detector),
            "fdi_head": str(args.fdi_head), "fdi_head_sha256": _sha(args.fdi_head)}

    gate = csev = bbin = bsev = None
    if "caries" in branches:
        gate, gate_cls = load_classifier(_need(args.caries_gate, "caries gate"), 2, device)
        csev, csev_cls = load_classifier(_need(args.caries_severity, "caries severity"), 2, device)
        if gate_cls and gate_cls != {"caries": 0, "no_caries": 1}:
            raise SystemExit(f"caries gate class order changed: {gate_cls}")
        if csev_cls and csev_cls != {"caries": 0, "deep_caries": 1}:
            raise SystemExit(f"caries severity class order changed: {csev_cls}")
        used["caries_gate"] = str(args.caries_gate)
        used["caries_gate_sha256"] = _sha(args.caries_gate)
        used["caries_severity"] = str(args.caries_severity)
    if "bone_loss" in branches:
        bbin, _ = load_classifier(_need(args.bone_loss, "bone-loss binary"), 2, device)
        bsev, _ = load_classifier(_need(args.bone_severity, "bone-loss severity"), 3, device)
        # These carry no class_to_idx; the order is confirmed in models/03_.../run_summary.txt.
        used["bone_loss"] = str(args.bone_loss)
        used["bone_loss_sha256"] = _sha(args.bone_loss)
        used["bone_severity"] = str(args.bone_severity)
        used["bone_loss_class_order"] = "[normal, bone_loss] -- confirmed, see run_summary.txt"

    print(f"device={device}")
    print("weights in use:")
    for k, v in used.items():
        if not k.endswith("_sha256"):
            print(f"  {k:18s} {v}")
    print(f"categories: {', '.join(categories)}")

    agg = defaultdict(lambda: defaultdict(int))
    per_image = []

    for category, branch in categories.items():
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
                    if args.decision == "constant-molars":
                        # The image is never read for the VERDICT. Codes come from Stage 2,
                        # already computed above, purely to know which boxes are molars.
                        pos = [i for i, a in enumerate(fdi)
                               if str(a.get("fdi")) in MOLAR_CONSTANT]
                    else:
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
               "tag": args.tag,
               "categories_evaluated": list(categories),
               "weights": used,
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
