"""
The T0.1-T0.4 re-run block for the DENTEX caries cascade.

Replaces the ad-hoc training in notebooks/caries/phase-1.ipynb, which is kept as the
historical record of how the currently-reported numbers were produced. That notebook has four
documented methodological defects (docs/research/PUBLICATION_TODO.md Tier 0); this script
fixes all four in one runnable artifact so a single GPU session closes the block.

  T0.1  Augmentation was defined in the notebook but never applied. This script runs BOTH
        arms -- Arm A (no augmentation, the historical recipe) and Arm B (augmentation) --
        and reports them side by side. The ablation was written into the notebook on
        2026-08-15 and never executed; the Kaggle output directory contains no
        best_phase2_augmented*.pth, confirming it.
  T0.2  The test split is reported SEPARATELY from val, and is touched exactly once, after
        the checkpoint has already been selected on val. Splits come from
        data/dentex/splits_v2.json via the crop tree built by build_dentex_crops.py --
        an image-level split, so no crop of a source image can straddle two splits.
  T0.3  Checkpoint selection is on macro-F1, never raw accuracy. Accuracy rewards the
        majority class on a 3.6:1 problem.
  T0.4  Cosine LR schedule replaces the notebook's hand-dropped 1e-3 -> 3e-5, and the full
        training configuration is written into the results JSON rather than living only in
        cell outputs.

Also closes PAPER_MATERIAL.md section 9's first blocking item: the Phase-1 gate
classification report is SAVED to disk. In the notebook that cell was executed without its
output being retained, so the cascade's end-to-end error has never been recorded.

WHAT THIS SCRIPT DELIBERATELY DOES NOT DO
-----------------------------------------
It does not attempt to fix the Phase-1 negative class. `no_caries` in DENTEX's disease subset
is Impacted + Periapical Lesion and contains NO HEALTHY TEETH, so the gate is really
"caries/deep-caries vs other-pathology" while the assembled pipeline would feed it every tooth
the detector finds. That defect is real, has no fix inside DENTEX's labelled data (the
enumeration subset covers disjoint patients -- see RESULTS_LOG 2026-08-21m), and must be
reported as a limitation. Numbers produced here inherit it.

RECIPE
------
Phase 1 (gate, caries vs no_caries): ImageNet-pretrained ResNet18, fc -> 2, all layers
trainable, Adam, cosine schedule, class weights computed from the ACTUAL training split
rather than hardcoded.

Phase 2 (severity, caries vs deep_caries): initialised from the selected Phase-1 backbone
with a fresh fc head, then two stages -- (1) backbone frozen, head only; (2) full fine-tune at
a lower LR. Each stage cosine-scheduled and macro-F1 selected. This mirrors the notebook's
freeze-then-unfreeze transfer structure, but with scheduling and honest selection.

Class weights use the standard n_total / (n_classes * n_class) form, which reproduces the
notebook's Phase-1 weights to 3 decimal places on the original split -- so the change here is
the split, not the weighting scheme.

Usage:
    python scripts/dentex/train_caries_cascade.py --arm a
    python scripts/dentex/train_caries_cascade.py --arm b
    python scripts/dentex/train_caries_cascade.py --arm a --smoke   # 1 epoch, tiny subset
"""

import argparse
import json
import random
from datetime import datetime
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEF_CROPS = REPO_ROOT / "data/dentex/crops_v2"
DEF_OUT = REPO_ROOT / "outputs/caries_rerun"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
IMG_SIZE = 224


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def build_transforms(augment: bool):
    """Arm B augmentation is exactly the notebook's unused `transform_train` (cell 107)."""
    from torchvision import transforms
    norm = [transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)]
    eval_tf = transforms.Compose([transforms.Resize((IMG_SIZE, IMG_SIZE))] + norm)
    if not augment:
        return eval_tf, eval_tf
    train_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomRotation(10),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
    ] + norm)
    return train_tf, eval_tf


def load_splits(crops_root: Path, variant: str, train_tf, eval_tf, batch_size, smoke=False):
    from torch.utils.data import DataLoader, Subset
    from torchvision import datasets

    base = crops_root / variant
    out = {}
    class_to_idx = None
    for split in ("train", "val", "test", "extern50"):
        d = base / split
        if not d.exists():
            continue
        tf = train_tf if split == "train" else eval_tf
        ds = datasets.ImageFolder(str(d), transform=tf)
        if class_to_idx is None:
            class_to_idx = ds.class_to_idx
        else:
            assert ds.class_to_idx == class_to_idx, (
                f"class_to_idx differs between splits: {ds.class_to_idx} vs {class_to_idx}. "
                "A split is missing a class directory; refusing to train on inconsistent labels."
            )
        if smoke:
            # stratified: take up to 32 per class, so every class is present in every split.
            # A strided sample would follow ImageFolder's class-sorted order and could
            # produce single-class splits, which is not what we want to be testing.
            per_class = {}
            for i, (_, y) in enumerate(ds.samples):
                per_class.setdefault(y, []).append(i)
            keep = [i for ys in per_class.values() for i in ys[:32]]
            ds = Subset(ds, sorted(keep))
        out[split] = DataLoader(ds, batch_size=batch_size, shuffle=(split == "train"),
                                num_workers=0)
    assert "train" in out and "val" in out, f"need train/ and val/ under {base}"
    return out, class_to_idx


def class_weights_from_loader(loader, n_classes):
    """n_total / (n_classes * n_class) — the notebook's scheme, computed from this split."""
    import torch
    ds = loader.dataset
    targets = [s[1] for s in (ds.dataset.samples if hasattr(ds, "dataset") else ds.samples)] \
        if not hasattr(ds, "indices") else [ds.dataset.samples[i][1] for i in ds.indices]
    counts = np.bincount(np.array(targets), minlength=n_classes).astype(float)
    assert (counts > 0).all(), f"a class has zero training samples: {counts}"
    w = counts.sum() / (n_classes * counts)
    return torch.tensor(w, dtype=torch.float32), counts.astype(int).tolist()


def evaluate(model, loader, device, class_names):
    """Returns the full metric set. No thresholds tuned here — argmax only."""
    import torch
    from sklearn.metrics import (classification_report, confusion_matrix, f1_score)
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for x, y in loader:
            out = model(x.to(device))
            preds.extend(out.argmax(1).cpu().numpy().tolist())
            labels.extend(y.numpy().tolist())
    # `labels=` is REQUIRED, not defensive: without it sklearn infers the label set from
    # whatever appears in y_true/y_pred, so a split (or a model that never predicts a class)
    # silently yields a differently-shaped confusion matrix and a report missing a row. That
    # would make results.json inconsistent across runs rather than merely crash.
    idx = list(range(len(class_names)))
    return {
        "macro_f1": float(f1_score(labels, preds, average="macro", labels=idx, zero_division=0)),
        "accuracy": float(np.mean(np.array(preds) == np.array(labels))),
        "confusion_matrix": confusion_matrix(labels, preds, labels=idx).tolist(),
        "report": classification_report(labels, preds, labels=idx, target_names=class_names,
                                        zero_division=0, output_dict=True),
        "report_text": classification_report(labels, preds, labels=idx,
                                             target_names=class_names, zero_division=0),
        "n": len(labels),
        "predicted_class_counts": np.bincount(np.array(preds), minlength=len(class_names)).tolist(),
        "true_class_counts": np.bincount(np.array(labels), minlength=len(class_names)).tolist(),
    }


def train_stage(model, loaders, device, class_names, weights, epochs, lr, params,
                stage_name, log):
    """One cosine-scheduled stage. Selects on val macro-F1 (T0.3). Returns best state_dict."""
    import copy
    import torch
    import torch.nn as nn

    criterion = nn.CrossEntropyLoss(weight=weights.to(device))
    optimizer = torch.optim.Adam(params, lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs))

    best_f1, best_state, best_epoch = -1.0, None, -1
    for ep in range(epochs):
        model.train()
        for x, y in loaders["train"]:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
        scheduler.step()
        val = evaluate(model, loaders["val"], device, class_names)
        log.append({"stage": stage_name, "epoch": ep + 1,
                    "lr": scheduler.get_last_lr()[0],
                    "val_macro_f1": val["macro_f1"], "val_accuracy": val["accuracy"]})
        print(f"  [{stage_name}] epoch {ep+1}/{epochs}  "
              f"val macro-F1 {val['macro_f1']:.4f}  acc {val['accuracy']:.4f}")
        if val["macro_f1"] > best_f1:
            best_f1, best_epoch = val["macro_f1"], ep + 1
            best_state = copy.deepcopy(model.state_dict())
            print(f"     ^ best so far (macro-F1)")
    return best_state, best_f1, best_epoch


def build_model(n_classes, device, init_state=None, pretrained=True):
    import torch.nn as nn
    from torchvision.models import ResNet18_Weights, resnet18
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1 if pretrained else None)
    model.fc = nn.Linear(model.fc.in_features, n_classes)
    if init_state is not None:
        # load the transferred backbone, then discard its head
        missing = model.load_state_dict(init_state, strict=False)
        model.fc = nn.Linear(model.fc.in_features, n_classes)
        print(f"  transferred backbone (unexpected keys: {len(missing.unexpected_keys)})")
    return model.to(device)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", type=Path, default=DEF_CROPS)
    ap.add_argument("--variant", default="phase1_legacy",
                    help="Phase-1 crop tree. phase1_legacy = the historical rule, whose "
                         "no_caries class is Impacted+Periapical and contains NO healthy "
                         "teeth. crops_v3_phase1 = the repaired gate set with 5,366 real "
                         "healthy teeth (RESULTS_LOG 2026-08-25a).")
    # Phase 1 and Phase 2 no longer necessarily live under the same root: the repaired Phase-1
    # tree is built from the enumeration<->disease MD5 join, while Phase 2 still comes from the
    # disease subset alone. Defaults preserve the original single-root behaviour exactly.
    ap.add_argument("--phase2-crops", type=Path, default=None,
                    help="root for the Phase-2 tree (default: --crops)")
    ap.add_argument("--phase2-variant", default="phase2")
    ap.add_argument("--phase1-only", action="store_true",
                    help="train and evaluate the gate alone; skip the severity head")
    ap.add_argument("--arm", choices=["a", "b"], required=True,
                    help="a = no augmentation (historical recipe); b = augmented (T0.1)")
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--p1-epochs", type=int, default=15)
    ap.add_argument("--p1-lr", type=float, default=1e-3)
    ap.add_argument("--p2-head-epochs", type=int, default=5)
    ap.add_argument("--p2-head-lr", type=float, default=1e-3)
    ap.add_argument("--p2-full-epochs", type=int, default=12)
    ap.add_argument("--p2-full-lr", type=float, default=3e-5)
    ap.add_argument("--smoke", action="store_true",
                    help="1 epoch per stage on <=64 images per split — verifies the code path")
    args = ap.parse_args()

    import torch

    if args.smoke:
        args.p1_epochs = args.p2_head_epochs = args.p2_full_epochs = 1

    set_seed(args.seed)
    # MPS included, matching train_enumeration_head.py / run_inference.py /
    # validate_fdi_assignment.py. This script was the only one that fell straight to CPU,
    # so on Apple silicon it silently trained several times slower than necessary.
    device = torch.device("cuda" if torch.cuda.is_available()
                          else "mps" if torch.backends.mps.is_available() else "cpu")
    run = f"arm_{args.arm}" + ("_smoke" if args.smoke else "")
    outdir = args.out / run
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"device={device}  arm={args.arm}  out={outdir}")

    augment = args.arm == "b"
    train_tf, eval_tf = build_transforms(augment)
    log = []
    results = {
        "run": run, "created": datetime.now().isoformat(timespec="seconds"),
        "arm": args.arm, "augmentation": augment, "seed": args.seed, "device": str(device),
        "smoke": args.smoke,
        "config": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "fixes": {"T0.1": "both arms run", "T0.2": "test reported separately, evaluated once",
                  "T0.3": "checkpoint selection on macro-F1",
                  "T0.4": "cosine LR schedule; full config recorded"},
        "known_limitation": "Phase-1 no_caries = Impacted + Periapical Lesion; contains NO "
                            "healthy teeth. See RESULTS_LOG 2026-08-21j / 21m.",
    }

    # ---------------- Phase 1 ----------------
    print("\n=== PHASE 1: caries vs no_caries (gate) ===")
    l1, c2i1 = load_splits(args.crops, args.variant, train_tf, eval_tf, args.batch_size, args.smoke)
    names1 = [k for k, _ in sorted(c2i1.items(), key=lambda kv: kv[1])]
    w1, counts1 = class_weights_from_loader(l1["train"], len(names1))
    print(f"  classes {c2i1}  train counts {counts1}  weights {[round(x,4) for x in w1.tolist()]}")
    m1 = build_model(len(names1), device)
    best1, f1_1, ep1 = train_stage(m1, l1, device, names1, w1, args.p1_epochs, args.p1_lr,
                                   m1.parameters(), "phase1", log)
    m1.load_state_dict(best1)
    results["phase1"] = {"class_to_idx": c2i1, "train_counts": counts1,
                         "class_weights": w1.tolist(),
                         "best_epoch": ep1, "best_val_macro_f1": f1_1,
                         "val": evaluate(m1, l1["val"], device, names1)}
    # T0.2: test touched once, after selection
    for extra in ("test", "extern50"):
        if extra in l1:
            results["phase1"][extra] = evaluate(m1, l1[extra], device, names1)
    torch.save({"model_state_dict": best1, "class_to_idx": c2i1}, outdir / "phase1_best.pth")
    # section 9 blocking item: the gate report is saved, not just printed
    (outdir / "phase1_gate_report.txt").write_text(
        f"PHASE 1 GATE — {run}\nval:\n{results['phase1']['val']['report_text']}\n"
        + "".join(f"{k}:\n{results['phase1'][k]['report_text']}\n"
                  for k in ("test", "extern50") if k in results["phase1"]))

    # ---------------- Phase 2 ----------------
    if args.phase1_only:
        (outdir / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(f"\n--phase1-only: wrote {outdir}/results.json and phase1_gate_report.txt")
        return
    print("\n=== PHASE 2: caries vs deep_caries (severity) ===")
    l2, c2i2 = load_splits(args.phase2_crops or args.crops, args.phase2_variant,
                           train_tf, eval_tf, args.batch_size, args.smoke)
    names2 = [k for k, _ in sorted(c2i2.items(), key=lambda kv: kv[1])]
    w2, counts2 = class_weights_from_loader(l2["train"], len(names2))
    print(f"  classes {c2i2}  train counts {counts2}  weights {[round(x,4) for x in w2.tolist()]}")
    m2 = build_model(len(names2), device, init_state=best1)

    for p in m2.parameters():
        p.requires_grad = False
    for p in m2.fc.parameters():
        p.requires_grad = True
    head_state, _, _ = train_stage(m2, l2, device, names2, w2, args.p2_head_epochs,
                                   args.p2_head_lr, m2.fc.parameters(), "phase2_head", log)
    m2.load_state_dict(head_state)
    for p in m2.parameters():
        p.requires_grad = True
    best2, f1_2, ep2 = train_stage(m2, l2, device, names2, w2, args.p2_full_epochs,
                                   args.p2_full_lr, m2.parameters(), "phase2_full", log)
    m2.load_state_dict(best2)
    results["phase2"] = {"class_to_idx": c2i2, "train_counts": counts2,
                         "class_weights": w2.tolist(),
                         "best_epoch": ep2, "best_val_macro_f1": f1_2,
                         "val": evaluate(m2, l2["val"], device, names2)}
    for extra in ("test", "extern50"):
        if extra in l2:
            results["phase2"][extra] = evaluate(m2, l2[extra], device, names2)
    torch.save({"model_state_dict": best2, "class_to_idx": c2i2}, outdir / "phase2_best.pth")
    (outdir / "phase2_report.txt").write_text(
        f"PHASE 2 SEVERITY — {run}\nval:\n{results['phase2']['val']['report_text']}\n"
        + "".join(f"{k}:\n{results['phase2'][k]['report_text']}\n"
                  for k in ("test", "extern50") if k in results["phase2"]))

    results["epoch_log"] = log
    (outdir / "results.json").write_text(json.dumps(results, indent=2) + "\n")

    print("\n" + "=" * 68)
    for ph in ("phase1", "phase2"):
        r = results[ph]
        line = f"{ph}: val macro-F1 {r['val']['macro_f1']:.4f} (n={r['val']['n']})"
        for k in ("test", "extern50"):
            if k in r:
                line += f" | {k} macro-F1 {r[k]['macro_f1']:.4f} (n={r[k]['n']})"
        print(line)
    print("=" * 68)
    print(f"\nWrote {outdir}/results.json, phase1_gate_report.txt, phase2_report.txt, *.pth")
    print("Run the other arm, then report BOTH side by side — the delta is the T0.1 result.")


if __name__ == "__main__":
    main()
