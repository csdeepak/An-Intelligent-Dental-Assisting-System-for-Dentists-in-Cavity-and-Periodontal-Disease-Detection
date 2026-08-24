"""
Stage-2 replacement: a learned per-tooth FDI enumeration head.

WHY A LEARNED HEAD, AND WHY IT IS THE ONLY REMAINING OPTION
-----------------------------------------------------------
Rank-order positional assignment scores **22.9% end-to-end exact FDI** on the clean
164-image set (936 teeth), and has a measured ceiling of **66.3%** even where a quadrant is
fully detected (RESULTS_LOG 2026-08-22j and 2026-08-24a; earlier 28.0%/68.7% figures were
measured on an evaluation set that turned out to be 34% leaked). The ceiling exists because eight detected teeth are not
positions 1-8 — they are eight teeth that survived extraction. Improving detector recall
cannot cross it. A per-tooth classifier makes no contiguity assumption at all: it judges each
tooth on its own evidence.

ARCHITECTURE — and the one non-obvious part
-------------------------------------------
ResNet18 backbone over a 1.5x-expanded tooth crop, **concatenated with four positional
features** (normalised centre x/y and box width/height), then two heads: quadrant (4-way) and
position (8-way). FDI = quadrant * 10 + position.

The positional features are a real but **modest** refinement — measured, not assumed
(`scripts/eval/ablate_head_inputs.py`, RESULTS_LOG 2026-08-24c). Replacing them with their
dataset mean costs only **3.2 points of laterality** (side 99.5% -> 96.3%) and 2.8 points of
FDI exact, and costs the position digit **nothing at all** (92.1% either way).

**An earlier version of this docstring claimed laterality was "simply not recoverable from
crop pixels" and that a pure image classifier "would be guessing on half the label". That is
false.** With neutral positional input the image alone recovers side at **96.3%**, not the 50%
of guessing: a 1.5x-expanded crop carries its neighbours and the local arch curvature, and
mirrored teeth sit in mirrored contexts. Keep the features — +3.2 points is worth having — but
do not build an argument on them.

**What the image is genuinely load-bearing for is the position digit**, which collapses without
it, and that is exactly where rank-order geometry fails.

**Sensitivity, and why it does NOT matter in practice** (RESULTS_LOG 2026-08-24e):
feeding *shuffled* positional features -- another tooth's -- costs 22.9 points of laterality.
That looks alarming and is misleading. A shuffle teleports the coordinate to a different tooth,
often across the midline, which is what flips laterality. **Real detector-box error is a small
LOCAL jitter and costs essentially nothing**: perturbing the centre by +/-15% of box size (the
training jitter magnitude) leaves side, position and FDI exact *unchanged* to 0.1pp, and even
+/-100% of box size costs only 0.2pp of side accuracy. A tooth is ~4.5% of image width, so a
whole-box displacement moves cx by <=0.045 while the median tooth sits 0.091 from the midline.
**Do not cite the shuffle number as a train/inference gap** -- an earlier version of this
docstring did.

Two heads rather than one 32-way softmax because the sub-problems have different difficulty
and different failure modes, and reporting them separately is what makes the result
diagnostic: it shows whether a wrong FDI came from the wrong side of the mouth or the wrong
tooth along the arch.

EVALUATION DISCIPLINE
---------------------
Train/val come from DENTEX `quadrant_enumeration` (634 images, split BY IMAGE). The **test set
is `DENTEX/disease/`**, evaluated separately by `scripts/eval/validate_fdi_assignment.py`.
**It is NOT disjoint from the training images**: 85 of its 250 are byte-identical to
`quadrant_enumeration` images and 1 to the detector's training set, so evaluation excludes all
86 (`data/dentex/disease_leaked_images.json`) and runs on the remaining **164**. Both methods
are scored on those same 164, so the before/after stays like-for-like. RESULTS_LOG 2026-08-22j.

Usage:
    python scripts/dentex/train_enumeration_head.py --smoke     # 1 epoch, tiny subset
    python scripts/dentex/train_enumeration_head.py             # full run
"""

import argparse
import csv
import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEF_DATA = REPO_ROOT / "data/dentex/enumeration_v1"
DEF_OUT = REPO_ROOT / "outputs/enumeration_head"
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def set_seed(s):
    random.seed(s); np.random.seed(s)
    import torch
    torch.manual_seed(s); torch.cuda.manual_seed_all(s)


class ToothSet:
    """Crops + the positional features the head needs; built from the manifest."""

    def __init__(self, rows, root, train, size=224):
        from torchvision import transforms
        self.rows, self.root = rows, Path(root)
        norm = [transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)]
        if train:
            # NO horizontal flip: it would swap left/right and invert the quadrant label.
            self.tf = transforms.Compose(
                [transforms.Resize((size, size)), transforms.RandomRotation(7),
                 transforms.ColorJitter(brightness=.2, contrast=.2)] + norm)
        else:
            self.tf = transforms.Compose([transforms.Resize((size, size))] + norm)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        import torch
        from PIL import Image
        r = self.rows[i]
        img = Image.open(self.root / r["split"] / r["fdi"] / r["crop"]).convert("RGB")
        feats = torch.tensor([float(r["cx"]), float(r["cy"]),
                              float(r["bw"]), float(r["bh"])], dtype=torch.float32)
        return self.tf(img), feats, int(r["quadrant"]) - 1, int(r["position"]) - 1


def build_model(device):
    import torch.nn as nn
    from torchvision.models import ResNet18_Weights, resnet18

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.backbone = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
            feat = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
            self.pos = nn.Sequential(nn.Linear(4, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
            self.quadrant = nn.Linear(feat + 64, 4)
            self.position = nn.Linear(feat + 64, 8)

        def forward(self, img, feats):
            import torch
            z = torch.cat([self.backbone(img), self.pos(feats)], dim=1)
            return self.quadrant(z), self.position(z)

    return Net().to(device)


def evaluate(model, loader, device, full=False):
    import torch
    model.eval()
    qs, ps, qt, pt = [], [], [], []
    with torch.no_grad():
        for img, feats, q, p in loader:
            oq, op = model(img.to(device), feats.to(device))
            qs += oq.argmax(1).cpu().tolist(); ps += op.argmax(1).cpu().tolist()
            qt += q.tolist(); pt += p.tolist()
    qs, ps, qt, pt = map(np.array, (qs, ps, qt, pt))
    fdi_ok = (qs == qt) & (ps == pt)
    from sklearn.metrics import confusion_matrix, f1_score
    fdi_true = (qt + 1) * 10 + (pt + 1)
    fdi_pred = (qs + 1) * 10 + (ps + 1)
    codes = sorted({(q + 1) * 10 + (p + 1) for q in range(4) for p in range(8)})
    out = {
        "n": int(len(qt)),
        "quadrant_acc": float((qs == qt).mean()),
        "position_acc": float((ps == pt).mean()),
        "fdi_exact": float(fdi_ok.mean()),
        "position_within_1": float((np.abs(ps - pt) <= 1)[qs == qt].mean()) if (qs == qt).any() else 0.0,
        "quadrant_macro_f1": float(f1_score(qt, qs, average="macro", zero_division=0)),
        "position_macro_f1": float(f1_score(pt, ps, average="macro", zero_division=0)),
        "fdi_macro_f1": float(f1_score(fdi_true, fdi_pred, average="macro",
                                       labels=codes, zero_division=0)),
    }
    if full:
        out["confusion_quadrant"] = confusion_matrix(qt, qs, labels=list(range(4))).tolist()
        out["confusion_position"] = confusion_matrix(pt, ps, labels=list(range(8))).tolist()
        out["confusion_fdi"] = confusion_matrix(fdi_true, fdi_pred, labels=codes).tolist()
        out["fdi_labels"] = codes
        # per-position accuracy: is the head, like the detector, weaker toward the molars?
        out["per_position_acc"] = {
            str(k + 1): float((ps[pt == k] == k).mean()) if (pt == k).any() else None
            for k in range(8)}
        out["per_quadrant_acc"] = {
            str(k + 1): float((qs[qt == k] == k).mean()) if (qt == k).any() else None
            for k in range(4)}
    return out


def save_figures(res, out):
    """Figures intended for the paper, not just for eyeballing a run."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    log, val = res["epoch_log"], res["val"]
    base = res["baseline_to_beat"]

    # 1) training curves, with the two baselines the head has to beat drawn in
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ep = [r["epoch"] for r in log]
    ax.plot(ep, [r["fdi_exact"] for r in log], "o-", lw=2, label="FDI exact", color="#0E7C86")
    ax.plot(ep, [r["quadrant_acc"] for r in log], "s--", lw=1.4, label="Quadrant", color="#2F7D5B")
    ax.plot(ep, [r["position_acc"] for r in log], "^--", lw=1.4, label="Position", color="#A8690B")
    ax.axhline(base["positional_ceiling_complete_quadrant"], color="#A8443A", ls=":", lw=1.6,
               label=f"positional ceiling {base['positional_ceiling_complete_quadrant']:.1%}")
    ax.axhline(base["positional_fdi_exact_end_to_end"], color="#A8443A", ls="-.", lw=1.4,
               label=f"positional end-to-end {base['positional_fdi_exact_end_to_end']:.1%}")
    ax2 = ax.twinx()
    ax2.plot(ep, [r.get("train_loss") for r in log], color="#5A6A76", lw=1.2, alpha=.65,
             label="train loss")
    ax2.set_ylabel("train loss", color="#5A6A76")
    ax2.tick_params(axis="y", labelcolor="#5A6A76")
    ax.set_xlabel("epoch"); ax.set_ylabel("validation accuracy")
    ax.set_title("Enumeration head — validation accuracy by epoch (GT boxes)")
    ax.set_ylim(0, 1.02); ax.grid(alpha=.25); ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(out / "training_curves.png", dpi=170); plt.close(fig)

    def cm_fig(mat, labels, title, fname, annot):
        import numpy as np
        m = np.array(mat, dtype=float)
        rows = m.sum(axis=1, keepdims=True)
        norm = np.divide(m, rows, out=np.zeros_like(m), where=rows > 0)
        sz = max(4.2, len(labels) * 0.30)
        fig, ax = plt.subplots(figsize=(sz, sz * 0.86))
        im = ax.imshow(norm, cmap="BuPu", vmin=0, vmax=1)
        ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=90, fontsize=7)
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(title, fontsize=10)
        if annot:
            for i in range(len(labels)):
                for j in range(len(labels)):
                    if norm[i, j] > 0.005:
                        ax.text(j, i, f"{norm[i,j]:.2f}", ha="center", va="center",
                                fontsize=7, color="white" if norm[i, j] > .55 else "#222")
        fig.colorbar(im, ax=ax, fraction=.046, label="row-normalised")
        fig.tight_layout(); fig.savefig(out / fname, dpi=170); plt.close(fig)

    cm_fig(val["confusion_quadrant"], [f"Q{i+1}" for i in range(4)],
           "Quadrant confusion (row-normalised)", "confusion_quadrant.png", True)
    cm_fig(val["confusion_position"], [str(i + 1) for i in range(8)],
           "Position confusion (row-normalised)", "confusion_position.png", True)
    cm_fig(val["confusion_fdi"], [str(c) for c in val["fdi_labels"]],
           "FDI confusion, 32 classes (row-normalised)", "confusion_fdi.png", False)

    # 2) per-position accuracy — the diagnostic that mattered for the detector
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ks = [str(i + 1) for i in range(8)]
    vs = [val["per_position_acc"][k] or 0 for k in ks]
    ax.bar(ks, vs, color="#0E7C86")
    for i, v in enumerate(vs):
        ax.text(i, v + .015, f"{v:.2f}", ha="center", fontsize=8)
    ax.set_xlabel("FDI position digit  (1 = central incisor … 8 = third molar)")
    ax.set_ylabel("accuracy"); ax.set_ylim(0, 1.08); ax.grid(axis="y", alpha=.25)
    ax.set_title("Position accuracy by tooth, enumeration head")
    fig.tight_layout(); fig.savefig(out / "per_position_accuracy.png", dpi=170); plt.close(fig)
    print(f"  figures -> {out}/: training_curves, confusion_{{quadrant,position,fdi}}, "
          "per_position_accuracy")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DEF_DATA)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3,
                    help="LR for the new heads; the pretrained backbone uses lr*backbone-lr-mult")
    ap.add_argument("--backbone-lr-mult", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader

    if args.smoke:
        args.epochs = 1
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available()
                          else "mps" if torch.backends.mps.is_available() else "cpu")
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"device={device}")

    rows = list(csv.DictReader(open(args.data / "enumeration_manifest.csv")))
    tr = [r for r in rows if r["split"] == "train"]
    va = [r for r in rows if r["split"] == "val"]
    if args.smoke:
        tr, va = tr[:512], va[:256]
    print(f"train {len(tr):,}  val {len(va):,}  classes {len({r['fdi'] for r in rows})}")

    g = torch.Generator(); g.manual_seed(args.seed)   # reproducible shuffling
    dl_tr = DataLoader(ToothSet(tr, args.data, True), batch_size=args.batch_size,
                       shuffle=True, num_workers=args.workers, generator=g)
    dl_va = DataLoader(ToothSet(va, args.data, False), batch_size=args.batch_size,
                       shuffle=False, num_workers=args.workers)

    model = build_model(device)
    # Discriminative learning rates. The backbone is ImageNet-pretrained and only needs
    # adapting; the positional MLP and both heads are randomly initialised and need to learn
    # from scratch. Driving all of them at the same 1e-3 lets the fresh heads' large early
    # gradients wash through the pretrained features — the standard fine-tuning failure. The
    # backbone therefore runs at lr/10.
    backbone_params = list(model.backbone.parameters())
    head_params = (list(model.pos.parameters()) + list(model.quadrant.parameters())
                   + list(model.position.parameters()))
    assert len(backbone_params) + len(head_params) == len(list(model.parameters())), \
        "parameter groups do not cover the model — some tensors would never be optimised"
    opt = torch.optim.AdamW(
        [{"params": backbone_params, "lr": args.lr * args.backbone_lr_mult},
         {"params": head_params, "lr": args.lr}], weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, args.epochs))
    crit = nn.CrossEntropyLoss()

    best, best_state, best_ep, log = -1.0, None, -1, []
    for ep in range(args.epochs):
        model.train()
        run_loss, run_q, run_p, nb = 0.0, 0.0, 0.0, 0
        for img, feats, q, p in dl_tr:
            img, feats = img.to(device), feats.to(device)
            q, p = q.to(device), p.to(device)
            opt.zero_grad()
            oq, op = model(img, feats)
            lq, lp = crit(oq, q), crit(op, p)
            (lq + lp).backward()
            opt.step()
            # tracked so the log shows train-vs-val divergence directly, rather than
            # leaving overfitting to be inferred from val alone
            run_q += lq.item(); run_p += lp.item(); run_loss += (lq + lp).item(); nb += 1
        sched.step()
        m = evaluate(model, dl_va, device)
        log.append({"epoch": ep + 1, "lr": sched.get_last_lr()[0],
                    "train_loss": run_loss / max(nb, 1),
                    "train_loss_quadrant": run_q / max(nb, 1),
                    "train_loss_position": run_p / max(nb, 1), **m})
        print(f"  ep {ep+1}/{args.epochs}  train_loss {run_loss/max(nb,1):.4f}  "
              f"quadrant {m['quadrant_acc']:.3f}  "
              f"position {m['position_acc']:.3f}  FDI exact {m['fdi_exact']:.3f}")
        if m["fdi_exact"] > best:                       # select on the metric that matters
            best, best_ep = m["fdi_exact"], ep + 1
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            print("     ^ best")

    model.load_state_dict(best_state)
    final = evaluate(model, dl_va, device, full=True)
    torch.save({"model_state_dict": best_state,
                "arch": "resnet18+pos4->(quadrant4,position8)",
                "positional_features": ["cx", "cy", "bw", "bh"]},
               args.out / "enumeration_head_best.pth")
    res = {"created": datetime.now().isoformat(timespec="seconds"),
           "device": str(device), "best_epoch": best_ep,
           "config": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
           "val": final, "epoch_log": log,
           "baseline_to_beat": {"source": "RESULTS_LOG 2026-08-22j / 2026-08-24a (clean 164)",
                                "positional_fdi_exact_end_to_end": 0.229,
                                "positional_ceiling_complete_quadrant": 0.663},
           "caveats": {
               "selection_bias": "The reported val figures come from the checkpoint that was "
                                 "SELECTED on this same val split, so they are optimistically "
                                 "biased and are not an unbiased estimate of generalisation. "
                                 "They are a model-selection diagnostic, not a result.",
               "boxes": "val uses GROUND-TRUTH boxes. The pipeline feeds DETECTOR boxes, which "
                        "are noisier and only reach 71.8% recall — that recall caps end-to-end "
                        "accuracy no matter how good the numbering is.",
               "comparable_number": "The like-for-like figure against the 22.9% baseline comes "
                                    "from scripts/eval/validate_fdi_assignment.py on DENTEX "
                                    "disease/ (164 leak-free images, detector boxes). "
                                    "Do not quote the val fdi_exact as an end-to-end result."}}
    (args.out / "results.json").write_text(json.dumps(res, indent=2) + "\n")
    try:
        save_figures(res, args.out)
    except Exception as e:                      # never lose a finished run to a plotting bug
        print(f"  WARNING: figures failed ({type(e).__name__}: {e}) — results.json is intact")

    print("\n" + "=" * 66)
    print(f"val (GT boxes): quadrant {final['quadrant_acc']:.1%}  "
          f"position {final['position_acc']:.1%}  FDI exact {final['fdi_exact']:.1%}")
    print("positional-assignment baseline, detector boxes: 22.9% end-to-end (clean 164)")
    print("=" * 66)
    print(f"\nwrote {args.out}/enumeration_head_best.pth and results.json")
    print("Next: wire into scripts/eval/validate_fdi_assignment.py and re-run on disease/ —")
    print("that is the like-for-like number against the 22.9% baseline.")


if __name__ == "__main__":
    main()
