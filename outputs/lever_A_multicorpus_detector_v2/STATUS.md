# Lever A — multi-corpus detector "done right" — **DONE 3 Sep 2026 · ABLATION**

Cold-start hub for this experiment. If you are picking Lever A up, read this file top to
bottom, then `../../models/15_detector_multicorpus_leverA/run_summary.txt` and
`../../models/15_detector_multicorpus_leverA/repro/README.md`.

- **Protocol (frozen before any GPU spend):** `PRE_REGISTRATION.md` (this dir), committed
  `ac927da` / `cc76ab5`.
- **Journal entries:** `docs/results/RESULTS_LOG.md` **2026-09-03** (primary + Guard 2) and
  **2026-09-03b** (Guard 1 + full verdict). Never edited after the fact — that is the house rule.
- **Scoreboard:** `docs/results/model_metrics.md` → "Lever A" subsection.
- **Paper:** `docs/results/PAPER_MATERIAL.md` §8.10 + §8.12a.
- **Weights:** `models/15_detector_multicorpus_leverA/{controlB,arm3c,arm4c}_best.pt` — 51 MB
  each, **gitignored, local disk only, not yet on Drive** (same gap as models/11, 13, 14).
  sha256 in `run_summary.txt` and `repro/README.md`.

---

## 1 · The verdict

Pre-registered rule (`PRE_REGISTRATION.md` §5): **adopt iff PRIMARY and GUARD 1 and GUARD 2 all
pass.** 2 of 3 pass → **ABLATION. The pipeline default detector is unchanged**
(`models/11_yolo_seg_tufts_r1` / `tooth-detector-seg-tufts-1024-v1.0`). Bar not moved.

| criterion | rule | Control | **Arm 3C** (primary) | Arm 4C |
|---|---|---|---|---|
| **PRIMARY** — FDI exact **end-to-end**, 164 leak-free DENTEX images, method=head, head=models/10; paired cluster bootstrap over images (10k, seed 42) | Δ vs Control A: 95% CI excludes 0 **and** lower bound ≥ +5 pp | A: **0.5844** | **0.9284** &nbsp; Δ **+34.40 pp [+30.29, +38.54]** ✅ | 0.9284 &nbsp; Δ +34.40 pp [+30.12, +38.71] ✅ |
| **GUARD 1** — pooled external caries lesion agreement, Ningxia ×4 (1,013 lesions) + CariesXrays random-1500 seed 42 (3,421), **frozen** caries gate v3.0, detector swapped; paired bootstrap over 1,837 images | Δ (arm − Control A) lower bound ≥ −2 pp | A: **0.3313** | **0.4224** &nbsp; Δ **+9.11 pp [+7.49, +10.81]** ✅ | 0.4082 &nbsp; Δ +7.69 pp [+6.08, +9.31] ✅ |
| **GUARD 2** — Tufts frozen **TEST** box mAP@0.5 (measured on the GPU box, `yolo val` on `best.pt`, 150 frozen Tufts images) | arm ≥ Control B − 4 pp = **0.6843** | B: **0.7243** | **0.5852** ❌ (0.099 below floor) | **0.5520** ❌ |
| **verdict** | PRIMARY ∧ GUARD 1 ∧ GUARD 2 | | **ABLATION** | **ABLATION** |

Per-metric detail behind the primary (`<arm>/stage2_summary_head.json`):

| arm | recall | FDI-exact of-detected | **FDI-exact end-to-end** | det/img | best epoch |
|---|---|---|---|---|---|
| Control A (deployed seg, `models/11`) | 0.708 | 0.825 | **0.5844** | 22.0 | — |
| Arm 3C (Tufts+DENTEX+Kaggle, 2100 bal) | 0.996 | 0.932 | **0.9284** | 27.5 | ~118 / 148 |
| Arm 4C (+ UFBA-425, 2800 bal) | 0.990 | 0.937 | **0.9284** | 27.6 | ~110 / 140 |
| Control B (Tufts detect only, 700) | — | — | — *(not measured — Control B exists only to set the Guard-2 floor)* | — | 106 / 136 |

Guard 1 by cohort (`RESULTS_LOG` 2026-09-03b):

| cohort | Control A | Arm 3C | Arm 4C |
|---|---|---|---|
| Ningxia pooled (1,013 lesions) | 0.407 | **0.600** (+19.3 pp, up on all 4 splits) | 0.548 (+14.1 pp) |
| — test1 / test2 / test3 / test4 | .294 / .519 / .401 / .392 | .519 / .702 / .512 / .624 | .475 / .636 / .457 / .586 |
| CariesXrays random-1500 (3,421 lesions) | 0.309 | **0.370** (+6.1 pp) | 0.367 (+5.8 pp) |
| **pooled (4,434 lesions)** | **0.331** | **0.422** | **0.408** |

---

## 2 · What this means (and does not mean)

**It is not an adoptable pipeline improvement** — Guard 2 (pre-registered) exists to protect the
reproducibility of every Tufts number already published, and it failed, monotonically in corpus
count: Tufts-only 0.724 → +DENTEX+Kaggle **0.585** → +UFBA **0.552**. Worse than Lever 1's single
arm (0.647). The pre-registered hypothesis — "more corpora + per-corpus balancing = less
dilution" — was **backwards**: balanced sampling put Tufts at 33 % of the training mix (vs Lever
1's 52 %), and a corpus's own held-out box mAP scales with its **training share**, not with how
balanced the mix is.

**What it gives the paper (Framing A+) is stronger than Lever 1's flat "domain dilution":**

1. The **"58 % end-to-end ceiling is detector *domain*, not the numbering method"** decomposition
   now **replicates** — Lever 1 (+34.9 pp) and Lever A (+34.40 pp) both roughly double the
   headline when the detector is in-domain, across different corpus counts and sampling. A
   robust result, not a one-off.
2. A clean **3-point in-domain / cross-domain tradeoff curve** for a single-class tooth
   detector: 0.724 → 0.585 → 0.552 on Tufts test as domains are added.
3. The tradeoff is **bidirectional and quantified**. The multi-corpus detector is **worse on
   Tufts test by ~14–17 pp** and **better on DENTEX e2e (+34 pp) and on every external cohort
   (Ningxia +19, CariesXrays +6)** — i.e. better on **5 of the 6 paper cohorts**, worse only on
   the one it is benchmarked against. Guard 2 protects benchmark continuity, not the deployment
   goal; that is a limitation of *our own adoption criterion* — it belongs in the discussion and
   was **not** used to move the bar.
4. UFBA-425 (640×640 aspect-distorted Roboflow export) is **inert** for the DENTEX-domain metric
   (Arm 3C = Arm 4C = 0.9284) and only adds Tufts dilution — the pre-registration correctly kept
   it an *additive* arm.

The 92.8 % is an **in-domain** number (the arm's detector is now DENTEX-trained; head models/10
was already DENTEX+Tufts; evaluated on held-out DENTEX). It is **not** the cross-domain scenario
the 58.3 % headline measures. Do not quote it as "the pipeline now works everywhere" — the same
detector scores 0.585 on Tufts test.

The **adoptable positive headline number, if there is one, is Lever B's to find** (§5).

---

## 3 · Artifact index

Everything below is **tracked in git** unless marked local-only.

| path | contents |
|---|---|
| `PRE_REGISTRATION.md` | the frozen protocol — corpora, recipe, arms, §5 acceptance bars, pre-flight logic checks |
| `STATUS.md` | this file |
| `controlA/stage2_{summary,rows,per_image}_head.json` | PRIMARY eval, Control A (`models/11` deployed seg) |
| `arm3c/…` , `arm4c/…` `stage2_*_head.json` | PRIMARY eval, the two multi-corpus arms |
| `{arm3c,arm4c}/primary_bootstrap.json` | paired-bootstrap Δ for the primary. ⚠️ its `verdict` **string** is stale (old Lever-1 "< 0.75" rule); the numbers are correct and `leverA_verdict.json` is authoritative |
| `{arm3c,arm4c}/leverA_verdict.json` | **the authoritative pre-registered verdict** — all 3 criteria, from `score_leverA_arm.py` |
| `{controlA,arm3c,arm4c}/ningxia_caries.json` | GUARD 1 raw — per-image Ningxia caries agreement (copy of `outputs/ningxia_leverA_<arm>/ningxia_external.json`) |
| `{controlA,arm3c,arm4c}/cariesxrays_caries.json` | GUARD 1 raw — per-image CariesXrays-1500 agreement (copy of `outputs/cariesxrays_external_leverA_<arm>/cariesxrays_external_pipeline.json`) |
| `models/15_detector_multicorpus_leverA/run_summary.txt` | full model record + sha256 + "what the 92.8 % is/is not" |
| `models/15_detector_multicorpus_leverA/{controlB,arm3c,arm4c}_results.csv` | per-epoch losses + Tufts-val curves |
| `models/15_detector_multicorpus_leverA/leverA_train.log` | full box training + Guard-2-val log |
| `models/15_detector_multicorpus_leverA/repro/` | **the exact as-run scripts** + a verify-every-number cheat sheet |
| `models/15_detector_multicorpus_leverA/{controlB,arm3c,arm4c}_best.pt` | **local-only** (51 MB each, gitignored, Drive-TBD) |
| `scripts/yolo/build_multicorpus_detector_v2_dataset.py` | dataset builder (4 corpora, rotation, geometry gate, dedup, list emit) |
| `scripts/yolo/train_multicorpus_detector_v2.py` | trainer (`--arm {controlB,arm3c,arm4c}`; config byte-identical to Lever 1; runs Guard-2 val after each train) |
| `scripts/eval/score_leverA_arm.py` | applies `PRE_REGISTRATION.md` §5 |
| `data/detector_multicorpus_v2/` | **local-only** (467 MB, gitignored, regenerable) — the built training set |
| `outputs/{ningxia,cariesxrays_external}_leverA_{controlA,arm3c,arm4c}/` | **local-only** — the original Guard-1 run dirs (the JSONs are copied into this tree, above) |

---

## 4 · Verify every number

See `models/15_detector_multicorpus_leverA/repro/README.md` for the full cheat sheet (CPU/MPS,
no GPU, ~15 min). The one command that reproduces the verdict from the tracked JSONs:

```bash
O=outputs/lever_A_multicorpus_detector_v2
/opt/anaconda3/bin/python3 scripts/eval/score_leverA_arm.py --label arm3c \
    --arm-stage2   $O/arm3c/stage2_rows_head.json \
    --ctrlA-stage2 $O/controlA/stage2_rows_head.json \
    --arm-caries   $O/arm3c/ningxia_caries.json $O/arm3c/cariesxrays_caries.json \
    --ctrlA-caries $O/controlA/ningxia_caries.json $O/controlA/cariesxrays_caries.json \
    --guard2-arm 0.5852 --guard2-controlB 0.7243
# -> PRIMARY PASS, GUARD 1 PASS, GUARD 2 FAIL, verdict ABLATION
```

Guard-2 values (`--guard2-arm` / `--guard2-controlB`) come from the GPU box and are recorded in
`leverA_train.log`, `{arm}_results.csv`, and `run_summary.txt` — they are not re-derivable on CPU.

**Env parity check:** Control A in the primary reproduces the documented 0.5844 e2e / 22.0
det-img headline exactly, and reproduces the published §8.25 CariesXrays 0.309 and §8.12a
Ningxia-pooled 0.407 in Guard 1 — so the local eval environment and scripts are sound.
Control B's Tufts test box mAP 0.7243 matches Lever 1's Control B (0.724) to 3 dp — GPU/env
parity confirmed.

---

## 5 · Continue here → Lever B

Lever A is closed. The next lever in the accepted plan
(`docs/session-memory/2026-09-02c-score-lever-council-and-plan.md` §5) is **Lever B — the
lesion-detection caries path**, the remaining shot at an *adoptable positive headline number*.

- Protocol: `outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md` (drafted, not yet frozen —
  one review round with the user/mentor, then frozen before the build).
- **Data prep is local and free:** (1) write the DENTEX `quadrant-enumeration-disease` → YOLO
  caries-box converter; (2) build the **seed-43** CariesXrays eval draw, disjoint from the 4,800
  training images.
- **B-single** = reuse `models/14/best.pt` (the Lever 2 CariesXrays lesion detector) — **zero
  GPU**. **B-pooled** = CariesXrays + DENTEX disease caries boxes — **~₹300**.
- Score: **frozen** downstream, lesion→tooth mapping, vs the image-blind constant **and** the
  AND-gate v3.0, on DENTEX-164 + Ningxia ×4 + the fresh seed-43 CariesXrays draw.

Also open, lower priority than Lever B (from `RESULTS_LOG` 2026-09-03b follow-ups):

- A **Tufts-weighted (not balanced)** multi-corpus arm would give a third frontier point (Tufts
  share 33 % → 52 % → ~70 %) and make the "you can't keep both" argument airtight. ~₹600, not
  pre-registered.
- `ningxia_external.py` `--tag` does not namespace `--out` — one-line fix (derive `--out`
  default from `--tag`) so the first-pass overwrite can't recur.
- Upload `models/15/*.pt` (and 11, 13, 14) to Drive.

GPU balance after Lever A: **₹1,732**. Nothing running. Instance 496005 destroyed.

---

## 6 · The built dataset (`data/detector_multicorpus_v2/`, local-only)

| corpus | train img | train box | 10% test img | frame |
|---|---|---|---|---|
| Tufts (frozen split_v1) | 700 | 18,221 | 150 (frozen, box 3,924) | native — already in the detector frame |
| DENTEX `quadrant_enumeration` | 561 | 15,981 | 62 (box 1,794) | rotated 90° CCW |
| Kaggle "dual" (LabelMe polygons → bbox) | 449 | 11,847 | 50 (box 1,294) | rotated 90° CCW |
| UFBA-425 (CC BY 4.0; 640×640 Roboflow) | 382 | 10,412 | 43 (box 1,172) | rotated 90° CCW |

- **val = Tufts only, 150 img** — canonical box count 3,794 reproduced exactly (build aborts otherwise).
- **test = Tufts frozen 150 (Guard 2)** + per-corpus 10% slices (a per-corpus mAP secondary).
- Geometry gate: 42,500 rotated boxes round-tripped, **median IoU vs source = 1.0000, PASS**; re-passed after the 1600 px / q85 resize.
- Leakage guard: the 164 leak-free DENTEX eval images hashed — **0 refusals**.
- Dedup: 11 byte-identical DENTEX images dropped (Lever 1 missed these), 1 Kaggle.
- Rotated corpora **capped at 1600 px / JPEG q85** — an upload-size mitigation for a slow home
  connection (1.1 GB → 467 MB). Training imgsz is 1024 and YOLO letterboxes every image to
  ~1024, so the cap is well above what the model sees; gate re-passed.

Train / test lists emitted by the builder:

| list | lines | arm / use |
|---|---|---|
| `train_tufts.txt` | 700 | Control B |
| `train_3corpus.txt` | 2,100 | **Arm 3C — primary** (Tufts+DENTEX+Kaggle, balanced 3×700) |
| `train.txt` | 2,800 | Arm 4C (+ UFBA-425, balanced 4×700) |
| `test_tufts.txt` | 150 | **Guard 2** — Tufts frozen test box mAP@0.5 |
| `test_{dentex,kaggle,ufba}.txt` | 62 / 50 / 43 | per-corpus detection-mAP secondary |

Balancing is by path repetition; verified real on ultralytics 8.4.127 (`YOLODataset` keeps
duplicate `train.txt` lines, `len(dataset) == n_lines`).

---

## 7 · Historical — the pre-run plan (every step done)

Kept for the record; superseded by §1–§6.

- **Hardware:** JarvisLabs RTX PRO 6000 Blackwell 96 GB, IN1. Started as instance **495956**;
  a pause/resume (to stop billing during a slow upload) spawned a **new container 496005** with
  a new IP and lost the pip installs (`/home` persists, the conda env does not). Env rebuilt to
  torch 2.11.0+cu130 / ultralytics 8.4.127 / Python 3.10 — identical to Lever 1's box. Instance
  **destroyed** after the 3 `best.pt` were downloaded + sha256-verified. Spend **~₹735**
  (₹2,467 → ₹1,732; ~₹150 of that pause/resume + failed-upload overhead, ~₹585 the training).
- **Upload:** `jl upload` of the 1.1 GB tar was unreliable on the home upstream (40–400 KB/s,
  jittery). Fixes: reduced the dataset to 467 MB (1600 px / q85), then `rsync --partial
  --append` in a retry loop with a sha256-verified completion check.
- **Pre-flight ML-logic checks (before renting), all passed:** balancing is real (above);
  0 leakage of Kaggle-dual / UFBA-425 vs the Guard-1 cohorts (Ningxia caries + all 6,000
  CariesXrays — 0 exact MD5, min aHash Hamming 39 / 57 of 256); training config byte-identical
  to `train_multicorpus_detector.py` (only the `train:` list varies per arm).
- **On-box:** `leverA_box_gate.py` → `GATE: GO`; `leverA_train_all.sh` (nohup) ran Control B →
  Arm 3C → Arm 4C over ~4.3 h with the Guard-2 val after each.
- **Bug caught:** the first local primary pass used a bash-4 `declare -A` array under macOS
  bash 3.2 → all 3 arms silently ran `arm4c_best.pt` (identical, real-but-mislabelled 0.9284).
  Re-run with explicit per-arm invocations (`leverA_primary2.sh`); Control A then reproduced
  0.5844 exactly. The three `stage2_rows_head.json` now have distinct sha256.
- **`ningxia_external.py` `--tag` overwrite:** the first Guard-1 pass overwrote 2 of 3 Ningxia
  dumps (`--tag` does not namespace `--out`); re-run with explicit `--out` (`leverA_ningxia.sh`).
