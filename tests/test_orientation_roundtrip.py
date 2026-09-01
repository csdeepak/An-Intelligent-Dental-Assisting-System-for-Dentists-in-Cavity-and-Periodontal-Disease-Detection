"""rot_box and unrot_box must be exact inverses.

Rotating annotations into the detector's frame is how a 90-epoch A100 run was once voided
(RESULTS_LOG 2026-08-27a): the losses fell smoothly for 90 epochs on misaligned data and nothing
failed along the way. A property test is the cheapest guard against repeating that.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.orientation import CCW, CW, rot_box, rot_point, unrot_box, unrot_point  # noqa: E402

# (orig_w, orig_h) covering both corpora: DENTEX upright landscape, Tufts portrait, and a square.
FRAMES = [(2872, 1504), (840, 1615), (512, 512), (2648, 1280)]
BOXES = [
    [0, 0, 10, 10],                 # touching the origin
    [100, 200, 340, 560],           # ordinary tooth box
    [1, 1, 2, 3],                   # degenerate-ish, still valid
]


@pytest.mark.parametrize("direction", [CCW, CW])
@pytest.mark.parametrize("w,h", FRAMES)
@pytest.mark.parametrize("box", BOXES)
def test_rot_unrot_roundtrip(box, w, h, direction):
    """unrot_box(rot_box(b)) == b, exactly, for every frame and both directions."""
    rotated = rot_box(box, w, h, direction)
    back = unrot_box(rotated, w, h, direction)
    assert back == box, f"round trip failed: {box} -> {rotated} -> {back}"


@pytest.mark.parametrize("direction", [CCW, CW])
@pytest.mark.parametrize("w,h", FRAMES)
def test_point_roundtrip(w, h, direction):
    for x, y in [(0, 0), (w - 1, h - 1), (w // 3, h // 4)]:
        rx, ry = rot_point(x, y, w, h, direction)
        bx, by = unrot_point(rx, ry, w, h, direction)
        assert (bx, by) == (x, y)


@pytest.mark.parametrize("w,h", FRAMES)
def test_rotated_box_stays_inside_the_rotated_frame(w, h):
    """A 90 deg rotation swaps the axes: the rotated frame is (h, w), not (w, h)."""
    box = [0, 0, w - 1, h - 1]
    x1, y1, x2, y2 = rot_box(box, w, h, CCW)
    assert 0 <= x1 <= x2 <= h - 1, f"x out of rotated width {h}: {(x1, x2)}"
    assert 0 <= y1 <= y2 <= w - 1, f"y out of rotated height {w}: {(y1, y2)}"


def test_corner_order_is_normalised():
    """The rotation sends top-left elsewhere; the result must still satisfy x1<x2, y1<y2."""
    x1, y1, x2, y2 = rot_box([10, 20, 300, 400], 2872, 1504, CCW)
    assert x1 < x2 and y1 < y2
