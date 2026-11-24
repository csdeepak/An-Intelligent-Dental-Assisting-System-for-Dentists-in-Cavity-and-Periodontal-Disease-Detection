# Reviewer C — methodology, statistics and scientific integrity

Manuscript: "Reading the Radiograph or the Prior? A Tooth-Level Panoramic Analysis System Evaluated
Against Image-Blind Baselines and External Cohorts" (`research_paper/paper_clean.md`, source of
`final_research_paper.pdf`). Bibliography: `research_paper/references.bib`.

Sources consulted: the manuscript; `docs/results/RESULTS_LOG.md` (entries 2026-08-27r/s,
2026-10-11f, 2026-10-11g, 2026-10-12b, 2026-11-02d); `outputs/stage1_switch/PRE_REGISTRATION.md`
(with Amendments 1–4); `outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md`;
`outputs/lever_b_eval/acceptance_rule_B-pooled.json`; `outputs/review_round1/README.md` and
`constant_stability_and_curve.json`; saved abstracts in `research_paper/literature/*.json` and
`outputs/citation_audit/2026-11-02_ars/{claim_abstracts,new_abstracts}.json`; two web searches
(Lipton et al. 2014; Li et al. 2024 dataset description). I recomputed the DerSimonian–Laird,
HKSJ and prediction-interval figures from the per-site intervals printed in Section VI-D.

---

## Summary

The paper builds a six-stage panoramic-radiograph pipeline and argues that tooth-level caries
scores conflate image evidence with a positional prior. It (i) derives the F1 of an image-blind
"constant" tooth list and the rule that selects the F1-optimal list (the eight first/second molars
on DENTEX, F1 0.320 on 164 scored images); (ii) compares two Stage-3a implementations (a per-crop
ResNet18 classifier and a whole-image YOLOv11l lesion detector), two zero-shot VLMs and the
constant on DENTEX, CariesXrays and four Ningxia test sets, using FDI-set F1 and "lesion
agreement" with paired cluster-bootstrap intervals; (iii) tests a "positional-shortcut signature"
on the crop classifier; (iv) reports numbering, abstention and calibration as outputs a constant
cannot produce; and (v) reports a sequence of negative results, including an abnormality flag that
is explicitly not a periodontal model.

The paper is unusually candid and most of its numbers trace exactly to saved artefacts. Its
central empirical claims are, however, weaker than the abstract and conclusion convey, for three
reasons: the closed-form theory is a direct corollary of a known result that is not cited; the
external cohort that carries the positive lesion-detector result was not blind to two adoption
decisions (only one is disclosed), and the paper's own evidence table misstates this; and the
"fewer, better flags" test of Section III-E does not control for operating point and so cannot
separate "reads the image" from "operates at a stricter threshold".

## Major strengths

1. **Image-blind baseline placed beside every number, with a matched-volume variant.** The matched
   constant (Table 5, "Matched") is a good control: it removes the "more flags, more hits"
   explanation for both pipeline leads on FDI-set F1.
2. **Traceability.** Every number I checked reproduces from saved artefacts: 286 TP / 1,312 named /
   477 carious → F1 0.3197, recall 0.5996, precision 0.218; lesion detector 274/350/203 → F1
   0.498, 42.6% missed; crop classifier 365/1,172/112 → F1 0.363; refit stability (26.7% exactly
   the eight molars, 45.3% seven codes, median 0.3197, 95% range [0.279, 0.330]); per-site
   intervals and pooled +9.28 [+4.72, +13.73] (`RESULTS_LOG` 2026-10-11g).
3. **The meta-analytic figures are correct.** From the four per-site intervals (normal
   approximation) I obtain Q = 15.79, I² = 81.0%, τ = 9.27, DL mean 9.61 [−0.54, +19.76], HKSJ
   [−5.02, +24.24], prediction interval with t₂ [−36.08, +55.29] — identical to Section VI-D.
4. **Negative results are reported, not buried:** VLMs below the constant; the crop classifier
   level with the constant externally and far below it on CariesXrays (−22.42); five failed
   repairs (Table 6); a crop-level leak that inflated Stage 4 (0.923 macro-F1 → 3.4% on unseen
   radiographs); a severity head trained on contrast; a detector adopted against its guard; the
   single-corpus lesion detector collapsing to 0.086 on DENTEX.
5. **Pre-registration discipline.** Adoption rules and re-measurement protocols were frozen before
   runs, departures are dated, and same-machine controls are used for detector comparisons.
6. **Within-type AUC** (Table 2) is the right way to strip the positional cue from a ranking, and
   the authors accept its unfavourable verdict ("not supported", Table 8).

## Major weaknesses

1. **The closed-form rule is a known result.** Equation (3) and the "prefix" optimum are the
   empirical-F1 form of Lipton, Elkan and Narayanaswamy (ECML-PKDD 2014, "Optimal Thresholding of
   Classifiers to Maximize F1 Measure", doi:10.1007/978-3-662-44851-9_15), whose central result is
   that the F1-optimal threshold on calibrated scores is half the optimal F1. An image-blind
   constant is a classifier whose score for (image, code) is p_c; thresholding it at F1*/2 is
   exactly rule (3). Related work on F-measure-optimal set prediction (e.g. Waegeman et al., JMLR
   2014; Ye et al., ICML 2012) is also absent. Contribution 1 ("the closed-form F1 of an
   image-blind constant and its selection rule") is presented as new theory; it is an application.
   The derivation is still useful in this setting, but the novelty claim must be cut back and the
   prior result cited.
2. **Ningxia was not blind to the Stage-1 detector choice, and Table 3 says the opposite.** The
   decision record (`RESULTS_LOG` 2026-10-11f) states that the crop-classifier ("gate") Ningxia
   result under the new detector (0.407 → 0.600) "was known when this decision was made, and
   Ningxia is therefore no longer blind to the choice of Stage-1 detector"; 2026-10-11g repeats
   this as a required disclosure. The manuscript discloses only that Ningxia "informed the lesion
   detector's adoption" (Table 4, V, VIII). Table 3's sentence "Only two stage results are both
   held out from every training corpus and from model selection: the crop classifier's external
   caries scores and numbering on UFBA-425", and its label "the cleanest external test", are
   therefore false for the crop classifier's Ningxia score: the 0.600 that appears in the
   abstract ("level with the constant") is the very number seen before the front end was adopted.
   The same records state that the Ningxia caries images had been scored in 20 full passes by
   11 Oct; the manuscript does not report the number of passes.
3. **The pre-registered adoption rule counted a selection-contaminated cohort.** The Lever B rule
   (`outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md` §4, §6) required a lead on ≥2 of 3
   cohorts, one of which is the 1,200-image CariesXrays split that also selected the detector's
   checkpoint (Section VI-A: "Each checkpoint is the best on its run's validation split"; Figure
   5b), and it applied "for the better of B-single / B-pooled", i.e. it embedded an arm selection
   on the evaluation cohorts. The rule was met on CariesXrays and Ningxia; the only fully clean
   cohort (DENTEX) was a tie. The paper says the detector was "adopted under a rule written before
   training", which is true but incomplete: pre-registration did not protect against these two
   selection channels, and neither is stated where the adoption is described (Sections V, VI-D).
4. **Section III-E's test does not identify perception.** "Fewer, better flags" is what any scorer
   produces when moved to a stricter operating point. The within-type comparison (DENTEX molar
   flags carious 46.3% for the detector vs 28.4% for the classifier) compares the detector at 624
   flags with the classifier at 1,537. Because the classifier has within-type AUC 0.745 (Table 2),
   raising its threshold would also raise its within-type precision. The comparison that would
   support the claim is the classifier thresholded to the detector's volume (overall and per tooth
   type), or within-type precision–recall curves for both. Without it, the "both implications of
   Section III-E hold" statement and the Table 8 row "Localising: fewer, better flags" are not
   evidence that the detector reads the image better. In addition, a CNN detector can encode a
   positional prior through absolute image location (molars occupy fixed lateral regions of an
   OPG), so "receives no tooth identity" does not mean "cannot express a positional prior"; no
   content-free control (blank, noise, mirrored or tooth-masked images) was run on the detector,
   although one was run on the VLMs.
5. **The shortcut signature (Section III-D) has unaddressed alternatives.** Rising mean scores on
   "healthy" teeth with tooth-type base rate is also predicted by (a) prevalence-proportional label
   noise — the negative class is largely recovered by MD5 join from another DENTEX subset
   (`RESULTS_LOG` 2026-08-27r), DENTEX labels only a minority of teeth, and unannotated caries will
   be most frequent among "healthy" molars; and (b) type-specific visual difficulty (molars carry
   more restorations and overlap). Limitations mention (a) only for the constant. The test is on 34
   radiographs, with 8 carious incisors and 5 carious canines; no per-type intervals are given.
6. **The change of task is confounded with the change of data.** The detector trained on 4,800
   CariesXrays images plus DENTEX; the classifier on DENTEX crops. The paper concedes this in
   VII and shows the single-corpus detector collapses, i.e. the training mixture, not localisation,
   drives transfer. RQ2 is nevertheless framed as "reformulating the caries stage ... separates
   them", and Contribution 3 credits the reformulation.
7. **The external lesion-detector result is site-level fragile and the headline omits that.** The
   pooled +9.28 [+4.72, +13.73] treats the four test sets as fixed; the random-effects interval
   includes zero, HKSJ is [−5.02, +24.24], and the prediction interval spans ±45 points. Per-site
   "separation" at test3 and test4 uses unadjusted 95% intervals. With a normal approximation
   (p ≈ 0.023 at test3, 0.013 at test4), Holm across the four sites keeps all three leads at
   α = 0.05 only just (adjusted p ≈ 0.046 and 0.038), and Bonferroni drops both. Moreover Li et
   al. describe three hospitals, so at least two of the four "sites" share a hospital; k = 4
   independent sites overstates the information for the between-site variance.
8. **Theory checks presented as confirmations.** Table 8 counts five implications as holding, but
   "Rule (3) gives the best constant" is a mathematical identity (checking it on data checks the
   code, not the theory), "Agreement does not transfer" is marked non-specific, and the last row
   holds at three of four sites under weakness 4. The Discussion's "five of its implications hold"
   overstates the empirical support; substantively two rows (floor moves with cohort; healthy
   scores rise with base rate, itself subject to weakness 5) carry weight.

## Unsupported or overstated claims

| # | Quote | Section | Why |
|---|---|---|---|
| 1 | "from 78 held-out radiographs the rule recovers the eight first and second molars" | Abstract | The 78 fit images are the images "excluded from scoring because our models trained on them" (Figure 2 caption). They are held out from scoring, not from training. "Held-out" is wrong here. |
| 2 | "led the constant on the external sites by 9.28 points of lesion agreement [+4.72, +13.73] while flagging fewer teeth, at three of the four sites" | Abstract | Omits that the random-effects interval includes zero (HKSJ [−5.02, +24.24]), that Ningxia informed adoption of both the lesion detector and the tooth detector, and that on DENTEX the detector does not beat the constant on lesion agreement (−3.55 [−10.11, +2.64]) and is below the crop classifier (0.595 vs 0.802). |
| 3 | "Only two stage results are both held out from every training corpus and from model selection: the crop classifier's external caries scores and numbering on UFBA-425" | IV, Table 3 ("the cleanest external test") | Contradicted by `RESULTS_LOG` 2026-10-11f/g: the Stage-1 default was chosen after its gate-path Ningxia result was known. The CariesXrays 1,500-image gate-path sample had also been seen. |
| 4 | "agreement on external cohorts, paired with the constant and reported per site, can [separate the two explanations]" | I, The gap | Table 8 itself marks external non-transfer "not specific": domain shift predicts the same pattern. External agreement alone does not separate prior use from perception. |
| 5 | "Five direct repairs ... none separated from zero, including a retrain with 2.67 times the carious crops, so the ceiling is not set by supervision" | VI-D | Single runs, 34 radiographs, intervals ±0.06–0.09 AP. Absence of a detectable gain is not evidence of absence; CLAHE's interval is [−0.003, +0.099]. |
| 6 | "Section III-D locates it [the ceiling] in the task as posed — a tight crop, a binary label and a strong prior" | VI-D | III-D shows the ranking within type carries real signal (AUC 0.745) and Table 8 rejects "shortcut carries the ranking". Nothing in III-D tests crop tightness or label granularity. |
| 7 | "Both implications of Section III-E hold" | VI-D | See weakness 4: no operating-point control; within-type evidence only on the development corpus. |
| 8 | "their F1 carries no detectable image information" (VLMs) | VI-B | Intervals [−4.90, +5.63] and [−2.06, +4.85] cannot exclude a several-point image contribution; "no detectable" is acceptable only with the interval width beside it. Prompt is single and decoding settings unrecorded. |
| 9 | "a lesion detector led it on four pooled external sites with fewer flags" | IX | Pooled over sites as fixed; not shown at test1; random-effects interval includes zero. |
| 10 | "A pre-registered reformulation of the caries stage as lesion detection, which led the constant on the pooled external sites" | I, Contribution 3 | Credits reformulation for a lead the paper itself attributes to the training mixture (VI-D, last sentence; VII). |
| 11 | "Five of its implications hold" | VII | One is an identity, one non-specific, one partial (weakness 8). |
| 12 | "The theory treats codes independently" | VIII | Equations (2)–(3) are exact identities on counts and assume no independence. The genuine limitation is that the constant is optimal only in-sample, and that the prior is estimated from 78 images that are training images. |
| 13 | "images of what the system does (Figures 4, 5 and 7)" | VII | Figure 5 is training curves. |
| 14 | "[Kelly et al.]" attached to "no regulatory or clinical-trial evidence exists for it" | VII, Clinical implications | A 2019 review cannot attest to the evidence status of this system; it supports only that such evidence is required. |

## Mathematical check of Section III

**Equation (1).** P(D ∩ N ∩ F) = P(D) P(N | D) P(F | D, N) is the chain rule; correct. Caveat:
for FDI-set F1, a missed *healthy* tooth produces no entry and costs nothing, so "a perfect caries
model still writes a wrong report on every tooth that was missed" holds for the report, not for
the metric. The identity-factor arithmetic (7.2, 36.5, 55.5 points from 92.8, 63.5, 44.5) is
correct.

**Equation (2).** Micro-F1 = 2TP / (2TP + FP + FN) = 2TP / (#predicted + #actual). With TP =
Σ_{c∈S} n_c, #predicted = |S|N, #actual = P = Σ_c n_c (one entry per carious (image, code)
pair): F1(S) = 2Σ_{c∈S} n_c / (|S|N + P). **Correct.** Numerically 2·286 / (1,312 + 477) =
0.3197. P is carious teeth (477), not lesions (479); the text uses it correctly.

**Equation (3).** Write A = Σ_{c∈S} n_c, k = |S|, D = kN + P. Adding c:
2(A + n_c)/(D + N) > 2A/D ⇔ (A + n_c)D > A(D + N) ⇔ n_c D > AN ⇔ n_c/N > A/D ⇔
p_c > F1(S)/2. All denominators are positive. **Correct.**

**Fixed size → top-k prefix.** For fixed k the denominator kN + P is fixed, so F1 is maximised by
maximising Σ n_c, i.e. the k most prevalent codes. **Correct** (non-unique under ties).

**Single peak.** F1(S_{k+1}) = [2A + 2n_{k+1}] / [D + N] is the mediant of 2A/D = F1(S_k) and
2n_{k+1}/N = 2p_{k+1}, so it lies between them. If code k+1 fails (3), 2p_{k+1} ≤ F1(S_k), hence
2p_{k+1} ≤ F1(S_{k+1}) ≤ F1(S_k), i.e. p_{k+1} ≤ ½F1(S_{k+1}) — the paper's claim. Then
p_{k+2} ≤ p_{k+1} ≤ ½F1(S_{k+1}), so k+2 fails against S_{k+1}, and by induction every later
code fails and F1 is non-increasing thereafter. Before the first failure F1 strictly rises.
**Correct.** (With exact equality p = F1/2 the peak is a plateau; "single peak" should read "a
single maximal plateau", immaterial here.)

**Characterisation of the optimum.** Let k* be the cut. For j ≤ k*, code k* passed against
S_{k*−1}, so by the mediant property F1* = F1(S_{k*}) < 2p_{k*} ≤ 2p_j; hence every member has
p_c > F1*/2. Code k*+1 fails: p_{k*+1} ≤ F1*/2. Since the best set of each size is a prefix, the
global optimum over all sets is max_k F1(S_k). The paper's statement — the optimum holds exactly
the codes with p_c > ½F1* — is **correct** (members strictly above; non-members at or below).

**Numerical check of rule (3).** Fit-set F1 0.392 → threshold 0.196; tooth 27 at 0.205 admitted;
tooth 15 at 0.128 rejected. Consistent. `constant_stability_and_curve.json` records rule (3) equal
to greedy search in 198 of 200 resamples, the two disagreements being ties — consistent with the
plateau caveat above.

**No error found in the derivation.** Two substantive comments:

- *Prior art.* The result is Lipton et al. (2014) applied to a score that equals the prior. It
  should be cited at Equation (3).
- *Scope.* (3) characterises the in-sample optimum on the fit set. The out-of-sample floor (0.320
  vs oracle 0.330) is an empirical fact, not a consequence of the theory, and the fit set is 78
  images selected for containing caries (prevalences are conditional on ≥1 lesion, unlike the
  164 scored images of which 16 have none). The text should say so.

**Equation (4)** is a definition; the monotonicity in 𝓕 and the 0.998 ceiling are correct
consequences.

**Equation (5) and I².** The DL estimator and I² = (Q − (k−1))/Q (truncated at 0) are stated
correctly; my recomputation matches all printed values (see Strength 3). Note q_HKSJ = 0.788 < 1
here, so the untruncated HKSJ variance is smaller than the DL variance; the wider HKSJ interval
comes only from t₃. The modified (truncated) HKSJ recommended for this case gives roughly
[−6.9, +26.1]. The prediction interval uses t_{k−2} = t₂, the Higgins/Riley convention; correct but
extremely unstable at k = 4 — which the text acknowledges.

## Statistical validity

- **Cluster bootstrap over images.** Appropriate, and the paired-difference construction is right.
  Two cautions: percentile intervals with 34 clusters (Table 2, Table 6) and 40–53 images per small
  Ningxia site (test3, test4) can under-cover; a BCa or studentised check, or simply stating the
  cluster counts beside those intervals, is warranted. The Field & Welsh citation supports variance
  consistency, not coverage at small cluster counts.
- **DerSimonian–Laird with four sites.** Correctly supplemented by HKSJ, Q-profile τ and a
  prediction interval. But the four test sets come from at most three hospitals (Li et al.; and
  test2 is described as the dataset's training centre), so sites are not independent draws. Per-site
  variances derived from asymmetric percentile intervals via a normal approximation should be
  stated as such.
- **No multiplicity correction.** Defensible for an estimation paper, and the paper says so. But
  conclusions are then drawn from per-interval "separation" (e.g. "the lead holds at three of these
  four sites"), which is a testing statement. Under Holm the three leads survive by a hair; under
  Bonferroni only test2 does. The 3-of-4 language should carry that qualification or be replaced by
  the random-effects summary.
- **Selection effects.** (a) Ningxia informed adoption of both the lesion detector and the tooth
  detector; only the first is disclosed. (b) Ningxia had been scored in ≥20 full passes by 11 Oct.
  (c) CariesXrays is the lesion detector's checkpoint-selection split and was one of the two
  cohorts that satisfied the adoption rule; the rule also chose between two arms on the evaluation
  cohorts. (d) The current tooth detector was adopted against two guards, after its DENTEX and
  Ningxia numbers were seen, so DENTEX is in-domain for the front end of every pipeline row. (e) The
  theory was written after the measurements (disclosed). (f) A possible scanner overlap between
  CariesXrays and one Ningxia centre should be ruled out: the lesion-detector pre-registration
  gives CariesXrays as ~2440×1280, and the dataset description of Li et al. lists 2440×1280 as one
  of its centres' resolutions. If CariesXrays and a Ningxia centre share a site or device, one
  "external" site is not external to the lesion detector.
- **Single runs.** Every model except Stage 4a is a single seed; the run-to-run variance of the
  lesion detector's Ningxia lead is unknown, and on Stage 4a the three seeds span 11.0–27.5%,
  indicating that seed variance is not small in this project.
- **Selective prediction.** The crop classifier's accuracy at full coverage, 0.797, is below the
  all-healthy accuracy implied by prevalence 0.147 (0.853). The shuffle control shows that
  confidence ranks errors, but the gain to 0.940 should be set beside the majority-class accuracy
  of the retained subset, which also rises as uncertain (mostly carious) items are declined.
- **Calibration** was fitted on validation and evaluated on test (`RESULTS_LOG` 2026-08-27r/s);
  the manuscript should say so, and should state that calibration was on crops cut with
  ground-truth boxes, not on the detector crops the deployed pipeline uses.
- **Conclusions vs statistics.** The abstract and conclusion lean on the fixed-site pooled interval
  and the unadjusted per-site intervals; the random-effects analysis the authors themselves ran
  says the lead is not shown for a new site. The abstract should carry that.

## Citation checks

| Sentence (abridged) | Key | Supports? | Why |
|---|---|---|---|
| Detect-then-classify numbering reached expert-level sensitivity on a held-out set of 222 images (numbering sensitivity 0.9800) | tuzoff2019tooth | Yes | Abstract: separate test set of 222 images; numbering sensitivity 0.9800; "comparable to the level of experts". |
| Class-averaged numbering accuracy 0.9988 (F1 0.979) | zancan2025ai | Largely | Abstract gives accuracy 0.998, F1 0.98 for numbering; four-decimal figures need the full text (the audit README says it was read). |
| Systematic review found accuracies of 86.1–96.1% on panoramic radiographs, quality and reporting judged low | mohammadrahimi2022deep | Yes | Abstract: "86.1% to 96.1% on panoramic radiographs"; "study and reporting quality are currently low". |
| CNN trained against measured % bone loss on OPG segments reached accuracy 0.81 | krois2019deep | Yes | Abstract: 2,001 segments, reference the measured % PBL, mean accuracy 0.81. |
| On Tufts-derived and Chilean radiographs a bone-loss model reached weighted F1 0.29 and could not detect severe loss | cerda2024determining | Partly | Weighted F1 0.29 and F1 = 0 for severe PBL are in the abstract; "Tufts-derived and Chilean" is not, and needs the full text. |
| Periodontitis model from OPGs linked to clinical diagnoses, tested at four centres | li2025novel | Yes, with nuance | Abstract: developed from OPGs linked to clinical diagnoses; 760 radiographically labelled OPGs from four centres (the clinically labelled test set is separate). |
| Of 516 studies (Jan–Aug 2018), only 31 (6%) validated externally | kim2019design | Yes | Abstract matches exactly. |
| Apical-lesion model fell from F1 54.1% to 32.7% at a second centre | krois2021generalizability | Yes | Abstract: 54.1 ± 0.8% Charité vs 32.7 ± 0.8% KGMU. |
| YOLOv11 fell from mAP@0.5 0.857 to 0.806 on external images, weakest on caries | mutlu2026comparison | Yes | Abstract matches; "external" images are from Roboflow Universe, not a clinical centre — worth saying. |
| VQA models answered from language priors, inflating apparent capability | goyal2017making | Yes | Abstract: "models that ignore visual information, leading to an inflated sense of their capability". |
| VQA models lost accuracy when answer priors differed between train and test | agrawal2018dont | Yes | Abstract: VQA-CP; performance "degrades significantly". |
| Hypothesis-only model beats the majority class on many NLI datasets | poliak2018hypothesis | Yes | Abstract: "significantly outperform a majority-class baseline across a number of NLI datasets". |
| COVID-19 detectors relied on confounders and failed at new hospitals | degrave2021ai | Yes | Abstract matches. |
| Sorting radiographs by hospital alone reached AUC 0.861 because prevalence differed | zech2018variable | Yes | Abstract: MSH 34.2% vs 1.2%/1.0%; sorting by hospital AUC 0.861. |
| "the site effect Zech et al. found for pneumonia" (constant's agreement varies 0.494–0.709 across sites) | zech2018variable | Partly | Zech shows prevalence differences that a model can exploit; here the variation is in a fixed list's coverage of lesions. Analogy, not the same effect; soften to "analogous to". |
| Cluster bootstrap stays consistent when clusters carry random effects | field2007bootstrapping | Yes | Abstract: cluster bootstrap gives consistent variance estimates under both the transformation and the random-effect model. |
| Prediction interval asks whether it would lead at another site | riley2011interpretation | Yes | Abstract: prediction intervals estimate the likely effect in an individual setting. |
| I² is the share of variation due to heterogeneity | higgins2002quantifying | Yes | Abstract defines I² this way. |
| Aggregate metrics hide failures on clinically important subsets | oakdenrayner2020hidden | Yes | Abstract: hidden stratification. |
| Biases enter medical-imaging evaluation at every step | varoquaux2022machine | Yes | Abstract: "at every step, potential biases can creep in". |
| Periodontitis staged from breakdown relative to root length, tooth loss and complexity factors | tonetti2018staging | Yes | Abstract matches. |
| Public datasets combined to predict segmentation, FDI numbers and diagnoses together | vannistelrooij2024combining | Yes for this clause | The preceding clause in the same sentence ("Classifying a cropped tooth is easier than numbering under detector output") is not supported by this work and carries no citation of its own. |
| First molars are the most caries-susceptible teeth, long established | batchelor2004grouping | Partly | The study is of 5–16-year-old children (surface susceptibility); DENTEX is an adult population. Cite as children's data or add an adult source. |
| Translating such systems into care requires clinical evaluation beyond retrospective accuracy | kelly2019key | Yes | Abstract: robust clinical evaluation, metrics beyond technical accuracy. |
| Same: | schwendicke2020artificial | Partly | Abstract argues for methodological rigour and demonstrated value, not specifically clinical evaluation beyond retrospective accuracy. |
| "no regulatory or clinical-trial evidence exists for it" | kelly2019key | No | Cannot attest to this system's status (see overstated claim 14). |
| CariesXrays task-specific method 48.2 AP (AP50 84.1); best of ten baselines 42.2 | chen2024cariesxrays | Not verifiable from saved abstract | The abstract gives no numbers; full-text table needed. |
| Ningxia dataset collected at three hospitals in Ningxia and Shenzhen | li2024multicenter | Yes | Saved abstract is empty; a dataset catalogue citing the paper lists two Yinchuan hospitals and one in Shenzhen. Implies the four test sets are not four hospitals. |
| (missing) F1-optimal threshold equals half the optimal F1 | — | Missing citation | Lipton, Elkan & Narayanaswamy 2014 should be cited at Equation (3). |

## Missing experiments

1. **Operating-point-matched comparison** of the crop classifier and the lesion detector: classifier
   thresholded to flag 624 (FDI-set) or 603 (agreement) teeth on DENTEX, with overall and per-type
   precision and paired intervals; or within-type PR curves. Needed to support Section III-E.
2. **Content-free and position-perturbation controls for the lesion detector**: blank and noise
   images (as for the VLMs), horizontally mirrored OPGs (which preserves tooth-type positions and
   so should not change flags if the detector reads lesions), and images with lesions inpainted.
3. **Task vs data disentanglement** (RQ2): a crop classifier trained on crops derived from the same
   CariesXrays + DENTEX supervision, or a detector trained on DENTEX alone, so that localisation is
   compared with classification on equal data.
4. **Seeds**: at least three seeds of the lesion detector, with the Ningxia per-site differences
   for each, before a "3 of 4 sites" statement.
5. **Per-tooth-type flags on Ningxia** (re-run inference only; acknowledged as not run).
6. **Ningxia site/device provenance** and a check for overlap with CariesXrays.
7. **A label-noise sensitivity analysis for Table 2**: within-type AUC and healthy-score gradient
   restricted to teeth positively labelled healthy (not "no annotation"), if the count permits.
8. **Disclosure of the survey method** behind "49 task-relevant papers" (databases, dates,
   inclusion), or removal of the count.

## Required corrections

1. **CRITICAL** — Table 3, Section IV ("Only two stage results ... held out ... from model
   selection"), Table 4 (Ningxia row), V, VIII: state that Ningxia informed the choice of the
   Stage-1 detector (the gate-path Ningxia result was known when it was adopted), remove "the
   cleanest external test" and the claim that the crop classifier's external caries scores are free
   of model selection, and report the number of times the Ningxia caries cohort has been scored.
2. **MAJOR** — Section III-B and Contribution 1: cite Lipton, Elkan & Narayanaswamy (2014) at
   Equation (3), present (3) as its specialisation to a prior-only score, and reduce the novelty
   claim accordingly; add F-measure set-prediction literature to Related Work.
3. **MAJOR** — Abstract and Conclusion: report the random-effects result (DL [−0.54, +19.76], HKSJ
   [−5.02, +24.24], prediction interval) beside the pooled +9.28, say that Ningxia informed
   adoption, and add the DENTEX lesion-agreement tie (−3.55) and the crop classifier's higher
   DENTEX agreement (0.802 vs 0.595).
4. **MAJOR** — Section V (pre-registration) and VI-D: disclose that the adoption rule counted the
   lesion detector's checkpoint-selection split (CariesXrays) as one of its three cohorts and chose
   the better of two arms on the evaluation cohorts.
5. **MAJOR** — Section VI-D, Table 8 row 6, VII (RQ2): either add the operating-point-matched
   comparison (Missing experiment 1) or withdraw "Both implications of Section III-E hold" and the
   "holds at 3 of 4 sites" verdict as evidence of reading the image; also qualify "receives no tooth
   identity" (absolute image position can carry the prior).
6. **MAJOR** — Section III-D, Table 8 row 3, VIII: name prevalence-proportional label noise and
   type-specific difficulty as alternative explanations of the healthy-score gradient; give
   per-type AUC intervals or state that incisor/canine AUCs rest on 8 and 5 positives.
7. **MAJOR** — Contribution 3, RQ2 framing, Section VI-D: state in the contribution itself that the
   lead is attributable to the training mixture as much as to localisation (the paper's own last
   sentence of VI-D).
8. **MAJOR** — Abstract: replace "from 78 held-out radiographs" with an accurate description (78
   training images excluded from scoring).
9. **MAJOR** — Section VI-D, VII, IX: qualify per-site "separated" statements for multiplicity
   (Holm keeps three leads only marginally; Bonferroni keeps one) and state that the four test sets
   come from three hospitals.
10. **MAJOR** — Section I ("agreement on external cohorts ... can [separate]"): reconcile with Table
    8's "not specific"; external agreement alone does not separate prior use from perception.
11. **MINOR** — Section VI-D: replace "so the ceiling is not set by supervision" and "Section III-D
    locates it in the task as posed" with statements the single-run, 34-radiograph intervals
    support.
12. **MINOR** — Section VII and Table 8: do not count the identity "Rule (3) gives the best
    constant" as an empirical confirmation; restate "five implications hold".
13. **MINOR** — Section VIII: replace "The theory treats codes independently" (the derivation
    assumes no independence) with the true limitation (in-sample optimality on 78 training images
    selected for containing caries).
14. **MINOR** — Section III-F/VI-D: note q_HKSJ < 1 and report the truncated-HKSJ interval; state
    that per-site variances come from a normal approximation to percentile intervals.
15. **MINOR** — Section VI-E: give the majority-class accuracy (0.853) beside the crop classifier's
    0.797 → 0.940 abstention result; state that calibration was fitted on validation and evaluated on
    test crops cut with ground-truth boxes.
16. **MINOR** — Section VI-B: give interval widths with "carries no detectable image information";
    record VLM decoding settings or state the result is not reproducible in detail.
17. **MINOR** — Citations: remove kelly2019key from "no regulatory or clinical-trial evidence exists
    for it"; soften the Zech analogy in III-C; qualify batchelor2004grouping as a children's study;
    give the vannistelrooij sentence's first clause its own support or drop it; verify cerda2024's
    "Tufts-derived" and chen2024cariesxrays's baseline figures against the full texts.
18. **MINOR** — Section VII: "images of what the system does (Figures 4, 5 and 7)" — Figure 5 is
    training curves.
19. **MINOR** — Section II/I: describe the survey behind "49 task-relevant papers" or drop the
    number.
20. **MINOR** — Data/Methods: check and report whether CariesXrays and any Ningxia centre share a
    site or scanner (matching 2440×1280 resolution).

## Optional improvements

- Report the fit-set prevalences conditional and unconditional on ≥1 lesion, and the constant fitted
  on all 86 excluded images, to show the floor's sensitivity to the fit-set definition.
- Show a leave-one-site-out version of the lesion-detector vs constant difference, to make the
  test1 anomaly concrete (e.g. does test1 have a higher molar share of lesions?).
- Add a per-site table with the constant's prior mass, lesion count and image count beside each
  difference, so that the reader can see whether the lead tracks the prior mass.
- Consider a "relative-to-prior" summary (system agreement minus constant agreement, divided by
  1 − constant agreement) to make cohorts with different floors comparable.
- Move the numbering-error taxonomy (Figure 8a/b) to a supplement if space is needed for the
  operating-point analysis.

## Recommendation

**Major revision.**

The derivations are correct, the statistics are mostly appropriate and correctly computed, the
negative results are reported unusually fully, and nearly every number traces to a saved artefact.
The core message — score a tooth-level caries result beside an image-blind constant, per site, with
paired intervals — is useful and supported. But three things prevent acceptance in the present
form. (1) The selection channels around the only external cohort are under-disclosed, and Table 3
asserts the opposite of the project's own decision record for the crop classifier. (2) The theory's
key result is a known theorem presented as new. (3) The positive RQ2 result rests on a test
(Section III-E) that does not control for operating point, on one seed, on four sets from three
hospitals, with a random-effects interval that includes zero — yet the abstract and conclusion
present it as a lead on "the external sites". All three can be corrected with text changes and one
or two analyses on saved or re-runnable outputs. No new data collection is needed.
