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

---

# Addendum 3 — fourth FDI pass: frames, geometry, test quality, BatchNorm

## What was checked

Again deliberately new ground. **No defect found in the FDI logic.**

- **GT coordinate frame** — assumed upright everywhere, never tested. 250 images, 1,600 shapes,
  **0 points out of bounds**; all images wide. A rotated-frame GT would have blown this up.
- **`unrot_box` at pixel level** — not just algebra: paint a patch, rotate the real image,
  recover its bbox, un-rotate. Exact match both directions. Plus 2,400 synthetic boxes, 0 error.
- **Test quality** — because "46/46" is worthless if the tests are vacuous. They are not:
  `test_fdi_converter` writes its expected table *independently of the module*, and its docstring
  explains why (the old version asserted the buggy value). `test_orientation` checks against real
  `cv2.rotate` pixels. `test_fdi_assignment` deletes a mid-arch tooth and requires a **flag**
  rather than silent renumbering.
- **BatchNorm state** — the one with real teeth. ResNet18 has BN; in train mode every tooth's
  prediction would depend on which other teeth shared its batch. `load_head` returns `.eval()`,
  and batch-invariance measures **~7e-6** across (12) vs (1,5,2,4) vs one-at-a-time. Train mode
  shifts by **1.518**, so the check discriminates and the code passes.
- **Architecture parity** — `load_head` rebuilds the net independently of `build_model`. 128
  tensors, keys and shapes identical, strict load succeeds.

## Decisions made

- **Documented the `0.30` threshold instead of tuning it.** It was a bare magic number, while the
  IoU thresholds two files over explicitly say they were chosen a priori "NOT by sweeping against
  this evaluation set". Since the flagged/unflagged split is *reported*, leaving it undocumented
  invites the tuning question. I measured its discrimination at the fixed value (50.5% vs 72.7%,
  +22.2 points) and wrote that down as an **observation, not a justification** — deliberately did
  not sweep for a better value, because that would be tuning on the test set.
- **Recorded the pixel-convention question rather than "fixing" it.** `unrot_point` uses a closed
  pixel-index convention; YOLO emits continuous edges. Worst case 1px ≈ 4e-4 in a normalised
  feature. Changing it would churn the frozen model's inputs for no measurable gain.
- **Verified the refactor byte-for-byte.** Extracting a constant *should* be inert; I re-ran the
  eval and diffed rather than assuming.

## The pattern across four passes

The FDI **logic** has survived every check. Every defect found has been in the **documentation
of** that logic — the ceiling figure, the laterality rationale, stale disjointness claims — plus
one half-applied augmentation. That is worth knowing: the risk here is not broken code, it is
confident prose about code that nobody re-derived.

## Next steps

**R4.** Four passes is enough.

---

# Addendum 4 — R4 built: the pipeline composes end to end

## What was done

Replaced the 38-line `run_inference.py` placeholder with a real six-stage pipeline, and added
`src/classifiers.py` for Stages 3–4. Image in → per-tooth JSON + optional overlay out. 14 new
tests, 60/60 pass. RESULTS_LOG 2026-08-24f.

## The thing that could have gone silently wrong

**Three stages use three different crop conventions** — 1.5×/1.5× (FDI head), 1.0× tight
(caries), 1.5×/2.0× (bone loss) — because they were trained by different people in different
notebooks. Cross them and you get the same tensor shape, plausible values, confident wrong
output, and **no error anywhere**. Same for class order: an inverted index reports every healthy
tooth as diseased and still looks like a working pipeline.

So I read every convention out of the artefact that defines it rather than inferring any of it,
and the bone-loss binary order — whose checkpoint has no `class_to_idx` — I recovered
arithmetically from the recorded FocalLoss α against the recorded class counts. The pipeline now
*asserts* the caries `class_to_idx` at load and aborts on a mismatch.

## What composing the stages revealed

Running 12 leak-free images, 299 detected teeth:

- **caries-positive 84.9%** (254) against 35 annotated carious teeth — a ~7× over-call
- **bone-loss-positive 0.7%** (2) at 0.93–0.999 confidence in `normal`
- **duplicate FDI codes: 0**

Two out-of-distribution failures **in opposite directions**. The caries gate over-calls because
its negative class holds no healthy teeth; the bone-loss branch is near-inert because it was
trained on Tufts and is being run on DENTEX. Neither is visible when a stage is evaluated on its
own curated crops — which is precisely the C3 argument, now demonstrated rather than asserted.

## Decisions made

- **Report the broken branches rather than disable them.** Both limitations are quantified
  inside every report under `["limitations"]`, and every caries prediction — positive *and*
  negative — carries `gate_out_of_distribution`. Suppressing the output would hide the finding;
  emitting it unlabelled would invite it being quoted as a caries rate.
- **Reused `LOW_CONFIDENCE = 0.30` for assessability** instead of adding a second threshold. A
  tooth the numbering head calls low-confidence is exactly a tooth whose findings cannot be
  attributed. One number to justify, not two.
- **Asserted positional alignment in the fusion step.** Four per-stage lists are zipped by
  index; if any stage ever returns a filtered list, findings would attach to the wrong tooth
  silently. Cheap to check, invisible if wrong.
- **Did not add Grad-CAM.** Stage 6 in the plan mentions it; it is not needed for the JSON
  report and would have expanded scope past what was asked.

## Open questions

- **The caries gate now blocks any meaningful caries number.** The detector-derived
  healthy-tooth idea in `transfer.md` §4 has moved from optional to blocking. Not yet decided.
- **Is bone loss inert only on DENTEX, or generally off-Tufts?** One dataset is not enough to
  say. This is what Ningxia is for.
- I checked alignment on `test_0` only (3/5 GT matched, 2/3 FDI correct). A systematic
  pipeline-vs-GT evaluation across the clean set has not been run.

## Next steps

1. Decide the caries negative class — now blocking, not optional.
2. R5 (severity reporting) is unblocked.
3. R1 seg retrain still the lever on detector recall; still the only job needing a rented GPU.

---

# Addendum 5 — correction to Addendum 2: the "over-trust" claim is withdrawn

**Addendum 2 above is wrong on one point, and it is left standing rather than edited so the
record shows what was believed when.** It says the head "over-trusts" its positional input and
treats that as a real train/inference gap and the strongest argument for a v1.1 retrain. That
does not survive measurement. RESULTS_LOG 2026-08-24e.

**What was wrong:** the 22.9-point figure came from *shuffling* positional features — giving a
tooth another tooth's coordinates. A shuffle teleports the coordinate, often across the midline,
and crossing the midline is exactly what inverts laterality. It is not a model of detector-box
error.

**What realistic error actually costs**, on the same val split:

| Perturbation | side | position | FDI exact |
|---|---|---|---|
| none | 99.5% | 92.1% | 91.6% |
| ±15% of box *(the training jitter)* | 99.5% | 92.1% | **91.6%** |
| ±100% of box | 99.3% | 92.2% | **91.5%** |

Displacing every box by its own full width costs 0.1 points. The geometry explains it: a tooth
is ~4.5% of image width, so a full-box shift moves normalised cx by ≤0.045 while the median
tooth sits 0.091 from the midline.

**Consequences for anyone picking this up:**
- the head **is** robust to detector-box error; 46.5% is not depressed by feature noise
- the jitter fix in `build_enumeration_crops.py` is a correctness fix worth keeping, but **not**
  a performance opportunity — do not cite it as one
- **v1.1 has no measured performance justification.** Addendum 2's "strongest and only
  quantified argument" is gone
- the shuffle result keeps one legitimate use: it is an **attribution** diagnostic showing the
  head genuinely reads the coordinate. Not evidence of fragility

**The methodological lesson, which is the durable part:** a shuffle answers *"does the model use
this input?"* It does not answer *"is the model robust to realistic error in this input?"*,
because the perturbation is not drawn from the error distribution the pipeline produces. Those
are different questions needing different experiments. Picking the easy perturbation and reading
it as a robustness result is the error — and I made it about my own ablation, in the same
session where I was correcting the same class of over-claim elsewhere.

---

# Addendum 6 — the caries gate's negative class, fixed (25 Aug)

## What was done

R4 exposed the gate calling 84.9% of detected teeth carious. Root cause: its `no_caries` class
was Impacted + Periapical Lesion — **no healthy teeth at all**. Rebuilt it and retrained.
RESULTS_LOG 2026-08-25a.

**The key finding: 2026-08-21m's conclusion was half right.** It correctly showed the
enumeration↔disease **filename** join is invalid (different patients), then concluded healthy
teeth are "NOT derivable from DENTEX". But the subsets share **260 byte-identical images under
different filenames** (`train_437.png` ≡ `train_1.png`). An **MD5** join recovers them exactly.

I did not take that on trust. The falsifiable test: for a shared image, a disease annotation and
an enumeration annotation covering the same tooth must carry the same FDI. **1,255 agree, 22
disagree = 98.28%**; different patients would sit near 3%. The builder re-runs this every build
and aborts below 90%.

Result: **5,366 real healthy teeth**. In-pipeline caries **84.9% → 19.1%** against an 11.7%
annotated floor; over-call 7.3× → 1.6×.

## Decisions made

- **Excluded the ambiguous IoU band (0.10–0.50, 856 teeth) rather than resolving it.** A
  partially-overlapped tooth is exactly where "healthy" would be a guess, and a diseased tooth
  mislabelled healthy is the error the whole exercise exists to remove. Cost 11.5% of the data;
  worth it.
- **Inherited splits from `splits_v2`** rather than making a fresh split, so the v3 test set is a
  subset of `phase1_legacy`'s and the two stay comparable.
- **Made v3 the pipeline default but kept the legacy gate.** The legacy model is not broken for
  the task it was trained on; it is wrong for the task the pipeline asks. It is still the model
  behind the published `phase1_legacy` numbers, so it stays, reachable via `--caries-gate`.
- **Renamed the flag `gate_out_of_distribution` → `caries_uncalibrated`.** The old name became
  false the moment the gate saw healthy teeth. The new one states what is still true: precision
  0.40 and a presumed-negative training class.
- **Reported four limitations rather than one headline.** Precision 0.40; the annotated count is
  a floor so 1.6× is an upper bound on how good this looks; presumed-negative assumption;
  tooth-type confound.

## What the visual check caught that the numbers did not

The healthy crops looked blank in a contact sheet. Cause: healthy is dominated by narrow
anterior teeth, stretched by the non-aspect-preserving resize, while caries concentrates in wide
molars. I then tested whether that is an exploitable shortcut — **aspect ratio alone scores
84.1%, exactly the majority baseline (−0.1% over it)**. Not exploitable, but real enough that
per-position evaluation is the honest way to report this model. I would have missed the question
entirely without looking at the images.

## Open questions

- **Per-position evaluation of the gate** has not been run; that is how to size the confound.
- **Precision 0.40 is the live problem now.** Whether that is genuine false positives or
  unannotated real caries cannot be separated inside DENTEX.
- **260 images, one dataset, one scanner population.** External validation is what Ningxia is for.
- **Phase-2 severity still trains on `phase1_legacy`-era crops** and was not touched.

## Next steps

1. **Bone loss is now the open OOD failure** — near-inert (0.7%) off-Tufts.
2. Per-position gate evaluation.
3. R1 seg retrain — still the only job needing a rented GPU.

---

# Addendum 7 — external Drive documented; upload blocked by a real tool limit (25 Aug)

## What was done

User provided two Google Drive links (DENTEX, Tufts) and asked for gitignored checkpoints and
datasets to be backed up there in new subfolders, plus a README documenting the drive
structure so the links never need to be re-shared.

**Scoped down to exactly what's load-bearing, verified against source, not assumed:**
cross-checked every `DEF_*` default in `scripts/run_inference.py` against `git ls-files`.
Result: of six untracked `.pt`/`.pth` files on disk, only **two** are actually loaded by the
pipeline — `06_yolo_detection_a100_run/best.pt` (49 MB, `DEF_DETECTOR`) and
`09_caries_gate_v3/caries_gate_v3.pth` (43 MB, `DEF_CARIES_GATE`). Confirmed the other four are
non-load-bearing lineage: `last.pt` is referenced only in prose/docs, never in a load path
(grepped); `best_model.pth`'s tensor payload is bit-identical to the already-tracked
`final_model.pth` (compared 122 tensors directly, not just file size).

Did not back up the multi-GB derived datasets (`crops_v2`, `enumeration_v1`, `crops_v3_phase1`,
`dataset_seg`, `_repo_archive/`) — all are marked in `.gitignore` as "regenerate with script X,
never commit," which is the same reasoning that says they don't need Drive backup either:
cheap to rebuild locally, expensive to transfer and store. `_repo_archive/opg_env/` (439 MB) is
a Python virtualenv and should never be backed up anywhere.

## The blocker, found by trying rather than assumed

Browsed both drives read-only first (unauthenticated `Claude_Browser`) to see existing
structure without risking an overwrite — DENTEX has `disease/`, `training_data/`,
`validation_data/`; Tufts has `ZIP/`, `processed_dataset_tufts/`, `resampled_dataset/`,
`severity_dataset/`, and an existing `models/` folder of unknown, unrelated content.

Attempted the actual upload via `claude-in-chrome` (needs the user's real, authenticated
session — Drive edit access requires it). Two blockers, both real tool limits rather than
something to route around:
1. The Chrome extension was not connected in this session.
2. Even if it had been, `file_upload` caps at **10 MB per call, combined** — both checkpoints
   (49 MB, 43 MB) exceed that alone.

**Did not attempt to split either binary into <10MB chunks and reassemble.** That would trade
a clean failure for a fragile one — a corrupted or misassembled checkpoint is a worse outcome
for "friend's laptop continues without errors" than an honest manual step.

## What was delivered instead

`docs/EXTERNAL_DRIVE.md` — the two links, verified folder structure, the exact two-file table
above with source/destination/size, restore commands for a fresh clone, and an explicit
"upload not yet done, here's how" note rather than a false "done" claim. Referenced from
`docs/README.md`'s index and from `models/README.md` (the first place someone hits the
"missing model weights" error). `transfer.md` §7 updated with both the Drive pointer and a
stale test count I found in passing (still said 46/46; R4's `test_classifiers.py` moved it to
60/60 on 24 Aug and nothing had corrected the line since).

## Decisions made

- **Manual upload over a workaround.** Two files, one-time, ~60 seconds by hand once the
  folder is open. Not worth the risk of a partial/corrupted transfer via a size-limited tool.
- **New `capstone_checkpoints/` folder rather than reusing Tufts' existing `models/`.** Its
  contents are unknown and the user's instruction was explicit: create new, don't touch
  existing.
- **Split the two checkpoints across drives by training data**, not both into one drive —
  keeps each drive matched to the dataset context it already represents.

## Open questions

- The two folders (`capstone_checkpoints/` in each drive) have not been created yet — that
  and the file drag-in are the user's remaining manual step.
- If this becomes a recurring need (more checkpoints, more often), `rclone` is the right tool —
  not attempted here since it needs the user's own one-time OAuth step and this was a two-file,
  one-off ask.

## Next steps

1. User creates `capstone_checkpoints/` in both drives and drags in the two files
   (`docs/EXTERNAL_DRIVE.md` has exact instructions).
2. Everything else from the prior addenda stands: C1/C2 external validation is the real next
   technical work, R4 and the caries gate fix are done.

---

# Addendum 8 — T0.1 closed: caries arm A run, and it's inconclusive by design (25 Aug)

## What was done

Three review passes on `train_caries_cascade.py` before running anything, at the user's
explicit request: traced arm A's transform path (`build_transforms(augment=False)` returns
`(eval_tf, eval_tf)`, zero randomness), hand-verified the `class_weights_from_loader`
one-liner against both the smoke and non-smoke code paths, confirmed no output-path collision
with arm B, and confirmed via `git diff --stat` that the script hadn't changed since arm B ran.
Then a live check during training: arm A printed the identical class weights arm B did
(`[3.2849, 0.5898]`) — proof both arms trained on the same data, isolating augmentation as the
only variable.

**Result:** val macro-F1 A=0.7210 / B=0.7350; test A=0.7212 / B=0.6948. Arm B wins on val (the
selection metric), arm A scores higher on test — a disagreement, not a clean story either way.

## The thing that mattered: sizing the noise before reading the gap as a finding

Extracted every epoch's val macro-F1 from both logs (had to fix a first attempt that
accidentally regex-matched the adjacent accuracy number too). Each arm swings **~0.27** across
its own 15 epochs. The between-arm gap is **0.014–0.026** — 10–20× smaller. That comparison is
the actual finding: a single-seed A/B this size cannot support any claim about augmentation,
and I said so rather than picking whichever number sounded more interesting.

## Decisions made

- **Re-scoped T0.1 before running it.** It was written against `phase1_legacy`, the caries
  gate's now-superseded negative class. Ablating a model nobody uses would have been wasted
  compute on the wrong question. Ran both arms on `crops_v3_phase1` instead.
- **Did not swap the frozen pipeline default.** `caries-gate-resnet18-v3.0` was frozen from
  arm B before arm A existed. Now that both do, val macro-F1 — the pre-registered selection
  metric — still narrowly favours B. Switching to A because it scored higher on *test* would
  be exactly the test-set-tuning this project's discipline exists to prevent (same shape as the
  `LOW_CONFIDENCE` threshold rule from 24d, and the Ningxia lock).
- **Reported the epoch_log gap rather than fixing it.** `results.json` never receives
  `epoch_log` when `--phase1-only` short-circuits before the line that attaches it. Real, minor,
  not worth a code change for a documentation completeness gap when the plain-text logs already
  carry the same numbers as the source of record.
- **Rewrote model_metrics.md's Stage 3 section rather than appending to it.** Found it was more
  stale than expected while updating — it still said "Phase 1 gate: metrics not recorded" and
  had never been touched with any of this session's caries-gate-v3 work. Fixed the whole
  section, not just added T0.1's number on top of a stale base.

## Open questions

- A confident augmentation verdict needs multiple seeds per arm — out of scope for a Tier-0
  close-out, worth flagging if it ever becomes a paper claim rather than a closed checklist item.

## Next steps

Unchanged: lesion-localization evaluator (no code yet, needed before Ningxia), connect the
Ningxia drive, T0.5 Mild decision, bone-loss version tag.

---

# Addendum 9 — C2: Ningxia connected, copied, leak-checked, evaluated (25 Aug)

## What was done

User connected the pen drive. Found `nangxia_dataset` (14 GB) — spelling matches what
`MASTER_PLAN_2026H2.md` §4.4 recorded (`D:\nangxia_dataset`).

**Copied test splits only (2.4 GB), leaving the 11.2 GB train split on the drive.** Deviated
from a literal "copy the dataset" on purpose and said so: we may never legitimately train on
Ningxia, so not having it locally makes that physically impossible rather than merely
forbidden. Verified: 12/12 split counts match source, 30/30 random files byte-identical,
manifest + README byte-identical, train confirmed absent.

**Zero leakage** against Tufts, DENTEX `disease/`, `quadrant_enumeration`,
`quadrant-enumeration-disease`, `quadrant` — each checked separately per the standing rule.

Results: caries lesion agreement **22.6–43.3%** across four hospitals (DENTEX internal 42.6%);
periodontitis affected-tooth sensitivity **0.8–5.4%**.

## The two catches — same root cause, caught at different stages

**1. Caught before running.** I had written in `lesion_localization.py` that only its GT loader
would need a Ningxia sibling and "nothing else assumes the DENTEX format." Wrong. Ningxia caries
lesions are 89–3,090 px against ~25,000 px tooth boxes → IoU 0.015–0.124, every true match below
the 0.30 threshold. Reusing the DENTEX matcher would have reported ~0% and looked like total
external failure.

**2. Caught after running, before reporting.** The first run applied centroid containment to
periodontitis too and gave 0.7–4.0%. I nearly wrote that up as "the bone-loss branch fails
externally." Checked the mask geometry first: periodontitis masks are **1 blob/image at median
365,680 px** — a single band across the alveolar ridge, ~8% of the image — versus caries at 2.5
blobs of 731 px. Rendered one: the centroid lands *between* teeth, in no tooth box. That metric
scores ~0% by construction regardless of model quality. Withdrawn and replaced with
affected-tooth sensitivity.

**Both are the same error**: assuming one dataset's annotation granularity transfers to another.
The corrected periodontitis conclusion is similar in magnitude to the artefact — which is
exactly why it was dangerous. A wrong method that produces a plausible number is worse than one
that produces an obviously broken one.

## Decisions made

- **Metric differs by category, deliberately.** Focal (caries) → centroid containment; diffuse
  (periodontitis) → affected-tooth sensitivity. Documented in the script so nobody "unifies"
  them later.
- **Reported two bounds for caries** (covered / strict 1:1) rather than picking one. A tooth can
  genuinely carry two carious lesions; one-to-one under-counts that, many-to-one is the faithful
  read of §4.3.4's per-lesion question. Picking one silently would be a choice disguised as a
  fact.
- **Flagged the "same_centre_as_train" trap.** That label describes *Ningxia's own* split
  design. We never trained on Ningxia, so all four splits are equally external to us — calling
  test2 "in-domain" in the paper would be wrong.
- **Did not synthesise negatives** from the other disease categories, per §4.3's explicit
  prohibition. Specificity/AUC stay uncomputable on Ningxia; they come from Tufts.

## Open questions

- Image-level caries sensitivity is ~96% and effectively saturated — the gate over-calls, and at
  ~22 teeth/image it nearly always flags one. Report as the weak metric §4.3.4 predicted.
- `impacted_teeth` (2,567 images) is entirely unevaluated — no branch predicts it. Could be
  future work or an explicit scope statement.
- One genuine intra-dataset duplicate found (`impacted_teeth/test2/45.png` ≡ `178.png`).
  Harmless here; would matter if impaction were ever added.

## Next steps

C2 has numbers. **C1 (VLM baseline) is now the only headline contribution still at zero** —
W5 in the plan. Also open: T0.5 Mild decision, bone-loss version tag.
