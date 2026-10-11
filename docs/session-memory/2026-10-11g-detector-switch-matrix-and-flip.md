# 2026-10-11g — Detector switch: the matrix run, the stop rule applied, the default changed

**Session goal:** Phases 3 to 5 of the plan in `2026-10-11e` — run the pre-registered
re-measurement, apply its one stop rule, change `DEF_DETECTOR`, and bring the documents along.

Run on the macOS clone. Numbers are in `RESULTS_LOG` 2026-10-11g; this file is the narrative.

## What was done

1. **Checked the starting state.** Tree clean at `c139779`, the commit that froze
   `outputs/stage1_switch/PRE_REGISTRATION.md`; all weight hashes matched.
2. **Wrote `outputs/stage1_switch/run_matrix.sh`** — every command of the matrix, one function
   per row, `models/11` before arm3c, each run in its own directory with its stdout. It refuses
   a run whose directory exists, so no row can be re-run by accident.
3. **Wrote `scripts/eval/stage1_switch_intervals.py`** — gates, point estimates, paired
   intervals and the stop rule. It reuses `bootstrap_ci.py`, `caries_intervals.py` and
   `lever_b_bootstrap.load_normalised`, opens a row's arm3c files only after that row's control
   has passed, and writes `stage1_switch_results.json`.
4. **Ran the rows** in the order A, B, H, C, D (alone, for latency), E (both detectors in
   parallel), then F and G. 32 runs, about two hours.
5. **Amendment 1**, committed locally by me at `85df6ff` on the user's instruction (that one
   file, not pushed), before any Ningxia run. See Decisions.
6. **Applied S1.** +10.40 pp [+8.71, +12.09] against a −2 pp bound. It does not fire.
7. **Changed the default.** `scripts/run_inference.py`: `DEF_DETECTOR` → arm3c; a
   `DETECTOR_PROFILES` entry with row B's figures and an in-domain note; the module docstring;
   the console note. `app.py`: docstring only. `.gitignore`: an exception for
   `arm3c_best.pt`.
8. **Verified.** `pytest tests` 174 passed; `verify_paper_numbers.py` 127 of 127; all eleven
   invariants hold; a default run and a `--detector models/11` run on one DENTEX image each
   carry their own tag and figures and reproduce their row D caries codes.
9. **Documents.** `RESULTS_LOG` 2026-10-11g; `model_metrics.md` (a new first section);
   `PAPER_MATERIAL.md` §5.1, §7.1, §8.30, §9; `transfer.md`; `README.md`; `models/README.md`;
   both run summaries; `docs/EXTERNAL_DRIVE.md`; `scripts/eval/README.md`;
   `scripts/yolo/README.md`; `CLAUDE.md` rule 4 and §6.

**Nothing is committed except Amendment 1.** The user commits.

## Decisions made

- **Amendment 1, before any Ningxia run.** While row D was running I read
  `affected_tooth_sensitivity` and saw that row G's frozen gate — exactly 6,791 affected teeth —
  is a count of *detected* boxes taken from the other machine, where the same weights give
  slightly different boxes. I asked the user rather than run and see. They chose to amend, with
  me committing only the pre-registration. The control then gave 6,792: the frozen gate would
  have failed by one tooth. This is the second gate I have drafted too tightly against a
  cross-machine figure (the first was this morning's M3 tolerance). The lesson is to ask, of
  every reference count, whether it is a property of the dataset or of a model's output.
- **The row C stop was the script's, and was fixed before reading the outcome.** The script
  compared 148 per-image rows with 164 images. `lesion_localization.py` lists only images that
  carry a caries lesion; the control files themselves say 164 and 479, as the published ones
  do. I changed the gate to read each file's own image count. No arm3c file of row C had been
  opened. It is disclosed in the results entry.
- **The Ningxia rows ran without the repo owner being told.** I asked; the user said he had not
  been and to run. The pre-registration allows that if the results entry says so, and it does.
- **The registered accuracy is row B's, as the pre-registration fixed, and the text beside it
  does the work.** 92.8% is an in-domain figure. The profile says so, gives the Tufts figure,
  and says no figure exists for an unseen source. I also rewrote the console line, which would
  otherwise have turned 92.8% into "about 7% of codes are expected wrong" — a claim nobody has
  measured for a new radiograph. That line changed for `models/11` too; it now quotes the
  figure and points at the interpretation instead of converting it.
- **`count_model_params.py` and `outputs/param_counts/` were left on `models/11`.**
  `verify_paper_numbers.py` asserts the manuscript against that file, and the manuscript still
  describes the previous detector. Changing one without the other would break a check that is
  currently true. The new counts are in `outputs/stage1_switch/H_params_arm3c/`.
- **`paper/main.tex` was not touched.** No LaTeX on this machine, and which front end the paper
  reports is the authors' decision, not an edit.
- **arm3c's weights are whitelisted, not committed.** A 51 MB file stays in history once
  pushed, and the owner has not been told. The whitelist makes the commit a one-line `git add`
  when the user decides.
- **The README's figures were left alone.** `hero.svg`, `pipeline.svg` and
  `error-propagation.svg` carry the previous front end's numbers. A dated note at the top says
  so. Redrawing them belongs with the manuscript decision.
- **Two stale lines corrected in passing, both verified first:** `transfer.md` listed
  `models/09`'s gate as Drive-only (it is tracked), and `models/README.md` called the gate the
  Stage-3 pipeline default (it has not been since 4 Sep).
- **Row E ran both detectors at once** to save an hour. Thread count is unchanged by that, and
  both controls reproduced their counts. Row D ran alone because it records latency.

## Open questions

- **Has the manuscript's front end been decided?** `PAPER_MATERIAL.md` §8.30 sets out both
  options. Until it is, the paper and the code disagree.
- **The repo owner and the mentor still do not know.**
- **The Kaggle "dual-labeled" licence.**
- **On DENTEX, under arm3c, the retired gate has higher lesion agreement than the lesion
  detector** (0.802 against 0.595) while flagging 2.4 times the teeth, and lower F1 (0.363
  against 0.498). I have reported both and not explained it beyond the flag counts. Whether the
  gate is finding real unannotated caries or simply covering area is not something this matrix
  can say.
- **Teeth matched to a box but given no code rose from 26 to 65 on Tufts.** The reject option
  the morning council parked is the obvious response, and it needs its own pre-registration.
- **Bare `pytest` fails at collection** because it also picks up
  `_repo_archive/implementation_stale_clone/`. `pytest tests` is what the docs say and what
  passes. Worth a `testpaths` line in a config file; not done here.

## Next steps

1. The user reviews and commits: the code change with the `.gitignore` exception; the run
   outputs and scripts; the documents. Whether `arm3c_best.pt` goes in that commit is theirs.
2. Tell the repo owner and the mentor, before the weights are pushed.
3. Decide the manuscript's front end.
4. On the Windows machine: `main.tex` and its PDF; then `count_model_params.py`,
   `param_counts.json` and `verify_paper_numbers.py` together; Docker rebuild and smoke test.
5. The Kaggle licence.
