# 2026-08-27 (second session) — Cold start, the last untagged models, and C2 re-measured

## Session goal

Come up to speed with no prior context, verify the state the previous session left, then work.
Three phases: (1) orientation, which turned into a rule-1 repair; (2) tag the bone-loss weights;
(3) re-measure C2 on Ningxia against the newly adopted seg detector. All zero-GPU.

## What was done

### 1. Verified the handed-over state rather than trusting it

Read `transfer.md`, `CLAUDE.md`, the 27 Aug session memory, `PUBLICATION_TODO.md`'s status
block and `MASTER_PLAN_2026H2.md` §5, then checked the claims against the working tree:

- **65/65 tests pass**, `verify_invariants.py` **all invariants hold** — with exactly the SKIPs
  §8 predicts for this machine (no DENTEX enumeration corpus, no caries gate).
- `run_inference.py:94` confirms `DEF_DETECTOR = models/11_yolo_seg_tufts_r1/best.pt`, so the
  adoption really is wired, not just written down.
- Working tree clean at `6c79725`; `models/11_yolo_seg_tufts_r1/best.pt` present (53.3 MiB).

### 2. Found that rule 1 item 3 had not been executed

2026-08-27b/d/e went into `RESULTS_LOG.md`, `model_metrics.md` and `transfer.md`. They did
**not** go into `PAPER_MATERIAL.md` or the root `README.md`. Established by grep, not by
impression: `PAPER_MATERIAL.md` contained **zero** occurrences of `58.3`, `0.8100` or `70.6`,
and still asserted the old story in three separate places.

So the largest single result this project has recorded (+12.0 points end-to-end) and a changed
Stage-1 default were absent from the one document `PAPER_MATERIAL.md` exists to be — the source
the paper is written from.

Propagated into `PAPER_MATERIAL.md` §7.1 (seg table, the missed mask bar, the withdrawn run as
a methods note), §8.5, §8.10, §9; and into `README.md`'s stage table, metrics table,
limitations blurb and publication assessment.

### 3. The actual bug: a fresh clone could not work, and would not say why

`README.md`'s clone-and-run recipe said to fetch `models/06_yolo_detection_a100_run/best.pt`.
The pipeline default had moved to `models/11_yolo_seg_tufts_r1/best.pt` — **which is not on
Drive**. Following the README exactly gets you the wrong checkpoint and then a missing-file
error naming a file the README never mentioned.

Fixed: the recipe now names the real default, flags that it is not yet uploaded, and documents
the `--detector` fallback to the bbox detector along with its honest cost (46.3% end-to-end,
not 58.3%).

### 4. Docker is closer than the docs think

`transfer.md` §3 item 7 has said "daemon unavailable every session so far" for days. On this
machine `docker version` reaches the Docker Desktop named pipe and reports it missing — i.e.
**the CLI is installed and only the engine is stopped**, which is a one-click user action, not
a missing dependency. Re-flagged as the cheapest unblockable item here.

## Decisions made

- **Repaired the docs before starting any new work.** The temptation was to pick up a backlog
  item; but an unpropagated result is exactly the failure mode `CLAUDE.md` was written against,
  and it was actively costing a fresh clone.
- **Did not rewrite the correctly-scoped historical tables** in `src/README.md` and
  `models/README.md`. Their 46.5% / 46.58% figures are real measurements on the bbox detector
  and are the honest basis for a head-vs-head comparison. Added a pointer saying so and naming
  the current number, instead of overwriting valid history with current-best.
- **Recomputed nothing.** Every figure written was copied from the 27 Aug entries and
  `run_summary.txt`. A propagation pass that quietly re-derives numbers is a second result, not
  a propagation.
- **Logged it as a milestone** (`RESULTS_LOG.md` 2026-08-27f) even though it produced no new
  number, because rule 1 counts a significant bug fix, and the fresh-clone break was one.

## Open questions

- **Does `docker build` actually pass?** Still unknown. Now blocked only on the user starting
  Docker Desktop.
- **Should `validate_fdi_assignment.py`'s defaults be realigned** to the current detector and
  head? 2026-08-27e deliberately left them on the old pair so historical numbers stay
  reproducible, at the cost of defaults that no longer describe the pipeline. That trade was
  never explicitly decided — it was inherited.
- **Is there a systematic check for "a `DEF_*` constant changed"?** This session's break came
  from a default moving without a grep for paths naming the old one. `verify_invariants.py`
  pins weight *hashes*; nothing pins the *documentation* that tells a human which file to fetch.

## Phase 2 — the last untagged models, and the check that was wrong

Tagged Stages 4a/4b (`bone-loss-binary-resnet18-v1.0`, `bone-loss-severity-resnet18-v1.0`) —
the last trained models with no version tag and no recorded hash, despite being pipeline
defaults for months. Nothing retrained; the April artifacts, now pinned. `verify_invariants.py`
went 4 → 6 pinned checkpoints.

**Writing the summary broke the invariant check, which is how a bug in the check surfaced.**
It read the sha256 as "the last 64-hex token anywhere in the file", so models/03's summary —
which documents both `best` (the default) and `final` (unused) — verified the default against
the wrong file's hash. Correct only while every summary happened to name one checkpoint.
Fixed by attributing each hash to the nearest preceding weight filename, extracted as
`hash_from_summary()`, covered by 8 tests.

**Bone-loss class order upgraded from inferred to confirmed.** The checkpoints are raw
`state_dict`s with no `class_to_idx`; `run_inference.py` honestly said "Inferred, not read".
Two independent confirmations agree: the FocalLoss alpha ratio 2.258/0.642 = 3.5171 matches
the class-count ratio 2500/711 = 3.5162 to 0.03% (so index 0 is the majority class, normal),
and `training_summary.txt` labels its own scores "F1 Normal (cls 0)" / "F1 Diseased (cls 1)".

## Phase 3 — C2 re-measured on Ningxia

Data was reachable at `D:
angxia_dataset` (the user supplied it). Two blockers first:

1. **`ningxia_external.py` hardcoded its weights** — old detector *and* old v1.0 head, no
   override, and nothing in its output recording what it loaded. That is precisely why the
   25 Aug C2 numbers went stale invisibly on 27 Aug. Now CLI flags defaulting to
   `run_inference`'s `DEF_*`, with resolved paths + SHA-256 written into every results file.
2. **`import ultralytics` monkeypatches `cv2.imread` globally.** Its replacement ends
   `return im[..., None] if im.ndim == 2 else im`, so `IMREAD_GRAYSCALE` yields (H, W, 1).
   Measured: (1480, 2893) before the import, (1480, 2893, 1) after, ultralytics 8.4.123.
   The mask reader died on the first image. Version-dependent (macOS runs 8.4.127), applied by
   an unrelated import, and **silent** for code that doesn't unpack the shape. One
   `read_mask_2d()` helper, 6 tests asserting patched and unpatched readers agree.

Also restored `caries_gate_v3.pth` from the DENTEX Drive via `gdown` (id resolved by listing
10,781 entries; now recorded in `EXTERNAL_DRIVE.md`), hash-verified against its pin. **All 7
checkpoints are now present on this machine — `run_inference.py` can complete here for the
first time.**

Ran a **control on the old detector first**, on this machine, before the treatment — the
27 Aug Stage-2 precedent. It reproduced 25 Aug, which is what licensed the comparison.

**Result: the same intervention, opposite outcomes.**

| Stage | Effect of the detector swap |
|---|---|
| Stage 2 FDI (DENTEX, internal) | +12.0 pts (measured 27 Aug, earlier session) |
| Stage 3 caries (Ningxia, 4 hospitals) | **+7.7 pts** pooled, improved on all four |
| Stage 4a bone loss (Ningxia, 4 hospitals) | **nothing** — 168 → 165 teeth flagged |

## Decisions made

- **Repaired the docs before starting new work.** An unpropagated result is the exact failure
  mode `CLAUDE.md` exists to prevent, and it was actively breaking clone-and-run.
- **Fixed the hash parser rather than reordering the summary.** Reordering would have silenced
  the symptom and left the trap armed for the next multi-checkpoint summary.
- **Ran a control instead of comparing against the published 25 Aug numbers.** Different
  machine, different cv2/ultralytics/numpy. The 27 Aug Stage-2 work had already found exactly
  that drift. The control cost 20 minutes of CPU and made the whole comparison interpretable.
- **Did not present test3's periodontitis 1.1% → 5.6% as improvement.** It is 4 → 23 teeth on
  50 images. Flagged as noise in every place it is written down.
- **Left `src/README.md` and `models/README.md`'s bbox-detector tables intact**, adding pointers
  instead. They are honest head-vs-head comparisons; overwriting valid history with
  current-best would destroy the comparison they exist to make.

## Phase 4 — closing the last stale number

Re-ran `lesion_localization.py` (DENTEX internal lesion agreement) on the seg detector, control
first. **42.0% → 44.3%** (201 → 212 of 479 GT polygons; denominator model-independent). The
control reproduced the published 42.6% to within 0.6 pp.

Third appearance of the same signature: predicted-positive teeth *fell* 773 → 755 while correct
localisations *rose*. The seg detector finds fewer wrong things, not more things.

**What it unlocks:** internal and external caries are now both on the same detector, so the
comparison is finally like-for-like — and the gap more than halved.

| | internal (DENTEX) | external (Ningxia, pooled) | gap |
|---|---|---|---|
| old detector (control) | 42.0% | 33.1% | 8.9 pp |
| **seg detector** | **44.3%** | **40.8%** | **3.5 pp** |

Much of what read as caries domain shift was a detection problem. Carefully *not* written up as
"caries generalises well" — 40.8% is weak absolutely, and 3 of 4 hospitals sit below internal.

Also fixed two things in that file: a **disproven claim** still in its docstring (that only the
GT loader would need a Ningxia sibling — the *matching criterion* doesn't transfer either;
corrected in `ningxia_external.py` on 25 Aug but never back here), and a **provenance gap** —
its JSON recorded no weights, so two result files were distinguishable only by directory name.
That is exactly the gap that let 42.6% go stale unnoticed.

**No pipeline number is now measured on the superseded detector.**

## Open questions
- **Bone-loss domain-shift fix — which approach?** Now a sharper question than before: the
  "shared root cause with the detector" hypothesis is falsified, so upstream fixes are ruled
  out. The DENTEX+Tufts combined-training trick is the obvious untried lever, and it needs
  DENTEX's ~13 GB training data, which is not on this machine.
- **Does `docker build` pass?** Docker Desktop is installed here but its engine is stopped —
  one user click from being testable, never once attempted.
- **Should `verify_invariants.py` also pin documentation?** Nothing catches a README naming a
  checkpoint path that is no longer the default; that is what broke clone-and-run this morning.

## Next steps

1. **Upload `models/11_yolo_seg_tufts_r1/best.pt` to Drive** — still the only thing between this
   repo and a working fresh clone. User-only action.
2. **Re-run `lesion_localization.py` on the seg detector** to close the last stale external
   number. Zero GPU, data present.
3. **Start Docker Desktop**, then run the build — closes a Review-1 blocker for zero compute.
4. Scope the bone-loss combined-training experiment; needs DENTEX fetched.
5. Unchanged zero-compute items: T0.5, the Tufts Drive permissions fix, IRB paperwork.

## Cost

**Zero.** No GPU rented; JarvisLabs balance unchanged at ₹650.81, 0 running, 0 paused. This
machine has no GPU (`torch 2.13.0+cpu`, no CUDA), so all 2,146 image-evaluations ran on CPU at
~1.7 s/image. Tests 65 → 79.
