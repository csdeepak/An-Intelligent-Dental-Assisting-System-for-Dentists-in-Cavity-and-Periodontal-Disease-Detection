# Transfer document — session handoff to a different machine

**Written:** 20 August 2026, at the user's explicit request to continue this session on a
friend's laptop. **Purpose:** let a new session (different physical machine) continue with
zero re-derivation and zero guessing. Every claim below is labeled by how it was established.

> **STATUS UPDATE — 21 August 2026. The handoff completed; most of this document is now
> history.** Read this block before acting on anything below it.
>
> - **§2's uncommitted changes were committed and pushed** before the switch (`9e3099d`,
>   `9fcf0d1`, `ad71ee4`). §0's warning and §5 step 1 are done. `clinical_dataset_provenance.md`
>   was correctly left out and is **not** on this machine.
> - **§3 / §5 step 4 — `outputs/eda_tufts/split_v1.csv` is NOT missing.** It is at
>   `_repo_archive/datasets_workspace/outputs/eda_tufts/split_v1.csv` on this (macOS) machine,
>   and has been verified to be the split the canonical detector was trained on. The 20 Aug
>   "exhaustive search" that missed it searched `C:\` and `D:\`. No decision is needed; no
>   substitute split is needed.
> - **§4's table is wrong for this machine.** The Tufts data did not need re-downloading — the
>   raw radiographs, the rotated radiographs, and `teeth_polygon.json` were all already here.
> - **The R1 seg dataset has been built for real** at `data/tufts/dataset_seg/` (26,005
>   instances). R1's only remaining blocker is GPU access.
> - **Still genuinely open:** the DENTEX split decision (§3, §5 step 3),
>   `clinical_dataset_provenance.md` (§5 step 6), and every SSH/E2E item in §3 and §5 step 5 —
>   none of which can be confirmed from this machine.
>
> Current state lives in `docs/session-memory/2026-08-21-split-recovery-and-seg-dataset-build.md`
> and `docs/research/T0.6_detector_reconciliation.md`, not here.

---

## 0. Read this first

1. **There are uncommitted, unpushed changes on THIS machine right now.** §2 lists them
   exactly. Until they're committed and pushed, `git clone`/`git pull` on the friend's laptop
   will **not** include them — a chunk of this session's work (the GPU setup doc, the DENTEX
   raw-data discovery, the Tufts real-data verification writeup) would simply be invisible
   there. **Do one of these before switching machines:**
   - Ask the current session to commit + push (same pattern used all session:
     say "commit this" then "push it") — recommended, keeps the git history the
     source of truth like everything else this session.
   - Or manually copy the modified/untracked files listed in §2 across via USB/cloud drive if
     you need to switch machines before that's done.
2. **Nothing on the new machine will have the ~390 MB of Tufts data, the SSH keys, or an E2E
   instance already set up** — those are local-machine or account-level, not git-tracked, by
   design. §4 says exactly how to reproduce what's needed.
3. **Read `docs/research/GPU_SETUP.md` and `docs/research/T0.6_detector_reconciliation.md`
   in full before doing anything else** — they contain the verified, current state of every
   blocker and every piece of prep work. Do not re-derive anything from scratch that's already
   answered there.

---

## 1. Verified git state

Checked via `git status`, `git log` on this machine, just now.

```
HEAD: 3c7059b  docs: log Week 2 detector-freeze and archive-triage results
Branch: main, tracking origin/main
```

Everything through `3c7059b` is already pushed — confirmed earlier this session via
`git push` (output: `2fd2721..3c7059b main -> main`). **Do not re-push those commits; do not
re-do that work.** A `git log --oneline -12` on the new machine will show the same history
back through `61eed08` (T0.6 reconciliation start) if you want to independently verify.

---

## 2. Uncommitted local changes on THIS machine (not yet pushed)

```
 M docs/research/T0.6_detector_reconciliation.md
 M docs/results/PAPER_MATERIAL.md
 M docs/results/RESULTS_LOG.md
 M docs/session-memory/2026-08-19-week2-engineering-prep.md
 M scripts/yolo/convert_tufts_to_yolo_seg.py
 M scripts/yolo/train_yolo_seg.py
?? docs/research/GPU_SETUP.md
?? docs/research/clinical_dataset_provenance.md
?? scripts/yolo/rotate_tufts_radiographs.py
```

What's in this batch, so nothing here reads as mysterious:

- **`GPU_SETUP.md` (new)** — E2E Networks provisioning checklist, verified live against
  `docs.e2enetworks.com` (not written from memory): exact console click-path, image choice
  (Pre-built → PyTorch), current GPU pricing table, disk budget, and the DENTEX raw-data
  finding (§3 below).
- **`T0.6_detector_reconciliation.md`, `PAPER_MATERIAL.md`, `RESULTS_LOG.md`,
  session-memory file** — updated to record that `teeth_polygon.json` and all 1,000 raw Tufts
  radiographs were located (Google Drive), downloaded, and the seg-conversion pipeline was
  run end-to-end against real data successfully (26,005 instances, zero errors). Also records
  the still-missing `outputs/eda_tufts/split_v1.csv`.
- **`rotate_tufts_radiographs.py` (new)** — formalizes the empirically-determined 90°
  clockwise rotation needed to turn the raw Tufts landscape images into the portrait shape
  every other script assumes. Was previously undocumented tribal knowledge; now it's code.
- **`convert_tufts_to_yolo_seg.py`, `train_yolo_seg.py`** — docstring/status updates only
  (moved from "untested" to "verified against real data") — logic unchanged from what's
  already committed.
- **`clinical_dataset_provenance.md` (untracked, deliberately NOT part of any commit)** — this
  one is intentionally left out of every commit this whole session. It documents real patient
  de-identification procedures for the private clinic dataset and needs your explicit
  decision (commit as-is / redact / keep local-only) before it ever enters git history. Don't
  sweep it into a commit by accident with a blanket `git add`.

**Recommendation:** commit the first group (everything except `clinical_dataset_provenance.md`)
in whatever scoped grouping makes sense — the session already has a clean precedent from
earlier commits like `5c0b442` and `f42933d` if you want to match that style — then push.

---

## 3. Major state as of this session (all independently verified, not just asserted)

### T0.6 / R1 — YOLOv11l-seg retrain: went from 3 blockers to 1 (plus GPU access)

- **Canonical bbox detector: frozen and versioned.** `best.pt`/`last.pt` located, verified
  (byte size, args.yaml/results.csv diff, loads under Ultralytics with correct params), copied
  to `models/06_yolo_detection_a100_run/` (gitignored). Version tag
  `tooth-detector-a100-1024-v1.0`, SHA-256 in `T0.6_detector_reconciliation.md` §1.
- **`teeth_polygon.json`** (1,000/1,000 records, 285 MB) and **all 1,000 raw radiographs**
  located at `https://drive.google.com/drive/folders/1_pPXCzNGlRuLaQhpqScX7sszSXSLQI-U`,
  downloaded to this machine at `data/tufts/ZIP/...` (gitignored, ~390 MB local, does **not**
  transfer via git).
- **Rotation direction (90° CW) empirically determined and visually verified** — 7 real
  images overlaid with real tooth polygons, every one traced correctly. See
  `rotate_tufts_radiographs.py` and `T0.6_detector_reconciliation.md` §3.2.
- **The real, unmodified `convert_tufts_to_yolo_seg.py` was run end-to-end against real
  data** (only path constants patched for the local test) — 26,005 instances, zero errors,
  instance counts closely matching the historical bbox baseline. The largest-polygon-fragment
  heuristic, previously flagged as unverified, is now confirmed correct.
- **Still missing: `outputs/eda_tufts/split_v1.csv`** — the frozen split the canonical bbox
  detector was evaluated on. Searched exhaustively (this Drive folder, both `_repo_archive/`
  locations, whole-machine filename search) — not found anywhere. **This is the one
  remaining blocker**, plus GPU access to actually run `train_yolo_seg.py`.

### T0.2 — DENTEX: a second Drive folder revealed more than expected

`https://drive.google.com/drive/folders/1DtdE_TYuYTeyvuaveQEvuhSpwL6U8Ovp` (10,446 files,
enumerated, not just assumed) contains not only the pre-processed crops `phase-1.ipynb`
reads, but also the **raw 705 source X-rays**, the **original COCO annotation file**
(`train_quadrant_enumeration_disease.json`), and the **original crop-generation notebooks**
for the disease-labeled subset. Full structure in `GPU_SETUP.md` §4.

**This means `scripts/dentex/split_dentex_holdout.py`'s "carve from val" fallback (written
19 Aug under the assumption raw DENTEX access was unavailable) may no longer be the best
option — a genuinely independent three-way split could now be built from scratch.** This was
**deliberately not rebuilt** this session — it's a real methodology decision (redo T0.2
properly now vs. proceed with the existing fallback), not something to default into silently.
**Needs a decision from you or whoever picks this up next.**

### Notebook version check — resolved, but re-confirm on the new machine

`C:\Users\csdee\Downloads\phase-1.ipynb` (this machine, "used for 4 months") was 123 cells,
pre-T0.3-fix. The repo's `notebooks/caries/phase-1.ipynb` (131 cells, includes the macro-F1
fix and the new Arm B augmentation-ablation section) is authoritative — already committed
and pushed. **Confirm the friend's laptop doesn't have its own older cached copy lying around
that could get confused with the repo's version.**

### GPU setup — verified against E2E's live docs, nothing launched yet

`GPU_SETUP.md` (§2 above, uncommitted) has the exact console click-path: **Pre-built → PyTorch**
image, **A100 80GB** recommended (matches what the existing detector was already trained on;
H100/H200 give "no material difference at this size" per the master plan's own compute
budget), storage set to **≥100 GB** (30 GB default is too tight). **No E2E instance has
actually been launched yet, as far as this session knows** — everything so far is
provisioning research and prep.

### SSH keys — a real security incident this session, now contained but not fully closed out

- The user pasted two private key files (`capstone.pem`, `ssh-key.pem` in Downloads,
  identical key material) into this conversation via `@` file-reference, which caused the
  full private key content to be read into the transcript. **Treat that key as compromised.**
  **Not confirmed: whether the matching public key was ever added to an E2E account, and if
  so whether it's since been removed/rotated there. Not confirmed: whether the two `.pem`
  files were deleted from Downloads.** Check both on whichever machine continues this.
- A fresh keypair was generated on **this machine only**: `~/.ssh/id_ed25519_e2e` (private,
  never displayed, 600 permissions) / `~/.ssh/id_ed25519_e2e.pub` (public, safe to share).
  **Not confirmed: whether the public key was actually added to the E2E account yet** — the
  user asked for this to be done, but it requires logging into E2E's console, which is
  something no Claude Code session will do (private-key generation is fine and was done;
  entering account credentials anywhere is a hard line that doesn't get crossed regardless of
  request). Manual steps are in this session's own chat history and are simple: My Account →
  SSH Keys → Add New SSH Key → paste the `.pub` content → Add SSH Key.
- **On the friend's laptop: do not copy `id_ed25519_e2e` over.** Generate a fresh keypair
  there instead (`ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_e2e -N ""`, same as this session)
  and add *that* machine's public key to the E2E account as an additional key — E2E supports
  multiple SSH keys per account, so both machines can have their own without sharing one
  private key across machines.

---

## 4. What does NOT transfer to the new machine, and how to get it back

| Item | Where it lives now | How to reproduce elsewhere |
|---|---|---|
| Tufts `teeth_polygon.json` + rotated radiographs (~390 MB) | `data/tufts/ZIP/...` on this machine, gitignored | Re-download from the Google Drive link in §3 / `GPU_SETUP.md` §4 |
| SSH keypair(s) | `~/.ssh/id_ed25519_e2e*` on this machine only | Generate a fresh pair on the new machine (see §3 above) — do not copy the private key |
| Any E2E instance state | E2E's own infrastructure, account-level | Same E2E account is shared across machines by design — just log in from the new machine |
| The compromised `.pem` files | `C:\Users\csdee\Downloads\` on this machine | Don't copy these anywhere. Rotate/delete per §3. |

---

## 5. Immediate next steps for whoever picks this up

1. Commit and push the changes in §2 (or manually transfer them) so the new machine's `git
   pull` actually has everything.
2. Read `GPU_SETUP.md` and `T0.6_detector_reconciliation.md` in full.
3. Decide: rebuild the DENTEX split from the newly-found raw data, or proceed with the
   existing `split_dentex_holdout.py` fallback (§3).
4. Locate `outputs/eda_tufts/split_v1.csv`, or make an explicit decision to accept a new
   split for the seg retrain with the comparability caveat documented everywhere the
   resulting numbers get reported.
5. On whichever machine actually drives the E2E instance: generate its own SSH keypair, add
   the public half to the E2E account, launch the instance per `GPU_SETUP.md`, and confirm
   the old compromised key situation (§3) is fully closed out.
6. The three untracked-file decisions carried over from before this session
   (`docs/research/clinical_dataset_provenance.md`, and two already resolved —
   `survey_paper/` archived, CEJ v3 notebook triaged and committed) — only
   `clinical_dataset_provenance.md` is still open.
