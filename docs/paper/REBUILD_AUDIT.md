# Manuscript rebuild — pre-writing audit

**Written 28 August 2026.** This document is the evidence pass that precedes the rewrite of
`paper/main.tex`. Nothing here is drawn from the existing manuscript: every number was re-read
from `outputs/*.json`, `models/*/run_summary.txt`, the DENTEX ground-truth label files, or the
checkpoint tensors themselves. Where the manuscript and the repository disagree, the repository
wins and the disagreement is recorded below rather than silently corrected.

Companion documents: `docs/results/PAPER_MATERIAL.md` (method and reasoning),
`docs/results/model_metrics.md` (current scoreboard), `docs/results/RESULTS_LOG.md` (history).

---

## Deliverable 1 — The research story, in one paragraph

Dental caries and periodontal bone loss are the two most common chronic diseases visible on a
panoramic dental radiograph, and a growing literature reports automated systems that read those
radiographs and name the affected teeth. Almost all of that work reports its result as a
tooth-level score — which teeth, out of the 32 in an adult mouth, are diseased — and almost none
of it reports what that score would be for a system that never looked at the image. This matters
because caries is not spread evenly across the mouth: it concentrates in the molars, so a fixed
list of molar codes, emitted identically for every patient, already answers the question
partially right. We built a complete six-stage panoramic pipeline (tooth detection → FDI
numbering → caries classification → periodontal bone-loss classification → fusion → report),
evaluated it on four Chinese hospitals it had never seen, and then measured the floor beneath its
own caries number by scoring it against progressively less-informed opponents under one identical
scorer: two general-purpose vision–language models, and finally a constant list of eight tooth
codes fitted on held-out images and frozen. On our 164-image development set the constant scored
highest — F1 0.320 against the pipeline's 0.294 — and a second, spatially grounded metric
returned the same ordering, so the effect is a property of the task rather than an artefact of
one metric. On the four external hospitals the comparison produced no separation at all, and the
per-site difference swung 26 points in a way the pooled figure erases. Both language models
returned confident, correctly formatted, anatomically specific tooth lists when shown pure random
noise; the larger one's answer to noise was exactly the eight-molar population prior. Meanwhile
the pipeline's periodontal branch, which scores 0.923 macro-F1 in domain, fires on 0.7 % of teeth
outside it and is reported as a measured failure. The defensible conclusion is not that automated
caries screening does not work — it is that a tooth-level score, reported without a floor, cannot
tell us whether it does; and that the things a constant provably cannot do (name a tooth, express
a calibrated confidence, decline when uncertain, be measured under domain shift) are where the
evidence for a working system actually lives.

---

## Deliverable 2 — Problem audit

Severity: **C** = critical, must fix before submission (wrong or unsupportable as written);
**H** = high (materially misleads a reader); **M** = medium (clarity, structure, presentation).

| # | Problem | Sev | Evidence | Required fix |
|---|---|---|---|---|
| 1 | Manuscript states the system "totals approximately 25 M parameters". | **C** | Counted from the checkpoints: detector 27.62 M, FDI head 11.20 M, caries gate 11.19 M, caries severity 11.19 M, bone-loss binary 11.19 M, bone-loss severity 11.19 M = **83.56 M**; caries-only path = **61.20 M**. The 25 M figure is the *superseded bbox detector alone* (`model_metrics.md`: "25.3M params"). | Replace with 83.6 M total / 61.2 M caries path. The efficiency claim survives (33.45 B ÷ 83.6 M ≈ 400×) but must be restated on the true number. |
| 2 | Manuscript names the VLMs "Qwen2.5-VL-33B" and "Qwen2.5-VL-8B". Neither model exists under that name. | **C** | `outputs/c1_vlm/arm_vlm_32b_0shot.json`: `model = Qwen/Qwen2.5-VL-32B-Instruct`, `params_billion = 33.453`. `arm_vlm_7b_0shot_rerun.json`: `Qwen/Qwen2.5-VL-7B-Instruct`, `8.292`. | Use the released names; report measured parameter counts (33.45 B, 8.29 B) as a separate column. Figure labels must be regenerated too. |
| 3 | "Presented with a blank grey image and with random noise, **both models** return confident, correctly formatted, dental-specific answers." | **C** | `control_pixels_32b.json`: `answers.blank = "NONE"`, `blank_matches_a_real_answer = false`. The 32 B model answers the blank image **correctly**. Only the 7 B model returns `26,36` to a blank. Both fail on noise. | State the two models separately. The precise result is stronger than the overstated one: the 32 B model's answer to pure noise is `16, 17, 26, 27, 36, 37, 46, 47` — *exactly* the eight-molar constant. |
| 4 | "isotonic regression reduced ECE to 0.043 … applied to confidences only, leaving every verdict byte-identical." | **C** | `caries_gate_isotonic.json`: `verdicts_flipped_at_0.5 = 155` (18 % of 863) and `average_precision: 0.550 → 0.4996`. The invariance is a *deployment choice* (verdicts stay `argmax` on raw logits), not a property of isotonic regression — which is what temperature scaling has (`decisions_unchanged_at_0.5 = true`). | Say what was actually done and what it cost: isotonic is applied to the reported confidence only; applied at the decision threshold it would flip 155/863 verdicts and drop AP to 0.500. |
| 5 | "…and **none** report a constant, image-blind, or otherwise uninformed baseline" — presented as a counted survey result. | **C** | `outputs/related_work_extract.csv` records a `Validation` design field. The 2-of-49 external-validation count **is** verifiable from it (verified independently here). Baseline reporting is **not a field in the extraction**, and no count exists anywhere in the repo. | Keep the counted claim (2/49 external, verified). Restate the baseline claim as what it is: we found no image-blind baseline reported in this literature, not a counted census. |
| 6 | Table I says "477 affected teeth", Table II says "479 annotated lesions", same images, unexplained. | **H** | Recomputed from `DENTEX/disease/label/*.json` over the 164 scored images: **479 çürük polygons** across **477 distinct (image, FDI) pairs**, because exactly two teeth carry two polygons each — `test_101` tooth 36 and `test_25` tooth 46. Both numbers are right; they are different units. | State the relationship in one sentence in the Table II caption. |
| 7 | Title "What Does 44 % Mean?" | **H** | 44.3 % = 212/479, the **pipeline's own** lesion-localisation agreement on development data. It is one row of Table II, is never written as "44 %" anywhere in the body, and is not the paper's finding — the finding is 0.488 vs 0.443 and 0.320 vs 0.294. | Replace. See Deliverable 6. |
| 8 | Bone-loss in-domain 0.923 macro-F1 reported with no caveat. | **H** | `PAPER_MATERIAL.md` §8.18: it is the **maximum of a noisy 32-epoch curve** whose diseased-class val F1 oscillates 0.40–0.85 over **59 validation positives** — selecting the best of 32 draws is optimistically biased. `RESULTS_LOG` 2026-08-27u: the figure is **not reproducible** — 773 of 1,558 val crops were built with an RNG jitter whose offsets were never saved, and the source images are off-machine; the rebuild attempt was rejected by its own geometry check (`geometry_verdict = DIVERGENT`). | Report 0.923 with both caveats attached. It strengthens the domain-shift argument rather than weakening it. |
| 9 | All four Ningxia sites described as external hospitals with no further qualification. | **H** | Every `ningxia_external.json`: `test2.centre = same_centre_as_train`; the other three are `cross_centre`. This describes **Ningxia's own** split design — we never trained on any Ningxia data, so all four are equally external to us. But test2 is the pipeline's best site (0.513) and this is exactly the kind of thing a reviewer asks about. | State it explicitly, with the "equally external to us" reasoning that `PAPER_MATERIAL.md` §8.12 already contains. |
| 10 | Periodontal bone loss appears in the system description and one results subsection, but is absent from title, abstract, introduction and contributions. | **H** | `main.tex` §III mentions "Stages 3 and 4 classify caries and periodontal bone loss"; §V-F reports the collapse. No introduction of the disease, no clinical motivation, no dataset/label description, no metric definition. | Decide and commit: it is a **second measured task reported as a negative result**. Introduce it properly (clinical relevance, what is predicted, labels, metric), keep it as a clearly-labelled secondary analysis, and name it in the title. |
| 11 | Statistical claims lack reproducible method statements. | **H** | `bootstrap_ci.json`: `n_boot = 10000`, `seed = 42`, `method = cluster bootstrap over IMAGES (percentile 95 % CI)`. None of this is in the manuscript; "paired bootstrap over images" is all it says. `c4_coverage_accuracy.json` intervals use different `n_images` per metric (151 vs 34). | Add a Statistical analysis subsection: resampling unit, count, seed, percentile method, why images and not teeth, and the two metrics `bootstrap_ci.json` explicitly does **not** cover. |
| 12 | Bibliography carries submission-blocking provenance notes. | **H** | `source.bib` lines 328/625/636 ("verify against the publisher record at proof stage") and four `% UNVERIFIED` tags on `he2016resnet`, `guo2017calibration`, `zadrozny2002isotonic`, `jocher2024yolo11` — all four are cited. | Verified in this session; see Deliverable 5. Complete the entries and delete the notes. |
| 13 | Tables compare quantities from different metric families without labelling the unit of analysis. | **M** | Table I is per-tooth-code set F1 (n = 477 teeth); Table II is per-lesion agreement (n = 479 lesions); Table III is per-lesion agreement under a *different* matcher (centroid containment, n = 1,013). Nothing in the tables says so. | Every table states dataset, task, metric, unit of analysis and n. |
| 14 | Column headers "P R F1"; no metric is defined in plain language anywhere. | **M** | `main.tex` Table I. | Spell out headers; add a Metrics subsection defining each in plain English before its formula. |
| 15 | Abstract deliberately withholds the result ("The comparison did not resolve the way we expected"). | **M** | `main.tex` abstract, and its own source comment: "deliberately withholds the outcome". | Rewrite from zero. State the problem, the system, the test, the finding, the implication. |
| 16 | Fig. 5 places macro-F1, a firing rate, and affected-tooth sensitivity on one shared y-axis. | **M** | `paper/fig_boneloss.png`; caption already concedes "Metrics necessarily differ between cohorts". | Regenerate with the in-domain bar visually separated and the metric named on each bar. |
| 17 | Introduction's worked example uses {16, 26, 36, 46}; the actual fitted constant is {16, 17, 26, 27, 36, 37, 46, 47}. | **M** | `c1_constant_arm_vlm_32b_0shot.json`, held-out entry. | Use the real eight-code constant in the example so the introduction and the result are the same object. |
| 18 | Prose style: "the floor is unusually high", "non-separability", "the metric costs to saturate", "the prior does not expect". | **M** | Throughout §I, §V, §VI. | Direct scientific register; define every term before using it. |
| 19 | Code docstring says the constant is fitted on "the 86 leakage-excluded images". | **M** | `scripts/eval/c1_constant_baseline.py:78`. The runtime label and the paper both say 78; verified — 86 excluded images, of which 78 carry ≥1 caries annotation, and `load_exemplars` keeps only those. Docstring is stale; the paper is right. | Fix the docstring (repo hygiene, not a paper change). |
| 20 | `transfer.md` states "84/84 tests pass". | **M** | `pytest tests/ -q` → **122 passed**. | Update the snapshot. |

---

## Deliverable 3 — Numerical audit

Every number that appears in the manuscript, traced to its artefact. "Repo value" is what the
artefact says today.

### 3a. Verified correct — no change

| Number in paper | Repo value | Source | Dataset / unit |
|---|---|---|---|
| Constant P 0.218, R 0.600, F1 0.320 | 0.218 / 0.5996 / **0.3197** | `c1_constant_arm_vlm_32b_0shot.json`, held-out entry | DENTEX 164 img, 477 teeth |
| Constant set = eight first/second molars | `{16,17,26,27,36,37,46,47}` | same; **independently re-derived** in this audit by re-running the greedy fit on the 78 images (exact match) | — |
| Pipeline P 0.235, R 0.390, F1 0.294 | 0.2354 / 0.3899 / 0.2936 | `c1_comparison.json` arm `pipeline` | same |
| VLM-large F1 0.246 | 0.2465 (P 0.250, R 0.2432) | `c1_constant_arm_vlm_32b_0shot.json` | same |
| VLM-small F1 0.149 | 0.1493 (P 0.2476, R 0.1069) | `c1_constant_arm_vlm_7b_0shot_rerun.json` | same |
| Oracle constant 0.330 | 0.3299, set `{16,26,36,37,46,47}` (six codes) | same file, oracle entry | same |
| 477 affected teeth | 477 | recomputed from DENTEX labels | distinct (image, FDI) pairs |
| 479 lesions | 479 | recomputed from DENTEX labels | çürük polygons |
| 148/164 images with caries | 148 | `lesion_localization.json`, all arms | — |
| Lesion agreement: constant 0.488 / pipeline 0.443 / all-teeth 0.722 | 0.4885 / 0.4426 / 0.7223 | `outputs/lesion_loc_{constant-molars,pipeline,all-teeth}/` | 479 lesions |
| Teeth flagged 859 / 755 / 3,344 | identical | same | — |
| Match rate 0.272 / 0.281 / 0.103 | 0.2724 / 0.2808 / 0.1035 | same | — |
| Δ = 4.59 pp, CI [+0.60, +8.89] | 0.4885 − 0.4426 = 4.59 pp | `ningxia_external.py:102`, `RESULTS_LOG` 2026-08-28d | paired bootstrap over images |
| External per-site 0.288 / 0.513 / 0.401 / 0.419 | identical | `ningxia_pipeline/ningxia_external.json` | 1,013 lesions, 337 images |
| External constant 0.446 / 0.407 / 0.377 / 0.323 | 0.4462 / 0.4069 / 0.3765 / 0.3226 | `ningxia_constant-molars/` | same |
| Pooled 0.408 vs 0.399, Δ −0.89 pp | 413/1013 = 0.4077; 404/1013 = 0.3988 | recomputed from the two files | same |
| 337 external images, 1,013 lesions | 134+110+40+53 = 337; 316+349+162+186 = 1,013 | same | caries subset only |
| Stage 2: 58.3 % (546/936), CI [53.9, 62.8] | `fdi_exact_of_all = 0.58333` | `stage2_segdet/stage2_summary_head.json` | 936 GT teeth, 164 images |
| 29.4 % never detected | `recall = 0.70620` → 29.38 % | same | — |
| 82.6 % of 661 detected | `fdi_exact_of_detected = 0.82602`; 546/661 | same + `stage2_failure_taxonomy.json` | — |
| 115 wrong codes, 89 off-by-one (77.4 %) | 115; 89; 89/115 = 77.4 % | `stage2_failure_taxonomy.json` | — |
| 16 of 661 quadrant errors (2.4 %) | wrong_arch 6 + mirror_lr 8 + other 2 = 16; `quadrant_correct_of_detected = 0.9758` | same | — |
| ECE 0.136 → temperature 0.152 → isotonic 0.043 | 0.1362 / 0.1521 / 0.0430 | `calibration/*.json` | 863 test crops, 14.7 % prevalence |
| Numbering 0.826 → 0.885 (+5.91 pp, CI [3.88, 7.68]) | 0.826 → 0.88508 | `c4_coverage_accuracy.json` | 661 teeth / 151 images |
| Caries gate 0.797 → 0.940 (+14.25 pp, CI [11.32, 16.63]) | 0.7972 → 0.93972 | same | 863 crops / 34 images |
| Shuffle control +0.03 / +0.00 pp | 0.03 / 0.0 | same | — |
| Threshold 0.30 → 90.8 % coverage, 0.847 accuracy | 0.9077 / 0.8467 | same | — |
| Within 0.2 pt of the 90 %-coverage point | 0.8487 at 90.0 % coverage | same | — |
| 75 % of 70.6 % = 53.0 % | 0.75 × 0.7062 = 0.5296 | derived | — |
| Few-shot 0.149 → 0.066 → 0.034; empty 56 → 123/164 | identical | `PAPER_MATERIAL.md` §8.22, arm files | — |
| Bone loss 0.923 macro-F1, sens 83.05 %, spec 99.53 %, 1,558 crops | 0.9233; 49/59 = 0.8305; 1492/1499 = 0.9953 | `PAPER_MATERIAL.md` §7.3 / `models/03/` | **see problem 8** |
| Bone loss 0.7 % DENTEX firing | 0.7 % | `PAPER_MATERIAL.md` §8.13 | 164 images |
| Bone loss 1.4–5.6 % external | 2.4 / 1.4 / 5.6 / 4.6 % | `ningxia_external_segdet/` | 6,791 affected teeth, 736 images |
| Detector swap: Stage 2 +12.0, caries +7.7, bone loss 0 | +12.0 / +7.7 / 0 | `PAPER_MATERIAL.md` §8.13 | — |
| Detection 0.810 box mAP@0.5 | 0.8100 | `models/11_yolo_seg_tufts_r1/` | Tufts test, 150 img, 3,930 inst |
| Mask 0.638 vs pre-registered 0.65 | 0.6383 | same | — |
| 2.39 s/image on CPU | `mean_latency_s = 2.386` | `arm_pipeline.json` | 164 images |
| 70 GB accelerator memory | `peak_vram_gb = 70.05` | `arm_vlm_32b_0shot.json` | — |
| Tufts 1,000 OPGs, 700/150/150 | 1,000; frozen split | `PAPER_MATERIAL.md` §3.1 | — |
| Third corpus: 915 teeth, 80.3 % vs 1.7 % | identical | `models/12_fdi_head_v3_3corpus/run_summary.txt` | — |
| 49 task-relevant papers | 49 unique titles in 84 rows | `related_work_extract.csv`, recomputed | — |
| 2 of 49 externally validated | 2 primary studies after negation handling | same, recomputed | — |

### 3b. Wrong — must change

| Number in paper | Repo value | Source | Action |
|---|---|---|---|
| "approximately 25 M parameters" (whole system) | **83.56 M** total; **61.20 M** caries path; 27.62 M detector alone | counted from the six checkpoints | Replace throughout, including the efficiency sentence in §V and the Discussion. |
| "Qwen2.5-VL-33B" | model is **Qwen2.5-VL-32B-Instruct**; 33.45 B params | `arm_vlm_32b_0shot.json` | Rename in text, tables and Fig. 1(a). |
| "Qwen2.5-VL-8B" | model is **Qwen2.5-VL-7B-Instruct**; 8.29 B params | `arm_vlm_7b_0shot_rerun.json` | Same. |
| "both models return … dental-specific answers" to blank **and** noise | 32 B answers `NONE` to blank; both fail on noise | `control_pixels_{7b,32b}.json` | Split the claim by model. |
| isotonic "leaving every verdict byte-identical" | 155/863 verdicts (18 %) flip at threshold 0.5; AP 0.550 → 0.500 | `caries_gate_isotonic.json` | Restate as a deployment choice with its measured cost. |

### 3c. Unsupported as stated

| Claim | Status | Action |
|---|---|---|
| "**none** report a constant, image-blind, or otherwise uninformed baseline" (of 49) | The extraction has no baseline field; no count exists. The *external* count (2/49) is verified. | Soften to an observation, not a census. |
| Bone-loss 0.923 presented without caveat | Documented as a noisy-curve maximum (59 val positives) and as irreproducible on this machine | Attach both caveats at first use and in Limitations. |

### 3d. Numbers the artefacts carry that the paper should add

| Number | Source | Why it belongs |
|---|---|---|
| 32 B model's answer to random noise = `16,17,26,27,36,37,46,47` | `control_pixels_32b.json` | It is *identical to the fitted constant*. The sharpest single result in the VLM analysis. |
| Caries gate AP 0.550 [0.445, 0.660] vs 0.147 prevalence | `caries_gate_calibration_test.json` | Discrimination is 3.7× chance; the failure is calibration, not ranking. Currently the paper reports only the failures. |
| Constant's fit-set F1 = 0.392 vs scored 0.320 | recomputed here | Shows the frozen constant transfers *down*, i.e. it was not overfitted to the scored set. |
| test2 = `same_centre_as_train` in Ningxia's own design | all `ningxia_external.json` | Pre-empts the obvious reviewer question about the best site. |
| 122 tests pass | `pytest tests/ -q` | Reproducibility statement. |

---

## Deliverable 4 — Paper storyboard

One narrative. Each section exists to answer the question the previous section raises.

| § | Section | What it must accomplish | Raises next |
|---|---|---|---|
| — | **Title / Abstract** | Name the disease, the data, the system, the baseline, the external test, the finding, the implication — in language that needs no prior knowledge of VLMs, FDI notation or calibration. | "What is the evaluation problem they mention?" |
| 1 | **Introduction** | (1) What an OPG is and why dentists take them; what caries and periodontal bone loss are and why missing them matters. (2) What AI is currently asked to do on these images. (3) The evaluation problem, by worked example: a program that always answers `16,17,26,27,36,37,46,47` scores respectably without reading anything. (4) Why that matters — a score is not evidence of perception. (5) What we did. (6) Why external validation is part of it. (7) Contributions. | "Has nobody checked this?" |
| 2 | **Related work** | Detection/classification on OPGs; tooth numbering and why pre-cropped accuracy is not end-to-end accuracy; VLMs in dentistry and why fluency is not evidence; external validation — 2 of 49, counted — and the absent floor. | "So what did you build?" |
| 3 | **System** | The six stages in one paragraph and one diagram; per-stage model and size (83.6 M total, honestly); what each stage outputs. Both diseases introduced here, with the periodontal branch flagged as a second task whose result is negative. | "What data, and how was it split?" |
| 4 | **Data** | Table: every corpus — images, teeth/lesions, labels, purpose, split, external?, used for baseline fitting? Leakage: how the 86 excluded and 78 fit images relate to the 164 scored; how overlap was established rather than asserted. Ningxia as locked external data, including the test2 note. | "How did you test it?" |
| 5 | **Evaluation protocol** | The ladder (four systems, one scorer). Fairness — every affordance favours the opponent. Constant construction, in plain words. VLM setup: which models, what prompt, how parsed, what they were told. Metrics, each defined in English before symbols, with its limitation. Controls: blank, noise, shuffle, flag-everything. Statistics: cluster bootstrap over images, 10,000 resamples, seed 42, percentile CIs, and what is *not* covered. | "What happened?" |
| 6 | **Results** | 6.1 development-set ladder → 6.2 the second metric agrees → 6.3 external, per site, no replication → 6.4 numbering → 6.5 calibration → 6.6 selective prediction → 6.7 VLM behaviour and controls → 6.8 periodontal branch under domain shift. Results only; interpretation deferred. | "What does that mean?" |
| 7 | **Discussion** | Main finding; why the floor is high (epidemiology, not model failure); why the external disagreement changes the reading; what still separates a system from a prior; what failed; what future papers should report; clinical interpretation, carefully bounded. No repetition of the results. | "What can't they claim?" |
| 8 | **Limitations** | Twelve items, each stating what it prevents us from concluding. | — |
| 9 | **Conclusion** | Six sentences, exactly the evidence, no more. | — |

---

## Deliverable 5 — Citation audit

All 26 cited entries. Placement re-checked with `scripts/audit_citations.py`; metadata
re-verified this session where a warning was attached.

| Key | Claim it supports | Correct? | Action |
|---|---|---|---|
| `lim2024dual`, `chen2024cariesxrays`, `bilal2024pdcnet` | caries/periodontal screening is an active field; dual-network, feature-pyramid, dedicated-CNN approaches | yes | keep |
| `mutlu2026comparison` | YOLOv11 vs YOLOv12 head-to-head on dental panoramics; weaker on radiolucent pathology | yes — verified, Odontology 2026, doi 10.1007/s10266-026-01333-3 | keep |
| `asif2026yolo26`, `nassiri2025yolo`, `eftimie2025tooth` | YOLO-family detectors widely applied to this data | yes | keep |
| `chen2023deep`, `alharbi2023detection` | broader detection/segmentation work | yes | keep |
| `zancan2025ai` | tooth numbering reported at 0.9988 | yes | keep |
| `zhang2025reliable` | multi-stage segmentation-and-numbering pipelines report comparable figures | yes | keep |
| `meng2026dentvlm`, `jha2026dentiask`, `li2026pandent`, `hao2025mmoral` | VLMs applied to dental imaging | yes | keep; **`meng2026dentvlm` now verified** — Nature Communications **17**, article **8933**, 2026; full author list confirmed against the Crossref record. Delete the "verify at proof stage" note. |
| `geirhos2020shortcut` | the content-free-input control comes from shortcut-learning work | yes | keep |
| `cao2024dpml` | 95.06 → 61.83 mAP in/out of domain | yes (bib note correctly flags this is object *recognition*, not caries) | keep |
| `cerda2024determining` | periodontal bone loss vs five clinicians, weighted F1 0.29, severe-class F1 0 | yes | keep |
| `jocher2024yolo11` | YOLOv11l architecture | yes | **complete**: software citation, add version and access date; drop `% UNVERIFIED` |
| `he2016resnet` | ResNet18 backbone | yes | **verified**: CVPR 2016, pp. 770–778, **doi 10.1109/CVPR.2016.90**; drop `% UNVERIFIED` |
| `kuhn1955hungarian` | Hungarian assignment | yes | keep |
| `panetta2022tufts` | Tufts Dental Database | yes | keep |
| `hamamci2023dentex` | DENTEX | yes | keep |
| `bai2025qwen25vl` | Qwen2.5-VL models | yes | keep — but the *body text* must use the released model names (problem 2) |
| `guo2017calibration` | temperature scaling | yes | **verified**: ICML 2017, PMLR **70**:1321–1330 (no DOI issued); drop `% UNVERIFIED` |
| `zadrozny2002isotonic` | isotonic regression for probability estimates | yes | **verified**: KDD 2002, pp. 694–699, **doi 10.1145/775047.775151**; drop `% UNVERIFIED` |

**Placement.** All 21 `\cite` commands sit immediately after the claim they support; no
end-of-paragraph dumping. No key is missing from the bib.

**Gaps to fill.** The rebuilt manuscript needs clinical grounding it currently lacks
(problem 10, ACTION 28) and methodological support for the evaluation argument. The bib already
holds **56 verified but uncited entries** — draw from those rather than adding new ones. Needed:
caries and periodontal disease prevalence/burden; panoramic radiography's role and limits;
external-validation and reporting-guideline methodology; patient-level splitting and leakage;
selective prediction. Where the existing pool has no suitable entry, add one and verify it —
never cite to fill a slot.

**One defect in an uncited entry**, recorded so it is not inherited later: `kong2024integrating`
carries `journal = {Bioengineering}, volume = {11}, number = {12}, pages = {1192}` alongside
`doi = {10.1007/978-3-032-09513-8_53}`, which is a Springer book-chapter DOI. The two cannot both
be right. Not cited, so not blocking; fix or drop before it is ever used.

---

## Deliverable 6 — Title options

The current title, **"What Does 44 % Mean? Constant Baselines for Tooth-Level Caries Evaluation
on Panoramic Radiographs"**, fails on four counts: 44 % is the pipeline's own lesion-localisation
agreement rather than the paper's finding; the figure never appears as "44 %" in the body; the
periodontal task is absent; and the reader must reverse-engineer a number to know what the paper
is about.

Five alternatives, all scientifically accurate against the evidence:

1. **An Image-Blind Baseline Outscores a Six-Stage Pipeline on Tooth-Level Caries Detection in
   Panoramic Radiographs** — *most direct; leads with the finding.*

2. **What a Tooth-Level Score Cannot Tell You: Constant Baselines, External Validation and
   Domain Shift in Automated Panoramic Dental Screening** — *leads with the methodological
   contribution and covers both diseases.* **← recommended**

3. **Measuring the Floor: Image-Blind Baselines for Caries and Periodontal Bone-Loss Detection on
   Panoramic Radiographs** — *names both diseases and the core idea.*

4. **Constant Baselines and Per-Site External Validation for Automated Dental Screening on
   Panoramic Radiographs** — *conservative, reviewer-legible, no rhetorical framing.*

5. **A Fixed List of Eight Molars Matches a Deep Pipeline and Two Vision–Language Models on
   Tooth-Level Caries Prediction** — *most concrete; states the actual comparison.*

Recommendation: **option 2.** It names the evaluation contribution rather than a single result,
survives the external cohort's non-replication (option 1 does not — the finding does not
reproduce externally, and a title asserting it would overclaim), and accommodates the periodontal
branch, which is real work with a real negative result.

---

## Reproducibility of this audit

- Parameter counts: `torch.load` on each checkpoint, summing `numel()` over tensors.
- 477 / 479 / 148 / 164 / 86 / 78: recomputed from `DENTEX/disease/label/*.json` with the
  repository's own `LABEL_RE` (`^(\d+)-(.+)-(\d+)$`, finding id `1` = *çürük*).
- Constant set: greedy fit re-run from scratch on the 78 fit images; exact match to the stored
  result.
- Survey counts: recomputed from `outputs/related_work_extract.csv` (84 rows → 49 unique titles;
  external-validation classifier re-applied with negation handling).
- Citations: `scripts/audit_citations.py`; four flagged entries re-verified against Crossref and
  PMLR.
- Test suite: `pytest tests/ -q` → 122 passed.
