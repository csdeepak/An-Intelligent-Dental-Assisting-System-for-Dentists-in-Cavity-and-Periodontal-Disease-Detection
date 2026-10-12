# Submission to-do — re-checked against `paper/main.tex`

**Status date: 11 October 2026, after the manuscript was rebuilt on the current front end**
(`RESULTS_LOG` 2026-10-11k). Line numbers in §2 are those of the *rebuilt* `main.tex`.
Rewritten from scratch earlier the same day; the 28 Aug list it replaces is in git
history (`git log -- docs/paper/SUBMISSION_TODO.md`). Every item was checked against
`paper/main.tex` as it then stood — last changed 7 Sep (`fc811ca`), 14 pages — and then
against the rebuilt file, **15 pages**. Tables are named by their LaTeX label; in the built PDF `tab:fdiset`
is Table IV, `tab:lesion` V, `tab:external` VI, `tab:cohorts` VII and `tab:leverb` VIII. Older
notes in this repo call `tab:fdiset` "Table I", from before the Related Work table was added. Items are marked done only with the evidence, because a list that
reopens closed work is how this project once lost a week (`CLAUDE.md` rule 4).

Nothing on this list needs a GPU. Items marked **LaTeX** are edits to `main.tex`; the macOS
clone can now compile it with tectonic, and the production pdfLaTeX build is on the Windows
machine.

---

## 1. Which tooth detector the paper reports — decided, and done

The pipeline's Stage-1 default changed on 11 Oct from the Tufts-only seg detector to a
multi-corpus detector, by a decision against two pre-registered ablation verdicts
(`RESULTS_LOG` 2026-10-11f, -g). That choice decides the paper's headline (2026-10-11i): with the
new detector the pipeline scores *above* the image-blind constant on DENTEX, where the old
manuscript said the constant "scored highest"; on the external cohorts nothing moves.

**The decision owner chose to rebuild the manuscript on the current front end, and it was
rebuilt the same day** (2026-10-11j for five further measurements, -k for the manuscript).

| Done | Evidence |
|---|---|
| Every table and every pipeline number re-stated from one front end and one machine | `scripts/verify_paper_numbers.py`, 191 claims against `outputs/stage1_switch/` |
| Headline rewritten: the pipeline clears the floor on its development corpus, with a detector trained there, and cannot be told from it at four external hospitals | Abstract, §Results, §Discussion, Conclusion |
| The detector's adoption over a failed registered guard stated in the paper | §Data ("Crop geometry and pre-registration"), §Limitations |
| 92.8% numbering labelled in-domain; Tufts 63.5% beside it; no figure on unseen data stated | §Results, §Limitations |
| Lever B's adoption evidence labelled as the previous front end's; current figures given as a description; the per-hospital intervals printed | `sec:leverb`, `tab:leverb` |
| Five things the first matrix had not measured: numbering taxonomy, coverage curve, Stage-4 firing on DENTEX, Stage 4 per hospital, Tufts mAP like for like | `RESULTS_LOG` 2026-10-11j |
| CariesXrays moved to the 1,200 held-out images, and that cohort leak-checked | `outputs/stage1_switch/cariesxrays_1200_leak_check.json` |
| Figures `fig_baselines`, `fig_stage2`, `fig_coverage`, `fig_boneloss` re-rendered | `scripts/figures/`, `outputs/stage1_switch/{I,J}_*` |
| Parameter counts moved to the current detector | `outputs/param_counts/param_counts.json` |
| It compiles: 15 pages, no undefined reference, one 4 pt overfull box | tectonic 0.17 on the macOS clone |

**Left over from the rebuild.**

| Item | Why it is open |
|---|---|
| **The mentor has not read the new headline** | The paper's first result changed. That is a co-author's call to accept, not an engineering one |
| A pdfLaTeX build on the Windows machine | The committed PDF is a tectonic (XeTeX) build with a Times clone; it matched pdfLaTeX's page count on the previous manuscript, but it is not the production engine |
| `paper/paper.txt` | A `pdftotext` dump of the old PDF, read by `scripts/check_text_reuse.py`. Stale; this machine has no `pdftotext` |
| One page longer than before | 15 pages against venues that cap or charge (§2 item 7) |
| The title | "What a Tooth-Level Score Cannot Tell You" still fits; "Domain Shift" in the subtitle now carries more of the argument than it did |
| Ningxia test4 under Stage 4 | The affected-tooth count there falls from 630 to 223 with the new detector, unexplained; the manuscript says so and does not offer the test4 rate as a site result |
| The Docker image | Predates the detector change |

### 1a. Defects in the rebuilt manuscript, found by the 12 Oct council

Each was checked against `main.tex` by the session chair
(`docs/session-memory/2026-10-12-publishability-council.md`). All are edits; none needs a run.

| # | Defect | Where | Fix |
|---|---|---|---|
| a | **Ningxia's role is under-disclosed.** "Never tuned against … a bounded and recorded number of times", with no count, and no word that the tooth detector was chosen with its Ningxia result in view, that Ningxia served as a veto, or that it was one of the cohorts deciding the lesion detector's adoption | 567–569; `sec:leverb` | State the number of passes and all three facts. Say the +9.28 pp lead is conditioned on that adoption: its sign is robust, its size optimistic |
| b | "A 31-point range" runs from test1 to test4, and test4's own interval includes zero | 915–917, 1536 | Anchor on test1 and test2, both separated; the range is the same 31 points |
| c | No limitation says each model is one training run, so intervals cover image sampling only | §Limitations | Add it |
| d | "Six independent cohorts" against "all five institutions" | 231, 475 | Three cohorts, one of them four hospitals |
| e | The last sentence — "this measurement cannot tell us whether it does" — is contradicted by the paper's own lesion-detector result on external data; "four capabilities" is claimed where the shipped caries stage shows two | 1547, 1556, abstract | Scope the claim to per-tooth classification; scope the capabilities to numbering and the retained gate |
| f | DENTEX is "whole-tooth boxes" in one place and "per-lesion polygons" in another | 452; 497, 688 | Say they are two subsets |
| g | The external comparisons are shown under the current detector only | §Results | Add the two-front-end table: Ningxia gate − constant +0.79 → +0.89 pp, lesion detector − constant +10.07 → +9.28 pp; only the DENTEX sign changes with the detector. Numbers are in `outputs/stage1_switch/stage1_switch_results.json` |
| h | "Almost always reported as a tooth-level score" is as uncounted as the 49-papers claim, and the paper's own benchmark table is lesion-level AP | 167; 312–314 | Soften both, or count |
| i | **The 1,200 CariesXrays images are the lesion detector's validation split, and the text says it "was kept away from" them.** No gradient came from them, but early stopping (`patience=25`) and the choice of `best.pt` did (`scripts/yolo/train_lever_b_pooled_detector.py`, `val: cariesxrays_det/images/val`). Found by the second 12 Oct council, verified against the trainer | 503; 588–589; 1019–1020 (footnote d) | Call it the lesion detector's validation split wherever the lesion detector is scored on it. It stays external for the gate and the constant, so gate − constant (−22.42 pp) is unaffected. Ningxia is then the only cohort the lesion detector neither trained nor selected on — say so in one sentence |
| j | Stage 3b (133 validation crops, no test) and Stage 4a/4b (crop-level split; 52 crops) are reported with figures no held-out set supports, and none can be built from data on hand: the 164 DENTEX images carry no deep-caries class | §System, §Results, abstract | In the conference cut, describe both stages as present and not evaluated here; no figure for either |

---

## 2. Blocking whichever front end is chosen

| # | Item | Evidence in `main.tex` | Owner |
|---|---|---|---|
| 1 | **Authors and affiliations** | `Unknown` at lines 66–70 | Authors |
| 2 | **Mandatory statements — none is present.** Ethics; data availability with licences; code availability; funding; conflict of interest; author contributions; acknowledgments with the AI-use disclosure IEEE requires | No match for any of them | Authors — **LaTeX** |
| 3 | **Bone-loss branch: cut it, or keep it re-described.** Of the three false statements, the two about its split were corrected in the rebuild — the Data section and the table caption now say evaluation splits are image-level and the bone-loss training split is not, and a limitation says its in-domain figure is not a held-out estimate. **Still as written:** "domain shift" / "did not transfer" as the reading of the external result (title, keywords, abstract area, `fig:boneloss` caption, Discussion, Conclusion), and the branch is still called bone loss although its label is "near an expert abnormality mask". `PAPER_MATERIAL.md` §8.28 | Partly corrected | Authors and mentor |
| 4 | **"No image-blind baseline in any of the 49 papers"** (205–206, 349–350). The review sheet has no such field; this was never counted. Soften to an observation, or count | Present | Authors |
| 5 | ~~Three statements against their intervals~~ (`PAPER_MATERIAL.md` §8.29) — **done in the rebuild.** "Scored highest" is gone; the Lever B result is stated as pooled with the four per-hospital intervals beside it; `tab:fdiset` has a row for each Stage-3a implementation | Rebuilt `main.tex` | — |
| 6 | ~~Reviewer-risk edits~~ — **done in the rebuild.** The Conclusion states the lesion detector's external result; §Evaluation Protocol says the constant's codes are placed by the pipeline's boxes and numbering and that its agreement moves with the front end; every pipeline row comes from one machine | Rebuilt `main.tex` | — |
| 7 | **Venue and length.** 14 pages against venues that cap or charge. Department guidelines and the grade table: `transfer.md` §5. NCC 2027 closes 16 Oct at six pages, double-blind; CONECCT 2027 was read as 15 Dec | — | Authors and mentor |
| 8 | **Compliance, account owner.** A Tufts Drive folder opens without signing in (re-checked 10 Oct) — a live licence breach. SDH `metadata/index.csv` sits beside `images/`, voiding that copy's de-identification. IRB not started. Tufts pixels in seven tracked notebooks, before the repo is ever public | `transfer.md` §4 | Account owner |
| 9 | **The Kaggle "dual-labeled" licence** — only if §1 goes to A. The current detector was trained on that set and its authors state no licence. A detector trained without it already exists (`models/13`, Tufts + DENTEX), but adopting it is a new decision with its own record | `data/README.md` | Authors |

---

## 3. Not blocking

| Item | State |
|---|---|
| Title | Unchanged: "What a Tooth-Level Score Cannot Tell You". Under option A it may no longer fit |
| Abstract form | Narrative by an earlier instruction; a medical journal will want it structured. A team call |
| One research question and 2–4 hypotheses in the Introduction | Implied, not stated |
| References | 27 cited, 83 in `source.bib`. Thin on calibration, selective prediction and reporting guidelines |
| "external validation" → "external testing" | 8 occurrences, 0 of the replacement |
| Terms defined at first use | FDI, mAP, ECE and coverage are not all defined |
| Dataset-flow diagram | Absent; the dataset table exists |
| Similarity check | Internal check done (`scripts/check_text_reuse.py`); the institutional one is pending |
| University-format and venue-format copies | Not made |

---

## 4. Done — do not reopen

| Item | Evidence |
|---|---|
| Dataset table | `tab:data`, line 455 |
| Clinical interpretation section | line 1303 |
| DENTEX and Ningxia licences | recorded 4 Sep, `transfer.md` §2.7 |
| Broken DOIs | resolved 2 Sep, `outputs/citation_audit/` |
| Citation audit | `scripts/audit_citations.py`; seven errors found and fixed |
| Confidence intervals, including Ningxia periodontitis and detection quality | `model_metrics.md` "Confidence intervals"; `RESULTS_LOG` 2026-09-04l |
| Lever B folded into the manuscript | 4 Sep, `RESULTS_LOG` 2026-09-04i |
| Interval on the headline F1 gap; Lever B per hospital; the lesion detector on the `tab:fdiset` metric | Measured 11 Oct, `RESULTS_LOG` 2026-10-11. **Measured, not yet in `main.tex`** — item 5 above |
| "Reproduce the periodontal experiment" | Closed as moot: the figure reproduces, and it is not a held-out estimate of a periodontal label (`RESULTS_LOG` 2026-10-10). Do not finish the 565-crop pull |
| Stage-4 wording in the report and the demo | Report schema 1.2, `RESULTS_LOG` 2026-10-11b |
| The pipeline under the current front end, with intervals | `RESULTS_LOG` 2026-10-11g, -h, -i, -j |
| The manuscript rebuilt on the current front end | `RESULTS_LOG` 2026-10-11k |

---

## 5. The one item that most changes the grade

**A reader study.** The protocol is written and runnable the day IRB clears: 100 images, two or
three dentists, the same scorer as every machine arm, the constant included. Without it the
paper rests on methodology against modest numbers. IRB is the longest lead time of anything
open, and it has not been started.
