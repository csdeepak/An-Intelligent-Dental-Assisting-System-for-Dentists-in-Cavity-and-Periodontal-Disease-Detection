# 2026-10-14c — The 15-page manuscript's Stage 4 rewritten, Fig. 5 replaced

**Session goal:** after the implementation was committed (`73d91e9`), the user asked to continue
and chose, from four options, "fix Stage 4 in `main.tex` + Fig. 5" now rather than with the
six-page cut (D2's default that morning).

Run on the macOS clone, evening. No measurement; numbers in `RESULTS_LOG` 2026-10-14b.

## What was done

- **Text.** Every Stage-4 statement in `paper/main.tex` rewritten to `SUBMISSION_TODO.md` §2
  item 3 and §1a rows o–r: abstract, keywords, introduction, §System and `tab:stages`, §Data and
  `tab:data`, §Evaluation protocol, a new §Results subsection `sec:stage4`, §Discussion,
  §Limitations, §Conclusion, §Reproducibility. Twenty-two anchored edits and three regex
  replacements; the file stays CRLF.
- **Fig. 5.** New `scripts/figures/make_stage4a_paper_figure.py` → `paper/fig_stage4a.png`: dot
  and interval for sensitivity and specificity of the three runs and the first model; one
  column wide; asserts 50/30/20 of 182 and 6 of 175 before drawing. Tick labels collided on the
  first render and were stacked.
- **Checker.** The Stage-4 block of `scripts/verify_paper_numbers.py` rebuilt from the confusion
  counts: 12 claims. Two older claims (+34.40, +19.35) failed once their paragraph left and were
  removed with a comment. 188 claims, no drift.
- **Build.** Tectonic: 15 pages, 0 undefined references, the one 4.47 pt overfull box that was
  there before. Pages 1 and 11 rendered and read.
- **Housekeeping.** `!paper/fig_*.png` in `.gitignore` (the new figure was silently ignored;
  the older paper figures had been force-added). The claim count updated in README ×4 and
  `transfer.md` §1. `RESULTS_LOG` 2026-10-14b; `PAPER_MATERIAL.md` §9, three items ticked;
  `SUBMISSION_TODO.md` §1a note; `transfer.md` top note and §3.

## Decisions made

- **A new figure script, not a rewrite of the old one.** `make_boneloss_paper_figure.py` and
  `fig_boneloss.png` stay unchanged, so the figure the 11 Oct manuscript carried can still be
  regenerated from HEAD.
- **The first model's Ningxia and DENTEX figures left the paper, not the record.** They describe a
  model the pipeline no longer ships, and row p's draft gives the flag "no external figure". The
  history the paper needs — 0.923 and 83% came from a leaky split; 3.4% held out — stays in one
  sentence.
- **The affected-tooth-sensitivity paragraph in §Evaluation protocol was removed** because it
  served only those figures.
- **The abstract's first sentence still names periodontal bone loss** as clinical background, and
  the introduction still describes the disease. Neither claims the system detects it; the next
  abstract sentence says what Stage 4 flags.
- **Out of scope and left alone:** row i (CariesXrays "kept away from", `main.tex` line 595),
  `paper/paper.txt`.

## Open questions

- The mentor has seen none of the changes since 11 Oct, now including the paper's Stage-4 text.
- Whether the six-page cut keeps Fig. 5 or states Stage 4 in one paragraph without a figure.

## Next steps

1. The user commits: `docs:` with `paper/main.tex`, `paper/main.pdf`, `paper/fig_stage4a.png`,
   `docs/results/figures/paper/07_stage4a_heldout.png`, `scripts/figures/make_stage4a_paper_figure.py`,
   `scripts/verify_paper_numbers.py`, `.gitignore`, `README.md`, `transfer.md`,
   `docs/results/RESULTS_LOG.md`, `docs/results/PAPER_MATERIAL.md`, `docs/paper/SUBMISSION_TODO.md`
   and this file.
2. Tell the mentor and the repo owner.
3. The six-page cut, from the corrected long text; `SUBMISSION_TODO.md` §1a row i with it.
