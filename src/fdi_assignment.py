"""
Stage 2 — positional FDI assignment from detector output.

This is the missing half of Stage 2. `src/utils/fdi_converter.py` holds the Universal->FDI
lookup *table*; this module answers the prior question the pipeline actually faces at
inference time: given N unlabelled tooth boxes from the detector, **which tooth is each one?**

CONVENTIONS — derived from ground truth, not assumed
----------------------------------------------------
Measured over the 1,600 FDI-keyed annotations in DENTEX `disease/label/` (22 Aug 2026):

  Q1 upper-right (patient)  mean normalised centroid  x=0.350  y=0.434   n=354
  Q2 upper-left  (patient)                            x=0.654  y=0.432   n=330
  Q3 lower-left  (patient)                            x=0.650  y=0.640   n=488
  Q4 lower-right (patient)                            x=0.362  y=0.638   n=428

So **patient-right appears on image-left** — the standard radiographic convention, confirmed
empirically rather than taken on faith. Getting this backwards mirrors every FDI code, which
is the same class of defect as the Universal->FDI lower-arch bug (`f8b31f8`).

Position digit rises monotonically with distance from the midline, again measured:
  pos 1 |x-0.5|=0.021 · 2 0.046 · 3 0.077 · 4 0.100 · 5 0.123 · 6 0.152 · 7 0.188 · 8 0.221

THE LIMITATION THIS MODULE CANNOT SOLVE, AND DOES NOT HIDE
----------------------------------------------------------
Positional assignment assumes the arch is **contiguous**. If tooth 16 is absent, every tooth
distal to it shifts one position inward and silently receives the wrong FDI code. No amount of
sorting fixes that; it needs anatomical modelling or a per-tooth classifier.

What this module does instead is **detect and flag** the condition rather than assign
confidently through it: consecutive spacing within each quadrant is compared against that
quadrant's own median, and an unusually large gap marks a suspected missing tooth. Every
assignment carries a `confidence` and a list of `flags`. Downstream filtering (Stage 5) is
expected to act on those rather than trust the code blindly.

`MASTER_PLAN_2026H2.md` §R4 names four failure modes; each is reported, none is silently
corrected:
  - missing teeth breaking positional assignment  -> `suspected_gap_before`, lowered confidence
  - duplicate FDI codes                           -> impossible by construction; >8 in a
                                                     quadrant yields `position_overflow`
  - teeth detected outside the arch               -> `off_arch`
  - edentulous regions                            -> `sparse_quadrant`
"""

from statistics import median

# quadrant digit by (jaw, image side). Patient-right == image-left, see module docstring.
_QUADRANT = {
    ("upper", "left"): 1,   # patient upper-right
    ("upper", "right"): 2,  # patient upper-left
    ("lower", "right"): 3,  # patient lower-left
    ("lower", "left"): 4,   # patient lower-right
}

MAX_POSITION = 8            # third molar; anything beyond is supernumerary or a false positive


def _split_two(values):
    """
    Deterministic 1-D 2-means, initialised at the extremes.

    Used for the jaw split. Chosen over a fixed y-threshold because OPG framing varies and a
    hard cut at 0.5 mis-assigns tilted or off-centre arches. Returns the boundary value.
    """
    if len(values) < 2:
        return None
    lo, hi = min(values), max(values)
    if lo == hi:
        return None
    c_lo, c_hi = lo, hi
    for _ in range(50):
        g_lo = [v for v in values if abs(v - c_lo) <= abs(v - c_hi)]
        g_hi = [v for v in values if abs(v - c_lo) > abs(v - c_hi)]
        if not g_lo or not g_hi:
            break
        n_lo, n_hi = sum(g_lo) / len(g_lo), sum(g_hi) / len(g_hi)
        if (n_lo, n_hi) == (c_lo, c_hi):
            break
        c_lo, c_hi = n_lo, n_hi
    return (c_lo + c_hi) / 2.0


def assign_fdi(boxes, img_w, img_h, midline_x=None, gap_factor=1.6, off_arch_sd=2.5):
    """
    Assign an FDI code to each detected tooth box.

    boxes       : sequence of (x1, y1, x2, y2) in pixels.
    img_w/img_h : image dimensions, used to normalise and to default the midline.
    midline_x   : override the midline in pixels. Defaults to the image centre — OPG machines
                  centre the patient, and the measured quadrant centroids above average to
                  x=0.504, so the centre is a sound prior. Supply this when a downstream
                  arch fit gives something better.
    gap_factor  : a spacing gap wider than gap_factor x the quadrant's median spacing marks a
                  suspected missing tooth.
    off_arch_sd : a detection further than this many SDs from its jaw's mean y is `off_arch`.

    Returns a list of dicts, one per input box, in the input order:
        {index, fdi, quadrant, position, jaw, side, centroid, confidence, flags}
    `fdi` is None when no valid code could be assigned (position overflow).
    """
    if not boxes:
        return []

    cents = [((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0) for b in boxes]
    mid_x = float(img_w) / 2.0 if midline_x is None else float(midline_x)

    ys = [c[1] for c in cents]
    jaw_boundary = _split_two(ys)
    if jaw_boundary is None:                       # single tooth, or all at one height
        jaw_boundary = float(img_h) / 2.0

    out = [None] * len(boxes)
    buckets = {}
    for i, (cx, cy) in enumerate(cents):
        jaw = "upper" if cy <= jaw_boundary else "lower"
        side = "left" if cx <= mid_x else "right"
        buckets.setdefault((jaw, side), []).append(i)

    # off-arch detection is judged per jaw, against that jaw's own vertical spread
    jaw_stats = {}
    for jaw in ("upper", "lower"):
        members = [cents[i][1] for k, idxs in buckets.items() if k[0] == jaw for i in idxs]
        if len(members) >= 3:
            m = sum(members) / len(members)
            sd = (sum((v - m) ** 2 for v in members) / len(members)) ** 0.5
            jaw_stats[jaw] = (m, sd)

    for (jaw, side), idxs in buckets.items():
        quadrant = _QUADRANT[(jaw, side)]
        # order by distance from the midline: nearest == central incisor == position 1
        idxs_sorted = sorted(idxs, key=lambda i: abs(cents[i][0] - mid_x))
        dists = [abs(cents[i][0] - mid_x) for i in idxs_sorted]
        gaps = [dists[k + 1] - dists[k] for k in range(len(dists) - 1)]
        med_gap = median(gaps) if gaps else 0.0

        for rank, i in enumerate(idxs_sorted):
            flags = []
            confidence = 1.0
            position = rank + 1

            if rank > 0 and med_gap > 0 and gaps[rank - 1] > gap_factor * med_gap:
                # a wider-than-typical step usually means a tooth is absent between these two,
                # so this and everything distal to it is probably numbered one too low
                flags.append("suspected_gap_before")
                confidence *= 0.5

            if position > MAX_POSITION:
                flags.append("position_overflow")
                confidence = 0.0

            if len(idxs) <= 2:
                flags.append("sparse_quadrant")
                confidence *= 0.7

            if jaw in jaw_stats:
                m, sd = jaw_stats[jaw]
                if sd > 0 and abs(cents[i][1] - m) > off_arch_sd * sd:
                    flags.append("off_arch")
                    confidence *= 0.4

            out[i] = {
                "index": i,
                "fdi": quadrant * 10 + position if position <= MAX_POSITION else None,
                "quadrant": quadrant,
                "position": position if position <= MAX_POSITION else None,
                "jaw": jaw,
                "side": side,
                "centroid": [round(cents[i][0], 1), round(cents[i][1], 1)],
                "confidence": round(confidence, 3),
                "flags": flags,
            }

    # a duplicate would mean the quadrant/position logic broke; assert rather than emit one
    seen = [r["fdi"] for r in out if r and r["fdi"] is not None]
    assert len(seen) == len(set(seen)), f"duplicate FDI codes produced: {sorted(seen)}"
    return out


def arch_summary(assignments):
    """Per-image diagnostics for Stage 5 filtering and for the domain-shift sanity checks."""
    per_q = {}
    for r in assignments:
        per_q.setdefault(r["quadrant"], 0)
        per_q[r["quadrant"]] += 1
    flagged = [r for r in assignments if r["flags"]]
    return {
        "n_teeth": len(assignments),
        "per_quadrant": {q: per_q.get(q, 0) for q in (1, 2, 3, 4)},
        "n_flagged": len(flagged),
        "flag_counts": {f: sum(1 for r in assignments for x in r["flags"] if x == f)
                        for f in sorted({x for r in assignments for x in r["flags"]})},
        "mean_confidence": round(sum(r["confidence"] for r in assignments) / len(assignments), 3)
        if assignments else 0.0,
    }
