"""
Tests for Lever C — the structural FDI position-digit post-processor.

These encode the pre-registration's local gate
(`outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md` §7) as executable checks, so the
gate cannot be declared passed by inspection:

  §7.1  a verified NO-OP on clean cases — quadrants whose head argmaxes are already strictly
        monotonic come out with exactly the codes the Hungarian gave them (20 quadrants here)
  §7.2  every emitted code is anatomically valid, and no code is ever emitted twice
  §7.3  the synthetic missing-tooth case: detections at the arch positions of teeth {1,2,4,5}
        with the head unsure about the last two must emit {41,42,44,45}, not {41,42,43,44}

Everything is synthetic — no model, no images, numpy only — because the point is the algorithm,
not the head. The head's behaviour is measured by the evaluation harnesses, not asserted here.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fdi_structural_repair import TAU, structural_repair

ARMS = ("dp", "sort")
W, H = 2000.0, 1000.0
MID = W / 2.0


def _lq(q, p=0.97):
    """Log-probabilities over the four quadrants, peaked on `q` (1-based)."""
    v = np.full(4, (1.0 - p) / 3.0)
    v[q - 1] = p
    return np.log(v)


def _lp(digit, p=0.90):
    """Log-probabilities over the eight position digits, peaked on `digit` (1-based)."""
    v = np.full(8, (1.0 - p) / 7.0)
    v[digit - 1] = p
    return np.log(v)


def _lp_from(weights):
    w = np.asarray(weights, dtype=float)
    return np.log(w / w.sum())


def _boxes(distances, y=700.0, side=-1, half=25.0):
    """Boxes at the given |cx - midline| distances, on one side of the arch."""
    out = []
    for d in distances:
        cx = MID + side * d
        out.append((cx - half, y - 40, cx + half, y + 40))
    return out


def _hung(codes, conf=0.5):
    """A minimal stand-in for `assign_fdi_head`'s output, in box order."""
    return [{"index": i, "fdi": c, "quadrant": None if c is None else c // 10,
             "position": None if c is None else c % 10, "confidence": conf, "flags": []}
            for i, c in enumerate(codes)]


def _codes(out):
    return [r["fdi"] for r in out]


def _flags(out):
    return {f for r in out for f in r["flags"]}


# --------------------------------------------------------------- §7.1 no-op on clean cases
@pytest.mark.parametrize("arm", ARMS)
def test_noop_on_clean_monotone_quadrants(arm):
    """A confident, already-monotonic quadrant must come out untouched — 20 of them."""
    rng = np.random.default_rng(42)
    for trial in range(20):
        n = int(rng.integers(4, 9))
        digits = list(range(1, n + 1))
        q = int(rng.integers(1, 5))
        boxes = _boxes([60 + 90 * k for k in range(n)], side=-1 if q in (1, 4) else 1)
        lq = np.stack([_lq(q) for _ in digits])
        lp = np.stack([_lp(d) for d in digits])
        codes = [q * 10 + d for d in digits]
        out = structural_repair(_hung(codes), boxes, lq, lp, W, H, arm=arm)
        assert _codes(out) == codes, f"trial {trial}: repair moved a clean quadrant"
        assert "structural_repaired" not in _flags(out)


# --------------------------------------------------------------- §7.2 validity and uniqueness
@pytest.mark.parametrize("arm", ARMS)
def test_emitted_codes_are_valid_and_unique(arm):
    rng = np.random.default_rng(7)
    for _ in range(25):
        n = int(rng.integers(2, 9))
        q = int(rng.integers(1, 5))
        boxes = _boxes(sorted(rng.uniform(40, 900, n)), side=-1 if q in (1, 4) else 1)
        lq = np.stack([_lq(q, p=float(rng.uniform(0.5, 0.99))) for _ in range(n)])
        lp = np.stack([_lp_from(rng.uniform(0.05, 1.0, 8)) for _ in range(n)])
        out = structural_repair(_hung([q * 10 + min(i + 1, 8) for i in range(n)]),
                                boxes, lq, lp, W, H, arm=arm)
        codes = [c for c in _codes(out) if c is not None]
        assert len(codes) == len(set(codes))
        assert all(11 <= c <= 48 and 1 <= c % 10 <= 8 for c in codes)


@pytest.mark.parametrize("arm", ARMS)
def test_overfull_quadrant_falls_back_rather_than_emitting_position_nine(arm):
    """Nine teeth cannot carry nine strictly increasing digits in 1..8 — keep the Hungarian."""
    n = 9
    boxes = _boxes([60 + 90 * k for k in range(n)])
    lq = np.stack([_lq(4) for _ in range(n)])
    lp = np.stack([_lp(min(k + 1, 8)) for k in range(n)])
    hung = _hung([41, 42, 43, 44, 45, 46, 47, 48, 31])
    out = structural_repair(hung, boxes, lq, lp, W, H, arm=arm)
    assert _codes(out) == [41, 42, 43, 44, 45, 46, 47, 48, 31]
    assert "structural_infeasible" in _flags(out)


# --------------------------------------------------------------- §7.3 the missing-tooth case
@pytest.mark.parametrize("arm", ARMS)
def test_wide_gap_permits_the_skip_that_even_spacing_forbids(arm):
    """
    Four detections in Q4. The head is confident about the first two (positions 1, 2) and
    unsure about the last two, mildly preferring 4 and 5 — the signature of a missing tooth 43.

    With a wide arch gap before the third tooth the repair must emit {41,42,44,45}; with even
    spacing, the same probabilities must give {41,42,43,44}. That difference IS the frozen
    `gap_factor` rule, and it is the pre-registration's §7.3 gate.
    """
    lq = np.stack([_lq(4) for _ in range(4)])
    lp = np.stack([
        _lp(1, p=0.92),
        _lp(2, p=0.92),
        _lp_from([0.02, 0.05, 0.22, 0.28, 0.20, 0.11, 0.07, 0.05]),   # argmax 4, conf < TAU
        _lp_from([0.02, 0.03, 0.10, 0.22, 0.29, 0.18, 0.10, 0.06]),   # argmax 5, conf < TAU
    ])
    assert np.exp(lp[2].max()) < TAU and np.exp(lp[3].max()) < TAU, "teeth 3-4 must be anchorless"
    hung = _hung([41, 42, 43, 44])

    wide = structural_repair(hung, _boxes([60, 150, 420, 510]), lq, lp, W, H, arm=arm)
    even = structural_repair(hung, _boxes([60, 150, 240, 330]), lq, lp, W, H, arm=arm)
    if arm == "dp":
        assert _codes(wide) == [41, 42, 44, 45], "the wide gap should permit the skip"
        assert _codes(even) == [41, 42, 43, 44], "even spacing should force consecutive digits"
        assert "structural_repaired" in _flags(wide)
    else:
        # C-sort ignores the softmax past anchor selection, so it fills consecutively either
        # way. Recording that here is the point of running the cheap arm at all.
        assert _codes(wide) == [41, 42, 43, 44]
        assert _codes(even) == [41, 42, 43, 44]


@pytest.mark.parametrize("arm", ARMS)
def test_off_by_one_run_is_repaired(arm):
    """[1, 2, 2, 4] with the duplicate below TAU -> [1, 2, 3, 4]: the off_by_one bucket."""
    lq = np.stack([_lq(1) for _ in range(4)])
    lp = np.stack([
        _lp(1, p=0.88),
        _lp(2, p=0.88),
        _lp_from([0.05, 0.27, 0.26, 0.18, 0.10, 0.06, 0.05, 0.03]),   # argmax 2, conf < TAU
        _lp(4, p=0.85),
    ])
    boxes = _boxes([60, 150, 240, 330], side=-1)
    out = structural_repair(_hung([11, 12, 12, 14]), boxes, lq, lp, W, H, arm=arm)
    assert _codes(out) == [11, 12, 13, 14]
    assert "structural_repaired" in _flags(out)


# --------------------------------------------------------------- fallbacks and collisions
@pytest.mark.parametrize("arm", ARMS)
def test_quadrant_without_an_anchor_keeps_the_hungarian_labels(arm):
    lq = np.stack([_lq(2) for _ in range(3)])
    lp = np.stack([_lp_from([0.2, 0.18, 0.16, 0.14, 0.12, 0.09, 0.06, 0.05]) for _ in range(3)])
    assert np.exp(lp.max(axis=1)).max() < TAU
    out = structural_repair(_hung([21, 22, 23]), _boxes([60, 150, 240], side=1),
                            lq, lp, W, H, arm=arm)
    assert _codes(out) == [21, 22, 23]
    assert "structural_no_anchor" in _flags(out)
    assert "structural_repaired" not in _flags(out)


@pytest.mark.parametrize("arm", ARMS)
def test_cross_group_collision_drops_the_weaker_code(arm):
    """
    A retained (no-anchor) Hungarian code can collide with a repaired one, since the groups are
    labelled independently. The lower joint log-prob must lose its code, not both keep it.
    """
    lq = np.stack([_lq(1, p=0.40), _lq(2, p=0.95)])           # tooth 0 groups to Q1, tooth 1 Q2
    lp = np.stack([
        _lp_from([0.18, 0.20, 0.16, 0.14, 0.12, 0.08, 0.07, 0.05]),   # conf < TAU -> no anchor
        _lp(2, p=0.93),
    ])
    boxes = _boxes([80, 300], side=1)
    out = structural_repair(_hung([22, 23], conf=0.10), boxes, lq, lp, W, H, arm=arm)
    codes = [c for c in _codes(out) if c is not None]
    assert codes == [22], f"expected the stronger tooth to keep 22, got {_codes(out)}"
    assert out[0]["fdi"] is None and "structural_collision" in out[0]["flags"]
    assert out[1]["fdi"] == 22


def test_unknown_arm_is_rejected_by_the_inference_wrapper():
    from src.fdi_head_inference import ASSIGNMENTS, assign_from_scores
    assert ASSIGNMENTS[0] == "hungarian", "the deployed default must stay first"
    with pytest.raises(ValueError):
        assign_from_scores(np.zeros((1, 32)), np.zeros((1, 4)), np.zeros((1, 8)),
                           _boxes([60]), W, H, assignment="structural")
