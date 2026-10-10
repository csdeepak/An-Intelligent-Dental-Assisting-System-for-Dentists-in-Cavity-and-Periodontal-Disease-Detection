# 2026-10-11 — Implementation-phase council: what is left to build before writing

**Session goal:** decide what implementation and improvement work is left, and the smallest set
to finish first and fast, before writing and submission.

Run on the macOS clone, late 10 Oct into 11 Oct. No model was trained or evaluated and nothing
was committed. It follows `2026-10-10-state-review-council.md`, whose documentation edits are
still uncommitted in the same working tree.

## What was done

### 1. Facts first

- Audited the Stage-4b (severity) split, which the 10 Oct audit had left open: **it is
  image-level** — 32 training radiographs, 9 validation, none shared
  (`data/tufts/severity_dataset/metadata/`). Its label source is the same expert abnormality
  masks as Stage 4a.
- Counted the leak-free pool for Stage 4a on this Mac: `_repo_archive/datasets_workspace/Expert/mask/`
  holds 1,000 masks; the Stage-4a build used 145 radiographs (49 with a non-empty mask). About
  **290 radiographs with a non-empty mask and 565 with an empty one were never used**. Non-empty
  was tested as `max > 0` on JPEG masks, so 290 may be slightly high.
- The pipeline's own output repeats the withdrawn reading: `scripts/run_inference.py` l.268–273
  writes a `bone_loss_domain_shift` caveat; the overlay prints `BL-…`; `app.py` shows a
  "Bone loss" column and its Limitations panel renders no Stage-4 caveat at all.
- Saved outputs allow two analyses with no inference: the three Ningxia Lever B files carry 337
  `per_image` rows with `split`; `outputs/c1_vlm/arm_pipeline.json` carries per-image FDI sets
  for all 164 images. `scripts/eval/bootstrap_ci.py` l.200–212 already does a per-hospital
  cluster bootstrap for the gate.
- The saved Lever B outputs carry no per-flag detector confidence.
- No FDI-set F1 exists anywhere for the adopted lesion detector. `c1_vlm_baseline.py --arm
  pipeline` has no caries-method switch, and `outputs/c1_vlm/c1_comparison.json` never mentions
  the detector. Table I of the manuscript scores the retired gate.

### 2. The council

Three independent read-only members (`Plan` agents). All three seats failed once on the account's
session limit and were re-seated after it reset.

| Seat | Lens | Model |
|---|---|---|
| 1 | Delivery minimalist | Sonnet |
| 2 | Scientific value | Opus |
| 3 | Capstone and engineering integrity | Opus |

**Consensus**

| Question | Verdict |
|---|---|
| Bone-loss branch | Keep it running, relabel it honestly, cut it from the paper. No new experiment. 3 of 3. |
| Intervals on the F1 gap and per hospital | Do first. They are the only items that block writing. 3 of 3. |
| Retrain Stage 4, new periodontal corpus, numbering or detector work | Refuse. 3 of 3. |
| `--tag` / `--out` fix | Defer to before the next Ningxia run. 3 of 3. |
| Lesion-detector calibration on DENTEX | Not now. Seat 2: not well-defined there, because unmatched flags are not known false positives. |

**Dissent**

| Point | Positions | Chair |
|---|---|---|
| Split-grouping invariant | Seat 1: refuse, it pins a known defect. Seat 3: do it, 1.5 h, as a recorded known violation. | Deferred. It protects a retrain nobody is doing. |
| Leak-free score of the frozen Stage 4a | Seat 1: refuse. Seats 2 and 3: after submission, journal and capstone value only. | After submission. |
| The detector's own row in Table I | Raised only by seat 2. | Accepted and added to the do-first list after checking that no such number exists. |
| Time box | 1.5 days, under 1 day of science, 8 hours plus the analyses. | Two working days, because the Table I run was added. |

### 3. What the chair verified

- The app's Limitations panel renders three caveats and none for Stage 4 (`app.py` l.146–153).
- `.gitignore` l.93 ignores `outputs/*` with per-directory exceptions; `outputs/lever_b_eval/`
  and `outputs/c1_vlm/` are whitelisted, so new artefacts belong there.
- The per-hospital bootstrap precedent exists (`bootstrap_ci.py` l.200–212).
- 0.923 appears on seven lines of `README.md` and in three SVGs under `docs/assets/`.

Reported by a member and not verified: seat 3's line-by-line list for the wording change; that
no test pins the report strings; that cutting bone loss from the paper retires three of the 127
number checks; that the review panel was told the withdrawn bone-loss story
(`docs/REVIEW3_PANEL.html`); seat 2's count of DENTEX periapical-lesion teeth.

## Decisions made

- **The implementation phase is six items and two working days** (`transfer.md` §3). Everything
  on it is independent of the venue, so nothing is wasted whichever conference is chosen.
- **Per-hospital analysis is estimation, not a test.** The point estimates were seen on 10 Oct,
  so the pre-registration sets no bar and the pooled Lever B verdict is not reopened. "Wins at k
  of 4" from point estimates is not to be written.
- **Add the detector's row to the headline table.** A paper whose first table scores a system
  the pipeline no longer ships invites the obvious question. The run is made once and printed
  whichever way it falls.
- **Do not rename the `bone_loss` keys.** A rename breaks `tests/test_classifiers.py` and
  `ningxia_external.py`. The change is wording plus additive fields, with a schema bump so a
  stale container is detectable.
- **No retrain of Stage 4.** A clean split would validate an abnormality label cleanly, cost
  two to three days of re-pinning, and leave the title gap where it is.

## Open questions

- What the final capstone review requires of the implementation, and whether the guide accepts
  the relabelled Stage 4 under a title that names periodontal disease. A written agreement is
  worth having before the review.
- LaTeX on this Mac: install it, or use Overleaf. Both are the user's decision — one adds a
  dependency, the other uploads the manuscript to a cloud service.
- Whether the Table I scorer accepts lesion-detector output unchanged.
- Whether the panel deck needs a correction slide for what it said about bone loss.

## Next steps

1. Commit the 10 Oct documentation edits (needs the user's go).
2. Write and commit one pre-registration for the three measurements.
3. Run the F1-gap interval, then the per-hospital intervals, from saved outputs. Log both.
4. Add the caries-method switch to the pipeline arm, run the detector once over the 164 images,
   score it, log it.
5. Change the Stage-4 wording in the report, overlay and app; add one test for the report
   builder; bump the schema to 1.2; regenerate one demo report.
6. Start the six-page caries-only cut.
