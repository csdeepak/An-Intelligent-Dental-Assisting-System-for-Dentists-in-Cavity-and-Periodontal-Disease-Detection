# Integrity check report

Every gate below was run with the tools of the Research Communication Engine at commit `3e4411f`
(`C:\Users\csdee\PESU\research_skill\research_writing_skill\tools\`, 0.5.0 candidate), from the repo
root with `--project-root .`. A gate is reported as passed only where its tool wrote a report with 0
errors. The gate reports sit in `research_paper/.rcs/audits/gates/`, which is gitignored by the
repository's existing `.rcs/` rule, so the results are copied here.

## 1. Gates on the final draft (v3; gate text hash `4f21c8ca…c2f8`)

| Gate | Tool | Result | Notes |
|---|---|---|---|
| G1 artifacts | `validate_artifacts.py research_paper/.rcs --project-root .` | **PASS** — 0 errors, 0 warnings | 54 evidence items, 44 claims, 10 limitations; spine bound; every negative result has a reporting decision |
| GL citations | `verify_citations.py --online`, then `--gate --draft` | **PASS** — 0 errors, 0 warnings | 52 sources: 50 `true`, 2 `unresolvable` (Bizjak 2024, not indexed, confirmed at publisher; YOLO11 software), both listed in `open_issues.md`; 0 `false`; 0 retracted |
| G3 lint | `lint_draft.py --rcs` | **PASS** — 0 errors, 64 warnings | warnings are style screens (long sentences, untagged claim-like sentences, rare acronyms); the one unlicensed strong verb in v1 ("beat") was rewritten |
| G3 numbers | `verify_numbers.py --project-root .` | **PASS** — 0 errors, 1 warning | the warning is "ISO 3950", a standard's name, not a result |
| GI integrity, round 1 (v1) | `integrity_check.py collect` → isolated VERIFIER | **BLOCKED** — M1 CLEAR, M2 INSUFFICIENT_EVIDENCE, M3 CLEAR, M4–M7 SUSPECTED | report kept at `.rcs/audits/integrity/pre/round1/verifier_report.json`; every finding's disposition in `reviewer_report.md` |
| GI integrity, round 2 (v2) | `integrity_check.py collect` → new isolated VERIFIER → `integrity_check.py gate` | **FAILED** — M6, M7 SUSPECTED; stale hash | §2 |
| **GI integrity, round 3 (v3)** | same, third isolated VERIFIER | **PASS** — 0 errors, 0 warnings; M1, M3–M7 CLEAR; M2 INSUFFICIENT_EVIDENCE (allowed at stage pre, listed in open_issues) | `GI_integrity.json`; recorded with `workflow_guard.py record --role VERIFIER` |
| G2 outline | no tool | **unverified** | the outline is the reviewed ten-page draft's, extended; not approved by a person in this run |
| G4 review | `g4_check.py` | **unverified** | needs the five-seat panel's JSON; this run used the three perspectives the brief asked for |
| G5 final | `claim_invariance.py` and final GI | **not run** | P7 needs the authors' inputs first (`open_issues.md`) |

## 2. GI rounds 2 and 3

**Round 2 (v2, after review round 1)** — a fresh isolated VERIFIER; report in
`.rcs/audits/integrity/pre/round2/`. `integrity_check.py gate` result: **FAILED** (3 errors).
- **Resolved:** M1, M3, M4, M5 CLEAR. M4 (undisclosed Ningxia selection) and M5 (null results worded
  as findings) from round 1 are resolved.
- **M2:** INSUFFICIENT_EVIDENCE (warning). Six literature numbers lack a saved quote; now listed in
  `open_issues.md`.
- **M6:** SUSPECTED. Contribution 3 still said the rule was "committed before training". **Fixed.** The
  VERIFIER withdrew its round-1 point about the 1.5× wording after checking the acceptance script.
- **M7:** SUSPECTED, on records only. **Fixed:** `story/alternatives.md` and `story/rq_check.md`
  written, RQ3 added to the spine, and `story_changes` logged in `state.json`.
- **GI_REPORT_STALE:** the VERIFIER hashed the file's bytes, but the gate hashes the text. Round 3 copies
  the gate's hash from `bundle.json`.
- **Non-blocking notes, both fixed:** the single-corpus values are now labelled as measured under the
  previous detector. "20 passes" became "14 before the choice, 20 including the re-measurement after
  it" (`RESULTS_LOG` line 8043).

**Round 3 (v3)** — **PASSED** (`integrity_check.py gate`: 0 errors, 0 warnings).
- **CLEAR:** M1, M3, M4, M5, M6 and M7, each with cited evidence. M6: the rule freeze `ef3f453`
  (4 Sep, 01:01) precedes the pooled arm's training. M7: the story records now exist.
- **M2:** INSUFFICIENT_EVIDENCE, the same six literature claims with no saved quote. This is allowed at
  stage pre and **blocks stage final**, so it is the first P7 task (`open_issues.md`).
- **Alignment:** 26 rows. 20 supported, including Lipton 2014; 6 not checkable (no saved quote); none
  overstated or unsupported.

## 3. Repository-side checks (this session)

| Check | Result |
|---|---|
| `pytest tests -q` | 210 passed, 3 skipped |
| `scripts/eval/verify_invariants.py` | all invariants hold |
| `scripts/verify_paper_numbers.py` (`paper/main.tex`) | 215/215 |
| `tools/trace_numbers_rp.py` on v2 | 442 distinct numbers; 10 not matched literally, each explained in `experimental_verification.md` §5b |
| `tools/build_rcs.py` value check | all 54 evidence items' values found in their locator files |
| `tools/build_paper.py` | 14 pages; 0 LaTeX errors; 0 undefined references; 0 overfull boxes; 0 BibTeX warnings |
| `tools/detected_constant.py` control | run 1 **stopped** on its control gate (12 of 164 images differ from the saved run); run 2 reports both runs |

## 4. What the gates cannot establish

- That a cited work supports its sentence beyond the abstract. Full texts were read for Zancan,
  Bizjak and Li 2024 on 2 Nov. Every other check is at abstract level.
- That the reviewers are independent. They are subagents of the same model family.
- That the numbers are reproducible on another machine. They are not exactly reproducible: 12 of 164
  images differ between this clone and the macOS clone.
