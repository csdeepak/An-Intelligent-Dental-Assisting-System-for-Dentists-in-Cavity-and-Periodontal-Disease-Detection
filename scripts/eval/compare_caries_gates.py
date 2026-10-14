"""
Before/after for the caries gate, measured through the assembled pipeline.

WHY THIS EXISTS
---------------
The gate trained on `phase1_legacy` has a negative class of Impacted + Periapical Lesion and
**no healthy teeth**, while the pipeline feeds it every tooth the detector finds. Measured in
situ it called **84.9%** of 299 detected teeth carious against 35 annotated (RESULTS_LOG
2026-08-24f). `crops_v3_phase1` rebuilds that negative class with 5,366 real healthy teeth.

This script runs BOTH gates over the SAME images, with the same detector, the same boxes and
the same crops, so the only thing that differs is the gate checkpoint. Anything else would not
be a controlled comparison.

The reference point is the annotated caries count on the same images. DENTEX's `disease/`
annotates only diseased teeth, so that count is a floor, not a complete label — it is used to
show the ORDER OF MAGNITUDE of over-calling, not to compute a precision.

Usage:
    python scripts/eval/compare_caries_gates.py --n 12
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DEF_DISEASE = Path.home() / "Downloads/Capstone/DENTEX/disease"
OLD_GATE = REPO_ROOT / "models/07_caries_cascade/final_model.pth"
NEW_GATE = REPO_ROOT / "outputs/caries_v3/run/arm_b/phase1_best.pth"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disease-dir", type=Path, default=DEF_DISEASE)
    ap.add_argument("--old-gate", type=Path, default=OLD_GATE)
    ap.add_argument("--new-gate", type=Path, default=NEW_GATE)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "outputs/caries_v3/gate_comparison.json")
    args = ap.parse_args()

    import cv2
    import torch
    from ultralytics import YOLO
    from scripts.run_inference import load_yolo_pinned

    from src.classifiers import CARIES_GATE_CLASSES, crop_batch, load_classifier, CARIES_EXPAND
    from src.orientation import detect_upright

    leaked = set(json.loads((REPO_ROOT / "data/dentex/disease_leaked_images.json").read_text())
                 ["all_excluded"])
    stems = [p.stem for p in sorted((args.disease_dir / "input").glob("*.png"))
             if p.stem not in leaked][:args.n]

    device = torch.device("cuda" if torch.cuda.is_available()
                          else "mps" if torch.backends.mps.is_available() else "cpu")
    det = load_yolo_pinned(REPO_ROOT / "models/06_yolo_detection_a100_run/best.pt")
    old, old_cls = load_classifier(args.old_gate, 2, device)
    new, new_cls = load_classifier(args.new_gate, 2, device)
    print(f"device={device}")
    print(f"  old gate {args.old_gate.name}  class_to_idx={old_cls}")
    print(f"  new gate {args.new_gate.name}  class_to_idx={new_cls}")
    for name, c2i in (("old", old_cls), ("new", new_cls)):
        if c2i and c2i != {"caries": 0, "no_caries": 1}:
            raise SystemExit(f"{name} gate class order unexpected: {c2i}")

    idx_caries = CARIES_GATE_CLASSES.index("caries")
    tot = old_pos = new_pos = gt_caries = 0
    per_image = []
    for stem in stems:
        img = cv2.imread(str(args.disease_dir / "input" / f"{stem}.png"))
        boxes, _ = detect_upright(det, img, imgsz=1024, conf=0.25, iou=0.50, verbose=False)
        if not boxes:
            continue
        batch = crop_batch(img, boxes, CARIES_EXPAND, device)   # identical crops for both
        with torch.no_grad():
            o = torch.softmax(old(batch), 1).argmax(1).cpu().numpy()
            n = torch.softmax(new(batch), 1).argmax(1).cpu().numpy()
        gt = json.loads((args.disease_dir / "label" / f"{stem}.json").read_text())
        g = len({s["label"].split("-")[-1] for s in gt.get("shapes", [])
                 if "çürük" in s["label"]})
        op, np_ = int((o == idx_caries).sum()), int((n == idx_caries).sum())
        tot += len(boxes); old_pos += op; new_pos += np_; gt_caries += g
        per_image.append({"image": stem, "teeth": len(boxes), "old_caries": op,
                          "new_caries": np_, "annotated_caries": g})
        print(f"  {stem:>9}  teeth {len(boxes):>3}   old {op:>3} ({op/len(boxes):5.1%})   "
              f"new {np_:>3} ({np_/len(boxes):5.1%})   annotated {g}")

    res = {"images": len(per_image), "detected_teeth": tot,
           "old_gate": {"weights": str(args.old_gate), "caries_positive": old_pos,
                        "rate": old_pos / tot},
           "new_gate": {"weights": str(args.new_gate), "caries_positive": new_pos,
                        "rate": new_pos / tot},
           "annotated_caries_teeth": gt_caries,
           "note": "annotated count is a FLOOR — DENTEX disease/ labels only diseased teeth. "
                   "Used to show the order of magnitude of over-calling, not a precision.",
           "per_image": per_image}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=2) + "\n")

    print(f"\n{'':<22}{'caries+':>9}{'rate':>9}")
    print(f"  {'OLD (phase1_legacy)':<20}{old_pos:>9}{old_pos/tot:>9.1%}")
    print(f"  {'NEW (crops_v3)':<20}{new_pos:>9}{new_pos/tot:>9.1%}")
    print(f"  {'annotated (floor)':<20}{gt_caries:>9}{gt_caries/tot:>9.1%}")
    print(f"\n  {tot} detected teeth across {len(per_image)} images")
    print(f"  over-call vs annotated:  old {old_pos/max(gt_caries,1):.1f}x   "
          f"new {new_pos/max(gt_caries,1):.1f}x")
    print(f"  -> {args.out}")


if __name__ == "__main__":
    main()
