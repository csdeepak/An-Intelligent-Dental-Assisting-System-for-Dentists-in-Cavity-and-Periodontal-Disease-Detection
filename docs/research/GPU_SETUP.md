# GPU environment setup — JarvisLabs (current provider)

**Rewritten:** 26 August 2026, when the project moved from E2E Networks to **JarvisLabs** and
the R1 seg retrain became genuinely runnable. The E2E material is preserved in §9 rather than
deleted — it was verified work, it is simply no longer the provider in use.

**Everything in §1–§3 was checked against JarvisLabs' live site and docs on 26 Aug 2026**, not
written from memory. A commercial console's pricing and UI go stale silently; re-verify §1's
price table and §3's command syntax if this document is more than a few weeks old when you
read it. Runtime and cost *estimates* are labelled as estimates — they are extrapolations from
this project's own A100 bbox run, not vendor claims.

---

## 1. The instance, and what it costs

**Verified 26 Aug 2026 against `jarvislabs.ai/in` (INR pricing page):**

| GPU | VRAM | ₹/hr | Verdict for this project |
|---|---|---|---|
| H200 SXM | 141 GB | 378.27 | Overkill — see below |
| H100 SXM | 80 GB | 255.15 | Overkill |
| RTX Pro 6000 Blackwell | 96 GB | 179.01 | Untested here; no reason to introduce a variable |
| **A100 80GB** | **80 GB** | **140.94** | ✅ **This one.** |
| A100 40GB | 40 GB | 84.24 | Fits the job, but see the warning below |
| L4 / A30 | 24 GB | 41.31 / 38.88 | Too small for batch 32 @ 1024px |

**A100 80GB is the right choice, and this is not a budget compromise.** The canonical bbox
detector (`tooth-detector-a100-1024-v1.0`) was trained on an A100 80GB PCIe, and
`MASTER_PLAN_2026H2.md` §6 records that H100/H200 give "no material difference at this size."
Matching the original hardware also removes hardware as a confound in the §2 comparison.

> **⚠️ Do not "save money" by dropping to the A100 40GB and shrinking the batch.** The
> pre-registered criterion (`T0.6_detector_reconciliation.md` §2) fixes **batch 32 @ 1024px**,
> and the whole point of that pre-registration is that any metric difference is attributable
> to the bbox→mask change and nothing else. Shrinking the batch changes the effective learning
> dynamics and silently voids the comparison. The job needs ~17.9 GB; 40 GB would *fit*, but
> the reason to stay on the 80GB card is hardware parity with the original run, not VRAM.

### Budget

At **₹140.94/hr**, a **₹900** balance buys **6 hours 23 minutes**. Paused instances bill
storage only, at **₹0.0130/GB/hr** — a 100 GB volume left paused costs ~₹1.30/hr (~₹31/day),
which is cheap but *not* free, so destroy the instance when the work is done rather than
leaving it parked indefinitely.

### What R1 should actually cost — **estimate, not a measurement**

Extrapolated from this project's own A100 bbox run (`models/06_yolo_detection_a100_run/`,
128 epochs in 0.592 h = **16.6 s/epoch** at batch 32 / imgsz 1024 / 700 train images):

| Step | Estimate | ₹ |
|---|---|---|
| Instance boot + `pip install` + `yolo11l-seg.pt` download | ~10 min | ~24 |
| Upload `dataset_seg` (334 MB, ~150 MB gzipped) | ~5–15 min | ~12–35 |
| **Training** — seg heads run ~1.3–1.8× a detect head per epoch, so ~22–30 s/epoch; 150 epochs, likely early-stopping near 128 as the bbox run did | **~55–85 min** | ~130–200 |
| Test-split evaluation + packaging results | ~10 min | ~24 |
| **Total for R1** | **~1.5–2 h** | **~₹210–280** |

**That leaves roughly ₹620–690 (4.5–5 h) of headroom** — comfortably enough for one full redo
if the first run is misconfigured, which `MASTER_PLAN_2026H2.md` §6 explicitly budgets for
("assume at least one full redo"). **Compute is not the bottleneck on this project and no
decision here should be made to save GPU rupees.**

**Storage:** `--storage 100` is comfortable. The default (40 GB) technically fits R1 alone,
but leaves nothing for a second run's `runs/` output or a DENTEX fetch later. Storage is
billed per GB-hour, so 100 GB for two hours is a rounding error against the GPU cost.

---

## 2. Yes — you can drive the whole thing from this laptop. Two ways.

This answers the standing question directly: **the training does not have to be babysat in a
browser.** JarvisLabs ships a first-class CLI, `jl`, and SSH access.

### 2a. `jl` CLI — the recommended path

**Verified by installing it — `jl 0.2.17`, read from `--help` on this machine 26 Aug 2026.**
Where the published docs page and the installed binary disagree, the binary wins and is what
is recorded below. It creates, uploads to, executes on, downloads from, pauses and destroys
instances — all from a local terminal. A Claude Code session on this machine can therefore run
the entire R1 job end to end without anyone clicking through a console.

```bash
pip install jarvislabs          # or: uv tool install jarvislabs
jl setup --token <API_TOKEN> --yes
```

Get the token from **`jarvislabs.ai/settings/api-keys`**. It can also be supplied as the
`JL_API_KEY` environment variable. `jl setup` also installs agent skills — pass
`--agents claude-code` to install the Claude Code ones alongside the default `.agents/skills`.

> **⚠️ Windows / Git Bash: `jl` crashes on any help or table output** with a `rich` console
> traceback (`_check_buffer`, a Unicode encode failure against the console codepage). It is a
> display bug, not an auth or network problem. Prefix commands with UTF-8 output:
>
> ```bash
> PYTHONIOENCODING=utf-8 TERM=dumb NO_COLOR=1 jl gpus
> ```
>
> Exporting `PYTHONIOENCODING=utf-8` once per shell is enough. Without it, every table-printing
> subcommand (`gpus`, `list`, `status`, `templates`, `--help`) dies mid-render.

**The full command surface** (from `jl --help`, v0.2.17), beyond the machine-management verbs
in the table below:

| Group | Commands |
|---|---|
| Account | `setup`, `status` (**shows account balance** — check it before and after a run), `logout` |
| Resources | `gpus` (availability **and** pricing), `resources`, `cpus`, `templates` |
| Machines | `list`, `get`, `create`, `rename`, `pause`, `resume`, `destroy` |
| Remote access | `ssh`, `exec`, `upload`, `download` |
| Infrastructure | `ssh-key {list,add,remove}`, `scripts`, `filesystem`, `vpc` |
| Workloads | `run` (managed: create → upload → install → run → auto-pause) |

**`jl ssh-key add` means SSH keys can be registered from the terminal** — the web-console step
in §2b is optional.

> **The API token is a credential.** Put it in the environment or let `jl setup` store it —
> do not paste it into a chat window, a commit, or a doc. This repo has already had one
> private-key exposure incident (`transfer.md` §8); that is once more than enough.

Core commands:

| Purpose | Command |
|---|---|
| Create | `jl create --gpu A100 --storage 100 --template pytorch --name "r1-seg" --yes` |
| List / status | `jl list` (add `--json` to parse) |
| Details incl. SSH string | `jl get <machine_id>` |
| Upload | `jl upload <id> ./local/path /home/remote/path` |
| Run a command, streaming output | `jl exec <id> -- nvidia-smi` |
| Interactive shell | `jl ssh <id>` |
| Download results | `jl download <id> /home/runs ./runs -r` |
| Stop billing, keep data | `jl pause <id> --yes` |
| Delete everything | `jl destroy <id> --yes` |

**`jl create` options, read from the binary (v0.2.17) — two published defaults are wrong:**

| Option | Real default | Note |
|---|---|---|
| `--template` / `-t` | **`pytorch`** | Already the right template for this repo — everything here is PyTorch/torchvision/Ultralytics |
| `--storage` / `-s` | **100 GB** | The docs page says 40. 100 is already the comfortable figure §1 recommends, so the default is fine as-is |
| `--gpu` / `-g` | *(none)* | Free text, "e.g. H100, A100, L4" |
| `--num-gpus` | 1 | Correct — nothing queued here is multi-GPU |
| `--region` | *(unpinned)* | `IN1`, `IN2`, `EU1` |
| `--spot` | off | Cheaper (~up to 56%) but preemptible — **not** for a 1.5 h pre-registered run you cannot restart mid-way without voiding determinism |
| `--vm` | off (container) | Containers ship PyTorch + Jupyter + IDE. Keep the default |
| `--http-ports` | — | Only needed to expose the Streamlit demo, not for R1 |

**Still unresolved: how `--gpu` distinguishes the 80 GB A100 from the 40 GB one.** The help
text just reads "A100". `jl gpus` prints live availability *and* pricing and would settle it,
but requires auth, so it cannot be checked before `jl setup`. **Resolve it as the first
authenticated command, before creating anything:**

```bash
jl status                              # account balance — confirm the ₹ figure first
jl gpus                                # exact GPU strings + live ₹/hr; find the 80GB A100
jl create --gpu <exact-string> --name "r1-seg" --yes
jl list                                # confirm the card and rate you actually got
jl exec <id> -- nvidia-smi             # confirm 80GB VRAM and that CUDA is live
```

If `jl list` or `nvidia-smi` shows a 40 GB card, or a rate that isn't ~₹140.94/hr, **destroy
and recreate before training** — a wrong card discovered 40 minutes in costs the whole run,
and silently shrinking to fit it would void the pre-registered comparison (§1).

### 2b. Plain SSH

**Verified against `docs.jarvislabs.ai/ssh`, 26 Aug 2026.**

1. Generate a key **on this machine** (do not reuse or copy one from another laptop):
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_jarvis -N ""
   ```
2. Add the **public** half (`~/.ssh/id_ed25519_jarvis.pub`) at **`jarvislabs.ai/settings/ssh`**.
3. **Pause and resume any already-running instance** so it picks up the new key — this step is
   in JarvisLabs' own docs and is the usual reason a correct key still fails.
4. Connect with the host/port from `jl get <id>`:
   ```bash
   ssh -i ~/.ssh/id_ed25519_jarvis -p <port> <user>@<host>
   ```

Caveats worth knowing before you lose ten minutes to them: fix `Permission denied` with
`chmod 400` on the private key; after an instance restart the host key changes, so clear the
stale entry with `ssh-keygen -R "[host]:port"`. Adding a key does **not** retroactively apply
to a running instance (step 3).

> **A note on the old key.** `transfer.md` §8 records a `.pem` private key pasted into a chat
> transcript on 20 Aug and says to treat it as compromised. That was an **E2E** key. Generate a
> fresh key for JarvisLabs as above; do not reuse it, and confirm the old one is deleted from
> `~/Downloads` and removed from any E2E account that still has it.

### 2c. Long runs — don't let a dropped connection kill training

`jl exec` streams output over the network; if the laptop sleeps or the Wi-Fi drops mid-run,
you can lose the stream. Start training detached, then poll:

```bash
jl exec <id> -- sh -lc 'cd /home/repo && nohup python scripts/yolo/train_yolo_seg.py > /home/train.log 2>&1 &'
jl exec <id> -- sh -lc 'tail -20 /home/train.log'          # poll whenever
```

`jl run` (managed runs: create → upload → install → run → auto-pause) is the tidier option if
you want the instance to stop billing automatically when the script exits. Its auto-pause is
genuinely useful here — it removes the "forgot to shut it down overnight" failure mode.

---

## 3. R1 runbook — the one job that needs a GPU

**Prerequisite state on this machine, all verified 26 Aug 2026:**

| Input | Status |
|---|---|
| `outputs/eda_tufts/split_v1.csv` | ✅ present, SHA-256 verified against `T0.6` §3.3 — regenerable with `scripts/tufts/regenerate_split_v1.py` |
| `data/tufts/dataset_seg/` | ✅ built — 700/150/150, **26,005 instances**, 334 MB |
| `scripts/yolo/train_yolo_seg.py` | ✅ present, config pre-registered, **never run** |
| Acceptance criterion | ✅ fixed in writing, `T0.6_detector_reconciliation.md` §2 |

```bash
# 0. LOCAL — package the dataset (labels are ~206 MB of polygon text; they gzip well)
tar -czf dataset_seg.tar.gz -C data/tufts dataset_seg

# 1. Create the box. Check balance and resolve the exact A100-80GB string FIRST (§2a) —
#    these two are free, the mistake they prevent is not.
jl status                                  # account balance
jl gpus                                    # exact --gpu strings + live ₹/hr
jl create --gpu <A100-80GB-string> --storage 100 --template pytorch --name "r1-seg" --yes
jl list                                    # note the machine id; CONFIRM 80GB + rate
jl exec <id> -- nvidia-smi                 # confirm 80GB VRAM + CUDA live before spending more

# 2. Code + data
jl exec <id> -- sh -lc 'cd /home && git clone https://github.com/csdeepak/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection.git repo'
jl upload <id> ./dataset_seg.tar.gz /home/dataset_seg.tar.gz
jl exec <id> -- sh -lc 'cd /home && tar -xzf dataset_seg.tar.gz'

# 3. Deps
jl exec <id> -- sh -lc 'cd /home/repo && pip install -r requirements.txt && pip install ultralytics'
jl exec <id> -- sh -lc 'python -c "import torch;print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"'

# 4. Point data.yaml at THIS machine (it stores an absolute path written at conversion time —
#    the copy you upload still says C:\Users\csdee\... and WILL fail otherwise)
jl exec <id> -- sh -lc "sed -i 's|^path:.*|path: /home/dataset_seg|' /home/dataset_seg/data.yaml && cat /home/dataset_seg/data.yaml"

# 5. Train, detached (see §2c)
jl exec <id> -- sh -lc 'cd /home/repo && TUFTS_SEG_DATA_YAML=/home/dataset_seg/data.yaml nohup python scripts/yolo/train_yolo_seg.py > /home/train.log 2>&1 &'
jl exec <id> -- sh -lc 'tail -30 /home/train.log'

# 6. Bring everything back — weights AND the full run dir, not just best.pt
jl download <id> /home/repo/runs ./runs_r1 -r

# 7. STOP BILLING
jl pause <id> --yes        # keeps data, storage-only charge
# jl destroy <id> --yes    # only once results are safely downloaded and verified
```

**Do not modify any hyperparameter in `train_yolo_seg.py`.** Every value in it is pinned to
the canonical bbox run so the comparison stays clean; `--gpu`, batch size and image size in
particular are part of the pre-registration.

### After the run — this part is not optional

1. Evaluate on the held-out **test** split, **once**, after the checkpoint is already selected
   on validation (`T0.6` §2, "Test set discipline").
2. Check against the pre-registered bar: **box mAP@0.5 ≥ 0.75** *and* **mask mAP@0.5 ≥ 0.65**.
   If either is missed, that is reported as a documented negative result and the bbox model
   stays canonical — the bar does not move after the fact.
3. Freeze and tag like every other model: `run_summary.txt`, SHA-256, version tag
   (`models/README.md` convention).
4. Append a dated `RESULTS_LOG.md` entry; update `model_metrics.md` and `PAPER_MATERIAL.md`
   per `CLAUDE.md` rule 1; write a `docs/session-memory/` file per rule 2.
5. Re-run `scripts/eval/verify_invariants.py` and the Stage-2 evaluation — detector recall
   changing should move the Stage-2 end-to-end ceiling, and that shift must be **measured, not
   assumed**.

---

## 4. What is NOT runnable from this machine, and why

**This matters for planning and is easy to get wrong.** The Windows machine has the Tufts raw
data but **not** DENTEX or Ningxia — checked 26 Aug 2026:

| Dataset | On this machine | Consequence |
|---|---|---|
| Tufts raw + rotated + polygons | ✅ `data/tufts/ZIP/` (~400 MB) | R1 is fully runnable |
| Tufts bone-loss crops | ❌ metadata CSVs only, no images | bone-loss retrains need a rebuild first |
| DENTEX (~14 GB) | ❌ `data/dentex/` holds 2 JSON files | caries work, and the bone-loss cross-corpus idea, are blocked here |
| Ningxia (2.4 GB) | ❌ `data/ningxia/` holds `manifest.csv` | external validation cannot be re-run here |

So **R1 is the only GPU job this machine can currently feed.** Anything touching caries or the
DENTEX+Tufts bone-loss experiment needs DENTEX fetched first (Drive links in
`docs/EXTERNAL_DRIVE.md`) — either onto this laptop or straight onto the instance with `gdown`.
Fetching ~14 GB onto a billing GPU box is itself a cost decision; prefer downloading it to the
laptop while nothing is running.

**Also missing here:** `models/09_caries_gate_v3/caries_gate_v3.pth`, one of the two Drive-only
checkpoints. `run_inference.py` will not complete on this machine until it is fetched
(`docs/EXTERNAL_DRIVE.md`). `best.pt` **is** present.

---

## 5. What NOT to rent for

From `transfer.md` §6, restated because idle GPU time invites scope creep:

- **T0.5** (the n=6 Mild severity class decision), **version-tagging the bone-loss weights**,
  and **IRB paperwork** are zero-compute. Do them on the laptop.
- **C1 (the VLM baseline)** is deliberately deferred to W5. Do **not** pull it forward to
  "use the instance while it's up" — it needs a properly scoped session, not a rushed add-on.
- **`docker build` verification** needs a Docker daemon, not a GPU.

---

## 6. Environment note — the numpy pin

`requirements.txt` pins `numpy>=1.24.0,<2`, with a comment that numpy 2.x silently breaks
`scipy.optimize` (the Stage-2 Hungarian assignment), torch↔numpy conversion and sklearn.

**That pin is correct for the stack it was written against** (torch 2.2.0 / scipy 1.12 /
sklearn 1.4, all compiled against numpy 1.x). It is **not** universally true: verified 26 Aug
2026 on the Windows machine, numpy **2.4.6** with scipy 1.17.1, sklearn 1.9.0 and torch 2.13.0
runs `linear_sum_assignment` and torch↔numpy conversion correctly, and the full suite passes
**65/65** with `verify_invariants.py` clean.

The real constraint is *consistency* — numpy must match what torch/scipy/sklearn were built
against — not the number 2 itself. On a JarvisLabs PyTorch image, install `requirements.txt`
and then **check what actually landed** rather than assuming either way:

```bash
python -c "import numpy,scipy,torch;from scipy.optimize import linear_sum_assignment;import numpy as np;print(numpy.__version__, scipy.__version__, torch.__version__);print(linear_sum_assignment(np.eye(3)))"
```

If that line runs, the environment is fine. If pip's resolver downgrades numpy and breaks the
image's prebuilt torch, that is the failure mode to watch for — the opposite of the one the
comment warns about. **R1 itself does not touch scipy or sklearn**, so this cannot affect the
seg retrain; it matters when running the Stage-2 evaluation afterwards.

---

## 7. Repo

```bash
git clone https://github.com/csdeepak/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection.git
```

Read `transfer.md` first (the cold-start snapshot), then
`docs/research/T0.6_detector_reconciliation.md` §2 and §3, then the newest entries at the
bottom of `docs/results/RESULTS_LOG.md`. They record what is verified, what is open, and why —
so nothing gets silently redone or silently skipped.

---

## 8. Data sources (Google Drive)

Both live in `docs/EXTERNAL_DRIVE.md`, which is the maintained copy — **read its Tufts licence
warning before re-sharing any Tufts file anywhere.**

- **Tufts:** `https://drive.google.com/drive/folders/1_pPXCzNGlRuLaQhpqScX7sszSXSLQI-U`
- **DENTEX:** `https://drive.google.com/drive/folders/1DtdE_TYuYTeyvuaveQEvuhSpwL6U8Ovp`

The DENTEX folder holds more than `phase-1.ipynb` currently reads. Enumerated 20 Aug 2026
(10,446 files):

```
DENTEX/
  disease/{input,label}/                                       (250 + 250 files)
  training_data/
    quadrant/xrays/                                            (360 raw images)
    quadrant_enumeration/xrays/                                (634 raw images)
    unlabelled/xrays/                                          (1,571 raw images)
    quadrant-enumeration-disease/
      train_quadrant_enumeration_disease.json                  <- original COCO annotations
      phase_1_Training_Processed_datasets.ipynb                <- original crop-generation notebooks
      phase_1_Validation_Processed_datasets.ipynb
      phase_2_Training_Processed_datasets.ipynb
      xrays/                                                   (705 raw source images)
      processed_dataset/{train,val}/{caries,no_caries}/         (2767+762 / 133+49 crops)
      severity_data/{train,val}/{caries,deep_caries}/           (2189+578 / 101+32 crops)
  validation_data/quadrant_enumeration_disease/xrays/          (50 raw images)
```

Because the raw `xrays/` **and** the original COCO annotations are both present, a genuinely
independent three-way DENTEX split is possible from scratch — rather than the "carve from val"
fallback in `scripts/dentex/split_dentex_holdout.py`, written when raw access looked
unavailable. **That is a methodology decision, still open** (`transfer.md` §4); it is not a
default to slide into while an instance happens to be running.

---

## 9. Appendix — E2E Networks (superseded, kept for the record)

The project evaluated **E2E Networks** first; §1 of the 20 Aug version of this document was
verified live against `docs.e2enetworks.com` at that time. **No E2E instance was ever
launched.** Retained because the pricing comparison is still informative and because a
provider switch is not a reason to erase verified work.

E2E's product for this workload is **TIR** (managed notebooks + GPU compute). Flow was:
Tir Cloud Portal → Products → Instances → Create Instance → image **Pre-built → PyTorch** →
compute plan **GPU / A100 80GB** → On-Demand hourly → storage raised to ≥100 GB (30 GB default
is too tight) → Network & Security: attach an SSH key **and** a security group with port 22
open. Their workspace mounts at **`/home/jovyan`**; anything written outside it can be lost on
a container restart. *(That `/home/jovyan` detail is E2E/TIR-specific — do not assume it holds
on JarvisLabs; confirm the working directory there with `jl ssh <id>` and `pwd`.)*

E2E pricing as published 20 Aug 2026 (INR/hr): H200 ₹436 · H100 ₹362 · A100 80GB ₹189 ·
A100 40GB ₹179. JarvisLabs' A100 80GB at ₹140.94/hr is ~25% cheaper than E2E's ₹189, which is
part of why the project moved.

---

## 10. One outstanding reconciliation, unrelated to provisioning

`C:\Users\csdee\Downloads\phase-1.ipynb` (checked 20 Aug 2026, described by the user as "the
file I've used for the past 4 months") is **123 cells** and checkpoints on raw `val_acc`. The
repo's `notebooks/caries/phase-1.ipynb` is **131 cells** and already includes the T0.3 macro-F1
checkpointing fix plus the Arm B augmentation-ablation section. **Run the repo's version.** If
there is a reason the Downloads copy should be authoritative instead (local edits never
pushed), say so explicitly before GPU time is spent on the older one.
