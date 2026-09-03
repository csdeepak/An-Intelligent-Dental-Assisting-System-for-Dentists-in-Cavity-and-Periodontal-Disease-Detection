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
- **The Guard-2 failure is exactly the pre-registered "domain dilution", and we now have its
  mechanism:** with Tufts at 33 % of the training mix, the detector **misses ~35 % more Tufts
  teeth (FN 1045 → 1427) and emits ~40 % more spurious boxes (FP 1058 → 1506)** at the same
  confidence. Localisation of the teeth it *does* find is fine (matched-pair IoU 0.62 → 0.64,
  unchanged). It is a **detection-confidence / capacity** effect, monotonic in Tufts training
  share: 100 % → 0.724, 52 % (Lever 1) → 0.647, 33 % (Lever A) → 0.585.
- **The single biggest lever on Tufts box quality is not the corpus mix at all — it is masks.**
  The *deployed* model is segmentation and scores **0.810**; every detection model here — even
  Tufts-only Control B — scores ≤ 0.724 because box supervision on Tufts is worse than mask
  supervision. DENTEX/Kaggle/UFBA have no masks, so the levers are forced to `detect`.
- **Recommendation: stop detector work. The diagnosis is a clean, quantified paper result.**
  Do the zero-GPU Phase-0 confirmations, fold the mechanism into the manuscript as a strengthened
  ablation, and move to **Lever B**. A genuine "another way" exists (multi-corpus *segmentation*
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

### 1.5 Hypothesis B — Tufts label hygiene — real but minor

Tufts boxes come from the original Labelbox export (`teeth_bbox.json`, Dec 2021), **not** from
masks. The builder applies its `MIN_PX = 2` degenerate-box filter to the *rotated* corpora only;
**Tufts is copied through unfiltered**. Result:

- raw Tufts: 66 / 26 005 boxes (0.3 %) have a side < 2 px;
- built Tufts **train**: 21 degenerate boxes (DENTEX/Kaggle/UFBA: 0);
- built Tufts **test** (Guard-2 GT): **4 / 3 924 (0.10 %)** un-matchable boxes → a ~0.1 pp
  guaranteed-FN tax on every model equally.

Plus every model predicts Tufts boxes ~20–36 % taller than GT (§1.3), which means the Tufts GT
boxes themselves are systematically short (crown-biased) relative to what a detector trained on
any mix of corpora considers a tooth. This **caps the achievable Tufts box mAP for everyone**
(hence the deployed seg model only reaching 0.81, Control B only 0.72) but does not explain why
Arm 3C < Control B.

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

| # | step | verify |
|---|---|---|
| 0.1 | Move the three diagnostic scripts into `models/15_detector_multicorpus_leverA/repro/diagnostics/` and commit. | scripts run from a clean checkout |
| 0.2 | Overlay 15 Tufts + 15 DENTEX GT boxes on their images, save to `_check/`. | visual: confirm/deny DENTEX boxes include more root than Tufts (settles §1.3's GT-stat question qualitatively; does not change the model-level conclusion) |
| 0.3 | Re-run the §1.4 greedy-match FN/FP/IoU diagnostic for Arm 4C too, and at conf ∈ {0.10, 0.25, 0.40}. | monotonic: Arm 4C FN/FP ≥ Arm 3C ≥ Control B at every threshold → dilution confirmed, not a threshold artefact |
| 0.4 | Write the finding into `PAPER_MATERIAL.md` §8.10 (mechanism: FN +37 %, FP +42 %, localisation flat, monotonic in share; seg-vs-box ceiling 0.81 vs 0.72) and note the Tufts-label height bias + the unfiltered degenerate boxes in §8 Known Limitations. | §8.10 reads as a quantified ablation, not "dilution (vague)" |
| 0.5 | `RESULTS_LOG.md` entry (diagnosis, no new model); `transfer.md` §5 council summary; session-memory. | house rules 1–2, 5 |

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
