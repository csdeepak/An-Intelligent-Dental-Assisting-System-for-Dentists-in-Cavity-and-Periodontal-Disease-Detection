# 2026-08-28 — C4: abstention and the coverage–accuracy curve

## Session goal

Close contribution **C4** — the `not_assessable` output reported as a coverage–accuracy curve —
which had been sitting at zero while every status table implied it was done.

## What was done

- **Audited what was actually open before choosing work.** The session began with the user
  challenging a bad estimate of mine: I had budgeted ~1 GPU-hour / ₹130 for C1 and it cost 5
  minutes / ₹37.93. Rather than propose work from memory, I grepped for the state of R2, R3 and
  the coverage curve. That found C4 missing — the pipeline has emitted an `assessable` flag per
  tooth since R4, and calibration landed 27 Aug, but **the curve itself had never been drawn**.
- **Wrote `scripts/eval/c4_coverage_accuracy.py`** (CPU only, no GPU, no retraining). Two curves:
  Stage 2 FDI numbering over 661 detected teeth from the saved 936-row evaluation, and the caries
  gate over 863 held-out crops re-scored with the isotonic-calibrated confidence.
- **Results.** Declining the least-confident quarter lifts Stage 2 **0.826 → 0.885**
  (+5.91 pp [+3.88, +7.68]) and the caries gate **0.797 → 0.940** (+14.25 pp [+11.32, +16.63]).
  CIs are clustered bootstrap over **images**, not teeth.
- **Added the shuffled-confidence control**, which collapses both gains to +0.03 / +0.00 pp.
- **Located the pre-registered threshold on the curve without tuning it:**
  `ASSESSABILITY_MIN_FDI_CONFIDENCE = 0.30` retains 90.8% of detected teeth at 0.847 accuracy —
  within 0.2 pp of the empirical 90%-coverage point (0.849).
- **8 new tests** in `tests/test_c4_coverage.py`; suite **84 → 92**, all invariants hold.
- Documented in `RESULTS_LOG.md` 2026-08-28a, `PAPER_MATERIAL.md` §8.21, `model_metrics.md`,
  and `transfer.md` §2.

## Decisions made

- **The threshold was deliberately not swept.** `run_inference.py` fixes 0.30 a priori and its
  comment forbids tuning it against an evaluation set. Reporting "0.42 was best on the test set"
  would be selecting an operating point on the data it is then evaluated on. The script reports
  where the pre-registered value *lands*, and I made that refusal explicit in the module docstring
  so a future session does not "improve" it.
- **The caries arm uses calibrated, not raw, confidence.** An abstention rule built on scores known
  to be systematically overconfident (ECE 0.136, §8.15) would decline the wrong cases. The
  *verdict* still comes from the raw argmax — only the ranking is calibrated.
- **Added the shuffled control rather than shipping the curve alone.** A coverage–accuracy curve
  rises for two very different reasons: informative confidence, or the arithmetic of discarding
  items. Shuffling separates them. This is the same move as C1's constant-guess control, and it is
  becoming the house pattern: *show what the number looks like with the mechanism removed.*
- **Clustered the bootstrap by `source_image_md5`** for the caries arm and by `image` for Stage 2 —
  teeth from one radiograph are not independent, the same correction as 2026-08-27n.
- **Recorded the coverage caveat prominently** instead of burying it: Stage-2 coverage is over
  *detected* teeth, so 75% coverage is 75% of 70.6% = **53.0% of teeth actually present**.
  Abstention cannot recover what Stage 1 never found, and a reviewer would catch that phrasing.

## Open questions

- **Is the Stage-2 abstention gain limited by saturation rather than by the curve?** The head needs
  confidence ≥ 0.962 just to reach 75% coverage — it is pinned near 1.0 on most teeth. Whether
  calibrating the *numbering* head (only the caries gate has been calibrated) would recover more
  abstention value is untested and is a genuinely open question.
- **No external abstention curve.** Both curves are internal (DENTEX). Whether the ranking still
  separates correct from incorrect on Ningxia is unknown — and answering it would consume one of
  the deliberately-rationed touches of that locked set.
- **Should the pipeline expose a coverage knob at all?** Right now 0.30 is fixed. The curve makes a
  clinician-tunable coverage setting defensible, but that is a product decision, not a measured one.

## Next steps

1. **Write the paper draft.** Unchanged, and now the only item on the critical path — C4 was the
   last unmeasured contribution.
2. **C1 hardening** (~₹80–150 of the ₹612.88 remaining): a second model and a few-shot arm, so the
   "below a constant guess" finding does not rest on one model under one prompt.
3. **Stage-2 head v3 on the Kaggle third FDI corpus** — the only justified remaining training job.
4. **Per-item prediction dumps** for detection mAP and both ResNet18s, to close the CI gaps §8.14
   still lists as missing.
5. **Rebuild the Docker image** — it predates the isotonic wiring.
6. The four compliance blockers remain account-owner actions and are still untouched.

## Note for the next session

`python` under the **Bash** tool resolves to MSYS2's `/c/msys64/ucrt64/bin/python` (3.11.7, no
numpy), **not** the rebuilt environment. The working interpreter is
`C:\Users\csdee\AppData\Local\Programs\Python\Python313\python.exe`. This cost a confusing
`ModuleNotFoundError` at the start of the session; use the explicit path.
