# Pre-registration — Lever 1: multi-corpus detector retrain

**Written and committed BEFORE any data was converted or any GPU rented, 1 September 2026.**
Fixes the metric, the comparator and the acceptance rule in advance so none can be chosen after
seeing a number. Same discipline as `T0.6_detector_reconciliation.md` §2, whose mask bar was
missed and reported as missed rather than moved, and as `outputs/caries_arms/PRE_REGISTRATION.md`.

## The hypothesis, and why it is not just "more data"

Stage-2 end-to-end decomposes exactly:

```
end-to-end FDI  =  detector recall  ×  FDI-exact of detected
     58.3%      =      70.6%        ×        82.6%
```

The numbering half is already strong. **Detector recall is the weak half and it caps everything
downstream** — 29.4 % of ground-truth teeth are never presented to Stage 2 at all. This is the
one place in the pipeline where the binding constraint has been *measured* rather than assumed
(`PAPER_MATERIAL.md` §8.16).

The detector currently trains on **700 Tufts images**. `DENTEX/training_data/quadrant_enumeration`
provides **623 further panoramic images carrying 18,095 annotated tooth boxes**, already local.
That is roughly a doubling of detection supervision, from a second institution.

Precedent, not guesswork: DentFound (Zhu et al., *Nat. Biomed. Eng.* 2026) trained its
tooth-identification model on **2,698** images assembled the same way — multiple public corpora
pooled specifically for tooth localisation.

## Leakage — verified before this document was written

The Stage-2 benchmark is 164 leak-free `DENTEX/disease/` images. Training the detector on
`quadrant_enumeration` would be worthless if those overlapped. Checked by MD5:

* 85 of the 250 `disease/` pool images **are** in `quadrant_enumeration`
* **all 85 are already inside the 86-image exclusion list** (`disease_leaked_images.json`)
* **overlap between the 164 evaluation images and `quadrant_enumeration` = 0**

The benchmark is untouched. This was the gate; it passed.

## Comparator

A **same-day control**: the current frozen detector (`models/11_yolo_seg_tufts_r1`,
`tooth-detector-seg-tufts-1024-v1.0`) re-measured **today, on this machine**, not the figures
published on 27 August. That re-measurement is required because the 27 Aug control already drifted
~3 teeth of 936 from the originally published numbers across machines
(`model_metrics.md`, Stage-2 reproduction caveat). All deltas are against the same-day control.

## Primary metric and acceptance rule — fixed now

**PRIMARY: FDI exact, end-to-end, on the 164 leak-free DENTEX images.**
This is the number the manuscript leads with. It is the thing this lever exists to move.

> **The arm SUCCEEDS if the paired delta in end-to-end FDI exact against the same-day control has
> a 95 % confidence interval EXCLUDING ZERO.**

* Interval from a **paired cluster bootstrap over the 164 images**, 10,000 resamples, seed 42 —
  clustered over images because teeth within one radiograph are not independent.
* Any interval spanning zero is reported as **not significant**, whatever the point estimate.

**GUARD, and it is a pre-existing bar not a new one: Tufts frozen test box mAP@0.5 ≥ 0.75.**
This is `T0.6` §2's own pre-registered floor for a detector replacement, reused verbatim rather
than invented for this experiment. Multi-corpus training could raise DENTEX performance while
degrading the Tufts benchmark every earlier number was measured on; that trade must be visible.

**ADOPTION REQUIRES BOTH: primary significant AND guard met.** If the primary succeeds but the
guard fails, the model is reported as an ablation and the pipeline default does not change —
the same disposition given to Stage-2 head v3 and caries gate v4.

## Reported alongside, never instead of

Detector recall on the 164; FDI-exact-of-detected; Tufts test box mAP@0.5 and mask mAP@0.5;
mean detections per image; duplicate-FDI count.

## Risks recorded in advance

1. **Recall and of-detected can move in opposite directions and cancel.** R1 showed that
   *fewer* spurious boxes lifted of-detected by 13.9 pp because every spurious box perturbs the
   Hungarian assignment across a whole quadrant. A detector trained on more, noisier data could
   raise recall while emitting more spurious boxes, leaving end-to-end flat. **The decomposition
   is therefore reported, not just the product.**
2. **Domain dilution.** Tufts is 840×1615 portrait; DENTEX is ~2872×1504 upright landscape.
   Pooling two acquisition domains may cost Tufts-test mAP. The guard exists for this.
3. **Data may not be the constraint.** Seven prior improvement attempts on this pipeline
   returned intervals spanning zero. Recall may be limited by resolution or architecture rather
   than by training-set size, in which case this nulls like the others. **That outcome is
   reported as a result, not retried with a moved bar.**

## Cost, fixed in advance

A100-40GB at **₹84.24/hr** (read from `jl gpus`, 1 Sep). Estimated ~3 h ⇒ **~₹253** of the
₹1,105.99 balance. One redo is budgeted. The job is **not** run until the local geometry gate
below passes — the first R1 attempt burned ₹119 and 47 minutes training on misaligned masks that
failed nothing along the way.

## Local gate before any rental

1. Every converted box round-trips: `unrot_box(rot_box(b)) == b` on all boxes, asserted in code.
2. Converted labels re-scored against the source annotations; a mismatch exits non-zero.
3. Rendered samples from both corpora inspected by eye in the detector's own frame.

Only after all three pass does anything get rented.

---

## AMENDMENT — 1 September 2026, before any training. Two arms, not one.

Appended rather than edited: the original text above stands unchanged, and this records what
changed and why, in advance of any result.

**The confound this fixes.** The deployed detector is YOLOv11l-**seg**. DENTEX carries no
polygons, so the multi-corpus arm must be trained as **detect**. A one-arm design would therefore
change **two** things at once — the data *and* the task head — and R1 already measured that the
head matters: seg-training produced a *better box* detector than box-training (**0.810 vs
0.782** on the same frozen split). A flat or negative result would be uninterpretable: data
didn't help, or the data gain was cancelled by losing seg.

**Arms, both trained in one session with identical config, seed 42:**

| arm | train set | isolates |
|---|---|---|
| **Control A** | *(no training)* the deployed seg detector, re-measured today | the deployment baseline — **end-to-end 0.5844** |
| **Control B** | YOLOv11l-**detect**, Tufts only (700 img / 18,221 boxes) | the **seg → detect** change |
| **Arm** | YOLOv11l-**detect**, Tufts + DENTEX (1,334 img / 36,316 boxes) | the **data** change |

**Attribution:** `Arm − Control B` isolates the effect of the added data, which is the actual
hypothesis. `Arm − Control A` is the deployment-relevant comparison and is the one the
acceptance rule above is scored on. **Both are reported**; neither substitutes for the other.

**The acceptance rule and the guard are unchanged.** Primary is still end-to-end FDI on the 164
against a same-day control, CI excluding zero; guard is still Tufts test box mAP@0.5 ≥ 0.75.

**Both arms share byte-identical val and test data** — the Tufts-only train split is derived from
the same uploaded tree by filename (`[0-9]*.JPG` = Tufts, `dentex_*.jpg` = DENTEX), so no second
conversion and no second chance to introduce a geometry difference between arms.

**Revised cost:** two sequential runs on one A100-40GB @ ₹84.24/hr — ~3 h + ~1.6 h plus ~0.5 h
boot/upload ≈ **₹430** of ₹1,105.99.
