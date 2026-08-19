# 2026-08-19/20 — Week 2 engineering prep: T0.6, R2, T0.3, T0.2, detector freeze

**Session goal:** Pick up Week 2 (`MASTER_PLAN_2026H2.md` §5, Aug 22–28) engineering work
one day early — detector reconciliation, mask-aware cropping, macro-F1 checkpointing, and a
DENTEX held-out split — as far as it can go without GPU access or missing external data,
while flagging every real blocker encountered rather than working around it silently.

No models were trained and no metric changed in this session. This machine has no GPU
(`torch.cuda.is_available()` is `False`) — all training-shaped work here is preparation for
a run on the E2E H100/Kaggle, not the run itself.

---

## Part 0 — Resuming from the prior session

Read `transfer.md` and independently re-verified its claims before trusting them: `git
status`/`git log`/`git rev-list` confirmed HEAD at `c9105db`, 0 ahead/0 behind
`origin/main`, and the three untracked items it listed (`docs/research/clinical_dataset_provenance.md`,
`notebooks/bone_loss/06_cej_estimation_v3.ipynb`, `survey_paper/`) were still present and
untouched. Separately confirmed `survey_paper/` is genuinely stale (47 `@` entries in its
`source.bib` vs. 71 in the committed `Survey Paper Latex folder/`, and no git history at
all), but did not act on any of the three untracked-file decisions — the user chose to focus
this session on Week 2 engineering instead when asked.

---

## Part 1 — T0.6: detector reconciliation

Formally reconciled the two prior YOLO detection runs (H200/768px vs. A100/1024px,
previously flagged "unreconciled" in `notebooks/yolo_detection/README.md`). The A100
config (imgsz 1024, batch 32, patience 30, degrees 10 rotation aug, seed 42) is now declared
canonical in writing, justified by ~16 mAP@0.5 points of validation margin before the H200
run's total lack of test evaluation is even considered.

While doing this, found `scripts/yolo/train_yolo.py` had drifted from the real A100 run
(`batch=16` vs. the actual `32`, run name `tufts_v1` vs. `tufts_clean_v1`, no explicit
seed/deterministic) — fixed so the script now faithfully reproduces the canonical run.

Pre-registered the acceptance criterion for the planned YOLOv11l-seg retrain (R1) **before**
running it, per T0.6's explicit instruction: test box mAP@0.5 ≥ 0.75, test mask mAP@0.5 ≥
0.65, same test-set-touched-once discipline as Ningxia. Full writeup:
`docs/research/T0.6_detector_reconciliation.md`.

**Blocker found, not fixed:** the master plan's claim that Tufts segmentation data needs "no
new annotation" doesn't hold cleanly. Investigated
`notebooks/bone_loss/01_tufts_data_exploration_v2.ipynb`'s saved cell output (from when the
Google Drive mount was live) and found `teeth_mask/` (raster masks) is only 308/1000
complete at the source — not usable as claimed — but `teeth_polygon.json` (1,000/1,000
records, same `External ID` schema as `teeth_bbox.json`) is complete and is the right
source. Neither file is on this machine right now. Wrote both scripts that will consume it
once it's back — `scripts/yolo/convert_tufts_to_yolo_seg.py` (polygon → YOLO-seg label
format, using a largest-fragment-per-object heuristic to discard what looks like
edge-tracing noise in the polygon data — unverified beyond one inspected record, flagged for
a spot-check) and `scripts/yolo/train_yolo_seg.py` (training script, args matched to the
canonical config) — but could not test either against real data.

Also could not locate `models/06_yolo_detection_a100_run/best.pt` anywhere on this machine
or in `_repo_archive/` (searched both) to compute the weight hash "freeze and version"
requires. That step stays open.

---

## Part 2 — R2: mask-aware cropping (implemented and tested)

Unlike Part 1, this one is actually done and verified — it doesn't need real mask data to
implement or test, only to eventually *use*. Added `rasterize_polygon`,
`extend_mask_below_root`, `apply_soft_mask_attenuation`, `extract_mask_aware_crop` to
`src/crop_generator.py`. Design: soft attenuation (dim to 50%, never zero) rather than a hard
cutout, and the kept region is explicitly extended downward within the tooth's own column
span before attenuation, so the sub-root bone signal the periodontal branch needs isn't
treated as background. 8 new tests added to `tests/test_crop_generator.py`, all passing (had
to `pip install opencv-python-headless` locally first — it's a declared `requirements.txt`
dependency that just wasn't installed in this environment). Full repo test suite (17 tests
across 4 files) passes with no regressions.

---

## Part 3 — T0.3: macro-F1 checkpointing (code fixed, not re-run)

`notebooks/caries/phase-1.ipynb` selected its "best" checkpoint by raw validation accuracy at
all five training stages — a known gap already flagged in `PAPER_MATERIAL.md` §8.1 and
`PUBLICATION_TODO.md` T0.3. Read the full notebook (small enough — 56 KB — to read directly
rather than delegate) and used the `NotebookEdit` tool to fix all three `validate()`
definitions to also compute and return macro-F1, and all five checkpoint-selection loops to
compare on it instead. This brings the caries notebook in line with what the two bone-loss
notebooks already did correctly, and with what `configs/dataset_config.yaml` already declared
(`training.early_stop_metric: "val_f1_macro"`) but the caries notebook never actually read.

One cell (`best_val_acc = 0.8195  # VERY IMPORTANT`, a hand-copied resume threshold from a
previous Kaggle session) needed care: since the metric changed, that accuracy number is no
longer meaningful as a resume threshold. Rather than guessing an equivalent, recovered the
actual macro-F1 of that exact checkpoint from the notebook's own already-saved
`classification_report` output two cells earlier (macro avg f1-score = 0.72) and used that
instead — grounded in a real number already in the notebook, not fabricated.

All 8 edited cells verified to still parse as valid Python (`ast.parse`) after editing.

---

## Part 4 — T0.2: DENTEX held-out split (scripted and fixture-tested, not run on real data)

There's no patient/study identifier anywhere in this repo's DENTEX pipeline and no raw
(pre-crop) DENTEX copy — the train/val split was pre-baked into an externally-uploaded Kaggle
dataset. Asked the user how to handle this; they picked carving a new test split out of the
existing `val/` pool (grouped by source-image ID recovered from crop filenames,
`{image_id}_{crop_id}.png`) over waiting for raw-data access. Wrote
`scripts/dentex/split_dentex_holdout.py` to do this — deterministic seeded split, groups by
image ID so no source OPG's crops land on both sides, emits a `splits.json` manifest.

Verified the actual logic (not just read it) against a synthetic 44-file/20-image-ID fixture
in the scratchpad: dry-run mode previews correctly, real mode moves the right files, and a
programmatic check confirmed no image ID crosses the val/test boundary. Fixture deleted after
verification. Not run against the real Kaggle-hosted data — that has to happen wherever the
data actually is.

---

## Part 5 — round 2: the full Week 2 checklist, item by item

After the first pass above, the user pasted the actual detailed Week 2 checklist (more
granular than the master-plan table this session started from) and asked for it completed in
full. Re-scoped against it directly rather than re-deriving from the higher-level plan:

- **Detector comparison table** — expanded `T0.6_detector_reconciliation.md` §1 to cover
  every axis the checklist named (dataset version, split, image size, epochs, hardware,
  augmentation, all metrics for both val and test), not just the subset in the first pass.
  Also surfaced that the two runs differ on four axes, not one (imgsz, batch,
  patience/workers, rotation aug) — so this pair cannot itself be read as an isolated
  augmentation ablation, a caveat worth keeping for the eventual paper.
- **Bone-loss val/test audit** (checklist item 4's last bullet) — grepped every citation of
  the 0.9233 macro-F1 result across the repo (14 files). All of them already correctly label
  it validation. Nothing to fix; documented that the audit was run and passed clean.
- **Two-arm augmentation ablation (T0.1)** — the biggest gap from the first pass. Built it
  into `notebooks/caries/phase-1.ipynb` as a new "Phase 2b — Arm B" section: same recipe as
  Arm A, only the training-set transform actually changes. Caught two of my own bugs before
  calling it done: a missing `f1_score` import (it's only ever imported *locally* inside the
  notebook's `validate()` functions, not at module scope, so the naive comparison cell would
  have raised `NameError`), and a self-inflicted index-shift bug where a same-session fix
  attempt landed on the wrong cell after an earlier insert shifted positions — caught by
  re-reading the file's actual state rather than trusting the edit tool's success response,
  then fixed both affected cells and re-verified with `ast.parse` and a grep for dangling
  variable references.
- **T0.3 criterion + operating threshold, made explicit** — added `PAPER_MATERIAL.md` §6.7,
  stating plainly that all four classifiers now checkpoint on macro-F1, and — new information
  this round — that none of them have any calibrated decision threshold; all four use
  uncalibrated argmax (equivalent to a fixed 0.5 threshold for the three binary classifiers).
  That's real, was previously unstated anywhere, and is explicitly R3's job (Week 6), not
  Week 2's.

**What's still genuinely not done, and why:** re-deriving every downstream crop/classifier
input from a frozen canonical detector, and actually running any of the training this session
prepared (seg retrain, two-arm ablation, DENTEX split-then-retrain) — all of it needs either
GPU (none available in this environment) or the two files still missing on this machine
(`teeth_polygon.json`, `best.pt`). These were named as blockers in the first pass and remain
exactly that; nothing in round 2 changed their status. Flagging this explicitly rather than
letting a long list of completed sub-tasks read as "the whole checklist is done" — it isn't;
the checklist's actual weight (a re-trained, re-evaluated system) is still gated on GPU access
and two missing files.

---

## Part 6 — 20 Aug: the missing weights turn up, detector gets frozen for real

After round 2 above, the user located `best.pt`/`last.pt` themselves on a different
machine/session and synced `_repo_archive/yolo_a100_run_workspace/` and
`_repo_archive/datasets_workspace/` onto this one (both were confirmed empty here at the end
of round 1 — see Part 1's blocker note). Also relevant: a `git pull` mid-session brought in a
new commit (from the user's own account, authored elsewhere, minutes before the pull) that
restructured `_repo_archive/` to live *inside* the repo rather than as a sibling, with
`.gitignore` rules anticipating exactly these three folder names — which is what made it
possible to recognize the sync when it landed.

**Verified before trusting, not just copied on faith:** file sizes (51,227,225 bytes, matches
`run_summary.txt`'s "51 MB"), `args.yaml`/`results.csv` byte-identical against the
already-committed copies, and — the strongest check — actually loaded `best.pt` under
Ultralytics (installed fresh for this) and confirmed `task=detect`, one class (`tooth`),
25,311,251 parameters, matching the documented 25.28M. Only after all of that copied the
files into `models/06_yolo_detection_a100_run/` and re-verified the copy byte-identical by
SHA-256. This closes the one part of T0.6 that was genuinely blocked before: the detector is
now frozen and versioned (`tooth-detector-a100-1024-v1.0`), not just reconciled on paper.

**What this does NOT unblock, and I was careful to say so rather than let "found the
weights" imply "Week 2 is done":** `datasets_workspace/` — the other synced folder — turned
out to hold only the small scripts and notebooks (22 MB), not the 2.2 GB of raw Tufts data
its own manifest entry describes it as containing. No `teeth_polygon.json`, no raw radiograph
images, anywhere on this machine, even after the sync. That means the seg retrain (R1) and
re-deriving crops from the now-frozen detector are still exactly as blocked as they were in
round 1 — freezing the detector and finding the Tufts source data turned out to be two
independent problems, and only one of them got solved by this sync.

**Also verified and completed as part of "restructuring the archive" per the user's
request:** confirmed `YOLO_trained.ipynb` in the archive is byte-identical to the
already-committed `notebooks/yolo_detection/a100_1024px_150ep.ipynb` (nothing to extract);
found three test-eval prediction JPGs that existed in the archive but were never copied into
`docs/results/figures/yolo_detection_a100/` during the original 2026-08-12 cleanup, and
copied them over. Added an addendum to `_repo_archive/ARCHIVE_MANIFEST.md` recording exactly
which archived folders are actually present on this machine vs. the original manifest's
description, so a future session doesn't have to re-run this detective work.

---

## Decisions made

1. **A100 config is canonical** for Stage-1 detection going forward (§1) — data-justified,
   not a coin flip, and now written down so it can't be silently re-litigated.
2. **Pre-registered, not post-hoc, acceptance criterion for the seg retrain** (§1) — the
   explicit point of T0.6's phrasing. The numeric thresholds (0.75 box / 0.65 mask) are a
   judgment call absent any prior mask baseline on this data; open to revision by the
   user/advisor, but only *before* the retrain runs, not after.
3. **Soft attenuation, not hard masking, for R2** (§2) — a wrong mask edge degrades instead
   of erasing signal, and bone-context preservation is a hard requirement from the master
   plan, not an optimization.
4. **DENTEX test split carved from val, not deferred pending raw data** (§4) — user's
   explicit choice. Documented clearly, in three separate places
   (script docstring, `RESULTS_LOG.md`, `PAPER_MATERIAL.md` §7.2/§9), that this is a weaker
   independence guarantee than a from-scratch three-way split, so it can't quietly get
   presented as equivalent in the eventual paper.

## Open questions

1. ~~Where is `models/06_yolo_detection_a100_run/best.pt`?~~ **Resolved 20 Aug** — found in
   `_repo_archive/yolo_a100_run_workspace/`, verified, frozen. See Part 6.
2. Where can `teeth_polygon.json` (Tufts) be re-fetched from? **Still open** — checked the
   newly-synced `_repo_archive/datasets_workspace/` on 20 Aug and it wasn't there either
   (only scripts/notebooks, not the raw 2.2 GB dataset). Most likely lives only in Google
   Drive at this point (`MyDrive/Capstone/tufts/ZIP/Segmentation/`, per the Colab mount path
   in `01_tufts_data_exploration_v2.ipynb`), which isn't synced to any machine checked so far.
3. Is the largest-polygon-fragment-per-object heuristic in
   `convert_tufts_to_yolo_seg.py` actually correct, or do some teeth have genuinely disjoint
   mask regions that it would wrongly discard? Unverifiable without real data.
4. The three untracked-file decisions from `transfer.md` (§1 there) are still open — not
   touched this session, by the user's explicit choice to prioritize engineering instead.

## Next steps

1. Locate/re-fetch `teeth_polygon.json` **and the raw Tufts radiograph images** (both still
   missing, independent of the now-resolved `best.pt`); run the seg retrain against the
   pre-registered criterion in `docs/research/T0.6_detector_reconciliation.md` §2.
2. Run `scripts/dentex/split_dentex_holdout.py` against the real Kaggle DENTEX data; commit
   the resulting `data/dentex/splits.json`.
3. Re-run the caries cascade (`notebooks/caries/phase-1.ipynb`, both Arm A and the new Arm B
   augmentation-ablation section) on Kaggle/H100 with T0.2's new split and T0.3's macro-F1
   checkpointing in effect; report both arms' val **and** test numbers, and replace
   `PAPER_MATERIAL.md` §7.2 and `model_metrics.md`'s caries table with them.
4. Spot-check the polygon-noise heuristic in `convert_tufts_to_yolo_seg.py` visually against
   a handful of real OPGs before trusting it for a full training run.
5. Once T0.6's seg retrain and T0.2/T0.3's caries re-run both land, re-derive every downstream
   crop and classifier input from the frozen canonical detector, per the Week 2 checklist's
   first item — this depends on both of the above and hasn't been started.
6. R3 (calibration + abstention head, Week 6) will give all four classifiers an actual tuned
   operating threshold in place of today's uncalibrated argmax — not a Week 2 item, but now
   explicitly named as a gap in `PAPER_MATERIAL.md` §6.7 so it doesn't get forgotten.
7. Revisit the three untracked-file decisions carried over from the prior session.
