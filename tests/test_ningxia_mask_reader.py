"""Tests for the Ningxia GT mask reader.

The bug these cover: `import ultralytics` monkeypatches `cv2.imread` globally with
`ultralytics.utils.patches.imread`, whose final line is

    return im[..., None] if im.ndim == 2 else im

so a cv2.IMREAD_GRAYSCALE read returns (H, W, 1) rather than (H, W). Every mask read in
`ningxia_external.py` happens after the pipeline's `from ultralytics import YOLO`, so the
patched reader is always the one that runs, and `affected_tooth_sensitivity` died on
`H, W = mb.shape` at the first image of the 27 Aug C2 re-run.

It is environment-dependent (the two machines run different ultralytics versions), it is
applied by an unrelated import, and for code that does not unpack the shape it fails
silently rather than loudly. So the reader normalises shape itself and is tested against
both reader behaviours explicitly.
"""

import importlib.util
import os
import sys

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

_SPEC = importlib.util.spec_from_file_location(
    "ningxia_external_for_test",
    os.path.join(os.path.dirname(__file__), "..", "scripts", "eval", "ningxia_external.py"),
)
_NX = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_NX)
read_mask_2d = _NX.read_mask_2d


def _write_mask(tmp_path, arr):
    p = tmp_path / "mask.png"
    cv2.imwrite(str(p), arr)
    return p


def _plain_mask():
    m = np.zeros((40, 60), np.uint8)
    m[10:20, 15:35] = 255
    return m


def test_plain_2d_grayscale_mask(tmp_path):
    p = _write_mask(tmp_path, _plain_mask())
    mb = read_mask_2d(p)
    assert mb.ndim == 2, "must always return a 2-D array"
    assert mb.shape == (40, 60)
    assert mb.dtype == bool
    assert mb.sum() == 10 * 20


def test_survives_the_ultralytics_trailing_channel_patch(tmp_path, monkeypatch):
    """The actual regression: a reader that appends a singleton channel axis."""
    p = _write_mask(tmp_path, _plain_mask())
    real = cv2.imread

    def patched(filename, flags=cv2.IMREAD_COLOR):
        im = real(filename, flags)
        return im[..., None] if im is not None and im.ndim == 2 else im

    monkeypatch.setattr(cv2, "imread", patched)
    assert patched(str(p), cv2.IMREAD_GRAYSCALE).ndim == 3, "test setup must reproduce the patch"

    mb = read_mask_2d(p)
    assert mb.ndim == 2
    assert mb.shape == (40, 60)
    assert mb.sum() == 10 * 20


def test_patched_and_unpatched_readers_agree(tmp_path, monkeypatch):
    """Same file, both reader behaviours, identical result -- the property that matters."""
    p = _write_mask(tmp_path, _plain_mask())
    unpatched = read_mask_2d(p)

    real = cv2.imread
    monkeypatch.setattr(
        cv2, "imread",
        lambda f, flags=cv2.IMREAD_COLOR: (
            lambda im: im[..., None] if im is not None and im.ndim == 2 else im
        )(real(f, flags)),
    )
    assert np.array_equal(read_mask_2d(p), unpatched)


def test_three_channel_mask_collapses_to_any_channel(tmp_path):
    """A mask saved as RGB must not silently read as one channel's worth of pixels."""
    m = np.zeros((30, 30, 3), np.uint8)
    m[5:10, 5:10, 1] = 255          # marked in green only
    p = tmp_path / "rgb.png"
    cv2.imwrite(str(p), m)

    mb = read_mask_2d(p)
    assert mb.ndim == 2
    assert mb.sum() > 0, "a region marked in a single channel must still register"


def test_missing_file_returns_none(tmp_path):
    """Callers rely on None to count mask_missing rather than crash."""
    assert read_mask_2d(tmp_path / "does_not_exist.png") is None


def test_empty_mask_is_all_false(tmp_path):
    p = _write_mask(tmp_path, np.zeros((20, 20), np.uint8))
    mb = read_mask_2d(p)
    assert mb.ndim == 2 and not mb.any()
