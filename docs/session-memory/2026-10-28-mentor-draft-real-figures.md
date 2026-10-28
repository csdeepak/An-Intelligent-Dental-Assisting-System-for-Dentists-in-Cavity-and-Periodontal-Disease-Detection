# 2026-10-28 — Mentor draft rebuilt on the current pipeline, with real radiographs and training curves

**Session goal:** one line — answer the repo owner's review of the mentor draft ("no evident results
from training and testing; only generated chart images") with real-radiograph evidence, and make the
draft's content correct for an IEEE reviewer who knows computer vision but not OPGs.

## What was done

1. **Revisited the content first, as asked.** The 30 Sep RCE draft (`paper/paper.md`,
   `paper/ieee/main.pdf`, `3cc15fe`) predated origin's 11–15 Oct work: it described the old Tufts-only
   detector, called Stage 4 a periodontal bone-loss gate with the leaked 0.923, and quoted pre-switch
   numbers. Adding figures alone could not make it correct.
2. **A question about which document to change was dismissed when the app closed**; on "continue" the
   recommended option was taken: rebuild the 8-page draft on the numbers `paper/main.tex` verifies.
3. **New figure script, `scripts/figures/make_opg_figures.py`.** Runs the shipped code path
   (`load_models` → `run_pipeline`, `run_lesion_detector_raw`, `draw_overlay`) on held-out DENTEX
   images and asserts each image's counts equal the saved evaluation before drawing. Outputs in
   `paper/ieee/figures/`: `R01_opg_primer.pdf` (quadrants, FDI codes, expert caries, the constant's
   molars), `R02_walkthrough.pdf` (stages 1–6 on `test_0`), `R03_outcomes.pdf` (rule-chosen 7/7, 2/3,
   0/4 cases, lesion detector beside the constant), `R04_training.pdf` (training logs of the four
   trained stages), plus `R_figures_facts.json` and `R02_test_0_report.json`.
4. **Draft rewritten** (`paper/paper.md`, 7 pages): OPG primer for the CV reader; system walkthrough
   with a real JSON record; §V-A on training; current RQ1–RQ3 results; Stage 4 as an abnormality flag
   measured held out. Reused `paper/fig_baselines.png` and `paper/fig_stage4a.png` (current charts).
5. **Build tool extended** (`paper/ieee/md_to_ieee.py`): PDF/PNG figures (`*` = full width),
   `[@key]` citations copied from `paper/source.bib`, code blocks, panel references
   ("Figure 4a" → "Fig. 4(a)"), a minus sign opening a table cell, wider text columns.
6. **Checks.** All 286 distinct numbers in the draft trace to `main.tex` or the saved figure facts /
   run files (script in this session, scratchpad); the JSON excerpt matches the saved report. PDF:
   7 pages, 0 errors, 0 undefined references, 0 overfull boxes.
7. **Records:** `RESULTS_LOG` 2026-10-28; `PAPER_MATERIAL.md` §8.19 (DENTEX share-alike note) and §9
   (new item); `transfer.md` header entry; `paper/ieee/open_issues.md` and `disclosure.md` rewritten
   for the new version.
8. **Committed** at the repo owner's request as one `docs:` commit, explicit paths, LaTeX byproducts
   left unstaged; not pushed.

## Decisions made

- **Rebuild rather than patch the 8-page draft:** its stale content would have contradicted the new
  figures (a walkthrough of the arm3c detector beside text about the Tufts-only one).
- **DENTEX pixels only.** Tufts' licence forbids redistribution; Ningxia and CariesXrays state none.
  DENTEX is CC BY-NC-SA 4.0 — attributed in every caption; share-alike recorded as an open item, not
  silently assumed fine.
- **Images chosen by rule, not by eye**, from the saved per-image evaluation, and stated in the text:
  most lesions all found; most lesions none found; `test_0` near the cohort rate. A failure row is
  shown on purpose.
- **Training curves labelled as validation-split selection diagnostics**, not results; the detector's
  still-rising curve and Stage 4a's sub-0.6 validation F1 are said plainly.
- **Every prediction from the shipped functions**, not a re-implementation, with an assertion tying
  each image to the paper's own evaluation — so a figure cannot show a different model.
- **`main.tex` left unchanged**; whether the figures go into it and into the six-page cut is the
  owner's call.

## Open questions

- DENTEX share-alike versus the venue's copyright form (`PAPER_MATERIAL.md` §8.19) — decide before any
  submission.
- Should Figures 1, 2, 3 and 5 go into `main.tex` and the planned six-page CONECCT cut? The cut
  drops Stage 4 and numbering; Figures 1, 2 and 5 are caries-relevant and would survive.
- The draft is 7 pages against CONECCT's 6.
- Author block, pre-registration public anchor, VLM decoding settings (`paper/ieee/open_issues.md`).

## Next steps

1. Repo owner reads `paper/ieee/main.pdf` (committed; the four figure PDFs are 4.8 MB).
2. Settle the DENTEX share-alike question with the mentor and the venue's form.
3. If accepted, port Figures 1, 2, 3 and 5 into `main.tex` (`make_opg_figures.py` can write a second
   copy) and point `verify_paper_numbers.py` at the six-page cut when it exists.
