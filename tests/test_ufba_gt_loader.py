"""UFBA-425 ground-truth loader used by row P (Amendment 3 of the Stage-1 switch pre-registration)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "eval"))
from validate_fdi_assignment_tufts import load_ufba_gt  # noqa: E402


def test_class_to_fdi_and_box(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("0 0.5 0.5 0.1 0.2\n7 0.25 0.25 0.1 0.1\n8 0.6 0.4 0.1 0.1\n31 0.1 0.9 0.2 0.2\n"
                 "16 0.1 0.1 0.3 0.1 0.3 0.4 0.1 0.4\n")          # last line: a polygon
    gt = load_ufba_gt(f, 1000, 500)
    assert [g["fdi"] for g in gt] == [11, 18, 21, 48, 31]
    assert gt[0]["bbox"] == [450.0, 200.0, 550.0, 300.0] and gt[0]["centroid"] == [500.0, 250.0]
    assert [round(v) for v in gt[4]["bbox"]] == [100, 50, 300, 200]
