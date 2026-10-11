# Submission to-do — re-checked against `paper/main.tex`

**Status date: 11 October 2026.** Rewritten from scratch; the 28 Aug list it replaces is in git
history (`git log -- docs/paper/SUBMISSION_TODO.md`). Every item was checked against
`paper/main.tex` as it stands — last changed 7 Sep (`fc811ca`), **14 pages** — and line numbers
below refer to that file. Tables are named by their LaTeX label; in the built PDF `tab:fdiset`
is Table IV, `tab:lesion` V, `tab:external` VI, `tab:cohorts` VII and `tab:leverb` VIII. Older
notes in this repo call `tab:fdiset` "Table I", from before the Related Work table was added. Items are marked done only with the evidence, because a list that
reopens closed work is how this project once lost a week (`CLAUDE.md` rule 4).

Nothing on this list needs a GPU. Items marked **LaTeX** need the Windows machine; this file
was written on the macOS clone, which cannot build the paper.

---

## 1. The decision everything else waits on — which tooth detector the paper reports

On 11 Oct the pipeline's Stage-1 default changed from the Tufts-only seg detector to a
multi-corpus detector, by a decision against two pre-registered ablation verdicts
(`RESULTS_LOG` 2026-10-11f, -g). `main.tex` describes the previous detector in every table.
**The choice now decides the paper's headline** (`RESULTS_LOG` 2026-10-11i): gate pipeline minus
image-blind constant, on the 164 DENTEX images,

| | Previous front end | Current front end |
|---|---|---|
| FDI-set F1 | −2.61 pp [−5.99, +0.64] — not separable | **+4.27 pp [+1.58, +7.05]** — pipeline ahead |
| Lesion agreement | −4.18 pp [−8.42, −0.21] — constant ahead | **+17.12 pp [+12.15, +21.89]** — pipeline ahead |

while on Ningxia (pooled +0.79 → +0.89 pp, not separated; test1 −19.0, test2 +12.3 pp) and on
CariesXrays (constant ahead by 22 pp) the comparison is the same either way.

| | **A — rebuild on the current front end** | **B — keep the previous front end** |
|---|---|---|
| Headline | "The constant scored highest" becomes false. The claim becomes: a pipeline that clears the floor on its development corpus still cannot be told from it at external hospitals, and clearing it took an in-domain detector, not a better caries model | Kept, on an interval that excludes zero by one lesion on this machine |
| Must be stated | The default was changed against two pre-registered verdicts; 92.8% numbering is in-domain; no cross-domain numbering figure exists | The released code's default differs from the system described, and why |
| Work | Every row of §1.1, the re-measurements of §1.2, four figures re-rendered | One paragraph, and `tab:fdiset`'s pipeline row restated from one machine |
| Paper and code agree | Yes | No |

**Owner: authors and mentor. Not an engineering call.** `PAPER_MATERIAL.md` §8.30 has the
wording rules for A.

### 1.1 Option A — what changes in `main.tex`, and from which file

All values are in `outputs/stage1_switch/stage1_switch_results.json` unless another file is
named. Both detectors were run on one machine, so no row mixes machines.

| Where (line) | Now | Under the current front end |
|---|---|---|
| Abstract (76–78) | F1 0.320 vs 0.294; lesion 0.489 vs 0.443 | Constant 0.320 vs gate pipeline 0.362 and lesion-detector pipeline 0.498; lesion agreement constant 0.630 vs gate 0.802 |
| Abstract (79–83) | "swung 26 percentage points"; "3,421 lesions … 25 percentage points" | Swing 31 points (test1 constant +19.0, test4 gate +12.4); CariesXrays is the 1,200 held-out images, 2,815 lesions, constant +22.4 — the 1,500-image sample was not re-run (§1.2) |
| Abstract (88–90) | lesion detector "beat the constant by 10.2 percentage points" | +9.28 pp [+4.72, +13.73] |
| Table `tab:stages` (382–397) | YOLOv11l-seg 27.62 M; total 97.65 M; caries path 75.29 M; gate variant 83.52 / 61.16 M | YOLOv11l multi-corpus 25.31 M; 95.34 M; 72.99 M; 81.21 / 58.85 M — `outputs/stage1_switch/H_params_arm3c/param_counts.json` |
| Speed (401) | 2.39 s per image on CPU (other machine) | 1.70 s on the macOS clone; 1.45 s there with the previous detector. State the machine |
| Table `tab:fdiset` (748–753) | Pipeline 0.235 / 0.390 / 0.294, 61.2 M | Gate pipeline 0.237 / 0.765 / 0.362 (365 / 1,172 / 112), 58.85 M; add the default: lesion-detector pipeline 0.439 / 0.574 / 0.498 (274 / 350 / 203), 72.99 M |
| Table `tab:lesion` (780–783) | Constant 0.489 (859 flagged); pipeline 0.443 (755); all teeth 0.722 (3,344) | Constant 0.630 (988); gate pipeline 0.802 (1,439); lesion detector 0.595 (603); all teeth 0.998 (4,132). Match rates: each run's `lesion_localization.json` under `C_dentex_*_arm3c/` |
| Table `tab:external` (813–817) | test1 0.288 / 0.446; test2 0.513 / 0.407; test3 0.401 / 0.377; test4 0.419 / 0.323; pooled 0.408 / 0.399 | Pipeline / constant: test1 0.519 / 0.709 (+19.0); test2 0.702 / 0.579 (−12.3); test3 0.512 / 0.494 (−1.9); test4 0.624 / 0.500 (−12.4); pooled 0.600 / 0.591 (−0.89 [−5.57, +3.86]) |
| Table `tab:cohorts` (861–863) | DENTEX +4.6 [+0.6, +8.9]; Ningxia −0.9 [−4.9, +3.0]; CariesXrays 3,421 lesions +25.2 [+23.2, +27.3] | Constant − pipeline: DENTEX **−17.12 [−21.89, −12.15]**; Ningxia −0.89 [−5.57, +3.86]; CariesXrays 2,815 lesions +22.42 [+20.18, +24.62] |
| Table `tab:leverb` (919–921) | Gate / constant / lesion: 0.443 / 0.489 / 0.455; 0.317 / 0.562 / 0.684; 0.408 / 0.399 / 0.500 | 0.802 / 0.630 / 0.595, −3.55 [−10.11, +2.64]; 0.379 / 0.604 / 0.757, +15.38 [+12.96, +17.73]; 0.600 / 0.591 / 0.684, +9.28 [+4.72, +13.73]. Label the 4 Sep adoption evidence as the previous front end's |
| Numbering (982–987) | 58.3% (546 / 936) [53.9, 62.8]; 29.4% never detected; 82.6% of 661 | 92.8% (869 / 936) [90.6, 94.9], **in-domain**; 4 of 936 never detected; 93.2% of 932. Add Tufts: 63.5% [59.3, 67.5], against 64.8% before, not separable |
| Capabilities list (1239–1240), Limitations (1368–1370) | 82.6% of detected, 70.6% bound, 0.810 box mAP | 93.2% and 99.6% on DENTEX; Tufts box mAP@0.5 **0.585**, below both pre-registered guards |
| Periodontal (1129–1135) | Fires on 0.7% of DENTEX teeth; external pooled 2.4% [2.0, 2.9] | External pooled 2.17% [1.75, 2.62] (153 of 7,049). The 0.7% and the per-site intervals were not re-measured (§1.2) |
| Discussion (1170), Conclusion (1397) | "an image-blind constant outscored a purpose-built …"; "outscored a six-stage pipeline and two vision–language models under two unrelated metrics" | No longer true on DENTEX. Rewrite around the external result |
| "What we propose" (1289–1290) | "our four systems span 0.149 to 0.320 with the least informed at the top" | Five systems, 0.149 to 0.498, with the constant third |

### 1.2 Option A — not yet measured under the current front end

All CPU, all from scripts that exist. None was part of the 11 Oct matrix.

| What the paper reports | Where | Needs |
|---|---|---|
| Stage-2 failure taxonomy: 546 correct, 275 undetected, 89 off-by-one … | `fig:stage2`, lines 976–987 | `stage2_failure_taxonomy.py` on `outputs/stage1_switch/B_dentex_arm3c/` |
| Coverage–accuracy for numbering, and "75% of 70.6% = 53.0%" | `fig:coverage`, lines 1047–1074 | `c4_coverage_accuracy.py` with the current detector; the 0.30 threshold stays as registered |
| CariesXrays on the 1,500-image sample, 3,421 lesions | Abstract, `tab:cohorts` | Either re-run the constant and the gate on that sample, or move the row to the 1,200 held-out images, which the matrix covers |
| Stage-4 firing rate on DENTEX, 0.7% | line 1130 | One pass of `bone_loss_eval.py` |
| Stage-4 per-hospital intervals | lines 1133–1134 | A per-split loop over `G_ningxia_stage4_arm3c/`; no inference |
| Tufts box mAP of the current detector | lines 1368, 507-area tables | 0.585 was measured on the training box on 3 Sep and not since |
| Figures `fig_baselines`, `fig_stage2`, `fig_coverage`, `fig_boneloss` | rendered at build time | Re-point the figure scripts at the new artefacts |
| `outputs/param_counts/param_counts.json` and `verify_paper_numbers.py` | 127 asserted numbers | Move together with the manuscript, never one without the other |

---

## 2. Blocking whichever front end is chosen

| # | Item | Evidence in `main.tex` | Owner |
|---|---|---|---|
| 1 | **Authors and affiliations** | `Unknown` at lines 49–53 | Authors |
| 2 | **Mandatory statements — none is present.** Ethics; data availability with licences; code availability; funding; conflict of interest; author contributions; acknowledgments with the AI-use disclosure IEEE requires | No match for any of them | Authors — **LaTeX** |
| 3 | **Bone-loss branch: cut it, or keep it re-described.** Three statements are false as written: "Splits are image-level throughout" (458); 700/150/150 given as its split (468, 492); "domain shift" / "did not transfer" as the reading of the external result (104, 217, 1116, 1235, 1250–1251, 1336, 1406, 1411). `PAPER_MATERIAL.md` §8.28 | Present | Authors and mentor |
| 4 | **"No image-blind baseline in any of the 49 papers"** (181–182, 326). The review sheet has no such field; this was never counted. Soften to an observation, or count | Present | Authors |
| 5 | **Three statements against their intervals** (`PAPER_MATERIAL.md` §8.29): "scored highest" / "outscored" (76, 1107, 1170, 1397) — the constant and the gate pipeline are not separable on F1 even on the previous front end; "It replicates on the one cohort that is genuinely external" (949) — true pooled, not at test1; Table `tab:fdiset` has no row for the lesion detector, the system the pipeline ships | Present | Authors — **LaTeX** |
| 6 | **Reviewer-risk edits.** The Conclusion (1389–1418) never mentions the lesion detector. "The radiograph is never read" (605) is untrue of the localisation tables, where the constant's teeth are placed with the pipeline's own boxes and codes. Table `tab:fdiset`'s pipeline row (0.294) is from the other machine; this one gives 0.300 | Present | Authors — **LaTeX** |
| 7 | **Venue and length.** 14 pages against venues that cap or charge. Department guidelines and the grade table: `transfer.md` §5. NCC 2027 closes 16 Oct at six pages, double-blind; CONECCT 2027 was read as 15 Dec | — | Authors and mentor |
| 8 | **Compliance, account owner.** A Tufts Drive folder opens without signing in (re-checked 10 Oct) — a live licence breach. SDH `metadata/index.csv` sits beside `images/`, voiding that copy's de-identification. IRB not started. Tufts pixels in seven tracked notebooks, before the repo is ever public | `transfer.md` §4 | Account owner |
| 9 | **The Kaggle "dual-labeled" licence** — only if §1 goes to A. The current detector was trained on that set and its authors state no licence. A detector trained without it already exists (`models/13`, Tufts + DENTEX), but adopting it is a new decision with its own record | `data/README.md` | Authors |

---

## 3. Not blocking

| Item | State |
|---|---|
| Title | Unchanged: "What a Tooth-Level Score Cannot Tell You". Under option A it may no longer fit |
| Abstract form | Narrative by an earlier instruction; a medical journal will want it structured. A team call |
| One research question and 2–4 hypotheses in the Introduction | Implied, not stated |
| References | 27 cited, 83 in `source.bib`. Thin on calibration, selective prediction and reporting guidelines |
| "external validation" → "external testing" | 8 occurrences, 0 of the replacement |
| Terms defined at first use | FDI, mAP, ECE and coverage are not all defined |
| Dataset-flow diagram | Absent; the dataset table exists |
| Similarity check | Internal check done (`scripts/check_text_reuse.py`); the institutional one is pending |
| University-format and venue-format copies | Not made |

---

## 4. Done — do not reopen

| Item | Evidence |
|---|---|
| Dataset table | `tab:data`, line 455 |
| Clinical interpretation section | line 1303 |
| DENTEX and Ningxia licences | recorded 4 Sep, `transfer.md` §2.7 |
| Broken DOIs | resolved 2 Sep, `outputs/citation_audit/` |
| Citation audit | `scripts/audit_citations.py`; seven errors found and fixed |
| Confidence intervals, including Ningxia periodontitis and detection quality | `model_metrics.md` "Confidence intervals"; `RESULTS_LOG` 2026-09-04l |
| Lever B folded into the manuscript | 4 Sep, `RESULTS_LOG` 2026-09-04i |
| Interval on the headline F1 gap; Lever B per hospital; the lesion detector on the `tab:fdiset` metric | Measured 11 Oct, `RESULTS_LOG` 2026-10-11. **Measured, not yet in `main.tex`** — item 5 above |
| "Reproduce the periodontal experiment" | Closed as moot: the figure reproduces, and it is not a held-out estimate of a periodontal label (`RESULTS_LOG` 2026-10-10). Do not finish the 565-crop pull |
| Stage-4 wording in the report and the demo | Report schema 1.2, `RESULTS_LOG` 2026-10-11b |
| The pipeline under the current front end, with intervals | `RESULTS_LOG` 2026-10-11g, -h, -i |

---

## 5. The one item that most changes the grade

**A reader study.** The protocol is written and runnable the day IRB clears: 100 images, two or
three dentists, the same scorer as every machine arm, the constant included. Without it the
paper rests on methodology against modest numbers. IRB is the longest lead time of anything
open, and it has not been started.
