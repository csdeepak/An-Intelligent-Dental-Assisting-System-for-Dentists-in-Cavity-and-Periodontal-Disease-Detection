# 2026-08-28 — Manuscript rebuilt from the artefacts

## Session goal

Audit the whole repository against `paper/main.tex`, then rebuild the manuscript so every
claim traces to evidence and a non-specialist reader can follow the argument.

## What was done

**Audit first, writing second — the request explicitly forbade starting with prose.**

1. **Evidence pass over the repository.** Read every JSON under `outputs/`, every
   `models/*/run_summary.txt`, `PAPER_MATERIAL.md`, `model_metrics.md`, `RESULTS_LOG.md`,
   the figure-generation scripts, the evaluation scripts and their docstrings. Recomputed
   from source rather than trusting the docs where it was cheap to do so: the DENTEX
   ground-truth counts, the greedy constant fit, the survey CSV, and the parameter counts.
2. **Wrote `docs/paper/REBUILD_AUDIT.md`** — research story, 20-item problem audit,
   numerical audit (verified / wrong / unsupported / missing), section storyboard, citation
   audit, five title options with a recommendation.
3. **Rewrote `paper/main.tex` end to end.** New title, new abstract, new introduction
   built from the clinical problem outward, a Data section with a corpus table, an
   evaluation-protocol section that defines every metric in words before symbols, a
   statistical-analysis subsection, results with interpretation stripped out, and a
   12-item limitations list where each item says what it prevents us concluding.
4. **Corrected five defects** (details in `RESULTS_LOG.md` 2026-08-28), fixed the two
   figures that carried them, completed five bibliography entries, and added
   `scripts/verify_paper_numbers.py`.
5. **Propagated the parameter correction** through 11 places in 5 files.
   `RESULTS_LOG.md` was deliberately not edited — it is append-only; the new entry records
   the correction instead.

Archived: `_repo_archive/paper_draft_v1_44percent_title/` (ARCHIVE_MANIFEST item 7).

## Decisions made

**The title had to change.** "What Does 44 % Mean?" anchors on 212/479 = 44.3 %, the
*pipeline's own* lesion-localisation agreement. It is one row of one table, never written
as "44 %" anywhere in the body, and it is not the paper's finding — the finding is the
comparison (0.488 vs 0.443; 0.320 vs 0.294). A title that makes the reader reverse-engineer
a number, and then rewards them with the wrong number, is worse than a plain one. Chose
*"What a Tooth-Level Score Cannot Tell You: Constant Baselines, External Validation and
Domain Shift in Automated Panoramic Dental Screening"* because it names the contribution
rather than a result — which matters here, since **the result does not replicate
externally** and a title asserting it would overclaim.

**Periodontal bone loss stays in, introduced properly, labelled secondary.** The old draft
had it appear mid-Methods with no clinical introduction and no place in the title, abstract
or contributions — a reviewer would ask why a second disease had materialised. The options
were to cut it or to commit to it. Committed: it is a real branch with a real, well-attributed
negative result (§8.13's falsified shared-cause hypothesis is genuinely good work), and the
paper is *about* the gap between in-domain scores and evidence — a branch scoring 0.923 in
domain and 1.4–5.6 % outside it is the argument, not a distraction from it. The primary
evaluation stays caries-only, because caries is the task annotated on all five institutions.

**Reported the bone-loss 0.923 with both caveats rather than quietly.** It is the maximum
of a noisy 32-epoch selection curve over 59 validation positives, and it is *not currently
reproducible* — half the validation crops used a jitter RNG whose offsets were never saved,
and the source radiographs are on the other machine; the rebuild attempt was rejected by
its own geometry check (`RESULTS_LOG` 2026-08-27u). Stating both makes the collapse less
surprising and the paper more defensible, and hiding them would have been the exact
practice the paper argues against.

**Kept the isotonic-calibration result but reframed it as a deployment choice with a
price.** The draft claimed isotonic left "every verdict byte-identical". It does not — the
JSON records 155 of 863 verdicts flipping at threshold 0.5 and AP falling 0.550 → 0.500.
What is true is that *we* apply it to the reported confidence only. That is a defensible
decision (it keeps every published number as measured) and it had to be stated as one.

**Declared the internal and external lesion-agreement figures non-comparable to each
other.** They use different matchers, forced by a ~200x lesion-to-tooth area difference.
`PAPER_MATERIAL.md` §8.12 knew this; the manuscript did not say it, and a reader would
naturally have read 0.443 → 0.408 as a degradation figure. It is not one.

**Built a number-checker rather than trusting a careful read.** Two of the five defects
were numbers that had drifted from their artefacts while reading as plausible.
`scripts/verify_paper_numbers.py` now asserts 82 of them against the JSON at any time.

## Open questions

- **Venue length.** The rebuilt manuscript is 12 pages; ISBI allows 4. The brief asked for
  a complete, self-explaining document and that is what exists. The cut is a separate,
  venue-specific task and should not be done by re-compressing the prose that was just
  written to be clear — §III–§V and the 12-item limitations list are where the compression
  lives, and some of it may belong in supplementary material.
- **test1 remains undiagnosed** — the pipeline's worst external site (0.288) and the
  constant's best (0.446). Reported unexplained. Nobody has looked at those 134 images.
- **Author list and affiliations are still `Unknown`.** Blocking for submission and not an
  engineering task.
- The four compliance items in `PAPER_MATERIAL.md` §8.19 are untouched by this session and
  still block submission.

## Next steps

1. Produce the venue-length cut of `main.tex` against a chosen target (ISBI 4 pages, or a
   journal with room for the full version). Decide venue first — the cut differs.
2. Fill in authors and affiliations.
3. Work the §8.19 compliance checklist; it is entirely account-owner actions.
4. Optional, cheap: fix `c1_constant_baseline.py:78`'s stale "86" docstring and the
   `kong2024integrating` journal/DOI mismatch in `source.bib`.
5. Optional, not cheap: diagnose test1.
