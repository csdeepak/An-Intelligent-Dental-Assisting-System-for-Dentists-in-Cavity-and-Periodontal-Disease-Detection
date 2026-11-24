# Review — Reviewer A (medical imaging / computer vision)

Manuscript: "Reading the Radiograph or the Prior? A Tooth-Level Panoramic Analysis System Evaluated Against Image-Blind Baselines and External Cohorts" (`research_paper/paper_clean.md`, figures in `research_paper/figures/`).

Scope of verification: the manuscript and figures, checked against `docs/results/model_metrics.md`, `docs/results/RESULTS_LOG.md`, `docs/results/PAPER_MATERIAL.md`, `outputs/**`, `models/16_lever_b_pooled/run_summary.txt` and `scripts/dentex/build_dentex_caries_boxes.py`. I did not read any other file under `research_paper/`.

---

## Summary of the submission

The authors build a six-stage panoramic-radiograph pipeline: a YOLOv11l tooth detector, a ResNet18 FDI numbering head with Hungarian assignment, a caries stage (by default a whole-image YOLOv11l lesion detector, with a ResNet18 crop classifier kept as a variant), a caries severity head, an "abnormality" flag, and a JSON/overlay report. The central argument is that tooth-level caries scores (FDI-set F1 and lesion agreement) mix image evidence with a positional prior. They derive the F1-optimal image-blind constant: the codes whose prevalence exceeds F1*/2, which here are the eight first and second molars, scoring F1 0.320 on 164 DENTEX images. They compare the pipeline, two Qwen2.5-VL models and this constant on DENTEX (development), CariesXrays (the lesion detector's validation split) and four Ningxia test sets (external). The crop classifier beats the constant on development data but is level with it on Ningxia. The lesion detector leads it on Ningxia (+9.28 pp pooled, three of four sites), but the random-effects interval includes zero. The abnormality branch is reported as a negative result.

## Major strengths

1. **An image-blind baseline scored beside every system, with paired cluster-bootstrap intervals over images.** Few dental-AI papers do this, and the constant's F1 (0.320, oracle 0.330) is a real floor that several systems, both VLMs among them, fail to clear.
2. **Per-site external reporting with heterogeneity made explicit.** DL, HKSJ, a Q-profile interval for tau and a prediction interval are all reported, and the prediction interval [-36.08, +55.29] is stated rather than hidden.
3. **Unusually candid disclosure of departures from protocol.** The detector was adopted against its pre-registered guards, Ningxia informed the adoption, CariesXrays is a validation split, and the abnormality flag's crop-level split inflated it from 3.4% to a reported 0.923 macro-F1. These are all in the text.
4. **Numbers are traceable.** Every number I checked against saved artefacts matched (table at the end), including bootstrap interval endpoints, resample counts and per-type counts.
5. **Shuffled-confidence control for selective prediction, and a matched-volume constant for F1.** Both are the right kind of control, even if each has a flaw (W6, W2).
6. **Content-free controls for the VLMs** (blank and noise images) show that the VLM outputs are largely prior-driven.

## Major weaknesses

**W1. The image-blind constant used for FDI-set F1 is weaker than a fair image-blind baseline, and the RQ1 conclusion may reverse under a fair one.** Equation (2) and Table 5 score a constant that names all eight molar codes on every image, absent teeth included (1,312 named codes = 8 x 164). The pipeline, by contrast, names only teeth its front end detected. The paper already builds a presence-aware constant for lesion agreement ("the eight molar boxes our front end finds": 988 flagged teeth on DENTEX, 302 of 479 lesions matched; `model_metrics.md`, arm3c row). Using those counts as an approximation, a presence-aware constant on FDI-set F1 would score roughly 2 x ~295 / (988 + 477) ≈ 0.40. That is above the crop-classifier pipeline's 0.362, and it would cut the lesion detector's lead from +17.80 to roughly +10 pp. This is my estimate from saved counts, not a computed result, but it is large enough that the "+4.27 points [+1.58, +7.05]" lead in the abstract and Table 5 may not survive. A constant that is allowed to see which teeth are present is still image-blind about caries, and it is the like-for-like comparator.

**W2. The matched-volume F1 comparison is structurally biased against the constant.** For the lesion detector (3.8 codes per image), the matched constant is a mixture of S_3 and S_4, whose F1 (0.274) is capped by recall, because F1 is not volume-neutral. The +22.35 "matched" lead is therefore larger than the raw +17.80 for a mechanical reason, not an informative one. The informative quantity at matched volume is precision: 0.439 against 0.242 (`outputs/review_round1/constant_stability_and_curve.json` → `matched_volume`). Report matched-volume precision, or a precision–recall operating curve of the constant against each system's operating point, instead of matched F1.

**W3. The "floor moves with the cohort" claim (Section III-C, Table 8 row 2) is confounded with front-end performance per site.** The constant's lesion agreement is not "the cohort's prior mass" alone. It also depends on whether the front end detects and codes the molars at each site. The artefacts show this directly. Switching only the tooth detector raised the constant's Ningxia agreement from 0.399 to 0.591 (+19.25 pp [+15.69, +22.81]). At test1 it rose from 0.449 to 0.709 (+25.95 pp) (`outputs/stage1_switch/stage1_switch_results.log`, Row F). So the 0.494–0.709 spread across sites mixes caries prior with detector recall and numbering per site. The paper's "as placed by our front end" acknowledges this only obliquely. The Tufts placement check (92.0% precision, 81.7% reach) is on a training corpus and says nothing about Ningxia. The verdict "holds" in Table 8 is not supported as worded. At minimum, report per-site front-end recall, or the constant's agreement computed from ground-truth tooth boxes, so that the prior is separated from the detector.

**W4. Section III-E's argument that localisation "resists the shortcut" does not apply on DENTEX, where the supporting evidence comes from.** On DENTEX, the lesion detector's training boxes are whole-tooth caries boxes ("whole-tooth granularity, a domain adapter, not a second lesion-box source": `models/16_lever_b_pooled/run_summary.txt`, `PAPER_MATERIAL.md` l.2397). A YOLO model run on the whole OPG has a receptive field that covers arch context, and padding gives it absolute position. It can learn "molar-region tooth → caries" as easily as a crop classifier can, and arguably more easily. Two facts follow:
- The detector's flags are *more* molar-concentrated than the crop classifier's: 71.6% against 66.6% (`model_metrics.md`, "What the caries stage flags").
- The per-tooth-type precision evidence is on DENTEX only, where the model was trained on tooth boxes: molars 46.3% (207/447) against 28.4% (291/1,023). It is also compared at very different flag volumes (447 against 1,023 molars). Any ranker with signal gains precision at lower volume.

The "fewer flags" prediction is not discriminating either, because a higher threshold produces it with no change in perception. The theory needs a test the prior cannot pass, such as precision at matched per-type volume, or a position-randomised or position-masked input ablation. Until then the RQ2 conclusion rests on the Ningxia lead alone.

**W5. The positional-shortcut test (Section III-D, Table 2) does not isolate position.** A crop classifier gets no position input; it infers tooth type from morphology. A healthy-tooth score that rises from incisors to molars is equally predicted by molar-specific image confounders: overlapping contacts, restorations, cervical burnout and occlusal fissures mimic radiolucency. The table cannot tell "prior over position" from "molars look more carious". The more direct quantity is in the artefact but not in the paper: pooled AUC 0.855 [0.801, 0.900] against within-type AUC 0.745 [0.660, 0.842] (`outputs/caries_position_bias/caries_position_bias_test.json`). Per-type AUCs rest on 8 (incisor) and 5 (canine) positives and have no intervals. Report them with intervals or drop them. A cleaner test is a classifier with explicit position input against one without, or within-type calibration curves.

**W6. Selective prediction for the crop classifier uses accuracy on an imbalanced task where the classifier is below the majority baseline.** At full coverage the classifier's accuracy is 0.797 (TP 94, FP 142, FN 33, TN 594). Always answering "healthy" gives 736/863 = 0.853. Declining the least-confident 25% removes mid-confidence crops and leaves mostly near-zero-score incisors and canines, which are almost all negative. The 0.797 → 0.940 gain therefore partly reflects enrichment for easy negatives. The shuffle control does not address this, because shuffling destroys exactly that enrichment. Use a class-balanced metric (balanced accuracy, or a selective risk–coverage curve on F1 or sensitivity), or report the retained set's prevalence.

**W7. DENTEX "teeth" are diseased teeth only, which the paper does not disclose.** The DENTEX disease subset annotates only teeth carrying a diagnosis (`RESULTS_LOG.md` l.1115). The 936 "teeth" in Tables 1 and 4 and Section VI-E are therefore about 5.7 diseased teeth per image, with impacted third molars heavily represented (244 at position 8 in `outputs/stage1_switch/I_taxonomy_arm3c/stage2_failure_taxonomy.json`). It is not the dentition. The DENTEX numbering accuracy (92.8%), the "identity costs 7.2 points" statement, and the per-position error rates are not comparable with the Tufts row (all teeth), and they are presented as if they were.

**W8. Contamination and selection disclosures are incomplete.**
- Tufts test radiograph 248 is a re-rendering of training radiograph 1017 from the same patient (`RESULTS_LOG.md` 2026-10-14; `model_metrics.md` l.703). It enters the Tufts Stage-1/Stage-2 figures (89.3%, 63.5%) and Stage-4 specificity. The paper says "all splits are image-level, chosen so that no radiograph contributes to both" and does not mention the same-patient duplicate. Tufts, DENTEX and the other corpora are split by image, not by patient; this should be stated as a limitation.
- Ningxia results under the previous front end (the +19 pp) were known when the current Stage-1 detector was chosen (`RESULTS_LOG.md` 2026-10-11f: "Ningxia is therefore no longer blind to the choice of Stage-1 detector"). The paper says only that Ningxia informed the *lesion detector's* adoption (Table 4, Section V).
- The Stage-1 switch was justified by the gain on the same 164 DENTEX images that are scored. All DENTEX results are therefore post-selection, which goes beyond "in-domain".

**W9. Baselines are thin on the learned side.** The only learned comparators are the authors' own crop classifier and two zero-shot, general-purpose VLMs run with one prompt and unrecorded decoding settings. There is no comparison to a published DENTEX method on the same task (for example the DENTEX challenge entries) or to a supervised detector trained only on DENTEX. Few-shot VLM runs exist in the artefacts (7B 2-shot F1 0.066, 4-shot 0.034; `outputs/c1_vlm/c1_comparison.json`) and are not reported. That is selective reporting in the paper's disfavour as well as its favour, and it should be disclosed. "Two vision-language models scored below that constant" is a weak headline result when the models were not adapted to the task.

**W10. The theoretical result is known prior art and is presented as new.** "The best list holds exactly the teeth whose prevalence exceeds half its F1" is the set-prediction instance of the known result that the F1-optimal threshold on calibrated probabilities equals half the optimal F1 (Lipton, Elkan and Naryanaswamy, "Optimal thresholding of classifiers to maximize F1 measure", ECML-PKDD 2014). The prefix/single-peak argument is the mediant inequality. Contribution 1 must cite this and recast the theory as an application, not a derivation.

**W11. The severity and abnormality evidence is reported partly by a single seed.** The retrained severity head is reported as 0.294 against a prior of 0.334. The other two seeds reached 0.328 and 0.382, and the old head 0.371 on radiographs it did not train on (`outputs/bone_loss_eval/v3_severity/test_summary.json`). One seed beats the prior. Reporting the pre-specified seed is defensible, but the spread must be given. The abnormality flag is reported only as sensitivity at a fixed specificity. The artefact has AUC about 0.69 and AP 0.15–0.18 against a prior AP of 0.080 (`outputs/bone_loss_eval/v2_retrain/test_summary.json`). These threshold-free figures should be reported, and so should PPV (seed 42: 50/202 = 24.8%).

**W12. Reproducibility is not yet at journal standard.** Release is undecided ("[ASK AUTHOR: release decision]"). The pre-registration anchor is not public. The CPU model is unstated. VLM decoding settings were not recorded. One training corpus (Kaggle FDI) has no stated licence. Every model except Stage 4a is a single training run, and one table value differs across machines (0.294 against 0.300). The external lesion-agreement matcher (centroid containment) does not say how a lesion centroid lying in two overlapping tooth boxes is assigned, which on OPGs is common at contacts.

## Unsupported or overstated claims

| # | Quote | Section | Why |
|---|---|---|---|
| 1 | "from 78 held-out radiographs the rule recovers the eight first and second molars" | Abstract | Factually wrong. Section III-B and Figure 2 say the 78 fit images are "excluded from scoring because our models trained on them". They are training images, not held-out ones. |
| 2 | "The system's per-crop caries classifier led it by 4.27 F1 points on development data" | Abstract, VI-B | Holds only against a constant that names absent teeth. A presence-aware image-blind constant likely exceeds 0.362 (W1). |
| 3 | "led the constant on the external sites by 9.28 points of lesion agreement [+4.72, +13.73] while flagging fewer teeth, at three of the four sites" | Abstract | The interval treats the sites as fixed, on a cohort that informed both the lesion detector's adoption and (per the artefacts) the front-end choice. The random-effects interval [-0.54, +19.76] and the HKSJ interval [-5.02, +24.24] include zero and belong in the abstract beside it. |
| 4 | "This prior mass is the cohort's, as placed by our front end … the site effect Zech et al. found" | III-C | Confounded with front-end recall per site: a detector change alone moved the constant by +19 to +26 pp (W3). |
| 5 | "A whole-image lesion detector receives no tooth identity: to flag a tooth it must place a box mostly inside it. It can express a positional prior only by drawing boxes over molars…" | III-E | On DENTEX it was trained on whole-tooth boxes, and a whole-image CNN sees arch position. Its flags are more molar-concentrated than the classifier's (71.6% against 66.6%) (W4). |
| 6 | "Both implications of Section III-E hold." | VI-D | The "fewer flags" implication is met by any higher threshold. The per-type precision comparison is at unmatched volume and is in-domain to tooth-box training (W4). |
| 7 | "The same metric moves 40 points across cohorts" | VII, RQ1 | Section V states that lesion agreement is matched by IoU ≥ 0.30 with centroid fallback on DENTEX and by centroid containment externally. The metric is not the same across cohorts, and V says every comparison is within a cohort. |
| 8 | "the prior is doing visible work" / Table 8 "Shortcut lifts healthy scores — holds" | III-D, VII | Not separable from molar-specific image confounders (W5). |
| 9 | "Declining the least-confident quarter raises … the crop classifier's from 0.797 to 0.940" | VI-E | Full-coverage accuracy is below always-negative (0.853). The gain partly reflects retention of easy negatives (W6). |
| 10 | "All splits are image-level, chosen so that no radiograph contributes to both training and evaluation." | V | A same-patient re-rendering crosses the Tufts train/test split (W8). The sentence is true literally but misleading by omission. |
| 11 | "A short theory of tooth-level caries scoring … the closed-form F1 of an image-blind constant and its selection rule" | I, contribution 1 | The selection rule is the known F1*/2 threshold result, uncited (W10). |
| 12 | "Placement is reliable: on Tufts, 92.0% … of the boxes our pipeline codes as one of the eight molars are true first or second molars." | III-C | Measured on a training corpus. The same paragraph uses it to interpret Ningxia and CariesXrays, where placement is unmeasured. Reach is 81.7%, so about 18% of true molars are not coded as molars. |
| 13 | "End-to-end FDI-exact accuracy on DENTEX is 92.8% (869 of 936 teeth)" | VI-E, Table 1 | These are diseased teeth only, not the dentition (W7). |
| 14 | "UFBA widened … 77.2" | Table 1 | `model_metrics.md` labels this row "sensitivity only, aspect unverified". The paper drops that qualifier. |

## Missing experiments

1. **Presence-aware image-blind constant on FDI-set F1**, scored on the same 164 images with the same front end, with a paired interval against each system. This is required: it may reverse RQ1 for the crop classifier.
2. **Constant's lesion agreement computed from ground-truth tooth boxes** where available, plus per-site front-end recall and molar placement on Ningxia, to separate cohort prior from detector behaviour.
3. **Per-tooth-type precision at matched volume.** For example, the crop classifier's top-447 molar flags against the detector's 447, on DENTEX, and on Ningxia once per-tooth records are regenerated (the authors note the images are available).
4. **A position-ablation test for the lesion detector.** Horizontally flipped or arch-shuffled inputs, or a detector trained without the DENTEX whole-tooth boxes (B-single exists, but it is confounded with domain).
5. **A learned position-only floor.** A model given only tooth type and position (and optionally restoration presence) that predicts caries, as a stronger image-blind baseline than a fixed set.
6. **A supervised DENTEX-trained comparator** and/or a published DENTEX method on the same 164 images.
7. **Patient-level de-duplication** of Tufts and DENTEX against training data, or a quantified bound on its effect.
8. **Threshold-free metrics (AUC, AP) with intervals** for the abnormality flag and for the lesion detector at tooth level, together with a lesion-level FROC on the external cohorts, which have lesion masks.
9. **A class-balanced selective-prediction analysis** for the crop classifier.
10. **Multiple training seeds** for the default caries and numbering models, or at least an estimate of seed variance for the headline F1 and agreement leads.

## Required corrections

1. **CRITICAL** — Abstract, Section VI-B, Table 5: add a presence-aware image-blind constant (names the eight molars only where the front end detects them) and restate the +4.27 and +17.80 leads against it.
2. **CRITICAL** — Section III-C, Table 8 row 2, Section VII RQ1: separate the cohort's caries prior from front-end recall and placement per site, citing the +19.25 pp shift of the constant under a detector change. Downgrade "holds" until that is done.
3. **MAJOR** — Abstract: "78 held-out radiographs" contradicts Section III-B; these images were used in training.
4. **MAJOR** — Section III-E and VI-D: disclose that the lesion detector's DENTEX training boxes are whole-tooth, and that a whole-image CNN encodes position. Report the 71.6% against 66.6% molar share. Replace the unmatched-volume per-type comparison with a matched-volume one, or withdraw "Both implications … hold".
5. **MAJOR** — Section III-D, Table 2: acknowledge the image confounders of tooth type. Report pooled AUC (0.855) beside within-type AUC (0.745). Give per-type AUC intervals or remove the per-type AUC column (5–8 positives for incisors and canines).
6. **MAJOR** — Tables 1 and 4, Section VI-E: state that the 936 DENTEX teeth are disease-annotated teeth only, and qualify the comparisons with Tufts and UFBA.
7. **MAJOR** — Section V and Section VIII: disclose the Tufts same-patient duplicate (248/1017) and that splits are by image, not patient. Disclose that Ningxia results were known when the current Stage-1 detector was chosen, and that the Stage-1 choice was made on the scored DENTEX images.
8. **MAJOR** — Abstract and Section VI-D: give the random-effects (and HKSJ) interval alongside the fixed-site 9.28 [+4.72, +13.73] in the abstract.
9. **MAJOR** — Section I contribution 1 and Section III-B: cite Lipton et al. (2014) for the F1*/2 rule, and present the theory as an application of it.
10. **MAJOR** — Section VI-E: redo the crop-classifier selective-prediction analysis with a class-balanced metric, and state the majority-class accuracy (0.853).
11. **MAJOR** — Section VI-B and VI-F: report the VLM few-shot runs present in the artefacts, the prompt in full (supplement), and that only one prompt was tried. Soften "Two vision-language models scored below that constant" as a headline finding.
12. **MAJOR** — Section VII RQ1: remove or qualify "The same metric moves 40 points across cohorts", since the matching rule differs between DENTEX and the external cohorts (Section V).
13. **MAJOR** — Data and Code Availability, Section IV: resolve the "[ASK AUTHOR]" items: code release, public pre-registration anchor, CPU model, ethics statement and author list. A manuscript with open placeholders cannot be reviewed as final.
14. **MINOR** — Section VI-F and Table 3: give all three severity seeds (0.294, 0.328, 0.382) and the old head's 0.371, not only the pre-specified seed.
15. **MINOR** — Section VI-F and Table 3: add AUC, AP and PPV for the Stage-4a flag beside sensitivity at fixed specificity.
16. **MINOR** — Table 1: restore the "aspect unverified, sensitivity only" qualifier on the UFBA widened row.
17. **MINOR** — Section V Metrics: specify how a lesion centroid inside two overlapping tooth boxes is assigned, and the ECE binning (10 equal-width bins, per the artefact).
18. **MINOR** — Section III-F: state that per-site variances are derived as (CI width / 3.92)^2 from percentile intervals, an approximation, and that the four Ningxia "sites" are release partitions of a three-hospital study, so site independence is assumed.
19. **MINOR** — Section VI-E calibration: the "stated 0.85 → observed 0.26" point rests on a bin of 31 crops. Give n, or an interval.
20. **MINOR** — Section III-C: state that the 92.0% placement figure is from Tufts (a training corpus) and that placement on the external cohorts is unmeasured. Report reach (81.7%) beside precision.

## Optional improvements

- Report each system's full operating curve (precision–recall over threshold) against the constant's prefix curve S_1…S_16 in one figure. This is more informative than single-point F1.
- Replace lesion agreement, or supplement it, with a lesion-level FROC on the external cohorts. Their lesion masks allow it, and it has the negative class (false positives per image) that agreement lacks.
- Section III-A's chain-rule decomposition is used once (Table 1). Either connect it quantitatively to the caries results, for example caries F1 recomputed on ground-truth tooth boxes to isolate the identity factors, or shorten it.
- Figure 6b: the crop-classifier interval at test4 appears to touch or include zero. State it in the text for completeness.
- Move the "evidence class" Table 3 earlier, or merge it with Table 4. It is the most useful single table for a reader.
- The single-corpus CariesXrays comparison (AP 48.2 against 48.2) adds little given the different split and checkpoint selection on the evaluation split. Consider moving it to a supplement.

## Numbers checked

| # | Claim | Paper value | Artefact path | Artefact value | Match? |
|---|---|---|---|---|---|
| 1 | Constant F1, scored set | 0.320; 286 TP / 1,312 named; recall 0.600 | `outputs/review_round1/constant_stability_and_curve.json` | f1 0.3197, tp 286, named 1,312, recall 0.5996 | Yes |
| 2 | Oracle constant | 0.330, six molars, P 0.245, R 0.505 | `outputs/c1_vlm/c1_constant_arm_vlm_32b_0shot.json` | f1 0.3299, P 0.2449, R 0.5052, 984 named (= 6 x 164) | Yes |
| 3 | Constant stability | 27% exactly eight; seven codes 45%; median 0.320 [0.279, 0.330]; flat 0.298–0.325 for k = 6–9 | same as #1 | 0.2668; size 7 0.453; median 0.3197 [0.2793, 0.3299]; k6 0.2984 … k7 0.3249 | Yes |
| 4 | Matched-volume leads | +22.35 [+17.42, +27.18]; +5.50 [+2.84, +8.22]; VLMs [-4.90, +5.63], [-2.06, +4.85] | same as #1 → `matched_volume` | identical | Yes |
| 5 | Crop-classifier pipeline FDI-set F1 | P 0.237, R 0.765, F1 0.362, 1,537 named | `outputs/stage1_switch/D_fdiset_gate_arm3c/c1_comparison.json` | 0.2375 / 0.7652 / 0.3625; TP 365 + FP 1,172 = 1,537 | Yes |
| 6 | VLM F1 | 32B 0.246 (P 0.250 R 0.243); 7B 0.149 (P 0.248 R 0.107) | `outputs/c1_vlm/c1_comparison.json` | 32B 0.2465 / 0.25 / 0.2432; 7B rerun 0.1493 / 0.2476 / 0.1069 | Yes (7B is the rerun; the original run gave 0.143 and 2/4-shot runs are unreported) |
| 7 | Lesion-detector FDI-set F1 and lead | 0.498; +17.80 [+13.48, +22.02]; 1.70 s/img | `docs/results/model_metrics.md` (arm3c table) | 0.498; +17.80 [+13.48, +22.02]; 1.70 | Yes |
| 8 | Table 7 lesion agreement | DENTEX 0.802/0.630/0.595; CXR 0.379/0.604/0.757; Ningxia 0.600/0.591/0.684 | `docs/results/model_metrics.md`; `outputs/stage1_switch/stage1_switch_results.log` | identical (Ningxia 0.6002/0.5913/0.6841) | Yes |
| 9 | Ningxia per-site lesion detector − constant | -3.16, +16.91, +11.73, +13.98 with stated CIs | `outputs/stage1_switch/F_ningxia_random_effects.json` | identical | Yes |
| 10 | Crop classifier − constant per site | -18.99 [-26.32, -11.84] test1; +12.32 [+5.01, +19.20] test2; pooled +0.89 [-3.86, +5.57] | `outputs/stage1_switch/stage1_switch_results.log` | identical | Yes |
| 11 | Random effects | +9.61 [-0.54, +19.76]; HKSJ [-5.02, +24.24]; I² 81%; tau 9.27 [3.22, 33.09]; PI [-36.08, +55.29] | `outputs/stage1_switch/F_ningxia_random_effects_hksj.json` | identical | Yes |
| 12 | Flags per image | 4.35 vs 7.15 (Ningxia); 2.16 vs 7.05 (CXR) | `stage1_switch_results.log`; `model_metrics.md` | 1,465/337 = 4.35; 2,410/337 = 7.15; 2,596/1,200 = 2.16; 8,457/1,200 = 7.05 | Yes |
| 13 | Table 2 shortcut test | healthy score 0.075→0.478; flagged 0.039/0.016/0.268/0.482; AUC 0.745 [0.660, 0.842]; AP 0.550 / 0.296 / 0.147 | `outputs/caries_position_bias/caries_position_bias_test.json` | 0.0747…0.4778; 0.0388/0.0161/0.2684/0.4817; 0.7454 [0.6604, 0.842]; 0.5503/0.2962/0.1472 | Yes |
| 14 | Calibration | ECE 0.136; temperature 0.152; isotonic 0.043; AP 0.550→0.500; 155 flips; 0.85→0.26 | `outputs/calibration/*.json` | 0.1362; 0.1521; 0.043; 0.55→0.4996; 155; bin 0.8–0.9 observed 0.2581 (n = 31) | Yes |
| 15 | Selective prediction | numbering 0.932→0.980, +4.76 [+3.29, +6.54]; classifier 0.797→0.940, +14.25; 0.30 at 96.1% / 0.941 | `model_metrics.md`; `outputs/c4_abstention/c4_coverage_accuracy.json` | identical (classifier full-coverage 0.7972, gain 14.25, shuffle 0.0) | Yes |
| 16 | Numbering errors | 869/936; 51 of 63 off by one (29 mesial / 22 distal); 6 quadrant errors; 11.3% / 10.1% / 4.1% / 8.2% by position | `outputs/stage1_switch/I_taxonomy_arm3c/stage2_failure_taxonomy.json` | 869; 51 (29/22); pos 2 7/62, pos 1 7/69, pos 5 4/98, pos 7 13/158 | Yes |
| 17 | Table 1 identity | Tufts 89.3 / 71.1 / 63.5 [59.3, 67.5]; UFBA 66.6 / 66.8 / 44.5; widened 95.6 / 80.8 / 77.2 | `model_metrics.md` | identical | Yes (but the widened row's "aspect unverified" qualifier is dropped) |
| 18 | Placement of constant's codes | 92.0% [89.58, 94.06] | `model_metrics.md` | 92.0% [89.58, 94.06]; reach 81.7% | Yes |
| 19 | Flag composition | 624 flags: 43.9 / 14.4 / 41.7%; molars 46.3 vs 28.4 vs 21.8%; premolars 39.7 vs 17.0% | `model_metrics.md`; `RESULTS_LOG.md` l.8498–8503 | identical (207/447; 291/1,023; 56/141; 65/382) | Yes |
| 20 | Stage-4a retrain | 27.5 / 16.5 / 11.0% (50, 30, 20 of 182); spec 95.9–98.6% | `outputs/bone_loss_eval/v2_retrain/test_summary.json` | TP 50/30/20 of 182; FP 152 and 51 of 3,710 → 95.9% and 98.6% | Yes |
| 21 | Stage-4 first model | 3.4% (6 of 175) on 125 radiographs | same file → `shipped.unseen_by_shipped` | 0.0343, TP 6, 175 positives, 125 radiographs | Yes |
| 22 | Severity head | 0.294 [0.214, 0.385] vs prior 0.334 | `outputs/bone_loss_eval/v3_severity/test_summary.json` | 0.2938 [0.2143, 0.385]; prior 0.3344 | Yes (seeds 43/44 at 0.328/0.382 unreported) |
| 23 | Lesion-detector training peak | mAP@0.5 0.820 at epoch 29 of 54 | `models/16_lever_b_pooled/lever_b_pooled_yolo11l-2/results.csv` | max 0.82012 at epoch 29; 54 rows | Yes |
| 24 | Detector Tufts box mAP | 0.587 vs 0.723 | `model_metrics.md` | 0.587 vs 0.723 | Yes |
| 25 | CariesXrays baseline comparison | 48.2 vs strongest baseline 42.2 | `PAPER_MATERIAL.md` l.2327; `model_metrics.md` | Conditional-DETR 42.2; ours 0.482 | Yes (the published table is itself flagged "re-verify against the AAAI PDF") |
| 26 | Earlier adoption under the previous front end | +12.2 [+10.1, +14.3] CXR; -3.3 [-8.4, +1.3] DENTEX | `models/16_lever_b_pooled/run_summary.txt` | identical | Yes |

No number I checked was wrong. The problems are in what the numbers are compared against, what they are labelled as, and what is left out.

## Recommendation: Major revision

The paper's central idea is valuable and under-practised in dental AI: score an image-blind constant beside every system, report per site, and pair the comparisons. The bookkeeping is exceptionally accurate; 26 of 26 checked numbers match the saved artefacts. However, the headline claims rest on comparisons that are not yet fair or not yet specific.
- The F1 constant is handicapped by naming absent teeth, and a presence-aware constant, which the authors already use for lesion agreement, plausibly overturns the crop classifier's +4.27 lead (W1).
- The "floor moves with the cohort" claim is confounded with per-site front-end behaviour, which a detector swap alone shifted by about 20 points (W3).
- The theoretical argument for why localisation resists the shortcut does not hold for a whole-image detector trained on whole-tooth DENTEX boxes, and its supporting evidence is in-domain and volume-unmatched (W4).
- The theory's core rule is a known result left uncited (W10).

Contamination and selection disclosures are also incomplete: the Tufts same-patient pair, Ningxia being known at the front-end choice, and DENTEX "teeth" being diseased teeth only. Several placeholders remain open. None of this requires new training except the optional ablations; most of it can be computed from saved outputs. The revision should still be substantial, because two of the three RQ conclusions may change in strength or direction.
