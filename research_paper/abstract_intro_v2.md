# Alternative Abstract and Introduction (v2, 24 Nov 2026)

Problem-first restructuring of the Abstract and Section I of `paper.md`. **Swapped in on 24 Nov 2026**
by `tools/swap_abstract_intro_v2.py`, which also condensed Section II to Datasets, a "Further related
work" paragraph holding every citation the new Section I does not carry, and Calibration; it asserts
that no citation or `{C###}` tag was dropped. `paper.tex`, `final_research_paper.pdf` and the Turnitin
copy were rebuilt. This file stays as the source of the swapped text. Every number and citation below is carried
from the current `paper.md` (same `{C###}` claim tags, same bib keys); nothing new is claimed.

Proportions, measured by word count (citation keys and claim tags excluded; Introduction
excludes the Figure 1 caption):

| Part | Abstract (≈290 words) | Introduction (≈1,120 words) |
|---|---|---|
| The problem | 53% | 50% (clinical 24% + measurement 26%) |
| Existing solutions | 27% | 26% |
| This work | 20% | 24% |

If the Introduction absorbs the literature, Section II (Related Work) should be cut to the
datasets paragraph plus what the Introduction does not cover (calibration, abstention, VLMs),
or the two will repeat each other.

---

## Abstract

Panoramic dental radiographs show both jaws in one image, and dentists read them tooth by tooth for caries, bone levels and missing teeth. An assistant that pre-charts these findings could shorten that reading, but only if its findings come from the image, and two features of the task make that hard to establish. The radiograph is a limited caries instrument: it shows radiolucencies that are not caries and detects proximal lesions less accurately than bitewings, so every label is itself a panoramic reading. And caries is not spread evenly over the mouth — the first and second molars carry most of it — while the usual tooth-level score counts only which teeth a system marks as carious. A model can therefore score well by knowing where caries usually occurs rather than seeing where it is, and the score cannot tell the two apart, because a list of tooth codes can be chosen without any image.

Published systems number teeth at expert-level sensitivity and report panoramic caries accuracies of 86.1–96.1%, in studies a systematic review judged to be of low quality; one caries detector held lesion sensitivity at 0.70 internally and 0.67 externally. External validation is rare in medical imaging, and dental models tested at a second centre lose accuracy. Input-blind baselines expose such priors in visual question answering and language inference, but in the panoramic caries work we read we found none.

We built a six-stage system and scored it beside an image-blind constant naming the eight molars (F1 0.320). Its crop classifier did not separate from that constant; a whole-image lesion detector led it on four external sites by 9.28 points of lesion agreement [+4.72, +13.73], though not demonstrably for an unseen site. We make no periodontal claim.

**Index Terms**: panoramic radiography, dental caries, tooth numbering, decision support, shortcut learning, image-blind baselines, external validation, calibration, selective prediction

---

## I. Introduction

### The clinical problem

A panoramic dental radiograph, or orthopantomogram (OPG), is a single X-ray of both jaws, unrolled into one wide image (Figure 1). Dentists read it for caries, bone levels, periapical lesions and missing or impacted teeth, and an artificial-intelligence (AI) assistant that pre-charts these findings tooth by tooth could shorten that reading — provided its findings come from the image. Two conventions make the OPG unfamiliar to a computer-vision reader. It is displayed as if the viewer faces the patient, so the patient's right side is on the image's left. And teeth are named in the two-digit notation of the FDI World Dental Federation (ISO 3950): the first digit is the quadrant (1 upper right, 2 upper left, 3 lower left, 4 lower right, in the patient's frame) and the second the position counted from the midline (1 central incisor to 8 third molar). Tooth 16 is therefore the upper-right first molar and 36 the lower-left one.

The image is also an imperfect witness to disease. Caries dissolves mineral, so a lesion appears as a darker (radiolucent) region inside the bright tooth; fillings and crowns are the brightest objects in the image. But panoramic images also show radiolucencies that are not caries, such as cervical burn-out, Mach bands and overlapping contacts, and they detect proximal caries less accurately than bitewings [@akarslan2008comparison], so every caries label in this paper is a panoramic reading. Periodontal disease is harder still: it is staged from periodontal breakdown relative to root length, tooth loss and complexity factors such as pocket depth and furcation involvement [@tonetti2018staging], so radiographic bone loss is one input to a diagnosis, not the diagnosis {C042}.

![Figure 1](figures/R01_opg_primer.pdf)

**Figure 1.** Reading an OPG. One held-out DENTEX radiograph (test_120) cropped to the teeth. Dotted lines separate the quadrants Q1–Q4; numbers are the FDI codes our numbering stage assigned. Yellow: the expert's seven caries annotations as released, on teeth 12, 16, 28, 35, 36, 37 and 46. Dashed: the eight-molar set {16, 17, 26, 27, 36, 37, 46, 47} named by an image-blind constant (Section III-B); seven of its codes are present here, and four of the seven annotated teeth are among them. Radiographs: DENTEX [@hamamci2023dentex], CC BY-NC-SA 4.0.

### The measurement problem

An automated report must decide three things for every tooth, in sequence: that a tooth is there, which tooth it is, and whether it carries a finding. The decisions compose, so an entry is right only when all three are, and an early error cannot be repaired later: a lesion correctly recognised but attached to the wrong tooth number is a wrong report. A score that summarises only the last decision is silent about the two that condition it.

The last decision itself draws on two sources of evidence: the pixels of the tooth, and the tooth's identity. Caries is not spread evenly over the mouth; in our data the first and second molars carry most of it (Figure 2). A learner trained to minimise error over a population will use any cue that predicts the label, and position predicts it, so a model can earn part of its score by knowing where caries usually is rather than seeing where it is in this image — a shortcut [@geirhos2020shortcut]. The usual metric cannot tell the two apart, because a set of tooth codes can be chosen without any image. Such a score therefore has a floor set by the prior, and means little until an image-blind constant is scored beside it {C001}. The floor also moves with the population: a constant's lesion agreement is the share of a cohort's lesions that lie on its teeth, and a model that has absorbed the prior moves with it, whereas a model that reads the lesion need not. Agreement on one development cohort cannot separate the two explanations; agreement on external cohorts, paired with the constant and reported per site, is necessary but not sufficient, because ordinary domain shift predicts the same pattern (Table 8).

### Existing solutions and their limits

Tooth numbering is the most mature step. Detect-then-classify numbering reached expert-level sensitivity with a convolutional neural network (CNN) on 222 held-out images (numbering sensitivity 0.9800) [@tuzoff2019tooth] {C040}, and later systems report class-averaged numbering accuracy of 0.9988 [@zancan2025ai]. These figures usually score correctly detected, cropped teeth, an easier task than numbering under detector output, where teeth can be missed or duplicated.

Caries detection reports high figures with weaker support. A systematic review found accuracies of 86.1–96.1% on panoramic radiographs, in studies whose quality and reporting it judged low [@mohammadrahimi2022deep]; one enumeration-then-caries detector held lesion sensitivity at 0.70 internally and 0.67 externally [@bizjak2024advancing]. For bone loss, a CNN trained against the measured percentage of loss reached accuracy 0.81 [@krois2019deep], but compared with clinicians another model reached weighted F1 0.29 and could not detect severe loss [@cerda2024determining].

Few of these figures are tested elsewhere. Of 516 medical-imaging AI studies from 2018, only 31 (6%) validated externally [@kim2019design], and dental models degrade when they are: an apical-lesion model fell from F1 54.1% to 32.7% at a second centre [@krois2021generalizability]. Other fields have a tool for the shortcut problem — a baseline that withholds the input the task is about. Visual-question-answering models answered from language priors while ignoring the image [@goyal2017making], a model that never sees the premise beats the majority class in natural-language inference [@poliak2018hypothesis], and sorting chest radiographs by hospital alone reached an area under the ROC curve (AUC) of 0.861 for pneumonia [@zech2018variable]. In the 49 task-relevant papers of our own structured review of 117 papers on tooth detection, caries and periodontal bone loss, we noticed no image-blind baseline (an observation from reading, not a systematic count). A reported tooth-level caries figure therefore cannot yet be read as evidence that a model reads the radiograph.

### This work

We set out to build a dentist-facing assistant for caries and periodontal disease, and designed it as a modular six-stage prototype — tooth detection, FDI numbering, caries localisation, caries severity, an abnormality flag and a per-tooth report — so that each stage can be measured, replaced and audited on its own {C030}. We ask three questions. RQ1: does tooth-level agreement separate the pipeline from an image-blind constant, on development data and on external cohorts? RQ2: does reformulating the caries stage from classifying tooth crops to localising lesions in the whole image — a task a fixed list cannot perform — separate them {C034}? RQ3: what does the pipeline show on outputs a fixed list cannot produce? The reasoning above was written down after the measurements, so it is a frame for reading the results, not a set of predictions tested in advance. The contributions are:

1. An application of F1-optimal thresholding [@lipton2014optimal] to tooth-level caries scoring: the best image-blind tooth list and its selection rule, set against our data post hoc (Section III, Table 8) {C002}.
2. A constant-baseline protocol: two metric families, three cohorts, four external sites, paired cluster-bootstrap intervals (Sections V–VI) {C003}.
3. A reformulation of the caries stage as lesion detection, adopted under a rule committed before its adopted arm was trained, which led the constant on the pooled external sites while flagging fewer teeth; the change of task is confounded with a new training mixture (Section VI-D) {C004}.
4. An evidence audit of the whole system, including its negative results: the crop classifier tracked the prior, and the abnormality flag supports no periodontal claim (Sections IV, VI-F, VIII) {C005}.
