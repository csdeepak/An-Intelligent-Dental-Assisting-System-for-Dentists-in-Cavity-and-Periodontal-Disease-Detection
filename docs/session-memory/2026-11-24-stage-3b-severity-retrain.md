# 2026-11-24 — the panel-review video read, and Stage 3b retrained and tested once

**Session goal:** understand what the panel-review video explains. Then, on the decision owner's
go, give the Stage-3b caries-severity head its first held-out test under a pre-registration.

This ran on the macOS clone, in the git worktree `stage-4b-retrain-preflight-6d676a` (branch
`claude/video-panel-review-script-745e1b`, cut from `main` at `5e19db3`). Nothing was pushed.
No Ningxia data was read.

## What was done

1. **Read the panel-review video** on `origin/video/panel-review` (`a6188d0`, 14 Oct; 16 commits
   behind `main`):
   - `brag-output/work/narration.json` (21 scenes), `brag-plan.md`, and session note `14h`.
   - Told the user three things are stale:
     - scene 19's claim and test counts (207 / 204);
     - schema 1.5;
     - scene 21's "six-page paper".
2. **Answered "should I worry about 'validated, never tested'?"**
   - Not a publication blocker: the paper makes no claim on Stage 3b (Table 3, Limitations).
   - A likely panel question.
   - Found that a clean test was possible from data already on disk:
     `data/dentex/crops_v2/phase2`, 395 test crops.
3. **Pre-registered** (`cf3090a`): `outputs/caries_severity_v2/PRE_REGISTRATION.md` and
   `scripts/dentex/train_caries_severity_v2.py`, plus `check_summary.json` and `.gitignore`
   rules (weights in `models/20` local; protocol and outputs tracked).
   - The harness checks (H1–H5) pass.
   - H4's first version failed on single-hash *candidates*, not duplicates. It was changed to
     fail on an MD5 copy or a pair close under both hashes. The 17 candidates were inspected
     side by side, and all are different patients. This was fixed before the commit and is
     recorded in protocol §3–§4.
4. **Trained** seeds 42, 43 and 44 on MPS: validation macro-F1 0.7727, 0.7628 and 0.7825. The
   histories and logs were frozen in `f8bc016` before the test pass.
5. **One test pass:**
   - Seed 42 test macro-F1 0.772 [0.711, 0.828], against 0.483 for the strongest prior.
     **Eligible.**
   - On extern50, `models/07` scored 0.738 under the pipeline's argmax, not its notebook's 0.77.
   - Docs updated: `RESULTS_LOG` 2026-11-24, `model_metrics.md`, `PAPER_MATERIAL.md` §8.46,
     `transfer.md` §1 and §4, `research_paper/open_issues.md` item 10, `models/README.md`, and
     `models/20_caries_severity_v2/run_summary.txt`.

6. **Adopted seed 42 as `DEF_CARIES_SEVERITY`** on the user's "Yes, adopt seed 42"
   (`RESULTS_LOG` 2026-11-24b).
   - **Pipeline:** hash pin, tag, and a per-weights `CARIES_SEVERITY_TEXTS`; schema 1.7.
   - **Checks and tests:** new pin pair, class order and text checks in `verify_invariants.py`;
     tests updated; golden Tufts report regenerated (2 teeth caries → deep caries);
     `.gitignore` exception so the 44.8 MB weights are committed.
   - **Parity:** 4 images × 2 modes. No flag, summary or non-severity field changed; 10 of 40
     flagged teeth changed grade (`outputs/caries_severity_v2/adoption_parity.json`).
   - **`research_paper/`:** source edited and regenerated, with CRLF restored to match the
     Windows-built files. The number tracer was given the new sources. The PDFs were not
     rebuilt (no pdfLaTeX).
   - **Results:** `pytest` 214 passed; invariants all hold.

## Decisions made

- **The report key `caries_severity_not_evaluated` was kept.** Its text now follows the weights
  loaded. The grade as the pipeline makes it (detector boxes, flagged teeth) is still untested
  for every checkpoint, so the key name stays true and no consumer breaks.
- **Figure 4's saved report (Windows, old head) was left as it is.** Its grades are unchanged
  under the new head. The text names both severity scores rather than mixing a Mac re-run into
  the figure's numbers.
- **`paper/main.tex` and `lesion_localization.py`'s own copy of the old default were not
  touched.** The first is the superseded manuscript. The second reproduces saved numbers, and
  the grade enters none of them.

- **The shipped head is not the subject, because it cannot be.** It trained on all 705 DENTEX
  training radiographs, the test split included. Scoring it there would be scoring training
  data, so it is compared only on extern50, where it was tuned (biased in its favour).
- **ImageNet initialisation, not a caries-gate backbone.** The legacy gate in `models/07` trained
  on the test radiographs too. ImageNet removes the question.
- **Stage 4a/4b's recipe, imported rather than redesigned.** It is one recipe already used twice
  in this repo, and fixing it in advance avoids a recipe search on validation.
- **Three priors, all fixed in advance:** majority, tooth majority, and a class-balanced tooth
  rate. For an imbalanced binary label the majority prior is a trivially weak floor; the tooth
  rate is the strongest image-blind arm designed in advance. The rule requires beating all
  three.
- **No default changed.** The protocol says eligibility only permits proposing a swap. The swap
  changes every report and the demo, so it is the owner's call (`transfer.md` §4).
- **The 0.738 vs 0.77 gap is logged as an observation, not a correction.** Its cause is
  unknown, and the 0.77 is still what the notebook printed.

## Open questions

- **Adoption was decided later this session (item 6).** The mentor has not been told.
- **Why does `models/07` score 0.738, not 0.77, on the regenerated extern50 crops?** Candidates
  are crop regeneration (21k verified 4 sample crops; 3 bit-identical, 1 off by ±1) and the
  notebook's evaluation preprocessing. Not investigated.
- **Severity on detector boxes and flagged teeth is untested.** The test used annotation boxes of
  truly carious teeth. No DENTEX image set with deep-caries labels has been run through the
  pipeline.
- **Should the video's scene 10 change?** "Validated, never tested" stays true of the shipped
  head. It could add "a retrained head tested at 0.77".

## Next steps

1. On Windows: rebuild `research_paper/final_research_paper.pdf` and the `turnitin` PDF with
   pdfLaTeX, and regenerate the RCE evidence registry (L010).
2. Rebuild the Docker image, which loads the defaults at build time.
3. Tell the mentor the Stage-3b default changed, and that the demo's deep-caries labels change.
4. Re-check the panel video against `main` before showing it: scene 10 now describes the
   replaced head, and scene 19 and Part 3 counts have moved.
5. Push this branch and merge to `main` when the owner asks. Four commits from the first half,
   plus this change.
