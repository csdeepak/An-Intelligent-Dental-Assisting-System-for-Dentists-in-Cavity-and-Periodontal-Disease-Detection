# `scripts/yolo/` — YOLO detector scripts (tooth detection + the Lever experiments)

**Last verified: 4 September 2026.**

Three of these were recovered from the ad-hoc `DataSets/` exploration workspace that used to
sit at the repo root (relocated to `_repo_archive/datasets_workspace/`, a sibling of this repo
— nothing was deleted). Two more were added in August 2026 for the **R1 bbox → instance-mask
upgrade** (`docs/research/MASTER_PLAN_2026H2.md` §3 R1); two more on 1 Sep for **Lever 1 / B1**,
the multi-corpus detector retrain; two more on 2 Sep for **Lever 2**, a standalone
caries-**lesion** detector on the CariesXrays benchmark; two more (2–3 Sep) for **Lever A**,
the multi-corpus detector *done right* — `build_multicorpus_detector_v2_dataset.py` and
`train_multicorpus_detector_v2.py`; and two more on 4 Sep for **Lever B's B-pooled arm** —
`build_lever_b_pooled_dataset.py` and `train_lever_b_pooled_detector.py`. **Lever A ran 3 Sep
and is an ABLATION** (same verdict as Lever 1, stronger result — see below). All under
`transfer.md` §3 Track B.

**Lever B (lesion-detection caries path) — pre-reg frozen and BOTH arms trained/evaluated,
4 Sep.** B-single (Lever 2's `models/14`, zero GPU) wins CariesXrays decisively but collapses
on DENTEX (8.6% tooth-level lesion agreement, a decisive loss vs. the gate/constant). B-pooled
(this session's new training, `models/16_lever_b_pooled/`) recovers DENTEX to a statistical tie
(45.5%) while barely costing the CariesXrays win (68.4%, was 69.4%). **Sec 6 acceptance rule not
yet met by either arm** — needs Ningxia, not on this machine. `RESULTS_LOG.md` 2026-09-04f / 04g,
`docs/session-memory/2026-09-04a-lever-b-build-and-both-arms.md`. Cold-start / next steps:
`outputs/lever_B_lesion_caries_path/START_HERE.md`.

The tooth-detection scripts are the **Stage 1 (YOLOv11 tooth detection)** toolchain, kept
separate from the scripts in `scripts/` one level up, which belong to the **Stage 2–5
crop/classifier** toolchain. Both sets are live; they simply serve different halves of the
pipeline. **Lever 2 is not a pipeline component at all** — it produces one benchmark row
(`models/14_cariesxrays_lever2/`, `RESULTS_LOG.md` 2026-09-02b) and adopts no checkpoint.

## The toolchains here

| | bbox (superseded baseline) | seg (**current pipeline default**) | multi-corpus (Levers 1 + A) |
|---|---|---|---|
| convert | `convert_tufts_to_yolo.py` | `convert_tufts_to_yolo_seg.py` | `build_multicorpus_detector_dataset.py` (L1) → `build_multicorpus_detector_v2_dataset.py` (LA) |
| train | `train_yolo.py` | `train_yolo_seg.py` | `train_multicorpus_detector.py` (L1) → `train_multicorpus_detector_v2.py` (LA) |
| evaluate | `evaluate_yolo.py` | — (use Ultralytics val) | `scripts/eval/validate_fdi_assignment.py` + `score_lever1_arm.py` / `score_leverA_arm.py` |
| dataset | `_repo_archive/datasets_workspace/dataset/` | `data/tufts/dataset_seg_v2/` (corrected build) | `data/detector_multicorpus/` (L1) / `data/detector_multicorpus_v2/` (LA) — both gitignored |
| status | **frozen**, `tooth-detector-a100-1024-v1.0` (val 0.834 / test 0.782) | **frozen + adopted 27 Aug**, `models/11_yolo_seg_tufts_r1/best.pt` (`tooth-detector-seg-tufts-1024-v1.0`, box test 0.810). Boxes only — masks failed §2's bar, R2 stays unwired | **Both ABLATIONS, neither adopted.** L1 (1 Sep, 2 corpora): FDI e2e 0.584 → 0.934, Tufts guard fails 0.810 → 0.647. **LA (3 Sep, 4 corpora + balanced sampling): primary + Guard 1 pass, Guard 2 fails** (Tufts test 0.585 / 0.552, monotonic). Bidirectional tradeoff — see "Lever A" below. `models/{13,15}_detector_multicorpus_*/`. |

**Lever A — DONE 3 Sep, ABLATION** (`models/15_detector_multicorpus_leverA/run_summary.txt`,
`RESULTS_LOG.md` 2026-09-03 + 03b). Lever 1 pooled only 2 corpora with Tufts at 52% of the mix;
Lever A pools **4 corpora / 4 institutions** — Tufts 700 + DENTEX 561 + Kaggle-dual 449 +
UFBA-425 382 — with **per-corpus balanced sampling** and a guard scoped to *cross-domain*, not
just Tufts. Ran on an RTX PRO 6000 (~₹735 total), geometry gate IoU 1.0000, arms `controlB` /
`arm3c` (primary) / `arm4c` (+ the aspect-distorted UFBA-425, additive only).

**Pre-registered verdict:** **PRIMARY passes** (FDI e2e on the 164 leak-free DENTEX images
**0.584 → 0.928**, Δ +34.4 pp [+30.3, +38.5] — *replicates* Lever 1's +34.9 pp with 3-4 corpora;
UFBA adds nothing, Arm 3C = Arm 4C). **GUARD 1 passes** (pooled external caries agreement Δ
+9.1 pp [+7.5, +10.8] — Ningxia 0.407 → 0.600, CariesXrays 0.309 → 0.370). **GUARD 2 FAILS**
(Tufts frozen test box mAP: Control B 0.724 → Arm 3C **0.585** → Arm 4C **0.552** — monotonic in
corpus count, *worse* than Lever 1's 0.647; balanced sampling put Tufts at 33% of the mix).
2 of 3 pass, adoption needs all three → **ABLATION, pipeline default detector unchanged.**

The tradeoff is **bidirectional** — the multi-corpus detector is worse on Tufts test by ~15 pp
and better on DENTEX (+34) and every external cohort (+6 to +19), i.e. better on 5 of the 6
paper cohorts. Guard 2 protects Tufts-benchmark continuity, not the deployment goal.
`outputs/lever_A_multicorpus_detector_v2/{PRE_REGISTRATION,STATUS}.md`.

**Lever B, B-pooled arm — DONE 4 Sep, ablation (Sec 6 not yet met).** Unlike Levers 1/A/2, this
is a **caries-lesion detector**, not a tooth detector — it competes with the caries *gate*
(Stage 3), not Stage 1. B-single (`models/14`, CariesXrays-only training, zero GPU here — see
Lever 2 below) wins CariesXrays decisively (69.4% tooth-level lesion agreement vs. gate 31.7% /
constant 56.2%, CI excludes 0) but loses DENTEX decisively (8.6%, CI excludes 0 the wrong way)
— the pre-registered "wins in-domain, fails to transfer" outcome. B-pooled adds DENTEX-domain
caries-box training data (`scripts/dentex/build_dentex_caries_boxes.py`, whole-tooth boxes, a
domain adapter — not a second lesion-box source) via a per-corpus-balanced pool
(`build_lever_b_pooled_dataset.py`, Lever A's exact balancing recipe: CariesXrays 4,800 +
DENTEX-caries 650 replicated to 4,800 = 9,600 images/epoch). Result: DENTEX moves from a
decisive loss to a **statistical tie** (45.5% [40.9,50.1], both deltas now include zero) at a
~1pp cost to the still-decisive CariesXrays win (68.4%). Not one of the pre-reg's discrete
outcome bins — recorded as its own honest result rather than forced into the nearest one. Rented
an **RTX-PRO6000** (A100 was unavailable at rental time, confirmed live via `jl gpus`), trained
120 epochs / patience 25, early-stopped at 54; ₹546.93, instance destroyed after a verified
download. **Sec 6's literal bar (≥2 of 3 cohorts, "beats" not "ties") is not met by either
arm** — Ningxia is the deciding cohort and is not on this machine.
`models/16_lever_b_pooled/run_summary.txt`, `RESULTS_LOG.md` 2026-09-04f / 04g.

**Lever 1 in one line:** pool the 700 Tufts detection images with DENTEX `quadrant_enumeration`
(634 images / 18,095 boxes) to lift detector **recall** (70.6%), which is the measured binding
constraint on the 58.3% Stage-2 headline. DENTEX ships no polygons, so this is a `detect` (not
`-seg`) run — hence the separate `yolo11l.pt` base and the Tufts-only, canonical val/test split.

`rotate_tufts_radiographs.py` sits upstream of both: the raw Tufts release ships **landscape
1615×840**, and every converter expects portrait 840×1615. That rotation is **90° counter-clockwise** —
undocumented tribal knowledge until Aug 2026, then recorded as *clockwise* until 22 Aug, when
comparing all 1,000 raw/rotated pairs settled it (1000/1000 CCW, 0/1000 CW). The visual check
that originally set the direction could not have caught the error: CW and CCW differ by 180°,
and tooth detection is largely indifferent to a 180° flip.

| Script | What it does |
|--------|--------------|
| `convert_tufts_to_yolo.py` | Converts Tufts annotations to YOLO format. Reads `Radiographs_rotated/` (portrait 840×1615), `Segmentation/teeth_bbox.json` and the frozen 70/15/15 split CSV; writes `dataset/images/{train,val,test}`, `dataset/labels/{train,val,test}` (`0 cx cy w h`, normalised) and `dataset/data.yaml`. Single-class detection (`tooth`), primary/letter teeth **included**, degenerate boxes (w<2 or h<2) dropped, unlabelled images skipped. |
| `train_yolo.py` | Fine-tunes YOLOv11l on the converted dataset. Locked config: imgsz 1024, AdamW, cosine LR 1e-3 → 1e-5, 150 epochs with early-stopping patience 30, clinically-valid augmentation only (no vertical flip, no mosaic). Writes `runs/detect/<name>/weights/{best,last}.pt`, `results.csv` and training curves. |
| `evaluate_yolo.py` | Runs the trained `best.pt` against the held-out **test** split, writes an eval run directory with metric plots, prediction visualisations on 20 test images, and an `eval_summary.txt`. |
| `build_multicorpus_detector_dataset.py` | **Lever 1 (1 Sep).** Builds `data/detector_multicorpus/` — Tufts (700 train, keyed by `outputs/eda_tufts/split_v1.csv`) + DENTEX `quadrant_enumeration` (634 imgs, all → train), converted into the detector's 90°-CCW frame via `src.orientation.rot_box`. **Three gates, all must pass or it aborts:** canonical box-count reproduction (Tufts val 3,794 / test 3,924, matching the frozen detector's GT), a geometry re-score of all 18,095 DENTEX boxes against source COCO (median IoU ≥ 0.99 — measured 1.0000), and an MD5 leakage guard vs the 164 leak-free eval images. Val/test are **Tufts-only** so box mAP stays comparable to the frozen detector. Tufts half is sourced from `_repo_archive/datasets_workspace/Segmentation/teeth_bbox.json` + `Radiographs_rotated/` — **not** `data/tufts/dataset_seg`, which is the withdrawn void corpus (`RESULTS_LOG.md` 2026-09-01e/f). |
| `train_multicorpus_detector.py` | **Lever 1 (1 Sep).** `--arm {tuftsonly, multicorpus}`. Config copied verbatim from `train_yolo_seg.py` (epochs 150, patience 30, batch 32, imgsz 1024, seed 42, deterministic, AdamW, cos_lr) — the **only** deliberate differences are `yolo11l.pt` (detect, not seg) and the train split. `tuftsonly` derives a 700-image Tufts-only train split from the same uploaded tree and is Control B (isolates the seg→detect head change); `multicorpus` is the Arm (isolates the data). Writes `data_<arm>.yaml` at runtime; refuses CPU. |
| `build_multicorpus_detector_v2_dataset.py` | **Lever A (2 Sep, session 3c).** Builds `data/detector_multicorpus_v2/` — Tufts 700 (frozen split) + DENTEX `quadrant_enumeration` 561 + Kaggle-dual 449 + UFBA-425 382, each upright corpus rotated 90°-CCW into the detector frame via `src.orientation.rot_box`. **Gates, all must pass or it aborts:** Tufts canonical box-count reproduction (val 3,794 / test 3,924), a combined geometry re-score of all 42,500 rotated boxes (median IoU ≥ 0.99 — measured 1.0000), MD5 leakage guard vs the 164 leak-free eval images, and within-/cross-corpus byte-identical dedup (11 DENTEX + 1 Kaggle dropped). Writes a **per-corpus balanced** `train.txt` (4×700) and `train_3corpus.txt` (3×700, no UFBA), `train_tufts.txt` (Control B), per-corpus `test_*.txt`, + `_check/` renders. Paths are `./`-relative so the lists survive the move to a GPU box. **Rotated corpora capped at 1600 px / JPEG q85** (3 Sep — upload-size mitigation for a slow home connection, 1.1 GB → 467 MB; training imgsz is 1024, geometry gate re-passed). val/test = Tufts-only. `--dry-run` supported. |
| `train_multicorpus_detector_v2.py` | **Lever A (3 Sep).** `--arm {controlB, arm3c, arm4c}` selects `train_tufts.txt` (700) / `train_3corpus.txt` (2,100) / `train.txt` (2,800). Config **byte-identical** to `train_multicorpus_detector.py` — the only thing that varies between arms is the `train:` list. Writes `data_<arm>.yaml` at runtime, refuses CPU, and runs the Guard-2 Tufts-frozen-test val on `best.pt` immediately after training. Result: `models/15_detector_multicorpus_leverA/`. |
| `build_cariesxrays_detector_dataset.py` | **Lever 2 (2 Sep).** Builds `data/cariesxrays_det/` from the CariesXrays benchmark (`~/Downloads/Capstone/CariesXrays_Dataset/`) — 6,000 VOC images, single class `decay`, **this project's own seed-42 4,800/1,200 image-level split** (the official FPCL split is not public). **Reads box dims from the decoded image, never the XML `<size>`** — 27.3% of the XMLs carry a wrong width, the same class of defect that voided a 90-epoch run (`RESULTS_LOG.md` 2026-08-27a). Gate: 0 px round-trip error, 0 normalised coords outside [0,1], 0 train/val overlap, renders eyeballed. `--dry-run` supported. |
| `train_cariesxrays_detector.py` | **Lever 2 (2 Sep).** YOLOv11l `detect`, config verbatim from `train_multicorpus_detector.py` except `nc=1` (`decay`), this project's CariesXrays split, and epochs/patience 150/30 → 120/25 (cost cap). Runs a final COCO-AP val on `best.pt` and prints AP / AP50 / AP75. Writes `data_lever2.yaml` at runtime; refuses CPU. **Result: AP 0.482 / AP50 0.845 / AP75 0.500** — level with FPCL, indicative not head-to-head (`models/14_cariesxrays_lever2/run_summary.txt`). Batch auto-reduced 32 → 16 after CUDA OOM at 1024px on an A100-40GB — **the fallback that became `train_lever_b_pooled_detector.py`'s pre-chosen default, below**. |
| `build_lever_b_pooled_dataset.py` | **Lever B, B-pooled (4 Sep).** Builds `data/lever_b_pooled/train_pooled.txt` — CariesXrays-train (4,800, as-is) + DENTEX-caries (650, replicated `list * ceil(4800/650)` sliced to 4,800 — Lever A's exact `balanced()` recipe) = 9,600 lines, shuffled seed 42. val stays CariesXrays-only (1,200, unreplicated — the same split B-single used for early stopping and its reported AP, so neither arm is advantaged by this choice). Gate: 0 cross-corpus MD5 overlap, every path in the pooled list resolves to both an image and a same-stem label. `--dry-run` supported. |
| `train_lever_b_pooled_detector.py` | **Lever B, B-pooled (4 Sep).** Config copied verbatim from `train_cariesxrays_detector.py` except the pooled train list. **`batch=16` by default, not the canonical 32** — B-single's own training already hit this exact OOM on an A100-40GB at 1024px (see the row above); 16 avoids repeating it AND keeps both arms' *realised* recipes identical. Asserts the pool is exactly 9,600 lines and val is exactly 1,200 images before training, refusing a stale or partial build. `data.yaml`'s `path:` (and, after a real bug found here, the train-list itself) are rewritten to **absolute paths at train time** — ultralytics' `train.txt` loader only rewrites a `./`-prefixed line, resolving a bare relative one against the training process's cwd rather than `path:` (verified directly against `ultralytics/data/base.py get_img_files`, not guessed — the first launch crashed with "No labels found" before this was found and fixed). **Result: AP 0.379 / AP50 0.822 / AP75 0.291** (COCO AP on CariesXrays-val — lower than B-single's own, the expected cost of pooling in coarser DENTEX boxes; **not** the number Lever B's acceptance rule is scored on — see the Lever B section above for the metric that is). Early-stopped at epoch 54 of 120. `models/16_lever_b_pooled/run_summary.txt`. |

## Relationship to the rest of the repo

- The run these scripts produced (A100, imgsz 1024, 150 epochs) is the **frozen canonical
  detector**, tag `tooth-detector-a100-1024-v1.0` — see `models/06_yolo_detection_a100_run/`
  and `docs/results/figures/yolo_detection_a100/`. T0.6 is closed.
- The notebooks that actually executed the two competing runs live in
  `notebooks/yolo_detection/`.

## Caveats before re-running

- **`convert_tufts_to_yolo.py` silently drops 66 real teeth.** Its degenerate-box guard
  (`w < 2 or h < 2`) fires on 66 objects whose `bounding box` field in the source JSON is
  corrupt (1×1 / 1×2 px) while their polygon is intact and full-size — verified, and three
  were rendered to confirm they are real teeth. So the bbox dataset is missing 47 train / 13
  val / 6 test teeth, and the frozen detector's numbers were scored against test ground truth
  holding 3,924 of 3,930 real instances. **Left unfixed on purpose** — changing it would
  invalidate the frozen detector's reproducibility. `convert_tufts_to_yolo_seg.py` keeps all
  66. Full analysis: `docs/research/T0.6_detector_reconciliation.md` §3.5.
- Paths at the top of `convert_tufts_to_yolo.py` are **hard-coded to the original macOS
  workspace** (`/Users/.../Downloads/Capstone/DataSets`, which no longer exists). Edit
  `TUFTS_ROOT`, `SPLIT_CSV` and `DATASET_DIR` before use. The **seg** converter does not have
  this problem — its paths are environment-overridable (`TUFTS_ROOT`, `TUFTS_IMG_DIR`,
  `TUFTS_POLY_JSON`, `TUFTS_SPLIT_CSV`, `TUFTS_SEG_DATASET_DIR`), so the script that runs is
  the script under review.
- The docstring targets in `train_yolo.py` / `evaluate_yolo.py` (mAP@0.5 ≥ 0.90) were
  copied from published Tufts benchmarks and are **not** what this project achieved.
  Actual numbers: val mAP@0.5 = 0.834, test mAP@0.5 = 0.782. See
  `docs/results/model_metrics.md`.
- `RUN_NAME` in the scripts is `tufts_v1`; the executed run was named `tufts_clean_v1`.

---

**Publication target and grading criteria:** `../../transfer.md` §5.
