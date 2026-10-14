# 2026-10-14f — Stage 4b retrained on overlap bands, tested once: not eligible

**Session goal:** run the registered Stage-4b retrain on the Mac — three seeds, then, on the
decision owner's "score", the one test pass — and document the result, so the Windows clone can
carry on with what needs no raw Tufts data.

Run on the macOS clone, in the git worktree `.claude/worktrees/stage-4b-retrain-preflight-6d676a`
(branch `claude/stage-4b-retrain-preflight-6d676a`), night of 14 Oct, from `e8bbf35`. Numbers in
`RESULTS_LOG` 2026-10-14d.

## What was done

- **Orient and gate.** HEAD `e8bbf35`, `dbc0024` (the protocol commit) an ancestor; `git diff
  dbc0024 HEAD` over the protocol and the four Stage-4 scripts empty; no `models/19` and no test
  files before the run.
- **Data into the worktree.** The raw Tufts data lives in the main checkout's gitignored
  `_repo_archive/datasets_workspace/`, which a worktree does not have. Three symlinks
  (`Radiographs`, `Expert`, `Segmentation`) point there; `.gitignore`'s `dir/` patterns do not
  match symlinks, so the three paths were added to `.git/info/exclude` (local, shared by the
  worktrees). No code changed. Checked: 1,000 radiographs and 1,000 masks, all 1615×840;
  `teeth_bbox.json` md5 `8fb9182c1f5c98a5ea8a231469f7ba80`.
- **Preflight.** Python 3.12.12, torch 2.2.0, MPS available; pytest 197 passed; invariants 12
  hold; 201 claims, no drift; `check` H1–H3 pass with the registered bands.
- **Training.** Seeds 42, 43, 44 in one background chain that stopped on the first failure,
  `caffeinate -i`, logs teed to `models/19_bone_severity_overlap/seed*_train.log`. All three ran
  once and finished by early stopping (best validation macro-F1 0.4425 / 0.4738 / 0.4726 at epochs
  3 / 5 / 13 of 13 / 15 / 23). `run_summary.txt` written; every figure in it checked against the
  history JSONs, and the sha256 of each `.pth` re-computed. The user committed the seven files in
  **`a6e837b`** before the test pass.
- **ML-engineering review** (`mle-reviewer`, the user's `/mle-review`): nothing blocks the test
  pass; disclosures adopted into `run_summary.txt` and the log (tooth-prior ties, seed 42 −
  `models/04` on teeth `models/04` trained on, MPS selection versus CPU scoring, `lr` logged after
  the scheduler step, version and data-hash records outside the history files).
- **The test pass**, once, on "score": `bone_severity_v2_eval.py score | tee test_stdout.log`.
  Seed 42 0.2938 [0.2143, 0.3850] against the tooth prior's 0.3344; difference −0.0405 [−0.1245,
  +0.0584]; **not eligible**. Every figure re-derived from `test_rows.json` with scikit-learn.
- **Documentation:** `RESULTS_LOG` 2026-10-14d; `model_metrics.md` Stage 4b; `PAPER_MATERIAL.md`
  §7.4 paragraph, new §8.40, a §9 item; `SUBMISSION_TODO.md` note on row o; `paper/main.tex` — the
  system overview, `sec:stage4` and the Limitations item; five claims and two assertions in
  `scripts/verify_paper_numbers.py` (206 claims); PDF rebuilt with tectonic, 15 pages, 0 errors, 0
  undefined references; `README.md` (the 4b row, the claim count); `models/README.md` row for
  `models/19`; the test section of `models/19_bone_severity_overlap/run_summary.txt`;
  `transfer.md` top line, §1, §3, §8.
- **Weights copied out of the worktree** to the main checkout's
  `models/19_bone_severity_overlap/` (gitignored there too), hashes re-checked.

## Decisions made

- **Ran on the Mac, per protocol §2, not on a rented GPU.** The trainer selects MPS or CPU only;
  CUDA would have needed a committed amendment to the protocol, and the job does not need a GPU
  (about 7–8 s an epoch, three runs in about eight minutes). Nothing was rented.
- **Linked the data instead of running in the main checkout or editing `SRC`.** The session works
  in a worktree; editing the path would have changed frozen code, and the main checkout is not
  this session's tree.
- **The chain stopped on the first failure**, so a crashed seed could not be followed by the next
  one before the decision owner ruled on it (protocol §9: no seed twice). None crashed.
- **Seed 42 stays the candidate** although it had the lowest validation figure — fixed before
  training. No choosing between seeds after the test.
- **The manuscript gives the contrast-trained head's test figure too** (0.366; 0.371 without its
  three training radiographs). The text had said "not evaluated"; once a figure against the true
  bands exists and is above the retrain's, leaving it out would read as selective. No comparison of
  that head with the prior was registered, and none is claimed.
- **Two-decimal difference in the paper** (−0.04 [−0.12, +0.06]): the stored bounds are rounded
  to four places, and −0.1245 cannot be rounded to three places without knowing the fifth.
- **No adoption question** — the protocol makes one only for an eligible result.
- **Session file suffix `f`**, following the repo's same-day convention, not the bare date.

## Open questions

- Whether the journal version keeps Stage 4b or removes it (plan J11 / D10). This result is the
  case for removal; the decision owner decides, and the mentor has not been told of any of the
  14 Oct Stage-4 work.
- Why `models/04` moved from 0.240 on validation to 0.366 on test against the same bands — noise
  on ~40 radiographs is the simplest reading; nothing further is registered to test it, and the
  Tufts test split is spent for Stage 4b.
- Whether the symlinks and the `.git/info/exclude` lines stay once this worktree is retired.

## Next steps

1. The user commits (two commits proposed at STOP 2: `data:` for the score artefacts, `docs:`
   for the rest) and decides when to push.
2. On Windows, after pulling: build `main.tex` with pdfLaTeX and compare with the tectonic PDF
   (15 pages); nothing there needs the raw Tufts data.
3. The six-page cut carries the Stage-4b sentence or drops Stage 4b (`SUBMISSION_TODO.md` row o
   note).
4. Tell the mentor and the repo owner: the Stage-4a default change, the withheld grade, and this
   negative Stage-4b result.
