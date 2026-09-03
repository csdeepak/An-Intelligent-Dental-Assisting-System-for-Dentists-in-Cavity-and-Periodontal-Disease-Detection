# Lever B — start here (cold-start handoff, 3 Sep 2026)

**Status: NOT STARTED.** Pre-registration drafted (`PRE_REGISTRATION.md`), bars **not yet frozen**.
Nothing trained. This is the next lever in the accepted plan
(`docs/session-memory/2026-09-02c-score-lever-council-and-plan.md` §5, `transfer.md` §3).

**What Lever B is:** a caries **lesion detector** (YOLOv11l, single class) wired in as a Stage-3
alternative to the caries *gate*, scored **frozen** on the exact lesion-agreement metric an
image-blind constant currently wins (`PAPER_MATERIAL.md` §8.22/§8.24/§8.25). It is the remaining
shot at an *adoptable* positive headline number. Every outcome (wins / floods / fails-to-transfer
/ nulls) is a publishable finding — see `PRE_REGISTRATION.md` §6.

---

## 0 · Before you can run anything — what a fresh laptop is missing

This repo tracks **code, docs, results, and small (<50 MB) checkpoints only**. You must obtain,
outside git:

| need | where | notes |
|---|---|---|
| **DENTEX** dataset | Drive (`docs/EXTERNAL_DRIVE.md`, "DENTEX" folder) → put at `~/Downloads/Capstone/DENTEX/` | need `training_data/quadrant-enumeration-disease/train_quadrant_enumeration_disease.json` (B-pooled train) + `disease/` (164-image eval set) |
| **CariesXrays** dataset | Drive / original AAAI 2024 release → `~/Downloads/Capstone/CariesXrays_Dataset/` | 6,000 images; `data/cariesxrays_det/` (the seed-42 split) is **regenerable** with `scripts/yolo/build_cariesxrays_detector_dataset.py`, not in git |
| **Ningxia** dataset | user only — restrictive licence, local-only, **never trained/tuned on** | `~/Downloads/Capstone/ningxia_local/`; eval cohort ×4 hospitals |
| `models/14_cariesxrays_lever2/best.pt` | **local-only on the user's Mac — not on Drive yet** | this **is** the B-single arm. Ask the user to upload it (same gap as `models/11`, `models/13`, `models/15` — `transfer.md` §3 Track A item, `docs/EXTERNAL_DRIVE.md`) |
| `models/11_yolo_seg_tufts_r1/best.pt` | **not on Drive yet** (`docs/EXTERNAL_DRIVE.md` §"Model checkpoints") | the pipeline default detector; needed to map lesions → teeth at eval |
| `models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` | **tracked in git (43 MB)** ✅ | already here |

Python: use a env with `torch` + `ultralytics==8.4.127` (the project pins this). On the user's
Mac that is `/opt/anaconda3/bin/python3`; on yours, whatever has those. GPU only needed for the
B-pooled training run (~₹300 on an A100-40GB) — **all eval is CPU**.

---

## 1 · The plan (from `PRE_REGISTRATION.md`)

### Step 1 — freeze the bars (no code)
`PRE_REGISTRATION.md` is a **draft**. One review round with the user/mentor on §4 (eval cohorts),
§5 (comparators + metric), §6 (acceptance rule), then it is frozen and the build starts. Do not
start training before this.

### Step 2 — local data prep (no GPU), with the §8 gate

1. **B-pooled training set** = CariesXrays seed-42 train (4,800 imgs, `data/cariesxrays_det/`)
   **+** DENTEX `quadrant-enumeration-disease` `caries` + `deep_caries` **tooth** boxes (705 imgs)
   from `train_quadrant_enumeration_disease.json`. Balanced per Lever A's recipe (§3 of
   `outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md`).
   - Write a `DENTEX quadrant-enumeration-disease → YOLO caries-box` converter. **Reuse**
     `scripts/yolo/build_cariesxrays_detector_dataset.py`'s image-dims-from-decoded-image logic
     (the XML `<size>` field is 27.3 % wrong — `RESULTS_LOG.md` 2026-08-27a).
   - COCO → YOLO-norm → pixel round-trip within 1 px; verify the caries/deep_caries category ids
     against the JSON `categories` block.
2. **Fresh CariesXrays eval draw** — random **1,500 images, seed 43** (NOT the training/§8.25
   seed 42), drawn from the 1,200 held-out val IDs + unused train IDs, **verified 0-overlap**
   with `data/cariesxrays_det/` train. This disjointness is pre-registered — a "just reuse the
   §8.25 draw" shortcut is visibly against the pre-reg.
3. **§8 local gate** (all must pass before renting):
   - CariesXrays box dims from the decoded image, never the XML `<size>`.
   - DENTEX boxes round-trip COCO → YOLO-norm → pixel to ≤ 1 px; category filter verified.
   - 0 MD5 overlap between the two training sources; 0 overlap CariesXrays-train vs seed-43 draw.
   - ≥ 12 rendered samples per source, boxes on lesions, eyeballed.

### Step 3 — B-single (zero GPU)
Re-use `models/14_cariesxrays_lever2/best.pt` **as-is** — no training. Run it frozen through the
eval (Step 5).

### Step 4 — B-pooled (~₹300, one GPU run)
One YOLOv11l `detect` run, ~5,500 images, 1024 px, 120/25 epochs (Lever 2's proven budget) on an
A100-40GB. Follow `transfer.md` §6 runbook: `tar` + sha256 the dataset, upload, delete `._*`
AppleDouble files, **re-run the §8 gate on the box**, then train. Download `best.pt` + sha256 +
**destroy the instance**.

### Step 5 — eval (all CPU), frozen
Predictions → mapped to containing/nearest detected tooth (detector = pipeline default) → the
**existing** matchers, no new matching code:

| cohort | source | matcher |
|---|---|---|
| DENTEX | 164 leak-free `disease/` images (479 çürük) | `scripts/eval/lesion_localization.py` (IoU 0.30 + centroid) |
| Ningxia | 4 hospitals, all splits (1,013 caries) | `scripts/eval/ningxia_external.py` `match_by_centroid` |
| CariesXrays | the fresh seed-43 1,500 draw (~3,400 lesions) | `scripts/eval/cariesxrays_external.py` centroid matcher |

Comparators, per cohort, **one metric** (lesion-localisation agreement, paired cluster bootstrap
over images, 10k, seed 42): the **lesion detector** vs **caries gate v3.0** vs the **image-blind
constant** `{16,17,26,27,36,37,46,47}`. **Always report** predicted-positive rate and
predicted-positive match rate (§5 — a detector trivially wins recall by flagging everything).

### Step 6 — acceptance (`PRE_REGISTRATION.md` §6, bar NOT moved after seeing numbers)
Wire in as Stage 3 IFF, for the better of B-single / B-pooled: (1) lesion agreement > the
constant's, CI excluding 0, on ≥ 2 of 3 cohorts; AND (2) predicted-positive rate ≤ 1.5× the
constant's on those cohorts; AND (3) also beats gate v3.0 on those cohorts. Otherwise the gate is
retained and the outcome is written per the §6 table. **If wired in → full downstream pipeline
re-run.**

---

## 2 · Optional warm-up first — Phase 0 of the Tufts Guard-2 diagnosis (no GPU, ~half a day)

Independent of Lever B, cheap, and it is paper material. See
`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` §3 Phase 0:
GT-box overlays (15 Tufts + 15 DENTEX), extend `models/15_detector_multicorpus_leverA/repro/diagnostics/iou_diag.py`
to Arm 4C and conf {0.10, 0.25, 0.40}, then write `PAPER_MATERIAL.md` §8.10 (mechanism) + §8
Known Limitations. Needs `data/detector_multicorpus_v2/` + `models/15/*.pt` (both local-only —
ask the user).

---

## 3 · Hard rules (do not break — `CLAUDE.md`, `transfer.md`)

- **Never train or tune on Ningxia.** Locked external test. Scored exactly once, frozen.
- **Never train on DENTEX `disease/`** — its 164 leak-free images are the eval set.
- Pre-register before building; **the bar is not moved after seeing any number.**
- Every result → `RESULTS_LOG.md` (append) + `model_metrics.md` + `PAPER_MATERIAL.md` if
  paper-relevant; every session → a `docs/session-memory/` file; update `transfer.md` §1–§4.
- Commit with explicit paths (not `git add -A`); never `git push` without being asked; preserve
  each file's CRLF/LF.
- Track A (manuscript + compliance) wins any time conflict.
