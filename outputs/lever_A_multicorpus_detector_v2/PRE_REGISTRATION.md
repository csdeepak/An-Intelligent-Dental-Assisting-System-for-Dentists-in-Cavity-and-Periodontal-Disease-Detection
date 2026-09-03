# Pre-registration — Lever A: multi-corpus detector, done right (Lever 1 v2)

**DRAFT written 2 September 2026 as part of the score-improvement council
(`docs/session-memory/2026-09-02c-score-lever-council-and-plan.md`,
`transfer.md` §5). Acceptance bars below are open to one round of review by the user /
mentor BEFORE any dataset is converted or any GPU is rented. Once the build starts they are
frozen, in the same way `outputs/detector_multicorpus/PRE_REGISTRATION.md` (Lever 1) and
`outputs/lever2_cariesxrays/PRE_REGISTRATION.md` (Lever 2) were frozen.**

This supersedes nothing. Lever 1's pre-registration and its ABLATION verdict stand on the
record unchanged. This is a **new experiment** with a different corpus set, a different training
recipe, and a differently-scoped guard — not a re-run of Lever 1 with a moved bar.

---

## 1. The hypothesis

Stage-2 end-to-end FDI accuracy decomposes exactly:

```
end-to-end FDI  =  detector recall  ×  FDI-exact of detected
     58.3%      =      70.6%        ×        82.6%
```

The numbering half is strong. **Detector recall is the binding constraint** — measured, not
assumed (`PAPER_MATERIAL.md` §8.16). Lever 1 (`RESULTS_LOG.md` 2026-09-01h) confirmed this in
the strongest possible form: a detector that also trains on DENTEX lifts end-to-end to **93.4 %
in-domain** on held-out DENTEX (recall 0.708 → 0.995), the entire gain attributable to the added
data (`Arm − Control B` +33.2 pp [+29.5, +37.0]).

**Lever 1 failed adoption on one guard — Tufts frozen test box mAP@0.5 0.810 → 0.647** — the
pre-registered "domain dilution" risk, confirmed. Three things about that failure are fixable and
are the reason this experiment exists:

1. **Only two corpora.** Tufts + DENTEX. Two acquisition domains, so pooling looked like
   dilution.
2. **Tufts was 52 % of the training mix** (700 of 1,334 images) and the recipe was a naive
   concatenation. When a second corpus is half the data, the first corpus's held-out
   performance is expected to drop.
3. **The guard measured one domain.** Tufts test box mAP was the only detection benchmark this
   project had in September. The paper this lever feeds is a *multi-cohort* paper; a guard that
   privileges one founding corpus is the wrong guard for it.

**The claim under test:** pooling **four to five** tooth-box corpora from four to five
institutions, with per-corpus-balanced sampling, lifts Stage-2 end-to-end **on held-out data
that is genuinely cross-domain** — and does so without a material regression on any single
cohort, Tufts included.

---

## 2. Corpora

Every corpus below carries per-tooth (or per-tooth-region) bounding boxes usable for a
**single-class `tooth` detector**. Numbering labels, where present, are not used by this lever's
detector (they feed the optional head-v4 arm, §6).

| corpus | images | tooth boxes | institution / source | licence | on this machine? |
|---|---|---|---|---|---|
| **Tufts** (frozen split) | 700 train / 150 val / 150 test | ~18,200 | Tufts Univ. School of Dental Medicine | restrictive — local only (`docs/EXTERNAL_DRIVE.md`) | ✅ `_repo_archive/datasets_workspace/` |
| **DENTEX** `quadrant_enumeration` | 634 (→ train) | 18,095 | DENTEX / MICCAI 2023 (Radboud) | to verify (`PAPER_MATERIAL.md` §8.19.3) | ✅ `~/Downloads/Capstone/DENTEX/` |
| **Kaggle "dual-labeled"** | 499 usable | 13,166 | Kaggle "Dual-labeled Panoramic Radiographs" | to verify | ❌ **re-download** (`scripts/kaggle_dual/`, gitignored; built on the Windows box for head v3) |
| **UFBA-425** | 425 | ~11,000 (est.) | Figshare `29827475`, 2025 — instance masks + bboxes + FDI, every tooth | **to verify** (Figshare, likely CC-BY) | ❌ download |
| **DNS** | 543 | ~14,000 (est.) | "Detection, Numbering, Segmentation" panoramic set, COCO + FDI | **to verify** | ❌ download |

**Build-gate rule on licences:** a corpus whose terms do not clearly permit research use in a
model that will be described in a publication is **dropped from the pool**, not used "quietly".
Tufts + DENTEX + Kaggle alone is three corpora / ~1,830 images / ~49,000 boxes — already a
stronger pool than Lever 1's two, and every one of those three is already used elsewhere in this
project. UFBA-425 and DNS are upside, not load-bearing.

**BUILD OUTCOME — 2 September 2026** (`scripts/yolo/build_multicorpus_detector_v2_dataset.py`,
`outputs/lever_A_multicorpus_detector_v2/STATUS.md`):

| corpus | got | note |
|---|---|---|
| Tufts | 700 / 150 / 150 (frozen), canonical 3,794 / 3,924 box counts **reproduced exactly** | in-frame |
| DENTEX `quadrant_enumeration` | 623 usable (11 byte-identical dupes dropped — Lever 1 did not catch these), 561 train / 62 test | rotated CCW, round-trip IoU 1.0000 |
| Kaggle "dual" | 499 usable (1 dupe dropped — matches the project's own count), 449 train / 50 test | rotated CCW |
| UFBA-425 | 425, 382 train / 43 test — **CC BY 4.0 confirmed** (figshare API) | rotated CCW |
| DNS / OdontoAI | **dropped** — both request-gated, not downloadable | — |

Geometry gate: **42,500 rotated boxes round-tripped, median IoU vs source 1.0000, PASS**;
0 leakage refusals; all four corpora eyeballed in the detector frame (`_check/`).

**⚠️ UFBA-425 is a square 640×640 Roboflow export — the panoramic is stretched to 1:1, so its
tooth boxes have a measurably distorted aspect: median box w/h 0.234 against DENTEX 0.347 and
Tufts ~0.371 (a ~35 % narrower shape). This is a preprocessing artifact, not acquisition
diversity.** Consequence for the arm design below.

**Not usable and why, recorded so it is not re-proposed:**
- DENTEX `quadrant` (693 img): its boxes are **4 quadrant *regions* per image**, not teeth
  (verified 2 Sep — 2,772 anns / 693 img = 4.0, box ~624×468 px). Not a tooth-detection source.
- DENTEX `unlabelled` (1,571 img): no boxes. Pseudo-labelling was ruled out project-wide
  (`MASTER_PLAN_2026H2.md` R7) as the kind of shortcut that produces an unfalsifiable result.
- CariesXrays (6,000 img): **lesion** boxes, not tooth boxes. It is Lever B's training data, not
  Lever A's.

---

## 3. Training recipe — fixed now

Config is **copied verbatim from `scripts/yolo/train_multicorpus_detector.py`** (which itself
copied the canonical bbox run), so this lever trains detectors the way the project already does.
The **only deliberate differences from Lever 1**:

| | value | rationale |
|---|---|---|
| model | `yolo11l.pt` COCO-pretrained, **`detect`** | same as Lever 1 — DENTEX/Kaggle/UFBA/DNS polygons are not uniformly available, so `detect` not `-seg` |
| corpora | 4–5 (§2), vs Lever 1's 2 | the hypothesis |
| **sampling** | **per-corpus balanced**: each corpus's train image list is upsampled (list replication, augmentation makes copies non-identical) to the size of the largest corpus, so per-epoch exposure is within **1.05×** across corpora | Lever 1's naive concat put Tufts at 52 %; this is the fix for guard failure #2 |
| val / test | **carved per corpus, image-level, seed 42, 70/15/15** — except Tufts, whose frozen `split_v1` val/test are carried through **untouched** so `Tufts test box mAP@0.5` stays comparable to the frozen detector's 0.810 | guard #3 needs an unchanged Tufts test set |
| epochs / patience | **150 / 30** (canonical), not Lever 2's trimmed 120/25 | this is an adoption candidate, not a benchmark row — no cost cap |
| image size / batch / optimizer / augmentation / seed | **all canonical**, unchanged (`imgsz 1024`, `mosaic=0`, `flipud=0`, AdamW, `cos_lr`, seed 42) | — |
| ultralytics | pinned **8.4.127** | matches the frozen models + the local env |

Deviations recorded in `run_summary.txt` with the reason.

---

## 4. Arms — all trained one session, identical config, seed 42

Refined 2 Sep after the build: **the 3-corpus pool is the primary Lever A arm; UFBA-425 is an
additive arm**, because UFBA's only public form is an aspect-distorted square export (§2). A
rigour refinement made *before any training*, not a bar move — it keeps a clean corpus as the
headline and tests the noisy one separately.

| arm | detector train set | isolates | `train.txt` |
|---|---|---|---|
| **Control A** | *(no training)* the deployed seg detector, re-measured **today on this machine** | the deployment baseline | — |
| **Control B** | YOLOv11l-**detect**, Tufts only, canonical split | the **seg → detect** head change (Lever 1: +1.7 pp [−3.4, +6.8], n.s. — re-measured here) | 700 Tufts |
| **Arm 3C** *(primary)* | YOLOv11l-**detect**, Tufts + DENTEX + Kaggle, balanced | the **multi-corpus data** effect, clean corpora | `train_3corpus.txt` (2,100) |
| **Arm 4C** *(additive)* | Arm 3C + UFBA-425, balanced | whether a 4th, aspect-distorted corpus helps or hurts | `train.txt` (2,800) |

`Arm − Control B` isolates the data. `Arm − Control A` is the deployment-relevant delta the
acceptance rule (§5) is scored on, **applied to Arm 3C**. Arm 4C is reported alongside and
adopted over Arm 3C only if it *also* passes §5 AND beats Arm 3C on the primary, CI excluding
zero. All four reported; none substitutes for another.

---

## 5. Metrics and the acceptance rule — fixed now

### Primary — the number the manuscript leads with

**FDI exact, end-to-end, on the 164 leak-free DENTEX `disease/` images**, method = head,
head = `models/10_fdi_head_dentex_tufts_v2` (unchanged, isolates the detector). Paired cluster
bootstrap over the 164 images, 10,000 resamples, seed 42.

> **PRIMARY PASSES if the paired Δ (Arm − Control A) has a 95 % CI that excludes zero AND a
> lower bound ≥ +5 pp.**

The +5 pp floor (Lever 1 used "excludes zero" only) is because this is now an *adoption* decision
on a headline number, not a proof-of-mechanism.

### Guard 1 — external, and it is the fix for Lever 1's blind spot

**Pooled caries lesion-localisation agreement on Ningxia (4 hospitals, 1,013 lesions) +
CariesXrays (random-1500, 3,421 lesions)**, computed with the **frozen** caries gate v3.0 and the
shared centroid-containment matcher, so the only thing that changes between control and arm is
the detector. Paired bootstrap over images.

> **GUARD 1 PASSES if the paired Δ (Arm − Control A) in pooled external lesion agreement has a
> 95 % CI whose lower bound is ≥ −2 pp** (i.e. no material external regression; an improvement is
> expected — Lever 1's +7.7 pp external caries gain from the seg swap is the precedent).

### Guard 2 — Tufts, corrected for the run-level shift Lever 1 exposed

Lever 1's Control B (Tufts-only detect) scored **0.724** on Tufts test while the frozen seg
detector scored **0.810** — an ~8 pp gap attributable to seg→detect + hardware/torch drift,
*before any multi-corpus effect*. Comparing the Arm against 0.810 therefore over-penalises it.

> **GUARD 2 PASSES if the Arm's Tufts held-out test box mAP@0.5 is ≥ (Control B's Tufts test box
> mAP@0.5) − 4 pp.** This measures *domain dilution specifically*, holding the head change and
> the hardware constant.

### Adoption

**Adopt the Arm as the pipeline default detector (`DEF_DETECTOR`) iff PRIMARY passes AND
GUARD 1 passes AND GUARD 2 passes.**

If PRIMARY passes but a guard fails → **ABLATION**, exactly as Lever 1, Stage-2 head v3 and
caries gate v4 were handled. The pipeline default does not change, the numbers are reported in
full as the "we diagnosed the ceiling and here is exactly what a same-domain-pooled detector
does" evidence, and the manuscript's Lever-1 paragraph is upgraded with them.

**If adopted**, the full downstream re-measurement is mandatory before any number is written:
Stage-2 end-to-end + failure taxonomy, C4 coverage curves, all lesion-localisation numbers,
Ningxia C2, CariesXrays §8.25, and `verify_invariants.py` re-pinned. A detector swap invalidates
every end-to-end number in the paper (this is why Lever 1, even had it passed, would have
triggered a full re-run).

---

## 6. Optional secondary arm — FDI head v4 on the same pool

Kaggle, UFBA-425 and DNS all carry FDI numbering. A head trained on DENTEX + Tufts + Kaggle +
UFBA-425 + DNS (`train_enumeration_head.py` already accepts multiple `--data` roots) is a natural
companion. **It is reported alongside but adopted only if it independently clears a crop-level
bar on every corpus's held-out set** (≥ v2.0 on DENTEX and Tufts, CI excluding a regression;
positive on the new corpora). The primary comparison in §5 always uses head **v2.0**, so the
detector effect stays isolated. Head v4 is pure upside and must not gate Lever A.

---

## 7. Risks recorded in advance

1. **Dilution persists.** Five domains instead of two may still cost Tufts test mAP, or may cost
   a *different* cohort. Guard 2 catches Tufts; Guard 1 catches external caries. If either fails,
   this is an ABLATION and is reported as one — a five-corpus honest per-cohort detection table
   is itself a contribution the field lacks.
2. **Recall and of-detected cancel.** Lever 1 showed *fewer* spurious boxes mattered more than
   raw recall. A noisier five-corpus detector could raise recall and spurious-box count together,
   leaving end-to-end flat. **The decomposition is reported, not just the product.**
3. **The new corpora do not download cleanly / have no usable licence.** Mitigation: the pool
   degrades gracefully to Tufts + DENTEX + Kaggle (three corpora, all already project-used).
4. **UFBA-425 / DNS numbering convention.** If either is mirrored like Tufts, or non-standard,
   it is verified by the DENTEX-trained arbiter (the method in `scripts/tufts/README.md`)
   **before** its boxes enter even the detector pool — a wrong-handed image is still a valid
   *tooth* image, but the check is cheap and catches a corrupt download.
5. **It nulls like the others.** Seven caries attempts returned intervals spanning zero. If the
   primary CI includes zero or its lower bound is < +5 pp, that is the result, reported, not
   retried with a moved bar. (Lever 1's +34.9 pp makes this unlikely for the *primary*; the
   *guards* are where this experiment can legitimately fail.)

---

## 8. Local gate before any rental

Reuses Lever 1's gate, extended per corpus:

1. Every converted box round-trips (`unrot_box(rot_box(b)) == b` where a rotation is applied;
   YOLO-norm → pixel xyxy to within 1 px otherwise), asserted in code, non-zero exit on failure.
2. Each corpus's written labels re-scored against its source annotations (median IoU ≥ 0.99 for
   corpora needing a frame transform; exact for those already in frame).
3. Tufts box counts reproduce the frozen detector's canonical **3,794 val / 3,924 test** exactly
   (the build aborts otherwise — `RESULTS_LOG.md` 2026-09-01e/f is why).
4. macOS AppleDouble `._*` files deleted before tar (Lever 1 runbook — they double file counts
   and feed YOLO garbage).
5. ≥ 12 rendered samples per corpus inspected by eye in the detector's frame.
6. The whole gate re-run **on the rented box** after upload, before `train` is launched.

Only after all six pass does training start.

**GATE OUTCOME — 2 Sep (see STATUS.md for the full record).** 1–5 all passed locally
(geometry 42,500 boxes median IoU 1.0000; Tufts canonical 3,794/3,924 exact; renders eyeballed).
Two ML-logic checks added and passed:

- **Balanced-sampling mechanism verified empirically** — a throwaway `YOLODataset` on a
  `train.txt` with known duplicate lines gives `len(dataset) == n_lines` (not n_unique) on
  ultralytics 8.4.127. So per-corpus path repetition *is* real oversampling, one sample per line
  per epoch. The balancing is not a no-op.
- **Guard-1 leakage check** — the two NEW corpora (Kaggle-dual, UFBA-425) MD5- and aHash-checked
  against the Guard-1 eval cohorts (Ningxia caries `dental_caries/test*`, all 6,000 CariesXrays):
  **0 exact MD5 collisions; min aHash Hamming 39/256 (Kaggle) and 57/256 (UFBA)** — well outside
  the "byte-identical = 0, near-dup < ~8" band. Guard 1 is valid. (DENTEX q_enum, Tufts and
  CariesXrays were already cross-checked in §8.12 / §8.25.)

---

## 9. Cost, fixed in advance

Three sequential YOLOv11l runs (Control B ~1.5 h, Arm ~3.5 h on ~3,500 balanced images at
1024 px, + head-v4 ~1 h local on MPS, no GPU) on one JarvisLabs A100-40GB or -80GB @ ~₹84/hr,
plus ~0.5 h boot/upload of one ~1.5 GB tar ⇒ **~₹550–700**. One full redo budgeted ⇒ **~₹1,300
ceiling**. Instance destroyed the moment weights are downloaded and sha256-verified.
