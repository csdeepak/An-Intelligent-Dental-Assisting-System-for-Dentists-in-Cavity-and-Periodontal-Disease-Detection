# RESULTS LOG

**Append-only chronological journal of this project.**

**Convention — read before writing:**

- **Newest entries go at the BOTTOM.** The file reads top-to-bottom as the project's
  history. Never reorder, never rewrite an old entry; if an earlier number turns out to be
  wrong, add a *new* entry that says so and links back.
- **One entry per milestone**, not per commit. A milestone = a training run, a new
  evaluation, a significant bug fix, or an architectural/methodological decision.
- Entries below dated before 2026-08-12 were **reconstructed** on 2026-08-12 from git
  history, the saved notebook output cells, and the `models/*/…summary.txt` files. They are
  accurate to those sources but were not written live.
- Anything that changes a current-best number must also be mirrored into
  `model_metrics.md`, and anything paper-relevant into `PAPER_MATERIAL.md`.

---

## Template for new entries

Copy this block verbatim to the bottom of the file and fill it in.

```markdown
## YYYY-MM-DD — <short title of the milestone>

- **What was done:** one or two sentences, concrete.
- **Dataset / config:** which dataset, which split, the hyperparameters that matter.
- **Metrics:** the numbers, with the split they were measured on. Say "val" or "test"
  explicitly. Include support counts for small classes.
- **Key decision or insight:** what this result changed about the plan. If nothing
  changed, say so.
- **Source:** relative path to the notebook / script / summary file that produced it.
- **Follow-ups:** open questions or next actions this created.
```

---

## 2026-01-31 — Literature review and survey paper

- **What was done:** Reviewed the dental-radiograph AI literature and drafted a survey
  paper covering tooth detection, caries classification and periodontal bone-loss
  assessment on panoramic radiographs. Established the target benchmarks the project would
  be measured against.
- **Dataset / config:** n/a — literature only.
- **Metrics:** Extracted target: published Tufts tooth-detection work reports
  **mAP@0.5 ≥ 0.90**; this became the acceptance bar written into `train_yolo.py` /
  `evaluate_yolo.py`.
- **Key decision or insight:** No public dataset annotates teeth + caries + bone loss
  together. This forced the modular multi-dataset pipeline design (Tufts for detection and
  bone loss, DENTEX for caries) instead of a single end-to-end detector.
- **Source:** `docs/reports/literature/Survey_paper.pdf`,
  `docs/reports/literature/Dental X-Ray Capstone Literature Review.xlsx`; commit `af3b8f6`.
- **Follow-ups:** Turn the review sheet into a proper Related Work comparison table.

## 2026-04-05 — Repo scaffold, config system, and Tufts data exploration

- **What was done:** Set up the project structure (`src/`, `scripts/`, `configs/`,
  `tests/`, `docs/`), centralised every path and hyperparameter in
  `configs/dataset_config.yaml`, and completed the Tufts exploration pass.
- **Dataset / config:** Tufts Dental Dataset — 1,000 radiographs, 26,005 tooth boxes across
  968 images, 439 expert masks (285 empty / 154 annotated), 423 images with full
  annotation overlap.
- **Metrics:** Dataset characterisation — uniform 840×1615 px; mean 26.9 teeth/image; mean
  tooth aspect ratio ~0.35; Michelson contrast 0.999; 102 degenerate boxes; deciduous
  teeth present.
- **Key decision or insight:** Three critical bugs were caught here and each would have
  silently destroyed the project: (1) the JSON join key is the nested `External ID` field,
  not the filename stem — before the fix, zero annotations matched; (2) bbox format is
  `[y1, x1, y2, x2]` corner points, not `[x, y, w, h]` — before the fix, every crop came
  from the wrong location; (3) expert masks encode **per-lesion instance IDs**, not
  severity classes — this killed the planned U-Net severity segmentation and forced the
  pivot to ResNet18 classification. The ~0.35 aspect ratio is what motivated asymmetric
  crop expansion.
- **Source:** `notebooks/bone_loss/01_tufts_data_exploration_v2.ipynb`,
  `docs/exploration/README.md`, `docs/reports/data_exploration_v2.pdf`; commits `9d8c95b`,
  `e8643f2`.
- **Follow-ups:** Build the crop dataset using the corrected coordinate handling.

## 2026-04-06 — Bone-loss crop dataset construction

- **What was done:** Built the per-tooth crop dataset for bone loss: expanded each
  ground-truth tooth box asymmetrically, assigned labels by pixel-overlap against the
  expert pathology mask, applied bbox jitter, and split at image level.
- **Dataset / config:** Tufts; expansion 1.5× W / 2.0× H; output 224×224; overlap threshold
  0.01; jitter ±15%; `min_bbox_dim` 3; val ratio 0.20; seed 42.
- **Metrics:** **22,806** crops built. Native imbalance **23.84×** (~96% normal / ~4%
  diseased). After resampling: train 2,500 normal + 711 diseased = 3,211 (ratio 3.52×);
  val left untouched at 1,499 normal + 59 diseased = 1,558.
- **Key decision or insight:** Rejected IoU for label assignment. Expert lesion masks cover
  only 0.5–2% of an expanded crop, so IoU ≈ 0 even for true positives. Replaced with
  `overlap = mask_pixels_in_crop / crop_area`, threshold 0.01 chosen from the overlap
  distribution plot. Also locked in image-level splitting so jittered copies of the same
  tooth can never straddle train/val.
- **Source:** `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`; commit `cf9ea24`.
- **Follow-ups:** Train the binary classifier; sanity-check crops visually before trusting labels.

## 2026-04-06 — Bone-loss binary classifier trained (headline result)

- **What was done:** Fine-tuned ResNet18 on the resampled crop dataset for binary bone-loss
  presence, using Focal Loss to counter residual imbalance.
- **Dataset / config:** 3,211 train / 1,558 val crops (val at real-world distribution).
  ResNet18 (ImageNet), FC 512→2, FocalLoss(γ=2.0, α=[0.642, 2.258]), Adam lr 1e-4 wd 1e-4,
  batch 32, ReduceLROnPlateau(patience 5), early stopping on val macro-F1 (patience 10).
  Ran 32/50 epochs, best epoch 22, 14.8 min.
- **Metrics (validation, untouched real distribution):** macro F1 **0.9233** (target ≥0.72);
  F1 normal **0.9943** (target ≥0.75); F1 diseased **0.8522** (target ≥0.70);
  sensitivity **83.05%**; specificity **99.53%**; accuracy 98.91%.
  Confusion matrix TN 1,492 / FP 7 / FN 10 / TP 49.
- **Key decision or insight:** All three targets cleared on a validation set that was
  deliberately left at the real 4% prevalence, so the numbers mean something clinically.
  Accuracy (98.91%) is meaningless here — a predict-everything-normal model scores 96% —
  which is why macro F1 and diseased-class recall are the reported criteria.
- **Source:** `notebooks/bone_loss/03_bone_loss_model_training.ipynb`,
  `models/03_bone_loss_model_training_notebook_models/training_summary.txt`; commits
  `f84ca62`, `60da004`.
- **Follow-ups:** Extend to severity grading; eventually wire into the full pipeline.

## 2026-04-06 — Bone-loss severity classifier (3-class) — at target, low confidence

- **What was done:** Trained a 3-class ResNet18 on positive crops only, with severity
  defined by the same expert-mask overlap ratio used for the binary labels.
- **Dataset / config:** 976 train / 52 val crops. Thresholds: mild ≤0.05, moderate
  0.05–0.15, severe >0.15. ResNet18, FC 512→3, FocalLoss(γ=2.0, α=[1.694, 0.72, 0.98]).
  Best epoch **2**, 1.6 min training.
- **Metrics (validation, 52 crops):** macro F1 **0.7208** (target 0.72); accuracy 69.23%.
  Per class — mild F1 0.80 (P 1.00 / R 0.67, **support 6**), moderate F1 0.6667
  (P 0.80 / R 0.57, support 28), severe F1 0.6957 (P 0.57 / R 0.89, support 18).
- **Key decision or insight:** Technically at target, but the margin is 0.0008 on 52
  samples and the mild class has 6 validation samples. Treat this as "works in principle,
  not yet trustworthy". Convergence at epoch 2 confirms the model saturates almost
  immediately on 976 crops.
- **Source:** `notebooks/bone_loss/04_bone_loss_severity.ipynb`,
  `models/04_bone_loss_severity_notebook_models/severity_summary.txt`; commits `e590269`,
  `ffc295a`.
- **Follow-ups:** More annotated positives, or k-fold CV, before this number can carry
  weight in the paper.

## 2026-04-06 — CEJ-based bone level estimation v2 (exploratory, negative result)

- **What was done:** Classical-CV attempt at the clinical gold standard — measure the
  CEJ-to-bone-crest distance as a fraction of root length. v2 added CLAHE preprocessing,
  column-wise CEJ and apex detection with median aggregation, a focused crest search window
  (CEJ → CEJ+40% root), IQR outlier removal, tooth-region isolation, and confidence scoring.
- **Dataset / config:** 296 positive bone-loss crops. Clinical mapping mild <33%,
  moderate 33–50%, severe >50%.
- **Metrics:** processing success **100.0%** (296/296, 0 failures); **62.5%** (185 crops)
  flagged reliable; bone loss % on reliable crops min 1 / median 2 / mean 5 / max 30.
  **Exact agreement with overlap-based severity: 15.1%**; within ±1 class: 61.6%.
- **Key decision or insight:** The 100% figure is a *completion* rate, not an accuracy. The
  15.1% agreement is the real result and it is at chance level for 3 classes. Conclusion:
  heuristic CEJ landmark detection does not transfer from periapical radiographs to OPGs
  (panoramic distortion, overlapping anatomy, crowns/restorations). The module stays
  exploratory and out of the pipeline; the overlap-based proxy remains primary.
- **Source:** `notebooks/bone_loss/05_cej_estimation_v2.ipynb`,
  `models/05_cej_estimation_v2_models/cej_v2_summary.txt`; commit `ffc295a`.
- **Follow-ups:** Revisit only with periapical images or a learned landmark detector.

## 2026-04-21 — Caries cascade (DENTEX, ResNet18) — Phase 1 gate + Phase 2 severity

- **What was done:** Built the two-stage caries cascade. Phase 1 gates caries vs no_caries;
  Phase 2 (warm-started from Phase 1 with a reset FC, head-only training then full
  fine-tune at low LR) splits caries vs deep_caries.
- **Dataset / config:** DENTEX pre-processed crops via `ImageFolder`. Phase 1 train 2,767
  caries / 762 no_caries, class weights [0.6377, 2.3156]. Phase 2 val 133 crops
  (101 caries / 32 deep_caries). ResNet18 ImageNet, 224×224, Adam, LR 1e-3 (head) → 3e-5
  (fine-tune), class weights swept [0.5, 3.5] → [0.6, 3.0].
- **Metrics (Phase 2 validation, 133 crops, three successive attempts):**
  attempt 1 — acc 0.80, macro F1 0.73, deep_caries F1 0.58;
  attempt 2 — acc 0.77, macro F1 0.72, deep_caries F1 0.62;
  **attempt 3 (best) — acc 0.81, macro F1 0.77, weighted F1 0.82**, caries P/R/F1
  0.94/0.80/0.87, deep_caries P/R/F1 0.57/**0.84**/0.68, confusion `[[81,20],[5,27]]`.
  **Phase 1 gate metrics were not saved.**
- **Key decision or insight:** The class-weight sweep is a deliberate precision→recall trade
  on deep caries (recall 0.59 → 0.84 while precision stays ~0.57): the model over-calls
  deep caries, which is the right direction of error for screening but must be stated.
  The freeze-head-then-unfreeze protocol is the methodologically strongest part of this
  notebook; the evaluation discipline around it is the weakest.
- **Source:** `notebooks/caries/phase-1.ipynb`, `notebooks/caries/approach.txt`; commit `535f2af`.
- **Follow-ups:** Documented gaps — augmentation defined but never actually applied, no LR
  scheduler, no held-out test set, no early stopping, model selection by accuracy on an
  imbalanced problem, missing Phase 1 report. All must be closed before publication.

## 2026-04-22 — YOLOv11l tooth detection, H200 run (imgsz 768, 50 epochs)

- **What was done:** First full fine-tune of YOLOv11l for single-class tooth detection on
  the converted Tufts dataset.
- **Dataset / config:** Tufts → YOLO format via `convert_tufts_to_yolo.py`; frozen
  image-level 70/15/15 split (700/150/150). `yolo11l.pt`, imgsz 768, 50 epochs, AdamW,
  NVIDIA H200 (143 GB), 0.093 h training.
- **Metrics (validation, 150 images / 3,794 instances):** P 0.609, R 0.678,
  **mAP@0.5 0.678**, mAP@0.5:0.95 0.282. Not evaluated on test.
- **Key decision or insight:** Well below the ≥0.90 literature benchmark. Hypothesis formed
  here: the 768 px input is under-resolving teeth on an 840×1615 OPG.
- **Source:** `notebooks/yolo_detection/h200_768px_50ep.ipynb`.
- **Follow-ups:** Re-run at imgsz 1024 with a longer schedule.

## 2026-04-23 — YOLOv11l tooth detection, A100 run (imgsz 1024, 150 epochs) — current best

- **What was done:** Re-ran detection at full resolution with a long schedule and early
  stopping, then evaluated on the held-out test split.
- **Dataset / config:** same frozen 70/15/15 split. `yolo11l.pt` (25.28 M params),
  imgsz **1024**, batch 32, AdamW, lr 1e-3→1e-5 cosine, 150 epochs requested / **128 run**
  (early stop, patience 30), best epoch **98** by Ultralytics fitness, AMP, seed 42.
  Clinically-valid augmentation only (fliplr 0.5, ±10° rotation, translate 0.1, scale 0.2,
  hsv_v 0.2, erasing 0.4; no mosaic, no mixup, no vertical flip). NVIDIA A100 80GB PCIe,
  0.592 h training.
- **Metrics:** **validation** (150 img / 3,794 inst) P 0.788, R 0.772, **mAP@0.5 0.834**,
  mAP@0.5:0.95 0.367. **Test** (150 img / 3,924 inst) P 0.7643, R 0.7421,
  **mAP@0.5 0.7824**, mAP@0.5:0.95 0.3351. Inference ~3.1 ms/image.
- **Key decision or insight:** Resolution dominates — 1024 vs 768 is worth ~15 mAP@0.5
  points on this dense, thin-object scene; epoch count is secondary. The ~5-point val→test
  drop is modest and indicates an honest split. Still below the ≥0.90 published benchmark.
- **Source:** `notebooks/yolo_detection/a100_1024px_150ep.ipynb`,
  `models/06_yolo_detection_a100_run/run_summary.txt`,
  `docs/results/figures/yolo_detection_a100/`.
- **Follow-ups:** **No canonical detector has been frozen** — this run and the H200 run
  still coexist. Pick this one, record its weight hash, retire the other in writing.

## 2026-08-12 — Repository restructure, docs system, no new model results

- **What was done:** Full repo audit and restructure. Relocated ~2.6 GB of untracked junk
  (a stale nested clone, a 2.2 GB raw-data workspace containing a checked-in virtualenv, a
  YOLO run workspace, duplicate diagrams) to `_repo_archive/` outside the repo; extracted
  the reusable artifacts from those folders into the tracked tree first; built this
  `docs/` system; corrected the root `README.md`, which had been claiming tooth detection
  was "in progress" and bone loss "planned" when both were finished months earlier.
- **Dataset / config:** n/a — no training was run.
- **Metrics:** none new. All metrics in `model_metrics.md` and `PAPER_MATERIAL.md` were
  transcribed from existing notebook outputs and summary files and cross-checked against
  the raw `results.csv` / notebook output cells.
- **Key decision or insight:** The project's blocking problem is **not** model quality — the
  bone-loss binary model is genuinely strong. It is that four working stages have never
  been joined into one runnable pipeline (Stages 5–6 do not exist), and that the
  documentation was describing a project three months out of date. Also found: the
  Universal→FDI table in `configs/dataset_config.yaml` mis-maps the entire lower arch from
  Universal 23 onward.
- **Source:** `docs/session-memory/2026-08-12-repo-understanding-and-restructure.md`,
  `_repo_archive/ARCHIVE_MANIFEST.md`.
- **Follow-ups:** Fix the lower-arch FDI mapping; freeze the canonical detector; build
  Stages 5–6; close the caries evaluation gaps listed in `PAPER_MATERIAL.md` §9.

## 2026-08-15 — FDI mapping bug fixed; caries augmentation discrepancy resolved (T0.1)

- **What was done:** Closed the two blocking Tier-0 correctness items. (1) Corrected the
  Universal→FDI lower-arch mapping in **both** `configs/dataset_config.yaml` and
  `src/utils/fdi_converter.py` — the module carried the same error as the YAML, which prior
  documentation had not noticed — and rewrote `tests/test_fdi_converter.py` against the FDI
  standard rather than against the implementation. (2) Audited the caries training code and
  confirmed at code level that the augmentation pipeline was defined and never applied.
- **Dataset / config:** n/a — no training was run. Audit and static correction only.
- **Metrics:** none new. **No existing metric changes.** Verified that no notebook or script
  ever executed the FDI mapping (the only references in the bone-loss notebooks are in
  markdown/comments), so no training label, crop assignment, or reported number was produced
  through the wrong table. The bug was latent and would have first caused damage at Stage 5.
- **Key decision or insight:** Three findings. (a) The old unit test *asserted the buggy
  value* (`universal_to_fdi("32") == 34`), having been written from the implementation rather
  than the dental standard — it reported green while locking the defect in place. The
  replacement adds two property checks (quadrant correctness, bijectivity) that would have
  caught it. (b) The unapplied augmentation is **isolated to the caries track**; both
  bone-loss notebooks genuinely apply it, so the project's strongest result (macro-F1 0.9233)
  is unaffected. (c) A repo-wide grep for false augmentation claims **found none** —
  `PAPER_MATERIAL.md` §8.1, `04_methodology.tex` and `approach.txt` had all already disclosed
  it accurately, which materially lowers the credibility risk `gap_analysis.md` §2C assigned
  to this item. Decision recorded: enable augmentation and re-run as a **two-arm** experiment
  during the W2 re-run block, turning the defect into an ablation data point.
- **Source:** `docs/results/METHODOLOGY_CHANGELOG.md` (full detail),
  `docs/session-memory/2026-08-15-strategic-replan-foundation-models.md`,
  `tests/test_fdi_converter.py` (8 tests, all passing).
- **Follow-ups:** Caries numbers (val acc 0.81, macro-F1 0.77) remain no-augmentation,
  validation-only, accuracy-checkpointed and must carry those qualifiers until the W2 re-run
  supersedes them. Next: W2 re-run block (T0.2/T0.3) and canonical detector (T0.6).

## 2026-08-16 — Corrected a wrong premise in MASTER_PLAN_2026H2.md: DentFound's weights are not public

- **What was done:** While fixing the survey paper's citation list, found that the survey's own
  text correctly states DentFound's fine-tuned weights are not public — contradicting what this
  project's `MASTER_PLAN_2026H2.md` had assumed ("public Apache-2.0 weights... free baseline for
  C1"). Re-verified directly against `github.com/ahukui/DentFound` rather than trusting the
  earlier, less careful pass: the repo's `checkpoints/` folder documents downloading the generic
  pretrained CLIP-ViT-L/14 and Vicuna-7B base models only; no link to DentFound's own trained
  checkpoint exists anywhere in the repository. Corrected every affected passage in
  `MASTER_PLAN_2026H2.md` (§0, §2.2, §2.3 C1, R6, §3.1 diagram, §5 W5, §5.1, §6 compute budget,
  §7 venue note, §8 risk register, §9 source table) rather than patching only the one place it
  was first noticed.
- **Dataset / config:** n/a — planning-document correction, no training run.
- **Metrics:** none. No experiment has been run yet under either the old or corrected plan.
- **Key decision or insight:** Contribution C1 (specialist-vs-foundation-model comparison) is
  **not achievable by running DentFound itself** — its training code is Apache-2.0 but its
  weights and its 101k-patient training data are both closed, so neither running their
  checkpoint nor reproducing it from scratch is possible with what's public. Decision: C1 now
  runs against an accessible open-weight VLM (selected in W5, not locked in now) as the primary
  comparison, with GPT-4o via API as a secondary point with direct literature precedent (the
  *Diagnostics* Sep 2025 study). A non-blocking email to DentFound's authors requesting research
  weight access was added as pure-upside, off the critical path. The underlying scientific
  question (small specialist vs. general-purpose VLM on subtle radiolucent pathology) is
  unchanged; only which model sits on the other side of the comparison changed. Net effect on
  risk is a **decrease** — the plan no longer depends on a third party's unreleased checkpoint
  at all, where the original version did.
- **Source:** `docs/research/MASTER_PLAN_2026H2.md` (corrected version, header dated 16 Aug 2026),
  direct inspection of `github.com/ahukui/DentFound`.
- **Follow-ups:** Select the specific open-weight VLM in W5 based on what's current and reliably
  deployable at that time. Send the (optional, non-blocking) email to DentFound's authors. No
  other plan document referenced the wrong premise — `PUBLICATION_STRATEGY.md`,
  `gap_analysis.md`, and the survey paper itself were all already correct or already fixed.

## 2026-08-18 — Ningxia dataset downloaded; two structural findings change the evaluation design

- **What was done:** The Ningxia multi-center dataset finished downloading to `D:\nangxia_dataset`
  (Baidu Cloud, manual CAPTCHA, ~3-day throttled transfer — the risk flagged in
  `MASTER_PLAN_2026H2.md` §4.4 materialised exactly as predicted and was cleared). Inspected the
  actual folder structure rather than reasoning from the paper's description, and verified
  extracted counts against the dataset's own README table. Six of seven `.rar` archives are
  extracted and count-verified; `segmentation/Periodontitis/train.rar` (4.26 GB, 2,000 images)
  was still extracting at time of writing.
- **Dataset / config:** Ningxia (Li et al., *J Imaging Inform Med* 2024) — 6,580 panoramic
  images, 3 hospitals. Segmentation subset: `{Dental caries, Impacted teeth, Periodontitis}` ×
  `{train, test1–test4}`, each with paired `img/` + `mask/`. Classification subset: 3 disease
  class folders, randomly split across centers.
- **Metrics:** none — no model was run. Count verification only. Image+mask pairing yields ~2× the
  README's per-image count, as expected (e.g. Dental caries/test: 674 PNGs = 337 images × 2).
- **Key decision or insight:** **Two structural findings, one opportunity and one correction.**
  (1) *The test splits are center-stratified.* The README states `test2` shares a center with
  their training data while `test1`/`test3`/`test4` come from different centers — so Ningxia is a
  built-in **domain-shift gradient**, not a single external set. Every headline metric will now be
  reported stratified by split, never pooled, which strengthens contribution C2 at zero cost.
  (2) *There are no healthy controls.* Every image in both subsets is a positive case of its
  category; there is no normal/healthy class. **Specificity, AUC and PPV are therefore not
  computable on Ningxia**, contradicting the original §4.3 which claimed "sensitivity/specificity/
  AUC at the image level." Metrics redistributed: specificity/PPV/NPV/calibration now come from the
  **Tufts held-out test** (which has genuine negatives at real prevalence, 1,499 normal / 59
  diseased); Ningxia supplies sensitivity-under-domain-shift plus lesion-localisation agreement.
  Localisation agreement is **promoted to the primary Ningxia metric** because it requires no
  negatives and simultaneously satisfies the quantified-XAI requirement (T1.5). Explicitly ruled
  out: synthesising negatives from other disease categories — the dataset annotates the diagnosis
  of interest, co-occurrence is clinically common, and that substitution would convert correct
  predictions into false positives.
- **Source:** direct inspection of `D:\nangxia_dataset` and its bundled `ReadMe.md`;
  `docs/research/MASTER_PLAN_2026H2.md` §4.3 (rewritten), §4.4, §5 (W4/W6), §8.
- **Follow-ups:** Confirm `Periodontitis/train` extracts to 2,000 images + 2,000 masks. Build and
  freeze a committed manifest CSV (category / split / center / img path / mask path / dimensions)
  verified against the README table — pixels stay on `D:`, only the manifest enters git. Verify the
  exact center↔split mapping against the published paper before naming centers in print (the
  README's qualitative statement does not obviously reconcile with the paper's 4,940 / 716 / 880
  per-hospital counts). Characterise the resolution gap vs. Tufts (840×1615 portrait vs. ~2976×1536
  landscape) as input to the preprocessing contract. **Do not delete the `.rar` archives** — a scan
  found no junk files to clean, and they are the only local fallback until every split has been
  read end to end.

## 2026-08-19 — T0.6: detector reconciliation declared, seg retrain blocked on missing masks

- **What was done:** Formally reconciled the two unreconciled YOLO detection runs (2026-04-22
  H200, 2026-04-23 A100) per T0.6: the A100 config is declared canonical going forward, on the
  existing evidence (A100 wins by ~16 mAP@0.5 points on validation alone, before the H200 run's
  total lack of test-set evaluation is even considered). Corrected `scripts/yolo/train_yolo.py`,
  which had drifted from the real A100 run (`batch=16` vs. the actual `batch=32`, run name
  `tufts_v1` vs. the real `tufts_clean_v1`, no explicit seed/deterministic flags). Pre-registered
  the acceptance criterion for the future YOLOv11l-seg retrain (R1) **before** running it: test box
  mAP@0.5 ≥ 0.75 and test mask mAP@0.5 ≥ 0.65, same test-set discipline as Ningxia. While
  investigating, found that Tufts `teeth_mask/` (raster masks) is only 308/1000 complete at the
  source — not the "no new annotation required" asset the master plan claimed — but
  `teeth_polygon.json` (1,000/1,000 records, same schema as `teeth_bbox.json`) is complete and is
  the correct segmentation source. Wrote `scripts/yolo/convert_tufts_to_yolo_seg.py` (polygon →
  YOLO-seg label converter) and `scripts/yolo/train_yolo_seg.py` (training script matching the
  canonical config) so the retrain can start immediately once the polygon file is available.
- **Dataset / config:** n/a — no training was run. Reconciliation and script-writing only.
- **Metrics:** none new.
- **Key decision or insight:** the reconciliation and pre-registration are complete and in
  writing, but **the actual retrain is blocked**: `teeth_polygon.json` is not present on this
  machine, and the bbox detector's own weights (`best.pt`) could not be located either (searched
  this machine and the `_repo_archive/`; not found), so "freeze and version" (the W2 exit
  criterion) is only half done — the config is frozen, the weight hash is not. The
  largest-polygon-per-object heuristic in the new converter (picking the biggest of several
  point-list fragments per tooth, since most objects carry one real contour plus small
  edge-tracing-noise fragments) is unverified beyond a single inspected record and needs a visual
  spot-check once real data is available.
- **Source:** `docs/research/T0.6_detector_reconciliation.md` (full detail),
  `notebooks/bone_loss/01_tufts_data_exploration_v2.ipynb` (polygon JSON schema, cell 6/7 output),
  `scripts/yolo/{train_yolo.py,train_yolo_seg.py,convert_tufts_to_yolo_seg.py}`.
- **Follow-ups:** re-fetch `teeth_polygon.json` from the original Tufts source; locate or
  re-obtain `best.pt` for the A100 run and compute its weight hash; run the seg retrain and
  evaluate against the pre-registered criterion, not a post-hoc one.

## 2026-08-19 — R2: mask-aware cropping implemented (code only, untested against real masks)

- **What was done:** Implemented mask-aware cropping in `src/crop_generator.py`
  (`rasterize_polygon`, `extend_mask_below_root`, `apply_soft_mask_attenuation`,
  `extract_mask_aware_crop`), with 8 new unit tests in `tests/test_crop_generator.py`. Soft
  attenuation (default: dim non-target pixels to 50%, never zero) rather than hard masking, and
  the mask is explicitly extended downward within the tooth's own column span before attenuation
  is applied, so the sub-root alveolar bone region the periodontal branch reads is preserved
  rather than suppressed as "background."
- **Dataset / config:** n/a — tested against synthetic arrays only (no real Tufts masks exist
  locally yet, see the T0.6 entry above). `opencv-python-headless` installed locally to run the
  test suite; it was already a declared `requirements.txt` dependency, just not installed in this
  environment.
- **Metrics:** all 12 tests in `tests/test_crop_generator.py` pass (4 pre-existing + 8 new); full
  repo test suite (`test_crop_generator.py`, `test_data_loader.py`, `test_fdi_converter.py`,
  `test_label_assigner.py`) passes with no regressions.
- **Key decision or insight:** the function has a documented fallback (fewer than 3 polygon
  points → identical output to the plain `extract_crop`), so it's safe to call on detections that
  don't have a usable mask yet — no need to branch on mask availability at every call site once
  it's wired into the bone-loss crop pipeline.
- **Source:** `src/crop_generator.py`, `tests/test_crop_generator.py`,
  `docs/results/PAPER_MATERIAL.md` §6.6.
- **Follow-ups:** wire into the actual bone-loss dataset-construction notebook once T0.6's
  segmentation masks exist; this becomes ablation C5's fourth cell (rectangular vs. mask-aware).

## 2026-08-19 — T0.3: caries checkpointing switched from accuracy to macro-F1 (code fix, not re-run)

- **What was done:** Fixed a bug flagged in `PUBLICATION_TODO.md` T0.3 and
  `PAPER_MATERIAL.md` §8.1: `notebooks/caries/phase-1.ipynb` selected its "best" checkpoint by
  raw validation accuracy at all five training stages (Phase 1 gate; Phase 2 stages 1, fine-tune,
  fixed, and fixed2), which rewards the majority class on this imbalanced problem. All three
  `validate()` definitions in the notebook now also compute and return macro-F1
  (`sklearn.metrics.f1_score(..., average='macro', zero_division=0)`), and all five
  checkpoint-selection loops now compare on `val_f1_macro` instead of `val_acc`. This already
  matches the convention the two bone-loss notebooks used correctly, and that
  `configs/dataset_config.yaml` already declared (`training.early_stop_metric: "val_f1_macro"`)
  but the caries notebook never read that config at all.
- **Dataset / config:** n/a — notebook code edited, not re-run (no GPU in this environment).
- **Metrics:** none new — the numbers in `PAPER_MATERIAL.md` §7.2 still describe the
  old, accuracy-selected checkpoints until the notebook is actually re-run.
- **Key decision or insight:** one cell (Phase 2 "fixed2" stage) hardcoded a resume threshold —
  `best_val_acc = 0.8195  # VERY IMPORTANT` — copied by hand from a previous session's printed
  accuracy for the checkpoint being resumed from. Since the metric changed, that number is no
  longer meaningful; rather than guessing an equivalent, the correct macro-F1 for that exact
  checkpoint (`best_phase2_fixed.pth`) was recovered from the notebook's own already-saved
  `classification_report` output (cell 114, "macro avg" f1-score = 0.72) and used instead. This
  is grounded in a real number already in the notebook, not fabricated.
- **Source:** `notebooks/caries/phase-1.ipynb` (cells 47, 49, 93, 95, 100, 112, 113, 118),
  `docs/results/PAPER_MATERIAL.md` §8.1.
- **Follow-ups:** re-run the full cascade on Kaggle/H100 and replace every number in
  `PAPER_MATERIAL.md` §7.2 with the macro-F1-selected results; combine with the T0.2 split below
  so val and test are reported separately in the same pass.

## 2026-08-19 — T0.2: DENTEX held-out test split methodology decided and scripted

- **What was done:** Wrote `scripts/dentex/split_dentex_holdout.py`, which carves the existing
  Kaggle-processed `val/` pool into a new `val/` + `test/`, grouped by source-image ID parsed from
  crop filenames (`{image_id}_{crop_id}.png`) so crops of the same OPG never land on both sides.
  Verified the core logic (grouping, deterministic seeded split, file move, no image-ID leakage
  across the boundary) against a synthetic 20-image fixture before trusting it — not run against
  the real DENTEX data, which lives on Kaggle, not this machine.
- **Dataset / config:** DENTEX (processed, Kaggle-hosted). Default `test_fraction=0.5`,
  `seed=42`, grouped split, manifest written to `data/dentex/splits.json` (committed once
  generated against real data, per `PUBLICATION_TODO.md` T0.2's "committed splits.json"
  requirement).
- **Metrics:** none — synthetic-fixture verification only (44 fixture files, 20 image IDs, split
  10/10 with the class balance and image-ID partition confirmed programmatically, then the
  fixture was deleted).
- **Key decision or insight:** this is a **weaker independence guarantee than a from-scratch
  three-way split** — there is no patient/study identifier anywhere in this repo's DENTEX
  pipeline and no raw (pre-crop) DENTEX copy to rebuild train/val/test from, so the new "test"
  set is carved from a `val` pool that was itself already used to select among model variants
  across several prior training attempts (see the caries entries above and
  `PAPER_MATERIAL.md` §7.2). That is a soft leak into whichever half becomes test, and must be
  named as a limitation in the paper's methods section, not presented as equivalent to an
  independent held-out set.
- **Source:** `scripts/dentex/split_dentex_holdout.py`,
  `docs/results/PAPER_MATERIAL.md` §7.2/§9.
- **Follow-ups:** run against the real Kaggle dataset, commit the resulting
  `data/dentex/splits.json`, re-run the cascade (combined with the T0.3 macro-F1 fix above), and
  report val/test separately per `PUBLICATION_TODO.md` T0.2.

## 2026-08-19 — T0.1: two-arm augmentation ablation built into the caries severity notebook (code only, not run)

- **What was done:** Per the T0.1 decision already closed in `METHODOLOGY_CHANGELOG.md`
  (2026-08-15) — enable augmentation and re-run as a two-arm comparison rather than just
  disclosing the gap — added a "Phase 2b — Arm B" section to `notebooks/caries/phase-1.ipynb`
  (new cells after the existing Arm A flow). Arm B reruns the *same* two-stage fine-tune
  recipe as Arm A (same starting checkpoint `best_phase2_final.pth`, same class-weight
  schedule `[0.5, 3.5]` → `[0.6, 3.0]`, same lr 3e-5, same epoch counts 9+3, same macro-F1
  checkpointing) with the one actual change: `transform_train` (defined back at cell 107,
  dead code in Arm A per the closed T0.1 finding) is now wired into the training set. `val`
  is unchanged between arms — `transform_val` is pixel-identical to the plain transform, so
  Arm A's existing `val_loader` is reused rather than duplicated. A final comparison cell
  reloads both arms' best checkpoints fresh and prints their macro-F1 and classification
  reports side by side.
- **Dataset / config:** n/a — cells added, not executed (no GPU in this environment). DENTEX
  severity data (`caries` vs `deep_caries`, 133 val crops), same as Arm A.
- **Metrics:** none new.
- **Key decision or insight:** caught and fixed a real bug before it could reach Kaggle:
  `f1_score` is only ever imported *locally* inside the notebook's `validate()` function
  bodies, never at module/global scope, so the new comparison cell would have raised
  `NameError` on `f1_score` if left as first written — added an explicit
  `from sklearn.metrics import f1_score` to that cell. Also caught a self-inflicted error
  while fixing it: an insert shifted cell indices, so a same-session correction attempt
  landed on the wrong cell (overwrote a markdown header with code) — caught immediately by
  re-reading the file's actual cell layout afterward rather than trusting the tool's success
  response, and fixed both cells. All code cells in the new section verified with
  `ast.parse`, and grepped for stray references to variables that don't exist.
- **Source:** `notebooks/caries/phase-1.ipynb` (cells 121–128),
  `docs/results/METHODOLOGY_CHANGELOG.md` (2026-08-15 T0.1 entry, the decision this
  implements).
- **Follow-ups:** run both arms on Kaggle/H100, combined with the T0.2 split above so both
  arms report val **and** test separately; update `PAPER_MATERIAL.md` §7.2 and
  `model_metrics.md` with all four resulting numbers (Arm A val/test, Arm B val/test).

## 2026-08-19 — T0.3: checkpoint criterion and operating threshold made explicit for all four classifiers

- **What was done:** Documented (did not change behavior beyond the caries fix already logged
  above) that all four classifiers — caries gate, caries severity, bone-loss binary, bone-loss
  severity — now select checkpoints by validation macro-F1, and audited every citation of the
  bone-loss binary result (macro-F1 0.9233) across the repo to confirm it is consistently and
  correctly labeled as validation, never test — no mislabels found (`README.md`, `CLAUDE.md`,
  `model_metrics.md`, `PAPER_MATERIAL.md`, `RESULTS_LOG.md`, session memory all agree).
  Additionally documented the current **operating threshold** for the first time: all four
  models use uncalibrated `argmax` over softmax outputs — for the three binary classifiers
  this is mathematically a fixed 0.5 probability threshold on the positive class, not chosen
  by any search or calibration step; for bone-loss severity (3-class) argmax has no single
  scalar-threshold interpretation. No calibration exists yet — that is R3 in
  `MASTER_PLAN_2026H2.md` §3, scheduled for Week 6, not Week 2.
- **Dataset / config:** n/a — documentation and a repo-wide grep audit only.
- **Metrics:** none new.
- **Key decision or insight:** naming the threshold as "uncalibrated 0.5-equivalent argmax" is
  itself a decision — it would be easy to leave this unstated and let a reader assume some
  threshold tuning happened. Stating it plainly now means R3's eventual calibration work reads
  as an improvement over a named baseline, not a silent fix to an unstated gap.
- **Source:** `docs/results/PAPER_MATERIAL.md` §6.7 (new).
- **Follow-ups:** none blocking — this is the documentation companion to the T0.3 code fix
  already logged above, and to R3 when it lands in Week 6.

## 2026-08-20 — T0.6: canonical detector located, verified, and frozen

- **What was done:** `_repo_archive/yolo_a100_run_workspace/` and `_repo_archive/datasets_workspace/`
  — empty on this machine as of 19 Aug — were populated from a separate session between then
  and now. Located `best.pt`/`last.pt` at
  `_repo_archive/yolo_a100_run_workspace/runs_backup/runs/detect/runs/detect/tufts_clean_v1/weights/`,
  exactly where the user pointed. Verified before trusting: both files are exactly 51,227,225
  bytes; the accompanying `args.yaml` and `results.csv` are byte-identical to the copies
  already committed at `models/06_yolo_detection_a100_run/`; `best.pt` loads cleanly under
  Ultralytics (installed for this check) with `task=detect`, one class (`tooth`), 25,311,251
  parameters, matching `run_summary.txt`'s documented 25.28M. Copied both files into
  `models/06_yolo_detection_a100_run/` (git-ignored, `models/**/*.pt`) and verified the copy
  byte-identical by SHA-256 against the archive source. Also diffed the archived
  `YOLO_trained.ipynb` against the already-committed
  `notebooks/yolo_detection/a100_1024px_150ep.ipynb` (identical) and found three test-eval
  prediction JPGs present in the archive but never copied into
  `docs/results/figures/yolo_detection_a100/` — copied them over.
- **Dataset / config:** n/a — verification and file relocation only, no training.
- **Metrics:** none new — same numbers as the 2026-04-23 entry, now with a verified, hashed
  weight file behind them instead of an unverified claim.
- **Key decision or insight:** this closes the one remaining piece of T0.6's W2 exit
  criterion — "one frozen, versioned detector." Version tag `tooth-detector-a100-1024-v1.0`;
  SHA-256 `4d9f099fb90bb03446fd1d81f2a509cd1589bdc0d4de83269894d9128e4b3a2b` (best.pt). Checked
  `_repo_archive/datasets_workspace/` at the same time in case it also carried
  `teeth_polygon.json` or raw Tufts images — it only holds the small scripts/notebooks (22 MB
  total: `convert_tufts_to_yolo.py`, `evaluate_yolo.py`, `train_yolo.py`, three `.ipynb`
  files), not the 2.2 GB of raw data the original `ARCHIVE_MANIFEST.md` describes it as
  having held. **This means R1's seg retrain and re-deriving crops from this now-frozen
  detector remain blocked** — freezing the detector and finding the missing Tufts source data
  are two independent blockers, and only the first is resolved.
- **Source:** `docs/research/T0.6_detector_reconciliation.md` §1 (verification record),
  `models/06_yolo_detection_a100_run/{best.pt,last.pt}`,
  `docs/results/figures/yolo_detection_a100/test_val_batch{1_labels,2_labels,2_pred}.jpg`.
- **Follow-ups:** locate `teeth_polygon.json` and the raw Tufts radiograph images (still not
  found anywhere on this machine) before R1's seg retrain or any crop re-derivation can
  start; both also still need GPU access, unavailable in this environment.

## 2026-08-20 — Triaged two of the three untracked-file decisions carried over since the first session

- **What was done:** `survey_paper/` and `notebooks/bone_loss/06_cej_estimation_v3.ipynb` had
  sat untracked and undecided across three prior sessions (`transfer.md` §1, this session's
  Part 0, Part 6). Resolved both:
  - **`survey_paper/`** — confirmed genuinely stale (not just assumed) by comparing
    `source.bib` reference counts: 47 in this draft vs. 71 in the current, actively-worked
    `Survey Paper Latex folder/source.bib`, and confirmed it was never tracked by git at any
    point (`git log --all` on the path: empty). Relocated with `mv` (never `rm`, per `CLAUDE.md`
    rule 3) to `_repo_archive/survey_paper_stale_47ref_draft/`, recorded as a new item in
    `_repo_archive/ARCHIVE_MANIFEST.md` with the exact recovery command.
  - **`06_cej_estimation_v3.ipynb`** — read in full before deciding, rather than assuming from
    the filename. It's a real further iteration on the CEJ negative result (6 named
    engineering fixes: strongest-gradient boundary detection, tighter search zone, left/right
    asymmetric bone analysis, artifact-column exclusion, overlap-label calibration) — but its
    last saved execution shows `Crops to analyze: 0`: the Colab Drive path it reads
    (`/content/drive/MyDrive/tufts/severity_dataset`) was empty or unmounted at run time, so
    every downstream number in the notebook is `N/A`. **Committed as-is** (research artifacts
    are never deleted per `CLAUDE.md` rule 3, and this is legitimate prepared-but-unexecuted
    future work, not noise), with a note added to `PAPER_MATERIAL.md` §8.3 stating plainly
    that it has never run and must not be cited as a second CEJ data point.
- **Dataset / config:** n/a — file triage and documentation, no training or new analysis.
- **Metrics:** none new. The CEJ negative-result figure (15.1% exact agreement, v2) is
  unchanged — v3 produced no numbers to compare it against.
- **Key decision or insight:** the third untracked item,
  `docs/research/clinical_dataset_provenance.md`, was deliberately **not** acted on. It
  documents real patient-data de-identification procedures for the private clinic dataset,
  was explicitly flagged across two prior sessions as needing human review before entering
  git history "because of what it describes, not because it's wrong," and `CLAUDE.md` states
  `docs/research/` is owned by a separate workstream not to be touched without the task being
  explicitly about it. None of that applies to the other two files, which is why they could be
  resolved directly — this one still needs the user's explicit decision.
- **Source:** `_repo_archive/ARCHIVE_MANIFEST.md` (item 6), `notebooks/bone_loss/06_cej_estimation_v3.ipynb`,
  `docs/results/PAPER_MATERIAL.md` §8.3.
- **Follow-ups:** `docs/research/clinical_dataset_provenance.md` still needs a decision from
  the user — commit as-is, redact/edit first, or keep local-only.

## 2026-08-20 — T0.6/R1: real Tufts seg data obtained, conversion pipeline verified end-to-end; one blocker down to one

- **What was done:** User provided the Tufts Google Drive folder
  (`drive.google.com/drive/folders/1_pPXCzNGlRuLaQhpqScX7sszSXSLQI-U`, public, no sign-in).
  Enumerated it with `gdown` (17,300 files) and downloaded `teeth_polygon.json` (285 MB) and
  all 1,000 raw radiographs from `ZIP/Radiographs/Radiographs/`. Discovered the raw images are
  **landscape (1615x840)**, not the portrait (840x1615) every conversion script assumes
  `Radiographs_rotated/` already is — that rotation step had never been captured as code
  anywhere in this repo. Determined the correct rotation (90° clockwise) empirically: tested
  both directions against real `teeth_bbox.json` boxes, then confirmed far more thoroughly by
  overlaying `teeth_polygon.json` polygons on 7 real rotated radiographs and visually checking
  every one traces an actual tooth. Formalized as new `scripts/yolo/rotate_tufts_radiographs.py`.
  Rotated and verified all 1,000 images (840x1615, zero corrupt). Ran
  `scripts/yolo/convert_tufts_to_yolo_seg.py` **unmodified** (only path constants patched)
  end-to-end against the real data as a validation pass.
- **Dataset / config:** Tufts (Google Drive source), 1,000 images, single-class ("tooth")
  instance segmentation. Validation run used a throwaway temporary split
  (`outputs/eda_tufts/split_TEMP_not_frozen_do_not_use_for_gpu_run.csv`, fixed seed,
  70/15/15), explicitly NOT the frozen `split_v1.csv` — which is a new, separate blocker
  found in the process (see below) — and NOT copied into the repo.
- **Metrics:** validation run only, not a training result: 26,005 polygon instances across
  700/150/150 images (18,214 / 3,871 / 3,920 train/val/test). Val instance count (3,871)
  closely matches the historical bbox conversion's val count (3,794) despite using a
  different image split — a meaningful sanity check on scale. Zero conversion errors; 21
  train / 8 val / 3 test images had no usable polygon instances (normal-range annotation
  gaps, not a pipeline bug).
- **Key decision or insight:** two of the three original T0.6 blockers are now closed
  (`teeth_polygon.json` located and verified; raw images located, and the previously-lost
  rotation transform rederived and validated) — but a **third, previously-unknown blocker**
  surfaced: `outputs/eda_tufts/split_v1.csv` (the frozen split the canonical bbox detector was
  evaluated on) is missing from every location checked (this Drive folder, both
  `_repo_archive/` locations, an exhaustive filename search of this machine). Deliberately did
  **not** generate a replacement split to use as the real training input — doing so would
  silently break direct comparability with the bbox detector's reported test mAP@0.5 (0.7824),
  which is exactly what T0.6's pre-registered criterion (§2) exists to protect. The temporary
  split was used only to prove the code correct, then discarded.
- **Source:** `docs/research/T0.6_detector_reconciliation.md` §3 (full record, includes the
  Drive link, rotation-determination method, and validation-run numbers),
  `scripts/yolo/rotate_tufts_radiographs.py` (new),
  `scripts/yolo/convert_tufts_to_yolo_seg.py` / `train_yolo_seg.py` (status headers updated).
- **Follow-ups:** locate `outputs/eda_tufts/split_v1.csv` — the one remaining blocker before
  the real (non-test) `dataset_seg/` can be assembled — or make an explicit, documented
  decision to accept a new split with the comparability caveat stated everywhere the
  resulting numbers are reported. GPU access is separately still needed to actually run
  `train_yolo_seg.py`.

## 2026-08-20 — Raw DENTEX source data located; GPU setup checklist written

- **What was done:** User provided a second Google Drive folder
  (`drive.google.com/drive/folders/1DtdE_TYuYTeyvuaveQEvuhSpwL6U8Ovp`) and their own
  `phase-1.ipynb` copy from Downloads. Enumerated the Drive folder with `gdown` (10,446
  files) rather than assuming it only held the pre-processed crops `phase-1.ipynb` reads.
  Wrote `docs/research/GPU_SETUP.md` — a from-scratch provisioning checklist for an E2E
  Networks GPU instance (OS/CUDA/Python/package versions, disk budget, data-fetch steps,
  run order) covering everything currently queued (Tufts seg retrain, DENTEX cascade).
- **Dataset / config:** n/a — enumeration and documentation only, nothing downloaded in
  full or trained.
- **Metrics:** none new.
- **Key decision or insight:** the DENTEX Drive folder is not just the processed crops —
  it also has the **raw source `xrays/`** (705 images for the disease-labeled subset),
  the **original COCO-style annotation file** (`train_quadrant_enumeration_disease.json`),
  and the **original crop-generation notebooks**. `scripts/dentex/split_dentex_holdout.py`
  (2026-08-19) was written under the assumption that raw DENTEX access was unavailable, and
  deliberately fell back to carving a new split out of the existing `val/` pool rather than
  building an independent one — that assumption no longer holds. A genuinely independent,
  from-scratch three-way split may now be possible. **Not rebuilt in this session** — this is
  a scope/methodology decision (redo T0.2 properly now vs. proceed with the existing
  fallback) that needs to be made deliberately, not defaulted into either direction. Also
  confirmed the user's Downloads copy of `phase-1.ipynb` (123 cells, accuracy-checkpointed
  throughout) predates the repo's committed version (131 cells, includes the T0.3 macro-F1
  fix and the Arm B augmentation-ablation section) — flagged so GPU time isn't spent running
  the older copy by mistake.
- **Source:** `docs/research/GPU_SETUP.md` (new, full directory listing and counts),
  `scripts/dentex/split_dentex_holdout.py` (2026-08-19 entry, the assumption this updates).
- **Follow-ups:** decide whether to rebuild the DENTEX split from the newly-available raw
  data before the caries cascade re-run, or proceed with the existing val-carve fallback and
  revisit later. Confirm which `phase-1.ipynb` copy (repo vs. Downloads) is authoritative
  before running anything on GPU.

## 2026-08-21 — Frozen split found; real `dataset_seg/` built; 66 teeth found missing from the bbox dataset

- **What was done:** Located `outputs/eda_tufts/split_v1.csv` — reported on 2026-08-20 as
  the last remaining blocker for the R1 seg retrain and as "not findable anywhere". It was
  at `_repo_archive/datasets_workspace/outputs/eda_tufts/split_v1.csv` the whole time; the
  20 Aug search missed it because that search covered a Windows filesystem (`C:\`, `D:\`)
  while this repo and its archive sibling live on macOS, and because
  `.gitignore:103` hides `_repo_archive/datasets_workspace/outputs/` from any git-based
  search. Verified it is the *right* split rather than assuming: its per-split filename
  lists were diffed against the built bbox dataset the canonical A100 detector was trained
  on — **zero differences on all three splits** (700/700, 150/150, 150/150) — and that
  dataset's label files total 3,794 val / 3,924 test instances, matching the A100 run's
  reported instance counts exactly. Then ran `convert_tufts_to_yolo_seg.py` against it for
  real (not the throwaway split used on 20 Aug), producing the actual R1 training input.
- **Dataset / config:** Tufts, frozen 70/15/15 image-level split
  (`split_v1.csv`, SHA-256 `6de8cef2af1e73ff843f0353dccc0f93ddac34f33422c418f8ac07c67accb58b`),
  1,000 rotated radiographs (840×1615), `teeth_polygon.json`. Output
  `data/tufts/dataset_seg/` (gitignored). Script run unpatched — its path constants were made
  environment-overridable instead of copy-patching a throwaway, which is how the 20 Aug
  verification run had to be done.
- **Metrics:** `dataset_seg/` contents — train 700 img / 18,268 instances / 21 empty labels;
  val 150 / 3,807 / 5; test 150 / 3,930 / 6. Total **26,005 instances**, zero conversion
  errors. No model was trained; these are dataset counts, not model metrics.
- **Key decision or insight:** Comparing the new seg labels against the bbox labels for the
  *same images on the same split* showed 942/1,000 images identical and 58 images with 1–3
  **more** seg instances — never fewer, a gap of exactly 66 objects. Root cause found:
  `teeth_polygon.json` and `teeth_bbox.json` carry identical object lists for all 1,000
  images, but `convert_tufts_to_yolo.py` drops any object whose `bounding box` field is under
  2 px on a side, and for these 66 objects **that field is corrupt (1×1 or 1×2 px) while the
  polygon is intact and full-size** — 1,617–13,425 px², up to 682 points, ordinary Universal
  tooth titles spread across the arch, and confirmed by rendering three of them over the
  radiograph as real tooth-sized structures. **The existing bbox dataset is therefore missing
  66 real annotated teeth** (47 train / 13 val / 6 test), which means the frozen detector's
  reported numbers were measured against test ground truth missing 6 of 3,930 instances
  (0.15%) — far too small to move mAP@0.5 = 0.7824 materially, but a genuine data-quality
  defect in the baseline. **Decision: keep all 66 in the seg dataset and do not replicate the
  bbox filter** (propagating a known bug for cosmetic comparability is the wrong trade), and
  **do not modify `convert_tufts_to_yolo.py`** (that would invalidate the frozen detector's
  reproducibility, which T0.6 §1 exists to protect). The resulting 6-instance ground-truth
  difference was written into T0.6 §2's pre-registered acceptance criterion **before** the
  retrain is run, not after seeing results; the 0.75 box-mAP bar is unchanged.
- **Source:** `docs/research/T0.6_detector_reconciliation.md` §3.3 (split recovery + proof),
  §3.5 (dataset build table + the 66-teeth analysis), §2 (criterion caveat);
  `scripts/yolo/convert_tufts_to_yolo_seg.py` (docstring), `scripts/yolo/convert_tufts_to_yolo.py`
  (inline note at the degenerate filter); dataset at `data/tufts/dataset_seg/` (gitignored).
- **Follow-ups:** R1 now has **no data blockers** — only GPU access. Remaining open decisions
  are unchanged from 20 Aug: rebuild the DENTEX split from the newly-found raw data or keep
  the val-carve fallback; and whether `docs/research/clinical_dataset_provenance.md` (written
  on the other machine, not present here) ever enters git history.

## 2026-08-21b — Clinic dataset found on Google Drive with its re-identification mapping intact

- **What was done:** `docs/research/clinical_dataset_provenance.md` (compiled 16 Aug on the
  other machine, held out of every commit pending a decision) was supplied along with Google
  Drive access. Its §1 asserted the clinic dataset is "local to this machine only" and its §7
  listed "confirm whether it has already left this machine" as an open item. Enumerated the
  Drive tree through the connector — **metadata only; no image and no CSV content was opened**
  — to answer that item.
- **Dataset / config:** SDH clinic dataset, Stage 2 (`D:\SDH dataset\dataset\`, 3,219 enhanced
  8-bit PNGs). No processing run, no model touched.
- **Metrics:** none — this is a governance/data-handling finding, not a result.
- **Key decision or insight:** **The claim was false.** The entire Stage-2 tree has been on
  Google Drive since **2026-06-04**, owned by `csdeepak2005@gmail.com` and shared with a
  second Google account: `images/`, `logs/`, `reports/`, `checkpoint.json`,
  `SESSION_MEMORY.md`, and `metadata/index.csv` — 267,337 bytes, the table mapping each
  opaque `000001.png` back to its clinic patient folder. `index.csv` and `images/` are
  siblings under the same shared parent, which is exactly the condition §4 of that same
  document names as voiding the de-identification: *"index.csv must never travel with
  images\ to anywhere the images go."* It travelled ten weeks before the document asserting
  containment was written. Mitigating: the share is account-to-account, not a public link —
  no `type: anyone` permission on `SDH dataset/` or `dataset/`. **Separately**, the Tufts
  research-data folder (`1_pPXCzNGlRuLaQhpqScX7sszSXSLQI-U`) *is* shared
  `role: writer, type: anyone` — world-writable. Public data, so that one is an integrity
  risk (this project re-downloads from it), not a confidentiality one. **Nothing on Drive was
  changed** — it is not this project's account to reconfigure. Two decisions taken: commit the
  provenance record (repo is private) with §1 struck through rather than deleted and the
  literal `index.csv` example row redacted to schema-only; and **rebuild the DENTEX split from
  the raw source data** rather than keeping the val-carve fallback, which is the fix for
  `PAPER_MATERIAL.md` §8.1.
- **Source:** `docs/research/clinical_dataset_provenance.md` §4a (Drive tree, file IDs,
  permissions, and the five recommended actions), §1 (struck claim), §7 (item closed);
  `docs/session-memory/2026-08-21-split-recovery-and-seg-dataset-build.md`.
- **Follow-ups:** all five §4a actions need the Drive owner, not this repo — separating
  `index.csv` from `images/` is the one with a real clock on it. The governance items in
  `clinical_dataset_plan.md` (ethics approval, written clinic agreement, PHI sign-off) are
  unchanged and now have a concrete trigger: an unapproved re-identifiable copy of patient
  data already exists off the origin machine.

## 2026-08-21c — DENTEX split rebuilt from raw source; the carve-from-val fallback is retired

- **What was done:** Acted on the 21 Aug decision to rebuild rather than keep the fallback.
  Downloaded the original COCO annotation file for the disease-labelled subset
  (`train_quadrant_enumeration_disease.json`, 1,188,275 bytes, SHA-256
  `6e1f702cfd6c83bc…`) from the DENTEX Drive folder, wrote
  `scripts/dentex/build_dentex_split_from_raw.py`, and ran it. Output manifest:
  `data/dentex/splits_v2.json` (committed; the raw annotations are gitignored as
  re-downloadable). `scripts/dentex/split_dentex_holdout.py` is kept and marked SUPERSEDED
  rather than deleted.
- **Dataset / config:** DENTEX quadrant-enumeration-disease subset — 705 source X-rays,
  3,529 disease annotations, 4 classes (Caries 2,189 · Impacted 604 · Deep Caries 578 ·
  Periapical Lesion 158). Split 70/15/15 at **image level**, seed 42, stratified on each
  image's 4-bit disease presence-vector (16 distinct signatures observed), largest-remainder
  proportional allocation per stratum. The 27 images carrying no disease annotation are kept,
  not dropped.
- **Metrics:** split composition — train 495 images (70.2%): Caries 1,564 · Deep Caries 400 ·
  Impacted 431 · Periapical 115. val 103 (14.6%): 314 · 94 · 86 · 21. test 107 (15.2%):
  311 · 84 · 87 · 22. Verified: zero image-id and zero filename overlap across all three
  pairs, union = 705/705, annotations accounted 3,529/3,529, and the manifest is
  byte-identical on re-run (SHA-256 `36d2bbb4f54c48e4…`) — the split is reproducible, not
  just seeded.
- **Key decision or insight:** this closes the **structural** half of `PAPER_MATERIAL.md`
  §8.1. The old fallback could only cut the existing val pool in two, and val had already
  been used repeatedly to select among model variants, so whichever half became "test"
  inherited a soft leak — its own docstring said so. Splitting at image level on the raw data
  *before any crop is generated* makes crop-level leakage structurally impossible rather than
  merely avoided: every crop inherits its source image's split. DENTEX ships no patient or
  study identifier, so one image is treated as one patient — the strongest grouping the data
  supports, and a caveat that still needs stating in the paper. **The caries numbers in
  `model_metrics.md` are NOT yet superseded** — no model has been retrained against this
  split. It is the input to that re-run, not a result.
- **Source:** `scripts/dentex/build_dentex_split_from_raw.py` (method in its docstring),
  `data/dentex/splits_v2.json` (manifest, carries source SHA-256, seed, and per-split
  per-class counts), `scripts/dentex/split_dentex_holdout.py` (superseded header).
- **Follow-ups:** regenerate DENTEX crops honouring `splits_v2.json` — crop generation must
  read the manifest and place each crop by its source image's split — then re-run the caries
  cascade and report Phase 1 and Phase 2 on the **test** split. That re-run also needs to
  save the Phase 1 gate classification report, still missing per §9's first blocking item.
  Both need GPU access, same as R1.

## 2026-08-21d — The "open" Universal→FDI bug has been fixed since `f8b31f8`; five docs said otherwise

- **What was done:** While checking what Stage-5 integration would need, verified the
  Universal→FDI mapping described as an open blocking bug in `CLAUDE.md` §5, the root
  `README.md` (four separate places), and `PAPER_MATERIAL.md` §9. It is not open. Commit
  `f8b31f8` ("fix: correct Universal->FDI lower-arch mapping; close Tier-0 audit items")
  fixed it. Confirmed entry-by-entry rather than by reading the commit message:
  `configs/dataset_config.yaml` and `src/utils/fdi_converter.py` hold identical tables, both
  matching the correct mapping (23→32, 24→31, 25–28→41–44, 29–32→45–48), and
  `tests/test_fdi_converter.py` carries regression tests that name the historical bug —
  the shifted lower arch and the duplicated FDI 33/34 that had collapsed the reverse lookup.
- **Dataset / config:** n/a — verification only, no data and no model touched.
- **Metrics:** none.
- **Key decision or insight:** this is `CLAUDE.md` rule 4's stale-status failure mode running
  in the opposite direction — the README once spent three months calling finished models "in
  progress"; here it spent an unknown stretch calling a closed bug open, in five places, with
  the strongest of them ("Left unfixed deliberately so the change is reviewed rather than
  applied silently") reading as an active decision. A reader planning Stage 5 would have
  budgeted work that no longer exists. All five corrected to state the fix, its commit, and
  the date of re-verification. **Nothing about the mapping itself was changed** — the code was
  already right; only the documentation was wrong.
- **Source:** `configs/dataset_config.yaml` (lines 99–131), `src/utils/fdi_converter.py`,
  `tests/test_fdi_converter.py`, commit `f8b31f8`.
- **Follow-ups:** none for the mapping. Worth a wider sweep of `README.md`'s status tables at
  some point — the Stage-1 row still says "canonical not yet frozen", which the 20 Aug freeze
  (`tooth-detector-a100-1024-v1.0`) also settled.

## 2026-08-21e — Weight inventory for Stage-5 integration: the caries checkpoints do not exist anywhere reachable

- **What was done:** Inventoried every trained weight file reachable from this machine, to
  establish what an end-to-end Stage-5 run could actually load. Searched the repo, both
  `_repo_archive/` trees, and the whole of the user's Google Drive.
- **Dataset / config:** n/a — inventory only.
- **Metrics:** none new. Present and loadable: the frozen detector
  (`models/06_yolo_detection_a100_run/best.pt` + `last.pt`, plus the archive originals),
  bone-loss binary (`bone_loss_resnet18_best.pth` / `_final.pth`), bone-loss severity
  (`bone_loss_severity_resnet18_best.pth`). **Absent: both caries cascade checkpoints
  (Phase 1 gate and Phase 2 severity).** Not in the repo, not in either archive, and not in
  Drive — a whole-Drive search returns exactly two `.pth` files, both bone-loss. They were
  presumably left in a Kaggle session output that no longer exists.
- **Key decision or insight:** three of the project's four trained models can be loaded and
  run today; the caries branch cannot. Two consequences. **(1)** A Stage-5/6 end-to-end
  integration can be built and demonstrated *now, on CPU, without GPU access* — detection →
  FDI numbering → bone-loss binary → severity → per-tooth JSON/PDF — with the caries branch
  stubbed behind the same interface until its weights exist. That makes the project's actual
  next milestone unblocked, unlike R1 and the caries re-run. **(2)** The caries numbers in
  `model_metrics.md` (val acc 81%, macro F1 0.77) have **no recoverable checkpoint behind
  them**. They cannot be re-verified, re-evaluated on the new split, or used for inference —
  only replaced by a re-run. That is a reproducibility hole in a paper-facing number and
  should be stated as such rather than discovered by a reviewer.
- **Source:** filesystem inventory of `models/`, `_repo_archive/`; Google Drive search
  (`title contains 'pth' and owner = 'me'` → 2 results, both bone-loss).
- **Follow-ups:** the caries re-run against `data/dentex/splits_v2.json` is now not just an
  evaluation-discipline improvement but the only route to a usable caries model at all. When
  it runs, save the checkpoints into `models/` and record their location per the repo's
  no-large-binaries rule.

## 2026-08-21f — Correction to 2026-08-21e: the caries checkpoints exist, on Kaggle

- **What was done:** Corrects the entry above (`2026-08-21e`). That entry established, correctly,
  that no caries checkpoint is present locally or in Google Drive — but then speculated they
  "were presumably left in a Kaggle session output that no longer exists," and concluded the
  reported caries numbers "can never be re-verified, only replaced." **The speculation was
  wrong and the conclusion that followed from it was wrong.** The user confirms the checkpoints
  are on Kaggle. The search was never extended there: Kaggle needs the account holder's
  credentials, so it is outside what a session here can reach, and that limit should have been
  stated as a limit rather than filled in with a guess.
- **Dataset / config:** n/a — record correction.
- **Metrics:** unchanged. No number in `model_metrics.md` moves.
- **Key decision or insight:** the caries branch is **recoverable, not lost**, which changes
  three things. (1) The scoreboard's caries numbers can be re-verified and re-evaluated against
  the new `data/dentex/splits_v2.json` test split, not merely overwritten by a re-run.
  (2) Stage-5/6 integration can wire the caries branch for **real** rather than stubbing it —
  all four models become loadable once these files are pulled down. (3) The re-run is back to
  being an evaluation-discipline improvement rather than the only route to a working model.
  Reading `notebooks/caries/phase-1.ipynb` also pins down **which** checkpoint backs the
  scoreboard: cell 119's saved `classification_report` output (caries 0.94/0.80/0.87 n=101;
  deep_caries 0.57/0.84/0.68 n=32; accuracy 0.81; macro F1 0.77) matches `model_metrics.md`
  exactly, and that cell evaluates **`best_phase2_fixed2.pth`** — bundled with its
  `class_to_idx` as `phase2_final_bundle.pth` in cell 120. That is the file to treat as the
  canonical caries Phase-2 weight.
- **Source:** `notebooks/caries/phase-1.ipynb` cells 119–120 (Phase 2) and 49/52/60 (Phase 1);
  correction supplied by the user, 21 Aug 2026.
- **Follow-ups:** pull the checkpoints off Kaggle into `models/` (see the entry below for the
  file list and the convention). Two related gaps re-confirmed from the same notebook while
  checking this, both still open: **Phase 1's gate cells (49, 56) have no saved outputs**, so
  the gate classification report is still unrecorded — §9's first blocking item stands; and
  **Arm B's cells (124, 126, 128) have no saved outputs either**, so the T0.1 augmentation
  ablation has been written but never run.

## 2026-08-21g — Caries checkpoint retrieval list and storage convention

- **What was done:** Established where the Kaggle caries checkpoints should land, from the
  existing precedent rather than by invention.
- **Key decision or insight:** the repo already tracks ResNet18 weights in git — all three
  present `.pth` files (43 MB each: bone-loss best/final, bone-loss severity) are committed,
  while the 49 MB YOLO `.pt` files are not (`.gitignore:60`, `models/**/*.pt`). A ResNet18
  caries checkpoint is the same 43 MB shape as the bone-loss ones, so it follows the same
  convention: committed, under a numbered `models/<NN>_<name>/` directory with a
  `run_summary.txt` beside it.
- **Files to retrieve from the Kaggle notebook's saved output** (`/kaggle/working/`), in
  priority order:
  - `phase2_final_bundle.pth` — **the one that matters.** Phase-2 weights + `class_to_idx`,
    the model behind the current scoreboard numbers.
  - `best_phase2_fixed2.pth` — the same state_dict without the bundle wrapper; take it if the
    bundle is missing.
  - `final_model.pth` — Phase-1 gate weights + `class_to_idx` (cell 60). Needed for the
    cascade's first stage; the scoreboard has no numbers for it because its report was never
    saved.
  - `best_model.pth` — Phase-1 best-by-macro-F1, the input to `final_model.pth`.
  - `best_phase2_final.pth` — the Phase-2 starting checkpoint both Arm A and Arm B fine-tune
    from; needed to reproduce either arm or to run the ablation.
  - `best_phase2_augmented.pth` / `best_phase2_augmented_stage1.pth` — Arm B outputs. Expect
    these to be **absent**: those cells have no saved outputs, so the ablation appears never
    to have run.
- **Source:** `notebooks/caries/phase-1.ipynb` (save/load cells 49, 60, 95, 100, 113, 118, 120,
  124, 126); `.gitignore:53–60`; `git ls-files models/`.
- **Follow-ups:** once retrieved, record each file's SHA-256 in a `run_summary.txt` under its
  `models/` directory, the same way `tooth-detector-a100-1024-v1.0` was frozen in T0.6 §1 —
  the caries branch is currently the only trained stage with no version tag and no hash.

## 2026-08-21h — Kaggle output confirmed against the retrieval list; Arm B never ran

- **What was done:** The user showed `/kaggle/working` (558.8 MiB). Checks the predictions in
  `2026-08-21g` against reality rather than leaving them as inference.
- **Present — all five priority files, confirmed:** `phase2_final_bundle.pth`,
  `best_phase2_fixed2.pth`, `final_model.pth`, `best_model.pth`, `best_phase2_final.pth`,
  plus `best_phase2_stage1.pth` and `best_phase2_fixed.pth` (the two intermediate Phase-2
  checkpoints). Seven caries checkpoints in total. Nothing on the retrieval list is missing.
- **Absent, as predicted:** `best_phase2_augmented.pth` and
  `best_phase2_augmented_stage1.pth`. The notebook evidence pointed here already — cells 122,
  124, 126 and 128 carry **no `execution_count` and no outputs**, unlike cells that ran but
  legitimately print nothing (111, 117, and 120, which has `execution_count=19` and is what
  wrote `phase2_final_bundle.pth`). The empty Kaggle directory confirms it.
- **Key decision or insight:** **the T0.1 augmentation ablation has never been executed.**
  Not "run and unrecorded" — never run. `PAPER_MATERIAL.md` §8.1's first bullet ("augmentation
  was defined but never applied") is the defect; the Arm B section in
  `notebooks/caries/phase-1.ipynb` is the fix that was written for it on 2026-08-15 and then
  left unexecuted. It needs the same GPU session as the caries re-run and should be folded
  into it, not treated as separate work. Note also that Arm B fine-tunes from
  `best_phase2_final.pth` — present, so the ablation is runnable as written.
- **Also settled:** Phase 1 of the notebook has **zero** saved outputs and zero execution
  counts across all its cells, so nothing from the gate stage is recoverable from the file —
  not the class counts, not the train/val sizes, not the classification report. §9's first
  blocking item is confirmed open by direct evidence, not just by absence of a number.
- **Source:** `/kaggle/working` directory listing supplied by the user 21 Aug 2026; raw
  `.ipynb` JSON inspection of `notebooks/caries/phase-1.ipynb` (8 of 72 code cells carry saved
  outputs — 79, 83, 104, 106, 108, 109, 114, 119 — all in Phase 2).
- **Follow-ups:** transfer the seven checkpoints into `models/`, hash them into a
  `run_summary.txt`, and give the caries branch the version tag it currently lacks. Then the
  GPU session covers three things at once: caries re-run on `splits_v2.json`, the Phase-1 gate
  report, and the Arm A/B ablation.

## 2026-08-21i — Caries cascade weights retrieved, verified structurally, and frozen as v1.0

- **What was done:** The user retrieved five checkpoints from Kaggle. Placed in
  `models/07_caries_cascade/` with a `run_summary.txt` recording every SHA-256, the
  provenance, and the limitations — giving the caries branch the version tag it was the only
  trained stage to lack: **`caries-cascade-resnet18-v1.0`**.
- **Metrics:** no model metric changes. All five files are ResNet18, 122 tensors,
  44,748,712 bytes of tensor payload each.
- **Verification (no torch on this machine, so structural rather than functional):** read the
  `.pth` zip archives directly. All five are valid archives with readable pickles; opcode
  scans confirm the `fc.weight`/`fc.bias` 512→2 head in each. **The two bundles carry the
  correct and distinct `class_to_idx`** — `{caries, no_caries}` for Phase 1's
  `final_model.pth`, `{caries, deep_caries}` for Phase 2's `phase2_final_bundle.pth`. That
  was the check worth making: a swapped bundle would fail silently inside the cascade.
  Tensor-payload digests (storage records only, pickle wrapper excluded) reproduce the
  notebook's execution order exactly — `best_model.pth` and `final_model.pth` are
  **byte-identical**, confirming cell 52 loaded, cells 54/56 only evaluated, and cell 60
  wrapped without training in between; the three Phase-2 checkpoints are all mutually
  distinct, matching three successive fine-tune stages.
- **Key decision or insight:** two files were deliberately **not** retrieved, and the reasons
  are now verified rather than assumed. `best_phase2_fixed2.pth` is superseded —
  `phase2_final_bundle.pth` is that same in-memory state_dict with `class_to_idx` attached
  (cell 120, `execution_count=19`, straight after cell 119's evaluation). `best_phase2_stage1.pth`
  is dead weight; nothing downstream loads it. **Storage split:** the two bundles are tracked
  in git — together they are the complete runnable cascade, 86 MB — while the three lineage
  checkpoints stay on local disk with hashes recorded, the same handling the YOLO weights get.
  Committing all five would have added 214 MB for 86 MB of usable model, and one of the five
  is a byte-identical duplicate.
- **Source:** `models/07_caries_cascade/run_summary.txt`; `notebooks/caries/phase-1.ipynb`
  cells 52/56/60/95/100/113/116/118/119/120; `.gitignore`.
- **Follow-ups:** functional verification still owed — load each state_dict into a resnet18
  and reproduce cell 119's macro F1 0.77 from the bundle. That needs torch, so it lands in the
  same GPU session as the caries re-run on `splits_v2.json`, the Phase-1 gate report, and the
  never-executed Arm A/B ablation.

## 2026-08-21j — The caries gate's negative class contains no healthy teeth

- **What was done:** Before writing a DENTEX crop generator, recovered and read the three
  notebooks that actually built the caries datasets (found on Google Drive, committed to
  `notebooks/caries/dataset_construction/` — they existed nowhere in this repo despite being
  the provenance of every caries number). Re-derived every count they print, directly from the
  annotation files, to confirm the code does what it appears to do.
- **Dataset / config:** DENTEX quadrant-enumeration-disease. No training, no crops generated.
- **Metrics:** none new. All verification arithmetic reproduced the notebooks' saved outputs
  exactly.
- **Finding 1 — the Phase-1 gate has never seen a healthy tooth.** The label rule is
  `category_id_3 in [1,3] -> 'caries', else -> 'no_caries'`, applied to a file in which every
  annotation is a *diseased* tooth. So `no_caries` is exactly **Impacted + Periapical Lesion**:
  604 + 158 = **762** in train, 40 + 9 = **49** in val — reproducing the notebooks' printed
  counts to the unit. The gate is really "caries/deep-caries vs impacted/periapical-lesion".
  **This is a train/deploy mismatch, not just a naming problem:** in the assembled pipeline the
  detector feeds *every* tooth into this gate, overwhelmingly healthy ones, and the gate has no
  training signal for that class at all. It also explains the notebook's own unanswered margin
  note, "why no_caries recall is lower?".
- **Finding 2 — train and val are different DENTEX releases, not a split.** 705 `train_*.png`
  images (3,529 anns) vs 50 `val_*.png` images (182 anns), **intersection zero**. Phase 2's val
  is 101 + 32 = 133 crops — the "133 validation crops" behind every reported caries metric.
  Consequence for this session's work: `data/dentex/splits_v2.json` splits the 705 and is
  **unaffected and needs no rebuild** (it is an image-level split, agnostic to label grouping),
  but the 50-image pool is a naturally independent set and should be preserved as a second
  evaluation set rather than merged into it.
- **Finding 3 — the fix exists in data already available.** `train_quadrant_enumeration.json`
  holds 634 images — **all of them a subset of the 705** — with 18,095 teeth annotated by
  quadrant and tooth number but no disease label. Joining enumeration teeth to disease
  annotations on `(file_name, quadrant, tooth_number)`: 2,545 match a disease annotation and
  **15,550 do not — genuinely healthy teeth**, averaging 24.5 per image, present in all 634.
  The remaining 71 disease-only images have no enumeration, so no healthy teeth are derivable
  there.
- **Key decision or insight:** this is a T0.1-class problem — a factual-accuracy defect rather
  than a performance one, and `PUBLICATION_TODO.md`'s governing principle names exactly this
  kind of thing as what sinks papers. It must be resolved **before** the crop generator is
  written, because it determines what the generator emits. Deliberately not resolved
  unilaterally: choosing the negative class redefines the task and decides whether the existing
  81% / macro-F1 0.77 remain comparable at all.
- **The verified crop contract**, for whatever is built next — identical across all three
  notebooks: raw COCO `bbox` with `floor`/`ceil` and bounds clipping, **no expansion of any
  kind** (unlike the bone-loss track's 1.5xW/2.0xH), `cv2.resize` to 224x224 with no
  aspect-ratio preservation, BGR PNG via OpenCV, filename `{image_id}_{annotation_id}.png`
  where `image_id` is the COCO id local to its own annotation file.
- **Source:** `notebooks/caries/dataset_construction/` (the three notebooks + README);
  `data/dentex/raw/{train_quadrant_enumeration_disease,train_quadrant_enumeration,validation_triple}.json`
  (gitignored, re-downloadable).
- **Follow-ups:** decide the negative-class definition, then write the generator. Everything
  else in the re-run block is blocked behind that one decision.

## 2026-08-21k — DENTEX crop generator written and verified against the original crops

- **What was done:** Wrote `scripts/dentex/build_dentex_crops.py`, replacing the three Drive
  notebooks that could only produce DENTEX's pre-baked release split. It regenerates every
  caries crop honouring `data/dentex/splits_v2.json`, and emits **both** negative-class
  definitions so the difference between them is measurable rather than assumed.
- **Dataset / config:** DENTEX. Planned output, from a dry run that reads no images —
  **phase1_legacy** train 2,510 / val 515 / test 504 (+182 extern50);
  **phase1_corrected** train 13,375 / val 2,775 / test 2,929 (+182 extern50);
  **phase2** train 1,964 / val 408 / test 395 (+133 extern50). 19,261 crops indexed in total.
- **Metrics:** no model metrics. Every planned count reconciles against the source files:
  legacy train+val+test = 3,529 = the annotation total (caries 2,767 / no_caries 762);
  phase2 = 2,767 (2,189 / 578); corrected minus legacy = 15,550 healthy teeth; extern50 = 182
  (133/49) and its phase2 = 133 (101/32) — the 133 crops behind every reported caries number.
- **Verification — the crop contract was checked, not trusted.** Downloaded four original
  Kaggle crops and their two source X-rays, regenerated them, and compared pixel-for-pixel:
  **three are bit-identical**; the fourth differs by exactly ±1 grey level on ~20% of
  subpixels. That one is the only sample where *both* dimensions downscale (243×300 → 224×224),
  and the deviation is a cv2 version difference in the bilinear downscale path (verified under
  cv2 5.0.0; the notebooks ran a 4.x). No logic difference. Also confirmed: the same crop is
  byte-identical across all three variant trees, the manifest matches the files on disk
  exactly (44/44 in the smoke test), and healthy crops appear only in the corrected variant.
- **Key decision or insight:** the generator emits `phase1_legacy` and `phase1_corrected` from
  the same crops. The re-run already changes four things at once (split, selection criterion,
  LR schedule, augmentation); making the negative class a fifth would leave any metric movement
  unattributable. Legacy stays comparable to the reported 0.81 / macro-F1 0.77 and isolates the
  four fixes; corrected is what the paper reports for the system, since it is what the gate
  actually faces. **The delta between the two arms is itself a reportable result.** Also
  established: **3 images** (`train_666`, `train_677`, `train_695`, all in train) have neither
  disease annotations nor enumeration entries and yield zero crops — reported explicitly by the
  script, because otherwise its per-split image counts silently disagree with `splits_v2.json`.
  And the 50-image extern set has no enumeration counterpart, so the **corrected** gate cannot
  be evaluated with healthy teeth on it — a real asymmetry, stated rather than papered over.
- **Source:** `scripts/dentex/build_dentex_crops.py` (contract and reasoning in its docstring);
  `notebooks/caries/dataset_construction/` (the originals it replaces).
- **Follow-ups:** the generator needs the 705 source X-rays (~2.5 GB, Drive) to run for real —
  they are not on this machine, and downloading them is the next concrete step. After that the
  re-run block can start.

## 2026-08-21m — CORRECTION to 21j and 21k: healthy teeth are NOT derivable from DENTEX

- **What was done:** Ran the crop generator for real against the full local DENTEX copy (which
  turned out to be already on this machine at `~/Downloads/Capstone/DENTEX`, so no download was
  needed). Two anomalies in the output — 748 images read where 752 were expected, and 19
  "skipped_degenerate" crops where the original notebooks reported zero skips — were traced
  rather than waved through, and they exposed a **serious error in entries 2026-08-21j and
  2026-08-21k**.
- **The error:** those entries claimed 15,550 healthy teeth were derivable by joining
  `train_quadrant_enumeration.json` to the disease annotations on
  `(file_name, quadrant, tooth_number)`, on the basis that "all 634 enumeration images are a
  subset of the 705". **That inference was wrong.** The filenames overlap; the *images* do not.
  DENTEX's three training subsets (quadrant / quadrant_enumeration /
  quadrant-enumeration-disease) number their files independently and cover **disjoint sets of
  patients**. Verified three ways: 622 of the 634 shared filenames have different declared
  dimensions; 58 of 60 sampled files differ in actual dimensions on disk; and rendering
  `train_0.png` and `train_1.png` side by side from both subsets shows plainly different people
  (an adult with heavy amalgam restorations vs. a young patient with developing dentition).
  Only the filename matched — never the patient.
- **Consequence:** the `phase1_corrected` tree produced by the first real run is invalid in two
  compounding ways — the join matched teeth belonging to unrelated patients, and the crops were
  then taken from the disease-subset image at enumeration-subset coordinates. All 15,531
  "healthy" crops are meaningless. The 19 degenerate skips were the visible symptom: boxes
  falling outside what was simply a different, narrower scan. Moved to
  `data/dentex/crops_v2/_INVALID_phase1_corrected_DO_NOT_USE/` with an explanation file rather
  than deleted, so the error stays inspectable.
- **What is UNAFFECTED and correct:** `phase1_legacy` (train 2,510 / val 515 / test 504 /
  extern50 182) and `phase2` (1,964 / 408 / 395 / 133), both built purely from the disease
  subset's own annotations and its own images; `data/dentex/splits_v2.json`, which only ever
  split the 705 disease images; and the crop-contract verification in 21k, which was checked
  against disease-subset crops. Counts on disk match the dry-run prediction in every cell.
- **Key decision or insight:** **the negative-class defect from 21j is real and now has no
  known fix within DENTEX's labelled data.** The disease subset annotates only diseased teeth;
  the enumeration subset carries no disease labels, so an un-tagged tooth there is *unknown*,
  not healthy. The recommendation given in 21j — "add healthy teeth" — is withdrawn. The one
  sound alternative left: run the frozen tooth detector (`tooth-detector-a100-1024-v1.0`) over
  the 705 disease images and treat detections that match no disease box as not-diseased. That
  stays within one image and one coordinate space, so it cannot repeat this class of error, but
  it introduces detector error into the labels and needs its own decision. Until then
  `phase1_legacy` is the only valid Phase-1 dataset, and the gate's behaviour on healthy teeth
  remains uncharacterised — a limitation to state, not to quietly fix.
- **Guard added:** `build_dentex_crops.py` now **refuses** `--enum` outright, printing the
  dimension evidence, because the filename overlap makes the join look plausible and it is not.
  The healthy-tooth code path is removed, not merely commented.
- **Source:** `scripts/dentex/build_dentex_crops.py`;
  `data/dentex/crops_v2/_INVALID_phase1_corrected_DO_NOT_USE/WHY_THIS_IS_INVALID.txt`;
  supersedes the healthy-tooth claims in 2026-08-21j and 2026-08-21k.
- **Follow-ups:** decide on the detector-derived negative class. `phase1_legacy` and `phase2`
  are ready for the re-run block now.

## 2026-08-21n — Caries re-run training script written and smoke-verified; crop manifest rebuilt

- **What was done:** (1) Regenerated `data/dentex/crops_v2` with the fixed generator, because
  the manifest and metadata from the first run were **stale artifacts of the buggy run** — they
  still carried a `phase1_corrected` column, an `enum_sha256`, and 15,531 `Healthy` rows
  pointing at the quarantined tree. Anyone reading the manifest would have believed those crops
  were part of the dataset. (2) Wrote `scripts/dentex/train_caries_cascade.py`, the artifact
  that turns T0.1–T0.4 into a single GPU sitting.
- **Dataset / config:** `phase1_legacy` train 2,510 / val 515 / test 504 / extern50 182;
  `phase2` 1,964 / 408 / 395 / 133. Manifest now 3,711 rows, all `src=d`, no `Healthy` rows.
  `images_read` fell from 748 to 724 (= 678 disease-annotated + 46 val), and
  `skipped_degenerate` from 19 to **0** — confirming all 19 skips had come from the invalid
  enumeration path.
- **Metrics:** none real. Smoke-run numbers (1 epoch, 64 images/split) are meaningless by
  construction and are not recorded anywhere as results.
- **Verification performed:** installed CPU torch locally so the script could be *run* rather
  than only syntax-checked. Both arms execute end to end: Phase 1 → Phase 2 backbone transfer
  (0 unexpected keys) → all four splits evaluated → checkpoints, `results.json`,
  `phase1_gate_report.txt`, `phase2_report.txt` written. Checked separately: crop trees have
  **zero split leakage** (no source image in more than one split), **zero filename collisions**,
  disk matches manifest exactly, no zero-byte files, and no file sits in a folder disagreeing
  with its manifest label. Class weights recomputed from the actual training split reproduce a
  hand calculation to float32 precision, and Arm B's recorded config differs from Arm A's in
  exactly one key (`arm`) — the single-variable condition an ablation requires.
- **Bug found and fixed by the smoke test:** `evaluate()` called `confusion_matrix` and
  `classification_report` without `labels=`, so sklearn inferred the label set from whatever
  appeared in the data. On a split where a class was absent — or where the model simply never
  predicted one — this produced a differently-shaped confusion matrix and a report missing a
  row, i.e. **silently inconsistent `results.json` across runs**, not just a crash. Now passes
  `labels=range(n_classes)` everywhere and additionally records per-split true and predicted
  class counts.
- **Key decision or insight:** the script implements a clean recipe rather than replicating the
  notebook's ad-hoc multi-stage fine-tune (1e-3 hand-dropped to 3e-5, an accuracy threshold
  copied by hand out of a printed report). T0.4 asks for scheduling, so cosine replaces the
  hand-drops; the notebook stays as the historical record of how the current numbers were made.
  Class weights are computed from the split rather than hardcoded, so the weighting *scheme* is
  unchanged from the notebook while the values track the new split. It **deliberately does not**
  attempt to fix the negative class, and records that limitation inside every `results.json`.
- **Source:** `scripts/dentex/train_caries_cascade.py`; `data/dentex/crops_v2/crops_meta.json`.
- **Follow-ups:** the block is now GPU-ready. One session runs both arms and produces: T0.1's
  augmentation delta, T0.2's val-vs-test split reporting, T0.3 macro-F1 selection, T0.4's
  schedule and config table, and PAPER_MATERIAL §9's first blocking item — the Phase-1 gate
  classification report, saved rather than printed. Still undecided beforehand: whether to add
  a detector-derived not-diseased class (RESULTS_LOG 21m).

## 2026-08-22 — A 250-image FDI-keyed disease set found in the DENTEX release, with healthy teeth

- **What was done:** Full inventory of `~/Downloads/Capstone/DENTEX/` while updating the repo's
  READMEs. Five subsets were already known; a sixth, `disease/{input,label}/`, had never been
  looked at. It is not part of the DENTEX challenge's four-class disease subset and is
  materially different from it.
- **Dataset / config:** 250 PNG images + 250 LabelMe-format JSONs, stem-for-stem matched.
  1,600 polygon annotations, median 6 per image (range 1–31). Label format
  `{id}-{Turkish name}-{FDI}`, parsed cleanly on all 1,600 with zero exceptions.
- **The eight classes** (Turkish, with counts): `çürük` caries 747 · `küretaj` curettage 265 ·
  `gömülü` impacted 221 · `kanal` root-canal 161 · **`saglam` sound/healthy 91** · `lezyon`
  lesion 75 · `çekim` extraction-indicated 29 · `kırık` fractured 11.
- **Why it matters — three distinct things this unlocks:**
  1. **Per-tooth FDI-keyed ground truth.** Tooth numbers span 11–48, all 32 permanent
     positions. `MASTER_PLAN_2026H2.md` §4.3.1 states that per-tooth FDI-keyed external
     metrics "remain available only from the clinic data, if IRB clears" — **that is no longer
     true**, and it changes what C2/C3 can measure without waiting on governance.
  2. **Real healthy teeth, explicitly labelled.** 91 `saglam` annotations, in the same images
     and the same coordinate space as the diseased ones. This is the first genuine healthy
     class found anywhere in DENTEX, and it does not repeat the disjoint-patient error of
     2026-08-21m. **Caveat that must not be lost:** annotation is not exhaustive — only teeth
     with a finding are marked — so "unannotated tooth = healthy" is still invalid here. Only
     the 91 explicit `saglam` teeth are usable, which is a small class.
  3. **End-to-end evaluation with per-tooth truth**, enabling the stage-wise error-propagation
     decomposition that is contribution C3 and `PUBLICATION_TODO.md` T1.1's hardest item.
- **Leakage check — the finding this rests on:** hashed and signature-matched all 250 against
  the 705 training images and the 50-image extern set. **Exactly one exact duplicate:**
  `disease/input/test_181.png` is byte-identical (MD5 and correlation 1.0000) to
  `training_data/quadrant-enumeration-disease/xrays/train_332.png`. Every other pairing tops
  out at 0.887, which is just "both are OPGs of similar anatomy". Zero overlap with the
  50-image set. **So this is a usable held-out set once `test_181.png` is excluded** — 249
  clean images. Dimension modes match the 705 exactly, so it is the same equipment and
  population, i.e. an internal held-out set, **not** an external-validation cohort. Do not
  present it as cross-institutional evidence; Ningxia remains the external set.
- **Key decision or insight:** nothing was built on this yet, deliberately. It arrived while
  auditing documentation, and the 2026-08-21m error came precisely from acting on an apparent
  dataset relationship before verifying it. The leakage check above is that verification done
  first; what to *use* it for is a scoping decision that belongs with the schedule, not with a
  README pass.
- **Source:** `~/Downloads/Capstone/DENTEX/disease/` (outside the repo, unmodified);
  inventory recorded in `data/README.md`.
- **Follow-ups:** decide whether this becomes (a) the caries cascade's honest held-out test
  set with per-tooth truth, (b) the source of a small real healthy class for the Phase-1 gate
  defect, (c) the substrate for C3's error-propagation analysis, or some combination. All
  three need a parser from LabelMe polygons to the repo's FDI conventions, which does not
  exist yet.

## 2026-08-22b — The canonical detector only works on 90°-rotated panoramics (R4 groundwork)

- **What was done:** Started R4 (Stages 5–6 integration) by building the missing half of
  Stage 2 — positional FDI assignment — and, before building on it, verified the two
  assumptions it rests on: the laterality convention and the input orientation the frozen
  detector expects. The second check found a preprocessing requirement nobody had recorded.
- **Metrics:** detector (`tooth-detector-a100-1024-v1.0`, conf 0.25, imgsz 1024) on one DENTEX
  image, `train_0.png`:

  | Input | Teeth found | Mean conf |
  |---|---|---|
  | DENTEX **as shipped** (upright, 2850×1316) | **3** | 0.361 |
  | DENTEX **rotated 90° CW** (1316×2850) | **35** | 0.418 |

  A healthy adult OPG should yield ~28–32 teeth. The three boxes found on the upright image
  are in the **nasal/sinus region** — not teeth at all. Verified visually, not just by count.
- **Key decision or insight:** **Tufts ships its annotations in portrait coordinates**, so
  `Radiographs_rotated/` (840×1615) is what every converter consumes and therefore what the
  detector was trained on — a *sideways* panoramic, arch running vertically. Confirmed two
  ways: the annotation y-range for image 1 reaches 993, which exceeds the raw height of 840
  but fits 1615; and overlaying `teeth_bbox.json` on both orientations shows the boxes
  tracking the tooth row only on the rotated one. So the rotation established on 20 Aug is
  correct — but its consequence was never followed through: **every non-Tufts image must be
  rotated 90° CW before it touches the detector.**
- **Why this mattered more than it looks:** DENTEX, Ningxia and the clinic data are all shipped
  upright. Running the pipeline on any of them as-is yields near-zero detections, and
  `MASTER_PLAN_2026H2.md` §8's risk register pre-frames poor cross-dataset transfer as
  **"Low — this is the finding"**. A preprocessing bug would have been recorded as a
  scientific result about domain shift, on the project's single most important contribution
  (C2). This is the second time an orientation assumption has cost this project real work;
  the first produced `rotate_tufts_radiographs.py`.
- **Also built:** `src/fdi_assignment.py` — Stage 2 positional assignment, which did not exist
  in any form (`src/utils/fdi_converter.py` is only the Universal→FDI lookup *table*, and
  `src/label_assigner.py` is pixel-overlap for bone-loss *training labels*). Conventions were
  derived from the 1,600 FDI-keyed annotations in `DENTEX/disease/label/` rather than assumed:
  Q1 (patient upper-right) sits at mean normalised x=0.350 and Q2 at x=0.654, so
  **patient-right is image-left** — the standard radiographic convention, now verified rather
  than trusted. Position digit rises monotonically with midline distance across all eight
  positions (0.021 → 0.221), which is what licenses sort-by-distance.
- **What the module deliberately does not do:** positional assignment cannot survive a missing
  tooth — everything distal shifts one place and silently gets the wrong code. Rather than
  assign confidently through that, it flags it (`suspected_gap_before`) and drops confidence.
  All four failure modes named in `MASTER_PLAN` §R4 are reported, none silently corrected:
  missing teeth, position overflow (>8 per quadrant), off-arch detections, sparse quadrants.
  Duplicate codes are impossible by construction and asserted against.
- **Source:** `src/fdi_assignment.py`, `tests/test_fdi_assignment.py` (11 tests, all passing;
  suite now 40/40).
- **Follow-ups:** (1) the orientation rule belongs in the preprocessing contract
  (`MASTER_PLAN` §3.1) and in `run_inference.py` as an explicit, tested step — **not** as tribal
  knowledge, which is how it was lost the first time. (2) Validate FDI assignment against the
  250-image `DENTEX/disease/` FDI ground truth — detector → assign → match to GT polygons —
  which would give the project its first real Stage-2 accuracy number and is the substrate for
  C3's error-propagation decomposition. (3) Then Stages 5–6 proper.

## 2026-08-22c — Stage 2 validated for the first time: positional FDI assignment does not work

- **What was done:** Ran the frozen detector + `src/fdi_assignment.py` against the 250-image
  `DENTEX/disease/` FDI ground truth (`test_181.png` excluded — byte-identical to a training
  image). 249 images, 1,534 annotated teeth. **This is the project's first Stage-2 number of
  any kind**, and the first stage-wise error-propagation measurement (C3).
- **Dataset / config:** detector `tooth-detector-a100-1024-v1.0`, imgsz 1024, conf 0.25,
  NMS IoU 0.50, GT↔detection matching at IoU ≥ 0.30 with centroid-containment fallback.
  Evaluated **GT → detection**: DENTEX annotation is not exhaustive (~6 annotated teeth per
  image against ~28–32 real ones), so detector *precision* is deliberately not reported — an
  unmatched detection is usually a real tooth that simply carries no annotation.
- **Metrics:**

  | | |
  |---|---|
  | Detection recall | **74.6%** (1,144 / 1,534) |
  | Quadrant correct (of detected) | **90.2%** |
  | **FDI exact (of detected)** | **35.3%** |
  | **FDI exact, end-to-end (of all GT teeth)** | **26.3%** |
  | Within ±1 position, correct quadrant | 78.0% |

- **The causal chain, which is the actual result:** quadrant assignment is fine (90.2%) — the
  jaw split and the image-left/patient-right convention both hold. **The position digit is
  what fails**, and not randomly. Errors are asymmetric: **40.2% predict too low against 20.6%
  too high.** Detector recall falls off sharply toward the back of the arch — 98.3% at position
  1 (central incisor) down to **61.0% at position 8** (third molar). A missed premolar or molar
  means every tooth distal to it becomes the *n*-th detected instead of the *(n+1)*-th, so its
  number comes out one or more too low. Detection loss does not merely reduce coverage — it
  **systematically corrupts the numbering of the teeth that were detected successfully.**
- **Key decision or insight:** **positional FDI assignment is not viable for the clinical
  report as designed.** At 26.3% end-to-end exact accuracy, roughly three of every four teeth
  in a per-tooth report would carry the wrong tooth number — and a wrong number is worse than
  no number, because it attributes a finding to the wrong tooth. Better sorting cannot fix
  this; the information needed is simply absent from the box geometry once a tooth is missing.
  Two real routes: raise posterior detector recall, or replace sorting with a learned
  per-tooth enumeration head. **The training data for the second already exists** —
  DENTEX's `quadrant_enumeration` subset carries 18,095 teeth labelled with quadrant *and*
  position across 634 images, and it covers **disjoint patients** from the `disease/` subset
  (RESULTS_LOG 2026-08-21m), so it can train a numbering head while `disease/` stays a clean
  held-out evaluation set. The property that made it useless for deriving healthy teeth is
  exactly what makes it correct here.
- **The confidence flags work.** Exact accuracy falls monotonically with the assigned
  confidence: 41.2% at confidence 1.0 (n=777), 27.5% in [0.30, 0.60) (n=269), 22.7% below 0.30
  (n=22). Unflagged assignments are 41.2% exact against 22.9% for flagged ones. So Stage 5
  filtering can act on these rather than trusting every code equally — which is what
  `MASTER_PLAN` §R3's abstention head is for.
- **A bug this validation caught before it reached the pipeline:** the first run scored **0.0%
  exact and 5.9% quadrant — worse than the 25% of guessing.** Cause: rotated boxes were being
  fed to an assigner that reasons about upright anatomy, where jaws separate vertically and the
  midline runs vertically; in the rotated frame those axes are swapped. Fixing it to un-rotate
  the boxes immediately after detection moved quadrant accuracy from 5.9% to 90.2%. The rule is
  now enforced in code by `src/orientation.py::detect_upright`, which does the rotate and
  un-rotate as one operation so the pair cannot be separated by accident.
- **NMS choice, stated because it matters:** the frozen run's recorded inference default is
  `iou: 0.70`, which leaves duplicate boxes — 31 detections on a sample image with 14 pairs
  overlapping above 0.5 IoU, versus 21 detections and zero such pairs at 0.50. Duplicates are
  specifically corrosive here because every spurious box shifts positional numbering for its
  whole quadrant. **0.50 was chosen a priori on anatomy** — real teeth in a panoramic do not
  overlap by half their area — **not by sweeping the threshold against this evaluation set**,
  which would have contaminated it.
- **Source:** `scripts/eval/validate_fdi_assignment.py`; `src/orientation.py`;
  `outputs/stage2_validation/stage2_{summary,rows,per_image}.json` (gitignored);
  14 overlays at `outputs/stage2_validation/viz/`.
- **Follow-ups:** decide between raising posterior recall and training an enumeration head
  (the latter looks stronger and its data is ready). Until Stage 2 is fixed, Stages 5–6 can be
  built but **any per-tooth report they emit is not clinically trustworthy** and must say so.

## 2026-08-22d — CORRECTION to 22b and 22c: the rotation direction was clockwise, and it is counter-clockwise

- **What was done:** Re-checked the orientation claim after being asked to verify it again.
  Entries 2026-08-22b and 2026-08-22c both state the detector requires a **90° clockwise**
  rotation. **That is wrong. It is counter-clockwise.** All numbers in 22c were therefore
  measured through a 180°-wrong input and are superseded below.
- **How the error happened, precisely:** the direction was inferred from a visual overlay on
  the *pre-existing* `Radiographs_rotated/` files — which showed annotations landing correctly
  on teeth, and did — but **how those files were produced was never checked**. Comparing all
  1,000 `Radiographs/` ↔ `Radiographs_rotated/` pairs directly settles it:

  | Hypothesis | Pairs consistent | mean abs diff |
  |---|---|---|
  | `cv2.ROTATE_90_CLOCKWISE` | **0 / 1000** | ~70 |
  | `cv2.ROTATE_90_COUNTERCLOCKWISE` | **1000 / 1000** | **0.49** (JPEG re-encode noise) |

  The visual check could not have caught this: CW and CCW differ by 180°, and a tooth detector
  is largely indifferent to a 180° flip, so the wrong direction still produced plausible-looking
  detections. **A check that cannot fail is not a check** — the earlier "verified three ways"
  claim in 22b verified the *transform arithmetic*, never the *direction*.
- **Measured cost, 60 images / 372 GT teeth, everything else held constant:**

  | Detector input | Recall | Quadrant | FDI exact | End-to-end |
  |---|---|---|---|---|
  | upright (no rotation) | 7.5% | 71.4% | 0.0% | **0.0%** |
  | 90° CW (what 22c used) | 73.7% | 86.9% | 29.6% | 21.8% |
  | **90° CCW (correct)** | 71.5% | **92.1%** | **36.5%** | **26.1%** |

- **Corrected full-set numbers** — 249 images, 1,534 GT teeth, replacing 22c's table:

  | Metric | 22c (CW, wrong) | **Corrected (CCW)** |
  |---|---|---|
  | Detection recall | 74.6% | **71.8%** |
  | Quadrant correct | 90.2% | **93.0%** |
  | FDI exact (of detected) | 35.3% | **39.1%** |
  | **FDI exact, end-to-end** | 26.3% | **28.0%** |
  | Within ±1 position | 78.0% | 74.0% |

- **Key decision or insight:** **the conclusion of 22c is unchanged and if anything firmer.**
  Stage 2 still fails — 28.0% end-to-end means roughly 7 of 10 teeth carry the wrong number —
  and the failure is still the position digit rather than the quadrant (93.0% correct). Fixing
  the rotation improved every numbering metric without rescuing the approach, which is the
  point: the defect is structural, not a preprocessing artefact. Everything said in 22c about
  detector recall decaying toward the posterior arch and shifting distal teeth inward stands.
- **Fixed in code:** `src/orientation.py` now defaults to CCW, supports both directions
  explicitly, and carries the 1000/1000 evidence in its docstring so the next reader does not
  re-derive it from a visual. Note CCW's inverse needs the original **width** where CW's needs
  the **height** — a detail that silently produces mirrored boxes if carried over unchanged.
  `tests/test_orientation.py` now round-trips both directions against cv2 on real pixels.
- **Source:** `src/orientation.py`, `tests/test_orientation.py`,
  `scripts/eval/validate_fdi_assignment.py`; supersedes the rotation direction in 2026-08-22b
  and all metrics in 2026-08-22c.
- **Follow-ups:** unchanged from 22c — the Stage-2 fix decision (raise posterior recall vs
  train an enumeration head) is what matters, and neither is affected by this correction.

## 2026-08-22e — `rotate_tufts_radiographs.py` rotated the wrong way; it was step 2 of the GPU run order

- **What was done:** Chasing the 22d correction through the codebase found that the error was
  not confined to documentation. **`scripts/yolo/rotate_tufts_radiographs.py` — the script that
  regenerates the Tufts training images — rotated 90° clockwise.** It used PIL
  `Image.ROTATE_270` (= 270° CCW = 90° CW). Verified against the real files:

  | Transform | mean abs diff vs `Radiographs_rotated/` |
  |---|---|
  | `Image.ROTATE_270` (90° CW, as committed) | **70.2** — a different image |
  | `Image.ROTATE_90` (90° CCW, correct) | **0.494** — JPEG re-encode noise |

  After the fix, 40/40 sampled pairs reproduce.
- **Why this was worse than a documentation error:**
  `docs/research/T0.6_detector_reconciliation.md` §4 lists *"Run
  `rotate_tufts_radiographs.py` to produce `Radiographs_rotated/`"* as **step 2 of the GPU run
  order**. Anyone following that on a fresh machine — which is exactly what the doc is for —
  would have regenerated all 1,000 Tufts images 180° flipped relative to the frozen detector's
  training data, then run the R1 seg retrain on them. **It would not have thrown an error and
  would not have looked wrong**: the script's own size assertions still pass (both directions
  give 840×1615), the annotations still overlay coherently, and a segmentation model trains
  perfectly happily on upside-down teeth. The result would have been a quietly degraded R1
  model and an unexplained gap against the bbox baseline, on a run whose acceptance criterion
  is pre-registered.
- **Key decision or insight:** the original direction was set by a visual check — rotate both
  ways, overlay real annotations, keep the one that traces teeth. That check is *incapable* of
  distinguishing CW from CCW, because they differ by 180° and a flipped dental arch still
  looks like a coherent dental arch. The lesson is narrow and worth keeping: **when two
  candidate transforms differ by a symmetry the data itself is nearly invariant to, only an
  artefact comparison can separate them.** The 1,000-pair file diff was decisive in seconds;
  three rounds of visual checking were not.
- **Fixed:** the script (with the evidence in its docstring and an inline note on the changed
  line), plus stale clockwise claims in `convert_tufts_to_yolo_seg.py`, `scripts/yolo/README.md`,
  and a correction box in `T0.6_detector_reconciliation.md` §3.2 — left annotated rather than
  rewritten, since the reasoning there is instructive.
- **Source:** `scripts/yolo/rotate_tufts_radiographs.py`; supersedes the direction in
  `T0.6_detector_reconciliation.md` §3.2 and `RESULTS_LOG.md` 2026-08-20 entries.
- **Follow-ups:** the existing `Radiographs_rotated/` files on this machine are correct (CCW)
  and were never regenerated by the buggy script, so **`data/tufts/dataset_seg/` is unaffected**
  and R1 needs no rebuild. Confirm before any GPU run that the rotated images in use came from
  the original source and not from a re-run of the pre-fix script.

## 2026-08-22f — Refining the Stage-2 diagnosis: positional assignment has a ceiling near 69%

- **What was done:** Cross-checked 22c/22d's causal claim before acting on it. Those entries
  attributed the FDI failure to detector recall decaying toward the posterior arch. That is a
  contributing factor but **not the whole story, and the refinement changes which fix is
  right.**
- **Cross-check 1 — image-level detection count barely predicts correctness.**
  correlation(n_detections, correct) = **+0.077**, and the bins are non-monotonic (54.2% exact
  on images with <16 detections, 30.3% at 22–26, 46.6% at 26–30). If missed teeth were the
  dominant driver this would rise cleanly. It does not.
- **Cross-check 2 — quadrant-level completeness is what actually matters.** Grouping each GT
  tooth by how many teeth were detected *in its own quadrant*:

  | Detections in quadrant | FDI exact |
  |---|---|
  | 4 | 20.3% |
  | 6 | 25.6% |
  | 7 | 41.9% |
  | **8 (complete)** | **68.7%** (n=198) |
  | 9 (a spurious extra) | 40.7% |

  The image-level correlation was near zero because it averages over four quadrants of
  differing completeness — a real effect hidden by aggregation.
- **Cross-check 3 — the ceiling.** Even with a complete 8-tooth quadrant, **31.3% are still
  wrong**, and those errors skew *high* (+1: 22.4%, −1: 5.6%). A contiguous, fully-detected
  arch should score ~100% under a correct algorithm. It does not, because the premise fails:
  **eight detected teeth are not positions 1–8, they are eight of the teeth that survived.**
  Extractions are normal in this population, and rank-order numbering cannot tell an absent
  tooth from a compressed arch.
- **Cross-check 4 — the ground truth is sound**, so this is not a measurement artefact:
  0/249 images contain duplicate GT FDI codes, and every GT value is a valid quadrant/position
  pair in 11–48. Match quality does contribute mildly (21.4% exact for centroid-fallback
  matches at IoU<0.3, n=103, versus 49.6% at IoU>0.7), but at 103 of 1,065 rows it cannot
  explain the gap.
- **Key decision or insight — this closes the Route A / Route B question.** "Raise posterior
  detector recall" (Route A) has a measurable ceiling: **68.7%**, and only for quadrants where
  detection is already perfect. Even granting perfect detection everywhere, positional
  assignment could not exceed roughly that, because its failure at 8/8 is caused by *real
  missing teeth*, not by detection error. **68.7% is not a usable per-tooth report**, so
  Route A cannot succeed no matter how much effort goes into the detector. **Route B — a
  learned per-tooth enumeration head — is not merely the better option, it is the only one of
  the two that can work.** It does not assume contiguity: it classifies each detected tooth
  from its own appearance and position.
- **This is also within the plan, not scope creep.** `MASTER_PLAN_2026H2.md` §5 W3's exit
  criterion already requires "FDI assignment robust to missing teeth / sparse arches". The
  measurement above is the evidence that the naive implementation does not meet it.
- **Correction to 22c/22d:** their stated cause ("detector recall decays → distal teeth shift
  inward") is real but secondary, and stating it alone implies Route A would fix things. It
  would not. The dominant limit is the contiguity assumption itself.
- **Source:** `outputs/stage2_validation/stage2_{rows,per_image}.json`; supersedes the causal
  attribution in 2026-08-22c and 2026-08-22d (their metrics stand).
- **Follow-ups:** train the enumeration head on DENTEX `quadrant_enumeration` (18,095 teeth,
  634 images, quadrant+position labels, patients disjoint from the `disease/` eval set). It is
  a ResNet18-scale classification problem on tooth crops — minutes of GPU, and it folds into
  the session already planned for R1 and the caries re-run.

## 2026-08-22g — Enumeration head built and smoke-verified; the Stage-2 fix is now GPU-ready

- **What was done:** Built the replacement for positional FDI assignment — a per-tooth
  classifier — as two scripts, both verified before any rented GPU time is spent on them:
  `scripts/dentex/build_enumeration_crops.py` (run: 33,461 crops) and
  `scripts/dentex/train_enumeration_head.py` (smoke-run end to end on MPS).
- **Dataset / config:** DENTEX `quadrant_enumeration` — 634 images, 18,095 teeth, all 32 FDI
  classes, 341–630 examples each. Split **by image** 85/15: 538 train images (15,366 teeth,
  30,732 crops after ±15% jitter copies) / 96 val images (2,729 teeth). Crops are 1.5×-expanded
  and 224×224.
- **The FDI mapping was verified, not assumed** — the third time this class of assumption has
  been checked in this project, after two prior ones proved wrong.
  `FDI = (category_id_1 + 1) * 10 + (category_id_2 + 1)`, confirmed spatially: Q1 mean
  normalised x=0.400 vs Q2 x=0.606 (patient-right on image-left, matching the independent
  finding from `disease/`), Q1 above Q3, and mean |x−0.5| rising monotonically 0.015 → 0.227
  across positions 1–8.
- **Key design decision — positional features are load-bearing, not a convenience.** The head
  is a ResNet18 over the crop **concatenated with four positional features** (normalised centre
  x/y, box w/h), feeding two heads: quadrant (4-way) and position (8-way). The reason is
  anatomical: **teeth 16 and 26 are near mirror images**, as are 36/46, 11/21 and every other
  left/right pair. Laterality is not recoverable from crop pixels at all — a pure image
  classifier would be guessing on half of every label. Normalised x resolves it, which is the
  same signal that already gives *geometric* quadrant assignment 93.0%. What the image
  contributes is the position digit, which is precisely where geometry has its 68.7% ceiling.
  The two problems are complementary, and the architecture reflects that rather than hoping one
  model absorbs both.
- **Two heads rather than a 32-way softmax**, so a wrong FDI is diagnostic: it says whether the
  error was the wrong side of the mouth or the wrong tooth along the arch.
- **Horizontal flip is excluded from augmentation** — it would mirror the arch and silently
  invert the quadrant label. Rotation and colour jitter only.
- **Training crops carry ±15% box jitter** (`src.crop_generator.apply_bbox_jitter`) because at
  inference the crops come from *detector* boxes, not ground-truth boxes. Without it the head
  would be trained on a box distribution the pipeline never produces.
- **Evaluation discipline:** train/val come from `quadrant_enumeration`; the **test set is
  `DENTEX/disease/`**, scored by `scripts/eval/validate_fdi_assignment.py` on the *same 249
  images* as the 28.0% baseline, with detector boxes. Disjoint patients (verified 2026-08-21m),
  so the before/after is like-for-like rather than a benchmark chosen after seeing results.
- **Metrics:** none real. The smoke run (1 epoch, 512 crops) produced quadrant 53.5% /
  position 21.9% / FDI 12.9% — meaningless by construction and recorded here only to note that
  the code path executes.
- **Source:** `scripts/dentex/build_enumeration_crops.py`,
  `scripts/dentex/train_enumeration_head.py`, `data/dentex/enumeration_v1/` (gitignored).
- **Follow-ups:** train on the rented GPU, then re-run the Stage-2 validation on `disease/` for
  the number that matters. Baseline to beat: **28.0% end-to-end**, with the positional ceiling
  at 68.7%. If the head lands materially above 68.7% it has done something rank-order sorting
  provably cannot.

## 2026-08-22h — Enumeration head clears the positional ceiling after ONE epoch (83.3%)

- **What was done:** Timed one full epoch of `train_enumeration_head.py` on the local M4 Pro
  (MPS) to size the job. The timing answer was 3.2 min/epoch; the accuracy was the headline.
- **Metrics — 1 epoch, 2,729 held-out val teeth, GT boxes:**

  | | Value |
  |---|---|
  | Quadrant accuracy | **98.6%** (macro-F1 0.986) |
  | Position accuracy | **84.5%** (macro-F1 0.846) |
  | **FDI exact** | **83.3%** |
  | Position within ±1 (given correct quadrant) | 97.7% |

- **Against the thing it replaces:** positional rank-order assignment scores 28.0% end-to-end
  and has a **measured ceiling of 68.7%** even with a fully-detected quadrant. **One epoch of
  the learned head is at 83.3% — already ~15 points above a ceiling that sorting provably
  cannot cross.**
- **Why it crosses the ceiling, mechanically:** rank-order assignment numbers a tooth by *its
  rank among the teeth that were detected*, so a missing or spurious neighbour shifts it. The
  head uses each tooth's *absolute* normalised position plus its appearance, and is therefore
  **order-independent** — it does not care how many other teeth were found. That is exactly the
  failure mode the 68.7% ceiling encodes, and the reason a better sorter could never have
  fixed it.
- **Leakage checked before believing the number:** 0 of 634 source images appear in both
  splits, 0 annotation ids span splits, and all 15,366 jittered copies are train-only. The
  split is by image, so no radiograph contributes to both sides.
- **What this number is NOT:** it is measured on **ground-truth boxes** from the enumeration
  subset. The comparable figure against the 28.0% baseline requires running the head inside
  `scripts/eval/validate_fdi_assignment.py` on `DENTEX/disease/` with **detector** boxes, which
  is a harder setting — detector boxes are noisier and recall is only 71.8%, which caps
  end-to-end accuracy regardless of how good numbering is. **Do not quote 83.3% as the
  end-to-end result.** The honest end-to-end figure is still pending that run.
- **Local timing (M4 Pro, MPS, batch 64, workers 4):** 190.7 s per epoch including validation
  and checkpointing — so 15 epochs ≈ 48 min, 25 epochs ≈ 80 min. Peak memory is a small
  fraction of the 24 GB available.
- **Source:** `scripts/dentex/train_enumeration_head.py`; run artifacts in the session
  scratchpad (not committed — this was a timing run, not the real training run).
- **Follow-ups:** (1) train properly for 15–25 epochs; (2) wire the head into
  `validate_fdi_assignment.py` and re-run on `disease/` for the like-for-like number; (3) run
  the with/without-positional-features ablation, which would substantiate the design claim that
  laterality is not recoverable from crop pixels — a clean C5 ablation costing one extra run.

## 2026-08-22i — Enumeration head trained: Stage-2 FDI accuracy 28.0% → 52.2% end-to-end

- **What was done:** Trained the Stage-2 enumeration head to completion (15 epochs, 48 min on
  the local M4 Pro via MPS) and evaluated it on the **same 249 `DENTEX/disease/` images, the
  same detector, the same matching rule** as the 28.0% positional baseline. Also ran the
  one-to-one ablation. This replaces rank-order assignment as the pipeline's Stage 2.
- **Dataset / config:** train on DENTEX `quadrant_enumeration` — 30,732 crops (15,366 teeth +
  jittered copies) from 538 images; val 2,729 teeth from 96 images, **split by image**.
  ResNet18 (ImageNet-pretrained) over 1.5×-expanded 224px crops, concatenated with four
  positional features, two heads (quadrant 4-way, position 8-way). AdamW lr 1e-3, cosine
  annealing over 15 epochs, batch 64, seed 42. Selection on val FDI-exact; best at epoch 13.

- **THE RESULT — like-for-like on the held-out `disease/` set, detector boxes:**

  | | Positional (baseline) | **Head + one-to-one** | Δ |
  |---|---|---|---|
  | Detection recall | 71.8% | 71.8% | — (same detector) |
  | Quadrant correct | 93.0% | **95.5%** | +2.5 |
  | FDI exact (of detected) | 39.1% | **72.7%** | **+33.6** |
  | **FDI exact, end-to-end** | **28.0%** | **52.2%** | **+24.2** |
  | Duplicate FDI codes | 0 (by construction) | **0** | — |

- **The ceiling is broken, which was the whole point.** Positional assignment was measured at a
  hard ceiling of **68.7%** even on fully-detected quadrants (2026-08-22f). The head numbers
  **72.7% of detected teeth** correctly — above that ceiling. It does so by being
  *order-independent*: it judges each tooth on its own appearance and absolute position rather
  than its rank among whatever else was detected, so a missing neighbour no longer shifts it.
- **End-to-end is now capped by Stage 1, not Stage 2.** With recall at 71.8%, perfect numbering
  would give 71.8% end-to-end. The head reaches 52.2%, i.e. **72.7% of the achievable maximum**.
  The bottleneck has moved from numbering to detection — which is a much more tractable problem
  and changes where effort should go next.
- **Ablation — one-to-one assignment (free, inference-only):**

  | | FDI/detected | End-to-end | Duplicate codes |
  |---|---|---|---|
  | Hungarian one-to-one | **72.7%** | **52.2%** | **0** |
  | Plain argmax | 70.6% | 50.7% | **1,013** |

  Plain argmax emits **1,013 duplicate FDI codes** — anatomically impossible, since a mouth has
  at most one tooth 16. Constraining to a one-to-one matching removes all of them *and* gains
  1.5 points end-to-end. It costs 1.6 points of raw quadrant accuracy (97.1% → 95.5%), because
  the global constraint sometimes moves a tooth across a quadrant boundary to satisfy it —
  a real trade, and the FDI-exact gain says it is worth making.
- **Val (GT boxes, for diagnosis only):** quadrant 99.4%, position 92.1%, FDI exact 91.6%
  (macro-F1 0.916). Per-position accuracy is remarkably flat — 0.886–0.963 across all eight
  positions — in sharp contrast to the detector, whose recall collapses from 98.3% at position 1
  to 61.0% at position 8. **The head does not share the detector's posterior weakness.**
  **These val figures are selection-biased** (the checkpoint was chosen on this split) and use
  ground-truth boxes; they are a model-selection diagnostic, not a result. The result is the
  52.2% above.
- **Train loss fell 0.807 → 0.002 while val FDI plateaued near 0.91** from epoch 8, i.e. the
  model memorised the training set and the last third of the schedule bought little. A shorter
  run, or early stopping on val FDI, would give the same model for less compute.
- **Figures saved for the paper** in `docs/results/figures/enumeration_head/`: training curves
  (with both positional baselines drawn in), confusion matrices for quadrant / position / the
  full 32-class FDI, per-position accuracy, and a qualitative overlay on `test_103` where the
  head gets FDI 18, 15, 46 and 36 right that positional assignment did not.
- **Source:** `scripts/dentex/train_enumeration_head.py`, `src/fdi_head_inference.py`,
  `scripts/eval/validate_fdi_assignment.py --method head`;
  `outputs/enumeration_head/`, `outputs/stage2_validation/` (gitignored).
- **Follow-ups:** (1) Stage 2 is no longer the binding constraint — **detector recall is**;
  R1's seg retrain may help and is already prepared. (2) The positional module stays as the
  documented baseline, not as the pipeline default. (3) A with/without-positional-features
  ablation would substantiate the design claim that laterality is unrecoverable from pixels;
  one extra 48-minute run.

## 2026-08-22j — CORRECTION to 22i: 34% of the Stage-2 test set was in the head's training data

- **What was done:** Asked to re-verify the FDI fix before relying on it, ran the one leakage
  check that had not been done: **`quadrant_enumeration` (the head's training images) against
  `disease/input` (the evaluation images)**. They overlap. All numbers in 2026-08-22i are
  contaminated and are superseded below.
- **The leak:** **85 of the 250 `disease/` images are byte-identical (MD5) to enumeration
  training images** — 34% of the test set. A separate, previously-known leak accounts for one
  more (`test_181` ↔ `train_332`, into the *detector's* training set). Total excluded: **86**.
  **164 clean images remain.**
- **Why it was missed, precisely:** I verified that `quadrant_enumeration` and the
  **disease *subset* (705 images)** cover disjoint patients — which is true, and is what
  RESULTS_LOG 2026-08-21m records. I then treated that as covering `disease/` too. It does not:
  `disease/` is a *third* folder, and a third of it is shared with the enumeration images. Two
  folders being disjoint says nothing about a third. **A verified fact about one pair was
  generalised to a pair it was never measured on** — the same shape of error as the
  filename-overlap bug it was supposed to guard against.
- **CORRECTED metrics — 164 clean images, 936 GT teeth, identical settings for both methods:**

  | | Positional | **Head** | Δ |
  |---|---|---|---|
  | Detection recall | 67.0% | 67.0% | — |
  | Quadrant correct | 92.3% | **94.7%** | +2.4 |
  | FDI exact (of detected) | 34.1% | **69.4%** | **+35.3** |
  | **FDI exact, end-to-end** | **22.9%** | **46.5%** | **+23.6** |
  | Duplicate FDI codes | 0 | **0** | — |

- **What the leak was worth:** the head measured **52.2%** end-to-end on the contaminated set
  versus **46.5%** clean — an inflation of **+5.7 points**, and +3.3 points on FDI-of-detected.
- **The ceiling claim, re-measured on clean data:** the positional ceiling on fully-detected
  quadrants is **67.0%** here (not the 68.7% measured on the contaminated set), and the head
  reaches **69.4%** of detected teeth. **It still clears the ceiling, but by +2.4 points, not
  the +4.0 previously reported.** The qualitative conclusion survives — an order-independent
  method exceeds what rank-order assignment can reach — but the margin is narrower and should
  be quoted as such.
- **The headline improvement is unaffected in kind:** end-to-end **22.9% → 46.5%** and
  of-detected **34.1% → 69.4%** are both a **2.0× improvement**, measured on data the head has
  never seen. That is the result; it did not depend on the leak.
- **Evaluating on the clean subset is sufficient — no retraining is needed.** The head trained
  on 85 images that also appear in `disease/`, but it is now scored only on the 164 it never
  saw, which is a valid held-out estimate. Retraining without them would change the model
  without changing the validity of this measurement.
- **Guard added so this cannot recur:** the exclusion list is generated to
  `data/dentex/disease_leaked_images.json` (tracked) and loaded by
  `scripts/eval/validate_fdi_assignment.py`, which now names both leakage sources in code
  rather than in a comment.
- **Source:** `outputs/stage2_clean/` (both methods, clean subset);
  `data/dentex/disease_leaked_images.json`; supersedes all `disease/`-set metrics in
  2026-08-22i and the ceiling figure in 2026-08-22f.
- **Follow-ups:** unchanged in substance — Stage 2 is fixed and detector recall (67.0% on this
  subset) is now the binding constraint. But **re-check the leakage question for every future
  evaluation set**, including Ningxia: overlap must be measured against *each* training corpus
  separately, never inferred from a neighbouring pair.

## 2026-08-22k — Two papers read; both independently support decisions already taken

- **What was done:** Read DPML (Cao et al., *Expert Systems With Applications* 254:124446,
  2024) and DentFound (Zhu et al., *Nature Biomedical Engineering*, 2026) and checked them
  against what this project has built, rather than for general background.

- **DPML §3.4 is direct prior art for the enumeration head's central design choice.** It states
  the rationale almost exactly as this project arrived at it independently:
  *"dentists typically identify tooth categories by considering the relative position of the
  target tooth. However, this mechanism is rare in general machine learning models… We have
  developed a mechanism to provide the model with positional information."* Their conclusion:
  *"the position-based image classification strategy utilizes the spatial information of teeth
  to improve model performance in scenarios of limited data availability."*
  **Cite it as the precedent for feeding spatial priors to a tooth classifier.** Implementation
  differs — DPML draws a positional marker onto the image and feeds the whole labelled image;
  ours concatenates four normalised box features into the classifier head. Same principle, and
  ours is the cheaper of the two.

- **DPML also, unintentionally, corroborates the laterality argument.** It classifies teeth into
  **eight** classes, justified explicitly by bilateral symmetry: *"the left and right sides of
  the mouth mirror each other."* By collapsing mirrored pairs it **avoids** the problem this
  project had to solve — FDI requires 32 classes and therefore requires distinguishing 16 from
  26, which are near-mirror images. DPML's own symmetry argument is the reason appearance alone
  cannot settle laterality, and hence why positional features are load-bearing here rather than
  merely helpful. It also explains why DPML can safely use horizontal flipping in augmentation
  while this project must not: flipping is label-preserving for their 8 classes and
  label-inverting for our 32.
  **Framing worth using:** our position head (8-way) is DPML's tooth-type task; our quadrant
  head (4-way) supplies the laterality DPML deliberately sets aside.

- **DentFound's instance-mask ablation is real, and R1's justification checks out.**
  `MASTER_PLAN_2026H2.md` §3 R1 asserts that DentFound's ablation shows instance masks are
  load-bearing. Verified against the paper: with tooth instance segmentation masks it reports
  relative improvements of **20.35% precision, 23.01% recall, 23.11% F1** on diseased-tooth
  identification, and attributes this to *"instance-level supervision enhances the model's
  sensitivity to precise tooth positional information as well as the overall structural
  characteristics of the dentition."* R1 stands as justified; the numbers can now be cited
  rather than asserted.

- **The most useful finding: DentFound names our Stage-2 problem as its own failure mode.**
  On 56,351 teeth it reports **73.58% accuracy / 73.87% recall / 84.78% F1** for aligning tooth
  positions with disease findings, and states that where its reports were judged *inferior* to
  human ones this was *"primarily owing to misalignment between tooth position and disease
  annotation."* So a 101,000-patient frontier VLM has the same weak link, and says so.
  **This reframes our Stage-2 work**: it is not a local bug we happened to have, it is a
  documented open problem at frontier scale, and our 22.9% → 46.5% progression with an explicit
  ceiling argument is a contribution to it rather than an embarrassment. **Do not claim a
  numeric comparison** — their 73.58% is disease-finding-with-position on a different corpus,
  ours is pure FDI numbering on 164 images; the tasks and denominators differ.

- **No method change is warranted by either paper.** DPML's polar-coordinate contour extraction
  targets segmentation, not numbering, and is a candidate for R1/R2 rather than Stage 2. Its
  positional mechanism is a heavier variant of what we already do.
- **Source:** `2026Zhu.pdf` (DentFound), `DPML…pdf`, both under `~/Downloads/Capstone/`.
- **Follow-ups:** add both to the Related Work comparison table; cite DPML in §5.2/§6 for the
  spatial-prior design and DentFound in §3 R1 for the instance-mask ablation and in §8.10 for
  the tooth-position failure mode.

## 2026-08-22l — Enumeration head frozen as `fdi-enumeration-head-resnet18-v1.0`

- **What was done:** Froze the Stage-2 enumeration head into `models/08_fdi_enumeration_head/`
  with a hash and a full `run_summary.txt`, matching how the detector and caries cascade were
  frozen. Until now it was the current numbering method while living in `outputs/` with no tag,
  no hash and no record — an inconsistency worth closing before R4 starts consuming it.
- **Version tag:** `fdi-enumeration-head-resnet18-v1.0`
  **SHA-256:** `e6abf1cd959c36824ef0061db84a5fbc8793af314099cb3cc72027662445cc5a`
- **Tracked in git (46 MB total)** — consistent with the existing precedent, where every
  43 MB ResNet18 (`03_`, `04_`, `07_`) is tracked and only the 49 MB YOLO weights are not.
- **What the directory holds, and why each piece is there:**
  - `enumeration_head_best.pth` — best epoch by val FDI-exact (13 of 15), not the last.
  - `training_results.json` — full config, per-epoch log **including train loss**, confusion
    matrices for quadrant/position/32-class FDI, per-class accuracy.
  - `enumeration_manifest.csv` — all 33,461 crops with source image, split, FDI, and the four
    positional features. The complete record of what the model actually saw; it makes the run
    reproducible without re-deriving the split.
  - `eval_stage2_head.json` + `eval_stage2_positional_baseline.json` — the held-out result and
    the method it replaces, same images and settings, so the comparison travels with the model.
  - `eval_excluded_leaked_images.json` — the 86 excluded images. **Without this the numbers
    cannot be reproduced**, and would come out 5.7 points too high.
- **`run_summary.txt` records** the architecture and why positional features are load-bearing,
  the training config, both result tables, the ceiling argument, the DPML prior-art citation,
  the full leakage story with its root cause, the instruction to check overlap per-corpus for
  future evaluation sets, and the exact commands to reproduce.
- **Verified after freezing, not assumed:** the validation script's default now points at
  `models/08_fdi_enumeration_head/`, and re-running end to end from that location reproduces
  **46.5% exactly**.
- **Paper figures** now in `docs/results/figures/enumeration_head/`: training curves with both
  baselines drawn in, three confusion matrices, per-position accuracy, and a new
  **`qualitative_positional_vs_head.jpg`** — the same radiograph under both methods, with the
  headline numbers on each panel. That one is figure-ready as-is.
- **Remaining inconsistency:** bone-loss weights (Stages 4a/4b) are still the only trained
  models without a version tag.
- **Source:** `models/08_fdi_enumeration_head/run_summary.txt`.

## 2026-08-24a — FDI audit: implementation correct; the *ceiling* figure was wrong and understated the result

- **What was done:** A full correctness audit of the FDI chain, re-deriving every claim from
  code and saved artefacts rather than from the log. **The implementation is correct.** Four
  defects were found around it — one real code bug, two wrong numbers in this log, and stale
  docstrings — and all are fixed here. Supersedes the ceiling figure in **2026-08-22j** and
  **2026-08-22f**.

- **VERIFIED CORRECT (each re-derived, not taken on trust):**
  - `src/utils/fdi_converter.py` — all 32 Universal→FDI entries checked individually against
    the standard (Universal 1 = upper-right third molar = FDI 18 … 32 = FDI 48). Correct.
  - **Joint-probability indexing in `src/fdi_head_inference.py`.** `(lq.unsqueeze(2) +
    lp.unsqueeze(1)).reshape(N, 32)` is row-major `k = q*8 + p`, and `FDI_CODES` is built
    q-outer/p-inner, so column `k` really is `FDI_CODES[k]`. A transposition here would be
    silent and would have corrupted every prediction. It is right.
  - **Rotation transforms**, independently re-derived against `np.rot90` over 1,600 random
    points at five image sizes including the real 840×1615: **0 mismatches**, forward and
    inverse, CCW and CW. The CCW contract holds.
  - **Leakage exclusion is applied, not merely present**: both eval runs report
    `n_images = 164`, `excluded = 86`.
  - **Headline metrics reproduce exactly** from the raw per-tooth rows: positional
    22.86% / head 46.47% end-to-end, 34.13% / 69.38% of detected, recall 66.99%, **0 duplicate
    FDI codes** in 627 assignments.
  - Training script is ML-sound: discriminative LR with an assert that the parameter groups
    cover the model, no horizontal flip (it would invert the quadrant label), seeded
    generator, explicit `labels=` in every confusion matrix, honest caveats block.

- **DEFECT 1 — the ceiling figure is wrong in four documents. `67.0%` is the detector's
  recall, not the ceiling.** The two are unrelated quantities that were confused while writing
  2026-08-22j. Recomputed on the clean 164-image set, bucketing both methods by the *same*
  geometric detections-per-quadrant so the populations are identical:

  | Detections in quadrant | n | Positional | Head | Δ |
  |---|---|---|---|---|
  | 6 | 115 | 26.1% | 72.2% | +46.1 |
  | 7 | 159 | 36.5% | 74.2% | +37.7 |
  | **8 (complete)** | **101** | **66.3%** | **80.2%** | **+13.9** |

- **DEFECT 2 — the "+2.4 points" margin compared two different populations,** and therefore
  understated this project's own result. It set the positional ceiling (restricted to teeth in
  complete 8-detection quadrants) against the head's accuracy over *all* detected teeth
  (69.4%). On the same population the head scores **80.2%** and the margin is **+13.9 points**,
  not +2.4. **The head beats positional assignment in every single bucket.** The corrected
  numbers strengthen the architectural claim rather than weakening it: this is not a narrow
  win that needs hedging.
- **Root cause of both: the figure came from an unsaved ad-hoc snippet.** Now
  `scripts/eval/analyze_stage2_ceiling.py`, which reads only saved artefacts and writes
  `outputs/stage2_clean/stage2_ceiling_analysis.json`. **Rule 1's "traceable to a saved
  output" applies to intermediate analyses too, not just headline metrics.**

- **DEFECT 3 — real code bug: the jitter augmentation was only half-applied.** In
  `build_enumeration_crops.py` the jittered variants `(vx,vy,vw,vh)` produced the *crop*, but
  the positional features were written from the un-jittered ground-truth box. Confirmed
  against the frozen manifest: **all 15,366 jittered rows carry their original's features,
  0 differ.** The head was therefore trained on shifted images paired with clean coordinates —
  precisely the box precision the pipeline cannot deliver, since at inference both crop and
  features come from the same noisy detector box. The stated purpose of the jitter ("emulate
  the detector box distribution") was thus not achieved for the features. **Fixed** — features
  now derive from the jittered box.
  - **This does NOT invalidate v1.0's numbers.** They were measured end-to-end on real
    detector boxes, so whatever the mismatch costs is already inside 46.5%. The fix is an
    expected *improvement*, unmeasured until a retrain. `fdi-enumeration-head-resnet18-v1.0`
    remains the frozen, reproducible-as-built model; the corrected builder yields v1.1.

- **DEFECT 4 — stale docstrings asserted the disproved disjointness.**
  `train_enumeration_head.py` still told the reader `disease/` was "disjoint patients
  (verified)" and "249 images" — the exact false claim that caused the leakage — and
  `build_enumeration_crops.py` said the same. Both now state the 85-image overlap and the
  164-image clean set, and `baseline_to_beat` in the results JSON now carries 0.229/0.663
  instead of the leaked 0.280/0.687.

- **Environment regression (not a code defect):** `cv2` and `ultralytics` are absent from the
  active interpreter (`/opt/anaconda3`, torch 2.2.0). **18 of the 46 tests cannot run**
  (`test_crop_generator` 12, `test_orientation` 6) and the eval script cannot be re-executed.
  The 28 tests that do not need cv2 **all pass**. The "46/46" claim was true when written and
  is not reproducible now until the environment is restored.
- **Source:** `scripts/eval/analyze_stage2_ceiling.py`,
  `outputs/stage2_clean/stage2_ceiling_analysis.json`, `outputs/stage2_clean/stage2_rows_*.json`,
  `models/08_fdi_enumeration_head/enumeration_manifest.csv`.
- **Follow-ups:** correct the ceiling in `model_metrics.md`, `PAPER_MATERIAL.md`,
  `transfer.md` and `run_summary.txt` (done in this session); restore `cv2`/`ultralytics`
  before any Stage-2 re-run; consider a v1.1 retrain with the jitter fix, but only *after* R4,
  since R4 is blocked on nothing and the head is already good enough to integrate.

## 2026-08-24b — Environment restored; Stage 2 reproduces byte-for-byte; one-to-one ablation re-measured clean

- **What was done:** With `cv2` and `ultralytics` installed, everything 2026-08-24a could not
  execute was executed. **Stage 2 reproduces exactly.** The one-to-one ablation, previously
  only available on the contaminated set, was re-measured on clean data.

- **Environment — the install broke three working packages before it fixed two.** Installing
  opencv/ultralytics pulled in **numpy 2.5.2**, and `torch 2.2.0` / `scipy 1.12.0` /
  `scikit-learn 1.4.0` are all compiled against numpy 1.x. Measured breakage: `torch.numpy()`
  and `torch.tensor(ndarray)` both raised, `scipy.optimize.linear_sum_assignment` failed to
  import (**this is the Hungarian assignment — Stage 2 cannot run without it**), and sklearn
  failed entirely. **Fix: pin `numpy==1.26.4`.** cv2 5.0.0 declares `numpy>=2` but is
  runtime-compatible with 1.x (numpy-2-built binaries are, by design), verified by exercising
  `resize`/`rotate`/`cvtColor`/`imencode`. All seven probed capabilities now pass, MPS included.
  **`pip install --upgrade pip` upgrades pip only** — it was the transitive numpy bump that did
  the damage.
- **Full test suite runs for the first time since the regression: 46/46 pass.**

- **Reproduction is exact, not approximate.** Re-running both methods from the frozen weights
  (sha256 `e6abf1cd…` re-verified against `run_summary.txt`) reproduced every headline number —
  recall 67.0%, head 69.4% / 46.5%, positional 34.1% / 22.9%, quadrant 94.7% / 92.3%, 0
  duplicates — and the artefacts are **byte-identical** to `outputs/stage2_clean/`:
  `stage2_rows_{head,positional}.json` and `stage2_per_image_{head,positional}.json` all match
  under `diff`. All 936 per-tooth rows agree. The pipeline is deterministic end to end, through
  YOLO detection, rotation/un-rotation, crop generation, head inference and Hungarian assignment.
- **The corrected ceiling holds on the fresh run:** positional **66.3%** vs head **80.2%** on
  complete (8-detection) quadrants, **+13.9 points**, n=101 — identical to 2026-08-24a.

- **One-to-one ablation, re-measured on the clean 164-image set** (both rows identical settings):

  | | FDI/detected | End-to-end | Quadrant | Duplicate codes |
  |---|---|---|---|---|
  | Hungarian one-to-one | **69.4%** | **46.5%** | 94.7% | **0** |
  | Plain argmax | 65.1% | 43.6% | **96.8%** | **679** |

- **The clean ablation is a *stronger* result than the contaminated one.** The gain is
  **+4.3 points of-detected / +2.9 end-to-end**, against +2.1 / +1.5 previously reported on the
  leaked set. Supersedes the 72.7 / 52.2 vs 70.6 / 50.7 / 1,013 figures in 2026-08-22i.
- **The trade-off is real and should be reported, not hidden:** one-to-one *costs* **2.1 points
  of raw quadrant accuracy** (94.7% vs 96.8%), because satisfying the global constraint
  sometimes moves a tooth across a quadrant boundary. It is still the right default — a
  duplicate FDI code is not a slightly-wrong answer but an anatomically impossible one that a
  per-tooth report cannot render at all.
- **Key insight:** the constraint's value scales with how confusable the input is. On clean
  data the classifier is *less* certain, so more teeth compete for the same code (679 duplicates
  across 627 detections), and arbitrating those collisions is worth more. Measuring an ablation
  on contaminated data understated the component being ablated.
- **Source:** `outputs/stage2_reverify/` (both methods + ceiling analysis),
  `outputs/stage2_reverify_argmax/`, `scripts/eval/analyze_stage2_ceiling.py`.
- **Follow-ups:** none blocking. Stage 2 is verified reproducible; **R4 integration is next and
  has no blocker.** Record `numpy==1.26.4` as a hard constraint for this repo — a future
  `pip install` that bumps numpy will silently break the Hungarian assignment again.

## 2026-08-24c — Third FDI pass: data contracts verified at source; the architecture rationale was overstated

- **What was done:** A third audit pass, deliberately checking what the first two had *not*:
  the data contracts at both ends of the chain, split hygiene, class balance, preprocessing
  equivalence, edge cases, and — new — an **input ablation** testing the architecture's stated
  rationale. The implementation remains correct. **One documented claim was refuted by
  measurement.**

- **The DENTEX category→FDI mapping is verified at source, and more strongly than claimed.**
  Previous docs said it was "confirmed spatially". It is in fact **documented in the COCO
  metadata**: `categories_1` carries `name` 1,2,3,4 and `categories_2` carries `name` "1".."8",
  so `(category_id_1+1, category_id_2+1)` is the file's own labelling, not an inference.
  The spatial signature corroborates independently: Q1 cx=0.400/cy=0.421, Q2 cx=0.606/cy=0.420,
  Q3 cx=0.603/cy=0.669, Q4 cx=0.403/cy=0.671 — upper-right, upper-left, lower-left, lower-right
  exactly as FDI requires — and mean |cx−0.5| rises monotonically 0.015→0.227 across positions
  1–8. 18,095 annotations, 634 images.
- **The `disease/` ground-truth parsing is verified.** Label format is
  `<finding_id>-<finding_name_tr>-<FDI>` (e.g. `1-çürük-26` = caries, tooth 26). Across 250
  files and **1,600 shapes there are 0 regex failures**; group(3) yields exactly **32 distinct
  values, every one a valid FDI code**, all 32 present; group(1) correlates perfectly with the
  finding names (747 `1` ↔ 747 `çürük`), confirming it is the finding id and not the tooth.
- **Split hygiene is clean:** 538 train / 96 val images, **0 image overlap, 0 ann_id overlap,
  0 jittered rows in val**. Augmentation never touches the validation split.
- **Class balance does not require weighting.** Train imbalance is **1.83×** (588–1074 per FDI
  class) and quadrants are near-perfectly balanced at **1.01×** (7652–7744). Unweighted
  cross-entropy is the right choice below roughly 10×, and macro-F1 is already reported
  alongside accuracy. Val carries all 32 classes, min support 47.
- **Train and inference preprocessing are bit-identical**, verified on a real crop rather than
  by reading: the redundant `Resize((224,224))` on an already-224 image is a true no-op
  (max|diff| 0.0), and PIL-RGB equals cv2 `BGR2RGB` exactly. Channels are identical, confirming
  these are greyscale radiographs stored as 3-channel.
- **The >32-detection edge case is exercised and handled.** Two images exceed the 32 available
  FDI codes (36 and 34 detections); Hungarian assignment still emitted **0 duplicates** and left
  **0 detected GT teeth unassigned**.

- **REFUTED — "laterality is not recoverable from crop pixels".** This claim appeared in five
  places and was the stated justification for the architecture. Input ablation on the 2,729-crop
  val split (`scripts/eval/ablate_head_inputs.py`), reporting quadrant decomposed into jaw and
  **side** (side *is* laterality; a quadrant score hides it behind the much easier jaw split):

  | Condition | jaw | **side (laterality)** | position | FDI exact |
  |---|---|---|---|---|
  | full | 99.9% | **99.5%** | 92.1% | 91.6% |
  | positional features → dataset mean | 99.9% | **96.3%** | 92.1% | 88.8% |
  | positional features shuffled (wrong) | 99.8% | **76.6%** | 92.2% | 70.8% |

  With neutral positional input **the image alone recovers laterality at 96.3%**, not the 50%
  of guessing. A 1.5× expanded crop carries its neighbours and the local arch curvature, so
  mirrored teeth sit in mirrored contexts. **The honest contribution of the positional features
  is +3.2 points of laterality and +2.8 FDI exact** — real, cheap, worth keeping, but a
  refinement rather than the load-bearing element. Corrected in all five places.
- **What survives unchanged:** the image *is* load-bearing for the **position digit** (92.1%,
  and it collapses without the image), which is exactly where rank-order geometry fails — so the
  reason the head beats positional assignment is intact. **Excluding horizontal flip also stands
  on its own**: flipping inverts the *label*, which is a fact about FDI, not about what the model
  can recover.
- **New risk, measured:** supplying *wrong* positional features costs **22.9 points of
  laterality** — far more than removing them. The head **over-trusts this input**. That compounds
  the half-applied jitter defect (2026-08-24a): training paired clean ground-truth coordinates
  with shifted crops, while inference supplies noisy **detector** coordinates. This is now the
  strongest argument for the v1.1 retrain, and it is a *quantified* one.
- **Caveat on the fourth ablation condition:** a blanked image is far out of distribution, so
  `no_image` measures "model fed an impossible input", not "positional features alone". Its jaw
  score of 47.5% is *below* the 50% chance line, which is the tell — real `cy` separates jaws
  trivially. Conclusions above rest only on the three in-distribution conditions.
- **Source:** `scripts/eval/ablate_head_inputs.py`, `outputs/enumeration_head/input_ablation.json`,
  `models/08_fdi_enumeration_head/enumeration_manifest.csv`, DENTEX
  `train_quadrant_enumeration.json`, `DENTEX/disease/label/*.json`.
- **Follow-ups:** none blocking — the implementation is correct and Stage 2 stands. The v1.1
  retrain now has a measured justification rather than a theoretical one, but **R4 still comes
  first**.

## 2026-08-24d — Fourth FDI pass: coordinate frames, box geometry, test quality, BatchNorm

- **What was done:** A fourth pass over ground the previous three did not touch — the ground-truth
  coordinate frame, box rotation geometry at pixel level, whether the test suite is substantive,
  and inference-time model state. **No defect found in the FDI logic.** One undocumented
  threshold was documented, and one sub-pixel convention question was resolved as negligible.

- **The `disease/` ground truth really is in the upright frame** the evaluation assumes — an
  assumption made everywhere and never tested. Across 250 images and **1,600 shapes, 0 points
  fall outside the image bounds** in either dimension; every image is wide (W>H), i.e. an
  upright panoramic; x/W spans [0.103, 0.874] and y/H [0.134, 0.887]. 138 distinct image sizes,
  all handled by normalisation. A rotated-frame ground truth would have produced mass
  out-of-bounds here; it does not.
- **`unrot_box` is correct at pixel level, not just algebraically.** 2,400 synthetic boxes across
  four image sizes round-tripped with **max corner error 0**. A pixel-level test — paint a patch,
  rotate the actual image, recover the patch's bounding box, un-rotate it — reproduces the
  original box **exactly, in both directions**. `detect_upright` takes `h, w` from the *upright*
  image before rotating, which is the one place a post-rotation dimension would silently corrupt
  every box.
- **A convention question, resolved as negligible.** `unrot_point` uses `(W-1-y)`, a closed
  pixel-index convention, while YOLO emits continuous `xyxy` where `x2` is the right edge. Worst
  case that is a **1-pixel** shift: ~1% of IoU on a 100px tooth box against a 0.30 matching
  threshold, and ~4e-4 in a normalised positional feature. Orders of magnitude below any
  decision threshold. Recorded rather than silently ignored.
- **The `_QUADRANT` table in `fdi_assignment.py` is correct** — (upper, image-left)→1,
  (upper, image-right)→2, (lower, image-right)→3, (lower, image-left)→4 — and matches the DENTEX
  spatial signature measured independently in 2026-08-24c.

- **The test suite is substantive, not decorative** — checked because "46/46 pass" is worthless
  if the tests are vacuous:
  - `test_fdi_converter.py` writes its 32-entry expected table **independently of the module
    under test**, and says why in its docstring: the previous version asserted
    `universal_to_fdi("32") == 34`, which was what the *buggy table* returned. *"A test written
    against the implementation cannot detect a wrong implementation."*
  - `test_orientation.py` validates against **real `cv2.rotate` output on 400 random pixels** per
    direction — it would have caught the CW/CCW bug.
  - `test_fdi_assignment.py` tests behaviour, not plumbing: a mid-arch tooth is deleted and the
    module must **flag** the gap rather than silently renumber — the exact failure mode Stage 2
    exists to address.

- **Inference-time model state is correct, and this one matters.** ResNet18 contains BatchNorm,
  so a model left in train mode would compute statistics **from the inference batch**, making
  every tooth's prediction depend on which other teeth happened to be in the image.
  - `load_head` returns `.eval()`; verified.
  - **Batch-invariance measured**: the same 12 samples fed as one batch, as chunks of (1,5,2,4),
    and one at a time agree to **~7e-6** — float32 accumulation noise, not batch-statistic
    leakage.
  - Counter-demonstration: the same model in train mode shifts outputs by **1.518**. The check
    discriminates, and the code passes it.
  - Train and inference architectures are **identical**: 128 tensors, all keys and shapes match,
    `load_state_dict(strict=True)` succeeds, output shapes (N,4) and (N,8), forward deterministic.

- **Fixed: `0.30` was a bare magic number.** The `low_confidence` threshold had no stated
  rationale, while the neighbouring IoU thresholds in `validate_fdi_assignment.py` explicitly
  document being chosen a priori "**NOT** by sweeping this threshold against this evaluation
  set". Since the flagged/unflagged breakdown **is reported in the results**, an undocumented
  threshold there invites exactly the question the IoU thresholds pre-empt. Now
  `LOW_CONFIDENCE = 0.30`, documented as a fixed heuristic under the same discipline.
  - Discrimination **at the fixed value** (a post-hoc measurement, explicitly *not* a
    justification for the number): flags 15.2% of assignments, which are **50.5% exact against
    72.7%** for the rest — a **22.2 point** separation. Confidence is otherwise highly skewed,
    median 0.991.
  - The refactor was verified behaviour-preserving: re-running the evaluation produced artefacts
    **byte-identical** to the pre-refactor run.
- **Source:** `outputs/stage2_postrefactor/` (byte-identical to `outputs/stage2_reverify/`),
  `src/orientation.py`, `src/fdi_head_inference.py`, `tests/`, `DENTEX/disease/label/*.json`.
- **Follow-ups:** none. Four passes have found no defect in the FDI logic itself; the defects
  found across them were in the *documentation of it* (the ceiling figure, the laterality
  rationale, stale disjointness claims) and one half-applied augmentation. **R4 remains next.**

## 2026-08-24e — The "over-trust" concern from 24c is withdrawn; it does not survive measurement

- **What was done:** Tested the claim this log made yesterday in 2026-08-24c — that the head
  "over-trusts" its positional input and that this constitutes a real train/inference gap. **It
  does not. The claim is withdrawn.** It was an over-reading of an ablation, by the author of
  that ablation, and is corrected here in the same spirit as the other corrections in this file.
- **What 24c actually measured:** shuffling positional features (giving a tooth *another
  tooth's* coordinates) costs 22.9 points of laterality. True, and reproduced. But a shuffle
  **teleports** the coordinate — often across the midline — and crossing the midline is exactly
  what inverts laterality. It is not a model of detector-box error.
- **What detector-box error actually looks like — graded perturbation, val split, 2,729 crops:**
  centres displaced by ±ε of box size and box sizes scaled by (1±ε), the same parameterisation
  as the training jitter:

  | Perturbation | side | position | FDI exact |
  |---|---|---|---|
  | none (baseline) | 99.5% | 92.1% | 91.6% |
  | ±15% of box (= training jitter) | 99.5% | 92.1% | **91.6%** |
  | ±25% of box | 99.5% | 92.1% | **91.6%** |
  | ±50% of box | 99.4% | 92.2% | **91.6%** |
  | ±100% of box | 99.3% | 92.2% | **91.5%** |

  **Displacing every box by its own full width costs 0.1 points of FDI exact.** At the realistic
  ±15% the numbers do not move at all.
- **The geometry explains it, so this is not a fluke of one split.** A tooth occupies **4.5% of
  image width**, so a full-box displacement moves the normalised centre by at most **0.045**,
  while the median tooth sits **0.091** from the midline. Only **17.3%** of teeth are close
  enough to the midline for a ±100% shift to cross it, and just **1.8%** at ±15% — and those are
  central incisors, where the confusion is 11↔21, one code. A shuffle, by contrast, redraws cx
  from the full [0.205, 0.840] span.
- **Consequences, stated plainly:**
  1. **The head is robust to detector-box error.** The 46.5% end-to-end figure is not being
     depressed by feature noise.
  2. **The jitter defect (2026-08-24a) is even less consequential than that entry allowed.** It
     remains a correctness fix worth keeping in the builder, but it should **not** be presented
     as a performance opportunity.
  3. **v1.1 has no measured performance justification.** 24c called this "the strongest and only
     quantified argument" for a retrain; that argument is gone. Retrain if the crops are rebuilt
     for another reason, not for this.
  4. **The shuffle result keeps a legitimate use** — it is an *attribution* diagnostic showing
     the head genuinely reads the coordinate rather than ignoring it. It is not evidence of
     fragility, and must not be cited as such.
- **Method note — why the earlier reading was wrong.** The shuffle ablation answers "does the
  model use this input?" It does **not** answer "is the model robust to realistic error in this
  input?", because the perturbation it applies is not drawn from the error distribution the
  pipeline produces. Those are different questions and they need different experiments. Choosing
  a perturbation because it is easy to implement, then interpreting it as a robustness result,
  is the error made in 24c.
- **Corrected in:** `scripts/dentex/train_enumeration_head.py`, `src/README.md`,
  `docs/results/model_metrics.md`, `docs/results/PAPER_MATERIAL.md` §8.10.
- **Source:** graded-perturbation run over `data/dentex/enumeration_v1` val split against
  `models/08_fdi_enumeration_head/enumeration_head_best.pth`.
- **Follow-ups:** none. **R4 is unblocked and is next.** All five trained checkpoints load
  cleanly and R4 is inference-only — no GPU rental required.

## 2026-08-24f — R4 built: the pipeline composes end to end, and immediately exposes two OOD failures

- **What was done:** Built the integration layer the project has never had — `src/classifiers.py`
  (Stages 3–4) and a rewritten `scripts/run_inference.py` (Stages 1–6), replacing a 38-line
  placeholder. **One OPG in, one per-tooth JSON report out.** This is paper claim **C3**, and
  composing the four stages produced a result on the first run that isolated testing never could.

- **The crop contract was the main correctness risk, and it is now explicit.** The four
  classifiers were trained in three different notebooks and **do not share a crop convention**.
  Crossing them yields the same tensor shape, plausible values, confident wrong output, and no
  error anywhere. Each was read out of the artefact that defines it, never inferred:
  | Branch | Expansion | Why |
  |---|---|---|
  | caries gate + severity | **1.0× tight** | caries is a crown-surface finding; bone is distractor |
  | bone-loss binary + severity | **1.5×W, 2.0×H** | read at the alveolar crest; teeth are ~3× taller than wide |
  | enumeration head (Stage 2) | 1.5×W, 1.5×H | a *third* convention, untouched here |
  Verified numerically: the tight crop reproduces the detector box exactly (100×300), the
  bone-loss crop is exactly 150×600, and **the two branches provably do not produce the same
  crop** — a regression test now asserts that.
- **Class order likewise read, not assumed.** The two caries checkpoints carry their own
  `class_to_idx` and the pipeline **asserts** it at load; a swapped checkpoint aborts rather than
  inverting every prediction. `{caries:0, no_caries:1}` and `{caries:0, deep_caries:1}`.
  Bone-loss severity is `['Mild','Moderate','Severe']` from the label-*generating* code in
  `notebooks/bone_loss/04_*.ipynb` cell 6. The bone-loss binary checkpoint has no `class_to_idx`;
  its order is **recovered arithmetically** from the recorded FocalLoss α=[0.642, 2.258] against
  counts 2500/711 — N/(K·nᵢ) gives 0.642 and 2.258 to three decimals, so 0=normal, 1=diseased.
  That is an inference, and the report metadata says so.

- **FIRST END-TO-END RESULT — 12 leak-free DENTEX images, 299 detected teeth:**

  | | Pipeline | Reference |
  |---|---|---|
  | caries-positive | **254 (84.9%)** | 35 annotated carious teeth |
  | bone-loss-positive | **2 (0.7%)** | — |
  | duplicate FDI codes | **0** | across all 299 |

- **The two disease branches fail in OPPOSITE directions, and both are out-of-distribution.**
  This is the substantive finding:
  1. **The caries gate over-calls ~7×.** Its negative class is Impacted + Periapical Lesion and
     contains **no healthy teeth**, while the pipeline feeds it every tooth the detector finds.
     An **84.9% caries rate is not clinically plausible**, which is the point: the defect was
     known in principle (2026-08-21j) and is now *measured in situ*.
  2. **The bone-loss branch is close to inert**, firing on 0.7% of teeth with 0.93–0.999
     confidence in `normal`. It was trained on **Tufts** and is applied here to **DENTEX** —
     cross-dataset domain shift. A `normal` bone-loss field in a report on non-Tufts data is
     therefore weak evidence, **not a negative finding**.
  **Neither is visible when a stage is evaluated on its own curated crops.** That is the argument
  for C3: composition is where these appear.
- **What worked:** Stage 1→2 behaved exactly as measured in isolation. **0 duplicate FDI codes
  across 299 teeth** — the Hungarian constraint holds at scale. On `test_0`, 3 of 5 annotated
  teeth were matched at mean IoU 0.540 and **2 of 3 FDI codes were correct** (36 ✓, 48 ✓, 45→44 ✗),
  consistent with the 67.0% recall / 69.4% of-detected figures from 2026-08-22j.
- **Both limitations are written into every report**, quantified, under `report["limitations"]`,
  alongside `stage1_detector_recall` and `stage2_fdi_exact_end_to_end`. Every caries prediction —
  positive *and* negative — carries `gate_out_of_distribution`. A report cannot be quoted as more
  than it is.
- **Assessability gating:** a tooth is reported assessable only if Stage 2 is confident *which*
  tooth it is, reusing `LOW_CONFIDENCE = 0.30` rather than introducing a second threshold —
  findings attached to a misnumbered tooth are worse than no findings.
- **Guards:** stage outputs are fused positionally, so the report builder **asserts** all four
  per-stage lists match the box count (a filtered list would otherwise attach one tooth's
  findings to another). Zero detections produce a valid empty report. 14 new tests, **60/60 pass**.
- **Source:** `scripts/run_inference.py`, `src/classifiers.py`, `tests/test_classifiers.py`,
  `outputs/r4_demo/` (report + overlay), `outputs/r4_batch/` (12-image run).
- **Follow-ups:** (a) the caries gate needs a real negative class before any pipeline caries
  number is meaningful — the detector-derived healthy-tooth idea in `transfer.md` §4 is now the
  blocking decision, not an optional one; (b) bone loss needs external validation before it can
  be claimed to work off-Tufts — this is what Ningxia is for; (c) Grad-CAM overlays for Stage 6
  are not built. **None of these block R5.**

## 2026-08-25a — Caries gate rebuilt with a real negative class: 84.9% → 19.1% in-pipeline

- **What was done:** Fixed the defect R4 exposed. The Phase-1 gate's `no_caries` class was
  Impacted + Periapical Lesion and contained **no healthy teeth**, so fed every detected tooth
  it called **84.9%** of them carious (2026-08-24f). Rebuilt the negative class from **5,366
  real healthy teeth**, retrained, and measured the difference through the assembled pipeline.

- **The data was recoverable after all — 2026-08-21m's conclusion was half right.** That entry
  correctly showed the enumeration↔disease filename join is invalid (different patients), then
  concluded healthy teeth are "NOT derivable from DENTEX". **The subsets share 260
  byte-identical images under DIFFERENT filenames** (`train_437.png` ≡ `train_1.png`). Joining
  on **MD5 of the image bytes** recovers them exactly; for those 260, both annotation sets
  describe the same pixels in the same coordinate frame.
- **The join is verified by a falsifiable test, not asserted.** For a shared image, a disease
  annotation and an enumeration annotation covering the same tooth must carry the same
  (quadrant, position): **1,255 agree / 22 disagree = 98.28%**, dimensions match **260/260**.
  Different patients would sit near chance (~3% over 32 classes) — this is exactly the check
  the filename join would have failed. `build_caries_phase1_v3.py` re-runs it every build and
  **aborts below 90%**.
- **Dataset `data/dentex/crops_v3_phase1/` — 6,616 crops, 260 images:**

  | | total | caries | no_caries |
  |---|---|---|---|
  | train | 4,750 | 723 (15.2%) | 4,027 |
  | val | 1,003 | 199 (19.8%) | 804 |
  | test | 863 | 127 (14.7%) | 736 |

  Negative class: **healthy 5,366**, impacted 179, periapical 22. The legacy gate had 762
  negatives, **zero healthy**. Labels by IoU: ≥0.50 takes the disease label, ≤0.10 is healthy,
  and the **856 teeth in between (11.5%) are EXCLUDED, not guessed** — a partially-overlapped
  tooth is precisely where "healthy" would be a guess. Splits inherited from `splits_v2.json`,
  so this test set is a subset of `phase1_legacy`'s. 0 images span splits; **0 leakage** against
  the 250-image eval set (checked per the standing rule).

- **RESULT — same 12 leak-free images, same detector, same boxes, same crops, only the gate
  differs** (`scripts/eval/compare_caries_gates.py`):

  | | caries+ | rate | over-call vs annotated |
  |---|---|---|---|
  | OLD (`phase1_legacy`) | 254 | **84.9%** | **7.3×** |
  | **NEW (v3)** | 57 | **19.1%** | **1.6×** |
  | annotated (floor) | 35 | 11.7% | — |

  The full pipeline with v3 as default reproduces this exactly: 57/299 = 19.1%.
- **Held-out test split (863 teeth, untouched during training):** caries P **0.40** / R 0.74 /
  F1 0.52; no_caries P 0.95 / R 0.81 / F1 0.87; accuracy 0.80, macro-F1 0.69.
  **Do not compare to the legacy gate's 0.81 / 0.77** — that was a different task (caries vs
  impacted/periapical, no healthy teeth in play), a different denominator.

- **IMPROVED, NOT SOLVED — report all four with any result:**
  1. **Precision is 0.40.** Six of ten positives are still wrong. Unusable → plausible, not
     reliable.
  2. **The annotated count is a FLOOR**, not a complete label. So 1.6× is an *upper bound* on
     how good v3 looks, and the comparison cannot separate true false-positives from
     unannotated real caries.
  3. **Presumed-negative assumption.** A tooth with no annotation is treated as healthy —
     absence of evidence. Any missed lesion is a false negative in training *and* in that 0.40.
     Unmeasurable inside DENTEX.
  4. **Tooth-type confound.** Caries concentrates in molars (44.3% at position 6 vs 1.5% at
     position 1). Tested for a shortcut: **aspect ratio alone scores 84.1%, exactly the
     majority baseline (−0.1% over it)** — not trivially exploitable, but per-position
     evaluation is the honest way to report this model.
- **Frozen** as `models/09_caries_gate_v3/`, tag `caries-gate-resnet18-v3.0`, sha256
  `8f4a99ba…`, with dataset meta, both reports and the comparison JSON. It is now the pipeline
  default; the legacy gate is retained (it is still the model behind the published
  `phase1_legacy` numbers) and reachable via `--caries-gate`.
- **Two incidental fixes:** `train_caries_cascade.py` selected **CUDA-or-CPU only** — the one
  script in the repo that never checked MPS, so on Apple silicon it silently trained several
  times slower than necessary. Fixed. It also hardcoded the Phase-2 tree relative to `--crops`;
  added `--phase2-crops` / `--phase2-variant` / `--phase1-only`, defaults unchanged, legacy path
  verified byte-for-byte identical.
- **The `gate_out_of_distribution` flag is renamed `caries_uncalibrated`** — the v3 gate *has*
  seen healthy teeth, so the old flag was no longer true. The new one states what is: precision
  0.40 and a presumed-negative training class.
- **Source:** `models/09_caries_gate_v3/run_summary.txt`,
  `outputs/caries_v3/gate_comparison.json`, `outputs/r4_batch_v3/`,
  `data/dentex/crops_v3_phase1/meta.json`. 60/60 tests pass.
- **Follow-ups:** (a) per-position evaluation of the gate, to size the tooth-type confound;
  (b) 260 images is one dataset and one scanner population — external validation is what
  Ningxia is for; (c) the Phase-2 severity head still trains on `phase1_legacy`-era crops and
  was not touched here.

## 2026-08-25b — T0.1 closed: the augmentation ablation ran, and the honest answer is "no signal at this seed"

- **What was done:** T0.1's augmentation A/B was written into a notebook on 15 Aug and never
  executed — confirmed again before running it (no `best_phase2_augmented*.pth` anywhere, no
  execution count on the relevant cells). **Re-scoped from its original target first**: T0.1
  was defined against `phase1_legacy`, the caries gate's now-superseded negative class. Running
  an augmentation ablation on a model nobody uses would answer the wrong question, so both arms
  ran on `crops_v3_phase1` — the tree that actually ships. Verified before launch, not assumed:
  script unchanged since arm B's 25 Aug run (`git diff --stat` clean), dataset counts identical
  (723/4027 train, matching arm B exactly), and a live check during arm A's run confirmed
  identical printed class weights `[3.2849, 0.5898]` — proof both arms trained on the same data,
  differing only in the one ablated variable.

- **Results, both arms, same data/weights/epochs/schedule, only the transform differs:**

  | | val macro-F1 | test macro-F1 | test caries P/R/F1 | test no_caries P/R/F1 |
  |---|---|---|---|---|
  | Arm A (no augmentation) | 0.7210 | **0.7212** | 0.47 / 0.62 / 0.54 | 0.93 / 0.88 / 0.91 |
  | Arm B (augmented) | **0.7350** | 0.6948 | 0.40 / 0.74 / 0.52 | 0.95 / 0.81 / 0.87 |

  Arm B wins on val (the selection metric, T0.3); arm A scores higher on test. A/B gap:
  0.014 (val), 0.026 (test).

- **That gap is not a finding — it is smaller than the noise floor, checked explicitly rather
  than eyeballed.** Extracted every epoch's val macro-F1 from both training logs (properly
  anchored regex, not conflated with the adjacent accuracy number — an earlier extraction
  attempt accidentally matched both): **arm A swings 0.4486–0.7210 across its own 15 epochs
  (range 0.272); arm B swings 0.4618–0.7350 (range 0.273).** Both arms individually vary by
  ~0.27 run over run within themselves. The between-arm gap (0.014–0.026) is roughly **10–20×
  smaller** than that. A single-seed A/B comparison this size cannot support a claim that
  augmentation helps or hurts here — it would need multiple seeds per arm to separate signal
  from the training process's own noise, which is out of scope for a Tier-0 close-out.
- **T0.1's honest answer, therefore: measured, not modelled as a clean win.** Report both rows
  in the table above. Do not claim augmentation improves or degrades the gate from this result.
- **The frozen pipeline default (`caries-gate-resnet18-v3.0`) is unchanged**, and deliberately
  not re-selected now that both arms exist. It was frozen from arm B before arm A was run; val
  macro-F1 — the pre-registered selection metric — still favours B, narrowly. Swapping to arm A
  *because it scored higher on test* would be exactly the test-set-tuning this project's
  discipline exists to prevent (same class of violation as the `LOW_CONFIDENCE` threshold rule,
  2026-08-24d, and the Ningxia lock in `MASTER_PLAN_2026H2.md` §4.3).
- **A real, minor documentation gap found in passing**: `results.json` never receives
  `epoch_log` when `--phase1-only` is set — `train_caries_cascade.py` returns at line ~312,
  before the line that attaches it. The per-epoch curve for both phase1-only arms exists only
  in the plain-text stdout logs (`outputs/caries_v3/train.log`, `train_arm_a.log`), not in the
  JSON artefact T0.4 promises. Not fixed here — logging both stdout files as the source of
  record is sufficient for this entry; worth a one-line fix if `--phase1-only` runs become
  routine.
- **Source:** `outputs/caries_v3/run/arm_a/` (`results.json`, `phase1_gate_report.txt`),
  `outputs/caries_v3/run/arm_b/` (same, from 25 Aug), `outputs/caries_v3/train_arm_a.log`,
  `outputs/caries_v3/train.log`.
- **Follow-ups:** none blocking. T0.1 is closed — both arms exist, reported honestly, and the
  frozen model is unchanged. If a confident augmentation verdict is ever wanted, it needs
  multiple seeds, not a rerun of this same ablation.

## 2026-08-25c — Lesion-localisation evaluator built and run: 42.6% agreement on DENTEX, no GPU needed

- **What was done:** Built `scripts/eval/lesion_localization.py` — no code for this existed
  anywhere before today. `MASTER_PLAN_2026H2.md` §4.3.4 promotes it to the **primary external
  number** for C2, precisely because it needs no negative class at all (immune to Ningxia's
  missing-healthy-controls problem, §4.4) and doubles as the T1.5 XAI metric. Built and
  validated against DENTEX first, deliberately, so Ningxia later is "point the script at a
  different folder," not new code under deadline pressure. Pure inference + geometry — no
  training, no GPU rental, runs on this machine's MPS.

- **Ground-truth scoping — re-verified directly from source, not from memory**, since getting
  this wrong would have silently corrupted the whole metric. `disease/label/*.json` carries 8
  Turkish finding types; re-extracted all 8 with counts (matches the parse
  `compare_caries_gates.py` already relies on): çürük 747, küretaj 265, gömülü 221, kanal 161,
  saglam 91, lezyon 75, çekim 29, kırık 11. Only **çürük** (caries) maps to what the caries
  branch predicts — küretaj/kanal are procedure markers (a treated tooth, not active disease);
  gömülü/lezyon/kırık are different clinical entities (position anomaly, periapical infection,
  fracture) no branch of this pipeline targets. Using only çürük means every unmatched lesion
  is unambiguously something the caries branch should have caught.

- **Matching reused, not reimplemented.** `iou()` and `match_gt_to_detections()` (greedy IoU
  with centroid-containment fallback — proven on exactly this problem, a small lesion polygon
  inside a much larger tooth box) imported directly from `validate_fdi_assignment.py`, along
  with `LABEL_RE` for GT parsing. `min_iou=0.30` inherited unchanged, not re-tuned.

- **Two real bugs found and fixed during review, before any run:**
  1. A first cut hand-split labels on `"-"` rather than reusing the already-validated
     `LABEL_RE`. No observed failure on current data (the 8 Turkish names contain no hyphens),
     but a second, independently-written parser is exactly the kind of thing that quietly
     drifts from the original — switched to the shared regex.
  2. A per-image diagnostic field (`unmatched_positive_findings`) was tautological by
     construction — it would only ever contain "caries"/"deep_caries", the exact values used
     to build the list being filtered in the first place. Replaced with unmatched positives'
     `gate_confidence` values, which actually discriminate (a cluster of high-confidence
     unmatched positives reads differently than low-confidence ones).

- **Verified against a hand-derived expectation before trusting any aggregate.** Read
  `test_0.json` directly: 5 shapes, only 3 are çürük (`26`, `48`, `45`). `load_lesion_gt`
  returned exactly those 3, correct FDI codes. Ran the full pipeline on that one image:
  `flag_counts: {'caries_uncalibrated': 18}` — independently confirms 18 teeth were detected,
  matching this exact image's detection count from earlier in this session (unrelated code
  path, unprompted corroboration). 1/3 lesions matched, consistent with a separate
  earlier finding that this image's detector run misses GT teeth 38 and 26 entirely (so lesion
  `26` could not possibly be matched — no detection exists there to match it to).

- **Full run — 164 leak-free images, pipeline default (`caries-gate-resnet18-v3.0`):**

  | | |
  |---|---|
  | Images with ≥1 çürük lesion | 148 / 164 |
  | Lesions (çürük polygons) | 479 |
  | **Lesion-localisation agreement** | **204/479 = 42.6%** |
  | Predicted-positive teeth | 772 |
  | — matched to a lesion (diagnostic, not precision) | 204 (26.4%) |

- **Arithmetic self-consistency checked exhaustively, not spot-checked**: summed all 148
  per-image entries against every top-level aggregate — 4/4 exact matches. 0 images with an
  impossible value (matched count exceeding lesion count, or unmatched-positive count
  exceeding positive count).

- **Sanity-checked against the two known stage recalls**, order-of-magnitude only: detector
  recall 0.670 (2026-08-22j) × caries test recall 0.74 (arm B, 2026-08-25b) = naive compound
  0.496, against the measured 42.6%. Different population and method — this is not a formal
  derivation — but the right order of magnitude for two compounding ~65–75% stages, which is
  reassuring rather than surprising.

- **What this number does NOT mean.** An unmatched predicted-positive tooth is not a confirmed
  false positive: `disease/` annotates only teeth carrying some finding (~6 of ~30 per image),
  so most teeth in any image are simply unannotated, not verified healthy. The
  predicted-positive match rate is reported explicitly as a diagnostic for this reason.

- **Also fixed in passing**: `PAPER_MATERIAL.md` §8.4 was titled "The pipeline has never been
  run end to end" and stated "any claim of an integrated system would be unsupported by this
  repo" — both false since R4 (2026-08-24f). Corrected with a dated note, original text kept
  intact per this project's never-rewrite-a-past-claim convention (same pattern as every prior
  correction this session).

- **Source:** `scripts/eval/lesion_localization.py`,
  `outputs/lesion_localization/full/lesion_localization.json`,
  `outputs/lesion_localization/n1_check/` (the single-image verification run).
- **Follow-ups:** Ningxia needs its own `load_lesion_gt` sibling for raster masks once the
  drive is connected and a real mask file can be inspected — deliberately not guessed here.

## 2026-08-25d — C2: first external validation. Ningxia, 4 hospitals, zero leakage

- **What was done:** The Ningxia drive was connected. Copied, leakage-checked, and evaluated —
  the first time this pipeline has been measured on institutions it has never seen. This is
  **contribution C2**, and per `MASTER_PLAN_2026H2.md` §4.2 Ningxia is now **touched**: locked
  external test data, evaluated once, no tuning of any kind against it.

- **Copy discipline.** Copied **test splits only** (2.4 GB) to `~/Downloads/Capstone/ningxia_local/`,
  deliberately leaving the 11.2 GB train split on the pen drive. We may never legitimately train
  on Ningxia, so not having it locally makes that *physically impossible* rather than merely
  forbidden. Original untouched (read-only rsync). Verified: all 12 split counts match source
  exactly, 30/30 random files byte-identical, manifest + README byte-identical, train absent.

- **LEAKAGE: ZERO**, checked against each corpus **separately** per the standing rule from
  2026-08-22j:

  | Corpus | n | Overlap with 2,912 unique Ningxia test hashes |
  |---|---|---|
  | Tufts radiographs (detector train) | 1,000 | **0** |
  | DENTEX `disease/` (Stage-2 eval) | 250 | **0** |
  | DENTEX `quadrant_enumeration` (FDI head train) | 634 | **0** |
  | DENTEX `quadrant-enumeration-disease` | 705 | **0** |
  | DENTEX `quadrant` | 693 | **0** |

  Also: **no image spans two centre splits** (so stratification is safe); 549 images appear
  under more than one *disease category* — multi-condition patients with a separate mask each,
  which is why results are never pooled across categories; and one genuine intra-dataset
  duplicate (`impacted_teeth/test2/45.png` ≡ `178.png`), harmless as we have no impaction branch.

- **RESULT — caries, focal-lesion centroid containment, stratified:**

  | Split | Centre | Lesions | Covered | Strict (1:1) |
  |---|---|---|---|---|
  | test1 | cross-centre | 316 | **26.6%** | 23.7% |
  | test2 | same-centre-as-Ningxia-train | 349 | **43.3%** | 36.4% |
  | test3 | cross-centre | 162 | **37.0%** | 29.0% |
  | test4 | cross-centre | 186 | **22.6%** | 18.8% |
  | *(pooled, for scale only)* | | 1,013 | 33.3% | 28.0% |

  Against DENTEX's 42.6% (2026-08-25c), Ningxia sits **at or below** the internal number across
  four independent hospitals — which is what honest external validation looks like.
  **Interpretive caution:** "same-centre-as-train" refers to **Ningxia's own** train split. We
  never trained on any Ningxia data, so all four splits are equally external *to us*; the
  spread reflects real inter-centre scanner/population variation, not proximity to our training
  set. Do not describe test2 as "in-domain."

- **RESULT — periodontitis, affected-tooth sensitivity** (of teeth inside the expert-marked
  region, how many were flagged): test1 **3.7%** (121/3,274), test2 **0.8%** (17/2,072),
  test3 **1.5%** (5/339), test4 **5.4%** (29/537); pooled 2.8% (172/6,222).
  With Tufts in-domain at 0.92 macro-F1, DENTEX at 0.7% firing, and Ningxia at 0.8–5.4%, the
  bone-loss branch's **domain-shift failure is now measured on two independent external
  datasets**, not inferred from one.

- **A WITHDRAWN NUMBER, AND THE REASON IT MATTERS.** The first run applied centroid containment
  to *both* categories and reported periodontitis at 0.7–4.0%. **Those figures were a
  measurement artefact and are withdrawn.** Measured on real masks: caries = 2.5 blobs/image,
  median 731 px (focal spots); periodontitis = 1.0 blob/image, median **365,680 px** — a single
  continuous band spanning the whole alveolar ridge, ~8% of the radiograph, visually confirmed
  (`outputs/ningxia_check/periodontitis_mask.jpg`). **The centroid of such a band lands in the
  gap between teeth, inside no tooth box — so that metric scores ~0% by construction regardless
  of model quality.** Reporting it as "the bone-loss branch fails externally" would have been a
  true-sounding conclusion drawn from a broken instrument. Replaced with affected-tooth
  sensitivity (≥50% of a tooth box inside the region ⇒ affected). The corrected conclusion is
  *similar in magnitude but now actually measures something.*

- **A SECOND ASSUMPTION THAT DIDN'T TRANSFER, caught before it ran.** `lesion_localization.py`'s
  docstring claimed only its GT loader would need a Ningxia sibling and "nothing else in this
  file assumes the DENTEX format." **Wrong** — the *matching criterion* doesn't transfer either.
  Ningxia caries lesions are 89–3,090 px against ~25,000 px tooth boxes, so a lesion sitting
  entirely inside the correct tooth scores IoU 0.015–0.124 — **every one below the 0.30
  threshold**. Reusing the DENTEX matcher unchanged would have reported ~0% caries agreement
  too. That claim is corrected in `ningxia_external.py`'s docstring.

- **Verified, not assumed, before any measurement**: Ningxia is **upright — no rotation applied**
  (all sampled images landscape; visually confirmed across all four centres). Tufts needs 90°
  CCW; DENTEX and Ningxia do not. That is per-dataset and was checked, because getting it wrong
  for Tufts already cost this project a correction (2026-08-22d). Per-centre heterogeneity is
  real and visible: test1 2893×1480 single-channel with **burned-in annotation arrows/stars**,
  test2 2440×1292 3-channel, test3 2440×1280, test4 2424×1328 with a burned-in letter marker.
- **Arithmetic checked exhaustively**: per-image sums matched every aggregate (4/4 fields);
  covered ≥ strict and covered ≤ lesions everywhere; affected ≤ detected and flagged ≤ affected
  everywhere; affected-teeth/image 6.8–10.2 against 19.7–25.2 detected/image — anatomically
  plausible for a band covering roughly one arch.
- **Not computed, and cannot be:** specificity/AUC. Ningxia has no healthy controls
  (§4.3, corrected 18 Aug). Those come from Tufts. Negatives were **not** synthesised from the
  other disease categories, per the same section's explicit prohibition.
- **Source:** `scripts/eval/ningxia_external.py`,
  `outputs/ningxia_external/full/ningxia_external.json`, `outputs/ningxia_check/`.
- **Follow-ups:** image-level sensitivity for caries is ~96% and effectively saturated (the gate
  over-calls, and with ~22 teeth/image it almost always flags one) — report it as the weak
  metric §4.3.4 already predicted it would be, not as a strength.

## 2026-08-25e — Paper/review figure suite: 6 figures, all generated from saved artefacts

- **What was done:** Built `scripts/figures/make_paper_figures.py` for Phase III's "performance
  analysis using tables and graphs." Tables existed in abundance; **graphs covered only Stages
  1–2** (Ultralytics' own detector output and the enumeration head's training curves). Nothing
  depicted the results that actually carry the paper.
- **Design rule: the script runs no models and re-measures nothing.** Every value is read from a
  committed JSON artefact, so a figure cannot drift from the logged result — if a figure and
  `RESULTS_LOG` ever disagree, the figure is stale and regenerating fixes it. Each run prints
  the numbers it drew so they can be diffed against this log.
- **Figures produced** (`docs/results/figures/paper/`):
  1. **Error propagation (C3)** — 936 GT teeth → 627 detected (67.0%) → 435 correctly numbered
     (46.5%), with the −309 / −192 losses annotated. The flagship system-paper figure.
  2. **External validation (C2)** — DENTEX 42.6% against Ningxia's four hospitals
     (26.6 / 43.3 / 37.0 / 22.6%), with the "all four are equally external to us" caveat printed
     on the figure itself so it cannot be separated from the number.
  3. **Caries gate repair** — 84.9% → 19.1% against the 11.7% annotated floor.
  4. **Stage-2 ceiling** — positional vs head by quadrant completeness.
  5. **Bone-loss domain shift** — Tufts 0.923 macro-F1 → DENTEX 0.7% → Ningxia 0.8–5.4%. The
     honest negative result, on one chart.
  6. **Input ablation** — jaw / side / position across the three in-distribution conditions.
- **Caught during review:** the first render clipped every caption off the canvas edge. Added a
  wrapping helper that also computes the bottom margin to reserve, so a longer caption widens
  the margin instead of silently disappearing.
- **Source:** `scripts/figures/make_paper_figures.py`; inputs are
  `outputs/stage2_reverify/`, `outputs/ningxia_external/full/`,
  `outputs/lesion_localization/full/`, `outputs/caries_v3/gate_comparison.json`,
  `outputs/enumeration_head/input_ablation.json`.
- **Follow-ups:** Grad-CAM overlays remain unbuilt (design-only since the architecture doc).
  **Deployment is the one Phase III item with nothing at all behind it.**

## 2026-08-25f — Deployment: Streamlit app + Dockerfile, wrapping run_inference.py unchanged

- **What was done:** Closed Phase III's one checklist item with nothing behind it. Refactored
  `scripts/run_inference.py`'s `main()` into `load_models()` + `run_pipeline()` — reusable
  functions, not a second implementation — then built `app.py` (Streamlit: upload an OPG, see
  the report + overlay in a browser) and a `Dockerfile` on top of them.
- **Refactor verified behaviour-preserving, not assumed.** `verify.json` (an earlier saved
  report) turned out to be stale — from before the caries-gate rebuild — so comparing against
  it would have been invalid. Instead: stashed the refactor, ran the **last-committed** CLI
  fresh on the same image, unstashed, ran the refactored CLI on the same image, and diffed both
  reports byte-for-byte (ignoring only the `generated` timestamp). **Identical**, including the
  `image.path` string representation.
- **Every API call verified against the installed library, not memory.** Two real
  inconsistencies found by introspecting `streamlit==1.37.1`'s actual signatures before running
  anything: `st.image` takes `use_column_width`, **not** `use_container_width` (which is what
  `st.dataframe` uses — the two widgets disagree). Using the wrong one would have raised a
  `TypeError` at first render. Fixed before the app ever ran.
- **The whole upload-to-render code path exercised with real data**, not just "it compiles":
  built the exact bytes `st.file_uploader.getvalue()` would hand the app from a real DENTEX
  image, ran it through `np.frombuffer` → `cv2.imdecode` → `run_pipeline` → the table-building
  loop → `pd.DataFrame` → `draw_overlay` → the limitations-block string formatting → the JSON
  download payload. Every step succeeded; the overlay (977 KB) was rendered and visually
  confirmed correct — orange boxes on the two true caries findings, matching the same image's
  known CLI output exactly.
- **`streamlit` was missing from `requirements.txt`** — a fresh `pip install -r requirements.txt`
  would not have provided it, and the Dockerfile would have failed at container start, not at
  build time. Added.
- **A path bug in `.dockerignore`, caught before it shipped.** First draft blanket-excluded
  `data/`, but the Dockerfile had a `COPY data/dentex/disease_leaked_images.json ...` line —
  which would have failed the build (source not in context). Traced why that `COPY` line
  existed at all: grepped `app.py`, `run_inference.py` and all of `src/` for any `data/` read at
  inference time. **None exists** — that file is read only by the eval scripts. Removed the
  unneeded `COPY` line instead of patching around the `.dockerignore` conflict.
- **A documentation inaccuracy in the Dockerfile's own comment, caught by checking local state.**
  The two Drive-only checkpoints are gitignored, but **are already present on this machine's
  disk** (frozen here earlier this session). `COPY` is not git-aware, so a build run *here*
  would bake them in despite a comment claiming otherwise. Corrected to state both cases: baked
  in in this repo's exact working state, omitted on a true fresh clone, with the documented
  `docker run -v` mount harmless in the former case and required in the latter.
- **The exact `CMD` flag syntax verified by actually starting the process** (`--server.headless=true
  --server.address=0.0.0.0 --server.port=…`), not assumed valid — confirmed the server starts
  clean with no CLI parse error before trusting it inside the image.
- **Docker build itself NOT executed.** The daemon was not running; `open -a Docker` plus a
  120s wait did not bring it up (first-run setup this session cannot click through). Stated
  honestly rather than claiming a build that didn't happen. Compensating verification: every
  `COPY` source confirmed to exist on disk, every package the app imports confirmed present in
  `requirements.txt`, and the process command verified to start outside the container.
- **Not multi-tenant, not authenticated, not clinical** — a single-user local demo whose purpose
  is satisfying the Phase III deployment checklist item with something a reviewer can drive
  themselves, stated as such in `app.py`'s own docstring.
- **Source:** `app.py`, `Dockerfile`, `.dockerignore`, `scripts/run_inference.py` (refactored),
  `requirements.txt`.
- **Follow-ups:** run an actual `docker build` once the daemon is available, before relying on
  it for the review itself.

## 2026-08-25g — Verified: Tufts has unused per-tooth numbering; Ningxia structurally cannot train FDI

- **What was done:** User asked which dataset trained FDI mapping, and whether Ningxia or Tufts
  could be used for it. Checked both directly against real files rather than answering from
  memory — this project's whole discipline this session has been "verify, don't recall."

- **FDI enumeration head training source, reconfirmed:** DENTEX `quadrant_enumeration` only —
  634 images, 18,095 teeth (`scripts/dentex/build_enumeration_crops.py`). Unchanged, no new
  finding here, stated for completeness of the answer.

- **Ningxia CANNOT train FDI numbering — verified three ways, not inferred from the README:**
  1. `data/ningxia/manifest.csv` columns: `task, category, split, center_group, filename,
     img_path, mask_path` — no tooth-identity field of any kind.
  2. Searched `~/Downloads/Capstone/ningxia_local/` for any JSON or label file carrying
     per-tooth data — none exists.
  3. Opened a real segmentation mask directly: `cv2.imread(...).flatten()` unique values are
     `{0, 255}` — a binary disease/no-disease mask with no tooth identity encoded in it at all.
  Ningxia tells you *there is a lesion here*, never *this is tooth 26*. This is not a data-
  quality gap; it's what the dataset is for (disease segmentation, not tooth identification).

- **NEW FINDING — Tufts has usable per-tooth numbering, verified, never used for FDI training.**
  Opened `_repo_archive/datasets_workspace/Segmentation/teeth_bbox.json` directly:
  - **1,000 images**, every one carrying a `title` field per tooth object.
  - Titles are **Universal System numbers `'1'`–`'32'`**, plus **deciduous letters `A`–`T`** —
    confirmed the letter set matches `is_deciduous()` in `src/utils/fdi_converter.py` exactly.
  - **Mean 26.0 teeth/image** (min 0, max 48 — the max exceeding 32 confirms some images mix
    permanent and deciduous dentition, needing explicit handling, not exclusion by assumption).
  - Universal→FDI is already a tested, correct lookup table in this exact repo
    (`src/utils/fdi_converter.py`, `f8b31f8`, `tests/test_fdi_converter.py`) — no new mapping
    logic would be needed, only applying the existing one to this new source.
  - This is structurally the same shape of data that trained the DENTEX head (full-dentition,
    per-tooth positional labels), at **~1.6× the image count** DENTEX provided (1,000 vs 634).

- **This is a real opportunity, not a decision made.** Before touching it: needs the same
  rigor DENTEX's mapping got before use — spatial verification of the Universal→FDI conversion
  against real Tufts image coordinates (mirroring how DENTEX's quadrant/position mapping was
  spatially confirmed in 2026-08-24c), explicit handling of the deciduous-letter teeth (exclude
  or map separately — undecided), and a hand-verified dry run before any crop generation or
  training. None of that has been done. Flagged in `transfer.md` §4 as a pending decision, not
  started as work.

- **Source:** direct inspection of `_repo_archive/datasets_workspace/Segmentation/teeth_bbox.json`,
  `data/ningxia/manifest.csv`, and one real Ningxia mask file.
- **Follow-ups:** if pursued, this becomes a new `scripts/dentex/`-style builder
  (`scripts/tufts/build_enumeration_crops.py` or similar) mirroring
  `build_enumeration_crops.py`'s verify-before-use discipline exactly.

## 2026-08-25h — Tufts numbering is MIRRORED; FDI crop corpus built (42,755 crops, untrained)

Follow-on from 2026-08-25g, which found Tufts carries unused per-tooth numbering. That entry
called it "an opportunity, not a decision." This one acts on it — and the first thing the
verification found is that reading the labels the obvious way would have been actively harmful.

### The finding: Tufts titles are left-right mirrored, not plain Universal

Tufts `title` values look like Universal numbers ('1'–'32') and their **within-arch ordering is
correct**, but **which side of the patient each number denotes is inverted**. Tufts `"1"` is the
upper-**LEFT** third molar (FDI **28**), not the upper-right (18).

Anatomy cannot settle this — the dentition is bilaterally symmetric — so it was settled three
independent ways, no one of which was trusted alone:

1. **Lead side-marker.** The radiographs carry an `L` marker on the viewer's right, i.e. the
   standard convention (patient's left on the viewer's right). Tufts `"1"` falls on the viewer's
   right → the patient's LEFT. Standard Universal `1` is the patient's upper-RIGHT third molar.
2. **Independent model arbiter.** The Stage-2 head trains on DENTEX (FDI spatially verified:
   Q1 mean x=0.400 vs Q2 x=0.606) and has never seen Tufts. Over **1,188** IoU≥0.5-matched teeth
   in 60 Tufts images:

   | reading | exact FDI | quadrant |
   |---|---|---|
   | direct (`universal_to_fdi`) | 3.6% | **6.1%** |
   | mirrored | 55.8% | **91.7%** |

   Quadrant confusion is a clean anti-diagonal: q1→q2 290, q2→q1 278, q3→q4 267, q4→q3 254.
3. **Control — to prove the arbiter is not itself the mirrored component.** Same head, detector
   and matching code on **841** DENTEX teeth (60 images): **98.6% direct / 0.7% mirrored**, a
   clean diagonal. The head is correct; Tufts is mirrored.

**Nothing already trained is affected.** The detector is single-class and emits no numbering;
the bone-loss models use the Tufts title only as an identifier and a deciduous flag, never
deriving laterality from it (verified: zero mentions of FDI/quadrant/universal in
`notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`).

### Supporting geometry, verified rather than assumed

- Annotations are **portrait** (840×1615), matching `Radiographs_rotated/`; crops are cut from
  the **upright** 1615×840 image because Stage 2 reasons about upright anatomy. Transform is
  CCW's inverse `(x,y)→(W-1-y,x)` — re-derived here and confirmed pixelwise (`np.rot90(land,1)`
  mean|diff| 0.308 vs 31–73 for all five alternatives), independently matching `src/orientation.py`.
- **Independent check on the same transform:** converted boxes have median aspect **0.371**,
  against DENTEX's **0.347** and the ~0.35 documented in `src/crop_generator.py`. Left in
  portrait it would have been ~2.7.
- Anatomical sanity across all 1,000 images: the longest teeth are exactly positions 6/11/22/27
  (the canines, median length 182/180/162/161 px) and the shortest, most-often-absent are
  1/16/17/32 (third molars, present in only ~360/1000 images). Profile is bilaterally symmetric.

### Leakage and split discipline

- **Tufts is disjoint from DENTEX**: zero overlap by MD5 **and** by perceptual hash (dHash)
  against `quadrant_enumeration` (634) and `quadrant-enumeration-disease` (705).
- **New finding — `split_v1` has a train/test leak.** `590.JPG` (test) and `591.JPG` (train) are
  byte-identical, so `tooth-detector-a100-1024-v1.0` **trained on one of its own test images**
  (1 of 150). Recorded, not quietly corrected. A second pair, `1007`/`1008`, is train/train.
  The builder keeps one representative per group, preferring test > val > train.
- The frozen `split_v1` (700/150/150) is **reused verbatim**, not re-randomised, so images from
  the detector's test set cannot enter the head's train set.

### What was built

`scripts/tufts/build_enumeration_crops.py` → `data/tufts/enumeration_v1/` (gitignored):

| | teeth | crops |
|---|---|---|
| train | 17,629 | 35,248 (incl. ±15% jitter copies) |
| val | 3,725 | 3,721 |
| test | 3,789 | 3,786 |
| **total** | **25,143** | **42,755** |

All 32 FDI classes present in every split. Verified after writing: manifest↔disk match exactly
(42,755 both ways, 0 missing, 0 orphans), **0 source images straddle splits**, 0 label
inconsistencies, jitter confined to train. Excluded: 738 deciduous teeth (82 mixed-dentition
images; the head's output space is the 32 permanent codes), 65 degenerate 1×1 "tooth absent"
boxes, 2 duplicate images.

For scale: **25,201 usable permanent teeth vs DENTEX's 18,095** — 1.4×, from a different
continent and machine population.

### Code

- `src/utils/fdi_converter.tufts_title_to_fdi()` + `mirror_fdi_quadrant()`. The existing
  `universal_to_fdi` table is untouched; the module docstring's claim that "Tufts uses Universal
  numbering" is corrected in place, as it was actively misleading.
- `tests/test_fdi_converter.py`: **60 → 65 tests**, all passing. Expected values written out
  independently of the implementation, per that file's existing rule.
- `scripts/dentex/train_enumeration_head.py --data` now accepts several corpus roots
  (backwards compatible; single root behaves as before).

### NOT done — deliberately

**No model has been retrained.** Whether the combined corpus improves the head is an open
experiment, not a claim. Two things to watch: Tufts teeth occupy a smaller share of the frame
(median normalised height 0.177 vs DENTEX 0.231), a genuine covariate shift in the `cy`/`bh`
features the head consumes; and Tufts contributes 2.0× DENTEX's training rows, so naive
concatenation lets it dominate the loss. `verify_invariants.py` passes, including the frozen
weight hashes — the deployed head is byte-unchanged.

### 2026-08-25h (continued) — dataset-wide spatial verification, and a coordinate discrepancy

**The corrected mapping passes the identical spatial test DENTEX's mapping passed.** Computed
over all 25,143 unjittered Tufts crops, directly comparable to the DENTEX figures quoted in
`scripts/dentex/build_enumeration_crops.py`:

| check | Tufts (mirror-corrected) | DENTEX (reference) |
|---|---|---|
| Q1 mean cx (upper right) | **0.390** | 0.400 |
| Q2 mean cx (upper left) | **0.603** | 0.606 |
| Q4 mean cx / Q3 mean cx | 0.400 / 0.594 | — |
| mean \|cx−0.5\|, position 1→8 | **0.015 → 0.236** | 0.015 → 0.227 |

Q1/Q2 sit above Q4/Q3 (cy 0.473/0.469 vs 0.677/0.675); |cx−0.5| rises monotonically across all
eight positions. Patient-right-on-image-left now holds, matching DENTEX to within 0.01. Read
without the mirror correction, every one of these would invert.

**A coordinate-convention discrepancy, resolved.** `PAPER_MATERIAL.md` §8.8 lists the Tufts
bbox format as `[y1, x1, y2, x2]`, and `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`
implements exactly that against the **landscape** `Radiographs/` images. That reading is the
exact horizontal **mirror** of the one used here (portrait `[x1, y1, x2, y2]` + the CCW inverse).
The two cannot both be right. Measured against detector boxes over 1,022 teeth in 40 images:

| reading | mean IoU vs detector |
|---|---|
| portrait `[x1,y1,x2,y2]` + CCW inverse (used here) | **0.611** |
| landscape `[y1,x1,y2,x2]` (§8.8 / bone-loss notebook) | 0.489 |

Independent of that, drawing the raw numbers as `(x, y)` on the **portrait** image with zero
conversion places every box tightly on a tooth in a clean arch — which is only possible if the
coordinates are portrait-frame. `src/orientation.py` and the archived `convert_tufts_to_yolo.py`
(the detector's own converter, `IMG_WIDTH=840, IMG_HEIGHT=1615`) both use the portrait reading.

**The bone-loss models are NOT affected, and were not changed.** Verified rather than assumed:
the notebook cuts the image *and* the expert mask from the same landscape frame (masks are
840×1615 on disk) at the same coordinates, so each crop is paired with the label belonging to
the tooth actually inside it — the pair is self-consistent, merely located at the contralateral
tooth. The only identity-derived use of `tooth_id` there is `is_deciduous`, which is
mirror-invariant (A↔J … K↔T all remain letters). Nothing was retrained or edited; §8.8 is
corrected in place to say which frame each reading belongs to.

## 2026-08-25i — A/B: adding Tufts does NOT improve Stage 2 (p=0.343). The detector is the wall.

Direct test of the question left open by 2026-08-25h. Two heads trained from scratch, **same
seed (42), same 15 epochs, same batch 64, same lr 1e-3**, differing only in training corpus,
then evaluated like-for-like by `scripts/eval/validate_fdi_assignment.py --method head
--head-weights ...` on the **164 leak-free `DENTEX/disease/` images (936 GT teeth)**.

Pre-checked before training: the 250 eval images have **zero MD5 and zero perceptual-hash
overlap with Tufts**, so arm B introduces no new leakage into the evaluation. (This is the
check whose absence forced the 5.7-point withdrawal in 2026-08-22j.)

| run | training corpus | rows | FDI exact of detected | **end-to-end** | correct/936 |
|---|---|---|---|---|---|
| frozen `v1.0` | DENTEX | 30,732 | 69.38% | **46.47%** | 435 |
| **arm A** | DENTEX (identical config to frozen) | 30,732 | 67.94% | **45.51%** | 426 |
| **arm B** | DENTEX + Tufts | 65,980 | 69.54% | **46.58%** | 436 |

Detector recall is identical across all three (66.99%, 23.62 detections/image) — the detector
is untouched, so only the head varies. Duplicate FDI codes: 0 in every run.

### The result is null, and the control is why we know

**Arm B vs arm A: +10 teeth of 936 (+1.07pp). Paired McNemar on aligned rows: 50 discordant
in B's favour, 40 against, χ²=0.900, exact two-sided binomial p=0.343 — not significant.**

More telling than the p-value: **arm A and the frozen head share an identical configuration,
identical seed and identical data, and still differ by 9 teeth (0.96pp).** MPS float
nondeterminism plus DataLoader worker ordering put the run-to-run noise floor at ~1 point
end-to-end. Tufts' apparent +1.07pp is the same size as that noise. Arm B lands 1 tooth from
the frozen head (436 vs 435).

**Methodological consequence, worth stating in the paper: on this 936-tooth evaluation, any
Stage-2 end-to-end difference below ~1 point is indistinguishable from run-to-run variance.**
Single-run comparisons at that scale should not be reported as improvements.

### What this settles

The head was already at **91.3–91.6% FDI exact on ground-truth boxes**; end-to-end is 46.5%
because the detector finds only 67.0% of teeth and the one-to-one assignment cannot know which
third is missing. Adding 35,248 more training crops — a 2.1× increase, from a different
continent and machine population — moved nothing. **This converts "the detector is probably the
binding constraint" from a hypothesis into a measured result, and makes R1 unambiguously the
next thing to do.**

### Decisions

- **The frozen head is NOT replaced.** `fdi-enumeration-head-resnet18-v1.0` stays; its hash is
  unchanged and `verify_invariants.py` still passes. Neither arm wrote to `models/`.
- **The Tufts corpus is kept**, not deleted. It cost nothing to hold (gitignored, rebuildable),
  it is verified correct, and it remains a candidate for robustness work after R1 — where the
  interesting question is generalisation across machines, not in-domain accuracy.
- Arm B's own val figure (81.0% vs arm A's 91.3%) is **not** evidence of degradation: the two
  were computed on different val populations (A: 2,729 DENTEX crops; B: 6,450 DENTEX+Tufts).
  Not a like-for-like number and must not be quoted as one.

Artefacts (scratchpad, not committed — rebuild with the same commands): `ab_A/`, `ab_B/`,
`eval_A.json/`, `eval_B.json/`.

## 2026-08-25j — Tufts-only tested; the 25i "null result" was measured in one domain only

Follow-on from 2026-08-25i, prompted by the question "can we use Tufts numbering *instead of*
DENTEX?". Arm C (**Tufts only**, 35,248 crops) trained at seed 42 / 15 epochs / batch 64 /
lr 1e-3, identical to arms A and B. Then every head was evaluated in **both** directions.

**This entry corrects the framing of 2026-08-25i.** That entry concluded "adding Tufts does not
improve Stage 2." That is true *on the DENTEX evaluation* and remains true. But it was a
single-domain measurement, and it missed the effect entirely. Measured on Tufts, adding Tufts
is worth **+21.5 points**.

### The 2×2

| head | trained on | DENTEX 164 leak-free (end-to-end) | Tufts test, 3,786 crops (FDI exact) |
|---|---|---|---|
| frozen `v1.0` | DENTEX | 46.47% | 50.0% |
| **arm A** | DENTEX | 45.51% | 49.8% |
| **arm B** | DENTEX + Tufts | **46.58%** | **71.5%** |
| **arm C** | Tufts only | 37.39% | **71.8%** |

Detector recall identical (66.99%) in all end-to-end runs; 0 duplicate FDI codes everywhere.
Arm C's of-detected accuracy is 55.82% against arm A's 67.94%.

**The two columns are not comparable to each other** — DENTEX is end-to-end (detector boxes,
Hungarian one-to-one), Tufts is crop-level (GT boxes, plain argmax). Within each column the
four heads are directly comparable, which is what the question needs. The crop evaluator was
validated first by reproducing the frozen head's documented DENTEX-val numbers exactly
(99.4% / 92.1% / 91.6%) and it imports `ToothSet` from the trainer rather than reimplementing
preprocessing, so the eval path cannot drift from the training path. Tufts `test` is unseen by
every arm: A never saw Tufts at all, B and C trained on `split==train/val` only.

### Answers

1. **Can Tufts replace DENTEX? No.** Arm C loses **9.1 points** on the project's standard
   evaluation (37.39% vs the frozen 46.47%) — far outside the ~1-point noise floor established
   in 2026-08-25i. Dropping DENTEX would be a straight downgrade against how this pipeline is
   measured.
2. **It is symmetric domain shift, not a weak corpus.** Arm C is the *best* head on Tufts
   (71.8%). Each corpus trains a head that wins on its own domain and loses on the other. A
   DENTEX-trained head scores 50.0% on Tufts; a Tufts-trained head scores 37.4% on DENTEX.
3. **The real result is arm B.** Training on both matches DENTEX-only in-domain (46.58% vs
   46.47%, inside noise) *and* gains **+21.5 points** on Tufts (71.5% vs 50.0%) — within 0.3
   points of the Tufts-specialist. Combined training buys cross-machine robustness at no
   measurable in-domain cost.

### Why this matters more than the in-domain number

Generalisation is this project's central documented weakness — the bone-loss cascade scores
0.92 macro-F1 in-domain on Tufts and 0.7–5.4% on DENTEX/Ningxia (2026-08-25d), and C2 external
validation is a headline paper claim. A Stage-2 head that holds up across two machine
populations at zero in-domain cost speaks directly to that, and it is a real ablation rather
than an assertion.

**2026-08-25i's conclusion that "the detector is the binding constraint" still stands** — it
was measured in-domain and nothing here contradicts it. R1 remains the top item. What changes
is that "adding Tufts does nothing" was too strong: it does nothing *in-domain*, and a great
deal out-of-domain.

### Decisions

- **The frozen head is still NOT replaced** — no arm wrote to `models/`; hash unchanged,
  `verify_invariants.py` passes. Adopting arm B is now a *recommended* pending decision
  (`transfer.md` §4) rather than an open question, but it is a model-freeze call.
- Adoption, if taken, means: re-freeze arm B with a new tag, update the hash in
  `verify_invariants.py`, and re-state Stage-2 numbers in `model_metrics.md` with **both**
  domains, not just DENTEX.

### 2026-08-25j (continued) — arm B strictly dominates arm C; the choice is not a trade-off

Asked directly: prefer arm B (both corpora) or arm C (Tufts only)? Paired McNemar in **both**
domains settles it — arm C's apparent Tufts advantage is not real, and its DENTEX loss is.

| domain | arm B | arm C | net | McNemar |
|---|---|---|---|---|
| Tufts held-out test (3,786 crops) | 71.50% | 71.76% | C +10 crops | 351 vs 341, χ²=0.117, **p=0.732 — not significant** |
| DENTEX 164 leak-free (936 teeth) | **46.58%** | 37.39% | **B +86 teeth** | 44 vs 130, χ²=41.52, **p=4.7×10⁻¹¹ — significant** |

**Arm C is a dominated option.** It is not better than arm B anywhere measurable — its 0.26pp
Tufts edge is 10 crops out of 3,786 and sits inside the same noise the 2026-08-25i control
established — while being 9.2 points worse on the evaluation this project reports. There is no
deployment target for which C is the right choice: on Tufts-like images B ties it, on
DENTEX-like images B beats it decisively.

**The downstream cost of choosing C is not just a headline number.** Stages 5–6 emit a
*per-tooth* report, so an FDI error does not lose a finding — it attaches a real finding to the
wrong tooth. 86 additional mis-numbered teeth per 936 is 86 more caries/bone-loss findings
filed against the wrong tooth in the JSON and the overlay.

Recommendation stands: **adopt arm B, not arm C**; `transfer.md` §4.

## 2026-08-26a — Head v2.0 (DENTEX+Tufts) adopted; literature check on the mirror claim; a licence problem

### 1. Arm B adopted as `fdi-enumeration-head-resnet18-v2.0`

New directory `models/10_fdi_head_dentex_tufts_v2/`, sha256
`6c675fa014551a0f184cf87a52d55ea26d21f23ae84dd5df1f7efce78a43004b`. `DEF_FDI_HEAD` in
`run_inference.py` repointed; verified live — a real run records
`models/10_fdi_head_dentex_tufts_v2` in the report's `models` block, 23 teeth, 0 duplicates.

**v1.0 is retained unchanged and STILL hash-pinned.** `verify_invariants.py` now checks both
heads (7/7 still passing). Every Stage-2 number published before today was measured on v1.0,
so it must stay byte-reproducible; this is an addition, not an overwrite (CLAUDE.md rule 3).

**Adopted for robustness, not accuracy** — restated here because it is the single easiest
thing to misquote: in-domain +0.11pp (inside the ~1pt noise floor), out-of-domain **+21.5pp**.

### 2. Literature check on the Tufts mirror finding — NOT yet a novelty claim

Searched the indexed biomedical/arXiv corpora and the web for prior reports.

- **The Tufts paper itself** (Panetta et al., IEEE JBHI 2022, pmid:34606466) states the
  *"universal tooth numbering system was used to identify and label"*. Full text is not in the
  indexed corpus, so **the paper's own description of its handedness convention has NOT been
  read** — only the abstract/figure text. **This is the one check still outstanding**; it must
  be done before any novelty claim, because if the paper documents the convention, the finding
  is a usage note, not a discovery.
- **The nearest hit is not the same thing.** *Structure-Guided Tooth Numbering and Lesion…*
  (MDPI J. Imaging 12(6):256) reports *"numbering jumps, duplicates, and left–right mirror
  errors"* — but that text is about **its own model's prediction errors** from a YOLOv8n-cls
  quadrant classifier, not about mirrored ground-truth labels in a released dataset. Read
  directly; different phenomenon.
- No GitHub issue or paper was found reporting mirrored ground truth in Tufts. **Absence of
  evidence found in one search session is not proof of novelty** — treat the claim as
  *unverified* until the Panetta full text is read.

### 3. What the two comparison papers actually used

| | DPML (ESWA 254:124446, 2024) | DentFound (Nat. Biomed. Eng. 2026) |
|---|---|---|
| Own data | 110 images, **10 train / 100 val**, one hospital, mostly one machine (Sirona Orthophos XG) | 101,000+ patients, multi-centre, 4 IRBs |
| Public? | **No** — *"Data will be made available on request"* | Clinical data **no** (IRB/PHI); tooth-ID data **yes** |
| Public sets used | **DENTEX** — the same corpus we use | **Dual-labeled Panoramic Radiographs** (Kaggle, 2,000 images, FDI 11–48 + label 91, 33 classes); **Teeth Segmentation on Dental X-ray Images** (Kaggle, 598 images, 15,318 polygons, 32 classes) |
| Code | not released | **released** — github.com/ahukui/DentFound |
| Numbering granularity | **8 classes** (tooth *type*; left/right collapsed by design, justified by bilateral symmetry) | **52 classes** (FDI 11–48 permanent **+ 20 primary**; 53-channel mask) |
| Headline | 95.80% acc / 97.70% precision (8-class, own data); 95.06% detection mAP | — |

**The number that matters most for our positioning:** DPML also evaluated on public DENTEX,
and reports **mAP 61.83 / mIoU 0.5562** there — against **95.06 mAP on its own data**. Their
own table shows HierarchicalDet at 60.11 and Faster-RCNN at 53.37 on DENTEX. So the published
ceiling on the shared public benchmark is ~62 mAP, **33 points below the headline they
advertise on their private single-centre set.** That is the same in-domain/out-of-domain gap
this project measured for Stage 2 (2026-08-25j) and for bone loss (2026-08-25d), reported
independently by a Q1 paper.

### 4. A licence problem, found while checking provenance

The Tufts release agreement (`https://tdd.ece.tufts.edu/`) states verbatim: *"No permission is
granted to reproduce the database or post into any webpage or any other storage means"*, *"The
Researcher may not provide research associates and colleagues with access to the Database"*,
and *"Failure to follow the above steps will invite legal prosecution."*

`docs/EXTERNAL_DRIVE.md` records a Google Drive folder holding the Tufts `ZIP/` raw release
that was **browsable without signing in**. That is link-accessible redistribution, which the
agreement forbids. Flagged in `EXTERNAL_DRIVE.md` with the required action (restrict the
folder; share the release *form*, not the files) and the mandatory citation. Not a model or
metric issue — but it is the kind of thing that surfaces at submission, so it is logged here.

### 2026-08-26a (continued) — novelty check: still NOT established, and why

Second, harder attempt to verify the Tufts mirror finding's novelty. Routes tried, all dead
ends for the decisive source:

| route | result |
|---|---|
| Indexed biomedical/arXiv corpora (`pmid:34606466`) | *"no full-text passages available"* |
| Same via DOI `10.1109/JBHI.2021.3117575` | 404 — not indexed |
| Author's own site (karenpanetta.com) | citation only, links to the paywalled IEEE DOI |
| PDF-category web search | no accessible full text; IEEE Xplore paywalled |
| GitHub (`JinweiZhu/ToothDetectionAndNumbering`, "Detecting and Labeling Panoramic Tufts…") | repo contains only a course-paper PDF, no README or code describing the convention |

**Verdict unchanged: novelty NOT established, and it cannot be from open sources.** The
decisive check — does Panetta et al. document the handedness convention? — needs IEEE Xplore
access. **Anyone with an institutional IEEE subscription can settle this in five minutes;
until then the claim stays out of the paper.**

**Supporting evidence found, which is worth having either way.** Eftimie et al. 2025
(*MethodsX* 15:103696, PMC12637385) describes the dataset as: *"1,000 panoramic radiographs
with tooth-level annotations, including tooth polygons and **FDI-based numbering (classes
0–31)**."* That is wrong on the face of it — Tufts ships Universal-style labels ('1'–'32' plus
deciduous letters 'A'–'T'), not FDI codes (11–48), as verified directly from `teeth_bbox.json`
(2026-08-25h). A peer-reviewed paper mis-naming the numbering system is concrete evidence that
the convention is genuinely unclear to users of this dataset — **but it is a different error
from the handedness one, and must not be presented as prior art for the mirror.**

Standard convention re-confirmed from a reference source while checking: Universal tooth 1 is
the maxillary **right** third molar, and the patient's right appears on the **left** of the
chart — consistent with the assumption the mirror finding was tested against.

### Venue facts (verified 26 Aug 2026, from the official sites)

- **IEEE ISBI 2027** — the **24th** International Symposium on Biomedical Imaging. Paper
  submission deadline **Monday 26 October 2026** (biomedicalimaging.org/2027/papers/). Well
  past the "10th edition" bar; already the target named in `transfer.md` §1.
- **IEEE ICBET 2027** — 17th International Conference on Biomedical Engineering and Technology
  (Aug 2027) — a mid/upper-tier fallback by edition count.
- Newly-launched venues (e.g. AIHC 2027, advertised as a **1st** International Conference,
  IEEE Conference Record #71011) sit in the lowest grading band by edition count.

Indexing status changes; **verify Scopus coverage on the Scopus source list for any venue
before submitting** rather than trusting a call-for-papers claim.

## 2026-08-26b — Found: real Tufts radiograph pixels embedded in tracked notebooks (repo is private; deferred)

While cross-verifying the repo before a `git push`, checked whether any Tufts pixel data had
ever been committed directly (not just referenced by path). It has: several notebooks carry
rendered radiographs as base64 PNG **cell outputs** — not references, the actual pixel data,
inside the tracked `.ipynb` JSON.

| File | Embedded images | Content |
|---|---|---|
| `notebooks/bone_loss/01_tufts_data_exploration_v2.ipynb` | 8 | Radiograph quality audit, mask visual inspection |
| `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb` | 3 | Sample crop grids, class visualisations |
| `notebooks/bone_loss/03_bone_loss_model_training.ipynb` | 5 | False-positive/negative sample crops |
| `notebooks/bone_loss/04_bone_loss_severity.ipynb` | 4 | CEJ estimation overlays on real crops |
| `notebooks/bone_loss/05_cej_estimation_v2.ipynb` | 2 | Sample overlays |
| `_repo_archive/datasets_workspace/week1_tufts_eda_v2.ipynb` | 22 | Full radiograph + FDI bbox overlays |
| `_repo_archive/datasets_workspace/x.ipynb` | 6 | Rotation-verification radiograph renders |

Two samples rendered directly to confirm content rather than infer it from cell source: one is
a real Tufts image (`1010.jpg`) with bounding-box overlays; the bone-loss notebooks show real
crop grids and mask overlays, not synthetic plots.

**Confirmed via `git merge-base --is-ancestor`: all of this is already on `origin/main`**, from
commit `6485eeb`, predating this session. Also confirmed: `_repo_archive/` — documented
elsewhere (CLAUDE.md, `docs/README.md`) as living *outside* the git tree — is in fact **inside
this repo's directory and partially tracked** (23 MB: scripts, notebooks, a stale survey-paper
draft, diagrams; no raw dataset files or full-resolution image dumps).

**Deferred, not actioned.** Asked the user directly: the GitHub repo is confirmed **private**,
which changes the urgency from "active leak" to "risk to address before any public release."
User's explicit decision: leave it as-is for now, proceed with the planned documentation push.
No git history was rewritten, no files were deleted, nothing was force-pushed.

**Action needed before this repo (or any fork/mirror of it) ever goes public:** either strip
the embedded outputs (`nbstripout` or equivalent, going forward — old commits still carry them
until history is rewritten) or purge the blobs from history entirely (destructive, needs a
force-push, and does not retroactively un-expose anything already cloned). Recorded as a
pending decision in `transfer.md` §4.

## 2026-08-26c — The frozen Tufts split is now derived from code, not carried between laptops

- **What was done:** Reproduced `outputs/eda_tufts/split_v1.csv` **byte-for-byte** on the
  Windows machine, from the raw data alone, and extracted the logic into
  `scripts/tufts/regenerate_split_v1.py`. Then rebuilt `data/tufts/dataset_seg/` from it —
  the R1 training input — which had never existed on this machine. R1 is now unblocked here
  with no file transfer from the macOS machine required.
- **Dataset / config:** Tufts, 1,000 rotated radiographs (840×1615) + `teeth_bbox.json` +
  `teeth_polygon.json`. Split logic lifted verbatim from `week1_tufts_eda_v2.ipynb` cells
  6/12/24: `np.random.RandomState(42).shuffle` over the sorted filename list, ratios
  70/15/15. NumPy's *legacy* `RandomState` is stream-stable across versions, which is why it
  reproduces exactly on NumPy 2.4.6 having been written under NumPy 1.x.
- **Metrics:** Four independent invariants, all recorded in this repo *before* the script
  existed, all passed:
  1. split counts **700 train / 150 val / 150 test**
  2. empty-label images per split **21 / 5 / 6**
  3. the documented duplicate leak **`590.JPG`→test, `591.JPG`→train**
  4. **SHA-256 `6de8cef2af1e73ff843f0353dccc0f93ddac34f33422c418f8ac07c67accb58b`** — exact
     match to `T0.6_detector_reconciliation.md` §3.3.

  The rebuilt `dataset_seg/` independently reproduces the macOS build: **26,005 instances**
  (18,268 train / 3,807 val / 3,930 test) over 700/150/150 images, 334 MB on disk. The test
  count of **3,930** matches the figure `T0.6` §2 pre-registered its acceptance caveat
  around (vs the bbox set's 3,924), confirming this is the same conversion, not a similar one.
- **Key decision or insight:** **`split_v1.csv` was never an irreplaceable artefact — it was
  always a pure function of the data plus seed 42, and nobody had written that down as code.**
  Because it is gitignored (`outputs/`), it was twice treated as a hard blocker: declared
  "lost after an exhaustive search" on 2026-08-20 (the search ran over a Windows filesystem
  while the file sat on macOS — see 2026-08-21), and genuinely absent again on 2026-08-26 when
  work resumed on Windows. The EDA notebook stated the determinism in its own header the whole
  time ("Rule 2: Split is deterministic and write-once, random seed FIXED to 42"). This entry
  closes that failure mode permanently: the split is now regenerable anywhere in seconds, and
  `--verify` turns the four invariants into a guard rather than a one-off check.
- **Source:** `scripts/tufts/regenerate_split_v1.py` (self-verifying; run with `--verify`);
  `scripts/yolo/convert_tufts_to_yolo_seg.py` run unmodified via its env-var overrides;
  provenance notebook `_repo_archive/datasets_workspace/week1_tufts_eda_v2.ipynb` cells 6/12/24.
- **Follow-ups:** R1 (`train_yolo_seg.py`) is now blocked on **nothing but GPU time** on this
  machine. Note this machine has **only** Tufts — DENTEX (~14 GB) and Ningxia are absent, so
  caries work and the DENTEX+Tufts bone-loss experiment cannot be fed from here without
  fetching DENTEX first (`docs/EXTERNAL_DRIVE.md`). `models/09_caries_gate_v3/caries_gate_v3.pth`
  is also absent here, so `run_inference.py` will not complete on this machine yet.

## 2026-08-27a — R1's first GPU run was trained on misaligned masks; two data defects found and fixed

- **What was done:** Ran R1 (YOLOv11l-seg) to completion on a JarvisLabs A100-80GB, then found
  the result was invalid: **every instance mask in the training data was spatially misaligned
  with its image.** Root-caused to two *independent* defects, both now fixed and verified. The
  run's numbers are withdrawn; the held-out test split was **not** touched, so the one-shot
  test-set discipline of `T0.6` §2 is intact and R1 can be re-run cleanly.
- **The trigger:** final validation on `best.pt` gave box mAP@0.5 **0.258** / mask mAP@0.5
  **0.204**, against the canonical bbox detector's **0.834** val mAP@0.5 on the same split.
  A ~0.58 gap is far too large for a bbox→mask change and matched the failure mode
  `rotate_tufts_radiographs.py`'s own docstring warns about — a detector "trains perfectly
  happily on upside-down teeth", so bad geometry degrades silently instead of crashing.
- **Defect 1 — `teeth_polygon.json` stores points as `[y, x]`.** `teeth_bbox.json` uses
  `[x1, y1, x2, y2]`. `convert_tufts_to_yolo_seg.py` inherited the bbox converter's
  "no transform needed" assumption, which is correct only for the bbox file. Established by
  matching **6,006 title-paired objects** across the two files and testing five candidate
  transforms — median centre-distance: identity **442.13 px**, 90° CCW **288.51 px**,
  90° CW **175.50 px**, **transpose 2.06 px**, anti-transpose **390.63 px**.
- **Defect 2 — this machine's `Radiographs_rotated/` is 180° out.** It has an mtime of
  20 Aug 2026, predating the 22 Aug rotation-direction fix in
  `rotate_tufts_radiographs.py`, so it holds `ROTATE_270` (CW) output where the canonical
  frame is `ROTATE_90` (CCW); CW and CCW differ by exactly 180°. Measured via mean pixel
  intensity inside `teeth_bbox` annotations (teeth are radio-dense, so aligned annotations sit
  on brighter-than-average pixels): **0.967 → 1.056** after a 180° rotation.
  **Both defects had to be fixed — correcting either alone still yields garbage.**
- **Metrics (verification, not model performance):** the decisive check is agreement between
  the built seg labels' bounding boxes and `teeth_bbox.json`, the ground truth the canonical
  detector was trained on, over 3,225 train instances:

  | dataset | median IoU vs `teeth_bbox` | match @ IoU≥0.5 |
  |---|---|---|
  | `dataset_seg` (used by the withdrawn run) | **0.000** | **1.6 %** |
  | `dataset_seg_v2` (fixed) | **0.837** | **99.4 %** |

  Corroborated two further ways: brightness ratio inside built label polygons **0.987 → 1.072**,
  and visual overlay on 3 radiographs (dense, sparse, restored arches) where every polygon
  traces a real tooth. Instance counts are unchanged at **26,005** (18,268 / 3,807 / 3,930) —
  the fix moves coordinates, it does not add or drop objects.
- **Key decision or insight:** **A falling loss curve is not evidence of correct data.** The
  withdrawn run's losses decreased smoothly for 90 epochs, GPU/throughput/checkpointing were
  all healthy, and every hyperparameter matched the pre-registration exactly — the run was
  *operationally* flawless and *scientifically* void. What caught it was comparing the result
  against a known reference (0.834) and treating the discrepancy as a defect to explain rather
  than a disappointing outcome to report. Geometry must be verified against an independent
  annotation source **before** training, which is now a required pre-flight step.
  Consequently, `T0.6` §3.5's claim that this converter was "verified end-to-end against real
  data" on 20–21 Aug (7 images spot-checked) is **not reliable** — it did not catch either
  defect and needs re-checking on the macOS machine.
- **Source:** `scripts/yolo/fix_tufts_orientation.py` (new, self-verifying, refuses to run on
  an already-aligned source); `scripts/yolo/convert_tufts_to_yolo_seg.py` (`[y,x]`→`(x,y)`
  swap); `data/tufts/dataset_seg_v2/`. Withdrawn run: 90 epochs, early-stopped, best epoch 60.
- **Cost:** ₹118.81 of the ₹900 JarvisLabs balance (~45 min wall-clock incl. debugging);
  instance destroyed, nothing left billing.
- **Follow-ups:** re-run R1 on `dataset_seg_v2` against the unchanged pre-registered criterion
  (box mAP@0.5 ≥ 0.75, mask mAP@0.5 ≥ 0.65). **Re-verify the macOS machine's `dataset_seg/`
  and its `Radiographs_rotated/` for the same two defects** — if its polygon data went through
  the same converter, anything derived from it is suspect. `data/tufts/dataset_seg/` (broken)
  is retained, not deleted, per `CLAUDE.md` rule 3.

## 2026-08-27b — R1 re-run on corrected data: box bar PASSED, mask bar MISSED, bbox stays canonical

- **What was done:** Re-ran R1 (YOLOv11l-seg) on `dataset_seg_v2` after the two data defects
  in 2026-08-27a were fixed and verified. Config unchanged from the pre-registration.
  Evaluated the held-out test split **exactly once**, after checkpoint selection on val.
- **Dataset / config:** Tufts frozen `split_v1` (700/150/150, not re-randomised),
  `dataset_seg_v2` (26,005 instances). `yolo11l-seg.pt` COCO-pretrained, **no warm start**
  from the bbox detector. imgsz 1024, batch 32, AdamW, lr0 0.001, seed 42, deterministic,
  degrees 10, mosaic 0, flipud 0 — every value verified against
  `models/06_yolo_detection_a100_run/train_args.yaml` before launch and against Ultralytics'
  resolved-config echo at runtime. 135 epochs (early stop, patience 30), best epoch 105,
  0.788 h on a JarvisLabs A100-80GB.
- **Metrics — held-out TEST, 150 images / 3,930 instances, single evaluation:**

  | | P | R | mAP@0.5 | mAP@0.5:0.95 |
  |---|---|---|---|---|
  | **Box** | 0.7666 | 0.7751 | **0.8100** | 0.3411 |
  | **Mask** | 0.6270 | 0.6339 | **0.6383** | 0.2238 |

  Validation (`best.pt`, 150 img / 3,807 inst): box mAP@0.5 **0.8250**, mask **0.6520**.

  **Against the pre-registered bar (`T0.6` §2):**

  | bar | result | verdict |
  |---|---|---|
  | Box mAP@0.5 ≥ 0.75 | 0.8100 | **PASS** |
  | Mask mAP@0.5 ≥ 0.65 | 0.6383 | **FAIL** (short by 0.0117) |

- **Key decision or insight:** **The bar was missed on mask, so the bbox detector
  `tooth-detector-a100-1024-v1.0` REMAINS the canonical Stage-1 model, and the 0.65 floor was
  not adjusted after seeing the number.** This is logged as a documented partial result, per
  §2's own instruction. R2 (mask-aware cropping) stays unwired.

  **But the box result is a genuine positive worth reporting on its own:** the seg model
  reaches **0.8100** test mAP@0.5 against the bbox detector's **0.7824** — **+2.76 points** on
  the same frozen split with an otherwise identical config. Training with instance masks
  produced a *better box detector* than training on boxes alone, directionally consistent with
  DentFound's ablation. This is also the number that matters most downstream, since Stage-2
  end-to-end is capped by **detector recall**, not mask quality. Whether that box gain is worth
  adopting is a **separate decision from the §2 bar**, which was written to govern a
  mask-driven replacement — it should not be resolved by quietly reinterpreting §2.

  **Caveat, pre-registered in §2 and repeated rather than buried:** the seg test ground truth
  holds 3,930 instances vs the bbox test set's 3,924 — 6 real teeth (0.15%) the bbox converter
  dropped on a corrupt `bounding box` field. Near-like-for-like, not exactly like-for-like.
- **Source:** `models/11_yolo_seg_tufts_r1/run_summary.txt`, `.../run/results.csv`,
  `.../test_results.txt` (the evaluation verbatim), `.../run/args.yaml`.
  Weights `best.pt` SHA-256 `271316c46caaf4029ea707fa77b6fe30697795e46632e1f6fcae3498c48781ba`,
  verified byte-identical after download; gitignored per `CLAUDE.md` rule 4, local disk only.
- **Cost:** ₹130.38 (₹781.19 → ₹650.81). Instance destroyed. Total R1 spend including the
  withdrawn run: **₹249.19** of the original ₹900.
- **Follow-ups:** (1) Decide whether the **+2.76-point box gain** justifies adopting this as
  Stage-1 despite the mask miss — a real methodology call, **not** something to default into.
  (2) If the mask gap is to be chased, pre-register the change first; candidate levers in
  `run_summary.txt` (`mask_ratio`/`overlap_mask` were never tuned; the largest-fragment
  heuristic caps achievable mask quality). (3) **Re-verify the macOS machine's `dataset_seg/`
  and `Radiographs_rotated/` for the same two defects** — still open from 2026-08-27a.
  (4) Re-measure Stage-2 end-to-end if this detector is ever adopted; the recall change moves
  the ceiling and that must be measured, not assumed.

## 2026-08-27c — Blast radius of the two data defects: no other result affected. Guards moved into code.

- **What was done:** Traced both defects from 2026-08-27a through every consumer, and replaced
  the "re-verify the other machine" follow-up — which entries 27a and 27b both listed — with an
  enforced guard in the converter. **This entry corrects those two follow-ups**; per the
  append-only rule they are left as written rather than edited.
- **Why it was wrong:** 27a/27b told the reader to go re-check the macOS machine. That machine
  is a second person's laptop and is not always reachable, so the follow-up was not actionable
  — and, once traced, not necessary either. Recording a hand-off task without establishing it
  is reachable *or* needed is the same failure mode as a stale status claim.
- **Findings — traced, not assumed:**
  - **Defect 2 (180° rotation) is Windows-only.** The macOS copy was always correct:
    `week1_tufts_eda_v2.ipynb` Rule 1 records the original rotation as `img.rotate(90)` (CCW),
    and `convert_tufts_to_yolo.py` applies **no** coordinate transform — so the canonical
    detector's **0.7824** test mAP@0.5 is only reachable if that machine's images already
    agreed with `teeth_bbox.json`. Misaligned data scores ~0.25 (the withdrawn run).
    `rotate_tufts_radiographs.py` was written 20 Aug as a reconstruction of undocumented
    knowledge, got the direction wrong, and **was only ever executed on Windows** — on macOS
    the correct images already existed, which is also why the 22 Aug fix was a code change with
    no data regeneration.
  - **Defect 1 (`[y,x]` point order) is machine-independent but has zero blast radius.** Its
    only consumer is `dataset_seg/`, and `train_yolo_seg.py` was unrun until 27 Aug. Verified
    every other reader of Tufts geometry: bone-loss crops are built from **`teeth_bbox.json`**
    (`02_bone_loss_dataset_construction.ipynb` sets `BBOX_JSON`; `teeth_polygon.json` appears
    only in a comment), `01_tufts_data_exploration_v2.ipynb` is exploration-only,
    `src/crop_generator.py` mentions polygons only in a docstring, and R2 is unwired from
    `run_inference.py`. **The detector, both FDI heads, the caries gate and the bone-loss
    models are all unaffected.**
- **Metrics (guard behaviour, verified both ways):**

  | path | image-orientation ratio | built-label agreement | outcome |
  |---|---|---|---|
  | auto-detect, correct dir | 1.040 (vs 0.964 for the broken dir) | median IoU 0.837, 99.4% @IoU≥0.5, n=3,225 | **GATE PASSED**, dataset written |
  | forced at the broken dir | 0.964 | — | **ABORT, exit code 1**, nothing written |

- **Key decision or insight:** **Documentation cannot enforce a data invariant; only an
  assertion can.** The 26 Aug void run happened despite the defects being discoverable, because
  nothing in the pipeline was obliged to check. So the fix is now code, and — because two
  machines with *different* local data are both in active use — it is written to be
  machine-agnostic: `convert_tufts_to_yolo_seg.py` chooses its image directory by **measuring**
  each candidate against `teeth_bbox.json` rather than trusting a directory name, then
  re-scores the labels it wrote and exits non-zero if they disagree. Neither machine needs
  configuring and nobody needs to remember which local copy is the good one. Shared thresholds
  and helpers: `scripts/yolo/_tufts_align.py`, imported by both scripts so the definition of
  "aligned" cannot drift between them.
- **Also fixed:** `validate_inputs()` counted images as `glob("*.jpg") + glob("*.JPG")`, which
  on a case-insensitive filesystem matched every file twice and reported "2000 images" for
  1,000 — it would have passed a half-empty directory. Now deduplicated by resolved path.
- **Source:** `scripts/yolo/_tufts_align.py` (new), `scripts/yolo/convert_tufts_to_yolo_seg.py`
  (auto-detect + post-build gate + count fix). Guard behaviour tested in both directions on the
  Windows machine, which holds one correct and one known-broken image directory — an unusually
  good test fixture for exactly this.
- **Follow-ups:** `T0.6` §3.5's "verified end-to-end against real data" claim is annotated in
  the converter docstring as unreliable *evidence of correctness* (a 7-image spot-check passed
  with both defects live) — but it invalidates no published number. `docs/research/` is owned by
  a separate workstream, so §3.5's own text is left for that owner to amend.

## 2026-08-27d — Seg detector ADOPTED as Stage-1 default (human decision; the bar was not met)

- **What was done:** Swapped `DEF_DETECTOR` from the bbox detector to
  `tooth-detector-seg-tufts-1024-v1.0` (`models/11_yolo_seg_tufts_r1/best.pt`), on the user's
  explicit instruction, for the box gain alone.
- **This is a decision, not a bar being met — stated plainly because the two are different
  claims.** `T0.6` §2 required **both** box mAP@0.5 ≥ 0.75 **and** mask mAP@0.5 ≥ 0.65 on the
  held-out test split. Box passed (0.8100); **mask failed (0.6383, short by 0.0117)**. §2 was
  **not** rewritten, softened, or reinterpreted, and 2026-08-27b's verdict stands as recorded.
  Adoption is logged here as a separate, dated human call.
- **Rationale (the user's, recorded as given):** +2.76 points of box mAP@0.5 over the
  superseded detector (0.8100 vs 0.7824) on the same frozen split with an otherwise identical
  config — and box quality, not mask quality, is what bounds everything downstream, since
  Stage-2 end-to-end is capped by detector recall.
- **Consequences, enforced in code rather than just written down:**
  - **Masks are NOT validated to §2's standard, so the model is used for its BOXES ONLY and
    R2 (mask-aware cropping) stays UNWIRED.** The 0.65 floor existed to protect R2; nothing has
    changed that judgement.
  - **Every DENTEX-measured downstream figure is now STALE.** `STAGE1_DETECTOR_RECALL` (0.670)
    and `STAGE2_FDI_EXACT_END_TO_END` (0.465) in `run_inference.py` are now `None`, with the
    old values kept as `SUPERSEDED_*` constants and a "pending re-measurement" note emitted in
    every report's `limitations` block. They could not be re-measured at adoption time because
    **DENTEX is not on the machine where the swap was made**. Emitting `null` was chosen over
    printing figures that would silently misdescribe the running pipeline.
  - The detector tag in report metadata was hardcoded as `tooth-detector-a100-1024-v1.0`; it is
    now a `DETECTOR_TAG` constant beside `DEF_DETECTOR` so the two cannot drift apart.
  - The bbox detector is **retained unchanged and hash-pinned** — every pre-27-Aug number was
    measured on it and it must stay byte-reproducible.
- **Verification before the swap:** confirmed the seg model is drop-in for the pipeline's
  detector call path — `src/orientation.detect_upright()` reads `r.boxes.xyxy`/`.conf`, which a
  `task=segment` model provides. Ran both models through it on the same image: **31 boxes each**
  (image 50 has 32 annotated teeth). `verify_invariants.py` now hash-pins the new default and
  reports **7/7 holding**; **65/65 tests pass**.
- **Source:** `scripts/run_inference.py` (`DEF_DETECTOR`, `DETECTOR_TAG`, stale-constant
  handling), `scripts/eval/verify_invariants.py`, `models/11_yolo_seg_tufts_r1/run_summary.txt`,
  `docs/results/model_metrics.md`, `models/README.md`, `docs/EXTERNAL_DRIVE.md`.
- **Follow-ups — the first is blocking for any quoted end-to-end number:**
  1. **Re-measure Stage-1 recall and Stage-2 end-to-end on DENTEX** against the new detector,
     then restore real values to the two constants. Until then the pipeline honestly reports
     that it does not know them.
  2. **Upload `models/11_yolo_seg_tufts_r1/best.pt` to the Tufts drive's
     `capstone_checkpoints/`.** It is now load-bearing and >50 MB, so a fresh clone currently
     **cannot run the pipeline at all**. `docs/EXTERNAL_DRIVE.md` lists it as missing.
  3. Re-run the C2 Ningxia external evaluation, which also used the old detector.

## 2026-08-27e — Stage-2 re-measured on DENTEX: end-to-end 46.3% → 58.3% (+12.0 points)

- **What was done:** Closed the blocking follow-up from 2026-08-27d. Fetched the 500-file
  `DENTEX/disease/` subset (250 images + 250 LabelMe labels, 1,023 MB — 4.6% of the 10,781-file
  Drive mirror, not the full ~14 GB) and re-measured Stage-2 end-to-end against the newly
  adopted seg detector. Ran a **control first**: the same harness with the *superseded* bbox
  detector, so any change is attributable to the detector and not to the machine or the data.
- **Dataset / config:** 164 leak-free `DENTEX/disease/` images, 936 GT teeth (86 excluded as
  training duplicates per `data/dentex/disease_leaked_images.json`). conf 0.25, NMS IoU 0.50,
  imgsz 1024, CCW rotation, head v2.0, Hungarian one-to-one. Only the detector differs between
  the two columns.
- **Metrics:**

  | Metric | bbox detector (control) | **seg detector (adopted)** | Δ |
  |---|---|---|---|
  | Detection recall | 67.3% (630/936) | **70.6%** (661/936) | **+3.3 pp** |
  | FDI exact (of detected) | 68.7% | **82.6%** | **+13.9 pp** |
  | Quadrant correct | 94.6% | **97.6%** | +3.0 pp |
  | Right quadrant, off-by-one | 22.7% | **13.5%** | −9.2 pp |
  | **FDI exact, end-to-end** | 46.3% (433/936) | **58.3%** (546/936) | **+12.0 pp** |
  | Duplicate FDI codes | 0 | **0** | — |
  | Mean detections/image | 23.7 | **22.0** | −1.7 |

- **Key decision or insight:** **The detector swap bought far more than its recall gain.**
  Recall rose 3.3 points, but end-to-end rose **12.0**. The mechanism is visible in the
  numbers: detections per image went *down* (23.7 → 22.0) while recall went *up*, i.e. the seg
  detector emits **fewer spurious boxes**. Because every spurious box perturbs the Hungarian
  one-to-one assignment across an entire quadrant, cleaner boxes lift FDI-exact-of-detected by
  13.9 points *on top of* the recall gain — and halve off-by-one errors (22.7% → 13.5%).
  **This retroactively strengthens the 27d adoption decision, which was taken on the box-mAP
  gain alone without knowing the downstream effect.** It also re-confirms the standing
  conclusion that Stage 1 — not the numbering head — is the binding constraint: the head was
  already 91% on ground-truth boxes, and improving the boxes is what moved the headline.
- **Reproduction caveat, recorded rather than hidden:** the control did **not** exactly
  reproduce the published bbox numbers — 67.3% / 46.3% here vs 67.0% / 46.5% as published,
  a ~3-tooth drift consistent with CPU-vs-GPU float differences and inside the ~1-point
  run-to-run noise floor already measured (`RESULTS_LOG` 2026-08-25i: identical configs
  differed by 9 teeth of 936). The +12-point effect is an order of magnitude larger, so it is
  not an artefact of that drift — but the control is not an exact reproduction and is not
  presented as one.
- **Also found and fixed during the fetch:** one image (`test_242.png`) was left truncated at
  2,428 bytes by an interrupted first download attempt, and the resumable logic skipped it
  because it was non-empty. The first control run silently evaluated **163 images / 934 teeth**
  instead of 164 / 936. Caught from the script's own `WARNING unreadable` line, re-fetched, and
  all 500 files were then integrity-checked (every PNG opened, every JSON parsed) before the
  reported runs. A size>0 check is not an integrity check.
- **Source:** `scripts/eval/validate_fdi_assignment.py --method head` with explicit `--weights`
  and `--head-weights`; outputs in `outputs/stage2_control_olddet/` and `outputs/stage2_segdet/`.
  Constants restored in `scripts/run_inference.py` (`STAGE1_DETECTOR_RECALL = 0.706`,
  `STAGE2_FDI_EXACT_END_TO_END = 0.583`).
- **Follow-ups:** (1) `scripts/eval/validate_fdi_assignment.py`'s own defaults still point at
  the **old** detector and the **v1.0** head — they were not changed, since old numbers must
  stay reproducible, but that means the defaults no longer describe the pipeline and every
  invocation must pass explicit weights. Worth aligning deliberately. (2) C2's Ningxia external
  validation still used the old detector and remains stale. (3) The seg checkpoint is still not
  uploaded to Drive — a fresh clone still cannot run the pipeline.

---

## 2026-08-27f — R1's results propagated into the paper doc and the READMEs; a fresh-clone break found

- **What was done:** Cold-start orientation pass found that 2026-08-27b/d/e were written into
  `RESULTS_LOG.md`, `model_metrics.md` and `transfer.md` but **never into
  `PAPER_MATERIAL.md` or the root `README.md`** — `CLAUDE.md` rule 1 item 3, unfulfilled. The
  largest result this project has recorded (+12.0 points end-to-end) and a changed Stage-1
  default were absent from the document the paper is written from. Propagated, and found one
  genuine correctness break while doing it.
- **Dataset / config:** n/a — documentation only. No number was recomputed; every figure
  written was copied from 2026-08-27b/d/e and `models/11_yolo_seg_tufts_r1/run_summary.txt`.
- **Metrics:** no new metrics. Verified unchanged before and after: **65/65 tests pass**,
  `verify_invariants.py` **all invariants hold** (with the expected Windows SKIPs for absent
  DENTEX/caries-gate artefacts).
- **The correctness break — this is the part that mattered.** `README.md`'s fresh-clone recipe
  told the reader to fetch `models/06_yolo_detection_a100_run/best.pt`, but
  `run_inference.py:94` has pointed `DEF_DETECTOR` at `models/11_yolo_seg_tufts_r1/best.pt`
  since the 27 Aug adoption. **A reader following the README exactly would fetch the superseded
  detector and then fail on a missing file** — with no hint as to why, since the file the
  pipeline actually wants is not on Drive at all. Now documented with the `--detector` fallback
  (and its honest cost: 46.3% end-to-end, not 58.3%).
- **Key decision or insight:** the adoption of a new default checkpoint has a **documentation
  blast radius**, and it is not the same as the blast radius of a new number. 2026-08-27c
  traced the *data* blast radius of the mask defects carefully and correctly; nobody traced the
  *default-changed* blast radius, which is why a stale fetch instruction survived. Changing a
  `DEF_*` constant should trigger a grep for every path that names the old one.
- **What was changed:** `PAPER_MATERIAL.md` §7.1 (seg results table, the missed mask bar, the
  withdrawn run as a methods note), §8.5 (was stale in both halves — "0.782" and "no canonical
  detector has been frozen"), §8.10 (the Stage-1-is-the-bottleneck prediction, now tested and
  held, with the recall-vs-precision asymmetry), §9 checklist (R1 ticked; Stages 5–6 ticked —
  it had sat unticked for three days after landing). `README.md` stage table, metrics table,
  limitations blurb, publication assessment, fresh-clone recipe. Scoping pointers added to
  `src/README.md` and `models/README.md`, whose 46.5%/46.58% tables are correctly-scoped
  historical comparisons but were newly easy to misread as current.
- **Source:** no new artefact. Traceability is to 2026-08-27b (`models/11_yolo_seg_tufts_r1/`),
  2026-08-27d (adoption) and 2026-08-27e (`outputs/stage2_segdet/`).
- **Follow-ups:** unchanged and still open — (1) upload the seg checkpoint to Drive, which is
  the only thing standing between this repo and a working fresh clone; (2) C2's Ningxia numbers
  are still on the old detector; (3) `validate_fdi_assignment.py`'s defaults still name the old
  detector and v1.0 head. Newly noted: Docker Desktop **is installed on the Windows machine**
  but its engine is not running — `docker build` has never once been executed
  (`transfer.md` §3 item 7) and is now one `Start Docker Desktop` away from being testable.

---

## 2026-08-27g — Bone-loss weights tagged (the last untagged models), and the hash check itself was wrong

- **What was done:** Froze and tagged Stages 4a/4b — `bone-loss-binary-resnet18-v1.0` and
  `bone-loss-severity-resnet18-v1.0` — the last trained models in the project without a version
  tag or a recorded hash (`models/README.md` had carried "One gap remains" for weeks; `transfer.md`
  §3 item 6). **Nothing was retrained**; these are the April 2026 artifacts, now pinned. Both are
  added to `verify_invariants.py`, taking it from 4 pinned checkpoints to 6.
- **Dataset / config:** n/a — freezing existing weights. Provenance recorded in the new
  `run_summary.txt` files from `training_summary.txt` / `severity_summary.txt`.
- **Metrics:** unchanged, and re-stated with their support counts. 4a validation macro-F1
  **0.9233** (1,558 crops at real prevalence, 1,499 normal / 59 diseased). 4b validation macro-F1
  **0.7208** on **52 crops total**, Mild n=6. SHA-256:
  `c52f7f48…` (4a `best`), `fa93a520…` (4b).
- **The check that was supposed to catch problems had one of its own.** Writing 4a's summary —
  which documents **two** checkpoints, `best` (the pipeline default) and `final` (unused) — made
  `verify_invariants.py` fail. Cause: it took the sha256 as "the last 64-hex token anywhere in the
  file", so `best.pth` was checked against `final.pth`'s hash. That heuristic was correct only
  while every summary named exactly one checkpoint, which had been true until now by accident.
  **Fixed properly rather than by reordering the file:** each hash is attributed to the most
  recent weight filename above it, `hash_from_summary()` was extracted to be testable, and the
  behaviour is covered by 8 new tests including the historical failure. **Tests 65 → 73.**
  Reordering the summary would have made the symptom go away and left the trap armed.
- **Key insight — the bone-loss class order is no longer an assumption.** Both checkpoints are
  raw `state_dict`s carrying no `class_to_idx`, and `run_inference.py` honestly described the
  order as "Inferred, not read". It is now confirmed two independent ways that agree:
  **(1)** FocalLoss alpha is inversely proportional to class frequency, and the alpha ratio
  **2.258/0.642 = 3.5171** matches the class-count ratio **2,500/711 = 3.5162** to 0.03%, so
  index 0 is the majority class = normal; **(2)** `training_summary.txt` labels its own scores
  **"F1 Normal (cls 0)" / "F1 Diseased (cls 1)"**. A flipped order would have the pipeline
  reporting bone loss on ~99% of teeth instead of the observed 0.7% on DENTEX — a third, weaker
  corroboration. `run_inference.py`'s note was upgraded accordingly.
- **What did NOT change:** the domain-shift failure. 0.9233 in-domain still collapses to 0.7%
  firing on DENTEX and 0.8–5.4% affected-tooth sensitivity on Ningxia. Tagging a model does not
  improve it, and both new summaries say so explicitly so the tag cannot be mistaken for
  validation. **T0.5 (the n=6 Mild class) is also NOT closed by this** — it is a reporting
  decision, and it remains open.
- **Source:** `models/03_bone_loss_model_training_notebook_models/run_summary.txt`,
  `models/04_bone_loss_severity_notebook_models/run_summary.txt`,
  `scripts/eval/verify_invariants.py`, `tests/test_verify_invariants.py`. 73/73 tests pass,
  all invariants hold.
- **Follow-ups:** every trained model is now tagged, so this class of gap is closed. Next in
  this session: re-run C2 external validation on Ningxia against the seg detector — the data is
  reachable at `D:
angxia_dataset`, so the blocker recorded earlier today is lifted.

---

## 2026-08-27h — C2 re-measured on the seg detector: caries +7.7 pts, bone loss unmoved

- **What was done:** Re-ran the full Ningxia external validation (contribution C2) against the
  current pipeline — seg detector + FDI head v2.0 — because 2026-08-27d changed the Stage-1
  default and left every C2 number measured on the superseded pair. **A control on the old
  detector + head v1.0 was run first**, on this machine, so the delta is attributable to the
  models rather than to this box's different library versions. 2,146 image-evaluations in total
  (736 periodontitis + 337 caries, each twice), ~1.7 s/image on CPU, no GPU rented.
- **Dataset / config:** Ningxia `segmentation/{dental_caries,periodontitis}/test1–4` from
  `D:\nangxia_dataset`. LOCKED external data — evaluated, not tuned against. Train split never
  touched. Metrics unchanged from 25 Aug: focal-lesion centroid containment for caries,
  affected-tooth sensitivity (≥50% of a tooth box inside the marked region) for periodontitis.

- **The control reproduces 25 Aug**, which is what makes the rest of this entry readable:

  | | 25 Aug published | control today |
  |---|---|---|
  | caries test1/2/3/4 | 26.6 / 43.3 / 37.0 / 22.6% | **27.2 / 43.3 / 35.2 / 22.0%** |
  | periodontitis test1/2/3/4 | 3.7 / 0.8 / 1.5 / 5.4% | **3.7 / 0.8 / 1.1 / 5.1%** |

  Caries lesion counts are **identical** (316/349/162/186) because that denominator comes from
  the GT masks, not the model. Periodontitis denominators moved by a few teeth — that one is
  model-dependent, see the caveat below.

- **RESULT — caries lesion agreement improved on ALL FOUR hospitals:**

  | Split | Lesions | Control | **Seg detector** | Δ | strict 1:1 |
  |---|---|---|---|---|---|
  | test1 | 316 | 27.2% | **28.8%** | +1.6 pp | 24.7 → 26.9% |
  | test2 | 349 | 43.3% | **51.3%** | +8.0 pp | 35.8 → 46.1% |
  | test3 | 162 | 35.2% | **40.1%** | +4.9 pp | 28.4 → 31.5% |
  | test4 | 186 | 22.0% | **41.9%** | +19.9 pp | 18.3 → 38.2% |
  | *(pooled, scale only)* | 1,013 | 33.1% | **40.8%** | **+7.7 pp** | 27.9 → 36.3% |

  The denominator is model-independent, so this is a straight read. External caries agreement
  now sits just under the **42.6%** DENTEX *internal* number (2026-08-25c) instead of well
  below it — the external/internal gap has largely closed without any caries model changing.

- **RESULT — periodontitis did NOT improve, and the numerator says why:**

  | Split | Affected (ctl → seg) | Flagged (ctl → seg) | Sensitivity |
  |---|---|---|---|
  | test1 | 3,278 → 3,285 | 121 → 79 | 3.7% → **2.4%** |
  | test2 | 2,068 → 2,462 | 16 → 34 | 0.8% → **1.4%** |
  | test3 | 349 → 411 | 4 → 23 | 1.1% → **5.6%** |
  | test4 | 534 → 633 | 27 → 29 | 5.1% → **4.6%** |
  | *(pooled, scale only)* | 6,229 → 6,791 (+9.0%) | **168 → 165** | 2.7% → **2.4%** |

  Across 736 images the pipeline flagged **168 affected teeth before and 165 after** — flat,
  while the denominator grew 9%. Per-split movement is in both directions and test3's
  1.1% → 5.6% is 4 → 23 teeth on 50 images; it is noise, not a win, and must not be quoted as one.

- **Key insight — the same intervention, opposite outcomes, and that is the finding.** Swapping
  the detector bought Stage 2 **+12.0 points** (2026-08-27e) and caries **+7.7 points** here,
  and bone loss **nothing**. Stages whose errors were dominated by *which teeth got cropped*
  improved; the bone-loss branch did not, because its failure is domain shift **inside the
  Stage-4a classifier**, which flags essentially the same absolute set of teeth regardless of
  what feeds it. `transfer.md` §3 item 4 suspected the detector and bone loss shared a root
  cause as the two Tufts-trained stages — **this measures that they do not.** The remaining
  lever is the DENTEX+Tufts combined-training trick that fixed Stage 2's generalisation, still
  untried for bone loss.
- **CAVEAT, stated because it limits the periodontitis comparison.** Affected-tooth sensitivity
  has a **model-dependent denominator**: "affected" teeth are counted from *detected* boxes, so
  a detector that finds different teeth changes numerator and denominator together. The control
  is what makes the comparison interpretable at all, and it should never be quoted as a plain
  sensitivity delta. Caries has no such problem. Detections/image rose in test2–4 (+15–20%) but
  *fell* in test1 (25.2 → 22.7) — test1 is the split with burned-in annotation arrows and stars.
- **Arithmetic audited exhaustively**, as on 25 Aug: per-image rows re-aggregated and matched
  every published total on all four runs (736/736 and 337/337 rows); covered ≤ lesions,
  strict ≤ covered, flagged ≤ affected, affected ≤ detected everywhere. All four result files
  record the resolved weight paths and their SHA-256, so none can be confused with the others.
- **Source:** `scripts/eval/ningxia_external.py`; `outputs/ningxia_external_control_olddet/`,
  `outputs/ningxia_external_segdet/`, `outputs/ningxia_caries_control_olddet/`,
  `outputs/ningxia_caries_segdet/`.
- **Follow-ups:** (1) C2 is no longer stale — but `lesion_localization.py`'s DENTEX 42.6% is
  still on the old detector and is now the *only* remaining pre-27-Aug external number, so the
  internal/external comparison above is not strictly like-for-like until it is re-run.
  (2) Bone-loss domain-shift fix is now the clearest open research problem in the project, with
  one specific untried approach. (3) Image-level caries sensitivity is 93–100% and remains
  saturated — still the weak metric, still not to be reported as a strength.

---

## 2026-08-27i — Lesion localisation re-run on the seg detector: the last stale number is closed

- **What was done:** Re-ran `lesion_localization.py` (DENTEX internal lesion agreement) against
  the seg detector, with a control on the old bbox detector first. This was the **last remaining
  number in the pipeline still measured on the superseded detector** — 2026-08-27h flagged that
  §8.12a's internal-vs-external caries comparison was not like-for-like until it was done.
- **Dataset / config:** DENTEX `disease/`, 164 leak-free images (86 excluded as training
  duplicates, same exclusion list as `validate_fdi_assignment.py`), 479 çürük polygons across
  148 images. `min_iou=0.30`, inherited a priori and **not** swept against this set. Caries gate
  v3 and severity unchanged — the detector is the only difference between arms.

  | | control (old det) | **seg detector** | Δ |
  |---|---|---|---|
  | Lesion-localisation agreement | 201/479 = **42.0%** | 212/479 = **44.3%** | **+2.3 pp** |
  | Predicted-positive teeth | 773 | **755** | −18 |
  | Of those, landing on a lesion (diagnostic, NOT precision) | 26.0% | **28.1%** | +2.1 pp |

  The control reproduces the published 42.6% (2026-08-25c) to within 0.6 pp on a different
  machine, so the delta is attributable to the detector. The denominator (479 GT polygons) is
  model-independent and **identical** across arms — a straight read.
- **Key insight — the same signature as Stage 2, for the third time: fewer positives, more of
  them right.** Predicted-positive teeth *fell* (773 → 755) while correctly-localised lesions
  *rose* (201 → 212). Stage 2 showed it too, gaining +12.0 pts while detections/image fell
  23.7 → 22.0 (2026-08-27e). The seg detector is not finding *more* things; it is finding
  *fewer wrong* things, and every stage consuming its boxes benefits.
- **THE COMPARISON THIS UNLOCKS — the internal/external gap has more than halved**, with both
  halves now on the same detector and controls run on the same machine:

  | | internal (DENTEX) | external (Ningxia, pooled) | gap |
  |---|---|---|---|
  | old detector (control) | 42.0% | 33.1% | **8.9 pp** |
  | **seg detector** | **44.3%** | **40.8%** | **3.5 pp** |

  **Much of what looked like a caries domain-shift problem was a detection problem.** The
  external number rose 7.7 points against the internal number's 2.3, so the swap helped
  out-of-domain data disproportionately — the same shape as the head-v2.0 result (2026-08-25j),
  where a change worth ~0 in-domain was worth +21.5 points out-of-domain. **Do not restate this
  as "caries generalises well":** 40.8% pooled external is still a weak absolute number, three of
  four hospitals sit below the internal figure, and Ningxia test2 exceeding it (51.3%) is one
  centre, not a trend.
- **Provenance gap found and closed.** This script's JSON recorded no weights, so its two result
  files were structurally identical and told apart only by the output directory name someone
  chose — exactly the gap that let 42.6% become a stale old-detector number unnoticed. It now
  writes detector/gate/severity paths plus the detector SHA-256, as `ningxia_external.py` does.
  **The two files reported above predate that change** and are identified by directory name;
  verified on a 3-image re-run that the field now appears.
- **Source:** `outputs/lesion_localization_control_olddet/lesion_localization.json`,
  `outputs/lesion_localization_segdet/lesion_localization.json`.
- **Follow-ups:** **no pipeline number is now measured on the superseded detector.** The
  bone-loss domain-shift failure is the one open technical problem, and 2026-08-27h established
  it is *not* upstream — the DENTEX+Tufts combined-training lever remains untried.

---

## 2026-08-27j — `docker build` executed for the first time; the demo runs, and the image is not what it claims

- **What was done:** Started Docker Desktop on the Windows machine and ran `docker build` — the
  first time it has ever executed in this project (`transfer.md` §3 item 7, open since the
  deployment work landed on 25 Aug; every prior session found no daemon). Then ran the container
  and verified the app actually loads, which is a **separate** check the Dockerfile's own comment
  warns is easy to skip.
- **RESULT: the build completes and the demo works.** Image `opg-demo`, 12 layers, CMD correct.
  Container started, `/_stcore/health` healthy, Streamlit rendered the upload widget
  ("Upload an OPG … 200MB per file • PNG, JPG"), and **all seven checkpoints loaded inside the
  container** — no `-v` mounts needed, since every one is now on local disk and `COPY models/`
  bakes them in. Logs clean apart from a benign Ultralytics config-dir warning.
- **Runtime verification inside the container** (the checks that matter, not just a green build):

  | check | result |
  |---|---|
  | `import cv2` | **4.11.0** — so `libgl1`/`libglib2.0-0` are correct |
  | `import torch` | **2.13.0+cu130**, `cuda_available: False` |
  | `import numpy` | **1.26.4** — the `<2` pin held |
  | `scipy.optimize.linear_sum_assignment` | works — the Hungarian FDI assignment numpy 2.x silently breaks |

- **DEFECT 1 — the image is NOT CPU-only, though the Dockerfile says it is.** Its comment reads
  *"CPU-only image, deliberately … A CUDA base image would roughly 5x the build size for no
  inference-time benefit."* The reasoning is right and the **base image** is indeed not CUDA —
  but nothing pins a CPU-only wheel index, so pip resolved the **CUDA** torch build and pulled
  ~2 GB of NVIDIA libraries: cublas 423 MB, cudnn 366 MB, cufft 214 MB, nccl 206 MB, cusolver
  201 MB, cusparselt 170 MB, cusparse 146 MB, nvrtc 90 MB, plus six more. **`torch` reports
  `2.13.0+cu130` with `cuda_available: False`** — a CUDA build that can never use CUDA. The
  stated intent was never enforced; the fix is an explicit
  `--index-url https://download.pytorch.org/whl/cpu`.
- **DEFECT 2 — torch is unpinned, so the container does not run the version any result was
  measured on.** `requirements.txt` says `torch>=2.0.0` with no upper bound; the image resolved
  **2.13.0**, while every published number in this repo was produced on **2.2.0**
  (`transfer.md` §8). `numpy` is correctly pinned `<2`; torch is not. The deployment artefact is
  therefore not reproducible against the measurements it demonstrates.
- **Also worth noting:** `jupyter` and `ipykernel` are installed into an image whose only job is
  to run Streamlit, and `.dockerignore` excludes `data/` and `_repo_archive/` but nothing inside
  `models/` — so `models/11/run/` and `models/06/last.pt`, which inference never reads, are
  baked in. Build context is 608 MB of models, of which roughly half is unused run artefacts.
- **A self-inflicted detour worth recording, because the lesson is general.** The first build's
  CLI appeared to hang for ~25 minutes after printing `naming to … done`. It was not hung: the
  final `unpacking to docker.io/library/opg-demo:latest` step takes **591.8 s** for an image this
  size, and BuildKit prints nothing while it runs. Killing the CLI there left the image config
  committed but its layer snapshots incomplete — `docker image inspect` succeeded while every
  `docker run` hung, which looked exactly like a broken daemon. What disproved that: **running an
  unrelated pre-existing image (`nginx`) worked fine**, isolating the fault to this image. A
  clean rebuild fixed it. *Lesson: a silent step is not a hung step, and the way to tell a
  broken environment from a broken artefact is to try a known-good artefact in the same
  environment.*
- **Source:** build log in the session scratchpad; `docker images opg-demo`;
  `docker exec opg-demo-run python -c "import cv2, torch, numpy …"`; browser render of
  `http://localhost:8501` showing the upload widget.
- **Follow-ups:** (1) pin torch and switch to the CPU wheel index — both change the deployment
  artefact and need a rebuild to re-verify, so they are proposed, not silently applied.
  (2) Consider excluding `models/*/run/` and `*/last.pt` from the build context.
  (3) `docker system df` reports 17.67 GB of images and 8.67 GB of build cache on this machine;
  a prune is worth discussing separately.

---

## 2026-08-27k — Both Dockerfile defects fixed and re-verified; image 11.2 GB → 4.69 GB

- **What was done:** Applied the two fixes 2026-08-27j proposed, rebuilt, and re-verified the
  running app. Both defects were things the Dockerfile *claimed* but did not enforce.
- **Fix 1 — the image is now actually CPU-only.** Torch is installed **first**, pinned, from
  `--index-url https://download.pytorch.org/whl/cpu`. Order is the mechanism: once torch and
  torchvision are satisfied, the later `pip install -r requirements.txt` (which asks only for
  `torch>=2.0.0`) leaves them alone instead of resolving the CUDA build from PyPI. Confirmed in
  the build log — **no `nvidia_*` CUDA runtime wheels at all** this time. The single remaining
  `nvidia` hit is `nvidia_ml_py` (53 kB), NVIDIA's management-library bindings pulled by
  ultralytics for GPU monitoring; it is not a CUDA runtime library.
- **Fix 2 — torch pinned to 2.2.0**, the version every published number was measured on
  (`transfer.md` §8). **Pinned in the Dockerfile, not `requirements.txt`, deliberately:** the two
  development machines currently run different torch versions (2.2.0 on macOS, 2.13.0+cpu on
  Windows) and both pass the full suite, so `requirements.txt` stays the permissive dev spec
  while the *image* — the artefact that has to be reproducible against published results — is
  exact. Verified along the way that torch 2.2.0 has a cp312 wheel (the base image is
  python:3.12-slim) and that ultralytics does not force a newer torch.
- **The part that outlasts this fix — the intent is now ENFORCED, not commented.** A build-time
  guard asserts the torch wheel is not a CUDA build, that numpy is 1.x, and that
  `scipy.optimize.linear_sum_assignment` actually runs, so the **build fails** rather than the
  defect surfacing later in a running container. Both failure modes it covers were previously
  silent: the CUDA wheel was detectable only by reading `torch.__version__` inside a live
  container, and numpy 2.x breaks the Hungarian FDI assignment at import rather than erroring
  loudly. It is written as `python -c` rather than a `RUN` heredoc on purpose — heredocs need
  the BuildKit 1.4+ frontend via a `# syntax` directive this Dockerfile does not carry.
  Guard output, from the build itself:

      #12 3.376 OK torch 2.2.0+cpu | numpy 1.26.4 | hungarian works

- **RESULT:**

  | | before | after |
  |---|---|---|
  | Image size | **11.2 GB** | **4.69 GB** (−58%) |
  | torch | 2.13.0+**cu130**, `cuda_available: False` | **2.2.0+cpu** |
  | pip layer (requirements) | 534.7 s | **102.2 s** |
  | Final unpack step | 591.8 s | **127.2 s** |

  Both sizes are complete builds measured the same way, so the comparison is like-for-like. (The
  3.9 GB figure quoted in 2026-08-27j was the *interrupted* image and is not a valid baseline.)
- **Re-verified running, not just built:** container healthy in ~3 s, `cv2` 4.11.0,
  `torch 2.2.0+cpu`, `numpy 1.26.4`, streamlit 1.62.0; all seven checkpoints loaded inside the
  container; Streamlit rendered the upload widget ("Upload an OPG … 200MB per file • PNG, JPG");
  container logs free of any traceback, error or load failure.
- **NOT done, deliberately:** `jupyter` and `ipykernel` are still installed into an image whose
  only job is serving Streamlit — the build log shows the full jupyterlab/jupyter-server/
  argon2-cffi tree being pulled. Removing them means changing `requirements.txt`, which is the
  shared dev spec for both machines, so it is a separate decision rather than a Dockerfile
  tweak. Likewise `.dockerignore` still ships `models/*/run/` and `models/06/last.pt`, which
  inference never reads (~300 MB of the 608 MB models context).
- **Source:** `Dockerfile`; build log in the session scratchpad; `docker images opg-demo`;
  `docker exec opg-demo-run python -c "import cv2, torch, numpy, streamlit"`; browser render of
  `http://localhost:8501`.
- **Follow-ups:** the two items above (`jupyter` in the image, `models/*/run/` in the build
  context) are the remaining known bloat, both requiring a decision outside the Dockerfile.

---

## 2026-08-27l — jupyter removed from the demo image; 4.69 GB → 4.4 GB

- **What was done:** Removed `jupyter` and `ipykernel` from the deployment image. 2026-08-27k
  had listed this as deliberately not done, because it looked like it required editing
  `requirements.txt`, which is the shared dev spec. It does not — the image now installs a
  **derived subset** instead.
- **Checked before removing, not assumed:** nothing in `app.py`, `src/` or
  `scripts/run_inference.py` imports `jupyter`, `ipykernel` or `IPython`, and the image's only
  job is `streamlit run app.py`. Meanwhile the repo tracks **12 notebooks** under `notebooks/`,
  so `requirements.txt` must keep both packages for development.
- **How — filtered, not duplicated.** The Dockerfile derives the deploy set at build time:

      RUN grep -vE '^(jupyter|ipykernel)([<>=!~]|$)' requirements.txt > /tmp/requirements-deploy.txt           && pip install --no-cache-dir -r /tmp/requirements-deploy.txt

  **A second `requirements-deploy.txt` was deliberately NOT created.** It would be a second
  source of truth that drifts from the first — precisely the failure mode this repo keeps
  finding in its own documentation, and the reason `regenerate_split_v1.py` derives the frozen
  split from code rather than carrying a copy. Deriving means a new dependency is picked up
  automatically and only the explicit exclusions need maintaining. The step echoes the filtered
  list into the build log, so what was installed is always on the record.
- **Guard extended in the same commit** — it now also asserts `notebook` and `jupyterlab` are
  unimportable, **and** that every runtime import still resolves (`cv2`, `streamlit`,
  `ultralytics`, `sklearn`, `pandas`, `yaml`, `PIL`). That second half matters more than the
  first: if the filter ever over-matches and strips something the app needs, the **build** fails
  instead of the container. Guard output:

      #12 5.188 OK torch 2.2.0+cpu | numpy 1.26.4 | cv2 4.11.0 | streamlit 1.62.0 | hungarian works | no jupyter

- **RESULT: 4.69 GB → 4.4 GB (−290 MB).** The whole jupyterlab / jupyter-server / argon2-cffi
  tree is gone from the build log. Modest next to the −6.5 GB from the CUDA fix, but real, and
  it removes a notebook server from a deployment artefact — a smaller attack surface as much as
  a smaller image.
- **Re-verified running, not just built:** healthy in ~3 s; `cv2` 4.11.0, `torch 2.2.0+cpu`,
  `numpy` 1.26.4, `streamlit` 1.62.0, `ultralytics` 8.4.130; `jupyter present: False`,
  `ipykernel present: False`; all seven checkpoints loaded; Streamlit rendered the upload widget;
  logs free of any traceback or load failure.
- **Cumulative effect of 27j → 27l on the deployment image: 11.2 GB → 4.4 GB (−61%)**, and it
  now runs the torch version its results were measured on.
- **Source:** `Dockerfile`; build log in the session scratchpad; `docker images opg-demo`;
  `docker exec opg-demo-run python -c "…find_spec('notebook')…"`; browser render of
  `http://localhost:8501`.
- **Follow-ups:** one known bloat item left — `.dockerignore` still ships `models/*/run/` and
  `models/06/last.pt`, roughly 300 MB of the 608 MB models context that inference never reads.

---

## 2026-08-27m — The demo crashed on first real use; fixed, and a real inference now verified in-container

- **What happened:** the user uploaded an image to the containerised demo and it raised
  `TypeError: ImageMixin.image() got an unexpected keyword argument 'use_column_width'`
  (`app.py:111`). **The build was green and the page load was green** — the crashing line only
  runs *after* an upload, so every check made up to that point passed while the demo was broken.
  The Dockerfile's own comment warns about exactly this shape ("easy to miss if you only
  smoke-test the build, not the run") and the verification stopped one step short anyway.
- **Root cause — the same unpinned-dependency class as the torch defect (2026-08-27j).**
  `requirements.txt` said `streamlit>=1.30.0`; the image resolved **1.62.0**, where
  `use_column_width` has been REMOVED. Streamlit has churned this kwarg twice:
  `use_column_width` → `use_container_width` → `width`.
- **Why the obvious fix was rejected.** Swapping to `use_container_width` would have worked
  today, but st.image's own docstring in 1.62 says it "is deprecated and will be removed in a
  future release", so it would have fixed the crash and **re-armed the identical trap**. Both
  call sites now use `width="stretch"`, the current API. **`st.dataframe` at `app.py:126` had
  the same latent bug** — it was already on `use_container_width`, one release from breaking —
  and is fixed in the same change.
- **A second defect found while testing the fix: the demo was printing a superseded number to
  users.** `run_inference.py` line 384 hardcoded *"Stage 2 = 46.5% end-to-end"* while
  `STAGE2_FDI_EXACT_END_TO_END = 0.583` sat 300 lines above it — updated on 27 Aug, but the
  `print()` literal beside it was not. The JSON written alongside was correct; only the
  human-facing text was stale. **Now derived from the constant** (`~42% of FDI codes are
  expected wrong (Stage 2 = 58.3% end-to-end)`), so it cannot drift again. The same stale pair
  was in `run_inference.py`'s module docstring and `app.py`'s header; both corrected.
- **Prevention, enforced rather than documented:** `requirements.txt` floor raised to
  `streamlit>=1.62.0`, and the Dockerfile guard now **binds `width="stretch"` against both
  `st.image` and `st.dataframe` at build time**, so a future removal of that kwarg fails the
  BUILD instead of surfacing at upload:

      OK torch 2.2.0+cpu | numpy 1.26.4 | cv2 4.11.0 | streamlit 1.62.0 | hungarian works | no jupyter | st width API ok

- **VERIFIED WITH A REAL INFERENCE THIS TIME, not a page load.** Ran the full six-stage pipeline
  inside the container on a real DENTEX radiograph (`disease/input/test_0.png`, 2829×1316):

  | | |
  |---|---|
  | teeth detected | **28** |
  | assessable | 24 |
  | distinct FDI codes | 28, **duplicates 0** |
  | caries-positive | 7 |
  | bone-loss-positive | 0 |

  **`duplicates 0` is the meaningful one** — it means `scipy.optimize`'s Hungarian assignment ran
  correctly under the pinned numpy 1.26.4, i.e. the invariant the `numpy<2` pin exists to protect
  was verified *in the deployment artefact*, not inferred from the dev environment. A valid
  report JSON (schema_version, summary, 28 tooth records, models, limitations) and a 1.0 MB
  overlay were written; the overlay renders correct boxes, FDI labels and CARI/DEEP flags. The
  report's `limitations` block correctly carries `stage1_detector_recall 0.706` and
  `stage2_fdi_exact_end_to_end 0.583`.
- **The Streamlit calls themselves were exercised**, not just signature-checked: both fixed calls
  were run through `streamlit.testing.v1.AppTest` inside the container —
  `exception raised: NONE`. That harness raises exactly as the user's upload did.
- **Lesson, and it is the same one this repo keeps paying for:** *a green build and a green page
  load are not a working app.* The check that mattered was the one nobody had run — feeding it a
  real image. Every stage of this session's Docker work (build completes → container starts →
  app loads) passed while the app was broken at the first thing a user would do.
- **Source:** `app.py`, `scripts/run_inference.py`, `requirements.txt`, `Dockerfile`; container
  run of `scripts/run_inference.py --image /tmp/test_0.png`; AppTest render probe.
- **Follow-ups:** unchanged — `.dockerignore` still ships `models/*/run/` and
  `models/06/last.pt` (~300 MB of unused build context).

---

## 2026-08-27n — DECISION: bone-loss domain shift is reported as a limitation, not fixed

- **What was decided:** the bone-loss branch's out-of-domain collapse is written up as a
  **measured limitation** (`PAPER_MATERIAL.md` §8.13) rather than attacked before the 14 Oct
  freeze. User decision, 27 Aug 2026. This closes `transfer.md` §3 item 4 as a work item and
  §4's "what approach?" pending decision.
- **Metrics:** no new measurement — this decision rests entirely on numbers already in the log.
  Tufts in-domain **0.9233 macro-F1** (1,558 val crops, 59 diseased, real prevalence); DENTEX
  fires on **0.7%** of detected teeth; Ningxia **2.4%** affected-tooth sensitivity pooled over
  6,791 affected teeth across four hospitals (2026-08-27h).
- **The reason a fix was not attempted, which is the substantive part.** The obvious lever was
  the DENTEX+Tufts combined training that gave Stage 2 **+21.5 points out-of-domain**
  (2026-08-25j). **It does not transfer: DENTEX carries no bone-loss labels.** Stage 2 could be
  trained on two corpora because both label FDI codes; this project has no second corpus with
  periodontal bone-loss annotation. That was checked against the DENTEX finding taxonomy
  (`lesion_localization.py`'s docstring: the eight finding types are caries, curettage, root
  canal, extraction, impacted, periapical lesion, fracture, healthy — none is alveolar bone
  loss). The remaining options — domain-generalisation training on Tufts alone, weak supervision
  from `küretaj` (periodontal curettage) treatment markers, or acquiring an annotated
  periodontal corpus — are research programmes, not fixes, and none fits the remaining schedule.
- **Why this is defensible rather than an omission.** The failure is measured on **two
  independent external datasets** with different GT formats and different metrics, and its cause
  has been **localised by experiment**: the 27 Aug detector swap moved Stage 2 by +12.0 points
  and caries by +7.7 and bone loss by **nothing** (168 → 165 teeth flagged while the denominator
  grew 9%), falsifying the standing hypothesis that the detector and bone-loss branch failed
  out-of-domain for a shared Tufts-trained reason. A reported limitation backed by a falsified
  causal hypothesis is a stronger contribution than a hurried fix would have been.
- **Key insight for the paper:** an in-domain 0.92 macro-F1 on a periodontal task is **not
  evidence of a usable periodontal model**, and this work shows that with external measurement
  rather than assertion — matching the shape of DPML's published 95.06 → 61.83 mAP gap
  (2026-08-26a). The takeaway a reader should leave with is that single-dataset periodontal
  results in this literature are not transferable, evidenced rather than asserted.
- **Operational consequence, already live:** every inference emits
  `report["limitations"]["bone_loss_domain_shift"]`, so no report can present a bone-loss finding
  without the caveat attached. Verified present in the in-container run today (2026-08-27m).
- **Source:** `PAPER_MATERIAL.md` §8.13 (new); prior measurements 2026-08-25d, 2026-08-27h.
- **Follow-ups:** none for bone loss — it is now a writing task, not an experiment. The freed
  capacity goes to the caries re-run block (T0.2/T0.3/T0.4), which is unblocked as soon as the
  DENTEX fetch completes.

---

## 2026-08-27o — DENTEX fetched (1,393 files); environment rebuilt; two invariants now run

- **What was done:** fetched the DENTEX subsets this repo actually uses, and rebuilt the local
  Python environment after the 3.11 install lost its interpreter mid-session.
- **Data:** **1,390 images + 3 annotation JSONs, 6.0 GB**, every file integrity-checked on
  download — 705 `quadrant-enumeration-disease/xrays` (caries cascade source),
  634 `quadrant_enumeration/xrays` (Stage-2 head), 51 `validation_data/.../xrays` (extern50).
  `quadrant/xrays` (693) and `unlabelled/xrays` (1,571) deliberately skipped: `data/README.md`
  records both as unused, so ~8,875 of the drive's 10,781 entries were never transferred.
- **THE RESULT THAT MATTERS — two invariants that had always SKIPped now RUN, and one of them
  reproduces a published number:**

      leakage exclusion list   OK   85 enumeration + 1 detector, 86 excluded total — matches disk
      caries v3 MD5 join       OK   260 shared images, FDI agreement 98.28%

  **98.28% is the exact figure recorded on 2026-08-25a**, now reproduced from a freshly
  downloaded copy of the dataset, on a different Python version, in a rebuilt environment. That
  is stronger evidence for the MD5-join method than the original measurement was: it rules out
  local state as the explanation.
- **Environment, rebuilt:** Python **3.13.7**, numpy **2.5.2**, scipy 1.18.1, torch **2.8.0+cpu**,
  ultralytics 8.4.130, opencv 4.11.0, streamlit 1.62.0. **79/79 tests pass, all invariants hold.**
- **A trap worth recording: Python 3.13 cannot satisfy `requirements.txt`'s `numpy<2` pin.**
  There is no numpy 1.x wheel for cp313 (`pip download "numpy<2" --only-binary=:all:` →
  *No matching distribution found*), so pip silently builds it **from source** with MSYS2's
  MinGW-W64 toolchain. The result imports with *"CRASHES ARE TO BE EXPECTED - PLEASE REPORT
  THEM TO NUMPY DEVELOPERS"* and emits `invalid value encountered in exp2 / nextafter / log10`
  from `getlimits`. Replaced with a numpy 2.x binary wheel per `transfer.md` §8's own note that
  the real constraint is ABI-matching torch/scipy/sklearn, not the number 2. **On 3.11/3.12 the
  literal pin is satisfiable; on 3.13 it is not.**
- **Two bugs of mine, both in the fetcher, both found by improving its error reporting first.**
  (1) It failed 3 files while naming neither the files nor a reason, because `FAILED` was printed
  only from the exception branch and these took the non-raising path. (2) With reporting fixed,
  the cause was immediate: downloads land in a `.part` temp file and `verify()` chose its check
  by **file suffix**, so `train_quadrant_enumeration.json.part` went down the image branch and
  was opened with PIL. The 1,390 images were unaffected only because PIL ignores extensions —
  which is exactly why precisely the 3 JSONs failed. *A failure counter without a reason is not a
  diagnostic; fixing the logging found the bug in one run.*
- **Also fixed:** the JSONs are mirrored to both locations their two consumers expect
  (`data/dentex/raw/` for `build_dentex_crops.py`, the DENTEX tree for `verify_invariants.py`),
  from a single download; and **`pytest` was added to `requirements.txt`** — `transfer.md` §8's
  fresh-clone checklist told you to run the suite, but a clean install could not.
- **Source:** `scripts/dentex/fetch_dentex_subsets.py`; `verify_invariants.py` output above.
- **Follow-ups:** the caries re-run block (T0.2/T0.3/T0.4) is now unblocked on this machine.

---

## 2026-08-27p — First confidence intervals in this project; two of today's claims do not survive them

- **What was done:** cluster-bootstrap 95% CIs for every headline metric that has saved per-item
  outputs. `scripts/eval/bootstrap_ci.py`, 10,000 resamples, seed 42. Closes the first half of
  `PAPER_MATERIAL.md` §9's "confidence intervals for every headline metric", which was **blocking**
  and had **no** coverage at all: until today not one number in this project carried an interval.
- **The methodological choice that matters: resample IMAGES, not teeth.** The 936 Stage-2 teeth
  come from 164 radiographs and are **not independent** — teeth in one image share a patient,
  scanner, exposure and operator, and errors cluster within an image (off-by-one FDI errors
  propagate across a quadrant, 2026-08-27e). A tooth-level bootstrap would treat 936 correlated
  observations as 936 independent ones and report intervals far too narrow. n is 164, not 936.

| Metric | Point | 95% CI | n (images) |
|---|---|---|---|
| Detection recall | 70.6% | **[66.5, 74.6]** | 164 |
| **FDI exact, end-to-end** | **58.3%** | **[53.9, 62.8]** | 164 |
| FDI exact, of detected | 82.6% | **[79.1, 85.8]** | 164 |
| Lesion agreement (DENTEX internal) | 44.3% | **[39.0, 49.3]** | 148 |
| Caries agreement — Ningxia test1 | 28.8% | **[23.3, 34.6]** | 134 |
| Caries agreement — Ningxia test2 | 51.3% | **[44.0, 58.5]** | 110 |
| Caries agreement — Ningxia test3 | 40.1% | **[31.9, 48.3]** | 40 |
| Caries agreement — Ningxia test4 | 41.9% | **[33.1, 50.8]** | 53 |
| Caries agreement — pooled *(scale only)* | 40.8% | **[37.0, 44.8]** | 337 |

- **PAIRED DELTAS — and this is where two of today's claims fail.** Same resampled image set for
  both arms, bootstrapping the difference:

| Paired delta (seg − bbox detector) | Point | 95% CI | Verdict |
|---|---|---|---|
| **FDI exact, end-to-end** | **+12.1 pp** | **[+6.8, +17.2]** | **excludes 0 — real** |
| **Caries agreement, Ningxia pooled** | **+7.7 pp** | **[+3.3, +12.0]** | **excludes 0 — real** |
| Detection recall | +3.3 pp | [−1.5, +8.0] | **INCLUDES 0 — not significant** |
| Lesion agreement (DENTEX internal) | +2.3 pp | [−3.4, +7.9] | **INCLUDES 0 — not significant** |

- **⚠️ CORRECTION to 2026-08-27e and 2026-08-27i.** Both were reported earlier today as gains:
  - *"Detection recall 67.3% → 70.6% (+3.3 pp)"* — the CI is **[−1.5, +8.0]**. **Not
    distinguishable from zero.** It should not be stated as an improvement.
  - *"Lesion localisation 42.0% → 44.3% (+2.3 pp)"* — the CI is **[−3.4, +7.9]**. **Also not
    significant.** 2026-08-27i's framing of it as the swap "paying off" internally is withdrawn.
  Neither point estimate changes; what changes is that neither supports a claim.
- **What this does to the story — it sharpens it rather than weakening it.** The interesting
  result was always that end-to-end FDI moved 12 points while detections/image *fell*. That is now
  statistically supported from both sides: **the end-to-end gain is real (+12.1 pp, excludes 0)
  while the recall gain is not (+3.3 pp, includes 0)**. The improvement therefore cannot be
  attributed to finding more teeth — it comes from finding *fewer wrong* ones. A precision effect,
  not a recall effect, now with evidence rather than inference.
- **And it sharpens §8.12a's internal/external claim.** Internal lesion agreement moved +2.3 pp
  (**not** significant); external Ningxia caries moved +7.7 pp (**significant**). The detector swap
  demonstrably helped out-of-domain data and demonstrably did not help in-domain — the same
  asymmetry as the head-v2.0 result (2026-08-25j), now with intervals.
- **A bug caught by disagreeing with a known number.** The first run reported the pooled Ningxia
  delta as **+10.9 pp** against a measured **+7.7** (2026-08-27h). Cause: the paired arms were
  keyed on image *name*, and Ningxia filenames **repeat across splits** — `test1/1.png` and
  `test2/1.png` are both `1.png` — so four hospitals collapsed into one and the arms mis-paired.
  Re-keyed on `(category, split, image)`; the delta then reproduced +7.7 exactly. *A number that
  disagrees with a reference is a bug until proven otherwise.*
- **NOT covered, stated so it is not mistaken for complete:** (1) **Ningxia periodontitis** —
  `ningxia_external.py` stores affected-tooth counts per split only, never per image, so there is
  no cluster to resample; not recomputed, because that would spend a touch on locked external data
  for a logging omission. (2) **Detection mAP@0.5 and both ResNet18 classifiers** — no per-item
  prediction dumps exist, so their intervals need a re-evaluation pass that writes per-image
  scores. §9's checklist item is therefore **partially** closed, not fully.
- **Source:** `scripts/eval/bootstrap_ci.py`, `outputs/bootstrap_ci/bootstrap_ci.json`.
- **Follow-ups:** add per-image prediction dumps to the classifier and detector eval paths so the
  remaining intervals can be computed without re-touching locked data.

---

## 2026-08-27q — Caries gate calibration measured: systematically overconfident, ECE 0.136

- **What was done:** first calibration and precision-recall analysis in the project, on the frozen
  `caries-gate-resnet18-v3.0` over its **held-out test split (863 crops, 14.7% prevalence)**.
  `scripts/eval/calibration_pr.py`. Every inference this pipeline emits carries a
  `caries_uncalibrated` flag; that flag was an assertion until today and is now a measurement.
- **Prerequisite, and it reproduced exactly:** `crops_v3_phase1` was rebuilt from the freshly
  fetched DENTEX with the committed `build_caries_phase1_v3.py` — the same script that produced
  the shipped gate's data. Composition matched the record to the crop: MD5-join agreement
  **98.28%**, train 723/4,027, val 199/804, **test 863**, 5,366 healthy negatives, 6,616 total.
  `verify_invariants.py`'s **caries v3 dataset hygiene** check consequently now RUNS rather than
  SKIPs — the third invariant activated by having DENTEX local.

  | | |
  |---|---|
  | Average precision | **0.550**, 95% CI **[0.445, 0.660]** |
  | Chance (= prevalence) | 0.147 |
  | **ECE** | **0.136** |
  | MCE | 0.596 |
  | Brier | 0.137 |

  CI is a **cluster bootstrap over source images** (not crops), 10,000 resamples, seed 42 — same
  independence argument as 2026-08-27p.

- **THE FINDING: the gate is systematically OVERCONFIDENT, not merely imprecise.** Every
  reliability bin sits **below** the diagonal — at a predicted P(caries) of 0.85 the observed
  frequency is **0.26**. The model's probabilities cannot be read as probabilities at all, in
  either direction, across the whole range. This is a different and more actionable statement
  than "precision is 0.40": it says the *scores* are broken, not just the *decisions*, and it
  points at a cheap fix (temperature scaling or Platt on the val split) that no retraining
  requires.
- **AP 0.550 against a 0.147 chance line is genuinely informative — 3.7x chance.** Worth stating,
  because "precision 0.40" alone reads as a coin-flip and understates what the model knows. The
  ranking is decent; the calibration and the operating point are what fail.
- **The operating point is now a defended choice rather than an inherited default.** The pipeline
  uses `argmax`, i.e. threshold 0.50. The sweep shows that is very close to **F1-optimal**:

| Threshold | Flagged | Precision | Recall | F1 |
|---|---|---|---|---|
| 0.30 | 319 | 0.339 | 0.850 | 0.484 |
| 0.40 | 266 | 0.376 | 0.787 | 0.509 |
| **0.50 — pipeline default (argmax)** | **236** | **0.398** | **0.740** | **0.518** |
| 0.60 | 195 | 0.420 | 0.646 | 0.509 |
| 0.75 | 116 | 0.534 | 0.488 | 0.510 |
| 0.90 | 65 | 0.692 | 0.354 | 0.469 |
| 0.95 | 27 | 0.778 | 0.165 | 0.273 |

  So the inherited default happens to be the right F1 choice — but that was never verified before,
  and the sweep also shows what is purchasable: **precision 0.40 -> 0.69 by moving to 0.90**, at
  the cost of recall 0.74 -> 0.35. For a screening aid that is a real design lever, and the paper
  should present the curve rather than a single operating point.
- **Why the caries gate and not the bone-loss classifier, which is what §9's checklist names.**
  Both need per-item probabilities that were never saved; only caries rebuilds *exactly*. The
  bone-loss metadata carries `filename,label,stem` and **no bounding boxes**, so its 1.5x/2.0x
  crops would have to be reconstructed by hand from tooth ids against `teeth_bbox.json`. A silent
  crop-geometry mismatch is precisely what voided the R1 run (2026-08-27a) and here it would
  corrupt a calibration curve while looking entirely plausible. **Bone-loss calibration therefore
  needs a geometry-verified crop rebuild first, and was deliberately not attempted.**
- **Source:** `scripts/eval/calibration_pr.py`,
  `outputs/calibration/caries_gate_calibration_test.json`,
  `docs/results/figures/paper/caries_gate_calibration_test.png`.
- **Follow-ups:** (1) temperature-scale the gate on val and re-measure ECE — cheap, no retraining,
  and would let the pipeline report meaningful confidences. (2) Bone-loss calibration, after a
  verified crop rebuild. (3) §9's two calibration items remain open because they name bone loss.

---

## 2026-08-27r — Temperature scaling does NOT fix the caries gate; NOT adopted

- **What was done:** fitted a single temperature T on the caries gate's logits (Guo et al. 2017),
  **fitted on val (1,003 crops), evaluated once on test (863)** — never the reverse; fitting on
  test would be tuning on the test set, the same error this project refuses to make with Ningxia
  at a larger scale. `scripts/eval/temperature_scale.py`.
- **RESULT — it does not work, and it is NOT adopted:**

  | | before (T=1) | after (T=1.377) |
  |---|---|---|
  | **ECE** | **0.1362** | **0.1521 — WORSE by 12%** |
  | MCE | 0.5958 | 0.4329 — better |
  | Brier | 0.1365 | 0.1319 — better |
  | Average precision | 0.5500 | **0.5500 — identical, as required** |

  Val NLL did improve (0.4300 → 0.4147), so T was fitted correctly; **T = 1.377 > 1 confirms the
  overconfidence 2026-08-27q diagnosed.** It simply is not the right correction.
- **WHY it fails, which is the useful part.** Temperature scaling assumes the miscalibration is a
  uniform *scale* error — one knob softening every score. The reliability curve shows a *shape*
  error instead: across predicted 0.50–0.85 the observed frequency is essentially **flat at
  ~0.27**, then jumps to 0.69 in the top bin. A single scalar cannot flatten and re-bend a curve;
  softening merely slides every point left, which is why MCE and Brier improve while **ECE gets
  worse** — the already-decent low bins are dragged off the diagonal to buy improvement in the
  high ones.
- **Two correctness checks passed**, and they are why this negative result can be trusted:
  **AP is unchanged to four decimals** (0.5500 → 0.5500) — temperature scaling is a monotonic
  transform and *cannot* change ranking, so any movement would have meant a bug; and **every
  decision at threshold 0.5 is identical**, since `argmax(z/T) == argmax(z)` for T > 0.
- **Decision: not adopted.** The pipeline keeps T=1 and keeps stamping `caries_uncalibrated` on
  every tooth. Adopting a transform that worsens the headline calibration metric to improve two
  secondary ones would be choosing the metric to fit the result.
- **What this says for the paper.** *"The gate's miscalibration is structural, not a temperature
  effect."* That is a more informative statement than an unqualified "poorly calibrated", and it
  is evidence against the cheapest available fix rather than an untested assumption. The next
  candidates — isotonic regression or Platt scaling, both still monotonic and therefore still
  decision- and AP-preserving — have the capacity to fit a shape and are the honest next step.
  A plausible underlying cause worth stating: the negative class is 84.8% healthy teeth recovered
  by MD5 join from a *different* DENTEX subset, so the score distribution the gate learned may not
  be one a single scalar can repair.
- **Source:** `scripts/eval/temperature_scale.py`,
  `outputs/calibration/caries_gate_temperature.json`,
  `docs/results/figures/paper/caries_gate_temperature_scaling.png`.
- **Follow-ups:** isotonic regression fitted on val, same discipline. Bone-loss calibration still
  blocked on a geometry-verified crop rebuild (2026-08-27q).

---

## 2026-08-27s — Isotonic calibration works (ECE −68%) but flips 18% of verdicts; adopt for CONFIDENCE only

- **What was done:** isotonic regression on the caries gate's scores, **fitted on val (1,003
  crops), evaluated once on test (863)** — same discipline as 2026-08-27r.
  `scripts/eval/isotonic_calibrate.py`. It reuses `temperature_scale.py`'s preprocessing rather
  than reimplementing it: the transform is the risky part, and a second copy would mean comparing
  two different models.

  | | raw | isotonic |
  |---|---|---|
  | **ECE** | 0.1362 | **0.0430 — 68% better** |
  | MCE | 0.5958 | **0.3338** |
  | Brier | 0.1365 | **0.0977** |
  | Average precision | 0.5500 | **0.4996 — 5.0 points WORSE** |

- **It fixes what temperature scaling could not, and for the predicted reason.** 27r argued the
  miscalibration was a *shape* error beyond the reach of one scalar. Isotonic fits an arbitrary
  non-decreasing function, and the reliability curve now tracks the diagonal across the whole
  range instead of sitting flat at ~0.27. The diagnosis was right, and is now confirmed by a
  method that had the capacity to act on it.
- **TWO COSTS, and the second one governs adoption.**
  1. **AP drops 0.550 → 0.500.** Isotonic is only *weakly* monotonic; its flat regions turn
     distinct scores into ties, collapsing ranking resolution to **46 distinct values across 863
     test crops**. A genuine cost of the method, not a bug — unlike temperature scaling, where AP
     invariance was a correctness check (27r).
  2. **155 of 863 verdicts flip at threshold 0.5 — 18.0% of all decisions.** Isotonic remaps the
     score axis, so the 0.5 cut lands elsewhere in raw-score space.
- **DECISION: adopt for reported CONFIDENCE, not for the verdict. Not yet wired.**
  Adopting it for decisions would change 18% of caries calls and invalidate **every downstream
  caries number** — the in-pipeline caries rate (19.1%), the DENTEX lesion agreement (44.3%), and
  the four Ningxia hospital figures, the last of which would cost another touch on locked external
  data. The calibration benefit does not justify that. **Applying isotonic only to the reported
  probability, while the verdict stays `argmax` on the raw logits, keeps every published number
  exactly as measured and still gives meaningful confidences (ECE 0.043).** One presentational
  wrinkle to state honestly if wired: a tooth can then be labelled `caries` while carrying a
  calibrated confidence below 0.5.
- **Overfitting reported rather than hidden.** In-sample val ECE falls to **0.0016** — essentially
  perfect, which is what an over-flexible fit looks like in-sample and is *not* evidence of
  anything. The number that matters is out-of-sample: **test ECE 0.0430**. It generalises, but the
  27x in-sample/out-of-sample ratio belongs in the record rather than the val figure being quoted.
- **For the paper:** the calibration story now has a shape — *miscalibrated (ECE 0.136) →
  temperature scaling insufficient because the error is structural → isotonic recovers it
  (ECE 0.043) at the cost of 5 AP points and 18% of decisions.* That is a better methods section
  than any single number, and it documents a real trade-off instead of presenting a fix as free.
- **Source:** `scripts/eval/isotonic_calibrate.py`,
  `outputs/calibration/caries_gate_isotonic.json`,
  `docs/results/figures/paper/caries_gate_isotonic.png`.
- **Follow-ups:** wire confidence-only isotonic into `run_inference.py` if the presentational
  wrinkle is acceptable; bone-loss calibration still blocked on a geometry-verified crop rebuild.

---

## 2026-08-27t — Confidence-only isotonic wired into the pipeline; verdicts verified unchanged

- **What was done:** wired 2026-08-27s's isotonic calibrator into `src/classifiers.run_caries`,
  applied to the **reported confidence only**. Schema `opg-report/1.0` → **1.1** (additive).
- **The calibrator is stored as KNOTS, not a pickle** —
  `models/09_caries_gate_v3/isotonic_calibrator.json`, 28 (x, y) pairs applied with
  `numpy.interp`. sklearn's `IsotonicRegression.predict` is exactly linear interpolation between
  `X_thresholds_`/`y_thresholds_` with end clipping, so this reproduces the fit with no sklearn
  dependency and no version coupling — and unlike a pickle it is readable, diffable and hashable.
- **A round-trip guard caught a real defect before anything was wired.** The first export rounded
  the knots to 6 dp and reproduced sklearn to only **1.89e-04**, above the 1e-5 bar, so the script
  printed `MISMATCH -- DO NOT WIRE`. Storing full float precision brought it to **6.03e-08**. A
  calibrator that cannot reproduce its own fit is a second source of truth; the bar was fixed
  rather than loosened.
- **VERDICTS VERIFIED UNCHANGED, not assumed.** Ran the pipeline on the same DENTEX image the
  containerised pre-patch build ran (`disease/input/test_0.png`) and diffed the reports:

      teeth 28 -> 28
      VERDICTS IDENTICAL: True   (0 differences)
      raw gate_confidence identical: True

  `gate_confidence` is deliberately left raw and untouched: `scripts/eval/lesion_localization.py`
  reads it, and every published caries number was measured against it, so its meaning must not
  move. The calibrated value is a **new** field, `gate_confidence_calibrated`.
- **What the calibrated numbers actually say, and it is uncomfortable in a useful way.** On that
  image, a tooth called `caries` at raw confidence **0.504** now reports a calibrated **0.285**.
  A positive verdict carrying a calibrated confidence below 0.5 is not a bug — it is the honest
  reading of a gate whose precision is 0.40, and it is exactly the signal the raw number was
  hiding. Also visible: many negatives collapse to identical values (0.9674), the isotonic
  step-function ties that cost 5 AP points in 27s.
- **Flags:** `caries_uncalibrated` **stays on every tooth** — it carries the precision-0.40 and
  presumed-negative caveats, which calibration does not address. `caries_confidence_isotonic` is
  added to mark that a calibrated field exists and which transform produced it. Conflating the
  two would have let a reader believe calibration fixed the precision.
- **Surfaced in the demo**, or the wiring would not reach a user: `app.py`'s per-tooth table gained
  a **"Caries conf (cal.)"** column showing the calibrated value, not the raw one.
- **Tests: 79 → 82.** The new ones assert the property that matters — the calibrator is monotonic
  and in [0, 1], a missing calibrator is a supported state rather than an error, and **the verdict
  follows the raw probability across the whole [0, 1] range**. That last one is the regression
  guard against someone later "simplifying" the code by recomputing the verdict from the
  calibrated score.
- **Source:** `src/classifiers.py`, `scripts/run_inference.py`, `app.py`,
  `models/09_caries_gate_v3/isotonic_calibrator.json`, `tests/test_classifiers.py`.
- **Follow-ups:** bone-loss calibration still blocked on a geometry-verified crop rebuild
  (2026-08-27q). The container image predates this change and would need a rebuild to serve it.

---

## 2026-08-27u — Bone-loss crop rebuild attempted and REJECTED by its own geometry check

- **Goal:** rebuild the bone-loss validation crops so the three §9 items that need them —
  calibration, a PR/threshold sweep, and confidence intervals — could finally be measured.
  **Outcome: the rebuild does not reproduce, the guard caught it, and no number from it is
  published.** The blocker is now identified precisely instead of being "crops are missing".
- **Two independent reasons the reported bone-loss numbers cannot be reproduced on this machine.**

  **(1) Half the validation set is irreproducible by construction.** 773 of 1,558 val rows
  (**49.6%**) carry `_jit_` in the filename: §6.5's ±15% coordinate jitter was applied at
  dataset-construction time from an RNG **whose offsets were never saved**. Those pixels cannot
  be regenerated by anyone, on any machine. Only the **785 deterministic rows** (750 normal /
  35 diseased) are rebuildable at all, so the reported **0.9233 macro-F1 — computed over all
  1,558 — can never be recomputed**, only approximated on a different population.

  **(2) The source images are not here.** Reading
  `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb` settles what the crops were
  actually built from:

      RADIO_DIR = os.path.join(BASE, "Radiographs", "Radiographs")   # 1.JPG, 100.JPG, ...

  the **ORIGINAL, un-rotated** Tufts radiographs, with **no rotation applied anywhere in the
  notebook** and the documented 1.5x/2.0x expansion, `cv2.resize` to 224 with `INTER_LINEAR`.
  This machine holds only `Radiographs_rotated` and `Radiographs_rotated_fixed` — the 90°-turned
  copies made on 20 Aug for the *detector* work, which postdates the bone-loss crops.
  `data/tufts/ZIP/` has no `Radiographs/` directory at all.
- **What the attempt measured, and why it was rejected.** Crops were rebuilt from
  `teeth_bbox.json` with the documented expansion, against the radiograph directory chosen by
  *measurement* (`_tufts_align.pick_image_dir` → `Radiographs_rotated_fixed`, ratio 1.040 ALIGNED
  vs 0.964). The frozen Stage-4a model was then run over them as an oracle:

  | source frame | macro-F1 | sensitivity | confusion |
  |---|---|---|---|
  | as-is (portrait) | 0.4869 | **0.0000** | TN=745 FP=5 FN=35 **TP=0** |
  | rotated CCW | 0.5371 | 0.0857 | TN=732 FP=18 FN=32 TP=3 |
  | **rotated CW (best)** | **0.7145** | **0.4000** | TN=737 FP=13 FN=21 TP=14 |
  | *documented (full 1,558)* | *0.9233* | *0.8305* | *TN=1492 FP=7 FN=10 TP=49* |

  Visual inspection explained the first row immediately: the crops **are** the right teeth but
  **lying sideways** — `teeth_bbox.json` is in the same 840x1615 portrait frame as the rotated
  radiographs, so boxes land correctly while every tooth is at 90°. Worse, the 1.5xW/2.0xH
  expansion assumes a tooth ~3x taller than wide, so in that frame it expands along the **wrong
  axes**. `pick_image_dir` passed it because that helper distinguishes 180°, **not 90°**.
  Rotating image and boxes together (one function, so pixels cannot rotate without their boxes)
  recovers most of it — but **0.40 sensitivity against a documented 0.83 is still divergent**,
  which is consistent with reconstructing from a rotated copy rather than the original.
- **DECISION: no calibration, CI or ablation number is reported from these crops.** The
  evaluation script prints
  `verdict: DIVERGENT -- suspect crop geometry, do not use these crops`, and that verdict is
  honoured. Had the geometry check been skipped, the run would have cheerfully produced
  **ECE 0.0394 / Brier 0.0497** and a clean reliability diagram from crops the model cannot even
  classify — the exact shape of the R1 failure (2026-08-27a), caught before publication rather
  than after.
- **This is the real blocker, and it is now specific:** bone-loss calibration, PR curve, CIs and
  all three §9 ablations need **`Radiographs/Radiographs/` — the original un-rotated Tufts
  radiographs** — which live on the macOS machine's `_repo_archive/datasets_workspace/` or in the
  Tufts Drive. With those, the 785 deterministic crops rebuild exactly; the 773 jittered ones
  never will, so any future bone-loss re-measurement is on a 785-crop subset and must say so.
- **Source:** `scripts/tufts/rebuild_bone_loss_crops.py` (new),
  `scripts/eval/bone_loss_eval.py` (new), `outputs/bone_loss_eval/`,
  `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`.
- **Also recorded:** the crop-name parser initially rejected 49 val rows and **refused to guess**.
  They were tooth ids like `TA`, `TC`, `TH` — Universal numbering uses **1-32 for permanent teeth
  and A-T for deciduous ones**, and `teeth_bbox.json`'s title vocabulary is exactly 32 numeric
  plus 20 lettered. Legitimate primary teeth, not corrupt names; the guard surfaced a real gap in
  my pattern rather than silently dropping 3% of the set.

---

## 2026-08-27v — Stage-2 failure taxonomy: the headline is detection-bound, and the errors are benign

- **What was done:** bucketed all 936 ground-truth teeth by *how* Stage 2 fails, from the
  already-saved `outputs/stage2_segdet/stage2_rows_head.json`. **No inference re-run, no test data
  re-touched** — pure analysis of a measurement that already happened.
  `scripts/eval/stage2_failure_taxonomy.py`. Answers `MASTER_PLAN_2026H2.md` W7's "failure
  taxonomy bucketed by confounder".

| Outcome | n | % of 936 GT teeth |
|---|---|---|
| **correct** | 546 | **58.3%** |
| **not_detected** (Stage 1 never found it) | 275 | **29.4%** |
| off_by_one (right quadrant, adjacent position) | 89 | 9.5% |
| same_quadrant_far (counting slip, 2+ positions) | 10 | 1.1% |
| mirror_lr (right arch + position, wrong SIDE) | 8 | 0.9% |
| wrong_arch (upper called lower, or vice versa) | 6 | 0.6% |
| other | 2 | 0.2% |

- **FINDING 1 — the 58.3% headline is a DETECTION number, not a numbering number.** 275 teeth
  (29.4%) are never detected and so can never be numbered. **Of the 661 teeth Stage 1 does find,
  Stage 2 numbers 82.6% correctly.** Those are two very different claims, and the paper has so far
  been reporting only the pessimistic composite. Both belong in the results.
- **FINDING 2 — the numbering errors that do occur are overwhelmingly benign.** Of 115 wrong codes
  on detected teeth, **89 (77.4%) are off-by-one**: right quadrant, adjacent position, usually the
  same tooth type. Only **16 of 661 detected teeth (2.4%)** suffer a *category* error —
  wrong arch (6), mirrored side (8), or other (2). For a screening aid, "26 called 27" and
  "upper-right molar called lower-left incisor" are not the same failure, and this is the first
  time the project can say which one it makes.
- **FINDING 3 — the off-by-one drift is not a systematic indexing bug.** Direction splits
  **53 mesial / 36 distal**. A clean one-sided lean would have implicated an off-by-one in the
  assignment code; a 60/40 split is consistent with genuine ambiguity at arch ends, not a defect.
  Worth checking, and worth reporting that it was checked.
- **FINDING 4 — first premolars are the hardest teeth, molars the easiest.** Wrong-code rate by
  position: **pos 4 = 41.7%** (of only 24 detected — small support, do not over-read), pos 5 =
  26.9%, positions 1–3 ≈ 18–20%, and **molars 6/7/8 = 13.0 / 14.9 / 14.3%** on much larger support
  (215 / 159 / 244 GT teeth). The counterintuitive direction — molars *easier* — is worth a
  sentence: they are large, distinctive and terminal, so they anchor the arch ordering.
- **FINDING 5 — the detector swap changed the SHAPE of the errors, not just the count.**

| Category | bbox control | seg detector | Δ |
|---|---|---|---|
| correct | 46.3% | **58.3%** | **+12.1 pp** |
| not_detected | 32.7% | 29.4% | −3.3 pp |
| off_by_one | 15.3% | 9.5% | −5.8 pp |
| same_quadrant_far | 2.1% | 1.1% | −1.1 pp |
| mirror_lr | 1.1% | 0.9% | −0.2 pp |
| **wrong_arch** | **2.4%** | **0.6%** | **−1.7 pp (a 75% reduction)** |

  **`wrong_arch` fell by 75%.** The seg detector did not merely find more teeth; it removed
  disproportionately many *category* errors. That is a stronger statement than "+12.1 points",
  and it is consistent with 2026-08-27p's interval result that the recall gain alone was not
  significant — the improvement is in the *quality* of the boxes, not the quantity.
- **Source:** `scripts/eval/stage2_failure_taxonomy.py`,
  `outputs/stage2_taxonomy/stage2_failure_taxonomy.json`,
  `docs/results/figures/paper/stage2_failure_taxonomy.png`.
- **Follow-ups:** the §9 failure-case *panel* item asks specifically for the bone-loss FN/FP crops
  with Grad-CAM, and remains blocked on the crop rebuild (2026-08-27u). A caries failure panel is
  buildable from `crops_v3_phase1` whenever wanted.

---

## 2026-08-27w — Caries failure panel: the gate is not confusing pathology, it is over-calling restorations

- **What was done:** scored the held-out caries test split (863 crops, 127 positive) with the
  frozen gate and bucketed every error by the `subtype` recorded in `crops_v3_phase1` — a
  confounder the manifest has always carried and nothing had used.
  `scripts/eval/caries_failure_panel.py`. Operating point is the pipeline's own
  (argmax == 0.50); **precision 0.398 / recall 0.740 reproduces the documented 0.40 exactly.**
  TP 94 · FP 142 · FN 33 · TN 594.
- **THE QUESTION THIS SETTLES.** The gate's negative class is 5,366 healthy + 179 impacted +
  22 periapical. The standing open question was whether its 0.40 precision comes from confusing
  *other pathology* for caries — which would mean the negative class needs a third label — or
  from over-calling *ordinary healthy teeth*. Answer:

| Negative subtype | n | false positives | FP rate |
|---|---|---|---|
| healthy | 714 | 137 | **19.2%** |
| impacted | 21 | 4 | **19.0%** |
| periapical | 1 | 1 | *100% (n=1, meaningless)* |

  **19.2% on healthy against 19.0% on impacted is the same number.** The gate is **not**
  confusing pathology-for-pathology; it is uniformly over-sensitive, and **137 of its 142 false
  positives (96.5%) are teeth labelled healthy.** That rules out "add a third class" as the fix
  and points the problem back at what the model considers caries-like texture.
- **What the panel shows, offered as an observation for a clinician to confirm rather than a
  finding I can certify.** Every one of the eight highest-confidence false positives is a
  `healthy` tooth at raw 0.95–0.99, and **several visibly carry restorations or root-canal
  fillings** — bright radiopaque material in the crown. If that reading holds, it connects
  directly to the documented presumed-negative assumption: DENTEX's "healthy" means *no disease
  annotation*, and **a restored tooth has already been treated for caries**, so it is not a clean
  negative at all. The gate may be right about the tooth's history and wrong about its label.
  **This needs a dentist's eye before it goes in the paper as a claim.**
  Figure: `docs/results/figures/paper/caries_failure_panel_test.png`.
- **False negatives run the other way, and that is worth reporting too:**

| Positive subtype | n | missed | FN rate |
|---|---|---|---|
| caries | 108 | 27 | 25.0% |
| deep_caries | 19 | 6 | **31.6%** |

  **`deep_caries` is missed MORE often than ordinary caries (31.6% vs 25.0%)** — the opposite of
  the intuition that deeper lesions are easier. Support is only 19 crops, so this is a flag for
  investigation, not a result. The missed cases in the panel are low-contrast and several appear
  poorly framed, with the crop catching mostly alveolar bone rather than the crown.
- **Captions carry raw AND calibrated confidence**, because 2026-08-27s showed the raw scores are
  systematically overconfident: a panel labelled only "raw 0.99" would overstate how sure the
  model was. Several false positives sit at calibrated 1.00 even so — those are genuinely
  confident errors, not borderline ones.
- **Source:** `scripts/eval/caries_failure_panel.py`,
  `outputs/caries_failure_panel/caries_failure_test.json`,
  `docs/results/figures/paper/caries_failure_panel_test.png`.
- **Follow-ups:** (1) have a clinician check whether the high-confidence false positives are
  restored teeth — if so, the negative class definition, not the model, is the defect worth
  writing up. (2) The `deep_caries` miss rate deserves a look once support allows.

---

## 2026-08-27x — Stage 3/4 figures regenerated from tracked artifacts; the curves show heavy overfitting

- **What was done:** regenerated the Stage-3 and Stage-4a figures §9 has wanted since the
  beginning. `scripts/figures/make_stage34_figures.py`. **Regenerated, not recovered:** the
  original PNGs sit in `_repo_archive/pes_capstone_report/figures/`, but copying them in would add
  pictures whose provenance is an un-rerunnable notebook. Every panel here is drawn from a
  **committed** artifact — `models/03/training_history.json` (32 epochs),
  `models/03/training_summary.txt`, `models/09_caries_gate_v3/results.json` — so both the figure
  and every number in it are traceable and reproducible from the repo alone.
- **Two figures written:** `stage4a_training_curves.png` (loss, validation F1 with the selection
  epoch marked, LR schedule) and `stage34_confusion_matrices.png` (bone-loss val, caries gate val
  and test). Best epoch resolves to **22**, matching `training_summary.txt` exactly.
- **A cross-check worth recording: the caries test confusion reproduces independently.**
  `results.json` records `[[94, 33], [142, 594]]` for the test split, and 2026-08-27w computed
  **TP 94 · FN 33 · FP 142 · TN 594** from crops rebuilt today, scored with the frozen gate.
  Identical. That is independent confirmation the `crops_v3_phase1` rebuild is faithful — the
  same class of check the bone-loss rebuild failed (2026-08-27u).
- **WHAT THE CURVES SHOW, and it is not flattering.** Train loss falls **0.126 → ~0.002** while
  validation loss flattens around **0.05 from roughly epoch 5 and never improves again** — a
  ~25x train/val gap. **The bone-loss binary model overfits heavily.** With 711 positive training
  crops (resampled, partly augmented duplicates of the same teeth) that is unsurprising, but it
  had never been *shown*, and it belongs in the paper beside the 0.9233.
- **The selection epoch was picked from a noisy curve, which biases the headline upward.**
  Diseased-class F1 swings between roughly **0.40 and 0.85 epoch to epoch**. With only **59
  validation positives** a single tooth moves F1 by ~1.7 points, so those swings are real
  sampling noise, not learning. Taking the maximum of such a curve is optimistically biased:
  **0.9233 is the best of 32 noisy draws, not a stable estimate.** Reporting it without that
  caveat overstates the model.
- **This connects the two things the project already knew.** A model that memorises its training
  positives and is selected on the peak of a noisy validation curve is exactly the model one would
  expect to collapse out of domain — and it does: 0.7% firing on DENTEX, 2.4% affected-tooth
  sensitivity on Ningxia (§8.13). The training curve is corroborating evidence for the
  domain-shift finding, not a separate complaint.
- **Also visible: the caries gate's precision degrades val → test**, 0.515 → 0.398 (macro-F1
  0.735 → 0.695). The val figure is the optimistic one; the test figure is the one to quote, and
  the pipeline already does.
- **NOT regenerated, and recorded rather than faked:** (1) **caries training curves** —
  `results.json` stores `best_epoch` and final metrics but **no per-epoch history**, so there is
  nothing to plot without inventing it; (2) **Stage 4b severity confusion matrix** —
  `severity_summary.txt` carries per-class F1 only (Mild 0.80 / Moderate 0.67 / Severe 0.70) and
  no matrix, on 52 crops. Both are printed by the script itself so the gap stays visible.
- **Source:** `scripts/figures/make_stage34_figures.py`,
  `docs/results/figures/paper/stage4a_training_curves.png`,
  `docs/results/figures/paper/stage34_confusion_matrices.png`.

---

## 2026-08-27y — Related-work comparison table built; only 2 of 49 comparable papers validate externally

- **What was done:** built §9's related-work comparison table from this project's own review
  sheet (`Dental X-Ray Capstone Literature Review.xlsx`, Sheets 3 and 5). 117 reviewed papers →
  **49 task-relevant** after de-duplication (tooth detection/numbering, caries, periodontal bone
  loss). Written into `PAPER_MATERIAL.md` §2.1; machine-readable extract at
  `outputs/related_work_extract.csv`.
- **THE HEADLINE, and it is now evidence rather than assertion:**

  | Validation design | n | % |
  |---|---|---|
  | **Genuine external / multi-centre** | **2** | **4%** |
  | Explicitly states it has none | 10 | 20% |
  | Internal split, CV, or unstated | 37 | 76% |

  Only two of the 49 validate externally: the two-step YOLOv8 DENTEX paper (*Informatica Medica
  Slovenica* 2024, external Slovenian clinic) and a periodontitis paper with multicentre plus two
  external cohorts. **This project's four-hospital Ningxia evaluation therefore puts it in a group
  of about three.** The claim that external validation is near-absent in this subfield has been
  made in planning documents for months; it is now counted.
- **A counting trap I nearly walked into, recorded because it inverts the result.** A keyword
  search for "external" returns **13** papers — but most contain the phrase only as
  *"no external validation"*. Taking that count would have reported 13 externally-validated papers
  when the true number is 2. The classifier now handles negation, and the §2.1 text warns the next
  reader explicitly. *Matching a keyword is not reading a field.*
- **Head-to-head table built on the datasets we actually use**, with our result beside each:
  the two-step YOLOv8 work (enumeration mAP 0.95; caries lesion sensitivity 0.70 internal → 0.67
  external), PLOS Digital Health's numbering accuracy 0.9988, a Tufts multi-stage system at
  mAP 66.2% / AP50 97.3%, and DPML's 95.06 → 61.83 in/out-of-domain gap.
- **Three reading traps written into the section so the comparison stays honest.** (1) The
  published *"numbering accuracy 0.9988"* classifies an already-cropped, correctly-detected tooth;
  our comparable figure is **82.6% of detected teeth**, not the **58.3%** end-to-end that includes
  detector recall — the paper must state both and say which compares to what. (2) **Our absolute
  numbers are lower than several published ones** (detection 0.810 vs a reported 0.95–0.97) and
  the paper should say so plainly; the contribution is external survival, intervals and error
  attribution, not peak accuracy. (3) The most useful row is the bone-loss comparator: an
  independent group reports **weighted F1 0.29 and severe-PBL F1 = 0 on Tufts** with clinician
  comparison, which makes §8.13's collapse a measured limitation of a hard task rather than a
  uniquely bad model.
- **Source:** `outputs/related_work_extract.csv`; `PAPER_MATERIAL.md` §2.1.
- **Follow-ups:** the narrative prose is still to write and is reusable from the archived
  `_repo_archive/pes_capstone_report/chapters/02_literature.tex`. §9's item is ticked for the
  table, with the prose noted as outstanding.

---

## 2026-08-27z — Ethics and licensing statement written; two compliance items still open, two licences unverified

- **What was done:** wrote `PAPER_MATERIAL.md` §8.19, the dataset ethics / licensing /
  de-identification statement ISBI requires, covering all four corpora with a pre-submission
  checklist. Closes §9's item as far as it can be closed — **the statement cannot be finalised
  until four things outside this repo are resolved.**
- **Tufts — terms recorded verbatim, and two distinct problems.** The release agreement forbids
  reproducing the database or posting it "into any webpage or any other storage means".
  (1) A Drive folder holding the raw `ZIP/` release was found **browsable without signing in** —
  squarely forbidden, unresolved, account-owner action. (2) Real Tufts pixels are embedded as
  base64 in **7 tracked notebooks already on `origin/main`**; the repo is private, so this is
  deferred risk by explicit user decision, but it blocks any public release. Different problems,
  different remedies, recorded separately so neither is mistaken for the other.
- **DENTEX and Ningxia licences are NOT verified, and the section says so rather than guessing.**
  Nothing in this repo records either licence — `EXTERNAL_DRIVE.md` says only that DENTEX
  "is a separate matter … check its own licence", and that check has never been done. Both are
  widely used public datasets so the expected answer is permissive, but **an ethics statement
  asserting a licence nobody read is exactly the kind of claim this project should not make.**
  Recorded as a pre-submission action instead.
- **Clinic (SDH) data — stated plainly as unusable.** It contributes to no result and must not
  until (1) `metadata/index.csv`, the 267 KB re-identification mapping, is moved out of the shared
  Drive folder where it currently sits **as a sibling of `images/`** — which voids the
  de-identification for that copy, exactly as `clinical_dataset_provenance.md` §4 warned before
  §4a found it had already happened — and (2) IRB approval is started, which it has not been.
  The paper should describe it as future work with governance pending.
- **A seven-item pre-submission checklist** is embedded in §8.19 so these do not have to be
  rediscovered under deadline: restrict the Tufts folder, record both licences, move the SDH
  mapping, decide on the notebook pixels, start IRB if clinic data is ever used, and confirm no
  submitted figure redistributes a restricted database.
- **Source:** `PAPER_MATERIAL.md` §8.19, drawing on `docs/EXTERNAL_DRIVE.md` (Tufts terms, read
  from the provider 26 Aug) and `docs/research/clinical_dataset_provenance.md` §4/§4a.
- **Follow-ups:** all four blockers are user/account-owner actions, not engineering. They are the
  only items on the critical path that no amount of local work can clear.

---

## 2026-08-27aa — C1 DONE: the VLM baseline does not beat a constant guess

- **What was done:** contribution **C1** — specialist pipeline vs a general-purpose VLM on the
  same 164 leak-free DENTEX images, one scorer, zero-shot. Instance 484872 (A100-80GB),
  **created, run and destroyed; total cost ₹37.93**, balance ₹650.81 → **₹612.88**. Nothing left
  running or paused.
- **The task was chosen by measurement, not habit.** The obvious framing — "does this radiograph
  show caries?" — is **degenerate here: 148 of 164 images (90.2%) contain caries**, so answering
  "yes" always scores 90.2%. C1 therefore asks **which teeth, by FDI code**, and scores both arms
  identically on the per-image FDI set (micro P/R/F1 + exact-set match).

| Arm | Precision | Recall | **F1** | exact-set | latency |
|---|---|---|---|---|---|
| **Our six-stage pipeline** | 0.235 | **0.390** | **0.294** | 1.2% | 2.39 s/img (CPU) |
| Constant guess `{26,36}` — **image ignored** | 0.250 | 0.172 | **0.204** | — | 0 |
| Qwen2.5-VL-7B-Instruct, zero-shot | 0.236 | 0.103 | **0.143** | 5.5% | 1.08 s/img (A100) |

- **THE RESULT: Qwen2.5-VL-7B scores BELOW a constant guess that never looks at the image.**
  A fixed answer of `{26,36}` scores **F1 0.204**; the VLM scores **0.143**. Its variation across
  images is not merely uninformative, it is actively harmful.
- **How that was established, because it would be easy to get wrong.** The smoke test returned
  suspiciously uniform answers, so a control was run on the box: the same prompt against a real
  radiograph, a **blank grey image**, and a **random-noise image**. Blank and noise both returned
  **`26,36`** — a confident, dental-specific answer identical to one given for a real radiograph.
  **A grey rectangle contains no teeth.** Across all 164 radiographs the model produced only
  **6 distinct answers**, with `{26,36}` and `{}` covering 110 of them.
  *26, 36 and 37 are among the most common caries sites — the model is reciting a prior.*
- **⚠️ A verdict bug of mine, corrected here because it reached the wrong conclusion.** The control
  script tested `if blank == real_A == real_B`, which requires all three to match; since the two
  radiographs differed it took the else-branch and printed *"the model IS looking at the pixels"*.
  That is the opposite of what the data shows — blank matched real_B **exactly**. The raw
  responses were inspected rather than the verdict trusted, which is the only reason it was
  caught. **A control whose pass condition is wrong is worse than no control.**
- **Efficiency comparison** (part of C1's brief): the VLM is **8.29 B parameters, 18.01 GB peak
  VRAM, 1.08 s/image on an A100-80GB**. Our pipeline is ~25 M parameters across five small
  models, runs at **2.39 s/image on a CPU with no GPU at all**, and scores **2.1× the F1**. That
  is the efficiency argument this project has been asserting, now measured.
- **The honest limits of this claim, which the paper must carry.** This is **one** open-weight
  model, **zero-shot**, under **one** prompt, on **one** task. It does **not** show that VLMs
  cannot read radiographs; it shows that this model, prompted this way, does not — and that its
  apparent score is a prior rather than perception. A larger model, few-shot prompting, or a
  domain-tuned VLM could differ, and the constant-guess control is the tool that would expose
  the same failure in any of them. **Report the control alongside the number, always** — the
  number without it invites a reviewer to read 0.143 as "the VLM is a bit worse", when the
  finding is "the VLM is not doing the task".
- **Source:** `scripts/eval/c1_vlm_baseline.py`, `scripts/eval/c1_constant_baseline.py`,
  `outputs/c1_vlm/{arm_pipeline,arm_vlm,c1_comparison,c1_constant_baseline}.json`.
- **Operational notes from the rental**, for the next one: the SSH key needed
  `icacls /inheritance:r` before `jl exec` would authenticate; `validate_fdi_assignment.py` could
  not be imported on the box (it pulls in cv2 and `src.fdi_assignment`), so `LABEL_RE` is now
  defined locally in the C1 script **with `tests/test_c1_label_re.py` asserting it never drifts
  from the canonical copy**; and the model download was started detached so it overlapped the
  539 MB data upload.

---

## 2026-08-28a - C4 DONE: abstention buys real accuracy, and the pre-registered threshold lands well

- **What was done:** contribution **C4** - the `not_assessable` abstention output, reported as a
  coverage-accuracy curve, which `MASTER_PLAN_2026H2.md` R3 specifies and which had **never been
  produced**. `scripts/eval/c4_coverage_accuracy.py`, CPU only, no GPU, no re-training.
- **Why it was missing and why that is worth recording:** the pipeline has emitted an `assessable`
  flag per tooth since R4, and calibration landed 27 Aug, so C4 *looked* done in every status
  table. It was not - the flag existed, the curve did not. **A contribution can sit at zero while
  every artefact around it says otherwise**, which is this repo's documented failure mode running
  in a new direction (see 2026-08-12 and CLAUDE.md rule 4).

| Coverage | Stage 2 - FDI numbering | Caries gate (calibrated) |
|---|---|---|
| 100% (no abstention) | 0.826 | 0.797 |
| 90% | 0.849 | 0.857 |
| 75% | **0.885** | **0.940** |
| 50% | 0.918 | 0.970 |
| gain at 75% coverage | **+5.91 pp [+3.88, +7.68]** | **+14.25 pp [+11.32, +16.63]** |
| same, confidences shuffled | +0.03 pp | +0.00 pp |

- **Stage 2**, 661 detected teeth: accuracy rises **0.826 -> 0.885** if the least confident quarter
  is declined. **Caries gate**, 863 held-out crops on isotonic-calibrated confidence: **0.797 ->
  0.940**. Both gains are clustered-bootstrap significant over **images, not teeth**.
- **The control that makes those numbers mean something.** Shuffling the confidences - breaking the
  confidence-correctness link while preserving both marginals - collapses the gain to **+0.03 pp
  and +0.00 pp**. So the rise comes from the ranking being informative, not from the arithmetic of
  discarding items. This is the same move as C1's constant-guess control, and for the same reason:
  *show what the number looks like when the mechanism is removed.*
- **The pre-registered threshold is vindicated, and was NOT tuned here.**
  `ASSESSABILITY_MIN_FDI_CONFIDENCE = 0.30` is fixed a priori in `run_inference.py`, whose comment
  forbids sweeping it against an evaluation set. Located on the curve, it retains **90.8% of
  detected teeth at 0.847 accuracy** - within **0.2 pp** of the empirical 90%-coverage point
  (0.849). A number chosen before seeing this data landed essentially where the data says it
  should. **The script deliberately does not report a "best" threshold**; doing so would be
  selecting an operating point on the set it is then evaluated on.
- **The caries branch carries far more abstention value than Stage 2** (+14.25 vs +5.91 pp). Stage
  2 needs confidence >= **0.962** just to reach 75% coverage: the numbering head is saturated near
  1.0 on most teeth, so there is little ranking information to exploit. That is the same
  overconfidence the 27 Aug calibration work measured, now showing up as a *capability* limit
  rather than a reliability one.
- **A caveat the paper must carry, because a reviewer will find it.** Stage-2 coverage is over
  **detected** teeth. Abstention cannot recover the 29.4% of ground-truth teeth Stage 1 never
  finds, so "75% coverage" means 75% of 70.6% - **53.0% of the teeth actually present**. Coverage
  here is not "share of the mouth reported on" and must never be written as if it were.
- **Also honest:** both curves are internal (DENTEX). There is no external abstention curve, and
  the caries curve below ~10% coverage is small-n noise (86 crops) and should not be read.
- **Source:** `outputs/c4_abstention/c4_coverage_accuracy.json`,
  `docs/results/figures/paper/c4_coverage_accuracy.png`, 8 new tests in `tests/test_c4_coverage.py`
  (**92/92 pass**, up from 84), all invariants hold.

---

## 2026-08-28b - C1 hardened: scale helps, prompting hurts, and an image-blind constant beats us all

Extends and partly **corrects** 2026-08-27aa. That entry stands as written; this one supersedes its
framing. H100 80GB (EU1), 59 min, **Rs 285.20**, plus **Rs 14.26 wasted** on a stray instance (below).

- **What was done:** the three things a reviewer would immediately ask of a one-model, zero-shot,
  one-prompt baseline - **a bigger model**, **few-shot prompting**, and **a reproducibility re-run** -
  plus a properly fitted image-blind constant. All six arms scored by the one scorer.

| System | P | R | **F1** | params | hardware |
|---|---|---|---|---|---|
| **Held-out constant** `{16,17,26,27,36,37,46,47}` — **image never read** | 0.218 | 0.600 | **0.320** | 0 | none |
| Our six-stage pipeline | 0.235 | 0.390 | **0.294** | ~25 M | CPU, 2.39 s/img |
| Qwen2.5-VL-32B-Instruct, zero-shot | 0.250 | 0.243 | **0.246** | 33.45 B | H100, 70.1 GB, 1.46 s/img |
| Qwen2.5-VL-7B-Instruct, zero-shot | 0.248 | 0.107 | **0.149** | 8.29 B | H100, 0.69 s/img |
| Qwen2.5-VL-7B, **2-shot** | 0.196 | 0.040 | **0.066** | 8.29 B | H100, 1.93 s/img |
| Qwen2.5-VL-7B, **4-shot** | 0.150 | 0.019 | **0.034** | 8.29 B | H100, 3.36 s/img |

- **1. The 27 Aug number reproduces.** Zero-shot 7B scores **0.149** against the 0.143 recorded on
  27 Aug, on **different hardware (H100 vs A100) and a different transformers MAJOR version
  (5.16.1 vs 4.x)**. The 0.006 drift is kernel-level nondeterminism under greedy decoding. C1's
  headline number is stable, which it had to be before going in a paper. **The library version is
  now recorded in every arm file - 27 Aug did not record it, which is why this re-run was needed.**
- **2. Scale helps a lot, and this is the correction.** 7B **0.149** -> 32B **0.246** (+65%).
  27 Aug concluded "the VLM does not beat a constant guess (0.204)". That holds for the **7B**;
  the **32B beats that particular constant**. The claim must be narrowed to the model it was
  measured on, and 0.204 was a hand-picked constant, not the best one - see item 4.
- **3. Few-shot makes it monotonically WORSE, and the reason matters.**
  0-shot **0.149** -> 2-shot **0.066** -> 4-shot **0.034**. Exemplars were drawn strictly from the
  86 leakage-excluded images, so no scored image ever entered a prompt (asserted at runtime and in
  `tests/test_c1_fewshot.py`). The mechanism: **in-context examples teach the model to answer
  nothing**, not to read radiographs.

| arm | empty predictions | mean codes/image | distinct answers |
|---|---|---|---|
| 0-shot | 56 / 164 | 1.26 | 6 |
| 2-shot | 113 / 164 | 0.59 | 9 |
| 4-shot | **123 / 164 (75%)** | 0.37 | 14 |

  **A trap worth recording: exact-set match RISES (5.5% -> 7.9% -> 9.2%) while F1 collapses.**
  16 of the 164 images contain no caries, so an empty answer harvests free exact matches.
  Reporting "few-shot improved exact-set match" would be true and completely misleading.
  Note also that few-shot does break the `{26,36}` prior (6 -> 14 distinct answers) - it replaces
  prior-recitation with **abstention**, not with perception.
- **4. THE UNCOMFORTABLE RESULT. A constant that never looks at the image beats everything,
  including us.** Fitting the greedy-best fixed FDI set on the **78 leakage-excluded images**
  (disjoint from the 164 scored - overlap asserted 0) and freezing it gives
  `{16,17,26,27,36,37,46,47}` - the eight first and second molars - which scores **F1 0.320** on
  the test set. **Our six-stage pipeline scores 0.294.** Nothing was tuned on the scored data;
  this is a baseline anyone could deploy in one line.
  - A test-set-fitted **oracle** constant reaches 0.330, but that one is not claimable and is
    labelled an oracle everywhere it appears.
  - The pipeline wins on **precision** (0.235 vs 0.218) and predicts far fewer teeth; the constant
    wins on **recall** (0.600 vs 0.390) and therefore on F1.
  - **Reading:** caries in DENTEX is overwhelmingly molar, so this tooth-level FDI-set F1 is
    **base-rate dominated and cannot by itself demonstrate clinical value**. This does not touch
    Stage-2 numbering, detection, abstention or the external-validation results. It does mean the
    C1 comparison must publish this constant beside every arm, and must not be headlined as
    "small specialist beats large generalist" without it.
- **5. Both controls still fire.** 7B: blank grey -> `26,36`, noise -> `26,36`, both identical to a
  real radiograph. 32B: blank -> **`NONE`** (a genuine improvement - it declines a content-free
  image), but **noise -> `16,17,26,27,36,37,46,47`, identical to its answer for a real
  radiograph**. `recites_prior` is true for both.
- **Process failures worth recording, because both cost money or nearly did.**
  - **Rs 14.26 wasted:** GPU availability was probed by looping `jl create` over GPU types. The
    first available type was *created*, not reported. `jl gpus` is the read-only query; the
    JarvisLabs skill says so and was not loaded until after the mistake.
  - **A 2.6 KB file broke the whole run.** The 982 MB upload reported bulk success but silently
    dropped `disease_leaked_images.json`; phase 1 launched and died on it in seconds. Every input
    is now verified **on the box** (164 images / 477 teeth / identical exemplar list) before a run
    starts, rather than inferred from an exit code.
  - Git-Bash rewrote remote paths (`/home/c1` -> `C:/Git/home/c1`) and MSYS `$(pwd)` produced paths
    the Windows `jl.exe` rejects. Use PowerShell, or `MSYS_NO_PATHCONV=1`.
  - The template ships **transformers 4.46.2, which cannot load Qwen2.5-VL at all**; upgrading
    lands on **5.x**, where `torch_dtype=` is renamed `dtype=`. The loader now handles both, and
    `apply_chat_template(..., tokenize=False)` is explicit - the default has moved between versions.
- **Source:** `outputs/c1_vlm/arm_vlm_{32b_0shot,7b_0shot_rerun,7b_2shot,7b_4shot}.json`,
  `control_pixels_{7b,32b}.json`, `c1_constant_arm_vlm_*.json`;
  `tests/test_c1_fewshot.py` + `tests/test_c1_constant.py`. **109/109 tests pass** (was 92).
  Instance destroyed; nothing left running.

---

## 2026-08-28c - Stage-2 head v3 on three corpora, and the 90-degree bug found on the way there

L4 (23 GB), 1h30m, **Rs 64.64**. Instance destroyed. Two results, and the second one nearly
poisoned the first.

### 1. THE GEOMETRY BUG - found before it reached a model

- **Every Tufts radiograph on this machine is 840x1615, rotated 90 degrees** from the 1615x840
  frame `build_enumeration_crops.py` expects. `data/dentex/enumeration_v1` and
  `data/tufts/enumeration_v1` were not on this machine at all - only the trained v2 head - so
  both had to be rebuilt before anything could train, and that is what exposed it.
- **It does not error.** The first rebuild wrote **28,171 train / 2,249 val** against v2's
  documented **35,248 / 3,721**, silently rejecting **10,087 crops (23%) as degenerate**.
- **The repo's own guard passed it.** `_tufts_align.image_orientation_score` scores mean
  brightness inside the annotation boxes; teeth sit centrally, so **both orientations score above
  1.0** - 1.040 rotated vs 1.021 upright. It was built to catch a 180-degree flip, where that
  signal genuinely works. `rebuild_bone_loss_crops.py` already documented this limitation in a
  comment; the enumeration builder never got the same protection.
- **Rotating CCW reproduces v2's corpus exactly: 35,248 / 3,721 / 3,786, all three**, with
  degenerate crops falling to 17. Three independent integers matching is what settled it.
- **Fix:** `build_enumeration_crops.py` now aborts above a **2% degenerate rate**. That figure
  separates the two cases by three orders of magnitude (23% vs 0.04%) and is agnostic to the
  cause - any future geometry mismatch trips the same wire, whatever its origin. The
  reconstructed upright radiographs are kept at `data/tufts/ZIP/Radiographs_upright`.
- **This does NOT unblock bone loss.** `rebuild_bone_loss_crops.py` already rotates image and
  boxes together via `--rotate` and still misses its geometry check by a wide margin
  (0.400 vs 0.831 sensitivity). That remains a separate, real defect - see 2026-08-27u.

### 2. HEAD v3 - three corpora

- **The third corpus** is the Kaggle *dual-labeled* set. Two corrections to
  `MASTER_PLAN`/`transfer.md`: it is **500 images, not 2,000** (the dataset publishes 2,066 labels
  but only 500 images; 2,566 files total, confirmed by full API pagination - the download is
  complete, the images are simply not all there), and its numbering was **verified, not assumed**.
  The v2 head as an independent arbiter over 915 teeth: **80.3% agreement read direct vs 1.7%
  mirrored**. Tufts looked like plain Universal and was mirrored; assuming here would have trained
  a third of v3 on side-swapped labels. Usable: **499 images / 13,166 teeth / 22,327 crops,
  0.00% degenerate**.
- **A control was trained the same day** (`models/12a_fdi_head_v2_control_rebuilt`) on the rebuilt
  DENTEX+Tufts crops - same code, seed, epochs, machine. Comparing v3 against *published* v2 would
  have folded the crop rebuild, the geometry fix, torch 2.11 and a different GPU into what is meant
  to be a single-variable test. The control reproduces published v2 to **within ~1 pp**
  (FDI exact 0.821 vs 0.810), which is also what clears the geometry fix - a head trained on
  misaligned crops collapses, it does not reach 98.3% quadrant accuracy.

| corpus (split) | n | v2 control | v3 | delta | 95% CI | verdict |
|---|---|---|---|---|---|---|
| **DENTEX** val | 2,729 | 91.4% | **92.5%** | **+1.14 pp** | [+0.33, +1.95] | **significant** (p=0.013) |
| **Tufts** test | 3,786 | 75.0% | 75.8% | +0.74 pp | [-0.37, +1.89] | **not significant** (p=0.25) |
| **Kaggle** test | 1,994 | 77.7% | **93.2%** | +15.45 pp | [+12.79, +18.28] | significant, but see below |

- **How to read that table.** The **Kaggle +15.45 pp is not a generalisation result**: v3 trained
  on that corpus and the control had never seen it, so it says "training on a corpus helps on that
  corpus". It is reported because omitting the largest number would look like concealment, not
  because it supports a claim. **The real result is DENTEX +1.14 pp**, which survives its interval
  - a third corpus improved accuracy on a corpus it added no data to. **Tufts is flat**: +0.74 pp,
  CI crossing zero, near-balanced churn (294 crops fixed, 266 broken). **Nothing regressed** on any
  corpus or metric.
- **Pooled val must never be quoted** (v3 0.855 vs control 0.821). v3's val set contains 1,961
  Kaggle crops the control's does not, so the two are computed over different mixtures; that
  comparison inflates the effect roughly threefold.
- **v3 is a reported ABLATION, not the pipeline default.** Adopting it would require re-measuring
  the Stage-2 58.3%/82.6% headline, the C4 coverage-accuracy curves, the §8.16 failure taxonomy and
  the pre-registered 0.30 operating point - all measured against v2. A +1.14 pp in-domain gain does
  not justify that before the 14 Oct freeze.
- **Deltas are paired** (same crops, two heads), bootstrapped over **source images** not crops, with
  an exact McNemar test alongside.
- **Process notes.** The pytorch template ships without `sklearn`, `matplotlib` or `cv2`; each
  surfaced as a crash mid-run (the eval failed all six cells on `cv2` before being installed).
  `jl run` accepted a job, created its directory, then died without starting it - SSH + `nohup` was
  reliable. A 982 MB upload reported bulk success while silently dropping one 2.6 KB file, which
  killed the first launch. Verify inputs **on the box** before starting a billed run.
- **Source:** `models/12_fdi_head_v3_3corpus/run_summary.txt`,
  `models/12a_fdi_head_v2_control_rebuilt/run_summary.txt`,
  `scripts/kaggle_dual/{build_enumeration_crops,verify_fdi_convention}.py`.
  **122/122 tests** (was 109).

---

## 2026-08-28d - The metric fix FAILED: a molar constant beats the pipeline on lesion localisation too

- **What was tried, and why.** 2026-08-28b found that an image-blind constant (the eight first and
  second molars) scores F1 **0.320** on tooth-level caries FDI-set prediction against this
  pipeline's **0.294**. The proposed rescue was to lead the paper on **lesion-localisation
  agreement** instead, on the reasoning that a constant "localises nothing". **That reasoning was
  wrong and the experiment says so.**
- **Two errors in the original reasoning, both found by reading the metric rather than trusting
  the pitch.** (1) A molar constant *does* localise: it flags eight real detected tooth boxes, and
  tooth-level is the only localisation this pipeline performs at all. (2)
  `lesion_localization_agreement` is **recall over lesions with no negative class** - by design, so
  Ningxia's missing healthy controls cannot corrupt it - which means flagging MORE teeth can only
  raise it.
- **Result, 164 leak-free DENTEX images, 479 caries lesions, one matcher, three decision rules:**

| arm | agreement (recall) | teeth flagged | on a lesion | match rate |
|---|---|---|---|---|
| Our pipeline | 0.443 | 755 | 212 | 0.281 |
| **Constant: eight molars, image never read** | **0.488** | 859 | 234 | 0.272 |
| Ceiling: flag every detected tooth | 0.722 | 3,344 | 346 | 0.103 |

- **The constant beats the pipeline by +4.59 pp [+0.60, +8.89]** (paired bootstrap over images,
  5,000 resamples). **The interval excludes zero: this is real, not a tie.**
- **And it does not win by brute force.** It flags 859 teeth against the pipeline's 755 - only
  **14% more** - at essentially the same match rate (0.272 vs 0.281). The two sit on the same
  efficiency frontier, with the constant slightly ahead on both axes taken together.
- **Reading.** The caries branch's tooth-level decisions carry little information beyond the prior
  "molars get caries". This is consistent with SS 8.17, where the gate over-calls healthy teeth
  (19.2%) at the same rate as impacted teeth (19.0%) - it was already visible, and this quantifies
  what it costs.
- **What this does NOT say.** It is a statement about the caries branch on this dataset under
  tooth-level metrics. It does not touch Stage-2 numbering (82.6% of detected - a constant cannot
  do that task at all), abstention (SS 8.21), calibration (SS 8.15), or the external-validation
  result (SS 8.12).
- **The honest conclusion, which supersedes the plan in the 28 Aug session note.** Changing the
  metric does not rescue the caries claim, because the problem is not the metric - it is that
  caries on public OPG data is molar-dominated and tooth-level decisions are dominated by that
  prior. **Any paper reporting tooth-level caries numbers in this range on this kind of data owes
  a constant-baseline row**, and this project should say so rather than quietly pick whichever
  metric flatters it. That is a stronger contribution than the pipeline number was.
- **Source:** `scripts/eval/lesion_localization.py --decision {pipeline,constant-molars,all-teeth}`,
  `outputs/lesion_loc_*/lesion_localization.json`.

---

## 2026-08-28e - The constant arm on Ningxia: externally, pipeline and constant are INDISTINGUISHABLE

**A Ningxia touch (the 4th).** Both arms run in the same session against the same detector, FDI head
and gate, so no drift is folded into the comparison. Caries only; periodontitis untouched.

- **Why this was run.** 2026-08-28b/d established that an image-blind constant (the eight first and
  second molars) beats this pipeline on DENTEX on **both** metric families - FDI-set F1 0.320 vs
  0.294, and lesion-localisation agreement 0.488 vs 0.443 (+4.59 pp [+0.60,+8.89]). Whether that is
  a property of DENTEX or of the task decides how strongly the paper can state it.
- **Metric note.** Ningxia uses **centroid containment**, not IoU >= 0.30: its caries lesions are
  89-3,090 px focal blobs inside ~25,000 px tooth boxes, and the DENTEX matcher would score ~0% by
  construction (25 Aug). The constant arm reuses Stage 2's codes only to know which detected boxes
  are molars; the **verdict never reads the pixels**.

| hospital | lesions | pipeline | flagged | constant | flagged | delta |
|---|---|---|---|---|---|---|
| test1 | 316 | 0.288 | 637 | **0.446** | 736 | **+15.8 pp** |
| test2 | 349 | **0.513** | 814 | 0.407 | 662 | -10.6 pp |
| test3 | 162 | 0.401 | 252 | 0.377 | 247 | -2.5 pp |
| test4 | 186 | 0.419 | 402 | 0.323 | 306 | -9.7 pp |
| **POOLED** | **1,013** | **0.408** | 2,105 | **0.399** | 1,951 | **-0.89 pp [-4.88, +3.01]** |

- **THE RESULT: pooled, the two are statistically indistinguishable** - constant minus pipeline
  **-0.89 pp, 95% CI [-4.88, +3.01]**, paired bootstrap over 337 images, 5,000 resamples. The
  interval straddles zero in both directions.
- **This does NOT replicate the DENTEX finding, and that is stated plainly.** On DENTEX the constant
  *won* significantly. Externally it does not; the pipeline is nominally ahead by 0.9 pp, which is
  noise. **The defensible claim across all five hospitals is therefore "indistinguishable", not
  "the constant is better".** That is a weaker sentence than 28 Aug's and a more accurate one.
- **The per-site spread is the more useful finding.** The delta swings **+15.8 pp at test1 to
  -10.6 pp at test2** - a 26-point range across four hospitals of one dataset. The pooled -0.89
  hides that completely. Any single-number external claim, ours included, is uninformative at this
  variance; report per site.
- **test1 is the interesting site**: the pipeline's *worst* (0.288) and the constant's *best*
  (0.446). Whatever makes test1 hard for a trained model does not make it hard for an anatomical
  prior. Not diagnosed here.
- **Two bugs of mine in the analysis, both caught before they reached a number.** (1) A first
  bootstrap keyed per-image rows by filename alone; **Ningxia filenames repeat across splits**, so
  337 rows collapsed to 134 - the identical defect recorded on 27 Aug. Fixed by keying
  `(split, image)` and asserting the pairing is total. (2) The same script read
  `n_lesions_covered` via `.get(key, 0)`; the real field is `n_covered`, so **both arms silently
  read zero and the delta printed as +0.00 pp [0.00, 0.00]**. A defaulting getter turned a wrong
  key into a confident null result. Neither was reported.
- **Source:** `scripts/eval/ningxia_external.py --decision constant-molars`,
  `outputs/ningxia_{pipeline,constant-molars}/ningxia_external.json`.

---

## 2026-08-28 — Manuscript rebuilt from the artefacts; five numeric/factual defects corrected

- **What was done:** a full evidence audit of `paper/main.tex` against the repository,
  followed by a complete rewrite. Audit written to `docs/paper/REBUILD_AUDIT.md`
  (research story, 20-item problem audit, numerical audit, storyboard, citation audit,
  five title options). The superseded draft is copied to
  `_repo_archive/paper_draft_v1_44percent_title/` (ARCHIVE_MANIFEST item 7); git history
  holds it too. **No experiment was re-run and no evaluation artefact was touched** — this
  is a documentation pass over already-measured results.
- **Dataset / config:** no new runs. Every number re-read from `outputs/*.json`,
  `models/*/run_summary.txt`, the DENTEX label files, and the checkpoint tensors.
- **FIVE DEFECTS IN THE PUBLISHED DRAFT, all now corrected:**
  1. **Parameter count.** The draft claimed the whole system is "approximately 25 M
     parameters". Counted from the six checkpoints with `torch.load`: detector 27.62 M,
     FDI head 11.20 M, caries gate 11.19 M, caries severity 11.19 M, bone-loss gate
     11.19 M, bone-loss severity 11.19 M = **83.56 M total**, **61.20 M on the caries
     path**. The 25 M figure was the *superseded bbox detector alone* (`model_metrics.md`
     records it as "25.3M params"), promoted to a whole-system claim. The efficiency
     argument survives — 33.45 B against 61.2 M is still ~550x — but on the true number.
  2. **Two model names that do not exist.** The draft wrote "Qwen2.5-VL-33B" and
     "Qwen2.5-VL-8B". The arms were run on **Qwen2.5-VL-32B-Instruct** (33.45 B params as
     loaded) and **Qwen2.5-VL-7B-Instruct** (8.29 B). Released name and measured parameter
     count are now separate columns. Figure labels regenerated.
  3. **The blank-image control was overstated.** The draft said *both* models return
     confident dental answers to a blank grey image and to noise. `control_pixels_32b.json`
     says `answers.blank = "NONE"` — the 32 B model answers the blank **correctly**. Only
     the 7 B model fails there; both fail on noise. The precise result is *stronger*: the
     32 B model's answer to random noise is `16, 17, 26, 27, 36, 37, 46, 47` — **exactly
     the eight-molar constant our greedy search recovered from the data.**
  4. **Isotonic calibration does not leave verdicts unchanged.** The draft said the ECE
     0.136 → 0.043 correction leaves "every verdict byte-identical".
     `caries_gate_isotonic.json` records `verdicts_flipped_at_0.5 = 155` (18% of 863) and
     `average_precision 0.550 → 0.4996`. The invariance is a **deployment choice** — we
     apply isotonic to the reported confidence only and leave the verdict as raw `argmax` —
     not a property of the method. Temperature scaling is the decision-invariant one, and it
     made calibration worse. Both costs are now stated.
  5. **An uncounted survey claim.** "None of the 49 report a constant, image-blind or
     otherwise uninformed baseline" was presented as a census.
     `outputs/related_work_extract.csv` has no baseline-reporting field and no such count
     exists. The **2-of-49 external-validation count is verified** (recomputed here: 84 rows
     → 49 unique titles; negation-aware classifier reproduces 2 primary studies). The
     baseline claim is now stated as an observation, not a count.
- **477 vs 479 RESOLVED, and it was never an error.** Recomputed from
  `DENTEX/disease/label/*.json` over the 164 scored images: **479 çürük polygons** across
  **477 distinct (image, FDI) pairs**. Exactly two teeth carry two annotated lesions each —
  `test_101` tooth 36 and `test_25` tooth 46. Different units, both correct; the manuscript
  now says so in the table caption.
- **The constant reproduces exactly.** The greedy fit was re-run from scratch on the 78
  fitting images and returned `{16,17,26,27,36,37,46,47}` — identical to the stored result.
  Also newly recorded: it scores **F1 0.392 on its fitting set and 0.320 on the scored
  set**, i.e. it transfers *downwards*, which is what an honest held-out fit does. This is a
  useful answer to "the constant was fitted, so it is not uninformed".
- **The 86 → 78 fitting-set arithmetic is now explained, not asserted.** 250 DENTEX
  `disease/` images; 86 excluded by **MD5 byte-identity** against training images (85 via
  the numbering head, 1 via the detector); 164 scored. Of the 86, **78 carry at least one
  caries annotation** and those are the fitting set. (`c1_constant_baseline.py`'s docstring
  still says "86" — stale comment; the runtime label and the paper are right.)
- **Metrics:** no metric changed. 82 numeric claims in the manuscript now pass an automated
  check against their artefacts (`scripts/verify_paper_numbers.py`, new). 122/122 tests
  pass. Manuscript compiles clean: 0 errors, 0 overfull boxes, 0 undefined references,
  12 pages.
- **Key decision or insight:** **the paper's title changed.** "What Does 44 % Mean?" anchors
  on 212/479 = 44.3 %, which is the *pipeline's own* lesion-localisation agreement — one row
  of one table, never written as "44 %" in the body, and not the finding. New title: *"What
  a Tooth-Level Score Cannot Tell You: Constant Baselines, External Validation and Domain
  Shift in Automated Panoramic Dental Screening."* It names the contribution rather than a
  result, survives the external cohort's non-replication (a title asserting the constant
  wins would not), and admits the periodontal branch, which the old title excluded.
- **Also now in the manuscript, and previously absent:** the periodontal task is introduced
  clinically rather than appearing mid-Methods; test2's `same_centre_as_train` label is
  stated with the "equally external to us" reasoning; the two lesion matchers are declared
  **not comparable to each other**; the bone-loss 0.923 carries both its documented caveats
  (peak of a noisy 32-epoch curve over 59 val positives; **not reproducible** — jitter RNG
  never saved, source images off-machine, rebuild rejected by its own geometry check); a
  Statistical analysis subsection states the cluster bootstrap (10,000 resamples, seed 42,
  over images) and the two quantities it cannot cover; and the caries gate's **AP 0.550
  [0.445, 0.660] against 0.147 prevalence** appears, so the calibration failure is not read
  as a failure of discrimination.
- **Bibliography:** five entries carrying `UNVERIFIED` or "verify at proof stage" notes were
  re-verified and completed — `he2016resnet` (doi 10.1109/CVPR.2016.90), `zadrozny2002isotonic`
  (doi 10.1145/775047.775151, pp. 694–699), `guo2017calibration` (PMLR 70:1321–1330, no DOI
  issued), `jocher2024yolo11` (software citation), `meng2026dentvlm` (Nat. Commun. **17**,
  art. 8933 — full author list confirmed against Crossref). **No submission-blocking
  provenance note remains on any cited entry.** Two such notes remain on *uncited* entries.
- **Source:** `docs/paper/REBUILD_AUDIT.md`, `paper/main.tex`, `paper/source.bib`,
  `scripts/verify_paper_numbers.py` (new), `scripts/figures/make_baseline_figure.py`,
  `scripts/figures/make_boneloss_paper_figure.py`.
- **Follow-ups:** (1) **12 pages against an ISBI 4-page limit** — the rebuilt manuscript is a
  complete, self-explaining document and needs a venue-specific cut, not a rewrite; §III–§V
  and the Limitations list are where the compression lives. (2) `kong2024integrating` pairs a
  Bioengineering journal record with a Springer *chapter* DOI; uncited, so not blocking, but
  fix before it is used. (3) `c1_constant_baseline.py:78` docstring says 86 where the fitting
  set is 78.

---

## 2026-08-30 — SDH clinic dataset: consent obtained, first measurements, and six corrupt images

- **What was done:** Oral consent from the SDH clinic was obtained (written agreement expected
  1 Sep 2026), unblocking `PUBLICATION_TODO.md` T1.2. The dataset was then measured for the
  first time rather than described: every one of the 3,219 enhanced PNGs was opened, per-image
  quality metrics were computed for all of them, and the frozen six-stage pipeline was run
  unmodified over a deterministic 24-image sample with a matched 24-image DENTEX reference run.
  An execution plan was written from those measurements
  (`docs/research/SDH_EXECUTION_PLAN.md`).
- **Dataset / config:** `D:\SDH dataset\dataset\images\` (3,219 files, 8-bit grayscale PNG,
  height fixed 1,316, width 2,043–3,001, 405 distinct sizes). Pipeline: `scripts/run_inference.py`
  at defaults — R1 seg detector `models/11_yolo_seg_tufts_r1/best.pt`, Stage-2 head v2.0,
  caries gate v3, `imgsz=1024`, `conf=0.25`, one-to-one FDI assignment, CPU
  (torch 2.8.0+cpu, Python 3.13.7). SDH sample = every 134th image; DENTEX sample = every 10th
  of `DENTEX/disease/input`.
- **Metrics — pilot inference, n=24 per corpus, NO ground truth, so these are behaviour
  distributions and not accuracy:**

  | | SDH (n=24) | DENTEX (n=24, reference) |
  |---|---|---|
  | teeth/image min / median / max | 5 / **27** / 30 | 5 / 21 / 31 |
  | images with 0 teeth | 0 | 0 |
  | mean detection confidence | 0.407 | 0.373 |
  | caries-positive per image | 1.67 (6.2% of detected) | 5.04 (24.0%) |
  | bone-loss-positive per image | 0.54 (**2.0%**) | 0.04 (0.2%) |
  | throughput, models loaded once | 2.2 s/image | 2.2 s/image |

  DENTEX is training-domain for the caries gate, so it is a reference distribution, not a
  control. Duplicate-FDI count was 0 on all 48 images **by construction** — one-to-one Hungarian
  assignment cannot emit a duplicate; that diagnostic requires `--no-one-to-one`.
- **Metrics — per-image quality, all readable images (n=3,213), p95/p5 spread:** `lapvar` 2.48,
  `frac_black` 2.96, `band_std` 1.99, `band_sharp_grad` 1.98, `sharp_grad` 1.90 — against
  `entropy` 1.09, `mean` 1.07, `dynamic_range` 1.32, `std` 1.45.
  `band_edge_density` came out degenerate (median 0.000, p99 0.002; Canny 60/160 is too high for
  a post-CLAHE panoramic) and is excluded from the feature set rather than left in.
  Full table: `data/sdh/quality_metrics_enhanced.csv`.
- **Bug found — six images are truncated and no artefact records it.** `001970.png` …
  `001975.png` fail to decode (`cv2.imread` → `None`; PIL `OSError: image file is truncated`;
  libpng read error). All six file sizes are exact multiples of 4,096 bytes (245/210/138/114/44/17
  blocks), and `logs/preprocessing_run.log` opens with `Resume checkpoint: 1975` — the June 2026
  run was interrupted with those six in flight and resumed *after* the checkpoint, never
  revisiting them. **`checkpoint.json`'s `completed_output_images: 3219` is therefore wrong by
  six; the usable set is 3,213.** Nothing had caught it because nothing had ever opened every
  file. The six source `.pano` files are intact in `D:\raw data\`, so this is repairable — but
  only after the hardcoded `D:\dataset_audit\dataset` output path is fixed
  (`clinical_dataset_provenance.md` §7), or a repair writes to a non-existent path and forks the
  dataset.
- **Key decisions or insights:**
  1. **Stage 1 does not collapse on SDH** — more teeth per image and higher mean confidence than
     on DENTEX. Not evidence of accuracy (recall is unmeasurable without labels), but the
     opposite of what `clinical_dataset_plan.md` §2's domain-shift register predicted for the
     highest-risk axis.
  2. **Bone loss fires on 2.0% of detected teeth**, alongside Ningxia's 2.4% and against DENTEX's
     0.7%. This independently **confirms** the decided limitation in `PAPER_MATERIAL.md` §8.13
     on a fourth corpus; it does not reopen it.
  3. **2.2 s/image on CPU means Tier A needs no GPU.** Full-set inference is a ~2-hour unattended
     CPU job. The ₹313 JarvisLabs balance is reserved for the one task that genuinely needs a
     GPU (pseudo-label detector adaptation), and ₹313 buys one attempt with no redo.
  4. **The June enhancement already normalises brightness, contrast, dynamic range and entropy**,
     which is why those metrics carry no filtering signal. The per-image filter must be built on
     sharpness and local band contrast, which is what percentile windowing cannot repair.
  5. **1,013 patients have repeat scans and 145 have same-day retakes** — a test–retest
     repeatability substrate that needs zero labels and that no other corpus in this project has,
     plus a weak free label for "non-diagnostic image". For all 144 same-day groups present in
     the kept set, the retained image is the lowest-numbered scan of its group, i.e. plausibly
     the one the clinic rejected.
  6. **Two tracked documents claimed the clinic data was "Not on this machine"** (`transfer.md`
     §8, `data/README.md`). Both were wrong; corrected this session.
- **Source:** `docs/research/SDH_EXECUTION_PLAN.md` (the plan and every number above),
  `data/sdh/quality_metrics_enhanced.csv` (n=3,213), `data/sdh/pilot_inference_n24.csv`,
  `D:\SDH dataset\dataset\logs\preprocessing_run.log`,
  `D:\dataset_audit\outputs\pano_format_summary.csv`.
- **Follow-ups:** (1) Repair or exclude the six truncated images and correct `checkpoint.json`
  before the DEV/TEST split is drawn — the split basis is 3,213 or 3,219 depending on that
  decision. (2) Freeze `data/sdh/splits_v1.json` (40/60 patient-level, stratified, seeded) before
  any filter threshold is chosen; the 24 pilot images are burned and must land in DEV.
  (3) Decide whether the GPU balance is topped up — Tier C1 cannot absorb a redo on ₹313.
  (4) Separate `metadata/index.csv` from `images/` on Google Drive before the written agreement
  is signed (`clinical_dataset_provenance.md` §4a). (5) `band_edge_density` needs re-tuned Canny
  thresholds or removal from the CSV.

---

## 2026-08-31 — The caries gate reads POSITION as much as lesion; and 2.7x more data does not fix it

- **What was done:** two experiments on the caries branch, prompted by "precision and recall are
  very low, how do we improve them". First a diagnostic of *where* the errors are; then the
  highest-value fix the diagnostic implied. **The diagnostic is a finding. The fix is a negative
  result.** No model was adopted; `caries-gate-resnet18-v3.0` remains the pipeline default,
  unchanged and hash-pinned.

### 1. The gate has partially absorbed the molar prior — measured

- **New script:** `scripts/eval/caries_position_bias.py`, read-only, re-runnable. It reproduces
  the published test confusion matrix exactly (TP 94 / FP 142 / FN 33 / TN 594) before drawing
  any conclusion, so the analysis path is validated against a known reference.
- **Mean P(caries) on teeth that are genuinely HEALTHY tracks the training base rate for that
  tooth position** — held-out test, 863 crops, 34 source images:

| tooth type | n | pos | precision | recall | FP rate | mean P on *healthy* | train base rate | within-type AUC |
|---|---|---|---|---|---|---|---|---|
| incisor | 266 | 8 | 0.091 | **0.125** | 0.039 | 0.075 | 0.017 | 0.681 |
| canine | 129 | 5 | 0.333 | **0.200** | 0.016 | 0.087 | 0.023 | 0.748 |
| premolar | 221 | 31 | 0.292 | 0.677 | 0.268 | 0.273 | 0.157 | 0.781 |
| molar | 247 | 83 | 0.473 | 0.855 | **0.482** | **0.478** | **0.343** | 0.781 |

- **48.2% of healthy molars are flagged carious**; 79 of the 142 false positives are healthy
  molars. That is where the 0.398 precision goes. In the other direction the gate is close to
  blind on anterior teeth — **1 of 8 incisor lesions found**.
- **But the lesion signal is real.** Ranking *within* a tooth type removes the shortcut, and
  **within-type AUC is 0.7454, 95% CI [0.6604, 0.8420]** — excludes 0.5. Pooled AUC (0.8548) is
  inflated by the prior, because ranking a molar above an incisor is free. A position-only
  predictor that never sees the image scores **AP 0.2962** against the model's 0.5503 and a
  0.1472 chance line.
- **This is the mechanism behind §8.22.** That section shows an image-blind molar constant beats
  the pipeline (F1 0.320 vs 0.294) and reports it as a property of the metric. This entry shows
  the caries gate *itself* has partially become that constant, and quantifies how much.
- **Threshold fixes are exhausted, and this was tested rather than assumed.** The shipped 0.50 is
  already F1-optimal across a 19-point sweep. Per-tooth-type thresholds fitted on val and applied
  once to test give **F1 +0.006, 95% CI [-0.034, +0.041]** — not significant, and no better than
  re-fitting a single global threshold. Anterior thresholds are fitted on 13 positives and are
  noise. **The curve has to be lifted; the decision rule cannot be tuned into a better one.**

### 2. Caries gate v4 — 2.67x the positives, and nothing moved

- **The gap that motivated it:** DENTEX's disease subset carries **2,767** Caries + Deep Caries
  annotations; `crops_v3_phase1` uses **1,049**. The MD5 join that makes healthy teeth derivable
  only covers 260 of 705 images, so **62% of the available caries supervision was unused**.
- **Build:** `build_caries_phase1_v3.py --include-disease-only` (new flag; the default path is
  unchanged and was verified to reproduce the frozen v3 corpus **exactly** — 4,750/1,003/863,
  healthy 5,366, ambiguous 856). Adds the 445 disease-only images as **positives only**; it adds
  no healthy teeth, because without an enumeration twin there is no list of which teeth exist,
  and deriving negatives from the detector would inject detector false positives into the
  negative class. Train positives **723 → 1,928**; healthy negatives unchanged at 5,366; class
  ratio 1:5.57 → 1:2.28.
- **Leakage:** exactly one image refused — `train_332.png` is byte-identical to `test_181.png`
  in the evaluation pool, already on record as `leaked_into_detector_training`. Also verified:
  0 images span two splits, 0 v3-test images in v4 train/val, all 863 v3 test crops present in
  v4's test split.
- **Training:** identical to v3's shipped command except `--variant`. 15 epochs, batch 32,
  lr 1e-3, seed 42, MPS, 8 min 16 s. Best epoch 12, val macro-F1 0.8090.
- **Metrics — both gates on the SAME published 863-crop test set:**

| | P | R | F1 | AP | AUC |
|---|---|---|---|---|---|
| v3 (shipped) | 0.3983 | 0.7402 | 0.5179 | **0.5503** | 0.8548 |
| v4 (2.67x positives) | 0.4346 | 0.6535 | 0.5220 | **0.5496** | 0.8599 |

  Paired cluster bootstrap over the 34 source images, 5,000 resamples, seed 42:

| paired delta (v4 − v3) | point | 95% CI | verdict |
|---|---|---|---|
| average precision | −0.0015 | [−0.0886, +0.0821] | **not significant** |
| ROC AUC | +0.0053 | [−0.0227, +0.0365] | not significant |
| F1 @0.5 | +0.0035 | [−0.0651, +0.0740] | not significant |
| precision @0.5 | +0.0358 | [−0.0272, +0.0991] | not significant |
| recall @0.5 | −0.0881 | [−0.1923, +0.0233] | not significant |

- **Every interval spans zero.** Average precision — threshold-independent, the whole PR curve —
  **did not move**. The precision gain and recall loss are a shift *along* the same curve, caused
  by the changed class balance moving what a 0.50 threshold means. **The bottleneck is not the
  quantity of positive supervision.**
- ⚠ **A number in this run that must never be quoted.** `outputs/caries_v4/arm_b/phase1_gate_report.txt`
  reports caries **P 0.71 / R 0.80** on v4's *own* test split. Against v3's published 0.398/0.740
  that reads as a transformation. It is not one: v4's test split has **2.2x the caries prevalence**
  (0.324 vs 0.147) because disease-only images contribute positives and no healthy teeth, and
  precision is a function of prevalence. Specificity — the model-intrinsic quantity — is
  essentially unchanged (**0.853 vs 0.843**). Comparing precision across two test sets of
  different prevalence measures the sets, not the models.
- **Key decision:** **v4 is NOT adopted.** It is not better, and swapping it would invalidate the
  44.3% lesion agreement, the C1 comparison, the C4 coverage curves, the calibration analysis and
  the Ningxia externals — all measured on v3 — in exchange for nothing. Same reasoning that kept
  Stage-2 head v3 an ablation (2026-08-28c).
- **Also ruled out by measurement, not argument:** raising input resolution. The median tooth box
  is 170x287 px = 46,288 against the 224x224 = 50,176 the model already sees — a 1.04x linear
  resize, and **58% of boxes are already being upsampled**. There is no detail to recover. A prior
  hypothesis that the square resize leaks tooth identity through aspect ratio was also **falsified**:
  crops are stored pre-squared, so no shape cue exists in the input; the model reads tooth type
  from genuine appearance.
- **Source:** `scripts/eval/caries_position_bias.py`,
  `outputs/caries_position_bias/caries_position_bias_test.json`,
  `outputs/caries_v4/run_summary.txt`, `outputs/caries_v4/arm_b/results.json`.
- **Follow-ups:** (1) The remaining untested levers all target *signal* rather than data volume:
  CLAHE contrast normalisation, a slightly expanded crop (interproximal caries sits at the contact
  point, which a 1.0x crop cuts through), and position-balanced sampling — the last attacks the
  measured shortcut directly but may *lower* pooled F1, since that metric rewards using the prior.
  (2) The negative class cannot grow inside DENTEX without new assumptions: enumeration images
  without a disease twin are not evidence of health. (3) The stratified table above belongs in the
  paper beside §8.22 — it is the mechanism behind the headline finding.

---

## 2026-08-31b — Three signal arms on the caries gate: none met the pre-registered bar

- **What was done:** the three levers left after 2026-08-31 ruled out threshold tuning, data
  volume and resolution — **CLAHE**, a **1.25× crop expansion**, and **position-balanced
  sampling** — each trained against a **same-day control** and scored under a rule written down
  before any arm ran (`outputs/caries_arms/PRE_REGISTRATION.md`). **No arm succeeded. Nothing was
  adopted.** Run locally on MPS, ~8 min per run; no GPU rented, because a ResNet18 at 224 px over
  6,616 crops is not a compute-bound job (`transfer.md` §6).
- **Pre-registered in advance:** primary metric **average precision** on the 863-crop held-out
  test split; comparator a same-day control (v3 config, frozen `crops_v3_phase1`, this
  environment); success = **paired AP delta vs control with a 95% CI excluding zero**, from a
  paired cluster bootstrap over the **34 source images**, 5,000 resamples, seed 42. AP rather
  than P/R because the v4 experiment had just demonstrated the failure mode: precision +3.6 pp
  and recall −8.7 pp while **AP did not move**.
- **The control is faithful:** best val macro-F1 **0.7350**, exactly v3's published figure, so
  environment drift is not confounding the deltas.
- **Preconditions verified before training** (arms A and B rebuild the pixels, so the pairing is
  only valid if the crop *sets* match): both rebuilt corpora have 6,616 crops, test 863/127,
  **identical (crop, split, label, fdi) composition and identical source images** to
  `crops_v3_phase1`, and the pixels genuinely differ (CLAHE mean abs diff 16.96, contrast std
  44.3 → 62.0; exp125 32.22). This is precisely what the v4 experiment could not claim.
- **Metrics — all four on the same 863-crop test split:**

| arm | P | R | F1 | **AP** | AUC | within-type AUC |
|---|---|---|---|---|---|---|
| control | 0.3983 | 0.7402 | 0.5179 | **0.5503** | 0.8548 | 0.7454 |
| clahe | 0.4545 | 0.7087 | 0.5538 | **0.5977** | 0.8741 | 0.7887 |
| exp125 | 0.4541 | 0.6614 | 0.5385 | **0.5684** | 0.8524 | 0.7406 |
| balance | 0.4244 | 0.6850 | 0.5241 | **0.5943** | 0.8577 | 0.7662 |

| arm | metric | point | 95% CI | verdict |
|---|---|---|---|---|
| clahe | **average precision** | **+0.0488** | **[−0.0031, +0.0993]** | **MISS by 0.0031** |
| clahe | precision @0.5 | +0.0558 | [+0.0106, +0.1008] | **REAL** |
| clahe | recall @0.5 | −0.0314 | [−0.1095, +0.0500] | not significant |
| clahe | within-type AUC | +0.0435 | [−0.0160, +0.0988] | not significant |
| exp125 | **average precision** | +0.0198 | [−0.0367, +0.0810] | not significant |
| exp125 | precision @0.5 | +0.0549 | [+0.0114, +0.0977] | REAL |
| exp125 | recall @0.5 | −0.0794 | [−0.1567, −0.0078] | REAL — **a pure trade** |
| balance | **average precision** | +0.0432 | [−0.0328, +0.1157] | not significant |
| balance | within-type AUC | +0.0194 | [−0.0692, +0.1303] | not significant |

- **Key decision: the bar was missed and was NOT moved.** CLAHE's AP interval misses by
  **0.0031** on the lower bound. Recorded as a miss, in the same terms as R1's mask bar (0.6383
  against a pre-registered 0.65). **No arm is adopted; `caries-gate-resnet18-v3.0` remains the
  pipeline default.**
- **What is real, as a secondary result:** **CLAHE buys precision (+5.6 pp, CI excludes zero)
  with no significant recall cost** — the only arm for which that holds. Its false-positive rate
  falls in every stratum (premolar 0.268 → 0.137, molar 0.482 → 0.457). exp125's precision gain
  is cancelled by a *real* recall loss, which is a slide along the curve, not a lift — the flat
  AP confirms it.
- **A pre-registered warning that did not materialise.** `PRE_REGISTRATION.md` recorded, in
  advance, that arm C might *lower* AP because the test population genuinely carries 3.4× more
  caries in molars and AP rewards exploiting that prior. **It did not** (AP +0.043, CI spans
  zero). The prior is not load-bearing for AP in the way anticipated. Recording this because the
  warning was written to be falsifiable, and it was falsified.
- **What CLAHE does NOT fix:** the anterior blindness. Incisor recall stays 0.125, canine recall
  goes 0.200 → 0.000, and the position prior is still plainly present (mean P on healthy teeth
  0.037 incisor → 0.443 molar). CLAHE suppresses false positives; it does not make the model see
  anterior lesions.
- **The honest limitation of this experiment: it is underpowered.** 863 crops but only **34
  source images**, and intervals are clustered over images because teeth in one radiograph are
  not independent. That is the correct choice and is why the intervals are wide — a +0.049 AP
  point estimate cannot be separated from zero at n=34. **Only a larger held-out image set
  resolves CLAHE**; no further modelling arm on this split will.
- **Source:** `outputs/caries_arms/PRE_REGISTRATION.md`, `outputs/caries_arms/run_summary.txt`,
  `outputs/caries_arms/arms_comparison.json`, `scripts/eval/caries_arms_compare.py`.
  New builder flags `--clahe` / `--crop-expand` and trainer flag `--balance-position`; the
  default paths are unchanged and still reproduce the frozen v3 corpus exactly.
- **Follow-ups:** (1) **CLAHE is the one candidate worth a confirmatory run**, and the only thing
  that would settle it is more held-out images — e.g. scoring it on the larger v4 test split
  (1,218 crops from more images), which is a *different* item set and so needs its own control.
  (2) Five independent attempts have now failed to lift this curve (thresholds, per-stratum
  thresholds, 2.67× data, and these three). **That the caries branch is at its headroom on DENTEX
  is now the leading hypothesis, not a worry** — and it is a legitimate, citable result for §8.24.

---

## 2026-09-01 — A sixth cohort, and the constant beats the pipeline by 25 points

- **What was done:** a 6,000-image caries corpus (`CariesXrays_Dataset`, supplied by the user)
  was verified for leakage and geometry, then the **frozen** pipeline was evaluated on it as an
  independent external cohort, against the image-blind molar constant. **Nothing was trained and
  no checkpoint changed.** New script: `scripts/eval/cariesxrays_external.py`, which imports
  `ningxia_external.match_by_centroid` rather than reimplementing it, so the cohorts stay
  comparable. Prompted by a request to use DentFound (Zhu et al., *Nat. Biomed. Eng.* 2026,
  doi:10.1038/s41551-026-01713-8) plus this dataset to improve the caries score.

### The corpus, and why it is not yet citable

- 6,000 images (**5,992 unique**, 8 internal duplicates), **13,785** boxes, single class `Decay`,
  Pascal VOC, panoramic, all height 1280; median lesion **62×74 px = 0.145%** of image area;
  34 images carry zero boxes. That is **13.1× the positive supervision and 23.1× the images** of
  `crops_v3_phase1`.
- **Provenance is UNRESOLVED and this blocks publication.** No README, no licence;
  `<source><database>` is the LabelImg default `Unknown`; the XML `<path>` fields point at
  `F:\datasets\labeled\source6000-label1-all\all-6021\img` — a private Windows working
  directory, not a released dataset. File IDs run **415–30,664 for 6,000 files**, i.e. a
  caries-selected subset of a ~30k pool, and the corpus carries an internal `img`/`test` split
  (5,208 / 792). Searches for `"source6000-label1-all"` and `"all-6021"` return nothing.
  **It cannot enter a Data Availability statement until someone identifies it.**
- **Leakage: none, verified three ways.** (1) 0 MD5 overlap against the DENTEX evaluation pool
  (250), both DENTEX training subsets (705, 623) and Ningxia (4,478). (2) A **positive control** —
  the known byte-identical pair `train_332` ≡ `test_181` — scores dHash distance **0**, so the
  perceptual method detects real duplicates. (3) The dHash distribution over **1.5M** pairs has
  min 2, mean 23.7, and only **36 pairs ≤ 5**; one caries image matched **three different**
  DENTEX images at distance 2–3, which a true duplicate cannot do, and visual inspection
  confirmed different patients, dentition stages and restorations.

### A geometry defect caught before it cost anything

- **27.3% of the XMLs (1,637 files, 4,055 boxes) carry a WRONG `<size>`** — always the width,
  stated 2648 where the image is really 2440 / 2324 / 2444; height always correct. **A converter
  that normalises by the XML `<size>` silently corrupts a quarter of the corpus**, which is how a
  90-epoch A100 run was voided on 2026-08-27a.
- The **coordinates are in the true image frame**, established two ways: **0 of 4,055** boxes
  exceed the actual width (max `xmax/width` = 0.809), and rendering boxes onto mismatched images
  places them **on teeth** rather than displaced right by the ~8.5% the stale width implies.
  **Rule now enforced in code: read width/height from the decoded image, never the XML.**
- **Detector transfer gate PASSED** before any evaluation: **26.08 teeth/image** against DENTEX's
  22.0 and Tufts' ~26. The Tufts-trained detector generalises to this cohort.

### The result

Frozen pipeline vs the image-blind constant `{16,17,26,27,36,37,46,47}`, centroid containment,
identical matcher to the Ningxia arm:

| run | n images | n lesions | pipeline | constant | paired delta | 95% CI |
|---|---|---|---|---|---|---|
| first 600 by id | 600 | 1,620 | 0.3086 | 0.5488 | **+0.2401** | [+0.2110, +0.2690] |
| **random 1,500, seed 42** | **1,500** | **3,421** | **0.3090** | **0.5612** | **+0.2523** | **[+0.2321, +0.2726]** |

- The two draws' intervals overlap heavily, so **the prefix sample carried no ordering bias** —
  checked because file IDs are not shuffled and a `[:N]` prefix could have been one acquisition
  batch. The randomised run is the number of record.
- **The constant does not win by brute force.** It flags 6.45 teeth/image against the pipeline's
  3.94 (+64%), but its **match rate is also higher** (0.2065 vs 0.1895), so it wins on
  per-flagged-tooth efficiency too. On DENTEX the brute-force defence held (859 vs 755 teeth at
  the same match rate, 2026-08-28d); **here it does not.**
- **Mechanism, measured rather than asserted** (300 images, 859 lesions, each mapped to the
  detected tooth containing it): **72.0% of lesions sit on molars** (premolar 20.5%, canine 3.7%,
  incisor 3.7%), and **60.2% land on exactly the eight teeth the constant flags**. The constant's
  0.561 is near its structural ceiling of ~0.60 on this cohort. It is exploiting an extremely
  molar-concentrated caries distribution, not reading anything.
- **A ceiling that binds every tooth-level arm here:** **22.1% of lesions fall inside no detected
  tooth at all.**

### Where this leaves the three cohorts

| cohort | n | constant − pipeline | verdict |
|---|---|---|---|
| DENTEX | 164 img / 479 lesions | +0.046 [+0.006, +0.089] | constant wins |
| Ningxia, 4 hospitals | 337 img / 1,013 lesions | −0.009 [−0.049, +0.030] | indistinguishable |
| **CariesXrays** | **1,500 img / 3,421 lesions** | **+0.252 [+0.232, +0.273]** | **constant wins decisively** |

- **Key decision / insight — and it corrects a claim made in this session.** A lesion-detector
  proposal (Path B) was argued partly on the premise that "a constant cannot win at lesion level,
  because it would have to place boxes". **This cohort falsifies that premise**: a constant wins
  at lesion level by 25 points. The premise was stated as a conclusion without being tested,
  which is the error this project's own §8.22 exists to criticise. Any future lesion-detector
  work must be justified against a much stronger constant than was assumed.
- **For the paper this is the strongest evidence yet for the central thesis.** *"A tooth-level
  score cannot establish that a system reads the radiograph"* is now supported on **five
  institutions plus a 6,000-image independent cohort**, with the mechanism quantified (72% molar
  concentration) rather than asserted, and with the largest lesion count of any cohort — 3,421,
  more than DENTEX and Ningxia combined.
- **DentFound — what was verified and what transfers.** Identity confirmed from the PDF metadata
  and text. Its Kaggle sources are named in Data Availability and are the *dual-labeled* corpus
  (stated as **2,000 images**; this repo measured **500 images / 2,066 labels** on 2026-08-28c —
  a discrepancy worth a footnote if cited) and *Teeth Segmentation on Dental X-ray Images* (598
  images / 15,318 polygons), plus 100 hand-labelled mixed-dentition images, **2,698 total, used
  only to train their tooth-identification model**. Two of their ablations are relevant:
  instance masks give **+20.35/+23.01/+23.11% relative** P/R/F1 on diseased-tooth identification
  (P<0.001) — evidence for wiring R2, though measured against a VLM with *no* tooth grounding, so
  not directly transferable to a pipeline that already crops per tooth; and **resolution gains
  were NOT significant** (336→1024, P>0.05), independently corroborating this project's own
  measurement that resolution is a no-op here.
- **Source:** `scripts/eval/cariesxrays_external.py`,
  `outputs/cariesxrays_external_rand/cariesxrays_external_{pipeline,constant-molars}.json`,
  `outputs/cariesxrays_external/` (the prefix run, retained as the ordering-bias control).
- **Follow-ups:** (1) **Identify the dataset's provenance and licence** — free, and it gates
  everything downstream including whether this result is publishable at all. (2) The full 6,000
  are available if a tighter interval is ever needed; 1,500 already gives ±2 pp. (3) Path B (a
  trained lesion detector) is **not** retired but must now clear a constant scoring 0.561, and
  needs its own pre-registered bar. (4) `run_inference.py` was never touched; the pipeline is
  byte-identical and all invariants still hold.

---

## 2026-09-01b — CariesXrays provenance RESOLVED: it is a peer-reviewed AAAI 2024 benchmark

- **What was done:** the 2026-09-01 entry recorded the 6,000-image caries corpus as having
  **unidentified provenance**, and flagged that as a hard blocker on publishing anything measured
  on it. The user supplied the source repository. **It is identified, peer-reviewed and citable.
  The blocker is cleared.** This entry supersedes that caveat; the measurements themselves are
  unchanged.
- **The dataset:**

  > Chen, B., Fu, S., Liu, Y., Pan, J., Lu, G., Zhang, Z. **"CariesXrays: Enhancing Caries
  > Detection in Hospital-Scale Panoramic Dental X-rays via Feature Pyramid Contrastive
  > Learning."** *Proceedings of the AAAI Conference on Artificial Intelligence*, vol. 38,
  > no. 20, pp. 21940–21948, 2024. DOI **10.1609/aaai.v38i20.30196**.
  > Code/data: `github.com/Binz-Chen/AAAI2024_CariesXrays`

- **Verified independently four ways** rather than trusting the repository README: AAAI's own OJS
  (`ojs.aaai.org/index.php/AAAI/article/view/30196`), ACM DL (which supplies the DOI), DBLP
  (`conf/aaai/ChenFLPLZ24`), and AAAI's Underline session page. The paper is real, peer-reviewed
  and in the AAAI 2024 proceedings.
- **Their stated counts vs what this repo measured on the local copy:**

| | paper states | measured here | note |
|---|---|---|---|
| images | 6,000 | **6,000** | exact match |
| caries instances | 13,783 | **13,785** raw `<object>` entries | **+2** |
| — after removing 1 degenerate box (x2≤x1 or y2≤y1) | | 13,784 | **+1** |
| exact-duplicate boxes within a file | | **0** | not the cause |

  The residual **+1 (0.007%)** is a counting-convention difference, not a data problem. Recorded
  because this project does not round discrepancies away — the same discipline that caught the
  "2,000 vs 500 images" gap in the Kaggle dual-labeled corpus (2026-08-28c).
- **Licence: still not stated.** The repository has **no LICENSE file** (HTTP 404) and the GitHub
  API reports `license: null`. It is a public research benchmark released alongside a
  peer-reviewed paper with an explicit citation request, which is ordinary academic practice —
  but the Data Availability statement should say "released publicly by the authors; no explicit
  licence stated; cited as requested" rather than assert a licence that does not exist.
- **What this changes for the paper.** §8.25's result — the constant beating the pipeline by
  **+0.252 [+0.232, +0.273]** on 1,500 images / 3,421 lesions — was measured on what was then an
  anonymous folder. It is now a measurement on a **published, peer-reviewed, hospital-scale
  benchmark with its own baselines**, annotated by dental professionals. That is a materially
  stronger exhibit: the cohort is independently described, citable, and reproducible by others.
- **Key decision or insight:** nothing measured changes. What changes is that the single largest
  caveat on the session's headline finding is removed. The **remaining** caveat is unchanged and
  still real — the corpus's annotation *exhaustiveness* is not documented, so `match_rate` stays
  a diagnostic and a flagged tooth with no box is still not a confirmed false positive.
- **Source:** `github.com/Binz-Chen/AAAI2024_CariesXrays`, AAAI OJS 30196, DOI
  10.1609/aaai.v38i20.30196, DBLP `conf/aaai/ChenFLPLZ24`.
- **Follow-ups:** (1) Add the citation to `paper/source.bib` when §8.25 is folded into
  `main.tex`. (2) The AAAI paper reports FPCL baselines on this benchmark — **not read here, and
  no number from it should be quoted until it is**. It would give any future lesion detector
  (Path B) a published comparison point. (3) The forensic path evidence
  (`F:\datasets\labeled\source6000-label1-all\all-6021`) is consistent with the authors' own
  working directory and is no longer a concern.

---

## 2026-09-01c — §8.25 folded into the manuscript; an 8th citation error found and fixed

- **What was done:** the CariesXrays cohort was written into `paper/main.tex` and the AAAI
  citation corrected. **No measurement changed.** `scripts/verify_paper_numbers.py` grew from
  **82 to 90** asserted claims and passes with no drift.
- **⚠️ AN INCORRECT CITATION WAS ALREADY IN THE MANUSCRIPT, CITED TWICE.** `source.bib` already
  held a `chen2024cariesxrays` entry (used at `main.tex` lines 136 and 234) with the **right
  title and pages** but pointing at the **adjacent AAAI article id**:

| field | was | corrected to |
|---|---|---|
| DOI | `10.1609/aaai.v38i20.30197` | `10.1609/aaai.v38i20.30196` |
| URL | `.../article/view/30197` | `.../article/view/30196` |
| author | Fu, **Shuai** | Fu, **Sisi** |

  Verified by fetching AAAI OJS **30197** directly: it is *"Referee-Meta-Learning for Fast
  Adaptation of Locational Fairness"* (Weiye Chen et al., pp. 21949–21957) — an unrelated paper on
  spatial fairness. The correct record is **30196**, pp. 21940–21948, confirmed against AAAI OJS,
  ACM DL and DBLP. **The 2026-08-28 citation audit found 7 errors including 4 wrong DOIs; this is
  an 8th that survived it**, and it was only found because the dataset was independently
  identified. Worth re-running `scripts/audit_citations.py` against publisher records, not just
  internal consistency.
- **What was added to `main.tex`:** a corpus-table row and footnote; a paragraph in
  §Data/External data stating the benchmark, the seed-fixed 1,500-image draw, the unverified
  annotation exhaustiveness and the 22.1% of lesions inside no detected tooth; a new
  **Table~\ref{tab:cohorts}** giving the three-cohort comparison; and a rewritten closing
  paragraph for the external-results subsection. Abstract and the contributions list updated for
  consistency ("five institutions" → "six independent cohorts").
- **The claim in the paper changed, and strengthened.** It previously read *"a purpose-built
  pipeline and an image-blind prior cannot be reliably told apart by these metrics"*, resting on
  DENTEX (+4.6) and a Ningxia tie (−0.9). With CariesXrays at **+25.2 pp [+23.2, +27.3]** the
  supported statement is stronger: **the three cohorts do not support the claim that the pipeline
  outperforms an image-blind prior, and the margin runs from a tie to 25 points depending only on
  which cohort is scored** — 26 points of swing across one cohort's sites, 25 across cohorts. The
  brute-force defence that held on DENTEX (14% more teeth at equal hit rate) is explicitly
  retired for this cohort, where the constant flags **64% more teeth and still has the higher hit
  rate (0.206 vs 0.190)**.
- **The number checker caught a transcription error of mine.** I wrote the constant's match rate
  as 0.207; the artefact is 0.2065, which formats to **0.206**. Corrected in favour of the
  artefact. This is the checker doing precisely the job it was built for on 2026-08-28.
- **⚠️ COMPILATION IS NOT VERIFIED.** There is **no LaTeX toolchain on this machine** (no
  `pdflatex`, `bibtex`, `latexmk` or `tectonic`; no MacTeX or TeX Live anywhere). Edits used only
  constructs already present in the file, and every static check available was run and passes:
  brace balance (433/433), all 9 environment pairs matched, **all `\cite` keys resolve**, all
  `\ref` targets have labels, per-tabular column arity correct for all six tabulars, and no
  unescaped `%`. **Someone must compile before submitting** — the previously verified
  "0 errors / 0 overfull boxes / 12 pages" no longer holds without a rebuild, and the paper is now
  **longer**, which matters against the outstanding venue-length cut.
- **Source:** `paper/main.tex`, `paper/source.bib`, `scripts/verify_paper_numbers.py`
  (82 → 90 claims), AAAI OJS 30196 / 30197, DBLP `conf/aaai/ChenFLPLZ24`.
- **Follow-ups:** (1) **Compile the manuscript and re-check page count and overfull boxes.**
  (2) Re-run `scripts/audit_citations.py` with publisher lookups — one wrong DOI survived a full
  audit. (3) The AAAI paper's own FPCL baselines on this benchmark are **still unread**; no number
  from it may be quoted until they are.

---

## 2026-09-01d — DOI audit against the registry: 22 of 63 checkable citations are broken

- **What was done:** every DOI in `paper/source.bib` was dereferenced against the DOI registry.
  **Read-only; no citation was changed** — the user asked for the audit to be saved and acted on
  separately. New script `scripts/verify_citations_crossref.py`; findings in
  `outputs/citation_audit/FINDINGS.md`, raw log alongside it.
- **Two defects in `audit_citations.py` fixed first.** It carried a **hardcoded Windows path**
  (`C:\Users\csdee\...`), so it could not run on this machine at all — which is why it had never
  actually been re-run — and it makes **no network call**, so it can only catch a citation that
  supports the wrong claim, never one whose DOI points at the wrong paper. Path is now
  repo-relative; the verification lives in the new script.
- **Method, and why the first attempt was wrong.** A Crossref-only version reported 16 failures
  that were false: **arXiv DOIs are registered with DataCite**, so Crossref 404s them. The final
  version resolves twice against `doi.org` itself — `doiRA` for the registering agency (where
  *"DOI does not exist"* is decisive) and **content negotiation** for CSL-JSON metadata, which
  works whichever agency registered it. That correction removed every arXiv false positive.
  LaTeX accent macros are stripped before author comparison, and year gaps of 1 are notes rather
  than errors (online-first vs issue year).
- **Validated against a known answer before being trusted:** the corrected `chen2024cariesxrays`
  DOI scores title overlap **1.00**; the wrong DOI it replaced scores **0.05** and correctly
  names the unrelated paper it resolves to. The tool catches what the 2026-08-28 manual audit
  missed.
- **Result — 63 entries carry a DOI, 19 do not:**

| category | count |
|---|---|
| clean | **40** |
| **DOI resolves to a DIFFERENT paper** (title overlap 0.00) | **11** |
| **DOI not registered with any agency** | **11** |
| author notation only (`Yalım`/`Yalim`) — cosmetic | 1 |
| no DOI, not checkable by this method | 19 |

  **22 of 63 checkable entries (35%) have a broken DOI.** Examples of the first kind:
  `karamuftuo2025panoramic` resolves to *Foundations of Pediatric Lifestyle Medicine*;
  `kong2024integrating` to OCT-guided femtosecond laser keratoplasty; `zanini2024systematic` to
  super-resolution cervical-spine MRI; `adnan2024orthopantomogram` to a COVID household-survey
  dataset.
- **What this establishes, stated precisely.** These 22 DOIs **do not identify the works the
  bibliography claims**, verified against the agency-agnostic registry rather than one provider.
  It does **not** establish that the cited papers are fabricated — a real paper can carry a
  mistyped or hallucinated identifier. **Separating "real paper, wrong DOI" from "no such paper"
  requires a manual title lookup for each of the 22 and is deliberately not attempted here.**
  The 19 DOI-less entries were not checked by any means; absence of a check is not a pass.
- **Key decision or insight:** **this blocks submission**, and it is the same failure class the
  2026-08-28 audit found (7 errors including two invented titles) without clearing. A reviewer who
  dereferences one bad DOI will check the rest. The lesson worth carrying is narrower than "audit
  citations": **an audit that cannot fail is not an audit** — the old script printed 26 citations
  for eye-review and passed a DOI pointing at a different paper, twice, because nothing in it ever
  dereferenced anything.
- **Source:** `scripts/verify_citations_crossref.py`, `outputs/citation_audit/FINDINGS.md`,
  `outputs/citation_audit/doi_verification_report.txt`, `scripts/audit_citations.py` (path fix).
- **Follow-ups:** (1) **Manually resolve each of the 22 by title** and decide per entry: correct
  the DOI, or remove the reference. (2) Decide what to do about the 19 unverifiable entries.
  (3) Add `verify_citations_crossref.py` to whatever pre-submission checklist exists, so this
  cannot regress. (4) Nothing here changes any measurement; the pipeline and all results are
  untouched.

---

## 2026-09-01e — Lever 1 pre-registered; multi-corpus detector dataset built and geometry-gated

- **What was done:** the acceptance bar for the multi-corpus detector retrain was written down
  **before** any data was converted, and the dataset was then built and passed a three-part
  geometry gate. **No GPU was rented and nothing was trained** — this is the local half that the
  pre-registration requires to pass first.
- **The hypothesis, and why it is not merely "more data":** Stage-2 decomposes exactly as
  `recall × of-detected` = 0.706 × 0.826 = **0.583**. The numbering half is strong; **detector
  recall is the binding constraint**, with 29.4 % of teeth never reaching Stage 2. The detector
  trains on 700 Tufts images; `quadrant_enumeration` adds 634 panoramics with 18,095 tooth boxes,
  already local. Precedent: DentFound pooled corpora the same way (2,698 images) for its
  tooth-identification model.
- **Leakage gate — run before the pre-registration was written, because it could have voided the
  whole experiment.** The Stage-2 benchmark is 164 leak-free `DENTEX/disease/` images. By MD5:
  **85 of the 250 pool images are in `quadrant_enumeration`, and all 85 sit inside the existing
  86-image exclusion list**, so **overlap with the 164 is 0**. Training the detector on that
  corpus does not touch the benchmark.
- **Pre-registered, in `outputs/detector_multicorpus/PRE_REGISTRATION.md`:**
  **PRIMARY** — FDI exact end-to-end on the 164, paired cluster bootstrap over images (10,000
  resamples, seed 42) against a **same-day control**; succeeds only if the 95 % CI **excludes
  zero**. **GUARD** — Tufts frozen test box mAP@0.5 **≥ 0.75**, which is `T0.6` §2's *existing*
  pre-registered floor reused verbatim rather than a number invented for this arm. **Adoption
  requires both.** Three risks recorded in advance, the sharpest being that recall and
  of-detected can move in opposite directions and cancel — R1 showed spurious boxes perturb the
  Hungarian assignment across a whole quadrant — so the decomposition is reported, not just the
  product.
- **New code:** `src/orientation.rot_box` / `rot_boxes` (upright → rotated), the missing inverse
  of the existing `unrot_box`. Put in the module that owns rotation rather than duplicated in a
  converter, and covered by `tests/test_orientation_roundtrip.py` — 37 property tests asserting
  `unrot_box(rot_box(b)) == b` across both rotation directions, four frame geometries and edge
  boxes. Suite is now **159 tests**.
- **Dataset:** `scripts/yolo/build_multicorpus_detector_dataset.py` →
  `data/detector_multicorpus/` (gitignored, regenerable).

| split | images | boxes | composition |
|---|---|---|---|
| train | **1,334** | 28,832 | 700 Tufts + 634 DENTEX — **1.91× the current 700** |
| val | 150 | 2,256 | **Tufts only, unchanged** |
| test | 150 | 2,309 | **Tufts only, unchanged — the frozen guard** |

  Keeping val/test Tufts-only is deliberate: it keeps `Tufts test box mAP@0.5` directly
  comparable to the frozen detector's 0.810, which is what the guard measures.
- **Geometry gate, three parts, all passed.** (1) Per-box round trip on every converted
  annotation. (2) **18,095 DENTEX boxes re-scored against their source COCO boxes: median IoU
  1.0000** against a 0.99 abort threshold. (3) Rendered samples from both corpora inspected —
  both now sit in the detector's frame with the jaw vertical, DENTEX boxes tracking every tooth,
  and the rotated vendor watermark confirming the pixels turned with the labels.
- **The gate fired once, and the defect was mine, not the data's.** The first run aborted on
  `train_217.png` with a round-trip mismatch. Investigated rather than loosened: the coordinates
  agreed to **1.1e-13**, and the failure was my equality test using `round()` across a `.5`
  boundary — `round(999.5) = 1000` under banker's rounding but
  `round(999.4999999999999) = 999`. Replaced with a 1e-6 tolerance. **The geometry was never
  wrong**; recorded because a gate that stops the build and is then investigated is the gate
  working, and this is the failure mode that voided a 90-epoch A100 run on 2026-08-27a.
- **Two build decisions worth stating.** Tufts boxes are **derived from `dataset_seg`'s polygon
  labels** (exact min/max) rather than re-converted from source, so the only new geometry risk is
  the DENTEX side, which is the side that gets re-scored. And rotated DENTEX is written as
  **JPEG q95** — Tufts is *already* JPEG, so this is the consistent choice, and it cuts the
  dataset from ~2.1 GB to **816 MB**, saving roughly 40 minutes of billed upload on a running
  A100 (~₹56).
- **Also recorded:** `quadrant_enumeration` ships 634 image entries but only **623 unique MD5s** —
  11 duplicate images. Left in, since duplication at this rate is immaterial against 1,334 images,
  but noted rather than discovered later.
- **Source:** `outputs/detector_multicorpus/PRE_REGISTRATION.md`,
  `scripts/yolo/build_multicorpus_detector_dataset.py`, `data/detector_multicorpus/meta.json`,
  `src/orientation.py`, `tests/test_orientation_roundtrip.py`.
- **Follow-ups:** (1) Re-measure the **same-day control** (current detector, this machine, the 164
  images) before renting — CPU work, free, and required by the pre-registration. (2) Then rent one
  **A100-40GB at ₹84.24/hr** (~₹253 estimated) and train. (3) Report the recall/of-detected
  decomposition, not just end-to-end. (4) Nothing here changes the pipeline; all invariants hold.

---

## 2026-09-01f — The Lever-1 dataset was VOID; caught before renting, and rebuilt

- **What was done:** a pre-training soundness check on the multi-corpus detector dataset found
  that **its Tufts half was built from the WITHDRAWN pre-fix corpus** and was geometrically
  void. Source corrected, dataset rebuilt, and the gate that missed it strengthened. **No GPU was
  rented; balance is unchanged at ₹1,105.99.** This cost time, not money — which is the entire
  purpose of the local gate.
- **How it surfaced.** A GT box-convention comparison between corpora, run as an ordinary
  sanity check before training:

| corpus | GT median w/h | detector's predicted w/h | |
|---|---|---|---|
| Tufts | **0.364** | 2.665 | **7.3× disagreement** |
| DENTEX | 2.877 | 2.561 | 1.12× — fine |

  A tooth is ~3× taller than wide upright (w/h ≈ 0.35, `PAPER_MATERIAL.md` §6.1); a 90° rotation
  inverts that to ≈ 2.9. **Tufts GT was reporting the UPRIGHT aspect while its images are in the
  ROTATED frame.** Rendering GT against detector predictions confirmed it: the Tufts boxes were
  90° out and **parked off the dentition in the top-right corner.**
- **Root cause.** `data/tufts/dataset_seg/` on this machine is the **pre-fix corpus from the void
  26 Aug R1 run** (`RESULTS_LOG` 2026-08-27a: *"every instance mask was spatially misaligned with
  its image"*). The corrected `dataset_seg_v2` was never built here — `.gitignore` names it as
  the *"Corrected R1 seg dataset (27 Aug 2026)"*. Transposing x/y does **not** repair it; the
  centroids still cluster in a sub-region. The corpus is simply void.
- **⚠️ THE GATE THAT LET IT THROUGH, AND WHY.** The build script's own docstring asserted
  *"the only new geometry risk is the DENTEX side, which is re-scored below."* **That assumption
  was the defect.** DENTEX was re-scored against its source and passed at median IoU 1.0000 —
  correctly — while **Tufts was taken on trust because it was believed already verified.** A gate
  that checks only the half you suspect is not a gate. This is the second time an unverified
  "already correct" assumption has produced void training data in this project.
- **Had it trained:** ~₹253 spent, 150 epochs of smoothly-falling loss on half-garbage labels,
  nothing erroring, and a confident null reading *"more data did not help"* — an exact rerun of
  the 26 Aug failure.
- **The fix, and how it is now proven.** Tufts boxes now come from
  **`Segmentation/teeth_bbox.json` + `Radiographs_rotated/`** — the annotation the canonical
  0.7824 detector was trained on, already in the portrait frame and never touched by the
  `teeth_polygon.json` `[y,x]` transpose. Keyed by the frozen `split_v1.csv`, with the same
  degenerate-box guard (66 source objects carry corrupt 1×1/1×2 boxes,
  `T0.6_detector_reconciliation.md` §3.5).

  **A hard verification target replaced the heuristic one.** `model_metrics.md` records the frozen
  detector's own instance counts, and the rebuild reproduces them **exactly**:

| split | canonical | rebuilt | |
|---|---|---|---|
| val | 3,794 | **3,794** | MATCH |
| test | 3,924 | **3,924** | MATCH |

  The build now **aborts** if either count differs. Exact agreement on two independent integers is
  far stronger evidence than any aspect-ratio heuristic, and it proves this conversion reproduces
  the canonical one.
- **Gate strengthened:** GT is now checked against the frozen detector **for every corpus**, not
  just the new one. Post-rebuild: Tufts 1.06× agreement, DENTEX 1.12× (was 7.3× for Tufts).
  Visual overlay confirms GT and detector boxes now coincide on every tooth.
- **Final dataset:** train **1,334** images / **36,316** boxes (700 Tufts + 634 DENTEX, **1.91×**
  the current 700); val 150 / 3,794; test 150 / 3,924 — both Tufts-only and canonical. 816 MB.
  The void build had 28,832 boxes, i.e. it was also **losing ~40 % of the Tufts boxes**.
- **Same-day control, measured earlier today** (`outputs/detector_multicorpus/control_sameday/`):
  recall **0.7083**, of-detected **0.8250**, **end-to-end 0.5844** — reproducing the 27 Aug
  published run to within +2 detected and +1 exact tooth of 936, well inside the documented
  9-tooth noise floor. All Lever-1 deltas will be measured against **0.5844**.
- **Key insight worth carrying:** the previous entry's lesson was *"an audit that cannot fail is
  not an audit."* This one is its twin: **a gate that only checks the half you already suspect is
  not a gate.** Both failures came from trusting a component labelled verified without re-deriving
  the verification in the current context.
- **Source:** `scripts/yolo/build_multicorpus_detector_dataset.py`,
  `data/detector_multicorpus/meta.json`, `outputs/detector_multicorpus/PRE_REGISTRATION.md`.
- **Follow-ups:** (1) Train — the pre-registration's local gate now genuinely passes. (2) Consider
  rebuilding `dataset_seg_v2` on this machine, since `dataset_seg` is void and anything else
  reading it inherits the defect. (3) `validate_fdi_assignment.py`'s `--head-weights` still
  defaults to head **v1.0** while the pipeline default is v2.0 — a live trap for the next re-run.

## 2026-09-01g — GPU rented for Lever 1, then aborted mid-upload; nothing trained

- **What was done:** Provisioned a JarvisLabs GPU to run the Lever-1 two-arm detector retrain
  (entry 2026-09-01e/f). `jl create --gpu A100` returned *"A100 not available at this moment"*
  for both the 40 GB and 80 GB cards, so an **A30 24 GB (₹38.88/hr)** was taken instead — it
  holds R1's `batch 32 @ 1024` config unchanged (R1 peaked at 17.9 GB). Upload of
  `data/detector_multicorpus/` (816 MB, 3,268 files) was started with `jl upload`, which runs
  as an rsync of many small files and moved at only ~19 MB/min. It also nested the tree one
  level deep (`/home/detector_multicorpus/detector_multicorpus/`), which the plan was to absorb
  with a `--data-root` flag rather than a code change. **The user terminated the instance before
  the upload finished.** No training started.
- **Dataset / config:** n/a — no run executed.
- **Metrics:** none. **Spend ₹21.45** (instance time during the upload attempt). Balance
  **₹1,105.99 → ₹1,084.54**. No instances running or paused afterwards (`jl list` empty).
- **Key decision or insight:** `jl upload` of a directory of thousands of small image files is
  the bottleneck, not the GPU. **Next attempt: `tar` the dataset locally, upload one ~800 MB
  file, extract on the box.** Also re-run the geometry gate *on the rented box* after extraction
  (the R1 lesson from 2026-08-27a), before launching either arm.
- **Source:** JarvisLabs account activity; `transfer.md` §3 Track B (B1), §6, §8;
  `docs/research/GPU_SETUP.md` §0 (macOS `jl` runbook).
- **Follow-ups:** (1) Re-tar and re-upload; train Control B (`--arm tuftsonly`) then Arm
  (`--arm multicorpus`), ~150 epochs each, ~₹210 total on an A30. (2) Score both against the
  same-day control (end-to-end 0.5844) per `outputs/detector_multicorpus/PRE_REGISTRATION.md`.
  (3) The `jl` CLI and this machine's `macos-m4pro` SSH key are now registered, so the next
  attempt starts from provisioning, not setup.

## 2026-09-01h — Lever 1 trained: +34.9 pp end-to-end FDI on DENTEX, but the Tufts guard fails → ABLATION

- **What was done:** Ran the pre-registered two-arm Lever-1 detector retrain
  (`outputs/detector_multicorpus/PRE_REGISTRATION.md`) on a rented RTX PRO 6000 Blackwell
  (JarvisLabs 491623, IN1, ₹179/hr). Dataset `data/detector_multicorpus/` was re-gated **on the
  rented box** after upload — canonical Tufts box counts (3,794 / 3,924) reproduced exactly,
  DENTEX round-trip IoU 1.0, aspect ratios consistent, renders inspected. (One tar-hygiene bug
  caught here: macOS `tar` shipped AppleDouble `._*` files that doubled the file counts and would
  have fed YOLO garbage — deleted, re-verified PASS.) Both arms trained with the canonical config
  verbatim (`scripts/yolo/train_multicorpus_detector.py`, ultralytics pinned 8.4.127), early-stopped
  at epoch 106 / 105 of 150. Scored on **this machine** against the same-day control with
  `scripts/eval/validate_fdi_assignment.py --head-weights models/10/...` +
  `scripts/eval/score_lever1_arm.py` (paired cluster bootstrap over the 164 images, 10k, seed 42).
- **Dataset / config:** Control B = YOLOv11l **detect**, Tufts only (700 img / 18,221 boxes).
  Arm = YOLOv11l **detect**, Tufts + DENTEX `quadrant_enumeration` (1,334 img / 36,316 boxes).
  Both val/test are Tufts-only and canonical. Only deliberate deviations from the frozen detector:
  detect head (DENTEX has no polygons) and the train split.
- **Metrics** (primary = FDI exact end-to-end on 164 leak-free DENTEX images; guard = Tufts frozen
  TEST box mAP@0.5):

  | | recall | of-detected | end-to-end | Tufts test mAP@0.5 |
  |---|---|---|---|---|
  | Control A (deployed seg, same-day) | 0.708 | 0.825 | **0.5844** | 0.810 |
  | Control B (Tufts detect) | 0.831 | 0.724 | 0.6015 | 0.724 |
  | Arm (Tufts+DENTEX detect) | 0.995 | 0.939 | **0.9338** | **0.647** |

  Paired Δ end-to-end, 95% CI: **Arm − Control A +34.9 pp [+30.8, +39.0]** (excludes 0);
  **Arm − Control B +33.2 pp [+29.5, +37.0]** (excludes 0 — the pure data effect);
  Control B − Control A +1.7 pp [−3.4, +6.8] (**includes 0** — the seg→detect head change is n.s.).
- **Key decision or insight:** **ABLATION. NOT adopted; pipeline default detector unchanged.**
  The pre-registered rule requires BOTH primary significant AND guard met. Primary succeeds
  overwhelmingly; **the guard fails (0.647 < 0.75)** — this is exactly the pre-registered
  "domain dilution" risk #2, now confirmed: adding DENTEX training data costs Tufts test box
  mAP@0.5 ~7.7 points (Arm − Control B on the guard metric). Same disposition as Stage-2 head v3
  (2026-08-28c) and caries gate v4 (2026-08-31). **The bar was not moved.**
  - **The entire Lever-1 gain is the added DATA, not the head change.** Control B (detect,
    Tufts-only) vs Control A (seg): end-to-end delta is not significant. Arm vs Control B: +33.2 pp.
  - **What the 93.4% is:** an **in-domain** number — the Arm's detector is now DENTEX-trained and
    the head (models/10) was already DENTEX+Tufts-trained, evaluated on held-out DENTEX. It
    confirms the paper's core thesis in its strongest form: **the 58.3% headline is
    detector-DOMAIN-limited, not numbering-limited.** A same-domain detector on the same metric
    nearly doubles end-to-end.
  - **What it is NOT:** image-level leakage. The 164 eval images were checked against the 634
    training images three ways — 0 byte-identical (MD5), 0 filename match, 0 perceptual
    near-duplicate (aHash 16×16: min Hamming 22, median 40; byte-identical calibration = 0,
    intra-corpus different-patient NN median = 32). Disjoint patients, same institution. Nor is it
    metric-gaming: rendered detections are ~1 box/tooth along the arch, and the eval metric is
    genuinely generous (IoU 0.30 match, scores only the ~5.7 annotated pathological teeth/image).
  - **Manuscript caveat:** 93.4% is Tufts-detector-free **in-domain**; 58.3% is Tufts→DENTEX
    **cross-domain** on the detector. Different generalisation scenarios — do not present 93.4%
    as "the pipeline works everywhere."
  - **A run-reproducibility note:** Control B's Tufts val mAP@0.5 best = 0.782, matching the
    canonical bbox detector's *test* 0.7824 — but Control B's own *test* came in at 0.724, a
    ~5 pt val→test drop consistent with the canonical run's own noted drop, and Control B sits
    ~5 pt below canonical on **both** val and test uniformly. Attributed to A100→Blackwell +
    torch 2.2→2.11 training variance, not a data defect. Even correcting for it, the Arm's
    guard would be ~0.705 — still under 0.75.
- **Source:** `models/13_detector_multicorpus_lever1/run_summary.txt` (+ weights, gitignored,
  sha256 recorded there); `outputs/detector_multicorpus/{multicorpus,tuftsonly}/`,
  `*_scored.json`; `scripts/yolo/train_multicorpus_detector.py`,
  `scripts/yolo/build_multicorpus_detector_dataset.py`, `scripts/eval/score_lever1_arm.py`.
  Spend ₹267.84 (balance ₹1,084.54 → ₹816.70); instance destroyed, nothing running.
- **Follow-ups:** (1) Fold into `PAPER_MATERIAL.md` §8.16 as the measured confirmation that
  detection domain, not the numbering head, is the 58.3% ceiling — with the in-domain/cross-domain
  caveat stated. (2) Lever 2 (caries lesion detector on CariesXrays) is the remaining score lever;
  it needs its own pre-registration and the AAAI baselines read first. (3) Do NOT chase adoption
  of the Arm by relaxing the guard — the Tufts cost is real and pre-registered.

---

## 2026-09-02 — The 22 broken DOIs: all real papers, wrong identifiers — fixed and re-verified

- **What was done:** Resolved the submission blocker opened by `RESULTS_LOG.md` 2026-09-01d
  (22 of 63 checkable DOIs in `paper/source.bib` broken — 11 resolving to a *different* paper,
  11 unregistered). Every one was looked up by title against Crossref / doi.org / publisher
  sites, the correct DOI confirmed by title-overlap 1.00 against the registry, and the entry
  patched. **All 22 are real, published papers that carried a wrong identifier — zero
  fabrications.** `paper/source.bib` re-audited: **62 clean / 1 flagged**, the flag being
  `yalim2026comparative` (cosmetic `İ`/`ı`, `ğ`/`g` author-accent mismatch only; DOI correct;
  entry uncited in `main.tex`).
- **Dataset / config:** n/a — bibliography. `scripts/verify_citations_crossref.py` (unchanged)
  is the audit; corrections applied by a one-off script, then re-run.
- **Metrics:**
  - Broken checkable DOIs **22 → 0** (1 residual cosmetic author-notation flag, not an error).
  - In **19 of 22** entries the `volume`/`pages` were *also* wrong, and in 2 the `year` — e.g.
    `adnan2024orthopantomogram` v55 p110654 → **v57 p111152**; `cerda2024determining`
    2024→resolves 2024 but was pointed at a 2024 DOI for a **2023** article (10.1186/s12903-023-03819-w,
    BMC Oral Health 24:100); `lim2024dual` year 2024 → **2026** (now published, JPD v135).
    These were corrected from the registry record, not from the old bib fields.
  - **6 `url` fields embedded the old wrong DOI** and were rewritten to `https://doi.org/<correct>`.
    The audit script only checks the `doi` field, so a stale `url` is a second, unchecked vector —
    noted for a follow-up sweep of all 63 `url` fields (not just the 22 touched here).
- **Key decision or insight:** The pattern — wrong DOI, wrong volume, wrong pages, sometimes
  wrong year, but a *real* paper underneath every one — is the signature of generated citation
  metadata that was never dereferenced. It is the same failure class as 2026-08-28's audit
  (7 errors, 2 invented titles) and 2026-09-01c (`chen2024cariesxrays` → adjacent AAAI article).
  **The DOI half of Track A item 2 is now cleared;** what remains is the 19 genuinely DOI-less
  entries (arXiv / web, expected) and the `url`-field sweep.
- **Source:** `paper/source.bib` (git diff), `outputs/citation_audit/RESOLUTION_2026-09-02.md`,
  `outputs/citation_audit/FINDINGS.md` (the original audit), `scripts/verify_citations_crossref.py`.
- **Follow-ups:** (1) Sweep the remaining `url` fields across all 63 entries for stale DOIs /
  non-canonical links — deferred, tracked in `transfer.md` §3. (2) Decide what to do about the
  19 DOI-less entries. (3) Re-run `verify_citations_crossref.py` clean end-to-end (needs
  `PYTHONIOENCODING=utf-8` on this Windows console or it dies mid-render on a Turkish glyph).
  (4) Recompile `paper/main.pdf` — done this session, still **12 pages, 0 errors / 0 undefined
  refs / 0 overfull boxes** with MiKTeX 25.12 (the "no LaTeX toolchain on this Mac" note in
  `transfer.md` §3.1 is stale for the Windows machine).

---

## 2026-09-02b — Lever 2: an off-the-shelf YOLOv11l matches FPCL on the CariesXrays benchmark

- **What was done:** Trained a **standalone caries-lesion detector** (YOLOv11l, `detect`) on the
  CariesXrays benchmark (Chen et al., AAAI 2024) and scored COCO AP on a held-out split, to place
  the project's first number beside a published table on a public benchmark's own metric. The user
  directed this ("forget the publication … start the gpu work") after the §5 council put Lever 2 as
  a GO. **Not wired into the pipeline; adopts no checkpoint; changes no default.** Pre-registration
  `outputs/lever2_cariesxrays/PRE_REGISTRATION.md` written and the dataset built + gated **before**
  the GPU was rented.
- **⚠️ The split is NOT FPCL's.** The official 4,800/1,200 split is not public (checked: FPCL repo
  ships only a 0.5% sample with no `ImageSets`; the Drive download is `Annotations.zip` +
  `JPEGImages.zip` only; DVCTNet's repo has its own gated dataset). This run uses **this project's
  own seed-42 image-level 80/20 split** (4,800 train / 1,200 val) — matching their *ratio* only.
  Every number here is *"same dataset, same ratio, same metric, different random test images"* —
  **indicative placement, not head-to-head.** Must be written that way; never as "beat/matched FPCL".
- **Dataset / config:** `data/cariesxrays_det/` — 6,000 images, single class `decay`, 13,784 boxes
  (paper says 13,783; the +1 is a counting-convention diff, same as `cariesxrays_external.py`).
  27.3% of source XMLs carry a wrong `<size>` width — the builder
  (`scripts/yolo/build_cariesxrays_detector_dataset.py`) reads dims from the decoded image, never
  the XML (`RESULTS_LOG.md` 2026-08-27a precedent). Local geometry gate (0.0 px round-trip, 0
  out-of-range, 0 split overlap, renders eyeballed) + re-gate on the rented box (sha256 match).
  YOLOv11l detect, 1024 px, AdamW lr0 1e-3 cos, `mosaic=0` (house rule), 120 ep / patience 25,
  seed 42, config otherwise verbatim from the canonical detector. **batch auto-reduced 32 → 16**
  after CUDA OOM at 1024 px on the A100-40GB (pre-registered fallback). ultralytics 8.4.127,
  torch 2.11+cu130.
- **Metrics — COCO AP@[.50:.95] on the 1,200-image val split (`best.pt`, epoch 61 of 86 early-
  stopped, re-scored with ultralytics default NMS):**

  | | AP | AP50 | AP75 | P | R |
  |---|---|---|---|---|---|
  | **ours — YOLOv11l, this project's split** | **0.482** | **0.845** | **0.500** | 0.803 | 0.774 |

  Published table (Chen et al., AAAI 2024 38(20) 21940–21948; COCO AP on **their** 4,800/1,200
  split — transcribed from the paper text + DVCTNet arXiv 2508.20813, **re-verify against the
  AAAI PDF before it goes in `main.tex`**):

  | method | AP | AP50 | AP75 |
  |---|---|---|---|
  | RetinaNet R50 | 13.0 | 30.5 | 10.2 |
  | DINO | 37.8 | 75.3 | 29.4 |
  | Faster R-CNN R50 | 39.9 | 78.0 | 37.8 |
  | YOLOX | 40.5 | 81.3 | 36.1 |
  | **FPCL (their method)** | **48.2** | **84.1** | **50.6** |
  | DVCTNet (MICCAI 2025) | 48.9 | 84.7 | 52.2 |

  Training-loop metric agrees (results.csv epoch 61: mAP50 0.8425, mAP50-95 0.4812). A first val
  pass with `iou=0.5` NMS gave 0.4787 / 0.8476 / 0.4916 — within noise; the default-NMS **0.4816**
  is the reported number.
- **Key decision or insight:** **A generic 2024 detector with no caries-specific design reaches
  ~48 AP on this benchmark's data** — level with the task-specific FPCL contrastive-learning
  method and ~8 AP above every off-the-shelf baseline in their table. Because the split differs,
  this is an *approximate* placement, but it is a real, defensible data point for the manuscript:
  the CariesXrays benchmark does not appear to require a specialised architecture to reach its
  reported ceiling. **Nothing in the pipeline changes.** This is one benchmark row, and it does
  not touch the base-rate-dominance finding (§8.22/§8.24) — that is about the *tooth-level* caries
  metric, a different quantity from lesion-level detection AP.
- **Source:** `models/14_cariesxrays_lever2/run_summary.txt` (+ `best.pt`/`last.pt` sha256 there,
  gitignored, local disk only), `results.csv`, `final_val_defaults/`, `val_batch*_pred.jpg`
  (predictions track ground truth, no geometry error);
  `scripts/yolo/{build_cariesxrays_detector_dataset,train_cariesxrays_detector}.py`;
  `outputs/lever2_cariesxrays/PRE_REGISTRATION.md`. JarvisLabs A100-40GB instance 492535, IN2,
  **spend ₹256.61** (balance ₹816.70 → **₹560.09**), instance destroyed, nothing running.
- **Follow-ups:** (1) Fold into `main.tex` as a benchmark-table row in Related Work, with the
  split caveat spelled out and the AAAI numbers re-verified against the PDF. (2) `best.pt`/`last.pt`
  are >50 MB and **not on Drive** — same gap as `models/11`. (3) If a genuine head-to-head is
  wanted, email the FPCL authors (`chenbingzhi@m.scnu.edu.cn`) for the official split and re-run.
  (4) Lever 3 (caries gate v5 on CariesXrays-derived tooth labels) is now cheap to attempt with
  this detector for label generation, but stays below Track A.

---

## 2026-09-03 — Lever A: multi-corpus detector "done right" — ABLATION (primary +34 pp, Guard 2 fails harder than Lever 1)

- **What was done:** Retrained the Stage-1 detector on **4 pooled public tooth-box corpora** —
  Tufts + DENTEX `quadrant_enumeration` + Kaggle "dual-labeled" + UFBA-425 (CC BY 4.0) — with
  **per-corpus balanced sampling** (each corpus's train list repeated to 700 images), to fix the
  domain-dilution that made Lever 1 (`RESULTS_LOG` 2026-09-01h) an ablation. Three arms + a
  same-day Control A re-measure. Pre-registered:
  `outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md` (committed `ac927da` / `cc76ab5`
  before any GPU spend; §4 refined UFBA to an *additive* arm before training because its only
  public form is a 640x640 square Roboflow export with a distorted tooth aspect).
- **Dataset / config:** `data/detector_multicorpus_v2/` (gitignored) — 2,092 train images / 4
  institutions, geometry gate median IoU 1.0000, on-box re-gate `GATE: GO`. Rotated corpora
  capped at 1600 px / JPEG q85 (upload-size mitigation, 1.1 GB -> 467 MB; training imgsz is 1024
  and YOLO letterboxes to ~1024 regardless, gate re-passed). YOLOv11l `detect`, config **byte-
  identical** to `train_multicorpus_detector.py` / the canonical run (batch 32, imgsz 1024,
  150 ep / patience 30, AdamW lr0 1e-3 cos_lr, seed 42, `mosaic=0`, `flipud=0`) — the ONLY
  thing that varies between arms is the `train:` list. Arms: **controlB** = Tufts only (700);
  **arm3c** = Tufts+DENTEX+Kaggle (2,100 balanced, the *primary*); **arm4c** = + UFBA (2,800).
  JarvisLabs RTX PRO 6000 96 GB (instance 496005, IN1 — same GPU class as Lever 1, env torch
  2.11+cu130 / ultralytics 8.4.127 identical), ~4.3 h wall, **~₹735** total (₹2,467 -> ₹1,732;
  ~₹150 pause/resume + failed-upload overhead). Instance destroyed after download + sha256.
- **Metrics — PRIMARY: FDI exact end-to-end on the 164 leak-free DENTEX images** (method=head,
  head=models/10, conf 0.25 / NMS IoU 0.50 / imgsz 1024 / CCW rotation), paired cluster bootstrap
  over images (10k, seed 42):

  | arm | recall | of-detected | **end-to-end** | det/img | Δ e2e vs Control A |
  |---|---|---|---|---|---|
  | Control A (deployed seg) | 0.708 | 0.825 | **0.5844** | 22.0 | — *(reproduces the documented 58.3 % headline exactly)* |
  | **Arm 3C** (Tufts+DENTEX+Kaggle) | 0.996 | 0.932 | **0.9284** | 27.5 | **+34.40 pp [+30.29, +38.54]** — excludes 0 |
  | **Arm 4C** (+ UFBA-425) | 0.990 | 0.937 | **0.9284** | 27.6 | **+34.40 pp [+30.12, +38.71]** — excludes 0 |

  **PRIMARY PASSES** for both arms (pre-reg bar: CI excludes 0 AND lower bound >= +5 pp; actual
  lower bound +30 pp). This **replicates Lever 1's +34.9 pp [+30.8, +39.0]** with 3-4 corpora and
  balanced sampling instead of 2 corpora naively concatenated. **UFBA-425 adds nothing to the
  primary** — Arm 3C and Arm 4C give the identical 0.9284.
- **Metrics — GUARD 2: Tufts frozen TEST box mAP@0.5** (measured on the GPU box on `best.pt`,
  test = 150 frozen Tufts images). Pre-reg rule: Arm >= (Control B) - 4 pp = 0.7243 - 0.04 = **0.6843**.

  | arm | Tufts test box mAP@0.5 |
  |---|---|
  | Control B (Tufts-only detect) | **0.7243** — matches Lever 1's Control B (0.724) to 3 dp; hardware/env parity confirmed |
  | Arm 3C | **0.5852** — 0.099 below the floor -> **GUARD 2 FAILS** |
  | Arm 4C | **0.5520** -> **GUARD 2 FAILS** |

  The decline is **monotonic in corpus count**: Tufts-only 0.724 -> +DENTEX+Kaggle 0.585 ->
  +UFBA 0.552. This is worse than Lever 1's arm (0.647). **The pre-registered hypothesis was
  backwards:** balanced sampling put Tufts at 33 % of the mix (vs Lever 1's 52 %), and a corpus's
  own held-out box mAP scales with its *training share*, not with how balanced the mix is. More
  domains + more balance = MORE dilution of any single domain.
- **Metrics — GUARD 1** (pooled external caries lesion agreement, Ningxia x4 + CariesXrays-1500,
  frozen gate v3.0, each arm's detector swapped in): **RUNNING 3 Sep** — numbers to be added to
  `model_metrics.md`. Does **not** change the verdict: adoption needs primary AND BOTH guards,
  and Guard 2 already failed.
- **VERDICT (pre-registered rule, bar NOT moved): ABLATION.** Primary passes overwhelmingly,
  Guard 2 fails. Pipeline default detector stays `models/11_yolo_seg_tufts_r1`
  (`tooth-detector-seg-tufts-1024-v1.0`). Same disposition as Lever 1, Stage-2 head v3 and caries
  gate v4.
- **Key decision or insight:** Lever A did **not** lift the paper's headline in an adoptable way
  — and the deployed 58.3 % is correctly unchanged. What it *did* give the paper is stronger:
  **(1)** the "58 % ceiling is detector *domain*, not numbering" decomposition now **replicates**
  across corpus configurations (Lever 1 + Lever A, both +34-35 pp in-domain) — a robust result,
  not a one-off. **(2)** A clean 3-point curve for the **in-domain / cross-domain tradeoff of a
  single-class tooth detector**: 0.724 -> 0.585 -> 0.552 on Tufts test as domains are added.
  **(3)** UFBA-425 (aspect-distorted) is inert for the DENTEX-domain metric and only adds Tufts
  dilution — the pre-registration correctly kept it additive-only. The remaining shot at an
  adoptable positive headline number is **Lever B** (lesion-detection caries path).
- **Bug caught and fixed (worth recording):** the first primary-eval pass used a bash-4
  `declare -A` associative array in a script run under macOS bash 3.2 -> all 3 arms silently ran
  with `arm4c_best.pt`, giving an identical (and real, but mislabelled) 0.9284 for all three. Re-
  run with explicit per-arm invocations; Control A then reproduced 0.5844 exactly, confirming the
  env and script are sound. The three `stage2_rows_head.json` now have distinct sha256.
- **Source:** `models/15_detector_multicorpus_leverA/run_summary.txt` (+ `{controlB,arm3c,arm4c}
  _best.pt` sha256 there; 51 MB each, gitignored, local disk only, Drive TBD), `*_results.csv`,
  `leverA_train.log`; `outputs/lever_A_multicorpus_detector_v2/{controlA,arm3c,arm4c}/stage2_*.json`,
  `{arm3c,arm4c}/primary_bootstrap.json`; `scripts/yolo/{build_multicorpus_detector_v2_dataset,
  train_multicorpus_detector_v2}.py`; `scripts/eval/score_leverA_arm.py`;
  `outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md`.
- **Follow-ups:** (1) finish Guard 1, add to `model_metrics.md` + `PAPER_MATERIAL.md` §8.10.
  (2) Fold the replication + the in/out-domain tradeoff curve into `PAPER_MATERIAL.md` §8.10 and
  the manuscript's Stage-2 section. (3) `models/15/*.pt` not on Drive (same gap as `models/11`,
  `models/13`, `models/14`). (4) **Lever B** next.

---

## 2026-09-03b — Lever A Guard 1 (external caries agreement) — PASSES; verdict stays ABLATION but the tradeoff is now bidirectional and quantified

Completes the Lever A milestone (`RESULTS_LOG` 2026-09-03). Guard 1 = pooled caries lesion
agreement, **Ningxia x4 hospitals (1,013 lesions) + CariesXrays random-1500 (3,421 lesions)**,
**frozen** caries gate v3.0, each arm's detector swapped in, everything else identical. Paired
cluster bootstrap over the 1,837 images (10k, seed 42). Control A here reproduces the published
§8.25 CariesXrays 0.309 and §8.12a Ningxia-pooled 0.407 exactly.

| cohort | Control A | Arm 3C | Arm 4C |
|---|---|---|---|
| Ningxia pooled (1,013 lesions) | 0.407 | **0.600** (+19.3 pp) | 0.548 (+14.1 pp) |
| — test1 / test2 / test3 / test4 | .294 / .519 / .401 / .392 | **.519 / .702 / .512 / .624** | .475 / .636 / .457 / .586 |
| CariesXrays-1500 (3,421 lesions) | 0.309 | **0.370** (+6.1 pp) | 0.367 (+5.8 pp) |
| **POOLED (4,434 lesions)** | **0.331** | **0.422**  Δ **+9.11 pp [+7.49, +10.81]** | 0.408  Δ **+7.69 pp [+6.08, +9.31]** |

**GUARD 1 PASSES** for both arms — pre-reg bar was "does not regress" (Δ lower bound >= -2 pp);
both arms are a clear *improvement*, lower bound +7.5 / +6.1 pp. Arm 3C is up on **all four**
Ningxia splits and on CariesXrays.

**Full pre-registered verdict** (`scripts/eval/score_leverA_arm.py`,
`outputs/lever_A_multicorpus_detector_v2/{arm3c,arm4c}/leverA_verdict.json`):

| | PRIMARY (DENTEX e2e) | GUARD 1 (external caries) | GUARD 2 (Tufts test mAP) | verdict |
|---|---|---|---|---|
| **Arm 3C** | +34.40 pp [+30.29, +38.54] ✅ | +9.11 pp [+7.49, +10.81] ✅ | 0.585 vs 0.684 floor ❌ | **ABLATION** |
| **Arm 4C** | +34.40 pp [+30.12, +38.71] ✅ | +7.69 pp [+6.08, +9.31] ✅ | 0.552 ❌ | **ABLATION** |

**Key insight — this is a much stronger result for the paper than Lever 1's flat "domain
dilution".** The multi-corpus detector is:
- **worse on Tufts test** box mAP by ~14-17 pp (Guard 2, the corpus it is benchmarked against);
- **better on DENTEX** end-to-end FDI by +34 pp (in-domain);
- **better on Ningxia** caries agreement by +19 pp and **CariesXrays** by +6 pp (external — the
  cohorts the paper's validation story actually rests on).

So the in-domain/cross-domain tradeoff is **real, bidirectional and measured**: for a pipeline
whose stated purpose is screening arbitrary panoramic X-rays and whose contribution is 6-cohort
external validation, the multi-corpus detector is better on 5 of 6 cohorts and worse only on
Tufts. The Guard-2 criterion (pre-registered) protects the reproducibility of past Tufts
numbers, not the deployment goal — a limitation of our own adoption rule that belongs in the
discussion, **not** grounds to move the bar. Pipeline default detector stays `models/11`; the
paper reports the multi-corpus detector's 6-cohort table as "what a deployment-optimised choice
looks like", clearly labelled.

- **Source:** `outputs/lever_A_multicorpus_detector_v2/{arm3c,arm4c}/{leverA_verdict,primary_bootstrap}.json`,
  `outputs/ningxia_leverA_{controlA,arm3c,arm4c}/`, `outputs/cariesxrays_external_leverA_{controlA,arm3c,arm4c}/`,
  `scripts/eval/score_leverA_arm.py`. All local CPU/MPS eval, no GPU. (Note: `ningxia_external.py`
  `--tag` does not namespace `--out`; the first Guard-1 pass overwrote 2 of 3 Ningxia dumps and
  was re-run with explicit `--out`.)
- **Follow-ups:** (1) `PAPER_MATERIAL.md` §8.10 + §8.12a updated with the tradeoff. (2) A possible
  cheap third data point: a *Tufts-weighted* (not balanced) multi-corpus arm to trace the frontier
  (Tufts share 33 % -> 52 % -> ~70 %); not pre-registered, below Lever B. (3) **Lever B next.**


## 2026-09-03c — Lever A Guard-2 diagnosis: the Tufts drop is capacity dilution, not a box bug (no new model)

Follow-up analysis after the user asked why Lever A's Tufts test box mAP falls (0.724 → 0.585)
while every other cohort improves. Full write-up + a 5-voice council + a phased plan:
`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md`. **Lever A stays ABLATION —
this did not re-open the pre-registration or move any bar.**

- **What was done:** Three local CPU diagnostics on the existing `models/15` weights +
  `data/detector_multicorpus_v2/` (scripts in `models/15_detector_multicorpus_leverA/repro/diagnostics/`):
  (1) GT box statistics per corpus; (2) predicted box size on the 150 Tufts frozen-test images,
  GT vs Control B vs Arm 3C vs Arm 4C; (3) greedy GT-match on Tufts test — TP / FN / FP,
  matched-pair IoU, pred/GT width+height ratio.
- **Metrics (Tufts frozen TEST, 150 img / 3,924 box; conf 0.25, local greedy match):**

  | | Control B (Tufts-only) | Arm 3C (Tufts+DENTEX+Kaggle) |
  |---|---|---|
  | matched teeth (TP) | 2,879 | 2,497 |
  | missed teeth (FN) | 1,045 | **1,427  (+37 %)** |
  | spurious boxes (FP) | 1,058 | **1,506  (+42 %)** |
  | precision / recall | 0.731 / 0.734 | 0.624 / 0.636 |
  | matched-pair IoU, median | 0.624 | **0.643 (unchanged/better)** |
  | pred/GT height ratio, median | 1.36 | 1.17 |

  Predicted median box area (% of image): Tufts GT 0.621, Control B **0.933**, Arm 3C **0.770**,
  Arm 4C 0.667 — i.e. adding corpora moves Arm predictions *closer* to Tufts GT, not further.
- **Key decision or insight:**
  - **Hypothesis "blended box convention → boxes mis-fit Tufts" is REFUTED.** GT stats did show
    DENTEX boxes ~1.5× Tufts area, but the trained models show Arm 3C boxes are better-shaped and
    better-localised than Control B's. Localisation is not where Lever A loses.
  - **Confirmed cause = capacity / domain dilution** (the pre-registered "risk #2"): with Tufts at
    33 % of the mix the detector misses more Tufts teeth and fires with worse confidence —
    FN +37 %, FP +42 %, monotonic in Tufts training share: 100 % → 0.724, 52 % (Lever 1) → 0.647,
    33 % (Lever A) → 0.585.
  - **New reference points:** the *deployed* Stage-1 model is segmentation and scores **0.810** on
    this exact split (`model_metrics.md` §"Stage 1 · Tufts"); every detection model here — even
    Tufts-only Control B — scores ≤ 0.724. seg→detect costs ~9 pp *before* any corpus is added;
    DENTEX/Kaggle/UFBA have no masks so the levers are forced to `detect`. All models predict
    Tufts boxes ~20–36 % taller than GT → the Tufts box labels are crown-biased and cap the
    achievable box mAP for everyone.
  - **Minor:** Tufts boxes bypass the builder's `MIN_PX=2` degenerate-box filter (applied to the
    rotated corpora only) — 4 / 3,924 un-matchable boxes in the Guard-2 GT (~0.1 pp FN tax on all
    models equally); 21 in Tufts train.
  - **Recommendation (council): no more GPU on the detector.** The diagnosis is a clean quantified
    ablation result → fold into `PAPER_MATERIAL.md` §8.10. A real "another way" exists (multi-corpus
    *segmentation* with pseudo-masks, or multi-corpus pretrain → Tufts fine-tune) but both are
    Lever-D-scale and sit behind Lever B and behind Track A. Any retry = a new pre-registration
    (Lever A2), deployed detector stays `models/11` until it passes cleanly.
- **Source:** `outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md`;
  `models/15_detector_multicorpus_leverA/repro/diagnostics/{box_conv,pred_box_size,iou_diag}.py`;
  Guard-2 P/R/mAP from `models/15_detector_multicorpus_leverA/leverA_train.log`.
- **Follow-ups:** (1) Phase 0 (no GPU): GT-box overlays, FN/FP at conf {0.10, 0.25, 0.40} incl.
  Arm 4C, then write §8.10 + §8 Known Limitations. (2) **Lever B** is still the next lever.
  (3) Lever A2 only if Lever B yields no adoptable headline AND ≥ 2 weeks schedule slack AND a
  decision that an adoptable multi-corpus detector is worth a full downstream re-measure — probe
  with pretrain→fine-tune (~₹400) before segmentation (~₹1,000).


## 2026-09-04 — Phase 0: the Lever A Guard-2 failure is a confidence-calibration collapse on the minority domain (no new model)

Completes the Lever A Guard-2 post-mortem (`RESULTS_LOG` 2026-09-03c). No GPU, no training —
diagnostics on the existing `models/15` weights + `data/detector_multicorpus_v2/`. Lever A stays
ABLATION; nothing re-opened.

- **What was done:** two local CPU diagnostics
  (`models/15_detector_multicorpus_leverA/repro/diagnostics/`):
  (1) `iou_diag_sweep.py` — greedy GT-match on the 150 Tufts frozen-test images, all 3 arms ×
  confidence {0.10, 0.25, 0.40}; (2) `gt_overlay.py` — GT-box overlays, 12 Tufts + 12 DENTEX
  test images.
- **Metrics — Tufts frozen TEST (3,924 GT teeth), greedy IoU≥0.5 match:**

  | arm (Tufts train share) | conf | FN | FP | recall | matched-pair IoU (median) |
  |---|---|---|---|---|---|
  | Control B (100 %) | 0.10 / 0.25 / 0.40 | 897 / 1045 / 1327 | 1531 / 1058 / 783 | 0.771 / 0.734 / 0.662 | 0.623 / 0.624 / 0.625 |
  | Arm 3C (33 %) | 0.10 / 0.25 / 0.40 | 995 / 1427 / 2120 | 2694 / 1506 / 967 | 0.746 / 0.636 / 0.460 | 0.645 / 0.643 / 0.643 |
  | Arm 4C (25 %) | 0.10 / 0.25 / 0.40 | 781 / 1457 / 2546 | 3377 / 1586 / 668 | 0.801 / 0.629 / 0.351 | 0.683 / 0.676 / 0.674 |

- **Key insight — the mechanism, sharper than "domain dilution":**
  - **Matched-pair IoU is flat across the entire sweep** (~0.62–0.68, multi-corpus arms if
    anything better). Localisation is not the loss — confirmed across 3 thresholds, not the
    one (0.25) the 03c diagnostic used.
  - **At low confidence the multi-corpus arms detect Tufts teeth as well as the Tufts-only
    control or better** (Arm 4C recall 0.80 vs 0.77) — but with a false-positive flood.
  - **What breaks is confidence calibration on the minority domain:** the score no longer
    separates real teeth from spurious boxes, so raising the threshold to clear the FP flood
    also kills the true positives — recall drop from conf 0.10→0.40 is −0.11 (Control B),
    **−0.29 (Arm 3C), −0.45 (Arm 4C)**. mAP@0.5 is a ranking metric ⇒ it degrades hardest:
    **0.724 → 0.585 → 0.552, monotonic in Tufts training share** (Lever 1 at 52 % = 0.647).
    The FN/FP split at a *fixed* threshold is threshold-dependent (FP-flood low, FN-collapse
    high); the mAP number and the calibration collapse are what is monotonic.
  - **A structural ceiling underneath:** every detection model here (incl. Tufts-only Control B)
    scores ≤ 0.724, while the deployed *segmentation* Stage-1 scores **0.810** on the identical
    split. seg→detect (forced — DENTEX/Kaggle/UFBA have no masks) costs ~9 pp of box mAP before
    any extra corpus; "0.585 vs 0.724" is the honest penalty, not "0.585 vs 0.810".
  - **GT-overlay (0.2):** visually confirms `box_conv.py` — DENTEX GT boxes are larger and
    heavily overlapping, extending into alveolar bone (`dentex_train_0` 1.19 % img median box
    area vs Tufts `1013` 0.64 %). Every model also draws Tufts boxes 17–36 % wider
    mesial-distally than GT — the Tufts `teeth_bbox.json` boxes are drawn tight in the narrow
    axis, which caps matched-pair IoU near 0.62 for anyone (→ `PAPER_MATERIAL.md` §8.9).
- **Source:** `models/15_detector_multicorpus_leverA/repro/diagnostics/{iou_diag_sweep,gt_overlay}.py`;
  two GT-overlay panels in `docs/results/figures/lever_a_guard2/`; full sweep output in the session-memory. Folded
  into `PAPER_MATERIAL.md` §8.16 (mechanism + box-vs-mask ceiling) and §8.9 (Tufts box-label
  findings). `outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` §1.4b, §1.5, §3.
- **Follow-ups:** Phase 0 is complete. Lever A2 (a retry) stays gated behind Lever B
  (`TUFTS_GUARD2_DIAGNOSIS.md` §3 Phase 1). **Lever B is the next lever** (the friend, on Windows).


## 2026-09-04b — Lever A2: a Tufts head fine-tune does NOT recover the benchmark — ABLATION

Executes the Lever A2 pre-registration (`outputs/lever_A2_detector_finetune/PRE_REGISTRATION.md`,
FROZEN `a7e4902`). Tests the fix implied by the Phase-0 diagnosis (`RESULTS_LOG` 2026-09-04):
if Lever A's Guard-2 failure is a *head*-calibration collapse, then freezing the multi-corpus
backbone and fine-tuning the head on Tufts should recover it. **It does not.** Lever A2 stays
ABLATION; pipeline default detector unchanged.

- **What was done:** loaded `models/15_detector_multicorpus_leverA/arm3c_best.pt` (the frozen
  Lever A 3-corpus checkpoint), **froze the backbone** (`freeze=11` → YOLOv11l layers 0–10,
  50.7 % of params; verified locally), fine-tuned the neck + Detect head on **Tufts-only**
  (`train_tufts.txt`, 700 images) — 40 epochs / patience 12 / warmup 1 / canonical LR 1e-3,
  every other knob byte-identical to `train_multicorpus_detector_v2.py`. JarvisLabs RTX PRO 6000
  (instance 496782, IN1, env identical to Lever A), ~10 min training, **~₹36**. Instance
  destroyed. EarlyStopping at epoch 18, best = epoch 6.
- **Dataset:** a Tufts-only subset of `data/detector_multicorpus_v2/` (280 MB tar, box counts
  val 3,794 / test 3,924 reproduced, on-box `GATE: GO`). A2 touches Tufts only.
- **Metrics — the pre-registered rule** (`scripts/eval/score_leverA_arm.py --label a2`; reuses
  Lever A's Control A / Control B numbers; paired cluster bootstrap 10k seed 42):

  | criterion | comparator | A2 | bar | result |
  |---|---|---|---|---|
  | **PRIMARY** — DENTEX FDI e2e (164 leak-free) | Control A 0.5844 | **0.8771**, Δ **+29.27 pp [+24.95, +33.59]** | lower bound ≥ +5 pp | ✅ **PASS** |
  | **GUARD 1** — pooled ext caries agreement (Ningxia ×4 + CariesXrays-1500, 4,434 lesions) | Control A 0.3313 | **0.4168**, Δ **+8.55 pp [+6.88, +10.24]** | lower bound ≥ −2 pp | ✅ **PASS** |
  | **GUARD 2** — Tufts frozen test box mAP@0.5 | Control B 0.7243 | **0.5929** | ≥ 0.6843 | ❌ **FAIL** |

  Per-cohort: Ningxia pooled 0.407 (Ctrl A) → 0.600 (arm3c) → **0.570** (A2); CariesXrays-1500
  0.309 → 0.370 → **0.372**; DENTEX e2e 0.584 → 0.928 (arm3c) → **0.877** (A2).
- **Key insight:** the Tufts head/neck fine-tune moved Tufts **test** box mAP by **+0.8 pp**
  (0.585 → 0.593) — essentially nothing — even though Tufts **val** mAP recovered (0.54 → 0.62).
  The operating-point P/R is unchanged from arm3c (0.593/0.638 vs 0.594/0.631). **The Phase-0
  calibration hypothesis was necessary but not sufficient:** re-specialising the head on Tufts
  does not fix Tufts box mAP, and the result gets nowhere near the from-scratch Tufts detector
  (0.593 vs Control B 0.724). The frozen 3-corpus backbone features cannot be recombined into a
  Control-B-quality Tufts detector by the neck + head alone — the ceiling is **deeper than the
  detection head**. This is pre-reg §5 row 3: "head fine-tuning is insufficient; the box-mAP
  ceiling is the box-vs-mask supervision gap (§8.9)."
- **What A2 *did* show:** a frozen-backbone fine-tune keeps most of the multi-corpus gains
  (DENTEX +29 vs +34 pp, external +8.6 vs +9.1 pp) — the +34/+9 pp gains live in the backbone,
  as Phase 0 argued. So the tradeoff is not "forgetting" — it is that a from-scratch Tufts
  detector's box quality is simply not reachable from these features.
- **VERDICT (pre-registered, bar NOT moved): ABLATION / not adopt-worthy.** 2 of 3 pass.
  Pipeline default detector stays `models/11_yolo_seg_tufts_r1`. Same disposition as Lever 1,
  Lever A, Stage-2 head v3, caries gate v4.
- **The Lever 1 → A → Phase 0 → A2 arc is now closed** as a methodological result: a single-class
  multi-corpus tooth detector cannot serve both the Tufts benchmark and the external cohorts, the
  failure mechanism is a calibration collapse (not localisation), and it is not fixable by head
  fine-tuning. The only untried lever is multi-corpus **segmentation** — pre-reg-scoped as
  **post-submission**, not a next step under the ISBI timeline.
- **Source:** `models/17_detector_leverA2_finetune/run_summary.txt` (+ `a2_best.pt` sha256
  `48e23e84797712edd63322bdd7407f3e57890a00f9e494cc862f1a3250bba300`, 49 MB, gitignored),
  `a2_results.csv`, `a2_train.log`; `outputs/lever_A2_detector_finetune/a2/{stage2_*,ningxia_caries,cariesxrays_caries,leverA2_verdict}.json`;
  `outputs/lever_A2_detector_finetune/{PRE_REGISTRATION,STATUS}.md`;
  `scripts/yolo/train_a2_finetune.py`; `scripts/eval/score_leverA_arm.py`.
- **Follow-ups:** (1) fold into `PAPER_MATERIAL.md` §8.16 (done). (2) `transfer.md` §4
  pending-decision row "is an adoptable multi-corpus detector worth chasing?" — **resolved: no,
  under this timeline**; segmentation is post-submission. (3) `models/16/a2_best.pt` local-only
  (same Drive gap as models/11–15). (4) **Lever B** (the friend, Windows) is now the only
  active score lever. (5) `transfer.md` GPU balance was ₹1,732, actually ₹1,184.84 before A2 —
  a ~₹547 gap to explain (not this session's spend).


## 2026-09-04c — GT-scale probe: the Tufts Guard-2 gap is NOT a box-convention problem (no new model)

Follow-up to A2 (`RESULTS_LOG` 2026-09-04b), answering "is the Tufts GT ~1.5× too tight, and
would fixing it recover the multi-corpus detector?". `models/15_detector_multicorpus_leverA/repro/diagnostics/gt_scale_probe.py`
— Control B / arm3c / A2 run on the 150 Tufts test images at conf 0.001, box mAP vs the GT with
the GT boxes scaled about their centre by s ∈ {1.0, 1.15, 1.3, 1.5, 1.7}, at IoU-match {0.3, 0.5}.

- **Metrics** (box mAP; s = GT scale factor):

  | model | @IoU 0.5, s=1.0 / 1.15 / 1.5 | @IoU 0.3, s=1.0 |
  |---|---|---|
  | Control B (Tufts-only) | 0.704 / **0.783** / 0.570 | **0.904** |
  | arm3c (Lever A) | 0.538 / 0.577 / 0.206 | 0.834 |
  | A2 (Tufts head FT) | 0.566 / 0.609 / 0.225 | **0.842** |

- **Findings:**
  1. **The "1.5×" is a between-corpus comparison** (DENTEX GT boxes are 1.49× Tufts GT area,
     `box_conv.py`), **not a factor applied to Tufts.** The offset between detector predictions
     and the recorded Tufts GT is only **~1.15×** — mAP@0.5 peaks at s = 1.15 for all three
     models; s = 1.5 is catastrophic. The recorded Tufts boxes are ~15 % tight, not 1.5× tight.
  2. **Most of the Guard-2 "failure" is the IoU-0.5 threshold.** At **IoU-match 0.3** — what the
     pipeline's FDI head actually uses — A2 = **0.842**, Control B = 0.904, gap ~6 pts (vs ~14
     at IoU 0.5). On the metric the pipeline needs, arm3c/A2 retain most of the Tufts performance.
  3. **The residual deficit is real and box-independent.** Control B beats arm3c/A2 by a roughly
     constant margin at *every* IoU threshold and *every* GT scale (~6 pts @0.3, ~13–17 @0.5).
     Rescaling the GT does not close it — it is the calibration / frozen-feature gap from Phase 0
     and A2.
- **Key insight:** a box-convention change is **not** a lever for the multi-corpus detector.
  What it *does* show, and this is useful for the paper: the Lever A / A2 Guard-2 "failure" is
  **substantially a strict-threshold artefact** — at the IoU-0.3 matching the pipeline uses, the
  multi-corpus detector holds **0.84 on Tufts** and 0.93 on DENTEX. The pre-registered
  mAP@0.5 verdict stands (bar not moved); this is post-hoc context showing the deployment impact
  is smaller than the headline number.
- **Source:** `models/15_detector_multicorpus_leverA/repro/diagnostics/gt_scale_probe.py`;
  `outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` §1.4c.
- **Follow-ups:** fold the IoU-0.3 reframing into `PAPER_MATERIAL.md` §8.16 (pending user call
  on whether to also re-pre-register a pipeline-relevant Tufts guard). Lever B unaffected.


## 2026-09-04d — Tufts end-to-end FDI: the Stage-2 number the paper never had

Built `scripts/eval/validate_fdi_assignment_tufts.py` — the Tufts twin of the DENTEX
`validate_fdi_assignment.py`. Same detector → `models/10` head → Hungarian one-to-one → greedy
IoU-0.30 + centroid matcher, scored against the **complete** mirror-corrected Tufts per-tooth
numbering (`teeth_bbox.json`, `tufts_title_to_fdi`). 149 frozen-test images (150 − `590`, a
train duplicate excluded by MD5), **3,760 permanent GT teeth** — so this is a real recall *and*
a real end-to-end accuracy, unlike DENTEX which only annotates ~6 pathological teeth/image.

- **Metrics** (conf 0.25, NMS IoU 0.50, one-to-one, `models/10` head):

  | detector | recall | FDI exact (of detected) | **end-to-end FDI** | quadrant (of det) | off-by-one |
  |---|---|---|---|---|---|
  | **`models/11` deployed seg** (Tufts-trained) | 82.4 % | 78.6 % | **64.8 %** | 96.3 % | 15.3 % |
  | `models/06` old bbox (superseded) | 91.2 % | 78.4 % | **71.5 %** | 96.5 % | 14.8 % |
  | `models/15` arm3c — Lever A multi-corpus | 89.3 % | 71.1 % | **63.5 %** | 94.6 % | 19.4 % |
  | `models/16` A2 — Tufts head fine-tune | 89.9 % | 70.8 % | 63.7 % | 94.2 % | 19.8 % |

  0 duplicate FDI codes (Hungarian). Mirror verified on 6 viz overlays (Q1 upper-viewer-left,
  Q2 upper-viewer-right). `models/11` at conf 0.10 is *worse* end-to-end (61.3 %, recall 95 %
  but det/img 35.7 — spurious boxes flood the assignment), so conf 0.25 is near-optimal.

- **Key insights:**
  1. **The pipeline's Tufts Stage-2 number is 64.8 % end-to-end / 78.6 % of detected** — vs
     DENTEX 58.3 % / 82.6 %. Tufts is higher end-to-end (in-domain detector) on a *harder*
     test (all ~26 teeth/image, including the ambiguous posterior ones, not just ~6 pathological).
  2. **The Lever A / A2 Guard-2 box-mAP "failure" does NOT translate to an end-to-end Tufts
     cost.** `models/11` 64.8 % → arm3c 63.5 % → A2 63.7 % — a ~1-point drop, from a −14-point
     box mAP@0.5 drop (0.724 → 0.585). This is the §8.16 IoU-0.3 reframing confirmed at the
     actual pipeline output, not a threshold analysis. The multi-corpus detector finds *more*
     Tufts teeth (recall 82 → 89 %) and numbers them slightly worse (of-detected 79 → 71 %),
     netting flat.
  3. **The old bbox detector beats the deployed seg detector on Tufts end-to-end (71.5 % vs
     64.8 %)** — driven by recall (91 % vs 82 % at conf 0.25). The 27 Aug bbox→seg swap improved
     DENTEX cross-domain (+12 pp, §8.10) but costs Tufts in-domain end-to-end (−6.7 pp): the seg
     detector's higher box mAP does not mean higher pipeline accuracy on its home domain,
     because Stage 2 is sensitive to the recall/precision *operating point*, not the PR-curve
     area. A real detector–Stage-2 coupling nuance — not a reason to revert (`models/11` was
     adopted on box mAP + the DENTEX gain, a dated human decision).
- **Source:** `scripts/eval/validate_fdi_assignment_tufts.py`;
  `outputs/stage2_tufts{,_arm3c,_a2,_bbox06,_conf010}/stage2_*_head.json`. Reuses
  `validate_fdi_assignment.py` (matcher, viz), `src.utils.fdi_converter.tufts_title_to_fdi`
  (the mirror), `src.orientation.detect_upright`, `src.fdi_head_inference`.
- **Follow-ups:** (1) `PAPER_MATERIAL.md` §8.10 + `model_metrics.md` Stage-2 — add the Tufts
  end-to-end row + insights 2 & 3. (2) Insight 3 (bbox vs seg on Tufts e2e) is paper-worthy —
  fold into §8.16's detector–Stage-2 discussion. (3) No GPU used.


## 2026-09-04e — Tufts Stage-2 failure taxonomy: same error shape as DENTEX, opposite detector-swap effect

Extends `RESULTS_LOG` 2026-09-04d. Ran the existing `scripts/eval/stage2_failure_taxonomy.py`
(gave it `--label` + `--fig-name` args — DENTEX defaults unchanged, regression verified) on the
Tufts end-to-end rows: 3,760 permanent teeth, `models/11` main vs `models/06` (bbox) control.
No inference re-run.

- **Metrics** (fraction of 3,760 GT teeth):

  | outcome | DENTEX | **Tufts** |
  |---|---|---|
  | correct | 58.3 % | **64.8 %** |
  | not_detected | 29.4 % | **18.2 %** |
  | off_by_one | 9.5 % | 12.6 % |
  | same_quadrant_far | 1.1 % | 2.0 % |
  | mirror_lr | 0.9 % | 1.3 % |
  | wrong_arch | 0.6 % | 0.5 % |
  | other | 0.2 % | 0.6 % |

  Of detected teeth: 20.7 % wrong code (DENTEX 17.4 %). **74 % of Tufts numbering errors are
  off-by-one; 3.2 % are category errors** (wrong_arch + mirror_lr). 43 of 49 `mirror_lr` errors
  are central incisors (midline) — not a systematic mirror-correction fault. Molars easiest
  (9-11 % wrong), premolars/incisors hardest (22-31 %) — same rank as DENTEX. Off-by-one leans
  distal (285:188) where DENTEX leaned mesial (53:36).
- **Key insight — the detector swap's effect on Tufts is the reverse of DENTEX.** bbox->seg
  control: `correct` 71.5 % -> 64.8 %, and the whole delta is `not_detected` 9.6 % -> 18.2 %;
  every error bucket is unchanged to <1 pt. On DENTEX the same swap *improved* the error shape
  (`wrong_arch` -75 %, of-detected +13.9 pp). **The seg detector's box-quality benefit is
  cross-domain** — it suppressed the spurious boxes that perturb the Hungarian on DENTEX; on
  Tufts (in-domain) the bbox detector was already clean, so the swap only cost recall. A clean
  illustration that box mAP does not capture detector-Stage-2 coupling.
- **Source:** `scripts/eval/stage2_failure_taxonomy.py`
  (`--rows outputs/stage2_tufts/... --control outputs/stage2_tufts_bbox06/...`),
  `outputs/stage2_taxonomy_tufts/stage2_failure_taxonomy.json`,
  `docs/results/figures/paper/stage2_failure_taxonomy_tufts.png`. Folded into `PAPER_MATERIAL.md`
  §8.16. No GPU.
---

## 2026-09-04f — Lever B, B-single arm: decisive in-domain win, decisive out-of-domain collapse

- **What was done:** Pre-registration frozen (4 defects fixed pre-freeze: the CariesXrays "1,500
  seed-43 draw" was arithmetically impossible — max disjoint pool is 1,200, the existing val
  split; confidence-tuning clause removed as circular once that val set became the eval cohort;
  B-pooled's image count corrected ~5,500 → 9,600/epoch against its own balancing rule; the
  lesion-prediction→tooth mapping was specified, argmax-containment). Wired `--decision
  lesion-detector` into `lesion_localization.py`, `ningxia_external.py`, `cariesxrays_external.py`
  (shared mapping in `ningxia_external.lesion_preds_to_tooth_idx`; a plain, unrotated
  `run_lesion_detector()` call — reusing `detect_upright()` would have silently rotated every
  image 90°, since that function is hardcoded to the tooth detector's Tufts-trained convention,
  not a generic rotation-optional helper). Built `data/dentex_caries_det/` (DENTEX
  `quadrant-enumeration-disease` → YOLO caries boxes, `scripts/dentex/build_dentex_caries_boxes.py`,
  new) and `data/lever_b_pooled/` (balanced pool, `scripts/yolo/build_lever_b_pooled_dataset.py`,
  new). Ran **B-single** (Lever 2's frozen `models/14_cariesxrays_lever2/weights/best.pt`, zero
  GPU, re-used as-is) through the frozen eval on DENTEX-164 and CariesXrays-val-1200; B-pooled
  training (GPU) started separately, not yet complete (see Follow-ups).
- **Dataset / config:** DENTEX `quadrant-enumeration-disease` — 705 images, 650 with ≥1
  caries/deep_caries box, 2,767 boxes (`category_id_3 ∈ CARIES_CLASSES={1,3}`, reused from
  `build_dentex_crops.py`), 0 leakage into the 164-image eval cohort (1 candidate MD5 duplicate
  found and it was already excluded there for an unrelated reason — verified live, not assumed).
  B-pooled dataset: CariesXrays-train 4,800 + DENTEX-caries replicated 650→4,800 (Lever A's
  balancing recipe, `list * ceil(big/len) sliced to big`, verified 0 cross-corpus MD5 overlap) =
  9,600 lines/epoch. Lesion-detector confidence frozen at 0.25 (ultralytics default, per the
  amended pre-reg). Paired cluster bootstrap over images, 10,000 resamples, seed 42
  (`scripts/eval/lever_b_bootstrap.py`, new — reuses `bootstrap_ci.py`'s primitives).
- **Metrics — lesion-localisation agreement, frozen eval, B-single (`models/14`) vs. gate v3.0 vs.
  the image-blind molar constant:**

  | cohort (n images) | gate v3.0 | constant-molars | **lesion-detector (B-single)** | Δ vs constant | Δ vs gate |
  |---|---|---|---|---|---|
  | DENTEX (148 w/ lesions of 164) | 44.3% [39.2,49.3] | 48.9% [44.1,53.5] | **8.6% [5.5,11.9]** | −40.3pp [−46.1,−34.6] | −35.7pp [−41.6,−29.9] |
  | CariesXrays-val (1,200) | 31.7% [29.6,33.7] | 56.2% [54.0,58.5] | **69.4% [67.4,71.3]** | +13.2pp [+11.1,+15.2] | +37.7pp [+35.4,+40.0] |

  Both deltas have CIs excluding zero on both cohorts, in opposite directions. Predicted-positive
  rate (mean teeth flagged/image): B-single 0.73 (DENTEX) / 1.90 (CariesXrays), well below every
  comparator (gate 5.10/3.98, constant 5.80/6.44) — CariesXrays' win is not a volume effect
  (rate ratio 0.30–0.48x, both under the pre-registered 1.5x cap).
- **Key decision or insight:** B-single is the cleanest confirmation yet of this project's central
  domain-shift thesis, in a NEW form: **a model trained on one caries corpus does not merely
  degrade on another — it can invert which comparator wins.** On CariesXrays (its own training
  domain) the lesion detector beats both the base-rate-dominated gate and the constant by a wide,
  statistically unambiguous margin, while flagging far fewer teeth than either — exactly the
  "not base-rate dominated" result the lever was pre-registered to test for. On DENTEX it
  collapses to near-silence (0.73 flagged teeth/image vs. the gate's 5.1), the pre-registered
  "wins in-domain, fails to transfer" outcome (§6 of the pre-reg), which strengthens rather than
  undermines the domain-shift thesis. **Sec 6 verdict for B-single alone: 1 of 2 scored cohorts
  passes (CariesXrays; DENTEX fails both comparator conditions). This is not the lever's final
  verdict** — Sec 6 is scored on "the better of B-single/B-pooled," and B-pooled exists
  specifically to close the DENTEX gap by adding DENTEX-domain training data.
- **Source:** `outputs/lever_b_eval/{dentex_pipeline,dentex_constant,dentex_lesion_b_single}/
  lesion_localization.json`; `outputs/cariesxrays_external_lever_b_b_single/
  cariesxrays_external_{pipeline,constant-molars,lesion-detector}.json`; `outputs/lever_b_eval/
  acceptance_rule.json`; `outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md` (frozen, commit
  `ef3f453`); `data/dentex_caries_det/meta.json`, `data/lever_b_pooled/` gate output (both PASS).
- **Follow-ups:** (1) **B-pooled training in progress** on a rented JarvisLabs RTX-PRO6000
  (instance 496516, IN1, ₹179.01/hr — A100 was unavailable at rental time) — a background monitor
  (`monitor_lever_b.sh`) downloads the checkpoint and destroys the instance on verified success,
  or stops and flags for a human look on any crash/mismatch, never destroying on ambiguous state.
  (2) Ningxia not yet run this lever (not on this machine) — the pre-reg's 2-of-available-cohorts
  fallback applies for now; back-fill when available. (3) Once B-pooled lands: re-run
  `lever_b_bootstrap.py --arm-tag B-pooled`, apply Sec 6 to the better arm, write the real
  adoption verdict, update `model_metrics.md` + `PAPER_MATERIAL.md` if adopted, full downstream
  re-run per Sec 6's outcome table. (4) One real bug caught and fixed before it could cost GPU
  time: ultralytics' `train.txt` file-list resolution only rewrites a line starting with `./`
  (verified against `ultralytics/data/base.py get_img_files` directly) — a bare relative line
  resolves against the training process's cwd, not `data.yaml`'s `path:`. Fixed in
  `train_lever_b_pooled_detector.py` by rewriting the list to absolute paths at train time.

---

## 2026-09-04g — Lever B, B-pooled arm: recovers DENTEX transfer, preserves the CariesXrays win

- **What was done:** Trained **B-pooled** — YOLOv11l `detect`, the per-corpus-balanced pool
  (CariesXrays 4,800 train + DENTEX-caries 650 replicated to 4,800 = 9,600 images/epoch, seed 42),
  120 epochs / patience 25, batch 16 (matched to B-single's own realised batch after its OOM
  fallback, not the nominal 32 — see 2026-09-02b). Rented a JarvisLabs **RTX-PRO6000** (IN1,
  ₹179.01/hr) — **A100 (both 40GB and 80GB) was unavailable at rental time**, confirmed via `jl
  gpus` live availability, not assumed. Ran the same frozen tooth-level eval used for B-single on
  the resulting checkpoint, then the paired cluster bootstrap against both comparators.
- **Dataset / config:** Same pooled dataset as the 2026-09-04f entry. Uploaded as 27×250MB chunks
  with per-chunk retry over a genuinely unstable connection (several resets/timeouts absorbed
  cleanly); reassembled and sha256-verified byte-identical to the local build before extracting.
  One real bug found and fixed before any epoch ran: ultralytics' file-list loader only rewrites a
  `./`-prefixed line; a bare relative `train.txt` line resolves against the training process's
  cwd, not `data.yaml`'s `path:` (verified directly against `ultralytics/data/base.py
  get_img_files`, not guessed) — first launch crashed with "No labels found" before wasting any
  epoch time. Fixed by rewriting the list to absolute paths at train time in
  `train_lever_b_pooled_detector.py`. Training **early-stopped at epoch 54** of 120 (patience 25).
- **Metrics — lesion-localisation agreement, frozen eval, B-pooled vs. B-single vs. gate v3.0 vs.
  the constant (paired cluster bootstrap, 10k resamples, seed 42):**

  | cohort | gate v3.0 | constant-molars | B-single | **B-pooled** | B-pooled vs constant | B-pooled vs gate |
  |---|---|---|---|---|---|---|
  | DENTEX (148 w/ lesions) | 44.3% | 48.9% | 8.6% [5.5,11.9] | **45.5% [40.9,50.1]** | −3.3pp [−8.4,+1.3] INCLUDES 0 | +1.3pp [−3.2,+5.7] INCLUDES 0 |
  | CariesXrays-val (1,200) | 31.7% | 56.2% | 69.4% [67.4,71.3] | **68.4% [66.4,70.4]** | +12.2pp [+10.1,+14.3] excludes 0 | +36.7pp [+34.4,+39.0] excludes 0 |

  CariesXrays COCO AP (secondary, not the acceptance metric): B-pooled 0.379/AP50 0.822/AP75
  0.291 — *below* B-single's own 0.482/0.845/0.500, the expected cost of pooling in coarser,
  different-domain boxes. The metric that matters (tooth-level agreement) barely moved (68.4 vs
  69.4%, well within each other's CI).
- **Key decision or insight:** **B-pooled did exactly what it was built for — it moved DENTEX
  from a decisive, statistically certain loss (B-single: −40.3pp / −35.7pp, both CI excluding
  zero) to a statistical TIE with both comparators (both new deltas include zero), at a real but
  small cost to the CariesXrays win (≈1pp, itself within noise).** This is not one of the four
  outcomes the pre-registration enumerated in its Sec 6 table — those anticipated "wins in-domain,
  fails to transfer" as a discrete failure mode; the actual result is continuous: out-of-domain
  transfer went from clear failure to parity, not to a win. Recorded honestly rather than forced
  into the nearest bin. **Sec 6's literal bar is still not met by either arm** — a tie is not
  "beats" under cond. 1/3, so DENTEX still fails those conditions for both B-single and B-pooled,
  leaving 1 of 2 scored cohorts passing either way. **Ningxia is now the deciding cohort** for a
  real 2-of-3 (or 3-of-3) call, and it is not on this machine (`WINDOWS_SETUP.md` §2 fallback
  applies: evaluated on 2 of 3 available cohorts, Ningxia pending). **B-pooled is the better arm
  to carry forward regardless of the final Sec 6 call** — same CariesXrays strength, no longer a
  liability on DENTEX.
- **Source:** `models/16_lever_b_pooled/lever_b_pooled_yolo11l-2/` (weights, `results.csv`,
  `args.yaml`, plots — full run archive, sha256-verified against the rented box before it was
  destroyed: `029018db…` for `best.pt`); `outputs/lever_b_eval/dentex_lesion_b_pooled/
  lesion_localization.json`; `outputs/cariesxrays_external_lever_b_b_pooled/
  cariesxrays_external_lesion-detector.json`; `outputs/lever_b_eval/acceptance_rule_B-pooled.json`
  (`scripts/eval/lever_b_bootstrap.py`, extended to take `--arm-tag {B-single,B-pooled}`).
  JarvisLabs instance 496516 (RTX-PRO6000, IN1) — **spend ₹546.93** (₹1,731.77 → ₹1,184.84),
  destroyed after a verified download, 0 running/paused.
- **Follow-ups:** (1) **Get Ningxia onto this machine** — the one remaining input for a real Sec 6
  verdict; everything else needed to score it (the eval script's `lesion-detector` decision mode,
  the bootstrap script) already exists and is already wired for a third cohort. (2) One
  operational lesson worth keeping: the training script's `project=` argument was silently
  reinterpreted by ultralytics as relative to its own internal `runs_dir` setting (`runs/detect/`
  prepended) rather than to the given path, and a stale directory from the crashed first attempt
  added a `-2` suffix — the real weights landed at
  `runs/detect/runs_lever_b/lever_b_pooled_yolo11l-2/weights/`, not the plain path the training
  script's own project/name arguments suggested. A monitoring script written to auto-download and
  destroy the instance on completion checked the wrong (assumed) path, correctly found nothing,
  and correctly refused to destroy anything rather than guess — the actual weights were found and
  verified by hand (`find … -name best.pt`) with the instance still safely running. No cost was
  lost to this; recorded so the next script that shells out to `model.train(project=..., ...)`
  checks the real output path rather than trusting the argument it passed. (3) Neither arm is
  adopted; the pipeline's Stage-3 caries path stays gate v3.0 until Sec 6 is actually met.

---

## 2026-09-04h — Lever B: Ningxia scored, Sec 6 MET, B-pooled ADOPTED as Stage 3

*(Labelled `04h`, not `04c`: the friend's parallel Tufts/Lever-A2 session independently used
`2026-09-04` through `04e` for its own entries, and relabelled this session's first two entries
`04f`/`04g` on merge to avoid colliding with them. This entry was written after that merge point,
so it collided with the friend's own `04c` — "GT-scale probe" — a different entry. Relabelled to
the next free letter, `04h`, on integrating both sessions' work back together.)*

- **What was done:** The Ningxia dataset was located on this machine (`D:\nangxia_dataset`,
  already in the exact `segmentation/{category}/{split}/{img,mask}` layout
  `ningxia_external.py` expects — no copy needed, `--root` points at it directly). Ran the same
  frozen eval (pipeline, constant-molars, B-single lesion-detector, B-pooled lesion-detector) on
  the full `dental_caries` category, all 4 hospital splits (337 images, 1,013 lesions — matches
  the pre-registered count exactly). `lever_b_bootstrap.py` extended to fold Ningxia in as the
  third cohort (a third, distinct `per_image` key naming scheme —
  `n_lesions`/`n_covered`/`n_predicted_positive` — normalised alongside DENTEX's and
  CariesXrays'; Ningxia filenames repeat across splits, so the pairing key was made
  `category/split/image`, not `image` alone, to avoid silently collapsing two different
  hospitals' images together). Then **adopted B-pooled as the pipeline's Stage-3 caries path**,
  per the pre-registration's own Sec 6 text ("wire the lesion detector in ... pipeline Stage 3
  updated").
- **Metrics — Ningxia, full `dental_caries` cohort, paired cluster bootstrap (10k resamples):**

  | | gate v3.0 | constant-molars | B-single | **B-pooled** |
  |---|---|---|---|---|
  | Ningxia (337 img, 1,013 lesions) | 40.8% | 39.9% | 24.0% [20.9,27.2] | **50.0% [46.3,53.9]** |
  | vs constant | — | — | −15.9pp, excludes 0 (loss) | **+10.2pp [+6.3,+14.0], excludes 0 (win)** |
  | vs gate | — | — | −16.8pp, excludes 0 (loss) | **+9.3pp [+5.3,+13.3], excludes 0 (win)** |

  B-single loses Ningxia too — same failure-to-transfer pattern as DENTEX, confirming the
  transfer failure is a property of CariesXrays-only training, not of lesion detection itself.
  B-pooled **wins** Ningxia decisively — not a tie like its own DENTEX result.
- **Full Sec 6 table, all three cohorts, B-pooled:**

  | cohort | cond1 (beats constant) | cond2 (rate ≤1.5×) | cond3 (beats gate) | verdict |
  |---|---|---|---|---|
  | DENTEX | False (tie, CI incl. 0) | True | False (tie, CI incl. 0) | fail |
  | CariesXrays | True | True | True | **PASS** |
  | Ningxia | True | True | True | **PASS** |

  **2 of 3 cohorts pass all three conditions. Sec 6 requires ≥2 of 3. Rule MET.** The bar was
  frozen 4 Sep, before any of these numbers existed (`ef3f453`); nothing was moved to make this
  pass.
- **Key decision or insight:** **Adopted B-pooled as Stage 3**, per the pre-registration's own
  outcome table. This is the first time in this project's history that anything has decisively
  beaten the image-blind molar constant that had tied-or-beaten the caries branch on every one
  of six cohorts (`PAPER_MATERIAL.md` §8.22/8.24/8.25) — five prior attempts to fix the gate
  directly (CLAHE, crop expansion, position-balanced sampling, gate v4, threshold tuning) all
  failed with CIs spanning zero. **Adoption is a mechanism change, not a constant swap**: the
  lesion detector is a whole-image DETECTOR, not a per-crop classifier, so Stage 3's actual
  computation changed (`src/classifiers.run_caries_lesion_detector`, new — maps predicted lesion
  boxes to the tooth box each overlaps most via argmax containment, then reuses the existing
  severity classifier on flagged teeth only). The old gate is retained, unchanged and fully
  functional, via `--caries-method gate` — every pre-4-Sep caries number stays reproducible.
  **DENTEX is a tie, not a win, and is reported as such everywhere** — this is not "solved
  everywhere," and the report's own limitations text says so on every run.
- **Implementation:** `lesion_preds_to_tooth_idx` and the raw lesion-detector call moved from
  `scripts/eval/ningxia_external.py` (eval-only) to `src/classifiers.py` (production) — Stage 3
  now owns the primitive it depends on, rather than depending on an eval script; the three eval
  scripts import it back from there. `run_inference.py` gained `DEF_CARIES_LESION_MODEL`,
  `--caries-method {lesion-detector,gate}` (default `lesion-detector`), and
  `--caries-lesion-conf` (frozen 0.25). `load_models()` loads both caries mechanisms
  unconditionally (same pattern as every other stage). The report schema's
  `limitations.caries_gate_precision` key is renamed `caries_method_caveat` (content now
  depends on which method ran; `app.py`'s one reference updated) — the old gate-specific text
  would have been actively misleading under the new default. `gate_confidence` on a
  lesion-detector report is a raw detection score, not a softmax probability, and is flagged
  `gate_confidence_is_detection_not_softmax` so it is never misread as the old field's meaning.
  Regression-checked: the refactor reproduces the pre-refactor smoke-test numbers byte-for-byte,
  **159/159 tests pass**, `verify_invariants.py` all-hold.
- **Source:** `outputs/lever_b_eval/ningxia_{pipeline,constant,lesion_b_single,lesion_b_pooled}/
  ningxia_external.json`; `outputs/lever_b_eval/acceptance_rule_B-pooled.json` (full 3-cohort
  verdict); `scripts/eval/lever_b_bootstrap.py`; `src/classifiers.py`
  (`run_caries_lesion_detector`, `lesion_preds_to_tooth_idx`, `run_lesion_detector_raw`);
  `scripts/run_inference.py` (`DEF_CARIES_LESION_MODEL` block); `outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md` Sec 6 (frozen, `ef3f453`).
- **Follow-ups:** (1) `docs/results/model_metrics.md` — Stage 3's current-best caries numbers
  need updating to the adopted mechanism (this session). (2) `PAPER_MATERIAL.md` §8.22/8.24/8.25
  — the caries-constant-dominance narrative needs the resolution folded in, honestly scoped to
  "2 of 3 cohorts, not universal" (this session). (3) The Docker image predates this change and
  needs a rebuild before any demo (`transfer.md` §3 item 8 already flagged this for the
  isotonic-calibration wiring; now doubly stale). (4) `C4` abstention curves and any other
  downstream number computed FROM the caries gate's confidence distribution have not been
  re-run against the new mechanism — flagged, not done, out of scope for this pass. (5) The
  `app.py` "Caries conf (cal.)" column shows "—" for every tooth under the new default (no
  isotonic calibration for a detection score) — not broken, just less informative; a future
  session could add a lesion-detector-appropriate confidence display.

## 2026-09-04i — Manuscript reconciled with the Lever B adoption; two pre-existing numeric defects found and fixed

*(Label `04i`, continuing this session's `04f`/`04g`/`04h` sequence — see the note on 2026-09-04h
for why this session's letters do not start at `04b`.)*

- **What was done:** Folded the Lever B adoption into `paper/main.tex`, which until now
  described only the per-crop caries gate. Two defects that predate this session were found in
  the process and are recorded here because both had propagated into the manuscript.
- **Manuscript changes:**
  - Table I (pipeline stages) now reports **both** Stage-3a implementations and four totals —
    97.65 M / 75.29 M for the adopted lesion-detector default, 83.52 M / 61.16 M for the
    retained gate variant.
  - §System gained `\subsection{Stage 3a: two formulations of the same clinical question}`
    (`sec:lesiondet`) — the method, the pooled training mixture, the frozen 0.25 confidence,
    and an explicit statement of what the reformulation **costs**: both training corpora were
    external test data for the gate and are development data for the detector, so the detector
    is supported by one external cohort where the gate had two.
  - §Results gained `\subsection{Changing the task, not the architecture}` (`sec:leverb`) with
    the three-cohort table, the not-a-volume-effect check, and the B-single transfer collapse.
  - §Discussion reframed. The paper's existing claim — *"no amount of **architectural** work
    raises a ceiling imposed by the pairing of task and metric"* — is **confirmed** by Lever B,
    not falsified: five repairs to the classifier failed, and the ceiling moved only when the
    task did. The result is additive to the thesis rather than in tension with it.
  - Abstract gained one factual sentence so it is not contradicted by its own Results section.
- **Defect 1 — a headline number was mis-rounded, in the abstract and two tables.** The DENTEX
  constant's lesion agreement is 234/479 = **0.488518**, which rounds to **0.489**. The
  manuscript carried **0.488** in the abstract, Table II and Table IV. Cause: the eval scripts
  store `lesion_localization_agreement` rounded to 4 dp (0.4885), and `verify_paper_numbers.py`
  formatted *that stored value* with `f"{x:.3f}"` — rounding an already-rounded number, with the
  binary double breaking the tie downward. The verifier was therefore validating the manuscript
  against a number that was itself wrong, and had been since 28 Aug. **Audited every 3-dp
  agreement figure in the paper the same way: this is the only one affected** — the other
  fourteen are unchanged under either rule. Corrected to 0.489 in `main.tex` (4 occurrences),
  `model_metrics.md` and `PAPER_MATERIAL.md`; the derived Δ (+0.046 [+0.006, +0.089]) is
  unaffected. The verifier now recomputes from the integer counts using the house `r()`
  half-up rounder at every such site. **Not corrected** in `RESULTS_LOG` entries 2026-08-28*,
  which are history (rule 1), nor in `docs/paper/{manuscript.md,draft_spine.md,REBUILD_AUDIT.md}`,
  which are superseded drafts of the 28 Aug rebuild — a reader of those should take
  `main.tex` and `model_metrics.md` as authoritative.
- **Defect 2 — the parameter table mixed two counting conventions.** The detector row (27.62 M)
  counted `.parameters()`; the four ResNet18 rows (11.19/11.20 M) summed every tensor in the
  state dict, which includes batch-norm `running_mean`/`running_var` buffers. No single rule
  reproduced the table. The three parameter claims in `verify_paper_numbers.py` were meanwhile
  **hardcoded literals** carrying the provenance label `"torch.load over models/*/"`, so nothing
  had ever checked them. Fixed by `scripts/count_model_params.py` (new), which applies one
  stated rule — **learnable parameters only** — to all seven checkpoints and writes
  `outputs/param_counts/param_counts.json`. Each ResNet18 row drops by 9,620 buffer values; the
  totals move by 0.04 M. Nothing about any model changed. `models/16`'s `run_summary.txt`
  separately reports 25.28 M, the *fused* count ultralytics prints — a third quantity, also not
  an error, now noted in that file so it is never reported as drift.
- **Defect 3 — a live leakage hazard, fixed before it produced a number.**
  `cariesxrays_external.py --decision lesion-detector` would, without `--manifest-split val`,
  score the adopted detector on a random draw from all 6,000 CariesXrays images — roughly 4,800
  of which are its own training data. Nothing prevented this, and `lesion-detector` is now the
  pipeline default, so the next person to run the script's obvious invocation would have
  produced a spuriously excellent number. The script now **refuses** that combination, with an
  `--allow-train-overlap` escape hatch for a lesion model that never saw the corpus. Verified
  the guard fires. No published number was affected: every CariesXrays figure in the paper is a
  gate or constant arm, and neither trained on that corpus.
- **Metrics:** no new evaluation was run and no model changed. Corrected current-best values:
  DENTEX constant lesion agreement **0.489** (was 0.488, mis-rounded); pipeline parameter totals
  **97,649,753** default / **83,516,040** gate variant / **75,294,164** caries path default /
  **61,160,451** caries path gate variant (each was ~0.04 M higher under the buffer-inclusive
  count).
- **Key decision or insight:** the manuscript's numbers were never *false* after the Lever B
  adoption — every claim still described the gate, whose artefacts are unchanged — but the
  **referent of "our pipeline" had moved**, which is a subtler and more dangerous state than a
  wrong number, because nothing fails. It took writing the reconciliation to surface all three
  defects above; none would have been caught by re-running the existing checks.
- **Source:** `paper/main.tex`; `scripts/count_model_params.py` (new);
  `outputs/param_counts/param_counts.json` (new); `scripts/verify_paper_numbers.py` (90 → **117**
  asserted claims, all passing); `scripts/eval/cariesxrays_external.py` (leakage guard);
  `models/16_lever_b_pooled/run_summary.txt` (adoption section appended); `model_metrics.md`;
  `PAPER_MATERIAL.md` §9.
- **Follow-ups:** (1) The title and the paper's central thesis are **unchanged and are the
  author's call** — the abstract's closing "four things a constant cannot do" is arguably five
  now that localising the finding has been demonstrated, but changing that list changes the
  paper's prescription. (2) `docs/paper/{manuscript.md,draft_spine.md}` still carry 0.488 and
  the gate-only pipeline description; they are superseded drafts, and someone should decide
  whether to retire them rather than let them rot. (3) Still open from 2026-09-04h: the Docker
  rebuild, and the C4 abstention curves computed from the gate's confidence distribution, which
  are now scoped to `--caries-method gate` by implication but not in writing. (4) Five figure
  and table labels in `main.tex` (`fig:boneloss`, `fig:calib`, `fig:coverage`, `fig:stage2`,
  `tab:data`) are defined but never referenced — pre-existing, harmless to LaTeX, but worth a
  pass before submission.

## 2026-09-04j — Calibration/abstention scoped to the gate variant; Lever 2 benchmark row folded in, and re-verifying it against the AAAI PDF caught two transcription errors

- **What was done:** Two follow-ups from 2026-09-04i, both in `paper/main.tex`. No model was
  trained and no evaluation re-run.

### 1. Calibration and selective prediction are now scoped to the gate variant

§"What the constant cannot do" reported ECE **0.136 → 0.043** (isotonic), average precision
**0.550**, and caries abstention **+14.25 pp** — all measured on the **per-crop caries gate**,
which 2026-09-04h demoted from the pipeline default to a retained variant. Nothing in those
numbers was wrong, but they were doing work in the paper's argument that they can no longer do:
two of the four axes the Discussion proposes as the right way to compare OPG systems were, for
caries, being demonstrated on a component that no longer ships.

Changes: both figure captions (`fig:calib`, `fig:coverage`) now name the gate explicitly; the
subsection opens with the scoping and its consequence; the §Discussion axis list separates
numbering from caries on axes 2 and 3; and a **new first item in §Limitations** (`sec:limits`)
states that the adopted lesion detector has no calibrator and no coverage–accuracy curve, that
its score is a detection score rather than a posterior, and that the **pre-registered 0.30
abstention threshold was located on the gate's curve and does not transfer** to a quantity with a
different meaning. Closing this is named as the first piece of follow-up work and as needing its
own pre-registration — a threshold chosen after seeing the detector's curve would be exactly the
practice this paper argues against.

Numbering is unaffected (Stage 2 did not change) and demonstrates all four axes; the paper now
says so rather than letting the reader assume it of caries too.

**Not done, deliberately:** the abstract's closing "four things a constant cannot do" is still
four. Adding *localisation* as a fifth is the thesis change flagged on 04i and remains the
author's call. An earlier draft of this session added it and it was reverted.

### 2. Lever 2's benchmark row is in Related Work — and its stated precondition found real errors

§8.26's own instruction was "**re-verify the FPCL / baseline numbers against the AAAI PDF**
before quoting in the paper". Done first, against
`ojs.aaai.org/index.php/AAAI/article/view/30196/32123`, Table 1, p. 21945. **Two of the seven
transcribed rows were wrong.**

| claim, as transcribed 2 Sep | AAAI Table 1 | verdict |
|---|---|---|
| RetinaNet R50 13.0 / 30.5 / 10.2 | 13.0 / 30.5 / 10.2 | ✅ |
| **DINO 37.8 / 75.3 / 29.4** | **there is no DINO row** | ❌ corresponds to nothing published; nearest is FCOS 35.9 / 75.6 / 29.5 |
| Faster R-CNN R50 39.9 / 78.0 / 37.8 | 39.9 / 78.0 / 37.8 | ✅ |
| YOLOX 40.5 / 81.3 / 36.1 | 40.5 / 81.3 / 36.1 | ✅ |
| — | **Conditional-DETR 42.2 / 80.6 / 40.4** | ❌ omitted, and it is their **strongest** baseline |
| FPCL 48.2 / 84.1 / 50.6 | 48.2 / 84.1 / 50.6 | ✅ |
| **"~8 AP above every off-the-shelf baseline"** | 48.2 − 42.2 = **6.0** | ❌ the 8 came from comparing against YOLOx 40.5 because Conditional-DETR had been dropped |

The authors' own text states both gaps explicitly — "+7.7% (48.2 vs 40.5)" over the best CNN
baseline and "+6.0% (48.2 vs 42.2)" over the best transformer one — so the correct claim for the
manuscript is **"about six points above the strongest of their ten baselines"**. Had this gone
into `main.tex` unverified, the paper would have cited a non-existent baseline row and overstated
a margin by two points, both attributed to someone else's published table.

Also verified: their split is **4,800 train / 1,200 test** (p. 21942), so this project's seed-42
80/20 draw matches their ratio, as claimed.

**A third discrepancy, on the dataset size.** The 1 Sep record said "their stated 13,783 caries
instances against 13,784 measured here — a +1 counting-convention difference". The 13,783 is from
the authors' **GitHub README**; the **AAAI paper states 13,778** (p. 21942). The authors publish
two different figures and ours is a third. `main.tex` now reports **our own 13,784** and names all
three rather than adopting one of theirs. Nothing in this project is derived from the published
count, so no number moves.

**DVCTNet (48.9 / 84.7 / 52.2)** is from a different paper (arXiv 2508.20813) and was **not**
verified, so it is kept out of `main.tex` entirely and marked unverified in §8.26.

### What went into the manuscript

New `\subsection{A published benchmark, and what a stock detector reaches on it}`
(`sec:benchmarkrow`) in Related Work, with `tab:fpcl` (four verified baseline/FPCL rows plus
ours), the split caveat in the authors' own terms, and no claim of matching or beating FPCL. One
connective fact was added that §8.26 did not have: **the checkpoint behind our 48.2 AP is the same
`models/14` that is Lever B's single-corpus arm** — the arm that reaches 0.694 tooth-level
agreement on this corpus and falls to **0.086** on DENTEX. A strong benchmark number and a failure
to transfer are the same model, which is this paper's argument applied to its own result.

- **Metrics:** none new. One corrected external claim (FPCL's margin over baselines, ~8 → ~6 AP)
  and one corrected dataset figure (caries instances now reported as our measured 13,784, with the
  authors' 13,778 and 13,783 both named).
- **Key decision or insight:** a stated precondition earned its keep. "Re-verify against the PDF
  before quoting" was written on 2 Sep by the session that did the transcribing, and it caught two
  errors that no internal check could have — `verify_paper_numbers.py` asserts against *our*
  artefacts, and both of these were about someone else's table. **Numbers taken from other
  people's papers are the one class of claim this project has no automated guard for.**
- **Source:** `paper/main.tex` (`sec:benchmarkrow`, `tab:fpcl`, `sec:limits`, `sec:demonstrate`);
  AAAI PDF `ojs.aaai.org/index.php/AAAI/article/view/30196/32123` Table 1 p. 21945 and dataset
  statistics p. 21942; `github.com/Binz-Chen/AAAI2024_CariesXrays` README (the 13,783);
  `models/14_cariesxrays_lever2/run_summary.txt` (correction block appended, original left as
  written per rule 1); `PAPER_MATERIAL.md` §8.26 + §9.
- **Follow-ups:** (1) `PAPER_MATERIAL.md` had **two sections numbered §8.26** — the two parallel
  4 Sep sessions each wrote one. The Lever B one is renumbered **§8.27**; anything citing "§8.26"
  for Lever B before 4 Sep means §8.27. (2) The manuscript is now **14 pages** (12 before this
  session's work), still 0 errors / 0 undefined refs, 2 overfull hboxes both pre-existing. If the
  venue turns out to be ISBI's 4-page cap this is a much larger cut than it was. (3) Unchanged
  from 04i: the title, the thesis, the four-vs-five list, the Docker rebuild, and retiring
  `docs/paper/{manuscript.md,draft_spine.md}`.

## 2026-09-04k — Bibliography hygiene, figure-redistribution audit, and licence recording

- **What was done:** Three independent, self-contained fixes from a five-item open-work scan.
  No model trained, no headline result changed.

### 1. Bibliography sweep — found real defects, not just gaps

Built `scripts/audit_bib_urls.py` (new): a publisher-aware structural check, not a naive
substring match (a first pass flagged 26 false positives because MDPI/IEEE/PMC URL schemes
legitimately don't embed the DOI suffix — refined to cross-check each entry's own
`volume`/`number`/`pages` fields against the URL for MDPI, and the DOI suffix against the URL
slug for nature.com, both **exact-match conventions those platforms actually guarantee**).

**5 genuine mismatches found and fixed, all confirmed via the DOI resolver's own redirect
(authoritative — the registry, not a scrape):**

- `kim2024unsupervised`, `bhoopalan2026self`: the `url` field pointed at a **different Nature
  article entirely** (right DOI, wrong URL). A reader clicking through would land on the wrong
  paper. Fixed to the DOI's actual target.
- `mathur2025comparative`: bib's own `volume` field (82) was wrong (real volume 87); `url`
  pointed at article 26, not the entry's own `pages=80`.
- `kong2024integrating`, `karamuftuo2025panoramic`: bib's own `number` (issue) field was wrong
  in both, and both `url`s pointed at the wrong issue/article.

**12 → 3 entries missing a DOI**, corrected by re-deriving the true count from the file rather
than trusting the "19 DOI-less" figure carried in `transfer.md`/`PAPER_MATERIAL.md` (already
stale before today — the true count was 12, and is now 3). Resolved via Crossref, by title +
author-list cross-check (not title alone — two of these turned up a title match at a **different
conference than the bib's own `booktitle`**, which would have been a wrong DOI if added blindly):

- `gamal2025automated`, `sastika2025ai`: DOI added, venue already correct.
- `vickram2025extraction`: DOI added; `booktitle` **corrected** — was "ICECCT", author-list-
  confirmed real venue is ICEARS.
- `kaushik2025densenet201`: DOI added; `booktitle` **corrected** — was "ACCAI", author-list-
  confirmed real venue is ICPC2T.
- `yaswanth2025automated`: DOI added; **author field corrected** — was "Yaswanth, T. and
  others", Crossref (title-exact, venue-exact match) gives the full three-author list.
- `hamamci2023dentex`, `bai2025qwen25vl`, `zhou2025deep`, `hao2025mmoral`: arXiv DOIs
  (`10.48550/arXiv.*`) added, each verified to resolve via `doi.org` and (for `hao2025mmoral`)
  title/author-confirmed against its stated arXiv precursor.
- `bizjak2024advancing`: searched by title and by author, no Crossref record — genuinely
  DOI-less (small regional journal), now noted as such rather than left silently blank.
- `guo2017calibration`, `jocher2024yolo11`: already correctly documented as DOI-less
  (PMLR mints none; GitHub software has none) — untouched.

`audit_bib_urls.py` now reports **0 structural mismatches, 3 justified DOI-less entries**.
`audit_citations.py`: 28 `\cite` commands, 27 distinct keys, all resolve. `main.tex` recompiles
clean (14 pages, 0 errors, 0 undefined refs).

### 2. Figure-redistribution audit — closed, no re-run needed

Checked the compliance checklist item "confirm no figure in the submitted paper redistributes
any part of a restricted database" (`PAPER_MATERIAL.md` §8.19.5). The generator scripts for
three of the five figures (`fig_calibration.png`, `fig_coverage.png`, `fig_stage2.png`) predate
the 28 Aug manuscript rebuild and could not be located in `scripts/`, so provenance-by-script
wasn't available — **opened and visually inspected all five PNGs directly** instead. All five
are matplotlib bar/line charts built from aggregate JSON metrics (calibration reliability
diagram, coverage-accuracy curves, a taxonomy bar chart, a three-panel baseline comparison, and
a two-panel bone-loss domain-shift chart). None contains a reproduced radiograph, crop, or
overlay. **Confirmed clean.**

### 3. Licence recording — DENTEX and Ningxia, both closed

- **DENTEX: CC-BY-NC-SA-4.0**, confirmed on the dataset's Hugging Face README verbatim
  ("released under a Creative Commons Attribution (CC-BY-NC-SA) license... freely used for
  non-commercial research purposes... provided the original work is properly cited"). This
  project's use (non-commercial research, cited as `hamamci2023dentex`, no data redistribution)
  is compliant.
- **Ningxia: no formal licence.** The source repo (`github.com/qinxin99/qinxini`) has no
  LICENSE file and no CC/OSI text — the only stated term is "we kindly request that you do not
  use it for any commercial purposes." Weaker than DENTEX's, but this project's use still
  satisfies it. **Found and fixed a real citation gap in the process**: the source paper (Li
  et al., *J. Imaging Informatics in Medicine* 37(2):831–841, 2024, DOI
  `10.1007/s10278-024-00972-8`) was **not cited anywhere in `main.tex`**, despite the dataset's
  own README requesting citation on use. Added as `li2024multicenter` to `source.bib` and cited
  at both mentions of "Ningxia" in §Data (prose and the corpus table).

- **Metrics:** none changed. Bibliography-metadata corrections only (5 fixed defects, 9 DOIs
  added, 1 new citation added and wired in).
- **Key decision or insight:** the bibliography sweep was scoped as "cheap, mechanical hygiene"
  and turned into the highest-density defect-finding of the session — 5 of the ~34 entries with
  both a DOI and a URL were structurally wrong, and 2 of the DOI-less entries had a **wrong
  conference name recorded**, not just a missing identifier. A naive check (does the DOI suffix
  appear in the URL) would have produced 26 false positives and buried the 5 real ones; the
  useful check had to know each publisher's actual URL convention.
- **Source:** `scripts/audit_bib_urls.py` (new); `paper/source.bib` (5 corrections, 9 DOIs
  added, 1 new entry); `paper/main.tex` (2 new `\cite{li2024multicenter}`);
  `docs/results/PAPER_MATERIAL.md` §8.19.1 and §8.19.5 (both licence checklist items and the
  figure-redistribution item ticked).
- **Follow-ups:** none — all three items closed. Two more items from the same open-work scan
  (bootstrap CIs for the remaining metric gaps; the `split_v1` 590/591 leak's quantified impact
  on the Stage-1 detector's headline box mAP) are in progress as background evaluation runs and
  will be logged separately once they complete.

## 2026-09-04l — Ningxia periodontitis CI closed; Stage-1 detector CI closed after a failed AP-reproduction detour; the `split_v1` leak decision resolved

- **What was done:** The remaining two of three CI-coverage gaps flagged in `bootstrap_ci.py`'s
  own "not_covered" list, both CPU-only, no GPU. No model trained.

### 1. Ningxia periodontitis — closed cleanly, no surprises

`ningxia_external.py` was computing `affected_tooth_sensitivity()`'s per-image `(n_affected,
n_affected_flagged)` return value on every image, then discarding it — only the per-split
aggregate was kept. Added two fields (`n_affected`, `n_affected_flagged`) to the existing
per-image record (None for the caries branch, where the record's other fields already carry
the per-image counts). Re-ran the periodontitis category on the current default weights against
`D:\nangxia_dataset` — the aggregate reproduced the existing published numbers **exactly** (2.4%
/ 1.4% / 5.6% / 4.6% per split) before anything was bootstrapped, confirming the extension didn't
change the measurement. `bootstrap_ci.py` extended with a periodontitis section (same
`ratio()`/`cluster_bootstrap()` primitives as every other metric in that file):

| split | n images | sensitivity | 95% CI |
|---|---|---|---|
| test1 | 320 | 2.4% | [1.8, 3.0] |
| test2 | 297 | 1.4% | [0.9, 2.0] |
| test3 | 50 | 5.6% | [3.0, 8.7] |
| test4 | 69 | 4.6% | [2.7, 6.6] |
| **pooled** | 736 | **2.4%** | **[2.0, 2.9]** |

`main.tex`'s periodontal-branch paragraph updated with the pooled and per-site intervals.

### 2. Stage-1 detector — three failed attempts, then a deliberate pivot

The goal was a bootstrap CI on the published Box mAP@0.5 = 0.8100
(`models/11_yolo_seg_tufts_r1`, the current default, frozen `split_v1` test, 150 images). No
per-item dump existed, so `scripts/eval/tufts_detector_ap_bootstrap.py` (new) reimplemented
single-class AP@IoU=0.5 from scratch to bootstrap it. **This did not work, in an instructive
way, and the debugging trail is recorded in full because the next person touching Tufts
detector geometry should not repeat it.**

- **Attempt 1: ground truth from `teeth_bbox.json`.** Reasoned as the "more canonical" source
  (the original annotation the canonical bbox detector trained on, same source
  `regenerate_split_v1.py` reads) — recomputed AP@0.5 = **0.593** against published 0.810, a
  0.217 deviation. The script's own sanity check (flag anything >0.06 off) correctly refused to
  trust it.
  - **Diagnosis:** opened `data/tufts/dataset_seg_v2/images/test/100.JPG` directly. It renders
    as a **portrait-oriented arc** — no OPG is portrait — and its pixel dimensions (840×1615,
    taller than wide) confirm it. `dataset_seg_v2`'s images are rotated relative to the frame
    `teeth_bbox.json`'s coordinates describe; `teeth_bbox.json` predates that rotation step.
    Pairing a rotated image with un-rotated boxes silently misaligns almost every tooth — the
    same failure class as the R1 void run (26 Aug) and the withdrawn `dataset_seg` build, both
    "smoothly-falling loss on garbage," never a loud error.
- **Attempt 2: ground truth from the YOLO-seg polygon labels instead** (already sitting beside
  the same images, built FROM them by `convert_tufts_to_yolo_seg.py`, so frame-consistent by
  construction — no rotation step to get wrong a second time). Closed most of the gap:
  AP@0.5 = **0.701**, diff 0.109 — better, but still failing the sanity check. (A side fix in
  the same attempt: 6 test images have zero GT boxes, which is expected per `split_v1`'s own EDA
  count and was initially a crash, not a result — relaxed the assertion to a count-and-continue.)
- **Attempt 3: NMS IoU corrected from 0.5 to 0.7**, matching this detector's own recorded
  training/val config (`models/11_yolo_seg_tufts_r1/run/args.yaml`). This is the fix that should
  have closed the remaining gap. It made things **worse**: AP@0.5 = **0.672**, moving *away*
  from 0.810. A config-correct change making the number worse is the signal that the residual
  gap lives in this script's own from-scratch AP implementation — COCO-style AP has enough
  subtlety (interpolation convention, tie-breaking, box-vs-mask handling) that an independent
  reimplementation is not a small thing to get bit-exact — not in any remaining `predict()`
  setting worth guessing at further.
- **Decision: stop chasing AP, report a different, correctly-bootstrappable statistic instead.**
  Reused the already-gathered per-image predictions (no fourth inference pass needed) to compute
  **box detection recall at the pipeline's own deployed confidence (conf=0.25)** — a plain
  per-image ratio, the same *kind* of statistic as the paper's existing DENTEX "70.6% detection"
  figure, not a PR-curve integral. Result:

  | | value |
  |---|---|
  | Recall @ conf=0.25, all 150 images | **69.1%** [95% CI 65.5, 72.6] |
  | Recall, 149 images (leaked `590.JPG` excluded) | 69.0% |
  | Effect of excluding the leaked image | $-0.15$ pp — within noise |
  | Predicted-positive match rate @ conf=0.25 | 63.8% |

  The AP-reproduction attempt is kept in the output artefact
  (`outputs/tufts_detector_ap_ci/tufts_detector_ap_ci.json`, key
  `ap_diagnostic_not_the_number_of_record`) as a disclosed, labelled diagnostic — not deleted,
  not asserted as a manuscript claim, not bootstrapped into anything the paper cites.

**This also resolves the `split_v1` 590/591 leak decision** open since 1 Sep
(`transfer.md` §4, "whether to re-measure the detector, or document and move on"): the leak's
measured effect on this statistic is $-0.15$ points against a $\pm$3.5-point CI half-width —
**document and move on**, not re-measure everything.

- **Metrics:** Ningxia periodontitis pooled sensitivity 2.4% [2.0, 2.9] (n=736); per-site CIs
  above. Tufts Stage-1 detector recall @ conf=0.25: 69.1% [65.5, 72.6] (n=150); leak-excluded
  69.0%. Neither is a revision of a previously-reported number — the periodontitis point
  estimates reproduce exactly what was already published, and the detector recall is a new
  statistic that was never published before (the AP figure it sits beside, 0.8100, is unchanged
  and un-revised; the two measure different things).
- **Key decision or insight:** a config-correct fix making a reimplementation's accuracy *worse*
  is meaningful evidence, not noise — it means the remaining discrepancy is probably in the
  reimplementation's own logic, not in a parameter choice, and is the signal to stop iterating on
  parameters and question the approach instead. Chasing a fourth AP variant with no new evidence
  about *why* the first three didn't converge would have been guessing, not debugging. Switching
  to a metric this project already knows how to compute and bootstrap correctly (a plain ratio,
  not a curve integral) closed the actual gap — a bootstrapped confidence interval on Stage-1
  detection quality on this frozen split — without requiring the AP reimplementation to ever be
  made correct.
- **Source:** `scripts/eval/ningxia_external.py` (per-image `n_affected`/`n_affected_flagged`
  fields added); `scripts/eval/bootstrap_ci.py` (periodontitis section added); `scripts/eval/
  tufts_detector_ap_bootstrap.py` (new, full debugging trail in its own docstring);
  `outputs/ningxia_periodontitis_ci/ningxia_external.json`;
  `outputs/bootstrap_ci/bootstrap_ci.json`; `outputs/tufts_detector_ap_ci/
  tufts_detector_ap_ci.json`; `paper/main.tex` (periodontal paragraph, Stage-1 detector
  paragraph); `scripts/verify_paper_numbers.py` (117 → 127 asserted claims, all passing);
  `docs/results/PAPER_MATERIAL.md` §9; `transfer.md` §3/§4.
- **Follow-ups:** the two bone-loss ResNet18 classifiers' CI gap remains genuinely blocked (see
  `PAPER_MATERIAL.md` §9) — the only candidate per-item dataset on this machine is explicitly
  flagged `DIVERGENT -- do not use` by its own creator, and the original un-rotated Tufts
  radiographs needed to redo it properly were searched for directly and confirmed absent, not
  assumed absent. Closing it needs either those source files or a decision to leave the 0.923
  macro-F1 figure without an interval, stated as such.

## 2026-09-06 — Option B: the Tufts-FDI positional-feature-shift hypothesis is falsified; the gap is the image-derived position digit

- **What was done:** Ran Option B from the 5 Sep Tufts-FDI council
  (`docs/session-memory/2026-09-05b-tufts-fdi-improvement-council.md`) — a zero-GPU direction
  check, no pre-registration (produces no paper number). New script
  `scripts/eval/tufts_pos_feat_diagnostic.py` scores the deployed head (`models/10`, DENTEX+Tufts
  v2.0) on **GT-box crops** (detector removed as a confound) under positional-feature
  interventions, on Tufts test (3,786 crops) and DENTEX val (2,729, the control). This is
  `ablate_head_inputs.py` pointed at the deployed head + both corpora + a cross-geometry
  condition.
- **Dataset / config:** `data/{dentex,tufts}/enumeration_v1` non-jittered crops, `models/10`
  head, argmax (no Hungarian — crop-level). Conditions: `full`; `no_position` (pos-feats → that
  corpus's train mean); `shuffled_pos` (pos-feats from a random other tooth); `dentex_geom`
  (Tufts only — each Tufts feat standardised to its test distribution then rescaled to the
  DENTEX-train distribution, `f' = (f−μ_t)/σ_t·σ_d + μ_d`).
- **Metrics** (crop-level FDI-exact / position-digit / SIDE / quadrant, GT boxes, argmax):

  | condition | DENTEX val FDI-exact | Tufts test FDI-exact | Tufts position digit |
  |---|---|---|---|
  | full | 91.0% | **71.5%** | **73.5%** |
  | no_position | 77.5% (Δ −13.4) | 58.0% (Δ −13.5) | 72.2% (Δ −1.2) |
  | shuffled_pos | 52.9% (Δ −38.1) | 39.1% (Δ −32.4) | 72.3% (Δ −1.1) |
  | **dentex_geom** | — | **71.6% (Δ +0.1)** | **73.6% (Δ +0.1)** |

  Full-condition digit-level: DENTEX position 91.9% / SIDE 99.1% / quadrant 99.0%;
  Tufts position **73.5%** / SIDE 97.8% / quadrant 97.4%. Positional-feature distributions
  (non-jittered): DENTEX-train `bh` 0.233 vs Tufts-test `bh` 0.175 (−25%), `bw` 0.045 vs 0.039,
  `cy` 0.546 vs 0.577; `cx` matched. The crop-level Tufts FDI-exact **71.5% reproduces
  `crop_eval.py`'s published v2.0 Tufts-test number exactly** (`model_metrics.md`), so the
  harness is validated.
- **Key decision or insight:** **the positional-feature covariate shift is NOT a lever for the
  Tufts numbering gap.** Rescaling every Tufts positional feature to the DENTEX-train
  distribution (`dentex_geom`) moves FDI-exact by **+0.1 pp** and the position digit by +0.1 pp —
  i.e. a per-corpus positional-feature normalisation layer in a retrain would buy nothing. The
  hypothesis is cleanly falsified. **What the diagnostic localises instead:** the Tufts gap is
  the **position digit derived from the image** — 73.5% on Tufts vs 91.9% on DENTEX (an 18.4 pp
  gap), while SIDE (97.8 vs 99.1) and quadrant (97.4 vs 99.0) are nearly matched. The positional
  features do the *same* job on both corpora (they carry quadrant/laterality — Δ no_position
  −13.4/−13.5, Δ shuffled −38/−32 — and ~nothing for the position digit, Δ −1.0/−1.2 on both).
  This matches §8.16's taxonomy (74% of Tufts numbering errors are `off_by_one`) at the crop
  level. **Consequence for the council's option ranking:** Option A (an anatomical
  sequence/arch-order post-processor) is confirmed as the right lever — it corrects exactly the
  position-digit / off-by-one error class without needing the head to tell position 4 from 5 by
  appearance. Option D (retrain with more FDI corpora) is *weakened* — more data of the same
  anterior-crowding difficulty is unlikely to move an image-pathway position-digit limit. The
  end-to-end (detector-box) re-run is unnecessary: `dentex_geom` at +0.1 pp crop-level would not
  become a material gain end-to-end.
- **Source:** `scripts/eval/tufts_pos_feat_diagnostic.py` (new);
  `outputs/tufts_fdi_pos_diagnostic/pos_feat_diagnostic.json`;
  `docs/session-memory/2026-09-06-tufts-fdi-option-b-diagnostic.md`;
  `PAPER_MATERIAL.md` §8.16; `transfer.md` §3.
- **Follow-ups:** if the Tufts numbering story is to be strengthened before submission, the next
  step is to **pre-register Option A** (`outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md`,
  Lever B template) with a frozen bar (Tufts FDI-exact-of-detected Δ ≥ +2 pp lower bound, paired
  cluster bootstrap over the 149 test images) and a DENTEX end-to-end no-regression guard —
  Deepak's go/no-go, Track A still wins any time conflict. Option E (a better image-pathway
  position encoder — higher-res crops, wider context, or a spatial-prior transformer) is the
  post-submission lever that would attack the 73.5% directly.

## 2026-09-06b — Lever C ran and is a NULL: an arch-order constraint on the position digit does not move the Tufts number

- **What was done:** implemented and evaluated **Lever C**, the structural FDI position-digit
  post-processor pre-registered the same day
  (`outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md`, drafted `9492abe`, **frozen
  `e9270a3` before any code was written**, go-ahead "freeze as written"). Both pre-registered
  arms were built and scored against the deployed Hungarian assignment on the frozen Tufts test
  set and the DENTEX guard cohort. Zero GPU, no training, no data touched beyond the two Stage-2
  evaluation cohorts. New module `src/fdi_structural_repair.py`; `assign_fdi_head` gained an
  `assignment=` switch (default `hungarian`, unchanged) and was split into
  `head_joint_scores` + `assign_from_scores` so every arm scores the SAME forward pass;
  `validate_fdi_assignment{,_tufts}.py` and `run_inference.py` gained `--assignment`;
  `scripts/eval/lever_c_bootstrap.py` applies the frozen rule; 15 new tests
  (`tests/test_fdi_structural_repair.py`) encode the §7 local gate.
- **Dataset / config:** Tufts frozen test, 149 images / 3,760 permanent mirror-corrected GT teeth
  (primary) and DENTEX `disease/`, 164 leak-free images / 936 GT teeth (guard). Deployed
  `models/11` seg detector at conf 0.25, NMS IoU 0.50, imgsz 1024, and the deployed `models/10`
  head — identical boxes and identical head forward pass for all three arms, so the arms are
  paired by construction. τ = 0.30 (the codebase's existing `LOW_CONFIDENCE`), gap_factor = 1.6
  (`assign_fdi`'s existing default); no new hyperparameter, nothing swept.
- **Metrics** (paired cluster bootstrap over images, 10,000 resamples, seed 42):

  | | C-sort | C-dp |
  |---|---|---|
  | **PRIMARY** Tufts FDI-exact-of-detected Δ | **+0.16 pp [−0.22, +0.58]** | **+0.29 pp [−0.07, +0.69]** |
  | Tufts end-to-end Δ | +0.13 pp [−0.18, +0.47] | +0.24 pp [−0.05, +0.56] |
  | **GUARD** DENTEX of-detected Δ | −0.76 pp [−1.86, +0.29] | −0.30 pp [−1.27, +0.61] |
  | **GUARD** DENTEX end-to-end Δ | −0.53 pp [−1.30, +0.21] | −0.21 pp [−0.90, +0.43] |
  | anterior (pos 1–3) Δ | +0.52 pp | +0.52 pp |
  | posterior (pos 4–8) Δ | −0.11 pp | +0.11 pp |
  | images with a detected gap Δ | −0.07 pp | +0.07 pp |
  | **images with a contiguous arch Δ** | **+2.36 pp** (n=296) | **+2.36 pp** (n=296) |

  Absolute Tufts of-detected: control **78.19%** → C-sort 78.35% → C-dp **78.48%**.
  **Frozen rule §5: primary FAIL (bar was a +2.0 pp lower bound), guard FAIL (−1.0 pp lower
  bound; C-dp reaches −1.27, C-sort −1.86), stratified PASS. Verdict: DO NOT ADOPT, both arms.**
  The pipeline default stays `hungarian`; both arms are retained behind `--assignment` and
  reported as an ablation. **No current-best number in `model_metrics.md` moves.**
- **Harness validation:** the control arm reproduces the published Stage-2 numbers — DENTEX
  recall 70.6% / of-detected 82.6% / end-to-end 58.3%, matching `RESULTS_LOG` 2026-09-04d to the
  digit; Tufts 82.2% / 78.2% / 64.2% against the published 82.4 / 78.6 / 64.8. The Tufts 0.2–0.6 pp
  shortfall is a **known machine-local artefact, not a code change**: this Windows clone has no
  copy of the original upright `Radiographs/`, and its `data/tufts/ZIP/Radiographs_upright/` is
  180° from the frame `upright_box()` maps GT into (verified two ways —
  `CW(Radiographs_rotated) == Radiographs_upright` at mean|diff| 0.61, and the 180° frame lifts
  of-detected on 12 val images from 12% to 64%), so the evaluation frame was regenerated by
  rotating and re-encoding at JPEG q95. Every arm consumes those identical pixels, so the deltas
  — the only quantities the acceptance rule reads — are unaffected.
- **Key decision or insight:** **the missing sequence constraint is not what holds the Tufts
  position digit back.** The mechanism was measured rather than guessed
  (`structural_diagnostics`, 149 test images, 3,489 detections, 541 quadrant groups): **72.6% of
  detections are anchors** and therefore immovable by construction, **13.4% sit in the 48
  over-full groups** (>8 detections in one head-argmax quadrant, where no strictly increasing
  labelling of 1..8 exists), leaving **13.9% movable at all**. τ = 0.30 was frozen to the existing
  `LOW_CONFIDENCE` precisely so Lever C would add no tunable — and at 0.30 the head clears the
  anchor threshold on most teeth, so the longest-increasing-subsequence anchors most of the arch
  *including teeth that are confidently wrong*, which is exactly the off-by-one error the
  constraint was meant to correct. The one stratum where the method does what it was designed to
  do is the contiguous-arch subset: **+2.36 pp on 296 detected teeth (9.5% of the cohort)** —
  a real signal in the place its assumption holds, and too small a slice to move the cohort.
  C-dp beats C-sort on every headline quantity, so the DP does earn its complexity over the cheap
  arm; with both far from the bar that comparison is academic. **Combined with Option B**
  (`RESULTS_LOG` 2026-09-06, positional-feature shift falsified at +0.1 pp), the Tufts numbering
  gap is now bounded from two directions: not the positional features, and not the assignment.
  What remains is the **image-derived position digit itself** (73.5% on Tufts GT crops vs DENTEX
  91.9%) — Option E, post-submission, needing its own pre-registration.
- **Source:** `outputs/lever_C_fdi_structural_postproc/` — `PRE_REGISTRATION.md` (§9 carries the
  freeze and verdict hashes), `run_summary.txt`, `lever_c_bootstrap.json`,
  `tufts_test/stage2_*_head{,__structural-sort,__structural-dp}.json`,
  `dentex/stage2_*_head{,__structural-sort,__structural-dp}.json`,
  `tufts_val/` (the §7.5 sanity run). Code: `src/fdi_structural_repair.py`,
  `scripts/eval/lever_c_bootstrap.py`, `tests/test_fdi_structural_repair.py`.
- **Follow-ups:** (1) `PAPER_MATERIAL.md` §8.16 now carries the null beside the caries-repair and
  detector-lever ablations — it *strengthens* the framing that the limit is the image pathway.
  (2) Nothing in `main.tex` changes: it never claimed the Tufts end-to-end number, and no
  current-best number moved. (3) If Lever C is ever revisited, the two levers this run exposes
  are τ (an anchor threshold chosen for the *flag* semantics, not for anchoring) and the
  over-full-group case — but both are new pre-registrations, not edits to this one.
  (4) Option E remains the lever that attacks 73.5% directly.

## 2026-09-06c — the Windows clone's Tufts crop corpus is cut from the wrong source frame (labels fine, pixels wrong)

- **What was done:** re-ran `scripts/eval/tufts_pos_feat_diagnostic.py` on the Windows box to
  close a traceability gap — `RESULTS_LOG` 2026-09-06 cites
  `outputs/tufts_fdi_pos_diagnostic/pos_feat_diagnostic.json`, which `.gitignore`'s `outputs/*`
  rule had kept untracked, so the numbers were uncheckable anywhere else. The re-run reproduced
  DENTEX and did **not** reproduce Tufts, and the cause was then isolated.
- **Dataset / config:** `data/{dentex,tufts}/enumeration_v1` non-jittered GT-box crops,
  `models/10` head, argmax, CPU. New `scripts/eval/tufts_crop_frame_check.py` re-cuts the same
  manifest boxes from candidate source directories and scores each.
- **Metrics:** DENTEX val reproduces to a tenth of a point (full **91.1%** vs published 91.0%,
  `no_position` 77.6% vs 77.5%, `shuffled_pos` 52.9% vs 52.9%). **Tufts test does not: 18.1%
  FDI-exact against a published 71.5%.** On 400 Tufts test rows:

  | crops scored | quadrant | position | FDI exact |
  |---|---|---|---|
  | as stored in `data/tufts/enumeration_v1` | 33.0% | 36.8% | **11.5%** |
  | re-cut from `Radiographs_upright/` (this clone's) | 33.0% | 36.0% | 11.5% |
  | **re-cut from `Radiographs_upright_fixed/` (180°)** | **97.2%** | **75.2%** | **73.5%** |

- **Key decision or insight:** **the crop corpus on this machine is cut from the wrong source
  frame — the labels are correct and the pixels are not.** Established by elimination:
  (1) the manifest is internally consistent and matches DENTEX's conventions exactly (Q1/Q4
  image-left, Q1/Q2 upper, |cx−0.5| rising 0.015→0.236 across positions 1→8), so the labels are
  not mirrored; (2) all **eight** dihedral transforms of the stored crops were scored and the
  best reached 37.2%, so it is not a rotated crop — each crop shows a *different tooth* than its
  label, which no transform of the crop can undo; (3) re-cutting the same boxes from the 180°
  frame reproduces the published number. `data/tufts/enumeration_v1/meta.json` records the corpus
  was built from a now-deleted scratchpad directory on this machine, and the same clone's
  `data/tufts/ZIP/Radiographs_upright/` is likewise 180° from the frame `upright_box()` maps
  annotations into — one root cause, an un-rotation applied in the wrong direction here.
  **The Mac's copy is valid and the published Option B numbers stand.** This is a machine-local
  data defect, and it fails **silently**: labels look right, crops look like teeth, accuracy is
  simply wrong. **It does not touch Lever C** (2026-09-06b), which runs on radiographs through
  the detector and whose control arm reproduces the published Stage-2 numbers on both cohorts.
- **Source:** `scripts/eval/tufts_crop_frame_check.py` (new),
  `outputs/tufts_fdi_pos_diagnostic/{crop_frame_check.json,pos_feat_diagnostic.json,README_WINDOWS_RUN.md}`
  — all three now tracked via a `.gitignore` exception, which closes the original gap for the
  DENTEX half. Also fixed: the diagnostic crashed on a Windows console (cp1252 vs the Greek
  deltas it prints) **after** the scoring work and **before** writing its JSON.
- **Follow-ups:** (1) rebuild `data/tufts/enumeration_v1` on this machine from
  `data/tufts/ZIP/Radiographs_upright_fixed/` before ANY crop-level work is done here — until
  then it is silently wrong. (2) The other Tufts-derived corpora on this clone
  (`bone_loss_crops_rebuilt`, `severity_dataset`, `dataset_seg*`) may share the defect and are
  untested; `tufts_crop_frame_check.py` generalises to any manifest of normalised boxes.
  (3) Consider making the frame check a `verify_invariants` entry so a wrong-frame corpus fails
  loudly on a fresh machine instead of producing a plausible-looking number.

## 2026-09-06d — Tufts crop corpus rebuilt on the Windows clone; Option B independently reproduces

- **What was done:** rebuilt `data/tufts/enumeration_v1` from the corrected frame
  (`data/tufts/ZIP/Radiographs_upright_fixed/`, the 180°-rotated set, now generated for all 1,000
  images), replacing the wrong-frame build diagnosed in 2026-09-06c. The defective corpus was
  **archived, not deleted** — `_repo_archive/tufts_enumeration_v1_wrongframe_2026-09-06/`, recorded
  in `ARCHIVE_MANIFEST.md` with the command that restores it — because it is the evidence for that
  entry. Then re-ran the Option B diagnostic against the rebuilt corpus.
- **Dataset / config:** `scripts/tufts/build_enumeration_crops.py --images
  data/tufts/ZIP/Radiographs_upright_fixed --split outputs/eda_tufts/split_v1.csv`, seed 42,
  expand 1.5, jitter-copies 1 — every parameter as the original build.
- **Metrics — the rebuild is label-identical and pixel-corrected:**
  - The new `enumeration_manifest.csv` is **byte-identical to the old one after sorting**: same
    42,755 rows, same labels, same coordinates, same split assignment, same duplicate resolution
    (1008→1007, 591→590). Only the pixels changed — which is exactly the claim 2026-09-06c made
    about where the defect was.
  - Same write stats (train 35,248 / val 3,721 / test 3,786 / 17 degenerate) and the same geometry
    guard reading (0.04% degenerate).
  - `tufts_crop_frame_check.py` on the rebuilt corpus: stored crops **73.2%** FDI-exact
    (400 test rows) against the wrong-frame build's **11.5%**, matching the 73.5% reference of
    boxes re-cut directly from the corrected frame.
- **Option B re-run on the rebuilt corpus — it reproduces the published result independently:**

  | condition (GT-box crops, argmax) | published (Mac, 2026-09-06) | this rebuild (Windows) |
  |---|---|---|
  | DENTEX val FDI-exact, full | 91.0% | **91.1%** |
  | Tufts test FDI-exact, full | 71.5% | **70.8%** |
  | Tufts position digit | 73.5% | 72.7% |
  | Tufts SIDE / quadrant | 97.8% / 97.4% | **97.8% / 97.5%** |
  | Tufts `no_position` | 58.0% | 57.6% |
  | Tufts `shuffled_pos` | 39.1% | 39.3% |
  | **Tufts `dentex_geom`** | **71.6% (Δ +0.1)** | **70.8% (Δ +0.0)** |

  Everything lands within 0.7 pp, consistent with the corrected frame being a second-generation
  JPEG (the source was re-encoded at q95 when rotated). **The conclusion reproduces exactly:
  mapping Tufts positional features onto the DENTEX-train distribution moves FDI-exact by
  +0.0 pp here against +0.1 pp there — the positional-feature covariate shift is not a lever, on
  two independent machines and two independently built crop corpora.**
- **Key decision or insight:** the traceability gap that started this is now closed properly
  rather than papered over. `outputs/tufts_fdi_pos_diagnostic/` is tracked, its JSON is a genuine
  reproduction rather than a re-run of a broken corpus, and the machine-local defect that made the
  first attempt fail is documented, archived and guarded. New `verify_invariants` entry
  **"crop source frames"** re-cuts a few manifest rows from the source `meta.json` names and
  compares pixel-wise (tufts max mean|diff| 3.6 = re-encode noise, dentex 0.0). Its docstring is
  explicit about what it does **not** catch: a corpus that is internally consistent but built from
  the wrong frame looks perfect to it — that needs `tufts_crop_frame_check.py`, which scores the
  head on candidate frames. Recorded so nobody files this as "cannot happen again".
- **Source:** `scripts/tufts/build_enumeration_crops.py` (unchanged, re-run),
  `outputs/tufts_fdi_pos_diagnostic/{pos_feat_diagnostic.json,crop_frame_check.json,crop_frame_check_rebuilt.json,README_WINDOWS_RUN.md}`,
  `_repo_archive/ARCHIVE_MANIFEST.md` (2026-09-06 entry),
  `scripts/eval/verify_invariants.py::inv_crop_frames`.
- **Follow-ups:** (1) the other Tufts-derived corpora on this clone
  (`bone_loss_crops_rebuilt`, `severity_dataset`, `dataset_seg*`) were built in the same era and
  are **still untested** — the bone-loss ones matter most, since that branch's 0.923 is the
  project's strongest in-domain number and its rebuild attempt already scored anomalously low
  (2026-08-27u/28c). Worth checking whether that anomaly and this defect are the same bug.
  (2) `data/tufts/ZIP/Radiographs_upright/` is still the wrong frame and still the default many
  scripts would reach for; consider retiring or renaming it on this machine.

## 2026-09-06e — audit of every Tufts-derived corpus on this machine: the bone-loss crops are NOT affected, and the 0.40-vs-0.83 gap is not orientation

- **What was done:** after 2026-09-06c/d found the enumeration crop corpus cut from the wrong
  frame, audited every other Tufts-derived corpus on the Windows clone rather than assuming the
  defect stopped there. Two instruments, both already in the repo: the pixel/model check
  (`tufts_crop_frame_check.py`, and a direct re-cut comparison for corpora with a different crop
  contract) and the repo's own `_tufts_align.image_orientation_score`, now wrapped as
  `scripts/eval/tufts_corpus_audit.py` so the whole surface is one command instead of shell history.
- **Bone-loss crops — clean, verified two independent ways.**
  1. **Pixel:** the stored `bone_loss_crops_rebuilt/val_cw` crops re-cut from
     `Radiographs_upright_fixed` (the corrected frame, 1.5×W/2.0×H expansion) differ by
     **mean|diff| 0.39** — JPEG noise — against **47.99** for the wrong frame. They are in the
     correct frame.
  2. **Model:** scoring the frozen Stage-4a classifier over the three stored variants reproduces
     `RESULTS_LOG` 2026-08-27u's table **exactly**, confusion matrices included:

     | variant | macro-F1 | sensitivity | confusion |
     |---|---|---|---|
     | `val` (portrait, teeth sideways) | 0.4869 | 0.0000 | TN=745 FP=5 FN=35 TP=0 |
     | `val_ccw` | 0.5371 | 0.0857 | TN=732 FP=18 FN=32 TP=3 |
     | `val_cw` (the correct upright frame) | **0.7145** | **0.4000** | TN=737 FP=13 FN=21 TP=14 |
     | *documented (full 1,558, incl. jittered)* | *0.9233* | *0.8305* | *TN=1492 FP=7 FN=10 TP=49* |

- **So the bone-loss gap is not the frame defect**, and one candidate cause is now also excluded:
  the source notebook reads radiographs with `cv2.IMREAD_GRAYSCALE` while
  `rebuild_bone_loss_crops.py` uses `IMREAD_COLOR` — rebuilding both ways gives **identical**
  predictions (macro-F1 0.7015 / sensitivity 0.3714 either way), because these radiographs are
  true greyscale. What remains is what 2026-08-27u already named: the 785 reproducible rows are a
  **different population** from the reported 1,558 (which include 773 crops whose jitter offsets
  were never saved), plus the source-image provenance (the notebook cut from the original
  un-rotated `Radiographs/`, absent here; ours is a rotate-and-re-encode round trip of it).
- **One new datum on how fragile that measurement is:** re-cutting from the re-encoded
  `Radiographs_upright_fixed` instead of rotating in memory moves sensitivity **0.4000 → 0.3714**
  — a single borderline positive flipping on JPEG noise. At 35 positives the subset cannot settle
  a 0.40-vs-0.83 question either way, which is an argument for leaving the 0.923 flagged as
  irreproducible rather than trying to approximate it.
- **Audit of the image directories** (`tufts_corpus_audit.py`, orientation score >1 = aligned):

  | directory | score | verdict |
  |---|---|---|
  | `ZIP/Radiographs_rotated` | 0.967 | **MISALIGNED** — the known pre-22-Aug copy |
  | `ZIP/Radiographs_rotated_fixed` | 1.030 | ALIGNED |
  | `dataset_seg/images/{train,val}` | 0.976 / 0.959 | **MISALIGNED** — expected: this is the withdrawn v1 (2026-08-27a) |
  | `dataset_seg_v2/images/{train,val}` | 1.039 / 1.074 | ALIGNED — and `models/11`'s own run_summary records 0.837 median IoU / 99.4% agreement for its labels |

  `dataset_seg_v2`'s images are **byte-identical** to `Radiographs_rotated_fixed` (mean|diff| 0.00),
  which independently corroborates today's frame conclusion from a third direction: the detector
  that reproduces its published Tufts recall was trained on that frame.
  `severity_dataset` and `resampled_dataset` hold **metadata only, no pixels** — nothing to check.
- **Key decision or insight:** the wrong-frame defect is contained to `Radiographs_upright/` and
  the corpus built from it (now rebuilt). Everything else on this machine is either correct or
  already-known-bad-and-superseded. **What is worth acting on is that three misaligned artefacts
  still sit on disk under inviting names** — `Radiographs_rotated`, `Radiographs_upright`, and
  `dataset_seg` — and each is the *shorter, more obvious* name next to its corrected counterpart.
  That is how the enumeration corpus got built from the wrong one in the first place.
- **Source:** `scripts/eval/tufts_corpus_audit.py` (new), `scripts/eval/tufts_crop_frame_check.py`,
  `scripts/yolo/_tufts_align.py::image_orientation_score`,
  `models/11_yolo_seg_tufts_r1/run_summary.txt`, `RESULTS_LOG` 2026-08-27a / 2026-08-27u / 2026-09-06c/d.
- **Follow-ups:** (1) rename or archive the three misaligned artefacts so the inviting name is the
  correct one — the single highest-value follow-up here, and not done in this session because
  moving `dataset_seg` touches a path other scripts may still reference. (2) The bone-loss
  reproduction gap stays open and stays flagged; nothing measured here changes what the paper says
  about it.

## 2026-09-06f — the three misaligned Tufts copies are archived, and the two pointers that sent people to them are fixed

- **What was done:** acted on 2026-09-06e's follow-up. Three **180°-out** directories sat on this
  machine under the *shorter, more inviting* name beside their corrected counterpart —
  `Radiographs_rotated` (vs `_fixed`), `Radiographs_upright` (vs `_fixed`), and `dataset_seg`
  (vs `dataset_seg_v2`). That naming has now caused **two** silent failures: a 90-epoch GPU run
  trained on misaligned masks and discarded (2026-08-27a) and an entire enumeration crop corpus
  built from the wrong frame (2026-09-06c). All three were **moved to
  `_repo_archive/misaligned_tufts_frames_2026-09-06/`** (717 MB total, `mv` per rule 3, recorded
  in `ARCHIVE_MANIFEST.md`), so a stale reference now raises `FileNotFoundError` instead of
  silently reading wrong pixels.
- **Why archive rather than rename.** A rename only moves the problem: some *other* path becomes
  the inviting one, and it would falsify provenance that `meta.json` and `run_summary.txt` files
  record truthfully (`models/11` really was trained on `dataset_seg_v2`). Removing the name
  entirely is the version that fails loudly.
- **The two live pointers, both fixed:**
  1. `scripts/tufts/build_enumeration_crops.py` — its **geometry-guard error message** named
     `data/tufts/ZIP/Radiographs_upright`, the wrong copy. That message fires *precisely* when
     someone already has a frame problem, and then sends them to the bad directory. This is the
     most plausible proximate cause of 2026-09-06c. It now names `Radiographs_upright_fixed`,
     states the 11.5%-vs-71.5% consequence, and points at `tufts_crop_frame_check.py`.
  2. `scripts/tufts/regenerate_split_v1.py` — defaulted `IMG_DIR` to `Radiographs_rotated`.
     It only needs the file inventory, so no split was ever wrong because of it, but the default
     is now resolved by a helper that prefers a `_fixed` copy when one exists. Machine-agnostic:
     on macOS the canonical name is the correct one and no `_fixed` sits beside it, so both
     machines resolve correctly without anyone remembering which is which — the same convention
     `convert_tufts_to_yolo_seg.py` and `_tufts_align.pick_image_dir` already use.
- **Everything still resolves, verified rather than assumed:** `pick_image_dir` still selects
  `Radiographs_rotated_fixed` by measurement (alignment 1.040) with the archived candidate gone;
  `tufts_crop_frame_check.py` keeps its **negative control** by resolving the archived
  `Radiographs_upright` (stored crops 74.5%, correct frame 75.5%, wrong frame **9.5%** — the
  control still discriminates); `verify_invariants` "crop source frames" OK; `pytest` **174**;
  `verify_paper_numbers` **127/127**.
- **Key decision or insight:** an audit that cries wolf gets ignored, so one thing was fixed in
  the tool rather than the data. `tufts_corpus_audit.py` initially scored
  `Radiographs_upright_fixed` as MISALIGNED (0.791) — but `image_orientation_score` compares
  against **portrait** boxes and simply does not apply to an upright directory, returning a low
  number rather than raising. The entry is now explicitly skipped with the reason printed,
  instead of a threshold being loosened to hide it. The audit's expected state for all three
  archived copies is **ABSENT**, and it exits non-zero if any reappears.
- **Source:** `_repo_archive/ARCHIVE_MANIFEST.md` (2026-09-06b entry),
  `scripts/eval/tufts_corpus_audit.py`, `scripts/eval/tufts_crop_frame_check.py`,
  `scripts/tufts/{build_enumeration_crops,regenerate_split_v1}.py`.
- **Follow-ups:** none open on this thread. The frame defect is diagnosed (2026-09-06c), repaired
  (2026-09-06d), bounded (2026-09-06e) and now guarded at the point where it entered.

## 2026-09-07 — the bone-loss val crops were never lost: sensitivity reproduces EXACTLY (49/59), and the 27 Aug rebuild was the thing that was wrong

- **What was done:** the project owner supplied the Tufts Drive folder. It contains
  `resampled_dataset/{train,val}` — **the original bone-loss crops, including the 773 jittered
  ones** this project has repeatedly documented as *irreproducible by construction*. Downloaded
  the val split (`val/1` complete at 59 files; `val/0` still downloading, Drive throttles a
  1,499-file shared-link pull) and scored the frozen Stage-4a model on the **complete positive
  class**.
- **The claim that was wrong, and where it came from.** `RESULTS_LOG` 2026-08-27u established
  that ±15% jitter was applied at construction time from an RNG **whose offsets were never
  saved**, and concluded those crops "cannot be regenerated by anyone, on any machine". That
  reasoning is correct and remains correct — but it answers *regeneration*, not *availability*.
  **The pixels themselves were sitting in Drive the whole time and nobody checked.** The
  conclusion propagated from there into `PAPER_MATERIAL.md` §8 ("a selected maximum on an
  irreproducible subset"), `docs/paper/SUBMISSION_TODO.md` (BLOCKED), `transfer.md`, and the
  project overview — five places asserting a blocker that a directory listing would have closed.
  This is `CLAUDE.md` rule 4's failure mode exactly: an inference nobody re-tested hardened into
  "known".
- **Metrics — exact reproduction on the complete positive class** (59 crops = 35 clean + 24
  jittered, filenames an exact match to `val_metadata.csv`):

  | | TP | FN | sensitivity |
  |---|---|---|---|
  | **original crops (this run)** | **49** | **10** | **0.8305** |
  | *documented (2026-04-06)* | *49* | *10* | *0.8305* |

  Matching to the digit, on the metric the August rebuild collapsed. Split by jitter: clean
  29/35 = 0.829, jittered 20/24 = 0.833 — the jittered crops are neither easier nor harder, which
  also retires the "maybe jitter made them easy" hypothesis.
- **The August rebuild was defective, not the reported number.** On the **same 35 clean positive
  teeth**, same model, same labels: **original crops 29/35 (0.829)** vs **the 27 Aug rebuild
  14/35 (0.400)**. Comparing the two crop sets tooth-by-tooth, mean|diff| ≈ 42 and pixel
  correlation ≈ **+0.50** — the same tooth, materially different framing, not a re-encode. So
  2026-08-27u's "0.40 against a documented 0.83 is still divergent" was evidence about the
  *rebuild pipeline*, and was read as evidence about the *original measurement*. The crop
  geometry the notebook used is not what `rebuild_bone_loss_crops.py` reconstructs; the notebook
  reads segmentation masks as well as boxes, which is the leading candidate and is not yet pinned.
- **Key decision or insight:** **the bone-loss branch's in-domain result is reproducible after
  all**, and the three `PAPER_MATERIAL.md` §9 items blocked on these crops — calibration, a
  PR/threshold sweep, and confidence intervals — are unblocked. The limitation as written in the
  paper ("irreproducible subset", "selected maximum") **must be corrected**, not softened: it
  overstates a weakness that does not exist. Nothing here rehabilitates the branch's
  *generalisation* failure (0.923 in-domain vs 2.4% external sensitivity), which is a separate,
  externally-validated finding and stands untouched.
- **Source:** `data/tufts/resampled_dataset/val/{0,1}` (from the project Drive; `val/1` complete,
  `val/0` in progress), `data/tufts/resampled_dataset/metadata/val_metadata.csv`,
  `models/03_bone_loss_model_training_notebook_models/bone_loss_resnet18_best.pth`.
- **Follow-ups:** (1) finish the `val/0` pull (1,499 crops) and report the **full macro-F1** —
  documented 0.9233, TN=1492 FP=7 FN=10 TP=49 — as a whole-set reproduction. (2) Then run the
  three unblocked §9 items on the original crops. (3) Correct the "irreproducible" claim in
  `PAPER_MATERIAL.md` §8, `SUBMISSION_TODO.md`, `transfer.md` and `PROJECT_OVERVIEW.html` — with a
  new log entry, never by editing this one or 2026-08-27u. (4) Pin down why the rebuild's geometry
  differs, so `rebuild_bone_loss_crops.py` is either fixed or retired rather than left as a trap.

## 2026-09-07b — root cause of the bone-loss rebuild divergence: a box-convention mismatch (and a circular check of mine, retracted)

Extends 2026-09-07 (which recovered the original crops and reproduced sensitivity 49/59 exactly).
Nothing here changes that result.

- **What was done:** with 99 of the original `Radiographs/` downloaded, re-cut the non-jittered
  val crops **the way the source notebook does** — reading `teeth_bbox.json`'s `bounding box` as
  `[y1, x1, y2, x2]` against the **landscape** `Radiographs/` — and compared against the stored
  original crops and the frozen Stage-4a model.
- **Metrics:**

  | | result |
  |---|---|
  | teeth re-cut (non-jittered, radiograph available) | 187 |
  | **bit-for-bit identical to the stored original crop** | **187 / 187** |
  | accuracy vs stored labels | **0.9947** |

- **Root cause, confirmed:** `scripts/tufts/rebuild_bone_loss_crops.py` reads the same field as
  `[x1, y1, x2, y2]` in the **portrait** frame and rotates it CW; the notebook that actually built
  the training data reads `[y1, x1, y2, x2]` landscape. The two differ by a horizontal mirror, so
  the rebuild cut a *different region* for every tooth — which is why it scored 0.400 sensitivity
  against the original crops' 0.829 on the same 35 teeth, and why the two crop sets correlate only
  ~0.50. **This closes follow-up (4) of 2026-09-07.** It is a defect in the rebuild script's
  premise, not in the reported 0.9233.
- **A claim of mine, retracted before it spread.** On first seeing this I measured where each
  Universal title lands under both readings, found the notebook's reading puts Universal 1–8 on
  the image-left, and concluded that §8.8b's "Tufts numbering is mirrored" finding was an
  artefact of the wrong field order. **That was circular.** The test assumes Tufts titles are
  true Universal numbers, which is precisely the premise §8.8b disputes: "boxes mirrored + true
  labels" and "boxes correct + mirrored labels" are geometrically indistinguishable, and §8.8b
  says so in as many words ("not anatomy — the jaw is symmetric"). The mirror finding rests on
  two checks my test does not touch and does not weaken: the physical **L side-marker**, and a
  **DENTEX-trained arbiter** at 91.7% mirrored vs 6.1% direct over 1,188 matched teeth with a
  98.6% DENTEX control. **§8.8b stands; treat the retraction, not the claim, as the record.**
- **One genuine loose thread, recorded not resolved:** §8.8's supporting IoU comparison
  (portrait 0.611 vs landscape 0.489, measured "against detector boxes") is **partly circular** —
  the detector was trained on data built with the portrait reading, so it should agree with it.
  That does not overturn anything, because the L-marker and arbiter evidence are independent of
  the detector, but the IoU line is weaker support than it reads as. Worth a footnote if §8.8 is
  ever cited as the reason for the convention.
- **Source:** `data/tufts/ZIP/Radiographs/Radiographs/` (99 of 1,000 originals; Drive throttled
  the rest), `data/tufts/resampled_dataset/val/`, `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`,
  `scripts/tufts/rebuild_bone_loss_crops.py`, `PAPER_MATERIAL.md` §8.8/§8.8b.
- **Follow-ups:** (1) `rebuild_bone_loss_crops.py` now carries a warning naming the mismatch and
  pointing at the original crops; it is no longer the way to obtain them. (2) The question that
  *is* still open and is NOT settled by any of this: the Stage-2 head trains on DENTEX and Tufts
  crops that are horizontal mirrors of each other in image content (labels flipped to match).
  That is self-consistent for quadrant and side, but a tooth's crown/root asymmetry is not
  mirror-invariant — which is a plausible, untested contributor to the Tufts position-digit
  weakness (73.5% vs DENTEX 91.9%, `RESULTS_LOG` 2026-09-06). Testing it needs its own
  pre-registration; it is not claimed here.

## 2026-09-07c — Docker image rebuilt: the deployment artefact now ships the Lever B caries path

- **What was done:** rebuilt `opg-demo` (the image predated the 4 Sep Lever B adoption, so the
  demo still ran the retired caries gate as Stage 3a) and verified it rather than assuming.
- **Build-time assertions all passed** — the Dockerfile fails the build on each: `torch 2.2.0+cpu`
  (pinned and CPU-only, not a CUDA wheel), `numpy 1.26.4` (<2, so `scipy.optimize`'s Hungarian
  assignment still imports), `linear_sum_assignment` executes, no jupyter stack leaked, and
  Streamlit 1.63.0 still accepts `width="stretch"`.
- **Contents verified inside the running image**, which was the point of the rebuild:

  | | |
  |---|---|
  | `DEF_CARIES_LESION_MODEL` (`models/16`) | **PRESENT** |
  | `DEF_DETECTOR` (`models/11`), `DEF_FDI_HEAD` (`models/10`) | PRESENT |
  | `DEF_CARIES_GATE` (`models/09`), `DEF_BONE_LOSS` (`models/03`) | PRESENT |
  | `run_pipeline` defaults | `caries_method=lesion-detector`, `assignment=hungarian` |

- **End-to-end smoke run inside the container** on a DENTEX `disease/` image: 28 teeth detected,
  28 distinct FDI codes, **0 duplicates**, 24 assessable, 3 caries-positive, 0 bone-loss-positive,
  and the `limitations` block emitted as designed. Stage 3 logged "caries LESION DETECTOR (whole
  image, adopted 4 Sep 2026)" — the wiring the rebuild existed to pick up.
- **Image:** 5.03 GB (the stale one was 4.4 GB, 11 days old). Note `data/` is deliberately not
  copied, so the demo needs an image mounted or uploaded; the two Drive-only checkpoints are
  baked in here because they are present on this machine.
- **Key decision or insight:** none — this is an artefact refresh, and it closes the last Tier-2
  engineering item. It changes no metric.
- **Source:** `Dockerfile`, build log; `scripts/run_inference.py`.
- **Follow-ups:** none. Re-run `docker build -t opg-demo .` after any change to a `DEF_*` default.

## 2026-09-07d — the "not reproducible" limitation is corrected in the manuscript and the four documents that carried it

- **What was done:** acted on 2026-09-07's follow-up (3). The claim that the in-domain bone-loss
  figure "is not currently reproducible" is **false** and was stated in `paper/main.tex` twice,
  plus `PAPER_MATERIAL.md` §9, `docs/paper/SUBMISSION_TODO.md` and `PROJECT_OVERVIEW.html`.
  Corrected all five to **exactly the evidence that exists**, no further.
- **The distinction the correction turns on.** Two separate claims had been bundled into one
  sentence, and only one of them is wrong:
  1. **"a selected maximum"** — best of 32 epochs, diseased-class F1 oscillating 0.40–0.85 over
     59 validation positives, so the figure is optimistically biased. **Untouched by any of this
     and still true.** It survives in every document, with its reasoning intact.
  2. **"not currently reproducible"** — rested on the crops being unavailable. **They were in the
     project Drive the whole time.** Corrected.
- **What is now claimed, and what is not.** Claimed: the crops are **retained**, and scoring the
  frozen checkpoint over the **complete diseased class** reproduces the reported figure exactly
  (**TP 49 / FN 10, sensitivity 0.8305**). Explicitly **not** claimed anywhere: the full macro-F1
  0.9233, which needs all 1,499 negatives — 934 recovered, Drive throttling the remaining 565. The
  manuscript wording says the number is *verified* while the set remains *not reconstructible*,
  which is the honest shape of it: the jitter offsets were never saved, so an independent party
  starting from source cannot recreate this exact validation set, and that limitation is kept.
- **Verification after editing:** `verify_paper_numbers.py` **127/127, no drift**; `pytest`
  **174 passed**; manuscript recompiled.
- **Key decision or insight:** the failure that produced this was not the 27 Aug analysis — that
  reasoning was correct about regeneration. It was the **compression of "cannot be regenerated"
  into "cannot be reproduced"** as the claim propagated across five documents, where it hardened
  into a blocker nobody re-tested. Rule 4's failure mode with a one-word hinge. The corrected
  wording deliberately keeps the two claims apart in every location so the same collapse cannot
  recur.
- **Source:** `paper/main.tex` (§Results, §Limitations), `docs/results/PAPER_MATERIAL.md` §9,
  `docs/paper/SUBMISSION_TODO.md`, `PROJECT_OVERVIEW.html`; evidence in `RESULTS_LOG` 2026-09-07
  and 2026-09-07b.
- **Follow-ups:** when the remaining 565 negative crops arrive, report the full macro-F1 against
  the documented 0.9233 / TN 1492 FP 7 and, if it holds, run the three §9 items this unblocks
  (calibration, PR/threshold sweep, bootstrap CIs) — each as a new entry, never by editing this one.

## 2026-10-10 — the bone-loss in-domain figure is not a held-out estimate (crop-level split, every radiograph shared with training), and its positive class is not periodontal bone loss

Found by a state-review council and recomputed by its chair
(`docs/session-memory/2026-10-10-state-review-council.md`). **No model was run and no number in
this file is re-measured.** What changes is what two existing numbers mean. Nothing is superseded
by edit: this entry qualifies 2026-04-06's 0.9233 and everything that quotes it, including
2026-08-27u, 2026-09-07 and 2026-09-07d.

- **What was done:** two read-only audits of the Stage-4a ("bone-loss binary") data, from files
  already on disk. (1) **The split** — from the crop manifests and the training notebook's saved
  output. (2) **The label** — from the Tufts expert's free-text description of every radiograph
  that supplies a positive crop.
- **Dataset / config:** the exact sets behind the reported figure. Validation 1,558 crops
  (1,499 normal / 59 diseased); training 3,211 rows (2,500 normal; 237 diseased plus 474 augmented
  copies of them). The counts match `model_metrics.md` Stage 4a and the 2,500 / 711 class ratio
  pinned in `models/README.md`.
- **Metrics — audit 1, the split:**

  | | |
  |---|---|
  | radiographs in validation / in training | 143 / 145 |
  | **validation radiographs that also supply training crops** | **143 of 143** |
  | validation crops whose tooth (radiograph + tooth title) is also in training | 543 of 1,558 (34.9%) — 46 diseased, 497 normal |
  | **validation positives whose tooth is a training positive's tooth** | **46 of 59** (78%) |
  | distinct diseased teeth in the whole build | 153 — 145 in training, 54 in validation |
  | byte-identical filenames shared | 0 |

  The cause is in the training notebook's own saved output: *"No val split found on disk;
  created a 20% validation split from train/."* `_ensure_train_val_metadata` found no `val/` and
  fell through to `train_test_split(test_size=0.2, random_state=42, stratify=label)` over crop
  rows. It is stratified by label and **not grouped by radiograph**. The shared teeth are not
  duplicate files — they are the clean crop and the ±15%-jittered crop of one tooth, landing on
  opposite sides.
- **Metrics — audit 2, the label:** a crop is labelled diseased when more than 1% of its area
  overlaps a Tufts **expert abnormality mask** (`label = 1 if overlap > OVERLAP_THRESHOLD`,
  threshold 0.01). Every diseased crop, training and validation, comes from **41 radiographs**.
  Counting words in those 41 expert descriptions (not exclusive): "apical" 26, "radiolucen" 14,
  "cyst" 9, "sclero" 9, "radiopa" 9, "impact" 4. Four contain a periodontal or alveolar word, and
  each is an apical finding: 149 (widened periodontal ligament space continuous with an apical
  radiolucency), 174 and 431 ("apical periodontitis"), 192 ("disuse alveolar atrophy" beside
  apical rarefying osteitis). One, 103, has no description. **Across all 1,000 Tufts expert
  descriptions, three describe periodontal bone loss or periodontal disease outright (205, 408,
  488) — and none of those three radiographs supplies a diseased crop.**
- **Key decision or insight:** three things this project says are not supported.
  1. **"All splits are image-level"** — `paper/main.tex` Table I caption and §Data,
     `PAPER_MATERIAL.md` §6.3, root `README.md` — **is false for the bone-loss models.** §6.3
     describes the design; the run that produced the shipped checkpoint took the fallback. The
     frozen 700/150/150 split is the detector's. The bone-loss models never used it.
  2. **0.9233 is not a held-out estimate.** It is validation on the training radiographs, with
     46 of 59 positives a sibling crop of a training positive. The 7 Sep reproduction (49/59)
     stands as a reproduction of the *measurement* and says nothing about its validity. How far
     the figure exceeds a leak-free one is unmeasured.
  3. **"Periodontal bone loss" is the wrong name for what Stage 4a was trained on.** It is a
     classifier for teeth near an expert-marked abnormality, most of them periapical. So the
     Ningxia periodontitis result (2.4% affected-tooth sensitivity) and the 0.7% DENTEX firing
     rate are what a label mismatch predicts. "Domain shift" and "does not transfer" —
     `PAPER_MATERIAL.md` §8.13, `main.tex` §Results, the bone-loss figure caption, the abstract —
     over-read them: the model is being scored on a target it was never shown. The detector-swap
     experiment (2026-08-27) still shows the cause is not upstream; it does not show the cause
     is shift.

  `verify_paper_numbers.py` passes 127 of 127 throughout. It checks that numbers match their
  artefacts, not that a split is what the text says it is.
- **Source:** `data/tufts/resampled_dataset/metadata/{train_resampled_metadata,val_metadata}.csv`;
  `notebooks/bone_loss/03_bone_loss_model_training.ipynb` (saved output of the data-loading cell,
  and `_ensure_train_val_metadata`); `notebooks/bone_loss/02_bone_loss_dataset_construction.ipynb`
  (label assignment); `_repo_archive/datasets_workspace/Expert/expert.json` on the macOS clone.
  Two council members reported the split independently; the chair recomputed every figure above.
- **What this does not establish:** the label audit is a keyword reading of free text, per
  radiograph, not a clinician's reading per mask. The size of the inflation is unknown. Stage 4b
  (severity) is built from the same crops and its split was not audited.
- **Follow-ups:** (1) **A decision for the authors and the mentor, not an engineering one:** cut
  the periodontal branch from the manuscript, or keep it re-described truthfully. Either way the
  three statements above must not reach a reviewer. (2) **Stop** the remaining 565-crop Drive
  pull and the three items 2026-09-07 called unblocked (calibration, PR sweep, CIs): they would
  characterise a validation set that shares every radiograph with training. (3) If the branch is
  kept, the one measurement worth making is a leak-free in-domain score on Tufts radiographs that
  supplied no training crop. The masks, the boxes and all 1,000 original radiographs are on the
  macOS clone. It needs its own pre-registration. (4) Untested: whether Stage 4a fires on DENTEX
  *periapical-lesion* teeth, which this audit predicts it should.

## 2026-10-11 — three pre-registered measurements for the caries tables: the constant and the gate pipeline are not separable on F1; Lever B per hospital; and the adopted detector beats the constant on the headline metric

Pre-registration `outputs/caries_intervals/PRE_REGISTRATION.md`, frozen at `1fd20b5` before any
analysis code existed; Amendment 1 at `33c1340`, committed before M3's detector arm was run.
Nothing was trained or tuned and no default changed. Items 2–5 of the implementation phase
(`transfer.md` §3).

- **What was done:** three measurements, each behind a harness gate that had to reproduce a
  published number exactly before anything new was read. **M1** — an interval on the headline
  FDI-set F1 gap between the image-blind constant and the pipeline. **M2** — Lever B against the
  constant and against the gate, per Ningxia hospital, from the saved outputs. **M3** — the
  FDI-set F1 of the adopted lesion detector, which Table I has never carried.
- **Dataset / config:** paired cluster bootstrap over images, 10,000 resamples, seed 42, 95%
  percentile interval, `bootstrap_ci.py` primitives. M1 and M3: the 164 leak-free DENTEX
  `disease/` images, 477 carious teeth, micro FDI-set F1 as `c1_vlm_baseline.score` computes it.
  M2: the three saved Ningxia files, 337 images, 1,013 lesions, paired on
  (category, split, image); **no inference, Ningxia was not re-run**. M3: `run_inference.py`
  defaults, CPU, macOS arm64, torch 2.2.0, ultralytics 8.4.127; detector confidence 0.25; the
  detector arm run once.
- **Metrics — M1, FDI-set F1 (164 images).** Gate: tp / fp / fn reproduced exactly for all four
  arms.

  | comparison | Δ F1 | 95% interval | |
  |---|---|---|---|
  | **constant − gate pipeline** (0.3197 vs 0.2936) | **+2.61 pp** | **[−0.64, +5.99]** | **includes 0** |
  | constant − Qwen2.5-VL-32B | +7.32 pp | [+3.42, +11.23] | excludes 0 |
  | constant − Qwen2.5-VL-7B | +17.04 pp | [+12.66, +21.22] | excludes 0 |
  | gate pipeline − Qwen2.5-VL-32B | +4.71 pp | [−0.22, +9.44] | includes 0 |

- **Metrics — M2, lesion agreement per Ningxia hospital.** Gate: the pooled rows reproduce the
  published +10.17 [+6.27, +14.02] and +9.28 [+5.31, +13.29] exactly. Estimation only — the
  point estimates were seen on 10 Oct, there is no bar, and the Sec 6 verdict is not reopened.

  | hospital | images | detector | constant | gate | detector − constant | detector − gate |
  |---|---|---|---|---|---|---|
  | test1 | 134 | 0.462 | 0.446 | 0.288 | +1.58 pp [−4.43, +7.74] — **includes 0** | +17.41 pp [+10.51, +24.62] |
  | test2 | 110 | 0.576 | 0.407 | 0.513 | +16.91 pp [+10.48, +23.35] | +6.30 pp [+0.28, +12.60] |
  | test3 | 40 | 0.494 | 0.377 | 0.401 | +11.73 pp [+1.29, +21.58] | +9.26 pp [−1.08, +20.00] — includes 0 |
  | test4 | 53 | 0.430 | 0.323 | 0.419 | +10.75 pp [+0.60, +20.18] | +1.08 pp [−10.50, +11.73] — includes 0 |
  | pooled | 337 | 0.500 | 0.399 | 0.408 | +10.17 pp [+6.27, +14.02] | +9.28 pp [+5.31, +13.29] |

- **Metrics — M3, the adopted lesion detector on the Table I metric (164 images, macOS).**

  | system | P | R | F1 | tp / fp / fn |
  |---|---|---|---|---|
  | image-blind constant | 0.218 | 0.600 | 0.320 | 286 / 1026 / 191 |
  | gate pipeline, same-day control on this machine | 0.242 | 0.396 | 0.300 | 189 / 593 / 288 |
  | **lesion-detector pipeline (the default since 4 Sep)** | **0.353** | **0.403** | **0.376** | 192 / 352 / 285 |

  **Detector − constant: +5.64 pp [+1.74, +9.47], excludes 0.** Detector − gate control:
  +7.59 pp [+4.47, +10.70], excludes 0. The detector flags 544 teeth where the constant names
  1,312; it wins on precision and loses on recall.
- **The M3 control missed its tolerance, and what that turned out to be.** The pre-registration
  gated the same-machine gate control at ±0.005 of the published F1 0.2936. It scored 0.3002
  (189 / 593 / 288 against 186 / 604 / 291): 126 of 164 images identical, 52 codes different.
  The run stopped there, before the detector arm, as §8 required. The pipeline code as of
  `322f787` (30 Aug) was then run on the same machine and gave **identical predictions on all
  164 images**. So no code change since August — the Lever B wiring and the Lever C refactor
  included — moved the gate path, and the 0.0066 is a difference between the Windows machine
  that produced the published file and this one. The tolerance had tested the wrong thing.
  Amendment 1 replaced it with the same-machine identity check and recorded the drift; it was
  approved and committed with only control numbers known.
- **Leakage, re-checked for M3 rather than assumed.** None of the 164 images is byte-identical
  to any of the 705 `quadrant-enumeration-disease` images the detector's DENTEX training set was
  drawn from. On a 256-bit perceptual hash, each scored image's nearest training image is as far
  away as training images are from each other (minimum 37, median 61 bits in both directions;
  the one known duplicate, already excluded, scores 0). The two closest pairs were looked at and
  are different patients.
- **Key decision or insight:**
  1. **"The constant scored highest" does not survive its interval against our own pipeline.**
     By the rule fixed in advance, the manuscript must say the constant and the gate pipeline are
     *not separable* on FDI-set F1. The constant does separate from both vision–language models.
     The paper's argument — a system that an image-blind constant cannot be told apart from has
     not shown it reads the image — is unchanged, and is arguably stated more exactly this way.
  2. **Lever B's external result is real pooled, and uneven by hospital.** It is separated from
     the constant at test2, test3 and test4 and not at test1, where the constant is strongest.
     "It replicates on the one cohort that is genuinely external" is a pooled statement and has
     to be written as one, beside this table. The manuscript recommends exactly this of others.
  3. **The adopted detector beats the image-blind constant on the paper's own headline metric.**
     No system in this project had done that on FDI-set F1. Three limits belong with it: DENTEX
     is *development* data for this detector (a corpus it trained on, scored on held-out
     images); it is one training run; and it is measured on one machine. It does not contradict
     the tie on lesion agreement on the same images (0.455 vs 0.489) — that metric is
     recall-shaped and F1 pays for precision — but the two must be reported together.
  4. **A cross-machine difference of 0.0066 F1 exists in a published row.** Table I's gate row
     is 0.2936 from one machine and 0.3002 from another, with identical code.
- **Source:** `outputs/caries_intervals/caries_intervals.json` (every number above);
  `arm_pipeline_gate_control.json`, `arm_pipeline_lesion_detector.json`,
  `arm_pipeline_gate_code322f787.json` and `repro_old_code_gate_run.py` in the same directory;
  `scripts/eval/caries_intervals.py`; `scripts/eval/c1_vlm_baseline.py` (the pipeline arm gained
  `--caries-method`, defaulting to the gate, and now forces CPU).
- **Follow-ups:** (1) Manuscript changes for the authors, not made here: reword "outscored" in
  the abstract, Table I text and Conclusion; add the detector row to Table I, labelled as
  development data and as measured on macOS; add the per-hospital table to the Lever B
  subsection and qualify "replicates" as pooled. (2) A thesis-level call for the authors: with
  M3, the paper's own system now clears the floor the paper is about. (3) Decide whether Table I
  restates both pipeline rows from one machine. (4) Until this session a bare
  `c1_vlm_baseline.py --arm pipeline` would have run the lesion detector and overwritten the
  published `arm_pipeline.json`; that default is fixed.

## 2026-10-11b — the report and the demo stop calling Stage 4 a periodontal finding (report schema 1.2)

Item 6 of the implementation phase (`transfer.md` §3). It acts on 2026-10-10: the pipeline's own
output was still repeating the reading that entry withdrew.

- **What was done:** changed what the shipped system *says* about Stage 4, and nothing about
  what it computes. In `scripts/run_inference.py`: every report's `limitations` block gains
  `bone_loss_label_and_validation` (the field is an abnormality-proximity flag, not a
  periodontal finding; the in-domain score is not held out); the text of the existing
  `bone_loss_domain_shift` key no longer asserts domain shift as the cause; `models.bone_loss`
  gains `label_definition` and `validation_split`; the overlay prints `ABN-…` where it printed
  `BL-…`; the console summary says "stage-4 abnormality flags". In `app.py`: the metric and the
  table column are relabelled, and the Limitations panel renders the two Stage-4 caveats — it
  rendered none before, beside a column headed "Bone loss". Report schema `opg-report/1.1` →
  **1.2**, additive.
- **Dataset / config:** no model, weight, threshold or default changed. Field names
  (`bone_loss`, `bone_loss_positive`, the `"bone_loss"` finding value) are deliberately kept: a
  rename breaks `tests/test_classifiers.py` and `scripts/eval/ningxia_external.py`.
- **Metrics — verification, not a result.** The previous commit's code and the changed code
  were run on the same Tufts radiograph (196): the `teeth` list and the `summary` are identical;
  one `limitations` key added, none removed; two `models.bone_loss` keys added. The app was
  driven headlessly through an upload (Streamlit `AppTest`): no exception before or after; the
  metric reads "Stage-4 flags 5"; the table column reads "Stage 4 flag" (5 flagged, 26 not);
  both caveats render. `pytest` 174 passed; `verify_paper_numbers.py` 127 of 127;
  `verify_invariants.py` holds, including one new invariant.
- **Key decision or insight:** on that radiograph the five flagged teeth are 17, 18, 27, 28 and
  48 — second and third molars. The Tufts expert's description of the same radiograph is a
  widened follicular space at three third molars (hyperplastic follicle or dentigerous cyst).
  That is the label audit of 2026-10-10 seen in one image: the flags sit on and beside teeth the
  expert marked for a follicular abnormality, not along the bone ridge. Radiograph 196 is one of
  Stage 4a's own training images, so this shows what the label is and says nothing about
  generalisation. A new invariant, "Stage-4 report wording", asserts that the caveat is in
  every report and is rendered by the app; it fails on the previous commit, as intended.
- **Source:** `scripts/run_inference.py`, `app.py`, `src/classifiers.py` (docstring only),
  `scripts/eval/verify_invariants.py`.
- **Follow-ups:** (1) **The Docker image built on 7 Sep carries the old wording** and must be
  rebuilt on the machine that has Docker running. A stale container is now detectable: it emits
  `opg-report/1.1`. (2) Saved demo reports under `outputs/` from before today carry the old
  caveat; they are history, not regenerated. (3) Noticed and left alone: the report's
  `interpretation` text says "roughly half the codes" will be wrong where the measured figure is
  42%; and the app's "Caries conf (cal.)" column is always empty under the default caries
  method, because that confidence belongs to the retained gate.

## 2026-10-11c — what limits end-to-end FDI, decomposed from saved rows; and the ceiling the front end puts on caries recall

A diagnostic, not a run. No model was executed and nothing changed. The numbers come from
per-tooth rows already saved and tracked; a council asked "how do we fix end-to-end FDI" and
these are the facts its verdict rests on (`docs/session-memory/2026-10-11d-fdi-and-lagging-metrics-council.md`).

- **What was done:** joined the saved Stage-2 rows of the deployed detector and of the Lever A
  multi-corpus detector (arm3c) on the same 936 DENTEX teeth, same numbering head, and counted.
- **Dataset / config:** 164 leak-free DENTEX images, 936 annotated teeth, of which 477 carious.
  `outputs/stage2_segdet/stage2_rows_head.json` (deployed, `models/11`) and
  `outputs/lever_A_multicorpus_detector_v2/arm3c/stage2_rows_head.json` (`models/15` arm3c).
- **Metrics — where the 41.7% goes (DENTEX, deployed detector):**

  | | teeth | of 936 |
  |---|---|---|
  | correct code | 546 | 58.3% |
  | never detected | 275 | 29.4% |
  | detected, wrong code | 115 | 12.3% |

  On the **660 teeth both detectors find**, the same head gives 115 wrong codes from the
  deployed detector's boxes and **41** from arm3c's. So roughly two thirds of the "numbering"
  errors are also the detector's. The misses are concentrated by image, not by tooth: the worst
  quarter of images (41) holds 168 of the 275, and 50 images have none.
- **Metrics — the ceiling this puts on the caries headline:** a flagged lesion only scores on
  FDI-set F1 if its tooth is detected and numbered correctly.

  | front end | carious teeth detected and correctly numbered | recall ceiling |
  |---|---|---|
  | deployed detector + head | 288 of 477 | **0.604** |
  | arm3c detector + same head | 453 of 477 | **0.950** |

  The lesion-detector pipeline's measured recall is 0.403 (192 of 477, 2026-10-11). Of its 285
  false negatives, 189 are teeth the front end never delivers under the right code.
- **Key decision or insight:** on DENTEX, end-to-end FDI is bound by a Tufts-only tooth detector
  losing whole radiographs, and the same loss caps the caries score. The fix that is known to
  work — a multi-corpus detector — already exists and was recorded as an ablation on 1 and 3 Sep
  because it failed its pre-registered Tufts box-mAP guard. The council's verdict: **the default
  does not change now** (3 of 3); see the session file for what is parked and why. The
  caries-recall ceiling is new, and it is the reason one measurement — the lesion detector on
  the arm3c front end, DENTEX only, default unchanged — is the single piece of Stage-1 work the
  council thought worth doing for the paper.
- **Source:** the two row files above; `outputs/caries_intervals/caries_intervals.json` for the
  0.403. Counted by the session chair after a council member reported them.
- **Follow-ups:** (1) Reported by a member and **not** re-derived by the chair: on Tufts,
  of-detected accuracy falls with the number of surplus boxes per image, identically for both
  detectors, because the one-to-one assignment has no way to reject a box; and at detector
  confidence 0.10 a tenth of detected teeth receive no code at all. If that holds, a reject
  option is the cheap Tufts lever, and the earlier "conf 0.25 is near-optimal" reading
  (2026-09-04d) measured the 32-code cap rather than the detector. (2) The saved Tufts summary
  says 143 images where the log says 149; untraced. (3) `run_inference.py --detector` stamps
  the default detector's tag and its 70.6% / 58.3% constants into the report whatever weights
  are loaded.

## 2026-10-11d — before the Stage-1 switch: the multi-corpus detector's hold-out re-checked, and the Tufts cohort is 143 images, not 149

Checks made while planning a change of the default tooth detector
(`docs/session-memory/2026-10-11e-detector-switch-plan-council.md`). No model was run.

- **What was done:** (1) re-checked that the 164 scored DENTEX images are held out from the
  Lever A arm3c detector's training data, by content rather than by filename; (2) traced a
  discrepancy in the Tufts end-to-end cohort size.
- **Dataset / config:** the 164 leak-free `disease/` images against arm3c's 634 DENTEX
  `quadrant_enumeration` source images and its 500 Kaggle images; MD5 and a 256-bit difference
  hash. Tufts: `split_v1.csv` test rows against `outputs/stage2_tufts/stage2_per_image_head.json`.
- **Metrics:**
  - *Hold-out.* No scored image is byte-identical to any training-source image. Nearest
    training image by perceptual hash, DENTEX: minimum 42 bits, median 63; training images
    among themselves: 5th percentile 45, median 59. Kaggle: minimum 55, median 77. No sign of a
    near-duplicate.
  - *Tufts cohort.* 150 test images − 1 train duplicate (`590`) − 6 with no tooth annotations
    (`118`, `339`, `417`, `501`, `528`, `974`) = **143 scored images**, 3,760 teeth.
  - *Hashes.* arm3c on disk is `5d301f13fb48da5c74e7ef01bd0f91226f9b6800cb433dee5aebc8f8db8f161e`;
    `models/15_detector_multicorpus_leverA/run_summary.txt` records only `5d301f13...`, which
    the invariant script cannot pin.
- **Key decision or insight:** 2026-09-04d and every document quoting it said "149 frozen-test
  images". **That count was wrong; every score computed on the cohort is unaffected** (the
  teeth, 3,760, were always right). Corrected in `model_metrics.md`, `README.md` and
  `transfer.md`; 2026-09-04d is left as written. The hold-out result means arm3c's 92.8% on
  DENTEX is an in-domain number on genuinely unseen images, as it was always labelled.
- **Source:** the files named above; counted in-session.
- **Follow-ups:** arm3c was trained partly on the Kaggle "dual-labeled" set, whose licence its
  authors do not state (`data/README.md`, `paper/main.tex`). That was acceptable for an ablation
  and has to be resolved or disclosed before a detector trained on it ships as the default.

## 2026-10-11e — a report could carry one detector's name and accuracy over another detector's boxes; fixed ahead of the Stage-1 switch (report schema 1.3)

Phase 1 of the plan in `docs/session-memory/2026-10-11e-detector-switch-plan-council.md`. The
default detector is unchanged by this entry.

- **What was done:** `scripts/run_inference.py` stamped a detector tag and two accuracy figures
  (recall 70.6%, end-to-end FDI 58.3%) into every report from module constants. Running it with
  `--detector` set to any other checkpoint produced a report naming the default detector and
  quoting its accuracy. The tag and both figures are now looked up by the sha256 of the weights
  actually loaded (`DETECTOR_PROFILES`); a detector with no entry is tagged `unregistered-<sha>`
  and its two figures are null. `models.detector` gains `sha256`. Schema 1.2 → **1.3**.
- **Also changed, so the planned re-measurement leaves a clean trail:**
  `scripts/eval/c1_vlm_baseline.py` takes `--detector` (default pinned to `models/11`, the
  detector the published arm used) and records the detector and its hash;
  `scripts/eval/cariesxrays_external.py` and `scripts/eval/validate_fdi_assignment.py` record
  which detector produced their output; `scripts/count_model_params.py` takes `--stage1` and
  `--out` and refuses to write a non-default count over the published file.
- **Hash pins:** `models/15_detector_multicorpus_leverA/run_summary.txt` now carries the full
  sha256 of its three checkpoints (it held 8-character prefixes); `verify_invariants.py` pins
  arm3c, and **fails** where it used to print "NO HASH RECORDED" and pass. A new invariant
  requires whatever `DEF_DETECTOR` is to have a profile with measured figures.
- **Dataset / config:** no model, weight, threshold or default changed.
- **Metrics — verification, not a result.** The previous commit's code and this code, default
  detector, on one Tufts and one DENTEX image: `teeth`, `summary` and `limitations` identical;
  the only differences are `schema_version`, the new `sha256` key and the timestamp. With
  arm3c passed explicitly, on a Tufts *training* image: tag `unregistered-5d301f13`, both
  figures null, and the report says no accuracy has been measured for that detector. `pytest`
  174 passed; `verify_paper_numbers.py` 127 of 127; all invariants hold.
- **Key decision or insight:** this had to land before the default changes, not with it. Had
  the default been switched first, every report from the new detector would have claimed the
  old one's 70.6% / 58.3% until someone remembered to edit two constants.
- **Source:** the files named above.
- **Follow-ups:** `count_model_params.py` rewrites `param_counts.json` with LF line endings on
  macOS where the committed file is CRLF — content identical, but it shows as modified; pass
  `--out` when counting anything on this machine. arm3c counts 25,311,251 learnable parameters.

## 2026-10-11f — DECISION RECORD: the Lever A multi-corpus detector (arm3c) is to become the Stage-1 default, overriding two pre-registered ABLATION verdicts

**This entry records a decision. It reports no new number, and at the time of writing nothing
has been run and `DEF_DETECTOR` is still `models/11`.** The re-measurement is pre-registered in
`outputs/stage1_switch/PRE_REGISTRATION.md`, committed with this entry and before any of it runs.

- **What was decided, and by whom:** on 11 Oct 2026 Gunadeep (gunadeep19) decided that
  `models/15_detector_multicorpus_leverA/arm3c_best.pt` (sha256 `5d301f13…8f161e`) will replace
  `models/11_yolo_seg_tufts_r1/best.pt` as the pipeline's Stage-1 tooth detector, in order to
  fix end-to-end FDI on DENTEX.
- **The two verdicts this overrides stand exactly as recorded.** Lever 1 (2026-09-01h): primary
  passed, guard failed — Tufts test box mAP@0.5 0.647 against a bar of 0.75. Lever A
  (2026-09-03, -03b): primary and Guard 1 passed, Guard 2 failed — 0.585 against 0.684. Both
  pre-registrations say what follows a failed guard: "the pipeline default does not change"
  (`outputs/detector_multicorpus/PRE_REGISTRATION.md`,
  `outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md`). **Neither bar has been moved
  and neither guard is claimed to have been met.** This is a later human decision to change the
  default anyway, and it is recorded as that.
- **It is a stronger override than the one of 27 Aug 2026.** Then, the seg detector was adopted
  against a missed *mask* bar, and the thing the bar protected — mask-aware cropping — was left
  unwired. Here the rules named the default itself.
- **Who advised against, and who was not asked.** A council on the morning of 11 Oct advised
  against changing the default, three seats of three
  (`docs/session-memory/2026-10-11d-fdi-and-lagging-metrics-council.md`). The repo owner and the
  mentor were not consulted before this entry was written.
- **Reasons the decision rests on.** The registered primary passed twice, by a wide margin
  (+34.9 pp and +34.4 pp end-to-end FDI on the 164 held-out DENTEX images). The saved-row
  decomposition of 2026-10-11c shows that on DENTEX both the numbering loss and the ceiling on
  caries recall come from the Tufts-only detector. And a judgement: that Tufts box mAP at IoU
  0.5 is worth giving up for that.
- **What is *not* offered as a reason.** The Tufts end-to-end figures (64.8% → 63.5%,
  2026-09-04d) were measured after both verdicts, carry no interval and were part of neither
  rule; they are reported, never as "the guard satisfied". The +19 pp on Ningxia with the
  retired gate was a no-regression guard on locked data, not a selection criterion — but it
  **was known when this decision was made**, and Ningxia is therefore no longer blind to the
  choice of Stage-1 detector. This morning's three pre-registered measurements were made to word
  three sentences, not to choose a detector.
- **What is given up.** Tufts test box mAP@0.5 0.810 → 0.585. Instance masks: arm3c is a
  detect model, so mask-aware cropping is not merely unwired but unavailable. The cross-domain
  numbering figure: 58.3% was a Tufts-trained detector on DENTEX; arm3c's 92.8% is in-domain.
  Continuity with every pipeline number measured between 27 Aug and 11 Oct, including Lever B's
  adoption and this morning's intervals, all of which used `models/11`.
- **Why arm3c and not another checkpoint.** It was named the primary arm in Lever A's
  pre-registration before any arm trained. For the record: the Lever 1 arm (`models/13`) scores
  higher on both detector metrics already seen (DENTEX 93.4%, Tufts box mAP 0.647), and the
  decision to switch at all was taken with outcomes in view.
- **Open, and disclosed rather than settled:** arm3c was trained partly on the Kaggle
  "dual-labeled" set, whose authors state no licence. If that cannot be cleared before
  submission, the remedy is a detector trained without it — a new decision with its own record.
- **Consequences enforced in code** (2026-10-11e, already in place): a report's detector tag
  and accuracy follow the weights loaded; `models/11` stays selectable and hash-pinned, so every
  number published to date remains reproducible; the default cannot change without measured
  figures of its own.
- **Source:** the two pre-registrations named above; 2026-09-01h, 2026-09-03, 2026-09-03b,
  2026-09-04d, 2026-10-11c, 2026-10-11d in this file.
- **Follow-ups:** run the pre-registered matrix; apply its one reversal rule; only then change
  the default. Lever B's verdict and this morning's measurements are not re-opened — they are
  relabelled "previous front end" wherever they are quoted beside the new numbers.

## 2026-10-11g — the pipeline re-measured under the multi-corpus tooth detector (arm3c), and the Stage-1 default changed to it

The re-measurement that the decision record (2026-10-11f) said would come before the default
moved. Pre-registered in `outputs/stage1_switch/PRE_REGISTRATION.md`, frozen at `c139779` before
any run; Amendment 1 at `85df6ff`, before any Ningxia run. **This entry does not show that the
switch was right. That was a person's decision, taken with outcomes in view, against two
pre-registered verdicts that still stand. It reports what the pipeline measures under the new
front end, and that the one result registered to stop the switch did not occur.**

- **What was done:** every pipeline-level number was run twice on the macOS clone — the previous
  detector `models/11` first, as a same-machine control, then
  `models/15_detector_multicorpus_leverA/arm3c_best.pt` — 32 runs over eight rows, each into
  its own directory under `outputs/stage1_switch/`. Each control was checked against its gate
  before the arm3c files of that row were opened. Every difference between detectors below is
  against the same-machine control, by paired cluster bootstrap over images (10,000 resamples,
  seed 42, 95% percentile interval). Then `DEF_DETECTOR` was changed.
- **Dataset / config:** nothing tuned. FDI head `models/10`, lesion detector `models/16`, gate
  `models/09`, detector confidence 0.25, image size 1024, NMS IoU 0.50, lesion confidence 0.25,
  one-to-one assignment — all as before. torch 2.2.0, ultralytics 8.4.127. Both detectors ran on
  CPU; the classifier heads ran on MPS for rows A, B, C, F and G and on CPU for rows D and E,
  which is what each script has always done on this machine.
- **Control gates — all eight passed.**

  | Row | Control must give | Control gave |
  |---|---|---|
  | A Tufts numbering | 2,438 of 3,760 on 143 images, exact | 2,438 |
  | B DENTEX numbering | 547 of 936 on 164 images, exact | 547 |
  | C DENTEX lesion agreement | 479 lesions; other machine 212 / 234 / 218 | 479; 215 / 235 / 219 (largest gap +0.63 pp) |
  | D FDI-set F1 | this morning's prediction sets, exact | identical, both caries methods |
  | E CariesXrays 1,200 | 1,200 images, 2,815 lesions; other machine 892 / 1,582 / 1,926 | 1,200; 2,815; 895 / 1,583 / 1,921 (largest gap −0.18 pp) |
  | F Ningxia caries | 1,013 lesions; gate 412 exact; other machine 404 / 507 | 1,013; 412; 404 / 506 |
  | G Ningxia Stage 4 (amended) | 736 images; other machine 6,791 affected, 165 flagged | 736; 6,792; 165 |
  | H parameters | 27,617,459 and 97,649,753 | both |

- **Metrics — tooth numbering.** Recall, accuracy on detected teeth, end to end.

  | Cohort | Detector | Recall | Of detected | End to end | 95% CI |
  |---|---|---|---|---|---|
  | Tufts test, 143 images, 3,760 teeth | previous | 82.4% | 78.6% | **64.8%** (2,438) | [60.44, 69.13] |
  | | arm3c | 89.3% | 71.1% | **63.5%** (2,389) | [59.34, 67.50] |
  | DENTEX, 164 images, 936 teeth | previous — **cross-domain** | 70.8% | 82.5% | **58.4%** (547) | [53.83, 63.05] |
  | | arm3c — **in-domain** | 99.6% | 93.2% | **92.8%** (869) | [90.63, 94.87] |

  - *Tufts:* end to end −1.30 pp [−4.64, +2.26]. **Not separable on Tufts.** Under that sits a
    real trade: recall +6.89 pp [+4.94, +9.00], accuracy on detected teeth −7.52 pp
    [−10.79, −4.16]. arm3c finds more teeth and numbers them worse. This is not evidence that
    either earlier guard was met; both were box-mAP guards and both failed.
  - *DENTEX:* +34.40 pp [+30.29, +38.54]. The 164 images are held out from arm3c's training
    data (2026-10-11d) but DENTEX is one of its training corpora, so 92.8% is an **in-domain**
    figure. The previous detector's 58.4% on this machine (58.3% as published, from the other
    machine) was a Tufts-only detector on DENTEX and stays as the cross-domain reference. With
    arm3c the pipeline has **no cross-domain numbering figure at all**: both cohorts with tooth
    labels are in its training distribution.
  - *Teeth matched to a detection but given no code,* because the one-to-one assignment stops
    at 32 boxes: Tufts 26 → 65; DENTEX 0 → 0. Mean boxes per image: Tufts 24.3 → 27.8, DENTEX
    22.0 → 27.5.

- **Metrics — caries, lesion agreement.** Lesions landing on a flagged tooth, with the number
  of teeth each arm flagged beside it, because agreement rises with flagged area.

  | Cohort | Front end | Retired gate | Image-blind constant | Lesion detector (default) |
  |---|---|---|---|---|
  | DENTEX, 479 lesions | previous | 0.449 (751 flagged) | 0.491 (857) | 0.457 (526) |
  | | arm3c | 0.802 (1,439) | 0.630 (988) | 0.595 (603) |
  | CariesXrays, 2,815 lesions | previous | 0.318 (4,776) | 0.562 (7,717) | 0.682 (2,351) |
  | | arm3c | 0.379 (5,808) | 0.604 (8,457) | 0.757 (2,596) |
  | Ningxia, 1,013 lesions | previous | 0.407 (2,109) | 0.399 (1,941) | 0.499 (1,287) |
  | | arm3c | 0.600 (3,104) | 0.591 (2,410) | 0.684 (1,465) |

  *The lesion detector, arm3c minus the control:* DENTEX +13.78 pp [+9.84, +17.93];
  CariesXrays +7.50 pp [+5.63, +9.41]; Ningxia +18.46 pp [+15.26, +21.78]. The constant rises
  by about as much on every cohort (+13.99, +4.12, +19.25), because in this metric the constant
  is placed with the pipeline's own boxes and codes. **Most of the rise is the front end
  finding and numbering more teeth, for every arm alike; it is not the caries model reading
  lesions better.** On DENTEX, flagging every detected tooth scores 0.722 → 0.998.

  *Lever B's comparison, recomputed under arm3c — a description, not a re-decision.* Lever B's
  verdict of 4 Sep stands for the front end it was scored on.

  | Cohort | Lesion detector − constant | Lesion detector − retired gate |
  |---|---|---|
  | DENTEX | −3.55 pp [−10.11, +2.64], not separated | **−20.67 pp [−26.39, −15.06]**, the gate is higher |
  | CariesXrays | +15.38 pp [+12.96, +17.73] | +37.80 pp [+35.29, +40.30] |
  | Ningxia | +9.28 pp [+4.72, +13.73] | +8.39 pp [+4.06, +12.67] |

  Against the constant the pattern is the one Lever B was adopted on: separated on the two
  external cohorts, not on DENTEX (previous front end, this machine: −3.34 pp [−8.33, +1.39],
  +12.01 pp, +10.07 pp). **One thing is new and unfavourable: on DENTEX under arm3c the retired
  gate scores above the lesion detector, 0.802 against 0.595, interval excluding zero.** It
  does so while flagging 1,439 teeth to the detector's 603, and under the previous front end
  the two were tied (+0.84 pp [−3.73, +5.30]). On the metric with a false-positive cost, below,
  the order is the other way round.

  *Ningxia per hospital, under arm3c, lesion detector − constant:* test1 −3.16 pp
  [−10.56, +3.97], not separated here; test2 +16.91 pp [+9.17, +24.62], separated; test3
  +11.73 pp [+1.07, +21.34], separated; test4 +13.98 pp [+2.34, +24.34], separated. Lesion
  detector − gate: test1 +15.82 pp [+7.80, +23.80], separated; test2 +4.58 pp [−2.43, +11.63],
  not separated here; test3 +9.88 pp [+0.74, +19.20], separated; test4 +1.61 pp
  [−10.80, +13.43], not separated here. 134, 110, 40 and 53 images. The same hospitals fail to
  separate as under the previous front end, with one change: test3 against the gate now does.

- **Metrics — caries, FDI-set F1** (164 DENTEX images, 477 carious teeth; this metric charges
  for false positives). The image-blind constant is fixed whatever the detector: tp/fp/fn
  286 / 1,026 / 191, F1 0.320.

  | Caries path | Front end | P | R | F1 | tp / fp / fn | s per image, CPU |
  |---|---|---|---|---|---|---|
  | Lesion detector (default) | previous | 0.353 | 0.403 | 0.376 | 192 / 352 / 285 | 1.45 |
  | | arm3c | 0.439 | 0.574 | **0.498** | 274 / 350 / 203 | 1.70 |
  | Retired gate | previous | 0.242 | 0.396 | 0.300 | 189 / 593 / 288 | 1.74 |
  | | arm3c | 0.238 | 0.765 | 0.363 | 365 / 1,172 / 112 | 2.11 |

  Lesion-detector pipeline: arm3c − constant **+17.80 pp [+13.48, +22.02]**, separated; arm3c −
  control +12.16 pp [+8.86, +15.52], separated. Gate pipeline: arm3c − constant +4.27 pp
  [+1.58, +7.05], separated; arm3c − control +6.22 pp [+3.31, +9.18], separated. With arm3c the
  lesion detector's 82 extra true positives come with two fewer false positives; the gate's 176
  come with 579 more. DENTEX is in-domain for arm3c, so these are in-domain figures for the
  front end.

- **Metrics — Stage 4, the abnormality-proximity flag, Ningxia periodontitis, 736 images.**
  165 of 6,792 affected teeth flagged (2.43% [1.99, 2.88]) → 153 of 7,049 (2.17%
  [1.75, 2.62]); −0.26 pp [−0.74, +0.23], not separable. An affected tooth is a detected box,
  so the two rates are over each detector's own affected teeth, not the same teeth. Stage 4
  remains a flag that almost never fires on this cohort and is not a periodontal finding
  (2026-10-10).
- **Metrics — size.** Stage 1: 27,617,459 → 25,311,251 learnable parameters. Whole default
  pipeline: 97,649,753 → **95,343,545**; caries path 75,294,164 → 72,987,956.
- **The one registered stop, S1.** Lesion-detector path, lesion agreement, arm3c − control,
  pooled over the 337 Ningxia caries images and the 1,200 CariesXrays images: **+10.40 pp
  [+8.71, +12.09]**. The rule was a lower bound below −2 pp. **S1 does not fire.** That is the
  caries result not being harmed, on a comparison in which the locked cohort was used as a
  veto. It is not validation of the detector.
- **Key decision or insight:** `DEF_DETECTOR` is now arm3c. Its `DETECTOR_PROFILES` entry
  carries row B's figures from this machine — recall 99.6% (932 of 936), end to end 92.8%
  (869) — and says in every report that DENTEX is in-domain, that Tufts is 89.3% / 63.5%, and
  that no figure exists for a source the detector was not trained on. The console note no
  longer turns that figure into "about 7% of codes are expected wrong". `models/11` is
  unchanged, hash-pinned and selectable with `--detector`. The FDI-set F1 harness and
  `count_model_params.py` keep `models/11` as their own default, because both reproduce
  published numbers. **Every result recorded before this entry — Lever B's adoption, this
  morning's three measurements, every table in `paper/main.tex` — belongs to the previous front
  end and is not superseded as a record; it is superseded as a description of the default.**
- **Disclosures the pre-registration requires.**
  - *The repo owner was not told* before the Ningxia rows ran. The decision owner confirmed
    this on 11 Oct and chose to run.
  - *Ningxia is not blind to this choice.* The default was chosen after this detector's
    gate-path Ningxia result (0.407 → 0.600) was known. By saved outputs the caries images have
    now been scored in 20 full passes, six of them here, and the periodontitis images in six,
    two of them here, besides one 24-image smoke test. Under arm3c: four caries passes, one
    periodontitis pass. Nothing was fitted, tuned or selected on Ningxia in this matrix.
  - *Amendment 1.* Row G's frozen gate demanded exactly 6,791 affected teeth. That count is a
    property of detected boxes and came from the other machine. Found by reading the code after
    rows A, B and H had been read, while row D was running, and before any Ningxia run; the
    gate became 736 images exact with the counts held to 1.5%. The control then gave 6,792, so the frozen gate would have failed by
    one tooth.
  - *One stop, caused by the analysis script.* Its first gate for row C compared the 148
    per-image rows (`lesion_localization.py` lists only images carrying a caries lesion)
    with the cohort's 164 images and stopped. The control files themselves report 164 images
    and 479 lesions. The gate was changed to read each file's own image count before any arm3c
    file of row C was opened.
  - *Seen before the matrix,* and so not a prediction of it: arm3c's numbering on both
    cohorts, its gate-path lesion agreement on Ningxia and on a 1,500-image CariesXrays sample,
    and the 0.604 → 0.950 ceiling on DENTEX caries recall. New here: the lesion detector with
    arm3c on any cohort, the constant under arm3c, FDI-set F1 under arm3c, every interval.
- **What this does not establish.** That arm3c generalises: both numbering cohorts are
  in-domain for it. That the Tufts cost is zero: the interval reaches −4.64 pp. That the
  caries model improved: the constant moved with it. That Lever B would be adopted afresh
  under this front end: its rule was not re-run and is not claimed.
- **Source:** `outputs/stage1_switch/stage1_switch_results.json` (every figure above) and
  `stage1_switch_results.log`; the 32 run directories beside them, each with its `stdout.log`;
  `outputs/stage1_switch/run_matrix.sh` (every command); `scripts/eval/stage1_switch_intervals.py`
  (gates and intervals). Verified after the change: `pytest tests` 174 passed;
  `verify_paper_numbers.py` 127 of 127; all eleven invariants hold, the default-detector one now
  reading the new profile; a default run and a `--detector models/11` run on one DENTEX image
  each reproduce their row D caries codes and carry their own tag and figures.
- **Follow-ups:** (1) `paper/main.tex` still describes `models/11` throughout and cannot be
  rebuilt on this machine; until it is, the manuscript and the pipeline default disagree.
  (2) The Docker image predates the change. (3) `outputs/param_counts/param_counts.json` is
  still the previous front end's count, because `verify_paper_numbers.py` asserts the
  manuscript against it; it moves with the manuscript. (4) The Kaggle "dual-labeled" licence is
  still unstated, and arm3c was trained on that set. (5) The repo owner and the mentor have not
  been consulted on any of this. (6) arm3c's weights (51 MB) are whitelisted in `.gitignore`
  and not yet committed. (7) Not done, and not registered: a Tufts box-mAP re-measurement — the
  guard figures of 1 and 3 Sep are unchanged — and any reject option for surplus boxes, which
  the 26 → 65 uncoded Tufts teeth make more pressing.

## 2026-10-11h — the Stage-1 switch verified after it was pushed; three figures in 2026-10-11g were mis-rounded by one digit

A verification pass over 2026-10-11g, made after the switch was committed and pushed
(`7dd3ff4`). **No model was run on any cohort, no count, difference, interval or reading
changes, and the default detector is as 2026-10-11g left it.** Three printed figures were wrong
in the third decimal and are corrected here.

- **What was done:** (1) checked out the pushed commit into a clean directory holding tracked
  files only, and ran the pipeline and the checks from it; (2) re-derived every count, point
  difference and interval of 2026-10-11g with a second implementation that shares no loader,
  pairing or bootstrap code with `scripts/eval/stage1_switch_intervals.py`; (3) audited every
  figure written into the documents against the results file and against exact arithmetic on
  the integer counts.
- **Dataset / config:** the 32 committed run directories under `outputs/stage1_switch/`. The
  only inference was one DENTEX image through the default pipeline, as a smoke test.
- **Metrics — the pushed commit, tracked files only.**
  - The blob in git for `models/15_detector_multicorpus_leverA/arm3c_best.pt` is 51,227,097
    bytes, sha256 `5d301f13…8f161e`, the pinned hash. It is the file, not a pointer.
  - `run_inference.py` with no `--detector` loads it and reports
    `tooth-detector-multicorpus-1024-v1.0`, recall 0.996, end to end 0.928, schema 1.3. Its
    caries codes for `test_0` equal row D's for arm3c.
  - `pytest tests` 174 passed; `verify_paper_numbers.py` 127 of 127; all eleven invariants
    hold, the two that need local datasets skipping as they are written to.
  - `stage1_switch_intervals.py`, run there, rewrites `stage1_switch_results.json` **byte for
    byte**.
- **Metrics — independent re-derivation: 164 comparisons, all agree.** Every count equals the
  results file, including each producing script's own totals against the sum of its per-image
  rows. Every point difference agrees to 0.01 pp. The 66 interval bounds, bootstrapped with a
  different seed, agree within 0.24 pp. Replaying seed 42 draw for draw reproduces the DENTEX
  numbering interval exactly, [+30.29, +38.54]. The stop rule, independently: +10.40 pp, lower
  bound +8.70 against the registered +8.71; it does not fire.
- **Metrics — how precise a registered interval is.** The pre-registered 10,000 resamples
  leave Monte Carlo noise in each bound. For the DENTEX numbering difference, 30 seeds put the
  lower bound at 30.43 ± 0.06 (30.32 to 30.57) and 400,000 resamples give [+30.42, +38.47]; the
  registered seed-42 interval is about 0.1 pp wider at each end. **No reading in 2026-10-11g
  turns on that.** The three bounds nearest zero keep their side across 30 seeds: Ningxia test3
  under arm3c, lesion detector − gate, lower +0.56 to +1.15 (registered +0.74, 40 images — the
  thinnest "separated" in the entry); test2 under the previous front end, lower −0.85 to −0.53;
  the Stage-4 flag-rate difference, upper +0.21 to +0.23.
- **Correction to 2026-10-11g — three figures, each one unit in the third decimal.** The
  results file stores four decimals; I rounded those to three by hand, which rounds twice.
  Recomputed exactly from the counts, 73 figures; three differ from what was printed:

  | Where in 2026-10-11g | Printed | Correct | From |
  |---|---|---|---|
  | F1 table, retired gate under arm3c, precision | 0.238 | **0.237** | 365 / 1,537 = 0.23748 |
  | F1 table, retired gate under arm3c, F1 (also quoted in the text as "0.363") | 0.363 | **0.362** | 730 / 2,014 = 0.36246 |
  | Lesion-agreement table, Ningxia, previous front end, lesion detector | 0.499 | **0.500** | 506 / 1,013 = 0.49951 |

  The tp / fp / fn beside the first two (365 / 1,172 / 112) and every difference and interval
  were right, being computed from counts. 2026-10-11g is left as written. Corrected in
  `model_metrics.md`, `PAPER_MATERIAL.md` §8.30, `transfer.md` §2.4 and
  `models/15_detector_multicorpus_leverA/run_summary.txt`. All 58 intervals quoted across those
  documents match the results file.
- **Also changed.** `stage1_switch_intervals.py` now prints each agreement to four places with
  its counts, so the log cannot be mis-rounded the same way; and its integrity gate exempts
  the script's own two output files, which became tracked with `7dd3ff4` — redirecting into
  the log tripped the gate before the script's first line ran. The gate still stops on any
  other modified output (tested by touching one and restoring it). The results file is
  unchanged; the log was regenerated. Documents that said arm3c's weights were "not yet
  committed" now say they are in git.
- **Key decision or insight:** nothing in 2026-10-11g moves. What this adds is that the pushed
  commit runs from a clean checkout, and that the numbers do not depend on the one script that
  produced them. The slip is a reminder that a figure in a table should be computed from the
  counts beside it, not from another rounded figure.
- **Source:** `outputs/stage1_switch/stage1_switch_results.json` and `.log`;
  `docs/session-memory/2026-10-11h-switch-verification-and-corrections.md`. The second
  implementation was a throwaway script and is not in the repo; its method is described in
  that session file closely enough to rewrite.
- **Follow-ups:** unchanged from 2026-10-11g, less item (6): the manuscript's front end, the
  Docker image, `param_counts.json` with the manuscript, the Kaggle licence, and telling the
  repo owner and the mentor.

## 2026-10-11i — the manuscript's own comparison under the new front end: on DENTEX the gate pipeline now scores above the image-blind constant

Found while mapping `paper/main.tex` against 2026-10-11g. The matrix compared the lesion
detector with the constant and with the gate, and each arm with itself across detectors. It did
not compare **the gate pipeline with the constant** — which is the comparison the manuscript's
abstract, Tables IV to VII and Conclusion are built on. Added here from the same saved runs.
**No model was run. This comparison is not among those `outputs/stage1_switch/PRE_REGISTRATION.md`
§7 lists; it was chosen after the matrix had been read, it is a description, and no rule reads
it.**

- **What was done:** one more paired difference in `scripts/eval/stage1_switch_intervals.py` —
  gate pipeline minus constant, lesion agreement, each cohort and each Ningxia hospital, under
  each front end. Same harness: paired cluster bootstrap over images, 10,000 resamples, seed 42.
  The results file gained 14 blocks; **no existing value in it changed** (checked key by key).
- **Dataset / config:** the committed run directories of rows C, E and F. Nothing re-run.
- **Metrics — gate pipeline minus image-blind constant, lesion agreement.**

  | Cohort | Previous front end | Current front end (arm3c) |
  |---|---|---|
  | DENTEX, 479 lesions | 215 vs 235: **−4.18 pp [−8.42, −0.21]**, constant ahead | 384 vs 302: **+17.12 pp [+12.15, +21.89]**, gate ahead |
  | CariesXrays 1,200, 2,815 lesions | 895 vs 1,583: −24.44 pp [−26.56, −22.36], constant ahead | 1,068 vs 1,699: −22.42 pp [−24.62, −20.18], constant ahead |
  | Ningxia pooled, 1,013 lesions | 412 vs 404: +0.79 pp [−3.27, +4.71], not separated | 608 vs 599: +0.89 pp [−3.86, +5.57], not separated |
  | — test1, 134 images | −15.51 pp [−22.04, −9.19], constant ahead | −18.99 pp [−26.32, −11.84], constant ahead |
  | — test2, 110 | +10.89 pp [+5.17, +16.67], gate ahead | +12.32 pp [+5.01, +19.20], gate ahead |
  | — test3, 40 | +3.09 pp [−9.03, +13.33], not separated here | +1.85 pp [−10.07, +11.56], not separated here |
  | — test4, 53 | +7.53 pp [−0.98, +15.82], not separated here | +12.37 pp [−0.50, +24.35], not separated here |

  The previous-front-end column agrees with what was published from the other machine
  (DENTEX constant − gate +4.59 pp [+0.60, +8.89]; Ningxia −0.89 pp [−4.88, +3.01]).
- **Metrics — the same comparison on FDI-set F1,** already in 2026-10-11 and 2026-10-11g, put
  side by side. Constant 0.320 throughout. Previous front end: constant − gate pipeline +2.61 pp
  [−0.64, +5.99], not separable — that interval is on the published gate arm from the other
  machine (F1 0.294); this machine's control scores 0.300, a gap of 1.95 pp with no interval
  computed. Current front end: gate pipeline 0.362, **+4.27 pp
  [+1.58, +7.05] above the constant**; lesion-detector pipeline 0.498, +17.80 pp
  [+13.48, +22.02] above it.
- **Key decision or insight:** **on development data the paper's headline reverses with the
  front end.** `main.tex` says an image-blind constant "scored highest" and "outscored a
  six-stage pipeline … under two unrelated metrics", and that its four systems span 0.149 to
  0.320 "with the least informed at the top". With the multi-corpus detector, on the same 164
  DENTEX images, the order on F1 is lesion-detector pipeline 0.498, gate pipeline 0.362,
  constant 0.320, then the two language models; and on lesion agreement the gate pipeline leads
  the constant by 17 pp. **The external results do not move:** on Ningxia the gate pipeline and
  the constant are still not separated pooled, with the same swing between hospitals — the
  constant ahead by 19 pp at test1, the gate ahead by 12 pp at test2 — and on CariesXrays the
  constant is still ahead of the gate by 22 pp.
  Three cautions. (1) DENTEX is in-domain for the new detector, so this is a pipeline clearing
  the floor on its own development corpus, not evidence that it reads radiographs it has not
  seen; the external rows are the ones that speak to that, and they are unchanged. (2) The gate
  gets its lesion-agreement lead while flagging 1,439 teeth to the constant's 988; F1, which
  charges for that, gives a 4 pp lead, not 17. (3) What the old headline rested on was thin:
  the previous-front-end DENTEX interval excludes zero by one lesion (upper bound −0.21 pp,
  1 / 479; across 40 other seeds it is −0.22 to 0.00, and −0.20 at 200,000 resamples).
- **What this means for the manuscript.** Which front end the paper reports is no longer only a
  question of which numbering figure to print. It decides whether the abstract's first result
  is true of the system described. `PAPER_MATERIAL.md` §8.30 and `docs/paper/SUBMISSION_TODO.md`
  set out both ways of writing it. Authors and mentor.
- **Source:** `outputs/stage1_switch/stage1_switch_results.json`, keys
  `…/deltas/"<detector>: pipeline_minus_constant-molars"`; the log beside it. Re-derived with a
  second implementation: all 14 points agree to 0.01 pp and every bound within 0.50 pp at a
  different seed.
- **Follow-ups:** the Ningxia test4 lower bounds (−0.98, −0.50) sit close to zero on 53 images
  and should be read as "not separated here", not as near-wins. Nothing else.

## 2026-10-11j — five further measurements under the current front end, for rebuilding the manuscript (Amendment 2)

The decision owner chose to rebuild `paper/main.tex` on the current front end
(`docs/paper/SUBMISSION_TODO.md` §1, option A). The manuscript reports five things the 11 Oct
matrix did not measure under it. They are measured here, under both detectors on this machine,
under Amendment 2 of `outputs/stage1_switch/PRE_REGISTRATION.md` — committed at `d78f502` before
any of them ran. **None is a test, none decides anything, and none can touch an earlier verdict.**

- **What was done:** rows I, J, K and M run; row L computed from row G's saved files. Each
  `models/11` (or Control B) control was checked against its gate before the arm3c result was
  opened. All five gates passed.
- **Dataset / config:** as 2026-10-11g. Rows I and J read the per-tooth rows row B saved and run
  no model. Row K runs the pipeline as shipped over the 164 DENTEX images on CPU. Row M is the
  validation call the trainer made on 3 Sep, on CPU. **Ningxia was not scored again.**
- **Metrics — row I, numbering failure taxonomy, DENTEX, 936 teeth.**

  | | Correct | Not detected | Off by one | Same quadrant, 2+ | Mirrored | Wrong arch | Other |
  |---|---|---|---|---|---|---|---|
  | Previous detector, this machine | 547 | 273 | 92 | 8 | 8 | 6 | 2 |
  | Previous detector, as published | 546 | 275 | 89 | 10 | 8 | 6 | 2 |
  | **arm3c — in-domain** | **869** | **4** | 51 | 6 | 2 | 2 | 2 |

  Under arm3c 63 detected teeth carry a wrong code; 51 of them (81.0%) name the neighbouring
  tooth in the right quadrant, and 6 of 932 detected teeth (0.6%) are placed in a wrong quadrant.
  With the previous detector on this machine: 92 of 116 (79.3%) and 16 of 663 (2.4%).
- **Metrics — row J, coverage–accuracy for numbering.** Threshold 0.30 as registered on 28 Aug,
  located and not tuned.

  | | Teeth | Full coverage | 90% | 75% | 50% | Gain at 75% | Shuffled | At 0.30 |
  |---|---|---|---|---|---|---|---|---|
  | Previous, this machine | 663 | 0.825 | 0.844 | 0.877 | 0.909 | +5.22 pp [+3.49, +7.30] | −0.06 pp | coverage 91.2%, accuracy 0.845 |
  | Previous, as published | 661 | 0.826 | 0.849 | 0.885 | 0.918 | +5.91 pp [+3.88, +7.68] | +0.03 pp | 90.8%, 0.847 |
  | **arm3c — in-domain** | 932 | 0.932 | 0.955 | **0.980** | 0.989 | **+4.76 pp [+3.29, +6.54]** | −0.06 pp | **96.1%, 0.941** |

  The gain from declining survives under arm3c and its shuffled control is still nil. At the
  registered threshold the pipeline keeps 896 of the 936 teeth present (95.7%); with the previous
  detector it kept 605 (64.6%). Retaining three quarters of detections is now 74.7% of the teeth
  present, where the manuscript's sentence says 53.0%.
- **Metrics — row K, Stage-4 flags on DENTEX, 164 images.** Previous detector 29 of 3,607
  detected teeth, 0.80% [0.48, 1.18], on 22 images; arm3c 34 of 4,512, 0.75% [0.48, 1.06], on 27
  images; difference −0.05 pp [−0.41, +0.32], not separable. On the 12 images of the August run:
  2 of 289 and 3 of 355. **The manuscript's "0.7% of DENTEX teeth" turns out to be 2 of 299 teeth
  on 12 images with the bbox detector of two front ends ago** (`outputs/r4_batch_v3/`); the
  figure survives on 164 images, but it had never been measured on the detector the manuscript
  describes. A firing rate, not a sensitivity: DENTEX has no periodontal ground truth.
- **Metrics — row L, Stage-4 flag rate per Ningxia hospital**, over each detector's own affected
  teeth.

  | Hospital | Images | Previous detector | arm3c | Difference |
  |---|---|---|---|---|
  | test1 | 320 | 77 / 3,289 = 2.34% [1.76, 2.97] | 103 / 3,538 = 2.91% [2.23, 3.65] | +0.57 pp [−0.12, +1.27] |
  | test2 | 297 | 35 / 2,458 = 1.42% [0.90, 2.02] | 18 / 2,834 = 0.64% [0.34, 0.96] | −0.79 pp [−1.34, −0.28] |
  | test3 | 50 | 22 / 415 = 5.30% [3.10, 8.00] | 18 / 454 = 3.96% [2.03, 6.36] | −1.34 pp [−4.08, +0.95] |
  | test4 | 69 | 31 / 630 = 4.92% [3.08, 6.96] | 14 / 223 = 6.28% [2.49, 12.12] | +1.36 pp [−2.89, +7.43] |

  The control is within 0.34 pp of the other machine at every hospital. **One thing is
  unexplained and is reported as such: at test4 the teeth counted as affected fall from 630 to
  223 under arm3c, while the teeth it detects there rise from 22.6 to 28.9 per image; 26 of the
  69 images have no affected tooth at all.** At the other three hospitals the count rises with
  the detector, as expected. A tooth is "affected" when at least half its box lies inside the
  expert band, so the count depends on box shape as well as box number; the boxes are not saved
  in these files and Ningxia was not re-run to look. Lesion agreement at test4 rose under arm3c
  like everywhere else (2026-10-11g), so the boxes are not misplaced. Until it is understood the
  test4 Stage-4 rate under arm3c rests on 223 teeth and should not be quoted as a hospital
  result.
- **Metrics — row M, Tufts test box mAP@0.5, 150 images, the Lever A label frame.** Control B
  (Tufts only, same recipe) 0.7233, against 0.7243 on the training machine; arm3c **0.5873**,
  against 0.5852. Both reproduce within 0.21 pp. The like-for-like cost of multi-corpus training
  on Tufts is therefore **−13.6 pp of box mAP** (0.723 → 0.587). The 0.810 → 0.585 quoted until
  now, including in 2026-10-11f and -g, compares a segmentation model scored on polygon labels
  with a detection model scored on box labels; it is two protocols and overstates the gap.
  Guard 2 is as it was: failed.
- **Key decision or insight:** nothing here changes a decision. For the manuscript: numbering's
  residual errors are still mostly off by one; selective prediction still works and the registered
  threshold now keeps 96% of teeth; Stage 4 is as inert on DENTEX as before; and the Tufts mAP
  cost should be stated as 13.6 pp against the Tufts-only control, not as 22.5 pp against a
  different kind of model.
- **Process, disclosed.** The first read of rows I–M stopped on the analysis script's own
  integrity check, because `run_matrix.sh` — tracked since `7dd3ff4` — had gained the five rows.
  It is the command list, not a result, and is now exempt, as the script's two output files
  already were. No row was run again and no existing value in the results file changed (checked
  key by key). The taxonomy and coverage figures were re-derived from the raw rows by separate
  code and agree.
- **Source:** `outputs/stage1_switch/stage1_switch_results.json`, keys `I_…`, `J_…`, `K_…`,
  `M_…` and `G_ningxia_stage4_flag/per_hospital`; the eight new run directories beside it;
  `run_matrix.sh` rows I, J, K, M.
- **Follow-ups:** the test4 affected-tooth count. Whether the bone-loss branch stays in the
  manuscript at all is still the authors' decision (`SUBMISSION_TODO.md` §2 item 3), and it
  decides whether rows K and L are ever printed.

## 2026-10-11k — the manuscript rebuilt on the current front end; its number checker rebuilt with it

Option A of `docs/paper/SUBMISSION_TODO.md` §1, chosen by the decision owner on 11 Oct.
`paper/main.tex` described the Tufts-only seg detector in every table; it now describes the
pipeline as it ships. **This entry reports no new pipeline measurement** — every figure the
manuscript now carries is from 2026-10-11g, -i and -j — and one new check, on leakage.

- **What was done:** `paper/main.tex` rewritten from the abstract to the Conclusion, in three
  passes, each compiled; four of its five figures re-rendered from the new artefacts;
  `scripts/verify_paper_numbers.py` rebuilt to assert the new text against
  `outputs/stage1_switch/`; `scripts/count_model_params.py` and
  `outputs/param_counts/param_counts.json` moved to the current Stage-1 detector.
- **What the manuscript now says, where it used to say otherwise.**
  - *Headline.* No longer "the constant scored highest". On the 164 DENTEX images the constant
    (F1 0.320) outscores both language models, and the pipeline is above it — 0.362 with the
    per-crop gate, 0.498 with the lesion detector — **with a tooth detector trained on that
    corpus**. On four external hospitals the gate pipeline and the constant are not separated
    (31-point swing between sites), and on CariesXrays the constant leads by 22.42 pp.
  - *The detector's adoption.* §Data states that it was adopted over a pre-registered guard it
    failed — Tufts test box mAP@0.5 0.587 against a Tufts-only control's 0.723 — by a dated
    decision, and the Discussion and Limitations repeat it.
  - *Numbering.* 92.8% on DENTEX labelled in-domain, 63.5% on Tufts beside it, and the absence
    of any figure on unseen data stated as a limitation.
  - *Lever B.* The adoption rule is reported as met on the pipeline as it then stood, with its
    three published differences; Table VIII gives the same arms under the current detector, as
    a description. "It replicates on the one cohort that is genuinely external" became a pooled
    statement with the per-hospital intervals beside it. The one comparison that went against
    the lesion detector (DENTEX lesion agreement, 0.595 against the gate's 0.802) is printed.
  - *The constant.* A paragraph in §Evaluation Protocol says its codes are placed by the
    pipeline's own boxes and numbering, so its agreement moves with the front end. "The
    radiograph is never read" was untrue of the localisation tables in that sense.
  - *CariesXrays.* Every row now uses the 1,200 held-out images (2,815 lesions). The
    1,500-image sample of 1 Sep and the three figures derived from it (72.0% on molars, 60.2% on
    the eight codes, 22.1% outside any detected tooth) are no longer quoted: they were measured
    with an earlier detector and were not re-measured.
  - *Stage 4.* DENTEX firing rate 0.75% on 164 images; external 2.17% pooled, per hospital with
    intervals, and the unexplained test4 denominator stated.
- **Metrics — the one new check.** The 1,200 CariesXrays images against every other corpus in
  the project: **0 byte-identical** to any of Tufts (1,000), DENTEX `disease/` (250), DENTEX
  enumeration (685 files), Kaggle dual (500) or Ningxia (1,640); nearest image by a 256-bit
  difference hash 42, 50, 46, 45 and 45 bits respectively. The manuscript's "verified
  leakage-free, both byte-wise and perceptually" had been established for the 1,500-image
  sample; it now holds for the cohort actually scored.
  `outputs/stage1_switch/cariesxrays_1200_leak_check.json`.
- **Verification.**
  - `verify_paper_numbers.py`: **191 numeric claims, all present** (it was 127). It asserts by
    presence, so a number typed in two places is only checked once: of eight deliberately wrong
    digits, it caught the four that occur once and missed the four that occur again elsewhere.
    Every repeated quantity was therefore also listed by pattern and read for a second
    spelling; none was found. The checker's limit is unchanged from before and worth knowing.
  - Built with tectonic 0.17 (XeTeX), which this machine now has. With a Times clone loaded for
    non-pdfLaTeX engines — a five-line conditional in the preamble that pdfLaTeX never enters —
    the *previous* manuscript builds to 14 pages, the same as the committed pdfLaTeX PDF, and
    the rebuilt one to **15 pages**, with no undefined reference or citation and one overfull
    box of 4 pt. `paper/main.pdf` is that build. `paper/main.bbl` is unchanged: the same
    references are cited.
  - `pytest tests` 174 passed; all eleven invariants hold.
- **Not changed, deliberately.** The title. The author block and every mandatory statement.
  The claim about the 49 surveyed papers. The bone-loss branch's place in the paper and the
  words "domain shift" and "did not transfer" — whether it stays is the authors' decision; what
  was corrected, because the sentences were being retyped anyway, is that the Data section and
  one limitation no longer say its split was image-level.
- **Still to do before this manuscript is a submission.** A pdfLaTeX build on the Windows
  machine, and `paper/paper.txt`, a `pdftotext` dump that this machine cannot regenerate and
  which is now stale. The Docker image. Everything in `SUBMISSION_TODO.md` §2. The manuscript is
  one page longer than it was, against venues that already capped below it.
- **Key decision or insight:** rebuilding on the new front end did not make the paper's
  argument weaker; it moved it. The claim is no longer that a constant beats the pipeline at
  home. It is that beating it at home, with a detector that has seen the corpus, told us
  nothing about the four hospitals where the two cannot be told apart.
- **Source:** `paper/main.tex`, `paper/main.pdf`, `paper/fig_{baselines,stage2,coverage,boneloss}.png`;
  `scripts/verify_paper_numbers.py`; `scripts/figures/make_baseline_figure.py`,
  `make_boneloss_paper_figure.py`; `outputs/param_counts/param_counts.json`.

## 2026-10-12 — per-stage evidence audit by a second council and an ML-engineering review: no new number, one cohort mis-described

- **What was done:** At the user's request every stage's evidence was classified — held out,
  in-domain, selection-conditioned, validation-only or invalid — by three independent read-only
  reviewers and the `mle-reviewer` agent. No model was run and no number changed. The chair
  re-ran `pytest tests` (174 pass), `scripts/verify_paper_numbers.py` (191 claims, no drift) and
  `scripts/eval/stage1_switch_intervals.py` (results file byte-identical to the committed one).
- **Dataset / config:** none run.
- **Metrics:** none new. Classification: Stages 1 and 2 held out but in-domain, with the default
  detector chosen against two registered verdicts. Stage 3a lesion detector: DENTEX in-domain;
  CariesXrays 1,200 **validation**; Ningxia external but one of the cohorts that decided its
  adoption. Retired gate: held-out test crops (863 crops, 34 images) and external on both
  CariesXrays and Ningxia. Stage 3b: validation only, 133 crops. Stage 4a: not held out.
  Stage 4b: 52 validation crops, split unaudited.
- **Key decision or insight:**
  1. **The 1,200 CariesXrays images scored in every lesion-agreement table are the lesion
     detector's validation split.** The training YAML written by
     `scripts/yolo/train_lever_b_pooled_detector.py` names `cariesxrays_det/images/val` as `val`,
     with `patience=25`. No gradient came from those images; early stopping and the choice of
     `best.pt` did. `models/16_lever_b_pooled/run_summary.txt` and
     `scripts/yolo/build_lever_b_pooled_dataset.py` have said so since 4 Sep. The manuscript
     rebuilt on 11 Oct says the detector "was kept away from" them (`paper/main.tex` 588–589;
     footnote d, 1019–1020; "1,200 held out", 503), and `stage1_switch_intervals.py` labels the
     cohort "1,200 held-out images". For the lesion detector they are validation data. For the
     gate and the constant, neither of which saw them, they remain external, so gate minus
     constant (−22.42 pp) is unaffected. Lever B's rule of 4 Sep counted this cohort among its
     "2 of 3"; that verdict stands as scored and must be described accurately from here on.
  2. **A held-out test of Stage 3b cannot be built from data on hand.** The 164 leak-free DENTEX
     images carry `çürük` only; the label table in `scripts/eval/lesion_localization.py` has no
     deep-caries class.
  3. **Verdict, 3 of 3:** no GPU, no new default, no further pass over Ningxia. Remove the
     Stage 3b and Stage 4 figures from the conference cut. None of the weak absolute numbers —
     precision 0.439, Tufts 63.5%, box mAP 0.587 — bears on the paper's thesis.
  4. Three default-preserving, estimation-only measurements were recommended and **none has been
     run**: the lesion detector's flagged teeth by tooth type and label category on DENTEX, from
     saved rows; the precision of the molar codes on Tufts, from saved rows; numbering on
     UFBA-425.
- **Source:** `docs/session-memory/2026-10-12b-stage-metrics-council.md`;
  `scripts/yolo/train_lever_b_pooled_detector.py`; `models/16_lever_b_pooled/run_summary.txt`;
  `paper/main.tex`.
- **Follow-ups:** correct the wording (`docs/paper/SUBMISSION_TODO.md` §1a, row i). A
  pre-registration for the three measurements needs the user's go-ahead. One reviewer counted
  tooth types in the saved predictions while checking feasibility — 447 of 624 flagged codes
  molars, by its count **[UNVERIFIED]** — so the pre-registration must list that as already
  seen. Engineering findings from the review (requirements mostly unpinned, `weights_only=False`, no
  hash check before loading a checkpoint) are in the session file; none changes a reported number.
