# Pre-registration — Stage 4b retrained on bands of mask overlap, split by radiograph

Written 14 October 2026, before any Stage-4b model has been trained on these labels and before
any such model has seen a test crop. **The commit that adds this file, together with
`scripts/tufts/train_bone_severity_v2.py` and `scripts/eval/bone_severity_v2_eval.py`, is the
record of when — and is the decision owner's authorisation to train and to make the one test
pass in §5.** Nothing is trained before that commit.

## 0. Compact

| | |
|---|---|
| **Goal** | Find out whether the Stage-4b architecture can learn the label it was named for — how much of a flagged tooth's crop overlaps the expert abnormality mask — when trained and tested on different radiographs |
| **Why** | The shipped head (`models/04`) was trained on bands of crop *contrast*, a stand-in its notebook built when the overlap column was missing (`RESULTS_LOG` 2026-10-13d). On 140 validation positives it scores macro-F1 0.240 against the true overlap bands, quadratic kappa −0.145 (`RESULTS_LOG` 2026-10-14c; 3 of those 41 radiographs were in its own training set) |
| **Decision owner** | The user, who on 14 Oct asked whether Stage 4b could be retrained and said to proceed. This overrides the 12–13 Oct councils, which refused a Stage-4b retrain (3 of 3) and any further pass over the Tufts test split |
| **What the label is** | An **extent band of an expert-marked abnormality** near a tooth — mostly apical lesions, sclerosis and cysts. **Not a clinical severity, not periodontal bone loss**, whatever the class names say |
| **What it is not for** | In the pipeline this head grades the teeth Stage 4a flags, about seven in ten of which carry no abnormality. A test on true positives says nothing about those |
| **Default change** | **None in this protocol.** The report keeps the grade withheld by default (D1, 14 Oct). Whether a new checkpoint replaces `models/04` behind `--bone-severity-grade` is a separate decision, recorded after §6 |

## 1. Data

- **Radiographs:** the frozen `outputs/eda_tufts/split_v1.csv`, twins removed as in Stage 4a
  (`train_bone_loss_v2.py`, `DROP`): 678 train, 145 val, 143 test.
- **Teeth:** every annotated tooth box (`clean_crops`, `scripts/eval/bone_loss_heldout.py`) whose
  1.5×W / 2.0×H crop overlaps the Tufts expert abnormality mask by more than 0.01 — the Stage-4a
  positives.
- **Label:** the overlap ratio cut at **0.05 and 0.15** into three bands, indices 0, 1, 2 in the
  order `["Mild", "Moderate", "Severe"]` of `src/classifiers.py`. These are the cut points the
  original notebook meant to use; no other cut is tried.
- **Counts (clean positives, counted 14 Oct before this file):** train 246 / 295 / 242 (783 teeth
  on 209 radiographs); val 41 / 57 / 42 (140 on 41); test 55 / 63 / 64 (182).
- Training adds one jittered copy of every train tooth (±15% box jitter, the notebook's), labelled
  by its own overlap and kept only if that exceeds 0.01. **The jitter is drawn from the run's seed**,
  unlike Stage 4a, whose three runs shared one jitter set.

## 2. Recipe

Stage 4a's recipe (`scripts/tufts/train_bone_loss_v2.py`), with the differences a three-class
head on balanced positives requires:

| | |
|---|---|
| Model | ResNet18, ImageNet weights, 3 outputs |
| Optimiser | Adam, lr 1e-4, weight decay 1e-4, batch 32 |
| Loss | Cross-entropy weighted n / (3 n_c) over the training bands (no undersampling, no focal loss: the bands are near-balanced) |
| Augmentation | Stage 4a's: flip, rotation within 10°, brightness ×[0.8, 1.2], contrast ×[0.9, 1.1] |
| Schedule | ReduceLROnPlateau on validation macro-F1 (0.5, patience 5); early stop after 10 epochs without gain; at most 50 epochs |
| Checkpoint | Best validation macro-F1 |
| Seeds | **42, 43, 44**, each run once. **Seed 42 is fixed now as the candidate**; 43 and 44 are reported to show the spread |
| Device | MPS where available (not bit-reproducible), else CPU |

## 3. What has already been seen

- The test split's radiographs and their Stage-4a labels and overlap ratios (`test_rows.json`
  of 13 Oct), including the band counts 55 / 63 / 64 above. No Stage-4b model of any kind has
  produced a prediction on a test crop.
- `models/04` on the 140 validation positives (the rehearsal in §0), run on 14 Oct to prove the
  scoring code before this file. That figure motivates the work; it chooses nothing in it.
- Tufts test radiograph 248 is a re-rendered copy of training radiograph 1017 (`RESULTS_LOG`
  2026-10-14). It holds no positive tooth, so it is outside this test set.

## 4. Harness checks, before any training

`python scripts/tufts/train_bone_severity_v2.py check` — run on 14 Oct, all three pass:

- **H1** the split is 678 / 145 / 143 and the clean positives per band are exactly the counts in §1.
- **H2** the band function puts 0.05 and 0.15 in the lower band, 0.0501 and 0.1501 in the upper.
- **H3** one epoch on 64 training crops runs (numbers discarded).

`tests/test_bone_severity_v2.py` covers the bands, macro-F1 and the quadratic kappa.

## 5. Evaluation — the test split, once

`python scripts/eval/bone_severity_v2_eval.py score`, after all three seeds are trained. It
refuses a second run. On the 182 test positives, crops at annotated tooth boxes:

| Arm | What it is |
|---|---|
| seed 42, 43, 44 | The three runs |
| `models/04` | The shipped contrast-trained head; also reported without its three radiographs inside the test split (149, 192, 249) |
| Tooth prior | The band most common for that tooth number among clean train positives (image-blind); majority band where a tooth is unseen |
| Majority | The most common train band for every tooth |

Reported for each: macro-F1 with a radiograph-cluster bootstrap interval (10,000 resamples,
seed 42, percentile), accuracy, quadratic-weighted kappa, recall per band, the 3×3 confusion
matrix. Paired differences, same resamples: seed 42 minus the tooth prior, minus `models/04`,
minus the majority band.

## 6. The rule, fixed now

- **Eligible** if seed 42's macro-F1 minus the tooth prior's has a 95% interval whose lower bound
  is above zero.
- Seeds 43 and 44 are reported whatever happens; if either falls below the tooth prior, say so
  beside the result.
- Eligible means a checkpoint *may* be proposed to replace `models/04` behind
  `--bone-severity-grade`. It does not change the report's default, and it does not make the
  grade a severity.

## 7. What this does not do

No Ningxia pass. No DENTEX scoring (no such label). No threshold. No other cut points, recipe or
seeds after this commit. No choice between seeds after the test. No change to Stage 4a. No new
default. No claim that the bands are clinical severity.

## 8. How the result is to be worded, fixed now

Either way: "Retrained on bands of the share of the tooth crop overlapping an expert-marked
abnormality — an extent band, not a severity — the head reached macro-F1 X [lo, hi] on 182 held-out
positive teeth, against Y for an image-blind tooth-position prior; two further runs gave … It
grades only teeth that truly carry the label; in the pipeline most flagged teeth do not."

## 9. Forbidden

Re-running `score`; training a seed twice; reading test crops in `check` or `train`; changing
§1–§6 after the commit; any Ningxia data.

## 10. Outputs and logging

`models/19_bone_severity_overlap/seed{42,43,44}_best.pth` (local, not in git) and
`seed*_history.json` (tracked, each with its sha256); `outputs/bone_loss_eval/v3_severity/`
`test_rows.json`, `test_summary.json` and the stdout log. One `RESULTS_LOG` entry for the training
and the test pass; `model_metrics.md` Stage 4b; `PAPER_MATERIAL.md` §8; `transfer.md`.
