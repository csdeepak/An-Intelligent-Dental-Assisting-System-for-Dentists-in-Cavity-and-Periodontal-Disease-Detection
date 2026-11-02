#!/usr/bin/env python
"""Perceptual-hash near-duplicate check: the 164 scored DENTEX images against every other DENTEX image.

Review round 1, item 6 (paper/ieee/review/2026-11-02_panel_round1.md); RESULTS_LOG 2026-11-02d.
The scored cohort already excludes 86 images that are byte-identical (MD5) to training images
(data/dentex/disease_leaked_images.json). MD5 misses a radiograph that was re-encoded, resized or
cropped. This script hashes every image with two perceptual hashes and reports, for each scored
image, its nearest neighbour in the reference pool.

Reference pool: all DENTEX images outside disease/ (training_data/quadrant_enumeration,
training_data/quadrant-enumeration-disease, validation_data/quadrant_enumeration_disease), a
superset of every DENTEX source any model here trained on.

Hashes, implemented here so the method is visible (the imagehash package is not installed):
  pHash - 32x32 grayscale, 2-D DCT-II, top-left 8x8 block thresholded at its median (64 bits),
          as imagehash.phash;
  dHash - 9x8 grayscale, sign of the horizontal gradient (64 bits), as imagehash.dhash.
Positive control: every MD5-identical pair must come out at distance 0 under both hashes.

    python scripts/eval/dentex_near_duplicates.py
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.fft import dct

REPO = Path(__file__).resolve().parents[2]
DENTEX = Path.home() / "Downloads/Capstone/DENTEX"
POOLS = {"quadrant_enumeration": DENTEX / "training_data/quadrant_enumeration/xrays",
         "quadrant_enumeration_disease": DENTEX / "training_data/quadrant-enumeration-disease/xrays",
         "validation": DENTEX / "validation_data/quadrant_enumeration_disease/xrays"}
QUERY = DENTEX / "disease/input"
LEAK = REPO / "data/dentex/disease_leaked_images.json"
OUT = REPO / "outputs/review_round1/dentex_near_duplicates.json"


def hashes(path):
    raw = path.read_bytes()
    im = Image.open(path).convert("L")
    p = np.asarray(im.resize((32, 32), Image.LANCZOS), dtype=np.float64)
    low = dct(dct(p, axis=0, norm=None), axis=1, norm=None)[:8, :8]
    ph = (low > np.median(low)).ravel()
    d = np.asarray(im.resize((9, 8), Image.LANCZOS), dtype=np.int64)
    dh = (d[:, 1:] > d[:, :-1]).ravel()
    return hashlib.md5(raw).hexdigest(), ph, dh, im.size


def main():
    leaked = set(json.loads(LEAK.read_text())["all_excluded"])
    q_paths = sorted(QUERY.glob("*.png"))
    r_paths = [(name, p) for name, d in POOLS.items() for p in sorted(d.glob("*.png"))]
    assert len(q_paths) == 250 and len(r_paths) == 1389, (len(q_paths), len(r_paths))

    q = [hashes(p) for p in q_paths]
    r = [hashes(p) for _, p in r_paths]
    q_ph, q_dh = np.array([h[1] for h in q]), np.array([h[2] for h in q])
    r_ph, r_dh = np.array([h[1] for h in r]), np.array([h[2] for h in r])
    d_ph = (q_ph[:, None, :] != r_ph[None, :, :]).sum(2)     # 250 x 1389 Hamming distances
    d_dh = (q_dh[:, None, :] != r_dh[None, :, :]).sum(2)

    # Positive control: MD5-identical pairs, recomputed live.
    r_md5 = {}
    for (name, p), h in zip(r_paths, r):
        r_md5.setdefault(h[0], []).append(f"{name}/{p.name}")
    md5_pairs = [(qp.stem, r_md5[h[0]]) for qp, h in zip(q_paths, q) if h[0] in r_md5]
    md5_stems = {s for s, _ in md5_pairs}
    for i, (qp, h) in enumerate(zip(q_paths, q)):
        if qp.stem in md5_stems:
            assert d_ph[i].min() == 0 and d_dh[i].min() == 0, qp.stem

    scored = [i for i, p in enumerate(q_paths) if p.stem not in leaked and f"{p.stem}.png" not in leaked]
    assert len(scored) == 164
    excluded = [i for i in range(len(q_paths)) if i not in set(scored)]

    def nn(i):
        jp, jd = int(d_ph[i].argmin()), int(d_dh[i].argmin())
        return {"image": q_paths[i].stem, "size": list(q[i][3]),
                "phash_min": int(d_ph[i, jp]), "phash_nn": f"{r_paths[jp][0]}/{r_paths[jp][1].name}",
                "phash_nn_size": list(r[jp][3]),
                "dhash_min": int(d_dh[i, jd]), "dhash_nn": f"{r_paths[jd][0]}/{r_paths[jd][1].name}",
                "dhash_at_phash_nn": int(d_dh[i, jp])}

    rows = sorted((nn(i) for i in scored), key=lambda x: (x["phash_min"], x["dhash_at_phash_nn"]))
    ph_min = np.array([x["phash_min"] for x in rows])
    dh_min = np.array([x["dhash_min"] for x in rows])
    # Reference distribution: every scored-image-to-pool pair, i.e. unrelated radiographs almost surely.
    all_ph = d_ph[scored].ravel()
    out = {
        "method": "pHash (32x32 DCT, 8x8 median) and dHash (9x8 gradient), 64 bits each, Hamming distance; "
                  "query = 250 DENTEX disease/ images (164 scored); reference = 1,389 DENTEX images outside "
                  "disease/. Post hoc.",
        "n_query": len(q_paths), "n_scored": len(scored), "n_reference": len(r_paths),
        "n_reference_by_pool": {k: sum(n == k for n, _ in r_paths) for k in POOLS},
        "n_candidates_inspected": sum(1 for x in rows if x["phash_min"] <= 6 or x["dhash_min"] <= 4),
        "positive_control": {"md5_identical_query_images": len(md5_stems),
                             "md5_identical_listed_as_excluded": len(md5_stems & leaked),
                             "md5_identical_not_in_exclusion_list": sorted(md5_stems - leaked),
                             "all_at_distance_0_both_hashes": True,
                             "excluded_images_nn_phash_max": int(d_ph[excluded].min(1).max())},
        "scored_nearest_neighbour_counts": {f"phash_le_{t}": int((ph_min <= t).sum()) for t in (0, 4, 8, 12, 16)}
                                          | {f"dhash_le_{t}": int((dh_min <= t).sum()) for t in (0, 4, 8, 12, 16)},
        "scored_nn_phash_quantiles": {p: float(np.percentile(ph_min, p)) for p in (0, 5, 25, 50)},
        "all_pairs_phash_quantiles": {p: float(np.percentile(all_ph, p)) for p in (0.01, 0.1, 1, 5, 50)},
        "closest_scored": rows[:25],
        "closest_scored_by_dhash": sorted(rows, key=lambda x: (x["dhash_min"], x["phash_min"]))[:25],
        # Candidates for visual inspection: close under either hash.
        "candidates_for_inspection": [x for x in rows if x["phash_min"] <= 6 or x["dhash_min"] <= 4],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("positive_control", "scored_nearest_neighbour_counts",
                                          "scored_nn_phash_quantiles", "all_pairs_phash_quantiles")}, indent=1))
    for x in rows[:12]:
        print(x)


if __name__ == "__main__":
    main()
