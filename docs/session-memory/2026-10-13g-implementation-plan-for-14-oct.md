# 2026-10-13g — Implementation plan for 14 Oct: what the council found, turned into tasks

**Session goal:** the user asked for a proper plan of everything from the 13 Oct council
(`2026-10-13f-implementation-readiness-council.md`) and every per-stage flaw that can be fixed,
to implement on 14 Oct.

Run on the macOS clone, 13 Oct, late. **No code changed.** This file and one pointer line in
`transfer.md` are the only edits.

## What was done

Read the code each task touches, so the plan names real lines: `scripts/run_inference.py`
(schema history, `CARIES_METHOD_CAVEATS`, `BONE_LOSS_PROFILES`, `build_report`, `draw_overlay`,
`run_pipeline`, the CLI), `src/classifiers.py` (`run_bone_loss`, `run_caries_lesion_detector`),
`app.py`, `scripts/eval/verify_invariants.py` (`hash_from_summary`, `inv_weight_hashes`,
`inv_stage4_report_wording`), the two unpinned run summaries, `docs/assets/hero.svg`, the README
header, the Dockerfile header, `PROJECT_OVERVIEW.html`.

**Six more defects surfaced while reading. Each was checked, none is fixed yet.**

| # | Defect | Evidence |
|---|---|---|
| 1 | Every report names the numbering head `fdi-enumeration-head-resnet18-v1.0`; the head loaded by default is v2.0 | `scripts/run_inference.py:635`; `models/10_fdi_head_dentex_tufts_v2/run_summary.txt:5` |
| 2 | With `--caries-method gate`, the report's caries tag is the cascade's `caries-cascade-resnet18-v1.0`; the gate is `caries-gate-resnet18-v3.0` | `scripts/run_inference.py:599`; `models/09_caries_gate_v3/run_summary.txt:2` |
| 3 | The hash parser matches a filename token exactly. `models/16`'s summary writes `weights/best.pt`, so asked for `best.pt` it returns `last.pt`'s hash. Run on the real summary: returns `f774bb1e…`, the file is `029018db…`. A pin added naively would fail | `scripts/eval/verify_invariants.py:59-82` |
| 4 | `run_bone_loss`'s docstring says the severity classes "are degrees of bone loss" | `src/classifiers.py:378-379` |
| 5 | README badges: 174 tests (184), PyTorch 2.8 (the figures of 11–13 Oct came from 2.2.0), "YOLOv11l-seg" (the default detector has no masks). `tests/README.md` says 159 tests | `README.md:8-12`; `tests/README.md:1` |
| 6 | The Dockerfile header tells the user to mount two checkpoints that are no longer needed | `Dockerfile:6-10` |

**One thing that is better than assumed.** The app's per-tooth table has no Stage-4 severity
column. The Stage-4b grade is visible in two places only: the overlay label (`ABN-Sev`,
`ABN-Mod`, `ABN-Mil`) and the JSON (`bone_loss.severity`, `severity_confidence`). The Stage-3b
output is the caries `finding` itself (`caries` or `deep_caries`), shown in the app's table and
on the overlay.

## Decisions made

- **Scope: only changes that cannot move a measured number and need no cohort scored.** Every
  improvement that would need a new test was refused by the council and is listed at the end.
- **One schema bump, 1.5, carries every change to the report.** Five small bumps would be five
  things for a consumer to track.
- **The plan is written for withholding the Stage-4b grade by default**, the chair's
  recommendation. It is the user's decision (D1); the other answer removes two sub-steps.
- **Frozen evaluation scripts get input guards only**, each one unable to change an output on
  valid input, and nothing registered is re-run to prove it.
- **The manuscript is not in tomorrow's must list** (D2). It is the authors' text and the
  six-page cut will rewrite most of it.
- **The plan lives here** because `docs/README.md` sends a cold start to the newest
  session-memory file.

## Open questions — answer before starting

| | Question | Planned default |
|---|---|---|
| D1 | Stage-4b grade: withhold by default, or keep it with a label? | Withhold; a flag brings it back |
| D2 | Correct the Stage-4 text in `paper/main.tex` tomorrow (Phase C), or with the six-page cut? | With the cut |
| D3 | The headline tiles in the README banner: which figures replace 0.810 / 58.3% / 0.9233? | Proposal in T4 |
| D4 | The optional tasks T6 and T7: do them if time allows? | Yes, after the must tasks |

## Next steps — the plan

### Ground rules for the day

- Start with the Karpathy skill; `python-testing` when writing tests. No new dependency.
- **Nothing is scored.** No Ningxia, no Tufts test pass, no DENTEX matrix.
  `scripts/eval/bone_loss_v2_eval.py score` and `outputs/stage1_switch/run_matrix.sh` are not
  run.
- Baseline before the first edit: `pytest tests` (184), `scripts/eval/verify_invariants.py`
  (11), `scripts/verify_paper_numbers.py` (191). Save one default report and overlay of one
  fixed image in the scratchpad as the before-reference.
- After every task: the same three commands.
- Line endings: `scripts/run_inference.py`, `scripts/eval/verify_invariants.py`,
  `scripts/eval/validate_fdi_assignment_tufts.py`, `README.md`, `transfer.md` and everything
  under `docs/results/` are CRLF. Patch through bytes; check `git diff --stat` shows no
  whole-file change.
- The user commits. One commit per task is the suggestion.

### Order and size

| # | Task | Tier | Est. |
|---|---|---|---|
| T0 | Start of day: commit the pending documents, answer D1–D4, take the baseline | — | 0.3 h |
| T1 | Hash pins for the two unpinned default checkpoints | must | 0.5 h |
| T2 | An invariant that the Tufts split is disjoint | must | 0.5 h |
| T3 | Report schema 1.5: corrected texts, every hash and tag, the severity grade | must | 3.5 h |
| T4 | Stale text a reader meets first | must | 2.5 h |
| T5 | Exact-version lock file | should | 0.75 h |
| T6 | Safer checkpoint loading in the two serving loaders | optional | 0.5 h |
| T7 | Input guards in evaluation scripts | optional | 1 h |
| T8 | Close-out: log, scoreboard, snapshot, session file | must | 1.25 h |

About nine hours without the optional tasks. If the day runs short, T4 and T5 can move to
15 Oct; the stop date for code is 20 Oct. T3 must not be left half done.

### T1 — Hash pins (fixes: lesion detector and caries severity bundle have no pin)

- `scripts/eval/verify_invariants.py`, `hash_from_summary`: attribute a hash to the
  **basename** of the last weight file mentioned, so `weights/best.pt` matches `best.pt`.
  One line.
- `inv_weight_hashes`: add
  `models/16_lever_b_pooled/lever_b_pooled_yolo11l-2/weights/best.pt` with
  `models/16_lever_b_pooled/run_summary.txt`, and
  `models/07_caries_cascade/phase2_final_bundle.pth` with
  `models/07_caries_cascade/run_summary.txt`.
- `tests/test_verify_invariants.py`: one test that a path-prefixed filename resolves, one that
  the real `models/16` summary resolves `best.pt` to `029018db…` and not to `last.pt`'s hash.
- **Check:** the invariant's line lists ten files; the existing `models/03` best-versus-final
  test still passes.

### T2 — Split invariant (guards the fault that produced 0.923)

- `scripts/eval/verify_invariants.py`: a new check, registered like the others. From tracked
  files only:
  - `outputs/eda_tufts/split_v1.csv`: every filename once; 700 / 150 / 150.
  - `outputs/bone_loss_eval/v2_retrain/test_rows.json`: 143 distinct radiographs, every one
    `test`.
  - `data/tufts/severity_dataset/metadata/`: the severity model's radiographs meet the test
    split in exactly 149 and 192 (training) and 249 (validation). This is a recorded exception,
    asserted so that a change is noticed, not a pass.
  - Skip, with a message, any part whose file is absent on the machine.
- **Check:** twelve invariant lines, all OK.

### T3 — Report schema 1.5

All in `scripts/run_inference.py` unless stated. Add the `1.5 (14 Oct 2026)` paragraph to the
schema history above `SCHEMA_VERSION`.

**a. Texts.**

| Text | Now | Change to |
|---|---|---|
| `CARIES_METHOD_CAVEATS["lesion-detector"]` | "beats … on 2 of 3 external cohorts (CariesXrays, Ningxia); on DENTEX a tie with both" | Adoption evidence was measured under the previous tooth detector. CariesXrays 1,200 is this detector's validation split. Ningxia is external and also informed adoption: +9.28 pp over the constant, pooled [+4.72, +13.73]. On DENTEX with the default tooth detector: F1 0.498 against the constant's 0.320; on lesion agreement not separated from the constant (−3.55 pp [−10.11, +2.64]) and 20.67 pp below the gate, which flags 2.4 times the teeth. 43.9% of the codes it flags are carious; no false-positive rate can be given. Figures: `docs/results/model_metrics.md` 74–121, 184–193 |
| Default profile, `label_and_validation` | "143 Tufts test radiographs that no model in this pipeline trained on" | "that this model did not train on (the severity head trained on two of them)". Add: the interval covers the sampling of radiographs, not the training run; pooled over three runs 18.3% (100 of 546); scored on crops cut at annotated tooth boxes, not at this pipeline's detections. Keep "abnormality" and "not as a periodontal" — the invariant looks for them |
| Default profile, `transfer` | A sentence on the severity grade "validated on 52 crops" | Remove it; the new key below carries the statement for every checkpoint |
| Default profile, `validation_split` | "severity: image-level, 32 training / 9 validation radiographs (unchanged)" | Add: its labels were a crop-contrast stand-in, not mask overlap |
| Previous checkpoint's profile | — | **Unchanged, verbatim.** A report made with `--bone-loss models/03…` must read as before |
| New `limitations.bone_severity_not_evaluated` | — | The Stage-4 severity head was trained on the standard deviation of crop grey levels, not on the expert mask; its classes are low, middle and high contrast; it has no test; withheld by default |
| New `limitations.caries_severity_not_evaluated` | — | The `caries` / `deep_caries` distinction comes from a head validated on 133 crops with no held-out test |
| Module docstring, Stage 4 paragraph | One run's 27.5% | Three runs; the severity head as above |

**b. Hashes and tags.** One table keyed by sha256 for the checkpoints that have no profile:
both numbering heads, the gate, the caries severity bundle, the lesion detector, the Stage-4
severity model. Copy each hash from its run summary, not from memory. Then in `run_pipeline`'s
`meta`:

- `fdi_head` gains `sha256`; its `tag` comes from the table. This fixes defect 1.
- `caries` gains `sha256` and `sha256_severity`; in gate mode it gains `tag_gate` (defect 2).
  The existing `tag` key stays, so nothing is renamed.
- `bone_loss` gains `sha256_severity`.
- A checkpoint with no entry gets `unregistered-<8 hex>`, as the detector does today.

**c. The Stage-4b grade [D1].**

- `src/classifiers.py`, `run_bone_loss`: when `severity` is `None`, skip the severity pass; a
  flagged tooth keeps `severity: None` and gains the flag `severity_withheld_contrast_proxy`.
  When a severity model is given, behaviour is as today plus the flag
  `severity_is_contrast_band_not_evaluated`.
- `run_pipeline(..., bone_severity_grade=False)` passes the model or `None`. CLI:
  `--bone-severity-grade`.
- `models.bone_loss` gains `severity_reported` (true or false).
- All seven checkpoints are still loaded, so every parameter total stands. The published
  seconds-per-image was measured with the grade computed; it is not re-measured and the log
  entry says so.
- `scripts/eval/bone_loss_v2_eval.py`, the `dentex` command: pass `bone_severity_grade=True`,
  so that if it is ever run again it reproduces its saved severity counts. One line. It is not
  run tomorrow.
- **If D1 is "label only":** skip the `None` branch and the CLI flag; keep the per-tooth flag
  and the texts.

**d. Overlay.** `draw_overlay`: `ABN` when the grade is withheld; `ABN-Sev` and so on only when
it was asked for.

**e. App.** `app.py`: two more lines under Limitations, one per new key. Nothing else; it calls
`run_pipeline` with the defaults.

**f. Docstrings.** `src/classifiers.py` lines 18, 37 and 378–379 (defect 4).

**g. Invariant.** Extend `inv_stage4_report_wording`: schema at least 1.5; the lesion-detector
caveat says "validation split" and no longer says "2 of 3 external"; the severity text says
"contrast"; `app.py` renders both new keys; a default report carries `severity_reported: false`.

**h. Tests.**

- `tests/test_classifiers.py`: `run_bone_loss` with two stub models returning fixed logits —
  withheld branch and graded branch.
- A new `tests/test_report.py`: `build_report` on empty stage outputs carries both new
  limitation keys and the schema string.

**i. Smoke, one fixed image, no cohort.**

| Run | Must hold |
|---|---|
| Default | Per-tooth output identical to the before-reference except `bone_loss.severity`, `severity_confidence` and `flags` |
| `--bone-severity-grade` | Per-tooth output identical to the before-reference except the added flag |
| `--bone-loss models/03…/bone_loss_resnet18_best.pth` | The two Stage-4 limitation texts byte-identical to a 1.4 report of that checkpoint |
| `--caries-method gate` | Runs; `tag_gate` present |
| Grep for callers of `run_pipeline(` and `run_bone_loss(` under `scripts/` and `src/` | Every caller still gets what it reads |

### T4 — Stale text

| File | Change |
|---|---|
| `docs/assets/hero.svg` lines 76–100, and the alt text at `README.md:3` | Five tiles today: 0.810, 58.3%, 0.9233, 4, 97.7 M. Three are stale as headlines and the parameter count is the previous detector's (now 95.3 M). Replace [D3]. Proposal: "89.3%" tooth recall, Tufts test · "63.5%" numbering end to end, Tufts test · "0.498" caries F1 against a constant's 0.320 · "4" external hospitals, unchanged · "95.3 M" parameters |
| `README.md` badges, lines 8–12 | 184 tests; PyTorch 2.2 with a link to the lock file; "YOLOv11l" |
| `README.md`, "127 numbers", four places | 191, after checking each one means the number checker |
| `README.md` Prerequisites, about line 591 | Point to the lock file |
| `README.md:300` and `docs/assets/domain-shift.svg` | The figures there (44.3, 28.8, 51.3, 40.1, 41.9) look like the gate under the previous detector. Check, then label them as such or redraw |
| `PROJECT_OVERVIEW.html` | A dated banner at the top: a 6 Sep snapshot; the detector, the Stage-4a model, the 0.923 and the severity head have all changed since; `transfer.md` is current. No rewrite |
| `Dockerfile` lines 1–11 | Remove the two mounts; every default checkpoint is in the repo. Say the image was last built on 7 Sep |
| `tests/README.md:1` | The real test count |
| `transfer.md` §8, fresh-clone checklist | Python and package versions as the lock file gives them |
| `models/18_bone_loss_radiograph_split/run_summary.txt` | "These files exist only on the macOS clone" is no longer true of seed 42 |
| `docs/README.md` line 4 | "periodontal bone loss per tooth" — say abnormality flag |

**Check:** grep the tracked tree for `0.9233`, `0.923`, `58.3%`, `0.810`; every hit left is
either history (the log, a superseded section, the previous checkpoint's profile) or the
manuscript, and the session file lists them.

### T5 — Lock file

- `requirements-lock.txt` at the root: the exact installed version of every package named in
  `requirements.txt`, generated from the environment with `importlib.metadata`, not typed. A
  header with the Python version, the platform, the date, and "produced every figure dated
  11–13 Oct 2026".
- Under it, as a comment: the other machine's stack, which produced the earlier figures
  (`transfer.md` §8), and that one row has differed between the two (0.294 and 0.300).
- `requirements.txt` and the Dockerfile are not changed: the image cannot be built on this
  machine.

### T6 — Safer loading (optional)

- `src/classifiers.py:108` and `src/fdi_head_inference.py:90`: `weights_only=True`.
- **Check:** `load_models()` loads all seven; the class-order invariant passes; the smoke
  report is identical. If any checkpoint refuses to load, revert that file and record which.
- The evaluation scripts that use the old setting are left alone.

### T7 — Input guards (optional)

| File | Guard | Test |
|---|---|---|
| `scripts/eval/validate_fdi_assignment_tufts.py`, `load_ufba_gt` | A class id outside 0–31, or a line too short to parse, raises | Two more in `tests/test_ufba_gt_loader.py` |
| Same file, CLI | `--aspect` without `--ufba` is an error instead of being ignored | — |
| `scripts/eval/bone_loss_v2_eval.py` lines 64, 68 | `zip(..., strict=True)` | — |
| `scripts/tufts/train_bone_loss_v2.py` line 8 | The docstring says no test radiograph is read; `check()` reads labels of a few. Correct the sentence | — |
| `scripts/eval/lesion_localization.py` 150, 272–278 | A missing exclusion file stops the run; an unreadable image is counted and printed | Only with the user's go: the council put this after submission |

None of these scripts is re-run.

### T8 — Close-out

- `docs/results/RESULTS_LOG.md`: one entry, 2026-10-14 — the decision on the grade, schema 1.5,
  the two pins, the split invariant, the six defects in the table above.
- `docs/results/model_metrics.md`: Stages 5–6 (schema, invariant count, test count).
- `docs/results/PAPER_MATERIAL.md`: a short §8.38.
- `transfer.md` §1–§4 and §8; `scripts/eval/README.md` (the new invariant);
  `README.md` stage table; a session file for 14 Oct.
- Final: the three commands; `git status`; hand over for commit.
- Tell the repo owner: the Docker image is then four changes behind.

### Phase C — the manuscript [D2]

If taken tomorrow, after T3: `paper/main.tex` lines 105, 384–388, 412–414, 1222, 1233, 1248
and 1545 and the `fig:boneloss` caption, with the paragraph in
`docs/paper/SUBMISSION_TODO.md` §1a row p; `scripts/verify_paper_numbers.py` claims changed in
the same commit; a tectonic build; the page count. Two to three hours.

### What this plan does not do, and why

| Flaw | Why it is not fixed |
|---|---|
| Stage 1: box mAP below the control; 621 boxes on no tooth; 66.6% recall unseen | Needs a retrained detector: refused, it orphans every Ningxia figure |
| Stage 1: the Kaggle set's licence | A person has to ask its authors |
| Stage 2: 63.5% Tufts, 44.5% unseen; uncoded teeth up from 26 to 65 | Two registered attempts were null; a reject option is parked behind its own pre-registration |
| Stage 3a: no untouched external cohort; no false-positive rate | No such cohort is on hand; the 164 DENTEX images hold no tooth labelled healthy |
| Stage 3b: no test | Its weights were trained on all 705 DENTEX images that carry its two labels; the only others are its own 133 validation crops |
| Stage 4a: 11–27.5% sensitivity; no pipeline-level or external figure | The only test split is spent; Ningxia is locked |
| Stage 4b: wrong labels | Retraining it is a fourth default change and was refused; it is withheld instead |
| One training run per model | A second seed cannot be scored anywhere clean |

These are disclosed in the paper, not repaired. None of tomorrow's tasks raises a metric.

### Done means

`pytest tests` passes with the new tests; every invariant holds, twelve of them; 191 manuscript
numbers still match; the four smoke runs hold; `git diff --stat` shows no whole-file
line-ending change; the log, the scoreboard and `transfer.md` say what ships.
