# 2026-09-03c — Lever A: why does the Tufts Guard-2 fail? (diagnosis + council, no new model)

**Session goal:** answer the user's question — Lever A's Tufts test box mAP drops (0.724 → 0.585)
while every other cohort improves; is it a fixable mistake, is there another way (the Tufts
masks?), check and verify, make a plan, council it.

No GPU. No model trained. Follow-up to `2026-09-03-lever-a-training-and-verdict.md` and
`2026-09-03b-lever-a-handoff-hardening.md`.

## What was done

- **Three local CPU diagnostics** on the existing `models/15` weights + `data/detector_multicorpus_v2/`
  (kept in `models/15_detector_multicorpus_leverA/repro/diagnostics/`):
  - `box_conv.py` — per-corpus GT box size / aspect / count.
  - `pred_box_size.py` — predicted box area on the 150 Tufts frozen-test images: GT vs Control B
    vs Arm 3C vs Arm 4C.
  - `iou_diag.py` — greedy GT-match on Tufts test: TP / FN / FP, matched-pair IoU, pred/GT w+h ratio.
- **Read the real Guard-2 P/R breakdown** from `leverA_train.log` (lines 758–768, 1581–1590,
  2362–2371) and the missing reference points: deployed seg model 0.810, old bbox detector
  0.7824, Lever 1 Control B 0.724 / Arm 0.647 (`RESULTS_LOG` 2026-09-01h, `model_metrics.md`).
- **Wrote** `outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` — the full
  diagnosis, a 5-voice council, and a 3-phase plan.
- **Logged:** `RESULTS_LOG.md` 2026-09-03c; `transfer.md` §5 (council) + §1 pointer;
  `repro/diagnostics/README.md`.

## Findings

| Tufts frozen TEST, conf 0.25, local greedy match | Control B (Tufts-only) | Arm 3C |
|---|---|---|
| matched teeth (TP) | 2,879 | 2,497 |
| missed teeth (FN) | 1,045 | **1,427 (+37 %)** |
| spurious boxes (FP) | 1,058 | **1,506 (+42 %)** |
| P / R | 0.731 / 0.734 | 0.624 / 0.636 |
| matched-pair IoU median | 0.624 | **0.643 (better)** |

Predicted median box area (% img): Tufts GT 0.621, Control B **0.933**, Arm 3C 0.770, Arm 4C 0.667.

- **Box-convention-mismatch hypothesis: REFUTED.** GT stats showed DENTEX boxes ~1.5× Tufts area,
  but the trained Arm 3C predicts boxes *closer* to Tufts GT than Control B does, with unchanged
  matched-pair IoU. Localisation is not where Lever A loses.
- **Confirmed cause: capacity / domain dilution** (the pre-registered "risk #2"). At Tufts 33 %
  of the mix the detector misses more Tufts teeth and fires with worse confidence — FN +37 %,
  FP +42 %. Monotonic in Tufts training share: 100 % → 0.724, 52 % (Lever 1) → 0.647, 33 %
  (Lever A) → 0.585.
- **Metric ceiling: box vs mask.** Deployed Stage-1 is *segmentation* and scores 0.810 on this
  exact split; every detection model here (incl. Tufts-only Control B) ≤ 0.724. seg→detect costs
  ~9 pp before any corpus is added. DENTEX/Kaggle/UFBA have no masks → the levers are forced to
  `detect`. All models predict Tufts boxes ~20–36 % taller than GT → Tufts box labels are
  crown-biased, capping everyone.
- **Minor:** Tufts boxes bypass the builder's `MIN_PX=2` degenerate-box filter (rotated corpora
  only) — 4/3,924 un-matchable boxes in the Guard-2 GT, 21 in Tufts train.

## Decisions made

- **No more GPU on the detector now.** *Reason:* the failure is not a fixable bug; raising Tufts
  share was already tried (52 % → still 0.647); Track A is the critical path (ISBI 26 Oct,
  compliance blockers open); Lever B is cheaper and more central. The diagnosis itself is a
  clean quantified ablation result and strengthens the paper.
- **Lever A stays ABLATION; nothing re-opened.** *Reason:* Guard 2 was pre-registered and
  failed. Re-scoring the existing arms against a new, easier Tufts metric to claim a pass would
  be goalpost-moving. Any retry is a *new* pre-registration (Lever A2), deployed detector stays
  `models/11` until it passes cleanly.
- **The real "another way" is masks, not box tweaks.** *Reason:* the 0.81 vs 0.72 gap is
  seg-vs-detect; box-scale augmentation won't help (box shape isn't the problem, §1.3). Multi-
  corpus segmentation with pseudo-masks, or multi-corpus pretrain → Tufts fine-tune, are the
  only options with real upside — both Lever-D-scale, both deferred behind Lever B.

## Open questions

1. **Interpretation of "how we did the bounding boxes for Tufts".** Assumed to mean the
   mask-based route and/or normalising box definitions across corpora. If the user meant
   something else the plan adjusts.
2. **Does a Tufts-only fine-tune keep the Guard-1 external-cohort gains?** Unknown — that is
   what Phase 2a would test, and its Guard-1 arm is mandatory.
3. **No end-to-end Tufts FDI evaluator exists** (`validate_fdi_assignment.py` is DENTEX-only).
   Building one (frozen Tufts FDI test split + leakage check, ~1 day) would let a future guard
   measure "boxes good enough for the pipeline on Tufts" instead of raw box mAP. Noted, not
   scheduled.
4. The greedy-match FN/FP decomposition reproduces the log's P/R within ~0.02 but is not the
   COCO mAP integrator — Phase 0 step 0.3 (FN/FP at conf {0.10, 0.25, 0.40}) firms this up.

## Next steps

1. **User/mentor decision on the plan** in `TUFTS_GUARD2_DIAGNOSIS.md` — recommended: Phase 0
   (no GPU), then Lever B; Lever A2 behind the Phase 1 gate.
2. **Phase 0** (if approved, ~half a day, no GPU): GT-box overlays (15 Tufts + 15 DENTEX);
   `iou_diag.py` extended to Arm 4C and conf {0.10, 0.25, 0.40}; write `PAPER_MATERIAL.md` §8.10
   (mechanism) + §8 Known Limitations (Tufts label height bias, unfiltered degenerate boxes).
3. **Lever B** — unchanged as the next lever (`outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md`).
4. Commit this session's docs + diagnostic scripts (explicit paths).
