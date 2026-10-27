"""Pure pieces of the Stage-4a retraining script (outputs/bone_loss_eval/v2_retrain/PRE_REGISTRATION.md)."""
import math
import random
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "tufts"))
from train_bone_loss_v2 import GAMMA, augment, confusion, focal_loss, notebook_jitter  # noqa: E402


def test_jitter_stays_in_the_image_and_within_15_percent():
    f = notebook_jitter(random.Random(0))
    for _ in range(500):
        x, y, w, h = f(100, 200, 40, 100, 1615, 840)
        assert abs(x - 100) <= 6 + 1e-9 and abs(y - 200) <= 15 + 1e-9
        assert abs(w - 40) <= 6 + 1e-9 and abs(h - 100) <= 15 + 1e-9
    x, y, w, h = notebook_jitter(random.Random(1))(1600, 800, 14, 39, 1615, 840)   # at the corner
    assert x >= 0 and y >= 0 and x + w <= 1615 + 1e-9 and y + h <= 840 + 1e-9


def test_augment_keeps_shape_and_range():
    img = (np.arange(224 * 224).reshape(224, 224) % 256).astype(np.uint8)
    out = augment(img, np.random.default_rng(0))
    assert out.shape == (224, 224) and out.dtype == np.float32
    assert 0.0 <= out.min() and out.max() <= 255.0


def test_focal_loss_matches_the_formula():
    logits = torch.tensor([[2.0, 0.0], [0.0, 1.0]])
    targets = torch.tensor([0, 0])
    alpha = torch.tensor([0.5, 2.0])
    p = [math.exp(2) / (math.exp(2) + 1), 1 / (1 + math.e)]           # p_t of the true class
    want = sum(0.5 * (1 - q) ** GAMMA * -math.log(q) for q in p) / 2
    assert abs(focal_loss(logits, targets, alpha).item() - want) < 1e-6


def test_confusion_counts_and_macro_f1():
    c = confusion(np.array([1, 1, 0, 0, 0]), np.array([1, 0, 1, 0, 0]))
    assert (c["tp"], c["fn"], c["fp"], c["tn"]) == (1, 1, 1, 2)
    assert abs(c["macro_f1"] - (0.5 + 2 / 3) / 2) < 1e-9 and c["sensitivity"] == 0.5


def test_validation_threshold_maximises_f1():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "eval"))
    from bone_loss_v2_eval import best_f1_threshold
    y = np.array([0, 0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.6, 0.55, 0.9])
    # at 0.55: TP 2, FP 1 -> F1 0.8; at 0.9: TP 1, FP 0 -> 2/3; at 0.6: TP 1, FP 1 -> 0.5
    assert best_f1_threshold(y, p) == (0.55, 0.8)


def test_stage4a_default_is_registered_and_the_previous_checkpoint_keeps_its_profile():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import run_inference as ri
    new = "e4bc874423e7c17752bb949d510862e4b4fd618f9a7602a95743663a3c27a0b2"
    old = "c52f7f484076a2a2c3c144c3351912b118b6b0d56fc51ba1b4296e6ce6213db1"
    assert set(ri.BONE_LOSS_PROFILES) == {new, old}
    assert ri.DEF_BONE_LOSS.name == "seed42_best.pth"
    assert ri.BONE_LOSS_PROFILES[new]["tag"] != ri.BONE_LOSS_PROFILES[old]["tag"]
    assert "27.5%" in ri.BONE_LOSS_PROFILES[new]["label_and_validation"]
    assert "7.6%" in ri.BONE_LOSS_PROFILES[old]["label_and_validation"]
    # an unknown checkpoint claims no figure, and every profile says it is not periodontal
    assert "No sensitivity" in ri.UNREGISTERED_BONE_LOSS["label_and_validation"]
    for prof in (*ri.BONE_LOSS_PROFILES.values(), ri.UNREGISTERED_BONE_LOSS):
        assert "not as a periodontal finding" in " ".join(prof["label_and_validation"].split())
        assert set(prof) == {"tag", "label_and_validation", "transfer", "validation_split", "class_order_note"}
