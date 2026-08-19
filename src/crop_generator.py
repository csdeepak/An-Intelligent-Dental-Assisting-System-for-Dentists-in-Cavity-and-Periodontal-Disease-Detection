"""
Crop generation for bone loss detection.

Handles:
  - Asymmetric expanded crop (1.5× W, 2.0× H)
  - Bbox jitter for YOLO noise simulation
  - Crop extraction and resize to 224×224
  - Mask-aware cropping (R2, docs/research/MASTER_PLAN_2026H2.md): soft-attenuates
    neighboring-tooth pixels once instance masks are available (T0.6/R1), while
    preserving the alveolar bone region below the root for the periodontal branch
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


def rasterize_polygon(polygon, shape):
    """
    Fill a polygon into a binary mask.

    polygon: list of (x, y) points in the SAME coordinate space as `shape`
             (e.g. crop-local coordinates, not full-image coordinates).
    shape: (height, width) of the target mask.

    Returns a uint8 array, 1 inside the polygon, 0 outside. Fewer than 3 points
    cannot form a polygon and returns an all-zero mask (caller should fall back
    to a plain rectangular crop in that case, as extract_mask_aware_crop does).
    """
    mask = np.zeros(shape, dtype=np.uint8)
    if len(polygon) < 3:
        return mask
    pts = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(mask, [pts], 1)
    return mask


def extend_mask_below_root(mask):
    """
    Extend a tooth mask downward from its lowest point, within its own column
    span, to the bottom of the array.

    WHY: the periodontal branch reads alveolar bone level below the root, which
         a raw tooth-instance mask does not cover (masks stop at the tooth
         surface). Without this extension, mask-aware attenuation would dim out
         exactly the bone context R2 exists to preserve — see R2 in
         docs/research/MASTER_PLAN_2026H2.md ("soft attenuation, not hard
         masking, so bone context below the root is preserved").
    """
    h, w = mask.shape
    extended = mask.copy()
    cols_with_mask = np.where(mask.any(axis=0))[0]
    if cols_with_mask.size == 0:
        return extended
    col_min, col_max = int(cols_with_mask.min()), int(cols_with_mask.max())
    rows_with_mask = np.where(mask[:, col_min:col_max + 1].any(axis=1))[0]
    if rows_with_mask.size == 0:
        return extended
    lowest_row = int(rows_with_mask.max())
    extended[lowest_row:h, col_min:col_max + 1] = 1
    return extended


def apply_soft_mask_attenuation(crop, mask, attenuation=0.5):
    """
    Dim pixels outside `mask` by `attenuation`, without zeroing them out.

    Soft, not hard: a wrong or noisy mask edge (real risk — see the polygon-noise
    caveat in docs/research/T0.6_detector_reconciliation.md §3) degrades gracefully
    instead of erasing real signal, and neighboring-tooth context that a classifier
    might legitimately use is suppressed rather than deleted.

    crop: HxW or HxWxC array. mask: HxW array, same H/W as crop, 1 = keep full
    strength, 0 = attenuate. attenuation: multiplier applied outside the mask,
    in [0, 1] (0 = hard masking, 1 = no-op).
    """
    if mask.shape != crop.shape[:2]:
        raise ValueError(f"mask shape {mask.shape} does not match crop shape {crop.shape[:2]}")
    weight = mask.astype(np.float32) * (1.0 - attenuation) + attenuation
    if crop.ndim == 3:
        weight = weight[..., None]
    attenuated = crop.astype(np.float32) * weight
    return np.clip(attenuated, 0, 255).astype(crop.dtype)


def extract_mask_aware_crop(img, polygon, cx1, cy1, cx2, cy2,
                             target_size=(224, 224), attenuation=0.5):
    """
    Mask-aware version of extract_crop (R2).

    Suppresses neighboring-tooth pixels via soft attenuation instead of a plain
    rectangular crop, while preserving the target tooth's own footprint and the
    bone region directly below its root (extend_mask_below_root).

    polygon: list of (x, y) points in FULL-IMAGE absolute coordinates — the same
             coordinate space as cx1/cy1/cx2/cy2 (e.g. teeth_polygon.json's
             per-object "polygons" field after picking the largest fragment, see
             convert_tufts_to_yolo_seg.py). Pass an empty list / fewer than 3
             points to fall back to a plain rectangular crop, identical to
             extract_crop — useful when a detection has no usable mask yet.
    """
    crop = img[cy1:cy2, cx1:cx2]
    if crop.size == 0:
        return None

    if len(polygon) < 3:
        return cv2.resize(crop, target_size, interpolation=cv2.INTER_LINEAR)

    local_polygon = [(x - cx1, y - cy1) for x, y in polygon]
    mask = rasterize_polygon(local_polygon, crop.shape[:2])
    mask = extend_mask_below_root(mask)
    attenuated = apply_soft_mask_attenuation(crop, mask, attenuation=attenuation)

    return cv2.resize(attenuated, target_size, interpolation=cv2.INTER_LINEAR)
