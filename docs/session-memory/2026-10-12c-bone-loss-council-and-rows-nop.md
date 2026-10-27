# 2026-10-12c — The bone-loss branch stays; rows N, O, P measured

**Session goal:** the user said he does not want the bone-loss model cut from the paper, asked
how to improve it so it can stay, asked for a council on that, and said to run the three
measurements recommended that morning (steps 2–4).

Run on the macOS clone on the evening of 12 Oct; written up on 13 Oct. Numbers are in
`RESULTS_LOG` 2026-10-12b (measurements) and -c (bone loss).

## What was done

### 1. Facts for the bone-loss question, before any member was seated

- Re-read `transfer.md` §2.5 and `PAPER_MATERIAL.md` §8.28.
- Looked for data with a periodontal label. The Ningxia ReadMe on this machine lists a
  2,000-image periodontitis **training** split; only the test splits are on disk. A web search
  found the BRAR dataset (Xia et al., *Scientific Data*, 15 Dec 2025): 1,104 patients, CC BY 4.0,
  patient-level bone-resorption grades, tabular labels only. Read from the article page, not
  from the files. Fourteen Firecrawl credits.
- Wrote the brief with seven options, K0 (cut) to K4 (a separate paper).

### 2. The bone-loss council

Three independent read-only `Plan` members, run in the background; none saw another's report.
"It stays" was given to them as the user's decision.

| Seat | Lens | Model | Recommendation |
|---|---|---|---|
| 1 | Strict reviewer, periodontal imaging | Opus | Held-out rescore now; a classifier trained on the Ningxia training split as a stretch; BRAR in a separate paper |
| 2 | Experimental design and feasibility | Opus | Re-description plus the held-out rescore now; BRAR as a gated side experiment; the Ningxia-trained classifier no |
| 3 | Paper architecture and the college's rules | Sonnet | Re-description in the six pages, the rescore if registered by 20 Oct; BRAR for the capstone report and a journal version |

**Consensus (3 of 3)**

- The branch is kept by re-describing it, and the 0.923, "domain shift", "did not transfer",
  "two independent external datasets agree" and the keyword "periodontal bone loss" leave.
- One measurement is worth running: the frozen Stage 4a, once, on Tufts radiographs that
  supplied no training crop.
- Training on one periodontal source and testing on the other is refused: a region mask and a
  patient grade share no label.
- BRAR does not go inside the six pages.

**Dissent**

| Point | Positions | Chair |
|---|---|---|
| A per-tooth classifier trained on the Ningxia training split | Seat 1: recommend, conditional — the only route to a true periodontal claim, against a geometry-only baseline. Seat 2: no — 32–45% of teeth are positive, no patient is healthy, the label is box-against-band geometry, the split is on a pen drive, and it breaks a house rule | **Not now.** Checked in row G's saved file: under arm3c 38.6%, 32.4%, 30.5% and 11.2% of detected teeth are "affected" at the four hospitals. Seat 2's objection holds. On a tie, the smaller and reversible option |
| Amend the never-train-on-Ningxia rule for periodontitis | Seat 1: yes, narrowly. Seat 2: no | **No change.** It is the decision owner's and the mentor's rule to change, not a council's |
| What keeping costs against cutting | Seat 1: −3 to −5 points re-described only, −2 to 0 with the rescore. Seats 2 and 3: 0 to −3 | Judgements, not measurements. Recorded as given |

**What the chair verified**

- 339 of 1,000 Tufts expert masks are non-empty; 145 radiographs supplied crops; **290 with a
  non-empty mask supplied none.** The "roughly 290" in earlier documents is exact.
- The Tufts radiographs, masks and boxes are on this machine under
  `_repo_archive/datasets_workspace/`. `scripts/eval/bootstrap_ci.py` 255–261 and a line of
  `model_metrics.md` still said they were absent; the scoreboard line is corrected, the script's
  note is not (it is a string in a script that produced published numbers).
- `main.tex` 1273–1275 says no second annotated periodontal corpus exists in this project.
- Neither the grade table nor the department guidelines says anything about what a paper must
  cover.

**Not verified:** anything about BRAR's files; whether the Ningxia training split is still on
the pen drive; why only 145 radiographs were cropped when 339 carry a mask; every acceptance
estimate.

### 3. Rows N, O, P

1. **Amendment 3** written and, on the user's instruction, committed by me at `f5d7f29` — that
   one file, not pushed — before any row was read.
2. **Row P's code.** `validate_fdi_assignment_tufts.py` gained `load_ufba_gt` and three options
   (`--ufba`, `--exclude`, `--aspect`). One unit test. The first write turned the file's CRLF
   endings into LF; caught in the diff stat and restored before anything ran.
3. **Gate P1:** the changed scorer, run on Tufts with arm3c into the scratchpad, gives rows
   byte-identical to row A's.
4. **Rows N and O** added to `stage1_switch_intervals.py` and read.
5. **Row P stopped at gate P2**, 404 of 425, before any model ran. Diagnosed from the label
   files: 21 images lack teeth in an arch or on a side; none is reversed. Asked the user;
   he chose to amend. **Amendment 4** committed by me at `f75e81f`, same terms. The failed gate
   output was moved to `P_ufba_gates_v1_failed/`, not deleted.
6. **Row P ran:** gates, then four runs, about fifteen minutes.
7. **Re-derived** every count of all three rows with separate code, and the four end-to-end
   intervals with a separate bootstrap. All match.
8. **Audited** the new documentation: 44 typed intervals, all present in the results file.
9. **Documents:** `RESULTS_LOG` -b and -c, `model_metrics.md`, `PAPER_MATERIAL.md` §8.32 and
   §8.33, `transfer.md`, `SUBMISSION_TODO.md`, the root and two folder READMEs. The detector
   profile in `scripts/run_inference.py` said no unseen-source figure existed; it now quotes
   both UFBA figures.

Committed by me: `f5d7f29` and `f75e81f` only, both local. Everything else is for the user.

## Decisions made

- **"It stays" is recorded as the decision owner's decision**, in the log, the snapshot and the
  submission list, and saved to memory so it is not argued again.
- **I told the user the branch cannot be improved on its own data.** He asked how to improve
  it. The honest answer is that the label is the fault, and that the way to a periodontal claim
  runs through a periodontal label. Two exist; the paper said none did.
- **The registered UFBA figure is 44.5%, and the 77.2% is written second every time.** The
  widening was registered as a sensitivity analysis on an unverified aspect ratio. It happens
  to be the flattering number, which is the reason to hold the order.
- **`models/11` was run on UFBA beside arm3c.** It doubled the compute and gives the only
  evidence about the 11 Oct switch on data neither detector saw. The amendment fixed in advance
  that the default changes on no outcome, and that if the old detector had won the paper would
  say so.
- **Row N's primary is reported as not computable.** The cohort has no tooth labelled healthy.
  I did not go to the 86 excluded images for one: they are training data for the numbering
  head and the row was not registered on them.
- **The gate was amended, not bypassed.** It fired as written; the cause was diagnosed from
  labels alone; the user chose; the corrected rule was committed; only then did a model run.
  Images that define no comparison stay in the scored cohort, because dropping them would
  select the cohort on its content.
- **The two amendment headers carry hand-typed times that are a few minutes off.** The log
  says so and gives the commit times. The amendments themselves were not edited.
- **`run_inference.py` was changed by one string.** A shipped report that says no unseen-source
  figure exists, the day one is measured, is the staleness this repo keeps paying for. No
  prediction changes.

## Open questions

- **Does the user want the held-out rescore of Stage 4a run?** It needs its own
  pre-registration. Seat 2 sketched one: every Tufts radiograph that supplied no crop, clean
  crops only, the frozen checkpoint, sensitivity and specificity with a radiograph-cluster
  interval, a gate that first re-cuts the existing validation crops.
- **Does the user want BRAR downloaded?** Its size and its columns are unknown.
- **Does the mentor require the paper to cover periodontal disease?** Unasked.
- Why were only 145 Tufts radiographs cropped for Stage 4?
- Is 1991:1127 the true shape of the UFBA-425 images?
- How many of arm3c's 621 boxes on no labelled Tufts tooth carry one of the constant's codes?
- Carried over: the mentor and the repo owner on the switch and the headline; the grading date;
  the Tufts Drive folder; the Kaggle licence.

## Next steps

1. The user commits and pushes this session's changes; `f5d7f29` and `f75e81f` go with them.
2. The user's answers on the rescore and on BRAR.
3. The six-page draft, with `SUBMISSION_TODO.md` §1a rows a to n and §2 item 3.
4. Mentor and repo owner.
5. Windows machine: pdfLaTeX build, `paper/paper.txt`, Docker rebuild.
