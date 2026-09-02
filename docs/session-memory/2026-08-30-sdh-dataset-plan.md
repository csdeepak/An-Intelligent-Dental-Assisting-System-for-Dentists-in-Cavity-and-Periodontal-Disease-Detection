# 2026-08-30 — SDH clinic dataset: consent, first measurements, execution plan

## Session goal

Plan the use of the SDH clinic dataset now that the clinic has given consent — usage tiers,
per-image filtering, GPU requirement and sequencing — grounded in measurement rather than in the
descriptions the existing clinic docs carry.

## What was done

1. **Cold-start briefing** from `transfer.md`, `docs/research/clinical_dataset_provenance.md`,
   `clinical_dataset_plan.md`, `MASTER_PLAN_2026H2.md`, `PUBLICATION_TODO.md`, `GPU_SETUP.md`.

2. **Located the data and found two tracked documents wrong.** `transfer.md` §8 and
   `data/README.md` both said the clinic data is "Not on this machine". It is: `D:\raw data\`
   (4,433 `.pano`), `D:\dataset_audit\` (Stage-1 conversion + audit CSVs), `D:\SDH dataset\dataset\`
   (3,219 enhanced PNGs). Both files corrected.

3. **Measured the dataset** rather than restating the June audit:
   - PIL header scan of all 3,219 files — 8-bit `L`, height fixed 1,316, width 2,043–3,001,
     405 distinct sizes, aspect 1.55–2.28, 3.72 GB.
   - Aggregated `metadata/index.csv` **without printing any identifier**: 3,220 rows, 3,220
     distinct `source_folder` values ⇒ exactly one image per patient. Device-folder distribution
     A–M (K 954 … F 14).
   - Aggregated `D:\dataset_audit\outputs\pano_format_summary.csv`: all Carestream CS 8100,
     12-bit stored, MONOCHROME2 ×4,417 / MONOCHROME1 ×4, study dates 2000–2024.
   - **Repeat-scan structure:** 3,228 patients, 1,013 with >1 scan, **145 same-day retake
     groups**, median first-to-last interval 38 days.
   - Joined `index.csv` against the audit scan table: for all **144** same-day groups present in
     the kept set, the retained image is the lowest-numbered scan of its group.

4. **Computed per-image quality metrics for the whole set** —
   `scripts` in scratchpad → `data/sdh/quality_metrics_enhanced.csv`, 19 columns, keyed by opaque
   image ID. The script deliberately never opens `index.csv`.

5. **Ran the frozen pipeline on SDH for the first time.** 24 SDH images (every 134th) plus a
   matched 24-image DENTEX reference run, same code path and hour: `data/sdh/pilot_inference_n24.csv`.
   Numbers in `RESULTS_LOG.md` 2026-08-30.

6. **Found six corrupt images.** `001970.png`–`001975.png` are truncated; sizes are exact
   multiples of 4,096 bytes and `preprocessing_run.log` opens with `Resume checkpoint: 1975`.
   `checkpoint.json` has claimed 3,219 completed images since June and is wrong by six.

7. **Wrote `docs/research/SDH_EXECUTION_PLAN.md`** — the deliverable. Verified facts, the four
   usage tiers and their ceiling, the DEV/TEST split rule, the four-layer filter, the compute
   budget, the sequence to 14 Oct, governance, and pre-registered acceptance criteria.

8. **Propagated per CLAUDE.md rules 1, 2 and 5:** `RESULTS_LOG.md` entry appended,
   `transfer.md` §1/§3/§8 updated, `data/README.md` and `docs/README.md` updated, this file.

## Decisions made

- **Tier A (label-free) is the plan; Tiers B and C are conditional.** SDH has zero labels, so no
  supervised training of the disease heads is possible on it — not difficult, impossible. What is
  certain without labels: behaviour-shift diagnostics, FDI-consistency violations, preprocessing
  and input-scale ablations, a failure taxonomy, and test–retest repeatability.
  *Reasoning:* it is ~2 days of mostly-unattended work, needs no dentist and no GPU, and it adds
  the only different-vendor, different-population source in the paper.

- **The DEV/TEST split is frozen before any filter threshold is chosen.**
  *Reasoning:* `clinical_dataset_plan.md` §6 rule 5 — the whole clinic set is test data, and
  choosing a filter cut-off is a tuning decision. A split drawn after the filter is designed is a
  split the filter has already seen. 40/60, patient-level (identical to image-level here, verified),
  stratified, seeded, with the 24 burned pilot images asserted into DEV.

- **The filter is built on sharpness and local band contrast, not on brightness or dynamic range.**
  *Reasoning:* measured p95/p5 spreads — `lapvar` 2.48 and `band_std` 1.99 against `entropy` 1.09,
  `mean` 1.07, `dynamic_range` 1.32. The June enhancement already normalises brightness, contrast
  and dynamic range per image, so thresholding on those would threshold the normaliser's output,
  not image quality. This was not knowable without computing the distribution.

- **Filtering is reported as a coverage–accuracy curve, never as a single cleaner number.**
  *Reasoning:* it is the fastest way to manufacture a good result, and framing it as contribution
  C4 (calibrated abstention) applied to a new device converts a housekeeping step into a result.

- **The same-day retake pairs are used to *validate* the filter, with a pre-registered threshold
  (>60% correct ranking).** *Reasoning:* it turns arbitrary thresholds into something checkable
  against the clinic's own implicit quality judgement, at zero labelling cost. Recorded as a
  **weak** label — a same-day repeat could be a second view rather than a retake.

- **No GPU for Tier A.** *Reasoning:* measured 2.2 s/image on CPU ⇒ ~2 h for the full set. GPU is
  reserved for pseudo-label detector adaptation, and ₹313 buys one attempt with no redo, against a
  plan that explicitly budgets for a redo and a precedent (R1) that needed one.

- **Bone loss on SDH is closed, not open.** 2.0% firing rate sits with Ningxia's 2.4%; it confirms
  `PAPER_MATERIAL.md` §8.13 on a fourth corpus. No work is scheduled against it.

- **Governance points stated once and the plan proceeds on the user's decision.** The written
  agreement's required contents are specified in §7.1; the Drive `index.csv` exposure is flagged
  as a five-minute fix to make before signing a letter that asserts de-identification.

## Open questions

1. **Do the six truncated images get repaired or excluded?** The split basis is 3,213 or 3,219
   depending on the answer, and the split must not be drawn twice. Sources are intact in
   `D:\raw data\`, but the enhancement script's hardcoded `D:\dataset_audit\dataset` output path
   must be fixed first or a repair forks the dataset.
2. **Do the 144 same-day-retake images stay, get swapped for the later scan, or get dropped?**
   They are plausibly the scans the clinic rejected.
3. **Does a dentist commit hours, and how many?** Gates all of Tier B; without it there is no
   sensitivity/specificity number on clinic data, ever.
4. **Is the JarvisLabs balance topped up beyond ₹313?** Gates Tier C1.
5. **Were the 4 MONOCHROME1 source images inverted correctly** at Stage-1 conversion?
   `dental_dataset_audit.py` has still never been read. Four images, but they will look exactly
   like model failures if wrong.
6. **`band_edge_density` is degenerate** (Canny 60/160 too high for a post-CLAHE panoramic) —
   re-tune or drop the column.

## Next steps

1. Separate `metadata/index.csv` from `images/` on Google Drive (~5 min, account-owner action,
   `clinical_dataset_provenance.md` §4a) — before the written agreement is signed.
2. Integrity pass: decode + SHA-256 every image; repair or exclude `001970`–`001975`; correct
   `checkpoint.json`'s count.
3. `scripts/sdh/build_sdh_split.py` → `data/sdh/splits_v1.json`. Nothing else runs first.
4. Freeze the L0 preprocessing contract with a unit test; fix the hardcoded output path.
5. Fit the L1+L2 filter on DEV; validate against the retake pairs against the >60% criterion.
6. Full-set Tier A inference with `--no-one-to-one` (~2 h CPU, unattended).
7. Repeatability on same-day pairs; then the ablations, coverage curves and failure taxonomy.
8. Locked TEST pass, once, with every parameter written down first.

**Ordering constraint that outranks all of the above:** the manuscript's venue-length cut is the
critical path (`transfer.md` §3 item 1). If it slips, the SDH track is what gets deferred.
