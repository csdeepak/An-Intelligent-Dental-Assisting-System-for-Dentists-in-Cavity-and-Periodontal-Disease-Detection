"""
Label-free pilot: run the frozen six-stage pipeline over a deterministic sample of a corpus and
record only aggregate per-image behaviour.

This is a feasibility and throughput measurement, NOT an evaluation -- there is no ground truth
on SDH. It produced the 24-image SDH numbers and the matched DENTEX reference numbers in
`RESULTS_LOG.md` 2026-08-30.

Two properties that matter for reproducing those numbers:

  * The sample is deterministic (every Nth file of a sorted listing), so the same images come
    back on a re-run. Every image it touches is BURNED for evaluation -- it has been looked at,
    and `docs/research/SDH_EXECUTION_PLAN.md` §3 requires such images to sit in SDH-DEV.
  * `run_pipeline` is imported from `scripts/run_inference.py` rather than reimplemented, so a
    pipeline change reaches this script automatically.

Note the one-to-one caveat: the pipeline's Hungarian FDI assignment cannot emit a duplicate
code, so `duplicate_fdi` is 0 by construction here. Measuring FDI-consistency violations as a
domain-shift signal needs a run with one-to-one assignment disabled.

Usage:
    python scripts/sdh/pilot_infer.py <n> <out.csv> <image_dir>
    python scripts/sdh/pilot_infer.py 24 data/sdh/pilot_inference_n24.csv "D:/SDH dataset/dataset/images"
"""
import csv
import glob
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.run_inference import load_models, run_pipeline  # noqa: E402


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    n_want, out_path, src = int(sys.argv[1]), sys.argv[2], sys.argv[3]

    files = sorted(glob.glob(os.path.join(src, "*.png")))
    if not files:
        raise SystemExit(f"no PNGs under {src}")
    step = max(1, len(files) // n_want)
    sample = files[::step][:n_want]
    print(f"{len(files)} images, sampling {len(sample)} every {step}", flush=True)

    models, device, paths = load_models()
    print("device", device, flush=True)

    rows = []
    t0 = time.time()
    for i, f in enumerate(sample):
        img = cv2.imread(f, cv2.IMREAD_COLOR)
        if img is None:
            print(f"  SKIP unreadable: {os.path.basename(f)}", flush=True)
            continue
        t1 = time.time()
        rep = run_pipeline(img, models, device, paths,
                           image_label=os.path.basename(f), verbose=False)
        dt = time.time() - t1
        s = rep["summary"]
        confs = [t["detection_confidence"] for t in rep["teeth"]]
        fconfs = [t["fdi_confidence"] for t in rep["teeth"] if t.get("fdi_confidence") is not None]
        gconfs = [t["caries"]["gate_confidence"] for t in rep["teeth"]]
        rows.append({
            "image_id": os.path.splitext(os.path.basename(f))[0],
            "width": img.shape[1], "height": img.shape[0],
            "teeth_detected": s["teeth_detected"],
            "teeth_assessable": s["teeth_assessable"],
            "distinct_fdi": s["distinct_fdi_codes"],
            "duplicate_fdi": s["duplicate_fdi_codes"],
            "caries_positive": s["caries_positive"],
            "bone_loss_positive": s["bone_loss_positive"],
            "det_conf_mean": round(float(np.mean(confs)), 4) if confs else None,
            "det_conf_min": round(float(np.min(confs)), 4) if confs else None,
            "fdi_conf_mean": round(float(np.mean(fconfs)), 4) if fconfs else None,
            "gate_conf_mean": round(float(np.mean(gconfs)), 4) if gconfs else None,
            "seconds": round(dt, 2),
        })
        print(f"  {i+1}/{len(sample)} {rows[-1]['image_id']} teeth={s['teeth_detected']} "
              f"dup={s['duplicate_fdi_codes']} caries={s['caries_positive']} "
              f"bone={s['bone_loss_positive']} {dt:.1f}s", flush=True)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    tt = [r["teeth_detected"] for r in rows]
    el = time.time() - t0
    print("---")
    print(f"total {el:.0f}s for {len(rows)} images ({el/len(rows):.1f}s/img on {device})")
    print("teeth/img  min/median/max:", min(tt), int(np.median(tt)), max(tt))
    print("images with 0 teeth:", sum(1 for x in tt if x == 0))
    print("images with duplicate FDI:", sum(1 for r in rows if r["duplicate_fdi"] > 0),
          "(0 by construction under one-to-one assignment)")
    dc = [r["det_conf_mean"] for r in rows if r["det_conf_mean"]]
    print("mean det conf:", round(float(np.mean(dc)), 4))
    print("mean caries-positive per image:", round(float(np.mean([r["caries_positive"] for r in rows])), 2))
    print("mean bone-loss-positive per image:", round(float(np.mean([r["bone_loss_positive"] for r in rows])), 2))
    print(f"-> {out_path}")


if __name__ == "__main__":
    main()
