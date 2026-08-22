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
