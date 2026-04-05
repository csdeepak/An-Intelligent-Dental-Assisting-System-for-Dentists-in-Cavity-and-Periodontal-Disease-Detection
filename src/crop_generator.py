"""
Crop generation for bone loss detection.

Handles:
  - Asymmetric expanded crop (1.5× W, 2.0× H)
  - Bbox jitter for YOLO noise simulation
  - Crop extraction and resize to 224×224
"""

import random
import cv2
import numpy as np


def compute_expanded_bbox(x, y, w, h, img_w, img_h, fw=1.5, fh=2.0):
    """
    Asymmetric expanded bounding box.

    Expansion: 1.5× width, 2.0× height
    WHY: Teeth are ~3× taller than wide (aspect ratio ~0.35).
         Horizontal over-expansion bleeds into adjacent teeth.
         Vertical expansion captures alveolar bone below root.

    Returns: (cx1, cy1, cx2, cy2) clipped to image bounds.
    """
    cx = x + w / 2.0
    cy = y + h / 2.0
    nw = w * fw
    nh = h * fh

    cx1 = max(0, int(cx - nw / 2.0))
    cy1 = max(0, int(cy - nh / 2.0))
    cx2 = min(img_w, int(cx + nw / 2.0))
    cy2 = min(img_h, int(cy + nh / 2.0))

    return cx1, cy1, cx2, cy2


def apply_bbox_jitter(x, y, w, h, img_w, img_h,
                      jitter_frac=0.15, min_dim=3):
    """
    Random ±jitter perturbation to simulate YOLO noise.

    At inference, crops come from YOLO predictions (slightly noisy).
    At training, crops come from ground-truth bboxes (perfect).
    Jitter bridges this gap.
    """
    dx = random.uniform(-jitter_frac, jitter_frac) * w
    dy = random.uniform(-jitter_frac, jitter_frac) * h
    dw = random.uniform(-jitter_frac, jitter_frac) * w
    dh = random.uniform(-jitter_frac, jitter_frac) * h

    new_x = max(0, x + dx)
    new_y = max(0, y + dy)
    new_w = max(min_dim, w + dw)
    new_h = max(min_dim, h + dh)

    if new_x + new_w > img_w:
        new_w = img_w - new_x
    if new_y + new_h > img_h:
        new_h = img_h - new_y

    return new_x, new_y, new_w, new_h


def extract_crop(img, cx1, cy1, cx2, cy2, target_size=(224, 224)):
    """Extract region from image and resize."""
    crop = img[cy1:cy2, cx1:cx2]
    if crop.size == 0:
        return None
    return cv2.resize(crop, target_size, interpolation=cv2.INTER_LINEAR)
