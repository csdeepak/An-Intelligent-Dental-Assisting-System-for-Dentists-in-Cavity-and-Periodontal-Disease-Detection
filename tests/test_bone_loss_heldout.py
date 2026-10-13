"""Crop geometry, label rule and manifest parsing of the held-out Stage-4a score
(outputs/bone_loss_eval/heldout/PRE_REGISTRATION.md). The numbers are the construction
notebook's formula worked by hand."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "eval"))
from bone_loss_heldout import CLEAN_ROW, OVERLAP_T, expanded_box, overlap_ratio  # noqa: E402


def test_expanded_box_is_the_notebook_formula():
    # centre (120, 250); 1.5 x 40 = 60 wide, 2.0 x 100 = 200 tall
    assert expanded_box(100, 200, 40, 100, 1615, 840) == (90, 150, 150, 350)
    # clipped at the top-left and at the bottom-right
    assert expanded_box(0, 0, 40, 100, 1615, 840) == (0, 0, 50, 150)
    assert expanded_box(1600, 800, 20, 60, 1615, 840) == (1595, 770, 1615, 840)
    # int() truncates both corners: centre 12.5, half-width 5.25 -> 7.25 and 17.75
    assert expanded_box(9, 0, 7, 10, 100, 100)[::2] == (7, 17)


def test_overlap_label_rule():
    mask = np.zeros((100, 100), np.uint8)
    mask[10:12, 10:15] = 255                                  # 10 marked pixels
    assert overlap_ratio(mask, 0, 0, 20, 20) == 10 / 400      # 2.5% -> diseased
    assert overlap_ratio(mask, 0, 0, 20, 20) > OVERLAP_T
    assert not overlap_ratio(mask, 0, 0, 50, 50) > OVERLAP_T  # 10 / 2500 = 0.4% -> normal
    assert overlap_ratio(mask, 50, 50, 60, 60) == 0.0


def test_only_clean_non_augmented_rows_parse():
    m = CLEAN_ROW.match("1034_T19_0649.png")
    assert (m["stem"], m["tooth"]) == ("1034", "19")
    assert CLEAN_ROW.match("12_TK_0003.png")["tooth"] == "K"   # a deciduous title
    assert CLEAN_ROW.match("1000_T31_jit_4228.png") is None
    assert CLEAN_ROW.match("aug0_196_T1_0108.png") is None
