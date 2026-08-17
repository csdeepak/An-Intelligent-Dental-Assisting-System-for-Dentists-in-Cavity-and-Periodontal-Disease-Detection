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
