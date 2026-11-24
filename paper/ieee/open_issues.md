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
- [ASK AUTHOR] CPU model for the 1.70 s per image runtime (Section IV, review item 20).
- [VENUE] Ten pages. The planned venue (IEEE CONECCT 2027, `transfer.md` §5) takes six; either this
  version targets a different venue or a cut is chosen (the planned caries-only cut drops Stage 4 and
  most of RQ3).
- [CITATION] "In the 49 task-relevant papers of our own survey we noticed none that reports an
  image-blind baseline" is an observation from the authors' reading, worded as such; it is not a
  systematic count.
- [DATA] Ningxia: Li et al. 2024 describe three hospitals; the release's four test splits (test2
  from the training centre, three cross-centre) are what the draft calls "four sites". Confirm with
  the dataset authors if a reviewer asks which hospital each split comes from.

## Review round 1, 2 Nov 2026 (`paper/ieee/review/`, `RESULTS_LOG` 2026-11-02b)
- Integrity gate (Stage 2.5): passed with notes after fixing Table 7's post-hoc framing and the
  Table 3 Stage-4 count. Panel decision: **Major revision**; one validated Devil's Advocate
  CRITICAL (the RQ2 sentence). The 21-item roadmap in `2026-11-02_panel_round1.md` is the open
  work list for this draft.
- Revision, 2 Nov (`2026-11-02_response_round1.md`, `RESULTS_LOG` 2026-11-02c): the 13 text items
  are applied and the CRITICAL is closed in the text; 10 done, 5 partial, 6 planned or open.
  Analyses of 2 Nov (`RESULTS_LOG` 2026-11-02d): HKSJ (4), DENTEX perceptual-hash check (6),
  constant stability (15) and the image-blind operating curve with matched volume (16) are done
  and in the draft. Open from the roadmap: Ningxia per-type comparison (1; needs the raw images,
  `outputs/review_round1/README.md`); learned position-only floor, content ablation and site probe
  (10); availability statement (11); a supplement for Stage 4 and the VLMs (2); a radiographic
  definition of deep caries (19); a boxed checklist (21).
- Figures 4 and 7 are at 0.80 and 0.78 text width. Their panel titles read in print, but the
  confidence numbers and FDI labels inside the boxes do not. Enlarged insets would fix it.

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
