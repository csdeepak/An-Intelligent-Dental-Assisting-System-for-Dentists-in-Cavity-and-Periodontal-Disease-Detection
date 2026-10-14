# 2026-10-14e — Manuscript rows a–n corrected; Stage-4b retrain prepared up to its commit

**Session goal:** the user said "do them" for D7–D10 of `2026-10-14d-plan-by-stage.md`, and for
D10 asked whether Stage 4b could be retrained instead of removed — "if yes, proceed".

Run on the macOS clone, night of 14 Oct, after the user's commit `4cf9618`. Numbers in
`RESULTS_LOG` 2026-10-14c.

## What was done

- **D7 (S2–S5): `SUBMISSION_TODO.md` §1a rows a–i and l–n** corrected in the 15-page
  `paper/main.tex`, 25 anchored edits; 13 new claims in `scripts/verify_paper_numbers.py`, each
  read from `outputs/stage1_switch/stage1_switch_results.json`, and two assertions. 201 claims,
  no drift; 15 pages; 0 undefined references.
- **D8 (S9):** one clause — 1.70 s/image was measured with the severity grade computed.
- **D9:** README sections C1–C4 left for after the cut, as defaulted.
- **D10, prepared not run:** `outputs/bone_loss_eval/v3_severity/PRE_REGISTRATION.md`,
  `scripts/tufts/train_bone_severity_v2.py`, `scripts/eval/bone_severity_v2_eval.py`,
  `tests/test_bone_severity_v2.py` (3 tests), a `.gitignore` line for the new weights. `check`
  H1–H3 pass. The scoring path was rehearsed on validation positives with the shipped head, which
  produced the one new number of the night: macro-F1 0.240, kappa −0.145 against the true bands.
- Logs: `RESULTS_LOG` 2026-10-14c; `model_metrics.md` Stage 4b; `PAPER_MATERIAL.md` §8.39;
  `SUBMISSION_TODO.md` §1a note; `transfer.md` top note, §1, §3, §8; README and `tests/README.md`
  counts (197 tests, 201 claims).

## Decisions made

- **Row a's count is "at least 25".** 25 Ningxia scoring outputs (plus a smoke run) exist on this
  clone; only 20 are in git, and the other machine was not checked. "At least" is the most that
  can be said without a ledger; the list is in the log.
- **The new numbers in the text are asserted from the artefact, not typed.** The intervals for
  row b are stated in words ("both intervals excluding zero") and asserted in the checker.
- **"Image-blind" is kept for the F1 constant only**, following row m. Under lesion agreement the
  text now calls it the constant, placed by the pipeline's front end.
- **D10: retrain, but not before the protocol is committed.** The Stage-4a precedent was
  criticised for committing its scripts after the test pass. Training now would repeat that.
  Committing the protocol is also the decision owner's explicit authorisation for one more pass
  over the Tufts test split, which the 12–13 Oct councils had frozen.
- **The retrain's label is named for what it is**: an extent band of an expert-marked abnormality.
  The protocol fixes, before any result, that the report keeps the grade withheld by default and
  that eligibility does not make it a severity.
- **The jitter is seeded per run**, fixing the shared-jitter flaw found in Stage 4a.
- **The rehearsal used validation data and the shipped head only**, so the test split stays
  untouched by any Stage-4b model until `score`.

## Open questions

- Whether the mentor accepts a fourth model change in four days, even one that is registered.
- What the report should call the bands if a retrained head is ever adopted (the class names are
  still Mild / Moderate / Severe). That is part of the adoption decision, not of this protocol.

## Next steps

1. The user commits: `outputs/bone_loss_eval/v3_severity/PRE_REGISTRATION.md`,
   `scripts/tufts/train_bone_severity_v2.py`, `scripts/eval/bone_severity_v2_eval.py`,
   `tests/test_bone_severity_v2.py`, `.gitignore`, and the manuscript and documentation changes
   (`paper/main.tex`, `paper/main.pdf`, `scripts/verify_paper_numbers.py`, `README.md`,
   `tests/README.md`, `transfer.md`, `docs/results/*`, `docs/paper/SUBMISSION_TODO.md`, this file).
2. Then: `train --seed 42`, `--seed 43`, `--seed 44` (MPS, roughly 10–30 min each), then
   `bone_severity_v2_eval.py score` once.
3. Then: `RESULTS_LOG` entry, `model_metrics.md` Stage 4b, `PAPER_MATERIAL.md`, the manuscript's
   Stage-4b sentence; an adoption decision recorded separately if eligible.
