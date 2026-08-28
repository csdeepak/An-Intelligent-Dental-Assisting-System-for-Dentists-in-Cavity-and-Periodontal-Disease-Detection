"""Tests for the C1 constant-guess baselines.

`heldout_constant` produces the most consequential number in C1 -- an image-blind answer that
outscores the pipeline on tooth-level F1. A bug that let the fit set touch the scored set would
inflate it and make the finding look worse than reality; a bug that broke the fit would make it
vanish. Both directions are pinned here.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

from c1_constant_baseline import best_constant, heldout_constant, score_sets  # noqa: E402

DISEASE = Path.home() / "Downloads" / "Capstone" / "DENTEX" / "disease"
needs_data = pytest.mark.skipif(not DISEASE.exists(), reason="DENTEX disease set not on this machine")


def test_score_sets_perfect_prediction():
    gt = {"a": {"16"}, "b": {"26", "36"}}
    r = score_sets(gt, dict(gt))
    assert r["precision"] == r["recall"] == r["f1"] == 1.0


def test_score_sets_counts_tp_fp_fn():
    gt = {"a": {"16", "17"}}
    r = score_sets(gt, {"a": {"16", "26"}})
    assert (r["tp"], r["fp"], r["fn"]) == (1, 1, 1)


def test_best_constant_finds_the_obvious_answer():
    # every image is carious at 16 -> the best fixed answer is exactly {16}
    gt = {f"i{n}": {"16"} for n in range(20)}
    const, f1 = best_constant(gt)
    assert const == {"16"}
    assert f1 == pytest.approx(1.0)


def test_best_constant_stops_instead_of_padding():
    """It must stop when adding a code stops helping -- otherwise it pads to max_size and the
    'best constant' is dominated by false positives."""
    gt = {f"i{n}": {"16"} for n in range(20)}
    gt["i0"] = {"16", "48"}          # 48 is rare; adding it should not help F1
    const, _ = best_constant(gt)
    assert "48" not in const


def test_best_constant_respects_max_size():
    gt = {f"i{n}": {str(10 + n)} for n in range(20)}
    const, _ = best_constant(gt, max_size=3)
    assert len(const) <= 3


@needs_data
def test_heldout_fit_set_is_disjoint_from_scored_set():
    """The whole claim rests on this. heldout_constant asserts it internally; this makes the
    assertion a test rather than a runtime hope."""
    from c1_vlm_baseline import load_exemplars, load_gt
    gt = load_gt(DISEASE)
    pool = load_exemplars(DISEASE, 10_000)
    assert pool, "fit pool empty"
    assert not (set(s for s, _ in pool) & set(gt))


@needs_data
def test_heldout_constant_beats_nothing_by_construction_but_is_reported_honestly():
    """Regression pin: the held-out constant scores ~0.32 on the 164 scored images and the
    pipeline ~0.29. If this ever flips, the paper's framing has to change with it -- so a silent
    change must fail here rather than be discovered by a reviewer."""
    import json
    from c1_vlm_baseline import load_gt
    gt = load_gt(DISEASE)
    _, _, n_fit, r = heldout_constant(DISEASE, gt)
    assert n_fit > 50
    assert 0.28 < r["f1"] < 0.38

    pipe = json.loads((REPO_ROOT / "outputs/c1_vlm/arm_pipeline.json").read_text())
    p = {k: set(v) for k, v in pipe["predictions"].items()}
    pr = score_sets({k: v for k, v in gt.items() if k in p}, p)
    # The uncomfortable fact, pinned so it cannot quietly disappear from the record.
    assert r["f1"] > pr["f1"], "held-out constant no longer beats the pipeline -- update the paper"
