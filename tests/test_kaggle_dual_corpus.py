"""Tests for the third FDI corpus (Kaggle dual-labeled).

`mirror_fdi` is the function that decides whether 13,166 teeth are read left-right correctly.
Tufts was mirrored and looked normal; getting this backwards would train a third of v3's data on
side-swapped labels and show up only as "the new corpus didn't help". So the mapping is pinned
here explicitly, in both directions.

The split tests exist because an image-level split silently degrading into a tooth-level one
would leak the same mouth across train and test, inflating every number the corpus produces.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "kaggle_dual"))

from build_enumeration_crops import VALID, make_split, poly_bbox  # noqa: E402
from verify_fdi_convention import mirror_fdi  # noqa: E402


def test_mirror_swaps_upper_quadrants():
    assert mirror_fdi("11") == "21"
    assert mirror_fdi("18") == "28"
    assert mirror_fdi("21") == "11"


def test_mirror_swaps_lower_quadrants():
    assert mirror_fdi("31") == "41"
    assert mirror_fdi("38") == "48"
    assert mirror_fdi("46") == "36"


def test_mirror_never_changes_position():
    for code in sorted(VALID):
        assert mirror_fdi(code)[1] == code[1]


def test_mirror_is_its_own_inverse():
    for code in sorted(VALID):
        assert mirror_fdi(mirror_fdi(code)) == code


def test_mirror_never_leaves_the_valid_vocabulary():
    for code in sorted(VALID):
        assert mirror_fdi(code) in VALID


def test_mirror_never_maps_upper_to_lower():
    """A left/right mirror must not change arch. If it ever does, the arbiter comparison in
    verify_fdi_convention becomes meaningless."""
    for code in sorted(VALID):
        assert (int(code[0]) <= 2) == (int(mirror_fdi(code)[0]) <= 2)


def test_valid_vocabulary_is_the_32_permanent_codes():
    assert len(VALID) == 32
    assert "91" not in VALID          # the 24 stray labels in this corpus
    assert "51" not in VALID          # deciduous


def test_poly_bbox_from_polygon():
    pts = [[10, 20], [30, 20], [30, 80], [10, 80]]
    assert poly_bbox(pts) == (10, 20, 20, 60)


def test_poly_bbox_handles_unordered_points():
    a = poly_bbox([[30, 80], [10, 20], [30, 20], [10, 80]])
    b = poly_bbox([[10, 20], [30, 20], [30, 80], [10, 80]])
    assert a == b


def test_split_is_deterministic():
    stems = [str(i) for i in range(200)]
    assert make_split(stems) == make_split(stems)


def test_split_is_image_level_and_covers_everything():
    stems = [str(i) for i in range(200)]
    s = make_split(stems)
    assert set(s) == set(stems)
    assert set(s.values()) == {"train", "val", "test"}


def test_split_proportions_are_roughly_70_15_15():
    stems = [str(i) for i in range(1000)]
    s = make_split(stems)
    n = len(stems)
    counts = {k: sum(1 for v in s.values() if v == k) for k in ("train", "val", "test")}
    assert abs(counts["train"] / n - 0.70) < 0.02
    assert abs(counts["val"] / n - 0.15) < 0.02
    assert abs(counts["test"] / n - 0.15) < 0.02


def test_split_seed_changes_the_assignment():
    stems = [str(i) for i in range(200)]
    assert make_split(stems, seed=1) != make_split(stems, seed=2)
