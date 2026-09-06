# Option B artefacts — read this before quoting `pos_feat_diagnostic.json`

**Status: RESOLVED the same day.** `pos_feat_diagnostic.json` in this directory is now a valid
6 Sep 2026 Windows re-run against a **rebuilt** crop corpus, and it reproduces the published
result on both cohorts (DENTEX 91.1% vs 91.0%; Tufts 70.8% vs 71.5%; `dentex_geom` +0.0 pp vs
+0.1 pp). The account below is kept because it is the diagnosis — the first attempt at this file
was invalid, and why it was invalid is the useful part. See `RESULTS_LOG` 2026-09-06d for the
rebuild and the side-by-side reproduction.

## Why the re-run happened

`RESULTS_LOG` 2026-09-06 traces the Option B result to
`outputs/tufts_fdi_pos_diagnostic/pos_feat_diagnostic.json`, but `.gitignore`'s `outputs/*` rule
meant that file was never committed — so on any other clone the numbers were uncheckable, which
CLAUDE.md rule 1 exists to prevent. Re-running it on the Windows box was meant to close that gap.

## What the re-run found

| condition | DENTEX val FDI-exact | published (Mac, 6 Sep) |
|---|---|---|
| full | **91.1%** | 91.0% |
| no_position | **77.6%** | 77.5% |
| shuffled_pos | **52.9%** | 52.9% |

DENTEX reproduces to a tenth of a point — the head, the loader, the feature handling and the
metric are all fine.

| condition | Tufts test FDI-exact | published (Mac, 6 Sep) |
|---|---|---|
| full | **18.1%** | 71.5% |
| dentex_geom | 18.9% (+0.8) | 71.6% (+0.1) |

## The cause: this clone's Tufts crop corpus is cut from the wrong source frame

Established by elimination, not inference — `scripts/eval/tufts_crop_frame_check.py`,
`crop_frame_check.json`:

1. **The labels are fine.** `data/tufts/enumeration_v1/enumeration_manifest.csv` is internally
   consistent and matches DENTEX's conventions exactly: Q1/Q4 image-left (mean cx 0.390 / 0.400),
   Q1/Q2 upper (mean cy 0.473 / 0.469), and |cx − 0.5| rises monotonically with the position digit
   (0.015 → 0.236 for positions 1 → 8).
2. **It is not a rotated crop.** All eight dihedral transforms of the stored crops were scored;
   the best (a vertical flip) reached 37.2% FDI-exact, nowhere near 71.5%.
3. **It is the source frame.** Re-cutting the *same manifest boxes* out of
   `data/tufts/ZIP/Radiographs_upright_fixed/` (the 180° frame, generated 6 Sep) scores
   **73.5% FDI-exact / 97.2% quadrant** on 400 test rows — reproducing the published result.
   Re-cutting from `data/tufts/ZIP/Radiographs_upright/` scores 11.5%, identical to the stored
   crops, which identifies the frame the corpus was actually built from.

`data/tufts/enumeration_v1/meta.json` records the corpus was built from
`…/scratchpad/tufts_ccw` — a temp directory from an earlier session on this machine, now gone.
The same clone's `Radiographs_upright/` is 180° from the frame `upright_box()` maps annotations
into, so both defects have the same root: an un-rotation applied in the wrong direction on this
box. **The Mac's copy is the valid one; the published Option B numbers stand.**

## What this does and does not affect

- **Does not affect Lever C** (`RESULTS_LOG` 2026-09-06b). That evaluation runs on radiographs
  through the detector, not on this crop corpus, and its control arm reproduces the published
  Stage-2 numbers on both cohorts (DENTEX to the digit).
- **Did affect anything crop-level run on this machine** — a diagnostic, an ablation, a head
  retrain. **The corpus was rebuilt from `data/tufts/ZIP/Radiographs_upright_fixed/` on 6 Sep**
  (`RESULTS_LOG` 2026-09-06d): manifest byte-identical, crops now scoring 73.2%, defective build
  archived to `_repo_archive/`. Note the failure mode for next time — it was silent: the labels
  looked right, the images looked like teeth, and the accuracy was simply wrong.
- **Untested and worth testing before use:** the other Tufts-derived crop corpora on this clone
  (`data/tufts/bone_loss_crops_rebuilt`, `severity_dataset`, `dataset_seg*`) may have been built
  in the same session from the same frame. `tufts_crop_frame_check.py` generalises to any corpus
  with a manifest of normalised boxes.
