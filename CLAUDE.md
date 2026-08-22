# CLAUDE.md — working rules for this repository

This file is read automatically by Claude Code / Cowork sessions working in this repo.
It applies to every session, human-assisted or autonomous.

**What this repo is:** a capstone research project — an OPG (panoramic dental X-ray)
analysis pipeline. YOLOv11l detects teeth, they are numbered in FDI notation, and two
ResNet18 branches classify caries (DENTEX) and periodontal bone loss (Tufts) per tooth.
Start at **`docs/README.md`** — it is the entry point for the documentation layout.
For current model numbers see `docs/results/model_metrics.md`; for the full technical
picture and the honest limitations, `docs/results/PAPER_MATERIAL.md`.

This is a research repo whose output is a paper. **Undocumented results are lost results.**
The three rules below exist because the root `README.md` once spent three months claiming
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
repo, **relocate** it to `_repo_archive/`, which is a sibling of this repo:

```
Capstone/Deepak impleentation/
├── An-Intelligent-Dental-Assisting-System-.../   <- this repo
└── _repo_archive/                                <- outside git, never staged
    └── ARCHIVE_MANIFEST.md
```

Record every relocation in `_repo_archive/ARCHIVE_MANIFEST.md`: original path, size, why it
moved, and the `mv` command that restores it. Use `mv`, never `rm`. The archive is
deliberately outside the working tree so it can never be picked up by `git add`.

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
  `models/<NN>_<name>/run_summary.txt` instead.
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

A stale snapshot is worse than no snapshot. It has already cost this project one wasted
search — see `transfer.md` §6.

## 6. Current state — pointer only

**Do not maintain project status here.** This section goes stale faster than anything else in
the repo, and has twice described a closed item as open. The authoritative snapshot is
**`transfer.md`** (§1 "Where we are, in five lines"); the authoritative history is
`docs/results/RESULTS_LOG.md`; the authoritative work list is
`docs/research/PUBLICATION_TODO.md` (status block at the top), sequenced by
`docs/research/MASTER_PLAN_2026H2.md`, which supersedes the other planning docs for ordering.

The only durable facts worth repeating here, because they shape almost every task:

- The pipeline is **six stages; Stages 5–6 (integration → per-tooth JSON/PDF report) do not
  exist.** That is the project's largest gap and its central paper claim (C3).
- **Four models are trained** (detection, caries cascade ×2, bone-loss binary + severity) and
  all their weights are on local disk. "Trained" does **not** mean validated to publication
  standard — the Tier-0 repairs are prepared but unrun.
- **Ningxia is external test data.** Never train on it, never tune on it
  (`MASTER_PLAN_2026H2.md` §4.1).
- The Universal→FDI lower-arch bug is **fixed** (`f8b31f8`), regression-tested in
  `tests/test_fdi_converter.py`. It was described as open in five places long after it closed
  — rule 4's failure mode running in reverse. Verify before you write, in both directions.
