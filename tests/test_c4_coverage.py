"""Tests for the C4 coverage-accuracy machinery.

The curve is the kind of code that is easy to get subtly backwards -- sorting the wrong way
produces a plausible-looking curve that says the opposite thing (accuracy IMPROVING as you keep
your least confident predictions). These tests pin the direction, the arithmetic, and the one
property the whole contribution rests on: that the shuffled control collapses the gain to zero.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

pytest.importorskip("numpy")
from c4_coverage_accuracy import at_coverage, curve, gain_stats  # noqa: E402


def test_curve_is_ranked_most_confident_first():
    # Two right answers held confidently, two wrong ones held weakly. Keeping only the top half
    # must give 100%; keeping everything must give 50%.
    items = [(0.9, True), (0.8, True), (0.2, False), (0.1, False)]
    cv = curve(items)
    assert cv[0]["accuracy"] == 1.0
    assert cv[1]["accuracy"] == 1.0
    assert cv[-1]["accuracy"] == 0.5
    assert cv[-1]["coverage"] == 1.0


def test_curve_direction_is_not_inverted():
    # If the sort were reversed this test fails: accuracy would RISE with coverage.
    items = [(0.99, True)] * 10 + [(0.01, False)] * 10
    cv = curve(items)
    assert cv[0]["accuracy"] > cv[-1]["accuracy"]


def test_curve_full_coverage_equals_plain_accuracy():
    items = [(0.5, True), (0.4, False), (0.3, True)]
    assert curve(items)[-1]["accuracy"] == pytest.approx(2 / 3)


def test_at_coverage_picks_nearest():
    items = [(i / 100, i % 3 != 0) for i in range(100)]
    assert at_coverage(curve(items), 0.75)["coverage"] == pytest.approx(0.75, abs=0.01)


def test_gain_is_positive_when_confidence_is_informative():
    import numpy as np
    rng = np.random.default_rng(0)
    # confidence correlates with correctness
    items, groups = [], []
    for i in range(400):
        c = rng.uniform()
        items.append((c, rng.uniform() < c))
        groups.append(i // 4)
    g = gain_stats(items, groups, n_boot=200)
    assert g["gain_pp"] > 0
    assert g["ci95_pp"][0] > 0            # interval excludes zero


def test_shuffled_control_collapses_the_gain():
    """The property the contribution rests on: break the confidence-correctness link and the
    gain must vanish. If this ever passes with a large shuffled gain, the curve is measuring
    something other than what it claims."""
    import numpy as np
    rng = np.random.default_rng(1)
    items, groups = [], []
    for i in range(400):
        c = rng.uniform()
        items.append((c, rng.uniform() < c))
        groups.append(i // 4)
    g = gain_stats(items, groups, n_boot=100)
    assert abs(g["shuffled_control_gain_pp"]) < 2.0
    assert g["gain_pp"] > g["shuffled_control_gain_pp"] + 5


def test_uninformative_confidence_gives_no_gain():
    import numpy as np
    rng = np.random.default_rng(2)
    # correctness independent of confidence -> abstention buys nothing
    items = [(rng.uniform(), bool(rng.integers(0, 2))) for _ in range(400)]
    g = gain_stats(items, list(range(400)), n_boot=200)
    assert g["ci95_pp"][0] < 0 < g["ci95_pp"][1]   # CI straddles zero


def test_gain_stats_clusters_by_group_not_item():
    """n_images must reflect the number of CLUSTERS, not the number of teeth -- the whole point
    of the correction (teeth within a radiograph are not independent)."""
    items = [(0.5, True)] * 20
    g = gain_stats(items, [0] * 10 + [1] * 10, n_boot=20)
    assert g["n_images"] == 2
