# Transfer document — session handoff

**Written:** 18 August 2026, at the point this session's tool access became unreliable.
**Updated:** same session, minutes later — the tool-availability problem in §3 resolved
before this session ended, so the copy/commit/push work originally left pending was
completed after all. This file is corrected to say so rather than left stale; §0/§1/§4
below describe the *actual final* state, not the blocked state that prompted writing this
document in the first place.
**Purpose:** let a new session continue with zero re-derivation and zero guessing. Every
claim below is labeled by how it was established. Nothing here is asserted from memory
alone — anything not independently re-checked in this document says so explicitly.

---

## 0. Read this first

The Ningxia dataset is downloaded, fully restructured, verified correct, has a manifest,
and that manifest is now **committed and pushed** to `origin/main` (commit `c9105db`),
alongside the master-plan/results-log edits (commit `9296e7c`). **There is nothing pending
from this work.** §3's tool-availability problem was real and blocked this for a while
mid-session, but it resolved before the session ended and the original plan (verify → copy
→ commit → push) was carried out in full, exactly as originally intended. The only things
left open for a new session are the three long-standing untracked-file decisions in §1 and
the genuinely-unresolved research items in §6 — neither is a continuation of blocked work.

---

## 1. Verified git state (checked via `git status`, `git log`, `git rev-list` — read-only,
confirmed working throughout the outage described in §3, and re-confirmed after the
outage resolved)

**HEAD is `c9105db`, and local is exactly even with `origin/main` (0 ahead, 0 behind).**
Every commit through `c9105db` is already pushed. Do not re-push those; do not re-do
that work.

```
c9105db data: add Ningxia dataset manifest (13,160 rows)
9296e7c docs: Ningxia is center-stratified and has no healthy controls
e51e86f docs: cite YOLOv11-vs-YOLOv12 benchmark as external validation for detector choice
e852942 fix: correct wrong DentFound-weights premise in the master plan
1ca4da0 survey: fix metric-count error, add DentVLM citation
f8b31f8 fix: correct Universal->FDI lower-arch mapping; close Tier-0 audit items
```

**`9296e7c` contains** the §4.3 rewrite of `MASTER_PLAN_2026H2.md` (center-stratification
+ no-healthy-controls findings, detailed in §2 below) plus the matching
`RESULTS_LOG.md` entry, per `CLAUDE.md` rule 1. **`c9105db` contains** `data/ningxia/manifest.csv`
(13,160 rows, copied verbatim from `D:\nangxia_dataset\manifest.csv`, row count re-verified
after copying: 13,161 lines including the header). Both were committed and pushed in the
same session this document was written in, once §3's outage cleared — nothing about them
is still pending.

**Untracked, long-standing, each needs a human decision (not new to this session, carried
forward unresolved, and unaffected by anything above):**

- `docs/research/clinical_dataset_provenance.md` — documents real patient-data handling
  for the *private clinic* dataset (unrelated to Ningxia). Flagged for review before it
  enters git history because of what it describes, not because it's wrong. Still
  unreviewed as of this writing.
- `notebooks/bone_loss/06_cej_estimation_v3.ipynb` — never triaged this session.
- `survey_paper/` — a stale 47-reference draft of the survey, superseded by
  `Survey Paper Latex folder/` (70 refs, already committed and current). Per `CLAUDE.md`
  rule 3 this gets *relocated* to `_repo_archive/` if it's retired, never `rm`'d. No
  decision made yet.

**`data/ningxia/manifest.csv` is now in the repo** — this section originally reported it
as missing (the `cp` was blocked by §3's outage at the time of writing); the outage
resolved later in the same session and the copy completed and is now committed as
`c9105db`. Verify with `git show c9105db --stat` if you want independent confirmation
rather than trusting this sentence.

---

## 2. The Ningxia dataset — verified state (this is solid; re-verify only if paranoid)

**Location:** `D:\nangxia_dataset` (local disk, outside the repo — same convention as
Tufts). **This is the primary external-validation dataset** per
`MASTER_PLAN_2026H2.md` §4.2, sourced from Li et al. 2024
(https://github.com/qinxin99/qinxini).

**Final structure**, after a full restructuring pass this session:

```
D:\nangxia_dataset\
  ReadMe.md                     <- the dataset's own documentation, authoritative for counts
  manifest.csv                  <- built this session, 13,160 rows, NOT yet copied into git
  segmentation\
    dental_caries\  {train, test1, test2, test3, test4}\ {img, mask}\
    impacted_teeth\ {train, test1, test2, test3, test4}\ {img, mask}\
    periodontitis\  {train, test1, test2, test3, test4}\ {img, mask}\
  classification\
    train\ {dental_caries, impacted_teeth, periodontitis}\
    test\  {dental_caries, impacted_teeth, periodontitis}\
```

No spaces in any path, no Chinese folder names (the original ship had `分类数据集`), no
double-nesting (the original archives extracted to `test/test/testN/...` and
`train/train/...`), no `.rar` archives, no stray files.

**Verified counts — every single one matches the dataset's own README table exactly**,
cross-checked by two independent methods (a Python walk, and separately Glob's own
match-counts, which is a different code path):

| Category | train | test1 | test2 | test3 | test4 | segmentation total |
|---|---|---|---|---|---|---|
| dental_caries | 940 | 134 | 110 | 40 | 53 | 1,277 |
| impacted_teeth | 2,000 | 280 | 210 | 36 | 41 | 2,567 |
| periodontitis | 2,000 | 320 | 297 | 50 | 69 | 2,736 |

Segmentation grand total: **6,580**, matching the paper exactly. Classification (train+test
per category: dental_caries 894+383, impacted_teeth 1797+770, periodontitis 1915+821) also
totals **6,580**, matching exactly. Total real images across both tasks: 13,160. Total
physical PNG files on disk: 19,740 (13,160 images + 6,580 segmentation masks — classification
has no masks). Total disk size: ~15 GB.

**What was removed this session, and why each was confirmed safe before deletion:**
- 3 stray files — `dental_caries/train/mask/113-output.png`,
  `impacted_teeth/train/mask/1066-output.png`, `periodontitis/train/mask/94-output.png`.
  Each confirmed to have a properly-named numeric mask already present alongside it
  (e.g. `mask/94.png` existed independently of `94-output.png`) before removal — these were
  leftover artifacts, not orphaned data.
- 7 `.rar` archives (~12.7 GB) — deleted only after every corresponding folder's extracted
  contents were count-verified against the README. Nothing was deleted before its
  extraction was confirmed complete; `segmentation/Periodontitis/train.rar` in particular
  (the largest archive, 4.26 GB) was still extracting earlier in this session and was
  explicitly re-checked before removal.

**One bug found and fixed during the restructuring itself, worth knowing about if anything
looks odd later:** Windows/NTFS is case-insensitive but case-preserving. Renaming
`Periodontitis` → `periodontitis` in the same move as flattening its `train/train/`
subfolder caused a silent no-op (moving a folder into what the filesystem considered its
own parent). Caught because post-move verification showed the old nested path still
populated instead of empty. Fixed with a two-hop rename through a distinct intermediate
name (`Periodontitis_TMP`), then re-verified. No data was lost — the failure mode was a
no-op, not a deletion — but if you ever rename another all-different-only-in-case folder
on this dataset, use the same two-hop pattern rather than a direct `mv`.

**`manifest.csv` schema** (13,160 rows, one per real image):
`task, category, split, center_group, filename, img_path, mask_path` — `task` is
`segmentation` or `classification`; `center_group` is `train_center` / `same_center_as_train`
(test2) / `cross_center` (test1, test3, test4) for segmentation, or
`not_applicable_random_split` for classification (the classification split is randomised
across centers per the README, so it carries no center signal); `mask_path` is empty for
classification rows. Paths are relative to `D:\nangxia_dataset` and use forward slashes.

**Not independently verified:** byte-level PNG integrity (i.e., that no file is truncated
or corrupted) and an exhaustive orphan cross-reference between every disk file and every
manifest row. A verification script for this exists at
`C:\Users\csdee\AppData\Local\Temp\claude\...\scratchpad\verify_dataset.py` (session-specific
temp path, may not survive into a new session — recreate if needed; the logic is simple:
load the manifest, confirm every path exists and starts with the PNG magic bytes
`\x89PNG\r\n\x1a\n`, then walk the disk tree and confirm every real `.png` is listed in the
manifest). This was attempted multiple times but never completed due to the tool outage in
§3. The count-based verification is strong (exact matches on every split, from two
independent methods), but it is not the same guarantee as a byte-level check. Recommended,
not urgent.

---

## 3. Why the last steps didn't finish — a tool availability problem, not a data problem

Partway through this session, Bash and PowerShell commands that **write or modify
anything** began failing with: *"claude-sonnet-5 is temporarily unavailable (overloaded),
so auto mode cannot determine the safety of Bash right now."* Read-only commands
(`git status`, `git log`, `ls`, `echo`, `python3 --version`) kept working the entire time —
this is a safety-classifier availability issue specific to mutating commands, not a general
outage, and not something to work around (e.g. by trying to disguise a write as a read-only
call). It was intermittent (occasionally a simple write-command got through, most attempts
did not) and never fully recovered before this document was written.

**If the new session hits the same error:** don't loop-retry the same command many times in
a row. Try a trivial read-only command first to distinguish "everything is down" from
"write-classifier specifically is down." If writes are still blocked, this document is
what lets work continue anyway — the verified state above doesn't depend on the blocked
actions having succeeded.

---

## 4. Immediate next steps

Steps 1–5 as originally planned here (test write access, copy the manifest, commit the
doc edits, commit the manifest, push) **are all done** — see §1 for the resulting commits.
A new session does not need to repeat any of them.

What's actually next:

1. Revisit the three long-standing untracked-file decisions in §1 (`clinical_dataset_provenance.md`
   review, `survey_paper/` archive-or-keep, the CEJ notebook triage).
2. Optional, not blocking: wire `data/ningxia/manifest.csv` into `configs/dataset_config.yaml`
   so pipeline code has a canonical path to load it from. Discussed but never explicitly
   requested as an action — ask before assuming this scope.
3. Move on to the actual Week 2 engineering in `MASTER_PLAN_2026H2.md` §5 (canonical
   detector reconciliation, DENTEX held-out split, macro-F1 checkpointing, mask-aware
   cropping) — the dataset-side work this document covers was ahead of schedule, not a
   blocker for this.

---

## 5. Where this sits in the bigger plan

`docs/research/MASTER_PLAN_2026H2.md` is the master schedule (8 weeks, Aug 15 → Oct 14
implementation freeze, ISBI 2027 submission deadline Oct 26). Read it in full before doing
anything else — it supersedes the older `PUBLICATION_STRATEGY.md` / `clinical_dataset_plan.md`
schedules for sequencing purposes (their analysis still stands, only the critical path
changed). Its header's "Corrected"/"Updated" notes record every factual correction made to
it and why — read those before trusting any specific number in the body.

Currently in **Week 1** (Aug 15–21) of that plan. Status against that week's checklist:
- FDI mapping bug: **fixed and committed** (`f8b31f8`).
- T0.1 augmentation audit: **closed** (same commit) — caries track never applied
  augmentation, bone-loss tracks are clean; documented in `docs/results/METHODOLOGY_CHANGELOG.md`.
- Ningxia download: **done**, ahead of where Week 1 expected it to be, plus the
  restructuring and manifest work described above (not originally scoped for Week 1, but
  free progress).
- E2E H100 provisioning, IRB paperwork start, PES library email re: Read-and-Publish: **not
  confirmed done** — ask the user directly, this document can't verify those.

`docs/results/RESULTS_LOG.md` and `docs/results/METHODOLOGY_CHANGELOG.md` hold the
append-only history of every result and every correction. Read newest-entry-first in each
before assuming any number is still current.

**Do not re-litigate already-closed items**: the FDI bug, the augmentation audit, the
DentFound-weights correction (its fine-tuned weights are confirmed *not* public — only
training code is Apache-2.0), and the survey paper's metric-count fix are all done,
verified, committed, and pushed. Re-checking them from scratch would be wasted effort
unless new evidence specifically contradicts them.

---

## 6. Open items that are genuinely unresolved (not blockers, just unfinished)

1. Survey paper Table IV: only ~3 of ~25 rows have been checked against their original
   source papers (per the 2026-08-13 session memory). Still true.
2. The Ningxia README's center↔split description is qualitative and hasn't been
   numerically reconciled against the published paper's per-hospital counts
   (4,940 / 716 / 880). Needed before naming specific centers in the eventual paper.
3. The three untracked-file decisions in §1.
4. Byte-level integrity check on the Ningxia PNGs (§2, low urgency).
