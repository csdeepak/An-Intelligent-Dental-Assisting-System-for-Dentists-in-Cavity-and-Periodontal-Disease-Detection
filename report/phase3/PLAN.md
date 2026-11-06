# Phase 3 report: build plan and conventions

This file is the working memory for the Phase 3 capstone report (UE23CS441A). Re-read it before
editing. The report is the successor of the Phase 2 report (`PW26_MHR_06_Report.pdf`, Jan–May
2026). It is built on branch `report/phase3` in the worktree `.claude/worktrees/phase3-report`.
Side deliverables never go on `main`.

## Brief from Deepak (6 Nov 2026)

**Format**
- Build in LaTeX and compile locally with MiKTeX (XeLaTeX).
- Follow the college guidelines (`Report- Guidelines.pdf`) and the initial-pages templates
  (`Report initial Pages(Pg 1-10).zip`) in Downloads.
- Fonts, visualisations and colour theme match the Phase 2 report.
- Never cut content to save pages.

**Content**
- Keep about 60–70% of the Phase 2 content and remove what is unnecessary.
- Keep every Phase 2 image and table.
- Use every picture, diagram and workflow that helps.
- Bring every Phase 3 result and novelty up to date with the repository.

**Process**
- Use the Research Communication Engine (`csdeepak/research_writing_skill`) for content
  preparation and validation.

## Guidelines (the binding ones)

| Item | Rule |
|---|---|
| Paper | A4; margins 2.00 cm on all sides |
| Text | 1.5 line spacing (text only); body 12 pt Times New Roman; justified |
| Chapter title | "CHAPTER N" + title, centred, 18 pt |
| Section | number + title, left, 16 pt |
| Subsection | number + title, left, 14 pt |
| Numbering | Arabic chapters; sections 2.1, subsections 2.1.1; figures, tables and equations numbered within the chapter |
| Front matter | Inner title page, Certificate, Declaration (template), Acknowledgement (14 pt bold heading), Abstract (≤150 words), TOC, List of Figures, List of Tables |
| Chapters | Introduction · Problem Statement · Literature Review · Project Requirements Specification · HLD · LLD · System Design (detailed) · Proposed Methodology · Implementation and Pseudocode · Results and Discussion · Conclusion and Future Work · References · Appendix A (definitions, acronyms) · Appendix B (user manual) |
| Header | Project title at left, institution logo at right. **None on a chapter's first page**. Headers and footers start at the Introduction |
| Footer | "Dept. of CSE" (left) · "August – Dec, 2026" (centre) · "Page No. N" (right) |
| References | IEEE style, numbered in order of first citation, in square brackets |
| Units and quotes | SI units only; no verbatim reproduction; any quotation in quote marks and cited |
| Acknowledgement order | guide, project coordinator (Dr. Chaitra B), Chairperson (Dr. Shylaja S S), Registrar (Dr. Sridhar K S), Vice-Chancellor (Dr. Suryaprasad J), Chancellor (Prof. Jawahar Doreswamy), family and friends |

## Phase 2 theme to reproduce

- **Cover:** title in #4A86E8 at 18 pt; date in red.
- **Header:** project title in italics on two lines at left, PES logo at right, a rule below.
- **Footer:** a rule above the three fields.
- **Captions:** "**Figure N.M:** text", centred, below the figure. "**Table N.M:** text", centred,
  above the table. Booktabs rules only.
- **Diagram palette** (sampled from the Phase 2 figure 3.1 image):

  | Role | Colour |
  |---|---|
  | Stage boxes | indigo #3C348A |
  | Caries branch | teal #085142 |
  | Bone-loss / abnormality branch | maroon #6F271D |
  | Filter | orange #BA7218 |
  | Report | green #244E06 |
  | Input / output | dark grey #474348 |
  | Arrows | grey #9E9A94 |

  The taxonomy figure adds navy #1B2F3A, teal #2A4E4F, mint #DBECE5, pink #F2D6D0 and sage #528075.
- **Plots:** Blues and Oranges colour maps for confusion matrices (as Phase 2); Times New Roman in
  the plots.

## Evidence rules (RCE)

- **Sources of numbers,** in this order:
  1. `paper/paper.md` (the ten-page draft, number-traced 390 / 6 known and verified 215/215);
  2. `transfer.md` §2;
  3. `docs/results/model_metrics.md`;
  4. the `models/*/run_summary.txt` files;
  5. the `outputs/**` JSON files.
- **Never invent a number.** Anything not in those files is `[MISSING]` and goes to
  `open_issues.md`.
- **Phase 2 numbers** that were later corrected stay in the report, labelled as the Phase 2 value,
  with the correction beside them. The bone-loss macro-F1 0.9233 came from a crop-level split; the
  held-out and radiograph-split results replace it.
- **Licences.** DENTEX images are CC BY-NC-SA 4.0. Phase 2 figures 5.1–5.3 show Tufts pixels,
  whose licence forbids redistribution. They are kept at Deepak's request and flagged in
  `open_issues.md`.
- **Validation (RCE).** `tools/export_md.py` renders the TeX into `build/report.md`, with claim
  tags written as `%{C###}` comments in the TeX. That file is checked with:
  - `validate_artifacts.py` (G1);
  - `lint_draft.py` (G3/G5);
  - `verify_numbers.py --strict` (numbers);
  - `skim_layer.py` on the abstract.

  Integrity (GI) and the panel need isolated roles, which were not run, so they are recorded as
  `unverified`.

## Status (6 Nov 2026)

**Built.** `Phase3_Report_PW26_MHR_06.pdf` has 114 pages: 15 front-matter pages, 11 chapters,
references and two appendices. The build has 0 errors, 0 undefined references and 0 overfull boxes.
Nothing is committed: the whole of `report/` is untracked on branch `report/phase3`.

**Validated.** Run the chain in this order:

1. `bash tools/build.sh`
2. `python -I tools/rcs_build.py`
3. `python -I tools/export_md.py`
4. `python -I tools/rcs_quotes.py`
5. `python -I tools/rcs_check.py`
6. `python -I tools/check_report.py`

Results of the last run:

| Check | Result |
|---|---|
| G1 artifacts | PASSED: 0 errors; 71 warnings (70 claims pending author confirmation, plus C001 resting on soft evidence) |
| G3 lint | PASSED: 0 errors, 14 warnings |
| G3 numbers, `--strict` | PASSED: every number in the report traced, 0 untraced |
| GL citations | PASSED: 62 sources, each with a verbatim support quote |
| Abstract skim check | 0 errors |
| G4 panel, GI integrity | not run (isolated roles unavailable), recorded as such |
| `check_report.py` | all PASS; 1 OPEN (the acknowledgement's CEO paragraph) |

**Left for the authors:** see `open_issues.md`. Before submission that means the CEO's name,
signatures, and confirming the claims.

**One-off fixers,** kept for the record:

- `tools/fix_fr_table.py`
- `tools/fix_overfull.py`
- `tools/fix_claim_tags.py`, which adds the claim tags, defines acronyms at first use and gives every
  float a lead-in. It can be re-run safely.

**In git, and what is not** (branch `report/phase3`; `report/phase3/.gitignore`). The sources, diagrams,
plots, the project's own Phase 2 charts, the logo and the tools are committed. These are kept out:

- **The RCE trail, `.rcs/`:** the claim map, registry, evidence copies and gate reports stay local
  under the repository's rule for RCE trails (root `.gitignore`), as the paper's trail does. The
  `tools/` scripts rebuild them: `rcs_build.py`, `fetch_abstracts.py`, `fetch_meta.py`,
  `rcs_quotes.py` and `rcs_check.py`.
- **Build outputs:** `build/`, `references.bib`, and the PDF itself.
- **`figures/repo/`:** byte copies of figures tracked elsewhere in the repository. `tools/build.sh`
  refreshes them on every build.
- **Third-party figures:** the paper figures reproduced in Chapter 3 (`figures/phase2/p2_2_*`).
- **Tufts crops:** `figures/phase2/p2_5_*`.
- **App screenshots:** `figures/screens/`.

`python -I tools/restore_images.py` restores the paper figures and Tufts crops from the Phase 2 `.docx`,
checking each against its hash. The screenshots must be recaptured; the steps are in the script's
docstring. A fresh clone still builds without any of them: `\optionalgraphics` draws a framed
placeholder.

**Network helpers,** for public metadata only:

- `tools/fetch_abstracts.py` writes `.rcs/corpus/p3c_abstracts.json`.
- `tools/fetch_meta.py` writes `.rcs/corpus/openalex_meta.json`.
