# Research gap and novelty

Phase 6 deliverable. Each candidate contribution from the prompt is tested against the
implementation, the evidence and the literature (`literature_review.md`), and then sorted.

## 1. Candidate-by-candidate

| Candidate | Implementation | Evidence | Literature | Novel? | Limitation | In the paper? |
|---|---|---|---|---|---|---|
| Image-blind constant for tooth-level caries scores, with closed-form F1 and selection rule | `scripts/figures/make_draft_figures.py`; constant arm in eval scripts | rule reproduces the eight molars; F1 0.320; stable median over 10,000 refits | input-blind baselines in VQA/NLI (Goyal 2017, Poliak 2018); none found for dental tooth-level scores | **Yes, scoped:** transfer of an established idea plus a derivation specific to micro-F1 over tooth codes; "none found" is bounded by a non-systematic search | theory post hoc; one corpus's prior | **Main contribution 1** |
| Constant-baseline protocol across cohorts and sites | eval scripts under `scripts/eval/`, paired cluster bootstrap, DL + HKSJ | three cohorts, four sites | site effects (Zech 2018); external validation rare (Kim 2019) | **Partly:** the components are standard; the combination for this task is not reported elsewhere in our search | DENTEX in-domain; Ningxia informed adoption | **Contribution 2** |
| Reformulating caries as lesion localisation | `models/16`, `src/classifiers.py::run_caries_lesion_detector` | 2 of 3 cohorts under its rule; +9.28 pooled external, fewer flags | lesion detection itself is standard (CariesXrays FPCL) | **No as a method;** yes as a pre-registered test that localisation escapes the positional floor | site interval includes 0; confounded with new training data | **Contribution 3**, worded as a result, not a method |
| Modular tooth-centric system with structured per-tooth JSON | `scripts/run_inference.py`, `app.py`, `Dockerfile` | runs end to end, 1.70 s CPU, 210 tests | two-stage dental systems common (Tuzoff 2019; van Nistelrooij 2024) | **No** — engineering contribution | not clinically validated | described as the vehicle (IV), not claimed as novel |
| Multi-corpus tooth detector | `models/15/arm3c_best.pt` | DENTEX numbering 92.8% in-domain; UFBA +23.86 pp over previous detector | combining public datasets done (van Nistelrooij 2024) | **No** | adopted against its own guard; Tufts box mAP 0.587 vs 0.723 | stated as a front-end choice with its override |
| Error propagation across stages (identity chain) | Table 1 from saved numbering results | DENTEX 7.2, Tufts 36.5, UFBA 55.5 points lost to identity | end-to-end numbering rarely reported (our reading) | **Modest** — a reporting device | single metric chain | **Part of contribution 1/4** |
| Calibration and abstention | isotonic calibrator; coverage curves with shuffle control | numbering +4.76, crop classifier +14.25 at 75% coverage; ECE 0.136 → 0.043 | standard methods (Guo 2017, Geifman 2017) | **No** as methods; the shuffle control is good practice | not for the shipped lesion detector | RQ3 evidence |
| Failure analysis under shift / evidence audit per stage | Table 3; Stage-4 audit; Stage-4b contrast finding | documented negative results | methodological-failure literature (Varoquaux 2022; Oakden-Rayner 2020) | **Not novel as an idea;** unusual in completeness for a dental system | — | **Contribution 4** |

## 2. Sorted

**Verified contributions (supported by evidence in this repository and not found in the searched literature for this task):**
1. A closed-form image-blind floor for tooth-level caries F1, with its selection rule, checked on data.
2. A multi-cohort, per-site paired comparison against that floor, showing a crop-classifier
   pipeline level with it externally.
3. A pre-registered test that lesion localisation led the floor on pooled external sites with
   fewer flags (with the stated confounds).

**Existing techniques reused:** YOLOv11l, ResNet18, Hungarian assignment, isotonic regression,
temperature scaling, selective classification, cluster bootstrap, DerSimonian–Laird, HKSJ.

**Engineering contributions:** the six-stage pipeline with hash-pinned checkpoints, structured JSON
report (schema 1.6) carrying per-stage limitations, Streamlit/Docker demo, a 215-claim number
checker and invariant suite.

**Proposed future improvements (not done):** learned position-only floor and site probe; Ningxia
per-type re-run; lesion-detector calibration on labelled-healthy data; periodontal grading on BRAR;
reader study.

## 3. What is explicitly not claimed

No state-of-the-art claim (no matched benchmark comparison licenses it); no "first" claim beyond
"we found none in our search"; no clinical-readiness claim; no periodontal claim; no claim that
the lesion detector's lead would hold at an unseen site.
