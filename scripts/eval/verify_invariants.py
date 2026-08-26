"""
Re-check the facts this repo's documentation depends on. Fast, no GPU, no model inference.

WHY THIS EXISTS
---------------
Every correction in `RESULTS_LOG.md` — there are seven — has the same shape:

    an inference that was never tested was written down as fact,
    then propagated into other documents, where it hardened into "known".

  21f  checkpoints "presumably lost"          -> they were on Kaggle
  21m  filenames overlap -> same patient      -> different patients entirely
  22d  the rotated files "look right"         -> rotation was the other way
  22j  two folders are disjoint               -> a THIRD folder was never tested
  24a  two numbers both read ~67%             -> one was recall, not the ceiling
  24e  a shuffle ablation shows fragility     -> it answers a different question
  25a  "healthy teeth NOT derivable"          -> derivable via MD5, just not by filename

Every one was catchable by a cheap direct test — hash the files, compare the pairs, recompute
the bucket. Each took minutes once actually attempted. The failure was never difficulty; it
was that the check was skipped because the inference felt safe.

This script runs those checks. It does not prove the project correct — it proves that the
specific things the docs assert are still true of the files on disk. Run it after changing
data, swapping a checkpoint, or before trusting a number in a paper draft.

Usage:
    python scripts/eval/verify_invariants.py
    python scripts/eval/verify_invariants.py --skip-slow     # omit the MD5 corpus joins
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DENTEX = Path.home() / "Downloads/Capstone/DENTEX"

RESULTS = []


def check(name, fn, slow=False):
    RESULTS.append((name, fn, slow))


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def hashes(d):
    return {md5(p): p.stem for p in sorted(Path(d).glob("*.png"))}


# ---------------------------------------------------------------- frozen weights
def inv_weight_hashes():
    """A frozen model's bytes must still match the hash its run_summary records."""
    pairs = [
        # v1.0 stays pinned even though v2 superseded it: it is the head every Stage-2
        # number before 26 Aug 2026 was measured on, so it must stay byte-reproducible.
        ("models/08_fdi_enumeration_head/enumeration_head_best.pth",
         "models/08_fdi_enumeration_head/run_summary.txt"),
        ("models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth",
         "models/10_fdi_head_dentex_tufts_v2/run_summary.txt"),
        ("models/09_caries_gate_v3/caries_gate_v3.pth",
         "models/09_caries_gate_v3/run_summary.txt"),
        # Stage-1 detector as of 27 Aug 2026. Pinned because it is now the pipeline default;
        # adopted for its box gain despite missing §2's mask bar (RESULTS_LOG 2026-08-27d).
        ("models/11_yolo_seg_tufts_r1/best.pt",
         "models/11_yolo_seg_tufts_r1/run_summary.txt"),
    ]
    out = []
    for w, s in pairs:
        wp, sp = REPO_ROOT / w, REPO_ROOT / s
        if not wp.exists():
            out.append(f"SKIP {Path(w).name} (not on this machine)")
            continue
        want = None
        # encoding is explicit: Windows defaults to cp1252 and dies on the em-dashes
        # and warning glyphs these summaries contain, while macOS defaults to utf-8 and
        # passes. That asymmetry is exactly the class of bug this repo keeps hitting.
        for line in sp.read_text(encoding="utf-8").splitlines():
            if "sha256" in line.lower():
                for tok in line.split():
                    if len(tok) == 64 and all(c in "0123456789abcdef" for c in tok):
                        want = tok
        got = hashlib.sha256(wp.read_bytes()).hexdigest()
        if want is None:
            out.append(f"NO HASH RECORDED for {Path(w).name}")
        elif want != got:
            raise AssertionError(f"{Path(w).name}: recorded {want[:12]}… but file is {got[:12]}…")
        else:
            out.append(f"{Path(w).name} matches {got[:12]}…")
    return "; ".join(out)


# ---------------------------------------------------------------- class orders
def inv_class_orders():
    """An inverted class index reports every healthy tooth as diseased, silently."""
    import torch
    want = {
        "models/07_caries_cascade/final_model.pth": {"caries": 0, "no_caries": 1},
        "models/07_caries_cascade/phase2_final_bundle.pth": {"caries": 0, "deep_caries": 1},
        "models/09_caries_gate_v3/caries_gate_v3.pth": {"caries": 0, "no_caries": 1},
    }
    n = 0
    for rel, expect in want.items():
        p = REPO_ROOT / rel
        if not p.exists():
            continue
        ck = torch.load(p, map_location="cpu", weights_only=False)
        got = ck.get("class_to_idx") if isinstance(ck, dict) else None
        if got is None:
            continue
        if got != expect:
            raise AssertionError(f"{Path(rel).name}: class_to_idx {got} != {expect}")
        n += 1
    return f"{n} checkpoints carry the expected class_to_idx"


# ---------------------------------------------------------------- crop contracts
def inv_crop_contracts():
    """Three stages, three expansions. Crossing them is silent and confidently wrong."""
    sys.path.insert(0, str(REPO_ROOT))
    from src.classifiers import BONE_LOSS_EXPAND, CARIES_EXPAND
    from src.fdi_head_inference import EXPAND as FDI_EXPAND
    assert CARIES_EXPAND == (1.0, 1.0), f"caries expansion drifted: {CARIES_EXPAND}"
    assert BONE_LOSS_EXPAND == (1.5, 2.0), f"bone-loss expansion drifted: {BONE_LOSS_EXPAND}"
    assert FDI_EXPAND == 1.5, f"FDI head expansion drifted: {FDI_EXPAND}"
    assert CARIES_EXPAND != BONE_LOSS_EXPAND, "the two branches must not share a crop"
    return "caries 1.0x, bone-loss 1.5x/2.0x, FDI head 1.5x — all distinct"


# ---------------------------------------------------------------- Stage-2 numbers
def inv_stage2_reproduces():
    """The headline Stage-2 figures must still fall out of the saved per-tooth rows."""
    run = REPO_ROOT / "outputs/stage2_clean"
    if not (run / "stage2_rows_head.json").exists():
        return "SKIP (outputs/stage2_clean not present)"
    out = []
    for meth, exp_all, exp_det in (("head", 0.465, 0.694), ("positional", 0.229, 0.341)):
        rows = json.loads((run / f"stage2_rows_{meth}.json").read_text(encoding="utf-8"))
        det = [r for r in rows if r["detected"]]
        ok = [r for r in det if r["pred_fdi"] == r["gt_fdi"]]
        a, d = len(ok) / len(rows), len(ok) / len(det)
        for got, want, lbl in ((a, exp_all, "end-to-end"), (d, exp_det, "of-detected")):
            if abs(got - want) > 0.002:
                raise AssertionError(f"{meth} {lbl}: {got:.3f} != documented {want:.3f}")
        out.append(f"{meth} {a:.3f}/{d:.3f}")
    return "; ".join(out)


# ---------------------------------------------------------------- leakage
def inv_leakage_list():
    """The exclusion list must still describe the actual overlaps on disk."""
    f = REPO_ROOT / "data/dentex/disease_leaked_images.json"
    L = json.loads(f.read_text(encoding="utf-8"))
    if not (DENTEX / "disease/input").exists():
        return "SKIP (DENTEX not on this machine)"
    d250 = hashes(DENTEX / "disease/input")
    enum = hashes(DENTEX / "training_data/quadrant_enumeration/xrays")
    overlap = {d250[h] for h in set(d250) & set(enum)}
    listed = set(L["leaked_into_enumeration_head_training"])
    if overlap != listed:
        raise AssertionError(
            f"enumeration overlap changed: on disk {len(overlap)}, listed {len(listed)}; "
            f"missing {sorted(overlap - listed)[:5]}")
    return f"{len(listed)} enumeration + {len(L['leaked_into_detector_training'])} detector, " \
           f"{len(L['all_excluded'])} excluded total — matches disk"


def inv_v3_join():
    """The MD5 join under the repaired caries gate — the falsifiable FDI-agreement test."""
    EN = DENTEX / "training_data/quadrant_enumeration"
    DI = DENTEX / "training_data/quadrant-enumeration-disease"
    if not DI.exists():
        return "SKIP (DENTEX not on this machine)"
    en = json.loads((EN / "train_quadrant_enumeration.json").read_text(encoding="utf-8"))
    di = json.loads((DI / "train_quadrant_enumeration_disease.json").read_text(encoding="utf-8"))
    eh = {md5(EN / "xrays" / i["file_name"]): i for i in en["images"]
          if (EN / "xrays" / i["file_name"]).exists()}
    dh = {md5(DI / "xrays" / i["file_name"]): i for i in di["images"]
          if (DI / "xrays" / i["file_name"]).exists()}
    shared = set(eh) & set(dh)
    ea, da = defaultdict(list), defaultdict(list)
    for a in en["annotations"]:
        ea[a["image_id"]].append(a)
    for a in di["annotations"]:
        da[a["image_id"]].append(a)

    def iou(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        iw = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
        ih = max(0.0, min(ay + ah, by + bh) - max(ay, by))
        inter = iw * ih
        u = aw * ah + bw * bh - inter
        return inter / u if u > 0 else 0.0

    agree = tot = 0
    for h in shared:
        E, D = ea[eh[h]["id"]], da[dh[h]["id"]]
        for d in D:
            best = max(E, key=lambda e: iou(e["bbox"], d["bbox"]), default=None)
            if best is None or iou(best["bbox"], d["bbox"]) < 0.5:
                continue
            tot += 1
            agree += (best["category_id_1"], best["category_id_2"]) == \
                     (d["category_id_1"], d["category_id_2"])
    rate = agree / max(tot, 1)
    if len(shared) < 200 or rate < 0.90:
        raise AssertionError(f"MD5 join degraded: {len(shared)} shared, FDI agreement {rate:.2%}")
    return f"{len(shared)} shared images, FDI agreement {rate:.2%}"


# ---------------------------------------------------------------- dataset hygiene
def inv_v3_dataset():
    """Split hygiene and label consistency in the repaired caries training set."""
    m = REPO_ROOT / "data/dentex/crops_v3_phase1/manifest.csv"
    if not m.exists():
        return "SKIP (crops_v3_phase1 not built here)"
    rows = list(csv.DictReader(open(m)))
    by = defaultdict(set)
    for r in rows:
        by[r["source_image_md5"]].add(r["split"])
    span = [k for k, v in by.items() if len(v) > 1]
    assert not span, f"{len(span)} images span more than one split"
    bad = [r for r in rows
           if (r["subtype"] in ("caries", "deep_caries")) != (r["label"] == "caries")]
    assert not bad, f"{len(bad)} rows where label and subtype disagree"
    amb = [r for r in rows if 0.10 < float(r["iou_to_disease"]) < 0.50]
    assert not amb, f"{len(amb)} rows in the excluded ambiguous band"
    return f"{len(rows):,} crops, {len(by)} images, 0 span splits, 0 label/subtype conflicts"


check("frozen weight hashes", inv_weight_hashes)
check("checkpoint class orders", inv_class_orders)
check("crop contracts distinct", inv_crop_contracts)
check("Stage-2 numbers reproduce", inv_stage2_reproduces)
check("caries v3 dataset hygiene", inv_v3_dataset)
check("leakage exclusion list", inv_leakage_list, slow=True)
check("caries v3 MD5 join", inv_v3_join, slow=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-slow", action="store_true", help="omit the MD5 corpus joins")
    args = ap.parse_args()
    width = max(len(n) for n, _, _ in RESULTS)
    failed = 0
    for name, fn, slow in RESULTS:
        if slow and args.skip_slow:
            print(f"  {name:<{width}}  SKIP (--skip-slow)")
            continue
        try:
            print(f"  {name:<{width}}  OK    {fn()}")
        except Exception as e:
            failed += 1
            print(f"  {name:<{width}}  FAIL  {type(e).__name__}: {e}")
    print()
    if failed:
        print(f"{failed} invariant(s) FAILED — a documented fact no longer matches the files.")
        raise SystemExit(1)
    print("all invariants hold.")


if __name__ == "__main__":
    main()
