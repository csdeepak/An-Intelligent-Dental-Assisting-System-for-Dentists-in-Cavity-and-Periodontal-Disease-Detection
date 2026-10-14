"""Tests for verify_invariants' run_summary hash attribution.

The bug these cover, in full: `hash_from_summary` used to return "the last 64-hex
token anywhere in the file". That is correct only while every run_summary documents
exactly one checkpoint. When models/03 was tagged on 27 Aug 2026 its summary listed
both `bone_loss_resnet18_best.pth` and `bone_loss_resnet18_final.pth`, so the
pipeline's actual default (`best`) was checked against `final`'s hash and the
invariant failed. Attribution is now by filename, with last-hash kept as a fallback.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'eval'))

from verify_invariants import hash_from_summary

A = "a" * 64
B = "b" * 64

TWO_CHECKPOINTS = f"""
WEIGHTS
best_model.pth    44,791,499 B   (the pipeline default)
  sha256 {A}
final_model.pth   44,791,627 B   (last epoch, NOT used)
  sha256 {B}
"""


def test_attributes_each_hash_to_its_own_checkpoint():
    """The whole point: two checkpoints in one summary must not collide."""
    assert hash_from_summary(TWO_CHECKPOINTS, "best_model.pth") == A
    assert hash_from_summary(TWO_CHECKPOINTS, "final_model.pth") == B


def test_does_not_regress_to_last_hash_in_file():
    """The historical bug: `best` silently resolved to `final`'s hash."""
    assert hash_from_summary(TWO_CHECKPOINTS, "best_model.pth") != B


def test_single_checkpoint_summary_still_works():
    """Every pre-27-Aug summary names one checkpoint; those must keep passing."""
    text = f"WEIGHTS\nonly_model.pth 123 B\n  sha256 {A}\n"
    assert hash_from_summary(text, "only_model.pth") == A


def test_falls_back_when_the_filename_is_not_mentioned():
    """A summary that records a hash but never names the file still resolves."""
    text = f"Frozen 27 Aug 2026\n  sha256 {A}\n"
    assert hash_from_summary(text, "unmentioned.pth") == A


def test_returns_none_when_no_hash_recorded():
    """inv_weight_hashes reports NO HASH RECORDED rather than crashing."""
    assert hash_from_summary("no hashes here at all\n", "x.pth") is None


def test_ignores_tokens_that_are_not_hex():
    """A 64-char non-hex token must not be mistaken for a digest."""
    text = "sha256 " + ("z" * 64) + "\n"
    assert hash_from_summary(text, "x.pth") is None


def test_handles_punctuation_around_filenames():
    """Filenames appear backticked or parenthesised in these summaries."""
    text = f"`wrapped_model.pth` (the default)\n  sha256 {A}\n"
    assert hash_from_summary(text, "wrapped_model.pth") == A


def test_real_bone_loss_summary_resolves_to_best_not_final():
    """End-to-end against the committed file that exposed the bug."""
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    d = repo / "models" / "03_bone_loss_model_training_notebook_models"
    summary = (d / "run_summary.txt").read_text(encoding="utf-8")
    best = hash_from_summary(summary, "bone_loss_resnet18_best.pth")
    final = hash_from_summary(summary, "bone_loss_resnet18_final.pth")
    assert best is not None and final is not None
    assert best != final, "the two checkpoints must not resolve to one hash"

    import hashlib
    actual = hashlib.sha256((d / "bone_loss_resnet18_best.pth").read_bytes()).hexdigest()
    assert best == actual


def test_path_prefixed_filename_resolves_by_basename():
    """models/16 writes `weights/best.pt`; the lookup asks for `best.pt`."""
    text = f"weights/best.pt   sha256 {A}\nweights/last.pt   sha256 {B}\n"
    assert hash_from_summary(text, "best.pt") == A
    assert hash_from_summary(text, "last.pt") == B


def test_real_lesion_detector_summary_resolves_best_not_last():
    """Until 14 Oct 2026 this returned last.pt's hash (f774bb1e...)."""
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    summary = (repo / "models" / "16_lever_b_pooled" / "run_summary.txt").read_text(encoding="utf-8")
    assert hash_from_summary(summary, "best.pt").startswith("029018db")
    assert hash_from_summary(summary, "last.pt").startswith("f774bb1e")
