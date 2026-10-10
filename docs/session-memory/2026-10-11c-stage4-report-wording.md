# 2026-10-11c — The report and the demo stop calling Stage 4 a periodontal finding

**Session goal:** item 6 of the implementation phase (`transfer.md` §3): make the shipped
system's own output match what the 10 Oct audit found about the bone-loss branch.

Run on the macOS clone. No model, weight, threshold or default changed.

## What was done

1. **Read every place the system describes Stage 4**: the report's `limitations` block, the
   overlay label and the console summary in `scripts/run_inference.py`; the metric, the table
   column and the Limitations panel in `app.py`; the docstring of `run_bone_loss`. Checked for
   readers of the affected keys — none outside `run_inference.py` itself.
2. **Changed the wording**, additively:
   - `limitations.bone_loss_label_and_validation` — new: the field is an abnormality-proximity
     flag, not a periodontal finding; the in-domain score is not held out.
   - `limitations.bone_loss_domain_shift` — same key, corrected text: it no longer asserts
     domain shift as the cause.
   - `models.bone_loss.label_definition` and `.validation_split` — new.
   - Overlay `BL-…` → `ABN-…`; console "bone-loss-positive" → "stage-4 abnormality flags".
   - App: metric "Stage-4 flags" with a help note; column "Stage 4 flag" showing flagged / —;
     two Stage-4 bullets in the Limitations panel.
   - `SCHEMA_VERSION` `opg-report/1.1` → `1.2`.
3. **Added one invariant**, "Stage-4 report wording", to `scripts/eval/verify_invariants.py`:
   the caveat is in every report and `app.py` renders it.
4. **Verified:**
   - Previous commit's code against the changed code on the same Tufts radiograph (196): the
     `teeth` list and the `summary` are identical; one limitation key added, none removed.
   - The overlay was looked at: flagged teeth read `ABN-Mod`, `ABN-Sev`.
   - The app was driven headlessly through an upload with Streamlit's `AppTest`: no exception,
     new labels present, both caveats rendered.
   - The new invariant fails on the previous commit's code and passes on this one.
   - `pytest` 174 passed; `verify_paper_numbers.py` 127 of 127; invariants hold.
5. **Logged:** `RESULTS_LOG` 2026-10-11b; `model_metrics.md` (Stages 5–6 row);
   `PAPER_MATERIAL.md` §8.28 update, which also records the Stage-4b split audit;
   `transfer.md` §3; root `README.md`.

## Decisions made

- **Field names stay.** `bone_loss`, `bone_loss_positive` and the `"bone_loss"` finding value
  are read by `tests/test_classifiers.py` and `scripts/eval/ningxia_external.py`. Renaming them
  would buy accuracy in a key name at the cost of breaking consumers; the caveat carries the
  meaning instead, and an invariant now guards the caveat.
- **Keep `bone_loss_domain_shift` as a key and fix its text**, rather than removing it. A
  removed key breaks a 1.1 consumer; a corrected one does not.
- **The label says "abnormality", not "periapical".** The audit of 10 Oct is a keyword reading
  of expert free text. "Abnormality mask" is what the training rule literally used; anything
  narrower would be a claim nobody has tested.
- **The check went into `verify_invariants.py`, not a new pytest file**, for the same reason as
  earlier today: "174 tests" is quoted in six places, one of them the manuscript.
- **Did not fix two adjacent things I noticed**: the report's `interpretation` text says
  "roughly half the codes" will be wrong where the measured figure is 42%; and the app's
  "Caries conf (cal.)" column is always empty under the default caries method. Neither is part
  of this change.

## Open questions

- **Will the guide accept a relabelled Stage 4 under a title that names periodontal disease?**
  The system now says plainly what the branch is. Whether that satisfies the capstone review is
  not an engineering question, and a written answer before the review is worth having.
- Does the review-panel deck (`docs/REVIEW3_PANEL.html`) need a correction for what it told the
  panel about bone loss? Reported by a council member on 11 Oct, not checked.
- One image is an anecdote, and radiograph 196 is one of Stage 4a's own training images. Its
  five flags are second and third molars, and the expert's description of it is a widened
  follicular space at three third molars — what the label audit predicts, on a tooth the model
  has seen. A count over the never-used Tufts radiographs would say how general that is; it is
  the deferred leak-free measurement.

## Next steps

1. Commit this session's files.
2. **Rebuild the Docker image** on the machine with Docker running; the 7 Sep image carries the
   old wording and emits `opg-report/1.1`.
3. The implementation phase is complete. Next is writing: the manuscript change list in
   `PAPER_MATERIAL.md` §8.28, §8.29 and §9, and the six-page caries-only cut.
4. Mentor meeting: venue, authors, the bone-loss branch, the two compliance items.
