# Clinical Dataset Implementation Plan

**Scope:** Turning the audited real-world dental clinic OPG dataset (~3,329 patient studies, 4,420 converted PNGs) into usable research material for this capstone.
**Source of facts:** the June 2026 dataset audit (`SESSION_MEMORY.md`, `checkpoint.json`, `FINAL_DATASET_AUDIT_REPORT.md` on the audit machine at `D:\dataset_audit`).
**Status:** planning document. Nothing in this plan has been executed yet.

---

## 1. What we actually have (verified from the audit)

| Property | Value | Source |
|---|---|---|
| Raw files / folders | 11,085 files, 3,356 folders | audit inventory |
| Estimated patient/study folders | 3,329 (`.RVG` hierarchy), 3,345 patient-like folders | audit inventory |
| `.PANO` files | 4,433 | audit inventory |
| Valid DICOM `.PANO` | 4,421 (DICM preamble present) | PANO format scan |
| Converted to grayscale PNG | 4,420 (99.71% success); 13 failures | conversion report |
| Transfer syntax | `1.2.840.10008.1.2.4.70` (JPEG Lossless, Nonhierarchical, First-Order Prediction) | format scan |
| Device | Carestream Health, **CS 8100**, modality `PX` | format scan |
| Bit depth | 16 allocated / **12 stored** | format scan |
| Photometric | MONOCHROME2 (4,417), MONOCHROME1 (4) | format scan |
| Geometry | height fixed **1,316 px**; width **837–3,001 px** (mode ~2,700–2,900) | quality analysis |
| Orientation | 4,414 horizontal, 3 vertical, 3 unknown-aspect | quality analysis |
| Duplicates | 0 (full SHA-256 hashing) | duplicate scan |
| Metadata | 3,296 `PatientInfo.xml`, 3,343 `FILEDATA.TXT` | inventory |
| Repeat scans | 1,015 folders contain more than one scan | Decision #5 |
| Labels | **None. Zero. Completely raw.** | audit |
| Sample gallery already built | 96-image manifest + contact sheet | sample gallery update |

Audit's own readiness scores (after curation): **caries detection 50/100**, **caries severity grading 35/100**, **periodontal / alveolar bone loss 70/100**. The audit explicitly recommends targeting periodontal disease first.

Audit's visual-review prevalence estimates (sample-level, not verified counts): restorations/crowns/bridges >50%, missing teeth 30–50%, RCT-treated 15–35%, implants 10–25%, orthodontic appliances and impacted teeth present as minorities, periodontal bone loss visually present but requiring expert site-level grading, caries prevalence unknown.

One artifact worth reconciling: `checkpoint.json` records a separate processing run with `completed_output_images: 3219` and one image excluded as `quality:insufficient_opg_resolution`. That implies a downstream per-image processing pass over ~3,220 of the 4,420 images already exists somewhere. **Action: find and document what produced that checkpoint before assuming the PNG set is the only derived artifact.**

---

## 2. Domain-shift risk register (clinic data vs. Tufts / DENTEX)

This is the crux: our trained models have never seen a Carestream CS 8100 image. The literature is unambiguous that this matters. A July 2026 *Frontiers in Medicine* review of clinical translation for caries AI reports that models achieving AUC 0.76–0.98 under controlled conditions "routinely degrade to AUC values of 0.53–0.57 due to severe domain shift," and that domain adaptation techniques recover only "0.1–34.2% of the precision drop" — see [Artificial intelligence for dental caries diagnosis: translating algorithms to clinical practice](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1879708/full). Near-chance AUC after a vendor switch is a real, documented outcome, not a hypothetical.

| # | Shift axis | Our training data | Clinic data | Expected impact | Mitigation |
|---|---|---|---|---|---|
| D1 | **Device / vendor** | Tufts Dental Database (Tufts Univ. School of Dental Medicine acquisition, see [IEEE Access / PubMed record](https://pubmed.ncbi.nlm.nih.gov/34606466/)); DENTEX (Hamamci et al., [arXiv:2305.19112](https://arxiv.org/abs/2305.19112)) | Carestream CS 8100, single clinic | Different detector response curve, beam hardening, sharpening kernels. Highest-risk axis. | Histogram matching / CLAHE normalisation to training-set statistics; report metrics before and after |
| D2 | **Resolution & aspect** | Tufts 840×1615 (portrait-ish aspect ≈0.52); DENTEX ~1316×2900-class | Clinic **1316 H × 837–3001 W**, i.e. landscape, aspect up to ~2.28 | YOLO letterboxing behaves differently; tooth pixel-scale differs; crop-expansion ratios (1.5×W / 2.0×H) were tuned at a different scale | Resample clinic images to the detector's training scale *by tooth size*, not by whole-image resize; verify mean tooth bbox area matches training distribution |
| D3 | **Bit depth / intensity range** | 8-bit JPG/PNG (0–255) | 16-bit container holding **12-bit** values (0–4095), no windowing applied | Direct 16-bit load into an 8-bit-trained model is a silent catastrophic failure. The audit already hit this: initial thresholds flagged **all 4,420** images as dark/blurry/low-dynamic-range purely from the 12-bit-in-16-bit mismatch (Decision #4). | Explicit, documented 12-bit → 8-bit mapping (per-image percentile windowing, e.g. 0.5–99.5%). Freeze this as a preprocessing contract and unit-test it. |
| D4 | **Photometric interpretation** | MONOCHROME2 assumed | 4 images MONOCHROME1 (inverted) | 4 images will be inverted; small but will look like model failure | Read `PhotometricInterpretation` tag, invert MONOCHROME1 at conversion. Flag these 4 explicitly. |
| D5 | **Clinical heterogeneity** | Tufts/DENTEX are curated research sets; DENTEX in particular is filtered to abnormal-tooth cases | >50% restorations/crowns/bridges, 30–50% missing teeth, 10–25% implants, 15–35% RCT, ortho appliances, impacted teeth, post-surgical cases | Metal restorations and implants produce high-intensity artifacts that a caries classifier can easily read as "not caries" or a bone-loss classifier as "bone." Missing teeth break FDI numbering assumptions. | Restoration/implant/missing status must be a first-class annotation field, and a "non-assessable" escape hatch must exist for every tooth-site label |
| D6 | **FDI numbering under missing teeth** | Full or near-full dentition | 30–50% of studies have missing teeth | Positional FDI assignment degrades when arch is sparse; errors cascade into every downstream per-tooth label | Evaluate numbering accuracy separately on high-missing-tooth cases; report it as a stratified metric |
| D7 | **Population / demographics** | US academic dental school (Tufts); DENTEX European multi-center | Single clinic, different population, different care patterns | Prevalence shift changes calibration even if discrimination holds | Report prevalence-adjusted metrics (PPV/NPV at observed prevalence, not just sensitivity/specificity) |
| D8 | **Repeat scans / pre-post treatment** | Single image per patient | 1,015 folders with repeat scans; audit found **no** filename-derivable pre/post labels (Decision #5) | Same patient appearing in both train and test = leakage; treatment change between scans breaks label validity | Patient-level splitting (§6), and default to one baseline scan per patient for cross-sectional work |

**Bottom line:** assume the existing models will *not* transfer zero-shot at their reported Tufts/DENTEX numbers. That is not a problem — **measuring how much they drop is itself the publishable result.**

---

## 3. Three usage tiers

### Tier 1 — External validation only (no new labels needed for the cheapest variant) — **RECOMMENDED NEAR-TERM PRIORITY**

**What:** Run the existing frozen YOLOv11l detector + FDI numbering + caries and bone-loss classifiers over a stratified sample of clinic images. No fine-tuning, no retraining. Measure generalisation.

**Two sub-variants:**

- **1a — Label-free diagnostics (week 1–2, zero annotation cost).** Reportable without any ground truth:
  - Detector behaviour: teeth detected per image (expected 24–32 for full dentition; distribution vs. Tufts), confidence-score distribution shift, rate of anatomically impossible outputs (duplicate FDI codes, left/right inconsistency, overlapping boxes).
  - Classifier behaviour: predicted-probability histograms vs. the Tufts/DENTEX validation distributions; entropy / max-softmax as a proxy for distribution shift; fraction of predictions in the uncertain band.
  - Failure taxonomy: bucket qualitative failures by the D5 categories (implant present, heavy restoration, ortho, edentulous region).
  - Preprocessing ablation: same images with and without the 12-bit windowing fix (D3) — this quantifies how much of the drop is preprocessing vs. genuine domain shift, and it is a genuinely useful methodological contribution.
- **1b — Expert-graded external test set (weeks 3–6, ~200–300 images).** Adds real numbers: sensitivity/specificity/F1 on clinic data vs. on Tufts/DENTEX val. This is the headline claim.

**Why this is the recommendation:**
1. **It is the highest-value-per-hour thing available.** The systematic review literature says external validation is the single most commonly missing element. A 2025 *Dentomaxillofacial Radiology* systematic review + meta-analysis of 30 ML/DL studies on periodontal bone loss from 2D radiographs scored **zero** papers as "very high quality" (≥80 on APPRAISE-AI), 63.3% only "intermediate," and named limited external validation as a headline weakness — [Detection of periodontal bone loss and periodontitis from 2D dental radiographs via machine learning and deep learning](https://academic.oup.com/dmfr/article/54/2/89/7917334). A July 2026 *Healthcare* systematic review of 15 imaging-AI-in-dentistry studies similarly found external performance "often declined relative to internal results without clear documentation of failure modes" — [From Algorithmic Performance to Clinical Translation](https://www.mdpi.com/2227-9032/14/13/1952).
2. **It converts our biggest weakness into our biggest strength.** Right now the project has zero external validation. Tier 1 flips that in weeks, not months.
3. **A negative result is still a result.** "Our Tufts-trained bone-loss classifier drops from F1-macro 0.92 to X on unseen Carestream CS 8100 clinic data, and here is the failure taxonomy" is a publishable, honest, useful finding. The Frontiers review above establishes that this is an actively discussed problem, so the framing has an audience.
4. **It respects the data-location constraint.** Inference over a few hundred images can run in Colab against Drive directly (§5).

**Deliverable:** a domain-shift report with per-stage metrics on clinic data, side-by-side with Tufts/DENTEX numbers, plus a failure taxonomy with example images.

### Tier 2 — Small-scale fine-tuning / domain adaptation

**What:** Once Tier 1b's ~200–300 annotated images exist, hold out ~half as a locked test set and use the rest for light-touch adaptation: fine-tune the detector's last layers, or (cheaper and often as effective) fit an intensity-normalisation transform and re-calibrate the classifier thresholds without touching weights.

**When:** only after Tier 1 has produced a number to improve on. Do not start here — without a Tier 1 baseline, a fine-tuning result has nothing to be measured against and reads as "we trained on some data."

**Realistic in a capstone:** yes, as a second phase, *if* Tier 1b annotation completes. Budget 2–3 weeks after annotation.

**Caveat, stated honestly:** the Frontiers 2026 review's figure that domain adaptation recovers only 0.1–34.2% of the precision drop should temper expectations. Set the success criterion as "measurable recovery with a documented method," not "restores original performance."

### Tier 3 — Full annotation + retraining as a new benchmark

**What:** Annotate several thousand images, build a new public/semi-public benchmark, retrain from scratch, release.

**Verdict: out of scope for this capstone.** Reference point: [BRAR](https://www.nature.com/articles/s41597-025-06400-y) (*Scientific Data*, Dec 2025) used 1,104 patients with **three trained periodontists** grading independently plus **two 20-year senior specialists** doing final review. [DentFound](https://www.nature.com/articles/s41551-026-01713-8) (*Nature Biomedical Engineering*, Jun 2026) used >101,000 patients. We cannot compete on that axis, and should not try.

**But:** keep Tier 3 alive as a *stated future direction* with a concrete on-ramp. If PHI/de-identification and clinic consent are resolved, even a 500-image expertly-annotated Carestream CS 8100 subset is a legitimate dataset-resource contribution — [MICCAI's Open Data track](https://conferences.miccai.org/2026/en/MICCAI-2026-Open-Data-Call-for-Papers-and-Reviewers.html) explicitly solicits "novel medical imaging datasets, particularly from underrepresented populations" and publishes to the MELBA Journal Resource Track. (The MICCAI 2026 Open Data submission deadline was 19 June 2026 and has passed; treat this as evidence that the *venue type* exists and recurs, not as a live deadline.)

**Recommendation summary: do Tier 1a immediately, Tier 1b as the main annotation push, Tier 2 if time permits, document Tier 3 as future work.**

---

## 4. Annotation protocol proposal

Scoped to what a student team plus (ideally) one cooperating dentist can realistically produce. Follows the audit's own medium-priority recommendations, tightened into something executable.

### 4.0 Prerequisites (do these before a single label is drawn)
- **De-identification decision.** The audit lists this as an open question. `PatientInfo.xml` almost certainly contains PHI, and DICOM headers do too. Before any image leaves the clinic environment or reaches an annotator: strip DICOM tags, do not carry `PatientInfo.xml` forward, and replace folder names with opaque study IDs via a mapping table kept separately. Record the clinic's permission in writing.
- **Written annotation guideline document**, versioned, with worked examples and explicit "when in doubt" rules. The audit lists this as high-priority action #3 for a reason: heterogeneous ground truth is a named weakness in the DMFR systematic review above.
- **Calibration round.** All annotators label the same 20 images, disagreements are discussed, guideline is revised, *then* production annotation starts.

### 4.1 Image-level (fast, ~30 s/image, whole team can do it)
| Field | Values |
|---|---|
| `diagnostic_quality` | good / acceptable / non-diagnostic |
| `orientation_ok` | yes / no (flags the 3 vertical + 3 unknown cases and any others) |
| `dentition` | permanent / mixed / primary |
| `ortho_appliance_present` | yes / no |
| `implants_present` | yes / no / count |
| `gross_artifact` | none / motion / ghost / positioning / metal-scatter |
| `periodontal_impression` | none / mild / moderate / severe / not-assessable (screening-level gestalt only) |

Target: all ~500 images of the working subset. This alone gives stratification variables and a prevalence estimate, which the audit currently lacks.

### 4.2 Tooth-level presence & status (the workhorse layer)
Per FDI-numbered tooth site, from the model's own detection output (annotator corrects rather than draws from scratch — 3–5× faster):
| Field | Values |
|---|---|
| `fdi_code` | 11–48, or `corrected_to` if the model's number is wrong |
| `present` | present / missing / retained-root / unerupted-impacted |
| `restoration` | none / filling / crown / bridge-abutment / pontic |
| `endodontic` | none / RCT / post-and-core |
| `implant` | yes / no |
| `assessable` | yes / no (**mandatory escape hatch** — this field is what makes the dataset honest) |

Rationale: these are exactly the D5 confounders. Without them we cannot stratify results, and reviewers will ask "how does it do on restored teeth?" — a question we currently cannot answer for *any* dataset.

### 4.3 Periodontal landmarks — the primary target
Consistent with the audit's 70/100 readiness score and its recommendation to lead with periodontal.

Per assessable tooth, per site (mesial + distal = 2 sites/tooth):
- **CEJ point** (x, y)
- **Alveolar crest point** (x, y)
- **Root apex point** (x, y)
- Derived: `RBL% = |CEJ − crest| / |CEJ − apex| × 100`
- `site_assessable`: yes / no

This is a directly validated design. The Feb 2026 *Scientific Reports* study used YOLOv8x for tooth detection plus **three separate Keypoint R-CNN models** for exactly CEJ / bone-level intersection / apex, reaching keypoint AP50:95 of 0.815–0.954 and ICC 0.801 for severity — [AI-assisted radiographic analysis in detecting alveolar bone-loss severity and patterns](https://www.nature.com/articles/s41598-026-38061-1) (note: that study is on **intraoral periapical** radiographs and the DenPAR dataset, not panoramic — a real differentiator for us). An April 2026 *Oral Radiology* study did the panoramic version with **six anatomical landmarks per tooth** via YOLOv11 keypoint detection on 607 panoramics / 15,605 cropped teeth, reaching keypoint mAP50 >0.958 and ICC vs. dentists of 0.705–0.871 — [Automated periodontitis diagnosis and staging using an end-to-end deep learning model on panoramic dental radiographs](https://link.springer.com/article/10.1007/s11282-026-00921-x).

**Two implications for us.** (1) Our current CEJ-based classical-CV module (15% agreement with the primary model) is doing by hand what the field now does with a learned keypoint head — this is a concrete, evidence-backed upgrade path, not speculation. (2) The panoramic landmark space is *already occupied* as of April 2026, so we should position around external validation and cross-device robustness rather than around "we detect CEJ landmarks."

Grading convention: use the 2017 AAP/EFP radiographic-bone-loss thresholds (the Oral Radiology study above stages against them), and additionally record raw RBL% so the data is re-gradeable under any future convention. Optionally compute BRAR = (RBL/root length)/age per the [BRAR](https://www.nature.com/articles/s41597-025-06400-y) formulation, since `PatientInfo.xml` likely carries age — cheap to add, gives a second comparable axis.

Target: 200–300 images fully landmarked. At ~24 assessable teeth × 2 sites × 3 points, that is ~144 clicks/image; assume 8–12 min/image for a trained annotator, so ~40–60 hours total. **This is the single largest cost item in the plan — budget it honestly.**

### 4.4 Caries flags — secondary, deliberately coarse
The audit scores caries severity grading at 35/100 and warns panoramics are poor for early/proximal caries. Do not attempt enamel/dentine/pulp staging on this data.

Per tooth: `caries_visible` ∈ {no / suspicious / clearly-present / not-assessable}. Nothing finer. Anything requiring bitewing correlation is out of reach — note that the Sep 2025 *Scientific Reports* multistage caries study explicitly used bitewings to establish ground truth for panoramic caries ([Clinical application of deep learning for enhanced multistage caries detection in panoramic radiographs](https://www.nature.com/articles/s41598-025-16591-4)); we have no bitewings, therefore we cannot establish comparable ground truth, therefore we should not claim caries severity results on clinic data at all.

### 4.5 Reliability measurement (non-negotiable)
- Double-annotate **≥50 images** (or 15%, whichever is larger) with disagreement resolved by a third rater or discussion.
- Report Cohen's/Fleiss' κ for categorical fields and ICC for RBL%. BRAR reported κ = 0.88 on a 50-image held-out subset; HC-Net+'s multicenter study reported specialist inter-rater κ = 0.64 and treated it as a *limitation* ([npj Digital Medicine, Nov 2025](https://www.nature.com/articles/s41746-025-02077-0)). Whatever we get, report it.
- Reviewers will ask for this. Not having it is a rejection risk on its own.

### 4.6 Tooling
Use an existing labeler (CVAT, Label Studio, or Roboflow) with model-assisted pre-annotation from our own detector. Do not build a custom tool — it is a time sink with no publication value.

---

## 5. Google Drive / data-size strategy

**Non-negotiable principle: compute goes to the data; the data does not come to the compute.** The full converted PNG set at 12-bit-in-16-bit, ~2,800×1,316, is on the order of tens of GB. Downloading it into any sandboxed working environment is wasted days.

### 5.1 Tiered access pattern
| Layer | Size | Where it lives | Who touches it |
|---|---|---|---|
| **L0 — full raw + full PNG set** | tens of GB | Google Drive, untouched | Nobody, except batch jobs run *in Colab* |
| **L1 — stratified working subset (~500 images)** | ~2–4 GB | Drive folder + optional local copy | Annotation, Tier 1b/2 |
| **L2 — annotation batch (200–300)** | ~1–2 GB, downsampled 8-bit PNG | Local / labeling tool | Annotators |
| **L3 — audit's existing 96-image sample gallery + manifest** | <500 MB | Already exists | **Start here, this week** |

### 5.2 Concrete steps
1. **Start from what already exists.** The audit already produced `technical_sample_manifest.csv` (96 images) and a contact sheet. That is a zero-cost Tier 1a pilot set available today. Use it to shake out the preprocessing pipeline (D3/D4) before touching anything larger.
2. **Build the stratified subset manifest in Colab, not locally.** Mount Drive (`drive.mount('/content/drive')`), read only the audit's `quality_metrics.csv` / `inventory_files.csv` (small CSVs, cheap to pull anywhere), and compute the sample selection from metadata alone. Stratify on: sharpness quartile, contrast quartile, image width bucket, orientation, and repeat-scan status. Write out `clinical_subset_manifest.csv` with study IDs. **The manifest is what moves between environments, never the pixels.**
3. **Run inference in Colab against Drive directly.** Stream image-by-image, write only per-image JSON predictions back. Predictions for 4,420 images are a few MB — those *can* live in the repo and be analysed anywhere. This makes even a full-dataset Tier 1a inference run feasible without downloading anything.
4. **Download only L2.** For annotation, export 200–300 images already windowed to 8-bit and downsampled to a labeling-friendly size. Keep the 12-bit originals in Drive and re-derive from them if the windowing choice changes.
5. **Never commit images to git.** Manifests, prediction JSON, metrics CSVs, and figures only. Add the subset folder to `.gitignore`.
6. **Explicit constraint for future agent sessions:** do not attempt to pull the clinical dataset into a sandboxed agent environment. All full-dataset operations happen in Colab against Drive, or on the machine that already has the data. Agent sessions work on manifests, metrics, and code.

### 5.3 Reproducibility hooks
- Store the exact selection script and a random seed alongside the manifest.
- Record a SHA-256 for every image that enters the working subset (the audit already hashed everything, so reuse those hashes rather than recomputing).
- Version the manifest (`clinical_subset_manifest_v1.csv`) and never edit in place.

---

## 6. Patient-level split discipline

The project already applies patient/image-level splitting on Tufts. Apply it here from day one, and more strictly, because this dataset has a repeat-scan structure that Tufts does not.

**Rules:**
1. **Split unit = patient folder** (the `X.RVG/X0000123` identity), never the image. 1,015 folders contain multiple scans; splitting on images would leak the same patient across train and test.
2. **Nested folders count as the same patient.** The audit found at least one nested case (`M.RVG\M0000140\M0000437\P1.pano`). Resolve patient identity to the top-level `.RVG` study folder and verify against `PatientInfo.xml` identifiers where present (3,296 of 3,345 have one) — but treat the folder as authoritative when metadata is missing.
3. **One baseline scan per patient for cross-sectional tasks.** The audit's own open question. Default: earliest scan by date. Repeat scans are held aside as a separate longitudinal pool, not silently mixed in.
4. **No pre/post-treatment inference from filenames.** Audit Decision #5 established there are no pre/post markers in the paths. Do not create such labels from filenames. If longitudinal work happens later, it needs date sequence *plus* visible treatment change *plus* ideally clinical records.
5. **Because Tier 1 is external validation, the whole clinic set is test data.** No clinic image used to select a threshold, pick a checkpoint, or tune preprocessing may later appear in a reported test metric. If Tier 1a is used to tune the intensity windowing, those images are burned — carve out a distinct locked evaluation subset before any tuning happens, and say so in the paper.
6. **Write the split as code with a fixed seed**, emitting a `splits.json` keyed by patient ID that is committed to the repo. Never regenerate ad hoc.

---

## 7. Phased timeline (capstone-realistic, in weeks)

Assumes a small student team working part-time. Dentist availability is the main external dependency and the main schedule risk.

| Phase | Weeks | Work | Exit criterion |
|---|---|---|---|
| **P0 — Plumbing** | 1 | Locate what produced `checkpoint.json` (3,219 images). Reconstruct the 96-image sample gallery. Write and unit-test the 12-bit→8-bit windowing + MONOCHROME1 inversion preprocessing contract. Confirm Colab-Drive mount works. | Preprocessing function with tests; 96 images loadable and visually correct |
| **P1 — Tier 1a, label-free** | 2–3 | Run frozen detector + classifiers over the 96-image gallery, then over a 500-image stratified subset. Collect detection counts, confidence distributions, FDI consistency violations, prediction-entropy shift. Preprocessing ablation (windowed vs. naive). Build failure taxonomy with example crops. | Domain-shift report v1 with figures; a defensible answer to "does it transfer?" |
| **P2 — Annotation setup** | 3–4 | De-identification pipeline. Written annotation guideline v1. Labeler configured with model-assisted pre-annotation. 20-image calibration round with the dentist. Guideline v2. | Calibrated guideline + working tool + measured pilot κ |
| **P3 — Annotation production** | 5–9 | 200–300 images: image-level fields + tooth presence/status for all; periodontal landmarks for the full set; coarse caries flags. ≥50 double-annotated. Rolling QC. | Locked annotated test set + reliability statistics (κ, ICC) |
| **P4 — Tier 1b, real external metrics** | 9–10 | Sensitivity/specificity/F1/AUC for bone-loss binary and severity on clinic data vs. Tufts val. Stratified by restoration/implant/missing status. Detection mAP and FDI numbering accuracy against corrected labels. Calibration curves at clinic prevalence. | **The headline result table.** |
| **P5 — Tier 2, adaptation (conditional)** | 11–13 | Split the annotated set into adapt/test. Try (a) intensity normalisation only, (b) threshold recalibration only, (c) light detector fine-tuning. Report recovery against the P4 baseline. | Recovery figures with the locked test set never touched during adaptation |
| **P6 — Write-up** | 12–14 | Integrate into the paper; CLAIM-style reporting ([CLAIM 2024 Update](https://pubs.rsna.org/doi/full/10.1148/ryai.240300)); limitations section written honestly | Draft with external-validation section complete |

**Critical path:** P2→P3 (annotation) gates everything downstream. **If the dentist is unavailable, P1 alone still produces a genuine, reportable contribution** — this is why Tier 1a is deliberately designed to need zero labels. Do not let the whole clinical-validation story depend on annotator availability.

**Risk register:**
| Risk | Likelihood | Mitigation |
|---|---|---|
| Dentist unavailable / slow | High | P1 is label-free and standalone; degrade gracefully to Tier 1a only |
| PHI/consent blocks external annotation | Medium | Resolve in P0/P2, before annotation starts, not after |
| Models transfer far worse than hoped | Medium-High | Reframed as the finding, not a failure. Budget the failure taxonomy as a deliverable. |
| Annotation slower than 8–12 min/image | Medium | Cut landmark scope to posterior sextants only; keep tooth-status layer at full coverage |
| Colab session limits on full-set inference | Medium | Checkpointed batch inference (the existing `checkpoint.json` pattern already demonstrates this works) |

---

## 8. Open questions carried forward from the audit

Unresolved, and each blocks something:
1. What produced `checkpoint.json` (3,219 processed images)? — blocks P0.
2. PHI / de-identification policy before images reach annotators? — blocks P2.
3. Dentist availability and hours committed? — blocks P3, i.e. the entire annotation track.
4. Are external clinical records available to confirm treatment dates / periodontal diagnoses? — would upgrade ground truth from radiographic-only to clinically-anchored, which is what the [HC-Net+ multicenter study](https://www.nature.com/articles/s41746-025-02077-0) did and is a meaningful quality step.
5. Caries definition on panoramic: gross-visible only (recommended) vs. anything finer (not feasible without bitewings).
6. The 13 failed `.PANO` files — low priority; document as excluded, do not chase.
