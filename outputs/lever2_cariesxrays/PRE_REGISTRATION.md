# Pre-registration — Lever 2: CariesXrays caries-lesion detector, 2 September 2026

**Written and committed BEFORE the dataset was built or any GPU rented.** Fixes the metric, the
comparator and how the result is reported, so none can be chosen after seeing a number. Same
discipline as `outputs/detector_multicorpus/PRE_REGISTRATION.md` (Lever 1) and
`T0.6_detector_reconciliation.md` §2.

## What Lever 2 is

A **standalone YOLOv11l caries-lesion detector** trained on the CariesXrays benchmark (Chen et
al., *AAAI 2024* 38(20) 21940–21948, DOI 10.1609/aaai.v38i20.30196; 6,000 panoramic images,
13,784 non-degenerate "Decay" boxes here vs their stated 13,783). It is **not wired into the
six-stage pipeline** and adopts no checkpoint. It exists to give the project one number on a
public benchmark's own metric — the thing a reviewer can place against published work.

Why it is worth doing: the pipeline has a tooth-level caries **gate** (ResNet18 over per-tooth
crops) that an image-blind molar constant ties or beats across six cohorts
(`PAPER_MATERIAL.md` §8.22/§8.24). It has **no lesion *detector*** at all. This is that model,
and CariesXrays is 13× the caries supervision of the DENTEX gate corpus.

## ⚠️ The split is NOT the official one

The FPCL 4,800/1,200 split is **not public** — checked the FPCL GitHub repo (ships a 0.5%
sample, no `ImageSets`), the Google-Drive download (`Annotations.zip` + `JPEGImages.zip` only),
and the DVCTNet release (`github.com/ShanghaiTech-IMPACT/DVCTNet` — its own dataset, application-
gated). DVCTNet's paper used "the original split … for fair comparison", so it exists but was
obtained privately from the FPCL authors.

**This experiment uses its own `seed-42` image-level 80/20 split (4,800 / 1,200), matching their
*ratio* only.** Every number it produces is *"same dataset, same ratio, same metric, different
random test images"* — **indicative of where an off-the-shelf detector lands relative to the
published table, NOT a head-to-head result**. The write-up must say this in these words and must
never read as "we beat / lost to FPCL". If a genuine head-to-head is wanted later, email the FPCL
authors (`chenbingzhi@m.scnu.edu.cn`, `darrenzz219@gmail.com`) for the split and re-run.

## Comparator — the published FPCL table, transcribed here, frozen

COCO AP (%), from Chen et al. Table on the CariesXrays test set (**re-verify against the AAAI PDF
before any of this goes in `main.tex`** — currently transcribed from the paper text + the DVCTNet
reproduction, arXiv 2508.20813):

| method | backbone | AP | AP50 | AP75 |
|---|---|---|---|---|
| RetinaNet | ResNet-50 | 13.0 | 30.5 | 10.2 |
| DINO | — | 37.8 | 75.3 | 29.4 |
| Faster R-CNN | ResNet-50 | 39.9 | 78.0 | 37.8 |
| YOLOX | CSPDarknet | 40.5 | 81.3 | 36.1 |
| **FPCL (their method)** | ResNet-50 | **48.2** | **84.1** | **50.6** |
| DVCTNet (MICCAI 2025) | DINOv2-ViT-B | 48.9 | 84.7 | 52.2 |

## Primary metric and how the result is reported — fixed now

**Primary: COCO AP@[.50:.95] on this project's 1,200-image held-out val split**, from
`ultralytics ... val` (101-point interpolation, the same definition as the `pycocotools`
`CocoEvaluator` the FPCL repo uses). **AP50 and AP75 reported alongside, never instead of.**

**This is a measurement, not a pass/fail gate.** There is no acceptance threshold and nothing is
adopted. Whatever AP the single trained model reaches is reported once, in `RESULTS_LOG.md` and
as one row in `main.tex` §Related Work, beside the table above, with the split caveat. Rules
fixed in advance:

* **One model, one training run** at the config below. No architecture sweep, no
  train-until-it-beats-a-number loop. A second run happens only to fix a *documented*
  misconfiguration, and both are reported.
* The number is **not** described as SOTA, not as beating any baseline, and not as a
  pipeline improvement. Expected outcome, stated now: **~40–46 AP** — competitive with the
  generic baselines (YOLOX 40.5, Faster R-CNN 39.9), likely below FPCL's 48.2. If it lands
  higher or lower, that is the result.
* If AP is *far* below the baselines (say < 30), that is a build/training bug to find, not a
  finding to report — check the geometry gate output and the loss curves first.

## Training config — fixed now

Every value copied from the canonical bbox run's `train_args.yaml` (via
`scripts/yolo/train_multicorpus_detector.py`), so Lever 2 trains detectors the way this project
already does. The **only** deliberate differences from that config:

| | value | note |
|---|---|---|
| model | `yolo11l.pt` (COCO-pretrained), `detect` | same as Lever 1 |
| classes | 1 — `decay` | vs `tooth` |
| dataset | `data/cariesxrays_det` (this project's seed-42 4,800/1,200 split) | the whole point |
| epochs / patience | **120 / 25** | canonical is 150/30; trimmed to cap worst-case cost. Early stop expected ~80–110 (the canonical run stopped at 105–128). |
| image size | **1024** | canonical. Lesions are small (median box ≈ 60×75 px in a ~2440×1280 image); going lower loses them — see risk 3. |
| batch | **32** (fall back to 16 on OOM, recorded) | canonical |
| optimizer / lr | AdamW, lr0 1e-3, lrf 0.01, cos_lr, warmup 3 | canonical, unchanged |
| augmentation | `hsv_v=0.2, degrees=10, translate=0.1, scale=0.2, fliplr=0.5`; **`mosaic=0.0`, `flipud=0.0`, `mixup=0.0`** | canonical. **`mosaic` is OFF by this project's house rule** ("corrupts spatial context in medical imaging"). Mosaic normally helps small-object AP a lot, so this is a *conservative* choice that may cost a few AP points — recorded now, not offered as an excuse later. |
| seed | 42 | canonical |
| ultralytics | pinned **8.4.127** on the rented box | matches the frozen models + the local env |

Deviations from this table are recorded in `run_summary.txt` with the reason.

## Local gate before any rental (in `build_cariesxrays_detector_dataset.py`)

1. Box w/h from the **decoded image**, never the XML `<size>` (27.3% carry a wrong width —
   `RESULTS_LOG.md` 2026-08-27a is the cautionary precedent).
2. Every converted box round-trips (YOLO-norm → pixel xyxy) to within **1 px** of the source.
3. 0 normalised coords outside [0, 1]; 0 stems shared between train and val; image count ==
   label count.
4. 12 rendered samples in `data/cariesxrays_det/_check/` inspected by eye — boxes on lesions,
   not shifted by the ~8.5% a stale width would imply.

Only after all four pass is anything tarred or rented.

## Cost, fixed in advance

A100-40GB @ **₹84.24/hr** (or A100-80GB spot, same price), read from `jl gpus` 2 Sep. Estimate:
~0.5 h boot + upload of one ~4 GB tar, ~2.5–3.5 h training (100 epochs, 4,800 images, 1024 px),
~0.2 h eval + packaging ⇒ **~₹280–360** of the ₹816.70 balance. One redo budgeted. Re-run the
geometry gate **on the rented box** after upload before launching — cheap insurance the Lever-1
runbook added the hard way.

## Risks recorded in advance

1. **Our split ≠ their split** — already the headline caveat above. Repeated here so it is in the
   risks list too: the comparison is indicative, and a reviewer who wants exact numbers needs the
   official split.
2. **CariesXrays annotation exhaustiveness is undocumented** (`cariesxrays_external.py` docstring).
   AP treats every un-boxed region as negative; if some real lesions are unannotated, AP is a
   slight under-estimate for everyone in the table equally — it does not bias the *comparison*.
3. **Small objects.** Median lesion ≈ 60×75 px in a ~2440×1280 image. 1024-px training already
   downsamples ~2.4×; going lower would lose them. Recorded so a future "train at 640 to save
   money" is visibly against the pre-registration.
4. **Licence.** CariesXrays ships **no LICENSE file** (GitHub API confirms none); the authors ask
   only for citation. Used here for research, cited as they ask, described as "publicly released
   without an explicit licence" — same wording as `main.tex` §8.25.
