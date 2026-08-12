# `docs/architecture/` — System diagrams

| File | Status | Description |
|------|--------|-------------|
| `corrected_opg_pipeline_architecture.svg` | **AUTHORITATIVE** | The current, most complete end-to-end pipeline diagram: YOLOv11l tooth detection → sort/jaw-split → FDI numbering → dual crop paths (tight crop → caries cascade; expanded 1.5×W/2.0×H crop → bone-loss binary + severity) → clinical filter → JSON/PDF report. Use this one in the paper and the report. |
| `pipeline_flowchart.svg` | Historical | The earlier flowchart (previously at `docs/flowcharts/pipeline_flowchart.svg`, moved here by `git mv` so all diagrams live in one place). Kept because it is referenced by older documents. Superseded by the file above. |
| `dental_opg_pipeline_flowchart.drawio` | Editable source | draw.io source for `pipeline_flowchart.svg`. Open at <https://app.diagrams.net> to edit, then re-export. |

## Deduplication note

The old top-level `Archi/` folder held a third copy of the flowchart —
`dental_opg_pipeline_flowchart.svg` — which was verified **byte-identical**
(md5 `97fe9f90207cb086b822eaaf4eb14b8c`) to the tracked `pipeline_flowchart.svg`, plus a
raster `.jpg` export of the same drawing. Rather than keep three copies of one diagram,
those two were relocated to `_repo_archive/archi_duplicate_diagrams/` (nothing deleted).

## If you edit a diagram

1. Edit the `.drawio` source, not the exported SVG.
2. Re-export to SVG in place, keeping the same filename.
3. If the architecture itself changed, also update the ASCII diagram in the root
   `README.md` and the "System Architecture" section of `docs/results/PAPER_MATERIAL.md`,
   and log the change in `docs/results/RESULTS_LOG.md`.
