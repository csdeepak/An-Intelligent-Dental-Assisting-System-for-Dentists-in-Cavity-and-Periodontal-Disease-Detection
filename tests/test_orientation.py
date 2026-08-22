"""Tests for the detector input-orientation contract (src/orientation.py)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.orientation import rot_point, unrot_box, unrot_point  # noqa: E402


def test_forward_maps_corners_correctly():
    W, H = 2850, 1316
    assert rot_point(0, 0, H) == (H - 1, 0)
    assert rot_point(W - 1, 0, H) == (H - 1, W - 1)
    assert rot_point(0, H - 1, H) == (0, 0)
    assert rot_point(W - 1, H - 1, H) == (0, W - 1)


def test_inverse_undoes_forward():
    H = 1316
    for x, y in [(0, 0), (10, 20), (2849, 1315), (500, 700)]:
        rx, ry = rot_point(x, y, H)
        assert unrot_point(rx, ry, H) == (x, y)


def test_matches_cv2_on_real_pixels():
    import cv2
    rng = np.random.default_rng(0)
    img = rng.integers(0, 255, (120, 300, 3), dtype=np.uint8)
    h = img.shape[0]
    rot = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    assert rot.shape[:2] == (img.shape[1], img.shape[0])
    for _ in range(500):
        x = int(rng.integers(0, img.shape[1])); y = int(rng.integers(0, h))
        rx, ry = rot_point(x, y, h)
        assert np.array_equal(img[y, x], rot[ry, rx])


def test_unrot_box_returns_ordered_corners():
    H = 1000
    b = unrot_box([100, 200, 150, 400], H)
    assert b[0] < b[2] and b[1] < b[3], f"corners not ordered: {b}"


def test_box_round_trip_preserves_area():
    H = 1316
    orig = [400.0, 300.0, 500.0, 460.0]
    r1 = rot_point(orig[0], orig[1], H); r2 = rot_point(orig[2], orig[3], H)
    rot_b = [min(r1[0], r2[0]), min(r1[1], r2[1]), max(r1[0], r2[0]), max(r1[1], r2[1])]
    back = unrot_box(rot_b, H)
    ao = (orig[2] - orig[0]) * (orig[3] - orig[1])
    ab = (back[2] - back[0]) * (back[3] - back[1])
    assert abs(ao - ab) < 1e-6, f"area changed: {ao} -> {ab}"


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"  ok  {n}")
    print("all passed")
