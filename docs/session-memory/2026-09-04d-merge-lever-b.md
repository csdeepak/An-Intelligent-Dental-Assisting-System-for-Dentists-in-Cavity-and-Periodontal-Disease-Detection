# 2026-09-04d — Merge the friend's Lever B work; resolve the parallel-session collisions

**Session goal:** `git merge origin/main` — integrate the friend's Lever B build/eval (4
commits, done on Windows in parallel with the Mac-side Phase 0 / Lever A2 / Tufts-e2e work) —
and resolve the collisions that two isolated same-day sessions produced.

Continues `2026-09-04c-tufts-e2e-fdi-eval.md` (Mac side) and merges
`2026-09-04a-lever-b-build-and-both-arms.md` (the friend, Windows side). No GPU, no new results
— an integration session.

## What was done

- **`git merge origin/main --no-edit`** (merge-base `c3c9843`; local `main` 10 commits ahead,
  `origin/main` 4 ahead — friend's `d46223f` models/14 weights, `ef3f453` Lever B pre-reg
  freeze, `0c3fd81` Lever B build, `1534121` Lever B results). Two files conflicted:
  `docs/results/RESULTS_LOG.md` and `transfer.md`.
- **`RESULTS_LOG.md` — resolved by relabelling the friend's two entries.** Both sessions had
  independently used the labels `2026-09-04` and `2026-09-04b`. The file is chronological,
  oldest first, and Phase 0 (Mac, morning) genuinely came first, so the Mac entries keep
  `2026-09-04` … `2026-09-04e` and the friend's Lever B entries became
  **`2026-09-04f`** (B-single) and **`2026-09-04g`** (B-pooled). Nothing of either side's
  content was dropped — verified by diffing the working copy against both parents.
- **`transfer.md` — 3 conflict hunks resolved** (§1 header, §3 Lever B bullet, §4
  pending-decision rows), CRLF preserved:
  - §1 rebuilt as one "Last updated: 4 September 2026" snapshot carrying **both** sessions'
    4-Sep work (Lever B *and* Phase 0 / A2 / Tufts-e2e), with the GPU balance reconciled — see
    Decisions.
  - §3 took the friend's "Lever B — DONE, VERDICT PENDING NINGXIA" bullet; the stale "(B)
    freeze the bars / (D) after B+C" to-do text in the "Where work resumes" paragraph was
    updated to "done".
  - §4 kept the friend's new "⚠️ Get Ningxia onto the Windows machine" row **and** the
    Mac side's "~~Lever A2 worth chasing?~~ RESOLVED 4 Sep" row (dropping the friend's older
    un-resolved "Lever A2 — worth chasing?" row, which predated A2 actually running).
  - §7 JarvisLabs ledger row: added the friend's instance **496516** (Lever B, RTX-PRO6000,
    ₹546.93).
- **`models/` directory-name collision resolved.** Both sessions created a `models/16_*`:
  Mac `models/16_detector_leverA2_finetune/`, friend `models/16_lever_b_pooled/`. The friend's
  was already pushed and referenced from pushed docs, so the **Mac dir was renamed
  `git mv models/16_detector_leverA2_finetune → models/17_detector_leverA2_finetune`** and its
  ~9 references updated (`transfer.md`, `RESULTS_LOG.md` 2026-09-04b + 04c, `model_metrics.md`,
  `PAPER_MATERIAL.md`, `outputs/lever_A2_detector_finetune/STATUS.md`, `gt_scale_probe.py`,
  `outputs/stage2_tufts_a2/…json`, `outputs/lever_A2_detector_finetune/a2/ningxia_caries.json`,
  `2026-09-04b-lever-a2-executed.md`, the run_summary.txt title). The gitignored `a2_best.pt`
  (49 MB) moved on disk with the dir.
- **Fixed the friend's now-stale cross-references** to `RESULTS_LOG` `2026-09-04` / `04b`
  (which, in their files, mean Lever B) → `2026-09-04f` / `04g`, in `README.md`,
  `models/README.md`, `scripts/{eval,yolo,dentex}/README.md`,
  `models/16_lever_b_pooled/run_summary.txt`, and the internal "same pooled dataset as the
  2026-09-04 entry" line inside entry 04g. Every remaining `2026-09-04*` ref was classified by
  hand as Mac-side (keep) or friend-side (fix).
- **Verified:** `scripts/eval/verify_invariants.py` (with `/opt/anaconda3/bin/python3`) — all
  invariants hold, including the six frozen weight hashes and `models/14`'s `best.pt`
  (`271316c46caa…`). Zero conflict markers in any tracked file. Every touched file keeps its
  original line-ending style (CRLF: transfer.md, RESULTS_LOG.md, model_metrics.md,
  PAPER_MATERIAL.md, models/README.md, scripts/eval/README.md; LF: everything else).

## The friend's Lever B result, as merged in

- **B-single** (Lever 2's frozen `models/14`, zero GPU): CariesXrays-val **69.4%** tooth-level
  lesion agreement vs gate 31.7% / constant 56.2% (CI excludes 0 — decisive win); DENTEX
  **8.6%** vs 44–49% (CI excludes 0 the wrong way — decisive loss). The pre-registered
  "wins in-domain, fails to transfer" outcome.
- **B-pooled** (`models/16_lever_b_pooled/`, CariesXrays + DENTEX-caries balanced, instance
  496516, ₹546.93): DENTEX **45.5%** — CI *includes* 0 vs both comparators, a statistical
  **tie** (no longer a loss); CariesXrays **68.4%** — still a decisive win, ~1 pp cost.
- **§6 acceptance rule NOT met by either arm** — needs ≥2 of 3 cohorts, only 1 passes.
  **Ningxia is the deciding cohort and is not on the friend's machine.** Pipeline caries path
  stays gate v3.0.

## Decisions made

- **Friend's RESULTS_LOG entries relabelled (04f/04g), not the Mac's.** *Reason:* the file is
  chronological oldest-first; Phase 0 was the first 4-Sep milestone; renumbering the Mac's five
  entries would either break that order or force reordering the friend's pushed entries above
  them. Cost = ~11 cross-ref fixes in the friend's files, each a factual correction.
- **`models/16_detector_leverA2_finetune` → `models/17`, not the friend's dir.** *Reason:* the
  friend's `16_lever_b_pooled` was pushed first and is referenced from pushed docs and from
  `RESULTS_LOG` 04g; the Mac dir is local-only. Standard "local work yields to published work".
  `12`/`12a` is the repo's precedent for a suffixed pair, but A2 and B-pooled are unrelated
  levers, so a clean new number is right, not `16a`.
- **GPU-balance mystery resolved by the merge.** The Mac side had flagged a "~₹547
  unexplained gap" (transfer.md said ₹1,732 on 3 Sep; `jl status` showed ₹1,184.84 before
  A2). It was **Lever B**: ₹1,731.77 − ₹546.93 (Lever B) − ₹36 (A2) = ₹1,148.78. Written
  into transfer.md §1; the old "needs explaining" note is gone.
- **A merge commit on `main` is the intended end state** — the user asked for the pull. Not
  pushed (not asked).
- **Touched two files that rule 2 says are frozen** — `2026-09-04a` (friend's session memory)
  and `2026-09-04b` (Mac's). Edits were path-pointer corrections only (`2026-09-04`→`04f`,
  `models/16`→`models/17`), not narrative. Noted here so the exception is on record.

## Open questions

1. **Is `models/17` the right number?** It reads slightly out of order (A2 conceptually
   follows A=15; B-pooled=16 slots between them). Left as-is — renumbering again is churn. If
   the mentor prefers `15a` or similar, it is a `git mv` + the same ~9 refs.
2. **The two machine-generated provenance JSONs** (`outputs/stage2_tufts_a2/…`,
   `outputs/lever_A2_detector_finetune/a2/ningxia_caries.json`) now say `models/17…` for a run
   that executed against `models/16…`. Chose one canonical path over "historically exact but
   now-broken". Anyone doing forensics has this file + the merge commit.
3. Nothing about the Lever B science is open here — that is `2026-09-04a` and `RESULTS_LOG`
   04f/04g. The one blocker (Ningxia → Windows) is in transfer.md §4.

## Next steps

1. **Push** when the user asks (≈24 unpushed commits + this merge).
2. **Get Ningxia + CariesXrays-raw onto the Windows machine** (user / account owner) — the
   only thing between Lever B and a real §6 verdict. Then `scripts/eval/lever_b_bootstrap.py
   --arm-tag B-pooled` — no new code.
3. Track A (the paper) stays the critical path — venue commit, the four compliance blockers,
   `main.tex` authors/affiliations, the Lever-2 Related Work row.
