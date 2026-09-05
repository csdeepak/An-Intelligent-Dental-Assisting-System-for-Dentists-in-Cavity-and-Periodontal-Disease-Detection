# 2026-09-06 — Option B run: the Tufts-FDI positional-feature-shift hypothesis, falsified

**Session goal:** run Option B from the 5 Sep Tufts-FDI council
(`2026-09-05b-tufts-fdi-improvement-council.md`) — the zero-GPU positional-feature-shift
diagnostic — and record what it says about the improvement options.

## What was done

- Wrote `scripts/eval/tufts_pos_feat_diagnostic.py` (~130 lines) — a direct extension of the
  existing `scripts/eval/ablate_head_inputs.py`, pointed at the **deployed head** (`models/10`,
  DENTEX+Tufts v2.0) and **both corpora**, on **GT-box crops** (no detector in the loop), with
  one extra condition (`dentex_geom`).
- Ran it. ~36 s wall (MPS). Output `outputs/tufts_fdi_pos_diagnostic/pos_feat_diagnostic.json`.
- Full numbers and the milestone reasoning are in `RESULTS_LOG.md` 2026-09-06. Headline:

  | condition (GT-box crops, argmax) | DENTEX val FDI-exact | Tufts test FDI-exact | Tufts position digit |
  |---|---|---|---|
  | full | 91.0% | **71.5%** | **73.5%** (DENTEX 91.9%) |
  | no_position (→ train mean) | 77.5% (−13.4) | 58.0% (−13.5) | 72.2% (−1.2) |
  | shuffled_pos | 52.9% (−38.1) | 39.1% (−32.4) | 72.3% (−1.1) |
  | **dentex_geom** (Tufts feats → DENTEX geometry) | — | **71.6% (+0.1)** | **73.6% (+0.1)** |

- Positional-feature shift confirmed and quantified: DENTEX-train `bh` 0.233 vs Tufts-test
  0.175 (−25%), `bw` 0.045 vs 0.039, `cy` 0.546 vs 0.577, `cx` matched.
- The crop-level Tufts FDI-exact **71.5% reproduces `crop_eval.py`'s published v2.0 Tufts-test
  number exactly** — harness validated.

## Decisions made

- **Crop-level, not end-to-end.** The council's Option B said "re-score Tufts of-detected." GT-box
  crop-level is a *cleaner* isolation of the head (removes detector-box noise) and it reproduces
  a known published number. The end-to-end detector-box re-run was judged unnecessary once the
  crop-level result came back: `dentex_geom` at +0.1 pp does not become a material gain
  end-to-end.
- **Kept the intervention out of `src/fdi_head_inference.py`.** That module has a strict
  "preprocessing contract" and is tested + production. The diagnostic reimplements only the
  ~15 lines of feature handling with a hook, matching `ablate_head_inputs.py`'s pattern (which
  also does its own crop loading rather than calling `assign_fdi_head`).
- **`dentex_geom` is the decisive condition.** `no_position` / `shuffled_pos` confirm the head
  *uses* the positional features (for quadrant/side) — so `dentex_geom` returning +0.1 pp is a
  real "the geometry region does not matter for the position digit," not a "head ignores the
  input" artefact.

## What the result means

1. **The positional-feature covariate shift is NOT a lever.** Mapping every Tufts positional
   feature to the DENTEX-train distribution moves FDI-exact +0.1 pp. A per-corpus
   positional-feature normalisation layer in a future head retrain would buy nothing. Hypothesis
   cleanly falsified — and that is a useful result: it removes a candidate and saves a wasted
   retrain.
2. **The Tufts gap is the image-derived position digit** — 73.5% vs DENTEX 91.9% (18.4 pp),
   while SIDE (97.8 vs 99.1) and quadrant (97.4 vs 99.0) are nearly matched. The ResNet18
   backbone + position head cannot tell, from a Tufts crop's appearance + coordinate, whether a
   tooth is position 4 vs 5 within its quadrant, whereas on DENTEX it can. Consistent with
   §8.16: Tufts scores every tooth including the crowded, similar-looking anterior region;
   DENTEX mostly annotates the large distinctive posterior.
3. **Option ranking updated:**
   - **Option A** (anatomical sequence / arch-order post-processor) — *confirmed* as the right
     lever. It corrects the off-by-one / position-digit error class using arch ordering +
     confident anchors + FDI sequence structure, without needing the head to distinguish
     position 4 from 5 by appearance.
   - **Option D** (retrain with OdontoAI + MICCAI STS 2024) — *weakened*. More FDI-labelled data
     of the same anterior-crowding difficulty is unlikely to move an image-pathway position-digit
     limit, unless those corpora have materially denser/cleaner anterior annotation.
   - **Option E** (a better image-pathway position encoder — higher-res crops, wider context, or
     a spatial-prior transformer like Li et al. IEEE TMI 2024) — this is the post-submission
     lever that would attack the 73.5% directly.
   - **Option F** (framing only) — unchanged; still the right call if Track A time is tight.

## Open questions

- **Why is the Tufts position digit so much weaker (73.5% vs 91.9%)?** The diagnostic localises
  it to the image pathway + anterior crowding but does not fully explain it. Candidate: the 1.5×
  crop on a 25%-shorter Tufts tooth captures less vertical context (fewer neighbouring-tooth
  cusps) than the same crop on a DENTEX tooth. A quick check would be a crop-expansion sweep
  (1.5× / 2.0× / 2.5×) on Tufts crop-level FDI-exact — cheap, CPU, but a *new* experiment, not
  in Option B's scope.
- **Does a crop-level +N pp translate end-to-end?** Not verified here. If Option A is pursued its
  pre-registration must measure end-to-end (detector-box) FDI-exact-of-detected, not crop-level.

## Next steps

1. **Deepak:** go/no-go on strengthening the Tufts numbering story before submission (Option A
   vs Option F). Track A wins any time conflict.
2. If go → write `outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md` (Lever B
   template): frozen bar = Tufts FDI-exact-of-detected Δ ≥ +2 pp lower bound (paired cluster
   bootstrap over the 149 test images), guard = DENTEX end-to-end Δ ≥ −1 pp lower bound,
   stratified check on the crowded-anterior subset. Then implement Option A behind a
   `--assignment structural` flag (default off) with `tests/` coverage.
3. Post-submission only, with a fresh pre-registration each: Option E (image-pathway position
   encoder) as the lever that attacks the 73.5% directly; Option D if OdontoAI/STS turn out to
   have denser anterior annotation.
