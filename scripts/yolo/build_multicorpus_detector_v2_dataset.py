#!/usr/bin/env python
"""Build the Lever A multi-corpus YOLO DETECTION dataset: Tufts + DENTEX + Kaggle-dual + UFBA-425.

WHY (pre-registered: outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md)
-------------------------------------------------------------------------------
Lever 1 (scripts/yolo/build_multicorpus_detector_dataset.py) pooled TWO corpora, put Tufts at
52 % of the train mix with a naive concatenation, and failed its Tufts-test guard (0.810 -> 0.647).
Lever A is the fix: FOUR corpora from four institutions, and per-corpus BALANCED sampling so no
corpus dominates the loss. Everything else -- the CCW detector frame, the round-trip geometry
gate, the Tufts canonical-count gate, the leakage guard -- is carried over from Lever 1 verbatim.

CORPORA
-------
  Tufts               700/150/150  frozen split_v1, already in the detector frame (portrait)
  DENTEX quad_enum    634          upright landscape -> rotated CCW
  Kaggle "dual"       ~499         LabelMe polygons, upright landscape -> rotated CCW
  UFBA-425            425          CC BY 4.0, Roboflow YOLO txt, 640x640 -> rotated CCW

  val/test are TUFTS ONLY and byte-identical to the frozen split, so `Tufts test box mAP@0.5`
  stays comparable to the frozen detector's 0.810 (pre-registered Guard 2). The three added
  corpora are split 90/10 train/test image-level (seed 42): their 10 % test slices exist ONLY
  for a reported per-corpus detection-mAP secondary and never gate anything.

WHAT THIS SCRIPT REFUSES TO GET WRONG (same three as Lever 1)
-----------------------------------------------------------
1. Orientation. Every non-Tufts corpus is upright; pixels AND boxes are rotated 90 deg CCW into
   the detector frame with src.orientation.rot_box, and every box is round-tripped through
   unrot_box before it is written. Rotating one and not the other is how a 90-epoch run was
   voided (RESULTS_LOG 2026-08-27a).
2. The frozen split. Tufts val/test are carried through untouched, Tufts-only, and the build
   aborts unless it reproduces the frozen detector's canonical 3,794 / 3,924 box counts.
3. Leakage. Every non-Tufts image is MD5-checked against the 164 leak-free DENTEX/disease eval
   images and refused on a match. (Expected 0 -- runs anyway.)

NOT this script's job: verifying the FDI handedness of Kaggle / UFBA. This builds a SINGLE-CLASS
`tooth` detector -- a tooth box is a tooth box whatever its number. Handedness only matters for
the optional head-v4 arm (pre-reg S6), which is a separate build.

Usage:
    python scripts/yolo/build_multicorpus_detector_v2_dataset.py --dry-run
    python scripts/yolo/build_multicorpus_detector_v2_dataset.py
"""

import argparse
import csv
import hashlib
import json
import math
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

HOME = Path.home()
DEF = dict(
    tufts_bbox=REPO / "_repo_archive/datasets_workspace/Segmentation/teeth_bbox.json",
    tufts_imgs=REPO / "_repo_archive/datasets_workspace/Radiographs_rotated",
    tufts_split=REPO / "outputs/eda_tufts/split_v1.csv",
    dentex=HOME / "Downloads/Capstone/DENTEX/training_data/quadrant_enumeration",
    kaggle=REPO / "data/kaggle_dual",
    ufba=REPO / "data/ufba425",
    eval_pool=HOME / "Downloads/Capstone/DENTEX/disease/input",
    exclusions=REPO / "data/dentex/disease_leaked_images.json",
    out=REPO / "data/detector_multicorpus_v2",
)
MIN_MEDIAN_IOU = 0.99
MIN_PX = 2
JPEG_Q = 95
SEED = 42
KAGGLE_VALID = {str(q * 10 + p) for q in (1, 2, 3, 4) for p in range(1, 9)}  # FDI 11..48


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def poly_bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def yolo_line(x1, y1, x2, y2, W, H):
    return (f"0 {((x1 + x2) / 2) / W:.6f} {((y1 + y2) / 2) / H:.6f} "
            f"{(x2 - x1) / W:.6f} {(y2 - y1) / H:.6f}\n")


def upright_boxes_tufts(entry):
    """teeth_bbox.json objects -> list of [x1,y1,x2,y2] in the portrait (detector) frame."""
    objs = (entry.get("Label") or {}).get("objects") or entry.get("objects") or []
    out = []
    for o in objs:
        b = o.get("bounding box") or o.get("bbox")
        if b and len(b) == 4 and b[2] - b[0] >= MIN_PX and b[3] - b[1] >= MIN_PX:
            out.append([float(b[0]), float(b[1]), float(b[2]), float(b[3])])
    return out


def load_upright_corpus(name, args):
    """Yield (stem, image_path, [ [x1,y1,x2,y2] upright pixel boxes ]) for a non-Tufts corpus."""
    if name == "dentex":
        coco = json.loads((args.dentex / "train_quadrant_enumeration.json").read_text())
        by_img = defaultdict(list)
        for a in coco["annotations"]:
            by_img[a["image_id"]].append(a["bbox"])
        for im in coco["images"]:
            p = args.dentex / "xrays" / im["file_name"]
            if not p.exists():
                continue
            boxes = [[x, y, x + w, y + h] for x, y, w, h in by_img.get(im["id"], [])]
            yield "dentex_" + Path(im["file_name"]).stem, p, boxes

    elif name == "kaggle":
        img_dir, lbl_dir = args.kaggle / "images1", args.kaggle / "labels"
        stems = sorted({p.stem for p in img_dir.glob("*.png")}
                       & {p.stem for p in lbl_dir.glob("*.json")})
        for stem in stems:
            d = json.loads((lbl_dir / f"{stem}.json").read_text())
            boxes = []
            for sh in d.get("shapes", []):
                if str(sh["label"]).strip() not in KAGGLE_VALID:
                    continue
                x1, y1, x2, y2 = poly_bbox(sh["points"])
                boxes.append([x1, y1, x2, y2])
            yield "kaggle_" + stem, img_dir / f"{stem}.png", boxes

    elif name == "ufba":
        img_dir, lbl_dir = args.ufba / "numbering_xrays", args.ufba / "boundinng_boxes"
        for img in sorted(img_dir.glob("*.jpg")):
            txt = lbl_dir / (img.stem + ".txt")
            if not txt.exists():
                continue
            # UFBA images are a uniform 640x640 Roboflow export; read real dims to be safe.
            import cv2
            im = cv2.imread(str(img))
            if im is None:
                continue
            H, W = im.shape[:2]
            boxes = []
            for ln in txt.read_text().splitlines():
                p = ln.split()
                if len(p) != 5:
                    continue
                cx, cy, w, h = (float(v) for v in p[1:])
                boxes.append([(cx - w / 2) * W, (cy - h / 2) * H,
                              (cx + w / 2) * W, (cy + h / 2) * H])
            yield "ufba_" + img.stem, img, boxes


def split_9010(stems, seed=SEED):
    r = random.Random(seed)
    s = list(stems)
    r.shuffle(s)
    cut = round(len(s) * 0.9)
    return {**{k: "train" for k in s[:cut]}, **{k: "test" for k in s[cut:]}}


def main():
    ap = argparse.ArgumentParser()
    for k, v in DEF.items():
        ap.add_argument(f"--{k.replace('_', '-')}", type=Path, default=v)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--renders", type=int, default=8, help="samples/corpus to _check/")
    args = ap.parse_args()

    import cv2
    from src.orientation import DEFAULT as ROT, rot_box, unrot_box

    stats = Counter()
    rows = []
    checks = []                       # (rotated_box, upright_box, W, H) for the IoU gate
    train_paths = defaultdict(list)   # corpus -> [abs image paths], for balanced train.txt

    for d in ("images/train", "images/val", "images/test",
              "labels/train", "labels/val", "labels/test", "_check"):
        (args.out / d).mkdir(parents=True, exist_ok=True) if not args.dry_run else None

    # ---------------------------------------------------------------- Tufts (frozen, in-frame)
    split_of = {r["filename"]: r["split"] for r in csv.DictReader(open(args.tufts_split))}
    print("TUFTS  boxes from teeth_bbox.json, frozen split_v1, already in the detector frame")
    for entry in json.loads(args.tufts_bbox.read_text()):
        stem = Path(str(entry.get("External ID", ""))).stem
        fname = stem + ".JPG"
        split = split_of.get(fname)
        src = args.tufts_imgs / fname
        if split is None or not src.exists():
            stats["tufts_skipped"] += 1
            continue
        boxes = upright_boxes_tufts(entry)
        stats[f"{split}/tufts_img"] += 1
        stats[f"{split}/tufts_box"] += len(boxes)
        rows.append(dict(corpus="tufts", split=split, stem=stem, n_boxes=len(boxes), rotated=0))
        if args.dry_run:
            continue
        img = cv2.imread(str(src))
        H, W = img.shape[:2]
        shutil.copy2(src, args.out / "images" / split / fname)
        (args.out / "labels" / split / (stem + ".txt")).write_text(
            "".join(yolo_line(*b, W, H) for b in boxes))
        if split == "train":
            train_paths["tufts"].append(str((args.out / "images/train" / fname).resolve()))
    for split, expect in (("val", 3794), ("test", 3924)):
        got = stats[f"{split}/tufts_box"]
        print(f"  canonical {split}: expected {expect}, got {got}  "
              f"[{'MATCH' if got == expect else 'MISMATCH'}]")
        if got != expect:
            raise SystemExit(f"Tufts {split} {got} != canonical {expect} -- refusing to write")

    # ------------------------------------------------------------------ leakage guard
    excl = set(json.loads(args.exclusions.read_text())["all_excluded"])
    leakfree = {md5(f) for f in sorted(args.eval_pool.iterdir())
                if f.suffix.lower() in (".png", ".jpg", ".jpeg") and f.stem not in excl}
    print(f"\nleakage guard: {len(leakfree)} leak-free eval images hashed (expect 164)")

    # ------------------------------------------------- DENTEX / Kaggle / UFBA (upright -> CCW)
    seen_hash = {}                     # md5 -> "corpus/stem" of first occurrence
    for corpus in ("dentex", "kaggle", "ufba"):
        items = list(load_upright_corpus(corpus, args))
        keep = []
        for stem, path, boxes in items:
            h = md5(path)
            if h in leakfree:
                stats[f"{corpus}_REFUSED_leakage"] += 1
                continue
            if h in seen_hash:          # within- or cross-corpus byte-identical duplicate
                stats[f"{corpus}_REFUSED_dup"] += 1
                continue
            seen_hash[h] = f"{corpus}/{stem}"
            if boxes:
                keep.append((stem, path, boxes))
        sp = split_9010([s for s, _, _ in keep])
        print(f"{corpus.upper():7s} {len(keep)} images with boxes  "
              f"({sum(v == 'train' for v in sp.values())} train / "
              f"{sum(v == 'test' for v in sp.values())} test, 90/10 seed {SEED})")

        for stem, path, boxes in keep:
            split = sp[stem]
            img = None if args.dry_run else cv2.imread(str(path))
            W, H = (None, None)
            if img is not None:
                H, W = img.shape[:2]
            elif not args.dry_run:
                stats[f"{corpus}_unreadable"] += 1
                continue
            else:
                im = cv2.imread(str(path)); H, W = im.shape[:2]

            lines, kept_boxes = [], 0
            rw, rh = H, W                       # 90-deg rotation swaps axes
            for up in boxes:
                rb = rot_box(up, W, H, ROT)
                back = unrot_box(rb, W, H, ROT)
                if max(abs(a - b) for a, b in zip(back, up)) > 1e-6:
                    raise SystemExit(f"round-trip failed {corpus}/{stem}: {up}->{rb}->{back}")
                x1, y1, x2, y2 = rb
                x1, y1, x2, y2 = max(0, x1), max(0, y1), min(rw, x2), min(rh, y2)
                if x2 - x1 < MIN_PX or y2 - y1 < MIN_PX:
                    stats[f"{corpus}_degenerate"] += 1
                    continue
                lines.append(yolo_line(x1, y1, x2, y2, rw, rh))
                checks.append((rb, up, W, H))
                kept_boxes += 1

            stats[f"{split}/{corpus}_img"] += 1
            stats[f"{split}/{corpus}_box"] += kept_boxes
            rows.append(dict(corpus=corpus, split=split, stem=stem,
                             n_boxes=kept_boxes, rotated=1))
            if args.dry_run:
                continue
            rot = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            assert rot.shape[:2] == (rh, rw)
            out_img = args.out / "images" / split / (stem + ".jpg")
            cv2.imwrite(str(out_img), rot, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
            (args.out / "labels" / split / (stem + ".txt")).write_text("".join(lines))
            if split == "train":
                train_paths[corpus].append(str(out_img.resolve()))

    # ------------------------------------------------------------------ geometry gate
    from src.orientation import unrot_box as _u
    ious = sorted(iou(_u(rb, W, H, ROT), up) for rb, up, W, H in checks)
    med = ious[len(ious) // 2] if ious else 0.0
    print(f"\nGEOMETRY GATE: {len(ious):,} rotated boxes round-tripped; "
          f"median IoU vs source = {med:.4f}  "
          f"[{'PASS' if med >= MIN_MEDIAN_IOU else 'FAIL'}]")
    if med < MIN_MEDIAN_IOU:
        raise SystemExit(f"median IoU {med:.4f} < {MIN_MEDIAN_IOU} -- refusing to write")

    # ------------------------------------------------------------------ composition
    corpora = ("tufts", "dentex", "kaggle", "ufba")
    tr_img = {c: stats[f"train/{c}_img"] for c in corpora}
    print("\nCOMPOSITION")
    for c in corpora:
        print(f"  {c:7s} train {tr_img[c]:>4} img / {stats[f'train/{c}_box']:>6} box"
              f"   test {stats[f'test/{c}_img']:>3} img / {stats[f'test/{c}_box']:>5} box")
    print(f"  val (Tufts only) {stats['val/tufts_img']} img / {stats['val/tufts_box']} box")
    print(f"  refused for leakage: "
          + ", ".join(f"{c} {stats[f'{c}_REFUSED_leakage']}" for c in corpora[1:])
          + " | dup: "
          + ", ".join(f"{c} {stats[f'{c}_REFUSED_dup']}" for c in corpora[1:]))

    # ------------------------------------------------------------- balanced train.txt
    biggest = max(tr_img.values())
    present = [c for c in corpora if tr_img[c]]
    smallest = min(tr_img[c] for c in present)
    print(f"\nBALANCED train.txt: {len(present) * biggest:,} lines "
          f"({len(present)} corpora x {biggest} each; per-epoch exposure "
          f"{biggest / smallest:.2f}x pre-balance -> 1.00x)")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    bal_lines = []
    for c in present:
        paths = train_paths[c]
        reps = math.ceil(biggest / len(paths))
        bal_lines += (paths * reps)[:biggest]
    random.Random(SEED).shuffle(bal_lines)

    (args.out / "train.txt").write_text("\n".join(bal_lines) + "\n")
    (args.out / "data.yaml").write_text(
        f"# Lever A multi-corpus detector -- Tufts + DENTEX + Kaggle + UFBA-425, detector frame ({ROT})\n"
        f"# Built by scripts/yolo/build_multicorpus_detector_v2_dataset.py\n"
        f"# train.txt is per-corpus BALANCED (repeated paths). val/test are TUFTS ONLY and\n"
        f"# byte-identical to the frozen split -- test box mAP@0.5 is the pre-registered guard.\n"
        f"path: {args.out}\ntrain: train.txt\nval: images/val\ntest: images/test\n\n"
        f"nc: 1\nnames: ['tooth']\n")
    with open(args.out / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (args.out / "meta.json").write_text(json.dumps({
        "built": "Lever A multi-corpus detector dataset",
        "pre_registration": "outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md",
        "corpora": {c: {"train_img": tr_img[c], "train_box": stats[f"train/{c}_box"],
                        "test_img": stats[f"test/{c}_img"], "test_box": stats[f"test/{c}_box"]}
                    for c in corpora},
        "val_test_policy": "Tufts only, frozen split_v1, canonical counts 3794/3924 reproduced",
        "rotation": f"DENTEX/Kaggle/UFBA rotated 90 deg {ROT} into the detector frame via "
                    f"src.orientation.rot_box; Tufts already in that frame",
        "balanced_train": {"lines": len(bal_lines), "per_corpus_target": biggest},
        "geometry_gate": {"boxes": len(ious), "median_iou": round(med, 6),
                          "threshold": MIN_MEDIAN_IOU},
        "leakage_guard": {c: stats[f"{c}_REFUSED_leakage"] for c in corpora[1:]},
        "ufba_licence": "CC BY 4.0 (figshare 10.6084/m9.figshare.29827475)",
        "kaggle_licence": "unstated (Kaggle 'a-dual-labeled-dataset'); already a project corpus "
                          "(head v3, models/12) -- compliance-track item, not new to Lever A",
        "counts": dict(stats),
    }, indent=2) + "\n")

    # ------------------------------------------------------------------ eyeball renders
    for c in corpora:
        picks = [r for r in rows if r["corpus"] == c and r["split"] in ("train", "val")][:args.renders]
        for r in picks:
            sp = r["split"]
            ext = ".JPG" if c == "tufts" else ".jpg"
            ip = args.out / "images" / sp / (r["stem"] + ext)
            lp = args.out / "labels" / sp / (r["stem"] + ".txt")
            im = cv2.imread(str(ip))
            if im is None:
                continue
            h, w = im.shape[:2]
            for ln in lp.read_text().splitlines():
                _, cx, cy, bw, bh = (float(v) for v in ln.split())
                cv2.rectangle(im, (int((cx - bw / 2) * w), int((cy - bh / 2) * h)),
                              (int((cx + bw / 2) * w), int((cy + bh / 2) * h)), (0, 255, 0), 2)
            cv2.imwrite(str(args.out / "_check" / f"{c}_{r['stem']}.jpg"), im,
                        [cv2.IMWRITE_JPEG_QUALITY, 80])
    print(f"\nwrote {args.out}\n  eyeball {args.out / '_check'} before tarring for the GPU box")


if __name__ == "__main__":
    main()
