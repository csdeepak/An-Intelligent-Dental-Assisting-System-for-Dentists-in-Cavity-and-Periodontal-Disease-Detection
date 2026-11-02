# Open issues: mentor draft, ten-page version of 28 Oct 2026

The 30 Sep version of this list (draft v002, review round v001_1) is in git at `3cc15fe`; the
seven-page version of 28 Oct at `5f35936`. This one is for the ten-page draft: current pipeline,
numbers as verified in `paper/main.tex`, a theory section checked against saved data, real-radiograph
figures (`scripts/figures/make_opg_figures.py`) and data figures
(`scripts/figures/make_draft_figures.py`); `RESULTS_LOG` 2026-10-28 and 2026-10-28b.

## Must resolve before any submission
- [LICENCE] Figures 1, 4 and 7 show DENTEX radiographs (CC BY-NC-SA 4.0). Share-alike must be
  reconciled with the venue's copyright form, or the figures replaced (`PAPER_MATERIAL.md` §8.19).
- [ASK AUTHOR] Author and affiliation block; acknowledgment and AI-use wording.
- [ASK AUTHOR] Public anchor for the lesion-detector pre-registration (commit `ef3f453` of a
  private repository).
- [ASK AUTHOR] VLM decoding settings (sampling, maximum tokens) are not recorded with the runs.
- [VENUE] Ten pages. The planned venue (IEEE CONECCT 2027, `transfer.md` §5) takes six; either this
  version targets a different venue or a cut is chosen (the planned caries-only cut drops Stage 4 and
  most of RQ3).
- [CITATION] "In the 49 task-relevant papers of our own survey we noticed none that reports an
  image-blind baseline" is an observation from the authors' reading, worded as such; it is not a
  systematic count.
- [DATA] Ningxia: Li et al. 2024 describe three hospitals; the release's four test splits (test2
  from the training centre, three cross-centre) are what the draft calls "four sites". Confirm with
  the dataset authors if a reviewer asks which hospital each split comes from.

## Closed 2 Nov 2026 (citation audit, `RESULTS_LOG` 2026-11-02)
- Every reference resolved on Crossref, OpenAlex, Semantic Scholar and arXiv (34 of 36; Bizjak and
  YOLO11 confirmed at the publisher), no retraction notices, and each cited claim checked against
  the cited work's abstract or full text. Wrong Li et al. title (from the local registry) fixed by
  citing everything from `paper/source.bib`; Cao et al.'s unverifiable 61.83 dropped; Zancan's
  0.9988 now carries its F1; 14 verified citations added (methods, related fields, checklists).
- The printed reference list follows IEEE style: abbreviated venues, at most six authors then
  et al., no URLs except for software, no curation notes.

## Closed since the seven-page version
- Theory: the closed-form F1 of the image-blind constant and its selection rule, the identity chain,
  lesion agreement as prior mass, and the shortcut signature, each set against a saved measurement
  (Table 7 of the draft lists them, including the one prediction not supported).
- Architecture figure, analysis-population/exposure table, paired-difference forest plot with the
  random-effects prediction interval, and the numbering / selective-prediction / reliability figure,
  taken from the structure of the two outside drafts (`ieee-draft-a/b.pdf`) with current numbers.
- One sign convention: system minus comparator throughout.

## Accepted risks
- Training-curve values are on validation splits used for checkpoint selection (optimistic).
- The three qualitative images are chosen by a rule stated in the text; they illustrate, and do not
  replace, the cohort statistics.
- The theory treats tooth codes independently and is checked on one corpus's prior (78 and 164
  images); the shortcut test rests on 34 radiographs.
- Related work is cited at abstract level; the full bibliography stays in `main.tex`.
