#!/usr/bin/env python
r"""
CariesXrays as a SIXTH external cohort for the caries branch — frozen pipeline, no training.

WHY THIS EXISTS
---------------
`PAPER_MATERIAL.md` §8.22/§8.24 establish that an image-blind molar constant is not
distinguishable from this pipeline on tooth-level caries, and §8.12 measures the same
comparison across four Ningxia hospitals (pooled delta -0.89 pp, CI [-4.88, +3.01]) on
**337 images**. This script asks the same question on an independent 6,000-image cohort —
roughly 18x the images — using the SAME matcher, so the answer is comparable rather than
merely adjacent.

Nothing is trained and no checkpoint changes. This is the frozen pipeline, measured on data
it has never seen.

PROVENANCE — RESOLVED, AND CITABLE
----------------------------------
This is the **CariesXrays** benchmark: Chen, Fu, Liu, Pan, Lu & Zhang, "CariesXrays: Enhancing
Caries Detection in Hospital-Scale Panoramic Dental X-rays via Feature Pyramid Contrastive
Learning", AAAI 2024, 38(20) 21940-21948, DOI 10.1609/aaai.v38i20.30196, released at
github.com/Binz-Chen/AAAI2024_CariesXrays. Identity verified against AAAI's OJS, ACM DL and DBLP
rather than the repository README alone (RESULTS_LOG 2026-09-01b).

6,000 images matches the paper exactly. 13,784 non-degenerate boxes here against their stated
13,783 is a +1 (0.007%) counting-convention difference, recorded rather than rounded away.
**Licence is NOT stated** (no LICENSE file; GitHub API reports none), so cite as the authors ask
and describe it as publicly released without an explicit licence.

The XML <path> fields point at `F:\datasets\labeled\source6000-label1-all\all-6021\img`,
consistent with the authors' own working directory. Annotation **exhaustiveness** is not
documented, which is why match_rate below is a diagnostic and never precision.

Leakage was verified three ways before use (RESULTS_LOG 2026-09-01): 0 MD5 overlap with the
DENTEX evaluation pool, the DENTEX training subsets and Ningxia; a positive control
(`train_332` = `test_181`) confirms the perceptual method scores true duplicates at distance 0;
and the dHash distribution over 1.5M pairs has min 2 / mean 23.7 with only 36 pairs <= 5 — the
expected tail for images that all share the same panoramic structure. One caries image matched
three different DENTEX images at distance 2-3, which a real duplicate cannot do, and visual
inspection confirmed different patients.

THE GEOMETRY DEFECT THIS SCRIPT REFUSES TO INHERIT
--------------------------------------------------
**27.3% of the XMLs (1,637 files, 4,055 boxes) carry a WRONG `<size>`** — always the width,
stated as 2648 when the image is really 2440 / 2324 / 2444; the height is always right. A
converter that normalises by the XML `<size>` silently corrupts a quarter of the corpus, which
is precisely how a 90-epoch A100 run was voided once before (RESULTS_LOG 2026-08-27a).

Verified that the COORDINATES are in the true image frame, two ways: no box exceeds the actual
width (0 of 4,055, max xmax/width = 0.809), and rendering boxes onto mismatched images puts
them on teeth rather than displaced right by the ~8.5% the stale width would imply.

**So this script reads width/height from the IMAGE and asserts the XML never overrides it.**

METRIC
------
Identical to the Ningxia caries arm: focal-lesion **centroid containment**, imported from
`ningxia_external.match_by_centroid` rather than reimplemented, so the two cohorts cannot drift
apart. `covered` (many-to-one) is primary; `strict` (one-to-one) is the conservative floor.

`match_rate` (flagged teeth that contain a lesion / flagged teeth) is reported as a DIAGNOSTIC,
never as precision — the corpus's annotation exhaustiveness is unknown, so a flagged tooth with
no box is not a confirmed false positive. Same restraint as §8.11.

Usage:
    python scripts/eval/cariesxrays_external.py --limit 300
    python scripts/eval/cariesxrays_external.py --limit 300 --decision constant-molars
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

DEF_ROOT = Path.home() / "Downloads/Capstone/CariesXrays_Dataset"
DEF_OUT = REPO_ROOT / "outputs/cariesxrays_external"


def lesions_from_voc(xml_path, img_w, img_h):
    """VOC boxes -> lesion centroids, in the ACTUAL image frame.

    img_w/img_h come from the decoded image, never from the XML <size>: 27.3% of those are
    wrong (see the module docstring). The XML size is read only to be reported as a mismatch.
    """
    r = ET.parse(xml_path).getroot()
    s = r.find("size")
    xml_w = int(s.find("width").text) if s is not None else None
    xml_h = int(s.find("height").text) if s is not None else None
    out = []
    for o in r.findall("object"):
        b = o.find("bndbox")
        x1, y1, x2, y2 = (int(float(b.find(k).text)) for k in ("xmin", "ymin", "xmax", "ymax"))
        x1, x2 = max(0, min(x1, img_w)), max(0, min(x2, img_w))
        y1, y2 = max(0, min(y1, img_h)), max(0, min(y2, img_h))
        if x2 <= x1 or y2 <= y1:
            continue
        out.append({"centroid": [(x1 + x2) / 2.0, (y1 + y2) / 2.0],
                    "area_px": float((x2 - x1) * (y2 - y1)),
                    "name": o.find("name").text})
    return out, (xml_w != img_w or xml_h != img_h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEF_ROOT)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--limit", type=int, default=None, help="first N images (sorted by id)")
    ap.add_argument("--sample", type=int, default=None,
                    help="RANDOM sample of N images instead of the first N. Preferred: file ids "
                         "run 415-30,664 and are not shuffled, so a --limit prefix may be a "
                         "single acquisition batch rather than a representative draw.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--decision", choices=["pipeline", "constant-molars", "lesion-detector"],
                    default="pipeline",
                    help="lesion-detector runs a caries-lesion YOLO model instead of the gate "
                         "(Lever B), scored via argmax-containment onto detected tooth boxes.")
    ap.add_argument("--lesion-model", type=Path, default=None,
                    help="required for --decision lesion-detector (Lever B)")
    ap.add_argument("--lesion-conf", type=float, default=0.25,
                    help="frozen per PRE_REGISTRATION.md Sec 7 risk 4 -- not tuned on any cohort")
    ap.add_argument("--manifest", type=Path,
                    default=REPO_ROOT / "data/cariesxrays_det/manifest.csv",
                    help="Lever B frozen eval cohort source -- see --manifest-split")
    ap.add_argument("--manifest-split", choices=["train", "val"], default=None,
                    help="Lever B (PRE_REGISTRATION.md Sec 4, amended 4 Sep): restrict to the "
                         "stems in this manifest split BEFORE --sample/--limit. 'val' = the "
                         "existing 1,200-image held-out split, disjoint from the 4,800 training "
                         "images by construction -- this IS the frozen eval cohort, not a new "
                         "draw. Omit for the old first-N/random-sample-of-all-6000 behaviour.")
    ap.add_argument("--detector", type=Path, default=None,
                    help="override the Stage-1 detector (Lever A Guard 1: swap in an arm's best.pt, "
                         "everything else frozen). Defaults to the pipeline default.")
    ap.add_argument("--allow-train-overlap", action="store_true",
                    help="permit --decision lesion-detector without --manifest-split val. Only "
                         "correct for a lesion model that never saw CariesXrays; see the guard "
                         "below for why it is otherwise a leak.")
    ap.add_argument("--tag", default=None, help="suffix for the output directory")
    args = ap.parse_args()

    import cv2
    import torch
    from ningxia_external import MOLAR_CONSTANT, match_by_centroid
    from run_inference import (DEF_CARIES_GATE, DEF_CARIES_SEVERITY, DEF_DETECTOR,
                               DEF_FDI_HEAD, file_sha256)
    from src.classifiers import (lesion_preds_to_tooth_idx, load_classifier, run_caries,
                                 run_lesion_detector_raw)
    from src.fdi_head_inference import assign_fdi_head, load_head
    from src.orientation import detect_upright
    from ultralytics import YOLO
    from scripts.run_inference import load_yolo_pinned

    device = "cpu"
    det_path = args.detector or DEF_DETECTOR
    print(f"detector: {det_path}")
    det = load_yolo_pinned(det_path)
    head = load_head(DEF_FDI_HEAD, device)

    lesion_model = gate = csev = None
    if args.decision == "lesion-detector":
        if not args.lesion_model:
            raise SystemExit("--decision lesion-detector requires --lesion-model")
        # LEAKAGE GUARD. Unlike the gate and the constant, the adopted lesion detector
        # (models/16, B-pooled) TRAINED on 4,800 CariesXrays images. The default cohort here
        # is a random draw from all 6,000, so ~80% of it is training data -- a run without
        # --manifest-split val would score the model on its own training images and return a
        # number that looks excellent and means nothing. The val split is disjoint from those
        # 4,800 by construction, which is why Lever B was evaluated on it.
        if not args.manifest_split and not args.allow_train_overlap:
            raise SystemExit(
                "--decision lesion-detector on the full corpus overlaps the Lever B training "
                "split (~4,800 of 6,000 images). Pass --manifest-split val for the frozen "
                "held-out cohort, or --allow-train-overlap if this lesion model never saw "
                "CariesXrays.")
        if args.manifest_split == "train" and not args.allow_train_overlap:
            raise SystemExit("--manifest-split train IS the Lever B training data; refusing.")
        lesion_model = load_yolo_pinned(args.lesion_model)
        print(f"lesion model: {args.lesion_model}  conf={args.lesion_conf} (frozen)")
    else:
        gate, gate_cls = load_classifier(DEF_CARIES_GATE, 2, device)
        csev, csev_cls = load_classifier(DEF_CARIES_SEVERITY, 2, device)
        # Same guard ningxia_external applies: a silently reordered class map would invert every
        # verdict while still producing plausible-looking numbers.
        if gate_cls and gate_cls != {"caries": 0, "no_caries": 1}:
            raise SystemExit(f"caries gate class order changed: {gate_cls}")
        if csev_cls and csev_cls != {"caries": 0, "deep_caries": 1}:
            raise SystemExit(f"caries severity class order changed: {csev_cls}")

    files = sorted((args.root / "JPEGImages").glob("*.jpg"))
    manifest_note = "none -- first-N/sample-of-all-6000"
    if args.manifest_split:
        import csv
        with open(args.manifest) as mf:
            keep = {row["stem"] for row in csv.DictReader(mf) if row["split"] == args.manifest_split}
        files = [f for f in files if f.stem in keep]
        manifest_note = f"{args.manifest} split={args.manifest_split} ({len(keep)} stems, {len(files)} resolved)"
        print(f"manifest filter: {manifest_note}")
    if args.sample:
        import random
        files = sorted(random.Random(args.seed).sample(files, min(args.sample, len(files))))
    elif args.limit:
        files = files[:args.limit]
    print(f"CariesXrays external — decision={args.decision}  images={len(files)}")

    per_image = []   # needed for the PAIRED cluster bootstrap between arms
    agg = dict(images=0, unreadable=0, no_xml=0, xml_size_mismatch=0,
               lesions=0, lesions_covered=0, lesions_strict=0,
               teeth_detected=0, teeth_flagged=0, flagged_hitting_a_lesion=0)
    for n, f in enumerate(files, 1):
        img = cv2.imread(str(f), cv2.IMREAD_COLOR)
        if img is None:
            agg["unreadable"] += 1
            continue
        xml = args.root / "Annotations" / (f.stem + ".xml")
        if not xml.exists():
            agg["no_xml"] += 1
            continue
        h, w = img.shape[:2]
        lesions, mismatched = lesions_from_voc(xml, w, h)
        agg["xml_size_mismatch"] += int(mismatched)

        boxes, _ = detect_upright(det, img, imgsz=1024, conf=0.25, iou=0.50, verbose=False)
        if args.decision == "constant-molars":
            # The image is never read for the VERDICT: Stage-2 codes are used only to know
            # which detected boxes are molars.
            fdi = assign_fdi_head(head, img, boxes, device) if boxes else []
            pos = [i for i, a in enumerate(fdi) if str(a.get("fdi")) in MOLAR_CONSTANT]
        elif args.decision == "lesion-detector":
            # Lever B: NOT detect_upright -- see run_lesion_detector_raw's docstring
            # (src/classifiers.py) -- the lesion model expects the plain upright image.
            lesion_preds = run_lesion_detector_raw(lesion_model, img, conf=args.lesion_conf) if boxes else []
            pos, _ = lesion_preds_to_tooth_idx(lesion_preds, boxes) if lesion_preds else ([], {})
        else:
            preds = run_caries(gate, csev, img, boxes, device) if boxes else []
            pos = [i for i, p in enumerate(preds) if p["finding"] != "no_caries"]

        flagged = [boxes[i] for i in pos]
        covered, strict = match_by_centroid(lesions, flagged) if flagged else (0, 0)
        hits = sum(1 for b in flagged
                   if any(b[0] <= l["centroid"][0] <= b[2] and b[1] <= l["centroid"][1] <= b[3]
                          for l in lesions))
        agg["images"] += 1
        agg["lesions"] += len(lesions)
        agg["lesions_covered"] += covered
        agg["lesions_strict"] += strict
        agg["teeth_detected"] += len(boxes)
        agg["teeth_flagged"] += len(flagged)
        agg["flagged_hitting_a_lesion"] += hits
        per_image.append({"image": f.name, "lesions": len(lesions), "covered": covered,
                          "strict": strict, "detected": len(boxes), "flagged": len(flagged),
                          "flagged_hits": hits})
        if n % 50 == 0:
            print(f"  {n}/{len(files)}  agreement so far "
                  f"{agg['lesions_covered']/max(agg['lesions'],1):.4f}", flush=True)

    L = max(agg["lesions"], 1)
    F = max(agg["teeth_flagged"], 1)
    res = {
        "cohort": "CariesXrays — Chen et al., AAAI 2024, 38(20) 21940-21948, DOI 10.1609/aaai.v38i20.30196 (licence not stated)",
        "decision": args.decision,
        "detector": str(det_path),
        "detector_sha256": file_sha256(str(det_path)),
        "lesion_model": (str(args.lesion_model) if args.decision == "lesion-detector" else None),
        "lesion_conf": (args.lesion_conf if args.decision == "lesion-detector" else None),
        "manifest_filter": manifest_note,
        "sampling": (f"random {args.sample}, seed {args.seed}" if args.sample
                     else f"first {args.limit} by id" if args.limit else "all"),
        "n_images_scored": agg["images"],
        "counts": agg,
        "agreement_covered": round(agg["lesions_covered"] / L, 4),
        "agreement_strict": round(agg["lesions_strict"] / L, 4),
        "match_rate_DIAGNOSTIC_not_precision": round(agg["flagged_hitting_a_lesion"] / F, 4),
        "mean_teeth_detected_per_image": round(agg["teeth_detected"] / max(agg["images"], 1), 2),
        "mean_teeth_flagged_per_image": round(agg["teeth_flagged"] / max(agg["images"], 1), 2),
        "matcher": "centroid containment, imported from ningxia_external.match_by_centroid",
        "geometry": "width/height read from the DECODED IMAGE; XML <size> deliberately ignored "
                    "(27.3% of them are wrong)",
        "caveat": "annotation exhaustiveness is unknown, so match_rate is a diagnostic and a "
                  "flagged tooth with no lesion is NOT a confirmed false positive",
        "per_image": per_image,
    }
    print(json.dumps({k: v for k, v in res.items() if k != "per_image"}, indent=2))
    out = args.out if not args.tag else args.out.parent / f"{args.out.name}_{args.tag}"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"cariesxrays_external_{args.decision}.json"
    dest.write_text(json.dumps(res, indent=2) + "\n")
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
