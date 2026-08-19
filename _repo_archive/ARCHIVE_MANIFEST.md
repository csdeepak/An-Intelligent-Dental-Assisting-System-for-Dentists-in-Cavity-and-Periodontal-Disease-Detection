# Repo Archive Manifest

**Created:** 2026-08-12
**Archive location:** `Capstone/Deepak impleentation/_repo_archive/`
**Source repo:** `Capstone/Deepak impleentation/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection/`

This archive is a **sibling** of the git repository, deliberately placed one level up so
it can never be picked up by `git status`, `git add`, or any future commit.

> **NOTHING IN THIS ARCHIVE WAS DELETED.**
> Every item listed below was *relocated* with `mv` from the repository working tree into
> this folder. All bytes are still on disk and every item is fully recoverable by moving
> it back to its original path. No `rm`, no `rmdir`, no `git rm` was used at any point.

---

## Summary

| # | Original path (relative to repo root) | Size | Archived to | Reason |
|---|---------------------------------------|------|-------------|--------|
| 1 | `Implementation/` | 175 MB | `implementation_stale_clone/` | Stale nested clone of this same repo |
| 2 | `DataSets/` | 2.2 GB | `datasets_workspace/` | Raw-data workspace: venv, duplicate tarball, raw data, scratch notebooks |
| 3 | `A100_150/` (remainder) | ~200 MB | `yolo_a100_run_workspace/` | YOLO run workspace; key artifacts extracted into the repo first |
| 4 | `Archi/` (whole folder) | 200 KB | `archi_duplicate_diagrams/` | Diagrams; the two current ones were copied into `docs/architecture/` first, the rest are duplicates |
| 5 | `docs/flowcharts/` (emptied dir) | 0 B | `empty_docs_flowcharts_dir/` | Directory left empty after `git mv` of its only file into `docs/architecture/` |

Total relocated: **~2.6 GB**, none of it git-tracked before the move (all four were
untracked, i.e. they appeared under `??` in `git status --short`).

---

## 1. `Implementation/` → `implementation_stale_clone/`

- **Original path:** `<repo>/Implementation/`
- **Size:** 175 MB
- **Git status before move:** untracked (`?? Implementation/`)
- **What it was:** A complete second clone of this very repository, including its own
  `.git` directory pointing at the same GitHub origin
  (`csdeepak/An-Intelligent-Dental-Assisting-System-...`). It was frozen at commit
  `f84ca62` ("Fix bone loss training notebook execution"), i.e. **4 commits behind**
  `main` (`535f2af`).
- **Why moved:** Pure dead weight and an active hazard — two working copies of the same
  project inside each other invites editing the wrong file. Its `src/` was verified
  byte-identical to the outer repo's `src/`, so nothing unique was lost. No merge or
  reconciliation was attempted or needed.
- **Recovery:** `mv "_repo_archive/implementation_stale_clone" "<repo>/Implementation"`

## 2. `DataSets/` → `datasets_workspace/`

- **Original path:** `<repo>/DataSets/`
- **Size:** 2.2 GB (the single largest item in the tree)
- **Git status before move:** untracked (`?? DataSets/`)
- **What it was:** The raw Tufts data + exploration workspace, containing:
  - `opg_env/` — a checked-in **Python virtualenv** (never belongs inside a project folder)
  - `dataset.tar.gz` (279 MB) — a tarball duplicating the already-extracted `dataset/` dir
  - `Radiographs/`, `Radiographs_rotated/`, `Segmentation/`, `Student/`, `Expert/`, `ZIP/`,
    `Verification Images/`, `outputs/` — raw Tufts source data and intermediates
  - `week1_tufts_eda_v2.ipynb` (16 MB), `x.ipynb` (6.5 MB), `y.ipynb` — scratch notebooks
  - `convert_tufts_to_yolo.py`, `train_yolo.py`, `evaluate_yolo.py` — **real reusable code**
  - `convert_tufts_to_yolo.py.bak`, `ground_truth_654.png`, `.vscode/`
- **Preserved before the move:** the three real scripts were **copied** (not moved) into the
  repo at `scripts/yolo/` with a `scripts/yolo/README.md` describing each. The originals
  remain here untouched.
- **Why moved:** Raw datasets, virtualenvs and 279 MB tarballs must not live inside a
  git working tree. Everything of lasting value was extracted first.
- **Recovery:** `mv "_repo_archive/datasets_workspace" "<repo>/DataSets"`

## 3. `A100_150/` (remainder) → `yolo_a100_run_workspace/`

- **Original path:** `<repo>/A100_150/`
- **Size:** 203 MB total; ~200 MB relocated after extraction
- **Git status before move:** untracked (`?? A100_150/`)
- **What it was:** The Ultralytics run directory for the A100 / imgsz=1024 / 150-epoch
  YOLOv11l tooth-detection run (the current best detector), containing
  `runs/detect/runs/detect/tufts_clean_v1/` (weights + curves + `results.csv` + `args.yaml`),
  `runs/detect/tufts_clean_v1_test_eval/` (held-out test plots), a redundant
  `runs_backup.tar.gz` (97 MB), and `YOLO_trained.ipynb` (460 KB).
- **Preserved before the move (copied into the repo):**
  - `runs/.../weights/best.pt`, `last.pt` → `models/06_yolo_detection_a100_run/`
  - `runs/.../args.yaml` → `models/06_yolo_detection_a100_run/train_args.yaml`
  - `runs/.../results.csv` → `models/06_yolo_detection_a100_run/results.csv`
  - all `*.png` curves/matrices from both run dirs → `docs/results/figures/yolo_detection_a100/`
    (prefixed `val_` and `test_`), plus three qualitative `val_batch*` prediction JPGs
  - `YOLO_trained.ipynb` → `notebooks/yolo_detection/a100_1024px_150ep.ipynb`
- **Why moved:** `runs/` is `.gitignore`d by design; the 97 MB `runs_backup.tar.gz` is a
  duplicate of `runs/`; the doubly-nested `runs/detect/runs/detect/` path was an artifact
  of a bad `project=` argument. All information needed for the paper is now in the repo.
- **Recovery:** `mv "_repo_archive/yolo_a100_run_workspace" "<repo>/A100_150"`

## 4. `Archi/` → `archi_duplicate_diagrams/`

- **Original path:** `<repo>/Archi/`
- **Size:** 200 KB (the whole folder was moved, after copying the two current files out)
- **Git status before move:** untracked (`?? Archi/`)
- **What is in here:**
  - `dental_opg_pipeline_flowchart.svg` (43 KB) — **verified byte-identical**
    (md5 `97fe9f90207cb086b822eaaf4eb14b8c`) to the already-tracked
    `docs/flowcharts/pipeline_flowchart.svg`
  - `dental_opg_pipeline_flowchart.jpg` (99 KB) — raster export of that same SVG
  - `.DS_Store`
  - plus the originals of the two files copied into the repo below (the archive is kept as
    a faithful snapshot of the folder, so those two files exist in both places)
- **Preserved before the move (copied into the repo):**
  - `corrected_opg_pipeline_architecture.svg` (37 KB, the more complete/current diagram)
    → `docs/architecture/`
  - `dental_opg_pipeline_flowchart.drawio` (11 KB, the editable source) → `docs/architecture/`
- **Why moved:** avoid keeping three copies (svg + jpg + tracked svg) of one diagram.
  `docs/architecture/README.md` records which file is authoritative.
- **Recovery:** `mv "_repo_archive/archi_duplicate_diagrams" "<repo>/Archi"`

---

## Items that were relocated *inside* the repo (NOT archived — still tracked/present)

These were moved for organisation only and remain part of the project:

| Original | New location |
|----------|--------------|
| `Survey_paper.pdf` | `docs/reports/literature/Survey_paper.pdf` |
| `Dental X-Ray Capstone Literature Review.xlsx` | `docs/reports/literature/` |
| `DENTAL_AI_ANALYSIS_REPORT.md` | `docs/reports/legacy/DENTAL_AI_ANALYSIS_REPORT.md` (content reorganised into `docs/results/PAPER_MATERIAL.md`) |
| `YOLO_trained.ipynb` (top level, H200 run) | `notebooks/yolo_detection/h200_768px_50ep.ipynb` |
| `notebooks/Bone Loss/` | `notebooks/bone_loss/` (`git mv`, space removed) |
| `pes_capstone_report/` | `docs/reports/pes_capstone_report/` (`git mv`, history preserved) |
| `docs/flowcharts/pipeline_flowchart.svg` | `docs/architecture/pipeline_flowchart.svg` (`git mv`) |

---

## Restoring everything

To put the working tree back exactly as it was before this cleanup:

```bash
cd "Capstone/Deepak impleentation"
REPO="An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection"
mv _repo_archive/implementation_stale_clone   "$REPO/Implementation"
mv _repo_archive/datasets_workspace           "$REPO/DataSets"
mv _repo_archive/yolo_a100_run_workspace      "$REPO/A100_150"
mv _repo_archive/archi_duplicate_diagrams     "$REPO/Archi"
mv _repo_archive/empty_docs_flowcharts_dir    "$REPO/docs/flowcharts"
cd "$REPO" && git checkout -- . && git reset --hard <commit-before-restructure>
```

---

## Addendum, 20 August 2026 — verified state of this archive on this machine

This manifest describes what was archived on 2026-08-12, from wherever that restructuring
originally ran. **As of 20 Aug 2026, on this machine, the archive is only partially
present** — worth recording so a future session doesn't have to re-derive this:

| Folder | Present here? | What's actually in it | What the manifest above says it should hold |
|---|---|---|---|
| `implementation_stale_clone/` | **No** — folder does not exist on this machine | — | The stale nested clone, 175 MB |
| `datasets_workspace/` | **Partial** — 22 MB | Only `convert_tufts_to_yolo.py`, `convert_tufts_to_yolo.py.bak`, `evaluate_yolo.py`, `train_yolo.py`, `week1_tufts_eda_v2.ipynb`, `x.ipynb`, `y.ipynb` — the three scripts are confirmed byte-identical to `scripts/yolo/` | 2.2 GB: `opg_env/` venv, `dataset.tar.gz`, raw `Radiographs/`, `Radiographs_rotated/`, `Segmentation/` (incl. `teeth_polygon.json`), `Student/`, `Expert/`, `ZIP/`, scratch notebooks |
| `yolo_a100_run_workspace/` | **Yes, complete** — 106 MB | `YOLO_trained.ipynb` (confirmed byte-identical to `notebooks/yolo_detection/a100_1024px_150ep.ipynb`) and `runs_backup/runs/detect/runs/detect/tufts_clean_v1/` — training + test-eval run dirs, including `weights/best.pt` and `weights/last.pt` | Same — this one matches in full |
| `archi_duplicate_diagrams/` | **Yes** — 96 KB | Matches; already committed into the repo directly (see the 2026-08-19 commit that added `.gitignore` rules for the other three folders) | Same |

**Practical consequence:** `best.pt`/`last.pt` were recovered from `yolo_a100_run_workspace/`
and are now copied into `models/06_yolo_detection_a100_run/` — see
`docs/research/T0.6_detector_reconciliation.md` §1 and the 2026-08-20 `RESULTS_LOG.md` entry.
`teeth_polygon.json` and the raw Tufts radiograph images are **still missing** — they were
never in `datasets_workspace/` here, only referenced in this manifest's description of what
was originally archived elsewhere. If you're reading this from a machine where the full
`datasets_workspace/` (2.2 GB, matching the table above) is actually present, that's the
place to look next, not this one.

---

## Item 6 — 20 August 2026: `survey_paper/` → `survey_paper_stale_47ref_draft/`

- **Original path:** `<repo>/survey_paper/` (repo root, alongside `Survey Paper Latex folder/`)
- **Size:** ~1 MB (`IEEEtran.cls`, `conference_101719.tex`, 5 figure files, `source.bib`)
- **Git status before move:** untracked (`?? survey_paper/`), and had never been tracked —
  no commits touch this path anywhere in `git log --all`.
- **What it was:** an earlier, superseded draft of the survey paper. Confirmed stale by
  direct comparison, not assumption: its `source.bib` has 47 `@` (reference) entries, vs. 71
  in the current, committed `Survey Paper Latex folder/source.bib` — the file the project's
  survey track actually works from (per `docs/research/MASTER_PLAN_2026H2.md` §5.1 and
  multiple `RESULTS_LOG.md` entries, e.g. the 2026-08-15 "survey: fix metric-count error, add
  DentVLM citation" commit).
- **Why moved:** flagged as an open decision across two prior sessions
  (`transfer.md`, then this session's Part 0); confirmed genuinely superseded rather than a
  parallel in-progress draft, so archiving rather than deleting was the safe call per
  `CLAUDE.md` rule 3.
- **Recovery:** `mv "_repo_archive/survey_paper_stale_47ref_draft" "<repo>/survey_paper"`
