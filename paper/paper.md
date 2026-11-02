# What a Tooth-Level Score Cannot Tell You: Positional Priors, Image-Blind Baselines and External Validation in Panoramic Dental Screening

[ASK AUTHOR: author names, affiliations and e-mail addresses]

## Abstract

Systems that find dental caries on panoramic radiographs are scored by which teeth they mark as carious. We show, in theory and then on three cohorts, that this score mixes the pixels of the tooth with a prior over where caries usually occurs. We derive the F1 of a list that never reads the image in closed form: the best list holds exactly the teeth whose caries prevalence exceeds half its F1, and from 78 held-out radiographs the rule recovers the eight first and second molars, which score F1 0.320 on our 164 scored images. Against that constant we scored a six-stage pipeline (tooth detection, FDI numbering, caries, an abnormality flag and a per-tooth report) and two vision-language models, both of which scored below it. The pipeline's per-crop caries classifier led the constant by 4.27 F1 points on development data, but its scores on healthy teeth tracked each position's base rate, and on 337 radiographs from four external sites it was level with the constant (+0.89 points, 95% CI [-3.86, +5.57]). A whole-image lesion detector, adopted under a rule written before training, led the constant there by 9.28 points [+4.72, +13.73] while flagging fewer teeth, at three of the four sites. Every stage is shown on real radiographs, with training curves and rule-chosen failures. A tooth-level score alone cannot show that a system reads the radiograph; an image-blind row, per-site external results and outputs a prior cannot produce must accompany it.

**Index Terms**: panoramic radiography, dental caries, object detection, shortcut learning, image-blind baselines, external validation, calibration, selective prediction

## I. Introduction

A panoramic dental radiograph (orthopantomogram, OPG) is a single X-ray of both jaws, unrolled into one wide image (Figure 1). Two conventions make it unfamiliar to a computer-vision reader. It is displayed as if the viewer faces the patient, so the patient's right side is on the image's left. And teeth are named in FDI two-digit notation: the first digit is the quadrant (1 upper right, 2 upper left, 3 lower left, 4 lower right, in the patient's frame) and the second the position counted from the midline (1 central incisor to 8 third molar). Tooth 16 is therefore the upper-right first molar and 36 the lower-left one. Caries dissolves mineral, so a lesion appears as a darker (radiolucent) region inside the bright tooth; fillings and crowns are the brightest objects in the image.

![Figure 1](figures/R01_opg_primer.pdf)

**Figure 1.** Reading an OPG. One held-out DENTEX radiograph (test_120) cropped to the teeth. Dotted lines separate the quadrants Q1–Q4; numbers are the FDI codes our numbering stage assigned. Yellow: the expert's seven caries annotations as released, on teeth 12, 16, 28, 35, 36, 37 and 46. Dashed: the eight-molar set {16, 17, 26, 27, 36, 37, 46, 47} named by an image-blind constant (Section III-B); seven of its codes are present here, and four of the seven lesions lie on them. Radiographs: DENTEX [@hamamci2023dentex], CC BY-NC-SA 4.0.

**A theory of the tooth-level score.** Consider what an automated report asks of such an image. For every tooth it must decide three things in sequence: that a tooth is there, which tooth it is, and whether it carries a finding. The decisions compose, so an entry is right only when all three are, and an early error cannot be repaired later: a lesion correctly recognised but attached to the wrong tooth number is a wrong report. A score that summarises only the last decision is silent about the two that condition it.

The last decision itself draws on two sources of evidence: the pixels of the tooth, and the tooth's identity. Caries is not spread evenly over the mouth; in our data the first and second molars carry most of it (Figure 2). A learner trained to minimise error over a population will use any cue that predicts the label, and position predicts it, so a model can earn part of its score by knowing where caries usually is rather than seeing where it is in this image — a shortcut in the sense of Geirhos et al. [@geirhos2020shortcut]. The usual metric cannot tell the two apart, because a set of tooth codes can be chosen without any image; Section III derives the best such set from the prevalence of caries at each position.

Two consequences organise this paper. First, a reported score has a floor set by the prior, so it means little until an image-blind constant is scored beside it. Second, the floor moves with the population: a constant's lesion agreement is the share of a cohort's lesions that lie on its teeth, and a model that has absorbed the prior moves with it, whereas a model that reads the lesion need not. Agreement on one development cohort therefore cannot separate the two explanations; agreement on external cohorts, paired with the constant and reported per site, can. The theory also says what a fixed list cannot do — place a lesion in the image, name the tooth, state a calibrated confidence, decline to answer — and those outputs are where evidence of perception has to come from.

We test these predictions on a complete system. RQ1: does tooth-level agreement separate a full pipeline from an image-blind constant, on development data and on external cohorts? RQ2: does reformulating the caries stage from classifying tooth crops to localising lesions in the whole image — a task a positional prior cannot satisfy — separate them? RQ3: what does the pipeline show on outputs a fixed list cannot produce? The contributions are:

1. A short theory of tooth-level caries scoring — the error chain of a tooth-indexed report, the closed-form F1 of an image-blind constant and the rule that selects it, the dependence of lesion agreement on a cohort's prior, and a testable signature of a positional shortcut — each checked against our data.
2. A constant-baseline protocol with two metric families on three cohorts, one of them four external sites reported per site, with paired cluster-bootstrap intervals.
3. A pre-registered reformulation of the caries stage as lesion detection, which led the constant on the external sites while flagging fewer teeth.
4. The evidence trail: every stage on a real radiograph, training curves of the four trained models, rule-chosen successes and failures, and a vision-language baseline with content-free controls.

## II. Related Work

**Datasets.** We use the Tufts Dental Database of 1,000 OPGs with expert tooth and abnormality annotations [@panetta2022tufts], DENTEX with hierarchically annotated quadrant, enumeration and diagnosis data [@hamamci2023dentex], the CariesXrays lesion benchmark of 6,000 OPGs [@chen2024cariesxrays], the multi-centre dataset of Li et al., collected at three hospitals in Ningxia and Shenzhen [@li2024multicenter], and UFBA-425 [@budagam2024oralbbnet]. **Detection, numbering and caries.** A systematic review of deep-learning caries detection found accuracies of 86.1–96.1% on panoramic radiographs, in studies whose quality and reporting it judged low [@mohammadrahimi2022deep]. Caries and periodontal classification have used dual networks [@lim2024dual], dedicated convolutional classifiers [@bilal2024pdcnet] and contrastive feature pyramids [@chen2024cariesxrays]. Numbering is reported at very high figures — class-averaged accuracy 0.9988 (F1 0.979) in one recent system [@zancan2025ai] — and a multi-stage segmentation-and-numbering system outperforms prior methods on Tufts and two other datasets [@zhang2025reliable]; often on pre-cropped teeth, an easier task than numbering under detector output. **Transfer.** Of 516 medical-imaging AI studies published January–August 2018, only 31 (6%) validated externally [@kim2019design]. Dental models tested elsewhere degrade: an apical-lesion model fell from F1 54.1% to 32.7% at a second centre [@krois2021generalizability]; a YOLOv11 detector of 13 conditions fell from mAP@0.5 0.857 to 0.806 on external images, strongest on crowns and implants and weakest on subtle pathology such as caries [@mutlu2026comparison]; and a bone-loss model compared with five clinicians reached weighted F1 0.29 [@cerda2024determining]. One enumeration-then-caries detector held lesion sensitivity at 0.70 internally and 0.67 externally [@bizjak2024advancing].

**Shortcuts and input-blind baselines.** Shortcut learning predicts that a model will exploit any cue correlated with the label [@geirhos2020shortcut], and other fields test for it with baselines that withhold the input the task is about. Visual-question-answering models were found to answer from language priors while ignoring the image, which inflated their apparent capability [@goyal2017making], and lost accuracy when answer priors differed between training and test [@agrawal2018dont]; in natural-language inference, a model that never sees the premise beats the majority class on many datasets [@poliak2018hypothesis]. In medical imaging, COVID-19 detectors relied on confounders and failed at new hospitals [@degrave2021ai], and in a pneumonia task sorting radiographs by hospital alone reached AUC 0.861 because prevalence differed between sites [@zech2018variable]. Reading the 49 task-relevant papers of our own survey of OPG analysis, we noticed none that reports an image-blind baseline; this is an observation from that reading, not a systematic count. **Calibration, abstention and VLMs.** Temperature scaling [@guo2017calibration] and isotonic regression [@zadrozny2002isotonic] are our calibration comparators, and abstention follows selective classification [@geifman2017selective]. Vision-language models (VLMs) are being adapted to dental diagnosis [@meng2026dentvlm]; we use Qwen2.5-VL [@bai2025qwen25vl] as general comparators that need no task training.

## III. Theory: What a Tooth-Level Score Measures

### A. The report as a chain of decisions

The report's entry for a tooth is correct only if the tooth is detected ($D$), numbered correctly once detected ($N$), and given the right finding ($F$):

$$
P(\text{entry correct}) = P(D)\, P(N \mid D)\, P(F \mid D, N).
$$

The first two factors concern identity, not disease, and bound everything after them: a perfect caries model still writes a wrong report on every tooth that was missed or misnumbered. A metric that matches findings to teeth by code (FDI-set F1, Section III-B) charges for both; one that matches lesions by position in the image (lesion agreement, Section III-C) is blind to the second. Table 1 measures the identity factors of our pipeline; the columns multiply exactly, and what the table adds is where the losses fall. On DENTEX, whose other images trained the detector, identity costs 7.2 points; on the Tufts test split, also from a training corpus, 36.5; on UFBA-425, which no model trained on, 55.5 points as the files are distributed.

**Table 1.** Identity before disease: the first two factors of (1) per tooth, in percent. Det.: detected; Exact: numbered exactly, of those detected; End to end: their product, with a 95% cluster-bootstrap interval. DENTEX 164 images, Tufts test 143, UFBA-425 425 (as distributed, and widened to a panoramic shape).

| Corpus | Teeth | Det. | Exact | End to end |
|---|---|---|---|---|
| DENTEX | 936 | 99.6 | 93.2 | 92.8 [90.6, 94.9] |
| Tufts test | 3,760 | 89.3 | 71.1 | 63.5 [59.3, 67.5] |
| UFBA as is | 11,591 | 66.6 | 66.8 | 44.5 [42.4, 46.6] |
| UFBA widened | 11,591 | 95.6 | 80.8 | 77.2 [75.2, 79.1] |

### B. An image-blind constant, in closed form

Let $N$ images be scored, $P$ be the number of carious teeth over all of them, and $n_c$ the number of images in which tooth code $c$ is carious, so that $p_c = n_c/N$ is the prevalence of caries at position $c$. A constant answers the same set $S$ of codes for every image. Its true positives are $\sum_{c \in S} n_c$ and it names $|S|N$ codes, so its micro-averaged F1 is

$$
F_1(S) = \frac{2 \sum_{c \in S} n_c}{|S|\,N + P}.
$$

Nothing in (2) depends on an image, and the constant's recall, $\sum_{c \in S} n_c / P$, is simply the share of carious teeth that lie at its codes. Writing $A = \sum_{c \in S} n_c$ and $k = |S|$, adding a code $c \notin S$ raises the score, $2(A+n_c)/((k+1)N+P) > 2A/(kN+P)$, if and only if

$$
p_c > \tfrac{1}{2}\, F_1(S).
$$

For any fixed size the best set is the $k$ most prevalent codes, so the F1-optimal constant is a prefix of the codes sorted by prevalence, cut where (3) first fails: a functional of the caries prior alone.

![Figure 2*](figures/R05_positional_prior.pdf)

**Figure 2.** The positional prior and the constant it implies. (a) For each FDI code, in chart order (patient's right to left, as displayed), the share of images in which the expert marked that tooth carious: grey, the 78 DENTEX images excluded from scoring because our models trained on them and that carry caries (the fit set); orange, the 164 scored images. Magenta codes are the eight that rule (3) admits from the fit set; dashed, the final threshold $F_1/2 = 0.196$. (b) F1 of the constant made of the $k$ most prevalent fit-set codes. Computed from the released labels with the evaluation's own loaders; the script asserts that it reproduces the saved scores.

On the fit set (Figure 2) rule (3) admits the eight first and second molars, with prevalences from 0.372 (tooth 26) to 0.205 (tooth 27), and rejects the ninth code, tooth 15, at 0.128 against a threshold of 0.196 — exactly the set the evaluation's greedy search returns. Frozen, {16, 17, 26, 27, 36, 37, 46, 47} scores F1 0.392 on its fit images and 0.320 on the 164 scored ones — 286 true positives among 1,312 named codes, against 477 carious teeth, so its recall is 0.600, the share of carious teeth that lie on those eight molars. The prior shifts between the two sets: teeth 17 and 27 fall to 0.140 and 0.134 on the scored images, so the oracle constant fitted on the scored images themselves keeps six molars and reaches only 0.330. Almost all of the image-blind score is therefore available without the evaluation data.

### C. Lesion agreement and the cohort's prior

The second metric family scores lesions rather than codes. Let a cohort contain $L$ expert lesions, let $T(\ell)$ be the detected tooth that contains lesion $\ell$, and let $\mathcal{F}$ be the set of teeth a system flags. Lesion agreement is

$$
A(\mathcal{F}) = \frac{1}{L} \sum_{\ell} \mathbf{1}\big[\, T(\ell) \in \mathcal{F} \,\big].
$$

$A$ has no negative class. It can only rise as $\mathcal{F}$ grows, and flagging every detected tooth reaches its ceiling, the share of lesions inside any detected tooth (0.998 on DENTEX); it must be read beside the number of teeth flagged. For the constant, $\mathcal{F}$ is the eight molar boxes our front end finds, so $A$ is the cohort's prior mass on those molars. Placement is reliable: on Tufts, 92.0% [89.58, 94.06] of the boxes our pipeline codes as one of the eight molars are true first or second molars. The prior mass belongs to the cohort, not to any model — 0.630 on DENTEX, 0.604 on CariesXrays, 0.591 on the four Ningxia sites, and from 0.494 to 0.709 between sites of that one cohort (Section VI) — the effect Zech et al. measured when pneumonia prevalence differed between hospitals [@zech2018variable]. A system that has absorbed the prior inherits this variation, so systems can be compared only when paired on the same images, cohort by cohort and site by site.

### D. A testable signature of a positional shortcut

If a per-tooth classifier has learned the probability of caries given position, and not only given pixels, two consequences follow. Its score on teeth that are truly healthy should rise with the base rate of their position, because the prior lifts every tooth of a caries-prone type. And its ranking should survive only partly when position is held fixed: the within-type AUC, which ranks carious against healthy teeth of the same type, removes the positional cue and keeps the image signal. Table 2 applies both tests to the pipeline's crop classifier on 863 held-out tooth crops from 34 radiographs, cut with ground-truth boxes so that the front end plays no part.

**Table 2*.** The positional-shortcut test on the crop classifier: 863 held-out crops from 34 radiographs. Base rate: share carious in its training data. Within-type AUC interval: cluster bootstrap over the 34 radiographs, 5,000 resamples.

| Tooth type | Crops | Carious | Base rate | Mean score, healthy | Healthy flagged | Within-type AUC |
|---|---|---|---|---|---|---|
| Incisor | 266 | 8 | 0.017 | 0.075 | 0.039 | 0.681 |
| Canine | 129 | 5 | 0.023 | 0.087 | 0.016 | 0.748 |
| Premolar | 221 | 31 | 0.157 | 0.273 | 0.268 | 0.781 |
| Molar | 247 | 83 | 0.343 | 0.478 | 0.482 | 0.781 |
| All, within type | 863 | 127 | — | — | — | 0.745 [0.660, 0.842] |

The classifier's mean score on healthy teeth climbs with the training base rate, from 0.075 on incisors to 0.478 on molars, and it flags 48.2% of healthy molars: the prior is doing visible work, and costs precision. Its within-type AUC is 0.745 [0.660, 0.842], above 0.5, so there is also genuine lesion signal. A predictor that uses position alone and never sees an image reaches average precision (AP) 0.296, against the classifier's 0.550 and chance at 0.147. The classifier is neither a lookup table nor a pure reader; it is a reader whose reported score is inflated by a prior that the constant captures for free.

### E. Why localisation resists the shortcut

A whole-image lesion detector receives no tooth identity. To flag a tooth it must place a box that lies mostly inside that tooth. It can express a positional prior only by drawing boxes over molars where it sees no lesion, and each such box is charged as a false positive under (2) and earns agreement under (4) only if a lesion happens to lie there. The theory therefore predicts that if the detector's lead over the constant comes from reading the image, it should come with fewer flagged teeth, not more, and within each tooth type its flags should be carious more often than the classifier's.

### F. Inference over images and sites

Teeth within one radiograph share exposure, anatomy and annotator, so their errors are correlated; we resample images, not teeth, the cluster bootstrap that stays consistent when clusters carry random effects [@field2007bootstrapping]. For two systems scored on the same images, the paired difference is recomputed on each bootstrap resample of images, and its 2.5th and 97.5th percentiles give the interval. Across sites, per-site differences $\Delta_j$ with variances $v_j$ (from each site's interval width) are pooled by DerSimonian–Laird random effects [@dersimonian1986meta],

$$
\hat\mu = \frac{\sum_j \Delta_j / (v_j + \hat\tau^2)}{\sum_j 1 / (v_j + \hat\tau^2)},
$$

where the between-site variance $\hat\tau^2$ is estimated from Cochran's $Q$, and $I^2 = (Q - k + 1)/Q$ is the share of variation due to sites [@higgins2002quantifying]. A fixed-site interval asks whether a system led at these sites; the random-effects prediction interval asks whether it would lead at another [@riley2011interpretation].

## IV. System

The pipeline maps an OPG to a per-tooth record in six stages (Figure 3); Figure 4 follows one held-out radiograph through every stage.

![Figure 3*](figures/R06_architecture.pdf)

**Figure 3.** The pipeline as it ships, with its default checkpoints and learnable parameter counts read from the saved weights (95.34 M in total). Blue: identity stages; dark blue: the default caries path; dashed orange: the retained caries variant, evaluated throughout as the comparison arm; green: the abnormality flag. Thresholds are the ones fixed in code; none was tuned on an evaluation cohort.

**Stage 1** is a YOLOv11l detector [@jocher2024yolo11]. **Stage 2** scores every FDI code for each tooth crop with a ResNet18 [@he2016resnet] and four box-position features, and the Hungarian algorithm [@kuhn1955hungarian] makes the assignment one-to-one. **Stage 3a** is by default a whole-image YOLOv11l lesion detector (9,600 samples per epoch, from 4,800 CariesXrays and 650 replicated DENTEX images) whose boxes go to the tooth containing most of each; the retained variant classifies each tight tooth crop. **Stage 3b** grades flagged teeth. **Stage 4** flags a tooth crop that overlaps an expert-marked abnormality; it was built for periodontal bone loss, and we name it for its label. **Stages 5–6** fuse the outputs on the FDI code into the report, the system's only output; the whole system runs at 1.70 s per image on a laptop CPU with no GPU. Abridged, the record for tooth 36 of Figure 4 reads:

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

![Figure 4*0.88](figures/R02_walkthrough.pdf)

**Figure 4.** One held-out DENTEX radiograph (test_0, not used to train any model) through the pipeline, exactly as it ships. (a) Input, 2,829 by 1,316 pixels; the dashed box is the region shown in (b)–(f). (b) Stage 1 finds 30 teeth (detection confidence beside each box). (c) Stage 2 assigns each an FDI code, one code per tooth; "?" marks the two codes it was unsure of (24, 42). (d) Stage 3a runs a lesion detector once on the whole image: four lesion boxes, confidence 0.35 to 0.89. (e) Each lesion box is assigned to the tooth that contains most of it, flagging 26 and 46 (caries) and 36 and 45 (deep caries); the Stage-4 abnormality flag fires on no tooth here. (f) The overlay the software writes, with the expert's three caries annotations (teeth 26, 45, 48) added in yellow: two are found, the lesion on 48 is missed, and 36 is flagged with no annotated lesion. Radiographs: DENTEX [@hamamci2023dentex], CC BY-NC-SA 4.0.

## V. Data and Evaluation Protocol

**Cohorts** (Table 3). All splits are image-level. DENTEX's disease subset has 250 annotated OPGs; MD5 hashing found 86 byte-identical to images our models trained on (85 in numbering, 1 in detection), leaving 164 scored, of which 148 carry a caries lesion (479 lesions on 477 teeth). Ningxia is the public release of the dataset of Li et al. [@li2024multicenter]: their paper describes three hospitals, and the release divides its test data into four sets — test2 from its training centre, test1, test3 and test4 described as cross-centre — which we treat as four sites.

**Table 3.** Evaluation cohorts, units and exposure. Each row is an analysis population; counts must not be summed across rows.

| Cohort | Images | Unit (n) | Role and exposure |
|---|---|---|---|
| DENTEX disease | 164 | 936 teeth; 477 carious teeth; 479 lesions | development; the tooth detector trained on other DENTEX images |
| Ningxia, 4 sites | 337 | 1,013 lesions | external; never trained on, but informed the lesion detector's adoption |
| CariesXrays | 1,200 | 2,815 lesions | external, except for the lesion detector, whose validation split it is |
| Tufts test | 143 | 3,760 teeth | numbering and Stage 4; both trained on the Tufts training split |
| UFBA-425 | 425 | 11,591 teeth | numbering; no model trained on it |

**The ladder.** Four systems answer one question — which teeth in this radiograph show caries? — on the same 164 images: the pipeline (with each Stage-3a implementation), Qwen2.5-VL-32B (33.45 B parameters) and Qwen2.5-VL-7B (8.29 B), both zero-shot with the FDI scheme in the prompt, and the constant of Section III-B. As content-free controls the VLMs are also shown a blank grey image and a random-noise image.

**Metrics.** FDI-set F1 (2) is micro-averaged over teeth. Lesion agreement (4) matches each expert lesion to a flagged tooth: on DENTEX by greedy IoU of at least 0.30 with a centroid fallback, on the external cohorts by centroid containment, because their lesions are small (median 731 pixels) inside tooth boxes of about 25,000 pixels; every comparison is therefore within a cohort.

**Statistics.** Intervals are 95% percentile cluster bootstraps over images (Section III-F): 10,000 resamples, seed 42, unless stated — 2,000 for the crop classifier's calibration AP, 5,000 for its within-type AUC, and 1,000 with seed 0 for the two abstention gains. Differences are system minus comparator in percentage points (pp); positive favours the system. **Pre-registration.** The lesion detector's adoption rule — beat both the constant and the crop classifier on at least two of three cohorts, at no more than 1.5 times their rate of flagged teeth — was committed (ef3f453) before any arm was trained.

## VI. Results

### A. Training: what each model learned, on its validation split

In Figure 5 every training loss falls steadily; each checkpoint is the best on its run's validation split, so these are selection diagnostics, not test results. The tooth detector reaches validation box mAP@0.5 0.634 on 150 Tufts images at its last epoch (148), still rising slowly. Its pre-registered guard on the frozen Tufts test split required box mAP@0.5 within four points of a Tufts-only control; it reached 0.587 against 0.723 and missed, and the detector was adopted regardless, by a dated decision, for its numbering and caries behaviour. The lesion detector peaks at mAP@0.5 0.820 on the 1,200 CariesXrays validation images at epoch 29 of 54. The numbering head reaches crop-level FDI-exact 0.810 on 6,450 validation crops at epoch 12 of 15; the quadrant digit is right on 98.1% of crops and the position digit on 82.5%, so almost all numbering error is in counting along the arch. The Stage-4a flag's validation macro-F1 stays below 0.6 in all three seeds (best 0.568, 0.580, 0.597), the first sign of its weakness.

![Figure 5*](figures/R04_training.pdf)

**Figure 5.** Training logs of the four trained stages, read from the saved run files. (a) Tooth detector, 148 epochs, validation on 150 Tufts radiographs. (b) Lesion detector, 54 epochs, validation on 1,200 CariesXrays radiographs. (c) Numbering head, 15 epochs, validation on 6,450 tooth crops (DENTEX and Tufts, ground-truth boxes). (d) Stage-4a flag, three seeds of one recipe. Dots mark the checkpoint each run kept. Validation splits, not test.

On a published benchmark the detector family is competitive: trained on CariesXrays alone, the lesion detector's single-corpus arm reaches COCO AP 48.2 (AP50 84.5) on our seed-fixed 1,200-image validation split, matching the authors' task-specific method (48.2, AP50 84.1) and six points above the strongest of their ten baselines (42.2) [@chen2024cariesxrays]. The splits differ and ours chose the checkpoint, so this is indicative only; Section VI-D shows that the checkpoint does not transfer.

### B. RQ1 on development data

**Table 4.** Tooth-level caries prediction on 164 DENTEX images (477 carious teeth), micro-averaged.

| System | Precision | Recall | F1 |
|---|---|---|---|
| Pipeline, lesion detector | 0.439 | 0.574 | 0.498 |
| Pipeline, crop classifier | 0.237 | 0.765 | 0.362 |
| Constant (never reads image) | 0.218 | 0.600 | 0.320 |
| Qwen2.5-VL-32B, zero-shot | 0.250 | 0.243 | 0.246 |
| Qwen2.5-VL-7B, zero-shot | 0.248 | 0.107 | 0.149 |
| Oracle constant (test-fitted) | 0.245 | 0.505 | 0.330 |

Both VLMs see the radiograph and score below a list that does not (Table 4): -7.32 points [-11.23, -3.42] for the 32B model and -17.04 [-21.22, -12.66] for the 7B. The crop-classifier pipeline leads the constant by +4.27 points [+1.58, +7.05] by naming 1,537 teeth to its 1,312, at barely higher precision (0.237 against 0.218), as Section III-D predicts for a classifier that leans on the prior. The lesion-detector pipeline leads by +17.80 [+13.48, +22.02] and is the only system whose precision clearly exceeds the constant's (0.439), naming 624 codes, 43.9% of them carious. Under lesion agreement the crop classifier leads the constant by +17.12 points [+12.15, +21.89], partly by volume: it flags 1,439 teeth against 988, at a lower match rate (0.267 against 0.306), and flagging every detected tooth reaches 0.998. The lesion detector flags 603 teeth at the highest match rate (0.473) and is not separable from the constant (-3.55 [-10.11, +2.64]). None of this is yet evidence of perception: the front end trained on this corpus.

### C. RQ1 on external data

On the four sites the crop-classifier pipeline and the constant are level when pooled: 0.600 against 0.591, a difference of +0.89 points [-3.86, +5.57] (Figure 6a). Per site the difference runs from -18.99 [-26.32, -11.84] at test1 to +12.32 [+5.01, +19.20] at test2 (Figure 6b), a 31-point swing within one cohort, while the constant's own agreement — each site's prior mass on the eight molars — ranges from 0.494 to 0.709. On CariesXrays the constant wins outright, 0.604 against 0.379, a difference of -22.42 points [-24.62, -20.18], and it flags 46% more teeth at the higher match rate (0.200 against 0.188), so volume does not explain it. The same pipeline is 17 points above the constant, level with it, or 22 below, leading only where its detector trained.

![Figure 6](figures/R07_paired_differences.pdf)

**Figure 6.** Lesion agreement of each Stage-3a option minus the constant, paired 95% cluster-bootstrap intervals (10,000 resamples). (a) Per cohort; DENTEX is development data for the front end and CariesXrays is the lesion detector's validation split. (b) The four Ningxia sites, the pooled difference with sites fixed, and the DerSimonian–Laird random-effects mean for the lesion detector (diamond) with its 95% interval (bar) and its prediction interval for a new site (dotted, beyond the axis).

### D. RQ2: localising lesions instead of classifying teeth

Five direct repairs of the crop classifier came first (Table 5), each against a same-day control under a rule fixed in advance; none separated from zero, including a retrain with 2.67 times the carious crops, so the ceiling is not set by supervision. Section III-D locates it in the task as posed — a tight crop, a binary label and a strong prior.

![Figure 7*0.88](figures/R03_outcomes.pdf)

**Figure 7.** Pipeline output against the expert on three held-out DENTEX radiographs; left the lesion detector, right the constant placed by the same front end. (a) test_120: all seven lesions found; 33 and 34 are also flagged with no annotated lesion. The constant, without reading the image, covers four of the seven. (b) test_0 (Figure 4): two of three found; the lesion on 48 is missed. (c) test_110: none of four found — lesions on 32, 33, 34 and 46 are missed while 16, 24, 26, 36 and 37 are flagged. A flagged tooth without an annotated lesion is not a confirmed false positive, since the annotation's exhaustiveness is not documented. Radiographs: DENTEX [@hamamci2023dentex], CC BY-NC-SA 4.0.

**Table 5.** Repairs of the crop classifier on the same 863 held-out crops (34 radiographs): paired difference in AP against the control (in F1 for the thresholds).

| Repair | Difference [95% CI] |
|---|---|
| Contrast equalisation (CLAHE) | +0.049 [-0.003, +0.099] |
| Crop expanded 1.25 times | +0.020 [-0.037, +0.081] |
| Position-balanced sampling | +0.043 [-0.033, +0.116] |
| Retrain, 2.67 times the positives | -0.002 [-0.089, +0.082] |
| Per-tooth-type thresholds (F1) | +0.006 [-0.034, +0.041] |

We then changed the task. Under the tooth detector of the time, the lesion detector met the pre-registered rule on two cohorts of three: +12.2 points [+10.1, +14.3] over the constant on CariesXrays and +10.2 [+6.3, +14.0] on Ningxia, with a tie on DENTEX (-3.3 [-8.4, +1.3]). Table 6 gives the three arms under the current detector.

**Table 6.** Lesion agreement of the three Stage-3a options under the current tooth detector: crop classifier (Clf.), constant (Const.) and lesion detector (Det.); last column, detector minus constant in points, paired 95% CI. CariesXrays is the detector's validation split.

| Cohort | Clf. | Const. | Det. | Det. minus const. |
|---|---|---|---|---|
| DENTEX | 0.802 | 0.630 | 0.595 | -3.55 [-10.11, +2.64] |
| CariesXrays | 0.379 | 0.604 | 0.757 | +15.38 [+12.96, +17.73] |
| Ningxia | 0.600 | 0.591 | 0.684 | +9.28 [+4.72, +13.73] |

Both predictions of Section III-E hold. The lead comes with fewer flags: the lesion detector flags 4.35 teeth per image against the constant's 7.15 on Ningxia, and 2.16 against 7.05 on CariesXrays. And within each tooth type its flags are carious more often: on DENTEX 46.3% of the molars it flags carry caries, against 28.4% for the crop classifier and 21.8% for the constant, and 39.7% of its flagged premolars against 17.0%. Per site (Figure 6b) it is separated from the constant at test2, test3 and test4 (+16.91 [+9.17, +24.62], +11.73 [+1.07, +21.34], +13.98 [+2.34, +24.34]) and not at test1 (-3.16 [-10.56, +3.97]), where the constant is strongest. Treating the sites as a sample (random effects, post hoc) gives +9.61 [-0.54, +19.76] with $I^2 = 81\%$ and a prediction interval of [-36.08, +55.29]: the lead holds at three of these four sites and is not shown for an unseen one. The training mixture, not the architecture, transfers: the single-corpus arm of Section VI-A reached 0.694 [0.674, 0.714] on CariesXrays and collapsed to 0.086 [0.055, 0.119] on DENTEX and 0.240 [0.209, 0.272] on Ningxia. On DENTEX agreement the crop classifier leads the lesion detector (0.802 against 0.595) by flagging 1,439 teeth to its 603; FDI-set F1, which charges for false positives, reverses the order.

Figure 7 shows what these numbers look like on images. Rows were chosen by a rule fixed before rendering: the scored image with the most lesions all found, a typical image, and the image with the most lesions none found.

![Figure 8*](figures/R08_numbering_reliability.pdf)

**Figure 8.** Outputs a constant cannot produce. (a) Outcome of the numbering stage for each of 936 ground-truth DENTEX teeth (log scale). (b) Share of detected teeth given a wrong code, by position. (c) Accuracy on the items answered as the least-confident are declined: numbering, from the saved per-tooth confidences (circle: the 0.30 threshold fixed in code); crop classifier, its saved operating points at 50, 75, 90 and 100% coverage. (d) Reliability of the crop classifier's raw confidence on 863 held-out crops, binned by stated probability (marker area proportional to the bin's count).

### E. RQ3: outputs a constant cannot produce

**Numbering** (Figure 8, panels a and b). End-to-end FDI-exact accuracy on DENTEX is 92.8% (869 of 936 teeth) [90.6, 94.9], an in-domain figure; 4 teeth are never detected and 93.2% of the 932 found are numbered correctly. Of 63 wrong codes, 51 (81.0%) name an adjacent tooth in the correct quadrant — 29 one step towards the midline, 22 one step away — and only 6 of 932 detected teeth (0.6%) get a quadrant-level error. Errors concentrate where adjacent teeth look alike: 11.3% of detected lateral incisors (position 2) and 10.1% of central incisors receive a wrong code, against 4.1% of second premolars. Off-domain the identity factors of Table 1 dominate.

**Selective prediction** [@geifman2017selective] (Figure 8c). Declining the least-confident quarter raises numbering accuracy from 0.932 to 0.980 (+4.76 points [+3.29, +6.54], 164 image clusters) and the crop classifier's from 0.797 to 0.940 (+14.25 [+11.32, +16.63], 34 clusters). With confidences shuffled across items both gains collapse, to -0.06 and +0.00 points, so the gain comes from the confidence ranking and not from discarding items. The 0.30 threshold fixed in code lands at 96.1% coverage and 0.941 accuracy; because coverage counts detected teeth, retaining 75% of detections is 74.7% of the teeth present.

**Calibration** (Figure 8d), measured on the crop classifier because the lesion detector emits detection scores rather than per-tooth probabilities. The classifier is overconfident: at a stated confidence of 0.85 the observed share carious is 0.26, and its expected calibration error (ECE) [@naeini2015obtaining,guo2017calibration] is 0.136. Temperature scaling made it worse (0.152); isotonic regression reduced it to 0.043 at a cost — AP falls from 0.550 to 0.500, and at the threshold 155 of 863 verdicts would change — so it adjusts the reported confidence only. AP 0.550 [0.445, 0.660] against a prevalence of 0.147 shows a model that ranks teeth well and fails at calibration and operating point.

### F. Vision-language model controls

Qwen2.5-VL-7B answers 26,36 to a blank grey image, to random noise and to a real radiograph. Qwen2.5-VL-32B answers NONE to the blank image but, to noise, 16, 17, 26, 27, 36, 37, 46, 47 — exactly the constant's set. Few-shot prompting lowers the 7B model's F1 from 0.149 to 0.066 (two shots) and 0.034 (four) by abstaining. For these models under this prompt, the outputs are not perception.

### G. Stage 4, measured held out

The first Stage-4 model's 0.923 macro-F1 came from a crop-level split in which every validation radiograph also supplied training crops; on 125 radiographs it had not trained on it found 3.4% of labelled teeth (6 of 175). Retrained with a radiograph-level split, three runs found 27.5%, 16.5% and 11.0% (50, 30 and 20 of 182) on 143 held-out radiographs at 95.9–98.6% specificity; the severity head (macro-F1 0.294 [0.214, 0.385] against 0.334 for an image-blind position prior) stays withheld. We make no periodontal claim.

## VII. Discussion

Table 7 sets each prediction of Section III beside the evidence: five hold, the last only at three of four sites. One is not supported — the prior inflates the classifier's thresholded scores, but its ranking within a tooth type carries real image signal.

**Table 7*.** Predictions of the theory (Section III) against the evidence.

| Prediction | Evidence | Verdict |
|---|---|---|
| A constant's F1 is fixed by the prior, and rule (3) selects it | rule reproduces the fitted eight molars exactly; recall 0.600 equals the share of carious teeth at those codes | holds |
| The floor moves with the cohort | constant's agreement 0.494–0.709 across four sites of one cohort | holds |
| A positional shortcut shows as base-rate tracking on healthy teeth | mean score on healthy teeth 0.075 (incisors) to 0.478 (molars); 48.2% of healthy molars flagged | holds |
| The shortcut carries the classifier's ranking | within-type AUC 0.745 [0.660, 0.842]; position-balanced training AP +0.043 [-0.033, +0.116] | not supported |
| Development agreement does not predict external agreement | crop classifier minus constant: +17.12 (DENTEX), +0.89 (Ningxia), -22.42 (CariesXrays) | holds |
| Localisation leads with fewer flags, and its flags are carious more often per type | +9.28 on Ningxia at 4.35 flags per image against 7.15; flagged molars 46.3% carious against 28.4% | holds at three of four sites |

**RQ1.** The same metric moves 40 points across cohorts and 31 across one cohort's sites, so a favourable tooth-level figure on development data is weak evidence of perception; Figures 1 and 7 show why, the constant's molars covering many of the expert's lesions without reading a pixel. **RQ2.** A detector that must place lesion boxes cannot score by reproducing a prior, and it led the constant on the external sites with fewer, more often correct flags. That lead is conditioned on Ningxia having informed its adoption, the change of task is confounded with new training data, and the site-level interval includes zero. The theory does not explain test1, where the constant is strongest; we report it unexplained. **RQ3.** Numbering, calibration and shuffle-controlled abstention are outputs a constant cannot attempt; they show confidence that ranks the system's own errors. **What to report.** A tooth-level caries score should travel with an image-blind row fitted off the test set, the identity factors of Table 1, per-site external results with paired intervals, and images of what the system does (Figures 4, 5 and 7), as a complement to the reporting checklists for medical-imaging and dental AI [@mongan2020claim,schwendicke2021checklist].

## VIII. Limitations

- DENTEX results are in-domain for the tooth detector, which missed its pre-registered Tufts guard (0.587 against 0.723). Only Ningxia is external to the lesion detector, it informed the adoption, and the random-effects interval includes zero.
- The theory treats codes independently and is checked on one corpus's prior (78 and 164 images); the shortcut test rests on 34 radiographs; the lesion detector has no calibration curve of its own.
- Agreement has no negative class and the external cohorts no healthy controls; every model but Stage 4a is a single run; no clinician comparison was made.

## IX. Conclusion

A tooth-level caries score mixes what a system sees with where caries usually is. We derived the image-blind part in closed form — the eight first and second molars — and found a complete pipeline above, level with and below it on three cohorts, its crop classifier showing the predicted shortcut signature, while a lesion detector led it on four external sites with fewer flags. An image-blind row, the identity factors, per-site external results and visible evidence should accompany any tooth-level score.

## Acknowledgment

[ASK AUTHOR: confirm wording] Drafted with the Research Communication Engine and the Claude Opus 5.5 model from the project's saved artifacts, under the authors' direction; the authors are responsible for its content.

## References
