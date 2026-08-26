# 2026-08-26 — Resuming on Windows: split regenerated from code, R1 staged, JarvisLabs runbook

## Session goal

Re-establish a working state on the Windows machine, close out the fixes the handoff document
called for, and plan the GPU phase against a real budget (₹900 on JarvisLabs).

## What was done

### 1. Discovered the local checkout was 67 commits stale — this dominated everything else

`git status` looked clean and `transfer.md` read plausibly, but
`git rev-list --left-right --count origin/main...HEAD` returned **67 / 0**: local `main` was
an ancestor of `origin/main`, 67 commits behind, with zero local commits. The `transfer.md`
being read as the source of truth was the **20 August** handoff document, superseded by a full
rewrite pushed on the 26th.

Everything the stale copy described as blocked or missing had in fact been done on the macOS
machine in between — Stages 5–6 integration (`run_inference.py`), the Streamlit/Docker
deployment, C2 external validation on Ningxia, the FDI head v2.0 adoption, the caries gate v3
rebuild, and the recovery of `split_v1.csv`. The stale `CLAUDE.md` loaded into the session even
described the Universal→FDI lower-arch bug as open; it was fixed in `f8b31f8` and
regression-tested.

Fast-forwarded to `ae37acc`. One untracked file blocked the merge —
`docs/research/clinical_dataset_provenance.md`, which origin also tracks. Compared them before
touching anything: the local copy was the stale 16 Aug draft **containing an unredacted clinic
patient identifier**, while origin's carries the 21 Aug correction and redacts it to
`<DEVICE>.RVG\<PATIENT-ID>`. Origin's strictly supersedes it. Stashed the local copy rather
than deleting it (`git stash` entry: *"stale 16-Aug local provenance draft, superseded by
origin"*), and a byte copy also sits in this session's scratchpad.

### 2. Made the frozen Tufts split regenerable from code — `RESULTS_LOG.md` 2026-08-26c

`outputs/eda_tufts/split_v1.csv` was absent on Windows (a whole-machine search confirmed it,
and `_repo_archive/datasets_workspace/` here has the notebooks but not `outputs/`). This is
the third time this file has been a blocker.

Rather than copying it from the macOS machine, extracted the generating logic from
`_repo_archive/datasets_workspace/week1_tufts_eda_v2.ipynb` (cells 6, 12, 24) into
**`scripts/tufts/regenerate_split_v1.py`**. It reproduces the file **byte-for-byte**, verified
on four invariants recorded in the repo before the script existed:

| Invariant | Expected | Got |
|---|---|---|
| split counts | 700 / 150 / 150 | ✅ |
| empty-label images per split | 21 / 5 / 6 | ✅ |
| documented duplicate leak | `590.JPG`→test, `591.JPG`→train | ✅ |
| SHA-256 | `6de8cef2…ccb58b` | ✅ exact |

### 3. Rebuilt `dataset_seg/` — R1's training input now exists here

Ran `scripts/yolo/convert_tufts_to_yolo_seg.py` **unmodified**, using only its env-var
overrides. Output: 700/150/150 images, **26,005 instances** (18,268 / 3,807 / 3,930), 334 MB.
The test count of 3,930 matches the number `T0.6` §2 pre-registered its acceptance caveat
around, which confirms this is the same conversion the macOS machine produced, not merely a
similar one.

### 4. Rewrote `docs/research/GPU_SETUP.md` for JarvisLabs

The document was an E2E Networks runbook; the project has moved to JarvisLabs. Verified
against JarvisLabs' live pricing page and CLI/SSH docs on 26 Aug: **A100 80GB at ₹140.94/hr**
(so ₹900 = 6 h 23 min), paused instances bill storage at ₹0.0130/GB/hr, and the `jl` CLI
covers create/upload/exec/ssh/download/pause/destroy. Added a full R1 command sequence, a
cost estimate derived from this project's own A100 bbox run (16.6 s/epoch → ~1.5–2 h, ~₹210–280
for R1), and the E2E material preserved as a superseded appendix.

### 5. Fixed stale status in `CLAUDE.md` §6

It still asserted "Stages 5–6 … do not exist" and "Four models are trained". Both false since
24–26 Aug. Verified against the working tree (`scripts/run_inference.py`, `app.py`,
`Dockerfile`, `models/07`–`10`) before rewriting, per rule 4's own instruction not to guess.
Replaced the model count with a pointer to `models/README.md` and the `DEF_*` defaults, since
a count is exactly the kind of fact that goes stale.

### 6. Verified the environment

65/65 tests pass; `verify_invariants.py` clean (several checks SKIP for want of DENTEX and the
caries gate checkpoint).

## Decisions made

- **Fast-forwarded rather than asking first.** Zero local commits, one untracked file that was
  backed up and demonstrably superseded, and the merge was a pure fast-forward — reversible
  with `git reset --hard ad71ee4`. Continuing to reason about a 67-commit-stale tree would have
  produced confidently wrong work; nothing else in the session was trustworthy until this
  was done.
- **Regenerated the split instead of copying it from the Mac.** Copying solves it once, for one
  machine. The file had already been a blocker three times *because* it is gitignored and was
  treated as an artefact rather than a derivation. The EDA notebook declared its own
  determinism ("random seed FIXED to 42") the whole time. Extracting that into a self-verifying
  script closes the failure mode rather than deferring it.
- **Did not weaken the four invariant checks to "close enough".** The hash matching exactly is
  what makes this a reproduction rather than a plausible re-split — and a plausible re-split
  would silently invalidate every reported Tufts number. The script exits non-zero on any
  mismatch for the same reason.
- **Left the `numpy<2` pin in `requirements.txt` alone.** Verified it does not hold on this
  machine's stack (numpy 2.4.6 + scipy 1.17.1 + torch 2.13.0 runs `linear_sum_assignment` and
  torch↔numpy conversion fine, 65/65 green), but the pin still protects the macOS environment
  every published number was produced in. Documented the nuance in `GPU_SETUP.md` §6 and
  `transfer.md` §8 instead of editing the constraint. **The real risk is the reverse of the
  comment's warning**: pip downgrading numpy and breaking a GPU image's prebuilt torch.
- **Flagged, and did not act on, the warm-start trap in `transfer.md` §6.** Step 2 suggested
  uploading `best.pt` "for reference/warm-start". `train_yolo_seg.py` starts from COCO-pretrained
  `yolo11l-seg.pt`, and §2's pre-registration permits only the model and data to change —
  warm-starting would be a third change and would void the comparison. Rewrote the step to say
  so explicitly.

## Open questions

- **Which `--gpu` string selects the 80 GB A100 on JarvisLabs?** The public CLI docs' `create`
  sub-page 404s, so the exact accepted values were not verifiable from here. `GPU_SETUP.md` §2a
  has a preflight (`jl create --help`, then `jl list` and `nvidia-smi`) to confirm before
  spending — a wrong card discovered 40 minutes into training costs the whole run.
- **`docs/research/clinical_dataset_provenance.md` is in a stash, not the working tree.** The
  tracked version supersedes it; the stash can be dropped once someone confirms nothing in the
  16 Aug draft is worth keeping. It contains an unredacted patient identifier, so it should not
  be committed as-is in any case.
- **`scripts/yolo/rotate_tufts_radiographs.py` has a self-contradicting docstring.** The 22 Aug
  correction block at the top says CCW (`ROTATE_90`) is correct — and the code does that — but
  a paragraph further down still reads "Rotation direction (90 deg CLOCKWISE, raw → portrait)".
  Harmless today because `Radiographs_rotated/` already exists and is verified 840×1615, but it
  is exactly the kind of stale sentence that misleads someone re-running the step.
- **DENTEX is not on this machine (~14 GB).** Whether to fetch it here, or leave caries and the
  bone-loss cross-corpus experiment to the macOS machine, is unresolved and shapes what a
  second GPU session could even do.

## Next steps

1. **Run R1 on JarvisLabs** — `GPU_SETUP.md` §3 has the exact command sequence. Preflight the
   card first. Estimated ~1.5–2 h / ~₹210–280 of the ₹900.
2. **On return: freeze, tag, and measure.** Evaluate the held-out test split exactly once
   against the pre-registered bar (box mAP@0.5 ≥ 0.75 **and** mask mAP@0.5 ≥ 0.65); if either
   is missed, report a documented negative and keep the bbox model canonical. Then
   `run_summary.txt` + SHA-256 + version tag, `RESULTS_LOG.md` entry, `model_metrics.md` and
   `PAPER_MATERIAL.md` per rule 1.
3. **Re-measure Stage-2 end-to-end after the detector changes.** Its 46.6% is capped by the
   detector's 67.0% recall; if recall moves, the ceiling moves, and that must be measured, not
   assumed.
4. **Fetch `models/09_caries_gate_v3/caries_gate_v3.pth`** so `run_inference.py` works on this
   machine (`docs/EXTERNAL_DRIVE.md`).
5. **Zero-compute items still open**, none of which should consume GPU time: T0.5 (the n=6 Mild
   severity decision), version-tagging the bone-loss weights, `docker build` verification, the
   Tufts Drive permissions fix, and IRB paperwork.
