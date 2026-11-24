# Open issues — research_paper/ (read this first)

Everything unresolved, in plain language. Items marked **[ASK AUTHOR]** need the authors; nothing
here can be settled from the repository.

## Must resolve before any submission

1. **[ASK AUTHOR] Author block** — names, affiliations, e-mail addresses (placeholder in the title block).
2. **[ASK AUTHOR] CPU model** for the 1.70 s/image runtime (Section IV).
3. **[ASK AUTHOR] Data and code availability** — release decision; a public anchor for the lesion
   detector's pre-registration commit (`ef3f453`, private repository).
4. **[ASK AUTHOR] Ethics statement** — whether the institution requires an exemption statement for
   public de-identified datasets.
5. **[ASK AUTHOR] Acknowledgment / AI-use wording** — draft in the paper and in `disclosure.md`.
6. **[LICENCE] DENTEX pixels** appear in Figures 1, 4 and 7 under CC BY-NC-SA 4.0; share-alike must be
   reconciled with the venue's copyright form or the figures replaced (`PAPER_MATERIAL.md` §8.19).
7. **[LICENCE] Kaggle "dual-labelled" FDI set** has no stated licence and is in the default detector's
   training mix (`transfer.md` §4).
8. **[VENUE] Length.** 14 pages in IEEE conference format. IEEE CONECCT 2027 (the planned venue,
   `transfer.md` §5) takes six; JBHI charges past 8. A venue decision, then a cut, is needed.
9. **[TITLE] The repository/capstone title promises "Periodontal Disease Detection".** No stage
   detects periodontal disease (`clinical_validity_assessment.md` §3). The paper title proposed here
   drops it; the authors decide.

10. **[CODE, owner's call] Stage-3b caries severity grade** is shown in every report but has no test
    (tuned and reported on the same 133 crops). Reviewer B recommends withholding it by default, as
    was done for the Stage-4 grade on 14 Oct. Not changed here: it is a functional change to the
    shipped pipeline.
    **Update 24 Nov 2026:** a retrained head of the same architecture now has a pre-registered
    held-out test (`RESULTS_LOG` 2026-11-24, `models/20_caries_severity_v2/`):
    - **Result:** macro-F1 0.772 [0.711, 0.828] on 395 DENTEX `splits_v2` test crops; eligible.
    - **Not the default.** The shipped head is still the default and still untested, so
      Table 3's row stays true.
    - **Three options:**
      1. adopt the retrained head and rewrite the row;
      2. keep the shipped head and cite the retrain as evidence for the architecture;
      3. withhold the grade.
    Paper wording if adopted: `docs/results/PAPER_MATERIAL.md` §8.46.
    **Decided 24 Nov 2026: adopted** (`RESULTS_LOG` 2026-11-24b).
    - **Updated:** `paper.md` and its generated `paper.tex`, `paper_clean.md`, `tables/table_3.*`
      and `turnitin/` md and tex.
    - **Still owed:** rebuild `final_research_paper.pdf` and `turnitin/paper_no_citations.pdf`
      with pdfLaTeX (`tools/build_paper.py`, `tools/build_no_citations.py`; no pdfLaTeX on the
      Mac), and regenerate the evidence registry (L010 still says "untested severity grade").
11. **[RECORD] `models/16_lever_b_pooled/run_summary.txt`** gives the best epoch as 54; its own
    `results.csv` gives 29, which the paper uses. Fix the summary (found by the VERIFIER).
12. **[REPRODUCIBILITY] Windows vs macOS.** A 23 Nov rerun of the shipped pipeline on the 164 DENTEX
    images on this Windows clone flagged different caries codes on 12 images than the saved macOS run
    (`audit_runs/review_round_analyses.json`). Both are reported; the paper's tables keep the saved run.

## Citation coverage gaps (GL)

- **SRC-016 Bizjak & Robič 2024** (*Informatica Medica Slovenica*) — `unresolvable` on Crossref,
  OpenAlex, Semantic Scholar and arXiv (not indexed). Confirmed at the publisher's PDF on 2 Nov 2026
  (`outputs/citation_audit/2026-11-02_ars/README.md`). Kept.
- **SRC-046 Ultralytics YOLO11** — software; no index record expected. Kept as a software citation.

- **GI M2 (INSUFFICIENT_EVIDENCE, non-blocking at stage pre).** These literature numbers have no saved
  quote in `research_paper/literature/` or `outputs/citation_audit/`, though none was found overstated:
  Zancan (0.9988, F1 0.979, read in full text 2 Nov), Bizjak (0.70/0.67, publisher PDF 2 Nov), Li 2024
  ("three hospitals", full text 2 Nov), Chen 2024 (AP 48.2, AP50 84.1, baseline 42.2; AAAI PDF 4 Sep),
  Akarslan 2008, Batchelor 2004. Save the quoted passages before final integrity (stage final blocks on it).

## Evidence gaps (stated in the paper as limitations)

- Ningxia per-tooth-type comparison: blocked — raw images (`D:\nangxia_dataset`) not attached on this
  machine; the per-tooth records were never saved.
- Learned position-only floor, content ablation, site-identification probe: not run (new compute,
  needs a pre-registration).
- No clinician comparison, no reader study, no healthy-control cohort; Stage 3b has no test.
- No periodontal label anywhere in the project.

## Workflow caveats (RCE)

- The C0 config, G1 spine/claim confirmation and G2 outline approval were not shown to a person
  during this run; they are recorded as accepted workflow risks in `.rcs/state.json` and must be
  confirmed by the authors.
- The VERIFIER and the three reviewers are separate Claude subagents of the same model family, not
  independent humans.

## Abstract and Introduction v3 (24 Nov 2026)

- Two citations were added for the narrative opening: `hennig2023frequency` and
  `schwendicke2015radiographic`. Both were checked on PubMed and Crossref
  (`literature/abstracts_intro_v3_2026-11-24.json`), but they are not yet in the RCE source registry
  or the evidence map, so GL `verify_citations` and the integrity gate have not been re-run with
  them. `verify_numbers` flags 9,680 (from Hennig) as untraced for the same reason.
- "Most widely taken **extraoral** dental X-ray" is the strongest wording the sources support.
  Intraoral films are taken more often overall, and Hennig's 78% comes from one university
  department and patients up to 18 years.
