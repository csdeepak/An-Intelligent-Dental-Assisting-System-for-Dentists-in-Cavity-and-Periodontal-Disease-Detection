#!/usr/bin/env python
"""Stage 3b (caries vs deep caries) retrained and tested on DENTEX's image-level split.

Pre-registration: outputs/caries_severity_v2/PRE_REGISTRATION.md. The data, the recipe, the three
seeds, the comparators, the rule and the forbidden list are fixed there.

The shipped severity head (models/07) was trained on crops of the 705-image DENTEX training release
and tuned and reported on the 133 crops of the separate 50-image release ("extern50"; RESULTS_LOG
2026-08-21j, models/07_caries_cascade/run_summary.txt). It has no held-out figure, and on the test
split of data/dentex/splits_v2.json it would be scored on its own training images. This trains the
same architecture on splits_v2 train, selects on splits_v2 val, and scores the test split once.

Crops: data/dentex/crops_v2/phase2 (scripts/dentex/build_dentex_crops.py) -- tight annotation boxes,
224x224, the pipeline's caries crop contract (src/classifiers.py). Recipe: Stage 4a/4b's
(scripts/tufts/train_bone_loss_v2.py), with two classes. `check` and `train` never read a test or
extern50 crop; `check` hashes their source radiographs for near-duplicates (H4).

    python scripts/dentex/train_caries_severity_v2.py check            # H1-H5, before any training
    python scripts/dentex/train_caries_severity_v2.py train --seed 42  # refuses to repeat a run
    python scripts/dentex/train_caries_severity_v2.py score            # the one test pass; refuses twice
    python scripts/dentex/train_caries_severity_v2.py report           # recompute from the saved rows
"""

import argparse
import copy
import csv
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import torch
from torch import nn

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "tufts"))
from bone_loss_heldout import N_BOOT, SEED                                              # noqa: E402
from bootstrap_ci import cluster_bootstrap                                              # noqa: E402
from dentex_near_duplicates import DENTEX, hashes                                       # noqa: E402
from train_bone_loss_v2 import (BATCH, LR, MAX_EPOCHS, PATIENCE, SCHED_FACTOR,          # noqa: E402
                                SCHED_PATIENCE, WEIGHT_DECAY, augment, to_batch)
from train_bone_severity_v2 import macro_f1, predict                                   # noqa: E402
from src.classifiers import IMAGENET_MEAN, IMAGENET_STD, load_classifier               # noqa: E402

CROPS = REPO_ROOT / "data/dentex/crops_v2"
MODELS = REPO_ROOT / "models/20_caries_severity_v2"
OUT = REPO_ROOT / "outputs/caries_severity_v2"
PRE_REG = "outputs/caries_severity_v2/PRE_REGISTRATION.md"
CLASSES = ("caries", "deep_caries")      # the index order scripts/run_inference.py asserts
SEEDS = (42, 43, 44)
SHIP = 42                                # the seed fixed in advance as the candidate
# Counted on 24 Nov 2026 before the protocol was written: crops per class, source radiographs.
REGISTERED = {"train": ([1564, 400], 456), "val": ([314, 94], 96),
              "test": ([311, 84], 98), "extern50": ([101, 32], 44)}
OLD = REPO_ROOT / "models/07_caries_cascade/phase2_final_bundle.pth"
OLD_SHA = "aa0a8a7ebf47a8acab0d24a6ecd948542c220196d1c71cbebbf56952beacbc86"
XRAYS = {"705": DENTEX / "training_data/quadrant-enumeration-disease/xrays",
         "extern50": DENTEX / "validation_data/quadrant_enumeration_disease/xrays"}
NEAR = (6, 4)                            # pHash <= 6 or dHash <= 4: dentex_near_duplicates.py's criterion
PRIORS = ("pred_majority", "pred_tooth_majority", "pred_tooth_rate")
ARMS = ("pred_42", "pred_43", "pred_44") + PRIORS


def rows(split):
    """Manifest rows of one Phase-2 split: crop, source radiograph, FDI code, label (0 caries, 1 deep)."""
    return [{"crop": r["crop_name"], "image": r["source_image"],
             "fdi": int(r["quadrant"]) * 10 + int(r["tooth"]), "y": CLASSES.index(r["phase2"])}
            for r in csv.DictReader(open(CROPS / "crops_manifest.csv"))
            if r["split"] == split and r["phase2"]]


def load(split):
    """-> (uint8 grey crops [N, 224, 224], labels [N], rows). Refuses a crop that is not 224x224 grey,
    so taking one channel is exactly the pipeline's BGR->RGB input."""
    rs = rows(split)
    crops = []
    for r in rs:
        im = cv2.imread(str(CROPS / "phase2" / split / CLASSES[r["y"]] / r["crop"]))
        if im is None or im.shape != (224, 224, 3) or not (
                np.array_equal(im[..., 0], im[..., 1]) and np.array_equal(im[..., 1], im[..., 2])):
            raise SystemExit(f"{split}/{r['crop']}: missing, not 224x224, or not grey")
        crops.append(im[..., 0])
    return np.stack(crops), np.array([r["y"] for r in rs]), rs


def counted(rs):
    return np.bincount([r["y"] for r in rs], minlength=2).tolist(), len({r["image"] for r in rs})


def priors(train_rows):
    """The three image-blind arms, fitted on train labels only.
    majority: the commoner class everywhere. tooth majority: the commoner class for that FDI code
    (a tie goes to caries). tooth rate: deep caries where that code's train deep-caries rate exceeds
    the overall train rate -- the class-balanced analogue, as the head's loss is class-weighted.
    A code absent from train gets the majority class."""
    y = np.array([r["y"] for r in train_rows])
    majority, base = int(np.bincount(y, minlength=2).argmax()), float(y.mean())
    by = defaultdict(Counter)
    for r in train_rows:
        by[r["fdi"]][r["y"]] += 1
    tooth_majority = {t: int(c[1] > c[0]) for t, c in by.items()}
    tooth_rate = {t: int(c[1] / (c[0] + c[1]) > base) for t, c in by.items()}
    return majority, tooth_majority, tooth_rate


def metrics(y, p):
    y, p = np.asarray(y), np.asarray(p)
    tp, fp = int(((p == 1) & (y == 1)).sum()), int(((p == 1) & (y == 0)).sum())
    fn, tn = int(((p == 0) & (y == 1)).sum()), int(((p == 0) & (y == 0)).sum())
    return {"macro_f1": macro_f1(y, p, k=2), "accuracy": float((y == p).mean()),
            "deep_recall": tp / (tp + fn) if tp + fn else None,
            "deep_precision": tp / (tp + fp) if tp + fp else None,
            "caries_recall": tn / (tn + fp) if tn + fp else None,
            "confusion_rows_true_cols_pred": [[tn, fp], [fn, tp]]}


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
    model.fc = nn.Linear(model.fc.in_features, len(CLASSES))
    model = model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="max", factor=SCHED_FACTOR,
                                                       patience=SCHED_PATIENCE)
    weight = torch.tensor(len(ytr) / (2 * np.bincount(ytr, minlength=2)), dtype=torch.float32, device=device)
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
        f1 = macro_f1(yva, predict(model, xva, device, mean, std), k=2)
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
    ok = {}
    split_rows = {s: rows(s) for s in REGISTERED}
    got = {s: counted(r) for s, r in split_rows.items()}
    want = {s: (list(c), n) for s, (c, n) in REGISTERED.items()}
    images = {s: {r["image"] for r in r_} for s, r_ in split_rows.items()}
    overlap = {f"{a}&{b}": len(images[a] & images[b])
               for i, a in enumerate(REGISTERED) for b in list(REGISTERED)[i + 1:]}
    on_disk = {s: sorted(p.name for c in CLASSES for p in (CROPS / "phase2" / s / c).glob("*.png"))
               for s in REGISTERED}
    disk_ok = all(on_disk[s] == sorted(r["crop"] for r in split_rows[s]) for s in REGISTERED)
    ok["H1"] = got == want and not any(overlap.values()) and disk_ok
    print(f"H1 data: crops per class, radiographs {got}; image overlap between splits {overlap}; "
          f"disk equals manifest {disk_ok} -> {'pass' if ok['H1'] else 'FAIL'}")

    for s in ("train", "val"):                                  # never a test or extern50 crop
        load(s)
    ok["H2"] = True
    print("H2 crops: every train and val crop is 224x224 with three equal channels -> pass")

    src = {s: [XRAYS["extern50" if s == "extern50" else "705"] / i for i in sorted(images[s])] for s in images}
    h = {s: [hashes(p) for p in ps] for s, ps in src.items()}
    ref = h["train"] + h["val"]
    ref_names = [p.name for p in src["train"] + src["val"]]
    r_ph, r_dh = np.array([x[1] for x in ref]), np.array([x[2] for x in ref])
    near = {}
    for s, pool in (("test", ref), ("extern50", ref), ("val", h["train"])):
        ph, dh = r_ph[:len(pool)], r_dh[:len(pool)]                   # val is checked against train only
        names = ref_names[:len(pool)]
        q = h[s]
        d_ph = (np.array([x[1] for x in q])[:, None, :] != ph[None]).sum(2)
        d_dh = (np.array([x[2] for x in q])[:, None, :] != dh[None]).sum(2)
        md5 = {x[0] for x in pool} & {x[0] for x in q}
        hits = [(src[s][i].name, names[j], int(d_ph[i, j]), int(d_dh[i, j]))
                for i in range(len(q)) for j in range(len(pool)) if d_ph[i, j] <= NEAR[0] or d_dh[i, j] <= NEAR[1]]
        near[s] = {"md5_identical": len(md5), "close_under_both": sum(p <= NEAR[0] and d <= NEAR[1] for *_, p, d in hits),
                   "candidates_for_inspection": hits, "min_phash": int(d_ph.min()), "min_dhash": int(d_dh.min())}
    # A re-encoded or resized copy is close under BOTH hashes (the MD5 copies of 2026-11-02d sit at 0/0);
    # a pair close under one only is a candidate, inspected by eye (pre-registration Sec 3).
    ok["H4"] = all(not v["md5_identical"] and not v["close_under_both"] for v in near.values())
    print(f"H4 near-duplicates of test and extern50 radiographs in train+val, and of val in train "
          f"(candidates: pHash <= {NEAR[0]} or dHash <= {NEAR[1]}): {json.dumps(near)} -> {'pass' if ok['H4'] else 'FAIL'}")

    y = np.array([0, 0, 0, 1, 1, 0])
    m = metrics(y, np.array([0, 0, 1, 1, 0, 0]))
    ok["H3"] = (abs(m["macro_f1"] - (0.75 + 0.5) / 2) < 1e-9 and m["confusion_rows_true_cols_pred"] == [[3, 1], [1, 1]]
                and priors([{"fdi": 16, "y": 1}, {"fdi": 16, "y": 0}, {"fdi": 11, "y": 0}, {"fdi": 11, "y": 0},
                            {"fdi": 36, "y": 1}]) == (0, {16: 0, 11: 0, 36: 1}, {16: 1, 11: 0, 36: 1}))
    print(f"H3 metrics and priors on a hand-worked example -> {'pass' if ok['H3'] else 'FAIL'}")

    if ok["H1"] and ok["H2"]:
        x, yy, rs = load("train")
        keep = np.r_[np.flatnonzero(yy == 0)[:32], np.flatnonzero(yy == 1)[:32]]
        state, _ = fit(0, x[keep], yy[keep], x[keep], yy[keep], max_epochs=1, log=lambda s: None)
        ok["H5"] = state is not None
        print(f"H5 loop: one epoch on 64 train crops ran -> {'pass' if ok['H5'] else 'FAIL'} (numbers discarded)")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "check_summary.json").write_text(json.dumps({"checks": ok, "counts": got, "split_image_overlap": overlap,
                                                        "near_duplicates": near}, indent=2) + "\n")
    return 0 if all(ok.values()) and len(ok) == 5 else 1


def train(seed):
    weights, hist = MODELS / f"seed{seed}_best.pth", MODELS / f"seed{seed}_history.json"
    if seed not in SEEDS:
        raise SystemExit(f"REFUSED: the registered seeds are {SEEDS}")
    if weights.exists() or hist.exists():
        raise SystemExit(f"REFUSED: seed {seed} has been run; a run is not repeated")
    xtr, ytr, rtr = load("train")
    xva, yva, rva = load("val")
    if counted(rtr) != tuple(REGISTERED["train"]) or counted(rva) != tuple(REGISTERED["val"]):
        raise SystemExit("train or val is not the registered split")
    print(f"train {len(ytr)} crops {counted(rtr)}   val {len(yva)} crops {counted(rva)}")

    MODELS.mkdir(parents=True, exist_ok=True)
    state, h = fit(seed, xtr, ytr, xva, yva)
    # The bundle shape models/07 ships, so load_classifier and the pipeline's class check accept it.
    torch.save({"model_state_dict": state, "class_to_idx": {c: i for i, c in enumerate(CLASSES)}}, weights)
    h.update(seed=seed, sha256=hashlib.sha256(weights.read_bytes()).hexdigest(), pre_registration=PRE_REG,
             torch=torch.__version__, classes=list(CLASSES),
             label="DENTEX disease annotation class (Caries / Deep Caries) of a tight annotation-box crop",
             split="data/dentex/splits_v2.json, image level", train_crops=int(len(ytr)),
             train_counts=counted(rtr)[0], val_crops=int(len(yva)), val_counts=counted(rva)[0],
             recipe={"init": "ImageNet ResNet18", "lr": LR, "weight_decay": WEIGHT_DECAY, "batch": BATCH,
                     "max_epochs": MAX_EPOCHS, "patience": PATIENCE, "loss": "class-weighted cross-entropy",
                     "augmentation": "scripts/tufts/train_bone_loss_v2.augment",
                     "scheduler": f"ReduceLROnPlateau(max, {SCHED_FACTOR}, {SCHED_PATIENCE})"})
    hist.write_text(json.dumps(h, indent=2) + "\n")
    print(f"seed {seed}: best validation macro-F1 {h['best_val_macro_f1']} at epoch {h['best_epoch']} "
          f"of {len(h['epochs'])} -> {weights.name}  sha256 {h['sha256'][:12]}")
    return 0


def scorer(weights, sha256):
    """-> f(uint8 grey crops) = argmax class, on CPU, through the same arithmetic as training."""
    if hashlib.sha256(Path(weights).read_bytes()).hexdigest() != sha256:
        raise SystemExit(f"{weights} is not the checkpoint its record names")
    model, c2i = load_classifier(weights, 2, torch.device("cpu"))              # eval mode
    if c2i != {c: i for i, c in enumerate(CLASSES)}:
        raise SystemExit(f"{weights}: class_to_idx {c2i}")
    mean = torch.tensor(IMAGENET_MEAN).view(1, 3, 1, 1)
    std = torch.tensor(IMAGENET_STD).view(1, 3, 1, 1)
    return lambda x: predict(model, x, torch.device("cpu"), mean, std)


def score():
    rows_file = OUT / "test_rows.json"
    if rows_file.exists():
        raise SystemExit(f"REFUSED: {rows_file} exists; the test pass is made once")
    hist = {s: json.loads((MODELS / f"seed{s}_history.json").read_text()) for s in SEEDS}
    majority, tooth_majority, tooth_rate = priors(rows("train"))
    out = []
    for split in ("test", "extern50"):
        x, y, rs = load(split)
        if counted(rs) != tuple(REGISTERED[split]):
            raise SystemExit(f"{split} is not the registered {REGISTERED[split]}")
        preds = {f"pred_{s}": scorer(MODELS / f"seed{s}_best.pth", hist[s]["sha256"])(x) for s in SEEDS}
        if split == "extern50":                    # models/07 trained on the test split's images
            preds["pred_old"] = scorer(OLD, OLD_SHA)(x)
        for i, r in enumerate(rs):
            out.append({**r, "split": split, **{k: int(v[i]) for k, v in preds.items()},
                        "pred_majority": majority, "pred_tooth_majority": tooth_majority.get(r["fdi"], majority),
                        "pred_tooth_rate": tooth_rate.get(r["fdi"], majority)})
    OUT.mkdir(parents=True, exist_ok=True)
    rows_file.write_text(json.dumps({"pre_registration": PRE_REG, "rows": out}) + "\n")
    print(f"{len(out)} rows -> {rows_file.name}")
    return report()


def report():
    all_rows = json.loads((OUT / "test_rows.json").read_text())["rows"]
    res = {"pre_registration": PRE_REG,
           "method": f"radiograph-cluster bootstrap, {N_BOOT} resamples, seed {SEED}, percentile; "
                     "paired differences on the same resamples",
           "label": "DENTEX annotation class of a tight annotation-box crop: caries 0, deep_caries 1"}
    for split in ("test", "extern50"):
        rs = [r for r in all_rows if r["split"] == split]
        by = defaultdict(list)
        for r in rs:
            by[r["image"]].append(r)
        clusters = list(by.values())
        flat = lambda cs: [r for c in cs for r in c]                            # noqa: E731
        f1_of = lambda arm: (lambda cs: macro_f1(np.array([r["y"] for r in flat(cs)]),  # noqa: E731
                                                 np.array([r[arm] for r in flat(cs)]), k=2))
        arms = ARMS + (("pred_old",) if split == "extern50" else ())
        s = {"crops": len(rs), "radiographs": len(clusters),
             "counts": np.bincount([r["y"] for r in rs], minlength=2).tolist(), "arms": {}}
        for arm in arms:
            m = metrics([r["y"] for r in rs], [r[arm] for r in rs])
            _, lo, hi, _ = cluster_bootstrap(clusters, f1_of(arm), N_BOOT, np.random.default_rng(SEED))
            m["macro_f1_ci95"] = [round(lo, 4), round(hi, 4)]
            s["arms"][arm] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}
        for other in PRIORS + (("pred_old",) if split == "extern50" else ()):
            diff = lambda cs, o=other: f1_of(f"pred_{SHIP}")(cs) - f1_of(o)(cs)  # noqa: E731
            pt, lo, hi, _ = cluster_bootstrap(clusters, diff, N_BOOT, np.random.default_rng(SEED))
            s[f"seed{SHIP}_minus_{other[5:]}"] = {"value": round(pt, 4), "ci95": [round(lo, 4), round(hi, 4)],
                                                 "excludes_zero": bool(lo > 0 or hi < 0)}
        res[split] = s
    res["eligible"] = all(res["test"][f"seed{SHIP}_minus_{p[5:]}"]["ci95"][0] > 0 for p in PRIORS)
    (OUT / "test_summary.json").write_text(json.dumps(res, indent=2) + "\n")
    for split in ("test", "extern50"):
        print(f"{split}: {res[split]['crops']} crops on {res[split]['radiographs']} radiographs {res[split]['counts']}")
        for arm, a in res[split]["arms"].items():
            print(f"  {arm:20s} macro-F1 {a['macro_f1']:.4f} {a['macro_f1_ci95']}  acc {a['accuracy']:.4f}  "
                  f"deep P {a['deep_precision']}  deep R {a['deep_recall']}")
        for k, v in res[split].items():
            if k.startswith(f"seed{SHIP}_minus_"):
                print(f"  {k}: {v}")
    print(f"eligible: {res['eligible']}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("check", "train", "score", "report"))
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    sys.exit(train(a.seed) if a.step == "train" else {"check": check, "score": score, "report": report}[a.step]())
