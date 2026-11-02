# Response to reviewers, round 1 — ten-page draft

Answers the 21-item roadmap of `2026-11-02_panel_round1.md` (decision: Major revision). Stage 4
(REVISE) of the academic-research-skills pipeline, applied to `paper/paper.md` and rebuilt into
`paper/ieee/main.pdf`.

**Provenance.** The panel and this response were written by the same model in one session. The
reviewer seats are personas with separate briefs, not independent referees, so this response
cannot settle a disagreement the way an editor would. A human read, and the Stage 3′ re-review,
are still due.

**Scope of this round.** This round had two passes on 2 Nov.
- **Pass 1:** the text items, plus the editing items as far as the page budget allowed.
- **Pass 2:** four analyses from saved data (items 4, 6, 15 and 16; `RESULTS_LOG` 2026-11-02d,
  `outputs/review_round1/README.md`).

Line numbers in pass-1 rows refer to `paper/paper.md` after pass 1. Pass 2 moved some text, so its
rows give sections instead.

## Status by item

| # | Item | Status | Where | What changed |
|---|---|---|---|---|
| 1 | RQ2 conclusion; per-type comparison on Ningxia | **Partial** | VII ¶RQ2 (l. 264); VI-D (l. 229); Table 7 | **Done:** reworded to what was shown: "can express a positional prior only at a cost in precision (Section III-E)", led on the external sites with fewer flags, and per-type precision on the development corpus. **Done:** VI-D now labels the per-type percentages as DENTEX, and the Table 7 row says "per-type on DENTEX only". **Not run:** the Ningxia per-type comparison. The saved Ningxia outputs hold per-image counts only, with no per-tooth codes, so it needs a frozen-pipeline re-run on the raw images, which were not on this machine (`outputs/review_round1/README.md`). **Done (pass 2):** the introduction's RQ2 called localisation "a task a positional prior cannot satisfy", the same overclaim; it now reads "a task a fixed list cannot perform". |
| 2 | Move Stage 4 and VLM detail to a supplement | **Partial** | VI-F (l. 245); II | **Done:** the VLM-controls and Stage-4 subsections merged into one paragraph ("Controls outside the caries pipeline"), every number kept; the bone-loss clause (Cerda et al.) dropped from Related Work. **Not done:** no supplement exists. |
| 3 | Novelty in proportion | **Done** | I (l. 23, 25) | Input-blind baselines are credited to VQA and NLI. The contribution is stated as bringing the floor to tooth-level caries scoring, with a closed form and multi-cohort, multi-site measurement. "We test these predictions" became "We examine these consequences", because the theory is post hoc. |
| 4 | HKSJ beside DL; τ² uncertainty | **Done** | III-F; VI-D | HKSJ +9.61 [−5.02, +24.24] beside DL [−0.54, +19.76]; τ 9.27 pp, Q-profile [3.22, 33.09]. Cited: IntHout et al. 2014, Viechtbauer 2007, both generated from Crossref and checked against their abstracts. Still labelled post hoc. |
| 5 | Selection and multiplicity | **Done** | V Statistics (l. 164) | Estimation framing, no multiplicity correction stated, and the Ningxia lead called "optimistic by construction". |
| 6 | Perceptual-hash near-duplicate check on DENTEX | **Done** | V Cohorts; VIII | pHash and dHash against all 1,389 other DENTEX images. Positive control: the 86 MD5 copies come out at distance 0. The 20 closest scored images were inspected by eye, and each differs from its neighbours in restorations or missing teeth: no further leak. Limitation added: a second radiograph of the same patient cannot be found this way. |
| 7 | Reference-standard limitation | **Done (wording)** | VIII bullet 3 (l. 270) | Panoramic-only labels; proximal caries detected less accurately than with bitewings [Akarslan et al. 2008, *Dentomaxillofac. Radiol.* 37:458, doi 10.1259/dmfr/84698143]; part of the molar prior may reflect what panoramic labels capture. Re-reading the labels (optional) was not done. |
| 8 | Caries epidemiology for the molar prior | **Done** | III-B (l. 73) | First molars as the most caries-susceptible teeth [Batchelor and Sheiham 2004, *BMC Oral Health* 4:2, doi 10.1186/1472-6831-4-2]; the floor depends on the population's age and exposure. |
| 9 | Severity (3b) unvalidated | **Done (wording option)** | IV (l. 129) | "validated on 133 crops in development and is not evaluated here". |
| 10 | Learned position-only floor; content ablation; site probe | **Planned** | — | New experiments; outside this round. |
| 11 | Availability statement; release the floor computation | **Open** | — | Needs the authors' release decision (licences: DENTEX CC BY-NC-SA; Tufts pixels not redistributable). |
| 12 | Prior mass "as placed by our front end" | **Done** | III-C (l. 89) | "This prior mass is the cohort's, as placed by our front end". |
| 13 | Table 7 development-vs-external row non-specific | **Done** | Table 7; VII ¶1 (l. 251) | Row verdict "holds; not specific (domain shift)"; the text says one implication "does not single out the theory". |
| 14 | Title and conclusion scope | **Done** | Title; abstract; IX (l. 275) | Title says "Caries Score". The abstract's last sentence is scoped to "On these cohorts". The conclusion says "The floor differs between populations" and that the detector's lead is "pooled over four external sites". |
| 15 | Stability of the fitted constant | **Done** | III-B | Rule (3) refitted on 10,000 resamples of the 78 fit images. It returns exactly the eight molars 27% of the time, but the refits score a median F1 of 0.320, 95% between 0.279 and 0.330. The membership is fragile; the floor is not. |
| 16 | Image-blind operating curve | **Done** | III-B; VI-B; Table 4 | F1 is flat from 6 to 9 codes (0.298–0.325). A matched-volume comparison was added, against an image-blind answer naming as many codes: lesion detector +22.35 [+17.42, +27.18], crop classifier +5.50 [+2.84, +8.22], VLMs level (new Table 4 column). Volume explains neither pipeline lead. |
| 17 | Single-run caveat | **Done** | VI-A (l. 170) | "each is a single run (three seeds for Stage 4a)". |
| 18 | Assumption and generality of (2) | **Done** | III-B (l. 67) | Every named code counts as a prediction, present tooth or not, as the scorer does; applies to any set prediction scored by micro-F1 over a fixed label set. |
| 19 | Deep caries; Stage 4 abnormality types; Fig. 8b and the identity chain | **Partial** | IV (l. 129); VI-E (l. 239) | **Done:** Stage 4 names its label types (apical lesions, sclerosis, cysts). **Done:** VI-E links Fig. 8b to factor two of (1): 8.2% of detected second molars receive a wrong code. **Partial:** deep caries is named as one of the two caries labels DENTEX releases, but no radiographic depth criterion is given. |
| 20 | Runtime hardware; VLM caveat | **Partial** | IV (l. 129); VI-F (l. 247) | **Done:** VLM caveat in the text ("one prompt; decoding settings not recorded"). **Open:** CPU model is an `[ASK AUTHOR: CPU model]` placeholder. |
| 21 | Fewer abstract numbers; boxed checklist | **Partial** | Abstract; VII | **Done:** the abstract drops the external interval for the crop classifier ("it was level with the constant"). **Not done:** a boxed checklist; the "What to report" paragraph in VII stays as prose, for space. |

**Totals after pass 2.** 14 done, 5 partial (1, 2, 19, 20, 21), 2 open (10 new experiments,
11 availability).
Each partial item has a done part and a pending part, both listed in its row.

## Changes beyond the roadmap

- **Acronyms** (suite's acronym check): FDI, AUC, IoU and mAP are now defined at first use.
  DENTEX, UFBA, COCO, MD5, CPU and GPU are left as names or standard terms.
- **Related Work.** An earlier trim had left a fragment in the numbering sentence; it is now a full
  sentence.
- **Related Work.** "Caries and periodontal classification" became "analysis": Lim et al. segment
  caries, they do not classify it.
- **Conclusion.** "led it on four external sites" became "led it, pooled over four external sites".
  The detector leads at three of the four sites, not at each.
- **Table 7.** The localisation row's per-type evidence is labelled as DENTEX-only (see item 1).

## Page budget

Back to ten pages after the text items (they had added most of a column). Restatements were
removed; each number stays elsewhere in the paper.

- **VI-D:** the DENTEX agreement reversal. 0.802 and 0.595 remain in Table 6; 1,439 and 603 in VI-B,
  where a clause now says F1 and agreement rank the two options oppositely.
- **VI-C:** "17 points above, level, 22 below". 17.12 and 22.42 remain.
- **Abstract:** the external interval [−3.86, +5.57]. It remains in VI-C.
- **Elsewhere:** repeated framing in the contributions, III-A, III-D, III-E, VII and IX.
- **Figures:** 4 (0.88 → 0.83 text width), 7 (0.88 → 0.82), 5 and 8 (0.92 → 0.88). Panel titles
  stay legible at 150 dpi. The confidence numbers inside Figure 4's boxes were already very small
  at 0.88; an enlarged inset would fix this in a later round.
- **Tried and reverted:** reflowing the JSON record onto fewer lines, which overflowed the column by
  26 pt.

## Checks after the revision

| Check | Result |
|---|---|
| Build | 10 pages; 0 LaTeX errors, 0 overfull boxes, 0 undefined citations or references; no BibTeX warnings |
| Number trace (`outputs/citation_audit/2026-11-02_ars/trace_numbers.py`) | 367 distinct numbers, 6 untraced. These are the same six as on 2 Nov, each explained there (Zancan's F1 0.979, two values derived from Table 1, the review's 86.1–96.1%, the 97.5th percentile, a table interval end) |
| `scripts/verify_paper_numbers.py` (`paper/main.tex`) | 215 of 215, no drift |
| New references | Both resolve on Crossref and OpenAlex; each abstract supports the sentence that cites it |
| `paper/main.tex` | Its equivalent of the RQ2 sentence already says "pooled, at three of the four hospitals … on a cohort that had also informed its adoption"; no change needed |
| Line endings | `paper.md`, `source.bib`, `md_to_ieee.py` still CRLF |

## Pass 2: page budget and checks

- **Space.** The four analyses added about a column. Recovered with the same facts:
  - Table 7 cells now take one line per row. Two caveats moved out of the Verdict column: "domain
    shift" is in Section VII's text, and "DENTEX" is in the row's evidence.
  - Shorter Table 3 cells and Table 4 row names.
  - The JSON record became one sentence, every value kept.
  - Captions of Figures 2–8 condensed.
  - Three counts in VI-A dropped, because the Figure 5 caption gives them.
  - Figure widths: 4 at 0.80, 7 at 0.78, 5 and 8 at 0.86, 2 and 3 at 0.92 of the text width; 6 at
    0.88 of the column.
  - `md_to_ieee.py` changes: page-wide tables whose cells all fit get natural widths;
    `![Figure N 0.9]` scales a one-column figure.
- **Wording.** VI-B's "by naming 1,537 teeth" became "while naming", since the matched-volume result
  shows the lead is not bought by volume.
- **Checks.**
  - Build: 10 pages; 0 errors, 0 overfull boxes, 0 undefined references; no BibTeX warnings.
  - Number trace: 390 distinct numbers, the same 6 known untraced. `outputs/review_round1/` was
    added to the tracer's sources.
  - `verify_paper_numbers.py`: 215/215.
  - Each new number spot-checked against its JSON.

## Still to do before Stage 3′ re-review

1. **Item 1's Ningxia per-type comparison**, when the raw Ningxia images are available
   (`D:\nangxia_dataset` or the macOS clone). It is a frozen-pipeline inference re-run recording
   per-tooth codes, flags and lesion containment; no training or tuning.
2. **Author inputs:** CPU model (item 20), the release decision (item 11), and the acknowledgment
   wording.
3. **Item 10** (new experiments), if the venue's timeline allows it; otherwise list it as a limitation.
4. **Not yet in `main.tex`:** HKSJ, matched volume, the near-duplicate check, and the
   reference-standard limitation.
5. **Then** the Stage 3′ re-review against this response, and the Stage 4.5 final integrity gate.
