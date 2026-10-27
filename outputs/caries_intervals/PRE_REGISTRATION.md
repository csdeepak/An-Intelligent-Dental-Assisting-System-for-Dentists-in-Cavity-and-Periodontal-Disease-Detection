# Pre-registration — three interval measurements for the caries tables

**Drafted 11 October 2026**, as items 2–5 of the implementation phase set by that day's council
(`docs/session-memory/2026-10-11-implementation-phase-council.md`, `transfer.md` §3).

**Frozen when committed, before any analysis code is written and before any number below is
computed.** The commit hash is recorded in the `RESULTS_LOG` entry that reports the results.
Nothing in this file moves after a number is seen. Same discipline as Levers 1, 2, A, A2, B, C.

None of the three measurements is a lever. No model is trained, no threshold is chosen, no
default changes, and no adoption decision depends on any outcome. They exist because the
manuscript makes three statements it cannot currently support with an interval or a number.

---

## 0. Compact

| | |
|---|---|
| Goal | Put intervals on two existing claims and measure one number the paper lacks |
| Who cares | A reviewer of the caries tables; the authors, who must word three sentences honestly |
| Decision changed | Wording only: abstract, Table I, the Lever B subsection, Conclusion |
| Unacceptable mistake | Choosing an analysis after seeing which one favours the pipeline |
| Acceptable mistake | A wide interval. It is reported as wide |
| Baseline | The image-blind molar constant, already frozen |
| Rollback | None needed. Nothing ships; the results are numbers in a log |

## 1. What has already been seen

Stated first, because it decides which of these can be a test and which can only be an estimate.

- **M1.** The point F1 values are published: constant 0.3197, gate pipeline 0.2936, Qwen2.5-VL-32B
  0.2465, Qwen2.5-VL-7B 0.1493 (`outputs/c1_vlm/c1_comparison.json`,
  `outputs/c1_vlm/c1_constant_arm_vlm_32b_0shot.json`). No interval on any difference between
  them has been computed.
- **M2.** The per-hospital **point estimates were computed on 10 Oct 2026**, during a review:
  lesion detector vs constant — test1 0.462 vs 0.446, test2 0.576 vs 0.407, test3 0.494 vs 0.377,
  test4 0.430 vs 0.323. The pooled paired intervals are published (+10.17 pp [+6.27, +14.02] vs
  the constant; +9.28 pp [+5.31, +13.29] vs the gate). No per-hospital interval has been
  computed. **Because the point estimates are known, M2 is estimation, not a test.**
- **M3.** On the same 164 DENTEX images the adopted lesion detector's *lesion-localisation
  agreement* is published — 0.455, a tie with the constant's 0.489 and the gate's 0.443 — along
  with 527 flagged teeth and 218 of 479 lesions matched over the 148 lesion-bearing images
  (`outputs/lever_b_eval/dentex_lesion_b_pooled/lesion_localization.json`). **Its FDI-set F1,
  the metric of Table I, has never been computed by anyone.**

## 2. Method common to all three

- **Paired cluster bootstrap over images**, 10,000 resamples, seed 42, 95% percentile interval,
  a fresh `numpy.random.default_rng(42)` per comparison. Images are the unit; teeth and lesions
  within one radiograph are not independent.
- Reuse `cluster_bootstrap`, `paired_bootstrap` and `ratio` from `scripts/eval/bootstrap_ci.py`.
  No new bootstrap, no new matcher, no new scorer.
- Every measurement has a **harness gate**: the code must first reproduce an already-published
  number exactly. If a gate fails, nothing further is read and the failure is logged as a
  harness defect.
- Every comparison listed here is reported. None is dropped for being inconvenient, and none is
  added afterwards.

## 3. M1 — an interval on the headline F1 gap

**Claim under examination.** "The constant scored highest (F1 0.320 versus our pipeline's 0.294)"
— abstract, Table I, Conclusion.

- **Metric.** Micro FDI-set F1 exactly as `scripts/eval/c1_vlm_baseline.py::score` computes it:
  with per-image counts `n_hit`, `n_pred`, `n_gt`, F1 = 2·Σn_hit / (Σn_pred + Σn_gt).
- **Data.** The 164 leak-free DENTEX `disease/` images, ground truth from `load_gt`.
  Predictions: the frozen constant `{16,17,26,27,36,37,46,47}` for every image;
  `outputs/c1_vlm/arm_pipeline.json` (the gate pipeline); `arm_vlm_32b_0shot.json`;
  `arm_vlm_7b_0shot_rerun.json`.
- **Comparisons.** Primary: constant − pipeline. Secondary: constant − VLM-32B,
  constant − VLM-7B, pipeline − VLM-32B.
- **Harness gate.** Reproduce tp / fp / fn exactly: constant 286 / 1026 / 191; pipeline
  186 / 604 / 291; VLM-32B 116 / 348 / 361; VLM-7B 51 / 155 / 426.
- **Reading rule, fixed now.** If the primary interval excludes zero, "outscored" stands. If it
  includes zero, the manuscript must say the constant and the pipeline are **not separable on
  FDI-set F1**, and the ordering claim rests on the lesion-agreement metric, where an interval
  already exists (+4.59 pp [+0.60, +8.89]). The paper's argument — that a score an image-blind
  constant can match cannot show a system is reading the image — does not depend on which way
  this falls, and that is to be said plainly rather than used to soften the result.

## 4. M2 — Lever B per hospital

**Claim under examination.** The manuscript recommends reporting external results "per
institution rather than pooled", and reports its own positive result pooled only.

- **Metric.** Lesion agreement, `n_covered / n_lesions`, within each Ningxia `split`
  (test1–test4), and pooled.
- **Data.** The saved outputs only:
  `outputs/lever_b_eval/ningxia_{lesion_b_pooled,constant,pipeline}/ningxia_external.json`,
  337 rows each, paired on (category, split, image). **No inference. Ningxia is not re-run,
  re-read or re-scored.**
- **Comparisons.** Lesion detector − constant, and lesion detector − gate, per hospital and
  pooled. Also each arm's own agreement with its interval, per hospital.
- **Harness gate.** The pooled rows must reproduce +10.17 pp [+6.27, +14.02] and +9.28 pp
  [+5.31, +13.29].
- **No bar.** The pre-registered Sec 6 verdict of Lever B (2 of 3 cohorts, 4 Sep 2026) is not
  reopened, strengthened or weakened by anything here.
- **Reading rule.** Per hospital: interval excludes zero → "separated at this hospital";
  includes zero → "not separated here". Hospitals have 134, 110, 40 and 53 images, so wide
  intervals at test3 and test4 are expected and are reported as such.
- **Forbidden.** Counting "wins at k of 4" from point estimates; leave-one-hospital-out;
  pooling the cross-centre hospitals only; any threshold, selection or tuning that uses these
  numbers.
- **Consequence stated in advance.** If any hospital's interval includes zero, the sentence
  "It replicates on the one cohort that is genuinely external" must be qualified as a pooled
  statement, and the per-hospital table is printed beside it.

## 5. M3 — the adopted lesion detector on the Table I metric

**Claim under examination.** Table I is headed as the pipeline's score and reports the gate
pipeline, which stopped being the pipeline's default on 4 Sep 2026.

- **Configuration, frozen.** `scripts/run_inference.py` defaults, unchanged: Stage 1
  `models/11` (sha256 `271316c4…`), Stage 2 `models/10` (`6c675fa0…`), Stage 3a lesion detector
  `models/16` (`029018db…`), detector confidence 0.25, image size 1024, NMS IoU 0.50, Hungarian
  one-to-one assignment. Device forced to CPU for both runs below. A tooth is predicted carious
  when its `caries.finding` is not `no_caries`, the rule the published arm already uses.
- **Control first.** A same-day, same-machine run of the **gate** path
  (`caries_method="gate"`, `models/09`, `8f4a99ba…`) over the same 164 images, written to a new
  file. **Gate: its F1 must fall within ±0.005 of the published 0.2936.** If it does not, the
  detector run is not read; the discrepancy is investigated and logged first.
- **Then the detector, run once.** `caries_method="lesion-detector"`, same images, written to
  its own file. It is not re-run with another confidence, image size or assignment.
- **Metric.** Micro precision, recall and FDI-set F1, the M1 scorer.
- **Comparisons.** Primary: detector pipeline − constant. Secondary: detector pipeline − the
  same-day gate control.
- **Leakage.** The 164 images are MD5-disjoint from the detector's DENTEX training images; that
  gate lives in `scripts/dentex/build_dentex_caries_boxes.py` and was recorded in `RESULTS_LOG`
  2026-09-04f. DENTEX is still *development* data for this detector — a corpus it trained on,
  scored on images held out from it — and the row is labelled that way.
- **Reading rule.** Primary interval excludes zero and is positive → the detector beats the
  constant on FDI-set F1 on DENTEX. Includes zero → a tie, written as a tie. Excludes zero and
  is negative → a loss, printed in Table I as a loss. All three outcomes are compatible with
  what is already published (a tie on lesion agreement on this cohort), and none changes the
  pipeline default.

## 6. What is deliberately not done

No threshold sweep, no second detector confidence, no calibration or abstention curve, no
Ningxia or CariesXrays inference, no change to any `DEF_*` default, no edit to `paper/main.tex`
in this piece of work. The manuscript changes these results require are written out as a list
for the authors.

## 7. Outputs and logging

- `outputs/caries_intervals/caries_intervals.json` — every point estimate, interval and gate.
- `outputs/caries_intervals/arm_pipeline_gate_control.json` and
  `arm_pipeline_lesion_detector.json` — per-image predictions for M3. The published
  `outputs/c1_vlm/arm_pipeline.json` is never overwritten.
- One `RESULTS_LOG.md` entry; `model_metrics.md`; `PAPER_MATERIAL.md`; `transfer.md` §3; a
  session-memory file. Per `CLAUDE.md` rules 1, 2 and 5.

## 8. Stop conditions

- A harness gate fails → stop, log it, fix the harness, and say so in the entry.
- The M3 control misses its tolerance → stop before the detector run.
- Anything here turns out to need a decision this file did not anticipate → stop and ask,
  rather than deciding after a number is visible.

---

## 9. Amendment 1 — 11 October 2026, written before M3's detector arm was run

Sections 1–8 above are unchanged and were frozen at commit `1fd20b5`. This amendment changes one
thing, the M3 control gate in §5, and it was written **knowing only control numbers**. The
lesion-detector arm had not been run, and no M3 result existed, when it was committed. The user
approved it in the session. M1 and M2 were already complete and are not touched.

**What happened.** The §8 stop condition fired. The same-day gate control on the macOS machine
scored tp / fp / fn 189 / 593 / 288, F1 **0.3002**, against the published 186 / 604 / 291,
F1 0.2936 — a difference of 0.0066, outside the ±0.005 tolerance. 126 of 164 images have
identical prediction sets; 52 tooth codes differ out of roughly 790.

**What the investigation found.** The pipeline code as of commit `322f787` (30 Aug 2026, the
state the published file was produced from) was run on the same macOS CPU over the same 164
images. Its predictions are **identical to the control's on all 164 images, with zero differing
codes**. So nothing in the code changed the gate path between 30 Aug and today — the Lever B
wiring and the Lever C refactor included — and two runs on this machine are deterministic. The
published file was produced on the Windows machine (its recorded latency is 2.39 s per image;
this machine runs 1.63 s). The difference is between machines, not between code versions.

**Why the original gate was wrong.** §5 asked for a "same-day, same-machine" control and then
gated it against a number from a different machine. This project has measured cross-machine
drift of this size before (`RESULTS_LOG` 2026-08-25i, 2026-08-27e). The tolerance tested the
wrong thing. That was an error in this pre-registration, made by its drafter.

**The amended gate.** The control passes if its predictions are identical, image by image, to
the `322f787` code's predictions on the same machine — which establishes that the harness and
the pipeline have not drifted. The cross-machine difference is **recorded, not gated**: both
sets of counts are written to the results file and to the log.

**What does not change.** The metric, the 164 images, the frozen configuration, CPU, the
run-once rule, both comparisons and all three reading rules. The secondary comparison was
always "detector − the same-day gate control", and it still is.

**What this costs, stated now.** The detector arm inherits this machine's Stage 1 and Stage 2
behaviour, so M3's numbers are **measured on the macOS machine** and are labelled that way.
They are directly comparable to the control (0.3002) and to the constant, which is the same on
every machine. They are comparable to the published 0.2936 only up to the 0.0066 drift recorded
above. Whether Table I should restate both pipeline rows from one machine is a decision for the
authors, and it is listed for them rather than taken here.

**Artefact.** The `322f787` predictions are kept as
`outputs/caries_intervals/arm_pipeline_gate_code322f787.json`.
