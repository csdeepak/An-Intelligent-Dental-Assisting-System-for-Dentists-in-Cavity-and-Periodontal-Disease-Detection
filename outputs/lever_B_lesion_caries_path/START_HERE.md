# Lever B — start here (cold-start handoff, updated 3 Sep 2026)

**Status: NOT STARTED.** Pre-registration drafted (`PRE_REGISTRATION.md`), bars **not yet frozen**.
Nothing trained. Next lever in the accepted plan
(`docs/session-memory/2026-09-02c-score-lever-council-and-plan.md` §5, `transfer.md` §3).

**What Lever B is:** a caries **lesion detector** (YOLOv11l, single class) wired in as a Stage-3
alternative to the caries *gate*, scored **frozen** on the exact lesion-agreement metric an
image-blind constant currently wins (`PAPER_MATERIAL.md` §8.22/§8.24/§8.25). It is the remaining
shot at an *adoptable* positive headline number. Every outcome (wins / floods / fails-to-transfer
/ nulls) is a publishable finding — see `PRE_REGISTRATION.md` §6.

---

## Where this sits in the order of work (`transfer.md` §3)

| # | task | owner | GPU | needs |
|---|---|---|---|---|
| **A** | **Phase 0** — finish the Tufts Guard-2 diagnosis write-up (`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` §3) | **the user**, on their Mac — everything it needs is already there | no | `data/detector_multicorpus_v2/` (514 MB, gitignored) + `models/15/*.pt` (local-only) |
| **B** | freeze the Lever B pre-reg bars (`PRE_REGISTRATION.md` §4–§6, one review round) | user / mentor — async, can overlap A | no | — |
| **C** | put the weights + data on Drive (see §0) | user (account owner) | no | — |
| **D** | **Lever B** — this document | **the friend** | only the B-pooled run | C done, B done |

**Phase 0 is first, but it is the user's** — it is unblocked on their Mac and closes an open
loop, whereas on a fresh laptop it needs the same 514 MB dataset + checkpoints as everything
else. Do **not** wait for Phase 0 to start Lever B once C + B are done; they are parallel.

---

## 0 · What a fresh laptop is missing (task C)

This repo tracks **code, docs, results, and small (<50 MB) checkpoints only.** Obtain, outside git:

| need | where | for |
|---|---|---|
| **DENTEX** dataset | Drive (`docs/EXTERNAL_DRIVE.md`, "DENTEX" folder) → `~/Downloads/Capstone/DENTEX/` | `training_data/quadrant-enumeration-disease/train_quadrant_enumeration_disease.json` (B-pooled train) + `disease/` (164-image DENTEX eval) |
| **CariesXrays** dataset | Drive / original AAAI 2024 release → `~/Downloads/Capstone/CariesXrays_Dataset/` | 6,000 images — the primary training corpus + the seed-43 eval draw |
| **Ningxia** dataset | user only (restrictive licence, local-only, **never trained/tuned on**) → `~/Downloads/Capstone/ningxia_local/` | one of the 3 eval cohorts — needed at Step 5 only |
| `models/14_cariesxrays_lever2/best.pt` | **local-only on the user's Mac — NOT on Drive.** Ask the user to upload it (`docs/EXTERNAL_DRIVE.md`). | **this is the B-single arm** — Step 3 cannot run without it |
| `models/11_yolo_seg_tufts_r1/best.pt` | **NOT on Drive** (`docs/EXTERNAL_DRIVE.md` §"Model checkpoints") | the pipeline default detector — maps lesions → teeth at eval (Step 5) |
| `models/09_caries_gate_v3/caries_gate_v3.pth` | DENTEX drive, `capstone_checkpoints/` (`docs/EXTERNAL_DRIVE.md`) | the gate-v3.0 comparator (Step 5) |
| `models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` | **tracked in git (43 MB)** ✅ | already present |

**Python:** an env with `torch` + `ultralytics==8.4.127` (the project pins this exact version).
On the user's Mac: `/opt/anaconda3/bin/python3`. **GPU** only for the B-pooled training run
(~₹300, A100-40GB) — all data prep and all eval is CPU.

---

## 1 · The plan (distilled from `PRE_REGISTRATION.md`)

### Step 1 — freeze the bars (task B, no code)
`PRE_REGISTRATION.md` is a **draft**. One review round with the user/mentor on §4 (eval cohorts),
§5 (comparators + metric), §6 (acceptance rule); then it is frozen and the build starts.
**Do not train before this.** (Data prep — Step 2 — implements §3/§4, which are marked "fixed
now"; it is low-risk to start, but redo it if the review changes §3 or §4.)

### Step 2 — local data prep (no GPU), then the §8 gate

**2a. Rebuild `data/cariesxrays_det/`** — it is gitignored and **not present on any machine**:
```
python scripts/yolo/build_cariesxrays_detector_dataset.py     # SEED=42, 80/20 -> 4,800 train / 1,200 val
```
(This is *this project's* seeded split, not the FPCL 4,800/1,200 split, which is not public —
see the script docstring. B-single's `models/14` was trained on this exact split.)

**2b. DENTEX `quadrant-enumeration-disease` → YOLO caries-box converter** (new, small script):
- Source: `train_quadrant_enumeration_disease.json` — **705 images, 650 with ≥1 caries box, ~2,767 caries+deep_caries boxes**.
- **Category filter:** the JSON has **`categories_3`** (there is no `categories` key), mapping
  `{0: Impacted, 1: Caries, 2: Periapical Lesion, 3: Deep Caries}`. Keep annotations with
  **`category_id_3 ∈ {1, 3}`** — this is already the project constant
  **`CARIES_CLASSES = {1, 3}` in `scripts/dentex/build_dentex_crops.py`** (reuse it, don't reinvent).
- **Boxes:** `bbox` is COCO `[x, y, w, h]` (top-left + width/height). Image dimensions come from
  the JSON **`images`** block (`width`/`height` are present, e.g. 2744×1316) — **not** from
  decoding the image. *(The "dims from the decoded image, XML `<size>` is 27.3 % wrong" gotcha
  in `PRE_REGISTRATION.md` §8.1 / `RESULTS_LOG` 2026-08-27a is a **CariesXrays / VOC-XML** issue,
  already handled by `build_cariesxrays_detector_dataset.py` — it does not apply to DENTEX COCO JSON.)*
- Round-trip COCO `[x,y,w,h]` → YOLO-norm `[cx,cy,w,h]` → pixel to ≤ 1 px.
- These are **tooth**-level boxes (coarser than CariesXrays lesion boxes) — recorded as expected
  in `PRE_REGISTRATION.md` §3; they are a domain adapter, not the primary signal.

**2c. B-pooled training set** = CariesXrays seed-42 train (4,800) **+** the converted DENTEX
caries boxes (650 imgs), balanced per Lever A's recipe (§3 of
`outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md`).

**2d. Fresh CariesXrays eval draw** — random **1,500 images, seed 43** drawn from the **1,200
held-out val IDs + any unused train IDs**, verified **0-overlap** with the 4,800 `data/cariesxrays_det/`
train images. This is NOT `build_cariesxrays_detector_dataset.py --seed 43` (that reshuffles the
whole split) — it is a small separate draw. Seed 43, not 42/§8.25, is pre-registered: a "reuse
the §8.25 draw" shortcut is visibly against the pre-reg.

**2e. §8 local gate — all must pass before renting:**
- CariesXrays box dims from the decoded image, never the XML `<size>` (handled in 2a's script).
- DENTEX boxes round-trip to ≤ 1 px; `category_id_3 ∈ {1,3}` filter verified against `categories_3`.
- 0 MD5 overlap between CariesXrays-train and the DENTEX images; 0 overlap CariesXrays-train vs the seed-43 draw.
- ≥ 12 rendered samples per source, boxes on lesions, eyeballed.

### Step 3 — B-single (zero GPU)
Re-use `models/14_cariesxrays_lever2/best.pt` **as-is**, no training. Run it frozen through the
eval (Step 5).

### Step 4 — B-pooled (~₹300, one GPU run)
One YOLOv11l `detect` run, ~5,500 images, 1024 px, 120/25 epochs (Lever 2's proven budget) on an
A100-40GB. Follow `transfer.md` §6 runbook: `tar` + sha256 the dataset, upload, **delete `._*`
AppleDouble files**, **re-run the §8 gate on the box**, then train. Download `best.pt` + sha256 +
**destroy the instance**. One redo budgeted ⇒ ~₹600 ceiling.

### Step 5 — eval (all CPU), frozen
Predictions → mapped to the containing/nearest detected tooth (detector = `models/11`, the
pipeline default) → the **existing** matchers, no new matching code:

| cohort | source | script + matcher |
|---|---|---|
| DENTEX | 164 leak-free `disease/` images, **479 çürük** | `scripts/eval/lesion_localization.py` (`--min-iou 0.30` + centroid fallback) |
| Ningxia | 4 hospitals, all splits, **1,013 caries** | `scripts/eval/ningxia_external.py` (`match_by_centroid`) |
| CariesXrays | the fresh seed-43 1,500 draw, **~3,400 lesions** | `scripts/eval/cariesxrays_external.py` (imports `ningxia_external.match_by_centroid`) |

`cariesxrays_external.py` and `lesion_localization.py` both take `--detector`; pass the lesion
model there (as done for Lever A's Guard 1). Comparators, per cohort, **one metric**
(lesion-localisation agreement; paired cluster bootstrap over images, 10k, seed 42):
**lesion detector** vs **caries gate v3.0** vs **image-blind constant** `{16,17,26,27,36,37,46,47}`.
**Always report** predicted-positive rate and predicted-positive match rate (`PRE_REGISTRATION.md`
§5 — a detector trivially wins recall by flagging everything). Current seg-detector +
gate-v3 baseline on DENTEX is 212/479 = 0.443 (`PAPER_MATERIAL.md` §8.11); the constant is 0.488
(§8.22).

### Step 6 — acceptance (`PRE_REGISTRATION.md` §6; bar NOT moved after seeing numbers)
Wire in as Stage 3 IFF, for the better of B-single / B-pooled: (1) lesion agreement > the
constant's, 95 % CI excluding 0, on **≥ 2 of 3 cohorts**; AND (2) predicted-positive rate ≤ 1.5×
the constant's on those cohorts; AND (3) also beats gate v3.0 on those cohorts. Otherwise the
gate is retained and the outcome is written per the §6 table. **If wired in → full downstream
pipeline re-run**, and every result → `RESULTS_LOG.md` + `model_metrics.md` + `PAPER_MATERIAL.md`.

---

## 2 · Hard rules (do not break — `CLAUDE.md`, `transfer.md`)

- **Never train or tune on Ningxia.** Locked external test. Scored exactly once, frozen.
- **Never train on DENTEX `disease/`** — its 164 leak-free images are the eval set. (B-pooled uses
  `quadrant-enumeration-disease`, a *different* DENTEX subset — `PRE_REGISTRATION.md` §3.)
- Pre-register before building; **the bar is not moved after seeing any number.**
- Every result → `RESULTS_LOG.md` (append, never edit) + `model_metrics.md` + `PAPER_MATERIAL.md`
  if paper-relevant; every session → a `docs/session-memory/` file; rewrite `transfer.md` §1–§4.
- Commit with **explicit paths** (not `git add -A`); **never `git push` without being asked**;
  never `--no-verify`; preserve each file's CRLF/LF (`transfer.md`, `docs/results/*`,
  `models/README.md`, `scripts/eval/README.md`, `.gitignore` are CRLF; most else is LF).
- Track A (manuscript + compliance) wins any time conflict.
