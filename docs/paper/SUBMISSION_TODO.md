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

**14 Oct, later: rows a–i and l–n are applied too** (`RESULTS_LOG` 2026-10-14c); row j needs
nothing (Stage 3b carries no figure) and row k's sentence left with the Stage-4 rewrite. Only
§2's items remain, plus the cut itself.

**14 Oct: rows o–r, and §2 item 3, are applied to the 15-page `main.tex`** (`RESULTS_LOG`
2026-10-14b): Stage 4 is described by its label, reported as three runs with the 248/1017 and
shared-jitter disclosures, and Fig. 5 is the held-out figure. The six-page cut must carry them.

**14 Oct, late night: row o is superseded in part.** Stage 4b now has a registered test result
(`RESULTS_LOG` 2026-10-14d, `PAPER_MATERIAL.md` §8.40): retrained on the true overlap bands, it does
not beat an image-blind tooth-position prior. `main.tex` states it in the protocol's §8 wording,
with the contrast-trained head's own figure, and no longer says "not evaluated". Row o's "no figure"
no longer holds; its other point, no severity claim, does. The cut carries the sentence or drops
Stage 4b.

**14 Oct, late night: a publishability council** (`RESULTS_LOG` 2026-10-14e, `PAPER_MATERIAL.md`
§8.41). Applied to the 15-page text: the test count, Table IV's in-domain caption, "had all
failed", a perceptual-hash sentence, the CariesXrays split by image, and the Ningxia interval as
fixed-site. The text is now 16 pages; the 16th holds four references. **For the cut:** build the
abstract around the shipped system — its DENTEX development headline is the retired gate's — and
drop "Domain Shift" from the title and keywords and the periodontal opening.

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
| j | Stage 3b (133 validation crops, no test) and Stage 4a/4b (crop-level split; 52 crops) are reported with figures no held-out set supports, and none can be built from data on hand: the 164 DENTEX images carry no deep-caries class | §System, §Results, abstract | In the conference cut, describe both stages as present and not evaluated here; no figure for either. **Superseded for Stage 4 on 12 Oct: the decision owner keeps the branch in the paper — §2 item 3** |
| k | "There is no second annotated periodontal corpus in this project" — two exist: the Ningxia periodontitis training split (2,000 images, locked by the house rule) and BRAR (1,104 patients, CC BY 4.0) | 1273–1275 | "None was used here", and name both |
| l | **Numbering on unseen data is now measured** (`RESULTS_LOG` 2026-10-12b). UFBA-425, neither model trained on it: 44.5% [42.39, 46.62] end to end, recall 66.6%, on the square export as distributed; 77.2% [75.19, 79.14] and 95.6% with the images widened to a panoramic shape | §Limitations ("we have none on unseen data", ~1497); §Results, numbering | Replace the sentence with both figures, the registered one first; say it is one corpus, a single pass, an aspect-distorted re-export, and that the second figure assumes an aspect ratio not verified for these files. Say in the same place that the adopted detector is ahead of the one it replaced there, +23.86 pp [+21.96, +25.77] |
| m | The constant's placement is now measured: on Tufts 92.0% [89.58, 94.06] of its codes sit on a true first or second molar and it reaches 81.7% [77.72, 85.35] of them | ~1320–1330; every lesion-agreement table | Call it a constant placed by the pipeline's boxes and numbering wherever it is scored on lesion agreement, with both figures. "Image-blind" stays for the FDI-set F1 constant only |
| n | The sentence "cannot score well by reproducing a prior over tooth positions" survived its registered rule | 447–449 | Keep it, and put beside it: 624 flagged codes, 43.9% carious, 71.6% molars, against the constant's 1,312, 21.8% and 100%. Add to the Limitations that the scored DENTEX cohort has no tooth labelled healthy |
| o | **Stage 4b's labels were image contrast, not mask overlap** (`RESULTS_LOG` 2026-10-13d). The severity head is listed in the system table and described as grading severity | 384–388; 414 | "A severity head is present in the released pipeline; its training labels were a contrast stand-in, not the expert mask, and it is not evaluated here." No figure, and no "overlap-extent severity" anywhere |
| p | **Stage 4a must be reported as three runs.** The draft in §2 item 3 gives one run's 27.5% with an interval that covers radiograph sampling only, and omits the false flags the pre-registration (§8) requires beside any sensitivity | wherever Stage 4 is described | *"Stage 4 is not a periodontal detector. It is a ResNet18 that flags teeth whose crop overlaps an expert-marked abnormality on Tufts. The model first shipped reported 83% validation sensitivity from a crop-level split; on 125 test radiographs it had not seen it found 3.4% of such teeth. Retrained with the split made by radiograph, three runs of one recipe found 11.0%, 16.5% and 27.5% of such teeth on 143 test radiographs, at 95.9–98.6% specificity, with about seven flags in ten false. The runs rank teeth alike (ROC area 0.68–0.69) and differ in operating point; the ranking is separated from a tooth-position prior on average precision and not on ROC area. It was scored on annotated tooth boxes, not on the pipeline's detections, and has no external figure. The three runs share one pre-computed set of jittered training crops, so their spread understates training variance, and every interval covers the sampling of radiographs only. One of the 143 test radiographs is a re-rendered copy of a training radiograph; it holds no positive tooth. We make no periodontal claim."* (Two sentences added 14 Oct 2026, RESULTS_LOG 2026-10-14.) Longer than the earlier draft; cut the history sentence first if space is short |
| q | "Under a pre-registered protocol" needs its limits: the protocol document was committed before training; the scripts entered version control eleven minutes after the test pass; adoption was decided with the test result in view | same paragraph; §Limitations | One clause: "under a protocol written down before training" — and do not call the adoption pre-registered |
| r | Any sentence that the Tufts test radiographs are unseen by every model in the pipeline is false of Stage 4b (two training radiographs, one validation radiograph) | §Data, if carried over from the pre-registration | Say it of the detector, the numbering head and the retrained Stage 4a only |

---

## 2. Blocking whichever front end is chosen

| # | Item | Evidence in `main.tex` | Owner |
|---|---|---|---|
| 1 | **Authors and affiliations** | `Unknown` at lines 66–70 | Authors |
| 2 | **Mandatory statements — none is present.** Ethics; data availability with licences; code availability; funding; conflict of interest; author contributions; acknowledgments with the AI-use disclosure IEEE requires | No match for any of them | Authors — **LaTeX** |
| 3 | **Bone-loss branch — DECIDED 12 Oct by the decision owner: it stays, re-described** (`RESULTS_LOG` 2026-10-12c, `PAPER_MATERIAL.md` §8.33). It must not say: "detects periodontal bone loss"; 0.923 as performance; "domain shift" / "did not transfer"; "two independent external datasets agree"; any severity or stage claim; the keyword "periodontal bone loss". Draft paragraph, 79 words, from the council: *"Stage 4 ships in the pipeline but is not evaluated here as a periodontal detector. It is a ResNet18 trained on Tufts tooth crops labelled by overlap with an expert abnormality mask, not by periodontal bone loss. Its in-domain score comes from a crop-level split and is not a held-out estimate, so we do not report it. On 736 Ningxia periodontitis images it flagged 2.17% of affected teeth (153/7,049). This is consistent with a label mismatch, which we did not test; we make no periodontal claim."* **The held-out score was run on 13 Oct (`RESULTS_LOG` 2026-10-13): sensitivity 7.6% (72 of 946) [5.19, 10.47], specificity 98.7% [98.43, 98.88], on 821 Tufts radiographs outside training — against 83.1% and 99.5% on the crop-level validation set.** That replaces the draft above. Draft with the figure: *"Stage 4 ships in the pipeline but is not a periodontal detector. It is a ResNet18 trained on Tufts tooth crops labelled by overlap with an expert abnormality mask. Its reported validation sensitivity, 83%, came from a crop-level split in which every validation radiograph also supplied training crops. Scored once, under a pre-registered protocol, on 821 Tufts radiographs that supplied none, it found 7.6% of such teeth (72/946; 95% CI 5.2–10.5) at 98.7% specificity. On 736 Ningxia periodontitis images it flagged 2.17% of affected teeth. We make no periodontal claim."* Every place that sets 0.923 beside an external figure (abstract, `fig:boneloss`, Discussion, Conclusion) needs the held-out figure between them. **Added 13 Oct, evening (`RESULTS_LOG` 2026-10-13b): the model was retrained with the split done by radiograph — test sensitivity 27.5% (50 of 182) [18.31, 37.98] at 95.9% specificity for the seed fixed in advance; 16.5% and 11.0% for the other two; above the shipped model and above a tooth-position prior on all three. It is not adopted.** One sentence to add after "…at 98.7% specificity.": *"Retrained with the split made by radiograph, the same architecture found 27.5% of such teeth on 143 test radiographs (95% CI 18.3–38.0) at 95.9% specificity, and 11.0–27.5% across three seeds."* **Adopted 13 Oct, night (`RESULTS_LOG` 2026-10-13c): the pipeline now ships the retrained model.** The paragraph, rewritten for that: *"Stage 4 is not a periodontal detector. It is a ResNet18 that flags teeth whose crop overlaps an expert-marked abnormality on Tufts. The model first shipped reported 83% validation sensitivity from a crop-level split in which every validation radiograph also supplied training crops; on 125 test radiographs it had not seen it found 3.4% of such teeth. Retrained with the split made by radiograph, under a pre-registered protocol, the shipped model finds 27.5% (50/182; 95% CI 18.3–38.0) at 95.9% specificity on 143 test radiographs, and 11.0–27.5% across three seeds. It has no external figure; on 736 Ningxia periodontitis images its predecessor flagged 2.17% of affected teeth. We make no periodontal claim."* Also to change in `main.tex`: the Stage-4 row and description in §System; the data table's bone-loss split; `fig:boneloss` and its caption; and one Limitations line that the severity stage has no held-out test. **The row as it stood:** Of the three false statements, the two about its split were corrected in the rebuild — the Data section and the table caption now say evaluation splits are image-level and the bone-loss training split is not, and a limitation says its in-domain figure is not a held-out estimate. **Still as written:** "domain shift" / "did not transfer" as the reading of the external result (title, keywords, abstract area, `fig:boneloss` caption, Discussion, Conclusion), and the branch is still called bone loss although its label is "near an expert abnormality mask". `PAPER_MATERIAL.md` §8.28 | Partly corrected | Authors and mentor |
| 4 | **"No image-blind baseline in any of the 49 papers"** (205–206, 349–350). The review sheet has no such field; this was never counted. Soften to an observation, or count. *(13 Oct: if counted, do it as a logged search — queries, dates, hit counts, screening reasons — over more than one database; PubMed alone does not cover the IEEE and arXiv dental-AI papers. Softening is one sentence and needs no tool.)* | Present | Authors |
| 5 | ~~Three statements against their intervals~~ (`PAPER_MATERIAL.md` §8.29) — **done in the rebuild.** "Scored highest" is gone; the Lever B result is stated as pooled with the four per-hospital intervals beside it; `tab:fdiset` has a row for each Stage-3a implementation | Rebuilt `main.tex` | — |
| 6 | ~~Reviewer-risk edits~~ — **done in the rebuild.** The Conclusion states the lesion detector's external result; §Evaluation Protocol says the constant's codes are placed by the pipeline's boxes and numbering and that its agreement moves with the front end; every pipeline row comes from one machine | Rebuilt `main.tex` | — |
| 7 | **Venue and length.** 14 pages against venues that cap or charge. Department guidelines and the grade table: `transfer.md` §5. NCC 2027 closes 16 Oct at six pages, double-blind; CONECCT 2027 was read as 15 Dec | — | Authors and mentor |
| 8 | **Compliance, account owner.** A Tufts Drive folder opens without signing in (re-checked 10 Oct) — a live licence breach. SDH `metadata/index.csv` sits beside `images/`, voiding that copy's de-identification. IRB not started. Tufts pixels in seven tracked notebooks, before the repo is ever public | `transfer.md` §4 | Account owner |
| 9 | **The Kaggle "dual-labeled" licence** — *this row was conditional on §1 going to A; it did, on 11 Oct, so it applies.* The current detector was trained on that set and its authors state no licence. A detector trained without it already exists (`models/13`, Tufts + DENTEX), but adopting it is a new decision with its own record | `data/README.md` | Authors |

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
| **Reporting checklist (CLAIM 2024)** | Not started, and not tracked here until 13 Oct. `docs/research/PUBLICATION_STRATEGY.md` names it the primary checklist for this paper (R12, P2.5), with STARD 2015 and TRIPOD+AI as alternatives by framing. A conference may not ask for it; medical-imaging journals increasingly do. No tool was found that fills it — it is a pass over the manuscript against the published items |
| A referee-style read of the six-page cut before the mentor sees it | Not done; the cut does not exist yet. A nine-dimension rubric skill is installed on the macOS clone for it (`docs/session-memory/2026-10-13d-ecc-skills-council.md`). It adds a structure, not a guarantee: the councils of 10–12 Oct found defects a–n without it |

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
