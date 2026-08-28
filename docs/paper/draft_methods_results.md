# Draft — Methods and Results

**Target:** ISBI 2027, 4 pages + references. This file is the *prose draft*; every number traces
to `../results/PAPER_MATERIAL.md` and `../results/RESULTS_LOG.md`. Section tags in brackets point
at the source so a reviewer question can be answered without re-deriving anything.

**Status:** first draft, 28 Aug 2026. Intro/Abstract deliberately unwritten — they should be
written last, from what the Results actually support.

**Budget:** Methods ~450 words, Results ~600 words. The binding constraint on this paper is what
to cut, not what to say. Anything below marked `[CUT-1]` goes first if we overrun, `[CUT-2]` next.

---

## 2. Methods

### 2.1 Pipeline

We evaluate a six-stage pipeline that maps a panoramic radiograph (OPG) to a per-tooth finding
record. **Stage 1** detects teeth with a YOLOv11l-seg model. **Stage 2** assigns each detection an
FDI two-digit code with a ResNet18 head that consumes the crop plus four positional features,
resolved to a one-to-one assignment by the Hungarian algorithm. **Stages 3 and 4** classify caries
and periodontal bone loss per tooth with independent ResNet18 branches. **Stages 5–6** fuse the
per-stage outputs on the FDI key and emit a structured record.

The design commitment is that every stage is small and separately auditable: the pipeline totals
~25 M parameters and runs at 2.39 s per image on CPU with no GPU. We return to that figure in
Section 3.5, because it is the basis of the only comparison in this paper we win outright.

### 2.2 Data

Three corpora, all split **image-level** — two crops from one radiograph are not independent, and
a tooth-level split leaks the same mouth across train and test. Detection and bone loss use the
**Tufts Dental Database** (1,000 OPGs, frozen 700/150/150). Caries uses **DENTEX**. FDI numbering
trains on DENTEX + Tufts, with a third corpus evaluated as an ablation (Section 3.6).

Two label defects had to be established before use, and both are reported because assuming either
would have produced a plausible wrong result. Tufts' tooth numbering is **left–right mirrored**
relative to Universal notation (Tufts "1" is FDI 28, not 18), confirmed three independent ways
[§8.8b]. The third corpus was checked the same way rather than trusted: using the two-corpus head
as an independent arbiter over 915 teeth, agreement was **80.3% reading labels as written vs 1.7%
mirrored** [§8.23].

**External test data.** Ningxia (four hospitals) is locked: never trained on, never tuned against,
and touched a bounded number of times [§8.12].

### 2.3 Crop contract and thresholds

All classifier inputs are expanded crops resized to 224×224. The crop contract is fixed per branch
and identical across corpora — 1.5× symmetric for the numbering head, 1.5×W/2.0×H for bone loss,
since teeth are ~3× taller than wide and horizontal over-expansion bleeds into neighbours [§6.1].

Operating points are **pre-registered**. The assessability threshold
(`ASSESSABILITY_MIN_FDI_CONFIDENCE = 0.30`) was fixed a priori and is reported where it lands on
the coverage–accuracy curve rather than tuned against it (Section 3.4). `[CUT-2]`

---

## 3. Results

### 3.1 Detection (Stage 1)

On the held-out Tufts test split (150 images, 3,930 instances) the seg detector reaches **box
mAP@0.5 0.810**, improving +2.8 points over a bbox-supervised detector on the same split (0.782).
Mask quality reached 0.638 against a **pre-registered bar of 0.65**; the bar was not moved after
the fact, the model was adopted for its boxes alone by dated human decision, and mask-aware
cropping remains unwired as a consequence [§7.1].

`[CUT-1]` A first detection run was withdrawn rather than reported: it trained 90 clean epochs on
masks misaligned by two independent defects, caught only by treating a val mAP of 0.258 against an
expected 0.834 as a defect to explain. Median label IoU went 0.000 → 0.837 after the fix. *A
falling loss curve is not evidence of correct data.*

### 3.2 Tooth numbering (Stage 2) — the headline is detection-bound

End-to-end FDI-exact accuracy is **58.3% [53.9, 62.8]** (cluster-bootstrapped over images). This
number is **detection-bound, and must be reported as two numbers**: 29.4% of ground-truth teeth are
never detected, and **of the 661 teeth Stage 1 does find, Stage 2 numbers 82.6% correctly** [§8.16].

The residual errors are mostly benign: **77.4% are off-by-one** position errors within the correct
quadrant, and only **2.4% of detected teeth** suffer a quadrant-level category error.

### 3.3 Disease branches

The caries branch reaches **44.3% lesion-localisation agreement** on DENTEX. The bone-loss branch
reaches **0.923 macro-F1 in-domain** (Tufts, 1,558 crops at the untouched 4% prevalence) — and does
not survive domain shift: it fires on 0.7% of DENTEX teeth and 2.4% of Ningxia teeth. We report
this as a **measured limitation rather than a fixed problem** [§8.13]; a detector swap that moved
Stage 2 by +12.0 and caries by +7.7 moved bone loss by nothing, falsifying the shared-root-cause
hypothesis.

### 3.4 Calibration and abstention

The caries gate's confidences are **not probabilities**: ECE 0.136, systematically overconfident.
Temperature scaling made it worse — the miscalibration is structural, not a scale factor — while
isotonic regression fixes it (**ECE 0.043**) and is wired confidence-only, leaving verdicts
byte-identical [§8.15].

Abstention then buys real accuracy. Declining the least-confident quarter lifts Stage 2 from
**0.826 → 0.885** (+5.91 pp [+3.88, +7.68]) and the caries gate from **0.797 → 0.940**
(+14.25 pp [+11.32, +16.63]). Shuffling the confidences collapses both gains to ~0, establishing
that the rise comes from the ranking rather than from discarding items. The pre-registered 0.30
threshold lands at **90.8% coverage / 0.847**, within 0.2 pp of the empirical 90% point [§8.21].

**Caveat that must survive editing:** Stage-2 coverage is over *detected* teeth. 75% coverage is
75% of 70.6% — **53.0% of teeth actually present**.

### 3.5 External validation and the VLM comparison

Across four Ningxia hospitals, caries lesion agreement is **28.8–51.3% (40.8% pooled)** against
44.3% internally — an internal/external gap of 3.5 pp, less than half the 8.9 pp of the previous
detector [§8.12a].

Against a general-purpose VLM on the same 164 leak-free images, one scorer: our pipeline **F1
0.294**, Qwen2.5-VL-32B **0.246**, Qwen2.5-VL-7B **0.149**. Few-shot prompting makes the VLM
monotonically *worse* (0.066 at 2-shot, 0.034 at 4-shot) because in-context examples teach it to
abstain — 123 of 164 answers are empty at 4-shot [§8.22]. Both models return a confident,
dental-specific answer to a **random-noise image**.

**The result that constrains this comparison, and which we report rather than omit:** a fixed list
of the eight first and second molars — fitted on held-out images, never on the scored set — scores
**F1 0.320**, above our 0.294. Caries in DENTEX is overwhelmingly molar, so tooth-level FDI-set F1
is **base-rate dominated and cannot on its own demonstrate clinical value**. What survives intact
is the efficiency claim: 33.45 B parameters and 70 GB of H100 VRAM lose to ~25 M parameters on a
CPU.

### 3.6 Third-corpus ablation

Adding a third FDI corpus, against a control trained the same day on identical data, gives
**DENTEX +1.14 pp [+0.33, +1.95]** (p=0.013, paired, bootstrapped over source images), **Tufts flat**
(+0.74 pp, CI crossing zero), and no regression anywhere [§8.23]. `[CUT-2]`

---

## Notes for the next editing pass

1. **§5.7 of PAPER_MATERIAL is stale** — it says Stages 5–6 are "designed, not built". They have
   been built since R4 (`scripts/run_inference.py`). Do not copy that phrasing forward.
2. **§5.2 references a Universal→FDI mapping defect as open.** It was fixed (`f8b31f8`) and
   regression-tested. Verify before citing.
3. **Phase-1 caries gate numbers are missing** from the saved notebook [§7.2]. Either re-derive or
   omit — do not quote a number without an output cell behind it.
4. The molar-constant result (3.5) may deserve promotion into the Discussion as a
   *metric* contribution rather than sitting inside the VLM comparison.
