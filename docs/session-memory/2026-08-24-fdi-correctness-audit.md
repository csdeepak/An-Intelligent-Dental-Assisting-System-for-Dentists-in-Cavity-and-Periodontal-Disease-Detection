# 2026-08-24 — FDI correctness audit: implementation sound, ceiling figure wrong

## Session goal

Verify the FDI implementation is actually correct — code, not documentation — and either fix
it or move on to next steps.

## What was done

**The verdict: the FDI implementation is correct.** Every load-bearing piece was re-derived
from source rather than read off the log:

- `src/utils/fdi_converter.py` — all 32 Universal→FDI entries checked individually.
- `src/fdi_head_inference.py` — the joint-probability reshape. `(lq.unsqueeze(2) +
  lp.unsqueeze(1)).reshape(N,32)` is row-major `k=q*8+p`; `FDI_CODES` is built q-outer/p-inner.
  They align. **This was the highest-risk thing in the codebase**: a transposition would be
  completely silent and would corrupt every prediction.
- `src/orientation.py` — transforms re-derived against `np.rot90` over 1,600 random points at
  five sizes including 840×1615. 0 mismatches, forward and inverse, both directions.
- Leakage exclusion — confirmed *applied*, not just loaded (both runs: 164 images, 86 excluded).
- Headline metrics — recomputed from raw per-tooth rows. 22.86% → 46.47% end-to-end reproduces
  exactly. 0 duplicate FDI codes across 627 assignments.
- 28 of 46 tests pass; the other 18 are blocked by a missing `cv2`, not by any defect.

**Four defects were found around the correct core**, all fixed:

1. **The ceiling figure was wrong in four documents.** `67.0%` is the *detector's recall*, not
   the ceiling. The real ceiling is **66.3%**.
2. **The "+2.4 point" margin compared two different populations** — the positional ceiling
   (complete quadrants only) against the head's accuracy over all detected teeth. Like-for-like
   it is **+13.9 points** (positional 66.3% vs head 80.2%, n=101). The head wins in *every*
   completeness bucket. **The error understated our own result.**
3. **A real code bug: the jitter augmentation was half-applied.** `build_enumeration_crops.py`
   cropped from the jittered box but wrote positional features from the un-jittered one — all
   15,366 jittered rows carry their original's features, 0 differ. Fixed.
4. **Stale docstrings** in `train_enumeration_head.py` still asserted `disease/` was "disjoint
   patients (verified)" and "249 images" — the exact claim the leakage disproved. Fixed, along
   with the leaked 0.280/0.687 baselines in the results JSON.

Also written: `scripts/eval/analyze_stage2_ceiling.py`, so the ceiling is reproducible from
saved artefacts instead of living in an unsaved snippet.

Files: `docs/results/RESULTS_LOG.md` (new entry 2026-08-24a), `model_metrics.md`,
`PAPER_MATERIAL.md`, `transfer.md`, `models/08_fdi_enumeration_head/run_summary.txt`,
`scripts/dentex/build_enumeration_crops.py`, `scripts/dentex/train_enumeration_head.py`,
`scripts/eval/analyze_stage2_ceiling.py` (new).

## Decisions made

- **Do not retrain for the jitter fix yet.** v1.0's 46.5% was measured end-to-end on real
  detector boxes, so the mismatch's cost is already inside that number — the fix can only help,
  and is unmeasured until a retrain. R4 is blocked on nothing and the head is good enough to
  integrate now. Retraining first would delay the project's largest gap to chase an unquantified
  gain. v1.0 stays frozen and reproducible-as-built; the corrected builder yields v1.1.
- **Corrected the ceiling rather than quietly restating it.** Rule 1 forbids editing a logged
  entry, so 2026-08-22j stands and 2026-08-24a supersedes it. The scoreboard files were
  corrected in place, each carrying an explicit "corrected 24 Aug" note — a silent fix would
  leave the next reader unable to tell which number to trust.
- **The root cause is a process gap, not carelessness.** The wrong figure survived because it
  came from an unsaved snippet. Rule 1's "traceable to a saved output" has to cover intermediate
  analyses too, not just headline metrics — hence the new script.

## Open questions

- **How much does the jitter fix actually buy?** Unmeasured. Needs a v1.1 rebuild + retrain
  (~50 min locally on MPS) to find out. Could plausibly be worth little.
- **Why did `cv2`/`ultralytics` disappear** from `/opt/anaconda3` between 22 and 24 Aug? Not
  investigated. Matters only because it blocks re-running the eval.
- **Are there other unsaved-snippet numbers in the log?** The ceiling was found by chance —
  two quantities colliding at 67.0%. Nothing systematic has been done to look for others.

## Next steps

1. **Restore the environment** — `pip install opencv-python ultralytics` — needed before any
   Stage-2 re-run or a full test pass.
2. **R4 — Stages 5–6 integration.** `scripts/run_inference.py` is still a 38-line placeholder.
   Top priority, no blocker, and it is paper claim C3.
3. **R1 — YOLOv11l-seg retrain** on a rented GPU. Detector recall (67.0%) is now the binding
   constraint; DentFound's ablation justifies it numerically.
4. Version-tag the bone-loss weights — the last untagged trained models.
5. Optionally, v1.1 of the enumeration head with the jitter fix — *after* R4.
