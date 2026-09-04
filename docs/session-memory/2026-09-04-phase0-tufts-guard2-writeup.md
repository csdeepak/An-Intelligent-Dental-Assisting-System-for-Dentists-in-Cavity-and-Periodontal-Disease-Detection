# 2026-09-04 — Phase 0: the Tufts Guard-2 failure, confirmed and written up

**Session goal:** execute Phase 0 of the Lever A Guard-2 post-mortem
(`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` §3) — confirm the mechanism
with a confidence sweep + GT overlays, then fold it into the manuscript. No GPU, no training.

Continues `2026-09-03c` (the diagnosis) and `2026-09-03f` (the Mac/Windows ownership split — the
user owns Phase 0 + Lever A2, does them on the Mac).

## What was done

- **Councilled Phase 0** (in chat, not a doc — output is the work). Key finding: `PAPER_MATERIAL.md`
  §8.16 already carries a thorough Lever A write-up, so Phase 0 is a *surgical add*, not a rewrite;
  §8.10 (the diagnosis doc's stated target) is the wrong section — it is about the numbering head.
- **`repro/diagnostics/iou_diag_sweep.py`** (new) — greedy GT-match on the 150 Tufts frozen-test
  images, all 3 arms × conf {0.10, 0.25, 0.40}. Raw output pasted below.
- **`repro/diagnostics/gt_overlay.py`** (new) — 24 GT-box panels (12 Tufts + 12 DENTEX test
  images) to `data/detector_multicorpus_v2/_check/gt_overlay/` (local-only); two representative
  panels kept tracked in `docs/results/figures/lever_a_guard2/`.
- **Wrote up:** `TUFTS_GUARD2_DIAGNOSIS.md` §1.4b (the sweep) + §1.5 (fixed the box-shape claim —
  it is a mesial-distal tightness, not "crown-biased") + §3 (Phase 0 marked complete);
  `PAPER_MATERIAL.md` §8.16 (+1 paragraph: mechanism + box-vs-mask ceiling) and §8.9 (+1
  paragraph: the two Tufts box-label findings); `RESULTS_LOG.md` 2026-09-04; `transfer.md` §1/§3/§5.

## Result — the mechanism is a confidence-calibration collapse, not FN/FP alone

`iou_diag_sweep.py` raw output (Tufts frozen TEST, 3,924 GT teeth, greedy IoU≥0.5):

```
arm                                 conf    TP    FN    FP      P      R   IoU~
Control B (Tufts only, 100% share)  0.10  3027   897  1531  0.664  0.771  0.623
Control B (Tufts only, 100% share)  0.25  2879  1045  1058  0.731  0.734  0.624
Control B (Tufts only, 100% share)  0.40  2597  1327   783  0.768  0.662  0.625
Arm 3C (Tufts+DENTEX+Kaggle, 33%)   0.10  2929   995  2694  0.521  0.746  0.645
Arm 3C (Tufts+DENTEX+Kaggle, 33%)   0.25  2497  1427  1506  0.624  0.636  0.643
Arm 3C (Tufts+DENTEX+Kaggle, 33%)   0.40  1804  2120   967  0.651  0.460  0.643
Arm 4C (+ UFBA-425, 25%)            0.10  3143   781  3377  0.482  0.801  0.683
Arm 4C (+ UFBA-425, 25%)            0.25  2467  1457  1586  0.609  0.629  0.676
Arm 4C (+ UFBA-425, 25%)            0.40  1378  2546   668  0.674  0.351  0.674
  conf 0.10:  FN [897, 995, 781]  NOT-MONO   FP [1531, 2694, 3377]  MONO
  conf 0.25:  FN [1045, 1427, 1457]  MONO   FP [1058, 1506, 1586]  MONO
  conf 0.40:  FN [1327, 2120, 2546]  MONO   FP [783, 967, 668]  NOT-MONO
```

- **Matched-pair IoU flat across the whole sweep** (0.62 / 0.64 / 0.68) — localisation is not
  the loss, confirmed at 3 thresholds (03c used only 0.25).
- **At conf 0.10 the multi-corpus arms detect Tufts teeth as well as Control B or better**
  (Arm 4C recall 0.801 vs 0.771) — the detector sees them.
- **The score stops separating real teeth from spurious boxes.** Recall drop conf 0.10→0.40:
  Control B −0.11, Arm 3C −0.29, Arm 4C −0.45. Raising the threshold to clear the FP flood
  kills the TPs too. mAP@0.5 (a ranking metric) breaks hardest: 0.724 → 0.585 → 0.552,
  **monotonic in Tufts training share** (the FN/FP split at a fixed threshold is not — it is
  FP-flood at low conf, FN-collapse at high conf).
- **GT overlays:** DENTEX GT boxes visibly ~1.5× Tufts (e.g. `dentex_train_0` 1.19 % img median
  vs Tufts `1013` 0.64 %) — real, but the arms adapt to it (§1.3 stands).
- **Structural ceiling:** every detect model ≤ 0.724; deployed seg = 0.810 on the same split.
  seg→detect costs ~9 pp before any extra corpus. "0.585 vs 0.724" is the honest penalty.

## Decisions made

- **§8.16, not §8.10, for the mechanism.** *Reason:* §8.10 is the FDI-numbering-head section;
  §8.16 (Stage-2 failure taxonomy) already holds the Lever 1/A decomposition. The diagnosis
  doc's "write into §8.10" was imprecise; corrected there.
- **Report the sweep honestly as "not cleanly monotonic in FN/FP at every threshold".**
  *Reason:* the Skeptic voice pre-committed to writing what the numbers show. What *is* monotonic
  — the mAP number and the calibration collapse — is stated as such; the threshold-dependence of
  the FN/FP split is stated too, not hidden.
- **Overlays → `docs/results/figures/lever_a_guard2/` (2 panels), not the diagnostics dir.**
  *Reason:* `models/**/*.jpg` is gitignored; `docs/**/*.jpg` is whitelisted; and it is the
  figures home.
- **No `model_metrics.md` change.** *Reason:* the sweep changes no current-best number (the
  Guard-2 0.724/0.585/0.552 were already on the scoreboard from the Lever A entry).

## Open questions

None from Phase 0 — it is complete. The residual box-shape observation (Tufts GT tight
mesial-distally) is a label-convention property, fully characterised in §8.9, not an open item.

## Next steps

1. **Lever B** — the friend, on Windows (`outputs/lever_B_lesion_caries_path/WINDOWS_SETUP.md`
   → `START_HERE.md`). Unchanged.
2. **Lever A2** stays gated behind Lever B (`TUFTS_GUARD2_DIAGNOSIS.md` §3 Phase 1). If it is ever
   run, it is the user's, on the Mac.
3. Commit this session's work (explicit paths).
