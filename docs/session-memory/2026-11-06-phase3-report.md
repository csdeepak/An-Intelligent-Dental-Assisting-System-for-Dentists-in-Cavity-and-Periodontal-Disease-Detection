# 2026-11-06: The Phase 3 capstone report, written in LaTeX and validated with the RCE skill

**Session goal:** produce the full Phase 3 capstone report (UE23CS441A, PW26_MHR_06) as the successor
of the Phase 2 report. It had to follow the college guidelines and templates and keep the Phase 2
theme, and every claim, number and citation had to be validated with the Research Communication
Engine (RCE) skill.

This session also covered the 2 Nov review-round-1 work. That work was committed and pushed to `main`
(`517123e`, `02b63a7`, `851f089`) and is logged in `RESULTS_LOG.md` as 2026-11-02b to d. This file
covers the report only.

## What was done

- **Inputs and location.**
  - The inputs were:
    - the Phase 2 report (`Downloads/PW26_MHR_06_Report.pdf`);
    - the college `Report- Guidelines.pdf`;
    - the initial-pages templates (`Report initial Pages(Pg 1-10).zip`).
  - The report lives in the worktree `.claude/worktrees/phase3-report`, on branch `report/phase3`
    (based on `851f089`), under `report/phase3/`. Everything there is untracked; nothing is
    committed.
- **Build.** XeLaTeX with BibTeX (IEEEtran), Times New Roman, the Phase 2 palette and caption style.
  - The bibliography is `paper/source.bib` plus `extra.bib` (Albano 2024, Iacob 2025).
  - The output is `Phase3_Report_PW26_MHR_06.pdf`, 114 pages, with 0 errors, undefined references or
    overfull boxes.
- **Content.**
  - Eleven chapters in the guideline's order, plus two appendices (definitions and acronyms; the user
    manual).
  - Phase 2 content is carried at roughly 60–70%, with all its images. Phase 2 numbers that were later
    corrected are labelled and corrected (bone-loss 0.9233; the claimed "OPG-level split").
- **Figures.**
  - 14 TikZ diagrams.
  - 8 plots generated from saved outputs (`tools/make_plots.py` asserts each value it draws).
  - 22 Phase 2 images.
  - 8 repository figures.
  - 3 screenshots of the Streamlit app running on DENTEX `test_0`.
- **RCE trail** (`report/phase3/.rcs/`):
  - `tools/rcs_build.py` builds the trail: 58 evidence items, 70 claims, 5 author-stated limitations
    and a registry of the 62 cited sources.
  - `tools/export_md.py` renders the TeX as Markdown for the checks. Claim tags are TeX comments
    (`% {C###}`), and citations come out in author-year form.
  - `tools/rcs_quotes.py` attaches a verbatim support quote of at most 40 words to every source.
    `tools/fetch_abstracts.py` and `tools/fetch_meta.py` fetched the missing abstracts, author lists
    and retraction flags from OpenAlex, Crossref, PubMed and arXiv.
  - `.rcs/story/spine.md` holds the seven-line spine.
- **Gates** (`tools/rcs_check.py`; reports in `.rcs/audits/gates/`):
  - G1, G3 lint, G3 numbers (`--strict`: every number traced) and GL all PASSED;
  - the abstract skim check had 0 errors;
  - G4 and GI were not run, because the isolated roles are not available in this session.
- **Report checks.** `tools/check_report.py` checks:
  - the abstract (149 words, two paragraphs);
  - the chapter order;
  - the acknowledgement order;
  - that every one of the 98 floats is referenced;
  - the citations;
  - that the claim tags and the claim map match exactly;
  - the build log.

  All pass, with one item OPEN (the CEO).
- **Errors found and fixed during validation:**
  - **Asci et al. 2024.** The text printed the permanent-dentition figures (0.8271 / 0.9125 / 0.8677)
    as the total. The abstract's total group is 0.8269 / 0.9123 / 0.8675. The error was introduced in
    this session.
  - **Acknowledgement.** It followed the template's single sentence (Chancellor before Vice-Chancellor).
    The guideline asks for separate paragraphs, with the Vice-Chancellor, then the CEO, then the
    Chancellor. Now fixed, with the CEO left open.
  - **TOC, LOF and LOT.** Their first pages carried the footer, although the guideline starts headers
    and footers at the Introduction. The TOC section numbers 10.10–10.14 also ran into their titles.
  - **Floats.** 15 floats had no reference in the text. Each now has a lead-in sentence.
  - **Acronyms.** FDI, OPG, ROC, AUC, NMS, CLAHE, AP and CI are now defined at first use.
  - **"Outperforms".** One literature sentence asserted "outperforms". It is now attributed as a
    reported result.
  - **Registry.** The first registry build read a Crossref *correction* notice as a retraction. That
    source was not cited in the report.
- **Commits on `report/phase3`, at Deepak's request ("Yes, commit it"); not pushed.**
  - `5fdb9e5`: the report sources, diagrams, plots, the project's own Phase 2 charts, the logo, and the
    build and restore tools.
  - `6020b2d`: the RCE validation tooling.

  Kept out of git (`report/phase3/.gitignore`):
  - the build outputs and the PDF;
  - `figures/repo/`: byte copies of tracked figures, which `build.sh` refreshes on every build;
  - the Chapter 3 figures reproduced from papers;
  - the Tufts crops;
  - the app screenshots;
  - the `.rcs/` trail.

  `tools/restore_images.py` restores the paper figures and the Tufts crops from the Phase 2 `.docx`,
  checking each against its SHA-256. `\optionalgraphics` lets a fresh clone build with placeholders.
  This was tested: with the images moved away the build gave 112 pages, 0 errors, 0 overfull boxes.

## Decisions made

- **LaTeX, not docx.** Deepak asked for TeX "for your easy editing". The theme was rebuilt in LaTeX
  rather than edited in the converted `.docx`, which has zero right margins and text boxes.
- **The report stays on its own branch** (`report/phase3`, worktree), per the side-deliverable rule.
  `main` carries no report files.
- **Tags are TeX comments, and the check runs on a Markdown view.** The PDF carries no RCE markup, and
  the skill's tools read Markdown.
  - A tag at the end of a paragraph applies to every sentence of that paragraph.
  - A tag-only line under `\litmeta` applies to the whole literature entry.
  - A tag after a float or list applies to every row or item.
- **Literature claims are claims too.** Each reviewed paper and each thematic paragraph is a
  `literature` claim, and its sources resolve to registry IDs. This way GL checks every citation
  against a quote, not only the project's own results.
- **The CEO's name is not guessed.** It is missing from the template, and a wrong name in an
  acknowledgement is worse than an open item.
- **Gates are marked passed only from a clean tool report.** G4 and GI are recorded as `not run`, not
  as unverified passes.
- **`.rcs/` stays local.** The root `.gitignore` already says the RCE audit trail is local only, and the
  report follows it. The tools that rebuild the trail are committed.
- **Images follow the repository's rule.** The root `.gitignore` ignores `*.jpg` and `*.png`, and the
  side-deliverable rule keeps dataset-derived and rendered images out.
  - Re-included: the project's own Phase 2 charts and diagrams and the PES logo (no radiograph pixels,
    no third-party figures, about 0.6 MB in all), so a fresh clone builds.
  - Kept out: the third-party figures, the Tufts crops and the screenshots.
- **No duplicate binaries.** The 14 figures under `figures/repo/` are copied from their tracked
  originals at build time instead of being committed a second time.

## Open questions

All 16 are in `report/phase3/open_issues.md`. The ones that need Deepak:

- the CEO's name;
- signatures;
- author confirmation of the 70 claims;
- whether the Tufts-pixel figures 9.2 to 9.4 and the reproduced paper figures 3.1 to 3.10 stay in the
  copy that is submitted.

## Next steps

1. **Supply the CEO's name.** Add the paragraph between the Vice-Chancellor and the Chancellor in
   `frontmatter/acknowledgement.tex`, then run `bash tools/build.sh`.
2. **Confirm the claims.** Deepak confirms or rejects each claim. At minimum this covers the abstract's
   claims C001, C002, C010, C013, C022, C024 and C040. Mark them in `rcs_build.py` and re-run the
   chain in `PLAN.md`.
3. **Pointer on `main`.** The report is committed on `report/phase3` (`5fdb9e5`, `6020b2d`) and is not
   pushed. Decide whether `transfer.md` on `main` should point to the branch. The branch itself is never
   merged into `main`.
4. **Run the PESU library plagiarism check** (at most 15%, guideline 22). Then sign and submit.
