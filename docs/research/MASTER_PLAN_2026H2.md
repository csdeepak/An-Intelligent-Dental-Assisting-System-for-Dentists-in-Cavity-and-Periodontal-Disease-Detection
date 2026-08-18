# Master Implementation Plan — August to October 2026

**Compiled:** 15 August 2026
**Updated:** 18 August 2026 — §4.3 rewritten and §4.4/§8 updated after inspecting the downloaded Ningxia dataset directly. Two structural findings: (1) the test splits are **center-stratified** (`test1`–`test4`), giving a built-in domain-shift gradient that strengthens C2 at no cost; (2) the dataset contains **no healthy controls**, so specificity/AUC are not computable on it — the original §4.3 claimed they were, and that was wrong. Metrics redistributed across datasets accordingly (§4.3.3). Logged in `../results/RESULTS_LOG.md`.
**Corrected:** 16 August 2026 — §0, §2.3 (C1), R6, §3.1, §5 (W5), §5.1, §6, §7, §8, §9 previously assumed DentFound's fine-tuned weights were public ("Apache-2.0 weight release"). Verified directly against the repository: only the training *code* is Apache-2.0; the fine-tuned weights and the 101k-patient training data are both closed. Logged in `../results/RESULTS_LOG.md`. C1 now runs against an accessible open-weight VLM instead of DentFound itself — the scientific question is unchanged, only which model sits on the other side of the comparison.
**Horizon:** implementation complete by **14 October 2026**; research paper submitted by **26 October 2026**.
**Supersedes for sequencing purposes:** the week-by-week schedules in `PUBLICATION_STRATEGY.md` §F and `clinical_dataset_plan.md` §7. The *analysis* in those documents stands; the *critical path* changes for the reason given in §1.
**Companion docs:** `gap_analysis.md`, `PUBLICATION_TODO.md`, `clinical_dataset_plan.md`, `PUBLICATION_STRATEGY.md`, `../results/PAPER_MATERIAL.md`.

---

## 0. The situation in five lines

We have four trained models, no integrated system, no external validation, and eight weeks. The previous plan routed external validation through a private clinic dataset that needs IRB approval and 40–60 hours of dentist annotation — a 12–14 week critical path that cannot land by 14 October. Meanwhile, two things appeared in the literature this month that change the arithmetic: a **free, downloadable, 3-hospital panoramic dataset covering both our target diseases**, which converts the 14-week path into an 8-week one, and **DentFound, the frontier dental VLM that supposedly obsoletes our project — whose training code is public (Apache-2.0) but whose trained weights are not**. That second fact hands us a sharper novelty claim than the one we had, once the comparison is built around an accessible open-weight VLM rather than DentFound's own unreleased checkpoint (§2.3, R6). This document is the plan that follows from that.

---

## 1. The strategic pivot

### 1.1 What changes

| | Old plan | New plan |
|---|---|---|
| **Primary external validation** | Private clinic data (Carestream CS 8100, 4,420 images) | **Ningxia multi-center dataset** (6,580 images, 3 hospitals) |
| **Gating dependency** | IRB approval + dentist annotation | None — dataset is public, pre-approved, pre-annotated |
| **Earliest external result** | ~Week 10 (optimistic), realistically never by 14 Oct | **Week 4** |
| **Headline novelty** | "We externally validated on one clinic" | "Specialist pipeline vs. dental foundation model, validated across 4 independent sources" |
| **Clinic data role** | The whole paper | A *second* validation stream — pure upside if IRB clears, zero risk if it doesn't |

### 1.2 Why this is the right call, not a retreat

The clinic dataset's value was always that it is a device/population not in any public benchmark. That value is real and it does not expire — it becomes the follow-up paper, or a strengthening addition during revision. What it cannot do is produce a number before mid-October.

The Ningxia dataset does something the clinic data never could: it gives us **three independent hospitals with existing expert annotations for both caries and periodontitis**, meaning we can report genuine cross-center generalisation *with ground truth* in week 4 rather than image-level shift diagnostics in week 10. `clinical_dataset_plan.md` §3 correctly identified label-free Tier 1a as the schedule-robust option **given the datasets known at the time**. A labelled public multi-center set is strictly better on every axis that matters for publication.

**Decision: the clinic-data track continues in the background (start IRB now — it costs nothing to have it running), but nothing on the critical path depends on it.**

---

## 2. The paper we are writing

### 2.1 Working title

> *Specialist pipelines versus dental foundation models: cross-dataset validation of an efficient per-tooth panoramic screening system*

### 2.2 The central question

Dental foundation models (DentFound, 7B params, 101k patients — code released, weights closed; DentVLM, 110k images, 2.46M VQA pairs — closed) now exist and are claimed to reach clinical-level interpretation. **Does a dramatically smaller specialist pipeline remain competitive against an accessible general-purpose VLM on the specific, hard, clinically-load-bearing sub-tasks — subtle radiolucent caries and quantitative bone loss — and how do both degrade across institutions?** (The comparison runs against an open-weight VLM standing in for DentFound, not DentFound itself — R6.)

This is a question nobody has answered, it is answerable in eight weeks, and *both possible answers are publishable*:

- **If the specialist wins or ties** on caries/bone-loss at a fraction of the compute → a real efficiency-frontier result with direct deployment implications for clinics that cannot run a multi-billion-parameter model.
- **If the VLM dominates** → we have quantified the specialist-model obsolescence boundary on an independent cohort, which is itself a finding, and our failure taxonomy explains *where* and *why*.

Prior evidence suggests the first outcome is plausible: the [*Diagnostics* Sep 2025 GPT-4o study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12468776/) found VLMs handle radiopaque features (implants, restorations) well but degrade badly on radiolucent ones (caries, periapical lesions) — exactly our target pathologies. [DentiAsk](https://arxiv.org/abs/2607.08790) independently found VLMs "degrade sharply on spatial localization and counting."

### 2.3 Contributions, ranked

| # | Contribution | Novelty status | Effort |
|---|---|---|---|
| **C1** | Specialist-vs-foundation-model comparison on subtle radiolucent pathology, at matched evaluation | **New.** Motivated by DentFound (June 2026) — its code is Apache-2.0 but its fine-tuned weights are not public, so the comparison runs against an accessible open-weight VLM instead (R6). Not yet done by anyone, for either model. | Medium |
| **C2** | Cross-dataset external validation across 4 independent sources (Tufts, DENTEX, Ningxia ×3 hospitals) | Fills the #1 gap named by three separate 2025–26 reviews | Medium |
| **C3** | End-to-end system-level metrics + stage-wise error-propagation decomposition | Rare in the field; our own largest gap | High |
| **C4** | Calibrated abstention ("not assessable") with coverage–accuracy curves | Not found in dental pipelines (`gap_analysis.md` §2B) | Low |
| **C5** | Ablation cluster: bbox jitter, asymmetric crop geometry, overlap-ratio vs. IoU | Small but honest; converts assertions into findings | Low |

C1+C2 are the paper. C3 is what makes it a *system* paper rather than a *model* paper. C4/C5 are the rigor padding that separates "major revisions" from "accept."

### 2.4 What we explicitly do NOT claim

Per `gap_analysis.md` §5, and non-negotiable: no novelty claims on tooth detection, FDI numbering, CEJ landmark detection on panoramics, caries cascade architecture, or Grad-CAM heatmaps. All published, recently, with better numbers. We cite them and move on.

---

## 3. Architecture redesign

Six changes. Each is justified by a specific paper, and each is costed. **GPU is not the constraint** — total compute below is ~35 hours on a single H100, so the schedule is bounded by integration and analysis work, not training.

### R1 — Detection → instance segmentation (YOLOv11l → YOLOv11l-seg) ✅ **do this**

**Why:** DentFound's own ablation shows tooth *instance masks* are a load-bearing component of its architecture — the frontier model does not trust raw pixels for spatial dental reasoning, it grounds on instances first. Our pipeline already makes the same bet implicitly (detect → crop → classify); upgrading bbox → mask makes it explicit and defensible, and lets us cite DentFound's ablation as independent justification for our own design.

**Why YOLOv11 specifically, staying on it rather than jumping to YOLOv12+:** [Mutlu et al., *Odontology* (2026)](https://doi.org/10.1007/s10266-026-01333-3) ran the exact head-to-head on dental panoramic radiographs and found YOLOv11 beats YOLOv12 (mAP@0.5 0.857 internal / 0.806 external), naming it the more robust architecture for multi-class dental detection. Verified 17 Aug 2026 — full detail in `../results/PAPER_MATERIAL.md` §5.1. Upgrading to `-seg` stays within the same generation this evidence supports; it is not an argument for chasing the newest release.

**Why it's cheap:** Tufts already ships `Segmentation/Segmentation/teeth_mask` and `teeth_polygon.json` (confirmed in `configs/dataset_config.yaml`). **No new annotation is required.** Ningxia also ships segmentation masks, giving us cross-dataset mask evaluation for free.

**Secondary benefit:** mask-aware cropping (R2) becomes possible, and instance masks give a cleaner signal for FDI assignment on sparse arches.

**Cost:** one retrain, ~6h H100.

### R2 — Mask-aware cropping ✅ **do this**

Currently crops are rectangular, so an expanded 1.5×W/2.0×H crop pulls in neighbouring teeth — a known confound the asymmetric ratio was chosen to *mitigate* rather than eliminate. With R1's masks we can suppress non-target-tooth pixels (soft attenuation, not hard masking, so bone context below the root is preserved for the periodontal branch).

**This becomes ablation C5's fourth cell** — rectangular vs. mask-aware crops is a clean, cheap experiment that nobody in the retrieved literature has reported.

**Cost:** ~2h implementation, folds into existing crop generator.

### R3 — Calibration + abstention head ✅ **do this**

Temperature scaling on all four classifiers, then an explicit `not_assessable` output with a calibrated threshold, reported as a coverage–accuracy curve (accuracy at 100% / 90% / 75% coverage).

**Why:** clinically correct behaviour, addresses the "silent failure on hard cases" problem that HC-Net+ (20.6% missed Stage-II periodontitis) and DentiAsk both document, and it is contribution C4 at near-zero cost. Also directly answers the prevalence-aware-metrics requirement (R8 in `PUBLICATION_STRATEGY.md` §B.2).

**Cost:** ~4h. No retraining needed — post-hoc.

### R4 — Stages 5–6: the integration layer ✅ **do this — this is the long pole**

The missing milestone. Single entry point: image in → per-tooth structured JSON out (FDI code, caries prediction + calibrated confidence, bone-loss prediction + confidence, assessability flag), then a filter/report layer.

Must handle, explicitly: missing teeth breaking positional FDI assignment, duplicate FDI codes, teeth detected outside the arch, edentulous regions. These are not edge cases on Ningxia data — they are the common case.

**Cost:** ~2 weeks of the schedule. Everything downstream blocks on it.

### R5 — Severity reporting, fixed honestly ✅ **do this**

The 3-class severity model has **6 validation samples in the Mild class**. Per `PUBLICATION_TODO.md` T0.5: report 2-class severity as the headline (defensible), keep 3-class in an appendix with bootstrap CIs and an explicit statement that Mild is not estimable at n=6, and additionally store raw overlap-ratio/RBL% so results are re-gradeable under any convention.

**Cost:** ~3h. Mostly a reporting change, not a modelling one.

### R6 — Comparison branch: an accessible VLM baseline, not DentFound itself ✅ **do this** (revised 16 Aug 2026)

**Correction to the original plan.** DentFound's training code is Apache-2.0 and public, but its fine-tuned weights are not — the repository's `checkpoints/` folder only documents downloading the generic pretrained CLIP-ViT-L/14 and Vicuna-7B base models anyone would start from, not DentFound's own trained model, and no working link to a DentFound checkpoint exists anywhere in the repo. Its 101k-patient training data is closed too, so training our own copy from the released code isn't an option either. Verified directly against the repository on 16 August 2026 — the original "free baseline" premise in this document was wrong, and is corrected here rather than silently edited. See `../results/RESULTS_LOG.md`.

**Non-blocking, pure-upside action:** email DentFound's corresponding author requesting research-use access to the fine-tuned weights for an independent comparison. Worth sending — it costs one email — but nothing in this schedule waits on a reply, and proceed as below regardless of outcome.

**What C1 actually runs on:** an accessible general-purpose VLM, evaluated zero-shot on the same test sets, standing in for DentFound. Two candidates, not mutually exclusive:

- **An open-weight multimodal model, run locally on the H100** — the primary comparison. Keeps faith with the reproducibility argument this whole project (and the survey) is built on: a result another lab can actually rerun. Which specific model is selected in W5, from whatever is current and reliably deployable at that time — not locked in now, on the same kind of unverified assumption that produced this correction in the first place.
- **GPT-4o via API**, as a secondary, supplementary comparison point. Direct literature precedent: it is the same model the [*Diagnostics* Sep 2025 study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12468776/) used to establish the radiopaque/radiolucent asymmetry that C1's hypothesis rests on. Not independently reproducible by others without their own API access, and carries a small real cost — useful context, not the primary result.

The scientific question C1 asks is unchanged: does a small specialist pipeline hold up against a general-purpose VLM on subtle radiolucent pathology. What changed is which VLM sits on the other side of the table — and, if anything, this removes a dependency on a third party's code rather than adding one.

**Cost:** ~6h environment setup for the open-weight model (lower risk than the original DentFound estimate — a mainstream model, not DentFound's specific, less-battle-tested repo) + ~4h inference. GPT-4o comparison adds ~2h setup and a small API cost proportional to image count.

### R7 — Learned CEJ keypoint head ❌ **defer, and say so**

`PUBLICATION_TODO.md` T2.1 proposes replacing the 15%-agreement classical CEJ module with a learned keypoint head, targeting the April 2026 *Oral Radiology* result. **This needs CEJ/crest/apex keypoint annotations that we do not have and cannot produce in eight weeks.**

Deriving pseudo-labels from Ningxia's periodontitis segmentation masks is tempting and is the kind of shortcut that produces an unfalsifiable result. Do not do it. Report the classical CEJ attempt as a clean documented negative result (T0.7) and name the learned keypoint head as future work with a concrete on-ramp.

### 3.1 Resulting architecture

```
OPG input (any source: Tufts / DENTEX / Ningxia / clinic)
  │
  ├─ Preprocessing contract  ── source-adaptive normalisation (CLAHE / percentile windowing),
  │                             unit-tested, versioned, ablated
  ▼
Stage 1  YOLOv11l-seg ──────► per-tooth bbox + instance mask          [R1]
  ▼
Stage 2  Sort → jaw split → FDI assignment  (mapping bug FIXED)
  ▼
  ├──────────── CARIES BRANCH ────────────┬──────── PERIODONTAL BRANCH ────────┐
  │  mask-aware tight crop  [R2]          │  mask-aware expanded crop  [R2]    │
  │  ResNet18 gate → ResNet18 depth       │  ResNet18 binary → severity (2-cl) │
  │  + temperature scaling  [R3]          │  + temperature scaling  [R3]       │
  └───────────────────┬───────────────────┴────────────────┬───────────────────┘
                      ▼                                    ▼
Stage 5  Fusion + calibrated abstention + filtering                   [R3][R4]
  ▼
Stage 6  Per-tooth JSON report + Grad-CAM overlays                    [R4]
  ▼
        ══ evaluated against ══  open-weight VLM baseline (frozen)   [R6]
```

---

## 4. Dataset strategy

### 4.1 The one rule that governs everything

> **Ningxia is external test data. It is worth more to us untouched than trained on.**

The temptation is to fold 6,580 new images into training and watch the numbers rise. Resist it. External validation is the single most-cited missing element in this subfield ([DMFR 2025](https://academic.oup.com/dmfr/article/54/2/89/7917334), [Frontiers Med Jul 2026](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1879708/full), [Healthcare Jul 2026](https://www.mdpi.com/2227-9032/14/13/1952)). Training on it converts our strongest available claim into a marginal accuracy improvement. **Bad trade.**

### 4.2 Assignments

| Dataset | Size | Role | Rule |
|---|---|---|---|
| **Tufts** | 1,000 images / 26,005 boxes | Detection + bone-loss training | Existing frozen 70/15/15 image-level split. Unchanged. |
| **DENTEX** | ~3,500 crops | Caries training | **Must carve a held-out test split** (T0.2). Current 81% is a validation number. |
| **Ningxia** ([download](https://github.com/qinxin99/qinxini)) | 6,580 images, 3 hospitals — periodontitis 2,736 / caries 1,277 / impacted 2,567 | **Primary external test** | Locked. No threshold tuning, no checkpoint selection, no preprocessing tuning on it. Touched once, at final evaluation. |
| **vzrad2** ([Roboflow](https://github.com/its-deema/ToothTruth-Dental-Disease-Classification)) | 10,580 images, 35 classes | Optional robustness spot-check | Only if time permits. Not on critical path. |
| **Private clinic** | 4,420 images, Carestream CS 8100 | Bonus stream | IRB-gated. Label-free Tier 1a only, if it clears. |

### 4.3 What Ningxia can and cannot measure — read this before building the eval

**Revised 18 August 2026**, after inspecting the downloaded dataset directly rather than reasoning from the paper's description. Two structural facts changed this section: one is an opportunity the original plan missed, one is a constraint the original plan got wrong.

#### 4.3.1 Baseline caveat (unchanged, still true)

Ningxia provides **image-level disease labels plus lesion segmentation masks**. It does **not** provide per-tooth FDI-keyed annotations. Our pipeline outputs per-tooth findings. These do not match one-to-one, and pretending otherwise would be exactly the kind of unfalsifiable evaluation this project's documentation exists to prevent. Per-tooth FDI-keyed external metrics remain available only from the clinic data, if IRB clears.

#### 4.3.2 Finding 1 — the test splits are center-stratified. Exploit this.

Every segmentation category ships **four** test splits (`test1`–`test4`), each with paired `img/` + `mask/` folders. Per the dataset's own README:

> "test2 and the training set are from the same center, and the remaining three are cross-center testsets from different centers."

So Ningxia is **not one external set — it is a built-in domain-shift gradient**:

| Split | Center relationship | What it measures |
|---|---|---|
| `test2` | Same center as their train data | Near-ceiling external performance |
| `test1`, `test3`, `test4` | Three genuinely different centers | True cross-center generalisation |

**This upgrades contribution C2 for free.** Instead of one external number, we report *how performance decays as a function of institutional distance* — which is precisely the "documented failure modes under domain shift" gap that [Frontiers Med](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1879708/full) and [Healthcare](https://www.mdpi.com/2227-9032/14/13/1952) (both Jul 2026) name as unmet. Report every headline metric **stratified by split**, never pooled.

Caveat: the **classification** subset was randomly split across centers (README §Classification), so it carries no center structure and is useless for this analysis. Only the segmentation subset supports it. Also note the exact center↔split mapping is stated qualitatively in the README but its arithmetic does not obviously reconcile with the three per-hospital counts in the published paper (4,940 / 716 / 880) — **verify the mapping against the paper before asserting which center is which in print.**

#### 4.3.3 Finding 2 — there are no healthy controls. This changes which metrics are reportable.

The classification set contains exactly three folders — `Dental caries`, `Impacted teeth`, `Periodontitis` — and **no normal/healthy class**. The segmentation set is the same: every image is a positive case of its category.

**Consequence: sensitivity/recall is computable on Ningxia. Specificity, AUC, and PPV are not.** The original §4.3 claimed "sensitivity/specificity/AUC at the image level" — that was wrong and is corrected here.

**Do not manufacture negatives from other categories.** Using a periodontitis image as a caries-negative assumes the absence of caries annotation means absence of caries. It does not — the dataset annotates the diagnosis of interest, and co-occurrence is clinically common. That substitution would convert correct predictions into false positives and silently corrupt the headline number.

**The fix is a division of labour across datasets, not a workaround within one:**

| Metric | Source | Why that source |
|---|---|---|
| Specificity, PPV/NPV at realistic prevalence, calibration | **Tufts held-out test** | Has genuine negatives at real prevalence (1,499 normal / 59 diseased) |
| Sensitivity under domain shift, stratified per center | **Ningxia** `test1`–`test4` | Positives only — but cross-center, which Tufts is not |
| Lesion-localisation agreement | **Ningxia masks** | Requires no negatives at all; unaffected by this constraint |

#### 4.3.4 The three Ningxia measurements, revised

1. **Lesion-localisation agreement** *(promoted to primary)* — do the predicted diseased teeth spatially overlap the expert lesion mask? Unaffected by the missing negatives, and doubles as the **quantified XAI metric** (T1.5), satisfying two requirements with one experiment. **This is now the headline external number.**
2. **Image-level detection sensitivity** *(demoted, relabelled)* — on an image labelled diseased, does the pipeline flag ≥1 diseased tooth? Report as sensitivity/recall only, per split. Explicitly state that specificity is not computable here and comes from Tufts instead.
3. **Detection + numbering sanity** — teeth-per-image distribution, duplicate-FDI rate, arch-consistency violations vs. Tufts. Label-free, from `clinical_dataset_plan.md` §3 Tier 1a. Also stratify by split — numbering failures are a likely domain-shift symptom.

**State all of this explicitly in the paper.** These are limitations, not flaws — and naming them precisely is what distinguishes us from the 63.3%-of-papers-rated-merely-"intermediate" baseline the DMFR meta-analysis found.

### 4.4 Logistical risk — RESOLVED 18 August 2026

**Outcome: the risk materialised as predicted, and was cleared.** The Baidu Cloud link (password `3et5`) presented a CAPTCHA gate that automated retrieval could not and should not bypass; it was completed manually. The download then ran across roughly three days (file timestamps 16–18 Aug), consistent with the throttling this section anticipated. The maintainer-email and vzrad2 fallbacks were never needed.

**Local location:** `D:\nangxia_dataset`. Structure: `segmentation/{Dental caries,Impacted teeth,Periodontitis}/{train,test}/` with `img/` + `mask/` pairs under `test1`–`test4`, plus `classification/分类数据集/{train,test}/` with three disease class folders. Seven `.rar` source archives are retained deliberately — see below.

**Verification status at time of writing:** six of seven archives extracted and count-verified against the README table (image+mask pairing gives ~2× the per-image count, as expected). `segmentation/Periodontitis/train.rar` (4.26 GB, 2,000 images — the largest single split, and the disease most central to this project) was **still extracting**. Confirm it lands at 2,000 images + 2,000 masks before treating the dataset as complete.

**Do not delete the `.rar` archives yet.** A scan found no junk in the folder — no `.tmp`/`.part`/`.crdownload`/`Thumbs.db`, no zero-byte files — so there is nothing to clean up, and the archives are the only local fallback for a download that cost three days and a manual CAPTCHA. Only counts have been verified, not byte-level integrity. Retire them once the pipeline has successfully read every split end to end.

---

## 5. Schedule

Eight weeks and change. Each week has an exit criterion; if a week's criterion is not met, the following week's scope is cut rather than the schedule slipping.

| Week | Dates | Work | Exit criterion |
|---|---|---|---|
| **W1** | Aug 15–21 | **Unblock + repair.** Download Ningxia (day 1, see §4.4). Fix the Universal→FDI lower-arch bug in `dataset_config.yaml` **and** `src/utils/fdi_converter.py` (both are wrong), cover with `tests/test_fdi_converter.py`. **T0.1** augmentation audit on the caries track — resolve and document. Start IRB paperwork for clinic data. Provision E2E H100. | Ningxia downloaded and loadable; FDI conversion correct and unit-tested; augmentation question answered in writing |
| **W2** | Aug 22–28 | **Canonical models.** **T0.6** — reconcile the two YOLO runs, declare the criterion *before* looking at results, retrain as **YOLOv11l-seg** [R1], freeze and version. **T0.2** — carve DENTEX held-out test split, re-run caries cascade. **T0.3** — macro-F1 checkpointing on all four classifiers. Implement mask-aware cropping [R2]. | One frozen canonical detector with a version tag; all four classifiers retrained with honest val/test separation |
| **W3** | Aug 29–Sep 4 | **Integration, part 1** [R4]. Single-entry-point inference. Per-tooth structured JSON schema. FDI assignment robust to missing teeth / sparse arches. | `run_inference.py` produces valid per-tooth JSON on a Tufts test image, end to end |
| **W4** | Sep 5–11 | **Integration part 2 + first external run.** Report assembly, Grad-CAM overlays. Then **run the frozen pipeline over Ningxia** — the three measurements in §4.3.4, reported **stratified by `test1`–`test4`**, never pooled (§4.3.2). First external numbers exist. | Domain-shift report v1 showing the per-center performance gradient |
| **W5** | Sep 12–18 | **VLM baseline** [R6]. Select and set up an open-weight VLM (plus GPT-4o as secondary), inference over the same test sets. Head-to-head table vs. our pipeline on caries + bone loss. Efficiency comparison (params, latency, VRAM). | C1 comparison table populated |
| **W6** | Sep 19–25 | **Rigor block.** Calibration + abstention [R3], coverage–accuracy curves. Bootstrap 95% CIs on every headline metric. PPV/NPV at observed prevalence — **on Tufts held-out test, not Ningxia** (§4.3.3). Ablations [C5]: jitter, asymmetric crop, mask-aware crop, overlap-vs-IoU. Stage-wise error propagation [C3]. | Every number in the paper has a CI and a support count |
| **W7** | Sep 26–Oct 2 | **Analysis + figures.** Failure taxonomy with example crops, bucketed by confounder. All result tables final. CLAIM 2024 checklist filled. Figures drawn. | Results section is fully specified — no experiment left to run |
| **W8** | Oct 3–9 | **Write.** Full draft. `RESULTS_LOG.md`, `model_metrics.md`, `PAPER_MATERIAL.md` updated per `CLAUDE.md` rules. | Complete draft circulated to Dr. Mamatha H R |
| **Buffer** | Oct 10–14 | Slack. Revisions, reruns, anything that slipped. **Project deadline: 14 Oct.** | Implementation frozen |
| **Submission** | Oct 15–26 | Compress to venue format, cover letter, **submit** | ISBI 2027 deadline: **26 Oct** |

### 5.1 Parallel track — the survey

The survey is nearly submittable and depreciating monthly. It runs **in parallel**, owned separately, and must not consume critical-path weeks. Minimum viable fix list from `PUBLICATION_STRATEGY.md` §A.3, plus two additions from this month's research:

- **S1** search-window contradiction (fatal, one paragraph, do it first)
- **S2** empty Section 9
- **S3** table/text audit — and the ~22 unverified Table IV rows flagged in the 2026-08-13 session memory
- **S4** — **now covers DentFound *and* DentVLM.** DentVLM (110k images, 2.46M VQA pairs, beats junior dentists on 21/36 tasks) is arguably the stronger threat to the central gap claim and is not currently cited anywhere in the draft.
- **S5** — add the 2026 papers, **including** DentVLM, the [Large AI Models in Dental Healthcare scoping review](https://arxiv.org/html/2606.02914v1) (97 studies, PRISMA-ScR, Jun 2026) and [Vision Foundation Models for Oral and Maxillofacial Radiology](https://arxiv.org/pdf/2510.14532) (Oct 2026). **The scoping review must be cited and scoped against explicitly** — it surveys foundation models across all of dentistry; we survey integrated panoramic caries+periodontal pipelines. Adjacent, not subsumed. Say so in one sentence or a reviewer will say it for us.

**Recommended reframing of the survey's central claim**, given both VLMs now exist:

> *No openly reproducible system — open in both weights and training data — integrates caries detection, severity staging, periodontal bone-loss quantification and explainability in a single panoramic pipeline.*

DentFound releases its training **code** but neither its fine-tuned weights nor its 101k-patient training data (corrected 16 Aug 2026 — the earlier draft of this note said "weights," which was wrong); DentVLM releases none of the three. That distinction — code open, weights and data both closed — is real, defensible, and verifiable. The survey's own text was already correct on this point (`Survey Paper Latex folder/conference_101719.tex`, the "Reproducibility is also asymmetric" passage); only this planning note had the error. Our own research paper then fills exactly the gap the survey names, which is the coherent two-paper structure `PUBLICATION_STRATEGY.md` §D.5 describes.

---

## 6. Compute budget (E2E Networks H100/H200)

| Job | Est. GPU-hours | Notes |
|---|---|---|
| YOLOv11l-seg retrain (1024px, 150 ep) | ~6 | Single H100. H200 if available, no material difference at this size. |
| 4× ResNet18 retrains (macro-F1 checkpointing) | ~4 | ~1h each |
| Ablation runs (jitter × crop geometry × imbalance) | ~8 | Parallelisable |
| Open-weight VLM inference (~8,000 images) | ~4 | Batched; bf16 — exact model set in W5, not DentFound (§R6) |
| Pipeline inference over Ningxia (×3 preprocessing variants) | ~3 | Cheap |
| Contingency / reruns | ~10 | Assume at least one full redo |
| **Total** | **~35 GPU-hours** | |

**Conclusion: compute is not the bottleneck, and no part of this plan should be designed around saving GPU time.** The scarce resources are integration engineering (W3–W4) and honest analysis (W6–W7). If a trade appears between "more GPU" and "less analysis time," always buy GPU.

Note: DentFound's own fine-tuned weights are not public (§R6), so DentFound itself is not part of this compute budget at all — C1 runs against an open-weight VLM instead, and inference on it fits comfortably on one H100. If DentFound's authors ever grant weight access on request, only ever run it for **inference**, never fine-tune it — fine-tuning would make it a component rather than a baseline and destroy contribution C1's framing regardless of which model sits opposite our pipeline.

---

## 7. Venue

| Target | Deadline | Fit | Verdict |
|---|---|---|---|
| **IEEE ISBI 2027** | **26 Oct 2026** | 4 pages, single-blind, IEEE→Scopus | **Primary target for the research paper.** The timing is near-perfect: implementation freezes 14 Oct, leaving 12 days to compress into 4 pages. Four pages forces the paper down to C1+C2, which is the sharpest possible framing. |
| *Oral Radiology* | Rolling | Free under subscription, accepts unsolicited reviews, demonstrably in scope | **Primary target for the survey**, and the fallback for the research paper if ISBI slips. |
| *Scientific Reports* | Rolling | £2,290 APC | Research-paper fallback if funding exists. Check PES Read-and-Publish first. |
| *Computers in Biology and Medicine* | Rolling | Hybrid, free option | Good fit for the methods framing; no deadline pressure. |

**Go/no-go checkpoint: 30 September.** If C1 (VLM comparison, §R6) and C2 (Ningxia external validation) are not both producing final numbers by then, drop ISBI without regret and target *Oral Radiology*. A rushed 4-page submission with half-finished validation wastes the submission and the reviewer goodwill.

---

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ~~Baidu Cloud download fails/throttles~~ | **RESOLVED 18 Aug** | — | Materialised as predicted (CAPTCHA + ~3-day throttled transfer), cleared manually. Data local at `D:\nangxia_dataset`. See §4.4. |
| Ningxia label granularity mismatches our per-tooth output | **Certain** | Medium | Already handled — §4.3.4 defines three honest measurements instead of one dishonest one |
| **Ningxia has no healthy controls** — specificity/AUC not computable there | **Certain (confirmed 18 Aug)** | Medium — would have silently corrupted the headline number | §4.3.3: specificity/PPV move to Tufts held-out test; Ningxia reports sensitivity + localisation agreement only. **Never synthesise negatives from other disease categories.** |
| Chosen open-weight VLM underperforms or is hard to deploy | Low-Medium | Medium — weakens C1's polish, not its core question | Pick an established, widely-used open VLM in W5, not a bleeding-edge release; GPT-4o (§R6) is a documented, low-effort fallback comparison point regardless |
| Integration (W3–W4) overruns | **High** | High | This is the historical long pole. Cut C5 ablations first, then C4, never C2. |
| Models transfer badly to Ningxia | Medium-High | **Low — this is the finding** | Reframed as the result, per Frontiers 2026 precedent (AUC 0.76–0.98 → 0.53–0.57 is *published, expected* behaviour). Do not tune until it looks good — that destroys the contribution. |
| IRB doesn't clear in time | High | **None** — by design | Clinic data is off the critical path. That is the entire point of §1. |
| A third foundation-model paper lands before submission | Medium | Medium | Re-run the literature check in W7 (`PUBLICATION_STRATEGY.md` P3.3). The field moved three times between April and July 2026. |

---

## 9. What we take from each paper

Direct answer to "what can I opt for from the study, and what can I redesign."

| Source | What we take | What we do NOT take |
|---|---|---|
| **[DentFound](https://github.com/ahukui/DentFound)** (*Nat BME*, Jun 2026) | (a) The instance-guided principle → justifies R1/R2. (b) Their ablation structure (masks / resolution / staged training) as a template for ours. (c) Their Apache-2.0 training code, if a from-scratch reproduction is ever attempted. | Their fine-tuned weights and their 101k-patient training data — **neither is released** (corrects the original "free baseline" premise; verified 16 Aug 2026). Their scale, their VLM framing. C1 runs against an open-weight VLM instead (R6); we are not competing on scale either way. |
| **[DentVLM](https://arxiv.org/abs/2509.23344)** (*Nat Commun*, 2026) | Their evaluation *structure* — dentist-panel comparison, per-task breakdown, diagnostic-time measurement. Cite as frontier context. | Nothing technical — no code, weights or data released. |
| **[Ningxia multi-center](https://github.com/qinxin99/qinxini)** (*J Imaging Inform Med*, 2024) | **The dataset itself** — primary external validation, both diseases, 3 hospitals, free, pre-approved. | Their benchmark numbers as a comparison target (within-dataset Dice ~97% is not comparable to our cross-dataset setting). |
| **[Oral Radiology keypoint staging](https://link.springer.com/article/10.1007/s11282-026-00921-x)** (Apr 2026) | Their honest limitation statement (panoramics underestimate early bone loss; should not be sole diagnostic basis) → quote in our limitations. AAP/EFP staging convention. | The keypoint head itself — deferred, R7. No annotations. |
| **[GPT-4o numbering study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12468776/)** (*Diagnostics*, Sep 2025) | The radiopaque-vs-radiolucent asymmetry finding — this is the **hypothesis behind C1** and the reason to believe a specialist can win. | Their tiny 50-image scale. |
| **[Frontiers Med](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1879708/full)** / **[Healthcare](https://www.mdpi.com/2227-9032/14/13/1952)** (Jul 2026) | The domain-shift framing and the "failure modes are undocumented" gap → motivates C2 and the failure taxonomy. | — |
| **[DMFR meta-analysis](https://academic.oup.com/dmfr/article/54/2/89/7917334)** (2025) | Pooled benchmark (sens 87%, spec 76%) to position against; the "0 of 30 very high quality" finding → rigor is our differentiator. | — |

---

## 10. Immediate next actions (this week)

Ordered. Items 1–3 are blocking; do them before anything else.

1. **Attempt the Ningxia download today.** Everything in C2 depends on it, and the failure mode is slow rather than loud. (§4.4)
2. **Fix the Universal→FDI lower-arch bug** in *both* `configs/dataset_config.yaml` (lines 122–131) and `src/utils/fdi_converter.py` (lines 20–22) — they are independently wrong in the same way. Add `tests/test_fdi_converter.py` coverage. Every lower-jaw finding is currently mis-numbered.
3. **T0.1 — the augmentation audit.** Read the caries training code, determine what actually ran, pick a path, write it down. Nothing in the research paper is trustworthy until this is closed.
4. Provision the E2E H100 instance and verify the Ultralytics + PyTorch environment.
5. Start the IRB / ethics paperwork for clinic data — longest lead time of anything, zero critical-path cost.
6. Email the PES library re: Read-and-Publish agreements (Springer/Oxford/Elsevier/Wiley) — five minutes, potentially saves $2–3k.
7. Confirm authorship order and the ISBI-vs-journal decision with Dr. Mamatha H R.

---

## 11. Open questions for the team

1. **Is the ISBI 4-page constraint acceptable**, or is a full journal paper preferred even at the cost of losing the October forcing function?
2. **Who owns the survey track?** It cannot share the critical path with the research paper, and §5.1 assumes it is separately owned.
3. **Is a dentist available at all** in the next 8 weeks, even for a few hours? Not needed for this plan — but a few hours of expert review of the failure taxonomy would materially strengthen C2 at near-zero cost.
4. **Does anyone on the team have a Baidu account?** See §4.4.
