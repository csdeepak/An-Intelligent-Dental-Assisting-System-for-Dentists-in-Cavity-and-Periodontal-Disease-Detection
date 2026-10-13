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
def hash_from_summary(text, weight_name):
    """Pull the sha256 a run_summary records FOR ONE named weight file.

    A summary may document several checkpoints -- models/03 records both `best` and
    `final`. Each sha256 is attributed to the most recent weight filename mentioned
    above it, and the one belonging to `weight_name` wins.

    Until 27 Aug 2026 this was simply "the last 64-hex token in the file", which
    checked models/03's `best.pth` against `final.pth`'s hash and failed. Kept as a
    fallback for summaries that name only one checkpoint. Covered by
    tests/test_verify_invariants.py.
    """
    current, attributed, last = None, {}, None
    for line in text.splitlines():
        for tok in line.split():
            if tok.endswith((".pth", ".pt")):
                current = tok.strip("`'\",()")
        if "sha256" in line.lower():
            for tok in line.split():
                if len(tok) == 64 and all(c in "0123456789abcdef" for c in tok):
                    last = tok
                    if current is not None:
                        attributed.setdefault(current, tok)
    return attributed.get(weight_name, last)


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
        # The Lever A multi-corpus detector. Pinned 11 Oct 2026, ahead of a planned change of
        # the Stage-1 default to it; not in git, so this is a SKIP on any other machine.
        ("models/15_detector_multicorpus_leverA/arm3c_best.pt",
         "models/15_detector_multicorpus_leverA/run_summary.txt"),
        # Stages 4a/4b, tagged 27 Aug 2026 -- the last untagged models in the project.
        # They were in use as pipeline defaults for months with no hash on record, so
        # nothing would have caught a silent swap or a partial copy.
        ("models/03_bone_loss_model_training_notebook_models/bone_loss_resnet18_best.pth",
         "models/03_bone_loss_model_training_notebook_models/run_summary.txt"),
        ("models/04_bone_loss_severity_notebook_models/bone_loss_severity_resnet18_best.pth",
         "models/04_bone_loss_severity_notebook_models/run_summary.txt"),
        # Stage 4a as of 13 Oct 2026: retrained with a radiograph-level split and adopted as the
        # pipeline default (RESULTS_LOG 2026-10-13b, -c). models/03 above stays pinned: every
        # Stage-4 number published before that date used it.
        ("models/18_bone_loss_radiograph_split/seed42_best.pth",
         "models/18_bone_loss_radiograph_split/run_summary.txt"),
    ]
    out = []
    for w, s in pairs:
        wp, sp = REPO_ROOT / w, REPO_ROOT / s
        if not wp.exists():
            out.append(f"SKIP {Path(w).name} (not on this machine)")
            continue
        want = None
        # A summary may document SEVERAL checkpoints (models/03 records both `best` and
        # `final`). Attribute each sha256 to the most recent weight filename mentioned
        # above it, and prefer the one belonging to the file under test. Falling back to
        # "last hash in the file" -- which is all this did until 27 Aug 2026 -- silently
        # checked models/03's `best` against `final`'s hash. Caught by this very check.
        # encoding is explicit: Windows defaults to cp1252 and dies on the em-dashes
        # and warning glyphs these summaries contain, while macOS defaults to utf-8 and
        # passes. That asymmetry is exactly the class of bug this repo keeps hitting.
        want = hash_from_summary(sp.read_text(encoding="utf-8"), Path(w).name)
        got = hashlib.sha256(wp.read_bytes()).hexdigest()
        if want is None:
            # A failure, not a note: a pin with nothing to compare against passes for no reason.
            # Lever A's summary held only an 8-character prefix until 11 Oct 2026.
            raise AssertionError(f"no sha256 recorded for {Path(w).name} in {s}")
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


# ---------------------------------------------------------------- crop source frames
def inv_crop_frames():
    """
    Every enumeration crop must actually be a cut of the source image its manifest names.

    A few manifest rows are re-cut from the source directory `meta.json` names, using the head's
    own crop contract, and compared pixel-wise against the stored crop. No model is loaded.

    WHAT THIS CATCHES, AND WHAT IT DOES NOT -- stated plainly, because the temptation is to file
    this under "2026-09-06c can't happen again" and it does not close that hole on its own.

      CATCHES  a corpus that has drifted from the source it claims: rebuilt from a different
               frame while meta.json still names the old one, half-rebuilt, swapped in from
               another machine, or silently re-cropped with different geometry.
      MISSES   a corpus that is internally consistent but built from the WRONG frame -- exactly
               2026-09-06c. Those crops matched their (wrong) source exactly; the manifest's
               labels and coordinates were correct and self-consistent too, and the builder's
               own geometry guard only fires on 90-degree errors, which produce degenerate
               boxes, not on a 180-degree one, which does not.

    Detecting THAT needs the labels and the pixels compared through something that knows what a
    tooth looks like: `scripts/eval/tufts_crop_frame_check.py`, which re-cuts the same boxes from
    each candidate frame and scores the head on them (11.5% vs 73.5% -- unmissable). Run that
    after building or moving a crop corpus; this invariant is the cheap daily guard that the
    corpus still matches what it says it is.
    """
    sys.path.insert(0, str(REPO_ROOT))
    import numpy as np
    try:
        import cv2
    except ImportError:
        return "SKIP (cv2 not installed)"
    from src.crop_generator import compute_expanded_bbox
    from src.fdi_head_inference import CROP, EXPAND

    out = []
    for corpus in ("tufts", "dentex"):
        base = REPO_ROOT / f"data/{corpus}/enumeration_v1"
        meta_p, man_p = base / "meta.json", base / "enumeration_manifest.csv"
        if not (meta_p.exists() and man_p.exists()):
            out.append(f"{corpus} SKIP (corpus absent)")
            continue
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        # the two builders name the field differently, and DENTEX's points at the dataset root
        src = Path(meta.get("source_images") or meta.get("source", ""))
        if not src.is_absolute():
            src = REPO_ROOT / src
        rows = [r for r in csv.DictReader(open(man_p, encoding="utf-8"))
                if r["jittered"] == "0"]
        rows = [r for r in rows if r["split"] == "test"] or rows
        rows = rows[:8]
        if rows:
            name = rows[0]["source_image"]
            for cand in (src, src / "xrays", src / "input"):
                if (cand / name).exists():
                    src = cand
                    break
        if not rows or not (src / rows[0]["source_image"]).exists():
            out.append(f"{corpus} SKIP (source images not on this machine)")
            continue
        diffs = []
        for r in rows:
            stored = cv2.imread(str(base / r["split"] / r["fdi"] / r["crop"]))
            img = cv2.imread(str(src / r["source_image"]))
            if stored is None or img is None:
                continue
            H, W = img.shape[:2]
            cx, cy, bw, bh = (float(r[k]) for k in ("cx", "cy", "bw", "bh"))
            x, y, w, h = (cx - bw / 2) * W, (cy - bh / 2) * H, bw * W, bh * H
            x1, y1, x2, y2 = (int(v) for v in
                              compute_expanded_bbox(x, y, w, h, W, H, fw=EXPAND, fh=EXPAND))
            patch = img[y1:max(y2, y1 + 1), x1:max(x2, x1 + 1)]
            if patch.size == 0:
                continue
            diffs.append(float(np.abs(cv2.resize(patch, (CROP, CROP)).astype(int)
                                      - stored.astype(int)).mean()))
        if not diffs:
            out.append(f"{corpus} SKIP (no readable pairs)")
            continue
        worst = max(diffs)
        # Re-encode noise sits in the low single digits; a frame error crops a different tooth
        # and lands in the tens. 12 separates them with room on both sides.
        if worst > 12:
            raise AssertionError(
                f"{corpus} crops do not match {src.name}: mean|diff| up to {worst:.1f} over "
                f"{len(diffs)} rows -- the corpus is cut from a different frame than its "
                f"meta.json names (see RESULTS_LOG 2026-09-06c)")
        out.append(f"{corpus} ok vs {src.name} (max mean|diff| {worst:.1f})")
    return "; ".join(out)


# ---------------------------------------------------------------- Lever C
def inv_lever_c_defaults():
    """
    Lever C must stay OFF by default and must not introduce a tunable of its own.

    Both halves have bitten this project before: a default that drifted (the Stage-3a swap was
    only safe because the old path stayed selectable) and a threshold that acquired a second,
    quietly different value. The repair's TAU is the head's existing LOW_CONFIDENCE and its
    GAP_FACTOR is `assign_fdi`'s existing default -- if either is edited on its own, the
    pre-registration's "the only free hyperparameter is tau, frozen to 0.30" stops being true.
    """
    import inspect
    sys.path.insert(0, str(REPO_ROOT))
    from src.fdi_assignment import assign_fdi
    from src.fdi_head_inference import ASSIGNMENTS, LOW_CONFIDENCE
    from src.fdi_structural_repair import GAP_FACTOR, TAU
    assert ASSIGNMENTS[0] == "hungarian", f"the deployed default moved: {ASSIGNMENTS}"
    assert TAU == LOW_CONFIDENCE, f"Lever C tau {TAU} != head LOW_CONFIDENCE {LOW_CONFIDENCE}"
    gap_default = inspect.signature(assign_fdi).parameters["gap_factor"].default
    assert GAP_FACTOR == gap_default, f"gap_factor drifted: {GAP_FACTOR} != {gap_default}"
    return (f"default={ASSIGNMENTS[0]}, tau={TAU} (== LOW_CONFIDENCE), "
            f"gap_factor={GAP_FACTOR} (== assign_fdi default)")


def inv_default_detector_registered():
    """
    The default Stage-1 detector must carry accuracy figures measured for IT.

    Every report states a detection recall and an end-to-end FDI accuracy. Until 11 Oct 2026
    both were module constants, so changing `DEF_DETECTOR`, or passing `--detector`, produced
    reports quoting another detector's name and numbers. They are now looked up by the weights'
    sha256. This names no checkpoint: it checks that whatever the default is has an entry, so
    a new default cannot ship without figures of its own.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.run_inference import DEF_DETECTOR, DETECTOR_PROFILES, file_sha256
    sha = file_sha256(str(DEF_DETECTOR))
    prof = DETECTOR_PROFILES.get(sha)
    assert prof, f"DEF_DETECTOR {DEF_DETECTOR.name} ({sha[:12]}…) has no DETECTOR_PROFILES entry"
    assert prof["recall"] and prof["fdi_exact_end_to_end"], f"{prof['tag']}: no accuracy recorded"
    return (f"{prof['tag']}: recall {prof['recall']:.3f}, "
            f"FDI end-to-end {prof['fdi_exact_end_to_end']:.3f}")


def inv_stage4_report_wording():
    """
    The report must not present Stage 4 as a periodontal finding (RESULTS_LOG 2026-10-10).

    Stage 4's positive class is "overlaps a Tufts expert abnormality mask" and its in-domain
    score is not held out. The per-tooth field names stay `bone_loss` so consumers do not break,
    which leaves the caveat as the only thing telling a reader what the field is. So it is
    checked: present in every report, and rendered by the app rather than left in the JSON --
    until 11 Oct 2026 the app showed a "Bone loss" column and no Stage-4 caveat at all.

    Since 13 Oct 2026 the caveat follows the binary weights that are loaded (BONE_LOSS_PROFILES,
    RESULTS_LOG 2026-10-13c), as the detector's figures do. So this checks three things: every
    profile, the unregistered one included, says the field is not a periodontal finding; the
    checkpoint whose 0.923 was validation on its own training radiographs still says so; and
    whatever the default is has a profile and the report carries it.
    """
    import numpy as np
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.run_inference import (BONE_LOSS_PROFILES, DEF_BONE_LOSS, SCHEMA_VERSION,
                                       UNREGISTERED_BONE_LOSS, build_report, file_sha256)
    assert float(SCHEMA_VERSION.split("/")[1]) >= 1.2, f"schema went backwards: {SCHEMA_VERSION}"
    for prof in (*BONE_LOSS_PROFILES.values(), UNREGISTERED_BONE_LOSS):
        text = " ".join(prof["label_and_validation"].lower().split())
        for needle in ("abnormality", "not as a periodontal"):
            assert needle in text, f"{prof['tag']}: the Stage-4 caveat lost its '{needle}' statement"
    previous = BONE_LOSS_PROFILES["c52f7f484076a2a2c3c144c3351912b118b6b0d56fc51ba1b4296e6ce6213db1"]
    assert "not a held-out" in previous["label_and_validation"].lower(), \
        "the previous Stage-4a checkpoint's caveat lost its 'not a held-out' statement"
    app = (REPO_ROOT / "app.py").read_text(encoding="utf-8")
    assert "lim['bone_loss_label_and_validation']" in app, "app.py does not render the caveat"
    if not DEF_BONE_LOSS.exists():
        return f"SKIP {DEF_BONE_LOSS.name} (not on this machine)"
    sha = file_sha256(str(DEF_BONE_LOSS))
    prof = BONE_LOSS_PROFILES.get(sha)
    assert prof, f"DEF_BONE_LOSS {DEF_BONE_LOSS.name} ({sha[:12]}…) has no BONE_LOSS_PROFILES entry"
    rep = build_report("x", np.zeros((8, 8, 3), np.uint8), [], [], [], [], [],
                       {"caries": {"method": "lesion-detector"}, "bone_loss": {"sha256_binary": sha}})
    assert rep["limitations"]["bone_loss_label_and_validation"] == prof["label_and_validation"], \
        "the report does not carry the default checkpoint's caveat"
    return f"{SCHEMA_VERSION}; {prof['tag']}; caveat follows the weights and is rendered by app.py"


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
    # BOTH corpora are required. Guarding on disease/ alone reported a false FAIL on a machine
    # that had only the disease/ subset fetched (for the Stage-2 re-measurement, 27 Aug 2026):
    # the overlap computed as 0-of-85 simply because the enumeration xrays were absent, which
    # reads as "the exclusion list is wrong" rather than "the data is not all here".
    # Different machines legitimately hold different subsets — see transfer.md §8.
    disease_dir = DENTEX / "disease/input"
    enum_dir = DENTEX / "training_data/quadrant_enumeration/xrays"
    if not disease_dir.exists() and not enum_dir.exists():
        return "SKIP (DENTEX not on this machine)"
    if not disease_dir.exists() or not enum_dir.exists():
        have = "disease/" if disease_dir.exists() else "training_data/quadrant_enumeration/"
        return f"SKIP (only {have} present — this check needs both corpora)"
    d250 = hashes(disease_dir)
    enum = hashes(enum_dir)
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
check("Lever C off by default", inv_lever_c_defaults)
check("default detector registered", inv_default_detector_registered)
check("Stage-4 report wording", inv_stage4_report_wording)
check("crop source frames", inv_crop_frames)
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
