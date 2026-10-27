#!/usr/bin/env python
"""Stage 4a retrained with a radiograph-level split (the frozen split_v1).

Pre-registration: outputs/bone_loss_eval/v2_retrain/PRE_REGISTRATION.md (commits 0993d4a, d8dff27).
The data, the recipe, the three seeds and the forbidden list are fixed there. The label is
"the crop overlaps a Tufts expert ABNORMALITY mask" -- not periodontal bone loss.

Training never reads a test radiograph. `check` does read two (13 and 24, with their labels) among
the twenty whose saved rows it rebuilds to prove the crop builder unchanged; nothing is trained on
them. scripts/eval/bone_loss_v2_eval.py scores the test split, once. (Corrected 14 Oct 2026; this
said the script never reads a test radiograph.)

    python scripts/tufts/train_bone_loss_v2.py check            # H1-H3, before any training
    python scripts/tufts/train_bone_loss_v2.py train --seed 42  # refuses to overwrite a run
"""

import argparse
import copy
import csv
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import torch
from torch import nn

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
from bone_loss_heldout import MIN_DIM, clean_crops, load_sources  # noqa: E402
from src.classifiers import IMAGENET_MEAN, IMAGENET_STD            # noqa: E402

SPLIT = REPO_ROOT / "outputs/eda_tufts/split_v1.csv"
OUT = REPO_ROOT / "models/18_bone_loss_radiograph_split"
HELDOUT_ROWS = REPO_ROOT / "outputs/bone_loss_eval/heldout/heldout_rows.json"
DROP = {"590": "byte-identical to 591 (train)", "1008": "byte-identical to 1007 (train)"}
WANT = {"train": 678, "val": 145, "test": 143}
SEEDS = (42, 43, 44)
# the original recipe (notebooks/bone_loss/03, cells 5, 14, 17, 20)
LR, WEIGHT_DECAY, BATCH, MAX_EPOCHS, PATIENCE = 1e-4, 1e-4, 32, 50, 10
SCHED_FACTOR, SCHED_PATIENCE, GAMMA, NORMALS_PER_DISEASED, JITTER, JITTER_SEED = 0.5, 5, 2.0, 3.5, 0.15, 42


def split_stems():
    """split -> sorted radiograph stems that carry at least one tooth box, twins removed."""
    records, _, _ = load_sources()
    out = {"train": [], "val": [], "test": []}
    for r in csv.DictReader(open(SPLIT)):
        stem = Path(r["filename"]).stem
        if stem not in DROP and records.get(stem):
            out[r["split"].strip()].append(stem)
    return {k: sorted(v, key=lambda s: (len(s), s)) for k, v in out.items()}, records


def notebook_jitter(rng):
    """The notebook's apply_bbox_jitter (02, cell 16): +-15% of the box in position and size."""
    def f(x, y, w, h, img_w, img_h):
        dx, dy = rng.uniform(-JITTER, JITTER) * w, rng.uniform(-JITTER, JITTER) * h
        dw, dh = rng.uniform(-JITTER, JITTER) * w, rng.uniform(-JITTER, JITTER) * h
        nx, ny = max(0, x + dx), max(0, y + dy)
        nw, nh = max(MIN_DIM, w + dw), max(MIN_DIM, h + dh)
        return nx, ny, min(nw, img_w - nx), min(nh, img_h - ny)
    return f


def build(stems, records, with_jitter):
    """-> (uint8 crops [N, 224, 224], labels [N], rows). Clean crops, then one jittered copy of
    every tooth when with_jitter; each crop's label comes from its own overlap."""
    rows, crops = [], []
    rng = random.Random(JITTER_SEED)
    for stem in stems:
        for jitter in ((None, notebook_jitter(rng)) if with_jitter else (None,)):
            for row, crop in clean_crops(stem, records[stem], jitter=jitter):
                rows.append(dict(row, jittered=jitter is not None))
                crops.append(crop)
    return np.stack(crops), np.array([r["label"] for r in rows]), rows


def augment(img, rng):
    """One 224x224 uint8 crop -> float32 in [0, 255]: flip, rotation within 10 degrees,
    brightness x[0.8, 1.2], contrast x[0.9, 1.1] (the original's train_transform)."""
    if rng.random() < 0.5:
        img = img[:, ::-1]
    m = cv2.getRotationMatrix2D((112, 112), rng.uniform(-10, 10), 1.0)
    f = cv2.warpAffine(np.ascontiguousarray(img), m, (224, 224), flags=cv2.INTER_LINEAR).astype(np.float32)
    f *= rng.uniform(0.8, 1.2)
    mean = f.mean()
    return np.clip((f - mean) * rng.uniform(0.9, 1.1) + mean, 0, 255)


def focal_loss(logits, targets, alpha):
    """The notebook's FocalLoss (03, cell 14): alpha_t * (1 - p_t)^gamma * CE, mean."""
    ce = nn.functional.cross_entropy(logits, targets, reduction="none")
    return (alpha[targets] * (1 - torch.exp(-ce)) ** GAMMA * ce).mean()


def to_batch(crops, device, mean, std):
    """float crops [B, 224, 224] in [0, 255] -> normalised [B, 3, 224, 224] on device; the same
    arithmetic as bone_loss_heldout.load_scorer, so training and scoring see one input."""
    x = torch.from_numpy(np.stack(crops)).float().div(255.0).to(device)     # (B, 224, 224)
    return (x.unsqueeze(1).expand(-1, 3, -1, -1) - mean) / std              # (B, 3, 224, 224)


def confusion(y, pred):
    tp, fp = int(((pred == 1) & (y == 1)).sum()), int(((pred == 1) & (y == 0)).sum())
    fn, tn = int(((pred == 0) & (y == 1)).sum()), int(((pred == 0) & (y == 0)).sum())
    f1_pos = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    f1_neg = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "macro_f1": (f1_pos + f1_neg) / 2,
            "f1_diseased": f1_pos, "sensitivity": tp / (tp + fn) if tp + fn else 0.0,
            "specificity": tn / (tn + fp) if tn + fp else 0.0}


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
    model.fc = nn.Linear(model.fc.in_features, 2)
    model = model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="max", factor=SCHED_FACTOR,
                                                       patience=SCHED_PATIENCE)
    pos, neg = np.flatnonzero(ytr == 1), np.flatnonzero(ytr == 0)
    n_neg = min(len(neg), round(NORMALS_PER_DISEASED * len(pos)))
    n = len(pos) + n_neg
    alpha = torch.tensor([n / (2 * n_neg), n / (2 * len(pos))], dtype=torch.float32, device=device)

    best, best_state, stale, history = -1.0, None, 0, []
    for epoch in range(1, max_epochs + 1):
        t0 = time.time()
        idx = rng.permutation(np.concatenate([pos, rng.choice(neg, n_neg, replace=False)]))
        model.train()
        total = 0.0
        for i in range(0, len(idx), BATCH):
            b = idx[i:i + BATCH]
            x = to_batch([augment(xtr[j], rng) for j in b], device, mean, std)
            loss = focal_loss(model(x), torch.from_numpy(ytr[b]).long().to(device), alpha)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            total += loss.item() * len(b)
        val = confusion(yva, predict(model, xva, device, mean, std))
        sched.step(val["macro_f1"])
        history.append({"epoch": epoch, "train_loss": round(total / len(idx), 5),
                        "lr": opt.param_groups[0]["lr"], "seconds": round(time.time() - t0, 1),
                        **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in val.items()}})
        log(f"  epoch {epoch:2d}  loss {total / len(idx):.4f}  val macro-F1 {val['macro_f1']:.4f}  "
            f"sens {val['sensitivity']:.3f}  spec {val['specificity']:.3f}  "
            f"lr {opt.param_groups[0]['lr']:.1e}  {time.time() - t0:.0f}s")
        if val["macro_f1"] > best:
            best, stale = val["macro_f1"], 0
            best_state = copy.deepcopy({k: v.detach().cpu() for k, v in model.state_dict().items()})
        else:
            stale += 1
            if stale >= PATIENCE:
                break
    return best_state, {"device": str(device), "epochs": history, "best_val_macro_f1": round(best, 4),
                        "best_epoch": max(history, key=lambda h: h["macro_f1"])["epoch"],
                        "epoch_crops": {"diseased": int(len(pos)), "normal": int(n_neg)},
                        "alpha": [round(float(a), 4) for a in alpha.cpu()]}


def check():
    stems, records = split_stems()
    counts = {k: len(v) for k, v in stems.items()}
    flat = [s for v in stems.values() for s in v]
    h2 = counts == WANT and len(flat) == len(set(flat)) and not set(DROP) & set(flat)
    print(f"H2 split: {counts}, no radiograph in two splits, 590 and 1008 out -> {'pass' if h2 else 'FAIL'}")

    saved = json.loads(HELDOUT_ROWS.read_text())["rows"]
    twenty = sorted({r["stem"] for r in saved}, key=lambda s: (len(s), s))[:20]
    key = lambda r: (r["stem"], r["tooth"], r["label"], r["overlap"])
    mine = [key(row) for s in twenty for row, _ in clean_crops(s, records[s])]
    theirs = [key(r) for r in saved if r["stem"] in set(twenty)]
    h1 = mine == theirs and len(mine) > 0
    print(f"H1 builder: {len(mine)} rows of 20 radiographs identical to the rows of 13 Oct -> "
          f"{'pass' if h1 else 'FAIL'}")

    h3 = False
    if h1 and h2:
        x, y, _ = build(stems["train"][:3], records, with_jitter=True)
        y = y.copy()
        y[:8] = 1                                   # the loop needs both classes; labels unused
        state, _ = fit(0, x[:64], y[:64], x[:64], y[:64], max_epochs=1, log=lambda s: None)
        h3 = state is not None
        print(f"H3 loop: one epoch on 64 crops ran -> {'pass' if h3 else 'FAIL'} (numbers discarded)")
    return 0 if h1 and h2 and h3 else 1


def train(seed):
    weights, hist = OUT / f"seed{seed}_best.pth", OUT / f"seed{seed}_history.json"
    if seed not in SEEDS:
        raise SystemExit(f"REFUSED: the registered seeds are {SEEDS}")
    if weights.exists() or hist.exists():
        raise SystemExit(f"REFUSED: seed {seed} has been run; a run is not repeated (Sec 9)")
    stems, records = split_stems()
    if {k: len(v) for k, v in stems.items()} != WANT:
        raise SystemExit("the split is not the registered 678 / 145 / 143")
    xtr, ytr, rtr = build(stems["train"], records, with_jitter=True)
    xva, yva, _ = build(stems["val"], records, with_jitter=False)
    print(f"train: {len(stems['train'])} radiographs, {len(ytr)} crops, {int(ytr.sum())} diseased "
          f"(clean + jittered)   val: {len(stems['val'])} radiographs, {len(yva)} clean crops, "
          f"{int(yva.sum())} diseased")

    OUT.mkdir(parents=True, exist_ok=True)
    prior_file = OUT / "tooth_prior.json"         # the image-blind baseline, from clean train crops
    if not prior_file.exists():
        n, k = Counter(), Counter()
        for r in rtr:
            if not r["jittered"]:
                n[r["tooth"]] += 1
                k[r["tooth"]] += r["label"]
        prior_file.write_text(json.dumps({"share_by_tooth": {t: k[t] / n[t] for t in sorted(n)},
                                          "overall_share": sum(k.values()) / sum(n.values()),
                                          "fitted_on_teeth": sum(n.values())}, indent=2) + "\n")

    state, h = fit(seed, xtr, ytr, xva, yva)
    torch.save(state, weights)                    # a bare state_dict, as models/03 ships
    h.update(seed=seed, sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
             pre_registration="outputs/bone_loss_eval/v2_retrain/PRE_REGISTRATION.md",
             torch=torch.__version__, radiographs={k: len(v) for k, v in stems.items() if k != "test"},
             train_crops=int(len(ytr)), train_diseased=int(ytr.sum()),
             val_crops=int(len(yva)), val_diseased=int(yva.sum()),
             recipe={"lr": LR, "weight_decay": WEIGHT_DECAY, "batch": BATCH, "max_epochs": MAX_EPOCHS,
                     "patience": PATIENCE, "gamma": GAMMA, "normals_per_diseased": NORMALS_PER_DISEASED,
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
