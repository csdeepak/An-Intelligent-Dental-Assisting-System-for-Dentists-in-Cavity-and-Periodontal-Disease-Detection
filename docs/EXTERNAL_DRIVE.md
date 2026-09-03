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

**Already in git — nothing to do** (updated 3 Sep 2026 — `models/09` + `models/11` added):

| File | Loaded as |
|---|---|
| `models/07_caries_cascade/final_model.pth` | (superseded by v3 below, kept for reproducibility) |
| `models/07_caries_cascade/phase2_final_bundle.pth` | `DEF_CARIES_SEVERITY` |
| `models/08_fdi_enumeration_head/enumeration_head_best.pth` | Stage-2 head **v1.0** — superseded 26 Aug but retained and hash-pinned |
| `models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` | `DEF_FDI_HEAD` (**v2.0**, DENTEX+Tufts) |
| **`models/11_yolo_seg_tufts_r1/best.pt`** (53 MB) | **`DEF_DETECTOR`** — committed 3 Sep via a `.gitignore` exception (private repo) for the Windows handoff |
| **`models/09_caries_gate_v3/caries_gate_v3.pth`** (43 MB) | **`DEF_CARIES_GATE`** — committed 3 Sep, same size as the `10` head |
| `models/03_bone_loss_model_training_notebook_models/bone_loss_resnet18_best.pth` | `DEF_BONE_LOSS` |
| `models/04_bone_loss_severity_notebook_models/bone_loss_severity_resnet18_best.pth` | `DEF_BONE_SEVERITY` |

**`git clone` now runs `run_inference.py` with no download.** Still outside git:

| File | Size | Why not in git |
|---|---|---|
| `models/06_yolo_detection_a100_run/best.pt` | 49 MB | superseded as `DEF_DETECTOR`; only for reproducing pre-27-Aug numbers |
| `models/13_detector_multicorpus_lever1/*.pt`, `models/15_.../*.pt` | ~51 MB each | Lever 1 / A ablation weights; SHA-256 in each `run_summary.txt` |
| `models/14_cariesxrays_lever2/weights/best.pt` | 51 MB | Lever 2 / **Lever B's B-single arm** — **on the friend's Windows laptop**; a 3 Sep `.gitignore` exception makes it committable once sha256 `278d1e00…` is verified (`outputs/lever_B_lesion_caries_path/WINDOWS_SETUP.md` §4). `last.pt` stays out. |

> **⚠️ Changed 27 Aug 2026 — a fresh clone now needs THREE files, not two.** The Stage-1
> detector was swapped to the YOLOv11l-seg model (`RESULTS_LOG.md` 2026-08-27d). Both detectors
> are listed because the new one is required to *run* the pipeline and the old one is required
> to *reproduce* anything published before that date.
>
> **RESOLVED 3 Sep 2026 — `models/11` is now committed to git.** A fresh clone runs
> `run_inference.py` with no download. The upload steps below are kept for a Drive *backup*
> and for `models/06`.
>
> **This is a manual step and cannot be automated from a Claude Code session** — confirmed
> twice now (25 Aug for the first two checkpoints, 27 Aug for this one). The reasons are
> concrete, not incidental: the browser tool's file-upload caps at **10 MB** and this file is
> **53.3 MiB**; `gdown` is download-only; `rclone` and `gh` are not installed; and uploading to
> Drive requires authenticating as the account owner, which a session will not do. Please stop
> re-attempting it and just do the 60-second drag-and-drop below.

### Uploading `models/11_yolo_seg_tufts_r1/best.pt` — the exact steps

1. Open the **Tufts** drive folder (link in the table above) — it was trained on Tufts.
2. If `capstone_checkpoints/` does not exist yet: **New → Folder → `capstone_checkpoints`**.
3. Drag `models/11_yolo_seg_tufts_r1/best.pt` into it. **Rename it in Drive to
   `yolo_seg_tufts_r1_best.pt`** — three of this project's checkpoints are called `best.pt`,
   and a folder with two files of that name is how the wrong weights get restored.
4. **Verify the upload is intact** — re-download it and check the hash matches the frozen one:

   ```bash
   # expected, from models/11_yolo_seg_tufts_r1/run_summary.txt
   # 271316c46caaf4029ea707fa77b6fe30697795e46632e1f6fcae3498c48781ba
   sha256sum <downloaded-file>
   ```

   This is not paranoia: during the 27 Aug DENTEX fetch, one file arrived truncated at 2,428
   bytes and was silently accepted by a size>0 check, which cost a full evaluation run.
   `scripts/eval/verify_invariants.py` checks this same hash automatically once the file is in
   place locally.
5. Delete this whole warning block once it is done, and un-bold the row above.

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

**Downloading is scriptable — only *uploading* needs a human.** `gdown` fetches a public
Drive file by id with no OAuth, so a Claude Code session can restore a checkpoint unattended.
The ids below were resolved on 27 Aug 2026 and the caries gate was fetched and hash-verified
this way; record any new id here so nobody has to enumerate a folder again (finding this one
meant listing **10,781** entries in the DENTEX drive).

| File | Drive | `gdown` id | Verified |
|---|---|---|---|
| `models/09_caries_gate_v3/caries_gate_v3.pth` | DENTEX | `1pBI1oeIoMF8d-k0o7ETUyWnjtyfOT_pL` | ✅ 27 Aug 2026 — 44,787,894 B, sha256 `8f4a99ba412c…`, matches the pin |
| `models/06_yolo_detection_a100_run/best.pt` | Tufts | *not yet resolved* | — |
| `models/11_yolo_seg_tufts_r1/best.pt` | Tufts | **not uploaded yet** — see the warning above | — |

```bash
# after git clone, from the repo root:
mkdir -p models/06_yolo_detection_a100_run models/09_caries_gate_v3 models/11_yolo_seg_tufts_r1

# caries gate -- scripted, id resolved above:
python -c "import gdown; gdown.download(id='1pBI1oeIoMF8d-k0o7ETUyWnjtyfOT_pL', \
  output='models/09_caries_gate_v3/caries_gate_v3.pth', quiet=False)"

# the two detectors: still manual from the drive links above
#   Tufts drive -> models/06_yolo_detection_a100_run/best.pt   (superseded; needed only to
#                                                               reproduce pre-27-Aug numbers)
#   Tufts drive -> models/11_yolo_seg_tufts_r1/best.pt         (DEF_DETECTOR -- NOT UPLOADED YET)

# ALWAYS verify before trusting a download -- this is not optional:
python scripts/eval/verify_invariants.py   # checks every present checkpoint against its pin
python scripts/run_inference.py --image <any_opg.png> --output report.json
```

> **A size check is not an integrity check.** On 27 Aug a DENTEX image truncated at 2,428 bytes
> passed a `size > 0` test and silently cost an evaluation run. `verify_invariants.py` compares
> the SHA-256 recorded in each `run_summary.txt` against the bytes on disk, which is why the
> step above is listed as mandatory rather than advisory.

To resolve an id for a file whose folder you can reach:

```bash
python -c "
import gdown
files = gdown.download_folder(url='<folder-url>', skip_download=True, quiet=True)
for f in files:
    if f.path.lower().endswith(('.pth','.pt')): print(f.path, f.id)
"
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
