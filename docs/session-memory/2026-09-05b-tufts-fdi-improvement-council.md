# 2026-09-05b — Council: why Tufts end-to-end FDI is 64.8%, and how to raise it

**Session goal:** one line — literature search (firecrawl) + a structured council on the low
Tufts FDI number: diagnose it, list the improvement options with cost/risk/pre-registration
need, and recommend.

## What was done

- **Literature pass** via the firecrawl research connector (`firecrawl_research_search_papers`,
  `firecrawl_research_inspect_paper`, `firecrawl_scrape`) — ~8 query framings, ~15 papers
  triaged, 6 read to method level. Corpus + IDs in the "Literature" section below. No paper is
  cited here without an author/venue/ID; two numbers I could not verify are marked as such.
- **Code review** of `src/fdi_head_inference.py` (`assign_fdi_head` — the deployed head +
  Hungarian) and `src/fdi_assignment.py` (the superseded rank-order baseline) so the options
  below describe what actually exists, not a guess.
- **No model trained, no evaluation run, no manuscript change.** No `RESULTS_LOG.md` entry —
  this session produced no number. `docs/research/` untouched (separate workstream).

## The number, and where the 35.2% goes

Anchor: `RESULTS_LOG` 2026-09-04d/04e, `model_metrics.md` "Tufts end-to-end FDI (4 Sep 2026)",
`PAPER_MATERIAL.md` §8.16. Deployed detector `models/11` (seg) → `models/10` head → Hungarian,
149 frozen-test images, **3,760 permanent GT teeth**, conf 0.25.

| | deployed seg `models/11` | old bbox `models/06` | DENTEX (contrast) |
|---|---|---|---|
| detection recall | 82.4% | 91.2% | 70.6% |
| FDI exact **of detected** | **78.6%** | 78.4% | 82.6% |
| **end-to-end FDI** | **64.8%** | **71.5%** | 58.3% |
| quadrant, of detected | 96.3% | 96.5% | — |

Taxonomy of all 3,760 teeth (`stage2_failure_taxonomy.py`):

| bucket | Tufts | DENTEX | what it is | who owns the fix |
|---|---|---|---|---|
| correct | 64.8% | 58.3% | — | — |
| **not_detected** | **18.2%** | 29.4% | Stage 1 never proposed the tooth | detector (arc closed) / operating point |
| **off_by_one** | **12.6%** | 9.5% | right quadrant, adjacent position | **head + a sequence constraint** |
| same_quadrant_far | 2.0% | 1.1% | counting slip ≥2 | same |
| mirror_lr | 1.3% | 0.9% | right position, wrong SIDE — **43 of 49 are central incisors (midline)** | laterality signal at the midline |
| wrong_arch + other | 1.1% | 0.8% | upper↔lower, misc | small |

**The decomposition is unusually clean:**

1. **Quadrant is already 96.3% right on detected teeth. The failure is the position digit** —
   which is exactly `off_by_one` + `same_quadrant_far`, together **14.6 pp of the 35.2%**, and
   **74% of all Tufts numbering errors** (§8.16). Among *detected* teeth the wrong-code rate is
   20.7% (DENTEX 17.4%).
2. **The head numbers detected teeth at ~78.5% regardless of detector** (`models/11` 78.6%,
   `models/06` 78.4%). The detector only moves recall, hence end-to-end. So there are two
   separable levers: raise recall (detector — the Lever 1→A→Phase 0→A2 arc is closed, all
   ablations; multi-corpus *segmentation* is the one untried idea, already scoped
   post-submission), **or** raise the head's 78.5%-of-detected toward DENTEX's 82.6%+.
3. **~7 pp of the end-to-end gap is a known detector operating-point effect, not numbering.**
   `models/06` (bbox) gets 71.5% e2e purely on recall (91% vs 82% at conf 0.25); lowering
   `models/11` conf to 0.10 makes it *worse* (61.3% — spurious boxes flood the Hungarian). The
   27 Aug bbox→seg swap was a dated human decision that bought +12 pp on DENTEX cross-domain and
   cost 6.7 pp on Tufts in-domain (`RESULTS_LOG` 2026-09-04d insight 3). This is already in the
   paper (§8.16).

**Root causes of the head's off_by_one, each traced:**

- **The Hungarian assignment enforces uniqueness, not sequence consistency.**
  `assign_fdi_head` maximises total joint (quadrant×position) log-prob over a one-to-one
  detection↔code matching. Nothing in it says "detected teeth in a quadrant, ordered along the
  arch, should carry monotonically increasing position digits with a skip only where a tooth is
  genuinely missing." One miscounted tooth shifts a run of neighbours by one. `fdi_assignment.py`
  (the superseded rank-order module) *does* detect gaps (`suspected_gap_before`) but only
  **flags**, never corrects, and has no per-code probabilities to correct with.
- **Covariate shift in the positional features.** `scripts/tufts/README.md`, §8.8b: Tufts
  median normalised tooth height **0.177** vs DENTEX **0.231**. The head eats raw
  `[cx, cy, bw, bh]`; a `cy/bh` distribution mismatch degrades exactly the position digit.
  Input ablation (§8.10): positional features are worth +3.2 pp laterality / +2.8 FDI-exact —
  real but not decisive; the image carries the position digit, the coordinate disambiguates.
- **Tufts scores every tooth including the crowded anterior region;** DENTEX mostly annotates
  posterior pathology (§8.16). Anterior teeth are small, similar, near the midline → both
  `off_by_one` and `mirror_lr` concentrate there (premolars/incisors 22–31% wrong, molars
  9–11%). This is the "class imbalance from uneven tooth-type distribution" and the
  "adjacent / bilaterally-symmetric confusion" named across the literature below.
- **Midline laterality is genuinely hard.** 43 of 49 `mirror_lr` errors are central incisors,
  where |cx − 0.5| ≈ 0 and the positional feature carries almost no side signal. Not a
  mirror-correction bug (verified 3 ways, `tufts_title_to_fdi`) — the head is honestly
  uncertain about side at the exact midline.

## Literature (firecrawl)

| Paper | Venue / ID | What it does | Relevance here |
|---|---|---|---|
| **Zhang et al., "A Reliable Multi-Stage System…" (SADP-Net)** | IEEE JBHI 2025 · doi:10.1109/JBHI.2025.3643805 · pmid:41396752 · code github.com/qklee-lz/SADP-Net · **already cited as `zhang2025reliable`** | 3 stages: supernumerary classifier → **Symmetry-Aware Dual-branch Pyramid Net** (SymAM models bilateral structure) → **dedicated missing-tooth detector + post-hoc FDI index completion**. Evaluated **on Tufts Dental** + O2PR + a multi-pathology cohort. GitHub/abstract report ~F1 91.4, mAP 66.2 on Tufts — **metric definitions NOT verified** (paper paywalled, only abstract + repo landing page read). | The direct comparator (same dataset) and a design template: a missing-tooth stage + a symmetry module are exactly the two things our head lacks. |
| **Lin et al., "Structure-Guided Tooth Numbering…" (ATGI)** | J Imaging 2026 · doi:10.3390/jimaging12060256 · pmcid:PMC13301722 | **Anchor-Teeth-Guided Inference**: find the longest run of predicted codes that matches the canonical FDI pattern (distal→mesial, bilateral symmetry) → anchors → extend numbering bidirectionally by ±1 along spatial order, with a confidence floor + max-interval to stop runaway. Weighted-F1 **0.687 → 0.813 (+12.6 pp)**, biggest gains on low-sample classes. Visible-light photos, 845 images. Stated limitation: breaks on severe crowding / multiple missing teeth. | The blueprint for a **zero-GPU post-processor** on top of our head output (Option A). Domain-agnostic — it operates on a code sequence + spatial order. |
| **van Nistelrooij et al., "Combining public datasets…"** | BMC Oral Health 2024 · doi:10.1186/s12903-024-04129-5 · pmcid:PMC10964594 | OdontoAI (2,000 FDI + instance masks) + DENTEX → 2-stage seg+numbering then diagnosis. FDI numbering costs **~0 mAP** with enough FDI data: mAP 0.848 with FDI vs 0.849 class-agnostic. Performance tracked annotation quality. | Evidence that "more good FDI-labelled data ≈ free numbering." OdontoAI is unused by this project (Option D). |
| **Silva et al., "OdontoAI"** | arXiv:2203.15856 (2022) | 4,000 panoramic radiographs, **2,000 with public FDI + instance-mask labels**, private online eval platform. Brazilian population. "Largest-scale public panoramic dataset." | Option D corpus #1 — a large, diverse, mask+FDI corpus for a head retrain. |
| **MICCAI STS 2024 Challenge** | MICCAI 2024 · arXiv:2511.22911 · pmid:41740303 | 2,380 OPGs with instance-level FDI annotations (part semi-supervised). Chinese population. | Option D corpus #2 — population diversity. |
| **Li, Gao, Lian, Meng, "Spatial Prior-Guided Bi-Directional Cross-Attention Transformers"** | IEEE TMI 2024 · doi:10.1109/TMI.2024.3406015 · pmid:38801691 | Panoramic. Models "symmetry within jaws + specific order" via bi-directional cross-attention → fixes misID of **adjacent / similarly-shaped teeth**. | Option E architecture reference (2D panoramic, top venue). |
| **Li et al., "Semantic Graph Attention w/ Explicit Anatomical Association"** | IEEE TMI 2022 · doi:10.1109/TMI.2022.3179128 · pmid:35635829 | CBCT. A semantic graph over teeth encoding anatomical associations, explicitly to control "bilaterally symmetric confusion". | Option E graph reference. |
| **Chung et al., "point-wise localization + distance regularization"** | Artif Intell Med 2021 · doi:10.1016/j.artmed.2020.101996 · pmid:33461689 | Panoramic. Localizes **missing teeth** explicitly, plus a distance-regularization term between teeth. | Precedent for treating missing teeth as first-class. |
| Wang et al., "STSN-Net" | Diagnostics 2024 · doi:10.3390/diagnostics14050497 · pmcid:PMC10930500 | "Crowded environments"; deformable + dilated conv for receptive field. Its graph module is for **bone-window** segmentation, not numbering. Private data (F1 98.49% not comparable). | Weak — receptive-field tricks, not a numbering method. Noted so nobody re-reads it. |
| (branched SSD + integration processing) | PMC9214417 (2022) | Post-processing to integrate two nets and **explicitly differentiate left/right** teeth. | Precedent for an explicit L/R post-processing step (the `mirror_lr` bucket). |
| B-Spline Embedded Structure Learning | arXiv:2608.17291 | Fits a parametric B-spline to tooth centres → continuous arch-topology constraint. 3D. | Elegant framing of the arch prior; longer-term idea. |

**Recurring message across 6+ of these:** the fix for adjacent/symmetric/off-by-one numbering
errors is an **explicit anatomical/structural prior** — arch continuity, FDI sequence, bilateral
symmetry — applied as (a) post-processing sequence repair, (b) a graph over teeth, (c) a
spatial-prior transformer, or (d) a continuous topology constraint; **plus** treating missing
teeth as a first-class stage rather than letting a contiguous-arch assumption fail silently.
This project's Hungarian assignment does neither.

## The council

**Voice 1 — paper strategy.** Track A (manuscript + compliance) is the critical path and wins
any time conflict (`transfer.md` §3). The manuscript is complete, compiles, 127/127 verified.
64.8% end-to-end is **reported honestly** with the full 7-bucket taxonomy, the 78.6%-of-detected
conditional, the 71.5% bbox reference, and the "detection-bound, not numbering-bound" argument
(§8.16, `RESULTS_LOG` 2026-09-04d). The paper's thesis is the constant-baseline /
external-validation methodology, not SOTA numbering — and numbering is explicitly framed as
*a task a constant cannot do at all* (`main.tex` `sec:numbering`). A pre-submission architecture
or data lever risks the timeline for a number that isn't the paper's point. **But** a zero-GPU,
zero-DENTEX-risk, pre-registered structural post-processor fits the paper's own established
pattern (it already reports 5 failed caries repairs + 4 detector ablations honestly): pass → a
small positive result; fail → another honest "the structural fix didn't move it" data point.
Either outcome is publishable and cheap.

**Voice 2 — skeptic.** This project's base rate on "lift the number" attempts is **0 of 9
adopted** (5 caries-gate repairs, Levers 1/A/A2/2 — Lever B is the sole exception, and it
changed the *task*, not the model). ATGI's +12.6 pp was on 845 visible-light photos with a weak
base model (YOLOv12s F1 0.687); our head is already at 78.6%-of-detected, far less headroom.
Realistic expectation for a post-processor: **+1 to +3 pp of-detected, and it can fail its
bar.** A chunk of `off_by_one` is genuinely ambiguous — a real missing tooth and a missed
detection are indistinguishable from a box list, so a sequence-repair pass that assumes
contiguity will *create* errors on the crowding/agenesis cases (ATGI's own stated failure
mode). And it adds a bespoke heuristic with its own frozen thresholds to a pipeline whose
selling point is simplicity + reproducibility — it needs its own `tests/` + a
`verify_invariants` entry + a never-swept threshold set. Do not oversell; treat as a genuine
experiment with a real chance of a null result.

**Voice 3 — systems / methods.** The decomposition says the hard part (quadrant, 96.3%) is
solved; the failure is purely the position digit. That is the *ideal* target for a sequence
constraint. Cleanest design: **do not replace the Hungarian** — add a post-Hungarian repair
pass that (i) sorts detected teeth in each quadrant by arch position, (ii) compares the
assigned position-digit order against that spatial order, (iii) only where they disagree *and*
the head's own second-choice would restore monotonicity *and* the confidence margin is small,
flips to the sequence-consistent code, (iv) respects detected gaps (a wide spacing = a missing
tooth = a legitimate skip — reuse `fdi_assignment.py`'s existing `gap_factor` logic). Also
cheap and worth doing *first*: the **positional-feature diagnostic** — re-score Tufts
of-detected with the head's positional features (a) raw, (b) zeroed, (c) rescaled to the DENTEX
training distribution. One day, CPU, tells us whether the covariate shift is actually a lever
before anyone considers a retrain. And restate for the paper: lead the Tufts numbering
discussion with **of-detected 78.6%** (detector-independent, the number comparable to prior
work's pre-cropped accuracies), not 64.8% e2e.

**Voice 4 — pre-registration / discipline.** `transfer.md` §4: no GPU spend without a written
pre-registration and explicit go-ahead. A post-processor is zero-GPU but still a Track-B lever
that produces a paper number — treat it with full Lever discipline: a frozen acceptance rule
*before* any code, a paired cluster bootstrap over the 149 Tufts test images, a DENTEX
no-regression guard, `RESULTS_LOG` + session-memory on completion. Write
`outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md` (Lever B template) first. GPU
options (D, E) need §4's written pre-registration + go-ahead and are post-submission; they get
added to `docs/research/PUBLICATION_TODO.md` **by the research workstream, not this session.**

## Options

| # | Lever | GPU? | Cost | Expected on Tufts | Risk | Status |
|---|---|---|---|---|---|---|
| **A** | **Anatomical sequence post-processor** (ATGI-style) on the head output — anchor on high-confidence FDI-consistent runs, repair position digits that disagree with arch order, respect detected gaps | **No** | ~3–5 days, CPU, few hundred lines in `src/` + tests | targets `off_by_one`+`same_quadrant_far` (74% of errors) + midline `mirror_lr`; plausibly **+2 to +6 pp of-detected**, could be null | can introduce errors on crowding/agenesis; adds heuristic complexity | **pre-registerable now** |
| **B (diag)** | **Positional-feature shift diagnostic** — re-score Tufts of-detected with pos-feats raw / zeroed / DENTEX-normalised | No | ~1 day, CPU | none directly — tells us if a normalisation fix in a future retrain is worth it | low | **do now, cheap** |
| C | Use bbox `models/06` for Tufts (71.5% e2e, already exists) | No | 0 | +6.7 pp e2e — but this is a detector operating-point effect, **already reported** (§8.16) | reverting the default is off the table (benchmark continuity, dated decision) | **already done — reporting only** |
| D | Retrain the head with OdontoAI (2,000) + MICCAI STS 2024 (2,380) as 3rd/4th FDI corpora | **Yes** | crop-build (days) + ~1–2h GPU/arm + eval | population diversity; van Nistelrooij evidence says numbering ≈ free with enough FDI data — but head-v3 (`models/12`, +Kaggle-dual) was an ablation (Tufts n.s.) | Tufts dilution, covariate shift per corpus | **post-submission, needs pre-reg + go-ahead** |
| E | Symmetry-aware head / adapt SADP-Net (on Tufts, code released) or a spatial-prior cross-attention head | **Yes** | weeks — new architecture, training, eval | the literature's strongest lever for exactly this error class | may not reproduce; large scope | **post-submission future work** |
| F | Do nothing to the number; fix only the framing (lead with of-detected 78.6%, keep the honest taxonomy + bbox reference) | No | ~0 | 0 | 0 | **the default if Track A time is tight** |

## Decisions made

- **This session decides nothing that spends GPU or changes a paper number.** It is analysis +
  a recommendation; the go/no-go on Option A is Deepak's.
- **Recommended sequence, if a stronger Tufts numbering story is wanted before submission:**
  Option B-diagnostic (1 day) → then Option A as a **pre-registered zero-GPU ablation**, bar =
  Tufts FDI-exact-of-detected Δ vs Hungarian-only ≥ +2 pp (lower bound, paired cluster
  bootstrap over the 149 test images), guard = DENTEX end-to-end Δ ≥ −1 pp (lower bound), adopt
  iff both, bar frozen before code. Total ~1 week, no GPU. Pass → adopt + report; fail → report
  as an honest null.
- **Recommended regardless (zero effort):** ensure `PAPER_MATERIAL.md` §8.16 / `main.tex`
  `sec:numbering` lead the Tufts discussion with **of-detected 78.6%** and present 64.8% e2e as
  detection-bound with the 71.5% bbox reference. `RESULTS_LOG` 2026-09-04d follow-ups (1)/(2)
  flag this — verify it landed.
- **D and E are post-submission future work.** Not queued, not pre-registered. If pursued they
  need `transfer.md` §4's written pre-registration + explicit go-ahead. Adding them to
  `docs/research/PUBLICATION_TODO.md` is the research workstream's call, not this session's.
- **Did not touch `docs/research/`** (separate workstream) or `transfer.md` (no state change —
  nothing finished, nothing queued).

## Open questions

- **Is Tufts e2e 64.8% actually a submission liability?** The paper's thesis does not rest on
  numbering SOTA, and the number is honestly decomposed. If a mock-reviewer read does not flag
  it, Option F (framing only) is the right call and Track A wins. **Deepak's call.**
- **SADP-Net's actual Tufts numbers.** The "F1 91.4 / mAP 66.2" seen on the GitHub landing page
  and abstract could not be pinned to a metric definition (IEEE JBHI paywalled). Someone with
  Xplore access should read Zhang et al. 2025 Table(s) directly before it is cited as a
  numbering comparator — the current `zhang2025reliable` cite in `main.tex` only claims
  "mAP 66.2%, AP50 97.3%", which is safe.
- **Does Option A's contiguity assumption survive Tufts' anterior crowding?** ATGI itself fails
  there. The pre-registration must include a stratified check (crowded/missing-heavy images vs
  the rest) so a headline +2 pp isn't hiding a regression on the hard subset.
- **Would a head retrain (D) dilute Tufts the way the multi-corpus detector did?** Head-v3's
  Tufts result was n.s. — weak prior. OdontoAI + STS are bigger and more diverse than
  Kaggle-dual, but the covariate-shift risk (per-corpus tooth-size distribution) is real and
  unmeasured.

## Next steps

1. **Deepak:** decide whether the Tufts numbering story needs strengthening pre-submission at
   all (Option F vs A), given Track A is the critical path.
2. If yes → run Option B-diagnostic (1 day, CPU, no pre-reg needed — it produces no paper
   number, only a direction check).
3. If B suggests the head has headroom → write
   `outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md` (Lever B template), freeze the
   bar, then implement Option A behind a `--assignment structural` flag (default off), with
   `tests/test_fdi_structural_repair.py` and a `verify_invariants` entry.
4. Independently: verify the §8.16 framing fix (lead with of-detected) landed in `main.tex`.
5. Post-submission only, and only with go-ahead: Options D (OdontoAI + STS head retrain) and E
   (symmetry-aware head / SADP-Net) — via a fresh pre-registration each.
