# Why does Lever A's Tufts test box mAP fall while every other cohort rises? — diagnosis + council

**Date:** 3 September 2026 · **Status:** diagnosis complete (local CPU eval, no GPU) · **Decision: recommended below, pending user/mentor sign-off**

Follow-up to `STATUS.md` / `RESULTS_LOG.md` 2026-09-03 + 03b. Lever A stays **ABLATION** — this
document does **not** re-open the frozen pre-registration or move any bar. It answers the
question the user asked after seeing the result:

> On Tufts test box mAP it decreases and on everything else it improves. Is there another way,
> like how we did the bounding boxes for Tufts — can we change it? What is the mistake with
> Tufts? Check and verify. Make a plan. Council this.

---

## TL;DR

- **There is no bug and no fixable data-prep mistake.** I hypothesised a box-annotation-convention
  mismatch (Tufts GT boxes are mask-tight, DENTEX GT boxes look ~1.5× larger) and **tested it
  directly against the trained models — the hypothesis is refuted.** Arm 3C's predicted boxes on
  Tufts test are *closer* to Tufts GT in size and shape than Control B's, not further.
- **The Guard-2 failure is the pre-registered "domain dilution", and the Phase-0 sweep (§1.4b)
  pins the mechanism: a confidence-calibration collapse on the minority domain.** At low
  confidence the multi-corpus arms find as many Tufts teeth as Control B (Arm 4C recall 0.80 vs
  0.77) — the detector *sees* them — but the confidence score no longer separates real teeth
  from spurious boxes, so raising the threshold to clear the false-positive flood also kills the
  true positives (recall drop 0.10 → 0.40 conf: Control B −0.11, Arm 3C −0.29, Arm 4C −0.45).
  mAP@0.5 (Guard 2) is a ranking metric, so it breaks hardest: **0.724 → 0.585 → 0.552,
  monotonic in Tufts training share** (100 % / 33 % / 25 %; Lever 1 at 52 % was 0.647).
  Matched-pair IoU is **flat across the whole sweep** — localisation is not the loss.
- **The single biggest lever on Tufts box quality is not the corpus mix at all — it is masks.**
  The *deployed* model is segmentation and scores **0.810**; every detection model here — even
  Tufts-only Control B — scores ≤ 0.724 because box supervision on Tufts is worse than mask
  supervision. DENTEX/Kaggle/UFBA have no masks, so the levers are forced to `detect`.
- **Recommendation: stop detector work. The diagnosis is a clean, quantified paper result.**
  **Phase 0 is done (4 Sep)** — the sweep + overlays are in `repro/diagnostics/`, the mechanism
  is folded into `PAPER_MATERIAL.md` §8.16 (+ §8.9 for the Tufts-label findings), `RESULTS_LOG`
  2026-09-04. Next is **Lever B**. A genuine "another way" exists (multi-corpus *segmentation*
  with pseudo-masks) but it is a Lever-D-scale effort that belongs behind Lever B and behind
  Track A, and only if an adoptable multi-corpus detector is worth a full downstream re-run.

---

## 1 · What was checked and verified

All local, CPU/MPS, on the existing `models/15` weights + the built `data/detector_multicorpus_v2/`.
Scripts in `models/15_detector_multicorpus_leverA/repro/diagnostics/`.

### 1.1 The Guard-2 numbers, broken out (from `leverA_train.log`)

| arm | Tufts test | P | R | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|---|
| Control B (Tufts-only detect, 700) | 150 img / 3 924 box | 0.718 | 0.696 | **0.7243** | 0.270 |
| Arm 3C (Tufts+DENTEX+Kaggle, 2100 bal) | | 0.594 | 0.631 | **0.5852** | 0.210 |
| Arm 4C (+ UFBA, 2800 bal) | | 0.529 | 0.653 | **0.5520** | 0.199 |

Both **precision and recall** fall by ~0.10 from Control B to Arm 3C. mAP@0.5 and mAP@0.5:0.95
fall in roughly the same *proportion* (−19 %, −22 %) — i.e. the loss is not concentrated at
strict IoU, which already argues against a box-tightness explanation.

### 1.2 Reference points the pre-registration did not put in the table

| model | task | Tufts frozen **test** box mAP@0.5 | source |
|---|---|---|---|
| `models/11_yolo_seg_tufts_r1` — **the deployed detector** | segmentation | **0.8100** | its pre-reg, `model_metrics.md` §"Stage 1 · Tufts" |
| `models/06` old bbox detector (superseded) | detect | 0.7824 | same frozen split |
| Lever 1 Control B (Blackwell retrain) | detect | 0.724 | `RESULTS_LOG` 2026-09-01h |
| Lever A Control B (Blackwell retrain) | detect | 0.7243 | this run |
| Lever 1 Arm (Tufts 52 %) | detect | 0.647 | `RESULTS_LOG` 2026-09-01h |
| Lever A Arm 3C (Tufts 33 %) | detect | 0.5852 | this run |

Two things fall out of this that the Guard-2 line alone hides:
- **seg → detect costs ~9 pp on this metric** (0.810 → ~0.72–0.78) *before any corpus is added*.
  The multi-corpus arms are measured from a base well below what is actually deployed. The
  pre-registration compares Arm to **Control B** (detect), which is the right control for the
  *data* question — but "0.585 vs 0.810 deployed" is not the real gap, "0.585 vs 0.724" is, and
  even that sits on a weak baseline.
- The decline is **monotonic in Tufts training share**, across two independent builds.

### 1.3 Hypothesis A — box-convention mismatch — TESTED AND REFUTED

GT box statistics in the built dataset (normalised, letterboxed frame) *did* look like a
convention clash:

| corpus | box/img | median box area (% img) | median w/h |
|---|---|---|---|
| tufts | 25.9 | **0.628** | 5.11 |
| dentex | 28.5 | **0.935** (×1.49) | 6.13 |
| kaggle | 26.3 | 0.666 | 5.20 |
| ufba | 27.3 | 0.938 | 4.27 (distorted export) |

DENTEX GT boxes are ~1.5× the area of Tufts/Kaggle and longer along the tooth axis (consistent
with including more root). So the natural hypothesis: Arm 3C, trained 33 % on each, learns a
*blended* box size that is too big for Tufts and Tufts strict-IoU mAP collapses.

**Direct test on the trained models** — predicted box area on the 150 Tufts test images:

| source | box/img | median predicted box area (% img) |
|---|---|---|
| Tufts GT | 26.2 | 0.621 |
| Control B (Tufts-only) | 26.2 | **0.933** — already 50 % oversized vs its own GT |
| Arm 3C | 26.7 | **0.770** — *closer* to GT than Control B |
| Arm 4C | 27.0 | 0.667 — closest to GT |

And matched-pair geometry (greedy IoU match, conf 0.25):

| | Control B | Arm 3C |
|---|---|---|
| matched-pair IoU, median | 0.624 | **0.643** (better) |
| matched-pair IoU, p10 | 0.531 | 0.530 (same) |
| pred / GT width ratio | 1.05 | 1.03 |
| pred / GT **height** ratio | **1.36** | **1.17** (Arm 3C closer to 1.0) |

**Adding corpora made Arm 3C's boxes *better* shaped and better localised, not worse.** The
box-convention hypothesis is wrong. (All models predict ~20–36 % *too tall* — a shared quirk,
discussed in §1.5, not the differential cause.)

### 1.4 What actually happens — the mechanism (greedy match on Tufts test, conf 0.25)

| | Control B | Arm 3C | change |
|---|---|---|---|
| matched teeth (TP) | 2 879 | 2 497 | **−382** |
| missed teeth (FN) | 1 045 | 1 427 | **+382 (+37 %)** |
| spurious boxes (FP) | 1 058 | 1 506 | **+448 (+42 %)** |
| precision | 0.731 | 0.624 | −0.107 |
| recall | 0.734 | 0.636 | −0.098 |

Localisation is unchanged; **detection and confidence degrade**. With Tufts at one-third of the
mix the model is simply a weaker Tufts detector — it fails to fire on more real Tufts teeth and
fires with lower/misplaced confidence elsewhere. This is textbook capacity dilution, and it is
**exactly the risk the pre-registration named** ("domain dilution risk #2").

### 1.4b Phase 0 (4 Sep 2026) — the sweep sharpens this to a *confidence-calibration* failure

`repro/diagnostics/iou_diag_sweep.py` — same greedy match, all three arms × conf ∈ {0.10, 0.25, 0.40}:

| arm (Tufts train share) | conf | TP | FN | FP | P | R | matched IoU (median) |
|---|---|---|---|---|---|---|---|
| Control B (100 %) | 0.10 | 3027 | 897 | 1531 | 0.664 | 0.771 | 0.623 |
| Control B (100 %) | 0.25 | 2879 | 1045 | 1058 | 0.731 | 0.734 | 0.624 |
| Control B (100 %) | 0.40 | 2597 | 1327 | 783 | 0.768 | 0.662 | 0.625 |
| Arm 3C (33 %) | 0.10 | 2929 | 995 | 2694 | 0.521 | 0.746 | 0.645 |
| Arm 3C (33 %) | 0.25 | 2497 | 1427 | 1506 | 0.624 | 0.636 | 0.643 |
| Arm 3C (33 %) | 0.40 | 1804 | 2120 | 967 | 0.651 | 0.460 | 0.643 |
| Arm 4C (25 %) | 0.10 | 3143 | 781 | 3377 | 0.482 | 0.801 | 0.683 |
| Arm 4C (25 %) | 0.25 | 2467 | 1457 | 1586 | 0.609 | 0.629 | 0.676 |
| Arm 4C (25 %) | 0.40 | 1378 | 2546 | 668 | 0.674 | 0.351 | 0.674 |

Three things, and the third is the finding:

1. **Matched-pair IoU is flat at every threshold** (0.62 / 0.64 / 0.68) — if anything the
   multi-corpus arms localise *slightly better*. Localisation is definitively not the loss.
   This is the robust result and it holds across the whole sweep.
2. **At low confidence (0.10) the multi-corpus arms find as many Tufts teeth as Control B or
   more** — Arm 4C recall 0.801 vs Control B 0.771 — but with a flood of false positives
   (Arm 4C FP 3377 vs Control B 1531). The detector *can* see the Tufts teeth.
3. **The confidence score has stopped separating real teeth from spurious boxes.** As the
   threshold rises 0.10 → 0.40, recall falls 0.11 for Control B, **0.29 for Arm 3C, 0.45 for
   Arm 4C** — filtering the false positives also kills the true positives, because the arm
   scores both about the same. mAP@0.5 (Guard 2) integrates the PR curve weighted by that
   ranking, so it is exactly the metric this breaks: **0.724 → 0.585 → 0.552, monotonic in
   Tufts training share.** The FN/FP split at a *fixed* threshold is threshold-dependent
   (FP-flooding at low conf, FN-collapse at high conf); the mAP number and the calibration
   collapse are what is monotonic.

So the mechanism is **not** "the model can't find Tufts teeth" and **not** "the boxes are the
wrong shape" — it is "with Tufts a minority of training, the model's confidence on Tufts
detections is no longer trustworthy," and a ranking metric punishes that hardest.

### 1.5 Hypothesis B — Tufts label hygiene — real but minor

Tufts boxes come from the original Labelbox export (`teeth_bbox.json`, Dec 2021), **not** from
masks. The builder applies its `MIN_PX = 2` degenerate-box filter to the *rotated* corpora only;
**Tufts is copied through unfiltered**. Result:

- raw Tufts: 66 / 26 005 boxes (0.3 %) have a side < 2 px;
- built Tufts **train**: 21 degenerate boxes (DENTEX/Kaggle/UFBA: 0);
- built Tufts **test** (Guard-2 GT): **4 / 3 924 (0.10 %)** un-matchable boxes → a ~0.1 pp
  guaranteed-FN tax on every model equally.

Plus, on the matched pairs, every model predicts Tufts boxes that hug the crown-to-root axis
(pred/GT long-axis ratio 1.03–1.05) but run **17–36 % wider mesial-distally than GT** (short-axis
ratio: Control B 1.36, Arm 3C 1.17). Tufts `teeth_bbox.json` is drawn tight to the tooth in the
narrow direction — tighter than a detector converges to, *even one trained only on Tufts*. Since
the boxes are ~5:1 thin, a 36 % short-axis error alone puts a concentric prediction at IoU ≈ 0.70,
so matched-pair IoU sits at ~0.62 and mAP@0.5:0.95 at ~0.27 for **everyone**. This **caps the
achievable Tufts box mAP** (deployed seg 0.81, any detect model ≤ 0.72) but does not explain why
Arm 3C < Control B — the calibration collapse in §1.4b does.

**Verdict on "the mistake with Tufts":** there is no build error that flipped the result. There
is (i) a fundamental capacity/dilution tradeoff — the confirmed cause — and (ii) a pre-existing
Tufts-label-quality ceiling that the box-supervised detection setup cannot escape and that the
deployed segmentation model partly does.

---

## 2 · Council

Five views on: *given the above, is any further detector work warranted, and if so what?*

### 2.1 The Reviewer (does it help or hurt the paper?)

The paper's thesis is "end-to-end numbers hide stage-wise failure; external validation is
almost never done." Lever A's ablation already supports that. **This diagnosis makes it
stronger, not weaker:** we can now write, with numbers, *why* a multi-corpus tooth detector
regresses on its benchmark corpus — not hand-waved "dilution" but "FN +37 %, FP +42 %,
localisation unchanged, monotonic in training share, and the benchmark metric itself is
mask-vs-box-capped." That is a genuinely useful negative result; a good reviewer rewards it.
A *fixed* multi-corpus detector that we then adopt would force re-measuring every pipeline
number in the paper under deadline — a large risk for a contribution that is not the paper's
spine. **Reviewer's call: report the diagnosis, do not chase the fix now.**

### 2.2 The ML Engineer (is there a fix that would actually work?)

- **Raising Tufts share back up** — tried at 52 % in Lever 1, still failed (0.647). To hold
  ~0.72 you likely need Tufts ≥ 70 %, which defeats the purpose (the other corpora stop
  contributing domain coverage). Dead end.
- **More data / bigger backbone / longer schedule** — capacity is the binding constraint, so
  this *could* lift all domains together, but Lever E ("bigger arch") was already judged
  marginal, and it is the most compute-hungry option.
- **Multi-corpus pretrain → Tufts-only fine-tune (last ~20 epochs)** — plausible: broad
  features, Tufts-specific calibration. But it produces a Tufts-specialised checkpoint; if it
  also has to stay good on DENTEX/external you are back to the same tradeoff, just with a
  better Pareto point. ~₹400, medium confidence.
- **Multi-corpus *segmentation* with pseudo-masks** (Tufts real masks + SAM/box-prompted masks
  for the others) — this attacks the *actual* ceiling (box vs mask supervision, the 0.81 vs
  0.72 gap) and matches the deployed model's task. Highest upside, highest effort — new data
  pipeline, mask-quality gating, ~₹800–1500. This is the honest reading of "another way, like
  how we did the bounding boxes for Tufts": use the masks Tufts already has.
- **Box-scale/jitter augmentation** — cheap (~₹300) but §1.3 shows box *shape* is not the
  problem, so expected value is low.

**Engineer's call:** only two options have real upside — pretrain→fine-tune (cheap, modest) and
multi-corpus segmentation (expensive, large). Neither is a small tweak.

### 2.3 The PI (schedule and budget)

Track A is the critical path: ISBI 2027 deadline 26 Oct, four compliance blockers unresolved,
authors still `Unknown` in `main.tex`. GPU balance ₹1,732. Lever B (the caries lever, and the
one that attacks the paper's *other* thesis directly) is unstarted, cheaper (~₹300 + a zero-GPU
arm), and more central. Spending the next block of time and ~₹600–1500 on a third detector
experiment — which even if it *passes* triggers a full downstream re-measurement — is the wrong
order. **PI's call: Phase 0 now (free), then Lever B. Detector work is post-Lever-B and
schedule-permitting only.**

### 2.4 The Skeptic (are we moving the goalposts?)

The pre-registration said adopt iff PRIMARY ∧ GUARD 1 ∧ GUARD 2. Guard 2 failed. Any of the
following would be goalpost-moving if done *to rescue Lever A*: re-scoring the existing arms
against a new, easier Tufts metric and calling it a pass; relaxing the −4 pp tolerance;
dropping Guard 2 because "the pipeline doesn't use box mAP." **The diagnosis must be reported
with the ablation verdict intact.** A *new* experiment (call it Lever A2) with its *own*
pre-registration, its own bars fixed before running, and the deployed detector staying
`models/11` until it passes cleanly — that is legitimate. The distinction is not cosmetic.

### 2.5 The Deployment Realist (what if we actually shipped this?)

For a screening tool on arbitrary panoramics, Arm 3C is **better on 5 of 6 cohorts** (DENTEX
+34 pp end-to-end, Ningxia +19, CariesXrays +6) and worse only on Tufts box mAP — a metric no
downstream stage consumes (the FDI head + Hungarian match at IoU 0.30, which Arm 3C clears
easily; that is why the *primary* soared). If the goal were shipping, Arm 3C is the better
detector and Guard 2 is the wrong gate. **But the paper is not a deployment** — it must keep
every already-published Tufts number reproducible, which is precisely what Guard 2 protects.
Both statements are true; the paper says so in the discussion and keeps `models/11`.

### 2.6 Synthesis

Unanimous on the near term: **the diagnosis is the deliverable; no GPU on the detector now;
Phase 0 then Lever B.** The only open question is whether a *Lever A2* is ever worth it, and the
council's answer is "only if Lever B does not yield an adoptable positive headline **and** ≥ 2
weeks of schedule slack open up **and** someone decides an adoptable multi-corpus detector
justifies re-measuring the whole pipeline" — and if so, the candidate is **multi-corpus
pretrain → Tufts fine-tune** first (cheap probe), **multi-corpus segmentation** only if that
probe is promising.

---

## 3 · Plan

### Phase 0 — confirm and document the diagnosis (no GPU, ~half a day)

| # | step | status |
|---|---|---|
| 0.1 | three diagnostic scripts + README in `models/15_detector_multicorpus_leverA/repro/diagnostics/` | ✅ **DONE** (commit `044ed3b`) |
| 0.2 | GT-box overlays, Tufts vs DENTEX | ✅ **DONE 4 Sep** (`repro/diagnostics/gt_overlay.py` → `data/detector_multicorpus_v2/_check/gt_overlay/`, 24 panels, local-only; two examples kept in the diagnostics dir). **Confirms the box_conv.py stat visually:** DENTEX GT boxes are visibly larger and heavily overlapping, extending past the tooth into alveolar bone (`dentex_train_0` median box area 1.19 % img vs Tufts `1013` 0.64 %). Does not change the model-level conclusion — §1.3 stands. |
| 0.3 | greedy-match FN/FP/IoU sweep, 3 arms × conf {0.10, 0.25, 0.40} | ✅ **DONE 4 Sep** (`repro/diagnostics/iou_diag_sweep.py`) → **§1.4b**. Sharper finding: the loss is a **confidence-calibration collapse** on the minority domain, not FN or FP alone; matched-pair IoU flat across the whole sweep; mAP monotonic in Tufts training share. |
| 0.4 | fold into `PAPER_MATERIAL.md` — the mechanism (§1.4b) + the box-vs-mask ceiling → **§8.16**; the Tufts short-axis label tightness + the unfiltered degenerate boxes → **§8.9** | ✅ **DONE 4 Sep** (§8.10 was the wrong target — it is the numbering-head section; §8.16 already carries the Lever A write-up, §8.9 the Tufts box-annotation findings) |
| 0.5 | `RESULTS_LOG.md` 2026-09-04 entry (sweep numbers, no new model); `transfer.md` §1; session-memory | ✅ **DONE 4 Sep** |

**Phase 0 is complete.** Next: **Lever B** (the friend, Windows) and the Phase 1 gate below is
downstream of Lever B's result.

**Phase-0 success criterion:** a reviewer reading §8.10 can state, from numbers, why multi-corpus
tooth *detection* regresses on Tufts and what would be required to prevent it. No GPU spent.

### Phase 1 — decision gate (after Lever B reports)

Proceed to Phase 2 **only if all three hold**:
1. Lever B did **not** produce an adoptable positive headline; **and**
2. ≥ 2 weeks of schedule slack vs the Track-A critical path; **and**
3. explicit user/mentor decision that an adoptable multi-corpus detector is worth a full
   downstream re-measurement.

Otherwise: Lever A + this diagnosis are final. Done.

### Phase 2 — Lever A2, *if* Phase 1 clears (new pre-registration, bars fixed first)

**2a — cheap probe (~₹400):** multi-corpus (Tufts+DENTEX+Kaggle, balanced) for 130 epochs, then
**Tufts-only fine-tune for the last 20 epochs** at low LR. One arm + reuse Lever A Control B.
- *Pre-registered success:* Tufts test box mAP@0.5 ≥ Control B − 4 pp (0.6843) **and** DENTEX
  end-to-end FDI Δ vs Control A lower bound ≥ +5 pp **and** pooled external caries Δ ≥ −2 pp.
  I.e. the identical Lever A rule.
- If 2a passes → that becomes the adoption candidate, run the full downstream re-measure.
- If 2a fails → **stop.** Do not escalate to segmentation under deadline.

**2b — only if 2a is close (within ~2 pp) and schedule still allows (~₹1 000):** multi-corpus
**segmentation** — Tufts real masks + box-prompted SAM pseudo-masks for DENTEX/Kaggle, mask-IoU
gate on a Tufts holdout before training. Same pre-registered rule, plus a mask-quality report.

---

## 4 · Assumptions and open questions

- **Interpretation of "how we did the bounding boxes for Tufts".** Read here as "Tufts has
  segmentation masks; the mask-derived / mask-based route is the alternative to box supervision"
  (→ Phase 2b) **and** "can the box *definitions* be normalised across corpora" (→ tested in
  §1.3, refuted at the model level). If the user meant something else, say so and this plan
  adjusts.
- The §1.4 diagnostic used greedy IoU matching, not the COCO mAP integrator; it reproduces the
  log's P/R within ~0.02, so the FN/FP decomposition is trustworthy, but the exact mAP
  attribution to FN vs FP vs ranking is Phase-0 step 0.3.
- Whether a Tufts-only fine-tune retains the external-cohort gains (Guard 1) is unknown — that
  is the whole point of testing 2a, and its Guard-1 arm is mandatory.
- No end-to-end Tufts FDI evaluator exists (`validate_fdi_assignment.py` is DENTEX-only).
  Building one — a frozen Tufts FDI test split + leakage check — is ~1 day and would let a
  future guard measure "boxes good enough for the pipeline on Tufts" instead of raw box mAP.
  Noted, not scheduled.
