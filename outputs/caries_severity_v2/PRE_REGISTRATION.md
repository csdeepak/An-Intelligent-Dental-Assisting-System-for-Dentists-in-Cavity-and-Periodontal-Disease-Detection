# Pre-registration — Stage 3b (caries vs deep caries) retrained and tested on DENTEX's image-level split

Written 24 November 2026, before any model has been trained under this protocol and before any
Stage-3b model of any kind has produced a prediction on a crop of the test split. **The commit that
adds this file, together with `scripts/dentex/train_caries_severity_v2.py`, is the record of when,
and is the decision owner's authorisation to train and to make the one test pass in §5.** Nothing
is trained before that commit.

## 0. Compact

| | |
|---|---|
| **Goal** | Give the Stage-3b architecture its first held-out figure: trained on one set of DENTEX radiographs, selected on a second, tested once on a third |
| **Why** | The shipped head (`models/07_caries_cascade/phase2_final_bundle.pth`) has none. Its macro-F1 0.77 was tuned and reported on the same 133 crops (`run_summary.txt`), and it was trained on crops of all 705 radiographs of DENTEX's training release, so it cannot be tested on any split of them. Every report still prints its grade, with a line saying it has no test (`scripts/run_inference.py`, `CARIES_SEVERITY_NOT_EVALUATED`). An image-level test split that labels deep caries exists and has never been used for this (`docs/session-memory/2026-10-15b-implementation-council.md`) |
| **Decision owner** | The user, who on 24 Nov 2026 asked to retrain the head and test it once, pre-registering first. The 12 Oct council's "infeasible" verdict on a first Stage-3b test rested on a label table with no deep-caries class; the 15 Oct council found the split and listed this work as allowed "with a pre-registration and the decision owner's go" |
| **What the label is** | The DENTEX annotation class of a tooth already annotated as carious: `Caries` or `Deep Caries`, as the DENTEX annotators drew it. One annotation round, no adjudication recorded here |
| **What it is not for** | In the pipeline the head grades teeth the lesion detector flags, on Stage-1 detector boxes. This test uses annotation boxes of truly carious teeth. It says nothing about flagged teeth that carry no caries, and nothing about detector-box crops |
| **What it does not test** | The shipped head. A figure here belongs to the retrained checkpoint, not to `models/07` |
| **Default change** | **None in this protocol.** Whether a retrained checkpoint replaces `models/07` as `DEF_CARIES_SEVERITY`, or the grade is withheld by default, is a separate decision recorded after §6 |

## 1. Data

- **Split:** `data/dentex/splits_v2.json` (21 Aug 2026; image-level, stratified, seed 42), over
  the 705 radiographs of DENTEX's `quadrant-enumeration-disease` training release. The separate
  50-radiograph validation release is kept apart as **extern50**.
- **Crops:** `data/dentex/crops_v2/phase2/` (`scripts/dentex/build_dentex_crops.py`), one per
  annotation of class `Caries` or `Deep Caries`. Each is a tight annotation box, floor/ceil, no
  expansion, resized to 224×224 (`crops_meta.json`). This is the pipeline's caries crop contract
  (`src/classifiers.py`). Gitignored, local.
- **Classes:** index 0 `caries`, 1 `deep_caries`, the order `scripts/run_inference.py` asserts.
- **Counts:** counted on 24 Nov before this file, as crops (caries / deep) and radiographs.

  | Split | Caries | Deep | Radiographs | Role |
  |---|---|---|---|---|
  | train | 1,564 | 400 | 456 | fit |
  | val | 314 | 94 | 96 | select the epoch |
  | test | 311 | 84 | 98 | **the one test pass** |
  | extern50 | 101 | 32 | 44 | secondary: the shipped head was tuned on these crops |

## 2. Recipe

The recipe of the Stage-4a and Stage-4b retrains (`scripts/tufts/train_bone_loss_v2.py`). Its
constants and augmentation are imported, not copied. It has two outputs.

| | |
|---|---|
| Model | ResNet18, ImageNet weights, 2 outputs. Not initialised from any caries-gate backbone (the legacy gate in `models/07` was trained on all 705 radiographs, this test split included) |
| Optimiser | Adam, lr 1e-4, weight decay 1e-4, batch 32 |
| Loss | Cross-entropy weighted n / (2 n_c) over the training classes (0.628, 2.455) |
| Augmentation | flip, rotation within 10°, brightness ×[0.8, 1.2], contrast ×[0.9, 1.1] |
| Schedule | ReduceLROnPlateau on validation macro-F1 (0.5, patience 5); early stop after 10 epochs without gain; at most 50 epochs |
| Checkpoint | Best validation macro-F1; argmax, no threshold |
| Seeds | **42, 43, 44**, each run once. **Seed 42 is fixed now as the candidate**; 43 and 44 are reported to show the spread |
| Device | MPS where available (not bit-reproducible), else CPU |
| Saved as | `{"model_state_dict", "class_to_idx"}`, the shape of `models/07`, so `load_classifier` and the pipeline's class check accept it unchanged |

## 3. What has already been seen

- The test and extern50 counts in §1, from the manifest and the crop folders.
- Every crop in all four splits was opened once on 24 Nov to confirm it is 224×224 with three
  equal channels (2,900 of 2,900). No crop was shown to any model.
- The source radiographs of every split were hashed for near-duplicates (H4). The 17 candidate
  pairs were viewed whole, without labels or predictions, as side-by-side images: 9 test, 3
  extern50, 5 val. Each pair differs in restorations, missing teeth or dentition stage. None
  is a copy, and none is excluded.
- No model trained on `splits_v2` has predicted a severity on a test crop. One exception: on
  21 Aug, `train_caries_cascade.py` was smoke-run at 1 epoch on ≤32 crops per class per split
  (`RESULTS_LOG` 2026-08-21n). Its numbers were declared meaningless, and they were never
  recorded or kept on this machine.
- `models/07` has not been scored on the test split, and will not be (§9).
- The caries **gate** (`models/09`) reported a test figure on crops of the same `splits_v2` test
  radiographs (`RESULTS_LOG` 2026-08-25). That was a different label (caries vs not), and it
  chooses nothing here.

## 4. Harness checks, before any training

`python scripts/dentex/train_caries_severity_v2.py check`, run on 24 Nov 2026. All five pass.
The output is in `check_summary.json`.

- **H1** The counts in §1 are exact. No radiograph is in two splits, and the files on disk equal
  the manifest.
- **H2** Every train and val crop is 224×224 with three equal channels, so one channel equals
  the pipeline's BGR→RGB input.
- **H3** The metrics and the three priors agree with a hand-worked example.
- **H4** Near-duplicates: no MD5 copy, and no pair close under both hashes (pHash ≤ 6 and
  dHash ≤ 4). Checked for test and extern50 against train + val, and for val against train.
  Pairs close under one hash only are listed and were inspected (§3). Method:
  `scripts/eval/dentex_near_duplicates.py`. A second radiograph of the same patient is not
  detectable this way.
- **H5** One epoch on 64 training crops runs (numbers discarded).

## 5. Evaluation — the test split, once

`python scripts/dentex/train_caries_severity_v2.py score`, after all three seeds are trained. It
refuses a second run.

**Primary: the 395 test crops on 98 radiographs.**

| Arm | What it is |
|---|---|
| seed 42, 43, 44 | The three runs |
| Majority | `caries` for every crop |
| Tooth majority | The commoner class for that FDI code among the train crops; a tie goes to `caries` |
| Tooth rate | `deep_caries` where that code's train deep-caries rate exceeds the overall train rate (400 / 1,964). This is the class-balanced analogue, as the head's loss is class-weighted |

A code absent from train gets the majority class. All three priors are image-blind and fitted
on train labels only.

**Secondary: the 133 extern50 crops on 44 radiographs.** The same arms, plus `models/07`. It
was tuned and reported on exactly these crops, so the comparison favours it.

**Reported for each arm:**

- macro-F1, with a radiograph-cluster bootstrap interval (10,000 resamples, seed 42, percentile);
- accuracy;
- deep-caries precision and recall;
- caries recall;
- the 2×2 confusion matrix.

**Paired differences, on the same resamples:** on test, seed 42 minus each of the three priors;
on extern50, also seed 42 minus `models/07`.

## 6. The rule, fixed now

- **Eligible** if, on the test split, seed 42's macro-F1 minus each of the three priors has a 95%
  interval whose lower bound is above zero.
- Seeds 43 and 44 are reported whatever happens. If either falls below a prior's point estimate,
  this is said beside the result.
- Eligible means a checkpoint *may* be proposed to replace `models/07`. It changes no default,
  and it is not a clinical validation of depth grading.
- If it is **not eligible**, the result is reported as a negative result. This protocol then
  recommends, without deciding, that the Stage-3b grade be withheld from the report by default,
  as the Stage-4b grade was on 14 Oct.

## 7. What this does not do

- No Ningxia data.
- No other cut, recipe, seed, threshold or initialisation after this commit.
- No choice between seeds after the test.
- No ensemble.
- No change to the caries gate, the lesion detector or any default.
- No claim about the shipped head.
- No claim that the DENTEX `Deep Caries` label is a clinical depth measurement.
- No test on detector boxes or on flagged teeth without caries.

## 8. How the result is to be worded, fixed now

Either way:

> "Retrained on DENTEX's image-level split, the caries-severity head (caries vs deep caries, as
> annotated) reached macro-F1 X [lo, hi] on 395 held-out crops from 98 radiographs, against Y for
> the strongest image-blind prior. Two further runs gave … The crops are annotation boxes of
> truly carious teeth; in the pipeline the head grades detector boxes of flagged teeth, some of
> which carry no caries."

## 9. Forbidden

- Re-running `score`.
- Training a seed twice.
- Reading a test or extern50 crop in `check` or `train`.
- Scoring `models/07` on the test split. It was trained on those radiographs.
- Changing §1–§6 after the commit.
- Any Ningxia data.

## 10. Outputs and logging

- **Weights:** `models/20_caries_severity_v2/seed{42,43,44}_best.pth`, local and not in git.
- **Training records:** `seed*_history.json`, tracked, each with its sha256.
- **Test outputs:** `outputs/caries_severity_v2/` holds `check_summary.json`, `test_rows.json`,
  `test_summary.json`, and the train and score logs.
- **Docs:** one `RESULTS_LOG` entry for the training and the test pass, plus updates to:
  - `model_metrics.md`, Phase 2 severity;
  - `PAPER_MATERIAL.md` §8;
  - `transfer.md`;
  - the `research_paper/` open issue 10.
