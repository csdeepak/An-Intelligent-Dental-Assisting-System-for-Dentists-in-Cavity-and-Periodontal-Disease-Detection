"""Stages 5-6: what every report states, and what the overlay's colours mean (schema 1.6).

No model is loaded: `build_report` and `draw_overlay` run on hand-built stage outputs.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
ri = pytest.importorskip("scripts.run_inference")
cv2 = pytest.importorskip("cv2")


def test_every_report_states_both_untested_severity_grades():
    rep = ri.build_report("x", np.zeros((8, 8, 3), np.uint8), [], [], [], [], [],
                          {"caries": {"method": "lesion-detector"}})
    assert rep["schema_version"] == "opg-report/1.6"
    assert "contrast" in rep["limitations"]["bone_severity_not_evaluated"]
    assert "133 crops" in rep["limitations"]["caries_severity_not_evaluated"]


def _tooth(x, assessable=True, fdi_flags=(), caries="no_caries", flagged=False):
    return {"bbox_xyxy": [x, 60, x + 30, 150], "fdi": 11, "fdi_flags": list(fdi_flags),
            "assessable": assessable, "caries": {"finding": caries},
            "bone_loss": {"finding": "bone_loss" if flagged else "normal", "severity": None}}


def test_overlay_colours_and_line_widths(tmp_path):
    """Grey thin = not assessable (red until 14 Oct 2026, read as most urgent); orange = a
    finding; blue = no finding, thin when the numbering is uncertain."""
    cases = [  # tooth, colour, thick line
        (_tooth(10, assessable=False, flagged=True), ri.OVERLAY_NOT_ASSESSABLE, False),
        (_tooth(60, flagged=True), ri.OVERLAY_FINDING, True),
        (_tooth(110, caries="caries", fdi_flags=["low_confidence"]), ri.OVERLAY_FINDING, True),
        (_tooth(160, fdi_flags=["reassigned_by_one_to_one"]), ri.OVERLAY_NO_FINDING, False),
        (_tooth(210), ri.OVERLAY_NO_FINDING, True),
    ]
    out = tmp_path / "overlay.png"
    ri.draw_overlay(np.zeros((200, 260, 3), np.uint8), {"teeth": [c[0] for c in cases]}, out)
    img = cv2.imread(str(out))
    for tooth, colour, thick in cases:
        x1, y1, _, y2 = tooth["bbox_xyxy"]
        mid = (y1 + y2) // 2                     # the left edge, away from the label above the box
        assert tuple(int(v) for v in img[mid, x1]) == colour
        assert tuple(int(v) for v in img[mid, x1 + 1]) == (colour if thick else (0, 0, 0))


def test_default_checkpoint_pins_match_the_files():
    """A wrong pin would stop every default run; a missing file is a fetch problem, not this."""
    for path, sha in ri.DEFAULT_SHA256.items():
        if path.exists():
            assert ri.file_sha256(str(path)) == sha, path


def test_a_default_checkpoint_with_the_wrong_hash_is_refused_before_loading(tmp_path, monkeypatch):
    pytest.importorskip("ultralytics")
    names = ("detector", "fdi_head", "caries_gate", "caries_severity", "caries_lesion_model",
             "bone_loss", "bone_severity")
    paths = {n: tmp_path / f"{n}.pt" for n in names}
    for p in paths.values():
        p.write_bytes(b"not a checkpoint")      # loading any of these would fail differently
    monkeypatch.setattr(ri, "DEFAULT_SHA256", {paths["detector"].resolve(): "0" * 64})
    with pytest.raises(SystemExit, match="sha256 is not the pinned"):
        ri.load_models(**paths)


def test_every_default_checkpoint_has_a_pin():
    defaults = (ri.DEF_DETECTOR, ri.DEF_FDI_HEAD, ri.DEF_CARIES_GATE, ri.DEF_CARIES_SEVERITY,
                ri.DEF_CARIES_LESION_MODEL, ri.DEF_BONE_LOSS, ri.DEF_BONE_SEVERITY)
    assert {p.resolve() for p in defaults} == set(ri.DEFAULT_SHA256)


# ---- input checks, NaN and the in-memory overlay (15 Oct 2026, schema 1.6) ----
def test_input_checks_warn_only_outside_the_training_radiographs():
    assert ri.check_input(np.zeros((840, 1615, 3), np.uint8)) == []          # Tufts shape
    assert ri.check_input(np.zeros((1316, 2850, 3), np.uint8)) == []         # DENTEX shape
    assert "portrait" in ri.check_input(np.zeros((1615, 840, 3), np.uint8))[0]
    assert "portrait or square" in ri.check_input(np.zeros((640, 640, 3), np.uint8))[0]
    assert "aspect ratio" in ri.check_input(np.zeros((840, 2600, 3), np.uint8))[0]
    assert any("low resolution" in w for w in ri.check_input(np.zeros((300, 600, 3), np.uint8)))
    assert any("16" in w for w in ri.check_input(np.zeros((840, 1615, 3), np.uint8), "uint16"))


def test_a_nan_numbering_confidence_is_not_assessable():
    rep = ri.build_report("x", np.zeros((200, 400, 3), np.uint8), [[0, 0, 10, 10]], [0.9],
                          [{"fdi": 11, "quadrant": 1, "position": 1, "confidence": float("nan"),
                            "flags": []}],
                          [{"finding": "no_caries"}], [{"finding": "normal", "severity": None}],
                          {"caries": {"method": "lesion-detector"}}, input_warnings=["w"])
    assert rep["teeth"][0]["assessable"] is False
    assert "fdi_confidence_below_threshold" in rep["teeth"][0]["not_assessable_reasons"]
    assert rep["image"]["warnings"] == ["w"]
    with pytest.raises(ValueError):                  # the CLI and the app refuse to write NaN
        json.dumps(rep, allow_nan=False)


def test_an_empty_detection_gives_an_empty_well_formed_report():
    rep = ri.build_report("x", np.zeros((8, 8, 3), np.uint8), [], [], [], [], [],
                          {"caries": {"method": "lesion-detector"}})
    assert rep["teeth"] == [] and set(rep["summary"].values()) == {0}
    assert rep["image"]["warnings"] == []


def test_the_overlay_is_returned_and_written_only_when_asked(tmp_path):
    viz = ri.draw_overlay(np.zeros((200, 260, 3), np.uint8), {"teeth": [_tooth(10)]})
    assert viz.shape == (200, 260, 3) and not list(tmp_path.iterdir())
