# 2026-08-12 — Repo understanding pass and full restructure

**Session goal:** Understand what this repository actually contains versus what it claims
to contain, clear out the accumulated junk without deleting anything, and build a
documentation system that makes the project legible to a stranger and usable as the source
for the paper.

No models were trained and no metric changed in this session.

---

## Part 1 — What the audit found

### The documentation was three months out of date

The root `README.md` described tooth detection as "🟡 In Progress", bone loss model
training as "⬜ Planned" and bone loss evaluation as "⬜ Planned". In reality all of these
finished between April 6 and April 23. Its Project Structure section listed files that do
not exist (`src/dataset_builder.py`, `src/model.py`, `src/train.py`, `notebooks/01–04`) and
omitted everything that does. Anyone opening this repo would have formed a materially wrong
picture of the project's state.

### Ground truth on each component

| Component | Real status |
|-----------|-------------|
| Tooth detection (YOLOv11l) | **Done.** Two competing runs, never reconciled: A100/1024px/150ep (val mAP@0.5 0.834, test 0.782) and H200/768px/50ep (val 0.678). No canonical model frozen. |
| Caries cascade (ResNet18, DENTEX) | **Done**, with documented methodology gaps. Val acc 81%, macro F1 0.77. |
| Bone loss binary (ResNet18 + Focal Loss, Tufts) | **Done and strong.** Macro F1 0.9233, diseased F1 0.8522, sensitivity 83.05%, specificity 99.53%. |
| Bone loss severity (3-class) | **Done but borderline.** Macro F1 0.7208 against a 0.72 target, on 52 val crops with only 6 "mild". |
| CEJ estimation | **Exploratory negative result.** 100% *completion*, but only 15.1% agreement with the primary severity label. Not in the pipeline. |
| Pipeline integration (Stages 5–6) | **Not built.** This is the actual next milestone. |

### 2.6 GB of untracked junk in the working tree

`git status --short` showed eight untracked entries. Four were large and had to go:

- `Implementation/` (175 MB) — a **stale nested clone of this same repo**, with its own
  `.git` pointing at the same GitHub origin, frozen at commit `f84ca62`, four commits
  behind `main`. Its `src/` was verified byte-identical to the outer repo's.
- `DataSets/` (2.2 GB) — raw-data workspace containing a **checked-in Python virtualenv**
  (`opg_env/`), a 279 MB `dataset.tar.gz` duplicating the already-extracted `dataset/`,
  raw Tufts imagery, scratch notebooks — and three genuinely useful scripts.
- `A100_150/` (203 MB) — the Ultralytics run directory for the best detector, plus a 97 MB
  `runs_backup.tar.gz` duplicating what was beside it, at a doubly-nested
  `runs/detect/runs/detect/` path caused by a bad `project=` argument.
- `Archi/` (200 KB) — diagrams, one of which was byte-identical to a diagram already tracked
  in `docs/`.

### Other findings worth recording

- The two `YOLO_trained.ipynb` files were **ambiguously named** (one at the repo root, one
  in `A100_150/`). They were disambiguated by reading the saved output cells — GPU banner,
  `imgsz`, epoch count, final metric line — not by trusting the folder name. Root =
  H200/768/50ep; `A100_150/` = A100/1024/150ep.
- The `universal_to_fdi` table in `configs/dataset_config.yaml` is **wrong for the entire
  lower arch from Universal 23 onward**. Correct: 23→32, 24→31, 25–28→41–44, 29–32→45–48.
  The config has 23→43, 24→44, 25–28→45–48, 29–32→31,32,33,34 — duplicating FDI 33/34,
  which are already used by Universal 22/21. Every lower-jaw finding would be reported
  against the wrong tooth. Left unfixed deliberately: it is a pipeline-behaviour change
  that should be reviewed and unit-tested, not slipped into a cleanup commit.
- Model checkpoints under `models/03_*` and `models/04_*` are **committed to git** (44 MB
  each) despite `.gitignore` containing `models/*.pth` — that pattern only matches the top
  level, not `models/<subdir>/*.pth`.

---

## Part 2 — What this session changed

### Relocated (never deleted) to `_repo_archive/`, a sibling of the repo

Full record with sizes, reasons and one-line restore commands:
`../_repo_archive/ARCHIVE_MANIFEST.md`.

| From | To |
|------|-----|
| `Implementation/` | `_repo_archive/implementation_stale_clone/` |
| `DataSets/` | `_repo_archive/datasets_workspace/` |
| `A100_150/` | `_repo_archive/yolo_a100_run_workspace/` |
| `Archi/` | `_repo_archive/archi_duplicate_diagrams/` |
| `docs/flowcharts/` (emptied dir) | `_repo_archive/empty_docs_flowcharts_dir/` |

The archive sits **outside** the git working tree by design, so it can never be
accidentally staged. Nothing was deleted; every item is recoverable with a single `mv`.

### Rescued into the repo before archiving

- `DataSets/{convert_tufts_to_yolo,train_yolo,evaluate_yolo}.py` → **`scripts/yolo/`**
  (+ a README explaining each and flagging that their hard-coded paths and their
  aspirational ≥0.90 mAP targets are stale). Kept separate from the existing
  `scripts/*.py`, which serve the crop/classifier half of the pipeline.
- A100 run: `best.pt`, `last.pt`, `args.yaml`, `results.csv` →
  **`models/06_yolo_detection_a100_run/`** with a written `run_summary.txt`; all PNG curves
  and confusion matrices plus three qualitative prediction JPGs →
  **`docs/results/figures/yolo_detection_a100/`** (`val_*` / `test_*` prefixes).
- Both YOLO notebooks → **`notebooks/yolo_detection/`** as `a100_1024px_150ep.ipynb` and
  `h200_768px_50ep.ipynb`, with a README recording how they were told apart.
- `Archi/corrected_opg_pipeline_architecture.svg` + `.drawio` → **`docs/architecture/`**.

### Renamed / moved inside the repo

| Before | After |
|--------|-------|
| `notebooks/Bone Loss/` | `notebooks/bone_loss/` (`git mv`; the space was a path hazard) |
| `pes_capstone_report/` | `docs/reports/pes_capstone_report/` (`git mv`, history preserved) |
| `docs/flowcharts/pipeline_flowchart.svg` | `docs/architecture/pipeline_flowchart.svg` (`git mv`) |
| `Survey_paper.pdf`, `Dental X-Ray Capstone Literature Review.xlsx` | `docs/reports/literature/` |
| `DENTAL_AI_ANALYSIS_REPORT.md` | `docs/reports/legacy/` (kept — it is a good source doc, just not the entry point) |
| `YOLO_trained.ipynb` | `notebooks/yolo_detection/h200_768px_50ep.ipynb` |

### New documentation

- `docs/README.md` — index of the whole docs system.
- `docs/results/PAPER_MATERIAL.md` — the master paper document: problem statement, related
  context, dataset descriptions with exact counts, architecture, per-stage methods, the five
  key engineering decisions with their numbers, all result tables, a blunt limitations
  section, and a "what's not yet written" checklist.
- `docs/results/RESULTS_LOG.md` — append-only journal, seeded with ten reconstructed
  milestone entries from 2026-01-31 to today, with a copy-paste template at the top.
- `docs/results/model_metrics.md` — one-page scoreboard.
- `docs/session-memory/README.md` + this file — the session-memory convention.
- `docs/architecture/README.md`, `notebooks/yolo_detection/README.md`,
  `scripts/yolo/README.md`, `models/06_yolo_detection_a100_run/run_summary.txt`.
- `CLAUDE.md` at the repo root — the standing instruction that keeps all of the above
  current in future sessions.
- Root `README.md` rewritten: same structure, badges and tone, corrected status tables,
  real project structure, pointers to `docs/`.

---

## Decisions made

1. **Archive as a sibling, not a subfolder.** `_repo_archive/` lives one level up, inside
   `Deepak impleentation/`. Inside the repo it would eventually be committed by someone
   running `git add -A`.
2. **Nothing is ever deleted.** Relocation only, with a manifest recording original path,
   size, reason and restore command. Research artifacts are cheap to store and impossible
   to reconstruct.
3. **The three YOLO scripts were copied, not moved.** `scripts/yolo/` gets working copies;
   the originals stay in the archived workspace so the archive remains a faithful snapshot.
4. **`models/06_.../*.pt` is git-ignored.** The two checkpoints are 51 MB each; GitHub warns
   above 50 MB and the pair would add ~100 MB to history permanently. They live on local
   disk and in the archive, and `run_summary.txt` says exactly where. This is a deliberate
   departure from the existing (arguably wrong) practice of committing the 44 MB `.pth`
   files — those are left alone rather than rewritten out of history.
5. **The duplicate flowchart was not kept three times.** `Archi/dental_opg_pipeline_flowchart.svg`
   was md5-identical to the tracked `docs/flowcharts/pipeline_flowchart.svg`; the duplicate
   and its raster export went to the archive, and `docs/architecture/README.md` records
   which file is authoritative.
6. **Both YOLO runs are kept and documented rather than one being deleted.** Freezing a
   canonical detector is a modelling decision for the project owner, not a cleanup decision.
7. **Limitations are stated bluntly in `PAPER_MATERIAL.md`.** The caries evaluation gaps,
   the 6-sample severity class, the 15.1% CEJ agreement and the absent integration are all
   written down explicitly. A reviewer will find them anyway.
8. **`docs/research/` was left completely untouched** — it is owned by a parallel
   workstream. It is not staged or committed by this session.

---

## Open questions

1. **Which detector is canonical?** A100/1024 is clearly better, but it has not been
   formally frozen (weight hash + config recorded, H200 retired in writing).
2. **The FDI quadrant-4 mapping bug** — is `src/utils/fdi_converter.py` derived from the
   broken YAML table, or does it have its own (possibly correct) mapping? Not verified.
3. **Should the committed 44 MB `.pth` files be rewritten out of git history?** Doing so
   rewrites shared history; left alone for the owner to decide.
4. **Where are the Stage 3/4 training curves and confusion matrices?** The summaries say
   they were saved to Google Drive; they are not in this repo. `docs/results/figures/`
   currently only has detector plots.
5. **Are the DENTEX class counts (2,767 / 762 / 133) correct?** They come from the legacy
   analysis document; the notebook cell that would confirm them has no saved output.
6. **Were the severity thresholds (0.05 / 0.15) tuned or chosen by eye?** Undocumented.

## Next steps

1. **Build Stages 5–6** — one runnable inference joining detector + caries cascade +
   bone-loss models on the FDI key, emitting a filtered per-tooth JSON and a PDF with
   Grad-CAM. This is the milestone, not more isolated model tuning.
2. Fix the lower-arch Universal→FDI mapping in `configs/dataset_config.yaml`
   (23→32, 24→31, 25–28→41–44, 29–32→45–48) and verify `src/utils/fdi_converter.py`
   against it. Add a unit test — `tests/test_fdi_converter.py` already exists.
3. Freeze the canonical detector and record it in `docs/results/model_metrics.md`.
4. Close the caries evaluation gaps (`PAPER_MATERIAL.md` §9 blocking list): save the Phase 1
   gate report, actually apply the augmentation pipeline, carve a held-out test split.
5. Measure error propagation: run the classifiers on real detector crops rather than
   ground-truth boxes, and quantify what the ±15% jitter training actually bought.
