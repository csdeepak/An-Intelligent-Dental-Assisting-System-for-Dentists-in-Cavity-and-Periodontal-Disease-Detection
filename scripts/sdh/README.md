# `scripts/sdh/` — the SDH clinic dataset

**Read `docs/research/SDH_EXECUTION_PLAN.md` before running anything here.** It carries the
usage tiers, the DEV/TEST split rule, the filter design and the pre-registered acceptance
criteria. These scripts are the measurement layer under that plan.

**Three standing rules, and they are not negotiable.**

1. **No clinic pixel enters this repo.** The data lives on `D:` on the Windows machine
   (`data/README.md` has the paths). What is tracked under `data/sdh/` is metrics and manifests,
   keyed by opaque image ID.
2. **`metadata/index.csv` is the re-identification mapping and is never read by code here, and
   never travels with `images/`** — including onto a rented GPU instance
   (`docs/research/clinical_dataset_provenance.md` §4a, `SDH_EXECUTION_PLAN.md` §7.3).
3. **SDH-TEST is locked once `data/sdh/splits_v1.json` exists.** No threshold, cut-off,
   checkpoint or preprocessing parameter may be chosen using it. Any image a script here has
   *looked at* is burned and belongs in SDH-DEV.

| Script | What it does | Status |
|---|---|---|
| `quality_scan.py` | Per-image quality metrics over the enhanced set → `data/sdh/quality_metrics_enhanced.csv`. Reports unreadable files instead of skipping them | ✅ run 30 Aug 2026, n=3,213 readable of 3,219 |
| `pilot_infer.py` | Deterministic-sample run of the frozen six-stage pipeline, aggregate behaviour only → `data/sdh/pilot_inference_n24.csv` | ✅ run 30 Aug 2026, n=24 SDH + n=24 DENTEX reference |

```bash
python scripts/sdh/quality_scan.py data/sdh/quality_metrics_enhanced.csv
```

```bash
python scripts/sdh/pilot_infer.py 24 data/sdh/pilot_inference_n24.csv "D:/SDH dataset/dataset/images"
```

## Two things a re-run will hit

**Six images do not decode.** `001970.png`–`001975.png` are truncated — all six sizes are exact
multiples of 4,096 bytes, and `preprocessing_run.log` opens with `Resume checkpoint: 1975`, so the
June 2026 run was interrupted with those in flight and resumed after them. `checkpoint.json` still
claims 3,219 completed images and is wrong by six. **The usable set is 3,213** until they are
repaired from `D:\raw data\` — and the enhancement script's hardcoded `D:\dataset_audit\dataset`
output path must be fixed first, or a repair writes to a path that does not exist and forks the
dataset. `RESULTS_LOG.md` 2026-08-30.

**`pilot_infer.py` cannot report duplicate FDI codes.** The pipeline's one-to-one Hungarian
assignment makes duplicates impossible, so that column is 0 by construction. FDI-consistency
violations as a domain-shift signal need a run with one-to-one assignment disabled.
