# What changed from the ten-page draft, and why

The prior version is `paper/paper.md`, built to `paper/ieee/main.pdf` (ten pages, 2 Nov 2026). It is
left unchanged. This version, `paper/v2/`, was rebuilt from the repository's saved evidence with the
Research Communication Engine in restructure mode: the evidence was re-read, a claim map was built and
confirmed by the authors, and the text was written from that map. Text from the prior version was
reused only where the new outline had a place for it.

No experiment was run and no result changed. Every number comes from a saved file in the repository.

## The round-1 review items

The first review round (`paper/ieee/review/2026-11-02_panel_round1.md`) set 21 items. Before this
version, 14 were done, 5 were partly done and 2 were open.

| # | Item | Status before | Status now | What this version does |
|---|---|---|---|---|
| 1 | Reword the localisation conclusion; repeat the per-tooth-type comparison on the external cohort | partly done | partly done | The conclusion says "consistent with reading the image" and names the confounds (Section VII-A). The external per-tooth-type comparison still needs the raw Ningxia images, which are not on this machine. It is stated as open (Sections VI-B and IX). |
| 2 | Move Stage 4 and the vision-language detail to a supplement | partly done | done for the six-page version | The full-length version keeps one short paragraph on each. The six-page version moves the detail to the supplement. |
| 3 | State the novelty in proportion to prior fields | done | kept | Related Work credits the earlier input-blind baselines and says what is new here. |
| 4 | Small-sample interval beside the random-effects interval | done | kept | Section VI-B and the methods give both intervals. |
| 5 | Estimation framing; the external lead is optimistic by construction | done | kept | Section V and Section VI-B. |
| 6 | Near-duplicate check on DENTEX | done | kept | Section V. |
| 7 | Reference standard is panoramic only | done | kept | Limitations. |
| 8 | Cite caries epidemiology for the molar prior | done | narrowed | The source studied children, so the sentence now says so. |
| 9 | Say that the severity stage is not evaluated | done | kept | Section IV. |
| 10 | Learned position-only floor, content ablation, site probe | open | open | These are new experiments. They are listed as open checks in the conclusion. |
| 11 | Code and data availability statement | open | open | It needs your release decision. A marked placeholder is in the paper. |
| 12 | The constant's prior mass is "as placed by our front end" | done | kept | Section III-D. |
| 13 | Mark the development-versus-external row as not specific to the theory | done | kept | Table 6. |
| 14 | Scope the title and the conclusion | done | kept | The title names caries scores on panoramic radiographs, and the conclusion is scoped to these cohorts. |
| 15 | Stability of the fitted constant | done | kept | Section III-C. |
| 16 | Image-blind operating curve | done as a table column | done as a figure | New Figure 5 places each system against the curve of image-blind lists, drawn from the saved round-1 analysis (`scripts/figures/make_v2_operating_curve.py`). |
| 17 | Single-run caveat | done | kept | Limitations. |
| 18 | State the assumption behind the closed form | done | kept | Section III-B. |
| 19 | Define deep caries; name the abnormality types; link numbering errors to the identity chain | partly done | partly done | The abnormality types are named, and the link to the identity chain is made in Section VI-C. A radiographic definition of deep caries is still missing: no checked source in the bibliography states it. |
| 20 | Hardware for the runtime; vision-language prompting caveat | partly done | partly done | Both caveats are in the Limitations. The processor model still needs your input. |
| 21 | Fewer numbers in the abstract; a boxed checklist | partly done | done | Table 7 is the checklist of what to report. The abstract leads with the floor and the external result. |

## Other changes

- **The argument is organised by the three research questions.** Each Results subsection opens with the question it answers and ends with what the result does not show.
- **Two unsupported numbers were removed.** The prior version stated a median lesion area of 731 pixels and a tooth-box area of about 25,000 pixels. No saved file records either.
- **One unsupported count was removed.** The prior version said the severity stage was validated on 133 crops. No machine-written file behind this version records that count, so the text now says "only on development crops".
- **One repair result was left out.** The per-tooth-type threshold repair (F1 +0.006) is recorded only in the project's scoreboard, not in a saved run file. The integrity check flagged it, so the paper now reports four repairs of the crop classifier instead of five. It is a null like the others, so leaving it out favours no claim.
- **The repairs are described as they were run.** Three were registered against a same-day control; the earlier retrain with 2.67 times the positives was compared against the shipped model. The prior version said all five had same-day controls under a registered rule.
- **The adoption rule is quoted exactly.** Its 1.5-times cap on flagged teeth is against the constant only, not against both comparators.
- **Three literature citations were narrowed to what their sources support:**
  - Mohammad-Rahimi et al.: the accuracy range is for classification models only.
  - Batchelor and Sheiham: first-molar susceptibility, in children.
  - Bizjak and Robič: the external sensitivity is printed together with its patient-level specificity. That paper's own table gives 0.64 where its text gives 0.67; this is recorded in `open_issues.md`.
- **One citation was added.** Oakden-Rayner et al. 2020, on hidden failure subgroups, suggested by the round-1 review and verified.
- **The authors' design reasons are stated where a reader first meets each design.** This covers the closed form, the modular pipeline, the adoption rule fixed in advance, and the detector decision reported as one taken against its registered guard.
- **Limitations are split by who states them.** The authors' nine come first; the writer's two caveats follow, marked "Additional caveats".
- **Figures.** The training-curve figure moves to the supplement. The walkthrough and outcome figures are printed wider, because reviewers could not read their labels.
- **Length.** The full-length version is about eleven pages. The six-page version is cut from it and is listed in `open_issues.md` with what it leaves out.
