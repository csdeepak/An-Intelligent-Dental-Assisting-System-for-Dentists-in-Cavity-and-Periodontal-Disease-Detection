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
