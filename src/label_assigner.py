"""
Label assignment via pixel-overlap ratio.

CRITICAL: This uses pixel-overlap ratio, NOT IoU.

Why not IoU:
  Expert mask blobs are tiny sparse lesion annotations.
  Expanded crop bboxes are large (crown + root + bone).
  IoU = intersection / union ≈ tiny / large ≈ near zero.
  Even true positives get IoU ≈ 0.

Pixel-overlap ratio:
  overlap = (nonzero mask pixels inside crop) / (crop area)
  Threshold: 0.005 – 0.02 (genuine lesions occupy 0.5–2% of crop)

Edge cases handled:
  - One blob spanning two teeth → both get positive label
  - Multiple blobs in one crop → all pixels counted
  - Blob barely clipping edge → low overlap, threshold decides
"""

import numpy as np


def compute_overlap_ratio(mask, cx1, cy1, cx2, cy2):
    """
    Compute pixel-overlap ratio for a single crop region.

    Args:
        mask: Full expert mask (grayscale, HxW)
        cx1, cy1, cx2, cy2: Crop region coordinates

    Returns:
        float: overlap ratio (0.0 to 1.0)
    """
    mask_crop = mask[cy1:cy2, cx1:cx2]

    if mask_crop.size == 0:
        return 0.0

    mask_pixels = np.count_nonzero(mask_crop > 0)
    crop_area = mask_crop.shape[0] * mask_crop.shape[1]

    if crop_area == 0:
        return 0.0

    return mask_pixels / crop_area


def assign_label(overlap, threshold=0.01):
    """
    Assign binary label based on overlap ratio.

    Args:
        overlap: pixel-overlap ratio
        threshold: decision boundary (default 0.01 = 1%)

    Returns:
        int: 1 (diseased) if overlap > threshold, else 0 (normal)
    """
    return 1 if overlap > threshold else 0
