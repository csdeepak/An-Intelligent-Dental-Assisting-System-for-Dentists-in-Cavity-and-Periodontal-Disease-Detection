#!/usr/bin/env python
"""The one test pass of the retrained Stage-4b models (bands of mask overlap, radiograph split).

Pre-registration: outputs/bone_loss_eval/v3_severity/PRE_REGISTRATION.md (Sec 5 what is reported,
Sec 6 the eligibility rule). Nothing here changes a default.

    python scripts/eval/bone_severity_v2_eval.py score    # the Tufts test positives; refuses twice
    python scripts/eval/bone_severity_v2_eval.py report   # recompute the summary from the saved rows

Scored on the 182 test teeth whose crop overlaps an expert abnormality mask by more than 1%, cut
at annotated tooth boxes -- the Stage-4a positives, not the teeth Stage 4a flags. In the pipeline
this head grades flagged teeth, about seven in ten of which carry no abnormality at all; this
pass says nothing about those.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "tufts"))
from bone_loss_heldout import N_BOOT, SEED                                              # noqa: E402
from bootstrap_ci import cluster_bootstrap                                              # noqa: E402
from train_bone_severity_v2 import OUT as MODELS, SEEDS, build_positives, macro_f1      # noqa: E402
from train_bone_loss_v2 import WANT, split_stems                                        # noqa: E402

OUT = REPO_ROOT / "outputs/bone_loss_eval/v3_severity"
SHIP = 42                         # the seed fixed in advance as the candidate (Sec 2)
OLD = REPO_ROOT / "models/04_bone_loss_severity_notebook_models/bone_loss_severity_resnet18_best.pth"
OLD_SHA = "fa93a5201833d8137bd2ae328d3afd63c2c1f9e4ac82a621d1b430a51eba8a4a"
OLD_TRAINED_ON = {"149", "192", "249"}       # models/04's radiographs inside the test split (2026-10-13d)
TEST_BANDS = [55, 63, 64]                    # known before registration, from the Stage-4a test rows
ARMS = ("pred_42", "pred_43", "pred_44", "pred_old", "pred_prior", "pred_majority")


def band_scorer(weights, sha256):
    """-> f(list of 224x224 grey crops) = argmax band, through the same arithmetic as training."""
    import torch
    from src.classifiers import IMAGENET_MEAN, IMAGENET_STD, load_classifier

    if hashlib.sha256(Path(weights).read_bytes()).hexdigest() != sha256:
        raise SystemExit(f"{weights} is not the checkpoint its record names")
    model, _ = load_classifier(weights, 3, torch.device("cpu"))     # eval mode
    mean = torch.tensor(IMAGENET_MEAN).view(1, 3, 1, 1)
    std = torch.tensor(IMAGENET_STD).view(1, 3, 1, 1)

    def f(crops):
        out = []
        with torch.inference_mode():
            for i in range(0, len(crops), 64):
                x = torch.from_numpy(np.stack(crops[i:i + 64])).float().div(255.0)
                x = (x.unsqueeze(1).expand(-1, 3, -1, -1) - mean) / std      # (B, 3, 224, 224)
                out.extend(model(x).argmax(1).tolist())
        return out
    return f


def qwk(y, p, k=3):
    """Quadratic-weighted kappa for k ordered classes."""
    o = np.zeros((k, k))
    for a, b in zip(y, p, strict=True):
        o[a, b] += 1
    w = np.array([[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)])
    e = np.outer(o.sum(1), o.sum(0)) / max(o.sum(), 1)
    return float(1 - (w * o).sum() / (w * e).sum()) if (w * e).sum() else 0.0


def metrics(y, p):
    y, p = np.asarray(y), np.asarray(p)
    recall = [float(((p == c) & (y == c)).sum() / max((y == c).sum(), 1)) for c in range(3)]
    return {"macro_f1": macro_f1(y, p), "accuracy": float((y == p).mean()), "qwk": qwk(y, p),
            "recall_by_band": recall,
            "confusion": [[int(((y == a) & (p == b)).sum()) for b in range(3)] for a in range(3)]}


def score():
    rows_file = OUT / "test_rows.json"
    if rows_file.exists():
        raise SystemExit(f"REFUSED: {rows_file} exists; the test pass is made once (Sec 9)")
    hist = {s: json.loads((MODELS / f"seed{s}_history.json").read_text()) for s in SEEDS}
    stems, records = split_stems()
    if {k: len(v) for k, v in stems.items()} != WANT:
        raise SystemExit("the split is not the registered 678 / 145 / 143")

    _, ytr, rtr = build_positives(stems["train"], records)          # clean train positives
    majority = int(np.bincount(ytr, minlength=3).argmax())
    by_tooth = defaultdict(Counter)
    for r in rtr:
        by_tooth[r["tooth"]][r["band"]] += 1
    prior = {t: c.most_common(1)[0][0] for t, c in by_tooth.items()}

    x, y, rows = build_positives(stems["test"], records)
    if np.bincount(y, minlength=3).tolist() != TEST_BANDS:
        raise SystemExit(f"test positives per band {np.bincount(y, minlength=3).tolist()} != {TEST_BANDS}")
    preds = {f"pred_{s}": band_scorer(MODELS / f"seed{s}_best.pth", hist[s]["sha256"])(list(x)) for s in SEEDS}
    preds["pred_old"] = band_scorer(OLD, OLD_SHA)(list(x))
    out = []
    for i, r in enumerate(rows):
        out.append({"stem": r["stem"], "tooth": r["tooth"], "overlap": r["overlap"], "band": int(y[i]),
                    **{k: int(v[i]) for k, v in preds.items()},
                    "pred_prior": int(prior.get(r["tooth"], majority)), "pred_majority": majority,
                    "old_trained_on": r["stem"] in OLD_TRAINED_ON})
    OUT.mkdir(parents=True, exist_ok=True)
    rows_file.write_text(json.dumps({"majority_band": majority, "rows": out}) + "\n")
    print(f"{len(out)} test positives from {len({r['stem'] for r in out})} radiographs -> {rows_file.name}")
    return report()


def report():
    rows = json.loads((OUT / "test_rows.json").read_text())["rows"]
    clusters = defaultdict(list)
    for r in rows:
        clusters[r["stem"]].append(r)
    clusters = list(clusters.values())
    flat = lambda cs: [r for c in cs for r in c]
    f1_of = lambda arm: (lambda cs: macro_f1(np.array([r["band"] for r in flat(cs)]),
                                             np.array([r[arm] for r in flat(cs)])))

    res = {"pre_registration": "outputs/bone_loss_eval/v3_severity/PRE_REGISTRATION.md",
           "method": f"radiograph-cluster bootstrap, {N_BOOT} resamples, seed {SEED}, percentile",
           "label": "band of mask overlap (<=0.05, 0.05-0.15, >0.15) on teeth with overlap > 0.01; "
                    "an extent band, not a clinical severity",
           "test_teeth": len(rows), "test_radiographs": len(clusters),
           "bands": np.bincount([r["band"] for r in rows], minlength=3).tolist(), "arms": {}}
    for arm in ARMS:
        m = metrics([r["band"] for r in rows], [r[arm] for r in rows])
        pt, lo, hi, _ = cluster_bootstrap(clusters, f1_of(arm), N_BOOT, np.random.default_rng(SEED))
        m["macro_f1_ci95"] = [round(lo, 4), round(hi, 4)]
        res["arms"][arm] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}
    unseen = [c for c in clusters if c[0]["stem"] not in {"149", "192", "249"}]
    res["old_on_radiographs_it_did_not_train_on"] = {
        "teeth": len(flat(unseen)), "macro_f1": round(f1_of("pred_old")(unseen), 4)}
    for other in ("pred_prior", "pred_old", "pred_majority"):
        diff = lambda cs, o=other: f1_of(f"pred_{SHIP}")(cs) - f1_of(o)(cs)
        pt, lo, hi, _ = cluster_bootstrap(clusters, diff, N_BOOT, np.random.default_rng(SEED))
        res[f"seed{SHIP}_minus_{other[5:]}"] = {"value": round(pt, 4), "ci95": [round(lo, 4), round(hi, 4)],
                                                 "excludes_zero": bool(lo > 0 or hi < 0)}
    res["eligible"] = res[f"seed{SHIP}_minus_prior"]["ci95"][0] > 0
    (OUT / "test_summary.json").write_text(json.dumps(res, indent=2) + "\n")
    for arm in ARMS:
        a = res["arms"][arm]
        print(f"  {arm:14s} macro-F1 {a['macro_f1']:.4f} {a['macro_f1_ci95']}  accuracy {a['accuracy']:.4f}  "
              f"kappa {a['qwk']:.4f}")
    print(f"  seed {SHIP} minus tooth prior: {res[f'seed{SHIP}_minus_prior']}  eligible: {res['eligible']}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("score", "report"))
    sys.exit(score() if ap.parse_args().step == "score" else report())
