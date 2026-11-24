# Status — 23 Nov 2026 (session stopped at the usage limit, mid-revision)

## Done
- Deliverables 1–6, 8–10, 15 written: audit, evidence registry, literature review, novelty,
  experimental verification, clinical validity, references, figures, tables, README.
- `final_research_paper.pdf` = **review version v1** (12 pp, 0 LaTeX errors, 0 undefined refs).
- RCE gates on v1: G1 PASS, GL PASS (49 true / 2 unresolvable, 0 retracted), G3 lint 0 errors,
  G3 numbers 0 errors 0 warnings.
- Independent review of v1 (`review/reviewer_A.md`, `_B.md`, `_C.md`): **all three: major revision**.
  Reviewer A checked 26 numbers: all match. Reviewer C verified Eq. 1–3 and recomputed the meta-analysis: correct.
- VERIFIER (`.rcs/audits/integrity/pre/verifier_report.json`, round 1): **GI BLOCKED** —
  M1 CLEAR, M3 CLEAR, M2 INSUFFICIENT_EVIDENCE, M4–M7 SUSPECTED.

## In progress when stopped
- `paper.md` has **batch 1 of the revision applied (23 text corrections**, `tools/revise_round1_text.py`):
  Lipton et al. 2014 cited for the half-F1 rule (verified on arXiv; bib entry added), "78 held-out"
  corrected, random-effects interval in the abstract, "not annotated as carious", pooled AUC 0.855,
  front-end dependence of the constant (0.399 → 0.591), periodontal aim stated as not achieved,
  three-hospital note, HKSJ variance note. **PDF not yet rebuilt from it; gates not re-run on it.**
- `tools/detected_constant.py` was running in the background: constant restricted to detected
  molars (Reviewer A CRITICAL 1) and DENTEX caries-polygon size vs tooth box (Reviewer B
  CRITICAL 1). Output → `audit_runs/review_round_analyses.json` (check its control gate first).

**Update:** `detected_constant.py` finished and **failed its control gate**: on 12 of 164 images
the lesion-detector codes from this Windows run differ from the saved run (`D_fdiset_lesion-detector_arm3c`,
made on the macOS clone). Nothing was scored. Two machines already disagreed once (0.294 vs 0.300).
Before using the analysis, compare the 12 images (`review_round_analyses.json` lists them) and
decide whether to score both runs side by side or rerun on the macOS clone.

## Left to do (in order)
1. Read `audit_runs/review_round_analyses.json`; if the detected-molar constant beats the crop
   classifier, restate the RQ1 development result; if caries polygons are tooth-sized, rename
   DENTEX "lesions" as annotated carious teeth and call DENTEX agreement tooth-level.
2. Batch 2 of text fixes (verified facts already gathered):
   - **M4/C1/A7:** state that Ningxia results were known when the tooth detector was chosen, and that
     Ningxia caries images were scored in 20 full passes by 11 Oct (`RESULTS_LOG` 2026-10-11f/g).
     Remove "cleanest external test" and the C032 sentence.
   - **M6:** the adoption rule was committed after the B-single arm trained. Stage 4's first split was
     crop-level. One of the two guards belonged to `models/13`. The 1.5× volume condition applies to
     the constant only.
   - **M5:** drop "ceiling is not set by supervision". Report that the 32B VLM answered NONE to the
     blank image.
   - **M7/C12:** label the theory post hoc in the abstract, I, III-E and VI-D ("consistent with", not
     "implies/holds"). Table 8: "rule (3)" row is an identity, and row 2 is "confounded with front end".
   - **C5/A4:** per-type flag precision is not volume-matched; withdraw "Both implications hold".
   - **Stage 4a:** PPV 0.25–0.29 (≈3 in 4 flags false), 0.36–1.06 false flags per radiograph, ROC
     0.68–0.69 (`models/18/run_summary.txt`). **Stage 4b:** all seeds 0.294/0.328/0.382, old head
     0.366.
   - **A10/C15:** always-healthy accuracy 0.853 beside 0.797. **A11:** VLM 7B 2-shot F1 0.066,
     4-shot 0.034, one prompt. **A12:** the DENTEX matching rule differs, so "40 points across
     cohorts" needs rewording. Truncated HKSJ [−6.88, +26.09].
   - **Clinical (B):** 31.6% of Ningxia lesions are not on a flagged tooth. Misnumbering moves
     findings. Over-treatment risk on restored teeth. Intended-use scope. The Stage-3b grade is
     untested. The JSON field is still named `bone_loss`. Fig. 4: 46 and 36 are both flagged
     without annotation.
   - **Fix the evidence map:** E018 should point to `acceptance_rule_B-pooled.json`.
3. Rebuild `.rcs` (`build_rcs.py`, relink claims, add Lipton to the registry, re-run
   `verify_citations.py --online`), re-run G1/GL/G3, rebuild the PDF.
4. Re-collect the GI bundle, re-run the VERIFIER (round 2), run `integrity_check.py gate`.
5. Write `reviewer_report.md` (dispositions), `integrity_check_report.md`, and
   `publication_readiness.md`.
6. Under CLAUDE.md, write the `RESULTS_LOG` entry (CRLF), `PAPER_MATERIAL` §9, the session-memory
   file and the `transfer.md` header. Nothing is committed.
