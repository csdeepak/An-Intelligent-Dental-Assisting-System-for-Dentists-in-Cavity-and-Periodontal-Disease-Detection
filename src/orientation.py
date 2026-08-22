"""
The detector's input-orientation contract.

**The rule: the frozen detector consumes 90 deg CLOCKWISE-rotated panoramics. Everything else
in the pipeline works in the original upright frame.**

Why the detector is the odd one out: Tufts ships its annotations in *portrait* coordinates, so
`Radiographs_rotated/` (840x1615) is what every converter consumed and therefore what
`tooth-detector-a100-1024-v1.0` was trained on — a sideways panoramic, arch running vertically.
Measured consequence on a DENTEX image shipped upright (RESULTS_LOG 2026-08-22b):

    upright, as shipped : 3 detections, and they sit in the nasal region
    rotated 90 deg CW   : 35 detections, on the arches

DENTEX, Ningxia and the clinic data are all shipped upright, so every one of them must be
rotated before inference and the boxes rotated back afterwards.

**Rotate for detection, un-rotate immediately.** Do not let rotated coordinates leak
downstream. Stage 2 assigns FDI codes by anatomy — jaws separate vertically, the midline runs
vertically — and in a rotated frame those axes are swapped. Feeding rotated boxes to
`assign_fdi` silently produces near-random quadrants: measured at 5.9% quadrant accuracy,
*worse than the 25% of guessing*, which is how this contract came to be written down.

Transform, for cv2.ROTATE_90_CLOCKWISE on a WxH image (result is HxW):

    forward   (x, y) -> (H-1-y, x)
    inverse   (x, y) -> (y, H-1-x)

Verified three ways before use: algebraically on all four corners; against cv2 on 4,000 random
pixels with zero mismatches; and by a rasterise-then-rotate vs rotate-then-rasterise mask
round-trip agreeing at IoU 0.99994.
"""

import cv2

ROT = cv2.ROTATE_90_CLOCKWISE


def rotate_for_detector(img):
    """Upright panoramic -> the orientation the frozen detector expects."""
    return cv2.rotate(img, ROT)


def rot_point(x, y, orig_h):
    """Upright (x, y) -> rotated frame. `orig_h` is the UPRIGHT image height."""
    return (orig_h - 1 - y, x)


def unrot_point(x, y, orig_h):
    """Rotated-frame (x, y) -> upright frame. `orig_h` is the UPRIGHT image height."""
    return (y, orig_h - 1 - x)


def unrot_box(box, orig_h):
    """
    Rotated-frame (x1, y1, x2, y2) -> upright frame, corners re-ordered so x1<x2, y1<y2.

    Both corners are mapped and then min/max'd: the rotation maps the top-left corner to the
    bottom-left, so naively reusing the corner order yields an inverted box.
    """
    x1, y1, x2, y2 = box
    ax, ay = unrot_point(x1, y1, orig_h)
    bx, by = unrot_point(x2, y2, orig_h)
    return [min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)]


def unrot_boxes(boxes, orig_h):
    return [unrot_box(b, orig_h) for b in boxes]


def detect_upright(model, img_upright, **predict_kwargs):
    """
    Run the frozen detector on an upright panoramic and return boxes in UPRIGHT coordinates.

    This is the function the pipeline should call. It exists so the rotate/un-rotate pair
    cannot be separated by accident — which is precisely the failure this module documents.
    Returns (boxes_upright, confidences).
    """
    orig_h = img_upright.shape[0]
    r = model.predict(rotate_for_detector(img_upright), **predict_kwargs)[0]
    boxes = r.boxes.xyxy.cpu().numpy().tolist()
    confs = r.boxes.conf.cpu().numpy().tolist()
    return unrot_boxes(boxes, orig_h), confs
