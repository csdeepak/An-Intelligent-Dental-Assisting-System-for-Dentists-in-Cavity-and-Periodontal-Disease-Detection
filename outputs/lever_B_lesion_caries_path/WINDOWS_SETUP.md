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
| **`models/14_cariesxrays_lever2/weights/best.pt`** (the **B-single** arm) | ~51 MB | ✅ **on this Windows laptop already** (per the user) — see §4 to verify + commit it | sha256 must be `278d1e00ed87472fa44700b7dbfb07721f694e45f81256b88e1f1700f4606548` |
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

## 4 · `models/14/best.pt` — it's on this laptop; verify it, then commit it

The user confirmed the B-single weights are **on this Windows laptop** (they were downloaded here
during the 2 Sep Lever 2 run, not to the Mac — which is why a Mac-side search couldn't find them).

```powershell
# 1. put it where the code expects it (if it isn't already):
#    models\14_cariesxrays_lever2\weights\best.pt
# 2. verify the pin — this is not optional (a size check is not an integrity check):
python -c "import hashlib; print(hashlib.sha256(open(r'models/14_cariesxrays_lever2/weights/best.pt','rb').read()).hexdigest())"
#    must print: 278d1e00ed87472fa44700b7dbfb07721f694e45f81256b88e1f1700f4606548
# 3. back it up — a .gitignore exception was added 3 Sep so best.pt (not last.pt) is committable:
git add models/14_cariesxrays_lever2/weights/best.pt
git commit -m "chore: models/14 B-single weights (from the Windows laptop, sha256 verified)"
#    then tell the user to push
```

If the hash does **not** match, do not use it — retrain from `data/cariesxrays_det/` (~₹250,
`scripts/yolo/train_cariesxrays_detector.py`, same recipe as Lever 2) or run Lever B as
**B-pooled only** (the pre-reg's rule is on "the better of B-single / B-pooled" — with one arm
it is just that arm).

---

## 5 · Ready check

```powershell
python -c "import torch, ultralytics; print(torch.__version__, ultralytics.__version__)"
python scripts/eval/verify_invariants.py
dir models\09_caries_gate_v3\caries_gate_v3.pth ; dir models\10_fdi_head_dentex_tufts_v2\enumeration_head_best.pth ; dir models\11_yolo_seg_tufts_r1\best.pt
dir "$env:USERPROFILE\Downloads\Capstone\DENTEX\training_data\quadrant-enumeration-disease\train_quadrant_enumeration_disease.json"
dir "$env:USERPROFILE\Downloads\Capstone\CariesXrays_Dataset"
dir models\14_cariesxrays_lever2\weights\best.pt     ; # on this laptop — verify sha256 per §4
```
All present (Ningxia optional — see §2) ⇒ go to `START_HERE.md` Step 2.
