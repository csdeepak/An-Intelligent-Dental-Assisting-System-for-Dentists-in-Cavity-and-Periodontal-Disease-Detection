# 2026-09-04b — Lever A2 executed: a Tufts head fine-tune does not recover the benchmark

**Session goal:** run Lever A2 — freeze the Lever A 3-corpus backbone, fine-tune the neck +
detection head on Tufts-only, and score it against the (identical Lever A) pre-registered bars.
Test the fix Phase 0's diagnosis implies.

Continues `2026-09-04-phase0-tufts-guard2-writeup.md`.

## What was done

- **Council + froze the pre-reg.** `outputs/lever_A2_detector_finetune/PRE_REGISTRATION.md`
  drafted (`eceba7a`), then **FROZEN** (`a7e4902`) after the user reviewed the bars. One
  correction from a local check on `arm3c_best.pt`: `freeze=10` leaves the C2PSA attention block
  trainable (55 % of params), so `freeze=11` (full backbone 0–10 frozen, 50.7 %; neck 11–22 +
  Detect head 23 trainable) is the clean "backbone frozen" experiment. `scripts/yolo/train_a2_finetune.py`
  written (~50-line companion to the Lever A trainer).
- **Built a Tufts-only subset** of `data/detector_multicorpus_v2/` (280 MB tar vs 467 MB full —
  A2 touches Tufts only). Box counts val 3,794 / test 3,924 reproduced.
- **GPU run:** JarvisLabs RTX PRO 6000 (instance 496782, IN1, env torch 2.11 / ultralytics
  8.4.127 — identical to Lever A). On-box `GATE: GO`. `train_a2_finetune.py` ran ~10 min,
  EarlyStopping at epoch 18 (best = epoch 6). Weights sha256-verified, **instance destroyed**.
  Spend **~₹36** (balance ₹1,184.84 → ₹1,148.78).
- **Local eval (CPU/MPS):** primary (`validate_fdi_assignment.py` on the 164 DENTEX images) +
  Guard 1 (`ningxia_external.py` + `cariesxrays_external.py` with `--detector a2_best.pt`) +
  `score_leverA_arm.py --label a2`. Reused Lever A's Control A / Control B numbers.
- **Logged:** `models/17_detector_leverA2_finetune/run_summary.txt`, `outputs/lever_A2_detector_finetune/STATUS.md`,
  `RESULTS_LOG.md` 2026-09-04b, `model_metrics.md` (new Lever A2 subsection), `PAPER_MATERIAL.md`
  §8.16 (+1 paragraph), `transfer.md` §1/§3/§4/§8.

## Result

| criterion | comparator | A2 | bar | result |
|---|---|---|---|---|
| PRIMARY — DENTEX FDI e2e (164) | Control A 0.5844 | **0.8771**, Δ **+29.27 pp [+24.95, +33.59]** | lower bound ≥ +5 pp | ✅ PASS |
| GUARD 1 — pooled ext caries agreement (4,434 lesions) | Control A 0.3313 | **0.4168**, Δ **+8.55 pp [+6.88, +10.24]** | lower bound ≥ −2 pp | ✅ PASS |
| GUARD 2 — Tufts frozen test box mAP@0.5 | Control B 0.7243 | **0.5929** | ≥ 0.6843 | ❌ FAIL |
| **verdict** | | | primary ∧ both guards | **ABLATION / not adopt-worthy** |

- Tufts **test** box mAP moved **+0.8 pp** (0.585 → 0.593). Tufts **val** mAP recovered
  (0.54 → 0.62) but did not transfer. Operating-point P/R unchanged from arm3c.
- A2 kept most of the multi-corpus gains: DENTEX e2e +29 vs +34 pp, external +8.6 vs +9.1 pp.
  Ningxia pooled 0.407 (Ctrl A) → 0.600 (arm3c) → 0.570 (A2); CariesXrays 0.309 → 0.370 → 0.372.

## Decisions made

- **`freeze=11`, not `freeze=10`.** *Reason:* verified locally — `freeze=10` leaves the C2PSA
  attention block trainable (a fuzzy backbone boundary). `freeze=11` = full backbone frozen.
  Recorded in the pre-reg §3 before freezing.
- **Verdict = ABLATION, bar not moved.** *Reason:* pre-reg §5 needs all three. Guard 2 fails.
- **Multi-corpus segmentation (Phase 2b) is post-submission, not a next step.** *Reason:*
  pre-reg §2 scoped it that way; A2's clean negative confirms head fine-tuning is a dead end,
  and 2b is a Lever-D-scale effort (Tufts masks + pseudo-masks + a mask-quality gate) that does
  not fit before the ISBI deadline. The `transfer.md` §4 pending-decision row is now **resolved**.
- **The calibration hypothesis was necessary but not sufficient.** *Reason:* Phase 0 showed the
  backbone finds the teeth and the head's confidence is miscalibrated; A2 shows re-specialising
  the head does not fix Tufts *test* box mAP. The ceiling is deeper than the head — a
  Control-B-quality Tufts detector is not reachable from the frozen 3-corpus features.

## Open questions

1. **Why did Tufts val recover but not test?** Either the frozen `split_v1` val/test are not
   iid enough for val-fitting to help test, or the frozen features genuinely cap test box mAP.
   Not worth chasing — the conclusion (head fine-tune insufficient) holds either way.
2. **The ₹547 GPU-balance gap** (₹1,732 recorded vs ₹1,184.84 actual pre-A2). Not this session.
   User to check — the friend testing something? a paused instance that billed?
3. `models/16/a2_best.pt` (49 MB) is local-only — same Drive gap as models/11–15.

## Next steps

1. **Lever B** — the friend, on Windows. Now the only active score lever
   (`outputs/lever_B_lesion_caries_path/WINDOWS_SETUP.md` → `START_HERE.md`).
2. Commit this session's work (explicit paths).
3. User: check the GPU-balance gap; upload `models/16` (+ 11–15) to Drive.
