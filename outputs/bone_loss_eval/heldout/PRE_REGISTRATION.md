# Pre-registration — the frozen Stage-4a classifier on Tufts radiographs it never trained on

Written 13 October 2026, before any tooth of the held-out radiographs has been cropped, labelled
or scored. The commit that adds this file is the record of when.

## 0. Compact

- **Goal:** the first held-out figure for the Stage-4a classifier, for the label it was
  actually trained on.
- **Decision owner:** the user, who decided on 12 Oct that the branch stays in the paper
  (`docs/results/RESULTS_LOG.md` 2026-10-12c) and on 13 Oct said to run this.
- **What this is:** an estimate. Nothing here trains, tunes, re-thresholds or changes a model, a
  default, a hash or a parameter count.
- **What it cannot do:** make the branch a periodontal classifier. Its positive class is "the
  crop overlaps a Tufts expert abnormality mask" (`PAPER_MATERIAL.md` §8.28). A held-out score
  is a held-out score for that label.
- **Reverses:** `transfer.md` §3 listed this as deferred until after submission. The decision
  to keep the branch in the paper is what brings it forward.

## 1. Frozen configuration

| | |
|---|---|
| Model | `models/03_bone_loss_model_training_notebook_models/bone_loss_resnet18_best.pth`, sha256 `c52f7f484076a2a2c3c144c3351912b118b6b0d56fc51ba1b4296e6ce6213db1` |
| Classes | index 0 normal, index 1 diseased (`models/03_…/run_summary.txt`) |
| Decision | argmax, which for two classes is P(diseased) ≥ 0.5 — what `src/classifiers.run_bone_loss` ships |
| Input | the crop as the training notebook's validation transform saw it: 224×224 grey crop, three identical channels, ImageNet mean and standard deviation |
| Device | CPU |
| Sources | `_repo_archive/datasets_workspace/Radiographs/` (1,000, landscape), `Expert/mask/` (1,000), `Segmentation/teeth_bbox.json` (md5 `8fb9182c1f5c98a5ea8a231469f7ba80`) |

## 2. The crop and the label — the construction notebook's recipe, clean crops only

From `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`, cells 5, 9, 14, 16 and 18,
reproduced and not re-designed:

- A box is `teeth_bbox.json`'s `bounding box` read as `[y1, x1, y2, x2]` on the landscape
  radiograph. Boxes under 3 px in either dimension are dropped. Deciduous teeth are kept.
- The crop is the box widened 1.5× and heightened 2.0× about its centre, corners truncated with
  `int()`, clipped to the image, then resized to 224×224 with `cv2.INTER_LINEAR` from the
  radiograph read in greyscale.
- A radiograph whose mask is all zero gives label 0 for every tooth. Otherwise the label is 1
  when more than 1% of the crop's pixels are non-zero in the expert mask.
- **No jitter.** The notebook also made a ±15% jittered copy of every crop from random offsets
  that were never saved. Those cannot be regenerated and are not part of this measurement.

## 3. Population

Every radiograph of the 1,000 that supplied no crop to either manifest
(`data/tufts/resampled_dataset/metadata/{train_resampled,val}_metadata.csv`; 145 radiographs
did). That is 855. From those: of any radiographs that are byte-identical to each other, only
the lowest-numbered is kept (the two known pairs are 590/591 and 1007/1008); any within a
256-bit difference-hash distance of 10 from a radiograph among the 145 is excluded and listed.
Every tooth those radiographs yield under §2 is scored. Nothing is sampled.

Two strata are reported beside the whole: radiographs with a non-empty expert mask (290 before
the exclusions above), where both labels occur, and radiographs with an empty one, where every
tooth is normal.

## 4. What has already been seen

- The validation figures: macro-F1 0.9233, sensitivity 49 of 59, specificity 1,492 of 1,499, on
  1,558 crops of which 773 are jittered. On the 35 clean validation positives the model finds
  29 (measured on the original crops, 7 Sep, on the other machine).
- That those figures are not held out: all 143 validation radiographs supply training crops,
  and 46 of the 59 validation positives share a tooth with a training positive.
- That 339 of the 1,000 expert masks are non-empty, 290 of them on radiographs outside the 145.
- One council member's guess at the held-out sensitivity, 0.35 to 0.70. A judgement, not a
  measurement.
- That the model flags 2.17% of affected teeth on Ningxia periodontitis and 0.75% of teeth on
  DENTEX. Different labels; no bearing on this population.
- **Not seen:** any crop, label or model output for any tooth of the 855 radiographs. Not even
  how many of their teeth are positive.

## 5. Gates — run on the 145 training-side radiographs, before any held-out tooth is touched

The original crop files are not on this machine; only their manifests are. So the builder is
checked against the manifests and against the one model result on clean crops that exists.

- **G1, labels, no model.** The builder is run on the 145 radiographs. Every clean,
  non-augmented manifest row is matched to a regenerated crop by radiograph and tooth title. At
  least 99% of the manifest rows must find a crop, and at least 99% of those must carry the same
  label.
- **G2, geometry and input, with the model.** On the regenerated crops of the 35 clean
  validation positives the frozen model must find 28, 29 or 30. The reference is 29, measured on
  the original files on the other machine; one tooth of tolerance covers the machine. On the 750
  clean validation normals its specificity must be at least 0.98.

A failed gate stops everything. The held-out radiographs are not opened until it is explained.
**The gate's numbers are training-side figures and are never reported as results.**

## 6. What is reported, fixed now

For the whole population and for each stratum, with a 95% interval from a cluster bootstrap over
radiographs (10,000 resamples, seed 42, percentile):

- **Primary: sensitivity and specificity** at the shipped decision, with their counts.
- Positive predictive value, F1 of the diseased class and macro-F1, with the prevalence beside
  them. Macro-F1 is given because 0.9233 is a macro-F1; the two are on populations of different
  prevalence and are not a like-for-like pair.
- Average precision and the area under the ROC curve.
- **Two image-blind baselines.** Flag nothing and flag everything, as counts. And a
  tooth-position prior: for each tooth title, the diseased share among the clean manifest rows
  of the 145 radiographs, one row per radiograph and tooth, used as a score (a title absent from
  those rows gets the overall share). Its average precision and ROC area, and the paired
  difference model minus prior on both, resampling the same radiographs.
- The count of radiographs and teeth, the exclusions, and the positive teeth per stratum.

With fewer than 30 positive teeth in the population, sensitivity and the two ranking figures
are given as counts and point values with no interval.

## 7. How the result is to be worded, fixed now

- The manuscript states the held-out sensitivity and specificity with their intervals, calls
  the label abnormality proximity, and says the crop-level validation figure was 0.83 and 0.995
  on radiographs the model had trained on. It gives the difference without an adjective.
- **0.9233 appears only as "crop-level validation, not held out"**, if at all.
- If the model's average precision is not separated from the tooth-position prior's — the
  paired interval includes zero — the manuscript says the classifier is not shown, on held-out
  radiographs, to read more than which tooth it is looking at.
- Whatever the result, the words "periodontal", "bone loss" as a finding, "domain shift" and
  "does not transfer" are not attached to it.
- A high figure is not evidence about periodontal disease, and a low one is not evidence about
  the detector or the rest of the pipeline. Neither is written as either.

## 8. Forbidden

A second pass with another threshold, expansion factor, overlap rule or interpolation; scoring
jittered or augmented crops; dropping a stratum or a radiograph because of its result; retraining
or fine-tuning anything; reading any Ningxia image; reporting a gate figure as a result;
intervals, calibration or a precision–recall sweep on the old validation set.

## 9. Outputs and logging

`scripts/eval/bone_loss_heldout.py` — `gate`, then `score`, which refuses to run without a
passed gate and refuses to run twice. Artefacts under `outputs/bone_loss_eval/heldout/`: the
gate's result, the per-tooth rows of the held-out pass and the summary. Logged in
`docs/results/RESULTS_LOG.md`, `model_metrics.md` and `PAPER_MATERIAL.md` whatever it shows.
