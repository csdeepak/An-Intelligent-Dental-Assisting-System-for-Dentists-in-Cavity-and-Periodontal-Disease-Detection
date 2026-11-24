"""Review round 1 (23 Nov 2026), batch 1: text corrections that need no new measurement.
Each replacement asserts that its old text is present, so a stale run fails loudly.
Dispositions: research_paper/reviewer_report.md. Run from the repo root."""
from pathlib import Path

p = Path("research_paper/paper.md")
s = p.read_text(encoding="utf-8")
R = [
# --- Abstract (A3, C8, A8, C3)
("from 78 held-out radiographs the rule recovers",
 "fitted on 78 radiographs excluded from scoring because our models trained on them, the rule recovers"),
("The F1 of a tooth list that never reads the image has a closed form: the best list holds exactly the teeth whose caries prevalence exceeds half its F1,",
 "Applying the known result that the F1-optimal threshold is half the optimal F1, the best tooth list that never reads the image holds exactly the teeth whose caries prevalence exceeds half its F1;"),
("and led the constant on the external sites by 9.28 points of lesion agreement [+4.72, +13.73] while flagging fewer teeth, at three of the four sites.",
 "and led the constant on four external sites by 9.28 points of lesion agreement [+4.72, +13.73] while flagging fewer teeth; treated as a sample of sites the lead is +9.61 [-0.54, +19.76], so it is not shown for an unseen site, and those sites had informed its adoption."),
# --- Introduction (B15, B13, B9, C10, C19, C2/A9, C7)
("A panoramic dental radiograph, or orthopantomogram (OPG), is a single X-ray of both jaws, unrolled into one wide image (Figure 1).",
 "A panoramic dental radiograph, or orthopantomogram (OPG), is a single X-ray of both jaws, unrolled into one wide image (Figure 1). This project set out to build a dentist-facing assistant for caries and periodontal disease on such images; the caries aim is evaluated here, and the periodontal aim was not achieved (Section VI-F)."),
("And teeth are named in the two-digit notation of the FDI (Fédération Dentaire Internationale):",
 "And teeth are named in the two-digit notation of the FDI World Dental Federation (ISO 3950):"),
("Caries dissolves mineral, so a lesion appears as a darker (radiolucent) region inside the bright tooth; fillings and crowns are the brightest objects in the image.",
 "Caries dissolves mineral, so a lesion appears as a darker (radiolucent) region inside the bright tooth; fillings and crowns are the brightest objects in the image. Panoramic images also show radiolucencies that are not caries, such as cervical burn-out, Mach bands and overlapping contacts, and they detect proximal caries less accurately than bitewings [@akarslan2008comparison], so every caries label in this paper is a panoramic reading."),
("Agreement on one development cohort therefore cannot separate the two explanations; agreement on external cohorts, paired with the constant and reported per site, can.",
 "Agreement on one development cohort therefore cannot separate the two explanations; agreement on external cohorts, paired with the constant and reported per site, is necessary but not sufficient, because ordinary domain shift predicts the same pattern (Table 8)."),
("In panoramic caries detection, external validation is rare and, in the 49 task-relevant papers of our own survey, we noticed no image-blind baseline (an observation, not a systematic count).",
 "In panoramic caries detection, external validation is rare and, in the 49 task-relevant papers of our own structured review of 117 papers on tooth detection, caries and periodontal bone loss, we noticed no image-blind baseline (an observation from reading, not a systematic count)."),
("1. A short theory of tooth-level caries scoring — the error chain of a tooth-indexed report, the closed-form F1 of an image-blind constant and its selection rule, the cohort dependence of lesion agreement, and a testable signature of a positional shortcut — each checked against our data (Section III, Table 8) {C002}.",
 "1. An application of F1-optimal thresholding [@lipton2014optimal] to tooth-level caries scoring — the error chain of a tooth-indexed report, the F1 of an image-blind constant and its selection rule, the cohort dependence of lesion agreement, and a signature of a positional shortcut — each set against our data post hoc (Section III, Table 8) {C002}."),
("3. A pre-registered reformulation of the caries stage as lesion detection, which led the constant on the pooled external sites while flagging fewer teeth (Section VI-D) {C004}.",
 "3. A reformulation of the caries stage as lesion detection under an adoption rule committed before training, which led the constant on the pooled external sites while flagging fewer teeth; the change of task is confounded with a new training mixture (Section VI-D) {C004}."),
# --- Related work (C17)
("Classifying a cropped tooth is easier than numbering under detector output, where teeth can be missed or duplicated; public datasets have been combined to predict segmentation, FDI numbers and diagnoses together [@vannistelrooij2024combining].",
 "Public datasets have been combined to predict segmentation, FDI numbers and diagnoses together [@vannistelrooij2024combining]. Classifying a correctly detected, cropped tooth is an easier task than numbering under detector output, where teeth can be missed or duplicated, so figures of the two kinds are not comparable."),
("On Tufts-derived and Chilean radiographs, a bone-loss model reached weighted F1 0.29 and could not detect severe loss [@cerda2024determining].",
 "Compared with clinicians on 40 test radiographs, a bone-loss model reached weighted F1 0.29 and could not detect severe loss [@cerda2024determining]."),
# --- Theory (A1, C2/A9, C17, A20, A2, B3/C6/A5, A4/C5, A18/C14)
("Equation (2) counts every named code as a prediction, present tooth or not, as the scorer does,",
 "Equation (2) counts every named code as a prediction, present tooth or not, as the scorer does (a constant restricted to detected teeth is scored in Section VI-B),"),
("adding a code $c \\notin S$ raises the score, $2(A+n_c)/((k+1)N+P) > 2A/(kN+P)$, if and only if",
 "adding a code $c \\notin S$ raises the score, $2(A+n_c)/((k+1)N+P) > 2A/(kN+P)$, if and only if (the set-prediction form of the result that the F1-optimal threshold on calibrated scores is half the optimal F1 [@lipton2014optimal])"),
("That first molars are the most caries-susceptible teeth is long established in caries epidemiology [@batchelor2004grouping]; the prior,",
 "That first molars are the most caries-susceptible teeth was found in children aged 5–16 [@batchelor2004grouping]; the prior,"),
("Placement is reliable: on Tufts, 92.0% [89.58, 94.06] of the boxes our pipeline codes as one of the eight molars are true first or second molars {C013}.",
 "On Tufts, a training corpus, 92.0% [89.58, 94.06] of the boxes our pipeline codes as one of the eight molars are true first or second molars, and it reaches 81.7% [77.72, 85.35] of them {C013}; placement is not measured on any external cohort."),
("This prior mass is the cohort's, as placed by our front end — 0.630 on DENTEX, 0.604 on CariesXrays, 0.591 on the four Ningxia sites, and from 0.494 to 0.709 between sites of that one cohort (Section VI) — the site effect Zech et al. found for pneumonia [@zech2018variable].",
 "This prior mass is the cohort's as placed by our front end — 0.630 on DENTEX, 0.604 on CariesXrays, 0.591 on the four Ningxia sites, and from 0.494 to 0.709 between sites of that one cohort (Section VI) — and it depends on the front end as well as on the cohort: changing only the tooth detector moved the constant's pooled Ningxia agreement from 0.399 to 0.591. Site-dependent prevalence also drove a pneumonia shortcut [@zech2018variable]."),
("Its score on teeth that are truly healthy should rise with the base rate of their position,",
 "Its score on teeth not annotated as carious should rise with the base rate of their position,"),
("Table 2 applies both tests to the pipeline's crop classifier on 863 held-out tooth crops from 34 radiographs, cut with ground-truth boxes so that the front end plays no part.",
 "Table 2 applies both tests to the pipeline's crop classifier on 863 held-out tooth crops from 34 radiographs, cut with ground-truth boxes so that the front end plays no part. Both consequences are also expected if caries is under-annotated more often on molars, or if molar crops differ in ways correlated with the label (restorations, overlap), so the test is consistent with a positional shortcut rather than proof of one."),
("| Tooth type | Crops | Carious | Base rate | Mean score, healthy | Healthy flagged | Within-type AUC |",
 "| Tooth type | Crops | Carious | Base rate | Mean score, not carious | Not carious, flagged | Within-type AUC |"),
("The classifier's mean score on healthy teeth climbs with the training base rate, from 0.075 on incisors to 0.478 on molars, and it flags 48.2% of healthy molars: the prior is doing visible work, and costs precision {C014}. Its within-type AUC is 0.745 [0.660, 0.842], above 0.5, so there is also genuine lesion signal.",
 "The classifier's mean score on teeth not annotated as carious climbs with the training base rate, from 0.075 on incisors to 0.478 on molars, and it flags 48.2% of such molars: consistent with a prior doing visible work, at a cost in precision {C014}. Its within-type AUC is 0.745 [0.660, 0.842] against a pooled AUC of 0.855, so position carries part of the ranking and there is also lesion signal; the per-type AUCs of incisors and canines rest on 8 and 5 positives and carry no interval."),
("A whole-image lesion detector receives no tooth identity: to flag a tooth it must place a box mostly inside it.",
 "A whole-image lesion detector receives no tooth code, although absolute position in the image still carries arch information: to flag a tooth it must place a box mostly inside it."),
("With four sites the DL interval is too narrow, so we also report the Hartung–Knapp–Sidik–Jonkman (HKSJ) interval [@inthout2014hartung] and a Q-profile interval for $\\tau$ [@viechtbauer2007confidence].",
 "Per-site variances are approximated from the interval widths (width/3.92). With four sites the DL interval is too narrow, so we also report the Hartung–Knapp–Sidik–Jonkman (HKSJ) interval [@inthout2014hartung], plain and with its scale truncated at one, and a Q-profile interval for $\\tau$ [@viechtbauer2007confidence]. The four Ningxia test sets are release partitions of a three-hospital study, so their independence is assumed."),
]
for a, b in R:
    assert a in s, a[:80]
    s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("batch 1 applied:", len(R))
