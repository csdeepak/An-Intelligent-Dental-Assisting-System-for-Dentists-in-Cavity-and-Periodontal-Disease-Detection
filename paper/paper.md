# What a Tooth-Level Caries Score Cannot Tell You: Positional Priors, Image-Blind Baselines and External Validation in Panoramic Dental Screening

[ASK AUTHOR: author names, affiliations and e-mail addresses]

## Abstract

Systems that find dental caries on panoramic radiographs are scored by which teeth they mark as carious. We show, in theory and on three cohorts, that this score mixes the pixels of the tooth with a prior over where caries usually occurs. We derive the F1 of a list that never reads the image in closed form: the best list holds exactly the teeth whose caries prevalence exceeds half its F1, and from 78 held-out radiographs the rule recovers the eight first and second molars, which score F1 0.320 on our 164 scored images. Against that constant we scored a six-stage pipeline (tooth detection, FDI numbering, caries, an abnormality flag and a per-tooth report) and two vision-language models, both of which scored below it. The pipeline's per-crop caries classifier led the constant by 4.27 F1 points on development data, but its scores on healthy teeth tracked each position's base rate, and on 337 radiographs from four external sites it was level with the constant. A whole-image lesion detector, adopted under a rule written before training, led the constant there by 9.28 points [+4.72, +13.73] while flagging fewer teeth, at three of the four sites. On these cohorts a tooth-level score alone could not show that a system reads the radiograph; an image-blind row, per-site external results and outputs a prior cannot produce should accompany it.

**Index Terms**: panoramic radiography, dental caries, object detection, shortcut learning, image-blind baselines, external validation, calibration, selective prediction

## I. Introduction

A panoramic dental radiograph (orthopantomogram, OPG) is a single X-ray of both jaws, unrolled into one wide image (Figure 1). Two conventions make it unfamiliar to a computer-vision reader. It is displayed as if the viewer faces the patient, so the patient's right side is on the image's left. And teeth are named in the two-digit notation of the FDI (Fédération Dentaire Internationale): the first digit is the quadrant (1 upper right, 2 upper left, 3 lower left, 4 lower right, in the patient's frame) and the second the position counted from the midline (1 central incisor to 8 third molar). Tooth 16 is therefore the upper-right first molar and 36 the lower-left one. Caries dissolves mineral, so a lesion appears as a darker (radiolucent) region inside the bright tooth; fillings and crowns are the brightest objects in the image.

![Figure 1](figures/R01_opg_primer.pdf)

**Figure 1.** Reading an OPG. One held-out DENTEX radiograph (test_120) cropped to the teeth. Dotted lines separate the quadrants Q1–Q4; numbers are the FDI codes our numbering stage assigned. Yellow: the expert's seven caries annotations as released, on teeth 12, 16, 28, 35, 36, 37 and 46. Dashed: the eight-molar set {16, 17, 26, 27, 36, 37, 46, 47} named by an image-blind constant (Section III-B); seven of its codes are present here, and four of the seven lesions lie on them. Radiographs: DENTEX [@hamamci2023dentex], CC BY-NC-SA 4.0.

**A theory of the tooth-level score.** Consider what an automated report asks of such an image. For every tooth it must decide three things in sequence: that a tooth is there, which tooth it is, and whether it carries a finding. The decisions compose, so an entry is right only when all three are, and an early error cannot be repaired later: a lesion correctly recognised but attached to the wrong tooth number is a wrong report. A score that summarises only the last decision is silent about the two that condition it.

The last decision itself draws on two sources of evidence: the pixels of the tooth, and the tooth's identity. Caries is not spread evenly over the mouth; in our data the first and second molars carry most of it (Figure 2). A learner trained to minimise error over a population will use any cue that predicts the label, and position predicts it, so a model can earn part of its score by knowing where caries usually is rather than seeing where it is in this image — a shortcut [@geirhos2020shortcut]. The usual metric cannot tell the two apart, because a set of tooth codes can be chosen without any image; Section III derives the best such set from the prevalence of caries at each position.

Two consequences organise this paper. First, a reported score has a floor set by the prior, so it means little until an image-blind constant is scored beside it. Second, the floor moves with the population: a constant's lesion agreement is the share of a cohort's lesions that lie on its teeth, and a model that has absorbed the prior moves with it, whereas a model that reads the lesion need not. Agreement on one development cohort therefore cannot separate the two explanations; agreement on external cohorts, paired with the constant and reported per site, can. The theory also says what a fixed list cannot do — place a lesion in the image, name the tooth, state a calibrated confidence, decline to answer — and those outputs are where evidence of perception has to come from. Input-blind baselines of this kind are established in visual question answering and language inference (Section II); our contribution is to bring the floor to tooth-level caries scoring, give it a closed form, and measure it across cohorts and sites.

We examine these consequences on a complete system. RQ1: does tooth-level agreement separate a full pipeline from an image-blind constant, on development data and on external cohorts? RQ2: does reformulating the caries stage from classifying tooth crops to localising lesions in the whole image — a task a fixed list cannot perform — separate them? RQ3: what does the pipeline show on outputs a fixed list cannot produce? The contributions are:

1. A short theory of tooth-level caries scoring — the error chain of a tooth-indexed report, the closed-form F1 of an image-blind constant and its selection rule, the cohort dependence of lesion agreement, and a testable signature of a positional shortcut — each checked against our data.
2. A constant-baseline protocol: two metric families, three cohorts, four external sites, paired cluster-bootstrap intervals.
3. A pre-registered reformulation of the caries stage as lesion detection, which led the constant on the pooled external sites while flagging fewer teeth.
4. The evidence: every stage on a real radiograph, training curves, rule-chosen successes and failures, and content-free controls for two vision-language models.

## II. Related Work

**Datasets.** We use the Tufts Dental Database of 1,000 OPGs with expert tooth and abnormality annotations [@panetta2022tufts], DENTEX, with hierarchical quadrant, enumeration and diagnosis labels [@hamamci2023dentex], the CariesXrays lesion benchmark of 6,000 OPGs [@chen2024cariesxrays], the multi-centre dataset of Li et al., collected at three hospitals in Ningxia and Shenzhen [@li2024multicenter], and UFBA-425 [@budagam2024oralbbnet]. **Detection, numbering and caries.** A systematic review of deep-learning caries detection found accuracies of 86.1–96.1% on panoramic radiographs, in studies whose quality and reporting it judged low [@mohammadrahimi2022deep]. Caries and periodontal analysis has used dual networks [@lim2024dual], dedicated convolutional classifiers [@bilal2024pdcnet] and contrastive feature pyramids [@chen2024cariesxrays]. Numbering is reported at very high figures — class-averaged accuracy 0.9988 (F1 0.979) in one system [@zancan2025ai] — and a multi-stage system outperforms prior methods on Tufts and two other datasets [@zhang2025reliable]; classifying a cropped tooth is easier than numbering under detector output, where teeth can be missed or duplicated. **Transfer.** Of 516 medical-imaging AI studies published January–August 2018, only 31 (6%) validated externally [@kim2019design]. Dental models tested elsewhere degrade: an apical-lesion model fell from F1 54.1% to 32.7% at a second centre [@krois2021generalizability]; a YOLOv11 detector of 13 conditions fell from mAP@0.5 0.857 to 0.806 on external images, weakest on subtle pathology such as caries [@mutlu2026comparison]. One enumeration-then-caries detector held lesion sensitivity at 0.70 internally and 0.67 externally [@bizjak2024advancing].

**Shortcuts and input-blind baselines.** Shortcut learning predicts that a model will exploit any cue correlated with the label [@geirhos2020shortcut], and other fields test for it with baselines that withhold the input the task is about. Visual-question-answering models answered from language priors while ignoring the image, inflating their apparent capability [@goyal2017making], and lost accuracy when answer priors differed between training and test [@agrawal2018dont]; in natural-language inference, a model that never sees the premise beats the majority class on many datasets [@poliak2018hypothesis]. In medical imaging, COVID-19 detectors relied on confounders and failed at new hospitals [@degrave2021ai], and in a pneumonia task sorting radiographs by hospital alone reached AUC 0.861 because prevalence differed between sites [@zech2018variable]. In the 49 task-relevant papers of our own survey of OPG analysis we noticed none that reports an image-blind baseline (an observation, not a systematic count). **Calibration, abstention and VLMs.** Temperature scaling [@guo2017calibration] and isotonic regression [@zadrozny2002isotonic] are our calibration comparators, and abstention follows selective classification [@geifman2017selective]. Vision-language models (VLMs) are being adapted to dental diagnosis [@meng2026dentvlm]; we use Qwen2.5-VL [@bai2025qwen25vl] as general comparators that need no task training.

## III. Theory: What a Tooth-Level Score Measures

### A. The report as a chain of decisions

The report's entry for a tooth is correct only if the tooth is detected ($D$), numbered correctly once detected ($N$), and given the right finding ($F$):

$$
P(\text{entry correct}) = P(D)\, P(N \mid D)\, P(F \mid D, N).
$$

The first two factors concern identity, not disease, and bound everything after them: a perfect caries model still writes a wrong report on every tooth that was missed or misnumbered. A metric that matches findings to teeth by code (FDI-set F1, Section III-B) charges for both; one that matches lesions by position in the image (lesion agreement, Section III-C) is blind to the second. Table 1 measures our pipeline's identity factors and where the losses fall. On DENTEX, whose other images trained the detector, identity costs 7.2 points; on the Tufts test split, also from a training corpus, 36.5; on UFBA-425, which no model trained on, 55.5 points as the files are distributed.

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

Equation (2) counts every named code as a prediction, present tooth or not, as the scorer does, and applies to any set prediction scored by micro-F1 over a fixed label set. Nothing in it depends on an image, and the constant's recall, $\sum_{c \in S} n_c / P$, is the share of carious teeth that lie at its codes. Writing $A = \sum_{c \in S} n_c$ and $k = |S|$, adding a code $c \notin S$ raises the score, $2(A+n_c)/((k+1)N+P) > 2A/(kN+P)$, if and only if

$$
p_c > \tfrac{1}{2}\, F_1(S).
$$

For any fixed size the best set is the $k$ most prevalent codes, so the F1-optimal constant is a prefix of the codes sorted by prevalence. Writing $S_k$ for the $k$ most prevalent codes, F1 rises along $S_1, S_2, \dots$ to a single peak: if code $k+1$ fails (3) against $S_k$, then $p_{k+1} \le \tfrac{1}{2}F_1(S_{k+1})$ as well, so every later, less prevalent code fails too. The optimum is therefore the prefix cut where (3) first fails, and it holds exactly the codes with $p_c > \tfrac{1}{2}F_1^{*}$: a functional of the caries prior alone. That first molars are the most caries-susceptible teeth is long established in caries epidemiology [@batchelor2004grouping]; the prior, and with it the floor, depends on the population's age and exposure.

![Figure 2*0.92](figures/R05_positional_prior.pdf)

**Figure 2.** The positional prior and the constant it implies. (a) Share of images in which the expert marked each FDI code carious, in chart order (patient's right to left, as displayed): grey, the fit set (78 DENTEX images with caries, excluded from scoring because our models trained on them); orange, the 164 scored images. Magenta: the eight codes rule (3) admits; dashed: the final threshold $F_1/2 = 0.196$. (b) F1 of the $k$ most prevalent fit-set codes. Computed with the evaluation's loaders; the script asserts the saved scores.

On the fit set (Figure 2) rule (3) admits the eight first and second molars, with prevalences from 0.372 (tooth 26) to 0.205 (tooth 27), and rejects the ninth code, tooth 15, at 0.128 against a threshold of 0.196 — exactly the set the evaluation's greedy search returns. Frozen, {16, 17, 26, 27, 36, 37, 46, 47} scores F1 0.392 on its fit images and 0.320 on the 164 scored ones — 286 true positives among 1,312 named codes, against 477 carious teeth, so its recall is 0.600, the share of carious teeth that lie on those eight molars. The prior shifts between the two sets: teeth 17 and 27 fall to 0.140 and 0.134 on the scored images, so the oracle constant fitted on the scored images themselves keeps six molars and reaches only 0.330. Almost all of the image-blind score therefore needs no evaluation data. The set is fragile at its margin and the floor is not: refitted on 10,000 resamples of the fit images, rule (3) returns exactly these eight molars 27% of the time and seven codes 45%, yet the refitted constants score a median F1 of 0.320 on the scored images, 95% of them between 0.279 and 0.330; over sizes one to sixteen the constant's F1 is flat from six to nine codes (0.298–0.325).

### C. Lesion agreement and the cohort's prior

The second metric family scores lesions rather than codes. Let a cohort contain $L$ expert lesions, let $T(\ell)$ be the detected tooth that contains lesion $\ell$, and let $\mathcal{F}$ be the set of teeth a system flags. Lesion agreement is

$$
A(\mathcal{F}) = \frac{1}{L} \sum_{\ell} \mathbf{1}\big[\, T(\ell) \in \mathcal{F} \,\big].
$$

$A$ has no negative class. It can only rise as $\mathcal{F}$ grows, and flagging every detected tooth reaches its ceiling, the share of lesions inside any detected tooth (0.998 on DENTEX); it must be read beside the number of teeth flagged. For the constant, $\mathcal{F}$ is the eight molar boxes our front end finds, so $A$ is the cohort's prior mass on those molars. Placement is reliable: on Tufts, 92.0% [89.58, 94.06] of the boxes our pipeline codes as one of the eight molars are true first or second molars. This prior mass is the cohort's, as placed by our front end — 0.630 on DENTEX, 0.604 on CariesXrays, 0.591 on the four Ningxia sites, and from 0.494 to 0.709 between sites of that one cohort (Section VI) — the site effect Zech et al. found for pneumonia [@zech2018variable]. A system that has absorbed the prior inherits this variation, so systems can be compared only when paired on the same images, cohort by cohort and site by site.

### D. A testable signature of a positional shortcut

If a per-tooth classifier has learned the probability of caries given position, and not only given pixels, two consequences follow. Its score on teeth that are truly healthy should rise with the base rate of their position, because the prior lifts every tooth of a caries-prone type. And its ranking should survive only partly when position is held fixed: the within-type area under the ROC curve (AUC), which ranks carious against healthy teeth of the same type, removes the positional cue and keeps the image signal. Table 2 applies both tests to the pipeline's crop classifier on 863 held-out tooth crops from 34 radiographs, cut with ground-truth boxes so that the front end plays no part.

**Table 2*.** The positional-shortcut test on the crop classifier: 863 held-out crops from 34 radiographs. Base rate: share carious in its training data. Within-type AUC interval: cluster bootstrap over the 34 radiographs, 5,000 resamples.

| Tooth type | Crops | Carious | Base rate | Mean score, healthy | Healthy flagged | Within-type AUC |
|---|---|---|---|---|---|---|
| Incisor | 266 | 8 | 0.017 | 0.075 | 0.039 | 0.681 |
| Canine | 129 | 5 | 0.023 | 0.087 | 0.016 | 0.748 |
| Premolar | 221 | 31 | 0.157 | 0.273 | 0.268 | 0.781 |
| Molar | 247 | 83 | 0.343 | 0.478 | 0.482 | 0.781 |
| All, within type | 863 | 127 | — | — | — | 0.745 [0.660, 0.842] |

The classifier's mean score on healthy teeth climbs with the training base rate, from 0.075 on incisors to 0.478 on molars, and it flags 48.2% of healthy molars: the prior is doing visible work, and costs precision. Its within-type AUC is 0.745 [0.660, 0.842], above 0.5, so there is also genuine lesion signal. A predictor that uses position alone and never sees an image reaches average precision (AP) 0.296, against the classifier's 0.550 and chance at 0.147. It is neither a lookup table nor a pure reader, but a reader whose score is inflated by a prior the constant captures for free.

### E. Why localisation resists the shortcut

A whole-image lesion detector receives no tooth identity: to flag a tooth it must place a box mostly inside it. It can express a positional prior only by drawing boxes over molars where it sees no lesion, and each such box is charged as a false positive under (2) and earns agreement under (4) only if a lesion happens to lie there. The theory therefore implies that if the detector's lead over the constant comes from reading the image, it should come with fewer flagged teeth, not more, and within each tooth type its flags should be carious more often than the classifier's.

### F. Inference over images and sites

Teeth within one radiograph share exposure, anatomy and annotator, so their errors are correlated; we resample images, not teeth, the cluster bootstrap that stays consistent when clusters carry random effects [@field2007bootstrapping]. For two systems scored on the same images, the paired difference is recomputed on each bootstrap resample of images, and its 2.5th and 97.5th percentiles give the interval. Across sites, per-site differences $\Delta_j$ with variances $v_j$ (from each site's interval width) are pooled by DerSimonian–Laird random effects [@dersimonian1986meta],

$$
\hat\mu = \frac{\sum_j \Delta_j / (v_j + \hat\tau^2)}{\sum_j 1 / (v_j + \hat\tau^2)},
$$

where the between-site variance $\hat\tau^2$ is estimated from Cochran's $Q$, and $I^2 = (Q - k + 1)/Q$ is the share of variation due to sites [@higgins2002quantifying]. A fixed-site interval asks whether a system led at these sites; the random-effects prediction interval asks whether it would lead at another [@riley2011interpretation]. With four sites the DL interval is too narrow, so we also report the Hartung–Knapp–Sidik–Jonkman (HKSJ) interval [@inthout2014hartung] and a Q-profile interval for $\tau$ [@viechtbauer2007confidence].

## IV. System

The pipeline maps an OPG to a per-tooth record in six stages (Figure 3); Figure 4 follows one held-out radiograph through every stage.

![Figure 3*0.92](figures/R06_architecture.pdf)

**Figure 3.** The pipeline as it ships, with its default checkpoints and learnable parameter counts read from the saved weights; the default configuration (Stages 1, 2, default 3a, 3b, 4a and the withheld 4b, 11.18 M) totals 95.34 M. Blue: identity stages; dark blue: the default caries path; dashed orange: the retained caries variant, the comparison arm throughout; green: the abnormality flag. Thresholds are fixed in code; none was tuned on an evaluation cohort.

**Stage 1** is a YOLOv11l detector [@jocher2024yolo11]. **Stage 2** scores every FDI code for each tooth crop with a ResNet18 [@he2016resnet] and four box-position features, and the Hungarian algorithm [@kuhn1955hungarian] makes the assignment one-to-one. **Stage 3a** is by default a whole-image YOLOv11l lesion detector (9,600 samples per epoch, from 4,800 CariesXrays and 650 replicated DENTEX images) whose boxes go to the tooth containing most of each; the retained variant classifies each tight tooth crop. **Stage 3b** grades flagged teeth as caries or deep caries, the two caries labels DENTEX releases; it was validated on 133 crops in development and is not evaluated here. **Stage 4** flags a tooth crop that overlaps an abnormality the Tufts expert marked (apical lesions, sclerosis, cysts); it was built for periodontal bone loss, and we name it for its label. **Stages 5–6** fuse the outputs on the FDI code into the report, the system's only output; the whole system runs at 1.70 s per image on a laptop CPU with no GPU [ASK AUTHOR: CPU model]. For tooth 36 of Figure 4 the record holds the code (confidence 0.9999), detection confidence 0.8389, a deep-caries finding (caries confidence 0.8892, severity 0.9579), a normal Stage-4 finding (0.7853) and an assessability flag.

![Figure 4*0.80](figures/R02_walkthrough.pdf)

**Figure 4.** One held-out DENTEX radiograph (test_0, not used to train any model) through the shipped pipeline. (a) Input, 2,829 by 1,316 pixels; dashed: the region in (b)–(f). (b) Stage 1: 30 teeth, with detection confidences. (c) Stage 2: one FDI code per tooth; "?" marks its two unsure codes (24, 42). (d) Stage 3a: one lesion-detector pass over the whole image, four boxes (confidence 0.35 to 0.89). (e) Each box goes to the tooth holding most of it: 26 and 46 flagged as caries, 36 and 45 as deep caries; no Stage-4 flag. (f) The written overlay with the expert's three caries annotations (26, 45, 48) in yellow: two found, 48 missed, 36 flagged with no annotated lesion. Radiographs: DENTEX [@hamamci2023dentex], CC BY-NC-SA 4.0.

## V. Data and Evaluation Protocol

**Cohorts** (Table 3). All splits are image-level. DENTEX's disease subset has 250 annotated OPGs; MD5 hashing found 86 byte-identical to images our models trained on (85 in numbering, 1 in detection), leaving 164 scored, of which 148 carry a caries lesion (479 lesions on 477 teeth). A perceptual-hash search (pHash, dHash) of the 1,389 other DENTEX images found no further copy: the 86 lie at distance 0, and the 20 scored images nearest to them differ in restorations or missing teeth. Ningxia is the public release of the dataset of Li et al. [@li2024multicenter]: their paper describes three hospitals, and the release divides its test data into four sets — test2 from its training centre, test1, test3 and test4 described as cross-centre — which we treat as four sites.

**Table 3.** Evaluation cohorts, units and exposure. Each row is an analysis population; counts must not be summed across rows.

| Cohort | Images | Unit (n) | Role and exposure |
|---|---|---|---|
| DENTEX disease | 164 | 936 teeth; 477 carious; 479 lesions | development; detector trained on other DENTEX images |
| Ningxia, 4 sites | 337 | 1,013 lesions | external; never trained on; informed the lesion detector's adoption |
| CariesXrays | 1,200 | 2,815 lesions | external, except to the lesion detector (its validation split) |
| Tufts test | 143 | 3,760 / 3,892 teeth | numbering / Stage 4 (182 labelled); both trained on Tufts train |
| UFBA-425 | 425 | 11,591 teeth | numbering; no model trained on it |

**The ladder.** Four systems answer one question — which teeth in this radiograph show caries? — on the same 164 images: the pipeline (with each Stage-3a implementation), Qwen2.5-VL-32B (33.45 B parameters) and Qwen2.5-VL-7B (8.29 B), both zero-shot with the FDI scheme in the prompt (and shown a blank grey and a random-noise image as content-free controls), and the constant of Section III-B.

**Metrics.** FDI-set F1 (2) is micro-averaged over teeth. Lesion agreement (4) matches each expert lesion to a flagged tooth: on DENTEX by greedy intersection over union (IoU) of at least 0.30 with a centroid fallback, on the external cohorts by centroid containment, because their lesions are small (median 731 pixels) inside tooth boxes of about 25,000 pixels; every comparison is therefore within a cohort.

**Statistics.** Intervals are 95% percentile cluster bootstraps over images (Section III-F): 10,000 resamples, seed 42, unless stated — 2,000 for the crop classifier's calibration AP, 5,000 for its within-type AUC, and 1,000 with seed 0 for the two abstention gains. Differences are system minus comparator in percentage points (pp); positive favours the system. We report estimates with intervals, not a family of tests: no multiplicity correction is applied across cohorts, arms, metrics and sites, and the Ningxia lead, measured on a cohort that informed the adoption, is optimistic by construction. **Pre-registration.** The lesion detector's adoption rule — beat both the constant and the crop classifier on at least two of three cohorts, at no more than 1.5 times their rate of flagged teeth — was committed (ef3f453) before any arm was trained.

## VI. Results

### A. Training: what each model learned, on its validation split

Every training loss in Figure 5 falls steadily. Each checkpoint is the best on its run's validation split, so these are selection diagnostics, not test results, and each is a single run (three seeds for Stage 4a). The tooth detector reaches validation box mean average precision at IoU 0.5 (mAP@0.5) 0.634 at its last epoch, still rising; on the frozen Tufts test split it missed its pre-registered guard (within four points of a Tufts-only control: 0.587 against 0.723) and was adopted regardless, by a dated decision, for its numbering and caries behaviour. The lesion detector peaks at mAP@0.5 0.820 (epoch 29 of 54). The numbering head reaches crop-level FDI-exact 0.810 (epoch 12 of 15), with the quadrant digit right on 98.1% and the position digit on 82.5%: its errors are counting errors along the arch. Stage 4a's validation macro-F1 stays below 0.6 in all three seeds (best 0.568, 0.580, 0.597).

![Figure 5*0.86](figures/R04_training.pdf)

**Figure 5.** Training logs of the four trained stages, from the saved run files; validation splits, not test. (a) Tooth detector, 148 epochs, 150 Tufts radiographs. (b) Lesion detector, 54 epochs, 1,200 CariesXrays radiographs. (c) Numbering head, 15 epochs, 6,450 tooth crops (DENTEX and Tufts, ground-truth boxes). (d) Stage-4a flag, three seeds of one recipe. Dots: the checkpoint each run kept.

On a published benchmark the detector family is competitive: trained on CariesXrays alone, the lesion detector's single-corpus arm reaches COCO AP 48.2 (AP50 84.5) on our seed-fixed 1,200-image validation split, matching the authors' task-specific method (48.2, AP50 84.1) and six points above the strongest of their ten baselines (42.2) [@chen2024cariesxrays]. The splits differ and ours chose the checkpoint, so this is indicative only; Section VI-D shows that the checkpoint does not transfer.

### B. RQ1 on development data

**Table 4.** Tooth-level caries prediction on 164 DENTEX images (477 carious teeth), micro-averaged. P: precision; R: recall; Matched: F1 minus that of a constant naming as many codes (pp).

| System | P | R | F1 | Matched |
|---|---|---|---|---|
| Pipeline, lesion detector | 0.439 | 0.574 | 0.498 | +22.35 |
| Pipeline, crop classifier | 0.237 | 0.765 | 0.362 | +5.50 |
| Constant (image-blind) | 0.218 | 0.600 | 0.320 | — |
| Qwen2.5-VL-32B, 0-shot | 0.250 | 0.243 | 0.246 | +0.39 |
| Qwen2.5-VL-7B, 0-shot | 0.248 | 0.107 | 0.149 | +1.39 |
| Oracle constant (test-fit) | 0.245 | 0.505 | 0.330 | — |

Both VLMs see the radiograph and score below a list that does not (Table 4): -7.32 points [-11.23, -3.42] for the 32B model and -17.04 [-21.22, -12.66] for the 7B. The crop-classifier pipeline leads the constant by +4.27 points [+1.58, +7.05] while naming 1,537 teeth to its 1,312, at barely higher precision (0.237 against 0.218), as Section III-D implies for a classifier that leans on the prior. The lesion-detector pipeline leads by +17.80 [+13.48, +22.02] and is the only system whose precision clearly exceeds the constant's (0.439), naming 624 codes, 43.9% of them carious. Volume explains neither pipeline lead: against a matched constant, which answers the $k$ most prevalent fit-set codes on some images and $k+1$ on the rest so as to name as many codes as the system, the leads are +5.50 [+2.84, +8.22] and +22.35 [+17.42, +27.18]. The VLMs are level with constants of their own volume (32B [-4.90, +5.63], 7B [-2.06, +4.85]): they fall below the eight molars by naming fewer teeth, and their F1 carries no detectable image information. Under lesion agreement the crop classifier leads the constant by +17.12 points [+12.15, +21.89], partly by volume: it flags 1,439 teeth against 988, at a lower match rate (0.267 against 0.306). The lesion detector flags 603 teeth at the highest match rate (0.473) and is not separable from the constant (-3.55 [-10.11, +2.64]); F1 ranks it above the crop classifier, agreement below. None of this is yet evidence of perception: the front end trained on this corpus.

### C. RQ1 on external data

On the four sites the crop-classifier pipeline and the constant are level when pooled: 0.600 against 0.591, a difference of +0.89 points [-3.86, +5.57] (Figure 6a). Per site the difference runs from -18.99 [-26.32, -11.84] at test1 to +12.32 [+5.01, +19.20] at test2 (Figure 6b), a 31-point swing within one cohort, while the constant's own agreement — each site's prior mass on the eight molars — ranges from 0.494 to 0.709. On CariesXrays the constant wins outright, 0.604 against 0.379 (-22.42 points [-24.62, -20.18]), and it flags 46% more teeth at the higher match rate (0.200 against 0.188), so volume does not explain it. The pipeline leads only where its detector trained.

![Figure 6 0.88](figures/R07_paired_differences.pdf)

**Figure 6.** Lesion agreement of each Stage-3a option minus the constant, paired 95% cluster-bootstrap intervals (10,000 resamples). (a) Per cohort; DENTEX is development data for the front end and CariesXrays is the lesion detector's validation split. (b) The four Ningxia sites, the pooled difference with sites fixed, and the DerSimonian–Laird mean for the lesion detector (diamond; bar: 95% interval; dotted, beyond the axis: prediction interval for a new site).

### D. RQ2: localising lesions instead of classifying teeth

Five direct repairs of the crop classifier came first (Table 5), each against a same-day control under a rule fixed in advance; none separated from zero, including a retrain with 2.67 times the carious crops, so the ceiling is not set by supervision. Section III-D locates it in the task as posed — a tight crop, a binary label and a strong prior.

![Figure 7*0.78](figures/R03_outcomes.pdf)

**Figure 7.** Pipeline output against the expert on three held-out DENTEX radiographs: left, the lesion detector; right, the constant placed by the same front end. (a) test_120: all seven lesions found, 33 and 34 also flagged; the constant covers four of the seven without reading the image. (b) test_0 (Figure 4): two of three found, 48 missed. (c) test_110: none of four found (32, 33, 34, 46 missed; 16, 24, 26, 36, 37 flagged). A flag without an annotated lesion is not a confirmed false positive: the annotation's exhaustiveness is not documented. Radiographs: DENTEX [@hamamci2023dentex], CC BY-NC-SA 4.0.

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

Both implications of Section III-E hold. The lead comes with fewer flags: the lesion detector flags 4.35 teeth per image against the constant's 7.15 on Ningxia, and 2.16 against 7.05 on CariesXrays. And within each tooth type its flags are carious more often — on DENTEX, the development corpus, where per-type records exist: 46.3% of the molars it flags carry caries, against 28.4% for the crop classifier and 21.8% for the constant, and 39.7% of its flagged premolars against 17.0%. Per site (Figure 6b) it is separated from the constant at test2, test3 and test4 (+16.91 [+9.17, +24.62], +11.73 [+1.07, +21.34], +13.98 [+2.34, +24.34]) and not at test1 (-3.16 [-10.56, +3.97]), where the constant is strongest. Treating the sites as a sample (random effects, post hoc) gives +9.61 [-0.54, +19.76] (HKSJ [-5.02, +24.24]), $I^2 = 81\%$, $\tau$ 9.27 points [3.22, 33.09] and a prediction interval of [-36.08, +55.29]: the lead holds at three of these four sites and is not shown for an unseen one. The training mixture, not the architecture, transfers: the single-corpus arm of Section VI-A reached 0.694 [0.674, 0.714] on CariesXrays and collapsed to 0.086 [0.055, 0.119] on DENTEX and 0.240 [0.209, 0.272] on Ningxia.

Figure 7 shows these numbers on images, in rows chosen by a rule fixed before rendering: the scored image with the most lesions all found, a typical image, and the one with the most lesions none found.

![Figure 8*0.86](figures/R08_numbering_reliability.pdf)

**Figure 8.** Outputs a constant cannot produce. (a) Numbering outcome for each of 936 ground-truth DENTEX teeth (log scale). (b) Share of detected teeth given a wrong code, by position. (c) Accuracy on the items answered as the least confident are declined: numbering, from saved per-tooth confidences (circle: the 0.30 threshold fixed in code); crop classifier, saved operating points at 50, 75, 90 and 100% coverage. (d) Reliability of the crop classifier's raw confidence on 863 held-out crops, by stated probability (marker area proportional to bin count).

### E. RQ3: outputs a constant cannot produce

**Numbering** (Figure 8, panels a and b). End-to-end FDI-exact accuracy on DENTEX is 92.8% (869 of 936 teeth) [90.6, 94.9], an in-domain figure; 4 teeth are never detected and 93.2% of the 932 found are numbered correctly. Of 63 wrong codes, 51 (81.0%) name an adjacent tooth in the correct quadrant — 29 one step towards the midline, 22 one step away — and only 6 of 932 detected teeth (0.6%) get a quadrant-level error. Errors concentrate where adjacent teeth look alike: 11.3% of detected lateral incisors (position 2) and 10.1% of central incisors receive a wrong code, against 4.1% of second premolars. At molar positions, where most caries lies, 8.2% of detected second molars receive a wrong code, and each such error moves any finding to the wrong tooth: the second factor of (1).

**Selective prediction** [@geifman2017selective] (Figure 8c). Declining the least-confident quarter raises numbering accuracy from 0.932 to 0.980 (+4.76 points [+3.29, +6.54], 164 image clusters) and the crop classifier's from 0.797 to 0.940 (+14.25 [+11.32, +16.63], 34 clusters). With confidences shuffled across items both gains collapse, to -0.06 and +0.00 points, so the gain comes from the confidence ranking and not from discarding items. The 0.30 threshold fixed in code lands at 96.1% coverage and 0.941 accuracy; because coverage counts detected teeth, retaining 75% of detections is 74.7% of the teeth present.

**Calibration** (Figure 8d), measured on the crop classifier because the lesion detector emits detection scores rather than per-tooth probabilities. The classifier is overconfident: at a stated confidence of 0.85 the observed share carious is 0.26, and its expected calibration error (ECE) [@naeini2015obtaining,guo2017calibration] is 0.136. Temperature scaling made it worse (0.152); isotonic regression reduced it to 0.043 at a cost — AP falls from 0.550 to 0.500, and at the threshold 155 of 863 verdicts would change — so it adjusts the reported confidence only. AP 0.550 [0.445, 0.660] against a prevalence of 0.147 shows a model that ranks teeth well and fails at calibration and operating point.

### F. Controls outside the caries pipeline

Shown no anatomy, the VLMs return the population prior: Qwen2.5-VL-7B answers 26,36 to a blank grey image, to random noise and to a real radiograph, and Qwen2.5-VL-32B answers noise with exactly the constant's eight molars (one prompt; decoding settings not recorded). Stage 4's first model reported 0.923 macro-F1 on a crop-level split that let every validation radiograph supply training crops, and found 3.4% of labelled teeth (6 of 175) on 125 unseen radiographs; retrained with a radiograph-level split, three runs found 27.5%, 16.5% and 11.0% (50, 30 and 20 of 182) on 143 held-out radiographs at 95.9–98.6% specificity. Its severity head (macro-F1 0.294 [0.214, 0.385] against 0.334 for an image-blind position prior) stays withheld, and we make no periodontal claim.

## VII. Discussion

The theory of Section III was formulated after the measurements, so Table 7 is a consistency check, not a test of predictions made in advance. Five of its implications hold, the last only at three of four sites; one of them is also expected under ordinary domain shift and does not single out the theory. One is not supported — the prior inflates the classifier's thresholded scores, but its ranking within a tooth type carries real image signal.

**Table 7*.** What the theory of Section III implies, and what the measurements show (a post-hoc consistency check).

| Implication | Evidence | Verdict |
|---|---|---|
| Rule (3) gives the best constant | reproduces the fitted eight molars; recall 0.600 = carious share at them | holds |
| The floor moves with the cohort | constant's agreement 0.494–0.709 across four sites | holds |
| Shortcut lifts healthy scores | healthy score 0.075 (incisors) to 0.478 (molars); 48.2% of healthy molars flagged | holds |
| Shortcut carries the ranking | within-type AUC 0.745 [0.660, 0.842]; position-balanced AP +0.043 [-0.033, +0.116] | not supported |
| Agreement does not transfer | classifier minus constant +17.12, +0.89, -22.42 on the three cohorts | holds; not specific |
| Localising: fewer, better flags | Ningxia +9.28, 4.35 vs 7.15 flags/image; DENTEX molar flags 46.3% vs 28.4% carious | 3 of 4 sites |

**RQ1.** The same metric moves 40 points across cohorts and 31 across one cohort's sites, so a favourable tooth-level figure on development data is weak evidence of perception. **RQ2.** A detector that must place lesion boxes can express a positional prior only at a cost in precision (Section III-E). It led the constant on the external sites with fewer flags, and on the development corpus its flags were carious more often within each tooth type. Ningxia informed its adoption, the change of task is confounded with new training data, and the site-level interval includes zero; test1, where the constant is strongest, stays unexplained. **RQ3.** Numbering, calibration and shuffle-controlled abstention are outputs a constant cannot attempt; they show confidence that ranks the system's own errors. **What to report.** A tooth-level caries score should travel with an image-blind row fitted off the test set, the identity factors of Table 1, per-site external results with paired intervals, and images of what the system does (Figures 4, 5 and 7), complementing the reporting checklists for medical-imaging and dental AI [@mongan2020claim,schwendicke2021checklist].

## VIII. Limitations

- DENTEX is in-domain for the tooth detector, which missed its Tufts guard (0.587 against 0.723); only Ningxia is external to the lesion detector, it informed the adoption, and the random-effects interval includes zero.
- The theory treats codes independently and was checked on one corpus (78 and 164 images); the shortcut test rests on 34 radiographs; the lesion detector has no calibration curve.
- DENTEX caries labels were read from panoramic radiographs alone, which detect proximal caries less accurately than bitewings [@akarslan2008comparison]; the expert lesions are a subset of disease, and part of the molar prior may be a prior of what panoramic labels capture.
- Agreement has no negative class and the external cohorts no healthy controls; every model but Stage 4a is a single run; no clinician comparison was made; duplicate checks cannot find a patient's second radiograph.

## IX. Conclusion

A tooth-level caries score mixes what a system sees with where caries usually is. Its image-blind part has a closed form, here the eight first and second molars; our pipeline sat above, level with and below it on three cohorts, and a lesion detector led it on four pooled external sites with fewer flags. The floor differs between populations, so the score should travel with an image-blind row and per-site results.

## Acknowledgment

[ASK AUTHOR: confirm wording] Drafted with the Research Communication Engine and Claude Opus 5.5 from the project's saved artifacts; the authors are responsible for its content.

## References
