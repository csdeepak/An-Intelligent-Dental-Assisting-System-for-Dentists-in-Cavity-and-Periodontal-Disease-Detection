> **SUPERSEDED — 6 September 2026. Do not quote a number from this file.** This is the
> 28 Aug 2026 spine. The argument it redrafted did land, and `paper/main.tex` carries it;
> this file's numbers predate the 4 Sep Lever B adoption. Specifically stale: Stage 3a is
> described as the **caries gate** (a lesion detector is the default since 4 Sep,
> `RESULTS_LOG` 2026-09-04h); **0.488** is the pre-Lever-B constant-vs-pipeline lesion
> agreement; **61.2 M** parameters is the gate path, not the shipped default (75.29 M;
> 97.65 M across all six models, re-counted 4 Sep). Kept per `CLAUDE.md` rule 3.

# Paper spine — redrafted 28 Aug 2026

**Supersedes the framing in `draft_methods_results.md`.** That draft's Methods survive almost
unchanged; its Results ordering does not. The reason for the change is in `RESULTS_LOG.md`
2026-08-28d: the plan to rescue the caries claim by switching metrics **failed under test** —
an image-blind constant beats the pipeline on the replacement metric too, significantly.

**Target:** journal (CiBM / Dentomaxillofacial Radiology; fallback *Scientific Reports*).
A journal, not a 4-page conference, because this argument needs the baselines shown, not cited.

---

## 1. The claim, in one sentence

> On panoramic radiographs, tooth-level caries metrics are dominated by anatomical priors: a
> specialist pipeline, a 33 B vision-language model, and a fixed list of eight molars that never
> reads the image are statistically indistinguishable — or favour the constant.

Everything else in the paper is either evidence for that, or the honest characterisation of the
system used to produce it.

## 2. Why this is the spine and the pipeline is not

The pipeline's caries branch scores 0.294 (FDI-set F1) and 0.443 (lesion agreement). Those are
unremarkable numbers, and defending them as a diagnostic contribution invites exactly one
reviewer question that we cannot answer: *does it beat a trivial baseline?* It does not.

But the reason it does not is a **finding**, not a failure — and it is one that generalises past
this project. It is supported here by three independent system classes and two unrelated metric
families, with intervals on every comparison. That is a stronger, more novel contribution than
another mid-range caries number.

The pipeline stays in the paper as the **vehicle and the honest case study**, and it keeps the
capabilities a constant genuinely cannot reproduce (Section 5.2).

## 3. Contributions, as they should be listed

**C1 — A constant-baseline protocol for tooth-level OPG evaluation.** We show that on DENTEX,
across two metric families, an image-blind constant matches or beats a specialist pipeline and two
general-purpose VLMs. We propose that a constant-baseline row is reported alongside any
tooth-level caries metric on this class of data.

**C2 — A VLM baseline with the control that makes it interpretable.** Qwen2.5-VL at 7 B and 33 B,
zero-shot and few-shot, scored by one scorer against the same images. Few-shot makes it
monotonically *worse*; blank and noise images elicit confident dental answers.

**C3 — External validation across four hospitals.** Rare in this literature (2 of 49 task-relevant
papers in our review), and reported with per-hospital spread rather than a pooled figure alone.

**C4 — Calibration and abstention.** The caries gate's confidences are not probabilities
(ECE 0.136); isotonic regression fixes it (0.043); abstention then buys real accuracy, with a
shuffle control proving the gain comes from the ranking.

**C5 — The pipeline**, characterised honestly, including a numbering stage that is
detection-bound and a bone-loss branch that does not survive domain shift.

## 4. Section plan (journal, ~5,000 words)

| § | content | words | notes |
|---|---|---|---|
| 1 | Introduction — build to C1 | 700 | write LAST |
| 2 | Related work + the review sheet (2/49 externally validated) | 500 | §2.1 |
| 3 | Methods — pipeline, data, crop contract, pre-registration | 900 | from old draft, near-unchanged |
| 4 | **Evaluation protocol — the baselines** | 500 | **new; C1 lives here** |
| 5 | Results | 1,400 | reordered, below |
| 6 | Discussion | 800 | what C1 means for the field |
| 7 | Limitations | 400 | §8 |
| 8 | Ethics / data statement | 200 | §8.19 — IRB gated |

## 5. Results, in the new order

### 5.1 The baselines (lead here)

Two metric families, one scorer per family, 164 leak-free DENTEX images.

**Tooth-level FDI-set F1**

| system | P | R | F1 |
|---|---|---|---|
| **Held-out molar constant — image never read** | 0.218 | 0.600 | **0.320** |
| Our pipeline | 0.235 | 0.390 | 0.294 |
| Qwen2.5-VL-33B zero-shot | 0.250 | 0.243 | 0.246 |
| Qwen2.5-VL-8B zero-shot | 0.248 | 0.107 | 0.149 |

**Lesion-localisation agreement** — chosen *because* it demands spatial correspondence, and
reported here even though it does not favour us:

| system | agreement | teeth flagged | match rate |
|---|---|---|---|
| **Molar constant** | **0.488** | 859 | 0.272 |
| Our pipeline | 0.443 | 755 | 0.281 |
| Flag every tooth (ceiling) | 0.722 | 3,344 | 0.103 |

The constant's advantage is **+4.59 pp [+0.60, +8.89]**, paired bootstrap over images. It is not
won by brute force: 14% more teeth flagged at the same match rate.

**This is the paper's central result.** Two metric families designed to measure different things
agree: tooth-level caries decisions on this data are dominated by the molar prior.

### 5.2 What the constant cannot do — the pipeline's real capabilities

Stated immediately after 5.1, because the contrast is the argument.

- **FDI numbering: 82.6% of detected teeth** (58.3% end-to-end [53.9, 62.8]; 29.4% of teeth are
  never detected, so both numbers are reported). A constant cannot perform this task at all.
  77.4% of residual errors are benign off-by-one; 2.4% of detected teeth are category errors.
- **Abstention works.** Declining the least-confident quarter: Stage 2 0.826 → 0.885
  (+5.91 pp [+3.88, +7.68]); caries gate 0.797 → 0.940 (+14.25 pp [+11.32, +16.63]). **Shuffling
  the confidences collapses both to ~0** — the gain is in the ranking, not the discarding.
- **Calibration is fixable and was fixed.** ECE 0.136 → 0.043 (isotonic); temperature scaling made
  it *worse*, showing the miscalibration is structural rather than a scale factor.

### 5.3 The VLM comparison

Pipeline 0.294 > 33 B 0.246 > 8 B 0.149 — **but all three sit below the constant's 0.320**, which
is the point. Few-shot degrades the VLM monotonically (0.066 at 2-shot, 0.034 at 4-shot): in-context
examples teach it to abstain, with 123 of 164 answers empty at 4-shot. Blank and random-noise images
both elicit confident, dental-specific answers.

Efficiency survives intact and is worth stating: 33 B parameters and 70 GB of GPU memory lose to
61.2 M parameters on a CPU.

### 5.4 External validation

Caries lesion agreement across four Ningxia hospitals: **28.8–51.3% (40.8% pooled)** against 44.3%
internally — an internal/external gap of 3.5 pp, less than half the previous detector's 8.9 pp.
Report the per-hospital spread; the pooled number hides a factor of 1.8.

### 5.5 Detection and numbering (supporting)

Box mAP@0.5 **0.810** on held-out Tufts, +2.8 over a bbox-supervised detector. The pre-registered
mask bar (0.65) was **missed** (0.638); the bar was not moved, the model was adopted for boxes only
by dated decision, and mask-aware cropping stays unwired as a consequence.

### 5.6 Where the pipeline fails (kept in Results, not exiled to Limitations)

Bone loss reaches 0.923 macro-F1 in-domain and **collapses out of domain** — firing on 0.7% of
DENTEX and 2.4% of Ningxia teeth. A detector swap that moved Stage 2 by +12.0 and caries by +7.7
moved bone loss by **nothing**, falsifying the shared-root-cause hypothesis.

## 6. Discussion — the three beats

1. **Why the prior dominates.** Caries in DENTEX is overwhelmingly molar. Any tooth-level decision
   inherits that base rate, so tooth-level metrics have low headroom above an anatomical prior.
2. **What the field should do.** Report a constant-baseline row. It costs nothing, and without it a
   mid-range tooth-level number is uninterpretable — our own three systems demonstrate exactly that
   ambiguity.
3. **What still separates a system from a prior.** Tasks a constant cannot express: numbering,
   calibrated confidence, principled abstention, and behaviour under domain shift. We argue these
   are the axes on which OPG systems should be compared.

## 7. Scope discipline — do not overclaim

The finding is demonstrated **on DENTEX, for caries, under tooth-level metrics**. We have **not**
shown that published caries results are wrong, and must not imply it. The defensible statement is
that *a number in this range, reported without a constant baseline, cannot be distinguished from
an anatomical prior* — which is a claim about evidence, not about other authors' systems.

Ningxia has a different caries distribution; whether the constant transfers there is **untested**.
`lesion_localization.py --decision constant-molars` will run it when C2 is next touched, and that
result should be in the paper if the touch budget allows.

## 8. What changes vs the previous draft

- Results **lead with the baselines**, not with detection.
- The constant moves from a caveat inside the VLM section to **the paper's central result**.
- Caries accuracy is **no longer claimed as a contribution**.
- Bone loss stays in Results as a measured negative rather than being demoted to Limitations.
- Methods are **unchanged**; only their placement and the framing around them move.

## 9. Open items before writing prose

1. Run the constant arm on **Ningxia** — the one experiment that would materially strengthen C1.
2. Decide whether to keep bone loss in the paper at all. Current recommendation: keep, as a
   measured negative; it is evidence for the domain-shift argument in 6.3.
3. Phase-1 caries gate numbers still have no saved output cell — re-derive or omit.
4. `PAPER_MATERIAL.md` §5.7 ("Stages 5–6 designed, not built") and §5.2 (Universal→FDI defect
   "open") are **stale** and must not be copied forward.
