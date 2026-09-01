# Model metrics — scoreboard

Current best numbers only. One table per model, nothing else. For how a number was
obtained see `PAPER_MATERIAL.md`; for when and why it changed see `RESULTS_LOG.md`.

**Last updated:** 2026-08-28 (header corrected 2026-08-31). Stage 1 and Stage 2 are **current** on
the seg detector + FDI head v2.0, re-measured 27 Aug 2026 (recall 70.6%, FDI exact 58.3%
end-to-end) — the "figures are STALE" warning this line used to carry is retired. 28 Aug added the
C1-hardened arms (32B / few-shot / image-blind constant), the C4 coverage–accuracy table, the
Stage-2 head-v3 three-corpus ablation, and the per-stage parameter table (83.6 M total / 61.2 M
caries path). The 29 Aug README rebuild changed no number here.

---

## Stage 1 — Tooth detection · Tufts

**Current default since 27 Aug 2026 is the YOLOv11l-SEG model — see the R1 block below.**
The YOLOv11l **bbox** run immediately following is the SUPERSEDED detector, retained and
hash-pinned because every number published before 27 Aug was measured on it.

### YOLOv11l bbox (superseded as default, still the reference for older results)

Best run: A100, imgsz 1024, 150 epochs requested / 128 run, best epoch 98.

| Split | Images | Instances | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|-------|--------|-----------|-----------|--------|---------|--------------|
| Validation | 150 | 3,794 | 0.788 | 0.772 | **0.834** | 0.367 |
| Test (held out) | 150 | 3,924 | 0.7643 | 0.7421 | **0.7824** | 0.3351 |

Superseded run (H200, imgsz 768, 50 ep): val mAP@0.5 **0.678**. Not test-evaluated.
Inference ~3.1 ms/image (A100). Weights: `models/06_yolo_detection_a100_run/best.pt`
(git-ignored, local only). **Canonical detector: FROZEN, 20 Aug 2026 — version tag
`tooth-detector-a100-1024-v1.0`, SHA-256 `4d9f099fb90bb03446fd1d81f2a509cd1589bdc0d4de83269894d9128e4b3a2b`.**
Verified by loading under Ultralytics (task=detect, 1 class, 25.3M params) and by
byte-identical `args.yaml`/`results.csv` against the copies already committed here — see
`docs/research/T0.6_detector_reconciliation.md` §1 for the full verification record.

### R1 — YOLOv11l-**seg** (27 Aug 2026) — **ADOPTED as Stage-1 default**

Same frozen split, same config, only `model` and label format changed. Held-out test touched
once. Weights `models/11_yolo_seg_tufts_r1/run/weights/best.pt` (gitignored), tag
`tooth-detector-seg-tufts-1024-v1.0`, SHA-256 `271316c46caaf4029ea707fa77b6fe30697795e46632e1f6fcae3498c48781ba`.

| Split | Images | Instances | | P | R | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|---|---|---|
| Test (held out) | 150 | 3,930 | **Box** | 0.7666 | 0.7751 | **0.8100** | 0.3411 |
| Test (held out) | 150 | 3,930 | **Mask** | 0.6270 | 0.6339 | **0.6383** | 0.2238 |
| Validation | 150 | 3,807 | **Box** | 0.7690 | 0.7730 | **0.8250** | 0.3530 |
| Validation | 150 | 3,807 | **Mask** | 0.6100 | 0.6490 | **0.6520** | 0.2310 |

**Pre-registered bar (`T0.6` §2): box ≥ 0.75 PASS · mask ≥ 0.65 FAIL (0.6383, short by
0.0117). The bar was NOT adjusted.** This model was nonetheless **adopted as the Stage-1
default on 27 Aug 2026 by an explicit human decision**, on the strength of the box result
alone — **+2.76 points over the superseded detector (0.8100 vs 0.7824)**, same frozen split,
otherwise identical config. Adoption ≠ the bar being met; both facts are recorded.
`RESULTS_LOG.md` 2026-08-27b, 2026-08-27d.

**Because the mask bar was missed, this model is used for its BOXES ONLY and R2 (mask-aware
cropping) stays UNWIRED** — that floor existed to protect R2, and nothing has changed it.

✅ **Re-measured 27 Aug 2026 on this seg detector** (`DENTEX/disease/` fetched locally, with a
same-machine control run of the old bbox detector first). Stage-1 recall **67.3% → 70.6%**,
Stage-2 FDI exact end-to-end **46.3% → 58.3%** — full table in the Stage 2 section below,
`RESULTS_LOG.md` 2026-08-27e. The earlier "figures are STALE / `run_inference.py` emits them as
`null`" note is retired.

Note the 3,930-vs-3,924 instance difference below makes the box comparison near-, not exactly,
like-for-like.

⚠️ An earlier R1 run (26 Aug) was **withdrawn** — its masks were misaligned by two data
defects. Nothing from it is reported here. `RESULTS_LOG.md` 2026-08-27a.

**Ground-truth caveat (found 21 Aug 2026, numbers above unchanged):** the instance counts in
this table are the counts the model was actually scored against, but the Tufts source data
holds **66 more annotated teeth** than this dataset contains — objects with a corrupt
`bounding box` field (1×1 / 1×2 px) but an intact full-size polygon, dropped by the
converter's degenerate-box guard. Test ground truth is therefore 3,924 of 3,930 real
instances (0.15% missing); val is 3,794 of 3,807. Too small to move mAP@0.5 = 0.7824
materially, and the numbers above are **not** being restated — but the R1 seg dataset keeps
all 66, so its instance counts will legitimately differ. Analysis:
`docs/research/T0.6_detector_reconciliation.md` §3.5; paper framing: `PAPER_MATERIAL.md` §8.9.

---

## Stage 2 — FDI numbering · learned enumeration head · ResNet18 + positional features

### Current — with the seg detector (re-measured 27 Aug 2026)

Same 164 leak-free `DENTEX/disease/` images, 936 GT teeth, same conf 0.25 / NMS IoU 0.50 /
imgsz 1024 / CCW rotation, same head v2.0. Only the detector changed. `RESULTS_LOG.md`
2026-08-27e.

| Metric | bbox detector (control re-run) | **seg detector (current)** | Δ |
|---|---|---|---|
| Detection recall | 67.3% (630/936) | **70.6%** (661/936) | **+3.3 pp** |
| FDI exact (of detected) | 68.7% | **82.6%** | **+13.9 pp** |
| Quadrant correct (of detected) | 94.6% | **97.6%** | +3.0 pp |
| Right quadrant, off-by-one | 22.7% | **13.5%** | −9.2 pp |
| **FDI exact, end-to-end** | 46.3% | **58.3%** (546/936) | **+12.0 pp** |
| Duplicate FDI codes | 0 | **0** | — |
| Mean detections/image | 23.7 | **22.0** | −1.7 |

**The gain is much larger than the recall change alone explains.** Detections per image went
*down* (23.7 → 22.0) while recall went *up* — the seg detector emits fewer spurious boxes, and
since every spurious box perturbs the Hungarian one-to-one assignment across a whole quadrant,
cleaner boxes lift FDI-exact-of-detected by 13.9 points on top of the recall gain.

> **Reproduction caveat, stated rather than hidden:** the control re-run of the *bbox*
> configuration on this machine gave **67.3% / 46.3%**, against the **67.0% / 46.5%** originally
> published — a ~3-tooth drift, consistent with CPU-vs-GPU float differences and inside the
> ~1-point run-to-run noise floor already measured here (identical configs once differed by 9
> teeth of 936, `RESULTS_LOG` 2026-08-25i). The +12-point gain is an order of magnitude larger
> than that drift, so it is not an artefact of it — but the control is **not** an exact
> reproduction and is not presented as one.

### Lever 1 — multi-corpus detector retrain (1 Sep 2026) — **ABLATION, NOT adopted**

Detector re-trained on Tufts + DENTEX `quadrant_enumeration` (`models/13_detector_multicorpus_lever1/`,
`RESULTS_LOG` 2026-09-01h, pre-registered). Two arms + a same-day control, primary = FDI exact
end-to-end on the 164 leak-free DENTEX images, guard = Tufts frozen **test** box mAP@0.5 ≥ 0.75.

| arm | detector train set | recall | of-detected | **end-to-end** | Tufts test box mAP@0.5 |
|---|---|---|---|---|---|
| Control A (deployed seg) | Tufts seg (frozen) | 0.708 | 0.825 | **0.5844** | **0.810** |
| Control B | Tufts detect | 0.831 | 0.724 | 0.6015 | 0.724 |
| **Arm** | Tufts + DENTEX detect | 0.995 | 0.939 | **0.9338** | **0.647** |

Paired cluster bootstrap over the 164 images (10k, seed 42): **Arm − Control A Δ end-to-end
+34.9 pp [+30.8, +39.0]**; Arm − Control B +33.2 pp [+29.5, +37.0] (the pure data effect);
Control B − Control A +1.7 pp [−3.4, +6.8] (**n.s.** — seg→detect head change does nothing).

**Verdict (pre-registered rule, bar not moved): primary SUCCEEDS, guard FAILS (0.647 < 0.75)
→ ABLATION.** Pipeline default detector stays `tooth-detector-seg-tufts-1024-v1.0`. The guard
failure is the pre-registered "domain dilution" risk, confirmed: adding DENTEX costs Tufts test
box mAP ~7.7 pt. **The 93.4% is an in-domain number** (DENTEX-trained detector + DENTEX+Tufts
head, on held-out DENTEX; leakage ruled out three ways) — it confirms that the 58.3% headline is
**detector-domain-limited, not numbering-limited**, but it is not the same generalisation
scenario as the cross-domain 58.3% and must not be quoted as if it were.

---

### Historical — the three-head comparison, all on the SUPERSEDED bbox detector

> ⚠️ The table below predates the 27 Aug detector swap. Its absolute numbers are superseded by
> the table above. The per-head comparisons remain valid **relative to each other**, since all
> three columns used the same detector.

**Method as of 22 Aug 2026.** Evaluated on **164 leak-free `DENTEX/disease/` images**
(936 FDI-labelled teeth) with detector boxes (`tooth-detector-a100-1024-v1.0` — the superseded
detector, imgsz 1024, conf 0.25, NMS IoU 0.50, rotated 90° CCW), Hungarian one-to-one
assignment over the 32 codes.

**86 of the original 250 images are excluded as training duplicates** — 85 byte-identical to
enumeration-head training images, 1 to a detector training image. An earlier version of this
table reported 52.2% on the contaminated 249-image set; that figure was inflated by 5.7 points
and is withdrawn. Exclusion list: `data/dentex/disease_leaked_images.json`.

| Metric | Positional (superseded) | Head v1.0 (DENTEX) | **Head v2.0 (DENTEX+Tufts)** |
|--------|------------------------|--------------------|------------------------------|
| Detection recall | 67.0% | 67.0% | 67.0% |
| Quadrant correct (of detected) | 92.3% | **94.7%** | 94.1% |
| FDI exact (of detected) | 34.1% | **69.4%** | 69.5% |
| **FDI exact, end-to-end** | 22.9% | **46.5%** | **46.6%** |
| Duplicate FDI codes | 0 | **0** | **0** |

**v2.0 is the current deployed head (26 Aug 2026). It was adopted for ROBUSTNESS, not
in-domain accuracy — do not quote it as an accuracy improvement.** In-domain it is +0.11pp,
which is inside the ~1-point run-to-run noise floor (two *identical* configurations differed
by 9 teeth of 936, RESULTS_LOG 2026-08-25i). What it buys is the second column below.

**Cross-domain, crop-level, GT boxes, plain argmax** (`scripts/eval/crop_eval.py` — not
comparable to the end-to-end table above, but comparable *across heads* within each row):

| Head | DENTEX val (2,729 crops) | Tufts test (3,786 crops) |
|---|---|---|
| v1.0 — DENTEX only | 91.6% | 50.0% |
| **v2.0 — DENTEX + Tufts** | 91.0% | **71.5%** |
| *(rejected)* Tufts only | — | 71.8% (but **37.4%** end-to-end on DENTEX) |

A Tufts-only head was trained and rejected: it is not significantly better than v2 on Tufts
(McNemar p=0.732) while losing 9.1 points on DENTEX (p=4.7×10⁻¹¹). v2 strictly dominates it.
RESULTS_LOG 2026-08-25j. v1.0 weights are **retained unchanged** in
`models/08_fdi_enumeration_head/` and still hash-pinned — every Stage-2 number published
before 26 Aug 2026 was measured on v1.0.

**A 2.0× improvement on both measures**, on data the head has never seen.

**It clears the positional ceiling decisively.** On teeth in complete (8-detection)
quadrants — the population where rank-order assignment is at its best — positional reaches
**66.3%** and the head **80.2%**, a margin of **+13.9 points** (n=101, same population for both).
The head wins in **every** completeness bucket. An order-independent method exceeds what
rank-order can reach, and not marginally.

> Corrected 24 Aug 2026. This was previously quoted as a 67.0% ceiling and a +2.4-point margin.
> **67.0% is the detector's recall, not the ceiling**, and the +2.4 compared the ceiling
> (complete quadrants only) against the head's accuracy over all detected teeth — two different
> populations. See RESULTS_LOG 2026-08-24a; recompute with
> `scripts/eval/analyze_stage2_ceiling.py`.

**End-to-end is capped by Stage 1.** At 67.0% recall, perfect numbering gives 67.0%; the head
reaches 69.4% of that maximum. Detector recall is now the binding constraint.

One-to-one ablation (clean 164-image set, 24 Aug 2026): plain argmax emits **679 anatomically
impossible duplicate codes** and scores 65.1% / 43.6%; Hungarian one-to-one removes **all** of
them for **69.4% / 46.5%** — **+4.3 points of-detected, +2.9 end-to-end** — at a cost of 2.1
points of raw quadrant accuracy (94.7% vs 96.8%), because the global constraint sometimes moves
a tooth across a quadrant boundary. Supersedes the contaminated-set figures.

**Input ablation** (val, 2,729 crops, `scripts/eval/ablate_head_inputs.py`) — quadrant split
into jaw and side, since *side* is the laterality claim:

| Condition | jaw | side (laterality) | position | FDI exact |
|---|---|---|---|---|
| full | 99.9% | **99.5%** | 92.1% | 91.6% |
| positional features → mean | 99.9% | **96.3%** | 92.1% | 88.8% |
| positional features shuffled | 99.8% | **76.6%** | 92.2% | 70.8% |

Positional features are worth **+3.2 points of laterality / +2.8 FDI exact** — not the decisive
signal earlier docs claimed, since the image alone recovers laterality at 96.3%. The image *is*
decisive for the **position digit**. Feeding *shuffled* coordinates costs 22.9 points, but that
is a worst case that does not occur: a shuffle teleports the coordinate to another tooth, often
across the midline. **Realistic box error is a small local jitter and costs ~nothing** — ±15% of
box size leaves FDI exact unchanged to 0.1pp, ±100% costs 0.2pp (RESULTS_LOG 2026-08-24e).
RESULTS_LOG 2026-08-24c.

Training-time val (GT boxes, **selection-biased — a diagnostic, not a result**): quadrant
99.4%, position 92.1%, FDI exact 91.6%; per-position accuracy 0.886–0.963, essentially flat,
unlike the detector's collapse from 98.3% (position 1) to 61.0% (position 8).

Weights **frozen and tracked**: `models/08_fdi_enumeration_head/`, tag
**`fdi-enumeration-head-resnet18-v1.0`**, SHA-256
`e6abf1cd959c36824ef0061db84a5fbc8793af314099cb3cc72027662445cc5a`. That directory also holds
the training config and per-epoch log, the full 33,461-row crop manifest, both evaluation
summaries and the leakage exclusion list. Figures: `docs/results/figures/enumeration_head/`.
Full record: `RESULTS_LOG.md` 2026-08-22i and **22j (the leakage correction)**.

---

## Stage 3 — Caries cascade · ResNet18 · DENTEX

**Phase 1 gate (caries vs no_caries) — `caries-gate-resnet18-v3.0`, pipeline default.**
Retrained 25 Aug 2026 with a rebuilt negative class (5,366 real healthy teeth, MD5-joined
from DENTEX's enumeration and disease subsets — RESULTS_LOG 2026-08-25a). Both T0.1 arms now
exist; arm B is frozen as the shipped model (val macro-F1 selected it, narrowly):

| | val macro-F1 | test macro-F1 | test caries P/R/F1 | test no_caries P/R/F1 |
|---|---|---|---|---|
| Arm A (no augmentation) | 0.7210 | 0.7212 | 0.47 / 0.62 / 0.54 | 0.93 / 0.88 / 0.91 |
| **Arm B (augmented, frozen)** | **0.7350** | 0.6948 | 0.40 / 0.74 / 0.52 | 0.95 / 0.81 / 0.87 |

**The A/B gap is not a finding.** Both arms swing ~0.27 in val macro-F1 across their own 15
epochs; the between-arm gap is 0.014–0.026 — 10–20&times; smaller than that noise floor.
Do not read this as "augmentation helps/hurts" (RESULTS_LOG 2026-08-25b).

**In-pipeline effect, same 12 images/detector/boxes, only the gate swapped**
(`scripts/eval/compare_caries_gates.py`): caries rate **84.9% &rarr; 19.1%** against an 11.7%
annotated floor (7.3&times; &rarr; 1.6&times; over-call). **Improved, not solved** — precision
0.40 means roughly six of ten positives are still wrong, and the healthy class rests on
presumed-negative labelling (RESULTS_LOG 2026-08-25a).

Weights: `models/09_caries_gate_v3/caries_gate_v3.pth` (gitignored, 43 MB — see
`docs/EXTERNAL_DRIVE.md`), sha256 `8f4a99ba412c…`, verified loadable and reproduced live
through `scripts/run_inference.py` (not just structurally checked).

**Where the 0.398 precision goes — stratified by tooth type (31 Aug 2026).** Held-out test, 863
crops, shipped v3.0 gate at its 0.50 operating point. `scripts/eval/caries_position_bias.py`;
full reading in `PAPER_MATERIAL.md` §8.24.

| tooth type | n | pos | precision | recall | FP rate | mean P(caries) on *healthy* | train base rate | within-type AUC |
|---|---|---|---|---|---|---|---|---|
| incisor | 266 | 8 | 0.091 | 0.125 | 0.039 | 0.075 | 0.017 | 0.681 |
| canine | 129 | 5 | 0.333 | 0.200 | 0.016 | 0.087 | 0.023 | 0.748 |
| premolar | 221 | 31 | 0.292 | 0.677 | 0.268 | 0.273 | 0.157 | 0.781 |
| molar | 247 | 83 | 0.473 | 0.855 | **0.482** | **0.478** | **0.343** | 0.781 |

**The gate's score on genuinely healthy teeth tracks the training base rate for that position** —
48.2% of healthy molars are flagged (79 of the 142 false positives), while only 1 of 8 incisor
lesions is found. Real lesion signal nonetheless survives removing the prior: **within-type AUC
0.7454 [0.6604, 0.8420]**, against a position-only baseline at AP 0.2962 and the model's 0.5503.

**FIVE attempted fixes, none adopted, all reported.** Primary metric throughout is **average
precision** on the 863-crop test split — threshold-independent, so it distinguishes "the curve
lifted" from "the operating point slid". Paired cluster bootstrap over the 34 source images.

| attempt | AP | ΔAP vs control | verdict |
|---|---|---|---|
| shipped v3.0 / same-day control | 0.5503 | — | — |
| per-tooth-type thresholds | — | F1 +0.006 [−0.034, +0.041] | n.s. |
| **v4 — 2.67× the positives** | 0.5496 | −0.0015 [−0.0886, +0.0821] | n.s. |
| **CLAHE** | 0.5977 | **+0.0488 [−0.0031, +0.0993]** | **misses by 0.0031** |
| crop expand 1.25× | 0.5684 | +0.0198 [−0.0367, +0.0810] | n.s. |
| position-balanced sampling | 0.5943 | +0.0432 [−0.0328, +0.1157] | n.s. |

Bars pre-registered before each run (`outputs/caries_arms/PRE_REGISTRATION.md`) and **not moved**.
One real secondary effect: **CLAHE gains precision +5.6 pp [+0.011, +0.101] with no significant
recall cost.** The experiment is underpowered — 863 crops but only **34 source images** — so a
+0.049 AP effect cannot be separated from zero. `outputs/caries_v4/`, `outputs/caries_arms/`.

⚠ **Two numbers here that must not be quoted as improvements.** (1) v4's own report shows P 0.71 /
R 0.80 on *its own* test split — a 2.2× prevalence difference, not a gain; specificity is unchanged
(0.853 vs 0.843). (2) The 1.25× arm's precision gain is offset by a *real* recall loss
(−0.079 [−0.157, −0.008]) — a slide along an unchanged curve.

**Phase 2 severity (caries vs deep_caries), validation, 133 crops — unchanged, still
`phase1_legacy`-era:**

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|----|---------|
| caries | 0.94 | 0.80 | 0.87 | 101 |
| deep_caries | 0.57 | 0.84 | 0.68 | 32 |
| **Accuracy** | | | **0.81** | 133 |
| **Macro F1** | | | **0.77** | |
| Weighted F1 | | | 0.82 | |

**Weights: `models/07_caries_cascade/phase2_final_bundle.pth`, version tag
`caries-cascade-resnet18-v1.0`.** Loaded and reproduced live via `run_inference.py`
(`DEF_CARIES_SEVERITY`) — the "structurally only, no torch available" caveat that used to sit
here no longer applies; this machine's environment was fixed 24 Aug 2026. Still trained on
`phase1_legacy`-era crops and not re-run this session — **only the gate was rebuilt**, not the
severity head. Validation-only; no held-out test split for Phase 2 exists yet.

---

## Stage 4a — Bone loss binary · ResNet18 + Focal Loss · Tufts

Frozen and tagged 27 Aug 2026 as `bone-loss-binary-resnet18-v1.0`, SHA-256
`c52f7f484076a2a2c3c144c3351912b118b6b0d56fc51ba1b4296e6ce6213db1`
(`bone_loss_resnet18_best.pth`, the pipeline default — `bone_loss_resnet18_final.pth` is a
different file and is **not** used). Class order is `[normal, bone_loss]`, confirmed two
independent ways — `models/03_.../run_summary.txt`.

Validation, 1,558 crops at real-world prevalence (1,499 normal / 59 diseased).

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Macro F1 | **0.9233** | ≥ 0.72 | PASS |
| F1 normal (class 0) | 0.9943 | ≥ 0.75 | PASS |
| F1 diseased (class 1) | 0.8522 | ≥ 0.70 | PASS |
| Precision / Recall diseased | 0.8750 / 0.8305 | — | — |
| Sensitivity | 83.05% | — | — |
| Specificity | 99.53% | — | — |
| Accuracy | 98.91% | — | misleading at 4% prevalence |

Confusion matrix: TN 1,492 · FP 7 · FN 10 · TP 49.

---

## Stage 4b — Bone loss severity 3-class · ResNet18 + Focal Loss · Tufts

Frozen and tagged 27 Aug 2026 as `bone-loss-severity-resnet18-v1.0`, SHA-256
`fa93a5201833d8137bd2ae328d3afd63c2c1f9e4ac82a621d1b430a51eba8a4a`. Class order
`[Mild, Moderate, Severe]` — `models/04_.../run_summary.txt`.

Validation, 52 crops. **Low support — treat as provisional.**

| Class (overlap ratio) | Precision | Recall | F1 | Support |
|-----------------------|-----------|--------|----|---------|
| Mild (≤ 0.05) | 1.00 | 0.67 | 0.80 | 6 |
| Moderate (0.05–0.15) | 0.80 | 0.57 | 0.6667 | 28 |
| Severe (> 0.15) | 0.57 | 0.89 | 0.6957 | 18 |
| **Macro F1** | | | **0.7208** | 52 |

Accuracy 69.23%. Target macro F1 0.72 — met by 0.0008 on 52 samples.

---

## Exploratory — CEJ bone level estimation (classical CV, not in pipeline)

| Metric | Value |
|--------|-------|
| Crops processed | 296 / 296 (100% completion, **not** accuracy) |
| Flagged reliable | 185 (62.5%) |
| Exact agreement with overlap-based severity | **15.1%** |
| Agreement within ±1 class | 61.6% |

Not integrated. Reported as a negative result.

---

## Stages 5–6 — Pipeline integration + report

**Implemented 24 Aug 2026** (`scripts/run_inference.py`, RESULTS_LOG 2026-08-24f — R4, paper
claim C3). Image in, per-tooth JSON + overlay out, through all six stages.

**In-pipeline batch result, 12 leak-free DENTEX images, 299 detected teeth:**

| | |
|---|---|
| Caries-positive (pipeline default, v3 gate) | 57 (19.1%), was 254 (84.9%) pre-fix |
| Bone-loss-positive | 2 (0.7%) — near-inert off-Tufts, domain shift |
| Duplicate FDI codes | 0 / 299 |

**Lesion-localisation agreement — 25 Aug 2026** (`scripts/eval/lesion_localization.py`,
RESULTS_LOG 2026-08-25c), 164 leak-free images: of 479 real çürük (caries) lesions,
**212 of 479 have a predicted-diseased tooth spatially overlapping them — 44.3%**
(re-measured 27 Aug 2026 on the seg detector; the old detector scored 42.0% in a same-machine
control, and 42.6% was the 25 Aug published figure). Predicted-positive teeth *fell* 773 → 755
while correct localisations *rose* 201 → 212. `RESULTS_LOG.md` 2026-08-27i. This is a
tooth-level correspondence check (the pipeline has no finer localisation than "which tooth"),
not a pixel-level segmentation-quality metric. Built against DENTEX first specifically so it
generalises to Ningxia's masks later without new code under deadline pressure — see
`PAPER_MATERIAL.md` §8.11 for the full scoping and caveats.

Both are pure inference; neither needed a GPU rental.

---

## C1 — VLM baseline (27 Aug 2026)

Tooth-level caries: predict the set of carious FDI codes per image, 164 leak-free DENTEX images,
one scorer for both arms. Image-level yes/no was rejected as degenerate (90.2% of images contain
caries).

| Arm | P | R | **F1** | latency |
|---|---|---|---|---|
| **Our six-stage pipeline** | 0.235 | 0.390 | **0.294** | 2.39 s/img (CPU) |
| Constant `{26,36}` — image ignored | 0.250 | 0.172 | **0.204** | 0 |
| Qwen2.5-VL-7B-Instruct, zero-shot | 0.236 | 0.103 | **0.143** | 1.08 s/img (A100) |

**The VLM scores below a constant guess.** Blank and random-noise images elicit the same confident
answer; only 6 distinct answers across 164 radiographs. **Never quote 0.143 without that control.**
Efficiency: 8.29 B params / 18.01 GB VRAM vs **61.2 M** params on CPU (caries path; 83.6 M all
six models — counted 28 Aug 2026, superseding "~25 M", which was the detector alone).
`RESULTS_LOG.md` 2026-08-27aa, 2026-08-28.

---

## Confidence intervals (added 27 Aug 2026)

**Cluster bootstrap over images**, 10,000 resamples, seed 42 — `scripts/eval/bootstrap_ci.py`.
Resampling images rather than teeth because teeth within a radiograph are not independent; a
tooth-level bootstrap would report intervals far too narrow.

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

**Paired deltas for the 27 Aug detector swap** (same resampled images, both arms):

| Paired delta (seg − bbox detector) | Point | 95% CI | Verdict |
|---|---|---|---|
| **FDI exact, end-to-end** | **+12.1 pp** | **[+6.8, +17.2]** | **excludes 0 — real** |
| **Caries agreement, Ningxia pooled** | **+7.7 pp** | **[+3.3, +12.0]** | **excludes 0 — real** |
| Detection recall | +3.3 pp | [−1.5, +8.0] | **INCLUDES 0 — not significant** |
| Lesion agreement (DENTEX internal) | +2.3 pp | [−3.4, +7.9] | **INCLUDES 0 — not significant** |

⚠️ **Two deltas reported earlier on 27 Aug do not survive their intervals** — detection recall
(+3.3 pp) and DENTEX-internal lesion agreement (+2.3 pp) both have CIs spanning zero and must not
be quoted as improvements. The end-to-end and external-caries gains do survive.
**Not yet covered:** Ningxia periodontitis (no per-image counts stored) and detection mAP / the two
ResNet18 classifiers (no per-item dumps). `RESULTS_LOG.md` 2026-08-27p.

---

## External validation (C2) — Ningxia, 4 hospitals · re-measured 27 Aug 2026

> **Current numbers are the 27 Aug re-run on the seg detector + FDI head v2.0**
> (`RESULTS_LOG.md` 2026-08-27h). The 25 Aug figures below the fold were measured on the
> superseded bbox detector + head v1.0 and are retained for comparison, not as current.
> A control on the old pair was re-run on the same machine first and reproduced 25 Aug, so the
> deltas are attributable to the models.

**Caries — focal-lesion centroid containment** (denominator is GT-derived, model-independent):

| Split | Centre | Lesions | 25 Aug (old det) | **Current (seg det)** | Δ |
|---|---|---|---|---|---|
| test1 | cross-centre | 316 | 26.6% | **28.8%** | +1.6 pp |
| test2 | same-centre-as-*Ningxia*-train | 349 | 43.3% | **51.3%** | +8.0 pp |
| test3 | cross-centre | 162 | 37.0% | **40.1%** | +4.9 pp |
| test4 | cross-centre | 186 | 22.6% | **41.9%** | +19.9 pp |
| *(pooled, scale only)* | | 1,013 | 33.3% | **40.8%** | **+7.7 pp** |

Improved on all four hospitals. **No caries model changed** — only the detector. With the
internal figure also re-measured on the seg detector (44.3%, above), **the internal/external gap
has more than halved:**

| | internal (DENTEX) | external (Ningxia, pooled) | gap |
|---|---|---|---|
| old detector (control) | 42.0% | 33.1% | **8.9 pp** |
| **seg detector** | **44.3%** | **40.8%** | **3.5 pp** |

Much of what read as caries domain shift was a detection problem. **Not** grounds for saying
caries generalises well: 40.8% is still weak in absolute terms and three of four hospitals sit
below the internal figure.

**Periodontitis — affected-tooth sensitivity: UNCHANGED by the detector swap.**
2.7% → 2.4% pooled; the pipeline flagged 168 affected teeth before and 165 after while the
denominator grew 9%. Per-split 2.4 / 1.4 / 5.6 / 4.6% (was 3.7 / 0.8 / 1.5 / 5.4%), moving in
both directions; test3's rise is 4 → 23 teeth on 50 images and is noise. ⚠️ This metric's
denominator is **model-dependent** (affected teeth are counted from detected boxes), so it is
not a plain sensitivity delta. The bone-loss branch's domain-shift failure is unmoved.

---

### Superseded — the 25 Aug measurement (old bbox detector + FDI head v1.0)

**Zero leakage** against Tufts, DENTEX `disease/`, `quadrant_enumeration`,
`quadrant-enumeration-disease` and `quadrant` — each checked separately (0 / 2,912 unique
Ningxia test hashes). LOCKED data: evaluated once, no tuning of any kind against it.

**Caries — focal-lesion centroid containment, stratified (never pooled):**

| Split | Centre | Lesions | Covered | Strict (1:1) |
|---|---|---|---|---|
| test1 | cross-centre | 316 | **26.6%** | 23.7% |
| test2 | same-centre-as-*Ningxia*-train | 349 | **43.3%** | 36.4% |
| test3 | cross-centre | 162 | **37.0%** | 29.0% |
| test4 | cross-centre | 186 | **22.6%** | 18.8% |

DENTEX internal was 42.6%; Ningxia sits at or below it across four independent hospitals.
*All four splits are equally external to us* — we never trained on Ningxia, so "same-centre-as-train"
describes Ningxia's own split design, not proximity to our training data.

**Periodontitis — affected-tooth sensitivity** (of teeth ≥50% inside the expert-marked region,
how many were flagged): test1 3.7%, test2 0.8%, test3 1.5%, test4 5.4% (pooled 172/6,222 = 2.8%).
Combined with Tufts in-domain (0.92 macro-F1) and DENTEX (0.7% firing), the bone-loss branch's
domain-shift failure is now measured on **two** independent external datasets.

**Specificity/AUC are not computable on Ningxia** — it has no healthy controls. They come from
Tufts. See `PAPER_MATERIAL.md` §8.12 for the withdrawn first-pass periodontitis figures and why
the metric had to differ by category.

## Constant-baseline vs pipeline — all three caries cohorts (1 Sep 2026)

Focal-lesion **centroid containment**, one matcher (`ningxia_external.match_by_centroid`) shared
by every row. Paired cluster bootstrap over images, 10,000 resamples, seed 42.

| cohort | n | pipeline | constant | constant − pipeline | verdict |
|---|---|---|---|---|---|
| DENTEX (internal) | 164 img / 479 lesions | 0.443 | 0.488 | +0.046 [+0.006, +0.089] | constant wins |
| Ningxia, 4 hospitals | 337 img / 1,013 lesions | 0.408 | 0.399 | −0.009 [−0.049, +0.030] | indistinguishable |
| **CariesXrays** | **1,500 img / 3,421 lesions** | **0.309** | **0.561** | **+0.252 [+0.232, +0.273]** | **constant wins decisively** |

Frozen pipeline throughout — nothing trained, no checkpoint changed. CariesXrays is the largest
cohort in the project by lesion count (more than DENTEX and Ningxia combined). Mechanism measured:
**72.0% of its lesions are on molars and 60.2% on exactly the eight constant teeth**, against the
constant's ~0.60 structural ceiling. Unlike DENTEX, the brute-force defence fails — the constant
flags 64% more teeth *and* has the higher match rate (0.207 vs 0.190). 22.1% of lesions fall
inside no detected tooth, bounding every tooth-level arm here.

**CariesXrays is a peer-reviewed public benchmark** — Chen et al., *CariesXrays: Enhancing Caries Detection in Hospital-Scale Panoramic Dental X-rays via Feature Pyramid Contrastive Learning*, **AAAI 2024**, 38(20) 21940–21948, DOI 10.1609/aaai.v38i20.30196 — verified against AAAI OJS, ACM DL and DBLP. 6,000 images matches their count exactly; 13,784 non-degenerate boxes vs their stated 13,783 is a +1 convention difference. Licence not stated. Leakage verified three ways (0 MD5 vs all corpora; positive control at distance 0; 1.5M-pair distribution).
`RESULTS_LOG.md` 2026-09-01, `PAPER_MATERIAL.md` §8.25, `outputs/cariesxrays_external_rand/`.

## C4 — abstention / coverage-accuracy (28 Aug 2026)

Accuracy on retained predictions as the least-confident are declined. Threshold **not** tuned here.

| Coverage | Stage 2 - FDI numbering | Caries gate (calibrated) |
|---|---|---|
| 100% (no abstention) | 0.826 | 0.797 |
| 90% | 0.849 | 0.857 |
| 75% | **0.885** | **0.940** |
| 50% | 0.918 | 0.970 |
| gain at 75% coverage | **+5.91 pp [+3.88, +7.68]** | **+14.25 pp [+11.32, +16.63]** |
| same, confidences shuffled | +0.03 pp | +0.00 pp |

- Stage 2: 661 detected teeth, FDI exact match. Caries gate: 863 crops, isotonic-calibrated confidence.
- CIs are clustered bootstrap over **images**. "Shuffled" breaks the confidence-correctness link.
- Pre-registered `ASSESSABILITY_MIN_FDI_CONFIDENCE = 0.30` -> **90.8% coverage at 0.847**.
- Stage-2 coverage is over *detected* teeth: 75% coverage = **53.0% of teeth actually present**.
- Source: `outputs/c4_abstention/c4_coverage_accuracy.json`.

## C1 hardened — all arms, one scorer (28 Aug 2026)

164 leak-free DENTEX images, 477 affected teeth. Tooth-level caries FDI-set micro P/R/F1.

| System | P | R | **F1** | params | hardware |
|---|---|---|---|---|---|
| **Held-out constant** `{16,17,26,27,36,37,46,47}` — **image never read** | 0.218 | 0.600 | **0.320** | 0 | none |
| Our six-stage pipeline | 0.235 | 0.390 | **0.294** | 61.2 M | CPU, 2.39 s/img |
| Qwen2.5-VL-32B-Instruct, zero-shot | 0.250 | 0.243 | **0.246** | 33.45 B | H100, 70.1 GB, 1.46 s/img |
| Qwen2.5-VL-7B-Instruct, zero-shot | 0.248 | 0.107 | **0.149** | 8.29 B | H100, 0.69 s/img |
| Qwen2.5-VL-7B, **2-shot** | 0.196 | 0.040 | **0.066** | 8.29 B | H100, 1.93 s/img |
| Qwen2.5-VL-7B, **4-shot** | 0.150 | 0.019 | **0.034** | 8.29 B | H100, 3.36 s/img |

- **The held-out constant is image-blind and beats the pipeline.** Fitted on the 78 leakage-excluded
  images (overlap with scored set = 0), frozen, then applied. A test-fitted *oracle* constant
  reaches 0.330 and is not claimable.
- Few-shot exemplars come only from leakage-excluded images. Empty predictions 56 -> 113 -> 123.
- Controls: 7B blank/noise both -> `26,36`; 32B blank -> `NONE`, noise -> full molar list.
- transformers 5.16.1 for all 28 Aug arms; the 27 Aug 7B run (F1 0.143) did not record its version.
- Source: `outputs/c1_vlm/`, `RESULTS_LOG.md` 2026-08-28b, `PAPER_MATERIAL.md` §8.22.

## Stage-2 head v3 — three corpora (28 Aug 2026, ABLATION not default)

| corpus (split) | n | v2 control | v3 | delta | 95% CI | verdict |
|---|---|---|---|---|---|---|
| **DENTEX** val | 2,729 | 91.4% | **92.5%** | **+1.14 pp** | [+0.33, +1.95] | **significant** (p=0.013) |
| **Tufts** test | 3,786 | 75.0% | 75.8% | +0.74 pp | [-0.37, +1.89] | **not significant** (p=0.25) |
| **Kaggle** test | 1,994 | 77.7% | **93.2%** | +15.45 pp | [+12.79, +18.28] | significant, but see below |

- Control = `models/12a_fdi_head_v2_control_rebuilt`, trained the same day on the same rebuilt
  DENTEX+Tufts crops; it reproduces published v2 within ~1 pp (FDI exact 0.821 vs 0.810).
- The **Kaggle cell is not a generalisation result** — v3 trained on that corpus.
- Pooled val (v3 0.855 vs control 0.821) is **not comparable**: different val mixtures.
- Pipeline default remains **v2.0** (`models/10_fdi_head_dentex_tufts_v2`).
- Source: `models/12_fdi_head_v3_3corpus/run_summary.txt`, `RESULTS_LOG.md` 2026-08-28c.

---

## Pipeline size — parameter counts per stage (28 Aug 2026)

Counted with `torch.load` over the six checkpoints, summing `numel()`. Recorded here
because the manuscript cites it and because a wrong version of this number propagated
through nine places in the docs before it was caught (`RESULTS_LOG.md` 2026-08-28).

| Stage | Model | Checkpoint | Parameters |
|---|---|---|---|
| 1  | YOLOv11l-seg | `models/11_yolo_seg_tufts_r1/best.pt` | 27,617,459 |
| 2  | ResNet18 + 4 positional feats | `models/10_fdi_head_dentex_tufts_v2/` | 11,197,536 |
| 3a | ResNet18 caries gate | `models/09_caries_gate_v3/` | 11,187,158 |
| 3b | ResNet18 caries severity | `models/07_caries_cascade/` | 11,187,158 |
| 4a | ResNet18 bone-loss gate | `models/03_bone_loss_model_training_notebook_models/` | 11,187,158 |
| 4b | ResNet18 bone-loss severity | `models/04_bone_loss_severity_notebook_models/` | 11,187,671 |
| | **Total, all six** | | **83,564,140** |
| | **Caries path only** (1, 2, 3a, 3b) | | **61,189,311** |

**Do not quote "~25 M" for the pipeline.** That is the *superseded bbox* detector's own
count (`tooth-detector-a100-1024-v1.0`, 25.3 M, recorded under Stage 1 above); the current
seg detector is 27.6 M and the pipeline is not one model. The efficiency comparison against
Qwen2.5-VL-32B-Instruct is 33.45 B vs 61.2 M — roughly 550x, in the VLM's disfavour.
