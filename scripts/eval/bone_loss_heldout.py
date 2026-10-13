#!/usr/bin/env python
"""One held-out score of the frozen Stage-4a classifier on Tufts radiographs it never trained on.

Pre-registration: outputs/bone_loss_eval/heldout/PRE_REGISTRATION.md (commit 570925c). The crop,
the label, the population, the gates, what is reported and how it is worded are all fixed there;
read it before changing anything here.

The label is "the crop overlaps a Tufts expert ABNORMALITY mask", not periodontal bone loss
(PAPER_MATERIAL.md Sec 8.28). This script measures the model on the label it was trained on.

    python scripts/eval/bone_loss_heldout.py gate     # the 145 training-side radiographs only
    python scripts/eval/bone_loss_heldout.py score    # refuses without a passed gate, or twice
    python scripts/eval/bone_loss_heldout.py report   # recompute the summary from the saved rows
"""

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

SRC = REPO_ROOT / "_repo_archive/datasets_workspace"
META = REPO_ROOT / "data/tufts/resampled_dataset/metadata"
WEIGHTS = REPO_ROOT / "models/03_bone_loss_model_training_notebook_models/bone_loss_resnet18_best.pth"
SHA256 = "c52f7f484076a2a2c3c144c3351912b118b6b0d56fc51ba1b4296e6ce6213db1"
OUT = REPO_ROOT / "outputs/bone_loss_eval/heldout"

# notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb, cell 5
EXPAND_W, EXPAND_H, CROP, MIN_DIM, OVERLAP_T = 1.5, 2.0, 224, 3, 0.01
N_BOOT, SEED, NEAR_DUP_BITS, MIN_POS = 10000, 42, 10, 30
# a clean, non-augmented manifest row: <stem>_T<tooth>_<counter>.png (no "_jit", no "aug<k>_")
CLEAN_ROW = re.compile(r"^(?P<stem>[^_]+)_T(?P<tooth>[^_]+)_\d+\.png$")


def expanded_box(x, y, w, h, img_w, img_h):
    """The notebook's compute_expanded_bbox (cell 16), verbatim: 1.5x W, 2.0x H, int(), clipped."""
    cx, cy, nw, nh = x + w / 2.0, y + h / 2.0, w * EXPAND_W, h * EXPAND_H
    return (max(0, int(cx - nw / 2.0)), max(0, int(cy - nh / 2.0)),
            min(img_w, int(cx + nw / 2.0)), min(img_h, int(cy + nh / 2.0)))


def overlap_ratio(mask, cx1, cy1, cx2, cy2):
    """Non-zero mask pixels inside the crop over the crop's area (cell 16)."""
    m = mask[cy1:cy2, cx1:cx2]
    return float(np.count_nonzero(m > 0)) / m.size if m.size else 0.0


def clean_crops(stem, objects):
    """Every clean crop of one radiograph, as the notebook built them (cells 9, 14, 18).
    Yields (row, 224x224 grey crop); row = {stem, tooth, label, overlap, mask_empty}."""
    img = cv2.imread(str(SRC / "Radiographs" / f"{stem}.JPG"), cv2.IMREAD_GRAYSCALE)
    mask = cv2.imread(str(SRC / "Expert/mask" / f"{stem}.JPG"), cv2.IMREAD_GRAYSCALE)
    if img is None or mask is None:
        raise SystemExit(f"cannot read radiograph or mask {stem}")
    img_h, img_w = img.shape[:2]
    mask_empty = bool(mask.max() == 0)
    for obj in objects:
        box = obj.get("bounding box")
        if box is None or len(box) < 4:
            continue
        y1, x1, y2, x2 = box[:4]                      # the field is [y1, x1, y2, x2], landscape
        x, y, w, h = x1, y1, x2 - x1, y2 - y1
        if w < MIN_DIM or h < MIN_DIM:
            continue
        cx1, cy1, cx2, cy2 = expanded_box(x, y, w, h, img_w, img_h)
        if cx2 - cx1 < MIN_DIM or cy2 - cy1 < MIN_DIM:
            continue
        overlap = 0.0 if mask_empty else overlap_ratio(mask, cx1, cy1, cx2, cy2)
        crop = cv2.resize(img[cy1:cy2, cx1:cx2], (CROP, CROP), interpolation=cv2.INTER_LINEAR)
        yield ({"stem": stem, "tooth": str(obj.get("title", "unknown")).strip(),
                "label": int(overlap > OVERLAP_T), "overlap": round(overlap, 6),
                "mask_empty": mask_empty}, crop)


def load_sources():
    """radiograph stem -> its tooth objects, and the clean manifest rows of the 145 used ones."""
    records = {Path(r["External ID"]).stem: r["Label"]["objects"]
               for r in json.loads((SRC / "Segmentation/teeth_bbox.json").read_text())
               if "Label" in r and "objects" in r["Label"]}
    used, clean = set(), {}
    for split, name in (("val", "val_metadata.csv"), ("train", "train_resampled_metadata.csv")):
        rows = list(csv.DictReader(open(META / name)))
        used |= {r["stem"] for r in rows}
        clean[split] = [(m["stem"], m["tooth"], int(r["label"])) for r in rows
                        if r.get("augmented", "False") == "False"
                        and (m := CLEAN_ROW.match(r["filename"]))]
    return records, used, clean


def load_scorer():
    """-> f(list of 224x224 grey crops) = P(diseased) for each: three identical channels,
    ImageNet normalisation -- what the training notebook's validation transform gave the model."""
    import torch
    from src.classifiers import BONE_LOSS_CLASSES, IMAGENET_MEAN, IMAGENET_STD, load_classifier

    if hashlib.sha256(WEIGHTS.read_bytes()).hexdigest() != SHA256:
        raise SystemExit(f"{WEIGHTS} is not the pinned checkpoint")
    device = torch.device("cpu")                       # registered: CPU
    model, _ = load_classifier(WEIGHTS, 2, device)     # returns the model in eval mode
    pos = BONE_LOSS_CLASSES.index("bone_loss")
    mean = torch.tensor(IMAGENET_MEAN).view(1, 3, 1, 1)
    std = torch.tensor(IMAGENET_STD).view(1, 3, 1, 1)

    def p_diseased(crops):
        out = []
        with torch.inference_mode():
            for i in range(0, len(crops), 64):
                x = torch.from_numpy(np.stack(crops[i:i + 64])).float().div(255.0)  # (B, 224, 224)
                x = (x.unsqueeze(1).expand(-1, 3, -1, -1) - mean) / std             # (B, 3, 224, 224)
                out.extend(torch.softmax(model(x.to(device)), dim=1)[:, pos].tolist())
        return out
    return p_diseased


def dhash(path):
    g = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    s = cv2.resize(g, (17, 16), interpolation=cv2.INTER_AREA)
    return (s[:, 1:] > s[:, :-1]).flatten()


# --------------------------------------------------------------------------------------- gate
def gate():
    records, used, clean = load_sources()
    regen, crop_of = defaultdict(list), defaultdict(list)
    for stem in sorted(used):
        for row, crop in clean_crops(stem, records[stem]):
            regen[row["stem"], row["tooth"]].append(row["label"])
            crop_of[row["stem"], row["tooth"]].append((row["label"], crop))

    manifest = clean["val"] + clean["train"]
    found = [(s, t, lab) for s, t, lab in manifest if (s, t) in regen]
    same = [1 for s, t, lab in found if lab in regen[s, t]]
    g1 = {"radiographs": len(used), "regenerated_crops": sum(len(v) for v in regen.values()),
          "clean_manifest_rows": len(manifest), "found": len(found), "same_label": len(same),
          "found_share": len(found) / len(manifest), "same_label_share": len(same) / len(found)}
    g1["pass"] = g1["found_share"] >= 0.99 and g1["same_label_share"] >= 0.99
    print(f"G1 labels: {g1['found']}/{g1['clean_manifest_rows']} manifest rows found, "
          f"{g1['same_label']}/{g1['found']} with the same label -> {'pass' if g1['pass'] else 'FAIL'}")

    g2 = {"pass": False}
    if g1["pass"]:
        val = [(s, t, lab) for s, t, lab in clean["val"] if (s, t) in crop_of]
        # two teeth of one radiograph can share a title: take the crop whose label agrees
        pick = [next((c for lab_c, c in crop_of[s, t] if lab_c == lab), crop_of[s, t][0][1])
                for s, t, lab in val]
        p = load_scorer()(pick)
        pos = [q >= 0.5 for q, k in zip(p, val) if k[2] == 1]
        neg = [q >= 0.5 for q, k in zip(p, val) if k[2] == 0]
        g2 = {"clean_val_positives": len(pos), "found": sum(pos), "reference_found": 29,
              "clean_val_normals": len(neg), "false_positives": sum(neg),
              "specificity": 1 - sum(neg) / len(neg)}
        g2["pass"] = 28 <= g2["found"] <= 30 and g2["specificity"] >= 0.98
        print(f"G2 model: {g2['found']}/{g2['clean_val_positives']} clean validation positives "
              f"found (reference 29, 28-30 passes); specificity {g2['specificity']:.4f} on "
              f"{g2['clean_val_normals']} normals -> {'pass' if g2['pass'] else 'FAIL'}")
    res = {"pre_registration": "outputs/bone_loss_eval/heldout/PRE_REGISTRATION.md",
           "note": "training-side figures; a harness check, never a result",
           "G1_labels": g1, "G2_model": g2, "pass": bool(g1["pass"] and g2["pass"])}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gate.json").write_text(json.dumps(res, indent=2) + "\n")
    print(f"gate {'PASSED' if res['pass'] else 'FAILED -- the held-out radiographs stay closed'}")
    return 0 if res["pass"] else 1


# -------------------------------------------------------------------------------------- score
def score():
    gate_file, rows_file = OUT / "gate.json", OUT / "heldout_rows.json"
    if not gate_file.exists() or not json.loads(gate_file.read_text())["pass"]:
        raise SystemExit("REFUSED: no passed gate (Sec 5)")
    if rows_file.exists():
        raise SystemExit(f"REFUSED: {rows_file} exists; the held-out pass is made once (Sec 8)")
    records, used, _ = load_sources()

    radio = SRC / "Radiographs"
    by_md5 = defaultdict(list)
    numeric = lambda s: (len(s), s)                 # "9" before "10" without assuming digits
    for stem in sorted(set(records) - used, key=numeric):
        by_md5[hashlib.md5((radio / f"{stem}.JPG").read_bytes()).hexdigest()].append(stem)
    dropped_twins = sorted(s for group in by_md5.values() for s in group[1:])
    stems = sorted((group[0] for group in by_md5.values()), key=numeric)
    used_hash = np.array([dhash(radio / f"{s}.JPG") for s in sorted(used)])
    near = [s for s in stems
            if (used_hash != dhash(radio / f"{s}.JPG")).sum(1).min() <= NEAR_DUP_BITS]
    stems = [s for s in stems if s not in set(near)]
    print(f"held-out radiographs: {len(stems)}  (byte-identical twins dropped: {dropped_twins}; "
          f"near-duplicates of a training-side radiograph: {near})")

    p_diseased, rows = load_scorer(), []
    for stem in stems:
        pairs = list(clean_crops(stem, records[stem]))
        if pairs:
            for (row, _), p in zip(pairs, p_diseased([c for _, c in pairs])):
                rows.append(dict(row, p=round(p, 6)))
    rows_file.write_text(json.dumps({"dropped_twins": dropped_twins, "near_duplicates": near,
                                     "n_radiographs": len(stems), "rows": rows}) + "\n")
    print(f"scored {len(rows)} teeth -> {rows_file}")
    return report()


# ------------------------------------------------------------------------------------- report
def tooth_prior():
    """P(diseased | tooth title) over the clean manifest rows, one per radiograph and tooth."""
    _, _, clean = load_sources()
    label = {}
    for s, t, lab in clean["val"] + clean["train"]:
        label[s, t] = max(lab, label.get((s, t), 0))
    n, k = Counter(), Counter()
    for (s, t), lab in label.items():
        n[t] += 1
        k[t] += lab
    overall = sum(k.values()) / sum(n.values())
    return {t: k[t] / n[t] for t in n}, overall, len(label)


def stats(y, p, q):
    """Every reported figure for one set of teeth. q is the image-blind prior's score."""
    from sklearn.metrics import average_precision_score, roc_auc_score
    f = p >= 0.5
    tp, fp = int((f & (y == 1)).sum()), int((f & (y == 0)).sum())
    fn, tn = int((~f & (y == 1)).sum()), int((~f & (y == 0)).sum())
    nan = float("nan")
    sens = tp / (tp + fn) if tp + fn else nan
    spec = tn / (tn + fp) if tn + fp else nan
    ppv = tp / (tp + fp) if tp + fp else nan
    f1_pos = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else nan
    f1_neg = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else nan
    out = {"sensitivity": sens, "specificity": spec, "ppv": ppv, "f1_diseased": f1_pos,
           "macro_f1": (f1_pos + f1_neg) / 2}
    if 0 < y.sum() < len(y):
        ap, ap0 = average_precision_score(y, p), average_precision_score(y, q)
        auc, auc0 = roc_auc_score(y, p), roc_auc_score(y, q)
        out.update(average_precision=ap, roc_auc=auc, prior_average_precision=ap0,
                   prior_roc_auc=auc0, ap_model_minus_prior=ap - ap0, auc_model_minus_prior=auc - auc0)
    return out, {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def summarise(rows, prior, overall):
    """Point values, counts and a radiograph-cluster bootstrap interval for one population."""
    y = np.array([r["label"] for r in rows])
    p = np.array([r["p"] for r in rows])
    q = np.array([prior.get(r["tooth"], overall) for r in rows])
    point, counts = stats(y, p, q)
    n_pos = int(y.sum())
    res = {"radiographs": len({r["stem"] for r in rows}), "teeth": len(rows), "positive_teeth": n_pos,
           "prevalence": n_pos / len(rows), "confusion": counts,
           "flag_nothing": {"sensitivity": 0.0, "specificity": 1.0},
           "flag_everything": {"sensitivity": 1.0, "specificity": 0.0, "ppv": n_pos / len(rows)}}
    members = defaultdict(list)
    for i, r in enumerate(rows):
        members[r["stem"]].append(i)
    members = [np.array(v) for v in members.values()]
    rng = np.random.default_rng(SEED)
    draws = defaultdict(list)
    for _ in range(N_BOOT):
        idx = np.concatenate([members[j] for j in rng.integers(0, len(members), len(members))])
        for k, v in stats(y[idx], p[idx], q[idx])[0].items():
            draws[k].append(v)
    positive_only = {"sensitivity", "average_precision", "roc_auc", "prior_average_precision",
                     "prior_roc_auc", "ap_model_minus_prior", "auc_model_minus_prior"}
    for k, v in point.items():
        res[k] = {"value": None if np.isnan(v) else round(v, 4)}
        if n_pos < MIN_POS and k in positive_only:
            res[k]["note"] = f"fewer than {MIN_POS} positive teeth: no interval (Sec 6)"
        elif not np.isnan(v):
            d = np.array(draws[k], dtype=float)
            res[k]["ci95"] = [round(float(np.nanpercentile(d, 2.5)), 4),
                              round(float(np.nanpercentile(d, 97.5)), 4)]
            res[k]["resamples_used"] = int((~np.isnan(d)).sum())
    return res


def report():
    saved = json.loads((OUT / "heldout_rows.json").read_text())
    rows = saved["rows"]
    prior, overall, n_prior = tooth_prior()
    res = {"pre_registration": "outputs/bone_loss_eval/heldout/PRE_REGISTRATION.md",
           "committed_at": "570925c", "weights_sha256": SHA256,
           "label": "crop overlaps a Tufts expert abnormality mask by more than 1% -- not periodontal bone loss",
           "method": f"radiograph-cluster bootstrap, {N_BOOT} resamples, seed {SEED}, percentile",
           "dropped_twins": saved["dropped_twins"], "near_duplicates": saved["near_duplicates"],
           "tooth_position_prior": {"fitted_on_teeth": n_prior, "overall_share": round(overall, 4)},
           "crop_level_validation_reference": {"sensitivity": "49/59", "specificity": "1492/1499",
                                               "macro_f1": 0.9233, "held_out": False}}
    for name, keep in (("all", lambda r: True), ("mask_non_empty", lambda r: not r["mask_empty"]),
                       ("mask_empty", lambda r: r["mask_empty"])):
        res[name] = summarise([r for r in rows if keep(r)], prior, overall)
        s, c = res[name], res[name]["confusion"]
        print(f"\n{name}: {s['radiographs']} radiographs, {s['teeth']} teeth, "
              f"{s['positive_teeth']} positive (prevalence {s['prevalence']:.4f})")
        print(f"  confusion  TP {c['tp']}  FN {c['fn']}  FP {c['fp']}  TN {c['tn']}")
        for k in ("sensitivity", "specificity", "ppv", "f1_diseased", "macro_f1", "average_precision",
                  "roc_auc", "prior_average_precision", "prior_roc_auc", "ap_model_minus_prior",
                  "auc_model_minus_prior"):
            if k in s and s[k]["value"] is not None:
                print(f"  {k:26s} {s[k]['value']:.4f}  {s[k].get('ci95', s[k].get('note', ''))}")
    (OUT / "heldout_summary.json").write_text(json.dumps(res, indent=2) + "\n")
    print(f"\n-> {OUT / 'heldout_summary.json'}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("gate", "score", "report"))
    sys.exit({"gate": gate, "score": score, "report": report}[ap.parse_args().step]())
