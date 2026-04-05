"""Tests for crop generation functions."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.crop_generator import compute_expanded_bbox, extract_crop


def test_expanded_bbox_dimensions():
    """Expanded bbox should be 1.5× wider and 2.0× taller."""
    x, y, w, h = 400, 300, 60, 150  # Well within bounds
    img_w, img_h = 1615, 840

    cx1, cy1, cx2, cy2 = compute_expanded_bbox(x, y, w, h, img_w, img_h)
    new_w = cx2 - cx1
    new_h = cy2 - cy1

    assert new_w >= w, "Expanded width should be >= original"
    assert new_h >= h, "Expanded height should be >= original"
    assert abs(new_w - w * 1.5) < 2, f"Width should be ~1.5x, got {new_w}"
    assert abs(new_h - h * 2.0) < 2, f"Height should be ~2.0x, got {new_h}"


def test_expanded_bbox_clipping():
    """Expanded bbox should clip to image bounds."""
    x, y, w, h = 0, 0, 60, 150
    img_w, img_h = 100, 200

    cx1, cy1, cx2, cy2 = compute_expanded_bbox(x, y, w, h, img_w, img_h)

    assert cx1 >= 0, "cx1 should not be negative"
    assert cy1 >= 0, "cy1 should not be negative"
    assert cx2 <= img_w, "cx2 should not exceed image width"
    assert cy2 <= img_h, "cy2 should not exceed image height"


def test_extract_crop_resize():
    """Extracted crop should be 224×224."""
    img = np.random.randint(0, 255, (840, 1615), dtype=np.uint8)
    crop = extract_crop(img, 100, 50, 200, 300)

    assert crop is not None
    assert crop.shape == (224, 224)


def test_extract_crop_empty():
    """Empty crop region should return None."""
    img = np.random.randint(0, 255, (840, 1615), dtype=np.uint8)
    crop = extract_crop(img, 100, 100, 100, 100)  # zero-size

    assert crop is None


if __name__ == "__main__":
    test_expanded_bbox_dimensions()
    test_expanded_bbox_clipping()
    test_extract_crop_resize()
    test_extract_crop_empty()
    print("All crop generator tests passed.")
