# `models/` — trained checkpoints

**Last verified: 26 August 2026 (Stage-2 head v2.0 added).** Every claim below was checked
against the working tree, not carried over from a previous version of this file.

**Cloned this repo and `run_inference.py` says a weight is missing?** As of **3 Sep 2026** the
three checkpoints `run_inference.py` needs — `11_yolo_seg_tufts_r1/best.pt` (53 MB),
`09_caries_gate_v3/caries_gate_v3.pth` (43 MB) and `10_.../enumeration_head_best.pth` — are all
**committed to git** (`.gitignore` exceptions + `.gitattributes`), so `git clone` / `git pull`
is enough to run the pipeline. Still Drive/local-only: `06_yolo_detection_a100_run/best.pt`
(superseded, only for pre-27-Aug reproduction) and the lever weights (`13`, `15`, `16`).
**`14_cariesxrays_lever2/weights/best.pt` (Lever B's B-single arm) is committed to git**
(4 Sep 2026, sha256-verified `278d1e00…`) — no Drive round-trip needed for it either.

## What is actually here

One numbered directory per trained stage, each with a `*summary*.txt` beside the weights.

| Directory | Stage | Weights | Tracked in git? |
|---|---|---|---|
| `06_yolo_detection_a100_run/` | Stage 1 — tooth detection, YOLOv11l **bbox**. **Superseded as the pipeline default 27 Aug 2026**; retained and hash-pinned, since every number published before that date was measured on it. | `best.pt`, `last.pt` (49 MB each) | **No** — `.gitignore` `models/**/*.pt`. Location + SHA-256 in `run_summary.txt`. |
| `11_yolo_seg_tufts_r1/` | Stage 1 — tooth detection, YOLOv11l-**seg**. **Current pipeline default (`DEF_DETECTOR`), adopted 27 Aug 2026.** Adopted for its box gain (+2.76 pts) **despite MISSING the pre-registered mask bar** — used for BOXES ONLY, R2 stays unwired. | `best.pt` (53 MB) | **Yes — committed 3 Sep 2026** (`.gitignore` exception; private repo; SHA-256 `271316c4…` in `run_summary.txt`). |
| `07_caries_cascade/` | Stage 3 — caries cascade, ResNet18 ×2 | 5 `.pth` (43 MB each) | **Partly** — the two bundles are tracked; the three lineage checkpoints are not. See below. |
| `09_caries_gate_v3/` | Stage 3 — **the gate the pipeline actually uses**, retrained with a real negative class (5,366 healthy teeth) | 1 `.pth` (43 MB) | **Committed 3 Sep 2026** (same size as the tracked `10` head; SHA-256 `8f4a99ba…`). `isotonic_calibrator.json` + reports were always tracked. |
| `03_bone_loss_model_training_notebook_models/` | Stage 4a — bone-loss binary | `bone_loss_resnet18_{best,final}.pth` | **Yes** |
| `04_bone_loss_severity_notebook_models/` | Stage 4b — bone-loss severity | `bone_loss_severity_resnet18_best.pth` | **Yes** |
| `05_cej_estimation_v2_models/` | Exploratory CEJ (negative result, not in the pipeline) | summary only | n/a |
| `08_fdi_enumeration_head/` | Stage 2 — FDI head **v1.0** (DENTEX only). Superseded as the pipeline default 26 Aug, **retained and still hash-pinned** — every Stage-2 number published before that date was measured on it. | `enumeration_head_best.pth` (43 MB) | **Yes** |
| `10_fdi_head_dentex_tufts_v2/` | Stage 2 — FDI head **v2.0** (DENTEX + Tufts). **Current pipeline default (`DEF_FDI_HEAD`).** Adopted for cross-domain robustness, not in-domain accuracy — see below. | `enumeration_head_best.pth` (43 MB) | **Yes** |
| `12_fdi_head_v3_3corpus/` + `12a_fdi_head_v2_control_rebuilt/` | Stage 2 — FDI head **v3** (DENTEX + Tufts + Kaggle) and its same-day control. **ABLATION, not the default** — `RESULTS_LOG.md` 2026-08-28c. | `enumeration_head_best.pth` (43 MB each) | **Yes** — both tracked, same as the 08/10 heads. SHA-256 also in each `run_summary.txt`. *(12's was committed with the run in `21ea05b`; 12a's was added 2 Sep — a brief `git rm --cached` of 12's that day was reverted the same day so no collaborator loses the file on pull.)* |
| `13_detector_multicorpus_lever1/` | Stage 1 — **Lever 1** multi-corpus detector retrain (Tufts + DENTEX). Two arms + a same-day control. **ABLATION, not the default** — primary passes (FDI end-to-end 0.584 → 0.934 on DENTEX) but the pre-registered Tufts guard fails (box mAP 0.810 → 0.647). `run_summary.txt`, `RESULTS_LOG.md` 2026-09-01h. | `controlB_tuftsonly_best.pt`, `arm_multicorpus_best.pt` (49 MB each) | **No** — gitignored; SHA-256 in `run_summary.txt`, local disk only |
| `14_cariesxrays_lever2/` | **Lever 2** — standalone caries-**lesion** detector (YOLOv11l) on the CariesXrays benchmark (Chen et al., AAAI 2024). **BENCHMARK ROW, not a pipeline component** — COCO AP 0.482 / AP50 0.845 on this project's own seed-42 split (the official FPCL split is not public), level with FPCL. **It is also Lever B's B-single arm.** `run_summary.txt`, `RESULTS_LOG.md` 2026-09-02b. | `best.pt`, `last.pt` (51 MB each) | `weights/best.pt` (sha256 `278d1e00…`) is **on the friend's Windows laptop** — committable via a 3 Sep `.gitignore` exception after verifying the hash (`outputs/lever_B_lesion_caries_path/WINDOWS_SETUP.md` §4); `last.pt` stays gitignored. SHA-256 in `run_summary.txt`. `run_summary.txt` / `results.csv` / `args.yaml` **are** tracked; the `.png` curves and `val_batch*` renders are `*.png`/`*.jpg`-ignored like every other `models/` dir. |
| `15_detector_multicorpus_leverA/` | Stage 1 — **Lever A** multi-corpus detector, "done right" (4 corpora: Tufts + DENTEX `quadrant_enumeration` + Kaggle "dual" + UFBA-425, per-corpus balanced). 3 arms (`controlB` / `arm3c` / `arm4c`). **ABLATION, not the default** (`RESULTS_LOG.md` 2026-09-03 + 03b). Pre-registered verdict: **PRIMARY passes** (FDI e2e on DENTEX 0.584 → 0.928, Δ +34.4 pp — replicates Lever 1), **GUARD 1 passes** (pooled external caries agreement +9.1 pp; Ningxia 0.41 → 0.60, CariesXrays 0.31 → 0.37), **GUARD 2 fails** (Tufts frozen test box mAP 0.724 → 0.585 / 0.552). 2 of 3 → ablation. The tradeoff is **bidirectional**: worse on Tufts, better on the other 5 of 6 cohorts. | `controlB_best.pt`, `arm3c_best.pt`, `arm4c_best.pt` (51 MB each) | **No** — gitignored; SHA-256 in `run_summary.txt`, local disk only. `run_summary.txt` / `*_results.csv` / `leverA_train.log` / `repro/` (as-run scripts + a verify-every-number cheat sheet) / `repro/diagnostics/` (the Tufts Guard-2 post-mortem, `RESULTS_LOG` 2026-09-03c) **are** tracked. |
| `16_lever_b_pooled/` | Stage 3 — **Lever B, B-pooled arm**: caries-**lesion** detector (YOLOv11l) trained on CariesXrays + DENTEX-caries, per-corpus balanced. **ABLATION, not adopted** — Sec 6 of the pre-reg needs Ningxia, not yet available (`RESULTS_LOG.md` 2026-09-04b). Tooth-level lesion agreement: DENTEX 45.5% [40.9,50.1] (a statistical **tie** with gate v3.0/constant — B-single alone lost decisively at 8.6%); CariesXrays 68.4% [66.4,70.4] (still a decisive win, ~unchanged from B-single). Rented an **RTX-PRO6000** (A100 unavailable at rental time), ₹546.93. | `lever_b_pooled_yolo11l-2/weights/{best,last}.pt` (51 MB each) | **No** — gitignored, same rule as `13`/`15` (an ablation arm, not a `DEF_*` default). SHA-256 in `run_summary.txt`. `run_summary.txt` / `results.csv` / `args.yaml` / `train.log` **are** tracked; the `.png`/`.jpg` plots are `*.png`/`*.jpg`-ignored like every other `models/` dir. |

> **Adopted vs ablation:** dirs `06`–`11` are pipeline components (current or hash-pinned
> superseded); `05`, `12`, `12a`, `13`, `15`, `16` are ablations / negative results kept per
> `CLAUDE.md` rule 3, none in the runtime pipeline; `14` is a standalone benchmark model, also not
> in the pipeline (and also Lever B's B-single arm — `14` and `16` are the two Lever B arms,
> scored against each other in `RESULTS_LOG.md` 2026-09-04 / 04b). **`13` and `15` are both the
> same experiment (multi-corpus detector) — `15` is `13` re-done with more corpora and a
> differently-scoped guard; the verdict was the same (ablation), the result is stronger**
> (bidirectional, replicated).

> The previous version of this file claimed "**Model files (.pth, .pt) are git-ignored** due
> to file size" and showed a flat `models/*.pth` layout. Both were wrong: the ResNet18 `.pth`
> files are and always were tracked, and the layout has been `models/<NN>_<name>/` throughout.

## Version tags

| Tag | Covers | Frozen |
|---|---|---|
| `tooth-detector-a100-1024-v1.0` | Stage 1 detector | 20 Aug 2026 — `docs/research/T0.6_detector_reconciliation.md` §1 |
| `caries-cascade-resnet18-v1.0` | Stage 3 cascade | 21 Aug 2026 — `07_caries_cascade/run_summary.txt` |
| `tooth-detector-seg-tufts-1024-v1.0` | Stage 1 detection (**pipeline default**) | 27 Aug 2026 — `11_yolo_seg_tufts_r1/run_summary.txt` |
| `caries-gate-resnet18-v3.0` | Stage 3 gate (**pipeline default**) | 25 Aug 2026 — `09_caries_gate_v3/run_summary.txt` |
| `fdi-enumeration-head-resnet18-v1.0` | Stage 2 numbering (DENTEX only) | 22 Aug 2026 — `08_fdi_enumeration_head/run_summary.txt` |
| `fdi-enumeration-head-resnet18-v2.0` | Stage 2 numbering (DENTEX + Tufts, **pipeline default**) | 26 Aug 2026 — `10_fdi_head_dentex_tufts_v2/run_summary.txt` |
| `bone-loss-binary-resnet18-v1.0` | Stage 4a bone loss present/absent (**pipeline default**) | 27 Aug 2026 — `03_bone_loss_model_training_notebook_models/run_summary.txt` |
| `bone-loss-severity-resnet18-v1.0` | Stage 4b severity Mild/Moderate/Severe (**pipeline default**) | 27 Aug 2026 — `04_bone_loss_severity_notebook_models/run_summary.txt` |
| `caries-lesion-detector-yolo11l-cariesxrays-v1.0` | Lever 2 — CariesXrays lesion detector (**benchmark only, not in the pipeline**) | 2 Sep 2026 — `14_cariesxrays_lever2/run_summary.txt` |

**No gaps remain — every trained model in this project is now tagged and hash-pinned**
(closed 27 Aug 2026). Stages 4a/4b were the last, and had been serving as pipeline defaults
for months with no version tag and no recorded hash, so a silent swap or a truncated copy
would not have been caught. Both are now checked by `scripts/eval/verify_invariants.py`.

Their tagging also upgraded the **bone-loss binary class order** from an inference to a
confirmed fact: the checkpoints are raw `state_dict`s carrying no `class_to_idx`, and
`run_inference.py` previously noted the order as "Inferred, not read". It is now corroborated
by the FocalLoss alpha ratio (2.258/0.642 = 3.5171) matching the class-count ratio
(2,500/711 = 3.5162) to 0.03%, **and** by `training_summary.txt` labelling its own scores
"F1 Normal (cls 0)" / "F1 Diseased (cls 1)". See
`03_bone_loss_model_training_notebook_models/run_summary.txt`.

## Which FDI head to use — v1.0 vs v2.0

**`10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` — it is the pipeline default
(`DEF_FDI_HEAD` in `scripts/run_inference.py`).**

v2.0 was adopted for **cross-domain robustness, not in-domain accuracy — do not quote it as an
accuracy improvement.** Measured both ways (`RESULTS_LOG.md` 2026-08-25j, 2026-08-26a):

| | DENTEX 164 leak-free, end-to-end | Tufts held-out test, 3,786 crops (GT boxes) |
|---|---|---|
| v1.0 (DENTEX only) | 46.47% | 50.0% |
| **v2.0 (DENTEX + Tufts)** | 46.58% (+0.11pp — inside the ~1pt noise floor) | **71.5%** (+21.5pp) |

> **Both columns were measured on the superseded bbox detector**, which is what makes them a
> fair head-vs-head comparison. On the seg detector (Stage-1 default since 27 Aug 2026) the
> same v2.0 head reaches **58.3% end-to-end on DENTEX**. The head did not change; the boxes
> did. RESULTS_LOG 2026-08-27e.

A Tufts-only head was also trained and rejected: it loses 9.1 points on DENTEX while its edge
over v2.0 on Tufts is not statistically significant (McNemar p=0.732). v2.0 strictly dominates
it. `v1.0` is retained and still hash-pinned by `scripts/eval/verify_invariants.py` — it is the
provenance of every Stage-2 number published before 26 Aug 2026, so it must stay
byte-reproducible even though it is no longer what `run_inference.py` loads by default.

Tufts' numbering had to be corrected before use — its labels are left-right **mirrored**
relative to standard Universal numbering (Tufts "1" = FDI 28, not 18). See
`../scripts/tufts/README.md` before touching this data yourself.

## `07_caries_cascade/` — which file is which

Retrieved from Kaggle on 21 Aug 2026; before that the caries branch was the only trained
stage with no local weight, no tag and no hash.

- `phase2_final_bundle.pth` **[tracked]** — Phase 2 severity, `{model_state_dict, class_to_idx}`,
  `{caries, deep_caries}`. **This is the model behind the reported caries numbers.**
- `final_model.pth` **[tracked]** — Phase 1 gate, `{model_state_dict, class_to_idx}`,
  `{caries, no_caries}`.
- `best_phase2_final.pth`, `best_phase2_fixed.pth`, `best_model.pth` **[gitignored]** —
  training lineage. Needed to *reproduce* the runs, not to *run* them. `best_model.pth` is
  byte-identical to `final_model.pth` (verified).

Storage split rationale: the two bundles are the complete runnable cascade at 86 MB; tracking
all five would add 214 MB for the same usable model. SHA-256 for all five is in
`run_summary.txt`.

## Model specifications

| | Stage 1 detector | **Stage 2 FDI head** | Caries cascade | Bone-loss binary | Bone-loss severity |
|---|---|---|---|---|
| Architecture | YOLOv11l | **ResNet18 + 4 positional features** | ResNet18 ×2 (ImageNet) | ResNet18 (ImageNet) | ResNet18 (ImageNet) |
| Input | 1024 px OPG | **224×224 crop at 1.5× + [cx,cy,bw,bh]** | 224×224 **tight** crop (no expansion) | 224×224 expanded 1.5×W / 2.0×H | same expanded crop |
| Output | tooth boxes, `nc=1` | **quadrant (4) + position (8) → FDI** | caries/no_caries → caries/deep_caries | Present / Absent | 3-class severity |
| Head | — | **(512+64) → 4 and → 8** | 512 → 2 | 512 → 2 | 512 → 3 |
| Normalisation | Ultralytics default | ImageNet mean/std | ImageNet mean/std | ImageNet mean/std | ImageNet mean/std |

Note the crop geometries differ by design: the caries track uses the raw bbox with **no
expansion**, the bone-loss track uses asymmetric expansion (`PAPER_MATERIAL.md` §6.1).

## Caveats worth knowing before using these

- **The caries weights are accuracy-selected**, predating the T0.3 macro-F1 fix, and were
  evaluated on validation only. `scripts/dentex/train_caries_cascade.py` is the re-run that
  replaces them.
- **The caries weights have never been loaded on this machine** — no torch was installed when
  they were recorded, so they were verified structurally (valid archives, correct
  `class_to_idx`, 512→2 head, lineage confirmed by tensor-payload digests) but not
  functionally. Reproduce cell 119's macro-F1 0.77 before trusting inference.
- Current numbers for all stages: `docs/results/model_metrics.md`.


## Which caries gate to use

**`09_caries_gate_v3/caries_gate_v3.pth` — it is the pipeline default.**

The Phase-1 gate in `07_caries_cascade/final_model.pth` has a negative class of Impacted +
Periapical Lesion and **no healthy teeth**. Fed every tooth a detector finds, it calls **84.9%**
of them carious. It is not broken *for the task it was trained on* — caries vs other-pathology —
but that is not the task the pipeline asks of it.

v3 rebuilds the negative class from 5,366 real healthy teeth (MD5 join of the enumeration and
disease subsets, verified at 98.28% FDI agreement) and calls **19.1%** against an 11.7%
annotated floor. Held-out precision is **0.40** — improved, not solved.

`07_caries_cascade/` is retained: it is still the model behind the published `phase1_legacy`
numbers, and its Phase-2 severity head is unchanged and still in use. RESULTS_LOG 2026-08-25a.

---

**Setting up on a new machine?** `../transfer.md` §8 has the full checklist — in short, `git
clone` plus the two Drive-only checkpoints above is everything `run_inference.py` needs.
**Publication target and grading criteria:** `../transfer.md` §5.
