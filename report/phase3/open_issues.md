# Open issues: Phase 3 report (PW26_MHR_06)

Written 6 November 2026, after the build and the Research Communication Engine (RCE) checks. Each item is
something the authors must decide or supply; none of them stops the PDF from building. Items marked
**before submission** affect what the college receives. The others matter only if the report or its
figures are published.

## Needs the authors before submission

1. **The CEO paragraph of the acknowledgement.** The guideline's order is guide, project coordinator,
   Chairperson, Registrar, Vice-Chancellor, **CEO**, Chancellor, parents, family and friends, each in its
   own paragraph. The CEO's name is not in the college template and has not been guessed. A comment in
   `frontmatter/acknowledgement.tex` marks where the paragraph goes. `tools/check_report.py` reports
   this as OPEN.
2. **Signatures and the viva table.** The certificate page has signature lines for the guide, the
   Chairperson and the Registrar, and two blank External Viva rows. The declaration has blank signature
   cells. These pages are signed by hand.
3. **Author confirmation of the claims.** All 70 claims and 5 limitations in
   `.rcs/claims/claim_evidence_map.json` are `author_confirmation: pending`. The skill expects each to be
   confirmed or rejected by an author. The ones the abstract rests on are C001, C002, C010, C013, C022,
   C024 and C040. The validator (G1) shows each pending claim as a warning.

## Data and image rights (before any public release)

4. **Tufts radiograph pixels in Figures 9.2, 9.3 and 9.4.** These are the Phase 2 crop grid, crop samples
   and CEJ overlays (Phase 2 Figures 5.1 to 5.3). The Tufts Dental Database terms do not allow its images
   to be redistributed. The figures are kept because the authors asked for them, and an internal college
   submission is the use they were made for. Remove or replace them before the report goes anywhere
   public.
5. **Figures reproduced from published papers.** Figures 3.1 to 3.10 reproduce one figure from each
   reviewed paper, as the Phase 2 report did. Each caption credits its source. An internal academic report
   can include them, but a public version needs permission or a redrawn figure.
6. **DENTEX images (CC BY-NC-SA 4.0).** Figures 1.1, 7.3 and B.1, and the overlays in Chapter 10, show
   DENTEX radiographs, and their captions credit DENTEX. A public version must keep the non-commercial,
   share-alike terms.

## Citations the GL gate accepts with a caveat

The gate is `.rcs/audits/gates/GL_citations.json`. Each item below is a source whose support quote could
not come from an abstract.

7. **SRC-010, Bizjak and Robič (2024), *Informatica Medica Slovenica*: `lookup_verified: unresolvable`.**
   The paper has no DOI, and no abstract is available from OpenAlex, Crossref, PubMed or Semantic Scholar.
   The report cites a lesion sensitivity of 0.70 internally and 0.67 externally. Those values were checked
   against the PDF text when the citation was added (`docs/results/RESULTS_LOG.md`, the entry that cites
   Bizjak and Robič). The registry's support quote is the title only. Re-check both numbers against the
   PDF.
8. **SRC-029, Ultralytics YOLO11 (software, Jocher and Qiu): `lookup_verified: unresolvable`.** This is a
   software citation with no DOI. Its support quote is the title.
9. **SRC-043 (Mongan et al. 2020, CLAIM), SRC-054 (Schwendicke et al. 2021) and SRC-047 (Nassiri and
   Akhloufi 2025).** No abstract was retrievable for any of them, so each support quote is the title. The
   two checklists are cited only as reporting checklists. The Nassiri entry carries no numbers, because
   none could be checked.
10. **Zancan et al. (2025).** The report gives the full-text numbering accuracy, 0.9988 with F1 0.979, as
    recorded in `docs/results/PAPER_MATERIAL.md`. The abstract, which is the support quote, rounds these to
    0.998 and 0.98.
11. **Pakdaman Naeini et al. (2015) and Zadrozny and Elkan (2002).** These are cited for the expected
    calibration error and for isotonic regression. Both terms appear in the papers' bodies, not their
    abstracts, so the quotes support only the general calibration method.
11a. **Retraction status not checked for SRC-012 (Budagam et al. 2024), SRC-020 (Geifman and El-Yaniv
    2017) and SRC-023 (Guo et al. 2017).** These are an arXiv preprint and two conference papers
    (NeurIPS and ICML) with no DOI, so the DOI-based retraction lookup used for the other sources cannot
    reach them. No withdrawal is known. The registry records their status as `unknown`.

## Corrections made during validation (6 Nov 2026)

12. **Asci et al. (2024).** The Strengths list of Section 3.2.7 gave the permanent-dentition figures
    (0.8271, 0.9125, 0.8677) as the result over all dentition groups. The abstract reports the total group
    as 0.8269, 0.9123 and 0.8675, and these are now in the text. The error was introduced while this
    report was being written. It was not in the Phase 2 report.
13. **A misread notice in the registry.** In the 2 Nov audit, `zhu2026dentfound` carries a *correction*
    notice, not a retraction. The first registry build marked it as retracted. The source is not cited in
    this report, and the registry now holds only the 62 cited sources.

## Not done in this session

14. **The G4 review panel and the GI integrity verifier did not run.** They need isolated reviewer and
    verifier roles that this session does not have, so `.rcs/state.json` records them as `not run`.
15. **The Ningxia per-type comparison is blocked.** It needs the raw Ningxia images, which are on the
    external D: drive, and the drive was not attached (Future Work item 1).
16. **The runtime claim (C001) has no saved run artefact.** The 1.70 s per image figure is recorded in
    `RESULTS_LOG.md` and `model_metrics.md` but not in a timing file, so G1 warns that C001 rests on
    soft evidence only.

## Lint warnings left as they are

The current list is in `.rcs/audits/gates/G3_lint.json`. It has no errors.

- **A6-result-dumping (12).** Runs of three or more sentences with numbers in Chapter 10. These are
  results paragraphs, and each one ends in the sentence that interprets it.
- **C1-orphan-claim.** The FDI description in Section 1.1 is flagged because "lower-left" and "lower
  right" match the linter's comparative-word list. The two future-work items are flagged for "reduce".
  Neither is a claim.
- **A-long-sentence (INFO).** Sentences over 35 words, mostly in the literature entries carried over from
  Phase 2.
