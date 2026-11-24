# Repository audit — 23 Nov 2026

Phase 1–2 deliverable. Every statement below was checked against the working tree at `851f089`
(`main` = `origin/main`, clean) on the Windows clone, unless it says otherwise. Where a document and
the code disagree, the code and the saved artefacts win, and the disagreement is listed in §7.

## 1. Checks run this session

| Check | Command | Result |
|---|---|---|
| Clone in sync | `git fetch; git rev-list --left-right --count origin/main...HEAD` | `0 0` |
| Unit and end-to-end tests | `C:\venvs\dental312\Scripts\python.exe -m pytest tests -q` | **210 passed, 3 skipped** (the 3 need the raw Tufts radiographs, absent on this clone — `transfer.md` §8) |
| Data/weight invariants | `scripts/eval/verify_invariants.py` | **all invariants hold** (leakage list 85 + 1 = 86 excluded, matches disk) |
| Manuscript numbers (`paper/main.tex`) | `scripts/verify_paper_numbers.py` | **215 numeric claims verified, no drift** |
| Ningxia raw images | `ls /d/` | **not attached** — any Ningxia re-run is blocked on this machine |

## 2. Actual system architecture (from `scripts/run_inference.py::run_pipeline`)

The prompt's assumed workflow is correct in substance, with two corrections from the code:
orientation is handled *inside* Stage 1 (not a separate preprocessing stage), and the caries and
Stage-4 branches run independently on the same detected boxes (not sequentially on each other).

```
OPG (upright, any size) ── check_input(): bit depth / aspect / size warnings, never blocks
  └─ Stage 1  detect_upright(): rotate 90° CCW → YOLOv11l (imgsz 1024, conf 0.25, NMS IoU 0.50)
              → boxes un-rotated back to upright coordinates            [src/orientation.py]
  └─ Stage 2  ResNet18 + 4 box-position features scores all 32 FDI codes per crop (1.5× expand);
              Hungarian one-to-one assignment; codes below τ = 0.30 marked unsure
                                                                       [src/fdi_head_inference.py]
  ├─ Stage 3a default: whole-image YOLOv11l lesion detector; each lesion box → the tooth holding
  │           most of it (argmax containment)       [src/classifiers.py::run_caries_lesion_detector]
  │           variant (--caries-method gate): ResNet18 on the tight tooth crop
  ├─ Stage 3b ResNet18 caries vs deep caries on flagged teeth (no test set exists)
  ├─ Stage 4a ResNet18 on 1.5×/2.0× crops: "overlaps a Tufts expert abnormality mask"
  └─ Stage 4b severity head — NOT run by default since 14 Oct (--bone-severity-grade)
  └─ Stages 5–6 build_report(): fuse on FDI code → JSON (schema opg-report/1.6) + overlay PNG,
              with every checkpoint's sha256, runtime provenance and limitation strings
```

One code path serves the CLI (`main()`) and the Streamlit demo (`app.py` calls `run_pipeline`).
`app.py` shows the per-stage limitation strings from the report and a fixed warning that the
pipeline "is not clinically validated". `Dockerfile` wraps the app (CPU only).

## 3. Verified default checkpoints

| Stage | `DEF_*` (run_inference.py line) | File | In git? | Params |
|---|---|---|---|---|
| 1 | `DEF_DETECTOR` (174) | `models/15_detector_multicorpus_leverA/arm3c_best.pt` | yes | 25.31 M |
| 2 | `DEF_FDI_HEAD` (235) | `models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth` | yes | 11.19 M |
| 3a | `DEF_CARIES_LESION_MODEL` (268) | `models/16_lever_b_pooled/.../weights/best.pt` | yes | 25.31 M |
| 3a variant | `DEF_CARIES_GATE` (270) | `models/09_caries_gate_v3/caries_gate_v3.pth` | yes | 11.18 M |
| 3b | `DEF_CARIES_SEVERITY` (271) | `models/07_caries_cascade/phase2_final_bundle.pth` | yes | 11.18 M |
| 4a | `DEF_BONE_LOSS` (312) | `models/18_bone_loss_radiograph_split/seed42_best.pth` | yes | 11.18 M |
| 4b | `DEF_BONE_SEVERITY` (313) | `models/04_.../bone_loss_severity_resnet18_best.pth` | yes | 11.18 M |

All defaults are sha256-pinned and checked before loading (commits `af5cc44`, `0c032b3`). Total of
the default configuration: **95.34 M** (`outputs/param_counts/param_counts.json`). Retained and
selectable: `models/11` (previous Tufts-only detector), `models/03` (previous Stage 4a). Not in git:
`models/06`, `13`, `17`, `19`, and `controlB`/`arm4c` under `models/15`.

## 4. Datasets and annotations

| Dataset | Role | Annotation used | Licence / status |
|---|---|---|---|
| Tufts Dental Database (1,000 OPGs) | detector + numbering training; Stage 4 label source; test split 143 | tooth boxes/masks; expert *abnormality* masks; FDI numbering is mirrored in the release | redistribution forbidden; a Drive folder was found browsable (live compliance item, `transfer.md` §4) |
| DENTEX (MICCAI 2023) | numbering + caries training; disease subset = development cohort (164 scored of 250 after removing 86 MD5 copies) | quadrant/enumeration/diagnosis boxes; caries and deep caries | CC BY-NC-SA 4.0; figures show its pixels (share-alike open) |
| CariesXrays (AAAI 2024, 6,000 OPGs) | lesion-detector training; 1,200-image split = its validation set and a "cohort" | lesion boxes | no licence file; used under citation |
| Ningxia multi-centre (Li et al. 2024) | external test only, 4 test sets (337 images, 1,013 lesions) | lesion masks | locked: never trained or tuned on; informed Lever B adoption |
| UFBA-425 | numbering only, no model trained on it | tooth labels, squashed 640×640 export | — |
| Kaggle "dual-labelled" (499 images) | part of the default detector's training mix | FDI boxes | **licence unstated** — open item for a shipped default |
| SDH clinic (3,219 images) | **no result uses it** | — | de-identification void; must stay out |

## 5. Completed experiments (each with its record)

| Experiment | Outcome | Record |
|---|---|---|
| Image-blind constant vs pipeline vs 2 VLMs, DENTEX + Ningxia + CariesXrays | constant ties/beats the crop-classifier pipeline externally | `RESULTS_LOG` 2026-08/09, 2026-10-11i |
| Lever B lesion detector, pre-registered (`ef3f453`) | met rule on 2 of 3 cohorts; adopted 4 Sep | `RESULTS_LOG` 2026-09-04h |
| Five repairs of the crop classifier | all CIs span 0 | `PAPER_MATERIAL` §8.24 |
| Stage-1 detector switch, 32-run pre-registered matrix | default changed **against** two registered verdicts | `RESULTS_LOG` 2026-10-11f/g |
| Rows N, O, P (UFBA numbering, constant placement, lesion flags by category) | UFBA 44.5% end to end | 2026-10-12b |
| Stage 4a held out; retrained by radiograph (3 seeds) | 7.6% → 27.5/16.5/11.0% sensitivity | 2026-10-13, -13b |
| Stage 4b retrained on overlap bands | not eligible (0.294 vs prior 0.334) | 2026-10-14d |
| Calibration, abstention with shuffle control | numbering + crop classifier only | `PAPER_MATERIAL` §8.15, §8.21 |
| Review round-1 analyses (HKSJ, constant stability, matched volume, DENTEX pHash) | all done from saved data | 2026-11-02d |
| Lever C arch-order post-processor; Option B positional shift | both null | 2026-09-06, -06b |

## 6. Missing experiments

| Missing | Why it matters | Status |
|---|---|---|
| Ningxia per-tooth-type comparison (round-1 item 1) | the RQ2 "better flags within type" claim is DENTEX-only | blocked: raw images not attached; frozen-pipeline re-run, no training |
| Learned position-only floor, content ablation, site-ID probe (item 10) | would strengthen the shortcut argument | not pre-registered; new compute |
| Lesion-detector calibration / abstention | RQ3 covers numbering and the *retired* classifier only | refused by councils for this paper (unmatched flags not known FPs) |
| Any periodontal-label experiment (BRAR, Ningxia periodontitis split) | the project title promises periodontal disease detection | not run; Ningxia split locked by house rule |
| Stage 3b test | grades shown to users have no test | no test set can be built from data on hand |
| Clinician comparison / reader study | needed for any clinical-utility claim | never run |
| Tufts box-mAP re-measurement of the switch; numbering error taxonomy under the current front end | completeness | parked |

## 7. Documentation conflicts and outdated results (found this session)

| # | Where | What it says | What is true | Severity |
|---|---|---|---|---|
| D1 | root `README.md` badge | "tests 197 passing" | 210 pass + 3 skip = 213 on this clone | low |
| D2 | root `README.md` START HERE | "This page's own figures … still describe the previous front end" | still true — README narrative is pre-11-Oct; self-flagged, not fixed | medium (first thing a reader meets) |
| D3 | root `README.md` | "rotate it 90° counter-clockwise" before running on non-Tufts images | `run_pipeline` calls `detect_upright`, which rotates internally; the warning applies only to calling the raw YOLO model directly (the README's next sentence points to `detect_upright`, so the text is ambiguous rather than wrong). A user who pre-rotates and then calls `run_inference.py` would double-rotate | medium |
| D4 | root `README.md` | "What should I work on? → PUBLICATION_TODO.md" | `CLAUDE.md` §6 and `transfer.md` §3 say those plans are not re-synced since before 4 Sep | low |
| D5 | `paper/main.tex` (16 pp) vs `paper/paper.md` (10 pp) | two maintained manuscripts | `main.tex` lacks HKSJ, matched volume, pHash check, reference-standard limitation; still says "four hospitals" (Li et al. describe three) and cites Cao et al.'s unverifiable 61.83 | medium |
| D6 | `transfer.md` header | "Last rewritten 4 September 2026" with dated targeted updates to 2 Nov | accurate as a log of updates; §1 body still quotes "214 claims" and "213/213", superseded by 215 and 210+3 | low |
| D7 | Project title (repo, request) | "Cavity and Periodontal Disease Detection" | no stage detects periodontal disease: Stage 4's label is "overlaps an abnormality mask" (apical lesions, sclerosis, cysts) | **high for the paper title** |
| D8 | `PROJECT_OVERVIEW.html`, `docs/research/*` | 6 Sep / pre-Lever-B snapshots | bannered as snapshots; not evidence | info |

No conflict was found between `docs/results/model_metrics.md`, `transfer.md` §2 and the saved
artefacts for any number used in the paper; `verify_paper_numbers.py` and the round-1 tracer
confirm that independently.

## 8. Changes after 11 Oct 2026 (the period the prompt asked to check)

46 commits from `289139f` to `851f089`. The material ones, in order:

1. **Stage-1 detector switched** to `models/15/arm3c_best.pt` (`c139779` pre-reg, `7dd3ff4` weights,
   `8511d40` intervals). Against two registered verdicts; Tufts box mAP 0.587 vs 0.723 control.
   Consequence: DENTEX became in-domain for Stage 1; DENTEX gate-vs-constant sign reversed
   (−2.61 → +4.27 pp F1).
2. **Manuscript rebuilt** on the new front end the same night (`paper/main.tex`, 191 → 215 claims).
3. **UFBA-425 numbering** (44.5% / 77.2% widened) — first off-corpus numbering figure.
4. **Stage 4a**: held-out score 7.6% exposed the 0.923 as a split artefact; retrained by radiograph;
   seed 42 adopted (`33dd966`).
5. **Stage 4b**: found to be trained on crop contrast; withheld by default; overlap retrain not
   eligible.
6. **Hygiene**: hash-checked loads, schema 1.6, NaN guards, lock file, end-to-end test (`86bf98a`).
7. **Ten-page draft** (`paper/paper.md`), citation audit on four indexes (`2121a0b`), review round 1
   with four saved-data analyses (`517123e`, `02b63a7`, `851f089`).

**Do the README, manuscript, checkpoints, figures and results agree?** The checkpoints, figures,
`model_metrics.md`, `main.tex` and the ten-page draft agree with each other and with the artefacts
(two independent checkers). The root README does not (D1–D4) and labels itself stale. The two
manuscripts differ in scope (D5), not in any shared number.

## 9. Scientific risks

1. **Selection on a test cohort.** Ningxia informed Lever B's adoption and was re-scored under the
   detector switch; the lesion detector's Ningxia lead is optimistic by construction.
2. **In-domain development cohort.** DENTEX trained the current detector; the DENTEX headline
   (F1 0.498 vs 0.320) is not external evidence.
3. **A "cohort" that is a validation split.** CariesXrays-1,200 selected the lesion detector's
   checkpoint.
4. **Front end chosen after results.** The detector switch overrode two pre-registered guards; the
   DENTEX sign of the gate comparison depends on it.
5. **Label validity.** Panoramic-only caries labels; Stage 4's label is not periodontal; Stage 4b
   was contrast; annotation exhaustiveness undocumented (unmatched flags are not known false
   positives); no healthy-tooth labels in the scored DENTEX images.
6. **Single runs** for every model except Stage 4a (three seeds, 11.0–27.5% — the operating point
   moves with the seed). Two machines gave 0.294 vs 0.300 on one row.
7. **Licences**: Kaggle set unstated (in the default detector); DENTEX share-alike for figures;
   Tufts redistribution breach unresolved.

## 10. Publication readiness (summary; full version in `publication_readiness.md`)

The evidence supports a **methodological paper about evaluating tooth-level caries scores**, with
the pipeline as the vehicle, and does **not** support a paper claiming an accurate, clinically
useful caries-and-periodontal detection system. Blocking items are author inputs (names, CPU model,
availability statement), licence questions, and a venue with a matching page limit — not new
experiments.
