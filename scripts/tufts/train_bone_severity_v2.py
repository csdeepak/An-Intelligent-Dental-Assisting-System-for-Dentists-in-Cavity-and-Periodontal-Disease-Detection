#!/usr/bin/env python
"""Stage 4b retrained on the label it was meant to have: bands of mask overlap, split by radiograph.

Pre-registration: outputs/bone_loss_eval/v3_severity/PRE_REGISTRATION.md. The data, the bands, the
recipe, the three seeds and the forbidden list are fixed there.

The shipped Stage-4b model (models/04) was trained on bands of crop CONTRAST, a stand-in its
notebook built when the overlap column was missing (RESULTS_LOG 2026-10-13d). This trains the same
architecture on the quantity it was named for: the share of the expanded tooth crop (1.5x W,
2.0x H) that overlaps a Tufts expert ABNORMALITY mask, cut at 0.05 and 0.15, on teeth whose
overlap exceeds 0.01 (the Stage-4a positives). That is an extent band of an abnormality, not a
clinical severity and not periodontal.

Training reads train and validation radiographs only. `check` and `train` never read the test
split; scripts/eval/bone_severity_v2_eval.py scores it, once.

    python scripts/tufts/train_bone_severity_v2.py check            # H1-H3, before any training
    python scripts/tufts/train_bone_severity_v2.py train --seed 42  # refuses to overwrite a run
"""

import argparse
import copy
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "tufts"))
from bone_loss_heldout import OVERLAP_T, clean_crops                                    # noqa: E402
from train_bone_loss_v2 import (BATCH, LR, MAX_EPOCHS, PATIENCE, SCHED_FACTOR,          # noqa: E402
                                SCHED_PATIENCE, WANT, WEIGHT_DECAY, augment, notebook_jitter,
                                split_stems, to_batch)
from src.classifiers import BONE_LOSS_SEVERITY_CLASSES, IMAGENET_MEAN, IMAGENET_STD     # noqa: E402

OUT = REPO_ROOT / "models/19_bone_severity_overlap"
SEEDS = (42, 43, 44)
CUTS = (0.05, 0.15)               # the bands the notebook meant to use (README, models/04 summary)
# The clean positives per band, counted on 14 Oct 2026 before this protocol was written (H1).
REGISTERED_BANDS = {"train": [246, 295, 242], "val": [41, 57, 42]}


def band(overlap):
    """Mask-overlap ratio of a positive crop -> 0, 1, 2 (index order of BONE_LOSS_SEVERITY_CLASSES)."""
    return 0 if overlap <= CUTS[0] else 1 if overlap <= CUTS[1] else 2


def build_positives(stems, records, jitter_seed=None):
    """-> (uint8 crops [N, 224, 224], bands [N], rows) for every crop whose own overlap exceeds
    OVERLAP_T. With jitter_seed, one jittered copy of every tooth as well, drawn from that seed --
    unlike Stage 4a, whose three runs shared one jitter set (RESULTS_LOG 2026-10-14)."""
    rng = random.Random(jitter_seed) if jitter_seed is not None else None
    rows, crops = [], []
    for stem in stems:
        for jitter in ((None, notebook_jitter(rng)) if rng else (None,)):
            for row, crop in clean_crops(stem, records[stem], jitter=jitter):
                if row["overlap"] > OVERLAP_T:
                    rows.append(dict(row, jittered=jitter is not None, band=band(row["overlap"])))
                    crops.append(crop)
    return np.stack(crops), np.array([r["band"] for r in rows]), rows


def macro_f1(y, pred, k=3):
    """Mean of per-class F1 over k classes; a class with no true and no predicted case scores 0."""
    f1 = []
    for c in range(k):
        tp = int(((pred == c) & (y == c)).sum())
        fp, fn = int(((pred == c) & (y != c)).sum()), int(((pred != c) & (y == c)).sum())
        f1.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
    return float(np.mean(f1))


def predict(model, crops, device, mean, std):
    model.eval()
    out = []
    with torch.inference_mode():
        for i in range(0, len(crops), 256):
            out.append(model(to_batch(crops[i:i + 256], device, mean, std)).argmax(1).cpu())
    return torch.cat(out).numpy()


def fit(seed, xtr, ytr, xva, yva, max_epochs=MAX_EPOCHS, log=print):
    """One run of the registered recipe. -> (best state_dict on CPU, history)."""
    from torchvision.models import ResNet18_Weights, resnet18

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    mean = torch.tensor(IMAGENET_MEAN, device=device).view(1, 3, 1, 1)
    std = torch.tensor(IMAGENET_STD, device=device).view(1, 3, 1, 1)

    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, len(BONE_LOSS_SEVERITY_CLASSES))
    model = model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="max", factor=SCHED_FACTOR,
                                                       patience=SCHED_PATIENCE)
    counts = np.maximum(np.bincount(ytr, minlength=3), 1)       # no band is empty in a real run
    weight = torch.tensor(len(ytr) / (3 * counts), dtype=torch.float32, device=device)
    criterion = nn.CrossEntropyLoss(weight=weight)

    best, best_state, stale, history = -1.0, None, 0, []
    for epoch in range(1, max_epochs + 1):
        t0 = time.time()
        idx = rng.permutation(len(ytr))
        model.train()
        total = 0.0
        for i in range(0, len(idx), BATCH):
            b = idx[i:i + BATCH]
            x = to_batch([augment(xtr[j], rng) for j in b], device, mean, std)
            loss = criterion(model(x), torch.from_numpy(ytr[b]).long().to(device))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            total += loss.item() * len(b)
        f1 = macro_f1(yva, predict(model, xva, device, mean, std))
        sched.step(f1)
        history.append({"epoch": epoch, "train_loss": round(total / len(idx), 5), "val_macro_f1": round(f1, 4),
                        "lr": opt.param_groups[0]["lr"], "seconds": round(time.time() - t0, 1)})
        log(f"  epoch {epoch:2d}  loss {total / len(idx):.4f}  val macro-F1 {f1:.4f}  "
            f"lr {opt.param_groups[0]['lr']:.1e}  {time.time() - t0:.0f}s")
        if f1 > best:
            best, stale = f1, 0
            best_state = copy.deepcopy({k: v.detach().cpu() for k, v in model.state_dict().items()})
        else:
            stale += 1
            if stale >= PATIENCE:
                break
    return best_state, {"device": str(device), "epochs": history, "best_val_macro_f1": round(best, 4),
                        "best_epoch": max(history, key=lambda h: h["val_macro_f1"])["epoch"],
                        "class_weight": [round(float(w), 4) for w in weight.cpu()]}


def check():
    stems, records = split_stems()
    counts = {k: len(v) for k, v in stems.items()}
    h1_split = counts == WANT
    got = {}
    for split in ("train", "val"):                     # never the test split
        _, y, _ = build_positives(stems[split], records)
        got[split] = np.bincount(y, minlength=3).tolist()
    h1 = h1_split and got == REGISTERED_BANDS
    print(f"H1 data: split {counts}; clean positives per band {got} "
          f"(registered {REGISTERED_BANDS}) -> {'pass' if h1 else 'FAIL'}")

    edges = [band(x) for x in (0.0101, 0.05, 0.0501, 0.15, 0.1501, 0.9)]
    h2 = edges == [0, 0, 1, 1, 2, 2]
    print(f"H2 bands at the cut points {edges} -> {'pass' if h2 else 'FAIL'}")

    h3 = False
    if h1 and h2:
        x, y, _ = build_positives(stems["train"][:40], records, jitter_seed=0)
        state, _ = fit(0, x[:64], y[:64], x[:64], y[:64], max_epochs=1, log=lambda s: None)
        h3 = state is not None
        print(f"H3 loop: one epoch on 64 crops ran -> {'pass' if h3 else 'FAIL'} (numbers discarded)")
    return 0 if h1 and h2 and h3 else 1


def train(seed):
    weights, hist = OUT / f"seed{seed}_best.pth", OUT / f"seed{seed}_history.json"
    if seed not in SEEDS:
        raise SystemExit(f"REFUSED: the registered seeds are {SEEDS}")
    if weights.exists() or hist.exists():
        raise SystemExit(f"REFUSED: seed {seed} has been run; a run is not repeated")
    stems, records = split_stems()
    if {k: len(v) for k, v in stems.items()} != WANT:
        raise SystemExit("the split is not the registered 678 / 145 / 143")
    xtr, ytr, _ = build_positives(stems["train"], records, jitter_seed=seed)
    xva, yva, _ = build_positives(stems["val"], records)
    print(f"train: {len(ytr)} crops (clean + jittered), per band {np.bincount(ytr, minlength=3).tolist()}   "
          f"val: {len(yva)} clean crops, per band {np.bincount(yva, minlength=3).tolist()}")

    OUT.mkdir(parents=True, exist_ok=True)
    state, h = fit(seed, xtr, ytr, xva, yva)
    torch.save(state, weights)                    # a bare state_dict, as models/04 and 18 ship
    h.update(seed=seed, sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
             pre_registration="outputs/bone_loss_eval/v3_severity/PRE_REGISTRATION.md",
             torch=torch.__version__, classes=list(BONE_LOSS_SEVERITY_CLASSES), cuts=list(CUTS),
             label="share of the 1.5x/2.0x tooth crop overlapping a Tufts expert abnormality mask; "
                   "positives only (overlap > 0.01). An extent band, not a clinical severity.",
             train_crops=int(len(ytr)), train_bands=np.bincount(ytr, minlength=3).tolist(),
             val_crops=int(len(yva)), val_bands=np.bincount(yva, minlength=3).tolist(),
             recipe={"lr": LR, "weight_decay": WEIGHT_DECAY, "batch": BATCH, "max_epochs": MAX_EPOCHS,
                     "patience": PATIENCE, "loss": "class-weighted cross-entropy",
                     "jitter_seed": seed,
                     "scheduler": f"ReduceLROnPlateau(max, {SCHED_FACTOR}, {SCHED_PATIENCE})"})
    hist.write_text(json.dumps(h, indent=2) + "\n")
    print(f"seed {seed}: best validation macro-F1 {h['best_val_macro_f1']} at epoch {h['best_epoch']} "
          f"of {len(h['epochs'])} -> {weights.name}  sha256 {h['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("check", "train"))
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    sys.exit(check() if a.step == "check" else train(a.seed))
