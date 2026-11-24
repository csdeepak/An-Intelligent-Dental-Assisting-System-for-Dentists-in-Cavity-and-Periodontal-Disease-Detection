# Reading the Radiograph or the Prior? A Tooth-Level Panoramic Analysis System Evaluated Against Image-Blind Baselines and External Cohorts

[ASK AUTHOR: author names, affiliations and e-mail addresses]

## Abstract

What does a dentist see on an X-ray, and what does a computer see? The panoramic radiograph, or orthopantomogram (OPG), is the most widely taken extraoral dental X-ray: one low-dose exposure shows every tooth and both jaws, and the dentist reads it by eye, tooth by tooth. That reading is hard. Early caries is a faint shadow that radiographs miss more often than they reveal, overlapping teeth and artefacts mimic lesions, and up to 32 teeth must be charted on every image. Artificial intelligence promises a second reader, but it inherits a trap first exposed in chest radiography, where a pneumonia model could profit from knowing which hospital an image came from. In teeth the trap is anatomical: caries clusters on the molars, so a model can score well by knowing where decay usually is without reading the image. Existing systems number teeth almost perfectly and report panoramic caries accuracies of 86–96%, but in studies of low quality, rarely tested at a second clinic and, in the papers we reviewed, never against a baseline that ignores the image. We built a six-stage assistant that detects, numbers and screens every tooth and writes a per-tooth report, and scored it beside such a baseline. Its crop classifier did not beat it; its whole-image lesion detector led it at four external sites by 9.28 points of lesion agreement, though not demonstrably at an unseen site. Its abnormality flag supports no periodontal claim.

**Index Terms**: panoramic radiography, dental caries, tooth numbering, decision support, shortcut learning, image-blind baselines, external validation, calibration, selective prediction

## I. Introduction

**The OPG in everyday dentistry.** A panoramic dental radiograph, or orthopantomogram (OPG), is a single X-ray of both jaws, unrolled into one wide image (Figure 1). It is the most widely taken extraoral dental radiograph: in one university department, 78% of 9,680 extraoral images taken over 18 years were OPGs, each at an effective dose of about 7 µSv. Dentists read it by eye for caries, bone levels, periapical lesions and missing or impacted teeth, charting each finding against a tooth. Two conventions make the OPG unfamiliar to a computer-vision reader. It is displayed as if the viewer faces the patient, so the patient's right side is on the image's left. And teeth are named in the two-digit notation of the FDI World Dental Federation (ISO 3950): the first digit is the quadrant (1 upper right, 2 upper left, 3 lower left, 4 lower right, in the patient's frame) and the second the position counted from the midline (1 central incisor to 8 third molar). Tooth 16 is therefore the upper-right first molar and 36 the lower-left one.

![Figure 1](figures/R01_opg_primer.pdf)

**Figure 1.** Reading an OPG. One held-out DENTEX radiograph (test_120) cropped to the teeth. Dotted lines separate the quadrants Q1–Q4; numbers are the FDI codes our numbering stage assigned. Yellow: the expert's seven caries annotations as released, on teeth 12, 16, 28, 35, 36, 37 and 46. Dashed: the eight-molar set {16, 17, 26, 27, 36, 37, 46, 47} named by an image-blind constant (Section III-B); seven of its codes are present here, and four of the seven annotated teeth are among them. Radiographs: DENTEX, CC BY-NC-SA 4.0.

**Why reading by eye is hard.** Caries dissolves mineral, so a lesion appears as a darker (radiolucent) region inside the bright tooth; fillings and crowns are the brightest objects in the image. Early lesions are faint: across 117 studies, radiographic detection found only 24–42% of carious lesions of any stage and 36–56% of those reaching the dentine, though it rarely called a sound surface carious. Panoramic images add their own confusions — radiolucencies that are not caries, such as cervical burn-out, Mach bands and overlapping contacts — and detect proximal caries less accurately than bitewings, so every caries label in this paper is a panoramic reading. Periodontal disease is harder still: it is staged from periodontal breakdown relative to root length, tooth loss and complexity factors such as pocket depth and furcation involvement, so radiographic bone loss is one input to a diagnosis, not the diagnosis. This project set out to build a dentist-facing assistant for caries and periodontal disease on such images; the caries aim is evaluated here, and the periodontal aim was not achieved (Section VI-F).

**The same trap as pneumonia detection.** An artificial-intelligence (AI) assistant that pre-charts findings tooth by tooth could shorten that reading — provided its findings come from the image. Chest radiography shows how that proviso fails. In a pneumonia task, sorting radiographs by hospital alone reached an area under the ROC curve (AUC) of 0.861, because prevalence differed between sites; a learner trained to minimise error over a population will use any cue that predicts the label, a shortcut. Teeth carry such a cue in their anatomy. Caries is not spread evenly over the mouth; in our data the first and second molars carry most of it (Figure 2). A model can therefore earn part of its score by knowing where caries usually is rather than seeing where it is in this image.

The usual metric cannot tell the two apart. An automated report must decide three things for every tooth, in sequence: that a tooth is there, which tooth it is, and whether it carries a finding. The decisions compose, so an entry is right only when all three are, and an early error cannot be repaired later: a lesion correctly recognised but attached to the wrong tooth number is a wrong report. A score that summarises only the last decision is silent about the two that condition it, and a set of tooth codes can be chosen without any image. Such a score therefore has a floor set by the prior, and means little until an image-blind constant is scored beside it. The floor also moves with the population: a constant's lesion agreement is the share of a cohort's lesions that lie on its teeth, and a model that has absorbed the prior moves with it, whereas a model that reads the lesion need not. Agreement on one development cohort cannot separate the two explanations; agreement on external cohorts, paired with the constant and reported per site, is necessary but not sufficient, because ordinary domain shift predicts the same pattern (Table 8).

**Existing solutions and their limits.** Tooth numbering is the most mature step. Detect-then-classify numbering reached expert-level sensitivity with a convolutional neural network (CNN) on 222 held-out images (numbering sensitivity 0.9800), and later systems report class-averaged numbering accuracy of 0.9988. These figures usually score correctly detected, cropped teeth, an easier task than numbering under detector output, where teeth can be missed or duplicated. Caries detection reports high figures with weaker support: a systematic review found accuracies of 86.1–96.1% on panoramic radiographs, in studies whose quality and reporting it judged low, and one enumeration-then-caries detector held lesion sensitivity at 0.70 internally and 0.67 externally. For bone loss, a CNN trained against the measured percentage of loss reached accuracy 0.81, but compared with clinicians another model reached weighted F1 0.29 and could not detect severe loss.

Few of these figures are tested elsewhere. Of 516 medical-imaging AI studies from 2018, only 31 (6%) validated externally, and dental models degrade when they are: an apical-lesion model fell from F1 54.1% to 32.7% at a second centre. Other fields guard against shortcuts with a baseline that withholds the input the task is about: visual-question-answering models answered from language priors while ignoring the image, and in natural-language inference a model that never sees the premise beats the majority class. In the 49 task-relevant papers of our own structured review of 117 papers on tooth detection, caries and periodontal bone loss, we noticed no image-blind baseline (an observation from reading, not a systematic count). A reported tooth-level caries figure therefore cannot yet be read as evidence that a model reads the radiograph.

**Our solution.** We built the assistant as a modular six-stage prototype — tooth detection, FDI numbering, caries localisation, caries severity, an abnormality flag and a per-tooth report — so that each stage can be measured, replaced and audited on its own, and we score it against the image-blind constant. RQ1: does tooth-level agreement separate the pipeline from that constant, on development data and on external cohorts? RQ2: does reformulating the caries stage from classifying tooth crops to localising lesions in the whole image — a task a fixed list cannot perform — separate them? RQ3: what does the pipeline show on outputs a fixed list cannot produce? The reasoning above was written down after the measurements, so it is a frame for reading the results, not a set of predictions tested in advance. The contributions are:

1. An application of F1-optimal thresholding to tooth-level caries scoring: the best image-blind tooth list and its selection rule, set against our data post hoc (Section III, Table 8).
2. A constant-baseline protocol: two metric families, three cohorts, four external sites, paired cluster-bootstrap intervals (Sections V–VI).
3. A reformulation of the caries stage as lesion detection, adopted under a rule committed before its adopted arm was trained, which led the constant on the pooled external sites while flagging fewer teeth; the change of task is confounded with a new training mixture (Section VI-D).
4. An evidence audit of the whole system, including its negative results: the crop classifier tracked the prior, and the abnormality flag supports no periodontal claim (Sections IV, VI-F, VIII).

## II. Related Work

**Datasets.** We use the Tufts Dental Database of 1,000 OPGs with expert tooth and abnormality annotations, DENTEX, with hierarchical quadrant, enumeration and diagnosis labels, the CariesXrays lesion benchmark of 6,000 OPGs, the multi-centre dataset of Li et al., collected at three hospitals in Ningxia and Shenzhen, and UFBA-425.

**Further related work.** Beyond the work discussed in Section I, a multi-stage system reports better results than prior methods on Tufts and two other datasets, and public datasets have been combined to predict segmentation, FDI numbers and diagnoses together. Caries analysis has used dual networks, dedicated classifiers and contrastive feature pyramids. Radiographic periodontal bone loss is measured against anatomical references: besides the CNN of Section I, a hybrid method located the bone level and cemento-enamel junction to stage periodontitis radiographically, and a periodontitis model built from OPGs linked to clinical diagnoses and tested at four centres is the strongest design we found. A YOLOv11 detector of 13 conditions fell from mAP@0.5 0.857 to 0.806 on external images, weakest on subtle pathology such as caries; aggregate metrics can hide failures on clinically important subsets, and biases enter medical-imaging evaluation at every step. Visual-question-answering models also lost accuracy when answer priors differed between training and test, and COVID-19 detectors relied on confounders and failed at new hospitals.

**Calibration, abstention, VLMs and translation.** Temperature scaling and isotonic regression are our calibration comparators, and abstention follows selective classification. Vision-language models (VLMs) are being adapted to dental diagnosis; we use Qwen2.5-VL as general comparators that need no task training. Translating such systems into care requires clinical evaluation beyond retrospective accuracy.

## III. Theory: What a Tooth-Level Score Measures

### A. The report as a chain of decisions

The report's entry for a tooth is correct only if the tooth is detected ($D$), numbered correctly once detected ($N$), and given the right finding ($F$):

$$
P(\text{entry correct}) = P(D)\, P(N \mid D)\, P(F \mid D, N).
$$

The first two factors concern identity, not disease, and bound everything after them: a perfect caries model still writes a wrong report on every tooth that was missed or misnumbered. A metric that matches findings to teeth by code (FDI-set F1, Section III-B) charges for both; one that matches lesions by position in the image (lesion agreement, Section III-C) is blind to the second. Table 1 measures our pipeline's identity factors and where the losses fall. On DENTEX, whose other images trained the detector, identity costs 7.2 points; on the Tufts test split, also from a training corpus, 36.5; on UFBA-425, which no model trained on, 55.5 points as the files are distributed.

**Table 1.** Identity before disease: the first two factors of (1) per tooth, in percent. Det.: detected; Exact: numbered exactly, of those detected; End to end: their product, with a 95% cluster-bootstrap interval. DENTEX 164 images, whose 936 teeth are those labelled in its disease release (about six per image, not the full dentition), so its figures are not comparable with the full-dentition Tufts and UFBA rows; Tufts test 143, UFBA-425 425 (as distributed, and widened to a panoramic shape).

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

Equation (2) counts every named code as a prediction, present tooth or not, as the scorer does (a constant restricted to detected teeth is scored in Section VI-B), and applies to any set prediction scored by micro-F1 over a fixed label set. Nothing in it depends on an image, and the constant's recall, $\sum_{c \in S} n_c / P$, is the share of carious teeth that lie at its codes. Writing $A = \sum_{c \in S} n_c$ and $k = |S|$, adding a code $c \notin S$ raises the score, $2(A+n_c)/((k+1)N+P) > 2A/(kN+P)$, if and only if (the set-prediction form of the result that the F1-optimal threshold on calibrated scores is half the optimal F1)

$$
p_c > \tfrac{1}{2}\, F_1(S).
$$

For any fixed size the best set is the $k$ most prevalent codes, so the F1-optimal constant is a prefix of the codes sorted by prevalence. Writing $S_k$ for the $k$ most prevalent codes, F1 rises along $S_1, S_2, \dots$ to a single peak: if code $k+1$ fails (3) against $S_k$, then $p_{k+1} \le \tfrac{1}{2}F_1(S_{k+1})$ as well, so every later, less prevalent code fails too. The optimum is therefore the prefix cut where (3) first fails, and it holds exactly the codes with $p_c > \tfrac{1}{2}F_1^{*}$: a functional of the caries prior alone. That first molars are the most caries-susceptible teeth was found in children aged 5–16; the prior, and with it the floor, depends on the population's age and exposure.

![Figure 2*0.92](figures/R05_positional_prior.pdf)

**Figure 2.** The positional prior and the constant it implies. (a) Share of images in which the expert marked each FDI code carious, in chart order (patient's right to left, as displayed): grey, the fit set (78 DENTEX images with caries, excluded from scoring because our models trained on them); orange, the 164 scored images. Magenta: the eight codes rule (3) admits; dashed: the final threshold $F_1/2 = 0.196$. (b) F1 of the $k$ most prevalent fit-set codes. Computed with the evaluation's loaders; the script asserts the saved scores.

On the fit set (Figure 2) rule (3) admits the eight first and second molars, with prevalences from 0.372 (tooth 26) to 0.205 (tooth 27), and rejects the ninth code, tooth 15, at 0.128 against a threshold of 0.196 — exactly the set the evaluation's greedy search returns. Frozen, {16, 17, 26, 27, 36, 37, 46, 47} scores F1 0.392 on its fit images and 0.320 on the 164 scored ones — 286 true positives among 1,312 named codes, against 477 carious teeth, so its recall is 0.600, the share of carious teeth that lie on those eight molars. The prior shifts between the two sets: teeth 17 and 27 fall to 0.140 and 0.134 on the scored images, so the oracle constant fitted on the scored images themselves keeps six molars and reaches only 0.330. Almost all of the image-blind score therefore needs no evaluation data. The set is fragile at its margin and the floor is not: refitted on 10,000 resamples of the fit images, rule (3) returns exactly these eight molars 27% of the time and seven codes 45%, yet the refitted constants score a median F1 of 0.320 on the scored images, 95% of them between 0.279 and 0.330; over sizes one to sixteen the constant's F1 is flat from six to nine codes (0.298–0.325).

### C. Lesion agreement and the cohort's prior

The second metric family scores lesions rather than codes. Let a cohort contain $L$ expert lesions, let $T(\ell)$ be the detected tooth that contains lesion $\ell$, and let $\mathcal{F}$ be the set of teeth a system flags. Lesion agreement is

$$
A(\mathcal{F}) = \frac{1}{L} \sum_{\ell} \mathbf{1}\big[\, T(\ell) \in \mathcal{F} \,\big].
$$

On DENTEX the released caries annotations outline the affected tooth rather than the lesion — the median annotation's bounding box covers 0.91 of the detected tooth box (IoU 0.81) — so there $A$ is a tooth-level measure; on the external cohorts the lesion annotations are small and $A$ asks only whether a lesion's centre lies on a flagged tooth, never whether a predicted box overlaps the lesion. $A$ has no negative class. It can only rise as $\mathcal{F}$ grows, and flagging every detected tooth reaches its ceiling, the share of lesions inside any detected tooth (0.998 on DENTEX); it must be read beside the number of teeth flagged. For the constant, $\mathcal{F}$ is the eight molar boxes our front end finds, so $A$ is the cohort's prior mass on those molars. On Tufts, a training corpus, 92.0% [89.58, 94.06] of the boxes our pipeline codes as one of the eight molars are true first or second molars, and it reaches 81.7% [77.72, 85.35] of them; placement is not measured on any external cohort. This prior mass is the cohort's as placed by our front end — 0.630 on DENTEX, 0.604 on CariesXrays, 0.591 on the four Ningxia sites, and from 0.494 to 0.709 between sites of that one cohort (Section VI) — and it depends on the front end as well as on the cohort: changing only the tooth detector moved the constant's pooled Ningxia agreement from 0.399 to 0.591. Site-dependent prevalence also drove a pneumonia shortcut. A system that has absorbed the prior inherits this variation, so systems can be compared only when paired on the same images, cohort by cohort and site by site.

### D. A testable signature of a positional shortcut

If a per-tooth classifier has learned the probability of caries given position, and not only given pixels, two consequences follow. Its score on teeth not annotated as carious should rise with the base rate of their position, because the prior lifts every tooth of a caries-prone type. And its ranking should survive only partly when position is held fixed: the within-type area under the ROC curve (AUC), which ranks carious against healthy teeth of the same type, removes the positional cue and keeps the image signal. Table 2 applies both tests to the pipeline's crop classifier on 863 held-out tooth crops from 34 radiographs, cut with ground-truth boxes so that the front end plays no part. Both consequences are also expected if caries is under-annotated more often on molars, or if molar crops differ in ways correlated with the label (restorations, overlap), so the test is consistent with a positional shortcut rather than proof of one.

**Table 2*.** The positional-shortcut test on the crop classifier: 863 held-out crops from 34 radiographs. Base rate: share carious in its training data. Within-type AUC interval: cluster bootstrap over the 34 radiographs, 5,000 resamples.

| Tooth type | Crops | Carious | Base rate | Mean score, not carious | Not carious, flagged | Within-type AUC |
|---|---|---|---|---|---|---|
| Incisor | 266 | 8 | 0.017 | 0.075 | 0.039 | 0.681 |
| Canine | 129 | 5 | 0.023 | 0.087 | 0.016 | 0.748 |
| Premolar | 221 | 31 | 0.157 | 0.273 | 0.268 | 0.781 |
| Molar | 247 | 83 | 0.343 | 0.478 | 0.482 | 0.781 |
| All, within type | 863 | 127 | — | — | — | 0.745 [0.660, 0.842] |

The classifier's mean score on teeth not annotated as carious climbs with the training base rate, from 0.075 on incisors to 0.478 on molars, and it flags 48.2% of such molars: consistent with a prior doing visible work, at a cost in precision. Its within-type AUC is 0.745 [0.660, 0.842] against a pooled AUC of 0.855, so position carries part of the ranking and there is also lesion signal; the per-type AUCs of incisors and canines rest on 8 and 5 positives and carry no interval. A predictor that uses position alone and never sees an image reaches average precision (AP) 0.296, against the classifier's 0.550 and chance at 0.147. It is neither a lookup table nor a pure reader, but a reader whose score is inflated by a prior the constant captures for free.

### E. Why localisation resists the shortcut

A whole-image lesion detector receives no tooth code, although absolute position in the image still carries arch information: to flag a tooth it must place a box mostly inside it. It can express a positional prior only by drawing boxes over molars where it sees no lesion, and each such box is charged as a false positive under (2) and earns agreement under (4) only if a lesion happens to lie there. If the detector's lead over the constant comes from reading the image, one would therefore expect it to come with fewer flagged teeth, not more, and within each tooth type its flags to be carious more often than the classifier's; both are also what any detector with a higher threshold would show, so they are consistent with reading, not proof of it.

### F. Inference over images and sites

Teeth within one radiograph share exposure, anatomy and annotator, so their errors are correlated; we resample images, not teeth, the cluster bootstrap that stays consistent when clusters carry random effects. For two systems scored on the same images, the paired difference is recomputed on each bootstrap resample of images, and its 2.5th and 97.5th percentiles give the interval. Across sites, per-site differences $\Delta_j$ with variances $v_j$ (from each site's interval width) are pooled by DerSimonian–Laird (DL) random effects,

$$
\hat\mu = \frac{\sum_j \Delta_j / (v_j + \hat\tau^2)}{\sum_j 1 / (v_j + \hat\tau^2)},
$$

where the between-site variance $\hat\tau^2$ is estimated from Cochran's $Q$, and $I^2 = (Q - k + 1)/Q$ is the share of variation due to sites. A fixed-site interval asks whether a system led at these sites; the random-effects prediction interval asks whether it would lead at another. Per-site variances are approximated from the interval widths (width/3.92). With four sites the DL interval is too narrow, so we also report the Hartung–Knapp–Sidik–Jonkman (HKSJ) interval, plain and with its scale truncated at one, and a Q-profile interval for $\tau$. The four Ningxia test sets are release partitions of a three-hospital study, so their independence is assumed.

## IV. System

The pipeline maps an OPG to a per-tooth record in six stages (Figure 3); Figure 4 follows one held-out radiograph through every stage. We kept the stages separate, rather than training one multi-task network, so that each stage could be scored, swapped and audited against its own held-out data, and so that a weak stage can be withheld from the report without retraining the rest.

![Figure 3*0.92](figures/R06_architecture.pdf)

**Figure 3.** The pipeline as it ships, with its default checkpoints and learnable parameter counts read from the saved weights; the default configuration (Stages 1, 2, default 3a, 3b, 4a and the withheld 4b, 11.18 M) totals 95.34 M. Blue: identity stages; dark blue: the default caries path; dashed orange: the retained caries variant, the comparison arm throughout; green: the abnormality flag. Thresholds are fixed in code; none was tuned on an evaluation cohort.

**Stage 1** is a YOLOv11l detector trained on Tufts, DENTEX and a Kaggle FDI set; it runs on the OPG rotated 90 degrees, and its boxes are rotated back, inside one function, so callers pass an upright image. **Stage 2** scores every FDI code for each tooth crop with a ResNet18 and four box-position features, and the Hungarian algorithm makes the assignment one-to-one; codes below a confidence of 0.30 are marked unsure. **Stage 3a** is by default a whole-image YOLOv11l lesion detector (9,600 samples per epoch, from 4,800 CariesXrays and 650 replicated DENTEX images) whose boxes go to the tooth containing most of each; the retained variant classifies each tight tooth crop. **Stage 3b** grades flagged teeth as caries or deep caries, the two caries labels DENTEX releases. It was retrained on DENTEX's image-level split and tested once, under a pre-registration, on 395 held-out crops from 98 radiographs: macro-F1 0.772 [0.711, 0.828] against 0.483 for an image-blind position prior, with 66 of its 116 deep-caries calls correct. Those crops are annotation boxes of teeth annotated carious, so its grade on the teeth the pipeline flags is untested. The head it replaced was tuned and validated on the same 133 development crops and could not be tested. **Stage 4** flags a tooth crop that overlaps an abnormality the Tufts expert marked (apical lesions, sclerosis, cysts); it was built for periodontal bone loss, and we name it for its label. Its severity head is withheld from the report by default. For backward compatibility the report still names this field and its positive value `bone_loss`; the field carries the abnormality label described here. **Stages 5–6** fuse the outputs on the FDI code into a JSON record and an annotated overlay, the system's only outputs, each carrying the checkpoint hashes and the per-stage limitations; the whole system ran at 1.70 s per image on a laptop CPU with no GPU, measured before the Stage-4 severity head was withheld [ASK AUTHOR: CPU model]. For tooth 36 of Figure 4 the record holds the code (confidence 0.9999), detection confidence 0.8389, a deep-caries flag (lesion-detector score 0.8892, a detection score rather than a probability; severity score 0.9579 in this saved report, made with the previous Stage-3b head, and 0.9996 with the current one), no Stage-4 flag (0.7853) and an assessability flag; the expert did not annotate caries on this tooth. A browser demonstration wraps the same function and states on every result that the pipeline is not clinically validated.

![Figure 4*0.80](figures/R02_walkthrough.pdf)

**Figure 4.** One held-out DENTEX radiograph (test_0, not used to train any model) through the shipped pipeline. (a) Input, 2,829 by 1,316 pixels; dashed: the region in (b)–(f). (b) Stage 1: 30 teeth, with detection confidences. (c) Stage 2: one FDI code per tooth; "?" marks its two unsure codes (24, 42). (d) Stage 3a: one lesion-detector pass over the whole image, four boxes (confidence 0.35 to 0.89). (e) Each box goes to the tooth holding most of it: 26 and 46 flagged as caries, 36 and 45 as deep caries; no Stage-4 flag. (f) The written overlay with the expert's three caries annotations (26, 45, 48) in yellow: two found, 48 missed, 36 and 46 flagged with no annotation. Radiographs: DENTEX, CC BY-NC-SA 4.0.

Table 3 states, for each stage, what its reported number is evidence of. Only one stage result is held out from every training corpus and from model selection: numbering on UFBA-425. The crop classifier's external scores are free of its own training and selection, but the current tooth detector was chosen after its Ningxia result was known.

**Table 3*.** The evidence behind each stage. Held out: scored on data no model trained on but from a training corpus; unseen: a corpus no model trained on; external: a cohort from other sites. Sens.: sensitivity; spec.: specificity.

| Stage | Model, params | Trained on | Held-out evidence | Unseen or external evidence | What it supports |
|---|---|---|---|---|---|
| 1 Detect | YOLOv11l, 25.31 M | Tufts, DENTEX, Kaggle | Tufts test recall 89.3%; box mAP@0.5 0.587 vs 0.723 for a Tufts-only control | UFBA-425 recall 66.6% | a front end, adopted against its guard |
| 2 Number | ResNet18 + position, 11.19 M | DENTEX, Tufts crops | Tufts test 63.5% end to end; DENTEX 92.8% (in-domain) | UFBA-425 44.5% (77.2% widened) | identity with stated error |
| 3a Lesion detector | YOLOv11l, 25.31 M | CariesXrays, DENTEX | DENTEX F1 0.498 vs 0.320 | Ningxia +9.28 pooled, 3 of 4 sites; informed adoption | the sign of the lead |
| 3a Crop classifier | ResNet18, 11.18 M | DENTEX crops | 863 test crops, AP 0.550 | Ningxia +0.89 (level); CariesXrays -22.42 | external to the classifier; Ningxia informed the detector choice |
| 3b Severity | ResNet18, 11.18 M | DENTEX, image-level split | three runs on 395 test crops: macro-F1 0.772 (default), 0.745, 0.817 vs 0.483 for a position prior; deep-caries precision 0.57 | none | a grade on annotated carious teeth; untested on the pipeline's flags |
| 4a Abnormality flag | ResNet18, 11.18 M | Tufts, radiograph split | three runs: sens. 27.5%, 16.5%, 11.0% at spec. 95.9–98.6%; PPV 0.25–0.29 | none | one sentence; not periodontal |
| 4b Its severity | ResNet18, 11.18 M | Tufts | retrain macro-F1 0.294, 0.328, 0.382 (three seeds) vs prior 0.334 | none | withheld |

## V. Data and Evaluation Protocol

**Cohorts** (Table 4). Splits are by image, chosen so that no radiograph contributes to both training and evaluation; the releases carry no patient identifiers, so a patient's second radiograph cannot be excluded, and one re-rendered Tufts radiograph (test 248) duplicates a training radiograph (1017) and holds no Stage-4 positive. The exception is Stage 4's first model, whose crop-level split is discussed in Section VI-F. DENTEX's disease subset has 250 annotated OPGs; MD5 hashing found 86 byte-identical to images our models trained on (85 in numbering, 1 in detection), leaving 164 scored, of which 148 carry caries (479 caries annotations on 477 teeth; the annotations outline the tooth, Section III-C). A perceptual-hash search (pHash, dHash) of the 1,389 other DENTEX images found no further copy: the 86 lie at distance 0, and the 20 scored images nearest to them differ in restorations or missing teeth. Ningxia is the public release of the dataset of Li et al.: their paper describes three hospitals, and the release divides its test data into four sets — test2 from its training centre, test1, test3 and test4 described as cross-centre — which we treat as four sites. No model was trained or tuned on Ningxia, but it is not blind: its caries images had been scored in 14 full passes before the current tooth detector was chosen (20 including the re-measurement that followed), and that choice was made with the detector's Ningxia result in view. All datasets are public, de-identified releases; no new patient data were collected. Each cohort carries one released annotation per image; the number of readers and whether annotation was exhaustive are not stated in what we used, and the scored DENTEX images carry no tooth labelled healthy and the external cohorts no healthy-control labels, so specificity cannot be estimated on them.

**Table 4.** Evaluation cohorts, units and exposure. Each row is an analysis population; counts must not be summed across rows.

| Cohort | Images | Unit (n) | Role and exposure |
|---|---|---|---|
| DENTEX disease | 164 | 936 labelled teeth; 477 carious; 479 tooth-level caries outlines | development; detector trained on other DENTEX images |
| Ningxia, 4 sites | 337 | 1,013 lesions | external; never trained on; informed both detector choices |
| CariesXrays | 1,200 | 2,815 lesions | external, except to the lesion detector (its validation split) |
| Tufts test | 143 | 3,760 / 3,892 teeth | numbering / Stage 4 (182 labelled); both trained on Tufts train |
| UFBA-425 | 425 | 11,591 teeth | numbering; no model trained on it |

**The ladder.** Four systems answer one question — which teeth in this radiograph show caries? — on the same 164 images: the pipeline (with each Stage-3a implementation), Qwen2.5-VL-32B (33.45 B parameters) and Qwen2.5-VL-7B (8.29 B), both zero-shot with the FDI scheme in the prompt (and shown a blank grey and a random-noise image as content-free controls), and the constant of Section III-B.

**Metrics.** FDI-set F1 (2) is micro-averaged over teeth. Lesion agreement (4) matches each expert annotation to a flagged tooth: on DENTEX, where annotations outline teeth, by greedy intersection over union (IoU) of at least 0.30 with a centroid fallback, on the external cohorts by centroid containment, because their lesions are small (median 731 pixels) inside tooth boxes of about 25,000 pixels; every comparison is therefore within a cohort.

**Statistics.** Intervals are 95% percentile cluster bootstraps over images (Section III-F): 10,000 resamples, seed 42, unless stated — 2,000 for the crop classifier's calibration AP, 5,000 for its within-type AUC, and 1,000 with seed 0 for the two abstention gains. Differences are system minus comparator in percentage points (pp); positive favours the system. We report estimates with intervals, not a family of tests: no multiplicity correction is applied across cohorts, arms, metrics and sites, and the Ningxia lead, measured on a cohort that informed the adoption, is optimistic by construction.

**Committed rules and departures from them.** The lesion detector's adoption rule — score above both the constant and the crop classifier on at least two of three cohorts, at no more than 1.5 times their rate of flagged teeth — was committed to the (private) repository before the adopted pooled arm was trained; the single-corpus arm reused a detector trained two days earlier, whose result the rule's rationale cites, and one of the three cohorts was the lesion detector's own validation split. Both arms were scored on the same cohorts and the pooled arm, the one that met the rule, was adopted. The current tooth detector was made the default by a dated decision against the failed Tufts guard of its own pre-registration (an earlier multi-corpus arm had failed a similar guard), after its DENTEX and Ningxia results were known; every comparison in Section VI was re-measured under it with the previous detector as a same-machine control.

## VI. Results

### A. Training: what each model learned, on its validation split

Every training loss in Figure 5 falls steadily. Each checkpoint is the best on its run's validation split, so these are selection diagnostics, not test results, and each is a single run (three seeds for Stage 4a). The tooth detector reaches validation box mean average precision at IoU 0.5 (mAP@0.5) 0.634 at its last epoch, still rising; on the frozen Tufts test split it missed its pre-registered guard (within four points of a Tufts-only control: 0.587 against 0.723) and was adopted regardless, by a dated decision, for its numbering and caries behaviour, measured on the scored DENTEX images and Ningxia. The lesion detector peaks at mAP@0.5 0.820 (epoch 29 of 54). The numbering head reaches crop-level FDI-exact 0.810 (epoch 12 of 15), with the quadrant digit right on 98.1% and the position digit on 82.5%: its errors are counting errors along the arch. Stage 4a's validation macro-F1 stays below 0.6 in all three seeds (best 0.568, 0.580, 0.597).

![Figure 5*0.86](figures/R04_training.pdf)

**Figure 5.** Training logs of the four trained stages, from the saved run files; validation splits, not test. (a) Tooth detector, 148 epochs, 150 Tufts radiographs. (b) Lesion detector, 54 epochs, 1,200 CariesXrays radiographs. (c) Numbering head, 15 epochs, 6,450 tooth crops (DENTEX and Tufts, ground-truth boxes). (d) Stage-4a flag, three seeds of one recipe. Dots: the checkpoint each run kept.

On a published benchmark the detector family is competitive: trained on CariesXrays alone, the lesion detector's single-corpus arm reaches COCO AP 48.2 (AP50 84.5) on our seed-fixed 1,200-image validation split, matching the authors' task-specific method (48.2, AP50 84.1) and six points above the strongest of their ten baselines (42.2). The splits differ and ours chose the checkpoint, so this is indicative only; Section VI-D shows that the checkpoint does not transfer.

### B. RQ1 on development data

**Table 5.** Tooth-level caries prediction on 164 DENTEX images (477 carious teeth), micro-averaged. P: precision; R: recall; Matched: F1 minus that of a constant naming as many codes (pp).

| System | P | R | F1 | Matched |
|---|---|---|---|---|
| Pipeline, lesion detector | 0.439 | 0.574 | 0.498 | +22.35 |
| Pipeline, crop classifier | 0.237 | 0.765 | 0.362 | +5.50 |
| Constant (image-blind) | 0.218 | 0.600 | 0.320 | — |
| Constant on detected molars | 0.259 | 0.581 | 0.358 | — |
| Qwen2.5-VL-32B, 0-shot | 0.250 | 0.243 | 0.246 | +0.39 |
| Qwen2.5-VL-7B, 0-shot | 0.248 | 0.107 | 0.149 | +1.39 |
| Oracle constant (test-fit) | 0.245 | 0.505 | 0.330 | — |

Both VLMs see the radiograph and score below a list that does not (Table 5): -7.32 points [-11.23, -3.42] for the 32B model and -17.04 [-21.22, -12.66] for the 7B. The crop-classifier pipeline leads the constant by +4.27 points [+1.58, +7.05] while naming 1,537 teeth to its 1,312, at barely higher precision (0.237 against 0.218), as Section III-D implies for a classifier that leans on the prior. The constant, however, names its molars even where a tooth is missing, which the pipeline cannot do. Restricted to the molars our front end detected and numbered, the constant names 1,069 codes and reaches F1 0.358 (+3.86 points [+2.83, +4.90] over the unrestricted one), and the crop classifier's lead over it is +0.41 [-2.24, +3.14]: not separable. The lesion-detector pipeline leads by +17.80 [+13.48, +22.02], and by +13.94 [+9.63, +18.15] over the restricted constant, and is the only system whose precision clearly exceeds the constant's (0.439), naming 624 codes, 43.9% of them carious. A rerun of the shipped pipeline on a second machine flagged different codes on 12 of the 164 images (F1 0.490 against 0.498; +13.12 [+8.84, +17.36] over the restricted constant). Volume explains neither pipeline lead: against a matched constant, which answers the $k$ most prevalent fit-set codes on some images and $k+1$ on the rest so as to name as many codes as the system, the leads are +5.50 [+2.84, +8.22] and +22.35 [+17.42, +27.18]. The VLMs are level with constants of their own volume (32B [-4.90, +5.63], 7B [-2.06, +4.85]): they fall below the eight molars by naming fewer teeth, and within those intervals their F1 shows no image information. Only one prompt was tried; giving the 7B model two or four examples lowered its F1 to 0.066 and 0.034. Under lesion agreement the crop classifier leads the constant by +17.12 points [+12.15, +21.89], partly by volume: it flags 1,439 teeth against 988, at a lower match rate (0.267 against 0.306). The lesion detector flags 603 teeth at the highest match rate (0.473) and is not separable from the constant (-3.55 [-10.11, +2.64]); F1 ranks it above the crop classifier, agreement below. Because DENTEX annotations outline whole teeth, the lesion detector, whose DENTEX training boxes are of the same kind, is scored here at the tooth level. None of this is yet evidence of perception: the front end trained on this corpus.

### C. RQ1 on external data

On the four sites the crop-classifier pipeline and the constant are level when pooled: 0.600 against 0.591, a difference of +0.89 points [-3.86, +5.57] (Figure 6a). Per site the difference runs from -18.99 [-26.32, -11.84] at test1 to +12.32 [+5.01, +19.20] at test2 (Figure 6b), a 31-point swing within one cohort, while the constant's own agreement — each site's prior mass on the eight molars — ranges from 0.494 to 0.709. On CariesXrays the constant wins outright, 0.604 against 0.379 (-22.42 points [-24.62, -20.18]), and it flags 46% more teeth at the higher match rate (0.200 against 0.188), so volume does not explain it. The pipeline leads only where its detector trained.

![Figure 6 0.88](figures/R07_paired_differences.pdf)

**Figure 6.** Lesion agreement of each Stage-3a option minus the constant, paired 95% cluster-bootstrap intervals (10,000 resamples). (a) Per cohort; DENTEX is development data for the front end and CariesXrays is the lesion detector's validation split. (b) The four Ningxia sites, the pooled difference with sites fixed, and the DerSimonian–Laird mean for the lesion detector (diamond; bar: 95% interval; dotted, beyond the axis: prediction interval for a new site).

### D. RQ2: localising lesions instead of classifying teeth

Five direct repairs of the crop classifier came first (Table 6), each against a same-day control under a rule fixed in advance; none separated from zero, including a retrain with 2.67 times the carious crops; that retrain was underpowered and did not enlarge the negative class, so it does not rule out a supervision-side limit. We therefore changed the task rather than the model, from classifying a crop to placing a lesion box in the whole image.

![Figure 7*0.78](figures/R03_outcomes.pdf)

**Figure 7.** Pipeline output against the expert on three held-out DENTEX radiographs: left, the lesion detector; right, the constant placed by the same front end. (a) test_120: all seven annotated carious teeth found, 33 and 34 also flagged; the constant covers four of the seven without reading the image. (b) test_0 (Figure 4): two of three found, 48 missed. (c) test_110: none of four found (32, 33, 34, 46 missed; 16, 24, 26, 36, 37 flagged). A flag without an annotated lesion is not a confirmed false positive: the annotation's exhaustiveness is not documented. Radiographs: DENTEX, CC BY-NC-SA 4.0.

**Table 6.** Repairs of the crop classifier on the same 863 held-out crops (34 radiographs): paired difference in AP against the control (in F1 for the thresholds).

| Repair | Difference [95% CI] |
|---|---|
| Contrast equalisation (CLAHE) | +0.049 [-0.003, +0.099] |
| Crop expanded 1.25 times | +0.020 [-0.037, +0.081] |
| Position-balanced sampling | +0.043 [-0.033, +0.116] |
| Retrain, 2.67 times the positives | -0.002 [-0.089, +0.082] |
| Per-tooth-type thresholds (F1) | +0.006 [-0.034, +0.041] |

Under the tooth detector of the time, the lesion detector met the committed rule on two cohorts of three, one of them its own validation split: +12.2 points [+10.1, +14.3] over the constant on CariesXrays and +10.2 [+6.3, +14.0] on Ningxia, with a tie on DENTEX (-3.3 [-8.4, +1.3]). Table 7 gives the three arms under the current detector.

**Table 7.** Lesion agreement of the three Stage-3a options under the current tooth detector: crop classifier (Clf.), constant (Const.) and lesion detector (Det.); last column, detector minus constant in points, paired 95% confidence interval (CI). CariesXrays is the detector's validation split.

| Cohort | Clf. | Const. | Det. | Det. minus const. |
|---|---|---|---|---|
| DENTEX | 0.802 | 0.630 | 0.595 | -3.55 [-10.11, +2.64] |
| CariesXrays | 0.379 | 0.604 | 0.757 | +15.38 [+12.96, +17.73] |
| Ningxia | 0.600 | 0.591 | 0.684 | +9.28 [+4.72, +13.73] |

Both observations Section III-E anticipates are present, but neither is controlled for operating point. The lead comes with fewer flags: the lesion detector flags 4.35 teeth per image against the constant's 7.15 on Ningxia, and 2.16 against 7.05 on CariesXrays. And within each tooth type its flags are carious more often — on DENTEX, the development corpus, where per-type records exist: 46.3% of the molars it flags carry caries, against 28.4% for the crop classifier and 21.8% for the constant, and 39.7% of its flagged premolars against 17.0%, but it flags 447 molars to the classifier's 1,023, and precision usually rises as flags fall. Per site (Figure 6b), without correction for four comparisons, it is separated from the constant at test2, test3 and test4 (+16.91 [+9.17, +24.62], +11.73 [+1.07, +21.34], +13.98 [+2.34, +24.34]) and not at test1 (-3.16 [-10.56, +3.97]), where the constant is strongest; the lower bounds at test3 and test4 are close to zero. Treating the sites as a sample (random effects, post hoc) gives +9.61 [-0.54, +19.76] (HKSJ [-5.02, +24.24], truncated [-6.88, +26.09]), $I^2 = 81\%$, $\tau$ 9.27 points [3.22, 33.09] and a prediction interval of [-36.08, +55.29]: the lead holds at three of these four sites and is not shown for an unseen one. The training mixture explains much of the transfer: under the previous tooth detector, the single-corpus arm of Section VI-A reached 0.694 [0.674, 0.714] on CariesXrays and collapsed to 0.086 [0.055, 0.119] on DENTEX and 0.240 [0.209, 0.272] on Ningxia.

Figure 7 shows these numbers on images, in rows chosen by a rule fixed before rendering: the scored image with the most annotated carious teeth all found, a typical image, and the one with the most of them none found.

![Figure 8*0.86](figures/R08_numbering_reliability.pdf)

**Figure 8.** Outputs a constant cannot produce. (a) Numbering outcome for each of 936 ground-truth DENTEX teeth (log scale). (b) Share of detected teeth given a wrong code, by position. (c) Accuracy on the items answered as the least confident are declined: numbering, from saved per-tooth confidences (circle: the 0.30 threshold fixed in code); crop classifier, saved operating points at 50, 75, 90 and 100% coverage. (d) Reliability of the crop classifier's raw confidence on 863 held-out crops, by stated probability (marker area proportional to bin count).

### E. RQ3: outputs a constant cannot produce

**Numbering** (Figure 8, panels a and b). End-to-end FDI-exact accuracy on DENTEX is 92.8% (869 of 936 labelled teeth) [90.6, 94.9], an in-domain figure on teeth that carry a finding; 4 teeth are not detected and 93.2% of the 932 found are numbered correctly. Of 63 wrong codes, 51 (81.0%) name an adjacent tooth in the correct quadrant — 29 one step towards the midline, 22 one step away — and only 6 of 932 detected teeth (0.6%) get a quadrant-level error. Errors concentrate where adjacent teeth look alike: 11.3% of detected lateral incisors (position 2) and 10.1% of central incisors receive a wrong code, against 4.1% of second premolars. At molar positions, where most caries lies, 8.2% of detected second molars receive a wrong code, and each such error moves any finding to the wrong tooth: the second factor of (1).

**Selective prediction** (Figure 8c). Declining the least-confident quarter raises numbering accuracy from 0.932 to 0.980 (+4.76 points [+3.29, +6.54], 164 image clusters) and the crop classifier's from 0.797 to 0.940 (+14.25 [+11.32, +16.63], 34 clusters); at full coverage the classifier is below the 0.853 of always answering not carious, so accuracy flatters neither end of this curve. With confidences shuffled across items both gains collapse, to -0.06 and +0.00 points, so the gain comes from the confidence ranking and not from discarding items. The 0.30 threshold fixed in code lands at 96.1% coverage and 0.941 accuracy; because coverage counts detected teeth, retaining 75% of detections is 74.7% of the teeth present.

**Calibration** (Figure 8d), measured on the crop classifier because the lesion detector emits detection scores rather than per-tooth probabilities. The classifier is overconfident: at a stated confidence of 0.85 the observed share carious is 0.26, and its expected calibration error (ECE) is 0.136. Temperature scaling made it worse (0.152); isotonic regression, fitted on the validation split and tested on crops cut with ground-truth boxes, reduced it to 0.043 at a cost — AP falls from 0.550 to 0.500, and at the threshold 155 of 863 verdicts would change — so it adjusts the reported confidence only. AP 0.550 [0.445, 0.660] against a prevalence of 0.147 shows a model that ranks teeth well and fails at calibration and operating point.

### F. Controls outside the caries pipeline

Shown no anatomy, the VLMs mostly return the population prior: Qwen2.5-VL-7B answers 26,36 to a blank grey image, to random noise and to a real radiograph, and Qwen2.5-VL-32B answers NONE to the blank image but noise with exactly the constant's eight molars (one prompt; decoding settings not recorded). Stage 4's first model reported 0.923 macro-F1 on a crop-level split that let every validation radiograph supply training crops, and found 3.4% of labelled teeth (6 of 175) on 125 unseen radiographs; retrained with a radiograph-level split, three runs found 27.5%, 16.5% and 11.0% (50, 30 and 20 of 182) on 143 held-out radiographs at 95.9–98.6% specificity, with positive predictive values of 0.25–0.29 and 0.36–1.06 false flags per radiograph; on the DENTEX images the default flags 6.1% of detected teeth. Its severity head, retrained on the intended overlap bands (macro-F1 0.294 [0.214, 0.385] for the pre-specified seed, 0.328 and 0.382 for the others, against 0.334 for an image-blind position prior), stays withheld, and we make no periodontal claim.

## VII. Discussion

The analysis of Section III was formulated after the measurements, so Table 8 is a consistency check, not a test of predictions made in advance. The first row is an identity of the constant's definition, not an empirical result. Of the rest, three are consistent with the data with stated confounds, one is not specific to the theory, and one is not supported — the prior inflates the classifier's thresholded scores, but its ranking within a tooth type carries image signal.

**Table 8*.** What the theory of Section III implies, and what the measurements show (a post-hoc consistency check).

| Implication | Evidence | Verdict |
|---|---|---|
| Rule (3) gives the best constant | reproduces the fitted eight molars; recall 0.600 = carious share at them | identity (check of the arithmetic) |
| The floor moves with the cohort | constant's agreement 0.494–0.709 across four sites; 0.399 to 0.591 with the detector alone | consistent; confounded with the front end |
| Shortcut lifts non-carious scores | not-carious score 0.075 (incisors) to 0.478 (molars); 48.2% of such molars flagged | consistent; label noise and molar confounders not excluded |
| Shortcut carries the ranking | within-type AUC 0.745 [0.660, 0.842]; position-balanced AP +0.043 [-0.033, +0.116] | not supported |
| Agreement does not transfer | classifier minus constant +17.12, +0.89, -22.42 on the three cohorts | holds; not specific |
| Localising: fewer, better flags | Ningxia +9.28, 4.35 vs 7.15 flags/image; DENTEX molar flags 46.3% vs 28.4% carious | 3 of 4 sites; volume not matched |

**RQ1.** The classifier-minus-constant difference runs from +17.12 on DENTEX to -22.42 on CariesXrays (the matching rule differs on DENTEX, so this span is approximate) and over 31 points across one cohort's sites under one rule, so a favourable tooth-level figure on development data is weak evidence of perception; on development data the crop classifier's F1 lead does not survive a constant restricted to detected teeth. **RQ2.** A detector that must place lesion boxes can express a positional prior only at a cost in precision (Section III-E). It led the constant on the external sites with fewer flags, and on the development corpus its flags were carious more often within each tooth type, at a lower volume. Ningxia informed its adoption, the change of task is confounded with new training data, and the site-level interval includes zero; test1, where the constant is strongest, stays unexplained. **RQ3.** Numbering, calibration and shuffle-controlled abstention are outputs a constant cannot attempt; they show confidence that ranks the system's own errors. **What to report.** A tooth-level caries score should travel with an image-blind row fitted off the test set, the identity factors of Table 1, the evidence class of each stage's number (Table 3), per-site external results with paired intervals, images of what the system does (Figures 4 and 7) and its training curves (Figure 5), complementing the reporting checklists for medical-imaging, prediction-model and dental AI.

**Clinical implications.** The system is a research prototype for decision support and has not been evaluated with dentists or patients. Its findings are radiographic and model-derived, and three distinctions bound how they may be read. First, a caries flag is a radiographic finding against panoramic labels, not a confirmed lesion: on the development images the default pipeline left 203 of 477 annotated carious teeth unflagged (42.6%), and of its 624 flags 274 (43.9%) were on annotated carious teeth, 90 (14.4%) on teeth with another annotated finding and 260 (41.7%) on teeth with no annotation, whose status is unknown. A missed lesion is the clinically costly error, so a negative report cannot be read as a caries-free tooth. Second, the Stage-4 flag is not periodontal bone loss and not periodontitis: valid bone-loss work measures bone level against anatomical references, and periodontitis staging needs clinical measures the radiograph does not carry. Third, every stage's confidence is a model score; only the crop classifier's has been calibrated, and only on development data. Externally, 31.6% of Ningxia lesions did not lie on a flagged tooth, a misnumbered tooth carries its finding to the wrong site in the report, and a flag on an unannotated or restored tooth risks unnecessary treatment if it is acted on. No result here concerns deciduous or mixed dentition, implants or pontics, which the evaluations do not measure separately. Intended use: a research tool for studying decision support on adult panoramic radiographs, whose every finding a dentist confirms on the image; it is not a screening or diagnostic device, and no regulatory or clinical-trial evidence exists for it. Clinical value would need prospective evaluation.

## VIII. Limitations

The authors' own limitations come first.

- DENTEX is in-domain for the tooth detector, which missed its Tufts guard (0.587 against 0.723) and was made the default against two pre-registered verdicts; only Ningxia is external to the lesion detector, it informed the adoption, and the random-effects interval includes zero.
- The abnormality flag's first validation used a crop-level split, its label is overlap with an expert abnormality mask rather than bone loss, and its held-out figure is one run of three; the severity head was found to grade crop contrast, and its retrain on the intended bands did not beat a position prior.
- DENTEX caries labels were read from panoramic radiographs alone, which detect proximal caries less accurately than bitewings; the expert lesions are a subset of disease, and part of the molar prior may be a prior of what panoramic labels capture.
- The constant is optimal only in-sample, on 78 training radiographs selected for containing caries, and the analysis was checked on one corpus (78 and 164 images); the shortcut test rests on 34 radiographs; the lesion detector has no calibration curve.
- The round-1 analyses are post hoc: the near-duplicate check cannot find a second radiograph of the same patient, and the per-tooth-type comparison exists for DENTEX only, because the Ningxia per-tooth records were not saved.
- Licensing is unresolved for one training corpus of the default detector (the Kaggle FDI set states no licence), and the figures reproduce DENTEX pixels under a share-alike licence.

Additional caveats. Agreement has no negative class and the external cohorts carry no healthy controls; every model but Stages 3b and 4a is a single run, and one table row differed between two machines (0.294 against 0.300) with identical code; no clinician comparison or reader study was made; the caries severity grade was tested on annotation boxes of teeth annotated carious, not on the teeth the pipeline flags; we could not verify whether CariesXrays and a Ningxia hospital share a site or scanner.

## IX. Conclusion

A tooth-level caries score mixes what a system sees with where caries usually is. Its image-blind part has a closed form, here the eight first and second molars; with the crop classifier, our pipeline was level with it on development data once the constant was restricted to detected teeth, level with it on four external sites and below it on a third cohort, and a lesion detector led it on four pooled external sites with fewer flags, a lead not shown for an unseen site and measured on sites that informed its adoption. The floor differs between populations, so the score should travel with an image-blind row, per-site results and the evidence class of each stage. The abnormality branch did not become a periodontal model, because its label was not a periodontal label; a periodontal claim would need bone-level or clinically linked labels, and a caries claim for clinical use would need a reader study.

## Data and Code Availability

[ASK AUTHOR: release decision.] All evaluation cohorts are public releases (DENTEX, CariesXrays, Ningxia, UFBA-425, Tufts under its licence); Tufts pixels may not be redistributed. The pipeline, evaluation scripts and the per-claim number checker are in the authors' repository; the lesion detector's adoption rule is committed there before its adopted arm was trained [ASK AUTHOR: public anchor for the commit].

## Ethics Statement

This study used only public, de-identified radiograph datasets released for research and collected no new patient data. [ASK AUTHOR: confirm whether the institution requires an exemption statement.]

## Acknowledgment

[ASK AUTHOR: confirm wording] Drafted with the Research Communication Engine and Claude Opus 5.5 from the project's saved artifacts; the authors are responsible for its content.

