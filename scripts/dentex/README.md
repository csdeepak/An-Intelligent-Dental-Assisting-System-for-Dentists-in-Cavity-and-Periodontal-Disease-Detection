# `scripts/dentex/` — Stage 3 caries data + training toolchain

**Written 22 August 2026.** These four scripts replace a set of Google Drive notebooks that
were the only way the DENTEX caries data had ever been built — they existed nowhere in this
repo despite being the provenance of every reported caries number. Those notebooks are now
preserved at `notebooks/caries/dataset_construction/`.

Run order: **split → crops → train**.

| Script | Status | What it does |
|---|---|---|
| `build_dentex_split_from_raw.py` | ✅ run, output committed | Draws the frozen image-level 70/15/15 split from the raw 705 disease X-rays. Stratified on each image's 4-bit disease presence-vector; largest-remainder allocation per stratum. Output `data/dentex/splits_v2.json` (**tracked**). |
| `build_dentex_crops.py` | ✅ run, output gitignored | Regenerates every caries crop honouring that split. Output `data/dentex/crops_v2/`. |
| `train_caries_cascade.py` | ⏳ smoke-tested, **needs GPU** | The T0.1–T0.4 re-run block in one artifact: both augmentation arms, macro-F1 selection, cosine schedule, val/test reported separately, gate report saved. |
| `split_dentex_holdout.py` | ❌ **SUPERSEDED — do not run** | The old carve-a-test-set-out-of-val fallback, written when raw DENTEX was believed unreachable. Kept per `CLAUDE.md` rule 3; its docstring explains the soft leak it carried. |

## Why the split was rebuilt rather than carved

`split_dentex_holdout.py` could only cut the existing val pool in two, and val had already
been used repeatedly to select among model variants — so whichever half became "test"
inherited a soft leak. Splitting the raw source images **before any crop exists** makes
crop-level leakage structurally impossible: every crop inherits its source image's split.

Verified on the output: zero image-id and zero filename overlap across all three split pairs,
705/705 images and 3,529/3,529 annotations accounted for, and the manifest is byte-identical
on re-run.

## Two things that will bite you

**1. The Phase-1 negative class contains no healthy teeth.** The rule is
`category_id_3 in [1,3] → caries, else → no_caries`, applied to a file where *every*
annotation is a diseased tooth. So `no_caries` is exactly Impacted + Periapical Lesion (762
train / 49 val). The gate is really "caries vs other-pathology" while the assembled pipeline
would feed it every tooth the detector finds. Real defect, no fix inside DENTEX's labelled
data — see the next point for why the obvious fix fails. Recorded as a limitation inside every
`results.json` the trainer writes.

**2. DENTEX's subsets cover disjoint patients despite sharing filenames.**
`quadrant_enumeration/train_0.png` is a **different person's scan** from
`quadrant-enumeration-disease/train_0.png` — 622 of 634 shared filenames differ in dimensions,
and a visual check settles it. Deriving "healthy" teeth by joining the two on filename
produced 15,531 crops of the wrong patients before it was caught. `build_dentex_crops.py` now
**refuses `--enum` outright** and prints the dimension evidence, because the filename overlap
makes that join look plausible. Full record: `docs/results/RESULTS_LOG.md` 2026-08-21m.

## The crop contract

Reproduced from the original notebooks and **verified pixel-for-pixel** against their real
output: four crops regenerated from source X-rays, three bit-identical, the fourth off by ±1
grey level on the only both-dimensions-downscale (a cv2 version difference in the bilinear
path, not a logic difference).

- crop = raw COCO `bbox`, floor near corner / ceil far edge, clipped. **No expansion at all** —
  unlike the bone-loss track's 1.5×W / 2.0×H.
- `cv2.resize` to 224×224, `INTER_LINEAR`, no aspect preservation, no padding.
- BGR 3-channel PNG via OpenCV.
- filename `{image_stem}_{d}{annotation_id}.png` — names the source image directly, unlike the
  notebooks' `{image_id}_{ann_id}.png`, where `image_id` was a COCO id local to its own file.

## Data location

The DENTEX release lives outside the repo at `~/Downloads/Capstone/DENTEX/`. See
`data/README.md` for the full subset map and which parts are usable.
