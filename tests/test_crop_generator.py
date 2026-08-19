"""Tests for crop generation functions."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.crop_generator import (
    compute_expanded_bbox,
    extract_crop,
    rasterize_polygon,
    extend_mask_below_root,
    apply_soft_mask_attenuation,
    extract_mask_aware_crop,
)


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


def test_rasterize_polygon_basic():
    """A square polygon should fill exactly its interior, nothing outside it."""
    shape = (50, 50)
    square = [(10, 10), (30, 10), (30, 30), (10, 30)]
    mask = rasterize_polygon(square, shape)

    assert mask[20, 20] == 1, "Center of the square should be filled"
    assert mask[5, 5] == 0, "Outside the square should be empty"
    assert mask.shape == shape


def test_rasterize_polygon_too_few_points():
    """Fewer than 3 points cannot form a polygon; should return an empty mask."""
    mask = rasterize_polygon([(5, 5), (10, 10)], (20, 20))

    assert mask.sum() == 0, "Degenerate polygon should produce an all-zero mask"


def test_extend_mask_below_root_fills_column_span_downward():
    """Extension should fill from the mask's lowest row to the array bottom,
    only within the columns the mask actually occupies."""
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:10, 8:12] = 1  # a small "tooth" block, columns 8-11, rows 5-9

    extended = extend_mask_below_root(mask)

    assert extended[15, 9] == 1, "Region below the root, same columns, should now be filled"
    assert extended[15, 0] == 0, "Region below but outside the tooth's columns should stay empty"
    assert np.array_equal(extended[:10], mask[:10]), "Original tooth region should be unchanged"


def test_extend_mask_below_root_empty_mask_noop():
    """An all-zero mask has no column span to extend; should stay all zero."""
    mask = np.zeros((10, 10), dtype=np.uint8)
    extended = extend_mask_below_root(mask)

    assert extended.sum() == 0


def test_apply_soft_mask_attenuation_preserves_masked_region():
    """Pixels inside the mask should be unchanged; pixels outside should be dimmed
    by exactly `attenuation`, not zeroed (soft, not hard, masking)."""
    crop = np.full((10, 10), 200, dtype=np.uint8)
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[:, :5] = 1  # left half is "kept"

    result = apply_soft_mask_attenuation(crop, mask, attenuation=0.5)

    assert result[5, 2] == 200, "Inside the mask, pixel value should be unchanged"
    assert result[5, 8] == 100, f"Outside the mask, pixel should be dimmed to 50%, got {result[5, 8]}"
    assert (result > 0).all(), "Soft attenuation must not zero out any pixel"


def test_apply_soft_mask_attenuation_shape_mismatch_raises():
    """Mask and crop must cover the same spatial region."""
    crop = np.zeros((10, 10), dtype=np.uint8)
    mask = np.zeros((5, 5), dtype=np.uint8)

    try:
        apply_soft_mask_attenuation(crop, mask)
        assert False, "Expected a ValueError on shape mismatch"
    except ValueError:
        pass


def test_extract_mask_aware_crop_matches_plain_crop_without_polygon():
    """With no usable polygon (< 3 points), output should match extract_crop exactly —
    the fallback path for detections that don't have a mask yet."""
    img = np.random.randint(0, 255, (840, 1615), dtype=np.uint8)
    plain = extract_crop(img, 100, 50, 200, 300)
    mask_aware = extract_mask_aware_crop(img, [], 100, 50, 200, 300)

    assert np.array_equal(plain, mask_aware)


def test_extract_mask_aware_crop_shape():
    """Mask-aware crop should still resize to the requested target size."""
    img = np.random.randint(0, 255, (840, 1615), dtype=np.uint8)
    polygon = [(120, 70), (180, 70), (180, 280), (120, 280)]  # inside the (100,50)-(200,300) crop

    crop = extract_mask_aware_crop(img, polygon, 100, 50, 200, 300)

    assert crop is not None
    assert crop.shape == (224, 224)


if __name__ == "__main__":
    test_expanded_bbox_dimensions()
    test_expanded_bbox_clipping()
    test_extract_crop_resize()
    test_extract_crop_empty()
    test_rasterize_polygon_basic()
    test_rasterize_polygon_too_few_points()
    test_extend_mask_below_root_fills_column_span_downward()
    test_extend_mask_below_root_empty_mask_noop()
    test_apply_soft_mask_attenuation_preserves_masked_region()
    test_apply_soft_mask_attenuation_shape_mismatch_raises()
    test_extract_mask_aware_crop_matches_plain_crop_without_polygon()
    test_extract_mask_aware_crop_shape()
    print("All crop generator tests passed.")
