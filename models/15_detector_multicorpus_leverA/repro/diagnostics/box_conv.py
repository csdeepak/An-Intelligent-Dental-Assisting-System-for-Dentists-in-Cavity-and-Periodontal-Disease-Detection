#!/usr/bin/env python
"""Lever A Tufts diagnostic: compare tooth-box CONVENTION across the 4 corpora.

If Tufts GT boxes (mask-derived) differ systematically from the human-drawn box
corpora, a model trained on the mix learns a blended box style that matches none,
and Tufts test mAP@0.5:0.95 collapses even when detection is fine.

Reads the built YOLO labels in data/detector_multicorpus_v2/ (all normalized xywh).
"""
import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path("data/detector_multicorpus_v2")
man = list(csv.DictReader(open(ROOT / "manifest.csv")))

# stem -> corpus  (stems are unique across corpora by construction)
corpus_of = {}
for r in man:
    corpus_of[r["stem"]] = r["corpus"]

def label_path(stem, split):
    return ROOT / "labels" / split / f"{stem}.txt"

by_corpus = defaultdict(lambda: {"w": [], "h": [], "ar": [], "area": [], "npi": [], "cx": [], "cy": []})

for r in man:
    lp = label_path(r["stem"], r["split"])
    if not lp.exists():
        continue
    c = r["corpus"]
    lines = [ln.split() for ln in lp.read_text().splitlines() if ln.strip()]
    by_corpus[c]["npi"].append(len(lines))
    for _, cx, cy, w, h in [(x[0], *map(float, x[1:5])) for x in lines]:
        by_corpus[c]["w"].append(w)
        by_corpus[c]["h"].append(h)
        by_corpus[c]["ar"].append(w / h if h else 0)
        by_corpus[c]["area"].append(w * h)
        by_corpus[c]["cx"].append(cx)
        by_corpus[c]["cy"].append(cy)

def q(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))]

print(f"{'corpus':8} {'nimg':>5} {'nbox':>7} {'box/img':>8} "
      f"{'w%img med':>10} {'h%img med':>10} {'w/h med':>9} {'w/h p10':>8} {'w/h p90':>8} "
      f"{'area%img med':>12}")
for c in ("tufts", "dentex", "kaggle", "ufba"):
    d = by_corpus[c]
    if not d["w"]:
        continue
    print(f"{c:8} {len(d['npi']):5d} {len(d['w']):7d} {st.mean(d['npi']):8.1f} "
          f"{100*st.median(d['w']):10.2f} {100*st.median(d['h']):10.2f} "
          f"{st.median(d['ar']):9.3f} {q(d['ar'],0.1):8.3f} {q(d['ar'],0.9):8.3f} "
          f"{100*st.median(d['area']):12.3f}")

print()
print("box CENTER spread (normalized) -- is the annotated region the same part of the image?")
print(f"{'corpus':8} {'cx p5':>7} {'cx p95':>7} {'cy p5':>7} {'cy p95':>7}")
for c in ("tufts", "dentex", "kaggle", "ufba"):
    d = by_corpus[c]
    if not d["cx"]:
        continue
    print(f"{c:8} {q(d['cx'],0.05):7.3f} {q(d['cx'],0.95):7.3f} {q(d['cy'],0.05):7.3f} {q(d['cy'],0.95):7.3f}")

print()
print("aspect-ratio (w/h) histogram, share of boxes per bin:")
bins = [(0, .25), (.25, .4), (.4, .55), (.55, .75), (.75, 1.1), (1.1, 9)]
print(f"{'corpus':8} " + " ".join(f"{a:.2f}-{b:.2f}" for a, b in bins))
for c in ("tufts", "dentex", "kaggle", "ufba"):
    ar = by_corpus[c]["ar"]
    if not ar:
        continue
    row = [sum(a <= x < b for x in ar) / len(ar) for a, b in bins]
    print(f"{c:8} " + " ".join(f"{v:9.2f}" for v in row))
