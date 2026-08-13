# Publication Strategy — Survey Paper + Research Paper

**Compiled:** 12 August 2026
**Goal:** get both papers into Scopus-indexed venues (conference or journal).
**Companion docs:** `gap_analysis.md` (literature vs. our work), `PUBLICATION_TODO.md` (engineering work list), `clinical_dataset_plan.md` (clinic data plan), `../results/PAPER_MATERIAL.md` (numbers and methods).

> **Scope note:** this document covers *publication strategy* — defects in the drafts, acceptance criteria, venue options, and sequencing. It does **not** repeat the engineering to-do list in `PUBLICATION_TODO.md`. Read both.

---

## 0. Read this first — the blunt version

Three things are true at once, and you need to hold all three:

1. **The survey draft is closer to submittable than the research paper is.** It is a real 16-page IEEE-format review with 47 papers, four tables, five figures, a taxonomy, and a roadmap. That is genuine work. It is not, however, submittable *today* — it has defects that would get it desk-rejected or shredded in review, and they are listed in Part A. Most are fixable in days, not months.

2. **The survey's central novelty claim is decaying fast, and one 2026 paper may have already broken it.** The survey's headline finding is: *"no existing system simultaneously addresses caries detection, severity staging, periodontal bone loss quantification, and explainability within a single unified pipeline on panoramic radiographs."* [DentFound](https://www.nature.com/articles/s41551-026-01713-8) (*Nature Biomedical Engineering*, 25 June 2026) covers >101,000 patients, 98 diseases, 52 tooth sites, multi-center external validation, and expert-rated report generation. You must read it and decide whether your claim survives, narrows, or dies. If you submit the claim unqualified and a reviewer knows that paper, you lose the review on your central contribution. **This is the single highest-risk item in this document.**

3. **The research paper has no publishable result yet — but it has a clear path to one.** Per-stage metrics on public datasets with no held-out test set, no integration, and no external validation is not a paper. The clinic dataset external validation (`clinical_dataset_plan.md`) converts it into one. That is the whole game.

**The order that follows from this:** fix and submit the survey within weeks, because it is nearly done and it is depreciating. Build the research paper over months, because it needs real new results. Do not let the research paper's timeline hold the survey hostage, and do not rush the survey into a deadline while it still has factual errors in it.

---

# PART A — The Survey Paper

## A.1 Defects found in the current draft

I read the full 16-page PDF. These are concrete, verifiable problems. Fix all of them before submitting anywhere.

### A.1.1 Fatal: the search window contradicts the corpus

Section 2 states:

> "The search was executed between **January 2024 and March 2025**, with publication year filters restricting results to 2020 onward."

Section 2.3 states:

> "47 papers were selected, spanning 2021–2026, with **25 papers from 2025 (53%)**, 17 from 2024 (36%), **2 from 2026**, 2 from 2023, and 1 from 2021"

A search that finished in March 2025 cannot have retrieved 25 papers published in 2025 and 2 published in 2026. This is a logical impossibility on the face of the paper, in the methodology section, where reviewers look hardest. **A single competent reviewer kills the paper on this line alone.** Fix: state the true search window (it was evidently extended into 2026), and give the exact final search date.

### A.1.2 Fatal: Section 9 is empty

```
9. COMPARATIVE ANALYSIS OF REPRESENTATIVE METHODS
10. DATASETS, BENCHMARKS, AND CLINICAL VALIDATION (C5)
```

Section 9 is a heading with **zero body text**, immediately followed by Section 10. Table IV appears to be the intended content but has no accompanying prose. Either write the section or delete the heading and fold Table IV into Section 12.

### A.1.3 Serious: text and tables disagree on the same references

Reviewers spot-check tables against text. Yours do not match:

| Ref | Body text says | Table IV says | Problem |
|---|---|---|---|
| [34] Zancan et al. | "accuracy = 0.94 and F1 = 0.94", "7,304 tooth-level images from 935 panoramic radiographs" | "Acc=0.998", "935 PAN + 18k teeth" | **Both the metric and the dataset size differ** |
| [40] Zhang et al. | "AP50 = 97.3% on Tufts and 98.1% on O2PR" | "mAP=77.4" | Large unexplained discrepancy |
| [30] Van Nistelrooij et al. | "FROC = 0.988 ... AUC = 0.996" | "mAP=0.848" | May be different tasks — but the table must say which |

Go through **every row of Tables I–IV** against its source paragraph and its source paper. One caught error makes a reviewer assume there are ten more.

### A.1.4 Serious: currency — only 2 of 47 papers are from 2026

You are submitting in late 2026 with a corpus that is effectively 2024–2025. Reviewers in a fast-moving field read this as "not current." `gap_analysis.md` already identified major 2026 work absent from your draft:

| Missing paper | Venue / date | Why it must be in |
|---|---|---|
| [DentFound](https://www.nature.com/articles/s41551-026-01713-8) | *Nature BME*, Jun 2026 | Directly threatens your central gap claim (see §0.2) |
| [End-to-end periodontitis staging with keypoints](https://link.springer.com/article/10.1007/s11282-026-00921-x) | *Oral Radiology*, Apr 2026 | YOLOv11 + 6 keypoints/tooth, mAP50 >0.958, ICC 0.705–0.871 — closest analogue to your C2 category |
| [YOLO26 on DENTEX](https://arxiv.org/abs/2604.16231) | arXiv, Apr 2026 | Enumeration mAP50 0.976; updates your "structural tasks are solved" claim |
| [AI-assisted bone-loss severity and patterns](https://www.nature.com/articles/s41598-026-38061-1) | *Sci Rep*, Feb 2026 | Keypoint R-CNN, ICC 0.801, pattern classification 87% |
| [DentiAsk VQA benchmark](https://arxiv.org/abs/2607.08790) | arXiv, Jun 2026 | Evidence VLMs fail at spatial reasoning — supports your pipeline argument |
| [Translating caries algorithms to clinic](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1879708/full) | *Frontiers in Medicine*, Jul 2026 | AUC 0.76–0.98 → 0.53–0.57 under domain shift. Best possible support for your dataset-fragmentation gap |
| [Translational readiness of imaging AI in dentistry](https://www.mdpi.com/2227-9032/14/13/1952) | *Healthcare*, Jul 2026 | "Formal explainability methods were uncommon" — independent confirmation of your 6.4% XAI finding |
| [Explainability/bias/generalisability review](https://onlinelibrary.wiley.com/doi/10.1002/cre2.70375) | *Clin Exp Dent Res*, 2026 | ⚠ our fetch returned HTTP 403 — **read it manually before citing** |

Adding ~10–15 papers from 2026 moves the corpus from 47 to ~60 and changes the currency story completely. Note that several of these *strengthen* your gaps (Frontiers and Healthcare independently confirm the dataset and explainability gaps) — so this is not just damage control.

### A.1.5 Moderate: no PRISMA flow diagram, no risk-of-bias assessment

You have a search methodology (Section 2) but no PRISMA flow diagram (records identified → screened → excluded with reasons → included) and no quality appraisal. Note that several papers *inside your own corpus* used PRISMA/QUADAS-2 — [Albano et al.], [Iacob et al.], [Bonfanti-Gris et al.], [Ferrara et al.] — so reviewers in this space expect it.

This determines venue eligibility:

- **Submitting as a narrative/structured survey** → acceptable at IEEE venues and IEEE Access. No PRISMA required.
- **Submitting to a dental journal as a "Systematic Review"** → [Dentomaxillofacial Radiology explicitly requires](https://academic.oup.com/dmfr/pages/general-instructions) a completed PRISMA checklist **and PROSPERO protocol registration**. PROSPERO registration is supposed to happen *before* the review is conducted — retrofitting it is problematic and you should not pretend otherwise.
- **Middle path (recommended):** add a PRISMA-style flow diagram as a figure, describe screening counts honestly, and label the paper a **"structured review"** or **"scoping review"** rather than a "systematic review." This buys most of the rigor credit without claiming a protocol you did not register.

### A.1.6 Minor but cumulative: proofreading

Real errors in the current text: `"unspecied"` (Sec. 11) · `"difficult and and makes it harder"` (Sec. 13.1) · `"reveals five structural gap"` (Conclusion) · `"Metrics: Met-ric heterogeneity"` (Sec. 12.4.2) · `"Overall ,this study"` (Sec. 1) · `"treatment recommendations.."` (Sec. 3.4). Also check Section 15's cross-reference — it says "Building on the limitations identified in Section 13" but the cross-cutting gap analysis is Section 14.

Individually trivial. Collectively they signal a draft that nobody read end-to-end, which primes a reviewer to distrust the data.

## A.2 What the survey has going for it

Be clear on the strengths so you don't over-correct:

- **The six-component formulation** (detection / localization / severity / quantification / explainability / clinical integration) is a genuinely useful analytical frame and is the paper's best original contribution.
- **The 6.4% explainability statistic** (3 of 47 papers) is a concrete, quotable, citable number. It is independently corroborated by [*Healthcare* Jul 2026](https://www.mdpi.com/2227-9032/14/13/1952). This is the finding most likely to get your paper cited.
- **The four-archetype taxonomy** (single-task / multi-task / pipeline / end-to-end) with capability coverage in Table I is clean and reusable.
- **Coverage of both caries and periodontal in one review** is less common than either alone.
- It links directly to your own research paper, which is a legitimate and normal structure: survey establishes the gap, research paper fills it.

## A.3 Survey fix list

- [ ] **S1.** Correct the search-window contradiction. State the true final search date. *(§A.1.1 — do this first)*
- [ ] **S2.** Write Section 9, or delete the heading and merge Table IV into Section 12.
- [ ] **S3.** Audit every row of Tables I–IV against body text **and** against the original papers. Fix [34], [40], [30] at minimum.
- [ ] **S4.** Read [DentFound](https://www.nature.com/articles/s41551-026-01713-8) in full. Decide whether the central gap claim survives. Most likely reframing: *"no **openly published, reproducible** system on **panoramic** radiographs addresses all six components"* — DentFound is a proprietary large-scale foundation model, which is a defensible distinction, but you must make it explicitly rather than ignore the paper.
- [ ] **S5.** Add 10–15 papers from 2026 (§A.1.4 table is your starting list). Update the corpus counts, the year-distribution sentence, and any "to our knowledge" claims.
- [ ] **S6.** Add a PRISMA-style flow diagram figure. Relabel as "structured review" or "scoping review" unless you are genuinely registering on PROSPERO.
- [ ] **S7.** Full proofread by someone who has not read it before.
- [ ] **S8.** Update the "proposed unified framework" section so it matches what the research paper actually does — including that it is under evaluation on an external clinical dataset. Keeps the two papers coherent.
- [ ] **S9.** Decide authorship order and confirm with Dr. Mamatha H R before submission, not after.

**Realistic effort:** S1, S2, S7 are hours. S3 is a full day of careful checking. S5 is 2–3 days of reading and writing. S4 is a half-day plus a judgement call. **Total: roughly one focused week.**

---

# PART B — The Research Paper

## B.1 The only novelty claim that survives contact with 2026 literature

Per `gap_analysis.md`, these are **dead** as lead claims: tooth detection, FDI numbering, CEJ/crest landmark detection on panoramics, caries cascade architecture, Grad-CAM heatmaps. All published, recently, with better numbers.

**What survives — and it is enough:**

> Tufts/DENTEX-trained models, frozen, evaluated on ~4,420 real panoramic radiographs from an unaudited private dental clinic on a **different vendor's device** (Carestream CS 8100), with a **documented failure taxonomy stratified by real-world confounders** (restorations >50%, implants 10–25%, RCT 15–35%), and an integrated per-tooth reporting pipeline with **system-level rather than per-stage metrics**.

Why this holds up:

- Three separate 2025–2026 reviews name external validation and undocumented failure modes as *the* field-wide gap ([Frontiers Med Jul 2026](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1879708/full), [Healthcare Jul 2026](https://www.mdpi.com/2227-9032/14/13/1952), [DMFR 2025](https://academic.oup.com/dmfr/article/54/2/89/7917334)).
- The DMFR meta-analysis found **0 of 30** studies rated "very high quality" on APPRAISE-AI. The rigor bar in this field is genuinely low. Clean methodology is itself a differentiator.
- Your clinic data is on a device and population that is not in any public benchmark. That is not something a competitor can trivially replicate.

**Critical framing point:** a large performance drop on clinic data is **the expected result, not a failure**. Frontiers 2026 documents AUC collapsing from 0.76–0.98 to 0.53–0.57 under domain shift. If you find a big drop, you have confirmed and *quantified* a known problem on a new device — that is the paper. Do not panic and start tuning until the number looks good; that destroys the contribution.

## B.2 Minimum result set for a submittable research paper

The engineering steps are in `PUBLICATION_TODO.md`. This is the **publication acceptance** view of the same thing — what must exist in the results section:

| # | Required result | Without it, the reviewer says | Source task |
|---|---|---|---|
| R1 | Held-out **test** metrics for every model, patient-level split | "All numbers are validation-set; these are optimistically biased" | T0.2 |
| R2 | Truthful methods section (augmentation actually run, or stated as absent) | *fatal — credibility* | T0.1 |
| R3 | One canonical detector, frozen and versioned | "Which detector produced these numbers?" | T0.6 |
| R4 | **End-to-end** per-tooth and per-patient metrics | "You have components, not a system" | T1.1 |
| R5 | Stage-wise error-propagation analysis | — *(this is a bonus contribution, few papers do it)* | T1.1 |
| R6 | External validation on clinic data + failure taxonomy | "Internal validation only" — **the most-cited weakness in every review** | T1.2 |
| R7 | 95% CIs on all headline metrics; per-class support counts always shown | "n=6 macro-F1 is uninterpretable" | T0.5, T1.3 |
| R8 | PPV/NPV at observed prevalence + calibration | "Accuracy is misleading at 4% prevalence" | T1.3 |
| R9 | Ablations for the design choices you claim (jitter, asymmetric crop, overlap-vs-IoU) | "These are assertions, not findings" | T1.4 |
| R10 | Quantified XAI localisation agreement, not a heatmap gallery | "Heatmaps without validation" | T1.5 |
| R11 | Inference latency per image | Expected for any clinical-utility claim | T1.1 |
| R12 | Complete CLAIM checklist as supplementary material | Increasingly requested by dental/medical imaging journals | T0.4 |

**R1–R6 are the floor.** R7–R12 are what separate "accepted with major revisions" from "accepted."

## B.3 Reporting checklists you will be asked for

| Checklist | Applies to | Get it from |
|---|---|---|
| **CLAIM 2024** (Checklist for AI in Medical Imaging) | The research paper — this is the primary one | [Radiology: AI 2024 update](https://pubs.rsna.org/doi/full/10.1148/ryai.240300) |
| **PRISMA 2020** | The survey, if submitted as systematic/scoping review | [PRISMA 2020 statement](https://pubmed.ncbi.nlm.nih.gov/33782057/) |
| **STARD 2015** | If you frame the paper as a diagnostic accuracy study (likely for the clinic validation) | Search STARD 2015 — diagnostic accuracy reporting |
| **TRIPOD+AI** | If you present the pipeline as a clinical prediction model | Relevant if you frame it prognostically |
| Dental-specific overview | Which checklist applies when in dentistry | [Reporting checklists in dentistry review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12756637/) |

Fill CLAIM early, not the night before submission. It will surface missing methods details while you can still generate them.

## B.4 Ethics and data governance — do not skip this

The clinic dataset is real patient data. Journals will ask, and some will desk-reject without it:

- [ ] **Institutional ethics / IRB approval or documented exemption** for retrospective use of the clinic images. Start this now — approvals take weeks.
- [ ] **Written agreement from the clinic** covering research use and publication.
- [ ] **De-identification policy**, executed and documented. The audit found 3,296 `PatientInfo.xml` files — those almost certainly contain PHI. DICOM headers in the `.PANO` files also carry patient identifiers. **Strip them and document the process.**
- [ ] **A data-availability statement** you can actually honour. If the clinic data cannot be shared, say so and explain why; that is acceptable, but it must be stated.
- [ ] If you ever release a curated subset (stretch goal T3.5), consent and de-identification must be airtight first.

> Journals increasingly desk-reject human-subjects work without an ethics statement regardless of scientific merit. This is not a formality you can add during revision.

---

# PART C — Acceptance criteria: what actually gets papers rejected

Synthesised from the reviews in `gap_analysis.md` and the checklists above. These are the recurring failure modes in *this specific subfield*.

**Rejection triggers — survey papers**

1. Methodology that doesn't reproduce — unclear or contradictory search dates, no screening counts, no inclusion/exclusion audit trail. *(You currently have this — §A.1.1.)*
2. Stale corpus — a review submitted in 2026 that stops at 2025.
3. Pure summarisation with no synthesis — tables of "who did what" with no taxonomy, no cross-cutting analysis, no position. *(You are fine here; your taxonomy is the strength.)*
4. Overlap with an existing recent review that is not cited or differentiated.
5. Unverifiable numbers — table values that disagree with the cited papers. *(You currently have this — §A.1.3.)*

**Rejection triggers — original research**

1. **No external validation.** The single most-cited weakness across all three reviews retrieved.
2. **Validation-set numbers reported as results.** No held-out test set.
3. **Accuracy reported on heavily imbalanced data** without prevalence-aware metrics.
4. **Metrics without confidence intervals**, or class-level metrics without support counts.
5. **Incomplete reproducibility spec** — missing seeds, splits, hyperparameters, hardware, exact model versions.
6. **Claims not supported by the experiments run** — asserting a design choice helps without ablating it.
7. **Missing ethics statement** for human-subjects data.
8. **Novelty already published.** Check the literature again immediately before submission — the field moved three times between April and July 2026.

**The meta-criterion:** the DMFR meta-analysis rated **0 of 30** dental bone-loss AI papers as "very high quality," with 63.3% merely "intermediate." Clean, complete, honest reporting is a genuine competitive advantage here. You do not need to beat the state of the art; you need to be more rigorous than a field that is currently not very rigorous.

---

# PART D — Venue options (all possible routes)

⚠ **Verification caveat.** Scopus's official source list requires login and could not be accessed directly. Everything below is **secondary evidence** — publisher pages, Scimago, journal sites. **Before submitting anywhere, verify current Scopus indexing yourself** at [scopus.com/sources](https://www.scopus.com/sources) or via your university library, which will have institutional access. Scopus discontinues titles regularly.

## D.1 The single most important budget fact

**Hybrid journals let you publish for free.** Fully open-access journals charge a mandatory APC; hybrid journals offer a subscription-model option at **zero cost** (your article sits behind a paywall, which does not affect Scopus indexing at all).

For a student team with no grant, this is decisive:

| Model | Cost | Examples |
|---|---|---|
| **Hybrid — subscription option** | **₹0** | Dentomaxillofacial Radiology, Oral Radiology, Journal of Dentistry, Computers in Biology and Medicine, Biomedical Signal Processing and Control |
| Fully open access | $2,000–3,300 mandatory | BMC Oral Health, Scientific Reports, Diagnostics, IEEE Access |

**Ask PES University whether it has a Read-and-Publish agreement** with Oxford, Springer Nature, Elsevier, or Wiley. Many Indian institutions do, and it can zero out the APC even at OA journals. This is a five-minute email to your library that could save $3,000.

## D.2 Journals — verified details

| Journal | Publisher | Quartile / metrics | Cost | Takes reviews? | Notes |
|---|---|---|---|---|---|
| **[Dentomaxillofacial Radiology](https://academic.oup.com/dmfr)** | Oxford | **Q1**, SJR 1.160, H-index 96 | **£0 subscription** / £2,392 OA (20% BIR member discount) | ✅ Reviews max 6,000 words; Systematic Reviews need PRISMA **+ PROSPERO** | Research Articles max 7,000 words. Does *not* take unsolicited Cutting Edge Reviews or Case Reports. Best prestige-per-rupee on this list. Competitive. |
| **[Oral Radiology](https://link.springer.com/journal/11282)** | Springer | Mid-tier | **₹0 subscription** / OA optional | ✅ Explicitly accepts unsolicited Reviews | Published the [Apr 2026 keypoint staging paper](https://link.springer.com/article/10.1007/s11282-026-00921-x) — demonstrably in scope. Strong realistic target. |
| **[BMC Oral Health](https://bmcoralhealth.biomedcentral.com/)** | Springer Nature | Q1/Q2 dentistry | **£2,490 / $3,290 / €2,790** — mandatory | ✅ | Waivers only for *lowest-income* countries; **India is unlikely to qualify** — check the country-tiered pricing pilot. Very common venue for dental AI. Expensive. |
| **[Diagnostics](https://www.mdpi.com/journal/diagnostics)** | MDPI | CiteScore 6.9, IF 3.8 | **CHF 2,600** | ✅ | Scopus + PubMed + WoS. Fast review. Some committees discount MDPI — check your evaluators' view before committing. |
| **[Scientific Reports](https://www.nature.com/srep/)** | Nature Portfolio | Q1 multidisciplinary | **£2,290 / $2,850 / €2,490** | Limited | Published [Feb 2026](https://www.nature.com/articles/s41598-026-38061-1) and [Sep 2025](https://www.nature.com/articles/s41598-025-16591-4) dental AI work. Strong name recognition. Better fit for the research paper than the survey. |
| **[IEEE Access](https://ieeeaccess.ieee.org/)** | IEEE | Q1 (multidisciplinary CS) | **$2,160** + tax. 5% IEEE member / 20% society member discount — **students ineligible** | ✅ **Surveys are standard here** | ~45–50% acceptance, ~4–6 week first decision. Low-income-country waiver requires *all* authors eligible. Fastest credible route for the survey. |
| **[Journal of Dentistry](https://www.sciencedirect.com/journal/journal-of-dentistry)** | Elsevier | Q1 dentistry | Hybrid — subscription option | Selective | High bar. Stretch target. |
| **[Computers in Biology and Medicine](https://www.sciencedirect.com/journal/computers-in-biology-and-medicine)** | Elsevier | Q1 | Hybrid — subscription option | Selective | Good fit for the *methods* framing of the research paper. |
| **[Biomedical Signal Processing and Control](https://www.sciencedirect.com/journal/biomedical-signal-processing-and-control)** | Elsevier | Q1/Q2 | Hybrid — subscription option | Selective | Slightly easier than CBM, same family. |

*APC figures retrieved 12 Aug 2026 — verify at submission, they change.*

## D.3 Conferences

| Venue | Deadline | Details | Verdict |
|---|---|---|---|
| **[IEEE ISBI 2027](https://biomedicalimaging.org/2027/)** | **26 October 2026** | Lausanne. **4 pages max** (5th page $200, non-technical only). Single-blind. Max 2 first-author submissions. | **Best conference target for the research paper.** ~10 weeks out. IEEE-published → Scopus. Competitive but reachable. 4 pages forces brutal focus — arguably a feature. |
| **[CVIP 2026](https://cvip2026.nitc.ac.in/)** | Round 2: **16 August 2026** | NIT Calicut, 9–12 Dec 2026. Springer LNCS/CCIS. IAPR-endorsed. | ⚠ **4 days away.** Springer LNCS/CCIS is normally Scopus-indexed but the site does not state it — verify. General computer vision; a survey may not fit scope. **Do not rush a defective survey into this.** Note it for CVIP 2027. |
| **IEEE EMBC 2027** | ~Feb 2027 (verify) | Large biomedical engineering conference | Reasonable backup. Verify dates at the EMBS site. |
| **MICCAI 2027** | ~Feb–Mar 2027 | Top-tier medical imaging | Realistically out of reach at current maturity. The [Open Data track](https://conferences.miccai.org/2026/en/MICCAI-2026-Open-Data-Call-for-Papers-and-Reviewers.html) would fit a curated clinical dataset release (stretch goal T3.5). |

**Conference vs. journal trade-off:** conferences give you a fixed deadline, faster turnaround, and a presentation line on the CV; journals give more space, more prestige, and no hard deadline. For a capstone with a graduation clock, a conference deadline is often the more useful forcing function — but only for work that is actually ready.

## D.4 Predatory venues — the warning

Searching "Scopus indexed conference India" returns mostly aggregator sites that monetise submissions. Some are outright predatory. **Do not submit to anything you found through a conference-alert aggregator.**

Red flags: guaranteed acceptance or guaranteed Scopus indexing · acceptance in days · unsolicited email invitations · fees due before review · vague or unverifiable editorial board · a journal name that closely mimics a well-known title (hijacking).

Before submitting anywhere, check: the venue is listed on the **publisher's own site** (IEEE, Springer, Elsevier, Oxford, Wiley, Nature) · the journal appears in **[DOAJ](https://doaj.org)** if open access · it is on the **Scopus source list** (verify via library access) · it is not on a discontinued-titles list.

A publication in a predatory venue is worse than no publication — it is a permanent line on your CV that informed readers discount, and some universities now refuse to count them.

## D.5 Do not double-submit

Never submit the same paper to two venues simultaneously — it is a serious ethics violation in every publisher's policy. Also note: your survey **proposes** the framework your research paper **implements**. That is a legitimate and common structure, but keep the papers textually distinct, cite the survey from the research paper once published, and do not reuse paragraphs verbatim. Publishers run similarity checks and will flag self-plagiarism.

---

# PART E — Recommended strategy

## E.1 Two-track, survey first

**Track 1 — Survey (weeks 1–4).** It is nearly done and it is depreciating in value every month. Fix §A.3, submit.

- **First choice:** [Oral Radiology](https://link.springer.com/journal/11282) — free under subscription, explicitly accepts unsolicited reviews, demonstrably in scope, realistic bar.
- **If you want prestige and can take the rejection risk:** [Dentomaxillofacial Radiology](https://academic.oup.com/dmfr) — Q1, free under subscription, 6,000-word review limit means cutting your draft down.
- **If you want speed and can find $2,160:** [IEEE Access](https://ieeeaccess.ieee.org/) — surveys are its bread and butter, ~4–6 week decisions.
- **Backup:** [Diagnostics](https://www.mdpi.com/journal/diagnostics) (CHF 2,600) or [BMC Oral Health](https://bmcoralhealth.biomedcentral.com/) ($3,290).

**Track 2 — Research paper (months 1–4).** Follow `PUBLICATION_TODO.md` Tier 0 → Tier 1. Target **ISBI 2027 (26 Oct 2026)** if the integration and clinic validation land in time; otherwise target a journal with no deadline pressure — *Oral Radiology*, *Scientific Reports*, *Dentomaxillofacial Radiology*, or *Computers in Biology and Medicine*.

## E.2 Honest timeline check

ISBI's 26 October deadline is **10 weeks away**. To hit it you need Tier 0 (credibility repairs), T1.1 (end-to-end integration), and T1.2 (clinic Tier 1a external validation) — all done, written, and compressed into 4 pages.

That is aggressive but not impossible **if Tier 0 starts this week**. If it slips past mid-September, drop ISBI without regret and go to a journal. A rushed 4-page submission with half-finished validation wastes the submission and the reviewer goodwill.

## E.3 Non-negotiable

- Do not submit the survey with the search-date contradiction in it.
- Do not submit the research paper with validation-set numbers presented as results.
- Do not submit clinic-data work without ethics approval.
- Do not submit anywhere you found via a conference-alert aggregator.

---

# PART F — Consolidated to-do list

## Week 0 — This week (start immediately, in this order)

- [ ] **P0.1** Fix the survey search-window contradiction *(§A.1.1)* — one paragraph, highest risk-reduction per minute of any item here
- [ ] **P0.2** Read [DentFound](https://www.nature.com/articles/s41551-026-01713-8) in full; decide whether the survey's central gap claim survives, and how to reframe it *(§A.3/S4)*
- [ ] **P0.3** Start the **ethics approval** process for clinic data — longest lead time of anything in this document *(§B.4)*
- [ ] **P0.4** Email the PES library: does the university have Read-and-Publish agreements with Oxford / Springer Nature / Elsevier / Wiley? *(§D.1)*
- [ ] **P0.5** Begin `PUBLICATION_TODO.md` **T0.1** — the unapplied-augmentation discrepancy. Nothing in the research paper matters until this is resolved.
- [ ] **P0.6** Confirm authorship order and target venue with Dr. Mamatha H R

## Weeks 1–4 — Survey to submission

- [ ] **P1.1** Write Section 9 or remove the heading *(S2)*
- [ ] **P1.2** Audit all four tables against body text and source papers *(S3)* — full day, do not skip
- [ ] **P1.3** Add 10–15 papers from 2026; update corpus counts and year distribution *(S5)*
- [ ] **P1.4** Add PRISMA-style flow diagram; relabel as structured/scoping review *(S6)*
- [ ] **P1.5** Update the proposed-framework section to match the research paper *(S8)*
- [ ] **P1.6** Full external proofread *(S7)*
- [ ] **P1.7** Verify target journal's current Scopus status via library access *(§D)*
- [ ] **P1.8** Format to target journal's template; write cover letter
- [ ] **P1.9** **Submit the survey**

## Weeks 1–8 — Research paper, credibility and system (parallel track)

- [ ] **P2.1** Complete `PUBLICATION_TODO.md` **T0.2–T0.6** — held-out test sets, model selection, LR scheduling, severity-class honesty, canonical detector
- [ ] **P2.2** **T1.1** — end-to-end integration with per-tooth and per-patient metrics, error propagation, latency
- [ ] **P2.3** **T1.2** — clinic external validation Tier 1a (label-free), failure taxonomy
- [ ] **P2.4** **T1.3** — CIs, PPV/NPV at prevalence, calibration
- [ ] **P2.5** Fill the **CLAIM 2024 checklist** as you go, not at the end
- [ ] **P2.6** Fix the FDI conversion bug in `configs/dataset_config.yaml` and unit-test it — *lower-arch findings are currently mis-numbered; every lower-jaw result in the paper would be wrong*

## Weeks 6–10 — Research paper, results and writing

- [ ] **P3.1** **T1.4** ablations — jitter, asymmetric crop, overlap-vs-IoU, imbalance strategy
- [ ] **P3.2** **T1.5** quantified XAI localisation agreement
- [ ] **P3.3** Re-run the literature check immediately before writing Related Work — the field moved three times in four months
- [ ] **P3.4** Draft the research paper against the target venue's format
- [ ] **P3.5** **Go / no-go decision on ISBI 2027 by 20 September.** If R1–R6 (§B.2) are not done and written by then, drop it and target a journal.
- [ ] **P3.6** Ethics statement, data-availability statement, CLAIM checklist as supplementary

## Ongoing / stretch

- [ ] **P4.1** `PUBLICATION_TODO.md` Tier 2 — learned keypoint head, annotated Tier 1b validation, confounder-stratified performance, calibrated abstention
- [ ] **P4.2** If a curated de-identified clinical subset becomes shareable, consider a dataset/resource paper (MICCAI Open Data track or *Scientific Data*) — a genuinely separate third publication
- [ ] **P4.3** Log every new result into `../results/RESULTS_LOG.md` per `CLAUDE.md`, so the paper writes itself from the log rather than from memory

---

# PART G — What I could not verify (check these yourself)

1. **Scopus indexing status of every journal listed.** The official source list requires login. All indexing claims here are secondary. **Verify via your university library before submitting.**
2. **India's eligibility tier** for Springer Nature / BMC APC waivers. The pages reference "lowest income countries" without naming India. Ask the publisher directly.
3. **Whether CVIP 2026 proceedings are Scopus-indexed.** Springer LNCS/CCIS usually is; the conference site does not state it.
4. **Exact APCs for MDPI journals other than Diagnostics.** The July 2026 MDPI update page did not list Dentistry Journal, Applied Sciences, Bioengineering, Healthcare, or JCM.
5. **Journal of Dentistry APC** — the Elsevier open-access options page is blocked by robots.txt.
6. **IEEE EMBC 2027 dates and deadline** — not confirmed from a primary source.
7. **[Mehta et al. 2026 explainability review](https://onlinelibrary.wiley.com/doi/10.1002/cre2.70375)** — fetch returned HTTP 403. Title and venue verified; contents not. Read before citing.
8. **Whether your survey's central gap claim survives DentFound.** I read the abstract and framing; you need to read the full paper and make the call.

---

## Sources

Journals and fees: [Dentomaxillofacial Radiology instructions](https://academic.oup.com/dmfr/pages/general-instructions) · [DMFR on Scimago](https://www.scimagojr.com/journalsearch.php?q=16649&tip=sid) · [Oral Radiology submission guidelines](https://link.springer.com/journal/11282/submission-guidelines) · [BMC Oral Health publishing](https://link.springer.com/journal/12903/how-to-publish-with-us) · [Diagnostics APC](https://www.mdpi.com/journal/diagnostics/apc) · [MDPI 2026 APC update](https://www.mdpi.com/about/apc-2026-2) · [Scientific Reports open access fees](https://www.nature.com/srep/open-access) · [IEEE Access APC](https://ieeeaccess.ieee.org/about/article-processing-charges/)

Conferences: [ISBI 2027 call for papers](https://biomedicalimaging.org/2027/contributors/papers/) · [ISBI 2027](https://biomedicalimaging.org/2027/) · [CVIP 2026](https://cvip2026.nitc.ac.in/index.html) · [MICCAI 2026 Open Data track](https://conferences.miccai.org/2026/en/MICCAI-2026-Open-Data-Call-for-Papers-and-Reviewers.html)

Standards: [CLAIM 2024 update](https://pubs.rsna.org/doi/full/10.1148/ryai.240300) · [PRISMA 2020](https://pubmed.ncbi.nlm.nih.gov/33782057/) · [Reporting checklists in dentistry](https://pmc.ncbi.nlm.nih.gov/articles/PMC12756637/)

Literature (2026 additions for the survey): [DentFound](https://www.nature.com/articles/s41551-026-01713-8) · [Oral Radiology keypoint staging](https://link.springer.com/article/10.1007/s11282-026-00921-x) · [YOLO26 on DENTEX](https://arxiv.org/abs/2604.16231) · [Sci Rep bone-loss severity](https://www.nature.com/articles/s41598-026-38061-1) · [DentiAsk](https://arxiv.org/abs/2607.08790) · [Frontiers in Medicine caries translation](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1879708/full) · [Healthcare translational readiness](https://www.mdpi.com/2227-9032/14/13/1952) · [DMFR APPRAISE-AI meta-analysis](https://academic.oup.com/dmfr/article/54/2/89/7917334)
