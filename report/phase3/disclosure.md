# Disclosure: how this report was prepared

The Phase 3 report (PW26_MHR_06, UE23CS441A) was drafted in LaTeX with an AI assistant, Claude, in
Claude Code, between 2 and 6 November 2026, at the project team's direction. The team set the
brief:

- follow the college guidelines and templates;
- impose no page limit;
- carry over 60–70% of the Phase 2 report, keeping all its images;
- reproduce the Phase 2 fonts and theme.

## What the assistant did

- **Wrote the text.** It wrote the chapters and appendices from the project's own records: the
  ten-page paper draft, `transfer.md`, `docs/results/` and the `models/*/run_summary.txt` files.
  It also used the saved `outputs/**` result files and the Phase 2 report.
- **Made the figures.** It drew the diagrams in TikZ and generated the plots from the saved result
  files (`tools/make_plots.py`). The three web-demo screenshots come from running the project's own
  app on a DENTEX test image.
- **Checked the Phase 2 literature survey against each paper's abstract.** Numbers that could not be
  confirmed were removed. Where the Phase 2 report was wrong, the entry says so.
- **Ran the Research Communication Engine checks:**
  - schema and claim validation (G1);
  - the draft lint (G3);
  - a strict trace of every number in the report to a saved file (G3);
  - the citation gate with verbatim support quotes (GL);
  - a check that the abstract keeps what its claims say.

  The results and the commands to re-run them are in `PLAN.md`. The reports are in
  `.rcs/audits/gates/`, which is kept local, not in git, under the repository's rule for RCE trails.

## What was not checked

- **No independent review.** The isolated review panel (G4) and integrity verifier (GI) were not run.
- **No author confirmation yet.** The 70 claims in `.rcs/claims/claim_evidence_map.json` all await an
  author's confirmation.
- **Some quotes are titles only.** Five sources have no retrievable abstract, so their support quote is
  the title. They are listed in `open_issues.md`.
- **Nothing was re-run.** The report presents the project's existing results. It introduces no new
  experiment and no new number. Every number in it traces to a project file (G3 numbers report).

## Data and image rights

Rights for the Tufts radiograph crops, the figures reproduced from published papers and the DENTEX
images are set out in `open_issues.md` (items 4 to 6). They need attention before any public release.
