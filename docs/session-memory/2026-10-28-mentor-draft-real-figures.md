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
8. **Committed** at the repo owner's request as one `docs:` commit (`5f35936`), explicit paths,
   LaTeX byproducts left unstaged; then pushed to origin main on request.
9. **Second request, same day: a ten-page draft.** The owner supplied two outside drafts
   (`~/Downloads/ieee-draft-a.pdf`, `ieee-draft-b.pdf`, 27 Oct; same text, B re-laid out) and asked
   for an "induced" ten-page draft: more evidential, theoretical and explanatory, with a
   theory-driven introduction and every figure correctly placed and referenced. Both outside drafts
   quote the archived pre-switch numbers and show no radiographs; their structure was taken, not
   their numbers.
10. **New theory section (§III of the draft)**, each claim checked against a saved measurement:
    the identity chain of a tooth-indexed report; the closed-form F1 of an image-blind constant and
    the rule (add a code iff its prevalence exceeds F1/2) that reproduces the eight molars exactly;
    lesion agreement as a cohort's prior mass; the positional-shortcut signature; why localisation
    resists it; the inference model. `PAPER_MATERIAL.md` §6.8.
11. **New figure script `scripts/figures/make_draft_figures.py`** (no model run; asserts against the
    saved files): R05 positional prior, R06 architecture, R07 paired-difference forest plot with the
    random-effects prediction interval, R08 numbering / selective prediction / reliability.
12. **Build tool** gained `$…$` and `$$` math, multi-digit figure and table numbers, starred
    (full-width) tables, content-proportional column widths, float-placement parameters, and drops
    `source.bib` curation notes and URLs from the printed references.
13. **Checks:** 10 pages, 0 errors, 0 undefined references, 0 overfull boxes; 364 distinct numbers
    traced (script in the scratchpad); `verify_paper_numbers.py` 215/215. Records: `RESULTS_LOG`
    2026-10-28b, `PAPER_MATERIAL.md` §6.8 and §9, `transfer.md`, `paper/ieee/open_issues.md`.
    Not committed. (An attempt to e-mail the PDF failed: Claude in Chrome was never connected, and
    the owner dropped the request on 2 Nov.)
14. **Third request, 2 Nov 2026: citations, with the academic-research-skills suite.** Cloned
    `Imbad0202/academic-research-skills` (commit `a41f3b2`) to a temp folder outside the repo, read
    its citation design (four-index triangulation, the C-V6 `false`/`unresolvable` rule,
    claim-faithfulness audit) and its four resolver clients, then ran those clients unmodified on
    the draft's references, all of `source.bib` and 19 candidates; added a retraction check and an
    abstract/full-text claim check. Results, scripts and README saved to
    `outputs/citation_audit/2026-11-02_ars/`; `RESULTS_LOG` 2026-11-02.
15. **Fixed in `paper/source.bib`** (reaches `main.tex`): Zancan URL and issue, Bilal URL, Bizjak
    issue/pages, Mutlu volume/pages, DENTEX title, YOLO11 citation, "and Others", 12 curation notes
    to `annote`; 14 new Crossref-generated entries. `main.tex` rebuilt: 16 pages, 215/215.
16. **Draft re-cited:** every citation by key from `source.bib` (the registry had a wrong Li et al.
    title); Related Work rebuilt around verified evidence (input-blind baselines in VQA and NLI,
    medical-imaging shortcuts, the 6% external-validation rate, a caries review); methods cited
    (cluster bootstrap, DerSimonian–Laird, I², prediction interval, ECE, selective classification);
    "four hospitals" → "four sites"; Cao's unverifiable number dropped. Build tool: IEEE venue
    abbreviations, six-author et al., figure scaling, unsplittable code listing. Final: 10 pages,
    36 references (34 resolve on the indexes, 2 confirmed at source), 363 numbers traced. Not
    committed.

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
- **Ten pages by cutting duplicates, not evidence:** `fig_baselines.png` (same numbers as Tables 4/6
  and the forest plot), the parameter table (now in Fig. 3) and the Stage-4 chart (numbers kept in
  the text) were dropped; reference URLs were dropped from the printed list.
- **One sign convention:** every difference is system minus comparator, so the crop classifier's
  Ningxia result reads +0.89, where `main.tex` writes the constant-minus-pipeline -0.89.
- **The theory is stated only as far as the data checks it**; the one prediction the data did not
  support (that the prior carries the classifier's ranking) is shown as such in Table 7.
- **Use the external skill's method, not install it.** The suite is a large Claude Code plugin; its
  value here is the resolver clients and the verification rules. Running the clients from a temp
  clone (after reading them) changes nothing in the user's Claude configuration and leaves no
  CC BY-NC code vendored in this repo.
- **A citation is kept only if the cited text supports the sentence**: the Li et al. "four
  hospitals" wording was changed, Cao's 61.83 dropped (not verifiable), Zancan's 0.9988 given with
  its F1. New citations were chosen for claims the draft already made, each checked the same way.
- **Fix `source.bib`, not the draft's copy**, so `main.tex` gets the corrections; the draft's
  build applies only presentation (abbreviations, et al., no URLs).

## Open questions

- DENTEX share-alike versus the venue's copyright form (`PAPER_MATERIAL.md` §8.19) — decide before any
  submission.
- Should Figures 1, 2, 3 and 5 go into `main.tex` and the planned six-page CONECCT cut? The cut
  drops Stage 4 and numbering; Figures 1, 2 and 5 are caries-relevant and would survive.
- The draft is 10 pages against CONECCT's 6; which venue the ten-page version is for is open.
- Author block, pre-registration public anchor, VLM decoding settings (`paper/ieee/open_issues.md`).
- Whether the theory section (§6.8) goes into `main.tex`.
- `main.tex` still says "four hospitals" for Ningxia and cites Cao's unverified 61.83; five
  `main.tex`-only bibliography follow-ups (`PAPER_MATERIAL.md` §9).

## Next steps

1. Repo owner reads the ten-page `paper/ieee/main.pdf` and sends change requests.
2. Settle the DENTEX share-alike question with the mentor and the venue's form.
3. Move `source.bib` curation notes to a non-printing field and rebuild `main.tex`.
4. If accepted, port the theory and the radiograph figures into `main.tex` and point
   `verify_paper_numbers.py` at the chosen cut.
