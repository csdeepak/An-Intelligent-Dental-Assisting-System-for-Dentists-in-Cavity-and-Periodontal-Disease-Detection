# Figures — figure-to-data map

All eight figures are byte-identical copies of the files tracked under `paper/ieee/figures/`,
produced by two scripts that assert each drawn value against the saved evaluation before drawing
(`R_figures_facts.json`, `R_draft_figures_facts.json`). No radiograph, annotation, curve or matrix
was drawn by hand or generated. Regenerate from the repo root with the scripts named below; they
write to `paper/ieee/figures/`, from which these were copied.

| Paper figure | File | Script | Data it reads | Kind | Pixels shown |
|---|---|---|---|---|---|
| Fig. 1 OPG primer | `R01_opg_primer.pdf` | `scripts/figures/make_opg_figures.py` | DENTEX test_120, expert annotations, shipped pipeline output | real radiograph + real model output | DENTEX (CC BY-NC-SA 4.0) |
| Fig. 2 Positional prior | `R05_positional_prior.pdf` | `scripts/figures/make_draft_figures.py` | DENTEX fit (78) and scored (164) caries labels | data plot | none |
| Fig. 3 Architecture | `R06_architecture.pdf` | `make_draft_figures.py` | `outputs/param_counts/param_counts.json`, `DEF_*` in `scripts/run_inference.py` | diagram with traced parameter counts | none |
| Fig. 4 Walkthrough | `R02_walkthrough.pdf` | `make_opg_figures.py` | DENTEX test_0; `R02_test_0_report.json` (the saved report) | real radiograph + real model output | DENTEX |
| Fig. 5 Training logs | `R04_training.pdf` | `make_opg_figures.py` | saved run files of the four trained stages (validation splits) | data plot | none |
| Fig. 6 Paired differences | `R07_paired_differences.pdf` | `make_draft_figures.py` | `outputs/stage1_switch/stage1_switch_results.json`, `F_ningxia_random_effects*.json` | forest plot | none |
| Fig. 7 Outcomes | `R03_outcomes.pdf` | `make_opg_figures.py` | three DENTEX test images chosen by a stated rule from the saved per-image evaluation | real radiographs + real model output | DENTEX |
| Fig. 8 Numbering / abstention / reliability | `R08_numbering_reliability.pdf` | `make_draft_figures.py` | taxonomy, coverage and calibration JSONs under `outputs/` | data plots | none |

No figure is conceptual-only: Fig. 3 is a diagram, but every number on it is read from saved
weights. Tufts, Ningxia and CariesXrays pixels are never shown (licence and consent constraints,
`PAPER_MATERIAL.md` §8.19). Patient identifiers: none in any shown image.
