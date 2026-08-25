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

**Stage 6 now exists — the pipeline runs end to end** (`scripts/run_inference.py`, 24 Aug):
image → per-tooth JSON. It exposed two OOD failures in opposite directions. **The caries one is
fixed** (25 Aug): a rebuilt negative class with 5,366 real healthy teeth took the pipeline's
caries rate from **84.9% → 19.1%**, though precision is only 0.40. **Bone loss remains
near-inert off-Tufts (0.7%)** and is now the open one. `RESULTS_LOG` 2026-08-24f, 2026-08-25a.

**Stage 2 is fixed.** The learned enumeration head lifts FDI accuracy from 22.9% to
**46.5% end-to-end** (69.4% of detected teeth), a 2.0x improvement, measured on **164 leak-free
images** after 86 were found to be training duplicates. On complete quadrants it clears the
positional ceiling (**66.3%**) by **+13.9 points**. The bottleneck has moved to detector
recall (67.0%). We are on **W2 of the 8-week plan** (`docs/research/MASTER_PLAN_2026H2.md` §5; W2 = Aug 22–28,
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
| **R4 Stages 1–6 integrated** — image → per-tooth JSON + overlay | `scripts/run_inference.py`, `src/classifiers.py`, `outputs/r4_demo/`; 60/60 tests |
| **Caries gate rebuilt** with 5,366 real healthy teeth — 84.9% → 19.1% in-pipeline | `models/09_caries_gate_v3/run_summary.txt`, `outputs/caries_v3/gate_comparison.json` |
| **Stage 2 FDI assignment** built + tested (R4, part 1) | `src/fdi_assignment.py` |
| **Orientation contract** — rotate for detector, un-rotate immediately | `src/orientation.py` |
| **Stage 2 validated** (22.9%) then **FIXED** (46.5%), **reproduces byte-for-byte** | `scripts/eval/validate_fdi_assignment.py --method head`; re-run 24 Aug produced artefacts `diff`-identical to `outputs/stage2_clean/`. *(Previously listed here as 28.0%→52.2% — both leaked-set figures. RESULTS_LOG 22j.)* |
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

1. ~~**R4 — Stages 5–6 integration.**~~ **DONE 24 Aug** (RESULTS_LOG 2026-08-24f).
   `scripts/run_inference.py` now runs image → per-tooth JSON + overlay through all six stages;
   Stages 3–4 live in `src/classifiers.py`; 14 new tests, 60/60 pass.
   **It immediately exposed two out-of-distribution failures that isolated evaluation could
   not** — which is the C3 argument:
   - **caries over-calls ~7×** (84.9% of 299 teeth vs 35 annotated) because the gate's negative
     class holds no healthy teeth;
   - **bone loss is near-inert** (0.7%), trained on Tufts and run on DENTEX.
   Both are quantified inside every report under `["limitations"]`. **0 duplicate FDI codes
   across 299 teeth.**

2. ~~**The caries gate's negative class.**~~ **FIXED 25 Aug** (RESULTS_LOG 2026-08-25a).
   The enumeration and disease subsets share **260 byte-identical images under different
   filenames** — 21m's "not derivable from DENTEX" was half right (the *filename* join is
   invalid; an **MD5** join is not). Verified by falsifiable test: **98.28% FDI agreement**.
   Gave **5,366 real healthy teeth**; retrained gate frozen as `caries-gate-resnet18-v3.0`
   and now the pipeline default. In-pipeline caries **84.9% → 19.1%** against an 11.7%
   annotated floor. **Improved, not solved** — held-out precision is **0.40**.

3. **Detector recall is now the binding constraint (67.0%).** At that recall 67.0% is the
   end-to-end maximum and the head already captures 69.4% of it. **R1's seg retrain is the
   lever**, and DentFound's ablation now justifies it with numbers (+20.35% precision,
   +23.01% recall, +23.11% F1 from tooth instance masks) rather than assertion.
4. ~~**Caries arms A and B.**~~ **DONE 25 Aug** — both ran on `crops_v3_phase1` (re-scoped
   from the superseded `phase1_legacy`). Gap between arms (0.01-0.03) is smaller than each
   arm's own epoch-to-epoch noise (~0.27) — reported as inconclusive, not a win either way.
   Frozen gate (arm B) unchanged. Closes T0.1&ndash;T0.4. RESULTS_LOG 2026-08-25b.
5. ~~**Lesion-localisation evaluator.**~~ **BUILT + RUN 25 Aug** (RESULTS_LOG 2026-08-25c) —
   no code for this existed before today. `scripts/eval/lesion_localization.py`. This is
   §4.3.4's primary EXTERNAL number for C2 (immune to Ningxia's missing-negatives problem) and
   the T1.5 XAI metric, built and validated against DENTEX first so Ningxia later is "point at
   a different folder," not new code under deadline pressure. **204/479 = 42.6%** lesion
   agreement on 164 clean images. Pure inference — no GPU needed, ran on MPS.
6. **T0.5 — the Mild n=6 decision.** No blocker, no compute. Still untouched.
7. **Version-tag the bone-loss weights** — Stages 4a/4b are now the only untagged models.
8. ~~**Reconnect the Ningxia drive.**~~ **DONE 25 Aug — C2 HAS ITS FIRST NUMBERS**
   (RESULTS_LOG 2026-08-25d). Test splits copied to `~/Downloads/Capstone/ningxia_local/`
   (train deliberately left on the drive — we may never train on it, so not having it locally
   makes that impossible). **Zero leakage** against all five corpora, each checked separately.
   Caries lesion agreement **22.6–43.3%** across four hospitals (DENTEX internal was 42.6%);
   periodontitis affected-tooth sensitivity **0.8–5.4%**. Ningxia is now **touched** — locked,
   no further tuning against it, ever.
9. **Start IRB paperwork.** Zero-cost, longest lead, flagged since 15 Aug, still not begun.

## 4. Decisions PENDING — do not default into these silently

| Decision | Why it needs a human |
|---|---|
| **Detector-derived not-diseased class?** The caries gate's negative class contains *no healthy teeth* — it is Impacted + Periapical Lesion only. Running the frozen detector over the 705 disease images and treating unmatched detections as not-diseased is the one sound fix, but it puts detector error into training labels. | Trade-off, not a fact |
| **What else to use `DENTEX/disease/` for.** It is now the Stage-2 evaluation set (164 leak-free of 250). The other candidate uses — a small real healthy class (91 `saglam` teeth) and the C3 error-propagation substrate — are still open. | Scoping call |
| **Clinic data governance.** `index.csv` sits beside `images/` on a shared Drive, which voids the de-identification. Five actions in `clinical_dataset_provenance.md` §4a, all needing the Drive owner. | Not this repo's account |
| **Bone-loss weights have no version tag** — now the only trained models lacking one, after the Stage-2 head was frozen as `fdi-enumeration-head-resnet18-v1.0`. | Trivial, just undone |

**RESOLVED 22 Aug — kept because the reasoning is the useful part:** *how to fix FDI numbering.*
Route A (raise posterior detector recall) was **ruled out by measurement** — rank-order
assignment is capped at **66.3%** even on a fully-detected quadrant, because eight detected
teeth are not positions 1–8, they are eight teeth that survived extraction. Route B (a learned
per-tooth enumeration head) was built, trained and validated at **46.5% end-to-end**, reaching
**80.2%** on that same complete-quadrant population — clearing the ceiling by **+13.9 points**.
`RESULTS_LOG.md` 2026-08-22f, 22i, 22j, 22l, **2026-08-24a** (audit: the ceiling was previously
mis-stated as 67.0%, which is the detector's recall).

---

## 5. The GPU session — run order, everything in one sitting

All GPU work is rented (user preference, and `MASTER_PLAN` §6 agrees: *"compute is not the
bottleneck… always buy GPU"*). Every script below has been run end to end locally first, so
the rented time is spent training, not debugging.

| # | Job | Command | Est. |
|---|---|---|---|
| ~~1~~ | ~~Enumeration head~~ | **DONE locally, 48 min** — **46.5%** end-to-end (52.2% was the leaked-set figure) | ✅ |
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
| Python env | `/opt/anaconda3` (python 3.12) | **Working — 60/60 tests pass** (25 Aug, up from 46 after R4's `test_classifiers.py`), Stage 2 re-runs and reproduces byte-for-byte. torch 2.2.0 + MPS, cv2 5.0.0, ultralytics 8.4.127, scipy, sklearn. ⚠️ **`numpy` must stay `<2`** (pinned 1.26.4): numpy 2.x breaks torch↔numpy, `scipy.optimize` — which **is** the Stage-2 Hungarian assignment — and sklearn, silently at import. `requirements.txt` now pins it. |
| **Two gitignored checkpoints, on Google Drive** | `docs/EXTERNAL_DRIVE.md` | `06_yolo_detection_a100_run/best.pt` (Tufts drive) + `09_caries_gate_v3/caries_gate_v3.pth` (DENTEX drive), both in a new `capstone_checkpoints/` folder. **Upload itself is still manual** — browser automation hit a 10 MB per-call cap on the upload tool, well under either file's size. |
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
