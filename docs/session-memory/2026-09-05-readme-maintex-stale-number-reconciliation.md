# 2026-09-05 — Root README + main.tex stale-number reconciliation

**Session goal:** one line — read the full doc set for context, then fix the stale numbers in
`paper/main.tex` and the root `README.md` that had drifted since the 4 Sep Lever B adoption and
the 4 Sep parameter re-count.

## What was done

Context pass first: read `transfer.md`, all component READMEs (`src/`, `scripts/**`, `tests/`,
`models/`, `data/`, `docs/`), `model_metrics.md`, `PAPER_MATERIAL.md` in full, `paper/main.tex`
in full, `MASTER_PLAN_2026H2.md`, `PUBLICATION_TODO.md`, `METHODOLOGY_CHANGELOG.md`,
`docs/exploration/README.md`, `RESULTS_LOG.md` 2026-09-04i–l, and the newest session-memory
files. No model trained, no evaluation run, no new number produced — so no `RESULTS_LOG.md`
entry (this file is the whole record).

Verified against the working tree before editing: `pytest` → **159 passed** (run directly);
`verify_paper_numbers.py` → **127 claims, no drift**; `run_inference.py` `DEF_CARIES_LESION_MODEL`
default confirmed at `scripts/run_inference.py:147`; `RESULTS_LOG.md` dated-header count → **128**;
`verify_paper_numbers.py` OK-line count → **127**.

### `paper/main.tex` — one change

- §Reproducibility: "supporting test suite comprises **122** tests" → **159**. Verified by
  running the suite. 122 was correct at the 28 Aug rebuild; `test_orientation_roundtrip.py`
  (37 tests, added 1 Sep) brought it to 159. `verify_paper_numbers.py` does not assert the test
  count, so nothing else moved.

**Deliberately NOT changed in `main.tex`:** the `61.2 M` / `550×` figures in `tab:fdiset` and
the "VLM behaviour" efficiency paragraph. These describe the **C1 experiment**, which was run on
the per-crop caries gate — line 897 ("Everything above scores the per-crop gate") already scopes
all pre-Lever-B Results to the gate, and `tab:stages` (382–398) carries the current default
(97.65 M / 75.29 M) plus the gate variant (83.52 M / 61.16 M). `model_metrics.md`'s own C1
sections still quote 61.2 M for the C1 row. Re-quoting `tab:fdiset` to 75.3 M would pair a gate
F1 (0.294) with a lesion-detector parameter count — the "referent moved" hazard `RESULTS_LOG`
2026-09-04i names. The `main.tex:17` header comment "25 M -> 83.6 M" is a historical
rebuild-changelog note (LaTeX comment, invisible in output) and was left as history.

### `README.md` — ~14 edits, all traced to `model_metrics.md` "Pipeline size" / `RESULTS_LOG`

| Was | Now | Source |
|---|---|---|
| hero alt-text "83.6 M parameters" | "97.7 M parameters" | model_metrics.md total_default |
| "115 dated entries" / "115 entries" (×2) | 128 | `grep -c '^## 20..-..-..'` |
| "asserts 90 manuscript numbers" (×3) + "The 90 manuscript numbers" | 127 | verify_paper_numbers.py OK count |
| Pipeline-stages table row 3a = "Caries gate" (only) | 3a = lesion detector (default); new 3a′ = gate (retained variant) | RESULTS_LOG 2026-09-04h |
| "still weak" callout: "caries precision is 0.40" | "lesion detector has no calibrated confidence / no abstention curve (retained gate's precision 0.40)" | main.tex sec:limits item 1 |
| Results table: no lesion-detector row | added row: DENTEX 45.5% tie / CariesXrays 68.4% / Ningxia 50.0% | model_metrics.md Stage 3 |
| Model-zoo intro "83,564,140 … torch.load" | "97,649,753 learnable parameters (count_model_params.py, one rule)" | model_metrics.md, RESULTS_LOG 2026-09-04i |
| Model-zoo table: buffer-inclusive counts, no lesion detector, gate as 3a | learnable-only counts (11,187,916 / 11,177,538 / 11,178,051), lesion detector row (25,311,251, models/16), 4 totals (97.65M / 83.52M / 75.29M / 61.16M) | model_metrics.md "Pipeline size" table |
| "~25 M" warning: "33.45 B vs 61.2 M" | "33.45 B vs 75.3 M (retained gate path 61.2 M) — ~444×"; added note the new Stage-3a lesion detector is also ~25.3 M | model_metrics.md 829–834 |
| C1 "efficiency claim" bullet: "61.2 M … 550×" | kept, + parenthetical "(this C1 run used the retained gate path; shipped default is 75.3 M, ~444×)" | reconcile with fixed Model Zoo |
| Lever 2 "~8 AP over the generic baselines" | "~6 AP over the strongest of their ten baselines" | RESULTS_LOG 2026-09-04j (Conditional-DETR row restored) |
| `models/16` "**ablation**, Sec 6 not yet met — needs Ningxia" | "adopted 4 Sep as Stage-3a default (Sec 6 met, 2/3 cohorts)" | RESULTS_LOG 2026-09-04h |
| Reproducing-numbers table: Lever B "Sec 6 pending Ningxia" | "Sec 6 met on 2/3 → models/16 adopted" | RESULTS_LOG 2026-09-04h |

### `docs/assets/hero.svg` — one change

- `<text>83.6 M</text>` → `97.7 M` (label "PARAMS, ALL SIX MODELS" kept). Per `docs/README.md`
  line 31: the hero SVG duplicates a headline number from `model_metrics.md` and must track it.

Parameter arithmetic re-checked against `model_metrics.md`: 27,617,459 + 11,187,916 + 25,311,251
+ 11,177,538 + 11,177,538 + 11,178,051 = **97,649,753**; caries path (1,2,3a-default,3b) =
**75,294,164**; gate-variant swaps give 83,516,040 / 61,160,451. All four match.

## Decisions made

- **C1 efficiency figures (61.2 M / 550×) are correct, not stale, wherever they describe the C1
  experiment.** The C1 pipeline used the gate; `model_metrics.md` keeps 61.2 M in its C1
  sections; `main.tex` line 897 scopes all pre-Lever-B Results to the gate. Changing them to
  75.3 M would mis-pair a gate result with a detector parameter count. Where a README figure was
  a *general* pipeline claim (Model Zoo intro, "~25 M" warning, hero), it was updated to the
  shipped default (75.3 M / 97.7 M / 444×); where it was C1-specific (the "efficiency claim"
  bullet), it was kept and annotated. This mirrors how `model_metrics.md` itself dual-reports.
- **Left `main.tex` almost untouched.** `verify_paper_numbers.py` passes 127/127 — the manuscript
  had no numeric drift the verifier could see, and its param table already carries both the
  default and the gate-variant totals under one rule. Only the un-asserted test count was wrong.
- **No `transfer.md` update.** This session changed no project state, decision, or next-step;
  root README drift is not tracked in `transfer.md` (its §3 items 7–8 concern
  `docs/paper/{manuscript.md,draft_spine.md}` and `docs/research/*`, not the root README).
- **No `RESULTS_LOG.md` entry** — no model, no number, no bug fix in the rule-1 sense; pure
  documentation reconciliation.

## Open questions

- The pre-Lever-B pipeline diagrams still describe a gate-only Stage 3a:
  `docs/architecture/corrected_opg_pipeline_architecture.svg` (the authoritative one, per
  `docs/architecture/README.md`), its `.drawio` source, `docs/assets/pipeline.svg` and its
  alt-text, and the ASCII diagram in the root README's "System architecture". Not touched —
  regenerating a diagram is out of scope for a stale-number fix. Someone should decide whether
  the architecture diagram needs a Lever B revision before submission.
- `docs/paper/{manuscript.md,draft_spine.md}` still carry the gate-only pipeline and the old
  0.488 / 61.2 M-era numbers — flagged across `transfer.md` §3 item 7 and multiple session
  memories, still not actioned (retire vs mark-superseded).
- `README.md` "Architecture specifications" table (~line 358) still lists "Caries cascade —
  ResNet18 ×2" without the lesion detector. Left because it accurately describes the retained
  cascade (gate + severity), and the severity head is still used under both Stage-3a paths —
  but a reader could read it as the current default. Borderline.

## Next steps

1. If committing: `git add README.md paper/main.tex docs/assets/hero.svg`, message
   `docs: reconcile root README + main.tex stale numbers with the 4 Sep Lever B adoption`.
   Currently on `main` — branch first per `CLAUDE.md`.
2. Decide the architecture-diagram question above (gate-only → Lever B).
3. Unchanged from prior sessions: Deepak's calls (venue, title/thesis, authors, the four-vs-five
   list), the four compliance blockers, the Docker rebuild.
