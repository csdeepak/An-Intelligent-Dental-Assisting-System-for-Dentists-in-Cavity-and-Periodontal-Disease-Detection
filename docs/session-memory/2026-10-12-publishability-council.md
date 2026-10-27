# 2026-10-12 — Council: is anything left to implement, and will this be published?

**Session goal:** the user asked, setting paper writing and venue choice aside, whether anything
is left on the implementation side, and for a strict opinion on whether the work will be
published under the college's rules. Asked for a council.

Run on the macOS clone. No model was run, no code and no manuscript text changed. Documentation
only. The working tree still carried the uncommitted manuscript rebuild of 11 Oct.

## What was done

### 1. Facts first

Re-read `transfer.md` §5 (grade table, department guidelines of 10 Oct, venue table), the
rebuilt `paper/main.tex`, `docs/paper/SUBMISSION_TODO.md` and the entries 2026-10-11f to -k. Put
the claims, their numbers, thirteen facts a reviewer could press on and ten candidate items
(A–J) in one brief (session scratchpad).

### 2. The council

Three independent read-only members (`Plan` agents); none saw another's report.

| Seat | Lens | Model |
|---|---|---|
| 1 | The strict reviewer | Opus |
| 2 | Experimental rigour and the remaining implementation | Opus |
| 3 | Compliance, the college rules and delivery | Sonnet |

**Consensus (3 of 3)**

| Question | Verdict |
|---|---|
| Is any new model, default or locked-cohort pass needed? | **No.** Freeze the pipeline, the default and Ningxia |
| NCC 2027 (16 Oct, six pages, double-blind) | **Not realistic** — under 10% |
| A six-page caries-only cut at a CONECCT-class Indian IEEE conference | **Publishable, not as it stands.** Estimates 35–45%, 45–60%, 50–65% per submission |
| A journal at JBHI's level | Unlikely: under 5%, 5–10%, 10–20% |
| Bone-loss branch | **Cut it from the paper; do not score it further** |
| Reject option (C), lesion-detector calibration (D), Kaggle-free detector as a new default (E), reader study now (G), public code release before a blind review (I) | **Don't** |
| Cross-domain numbering on UFBA-425 (A) | **Should, optional** — the one new measurement worth running; not needed for the conference cut |

**Dissent**

| Point | Positions | Chair |
|---|---|---|
| A second training seed of the lesion detector (B) | Seat 1: should, and must for a journal. Seats 2 and 3: don't now — half the budget, a 21st Ningxia pass, and a "which seed ships" fork | **Don't now.** Say "one training run" in the Limitations, which the manuscript does not. Decide again for a journal revision; if run, score it on DENTEX and CariesXrays only |
| The claim about the 49 surveyed papers (H) | Seats 1 and 2: must count, or delete. Seat 3: don't count, soften | **Soften now, count if a journal is the target.** All three agree it cannot stand as written |

### 3. What the chair verified

Checked against `paper/main.tex` rather than taken on a member's word. All of these are in the
manuscript rebuilt on 11 Oct, and the first three are sentences I wrote or left in place:

- **Ningxia is under-disclosed in the manuscript.** Lines 567–569 say "never tuned against, and
  evaluated a bounded and recorded number of times". The manuscript gives no count, and does not
  say that the tooth detector was chosen with its Ningxia result in view, that Ningxia was used
  as a veto, or that Ningxia was one of the cohorts that decided the lesion detector's adoption.
  The results log says all of it (2026-10-11g); the paper does not. Seat 2's reading is right:
  the +9.28 pp is adoption-conditioned, its sign is robust and its size is optimistic.
- **"A 31-point range" is anchored on a hospital whose own interval includes zero** (lines
  915–917: test1 to test4). test1 to test2, both separated, gives the same 31 points.
- **No limitation says "one training run per model".**
- "Six independent cohorts" (line 231) and "all five institutions" (line 475) cannot both be
  right; the honest count is three cohorts, one of them four hospitals.
- The closing sentence, "this measurement cannot tell us whether it does" (line 1556), sits
  awkwardly beside the paper's own lesion-detector result, which the same measurement does
  separate from the constant on external data. "Four capabilities" is likewise claimed for a
  system whose shipped caries stage shows two.
- DENTEX is described as carrying "whole-tooth boxes" (line 452, the lesion detector's training
  subset) and "per-lesion polygons" (lines 497, 688, the scored subset). Both are true of
  different subsets; the text does not say so.
- Seat 2's arithmetic: with a standard error of about 2.3 pp, a Bonferroni bound for 20 looks
  leaves the Ningxia lesion-detector lead at about +2.3 pp. Reproduced.

Seat 2 also proposed something no member was asked for and which needs no run: **a table of the
external comparisons under both front ends.** Gate minus constant on Ningxia is +0.79 pp before
the detector change and +0.89 after; lesion detector minus constant is +10.07 and +9.28. Only
the DENTEX sign flips. That is the strongest available answer to the override, and the numbers
are already in `outputs/stage1_switch/stage1_switch_results.json`.

Not verified by the chair: any acceptance rate — the percentages above are members' judgement,
not data; the indexing of either conference; CONECCT's page limit and dates; Seat 3's inference
that NCC and CONECCT cannot both be tried with the same paper.

## Decisions made

- **Nothing was edited in the manuscript.** The user asked for an opinion. The defects found are
  listed in `docs/paper/SUBMISSION_TODO.md` so they are not lost.
- **The verdict on implementation is "stop".** Three members, three lenses, one answer: no new
  model, no third default, no further pass over Ningxia. The earlier councils said the same
  before the detector switch; this one says it after.
- **The honest answer to "will it be published" is conditional.** As it stands — 15 pages, no
  authors, no statements, a co-author and a mentor who have not seen the new headline — it is
  not submittable. As a six-page caries-only cut with the corrections, about even odds at a
  CONECCT-class conference per submission. The college's S grade then turns on two things
  nobody has answered: the date by which publication must be "secured" and what that word
  means, and whether the edition's proceedings are indexed.

## Open questions

- The grading date, and whether "secured" means submitted, accepted or published. Open since
  6 Sep.
- Whether the mentor and the repo owner accept the detector switch and the new headline.
- Whether UFBA-425 overlaps any training corpus of the default detector. It must be hash-checked
  before item A is run.
- Whether any external caries cohort exists that this project has never scored. If one does, it
  is worth more than anything on the list.

## Next steps

1. The user commits the 11 Oct manuscript rebuild, then tells the mentor and the repo owner about
   the switch and the headline, and asks the four questions in `transfer.md` §5.
2. Restrict the Tufts Drive folder. Minutes of work, and it blocks a truthful data statement.
3. Write the six-page caries-only cut, with the corrections in `SUBMISSION_TODO.md` §1a.
4. Optional, after the cut exists: item A, pre-registered as a description.
5. Target CONECCT 2027; confirm its dates, page limit and indexing when the call opens.
