# 2026-10-14d — The plan from here, stage by stage: what is done, what to fix, what to improve

**Session goal:** the user asked for the implementation plan to be updated "properly and
carefully", for each stage, as a fix plan and an improvement plan, using the research survey of
14 Oct.

**Why a new file.** `2026-10-13g-implementation-plan-for-14-oct.md` is a previous session's file
and is never edited (CLAUDE.md rule 2). Its tasks were absorbed by
`2026-10-14-research-audit-and-plan.md`, whose tasks are now all done (`RESULTS_LOG` 2026-10-14,
-14b). This file is the current plan; `transfer.md` §3 points here. Nothing was run to write it;
every status below was checked against the files tonight.

---

## 1. Where things stand

| Check | Value |
|---|---|
| `pytest tests` | 194 passed (184 on the morning of 14 Oct) |
| `scripts/eval/verify_invariants.py` | 12 hold (11) |
| `scripts/verify_paper_numbers.py` | 188 claims, no drift (191; the Stage-4 claims were replaced) |
| `paper/main.tex` | 15 pages under tectonic, 0 undefined references |
| Commits | `73d91e9` holds the implementation. **Not yet committed:** the evening's manuscript change (`2026-10-14c-manuscript-stage4.md` lists the files) and this file |

**The 14 Oct plan, closed.**

| Task | Status | Record |
|---|---|---|
| T0–T8, V1, V2, F1, F3, F7, W1, W2 | Done | `RESULTS_LOG` 2026-10-14; `2026-10-14b-implementation.md` |
| F2 + Phase C (Stage-4 manuscript text, Fig. 5) | Done in the 15-page text; D2's default overridden by the decision owner | `RESULTS_LOG` 2026-10-14b; `2026-10-14c-manuscript-stage4.md` |
| F4, F5, F6, C1 | Open — wait for the six-page cut | §4 below |

**Corrections made to the first version of the 14 Oct plan, kept here so they are not re-made.**

| Earlier claim | What is true | Consequence |
|---|---|---|
| Near-duplicates were never checked | A check existed for the old model's 145 radiographs against the other 853; the current split's train, val and test were never compared | V1 reused it — and **found 248 (test) / 1017 (train)**, a re-rendered copy of one patient's radiograph; disclosed, no positive tooth in it |
| A validation-chosen threshold might help Stage 4a (E2) | Already measured as a pre-registered secondary: 29.1% / 95.0%, F1 0.252 against 0.260 at `argmax` | E2 closed; Amendment 1 forbids another threshold |
| Stage-4a training and serving crops differ | Same geometry, same decoded pixels; only `cv2.resize` rounds differently (≤ 3 grey levels inside a crop) | 0 of 503 flag decisions change; disclosed, not "fixed" |
| The old overlay's red and orange are hard to tell apart for colour-blind readers | Simulated, they stay distinguishable (ΔE 41 under deuteranopia) | The change stands on what red means, not on legibility |
| Missed in the audit | `pipeline.svg` and the README tagline were stale | Both corrected (F7) |

---

## 2. Rules that still hold

- **Freeze until 20 Oct, the stop date for code.** No new model, no new default, no second pass
  over the Tufts test split, no pass over Ningxia (councils of 12 and 13 Oct, 3 of 3).
- **Every measurement:** pre-registered, run once, logged (`RESULTS_LOG`, `model_metrics.md`,
  `PAPER_MATERIAL.md`). A new default needs a recorded decision and its predecessor retained.
- **Ningxia is locked** (CLAUDE.md §6). The Tufts test split is spent for Stage 4a.
- **The user commits.** CRLF files are patched through bytes. No new dependency without asking.
- **The contracts now in force** (from `/mle-workflow`):

  | Contract | Where it lives | Guarded by |
  |---|---|---|
  | Prediction contract: one record per detected tooth, schema `opg-report/1.5`, every checkpoint's sha256 and tag, limitations that follow the weights | `scripts/run_inference.py` | `tests/test_report.py`; invariants "Stage-4 report wording", "default detector registered" |
  | Data contract: Tufts `split_v1` by radiograph, no unexplained near-duplicate across it, DENTEX leakage list by MD5 | `outputs/eda_tufts/`, `data/dentex/disease_leaked_images.json` | invariants "Tufts split disjoint", "leakage exclusion list" |
  | Artefact contract: ten weight files pinned; safe loading | `scripts/eval/verify_invariants.py`; `src/classifiers.py`, `src/fdi_head_inference.py` | invariant "frozen weight hashes"; `weights_only=True` |
  | Train/serve parity for Stage 4a | `tests/test_crop_parity.py` | that test |
  | Promotion gate for any new default | a pre-registration with an untouched test set, written before training | the house rule; no code gate |
  | Rollback | every previous default retained, hash-pinned, selectable (`--detector`, `--bone-loss`, `--caries-method gate`) | invariants |

---

## 3. Stage by stage

Each stage: the evidence as it stands, what 14 Oct fixed, what is still to fix before
submission (S-numbers, cards in §4), what to improve after submission (J-numbers, matrix in §5),
and what is deliberately not done. Research sources R1–R14 are in
`2026-10-14-research-audit-and-plan.md` §4.

### A. Data

| | |
|---|---|
| Evidence | Tufts 1,000 radiographs, frozen radiograph-level split; DENTEX 164 scored / 86 excluded by MD5; CariesXrays 1,200 = the lesion detector's validation split; Ningxia locked; UFBA-425 unseen |
| Done 14 Oct | Near-duplicate scan of the Tufts split (V1); split invariant (T2); one pair found and disclosed (248/1017) |
| Fix before submission | **S2:** the manuscript still calls the 1,200 CariesXrays images ones the lesion detector "was kept away from" (`main.tex` ~595; `SUBMISSION_TODO.md` §1a row i) |
| Improve after | **J1:** an embedding-similarity duplicate check (R2 found 18 pairs in HAM10000 that metadata missed) — needs a new dependency, ask first |
| Not doing | Patient-level grouping on DENTEX: it ships no identifier; stated as a limitation |

### Stage 1 — tooth detector (multi-corpus YOLOv11l)

| | |
|---|---|
| Evidence | Recall 89.3% Tufts test, 99.6% DENTEX (in-domain), 66.6% UFBA-425 (unseen); Tufts box mAP 0.587 against a Tufts-only control's 0.723; adopted over that registered guard; one training run |
| Done 14 Oct | Pinned (it already was); banner and diagram now quote its own figures |
| Fix before submission | **S4:** state the unseen-corpus figures (UFBA-425 recall 66.6%) in the paper (row l). **O2:** the Kaggle training set's licence (`SUBMISSION_TODO.md` §2 item 9) |
| Improve after | **J2:** a detector trained without the Kaggle set — `models/13` (Tufts + DENTEX) exists — scored on UFBA-425, pre-registered; several seeds (R6) |
| Not doing | A retrained default now: it orphans every Ningxia figure (councils of 11–12 Oct) |

### Stage 2 — FDI numbering (ResNet18 head v2.0, Hungarian)

| | |
|---|---|
| Evidence | 92.8% DENTEX (in-domain detector), 63.5% Tufts test, 44.5% UFBA-425 unseen |
| Done 14 Oct | The report now tags the head v2.0, which it always was |
| Fix before submission | **S4:** the unseen 44.5% is not in `main.tex` (row l); "trained once" is not a stated limitation (row c, **S3**) |
| Improve after | **J3:** the reject option parked behind its own pre-registration (11d, 12a councils); report coverage with the shuffled control drawn (F4) |
| Not doing | A new numbering model: two registered attempts were null |

### Stage 3a — caries: lesion detector (default) and the retained gate

| | |
|---|---|
| Evidence | DENTEX 164: FDI-set F1 0.498 vs constant 0.320; lesion agreement not separated from the constant; Ningxia +9.28 pp pooled (external, informed adoption); CariesXrays is its validation split; 43.9% of flagged codes carious; one run. Gate: macro-F1 0.695 on held-out crops, precision 0.40 |
| Done 14 Oct | Report caveat corrected (W1/T3); Fig. 1 separates default and gate (F3) |
| Fix before submission | **S2** (row i); **S4** rows m and n — the constant's placement (92.0% of its codes on true molars) and the flagged-code composition (624 codes, 43.9% carious, 71.6% molars) beside the "cannot score well by reproducing a prior" sentence; **S5** row g — check the two-front-end comparison is in the text |
| Improve after | **J4:** second and third training seeds, scored on DENTEX 164 and CariesXrays only (E5; R6). **J5:** calibration of the detector's scores fitted on CariesXrays val, judged with equal-mass bins (R10, R11) — only with an untouched cohort to test it. **J6:** a false-positive rate — needs a cohort annotated exhaustively (the clinic data, after ethics approval) |
| Not doing | Threshold or calibration study now (12b council: no clean test set) |

### Stage 3b — caries severity (caries / deep caries)

| | |
|---|---|
| Evidence | Validation only: 133 crops, macro-F1 0.77; trained on all 705 DENTEX images |
| Done 14 Oct | `limitations.caries_severity_not_evaluated` in every report; the paper reports no figure for it |
| Fix before submission | Nothing in code. The six-page cut says "present, not evaluated" (row j) |
| Improve after | **J7:** a held-out deep-caries label set — a new annotation round or a cohort that labels depth |
| Not doing | A test on DENTEX 164: it carries no deep-caries class |

### Stage 4a — abnormality flag (ResNet18, radiograph split, seed 42)

| | |
|---|---|
| Evidence | Tufts test: 27.5 / 16.5 / 11.0% sensitivity over three runs (18.3% pooled), 95.9–98.6% specificity, precision 24.8–29.4%, ROC area 0.68–0.69; label = overlap with an expert abnormality mask, not periodontal; no external figure |
| Done 14 Oct | Confidence described as a ranking score (W1, R5); shared jitter set and radiograph-only intervals disclosed (W2, R6); crop parity measured (V2); the near-duplicate disclosed; paper and Fig. 5 rewritten |
| Fix before submission | None in code. The cut keeps the `sec:stage4` paragraph (or its 80-word core) and both disclosures |
| Improve after | **J8:** a periodontal label — bone level as % of root length (R12) — from BRAR (CC BY 4.0, 1,104 patients), with a patient-level split; check first whether BRAR's grades are per tooth. **J9:** training variance measured properly: jitter seeded per run, three new seeds, validation only (E3; R6). **J10:** recalibrate the flag's scores on the 145 validation radiographs (R5) before ever printing them as probabilities. Any new Stage-4a model needs a **new untouched test set** — the Tufts test split is spent |
| Not doing | A threshold (measured, no gain, forbidden by Amendment 1); an ensemble of the saved probabilities (arithmetic after the fact); training on Ningxia (house rule; changing it is the decision owner's and the mentor's) |

### Stage 4b — severity of flagged teeth

| | |
|---|---|
| Evidence | Trained on bands of crop contrast; validation only, 52 crops; three of its radiographs are in the Tufts test split |
| Done 14 Oct | Withheld by default (D1); `--bone-severity-grade` restores it, flagged; the paper says present, not evaluated |
| Fix before submission | Nothing |
| Improve after | **J11:** either retrain on the true overlap classes with radiograph-level splits (E1) — still not a clinical severity — or remove the head in the journal version. Removal is the smaller change |
| Not doing | A first test: it would score contrast |

### Stages 5–6 — report, overlay, app

| | |
|---|---|
| Evidence | Schema 1.5; every checkpoint's hash and tag; overlay colours by meaning; app renders every limitation |
| Done 14 Oct | T3, F1, T6 (safe loading), T7 (input guards) |
| Fix before submission | **S9 (optional):** seconds per image — 1.70 s was measured with the severity grade computed, so it is conservative; say that in one clause rather than re-measure (D8) |
| Improve after | **J12:** the Docker image rebuilt and smoke-tested on the other machine (three default changes behind); a live check of the app with a browser (`browser-automation` skill) |
| Not doing | Monitoring, canaries, feedback logging: there is no deployment, only a research demo |

### Evaluation and statistics

| | |
|---|---|
| Evidence | Radiograph-cluster percentile bootstrap, paired for differences (R3 supports it); pre-registration; one pass per test split |
| Done 14 Oct | Intervals described as covering radiograph sampling only (W2) |
| Fix before submission | **S3:** one Limitations sentence — each model is one training run, so intervals do not cover training variance (row c; R6) |
| Improve after | **J9/J4:** several seeds wherever a model is retrained (R6). Keep the single-pass rule; R7 qualifies it but does not cover one model chosen on a small cohort |

### Figures and colour

| | |
|---|---|
| Done 14 Oct | Fig. 1 (F3), Fig. 5 (F2), overlay (F1), README banner and diagram (F7) |
| Fix with the cut | **F4** coverage curves with the shuffled control and a minimum count; **F5** reliability diagram with equal-mass bins and counts (R10, R11); **F6** per-position denominators — each only if the figure survives the cut |
| Not doing | Redrawing the four retired README infographics |

### Manuscript and reporting

| | |
|---|---|
| Done 14 Oct | Stage 4 throughout; Fig. 5; 188 numbers checked |
| Fix before submission | **S1** the six-page cut; **S2–S5** the open rows a, b, c, d, e, f, g, h, i, l, m, n of `SUBMISSION_TODO.md` §1a; **S6** the mandatory statements; **S7** a CLAIM 2024 self-check of the cut (R13); **S8** a referee-style read of the cut before the mentor sees it |
| Not doing | Counting the "49 papers" now — soften it (§2 item 4); count only for a journal |

---

## 4. Fix before submission — task cards

Hours are estimates. S2–S5 are edits to the 15-page text first, so the cut starts from a true
text (the approach the decision owner chose for Stage 4) — unless D7 says otherwise.

| ID | What | Where | Check | Est. |
|---|---|---|---|---|
| S2 | Row i: CariesXrays 1,200 is the lesion detector's validation split; early stopping and `best.pt` used it. Correct "kept away from", footnote c of `tab:data`, and any "external" wording for it | `main.tex` §Data, `tab:data`, §Results where CariesXrays is quoted | grep "kept away", "held out from that training"; checker passes | 0.5 h |
| S3 | Row c: one Limitations item — every model is one training run; every interval covers radiograph sampling only | §Limitations | sentence present | 0.25 h |
| S4 | Rows l, m, n: UFBA-425 (recall 66.6%, numbering 44.5% as distributed); the constant's placement (92.0% of its codes on a true first or second molar, reaching 81.7% of them, Tufts); flagged codes (624, 43.9% carious, 71.6% molars, against the constant's 1,312, 21.8%, 100%) | §Results, §Limitations | each number asserted in `verify_paper_numbers.py` from its artefact (`RESULTS_LOG` 2026-10-12b) | 1.5 h |
| S5 | Rows a, b, d, e, f, g, h: Ningxia's role and pass count; anchor the 31-point range on test1/test2; "three cohorts, one of them four hospitals"; scope the last sentence and "four capabilities"; DENTEX's two subsets; confirm the two-front-end comparison is stated; soften "almost always" | as listed in §1a | read against each row; checker passes | 2 h |
| S1 | The six-page cut, IEEE conference format, carrying everything above and `sec:stage4` | new `paper/main_6p.tex` (the 15-page file stays) | tectonic build; page count ≤ 6; `verify_paper_numbers.py` pointed at it | 2–3 days |
| S6 | Mandatory statements: authors and affiliations, ethics, data availability with licences, code availability (cite `requirements-lock.txt`), funding, conflicts, contributions, the AI-use disclosure | the cut | each present | Authors; I can draft |
| S7 | CLAIM 2024 self-check of the cut (R13), item by item, with N/A where it applies | `docs/paper/CLAIM_2024_check.md` | every item answered | 2 h |
| S8 | Referee-style read of the cut (the `scientific-thinking-scholar-evaluation` skill) | findings only | — | 1 h |
| F4–F6 | Figure fixes, only for figures in the cut | figure scripts | values unchanged; greyscale check | 1–2 h |
| S9 | One clause: 1.70 s/image includes the severity grade, now withheld by default | §System | — | 5 min |
| S10 | README sections C1–C4 rewritten to the current front end, after the cut fixes the wording | `README.md` | the grep check of 14 Oct | 1.5 h |

**Owner tasks — not mine to do.**

| ID | Task |
|---|---|
| O1 | Tell the mentor and the repo owner: the detector switch (11 Oct), the Stage-4a retrain and adoption (13 Oct), the withheld severity grade, the 248/1017 pair, the rewritten Stage-4 text (14 Oct) |
| O2 | The Kaggle set's licence (ask its authors) |
| O3 | On the Windows machine: pdfLaTeX build; Docker rebuild if the paper mentions Docker |
| O4 | Compliance (`transfer.md` §4): the Tufts Drive folder that opens without sign-in; the SDH `metadata/index.csv`; ethics approval; Tufts pixels in tracked notebooks before any public release |
| O5 | Confirm the venue's deadline and edition from its call for papers (`transfer.md` §5 rules) |

---

## 5. Improve after submission — experiment matrix (journal version)

None is run now. Each needs a pre-registration, the decision owner's go, and — for any new
model — a test set nothing in the project has seen. Expected effects are hypotheses.

| ID | Stage | Hypothesis | Single change | Data · split | Metric · success | Basis | Prerequisite |
|---|---|---|---|---|---|---|---|
| J1 | Data | Tufts holds same-patient pairs a difference hash misses | Embedding similarity + review | All 1,000 | Pairs found; any cross-split one disclosed | R2 | New dependency (ask) |
| J2 | 1 | A detector without the Kaggle set matches the default on unseen data | Training corpora | `models/13` vs default, UFBA-425 | Recall and numbering, paired CI; no worse than −2 pp | R6 for seeds | Pre-registration; licence answer may make it necessary |
| J3 | 2 | Declining low-confidence assignments raises accuracy on kept teeth | Reject option | DENTEX 164, Tufts val | Coverage–accuracy with shuffled control | existing C4 | Its parked pre-registration |
| J4 | 3a | The lesion detector's F1 is stable across seeds | Seed | DENTEX 164, CariesXrays only | Spread of FDI-set F1 | R6 | GPU; pre-registration |
| J5 | 3a | Calibrated scores support a probability in the report | Isotonic or temperature on CariesXrays val | Untouched cohort | ECE with equal-mass bins, interval | R5, R10, R11 | An untouched cohort |
| J6 | 3a | A false-positive rate can be measured | Exhaustively annotated cohort | Clinic data | FP per radiograph | — | Ethics approval |
| J7 | 3b | The depth head separates deep from shallow caries on new data | Test set | New annotation | Macro-F1 vs majority | — | Annotation |
| J8 | 4a | A periodontal label is learnable | Label: bone level % root length | BRAR, patient split | Sensitivity/specificity vs reference | R12 | Check BRAR's label granularity; licence CC BY 4.0 |
| J9 | 4a | Training variance exceeds what three shared-jitter runs show | Jitter seeded per run | Tufts val only | Spread of val macro-F1 | R6 | CPU/MPS hours |
| J10 | 4a | Recalibration makes the flag's confidence a probability | Prior-shift correction or isotonic | Tufts val | Calibration on val; untouched set to confirm | R5 | An untouched set |
| J11 | 4b | True overlap classes are learnable — or remove the head | Labels, or removal | Tufts train/val | Macro-F1 vs majority | — | Decision owner |
| J12 | 5–6 | The image and app work as documented | Rebuild, smoke test | — | Starts; one report | — | Other machine |

Stopping rule for all: pre-register, run once, stop if no clean evaluation set exists.

---

## 6. Order and timing

| When | What |
|---|---|
| Now | The user commits the evening's manuscript change and this file; **O1** |
| 15 Oct | S2, S3, S4 in the 15-page text (≈ 2.5 h), checker updated; S9 |
| 16 Oct | S5 (≈ 2 h); start S1 |
| By 20 Oct | Stop date for code. Nothing after it changes a model or a measurement |
| Late Oct – Nov | S1 the cut; S6 with the authors; F4–F6 for surviving figures; S7, S8; S10 |
| Before submission | O2–O5 closed; pdfLaTeX build |
| After submission | J-items, each behind its own pre-registration |

## 7. Decisions needed

| | Question | Default |
|---|---|---|
| D7 | Fix rows a–n (S2–S5) in the 15-page text first, as was done for Stage 4, or only in the cut? | Long text first |
| D8 | Re-measure seconds per image, or add one clause that 1.70 s included the grade? | One clause, no measurement |
| D9 | README sections C1–C4: rewrite now or after the cut? | After the cut |
| D10 | Stage 4b in the journal version: retrain on true labels (J11) or remove? | Remove — the smaller change |

## Open questions

- Whether the mentor accepts the Stage-4 description; nothing has been shown to her since 11 Oct.
- Whether BRAR labels bone loss per tooth or per patient (decides J8's design).
- The venue's deadline and page limit, from its own call for papers.

## Next steps

1. The user commits; tells the mentor and the repo owner (O1).
2. Answer D7–D10.
3. S2 → S3 → S4 → S5 → S9, each with the three checks; then S1.
