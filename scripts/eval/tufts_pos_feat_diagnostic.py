"""
Option B — is the positional-feature pathway a lever for the low Tufts FDI number?

CONTEXT
-------
Tufts end-to-end FDI is 64.8% / 78.6%-of-detected vs DENTEX 58.3% / 82.6% (RESULTS_LOG
2026-09-04d). The 5 Sep council (docs/session-memory/2026-09-05b-tufts-fdi-improvement-council.md)
named a positional-feature covariate shift as one candidate cause: the deployed head
(models/10, DENTEX+Tufts) eats raw [cx, cy, bw, bh] normalised by image size, and Tufts teeth
are ~25% shorter in normalised height (bh 0.175 vs DENTEX 0.233 — measured, see below).

This is the council's Option B: a DIRECTION CHECK, not a paper number. It re-scores the head
on GT-box crops (no detector in the loop) under positional-feature interventions, on Tufts
test AND DENTEX val (the control), and asks whether the pos-feat pathway helps, is neutral, or
hurts on Tufts. `ablate_head_inputs.py` does the same on DENTEX val with the v1.0 head; this
is that script pointed at the deployed head and both corpora, plus a cross-geometry condition.

CONDITIONS (all on GT-box crops, `models/10` head)
  full            [cx,cy,bw,bh] as built
  no_position     pos-feats -> that corpus's own TRAIN mean (the honest "no information"
                  value; zeros would mean cx=0 == far-left edge, a confident lie)
  shuffled_pos    pos-feats from a random OTHER tooth in the same corpus -- separates
                  "ignores the input" from "relies on it"
  dentex_geom     (Tufts only) each Tufts feat standardised to its own test distribution then
                  rescaled to the DENTEX-train distribution: f' = (f-mu_t)/sd_t*sd_d + mu_d.
                  "If Tufts teeth had DENTEX-like geometry, would the head number them better?"

Usage:
    python scripts/eval/tufts_pos_feat_diagnostic.py
"""

import argparse
import csv
import json
import random
import sys
from pathlib import Path

import numpy as np

# The report prints Greek deltas; a Windows console defaults to cp1252 and raises on them, which
# killed a run AFTER the scoring work was done and BEFORE the JSON was written -- losing the
# artefact every number in RESULTS_LOG 2026-09-06 is traced to. Reconfigure rather than
# de-Unicode the report.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):        # non-reconfigurable stream (a pipe on some hosts)
    pass

REPO = Path(__file__).resolve().parents[2]
DENTEX = REPO / "data/dentex/enumeration_v1"
TUFTS = REPO / "data/tufts/enumeration_v1"
DEF_HEAD = REPO / "models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth"
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def rows_for(data_dir, split):
    """Non-jittered manifest rows for one split, with [cx,cy,bw,bh] as float32."""
    rows = [r for r in csv.DictReader(open(data_dir / "enumeration_manifest.csv"))
            if r["split"] == split and r["jittered"] == "0"]
    feats = np.array([[float(r["cx"]), float(r["cy"]), float(r["bw"]), float(r["bh"])]
                      for r in rows], dtype=np.float32)
    return rows, feats


def train_mean(data_dir):
    _, f = rows_for(data_dir, "train")
    return f.mean(axis=0)


def score(model, device, data_dir, split, feat_variants, seed=42):
    """Run the head over one split's GT-box crops under each feature variant."""
    import torch
    from PIL import Image
    from torch.utils.data import DataLoader, Dataset
    from torchvision import transforms

    rows, feats = rows_for(data_dir, split)
    rng = np.random.RandomState(seed)
    perm = rng.permutation(len(rows))
    tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                             transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])

    class DS(Dataset):
        def __len__(self): return len(rows)

        def __getitem__(self, i):
            r = rows[i]
            img = Image.open(data_dir / split / r["fdi"] / r["crop"]).convert("RGB")
            return (tf(img), i, int(r["quadrant"]) - 1, int(r["position"]) - 1)

    dl = DataLoader(DS(), batch_size=64, shuffle=False, num_workers=0)
    variants = {}
    for name, fn in feat_variants.items():
        variants[name] = torch.tensor(fn(feats, perm), dtype=torch.float32)

    got = {name: {"q": [], "p": []} for name in variants}
    qt, pt = [], []
    with torch.no_grad():
        for img, idx, q, p in dl:
            img = img.to(device)
            qt += q.tolist(); pt += p.tolist()
            for name, fv in variants.items():
                oq, op = model(img, fv[idx].to(device))
                got[name]["q"] += oq.argmax(1).cpu().tolist()
                got[name]["p"] += op.argmax(1).cpu().tolist()

    qt, pt = np.array(qt), np.array(pt)
    side = lambda v: np.isin(v, [1, 2]).astype(int)   # Q2,Q3 == patient-left; SIDE is laterality
    out = {}
    for name, g in got.items():
        gq, gp = np.array(g["q"]), np.array(g["p"])
        out[name] = {
            "quadrant": float((gq == qt).mean()),
            "side_laterality": float((side(gq) == side(qt)).mean()),
            "position": float((gp == pt).mean()),
            "fdi_exact": float(((gq == qt) & (gp == pt)).mean()),
        }
    return len(rows), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", type=Path, default=DEF_HEAD)
    ap.add_argument("--out", type=Path, default=REPO / "outputs/tufts_fdi_pos_diagnostic")
    args = ap.parse_args()

    import sys
    sys.path.insert(0, str(REPO))
    import torch
    from src.fdi_head_inference import load_head

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model = load_head(args.head, device)

    md, sd_d = train_mean(DENTEX), rows_for(DENTEX, "train")[1].std(axis=0)
    _, ft_test = rows_for(TUFTS, "test")
    mt, st = ft_test.mean(axis=0), ft_test.std(axis=0)
    mean_d, mean_t = md, train_mean(TUFTS)

    print("positional-feature distributions (non-jittered):")
    print(f"  DENTEX train  cx {md[0]:.3f}  cy {md[1]:.3f}  bw {md[2]:.3f}  bh {md[3]:.3f}")
    print(f"  Tufts  test   cx {mt[0]:.3f}  cy {mt[1]:.3f}  bw {mt[2]:.3f}  bh {mt[3]:.3f}")
    print(f"  device={device}  head={args.head.parent.name}\n")

    dentex_variants = {
        "full": lambda f, pm: f,
        "no_position": lambda f, pm: np.broadcast_to(mean_d, f.shape).copy(),
        "shuffled_pos": lambda f, pm: f[pm],
    }
    tufts_variants = dict(dentex_variants)
    tufts_variants["no_position"] = lambda f, pm: np.broadcast_to(mean_t, f.shape).copy()
    tufts_variants["dentex_geom"] = lambda f, pm: ((f - mt) / st * sd_d + md).astype(np.float32)

    results = {}
    for tag, data_dir, split, variants in (
        ("DENTEX_val", DENTEX, "val", dentex_variants),
        ("Tufts_test", TUFTS, "test", tufts_variants),
    ):
        n, res = score(model, device, data_dir, split, variants)
        results[tag] = {"n_crops": n, "conditions": res}
        print(f"{tag}  (n={n})")
        print(f"  {'condition':<14} {'quadrant':>9} {'SIDE':>8} {'position':>9} {'FDI exact':>10}")
        for name, r in res.items():
            print(f"  {name:<14} {r['quadrant']:>9.1%} {r['side_laterality']:>8.1%} "
                  f"{r['position']:>9.1%} {r['fdi_exact']:>10.1%}")
        f0 = res["full"]
        for name in res:
            if name == "full":
                continue
            d = res[name]
            print(f"  {'Δ '+name:<14} {d['quadrant']-f0['quadrant']:>+9.1%} "
                  f"{d['side_laterality']-f0['side_laterality']:>+8.1%} "
                  f"{d['position']-f0['position']:>+9.1%} {d['fdi_exact']-f0['fdi_exact']:>+10.1%}")
        print()

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "pos_feat_diagnostic.json").write_text(json.dumps({
        "head": str(args.head), "device": str(device),
        "pos_feat_dist": {"dentex_train_mean": md.tolist(), "tufts_test_mean": mt.tolist(),
                          "dentex_train_std": sd_d.tolist(), "tufts_test_std": st.tolist()},
        "results": results,
    }, indent=2) + "\n")
    print(f"wrote {args.out}/pos_feat_diagnostic.json")


if __name__ == "__main__":
    main()
