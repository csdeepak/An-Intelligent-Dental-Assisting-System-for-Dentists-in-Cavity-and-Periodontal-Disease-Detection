# 2026-10-13b — Stage 4a retrained with a radiograph-level split

**Session goal:** the user committed and pushed the held-out result and said to continue with
option 2 — retrain the bone-loss classifier with a proper split on all the radiographs.

Run on the macOS clone, evening of 13 Oct. Numbers are in `RESULTS_LOG` 2026-10-13b.

## What was done

1. **Checked the ground.** Tree clean and pushed. M4 Pro with MPS at about 235 images a second
   in training, so no rental. ImageNet ResNet18 weights already in the local cache, so no
   download. Read the original recipe from the training notebook and its saved summary.
2. **Chose the split before anything else:** the frozen `split_v1`, the one the detector and the
   numbering head use. A Tufts test radiograph is then unseen by every model in the pipeline.
   Model-free counts: 678 / 145 / 143 after two twins and 32 radiographs with no tooth box.
3. **Pre-registration** at `outputs/bone_loss_eval/v2_retrain/PRE_REGISTRATION.md`, committed
   by me at `0993d4a` before any crop was cut. I had typed 14 October in it; `d8dff27` corrects
   the date and nothing else. Both local, on the same terms as the earlier ones.
4. **Code.** `scripts/tufts/train_bone_loss_v2.py` (check, train);
   `scripts/eval/bone_loss_v2_eval.py` (the test pass, refuses twice). The gated crop builder in
   `bone_loss_heldout.py` gained an optional box-jitter argument, off by default, and its scorer
   a weights argument. Five unit tests. A `.gitignore` line keeps the new weights out.
5. **Harness checks, all passed:** the builder reproduces 512 saved rows of 13 Oct exactly; the
   split is disjoint with the registered counts; one epoch on 64 crops runs.
6. **Three training runs**, seeds 42, 43, 44, about 18 to 35 minutes each.
7. **The one test pass.** Seed 42: sensitivity 27.5%, specificity 95.9%. Seeds 43 and 44: 16.5%
   and 11.0%. The shipped model on the same split: 3.4%. Both registered eligibility conditions
   pass on all three seeds.
8. **Re-derived** every count and point value and the three E1 intervals with separate code and
   no scikit-learn. All match. Checked that the 143 scored radiographs are exactly the test
   split.
9. **Documents:** `RESULTS_LOG`, `model_metrics.md`, `PAPER_MATERIAL.md` §8.35, `transfer.md`,
   `SUBMISSION_TODO.md`, the READMEs, and `models/18_bone_loss_radiograph_split/run_summary.txt`.
   Fifty bracketed pairs audited against the result files; the five that do not match are two
   one-decimal renderings of an interval and three recipe ranges.

Committed by me: `0993d4a` and `d8dff27` only. **No default was changed.**

## Decisions made

- **The split is `split_v1`, not a new one and not cross-validation.** One split for the whole
  Tufts side is worth more than the tighter intervals five folds would give, and it leaves one
  shippable checkpoint rather than five.
- **The recipe is the original's.** The question was what the split cost, so everything else
  that could stay the same did. Three differences are registered; one of them — redrawing the
  normals each epoch instead of fixing 2,500 — is a change I chose, and it is named as mine.
- **Three seeds, with the shipping seed fixed before training.** It cost an hour and it is the
  most informative thing in the result: sensitivity moves from 11% to 27% between seeds while
  the ranking quality does not move. Seed 42 turned out to be the most sensitive of the three.
  Had I picked it afterwards it would have been a selection; fixed beforehand it is luck, and
  the other two are printed beside it.
- **"Eligible" was separated from "adopted" in the registration.** The rule decides whether the
  question of adoption arises. It has arisen. I did not change `DEF_BONE_LOSS`: every earlier
  change of default in this project was the decision owner's, and this one puts a 45 MB file in
  git and changes what the demo shows.
- **The operating point stays at argmax.** A validation-chosen threshold was registered as a
  secondary and turned out no better, which closes that door cheaply.
- **I stopped the first launch.** Its log was block-buffered and showed nothing after two
  minutes. No epoch had printed and no model file existed, so restarting it unchanged with live
  logging selected on nothing. It is in the log entry.
- **I did not rescue the weak absolute result.** The validation curves made it clear within one
  run that this recipe memorises. Changing the recipe after seeing that is exactly what the
  registration forbids, and a regularised second attempt would be a new experiment with its own
  registration.

## Open questions

- **Does the user adopt the retrained model as the Stage-4a default?** For: it is measurably
  better than the one shipped, on every seed, and its numbers are honest. Against: about one
  false flag per radiograph, a quarter of labelled teeth found, an operating point that depends
  on the seed, and no external figure. It is still an abnormality flag either way.
- Would a regularised recipe do better? Every run memorised its training crops. Unregistered.
- What does the severity model do on the teeth the retrained model flags? Unmeasured.
- The retrained model's firing rate on DENTEX. Unmeasured.
- BRAR, for a periodontal label. Not started.
- Carried over: the mentor and the repo owner; the grading date; the Tufts Drive folder; the
  Kaggle licence.

## Next steps

1. The user commits and pushes; `0993d4a` and `d8dff27` go with it. The three checkpoints stay
   on this Mac unless one is adopted.
2. The adoption decision. If yes: hash pin and tag, `.gitignore` exception for
   `seed42_best.pth`, `DEF_BONE_LOSS`, the report text, the scoreboard, a pipeline smoke test,
   and the Docker image on the Windows machine.
3. The six-page draft, with the matched pair for the bone-loss paragraph.
4. Mentor and repo owner.
