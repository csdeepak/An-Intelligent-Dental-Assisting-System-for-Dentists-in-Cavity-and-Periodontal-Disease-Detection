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
