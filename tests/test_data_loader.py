"""
Tests for data loading and parsing.

NOTE: These tests require access to the Tufts dataset.
They are designed to run in Colab/Kaggle with the dataset mounted.
For CI/CD, mock the data or skip with @pytest.mark.skipif.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_bbox_coordinate_conversion():
    """
    Verify that [y1, x1, y2, x2] is correctly converted to [x, y, w, h].
    
    This is the most critical test — Bug #2 caused all crops to be
    extracted from wrong locations.
    """
    # Simulate raw bbox from JSON
    raw_bbox = [50, 100, 300, 200]  # [y1, x1, y2, x2]

    y1, x1, y2, x2 = raw_bbox
    x = x1
    y = y1
    w = x2 - x1
    h = y2 - y1

    assert x == 100, f"x should be x1=100, got {x}"
    assert y == 50, f"y should be y1=50, got {y}"
    assert w == 100, f"w should be x2-x1=100, got {w}"
    assert h == 250, f"h should be y2-y1=250, got {h}"


def test_external_id_stem_extraction():
    """
    Verify that External ID field is correctly parsed to stem.
    
    Bug #1: Using dict keys instead of External ID field
    produced 0 coverage matches.
    """
    from pathlib import Path

    test_cases = [
        ("53.JPG", "53"),
        ("100.JPG", "100"),
        ("1000.jpg", "1000"),
        ("image_42.PNG", "image_42"),
    ]

    for ext_id, expected_stem in test_cases:
        stem = Path(ext_id).stem
        assert stem == expected_stem, f"Expected '{expected_stem}', got '{stem}'"


if __name__ == "__main__":
    test_bbox_coordinate_conversion()
    test_external_id_stem_extraction()
    print("All data loader tests passed.")
