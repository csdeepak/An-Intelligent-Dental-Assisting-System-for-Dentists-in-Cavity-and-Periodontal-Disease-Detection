# Pre-registration — Stage 4a retrained with a radiograph-level split

Written 14 October 2026, before any crop of the new training set has been cut and before any
model has been trained. The commit that adds this file is the record of when.

## 0. Compact

| | |
|---|---|
| **Goal** | Find out whether the Stage-4a architecture can learn its label when it is trained and tested on different radiographs. The shipped model cannot be said to: held out, it finds 7.6% of its own label (`docs/results/RESULTS_LOG.md` 2026-10-13) |
| **Who cares** | Anyone reading the per-tooth flag in the report or the demo; a reviewer reading the bone-loss paragraph |
| **Decision owner** | The user. On 14 Oct he chose this option ("retrain with a proper radiograph-level split on all 1,000 radiographs") |
| **What the model changes** | One per-tooth field, shown as `ABN` on the overlay |
| **The label, unchanged** | "The crop overlaps a Tufts expert abnormality mask by more than 1%." **Not periodontal bone loss.** A better model for this label is a better abnormality flag and nothing else (`PAPER_MATERIAL.md` §8.28) |
| **Success** | On test radiographs: better than the shipped model, and better than a score that knows only the tooth's position (§6) |
| **Guardrail** | Specificity and the number of false flags per radiograph are reported beside every sensitivity |
| **Mistakes** | A missed abnormal tooth costs a missed prompt to look. A false flag costs attention and trust. Neither is a diagnosis. The unacceptable mistake is in the wording: calling the output periodontal |
| **Constraints** | This Mac (MPS), no GPU rental, no Ningxia image, one source corpus |
| **Baselines** | The shipped checkpoint on the same test teeth; a tooth-position prior fitted on the new training split |
| **Rollback** | The shipped checkpoint stays in place, hash-pinned. This pre-registration changes no default (§7) |

## 1. Data

- **Source:** the 1,000 Tufts radiographs, expert masks and `teeth_bbox.json` under
  `_repo_archive/datasets_workspace/`.
- **Split:** the frozen `outputs/eda_tufts/split_v1.csv`, 700 / 150 / 150 by radiograph — the
  split the detector and the numbering head already use, so a Tufts test radiograph is unseen by
  every model in the pipeline. Radiograph 590 (test) is byte-identical to 591 (train) and is
  dropped from test. 1008 is byte-identical to 1007, both in train; 1008 is dropped. Thirty-two
  radiographs carry no tooth box. That leaves **678 train, 145 validation, 143 test.**
- **Crops and labels:** the construction notebook's recipe, as rebuilt and gated on 13 Oct
  (`scripts/eval/bone_loss_heldout.py`): box read as `[y1, x1, y2, x2]`, 1.5× wide and 2.0×
  tall, 224×224 from the greyscale radiograph; label 1 when more than 1% of the crop is non-zero
  in the expert mask.
- **Training set:** for every tooth of the 678 radiographs, the clean crop and one crop from a
  box jittered by ±15% in position and size (the notebook's `apply_bbox_jitter`, seed 42), each
  with its own label from its own overlap.
- **Validation and test sets:** clean crops only, every tooth, natural prevalence.

## 2. Recipe — the original's, with three stated differences

From `notebooks/bone_loss/03_bone_loss_model_training.ipynb` and its saved summary:

| | |
|---|---|
| Model | ResNet18, ImageNet weights, all layers trained, 512 → 2 |
| Loss | focal, γ = 2.0, α = n / (2·n_class) from the epoch's class counts |
| Optimiser | Adam, learning rate 1e-4, weight decay 1e-4, batch 32 |
| Schedule | ReduceLROnPlateau on validation macro-F1, factor 0.5, patience 5 |
| Stopping | at most 50 epochs; stop after 10 without a better validation macro-F1 |
| Checkpoint | the epoch with the best validation macro-F1 at the argmax decision |
| Augmentation | horizontal flip, rotation within ±10°, brightness ×[0.8, 1.2], contrast ×[0.9, 1.1] |
| Device | MPS; runs are seeded but MPS is not bit-reproducible |

**Differences from the original, all fixed now:**

1. **The split is by radiograph.** That is the point.
2. **All 678 training radiographs**, not 111. The original's pool was 145 radiographs.
3. **Class balance by sampling, not by a fixed subset.** An epoch is every diseased crop once
   and 3.5 normal crops for each, drawn afresh each epoch without replacement. The original kept
   one fixed 2,500 normals and tripled the diseased crops with saved augmented copies, for the
   same 3.5 to 1.

**Three seeds: 42, 43, 44.** Seed 42 is the one whose checkpoint would be considered for
shipping, decided now. The other two show how much a result moves between runs. No seed is
chosen by its result.

## 3. What has already been seen

- Everything about the shipped model: its crop-level validation figures, and its held-out pass
  of 13 Oct over 821 radiographs — which include the validation and test radiographs of this
  split that lie outside its own 145. From that pass: 946 positive teeth of 21,956; sensitivity
  7.6%; a tooth-position prior at average precision 0.0675. Only pooled figures were looked at.
- That the shipped model's 145 radiographs fall 111 / 16 / 18 across train / validation / test.
- A synthetic timing of ResNet18 on this machine. No data, no result.
- **Not seen:** any crop of the new training set; any label count for a single split; any
  output of any newly trained model; the shipped model's figures on this test split alone.

## 4. Harness checks, before any training

- **H1.** With jitter switched off, the crop builder gives rows identical in tooth, label and
  overlap to the rows saved on 13 Oct, for twenty held-out radiographs.
- **H2.** No radiograph is in two splits; the counts are 678 / 145 / 143; 590 and 1008 are out.
- **H3.** The training loop runs for one epoch on 64 crops without error. Its numbers are
  discarded.

A failed check stops everything.

## 5. Evaluation — the test split, once per seed

For each seed's best checkpoint, every tooth of the 143 test radiographs, at the argmax
decision. Radiograph-cluster bootstrap, 10,000 resamples, seed 42, percentile intervals.

- **Primary: sensitivity and specificity**, with counts; positive predictive value; F1 of the
  diseased class; macro-F1; average precision; ROC area; false flags per radiograph.
- **Against the shipped model**, on the test radiographs it never trained on (143 less its 18):
  both models on the same teeth, and the paired difference in each figure above.
- **Against a tooth-position prior** fitted on the clean crops of the 678 training radiographs:
  its average precision and ROC area, and the paired difference model minus prior.
- **Stratum:** test radiographs with a non-empty mask.
- **Seeds:** every figure for each of the three, side by side, and their range.
- **Secondary, one number:** the threshold that maximises diseased-class F1 on the validation
  set, applied once to test. It is reported to show whether 0.5 is a poor operating point. It
  is not shipped: the pipeline decides by argmax.

With fewer than 30 positive teeth in a population, sensitivity and the ranking figures are
given without an interval.

## 6. Whether the new model is eligible to replace the shipped one — fixed now

For seed 42, on test. **Eligible if and only if both hold:**

- **E1.** F1 of the diseased class, new minus shipped, on the test radiographs the shipped model
  never trained on: the lower bound of the 95% paired interval is above zero.
- **E2.** Average precision, new minus the tooth-position prior, within the test radiographs
  that carry a mask: the lower bound of the 95% paired interval is above zero. This is the
  comparison the shipped model failed.

If either fails, the new model is an ablation: reported in full, not adopted, and the result is
written as a second negative. If seed 42 passes and another seed would not have, that is
reported in the same sentence.

## 7. What this does not do

- **It changes no default.** Eligible means the decision owner may then choose to adopt it.
  Adoption would be its own recorded step: a hash pin, a version tag, a `.gitignore` exception,
  the scoreboard, the Docker image.
- **It does not make anything periodontal.**
- **It gives the new model no external figure.** Ningxia is locked and is not read. The 2.17%
  on Ningxia and the 0.75% on DENTEX belong to the shipped model.
- **It does not touch Stage 4b**, the severity model, which grades whichever teeth Stage 4a
  flags.

## 8. How the result is to be worded, fixed now

- The test figures with their intervals, the label called abnormality proximity, one source
  corpus, three seeds, and the shipped model's figures on the same teeth beside them.
- "Works", "accurate", "detects bone loss" and "periodontal" are not used. A sensitivity is
  given with its specificity and the false flags per radiograph.
- If the new model is not eligible, the manuscript says a radiograph-level split and six times
  the radiographs did not make this label learnable by this recipe.
- If it is eligible, the manuscript says what the split cost the shipped model and what the
  retrained one reaches, as a matched pair, and that no external figure exists for it.

## 9. Forbidden

A second recipe, learning rate, loss, architecture, expansion factor or class ratio after seeing
a validation or test figure; choosing a seed by its result; a second pass over test; choosing a
threshold on test; training on validation or test radiographs; reading any Ningxia image;
changing `DEF_BONE_LOSS` under this document.

## 10. Outputs and logging

`scripts/tufts/train_bone_loss_v2.py` (build, check, train) and
`scripts/eval/bone_loss_v2_eval.py` (the test pass, which refuses to run twice). Weights and
training histories under `models/18_bone_loss_radiograph_split/`; the weights stay out of git
unless adopted. Per-tooth test rows and the summary under `outputs/bone_loss_eval/v2_retrain/`.
Logged in `RESULTS_LOG.md`, `model_metrics.md` and `PAPER_MATERIAL.md` whatever it shows.
