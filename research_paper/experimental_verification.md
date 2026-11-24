# Experimental verification

Phase 7 deliverable. What was re-checked this session, how, and what each check found. No model was
trained, tuned or re-scored on any cohort; every check below reads saved artefacts or code.

## 1. Re-run checks (23 Nov 2026, Windows clone, `C:\venvs\dental312`, Python 3.12.10)

| Check | Tool | Result | Saved |
|---|---|---|---|
| Tests | `pytest tests -q` | 210 passed, 3 skipped (need raw Tufts radiographs) | `audit_runs/checks_2026-11-23.txt` |
| Data/weight invariants (split disjointness, leakage list, pinned hashes) | `scripts/eval/verify_invariants.py` | all hold | same |
| 215 numeric claims of `paper/main.tex` against artefacts | `scripts/verify_paper_numbers.py` | 215/215, no drift | same |
| Every distinct number in the new paper (403) against `main.tex`, run files, figure-fact files and cited abstracts | `tools/trace_numbers_rp.py` | 7 untraced, each explained in §2 | console (re-runnable) |
| RCE number tracer on the tagged draft | `verify_numbers.py --project-root .` | 0 errors, 0 warnings | `.rcs/audits/gates/G3_numbers.json` |
| Evidence values present in their locator files | `tools/build_rcs.py` (fails closed) | all 45 items pass | — |

## 2. The 7 numbers the first tracer cannot find, explained

| Number | Where | Why it is correct |
|---|---|---|
| 7.2, 55.5 (and 36.5) | Section III-A | 100 − 92.8, 100 − 44.5, 100 − 63.5 from Table 1 |
| 42.6 | Abstract, VII | 203 / 477: `fn` 203 of 477 carious teeth, `D_fdi_set_f1/lesion-detector/arm3c` in `outputs/stage1_switch/stage1_switch_results.json` |
| 0.979 | II | Zancan et al. full text (F1 0.9788), recorded 2 Nov 2026 |
| 86.1 | II | Mohammad-Rahimi et al. abstract via Europe PMC, saved in `literature/abstract_mohammadrahimi_europepmc_2026-11-23.json` |
| 97.5 | III-F | percentile definition, not a result |
| 0.089 | Table 6 | interval end of the retrain row, `outputs/caries_v4/run_summary.txt` (2 Nov record) |

## 3. Protocol audit — the checklist the prompt asked for

| Risk | Finding | Evidence | Disposition in the paper |
|---|---|---|---|
| **Data leakage / duplicates** | 86 DENTEX images byte-identical to training images were removed (MD5); pHash/dHash found no further copy; one Tufts test radiograph (248) is a re-rendered copy of training radiograph 1017, holding no Stage-4a positive | `verify_invariants.py`; `outputs/review_round1/dentex_near_duplicates.json`; `RESULTS_LOG` 2026-10-14 | V Cohorts; Limitations (patient-level duplicates undetectable) |
| **Patient overlap** | No patient IDs in any public release; image-level splits only | dataset READMEs | Limitations |
| **Train/test separation** | Tufts `split_v1` code-derived and invariant-checked; one known leak (`590.JPG`/`591.JPG`) measured at −0.15 pp | `transfer.md` §2.7 | not material; stated in repo |
| **Domain confounding** | DENTEX is in-domain for the current detector; CariesXrays-1,200 is the lesion detector's validation split | `transfer.md` §2.3–2.4 | Table 4 roles; L001 |
| **Class imbalance** | Caries prevalence 0.147 at crop level; Stage 4 ~4% | `outputs/caries_position_bias/`; `PAPER_MATERIAL` §6.4 | AP and within-type AUC reported, not accuracy alone |
| **Inappropriate metrics** | Lesion agreement has no negative class and grows with flagged teeth | theory §III-C | always reported beside teeth flagged; matched-volume constant |
| **Selective reporting** | Five failed repairs, a null post-processor (Lever C), the 0.923 split artefact, the Stage-4b non-eligible retrain, the single-corpus arm's collapse are all reported | `.rcs` negative-result decisions | Table 6, VI-D, VI-F |
| **Invalid statistical conclusions** | Estimation only, no tests, no multiplicity correction claimed; DL interval supplemented by HKSJ and τ Q-profile | `F_ningxia_random_effects*.json` | V Statistics |
| **Unfair baselines** | Constant fitted on 78 non-scored images (oracle on test shown separately); VLMs zero-shot with one prompt, decoding not recorded | figure-facts JSON; `c1_vlm` | Table 5; VI-F caveat |
| **Test-set-driven model selection** | (a) Ningxia informed Lever B adoption; (b) the Stage-1 default was chosen after its Ningxia re-score, against two registered guards; (c) CariesXrays-1,200 selected the lesion detector checkpoint | `RESULTS_LOG` 2026-09-04h, 2026-10-11f/g | V "departures"; L002, L003; "optimistic by construction" |

## 4. Does the constant-baseline comparison survive the detector change?

Yes for the external cohorts, no for the development cohort, and the paper reports the current one:

| Comparison | Previous detector | Current detector | Verdict |
|---|---|---|---|
| DENTEX, crop classifier − constant, F1 | −2.61 pp, not separable | +4.27 [+1.58, +7.05]; against a constant restricted to detected molars +0.41 [−2.24, +3.14] | **reversed against the naive constant, level against the restricted one** |
| Ningxia pooled, crop classifier − constant, agreement | +0.79 pp | +0.89 [−3.86, +5.57] | unchanged: level |
| CariesXrays, crop classifier − constant | −24.44 pp | −22.42 [−24.62, −20.18] | unchanged: constant wins |
| Lesion detector − constant, Ningxia | +10.2 [+6.3, +14.0] | +9.28 [+4.72, +13.73] | unchanged in size |

Every column rose with the new front end, the constant's included (it is placed by Stages 1–2),
so the rises are mostly the front end (`transfer.md` §2.4).

## 5. Per-stage metrics against the prompt's list

| Area | Requested metric | Available | Not available (why) |
|---|---|---|---|
| Detection | precision/recall, mAP | recall (Tufts 89.3%, UFBA 66.6%), box mAP@0.5 Tufts test 0.587 | precision on unseen corpora (not measured) |
| Numbering | accuracy, missing/overlap errors, cross-dataset | Table 1; error taxonomy (adjacent-tooth 81.0%, quadrant 0.6%) | taxonomy for Tufts/UFBA under current front end (parked) |
| Caries | P/R/F1, ROC-AUC/PR-AUC, FP/FN, tooth vs image | tooth-level P/R/F1; crop AP 0.550, within-type AUC 0.745; FP/FN counts on DENTEX | image-level metrics (not computed); lesion-detector calibration (not well defined on unexhaustive labels) |
| Bone loss | detection, severity, agreement, measurement error | Stage 4a sensitivity/specificity, 3 seeds; Stage 4b macro-F1 vs prior | **any periodontal measure** — no bone-level label exists in the project |
| Integrated | end-to-end, error propagation, baselines, ablation, cross-domain, calibration, abstention, efficiency | identity chain (Table 1), constant/VLM ladder, five-repair ablation, three cohorts + four sites, ECE, shuffle-controlled abstention, 1.70 s/image CPU, 95.34 M params | clinician comparison; GPU latency; memory |

## 5b. Analyses run in response to review (23 Nov 2026)

`tools/detected_constant.py` (post hoc, DENTEX 164, CPU, no training): a constant restricted to the
detected molars scores F1 0.358; the crop classifier is not separable from it (+0.41 [−2.24, +3.14]);
the lesion detector leads (+13.94 [+9.63, +18.15]). DENTEX caries annotations outline whole teeth
(median box ratio 0.907). A rerun on this machine differs from the saved macOS run on 12 of 164
images (F1 0.490 vs 0.498): **the pipeline is not bit-reproducible across the two machines.** The
paper's tables keep the saved run and report both.

After revision the tracer reads 442 distinct numbers; 10 are not matched literally: the 7 above, two
roundings of new JSON values (0.2591 → 0.259, 0.5807 → 0.581), and two record references (117 papers,
`PAPER_MATERIAL.md` §2.1; radiograph 1017, `transfer.md` §1). RCE's `verify_numbers.py`: 0 errors,
1 warning ("ISO 3950", a standard's name).

## 6. Experiments proposed, not run (status accurate)

| Experiment | Why | Cost / blocker | Status |
|---|---|---|---|
| Ningxia per-tooth-type re-run of the frozen pipeline | makes the RQ2 within-type claim external | CPU hours; needs `D:\nangxia_dataset` attached | **blocked** (drive absent); no training, no tuning, so allowed under the house rule as inference only |
| Learned position-only floor + content ablation + site-ID probe | tests whether learned priors exceed the closed-form constant | GPU-light; needs pre-registration | proposed |
| Lesion-detector calibration on a labelled-healthy cohort | RQ3 for the shipped caries stage | needs a cohort with healthy-tooth labels | proposed |
| Periodontal grading on BRAR against age-only baselines | the only route to a periodontal claim | download permission; new training | proposed, journal version |
| Reader study with dentists | clinical usefulness | ethics approval, recruitment | proposed |

None was run: each either needs data not attached, new GPU work under a fresh pre-registration
(`transfer.md` §6), or human participants.
