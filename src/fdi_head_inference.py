"""
Inference wrapper for the learned Stage-2 enumeration head.

Mirrors, exactly, the preprocessing used to build the training crops
(`scripts/dentex/build_enumeration_crops.py`) and to load them
(`scripts/dentex/train_enumeration_head.py::ToothSet`, eval branch). Any drift between the
two silently degrades accuracy without raising anything, so the contract is stated here and
the constants are defined once:

  * crop  = 1.5x expanded detector box, clipped to the image, resized to 224x224
  * colour = RGB. `cv2.imread` returns BGR, and the training crops were written by cv2 and
    then read back by PIL as RGB, so an explicit BGR->RGB conversion is required here.
    (On this data the channels happen to be identical — these are greyscale radiographs
    stored as 3-channel — so the conversion is currently a no-op. It is done anyway, because
    relying on that would make the code quietly wrong for any future colour input.)
  * features = [cx, cy, bw, bh], each normalised by the FULL image dimensions, not the crop's

ONE-TO-ONE ASSIGNMENT
---------------------
Rank-order assignment cannot emit a duplicate FDI code — the construction forbids it. An
independent per-tooth classifier can, and will: two adjacent molars can both look most like
tooth 17. A mouth has at most one tooth per code, so treating this as a linear assignment
problem is the faithful model: maximise the total joint log-probability over a one-to-one
matching of detections to codes (Hungarian algorithm). `--no-one-to-one` falls back to plain
argmax, which is what makes the duplicate rate measurable rather than assumed.
"""

import sys
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.crop_generator import compute_expanded_bbox  # noqa: E402

CROP = 224
EXPAND = 1.5
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
FDI_CODES = [(q + 1) * 10 + (p + 1) for q in range(4) for p in range(8)]


def load_head(weights, device):
    """Rebuild the architecture and load the trained weights."""
    import torch
    import torch.nn as nn
    from torchvision.models import resnet18

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.backbone = resnet18(weights=None)
            feat = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
            self.pos = nn.Sequential(nn.Linear(4, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
            self.quadrant = nn.Linear(feat + 64, 4)
            self.position = nn.Linear(feat + 64, 8)

        def forward(self, img, feats):
            z = torch.cat([self.backbone(img), self.pos(feats)], dim=1)
            return self.quadrant(z), self.position(z)

    ck = torch.load(weights, map_location="cpu", weights_only=False)
    net = Net()
    net.load_state_dict(ck["model_state_dict"])
    return net.to(device).eval()


def _batch(img_bgr, boxes):
    """Crops + positional features for every box, in the training preprocessing."""
    import torch
    from torchvision import transforms
    tf = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    H, W = img_bgr.shape[:2]
    crops, feats = [], []
    for b in boxes:
        x1, y1, x2, y2 = b
        x, y, w, h = x1, y1, x2 - x1, y2 - y1
        cx1, cy1, cx2, cy2 = compute_expanded_bbox(x, y, w, h, W, H, fw=EXPAND, fh=EXPAND)
        cx1, cy1, cx2, cy2 = int(cx1), int(cy1), int(cx2), int(cy2)
        cx2, cy2 = max(cx2, cx1 + 1), max(cy2, cy1 + 1)
        patch = img_bgr[cy1:cy2, cx1:cx2]
        if patch.size == 0:
            patch = np.zeros((CROP, CROP, 3), np.uint8)
        patch = cv2.resize(patch, (CROP, CROP))
        patch = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)      # see module docstring
        crops.append(tf(patch))
        feats.append([(x + w / 2) / W, (y + h / 2) / H, w / W, h / H])
    return torch.stack(crops), torch.tensor(feats, dtype=torch.float32)


def assign_fdi_head(model, img_bgr, boxes, device, one_to_one=True):
    """
    Returns a list aligned with `boxes`:
        {index, fdi, quadrant, position, confidence, flags}

    `confidence` is exp() of the joint quadrant+position log-probability of the chosen code,
    so it is comparable across teeth and usable by Stage-5 filtering.
    """
    import torch
    if len(boxes) == 0:
        return []
    imgs, feats = _batch(img_bgr, boxes)
    with torch.no_grad():
        oq, op = model(imgs.to(device), feats.to(device))
        lq = torch.log_softmax(oq, dim=1)          # (N,4)
        lp = torch.log_softmax(op, dim=1)          # (N,8)
        # joint log-prob of every (quadrant, position) pair -> (N,32), column order FDI_CODES
        joint = (lq.unsqueeze(2) + lp.unsqueeze(1)).reshape(len(boxes), 32).cpu().numpy()

    if one_to_one and len(boxes) > 0:
        from scipy.optimize import linear_sum_assignment
        rows, cols = linear_sum_assignment(-joint)     # maximise total joint log-prob
        chosen = dict(zip(rows.tolist(), cols.tolist()))
    else:
        chosen = {i: int(joint[i].argmax()) for i in range(len(boxes))}

    out = []
    for i in range(len(boxes)):
        k = chosen.get(i)
        if k is None:                       # more detections than the 32 available codes
            out.append({"index": i, "fdi": None, "quadrant": None, "position": None,
                        "confidence": 0.0, "flags": ["unassigned_no_code_left"]})
            continue
        fdi = FDI_CODES[k]
        conf = float(np.exp(joint[i, k]))
        flags = []
        if conf < 0.30:
            flags.append("low_confidence")
        if one_to_one and int(joint[i].argmax()) != k:
            # the one-to-one constraint overrode this tooth's own best guess
            flags.append("reassigned_by_one_to_one")
        out.append({"index": i, "fdi": fdi, "quadrant": fdi // 10, "position": fdi % 10,
                    "confidence": round(conf, 4), "flags": flags})
    return out
