# External storage — Google Drive

This repo's `.gitignore` deliberately excludes large binaries: trained model weights and
generated dataset crops (see `models/README.md` and each dataset builder's docstring for why
each specific file is excluded). This file is the map of where those live outside git, so
nobody has to re-share the two links below again.

**Read this before assuming a file is "lost" because it isn't in git** — check here first.

---

## The two drives

| Drive | Link | What it is |
|---|---|---|
| **DENTEX** | https://drive.google.com/drive/folders/1DtdE_TYuYTeyvuaveQEvuhSpwL6U8Ovp | Mirror of the DENTEX challenge release: `disease/`, `training_data/`, `validation_data/` — the same layout as `~/Downloads/Capstone/DENTEX/` referenced throughout `docs/results/*.md` and `scripts/dentex/*.py`. |
| **Tufts** | https://drive.google.com/drive/folders/1_pPXCzNGlRuLaQhpqScX7sszSXSLQI-U | Tufts Dental Database materials: `ZIP/` (raw release), `processed_dataset_tufts/`, `resampled_dataset/`, `severity_dataset/`, `models/`. |

Both were browsed read-only (not signed in) on 25 Aug 2026 to confirm the structure above —
verified, not assumed. Neither drive's contents are duplicated here in detail; treat Drive as
the source of truth for what's inside each folder and update this table if the top-level
layout changes.

> ### ⚠️ LICENCE PROBLEM WITH THE TUFTS DRIVE — resolve before submitting anything
>
> The Tufts Dental Database release agreement (read from `https://tdd.ece.tufts.edu/`,
> 26 Aug 2026) states, verbatim:
>
> - *"No permission is granted to reproduce the database or post into any webpage or any
>   other storage means."*
> - *"The Researcher may not provide research associates and colleagues with access to the
>   Database."*
> - *"The distribution of this database to any parties that have not read and agreed to the
>   terms and conditions of usage is strictly prohibited."*
> - *"Failure to follow the above steps will invite legal prosecution."*
>
> The Tufts drive above holds `ZIP/` — the **raw release** — and the note directly above
> records that it was browsable **without signing in**, i.e. link-accessible to anyone.
> That is squarely what the agreement forbids. **Action: set that folder to private /
> restricted immediately**, and keep Tufts data local-only. Each user must sign the release
> form themselves; the correct way to "share" it is to send the form link, not the files.
>
> Every publication using it must cite **both** the website and Panetta, K., Rajendran, R.,
> Ramesh, A., Rao, S. P., & Agaian, S. (2021), *Tufts Dental Database: A Multimodal
> Panoramic X-ray Dataset for Benchmarking Diagnostic Systems*, IEEE JBHI. Use is
> **non-commercial research/education only**.
>
> DENTEX is a separate matter and is not covered by this warning — check its own licence
> before mirroring it publicly too.

---

## Model checkpoints — what a fresh clone is missing, and where to get it

`git clone` alone is **not** enough to run `scripts/run_inference.py`. Cross-checked against
every `DEF_*` default in that script (re-verified 26 Aug 2026, after the Stage-2 head v2.0
swap) against `git ls-files`. **Only the two checkpoints below actually block inference — that
has not changed with the v2.0 adoption, since v2.0 is 43 MB and already tracked in git.**

**Already in git — nothing to do:**

| File | Loaded as |
|---|---|
| `models/07_caries_cascade/final_model.pth` | (superseded by v3 below, kept for reproducibility) |
| `models/07_caries_cascade/phase2_final_bundle.pth` | `DEF_CARIES_SEVERITY` |
| `models/08_fdi_enumeration_head/enumeration_head_best.pth` | Stage-2 head **v1.0** — superseded 26 Aug but retained and hash-pinned |
| `models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` | `DEF_FDI_HEAD` (**v2.0**, DENTEX+Tufts) |
| `models/03_bone_loss_model_training_notebook_models/bone_loss_resnet18_best.pth` | `DEF_BONE_LOSS` |
| `models/04_bone_loss_severity_notebook_models/bone_loss_severity_resnet18_best.pth` | `DEF_BONE_SEVERITY` |

**Missing after a fresh clone — these two, and only these two, actually block inference:**

| File | Size | Trained on | Loaded as |
|---|---|---|---|
| **`models/11_yolo_seg_tufts_r1/best.pt`** | **55.8 MB** | **Tufts** | **`DEF_DETECTOR` (since 27 Aug 2026)** |
| `models/06_yolo_detection_a100_run/best.pt` | 49 MB | Tufts | superseded as `DEF_DETECTOR`; still needed to reproduce every pre-27-Aug number |
| `models/09_caries_gate_v3/caries_gate_v3.pth` | 43 MB | DENTEX | `DEF_CARIES_GATE` |

> **⚠️ Changed 27 Aug 2026 — a fresh clone now needs THREE files, not two.** The Stage-1
> detector was swapped to the YOLOv11l-seg model (`RESULTS_LOG.md` 2026-08-27d). Both detectors
> are listed because the new one is required to *run* the pipeline and the old one is required
> to *reproduce* anything published before that date.
>
> **The seg checkpoint has NOT been uploaded to Drive yet.** Until someone does, a fresh clone
> cannot run `run_inference.py` even after following the steps below. Upload it to the Tufts
> drive's `capstone_checkpoints/` (it was trained on Tufts) and delete this warning.

Everything else on local disk under `models/` (`last.pt`, `best_model.pth`,
`best_phase2_final.pth`, `best_phase2_fixed.pth`) is training lineage, not load-bearing —
confirmed by grepping every script for a load path and finding none. They are **not** backed
up here; see `models/07_caries_cascade/run_summary.txt` for their SHA-256 if reproduction is
ever needed.

### Where they live

- `models/11_yolo_seg_tufts_r1/best.pt` → **Tufts drive**, `capstone_checkpoints/`
  (trained on Tufts). **Not uploaded yet — see the warning above.**
- `models/06_yolo_detection_a100_run/best.pt` → **Tufts drive**, `capstone_checkpoints/`
  (it was trained on Tufts).
- `models/09_caries_gate_v3/caries_gate_v3.pth` → **DENTEX drive**, `capstone_checkpoints/`
  (it was trained on DENTEX).

`capstone_checkpoints/` is a new folder in each drive, added 25 Aug 2026, distinct from any
pre-existing folder (e.g. Tufts already has a `models/` folder with unrelated Colab-era
content — this repo's checkpoints are kept separate to avoid ambiguity about what's what).

**Status as of 25 Aug 2026: folders not yet created.** Browser automation could not complete
this — `claude-in-chrome`'s file-upload tool caps at 10 MB per call, and both files exceed
that alone; the extension was also not connected in this session. This is a manual step:

1. Open the drive link above.
2. New → Folder → name it `capstone_checkpoints`.
3. Drag the file in from Finder.

### To restore on a fresh clone (a friend's laptop, or after re-cloning)

```bash
# after git clone, from the repo root:
mkdir -p models/06_yolo_detection_a100_run models/09_caries_gate_v3
# download best.pt from the Tufts drive -> models/06_yolo_detection_a100_run/best.pt
# download caries_gate_v3.pth from the DENTEX drive -> models/09_caries_gate_v3/caries_gate_v3.pth
python scripts/run_inference.py --image <any_opg.png> --output report.json   # should now run
```

If `run_inference.py` raises `missing model weights`, it names the exact missing path — cross-
check it against the table above.

---

## Keeping this file current

If a new gitignored checkpoint becomes load-bearing (a new `DEF_*` default in
`run_inference.py`, or a retrained R1/R3 model), add it to the "missing" table above and upload
it to the matching drive's `capstone_checkpoints/` folder. If the top-level structure of either
drive changes, update the table in "The two drives" section — verify by opening the link, don't
assume it still matches what's written here.

---

**Publication target and grading criteria:** `../transfer.md` §5.
