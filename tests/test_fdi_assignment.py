"""
Tests for Stage 2 positional FDI assignment.

The conventions asserted here were derived empirically from the 1,600 FDI-keyed annotations
in DENTEX `disease/label/` (RESULTS_LOG 2026-08-22), not assumed. In particular
**patient-right appears on image-left**; getting that backwards mirrors every code, which is
the same class of defect as the Universal->FDI lower-arch bug (`f8b31f8`).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fdi_assignment import arch_summary, assign_fdi


def _arch(n_per_quadrant=8, w=2000, h=1000):
    """A synthetic, perfectly symmetric full dentition: 32 teeth, 8 per quadrant."""
    boxes = []
    for jaw_y in (300, 700):                       # upper band, lower band
        for side in (-1, 1):                       # image-left, image-right
            for k in range(n_per_quadrant):
                cx = w / 2 + side * (60 + k * 90)
                boxes.append((cx - 30, jaw_y - 40, cx + 30, jaw_y + 40))
    return boxes, w, h


def test_full_dentition_produces_all_32_codes():
    boxes, w, h = _arch()
    out = assign_fdi(boxes, w, h)
    codes = sorted(r["fdi"] for r in out)
    expected = sorted(q * 10 + p for q in (1, 2, 3, 4) for p in range(1, 9))
    assert codes == expected, f"expected all 32 FDI codes, got {codes}"


def test_laterality_patient_right_is_image_left():
    """Q1/Q4 (patient right) must land on image-left. The empirical check, as a test."""
    boxes, w, h = _arch()
    out = assign_fdi(boxes, w, h)
    for r in out:
        cx = r["centroid"][0]
        if r["quadrant"] in (1, 4):
            assert cx < w / 2, f"Q{r['quadrant']} should be image-left, got x={cx}"
        else:
            assert cx > w / 2, f"Q{r['quadrant']} should be image-right, got x={cx}"


def test_upper_quadrants_are_above_lower():
    boxes, w, h = _arch()
    out = assign_fdi(boxes, w, h)
    upper = [r["centroid"][1] for r in out if r["quadrant"] in (1, 2)]
    lower = [r["centroid"][1] for r in out if r["quadrant"] in (3, 4)]
    assert max(upper) < min(lower), "jaw split failed to separate the arches"


def test_position_1_is_nearest_the_midline():
    boxes, w, h = _arch()
    out = assign_fdi(boxes, w, h)
    for q in (1, 2, 3, 4):
        quad = sorted((r for r in out if r["quadrant"] == q), key=lambda r: r["position"])
        dists = [abs(r["centroid"][0] - w / 2) for r in quad]
        assert dists == sorted(dists), f"Q{q} positions not ordered by midline distance"


def test_no_duplicate_codes_ever():
    boxes, w, h = _arch()
    out = assign_fdi(boxes, w, h)
    codes = [r["fdi"] for r in out if r["fdi"] is not None]
    assert len(codes) == len(set(codes))


def test_missing_tooth_is_flagged_not_silently_renumbered():
    """
    The failure mode positional assignment cannot solve. Remove one tooth mid-arch; the
    module must FLAG the gap rather than quietly hand out shifted codes.
    """
    boxes, w, h = _arch()
    # drop position 4 of the upper-left-of-image quadrant (Q1): index 3 in the first block
    del boxes[3]
    out = assign_fdi(boxes, w, h)
    q1 = [r for r in out if r["quadrant"] == 1]
    assert any("suspected_gap_before" in r["flags"] for r in q1), \
        "a missing tooth must raise suspected_gap_before"
    assert any(r["confidence"] < 1.0 for r in q1), "flagged assignments must lose confidence"


def test_position_overflow_when_more_than_eight_in_a_quadrant():
    boxes, w, h = _arch(n_per_quadrant=9)
    out = assign_fdi(boxes, w, h)
    over = [r for r in out if "position_overflow" in r["flags"]]
    assert len(over) == 4, f"expected one overflow per quadrant, got {len(over)}"
    assert all(r["fdi"] is None and r["confidence"] == 0.0 for r in over)


def test_sparse_quadrant_flagged():
    boxes, w, h = _arch(n_per_quadrant=2)
    out = assign_fdi(boxes, w, h)
    assert all("sparse_quadrant" in r["flags"] for r in out)


def test_empty_input_is_safe():
    assert assign_fdi([], 100, 100) == []


def test_single_tooth_does_not_crash():
    out = assign_fdi([(10, 10, 40, 60)], 200, 200)
    assert len(out) == 1 and out[0]["fdi"] is not None


def test_arch_summary_reports_per_quadrant_counts():
    boxes, w, h = _arch()
    s = arch_summary(assign_fdi(boxes, w, h))
    assert s["n_teeth"] == 32
    assert s["per_quadrant"] == {1: 8, 2: 8, 3: 8, 4: 8}
    assert s["mean_confidence"] == 1.0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("all passed")
