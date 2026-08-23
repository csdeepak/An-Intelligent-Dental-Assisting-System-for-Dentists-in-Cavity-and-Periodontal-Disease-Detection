# `scripts/eval/` — evaluation and error-propagation

Scripts that measure the pipeline rather than build or train it. This is where contribution
**C3** (system-level metrics + stage-wise error-propagation decomposition,
`MASTER_PLAN_2026H2.md` §2.3) is produced.

| Script | Measures | Status |
|---|---|---|
| `validate_fdi_assignment.py` | Stage 1 → Stage 2: does the pipeline give each tooth the right FDI number? | ✅ run — **28.0% end-to-end**, see below |

## `validate_fdi_assignment.py`

Runs the frozen detector + `src/fdi_assignment.py` against `DENTEX/disease/` — 250 images with
1,600 LabelMe polygons labelled `{id}-{Turkish name}-{FDI}`, the only per-tooth FDI ground
truth this project has.

```bash
python scripts/eval/validate_fdi_assignment.py --limit 8 --save-viz   # eyeball first
python scripts/eval/validate_fdi_assignment.py                        # full 249
```

Results (249 images, 1,534 teeth): recall **71.8%**, quadrant **93.0%**, FDI exact of detected
**39.1%**, **end-to-end 28.0%**. Writes `outputs/stage2_validation/` — summary, per-row and
per-image JSON, plus annotated overlays with `--save-viz` (blue = GT numbered correctly, red =
wrong or missed, orange = flagged assignment).

### Three things that make this evaluation honest, and are easy to get wrong

- **`test_181.png` is excluded.** It is byte-identical to `train_332.png` in the detector's own
  training set. Leaving it in would leak. It is the only such duplicate among 250 — checked by
  MD5 and by signature correlation against all 705 training and 50 extern images.
- **GT → detection only; no precision number is reported.** DENTEX `disease/` annotates only
  teeth carrying a finding (~6 of ~30 per image), so an unmatched detection is usually a real
  tooth with no annotation. Reporting precision here would be meaningless.
- **NMS IoU is 0.50, not the frozen run's recorded 0.70.** Chosen *a priori* on anatomy — real
  teeth in a panoramic do not overlap by half their area — **not** by sweeping the threshold
  against this evaluation set, which would contaminate it.

### What it found

Quadrant assignment is sound; the position digit is not, and the limit is structural rather
than a tuning problem. Even with a complete 8-tooth quadrant accuracy is only 68.7%, so
improving detector recall cannot rescue the approach — eight detected teeth are not positions
1–8, they are eight teeth that survived extraction. Full analysis and the cross-checks behind
that conclusion: `docs/results/RESULTS_LOG.md` 2026-08-22c, 22d and 22f.

**Re-run this after any Stage-2 change.** It is the before/after that will show whether a
learned enumeration head actually fixes the problem, against a held-out set that has never
been tuned on.
