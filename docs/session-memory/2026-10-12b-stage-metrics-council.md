# 2026-10-12b — Council: are the metrics good at every stage, and what is left to implement?

**Session goal:** the user asked whether every stage's metrics, test metrics included, are good
enough, and for a plan of implementation steps that would let the work be published
"confidently without worrying". Asked for a council and for the `mle-reviewer` agent.

Run on the macOS clone. No model was run and no manuscript text or code changed. Documentation
only. Earlier the same day the user asked what "cut the bone-loss branch" meant; the answer was
"from the paper only — nothing is deleted from the code or the repo".

## What was done

### 1. Checks by the chair, before any member was seated

- `pytest tests`: 174 passed.
- `scripts/verify_paper_numbers.py`: 191 claims, no drift.
- `scripts/eval/stage1_switch_intervals.py`: exit 0, and the working tree was still clean
  afterwards, so `stage1_switch_results.json` was re-derived byte-identical.
- Read `docs/results/model_metrics.md` in full and `models/{15,16}/run_summary.txt`, and put a
  per-stage evidence table and twelve candidate actions (A–L) in one brief (session scratchpad).

### 2. The council

Four independent read-only members; none saw another's report.

| Seat | Lens | Agent, model |
|---|---|---|
| 1 | Strict peer reviewer | `Plan`, Opus |
| 2 | Experimental design and improvement planning | `Plan`, Opus |
| 3 | Publication pragmatist under the college's rules | `Plan`, Sonnet |
| 4 | ML-engineering review, findings only | `mle-reviewer` |

**Consensus**

| Question | Verdict |
|---|---|
| GPU spend, a new default, a further pass over Ningxia | **No** (3 of 3) |
| Are the weak absolute numbers a problem for this paper? | **No.** Precision 0.44, Tufts 63.5% and box mAP 0.587 sink a "good clinical system" paper, not a paper about a required baseline (3 of 3) |
| Stage 3b and Stage 4 figures | **Out of the conference cut**; describe both stages as present and not evaluated (3 of 3) |
| Two-front-end table (J) | **Must**, zero cost (3 of 3) |
| Second seed (B), threshold or calibration study (D), reject option (E), retrained detector (F), Stage-4 rescore (G) | **Don't** (3 of 3). This reverses Seat 1's dissent of the morning council on B |
| Flagged-teeth breakdown from saved rows (I) | Run it: must (Seat 2), should (Seats 1 and 3) |
| Environment work: pdfLaTeX build, fresh-clone smoke test (K) | Should (3 of 3) |
| "Publish confidently without worrying" | **Not achievable** (3 of 3). Achievable: every sentence survives a hostile reading |

**Dissent**

| Point | Positions | Chair |
|---|---|---|
| UFBA-425 numbering (A) | Seats 1 and 2: should. Seat 3: optional, only after the six-page cut exists | **Should, third in order.** It is the only step that removes "no figure on unseen data" for Stages 1 and 2. Seat 2 checked feasibility: about a day, not an hour — no scorer reads its label format, and handedness was never verified |
| Tufts box mAP 0.587 in the paper | Seat 3: drop it, it invites "why adopt it?". Seats 1 and 2 keep the override disclosed | **Keep one sentence.** A paper whose argument is "report what does not favour you" cannot remove the guard it failed. Shorten, do not delete |
| First test of Stage 3b (C) | Seat 1: should, if severity output stays. Seat 2: infeasible. Seat 3: don't | **Don't — infeasible.** Checked: the label table in `scripts/eval/lesion_localization.py` has caries and no deep-caries class |

### 3. What the chair verified

- **New, and a defect in text I wrote on 11 Oct.** The 1,200 CariesXrays images are the lesion
  detector's validation split. `scripts/yolo/train_lever_b_pooled_detector.py` writes
  `val: cariesxrays_det/images/val` and trains with `patience=25`; Ultralytics chooses `best.pt`
  on that split. `paper/main.tex` 588–589 says the detector "was kept away from" them, footnote d
  (1019–1020) says "held out from that training", and line 503 says "1,200 held out". True of
  gradients, not of selection. Found by Seat 1 and the `mle-reviewer` independently.
- The constant in the lesion-agreement tables is placed by Stages 1 and 2
  (`lesion_localization.py` 293–296). Already disclosed at `main.tex` 1326.
- The matcher differs by cohort. Already disclosed at `main.tex` 690–693 and 884.
- DENTEX numbering covers only teeth carrying a finding. Already disclosed at `main.tex`
  1087–1088 and 1488.
- `requirements.txt`: 18 version lines, all `>=`. `torch.load(..., weights_only=False)` at
  `src/classifiers.py:108` and `src/fdi_head_inference.py:90`.

Not verified by the chair: Seat 2's count that 447 of 624 flagged codes in the saved DENTEX
predictions are molars; the number of labelled-healthy teeth inside the 164 images; UFBA-425's
hash overlap with any training list, its handedness and its native aspect ratio; the rest of the
`mle-reviewer`'s engineering findings (no hash check before loading a checkpoint, a silently
skipped unreadable image, a scored-images gate that reads the label count); every acceptance
estimate.

## Decisions made

- **The answer to "are all metrics good" is no, and it is recorded stage by stage** in
  `transfer.md` §3 and `PAPER_MATERIAL.md` §8.31. No stage has evidence that is both cleanly
  external and strong. The cleanest evidence in the project is the retired gate's.
- **Nothing was run.** Three measurements are recommended. Each needs a committed
  pre-registration first, and the house rule puts that behind the user's go-ahead. Seat 2 looked
  at the tooth-type split of saved predictions while checking feasibility, so a
  pre-registration for item 1 must list that as already seen.
- **The manuscript was not edited**, as on the morning of the same day. The CariesXrays wording
  went into `docs/paper/SUBMISSION_TODO.md` §1a as row i, and the Stage 3b and Stage 4 figures
  as row j.
- **Members' proposed stop-rule bars were not adopted.** Seat 1 and Seat 2 each suggested
  thresholds for the molar-code precision and for UFBA. They belong in a pre-registration the
  user approves, not in this file.

## Open questions

- Does the user want the three measurements run? In order: flagged teeth by tooth type and label
  category on DENTEX; precision of the molar codes on Tufts; UFBA-425.
- Is UFBA-425 clean against the Kaggle and DENTEX training images? MD5 misses re-encodes.
- Carried over, unchanged: the mentor and the repo owner have not seen the detector switch or
  the headline; the grading date and the meaning of "secured"; the Tufts Drive folder; the
  Kaggle licence.

## Next steps

1. User decides on the three measurements. If yes: one pre-registration, committed before any of
   them is read, then items 1 and 2 from saved rows, then item 3.
2. Hard stop proposed by Seat 2: 31 Oct. Nothing new is measured after it.
3. Write the six-page caries-only cut with `SUBMISSION_TODO.md` §1a rows a–j.
4. Mentor and repo owner: the switch, the headline, the four questions in `transfer.md` §5.
5. Windows machine: pdfLaTeX build, `paper/paper.txt`, Docker rebuild, fresh-clone smoke test.
