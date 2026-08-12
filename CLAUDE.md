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

## 5. Current state, in one paragraph

Four of six pipeline stages are trained and evaluated: tooth detection (A100/1024px run,
test mAP@0.5 0.782 — best of two unreconciled runs), the caries cascade (val acc 81%,
macro F1 0.77, with known evaluation gaps), bone-loss binary (macro F1 0.9233 — the
strongest result), and bone-loss severity (macro F1 0.7208 on only 52 validation crops).
CEJ estimation is an exploratory negative result and is not part of the pipeline.
**Stages 5–6 — joining everything into one runnable inference that emits a per-tooth
JSON/PDF report — do not exist yet, and that is the project's actual next milestone.**
There is also an open bug: the Universal→FDI table in `configs/dataset_config.yaml`
mis-maps the whole lower arch from Universal 23 onward (correct: 23→32, 24→31,
25–28→41–44, 29–32→45–48). See the root `README.md` for the correct table.
