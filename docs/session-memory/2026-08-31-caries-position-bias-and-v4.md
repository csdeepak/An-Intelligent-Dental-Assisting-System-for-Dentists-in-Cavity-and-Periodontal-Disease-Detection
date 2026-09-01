# 2026-08-31 — Why caries precision/recall are low, and what did not fix it

## Session goal

Answer "precision and recall are very low, how do we improve them" for the caries branch —
diagnose the cause from the artefacts, then run the highest-value fix the diagnosis implied.

## What was done

**Diagnosis first, and it was anchored to a known reference before anything was concluded.**
Every analysis reproduced the published test confusion matrix (TP 94 / FP 142 / FN 33 /
TN 594) as a correctness gate. Findings:

- **The gate scores teeth partly by which tooth it is.** Mean P(caries) on *genuinely healthy*
  teeth tracks the training base rate for that position: 0.075 on healthy incisors (base rate
  0.017) up to **0.478 on healthy molars** (0.343). **48.2% of healthy molars are flagged** —
  79 of the 142 false positives. That is where precision 0.398 goes. Symmetrically the gate
  finds **1 of 8 incisor lesions**.
- **Real lesion signal survives removing the prior.** Within-tooth-type AUC **0.7454, 95% CI
  [0.6604, 0.8420]** (excludes 0.5). Pooled AUC 0.8548 is inflated because ranking a molar above
  an incisor is free. A position-only predictor scores AP 0.2962 vs the model's 0.5503.
- New re-runnable script: `scripts/eval/caries_position_bias.py` → `outputs/caries_position_bias/`.

**Then three candidate fixes, tested rather than assumed. All three failed, and all three are
recorded:**

1. **Threshold tuning — exhausted.** The shipped 0.50 is already F1-optimal across a 19-point
   sweep.
2. **Per-tooth-type thresholds** (fitted on val, applied once to test): F1 **+0.006, 95% CI
   [−0.034, +0.041]** — not significant, and no better than re-fitting one global threshold.
3. **Gate v4 on 2.67× the positives.** Found that DENTEX carries **2,767** caries-family
   annotations while the corpus used **1,049** — **62% unused**, because the MD5 join that makes
   healthy teeth derivable covers only 260 of 705 images. Added the 445 disease-only images as
   positives (`build_caries_phase1_v3.py --include-disease-only`, new opt-in flag). Train
   positives 723 → 1,928. On the **same** 863-crop test set: **AP 0.5503 → 0.5496, paired delta
   −0.0015 [−0.0886, +0.0821]**. Every paired delta spans zero. **Not adopted.**

**Also ruled out by measurement, not argument:** raising input resolution. Median tooth box is
170×287 px against the 224×224 already fed to the model — a 1.04× linear resize, 58% of boxes
already upsampled. A prior hypothesis that the square resize leaks tooth identity via aspect
ratio was **falsified** — crops are stored pre-squared, so no shape cue exists; the model reads
tooth type from genuine appearance.

**Written up:** `RESULTS_LOG.md` 2026-08-31, `PAPER_MATERIAL.md` §8.24 (new),
`model_metrics.md` (stratified table added under Stage 3), `outputs/caries_v4/run_summary.txt`.

## Decisions made

- **v4 is not adopted.** It is not better, and swapping it would invalidate the 44.3% lesion
  agreement, the C1 comparison, the C4 curves, the calibration analysis and the Ningxia
  externals — all measured on v3 — in exchange for nothing. Same reasoning that kept Stage-2
  head v3 an ablation (2026-08-28c).
- **The expansion adds positives only, no healthy teeth.** Without an enumeration twin there is
  no list of which teeth are present. The alternative — running the detector and calling every
  unannotated box healthy — would inject detector false positives into the negative class. That
  choice is also the most likely reason the experiment failed, and it is stated as such rather
  than hidden: the decision boundary is set by the negatives, and the negatives did not grow.
- **The new capability was added as an opt-in flag on the existing builder**, not a copied
  script, so the crop contract is literally the same code. The default path was verified to
  reproduce the frozen v3 corpus exactly (4,750/1,003/863, healthy 5,366, ambiguous 856).
- **A leakage guard now runs in both modes.** Any image byte-identical to one in the
  `DENTEX/disease/` evaluation pool is refused. Exactly one qualifies — `train_332.png` ≡
  `test_181.png`, already on record as `leaked_into_detector_training`. The v3 corpus never
  contained it; the guard is what keeps any future expansion clean.
- **The diagnostic is a paper contribution, not just debugging.** §8.22 reports that an
  image-blind constant beats the pipeline and treats it as a property of the metric. §8.24 now
  shows the gate *itself* has partially become that constant, and quantifies it. That upgrades
  the headline finding from an observation about scoring to a measured statement about the
  system.

## Open questions

- **A number in `outputs/caries_v4/arm_b/phase1_gate_report.txt` is a trap.** It shows caries
  P 0.71 / R 0.80 on v4's *own* test split, against v3's published 0.398/0.740. That is a **2.2×
  prevalence difference** (0.324 vs 0.147), not an improvement — specificity is unchanged (0.853
  vs 0.843). Flagged in three places (run summary, RESULTS_LOG, §8.24) because it is exactly the
  kind of number that reaches a slide intact.
- **Untested levers, all targeting signal rather than data volume:** CLAHE contrast
  normalisation; a slightly expanded caries crop (interproximal caries sits at the contact point,
  which a tight 1.0× crop cuts through); position-balanced sampling. The last attacks the measured
  shortcut directly but may *lower* pooled F1, since that metric rewards using the prior — which
  would itself be a publishable result.
- **The negative class cannot grow inside DENTEX** without new assumptions. Enumeration images
  with no disease twin are not evidence of health.
- Whether the caries branch is simply at its headroom on this data. Three independent fixes
  moved nothing; that is now the leading hypothesis rather than a worry.

## Addendum, same session — the three signal arms were run, and all three missed

Pre-registered first (`outputs/caries_arms/PRE_REGISTRATION.md`, written before any arm trained):
primary metric **average precision** on the 863-crop test split, comparator a **same-day control**,
success = paired ΔAP with a 95% CI excluding zero. Ran locally on MPS, ~8 min per run, 4 runs; no
GPU rented — a ResNet18 at 224 px over 6,616 crops is not compute-bound (`transfer.md` §6).

The control reproduced v3's published val macro-F1 **exactly (0.7350)**, so drift is not confounding.

| arm | AP | ΔAP vs control | verdict |
|---|---|---|---|
| control | 0.5503 | — | — |
| **CLAHE** | 0.5977 | **+0.0488 [−0.0031, +0.0993]** | **misses by 0.0031** |
| crop 1.25× | 0.5684 | +0.0198 [−0.0367, +0.0810] | not significant |
| position-balanced | 0.5943 | +0.0432 [−0.0328, +0.1157] | not significant |

- **The bar was missed and not moved**, in the same terms as R1's mask bar. Nothing adopted.
- **Real secondary effect:** CLAHE gains precision **+5.6 pp [+0.011, +0.101] with no significant
  recall cost** — the only arm where that holds; FP rate falls in every stratum. The 1.25× arm's
  precision gain is cancelled by a *real* recall loss, i.e. a slide along an unchanged curve.
- **A pre-registered prediction was falsified**, and that is recorded rather than quietly dropped:
  the pre-registration warned arm C might *lower* AP because the population carries 3.4× more
  caries in molars. It did not.
- **CLAHE does not fix the anterior blindness** — incisor recall stays 0.125, canine goes to 0.000,
  and the prior is still visible (healthy-tooth score 0.037 incisor → 0.443 molar).
- **The experiment is underpowered and this is the real limitation:** 863 crops but only **34
  source images**, with intervals correctly clustered over images. A +0.049 AP effect cannot be
  separated from zero at n=34. Only more held-out images settle CLAHE.

New surface: `--clahe` / `--crop-expand` on the builder, `--balance-position` on the trainer,
`scripts/eval/caries_arms_compare.py`. All default paths unchanged and still reproducing the
frozen v3 corpus exactly.

## Next steps

1. **CLAHE is the one live candidate.** It is not adoptable on this evidence, and no further
   modelling arm on this split will settle it — the blocker is 34 source images, not method.
   A confirmatory run would need a larger held-out image set (e.g. v4's 1,218-crop split, which
   is a different item set and needs its own control).
2. **Five independent attempts have now failed to lift this curve.** "The caries branch is at its
   headroom on DENTEX" is now the supported reading rather than a worry — and it is a citable
   result, not a gap. Write it into §8.24 that way.
3. Fold §8.24 into `paper/main.tex` beside the §8.22 constant-baseline discussion — it is the
   mechanism behind the paper's headline and costs no compute.
4. Unchanged and still the actual critical path: venue-length cut, the four compliance
   blockers, and uploading `models/11_yolo_seg_tufts_r1/best.pt` to Drive.
