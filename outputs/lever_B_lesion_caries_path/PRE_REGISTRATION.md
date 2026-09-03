# Pre-registration — Lever B: a lesion-detection caries path that is not base-rate dominated

**DRAFT written 2 September 2026 as part of the score-improvement council
(`docs/session-memory/2026-09-02c-score-lever-council-and-plan.md`, `transfer.md` §5).
Bars below are open to one round of user / mentor review BEFORE any GPU is rented. They freeze
once the build starts — same discipline as Levers 1 and 2.**

**FROZEN 4 September 2026, before any GPU rented or code written against it.** Review round found
four defects in the draft, all fixed here before freezing (none is a bar moved after seeing a
number — no lesion detector had been run against these cohorts yet):

1. §4's "fresh random-1500 draw, seed 43" is arithmetically impossible — the raw CariesXrays
   release is exactly 6,000 images = the existing 4,800/1,200 split, with no images left over to
   draw from. Fixed: the eval cohort is the existing disjoint 1,200-image val split.
2. §7 risk 4 allowed tuning the lesion-confidence threshold "on the CariesXrays held-out val" —
   circular now that that val set IS the eval cohort (fix 1). Fixed: threshold frozen flatly at
   0.25, no tuning clause.
3. §9's "~5,500 images" for B-pooled undercounts §3's own balancing instruction by ~2× (verified
   against Lever A's actual balancing code, which replicates the smaller corpus up to the larger
   one's count, not a simple concatenation). Fixed: cost re-estimated on the correct ~9,600
   images/epoch.
4. (Not a defect, a gap) §4/§6 never specified how a lesion DETECTOR's predictions become a
   tooth-level verdict for the acceptance metric. Fixed: added to §4 — centroid containment,
   reusing the primitive `ningxia_external.match_by_centroid` already applies to ground truth.

---

## 1. The hypothesis

The pipeline's caries branch is a **per-tooth gate** (ResNet18 over a tight crop). Across six
cohorts an **image-blind constant** — always flag the eight first/second molars — ties or beats
it on tooth-level caries agreement (`PAPER_MATERIAL.md` §8.22, §8.25). §8.24 supplies the
mechanism: **the gate scores teeth partly by which tooth they are.** Its mean score on
*genuinely healthy* teeth tracks the training base rate for that position (0.075 healthy
incisors → 0.478 healthy molars); 48.2 % of healthy molars are flagged. The gate has "partially
become the constant."

Five attempts to lift the gate's curve on DENTEX all returned intervals spanning zero (§8.24).
The supported reading is that **the task as posed — a tight per-tooth crop, a binary label, a
presumed-healthy negative class — has a ceiling that more data and more preprocessing do not
move.**

**Lever B changes the task.** A caries **lesion detector** localises the lesion directly rather
than scoring the tooth. Lever 2 already showed a stock YOLOv11l reaches **COCO AP 0.482 / AP50
0.845** on the CariesXrays benchmark (`RESULTS_LOG.md` 2026-09-02b) — level with the
task-specific FPCL method. A detector that finds lesions is **not** subject to §8.24's
base-rate shortcut: it has no per-tooth prior to lean on.

**The claim under test:** a caries-lesion detector, wired in as a Stage-3 alternative and scored
on **the exact lesion-localisation-agreement metric the constant currently wins on**, beats the
constant on a majority of the paper's caries cohorts — turning the paper's central negative
caries finding into a "here is what works instead" result.

---

## 2. What Lever B is, and is not

**Is:** a standalone caries-lesion detector (YOLOv11l `detect`, single class), its predictions
mapped to the detected tooth that contains each predicted lesion box, that tooth then marked
caries-positive. Scored frozen, on held-out cohorts, against two comparators on one metric.

**Is not:** a change to the six-stage pipeline's default caries gate (that stays v3.0 unless the
acceptance rule in §6 is met), a claim on CariesXrays' COCO-AP leaderboard (that is Lever 2, and
its split is not the official one), or a touch on any locked data (Ningxia is scored once,
frozen, no tuning).

This does **not** interact with §8.22 / §8.24. Those concern the *tooth-level* caries score.
Lesion-level detection AP is a different quantity; the point of §6's evaluation is to bring the
lesion detector **onto the tooth-level metric** so it is comparable to the constant and the gate.

---

## 3. Training data — fixed now

| source | images | what | role |
|---|---|---|---|
| **CariesXrays** train split | 4,800 (this project's seed-42 split, `data/cariesxrays_det/`) | lesion boxes, single class `decay` | primary — 13× the caries supervision of the DENTEX gate corpus |
| **DENTEX** `quadrant-enumeration-disease` | 705 | `caries` + `deep_caries` **tooth** boxes (coarser than lesion boxes) from `train_quadrant_enumeration_disease.json` | domain adapter — adds DENTEX-domain caries signal so the detector is not CariesXrays-only |

**Two arms, so the domain-transfer question is answered rather than assumed:**

| arm | train set |
|---|---|
| **B-single** | CariesXrays only (= Lever 2's model, re-used, no new training) |
| **B-pooled** | CariesXrays + DENTEX `quadrant-enumeration-disease`, balanced per §3 of Lever A's recipe |

**Forbidden as training data, recorded so it is not proposed:** DENTEX `disease/` (the 250-image
set). Its 164 leak-free images are the **evaluation** set (§4); its çürük polygons are the
DENTEX ground truth. Training on any of it contaminates the headline comparison.

---

## 4. Evaluation — frozen, three cohorts

Predictions from `best.pt`, mapped to containing/nearest detected tooth (detector = whatever is
the pipeline default at eval time), then the **existing, shared** matchers — no new matching
code:

| cohort | source | lesions | matcher |
|---|---|---|---|
| **DENTEX** | 164 leak-free `disease/` images | 479 çürük | `lesion_localization.py` (IoU 0.30 + centroid fallback) |
| **Ningxia** | 4 hospitals, all splits | 1,013 caries | `ningxia_external.match_by_centroid` |
| **CariesXrays** | **the existing 1,200-image val split** (`data/cariesxrays_det/`, disjoint from the 4,800 training images by construction) | ~2,815 | `cariesxrays_external` centroid matcher |

**AMENDED 4 Sep — the original "fresh 1,500 draw, seed 43" is impossible: the raw release is
exactly 6,000 images = 4,800 train + 1,200 val, with nothing left to draw. The max possible
disjoint eval set is 1,200, which is exactly the existing val split** (`meta.json`:
`train_val_overlap: 0`, already gate-verified — no new draw script needed). This is a stronger
design than the original plan, not a weaker one: it uses the full held-out pool rather than a
subsample of it, and needs no new randomness to reason about. `~2,815` lesions is the val split's
actual box count (`data/cariesxrays_det/meta.json`); the original `~3,400` was extrapolated from
the now-impossible 1,500-image figure.

**Lesion-detector predictions → tooth-level verdict (added 4 Sep, was unspecified):** a detected
tooth is marked caries-positive if **any** lesion-detector prediction's centroid falls inside its
box — the same centroid-containment primitive `ningxia_external.match_by_centroid` already
applies to ground-truth lesions, applied here to predicted ones. A tooth containing zero lesion
predictions is negative. This yields `pos_idx` in exactly the shape `--decision pipeline` /
`constant-molars` already produce, so no downstream code (matchers, bootstrap) changes.

---

## 5. Comparators and metric — fixed now

**Three systems, one metric, one matcher, per cohort:**

| system | what |
|---|---|
| **Lesion detector** (B-single, B-pooled) | this lever |
| **Caries gate v3.0** | the current pipeline Stage 3 |
| **Image-blind constant** `{16,17,26,27,36,37,46,47}` | the current winner (§8.22, §8.25) |

**Primary metric: lesion-localisation agreement** — of all real lesions, the fraction whose
containing/nearest tooth was flagged caries-positive. Paired cluster bootstrap over images,
10,000 resamples, seed 42.

**Reported always, never omitted: predicted-positive rate** (flagged teeth per image) and
**predicted-positive match rate** (of flagged teeth, the fraction on an annotated lesion — a
precision proxy, caveated exactly as §8.11/§8.25 caveat it: an unmatched flag is not a confirmed
false positive on cohorts whose annotation exhaustiveness is undocumented).

A detector can trivially win recall by flagging everything. The rate and match-rate columns are
what make the comparison honest, and the acceptance rule below is conditioned on them.

---

## 6. Acceptance rule — fixed now

> **Wire the lesion detector in as the Stage-3 caries path and report it as the primary caries
> result IFF, for the better of B-single / B-pooled:**
>
> 1. **lesion agreement > the constant's**, paired 95 % CI excluding zero, on **≥ 2 of the 3
>    cohorts**; AND
> 2. on those winning cohorts, the detector's **predicted-positive rate is ≤ 1.5× the
>    constant's** (it is not winning by volume); AND
> 3. it **also beats the gate v3.0** on those cohorts (CI excluding zero) — otherwise the gate,
>    already wired, is retained.

**Outcomes and how each is written — none is a failure to hide:**

| outcome | how it is reported |
|---|---|
| Rule met | New §: "a lesion detector is not base-rate dominated — it beats both the constant and the gate on N of 3 cohorts." The paper's caries story flips from negative to constructive. Pipeline Stage 3 updated; full downstream re-run. |
| Wins agreement but floods predictions (fails cond. 2) | "higher recall at a real precision cost" — reported as a partial result with the rate columns, gate retained |
| Wins in-domain (CariesXrays) only, fails to transfer to DENTEX / Ningxia | "**lesion detection also degrades out of domain**" — this *strengthens* the domain-shift thesis (§8.13, §8.12a) and is a clean finding |
| Nulls everywhere | reported beside Lever 2's benchmark row: "even a competitive lesion detector does not beat an image-blind prior on tooth-level agreement — the metric ceiling is structural, not a model deficiency." The strongest possible form of the paper's central claim. |

**The bar is not moved after seeing any number.**

---

## 7. Risks recorded in advance

1. **Domain transfer.** CariesXrays is ~2440×1280, a different scanner population from DENTEX
   and Ningxia. B-single may not transfer; B-pooled is the mitigation, and a failure to transfer
   is itself a reportable finding (§6).
2. **Granularity mismatch in training.** DENTEX `quadrant-enumeration-disease` boxes are whole
   *teeth*, CariesXrays boxes are *lesions*. Pooling them trains on two box conventions. The
   builder tags each box's source; if the mix degrades B-pooled below B-single on a held-out
   CariesXrays check, B-pooled is dropped and only B-single is carried, recorded.
3. **The matcher favours large predictions.** Centroid-containment counts a lesion as matched if
   its centroid falls in a flagged tooth. A detector predicting large boxes gets easy matches.
   Mitigation: predicted boxes are mapped to a single tooth (argmax containment), and the
   predicted-positive-rate cap (§6 cond. 2) bounds this.
4. **Ningxia is locked.** Scored exactly once, frozen detector, frozen lesion model, no
   threshold chosen on it. The confidence threshold for "is this a lesion" is **fixed flatly at
   the ultralytics default, 0.25 — never tuned, on any cohort.** (**AMENDED 4 Sep**: the original
   text allowed tuning on "the CariesXrays held-out val", but §4's fix makes that val set the
   eval cohort itself — tuning on it would be circular. No cohort is available for tuning without
   either contaminating an eval cohort or spending Ningxia's one touch, so the ultralytics
   default is the only option that stays clean.)
5. **It works and the paper gets more complex.** A positive caries result adds a section and
   makes the ISBI 4-page cut harder. This is a venue problem (journal primary — `transfer.md`
   §5), not a reason to not run it.

---

## 8. Local gate before any rental

1. CariesXrays boxes: dims from the decoded image, never the XML `<size>` (27.3 % wrong —
   `RESULTS_LOG.md` 2026-08-27a). Already handled in
   `scripts/yolo/build_cariesxrays_detector_dataset.py` — reused, not reinvented.
2. DENTEX `quadrant-enumeration-disease` boxes round-trip COCO → YOLO-norm → pixel to within
   1 px; caries/deep_caries category filter verified against the COCO `categories` block.
3. 0 training-image overlap between the two sources (MD5); 0 overlap between the CariesXrays
   training images and the seed-43 eval draw.
4. ≥ 12 rendered samples per source, boxes on lesions, inspected by eye.
5. Gate re-run on the rented box after upload.

---

## 9. Cost, fixed in advance

B-single: **zero GPU** — Lever 2's `models/14_cariesxrays_lever2/best.pt` is re-used as-is.

B-pooled: one YOLOv11l `detect` run, 1024 px, 120/25 epochs (Lever 2's proven budget), on an
A100-40GB @ ~₹84/hr. **AMENDED 4 Sep — image count corrected.** §3's per-corpus balancing (Lever
A's recipe: replicate the smaller corpus up to the larger one's count, not concatenate) gives
**4,800 (CariesXrays) + 4,800 (DENTEX-caries, 650 replicated ~7.4×) = 9,600 images/epoch**, not
the original "~5,500" (a naive-concatenation figure that did not apply §3's own instruction).
Roughly double the images at the same epoch count ⇒ roughly double the wall-clock and cost:
**~₹600 point estimate, ~₹1,200 ceiling with one redo** (was ~₹300/~₹600). Balance ₹1,732 covers
this with margin. Evaluation is all CPU (frozen inference + the existing matchers).
