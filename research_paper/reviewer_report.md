# Independent review — reports, and the disposition of every required correction

## Provenance (read first)

Three reviewer perspectives and one integrity VERIFIER, each run as a **separate Claude subagent in
its own context** on 23 Nov 2026. Each saw the manuscript (`paper_clean.md` / PDF, version v1) and
the repository's saved artefacts, and was told not to read the author's own assessment files. They
are **not independent human referees** and do not endorse the paper; one model family wrote the
paper and played the reviewers. Full reports: `review/reviewer_A.md` (medical imaging and computer
vision), `review/reviewer_B.md` (dental and clinical validity), `review/reviewer_C.md` (methodology
and scientific integrity), `.rcs/audits/integrity/pre/verifier_report.json` (RCE GI, round 1).

| Reviewer | Recommendation | Verified on their own |
|---|---|---|
| A — imaging / CV | **Major revision** | 26 numbers against artefacts, all match |
| B — dental / clinical | **Major revision** | label definitions, report code, clinical wording |
| C — methodology / integrity | **Major revision** | Eq. 1–3 and the prefix argument correct; meta-analysis recomputed exactly |
| VERIFIER (GI round 1) | **Blocked**: M1 CLEAR, M3 CLEAR, M2 INSUFFICIENT_EVIDENCE, M4–M7 SUSPECTED | ~90 numbers spot-checked; 24 citation rows, 19 supported, 5 not checkable, 0 unsupported |

## Consensus findings (raised by two or more)

1. **Selection on Ningxia was not disclosed for the tooth detector** (C1, A7, VERIFIER M4). Verified:
   `RESULTS_LOG` 2026-10-11f/g — chosen after its Ningxia gate-path result (0.407 → 0.600) was known;
   caries images scored in 20 full passes by then. **Fixed:** abstract, Table 3 (row and lead-in),
   Table 4, Section V, VI-A, contribution 4.
2. **The F1-optimal rule is prior work** (A9, C2). Verified: Lipton, Elkan & Naryanaswamy 2014 (ECML
   PKDD, doi 10.1007/978-3-662-44851-9_15), abstract: "the optimal threshold is half the optimal F1
   score". **Fixed:** cited at Eq. 3, in the abstract and contribution 1, reframed as an application.
3. **Post-hoc analysis presented as confirmed predictions** (C10, C12, VERIFIER M7). **Fixed:**
   abstract ("examine, with a post-hoc analysis"), Section I (frame, not predictions), III-E
   ("consistent with reading, not proof"), VI-D, Table 8 verdicts rewritten.
4. **"78 held-out radiographs" is wrong** (A3, C8). **Fixed** in the abstract.
5. **External lead reported without its random-effects interval in the abstract/conclusion** (A8, C3).
   **Fixed.**
6. **"Healthy" means "not annotated as carious"; alternative explanations of the shortcut test**
   (A5, B3, C6). **Fixed:** III-D, Table 2 header, Table 8; pooled AUC 0.855 added; per-type AUCs on
   8 and 5 positives flagged as having no interval.
7. **"Fewer, better flags" is not volume-controlled** (A4, C5). **Fixed:** VI-D and Table 8 now say so
   (447 vs 1,023 flagged molars).
8. **The 936 DENTEX teeth are annotated teeth, not the whole dentition** (A6, B7). **Fixed** in Tables 1 and 4 and VI-E.
9. **Stage 4a predictive value missing** (A15, B5). **Fixed:** PPV 0.25–0.29, 0.36–1.06 false flags
   per radiograph, 6.1% DENTEX firing (`models/18/run_summary.txt`, `stage1_switch_results.json`).

## Disposition of every required correction

Status: **fixed** (where), **measured** (new analysis), **declined** (reason), **deferred**
(open_issues), **author** (needs the authors).

### Reviewer A
| # | Sev. | Item | Status |
|---|---|---|---|
| 1 | CRIT | Constant restricted to detected molars | **measured — reviewer right**: F1 0.358; crop classifier − it +0.41 [−2.24, +3.14], not separable; lesion detector +13.94 [+9.63, +18.15]. Abstract, VI-B, Table 5, VII, IX revised (§4) |
| 2 | CRIT | "Floor moves with cohort" confounded with front end | **fixed** III-C (0.399 → 0.591 with the detector alone), Table 8 row 2 "confounded with the front end" |
| 3 | MAJ | "78 held-out" | fixed, abstract |
| 4 | MAJ | Lesion detector can learn arch position; per-type precision at different volumes | fixed III-E, VI-D, Table 8 |
| 5 | MAJ | Image confounders; pooled AUC; per-type intervals | fixed III-D (pooled 0.855; few-positive caveat) |
| 6 | MAJ | 936 = annotated teeth | **fixed** Table 1 caption, Table 4, VI-E (about six labelled teeth per image) |
| 7 | MAJ | Tufts 248/1017 pair; image vs patient splits; Ningxia known at detector choice | fixed V |
| 8 | MAJ | RE and HKSJ beside +9.28 in abstract | fixed |
| 9 | MAJ | Cite Lipton 2014 | fixed |
| 10 | MAJ | Majority-class accuracy 0.853 beside 0.797 | fixed VI-E (balanced-metric re-analysis **declined**: per-crop labels are not saved beside the coverage curve; stated instead) |
| 11 | MAJ | VLM few-shot results; one prompt | fixed VI-B (7B 2-shot 0.066, 4-shot 0.034; `outputs/c1_vlm/c1_comparison.json`) |
| 12 | MAJ | "40 points across cohorts" mixes matching rules | fixed VII RQ1 |
| 13 | MAJ | [ASK AUTHOR] items | **author** (open_issues 1–5) |
| 14 | MIN | All Stage-4b seeds | fixed VI-F, Table 3 (0.294 / 0.328 / 0.382; old head 0.366 not added — the old head is not in the paper) |
| 15 | MIN | AUC/AP/PPV for Stage 4a | PPV fixed; ROC 0.684–0.687 kept in the record, not added (space) |
| 16 | MIN | UFBA widened row qualifier | **declined for the table**; the caption already says "widened to a panoramic shape" and Section III-A calls the as-distributed figure the registered one |
| 17 | MIN | Centroid in two boxes; ECE binning | **deferred** — the tie rule is in `scripts/eval/lesion_localization.py`; not restated for space |
| 18 | MIN | Variances from width/3.92; three hospitals | fixed III-F |
| 19 | MIN | n of the 0.85 → 0.26 calibration bin | **deferred** (bin count is in Fig. 8d marker area) |
| 20 | MIN | 92.0% is Tufts, add reach 81.7% | fixed III-C |

### Reviewer B
| # | Sev. | Item | Status |
|---|---|---|---|
| 1 | CRIT | DENTEX caries annotations outline whole teeth | **measured — reviewer right**: median annotation box 0.907 of the tooth box, IoU 0.814, 99.6% above 0.5. III-C, V, VI-B, Table 4, Fig. 1/7 captions revised (§4) |
| 2 | CRIT | Stage-3b grade untested; tooth-36 example | fixed IV (grade "unvalidated"; tooth 36 unannotated). Changing the shipped default to withhold the grade is a code change **not made** without the owner's approval — recommended in open_issues |
| 3 | MAJ | "Truly healthy"; alternatives; "consistent with" | fixed |
| 4 | MAJ | JSON field still named `bone_loss` | fixed IV (disclosed) |
| 5 | MAJ | Stage 4a predictive value; drop "normal Stage-4 finding" | fixed |
| 6 | MAJ | External miss rate, misnumbering, over-treatment | fixed VII (31.6% = 1 − 0.684) |
| 7 | MAJ | 936 = annotated teeth | **fixed** (as A6) |
| 8 | MAJ | Intended-use and scope statement | fixed VII |
| 9 | MAJ | Reference standard per cohort; move bitewing caveat | fixed I and V (readers and exhaustiveness "not stated in what we used") |
| 10 | MIN | 46 also unannotated | fixed Fig. 4 caption |
| 11 | MIN | 0.8892 is a detection score | fixed IV |
| 12 | MIN | "Pre-registered" needs a public anchor | fixed: "committed to the (private) repository"; anchor = **author** |
| 13 | MIN | FDI / ISO 3950; panoramic pitfalls | fixed I |
| 14 | MIN | 1.70 s measured with 4b computed | fixed IV (measured 11 Oct, before the 14 Oct withholding) |
| 15 | MIN | State that the periodontal aim was not achieved | fixed I |
| 16 | MIN | Placeholders, Kaggle licence | **author** |

### Reviewer C
| # | Sev. | Item | Status |
|---|---|---|---|
| 1 | CRIT | Ningxia informed Stage-1 choice | fixed (consensus 1) |
| 2 | MAJ | Lipton 2014 | fixed |
| 3 | MAJ | Abstract/conclusion intervals; DENTEX tie | fixed (tie and 0.802 vs 0.595 remain in VI-B and Table 7; not added to the abstract for length) |
| 4 | MAJ | Rule counted the validation split; better arm chosen | fixed V and VI-D |
| 5 | MAJ | Operating-point control; "no tooth identity" | fixed III-E, VI-D |
| 6 | MAJ | Alternative explanations; per-type intervals | fixed III-D |
| 7 | MAJ | Lead attributable to mixture | fixed contribution 3, VI-D |
| 8 | MAJ | "78 held-out" | fixed |
| 9 | MAJ | Per-site multiplicity; three hospitals | fixed VI-D, III-F |
| 10 | MAJ | Section I "can" vs Table 8 "not specific" | fixed I |
| 11 | MIN | Drop "ceiling not set by supervision" | fixed VI-D (also VERIFIER M5) |
| 12 | MIN | Rule (3) row is an identity | fixed Table 8, VII |
| 13 | MIN | "Treats codes independently" inaccurate | fixed VIII |
| 14 | MIN | Truncated HKSJ | fixed VI-D ([−6.88, +26.09], already in the saved file) |
| 15 | MIN | Majority-class accuracy; calibration fit/test | fixed VI-E |
| 16 | MIN | Interval widths for "no image information"; VLM decoding | fixed VI-B; decoding settings = **author** (not recorded) |
| 17 | MIN | Citation fixes (Kelly, Zech, Batchelor, van Nistelrooij, Cerda) | fixed II, III-B, III-C, VII |
| 18 | MIN | Fig. 5 is curves, not images of outputs | fixed VII |
| 19 | MIN | Describe the 49-paper review | fixed I (structured review of 117, 49 task-relevant, observation not a count) |
| 20 | MIN | CariesXrays and Ningxia may share a site | fixed VIII ("could not verify") |

### VERIFIER (GI round 1)
| Mode | Finding | Status |
|---|---|---|
| M2 | Some numeric literature claims have no saved quote (Bizjak, Zancan, Li 2024, Cerda provenance, Batchelor) | Bizjak and Zancan were checked against full text on 2 Nov (`outputs/citation_audit/2026-11-02_ars/README.md`); Cerda provenance and Batchelor wording **fixed**; Li 2024 "three hospitals" rests on the 2 Nov full-text read |
| M3 | E018 pointed at the wrong arm's file | **fixed** (`acceptance_rule_B-pooled.json`) |
| M4 | Undisclosed Ningxia selection | **fixed** |
| M5 | "Ceiling not set by supervision"; 32B answered NONE to blank | **fixed** |
| M6 | Rule "before any arm"; "all splits image-level"; "two of its own guards"; 1.5× wording | first three **fixed**; the 1.5× wording is **kept**: `outputs/lever_b_eval/acceptance_rule_B-pooled.json` checks the rate ratio against both comparators (`rate_ratio_le_1.5x` for constant and pipeline) |
| M7 | Post-hoc theory framed as predictions | **fixed** |
| Record | `models/16/run_summary.txt` says best epoch 54, `results.csv` says 29 | the paper uses 29 (from `results.csv`); the run summary's error is a repository record defect, logged in open_issues |

## 4. Analyses run in response (post hoc, development data only)

Script `tools/detected_constant.py`; output `audit_runs/review_round_analyses.json`; per-image rerun
`audit_runs/dentex_rerun_windows_2026-11-23.json`. Shipped default pipeline, CPU, this Windows clone;
10,000 image resamples, seed 42; no training or tuning; DENTEX only.

| Question | Result |
|---|---|
| A-1: constant restricted to detected molars | P 0.259, R 0.581, **F1 0.358** (1,069 codes); vs unrestricted +3.86 [+2.83, +4.90] |
| crop-classifier pipeline − restricted constant | **+0.41 [−2.24, +3.14]: not separable** (the +4.27 lead does not survive) |
| lesion-detector pipeline − restricted constant | **+13.94 [+9.63, +18.15]** (saved run); +13.12 [+8.84, +17.36] (rerun) |
| B-1: DENTEX caries polygon box / tooth box | median 0.907 (P10–P90 0.728–1.145); IoU median 0.814; 99.6% > 0.5: **tooth outlines** |
| Control: rerun vs saved macOS run | **12 of 164 images** differ in lesion-detector codes (F1 0.490 vs 0.498). Run 1 stopped on this gate (`audit_runs/review_round_analyses_run1_gate_failed.json`); run 2 reports both |

The first finding changes the paper's RQ1 development-data statement: the crop classifier's F1 lead
over the image-blind floor came from a constant that names absent teeth. The paper now says so in the
abstract, VI-B, VII and IX.
