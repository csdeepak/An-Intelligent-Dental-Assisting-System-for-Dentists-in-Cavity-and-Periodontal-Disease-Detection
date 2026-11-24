# Ten-page draft: Stage 2.5 integrity gate, checks, workflow audit, review-panel setup

Run on 2 Nov 2026 against `paper/paper.md` / `paper/ieee/main.pdf` at commit `4b314da`, following
the academic-research-skills suite (`github.com/Imbad0202/academic-research-skills`, commit
`a41f3b2`, v3.24.1): `academic-pipeline` Stage 2.5 (`integrity_verification_agent`, five
verification phases and the 7-mode AI-research failure checklist), `academic-paper`'s writing
quality and figure checks, and `academic-paper-reviewer` Phase 0 (field analysis and reviewer
configuration cards). Reviewers in that skill are read-only: nothing here edits the manuscript.

## 1. Integrity gate (Stage 2.5)

### Phase A — references

36 references, each with an explicit verdict. **VERIFIED: 36** — 34 resolve on Crossref, OpenAlex,
Semantic Scholar or arXiv by DOI or arXiv ID with a title match; Bizjak and Robič 2024 (journal
registers no DOIs) and the YOLO11 software citation confirmed at the publisher. No retraction
notices. Record: `outputs/citation_audit/2026-11-02_ars/final_refs.json`, `RESULTS_LOG` 2026-11-02.

### Phase B — citation context

Every citing sentence checked against the cited work's abstract or full text on 2 Nov
(`claim_abstracts.json`, `new_abstracts.json`). Three corrections already made then: Li et al.
"four hospitals" (the paper says three), Cao et al. 61.83 (not verifiable, dropped), Zancan 0.9988
(now with its F1). No open item.

### Phase C — data

- **C1, numbers against sources.** 363 distinct numbers traced to `paper/main.tex`, saved run files,
  or the cited work's own text (`trace_numbers.py`); 7.2 and 55.5 are subtractions.
- **C2, internal consistency.** Abstract against body: every abstract number (0.320, 78, 164, 4.27,
  337, +0.89 [−3.86, +5.57], 9.28 [+4.72, +13.73], three of four sites) appears in the body with the
  same value; no abstract claim is absent from the body. Repeated numbers agree across sections
  (0.591, 0.494–0.709, 31-point swing = −18.99 to +12.32, 46% = 8,457/5,808).
  **Issue C2-1 (MEDIUM).** Table 3's Tufts row reads "143 images, 3,760 teeth — numbering and
  Stage 4". 3,760 is the numbering population; Stage 4 was scored on the same 143 radiographs but
  over 3,892 teeth, 182 carrying its label (`main.tex`, Stage 4 figure caption). The row gives one
  unit for two populations.
- **C3, caption fidelity.** See §2.
  **Issue C3-1 (MINOR).** Fig. 3's caption says "95.34 M in total". That is `main.tex`'s total for
  the default pipeline (Stages 1, 2, default 3a, 3b, 4a, 4b), but the figure also draws the retained
  crop classifier (11.18 M) and gives no count for 4b. The caption should say what the total covers.

### Phase D — originality

Not applicable as an overlap check against prior literature: the draft is a condensed rewrite of the
same authors' unpublished maintained manuscript (`paper/main.tex`). Note for submission: if either
is published first, the other must be declared as related work by the same authors.

### Phase E — claims

Registered claims: the quantitative claims (Phase C), the citing claims (Phase B), and the
categorical and theoretical claims below.

- **Issue E-1 (MEDIUM, claim-strength).** Table 7 is titled "Predictions of the theory … against
  the evidence", and Section VII says five predictions "hold". The theory in Section III was
  written after every measurement in Table 7 existed, so these rows are consistency checks, not
  out-of-sample predictions. Either retitle (e.g. "What the theory implies, and what the data
  show") and say once that the theory was formulated after the measurements, or label the table
  post hoc. The theory's derivations themselves are not affected.
- **Issue E-2 (MINOR, completeness of a derivation).** Section III-B states that the F1-optimal
  constant is the prevalence-sorted prefix cut where rule (3) first fails, but shows only the
  per-step rule and the fixed-size argument. Global optimality needs one more line: if
  p_{k+1} ≤ F1_k/2 then F1_{k+1}/2 ≥ p_{k+1} ≥ p_{k+2}, so F1 along the prefix rises to one peak and
  then falls; and every admitted code satisfies p_c > F1*/2. (Checked algebraically for this
  report.) The abstract's "exactly" depends on it.
- **Note E-3.** "Such figures are often obtained on pre-cropped teeth" (Related Work) carries no
  citation of its own; it follows the Zancan and Zhang citations but neither abstract establishes
  it. Cite a source or soften to the authors' observation.
- Checked and supported: "the first and second molars carry most of it" (60.0% of carious teeth on
  the eight molars, the constant's recall); "the only system whose precision clearly exceeds the
  constant's" (0.439 against 0.218–0.250 for every other row of Table 4).

### 7-mode AI-research failure checklist

| Mode | Outcome | Evidence |
|---|---|---|
| 1 Implementation bug passing self-review | CLEAR | Every number has a saved source; the four figure scripts assert their values against the saved evaluations before drawing; `verify_paper_numbers.py` 215/215; test suite 210 passed / 3 skipped (27 Oct). Scope: this checks reporting against saved runs, not the correctness of the original training code. |
| 2 Hallucinated citation | CLEAR | Phases A and B above. |
| 3 Hallucinated experimental result | CLEAR | 363 numbers traced; seeds claimed (3, Stage 4a) match three run histories. |
| 4 Shortcut reliance | FLAG (flag-only at 2.5) | The paper's subject. For the crop classifier the shortcut is measured (Table 2). For the lesion detector two controls exist (fewer flags; higher carious share within tooth type), but none removes site- or scanner-level cues, and its adoption used Ningxia. For the Devil's Advocate at Stage 3. |
| 5 Bug reframed as insight | CLEAR | No "surprisingly / unexpectedly / in hindsight" phrasing. The one unexplained result (test1) is reported as unexplained; the Stage-4 0.923 is reported as the split artefact it was. |
| 6 Methodology fabrication | CLEAR | Methods numbers checked against configs: 9,600 samples per epoch from 4,800 CariesXrays + 650 DENTEX replicated (`models/16_lever_b_pooled/run_summary.txt`); 1,024 px, conf 0.25, NMS 0.50, crops 1.5×/1.5× and 1.5×/2.0×, threshold 0.30 (`scripts/run_inference.py`); 148 / 54 / 15 epochs (training logs); bootstrap 10,000 seed 42, 2,000 (calibration), 5,000 (within-type AUC), 1,000 seed 0 (abstention) (output JSONs, `main.tex`). |
| 7 Frame-lock | CLEAR | The project changed course when its evidence required it (caries task reformulated; Stage 4 relabelled; detector switched). The post-hoc framing of Table 7 is a claim-strength issue (E-1), not a locked-in wrong question. |

### Verdict

**FAIL** under the gate's rule (any MEDIUM issue fails): two MEDIUM issues (C2-1, E-1), two MINOR
(C3-1, E-2), one note (E-3). No mode is SUSPECTED; Mode 4 is flagged for the review. Correction list,
in order: E-1, C2-1, C3-1, E-2, E-3. After the corrections, re-verify only the corrected items.

## 2. Figure and table verification

| Item | Checked against | Result |
|---|---|---|
| Fig. 1 | `R_figures_facts.json` (test_120: 7 lesions on 12 16 28 35 36 37 46; 7 constant codes present; 4 of 7 covered) | matches |
| Fig. 2 | `R_draft_figures_facts.json` (78 / 164 images; threshold 0.196; magenta = the eight admitted codes) | matches; figure label and caption use the same notation |
| Fig. 3 | `run_inference.py`, `models/16` run summary, `main.tex` parameter table | content matches; total ambiguous (C3-1) |
| Fig. 4 | `R_figures_facts.json`, `R02_test_0_report.json` | matches (30 teeth; 24, 42 uncertain; 4 boxes 0.35–0.89; flags 26, 46, 36, 45; 48 missed) |
| Fig. 5 | training logs (148 / 54 / 15 epochs; three seeds) | matches |
| Fig. 6 | `stage1_switch_results.json`, `F_ningxia_random_effects.json` | matches (10,000 resamples; PI [−36, 55]) |
| Fig. 7 | `R_figures_facts.json` | matches |
| Fig. 8 | taxonomy, coverage and calibration JSONs | matches (saved operating points 50/75/90/100%; ECE 0.136 / 0.043) |
| Tables 1, 2, 4–7 | sources in §1 C1 | match |
| Table 3 | cohort sources | Tufts unit (C2-1) |

Every figure and table is referenced in the text, appears on or after the page of its first
reference, and carries a caption that states its source population.

## 3. Writing quality (advisory)

5,864 words of body text. None of the suite's 25 flagged terms occurs. Three patterns to review:

- **Em dashes:** 35 (6.0 per 1,000 words). Several asides would read better as commas or a
  separate sentence; keep those that carry the argument.
- **Semicolons:** 75, many joining long clauses; split where a period makes the relationship clearer.
- **Long sentences:** 40 of 239 sentences exceed 40 words (median 24). Most are in Sections III-B,
  VI-B and VI-D, where several numbers are packed into one sentence.

These do not affect the gate.

## 4. Workflow against the suite's 10-stage pipeline

| Stage | Deliverable in the suite | In this project | Status |
|---|---|---|---|
| 1 Research | RQ brief, methodology, bibliography, synthesis | `docs/research/` (survey of 49 papers, master plan), pre-registrations (`ef3f453`, Stage 1 and Stage 4 protocols) | done; the 49-paper survey is not a systematic review, as the paper says |
| 2 Write | draft | `paper/main.tex` (16 pp) and the ten-page draft | done |
| 2.5 Integrity | integrity report + corrected paper | references, citation context and numbers (2 Nov); this report adds the failure-mode checklist, caption and claim checks | **FAIL — corrections pending** |
| 3 Review | 5 reports + editorial decision + revision roadmap | not run on the ten-page draft (two blind rounds were run on the superseded 30 Sep draft) | **next — cards awaiting approval** |
| 4 Revise | revised draft + response to reviewers | — | pending |
| 3′ Re-review | revision checklist + residual issues | — | pending |
| 4.5 Final integrity | final verification, zero issues | — | pending |
| 5 Finalize | final formats | IEEEtran PDF builds; venue cut (six pages for CONECCT) not made | partial |
| 6 Process summary | process record | `RESULTS_LOG`, session memory, `paper/ieee/disclosure.md` cover most of it | partial |

Also outside the stage list: the AI-use disclosure exists in draft form (venue wording pending);
the suite's compliance check targets evidence-synthesis reporting (PRISMA-trAIce, RAISE) and does
not apply; the medical-imaging equivalent, CLAIM, is cited but the draft has not been checked
against it item by item.

## 5. Review panel setup (reviewer skill, Phase 0)

### Field analysis

| Dimension | Assessment |
|---|---|
| Primary discipline | Medical image analysis in dentistry (AI for panoramic radiographs) |
| Secondary disciplines | Evaluation methodology for machine learning (shortcuts, baselines, external validation); biostatistics (clustered resampling, random-effects pooling); dental radiology |
| Paradigm | Quantitative, empirical, with an analytic (closed-form) component |
| Methodology type | Retrospective model-evaluation study on public datasets, with pre-registered comparisons, paired cluster bootstraps and site-level pooling |
| Target venue | Field-general (no author-confirmed target; chosen 2 Nov) |
| Maturity | Advanced draft: complete and internally verified; author block, licence question and venue cut open |

### Reviewer Configuration Card #1

**Role**: EIC
**Display role**: Journal-Fit Reviewer
**Identity Description**: A senior reviewer for medical-imaging and dental-AI venues, field-general (no target journal), who has handled evaluation-methodology papers as well as system papers.
**Review Focus**:
  1. Whether the contribution — an image-blind floor with a closed-form account of it — is new for dental AI and stated in proportion to the related work it now cites (VQA and NLI input-blind baselines, medical-imaging shortcut studies).
  2. Whether the paper is one paper: a theory, a six-stage system and a multi-cohort evaluation in ten pages.
  3. Whether the title and abstract promise only what the evidence carries (for example, the lesion detector's lead "not shown for an unseen site").
**Will particularly care about**: Proportion between claims and evidence, and whether a reader outside dentistry learns something transferable.
**Possible blind spots**: Statistical detail and dental clinical nuance.

### Reviewer Configuration Card #2

**Role**: Peer Reviewer 1
**Display role**: Peer Reviewer 1 (Methodology)
**Identity Description**: A biostatistician and evaluation methodologist for diagnostic-accuracy studies with clustered data and multi-site validation (cluster bootstrap, meta-analysis of site effects, pre-registration).
**Review Focus**:
  1. Validity of the paired cluster bootstrap with 34 clusters (crop-classifier tests) and of DerSimonian–Laird pooling over k = 4 sites; alternatives such as Hartung–Knapp intervals.
  2. Selection effects and multiplicity: Ningxia informed the lesion detector's adoption, the CariesXrays validation split chose its checkpoint, and many cohort-by-arm comparisons are reported.
  3. The closed-form theory: correctness, assumptions (micro-averaged F1, codes treated independently), and the post-hoc status of Table 7.
**Will particularly care about**: Whether every interval is interpreted at the population it describes.
**Possible blind spots**: Dental clinical meaning; imaging-pipeline engineering.

### Reviewer Configuration Card #3

**Role**: Peer Reviewer 2
**Display role**: Peer Reviewer 2 (Domain)
**Identity Description**: An oral and maxillofacial radiologist with research experience in AI-assisted caries detection on panoramic and bitewing radiographs, familiar with DENTEX, Tufts and how their reference standards were built.
**Review Focus**:
  1. The reference standard: whether DENTEX caries annotations are exhaustive, and panoramic radiography's limited sensitivity for caries compared with bitewings.
  2. Clinical meaning of FDI-set F1, lesion agreement and a "flag"; caries versus deep-caries grading; adjacent-tooth numbering errors.
  3. Stage 4's relabelling as an abnormality flag, and whether any periodontal reading survives.
**Will particularly care about**: Whether the conclusions mean something to a dentist, and whether the molar prior is consistent with caries epidemiology.
**Possible blind spots**: Statistical methodology; machine-learning theory.

### Reviewer Configuration Card #4

**Role**: Peer Reviewer 3
**Display role**: Peer Reviewer 3 (Perspective)
**Identity Description**: A computer-vision researcher working on dataset bias, shortcut learning and domain generalisation, reviewing from the CV and ML community.
**Review Focus**:
  1. Whether the image-blind floor generalises beyond dentistry, and how it relates to spurious-correlation benchmarks and blind baselines.
  2. Stronger shortcut controls that are missing: a learned position-only model, occlusion of tooth content, a site-classifier test in the manner of Zech et al.
  3. Reproducibility and release: code, weights, data licences (DENTEX CC BY-NC-SA), and deployment implications.
**Will particularly care about**: Whether the lesson changes evaluation practice in medical computer vision.
**Possible blind spots**: Dental clinical detail.

### Fixed fifth seat

**Devil's Advocate** (no configuration card): challenges the core argument — for example, that the
constant is not a fair floor because it uses the pipeline's own front end; that the lesion
detector's external lead could come from its training mixture or site cues rather than from
localisation; that the closed form is elementary. It also receives the Mode 4 flag from §1.

### Checkpoint

The reviewer skill does not write any review until the cards are accepted (Checkpoint Rule 1), and
the pipeline does not enter Stage 3 while the integrity gate is FAIL. Two decisions are needed:
apply the correction list in §1 to the draft, and accept or edit the four cards above.

## 6. Re-verification after corrections (2 Nov 2026)

The owner accepted the correction list and the four cards. Corrections applied to `paper/paper.md`
and re-verified item by item:

| Item | Correction | Re-check |
|---|---|---|
| E-1 | Table 7 retitled as a post-hoc consistency check ("Implication" column); Section VII states the theory was formulated after the measurements; remaining "predicts / predictions" of the theory in III-E, VI-B, VI-D and the conclusion read "implies / implications" | present in `main.tex`; no theory sentence left claiming prediction |
| C2-1 | Table 3 Tufts row: numbering 3,760 teeth, Stage 4 3,892 teeth with 182 labelled | matches `main.tex` |
| C3-1 | Fig. 3 caption names what the 95.34 M covers (default configuration incl. withheld 4b) | matches `main.tex` parameter table |
| E-2 | Section III-B adds the single-peak argument and the exact form of the optimal set | algebra checked |
| E-3 | The unsourced claim about pre-cropped teeth reworded as an argument, not a claim about the literature | no literature claim remains |

Number trace after the corrections: 366 distinct numbers, the same six resolved by hand. Build:
10 pages, 0 errors, 0 undefined references, 0 overfull boxes (the column-table width budget in
`md_to_ieee.py` narrowed from 8.4 to 8.2 cm; Figs. 5 and 8 at 92% width; the Fig. 2 and Table 7 captions, the survey sentence, the ladder
paragraph, a Section VI-D sentence, the acknowledgment and the conclusion shortened, with no number
or claim removed).
**Verdict: PASS WITH NOTES** (notes: the writing-quality advisories of §3). Stage 3 proceeded:
`2026-11-02_panel_round1.md`.
