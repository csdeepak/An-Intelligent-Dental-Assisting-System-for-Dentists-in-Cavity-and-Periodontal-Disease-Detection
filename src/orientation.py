"""
The detector's input-orientation contract.

**The rule: the frozen detector consumes 90 deg COUNTER-CLOCKWISE-rotated panoramics.
Everything else in the pipeline works in the original upright frame.**

Why the detector is the odd one out: Tufts ships its annotations in *portrait* coordinates, so
`Radiographs_rotated/` (840x1615) is what every converter consumed and therefore what
`tooth-detector-a100-1024-v1.0` was trained on -- a sideways panoramic, arch running vertically.

DIRECTION -- established by checking, after getting it wrong once
----------------------------------------------------------------
An earlier version of this module said CLOCKWISE. That was wrong. It had been inferred from a
visual overlay on the pre-existing `Radiographs_rotated/` files without ever checking how those
files were produced. Comparing all 1,000 pairs directly:

    cv2.ROTATE_90_CLOCKWISE  vs Radiographs_rotated : 0 / 1000 consistent (mean|diff| ~70)
    cv2.ROTATE_90_COUNTERCLOCKWISE                  : 1000 / 1000 consistent (mean|diff| 0.49,
                                                      i.e. JPEG re-encode noise)

Orientation matters twice over, and the two are independent:
  1. the detector must see the orientation it was trained on, and
  2. Stage 2 reasons about upright anatomy -- jaws separate vertically, the midline runs
     vertically -- so rotated boxes must never reach it. Feeding rotated boxes to `assign_fdi`
     scored 5.9% quadrant accuracy, worse than the 25% of guessing.

**Rotate for detection, un-rotate immediately.** `detect_upright` does both as one call so the
pair cannot be separated by accident.

Transforms, on a WxH image (result is HxW):

    CCW  forward (x, y) -> (y, W-1-x)        inverse (x, y) -> (W-1-y, x)
    CW   forward (x, y) -> (H-1-y, x)        inverse (x, y) -> (y, H-1-x)

Note CCW's inverse needs the original WIDTH, CW's the original HEIGHT.
"""

import cv2

CCW = "ccw"
CW = "cw"
DEFAULT = CCW          # what the frozen detector was trained on -- verified, see docstring

_CV2 = {CCW: cv2.ROTATE_90_COUNTERCLOCKWISE, CW: cv2.ROTATE_90_CLOCKWISE}


def rotate_for_detector(img, direction=DEFAULT):
    """Upright panoramic -> the orientation the frozen detector expects."""
    return cv2.rotate(img, _CV2[direction])


def rot_point(x, y, orig_w, orig_h, direction=DEFAULT):
    """Upright (x, y) -> rotated frame."""
    if direction == CCW:
        return (y, orig_w - 1 - x)
    return (orig_h - 1 - y, x)


def unrot_point(x, y, orig_w, orig_h, direction=DEFAULT):
    """Rotated-frame (x, y) -> upright frame."""
    if direction == CCW:
        return (orig_w - 1 - y, x)
    return (y, orig_h - 1 - x)


def unrot_box(box, orig_w, orig_h, direction=DEFAULT):
    """
    Rotated-frame (x1, y1, x2, y2) -> upright, corners re-ordered so x1<x2, y1<y2.

    Both corners are mapped then min/max'd: a 90 deg rotation sends the top-left corner to a
    different corner, so reusing the original corner order yields an inverted box.
    """
    x1, y1, x2, y2 = box
    ax, ay = unrot_point(x1, y1, orig_w, orig_h, direction)
    bx, by = unrot_point(x2, y2, orig_w, orig_h, direction)
    return [min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)]


def unrot_boxes(boxes, orig_w, orig_h, direction=DEFAULT):
    return [unrot_box(b, orig_w, orig_h, direction) for b in boxes]


def detect_upright(model, img_upright, direction=DEFAULT, **predict_kwargs):
    """
    Run the frozen detector on an upright panoramic; return boxes in UPRIGHT coordinates.

    The function the pipeline should call: it keeps the rotate/un-rotate pair together, which
    is exactly the failure this module documents. Returns (boxes_upright, confidences).
    """
    h, w = img_upright.shape[:2]
    r = model.predict(rotate_for_detector(img_upright, direction), **predict_kwargs)[0]
    boxes = r.boxes.xyxy.cpu().numpy().tolist()
    confs = r.boxes.conf.cpu().numpy().tolist()
    return unrot_boxes(boxes, w, h, direction), confs
