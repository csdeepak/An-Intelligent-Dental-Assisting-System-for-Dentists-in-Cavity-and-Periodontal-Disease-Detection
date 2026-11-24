# 2026-10-27 — Repo revisit: a stale Windows clone, merged up to origin, and a resample-count audit

**Session goal:** one line — cold-start re-orientation after a long gap, fix the highest-value
defects, and land the result on `main` without pushing.

## What was done

1. **Revisit on the local `main` (later found stale).** Self-briefed from `transfer.md` and the
   30 Sep RCE note. Checks green on the right interpreter (Git Bash's `python` is msys64 3.11 with
   no numpy; `C:\venvs\dental312` and `py -3.13` both work). Verified the five defects the 30 Sep
   mentor draft flagged and fixed them on that base: the three constant-minus-pipeline intervals of
   the then-manuscript had never been saved and were regenerated at 10,000 / seed 42
   (`scripts/eval/constant_vs_pipeline_ci.py`); resample-count exceptions stated; a false "carries
   no interval"; molar-mechanism scope; 0.207 → 0.206; Tufts 143-of-149.
2. **Commit time: the base was 42 commits behind `origin/main`** (`508c963`, 15 Oct, the
   collaborator's 11–15 Oct work: Stage-1 detector switch and manuscript rebuild, caries-interval
   pre-registration, Stage-4a retrain adopted, Stage-4b retrain not eligible, two publishability
   councils). Stopped before committing the fixes and asked.
3. **On the user's instruction:**
   - `3cc15fe` `docs:` — the 30 Sep mentor draft, its LaTeX byproducts unstaged and gitignored.
   - `8e150fe` on `record/2026-10-27-stale-base-revisit` — step 1's full work, kept unmerged.
   - `5dc5c09` — merge of `origin/main`. One conflict (`transfer.md` header list), resolved to
     origin's side as instructed; `.gitignore` merged as a union.
   - Re-checked every step-1 fix against the merged tree, audited the resample count behind every
     manuscript interval, and applied only what was still wrong there (one `fix:` commit on top):
     `main.tex` abstention exception (1,000 / seed 0) and the no-interval paragraph;
     `model_metrics.md` 0.206 + [UNVERIFIED] molar mechanism; `PAPER_MATERIAL.md` §8.10, §8.14,
     §8.15, §8.25, §9; `verify_paper_numbers.py` guard (214 → 215); `transfer.md` header entry and
     §8 Docker/Python notes; `RESULTS_LOG` 2026-10-27. Also `paper/main.bbl`: origin's tracked copy
     lacked the four 15 Oct citations (tectonic hides it), so a pdfLaTeX build had 4 undefined
     citations; regenerated with `bibtex`, additive only.
   - Merged tree here: `pytest` 210 passed / 3 skipped, invariants hold, 215/215 claims.

## Decisions made

- **Keep origin's manuscript and `transfer.md` where they conflict** (user's instruction): origin
  is the maintained line; the stale-base edits targeted text that no longer exists.
- **Do not merge the paired-CI regeneration.** The manuscript now cites the post-switch comparison
  (`outputs/stage1_switch/`, 10,000 / seed 42), so the old intervals are history; `PAPER_MATERIAL`
  §8.25 points at the record branch for their saved regeneration instead.
- **State the abstention exception rather than re-run it at 10,000.** A re-run changes printed
  digits — its own result, with its own entry, if wanted.
- **Update origin's existing calibration-phrase assertion** rather than add a parallel one; the
  new guard covers only the abstention count, read from `gain_stats`'s default because the
  artefact does not record it.

## Open questions

- Should both abstention intervals be re-run at 10,000 / seed 42 so the methods sentence carries one
  exception fewer?
- The molar-mechanism figures (72.0 % / 60.2 %) have no artefact anywhere — save one (per-lesion
  tooth mapping over the 1,500 CariesXrays draw, CPU) or drop them from `model_metrics.md` and
  `PAPER_MATERIAL.md`?
- J_coverage's saved caries-gate upper bound is 16.62 (macOS) against 16.63 on Windows — a
  cross-machine float difference; harmless for the manuscript, which reads 16.63 from
  `outputs/c4_abstention/`, but worth knowing if the two files are ever compared.
- Seven Tufts scripts default to `REPO/_repo_archive/datasets_workspace/…` (macOS layout); on this
  clone that path is absent and `validate_fdi_assignment_tufts.py`'s leak check silently returns
  empty unless `--images` is passed. Not changed: a default image directory needs a frame check.

## Next steps

1. Push `main` when ready — 3 commits ahead of `origin/main` (`3cc15fe`, `5dc5c09`, the `fix:`).
   Keep `record/2026-10-27-stale-base-revisit`; do not merge it.
2. Rebuild the Docker image on Windows (predates the 11–15 Oct defaults).
3. Mentor meeting: venue per `transfer.md` §3 item 1, with `paper/ieee/main.pdf` as a reading copy.
4. Optional CPU items above (abstention re-run, molar-mechanism artefact).
