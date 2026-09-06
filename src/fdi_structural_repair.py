"""
Lever C — a structural post-processor for the Stage-2 FDI **position digit**.

Pre-registration: `outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md` (frozen
6 Sep 2026, commit `e9270a3`, before this file existed). Nothing here may be tuned against
Tufts test or DENTEX; the one threshold is inherited, see TAU below.

WHAT GAP THIS ATTACKS
---------------------
`assign_fdi_head`'s Hungarian pass maximises the total joint (quadrant x position)
log-probability over a **one-to-one** matching of detections to the 32 codes. It enforces
uniqueness — no two teeth get code 16 — but **not anatomical sequence consistency**: teeth
ordered along the arch inside a quadrant are not required to carry monotonically increasing
position digits, with a skip only where a tooth is genuinely absent. One miscounted tooth
therefore shifts a run of its neighbours by one, which is the `off_by_one` bucket: 74% of all
Tufts numbering errors (PAPER_MATERIAL.md 8.16), and the Option B diagnostic
(RESULTS_LOG 2026-09-06) localised the weakness to the position digit specifically
(Tufts 73.5% vs DENTEX 91.9% on GT crops) while quadrant (97.4%) and side (97.8%) are near-matched.

So: trust the head's quadrant, re-label only the position digit, under an arch-order
monotonicity constraint anchored on the teeth the head is already confident about.

THE METHOD (frozen; step numbers are the pre-registration's)
------------------------------------------------------------
1. Quadrant per tooth = the head's **argmax** (NOT the Hungarian's jointly-reassigned
   quadrant, which can move a tooth across the mouth to satisfy global uniqueness).
2. Inside each quadrant, sort teeth by `|cx - midline_x|` ascending — nearest the midline is
   position 1. The identical ordering `src/fdi_assignment.py` uses.
3. **Anchors** = the longest strictly-increasing subsequence of the position argmaxes, over
   only those teeth whose position-digit confidence (max softmax) >= TAU. Ties in "longest"
   are broken by the larger total confidence.
4. Non-anchor teeth are re-labelled by an exact dynamic program over the quadrant that
   maximises the head's own sum of log p subject to strictly increasing digits, with anchors
   pinned. A **skipped digit** (a missing tooth) is permitted only where the arch-spacing gap
   before that tooth exceeds GAP_FACTOR x the quadrant's median spacing.
5. A quadrant with no eligible anchor falls back to the Hungarian labels, flag
   `structural_no_anchor`.
6. Cross-quadrant duplicates (possible now that quadrants are labelled independently) are
   resolved in favour of the higher joint log-prob; the loser emits no code, flag
   `structural_collision`.

Every tooth whose FDI changed vs the Hungarian result carries `structural_repaired`.

TWO ARMS
--------
`arm="sort"` (C-sort)  steps 1-3, then non-anchor teeth simply take the unused digits between
                       their flanking anchors in arch order. ~15 lines, no softmax past the
                       anchor selection. The cheap baseline.
`arm="dp"`   (C-dp)    the full method, steps 1-6.

Both are reported whatever the verdict — the point of running C-sort is to show whether the
DP's complexity earns its keep instead of asserting that it does.

IMPLEMENTATION CHOICES LEFT OPEN BY THE PRE-REGISTRATION (settled here, before the first run
on Tufts test or DENTEX, and repeated in each arm's `run_summary.txt`)
--------------------------------------------------------------------------------------------
* DP recurrence: `dp[i][d]` = best total log p for teeth 0..i with tooth i labelled `d`, over
  `d' < d` allowed by the skip rule. O(N * 8^2) per quadrant, exact, no beam.
* Tie-breaking inside the DP: the lowest digit wins (`>` not `>=` when comparing scores), so
  the result is deterministic and independent of dict/array ordering.
* Spacing -> skip: `gap_before[i] > GAP_FACTOR * median(gaps)` permits any jump, not a jump of
  a specific size — the spacing tells us *that* a tooth is missing, not how many.
* Feasibility ladder: if the skip-constrained DP has no solution (anchors that demand a jump
  where the spacing does not permit one), retry with the skip rule relaxed to plain strict
  monotonicity; if that is also infeasible (more than 8 teeth in a quadrant), keep the
  Hungarian labels for that quadrant and flag `structural_infeasible`. Never emit an invalid code.
* Confidence of an emitted code is recomputed the way `assign_fdi_head` defines it —
  `exp(log p(quadrant) + log p(position))` — so downstream Stage-5 filtering is unaffected.
"""

import numpy as np

# Inherited a priori, never swept. TAU is the codebase's existing LOW_CONFIDENCE
# (src/fdi_head_inference.py); GAP_FACTOR is src/fdi_assignment.assign_fdi's default. Lever C
# introduces no new tunable of its own -- that is the point.
TAU = 0.30
GAP_FACTOR = 1.6
MAX_POSITION = 8
NEG_INF = -1e18


def _arch_order(indices, cents, mid_x):
    """Quadrant members sorted by distance from the midline (position 1 == nearest)."""
    return sorted(indices, key=lambda i: (abs(cents[i][0] - mid_x), i))


def _skip_allowed(order, cents, mid_x, gap_factor=GAP_FACTOR):
    """
    skip_allowed[k] answers: may tooth `order[k]` jump more than one digit past its neighbour?

    True where the step in arch distance before it is unusually wide for this quadrant, which
    is `src/fdi_assignment.py`'s existing missing-tooth signal (`suspected_gap_before`), reused
    verbatim rather than re-derived. Index 0 is always True: nothing precedes the first tooth,
    so its digit is unconstrained from below.
    """
    dists = [abs(cents[i][0] - mid_x) for i in order]
    gaps = [dists[k + 1] - dists[k] for k in range(len(dists) - 1)]
    med = float(np.median(gaps)) if gaps else 0.0
    out = [True]
    for k in range(1, len(order)):
        out.append(med > 0 and gaps[k - 1] > gap_factor * med)
    return out


def _anchors(order, argmax_pos, conf_pos, tau=TAU):
    """
    Longest strictly-increasing subsequence of position argmaxes among teeth with
    confidence >= tau, ties broken by total confidence. Returns {index_in_order: digit}.

    O(N^2); N is teeth-in-a-quadrant, at most ~10.
    """
    elig = [k for k in range(len(order)) if conf_pos[order[k]] >= tau]
    if not elig:
        return {}
    best_len = {k: 1 for k in elig}
    best_conf = {k: conf_pos[order[k]] for k in elig}
    prev = {k: None for k in elig}
    for a, k in enumerate(elig):
        for j in elig[:a]:
            if argmax_pos[order[j]] < argmax_pos[order[k]]:
                cand_len = best_len[j] + 1
                cand_conf = best_conf[j] + conf_pos[order[k]]
                if (cand_len, cand_conf) > (best_len[k], best_conf[k]):
                    best_len[k], best_conf[k], prev[k] = cand_len, cand_conf, j
    end = max(elig, key=lambda k: (best_len[k], best_conf[k], -k))
    chain, k = {}, end
    while k is not None:
        chain[k] = int(argmax_pos[order[k]])
        k = prev[k]
    return chain


def _dp_labels(order, logp, anchors, skip_allowed):
    """
    Exact max-sum-log-p strictly-increasing labelling with anchors pinned.

    Returns a list of digits (1-based) aligned with `order`, or None if infeasible.
    """
    n = len(order)
    if n > MAX_POSITION:
        return None
    score = np.full((n, MAX_POSITION + 1), NEG_INF)     # score[k][d], d in 1..8
    back = np.zeros((n, MAX_POSITION + 1), dtype=int)

    def allowed(k, d):
        return (k not in anchors) or anchors[k] == d

    for d in range(1, MAX_POSITION + 1):
        if allowed(0, d):
            score[0][d] = logp[order[0]][d - 1]
    for k in range(1, n):
        for d in range(1, MAX_POSITION + 1):
            if not allowed(k, d):
                continue
            lo = 1 if skip_allowed[k] else d - 1        # skip only where the spacing says so
            hi = d - 1
            best, arg = NEG_INF, 0
            for dp_ in range(max(1, lo), hi + 1):
                if score[k - 1][dp_] > best:
                    best, arg = score[k - 1][dp_], dp_
            if best > NEG_INF / 2:
                score[k][d] = best + logp[order[k]][d - 1]
                back[k][d] = arg
    last = int(np.argmax(score[n - 1]))
    if score[n - 1][last] <= NEG_INF / 2:
        return None
    digits = [0] * n
    d = last
    for k in range(n - 1, -1, -1):
        digits[k] = d
        d = int(back[k][d])
    return digits


def _sort_labels(order, anchors):
    """
    C-sort: non-anchor teeth take the unused digits adjacent to their flanking anchors, in
    arch order. No DP, no softmax past the anchor selection. None if it cannot fit.
    """
    n = len(order)
    if n > MAX_POSITION or not anchors:
        return None
    digits = [None] * n
    keys = sorted(anchors)
    for k in keys:
        digits[k] = anchors[k]
    first = keys[0]
    for offset, k in enumerate(range(first - 1, -1, -1)):        # walk toward the midline
        digits[k] = anchors[first] - 1 - offset
    last = keys[-1]
    for offset, k in enumerate(range(last + 1, n)):
        digits[k] = anchors[last] + 1 + offset
    for a, b in zip(keys, keys[1:]):
        for offset, k in enumerate(range(a + 1, b)):
            digits[k] = anchors[a] + 1 + offset
    if any(d is None or d < 1 or d > MAX_POSITION for d in digits):
        return None
    if any(digits[k] >= digits[k + 1] for k in range(n - 1)):
        return None
    return digits


def has_detected_gap(boxes, lq, img_w, img_h, midline_x=None, gap_factor=GAP_FACTOR):
    """
    Does any quadrant in this image show a wider-than-typical arch step?

    The same rule the repair uses to permit a skipped digit, exposed so an evaluation can
    stratify images by "the detector's boxes imply a missing tooth" vs "contiguous" -- the
    pre-registration's second stratified split. It is a property of the boxes and the head's
    quadrants, so it is identical across the arms and computable once per image.
    """
    n = len(boxes)
    if n == 0:
        return False
    lq = np.asarray(lq, dtype=float)
    cents = [((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0) for b in boxes]
    mid_x = float(img_w) / 2.0 if midline_x is None else float(midline_x)
    quad_of = (lq.argmax(axis=1) + 1).astype(int)
    for q in (1, 2, 3, 4):
        members = [i for i in range(n) if quad_of[i] == q]
        if len(members) < 3:
            continue
        order = _arch_order(members, cents, mid_x)
        if any(_skip_allowed(order, cents, mid_x, gap_factor)[1:]):
            return True
    return False


def structural_repair(hungarian, boxes, lq, lp, img_w, img_h,
                      arm="dp", midline_x=None, tau=TAU, gap_factor=GAP_FACTOR):
    """
    Re-label the position digit of an existing Hungarian assignment.

    hungarian : the list `assign_fdi_head` returns (one dict per box, in box order).
    boxes     : the same boxes, (x1, y1, x2, y2) in pixels.
    lq, lp    : (N,4) and (N,8) log-softmax arrays from the head, box order.
    arm       : "dp" (C-dp, the full method) or "sort" (C-sort, the cheap baseline).
    midline_x : pixels; defaults to the image centre, as `src/fdi_assignment.assign_fdi` does.

    Returns a new list in the same schema as `assign_fdi_head`. Input is not mutated.
    """
    n = len(hungarian)
    if n == 0:
        return []
    lq = np.asarray(lq, dtype=float)
    lp = np.asarray(lp, dtype=float)
    cents = [((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0) for b in boxes]
    mid_x = float(img_w) / 2.0 if midline_x is None else float(midline_x)

    quad_of = (lq.argmax(axis=1) + 1).astype(int)          # step 1: head argmax, not Hungarian
    argmax_pos = (lp.argmax(axis=1) + 1).astype(int)
    conf_pos = np.exp(lp.max(axis=1))

    out = [dict(h, flags=list(h["flags"])) for h in hungarian]
    quad_flag = {}

    for q in (1, 2, 3, 4):
        members = [i for i in range(n) if quad_of[i] == q]
        if not members:
            continue
        order = _arch_order(members, cents, mid_x)         # step 2
        anchors = _anchors(order, argmax_pos, conf_pos, tau)   # step 3
        if not anchors:                                    # step 5
            quad_flag[q] = "structural_no_anchor"
            continue
        if arm == "sort":
            digits = _sort_labels(order, anchors)
        else:
            skip = _skip_allowed(order, cents, mid_x, gap_factor)   # step 4
            digits = _dp_labels(order, lp, anchors, skip)
            if digits is None:                             # feasibility ladder, see docstring
                digits = _dp_labels(order, lp, anchors, [True] * len(order))
        if digits is None:
            quad_flag[q] = "structural_infeasible"
            continue
        for k, i in enumerate(order):
            d = int(digits[k])
            out[i]["fdi"] = q * 10 + d
            out[i]["quadrant"] = q
            out[i]["position"] = d
            out[i]["confidence"] = round(float(np.exp(lq[i][q - 1] + lp[i][d - 1])), 4)

    # step 6 -- a code may now appear twice, since quadrants were labelled independently.
    # Fallback quadrants take part too: their retained Hungarian code can collide with a
    # repaired one, and confidence is the same quantity on both sides of that comparison.
    seen = {}
    for i, r in enumerate(out):
        if r["fdi"] is None:
            continue
        prev = seen.get(r["fdi"])
        if prev is None:
            seen[r["fdi"]] = i
        else:
            loser = i if r["confidence"] <= out[prev]["confidence"] else prev
            keeper = prev if loser == i else i
            seen[r["fdi"]] = keeper
            out[loser].update(fdi=None, quadrant=None, position=None, confidence=0.0)
            out[loser]["flags"] = [f for f in out[loser]["flags"] if f != "low_confidence"]
            out[loser]["flags"].append("structural_collision")

    for i, r in enumerate(out):
        qf = quad_flag.get(int(quad_of[i]))
        if qf:                                             # quadrant kept its Hungarian labels
            if qf not in r["flags"]:
                r["flags"].append(qf)
            continue
        if "structural_collision" in r["flags"]:
            continue
        r["flags"] = [f for f in r["flags"]
                      if f not in ("low_confidence", "reassigned_by_one_to_one")]
        if r["fdi"] is not None and r["confidence"] < TAU:
            r["flags"].append("low_confidence")
        if r["fdi"] != hungarian[i]["fdi"]:
            r["flags"].append("structural_repaired")

    codes = [r["fdi"] for r in out if r["fdi"] is not None]
    assert len(codes) == len(set(codes)), f"structural repair emitted duplicates: {sorted(codes)}"
    assert all(11 <= c <= 48 and 1 <= c % 10 <= 8 for c in codes), f"invalid code: {sorted(codes)}"
    return out


def repair_diagnostics(boxes, lq, lp, img_w, img_h, midline_x=None, tau=TAU):
    """
    Why the repair did or did not have room to act, per image. Arm-independent.

    Returns {n_groups, n_overfull, n_no_anchor, n_teeth, n_anchor_teeth, n_movable_teeth},
    where "movable" = in a feasible, anchored group AND not itself an anchor. A method that
    cannot move a tooth cannot fix it, so this is the honest denominator for any effect size --
    reported rather than left for a reader to infer from a null.
    """
    n = len(boxes)
    if n == 0:
        return {"n_groups": 0, "n_overfull": 0, "n_no_anchor": 0, "n_teeth": 0,
                "n_anchor_teeth": 0, "n_movable_teeth": 0}
    lq = np.asarray(lq, dtype=float)
    lp = np.asarray(lp, dtype=float)
    cents = [((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0) for b in boxes]
    mid_x = float(img_w) / 2.0 if midline_x is None else float(midline_x)
    quad_of = (lq.argmax(axis=1) + 1).astype(int)
    argmax_pos = (lp.argmax(axis=1) + 1).astype(int)
    conf_pos = np.exp(lp.max(axis=1))
    d = {"n_groups": 0, "n_overfull": 0, "n_no_anchor": 0, "n_teeth": n,
         "n_anchor_teeth": 0, "n_movable_teeth": 0}
    for q in (1, 2, 3, 4):
        members = [i for i in range(n) if quad_of[i] == q]
        if not members:
            continue
        d["n_groups"] += 1
        order = _arch_order(members, cents, mid_x)
        anchors = _anchors(order, argmax_pos, conf_pos, tau)
        if len(members) > MAX_POSITION:
            d["n_overfull"] += 1
            continue
        if not anchors:
            d["n_no_anchor"] += 1
            continue
        d["n_anchor_teeth"] += len(anchors)
        d["n_movable_teeth"] += len(members) - len(anchors)
    return d
