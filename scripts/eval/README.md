# `scripts/eval/` — evaluation and error-propagation

Scripts that measure the pipeline rather than build or train it. This is where contribution
**C3** (system-level metrics + stage-wise error-propagation decomposition,
`MASTER_PLAN_2026H2.md` §2.3) is produced.

| Script | Measures | Status |
|---|---|---|
| `validate_fdi_assignment.py` | Stage 1 → Stage 2: does the pipeline give each tooth the right FDI number? | ✅ run for both methods |
| `validate_fdi_assignment_tufts.py` | Same, on **Tufts** — detector → `models/10` head → Hungarian, vs the *complete* mirror-corrected Tufts numbering (3,760 teeth). The Stage-2 end-to-end number the paper lacked. Reuses the DENTEX eval's matcher/viz + `src.utils.fdi_converter.tufts_title_to_fdi`. | ✅ 4 Sep — deployed 64.8 % e2e; the multi-corpus box-mAP guard failure = ~1 pt e2e cost. `RESULTS_LOG` 2026-09-04d |
| `analyze_stage2_ceiling.py` | Why rank-order assignment has a ceiling, and by how much the head clears it | ✅ run on `outputs/stage2_clean` |
| `ablate_head_inputs.py` | Which input carries which FDI digit — tests the architecture's stated rationale | ✅ run on the 2,729-crop val split |
| `tufts_pos_feat_diagnostic.py` | **Council Option B** (`docs/session-memory/2026-09-05b`): is the positional-feature covariate shift a lever for the low Tufts FDI number? Scores `models/10` on GT-box crops (Tufts test + DENTEX val) under pos-feat interventions incl. a Tufts→DENTEX geometry rescale. | ✅ 6 Sep — **falsified** (+0.1 pp): the Tufts gap is the image-derived position digit (73.5% vs DENTEX 91.9%). `RESULTS_LOG` 2026-09-06 |
| `compare_caries_gates.py` | Before/after for the caries gate, through the pipeline, same boxes and crops | ✅ 84.9% → 19.1% |
| **`verify_invariants.py`** | **Re-checks the facts the documentation depends on.** Run after changing data, swapping a checkpoint, or before trusting a number in a draft | ✅ 7/7 hold |
| **`lesion_localization.py`** | Do predicted-diseased teeth spatially overlap a real expert lesion? §4.3.4's primary EXTERNAL number for C2 (Ningxia-ready — no negatives needed) and the T1.5 XAI metric. `--decision {pipeline, constant-molars, all-teeth, lesion-detector}` — the last (4 Sep, Lever B) swaps the caries gate for a standalone lesion-detector YOLO model (`--lesion-model`), scored via argmax-containment onto detected tooth boxes, **not** `detect_upright` (that helper is hardcoded to the tooth detector's rotation convention — see `ningxia_external.run_lesion_detector`'s docstring). | ✅ **44.3%** on DENTEX (seg detector, 27 Aug; old detector 42.0%). **Lever B, 4 Sep:** B-single lesion-detector **8.6%** (decisive loss vs gate/constant), B-pooled **45.5%** (statistical tie) — `RESULTS_LOG` 2026-09-04f / 04g |
| **`ningxia_external.py`** | **C2 external validation** — the three §4.3.4 measurements on Ningxia, stratified by centre. Metric differs by category (focal vs diffuse). `--detector` swaps the Stage-1 detector (Lever A Guard 1). `--decision` gained `lesion-detector` (4 Sep, Lever B) — also the **shared home** for `lesion_preds_to_tooth_idx` (argmax-containment) and `run_lesion_detector` (deliberately unrotated inference), imported by the other two eval scripts below. ⚠️ **`--tag` renames the printed label but NOT `--out`** — pass `--out` explicitly when running several detectors or the later runs overwrite the earlier `ningxia_external.json` (bit 2 of the 3 Sep Guard-1 pass; a one-line fix is queued in `RESULTS_LOG` 2026-09-03b follow-ups). | ✅ caries 22.6–43.3%, periodontitis 0.8–5.4%; **3 Sep (Lever A):** multi-corpus detector lifts pooled Ningxia caries agreement 0.407 → 0.600. **Not yet run for Lever B** — Ningxia is not on the Windows machine; the `lesion-detector` decision mode is wired and ready the moment it arrives |
| **`crop_eval.py`** | **Crop-level** Stage-2 evaluation on a held-out manifest split — GT boxes, plain argmax, no detector in the loop. Used to compare Stage-2 heads **across corpora** (e.g. a DENTEX-trained head measured on Tufts), which `validate_fdi_assignment.py` cannot do since it always runs against `DENTEX/disease/`. Imports `ToothSet` from `scripts/dentex/train_enumeration_head.py` rather than reimplementing preprocessing. | ✅ produced the v1.0-vs-v2.0-vs-Tufts-only 2×2, `RESULTS_LOG.md` 2026-08-25j |
| **`caries_position_bias.py`** | Does the caries gate read lesions, or tooth position? Stratifies P(caries) by tooth type, computes within-type AUC, compares mean score on genuinely-healthy teeth to the training base rate. Reproduces the published confusion matrix as a correctness gate. | ✅ 31 Aug — within-type AUC **0.7454 [0.6604, 0.8420]**; 48.2% of healthy molars flagged. `PAPER_MATERIAL.md` §8.24 |
| **`caries_arms_compare.py`** | Applies the pre-registered rule (`outputs/caries_arms/PRE_REGISTRATION.md`) to the CLAHE / crop-expand / position-balance gate arms. Primary metric AP; comparator a same-day control; paired cluster bootstrap over images. | ✅ 31 Aug — all three arms miss the bar (CLAHE +0.0488 [−0.0031, +0.0993]); nothing adopted. `RESULTS_LOG.md` 2026-08-31b |
| **`cariesxrays_external.py`** | Evaluates the **frozen** pipeline on CariesXrays (AAAI 2024) as a **6th external cohort**. `--decision {pipeline, constant-molars, lesion-detector}`, `--sample N --seed 42` (random draw — a prefix risks one acquisition batch), **`--detector` to swap the Stage-1 detector** (Lever A Guard 1, everything else frozen). Reads image dimensions from the decoded pixels, never the XML `<size>` (27.3% wrong there). Imports `match_by_centroid` (+ `lesion_preds_to_tooth_idx`, `run_lesion_detector` for the 4 Sep `lesion-detector` arm) from `ningxia_external.py` so cohorts stay comparable. **`--manifest-split {train,val}`** (4 Sep, Lever B) restricts to a `data/cariesxrays_det/manifest.csv` split — `val` is the frozen, disjoint-by-construction 1,200-image Lever B eval cohort, replacing an earlier "fresh seed-43 draw" plan that turned out to be arithmetically impossible (the raw release is exactly 4,800+1,200, nothing left to draw). | ✅ 1 Sep — pipeline **0.309** vs constant **0.561**, paired Δ **+0.252 [+0.232, +0.273]** on 3,421 lesions. `PAPER_MATERIAL.md` §8.25. **Lever B, 4 Sep** (1,200-image val split): gate **31.7%**, constant **56.2%**, B-single lesion-detector **69.4%**, B-pooled **68.4%** — both lesion-detector arms beat both comparators decisively (CI excludes 0) |
| **`score_lever1_arm.py`** | Applies the Lever-1 pre-registration to one detector arm: paired cluster bootstrap of ΔFDI end-to-end (arm − same-day control) over the 164 images, plus the guard verdict (Tufts test box mAP@0.5 ≥ 0.75). Reuses `bootstrap_ci.py`'s `paired_bootstrap`/`load_stage2` — no reimplementation. `--control-rows` swappable to compare Arm vs Control B. | ✅ 1 Sep — Arm Δ end-to-end **+34.9 pp [+30.8, +39.0]** (primary passes), guard **0.647 < 0.75** (fails) → **ABLATION**. `RESULTS_LOG.md` 2026-09-01h |
| **`score_leverA_arm.py`** | Applies the **Lever A** pre-registration (`outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md` §5): PRIMARY (ΔFDI e2e, paired bootstrap, lower bound ≥ +5 pp), GUARD 1 (pooled external caries agreement Δ over Ningxia + CariesXrays, lower bound ≥ −2 pp), GUARD 2 (Tufts test box mAP ≥ Control B − 4 pp, passed in). ADOPT iff all three; else ABLATION. Pools the two caries dumps' differing key names (`n_covered`/`covered`). | ✅ 3 Sep — PRIMARY **+34.40 pp [+30.29, +38.54]** pass, GUARD 1 **+9.11 pp [+7.49, +10.81]** pass, GUARD 2 **0.585 < 0.684** fail → **ABLATION**. `RESULTS_LOG.md` 2026-09-03 + 03b |
| **`lever_b_bootstrap.py`** | Applies the **Lever B** pre-registration (`outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md` §5/§6): lesion-localisation agreement of the lesion detector vs the caries gate v3.0 vs the image-blind molar constant, paired cluster bootstrap (reuses `bootstrap_ci.py`'s primitives — no new matcher), applies the Sec 6 rule mechanically. `--arm-tag {B-single,B-pooled}` selects which lesion-detector run to score; pipeline/constant-molars sources are shared between both. Normalises the two source scripts' different `per_image` key names (`n_lesions`/`n_matched` vs `lesions`/`covered`) rather than editing either producer. | ✅ 4 Sep — DENTEX + CariesXrays scored for both arms; Sec 6 not yet met (needs Ningxia, not on this machine — 1 of 2 scored cohorts passes either way). `RESULTS_LOG.md` 2026-09-04f / 04g, `outputs/lever_b_eval/acceptance_rule_{B-single,B-pooled}.json` |
| **`caries_intervals.py`** | Three pre-registered measurements for the caries tables (`outputs/caries_intervals/PRE_REGISTRATION.md`): an interval on the headline FDI-set F1 gap, Lever B per Ningxia hospital, and the adopted lesion detector on the Table I metric. Runs no model; reuses `bootstrap_ci.py`, `c1_vlm_baseline.score` and `lever_b_bootstrap.load_normalised`. Each measurement first reproduces a published number exactly and stops if it cannot. The detector arm itself comes from `c1_vlm_baseline.py --arm pipeline --caries-method lesion-detector` — that arm now **defaults to the gate**, because a bare re-run would otherwise have overwritten the published `arm_pipeline.json` with the lesion detector's predictions. | ✅ 11 Oct — constant − gate pipeline **+2.61 pp [−0.64, +5.99]** (not separable); detector − constant per hospital, not separated at test1; detector pipeline F1 **0.376**, **+5.64 pp [+1.74, +9.47]** over the constant. `RESULTS_LOG` 2026-10-11 |

## `validate_fdi_assignment.py`

Runs the frozen detector plus either Stage-2 method against `DENTEX/disease/` — the only
per-tooth FDI ground truth this project has (LabelMe polygons labelled
`{id}-{Turkish name}-{FDI}`).

**`--head-weights` still defaults to Stage-2 head v1.0** (`models/08_fdi_enumeration_head/`),
not the pipeline's current default (v2.0, `models/10_fdi_head_dentex_tufts_v2/`). This is
deliberate: this script is the reproducibility harness for the historical 46.5% end-to-end
number, and changing its default would make a bare re-run silently reproduce a different
figure than every number already written into `docs/results/*.md`. Pass
`--head-weights models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` explicitly to
evaluate the currently-deployed head this way — or use `crop_eval.py` below, which is what
actually produced the v1.0-vs-v2.0 comparison.

```bash
python scripts/eval/validate_fdi_assignment.py --method positional   # the baseline
python scripts/eval/validate_fdi_assignment.py --method head         # the current method
python scripts/eval/validate_fdi_assignment.py --method head --no-one-to-one   # ablation
python scripts/eval/validate_fdi_assignment.py --method head --save-viz        # overlays
```

## Results — 164 leak-free images, 936 GT teeth, identical settings

| | Positional | **Head** |
|---|---|---|
| Detection recall | 67.0% | 67.0% |
| Quadrant correct (of detected) | 92.3% | **94.7%** |
| FDI exact (of detected) | 34.1% | **69.4%** |
| **FDI exact, end-to-end** | 22.9% | **46.5%** |

A **2.0× improvement**. On teeth in complete (8-detection) quadrants — rank-order's best case —
positional tops out at **66.3%** while the head reaches **80.2%**, a **+13.9 point** margin on an
identical population (n=101); the head wins in every completeness bucket, because it does not
depend on rank order. **End-to-end is now capped by detection**, not numbering — at 67.0% recall
that is the maximum available.

> *Corrected 24 Aug 2026:* this previously read "tops out at 67.0% … the head reaches 69.4%".
> **67.0% is the detector's recall, not the ceiling**, and 69.4% is over *all* detected teeth,
> not the complete-quadrant subset — two different populations. Recompute with
> `analyze_stage2_ceiling.py`; see RESULTS_LOG 2026-08-24a.

Writes `stage2_{summary,rows,per_image}_{method}.json`, plus annotated overlays with
`--save-viz` (blue = GT numbered correctly, red = wrong or missed, orange = flagged).

## Four things that make this evaluation honest — and are easy to get wrong

- **86 images are excluded as training duplicates.** 85 are byte-identical to
  enumeration-head training images; 1 to a detector training image. The list lives in
  `data/dentex/disease_leaked_images.json` and is loaded automatically. **A first run reported
  52.2% before this was caught — an inflation of 5.7 points.** The cause is worth remembering:
  `quadrant_enumeration` and the disease *subset* (705) genuinely are disjoint patients, and
  that was verified — but `disease/` is a *third* folder sharing a third of its images. A
  verified fact about one pair was generalised to a pair never measured.
- **Check leakage against every training corpus separately.** When Ningxia arrives, test it
  against Tufts, DENTEX *and* the enumeration corpus independently. Do not infer from a
  neighbouring pair; that is exactly the mistake above.
- **GT → detection only; no precision is reported.** `disease/` annotates only teeth carrying a
  finding (~6 of ~30 per image), so an unmatched detection is usually a real tooth with no
  annotation. A precision figure here would be meaningless.
- **NMS IoU is 0.50, not the frozen run's recorded 0.70.** Chosen *a priori* on anatomy — real
  teeth do not overlap by half their area — **not** by sweeping it against this evaluation set.

## Ablation: one-to-one assignment

Measured on the clean 164-image set, 24 Aug 2026 (both rows, identical settings):

| | FDI/detected | End-to-end | Quadrant | Duplicate codes |
|---|---|---|---|---|
| Hungarian one-to-one | **69.4%** | **46.5%** | 94.7% | **0** |
| Plain argmax | 65.1% | 43.6% | **96.8%** | **679** |

Plain argmax emits **679 anatomically impossible duplicate codes** — a mouth has at most one
tooth 16. The constraint removes **all** of them and gains **+4.3 points** of-detected /
**+2.9 end-to-end**, while *costing* **2.1 points of raw quadrant accuracy**: satisfying the
global one-to-one constraint sometimes moves a tooth across a quadrant boundary. That trade is
worth taking — a duplicate code is not a slightly-wrong answer, it is an impossible one that a
downstream report cannot render.

*(Supersedes the earlier 72.7 / 52.2 vs 70.6 / 50.7 / 1,013 figures, which were measured on the
pre-leak-fix 249-image set. The clean numbers show a **larger** benefit than the contaminated
ones did. RESULTS_LOG 2026-08-24b.)*

**Re-run this after any Stage-1 or Stage-2 change.** It is the before/after on a held-out set
that has never been tuned on. Full record: `docs/results/RESULTS_LOG.md` 2026-08-22c, 22f, 22i
and **22j (the leakage correction)**.


## `verify_invariants.py` — why it exists

Every correction in `RESULTS_LOG.md` has the same shape: **an inference that was never tested
was written down as fact, then propagated into other documents until it read as known.**

| Correction | The untested inference |
|---|---|
| 21f | checkpoints "presumably lost" → they were on Kaggle |
| 21m | filenames overlap → assumed same patient (they were different people) |
| 22d | the rotated files "look right" → rotation was the other way |
| 22j | two folders are disjoint → a **third** folder was never tested; 34% leaked |
| 24a | two numbers both read ~67% → one was recall, not the ceiling |
| 24e | a shuffle ablation → assumed it models detector noise; it does not |
| 25a | "healthy teeth NOT derivable" → derivable by MD5, just not by filename |

Every one was catchable by a cheap direct test, and each took minutes once actually attempted.
The failure was never difficulty — it was that the check felt unnecessary.

This script runs those checks. It proves the specific things the docs assert are still true of
the files on disk; it does not prove the project correct. It needs no GPU and no model
inference — `--skip-slow` drops the two MD5 corpus joins and finishes in seconds. Since
26 Aug 2026 it pins **both** Stage-2 head hashes (v1.0 and v2.0) — a model swap is only ever
an addition here, never an overwrite, so both must stay reproducible.

---

**Publication target and grading criteria:** `../../transfer.md` §5.
