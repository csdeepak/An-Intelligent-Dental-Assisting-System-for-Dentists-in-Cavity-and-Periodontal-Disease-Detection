"""Tests for pixel-overlap label assignment."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.label_assigner import compute_overlap_ratio, assign_label


def test_empty_mask_zero_overlap():
    """Empty mask should produce zero overlap."""
    mask = np.zeros((840, 1615), dtype=np.uint8)
    overlap = compute_overlap_ratio(mask, 100, 50, 200, 300)
    assert overlap == 0.0


def test_full_mask_high_overlap():
    """Fully filled mask region should produce high overlap."""
    mask = np.zeros((840, 1615), dtype=np.uint8)
    mask[50:300, 100:200] = 255  # Fill the crop region
    overlap = compute_overlap_ratio(mask, 100, 50, 200, 300)
    assert overlap > 0.9, f"Expected >0.9, got {overlap}"


def test_sparse_mask_low_overlap():
    """Small blob in large region should produce low but nonzero overlap."""
    mask = np.zeros((840, 1615), dtype=np.uint8)
    # Small 5x5 blob inside a 100x250 crop region
    mask[150:155, 145:150] = 42
    overlap = compute_overlap_ratio(mask, 100, 50, 200, 300)
    assert 0 < overlap < 0.01, f"Expected small overlap, got {overlap}"


def test_label_above_threshold():
    """Overlap above threshold → label 1 (diseased)."""
    assert assign_label(0.02, threshold=0.01) == 1
    assert assign_label(0.05, threshold=0.01) == 1


def test_label_below_threshold():
    """Overlap below threshold → label 0 (normal)."""
    assert assign_label(0.005, threshold=0.01) == 0
    assert assign_label(0.0, threshold=0.01) == 0


def test_label_at_threshold():
    """Overlap exactly at threshold → label 0 (strictly greater than)."""
    assert assign_label(0.01, threshold=0.01) == 0


def test_zero_size_crop():
    """Zero-size crop should return 0 overlap."""
    mask = np.ones((840, 1615), dtype=np.uint8) * 255
    overlap = compute_overlap_ratio(mask, 100, 100, 100, 100)
    assert overlap == 0.0


if __name__ == "__main__":
    test_empty_mask_zero_overlap()
    test_full_mask_high_overlap()
    test_sparse_mask_low_overlap()
    test_label_above_threshold()
    test_label_below_threshold()
    test_label_at_threshold()
    test_zero_size_crop()
    print("All label assigner tests passed.")
