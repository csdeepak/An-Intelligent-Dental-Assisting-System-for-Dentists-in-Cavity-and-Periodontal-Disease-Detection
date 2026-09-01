# 2026-09-01 — DentFound read, a sixth caries cohort, and the constant wins by 25 points

## Session goal

Read the DentFound paper in full, verify the user's claim about its Kaggle datasets, and work out
what a newly supplied 6,000-image caries corpus can do for the caries score. GPU budget available
(₹1105.99) and explicitly authorised.

## What was done

**DentFound verified, not assumed.** Confirmed from PDF metadata and text: Zhu et al., *"Towards
clinical-level interpretation of dental panoramic radiography using an instance-guided
vision-language model"*, Nature Biomedical Engineering, doi:10.1038/s41551-026-01713-8. **29 pages**,
not the 114 the file loader reported. The user's Kaggle claim is **correct** — Data Availability
names `zwbzwb12341234/a-dual-labeled-dataset` and `humansintheloop/teeth-segmentation-on-dental-x-ray-images`,
used with 100 hand-labelled mixed-dentition images (2,698 total) to train **only** their
tooth-identification model. Three things transfer: instance masks give +20.35/+23.01/+23.11%
relative P/R/F1 (P<0.001) — but against a VLM with *no* tooth grounding, so weak analogy to a
pipeline that already crops per tooth; **resolution gains were NOT significant** (P>0.05),
independently corroborating our own measurement; and their tooth-ID model is a SAM-pretrained ViT.
Noted a discrepancy: the paper states the dual-labeled corpus is 2,000 images; this repo measured
**500 images / 2,066 labels** (2026-08-28c).

**The corpus was characterised and cleared before any use.**
- 6,000 images (5,992 unique), **13,785** `Decay` boxes, VOC, panoramic, all height 1280.
  **13.1× the positives and 23.1× the images** of `crops_v3_phase1`.
- **Leakage verified three ways** — 0 MD5 against every existing corpus; a **positive control**
  (`train_332` ≡ `test_181`) scoring dHash 0, proving the method detects real duplicates; and a
  1.5M-pair distance distribution (min 2, mean 23.7, 36 pairs ≤5) whose near-matches are the
  expected tail. One caries image matched **three different** DENTEX images at distance 2–3 —
  impossible for a true duplicate — and visual inspection confirmed different patients.
- **Provenance initially UNRESOLVED — then resolved by the user mid-session.** Forensics from the
  XMLs (`<database>Unknown`, paths at `F:\datasets\labeled\source6000-label1-all\all-6021\img`)
  suggested a private working directory, and searches for those strings returned nothing. The user
  then supplied the source: it is the **CariesXrays** benchmark, Chen et al., **AAAI 2024**,
  38(20) 21940–21948, DOI **10.1609/aaai.v38i20.30196**,
  `github.com/Binz-Chen/AAAI2024_CariesXrays`. Verified against AAAI OJS, ACM DL and DBLP, not the
  README alone. 6,000 images matches exactly; 13,784 non-degenerate boxes vs their stated 13,783
  is a +1 convention difference. **Licence not stated** (no LICENSE file, GitHub API reports none).
  The forensic path is consistent with the authors' own drive.
- **27.3% of the XMLs carry a wrong `<size>`** (1,637 files, 4,055 boxes) — width only. Verified
  the *coordinates* are in the true frame two ways: 0 of 4,055 boxes exceed the actual width
  (max ratio 0.809), and rendered boxes land **on teeth** rather than displaced ~8.5% right.
- **Detector transfer gate passed**: 26.08 teeth/image vs DENTEX 22.0.

**Path 0 — frozen pipeline vs the image-blind constant on the new cohort.** New script
`scripts/eval/cariesxrays_external.py`, importing `ningxia_external.match_by_centroid` so the
cohorts cannot drift apart. Random 1,500 images, 3,421 lesions:

| | pipeline | constant | delta | 95% CI |
|---|---|---|---|---|
| agreement | 0.3090 | 0.5612 | **+0.2523** | [+0.2321, +0.2726] |

A prefix draw (first 600 by id) gave +0.2401 [+0.2110, +0.2690] — overlapping, so no ordering bias.
**Mechanism measured:** 72.0% of lesions on molars, **60.2% on exactly the eight constant teeth**,
against the constant's ~0.60 structural ceiling. 22.1% of lesions fall inside no detected tooth.

## Decisions made

- **Nothing was trained and no GPU was rented.** The whole session ran on CPU. The budget was
  never the constraint; the constraint was doing the verification correctly first.
- **Path 0 before Path B, deliberately.** Evaluating the frozen pipeline is free, additive,
  invalidates no published number, and — as it turned out — answered the question Path B was
  supposed to answer, for ₹0.
- **A claim I made earlier this session was falsified and I recorded it as such.** I argued Path B
  (a lesion detector) was worth ₹260 partly because "a constant cannot win at lesion level, it
  would have to place boxes". This cohort shows a constant winning at lesion level by 25 points.
  I stated a hypothesis as a conclusion — the exact error §8.22 exists to criticise. Path B is not
  retired, but it must now clear a constant scoring 0.561 and needs its own pre-registered bar.
- **Sampling weakness in my own first run, caught and fixed.** The initial 600 were
  `sorted()[:600]`, i.e. the lowest IDs, which could have been one acquisition batch. Added
  `--sample/--seed` and re-ran randomised at n=1,500; the two agree.
- **`match_rate` is reported as a diagnostic, never precision**, because the corpus's annotation
  exhaustiveness is unknown — same restraint as §8.11.
- **The brute-force defence was re-checked per cohort rather than reused.** On DENTEX the constant
  flagged only 14% more teeth at equal match rate. Here it flags 64% more *and* has the higher
  match rate, so that defence fails and is not carried over.

## Open questions

- ~~Where did this dataset come from?~~ **RESOLVED mid-session** — peer-reviewed AAAI 2024
  benchmark, citable, DOI recorded. The result is on a published hospital-scale benchmark rather
  than an anonymous folder, which materially strengthens it. Only the *licence* remains unstated.
- **Is the annotation exhaustive?** If only some lesions were marked, "tooth with no box = healthy"
  is unreliable, and `match_rate` cannot become precision. Unmeasurable from inside the data.
- **Does Path B still make sense?** Its headline justification is gone. The honest case now is
  narrower: a detector might beat a 0.561 constant, but that must be pre-registered, not assumed.
- The full 6,000 could tighten the interval; 1,500 already gives ±2 pp, so probably unnecessary.

## Next steps

1. ~~Identify the dataset.~~ **DONE** — add the AAAI citation to `paper/source.bib` when §8.25
   lands in `main.tex`. Note: the AAAI paper reports FPCL baselines on this benchmark; **they were
   not read here and no number from it may be quoted until they are.**
2. Fold §8.25 into `paper/main.tex` — this is now the strongest form of the paper's central claim,
   on the largest cohort by lesion count, with the mechanism quantified.
3. Re-decide Path B only after (1), and only with a pre-registered bar against the 0.561 constant.
4. Unchanged critical path: venue-length cut, the four compliance blockers, and uploading
   `models/11_yolo_seg_tufts_r1/best.pt` to Drive.
