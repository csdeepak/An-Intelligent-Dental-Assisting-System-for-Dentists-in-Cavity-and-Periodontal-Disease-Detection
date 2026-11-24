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

## Decisions made

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

- **Adopt seed 42 as `DEF_CARIES_SEVERITY`?** The two heads are not separable on extern50, so
  the argument for adopting is "tested", not "better". Adopting needs:
  - a hash pin in `run_inference.py`;
  - a `.gitignore` exception (44.8 MB);
  - `CARIES_SEVERITY_NOT_EVALUATED` rewritten, and a schema bump;
  - a parity run;
  - Table 3 and the Limitations line in `research_paper/`.
- **Why does `models/07` score 0.738, not 0.77, on the regenerated extern50 crops?** Candidates
  are crop regeneration (21k verified 4 sample crops; 3 bit-identical, 1 off by ±1) and the
  notebook's evaluation preprocessing. Not investigated.
- **Severity on detector boxes and flagged teeth is untested.** The test used annotation boxes of
  truly carious teeth. No DENTEX image set with deep-caries labels has been run through the
  pipeline.
- **Should the video's scene 10 change?** "Validated, never tested" stays true of the shipped
  head. It could add "a retrained head tested at 0.77".

## Next steps

1. The decision owner (and the mentor) decide: adopt, keep, or withhold (`transfer.md` §4).
2. If adopt: wire the default with a hash pin, update the report text and the schema, run the
   parity check, and update the `research_paper/` Table 3 row from `PAPER_MATERIAL.md` §8.46.
3. If keep: the paper may add one clause, saying a retrained head of the same architecture was
   tested. Table 3 stays as is.
4. Re-check the panel video's scene 19 and Part 3 against `main` before showing it.
