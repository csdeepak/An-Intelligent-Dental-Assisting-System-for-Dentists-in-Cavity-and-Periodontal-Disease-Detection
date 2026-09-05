# 2026-09-06b — Council: pre-registering Lever C (structural FDI post-processor)

**Session goal:** write the pre-registration for Option A from the Tufts-FDI council
(now "Lever C"), and council its design decisions. Not implement — the pre-registration is a
document; the freeze and the code wait on Deepak's go/no-go.

## What was done

- Wrote `outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md` following the Lever B
  template (`outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md`): hypothesis → what it
  is/isn't → method (frozen) → evaluation (frozen) → acceptance rule (frozen) → risks → local
  gate → cost.
- Added the `.gitignore` exception so the pre-registration and its future JSON artefacts are
  tracked (same pattern as `!outputs/lever_B_lesion_caries_path/`), no weights (zero-training
  lever).
- Re-read `src/fdi_head_inference.py`, `src/fdi_assignment.py`,
  `scripts/eval/validate_fdi_assignment{,_tufts}.py`, `scripts/eval/bootstrap_ci.py` to make the
  method spec match what exists.
- **`find-skills` (`.claude/skills/find-skills/SKILL.md`) — checked, not used.** Pre-registration
  in this repo has an established in-repo template cited across `transfer.md`, `RESULTS_LOG.md`
  and every prior lever; an external skill would add a dependency without beating it. Not
  running `npx skills` without a request.
- No model, no evaluation, no `RESULTS_LOG` entry (a draft plan is not a milestone — Lever B's
  pre-reg got its entries when it ran, not when it was drafted).

## The design, and the choices behind it

**Method class — order-constrained maximum-likelihood re-labelling of the position digit only.**
Quadrant stays from the head (Option B: 97.4% Tufts / 99.0% DENTEX). Per quadrant, teeth sorted
by arch position; anchor on the longest strictly-increasing run of head position-argmaxes among
teeth with confidence ≥ τ; fill the gaps between anchors with the arch-order-monotonic labelling
that maximises the head's own Σ log p.

- **Why not pure rank-order (`fdi_assignment.py`)?** It ignores the head's per-code
  probabilities and has a hard ceiling (§8.10: 66.3% on complete quadrants vs the head's 80.2%).
- **Why not a plain "re-sort the argmax multiset to be monotonic"?** It cannot fix a case where
  the multiset itself is wrong ([3,3,5,6] for four teeth). But it is a fair cheap baseline —
  so it is **arm C-sort**, run alongside the full **arm C-dp**, both reported. If C-sort captures
  most of the gain, C-dp's complexity is not worth shipping.
- **Why anchor rather than force strict monotonicity everywhere?** A complete 8-detection
  quadrant has exactly one strictly-increasing labelling of {1..8} — any unconditional monotonic
  method collapses to rank-order there and would *regress* the case the head already wins.
  Anchoring means those quadrants (usually all-high-confidence, already monotonic) pass through
  unchanged.
- **The one hyperparameter is τ, frozen to the codebase's existing `LOW_CONFIDENCE = 0.30`** —
  never tuned on any cohort. `gap_factor = 1.6` for the missing-tooth skip is inherited a-priori
  from `fdi_assignment.py`. Nothing else is tunable.

**Bars.** Primary: Tufts FDI-exact-of-detected Δ vs Hungarian, lower bound of the 95% CI
≥ **+2.0 pp** (paired cluster bootstrap over the 149 test images, `bootstrap_ci.paired_bootstrap`,
seed 42). Guard: DENTEX FDI-exact-of-detected **and** end-to-end Δ, lower bound ≥ **−1.0 pp** on
both. Stratified: anterior (pos 1–3) Tufts Δ point estimate ≥ **−2.0 pp**. Adopt as the
`run_inference.py` default iff all three; else retain as `--assignment structural` opt-in and
report as an ablation.

## The council

**Voice 1 — methods.** The DP is principled, not a heuristic: it is the max-Σ-log-p monotonic
labelling, exact in O(N·8²). The real design risk is the full-quadrant collapse to rank-order,
which the anchoring mitigates and the two-arm design (C-sort vs C-dp) plus the stratified check
will expose if the mitigation fails. Trusting the head's quadrant (not the Hungarian's joint
re-assignment) is right — Option B measured it at 97%+ and the joint Hungarian can move a tooth's
quadrant to satisfy global uniqueness, which is exactly the kind of side effect a position-only
post-processor should not inherit.

**Voice 2 — skeptic.** Three concrete ways this ends badly, all now covered by the frozen rule:
(a) a real +2–3 pp effect with a wide interval lands *below* the +2.0 pp lower-bound bar → a
"null" verdict on a genuine improvement; accepted, because the alternative is post-hoc bar
adjustment. (b) The DP helps the posterior and quietly hurts the crowded anterior (ATGI's own
failure mode) → the anterior stratified condition catches it. (c) It regresses complete quadrants
→ the DENTEX guard and the C-sort/C-dp split catch it. Realistic outcome distribution: ~40%
null, ~40% partial (retained flag), ~15% clean adopt, ~5% net harm caught by the guard. The
"0/9 lift-the-number attempts adopted" base rate is *some* evidence but those were all training
bets; a deterministic algorithm exploiting a constraint the assignment genuinely lacks is a
different kind of move.

**Voice 3 — paper strategy.** Every outcome is publishable in a methodology paper: adopt →
"a monotonicity constraint recovers N pp"; null → "an explicit arch-order constraint does not
move it — the limit is the image-derived position estimate (Option B), not the assignment,"
which *strengthens* §8.16. The framing fix (lead Tufts numbering with of-detected 78.6%) ships
regardless and is what actually neutralises 64.8% as a reviewer concern. Track A (manuscript +
the four compliance blockers) wins any time conflict — hence the hard 3-working-day box written
into §8 of the pre-reg. Do not let Lever C compete with the author/venue/compliance decisions.

**Voice 4 — discipline.** The pre-registration freezes the moment it is committed with the
go-ahead: method, τ, the three bars, the two arms. Implementation details left open (DP recurrence
form, tie-breaking, spacing→skip mapping) are committed *before* the first run on Tufts test or
DENTEX and documented in `run_summary.txt` — the local gate in §7 (no-op on clean cases,
synthetic missing-tooth recovery, `pytest`, `verify_invariants`) runs first, and the first real
run is Tufts *val*, not test. On completion, whatever the verdict: `RESULTS_LOG` entry,
`model_metrics.md` if a best number moves, `PAPER_MATERIAL.md` §8.16, a session-memory file, and
this file annotated with the frozen commit hash. `docs/research/` is not touched.

## Decisions made

- **Pre-registration written as a DRAFT, not frozen.** It freezes on commit-with-go-ahead. This
  session commits the draft alongside the other doc updates so it is on the record and
  reviewable, but the "FROZEN <date>, before any code" line is filled in only when Deepak says go
  — exactly how Lever B's was handled (drafted 2 Sep, frozen 4 Sep after a review round found
  four defects).
- **Two arms (C-sort, C-dp), both reported.** Mirrors Lever B's B-single/B-pooled — it answers
  "does the DP earn its complexity" with a measurement instead of an assertion.
- **τ = 0.30, not a new tunable.** Reusing the codebase's existing `LOW_CONFIDENCE` removes the
  last degree of freedom that could be fished.
- **3-working-day hard box**, written into the pre-reg — the user's own condition, enforced.
- **`docs/research/` untouched** (separate workstream); D/E remain post-submission.

## Open questions (for the review round, before the freeze)

- **Is +2.0 pp the right primary bar?** The council's realistic estimate is +1 to +3 pp. A
  looser bar (+1.0 pp lower bound) would let a modest-but-real effect adopt; a tighter one keeps
  the "simplicity cost" honest. Deepak / mentor call.
- **Should the stratified anterior condition be a hard bar or just reported?** Currently a hard
  condition (point estimate ≥ −2.0 pp). Making it report-only would let a net-positive method
  adopt even with a small anterior cost — arguably fine if the posterior gain dominates.
- **Adopt-as-default vs always-retained-flag?** The pre-reg says adopt-as-default iff all three
  bars. An alternative: always ship it as an opt-in flag and never change the default, so every
  pre-Lever-C number stays the literal default — matching how the caries gate is now handled.

## Next steps

1. **Deepak / mentor:** one review round on the pre-registration — the three open questions
   above, plus a sanity check that the method as written is what's wanted. Then go/no-go.
2. On **go:** fill the "FROZEN" line, commit, then implement per §7's local gate → C-sort and
   C-dp → the four eval runs → `bootstrap_ci` → verdict. 3 working days, then stop regardless.
3. On **no-go:** annotate `PRE_REGISTRATION.md` `NOT PURSUED — <reason>`, ship Option F (the
   §8.16 framing fix — already staged in `PAPER_MATERIAL.md`), done.
4. Either way: verify the of-detected-78.6%-first framing lands in `main.tex` `sec:numbering`.
