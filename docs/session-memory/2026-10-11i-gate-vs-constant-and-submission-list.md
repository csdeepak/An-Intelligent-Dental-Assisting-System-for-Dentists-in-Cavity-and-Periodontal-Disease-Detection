# 2026-10-11i — The paper's own comparison under the new detector, and the submission list rewritten

**Session goal:** the user asked to continue, asked whether JarvisLabs credits exist, and said to
use a GPU if one was required. Find what is next, and whether it needs one.

Run on the macOS clone. Numbers are in `RESULTS_LOG` 2026-10-11i.

## What was done

1. **Checked the account.** `jl status`: balance ₹1,148.78, no grants, nothing running or
   paused. Read only; no instance was created.
2. **Decided no GPU was required.** Every open item in `transfer.md` §3 is a decision, an edit
   to the manuscript, or a rebuild on the other machine. See Decisions.
3. **Took the one open item with no owner: `docs/paper/SUBMISSION_TODO.md`** (§3 item 12, stale
   since 28 Aug). To rewrite it honestly each line had to be checked against `paper/main.tex`,
   which meant reading every results table against the 11 Oct matrix.
4. **Found a gap in the matrix.** It compared the lesion detector with the constant and with
   the gate. It never compared the gate pipeline with the constant — the comparison the
   abstract, four tables and the Conclusion rest on. Added it to
   `scripts/eval/stage1_switch_intervals.py` from the saved runs: 14 new blocks in the results
   file, no existing value changed.
5. **The result.** On DENTEX the order reverses with the front end: the gate pipeline is now
   above the constant on lesion agreement (+17.12 pp [+12.15, +21.89]) and on F1 (+4.27 pp
   [+1.58, +7.05]). On Ningxia and CariesXrays nothing moves.
6. **Cross-checked** the 14 comparisons with a second implementation, and the seed sensitivity
   of the three bounds nearest zero.
7. **Rewrote the submission list** around the decision that result sharpens, with a
   line-by-line table of what `main.tex` would say on the current front end and where each value
   lives, and a list of what has not been measured on it.
8. **Carried it through:** `model_metrics.md`, `PAPER_MATERIAL.md` §8.30 and §9, `transfer.md`,
   `README.md`.

Nothing is committed. The user commits.

## Decisions made

- **No GPU, and no new experiment.** The balance would buy two runs of the lesion detector
  (₹547 each) and nothing on the list asks for one. The work list says writing is the critical
  path and that no GPU work starts without a pre-registration and a go; a general "use it if
  required" is not that, and nothing was required.
- **The gate-against-constant comparison was added although it was not pre-registered.** It
  needs no run and decides nothing; it is the manuscript's own comparison, and leaving it out
  would have meant the authors chose a front end without knowing it reverses their headline.
  The log entry and the script both say it was chosen after the matrix had been read.
- **The finding is reported with its limits in the same breath.** DENTEX is in-domain for the
  new detector; the gate's lead on lesion agreement comes with 1,439 flagged teeth against 988;
  and the old headline itself excluded zero by one lesion on this machine. Without those three
  it reads as "the pipeline works now", which the external rows do not support.
- **Did not choose a front end for the manuscript and did not edit `main.tex`.** The submission
  list sets out both options. Option A changes what the paper claims.
- **Intervals in the new list are quoted to two decimals as stored**, not re-rounded to the
  manuscript's one decimal — the mistake of 2026-10-11h, avoided. The per-hospital differences
  are given to one decimal because they come straight from counts.
- **Tables are named by LaTeX label.** The built PDF numbers the FDI-set table IV; several
  older notes call it "Table I". Not mass-corrected; the new list says so once.

## Open questions

- **Which front end the paper reports.** Now the central question, not a housekeeping one.
- The gate pipeline's F1 gap to the constant on the previous front end has an interval only on
  the other machine's arm (−2.61 pp [−5.99, +0.64]); on this machine the point is −1.95 pp and
  no interval was computed. Cheap to add if option B is chosen.
- If option A: seven things are unmeasured on the current front end (`SUBMISSION_TODO.md`
  §1.2), all CPU. Whether each needs a line in a pre-registration is worth deciding once,
  together, rather than piecemeal.
- Three measurements that would strengthen either paper and are not on any list: numbering on
  UFBA-425 (425 images with per-tooth FDI boxes, CC BY 4.0, on this machine, never used to
  train the current detector or the numbering head) as the missing cross-domain figure; a second
  training seed of the lesion detector (about ₹547); the reject option for surplus boxes. None
  was started.

## Next steps

1. The user reviews and commits.
2. Take `docs/paper/SUBMISSION_TODO.md` §1 to the mentor with the two-column table.
3. If A: pre-register and run §1.2 on this machine, then rebuild on the other one.
   If B: one paragraph and one restated table row.
4. Everything in §2 of that list, whichever is chosen.
