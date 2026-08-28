# Manuscript draft

**Working title:** *Anatomical priors dominate tooth-level caries metrics on panoramic
radiographs: a constant-baseline protocol and an externally validated pipeline*

**Target:** Computers in Biology and Medicine / Dentomaxillofacial Radiology.
Fallback: *Scientific Reports*. ~5,000 words.

**Status, 28 Aug 2026.** All sections drafted. Numbers marked `[NINGXIA-CONST]` await the
external constant arm (running). Everything else traces to `../results/PAPER_MATERIAL.md`.

---

## Abstract

*(Written last, from what the Results support. ~200 words.)*

Automated analysis of panoramic radiographs (OPGs) is usually evaluated with tooth-level metrics:
which teeth are carious. We show that on a public OPG dataset such metrics are dominated by
anatomical priors. Using one scorer and 164 leakage-free images, we compare a purpose-built
six-stage pipeline (~25 M parameters), two general-purpose vision-language models (8 B and 33 B),
and an **image-blind constant** — a fixed list of the eight first and second molars, fitted on
held-out data and never shown a radiograph. The constant scores **F1 0.320** against the
pipeline's 0.294 and the 33 B model's 0.246, and the result is not an artefact of one metric: on
a lesion-localisation metric requiring spatial correspondence, the constant again leads,
0.488 vs 0.443 (+4.59 pp, 95% CI [+0.60, +8.89]). We therefore argue that a constant-baseline row
should accompany any tooth-level caries metric on this class of data. We further report what a
constant provably cannot do — FDI tooth numbering (82.6% of detected teeth), calibrated confidence
(ECE 0.136 → 0.043), and principled abstention (+14.25 pp accuracy at 75% coverage, with a shuffle
control) — and external validation across four hospitals, and propose these as the axes on which
OPG systems should be compared.

---

## 1. Introduction

**Beat 1 — the setting.** OPGs are the most common extraoral radiograph in dentistry. Automated
caries and periodontal screening on them is an active area, and reported tooth-level accuracies
cluster in a range that is difficult to interpret without knowing what a trivial system would
score on the same data.

**Beat 2 — the gap.** Two features of OPG caries data make that interpretation hard. Caries is
**anatomically concentrated**: molars dominate. And tooth-level metrics ask a *set-membership*
question — which teeth — that a fixed anatomical answer can address without perception. Together
these give a high floor that is rarely measured. In our review of 49 task-relevant papers, **2**
report external validation, and none report a constant baseline.

**Beat 3 — what we do.** We build a six-stage OPG pipeline, evaluate it honestly, and then
evaluate three progressively less informed systems against it under the same scorer: a 33 B VLM, an
8 B VLM, and an image-blind constant. We report the result even though it does not favour our
system.

**Beat 4 — contributions.**
1. A **constant-baseline protocol** for tooth-level OPG evaluation, and evidence across two metric
   families that a specialist pipeline, a 33 B VLM and an image-blind constant are
   indistinguishable or favour the constant.
2. A **VLM baseline with the control that makes it interpretable** — including that blank and
   random-noise images elicit confident dental answers, and that few-shot prompting makes
   performance monotonically worse.
3. **External validation across four hospitals**, reported per site rather than pooled.
4. **Calibration and abstention** results, with a shuffle control isolating the mechanism.
5. An honest characterisation of the pipeline, including a numbering stage that is detection-bound
   and a bone-loss branch that does not survive domain shift.

**Beat 5 — what this is not.** We do not claim published caries results are wrong. We claim that a
tooth-level number reported without a constant baseline cannot be distinguished from an anatomical
prior — a statement about evidence, not about other systems.

---

## 2. Related work

*(From `PAPER_MATERIAL.md` §2.1 — comparison table built from the project's own review sheet.)*

Key framing sentences to keep:
- Of 49 task-relevant papers, **2 validate externally**.
- Independent confirmation that reported performance collapses out of domain (DPML: 95.06 mAP on
  own data → 61.83 on public DENTEX).
- YOLOv11 over YOLOv12 for dental detection is externally supported (Mutlu et al., *Odontology*
  2026), including the same subtle-pathology asymmetry we observe.
- **No paper in the sheet reports a constant or image-blind baseline.** This is the gap.

---

## 3. Methods

*(Carried from `draft_methods_results.md` §2, unchanged. Condensed here; see that file for full
prose.)*

**3.1 Pipeline.** Six stages: YOLOv11l-seg detection → FDI numbering (ResNet18 + 4 positional
features, Hungarian one-to-one) → caries cascade → bone-loss cascade → fusion → report.
~25 M parameters total, 2.39 s/image on CPU.

**3.2 Data.** Tufts (1,000 OPGs, frozen 700/150/150) for detection and bone loss; DENTEX for
caries; DENTEX + Tufts for numbering, with a third corpus as an ablation. **All splits are
image-level** — a tooth-level split leaks the same mouth across train and test.

Two label conventions were **established, not assumed**: Tufts numbering is left–right mirrored
relative to Universal, and the third corpus was verified as standard FDI by an independent arbiter
(80.3% direct vs 1.7% mirrored over 915 teeth).

**3.3 Crop contract.** Fixed per branch, identical across corpora: 1.5× symmetric for numbering,
1.5×W/2.0×H for bone loss (teeth are ~3× taller than wide).

**3.4 Pre-registration.** Operating points are fixed a priori and reported where they land, not
tuned against evaluation data. The detector's mask bar (0.65) was **missed** (0.638); the bar was
not moved, and the consequence — mask-aware cropping stays unwired — is reported.

**3.5 External data.** Ningxia (four hospitals) is locked: never trained on, never tuned against,
touched a bounded number of times.

---

## 4. Evaluation protocol — the baselines

This section is the paper's methodological core.

**4.1 The comparison.** All arms see the same 164 leakage-free DENTEX images and are scored by one
scorer per metric family. Any difference is the system, not the metric.

**4.2 The systems.**
- *Pipeline* — the six stages above.
- *VLM* — Qwen2.5-VL-8B and -33B, zero-shot, given FDI notation in the prompt, told teeth may be
  absent, and parsed permissively. Every affordance favours the VLM; our pipeline gets none.
- *Constant* — a fixed set of FDI codes, applied to every image, **never reading the pixels**.
  Fitted greedily on the 78 leakage-excluded images, disjoint from the scored set (overlap
  asserted zero), then frozen. A test-set-fitted oracle is also reported and labelled as such.

**4.3 The metrics.**
- *FDI-set F1* — per-image precision/recall/F1 over predicted vs ground-truth FDI code sets.
- *Lesion-localisation agreement* — of every expert-annotated lesion, was a tooth flagged that
  overlaps it. Chosen because it demands spatial correspondence; reported with its
  predicted-positive match rate, because agreement alone is recall and rewards flagging more.

**4.4 Controls.** For the VLM, a **blank grey** and a **random-noise** image, to test whether the
model conditions on pixels at all. For abstention, a **confidence shuffle**, to test whether gains
come from the ranking or from discarding items.

---

## 5. Results

*(Ordering per `draft_spine.md` §5. Full tables there; numbers repeated here in prose form.)*

**5.1 The baselines.** FDI-set F1: constant **0.320** > pipeline 0.294 > 33 B 0.246 > 8 B 0.149.
Lesion localisation: constant **0.488** > pipeline 0.443, a gap of **+4.59 pp [+0.60, +8.89]**
(paired bootstrap over images) achieved with only 14% more teeth flagged at the same match rate.
Flagging every detected tooth reaches 0.722, bounding the metric.

**5.2 What the constant cannot do.** FDI numbering 82.6% of detected teeth (58.3% end-to-end;
29.4% of teeth are never detected, so both are reported). Abstention: Stage 2 0.826 → 0.885,
caries gate 0.797 → 0.940, both collapsing to ~0 under confidence shuffling. Calibration:
ECE 0.136 → 0.043 by isotonic regression, with temperature scaling making it *worse* — the
miscalibration is structural.

**5.3 VLM behaviour.** Few-shot degrades monotonically (0.149 → 0.066 → 0.034); 123 of 164 answers
are empty at 4-shot. Blank and noise images both elicit confident dental answers. Efficiency:
33 B parameters and 70 GB of GPU memory lose to ~25 M parameters on CPU.

**5.4 External validation.** Four hospitals, caries lesion agreement **28.8–51.3% (40.8% pooled)**
against 44.3% internally. `[NINGXIA-CONST]` — the constant arm on the same four hospitals, which
determines whether §5.1 is a DENTEX property or a general one.

**5.5 Supporting.** Detection box mAP@0.5 0.810. Bone loss 0.923 macro-F1 in-domain, firing on
0.7% of DENTEX and 2.4% of Ningxia teeth out of domain — a detector swap that moved Stage 2 by
+12.0 and caries by +7.7 moved it by nothing.

---

## 6. Discussion

**6.1 Why the prior dominates.** Caries in DENTEX is anatomically concentrated in molars. A
tooth-level decision is a set-membership question, and set membership inherits that base rate
directly. The headroom above a fixed anatomical answer is therefore small — and crucially, it is
small *independently of how good the model is*. This is a property of the task-metric pairing, not
of any system.

That two unrelated metrics agree matters. FDI-set F1 and lesion-localisation agreement were
designed to measure different things; the second was adopted specifically because it demands
spatial correspondence. Both put the constant ahead. A single-metric result would be a metric
artefact; two are a property of the data.

**6.2 What the field should do.** Report a constant-baseline row. It costs one line of code and no
compute. Without it, a mid-range tooth-level number is uninterpretable — as our own three systems
demonstrate, spanning 0.149 to 0.320 with the *least* informed system at the top.

We are explicit that this does not invalidate prior work. It means a specific claim — *this system
perceives caries* — is not supported by a tooth-level number alone, and needs either a constant
comparison or a metric with more headroom.

**6.3 What still separates a system from a prior.** A constant cannot number teeth, cannot produce
a calibrated confidence, cannot abstain informatively, and has no behaviour under domain shift to
measure. Our pipeline does all four, and its results on those axes are meaningful in a way its
caries F1 is not. We propose these as the axes on which OPG systems should be compared:

1. **Identification** — can it say *which* tooth (82.6% of detected here)?
2. **Calibration** — are its confidences probabilities (ECE 0.136 → 0.043)?
3. **Selective prediction** — does declining improve accuracy, and is the gain in the ranking
   (shuffle control)?
4. **Domain shift** — measured on held-out hospitals, reported per site.

**6.4 On negative results.** Two findings here are negative about our own system: the constant
comparison, and a bone-loss branch that does not generalise. Both are reported because a screening
tool that fails silently is worse than one that fails visibly — and because the alternative,
selecting the metric that flatters the system, is the practice this paper argues against.

---

## 7. Limitations

1. **Single caries dataset for the constant result.** Demonstrated on DENTEX; the external arm
   `[NINGXIA-CONST]` tests transfer but on one further population.
2. **Tooth-level is the finest localisation this pipeline performs.** The lesion-localisation
   metric is a tooth-level correspondence check, not pixel-level segmentation quality.
3. **No clinician comparison.** We do not know how any of these systems compare to a dentist on
   these images. This is the single largest gap and is planned (Appendix A).
4. **Bone loss does not generalise** and is reported as a measured negative, not a component.
5. **One VLM family.** Qwen2.5-VL at two scales; a domain-tuned medical VLM was not accessible.
6. **Detection is below published benchmarks** (0.810 mAP@0.5), and Stage 2 is bounded by it.
7. **Ningxia lacks healthy controls**, so specificity and AUC are not computable there; we report
   lesion agreement and image-level sensitivity only.

---

## 8. Data, ethics and reproducibility statement

*(From `PAPER_MATERIAL.md` §8.19. **Gated on the compliance items — do not submit before these are
closed.**)*

- Datasets, licences, and the terms under which each was obtained.
- **IRB status** for the clinic data — required before any clinic-derived result appears.
- De-identification procedure and its verification.
- Code availability; model weights and hashes; the frozen splits, derived from code rather than
  carried as files.
- Statement that external test data was touched a bounded number of times, with dates.

---

## Appendix A — Reader study protocol (to run)

Designed so it can start the day IRB clears. Addresses Limitation 3, and is the item most likely
to move this from a solid paper to a strong one.

**Design.** 100 OPGs sampled from the leakage-free DENTEX set, stratified by lesion count
(0, 1–2, 3–5, 6+). Three readers: two general dentists, one with ≥5 years' experience.

**Task.** Identical to the machine task: list FDI codes of teeth showing caries. Same prompt
wording as the VLM arm, so all four arms answer one question.

**Blinding.** Readers see only the radiograph — no model output, no clinical history. Order
randomised per reader. No time limit, but time recorded.

**Analysis.**
- Score readers with the *same scorer* as every machine arm.
- **Include the constant in the comparison.** If the constant approaches human agreement, that is
  a far stronger version of this paper's claim; if humans clear it decisively, that quantifies the
  headroom the metric actually has — which is the number this paper currently lacks.
- Inter-reader agreement (Fleiss' κ) as the noise floor for the whole comparison.

**Sample size.** 100 images × 3 readers is powered to detect a ~10 pp difference at the observed
variance; smaller differences will not be claimed.

---

## Appendix B — Figures

| # | figure | source | status |
|---|---|---|---|
| 1 | Pipeline schematic, six stages | new | to draw |
| 2 | **Baseline comparison** — all arms, both metric families | `c1_comparison.json`, `lesion_loc_*` | **to draw — the paper's key figure** |
| 3 | Coverage–accuracy curves, both branches | `c4_coverage_accuracy.png` | exists |
| 4 | Reliability diagram before/after isotonic | §8.15 | exists |
| 5 | Per-hospital external agreement, pipeline vs constant | `ningxia_*` | pending arm |
| 6 | Stage-2 failure taxonomy | §8.16 | exists |
| 7 | Qualitative panel — VLM answers to blank/noise vs real | `control_pixels_*.json` | to draw |

Figure 2 is the paper. It should be readable in isolation: four systems, two metrics, constant
highlighted.

---

## Open items before submission

| item | owner | blocking |
|---|---|---|
| IRB | author | **yes** — ethics statement and reader study |
| Restrict Tufts Drive folder | author | **yes** — live licence breach |
| Record DENTEX + Ningxia licences | author | yes — Methods |
| Move SDH `metadata/index.csv` | author | yes — de-identification |
| Ningxia constant arm | running | §5.4, Figure 5 |
| Reader study | author + analysis | no, but decides S-grade odds |
| Phase-1 caries gate numbers have no saved output cell | analysis | re-derive or omit |
| Figures 1, 2, 7 | analysis | yes |
