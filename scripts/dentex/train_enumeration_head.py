"""
Stage-2 replacement: a learned per-tooth FDI enumeration head.

WHY A LEARNED HEAD, AND WHY IT IS THE ONLY REMAINING OPTION
-----------------------------------------------------------
Rank-order positional assignment scores **28.0% end-to-end exact FDI** on 1,534 ground-truth
teeth, and has a measured ceiling of **68.7%** even where a quadrant is fully detected
(RESULTS_LOG 2026-08-22c and 22f). The ceiling exists because eight detected teeth are not
positions 1-8 — they are eight teeth that survived extraction. Improving detector recall
cannot cross it. A per-tooth classifier makes no contiguity assumption at all: it judges each
tooth on its own evidence.

ARCHITECTURE — and the one non-obvious part
-------------------------------------------
ResNet18 backbone over a 1.5x-expanded tooth crop, **concatenated with four positional
features** (normalised centre x/y and box width/height), then two heads: quadrant (4-way) and
position (8-way). FDI = quadrant * 10 + position.

The positional features are not a convenience, they are load-bearing. **Teeth 16 and 26 are
near mirror images**; so are 36/46, 11/21, and every other left/right pair. Laterality is
simply not recoverable from crop pixels, and a pure image classifier would be guessing on
half the label. Feeding normalised x resolves it — the same signal that already gives
geometric quadrant assignment 93.0% accuracy. What the *image* adds is the position digit,
which is exactly where geometry fails.

Two heads rather than one 32-way softmax because the sub-problems have different difficulty
and different failure modes, and reporting them separately is what makes the result
diagnostic: it shows whether a wrong FDI came from the wrong side of the mouth or the wrong
tooth along the arch.

EVALUATION DISCIPLINE
---------------------
Train/val come from DENTEX `quadrant_enumeration` (634 images, split BY IMAGE). The **test set
is `DENTEX/disease/`**, evaluated separately by `scripts/eval/validate_fdi_assignment.py` —
disjoint patients (verified, RESULTS_LOG 2026-08-21m), and the *same* 249 images the 28.0%
baseline was measured on, so the before/after is a like-for-like comparison rather than a new
benchmark chosen after the fact.

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


class EnumerationHead:
    pass


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


def evaluate(model, loader, device):
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
    from sklearn.metrics import f1_score
    return {
        "n": int(len(qt)),
        "quadrant_acc": float((qs == qt).mean()),
        "position_acc": float((ps == pt).mean()),
        "fdi_exact": float(fdi_ok.mean()),
        "position_within_1": float((np.abs(ps - pt) <= 1)[qs == qt].mean()) if (qs == qt).any() else 0.0,
        "quadrant_macro_f1": float(f1_score(qt, qs, average="macro", zero_division=0)),
        "position_macro_f1": float(f1_score(pt, ps, average="macro", zero_division=0)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DEF_DATA)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
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

    dl_tr = DataLoader(ToothSet(tr, args.data, True), batch_size=args.batch_size,
                       shuffle=True, num_workers=args.workers)
    dl_va = DataLoader(ToothSet(va, args.data, False), batch_size=args.batch_size,
                       shuffle=False, num_workers=args.workers)

    model = build_model(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, args.epochs))
    crit = nn.CrossEntropyLoss()

    best, best_state, best_ep, log = -1.0, None, -1, []
    for ep in range(args.epochs):
        model.train()
        for img, feats, q, p in dl_tr:
            img, feats = img.to(device), feats.to(device)
            q, p = q.to(device), p.to(device)
            opt.zero_grad()
            oq, op = model(img, feats)
            (crit(oq, q) + crit(op, p)).backward()
            opt.step()
        sched.step()
        m = evaluate(model, dl_va, device)
        log.append({"epoch": ep + 1, "lr": sched.get_last_lr()[0], **m})
        print(f"  ep {ep+1}/{args.epochs}  quadrant {m['quadrant_acc']:.3f}  "
              f"position {m['position_acc']:.3f}  FDI exact {m['fdi_exact']:.3f}")
        if m["fdi_exact"] > best:                       # select on the metric that matters
            best, best_ep = m["fdi_exact"], ep + 1
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            print("     ^ best")

    model.load_state_dict(best_state)
    final = evaluate(model, dl_va, device)
    torch.save({"model_state_dict": best_state,
                "arch": "resnet18+pos4->(quadrant4,position8)",
                "positional_features": ["cx", "cy", "bw", "bh"]},
               args.out / "enumeration_head_best.pth")
    res = {"created": datetime.now().isoformat(timespec="seconds"),
           "device": str(device), "best_epoch": best_ep,
           "config": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
           "val": final, "epoch_log": log,
           "baseline_to_beat": {"source": "RESULTS_LOG 2026-08-22c/f",
                                "positional_fdi_exact_end_to_end": 0.280,
                                "positional_ceiling_complete_quadrant": 0.687},
           "note": "val here is GT-boxed enumeration data. The comparable number is produced "
                   "by scripts/eval/validate_fdi_assignment.py on DENTEX disease/, which uses "
                   "DETECTOR boxes on the same 249 images as the 28.0% baseline."}
    (args.out / "results.json").write_text(json.dumps(res, indent=2) + "\n")

    print("\n" + "=" * 66)
    print(f"val (GT boxes): quadrant {final['quadrant_acc']:.1%}  "
          f"position {final['position_acc']:.1%}  FDI exact {final['fdi_exact']:.1%}")
    print(f"positional-assignment baseline, detector boxes: 28.0% end-to-end")
    print("=" * 66)
    print(f"\nwrote {args.out}/enumeration_head_best.pth and results.json")
    print("Next: wire into scripts/eval/validate_fdi_assignment.py and re-run on disease/ —")
    print("that is the like-for-like number against the 28.0% baseline.")


if __name__ == "__main__":
    main()
