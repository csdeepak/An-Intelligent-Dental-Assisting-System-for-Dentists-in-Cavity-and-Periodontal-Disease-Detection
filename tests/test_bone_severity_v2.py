"""Stage-4b retraining (outputs/bone_loss_eval/v3_severity/PRE_REGISTRATION.md): the band cut points
and the two metrics the single test pass reports. No data, no model."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "tufts"))
sys.path.insert(0, str(ROOT / "scripts" / "eval"))
from train_bone_severity_v2 import CUTS, band, macro_f1  # noqa: E402
from bone_severity_v2_eval import qwk                     # noqa: E402


def test_bands_follow_the_registered_cut_points():
    assert CUTS == (0.05, 0.15)
    assert [band(x) for x in (0.0101, 0.05, 0.0501, 0.15, 0.1501, 1.0)] == [0, 0, 1, 1, 2, 2]


def test_macro_f1_perfect_and_constant():
    y = np.array([0, 1, 2, 2])
    assert macro_f1(y, y) == 1.0
    assert abs(macro_f1(y, np.array([2, 2, 2, 2])) - (2 * 2 / (2 * 2 + 2)) / 3) < 1e-12


def test_quadratic_kappa_rewards_order():
    y = [0, 1, 2, 0, 1, 2]
    assert qwk(y, y) == 1.0
    assert qwk(y, [2, 1, 0, 2, 1, 0]) < 0          # reversed order is worse than chance
    assert qwk(y, [1, 1, 1, 1, 1, 1]) == 0.0       # a constant prediction carries no agreement
