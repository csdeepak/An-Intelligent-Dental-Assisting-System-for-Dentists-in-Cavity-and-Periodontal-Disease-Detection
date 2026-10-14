# 2026-10-15 — Are all six stages publishable? A second council, checked against published practice

**Session goal:** the user asked to push the 14 Oct fixes, then whether all six stages are good
to publish — check every metric and test result, and where fixes are needed, see what published
papers do (`/council`); then said to apply the verified fixes, assert new numbers, re-run every
check, log it, and not commit.

Same worktree as `2026-10-14f` and `2026-10-14g`. The session crossed midnight and paused once on a
usage limit; nothing had been changed when it paused. Record in `RESULTS_LOG` 2026-10-15.

## What was done

- **Pushed** `af5cc44` and `f1007ca` to `origin/main` (fast-forward, no deletions).
- **Checks before any change:** pytest 204, invariants 12 (two in part — crop corpora not built
  here), 207 claims; every stage's headline re-read from `stage1_switch_results.json` and the
  Stage-4 summaries.
- **Literature:** Firecrawl had no tools in this session, so WebSearch was the fallback (the
  user's routing rule). The facts used were confirmed at source: Krois 2021 through Crossref and
  the Europe PMC abstract; Schwendicke 2021 through Crossref; Bizjak & Robič 2024 from the PDF's
  text; UFBA-425's source (Budagam et al. 2024) through the arXiv API.
- **Council:** brief in the session scratchpad; three `Plan` seats (dental-AI referee, Opus;
  evaluation statistician, Sonnet; red-team auditor, Opus), read-only, web limited to the listed
  URLs. All three reported. The chair checked each finding used: the main.tex lines, the absence
  of any numbering-calibration artefact, the 0.30 threshold's home in the coverage JSON and its
  24 Aug origin, 25,000 / 731, the calibration file's 2,000 resamples over 34 images, the 148
  images behind Table V, the IoU 0.30 matcher, and the random-effects arithmetic (reproduced).
- **Applied:** 24 corrections to `paper/main.tex`; three entries in `paper/source.bib`;
  `scripts/eval/ningxia_random_effects.py` and its artefact; seven new claims and two assertions
  in `scripts/verify_paper_numbers.py`; `DEFAULT_SHA256` keyed by resolved path and a test that
  every default has a pin.
- **Checks after:** pytest 205; invariants 12; 214 claims, no drift; tectonic 16 pages, 0 errors,
  0 undefined references or citations; the four citations render; `paper/main.pdf` replaced.
- **Records:** `RESULTS_LOG` 2026-10-15; `PAPER_MATERIAL.md` §8.42 and two §9 items;
  `model_metrics.md` (Ningxia random effects; test count); `SUBMISSION_TODO.md` note;
  `transfer.md` top line, §1 counts, §3, §8 count; `README.md` and `tests/README.md` counts.

## Decisions made

- **The registered Ningxia figure stays; the random-effects one is added beside it, labelled post
  hoc.** Replacing the registered analysis after the fact would be the selection this paper
  criticises. The new sentence states what each pooling answers.
- **Two decimals for the random-effects figures**, matching the per-hospital figures and the
  checker's formatting; the artefact keeps p to four places.
- **The 34-fold ratio is asserted against the text's own areas**: no artefact records the
  731 px median, and inventing one now would be a new measurement.
- **The Schwendicke sentence says the checklist covers reference-test construction**, not that it
  asks for inter-rater agreement specifically — that much was verified; the item text was not.
- **UFBA-425 cited to the arXiv preprint that introduces it**: no DOI exists, as the bib note says.
- **Scope held to the approved list.** Abstention per cohort, Tufts in the patient-level
  limitation, "no GPU present", "fuse on the FDI key", false positives per image and lesion-level
  AP were found but not approved; they are recorded as the authors' choice.

## Open questions

- Whether the six-page cut reports the random-effects interval or only "three of four hospitals".
- Whether to add abstention per cohort (one seat's count: 3.9 / 14.4 / 26.3% declined on DENTEX /
  Tufts / UFBA) — it would strengthen the "declining" axis honestly but adds a measurement.
- Whether "every tooth in the mouth" (Tufts 3,760) should read "every permanent tooth"; not checked.

## Next steps

1. The user commits (proposed at the end of the session) and decides on a push; the main checkout
   then pulls.
2. The mentor meeting (O1), then the six-page cut, carrying 14 Oct's and 15 Oct's corrections.
3. Optional items above, if the authors want them, each logged.
