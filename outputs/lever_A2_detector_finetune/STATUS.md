# Lever A2 — status: DONE 4 Sep 2026 — **ABLATION / not adopt-worthy**

**Verdict (`score_leverA_arm.py --label a2`): PRIMARY passes, GUARD 1 passes, GUARD 2 fails → not
adopt-worthy** (pre-reg §5 needs all three). Pipeline default detector unchanged. Instance 496782
destroyed. Full record: `models/16_detector_leverA2_finetune/run_summary.txt`, `RESULTS_LOG`
2026-09-04b, `a2/leverA2_verdict.json`.

| criterion | comparator | A2 | bar | result |
|---|---|---|---|---|
| **PRIMARY** — DENTEX FDI e2e (164 leak-free) | Control A 0.5844 | **0.8771**, Δ **+29.27 pp [+24.95, +33.59]** | lower bound ≥ +5 pp | ✅ pass |
| **GUARD 1** — pooled ext caries agreement (Ningxia + CariesXrays, 4,434 lesions) | Control A 0.3313 | **0.4168**, Δ **+8.55 pp [+6.88, +10.24]** | lower bound ≥ −2 pp | ✅ pass |
| **GUARD 2** — Tufts frozen test box mAP@0.5 | Control B 0.7243 | **0.5929** | ≥ 0.6843 | ❌ fail |
| **verdict** | | | primary ∧ G1 ∧ G2 | **ABLATION** |

## What A2 was and what it found

A2 = the fix Phase 0's diagnosis implied: freeze the Lever A 3-corpus backbone (`freeze=11`,
layers 0–10), fine-tune the neck + Detect head on Tufts-only (700 images, 40 ep / patience 12).
Hypothesis: re-specialise the collapsed Tufts head calibration while the frozen backbone keeps
the +34 pp DENTEX / +9 pp external gains.

- **It kept the gains:** DENTEX e2e +29 pp (arm3c was +34), external caries +8.6 pp (arm3c +9.1).
  The Tufts fine-tune eroded ~5 pp of DENTEX, ~0.5 pp of external — small.
- **It did not recover Tufts.** Tufts test box mAP 0.585 → **0.593** (+0.8 pp). Tufts *val* mAP
  recovered (0.54 → 0.62) but did not transfer to test; the operating-point P/R is unchanged
  from arm3c (0.593/0.638 vs 0.594/0.631). Early-stopped, best = epoch 6.
- **Reading:** the calibration hypothesis was necessary but not sufficient. The frozen 3-corpus
  backbone features cannot be recombined into a Control-B-quality Tufts detector by the
  neck + head alone — the ceiling is deeper than the detection head. This is pre-reg §5 row 3.

## What it means for the paper

The Lever 1 → A → **Phase 0** → **A2** arc is now complete and it is a clean methodological
result: a single-class multi-corpus tooth detector cannot be made to serve both the Tufts
benchmark and the external cohorts —
- naively (Lever 1) → fails the Tufts guard;
- with 4 corpora + balancing (Lever A) → fails harder, monotonic in Tufts training share;
- the failure is a confidence-calibration collapse, not localisation (Phase 0);
- and it is **not fixable by fine-tuning the detection head** (A2).

The only untried lever is multi-corpus **segmentation** (Tufts masks + pseudo-masks for the
box-only corpora), which the pre-reg scoped as **post-submission**. `PAPER_MATERIAL.md` §8.16.

## Files

`a2_best.pt` (49 MB, gitignored) · `a2_results.csv` · `a2_train.log` · `results.png` ·
`a2/stage2_*_head.json` (primary) · `a2/{ningxia,cariesxrays}_caries.json` (Guard 1 raw) ·
`a2/leverA2_verdict.json` · `PRE_REGISTRATION.md` (FROZEN, `a7e4902`).
Eval reused Lever A's Control A / Control B numbers and scripts (`models/15/repro/`,
`scripts/eval/score_leverA_arm.py`).
