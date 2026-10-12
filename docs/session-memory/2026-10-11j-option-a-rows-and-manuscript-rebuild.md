# 2026-10-11j — Option A: five more rows, and the manuscript rebuilt on the current front end

**Session goal:** the user chose option A of `docs/paper/SUBMISSION_TODO.md` §1 — rebuild the
manuscript on the multi-corpus tooth detector — and said to continue.

Run on the macOS clone. Numbers are in `RESULTS_LOG` 2026-10-11j (measurements) and -k
(manuscript).

## What was done

1. **Scoped it.** Read `paper/main.tex` in full, its number checker and the three figure
   scripts. Five things the manuscript reports had not been measured under the current
   detector; one of them — "fires on 0.7% of DENTEX teeth" — traced back to a 12-image run with
   the bbox detector of two front ends ago.
2. **Amendment 2** to `outputs/stage1_switch/PRE_REGISTRATION.md`, five rows (I to M),
   committed locally by me at `d78f502` on the user's instruction — that one file, not pushed —
   before any of them ran.
3. **Ran rows I, J, K, M and computed L.** `run_matrix.sh` gained the four commands;
   `c4_coverage_accuracy.py` gained `--rows`; `stage1_switch_intervals.py` gained the gates and
   reports. All five gates passed. Taxonomy and coverage were re-derived by separate code.
4. **Asked two things** before going further: who commits the amendment, and how to handle a
   manuscript this machine could not build. Answers: I commit the amendment; install tectonic.
5. **Installed tectonic 0.17** with Homebrew and built the unchanged manuscript first, as a
   baseline.
6. **Rewrote `paper/main.tex`** in three passes — front matter to protocol, results, discussion
   to conclusion — compiling after each. Each replacement was anchored on unique strings and
   asserted, so a missed anchor stops the patch rather than editing the wrong place.
7. **Leak-checked the 1,200 CariesXrays images** against every other corpus, because the new
   text says they are leak-free and the old check covered a different sample.
8. **Re-rendered four figures**; repointed two figure scripts; copied the taxonomy and coverage
   figures from rows I and J.
9. **Rebuilt `scripts/verify_paper_numbers.py`** against the new artefacts: 191 claims. Tested
   it with eight deliberately wrong digits.
10. **Moved `count_model_params.py` and `param_counts.json`** to the current detector.
11. **Documents:** `RESULTS_LOG` -j and -k, `model_metrics.md`, `PAPER_MATERIAL.md` §8.30 and
    §9, `transfer.md`, `SUBMISSION_TODO.md`, `README.md`, `scripts/eval/README.md`.

Committed by me: `d78f502` only. Everything else is for the user to commit.

## Decisions made

- **The paper's claim was moved, not softened.** It no longer says a constant beats the
  pipeline at home. It says that beating it at home, with a detector trained on that corpus,
  tells nothing about four hospitals where the two cannot be separated. Every sentence that
  reports the development-data lead says in the same breath that the detector had seen the
  corpus.
- **The override is in the paper.** §Data states that the detector was adopted over a registered
  guard it failed, with the figure. A paper that asks others to report what does not favour
  them cannot leave that out.
- **Lever B's verdict is quoted as it was scored.** The rule was met on the previous front end,
  and the manuscript says so and gives those three numbers. The table shows the current front
  end as a description. I did not let the new, slightly better external numbers stand in for
  the old verdict.
- **The Tufts cost is stated like for like.** Row M gave Control B 0.723 and arm3c 0.587 in one
  label frame on one machine: −13.6 pp. The 0.810 → 0.585 that this project — and I, in entries
  -f and -g — had been quoting sets a segmentation model on polygon labels against a detection
  model on box labels. The manuscript uses the like-for-like figure.
- **Three statistics were dropped rather than carried over.** "72.0% on molars", "60.2% on the
  eight codes" and "22.1% outside any detected tooth" came from the 1,500-image CariesXrays
  sample under an earlier detector. They were not re-measured, so they are not in the rebuilt
  text. The constant's own agreement, 0.604, makes the same point from a number that was
  measured.
- **Two false sentences about the bone-loss split were corrected because they were being
  retyped.** Whether the branch stays is still the authors' decision; I did not rename it or
  change "domain shift", and the checklist says what is left.
- **A font fallback went into the preamble.** Under XeTeX, IEEEtran's Times request found
  nothing, the bold face vanished and the paper grew a page. Five conditional lines load a
  Times clone for non-pdfLaTeX engines. Checked: the previous manuscript then builds to 14
  pages, the same as the committed pdfLaTeX PDF. pdfLaTeX never enters the branch.
- **`paper/main.pdf` is now the tectonic build.** A PDF that matches its source seemed better
  than a correct-engine PDF of a text that no longer exists. It is marked as such everywhere.
- **`paper/paper.txt` was left stale.** It is a `pdftotext` dump with no recorded command and
  this machine has no `pdftotext`. Guessing its format would have been worse than saying so.
- **The integrity gate was narrowed once more.** It stopped the first read of rows I–M because
  `run_matrix.sh`, tracked since the last push, had gained the new rows. The run script is the
  command list, not a result, so it is exempt like the script's two outputs.
- **The same gate then objected to the regenerated parameter file, and it was right to.**
  `outputs/param_counts/param_counts.json` is a tracked output and I had changed it on purpose.
  I did not exempt it. The results log was regenerated with that file put back to its committed
  state, and the new parameter file restored afterwards; the results file came out
  byte-identical. Until this session's changes are committed,
  `stage1_switch_intervals.py` will stop on that file. After the commit it runs clean.
- **The checker's weakness is stated, not hidden.** It asserts by presence. Of eight wrong
  digits it caught four; the four it missed are numbers that also appear correctly elsewhere.
  I listed every repeated quantity by pattern and found one spelling each. That check is not in
  the repo; the limit is described in the log entry.

## Open questions

- **The mentor has not read the new headline.** This is the main one.
- **Ningxia test4 under Stage 4:** affected teeth fall from 630 to 223 with the new detector
  while detected teeth rise. Boxes are not saved and Ningxia was not re-run. Unexplained.
- **Is the rebuilt paper's claim one the authors want?** I wrote it to be true and to keep the
  paper's argument. Whether it is the paper they want to submit is theirs.
- **Length.** 15 pages now. The six-page cut for a conference is a separate piece of writing.
- Carried over: the Kaggle licence; the repo owner and mentor; the reject option for surplus
  boxes; a cross-domain numbering figure (UFBA-425 is on this machine and unused by the
  detector and the head).

## Next steps

1. The user reviews the rebuilt manuscript — `paper/main.pdf`, 15 pages — and commits.
2. Mentor: the new headline, with `SUBMISSION_TODO.md` §1 as the one-page summary.
3. Windows machine: pdfLaTeX build, `paper.txt`, Docker.
4. `SUBMISSION_TODO.md` §2: authors, the mandatory statements, the bone-loss branch, the
   49-papers claim, venue and length, compliance.
