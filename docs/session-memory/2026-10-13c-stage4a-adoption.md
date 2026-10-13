# 2026-10-13c — The retrained Stage-4a model adopted as the pipeline default

**Session goal:** the user committed and pushed the retraining result and said: adopt it as
default.

Run on the macOS clone, night of 13 Oct. Numbers are in `RESULTS_LOG` 2026-10-13c.

## What was done

1. **Recorded the decision before acting on it.** Amendment 1 of
   `outputs/bone_loss_eval/v2_retrain/PRE_REGISTRATION.md`, committed by me at `9df2f7b`, same
   terms as before: what adoption consists of, what it does not give, and one re-measurement —
   the Stage-4 firing rate on DENTEX, the only pipeline-level figure that a change of Stage 4a
   makes stale and that can still be measured.
2. **`scripts/run_inference.py`.** `DEF_BONE_LOSS` now points at
   `models/18_bone_loss_radiograph_split/seed42_best.pth`. A `BONE_LOSS_PROFILES` table, keyed by
   the sha256 of the binary weights, supplies the tag, the two limitation texts and the two
   model-block texts — the arrangement the detector has had since 11 Oct. The previous
   checkpoint's four strings were moved into its profile verbatim. An unregistered checkpoint
   gets no figure. Schema 1.4.
3. **The pins.** `verify_invariants.py` gained the new checkpoint beside the old one, and its
   report-wording check was rewritten for the new arrangement: every profile must say "not a
   periodontal finding", the previous one must still say its 0.923 is not held out, and the
   default must have a profile that the report actually carries.
   `count_model_params.py` and `param_counts.json` name the new file; every total is unchanged.
4. **`.gitignore`**: an exception for `seed42_best.pth`; seeds 43 and 44 stay ignored.
5. **DENTEX firing, registered, control first.** Previous checkpoint: 34 of 4,512 teeth,
   exactly as on 11 Oct. New default: 274 of 4,512, 6.1%. Every per-tooth field outside
   `bone_loss` identical on all 164 images.
6. **Smoke tests.** The pipeline runs with the default and, with `--bone-loss`, with the
   previous checkpoint; the second reproduces the per-tooth output and the limitation text it
   gave before the change. `app.py` compiles; it renders the limitation text from the report, so
   it follows the weights without a change of its own.
7. **Documents:** `RESULTS_LOG`, `model_metrics.md`, `PAPER_MATERIAL.md` §8.36, `transfer.md`
   (§2.1, §2.5, §3, §4, §8), `SUBMISSION_TODO.md`, the root README's stage and results rows,
   `models/README.md`, both run summaries, `CLAUDE.md` (rule 4 and §6), `scripts/eval/README.md`.

184 tests pass, all invariants hold, 191 manuscript numbers still match.

Committed by me: `9df2f7b` only. **The weight file is not committed.** That is the user's.

## Decisions made

- **The report follows the weights, rather than the text being rewritten in place.** A flag
  that lets the previous checkpoint run must not let it run under the new one's figures. The
  detector's profile table already solved this; the same shape was reused.
- **The previous checkpoint's text was moved, not edited.** A report made with it today reads
  as it did yesterday, which the smoke test confirms.
- **The tag drops "bone-loss".** `abnormality-flag-resnet18-radiograph-split-v2.0`. The field
  names in the report keep `bone_loss`, because consumers depend on them; the tag was the one
  place the name could be corrected at no cost.
- **DENTEX was re-measured; Ningxia was not.** One is a development corpus that can be re-run.
  The other is locked, and the new model has no figure there. Every document that carries the
  2.17% now says whose it is.
- **The severity model's behaviour is reported, not fixed.** It grades eight times as many
  DENTEX teeth as before and calls 95% of them Moderate or Severe, on the strength of 52
  validation crops. I put that in the report's own text and in the log, and did not hide the
  grade from the overlay: that is a change to what the demo shows, and nobody asked for it.
- **The manuscript was not touched.** It describes the previous model on this branch. The
  rewritten paragraph is in the submission list for the authors.
- **A failing invariant was rewritten, not weakened.** It demanded the words "not a held-out"
  of every report. For the new default that statement would be false. The check now asks for
  what stays true of every checkpoint, and keeps the old demand for the old checkpoint.

## Open questions

- **Should the overlay and the app keep printing a severity grade?** The model behind it has no
  held-out test and now speaks far more often.
- Does the mentor accept a second change of default made without her? Neither she nor the repo
  owner has been told of this one, the detector switch, or the held-out result.
- A regularised recipe: every run memorised. Unregistered, not started.
- BRAR, for a periodontal label. Not started.
- Carried over: the grading date; the Tufts Drive folder; the Kaggle licence.

## Next steps

1. **The user commits and pushes, including `models/18_bone_loss_radiograph_split/seed42_best.pth`
   (44.8 MB).** Without it a fresh clone cannot run the default pipeline. `9df2f7b` goes too.
2. Mentor and repo owner: the held-out 7.6%, the retraining, the new default.
3. The decision on the severity grade.
4. The six-page draft, with the rewritten Stage-4 paragraph.
5. Windows machine: pull, check the default runs there, rebuild the Docker image — it is three
   changes behind — and the pdfLaTeX build.
