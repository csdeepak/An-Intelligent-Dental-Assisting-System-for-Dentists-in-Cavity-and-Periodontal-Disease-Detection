# 2026-09-04c — Tufts end-to-end FDI eval: the Stage-2 number the paper never had

**Session goal:** build the Tufts analog of `validate_fdi_assignment.py` (detector → head →
Hungarian FDI, scored against Tufts GT), fill the paper's gap (it decomposes DENTEX
stage-by-stage but has no Tufts end-to-end number), and report the multi-corpus comparison the
Lever A arc needs. No GPU.

Continues `2026-09-04b-lever-a2-executed.md`. Recommended in that session's council as Option 1.

## What was done

- **`scripts/eval/validate_fdi_assignment_tufts.py`** (new, ~150 lines). Reuses:
  `validate_fdi_assignment.iou` / `match_gt_to_detections` / `draw_viz`;
  `src.utils.fdi_converter.tufts_title_to_fdi` (the left-right mirror, verified 3 ways —
  RESULTS_LOG 2026-08-25h); `src.orientation.detect_upright`; `src.fdi_head_inference`.
  New code: a Tufts GT loader + `upright_box` (copied, 6 lines, from `build_enumeration_crops.py`)
  + an MD5 leak scan + a compact report.
- **Verified** on a 6-image dry run + 6 viz overlays: the mirror is correct (Q1 upper-viewer-left,
  Q2 upper-viewer-right), boxes sit on teeth, 0 duplicate FDI codes, 1 leak excluded (`590`,
  byte-identical to a training image — handled like DENTEX's `test_181`).
- **Ran** the full 149-image eval for 4 detectors + a conf-0.10 sensitivity check on `models/11`.
- **Logged:** `RESULTS_LOG` 2026-09-04d, `model_metrics.md` (new Stage-2 subsection),
  `PAPER_MATERIAL.md` §8.10 (+1 paragraph), `transfer.md` §1. `.gitignore` whitelist for
  `outputs/stage2_tufts*/**.json` (viz stays local).

## Results (149 imgs, 3,760 permanent GT teeth, conf 0.25, one-to-one)

| detector | recall | FDI exact (of detected) | **end-to-end FDI** |
|---|---|---|---|
| `models/11` deployed seg (Tufts-trained) | 82.4 % | 78.6 % | **64.8 %** |
| `models/06` old bbox (superseded) | 91.2 % | 78.4 % | **71.5 %** |
| `models/15` arm3c (Lever A multi-corpus) | 89.3 % | 71.1 % | 63.5 % |
| `models/16` A2 (Tufts head fine-tune) | 89.9 % | 70.8 % | 63.7 % |

`models/11` @ conf 0.10: end-to-end **61.3 %** (recall 95 %, det/img 35.7 — worse, spurious
boxes flood the assignment). conf 0.25 is near-optimal.

## Findings

1. **The pipeline's Tufts Stage-2 number is 64.8 % end-to-end / 78.6 % of detected** — above
   DENTEX's 58.3 % (in-domain detector) on a *harder* test (every tooth, not just ~6 pathological).
2. **The Lever A / A2 box-mAP guard failure is a ~1-point end-to-end Tufts cost**
   (64.8 → 63.5 → 63.7), from a −14-point box mAP@0.5 drop. Confirms the §8.16 IoU-0.3
   reframing at the actual pipeline output. The multi-corpus detector finds *more* Tufts teeth
   (recall +7 pp) and numbers them slightly worse (of-detected −8 pp) — nets flat.
3. **`models/06` (old bbox) beats `models/11` (deployed seg) on Tufts end-to-end: 71.5 % vs
   64.8 %**, recall-driven. The 27 Aug bbox → seg swap gained +12 pp on DENTEX cross-domain and
   costs 6.7 pp on Tufts in-domain — a higher box mAP did not buy higher pipeline accuracy on
   the detector's home corpus. A detector–Stage-2 coupling nuance, **not** a reason to revert.

## Decisions made

- **Separate script, not a `--dataset` flag on `validate_fdi_assignment.py`.** *Reason:* the
  DENTEX eval produces published numbers; a divergent GT loader + orientation path through its
  `main()` risks breaking it. The new script imports its stable helpers.
- **Report `models/11` as the headline, keep the 3 other detectors as comparison rows.**
  *Reason:* `models/11` is the deployed default; the others answer "what does the Lever A
  detector / the old detector do end-to-end on Tufts".
- **Finding 3 is reported, not acted on.** *Reason:* `models/11` was adopted on box mAP + the
  DENTEX cross-domain gain, a dated human decision (§7.1); DENTEX is the generalisation test
  the paper rests on. Reverting for a Tufts in-domain number would be the wrong trade. But it
  is an honest nuance for §8.16's detector–Stage-2 discussion.

## Open questions

1. Whether to build a Tufts *failure taxonomy* (like §8.16's DENTEX one) from the saved rows —
   the per-tooth JSON is there. Cheap, paper-relevant, not done.
2. `models/06`'s Tufts advantage is at conf 0.25 — a per-detector conf tune was not done
   (would contaminate; conf 0.25 is the frozen pipeline default).

## Continued — Tufts failure taxonomy (same session, `RESULTS_LOG` 2026-09-04e)

Ran `scripts/eval/stage2_failure_taxonomy.py` on the Tufts rows — added `--label` + `--fig-name`
args (DENTEX defaults unchanged, regression verified: 546/275/89/10/8/6/2). `models/11` main,
`models/06` control.

- Tufts: correct **64.8 %**, not_detected **18.2 %** (vs DENTEX 29.4 %), off_by_one 12.6 %,
  category errors (wrong_arch + mirror_lr) **3.2 %** of teeth. 74 % of numbering errors are
  off-by-one. 43/49 `mirror_lr` are central incisors — not a mirror-correction bug.
- **The detector swap's effect on Tufts is the reverse of DENTEX:** bbox→seg moved `correct`
  71.5 → 64.8, entirely via `not_detected` 9.6 → 18.2 — error shape unchanged. On DENTEX the
  swap improved the shape (`wrong_arch` −75 %). The seg detector's box-quality benefit is
  cross-domain; on Tufts (in-domain, bbox already clean) it only cost recall.
- Reverted the no-op regen of the DENTEX taxonomy fig + json (Windows path only differed).

## Next steps

1. **Lever B** — the friend, on Windows. Still the only active *score* lever.
2. Commit this session's work.
