# GPU environment setup — E2E Networks instance

**Written:** 20 August 2026. Purpose: a from-scratch checklist for provisioning a GPU
instance (E2E Networks or equivalent) to run everything currently prepared and queued —
the YOLOv11l-seg retrain (T0.6/R1) and the DENTEX caries cascade (T0.1/T0.2/T0.3). Written
so a fresh Claude Code session (or a human) on that box can follow it without re-deriving
anything from this conversation.

**§1 (console steps, image choice, pricing table) was checked directly against
`docs.e2enetworks.com` and `e2enetworks.com/gpu-cloud` on 20 Aug 2026** — not written from
memory, since a live commercial console's UI and pricing are exactly the kind of thing that
goes stale silently. Re-verify if this document is more than a few weeks old when read.

---

## 1. What to actually click in the E2E console (verified 20 Aug 2026 against `docs.e2enetworks.com` — not from memory)

E2E's GPU product for this kind of work is **TIR** (their managed AI platform — Jupyter
notebooks + GPU compute), not a bare VM you install CUDA on by hand. The exact flow,
confirmed from their current docs:

1. Log in to the **Tir Cloud Portal** (`myaccount.e2enetworks.com` → TIR), select your Project
   from the left sidebar.
2. **Products → Instances → Create Instance.**
3. **Choose an Image.** TIR offers three image types — pick **Pre-built**:
   - *Pre-built* — ready-to-use ML environments, CUDA + framework pre-installed, JupyterLab
     supported. **This is what you want.** From the pre-built catalog, select **PyTorch**
     (their listed pre-built images include Transformers, PyTorch, TensorFlow 2, Diffusers,
     NVIDIA NeMo, RAPIDS, FastAI, vLLM, and others — PyTorch is the right one, since every
     script and notebook in this repo is PyTorch/torchvision/Ultralytics, nothing needs
     TensorFlow or the others). Check **JupyterLab Supported** — pre-built images support it.
   - *Base OS* — minimal Ubuntu, nothing pre-installed, no JupyterLab. Skip this; it just
     means manually doing the CUDA/PyTorch install the pre-built image already does for you.
   - *Custom* — bring-your-own container image (Docker Hub or your own registry). Not needed
     here.
4. **Configure Compute Resources.** Pick instance type **GPU**, then a hardware plan. Current
   published pricing (`e2enetworks.com/gpu-cloud`, INR/hour, confirm before committing since
   pricing pages change):

   | GPU | VRAM | Price/hr | Price/month |
   |---|---|---|---|
   | H200 | 141 GB | ₹436 | ₹2,72,401 |
   | H100 | 80 GB | ₹362 | ₹2,26,849 |
   | A100 80GB | 80 GB | ₹189 | ₹99,250 |
   | A100 40GB | 40 GB | ₹179 | ₹81,250 |

   **Recommendation: A100 80GB.** It's what the canonical detector was already trained on
   (`models/06_yolo_detection_a100_run/run_summary.txt`), and the master plan's own compute
   budget (`MASTER_PLAN_2026H2.md` §6) says H100/H200 make "no material difference at this
   size" — so paying ~2x for H100 or ~2.3x for H200 buys nothing for this workload. Nothing
   queued needs multi-GPU.
5. **Pricing & Storage.** On-Demand (hourly) is right for this — nothing here is a long-running
   committed workload yet. Storage defaults to 30 GB free, expandable (up to several TB, raise
   a support ticket for very large asks). **Set it to at least 100 GB** — see the disk budget
   in §1a below; 30 GB is too tight once Tufts + DENTEX + run outputs are all present at once.
6. **Network & Security.** Create or select an **SSH key** — if new, it downloads as a `.pem`
   file **once, non-recoverable**; save it immediately. Attach a **Security Group** with port
   22 open, or SSH won't work even with a valid key.
7. **Advanced Settings (optional):** skip Parallel/Shared File Systems and Static IP for now —
   not needed for a single-instance training run. Storage Encryption (AES-256) is a fine
   default-on if offered at no cost.
8. **Launch Instance.**

**Critical operational detail, easy to lose work to:** the instance workspace is mounted at
**`/home/jovyan`**. Anything saved outside that path can be lost on a container restart. Clone
the repo and do all work inside `/home/jovyan` — don't work in `/root` or `/tmp`.

Use **Launch App** to open the interactive JupyterLab workspace once the instance is running;
verify the GPU is actually attached with `nvidia-smi` in a terminal or Python 3 kernel before
running anything real.

### 1a. Disk budget (why 30 GB default isn't enough)

| | |
|---|---|
| Tufts raw + rotated images + `teeth_polygon.json` | ~400 MB |
| `dataset_seg/` once built | similar order |
| DENTEX (raw xrays + processed crops, 10,446 files — see §4) | a few GB |
| YOLO `runs/` output per run | ~100-250 MB (weights + curves + plots) |
| ResNet18 checkpoints | tens of MB each |

**100 GB is comfortable headroom**; 50 GB is a workable minimum if you clean up between runs.

## 2. Software

The **PyTorch pre-built image already has CUDA + PyTorch configured** — no manual driver/CUDA
install needed, that's the entire point of choosing it over Base OS. Once inside the instance:

```bash
# Confirm what the pre-built image actually shipped before assuming versions
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
nvidia-smi

# This repo's own dependencies
pip install -r requirements.txt

# YOLO (commented out in requirements.txt — install explicitly)
pip install ultralytics

# For pulling data directly from the Google Drive folders (see §4) — no Kaggle
# credentials needed, both folders are public/shared-link accessible
pip install gdown
```

If `torch.cuda.is_available()` is `False` on a GPU instance, something's wrong with the
plan/image pairing — don't proceed to training, check the instance configuration first.

## 3. Repo

```bash
git clone https://github.com/csdeepak/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection.git
cd An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection
```

Read `docs/research/T0.6_detector_reconciliation.md` and this session's log entries in
`docs/results/RESULTS_LOG.md` (newest at the bottom) before running anything — they record
exactly what's been verified, what's still open, and why, so nothing here gets silently
redone or silently skipped.

## 4. Data

Both source datasets are reachable directly from Google Drive, no Kaggle credentials needed:

- **Tufts:** `https://drive.google.com/drive/folders/1_pPXCzNGlRuLaQhpqScX7sszSXSLQI-U`
  Fetch `teeth_polygon.json` and the raw `ZIP/Radiographs/Radiographs/` images (1,000 files,
  landscape 1615×840 — rotate with `scripts/yolo/rotate_tufts_radiographs.py` before use, see
  that script's docstring for why). Place at `data/tufts/ZIP/...` paths matching
  `.gitignore` (already set up to keep this out of git).
  **Still missing from this folder: `outputs/eda_tufts/split_v1.csv`, the frozen split the
  canonical bbox detector was evaluated on.** Locate it before running the real (non-test)
  seg conversion — see `T0.6_detector_reconciliation.md` §3.3 for what was already checked
  and ruled out.

- **DENTEX:** `https://drive.google.com/drive/folders/1DtdE_TYuYTeyvuaveQEvuhSpwL6U8Ovp`
  **This folder has more than the notebook currently reads.** Enumerated 20 Aug 2026
  (10,446 files) — structure:
  ```
  DENTEX/
    disease/{input,label}/                                         (250 + 250 files)
    training_data/
      quadrant/xrays/                                               (360 raw images)
      quadrant_enumeration/xrays/                                   (634 raw images)
      unlabelled/xrays/                                             (1,571 raw images)
      quadrant-enumeration-disease/
        train_quadrant_enumeration_disease.json                     <- original COCO-style annotations
        phase_1_Training_Processed_datasets.ipynb                   <- original crop-generation notebooks
        phase_1_Validation_Processed_datasets.ipynb
        phase_2_Training_Processed_datasets.ipynb
        xrays/                                                      (705 raw source images)
        processed_dataset/{train,val}/{caries,no_caries}/            (2767+762 / 133+49 crops)
        severity_data/{train,val}/{caries,deep_caries}/               (2189+578 / 101+32 crops)
    validation_data/quadrant_enumeration_disease/xrays/              (50 raw images)
  ```
  `phase-1.ipynb`'s `BASE_PATH` variables point at
  `.../processed_dataset` and `.../severity_data` — those are here, confirmed (severity val
  total = 133, matching every number already reported in `PAPER_MATERIAL.md` §7.2). Crop
  filenames follow `{image_id}_{crop_id}.png` (confirmed: `101_572.png` etc.), matching what
  `scripts/dentex/split_dentex_holdout.py` already assumes.

  **This is a bigger finding than it looks:** `xrays/` (705 raw source images) plus the
  original `train_quadrant_enumeration_disease.json` plus the three original
  processing notebooks mean a **genuinely independent, from-scratch three-way split** may now
  be possible — not just the "carve from val" fallback `split_dentex_holdout.py` was written
  for when raw DENTEX access looked unavailable (see that script's own docstring, and
  `RESULTS_LOG.md`'s 2026-08-19 T0.2 entry for why the fallback was chosen at the time). This
  wasn't rebuilt in this session — it's a scope decision (redo T0.2's split methodology now
  that better data exists) that should be made deliberately, not defaulted into. Flagging it
  here rather than silently either doing it or ignoring it.

## 5. Order of operations

1. **DENTEX caries cascade** — fully unblocked, start here. Fetch the DENTEX data (§4),
   decide on the split methodology (existing `split_dentex_holdout.py` fallback, or rebuild
   from raw data per the finding above — human call), then run
   `notebooks/caries/phase-1.ipynb` (Arm A + the new Arm B augmentation-ablation section).
   Report val **and** test, both arms.
2. **Tufts YOLOv11l-seg retrain** — blocked on locating `outputs/eda_tufts/split_v1.csv`
   (§4). Once resolved: `rotate_tufts_radiographs.py` → `convert_tufts_to_yolo_seg.py`
   (already proven correct against real data, 20 Aug 2026) → `train_yolo_seg.py` against the
   pre-registered criterion in `T0.6_detector_reconciliation.md` §2.

## 6. One outstanding reconciliation, unrelated to GPU setup

`C:\Users\csdee\Downloads\phase-1.ipynb` (checked 20 Aug 2026, provided by the user as "the
file I've used for the past 4 months") is **123 cells** and checkpoints on raw `val_acc`
throughout. The repo's `notebooks/caries/phase-1.ipynb` is **131 cells** — it already
includes the T0.3 macro-F1 checkpointing fix and the new Arm B augmentation-ablation section
(both committed and pushed, 19-20 Aug 2026). **Run the repo's version, not the Downloads
copy** — the Downloads copy predates those fixes. If there's a reason the Downloads copy
should be authoritative instead (e.g. it has local edits never pushed), that needs to be
said explicitly before GPU time is spent on the older version.
