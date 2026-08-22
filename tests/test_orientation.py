"""Tests for the detector input-orientation contract (src/orientation.py)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.orientation import CCW, CW, rot_point, unrot_box, unrot_point  # noqa: E402


def test_cw_forward_maps_corners_correctly():
    W, H = 2850, 1316
    assert rot_point(0, 0, W, H, CW) == (H - 1, 0)
    assert rot_point(W - 1, 0, W, H, CW) == (H - 1, W - 1)
    assert rot_point(0, H - 1, W, H, CW) == (0, 0)
    assert rot_point(W - 1, H - 1, W, H, CW) == (0, W - 1)


def test_ccw_forward_maps_corners_correctly():
    W, H = 2850, 1316
    assert rot_point(W - 1, 0, W, H, CCW) == (0, 0)
    assert rot_point(0, 0, W, H, CCW) == (0, W - 1)


def test_inverse_undoes_forward_both_directions():
    W, H = 2850, 1316
    for d in (CCW, CW):
        for x, y in [(0, 0), (10, 20), (2849, 1315), (500, 700)]:
            rx, ry = rot_point(x, y, W, H, d)
            assert unrot_point(rx, ry, W, H, d) == (x, y), f"{d} round-trip failed at {(x,y)}"


def test_matches_cv2_on_real_pixels_both_directions():
    import cv2
    rng = np.random.default_rng(0)
    img = rng.integers(0, 255, (120, 300, 3), dtype=np.uint8)
    h, w = img.shape[:2]
    for d, cvflag in ((CCW, cv2.ROTATE_90_COUNTERCLOCKWISE), (CW, cv2.ROTATE_90_CLOCKWISE)):
        rot = cv2.rotate(img, cvflag)
        assert rot.shape[:2] == (w, h)
        for _ in range(400):
            x = int(rng.integers(0, w)); y = int(rng.integers(0, h))
            rx, ry = rot_point(x, y, w, h, d)
            assert np.array_equal(img[y, x], rot[ry, rx]), f"{d} mismatch at {(x,y)}"


def test_unrot_box_returns_ordered_corners():
    for d in (CCW, CW):
        b = unrot_box([100, 200, 150, 400], 2000, 1000, d)
        assert b[0] < b[2] and b[1] < b[3], f"{d}: corners not ordered: {b}"


def test_box_round_trip_preserves_area():
    W, H = 2850, 1316
    orig = [400.0, 300.0, 500.0, 460.0]
    for d in (CCW, CW):
        r1 = rot_point(orig[0], orig[1], W, H, d); r2 = rot_point(orig[2], orig[3], W, H, d)
        rot_b = [min(r1[0], r2[0]), min(r1[1], r2[1]), max(r1[0], r2[0]), max(r1[1], r2[1])]
        back = unrot_box(rot_b, W, H, d)
        ao = (orig[2] - orig[0]) * (orig[3] - orig[1])
        ab = (back[2] - back[0]) * (back[3] - back[1])
        assert abs(ao - ab) < 1e-6, f"{d}: area changed {ao} -> {ab}"


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"  ok  {n}")
    print("all passed")
