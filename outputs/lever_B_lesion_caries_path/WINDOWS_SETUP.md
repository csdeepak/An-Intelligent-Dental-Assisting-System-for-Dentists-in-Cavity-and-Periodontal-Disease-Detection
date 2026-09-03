# Lever B — Windows setup (for the friend)

Ownership (decided 3 Sep 2026): **the user does Phase 0 + Lever A2 on the Mac; the friend does
Lever B on Windows.** This file is the Windows side. Read `START_HERE.md` for what Lever B is and
the step-by-step plan; this file is only "get the machine ready".

The Windows machine already used for this project (`transfer.md` §8, as of 27 Aug 2026) has a
rebuilt Python env, the Tufts `ZIP/`, `models/06`, and — importantly — **the DENTEX subsets**
(`training_data/` + `validation_data/` + `disease/`, 6 GB, fetched 27 Aug with
`scripts/dentex/fetch_dentex_subsets.py`). If your laptop is a *different* Windows machine,
you also need DENTEX (below).

---

## 1 · `git pull` gets you most of the checkpoints now

As of commit **[this change]**, three checkpoints are **committed to git** — a `git pull` brings
them in, no Drive round-trip:

| file | size | role in Lever B |
|---|---|---|
| `models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` | 43 MB | FDI enumeration head (was always tracked) |
| `models/11_yolo_seg_tufts_r1/best.pt` | 53 MB | **`DEF_DETECTOR`** — maps lesions → teeth at eval (Step 5) |
| `models/09_caries_gate_v3/caries_gate_v3.pth` | 43 MB | gate-v3.0 comparator (Step 5) |

Verify them after pulling:
```powershell
python scripts/eval/verify_invariants.py    # checks every present checkpoint against its pinned sha256
```
Expected sha256 (also in each `models/<NN>/run_summary.txt`):
- `models/11_.../best.pt` → `271316c46caaf4029ea707fa77b6fe30697795e46632e1f6fcae3498c48781ba`
- `models/09_.../caries_gate_v3.pth` → `8f4a99ba412c5562e0bc444fef9b856af091d3d1c8b5ba74876735e616357a76`

**Line endings:** a `.gitattributes` (`* -text`) was added so your `core.autocrlf` cannot flip
the repo's hand-managed CRLF/LF. Just `git pull`; if you have a stale local clone, a fresh
`git clone` is cleanest.

---

## 2 · What `git pull` does NOT give you — get these separately

| need | size | where | notes |
|---|---|---|---|
| **`models/14_cariesxrays_lever2/weights/best.pt`** (the **B-single** arm) | ~51 MB | ⚠️ **currently missing everywhere** — see §4. sha256 `278d1e00ed87472fa44700b7dbfb07721f694e45f81256b88e1f1700f4606548` | ask the user; if not found, either retrain (~₹250) or run Lever B with **B-pooled only** |
| **CariesXrays** raw dataset | `JPEGImages.zip` 4.2 GB + `Annotations.zip` | AAAI 2024 release / the user's Drive → `~/Downloads/Capstone/CariesXrays_Dataset/` | needed for B-pooled training **and** the seed-43 eval draw. `data/cariesxrays_det/` (the built split) is regenerated from this — it is gitignored and on no machine |
| **DENTEX** `training_data/` + `disease/` | 6 GB + 1 GB | already on the 27-Aug Windows machine; else `scripts/dentex/fetch_dentex_subsets.py` or the DENTEX Drive (`docs/EXTERNAL_DRIVE.md`) → `~/Downloads/Capstone/DENTEX/` | `quadrant-enumeration-disease/train_quadrant_enumeration_disease.json` = B-pooled DENTEX boxes; `disease/` = the 164-image DENTEX eval cohort |
| **Ningxia** dataset | 2.4 GB | **user only** — restrictive licence, `data/ningxia/` on the Windows machine holds `manifest.csv` only | one of the 3 eval cohorts. If the user cannot get it to you, Lever B runs on **DENTEX + CariesXrays** (2 of 3) and the pre-reg's "≥ 2 of 3 cohorts" rule still applies — note Ningxia as pending |

The datasets are **not** removable from `.gitignore` — CariesXrays + Ningxia + DENTEX are ~25 GB
combined and the Tufts licence forbids redistribution. Drive / the user is the only path.

---

## 3 · Python env

The 27-Aug Windows env is **Python 3.13.7 / torch 2.8.0+cpu / ultralytics 8.4.130 / numpy 2.5.2**
(79/79 tests green). That is fine for the **eval** (Steps 3, 5 — all CPU) and for data prep.

**For the B-pooled training run only**, match the project pin so the result is byte-comparable to
Lever 2:
```powershell
pip install ultralytics==8.4.127
```
The B-pooled run needs a GPU (rented, ~₹300) — it does not run on the CPU-only Windows env. Follow
`transfer.md` §6 (JarvisLabs runbook) + `START_HERE.md` Step 4. **Windows `jl` CLI gotchas are in
`transfer.md` §8** (the on-PATH `jl` is broken — use `%LOCALAPPDATA%\Programs\Python\Python313\Scripts\jl.exe`;
every remote `/path` needs `MSYS_NO_PATHCONV=1`).

---

## 4 · ⚠️ `models/14/best.pt` is missing — user action needed

`models/14_cariesxrays_lever2/run_summary.txt` records it as downloaded + sha256-verified on
2 Sep and "local disk only, not yet on Drive". As of 3 Sep it is **not** in
`models/14_cariesxrays_lever2/weights/` on the Mac, not in `_repo_archive/`, and not on Drive.

**User: before the friend starts Step 3**, either
1. locate it (external drive? Trash? the Windows machine's own download dir?), verify sha256
   `278d1e00…`, and upload to Drive; **or**
2. accept that B-single is re-trained from `data/cariesxrays_det/` (~₹250, same recipe as Lever 2
   — `scripts/yolo/train_cariesxrays_detector.py`); **or**
3. run Lever B as **B-pooled only** and drop B-single (the pre-reg's acceptance rule is on "the
   better of B-single / B-pooled" — with one arm it is just that arm).

---

## 5 · Ready check

```powershell
python -c "import torch, ultralytics; print(torch.__version__, ultralytics.__version__)"
python scripts/eval/verify_invariants.py
dir models\09_caries_gate_v3\caries_gate_v3.pth ; dir models\10_fdi_head_dentex_tufts_v2\enumeration_head_best.pth ; dir models\11_yolo_seg_tufts_r1\best.pt
dir "$env:USERPROFILE\Downloads\Capstone\DENTEX\training_data\quadrant-enumeration-disease\train_quadrant_enumeration_disease.json"
dir "$env:USERPROFILE\Downloads\Capstone\CariesXrays_Dataset"
```
All present (except possibly Ningxia and `models/14`) ⇒ go to `START_HERE.md` Step 2.
