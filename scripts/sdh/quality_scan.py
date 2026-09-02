"""
Per-image quality metrics for the SDH clinic set.

Produced `data/sdh/quality_metrics_enhanced.csv` (n=3,213) -- the substrate for the L2 filter in
`docs/research/SDH_EXECUTION_PLAN.md` §4.

Two deliberate properties:

  * **It never opens `metadata/index.csv`.** That file is the re-identification mapping. Nothing
    written here can be joined back to a patient: the output is keyed by the opaque image ID and
    contains only numbers.
  * **It reports unreadable files rather than skipping them silently.** That is how the six
    truncated images (`001970`-`001975`) were found on the first pass that ever opened all 3,219
    files -- `checkpoint.json` had been claiming 3,219 completed images since June 2026.

What the numbers are for: measured over the enhanced set, brightness / contrast / dynamic range /
entropy carry almost no spread (p95/p5 of 1.07-1.45) because the June enhancement normalises
exactly those quantities per image. The variance that survives is sharpness and local band
contrast (`lapvar` 2.48x, `band_std` 1.99x), which is what the filter must be built on.
`band_edge_density` is degenerate as computed -- Canny 60/160 is too high for a post-CLAHE
panoramic -- and is excluded from the feature set; re-tune or drop it.

Usage:
    python scripts/sdh/quality_scan.py <out.csv> [image_dir]
"""
import csv
import glob
import os
import sys
import time

import cv2
import numpy as np

DEFAULT_SRC = r"D:/SDH dataset/dataset/images"

COLS = ["image_id", "width", "height", "aspect",
        "mean", "std", "p01", "p99", "dynamic_range", "entropy",
        "sharp_grad", "lapvar", "band_mean", "band_std", "band_sharp_grad",
        "frac_black", "frac_white", "frac_bright_band", "band_edge_density"]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out = sys.argv[1]
    src = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SRC

    files = sorted(glob.glob(os.path.join(src, "*.png")))
    print(f"{len(files)} images", flush=True)
    unreadable = []

    t0 = time.time()
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for i, f in enumerate(files):
            img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
            if img is None:
                unreadable.append(os.path.basename(f))
                continue
            h, wid = img.shape
            a = img.astype(np.float32)
            # dental band: central 20-82% of image height -- the stage-2 gate's own definition
            band = a[int(0.20 * h):int(0.82 * h), :]
            gx = np.abs(np.diff(a, axis=1)).mean()
            gy = np.abs(np.diff(a, axis=0)).mean()
            bgx = np.abs(np.diff(band, axis=1)).mean()
            bgy = np.abs(np.diff(band, axis=0)).mean()
            p01, p99 = np.percentile(a, [1, 99])
            hist = np.bincount(img.ravel(), minlength=256).astype(np.float64)
            p = hist / hist.sum()
            nz = p[p > 0]
            ent = float(-(nz * np.log2(nz)).sum())
            lap = cv2.Laplacian(img, cv2.CV_64F).var()
            edges = cv2.Canny(band.astype(np.uint8), 60, 160)
            w.writerow([
                os.path.splitext(os.path.basename(f))[0], wid, h, round(wid / h, 4),
                round(float(a.mean()), 3), round(float(a.std()), 3),
                round(float(p01), 1), round(float(p99), 1), round(float(p99 - p01), 1),
                round(ent, 4),
                round(float((gx + gy) / 2), 4), round(float(lap), 3),
                round(float(band.mean()), 3), round(float(band.std()), 3),
                round(float((bgx + bgy) / 2), 4),
                round(float((img == 0).mean()), 6), round(float((img == 255).mean()), 6),
                round(float((band >= 240).mean()), 6),
                round(float((edges > 0).mean()), 6),
            ])
            if (i + 1) % 250 == 0:
                el = time.time() - t0
                print(f"  {i+1}/{len(files)}  {el:.0f}s  ({el/(i+1):.2f}s/img)", flush=True)

    print(f"done in {time.time()-t0:.0f}s -> {out}", flush=True)
    if unreadable:
        print(f"UNREADABLE ({len(unreadable)}): {', '.join(unreadable)}", flush=True)
        print("These are a dataset defect, not a scan failure -- see SDH_EXECUTION_PLAN.md "
              "S1.4 before treating the set size as correct.", flush=True)


if __name__ == "__main__":
    main()
