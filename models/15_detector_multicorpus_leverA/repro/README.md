# Lever A — the exact scripts that were run (3 Sep 2026)

These are the **as-run** orchestration scripts for Lever A, preserved verbatim so the
run can be checked and repeated. They are records, not polished tools — the reusable
tools they call live in `scripts/` (`train_multicorpus_detector_v2.py`,
`score_leverA_arm.py`, `build_multicorpus_detector_v2_dataset.py`, `validate_fdi_assignment.py`,
`ningxia_external.py`, `cariesxrays_external.py`, `bootstrap_ci.py`).

Full narrative + verdict: `../run_summary.txt`, `../../../outputs/lever_A_multicorpus_detector_v2/STATUS.md`,
`docs/results/RESULTS_LOG.md` 2026-09-03 + 2026-09-03b.

> **On another machine:** the three local `*.sh` hardcode this Mac's checkout path (line 2) and
> `PY=/opt/anaconda3/bin/python3` (line 3, must be a Python with `torch` + `ultralytics==8.4.127`).
> Edit those two lines, or just run the underlying `scripts/eval/*.py` calls directly — the
> `run ()` / `nin ()` / `cxr ()` bodies show the exact flags.

| script | where it ran | what it did |
|---|---|---|
| `leverA_box_gate.py`   | GPU box, after tar extract, before training | re-checks the dataset that arrived == the dataset that was built (tar sha256, no AppleDouble junk, YOLO label sanity, ultralytics loads every list, renders a few for eyeball). Must print `GATE: GO`. |
| `leverA_train_all.sh`  | GPU box (`nohup`)                           | trains **Control B → Arm 3C → Arm 4C** sequentially, one instance, identical config; each calls `train_multicorpus_detector_v2.py --arm <arm>`, which runs the Guard-2 Tufts-**test** `yolo val` on `best.pt` immediately after its train. Prints each `best.pt` sha256 + greps the Guard-2 line at the end. |
| `watch_leverA.sh`      | this Mac (background)                       | polled the box every 7 min via `/home/box_status.sh`; woke the session on `all_finished` / `any_failed` / process-gone / timeout. Hardcoded box IP + scratchpad path — pure record. |
| `leverA_primary2.sh`   | this Mac (CPU/MPS)                          | the **PRIMARY** eval: `validate_fdi_assignment.py --method head --head-weights models/10/…` on the 164 leak-free DENTEX images, for Control A (`models/11`) + Arm 3C + Arm 4C. Writes `outputs/lever_A_multicorpus_detector_v2/<arm>/stage2_*_head.json`. `sha256sum`s the three row files at the end (they must differ — see the `declare -A` bug in `run_summary.txt`). |
| `leverA_guard1.sh`     | this Mac (CPU/MPS)                          | **GUARD 1**, first pass: `ningxia_external.py` (caries) + `cariesxrays_external.py --sample 1500 --seed 42`, `--detector` swapped per arm, frozen gate v3.0. |
| `leverA_ningxia.sh`    | this Mac (CPU/MPS)                          | **GUARD 1**, Ningxia re-run with explicit `--out outputs/ningxia_leverA_<arm>` — the first pass overwrote 2 of 3 Ningxia dumps because `--tag` does not namespace `--out` (see `run_summary.txt` open items). |

## Verify every headline number (CPU/MPS, no GPU, ~15 min total)

```bash
PY=/opt/anaconda3/bin/python3                       # 3.12; has torch 2.2 / ultralytics 8.4.127
O=outputs/lever_A_multicorpus_detector_v2

# --- weights integrity (51 MB each, gitignored — local disk / Drive-TBD) ---
shasum -a 256 models/15_detector_multicorpus_leverA/{controlB,arm3c,arm4c}_best.pt
#   controlB d3aa1e388fc41da1a449d2dd39b1e6c0764e8dd541edbc91c6cf896ac0145757
#   arm3c    5d301f13fb48da5c74e7ef01bd0f91226f9b6800cb433dee5aebc8f8db8f161e
#   arm4c    8cafd77a3e9b27eb2e15be2f4b26f6d89b043ae0a37af849786541d67860ade7
#   (these match models/15_detector_multicorpus_leverA/run_summary.txt)

# --- PRIMARY (FDI e2e on the 164 leak-free DENTEX images) ---
bash models/15_detector_multicorpus_leverA/repro/leverA_primary2.sh
#   Control A 0.5844   Arm 3C / Arm 4C 0.9284   (see $O/<arm>/stage2_summary_head.json)

# --- GUARD 1 (pooled external caries agreement, frozen gate) ---
bash models/15_detector_multicorpus_leverA/repro/leverA_guard1.sh
bash models/15_detector_multicorpus_leverA/repro/leverA_ningxia.sh   # Ningxia with correct --out

# --- VERDICT (applies PRE_REGISTRATION.md §5; Guard-2 numbers come from the box) ---
$PY scripts/eval/score_leverA_arm.py --label arm3c \
    --arm-stage2   $O/arm3c/stage2_rows_head.json \
    --ctrlA-stage2 $O/controlA/stage2_rows_head.json \
    --arm-caries   $O/arm3c/ningxia_caries.json $O/arm3c/cariesxrays_caries.json \
    --ctrlA-caries $O/controlA/ningxia_caries.json $O/controlA/cariesxrays_caries.json \
    --guard2-arm 0.5852 --guard2-controlB 0.7243 --out $O/arm3c/leverA_verdict.json
# repeat with --label arm4c, --guard2-arm 0.5520
```

The Guard-1 inputs (`<arm>/ningxia_caries.json`, `<arm>/cariesxrays_caries.json`) are copies of
`outputs/ningxia_leverA_<arm>/ningxia_external.json` and
`outputs/cariesxrays_external_leverA_<arm>/cariesxrays_external_pipeline.json`, placed here so the
verdict command above runs against one directory. `score_leverA_arm.py:load_caries()` reads either
key spelling (`covered`/`n_covered`, `lesions`/`n_lesions`).

## Repeat the training (GPU, ~4.3 h, ~₹600 on an RTX-PRO-6000-class card)

```bash
# 1. build + gate the dataset locally (regenerable; never committed)
/opt/anaconda3/bin/python3 scripts/yolo/build_multicorpus_detector_v2_dataset.py
# 2. tar data/detector_multicorpus_v2/  (images + labels + all 7 lists + data.yaml), sha256
# 3. rent RTX-PRO-6000 / A100-80GB, upload, extract, then:
python models/15_detector_multicorpus_leverA/repro/leverA_box_gate.py /home/detector_multicorpus_v2 <tar_sha256>   # -> GATE: GO
nohup bash models/15_detector_multicorpus_leverA/repro/leverA_train_all.sh > /home/leverA_train.log 2>&1 &
# 4. download the 3 best.pt + results.csv; sha256; DESTROY the instance
```
