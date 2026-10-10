# Submission to-do — cross-verified against the repository

**Status date: 28 August 2026.** Every item below was checked against the actual repository
before being marked. Items already satisfied are marked **DONE** with the evidence, because a
to-do list that reopens closed work is how this project previously lost a week
(`CLAUDE.md` rule 4).

> **Re-checked against `paper/main.tex` on 10 Oct 2026 — this list is stale in both directions.**
> It has not been rewritten; read it with these corrections
> (`docs/session-memory/2026-10-10-state-review-council.md`).
>
> - **Already done, still listed as open below:** the dataset table (Table I); the clinical
>   interpretation subsection; the DENTEX and Ningxia licences (recorded 4 Sep, `transfer.md`
>   §2.7); the "22 broken DOIs" blocker (resolved 2 Sep).
> - **Open and blocking, as listed:** authors and placeholders; ethics, funding, conflict of
>   interest, contributions and acknowledgements; data and code availability; the claim that
>   none of the 49 surveyed papers reports an image-blind baseline. Add the AI-use disclosure
>   IEEE requires in the acknowledgments.
> - **New blockers that are not on this list:** the bone-loss split and label
>   (`RESULTS_LOG` 2026-10-10 — it also overturns this file's "UNBLOCKED" banner below, since the
>   experiment is not worth reproducing further); and the venue facts in `transfer.md` §5.

Legend: **DONE** · **PARTIAL** — some of it exists, the gap is named · **OPEN** — not started ·
**BLOCKED** — cannot be done with the data on this machine.

---

## 🔴 Technical / Scientific

### Reproduce the periodontal experiment — **UNBLOCKED 7 Sep 2026 (was BLOCKED)**

> The crops were recovered from the project Drive, jittered ones included, and the frozen
> checkpoint reproduces the reported diseased-class figure **exactly: 49/59, sensitivity 0.8305**
> (`RESULTS_LOG` 2026-09-07). The table below is the 27 Aug state and its "cannot be rebuilt"
> reasoning was about *regenerating* the crops from source, which remains true and is now beside
> the point. The 0.40 rebuild was a defective reconstruction (wrong box convention — 187/187
> crops match bit-for-bit once corrected, `RESULTS_LOG` 2026-09-07b). Full macro-F1 verification
> awaits the remaining 565 negative crops. The *selected-maximum* caveat is unaffected and stands.

| sub-item | status |
|---|---|
| Save random seeds | DONE going forward (`seed=42` fixed in all builders) |
| Save exact crop coordinates / jitter | **BLOCKED for the existing result** |
| Save checkpoint / model version | DONE — hash-pinned in `verify_invariants.py` |
| Save predictions + eval scripts | PARTIAL — scripts saved, per-item predictions not dumped |
| Rerun and replace | **BLOCKED** |
| If impossible, remove from primary results | **DONE** |

**Why it is blocked.** 49.6% of the bone-loss validation crops (773 of 1,558) carry ±15% jitter
applied at construction time with offsets that were never saved. Those crops are irreproducible
*by construction*. The remaining 785 are reproducible, but a number computed on them is a new
measurement on a clean subset, not a reproduction of the reported 0.9233.
The original un-rotated Tufts radiographs are also absent from this machine; the rebuild attempt
scored 0.400 sensitivity against a documented 0.831 (`RESULTS_LOG.md` 2026-08-27u, 2026-08-28c).

**The fallback is already applied**: bone loss appears in the paper as a *measured negative
result* — strong in-domain, near-inert out of domain — never as a headline capability.

### Add 95% confidence intervals — **MOSTLY DONE**

Already present (`model_metrics.md` "Confidence intervals", cluster-bootstrapped over **images**):

| metric | point | 95% CI |
|---|---|---|
| Detection recall | 70.6% | [66.5, 74.6] |
| FDI exact, end-to-end | 58.3% | [53.9, 62.8] |
| FDI exact, of detected | 82.6% | [79.1, 85.8] |
| Lesion agreement (internal) | 44.3% | [39.0, 49.3] |
| External site 1–4 | 28.8 / 51.3 / 40.1 / 41.9% | all four have CIs |
| External pooled | 40.8% | [37.0, 44.8] |
| Paired detector delta | +12.1 pp | [+6.8, +17.2] |
| Abstention gain, Stage 2 | +5.91 pp | [+3.88, +7.68] |
| Abstention gain, caries | +14.25 pp | [+11.32, +16.63] |
| Constant − pipeline, internal | +4.59 pp | [+0.60, +8.89] |
| Constant − pipeline, external | −0.89 pp | [−4.88, +3.01] |
| Third-corpus gain, DENTEX | +1.14 pp | [+0.33, +1.95] |

**Still OPEN:** detection **mAP** and per-class **precision/recall** for the classifiers. Both need
per-item prediction dumps, which are cheap CPU work and not yet written.

### Statistical uncertainty on external testing — **DONE**
Per-site results, pooled result, and uncertainty **around the difference** are all reported.
The per-site spread (a 26-point swing) is presented as a finding in its own right.

### Clearly distinguish the metrics — **DONE**
DENTEX uses IoU ≥ 0.30 with a centroid-containment fallback; external cohorts use centroid
containment alone. The reason is documented in both scripts and the paper: external lesions are
89–3,090 px focal blobs inside ~25,000 px tooth boxes, so IoU ≥ 0.30 would score ~0% *by
construction* regardless of model quality. Which comparisons remain valid is stated with it.

---

## 🟠 Story / Structure

| item | status | note |
|---|---|---|
| Replace the title | **DECISION NEEDED** | current: *"What a Tooth-Level Score Cannot Tell You…"*. The recommended alternative is more literal and more searchable; the current one is more memorable. Pick one. |
| One primary research question in the Introduction | **PARTIAL** | implied throughout, never stated as a single sentence |
| 2–4 explicit hypotheses / objectives | **OPEN** | |
| Restructure around the story arc | **MOSTLY DONE** | current order is problem → floor → baseline ladder → controls → external → implications |
| Every Results subsection answers a Methods question | **PARTIAL** | true for the baseline sections, looser for the supporting ones |
| Move secondary experiments out of the main story | **DONE** | |
| Make periodontal clearly secondary | **DONE** | |

---

## 🟠 Literature

| item | status |
|---|---|
| Grow references from 26 to 35–50 | **OPEN** — 26 present, all verified |
| Cover the 11 named topic areas | **PARTIAL** — dental AI, caries, periodontal, numbering, VLM, shortcut learning present; calibration, selective prediction, distribution shift, medical-AI reporting are thin |
| Strengthen the research gap | **PARTIAL** |
| Document or downgrade the "49 papers" claim | **MUST FIX** |

**On the "49 papers" claim.** The *external-validation* count (2 of 49) is traceable to the review
sheet. The claim that **none** report an image-blind baseline was **never actually counted** — the
extraction has no such field. It must be softened to a targeted observation, or the census must be
done properly. This was caught in the manuscript audit and is the single most exposed claim in the
paper, because the whole contribution rests on that gap existing.

---

## 🟡 Methods / Reproducibility

| item | status |
|---|---|
| Dataset characteristics table | **OPEN** — all facts exist, the table does not |
| Dataset-flow diagram (inclusion/exclusion, splits) | **OPEN** |
| Document model, prompt, preprocessing, seed, thresholds, matching, metric impl., versions | **PARTIAL** — all live in code and are recorded per run; the paper states some, not all |
| Code Availability section | **OPEN** |
| Data Availability section | **OPEN** |

Facts available for the dataset table: Tufts (1,000 OPGs, frozen 700/150/150), DENTEX (250 disease
images → **164 leak-free**, 477 affected teeth, 479 lesions; 634 enumeration images), Kaggle
dual-labeled (499 usable images, 13,166 teeth, ablation only), Ningxia (4 hospitals, 337 caries
images, 1,013 lesions, locked external), SDH clinic (IRB-blocked, contributes to no result).

---

## 🟡 Clinical / Scientific Interpretation

| item | status |
|---|---|
| Add a Clinical and Evaluation Implications section, covering the five points | **OPEN** |
| Do not claim clinical diagnostic capability | **DONE** |
| Do not generalise the VLM findings beyond the models tested | **DONE** |

The five points are already argued in the Discussion; they are not gathered under a heading a
clinical reader would look for.

---

## 🟡 Writing

| item | status |
|---|---|
| Rewrite the abstract as Background → Problem → Methods → Results → Conclusion | **CONFLICT — decide** |
| Remove VLM/AI jargon from the first ~2 pages | **PARTIAL** |
| Introduction understandable without VLM knowledge | **MOSTLY DONE** |
| Define every technical term at first use | **PARTIAL** — FDI, mAP, ECE, coverage are not all defined |
| Remove disconnected consecutive sentences | **PARTIAL** |
| Every section: Why → How → What → So what | **PARTIAL** |
| Remove rhetorical language that does not aid clarity | **PARTIAL** |

**The abstract conflict, stated plainly.** The current abstract is deliberately narrative: it
states the question and withholds the outcome, to make the reader open the paper. That was an
explicit earlier instruction. This to-do asks for a structured Background/Problem/Methods/Results/
Conclusion abstract, which requires giving the result away in sentence four. **Both are defensible
and they are mutually exclusive.** Most clinical journals expect the structured form; most CS
venues accept either. Recommendation: **structured**, if the target is a medical journal — but this
is a call for the team, not a silent edit.

---

## 🟢 Final publication cleanup

| item | status |
|---|---|
| "external validation" → "external testing" | **OPEN** |
| "reference standard" used consistently | **OPEN** |
| Funding statement | **OPEN** |
| Conflict-of-interest statement | **OPEN** |
| Ethics / IRB statement | **OPEN — blocked on IRB** |
| Author contributions | **OPEN** |
| Acknowledgements | **OPEN** |
| Remove `unknown@unknown`, withheld affiliations, "Others", TODOs | **OPEN** — 4 `Unknown`, 1 `unknown@unknown`, `Others` in 3 bib entries |
| Citation audit | **DONE** — see below |
| Plagiarism / similarity | **PARTIAL** |
| University format + venue format copies | **OPEN** |

**Citation audit — done, and it found real errors.** All 19 citation commands were checked against
the entry each points at (`scripts/audit_citations.py`, re-runnable). Seven were wrong: two invented
titles, one wrong publication year, one claim attributed to two papers about entirely different
conditions, and three descriptions that did not match the cited work. Ten added entries had their
DOIs verified against publisher records; four were wrong. No orphan or missing references remain.

**Plagiarism — internal check done, institutional check pending.** `scripts/check_text_reuse.py`
found a longest shared span of 15 words (a table row of model names and numbers) and **zero overlap
with the team's prior survey paper** at a 6-word threshold. This is not a literature check and does
not substitute for Turnitin/iThenticate.

---

## 🔴 NEW BLOCKER (1 Sep 2026) — 22 of 63 checkable DOIs are broken

Every DOI in `source.bib` was dereferenced against the DOI registry
(`scripts/verify_citations_crossref.py`, read-only). **Nothing was fixed — this is the saved
work item.**

| category | count |
|---|---|
| clean | 40 |
| **DOI resolves to a DIFFERENT paper** | **11** |
| **DOI not registered with any agency** | **11** |
| no DOI, unverifiable by this method | 19 |

Full list and per-entry evidence: `outputs/citation_audit/FINDINGS.md`.

**To do, per entry, for all 22:** look the work up by title, then either correct the DOI or drop
the reference. This cannot be automated — the audit can prove a DOI is wrong but not what the
right one is. It does **not** follow that the papers are fabricated; a real paper can carry a
wrong identifier, and that distinction has to be made by hand.

Then decide what to do about the 19 entries carrying no DOI at all.

**Why this is a blocker:** a reviewer who dereferences one bad DOI checks the rest. The 28 Aug
audit found 7 citation errors including two invented titles and still passed all 22 of these,
because `audit_citations.py` makes no network call — it prints citations for eye-review. An audit
that cannot fail is not an audit.

Re-run: `python scripts/verify_citations_crossref.py`

---

## The four items that block submission regardless of the above

None are engineering, and all are account-owner actions:

1. **IRB not started** — longest lead time of anything open. Gates the ethics statement *and* the
   reader study.
2. **A Tufts Drive folder is browsable without sign-in** — the licence forbids redistribution.
   This is a live breach, not paperwork.
3. **DENTEX and Ningxia licences never read or recorded** — required for the Data Availability
   section.
4. **SDH `metadata/index.csv` sits beside `images/`** — voids that copy's de-identification.

## The one item that most changes the grade

**A reader study.** Protocol is written and runnable the day IRB clears (100 images, 2–3 dentists,
the same scorer as every machine arm, with the constant included in the comparison). Without it
the paper rests on methodology against modest numbers. With it, it has external testing across four
hospitals *and* a clinician reference — a combination that is uncommon in this literature.
