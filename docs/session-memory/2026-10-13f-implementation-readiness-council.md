# 2026-10-13f — Council: is anything left to implement, and is every stage fit to publish?

**Session goal:** the user asked, for the third time in two days and after the Stage-1 and
Stage-4a changes, whether every stage's metrics are good, test metrics included, and for a plan
of implementation steps toward publishing "confidently without worrying". Asked for the
`mle-workflow` skill, the new `/mle-review` command and a council.

Run on the macOS clone, late on 13 Oct. **No model was run, no cohort was scored and no code
changed.** Seven documents were edited. Numbers are in `RESULTS_LOG` 2026-10-13d.

## What was done

### 1. Facts first, by the chair

- `pytest tests`: 184 passed. `scripts/eval/verify_invariants.py`: all 11 hold.
  `scripts/verify_paper_numbers.py`: 191 claims, no drift.
- All nine checkpoint files named in `scripts/run_inference.py` are tracked. A `git archive`
  extract of `898abf4`, tracked files only, runs the default pipeline (schema 1.4, both current
  tags). One image; the extract was deleted afterwards.
- A per-stage evidence table and sixteen candidate actions (A–P) went into one brief in the
  session scratchpad.

### 2. The council

Three independent read-only members and one reviewer; none saw another's report. None executed
repo code.

| Seat | Lens | Agent, model |
|---|---|---|
| 1 | Hostile referee | `Plan`, Opus |
| 2 | Experimental design and feasibility | `Plan`, Opus |
| 3 | Release engineering and deadline | `Plan`, Sonnet |
| — | ML-engineering review, findings only | `mle-reviewer` |

**Consensus (3 of 3)**

| Question | Verdict |
|---|---|
| A new model, a new measurement, a second pass over the Tufts test split, any pass over Ningxia | **No** |
| Retrain Stage 4b; a second round on Stage 4a; anything more for the lesion detector; BRAR for this paper | **Don't** |
| Stage 3b | Describe as present, not evaluated |
| Stale text (README banner image, the five 0.923 sentences in `main.tex`, the overview page) | **Must** |
| An exact-version lock file; an invariant that the split is disjoint | Should |
| Stage 4a's 27.5% on its own | Not reportable alone: three runs, with the share of flags that are correct |
| "Publish confidently without worrying" | Not as "all metrics are good". As: no sentence can be falsified from the repo |

**Dissent**

| Point | Positions | Chair |
|---|---|---|
| Severity grades in the report | Seat 2: hide both. Seat 1: label or hide, must. Seat 3: label only, do not hide | **Hide the Stage-4b grade by default; keep Stage 3b's with a line that it has no test.** Seat 3 graded before the contrast finding was known. The decision is the user's: it changes the demo |
| A first test of Stage 4b | Seats 1 and 3: optional. Seat 2: don't | **Don't.** Its labels are not the quantity the test would score |
| Loud failures in evaluation scripts | Seat 1: should. Seat 3: after submission | **After submission.** Seat 3 recounted the DENTEX cohort from the label files against 17 saved outputs; no figure moved |
| Hash checks | Seat 3: pin the two missing files and stamp all hashes; do not enforce at load. Seats 1, 2: optional | **Pin and stamp.** The default caries path has no pin today |
| Stop date for code | 17 Oct, 18 Oct, 20 Oct | **20 Oct** |

### 3. What the chair verified

- **Stage 4b's labels are image contrast** (Seat 2). The saved output of cell 5 of
  `notebooks/bone_loss/04_bone_loss_severity.ipynb` lists the metadata columns as `filename,
  label, stem, augmented` and prints the warning that it is building a proxy from image
  contrast. The code beside it takes the standard deviation of the grey crop. The manifests under
  `data/tufts/severity_dataset/metadata/` carry the rescaled 0.01–0.30 column.
- **Three of Stage 4b's radiographs are in the Tufts test split**: 149 and 192 in training, 249
  in validation. Counted from the manifests against `outputs/eda_tufts/split_v1.csv`.
- **The three-run reading of Stage 4a** (Seat 1 and the reviewer): recounted from
  `test_rows.json` — 50, 30 and 20 of 182; 202, 102 and 71 flagged; 14 found by all three. The
  intervals, ROC areas and differences were read from `test_summary.json`.
- **The report's caries caveat** and its "no model in this pipeline trained on" sentence: read in
  `scripts/run_inference.py`.
- **The two missing hash pins**: read in `scripts/eval/verify_invariants.py`.
- **Commit times**: `0993d4a` (protocol) 18:10; `tooth_prior.json` written 18:12; test rows
  19:59; the scripts' first commit `6b57f39` 20:10.
- **The 55 / 63 / 64 split of test positives by true overlap** (Seat 2): recounted.

Not verified by the chair: that `weights_only=True` would load the five classifier checkpoints
(Seat 3 disassembled the pickles and expects it to); the cause of one unreadable image recorded
at Ningxia test1 on the other machine; whether JPEG ringing in the expert masks creates
positives; near-duplicate radiographs across the retraining split; Seat 2's count that Stage
4b's class agrees with the true overlap class in 6 of 14 rows on the teeth both files hold; the
conference's format and artefact rules, whose call for papers was not checked.

### 4. Documents edited

`docs/results/RESULTS_LOG.md` (entry 2026-10-13d), `docs/results/model_metrics.md` (Stage 4a
and 4b), `docs/results/PAPER_MATERIAL.md` (§8.37 and one checklist item), `transfer.md` (top
note, §1, §2.1, §3, §4, §8), `docs/paper/SUBMISSION_TODO.md` (§1a rows o–r; §2 item 9),
`models/04_bone_loss_severity_notebook_models/run_summary.txt` (a dated correction; the hash
line is untouched and the invariant still passes), `README.md` (one sentence).

Earlier in the same conversation a `/mle-review` command was added to the user's own
configuration; that is recorded in `2026-10-13e-implementation-skills.md`.

## Decisions made

- **Logged, not fixed.** The findings touch the report's text, which lives in code. A change
  there is a schema bump and a change to what the demo shows. The user asked for a check and a
  plan; the plan is in `transfer.md` §3.
- **A run summary was corrected in place, with a date, above the text it corrects.** It is not
  a journal, and leaving "labels come from the overlap ratio" as the first thing a reader meets
  would repeat the fault.
- **The stale Stage-4 paragraph in the submission list was superseded by a new row, not
  rewritten.** That cell already carries four layers of history; a fifth would be unreadable.
- **The chair's recommendation on severity goes one step past two of the three seats** because
  the finding that justifies it arrived from the third.
- **No ensemble was computed**, though the saved rows would allow it in one line. A number
  chosen after seeing three test results is not a result.

## Open questions

- Hide the Stage-4b grade, or label it? The user's call.
- Does the mentor accept a Stage 4 whose own numbers are this weak, described this plainly?
  She has still not been told of the detector switch, the held-out result, the retraining or the
  adoption.
- Is the conference deadline 15 Dec? The call for papers was not live when it was read.
- The Kaggle set's licence, now that the manuscript reports the detector trained on it.
- Carried over: the grading date; the Tufts Drive folder; the pdfLaTeX build.

## Next steps

1. The user commits the seven documents and this file.
2. The user decides on the severity grades.
3. With that decision: one code change, schema 1.5 — corrected report texts, every checkpoint's
   hash stamped, the two missing pins, the split invariant. Then the lock file and the stale
   text. Stop on 20 Oct.
4. The mentor meeting, before more is built on decisions she has not seen.
5. The six-page cut, from `SUBMISSION_TODO.md` §1a rows a–r.
