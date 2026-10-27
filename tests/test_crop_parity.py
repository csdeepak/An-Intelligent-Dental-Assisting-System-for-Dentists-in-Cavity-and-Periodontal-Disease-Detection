"""Stage-4a crops: the training path and the serving path must cut the same pixels.

The Tufts test figures for Stage 4a were computed with the training crop function
(`scripts/eval/bone_loss_heldout.clean_crops`, greyscale read, `to_batch`); the pipeline crops with
`src.classifiers.crop_batch` (colour read). Measured 14 Oct 2026 (RESULTS_LOG 2026-10-14) on 20
train-split radiographs: identical boxes and identical decoded pixels. `cv2.resize` rounds 1- and
3-channel input slightly differently: at most 3 grey levels inside the crop, and up to 255 on a
few pixels of the first one or two columns. No flag decision changed (0 of 503 teeth).

This pins the geometry and bounds the interior difference. Two train-split radiographs; no label,
no model. Skipped where the Tufts radiographs are absent (a fresh clone).
"""

import csv
import sys
from pathlib import Path

import cv2
import pytest
import torch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "eval"))
sys.path.insert(0, str(REPO / "scripts" / "tufts"))
from bone_loss_heldout import MIN_DIM, SRC, clean_crops, expanded_box, load_sources  # noqa: E402

pytestmark = pytest.mark.skipif(not (SRC / "Radiographs").is_dir(),
                                reason="Tufts radiographs not on this machine")


def _paths(stem, objects):
    """-> (training-path tensor, serving-path tensor), both de-normalised to grey levels."""
    from src.classifiers import BONE_LOSS_EXPAND, IMAGENET_MEAN, IMAGENET_STD, crop_batch
    from train_bone_loss_v2 import to_batch
    mean = torch.tensor(IMAGENET_MEAN).view(1, 3, 1, 1)
    std = torch.tensor(IMAGENET_STD).view(1, 3, 1, 1)
    img = cv2.imread(str(SRC / "Radiographs" / f"{stem}.JPG"))
    h_img, w_img = img.shape[:2]
    boxes = []
    for obj in objects:                       # the same filters as clean_crops
        box = obj.get("bounding box")
        if box is None or len(box) < 4:
            continue
        y1, x1, y2, x2 = box[:4]              # the field is [y1, x1, y2, x2]
        if x2 - x1 < MIN_DIM or y2 - y1 < MIN_DIM:
            continue
        cx1, cy1, cx2, cy2 = expanded_box(x1, y1, x2 - x1, y2 - y1, w_img, h_img)
        if cx2 - cx1 < MIN_DIM or cy2 - cy1 < MIN_DIM:
            continue
        boxes.append((x1, y1, x2, y2))
    train = to_batch([c for _, c in clean_crops(stem, objects)], "cpu", mean, std)
    serve = crop_batch(img, boxes, BONE_LOSS_EXPAND, "cpu")
    return (train * std + mean) * 255, (serve * std + mean) * 255


def test_expanded_box_is_the_serving_geometry():
    from src.crop_generator import compute_expanded_bbox
    for x, y, w, h in [(609.4, 306.0, 78.2, 154.0), (0.0, 5.5, 40.0, 300.0), (1580.0, 700.0, 30.0, 139.0)]:
        assert expanded_box(x, y, w, h, 1615, 840) == compute_expanded_bbox(x, y, w, h, 1615, 840)


def test_training_and_serving_crops_match_inside_the_crop():
    records, _, _ = load_sources()
    split = list(csv.DictReader(open(REPO / "outputs/eda_tufts/split_v1.csv")))
    stems = [Path(r["filename"]).stem for r in split if r["split"] == "train"]
    stems = [s for s in stems if records.get(s)][:2]
    for stem in stems:
        train, serve = _paths(stem, records[stem])
        assert train.shape == serve.shape
        inner = (train - serve).abs()[..., 2:]           # columns 0-1: cv2's border rounding
        assert float(inner.max()) <= 4, f"{stem}: {float(inner.max()):.1f} grey levels"
        assert float(inner.mean()) < 0.1, f"{stem}: mean {float(inner.mean()):.3f}"
