# SDH clinic dataset — execution plan

**Written:** 30 August 2026. **Status:** plan, not a record of work done. Everything in §1 was
measured today against the actual files; everything in §3–§8 is proposed and not yet executed.

**Why this document exists.** Oral consent to use the SDH clinic dataset for this project was
obtained from the clinic; the written agreement is expected **1 September 2026**. That closes
the blocker that made `PUBLICATION_TODO.md` T1.2 "governance-blocked" and makes the clinic
track runnable. This is the plan for running it: what the data can and cannot produce, how it
is filtered, what compute it needs, and in what order.

**Relationship to the two existing clinic docs — read them, they are not superseded.**

| Doc | What it is | Still true? |
|---|---|---|
| `clinical_dataset_provenance.md` | Factual record of where the data lives and exactly what preprocessing has already run on it | **Yes.** §2's enhancement algorithm and §3's PREOP policy are the input contract for this plan |
| `clinical_dataset_plan.md` | The strategy document written when clinic data was the *primary* external validation route | **Analysis yes, sequencing no.** `MASTER_PLAN_2026H2.md` §1 demoted the clinic track to a second validation stream in August; its §7 timeline is superseded |

This document supersedes neither. It is the *execution* layer under both, written now that
consent exists and the deadline is 14 October.

---

## 1. Verified facts — measured 30 August 2026, not recalled

Every row was checked against the files today. Where a previously-written document disagrees,
the disagreement is named.

### 1.1 The data

| Property | Value | How checked |
|---|---|---|
| Enhanced training-ready set | 3,219 files, `D:\SDH dataset\dataset\images\`, 3.72 GB — of which **3,213 are readable** (§1.4) | file scan |
| Format | 8-bit grayscale PNG, mode `L`, opaque IDs `000001.png`… | PIL header scan, all 3,219 |
| Geometry | **height fixed 1,316**; width **2,043–3,001** (median 2,792); 405 distinct sizes | PIL header scan |
| Aspect ratio | 1.55 – 2.28 (median 2.12), i.e. **landscape** | derived |
| Patients | `metadata/index.csv` has **3,220 rows and 3,220 distinct `source_folder` values** — one image per patient, exactly | join; no identifier printed or stored |
| Kept / excluded | 3,219 `completed_previous`, 1 `excluded_quality:insufficient_opg_resolution` | `index.csv` status column |
| Acquisition device | **Carestream CS 8100**, all 4,421 valid source DICOMs, single manufacturer | audit `pano_format_summary.csv` |
| Source bit depth | 12 stored / 16 allocated, transfer syntax JPEG-Lossless | audit |
| Photometric | MONOCHROME2 ×4,417, **MONOCHROME1 ×4** | audit |
| Study dates | **2000-02-12 → 2024-11-27**; modal year 2013 (1,044); ≈2,900 scans from 2015 onward | audit `study_date` |
| Labels | **none, zero, for anything** | audit |

**⚠️ Two tracked documents say the clinic data is "Not on this machine". Both are wrong** as of
today: `transfer.md` §8 and `data/README.md`. The full Stage-2 tree, the raw `.pano` tree, the
Stage-1 conversion and every audit CSV are all present on this Windows machine on `D:`.
Corrected in both files in this session.

### 1.2 The structure nobody has exploited yet — repeat scans

The 3,219 set is a **one-scan-per-patient PREOP baseline** (`clinical_dataset_provenance.md`
§3). The scans it dropped are still on disk in `D:\dataset_audit\outputs\converted_png\`, and
they are an asset, not waste:

| | Count |
|---|---|
| Patients in the raw tree | 3,228 |
| Patients with **more than one** scan | **1,013** |
| Patients whose repeats all share one study date (a retake) | **145** |
| Interval, first to last scan, multi-scan patients (n=1,009) | median **38 days**, p25 18, p75 428, max 8,165 |
| Pairs ≤30 days apart | 420 |

**Two things follow, and both are cheap, label-free and unique to this dataset.** No public
panoramic corpus this project uses — Tufts, DENTEX, Ningxia — ships repeat acquisitions of the
same patient.

1. **Test–retest repeatability.** Two acquisitions of the same patient on the same day cannot
   differ clinically. Running the pipeline on both and measuring agreement (tooth count, FDI
   map, per-tooth verdicts) is a **reliability** measurement that needs no ground truth at all.
   Almost no dental-AI paper reports one; reviews cited in `clinical_dataset_plan.md` §3 name
   reliability among the missing elements.
2. **A free weak label for "non-diagnostic image".** A same-day retake usually means the
   operator judged the first acquisition inadequate. That gives ~145 pairs on which a quality
   filter can be *validated* rather than merely asserted: does the filter score the
   first-of-pair worse than the retake, more often than chance?

**And a defect this exposes, verified today.** The PREOP policy keeps the *earliest* scan per
patient. For all **144** same-day retake groups represented in the kept set, the image retained
is the **lowest-numbered scan of the group** — i.e. plausibly the one the clinic rejected and
re-took. The current 3,219 set may therefore be systematically holding the discarded image for
those 144 patients. Not fatal (4.5% of the set) but it must be settled before any locked
evaluation subset is drawn, and it is a concrete argument for the filter in §4.

*Caveat, stated because it limits the claim:* same-day repeats are not always retakes — a
second view or a post-extraction check would look identical in the file structure. Treat the
retake label as **weak**, validate it directionally, and visually spot-check ~30 pairs before
reporting anything from it.

### 1.3 The pipeline already runs on this data — measured today

The frozen six-stage pipeline (`scripts/run_inference.py`, R1 seg detector + Stage-2 head v2.0)
was run unmodified over a deterministic sample of **24 SDH images** (every 134th, so spread
across the whole ID range), and over **24 DENTEX `disease/` images** as an in-domain reference,
same code path, same settings, same machine, same hour.

| | **SDH** (n=24) | DENTEX (n=24, reference) |
|---|---|---|
| Teeth detected / image — min / median / max | 5 / **27** / 30 | 5 / 21 / 31 |
| Images with 0 teeth | **0** | 0 |
| Mean detection confidence | **0.407** | 0.373 |
| Caries-positive teeth / image | 1.67 (**6.2%** of detected) | 5.04 (24.0%) |
| Bone-loss-positive teeth / image | 0.54 (**2.0%** of detected) | 0.04 (0.2%) |
| Throughput, CPU, models loaded once | **2.2 s/image** | 2.2 s/image |

**Read these four ways and no further — n=24, no labels, and DENTEX is training-domain for the
caries gate, so it is a reference distribution, not a control.**

1. **Stage 1 does not visibly collapse on SDH.** More teeth per image and *higher* mean
   confidence than on DENTEX. The likely reason is mundane: SDH is consecutive clinic
   panoramics with mostly complete dentition, DENTEX is curated to abnormal-tooth cases. This
   is the opposite of the outcome `clinical_dataset_plan.md` §2 warned about, and it is the
   single most encouraging fact in this document. It is **not** evidence that detection is
   *accurate* here — only that it is not degenerate. Recall is unmeasurable without labels.
2. **Bone loss fires on 2.0% of teeth.** The documented collapse is 0.7% on DENTEX and 2.4% on
   Ningxia (`PAPER_MATERIAL.md` §8.13). SDH lands with Ningxia. **This independently confirms a
   limitation already decided; it does not reopen it.** Do not spend time here.
3. **Caries fires 4× less often than on DENTEX.** Expected — DENTEX is enriched for disease,
   SDH is consecutive patients — but prevalence shift and sensitivity loss are
   indistinguishable without labels. That gap is precisely what Tier B (§2) exists to close.
4. **2.2 s/image on CPU settles the compute question** (§5). The full 3,219-image set is a
   **~2-hour CPU job**. It needs no GPU.

**One measurement artefact not to repeat:** duplicate-FDI count was 0 on all 48 images because
the pipeline runs one-to-one Hungarian assignment, which cannot emit a duplicate. To use
FDI-consistency violations as a domain-shift signal, the run must pass `--no-one-to-one`.

### 1.4 Six images are corrupt, and `checkpoint.json` does not know it

Found today, on the first pass that ever opened all 3,219 files:

**`001970.png` … `001975.png` are truncated and cannot be decoded** — `cv2.imread` returns
`None`, PIL raises `OSError: image file is truncated`, libpng reports a read error. Six
contiguous IDs.

The cause is legible from the artefacts and is not a mystery:

- All six file sizes are **exact multiples of 4,096** (1,003,520 / 860,160 / 565,248 / 466,944 /
  180,224 / 69,632 bytes = 245 / 210 / 138 / 114 / 44 / 17 blocks) — the signature of writes
  truncated at a filesystem block boundary, i.e. an unflushed buffer, not a bad source image.
- `preprocessing_run.log` opens with **`Resume checkpoint: 1975`** and queues `first new id:
  001976`. The June run was interrupted with those six images in flight, and the resume logic
  correctly restarted *after* the checkpoint — so it never revisited the six partial files it
  had left behind.
- `checkpoint.json` therefore claims `completed_output_images: 3219`, and that count is **wrong
  by six**. Nothing has ever verified it, because nothing had ever opened every file.

**Consequences, in order of importance:**

1. **The usable set is 3,213, not 3,219.** Every count in this plan, the split in §3 and any
   number reported later must use 3,213.
2. **The L1 "decodes" check in §4 is not ceremony.** It was written as a tripwire against a
   future rebuild; it caught a defect that has been sitting in the dataset for three months.
3. **It is repairable.** The six source `.pano` files are intact in `D:\raw data\`, and the
   enhancement pipeline is checkpointed and re-runnable. Re-deriving six images is minutes of
   work — but only *after* the hardcoded `D:\dataset_audit\dataset` output path is fixed
   (`clinical_dataset_provenance.md` §7), or the repair writes to a non-existent path and forks
   the dataset. Repair before freezing the split; whichever way it goes, the split must record
   the decision.
4. **Assume nothing else about this dataset has been integrity-checked either.** Add a
   full-set decode-and-hash pass to task 1 in §6.

---

## 2. How far this dataset can go — the honest ceiling

Four tiers. A is certain, B is dentist-gated, C is conditional, D is out of scope. **Only A is
on the path to 14 October.**

### Tier A — label-free external diagnostics + repeatability. No labels, no dentist, no GPU.

Deliverable: SDH as a **fifth independent source, and the only different-vendor,
different-population one** in the paper — reported as behaviour rather than accuracy — plus a
repeatability result the other four corpora cannot produce.

What it yields:
- Detection-behaviour shift: teeth/image, confidence distribution, anatomically-implausible
  output rate, against Tufts/DENTEX/Ningxia reference distributions.
- FDI-consistency violations under `--no-one-to-one` (duplicate codes, quadrant inconsistency,
  left/right violations).
- Predicted-probability and entropy shift for both disease heads; fraction of teeth in the
  uncertain band.
- **Test–retest repeatability** on same-day pairs (§1.2).
- **Preprocessing ablation** — the June enhancement pipeline vs naive 12→8-bit — quantifying how
  much of any shift is preprocessing rather than domain. This was `clinical_dataset_plan.md`
  §3 Tier 1a's best idea and it is still unexecuted.
- **Detector input-scale ablation** (§4.5), the one lever likely to move detection.
- Failure taxonomy bucketed by the D5 confounders, with example crops.

**Certainty: high.** Everything above is measurable this week with code that already exists.

### Tier B — expert-labelled evaluation subset (150–250 images). Dentist-gated.

The only route to sensitivity/specificity/F1 on clinic data, i.e. the only route to a headline
*number*. Scope discipline, following `clinical_dataset_plan.md` §4 but cut to fit the deadline:

- Image-level fields (that document's §4.1) across the whole labelled subset — ~30 s/image.
- Tooth-level presence/status **corrected from the model's own output**, not drawn from scratch.
- **Caries: coarse only** — `no / suspicious / clearly-present / not-assessable`. No severity
  staging: there are no bitewings, so there is no defensible ground truth for it.
- **Periodontal landmarks: cut entirely** unless a dentist commits ≥40 hours. The full
  CEJ/crest/apex protocol is 40–60 h and cannot land by 14 October. Bone loss is already a
  **decided limitation** (`PAPER_MATERIAL.md` §8.13); labelling it would spend the scarcest
  resource on the branch already written off.
- ≥30 double-annotated images with κ reported.

**Certainty: medium, and entirely outside our control.** Tier A must stand alone without it.

### Tier C — using SDH for training. Conditional, and narrower than it sounds.

The dataset has **no labels**, so supervised training of the caries or bone-loss heads on it is
not possible — not "hard", not possible. What unlabelled clinic data can legitimately train:

| Route | What it does | Verdict |
|---|---|---|
| **C1 — pseudo-label detector adaptation** | Run the frozen detector on SDH-DEV, keep only high-confidence + anatomically-plausible detections, fine-tune the detector on them | **The one worth doing.** Detection bounds everything: 29.4% of GT teeth are never detected, and end-to-end Stage-2 FDI (58.3%) is detection-bound. Boxes are also the one output a non-expert can verify by eye |
| **C2 — self-supervised pretraining** of the ResNet18 backbones on SDH crops, then fine-tune on DENTEX/Tufts labels | Device-agnostic representation | Defensible, but a research programme. Does not fit before 14 Oct. **Future work** |
| **C3 — intensity/appearance normalisation** fitted on SDH-DEV | The cheapest domain adaptation there is | Do it inside Tier A as the preprocessing ablation, not as a separate training effort |
| **C4 — training the disease heads on SDH** | — | **Impossible. No labels.** If Tier B lands, 150–250 images is an evaluation set, not a training set. Do not let it become one |

C1's risk is real and must be named: a detector at ~70% recall retrained on its own confident
outputs learns its own blind spots. Mitigation is the acceptance criterion in §8.

### Tier D — explicitly out of scope

Dataset release, a public benchmark, severity grading, retraining from scratch, anything
requiring the raw tree to leave `D:`. `clinical_dataset_plan.md` §3 Tier 3 already argues this
and the argument has not changed.

---

## 3. The split — decided and frozen BEFORE anything else touches the data

This is the first task, and nothing in §4 or §5 may run before it exists.

**Why it comes first.** `clinical_dataset_plan.md` §6 rule 5: because SDH is external
validation, *the whole set is test data*, and any image used to pick a threshold, choose a
filter cut-off, tune preprocessing or select a checkpoint is **burned** for evaluation.
Choosing filter thresholds is exactly such a tuning decision. A split drawn after the filter is
designed is a split the filter has already seen.

**The split:**

- **Unit: patient.** Verified today to be identical to image-level here — 3,220 images, 3,220
  distinct patient folders, a strict 1:1. This removes the leakage risk that motivated §6
  rule 1 in the first place, and it belongs in the paper, because it is a design advantage over
  corpora that cannot guarantee it.
- **SDH-DEV — 40% (1,285 of the 3,213 readable images).** Everything that involves *choosing*
  anything: filter thresholds, preprocessing ablation, input-scale ablation, pseudo-label
  generation, visual inspection, figure selection.
- **SDH-TEST — 60% (1,928 images).** Locked. Touched once, at the end, with every parameter
  already fixed in writing. *(If the six truncated images of §1.4 are repaired before the split
  is drawn, the basis becomes 3,219 → 1,288 / 1,931. Fix or exclude them first; do not draw the
  split twice.)*
- **Stratified on** device folder (A/D/E/F/G/H/I/J/K/M — 10 acquisition folders, counts 14 to
  954), study year, image-width tercile, and quality decile from §4's metrics.
- **Seeded, written as code**, emitted to `data/sdh/splits_v1.json`, committed, never
  regenerated ad hoc.
- **25 SDH images are already burned and must land in DEV.** The 24 listed in
  `data/sdh/pilot_inference_n24.csv` (§1.3), plus `001611.png` from a two-image smoke test of the
  relocated script. The split code must assert all 25 into DEV and fail if any lands in TEST.
  Keeping this list exact is the whole point: a burned image that quietly ends up in TEST is
  indistinguishable from an honest one afterwards.
- If Tier B happens, the labelled subset is drawn **from SDH-TEST**, stratified — labelling DEV
  images produces a number that measures nothing.

**Write the rule into the split file itself** so a later session cannot plead ignorance:
`"policy": "SDH-TEST is locked. No threshold, cut-off, checkpoint, preprocessing parameter or
hyperparameter may be selected using it. Report unfiltered and filtered numbers together."`

---

## 4. Filtering — four layers, in cost order

The requirement, stated plainly: **image clarity varies far more within SDH than within the
curated public corpora**, so a per-image decision is needed. But filtering is the easiest way in
this project to accidentally manufacture a good result, so each layer carries the rule that
keeps it honest.

**The governing rule, applied to all four layers:** *no filtered number is ever reported without
the unfiltered number beside it.* The output of filtering is a **coverage–accuracy curve**, not
a single cleaner number. This is not extra work — it is contribution **C4** (calibrated
abstention, `MASTER_PLAN_2026H2.md` §2.3) applied to a new device. Framed that way, the filter
stops being data cleaning and becomes a result.

### L0 — what has already been applied (document it, do not redo it)

The June 2026 enhancement (`clinical_dataset_provenance.md` §2) already performs per-image
percentile windowing, adaptive gamma, median-targeting gain and *conditional* CLAHE at 35%
blend, plus a quality gate on aspect / resolution / dynamic range / contrast / dental-band
visibility.

Three facts about it that matter:
- **It is already an adaptive per-image normalisation.** Part of what "filtering for clarity"
  would do is done. Do not rebuild it.
- **Its gate rejected exactly 1 image of 3,220.** It is very loose. That is why L2 is needed.
- It was written in June by a script never validated against these models. **Freeze it as a
  preprocessing contract with a unit test** (`tests/test_sdh_preprocessing.py`) that reproduces
  the enhancement of a fixed reference image, so a re-run cannot silently drift. Fix the
  hardcoded `D:\dataset_audit\dataset` output path first — a re-run today writes to a path that
  does not exist and forks the dataset in two (`clinical_dataset_provenance.md` §7).

### L1 — geometry and format gate (deterministic, no model, nothing to tune)

Aspect 1.35–2.40; height ≥ 900; width ≥ 1,800; mode `L`; non-constant; decodes. All 3,219 pass
by construction — this layer exists to fail loudly if the set is ever rebuilt, not to remove
anything today.

### L2 — image-quality gate (per-image metrics, thresholds fitted on DEV only)

**Computed today for all 3,219 images → `data/sdh/quality_metrics_enhanced.csv`** (numbers only,
keyed by opaque image ID; that script deliberately never opens the mapping file). Per image:
width, height, aspect, mean, std, p01, p99, dynamic range, histogram entropy,
mean-absolute-gradient sharpness, Laplacian variance, the same statistics restricted to the
**central 20–82% dental band**, black/white clipping fractions, bright-pixel fraction in the
band, and Canny edge density in the band. Observed distribution in §4.6.

Rules:
- **Thresholds are percentiles of the DEV distribution, not magic constants.** Absolute
  cut-offs copied from a paper do not transfer across vendors; that is the whole premise here.
- **Expected exclusion is small — target ≤5%.** A filter that removes 20% of a clinic's
  consecutive patients is not a quality filter, it is a selection bias, and it destroys the
  "consecutive clinic population" property that makes SDH worth having.
- **Validate against the retake pairs** (§1.2): the filter should rank first-of-pair worse than
  the retake more often than chance across the ~145 same-day groups. If it does not, the
  thresholds are measuring something other than diagnostic quality — say so rather than
  shipping it.
- Bright-band fraction is a **metal/restoration proxy**. It is a *stratifier*, never an
  exclusion criterion. Images are not dropped for having implants; >50% of this clinic's
  patients have restorations (`clinical_dataset_plan.md` §1).

### L3 — model-assisted assessability (this is C4, not cleaning)

Runs the detector and asks whether the *image* is assessable, reusing the per-tooth
`assessable` / `not_assessable_reasons` fields the pipeline already emits:
- implausible tooth count (< 8 or > 36) — the pilot's minimum was 5;
- detected-tooth hull covering an implausibly small share of the dental band (positioning or
  cropping error);
- FDI-consistency violations under `--no-one-to-one`;
- fraction of teeth already flagged not-assessable by the pipeline.

Rules: the same fixed rule applies to DEV and TEST; abstention is **reported as coverage**,
never silently applied; every metric is published at 100% coverage as well.

### L4 — stratification, which is not filtering

Never exclude an image for being clinically hard. Flag and stratify on metal/restoration burden
(L2 bright-band), edentulism proxy (tooth count), image-width tercile, study-year bucket, device
folder and retake status. Report metrics per stratum. "How does it do on heavily restored
teeth?" is the question reviewers ask and that no dataset in this project can currently answer.

### 4.5 The one preprocessing experiment worth running

The detector was trained on Tufts at 840×1615 and runs at `imgsz=1024`; SDH rotates
(`src/orientation.py`, 90° CCW) to 1,316×2,792, so teeth arrive at roughly **1.7× smaller pixel
scale** than in training — letterbox scale 0.37 against Tufts' 0.63. DENTEX sits at 0.35, so SDH
is close to DENTEX and it is *Tufts* that is the outlier, which is consistent with §1.3's
detection numbers being unremarkable.

Input scale is still the cheapest lever on detection recall, which bounds every downstream
number. **Ablate `imgsz` ∈ {1024, 1280, 1536} on SDH-DEV only** — about 20 CPU-minutes per pass
over a 300-image DEV sample. `imgsz` is frozen at 1024 across the project; if the ablation moves
anything, that is an SDH-specific inference setting, reported as such and **never retrofitted
onto the existing DENTEX/Ningxia numbers**.

### 4.6 What the quality metrics actually look like

Measured over all readable images today, n = 3,213 (`data/sdh/quality_metrics_enhanced.csv`).

| Metric | p1 | p5 | p25 | median | p75 | p95 | p99 | **p95/p5** |
|---|---|---|---|---|---|---|---|---|
| `sharp_grad` (mean abs gradient) | 0.617 | 0.658 | 0.763 | 0.870 | 1.000 | 1.247 | 1.436 | **1.90** |
| `lapvar` (Laplacian variance) | 4.78 | 5.38 | 6.93 | 8.34 | 10.02 | 13.33 | 16.18 | **2.48** |
| `band_sharp_grad` (dental band) | 0.539 | 0.595 | 0.705 | 0.812 | 0.938 | 1.175 | 1.354 | **1.98** |
| `band_std` (dental-band contrast) | 18.97 | 21.87 | 26.75 | 30.75 | 35.51 | 43.44 | 49.89 | **1.99** |
| `frac_black` | 0.005 | 0.005 | 0.005 | 0.005 | 0.006 | 0.015 | 0.034 | **2.96** |
| `std` (whole image) | 34.77 | 36.48 | 40.00 | 42.98 | 46.43 | 53.05 | 61.24 | 1.45 |
| `dynamic_range` (p99−p01) | 172 | 177 | 187 | 198 | 210 | 234 | 251 | 1.32 |
| `entropy` (bits) | 6.88 | 6.98 | 7.16 | 7.30 | 7.45 | 7.64 | 7.75 | 1.09 |
| `mean` | 121.6 | 123.6 | 126.2 | 127.9 | 129.8 | 132.9 | 136.0 | 1.07 |
| `band_mean` | 125.3 | 127.9 | 131.7 | 134.2 | 137.0 | 141.5 | 145.2 | 1.11 |
| `aspect` | 1.68 | 2.02 | 2.08 | 2.12 | 2.17 | 2.23 | 2.25 | 1.10 |
| `width` | 2215 | 2663 | 2737 | 2792 | 2852 | 2930 | 2965 | 1.10 |

**This table decides the filter's feature set, and it says something that changes the design.**

- **Brightness, contrast, dynamic range and entropy carry almost no signal** — p95/p5 spreads of
  1.07 to 1.45. That is not because the clinic's images are uniform; it is because the June
  enhancement (§4 L0) explicitly normalises exactly those quantities per image: percentile
  windowing, adaptive gamma and median-targeting gain. **Thresholding on brightness or dynamic
  range after L0 would be thresholding on the output of the normaliser, not on image quality.**
  Any filter design copied from a paper that windows on raw DICOM values would be measuring
  nothing here.
- **The variance that survives normalisation is sharpness and local contrast** — `lapvar`
  spreads 2.48×, `band_sharp_grad` and `band_std` about 2×. Sharpness is what percentile
  windowing cannot fix, and it is what motion, patient positioning and focal-trough error
  actually destroy. **Build L2 on `lapvar`, `band_sharp_grad` and `band_std`**, with
  `frac_black` (2.96×, i.e. collimation/edge blanking) as a fourth.
- **`band_edge_density` came out degenerate** — median 0.000, p99 0.002 — because the Canny
  thresholds (60/160) are far too high for a post-CLAHE panoramic. It is in the CSV, it carries
  no information as computed, and it is **excluded from the feature set** rather than quietly
  left in. Re-tune the thresholds or drop the column at task 3.
- Geometry (`aspect`, `width`) is tight, as expected from a single device — it is a
  stratification variable, not a filter.

---

## 5. Compute and GPU budget

**Measured, not estimated: 2.2 s/image on this machine's CPU** with models loaded once
(torch 2.8.0+cpu; there is no CUDA on this box).

| Job | Size | Where | Cost |
|---|---|---|---|
| Quality metrics, full set | 3,213 images | CPU | ~30 min — **already run today** |
| Tier A full-set inference, one config | 3,213 images | CPU | **~2.0 h**, unattended |
| Preprocessing ablation (2 configs) | DEV, 2 × 1,285 | CPU | ~1.6 h |
| Input-scale ablation (3 configs) | DEV sample, 3 × 300 | CPU | ~1 h |
| Repeatability, same-day pairs | ~290 images | CPU | ~11 min |
| **Tier A total** | | **CPU only** | **~5–6 h over two nights, ₹0** |

**Conclusion: Tier A needs no GPU at all.** This is the most important line in this section. The
instinct to rent a GPU for 3,000 images is wrong — inference at this scale is a laptop-overnight
job, and GPU rupees are the scarcest resource on this project.

GPU is needed only for **Tier C1** (detector fine-tuning), and there the budget is genuinely
tight:

| | |
|---|---|
| JarvisLabs balance | **₹313** (₹900 start, ₹249.19 on R1, ₹285.20 on the C1-VLM run, ₹14.26 wasted on a stray instance) |
| A100 80 GB | ₹140.94/hr → **2 h 13 min affordable** |
| C1 fine-tune estimate | 1,285 DEV images at 1024 px. R1's measured rate was 16.6 s/epoch for 700 images (detect head); ×1.84 for the image count and ×1.5 for a seg head ⇒ **~46 s/epoch**, so 60 epochs ≈ **46 min**. With boot, `pip install`, a ~1.5 GB upload and evaluation: **~1.3–1.6 h ≈ ₹185–225** |
| Headroom for a redo | **₹90–130 — under one hour. Not a redo.** |

So ₹313 buys **exactly one attempt**. `MASTER_PLAN_2026H2.md` §6 explicitly budgets "at least
one full redo", and R1 needed exactly that — its first run was scientifically void (misaligned
masks) and had to be repeated in full. **Recommendation: do not start Tier C1 on ₹313.** Either
top up to **₹1,500** (≈10.6 A100-hours: one run, two redos and slack) or defer C1 and ship
Tier A. The failure mode to avoid is deciding this by *not* deciding — starting the run and
discovering mid-way that there is no redo budget.

Hardware-parity note: R1 fixed batch 32 @ 1024 px on an A100 80 GB for pre-registration reasons
(`GPU_SETUP.md` §1). A C1 fine-tune starting from the R1 checkpoint should hold the same
configuration, for the same reason.

**Data-transfer note, and it is a governance decision, not a logistics one.** Tier C1 is the
only task in this plan that requires **clinic images to leave this machine** — ~1.5 GB of
SDH-DEV pixels onto a rented GPU instance. Tier A does not: it runs where the data already is,
which is `clinical_dataset_plan.md` §5's "compute goes to the data" rule and a further reason to
do Tier A first. If C1 proceeds: upload the enhanced 8-bit PNGs only, **never** `index.csv`
(§7.3), destroy the instance and its storage volume when the run ends rather than leaving it
paused, and record the transfer in `clinical_dataset_provenance.md` — that document exists
because a previous copy of this data left the machine without anyone writing it down.

---

## 6. Sequence and dates, against the 14 October implementation freeze

Tier A is roughly two working days of wall-clock, most of it unattended.

| # | Task | Depends on | Effort | Output |
|---|---|---|---|---|
| **0** | Fix the two stale "not on this machine" claims; separate `index.csv` from `images/` on Drive (§7.3) | — | 30 min | correct docs; valid de-identification |
| **0b** | **Integrity pass** — decode and SHA-256 every image; repair or exclude the six truncated files (§1.4); correct `checkpoint.json`'s count | 0 | 1 h | a set whose size is actually known |
| **1** | **Freeze the split** — `scripts/sdh/build_sdh_split.py` → `data/sdh/splits_v1.json`, DEV/TEST 40/60, stratified, seeded, pilot images asserted into DEV | 0b | 2 h | the thing everything else depends on |
| **2** | L0 preprocessing contract + unit test; fix the hardcoded output path | 1 | 2 h | `tests/test_sdh_preprocessing.py` |
| **3** | L1+L2 filter, thresholds fitted on **DEV**, validated against the 145 retake pairs | 1, 2 | 4 h | `data/sdh/filter_v1.json` + a validation number |
| **4** | Full-set Tier A inference, `--no-one-to-one`, per-image JSON | 1 | 2 h CPU, unattended | `outputs/sdh_tier_a/` |
| **5** | Repeatability on same-day pairs (κ, count agreement, FDI-map agreement) | 4 | 3 h | the result no other corpus can give |
| **6** | Preprocessing + input-scale ablations, **DEV only** | 3, 4 | 3 h CPU | two ablation tables |
| **7** | L3 assessability → coverage–accuracy curves, i.e. C4 on a new device | 4, 6 | 4 h | the filtering *result* |
| **8** | Failure taxonomy with example crops, stratified by L4 | 4, 7 | 4 h | figures |
| **9** | **Locked TEST pass** — every parameter fixed in writing first | 3–8 | 2 h CPU | the reported numbers |
| **10** | Write into `PAPER_MATERIAL.md` §7/§8 and the manuscript | 9 | 4 h | paper text |
| — | *Tier B, if the dentist commits* | 1, 9 | weeks | real external metrics |
| — | *Tier C1, if the budget is topped up* | 1, 3, 9 | 1 GPU day | detection-recall gain |

**Hard constraint on ordering:** task 9 happens **once**. If a parameter changes after it runs,
it is not re-run quietly — the change is logged in `RESULTS_LOG.md` with the reason.

**Where this sits against the real critical path — it does not displace it.** As of 28 August
the critical path is the **venue-length cut** (12 pages → 4 for ISBI) plus the compliance
blockers. SDH Tier A is ~2 days of mostly-unattended work that adds a fifth source and a
repeatability result. If the length cut slips, **Tier A is what gets deferred, not the cut.**

---

## 7. Governance — what the letter must say, and the one thing to fix today

Consent is the user's decision and this plan proceeds on it. Three factual points remain, each
stated once.

**7.1 The written agreement (expected 1 Sep) should explicitly cover four things.** A letter
saying only "permission granted" will not satisfy a reviewer or an ethics committee:

1. **Retrospective use of already-acquired, anonymised radiographs** — no new imaging was
   performed for this research and no patient was contacted.
2. **Research use *and publication*** of derived results, aggregate statistics and
   de-identified example images.
3. **That no patient identifiers leave the clinic's control** — naming the de-identification
   mechanism (opaque IDs; mapping table retained separately).
4. **Date, clinic name, signatory name and role.** Undated or unsigned is not usable.

**7.2 Clinic consent is not institutional ethics approval — they are different objects.** Most
venues require an ethics statement and ISBI is one. What can be written honestly once the letter
exists: *retrospective analysis of de-identified radiographs under written permission from the
originating clinic; institutional review [status]*. Starting the institutional process costs
nothing and runs in parallel; it is `PAPER_MATERIAL.md` §8.19 item 4 and it is still unstarted.

**7.3 One concrete fix, about five minutes, and it should happen before the letter arrives.**
`metadata/index.csv` — the re-identification mapping — sits **in the same shared Google Drive
folder as `images/`**, and has since 4 June 2026 (`clinical_dataset_provenance.md` §4a). Anyone
with access to that folder holds both the anonymised images and the table that undoes the
anonymisation, so **that copy is not de-identified in any meaningful sense**. Move `index.csv`
out of the shared tree, or delete the Drive copy and keep the mapping only on `D:`. Worth doing
before signing a letter that asserts de-identification. It is on the user's own Drive and is the
user's action to take.

**7.4 For tomorrow's review, describe the status precisely.** "Written data-use agreement signed
and on file" becomes true only after 1 September. Until then: **"permission obtained from the
clinic; written agreement expected 1 September; no clinic data has contributed to any reported
number."** The last clause is currently true and is worth keeping true.

---

## 8. Pre-registered criteria, stated before the numbers exist

Written now so they cannot be adjusted to fit the outcome.

| Question | Criterion, fixed in advance |
|---|---|
| Does the L2 quality filter measure diagnostic quality? | It ranks first-of-pair worse than the retake in **>60%** of the ~145 same-day groups (chance = 50%). Below that, report it as unvalidated and do not use it to exclude anything |
| Does the filter distort the cohort? | Exclusion **≤5%** of images. Above that it is selection bias and must be reported as such |
| Is the input-scale ablation a real effect? | A change in mean teeth/image **>2 SD of the per-image bootstrap** on DEV. Otherwise `imgsz` stays at 1024 |
| Is pipeline output repeatable? | Report κ and count agreement whatever they are. **No threshold** — a poor repeatability number is a finding, not a failure |
| Is Tier C1 worth keeping? | Detection recall improves on the **DENTEX/Tufts held-out sets** (in-domain, labelled) **without regression**, before any SDH claim is made. A detector that improves only on its own pseudo-labels has learned nothing |
| Bone loss on SDH | **Not an open question.** 2.0% firing confirms `PAPER_MATERIAL.md` §8.13. Report it and move on |

**Risks, and what is done about them:**

| Risk | Response |
|---|---|
| Written agreement is late or narrower than expected | Tier A produces no patient-level output and no image release. Nothing is published before the letter exists |
| Filter thresholds picked to make a number look good | The DEV/TEST split (§3) exists precisely to make that impossible; TEST is touched once |
| Pseudo-label self-confirmation in Tier C1 | Acceptance criterion is on **labelled in-domain** sets, not on SDH |
| SDH work displaces the ISBI length cut | Tier A is ~2 days, mostly unattended, and is explicitly the thing that gets deferred (§6) |
| Same-day pairs are not retakes | Weak label, validated directionally, ~30 pairs spot-checked before any claim |
| Dentist never becomes available | Tier A is designed to stand alone and needs zero labels |

---

## 9. Open questions

1. **Does a dentist commit hours, and how many?** Gates all of Tier B. Needs a number, not a
   maybe.
2. **Is the GPU budget topped up?** Gates Tier C1. ₹313 buys one run and no redo (§5).
3. **Were the 4 MONOCHROME1 images inverted correctly** during Stage-1 conversion?
   `dental_dataset_audit.py` has still never been read (`clinical_dataset_provenance.md` §7).
   Four images — but they will look exactly like model failures if wrong.
4. **Which venue?** The length cut differs, and it decides whether SDH is a paragraph, a
   subsection, or supplementary material.
5. **Do the 144 same-day-retake images stay in the kept set** (§1.2), get swapped for the later
   scan, or get excluded? Decide during task 1, before the split is frozen.
