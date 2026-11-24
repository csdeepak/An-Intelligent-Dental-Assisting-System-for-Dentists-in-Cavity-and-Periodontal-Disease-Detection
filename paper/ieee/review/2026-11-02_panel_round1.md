# Review panel, round 1 — ten-page draft

Manuscript: `paper/paper.md` → `paper/ieee/main.pdf`, ten pages, after the Stage 2.5 corrections of
2 Nov 2026 (gate re-verified: PASS WITH NOTES; `2026-11-02_integrity_gate_and_panel_setup.md`).
Method: `academic-paper-reviewer` full mode of the academic-research-skills suite (commit
`a41f3b2`), with the four configuration cards the repo owner accepted on 2 Nov and the fixed
Devil's Advocate. Target venue: field-general (`criteria_binding_unavailable`; the panel makes no
venue-alignment claim).

**Panel provenance.** One model (Claude Opus 5.5), one session, five role-separated seats written
in sequence. Each report was committed before the next was started and was not revised after any
other was written. This is persona separation, not independent review: the seats share a model, its
knowledge and its blind spots, and the session had already built the manuscript. No cross-model
review was run. Accountable human: the repo owner. Reviewers are read-only; nothing here edits the
manuscript.

Severity: **Critical** (the conclusion does not stand as written), **Major** (must be addressed for
the claim to be credible), **Minor** (improves the paper).

---

## Report 1 — Journal-Fit Reviewer (field-general)

**Summary of the submission.** The paper argues that tooth-level caries scores on panoramic
radiographs mix image evidence with a prior over where caries occurs. It gives the F1 of the best
image-blind tooth list in closed form, measures a six-stage pipeline, two vision-language models and
that list on three cohorts, and shows that reformulating the caries stage as whole-image lesion
detection led the list on four external sites. Real radiographs, training curves and rule-chosen
failures accompany the numbers.

**Assessment of fit and significance.** The message matters to anyone who reads or writes dental-AI
results, and it transfers to multi-label medical imaging generally. The reporting is unusually
candid: a missed pre-registered guard, an unexplained site, a split artefact and a post-hoc
consistency table are all stated.

**Strengths**
1. A clear, testable thesis supported by paired, clustered intervals on three cohorts.
2. The closed form turns an observation ("a molar list scores well") into an explanation.
3. Evidence a reader can inspect: every stage on a real image, failures shown deliberately.

**Weaknesses**
- **Major — one paper or three.** A theory, a six-stage system and a multi-cohort evaluation share
  ten pages. Stage 4 (Section VI-G), the vision-language controls (VI-F) and much of the system
  description serve the system, not the thesis. The evaluation contribution would read more strongly
  with Stage 4 and the VLM detail moved to a supplement, freeing space for the controls other
  reviewers will ask for.
- **Major — novelty in proportion.** Input-blind baselines are established in visual question
  answering and language inference, and prior-driven scores are documented in medical imaging (the
  paper now cites these). The contribution is bringing the floor to dental caries scoring with a
  closed form and multi-site evidence. The abstract and introduction should say so in those terms;
  as written, a reader could take the idea itself to be new.
- **Minor.** The abstract carries twelve numbers in eight sentences; a reader outside dentistry
  needs fewer. The "what to report" recommendation would be more usable as a short boxed checklist.

**Questions for the authors.** Is the target readership dental AI or medical-imaging evaluation?
The answer decides what moves to a supplement.

**Recommendation: Major revision.**

---

## Report 2 — Peer Reviewer 1 (Methodology)

**Summary.** I assessed the inferential design: paired cluster bootstraps over images, a
pre-registered adoption rule, random-effects pooling over four sites, and the closed-form account of
the constant.

**Strengths**
1. Resampling images rather than teeth is the right unit, and pairing is used wherever systems share
   images.
2. The adoption rule was registered before training, and the bar was not moved.
3. The random-effects analysis reports a prediction interval, which is the honest quantity for a new
   site.

**Weaknesses**
- **Major — four sites cannot estimate between-site variance.** With k = 4, the DerSimonian–Laird
  τ² is poorly determined and its confidence interval for the mean is known to be too narrow;
  per-site variances are also back-calculated from percentile-interval widths, which assumes
  approximate normality. Report the Hartung–Knapp–Sidik–Jonkman interval beside DL [suggested:
  IntHout et al. 2014], show τ² with its uncertainty, and present the random-effects result as
  descriptive.
- **Major — selection and multiplicity.** The headline external result (+9.28 on Ningxia) comes from
  the one cohort that also decided the detector's adoption; the CariesXrays result is on the split
  that chose its checkpoint. Many comparisons are reported (three cohorts, three arms, two metrics,
  four sites) without any multiplicity framing. The text acknowledges the selection; it should also
  say that the Ningxia lead is optimistic by construction, and frame the analysis as estimation, not
  as a family of tests. An untouched cohort is the only full remedy.
- **Major — leakage beyond byte identity.** DENTEX exclusions use MD5 identity (86 removed). Was a
  near-duplicate check (perceptual hash) run for DENTEX, as for UFBA-425? Resized or re-exported
  copies would pass an MD5 check.
- **Minor — stability of the fitted constant.** The eight-molar set is fitted on 78 images. A
  bootstrap over those images, reporting how often the same set is selected, would show whether the
  floor is a stable property or a lucky draw.
- **Minor — a volume-matched floor.** Lesion agreement rises with teeth flagged. Plotting agreement
  against teeth flagged for constants of size k = 1…16 (an image-blind operating curve), with each
  system as a point, would make the comparison volume-free at a glance.
- **Minor.** Every model except Stage 4a is a single training run, so training variance is unknown;
  say so where the training curves are presented, not only in Limitations.

**Assessment of the theory.** Equations (2)–(3) and the single-peak argument are correct; I checked
the step from "code k+1 fails" to "every later code fails". The micro-F1 assumption (every named code
counts as a prediction, present tooth or not) should be stated once, since it is what makes (2) exact.

**Recommendation: Major revision.**

---

## Report 3 — Peer Reviewer 2 (Domain: oral and maxillofacial radiology)

**Summary.** I read the paper as a dentist would: whether the reference standard, the metrics and the
outputs mean something clinically.

**Strengths**
1. The OPG primer and Figure 1 are accurate and genuinely useful to non-dental readers.
2. Stage 4 is named for its label, and the paper makes no periodontal claim.
3. The qualitative figures show failures, including a flag without an annotated lesion, and say that
   such a flag is not a confirmed false positive.

**Weaknesses**
- **Major — the reference standard.** DENTEX caries labels come from panoramic radiographs alone.
  Panoramic radiography detects proximal and early lesions poorly compared with bitewings and clinical
  examination, so the "expert lesions" are a subset of disease, skewed towards larger and occlusal
  lesions, which are themselves concentrated in molars. Part of the molar prior may therefore be a
  prior of what panoramic labels capture. This needs a paragraph in Data or Limitations, and ideally a
  re-read of a sample by a second examiner.
- **Major — the prior is epidemiology.** That first and second molars are the most caries-susceptible
  teeth is long established [suggested: Batchelor and Sheiham 2004, first-molar pits and fissures most
  susceptible]. Citing it strengthens the paper and adds a caveat: the prior depends on age,
  fluoridation and population, so the floor will differ in paediatric or elderly cohorts.
- **Major — severity is reported but not validated.** The pipeline writes "caries" or "deep caries"
  (Stage 3b; the JSON excerpt shows deep_caries), but the draft evaluates only the binary flag. State
  that severity is unvalidated, or evaluate it.
- **Minor.** Define "deep caries" as DENTEX defines it. Name the abnormality types behind Stage 4's
  label (the maintained manuscript lists apical lesions, sclerosis and cysts). Wrong-tooth errors at
  molar positions (8.2% at position 7) matter more clinically than at incisors, because they move a
  caries finding to the wrong tooth; connect Figure 8b to the identity chain.

**Recommendation: Major revision.**

---

## Report 4 — Peer Reviewer 3 (Perspective: computer vision, dataset bias)

**Summary.** I read the paper as a contribution to evaluation practice in medical computer vision.

**Strengths**
1. The image-blind floor and its closed form apply to any multi-label task scored by micro-F1 over a
   fixed label set; the paper is more general than its title.
2. The base-rate-tracking test with within-type AUC is a clean, reusable shortcut diagnostic.
3. The connection to visual question answering and language inference is drawn correctly.

**Weaknesses**
- **Major — stronger shortcut controls.** The frozen constant is the weakest image-blind model. Three
  stronger controls are cheap relative to the claim: (a) a learned position-only model (tooth code or
  box geometry as input) for the tooth-level task — the paper already reports a position-only AP of
  0.296 for the crop classifier, so extend it; (b) a content ablation, masking or blurring tooth
  interiors to see whether flags persist; (c) a site-identification probe on Ningxia — if test1–test4
  are predictable from the image, site cues are available to any model [cf. the paper's own Zech et
  al. citation; also Oakden-Rayner et al. 2020 on hidden stratification].
- **Major — reproducibility.** The draft has no code, weights or data availability statement, and the
  DENTEX share-alike licence bears on the released figures. A field that the paper asks to report an
  image-blind row needs the tool to compute it; release the floor computation as a script.
- **Minor.** State the generality of (2) explicitly (any micro-F1 set prediction with a label prior).
  Report the hardware behind "1.70 s per image on a laptop CPU". The VLMs were run with one prompt and
  unrecorded decoding settings (an open issue the authors already list); say so in the text. Group
  robustness work [suggested: Sagawa et al. 2020] is the natural framing for per-site worst cases.

**Recommendation: Major revision.**

---

## Report 5 — Devil's Advocate

**The strongest counter-argument.** The paper shows that a molar list scores comparably to its
pipeline on some cohorts and that a lesion detector beats the list on Ningxia. It concludes that a
tooth-level score "cannot show that a system reads the radiograph" and that localisation "cannot
score by reproducing a prior". The first conclusion is close to true of any aggregate metric; the
second is contradicted by the paper's own Section III-E.

**Findings**
- **CRITICAL — the RQ2 conclusion overstates the evidence.** Section VII says "A detector that must
  place lesion boxes cannot score by reproducing a prior". Section III-E says it *can*, by drawing
  boxes over molars, at a cost in precision. The two evidence lines for localisation reading the image
  (fewer flags; flags carious more often per tooth type) are measured on DENTEX, the development
  corpus, for the per-type comparison; on the external cohort only the flag volume is shown. The
  conclusion needs rewording to what was shown, and the per-type comparison should be repeated on
  Ningxia if the saved per-lesion records allow it.
- **Major — "belongs to the cohort, not to any model".** Section III-C says the constant's agreement
  is the cohort's prior mass and "belongs to the cohort, not to any model", one sentence after saying
  the molar boxes are placed by the pipeline's own front end (92.0% placement precision on Tufts). The
  quantity is the prior mass *as placed by this detector*; state it that way.
- **Major — a non-diagnostic row.** Table 7's "development agreement does not predict external
  agreement" would hold under ordinary domain shift with no positional prior at all, so it does not
  support the theory over the obvious alternative. Mark it as consistent with, not specific to, the
  theory — or drop it from the table.
- **Major — scope of the title.** Three cohorts, one disease and one pipeline support "here, a
  tooth-level caries score did not show it". The title and conclusion generalise to tooth-level scores
  as such; a population where caries is not molar-concentrated would have a low floor.
- **Minor — cherry-picking check: passed.** Qualitative images are chosen by a stated rule, a failure
  row is included, and the unexplained site is reported.
- **"So what?" test: passed.** The recommendation (an image-blind row, identity factors, per-site
  results, images) is actionable.

**Recommendation: Major revision.**

---

## Editorial synthesis

### Consensus (raised by three or more seats)

| Theme | Seats | What is needed |
|---|---|---|
| The external evidence is selection-conditioned and thin (one external cohort, informed adoption, four sites) | R1, DA, JF | Temper wording; HKSJ beside DL; estimation framing; an untouched cohort as the full remedy |
| Shortcut controls for the lesion detector are weaker than the claim | R3, DA, R1 | Learned position-only floor; content ablation; site probe; per-type comparison on Ningxia |
| Claims outrun evidence in places (RQ2 sentence, prior mass "of the cohort", title scope, novelty framing) | DA, JF, R2 | Rewording to what was shown |

### Disagreements and arbitration

- **Add analyses (R3, R1) versus cut scope (JF).** Both can hold: move Stage 4 and the VLM detail to
  a supplement, and use the space for the controls. Arbitration: adopt both.
- **How much the reference standard undermines the floor (R2).** Other seats did not raise it. It is
  a genuine limitation, not a refutation: the floor is defined against the labels a study uses, and
  the paper's argument concerns scores against those labels. Arbitration: add the limitation and the
  epidemiological citation; a re-read is desirable, not required.

### Devil's Advocate CRITICAL — adjudication

**Validated.** The RQ2 sentence contradicts Section III-E and claims more than the development-only
per-type evidence shows. It blocks an Accept until reworded; the external per-type comparison is
requested if the saved data allow it.

### Decision: **Major revision**

Every seat recommended major revision. The paper's thesis is sound and its reporting candid; the
revision concerns the strength of the external evidence, missing shortcut controls and several
over-general sentences, not the core analysis.

### Revision roadmap (source-ordered; no ranking implied)

| # | Item | Source | Severity | Work |
|---|---|---|---|---|
| 1 | Reword the RQ2 conclusion to what was shown; repeat the per-type comparison on Ningxia if per-lesion records carry tooth codes | DA | Critical | wording; analysis from saved data |
| 2 | Re-scope: move Stage 4 and VLM detail to a supplement | JF | Major | editing |
| 3 | State novelty as bringing the floor to dental caries scoring, with a closed form and multi-site evidence | JF | Major | wording |
| 4 | HKSJ interval beside DL; τ² with uncertainty; random effects as descriptive | R1 | Major | analysis from saved data |
| 5 | Selection and multiplicity: estimation framing; say the Ningxia lead is optimistic by construction | R1 | Major | wording |
| 6 | Near-duplicate (perceptual-hash) leakage check for DENTEX | R1 | Major | analysis from saved data |
| 7 | Reference-standard limitation of panoramic caries labels | R2 | Major | wording (re-read optional) |
| 8 | Cite caries epidemiology for the molar prior; population caveat | R2 | Major | wording + citation |
| 9 | Severity (3b) unvalidated, or evaluate it | R2 | Major | wording or analysis |
| 10 | Learned position-only floor; content ablation; site-identification probe | R3 | Major | new experiments |
| 11 | Code, weights and data availability statement; release the floor computation | R3 | Major | release |
| 12 | Prior mass "as placed by our detector", not "of the cohort" | DA | Major | wording |
| 13 | Mark Table 7's development-vs-external row as non-specific | DA | Major | wording |
| 14 | Title and conclusion scope to the evidence | DA | Major | wording |
| 15 | Stability of the fitted constant (bootstrap the 78 fit images) | R1 | Minor | analysis from labels |
| 16 | Image-blind operating curve (constants of size 1–16 against teeth flagged) | R1 | Minor | analysis from saved data |
| 17 | Single-run caveat where training curves are shown | R1 | Minor | wording |
| 18 | State the micro-F1 assumption behind (2); state its generality | R1, R3 | Minor | wording |
| 19 | Define deep caries; name Stage 4's abnormality types; link Fig. 8b to the identity chain | R2 | Minor | wording |
| 20 | Hardware for the runtime; VLM prompt and decoding caveat in the text | R3 | Minor | wording |
| 21 | Fewer numbers in the abstract; boxed "what to report" checklist | JF | Minor | editing |

Items 1, 3, 5, 7–9 (wording option), 12–14 and 17–21 are text changes. Items 1 (analysis), 4, 6, 15
and 16 can be computed from saved files. Item 10 needs new experiments; item 11 needs a release
decision.

---

## Attachment: Suggested-Reference Check (advisory, #1001)

Run with the same four-index resolver clients as the 2 Nov citation audit
(`outputs/citation_audit/2026-11-02_ars/verify_refs.py`), in place of the suite's
`verify_panel_recommendations.py`, which reads YAML suggested-reference blocks that this inline
panel did not emit.

| Suggested by | Work | Result |
|---|---|---|
| R1 | IntHout, Ioannidis, Borm 2014, *BMC Med. Res. Methodol.* 14:25, doi 10.1186/1471-2288-14-25 | resolves (Crossref, OpenAlex, S2); abstract supports "HKSJ outperforms DL" |
| R2 | Batchelor, Sheiham 2004, *BMC Oral Health* 4:2, doi 10.1186/1472-6831-4-2 | resolves; abstract supports first molars as most susceptible (children 5–16, US) |
| R3 | Oakden-Rayner et al. 2020, *CHIL*, doi 10.1145/3368555.3384468 | resolves |
| R3 | Sagawa et al. 2020, arXiv:1911.08731 | resolves (arXiv, OpenAlex) |

## Attachment: Reviewer Claim Check (advisory, #1002)

Did not run: the suite sends the five reports to a separate subagent as judge, and this panel ran
inline in one session.

## Attachment: Acronym Check (advisory, #849)

Output of the suite's `scripts/check_acronyms.py --input paper/paper.md --lang en`, unchanged except
that the two author-placeholder rows (ASK, AUTHOR) are omitted:

```
Coverage: body, English abstract (partial)
Not checked: OPG and VLM (defined in parentheses whose initials the script cannot match)
Not defined at first use: FDI (9 uses), RQ1–RQ3, AI, DENTEX, UFBA, mAP (4), AUC (4), COVID, VL,
CPU, GPU, MD5, IoU, AP50, COCO, NONE (an answer string, not an acronym)
```

Script output, not a reviewer finding: it creates no roadmap item and asks for no reply.
