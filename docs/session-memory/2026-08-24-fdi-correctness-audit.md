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

---

# Addendum — same day, after the environment was restored

## What changed

`cv2` and `ultralytics` got installed, which made everything the audit above *could not
execute* executable. Two things came out of it.

**1. The install broke more than it fixed, briefly.** Pulling in opencv/ultralytics upgraded
numpy to 2.5.2, and torch 2.2.0 / scipy 1.12 / sklearn 1.4 are all compiled against numpy 1.x.
Measured, not guessed: `torch.numpy()` raised, `torch.tensor(ndarray)` raised,
`scipy.optimize.linear_sum_assignment` failed to import — **that is the Stage-2 Hungarian
assignment** — and sklearn failed entirely. Pinning `numpy==1.26.4` fixed all three while
keeping cv2 working (opencv 5.0 *declares* `numpy>=2` but is runtime-compatible with 1.x, which
I verified by exercising resize/rotate/cvtColor/imencode rather than trusting the metadata).

`requirements.txt` had `numpy>=1.24.0` — the constraint that allowed this — and was *also*
missing `scipy` entirely while `ultralytics` sat commented out. All three fixed.

**2. Stage 2 reproduces byte-for-byte.** Re-ran both methods from the frozen weights
(sha256 re-verified). Every headline number came back identical, and the artefacts are
`diff`-identical to `outputs/stage2_clean/` — all 936 per-tooth rows. The corrected ceiling
(66.3% vs 80.2%, +13.9) reproduced on the fresh run too. **46/46 tests pass** for the first
time this session.

**3. The one-to-one ablation, re-measured clean** (it had only ever been run on the
contaminated set): Hungarian 69.4% / 46.5% / **0 duplicates** vs argmax 65.1% / 43.6% /
**679 duplicates**. The gain is **+4.3 / +2.9**, against +2.1 / +1.5 on the leaked set — the
clean measurement makes the component look *better*, not worse.

## Decisions made

- **Pin numpy rather than upgrade torch/scipy.** Upgrading torch on a machine whose only GPU
  path is MPS, mid-project, with frozen weights that must keep loading, risks far more than it
  gains. The pin is one line and reversible.
- **Report the one-to-one quadrant trade-off rather than bury it.** One-to-one *costs* 2.1
  points of raw quadrant accuracy (94.7% vs 96.8%) because the global constraint sometimes moves
  a tooth across a quadrant boundary. It is still right by default — a duplicate FDI code is not
  a slightly-wrong answer, it is an impossible one a per-tooth report cannot render — but the
  cost is real and a reviewer will find it.

## Open questions

- **Why does the constraint help *more* on clean data?** Working theory: on unseen images the
  classifier is less certain, so more teeth compete for the same code (679 duplicates across 627
  detections), and arbitrating collisions is worth more. Plausible, not verified.
- Still unknown what the jitter fix buys — unchanged from above, needs a v1.1 retrain.

## Next steps

Unchanged and now unblocked: **R4 integration first.** The environment works, Stage 2 is
verified reproducible, and nothing is waiting on compute.

---

# Addendum 2 — third FDI pass, focused on ML principles

## What was checked that the first two passes had not

Deliberately different ground: data contracts at both ends, split hygiene, class balance,
preprocessing equivalence, edge cases, and an input ablation.

- **DENTEX category→FDI mapping** — verified *at source*, and it turns out to be stronger than
  the docs claimed. The COCO metadata's `name` fields literally read 1,2,3,4 and "1".."8", so
  the `+1` is the file's own labelling, not an inference. Spatial signature corroborates.
- **`disease/` GT parsing** — format is `<finding_id>-<finding_name_tr>-<FDI>` (`1-çürük-26`).
  1,600 shapes, 0 regex failures, exactly 32 distinct valid FDI codes.
- **Split hygiene** — 0 image overlap, 0 ann_id overlap, 0 jittered rows in val.
- **Class balance** — 1.83× overall, 1.01× on quadrants. Unweighted CE is correct here.
- **Preprocessing** — train and inference paths are **bit-identical** (max|diff| 0.0), verified
  on a real crop rather than by reading the code.
- **Edge case** — 2 images exceed 32 detections; Hungarian still emits 0 duplicates.

## The finding: a documented claim was wrong

Five places asserted "laterality is not recoverable from crop pixels" and that a pure image
classifier "would be guessing on half the label". That was the stated justification for the
architecture, and **it had never been tested**. So I tested it, decomposing quadrant into jaw
and side (side *is* laterality — a quadrant score hides it behind the trivially easy jaw split):

- image alone, neutral position → **side 96.3%**, not the 50% of guessing
- positional features contribute **+3.2 points of laterality, +2.8 FDI exact**
- the position digit comes **entirely** from the image (92.1% either way)
- *wrong* positional features cost **22.9 points of laterality**

Corrected in all five places.

## Decisions made

- **Corrected the rationale rather than the design.** The features earn their keep at +3.2/+2.8
  and cost almost nothing; nothing about the architecture needs to change. What was wrong was
  the *argument*, and that argument was headed into the paper.
- **Kept the no-horizontal-flip rule and re-grounded it.** It had been justified by the same
  refuted claim, but it never depended on it: flipping inverts the *label*, which is a fact
  about FDI notation, not about what the model can recover. Same rule, honest reason.
- **Reported the over-trust finding as a risk, not a footnote.** −22.9 points from wrong
  coordinates is larger than the entire benefit of having them, and inference feeds detector
  boxes. It is now the strongest — and only *quantified* — argument for the v1.1 retrain.
- **Discarded the `no_image` condition from the conclusions.** Its jaw score fell below chance,
  which means the blanked input is out of distribution and the model's behaviour there is
  undefined. Kept in the output for transparency, excluded from the claims.

## Open questions

- **Why is laterality recoverable from a crop at all?** Working hypothesis: the 1.5× expansion
  pulls in neighbours and arch curvature, so mirrored teeth sit in mirrored contexts. Not
  verified — a crop-size sweep would settle it, and would also say whether 1.5× is optimal.
- **Would the model still over-trust coordinates after the jitter fix?** That is the natural
  before/after for v1.1, and this ablation is now the instrument to measure it.

## Next steps

Unchanged. **R4 first.** The implementation is correct and verified three ways; v1.1 now has a
measured justification but is still not the priority.
