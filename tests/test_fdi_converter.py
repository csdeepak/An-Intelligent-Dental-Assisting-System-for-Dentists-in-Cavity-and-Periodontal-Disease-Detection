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
    mirror_fdi_quadrant,
    tufts_title_to_fdi,
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


# ---------------------------------------------------------------------------
# Tufts mirrored numbering
# ---------------------------------------------------------------------------
#
# Written out independently, same rule as EXPECTED above: these are what the FDI standard
# requires GIVEN the measured fact that a Tufts "title" denotes the CONTRALATERAL tooth of
# the same-numbered Universal code (RESULTS_LOG 2026-08-25h — L-marker, a DENTEX-trained
# arbiter at 91.7% mirrored vs 6.1% direct, and a DENTEX control at 98.6% direct).
#
# So Tufts n names Universal (17-n) in the upper arch and Universal (49-n) in the lower.
EXPECTED_TUFTS = {
    # upper — Tufts 1 is the upper LEFT third molar (28), not the upper right (18)
    "1": 28, "2": 27, "3": 26, "4": 25, "5": 24, "6": 23, "7": 22, "8": 21,
    "9": 11, "10": 12, "11": 13, "12": 14, "13": 15, "14": 16, "15": 17, "16": 18,
    # lower
    "17": 48, "18": 47, "19": 46, "20": 45, "21": 44, "22": 43, "23": 42, "24": 41,
    "25": 31, "26": 32, "27": 33, "28": 34, "29": 35, "30": 36, "31": 37, "32": 38,
}


def test_tufts_titles_map_to_mirrored_fdi():
    """All 32 Tufts titles map to the contralateral FDI code."""
    for title, expected in EXPECTED_TUFTS.items():
        actual = tufts_title_to_fdi(title)
        assert actual == expected, f"Tufts '{title}': expected FDI {expected}, got {actual}"


def test_tufts_mapping_preserves_position_and_flips_quadrant():
    """The mirror changes side only — the position digit must survive untouched.

    This is the property that makes the mapping anatomically meaningful: a canine stays a
    canine. It is what the measured tooth-length profile confirmed (Tufts 6/11/22/27 are the
    longest teeth in each arch, and all four land on FDI position 3, the canine).
    """
    for title, expected in EXPECTED_TUFTS.items():
        standard = universal_to_fdi(title)
        assert expected % 10 == standard % 10, f"position digit changed for '{title}'"
        assert expected // 10 != standard // 10, f"quadrant not flipped for '{title}'"
    for canine in ("6", "11", "22", "27"):
        assert tufts_title_to_fdi(canine) % 10 == 3, "canine must land on FDI position 3"
    for third_molar in ("1", "16", "17", "32"):
        assert tufts_title_to_fdi(third_molar) % 10 == 8, "third molar must be position 8"


def test_tufts_mapping_is_a_bijection():
    """32 distinct titles must produce 32 distinct FDI codes — no tooth may be lost."""
    codes = [tufts_title_to_fdi(str(n)) for n in range(1, 33)]
    assert len(set(codes)) == 32, "mirrored mapping collapsed two teeth onto one code"
    assert set(codes) == set(UNIVERSAL_TO_FDI.values()), "mapping left the valid FDI set"


def test_tufts_rejects_deciduous_and_junk():
    """Deciduous letters are deliberately unmapped; junk returns None rather than guessing."""
    for letter in ("A", "J", "K", "T"):
        assert tufts_title_to_fdi(letter) is None
    assert tufts_title_to_fdi("0") is None
    assert tufts_title_to_fdi("33") is None
    assert tufts_title_to_fdi("") is None
    assert tufts_title_to_fdi(None) is None


def test_mirror_is_an_involution():
    """Mirroring twice returns the original code."""
    for fdi in UNIVERSAL_TO_FDI.values():
        assert mirror_fdi_quadrant(mirror_fdi_quadrant(fdi)) == fdi
    assert mirror_fdi_quadrant(99) is None
    assert mirror_fdi_quadrant(None) is None


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("\nAll FDI converter tests passed.")
