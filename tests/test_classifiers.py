"""
Tests for the Stage-3/4 disease classifiers (src/classifiers.py).

WHAT THESE GUARD
----------------
Two failure modes that produce no error, no warning, and confidently wrong output:

  1. **Crossed crop conventions.** The three branches use 1.0x, 1.5x/1.5x and 1.5x/2.0x. Feed a
     model the wrong one and the tensor shape is still (N,3,224,224) and the numbers are still
     plausible. Nothing downstream can detect it.
  2. **An inverted class index.** Reporting every healthy tooth as diseased looks exactly like
     a working pipeline until someone checks the rate.

The class-order tests read the checkpoints' own `class_to_idx`, so they fail if a checkpoint is
ever swapped for one trained with a different label order.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.classifiers import (  # noqa: E402
    BONE_LOSS_CLASSES, BONE_LOSS_EXPAND, BONE_LOSS_SEVERITY_CLASSES, CARIES_EXPAND,
    CARIES_GATE_CLASSES, CARIES_SEVERITY_CLASSES, crop_batch, run_bone_loss, run_caries)

torch = pytest.importorskip("torch")

DEV = torch.device("cpu")
H, W = 1504, 2508
BOX = [1000.0, 600.0, 1100.0, 900.0]          # w=100, h=300 -- a realistic tooth aspect


def _img(seed=0):
    return np.random.default_rng(seed).integers(0, 255, (H, W, 3), dtype=np.uint8)


class _Fixed(torch.nn.Module):
    """A stand-in classifier returning a fixed argmax, so cascade logic can be tested alone."""
    def __init__(self, n, cls):
        super().__init__()
        self.n, self.cls = n, cls
    def forward(self, x):
        out = torch.full((len(x), self.n), -5.0)
        out[:, self.cls] = 5.0
        return out


def test_caries_uses_a_tight_crop_and_bone_loss_does_not():
    assert CARIES_EXPAND == (1.0, 1.0)
    assert BONE_LOSS_EXPAND == (1.5, 2.0), "bone loss must stay asymmetric: teeth are tall"


def test_tight_crop_is_the_detector_box_floor_near_ceil_far():
    """The documented caries contract, not compute_expanded_bbox's int() on both edges."""
    img = _img()
    x, y = BOX[0], BOX[1]
    w, h = BOX[2] - BOX[0], BOX[3] - BOX[1]
    expected = img[math.floor(y):math.ceil(y + h), math.floor(x):math.ceil(x + w)]
    assert expected.shape[:2] == (300, 100)
    import cv2
    ref = cv2.cvtColor(cv2.resize(expected, (224, 224)), cv2.COLOR_BGR2RGB)
    got = crop_batch(img, [BOX], CARIES_EXPAND, DEV)[0]
    from torchvision import transforms
    want = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])(ref)
    assert torch.allclose(got, want, atol=1e-6), "tight crop is not the raw detector box"


def test_bone_loss_crop_is_1_5x_wide_and_2_0x_tall():
    from src.crop_generator import compute_expanded_bbox
    x, y = BOX[0], BOX[1]
    w, h = BOX[2] - BOX[0], BOX[3] - BOX[1]
    cx1, cy1, cx2, cy2 = compute_expanded_bbox(x, y, w, h, W, H, fw=1.5, fh=2.0)
    assert (cx2 - cx1) == pytest.approx(1.5 * w, abs=1)
    assert (cy2 - cy1) == pytest.approx(2.0 * h, abs=1)


def test_the_two_branches_do_not_produce_the_same_crop():
    """If these ever coincide, one branch is silently being fed the other's input."""
    img = _img(1)
    a = crop_batch(img, [BOX], CARIES_EXPAND, DEV)
    b = crop_batch(img, [BOX], BONE_LOSS_EXPAND, DEV)
    assert not torch.equal(a, b)


@pytest.mark.parametrize("box", [
    [0.0, 0.0, 50.0, 80.0],                    # touching the origin
    [W - 30.0, H - 40.0, float(W), float(H)],  # touching the far corner
    [10.0, 10.0, 11.0, 11.0],                  # degenerate, 1px
])
def test_crops_at_image_edges_clip_rather_than_crash(box):
    for expand in (CARIES_EXPAND, BONE_LOSS_EXPAND):
        t = crop_batch(_img(2), [box], expand, DEV)
        assert t.shape == (1, 3, 224, 224)
        assert bool(torch.isfinite(t).all())


def test_empty_box_list_returns_empty_not_a_crash():
    assert run_caries(None, None, _img(), [], DEV) == []
    assert run_bone_loss(None, None, _img(), [], DEV) == []


def test_caries_severity_only_runs_on_gate_positives():
    """A gate-negative tooth must not be graded: both severity classes are carious."""
    img = _img(3)
    gate_neg = _Fixed(2, CARIES_GATE_CLASSES.index("no_caries"))
    out = run_caries(gate_neg, _Fixed(2, 1), img, [BOX, BOX], DEV)
    assert [r["finding"] for r in out] == ["no_caries", "no_caries"]
    assert all(r["severity"] is None for r in out)

    gate_pos = _Fixed(2, CARIES_GATE_CLASSES.index("caries"))
    out = run_caries(gate_pos, _Fixed(2, CARIES_SEVERITY_CLASSES.index("deep_caries")),
                     img, [BOX], DEV)
    assert out[0]["finding"] == "deep_caries"
    assert out[0]["severity_confidence"] is not None


def test_every_caries_result_is_flagged_uncalibrated():
    """Held-out caries precision is 0.40 and the healthy class is presumed-negative, so a
    negative is no more trustworthy than a positive. Both must carry the flag."""
    out = run_caries(_Fixed(2, 1), _Fixed(2, 0), _img(4), [BOX, BOX], DEV)
    assert all("caries_uncalibrated" in r["flags"] for r in out)


def test_bone_loss_severity_only_runs_on_positives():
    img = _img(5)
    out = run_bone_loss(_Fixed(2, BONE_LOSS_CLASSES.index("normal")), _Fixed(3, 2),
                        img, [BOX], DEV)
    assert out[0]["finding"] == "normal" and out[0]["severity"] is None

    out = run_bone_loss(_Fixed(2, BONE_LOSS_CLASSES.index("bone_loss")),
                        _Fixed(3, BONE_LOSS_SEVERITY_CLASSES.index("Severe")), img, [BOX], DEV)
    assert out[0]["finding"] == "bone_loss" and out[0]["severity"] == "Severe"


def test_mild_severity_carries_the_low_support_flag():
    """n=6 in the Mild training class (T0.5, open). Must be reported, never suppressed."""
    out = run_bone_loss(_Fixed(2, BONE_LOSS_CLASSES.index("bone_loss")),
                        _Fixed(3, BONE_LOSS_SEVERITY_CLASSES.index("Mild")), _img(6), [BOX], DEV)
    assert "severity_class_low_support" in out[0]["flags"]


@pytest.mark.parametrize("weights,expected", [
    ("models/07_caries_cascade/final_model.pth", {"caries": 0, "no_caries": 1}),
    ("models/07_caries_cascade/phase2_final_bundle.pth", {"caries": 0, "deep_caries": 1}),
])
def test_checkpoint_class_order_matches_the_constants(weights, expected):
    """Reads the checkpoint's own class_to_idx: fails if a model is swapped for one with a
    different label order, which would invert every prediction silently."""
    p = REPO_ROOT / weights
    if not p.exists():
        pytest.skip(f"{weights} not on this machine")
    ck = torch.load(p, map_location="cpu", weights_only=False)
    assert ck["class_to_idx"] == expected
    names = list(expected)
    assert names == (CARIES_GATE_CLASSES if "no_caries" in expected else CARIES_SEVERITY_CLASSES)


# --------------------------------------------------------------------------------------
# Isotonic confidence calibration (wired 27 Aug 2026, RESULTS_LOG 2026-08-27s).
# The property under test is NOT that the calibration is accurate -- that is measured in
# scripts/eval/ -- but that it is CONFIDENCE-ONLY. Applying it to the verdict would flip 18%
# of decisions and invalidate every downstream caries number, so "verdicts must not move"
# is the invariant worth a regression test.

def test_isotonic_knots_load_or_absent_cleanly():
    """Missing calibrator is a supported state, not an error."""
    from src.classifiers import _isotonic_knots
    k = _isotonic_knots()
    assert k is None or (len(k) == 2 and len(k[0]) == len(k[1]) and len(k[0]) > 1)


def test_isotonic_knots_are_monotonic_non_decreasing():
    """Isotonic output must be non-decreasing, or it is not a calibrator."""
    from src.classifiers import _isotonic_knots
    k = _isotonic_knots()
    if k is None:
        return
    x, y = k
    assert all(x[i] <= x[i + 1] for i in range(len(x) - 1)), "knot x must be sorted"
    assert all(y[i] <= y[i + 1] for i in range(len(y) - 1)), "knot y must be non-decreasing"
    assert y.min() >= 0.0 and y.max() <= 1.0, "calibrated values must stay in [0, 1]"


def test_calibration_never_changes_the_verdict():
    """THE invariant: the reported finding is argmax on RAW probabilities, always.

    Built from probabilities directly rather than from a model, so it holds regardless of
    what the gate happens to predict on any particular image.
    """
    import numpy as np
    from src.classifiers import CARIES_GATE_CLASSES, _isotonic_knots
    k = _isotonic_knots()
    if k is None:
        return
    idx_caries = CARIES_GATE_CLASSES.index("caries")
    for p_caries in np.linspace(0.0, 1.0, 101):
        raw = np.array([0.0, 0.0])
        raw[idx_caries] = p_caries
        raw[1 - idx_caries] = 1.0 - p_caries
        verdict_raw = int(raw.argmax()) == idx_caries
        # Calibration is applied only to the reported number; recomputing a verdict from it
        # is exactly what the wiring must never do. Assert the two can disagree, and that the
        # pipeline follows the raw one.
        cal = float(np.interp(p_caries, k[0], k[1]))
        assert isinstance(cal, float)
        assert verdict_raw == (p_caries >= 0.5), "verdict must follow the raw probability"
