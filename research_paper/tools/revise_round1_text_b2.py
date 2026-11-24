"""Review round 1 (23 Nov 2026), batch 2: disclosure, framing and clinical corrections from the
three reviewers and the VERIFIER (M4-M7). Every number added here was read from its artefact first
(sources in research_paper/reviewer_report.md). Asserting replacements. Run from the repo root."""
from pathlib import Path

p = Path("research_paper/paper.md")
s = p.read_text(encoding="utf-8")
R = [
# ---- Abstract (M7, B3, M6, C1)
("and show, in theory and on three cohorts, that this score mixes the pixels of the tooth with a prior over where caries usually occurs.",
 "and examine, with a post-hoc analysis and on three cohorts, how this score mixes the pixels of the tooth with a prior over where caries usually occurs."),
("but its scores on healthy teeth tracked each position's base rate,",
 "but its scores on teeth not annotated as carious tracked each position's base rate,"),
("A whole-image lesion detector, adopted under a rule written before training,",
 "A whole-image lesion detector, adopted under a rule committed before its adopted arm was trained,"),
("and found 11.0–27.5% of labelled teeth in three runs, so we make no periodontal claim.",
 "and found 11.0–27.5% of labelled teeth in three runs, about three of every four flags false, so we make no periodontal claim. The external cohort also informed the choice of tooth detector, so no external figure here is free of selection."),
# ---- Introduction (M7)
("Two consequences of the theory organise this paper.",
 "Two consequences of this view organise the paper; we wrote them down after the measurements, so they are a frame for reading the results, not predictions tested in advance."),
("4. An evidence audit of a complete six-stage system: every stage on a real radiograph, the evidence class each stage's number belongs to (Table 3), rule-chosen successes and failures, content-free controls for two vision-language models, and the negative results — a crop-level split that inflated the abnormality flag, a severity head trained on image contrast, a detector adopted against its own pre-registered guard (Sections IV, VI-F, VIII) {C005}.",
 "4. An evidence audit of a complete six-stage system: every stage on a real radiograph, the evidence class and selection history of each stage's number (Table 3), rule-chosen successes and failures, content-free controls for two vision-language models, and the negative results — a crop-level split that inflated the abnormality flag, a severity head trained on image contrast, a detector adopted against its own pre-registered guard after its external result was known (Sections IV, VI-F, VIII) {C005}."),
# ---- III-E (M7)
("The theory therefore implies that if the detector's lead over the constant comes from reading the image, it should come with fewer flagged teeth, not more, and within each tooth type its flags should be carious more often than the classifier's.",
 "If the detector's lead over the constant comes from reading the image, one would therefore expect it to come with fewer flagged teeth, not more, and within each tooth type its flags to be carious more often than the classifier's; both are also what any detector with a higher threshold would show, so they are consistent with reading, not proof of it."),
# ---- IV: system description (B2, B4, B11, B14, B10, B5)
("**Stage 3b** grades flagged teeth as caries or deep caries, the two caries labels DENTEX releases; it was validated on 133 crops in development and is not evaluated here.",
 "**Stage 3b** grades flagged teeth as caries or deep caries, the two caries labels DENTEX releases; it was tuned and validated on the same 133 development crops, has no test, and its grade in the report is unvalidated."),
("Its severity head is withheld from the report by default.",
 "Its severity head is withheld from the report by default. For backward compatibility the report still names this field and its positive value `bone_loss`; the field carries the abnormality label described here."),
("the whole system runs at 1.70 s per image on a laptop CPU with no GPU [ASK AUTHOR: CPU model] {C031}.",
 "the whole system ran at 1.70 s per image on a laptop CPU with no GPU, measured before the Stage-4 severity head was withheld [ASK AUTHOR: CPU model] {C031}."),
("For tooth 36 of Figure 4 the record holds the code (confidence 0.9999), detection confidence 0.8389, a deep-caries finding (caries confidence 0.8892, severity 0.9579), a normal Stage-4 finding (0.7853) and an assessability flag.",
 "For tooth 36 of Figure 4 the record holds the code (confidence 0.9999), detection confidence 0.8389, a deep-caries flag (lesion-detector score 0.8892, a detection score rather than a probability; unvalidated severity score 0.9579), no Stage-4 flag (0.7853) and an assessability flag; the expert did not annotate caries on this tooth."),
("(f) The written overlay with the expert's three caries annotations (26, 45, 48) in yellow: two found, 48 missed, 36 flagged with no annotated lesion.",
 "(f) The written overlay with the expert's three caries annotations (26, 45, 48) in yellow: two found, 48 missed, 36 and 46 flagged with no annotation."),
# ---- Table 3 and its lead-in (C1, M4, A7, A14, B5)
("Table 3 states, for each stage, what its reported number is evidence of. Only two stage results are both held out from every training corpus and from model selection: the crop classifier's external caries scores and numbering on UFBA-425 {C032}.",
 "Table 3 states, for each stage, what its reported number is evidence of. Only one stage result is held out from every training corpus and from model selection: numbering on UFBA-425. The crop classifier's external scores are free of its own training and selection, but the current tooth detector was chosen after its Ningxia result was known {C032}."),
("| 3a Crop classifier | ResNet18, 11.18 M | DENTEX crops | 863 test crops, AP 0.550 | Ningxia +0.89 (level); CariesXrays -22.42 | the cleanest external test |",
 "| 3a Crop classifier | ResNet18, 11.18 M | DENTEX crops | 863 test crops, AP 0.550 | Ningxia +0.89 (level); CariesXrays -22.42 | external to the classifier; Ningxia informed the detector choice |"),
("| 3b Severity | ResNet18, 11.18 M | DENTEX | 133 validation crops, no test | none | no claim |",
 "| 3b Severity | ResNet18, 11.18 M | DENTEX | 133 validation crops, no test | none | no claim; grade unvalidated |"),
("| 4a Abnormality flag | ResNet18, 11.18 M | Tufts, radiograph split | three runs: sens. 27.5%, 16.5%, 11.0% at spec. 95.9–98.6% | none | one sentence; not periodontal |",
 "| 4a Abnormality flag | ResNet18, 11.18 M | Tufts, radiograph split | three runs: sens. 27.5%, 16.5%, 11.0% at spec. 95.9–98.6%; PPV 0.25–0.29 | none | one sentence; not periodontal |"),
("| 4b Its severity | ResNet18, 11.18 M | Tufts | retrain macro-F1 0.294 vs prior 0.334 | none | withheld |",
 "| 4b Its severity | ResNet18, 11.18 M | Tufts | retrain macro-F1 0.294, 0.328, 0.382 (three seeds) vs prior 0.334 | none | withheld |"),
# ---- V: cohorts, selection (M6, C1, M4, A7, B9)
("**Cohorts** (Table 4). All splits are image-level, chosen so that no radiograph contributes to both training and evaluation {C033}.",
 "**Cohorts** (Table 4). Splits are by image, chosen so that no radiograph contributes to both training and evaluation; the releases carry no patient identifiers, so a patient's second radiograph cannot be excluded, and one re-rendered Tufts radiograph (test 248) duplicates a training radiograph (1017) and holds no Stage-4 positive. The exception is Stage 4's first model, whose crop-level split is discussed in Section VI-F {C033}."),
("which we treat as four sites. No model was trained or tuned on Ningxia.",
 "which we treat as four sites. No model was trained or tuned on Ningxia, but it is not blind: its caries images had been scored in 20 full passes by the time the current tooth detector was chosen, and that choice was made with the detector's Ningxia result in view."),
("All datasets are public, de-identified releases; no new patient data were collected.",
 "All datasets are public, de-identified releases; no new patient data were collected. Each cohort carries one released annotation per image; the number of readers and whether annotation was exhaustive are not stated in what we used, and DENTEX and Ningxia include only radiographs with findings, so specificity cannot be estimated on them."),
("| Ningxia, 4 sites | 337 | 1,013 lesions | external; never trained on; informed the lesion detector's adoption |",
 "| Ningxia, 4 sites | 337 | 1,013 lesions | external; never trained on; informed the lesion detector's adoption and the tooth-detector choice |"),
("**Pre-registration and departures from it.** The lesion detector's adoption rule — score above both the constant and the crop classifier on at least two of three cohorts, at no more than 1.5 times their rate of flagged teeth — was committed before any arm was trained {C016}. The current tooth detector was made the default by a dated decision against two of its own pre-registered guards, and every comparison in Section VI was re-measured under it with the previous detector as a same-machine control {L002}.",
 "**Committed rules and departures from them.** The lesion detector's adoption rule — score above both the constant and the crop classifier on at least two of three cohorts, at no more than 1.5 times their rate of flagged teeth — was committed to the (private) repository before the adopted pooled arm was trained; the single-corpus arm reused a detector trained two days earlier, whose result the rule's rationale cites, and one of the three cohorts was the lesion detector's own validation split {C016}. Both arms were scored on the same cohorts and the pooled arm, the one that met the rule, was adopted. The current tooth detector was made the default by a dated decision against the failed Tufts guard of its own pre-registration (an earlier multi-corpus arm had failed a similar guard), after its DENTEX and Ningxia results were known; every comparison in Section VI was re-measured under it with the previous detector as a same-machine control {L002}."),
# ---- VI-A (M6)
("on the frozen Tufts test split it missed its pre-registered guard (within four points of a Tufts-only control: 0.587 against 0.723) and was adopted regardless, by a dated decision, for its numbering and caries behaviour {C017}.",
 "on the frozen Tufts test split it missed its pre-registered guard (within four points of a Tufts-only control: 0.587 against 0.723) and was adopted regardless, by a dated decision, for its numbering and caries behaviour, measured on the scored DENTEX images and Ningxia {C017}."),
# ---- VI-B (A11, C16)
("The VLMs are level with constants of their own volume (32B [-4.90, +5.63], 7B [-2.06, +4.85]): they fall below the eight molars by naming fewer teeth, and their F1 carries no detectable image information.",
 "The VLMs are level with constants of their own volume (32B [-4.90, +5.63], 7B [-2.06, +4.85]): they fall below the eight molars by naming fewer teeth, and within those intervals their F1 shows no image information. Only one prompt was tried; giving the 7B model two or four examples lowered its F1 to 0.066 and 0.034."),
# ---- VI-D (M5, C11, C5, A4, C7, C9)
("none separated from zero, including a retrain with 2.67 times the carious crops, so the ceiling is not set by supervision {C024}. Section III-D locates it in the task as posed — a tight crop, a binary label and a strong prior.",
 "none separated from zero, including a retrain with 2.67 times the carious crops; that retrain was underpowered and did not enlarge the negative class, so it does not rule out a supervision-side limit {C024}."),
("Under the tooth detector of the time, the lesion detector met the pre-registered rule on two cohorts of three:",
 "Under the tooth detector of the time, the lesion detector met the committed rule on two cohorts of three, one of them its own validation split:"),
("Both implications of Section III-E hold. The lead comes with fewer flags:",
 "Both observations Section III-E anticipates are present, but neither is controlled for operating point. The lead comes with fewer flags:"),
("46.3% of the molars it flags carry caries, against 28.4% for the crop classifier and 21.8% for the constant, and 39.7% of its flagged premolars against 17.0% {C027}.",
 "46.3% of the molars it flags carry caries, against 28.4% for the crop classifier and 21.8% for the constant, and 39.7% of its flagged premolars against 17.0%, but it flags 447 molars to the classifier's 1,023, and precision usually rises as flags fall {C027}."),
("Per site (Figure 6b) it is separated from the constant at test2, test3 and test4",
 "Per site (Figure 6b), without correction for four comparisons, it is separated from the constant at test2, test3 and test4"),
("and not at test1 (-3.16 [-10.56, +3.97]), where the constant is strongest.",
 "and not at test1 (-3.16 [-10.56, +3.97]), where the constant is strongest; the lower bounds at test3 and test4 are close to zero."),
("Treating the sites as a sample (random effects, post hoc) gives +9.61 [-0.54, +19.76] (HKSJ [-5.02, +24.24]),",
 "Treating the sites as a sample (random effects, post hoc) gives +9.61 [-0.54, +19.76] (HKSJ [-5.02, +24.24], truncated [-6.88, +26.09]),"),
("The training mixture, not the architecture, transfers:",
 "The training mixture explains much of the transfer:"),
# ---- VI-E (A10, C15)
("and the crop classifier's from 0.797 to 0.940 (+14.25 [+11.32, +16.63], 34 clusters) {C035}.",
 "and the crop classifier's from 0.797 to 0.940 (+14.25 [+11.32, +16.63], 34 clusters) {C035}; at full coverage the classifier is below the 0.853 of always answering not carious, so accuracy flatters neither end of this curve."),
("Temperature scaling made it worse (0.152); isotonic regression reduced it to 0.043",
 "Temperature scaling made it worse (0.152); isotonic regression, fitted on the validation split and tested on crops cut with ground-truth boxes, reduced it to 0.043"),
# ---- VI-F (M5, A14, B5)
("Shown no anatomy, the VLMs return the population prior: Qwen2.5-VL-7B answers 26,36 to a blank grey image, to random noise and to a real radiograph, and Qwen2.5-VL-32B answers noise with exactly the constant's eight molars (one prompt; decoding settings not recorded) {C037}.",
 "Shown no anatomy, the VLMs mostly return the population prior: Qwen2.5-VL-7B answers 26,36 to a blank grey image, to random noise and to a real radiograph, and Qwen2.5-VL-32B answers NONE to the blank image but noise with exactly the constant's eight molars (one prompt; decoding settings not recorded) {C037}."),
("on 143 held-out radiographs at 95.9–98.6% specificity {C038}.",
 "on 143 held-out radiographs at 95.9–98.6% specificity, with positive predictive values of 0.25–0.29 and 0.36–1.06 false flags per radiograph; on the DENTEX images the default flags 6.1% of detected teeth {C038}."),
("Its severity head (macro-F1 0.294 [0.214, 0.385] against 0.334 for an image-blind position prior) stays withheld, and we make no periodontal claim {L004}.",
 "Its severity head, retrained on the intended overlap bands (macro-F1 0.294 [0.214, 0.385] for the pre-specified seed, 0.328 and 0.382 for the others, against 0.334 for an image-blind position prior), stays withheld, and we make no periodontal claim {L004}."),
# ---- VII (C12, M7, A2, A12, C18, B6, B8, C17)
("The theory of Section III was formulated after the measurements, so Table 8 is a consistency check, not a test of predictions made in advance. Five of its implications hold, the last only at three of four sites; one of them is also expected under ordinary domain shift and does not single out the theory. One is not supported — the prior inflates the classifier's thresholded scores, but its ranking within a tooth type carries real image signal {C006}.",
 "The analysis of Section III was formulated after the measurements, so Table 8 is a consistency check, not a test of predictions made in advance. The first row is an identity of the constant's definition, not an empirical result. Of the rest, three are consistent with the data with stated confounds, one is not specific to the theory, and one is not supported — the prior inflates the classifier's thresholded scores, but its ranking within a tooth type carries image signal {C006}."),
("| Rule (3) gives the best constant | reproduces the fitted eight molars; recall 0.600 = carious share at them | holds |",
 "| Rule (3) gives the best constant | reproduces the fitted eight molars; recall 0.600 = carious share at them | identity (check of the arithmetic) |"),
("| The floor moves with the cohort | constant's agreement 0.494–0.709 across four sites | holds |",
 "| The floor moves with the cohort | constant's agreement 0.494–0.709 across four sites; 0.399 to 0.591 with the detector alone | consistent; confounded with the front end |"),
("| Shortcut lifts healthy scores | healthy score 0.075 (incisors) to 0.478 (molars); 48.2% of healthy molars flagged | holds |",
 "| Shortcut lifts non-carious scores | not-carious score 0.075 (incisors) to 0.478 (molars); 48.2% of such molars flagged | consistent; label noise and molar confounders not excluded |"),
("| Localising: fewer, better flags | Ningxia +9.28, 4.35 vs 7.15 flags/image; DENTEX molar flags 46.3% vs 28.4% carious | 3 of 4 sites |",
 "| Localising: fewer, better flags | Ningxia +9.28, 4.35 vs 7.15 flags/image; DENTEX molar flags 46.3% vs 28.4% carious | 3 of 4 sites; volume not matched |"),
("**RQ1.** The same metric moves 40 points across cohorts and 31 across one cohort's sites, so a favourable tooth-level figure on development data is weak evidence of perception {C007}.",
 "**RQ1.** The classifier-minus-constant difference runs from +17.12 on DENTEX to -22.42 on CariesXrays (the matching rule differs on DENTEX, so this span is approximate) and over 31 points across one cohort's sites under one rule, so a favourable tooth-level figure on development data is weak evidence of perception {C007}."),
("**RQ2.** A detector that must place lesion boxes can express a positional prior only at a cost in precision (Section III-E). It led the constant on the external sites with fewer flags, and on the development corpus its flags were carious more often within each tooth type.",
 "**RQ2.** A detector that must place lesion boxes can express a positional prior only at a cost in precision (Section III-E). It led the constant on the external sites with fewer flags, and on the development corpus its flags were carious more often within each tooth type, at a lower volume."),
("and images of what the system does (Figures 4, 5 and 7),",
 "images of what the system does (Figures 4 and 7) and its training curves (Figure 5),"),
("Third, every stage's confidence is a model score; only the crop classifier's has been calibrated, and only on development data. A dentist using such a system would need to read every radiograph as before; the measurements here support its use as a second reader in research, not as a screening or diagnostic device, and no regulatory or clinical-trial evidence exists for it [@kelly2019key].",
 "Third, every stage's confidence is a model score; only the crop classifier's has been calibrated, and only on development data. Externally, 31.6% of Ningxia lesions did not lie on a flagged tooth, a misnumbered tooth carries its finding to the wrong site in the report, and a flag on an unannotated or restored tooth risks unnecessary treatment if it is acted on. No result here concerns deciduous or mixed dentition, implants or pontics, which the evaluations do not measure separately. Intended use: a research tool for studying decision support on adult panoramic radiographs, whose every finding a dentist confirms on the image; it is not a screening or diagnostic device, and no regulatory or clinical-trial evidence exists for it. Clinical value would need prospective evaluation [@kelly2019key]."),
# ---- VIII (C13, C20, A7)
("- The theory treats codes independently and was checked on one corpus (78 and 164 images); the shortcut test rests on 34 radiographs; the lesion detector has no calibration curve {L007}.",
 "- The constant is optimal only in-sample, on 78 training radiographs selected for containing caries, and the analysis was checked on one corpus (78 and 164 images); the shortcut test rests on 34 radiographs; the lesion detector has no calibration curve {L007}."),
("the caries severity grade shown in reports has no test {L010}.",
 "the caries severity grade shown in reports has no test; we could not verify whether CariesXrays and a Ningxia hospital share a site or scanner {L010}."),
# ---- IX (C3)
("and a lesion detector led it on four pooled external sites with fewer flags.",
 "and a lesion detector led it on four pooled external sites with fewer flags, a lead not shown for an unseen site and measured on sites that informed its adoption."),
# ---- Data availability (B12)
("the lesion detector's adoption rule is committed there before training [ASK AUTHOR: public anchor for the pre-registration commit].",
 "the lesion detector's adoption rule is committed there before its adopted arm was trained [ASK AUTHOR: public anchor for the commit]."),
]
for a, b in R:
    assert a in s, a[:90]
    s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("batch 2 applied:", len(R))
