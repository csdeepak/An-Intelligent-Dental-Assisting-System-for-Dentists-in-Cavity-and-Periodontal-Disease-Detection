# Pre-registration — re-measuring the pipeline for a change of Stage-1 detector

**Drafted 11 October 2026.** It accompanies the decision record `RESULTS_LOG` 2026-10-11f, and
follows the plan in `docs/session-memory/2026-10-11e-detector-switch-plan-council.md`.

**Frozen when committed, before any run below is made.** The commit hash is recorded in the
`RESULTS_LOG` entry that reports the results. Nothing here moves after a number is seen.

**What this is not.** It is not a test of whether to switch. That was decided by a person, with
outcomes already in view, against two pre-registered verdicts; the decision record says so. This
file fixes how the pipeline is re-measured under the new detector, what may be said about each
result, and the one result that stops the switch.

---

## 0. Compact

| | |
|---|---|
| Change | Stage-1 tooth detector: `models/11` (Tufts-only, seg) → `models/15` arm3c (Tufts + DENTEX + Kaggle, detect) |
| Decision owner | Gunadeep (gunadeep19). Repo owner and mentor not yet consulted |
| What must not happen | A number chosen, dropped or re-run because of how it came out; a table mixing two detectors; a report labelled with the wrong detector |
| Baseline | `models/11`, re-run on this machine immediately before each arm3c run |
| Stop rule | §5 — one, about the caries result |
| Rollback | Do not change `DEF_DETECTOR`; or, afterwards, revert that one commit |

## 1. Frozen configuration

- **New detector:** `models/15_detector_multicorpus_leverA/arm3c_best.pt`,
  sha256 `5d301f13fb48da5c74e7ef01bd0f91226f9b6800cb433dee5aebc8f8db8f161e`.
- **Baseline detector:** `models/11_yolo_seg_tufts_r1/best.pt`,
  sha256 `271316c46caaf4029ea707fa77b6fe30697795e46632e1f6fcae3498c48781ba`.
- **Everything else unchanged and hash-pinned:** FDI head `models/10`; lesion detector
  `models/16`; caries gate `models/09`; detector confidence 0.25, image size 1024, NMS IoU 0.50;
  lesion confidence 0.25; Hungarian one-to-one assignment.
- **One machine:** the macOS clone, torch 2.2.0, ultralytics 8.4.127. Every run names its
  detector explicitly with `--detector` or `--weights`. The default is not changed until §6.
- **Nothing is tuned.** No confidence, threshold, image size or assignment option is varied.

## 2. What has already been seen

- arm3c's numbering on DENTEX (92.8% end to end, recall 99.6%) and on Tufts (63.5%, recall
  89.3%), and its Tufts test box mAP@0.5 (0.585).
- arm3c with the **retired caries gate** on Ningxia (0.407 → 0.600, per hospital as well) and on
  a 1,500-image CariesXrays sample (0.309 → 0.370).
- That the current front end delivers 288 of 477 carious DENTEX teeth under the right code, and
  arm3c 453 (`RESULTS_LOG` 2026-10-11c).
- arm3c's parameter count, 25,311,251.

**Never measured, and the substance of this file:** the current caries default — the lesion
detector — together with arm3c, on any cohort; the image-blind constant's lesion-agreement
score under arm3c; FDI-set F1 under arm3c; an interval on the Tufts numbering difference.

## 3. Method

- **Paired cluster bootstrap over images**, 10,000 resamples, seed 42, 95% percentile interval,
  a fresh generator per comparison, primitives from `scripts/eval/bootstrap_ci.py`.
- **Every row is run twice on this machine: `models/11` first, then arm3c**, each into its own
  directory under `outputs/stage1_switch/`. No published artefact is overwritten. The arm3c
  result of a row is not read until that row's `models/11` control has passed its gate.
- **Gates.** Where a `models/11` result produced on this machine already exists, the control
  must reproduce it exactly. Where the published figure came from the Windows machine, the
  image and lesion counts must match exactly, the two figures are recorded side by side, and a
  difference above 1.5 percentage points stops the row until it is explained.
- **Differences between detectors are always computed against the same-machine control**, never
  against a published number from the other machine.

## 4. The matrix

| Row | What | Script (`scripts/eval/` unless noted) | Control must give |
|---|---|---|---|
| A | Tufts numbering, 143 images, 3,760 teeth | `validate_fdi_assignment_tufts.py --weights` | 2,438 correct — exact |
| B | DENTEX numbering, 164 images, 936 teeth | `validate_fdi_assignment.py --method head --weights --head-weights models/10…` | 547 correct — exact |
| C | DENTEX lesion agreement: gate, constant, lesion detector, all-teeth | `lesion_localization.py --detector --decision` | 479 lesions; 212 / 234 / 218 from the other machine |
| D | DENTEX FDI-set F1, both caries methods; latency | `c1_vlm_baseline.py --arm pipeline --caries-method --detector` | this morning's prediction sets — exact (189/593/288 and 192/352/285) |
| E | CariesXrays, the 1,200 held-out images: gate, constant, lesion detector | `cariesxrays_external.py --detector --decision --manifest --manifest-split val` | 1,200 images, 2,815 lesions; 892 / 1,582 / 1,926 from the other machine |
| F | Ningxia caries, 337 images: gate, constant, lesion detector; per hospital | `ningxia_external.py --categories dental_caries --detector --decision` | 1,013 lesions; gate 412 — exact; 404 / 507 from the other machine |
| G | Ningxia Stage-4 flag rate | `ningxia_external.py --categories periodontitis` | 6,791 affected teeth; 165 flagged from the other machine |
| H | Parameter counts | `scripts/count_model_params.py --stage1 --out` | 27,617,459; total 97,649,753 |

The CariesXrays list of 1,200 is rebuilt as a file from the image names in the three saved
per-image outputs of 4 Sep, which carry one identical set; the run must report "1200 resolved".

**Rows F and G touch the locked Ningxia cohort. They run last, and once.** The repo owner is to
be told before they run; if he has not been, the results entry says so. Nothing is fitted or
chosen on Ningxia. The results entry states the number of times the cohort has now been scored,
and repeats that the default was chosen after this detector's gate-path Ningxia result was known.

## 5. The one result that stops the switch

**S1.** For the lesion-detector caries path, take the paired difference in lesion agreement,
arm3c minus the same-machine `models/11` control, pooled over the Ningxia caries images (row F)
and the CariesXrays 1,200 (row E), resampling images. **If the 95% lower bound is below
−2 percentage points, `DEF_DETECTOR` is not changed.**

- The margin is Lever A's Guard 1, which arm3c passed only for the retired gate. This asks the
  same of the caries path the pipeline actually ships.
- S1 uses a locked cohort as a veto. That is disclosed here and in the results entry.
- **Not triggering S1 is not validation.** It means the caries result was not materially harmed.

**Nothing else reverses the switch.** In particular, no comparison against the image-blind
constant does: in lesion agreement the constant is placed with the pipeline's own boxes and
numbering, so it moves with the detector. A comparison that both arms shift cannot referee the
shift.

**Integrity stops, which are not outcomes:** a weight hash that does not match; a control that
misses its gate; an output file whose recorded detector is not the one intended; any tracked
file under `outputs/` showing as modified.

## 6. What happens after the matrix

If S1 does not fire and no integrity stop is open: `DEF_DETECTOR` changes in one commit, and
arm3c is added to `DETECTOR_PROFILES` with the recall and end-to-end FDI measured in row B on
this machine and a note that DENTEX is in-domain for it. The weights are committed under a
recorded `.gitignore` exception. Not before.

## 7. How each result is to be worded, fixed now

- **Tufts numbering (row A).** The paired difference with its interval. Interval excludes zero
  and is negative → "costs X pp on Tufts". Includes zero → "not separable on Tufts". Never "no
  cost", and never as evidence that either earlier guard was met.
- **DENTEX numbering (row B).** Reported as **in-domain** for arm3c. 58.3% is kept beside it as
  the cross-domain reference. Never an unlabelled "58.3 → 92.8".
- **Caries, three cohorts (rows C, E, F).** Lesion agreement for the gate, the constant and the
  lesion detector under each front end, with flagged-teeth counts beside every figure, because
  agreement rises with flagged area. Lever B's 4 Sep comparison is recomputed under arm3c **as a
  description**. Lever B's verdict is not re-decided: it stands for the front end it was scored
  on. If under arm3c the lesion detector no longer separates from the constant on two cohorts,
  the manuscript says the rule was met under the previous front end and states what holds now.
- **FDI-set F1 (row D).** The constant is fixed, 286 / 1026 / 191, whatever the detector. Both
  caries methods under arm3c against it, and arm3c against the control for each method.
  Excludes zero → separated; includes zero → not separable.
- **Per hospital (row F).** As in `outputs/caries_intervals/PRE_REGISTRATION.md` §4: intervals,
  "separated" or "not separated here", and none of its forbidden summaries.
- **Stage 4 (row G).** A flag rate, described as an abnormality-proximity flag.
- **Everything measured before this file** — Lever B's verdict, the three measurements of this
  morning, every table in `paper/main.tex` — keeps its numbers and is labelled "previous front
  end" wherever it stands beside a new one. No old entry is edited.

## 8. Forbidden

Re-running any row because of its result; a second pass over Ningxia; a different detector
confidence, image size or assignment option; choosing a front end per cohort; a table or
sentence that mixes front ends without saying so; "generalises", "guard met", or "pre-registered
adoption"; reading an arm3c result before its control has passed.

## 9. Known traps, written down so they are not rediscovered

- The one-to-one assignment gives no code to boxes beyond the 32nd in an image and rejects none
  below it. arm3c emits more boxes. Uncoded teeth drop silently out of FDI-set F1; the count of
  uncoded matched teeth is reported for both detectors.
- A lesion is mapped to the tooth box it overlaps most. Different box sizes change that mapping
  and the flagged area. Hence the flagged counts in §7.
- Several scripts write to a fixed filename, and one names its output directory from a tag that
  does not namespace the default. Every run passes an explicit output directory.
- `scripts/count_model_params.py` rewrites its JSON with LF line endings on this machine. Row H
  writes elsewhere.
- arm3c was trained partly on the Kaggle "dual-labeled" set, whose licence is unstated. That is
  a publication question, recorded in the decision record; it is not an outcome of this matrix.

## 10. Outputs and logging

Everything under `outputs/stage1_switch/`: one directory per row and detector, the rebuilt
CariesXrays list, one results JSON with every point estimate, interval and gate, and the stdout
of each run. One `RESULTS_LOG.md` entry; `model_metrics.md`; `PAPER_MATERIAL.md`; `transfer.md`;
a session-memory file. `paper/main.tex` is not edited on this machine.

---

## Amendment 1 — the control gate for row G (11 October 2026, 17:27 IST)

**State when written.** Rows A, B and H had run and been read. Row C had run and had not been
read. Row D was running. Row E had not started. **No Ningxia run, under either detector, had been
made on this machine** — rows F and G did not exist. Committed before either is started; the
commit hash goes in the results entry beside the freeze hash.

**What is wrong with §4 as frozen.** Row G says the `models/11` control "must give 6,791 affected
teeth". An affected tooth is a *detected* tooth box with at least half its area inside the expert
region (`affected_tooth_sensitivity`, `scripts/eval/ningxia_external.py`). The count is therefore
a property of the detector's boxes, not of the dataset, and 6,791 was produced on the other
machine. The same weights do not give the same boxes on the two machines: 546 against 547
correctly numbered DENTEX teeth, 413 against 412 matched Ningxia lesions. An exact match was never
a sound requirement. This is the drafting error of this morning's first M3 tolerance
(`outputs/caries_intervals/PRE_REGISTRATION.md`, Amendment 1), found this time by reading the
code rather than by missing the gate.

**The gate for row G, replacing that cell of §4.**

- The control must score **736 images** — a dataset count, exact.
- Its affected-teeth and flagged counts are recorded beside the other machine's 6,791 and 165.
- The row stops until explained if the affected-teeth count is more than 1.5% from 6,791, or the
  flag rate more than 1.5 percentage points from 165 / 6,791. That is §3's tolerance, unchanged.

**A consequence, stated now.** The flag rate's denominator is detector-dependent, so it will
differ between the two front ends. Both counts are reported beside each rate, and the difference
is described as a difference in flag rate over each detector's own affected teeth, never as the
same teeth flagged more or less often.

**The repo owner.** The decision owner confirmed on 11 October that the repo owner has not been
told and that rows F and G run regardless. §4 requires the results entry to say so.

Nothing else in this file changes. S1 (§5) does not involve row G.

---

## Amendment 2 — five further rows, for rebuilding the manuscript (11 October 2026, 20:45 IST)

**State when written.** Rows A–H have run, been read and been logged (`RESULTS_LOG` 2026-10-11g,
-h, -i). The default has changed. The decision owner has chosen to rebuild the manuscript on the
current front end (`docs/paper/SUBMISSION_TODO.md` §1, option A). **None of rows I–M has been
run.** Committed before any of them starts.

**What these rows are for.** `paper/main.tex` reports five things the matrix did not measure
under the current front end. These rows measure them, under both detectors, on this machine, so
that every table of the rebuilt manuscript comes from one front end and one machine. **They are
not a test. Nothing here can change the default, the decision, or any earlier verdict.**

**Already seen, and bearing on these rows.** Row B's totals for both detectors, so row I's
"correct" and "not detected" buckets and row J's full-coverage accuracy are known. That on the 660
DENTEX teeth both detectors find, arm3c's boxes give 41 wrong codes (2026-10-11c). Row G's pooled
Stage-4 counts, of which row L is a breakdown. arm3c's Tufts test box mAP as measured on the
training machine, 0.5852, which row M repeats. **Not seen:** how arm3c's wrong codes divide
between buckets; any numbering-head confidence under arm3c; any Stage-4 output on DENTEX under
either current detector; the per-hospital Stage-4 split under arm3c.

| Row | What | How | The `models/11` control must give |
|---|---|---|---|
| I | Numbering failure taxonomy, DENTEX, 936 teeth | `stage2_failure_taxonomy.py` on the rows row B saved. No inference | 936 teeth, 547 correct, 273 not detected — exact (row B, this machine). Other machine: 546 / 275 / 89 off-by-one / 10 same-quadrant-far / 8 mirrored / 6 wrong arch / 2 other; a bucket more than 14 teeth (1.5% of 936) away stops the row |
| J | Coverage–accuracy for numbering | `c4_coverage_accuracy.py --rows` on the same rows. No inference. Threshold 0.30, registered 28 Aug: located, never tuned | 663 teeth, 547 correct at full coverage — exact. Other machine: 0.826 at full coverage, 0.885 at 75% (+5.91 pp [+3.88, +7.68]), 90.8% coverage and 0.847 at the threshold; a difference above 1.5 pp stops the row |
| K | Stage-4 flags on DENTEX, 164 images, through the pipeline as shipped, CPU | the driver in `run_matrix.sh` (`load_models`, `run_pipeline`) | 164 images. **No reference exists.** The manuscript's 0.7% (2 of 299 teeth) is a 12-image run of 24–25 Aug with the bbox detector, two front ends ago. It is printed beside the result, not gated on |
| L | Stage-4 flag rate per Ningxia hospital | analysis of row G's saved files. **Ningxia is not scored again** | 320 / 297 / 50 / 69 images — exact. Other machine: 79 of 3,285, 34 of 2,462, 23 of 411, 29 of 633; a flag-rate difference above 1.5 pp stops the row |
| M | Tufts test box mAP@0.5, 150 images, the detectors' own label frame | the call `train_multicorpus_detector_v2.py` made on 3 Sep, on CPU. Control B (Tufts-only, same recipe) first, then arm3c | Control B 0.7243 and arm3c 0.5852, both from the training machine; each must come within 1.5 pp here |

Row M has no `models/11` run. That model is a segmentation model validated against polygon
labels, and its 0.810 is on a different label set from the one both Lever A detectors were scored
on. The like-for-like pair is Control B and arm3c, and the manuscript states the cost that way.

**What is reported, fixed now.**

- **Row I.** All seven buckets for both detectors; the share of wrong codes that are off by one;
  the share of detected teeth placed in a wrong quadrant. In-domain for arm3c, and labelled so.
- **Row J.** Accuracy at 100, 90, 75 and 50% coverage; the gain at 75% with its interval and its
  shuffled control; coverage and accuracy at 0.30; and that coverage restated over teeth present
  (coverage × detection recall). **The threshold stays at 0.30 whatever it gives.** If under
  arm3c it retains nearly every tooth, or the gain's interval includes zero, that is what is
  reported.
- **Row K.** Flagged over detected teeth with a cluster interval for each detector, and the
  paired difference. The 12 images of the earlier run are reported as a subset beside the 164.
  It is a firing rate, not a sensitivity: DENTEX carries no periodontal ground truth.
- **Row L.** Per hospital, each detector's rate with its interval, and the difference, over each
  detector's own affected teeth (Amendment 1).
- **Row M.** Both values and their distance from the training-machine figures. **Reproducing
  0.585 does not touch Guard 2, which failed.**
- **CariesXrays.** The manuscript's CariesXrays row becomes the 1,200 held-out images of row E.
  The 1,500-image sample of 1 Sep is not re-run, and its figures, which are the previous front
  end's, are not set beside current ones.

**Forbidden,** in addition to §8: moving the 0.30 threshold; choosing between the 12-image and the
164-image firing rate after seeing them — 164 is the figure; dropping a row because the
manuscript reads better without it; any run on Ningxia.

## Amendment 3 — three rows on what the caries stage flags, how the constant is placed, and numbering on an unseen corpus (12 October 2026, 18:40 IST)

**State when written.** Rows A–M have run, been read and been logged. A second council of
12 Oct (`docs/session-memory/2026-10-12b-stage-metrics-council.md`) recommended three further
measurements and the decision owner said to run them. **None of rows N, O, P has been run.**
Committed before any of them starts.

**What these rows are for.** They are estimates for the manuscript. **Nothing here is a test.
Nothing here can change the default detector, the default caries path, or any earlier verdict,
whatever it gives.** No row touches Ningxia.

**Already seen, and bearing on these rows.**

- Row D: the lesion detector under arm3c flags 624 tooth codes on the 164 DENTEX images, 274 of
  them carious (tp 274, fp 350, fn 203). The constant: 286 / 1,026 / 191.
- A council member, checking that row N was feasible, counted tooth types in the saved
  predictions and reported 447 of the 624 flagged codes as molars. The chair has not checked
  that count. It is listed here because someone has seen it.
- On held-out crops with ground-truth boxes the retired gate flags 48.2% of healthy molars
  (31 Aug). That is a different population and a different model.
- Rows A and B: every numbering total for both detectors. Row I: the DENTEX error buckets.
- arm 4C, a detector trained **on** UFBA-425, was scored in September. arm3c and the numbering
  head v2.0 never trained on UFBA-425 (`data/detector_multicorpus_v2/train_3corpus.txt` has no
  UFBA line; the head's corpora are DENTEX and Tufts) and neither has been run on it.
- **Not seen:** how the 624 codes divide by label category; how many teeth in the 164 images
  are labelled healthy; precision by tooth type; how often a code in the constant's set sits on
  a tooth that is one; any output of either current detector on UFBA-425.

| Row | What | How | Gate before anything new is read |
|---|---|---|---|
| N | What the caries stage flags on DENTEX, 164 images | Analysis of the files row D saved, against the DENTEX labels. No inference | 164 leak-free images; the constant's 286 / 1,026 / 191; the lesion detector's 274 / 350 / 203 and the gate's row-D counts under arm3c, all exact |
| O | How well the constant's eight codes are placed, Tufts test, 143 images | Analysis of the rows row A saved. No inference. DENTEX (row B's rows) beside it as a secondary | Row A's totals for both detectors, exact: 3,760 teeth; 2,438 correct for `models/11` |
| P | Numbering and tooth recall on UFBA-425 | `validate_fdi_assignment_tufts.py` with a UFBA loader, head v2.0, conf 0.25, NMS 0.50, imgsz 1024, one-to-one. `models/11` first, then arm3c | Three gates, below |

**Row N, fixed now.**

- Each flagged (image, FDI code) pair falls in one category, first match wins: **caries** (the
  code carries a class-1 label), **other finding** (any of classes 2, 3, 5, 6, 7, 8),
  **labelled healthy** (class 0 only), **no annotation**.
- Tooth type by the code's position digit: incisor 1–2, canine 3, premolar 4–5, molar 6–8.
- Reported for the lesion detector, the retired gate and the constant: flagged codes by
  category; flagged codes by tooth type, with the carious share of each.
- **Primary:** the fraction of labelled-healthy teeth whose code is flagged, per arm, with a
  cluster interval over images, and the paired differences lesion detector − constant and
  lesion detector − gate. The same over labelled-healthy teeth at the constant's eight codes,
  where the constant is 100% by construction.
- With fewer than 30 labelled-healthy teeth in the cohort, or fewer than 10 at the eight codes,
  the counts are reported and no interval is.
- **Limits, to be printed with the result.** A flagged code is a code the pipeline assigned, so
  a misnumbered tooth is filed under the wrong tooth. "No annotation" is not "healthy": DENTEX
  labels about 6 teeth in 30. Labelled-healthy teeth are a small, non-random sample.
- **Wording.** `paper/main.tex` 447–449 says a model that must place a lesion "cannot score well
  by reproducing a prior over tooth positions". If the molar share of the lesion detector's
  flagged codes is within 10 points of the constant's 100%, or its flag rate on labelled-healthy
  teeth at the eight codes is 40% or more, that sentence is deleted. Otherwise it stays and the
  figures are quoted beside it.

**Row O, fixed now.** M is the constant's set {16, 17, 26, 27, 36, 37, 46, 47}.

- **Placement precision:** of ground-truth teeth matched to a box whose assigned code is in M,
  the fraction whose true code is in M; and the fraction whose assigned code is exactly right.
- **Reach:** of ground-truth teeth whose true code is in M, the fraction matched to a box and
  given a code in M.
- Each with a cluster interval over images, for both detectors, and the paired difference.
- Where the others go: of true-M teeth that are matched but coded outside M, the counts coded as
  a third molar, as a premolar, as anything else, and given no code.
- **Limit, to be printed.** Saved rows are per ground-truth tooth. A box matched to no tooth is
  not in them, so its code is unknown; the number of such boxes per detector is reported.
- **Wording.** In every lesion-agreement table the constant is described as placed by the
  pipeline's own boxes and numbering, with this row's precision and reach beside it, whatever
  they are. No bar.

**Row P, fixed now.**

- **Gate P1 — harness.** The scorer with the loader added, run **without** the UFBA option on
  the Tufts test split with arm3c into a scratch directory, must give rows identical to the
  rows row A saved. The scratch output is discarded.
- **Gate P2 — handedness, from the labels alone.** In at least 99% of images, the mean x of the
  boxes labelled quadrants 1 and 4 must lie left of the mean x of quadrants 2 and 3, and the
  mean y of quadrants 1 and 2 above the mean y of quadrants 3 and 4. A failure stops the row
  before any model is run.
- **Gate P3 — leakage.** MD5 and a 256-bit difference hash of all 425 images against the Tufts
  radiographs, every DENTEX release folder on this machine and the Kaggle "dual" images. A
  byte-identical image, or one within Hamming distance 10, is excluded and listed. More than 20
  exclusions stops the row.
- **Images.** Primary: as distributed, 640×640. The export is square and the original aspect
  ratio is not recorded in its metadata (the segmentation images are 512×512). Secondary, a
  sensitivity analysis only: each image widened to 1991:1127, the frame size the source
  collection reports, which has not been verified for these files. **The primary is the
  as-distributed figure whatever the secondary gives.**
- **Ground truth.** Every box in the YOLO label files, class c mapped to FDI
  (c // 8 + 1) × 10 + (c mod 8 + 1). All teeth, third molars included.
- **Reported, for each detector and each image treatment:** end-to-end exact FDI over all
  ground-truth teeth (primary), recall, exact of detected, quadrant correct of detected, each
  with a cluster interval; and the paired difference arm3c − `models/11`.
- **One pass.** A run directory that exists is refused, as for every row.
- **Wording.** The figure replaces "we have none on unseen data" (`main.tex`, Limitations),
  described as one corpus neither model trained on, an aspect-distorted 640×640 re-export,
  single pass. It is set beside Tufts 63.5% and DENTEX 92.8% with no claim that the three are
  comparable cohorts. If `models/11` scores above arm3c with an interval excluding zero, the
  paper says so in the same sentence. **The default does not change on any outcome of this row.**

**Forbidden,** in addition to §8: a second pass over UFBA-425 with another confidence, image
size, interpolation or aspect ratio; reporting the secondary treatment without the primary;
re-drawing row N's categories or row O's set after seeing them; any run on Ningxia.

## Amendment 4 — gate P2 corrected after it stopped row P (12 October 2026, 19:05 IST)

**What happened.** Gate P1 passed: the scorer with the UFBA loader reproduces row A's saved rows
byte for byte. Gate P3 passed: no UFBA-425 image is byte-identical to, or within Hamming
distance 62 of, any of 1,000 Tufts, 10,515 DENTEX or 500 Kaggle images. **Gate P2 failed, 404 of
425 images (95.1%) against 99%, and the row stopped before any model was run.**
`outputs/stage1_switch/P_ufba_gates_v1_failed/` keeps that output.

**Why, from the label files alone.** All 21 failing images lack labelled teeth in one arch or on
one side, so one or both of the comparisons Amendment 3 wrote down has nothing to compare, and
the gate counted "undefined" as "inconsistent". Of the 419 images where at least one comparison
is defined, 419 satisfy every defined one. Six images label teeth on one side of one arch only
and define neither. No image is reversed.

**State when written.** No output of either detector on any UFBA-425 image exists. Rows N and O
have been read (they do not involve UFBA-425). The decision owner chose to amend and run.

**Gate P2, as it now stands.** For each image, each comparison is evaluated only if both of its
sides have a labelled tooth: quadrants 1 and 4 left of quadrants 2 and 3; quadrants 1 and 2
above quadrants 3 and 4. An image passes if every comparison it defines holds. **At least 99% of
the images that define a comparison must pass.** Images that define none are counted and
reported, and stay in the scored cohort: a radiograph with few teeth is still a radiograph, and
dropping it would select the cohort on its content.

Nothing else in Amendment 3 changes: the 425 images, both image treatments, the order of the
detectors, the single pass, the metrics and the wording.
