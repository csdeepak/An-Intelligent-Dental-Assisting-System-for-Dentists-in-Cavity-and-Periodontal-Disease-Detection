# 2026-10-14b — Implementation of the 14 Oct plan, with the decision owner's defaults

**Session goal:** implement `2026-10-14-research-audit-and-plan.md`; the user answered "go with
defaults" for D1–D6 after committing the plan (`8e60f96`).

Run on the macOS clone. No model trained, no cohort scored, nothing re-run on a test split.
Numbers are in `RESULTS_LOG` 2026-10-14; this file is the narrative.

## What was done

In the plan's order. Every task ended with the three checks; the last run: **194 passed, 12
invariants hold, 191 paper numbers, no drift**.

| Task | What changed | Check |
|---|---|---|
| T0 | Baseline 184 / 11 / 191. The 13 Oct smoke image has 3 teeth and no Stage-4 flag, so the before-reference became DENTEX `test_185` (24 teeth, 10 flags, 5 caries findings), four modes | — |
| T1 | `hash_from_summary` matches by basename; `models/16` and `models/07` pinned; two tests | ten files pinned; 186 tests |
| V1 | `scripts/eval/tufts_split_near_duplicates.py` (reuses `dhash`, `NEAR_DUP_BITS`) → `outputs/eda_tufts/near_duplicates.json`, tracked through a `.gitignore` exception | **found 248 (test) / 1017 (train) at 7 bits** — see Decisions |
| T2 | Invariant "Tufts split disjoint": 700/150/150 unique; Stage-4a test rows 143, all test; the severity head meets the test split at 149, 192, 249 only; no unexplained near-duplicate | twelve invariants |
| V2 | `tests/test_crop_parity.py`: same geometry asserted; interior difference ≤ 4 grey levels | measured first: ≤ 3 inside, up to 255 in columns 0–1 (cv2 resize on 3 channels); 0 of 503 flag decisions change |
| T3 | Schema 1.5 in `scripts/run_inference.py`, `src/classifiers.py`, `app.py`: corrected caveat and Stage-4a text (W1 inside), two new limitation keys, sha256 and tag of every checkpoint, `--bone-severity-grade` (off), overlay colours (F1), docstrings; invariant extended; 4 tests | smoke: only the severity fields differ (default) or one flag (graded); previous checkpoint's texts byte-identical; `tag_gate` in gate mode; numbering-head tag now v2.0 |
| T5 | `requirements-lock.txt`, generated with `importlib.metadata` | — |
| T4 + F7 | Banner tiles and subtitle, README tagline, alt texts, badges, "127" → "191" ×4, Prerequisites; `pipeline.svg` corrected in place (text, `aria-label`, `<desc>`); four infographics unlinked, files kept; `PROJECT_OVERVIEW.html` banner; Dockerfile header; `docs/README.md`; `models/18` summary | both SVGs measured in the browser pane: no text over a box edge or another text after shortening one tile label |
| F3 | Fig. 1: gate hatched, one order in every panel (asserted), labels with backdrops, constant `#e15759` | values unchanged; greyscale render: default 62, constant 128, VLMs 152 grey levels |
| W2 | Two sentences in `SUBMISSION_TODO.md` row p | — |
| T6 | `weights_only=True` in both serving loaders | all seven checkpoints load; report identical |
| T7 | UFBA loader raises on a short line or a class outside 0–31; `--aspect` without `--ufba` is an error; `zip(strict=True)` ×2; `train_bone_loss_v2.py` docstring corrected | all 11,591 real label lines pass; 2 tests |
| T8 | `RESULTS_LOG` 2026-10-14, `model_metrics.md` (4a, 4b, 5–6), `PAPER_MATERIAL.md` §8.38 + one §9 item, `transfer.md` (top note, §1, §2.1, §3, §4, §8), `scripts/eval/README.md`, README stage rows | — |

## Decisions made

- **D1–D6 at their defaults**, by the decision owner, recorded in §6.2 of the plan file before
  the first edit.
- **The near-duplicate is disclosed with a bound, not re-analysed** (the decision owner, asked
  when V1 found it). 248 holds 27 of 3,892 Stage-4a test teeth and none of the 182 positives, so
  no sensitivity moves; specificity, PPV and the Tufts Stage-1/2 test figures include it as 1 of
  143. A re-analysis would put more numbers into a six-page paper for a radiograph with no
  positive tooth.
- **The crop-path difference is not "fixed".** Every pipeline-level figure was measured on the
  serving path, and the difference changes no decision on 503 teeth. Changing either path now
  would separate the code from its numbers.
- **The before-reference image was changed** from the 13 Oct one: a smoke run that exercises no
  Stage-4 flag cannot show what the D1 change does.
- **The README's narrative sections C1–C4 were not rewritten.** Their figures are unlinked and a
  note says the text describes the earlier configuration; rewriting the README belongs after the
  six-page cut, which decides what the paper says.
- **The constant's colour in Fig. 1 was changed** (`#c1121f` → `#e15759`): the greyscale check in
  the plan failed for the default-vs-constant pair, which printed as the same grey. Every value is
  unchanged; the paper's caption mentions no colour.

## Corrections to the audit

- **The colour-blindness argument for the overlay was overstated** (plan §1 item 3, §2 row 10).
  Simulated, the old red/orange pair stays distinguishable (ΔE 41 under deuteranopia). The change
  stands on meaning — red for "could not assess" — not legibility. The plan file is not edited
  after implementation started; the correction is here and in `RESULTS_LOG` 2026-10-14.
- **The interior crop difference is 3 grey levels, not 13.** A number in an intermediate step of
  this session included column 0; corrected before anything was written down.

## Open questions

- The mentor and the repo owner have still not been told of the detector switch (11 Oct), the
  Stage-4a change (13 Oct), the withheld grade or the 248/1017 pair (14 Oct).
- Whether Tufts holds more same-patient pairs that a difference hash cannot see (different
  exposures, crops). The gap from 7 to 33 bits suggests not; an embedding-based check would need a
  new dependency.
- Seconds per image were not re-measured; the README still quotes 2.39 s from the previous front
  end on the other machine.

## Next steps

1. The user commits. Suggested commits, explicit paths: `fix:` T1 + T2 + V1 (invariants, the
   scan, its JSON, `.gitignore`); `test:` V2; `feat:` T3 (schema 1.5, `app.py`, classifiers, the
   eval one-liner, tests); `fix:` T6 + T7; `docs:` T4 + F7 + W2 + T8 + the lock file + Fig. 1 + this
   file.
2. Tell the mentor and the repo owner (the four items above); the Docker image is three default
   changes behind (11, 13, 14 Oct).
3. The six-page cut, then Phase C and F2 (Stage-4 manuscript text, Fig. 5, its
   `verify_paper_numbers.py` claims), then F4–F6 for the figures that survive.
4. Stop date for code: 20 Oct.
