# `scripts/` — runnable entry points

Four families. The library they call is `src/`; see `src/README.md`.

| Path | Stage | See |
|---|---|---|
| `yolo/` | 1 — tooth detection (bbox baseline, the adopted seg detector, the Lever 1 multi-corpus retrain) + Lever 2, a standalone CariesXrays lesion detector (benchmark row, not a pipeline component) | `yolo/README.md` |
| `dentex/` | 2 and 3 — the enumeration head, plus caries data + training (incl. the 31 Aug signal arms) | `dentex/README.md` |
| `tufts/` | 2 — Tufts as a **second** FDI-numbering corpus (its labels are mirrored) | `tufts/README.md` |
| `eval/` | evaluation and error propagation (C3), plus the external-cohort evals (Ningxia, CariesXrays) | `eval/README.md` |
| `sdh/` | the SDH clinic set — measurement only, no pixel enters the repo | `sdh/README.md` |
| *(top level)* | Stage 4 bone-loss dataset/training, the full-pipeline entry point, and the paper-number / citation verifiers | below |

## Top-level scripts

| Script | What it does | Status |
|---|---|---|
| `build_dataset.py` | Builds the bone-loss training crops from Tufts | ✅ used |
| `train_model.py` | Trains the bone-loss ResNet18 | ✅ used |
| `run_inference.py` | **The full-pipeline entry point: OPG in → per-tooth JSON + overlay out** | ✅ **Built 24 Aug** — all six stages; see `src/classifiers.py` for Stages 3–4 |
| `verify_paper_numbers.py` | Asserts every number in `paper/main.tex` against its saved JSON artefact | ✅ **90 claims** (was 82; +8 for the CariesXrays cohort, 1 Sep) |
| `audit_citations.py` | Offline structural check of `paper/source.bib` (fields present, formatting) | ✅ hardcoded Windows path fixed 1 Sep — now repo-relative |
| `verify_citations_crossref.py` | **Dereferences every DOI against the registry** (doi.org content negotiation + `doiRA` agency lookup) | ⚠️ **1 Sep: 22 of 63 checkable DOIs broken** — 11 resolve to a different paper, 11 unregistered. Submission blocker, `outputs/citation_audit/FINDINGS.md` |

`run_inference.py`'s `main()` now delegates to `load_models()` + `run_pipeline()` (refactored
25 Aug, verified byte-identical) so the CLI and `../app.py` (the Streamlit deployment demo,
root of the repo) share one code path — no second implementation to drift. `../Dockerfile`
builds the same app as a CPU-only container. Neither is under `scripts/`; both are listed here
because they exist entirely to expose what this directory builds. Use
`src.fdi_head_inference.assign_fdi_head`, not the superseded positional module.

**`DEF_FDI_HEAD` points at Stage-2 head v2.0** (`models/10_fdi_head_dentex_tufts_v2/`,
DENTEX+Tufts) as of 26 Aug 2026 — adopted for cross-domain robustness, not in-domain accuracy.
`models/README.md` "Which FDI head to use" has the comparison against v1.0, which is retained.

---

**Publication target and grading criteria:** `../transfer.md` §5.

## If you are running anything on a non-Tufts image

Rotate it. The frozen detector consumes **90° counter-clockwise** panoramics; DENTEX, Ningxia
and the clinic data all ship upright, and feeding them as-is gives 7.5% recall and 0% FDI
accuracy. Use `src.orientation.detect_upright`, which handles the rotate/un-rotate pair.
