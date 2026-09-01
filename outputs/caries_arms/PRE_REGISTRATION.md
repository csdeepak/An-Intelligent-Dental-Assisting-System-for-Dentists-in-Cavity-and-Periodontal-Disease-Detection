# Pre-registration — caries gate signal arms, 31 August 2026

**Written and committed BEFORE any arm was trained.** This file fixes the metric, the
comparator and the acceptance rule in advance, so none of them can be chosen after seeing a
number. Same discipline as `T0.6_detector_reconciliation.md` §2, whose mask bar was missed and
reported as missed rather than moved.

## Why these three arms

`RESULTS_LOG.md` 2026-08-31 established, on the shipped `caries-gate-resnet18-v3.0`:

* the gate scores teeth partly by position — mean P(caries) on *genuinely healthy* teeth runs
  0.075 (incisor) to 0.478 (molar), tracking the training base rate;
* real lesion signal survives removing that prior — within-type AUC **0.7454 [0.6604, 0.8420]**;
* **three fixes already failed**: threshold tuning (0.50 already F1-optimal), per-tooth-type
  thresholds (F1 +0.006, CI spans zero), and 2.67x more positive data (AP delta −0.0015, CI
  spans zero);
* raising input resolution is a measured no-op (median box 170x287 vs the 224x224 already fed).

Data volume is therefore not the lever. The three arms below all target **signal** instead.

| arm | change | hypothesis |
|---|---|---|
| **A — CLAHE** | CLAHE (clip 2.0, 8x8 tiles) on the source radiograph before cropping | caries is a low-contrast radiolucency; local contrast equalisation should make small enamel lesions more separable |
| **B — expand 1.25x** | crop box expanded 1.25x about its centre, still resized to 224 | interproximal caries sits at the *contact point* between adjacent teeth, which a tight 1.0x box cuts through |
| **C — position balance** | `WeightedRandomSampler` equalising each (tooth type x label) cell in training | removes the incentive to use the position prior, forcing the model onto the lesion |

Arm C carries an explicit warning, recorded now rather than as an excuse later: **it may LOWER
pooled AP**, because the evaluation population genuinely has 3.4x more caries in molars and a
metric computed over it rewards using that prior. A drop in arm C is therefore *not* automatically
a failed experiment — it would be evidence that the reported score depends on the prior, which is
the paper's §8.24 thesis. That interpretation is fixed here, in advance.

## Comparator

A **same-day control**: v3's exact configuration and the frozen `crops_v3_phase1` corpus,
retrained today in this environment. All deltas are measured against the control, not against the
published 0.5503, so environment and torch-version drift cannot be mistaken for an effect. This is
the pattern used for `models/12a_fdi_head_v2_control_rebuilt`.

## Primary metric

**Average precision on the 863-crop held-out test split of `crops_v3_phase1`.**

AP, not F1 or precision/recall at a threshold, because the v4 experiment showed exactly why:
precision rose 3.6 pp and recall fell 8.7 pp while **AP did not move** — the operating point slid
along an unchanged curve. AP is threshold-independent and is the only one of the four that
measures whether the curve itself lifted.

Reported alongside, never instead of: precision, recall and F1 at 0.50, and within-type AUC.

## Acceptance rule — fixed in advance

An arm **succeeds** if its paired delta in average precision against the control has a
**95% confidence interval excluding zero**.

* Interval from a **paired cluster bootstrap over the 34 source images**, 5,000 resamples,
  seed 42 — paired, so both arms are scored on the identical resample.
* Clustered over images, not crops, because teeth from one radiograph are not independent.
* Any arm whose interval spans zero is reported as **not significant**, in the log and in the
  paper, whatever its point estimate.
* No arm is adopted as the pipeline default on the strength of this experiment alone. Swapping
  the gate invalidates the 44.3 % lesion agreement, the C1 comparison, the C4 coverage curves,
  the calibration analysis and the Ningxia externals, all measured on v3.0.

## Preconditions verified before training

Arms A and B rebuild the crops, so the comparison is only valid if the rebuilt corpora contain
the **same teeth with the same labels** — only the pixels may differ. Required, and checked:

* total crops **6,616**; test split **863** with **127** positive;
* identical `(split, label, fdi)` composition to `crops_v3_phase1`;
* identical set of `source_image_md5`.

If any arm's corpus fails these, it is rebuilt or dropped — it is not compared.

## Environment

Local, macOS M4 Pro, MPS. Measured: 8 min 16 s per phase-1 run. Four runs ~35 min. No GPU rental:
a ResNet18 at 224 px over 6,616 crops is not a compute-bound job, and `transfer.md` §6's rule is
not to rent for anything that is not compute.
