"""Crop-level evaluation of an enumeration head on a held-out manifest split.

Used for the REVERSE direction of the corpus question: the project's standard metric is
end-to-end on 164 DENTEX images, which tells you nothing about how a head does on Tufts.
Tufts `test` (3,786 crops) is unseen by every arm -- arm A never saw Tufts at all, arms B
and C trained on split==train/val only -- so it is a fair held-out set for all three.

Preprocessing is not reimplemented: `ToothSet` is imported from the trainer and used with
train=False, which is the same eval branch the deployed inference path mirrors. Any drift
there would silently change the numbers, so there is exactly one definition of it.

Plain argmax, no Hungarian one-to-one: these are independent crops, not a mouth. This
measures what the corpus taught the head, not the assignment layer on top of it.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from src.fdi_head_inference import load_head                      # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "teh", REPO / "scripts/dentex/train_enumeration_head.py")
_teh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_teh)


def evaluate(weights, data_root, split, device=None, batch_size=128, workers=0):
    import torch
    from torch.utils.data import DataLoader

    dev = device or torch.device("cuda" if torch.cuda.is_available()
                                 else "mps" if torch.backends.mps.is_available() else "cpu")
    rows = [r for r in _teh.load_manifests([Path(data_root)]) if r["split"] == split]
    if not rows:
        raise SystemExit(f"no rows with split={split} under {data_root}")
    model = load_head(weights, dev)
    dl = DataLoader(_teh.ToothSet(rows, False), batch_size=batch_size,
                    shuffle=False, num_workers=workers)

    nq = npos = nfdi = n = 0
    with torch.no_grad():
        for imgs, feats, gq, gp in dl:
            oq, op = model(imgs.to(dev), feats.to(dev))
            pq = oq.argmax(1).cpu()
            pp = op.argmax(1).cpu()
            nq += (pq == gq).sum().item()
            npos += (pp == gp).sum().item()
            nfdi += ((pq == gq) & (pp == gp)).sum().item()
            n += len(gq)
    return {"n": n, "quadrant": nq / n, "position": npos / n, "fdi_exact": nfdi / n}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    r = evaluate(a.weights, a.data, a.split)
    print(f"{a.label:24s} n={r['n']:6,}  quadrant {r['quadrant']*100:5.1f}%  "
          f"position {r['position']*100:5.1f}%  FDI exact {r['fdi_exact']*100:5.1f}%")
