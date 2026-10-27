# 2026-10-13 — Stage 4a scored on radiographs it never trained on

**Session goal:** the user asked whether the held-out bone-loss score was good to go and said
to start. Run it, properly.

Run on the macOS clone. Numbers are in `RESULTS_LOG` 2026-10-13.

## What was done

1. **Checked it could be done here.** The 1,000 Tufts radiographs, the expert masks and
   `teeth_bbox.json` are on this machine. The original crop images are not — only their two
   manifests are. That shaped the gate.
2. **Read the recipe from its source**: cells 5, 9, 14, 16 and 18 of
   `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`, the training notebook's
   validation transform, and the two log entries of 7 Sep on how the August rebuild went wrong
   (it read the box field in the wrong order and cut a mirrored region).
3. **Counted the population without opening a mask**: 855 radiographs outside the 145; two
   byte-identical pairs, both inside the 855.
4. **Pre-registration** written to `outputs/bone_loss_eval/heldout/PRE_REGISTRATION.md` and
   committed by me at `570925c` — that one file, local, not pushed — before any held-out tooth
   was cropped. The user's "start doing" followed my saying I would write it first "as before";
   I read that as the same terms as the three earlier amendments.
5. **`scripts/eval/bone_loss_heldout.py`**: `gate`, `score`, `report`. `score` refuses without
   a passed gate and refuses to run twice. Three unit tests.
6. **Gate, on the 145 training-side radiographs.** All 2,131 clean manifest rows found a
   regenerated crop, 2,127 with the same label. The model found 29 of 35 clean validation
   positives — the figure from the other machine — and passed 748 of 750 normals.
7. **The one held-out pass.** 821 radiographs, 21,956 teeth, 946 positive. **Sensitivity 7.6%,
   specificity 98.7%.**
8. **Checked it was not an artefact, without a model.** Same frame and mask size as the 145,
   26.7 teeth per radiograph against 26.9, the 32 radiographs that yielded nothing have no tooth
   objects, and the held-out positives overlap the mask by a median 8.6% against a 1% threshold.
9. **Re-derived** every count, both primary intervals and the four ranking figures with separate
   code and no scikit-learn. All match.
10. **Documents:** `RESULTS_LOG`, `model_metrics.md` (Stage 4a now leads with the held-out
    table), `PAPER_MATERIAL.md` §8.34, `transfer.md`, `SUBMISSION_TODO.md` (a draft paragraph
    with the figure), the root README's limitation row, `scripts/eval/README.md`, and
    `models/03_…/run_summary.txt`.
11. **The pipeline's own report** now states the held-out figure in two places. A run before and
    after gives identical per-tooth output.

Committed by me: `570925c` only. With `f5d7f29` and `f75e81f` from 12 Oct, three local commits
are unpushed. Everything else is for the user.

## Decisions made

- **The gate was built from what this machine has.** Bit-identity with the original crops could
  not be checked here. Label agreement against the manifests and the one known model result on
  clean crops could, and between them they test the box convention, the expansion, the label
  rule and the model's input. The August rebuild would have failed both.
- **The population is every radiograph outside the 145, not only the 290 with a mask.** The
  training build mixed both kinds, and specificity on patients with nothing marked is half of
  what a flag is for. The masked stratum is reported beside it.
- **A tooth-position prior was registered as the baseline.** It is the paper's own argument
  turned on this branch, and it was fixed before the result was known. On the whole population
  the model clears it on average precision by 2.8 points; within the masked radiographs it does
  not. Both are written, because the registered rule was stated for the population and the
  stratum tells the other half.
- **I did not look further once the number was in.** No per-tooth-type breakdown, no threshold
  sweep, no look at which 72 were found. The registration lists what is reported; a 7.6% result
  is exactly when a search for a kinder cut is tempting.
- **Three rates whose fourth decimal is a 5 are quoted to four places** rather than re-rounded.
- **The report text was changed, again by strings only.** A demo that tells its user the
  validation figure "is not a held-out estimate" should say what the held-out estimate is, now
  that there is one.
- **The README's banner and two of its table rows still show 0.9233.** I corrected the
  limitation row and logged the rest. The banner is an SVG image and a wider edit than this
  session's.

## Open questions

- **What does the user want the branch to be now?** It stays in the paper. As measured, it is a
  flag that misses 92% of its own label. Three roads: report that, as a pre-registered negative
  result; retrain it with a radiograph-level split on all 1,000 radiographs, which would be a
  new default and still an abnormality flag; or a periodontal-label experiment on BRAR.
- Why did the original build use 145 radiographs? 339 carry a mask.
- Does the mentor know any of this? Not recorded.
- Carried over: the repo owner; the grading date; the Tufts Drive folder; the Kaggle licence.

## Next steps

1. The user commits and pushes; three local commits go with it.
2. The user's choice among the three roads. Each of the last two needs its own pre-registration.
3. The six-page draft: `SUBMISSION_TODO.md` §1a rows a to n, and §2 item 3 with the new figure.
4. Mentor and repo owner, with this result first: it is the one most likely to change what they
   want the paper to say about the second half of the capstone's title.
5. Windows machine: pdfLaTeX build, `paper/paper.txt`, Docker rebuild.
