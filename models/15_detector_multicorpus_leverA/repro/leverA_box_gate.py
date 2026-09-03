#!/usr/bin/env python
"""On-box re-gate for Lever A: run AFTER extracting the tarball, BEFORE training.
Confirms what arrived is what was built (the Mac already did the geometry IoU gate).

  python leverA_box_gate.py /home/detector_multicorpus_v2 <expected_sha256_of_tar>
"""
import sys, hashlib, csv, subprocess
from pathlib import Path
from collections import Counter

root = Path(sys.argv[1])
tar = root.parent / "detector_multicorpus_v2.tar.gz"
expect_sha = sys.argv[2] if len(sys.argv) > 2 else None

fail = []

# 1. tar sha256
if expect_sha and tar.exists():
    got = hashlib.sha256(tar.read_bytes()).hexdigest()
    ok = got == expect_sha
    print(f"[{'OK' if ok else 'FAIL'}] tar sha256 {got}")
    if not ok:
        fail.append(f"sha256 mismatch: expected {expect_sha}")

# 2. no AppleDouble / cache junk
junk = list(root.rglob("._*")) + list(root.rglob(".DS_Store")) + list(root.rglob("*.cache"))
print(f"[{'OK' if not junk else 'CLEAN-NEEDED'}] junk files: {len(junk)}")
for j in junk:
    j.unlink()

# 3. image == label counts per split, and against the manifest
man = list(csv.DictReader(open(root / "manifest.csv")))
man_counts = Counter((r["corpus"], r["split"]) for r in man)
for split in ("train", "val", "test"):
    imgs = {p.stem for p in (root / "images" / split).iterdir()}
    labs = {p.stem for p in (root / "labels" / split).iterdir()}
    miss_lab, miss_img = imgs - labs, labs - imgs
    ok = not miss_lab and not miss_img
    print(f"[{'OK' if ok else 'FAIL'}] {split}: {len(imgs)} images, {len(labs)} labels"
          + ("" if ok else f"  missing labels {len(miss_lab)}, missing images {len(miss_img)}"))
    if not ok:
        fail.append(f"{split} image/label mismatch")

# 4. per-arm list line counts
want = {"train_tufts.txt": 700, "train_3corpus.txt": 2100, "train.txt": 2800,
        "test_tufts.txt": 150, "test_dentex.txt": 62, "test_kaggle.txt": 50, "test_ufba.txt": 43}
for f, n in want.items():
    got = sum(1 for _ in open(root / f))
    ok = got == n
    print(f"[{'OK' if ok else 'FAIL'}] {f}: {got} lines (want {n})")
    if not ok:
        fail.append(f"{f} has {got} lines")

# 5. YOLO label sanity across every label file
bad = 0
n_boxes = 0
for lf in root.rglob("labels/*/*.txt"):
    for ln in lf.read_text().split("\n"):
        p = ln.split()
        if not p:
            continue
        n_boxes += 1
        if len(p) != 5 or p[0] != "0":
            bad += 1; continue
        v = list(map(float, p[1:]))
        if any(x != x or x < 0 or x > 1 for x in v) or v[2] <= 0 or v[3] <= 0:
            bad += 1
print(f"[{'OK' if bad == 0 else 'FAIL'}] label sanity: {n_boxes} boxes, {bad} malformed / out-of-range")
if bad:
    fail.append(f"{bad} bad label lines")

# 6. lists resolve via ultralytics (the ./-relative path check, on THIS box)
try:
    import tempfile
    from ultralytics.data.dataset import YOLODataset
    from ultralytics.data.utils import check_det_dataset
    y = Path(tempfile.mkdtemp()) / "d.yaml"
    y.write_text(f"path: {root}\ntrain: train_3corpus.txt\nval: images/val\nnc: 1\nnames: ['tooth']\n")
    d = check_det_dataset(str(y))
    ds = YOLODataset(img_path=d["train"], data=d, task="detect")
    ok = len(ds) == 2100
    print(f"[{'OK' if ok else 'FAIL'}] ultralytics loads train_3corpus.txt -> {len(ds)} samples (want 2100)")
    if not ok:
        fail.append(f"ultralytics loaded {len(ds)} not 2100")
except Exception as e:
    print(f"[FAIL] ultralytics load: {e}")
    fail.append(str(e))

# 7. render 3 per corpus for eyeball
import cv2
out = root / "_regate"; out.mkdir(exist_ok=True)
seen = Counter()
for r in man:
    c, s = r["corpus"], r["split"]
    if s not in ("train", "val") or seen[c] >= 3:
        continue
    seen[c] += 1
    ext = ".JPG" if c == "tufts" else ".jpg"
    ip, lp = root / "images" / s / (r["stem"] + ext), root / "labels" / s / (r["stem"] + ".txt")
    im = cv2.imread(str(ip))
    if im is None:
        print(f"  render: cannot read {ip}"); continue
    h, w = im.shape[:2]
    for ln in lp.read_text().split("\n"):
        q = ln.split()
        if len(q) == 5:
            cx, cy, bw, bh = map(float, q[1:])
            cv2.rectangle(im, (int((cx-bw/2)*w), int((cy-bh/2)*h)),
                          (int((cx+bw/2)*w), int((cy+bh/2)*h)), (0, 255, 0), 2)
    cv2.imwrite(str(out / f"{c}_{r['stem']}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 75])
print(f"[OK] wrote {len(list(out.iterdir()))} renders to {out} (download + eyeball)")

print("\n" + ("=" * 60))
print("GATE: GO" if not fail else "GATE: NO-GO -> " + "; ".join(fail))
sys.exit(0 if not fail else 1)
