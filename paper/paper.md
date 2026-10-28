# What a Tooth-Level Score Cannot Tell You: Constant Baselines, External Validation and Domain Shift in Automated Panoramic Dental Screening

[ASK AUTHOR: author names, affiliations and e-mail addresses]

## Abstract

Systems that find tooth decay (caries) on panoramic dental radiographs are usually scored by which teeth they mark as diseased. We show that this tooth-level score is hard to interpret, because caries concentrates in the molars: a program that never reads the image and always names the same eight molars scores F1 0.320 on our development set. We built a six-stage pipeline (tooth detection, FDI numbering, caries, and a per-tooth abnormality flag) and scored it, two vision-language models and that constant with one scorer on 164 leakage-free radiographs. Both vision-language models scored below the constant. Our pipeline cleared it on the development set — F1 0.362 with a per-crop caries classifier and 0.498 with a whole-image lesion detector — but its tooth detector had trained on that corpus. On 337 radiographs from four hospitals that contributed no training data, the per-crop pipeline and the constant could not be separated (-0.89 points, 95% CI [-5.57, +3.86]), and on a second benchmark of 2,815 lesions the constant led by 22.42 points. The lesion detector, adopted under a rule written before training, led the constant by 9.28 points [+4.72, +13.73] on the four hospitals while flagging fewer teeth, at three of the four sites. We show every stage on real radiographs, the training curves of every trained model, and successes and failures against the expert annotation. We conclude that a tooth-level score alone cannot show that a system reads the radiograph, and that tooth identity, calibrated confidence, abstention and external per-site results are where that evidence has to come from.

**Index Terms**: panoramic radiography, dental caries, object detection, evaluation methodology, image-blind baselines, external validation, calibration, selective prediction

## I. Introduction

A panoramic dental radiograph (orthopantomogram, OPG) is one X-ray of both jaws (Figure 1). Two conventions make it unfamiliar to a computer-vision reader. First, it is displayed as if the viewer faces the patient, so the patient's right side is on the image's left. Second, teeth are named in FDI two-digit notation: the first digit is the quadrant (1 upper right, 2 upper left, 3 lower left, 4 lower right, in the patient's frame) and the second the position from the midline (1 central incisor to 8 third molar). Tooth 16 is therefore the upper-right first molar, and 36 the lower-left one. Caries appears as a dark (radiolucent) region inside the bright tooth; fillings and crowns are the brightest objects in the image.

![Figure 1](figures/R01_opg_primer.pdf)

**Figure 1.** Reading an OPG. One held-out DENTEX radiograph (test_120) cropped to the teeth. Dotted lines separate the quadrants Q1–Q4; numbers are the FDI codes our numbering stage assigned. Yellow: the expert's seven caries annotations as released, on teeth 12, 16, 28, 35, 36, 37 and 46. Dashed: the eight-molar set {16, 17, 26, 27, 36, 37, 46, 47} named by an image-blind constant; seven of its codes are present here, and four of the seven lesions lie on them. Radiographs: DENTEX (Hamamci et al., 2023), CC BY-NC-SA 4.0.

Automated systems detect each tooth and then classify it, and are scored per tooth: which teeth does the system call carious, and how well does that list match the expert's. Figure 1 shows why that score needs a floor. Caries is not spread evenly; molars carry most of it. A fixed list of molars collects part of the score without looking at any patient, so a reported number may reflect where caries usually is rather than where it is in this image — a shortcut in the sense of Geirhos et al. (Geirhos et al., 2020). In the 49 task-relevant papers of our own survey we noticed none that reports an image-blind baseline, an observation from that reading rather than a systematic count.

We ask three questions. RQ1: does tooth-level agreement separate a complete pipeline from an image-blind constant, on development data and on external cohorts? RQ2: does changing the caries task from classifying tooth crops to localising lesions in the whole image separate them? RQ3: what does the pipeline show on outputs a fixed list cannot produce — tooth identity, calibrated confidence and abstention? The contributions are:

1. A constant-baseline protocol for tooth-level OPG evaluation, applied with two metric families on three cohorts, one of them four external hospitals reported per site.
2. A pre-registered reformulation of the caries stage as lesion detection, which led the constant on the external hospitals while flagging fewer teeth.
3. The complete evidence trail of the system: every stage on a real radiograph, the training curves of the four trained models, and rule-chosen successes and failures against the expert annotation.
4. A vision-language-model baseline with content-free controls, and a fourth stage reported held out after its first score proved to be a split artefact.

## II. Related Work

**Data.** We use the Tufts Dental Database of 1,000 OPGs (Panetta et al., 2022), DENTEX (Hamamci et al., 2023), the CariesXrays benchmark of 6,000 OPGs (Chen et al., 2024), a multi-centre cohort from four Chinese hospitals (Li et al., 2024) and UFBA-425 [@budagam2024oralbbnet]. **Reported performance.** Numbering and classification systems report high in-domain figures (Zancan et al., 2025; Bilal et al., 2024); a bone-loss model compared with dentists reported weighted F1 0.29 (Cerda Mardini et al., 2024). Generalisation of dental image models across centres is known to be limited [@krois2021generalizability], and a dental-AI reporting checklist asks how the reference standard was built [@schwendicke2021checklist]. **Shortcuts and calibration.** An image-blind constant tests one shortcut (Geirhos et al., 2020). Temperature scaling (Guo et al., 2017) and isotonic regression (Zadrozny et al., 2002) are our calibration comparators. **Vision-language models.** We use Qwen2.5-VL (Bai et al., 2025) as general comparators that need no task training.

## III. System

The pipeline maps an OPG to a per-tooth record in six stages. Figure 2 shows each stage on one held-out radiograph, and Table 1 lists the models.

![Figure 2*](figures/R02_walkthrough.pdf)

**Figure 2.** One held-out DENTEX radiograph (test_0, not used to train any model) through the pipeline, exactly as it ships. (a) Input, 2,829 by 1,316 pixels; the dashed box is the region shown in (b)–(f). (b) Stage 1 finds 30 teeth (detection confidence beside each box). (c) Stage 2 assigns each an FDI code, one code per tooth; "?" marks the two codes it was unsure of (24, 42). (d) Stage 3a runs a lesion detector once on the whole image: four lesion boxes, confidence 0.35 to 0.89. (e) Each lesion box is assigned to the tooth it overlaps most, flagging 26 and 46 (caries) and 36 and 45 (deep caries); the Stage-4 abnormality flag fires on no tooth here. (f) The overlay the software writes, with the expert's three caries annotations (teeth 26, 45, 48) added in yellow: two are found, the lesion on 48 is missed, and 36 is flagged with no annotated lesion. Radiographs: DENTEX (Hamamci et al., 2023), CC BY-NC-SA 4.0.

**Stage 1** detects teeth with a YOLOv11l detector [@jocher2024yolo11] trained on three corpora in equal proportion: the Tufts training split, DENTEX's enumeration subset and a third public corpus. **Stage 2** crops each tooth (1.5 times its box), and a ResNet18 (He et al., 2016) with four positional features scores every FDI code; the Hungarian algorithm (Kuhn, 1955) turns the scores into a one-to-one assignment, so no two teeth share a code. **Stage 3a** has two implementations. The default is a whole-image YOLOv11l lesion detector whose boxes are assigned to the tooth box they overlap most; it trains on 4,800 CariesXrays images and 650 DENTEX images replicated to equal weight (9,600 samples per epoch), with confidence fixed at 0.25 in advance. The retained variant is a ResNet18 that classifies each tooth crop. **Stage 3b** grades flagged teeth as caries or deep caries. **Stage 4** is a ResNet18 trained on Tufts whose label is whether a tooth crop overlaps an expert-marked abnormality; it was built for periodontal bone loss, and we name it for its label. Its severity head is withheld by default (Section V-G). **Stages 5–6** fuse the outputs on the FDI code and write a JSON record per tooth; abridged, tooth 36 of Figure 2 reads:

```
{"fdi": 36, "fdi_confidence": 0.9999,
 "detection_confidence": 0.8389,
 "caries": {"finding": "deep_caries",
            "gate_confidence": 0.8892,
            "severity_confidence": 0.9579},
 "bone_loss": {"finding": "normal",
               "confidence": 0.7853},
 "assessable": true}
```

**Table 1.** Stages and learnable parameters, counted from the saved checkpoints.

| Stage | Model | Params |
|---|---|---|
| 1 Tooth detection | YOLOv11l | 25.31 M |
| 2 FDI numbering | ResNet18 + 4 features | 11.19 M |
| 3a Caries (default) | YOLOv11l lesion detector | 25.31 M |
| 3a Caries (variant) | ResNet18 crop classifier | 11.18 M |
| 3b Caries severity | ResNet18 | 11.18 M |
| 4a Abnormality flag | ResNet18 | 11.18 M |
| 4b Severity (withheld) | ResNet18 | 11.18 M |
| Total | | 95.34 M |

The complete system runs at 1.70 s per image on a laptop CPU with no GPU.

## IV. Data and Evaluation Protocol

**Cohorts.** Table 2 lists them. All splits are image-level. DENTEX's disease subset has 250 annotated OPGs; MD5 hashing found 86 byte-identical to images our models trained on (85 in numbering, 1 in detection), leaving 164 scored, of which 148 carry a caries lesion (479 lesions on 477 teeth). Because the tooth detector trained on other DENTEX images, every DENTEX result is in-domain for the front end. The Ningxia hospitals (test1–test4) were never trained on; they were, however, one of the three cohorts that decided the lesion detector's adoption. CariesXrays' 1,200 scored images are the lesion detector's validation split, so they are external for the crop classifier and the constant only.

**Table 2.** Evaluation cohorts.

| Cohort | Images | Lesions | Role |
|---|---|---|---|
| DENTEX disease | 164 | 479 | development |
| Ningxia, 4 hospitals | 337 | 1,013 | external |
| CariesXrays | 1,200 | 2,815 | external (except lesion detector) |
| Tufts test | 150 | — | detector, numbering, Stage 4 |
| UFBA-425 | 425 | — | numbering, unseen corpus |

**The ladder.** Four systems answer one question — which teeth in this radiograph show caries? — on the same 164 images: the pipeline (with each Stage-3a implementation), Qwen2.5-VL-32B (33.45 B parameters) and Qwen2.5-VL-7B (8.29 B), both zero-shot, and a constant. The constant is found by greedy search over tooth codes on the 78 excluded images that carry caries, then frozen: {16, 17, 26, 27, 36, 37, 46, 47}. It scores F1 0.392 on those images and 0.320 on the scored ones, as an honestly held-out fit should. The VLMs receive the FDI scheme in the prompt and are parsed permissively. As content-free controls they are also shown a blank grey image and a random-noise image.

**Metrics.** *FDI-set F1* treats each image as a set of carious tooth codes, micro-averaged over teeth. *Lesion-localisation agreement* is the fraction of expert lesions that overlap a flagged tooth: on DENTEX by greedy IoU >= 0.30 with a centroid fallback, and on external cohorts by centroid containment, because their lesions are small (median 731 pixels) inside tooth boxes of about 25,000 pixels. Agreement has no negative class and rises with the number of teeth flagged, so we report teeth flagged and the match rate beside it. Under this metric the constant's eight codes are placed by the pipeline's own boxes and numbering; on Tufts, 92.0% [89.58, 94.06] of them land on a true first or second molar.

**Statistics.** Intervals are 95% percentile cluster bootstraps over images, 10,000 resamples, seed 42 (2,000 for the caries classifier's calibration intervals; 1,000 with seed 0 for the two abstention gains), paired when two systems share images. Images, not teeth, are resampled, because errors within an image are correlated. **Pre-registration.** The lesion detector's adoption rule — beat both the constant and the crop classifier on at least two of three cohorts, at no more than 1.5 times their rate of flagged teeth — was committed (ef3f453) before any arm was trained.

## V. Results

### A. Training: what each model learned, on its validation split

Figure 3 shows the training logs of the four trained stages. Every training loss falls steadily; the checkpoint used is the best on each run's validation split, so these validation figures are selection diagnostics, not test results. The tooth detector reaches validation box mAP@0.5 0.634 on the 150 Tufts validation images at its last epoch (148), still rising slowly when training stopped. Its pre-registered guard on the frozen Tufts test split required box mAP@0.5 within four points of a Tufts-only control; it reached 0.587 against 0.723 and missed, and the detector was adopted regardless, by a dated decision, for the numbering and caries behaviour below. The lesion detector peaks at mAP@0.5 0.820 on the 1,200 CariesXrays validation images at epoch 29 of 54. The numbering head reaches crop-level FDI-exact 0.810 on 6,450 validation crops with ground-truth boxes at epoch 12 of 15; the quadrant digit is right on 98.1% of crops and the position digit on 82.5%, so almost all numbering error is in counting along the arch. The Stage-4a flag's validation macro-F1 stays below 0.6 in all three seeds (best 0.568, 0.580, 0.597), the first sign of its weakness.

![Figure 3*](figures/R04_training.pdf)

**Figure 3.** Training logs of the four trained stages, read from the saved run files. (a) Tooth detector, 148 epochs, validation on 150 Tufts radiographs. (b) Lesion detector, 54 epochs, validation on 1,200 CariesXrays radiographs. (c) Numbering head, 15 epochs, validation on 6,450 tooth crops (DENTEX and Tufts, ground-truth boxes). (d) Stage-4a flag, three seeds of one recipe. Dots mark the checkpoint each run kept. Validation splits, not test.

### B. RQ1 on development data

**Table 3.** Tooth-level caries prediction on 164 DENTEX images (477 carious teeth), micro-averaged.

| System | Precision | Recall | F1 |
|---|---|---|---|
| Pipeline, lesion detector | 0.439 | 0.574 | 0.498 |
| Pipeline, crop classifier | 0.237 | 0.765 | 0.362 |
| Constant (never reads image) | 0.218 | 0.600 | 0.320 |
| Qwen2.5-VL-32B, zero-shot | 0.250 | 0.243 | 0.246 |
| Qwen2.5-VL-7B, zero-shot | 0.248 | 0.107 | 0.149 |
| Oracle constant (test-fitted) | 0.245 | 0.505 | 0.330 |

Both VLMs see the radiograph and score below a list that does not, by +7.32 points [+3.42, +11.23] and +17.04 [+12.66, +21.22] (Table 3, Figure 4a). The frozen constant is one point below the oracle fitted on the test set, so almost all of the image-blind score is available without the evaluation data. Our pipeline leads the constant by +4.27 [+1.58, +7.05] with the crop classifier, by naming 1,537 teeth where the constant names 1,312, and by +17.80 [+13.48, +22.02] with the lesion detector, which leads on precision (0.439 against 0.218) and flags 624 tooth codes, 43.9% of them carious. Under lesion agreement (Figure 4b) the crop classifier leads the constant by 17.12 points [+12.15, +21.89], partly by volume: it flags 1,439 teeth against 988, at a lower match rate (0.267 against 0.306), and flagging every detected tooth reaches 0.998. The lesion detector flags 603 teeth at the highest match rate (0.473) and is not separable from the constant (-3.55 [-10.11, +2.64]).

![Figure 4*](../fig_baselines.png)

**Figure 4.** The constant-baseline comparison. (a) FDI-set F1 on 164 DENTEX images. (b) Lesion agreement on the same images, with teeth flagged inside each bar; the flag-everything arm shows the metric's ceiling. (c) The four external hospitals, crop classifier against the constant: the development lead does not replicate. (a) and (b) are in-domain for the tooth detector and use a different matcher from (c). Values are read from the saved evaluation files at render time.

### C. RQ1 on external data

On the four hospitals (Figure 4c) the crop-classifier pipeline and the constant are level when pooled: 0.600 against 0.591, a difference of -0.89 points [-5.57, +3.86]. Per site the difference runs from +19.0 points for the constant at test1 (0.709 against 0.519) to -12.3 at test2 (0.579 against 0.702), a 31-point swing within one cohort; test2 shares a centre with the source cohort's own training portion, though none of its data trained our system. On CariesXrays the constant wins outright, 0.604 against 0.379, by 22.42 points [+20.18, +24.62], and flags 46% more teeth at the higher match rate (0.200 against 0.188). The same pipeline is therefore 17 points above the constant, level with it, or 22 points below it depending only on the cohort, and it leads only on the corpus its detector trained on.

### D. RQ2: localising lesions instead of classifying teeth

Five direct repairs of the crop classifier — contrast equalisation, crop expansion, position-balanced sampling, a retrain and threshold tuning — all returned intervals spanning zero. We then changed the task. Under the tooth detector of the time, the lesion detector met the pre-registered rule on two cohorts of three: +12.2 points [+10.1, +14.3] over the constant on CariesXrays and +10.2 [+6.3, +14.0] on Ningxia, with a tie on DENTEX (-3.3 [-8.4, +1.3]). Table 4 gives the same three arms under the current detector.

**Table 4.** Lesion agreement of the three Stage-3a options, current tooth detector; difference of the lesion detector minus the constant, paired 95% CI.

| Cohort | Crop classifier | Constant | Lesion detector | Difference (pp) |
|---|---|---|---|---|
| DENTEX (dev.) | 0.802 | 0.630 | 0.595 | -3.55 [-10.11, +2.64] |
| CariesXrays (its val. split) | 0.379 | 0.604 | 0.757 | +15.38 [+12.96, +17.73] |
| Ningxia (external) | 0.600 | 0.591 | 0.684 | +9.28 [+4.72, +13.73] |

The lead is not a volume effect: the lesion detector flags fewer teeth than the constant on every cohort (4.35 per image against 7.15 on Ningxia, 2.16 against 7.05 on CariesXrays). Per hospital it is separated from the constant at test2, test3 and test4 (+16.91 [+9.17, +24.62], +11.73 [+1.07, +21.34], +13.98 [+2.34, +24.34]) and not at test1 (-3.16 [-10.56, +3.97]). Treating the hospitals as a sample (DerSimonian–Laird random effects, post hoc) gives +9.61 [-0.54, +19.76] with I-squared 81%: the lead holds at three of these four hospitals and is not shown for an unseen one. The training mixture, not the architecture, transfers: an arm trained on CariesXrays alone reached 0.694 [0.674, 0.714] on CariesXrays and collapsed to 0.086 [0.055, 0.119] on DENTEX and 0.240 [0.209, 0.272] on Ningxia.

Figure 5 shows what these numbers look like on images. Rows were chosen by a rule fixed before rendering: the scored image with the most lesions all found, a typical image, and the image with the most lesions none found.

![Figure 5*](figures/R03_outcomes.pdf)

**Figure 5.** Pipeline output against the expert on three held-out DENTEX radiographs; left the lesion detector, right the constant placed by the same front end. (a) test_120: all seven lesions found; 33 and 34 are also flagged with no annotated lesion. The constant, without reading the image, covers four of the seven. (b) test_0 (Figure 2): two of three found; the lesion on 48 is missed. (c) test_110: none of four found — lesions on 32, 33, 34 and 46 are missed while 16, 24, 26, 36 and 37 are flagged. A flagged tooth without an annotated lesion is not a confirmed false positive, since the annotation's exhaustiveness is not documented. Radiographs: DENTEX (Hamamci et al., 2023), CC BY-NC-SA 4.0.

### E. RQ3: outputs a constant cannot produce

**Numbering.** End-to-end FDI-exact accuracy on DENTEX is 92.8% (869 of 936 teeth) [90.6, 94.9], an in-domain figure; 4 of the 936 teeth are never detected, and 93.2% of the 932 found are numbered correctly. Of 63 wrong codes, 51 (81.0%) name an adjacent tooth in the correct quadrant, and 6 of 932 detected teeth (0.6%) get a quadrant-level error. On the Tufts test split (3,760 teeth) the pipeline reaches 63.5% [59.3, 67.5] end to end, with 89.3% of teeth detected and 71.1% of those numbered correctly. On UFBA-425, which no model trained on, it reaches 44.5% [42.39, 46.62] on the square export as distributed, and 77.2% [75.19, 79.14] with each image widened to a panoramic shape.

**Calibration** (measured on the crop classifier, not the lesion detector, which emits detection scores rather than per-tooth probabilities). The classifier is overconfident: expected calibration error (ECE) 0.136. Temperature scaling made it worse (0.152); isotonic regression reduced it to 0.043, at a cost — average precision falls from 0.550 to 0.500, and applied at the threshold it would change 155 of 863 verdicts — so we apply it to the reported confidence only. Its average precision, 0.550 [0.445, 0.660] against a prevalence of 0.147, shows that it ranks teeth well and fails at calibration and operating point.

**Selective prediction.** Declining the least-confident quarter raises numbering accuracy from 0.932 to 0.980 (+4.76 points [+3.29, +6.54], 164 image clusters) and the crop classifier's from 0.797 to 0.940 (+14.25 [+11.32, +16.63], 34 clusters). With shuffled confidences both gains collapse to -0.06 and +0.00 points, so the gain comes from the confidence ranking, not from discarding items. The 0.30 threshold fixed in code lands at 96.1% coverage and 0.941 accuracy.

### F. Vision-language model controls

Qwen2.5-VL-7B answers 26,36 to a blank grey image, to random noise and to a real radiograph. Qwen2.5-VL-32B answers NONE to the blank image but, shown noise, answers 16, 17, 26, 27, 36, 37, 46, 47 — exactly the constant's set. Few-shot prompting lowers the 7B model's F1 from 0.149 to 0.066 (two shots) and 0.034 (four), by abstaining: empty answers rise from 56 to 123 of 164 images. These outputs on a noise input are not perception, for these two models under this prompt.

### G. Stage 4, measured held out

The first Stage-4 model reported 0.923 macro-F1 on a crop-level split in which every validation radiograph also supplied training crops; on 125 test radiographs it had not trained on it found 3.4% of labelled teeth (6 of 175). Retrained with the split made by radiograph, three runs found 27.5%, 16.5% and 11.0% (50, 30 and 20 of 182) at 95.9–98.6% specificity and 24.8–29.4% precision (Figure 6). On DENTEX, which has no such label, the flag fires on 6.1% of detected teeth (274 of 4,512). The severity head, retrained on extent bands, scored macro-F1 0.294 [0.214, 0.385] against 0.334 for an image-blind tooth-position prior, did not meet its registered rule, and stays withheld. We make no periodontal claim.

![Figure 6](../fig_stage4a.png)

**Figure 6.** Stage 4 on the held-out Tufts test split (143 radiographs, 3,892 teeth, 182 carrying its label): three training runs with 95% radiograph-bootstrap intervals, beside the first model on the 125 radiographs it had not trained on.

## VI. Discussion

**RQ1.** The pipeline clears the image-blind constant on the corpus its detector trained on, is level with it pooled over four external hospitals, and loses to it on a second benchmark; the same metric moves 40 points across cohorts and 31 across one cohort's sites. A favourable tooth-level figure on development data is therefore weak evidence of perception. Figure 1 and Figure 5 show the mechanism: the constant's molars overlap a large share of the expert's lesions without reading any pixel. **RQ2.** A detector that must place lesion boxes cannot score by reproducing a prior over positions, and it led the constant on the external hospitals while flagging fewer teeth; that lead is conditioned on Ningxia having informed its adoption, and the change of task is confounded with new training data. **RQ3.** Numbering, calibration and abstention with a shuffle control are outputs a constant cannot attempt; they still lack position-only controls. **What to report.** We propose that a tooth-level caries score be reported with an image-blind row, per-site external results, and the qualitative and training evidence of Figures 2, 3 and 5, so a reader can see what the system does on an image.

## VII. Limitations

- DENTEX results are in-domain for the tooth detector, and the detector was adopted although it missed its pre-registered Tufts guard (0.587 against 0.723).
- Only Ningxia is external to the lesion detector, and it informed the detector's adoption; the random-effects interval includes zero.
- The lesion detector has no calibration or abstention curve of its own; those results describe the crop classifier.
- Internal and external agreement use different matchers and are not comparable; agreement has no negative class, and the external cohorts have no healthy controls.
- Training-curve values are on validation splits used to select checkpoints and are optimistic; every model is a single run except Stage 4a's three seeds.
- The qualitative examples are three images chosen by a rule; they illustrate, and do not replace, the cohort statistics.
- No clinician comparison was made, and no reference standard was re-annotated.

## VIII. Conclusion

On three cohorts the same pipeline sat above, level with and below an image-blind molar constant on tooth-level caries agreement, leading only on the corpus its detector had trained on. Reformulating caries as lesion localisation led the constant on four external hospitals while flagging fewer teeth. Real outputs, training logs and rule-chosen failures are shown beside every number. A tooth-level score reported alone cannot show that a system reads the radiograph; an image-blind row, per-site external results and visible evidence from the images should accompany it.

## Acknowledgment

[ASK AUTHOR: confirm wording] This manuscript draft was prepared with the assistance of the Research Communication Engine and the Claude Opus 5.5 model, which drafted text and rendered figures from the project's saved evaluation artifacts and models under the authors' direction. The authors are responsible for its content.

## References
