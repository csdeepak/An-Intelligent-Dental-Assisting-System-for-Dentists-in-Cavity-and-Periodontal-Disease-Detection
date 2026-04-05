"""Tests for Universal → FDI tooth numbering conversion."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.fdi_converter import universal_to_fdi, fdi_to_universal, is_deciduous


def test_universal_to_fdi_upper_right():
    """Upper right quadrant: Universal 1-8 → FDI 18-11."""
    assert universal_to_fdi("1") == 18
    assert universal_to_fdi("8") == 11


def test_universal_to_fdi_upper_left():
    """Upper left quadrant: Universal 9-16 → FDI 21-28."""
    assert universal_to_fdi("9") == 21
    assert universal_to_fdi("16") == 28


def test_universal_to_fdi_lower():
    """Lower quadrants."""
    assert universal_to_fdi("17") == 38
    assert universal_to_fdi("32") == 34


def test_all_universal_have_fdi():
    """Every Universal tooth (1-32) should have an FDI mapping."""
    for u in range(1, 33):
        fdi = universal_to_fdi(str(u))
        assert fdi is not None, f"Universal {u} has no FDI mapping"
        assert isinstance(fdi, int), f"FDI for Universal {u} should be int"


def test_invalid_tooth():
    """Invalid tooth ID returns None."""
    assert universal_to_fdi("99") is None
    assert universal_to_fdi("X") is None


def test_deciduous():
    """Deciduous teeth A-T should be detected."""
    assert is_deciduous("A") is True
    assert is_deciduous("T") is True
    assert is_deciduous("1") is False
    assert is_deciduous("15") is False


if __name__ == "__main__":
    test_universal_to_fdi_upper_right()
    test_universal_to_fdi_upper_left()
    test_universal_to_fdi_lower()
    test_all_universal_have_fdi()
    test_invalid_tooth()
    test_deciduous()
    print("All FDI converter tests passed.")
