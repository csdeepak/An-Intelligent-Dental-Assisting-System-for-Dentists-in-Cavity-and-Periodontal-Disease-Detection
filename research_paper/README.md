# research_paper/ — evidence-locked revision of the dental OPG paper (23 Nov 2026)

**Read first:** [`open_issues.md`](open_issues.md) — everything the authors must still decide or supply.
**The paper:** [`final_research_paper.pdf`](final_research_paper.pdf) (14 pages, IEEEtran; v2, after review round 1) ·
source [`paper.md`](paper.md) (tagged) → [`paper.tex`](paper.tex) + [`references.bib`](references.bib).

`paper/` was not modified. This directory is a new, separate revision built from the ten-page draft
reviewed on 2 Nov 2026 (`paper/paper.md`, review round 1 in `paper/ieee/review/`).

## Deliverables

| # | File | What it is |
|---|---|---|
| 1 | [`repository_audit.md`](repository_audit.md) | architecture from code, default checkpoints, datasets, experiments done/missing, documentation conflicts, post-11-Oct changes, risks |
| 2 | [`evidence_registry.md`](evidence_registry.md) | evidence items, claim-to-evidence map, limitations, negative results, conflicting-results register, live-verified source registry (generated from `.rcs/`) |
| 3 | [`literature_review.md`](literature_review.md) | search protocol as actually run, comparison table, synthesis, the genuine gap |
| 4 | [`research_gap_and_novelty.md`](research_gap_and_novelty.md) | each candidate contribution tested; verified / reused / engineering / future |
| 5 | [`experimental_verification.md`](experimental_verification.md) | re-run checks, leakage/selection audit, the detector-change question, proposed experiments |
| 6 | [`clinical_validity_assessment.md`](clinical_validity_assessment.md) | radiographic finding vs diagnosis; why no periodontal claim; false-negative implications |
| 7 | [`paper.tex`](paper.tex) | generated from `paper.md` by `tools/build_paper.py` |
| 8 | [`references.bib`](references.bib) | 52 entries: `paper/source.bib` (Crossref-checked 2 Nov) + `references_extra.bib` (Crossref-generated 23 Nov) |
| 9 | [`figures/`](figures/) | 8 figures, each produced by a repo script that asserts its values; [`figures/README.md`](figures/README.md) maps figure → data |
| 10 | [`tables/`](tables/) | the paper's 8 tables as CSV and Markdown |
| 11 | [`reviewer_report.md`](reviewer_report.md) | three independent reviewer perspectives and the disposition of every required correction |
| 12 | [`integrity_check_report.md`](integrity_check_report.md) | every RCE gate run, with tool output |
| 13 | [`publication_readiness.md`](publication_readiness.md) | verdict, blockers, venue fit |
| 14 | [`final_research_paper.pdf`](final_research_paper.pdf) | compiled with MiKTeX pdfLaTeX + BibTeX |
| 15 | this file | |

Also: [`WORKFLOW.md`](WORKFLOW.md) (the session's flowchart), [`tooling_decisions.md`](tooling_decisions.md)
(RCE version; PaperOrchestra evaluated and not used, with reasons), [`disclosure.md`](disclosure.md)
(AI-use statement draft), `review/` (the reviewers' full reports), `literature/` (saved abstracts),
`audit_runs/` (raw check outputs), `.rcs/` (RCE audit trail; gate reports in `.rcs/audits/gates/`).

## Rebuild

From the repo root, with `C:\venvs\dental312\Scripts\python.exe` and MiKTeX on PATH:

```
python research_paper/tools/build_rcs.py          # evidence + claim maps (fails if a value is not in its file)
python research_paper/tools/build_paper.py        # paper.md -> paper.tex -> final_research_paper.pdf
python research_paper/tools/trace_numbers_rp.py . # every number vs saved artefacts
python research_paper/tools/render_registry.py    # evidence_registry.md
python research_paper/tools/export_tables.py      # tables/
```

`build_registry.py` rewrites the source registry and drops the live verification; run RCE's
`verify_citations.py research_paper/.rcs --online` after it. RCE gates are run with the skill at
`C:\Users\csdee\PESU\research_skill\research_writing_skill\tools\` (commit `3e4411f`), always with
`--project-root .` from the repo root.
