# Abstract and Introduction, v3: narrative arc (24 Nov 2026)

Author brief: open with the OPG as the dental X-ray dentists use routinely and read by eye; then
why reading by eye is hard, and why an AI reader inherits the same trap as pneumonia detection;
then existing solutions; end briefly with what this system adds. Abstract at most 250 words; the
Introduction follows the same arc. Supersedes `abstract_intro_v2.md`, which stays as the record of
the previous swap.

Facts are carried from `paper.md` with their `{C###}` tags, except two new, verified sources
(PubMed + Crossref, saved in `literature/abstracts_intro_v3_2026-11-24.json`):
`hennig2023frequency` (78% of 9,680 extraoral dental images in one department were OPGs) and
`schwendicke2015radiographic` (radiographic caries detection: sensitivity 0.24–0.42 for lesions of
any stage, 0.36–0.56 for dentine lesions).

Wording kept deliberately: "the most widely taken **extraoral** dental X-ray". Intraoral bitewing
and periapical films are taken more often overall, and no source here says the OPG is the most
frequent dental X-ray of all.

---

## Abstract

What does a dentist see on an X-ray, and what does a computer see? The panoramic radiograph, or orthopantomogram (OPG), is the most widely taken extraoral dental X-ray: one low-dose exposure shows every tooth and both jaws, and the dentist reads it by eye, tooth by tooth. That reading is hard. Early caries is a faint shadow that radiographs miss more often than they reveal, overlapping teeth and artefacts mimic lesions, and up to 32 teeth must be charted on every image. Artificial intelligence promises a second reader, but it inherits a trap first exposed in chest radiography, where a pneumonia model could profit from knowing which hospital an image came from. In teeth the trap is anatomical: caries clusters on the molars, so a model can score well by knowing where decay usually is without reading the image. Existing systems number teeth almost perfectly and report panoramic caries accuracies of 86–96%, but in studies of low quality, rarely tested at a second clinic and, in the papers we reviewed, never against a baseline that ignores the image. We built a six-stage assistant that detects, numbers and screens every tooth and writes a per-tooth report, and scored it beside such a baseline. Its crop classifier did not beat it; its whole-image lesion detector led it at four external sites by 9.28 points of lesion agreement, though not demonstrably at an unseen site. Its abnormality flag supports no periodontal claim.

**Index Terms**: panoramic radiography, dental caries, tooth numbering, decision support, shortcut learning, image-blind baselines, external validation, calibration, selective prediction

---

## I. Introduction

### The OPG in everyday dentistry

A panoramic dental radiograph, or orthopantomogram (OPG), is a single X-ray of both jaws, unrolled into one wide image (Figure 1). It is the most widely taken extraoral dental radiograph: in one university department, 78% of 9,680 extraoral images taken over 18 years were OPGs, each at an effective dose of about 7 µSv [@hennig2023frequency]. Dentists read it by eye for caries, bone levels, periapical lesions and missing or impacted teeth, charting each finding against a tooth. Two conventions make the OPG unfamiliar to a computer-vision reader. It is displayed as if the viewer faces the patient, so the patient's right side is on the image's left. And teeth are named in the two-digit notation of the FDI World Dental Federation (ISO 3950): the first digit is the quadrant (1 upper right, 2 upper left, 3 lower left, 4 lower right, in the patient's frame) and the second the position counted from the midline (1 central incisor to 8 third molar). Tooth 16 is therefore the upper-right first molar and 36 the lower-left one.

![Figure 1](figures/R01_opg_primer.pdf)

**Figure 1.** Reading an OPG. One held-out DENTEX radiograph (test_120) cropped to the teeth. Dotted lines separate the quadrants Q1–Q4; numbers are the FDI codes our numbering stage assigned. Yellow: the expert's seven caries annotations as released, on teeth 12, 16, 28, 35, 36, 37 and 46. Dashed: the eight-molar set {16, 17, 26, 27, 36, 37, 46, 47} named by an image-blind constant (Section III-B); seven of its codes are present here, and four of the seven annotated teeth are among them. Radiographs: DENTEX [@hamamci2023dentex], CC BY-NC-SA 4.0.

### Why reading by eye is hard

Caries dissolves mineral, so a lesion appears as a darker (radiolucent) region inside the bright tooth; fillings and crowns are the brightest objects in the image. Early lesions are faint: across 117 studies, radiographic detection found only 24–42% of carious lesions of any stage and 36–56% of those reaching the dentine, though it rarely called a sound surface carious [@schwendicke2015radiographic]. Panoramic images add their own confusions — radiolucencies that are not caries, such as cervical burn-out, Mach bands and overlapping contacts — and detect proximal caries less accurately than bitewings [@akarslan2008comparison], so every caries label in this paper is a panoramic reading. Periodontal disease is harder still: it is staged from periodontal breakdown relative to root length, tooth loss and complexity factors such as pocket depth and furcation involvement [@tonetti2018staging], so radiographic bone loss is one input to a diagnosis, not the diagnosis {C042}. This project set out to build a dentist-facing assistant for caries and periodontal disease on such images; the caries aim is evaluated here, and the periodontal aim was not achieved (Section VI-F).

### The same trap as pneumonia detection

An artificial-intelligence (AI) assistant that pre-charts findings tooth by tooth could shorten that reading — provided its findings come from the image. Chest radiography shows how that proviso fails. In a pneumonia task, sorting radiographs by hospital alone reached an area under the ROC curve (AUC) of 0.861, because prevalence differed between sites [@zech2018variable]; a learner trained to minimise error over a population will use any cue that predicts the label, a shortcut [@geirhos2020shortcut]. Teeth carry such a cue in their anatomy. Caries is not spread evenly over the mouth; in our data the first and second molars carry most of it (Figure 2). A model can therefore earn part of its score by knowing where caries usually is rather than seeing where it is in this image.

The usual metric cannot tell the two apart. An automated report must decide three things for every tooth, in sequence: that a tooth is there, which tooth it is, and whether it carries a finding. The decisions compose, so an entry is right only when all three are, and an early error cannot be repaired later: a lesion correctly recognised but attached to the wrong tooth number is a wrong report. A score that summarises only the last decision is silent about the two that condition it, and a set of tooth codes can be chosen without any image. Such a score therefore has a floor set by the prior, and means little until an image-blind constant is scored beside it {C001}. The floor also moves with the population: a constant's lesion agreement is the share of a cohort's lesions that lie on its teeth, and a model that has absorbed the prior moves with it, whereas a model that reads the lesion need not. Agreement on one development cohort cannot separate the two explanations; agreement on external cohorts, paired with the constant and reported per site, is necessary but not sufficient, because ordinary domain shift predicts the same pattern (Table 8).

### Existing solutions and their limits

Tooth numbering is the most mature step. Detect-then-classify numbering reached expert-level sensitivity with a convolutional neural network (CNN) on 222 held-out images (numbering sensitivity 0.9800) [@tuzoff2019tooth] {C040}, and later systems report class-averaged numbering accuracy of 0.9988 [@zancan2025ai]. These figures usually score correctly detected, cropped teeth, an easier task than numbering under detector output, where teeth can be missed or duplicated. Caries detection reports high figures with weaker support: a systematic review found accuracies of 86.1–96.1% on panoramic radiographs, in studies whose quality and reporting it judged low [@mohammadrahimi2022deep], and one enumeration-then-caries detector held lesion sensitivity at 0.70 internally and 0.67 externally [@bizjak2024advancing]. For bone loss, a CNN trained against the measured percentage of loss reached accuracy 0.81 [@krois2019deep], but compared with clinicians another model reached weighted F1 0.29 and could not detect severe loss [@cerda2024determining].

Few of these figures are tested elsewhere. Of 516 medical-imaging AI studies from 2018, only 31 (6%) validated externally [@kim2019design], and dental models degrade when they are: an apical-lesion model fell from F1 54.1% to 32.7% at a second centre [@krois2021generalizability]. Other fields guard against shortcuts with a baseline that withholds the input the task is about: visual-question-answering models answered from language priors while ignoring the image [@goyal2017making], and in natural-language inference a model that never sees the premise beats the majority class [@poliak2018hypothesis]. In the 49 task-relevant papers of our own structured review of 117 papers on tooth detection, caries and periodontal bone loss, we noticed no image-blind baseline (an observation from reading, not a systematic count). A reported tooth-level caries figure therefore cannot yet be read as evidence that a model reads the radiograph.

### Our solution

We built the assistant as a modular six-stage prototype — tooth detection, FDI numbering, caries localisation, caries severity, an abnormality flag and a per-tooth report — so that each stage can be measured, replaced and audited on its own {C030}, and we score it against the image-blind constant. RQ1: does tooth-level agreement separate the pipeline from that constant, on development data and on external cohorts? RQ2: does reformulating the caries stage from classifying tooth crops to localising lesions in the whole image — a task a fixed list cannot perform — separate them {C034}? RQ3: what does the pipeline show on outputs a fixed list cannot produce? The reasoning above was written down after the measurements, so it is a frame for reading the results, not a set of predictions tested in advance. The contributions are:

1. An application of F1-optimal thresholding [@lipton2014optimal] to tooth-level caries scoring: the best image-blind tooth list and its selection rule, set against our data post hoc (Section III, Table 8) {C002}.
2. A constant-baseline protocol: two metric families, three cohorts, four external sites, paired cluster-bootstrap intervals (Sections V–VI) {C003}.
3. A reformulation of the caries stage as lesion detection, adopted under a rule committed before its adopted arm was trained, which led the constant on the pooled external sites while flagging fewer teeth; the change of task is confounded with a new training mixture (Section VI-D) {C004}.
4. An evidence audit of the whole system, including its negative results: the crop classifier tracked the prior, and the abnormality flag supports no periodontal claim (Sections IV, VI-F, VIII) {C005}.
