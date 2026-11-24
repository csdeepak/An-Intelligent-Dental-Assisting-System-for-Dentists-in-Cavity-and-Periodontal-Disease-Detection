# 2026-11-23 — research_paper/: repository audit, evidence-locked revision, three-perspective review

**Session goal:** one line — on the owner's master prompt, re-audit the repository and produce a new,
evidence-locked research paper in `research_paper/` with the RCE skill: audit, evidence registry,
literature, novelty, verification, clinical validity, review, integrity gates, LaTeX and PDF.

## What was done

1. **Oriented and checked** (`main` = `origin/main` = `851f089`, clean): `pytest` 210 passed / 3 skipped,
   `verify_invariants.py` all hold, `verify_paper_numbers.py` 215/215. `D:\nangxia_dataset` not attached.
2. **RCE skill** (`C:\Users\csdee\PESU\research_skill\research_writing_skill`): switched from
   `rce-adaptive-representation` (clean) to `main`, fast-forwarded to `3e4411f` (0.5.0 candidate; the
   release is v0.4.0). Only that checkout's tools were used.
3. **PaperOrchestra** evaluated from its README and arXiv abstract; **not used** (needs hosted LLM keys,
   regenerates text and plots outside the evidence trail). `research_paper/tooling_decisions.md`.
4. **Deliverables in `research_paper/`** (new directory; `paper/` untouched): `WORKFLOW.md` (flowchart),
   `repository_audit.md`, `evidence_registry.md` (generated from `.rcs/`), `literature_review.md`,
   `research_gap_and_novelty.md`, `experimental_verification.md`, `clinical_validity_assessment.md`,
   `paper.md` → `paper.tex` → `final_research_paper.pdf`, `references.bib`, `figures/` (8, copied
   from `paper/ieee/figures/`, script-generated), `tables/` (8), `reviewer_report.md`,
   `integrity_check_report.md`, `publication_readiness.md`, `open_issues.md`, `disclosure.md`, `README.md`.
5. **Manuscript**: built from the reviewed ten-page draft (`paper/paper.md`), with new sections
   (stage-evidence Table 3, clinical implications, availability, ethics, related work on periodontal
   bone loss, numbering, methodological failures) and 10 new verified citations (9 + Lipton 2014),
   each generated from Crossref and checked against its abstract (OpenAlex, Europe PMC, arXiv).
6. **Gates (RCE `3e4411f`)**: G1, GL (49 true, 2 unresolvable, 0 retracted, live), G3 lint and numbers
   passed on v1; reviewers and VERIFIER ran as isolated subagents (not humans); results and the
   round-2 re-run are in `integrity_check_report.md`.
7. **Review round 1**: A, B and C all major revision; VERIFIER blocked GI on M4–M7. About 90 text
   corrections in three scripted batches (`tools/revise_round1_text.py`, `_b2.py`, `_b3.py`) plus one
   new post-hoc analysis on the 164 DENTEX images (`tools/detected_constant.py`). Its first run
   stopped on its own control gate (12 of 164 images flag different caries codes on Windows than the
   saved macOS run); the second run scores both side by side.
8. **What the analysis found** (`RESULTS_LOG` 2026-11-23):
   - A constant naming only the detected molars scores F1 0.358. Against it the crop classifier is
     not separable (+0.41 [−2.24, +3.14]); the lesion detector leads (+13.94 [+9.63, +18.15]).
   - DENTEX caries annotations outline whole teeth (median box ratio 0.907).
9. **GI** (pre-review integrity) took three isolated VERIFIER rounds:
   - Round 1 blocked on M4–M7.
   - Round 2 blocked on M6 (one sentence) and M7 (missing story records).
   - Round 3 **passed** with 0 errors.
   - M2 is still INSUFFICIENT_EVIDENCE: six literature quotes are not saved. That will block
     stage-final GI.

   Final draft v3: 14 pp; G1, GL, G3 lint and G3 numbers all 0 errors.
10. Records: `RESULTS_LOG` 2026-11-23, `model_metrics.md`, `PAPER_MATERIAL` §7.8, §8.45, §9, and the
   `transfer.md` header, all with CRLF kept. Nothing committed.

## Decisions made

- **Base the paper on the ten-page reviewed draft, not on the 16-page `main.tex`**: the newer text, with
  review round 1 already applied.
- **Title drops "periodontal"**: no stage detects periodontal disease (Stage 4's label is abnormality-mask
  overlap). Author's decision to confirm.
- **Theory reframed as an application of Lipton et al. 2014** after reviewers A and C found the half-F1
  rule is known; verified on arXiv before citing.
- **Ningxia's role in the tooth-detector choice disclosed** everywhere it bears on a claim
  (`RESULTS_LOG` 2026-10-11f/g).
- **No code default changed**: withholding the Stage-3b grade (Reviewer B) is left to the owner.
- **Reviewer claims verified before acting**: e.g. the 1.5× volume condition was kept as written because
  the saved acceptance file checks both comparators.

## Open questions

- Which venue, and is a six-page caries-only cut wanted now (`publication_readiness.md`)?
- Why do the Windows and macOS runs differ on 12 DENTEX images (library versions? non-determinism)?
- Kaggle licence; DENTEX share-alike; public anchor for `ef3f453`; author block; CPU model.

## Next steps

1. Owner reads `research_paper/open_issues.md`, then the PDF.
2. Decide the venue; cut accordingly (planned: CONECCT-length caries-only).
3. Fill the CLAIM 2024 / TRIPOD+AI / dental checklist item by item.
4. If wanted: commit `research_paper/` (explicit paths) on a branch.
