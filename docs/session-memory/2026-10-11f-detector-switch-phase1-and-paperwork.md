# 2026-10-11f — Detector switch: the safety fixes, the decision record and the pre-registration

**Session goal:** start the Stage-1 detector switch the user confirmed (arm3c): do Phase 1 of the
plan in `2026-10-11e`, and write the Phase 2 paperwork for the user to commit.

Run on the macOS clone. **The default detector is unchanged and no part of the re-measurement
matrix has been run.**

## What was done

### Phase 1 — code, with the default still `models/11`

1. `scripts/run_inference.py`: a `DETECTOR_PROFILES` table keyed by the weights' sha256 replaces
   the module constants as the source of the report's detector tag and its two accuracy figures.
   A detector with no entry is tagged `unregistered-<sha>` and gets no accuracy claim.
   `models.detector` gains `sha256`; schema 1.2 → 1.3. The console note reads the figure from the
   report.
2. `scripts/eval/c1_vlm_baseline.py`: `--detector` for the pipeline arm, defaulting to a path
   pinned in that file rather than to `DEF_DETECTOR`, and the arm file records the detector and
   its hash.
3. `scripts/eval/cariesxrays_external.py`, `scripts/eval/validate_fdi_assignment.py`: record
   which detector produced the output.
4. `scripts/count_model_params.py`: `--stage1` and `--out`; refuses to write a non-default count
   over the published file.
5. `models/15_detector_multicorpus_leverA/run_summary.txt`: the three checkpoints' full hashes
   appended (it held prefixes). `scripts/eval/verify_invariants.py`: arm3c pinned; a pin with no
   recorded hash now fails; new invariant "default detector registered".

Verified: previous-commit code against this code on one Tufts and one DENTEX image — identical
`teeth`, `summary` and `limitations`, differing only in `schema_version`, the new `sha256` key
and the timestamp. arm3c passed explicitly on a Tufts training image — `unregistered-5d301f13`,
null figures. `pytest` 174; paper numbers 127 of 127; all invariants hold.

### Phase 2 — paperwork, written and left for the user to commit

- `RESULTS_LOG` 2026-10-11f, the decision record: who decided, that both ABLATION verdicts stand
  and neither guard is claimed met, that it is a stronger override than 27 Aug's, that a council
  advised against it and the owner and mentor were not asked, what is given up, and why arm3c.
- `outputs/stage1_switch/PRE_REGISTRATION.md`: what is already seen, the eight-row matrix with a
  same-machine control before every arm3c run, the gates, the one stop rule, the wording rules,
  and what is forbidden. `.gitignore` whitelists the directory.

## Decisions made

- **Did not commit the weights or touch `.gitignore` for them yet.** The plan put that in
  Phase 1. A 51 MB file stays in history once pushed, and the stop rule may still fire, so it
  moves to the flip. The hash pin works on the local file without it.
- **The FDI-set-F1 harness keeps `models/11` as its own default** after the pipeline default
  changes. It is the reproducibility harness for a published number; the same reasoning as its
  `--caries-method gate` default.
- **`models/06` was not given a profile.** Its hash is not recorded anywhere, so there is nothing
  to say the file on this disk is the original. Its reports are tagged unregistered, which is
  true.
- **No guard added in `app.py` for a null accuracy figure.** The app always loads the default,
  and an invariant now forbids a default without figures.
- **The licence fallback is described, not made a rule.** The user said "continue with arm3c"
  and did not answer the suggestion of pre-declaring `models/13` as a fallback. The decision
  record says a detector trained without the Kaggle set would be a new decision.
- **The stop rule is about the caries path only.** It is what the paper is about, and it is the
  one thing a better tooth detector could plausibly harm that nobody has measured.

## Open questions

- Has the repo owner been told? The pre-registration says the Ningxia rows run after he is, or
  the results entry says he was not.
- The Kaggle licence.
- Whether a 1.5 pp tolerance for references produced on the other machine is right. It is fixed
  in advance either way.
- `scripts/eval/README.md` still says the invariant script has seven checks; it has eleven.

## Next steps

1. The user reads the decision record and the pre-registration, edits anything, and commits:
   Phase 1 code as one commit, the paperwork as another.
2. Run rows A to E and H, each control first.
3. Run rows F and G, last and once.
4. Apply S1; if it does not fire, flip the default, register arm3c's profile, commit the weights.
5. Log, then hand the manuscript and Docker to the other machine.
