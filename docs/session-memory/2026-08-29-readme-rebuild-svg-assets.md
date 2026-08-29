# 2026-08-29 — Root README rebuilt, with animated SVG assets

## Session goal

Rebuild the repository's front page (`README.md`) against the actual artefacts, at a standard
appropriate for a machine-learning / vision-language-model audience, with the pipeline and
repository structure drawn as animated SVGs.

## What was done

**Verified the repo state before writing anything** (the whole point — the previous README had
drifted):

- `python -m pytest tests/ -q` → **122 passed** in 15.65 s.
- `python scripts/eval/verify_invariants.py` → **all invariants hold**, including the three
  checks that used to skip.
- Read `transfer.md`, `docs/results/model_metrics.md` (all 5 sections), `docs/results/PAPER_MATERIAL.md`
  §1, §2.1, §3.2, §8.12–§8.19, `docs/README.md`, `models/README.md`, `requirements.txt`,
  `Dockerfile`, `app.py`, and `scripts/run_inference.py`'s `DEF_*` block and argparse surface.
- Counted, rather than assumed: 18 scripts in `scripts/eval/`, 22 directories under `outputs/`,
  17 figures in `docs/results/figures/paper/`, 25 `### 8.x` subsections in `PAPER_MATERIAL.md`,
  100 dated entries in `RESULTS_LOG.md`. Three of these had been guessed wrong in the first draft
  of the structure SVG and were corrected before commit.

**Created `docs/assets/` — seven hand-authored animated SVGs**, self-contained (no external
fonts, no scripts, no network references), each with `<title>`, `<desc>` and an `aria-label`, and
each honouring `prefers-reduced-motion`:

| File | Content |
|---|---|
| `hero.svg` | Banner + five headline KPIs |
| `pipeline.svg` | The six stages with per-stage metrics and animated flow along the connectors |
| `error-propagation.svg` | Stage-2 failure taxonomy over all 936 GT teeth |
| `baselines.svg` | C1 — all six arms including the image-blind constant |
| `domain-shift.svg` | C2 — caries survives, bone loss does not |
| `abstention.svg` | C4 — coverage–accuracy with the shuffled control |
| `repo-structure.svg` | The repository in four zones ("pipeline/folder structure in SVG") |

**Rewrote `README.md`** (700 → 855 lines), keeping what was still true (Universal→FDI table, the
bug table, the engineering-decision rationale, the rotation warning, the fresh-clone caveat) and
adding a model zoo with parameter counts and version tags, a reproduce-every-number table mapping
each claim to its script and its `outputs/` artefact, a methodology/rigor section, a 12-row
limitations table, and the compliance block.

**Stale front-page claims corrected** — each verified against the working tree, not assumed:

| Was | Is |
|---|---|
| Tests badge "84 passing"; tree said "65 tests" | **122** |
| Stage 1 headline `mAP@0.5 0.782` | **0.810** — 0.782 is the *superseded* bbox detector |
| Phase 6: "Drafting itself has not started" | Manuscript complete, compiles clean, 12 pages |
| Risk table: "No external clinical validation … out of scope for the capstone" | Four hospitals, done, C2 |
| Risk table: "Detector recall 0.74" | **70.6%** |
| Evaluation targets: detection "0.782 against ≥0.90 — not met" | 0.810, still not met |
| Tree missing `models/11,12,12a`, `scripts/kaggle_dual`, `scripts/figures`, `docs/paper`, `docs/assets` | All present |
| Dataset section had no Ningxia | Added with counts and the locked-data policy |

**Checked, machine-verified:** a script parsed every markdown link, `<img src>` and `#anchor` in
the finished README — **0 broken local paths, 0 broken anchors** across 39 headings.

## Decisions made

- **Numbers live in the SVGs, so `docs/assets/` is now a maintenance surface.** Hard-coding
  metrics into hand-authored diagrams is exactly the drift risk `CLAUDE.md` rule 1 exists to
  prevent. Mitigated by documenting it in *both* index files (`docs/README.md` layout table and
  `transfer.md` §7) with an explicit "edit these when a headline number moves" instruction. The
  alternative — generating the SVGs from the JSONs — is better and is listed under Next steps.
- **Dark self-contained cards rather than theme-reactive SVGs.** GitHub serves README images
  through a proxy and renders them in `<img>` context; a fixed dark palette reads as deliberate on
  both GitHub themes, whereas `prefers-color-scheme` inside a proxied image is not reliably
  honoured. Every diagram therefore paints its own background.
- **The README leads with the constant baseline beating our own pipeline.** That is the honest
  reading of C1 and it is the first figure a reader meets. Leading with "small specialist beats
  large VLM" would have been available from the same table and would have been misleading.
- **No `RESULTS_LOG.md` entry.** This session trained nothing and produced no new evaluation
  number. Re-running the suite and the invariants confirmed existing figures rather than
  generating new ones. Rule 1's trigger conditions are not met; rule 2's are, hence this file.

## Open questions

- **Do the SMIL/CSS animations survive GitHub's image proxy in practice?** They render correctly
  in Chrome from `file://` (verified by rasterising each SVG headless at a 6 s virtual-time
  budget and inspecting the output). Not yet confirmed on `github.com` itself, which needs a push
  and a look — nobody has done that.
- **`docs/architecture/corrected_opg_pipeline_architecture.svg` is still described as the
  authoritative diagram** and it predates the seg-detector swap. `docs/assets/pipeline.svg` is now
  current but is a *front-page* asset, not the technical one. Two diagrams claiming to describe the
  same pipeline is the setup for exactly the drift this repo keeps finding. Someone should decide
  which is authoritative and say so in `docs/architecture/README.md`.
- The README states three checkpoints are Drive-only; `models/README.md` says "only two" and then
  lists three. Minor internal inconsistency in that file, not introduced here, not fixed here.

## Next steps

1. **Push and visually confirm the SVGs animate on github.com** — the one claim in this session
   that is verified locally but not in the target environment.
2. **Generate `docs/assets/*.svg` from the artefact JSONs** rather than hand-editing them, or at
   minimum extend `scripts/verify_paper_numbers.py` to assert the SVG-embedded numbers too. Until
   then the front page can silently disagree with `model_metrics.md`.
3. Resolve the two-authoritative-diagrams question above.
4. Unchanged and still the actual critical path: the **venue-length cut** (12 pages → 4) and the
   **four non-engineering compliance blockers** in `PAPER_MATERIAL.md` §8.19.
