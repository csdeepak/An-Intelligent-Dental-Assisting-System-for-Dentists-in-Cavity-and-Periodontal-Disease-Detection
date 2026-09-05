# Pre-registration — Lever C: a structural post-processor for the Stage-2 FDI position digit

**DRAFT written 6 September 2026** as the output of the Tufts-FDI improvement council
(`docs/session-memory/2026-09-05b-tufts-fdi-improvement-council.md`) and its Option B diagnostic
(`docs/session-memory/2026-09-06-tufts-fdi-option-b-diagnostic.md`, `RESULTS_LOG` 2026-09-06).
The council session for this pre-registration itself is
`docs/session-memory/2026-09-06b-lever-c-preregistration-council.md`.

**Bars and method below are open to one round of user / mentor review. They FREEZE the moment
this file is committed with Deepak's go-ahead — same discipline as Levers 1, 2, A, A2 and B.
Zero GPU is involved; the pre-registration is a document, and drafting it commits nothing.**

**Track A (manuscript + the four compliance blockers, `transfer.md` §3/§4) remains the critical
path and wins any time conflict. If pursued, Lever C is time-boxed to THREE working days — if the
primary is not converging by then, it is dropped and Option F (framing only) ships.**

---

## 1. The hypothesis

Tufts end-to-end FDI is **64.8% / 78.6%-of-detected** vs DENTEX 58.3% / 82.6% (`RESULTS_LOG`
2026-09-04d). The failure taxonomy (§8.16): of the 21.4% of *detected* Tufts teeth that get a
wrong code, **74% are `off_by_one`** — right quadrant, adjacent position — and only 3.2% are
category errors. Option B (`RESULTS_LOG` 2026-09-06) localised this precisely on GT-box crops:
**quadrant is 97.4% right and SIDE 97.8%, but the position digit is only 73.5%** (DENTEX 91.9%).
The positional-feature covariate shift was falsified as the cause (+0.1 pp when Tufts geometry is
mapped to the DENTEX distribution) — the weakness is the **image-derived position digit** in the
crowded anterior region Tufts scores and DENTEX mostly does not.

**The gap Lever C attacks:** `assign_fdi_head`'s Hungarian assignment maximises the total joint
(quadrant × position) log-probability over a *one-to-one* matching of detections to the 32 codes.
It enforces **uniqueness** — no two teeth get code 16 — but **not anatomical sequence
consistency**: detected teeth, ordered along the arch within a quadrant, are not required to
carry monotonically-increasing position digits, with a skip only where a tooth is genuinely
absent. A single mis-counted tooth therefore shifts a run of its neighbours by one — the
`off_by_one` cascade. `src/fdi_assignment.py` (the superseded rank-order module) already *detects*
the missing-tooth condition (`suspected_gap_before`, `gap_factor` 1.6) but only **flags** it,
and has no per-code probabilities to correct with.

**The claim under test:** a post-processor that re-labels only the position digit, using the
head's own position-digit softmax under an arch-order monotonicity constraint anchored on
high-confidence teeth, raises Tufts FDI-exact-of-detected by a bootstrap-significant margin
without regressing DENTEX.

---

## 2. What Lever C is, and is not

**Is:** a deterministic, zero-training, CPU post-processing pass applied *after* `assign_fdi_head`,
selectable as `--assignment structural` (default `hungarian` until §5's rule is met). It changes
**only the position digit** of already-assigned teeth; quadrant assignment is untouched.

**Is not:** a change to the detector, the head weights, or the crop contract; a new model; or a
touch on any locked data (no Ningxia involvement — this is a Tufts+DENTEX Stage-2 question). It
does not interact with the caries or bone-loss branches.

---

## 3. Method — FROZEN on commit

Quadrant is taken from the **head's argmax** per tooth (Option B: 97.4% reliable on Tufts,
99.0% DENTEX), *not* from the Hungarian's jointly-reassigned quadrant. Then, per quadrant Q, over
the teeth assigned to it:

1. **Sort** by arch position: ascending `|cx − midline_x|`, `midline_x` = image centre — the
   identical ordering `src/fdi_assignment.py` already uses.
2. **Anchors** = the **longest strictly-increasing subsequence** of the head's position-digit
   argmaxes `(a_i)`, restricted to teeth whose position-digit confidence `c_i = max softmax ≥ τ`.
   **τ = 0.30 — the codebase's existing `LOW_CONFIDENCE` constant** (`src/fdi_head_inference.py`),
   frozen, never tuned on any cohort. Ties in "longest" broken by max total confidence.
3. **Non-anchor teeth** get position digits from an **exact O(N·8²) dynamic program** that
   maximises `Σ_i log p_i(d_i)` subject to `d_1 < d_2 < … < d_N` (strictly increasing, d ∈ [1,8]),
   with each run of non-anchor teeth constrained to lie strictly between its flanking anchors'
   digits (or [1,·] / [·,8] at the quadrant ends). A skipped digit inside a run is permitted only
   where the arch-spacing gap before that tooth exceeds `gap_factor` (1.6, inherited a-priori from
   `fdi_assignment.py`) × the quadrant's median spacing.
4. **Empty anchor set** (all teeth below τ) → the quadrant falls back to the Hungarian result,
   flag `structural_no_anchor`.
5. **Cross-quadrant uniqueness:** if a code now appears twice across quadrants (requires two
   quadrants wrong — Option B says < 3%), keep the higher joint log-prob, flag the other
   `structural_collision`, do not emit it.
6. Every tooth whose FDI changed vs the Hungarian result carries flag `structural_repaired`.

**Two arms, so the DP's complexity is shown to earn its keep rather than assumed:**

| arm | method |
|---|---|
| **C-sort** | steps 1–2, then the non-anchor teeth simply take the unused digits between anchors in arch order (no DP, no softmax beyond the anchor selection) — the ~15-line version |
| **C-dp** | the full method above (steps 1–6) |

**The only free hyperparameter is τ, and it is frozen to the existing 0.30.** Implementation
details not fixed here — exact DP recurrence form, tie-breaking inside a run, the
spacing→skip-count mapping — are settled during implementation and **committed before the first
run on Tufts test or DENTEX**, documented in the arm's `run_summary.txt`.

---

## 4. Evaluation — FROZEN

Both arms and the control (unchanged Hungarian) score the **same detector boxes** — deployed
`models/11` seg detector, conf 0.25, NMS IoU 0.50, imgsz 1024 — so the only variable is the
assignment. Harnesses: `scripts/eval/validate_fdi_assignment_tufts.py` (Tufts, 149 frozen-test
images, 3,760 permanent mirror-corrected GT teeth) and `scripts/eval/validate_fdi_assignment.py`
(DENTEX, 164 leak-free `disease/` images, 936 GT teeth), both gaining an `--assignment` flag.
CIs via `scripts/eval/bootstrap_ci.paired_bootstrap` — cluster bootstrap over **images**, 10,000
resamples, seed 42, same primitive every other paired delta in this project uses.

| quantity | cohort | reported |
|---|---|---|
| **PRIMARY** — FDI-exact-of-detected, Δ (arm − Hungarian) | Tufts, 149 images | point + 95% CI |
| end-to-end FDI-exact, Δ | Tufts | point + 95% CI |
| taxonomy shift (`off_by_one`, `mirror_lr`, `same_quadrant_far`) | Tufts | `stage2_failure_taxonomy.py` before/after |
| `structural_repaired` / `structural_collision` / `structural_no_anchor` counts | Tufts | raw counts |
| **GUARD** — FDI-exact-of-detected AND end-to-end, Δ | DENTEX, 164 images | point + 95% CI, both |
| **STRATIFIED** — Tufts FDI-exact-of-detected, Δ, split anterior (pos 1–3) vs posterior (4–8), and images-with-a-detected-gap vs contiguous | Tufts | point estimates per stratum |

---

## 5. Acceptance rule — FROZEN

> **Adopt the better of C-sort / C-dp as the `run_inference.py` default (`--assignment
> structural`) IFF ALL THREE hold:**
>
> 1. **PRIMARY** — Tufts FDI-exact-of-detected Δ vs Hungarian: **lower bound of the 95% CI
>    ≥ +2.0 pp**; AND
> 2. **GUARD** — DENTEX FDI-exact-of-detected Δ **and** end-to-end Δ: **lower bound ≥ −1.0 pp**
>    on both (no meaningful DENTEX regression); AND
> 3. **STRATIFIED** — the anterior (pos 1–3) Tufts Δ **point estimate ≥ −2.0 pp** (a headline
>    gain is not hiding an anterior regression).

**Outcomes, none hidden:**

| outcome | how it is written |
|---|---|
| All three met | Adopt. New §8.16 paragraph: "a monotonicity constraint the Hungarian assignment lacks recovers N pp of the position-digit gap." `main.tex` line ~352 (the Hungarian sentence) updated; Tufts + DENTEX Stage-2 numbers re-reported; full downstream check. |
| Primary met, guard or stratified fails | Retained as `--assignment structural` opt-in, reported as a **partial result** with the DENTEX cost / anterior regression stated explicitly. Default stays `hungarian`. |
| Primary not met (CI includes < +2.0 pp) | Reported as an **honest null** beside the caries-repair and detector-lever ablations: "an explicit arch-order constraint on the position digit does not move the Tufts number beyond noise — the limit is the image-derived position estimate itself (Option B), not the assignment." Strengthens the §8.16 framing. |
| Net harm on Tufts (Δ point estimate < 0) | Same as null, plus the mechanism (which stratum regressed). |

**The bar is not moved after seeing any number. C-sort and C-dp are both reported regardless of
which (if either) is carried forward.**

---

## 6. Risks recorded in advance

1. **Full-quadrant regression.** A complete 8-detection quadrant has exactly one strictly-
   increasing labelling of {1..8}, so any monotonic method collapses to rank-order there — and
   the head *beats* rank-order on complete quadrants (§8.10: 80.2% vs 66.3%). Mitigation: those
   teeth are usually high-confidence and already monotonic → all-anchor → **unchanged**. The
   stratified check + the guard catch it if the mitigation fails. If C-dp regresses complete
   quadrants and C-sort does not (or vice versa), that is a reportable finding about the method.
2. **Contiguity assumption in the crowded anterior.** This is ATGI's (Lin et al. 2026) own stated
   failure mode. The anterior stratified bar (§5.3) exists specifically for it.
3. **Complexity cost to a pipeline whose selling point is simplicity + reproducibility.** Lever C
   adds a deterministic algorithm with one frozen threshold. It ships behind a flag (default off)
   until adopted, with `tests/test_fdi_structural_repair.py` (the no-op-on-clean-cases property,
   the synthetic missing-tooth recovery, cross-quadrant uniqueness) and a `verify_invariants`
   entry. Recorded as a real cost, not waved away.
4. **Detector-box noise is upstream and unfixed.** A spurious detection still poisons a quadrant's
   arch order; Lever C cannot recover a tooth the detector never proposed (`not_detected` 18.2%
   on Tufts is untouched).
5. **The `+2.0 pp` lower-bound bar can "fail" a real but modest effect.** The council's realistic
   estimate is +1 to +3 pp, so a +3 pp point estimate with a wide interval can land below the
   bar. This is accepted: pre-registration means the bar decides, and a retained-flag partial is
   a legitimate, publishable outcome.
6. **It works and the paper gets longer.** Same as Lever B risk 5 — venue is journal-primary
   (`transfer.md` §5), no page-limit fight; not a reason to skip.
7. **Scope creep into a retrain.** If C fails, the tempting next move is "retrain the head with a
   better position encoder / higher-res crops" (Option E). That is **post-submission** and needs
   its own pre-registration — not a same-session pivot.

---

## 7. Local gate — before the first run on Tufts test or DENTEX

1. `--assignment structural` reproduces the **exact** Hungarian FDI codes on ≥ 20 quadrants
   whose head argmaxes are already strictly monotonic (the post-processor is a verified no-op on
   clean cases).
2. Every emitted code is anatomically valid — position ∈ [1,8], zero cross-quadrant duplicates.
3. Synthetic quadrant with a known gap: detections at arch positions of teeth {1,2,4,5},
   GT {41,42,44,45} → the repair emits {41,42,44,45}, not {41,42,43,44}.
4. `pytest` green (incl. the new `test_fdi_structural_repair.py`); `verify_invariants.py` green.
5. First real run is on **Tufts val (150 images, `split_v1`)** — a sanity check, explicitly
   **not** for tuning τ or anything else; if it is visibly broken there, fix before touching the
   frozen test sets.

---

## 8. Cost, fixed in advance

**Zero GPU.** Implementation ~2 days (the DP, the two harness flags, the tests); evaluation ~0.5
day (four re-runs of two existing CPU harnesses + `bootstrap_ci`); write-up ~0.5 day.
**Time-boxed to 3 working days total** — if the primary is not converging by end of day 3, Lever
C is dropped, Option F ships, and this file is annotated `NOT PURSUED — <reason>`.

Deliverables on completion (whatever the outcome): `RESULTS_LOG` entry, `model_metrics.md` update
if a current-best number moves, `PAPER_MATERIAL.md` §8.16, a session-memory file,
`outputs/lever_C_fdi_structural_postproc/{c_sort,c_dp}/run_summary.txt` + the JSON artefacts, and
this file annotated with the frozen commit hash and the verdict. `docs/research/` is **not**
touched by this workstream.
