# 2026-09-30 — RCE mentor draft of the paper (evidence-traced, two blind review rounds)

## Session goal

Produce an 8-page IEEE-conference **mentor draft** of the paper with the Research Communication Engine (RCE v0.4,
`C:/Users/csdee/PESU/research_skill/research_writing_skill`), every number traced to a saved artifact. Not for
submission; the author asked for a draft to iterate on with the mentor.

## What was done

- `.rcs/` created and git-ignored (`.gitignore`, uncommitted). Guardrail v0.3.
- **Evidence map**: 133 items (`.rcs/evidence/research_evidence.json`), built by script
  (`build_evidence.py`, scratchpad): values read from `outputs/*.json`, `models/*/run_summary.txt`, with sha256.
  17 missing-evidence items, 6 conflicts (all resolved by the author's chat instruction, recorded as Q-001..Q-013 answers).
- **Literature**: 15 sources verified via Crossref / arXiv APIs (`.rcs/corpus/source_registry.json`), abstract-level only.
- **Claim map**: 63 claims (1 BLOCKED, C004), 27 limitations (16 author-stated from `paper/main.tex`, 11 writer-derived).
- **Figures**: 4 empirical charts rendered by RCE `visuals.py` from `.rcs/plan/figure_data/*.csv`
  (`make_figure_data.py` extracts them from the artifacts); 1 hand-authored architecture SVG whose components trace to
  `scripts/run_inference.py` DEF_* anchors. No AI-generated images, no radiograph pixels.
- **Drafts**: v001 → blind review round 1 (38 findings, 4 dimensions at 2) → v002 → round 2 (no dimension ≤ 2) → v003 →
  line edit v004 (claim invariance 0 drift) → `paper/paper.md`.
- **LaTeX**: `paper/ieee/{main.tex,references.bib,figures/*.pdf,main.pdf}` via `paper/ieee/md_to_ieee.py`
  (faithful md→tex) and `paper/ieee/svg_to_pdf.sh` (headless Chrome; LaTeX crops with trim/clip). 8 pages, 0 undefined
  references, 0 overfull boxes. `paper/main.tex` untouched.
- Gate status from `tools/run_workflow.py`: G1, G3, G4 and V1–V4, V6 PASSED; G2 UNVERIFIED (no tool); V5 NOT_RUN
  (needs a human); G5 FAILED **only** because 7 author markers remain open (Q-014..Q-020).
- No commits made.

## Decisions made

- Spine A (evaluation finding + lesion-localisation replacement), matching the author's own `main.tex` thesis — author
  instruction Q-004.
- Soft-only numbers (constant fit-set F1 0.392, 72.0%/60.2% molar mechanism, 22.1%, Kaggle 80.3%, 168→165,
  "2 of 49") omitted: they have no saved artifact (Q-010).
- Paired constant-minus-pipeline CIs omitted rather than regenerated (Q-008) → non-separability is worded as point
  estimates only.
- All figures `figure*`: at column width the 12 px chart fonts would print at ~4.7 pt.

## Defects found in the existing manuscript (`paper/main.tex`) — not fixed there

1. States the CariesXrays molar mechanism (72.0%/60.2%) for "every lesion"; RESULTS_LOG says 300 images / 859 lesions,
   and no artifact is saved.
2. Statistical-analysis section says external periodontal sensitivity "carries no interval"; `bootstrap_ci.json` has one
   (and Results reports it). Also says the classifier branches have no per-item dumps, but the gate AP has a CI.
3. Claims all CIs use 10,000 resamples; RESULTS_LOG says the DENTEX constant-vs-pipeline CI used 5,000.
4. `model_metrics.md` rounds the CariesXrays constant match rate to 0.207; counts give 0.206 (1997/9672).
5. Tufts end-to-end artifact says 143 images, `model_metrics.md` says 149.
6. The reviewer's strongest substantive point: the lesion-detector gain is confounded with architecture and the added
   CariesXrays training data, and Ningxia is one of the three cohorts in the rule that chose between the two arms.

## Open questions

Q-014..Q-020 in `.rcs/checkpoints/pending.json`: author block; hash check of the lesion detector's DENTEX training
images vs the 164 scored images; VLM decoding settings; public pre-registration anchor; regenerate paired CIs; gap
citation; acknowledgment wording. Full list in `.rcs/open_issues.md` (copy in `paper/ieee/open_issues.md`).

## Next steps

1. Mentor reads `paper/ieee/main.pdf` + `open_issues.md`; decide title scope and venue/page limit.
2. Regenerate and save the paired constant-minus-pipeline CIs (Q-018) — the RQ1 claim needs them.
3. Answer Q-015/Q-016/Q-017; then fix the five `main.tex` defects above if `main.tex` stays the maintained manuscript.
4. Consider a position-only numbering/confidence control (reviewer finding; an experiment, needs pre-registration).
5. Next RCE round: new packet from the revised draft, `g4_check`, then G5 once markers close.
