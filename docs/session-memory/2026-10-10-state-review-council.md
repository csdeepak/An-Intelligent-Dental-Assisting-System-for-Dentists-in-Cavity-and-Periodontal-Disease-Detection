# 2026-10-10 — State-review council: what is done, what is next, and what the review found

**Session goal:** read `transfer.md` and every README for the current state, then council what
should happen next — 34 days after the last council, 16 days before the ISBI 2027 deadline.

Run on the **macOS clone** (gunadeep19). No model was trained or evaluated, no GPU was rented,
nothing was committed or pushed.

## What was done

### 1. Facts first

- Read `transfer.md`, the root `README.md`, the 21 other in-repo READMEs, the last two session
  files, `docs/EXTERNAL_DRIVE.md`, `docs/paper/SUBMISSION_TODO.md` and `MASTER_PLAN_2026H2.md`
  §5 and §7.
- **This clone was 4 commits behind `origin/main`** — the four 7 Sep commits (bone-loss crops
  recovered, rebuild root cause, Docker rebuild, manuscript limitation reworded). Fast-forwarded
  `39c0445 → fc811ca` with `git merge --ff-only origin/main`: no network, nothing deleted, tree
  clean beforehand. It was done so that the log entries below could be appended without a
  conflict. Undo: `git reset --hard 39c0445`, after discarding this session's edits.
- **Nothing has been committed anywhere since 7 Sep** — 33 days.
- Health on this Mac (`/opt/anaconda3/bin/python3`, torch 2.2.0, numpy 1.26.4): `pytest`
  174 passed; `verify_paper_numbers.py` 127 of 127; `verify_invariants.py --skip-slow` all hold.
- Checked live on 10 Oct:
  - **The Tufts Drive folder still opens without signing in** (HTTP 200, page title
    "tufts – Google Drive"). First recorded 26 Aug; used for a shared-link pull on 7 Sep.
  - **ISBI 2027** (official author page, modified 1 Oct): deadline 26 Oct; all technical content
    in 4 pages, an optional 5th ($200) for ethics, acknowledgments and references; single-blind;
    **in person only, Lausanne, 25–28 May 2027 — a paper not presented in person is withdrawn
    from the proceedings**; ethics and conflict-of-interest statements are mandatory; IEEE
    requires AI-generated content to be disclosed in the acknowledgments.
  - **IEEE JBHI** (embs.org): **14-page limit** including supplementary; mandatory charges past
    8 pages — $250 a page for pages 9–10, $350 a page from 11. Fourteen pages cost $1,900.
  - **Computers in Biology and Medicine**: on hold with Clarivate since April 2024, Web of
    Science coverage discontinued 17 Nov 2025; reported still in Scopus by a third-party post
    (6 Jan 2026). Scopus's own source list was not checked.
- Found on this Mac: all **1,000 original landscape Tufts radiographs** (1615×840) at
  `_repo_archive/datasets_workspace/Radiographs/`. `transfer.md` §8 said they were "confirmed
  absent from every machine checked". There is no LaTeX here, and the Docker daemon was not
  running.

### 2. The council

Three independent, read-only members (`Plan` agents). Seat 1 was first seated on Fable and failed
on a usage-credit error; it was re-seated on Opus. The brief lived in the session scratchpad and
is not kept.

| Seat | Lens | Model |
|---|---|---|
| 1 | Venue and calendar | Opus |
| 2 | Adversarial reviewer | Opus |
| 3 | Execution, compliance, repo integrity | Sonnet |

**Consensus**

| Question | Verdict |
|---|---|
| ISBI 2027 | **No-go**, 3 of 3. In-person-only attendance, a 4-page cap, 16 days, no LaTeX on this clone, and it cannot run beside the journal paper. Flips only if the mentor confirms a funded, named presenter by about 15 Oct. |
| Is the manuscript feature-complete? | **No** (seats 2 and 3; seat 1 independently lists the missing statements). The 6 Sep verdict is withdrawn. |
| Journal route | Journal first, **cut to about 8 pages** — seat 1 for cost and retargeting, seat 2 because the caries story is the paper. Strike Computers in Biology and Medicine unless Scopus alone is enough. |
| Tufts Drive folder | Restrict it now, do not delete it; fetch anything still needed with a signed-in account. |
| Scope guard | No GPU, no new lever, no reader study, no mirror-crop test, no public repo, no "just in case" ISBI draft. |

**Dissent**

| Point | Positions | Chair |
|---|---|---|
| The bone-loss branch | Seat 2: cut it from the paper and refuse all further bone-loss work. Seat 3: demote it, log the audit, optionally re-measure on radiographs never used in training. Seat 1 did not see the finding. | Not settled here. It is the authors' and the mentor's call, because the capstone title names periodontal disease. What is settled: the false statements go either way. |
| Survey paper | Seat 1: the one legitimate second submission, if it counts. Seat 2: scope creep. | Ask the mentor whether it counts. Start nothing. |
| ISBI flip date | 14, 15 or 16 Oct. | 15 Oct. |

### 3. What the chair verified, and one finding that outweighs the rest

Seats 2 and 3 independently reported that the bone-loss validation set is not held out. Recomputed
from the manifests, not taken on their word. Full numbers in `RESULTS_LOG` 2026-10-10.

- **The split is crop-level.** All 143 validation radiographs also supply training crops. 46 of
  the 59 validation positives share their tooth with a training positive — the clean crop and
  the jittered crop of one tooth on opposite sides. The training notebook's saved output says
  "No val split found on disk; created a 20% validation split from train/."
- **The label is not periodontal bone loss.** A crop is positive when it overlaps a Tufts expert
  abnormality mask. Every positive comes from 41 radiographs whose expert descriptions are
  apical lesions, sclerosis and cysts. Of the three Tufts radiographs that are described as
  periodontal bone loss or periodontal disease, none supplies a positive crop.

Also verified by the chair:

- `main.tex` contains none of: ethics, data availability, code availability, funding, conflict of
  interest, author contributions, acknowledgments. The author block is `Unknown`.
- The Conclusion (l.1389–1417) never mentions Lever B, the paper's one positive result.
- In the lesion-localisation metric the constant is placed with the pipeline's own detector boxes
  and FDI head (`scripts/eval/lesion_localization.py` l.293–296). `main.tex` l.604–605 says "the
  radiograph is never read" and the Metrics section does not qualify it.
- Lever B against the constant, per hospital, from the saved outputs: test1 0.462 vs 0.446
  (+1.6 pp), test2 0.576 vs 0.407, test3 0.494 vs 0.377, test4 0.430 vs 0.323. The manuscript
  reports only the pooled +10.2 while recommending per-institution reporting. No per-hospital
  intervals exist yet.
- `docs/paper/SUBMISSION_TODO.md` is stale in both directions.

Reported by a member and **not** verified by the chair: seat 2's line-level points on calibration
scope (l.213–215, l.1408–1411, numbering confidence), stale Discussion lines (l.1212–1215,
l.1347–1349), "237 crops, not 711 teeth" at l.1379, and audit notes printing in `main.bbl`.

### 4. Documents changed (uncommitted)

| File | Change |
|---|---|
| `docs/results/RESULTS_LOG.md` | New entry 2026-10-10 — the bone-loss split and label audit |
| `docs/results/model_metrics.md` | Stage 4a: caveat block above the table |
| `docs/results/PAPER_MATERIAL.md` | §6.3 correction note; new §8.28; two blocking items in §9; a "superseded" note on the bone-loss calibration item |
| `transfer.md` | Header note; §1, §2.5, §2.7, §3, §4, §5, §8 corrected in place |
| `README.md` | "Image-level everywhere" corrected; limitation row 14; log entry count 138 → 139 |
| `docs/paper/SUBMISSION_TODO.md` | Corrective banner only |

`paper/main.tex` was **not** edited: it cannot be compiled on this clone, and the largest change
it needs is a decision that belongs to the authors and the mentor.

### 5. Later the same day — the department's publication guidelines

The user supplied the CSE Department's guidelines for capstone publications: prefer high-rated
conferences; prefer ones held in India and indexed in Scopus / WoS; a conference outside India
needs University approval before submission or any payment; reimbursement is possible for
conferences that meet the criteria; verify the indexing of the specific edition. They are
recorded in `transfer.md` §5, with a pointer in `CLAUDE.md` §6.

Two India conferences were then checked on their own sites:

- **NCC 2027** — 33rd edition, IISc Bengaluru, 17–20 Feb 2027; deadline 16 Oct 2026,
  notification 24 Dec 2026; six pages, IEEE format, double-blind.
- **IEEE CONECCT 2027** — 13th edition, Bengaluru, 29–31 Jul 2027; home-page timeline reads
  deadline 15 Dec 2026, notification 15 Feb 2027. Its call-for-papers page returned 404.

The venue advice in `transfer.md` §5 was updated accordingly: a six-page, caries-only conference
paper first, the journal as its extended version afterwards. That update is the chair's and was
not put back to the council.

## Decisions made

- **Withdraw "feature-complete".** The 6 Sep council judged the manuscript on whether it compiled
  and whether its numbers traced. Both are still true. Neither tests whether a stated split was
  the split used, or whether a label means what its name says.
- **Do not finish the 565-crop pull, and do not run calibration, a PR sweep or intervals on the
  bone-loss validation set.** They were "unblocked" on 7 Sep. On a set that shares every
  radiograph with training they would produce precise numbers about a leaked split.
- **Do not edit the manuscript from this clone.** No LaTeX, so nothing could be compiled or
  checked; and cutting versus re-describing the branch is not an engineering decision.
- **ISBI 2027: no-go unless the mentor confirms funded attendance by 15 Oct.** The in-person rule
  decides it. An accepted paper nobody presents is withdrawn.
- **Fast-forwarded the clone without being asked.** Rule 1 required a log entry, and the log had
  changed upstream. The merge was local and deleted nothing.
- **Left `_repo_archive/` where it is.** On this clone it sits inside the working tree with 20
  tracked files, while `CLAUDE.md` rule 3 and the README described a sibling outside git. Moving
  it is a rule-3 operation, so the folder stays.
- **Corrected `CLAUDE.md` to match the repo, at the user's request, later the same day.** Rule 3
  now says the archive is at the repo root and is protected only by `.gitignore`; the rule-4
  weights exception now names `models/14` and `models/16` and the three files actually over
  50 MB; the intro names the lesion detector; §5's dead pointer to `transfer.md` §6 is gone; §6
  points at `transfer.md` §3 as the work list and no longer says two checkpoints are Drive-only.
  Not changed: `_repo_archive/ARCHIVE_MANIFEST.md` and the root `README.md` still say "sibling".
- **Corrections to this session's own work.** The council brief said every commit since 4 Sep was
  the owner's; three 6 Sep commits are gunadeep19's. Seat 3 caught it.

## Open questions

- **By what date must the publication be secured, and does that mean submitted or accepted?**
  Nothing in the repo says. It decides the venue.
- **Scopus or SCI(E)?** It decides whether Computers in Biology and Medicine is usable at all.
- **Does the bone-loss branch stay in the paper?** And if it does, is a leak-free re-measurement
  on never-used Tufts radiographs worth pre-registering?
- **How inflated is 0.9233?** Unmeasured. Stage 4b uses the same crops and was not audited.
- **Does Stage 4a fire on DENTEX periapical-lesion teeth?** The label audit predicts it should.
  Untested.
- **Who owns the Tufts Drive folder, and has every team member signed the Tufts release form?**
- **Is anyone able to travel to Lausanne in May 2027, and is there money for page charges?**
- *Oral Radiology* and *Dentomaxillofacial Radiology*: limits, indexing and review times were
  proposed from memory and not checked.
- The survey paper: status unknown since mid-August, and absent from `transfer.md`.
- The 7 Sep sessions left no session-memory file.

## Next steps

1. **Today — send the owner and the mentor three things:** the bone-loss finding (`RESULTS_LOG`
   2026-10-10), the venue facts (`transfer.md` §5), and that the Tufts folder is still public.
   Ask the mentor the first two open questions and whether there is money for travel or charges.
2. **Today — the Drive owner restricts the Tufts folder.** Restrict, do not delete.
3. **This week — owner and mentor decide:** cut the bone-loss branch or keep it re-described;
   commit the venue; fix the author order.
4. **Doable on this Mac now, needing nobody:** per-hospital paired intervals for Lever B and an
   interval on the headline F1 gap, both from saved artefacts with no inference; draft the text
   of the mandatory statements; count or soften the "49 papers" claim; rewrite
   `SUBMISSION_TODO.md` against `main.tex`.
5. **Owner, on the machine with LaTeX — apply to `main.tex`, then recompile and re-run
   `verify_paper_numbers.py`:**
   - l.23 `\documentclass[conference]` → the committed venue's class;
   - l.49–53 the author block;
   - l.85–86, l.1405–1406 the 0.923-against-external sentences;
   - l.456–458, l.467–468, l.491–499 "image-level throughout" and 700/150/150 as the bone-loss
     split;
   - l.1111–1163 the periodontal subsection and its "under domain shift" caption;
   - l.604–605 and the Metrics section: say how the constant is placed in the localisation
     metric;
   - l.906–934 add Lever B per hospital; l.1389–1417 put Lever B in the Conclusion;
   - l.178–182, l.317 the "49 papers" absence claim;
   - add ethics, data and code availability, funding, conflict of interest, contributions and
     acknowledgments with the AI-use disclosure.
6. **Then** cut to about 8 pages in the venue's template and submit.
7. **Not before a decision in step 3, and only with a pre-registration:** the leak-free bone-loss
   re-measurement.
