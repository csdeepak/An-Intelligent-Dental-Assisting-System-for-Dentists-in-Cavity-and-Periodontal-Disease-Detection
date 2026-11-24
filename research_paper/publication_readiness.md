# Publication readiness

## Verdict

**Not submittable today; submittable after author inputs and a venue choice, without new
experiments.** The revised manuscript states only what the saved artefacts support, and it passes every executable RCE gate up to the pre-review integrity gate (GI passed on its third VERIFIER round). Every number is
traced, every citation is live-verified, and the disclosures the reviewers asked for are in the
text. What remains is in the authors' hands: names, statements, licences and the venue. Acceptance
cannot be predicted. The three reviewer perspectives all asked for major revision of v1, and v2
answers them in text and with one new analysis. Whether a human referee would accept v2 is unknown.

## What the paper can claim (and what it cannot)

| Can claim | Cannot claim |
|---|---|
| A tooth-level caries F1 has an image-blind floor; the F1-optimal constant follows from a known thresholding result and here is the eight molars | That the system detects periodontal disease, or periodontal bone loss |
| A crop-classifier pipeline was level with that floor on development data (once the constant cannot name absent teeth) and on four external sites, and below it on CariesXrays | Clinical usefulness, readiness, regulatory status, or any dentist evaluation |
| A lesion detector led the floor on pooled external sites with fewer flags; not shown for an unseen site; those sites informed its adoption | State-of-the-art caries or numbering performance |
| A per-stage evidence audit with its negative results | A lead that holds at every site, or that is free of selection |

## Blockers (all in `open_issues.md`)

| Blocker | Owner | Kind |
|---|---|---|
| Author block, CPU model, availability statement, ethics wording, acknowledgment | authors | input |
| Public anchor for the adoption-rule commit (repository is private) | authors | release decision |
| DENTEX share-alike vs the venue's copyright form (Figs. 1, 4, 7) | authors | licence |
| Kaggle FDI set licence (in the default detector's training data) | authors | licence; the remedy is a detector trained without it |
| Length: 14 pp in IEEE conference format | authors + mentor | venue |

## Venue fit (constraints from `transfer.md` §5 and the department guidelines of 10 Oct 2026)

| Route | Fit | Needs |
|---|---|---|
| Indian Scopus/WoS conference, 10th+ edition (e.g., IEEE CONECCT 2027, 13th edition, deadline about 15 Dec 2026, dates to confirm when its call opens) | Satisfies both the grade table and the guidelines | A six-page caries-only cut: Sections III–VI-D, Tables 1, 5, 7, Fig. 6; Stage 4 one sentence; indexing of that edition verified |
| Journal extended version (e.g., IEEE JBHI: 14-page cap, free to 8 pp) | Grade S if accepted; check with the mentor whether a journal still counts under the new guidelines | Journal class and an 8-page cut, or paid pages |
| Conference outside India | Allowed only with University approval *before* submitting or paying | Approval |

## Reporting checklists to complete before submission

CLAIM 2024 (medical imaging AI), TRIPOD+AI (prediction models), and the dental AI checklist of
Schwendicke et al. 2021 are cited in the paper. Most items are already answered in the text, but
none of the checklists has been filled item by item. Doing so is the next writing task.

## Risk register for a referee

1. **Selection on the external cohort.** Disclosed, but a referee may still discount Ningxia. The
   mitigation is a new external cohort that no decision has seen.
2. **Development cohort in-domain.** DENTEX trained the current detector. Disclosed.
3. **Single runs and cross-machine differences.** Disclosed: 0.294 vs 0.300, and 12 of 164 images
   differ between the Windows and macOS runs.
4. **Theory novelty.** Now framed as an application of Lipton et al. 2014. A referee may still call
   it modest; the measured multi-cohort finding carries the paper.
5. **Title vs the capstone's stated aim.** The paper cannot be called a periodontal detection paper.
