# `docs/` — documentation index

You are looking at the documentation for an OPG (panoramic dental X-ray) analysis pipeline:
detect every tooth, number it in FDI notation, and classify caries and periodontal bone
loss per tooth. If you have five minutes and want the real state of the project, read these
three files in order:

1. **`results/model_metrics.md`** — every current best number on one page.
2. **`results/PAPER_MATERIAL.md`** — the full technical story, including an honest
   limitations section. This is the master document the paper gets written from.
3. **`session-memory/`** (newest file) — what the last person to work here actually did.

---

## Layout

| Path | What lives there |
|------|------------------|
| `README.md` | This index. |
| `architecture/` | System diagrams. `corrected_opg_pipeline_architecture.svg` is authoritative; `.drawio` is the editable source. See `architecture/README.md`. |
| `results/PAPER_MATERIAL.md` | **The master paper-writing document.** Problem statement, datasets, architecture, per-stage methods, the five key engineering decisions, all result tables, known limitations, and a checklist of what still has to be written. |
| `results/RESULTS_LOG.md` | Append-only chronological journal — one entry per milestone, newest at the bottom. Every new training run or evaluation gets an entry. Template is at the top of the file. |
| `results/model_metrics.md` | Single-glance scoreboard: one table per model, current best numbers only. |
| `results/figures/` | Result plots. `yolo_detection_a100/` holds the detector's curves, confusion matrices and qualitative predictions (`val_*` from the training run, `test_*` from the held-out test evaluation). |
| `reports/project_report.pdf` | Full project report (PDF). |
| `reports/data_exploration_v2.pdf` | Tufts data-exploration report (PDF). |
| `reports/pes_capstone_report/` | LaTeX source of the PES capstone report (`main.tex`, `chapters/`, `figures/`). Moved here with `git mv`, history intact. |
| `reports/literature/` | `Survey_paper.pdf` and the literature-review spreadsheet — source material for the Related Work section. |
| `reports/legacy/DENTAL_AI_ANALYSIS_REPORT.md` | The original all-in-one analysis document (written as placement/interview prep). Technically accurate and still a useful source, but **no longer the entry point** — its content has been reorganised into `results/PAPER_MATERIAL.md`. |
| `exploration/README.md` | Dataset quirks and the five critical bugs caught during exploration, with root cause and fix for each. Still the best single explanation of *why* the data handling looks the way it does. |
| `session-memory/` | One dated file per substantial working session: goal, what was done, decisions, open questions, next steps. See `session-memory/README.md`. |
| `research/` | Maintained separately by a parallel workstream — see that folder's own README. Not covered by this index. |

---

## Where the numbers come from

Nothing in `results/` is invented. Each metric traces to one of:

- a saved output cell in a notebook under `notebooks/`,
- a `*summary*.txt` under `models/<NN>_<name>/`,
- or `models/06_yolo_detection_a100_run/{results.csv,train_args.yaml}`.

If you add a number without one of those behind it, mark it `[UNVERIFIED]`.

## Keeping this current

The repo-root `CLAUDE.md` states the rules that keep these files from going stale:
every new result appends to `results/RESULTS_LOG.md`, updates `results/model_metrics.md`
if it changes a best number, and updates `results/PAPER_MATERIAL.md` if it is
paper-relevant; every substantial session leaves a `session-memory/` file. The root
`README.md` used to describe a project three months out of date — that is exactly the
failure mode these conventions exist to prevent.
