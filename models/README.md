# `models/` — trained checkpoints

**Last verified: 22 August 2026 (a fifth model now exists).** Every claim below was checked against the working tree,
not carried over from a previous version of this file.

## What is actually here

One numbered directory per trained stage, each with a `*summary*.txt` beside the weights.

| Directory | Stage | Weights | Tracked in git? |
|---|---|---|---|
| `06_yolo_detection_a100_run/` | Stage 1 — tooth detection, YOLOv11l | `best.pt`, `last.pt` (49 MB each) | **No** — `.gitignore` `models/**/*.pt`. Location + SHA-256 in `run_summary.txt`. |
| `07_caries_cascade/` | Stage 3 — caries cascade, ResNet18 ×2 | 5 `.pth` (43 MB each) | **Partly** — the two bundles are tracked; the three lineage checkpoints are not. See below. |
| `09_caries_gate_v3/` | Stage 3 — **the gate the pipeline actually uses**, retrained with a real negative class (5,366 healthy teeth) | 1 `.pth` (43 MB) | Weights gitignored; summary + reports tracked |
| `03_bone_loss_model_training_notebook_models/` | Stage 4a — bone-loss binary | `bone_loss_resnet18_{best,final}.pth` | **Yes** |
| `04_bone_loss_severity_notebook_models/` | Stage 4b — bone-loss severity | `bone_loss_severity_resnet18_best.pth` | **Yes** |
| `05_cej_estimation_v2_models/` | Exploratory CEJ (negative result, not in the pipeline) | summary only | n/a |
| `08_fdi_enumeration_head/` | **Stage 2 — FDI enumeration head, ResNet18 + positional features** | `enumeration_head_best.pth` (43 MB) | **Yes** |

> The previous version of this file claimed "**Model files (.pth, .pt) are git-ignored** due
> to file size" and showed a flat `models/*.pth` layout. Both were wrong: the ResNet18 `.pth`
> files are and always were tracked, and the layout has been `models/<NN>_<name>/` throughout.

## Version tags

| Tag | Covers | Frozen |
|---|---|---|
| `tooth-detector-a100-1024-v1.0` | Stage 1 detector | 20 Aug 2026 — `docs/research/T0.6_detector_reconciliation.md` §1 |
| `caries-cascade-resnet18-v1.0` | Stage 3 cascade | 21 Aug 2026 — `07_caries_cascade/run_summary.txt` |
| `caries-gate-resnet18-v3.0` | Stage 3 gate (**pipeline default**) | 25 Aug 2026 — `09_caries_gate_v3/run_summary.txt` |
| `fdi-enumeration-head-resnet18-v1.0` | Stage 2 numbering | 22 Aug 2026 — `08_fdi_enumeration_head/run_summary.txt` |

**One gap remains:** bone-loss weights (Stages 4a/4b) are still not version-tagged.

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
