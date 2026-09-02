# 2026-09-02b — Lever 2 executed: YOLOv11l on CariesXrays reaches the benchmark ceiling

Second working session of 2 Sep. Continues from
`2026-09-02-doi-blocker-cleared-and-lever2-council.md`, which ended with the Lever-2 council
GO'd conditional on the FPCL split being reproducible.

## Session goal

One line: the user said "forget the publication, i am giving you the right to download the
cariesxrays and start the gpu work" — download the benchmark, build + gate the dataset, rent a
GPU, train a standalone caries-lesion detector, report COCO AP against the published table.

## What was done

**Download + inspection.**
- `gdown --folder` the CariesXrays Drive folder → `Annotations.zip` (3 MB, 6,000 VOC XMLs) +
  `JPEGImages.zip` (**4.2 GB**, not the ~2 GB the old notes guessed) → `~/Downloads/Capstone/
  CariesXrays_Dataset/`.
- **The council's split gate came back NEGATIVE.** No `ImageSets` / split file anywhere — not in
  the zip, not in the FPCL GitHub repo (ships a 0.5% sample only), not in the DVCTNet repo
  (`github.com/ShanghaiTech-IMPACT/DVCTNet`, which has its own application-gated dataset).
  DVCTNet's paper used "the original split … for fair comparison", so it exists but was shared
  privately by the FPCL authors.
- **Proceeded anyway on the user's direction**, with a **seed-42 image-level 80/20 split**
  (4,800 / 1,200) matching only FPCL's ratio. Every number is therefore *indicative* vs the
  published table, not head-to-head — baked into the pre-registration, `data.yaml`, `run_summary`,
  RESULTS_LOG and PAPER_MATERIAL in those words.
- Inspection: single class `Decay`, 13,784 non-degenerate boxes (paper: 13,783; +1 counting diff),
  **27.5% of XMLs carry a wrong `<size>` width** (height always right) — exactly the documented
  bug. Coordinates verified in the true image frame (0 boxes exceed real width).

**Build + gate.** New `scripts/yolo/build_cariesxrays_detector_dataset.py` — reads box dims from
the **decoded image**, never the XML `<size>`. Local gate: 0.0 px round-trip, 0 normalised coords
out of [0,1], 0 train/val stem overlap, image count == label count, 12 renders eyeballed (boxes on
interproximal/cervical lesions, no offset). `data/cariesxrays_det/` (~4 GB, gitignored).

**Pre-registration** written and committed *before* renting:
`outputs/lever2_cariesxrays/PRE_REGISTRATION.md` — COCO AP primary, the split caveat, "one run,
report as-is, bar not moved", config = canonical detector settings verbatim + `nc=1` + `mosaic=0`.

**GPU run.** JarvisLabs A100-40GB on-demand (instance **492535**, IN2, ₹84.24/hr).
- Tar → one 4.22 GB file → `jl upload` (~4.5 min) → sha256 verified bit-identical → extract →
  **on-box gate re-passed** (sha match, 0 AppleDouble junk — Windows tar, no Lever-1 repeat,
  4800/1200 counts, 0 bad labels, box renders pulled back and eyeballed).
- `pip install ultralytics==8.4.127` (pinned, matches the frozen models).
- `scripts/yolo/train_cariesxrays_detector.py` — YOLOv11l detect, 1024 px, config verbatim from
  `train_multicorpus_detector.py` except epochs 150/30 → 120/25 (cost cap). **CUDA OOM at batch
  32 → ultralytics auto-reduced to 16** (the pre-registered fallback). ~115 s/epoch.
- Ran **86 epochs**, early-stopped (patience 25); **best epoch 61**. Weights + all plots +
  results.csv bundled, downloaded, sha256-verified. **Instance destroyed.** Spend **₹256.61**
  (balance ₹816.70 → ₹560.09).

**Result — COCO AP@[.50:.95] on the 1,200-image val split** (`best.pt`, re-scored with default NMS):

| | AP | AP50 | AP75 | P | R |
|---|---|---|---|---|---|
| ours (YOLOv11l, our split) | **0.482** | **0.845** | **0.500** | 0.803 | 0.774 |
| FPCL (their method, their split) | 0.482 | 0.841 | 0.506 | — | — |
| YOLOX / Faster R-CNN / DINO / RetinaNet | .405 / .399 / .378 / .130 | | | | |

An off-the-shelf 2024 one-stage detector with no caries-specific design lands on top of the
task-specific FPCL contrastive method and ~8 AP above every generic baseline in their table.

## Decisions made

- **Proceeded without the official split.** The council said "drop Lever 2 if the split isn't
  reproducible", but the user explicitly overrode that ("forget the publication … start the gpu
  work"). Reasoning: the scientific value survives — "a generic detector reaches the benchmark
  ceiling on this data" is a real, defensible statement even on a different random split, and the
  cheap run (~₹256) also produces a genuine caries-lesion detector the project didn't have. The
  *comparability* caveat is documented everywhere it could be misread.
- **batch 16, mosaic 0** are pre-registered deviations, not silent choices — both recorded as
  possibly costing a few AP.
- **Not wired into the pipeline.** One benchmark row in Related Work. It does not touch the
  base-rate-dominance finding (§8.22/§8.24), which is about the tooth-level metric.
- Reported the **default-NMS** number (0.4816), not the script's first `iou=0.5` pass (0.4787) —
  within noise, default is the standard.

## Open questions

- **The official FPCL split** — still not obtained. A true head-to-head needs emailing
  `chenbingzhi@m.scnu.edu.cn` / `darrenzz219@gmail.com`. Until then the paper row carries the
  caveat.
- **The AAAI baseline numbers** (FPCL 48.2/84.1/50.6 etc.) are transcribed from the paper text +
  the DVCTNet arXiv reproduction — **not yet checked against the AAAI PDF itself**. Must be, before
  `main.tex`.
- `best.pt`/`last.pt` (51 MB) are **not on Drive** — same gap as `models/11`.
- Would mosaic-on have pushed past FPCL? Untested; the house rule says no mosaic for medical
  imaging, so not pursued.

## Next steps

1. **Track A** (the actual critical path, paused this session): venue decision, 4-page cut, the
   four compliance blockers, authors/affiliations.
2. Fold the Lever-2 row into `main.tex` §Related Work — re-verify the AAAI table against the PDF
   first, present with the split caveat, NOT as a pipeline result.
3. Upload `models/11` + `models/14` weights to Drive (the fresh-clone gap).
4. Optional/low-priority: Lever 3 (caries gate v5) can now use `models/14/weights/best.pt` to
   assign lesion boxes to teeth for label generation — but it stays below Track A.
5. Housekeeping: `url`-field sweep in `source.bib`; find out where `D:` went (SDH track).
