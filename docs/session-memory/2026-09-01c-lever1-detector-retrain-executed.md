# 2026-09-01c — Lever 1 executed: +34.9 pp end-to-end FDI, but the Tufts guard fails → ABLATION

Third working session of 1 Sep. Continues from `2026-09-01b-lever1-prep-doi-audit-and-gpu-abort.md`,
which ended with the Lever-1 dataset built and gated but the first GPU run aborted mid-upload.

## Session goal

Council the Lever-1 training logic/workflow for flaws, then provision a GPU and run the
pre-registered two-arm multi-corpus detector retrain end to end, keeping an eye on training.

## What was done

**Pre-flight audit (before any spend).** Read the builder, trainer, pre-registration, scorer and
the frozen-config reference. Verified:
- **Config fidelity** — `train_multicorpus_detector.py` matches the canonical bbox run's
  `train_args.yaml` parameter-for-parameter (checked the box's own `engine/trainer` dump too).
  Only intended deltas: `yolo11l.pt` detect head (DENTEX has no polygons) and the train split.
- **Geometry** — canonical Tufts box counts reproduced exactly (val 3,794 / test 3,924); DENTEX
  round-trip IoU 1.0; Tufts vs DENTEX box aspect ratios in the same regime (pixel w/h ≈ 2.6–2.7),
  where the void build had them orthogonal. Rendered 4 samples — boxes on teeth.
- **Fixed two stale breadcrumbs** in `build_multicorpus_detector_dataset.py` (docstring +
  `meta.json` still named `dataset_seg` as the Tufts source — the *void* corpus; the code was
  already correct, reading `teeth_bbox.json`). Patched the on-disk `meta.json` too.

**GPU run.** `jl create --gpu` reported A100 and H100 containers unavailable; provisioned an
**RTX PRO 6000 Blackwell 96 GB** (IN1, ₹179/hr, instance 491623) after asking the user to choose.
- `tar` → one 817 MB file → `jl upload` (7 min, vs the aborted rsync) → sha256 verified identical.
- **On-box gate caught a tar-hygiene bug:** macOS `tar` shipped AppleDouble `._*` files, doubling
  every file count (2668 vs 1334) and would have fed YOLO garbage. `find … -name '._*' -delete`,
  re-verified PASS.
- `pip install ultralytics==8.4.127` on the box (match the canonical run + the Mac, so `best.pt`
  loads locally).
- Both arms trained, early-stopped at epoch 106 / 105 of 150 (~26 min / ~47 min). Guard val
  (`yolo val split=test`) run on the box for each. Weights + results downloaded, sha256 verified,
  **instance destroyed.** Spend **₹267.84** (balance ₹1,084.54 → ₹816.70).

**Scoring (on the Mac, same machine as the same-day control).** New reusable script
`scripts/eval/score_lever1_arm.py` (reuses `bootstrap_ci.py`'s `paired_bootstrap`/`load_stage2`;
self-tested — arm=control gives Δ0). `validate_fdi_assignment.py` run per arm with
`--head-weights models/10/...` explicitly (its default is v1.0 — the known trap).

**Results:**

| | recall | of-detected | end-to-end | Tufts test box mAP@0.5 |
|---|---|---|---|---|
| Control A (deployed seg, same-day) | 0.708 | 0.825 | **0.5844** | 0.810 |
| Control B (Tufts detect) | 0.831 | 0.724 | 0.6015 | 0.724 |
| Arm (Tufts+DENTEX detect) | 0.995 | 0.939 | **0.9338** | **0.647** |

Paired cluster bootstrap over the 164 images (10k, seed 42):
`Arm − Control A` Δ end-to-end **+34.9 pp [+30.8, +39.0]** (excludes 0);
`Arm − Control B` +33.2 pp [+29.5, +37.0] (the pure data effect);
`Control B − Control A` +1.7 pp [−3.4, +6.8] (**n.s.** — seg→detect head change does nothing).

**Leakage ruled out three ways** (the 164 eval images vs the 634 training images): 0 byte-identical
(MD5), 0 filename match, 0 perceptual near-duplicate (aHash 16×16 — min Hamming 22, median 40;
calibration: byte-identical = 0, intra-corpus different-patient NN median = 32).

**Writeup:** `models/13_detector_multicorpus_lever1/run_summary.txt`, `RESULTS_LOG.md` 2026-09-01h,
`model_metrics.md` (Stage 1 Lever-1 block), `PAPER_MATERIAL.md` §8.16, `transfer.md` §1/§3/§6/§8.
`.gitignore` whitelists `outputs/detector_multicorpus/` (JSON/MD evidence, no weights).

## Decisions made

- **ABLATION. Not adopted. Pipeline default detector unchanged.** Pre-registered rule needs BOTH
  primary significant AND guard met. Primary succeeds overwhelmingly; the guard fails decisively
  (0.647 < 0.75). Same disposition as Stage-2 head v3 and caries gate v4. **The bar was not moved**
  — and the guard failure is the *pre-registered* "domain dilution" risk, confirmed (Arm − Control B
  on the guard metric = −7.7 pt).
- **The 93.4% is reported as an in-domain number, with the caveat stated everywhere it appears.**
  Detector and head both DENTEX-domain-trained, evaluated on held-out DENTEX. The 58.3% headline is
  cross-domain for the detector (Tufts→DENTEX). Different questions. 93.4% ≠ "works everywhere."
- **It is the strongest evidence in the paper that the 58.3% ceiling is detection *domain*, not
  the numbering head** — the head is frozen and identical across all three conditions; only the
  detector's training domain changed, and end-to-end nearly doubled.
- **Continued past Control B's surprising guard result rather than stopping.** Control B (Tufts-only
  detect) came in at test box mAP 0.724 — ~5 pt below the canonical bbox detector's 0.7824 for a
  near-identical setup. Traced to a *uniform* val+test shift (val best 0.782 vs canonical 0.834),
  consistent with A100→Blackwell + torch 2.2→2.11 training variance, not a data defect. Even
  correcting for it the Arm's guard is ~0.705 — still under 0.75. Recorded as a caveat.
- **Scored arms on the Mac, not the box** — to keep detector inference in the same numerical
  environment as the 0.5844 same-day control.

## Open questions

- **Is aHash 16×16 a strong enough leakage check for a paper claim this size?** Min Hamming 22 is
  well clear of the byte-identical regime, but a DCT-based pHash or the DENTEX organisers' own
  statement on whether `disease/` and `quadrant_enumeration` share patients would be more
  ironclad. Worth one more pass before 93.4% goes in a manuscript.
- **Why exactly is Control B ~5 pt below canonical?** Attributed to hardware/torch-version variance
  (uniform val+test shift is the tell), but not proven. A same-config A100 re-run would settle it;
  not worth the money for an ablation.
- **Lever 3 (caries gate on CariesXrays-derived labels) was to be "blocked on B1 producing a better
  detector."** B1 produced a better *DENTEX* detector that isn't adopted. Re-scope: Lever 3 can use
  the Arm weights (`models/13/arm_multicorpus_best.pt`) as a non-default detector purely to assign
  CariesXrays lesion boxes to teeth for label generation, without adopting it into the pipeline.

## Addendum, same session — publication framing council

The user asked, after Lever 1: what future work leads to an A/S-grade conference publication, and
is Framing A or B better. Council held; recorded in `transfer.md` §5 (new subsection).

- **Framing A** — evaluation / protocol paper. Core: tooth-level caries scores are base-rate
  dominated, an image-blind constant ties/beats the pipeline across 6 cohorts, stage-wise
  decomposition locates the ceiling (detector *domain*, quantified by Lever 1). Everything exists.
- **Framing B** — systems paper with a positive number. Needs Lever 2 to land a caries-lesion mAP
  near the CariesXrays / AAAI 2024 FPCL baselines. 1.5–3 weeks of research; real chance of nothing
  usable; and it does **not** overturn the finding (the constant beats the *tooth-level* metric
  because of base-rate dominance, not model quality — Lever 2 improves a different, lesion-level
  metric).

**Decision: Framing A is the working spine. Lever 2 is capped at a 1-day read-the-baselines
go/no-go and can only be a bonus section that does not block Track A. B is never load-bearing.**
Rationale in full: `transfer.md` §5. A is *not* a negative-result paper — its positive
deliverables are the reusable eval protocol (only 2/49 task-relevant papers do external
validation), the Lever-1 mechanism result, and the deployed reproducible pipeline.

**Venue:** target ISBI 2027 (26 Oct, S-grade), commit a journal (JBHI / *Diagnostics* / MedIA)
as the fallback — journal = S regardless of edition. Not a 1st-edition conference.

**Also this session:** added a "Response style" rule (telegraphic, dense chat responses) to the
repo `CLAUDE.md` §7 and created `~/.claude/CLAUDE.md` (global) with the same.

## Next steps — resume 2 Sep

1. **Venue decision — ISBI vs journal (user call).** Everything downstream depends on it.
2. **Hand the compliance list to the account owner** — Tufts Drive folder, DENTEX/Ningxia
   licences, SDH `index.csv`, and *start IRB* (longest lead time of anything open).
3. **Lever 2 go/no-go** — read the AAAI CariesXrays FPCL baselines (metric, exact test split,
   numbers). Reproducible split + beatable → pre-register + ~1 GPU-day. Else drop.
4. **Begin the 22 broken DOI fixes** (`outputs/citation_audit/FINDINGS.md`) — per entry, title
   lookup → correct or drop.
5. One more leakage pass on the 164 vs `quadrant_enumeration` (DCT pHash) before 93.4% is written
   into `main.tex`; then fold §8.16's Lever-1 paragraph in.
6. Unchanged critical path: the 4-page venue cut, upload `models/11_yolo_seg_tufts_r1/best.pt` to
   Drive, authors/affiliations, `docker` rebuild, remaining CIs.
