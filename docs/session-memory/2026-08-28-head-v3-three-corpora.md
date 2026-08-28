# 2026-08-28 — Stage-2 head v3 on three corpora, and a 90-degree geometry bug

Third work block of 28 Aug. Earlier: `2026-08-28-c4-abstention.md`, `2026-08-28-c1-hardening.md`.

## Session goal

Complete the remaining GPU work: train the Stage-2 head on a third FDI corpus, as the user asked
for all GPU-side implementation to be finished today.

## What was done

- **Rebuilt the DENTEX and Tufts enumeration corpora locally.** Neither was on this machine —
  only the trained v2 head was. DENTEX reproduced v2's counts exactly first time (30,732 / 2,729).
- **Found a 90-degree geometry bug in the Tufts rebuild.** Every Tufts radiograph here is
  840×1615, rotated from the 1615×840 frame the crop builder expects. It produced 28,171/2,249
  instead of 35,248/3,721, silently rejecting **10,087 crops (23%)** as degenerate — no error.
  Rotating CCW reproduces v2's counts **exactly on all three splits**; degenerate crops fall to 17.
- **Added a degenerate-rate guard** (abort above 2%) to `scripts/tufts/build_enumeration_crops.py`
  and the new Kaggle builder. Persisted reconstructed upright images to
  `data/tufts/ZIP/Radiographs_upright`.
- **Fetched and verified the third corpus** (Kaggle `zwbzwb12341234/a-dual-labeled-dataset`), wrote
  `scripts/kaggle_dual/{build_enumeration_crops,verify_fdi_convention}.py`.
- **Trained two heads on an L4** (1h30m, ₹64.64, destroyed): a same-day control on rebuilt
  DENTEX+Tufts, and v3 on all three corpora. Evaluated per corpus with paired significance tests.
- Documented in `RESULTS_LOG.md` 2026-08-28c, `PAPER_MATERIAL.md` §8.23, `model_metrics.md`,
  `transfer.md` §2, and two `models/` run summaries. Suite **109 → 122**.

## Decisions made

- **Trained a control rather than comparing against published v2.** Three things changed at once
  (crop rebuild, geometry fix, torch 2.11 + new GPU). Comparing v3 to the published numbers would
  have folded all of them into what is meant to be a single-variable test. The control reproduces
  published v2 within ~1 pp, which *also* serves as the proof the geometry fix is right — a head
  trained on misaligned crops collapses rather than reaching 98.3% quadrant accuracy.
- **Verified the third corpus's numbering instead of trusting it.** Its vocabulary is exactly the
  32 FDI codes, which is precisely how Tufts looked before turning out mirrored. Used the v2 head
  as an arbiter over 915 teeth: 80.3% direct vs 1.7% mirrored. A close result would have been
  reported as inconclusive rather than resolved by picking the larger number.
- **Refused to quote pooled val.** v3's val set contains 1,961 Kaggle crops the control's does not,
  so the pooled comparison (0.855 vs 0.821) measures the val mixture as much as the head and
  inflates the effect ~3×. Reported per corpus on shared splits instead.
- **Ran paired significance tests before claiming the ~1 pp deltas.** DENTEX +1.14 pp survives
  ([+0.33,+1.95], p=0.013); Tufts +0.74 pp does not (CI crosses zero) and is reported as flat.
  This project has already withdrawn two claims for failing their intervals.
- **Kept the Kaggle +15.45 pp in the table but not as a headline.** v3 trained on that corpus, so
  it is not a generalisation result — but omitting the largest number would look like concealment.
- **Recommended v3 as a reported ablation, not the pipeline default.** A default swap invalidates
  the 58.3%/82.6% headline, the C4 curves, §8.16 and the pre-registered 0.30 operating point. A
  +1.14 pp in-domain gain does not justify that re-measurement before the 14 Oct freeze.
- **Did not re-open bone loss.** Its rebuild already rotates image and boxes together and still
  misses its geometry check by a wide margin; that is a separate, properly-investigated defect.

## Open questions

- **Why is Tufts flat while DENTEX gains?** Tufts is the largest corpus (35,248 crops) and the
  hardest (75% vs 91%). Whether a third corpus cannot help it, or whether Tufts' own label noise
  dominates, is untested.
- **Would v3 change the end-to-end number?** All v3 metrics here are crop-level on GT boxes. Its
  effect on the 58.3% end-to-end figure is unmeasured, and measuring it is most of the
  re-measurement cost that argues against adoption.
- **The corpus is 500 images, not 2,000.** Whether a fuller version exists elsewhere (the dataset
  ships 2,066 labels) is worth ten minutes before anyone plans around the larger figure.
- `_tufts_align.image_orientation_score` still cannot detect a 90° rotation. The degenerate-rate
  guard catches the *consequence*; a direct orientation test would be better.

## Next steps

1. **Write the paper draft** — unchanged, and now the only thing left. All GPU work is done.
2. Decide the C1 metric question from `2026-08-28-c1-hardening.md` before writing that section.
3. The four compliance blockers and the Drive upload remain account-owner actions.
4. Optional: measure v3 end-to-end if the schedule later allows adopting it.
