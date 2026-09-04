# `scripts/dentex/` — Stage 2 enumeration head + Stage 3 caries toolchain

**Written 22 August 2026; caries-signal section updated 1 September 2026.** These scripts replace a set of Google Drive notebooks that
were the only way the DENTEX caries data had ever been built — they existed nowhere in this
repo despite being the provenance of every reported caries number. Those notebooks are now
preserved at `notebooks/caries/dataset_construction/`.

Run order — Stage 3: **split → crops → train**. Stage 2: **enumeration crops → train head → validate**.

### Stage 2 — the FDI enumeration head (the current numbering method)

| Script | Status | What it does |
|---|---|---|
| `build_enumeration_crops.py` | ✅ run — 33,461 crops | Tooth crops labelled with FDI, from DENTEX `quadrant_enumeration` (634 images, 18,095 teeth, all 32 classes). Split **by image**; 1.5× expansion; ±15% jitter on train only. Output `data/dentex/enumeration_v1/` (gitignored). |
| `train_enumeration_head.py` | ✅ trained — 15 epochs, 48 min on local MPS | ResNet18 over the crop **concatenated with four positional features**, two heads (quadrant 4-way, position 8-way). Weights + figures to `outputs/enumeration_head/`. |

**Result: 22.9% → 46.5% end-to-end FDI accuracy** (69.4% of detected teeth), measured on 164
leak-free `DENTEX/disease/` images by `scripts/eval/validate_fdi_assignment.py --method head`.
On complete (8-detection) quadrants — rank-order's best case — it scores **80.2%** against
positional's **66.3%** ceiling, a **+13.9 point** margin on an identical population (n=101).
*(Corrected 24 Aug 2026: previously stated as a 67.0% ceiling and +2.4 points — 67.0% is the
detector's recall. RESULTS_LOG 2026-08-24a.)*

**Why positional features, and why no horizontal flip.** Teeth 16 and 26 are near mirror
images, as are 36/46 and every other left/right pair. Normalised x helps disambiguate them —
worth **+3.2 points of laterality** and +2.8 FDI exact, measured by
`scripts/eval/ablate_head_inputs.py`. *(This previously claimed laterality was "not recoverable
from crop pixels" and that a crop-only classifier "would guess half of every label". Measured:
the image alone recovers side at **96.3%**. The features are a refinement, not the load-bearing
element. RESULTS_LOG 2026-08-24c.)* Independently of that, horizontal flip **inverts** the
quadrant label and must stay excluded from augmentation — that reasoning never depended on
what the model can recover. DPML (Cao et al., *ESWA* 254:124446, 2024) §3.4 argues the same design
independently, and sidesteps the problem entirely by collapsing mirrored pairs into 8 classes —
which FDI's 32 cannot do.

**The evaluation set overlaps this training set.** 85 of the 250 `DENTEX/disease/` images are
byte-identical to enumeration training images. They are excluded via
`data/dentex/disease_leaked_images.json`. Anything trained here must be scored with that
exclusion applied, or the number is inflated (it was, by 5.7 points, before this was caught).

**This is v1.0 (DENTEX only) — not the current pipeline default.** `train_enumeration_head.py`
now also accepts `../tufts/build_enumeration_crops.py`'s output; a head trained on both
corpora (`fdi-enumeration-head-resnet18-v2.0`) is what `run_inference.py` loads by default as
of 26 Aug 2026. It does not change the number above (46.5% end-to-end is still what v1.0
measures, and v2.0 lands within 0.1pp of it) — v2.0 was adopted for a different reason
entirely: it gains +21.5 points on a second machine population (Tufts) that v1.0 never saw.
See `../tufts/README.md` and `../../models/README.md` "Which FDI head to use" before assuming
which head a given number came from.

### Stage 3 — caries data + training

| Script | Status | What it does |
|---|---|---|
| `fetch_dentex_subsets.py` | ✅ run 27 Aug | Downloads + integrity-checks the exact DENTEX subsets this repo uses (`quadrant-enumeration-disease`, `quadrant_enumeration`, `validation_data/.../xrays`). Every PNG opened, every JSON parsed on download. |
| `build_dentex_split_from_raw.py` | ✅ run, output committed | Draws the frozen image-level 70/15/15 split from the raw 705 disease X-rays. Stratified on each image's 4-bit disease presence-vector; largest-remainder allocation per stratum. Output `data/dentex/splits_v2.json` (**tracked**). |
| `build_dentex_crops.py` | ✅ run, output gitignored | Regenerates every caries crop honouring that split. Output `data/dentex/crops_v2/`. |
| `build_caries_phase1_v3.py` | ✅ run — default path reproduces the frozen v3 corpus exactly | Builds the Phase-1 caries-gate crops. Default output is byte-for-byte the pinned v3.0 corpus (4,750/1,003/863, 5,366 healthy). **Opt-in flags added 31 Aug for the signal experiments** (all default off): `--include-disease-only` (adds the 444 disease-only images as positives), `--clahe` (CLAHE clip 2.0, 8×8 on source), `--crop-expand 1.25`, `--eval-pool` (MD5 leakage guard — refuses `train_332.png` ≡ `test_181.png`). |
| `train_caries_cascade.py` | ✅ run locally on MPS (31 Aug); no GPU needed — ResNet18 @ 224 over ~6.6k crops is not compute-bound | The T0.1–T0.4 re-run block in one artifact: both augmentation arms, macro-F1 selection, cosine schedule, val/test reported separately, gate report saved. **`--balance-position` added 31 Aug** — a `WeightedRandomSampler` equalising each (tooth type × label) cell, one of the three signal arms. |
| `split_dentex_holdout.py` | ❌ **SUPERSEDED — do not run** | The old carve-a-test-set-out-of-val fallback, written when raw DENTEX was believed unreachable. Kept per `CLAUDE.md` rule 3; its docstring explains the soft leak it carried. |
| `build_dentex_caries_boxes.py` | ✅ run 4 Sep — 650 images, 2,767 boxes | **Lever B domain adapter**: `quadrant-enumeration-disease` (705 images) → YOLO caries boxes, single class `decay` (same class name as `scripts/yolo/build_cariesxrays_detector_dataset.py`, so the two pool cleanly). Reuses `CARIES_CLASSES = {1,3}` from `build_dentex_crops.py` rather than redefining it. Dims from the JSON `images` block, cross-checked against the decoded image shape (0 mismatches required). **Leakage gate**: live-verifies 0 MD5 overlap between the written training images and the *currently-scored* DENTEX `disease/` eval cohort (never hardcodes the exclusion list) — one candidate overlap exists (`test_181.png` == `train_332.png`) and is already excluded from the 164-image eval set for an unrelated reason, verified rather than assumed. These are whole-**tooth** boxes, coarser than CariesXrays' lesion boxes — a domain adapter, not a second lesion-box source. `RESULTS_LOG.md` 2026-09-04f. |

**Caries signal experiments, 31 Aug – 1 Sep — 7 attempts, all negative, all recorded.** The
caries branch precision/recall question was diagnosed (`scripts/eval/caries_position_bias.py`:
the gate scores teeth partly by *which tooth it is* — 48.2% of healthy molars flagged) and then
attacked: threshold tuning, per-stratum thresholds, gate v4 on 2.67× the positives, CLAHE, a
1.25× crop, position-balanced sampling. Every paired ΔAP/ΔF1 CI spans zero. **Nothing was
adopted; v3.0 stays pinned.** The DENTEX blocker is ~34 held-out source images, not method —
`RESULTS_LOG.md` 2026-08-31 / 08-31b, `PAPER_MATERIAL.md` §8.24,
`docs/session-memory/2026-08-31-caries-position-bias-and-v4.md`. The follow-on (Lever 2/3 on the
13× larger CariesXrays corpus) is `transfer.md` §3 Track B, not started.

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

---

**Publication target and grading criteria:** `../../transfer.md` §5.
