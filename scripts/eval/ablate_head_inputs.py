"""
Input ablation for the Stage-2 enumeration head: which signal carries which digit?

WHY THIS EXISTS
---------------
`train_enumeration_head.py`, `src/README.md` and `PAPER_MATERIAL.md` all assert a specific
division of labour:

    "Laterality is simply not recoverable from crop pixels... Feeding normalised x resolves
     it. What the *image* adds is the position digit, which is exactly where geometry fails."

That is a **testable** claim and it had never been tested. It is also the entire justification
for the architecture, so if it is wrong the design rationale in the paper is wrong. This script
measures it by removing one input at a time and reporting the two heads separately.

METHOD
------
Four conditions on the enumeration val split (GT boxes, 2,729 crops):

  full          both inputs, as trained
  no_position   positional features replaced by their DATASET MEAN — the honest "no
                information" value. (Zeros would mean cx=0, i.e. the far-left image edge:
                that is not absence of information, it is a confident lie.)
  no_image      normalised image tensor replaced by zeros == the ImageNet mean colour, the
                same "no information" argument.
  shuffled_pos  positional features taken from a random OTHER tooth — not absence of
                information but actively wrong information. Separates "ignores the input"
                from "relies on the input".

READ `no_image` WITH CARE — IT IS CONFOUNDED
--------------------------------------------
A blank (mean-colour) tensor is far outside anything the backbone saw in training, so
`no_image` measures "what the model does when fed an impossible input", NOT "what the
positional features alone can support". Its jaw score (47.5%) lands *below* the 50% chance
line, which is the tell: real `cy` trivially separates upper from lower, so a clean
position-only model could not score 47.5%. Treat `no_image` as a lower bound and draw
conclusions from `full`, `no_position` and `shuffled_pos`, whose inputs are all plausible
values the network was trained to handle.

Usage:
    python scripts/eval/ablate_head_inputs.py
"""

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEF_DATA = REPO_ROOT / "data/dentex/enumeration_v1"
DEF_WEIGHTS = REPO_ROOT / "models/08_fdi_enumeration_head/enumeration_head_best.pth"
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DEF_DATA)
    ap.add_argument("--weights", type=Path, default=DEF_WEIGHTS)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "outputs/enumeration_head")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    import torch
    from PIL import Image
    from torch.utils.data import DataLoader, Dataset
    from torchvision import transforms

    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from src.fdi_head_inference import load_head

    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    rows = [r for r in csv.DictReader(open(args.data / "enumeration_manifest.csv"))
            if r["split"] == "val"]
    print(f"val crops: {len(rows):,}   device={device}")

    feats_all = np.array([[float(r["cx"]), float(r["cy"]), float(r["bw"]), float(r["bh"])]
                          for r in rows], dtype=np.float32)
    mean_feat = feats_all.mean(axis=0)
    print(f"dataset mean positional feature: cx={mean_feat[0]:.4f} cy={mean_feat[1]:.4f} "
          f"bw={mean_feat[2]:.4f} bh={mean_feat[3]:.4f}")
    perm = np.random.permutation(len(rows))          # for shuffled_pos

    tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                             transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])

    class DS(Dataset):
        def __len__(self): return len(rows)
        def __getitem__(self, i):
            r = rows[i]
            img = Image.open(args.data / r["split"] / r["fdi"] / r["crop"]).convert("RGB")
            return (tf(img), torch.tensor(feats_all[i]), torch.tensor(feats_all[perm[i]]),
                    int(r["quadrant"]) - 1, int(r["position"]) - 1)

    # num_workers=0: DS is a local class and cannot be pickled for spawned workers, and
    # 2,729 crops do not need them.
    dl = DataLoader(DS(), batch_size=args.batch_size, shuffle=False, num_workers=0)
    model = load_head(args.weights, device)
    mf = torch.tensor(mean_feat, device=device)

    conds = ["full", "no_position", "no_image", "shuffled_pos"]
    acc = {c: {"q": [], "p": [], "qt": [], "pt": []} for c in conds}
    with torch.no_grad():
        for img, f, fs, q, p in dl:
            img, f, fs = img.to(device), f.to(device), fs.to(device)
            variants = {
                "full":         (img, f),
                "no_position":  (img, mf.expand_as(f)),
                "no_image":     (torch.zeros_like(img), f),
                "shuffled_pos": (img, fs),
            }
            for c, (i_, f_) in variants.items():
                oq, op = model(i_, f_)
                acc[c]["q"] += oq.argmax(1).cpu().tolist()
                acc[c]["p"] += op.argmax(1).cpu().tolist()
                acc[c]["qt"] += q.tolist(); acc[c]["pt"] += p.tolist()

    # Quadrant decomposes into two independent binary facts, and only one of them is the
    # claim under test. FDI quadrants 1,2 are upper and 3,4 lower (JAW); quadrants 1,4 are the
    # patient's right and 2,3 the left (SIDE). "Laterality" means SIDE specifically, so it is
    # reported separately -- a quadrant score mixes it with the much easier jaw split.
    def jaw(v):  return (v >= 2).astype(int)          # 0,1 -> upper ; 2,3 -> lower
    def side(v): return np.isin(v, [1, 2]).astype(int)  # Q2,Q3 -> patient-left

    res = {}
    for c in conds:
        a = {k: np.array(v) for k, v in acc[c].items()}
        res[c] = {
            "quadrant_acc": float((a["q"] == a["qt"]).mean()),
            "jaw_acc": float((jaw(a["q"]) == jaw(a["qt"])).mean()),
            "side_acc_laterality": float((side(a["q"]) == side(a["qt"])).mean()),
            "position_acc": float((a["p"] == a["pt"]).mean()),
            "fdi_exact": float(((a["q"] == a["qt"]) & (a["p"] == a["pt"])).mean()),
        }

    print(f"\n{'condition':<14} {'quadrant':>9} {'jaw':>7} {'SIDE':>8} {'position':>9} {'FDI':>8}")
    for c in conds:
        r = res[c]
        print(f"{c:<14} {r['quadrant_acc']:>9.1%} {r['jaw_acc']:>7.1%} "
              f"{r['side_acc_laterality']:>8.1%} {r['position_acc']:>9.1%} {r['fdi_exact']:>8.1%}")
    f = res["full"]
    print(f"\n{'drop vs full':<14} {'quadrant':>9} {'jaw':>7} {'SIDE':>8} {'position':>9}")
    for c in conds[1:]:
        print(f"{c:<14} {res[c]['quadrant_acc']-f['quadrant_acc']:>+9.1%} "
              f"{res[c]['jaw_acc']-f['jaw_acc']:>+7.1%} "
              f"{res[c]['side_acc_laterality']-f['side_acc_laterality']:>+8.1%} "
              f"{res[c]['position_acc']-f['position_acc']:>+9.1%}")
    print("\nchance: quadrant 25.0%, jaw 50.0%, SIDE 50.0%, position 12.5%")
    print("SIDE is the laterality claim under test.")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "input_ablation.json").write_text(json.dumps(
        {"n_val_crops": len(rows), "weights": str(args.weights),
         "mean_positional_feature": mean_feat.tolist(), "results": res}, indent=2) + "\n")
    print(f"\nwrote {args.out}/input_ablation.json")


if __name__ == "__main__":
    main()
