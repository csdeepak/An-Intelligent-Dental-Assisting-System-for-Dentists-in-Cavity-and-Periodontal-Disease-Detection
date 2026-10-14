#!/usr/bin/env python
"""Turn the traced pipeline run on one DENTEX image into the composition's data and assets.

    python brag-output/work/prep_data.py <dentex_input.png> <dentex_label.json>

Reads  work/trace/<stem>_report.json, work/trace/<stem>_lesions.json, work/timeline.json.
Writes work/site/data.js and work/site/assets/{opg.jpg, crop_fdi.png, crop_s4.png}.
Everything shown in the architecture section comes from these files: no box, code or score in
the video is typed by hand.
"""

import json
import sys
from pathlib import Path

import cv2

WORK = Path(__file__).resolve().parent
REPO = WORK.parents[1]
sys.path.insert(0, str(REPO))
from src.classifiers import lesion_preds_to_tooth_idx  # noqa: E402

SITE = WORK / "site"
CROP_TOOTH_FDI, CROP_TOOTH_S4 = 16, 48       # the two teeth whose crops are shown


def expand(box, fx, fy, w, h):
    x1, y1, x2, y2 = box
    cx, cy, bw, bh = (x1 + x2) / 2, (y1 + y2) / 2, (x2 - x1) * fx, (y2 - y1) * fy
    return [max(0, cx - bw / 2), max(0, cy - bh / 2), min(w, cx + bw / 2), min(h, cy + bh / 2)]


def main():
    img_path, label_path = Path(sys.argv[1]), Path(sys.argv[2])
    stem = img_path.stem
    report = json.loads((WORK / "trace" / f"{stem}_report.json").read_text())
    lesions = json.loads((WORK / "trace" / f"{stem}_lesions.json").read_text())
    timeline = json.loads((WORK / "timeline.json").read_text())
    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]

    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(SITE / "assets" / "opg.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 93])
    overlay = cv2.imread(str(WORK / "trace" / f"{stem}_overlay.jpg"))     # run_inference's own overlay
    cv2.imwrite(str(SITE / "assets" / "overlay.jpg"),
                cv2.resize(overlay, (1200, round(1200 * h / w)), interpolation=cv2.INTER_AREA),
                [cv2.IMWRITE_JPEG_QUALITY, 90])

    teeth = report["teeth"]
    by_fdi = {t["fdi"]: t for t in teeth}
    # the report sorts teeth by FDI; the mapping below works on detection order, as the pipeline does
    det_order = sorted(teeth, key=lambda t: t["detection_index"])
    boxes = [t["bbox_xyxy"] for t in det_order]
    lesion_list = [(tuple(b), c) for b, c in lesions]
    positives, _ = lesion_preds_to_tooth_idx(lesion_list, boxes)

    def owner(lbox):                                  # the tooth each lesion box went to
        best, best_frac = None, 0.0
        lx1, ly1, lx2, ly2 = lbox
        la = max(0.0, lx2 - lx1) * max(0.0, ly2 - ly1)
        for t, (tx1, ty1, tx2, ty2) in zip(det_order, boxes):
            iw, ih = max(0.0, min(lx2, tx2) - max(lx1, tx1)), max(0.0, min(ly2, ty2) - max(ly1, ty1))
            frac = iw * ih / la if la else 0.0
            if frac > best_frac:
                best, best_frac = t["fdi"], frac
        return best

    lesion_out = [{"box": [round(v, 1) for v in b], "conf": round(c, 3), "tooth": owner(b)}
                  for b, c in lesion_list]
    flagged = sorted({det_order[i]["fdi"] for i in positives})
    assert flagged == sorted(t["fdi"] for t in teeth if t["caries"]["finding"] != "no_caries"), \
        "lesion mapping does not reproduce the report's caries flags"

    crops = {}
    for name, fdi, fx, fy in (("crop_fdi", CROP_TOOTH_FDI, 1.5, 1.5), ("crop_s4", CROP_TOOTH_S4, 1.5, 2.0)):
        x1, y1, x2, y2 = [int(round(v)) for v in expand(by_fdi[fdi]["bbox_xyxy"], fx, fy, w, h)]
        cv2.imwrite(str(SITE / "assets" / f"{name}.png"), img[y1:y2, x1:x2])
        crops[name] = {"fdi": fdi, "box": [x1, y1, x2, y2]}

    gt = json.loads(label_path.read_text(encoding="utf-8", errors="replace"))["shapes"]
    gt_caries = [{"fdi": int(s["label"].split("-")[-1]), "points": s["points"]}
                 for s in gt if s["label"].split("-")[0] == "1"]

    t16 = by_fdi[16]
    record = {k: t16[k] for k in ("bbox_xyxy", "detection_confidence", "fdi", "fdi_confidence",
                                  "caries", "bone_loss", "assessable")}
    data = {
        "timeline": timeline,
        "image": {"w": w, "h": h, "name": img_path.name, "src": "assets/opg.jpg"},
        "teeth": [{"fdi": t["fdi"], "box": t["bbox_xyxy"], "det": t["detection_confidence"],
                   "fdiConf": t["fdi_confidence"], "caries": t["caries"]["finding"],
                   "cariesConf": t["caries"]["gate_confidence"], "sev": t["caries"]["severity"],
                   "abn": t["bone_loss"]["finding"] == "bone_loss",
                   "abnConf": t["bone_loss"]["confidence"], "flags": t["fdi_flags"]}
                  for t in det_order],
        "lesions": lesion_out,
        "crops": crops,
        "gtCaries": gt_caries,
        "record16": record,
        "schema": report["schema_version"],
        "models": {k: {"tag": v.get("tag") or v.get("tag_binary"),
                       "sha": (v.get("sha256") or v.get("sha256_binary") or "")[:12]}
                   for k, v in report["models"].items()},
        "summary": report["summary"],
    }
    (SITE / "data.js").write_text("window.DATA = " + json.dumps(data) + ";\n", encoding="utf-8")
    print(f"teeth {len(teeth)}  lesions {len(lesion_out)} -> flagged {flagged}  "
          f"gt caries teeth {sorted({g['fdi'] for g in gt_caries})}  total {timeline['total']} s")


if __name__ == "__main__":
    main()
