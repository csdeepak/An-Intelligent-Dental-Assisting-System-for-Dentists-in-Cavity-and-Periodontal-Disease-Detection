#!/usr/bin/env python
"""Run the shipped pipeline on DENTEX images and keep every stage's intermediate output.

For the panel-review video only. It calls scripts/run_inference.py's own load_models() and
run_pipeline() with the shipped defaults, unchanged; the one addition is a wrapper around
src.classifiers.run_lesion_detector_raw that records the raw lesion boxes (Stage 3a's own
output), which the report does not keep. No metric is computed and nothing is scored.

    python brag-output/work/trace_pipeline.py <out_dir> <image.png> [<image.png> ...]
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import cv2  # noqa: E402

import src.classifiers as clf  # noqa: E402
import run_inference as ri  # noqa: E402

captured = {}
_raw = clf.run_lesion_detector_raw


def _recording_raw(*a, **k):
    preds = _raw(*a, **k)
    captured["lesions"] = preds
    return preds


clf.run_lesion_detector_raw = _recording_raw


def jsonable(x):
    try:
        import numpy as np
        if isinstance(x, np.ndarray):
            return x.tolist()
        if isinstance(x, (np.floating, np.integer)):
            return x.item()
    except ImportError:
        pass
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    return x


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    models, device, paths = ri.load_models()
    for img_path in map(Path, sys.argv[2:]):
        img = cv2.imread(str(img_path))
        captured.clear()
        report = ri.run_pipeline(img, models, device, paths, image_label=img_path.name)
        stem = img_path.stem
        (out / f"{stem}_report.json").write_text(json.dumps(report, indent=2) + "\n")
        (out / f"{stem}_lesions.json").write_text(
            json.dumps(jsonable(captured.get("lesions", [])), indent=2) + "\n")
        ri.draw_overlay(img, report, out / f"{stem}_overlay.jpg")
        s = report["summary"]
        print(f"{stem}: {img.shape[1]}x{img.shape[0]}  teeth {s['teeth_detected']}  "
              f"distinct {s['distinct_fdi_codes']}  caries+ {s['caries_positive']}  "
              f"stage4+ {s['bone_loss_positive']}  lesion boxes {len(captured.get('lesions', []))}",
              flush=True)


if __name__ == "__main__":
    main()
