# 2026-09-03 — Lever A: trained, evaluated, ABLATION verdict

**Session goal:** execute Lever A (multi-corpus detector "done right") end to end — trainer,
GPU run, the pre-registered primary + two guards, verdict — and log everything.

## What was done

- **Pre-flight ML-logic checks (before renting):**
  - Verified empirically that ultralytics 8.4.127 `YOLODataset` keeps duplicate `train.txt`
    lines (`len(dataset) == n_lines`) — so the per-corpus balancing (path repetition) is real,
    not a no-op.
  - Leakage: Kaggle-dual + UFBA-425 vs the Guard-1 eval cohorts (Ningxia caries + all 6,000
    CariesXrays) — 0 exact MD5, min aHash Hamming 39 / 57 of 256. Guard 1 valid.
  - Confirmed the training config is byte-identical to `train_multicorpus_detector.py` (Lever 1)
    / the canonical run; only the `train:` list varies per arm.
- **Wrote `scripts/yolo/train_multicorpus_detector_v2.py`** (`--arm {controlB, arm3c, arm4c}`,
  runs the Guard-2 Tufts-test val on `best.pt` right after each train) and
  **`scripts/eval/score_leverA_arm.py`** (the pre-registered §5 verdict). Added `--detector` to
  `scripts/eval/cariesxrays_external.py` for Guard 1.
- **Builder changes** (`build_multicorpus_detector_v2_dataset.py`): emit per-arm train lists
  (`train_tufts` / `train_3corpus` / `train.txt`) and per-corpus test lists; `./`-relative paths
  so the lists survive the move to the box; **cap rotated corpora at 1600 px / JPEG q85**
  (upload-size mitigation, 1.1 GB → 467 MB — training imgsz is 1024, YOLO letterboxes to ~1024
  regardless; geometry gate re-passed at IoU 1.0000, resized renders eyeballed).
- **GPU run:** JarvisLabs RTX PRO 6000 96 GB, IN1 (instance 495956 → 496005 after a pause/resume
  — resume spawns a new container id + IP and drops pip installs, `/home` persists). Env torch
  2.11+cu130 / ultralytics 8.4.127, identical to Lever 1. On-box gate `GATE: GO`.
  `leverA_train_all.sh` (nohup) ran Control B → Arm 3C → Arm 4C over ~4.3 h. All 3 `best.pt`
  downloaded + sha256-verified, instance **destroyed**. **Cost ~₹735** (balance ₹2,467 → ₹1,732;
  ~₹150 was pause/resume + failed-upload overhead — the home upstream was 40–300 KB/s and jittery).
- **Local eval (CPU/MPS, no GPU):**
  - PRIMARY — `validate_fdi_assignment.py` on the 164 leak-free DENTEX images, head=models/10,
    for Control A (models/11) + Arm 3C + Arm 4C.
  - GUARD 1 — `ningxia_external.py` + `cariesxrays_external.py` (`--detector` swap, frozen gate,
    Ningxia caries ×4 + CariesXrays-1500 seed 42) for all 3.
  - GUARD 2 — from the box (`yolo val` on each `best.pt`, test = 150 frozen Tufts images).
  - `score_leverA_arm.py` applied the pre-registered rule.

## Results

| criterion | rule | Arm 3C | Arm 4C |
|---|---|---|---|
| PRIMARY — FDI e2e Δ vs Control A (0.5844 → 0.9284) | lower bound ≥ +5 pp | **+34.40 pp [+30.29, +38.54]** ✅ | +34.40 [+30.12, +38.71] ✅ |
| GUARD 1 — pooled ext caries agreement Δ (Ningxia 0.407→0.600, CariesXrays 0.309→0.370; 4,434 lesions) | lower bound ≥ −2 pp | **+9.11 pp [+7.49, +10.81]** ✅ | +7.69 [+6.08, +9.31] ✅ |
| GUARD 2 — Tufts frozen test box mAP@0.5 | ≥ Control B (0.7243) − 4 pp | **0.5852** ❌ | 0.5520 ❌ |
| **verdict** | primary AND both guards | **ABLATION** | **ABLATION** |

- Control A reproduces the documented headline (58.4 % e2e, 22.0 det/img) and §8.25/§8.12a
  caries numbers exactly — env + scripts confirmed sound.
- Primary **replicates Lever 1** (+34.9 pp) with 3–4 corpora + balancing.
- UFBA-425 is inert for the primary (Arm 3C = Arm 4C = 0.9284); its only effect is more Tufts
  dilution (Guard 2 0.585 → 0.552).

## Decisions made

- **Verdict = ABLATION, bar NOT moved.** 2 of 3 criteria pass; the pre-registration requires all
  three. Pipeline default detector stays `models/11_yolo_seg_tufts_r1`. *Reason:* the pre-reg is
  the pre-reg; Guard 2 exists to protect the reproducibility of every Tufts number published
  before this, and it failed.
- **But the paper framing changes.** Lever 1 was a flat "domain dilution → ablation". Lever A
  shows the tradeoff is **bidirectional and quantified**: the multi-corpus detector is worse on
  Tufts test by ~14–17 pp and **better on DENTEX (+34) and every external cohort (+6 to +19)** —
  better on 5 of the 6 paper cohorts, worse only on the one it is benchmarked against. *Reason:*
  the pipeline's stated purpose is screening arbitrary panoramic X-rays; the Guard-2 criterion
  protects benchmark continuity, not the deployment goal. This is a limitation of our own
  adoption rule — stated in the discussion, **not** grounds to move the bar. The paper reports
  the multi-corpus detector's full 6-cohort table as "what a deployment-optimised choice costs
  and buys", clearly labelled, while the default detector stays `models/11`.
- **Rotated corpora resized to 1600 px / q85** for Lever A only. *Reason:* the home upstream was
  too slow to push 1.1 GB reliably; training imgsz is 1024 so the model sees ~1024 either way;
  geometry gate re-passed. Documented in `run_summary.txt` and `RESULTS_LOG`.

## Open questions

1. **A Tufts-weighted (not balanced) arm** would give a third point on the frontier (Tufts share
   33 % → 52 % → ~70 %) and make the "you can't keep both" argument airtight. ~₹600, not
   pre-registered, **below Lever B** in priority.
2. **`ningxia_external.py` `--tag` does not namespace `--out`** — the first Guard-1 pass
   overwrote 2 of 3 Ningxia dumps; re-run with explicit `--out`. Worth a small fix to the script
   so this can't recur (a one-liner: `--out` default derived from `--tag`).
3. **`models/15/*.pt` are the only copy** (local disk) — same Drive-upload gap as
   `models/11`, `13`, `14`.
4. **Guard-1 eval ran on MPS** (the head/gate device auto-selects MPS on this Mac), a deviation
   from the project's CPU-only eval norm. It is internally consistent (all arms same device) and
   Control A reproduced the published CPU numbers exactly, so the paired comparison is sound —
   but note it if a reviewer asks.

## Next steps

1. **Lever B** — the lesion-detection caries path (`outputs/lever_B_lesion_caries_path/
   PRE_REGISTRATION.md`). The remaining shot at an *adoptable* positive headline number. Data
   prep first (local): the DENTEX `quadrant-enumeration-disease` → YOLO caries converter, the
   seed-43 CariesXrays eval draw disjoint from the 4,800 training images. Then B-single (reuse
   `models/14/best.pt`, zero GPU) + B-pooled (~₹300).
2. **User / mentor:** the Lever A tradeoff result strengthens the Framing-A+ paper — fold it
   into the manuscript's Stage-2 / external-validation sections (`PAPER_MATERIAL.md` §8.10 and
   §8.12a are updated). Still open: journal choice, compliance blockers, authors in `main.tex`.
3. Bug-fix `ningxia_external.py --out`/`--tag` (open question 2).
