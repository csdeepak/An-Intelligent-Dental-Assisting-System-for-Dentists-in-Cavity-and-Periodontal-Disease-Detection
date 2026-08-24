# CURRENT STATE — read this first

**This file is the project's living state-of-play.** It answers "where are we, what is done,
what is next" for a session that is starting cold. It is **rewritten, not appended to** —
unlike `docs/results/RESULTS_LOG.md` (append-only history) and `docs/session-memory/`
(one file per session, never edited). Those two are the record; this is the snapshot.

**Last updated: 22 August 2026 (ninth update — Stage-2 head frozen as v1.0; papers read).** Rewritten from a one-off machine-handoff document — the
20–21 Aug handoff it described is complete, and its content is preserved in git history
(`git show ad71ee4:transfer.md`) and in §6 below.

> **Maintenance rule (CLAUDE.md rule 5):** whenever a session finishes something, decides
> something, or changes what should happen next, update §1–§4 here **before the session ends**.
> A stale snapshot is worse than none — it is the exact failure mode `CLAUDE.md` rule 4 exists
> to prevent, and this file has already caused one wasted search (§6).

---

## 1. Where we are, in five lines

**Stage 2 is fixed.** The learned enumeration head lifts FDI accuracy from 22.9% to
**46.5% end-to-end** (69.4% of detected teeth), a 2.0x improvement, measured on **164 leak-free
images** after 86 were found to be training duplicates. It clears the positional ceiling
(67.0%) by +2.4 points. The bottleneck has moved to detector recall (67.0%). We are on **W2 of the 8-week plan** (`docs/research/MASTER_PLAN_2026H2.md` §5; W2 = Aug 22–28,
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
| **Papers read** — DPML + DentFound, both corroborate decisions taken | `RESULTS_LOG.md` 2026-08-22k |
| Test suite | **46/46 pass** |

**Findings that changed the science** (all in `RESULTS_LOG.md`):
- The bbox detector's ground truth is **missing 66 real teeth** (corrupt `bounding box` fields); test GT holds 3,924 of 3,930. Left unfixed on purpose to preserve the frozen detector.
- The **caries gate's negative class contains no healthy teeth** — `no_caries` is Impacted + Periapical Lesion. Real defect, no fix inside DENTEX's labelled data.
- **DENTEX's subsets cover disjoint patients despite sharing filenames.** Cost one bug (15,531 crops of the wrong patients) before it was caught.
- `DENTEX/disease/` holds **250 images, 1,600 FDI-keyed polygons, 8 classes, 91 explicitly healthy teeth** — leakage-checked, exactly 1 duplicate (`test_181.png` = `train_332.png`). Internal held-out set, **not** external validation.

---

## 3. What is NEXT — ordered, with the real blocker named

1. **R4 — Stages 5&ndash;6 integration.** *No blocker, and now worth doing.* Stage 2 is fixed
   and frozen, so a per-tooth report is finally meaningful. `scripts/run_inference.py` is a
   38-line placeholder; all five models are on local disk. Use
   `src.fdi_head_inference.assign_fdi_head`, **not** the superseded positional module.
   This is C3 and the plan's long pole.
2. **Detector recall is now the binding constraint (67.0%).** At that recall 67.0% is the
   end-to-end maximum and the head already captures 69.4% of it. **R1's seg retrain is the
   lever**, and DentFound's ablation now justifies it with numbers (+20.35% precision,
   +23.01% recall, +23.11% F1 from tooth instance masks) rather than assertion.
3. **Caries arms A and B** — `train_caries_cascade.py --arm a` / `--arm b`. ~10 min locally on
   MPS, or bundle into the GPU session. Closes T0.1&ndash;T0.4.
4. **T0.5 — the Mild n=6 decision.** No blocker, no compute. Still untouched.
5. **Version-tag the bone-loss weights** — Stages 4a/4b are now the only untagged models.
6. **Reconnect the Ningxia drive** for W4's external run. It is external test data: never
   train or tune on it. **Check its overlap against Tufts, DENTEX *and* the enumeration
   corpus separately** — inferring disjointness from a neighbouring pair is exactly the
   mistake that cost 5.7 points on Stage 2.
7. **Start IRB paperwork.** Zero-cost, longest lead, flagged since 15 Aug, still not begun.

## 4. Decisions PENDING — do not default into these silently

| Decision | Why it needs a human |
|---|---|
| **Detector-derived not-diseased class?** The caries gate's negative class contains *no healthy teeth* — it is Impacted + Periapical Lesion only. Running the frozen detector over the 705 disease images and treating unmatched detections as not-diseased is the one sound fix, but it puts detector error into training labels. | Trade-off, not a fact |
| **What else to use `DENTEX/disease/` for.** It is now the Stage-2 evaluation set (164 leak-free of 250). The other candidate uses — a small real healthy class (91 `saglam` teeth) and the C3 error-propagation substrate — are still open. | Scoping call |
| **Clinic data governance.** `index.csv` sits beside `images/` on a shared Drive, which voids the de-identification. Five actions in `clinical_dataset_provenance.md` §4a, all needing the Drive owner. | Not this repo's account |
| **Bone-loss weights have no version tag** — now the only trained models lacking one, after the Stage-2 head was frozen as `fdi-enumeration-head-resnet18-v1.0`. | Trivial, just undone |

**RESOLVED 22 Aug — kept because the reasoning is the useful part:** *how to fix FDI numbering.*
Route A (raise posterior detector recall) was **ruled out by measurement** — rank-order
assignment is capped at 67.0% even on a fully-detected quadrant, because eight detected teeth
are not positions 1–8, they are eight teeth that survived extraction. Route B (a learned
per-tooth enumeration head) was built, trained and validated at **46.5% end-to-end**, clearing
that ceiling by +2.4 points. `RESULTS_LOG.md` 2026-08-22f, 22i, 22j, 22l.

---

## 5. The GPU session — run order, everything in one sitting

All GPU work is rented (user preference, and `MASTER_PLAN` §6 agrees: *"compute is not the
bottleneck… always buy GPU"*). Every script below has been run end to end locally first, so
the rented time is spent training, not debugging.

| # | Job | Command | Est. |
|---|---|---|---|
| ~~1~~ | ~~Enumeration head~~ | **DONE locally, 48 min** — 52.2% end-to-end | ✅ |
| ~~2~~ | ~~Re-validate Stage 2~~ | **DONE** — `--method head` | ✅ |
| 3 | Caries Arm A | `python scripts/dentex/train_caries_cascade.py --arm a` | ~5 min (or ~2 min locally) |
| 4 | Caries Arm B | `python scripts/dentex/train_caries_cascade.py --arm b` | ~5 min (or ~2 min locally) |
| 5 | **R1 seg retrain** — **the only job that genuinely needs renting** | `python scripts/yolo/train_yolo_seg.py` | ~40 min on A100 |

Measured locally on the M4 Pro: ResNet18 work runs at ~287 img/s on MPS, so every caries job
is minutes. R1 is 7 h locally and needs 17.9 GB at the pre-registered batch 32 @ 1024px, which
is too close to the 24 GB ceiling to risk — **and shrinking the batch would break the
pre-registered comparison**, which is the real reason to rent rather than speed.

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

## 6. Where the documentation lives

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

## 7. Local state that git does NOT carry

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

## 8. History — the 20–21 Aug machine handoff (closed)

This file began as a one-off handoff to a second laptop. That handoff is complete: the
uncommitted work was committed and pushed, and the machine switch happened. Two of its claims
turned out to be **wrong**, and both are worth remembering as cautionary examples:

- It declared `outputs/eda_tufts/split_v1.csv` missing after an "exhaustive search". The search
  covered `C:\` and `D:\` — a Windows filesystem — while the repo lives on macOS. The file was
  there all along.
- Its §4 table said the Tufts data would need re-downloading. It was already local.

Full original text: `git show ad71ee4:transfer.md`.
