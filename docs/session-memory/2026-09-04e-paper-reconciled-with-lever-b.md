# 2026-09-04e — Reconciling `paper/main.tex` with the Lever B adoption

## Session goal

Fold the adopted lesion-detector Stage 3a into the manuscript, which still described only the
per-crop caries gate.

## What was done

Continuation of `2026-09-04d-merge-lever-b.md`. No model was trained and no evaluation was
re-run; every number below already existed in a saved artefact.

**Manuscript (`paper/main.tex`).**

- Table I rewritten to report **both** Stage-3a implementations and four totals: 97.65 M /
  75.29 M for the adopted default, 83.52 M / 61.16 M for the retained gate variant.
- §System, new `\subsection{Stage 3a: two formulations of the same clinical question}`
  (`sec:lesiondet`) — the two tasks, the pooled training mixture, the frozen 0.25 confidence,
  and what the reformulation costs in external evidence.
- §System, Stage 3/4 paragraph rewritten: it described both branches as gate cascades, which is
  now true only of Stage 4 and of the retained variant.
- §Results, new `\subsection{Changing the task, not the architecture}` (`sec:leverb`) — the
  three-cohort table, the not-a-volume-effect check, and the B-single transfer collapse.
- §Discussion, Main finding and "Why the floor is high" reframed (see Decisions).
- Abstract: one factual sentence added.

**Verification infrastructure.**

- `scripts/count_model_params.py` (new) → `outputs/param_counts/param_counts.json`.
- `scripts/verify_paper_numbers.py`: **90 → 117** asserted claims, all passing. New coverage of
  every Lever B figure, all four parameter totals, and two structural assertions that are not
  string checks — that `sec6_rule_met` is still true, and that the detector still flags no more
  teeth than the constant on each cohort where the prose says it flags fewer.
- `scripts/eval/cariesxrays_external.py`: leakage guard (see Defect 3).

**Documentation.** `models/16_lever_b_pooled/run_summary.txt` (still said "ABLATION ARM, not
adopted"); `docs/results/model_metrics.md` (parameter table re-counted, DENTEX row corrected);
`docs/results/PAPER_MATERIAL.md` (§9 blocking item ticked, DENTEX row corrected);
`RESULTS_LOG.md` entry **2026-09-04i**.

**Three defects found, all predating this session.** Full detail in RESULTS_LOG 2026-09-04i.

1. **A headline number was mis-rounded.** DENTEX constant lesion agreement is 234/479 =
   0.488518 → **0.489**; the paper carried **0.488** in the abstract, Table II and Table IV.
   The verifier had been formatting the artefact's *already 4-dp-rounded* field with `:.3f`,
   so it was validating the manuscript against a number that was itself wrong. Audited all
   fifteen 3-dp agreement figures; this is the only one affected.
2. **The parameter table mixed two counting conventions** (YOLO rows excluded batch-norm
   buffers, ResNet18 rows included them), and the verifier's three parameter claims were
   hardcoded literals labelled `"torch.load over models/*/"`, so nothing had ever checked them.
3. **A live leakage hazard.** `cariesxrays_external.py --decision lesion-detector` without
   `--manifest-split val` scores the adopted detector on ~4,800 of its own training images.
   `lesion-detector` is now the default, so the obvious invocation was the dangerous one.

Checks after all edits: `verify_paper_numbers.py` 117/117, `audit_citations.py` 26/26 keys
resolved, `pytest` 159/159, no undefined or duplicate LaTeX labels.

## Decisions made

- **The Lever B result is additive to the paper's thesis, not a contradiction of it.** §Main
  finding already said *"no amount of **architectural** work raises a ceiling imposed by the
  pairing of task and metric."* Lever B changed the **task**, not the architecture. So the
  paper's claim is *confirmed* — five repairs to the classifier failed, and the ceiling moved
  only when the pairing did. I wrote the reframing that way rather than as a retraction, and
  added a sentence to "Why the floor is high" making the test explicit.
- **Did not touch the title or re-centre the thesis.** That is Deepak's call. The one place it
  bites is the abstract's closing "four things a constant cannot do" — localising the finding is
  arguably a fifth, now demonstrated, but adding it changes the paper's prescription. Flagged in
  `PAPER_MATERIAL.md` §9 and RESULTS_LOG, not done.
- **Stated the cost of the reformulation in the paper rather than only in the log.** DENTEX and
  CariesXrays were external test data for the gate and are development data for the detector.
  Ningxia is the only cohort external to both, so the detector has one external cohort where the
  gate had two. Table V footnotes every row `d` or `e` accordingly. Without this the paper would
  read as though the caries result strengthened on three external cohorts, which is false.
- **Adopted "learnable parameters only" as the single counting rule** and re-counted everything,
  rather than reproducing the old mixed convention to keep the printed digits stable. The
  totals moved 0.04 M. A table nobody can reproduce from a stated rule is the defect; the digit
  is not.
- **Corrected 0.488 → 0.489 in `main.tex`, `model_metrics.md` and `PAPER_MATERIAL.md` only.**
  `RESULTS_LOG` entries are append-only history (rule 1) and were left alone with a new entry
  linking back. `docs/paper/{manuscript.md,draft_spine.md,REBUILD_AUDIT.md}` are superseded
  drafts of the 28 Aug rebuild and were left alone deliberately — editing another workstream's
  historical artefacts to chase one digit is how the propagation problem started.
- **Made the leakage guard a hard failure, not a warning.** A warning in a script whose output
  is a JSON file gets scrolled past; the number survives.

## Open questions

- Does the abstract's "four things" list become five? Thesis-level, deliberately not decided.
- The C4 abstention curves are computed from the *gate's* confidence distribution. Under the new
  default there is no calibrated probability to abstain on — `gate_confidence` is a raw
  detection score, flagged as such. Are those curves re-run against the detector, or explicitly
  scoped in the paper to `--caries-method gate`? Currently neither: they are scoped by
  implication only.
- `docs/paper/manuscript.md` and `draft_spine.md` still describe a gate-only pipeline and carry
  0.488. Retire them, or mark them superseded? Leaving them is a trap for the next reader.
- Is the DENTEX tie worth a second pooled arm with a different mixture ratio, or is the honest
  answer to leave DENTEX as a reported tie? Not investigated.

## Next steps

1. Deepak's call on the title / thesis / "four things" list.
2. Decide the C4 abstention scoping — one sentence in the paper is enough if the answer is
   "gate variant only".
3. Docker rebuild (stale twice over: isotonic calibration wiring, now Stage 3a too).
4. Retire or mark-superseded `docs/paper/manuscript.md` and `draft_spine.md`.
5. Remaining pre-submission blockers are unchanged and mostly not mine: venue, authors and
   affiliations, the four compliance items including IRB and the two live data-exposure
   breaches, the Lever-2 CariesXrays row in Related Work, and the `source.bib` `url` sweep.
