# Publication Readiness To-Do

**Purpose:** a prioritised, concrete work list to get this capstone from "collection of trained models" to something submittable.
**Companion docs:** `gap_analysis.md` (literature + our weaknesses), `clinical_dataset_plan.md` (clinic dataset implementation plan).
**Date compiled:** August 2026. **Status reconciled:** 21 August 2026 — see the status block
below, which is the authority on what is actually done. Checkbox states inside the tiers were
never maintained; trust the block.

---

## STATUS AS OF 21 AUGUST 2026

> ⚠️ **DATED 21 AUGUST AND STALE FOR THE CARIES ITEMS. Corrected 27 Aug 2026.**
> **T0.2, T0.3 and T0.4 are CLOSED**, not open — the caries re-run landed **25 Aug**
> (`RESULTS_LOG.md` 2026-08-25b): checkpoint selection on val macro-F1, cosine schedule, and the
> held-out test split reported separately and touched once after selection. The shipped
> `caries-gate-resnet18-v3.0` is that run's arm B (`models/09_caries_gate_v3/run_summary.txt`).
> **`transfer.md` §2 is the accurate record.** Reading this block as current on 27 Aug nearly
> cost a GPU session re-running work that was already done.

Verified against the repo, not asserted. Every "done" here traces to a committed artifact.

| Item | State | What is actually true |
|---|---|---|
| **T0.1** augmentation | **CLOSED 25 Aug** | Both arms run on `crops_v3_phase1` (re-scoped from `phase1_legacy`, which is superseded). Val macro-F1: A 0.7210, B 0.7350; test: A 0.7212, B 0.6948. **Gap is within this run's own epoch-to-epoch noise (~0.27 swing per arm vs a 0.01-0.03 gap between arms)** — reported as inconclusive at this seed, not modelled as a win either way. Frozen pipeline default (arm B) unchanged. `RESULTS_LOG.md` 2026-08-25b. |
| **T0.2** held-out test set | **CLOSED 25 Aug** (see warning above) | Not a carve from val — rebuilt from the raw 705-image source as an independent image-level 70/15/15 split, stratified on the disease presence-vector, verified disjoint and reproducible. `scripts/dentex/build_dentex_split_from_raw.py` → `data/dentex/splits_v2.json` (train 495 / val 103 / test 107). **No model has been trained or evaluated on it.** Bone-loss audit sub-item: `model_metrics.md` labels 0.9233 as validation — correct, nothing to fix. |
| **T0.3** model selection | **CLOSED 25 Aug** (see warning above) | The caries notebook now checkpoints on macro-F1, but the weights in `models/07_caries_cascade/` predate that fix and are accuracy-selected. Both bone-loss notebooks already select on macro-F1 and have full saved outputs — **no bone-loss re-run is needed for T0.3**, which is a real scope reduction against this item's "re-run all four classifiers". |
| **T0.4** LR scheduling | **CLOSED 25 Aug** (see warning above) | Both bone-loss notebooks already have a scheduler. The caries track has none — LR was hand-dropped 1e-3 → 3e-5. The training-config table for all models is also still unwritten. |
| **T0.5** Mild class (n=6) | **OPEN, untouched** | No bootstrap CIs anywhere. The merge-vs-report-3-class decision has not been made. This is the cheapest Tier-0 item — it is a decision plus a re-report, not a re-train. |
| **T0.6** canonical detector | **DONE** | Frozen and tagged `tooth-detector-a100-1024-v1.0`, SHA-256 recorded, H200 run documented as superseded. Full record in `T0.6_detector_reconciliation.md`. **One sub-item remains open:** "re-derive every downstream crop and reported number from the canonical detector" — that has not happened and folds naturally into T1.1. |
| **T0.7** CEJ labelling | **DONE** | Documented as an exploratory negative result in `PAPER_MATERIAL.md` §5.6/§7.5 and excluded from the pipeline. |
| **T1.1** end-to-end | **CLOSED 24 Aug** | `scripts/run_inference.py` runs all six stages (RESULTS_LOG 2026-08-24f, R4/C3). Immediately exposed two OOD failures isolated evaluation could not — caries fixed 25 Aug (2026-08-25a), bone loss remains the open one. **Deployment closed 25 Aug**: `app.py` (Streamlit) + `Dockerfile`, wrapping the same pipeline unchanged (2026-08-25f). |
| **T1.2** clinic Tier 1a | **OPEN and now governance-blocked** | Blocked on something new: an unapproved re-identifiable copy of the clinic dataset is on Google Drive with `metadata/index.csv` beside `images/`. See `clinical_dataset_provenance.md` §4a. Resolve before any clinic data is processed. |
| **T1.3 / T1.4 / T1.5** | OPEN, untouched | Cheap once the re-run block lands. |

**Not in this list, and deliberately so — R1 (YOLOv11l-seg retrain).** It comes from
`MASTER_PLAN_2026H2.md` §3, not from this Tier-0/1 plan. T0.6 is already satisfied by the
frozen bbox detector, so R1 is an *enhancement* (it enables R2 mask-aware cropping), **not a
prerequisite for a submittable paper**. Its data is fully prepared (`data/tufts/dataset_seg/`,
26,005 instances) with a pre-registered acceptance criterion, so it is cheap to run alongside
the re-run block — but it must not displace Tier 0. Earlier sessions worked on it heavily
because it was the thing that happened to be unblocked, which is not the same as it being the
thing that mattered most.

~~**The one genuinely missing piece of code** ... there is no DENTEX crop generator in this
repo.~~ **Written and verified 21 Aug 2026** — `scripts/dentex/build_dentex_crops.py`. The
three original crop notebooks were recovered from Drive (now at
`notebooks/caries/dataset_construction/`), their crop contract was reproduced and checked
pixel-for-pixel against real Kaggle crops, and the generator honours `splits_v2.json`.
**Remaining prerequisite: the 705 source X-rays (~2.5 GB) are not on this machine** and must be
downloaded before the re-run block can start.

**A T0.1-class defect found while doing that, now the reason T0.1 is bigger than it looked:**
the Phase-1 gate's negative class contains **no healthy teeth** — `no_caries` was exactly
Impacted + Periapical Lesion (762 train / 49 val), while the assembled pipeline feeds the gate
every tooth the detector finds. ~~15,550 real healthy teeth are derivable from `train_quadrant_enumeration.json`~~ — **that
was wrong and is withdrawn**: DENTEX's training subsets cover disjoint patients despite sharing
filenames, so no healthy teeth are derivable from its labelled data at all. **The defect is
real and currently has no fix**; the gate's behaviour on healthy teeth is uncharacterised and
must be stated as a limitation. The one sound alternative — deriving a not-diseased class by
running the frozen detector over the 705 disease images — needs a decision. Full record:
`RESULTS_LOG.md` 2026-08-21j, 21k and **21m (the correction)**.



**Governing principle:** *methodological defects sink papers faster than missing novelty.* A reviewer who discovers that the augmentation pipeline was written but never executed stops evaluating the science and starts questioning everything else in the paper. Tier 0 is not optional and is not negotiable against Tier 1.

---

## Tier 0 — Must fix before any submission (credibility repairs)

These are correctness and honesty issues. Nothing below Tier 0 matters until these are done.

### T0.1 — Resolve the unapplied-augmentation discrepancy on the caries track ⚠ **highest priority**
- [ ] Read the caries training code and determine exactly what augmentation ran, if any.
- [ ] Choose one path and commit to it: **(a)** actually enable the augmentation and fully re-run + re-report every caries number, or **(b)** state in the methods that no augmentation was applied.
- [ ] Grep the entire repo, README, report drafts, and slides for any text claiming augmentation on the caries track and correct it.
- [ ] Record the decision and the date in a methodology-changelog file so the discrepancy has a paper trail rather than looking like a cover-up.

*Why first:* this is the one item that is a factual-accuracy problem rather than a performance problem. Everything else is "we could do better"; this is "the paper says something untrue." See `gap_analysis.md` §2C.

### T0.2 — Create a real held-out test set for the caries track
- [ ] Patient/image-level three-way split (train / val / test) with a fixed seed, emitted as a committed `splits.json`.
- [ ] Test set is locked: no checkpoint selection, no threshold tuning, no hyperparameter choice ever touches it.
- [ ] Re-run the two-phase cascade; report **val and test separately**.
- [ ] Expect the 81% to drop. Report the drop. A lower honest number is worth more than a higher contaminated one.
- [ ] Do the same audit for the bone-loss track — confirm whether 0.9233 is val or test, and label it correctly everywhere.

### T0.3 — Fix model selection on imbalanced data
- [ ] Replace accuracy-based checkpointing with macro-F1 or minority-class recall for all classifiers.
- [ ] Re-run all four classifiers (caries binary, caries severity, bone-loss binary, bone-loss severity).
- [ ] State the selection criterion explicitly in the methods.
- [ ] Report the operating point (threshold) used, and how it was chosen, on val only.

### T0.4 — Add LR scheduling and complete the training-config reporting
- [ ] Add cosine or step LR scheduling to the caries track; re-run.
- [ ] Produce a complete training-configuration table for every model: optimiser, LR schedule, batch size, epochs, augmentation (truthfully), loss, class weighting, early-stopping criterion, seed, hardware.
- [ ] Cross-check against the [CLAIM 2024 checklist](https://pubs.rsna.org/doi/full/10.1148/ryai.240300) and the dental-specific [reporting-checklist review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12756637/). Fill every applicable row.

### T0.5 — Deal honestly with the 6-sample "Mild" severity class
- [ ] Never report macro-F1 0.7208 again without the per-class support counts printed beside it.
- [ ] Add bootstrap confidence intervals to all per-class metrics. The Mild CI will be enormous — show it.
- [ ] Decide and justify: merge Mild into an adjacent class and report a defensible 2-class severity task, **or** report 3-class with an explicit statement that Mild is not reliably estimable at n=6.
- [ ] Precedent for stating this openly: the [April 2026 *Oral Radiology* study](https://link.springer.com/article/10.1007/s11282-026-00921-x) named canine underrepresentation in advanced stages as a limitation rather than hiding it.

### T0.6 — Reconcile the two YOLO runs into one canonical detector
- [ ] Tabulate both runs side by side: dataset version, split, image size, epochs, hardware, augmentation, all metrics.
- [ ] Declare the selection criterion **before** looking at which run wins (e.g. "highest val mAP@0.5:0.95 under the canonical split").
- [ ] Pick one. Freeze the weights file. Give it a version tag.
- [ ] Re-derive every downstream crop, classifier input, and reported number from the canonical detector.
- [ ] Document the non-canonical run in an appendix — do not delete it, that looks worse than reporting it.

### T0.7 — Label the CEJ classical-CV module correctly
- [ ] Ensure no document, figure, or slide presents the 15%-agreement CEJ module as a validated result.
- [ ] Reframe it explicitly as a documented negative/exploratory finding that motivates the learned-keypoint approach (T2.1). A clean negative result is publishable; a buried one is a liability.

---

## Tier 1 — Builds the system and the core claims

### T1.1 — Build actual end-to-end pipeline integration ⚠ **largest single gap**
Right now there are per-stage numbers and **no system-level numbers at all**. The stated deliverable — a filtered per-tooth report — has never been produced or measured.

- [ ] Single entry point: image in → per-tooth structured report out (FDI code, caries prediction + confidence, bone-loss prediction + confidence, quality/assessability flag).
- [ ] Define and implement the filtering/confidence policy explicitly, rather than leaving it implied.
- [ ] Handle the failure modes the clinic data will throw: missing teeth breaking FDI assignment, duplicate FDI codes, teeth detected outside the arch, edentulous regions.
- [ ] Measure and report **end-to-end**, not per-stage:
  - Per-tooth metrics through the full pipeline (detector crops, not GT crops).
  - Per-patient / per-image aggregate metrics — the [*Sci Rep* 2025 AI-platform study](https://www.nature.com/articles/s41598-025-32226-0) reports both tooth- and patient-level, and that is the expected format.
  - **Stage-wise error propagation analysis:** how much accuracy is lost at detection, at numbering, at classification. A detector at mAP@0.5 = 0.834 feeding an 81%-accurate classifier does not produce an 81% system, and quantifying that decomposition is genuinely informative.
  - Inference latency per image (HC-Net+ reports 0.02 s/image — [npj Digital Medicine](https://www.nature.com/articles/s41746-025-02077-0); a latency number is expected for anything claiming clinical utility).
- [ ] Comparable systems are explicitly end-to-end ([*Oral Radiology* Apr 2026](https://link.springer.com/article/10.1007/s11282-026-00921-x)). Without this, we have components, not a system, and the paper's central claim is unsupported.

### T1.2 — Clinical dataset external validation, Tier 1a (label-free) ⚠ **best novelty-per-hour available**
Full detail in `clinical_dataset_plan.md` §3. Requires **zero new annotations**.

- [ ] Write and unit-test the preprocessing contract: 12-bit→8-bit windowing + MONOCHROME1 inversion. The audit already showed that getting this wrong falsely flags all 4,420 images (Decision #4).
- [ ] Run the frozen canonical pipeline over the audit's existing 96-image sample gallery, then a 500-image stratified subset.
- [ ] Report label-free shift diagnostics: teeth-detected-per-image distribution vs. Tufts, confidence distribution shift, anatomically impossible outputs (duplicate FDI, L/R inconsistency), prediction-entropy shift, fraction in the uncertain band.
- [ ] **Preprocessing ablation:** windowed vs. naive 16-bit load. Separates "we mishandled the format" from "genuine domain shift" — a useful methodological result in its own right.
- [ ] Build a failure taxonomy with example crops, bucketed by confounder (implant / heavy restoration / ortho / edentulous / poor quality). The [*Healthcare* Jul 2026 review](https://www.mdpi.com/2227-9032/14/13/1952) specifically names missing "clear documentation of failure modes" as a field-wide gap — so the taxonomy is the contribution, not a byproduct.
- [ ] Motivating citation to use throughout: [*Frontiers in Medicine* Jul 2026](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1879708/full) documents AUC collapsing from 0.76–0.98 to 0.53–0.57 under domain shift, with adaptation recovering only 0.1–34.2% of the loss.
- [ ] Run everything in Colab against Drive. Do not download the dataset. Move manifests and prediction JSON, never pixels.

### T1.3 — Report prevalence-aware, clinically meaningful metrics
- [ ] Add PPV/NPV at observed prevalence alongside sensitivity/specificity.
- [ ] Add calibration curves and Brier score for all four classifiers.
- [ ] Add bootstrap 95% CIs to every headline metric.
- [ ] Position the bone-loss binary against the pooled meta-analytic benchmark — sens 87% (95% CI 80–93), spec 76% (69–81), acc 84% (75–91) across 30 studies, [DMFR 2025](https://academic.oup.com/dmfr/article/54/2/89/7917334). Our 83% sensitivity / 99.5% specificity is a favourable comparison **provided** we state clearly that ours is internal validation against their pooled multi-study estimate.

### T1.4 — Ablations for the methodological contributions we want to claim
Each of these is currently an unmeasured design decision. Measured, each is a paragraph; unmeasured, each is an assertion a reviewer will discount.
- [ ] **Bbox-jitter training:** classifier performance on GT crops vs. detector crops, with and without ±15% jitter training. Four-cell table. This is our strongest small novelty.
- [ ] **Asymmetric crop expansion:** symmetric vs. 1.5×W/2.0×H vs. a couple of other ratios.
- [ ] **Pixel-overlap-ratio vs. IoU** for sparse pathology masks — show why IoU is degenerate here rather than asserting it.
- [ ] **Class-imbalance strategy:** stratified undersampling vs. Focal Loss vs. both vs. neither.
- [ ] **Before claiming novelty on any of these,** run a targeted Google Scholar / Semantic Scholar search. Our web search did not find prior art for jitter training or asymmetric crops, but four queries is weak evidence — see `gap_analysis.md` §4.

### T1.5 — Quantified explainability, not a heatmap gallery
- [ ] Grad-CAM (or Eigen-CAM) on per-tooth crops for all four classifiers.
- [ ] **Quantify localisation agreement:** does the activation fall on the actual lesion / crestal region? Report a number, not just images.
- [ ] Report XAI behaviour separately on clinic-data failure cases — where does the model look when it is wrong on out-of-domain data? This ties T1.5 to T1.2 and makes it more than a checkbox.
- [ ] Motivation: [*Healthcare* Jul 2026](https://www.mdpi.com/2227-9032/14/13/1952) found "formal explainability methods were uncommon" and performance-focused reporting dominant. A 2026 systematic review on explainability/bias/generalisability in dentistry exists ([Mehta et al.](https://onlinelibrary.wiley.com/doi/10.1002/cre2.70375)) — **fetch returned HTTP 403, read it manually before citing its contents.**

---

## Tier 2 — Strengthens novelty

### T2.1 — Replace the classical CEJ module with a learned keypoint head
- [ ] Implement CEJ / alveolar-crest / apex keypoint detection per tooth; compute RBL% = |CEJ−crest| / |CEJ−apex|.
- [ ] Targets to aim at: [*Oral Radiology* Apr 2026](https://link.springer.com/article/10.1007/s11282-026-00921-x) — YOLOv11 keypoints, mAP50 >0.958, ICC vs. dentists 0.705–0.871 on panoramics; [*Sci Rep* Feb 2026](https://www.nature.com/articles/s41598-026-38061-1) — Keypoint R-CNN, AP50:95 0.815–0.954, ICC 0.801 on periapicals.
- [ ] **Position this correctly:** landmark-based panoramic staging is no longer novel as of April 2026. The novelty is asking whether landmark-based RBL survives a vendor change — i.e. run it under T1.2's cross-device setting. Frame accordingly.
- [ ] Grade against 2017 AAP/EFP radiographic-bone-loss thresholds and additionally store raw RBL% so results are re-gradeable.

### T2.2 — Clinical annotation + Tier 1b external validation with real ground truth
Full protocol in `clinical_dataset_plan.md` §4. This is the highest-effort item in the whole list (~40–60 annotator hours) and gated on dentist availability.
- [ ] Resolve PHI / de-identification policy **before** any annotation starts.
- [ ] Write a versioned annotation guideline; run a 20-image calibration round; revise.
- [ ] Annotate 200–300 images: image-level quality fields, tooth presence/status (including a mandatory `assessable` escape hatch), periodontal landmarks, coarse caries flags only.
- [ ] Double-annotate ≥50 images; report Cohen's/Fleiss' κ and ICC. Precedent: [BRAR](https://www.nature.com/articles/s41597-025-06400-y) reports κ = 0.88 with three periodontists; [HC-Net+](https://www.nature.com/articles/s41746-025-02077-0) reports specialist κ = 0.64 and treats it as a limitation.
- [ ] Produce the headline external-validation table: sens/spec/F1/AUC on clinic data vs. Tufts/DENTEX val, for detection, numbering, and both pathology tracks.
- [ ] **Do not attempt caries severity grading on clinic data.** The audit scores it 35/100, and the [*Sci Rep* Sep 2025 multistage caries study](https://www.nature.com/articles/s41598-025-16591-4) established panoramic caries ground truth using bitewings, which we do not have.

### T2.3 — Stratified performance by real-world confounders
- [ ] Report caries and bone-loss metrics stratified by restoration / crown / bridge / implant / RCT / missing-tooth status on clinic data (>50% restorations, 10–25% implants, 15–35% RCT per the audit).
- [ ] Report FDI numbering accuracy separately on high-missing-tooth cases.
- [ ] Related work on detecting these features exists ([*BMC Oral Health* 2025](https://link.springer.com/article/10.1186/s12903-025-07138-0), [*Sci Rep* 2025](https://www.nature.com/articles/s41598-025-32226-0)) but a stratified *pathology-performance* breakdown by restoration status was not found in our search — plausibly a genuine reporting gap, and exactly what a practising dentist would ask for.

### T2.4 — Calibrated abstention / "not assessable" output
- [ ] Add an explicit defer-to-clinician output with a calibrated confidence threshold.
- [ ] Report a coverage-vs-accuracy curve (accuracy at 100% / 90% / 75% coverage).
- [ ] Clinically the right behaviour, and it maps directly onto the `assessable` annotation field. Motivated by HC-Net+'s 20.6% missed-diagnosis rate on Stage II periodontitis and [DentiAsk](https://arxiv.org/abs/2607.08790)'s finding that large models "degrade sharply on spatial localization and counting" — silent failure on hard cases is the field's shared problem.

### T2.5 — Reconcile our detection numbers against current benchmarks
- [ ] Our detection mAP@0.5 = 0.834 vs. [YOLO26 on DENTEX](https://arxiv.org/abs/2604.16231) at box mAP50 = 0.976 for enumeration. Either explain the gap precisely (different task framing, different splits, different preprocessing — they used Roboflow-preprocessed DENTEX with 1,082 enumeration images at 800×800) or close it.
- [ ] **Manually retrieve the [DENTEX challenge assessment/leaderboard](https://dentex.grand-challenge.org/assessment/)** — our automated search did not recover final rankings. Do not claim a position relative to challenge entrants without it.
- [ ] **Manually verify current Tufts-based results.** Our searches returned only the [original 2021 dataset paper](https://ieeexplore.ieee.org/document/9557804/) and its indexing records; direct fetches of IEEE and PubMed failed. There is no confirmed Tufts SOTA to compare against yet.

---

## Tier 3 — Stretch goals if time allows

- [ ] **T3.1 — Tier 2 domain adaptation.** After T2.2, split the annotated set into adapt/test; try intensity normalisation only, threshold recalibration only, and light detector fine-tuning; report recovery against the T1.2/T2.2 baseline. Set expectations from the Frontiers 2026 figure that adaptation recovers only 0.1–34.2% of the drop — success is "measurable, documented recovery," not "restored performance."
- [ ] **T3.2 — BRAR age-normalised severity.** If `PatientInfo.xml` carries age (3,296 of 3,345 studies do), compute BRAR = (BL/RL)/age per [BRAR](https://www.nature.com/articles/s41597-025-06400-y). Nearly free, adds a published comparable severity axis.
- [ ] **T3.3 — Angular vs. horizontal bone-loss pattern classification.** Done on periapicals at 87% accuracy ([*Sci Rep* Feb 2026](https://www.nature.com/articles/s41598-026-38061-1)); the panoramic version with cross-device validation would be a clean incremental contribution.
- [ ] **T3.4 — Longitudinal / repeat-scan analysis.** 1,015 clinic folders contain repeat scans. Change detection over time is genuinely under-explored. **Blocked on** the audit's Decision #5 — there are no filename-derivable pre/post labels, so this needs date sequence plus visible treatment change plus ideally clinical records.
- [ ] **T3.5 — Curated de-identified clinical subset as a data resource.** A few hundred expertly-annotated Carestream CS 8100 panoramics from an under-represented population would be a legitimate resource contribution. [MICCAI's Open Data track](https://conferences.miccai.org/2026/en/MICCAI-2026-Open-Data-Call-for-Papers-and-Reviewers.html) explicitly solicits "novel medical imaging datasets, particularly from underrepresented populations" and publishes to the MELBA Journal Resource Track. Requires clinic consent and a PHI policy first.
- [ ] **T3.6 — VLM comparison baseline.** Run an off-the-shelf multimodal model on a sample and compare against our geometric pipeline. [DentiAsk](https://arxiv.org/abs/2607.08790) suggests VLMs are weak at exactly the spatial/quantitative reasoning our pipeline does explicitly, which would make a nice contrast figure. Positions us relative to the frontier ([DentFound](https://www.nature.com/articles/s41551-026-01713-8), >101k patients) without pretending to compete on scale.

---

## Venue selection — open item

**No target venue is recommended here**, because that decision needs the mentor and depends on which of the above actually completes.

Genuine evidence found during the literature scan, offered as input to that conversation, not as a recommendation:
- **[MICCAI Open Data track](https://conferences.miccai.org/2026/en/MICCAI-2026-Open-Data-Call-for-Papers-and-Reviewers.html)** — solicits datasets from under-represented populations, annotation methodology papers, and publishes to MELBA Journal's Resource Track. The 2026 submission deadline (19 June 2026) has **already passed**; this is evidence that a recurring venue of the right shape exists, not a live deadline. Fits T3.5.
- Journals that published directly comparable work in the last 12 months, i.e. demonstrably in scope: *Oral Radiology* ([Apr 2026](https://link.springer.com/article/10.1007/s11282-026-00921-x)), *Dentomaxillofacial Radiology* ([2025 review](https://academic.oup.com/dmfr/article/54/2/89/7917334)), *Scientific Reports* ([Feb 2026](https://www.nature.com/articles/s41598-026-38061-1), [Sep 2025](https://www.nature.com/articles/s41598-025-16591-4)), *BMC Oral Health* ([2025](https://link.springer.com/article/10.1186/s12903-025-07138-0)).

**Do not** set a submission date before Tier 0 is complete.

---

## Suggested execution order

1. **T0.1** — the augmentation discrepancy. Today. Nothing else until this is resolved.
2. **T0.6** — canonical detector, because every downstream re-run depends on it.
3. **T0.2 → T0.3 → T0.4 → T0.5** — the re-run block. Do these together; they share the same training loop and produce one clean set of numbers.
4. **T1.1** — end-to-end integration. This is the long pole for the "system" claim.
5. **T1.2** — clinical Tier 1a. Can run in parallel with T1.1 once the canonical detector is frozen, and it needs no annotations, so it is the most schedule-robust source of new results.
6. **T1.3 + T1.4** — metrics and ablations. Fast once the re-run block is done.
7. **T2.2** — annotation, started early in the background because it is gated on the dentist and has the longest lead time.
8. Everything else as time permits.

**Single highest-leverage move:** finish T0.1 and the T0.2–T0.5 re-run block, then run T1.2 while T1.1 is being built. That combination turns "unvalidated models with a methods-section problem" into "a validated, honestly-reported system with real-world external evidence" — which is a submittable paper even if none of Tier 2 or Tier 3 ever happens.
