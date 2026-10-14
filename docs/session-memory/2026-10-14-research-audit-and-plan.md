# 2026-10-14 — Research-driven audit, and the implementation plan that follows from it

**Session goal:** the user asked for a senior-MLE audit of the whole pipeline — every stage, every
figure's colour scheme, the earlier councils' advice — checked against published research found
with Firecrawl, ending in a prioritised plan; then asked for the plan to be made complete. Plan
only: no code, model, figure or manuscript was changed, nothing was scored.

**This file is the plan for implementation.** It absorbs
`2026-10-13g-implementation-plan-for-14-oct.md` (tasks T0–T8 keep their numbers and their detail
is repeated in §6, so this file can be followed alone) and adds tasks V1–V2 (verification), F1–F7
(figures and colour), W1–W2 (wording).

## What was done

- **Read:** the five figures `paper/main.tex` includes (opened as images) and their captions
  (lines 763–781, 1069–1077, 1099–1107, 1147–1156, 1218–1231); the seven README graphics (colours
  and text extracted from the SVGs); the overlay code (`scripts/run_inference.py:476-498`) and the
  app caption (`app.py:124`); the figure scripts; the Stage-4a training recipe
  (`scripts/tufts/train_bone_loss_v2.py`); the Stage-4a training and serving crop code
  (`scripts/eval/bone_loss_heldout.py:44-86`, `src/classifiers.py:121-158`,
  `src/crop_generator.py:18-39`); the bootstrap code; `test_summary.json`; the council records of
  11 Oct (d, e), 12 Oct (a, b, c) and 13 Oct (f); `docs/paper/REBUILD_AUDIT.md`.
- **Research:** Firecrawl's paper search and paper reader (no credits charged), Europe PMC's open
  full-text API for five open-access papers, one Firecrawl scrape of the PyTorch docs (5 credits).
  Fourteen sources verified; §4 says for each whether the full text or only the abstract was read.
- **Corrected the same day, while making the plan task-level** (the first version of this file
  said otherwise):
  1. A near-duplicate check **does exist** — a 256-bit difference hash with a 10-bit threshold,
     `scripts/eval/bone_loss_heldout.py:129-132, 186-199` — but it compared only the previous
     model's 145 training radiographs with the other 853 (none found,
     `outputs/bone_loss_eval/heldout/heldout_summary.json`). The retraining split's train, val and
     test were never compared with each other. V1 reuses that code and threshold.
  2. A **validation-chosen threshold for Stage 4a was already pre-registered and measured**
     (`test_summary.json`, `validation_threshold_on_test`): seed 42, threshold 0.465, sensitivity
     29.1%, specificity 95.0%, F1 0.252 against `argmax`'s 0.260. No gain, and Amendment 1 forbids
     another threshold. The experiment proposed for it (E2) is closed.
  3. Stage-4a crop geometry is the **same formula** in training and serving
     (`expanded_box` ≡ `compute_expanded_bbox`); what differs is only the image decode (greyscale
     read vs BGR read). V2 is now a cheap guard expected to pass, not a suspected fault.
  4. Two more stale items: `docs/assets/pipeline.svg` (the architecture diagram) and the README
     tagline at line 18, "caries and periodontal bone-loss screening".
- **Not done:** the EDA notebooks' plots were not audited (none is in the paper); the CVD
  simulation proposed in §2 was not run.

---

## 1. Executive diagnosis

The pipeline's numbers cannot be raised before submission without spending data the project has
already used. The audit therefore finds defects of **claim**, **display** and **verification**,
not of model quality. Ranked by consequence:

1. **Published-facing graphics still assert a result the project withdrew.** Paper Fig. 5
   (`fig_boneloss.png`), `domain-shift.svg` and `pipeline.svg` show the previous Stage-4a model's
   0.923 — a crop-level split with radiograph leakage; that model found 7.6% of affected teeth held
   out. Fig. 5 and `domain-shift.svg` put it in "success" teal beside "failure" crimson. The README
   tagline and banner say "periodontal", wording the 12 Oct decision forbids. *(P0)*
2. **The report and the demo say things that are false** (13f, re-verified): a stale caries caveat,
   a "no model trained on these radiographs" sentence false for Stage 4b, the wrong numbering-head
   tag in every report, two unpinned default checkpoints, a Stage-4b "Mild/Moderate/Severe" grade
   that is an image-contrast band. *(P0)*
3. **The overlay's colours invert their meaning for a clinician.** Red marks a tooth the pipeline
   could *not* assess; a reader takes red as the most urgent. Orange merges three different flags.
   Red and orange separate mainly along the red–green axis. *(P1)*
4. **The retraining split was never checked for near-duplicates across train, val and test.** Two
   byte-identical pairs exist in Tufts (590/591, 1007/1008, dropped). A near-twin across the split
   would be leakage of the kind that produced 0.923. *(P0 check, no labels touched)*
5. **Two disclosures are missing from the Stage-4a paragraph:** the three seeds share one
   pre-computed jitter set, so their spread is a lower bound on training variance; and the printed
   "confidence" is a softmax trained at ~22% effective prevalence (3.5:1 undersampling,
   class-weighted focal loss) and applied at 4.7%, so it is not a probability. *(P1 text)*
6. **What the evidence does not support now:** recalibration, ensembling or a second seed, each
   needing unseen data; and a threshold for Stage 4a, already measured without gain. The councils'
   freeze stands; §5 shows where the research agrees and where it qualifies it.

---

## 2. Colour-scheme audit

**The palette as a whole.** Across the paper's figures navy means "our pipeline"; crimson the
constant (Fig. 1), raw uncalibrated output (Fig. 3) *and* external failure (Fig. 5); teal a correct
tooth (Fig. 2) *and* the 0.923 in-domain score (Fig. 5); coral a numbering error (Fig. 2) *and* the
pre-registered threshold (Fig. 4). One hue, three meanings. The fix is one semantic palette for the
paper: default model · retained alternative · reference (constant, previous model) · neutral ink.
Good/bad hues never encode a cohort or a metric.

| # | Visualization | Current color implication | Why it is incorrect or misleading | Recommended fix | Validation method | Class |
|---|---|---|---|---|---|---|
| 1 | **Paper Fig. 5**, `paper/fig_boneloss.png` (`scripts/figures/make_boneloss_paper_figure.py:42-44`) | Teal 0.923 = "works in domain"; crimson bars = "fails outside" | The teal bar is a crop-level-split validation score (radiograph leakage) of a model no longer the default. Panel (b) puts a firing rate (DENTEX, no labels) and sensitivities (Ningxia) in one crimson series under one axis label. The hue pair asserts a validity the 12 Oct decision withdrew; "out of domain" / "domain shift" are banned wording (`SUBMISSION_TODO.md` §2 item 3) | F2 (§6) | F2's checks | **Analytical** |
| 2 | **Paper Fig. 1**, `paper/fig_baselines.png` (`make_baseline_figure.py:37-40`) | Navy = one system, "ours"; crimson = the constant to beat | Navy encodes two caries methods. In (b) the navy bar above the constant (0.802) is the retired gate; the shipped default is the navy bar below it (0.595). The two navy bars swap order between (a) and (b). Skimming by colour gives "ours beats the constant everywhere". Crimson for the reference is consistent and fine | F3 (§6) | F3's checks | **Analytical** |
| 3 | **Paper Fig. 4**, `paper/fig_coverage.png` (`scripts/eval/c4_coverage_accuracy.py:234-240`) | Two similar falling curves, both "gain"; a coral line reads as a warning | Independent truncated y-ranges (93–100, 80–100) make an effect of about one point and one of about fifteen look alike. The low-coverage end rests on few teeth. The shuffled-confidence control the claim rests on is computed (lines 79–114) but not drawn | F4 (deferred) | — | Analytical, moderate |
| 4 | **Paper Fig. 3**, `paper/fig_calibration.png` (`scripts/eval/isotonic_calibrate.py:168-169`) | Crimson raw = bad, navy isotonic = good; the dip at ~0.83 looks real | Equal-width bins without counts; sparse high-confidence bins; ECE with no interval. Equal-width ECE is the more biased estimator (R10) | F5 (deferred) | — | Analytical, minor |
| 5 | **Paper Fig. 2**, `paper/fig_stage2.png` (`scripts/eval/stage2_failure_taxonomy.py:167-179`) | Teal correct, grey undetected, coral wrong; per-position bars equally certain | Hue mapping right. The right panel has no denominators, so third molars weigh like premolars. Snake-case labels | F6 (deferred) | — | Minor + cosmetic |
| 6 | **README banner** `docs/assets/hero.svg`, alt text `README.md:3`, tagline `README.md:18` | Teal tiles = today's headline results | Four of five tiles stale (0.810, 58.3%, 0.9233, 97.7 M). Subtitle "YOLOv11l-seg" and "caries and periodontal bone loss"; tagline "caries and periodontal bone-loss screening" — forbidden wording | T4 + F7 | `grep -i periodontal` on both files | Content error |
| 7 | **Architecture diagram** `docs/assets/pipeline.svg` (`README.md:144`) | Current architecture and numbers | "YOLOv11l-seg", 0.810, 58.3%, the gate as the caries path, "BONE-LOSS PATH" with 0.9233 / sens 83.1% / spec 99.5%, a "mild / mod / severe" head with 0.7208 | F7: text corrected in place | Each new number matched to `docs/results/model_metrics.md` | Content error |
| 8 | `docs/assets/domain-shift.svg` (`README.md:300`) | Amber caries "degrades gracefully", rose bone loss "does not transfer", teal 0.9233 = success | Same good/bad encoding of the leaked 0.9233 as Fig. 5; banned wording. Caries numbers appear to be the retired gate under an earlier detector; "never trained or tuned on" holds for the gate only (Ningxia informed the lesion detector's adoption) | F7 [D5] | README renders | **Analytical** |
| 9 | `error-propagation.svg`, `baselines.svg`, `abstention.svg` (`README.md:237, 208, 329`) | Current results | Previous-detector numbers (58.3%, 0.294, 661 teeth). "The errors that remain are overwhelmingly benign" is editorial: an off-by-one code attaches a finding to the wrong tooth | F7 [D5] | README renders | Content |
| 10 | **Overlay**, `scripts/run_inference.py:476-498`; caption `app.py:124` | Red box = most urgent tooth; orange = something found; blue = healthy | Red means "not assessable" — absence of a finding in the colour of alarm. Orange merges a numbering doubt, a caries finding and an abnormality flag. Red (RGB 220,60,60) and orange (255,165,0) differ mainly along red–green, hard to separate under deuteranopia or protanopia (R8; up to 8% of men, R9) | F1 [D6] | F1's checks | **Clinical-semantic** |
| 11 | Enumeration confusion matrices (`scripts/dentex/train_enumeration_head.py:250`); `scripts/figures/make_stage34_figures.py:48` | Darker = more | BuPu on row-normalised values with `vmin=0, vmax=1` is correct for proportions. `make_stage34_figures.py` uses Blues on raw counts (not in the paper): under imbalance only the majority cell shows | None now; row-normalise if reused | — | Cosmetic |
| 12 | `src/utils/visualization.py` | — | No importer anywhere | Mention only; not deleted | — | — |

**No problem invented:** Fig. 2's left panel and the confusion matrices use colour correctly.
Fig. 1's crimson for the constant is deliberate (`make_baseline_figure.py:37`) and consistent.

---

## 3. Stage-by-stage audit

The request's tabular-competition items (imputation, categorical encoding, scaling, sample
submission) have no counterpart here. Their image-pipeline equivalents are covered: crop and
normalisation parity (preprocessing), report schema (submission format), split integrity (leakage).

### A. Data and EDA (all corpora)

| | |
|---|---|
| Current | Tufts 1,000 radiographs, frozen radiograph-level split 700/150/150 (`outputs/eda_tufts/split_v1.csv`); byte-identical pairs dropped (`train_bone_loss_v2.py:39`). DENTEX 705 + 164 development images, no patient identifier (`PAPER_MATERIAL.md:718-720`); the 164 were checked against detector training images (MD5 + 256-bit difference hash, nearest 42 bits; `RESULTS_LOG.md` ~7778-7784). CariesXrays 1,200 = the lesion detector's validation split. Ningxia locked. UFBA-425 unseen. |
| Flaw | Near-duplicates never compared across the retraining split (train/val/test). Stage 4b's radiographs 149, 192, 249 sit in the Tufts test split (13f). EDA plots not audited. |
| Why | Near-twins across a split inflate held-out figures by the mechanism that produced 0.923 (R1: 29–55 accuracy points from slice-level splitting). |
| Fix | **V1** (§6). |
| Alternative | Embedding similarity (R2 used fastdup): stronger, but a new dependency. |

### Stage 1 — tooth detector (`models/15…/arm3c_best.pt`)

| | |
|---|---|
| Evidence | Tufts test box mAP@0.5 0.587 (Tufts-only control 0.723); recall 89.3% Tufts, 99.6% DENTEX (in-domain); UFBA-425 recall 66.6% as distributed. One training run. |
| Flaw | Adopted against two pre-registered verdicts (disclosed); Kaggle licence unknown; 621 boxes on no labelled Tufts tooth. |
| Fix now | None in code; the paper keeps the one-sentence disclosure (12b). A retrained detector was refused (it orphans every Ningxia figure). |

### Stage 2 — FDI numbering (ResNet18 head v2.0 + Hungarian assignment)

| | |
|---|---|
| Evidence | DENTEX 92.8% [90.63, 94.87] (in-domain detector); Tufts test 63.5% [59.34, 67.50]; UFBA-425 44.5% [42.39, 46.62]. |
| Flaw | Every report tags the head `v1.0` while v2.0 loads (`run_inference.py:635`). Numbering is detection-bound. |
| Fix | T3(b). |

### Stage 3a — caries: lesion detector (`models/16`), retained gate (`models/09`)

| | |
|---|---|
| Evidence | DENTEX 164: FDI-set F1 0.498 vs constant 0.320, +17.80 pp [+13.48, +22.02]; lesion agreement 0.595 vs 0.630, not separated. CariesXrays is its validation split. Ningxia +9.28 pp informed adoption. |
| Flaw | Report caveat stale (`run_inference.py:258-260`); no hash pin; gate-mode tag wrong (`:599`); no false-positive rate possible (no tooth labelled healthy); 43.9% of flagged codes carious. |
| Why | A cohort that helped choose the model is not an external test. R7 finds little adaptive overfitting on large shared benchmarks; it does not cover one model chosen on one small cohort. |
| Fix | T1, T3(a), T3(b); the paper says "informed adoption", never "external validation", for this model. |

### Stage 3b — caries severity (`models/07`)

| | |
|---|---|
| Evidence | Validation only, 133 crops, macro-F1 0.77; trained on all 705 DENTEX images. |
| Flaw | Printed in the report with no test behind it; untestable (no deep-caries class in the lesion labels). |
| Fix | T3(a): `limitations.caries_severity_not_evaluated`. Stays visible (13f chair). |

### Stage 4a — abnormality flag (`models/18…/seed42_best.pth`)

| | |
|---|---|
| Evidence | Tufts test, 143 radiographs, 182 positive teeth: sensitivity 27.5% / 16.5% / 11.0% (seeds 42/43/44), pooled 18.3%; specificity 95.9 / 98.1 / 98.6%; PPV 24.8 / 29.4 / 28.2%; ROC-AUC 0.687 / 0.684 / 0.687. Validation-chosen threshold (pre-registered secondary): 29.1% / 95.0%, F1 0.252 vs 0.260 at `argmax`. Label: crop overlaps a Tufts expert abnormality mask. |
| Flaws | (1) The three runs share one pre-computed jitter set (`JITTER_SEED = 42`, `train_bone_loss_v2.py:44,73`); only initialisation, order and online augmentation vary. (2) Trained at ~22% effective prevalence (negatives undersampled to 3.5 per positive, `:145-147`, class-weighted focal loss), applied by `argmax` at 4.7%; the printed `confidence` (`src/classifiers.py:400`) is not a probability. (3) Test figures come from the training crop path on annotated boxes; the pipeline reads the image in colour and crops detector boxes. Crop geometry is the same formula (`expanded_box`, `bone_loss_heldout.py:44-48` ≡ `compute_expanded_bbox`, `src/crop_generator.py:18-39`); decode and normalisation were never compared. (4) Not a periodontal label (R12: bone level as % of root length). |
| Why | (1) R6: data sampling dominates training variance, and stochastic augmentation should not share a seed across runs — the spread is a lower bound. (2) R5: undersampling strongly overestimates minority-class probability. (3) A skew would make the test figures describe a path the product does not take. |
| Fix | W1, W2, V2 (§6). |
| Already measured, not to repeat | A threshold: no gain at ROC-AUC ≈0.69, and Amendment 1 forbids another. |

### Stage 4b — severity of flagged teeth (`models/04`)

| | |
|---|---|
| Evidence | Labels are a crop-contrast stand-in (`notebooks/bone_loss/04_bone_loss_severity.ipynb`, cell 5 output). Validation only, 52 crops. |
| Fix | T3(c) [D1]: withheld by default; `--bone-severity-grade` restores it, labelled; overlay shows `ABN` only. |

### Stages 5–6 — report, overlay, app

| | |
|---|---|
| Flaws | Tags, hashes, caveats (T1, T3); overlay colour semantics (§2 row 10). |
| Fix | T3, with F1 inside it (both change the overlay; one before/after). |

### Evaluation infrastructure

| | |
|---|---|
| Current | Radiograph-cluster percentile bootstrap (`scripts/eval/bootstrap_ci.py:66-97`), paired for differences; pre-registration; one pass per test split. |
| Assessment | **Sound.** R3: percentile bootstrap intervals cover better than asymptotic ones when many sites belong to one patient — this project's design. |
| Gap | Intervals cover test sampling only, not training variance (R6). One sentence in the methods (W2). |

### Reproducibility and serving safety

| | |
|---|---|
| Current | `requirements.txt` mostly `>=`; `torch.load(..., weights_only=False)` at `src/classifiers.py:108`, `src/fdi_head_inference.py:90`; eight checkpoints hash-pinned, not the default lesion detector or caries-severity bundle. |
| Evidence | R14: in the current docs (2.14) the default is `weights_only=True`; "never load data from an untrusted source". The installed 2.2.0 defaults to `False`. |
| Fix | T1, T5, T6 (optional; the files are the project's own). |

---

## 4. Research evidence

| # | Source | Read | Problem · method | Reported result | Limits | Applies to | Strength |
|---|---|---|---|---|---|---|---|
| R1 | Yagis E, Atnafu S, García Seco de Herrera A, et al. *Effect of data leakage in brain MRI classification using 2D CNNs.* Sci Rep 11:22544, 2021. doi:10.1038/s41598-021-01681-w | Full text | Slice- vs subject-level splits; 3 CNNs (incl. ResNet-18) on OASIS, ADNI, PPMI and a local set; nested CV | Slice-level splitting inflated test accuracy by 30 (OASIS), 29 (ADNI), 48 (PPMI), 55 (local) points; random labels ~96% slice-level vs ~50% subject-level | MRI slices, not tooth crops | Why 0.923 fell to 7.6%; V1, T2 | **Direct** |
| R2 | Abhishek K, Jain A, Hamarneh G. *Investigating the quality of DermaMNIST and Fitzpatrick17k.* Sci Data, 2025. doi:10.1038/s41597-025-04382-5 | Full text (parts) | Duplicates and cross-partition leakage; embedding similarity, then manual review | 18 duplicate pairs in HAM10000 the metadata did not record; leakage corrected by moving images | Dermoscopy | V1's method (hash, then look) | Direct (method) |
| R3 | Rutter CM. *Bootstrap estimation of diagnostic accuracy with patient-clustered data.* Acad Radiol, 2000. doi:10.1016/s1076-6332(00)80381-5 | Abstract | Simulation, bootstrap vs analytic CIs, multi-site data | Percentile bootstrap covered better than asymptotic normal; slightly better than analytic with many sites per patient | Angiography | Confirms the existing bootstrap | Direct, confirms |
| R4 | Genders TSS, Spronk S, Stijnen T, et al. *Methods for calculating sensitivity and specificity of clustered data: a tutorial.* Radiology, 2012. doi:10.1148/radiol.12120509 | Metadata only | — | Not read; no result cited | — | Citable for "teeth are clustered within radiographs" | Existence only |
| R5 | van den Goorbergh R, van Smeden M, Timmerman D, Van Calster B. *The harm of class imbalance corrections for risk prediction models.* JAMIA 29:1525, 2022. doi:10.1093/jamia/ocac093 | Full text | Undersampling, oversampling, SMOTE vs none; logistic regression; simulation (2,000 runs per scenario) and a case study | Every correction strongly overestimated minority-class probability; AUROC 0.79–0.80 throughout; shifting the threshold gave similar sensitivity/specificity | Logistic regression, not CNNs | W1 | Indirect |
| R6 | Bouthillier X, Delaunay P, Bronzi M, et al. *Accounting for variance in machine learning benchmarks.* arXiv:2103.03098, 2021 | Full text | Sources of variance across 5 tasks, 200 seeds per source (one with a ResNet18 backbone) | Data sampling the largest source; initialisation under half of it, on par with data order; randomise every source; stochastic augmentation should not share a seed across runs | Compute-heavy | W2 | Direct |
| R7 | Recht B, Roelofs R, Schmidt L, Shankar V. *Do ImageNet classifiers generalize to ImageNet?* arXiv:1902.10811, 2019 | Abstract | New test sets for CIFAR-10 and ImageNet | Drops of 3–15 and 11–14 points, attributed to harder images, not adaptivity | Large benchmark, many models | **Qualifies** the single-pass rule: it stands on small n and explicit selection, not on R7 | Indirect, partly contrary |
| R8 | Crameri F, Shephard GE, Heron PJ. *The misuse of colour in science communication.* Nat Commun 11:5444, 2020. doi:10.1038/s41467-020-19160-7 | Full text (parts) | Review with CVD simulations | Red–green maps of similar lightness unreadable to a large fraction of readers; colour misuse can highlight some data over others | Mostly continuous maps | F1, F2, F3 | Direct |
| R9 | Nuñez JR, Anderton CR, Renslow RS. *Optimizing colormaps with consideration for color vision deficiency.* PLOS ONE 13:e0199239, 2018. doi:10.1371/journal.pone.0199239 | Full text (parts) | CVD-optimised colormap (cividis) | CVD affects up to 8% of men and 0.5% of women; cividis reads nearly the same with and without red–green CVD | Sequential maps | F1; any new heatmap | Direct |
| R10 | Roelofs R, Cain N, Shlens J, Mozer MC. *Mitigating bias in calibration error estimation.* arXiv:2012.08668 | Abstract | Bias of ECE estimators | Equal-mass bins less biased than equal-width | Synthetic outputs | F5 | Direct |
| R11 | Nixon J, Dusenberry M, Jerfel G, et al. *Measuring calibration in deep learning.* arXiv:1904.01685, 2019 | Abstract | Calibration-metric choices | Adaptive binning recommended | Large benchmarks | F5 | Supporting |
| R12 | Krois J, Ekert T, Meinhold L, et al. *Deep learning for the radiographic detection of periodontal bone loss.* Sci Rep 9:8495, 2019. doi:10.1038/s41598-019-44839-3 | Full text (parts) | CNN on panoramic segments; reference = bone loss as % of root length (CEJ→crest over CEJ→apex), three examiners; 10-fold CV | Accuracy 0.81, sensitivity 0.81, specificity 0.81; six dentists 0.76 (n.s., p = 0.067) | Single centre | What a periodontal label requires; E4 | Indirect |
| R13 | Khurshid Z, Osathanon T, Shire MA, Schwendicke F, Samaranayake L. *AI in dentistry: a concise review of reporting checklists.* Int Dent J, 2026. doi:10.1016/j.identj.2025.109322 | Full text (parts) | Review of CONSORT-AI, TRIPOD-AI, CLAIM, PROBAST-AI and others | CLAIM's 2024 update (Delphi) adds image-acquisition items and "reference standard" terminology | Narrative review | C1 | Direct (reporting) |
| R14 | PyTorch 2.14 docs, `torch.load` (docs.pytorch.org); installed 2.2.0 docstring | Read | — | Default `weights_only=True`; restricts unpickling to tensors, primitives, dicts and allow-listed types; "never load data from an untrusted source". 2.2.0 defaults to `False` | — | T6 | Official |

Searched for and not found in the index: Schwendicke et al.'s 2021 *J Dent* checklist for dental AI
research (R13 reviews the checklists instead). Nothing above is a measurement of this project.

---

## 5. Council feedback against the evidence

| Council recommendation (source) | Current implementation | Evidence | Assessment | Final decision |
|---|---|---|---|---|
| Freeze: no new model, default, or Ningxia pass (12a, 12b, 13f) | Holding | R7 qualifies; R1, R6 support caution at small n | Small test sets, explicit selection | **Accept** |
| Second lesion-detector seed — not now (12a, 12b) | Not run | R6 | Needed for a journal; not cleanly scorable now | **Accept**; E5 later |
| No lesion-detector threshold or calibration study (12b) | None | R5 | No clean data to test on | **Accept** |
| Reject option after submission (11d, 12a) | Parked | — | — | **Accept** |
| No retrained detector (11d, 12b) | — | — | — | **Accept** |
| Cut the bone-loss branch (12a) | Overruled by the decision owner, 12 Oct | R12 | Stays, as an abnormality flag | **Reject** (decision owner) |
| Stage 3b: present, not evaluated (12b, 13f) | Grade shown | — | — | **Accept**; T3 |
| Hide the Stage-4b grade by default (13f chair) | Grade shown | Label is image contrast | A shown grade is a mislabel | **Accept** [D1] |
| No first test of 4b; no 4b retrain (13f) | — | — | A test would score contrast | **Accept**; E1 investigates |
| 4a: report three runs (13f) | Not yet in the manuscript | R6 | Spread is a lower bound | **Modify**: W2 |
| Pin the two missing hashes; stamp all; don't enforce at load (13f) | 8 pinned; two defaults not | R14 | — | **Accept** (T1, T3); T6 optional |
| Lock file; split invariant (13f) | Absent | R1, R2 | Exact twins already found | **Modify**: T2 also reads V1 |
| Loud failures in eval scripts after submission (13f) | Silent `continue` | — | No saved figure moved | **Accept** |
| No BRAR for this paper (13f) | — | R12 | Journal work | **Accept**; E4 |
| Stop date 20 Oct (13f) | — | — | — | **Accept** |
| Keep one sentence on Tufts mAP 0.587 (12b) | In draft | — | — | **Accept** |
| Never train on Ningxia (12c) | In force | — | — | **Accept** |
| Figures and colours | Never reviewed by a council | R8–R11 | New | **New**: F1–F7 |

---

## 6. The implementation plan

### 6.1 Ground rules

- Karpathy skill before the first edit; `python-testing` for tests. **No new dependency.**
- **Nothing is scored.** No Ningxia, no Tufts test pass, no `bone_loss_v2_eval.py score`, no
  `outputs/stage1_switch/run_matrix.sh`. V1 reads radiographs, never labels; V2 reads two
  *train-split* radiographs.
- **Baseline first** (T0); after every task the same three commands: `pytest tests`,
  `scripts/eval/verify_invariants.py`, `scripts/verify_paper_numbers.py`.
- **Line endings.** CRLF: `scripts/run_inference.py`, `scripts/eval/verify_invariants.py`,
  `scripts/eval/validate_fdi_assignment_tufts.py`, `scripts/eval/README.md`, `README.md`,
  `transfer.md`, `docs/results/*`, `docs/paper/SUBMISSION_TODO.md`, `docs/EXTERNAL_DRIVE.md`. Patch
  through bytes (decode, normalise, anchored replace asserted once, re-encode, assert no lone LF).
  Everything else LF. `git diff --stat` must show no whole-file change.
- **The user commits.** One commit per task, prefixes `fix:` / `feat:` / `test:` / `docs:`, explicit
  paths only.
- **Rollback** for every task is `git restore` / `git checkout` of the files that task names,
  before commit; `git revert` of its commit after. Not written as runnable commands here.
- **Stop and ask** whenever a step's outcome contradicts what this plan expects (V1 finds a pair; V2
  fails; a checkpoint refuses `weights_only=True`; a smoke run differs outside the expected keys).

### 6.2 Decisions to take before the first edit

| | Question | Default | What changes with the other answer |
|---|---|---|---|
| D1 | Stage-4b grade: withhold by default, or keep it with a label? | Withhold; `--bone-severity-grade` brings it back | "Label only": T3(c) drops the `None` branch and the CLI flag; texts and per-tooth flag stay |
| D2 | Stage-4 manuscript text and Fig. 5: now, or with the six-page cut? | With the cut | "Now": Phase C + F2 on day 2, +3 to 4 h |
| D3 | README banner tiles | 89.3% tooth recall (Tufts test) · 63.5% numbering end to end (Tufts test) · 0.498 caries F1 vs constant 0.320 · 4 external hospitals · 95.3 M parameters | Any other figures from `model_metrics.md` |
| D5 | Stale README infographics | `pipeline.svg`: correct its text in place. `baselines`, `error-propagation`, `domain-shift`, `abstention`: unlink with a one-line note; files stay in `docs/assets/` | Redraw all four: +3 h, not recommended before the cut |
| D6 | Overlay colours | Not-assessable grey 1 px; finding orange 2 px; numbering doubt blue 1 px with `?`; clean blue 2 px | "Keep red": F1 shrinks to the caption only |
| D4 | T6, T7 if time | Yes, after the must tasks | Skip both |

### 6.3 Order, tier, size

| Day | # | Task | Tier | Depends on | Est. |
|---|---|---|---|---|---|
| 1 | T0 | Commit pending documents; D1–D6; baseline | — | — | 0.3 h |
| 1 | T1 | Hash pins for the two unpinned defaults | must | T0 | 0.5 h |
| 1 | V1 | Near-duplicate scan of the retraining split | must | T0 | 1 h |
| 1 | T2 | Split invariant, reading V1's output | must | V1 | 0.5 h |
| 1 | V2 | Stage-4a crop-parity test | should | T0 | 0.75 h |
| 1 | T3 | Report schema 1.5, with W1 and F1 inside | must | D1, D6, T1 | 4.25 h |
| 2 | T4 + F7 | Stale text and README graphics | must | D3, D5, T3 | 3 h |
| 2 | T5 | Lock file | should | — | 0.75 h |
| 2 | F3 | Fig. 1: two methods, two encodings | should | — | 0.75 h |
| 2 | W2 | Three-run paragraph draft | should | — | 0.25 h |
| 2 | T6, T7 | Safe loading; input guards | optional | D4 | 1.5 h |
| 2 | T8 | Close-out | must | all above | 1.5 h |
| cut | F2 + Phase C | Fig. 5 redraw and the Stage-4 manuscript text | must, timing [D2] | T3 | 3–4 h |
| cut | F4, F5, F6, C1 | Only for figures that survive the six-page cut | P2/P3 | the cut | — |

Day 1 ≈ 7.3 h, day 2 ≈ 6.25 h without optional tasks. **T3 is never left half done**; if day 1
runs short, V2 moves to day 2, not T3. Stop date for code: 20 Oct.

### 6.4 Task cards

#### T0 — Start of day (0.3 h)

1. The user commits this file and the `transfer.md` pointer.
2. D1–D6 answered; answers written into §6.2 of this file.
3. Baseline into the scratchpad: the three commands (expect 184 / 11 / 191); one default report and
   overlay of `data/dentex/enumeration_v1/_crop_sanity.png` (the image used for the 13 Oct smoke
   test) as `before.json`, `before.jpg`.

#### T1 — Hash pins (0.5 h, must)

- `scripts/eval/verify_invariants.py`, `hash_from_summary` (59–82): attribute a hash to the
  **basename** of the last weight file mentioned, so `weights/best.pt` matches `best.pt`. One line.
- `inv_weight_hashes` (85–143): add `models/16_lever_b_pooled/lever_b_pooled_yolo11l-2/weights/best.pt`
  against `models/16_lever_b_pooled/run_summary.txt`, and
  `models/07_caries_cascade/phase2_final_bundle.pth` against `models/07_caries_cascade/run_summary.txt`.
- `tests/test_verify_invariants.py`: (a) a path-prefixed filename resolves; (b) the real `models/16`
  summary resolves `best.pt` to `029018db…`, not `last.pt`'s `f774bb1e…`.
- **Check:** the invariant lists ten files; the `models/03` best-versus-final test still passes;
  186 tests.

#### V1 — Near-duplicate scan of the retraining split (1 h, must)

- New `scripts/eval/tufts_split_near_duplicates.py` (~40 lines, LF). Reuses `SRC`, `dhash`,
  `NEAR_DUP_BITS` (= 10) from `scripts/eval/bone_loss_heldout.py`, the same import pattern as
  `train_bone_loss_v2.py:30-34`.
  - Reads `outputs/eda_tufts/split_v1.csv`; hashes every radiograph in
    `_repo_archive/datasets_workspace/Radiographs/` (1,000 files, < 1 min).
  - For every pair in **different** splits: Hamming distance (one row at a time, not a 1000×1000×256
    array).
  - Writes `outputs/eda_tufts/near_duplicates.json`: method, threshold, every cross-split pair at
    ≤ 20 bits with both splits, the nearest-neighbour distribution over all pairs (min, 5th
    percentile, median) as calibration, and `known_twins` (590/591, 1007/1008; their dropped member
    is in `DROP`, `train_bone_loss_v2.py:39`).
  - Exits non-zero if a radiograph cannot be read. Reads no label, no mask.
- **Review:** the closest ten cross-split pairs opened side by side locally (never sent to any cloud
  tool).
- **Expected:** only the two known twins at ≤ 10 bits; DENTEX's comparable figure was 42 bits
  nearest.
- **If any other pair is ≤ 10 bits, or the review finds a same-patient pair: stop.** Options for the
  user: disclose the count; or a pre-registered exclusion re-analysis of the saved
  `test_rows.json` (arithmetic on saved rows, no model run). Nothing is re-trained.
- **Logged** in T8 (RESULTS_LOG, PAPER_MATERIAL §8).

#### T2 — Split invariant (0.5 h, must)

- `scripts/eval/verify_invariants.py`: a new check, registered like the others. From tracked files:
  - `split_v1.csv`: every filename once; 700 / 150 / 150.
  - `outputs/bone_loss_eval/v2_retrain/test_rows.json`: 143 distinct radiographs, all `test`.
  - `data/tufts/severity_dataset/metadata/`: the severity model's radiographs meet the test split in
    exactly 149 and 192 (training) and 249 (validation) — a recorded exception, asserted so that a
    change is noticed.
  - `near_duplicates.json` (V1): no cross-split pair at ≤ `NEAR_DUP_BITS` except `known_twins`.
  - Any part whose file is absent: skipped with a message.
- **Check:** twelve invariant lines, all OK.

#### V2 — Stage-4a crop-parity test (0.75 h, should)

- New `tests/test_crop_parity.py` (LF). For the first two `train` radiographs of `split_v1.csv` that
  have tooth boxes:
  - training path: `clean_crops(stem, records[stem])` → `to_batch` arithmetic
    (`train_bone_loss_v2.py:100-104`);
  - serving path: the same boxes — `[y1, x1, y2, x2]` reordered to `x1, y1, x2, y2`, same
    `MIN_DIM` filter — through `crop_batch(cv2.imread(path), boxes, BONE_LOSS_EXPAND, "cpu")`.
  - Assert the two tensors agree to within one grey level (≈ 0.02 after normalisation).
  - `pytest.skip` when `_repo_archive/datasets_workspace/Radiographs` is absent (fresh clones).
- **Expected:** pass (same geometry; a greyscale JPEG decodes to equal channels).
- **If it fails:** stop; record the measured difference; the paper then says the test figures were
  computed on the training crop path. No code fix without a decision — the model is frozen.

#### T3 — Report schema 1.5 (4.25 h, must) — includes W1 and F1

All in `scripts/run_inference.py` unless stated. The `1.5 (14 Oct 2026)` paragraph goes into the
schema history above `SCHEMA_VERSION` (line 100).

**a. Texts.**

| Text | Now | Change to |
|---|---|---|
| `CARIES_METHOD_CAVEATS["lesion-detector"]` (254–271) | "beats … on 2 of 3 external cohorts (CariesXrays, Ningxia); on DENTEX a tie with both" | Adoption evidence was measured under the previous tooth detector. CariesXrays 1,200 is this detector's validation split. Ningxia is external and also informed adoption: +9.28 pp over the constant, pooled [+4.72, +13.73]. On DENTEX with the default tooth detector: F1 0.498 against the constant's 0.320; lesion agreement not separated from the constant (−3.55 pp [−10.11, +2.64]) and 20.67 pp below the gate, which flags 2.4 times the teeth. 43.9% of the codes it flags are carious; no false-positive rate can be given |
| Default profile, `label_and_validation` | "143 Tufts test radiographs that no model in this pipeline trained on" | "that this model did not train on (the severity head trained on two of them)". Add: the interval covers radiograph sampling, not the training run; pooled over three runs 18.3% (100 of 546); scored on crops at annotated tooth boxes, not this pipeline's detections. Keep "abnormality" and "not as a periodontal" (the invariant looks for them) |
| **W1**, same profile | — | One sentence: "`confidence` is the softmax of a model trained with negatives undersampled to 3.5 per positive and a class-weighted focal loss, applied at about 5% prevalence; read it as a ranking score, not a probability." |
| Default profile, `transfer` | A sentence on the severity grade "validated on 52 crops" | Removed; the new key below carries it |
| Default profile, `validation_split` | "severity: image-level, 32 training / 9 validation radiographs (unchanged)" | Add: its labels were a crop-contrast stand-in, not mask overlap |
| Previous checkpoint's profile | — | **Unchanged, verbatim** |
| New `limitations.bone_severity_not_evaluated` | — | The Stage-4 severity head was trained on the standard deviation of crop grey levels, not on the expert mask; its classes are low, middle and high contrast; it has no test; withheld by default |
| New `limitations.caries_severity_not_evaluated` | — | The `caries` / `deep_caries` distinction comes from a head validated on 133 crops with no held-out test |
| Module docstring, Stage-4 paragraph | One run's 27.5% | Three runs; the severity head as above |

**b. Hashes and tags.** One table keyed by sha256 for the checkpoints without a profile: both
numbering heads, the gate, the caries-severity bundle, the lesion detector, the Stage-4 severity
model — each hash copied from its run summary, not from memory. In `run_pipeline`'s `meta`
(629–650):

- `fdi_head` gains `sha256`; its `tag` comes from the table (fixes the `v1.0` tag at 635).
- `caries` gains `sha256` and `sha256_severity`; in gate mode also `tag_gate` (fixes 599). The
  existing `tag` key stays.
- `bone_loss` gains `sha256_severity`.
- A checkpoint with no entry gets `unregistered-<8 hex>`, as the detector does today.

**c. The Stage-4b grade [D1].**

- `src/classifiers.py`, `run_bone_loss` (376–412): `severity=None` skips the severity pass; a
  flagged tooth keeps `severity: None` and gains `severity_withheld_contrast_proxy`. With a model:
  as today plus `severity_is_contrast_band_not_evaluated`.
- `run_pipeline(..., bone_severity_grade=False)`; CLI `--bone-severity-grade`;
  `models.bone_loss.severity_reported`.
- All seven checkpoints still load, so parameter totals stand. Seconds-per-image was measured with
  the grade computed; not re-measured, and T8's log entry says so.
- `scripts/eval/bone_loss_v2_eval.py`, `dentex` command: pass `bone_severity_grade=True` so a
  re-run would reproduce its saved counts. One line; not run.

**d. Overlay — the D1 label and F1 colours in one change.** `draw_overlay` (476–498):

| Tooth state | Colour (BGR) | Line | Label |
|---|---|---|---|
| Not assessable | grey (160,160,160) | 1 px | as today |
| Finding: caries ≠ `no_caries`, or the abnormality flag | orange (0,165,255) | 2 px | as today; `ABN` when the grade is withheld, `ABN-Sev` etc. only when asked |
| Numbering doubt only (`fdi_flags`, no finding) | blue (200,120,0) | 1 px | FDI code followed by `?` |
| Assessable, nothing found | blue (200,120,0) | 2 px | as today |

Docstring line 477 updated to match.

**e. App.** `app.py:124` caption: "Orange = finding (caries or abnormality flag) · Blue = no
finding · thin blue with ? = numbering uncertain · Grey = not assessable". Two more Limitations lines,
one per new key (150–159).

**f. Docstrings.** `src/classifiers.py` lines 18, 37, 378–379 ("degrees of bone loss").

**g. Invariant.** Extend `inv_stage4_report_wording` (317–357): schema ≥ 1.5; the lesion-detector
caveat contains "validation split" and no longer "2 of 3 external"; the severity text contains
"contrast"; `app.py` renders both new keys; a default report carries `severity_reported: false`.

**h. Tests.**

- `tests/test_classifiers.py`: `run_bone_loss` with two stub models of fixed logits — withheld branch
  and graded branch.
- New `tests/test_report.py`: (1) `build_report` on empty stage outputs carries both new limitation
  keys and the schema string; (2) `draw_overlay` on a black 200×200 image with four fake teeth, one
  per state, written as PNG to `tmp_path`, asserts each box's top-edge pixel colour.

**i. Smoke — one fixed image, no cohort.**

| Run | Must hold |
|---|---|
| Default | Per-tooth output identical to `before.json` except `bone_loss.severity`, `severity_confidence`, `flags` |
| `--bone-severity-grade` | Identical to `before.json` except the added flag |
| `--bone-loss models/03…/bone_loss_resnet18_best.pth` | The two Stage-4 limitation texts byte-identical to a 1.4 report of that checkpoint |
| `--caries-method gate` | Runs; `tag_gate` present |
| Grep callers of `run_pipeline(` and `run_bone_loss(` under `scripts/`, `src/`, `app.py` | Every caller still gets what it reads |

`after.jpg` beside `before.jpg` for the user. **CVD check:** the four box colours through a numpy
deuteranopia/protanopia simulation (Machado et al. 2009 matrices — a method not verified this session;
about ten lines in the scratchpad, not committed); orange must stay distinguishable from blue and grey.

**Check:** about 190 tests; twelve invariants; 191 paper numbers; schema `opg-report/1.5`.

#### T4 + F7 — Stale text and README graphics (3 h, must)

| File | Change |
|---|---|
| `docs/assets/hero.svg` (tiles, lines 76–100) and `README.md:3` alt text | Tiles per D3. Subtitle: "YOLOv11l" (no "-seg"); "caries detection and an abnormality flag" instead of "caries and periodontal bone loss" |
| `README.md:18` tagline | "periodontal bone-loss screening" → wording that names an abnormality flag |
| `docs/assets/pipeline.svg` + `README.md:144` alt | [D5] text in place. Stage 1: "YOLOv11l · multi-corpus · boxes", recall 89.3% Tufts test, box mAP@0.5 0.587. Stage 2: 63.5% end to end Tufts test; 92.8% DENTEX (in-domain detector). Caries path: lesion detector (default), per-crop gate retained; F1 0.498 vs constant 0.320 (DENTEX 164); depth head "133 val crops, no test". Stage-4 path renamed "abnormality flag": test sensitivity 11.0 / 16.5 / 27.5% over three runs, specificity 95.9–98.6%; severity head "contrast band, withheld". Every number checked against `docs/results/model_metrics.md` |
| `README.md:208, 237, 300, 329` | [D5] each `<img>` replaced by one line: figure retired 14 Oct 2026, it showed an earlier configuration; current numbers in `docs/results/model_metrics.md`. SVG files stay |
| `README.md` badges, lines 8–12 | 184 tests (or the count after T3); PyTorch 2.2 with a link to the lock file; "YOLOv11l" |
| `README.md`, "127 numbers", four places | 191, after checking each refers to the number checker |
| `README.md` Prerequisites (~line 591) | Point to the lock file |
| `PROJECT_OVERVIEW.html` | Dated banner: a 6 Sep snapshot; detector, Stage-4a model, 0.923 and the severity head have changed; `transfer.md` is current. No rewrite |
| `Dockerfile` lines 1–11 | Remove the two mounts; say the image was last built 7 Sep |
| `tests/README.md:1` | Real test count |
| `transfer.md` §8 | Python and package versions from the lock file |
| `models/18_bone_loss_radiograph_split/run_summary.txt` | "exist only on the macOS clone" no longer true of seed 42 |
| `docs/README.md` line 4 | "periodontal bone loss per tooth" → abnormality flag |

**Check:** grep the tracked tree for `0.9233`, `0.923`, `58.3%`, `0.810`, `0.294`, `YOLOv11l-seg`,
`periodontal`; every remaining hit is history (the log, a superseded section, the previous
checkpoint's profile), an explicit disclaimer, or the manuscript (Phase C); the T8 session file
lists them. README renders (no broken image).

#### T5 — Lock file (0.75 h, should)

- `requirements-lock.txt` at the root: the installed version of every package named in
  `requirements.txt`, generated with `importlib.metadata.version`, not typed; a package not
  installed is listed as such. Header: Python version, platform, date, "produced every figure dated
  11–13 Oct 2026".
- As a comment: the other machine's stack (`transfer.md` §8), and that one row differed between the
  two (0.294 vs 0.300).
- `requirements.txt` and the Dockerfile unchanged (the image cannot be built here).

#### F3 — Fig. 1, two methods two encodings (0.75 h, should)

- `scripts/figures/make_baseline_figure.py`: add `C_GATE` (a lighter tint of navy, with dark value
  labels on it); the gate's bars in (a), (b) and (c) use it; legend and labels say "default: lesion
  detector" and "retained: per-crop gate".
- One order in every panel: lesion detector, gate, constant, then the extra arms. (b)'s `b_rows`
  reordered to match (a).
- Panel (c) title names the gate.
- **Check:** an assert that the method order of (a) and (b) is identical; re-render; every printed
  value unchanged (data read from the same JSON); grayscale render tells the methods apart; paper
  numbers 191.

#### W2 — The three-run paragraph (0.25 h, should)

- `docs/paper/SUBMISSION_TODO.md` §1a row p (CRLF): add to the draft paragraph that the three runs
  share one pre-computed jitter set, so their spread understates training variance, and that every
  interval covers radiograph sampling only. Goes into `main.tex` with Phase C.

#### F2 + Phase C — Fig. 5 and the Stage-4 manuscript text [D2] (3–4 h)

- `scripts/figures/make_boneloss_paper_figure.py` rewritten to read
  `outputs/bone_loss_eval/v2_retrain/test_summary.json` only:
  - panel (a) sensitivity, panel (b) specificity, each with its radiograph-cluster interval
    (`seed_4x.all.*.ci95`); the three seeds in one neutral ink, told apart by position and label;
    the previous model (`shipped.unseen_by_shipped`, 125 radiographs it had not seen, 3.4%) in grey,
    its different denominator stated in the tick label;
  - no 0.923, no DENTEX bar, no Ningxia bar (those are the previous model's; the DENTEX firing rate
    stays a sentence in the text);
  - asserts 50/182, 30/182, 20/182 from the confusion counts before drawing.
- The old PNGs are relocated, not deleted: `paper/fig_boneloss.png` and
  `docs/results/figures/paper/05b_bone_loss_domain_shift_paper.png` to `_repo_archive/` with a
  manifest row, unless git history is judged enough (decide in T8).
- `paper/main.tex` 105, 384–388, 412–414, 1222, 1233, 1248, 1545 and the `fig:boneloss` caption,
  from `SUBMISSION_TODO.md` row p with W2's sentence; `scripts/verify_paper_numbers.py` claims
  changed in the same commit; tectonic build; page count.

#### T6 — Safe loading (0.5 h, optional)

- `src/classifiers.py:108`, `src/fdi_head_inference.py:90`: `weights_only=True`.
- **Check:** `load_models()` loads every checkpoint; the class-order invariant passes; smoke report
  identical. A checkpoint that refuses: revert that file, record which (the 13f seat that predicted
  success was not verified).

#### T7 — Input guards (1 h, optional)

| File | Guard | Test |
|---|---|---|
| `scripts/eval/validate_fdi_assignment_tufts.py`, `load_ufba_gt` | Class id outside 0–31, or a line too short, raises | Two in `tests/test_ufba_gt_loader.py` |
| Same file, CLI | `--aspect` without `--ufba` is an error | — |
| `scripts/eval/bone_loss_v2_eval.py` 64, 68 | `zip(..., strict=True)` | — |
| `scripts/tufts/train_bone_loss_v2.py:8` | Docstring says no test radiograph is read; `check()` reads labels of a few — correct the sentence | — |

`scripts/eval/lesion_localization.py` stays as is (after submission, 13f). None of these scripts is
re-run.

#### T8 — Close-out (1.5 h, must)

- `docs/results/RESULTS_LOG.md`: one entry, 2026-10-14 — V1's result (counts and threshold), V2's
  result, D1–D6 as decided, schema 1.5, two pins, the split invariant, the overlay colours, the six
  13g defects, F3; the seconds-per-image note.
- `docs/results/model_metrics.md`: Stages 5–6 (schema, invariants, tests).
- `docs/results/PAPER_MATERIAL.md` §8.38: V1, V2, W1, W2 as limitations or confirmations.
- `transfer.md` §1–§4, §8; `scripts/eval/README.md` (new script, new invariant); README stage table.
- A new session file `docs/session-memory/2026-10-14b-…` for the implementation; this file is not
  edited after implementation starts.
- Final: the three commands; `git status`; hand over for commit. Tell the repo owner the Docker
  image is four default changes behind.

### 6.5 What the plan does not do, and why

| Flaw | Why it is not fixed |
|---|---|
| Stage 1: box mAP below the control; 621 boxes on no tooth; 66.6% recall unseen | Needs a retrained detector: refused, it orphans every Ningxia figure |
| Stage 1: Kaggle licence | A person has to ask its authors |
| Stage 2: 63.5% Tufts, 44.5% unseen | Two registered attempts were null; a reject option is parked |
| Stage 3a: no untouched external cohort; no false-positive rate | No such cohort on hand; no tooth labelled healthy in the 164 images |
| Stage 3b: no test | Trained on all 705 DENTEX images with its labels |
| Stage 4a: 11–27.5% sensitivity | The test split is spent; the threshold lever was measured without gain; Ningxia is locked |
| Stage 4b: wrong labels | Retraining is a fourth default change; withheld instead (E1 for the journal) |
| One training run per model | A second seed cannot be scored anywhere clean |
| Figs. 2, 3, 4 | Wait for the six-page cut (F4–F6) |

None of these tasks raises a metric. They remove every sentence the repository can falsify.

---

## 7. Experiment matrix — for the journal version; none run now

Every row needs data the project has not looked at, or a pre-registered exception the decision owner
grants. Expected effects are hypotheses.

| ID | Hypothesis | Single change | Baseline | Split · seed | Metric | Budget | Success criterion | Failure modes |
|---|---|---|---|---|---|---|---|---|
| E1 | A 4b head trained on true mask-overlap classes predicts overlap class above chance | Labels: overlap ratio from Tufts masks instead of contrast | Majority class; `models/04` | Tufts train/val by radiograph, test radiographs excluded · 3 seeds, jitter seeded per run | Macro-F1 or weighted kappa, radiograph-cluster CI | CPU/MPS < 1 h per seed | Paired lower bound > 0 vs majority | 182 test positives (55/63/64) give wide intervals; overlap class is not clinical severity; the only test is the spent Tufts split |
| ~~E2~~ | ~~A validation-chosen threshold raises 4a sensitivity~~ | — | — | — | — | — | **Closed: measured 13 Oct as a pre-registered secondary — 29.1% / 95.0%, F1 0.252 vs 0.260. No gain** | — |
| E3 | 4a's training variance is larger than three shared-jitter runs show | Jitter seed = run seed | The three runs | Val only · 3 new seeds | Spread of val macro-F1 | 3 training runs | Estimation only | Measures variance, not improvement |
| E4 | A periodontal label (bone level as % of root length, R12) is learnable from BRAR | New label and dataset | Constant; geometry-free baseline | BRAR, patient-level split | Sensitivity/specificity vs reference | Days; licence check | CI lower bound above baseline | BRAR grades may be patient-level only (unverified) |
| E5 | The lesion detector's F1 is stable across training seeds | Seed | `models/16` | DENTEX 164 and CariesXrays only (12a) | FDI-set F1 | GPU; pre-registration and the user's go | Estimation only | A second checkpoint invites a "which ships" fork |

Stopping rule for all: pre-register, run once, stop if a clean evaluation set does not exist.

---

## 8. Validation checklist and "done"

Per task: the three commands; the task card's own check; `git diff --stat` without whole-file
line-ending changes. Per figure: every plotted number read from a saved artefact and asserted;
grayscale render readable; caption numbers match. Never: a Ningxia pass, a Tufts test pass, a
`score` command.

**Done means:** about 190 tests pass; twelve invariants hold; 191 paper numbers match (or the claims
changed in the same commit); the four smoke runs hold; V1's JSON is reviewed and its result logged;
V2 passes or its difference is recorded; the log, the scoreboard and `transfer.md` say what ships.

## 9. Open questions

D1–D6 in §6.2 — the only blocking ones. Not blocking: whether the mentor accepts Stage 4 described
this plainly (she has not yet been told of the detector switch or the Stage-4a change); the Kaggle
licence; the pdfLaTeX build on the other machine.

## Decisions made

- **No metric is promised.** Recalibration and more seeds need unseen data; the Stage-4a threshold
  was already measured without gain. Promising a gain would repeat the 0.923 fault.
- **The near-duplicate scan and the crop-parity test come before any text.** If either finds a
  fault, sentences written first would be rewritten.
- **Existing code is reused** — `dhash` and `NEAR_DUP_BITS` for V1, the training crop function for
  V2 — instead of a new dependency.
- **F1 rides inside T3**: both change the overlay, so one before/after and one schema bump cover
  them.
- **The four stale infographics are unlinked, not redrawn or deleted** (D5 default): redrawing
  figures the six-page cut may drop is wasted work; the files stay, per the no-delete rule.
- **Figures that may not survive the cut wait** (F4–F6).
- **Recht et al. is cited as qualifying, not supporting, the single-pass rule.**
- **Three statements of this file's first version were wrong and are corrected above** (the
  near-duplicate precedent, the already-measured threshold, the crop geometry), found by reading the
  code each task touches.
