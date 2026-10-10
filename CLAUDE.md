# CLAUDE.md — working rules for this repository

This file is read automatically by Claude Code / Cowork sessions working in this repo.
It applies to every session, human-assisted or autonomous.

**What this repo is:** a capstone research project — an OPG (panoramic dental X-ray)
analysis pipeline. YOLOv11l detects teeth, a ResNet18 head numbers them in FDI notation, a
YOLOv11l lesion detector finds caries (the earlier ResNet18 caries gate is retained behind
`--caries-method gate`), and a ResNet18 branch trained on Tufts expert masks covers bone loss.
Start at **`docs/README.md`** — it is the entry point for the documentation layout.
For current model numbers see `docs/results/model_metrics.md`; for the full technical
picture and the honest limitations, `docs/results/PAPER_MATERIAL.md`.

This is a research repo whose output is a paper. **Undocumented results are lost results.**
The rules below exist because the root `README.md` once spent three months claiming
finished models were "in progress".

---

## 1. Every result gets logged — no exceptions

Whenever a session **trains a model, produces a new evaluation number, fixes a significant
bug, or makes an architectural or methodological decision**, before that session ends it
MUST:

1. **Append a dated entry to `docs/results/RESULTS_LOG.md`**, using the
   `## Template for new entries` block at the top of that file. Append at the **bottom**
   (the file is chronological, oldest first). One entry per milestone, not per commit.
   Never edit or reorder an existing entry — if an old number was wrong, add a new entry
   saying so and link back to it.
2. **Update `docs/results/model_metrics.md`** if the result changes any current-best
   number. That file is a scoreboard: current numbers only, one table per model, no
   history. Keep it consistent with the log.
3. **Update the relevant section of `docs/results/PAPER_MATERIAL.md`** if the result is
   paper-relevant — a new metric goes in §7 Results, a new method or design choice in §5/§6,
   a newly discovered weakness in §8 Known Limitations, and tick or add items in
   §9 the "what's not yet written" checklist.

Every number written into these files must be traceable to a saved notebook output cell, a
`models/<NN>_<name>/*summary*.txt`, or a run artifact such as `results.csv`. If it is not,
mark it `[UNVERIFIED]`. Do not soften a limitation to make a result look better.

## 2. Every substantial session leaves a memory file

At the end of any substantial working session, write a new file:

```
docs/session-memory/YYYY-MM-DD-<short-slug>.md
```

Follow the format of `docs/session-memory/2026-08-12-repo-understanding-and-restructure.md`
and the convention described in `docs/session-memory/README.md`. Required sections:

- **Session goal** — one line.
- **What was done** — concrete actions, with paths and commit hashes.
- **Decisions made** — each with the reasoning behind it.
- **Open questions** — what you did not resolve, specific enough to hand off.
- **Next steps** — ordered and actionable.

One file per session; never edit a previous session's file. Session memory holds narrative
and context; numeric results belong in `RESULTS_LOG.md`. A session that produces a result
writes both.

## 3. Never delete raw research artifacts

Notebooks, checkpoints, run directories, raw data, exploratory scripts and old diagrams are
**never** deleted, and never `git rm`'d into oblivion. If something must leave the tracked
repo, **relocate** it to `_repo_archive/`, which sits at the root of this repo:

```
An-Intelligent-Dental-Assisting-System-.../       <- this repo
└── _repo_archive/
    ├── ARCHIVE_MANIFEST.md                       <- tracked, with a few small files
    └── datasets_workspace/, ...                  <- bulk: gitignored, never staged
```

Record every relocation in `_repo_archive/ARCHIVE_MANIFEST.md`: original path, size, why it
moved, and the `mv` command that restores it. Use `mv`, never `rm`.

The archive is inside the working tree, so nothing protects it from `git add` except
`.gitignore`. **When you add a subfolder to it, add that subfolder to the "Archive ignores"
block of `.gitignore` in the same change, and confirm with `git status` that nothing new shows
up.** *(Corrected 10 Oct 2026: this rule and the manifest header used to describe a sibling
folder outside git. Git has tracked `_repo_archive/ARCHIVE_MANIFEST.md` at the repo root since
`0fd5741`, 19 Aug 2026.)*

## 4. House conventions

- **Documentation entry point:** `docs/README.md`. Keep it accurate — if you add a folder
  under `docs/`, add its row to that index.
- **`docs/research/` is owned by a separate workstream.** Do not create, move, or rewrite
  its contents unless the task is explicitly about it.
- **Commit messages** use the existing prefixes: `feat:`, `fix:`, `data:`, `docs:`,
  `refactor:`, `test:`. Small, clearly-scoped commits.
- **Never `git push` without being asked**, and never use `--no-verify` or skip hooks.
- **Stage explicit paths** (`git add <path>`), not a blanket `git add -A`; this repo sits
  next to large untracked data directories.
- **No large binaries in commits.** Model weights above ~50 MB stay on local disk and in
  the archive, and are `.gitignore`d — record where they live in the relevant
  `models/<NN>_<name>/run_summary.txt` instead. *(Exceptions, 3–4 Sep 2026: the `DEF_*`
  checkpoints `models/{09,10,11}` and, once Lever B was adopted, `models/16` — plus `models/14`,
  its single-corpus arm — are committed via `.gitignore` exceptions so a fresh clone runs the
  pipeline without a Drive round-trip. Three of them are over the line: `models/11` at 56 MB,
  `models/14` and `models/16` at 51 MB each. Private repo; `transfer.md` §4 records it and how
  to undo. This does not open the door to committing other weights — `models/06`, the
  `models/{13,15,17}` ablation weights, and anything new stay out.)*
- **No new file paths containing spaces.** `notebooks/Bone Loss/` was renamed to
  `notebooks/bone_loss/` for exactly this reason.
- **Do not "fix" a stale status table by guessing.** Verify against notebook outputs and
  summary files first — that is how the previous README drifted three months out of date.

## 5. Keep `transfer.md` current — it is the cold-start snapshot

`transfer.md` at the repo root answers "where are we, what is done, what is next" for a
session starting with no context. **Before any substantial session ends, update its §1–§4**
if that session finished something, decided something, or changed what should happen next.

It is **rewritten in place**, not appended to — it is a snapshot, not a journal. The journals
are `docs/results/RESULTS_LOG.md` (append-only, never edit an entry) and
`docs/session-memory/` (one file per session, never edit a previous one). Do not duplicate
their content here; `transfer.md` links to them.

A stale snapshot is worse than no snapshot. It has cost this project real time more than once:
a wasted search for files that were never lost, and a month in which it called the manuscript
feature-complete (`docs/session-memory/2026-10-10-state-review-council.md`).

## 6. Current state — pointer only

**Do not maintain project status here.** This section goes stale faster than anything else in
the repo, and has twice described a closed item as open. The authoritative snapshot is
**`transfer.md`** (§1 "Where we are"); the authoritative history is
`docs/results/RESULTS_LOG.md`; the authoritative work list is `transfer.md` §3.
`docs/research/PUBLICATION_TODO.md` and `docs/research/MASTER_PLAN_2026H2.md` are the original
plan and have not been re-synced since before 4 Sep 2026 — read them for intent, not status.

The only durable facts worth repeating here, because they shape almost every task:

- The pipeline is **six stages, and all six now run** — `scripts/run_inference.py` takes an
  image and emits per-tooth JSON + an overlay (R4, paper claim C3); `app.py` + `Dockerfile`
  wrap it for a browser demo. "Runs" does **not** mean "validated to publication standard":
  the honest per-stage numbers, including the ones that collapse out-of-domain, are in
  `transfer.md` §1–§2.
- **Model weights live under `models/<NN>_<name>/`, and which checkpoint is the pipeline
  default changes** — the Stage-2 head became v2.0 on 26 Aug and the Stage-3a caries default
  became the lesion detector (`models/16_lever_b_pooled/`) on 4 Sep, each with its predecessor
  retained and hash-pinned. Read `models/README.md` and the `DEF_*` defaults in
  `run_inference.py` rather than assuming. Every `DEF_*` checkpoint is in git; the superseded
  detector (`models/06`) and the ablation weights (`models/{13,15,17}`) are not —
  `docs/EXTERNAL_DRIVE.md` and each `run_summary.txt` say where they live.
- **Ningxia is external test data.** Never train on it, never tune on it
  (`MASTER_PLAN_2026H2.md` §4.1).
- **Two documents constrain where this work can be published, and both are in `transfer.md`
  §5.** The grade table: a journal, or a conference in its 10th edition or later, for an S. The
  department guidelines of 10 Oct 2026: prefer a Scopus/WoS-indexed conference held in India; a
  conference outside India needs University approval *before* submitting or paying anything;
  and the indexing of the specific edition must be verified first. Check both before proposing
  a venue.
- **Several files here use CRLF line endings and the rest use LF** (`transfer.md` §7 lists
  which). Edit in place and never run a blanket line-ending normaliser.
- The Universal→FDI lower-arch bug is **fixed** (`f8b31f8`), regression-tested in
  `tests/test_fdi_converter.py`. It was described as open in five places long after it closed
  — rule 4's failure mode running in reverse. Verify before you write, in both directions.

---

## 7. Response style

Output zero conversational filler. Maximize information density. Prioritize telegraphic
phrasing, lists, and tables over prose. Retain structural grammar strictly to preserve logical
reasoning, but ruthlessly strip all pleasantries, transitional phrases, and redundant context.

This governs chat responses only — **not** the prose written into `RESULTS_LOG.md`,
`transfer.md`, session-memory files, paper drafts, or code comments, which keep their own
conventions.
