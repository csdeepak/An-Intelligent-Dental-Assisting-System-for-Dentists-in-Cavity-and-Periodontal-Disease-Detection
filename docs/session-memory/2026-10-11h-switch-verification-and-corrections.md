# 2026-10-11h — Detector switch: verified after the push, and three rounding slips corrected

**Session goal:** the user had committed and pushed the switch (`7dd3ff4`) and asked to continue
and to verify and cross-check. Check that what was pushed works and that what was written is
right.

Run on the macOS clone. Numbers are in `RESULTS_LOG` 2026-10-11h.

## What was done

1. **Checked the push.** `HEAD` and `origin/main` both at `7dd3ff4`, tree clean, all 32 run
   directories in the commit. `arm3c_best.pt` is tracked: 51,227,097 bytes, sha256 equal to the
   pin, no LFS pointer.
2. **Fresh-checkout test.** `git worktree add --detach` of `HEAD` into the session scratchpad —
   tracked files only, nothing ignored. From it: the default pipeline on one DENTEX image
   (arm3c tag, hash and figures; caries codes equal row D's), `pytest tests`,
   `verify_paper_numbers.py`, `verify_invariants.py`, and `stage1_switch_intervals.py`, which
   rewrote the results file byte for byte. The worktree was removed afterwards.
3. **Independent re-derivation.** A throwaway script, not in the repo. Method, so it can be
   rewritten: read each run's raw JSON; build per-image numpy arrays keyed by sorted image id
   (Ningxia by `(split, image)`); check each producing script's own totals against the
   results file; bootstrap ratio differences with one vectorised
   `rng.integers(0, n, (10000, n))` draw at seed 7; F1 as the ratio `2·tp / (pred + gt)` of
   per-image sums. 164 comparisons, all agree.
4. **Monte Carlo precision.** 30 seeds and one 400,000-resample run on the DENTEX numbering
   difference; 30 seeds on the three registered bounds nearest zero.
5. **Document audit.** Every `x pp [a, b]` in the entry and the documents derived from it
   matched against the results file (58 of 58); every table value recomputed with exact
   half-up rounding from integer counts (73 figures).
6. **Corrections.** Three figures off by one in the third decimal; fixed in `model_metrics.md`,
   `PAPER_MATERIAL.md` §8.30, `transfer.md` §2.4 and `models/15…/run_summary.txt`, and recorded
   in a new log entry because 2026-10-11g is not to be edited. Documents saying arm3c's weights
   were "not yet committed" corrected in `transfer.md`, `README.md`, `models/README.md`,
   `docs/EXTERNAL_DRIVE.md`, the run summary and `CLAUDE.md`.
7. **Script.** `stage1_switch_intervals.py`: agreements printed to four places with counts;
   the integrity gate exempts the script's own two outputs. Log regenerated; results file
   unchanged.

Nothing is committed. The user commits.

## Decisions made

- **A new log entry rather than an edit.** The three figures are in an entry that is already
  pushed. The rule is append-only, and a reader of 2026-10-11g should be able to find out that
  three of its digits were wrong.
- **`docs/session-memory/2026-10-11g…` was left alone**, though it quotes "0.363". Session
  files are not edited after their session; this file is the correction.
- **The second implementation was not added to the repo.** One script already computes these
  numbers and is tested by reproducing them from a clean checkout. A second permanent copy is
  two things to keep in step. Its method is written above.
- **The integrity gate was narrowed, not removed.** It tripped because the script's own log is
  now tracked and the shell truncates it before Python starts. Exempting those two files keeps
  the protection for every other output, and that was tested by touching another tracked output
  and watching the gate stop.
- **The log prints four places and the counts.** The slip came from rounding a rounded number.
  Printing the counts beside the value removes the temptation.
- **The different-seed comparison was kept as the check.** Replaying the registered seed proves
  two implementations make the same draws; a different seed shows the conclusions do not
  depend on the draws. Both were done; the second is the more useful.
- **Did not start anything new.** What is left for the switch is the manuscript's front end,
  the repo owner and mentor, the licence, and the Windows-side rebuilds. None is an engineering
  task for this machine, and the parked measurements each need a pre-registration and a go.

## Open questions

- Whether the repo owner and the mentor have been told. The weights are now pushed; the last
  recorded word, before the Ningxia rows ran, was that the owner had not been.
- Ningxia test3 under arm3c, lesion detector against the gate: +9.88 pp [+0.74, +19.20] on 40
  images. "Separated" by the registered rule and stable across seeds, but it is the thinnest
  such call in the entry and should not carry weight in the paper.
- Everything open in `2026-10-11g`, unchanged: the manuscript's front end, the gate scoring
  above the lesion detector on DENTEX lesion agreement, the 26 → 65 uncoded Tufts teeth, the
  Kaggle licence, bare `pytest` collecting the archived clone.

## Next steps

1. The user reviews and commits this session's changes.
2. Tell the repo owner and the mentor.
3. Decide the manuscript's front end (`PAPER_MATERIAL.md` §8.30, §9).
4. On the Windows machine: `main.tex` and PDF; `count_model_params.py`, `param_counts.json` and
   `verify_paper_numbers.py` together; Docker rebuild and smoke test.
5. The Kaggle licence.
