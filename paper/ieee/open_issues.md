# Open issues: mentor draft, rebuilt 28 Oct 2026

The 30 Sep version of this list (draft v002, review round v001_1) is in git at `3cc15fe`. This one
replaces it for the rebuilt draft: 7 pages, current pipeline, numbers as verified in `paper/main.tex`,
real-radiograph figures from `scripts/figures/make_opg_figures.py` (`RESULTS_LOG` 2026-10-28).

## Must resolve before any submission
- [LICENCE] Figures 1, 2 and 5 show DENTEX radiographs (CC BY-NC-SA 4.0). Share-alike must be
  reconciled with the venue's copyright form, or the figures replaced (`PAPER_MATERIAL.md` §8.19).
- [ASK AUTHOR] Author and affiliation block; acknowledgment and AI-use wording.
- [ASK AUTHOR] Public anchor for the lesion-detector pre-registration (commit `ef3f453` of a
  private repository).
- [ASK AUTHOR] VLM decoding settings (sampling, maximum tokens) are not recorded with the runs.
- [VENUE] The planned venue (IEEE CONECCT 2027, `transfer.md` §5) needs six pages; this draft is seven
  and still carries Stage 4 and the numbering results, which the planned caries-only cut drops.
- [CITATION] "In the 49 task-relevant papers of our own survey we noticed none that reports an
  image-blind baseline" is an observation from the authors' reading, worded as such; it is not a
  systematic count.

## Closed since 30 Sep
- Paired constant-minus-pipeline intervals: the draft now quotes the post-switch intervals that
  `main.tex` verifies (`outputs/caries_intervals/`, `outputs/stage1_switch/`).
- Stage 4 is described by its label (an abnormality-proximity flag), held out, not as a periodontal
  detector; the 0.923 is quoted only as the split artefact it was.
- "No evident results": every stage is now shown on a real radiograph, with training curves and
  rule-chosen successes and failures against the expert.

## Accepted risks
- Training-curve values are on validation splits used for checkpoint selection (optimistic).
- The three qualitative images are chosen by a rule stated in the text; they illustrate, and do not
  replace, the cohort statistics.
- Related work is cited at abstract level; the full bibliography stays in `main.tex`.
