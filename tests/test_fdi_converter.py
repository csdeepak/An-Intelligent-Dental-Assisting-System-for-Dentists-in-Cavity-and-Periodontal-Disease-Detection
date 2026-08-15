"""Tests for Universal → FDI tooth numbering conversion.

The expected values here are derived from the FDI two-digit standard, NOT read back
from `src/utils/fdi_converter.py`. That distinction matters: the previous version of
this file asserted `universal_to_fdi("32") == 34`, which is what the buggy table
returned rather than what the standard requires (48). A test written against the
implementation cannot detect a wrong implementation.

FDI: first digit is the quadrant (1 upper-right, 2 upper-left, 3 lower-left,
4 lower-right), second is distance from the midline (1 central incisor ... 8 third
molar). Universal runs clockwise from the upper-right third molar.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.fdi_converter import (
    UNIVERSAL_TO_FDI,
    universal_to_fdi,
    fdi_to_universal,
    is_deciduous,
)

# The full expected table, written out independently of the module under test.
EXPECTED = {
    # Quadrant 1 — upper right, third molar → central incisor
    "1": 18, "2": 17, "3": 16, "4": 15, "5": 14, "6": 13, "7": 12, "8": 11,
    # Quadrant 2 — upper left, central incisor → third molar
    "9": 21, "10": 22, "11": 23, "12": 24, "13": 25, "14": 26, "15": 27, "16": 28,
    # Quadrant 3 — lower left, third molar → central incisor
    "17": 38, "18": 37, "19": 36, "20": 35, "21": 34, "22": 33, "23": 32, "24": 31,
    # Quadrant 4 — lower right, central incisor → third molar
    "25": 41, "26": 42, "27": 43, "28": 44, "29": 45, "30": 46, "31": 47, "32": 48,
}


def test_full_mapping_matches_fdi_standard():
    """Every one of the 32 permanent teeth maps to its standard FDI code."""
    for universal, expected_fdi in EXPECTED.items():
        actual = universal_to_fdi(universal)
        assert actual == expected_fdi, (
            f"Universal {universal} → FDI {actual}, expected {expected_fdi}"
        )


def test_quadrant_boundaries():
    """The four quadrant transitions — where off-by-one table errors surface."""
    assert universal_to_fdi("1") == 18    # start upper right
    assert universal_to_fdi("8") == 11    # end upper right (midline)
    assert universal_to_fdi("9") == 21    # start upper left (midline)
    assert universal_to_fdi("16") == 28   # end upper left
    assert universal_to_fdi("17") == 38   # start lower left
    assert universal_to_fdi("24") == 31   # end lower left (midline)
    assert universal_to_fdi("25") == 41   # start lower right (midline)
    assert universal_to_fdi("32") == 48   # end lower right


def test_quadrant_digit_is_correct():
    """Universal ranges must land in the right FDI quadrant.

    The historical bug put Universal 23-28 into quadrant 4 and 29-32 into quadrant 3,
    i.e. it reported lower-left teeth as lower-right and vice versa. This property
    check catches that class of error regardless of the exact within-quadrant order.
    """
    for universal, fdi in EXPECTED.items():
        u = int(universal)
        actual = universal_to_fdi(universal)
        expected_quadrant = fdi // 10
        assert actual // 10 == expected_quadrant, (
            f"Universal {u} landed in quadrant {actual // 10}, "
            f"expected quadrant {expected_quadrant}"
        )


def test_mapping_is_bijective():
    """All 32 FDI codes must be distinct.

    The buggy table emitted FDI 33 and 34 twice each (from Universal 22/31 and
    21/32), which silently collapsed entries in the reverse lookup. A duplicate
    means two different teeth are reported under one code.
    """
    fdi_values = list(UNIVERSAL_TO_FDI.values())
    assert len(fdi_values) == 32, f"expected 32 entries, got {len(fdi_values)}"
    assert len(set(fdi_values)) == 32, (
        f"duplicate FDI codes in table: "
        f"{sorted(v for v in set(fdi_values) if fdi_values.count(v) > 1)}"
    )


def test_round_trip():
    """universal → fdi → universal returns the original tooth."""
    for universal in EXPECTED:
        fdi = universal_to_fdi(universal)
        assert fdi_to_universal(fdi) == universal, (
            f"round trip failed for Universal {universal} (via FDI {fdi})"
        )


def test_accepts_int_and_str():
    """Callers pass tooth IDs both ways; both must work."""
    assert universal_to_fdi(32) == universal_to_fdi("32") == 48
    assert fdi_to_universal(48) == fdi_to_universal("48") == "32"


def test_invalid_tooth():
    """Invalid tooth ID returns None rather than raising."""
    assert universal_to_fdi("99") is None
    assert universal_to_fdi("0") is None
    assert universal_to_fdi("X") is None
    assert universal_to_fdi("") is None


def test_deciduous():
    """Deciduous teeth A-T should be detected."""
    assert is_deciduous("A") is True
    assert is_deciduous("T") is True
    assert is_deciduous("1") is False
    assert is_deciduous("15") is False


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("\nAll FDI converter tests passed.")
