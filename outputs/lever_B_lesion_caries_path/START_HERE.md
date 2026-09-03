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

## Ownership + order of work (`transfer.md` §1/§3)

| # | task | owner + machine | GPU |
|---|---|---|---|
| **A** | **Phase 0** — finish the Tufts Guard-2 diagnosis write-up (`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` §3) → `PAPER_MATERIAL.md` §8.10 | **the user, on the Mac** — has the 514 MB `data/detector_multicorpus_v2/` + `models/15/*.pt` locally | no |
| **A2** | **Lever A2** — the conditional multi-corpus detector retry (`TUFTS_GUARD2_DIAGNOSIS.md` §3 Phase 1 gate + Phase 2) | **the user, on the Mac** — only if Lever B yields no adoptable headline | yes, later |
| **B** | freeze the Lever B pre-reg bars (`PRE_REGISTRATION.md` §4–§6, one review round) | user / mentor — async | no |
| **C** | get the datasets + `models/14` to the friend (see `WINDOWS_SETUP.md`) | user (account owner) | no |
| **D** | **Lever B** — this document | **the friend, on Windows** — `WINDOWS_SETUP.md` first | only the B-pooled run |

**A/A2 (user, Mac) and D (friend, Windows) run in parallel — D is not gated on A.** The Lever B
bars (B) do gate D's *training*; data prep can start once §0 files are in place.

**Windows friend: read [`WINDOWS_SETUP.md`](WINDOWS_SETUP.md) first.** Three checkpoints
(`models/09`, `10`, `11`) are now committed to git — a `git pull` brings them in. The datasets
and `models/14` are still separate (they cannot go in git — 25 GB + the Tufts licence).

---

## 0 · Files — what's in git now, and what still isn't

**Committed to git as of 3 Sep 2026** (a `git pull` brings them — `WINDOWS_SETUP.md` §1):

| file | size | for |
|---|---|---|
| `models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` | 43 MB | FDI head |
| `models/11_yolo_seg_tufts_r1/best.pt` | 53 MB | `DEF_DETECTOR` — lesion → tooth mapping at eval |
| `models/09_caries_gate_v3/caries_gate_v3.pth` | 43 MB | gate-v3.0 comparator |

**Still outside git — cannot go in (25 GB of data + the Tufts licence forbids redistribution):**

| need | where | for |
|---|---|---|
| **CariesXrays** raw | Drive / AAAI 2024 release → `~/Downloads/Capstone/CariesXrays_Dataset/` | B-pooled training corpus + the seed-43 eval draw. `data/cariesxrays_det/` (the built split) regenerates from this |
| **DENTEX** `training_data/` + `disease/` | already on the 27-Aug Windows machine, else the DENTEX Drive / `scripts/dentex/fetch_dentex_subsets.py` → `~/Downloads/Capstone/DENTEX/` | `quadrant-enumeration-disease/…disease.json` (B-pooled boxes) + `disease/` (164-image eval) |
| **Ningxia** | **user only** (restrictive licence) | 3rd eval cohort. If unavailable to the friend → run 2 of 3, note Ningxia pending (`WINDOWS_SETUP.md` §2) |
| ⚠️ `models/14_cariesxrays_lever2/weights/best.pt` | **missing everywhere** — see `WINDOWS_SETUP.md` §4 | the **B-single** arm — locate, retrain, or drop |

**Python:** `torch` + `ultralytics` (the Windows env's 8.4.130 is fine for prep + eval; `pip
install ultralytics==8.4.127` before the B-pooled **training** run only). **GPU** only for
B-pooled (~₹300, A100-40GB) — all data prep and all eval is CPU.

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
Re-use `models/14_cariesxrays_lever2/weights/best.pt` **as-is**, no training. Run it frozen
through the eval (Step 5). **⚠️ this file is currently missing** — resolve per `WINDOWS_SETUP.md`
§4 (locate / retrain / drop B-single) before this step.

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
