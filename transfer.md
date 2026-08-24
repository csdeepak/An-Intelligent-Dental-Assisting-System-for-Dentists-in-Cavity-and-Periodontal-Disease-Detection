# CURRENT STATE — read this first

**This file is the project's living state-of-play.** It answers "where are we, what is done,
what is next" for a session that is starting cold. It is **rewritten, not appended to** —
unlike `docs/results/RESULTS_LOG.md` (append-only history) and `docs/session-memory/`
(one file per session, never edited). Those two are the record; this is the snapshot.

**Last updated: 22 August 2026 (seventh update — enumeration head TRAINED, Stage 2 fixed).** Rewritten from a one-off machine-handoff document — the
20–21 Aug handoff it described is complete, and its content is preserved in git history
(`git show ad71ee4:transfer.md`) and in §6 below.

> **Maintenance rule (CLAUDE.md rule 5):** whenever a session finishes something, decides
> something, or changes what should happen next, update §1–§4 here **before the session ends**.
> A stale snapshot is worse than none — it is the exact failure mode `CLAUDE.md` rule 4 exists
> to prevent, and this file has already caused one wasted search (§6).

---

## 1. Where we are, in five lines

**Stage 2 is fixed.** The learned enumeration head lifts FDI accuracy from 28.0% to
**52.2% end-to-end** (72.7% of detected teeth, above the 68.7% ceiling positional assignment
could never cross). The bottleneck has moved to detector recall. We are on **W2 of the 8-week plan** (`docs/research/MASTER_PLAN_2026H2.md` §5; W2 = Aug 22–28,
implementation freeze **14 Oct**, ISBI submission **26 Oct**). Four of six pipeline stages are
trained; **Stages 5–6 do not exist** and are the largest single gap. The Tier-0 credibility
repairs are *prepared but unrun* — every one of them needs a GPU, and **no GPU instance is
provisioned**. The paper's two headline contributions (C1 VLM comparison, C2 external
validation) are at **0%**. Overall ≈35% complete: strong foundation, paper barely started.

**The single highest-leverage action right now: start R4 (Stages 5–6 integration).** It needs
no GPU, all four models are local, and `MASTER_PLAN` §8 flags it High/High as "the historical
long pole."

---

## 2. What is DONE — verified, not assumed

| Item | Evidence |
|---|---|
| **T0.6** detector reconciled, frozen, tagged `tooth-detector-a100-1024-v1.0` | `docs/research/T0.6_detector_reconciliation.md` §1 |
| **T0.7** CEJ labelled as a documented negative result | `PAPER_MATERIAL.md` §5.6/§7.5 |
| **T0.2 (split half)** independent image-level 70/15/15 built **from raw**, not carved from val | `data/dentex/splits_v2.json` (tracked), train 495 / val 103 / test 107 |
| **Universal→FDI bug** fixed, regression-tested; 5 stale docs corrected | `f8b31f8`, `tests/test_fdi_converter.py` |
| **Caries weights** retrieved from Kaggle, hashed, tagged `caries-cascade-resnet18-v1.0` | `models/07_caries_cascade/run_summary.txt` |
| **DENTEX crops** regenerated on the new split | `data/dentex/crops_v2/` — phase1_legacy 2,510/515/504 (+182 extern50); phase2 1,964/408/395 (+133) |
| **R1 seg dataset** built on the frozen split | `data/tufts/dataset_seg/` — 26,005 instances, 700/150/150 |
| **R2 mask-aware cropping** implemented + unit-tested (**unwired** — needs R1's masks) | `src/crop_generator.py`, `tests/test_crop_generator.py` |
| **Caries re-run script** written, smoke-verified on CPU | `scripts/dentex/train_caries_cascade.py` |
| **Stage 2 FDI assignment** built + tested (R4, part 1) | `src/fdi_assignment.py` |
| **Orientation contract** — rotate for detector, un-rotate immediately | `src/orientation.py` |
| **Stage 2 validated** (28.0%) then **FIXED** (52.2%) | `scripts/eval/validate_fdi_assignment.py --method head` |
| **Enumeration head trained** — ResNet18 + positional features | `scripts/dentex/train_enumeration_head.py` |
| Test suite | **45/45 pass** |

**Findings that changed the science** (all in `RESULTS_LOG.md`):
- The bbox detector's ground truth is **missing 66 real teeth** (corrupt `bounding box` fields); test GT holds 3,924 of 3,930. Left unfixed on purpose to preserve the frozen detector.
- The **caries gate's negative class contains no healthy teeth** — `no_caries` is Impacted + Periapical Lesion. Real defect, no fix inside DENTEX's labelled data.
- **DENTEX's subsets cover disjoint patients despite sharing filenames.** Cost one bug (15,531 crops of the wrong patients) before it was caught.
- `DENTEX/disease/` holds **250 images, 1,600 FDI-keyed polygons, 8 classes, 91 explicitly healthy teeth** — leakage-checked, exactly 1 duplicate (`test_181.png` = `train_332.png`). Internal held-out set, **not** external validation.

---

## 3. What is NEXT — ordered, with the real blocker named

1. **R4 — Stages 5–6 integration. IN PROGRESS.** *No blocker.*
   - ✅ **Stage 2 positional FDI assignment built** — `src/fdi_assignment.py`, 11 tests.
     Conventions derived from DENTEX FDI ground truth, not assumed.
   - ✅ **Orientation rule found and must be honoured** — see the warning box below.
   - ✅ **Stage 2 validated against DENTEX FDI ground truth** — 249 images, 1,534 teeth.
     **Negative and important: 28.0% end-to-end FDI exact accuracy.** Quadrant is fine
     (93.0%); the position digit fails because detector recall decays from 98.3% at position 1
     to 61.0% at position 8, and each missed tooth shifts everything distal to it inward.
     `RESULTS_LOG.md` 2026-08-22c, `model_metrics.md` Stage 2, `PAPER_MATERIAL.md` §8.10.
   - ✅ **Enumeration head TRAINED and validated** — **28.0% → 52.2% end-to-end**, 72.7% of
     detected teeth (above the 68.7% ceiling). Trained locally in 48 min on MPS. One-to-one
     Hungarian assignment emits 0 duplicate codes vs 1,013 for plain argmax. Figures in
     `docs/results/figures/enumeration_head/`. `RESULTS_LOG.md` 2026-08-22i.
   - ⬜ **Stage 1 is now the bottleneck** — at 71.8% recall, 71.8% is the end-to-end maximum.
     R1's seg retrain is the prepared lever.
   - ⬜ `scripts/run_inference.py` — still a 38-line placeholder. Stages 5–6 proper.

> ### ⚠️ ORIENTATION — read before running the pipeline on ANY non-Tufts image
> The frozen detector was trained on Tufts' **portrait-space** annotations, i.e. *sideways*
> panoramics. DENTEX, Ningxia and the clinic data are all shipped upright. **Rotate 90°
> COUNTER-CLOCKWISE before inference** — verified against all 1,000 Tufts pairs (1000/1000 CCW,
> 0/1000 CW). Measured against ground truth: upright gives 7.5% recall and 0% FDI accuracy;
> CW 73.7%/21.8%; **CCW 71.5%/26.1%**. Use `src/orientation.py::detect_upright`, which rotates
> and un-rotates as one call. An earlier note here said clockwise — wrong, and it survived a
> visual check because a tooth detector barely notices a 180° flip. `MASTER_PLAN` §8 pre-frames weak cross-dataset
> transfer as "this is the finding", so skipping this would log a preprocessing bug as a
> domain-shift result on C2. Full record: `RESULTS_LOG.md` 2026-08-22b.
2. **Provision the E2E GPU instance.** *Blocker for everything in W2.* `docs/research/GPU_SETUP.md`
   has the verified click-path. Still not launched.
3. **One GPU session, once provisioned:** R1 seg retrain (~6h; criterion pre-registered in
   T0.6 §2 — do not adjust it after seeing results), then both caries arms
   (`train_caries_cascade.py --arm a` / `--arm b`, minutes). That closes T0.1–T0.4.
4. **T0.5 — the Mild n=6 decision.** *No blocker, no compute.* Report 2-class severity as
   headline, 3-class in appendix with bootstrap CIs. Untouched since written.
5. **Reconnect the Ningxia drive.** Images are on an external drive, **not on this machine**
   (`data/ningxia/` holds only `manifest.csv`). W4's external run depends on it. It is
   **external test data — never train on it** (`MASTER_PLAN` §4.1).
6. **Start IRB paperwork.** Flagged as zero-cost since 15 Aug, still not begun.

---

## 4. Decisions PENDING — do not default into these silently

| Decision | Why it needs a human |
|---|---|
| ~~**How to fix FDI numbering.**~~ **RESOLVED 22 Aug — Route B built, trained and validated: 52.2% end-to-end.** Original framing kept for the record: | At 28.0% exact a per-tooth report mislabels ~7 of 10 teeth. ~~Route A: raise posterior detector recall~~ — **measured ceiling 68.7%** even with a complete 8-tooth quadrant, because eight detected teeth are not positions 1–8, they are eight teeth that survived extraction; no detector work breaches that. **Route B: train a per-tooth enumeration head** — DENTEX `quadrant_enumeration` labels 18,095 teeth with quadrant+position across 634 images, on patients disjoint from the `disease/` eval set, so it trains without leaking. ResNet18-scale, minutes of GPU. `RESULTS_LOG.md` 2026-08-22f. | Changes the architecture |
| **Detector-derived not-diseased class?** Running the frozen detector over the 705 disease images and treating unmatched detections as not-diseased is the one sound fix for the gate's negative-class defect — but it puts detector error into training labels. | Trade-off, not a fact |
| **What to use `DENTEX/disease/` (250 imgs, FDI-keyed) for** — honest per-tooth test set / small healthy class / C3 error-propagation substrate. Needs a LabelMe→FDI parser that does not exist. Exclude `test_181.png`. | Scoping call |
| **Clinic data governance.** `index.csv` sits beside `images/` on a shared Drive, which voids the de-identification. Five actions in `clinical_dataset_provenance.md` §4a, all needing the Drive owner. | Not this repo's account |
| **Bone-loss weights have no version tag** — the only trained stage still lacking one. | Trivial, just undone |

---

## 3b. The GPU session — run order, everything in one sitting

All GPU work is rented (user preference, and `MASTER_PLAN` §6 agrees: *"compute is not the
bottleneck… always buy GPU"*). Every script below has been run end to end locally first, so
the rented time is spent training, not debugging.

| # | Job | Command | Est. |
|---|---|---|---|
| ~~1~~ | ~~Enumeration head~~ | **DONE locally, 48 min** — 52.2% end-to-end | ✅ |
| ~~2~~ | ~~Re-validate Stage 2~~ | **DONE** — `--method head` | ✅ |
| 3 | Caries Arm A | `python scripts/dentex/train_caries_cascade.py --arm a` | ~5 min |
| 4 | Caries Arm B | `python scripts/dentex/train_caries_cascade.py --arm b` | ~5 min |
| 5 | **R1 seg retrain** — now the only job that needs renting | `python scripts/yolo/train_yolo_seg.py` | ~40 min on A100 |

**What to upload** (none of it is in git): `data/dentex/enumeration_v1/` 1.7 GB ·
`data/dentex/crops_v2/` 1.2 GB · `data/tufts/dataset_seg/` 474 MB · `models/06_yolo_detection_a100_run/best.pt` ·
plus `DENTEX/disease/{input,label}/` (~1 GB) for step 2. Roughly **4.5 GB**.

**What to bring back:** `outputs/enumeration_head/`, `outputs/stage2_validation/`,
`outputs/caries_rerun/`, and the seg run's `weights/` + `results.csv`.

**Two things not to get wrong:**
- **R1's config is pre-registered** (T0.6 §2): imgsz 1024, batch 32, only model and data
  changed. Do not reduce the batch size to fit — that breaks the comparison the
  pre-registration exists to protect. Rent a card that holds batch 32 at 1024px.
- **Fix `data.yaml`'s absolute `path:`** for the rented machine before step 5.

---

## 4b. Where the documentation lives

`CLAUDE.md` loads automatically every session and points here. After this file:

| Question | File |
|---|---|
| Current numbers | `docs/results/model_metrics.md` |
| Full technical story + honest limitations | `docs/results/PAPER_MATERIAL.md` |
| What happened, when, and why (append-only) | `docs/results/RESULTS_LOG.md` |
| What to work on next | `docs/research/PUBLICATION_TODO.md` status block, sequenced by `MASTER_PLAN_2026H2.md` |
| Narrative of each session | `docs/session-memory/` (newest file) |
| Documentation layout | `docs/README.md` |
| **Pipeline code, and the two contracts easy to get wrong** | **`src/README.md`** |
| Entry points / how to run things | `scripts/README.md`, and `scripts/{yolo,dentex,eval}/README.md` |
| Datasets: what is where, what is usable | `data/README.md` |
| Weights, version tags, what is tracked | `models/README.md` |

Every directory containing code has a README, and all were re-verified 22 Aug 2026.

---

## 5. Local state that git does NOT carry

| Item | Where | Note |
|---|---|---|
| DENTEX full release (~14 GB) | `~/Downloads/Capstone/DENTEX/` | Complete and verified. Subset map in `data/README.md`. |
| Tufts raw + rotated radiographs | `_repo_archive/datasets_workspace/` | 1,000 each; `Radiographs_rotated/` is what scripts expect |
| Tufts frozen split | `_repo_archive/datasets_workspace/outputs/eda_tufts/split_v1.csv` | Gitignored — which is why a previous session wrongly declared it lost |
| Ningxia images | **External drive, disconnected** | Only `manifest.csv` is in-repo |
| Clinic (SDH) data | Not on this machine | Governance-blocked |
| torch/cv2 | **Not installed in any repo env** | A scratch venv was used for verification; it is outside the repo |
| E2E instance / SSH keys | Account-level | No instance launched. Treat the `.pem` pasted on 20 Aug as compromised. |

---

## 6. History — the 20–21 Aug machine handoff (closed)

This file began as a one-off handoff to a second laptop. That handoff is complete: the
uncommitted work was committed and pushed, and the machine switch happened. Two of its claims
turned out to be **wrong**, and both are worth remembering as cautionary examples:

- It declared `outputs/eda_tufts/split_v1.csv` missing after an "exhaustive search". The search
  covered `C:\` and `D:\` — a Windows filesystem — while the repo lives on macOS. The file was
  there all along.
- Its §4 table said the Tufts data would need re-downloading. It was already local.

Full original text: `git show ad71ee4:transfer.md`.
