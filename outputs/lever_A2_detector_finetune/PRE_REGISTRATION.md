# Pre-registration — Lever A2: can a target-domain fine-tune recover the Tufts benchmark without losing the multi-corpus gains?

**DRAFT written 4 September 2026.** Bars are open to **one review round** with the user/mentor,
then frozen. **No GPU is rented until this file is committed as frozen.**

Follow-up to Lever A (`outputs/lever_A_multicorpus_detector_v2/`, `RESULTS_LOG` 2026-09-03 + 03b +
03c + 2026-09-04). Lever A pooled 4 corpora, doubled DENTEX end-to-end FDI (+34 pp) and lifted
every external cohort (+6 to +19 pp), but **failed its pre-registered Tufts guard** — Tufts frozen
test box mAP@0.5 fell 0.724 → 0.585. Phase 0 (`TUFTS_GUARD2_DIAGNOSIS.md` §1.4b, `RESULTS_LOG`
2026-09-04) diagnosed the failure precisely: **not localisation** (matched-pair IoU flat across a
confidence sweep), **not box convention** (tested and refuted), but a **confidence-calibration
collapse on the minority domain** — with Tufts at 33 % of training, the detector's confidence
score stops separating real Tufts teeth from spurious boxes, and mAP (a ranking metric) breaks.

---

## 1. The hypothesis

The multi-corpus **backbone learned good features** — at confidence 0.10 the multi-corpus arms
detect Tufts teeth as well as the Tufts-only control or better (Arm 4C recall 0.80 vs 0.77). What
degraded is the **detection head's calibration on Tufts**. So:

> **Freezing the multi-corpus backbone and fine-tuning only the neck + detection head on Tufts
> should re-specialise the Tufts confidence distribution — recovering Tufts box mAP toward
> Control B's — while the frozen backbone preserves the DENTEX and external-cohort gains that
> live in the shared features.**

If it works, the Lever 1 / A / A2 arc goes from "ablation" to "the domain tradeoff is not
fundamental — a pretrain-then-fine-tune pipeline serves both." If it fails, we learn *how*:
either the fine-tune recovers Tufts but erodes the external gains (the tradeoff survives even
fine-tuning — a stronger, more final §8.16), or it does not recover Tufts at all (the ceiling is
the box-vs-mask supervision gap, §8.9 — points at segmentation, which is **not** in scope here).

**What is ruled out and why:** post-hoc confidence recalibration (Platt / isotonic). mAP is
computed over the score *ranking*; a monotonic recalibration leaves mAP unchanged. The fix has
to be in the weights.

---

## 2. What Lever A2 is, and is not

**Is:** one training run — load `models/15_detector_multicorpus_leverA/arm3c_best.pt` (the frozen
3-corpus Lever A checkpoint, sha256 `5d301f13fb48da5c74e7ef01bd0f91226f9b6800cb433dee5aebc8f8db8f161e`),
freeze the backbone (`freeze=10`), fine-tune neck + head on the **Tufts-only** train list for 40
epochs at the canonical LR. Then the identical Lever A evaluation: primary + two guards.

**Is not:**
- a re-run of the 130-epoch multi-corpus pretrain — `arm3c_best.pt` already *is* the 3-corpus
  model, so A2 starts from it. (This is the only deviation from `TUFTS_GUARD2_DIAGNOSIS.md`
  §3 Phase 2a, which assumed a fresh pretrain; the checkpoint makes it redundant and ~₹150 cheaper.)
- a change to the deployed pipeline. The default detector stays `models/11` unless A2 passes
  **and** a separate mentor go/no-go clears the downstream re-run (§6).
- a hyperparameter search. One recipe, fixed below, not swept.
- a segmentation experiment (`TUFTS_GUARD2_DIAGNOSIS.md` §3 Phase 2b). If A2 fails, 2b is
  **post-submission** work, not a next step under the ISBI timeline.
- trained or tuned on Ningxia — ever (`MASTER_PLAN_2026H2.md` §4.1).

---

## 3. Training — fixed now

| item | value |
|---|---|
| start checkpoint | `models/15_detector_multicorpus_leverA/arm3c_best.pt` (sha256 `5d301f13…`) |
| train list | `data/detector_multicorpus_v2/train_tufts.txt` — **700 Tufts images** (identical to Lever A Control B's data) |
| val | `data/detector_multicorpus_v2/images/val` — 150 frozen Tufts val, canonical box count 3,794 |
| `freeze` | **10** (YOLOv11l backbone frozen; neck + detection head trainable) |
| `epochs` | **40** |
| `patience` | **12** (early-stop on Tufts-val mAP@0.5) |
| `warmup_epochs` | **1** |
| `lr0` / `lrf` | **0.001 / 0.01**, `cos_lr=True` (canonical — a frozen backbone removes the main forgetting risk, so the LR is not lowered) |
| everything else | **byte-identical to `scripts/yolo/train_multicorpus_detector_v2.py`**: `batch=32`, `imgsz=1024`, `seed=42`, `deterministic=True`, `optimizer=AdamW`, `momentum=0.937`, `weight_decay=0.0005`, `box=7.5`, `cls=0.5`, `dfl=1.5`, `hsv_v=0.2`, `degrees=10.0`, `translate=0.1`, `scale=0.2`, `fliplr=0.5`, `flipud=0.0`, `mosaic=0.0`, `mixup=0.0`, `copy_paste=0.0` |

Script: `scripts/yolo/train_a2_finetune.py` (a ~40-line companion to the Lever A trainer; the
config block above is copied from it verbatim). The Guard-2 Tufts-test `yolo val` runs on
`best.pt` immediately after training, same as Lever A.

**Rationale for the three changed knobs** (`freeze=10`, `epochs=40`, `patience=12`,
`warmup_epochs=1`), recorded so they are visibly *not* moved after seeing results:
- `freeze=10` — Phase 0 says the failure is head calibration, not features; freezing the
  backbone targets that and maximally protects the DENTEX/external gains.
- `epochs=40` / `patience=12` — a light fine-tune of an already-trained head on 700 images;
  40 gives room, patience 12 stops it when Tufts-val plateaus. Chosen once, not tuned.

---

## 4. Evaluation — frozen, identical to Lever A §5

All local CPU/MPS, no GPU. Reuses Lever A's Control A and Control B numbers and its eval scripts
(`models/15_detector_multicorpus_leverA/repro/{leverA_primary2,leverA_guard1,leverA_ningxia}.sh`,
`scripts/eval/score_leverA_arm.py`).

| criterion | measurement | comparator |
|---|---|---|
| **PRIMARY** | FDI exact **end-to-end** on the 164 leak-free DENTEX images, `method=head`, head=`models/10`, conf 0.25 / NMS IoU 0.50 / imgsz 1024 / CCW rotation. Paired cluster bootstrap over the 164 images, 10 000 resamples, seed 42. | **Control A** (deployed seg `models/11`, e2e 0.5844 — Lever A) |
| **GUARD 1** | Pooled external caries lesion agreement: Ningxia ×4 (1,013 lesions) + CariesXrays random-1500 seed 42 (3,421), **frozen** caries gate v3.0, A2 detector swapped in, everything else identical. Paired bootstrap over 1,837 images, 10k, seed 42. | **Control A** (pooled agreement 0.3313 — Lever A) |
| **GUARD 2** | A2 Tufts frozen **TEST** box mAP@0.5, measured on the GPU box (`yolo val` on `best.pt`, `test = test_tufts.txt`, 150 frozen Tufts images). | **Control B** (Tufts-only detect, 0.7243 — Lever A) |

---

## 5. Acceptance rule — fixed now, bar not moved after seeing any number

> **A2 is "adopt-worthy" IFF all three hold:**
> 1. **PRIMARY** — Δ e2e (A2 − Control A) 95 % CI **lower bound ≥ +5 pp**; AND
> 2. **GUARD 1** — Δ pooled external caries (A2 − Control A) 95 % CI **lower bound ≥ −2 pp**; AND
> 3. **GUARD 2** — A2 Tufts test box mAP@0.5 **≥ Control B − 4 pp = 0.6843**.
>
> This is the **identical Lever A rule**. `scripts/eval/score_leverA_arm.py` applies it
> (`--label a2`, `--guard2-arm <A2>`, `--guard2-controlB 0.7243`).

**"Adopt-worthy" is not "adopted."** If A2 is adopt-worthy, the paper reports its full 6-cohort
table as the recommended detector, but **wiring it into the pipeline default + the downstream
re-measurement (Stages 2–6 × 6 cohorts, ~1–2 weeks) is a separate, dated go/no-go with the
mentor, gated on the submission timeline.** This mirrors how Lever A was handled (2/3 → ablation,
default unchanged) and keeps the paper's schedule off the critical path of a single training run.

**Outcomes and how each is written — none is a failure to hide:**

| outcome | how it is reported |
|---|---|
| All three pass | New §: "the domain tradeoff is not fundamental — freezing the multi-corpus backbone and fine-tuning the head on the target domain recovers benchmark parity (Tufts 0.585 → ≥ 0.684) while keeping the DENTEX (+34 pp) and external (+6–19 pp) gains." The Lever arc becomes constructive. |
| PRIMARY / GUARD 1 fail (Tufts recovers, DENTEX or external erode) | "the tradeoff survives fine-tuning" — a stronger, more final version of §8.16: a single-class detector genuinely cannot serve Tufts and the external cohorts at once, even with target-domain fine-tuning. |
| GUARD 2 fails (Tufts does not recover) | "head fine-tuning is insufficient; the box-mAP ceiling is the box-vs-mask supervision gap (§8.9), not the training mix" — the only remaining lever is segmentation (2b), which is post-submission. |
| Partial / all fail | reported beside the Lever A table; the ablation stands, default detector unchanged. |

---

## 6. Risks recorded in advance

1. **Catastrophic forgetting.** The Tufts fine-tune could pull the head back toward Tufts-only
   behaviour and erode the +34 pp DENTEX / +9 pp external gains. `freeze=10` is the mitigation
   (backbone features fixed); PRIMARY and GUARD 1 are the checks. If they erode → clean negative.
2. **`arm3c_best.pt` was Tufts-val-selected.** It is the epoch-~118 checkpoint that scored best on
   Tufts val during multi-corpus training, so it is already the most Tufts-favourable multi-corpus
   checkpoint. Fine-tuning from it is the right starting point for *this* goal but means A2's
   Tufts recovery is measured from a slightly optimistic base. Stated, not corrected (`last.pt`
   was not downloaded from the Lever A box).
3. **`freeze=10` boundary.** YOLOv11l's backbone/neck split is around module 10; `freeze=10`
   freezes modules 0–9. If the calibration problem lives partly in the neck (trained here) this
   is fine; if it needs backbone movement, A2 under-fits Tufts and GUARD 2 fails — an informative
   negative, not a wasted run.
4. **A2 and Lever B both land.** If both produce adopt-worthy positives, there are two candidate
   pipeline changes and a harder adoption call — a good problem, resolved with the mentor.
5. **Schedule.** A2 itself is ~1 h GPU + ~½ day local eval. The risk is *adoption* (the
   downstream re-run) — §5 decouples that.

---

## 7. Local gate before renting

1. `arm3c_best.pt` sha256 == `5d301f13fb48da5c74e7ef01bd0f91226f9b6800cb433dee5aebc8f8db8f161e`.
2. `data/detector_multicorpus_v2/` re-gated on the box (tar sha256, no AppleDouble, `train_tufts.txt`
   = 700 lines, val = 150 / 3,794 boxes) — the Lever A `leverA_box_gate.py` covers this.
3. `train_a2_finetune.py` prints the `freeze=10` layer list and refuses CPU, like the Lever A trainer.

---

## 8. Cost, fixed in advance

One training run: `arm3c_best.pt` + `train_tufts.txt` (700 img), `freeze=10`, ≤ 40 epochs, batch 32,
1024 px, on an RTX-PRO-6000 / A100 @ ~₹179/hr. ~8 min training + ~1 h upload/gate/download/destroy
overhead ≈ **~₹250**. One redo budgeted ⇒ **~₹450 ceiling**. Evaluation is all CPU. GPU balance
before A2: **₹1,732**.
