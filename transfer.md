# CURRENT STATE — read this first

**This file is the project's living state-of-play.** It answers "where are we, what is done,
what is next" for a session that is starting cold — human or AI, on this machine or a new one.
It is **rewritten, not appended to** — unlike `docs/results/RESULTS_LOG.md` (append-only
history) and `docs/session-memory/` (one file per session, never edited). Those two are the
record; this is the snapshot.

**Last updated: 27 August 2026** (**Lesion localisation re-run too — 42.0% → 44.3% on DENTEX,
which means NO pipeline number is still measured on the superseded detector. Internal vs
external caries gap more than halved, 8.9 → 3.5 pp: much of what read as domain shift was a
detection problem.** `RESULTS_LOG.md` 2026-08-27i. Earlier: **C2 re-measured on the seg detector: caries +7.7 pts pooled
across all four Ningxia hospitals, bone loss completely unmoved (168 → 165 teeth flagged) — the
same intervention that gave Stage 2 +12.0 pts. That falsifies the standing guess that the
detector and bone-loss branch failed out-of-domain for a shared Tufts-trained reason.**
`RESULTS_LOG.md` 2026-08-27h. The caries gate was restored from Drive and hash-verified, so this
machine can run the full pipeline for the first time. Earlier: **bone-loss weights tagged — every trained model in the project is now frozen, tagged and hash-pinned**, and doing it surfaced a positional-attribution bug in `verify_invariants.py`; tests 65 → 73. §3 item 6 closed. Next: Ningxia C2 re-run on the seg detector, data now reachable at `D:
angxia_dataset`. Earlier: a cold-start orientation pass found R1's
results had never reached `PAPER_MATERIAL.md` or the root `README.md` — rule 1 item 3 — and
propagated them. That sweep turned up a **fresh-clone break**: the README told you to fetch the
*superseded* detector while `run_inference.py` defaults to the seg one. Fixed, with a documented
`--detector` fallback. `RESULTS_LOG.md` 2026-08-27f. Also: **Docker Desktop is installed on this
machine but not running** — §3 item 7 is one click from being testable. Earlier that day: R1 ran twice — the first attempt was withdrawn, its masks
misaligned by two data defects, both now fixed. The re-run passed the box bar, missed the mask
bar, and was **adopted anyway by user decision** for its box gain. Stage-2 was then
**re-measured on DENTEX: end-to-end 46.3% → 58.3%, +12.0 points** — the largest single jump this
project has recorded. **No GPU instances are running or paused; ₹650.81 of ₹900 remains.**
See §1a.)

**Previously: 26 August 2026** (later the same day: work resumed on the **Windows** machine;
the frozen Tufts split was made regenerable from code and `dataset_seg/` rebuilt, so R1 is
blocked on nothing but GPU time; GPU provider switched to **JarvisLabs** and `GPU_SETUP.md`
rewritten for it. Earlier that day: Stage-2 head v2.0 adopted; publication/grading guidance
added; full README + checkpoint-continuity audit for a machine handoff.)

> **⚠️ Two machines are now in play, and they do not hold the same data.** The macOS machine
> (M4 Pro) has DENTEX, Ningxia and the Tufts archive; the Windows machine has **only** Tufts,
> plus the detector checkpoint. §8 covers both — read the machine column before concluding a
> file is missing. The git history is the same on both; the *data* is not.

> **Maintenance rule (CLAUDE.md rule 5):** whenever a session finishes something, decides
> something, or changes what should happen next, update this file **before the session ends**.
> A stale snapshot is worse than none — it has already cost this project a wasted search
> (§8), and, in past sessions, several stale README claims that read as done-when-they-weren't
> or vice versa. Verify against the working tree before writing anything here.

---

## 1. Where we are, in six lines

**The pipeline runs end to end, is deployed, and has been measured on four hospitals it
never trained on.** `run_inference.py` → all six stages; `app.py` + `Dockerfile` wrap it
unchanged for a browser demo. Caries went from unusable (84.9% false-positive-dominated) to
plausible (19.1%, precision 0.40) by rebuilding its negative class with 5,366 real healthy
teeth. **Bone loss is the one open technical failure** — 0.92 macro-F1 on Tufts collapses to
0.7% firing on DENTEX and 0.8–5.4% affected-tooth sensitivity on Ningxia — measured on two
independent external datasets, not asserted from one.

**Stage 2 (FDI numbering) ships head v2.0** (DENTEX + Tufts, adopted 26 Aug). Swapping heads
did **not** move the in-domain headline (46.6% vs 46.5% — inside the ~1-point noise floor) but
gained **+21.5 points** out-of-domain on Tufts. v1.0 is retained and hash-pinned.

**The headline number moved on 27 Aug, and it was the DETECTOR that moved it: end-to-end
46.3% → 58.3% (+12.0 points)** after adopting the seg detector (§1a). That is the prediction
this project had been making for weeks — the head was already 91% on ground-truth boxes, so
Stage 1 was the binding constraint — now measured rather than asserted. Detection recall is
**70.6%** (was 67.3%).

**C2 (external validation) has real numbers**: zero leakage against all internal corpora,
caries lesion agreement **28.8–51.3% across four Ningxia hospitals (40.8% pooled), against
44.3% DENTEX internal — both re-measured on the seg detector 27 Aug, both with same-machine
controls. The internal/external gap more than halved (8.9 → 3.5 pp).**
**C1 (VLM baseline) is the only headline paper contribution still at 0%** — deliberately
deferred to W5 by the plan, not forgotten. **65/65 tests pass, `verify_invariants.py` is 7/7**
(now checking both Stage-2 heads). We are on **W2 of the 8-week plan**
(`docs/research/MASTER_PLAN_2026H2.md` §5), implementation freeze **14 Oct**.

**⚠️ Three things need attention before anything gets submitted or made public, and none are
modelling problems:** (1) a Tufts Drive folder was found browsable without sign-in, which the
dataset's own licence forbids — see §4. (2) Real Tufts radiograph pixels are embedded in 7
tracked notebooks, already on `origin/main` — the GitHub repo is confirmed **private**, so this
is deferred risk by explicit user decision (26 Aug), not an active leak, but it must be
resolved before any public release. (3) The Tufts left-right mirror finding (§2) is **not yet
established as novel** — the decisive source is IEEE-paywalled and unread.

**The user's stated intent: continue implementation, the paper draft happens last.**
See §5 for the grading stakes this is being built toward.

---

## 1a. R1 — what actually happened, 26–27 Aug

**Ran twice. The first run is withdrawn; the second is a documented PARTIAL result.**

**Attempt 1 (26 Aug) — WITHDRAWN, not a result.** Completed 90 epochs cleanly on an A100 and
was scientifically void: **every instance mask was spatially misaligned with its image.**
Caught by comparing final val mAP@0.5 (0.258) against the canonical bbox detector's 0.834 on
the same split — a gap far too large for a bbox→mask change. Two *independent* data defects,
both required to produce the failure:

1. `teeth_polygon.json` stores points as **`[y, x]`**; `teeth_bbox.json` uses `[x1,y1,x2,y2]`.
   The seg converter had inherited the bbox converter's "no transform needed" assumption.
   Proven over **6,006 title-paired objects**: transpose → 2.06 px median centre-distance,
   every other candidate 175–442 px.
2. This machine's `Radiographs_rotated/` predates the 22 Aug rotation-direction fix and was
   **180° out**.

Fixed in `scripts/yolo/fix_tufts_orientation.py` (new, self-verifying, refuses to run on an
already-aligned source) and a one-line swap in `convert_tufts_to_yolo_seg.py`. Verified against
`teeth_bbox.json` — the ground truth the 0.7824 detector was trained on — over 3,225 instances:
**median IoU 0.000 → 0.837, agreement 1.6% → 99.4%.** `RESULTS_LOG.md` 2026-08-27a.

**Blast radius — settled 27 Aug, no other result is affected, and there is nothing to check on
the other machine.** Traced both defects through every consumer:
- **Defect 2 (rotation) is Windows-only.** The macOS copy was always correct: the EDA notebook
  records the original rotation as `img.rotate(90)` (CCW), and `convert_tufts_to_yolo.py`
  applies *no* coordinate transform — so the canonical detector's **0.7824** test mAP is only
  achievable if that machine's images already matched `teeth_bbox.json`. Misaligned data scores
  ~0.25, as the withdrawn run showed. `rotate_tufts_radiographs.py` was written 20 Aug as a
  reconstruction of undocumented tribal knowledge, got the direction wrong, and **was only ever
  run on Windows** — on macOS the correct images already existed.
- **Defect 1 (`[y,x]`) is machine-independent but has no blast radius.** Its only consumer is
  `dataset_seg/`, and `train_yolo_seg.py` was unrun until 27 Aug. The bone-loss crops are built
  from `teeth_bbox.json` (verified: `02_bone_loss_dataset_construction.ipynb` sets
  `BBOX_JSON`; `teeth_polygon.json` appears there only in a comment); `src/crop_generator.py`
  mentions polygons only in a docstring and R2 is unwired from `run_inference.py`.

**The fix is enforced in code, not documentation** (27 Aug): `convert_tufts_to_yolo_seg.py` now
picks its image directory **by measuring** against `teeth_bbox.json` rather than by name — so
either machine auto-selects its own correct copy — and re-scores the written labels afterwards,
exiting non-zero if they disagree. Both paths were tested: the good path passes
(0.837 / 99.4%), and pointing it at the known-broken directory aborts with exit code 1 and
writes nothing. Shared thresholds in `scripts/yolo/_tufts_align.py`.

**The lesson worth carrying: a falling loss curve is not evidence of correct data.** That run's
losses fell smoothly for 90 epochs, throughput and checkpointing were healthy, and every
hyperparameter matched the pre-registration. It was operationally flawless and scientifically
void. What caught it was **comparing against a known reference and treating the gap as a defect
to explain rather than a disappointing number to report.** Geometry is now verified against an
independent annotation source *before* training, and that gate is re-run **on the GPU box**
immediately before launch.

**Attempt 2 (27 Aug) — ran clean, PARTIAL result.** 135 epochs, early-stopped, best epoch 105,
47 min. Held-out test touched **exactly once**:

| | mAP@0.5 | bar (`T0.6` §2) | verdict |
|---|---|---|---|
| **Box** | **0.8100** | ≥ 0.75 | **PASS** |
| **Mask** | **0.6383** | ≥ 0.65 | **FAIL** (short 0.0117) |

**The bar was not moved after seeing the number.** §2 stands exactly as written and this model
does not satisfy it.

**ADOPTED ANYWAY, 27 Aug, by explicit user decision — for the box gain alone.**
`DEF_DETECTOR` is now `models/11_yolo_seg_tufts_r1/best.pt`
(`tooth-detector-seg-tufts-1024-v1.0`). Adoption is a dated human call, **not** the bar being
met; both facts are on the record (`RESULTS_LOG.md` 2026-08-27d). Two consequences that matter
more than the swap itself:
- **Masks are not validated to §2's standard, so the model is used for its BOXES ONLY and
  R2 (mask-aware cropping) STAYS UNWIRED.**
- ✅ **RE-MEASURED 27 Aug — and the swap paid off far more than expected.** Fetched just the
  500-file `DENTEX/disease/` subset (1,023 MB, 4.6% of the Drive mirror) and re-ran Stage-2,
  with a control on the old detector first so the delta is attributable to the detector:

  | | bbox (control) | **seg (adopted)** | Δ |
  |---|---|---|---|
  | Detection recall | 67.3% | **70.6%** | +3.3 pp |
  | FDI exact (of detected) | 68.7% | **82.6%** | +13.9 pp |
  | **FDI exact, end-to-end** | 46.3% | **58.3%** | **+12.0 pp** |

  **Recall rose 3.3 points but end-to-end rose 12.0.** Detections/image *fell* (23.7 → 22.0)
  while recall *rose* — fewer spurious boxes, and every spurious box perturbs the Hungarian
  assignment across a whole quadrant. Off-by-one errors nearly halved (22.7% → 13.5%). This
  retroactively strengthens the adoption decision, which was taken on box mAP alone.
  `RESULTS_LOG.md` 2026-08-27e. Constants restored in `run_inference.py`.
- ⚠️ **The new checkpoint is >50 MB, gitignored, and NOT yet on Drive** — so a fresh clone
  currently cannot run the pipeline at all until it is uploaded (`docs/EXTERNAL_DRIVE.md`).

The bbox detector is retained unchanged and hash-pinned; every pre-27-Aug number was measured
on it.

**But box detection genuinely improved: 0.8100 vs the bbox detector's 0.7824 — +2.76 points**
on the same frozen split, otherwise identical config. Masks produced a *better box detector*
than boxes alone. That is also the number that matters downstream, since Stage-2 end-to-end is
capped by **detector recall**, not mask quality. **Whether to adopt on that basis is an open
decision (§4) — §2's bar governed a mask-driven replacement and should not be quietly
reinterpreted to wave this through.** Caveat, pre-registered: seg test GT has 3,930 instances
vs bbox's 3,924 (+0.15%), so near-, not exactly, like-for-like.

**Cost:** ₹249.19 total across both runs (₹900 → ₹650.81). No instance left running.

---

## 2. What is DONE — verified, not assumed

| Item | Evidence |
|---|---|
| **Detector** frozen, tagged `tooth-detector-a100-1024-v1.0` | `docs/research/T0.6_detector_reconciliation.md` §1 |
| **FDI enumeration head v1.0** (DENTEX) — 22.9% → 46.5% end-to-end, frozen `fdi-enumeration-head-resnet18-v1.0` | `models/08_fdi_enumeration_head/run_summary.txt`; 4 independent audit passes, reproduces byte-for-byte |
| **FDI enumeration head v2.0** (DENTEX+Tufts) — **current pipeline default**, adopted for cross-domain robustness | `models/10_fdi_head_dentex_tufts_v2/run_summary.txt`; +21.5pp on Tufts, ±0.1pp in-domain (noise floor); `RESULTS_LOG.md` 2026-08-25j, 2026-08-26a |
| **Tufts is a verified second FDI corpus — its labels are left-right MIRRORED** (Tufts "1" = FDI 28, not 18). Corrected via `src/utils/fdi_converter.tufts_title_to_fdi()`, established 3 independent ways (side-marker, a DENTEX-trained arbiter at 91.7% mirrored vs 6.1% direct, a DENTEX control at 98.6% direct) | `RESULTS_LOG.md` 2026-08-25h; `scripts/tufts/README.md` |
| A Tufts-**only** head was trained and rejected (loses 9.1pp on DENTEX; its Tufts edge over v2 is not significant, p=0.732) | `RESULTS_LOG.md` 2026-08-25j |
| **Caries gate rebuilt** — 5,366 real healthy teeth (MD5-joined, 98.28% FDI agreement), frozen `caries-gate-resnet18-v3.0` | `models/09_caries_gate_v3/run_summary.txt`; 84.9% → 19.1% in-pipeline, precision 0.40 |
| **T0.1–T0.4 caries re-run closed** — both arms run, gap is noise (0.01–0.03 vs 0.27 epoch-to-epoch swing) | `RESULTS_LOG.md` 2026-08-25b |
| **Stages 5–6 built** — `run_inference.py` runs all six stages, image → per-tooth JSON + overlay | `RESULTS_LOG.md` 2026-08-24f (R4, paper claim C3); refactored into `load_models()`/`run_pipeline()`, verified byte-identical |
| **Lesion-localisation evaluator** — **44.3%** agreement on DENTEX (seg detector, 27 Aug; 42.0% control on the old one) | `scripts/eval/lesion_localization.py`, `RESULTS_LOG.md` 2026-08-25c |
| **C2 external validation on Ningxia** — 4 hospitals, zero leakage, first external numbers | `scripts/eval/ningxia_external.py`, `RESULTS_LOG.md` 2026-08-25d |
| **Deployment** — Streamlit app + Dockerfile, wrapping the pipeline unchanged | `app.py`, `Dockerfile`, `RESULTS_LOG.md` 2026-08-25f |
| **6 paper/review figures**, generated from saved artefacts only | `scripts/figures/make_paper_figures.py`, `docs/results/figures/paper/`, `RESULTS_LOG.md` 2026-08-25e |
| **Literature check on two comparison papers** (DPML, DentFound) — what they used, whether public, and independent confirmation that DPML also collapses out-of-domain (95.06 mAP own data → 61.83 on public DENTEX) | `RESULTS_LOG.md` 2026-08-26a |
| **Bone-loss binary + severity** trained (Tufts), **now frozen and tagged** `bone-loss-binary-resnet18-v1.0` / `bone-loss-severity-resnet18-v1.0` (27 Aug) | `models/03_.../run_summary.txt`, `models/04_.../run_summary.txt`; hash-pinned in `verify_invariants.py`. **Every trained model in the project is now tagged — no gaps left.** `RESULTS_LOG.md` 2026-08-27g |
| **R1 seg dataset** built on the frozen split, ready to train | `data/tufts/dataset_seg/` — 26,005 instances, 700/150/150. Rebuilt independently on the Windows machine 26 Aug and reproduces exactly (18,268/3,807/3,930) |
| **The frozen Tufts split is now derived from code**, not a file carried between laptops — reproduces byte-for-byte (SHA-256 verified) | `scripts/tufts/regenerate_split_v1.py`; `RESULTS_LOG.md` 2026-08-26c |
| **R2 mask-aware cropping** implemented + unit-tested (**unwired** — needs R1's masks) | `src/crop_generator.py`, `tests/test_crop_generator.py` |
| **Environment fixed and pinned** — numpy<2, or `scipy.optimize` (the Hungarian assignment) silently breaks | `requirements.txt`, `RESULTS_LOG.md` 2026-08-24b |
| **All READMEs + this file** swept for staleness (three passes across two sessions) | `RESULTS_LOG.md` 2026-08-25e/f, 2026-08-26b, this rewrite |
| Test suite | **65/65 pass**; `scripts/eval/verify_invariants.py` **7/7** (now pins both Stage-2 heads) |

**The pattern worth remembering, stated once rather than per-entry below:** almost every defect
found across these sessions was in *documentation* or *methodology* — a stale claim, a metric
applied outside its valid range, an untested assumption, a single-domain measurement presented
as a general conclusion — never in the core FDI/detection logic itself, which has now survived
five independent audit passes and reproduces exactly from frozen weights. The discipline that
found them: **verify every number against a saved artefact before writing it down**, run a
cheap check even when the answer feels obvious, and **measure a claim in every domain it will
be read in** before generalising it. The clearest example of the last one: 2026-08-25i
concluded "adding Tufts does nothing" from a DENTEX-only measurement — true, but only in that
one domain. 2026-08-25j re-measured on Tufts and found +21.5 points. The DENTEX conclusion
about the detector being the binding constraint still stands; the "does nothing" framing did
not, and would have been quietly wrong if the second measurement had not been asked for.

---

## 3. What is NEXT — implementation first, paper draft last

**User's explicit framing: continue implementation now; the paper draft is the final step, not
the next one.** Ordered by what actually blocks something else:

1. **R1 — YOLOv11l-seg retrain. ✅ DONE 27 Aug, and ADOPTED as Stage-1 default.** Box bar
   passed (0.8100 test mAP@0.5 vs a 0.75 bar, and vs the bbox detector's 0.7824); **mask bar
   missed** (0.6383 vs 0.65). Per the pre-registration the bar was not moved and the bbox
   detector *would* have stayed canonical on the bar alone; **the user then decided on 27 Aug to
   adopt it for the +2.76-point box gain regardless.** R2 stays unwired either way.
   `RESULTS_LOG.md` 2026-08-27b/d, `models/11_yolo_seg_tufts_r1/run_summary.txt`.
   ✅ **Stage-2 re-measured 27 Aug — 46.3% → 58.3% end-to-end (+12.0 pts), recall 67.3% → 70.6%**
   (`RESULTS_LOG.md` 2026-08-27e). Constants restored in `run_inference.py`. **Still open:
   upload the checkpoint to Drive** — it is >50 MB and gitignored, so a fresh clone still cannot
   run the pipeline at all; and **C2's Ningxia external validation is still on the old
   detector**, so those numbers are stale in the same way Stage-2 was.
   Original framing kept below for context. Detector recall (67.0%) is the binding constraint on everything
   downstream of it — Stage-2 end-to-end is capped at 67.0% no matter how good the numbering
   is. **This is now measured, not assumed:** doubling the Stage-2 training corpus with Tufts
   moved in-domain end-to-end by +10 teeth of 936, p=0.343 — nothing, against a ~1-point noise
   floor (though it bought +21.5 points out-of-domain — see §2 — a different axis from what R1
   addresses). The head is already 91.0–91.6% on ground-truth boxes; the detector is what is
   missing. `RESULTS_LOG.md` 2026-08-25i, 2026-08-25j. DentFound's ablation (+20.35% precision,
   +23.01% recall, +23.11% F1 from instance masks) is a citable justification, not an assertion.
   Config is **pre-registered** (`T0.6_detector_reconciliation.md` §2): imgsz 1024, batch 32,
   only model+data change — do not shrink the batch to fit a smaller card, that breaks the
   comparison. Runbook: **`docs/research/GPU_SETUP.md`**, rewritten 26 Aug for JarvisLabs with
   the full `jl` CLI command sequence; §6 below is the summary.
   **As of 26 Aug this is blocked on nothing but GPU time** — on the Windows machine the split
   and `dataset_seg/` are both present and verified (`RESULTS_LOG.md` 2026-08-26c). Estimated
   cost on a JarvisLabs A100 80GB at ₹140.94/hr: **~1.5–2 h, ~₹210–280** including upload and
   evaluation (estimate extrapolated from this project's own A100 bbox run, not a vendor claim).
2. **Fix the Tufts Drive permissions.** Costs a minute, zero compute, and is a real submission
   risk if left — see §4. Do this before anything else gets shared or pushed further.
3. **Settle the Tufts-mirror novelty question.** Needs institutional IEEE Xplore access to read
   Panetta et al. (IEEE JBHI 2022) — does it document tooth-1's side? Five minutes for anyone
   with access; cannot be done from open sources (tried and failed twice, `RESULTS_LOG.md`
   2026-08-26a). Until answered, the mirror finding is a **candidate** contribution, not a
   claimed one, in every paper draft.
4. **Bone loss — DECIDED 27 Aug: reported as a measured limitation, NOT fixed.**
   `PAPER_MATERIAL.md` §8.13 is written and is the authority; the paper treats it as a finding,
   not an apology. **This item is closed as a work item and open only as a paper section.**
   The reasoning: the DENTEX+Tufts combined-training lever that fixed Stage 2 **does not
   transfer, because DENTEX carries no bone-loss labels** — Stage 2 worked because both corpora
   label FDI codes, and no second corpus here has periodontal annotation. The alternatives
   (domain-generalisation training, weak supervision from DENTEX `küretaj` markers, acquiring an
   annotated periodontal corpus) are research programmes, not fixes, and none fits the schedule
   before the 14 Oct freeze. Original framing kept below for context.

   **Prior framing:** Bone loss is the standing open research problem, and it is now the CLEAREST one.**
   In-domain 0.92 macro-F1 on Tufts; 0.7% firing on DENTEX; 2.4% affected-tooth sensitivity on
   Ningxia (re-measured 27 Aug on the seg detector; was 2.7%). Two independent external datasets
   agree it collapses outside its training domain.
   ❌ **The "one shared root cause with the detector" guess is now FALSIFIED, not merely
   untested.** Replacing the detector moved Stage 2 by +12.0 pts and caries by +7.7 pts and moved
   bone loss by **nothing** — 168 → 165 teeth flagged over 736 images while the denominator grew
   9% (`RESULTS_LOG.md` 2026-08-27h). The failure is inside the Stage-4a classifier, not upstream
   of it. That removes an entire class of candidate fixes and leaves one obvious lever. **The DENTEX+Tufts combined-training trick that fixed
   Stage 2's generalisation has not been tried here yet** — it is the most promising untried
   lever, since bone loss already has cross-corpus data available (Tufts trained, DENTEX/Ningxia
   measured) but has never been trained on more than one.
5. **T0.5 — the Mild severity class (n=6) decision.** Zero compute, zero blocker, untouched
   for two weeks. The cheapest open item in the project; there is no reason this stays open.
6. **Version-tag the bone-loss weights. ✅ DONE 27 Aug.** `bone-loss-binary-resnet18-v1.0` and
   `bone-loss-severity-resnet18-v1.0`, both hash-pinned. It was not quite trivial: writing the
   summaries exposed that `verify_invariants.py` attributed a sha256 by *position* (last hash
   in the file) rather than by filename, so a summary documenting two checkpoints checked the
   wrong one. Fixed, extracted into `hash_from_summary()`, covered by 8 new tests (65 → 73).
   It also upgraded the bone-loss **class order** from "inferred" to confirmed two ways.
   `RESULTS_LOG.md` 2026-08-27g.
7. **Verify `docker build` actually completes. ✅ DONE 27 Aug 2026 — and the demo RUNS.**
   Executed for the first time in this project. Build completes; container starts; Streamlit
   serves the upload widget; **all seven checkpoints load inside the container** (no `-v` mounts
   needed now that every checkpoint is on local disk). `import cv2` works — the failure mode the
   Dockerfile warns about, which only shows at container start — and `numpy` is 1.26.4 with the
   Hungarian assignment working. **This is no longer a Review-1 blocker.**
   ✅ **Both image defects found by that first run are now FIXED and re-verified**
   (`RESULTS_LOG.md` 2026-08-27k). The image really is CPU-only (torch installed first from the
   CPU wheel index) and torch is pinned to **2.2.0**, the version every published number was
   measured on — pinned in the Dockerfile rather than `requirements.txt`, since the two machines
   run different torch versions and both pass the suite. **Image 11.2 GB → 4.69 GB (−58%).**
   A build-time guard now asserts the torch wheel is not CUDA, numpy is 1.x, and the Hungarian
   assignment runs, so the **build fails** instead of the defect surfacing in a live container:
   `OK torch 2.2.0+cpu | numpy 1.26.4 | hungarian works`.
   ✅ **`jupyter` removed too** (27 Aug, `RESULTS_LOG.md` 2026-08-27l) — not by editing the
   shared `requirements.txt`, which must keep it for the 12 tracked notebooks, but by having the
   Dockerfile install a **derived** subset (`grep -vE '^(jupyter|ipykernel)'`). No second
   requirements file, so nothing can drift. The guard now also asserts the jupyter stack is
   absent *and* that every runtime import still resolves. **Cumulative: 11.2 GB → 4.4 GB, −61%.**
   ⚠️ **One bloat item left:** `.dockerignore` still ships `models/*/run/` and
   `models/06/last.pt` — ~300 MB of the 608 MB models context that inference never reads.
8. **Consider the third public FDI corpus.** DentFound's tooth-ID training data includes the
   Kaggle *Dual-labeled Panoramic Radiographs* set — 2,000 images, **native FDI 11–48, no
   mirror to correct**, larger than DENTEX (634) or Tufts (1,000). Would turn a 2-corpus
   generalisation result into a 3-corpus one — a materially stronger paper claim — for the cost
   of one more crop-builder script. `RESULTS_LOG.md` 2026-08-26a §3.
9. **C1 — VLM baseline.** Deliberately still at 0%; correctly deferred to W5 by the plan's own
   design. Do not pull it forward to fill idle time.
10. **Start IRB paperwork** for the clinic dataset. Zero-cost, longest lead time of anything
    open, still not begun.

**The paper draft is explicitly LAST**, per the user's instruction — not next, not in parallel.
`PAPER_MATERIAL.md` is already structured for it (§5–6 methods, §7 results, §8 limitations
through §8.12, §9 the gap checklist) and the 6 figures are ready to drop in when that phase
starts.

---

## 4. Decisions PENDING — do not default into these silently

| Decision | Why it needs a human |
|---|---|
| **⚠️ Tufts licence breach — act before submitting or sharing further.** The release agreement forbids reproducing or posting the database "into any webpage or any other storage means"; `docs/EXTERNAL_DRIVE.md` records a Drive folder with the raw `ZIP/` release that was browsable **without signing in**. Restrict it, keep Tufts local-only, share the release *form* instead of the files. | Account owner's action, and a real submission risk |
| **⚠️ Real Tufts radiograph pixels are embedded in 7 tracked notebooks, already on `origin/main`** — not references, actual base64 image data in cell outputs (`RESULTS_LOG.md` 2026-08-26b). **The GitHub repo is confirmed private, so this is deferred risk, not an active leak** — the user's explicit call. Must be resolved (strip outputs going forward, or rewrite history — destructive, needs a force-push) **before this repo, or any fork of it, is ever made public.** | Deferred by explicit user decision 26 Aug; revisit before any public release |
| **Is the Tufts mirror finding novel?** NOT established. The Panetta et al. (IEEE JBHI 2022) full text is IEEE-paywalled and unread — tried the indexed biomedical/arXiv corpora, the DOI, the author's own site, PDF search, and GitHub; all dead ends. If the paper documents the convention, this is a usage note, not a discovery. `RESULTS_LOG.md` 2026-08-25h §2, 2026-08-26a. | Needs someone with IEEE Xplore access — a 5-minute read, not a research task |
| ~~**Bone-loss domain-shift fix — what approach?**~~ **RESOLVED 27 Aug: none — reported as a measured limitation** (`PAPER_MATERIAL.md` §8.13). The Stage-2 combined-training lever does not transfer (DENTEX has no bone-loss labels); every remaining option is a research programme that does not fit before the 14 Oct freeze. Kept here for the reasoning, not because it is open. Options span the DENTEX+Tufts combined-training trick that worked for Stage 2 (untried here), R1 (shared Tufts-side fix), Ningxia-informed fine-tuning (needs care — Ningxia is locked, no tuning against it directly), or documenting it as a limitation rather than a fix. | Research direction, not a fact to look up |
| **A third public FDI corpus exists, unused.** DentFound trains tooth-ID on the Kaggle *Dual-labeled Panoramic Radiographs* set — 2,000 images, native FDI 11–48, larger than DENTEX or Tufts, no mirror to correct. | Whether to add it before or after R1 |
| **What else to use `DENTEX/disease/` for**, beyond the Stage-2 eval set (164 leak-free of 250) and the lesion-localisation source. The 91 `saglam` (healthy) teeth as a small real healthy class is still an open candidate use. | Scoping call |
| **Clinic data governance.** `index.csv` sits beside `images/` on a shared Drive, voiding the de-identification. Five actions in `clinical_dataset_provenance.md` §4a, all needing the Drive owner. | Not this repo's account |
| **`split_v1` has a train/test leak** — `590.JPG` (test) and `591.JPG` (train) are byte-identical, so the frozen detector trained on one of its own test images (1 of 150). The Tufts crop builder works around it; the detector's reported test metrics have **not** been re-measured. | Whether to re-measure the detector, or document and move on |

**RESOLVED and kept for the reasoning, not because still open:**
- **How to fix FDI numbering** (22 Aug) — rank-order capped at 66.3%, learned head reaches
  80.2% on the same population. `RESULTS_LOG.md` 2026-08-22f through 24a.
- **The caries gate's negative class** (25 Aug) — MD5-joining the enumeration and disease
  subsets recovers 5,366 real healthy teeth. `RESULTS_LOG.md` 2026-08-25a.
- **Ningxia leakage policy** (25 Aug) — checked against all five corpora separately, zero
  overlap. `RESULTS_LOG.md` 2026-08-25d.
- **Ningxia confirmed unusable for FDI training** (25 Aug) — no tooth-identity field anywhere,
  masks are binary disease-only. `RESULTS_LOG.md` 2026-08-25g.
- **Adopt DENTEX+Tufts as the Stage-2 head?** (26 Aug) — yes, as v2.0, alongside v1.0 rather
  than replacing it. `RESULTS_LOG.md` 2026-08-25j, 2026-08-26a.

---

## 5. Publication target and grading criteria

**Grading rubric, as given to the team:**

| Grade | Requirement |
|---|---|
| **S** | Publication in a journal, or a conference in its **10th edition or later** |
| **A** | Mid-tier conference, **5th–10th edition** |
| **B** | Newer/lower-tier conference, **1st–5th edition** |
| **C** | No publication secured — lowest passing grade |

**Senior guidance on this project:** an IEEE conference with good Scopus indexing is the
target for S/A. Verify Scopus coverage on the official Scopus source list for any specific
venue before submitting — a call-for-papers page claiming indexing is not the same as being on
that list, and indexing status changes.

**Verified venue facts (checked against official sites, 26 Aug 2026 — re-verify before
submission, these move):**

| Venue | Edition | Deadline | Grading band if accepted |
|---|---|---|---|
| **IEEE ISBI 2027** (International Symposium on Biomedical Imaging) | **24th** | Paper submission **26 Oct 2026** | **S** |
| IEEE ICBET 2027 (Biomedical Engineering and Technology) | 17th | Aug 2027 | A |
| Newly-launched venues (e.g. an event advertised as a 1st-edition conference) | 1st | varies | B |

**ISBI 2027 is the named target** (`MASTER_PLAN_2026H2.md`, W8 = ISBI submission window) and
is verified as an S-grade venue by edition count. As of this update: **~2 months to the
deadline.**

### Is this project publishable there, honestly assessed

**Not on the strength of any single model swap** (adopting head v2.0 over v1.0, or v1.0 over
v2.0, is not a publication-deciding change — reviewers do not accept or reject papers on an
internal checkpoint choice). What is actually competitive:

- **Cross-corpus generalisation measured in both directions with paired significance tests**
  (2026-08-25j) — most comparable work does not do this. DPML does not.
- **External validation on 4 hospitals never trained on**, zero leakage verified per corpus.
- **A withdrawn, leakage-corrected result** (52.2% → 46.5%, 2026-08-22j) — reviewers respond
  well to visible correction discipline.
- **An independently-corroborated domain-shift story.** DPML (Cao et al., *ESWA*, 2024) reports
  95.06 mAP on its own 110-image single-centre set but only **61.83 mAP on public DENTEX** — a
  33-point in-domain/out-of-domain gap, from a different Q1 paper, matching what this project
  measured for its own Stage 2 and bone-loss branches. `RESULTS_LOG.md` 2026-08-26a §3.

**What will draw reviewer pushback, and should be framed rather than hidden:**
- **46.6% Stage-2 end-to-end** is not a strong headline number by itself — it is a fair
  end-to-end number *including* the detector's recall, which most comparable work does not
  report on. R1 is the lever that actually raises it.
- **Bone loss collapsing out-of-domain** (0.92 → 0.7–5.4%) reads badly presented as a bug; it
  reads as a genuine, well-measured finding presented as one, since it is corroborated on two
  independent external datasets.

**Do not claim the Tufts-mirror finding as a discovery until §4's novelty item is resolved.**
If it turns out to be undocumented in the source paper, it is a strong, concrete methodology
contribution (a public dataset error nobody else has flagged); until then it belongs in the
paper only as "a labelling convention this pipeline had to detect and correct," not as
"discovered a previously unreported dataset defect."

**Bottom line:** ISBI 2027 (S-grade) is a realistic target if R1 lands and moves the headline
number, and a defensible one even if it does not, on the strength of the generalisation and
external-validation results already in hand. Nobody can promise acceptance; the honest
framing above is what gives it the best odds.

---

## 6. The R1 GPU session — run order, JarvisLabs

> ✅ **R1 IS DONE (27 Aug 2026) and no instance is running.** This section is retained as the
> validated runbook for the *next* rented job, not as an outstanding task. What it cost in
> practice: **₹249.19 across two runs** (one void, one real), against the ~₹210–280 estimated
> for a single run — i.e. the estimate was right, and the overrun was entirely the withdrawn
> run. **₹650.81 remains.**
>
> **Two things this runbook did NOT say, learned the hard way — do them next time:**
> 1. **Verify data geometry against an independent reference BEFORE renting.** The first run
>    burned ~₹119 and 47 minutes training on misaligned masks and failed nothing along the way.
>    `convert_tufts_to_yolo_seg.py` now enforces this automatically and exits non-zero.
> 2. **Re-run that check ON the rented box after upload**, not just locally — cheap insurance
>    that what arrived is what you built.

The only job that needed renting. Everything else runs locally on the M4 Pro (ResNet18 work at
~287 img/s on MPS — minutes per job); the Windows machine is CPU-only torch, so even ResNet18
work is slow there.

**Full runbook with the exact commands: `docs/research/GPU_SETUP.md`** (rewritten 26 Aug 2026
for JarvisLabs, verified against their live pricing and CLI/SSH docs). Summary:

| Step | Action |
|---|---|
| 1 | Provision a JarvisLabs **A100 80GB** (**₹140.94/hr**, verified 26 Aug) holding **batch 32 @ 1024px**, ~17.9 GB. Do not size down to the 40GB card and shrink the batch — that breaks the pre-registered comparison. |
| 2 | Upload `data/tufts/dataset_seg/` (**334 MB**; gzips to roughly half). **Do not upload `best.pt` as a warm start** — `train_yolo_seg.py` deliberately starts from COCO-pretrained `yolo11l-seg.pt`, and §2's pre-registration allows only the model and data to change. Warm-starting from the bbox detector would be a third change and would void the comparison. |
| 3 | Fix `data.yaml`'s absolute `path:` for the rented machine before launching — the uploaded copy still carries the path of the machine that built it. |
| 4 | Run `python scripts/yolo/train_yolo_seg.py` — config is pre-registered, do not modify hyperparameters. |
| 5 | Bring back `weights/` and `results.csv`. Freeze and tag on return, same convention as every other model (`run_summary.txt`, SHA-256, version tag). |
| 6 | Re-run `scripts/eval/verify_invariants.py` and the Stage-2 eval after freezing — detector recall changing should shift the Stage-2 end-to-end ceiling, and that shift needs to be measured, not assumed. |

**What NOT to do:** don't rent for T0.5, the version tag, or IRB paperwork — none of those are
compute. Don't pull C1 forward to use the rented instance "while it's up" — it needs its own
properly-scoped session (W5), not a rushed add-on.

**You do not have to babysit this in a browser.** JarvisLabs ships a `jl` CLI (`jl create`,
`jl upload`, `jl exec`, `jl ssh`, `jl download`, `jl pause`) plus ordinary SSH, so the whole
run can be driven from a local terminal — including by a Claude Code session on the laptop.
Start training detached (`nohup … &`) so a dropped connection cannot kill the run, and
**`jl pause` the instance the moment results are downloaded**; paused instances still bill
storage at ₹0.0130/GB/hr. `GPU_SETUP.md` §2 has the details and the key-setup gotcha (adding
an SSH key does not apply to an already-running instance until you pause and resume it).

**Budget reality (as written before R1 ran; the actual spend was ₹249.19 for both runs, leaving
₹650.81 ≈ 4 h 37 min):** at ₹140.94/hr a ₹900 balance is **6 h 23 min**. R1 was estimated at
~1.5–2 h, leaving room for the one full redo `MASTER_PLAN_2026H2.md` §6 already assumes.
That plan's ~6 GPU-hour line item for this job predates the measured 16.6 s/epoch of the
actual A100 bbox run and looks conservative by roughly 3–4×.

---

## 7. Where the documentation lives

`CLAUDE.md` loads automatically every session and points here. After this file:

| Question | File |
|---|---|
| Current numbers (both Stage-2 heads, both domains) | `docs/results/model_metrics.md` |
| Full technical story + honest limitations | `docs/results/PAPER_MATERIAL.md` |
| What happened, when, and why (append-only) | `docs/results/RESULTS_LOG.md` |
| What to work on next | `docs/research/PUBLICATION_TODO.md` status block, sequenced by `MASTER_PLAN_2026H2.md` |
| Narrative of each session | `docs/session-memory/` (newest file) |
| Documentation layout | `docs/README.md` |
| **Pipeline code, and the three crop contracts easy to get wrong** | **`src/README.md`** |
| Entry points / how to run things, incl. the deployment app | `scripts/README.md`, and `scripts/{yolo,dentex,tufts,eval}/README.md` |
| **Tufts as a second FDI corpus — read before touching its numbering, which is mirrored** | `scripts/tufts/README.md` |
| Datasets: what is where, what is usable | `data/README.md` |
| Weights, version tags, which head is the pipeline default | `models/README.md` |
| **Google Drive links, checkpoint restore steps, and the Tufts licence warning** | `docs/EXTERNAL_DRIVE.md` |
| Paper/review figures | `docs/results/figures/paper/` |
| **This file's own §5** | Publication target and grading criteria |

Every directory containing code has a README; all were swept for staleness across three passes
(25 Aug ×2, 26 Aug) — the last pass specifically checked every README against the v2.0 head
adoption, the licence finding, and the current checkpoint set, since a friend continuing this
work on another machine must not be missing a file or a fact any of these claim is settled.

---

## 8. Local state that git does NOT carry, and what a new machine needs

**If you are setting up this repo on a different machine (a friend continuing the work, or a
fresh clone after `git push`), read this section in full before assuming anything is missing.**

| Item | Where | Note |
|---|---|---|
| DENTEX full release (~14 GB) | `~/Downloads/Capstone/DENTEX/` | Complete and verified. Subset map in `data/README.md`. Not needed for inference, only for re-running training/eval scripts. |
| Tufts raw + rotated radiographs | `_repo_archive/datasets_workspace/` | 1,000 each; `Radiographs_rotated/` is what the detector-training scripts expect. **⚠️ See the licence warning in `docs/EXTERNAL_DRIVE.md` before re-sharing any of this.** |
| Tufts frozen split | `_repo_archive/datasets_workspace/outputs/eda_tufts/split_v1.csv` | Gitignored — which is why a previous session wrongly declared it lost. Contains a known train/test leak (`590.JPG`/`591.JPG`), see §4. |
| **Ningxia** | `~/Downloads/Capstone/ningxia_local/` (test splits, 2.4 GB) | Connected, copied, evaluated. Train (11.2 GB) deliberately left on the pen drive — locked external data, never train on it. |
| Clinic (SDH) data | Not on this machine | Governance-blocked |
| Python env | `/opt/anaconda3` (python 3.12) | **65/65 tests, 7/7 invariants.** torch 2.2.0 + MPS, cv2 5.0.0, ultralytics 8.4.127, scipy, sklearn, streamlit 1.37.1. ⚠️ **`numpy` must stay `<2`** — pinned 1.26.4 in `requirements.txt`; numpy 2.x silently breaks `scipy.optimize` (the Hungarian FDI assignment) at import. A fresh machine should `pip install -r requirements.txt` into a venv rather than assume any particular Python distribution. |
| **Model checkpoints — what `git clone` alone gets you, and what it does not.** | `docs/EXTERNAL_DRIVE.md` | **Only two files, unchanged from before, need a manual fetch**: `models/06_yolo_detection_a100_run/best.pt` (detector, Tufts drive) and `models/09_caries_gate_v3/caries_gate_v3.pth` (caries gate, DENTEX drive) — both >50 MB, gitignored per `CLAUDE.md` rule 4. **Everything else `run_inference.py` needs, including the new Stage-2 head v2.0 (`models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth`, 43 MB), is committed to git and needs no Drive fetch.** `docs/EXTERNAL_DRIVE.md` has exact restore steps and a runnable smoke-test command. |
| Docker daemon | Not verified this session either | `docker build` has never actually executed — see §3 item 7. |
| JarvisLabs instances | Account-level | **None running, none paused — verified 27 Aug.** Both R1 instances (482754 void run, 482810 the real one) were destroyed after artefacts were downloaded and checksum-verified. Balance **₹650.81** of the original ₹900. |
| SSH keys | `~/.ssh/id_ed25519_jarvis` (+ a copy at `~/.ssh/id_ed25519`, since `jl` passes no `-i` and relies on OpenSSH's default lookup) | Registered with JarvisLabs as `r1-seg-windows`. The **E2E** `.pem` pasted into a chat on 20 Aug is still to be treated as compromised — different provider, unrelated key. |

### The Windows machine — a different inventory, verified 26 Aug 2026

The table above describes the **macOS** machine. Work resumed on Windows on 26 Aug, and it
holds a strictly smaller set. Check this before concluding anything is lost:

| Item | Windows | Note |
|---|---|---|
| Tufts raw `ZIP/` — 1,000 rotated radiographs (840×1615), `teeth_bbox.json`, `teeth_polygon.json` | ✅ | ~400 MB, at `data/tufts/ZIP/` |
| `outputs/eda_tufts/split_v1.csv` | ✅ | **Regenerated from code**, SHA-256 verified. `scripts/tufts/regenerate_split_v1.py` |
| `data/tufts/dataset_seg/` | ✅ | Rebuilt 26 Aug, 26,005 instances, 334 MB — reproduces the macOS build exactly |
| `models/06_yolo_detection_a100_run/best.pt` | ✅ | 51 MB, present |
| `models/09_caries_gate_v3/caries_gate_v3.pth` | ❌ | Drive-only; **`run_inference.py` will not complete here until fetched** |
| DENTEX `disease/` (250 img + 250 labels, 1,023 MB) | ✅ | At `~/Downloads/Capstone/DENTEX/disease/` — fetched 27 Aug for the Stage-2 re-measurement. All 500 files integrity-checked (every PNG opened, every JSON parsed). **This is the subset the Stage-2 eval needs**, and it is enough to re-run `validate_fdi_assignment.py` here. |
| DENTEX `training_data/` + `validation_data/` — **the subsets this repo uses** | ✅ **fetched 27 Aug** | **1,390 images + 3 annotation JSONs, 6.0 GB**, every file integrity-checked on download (`scripts/dentex/fetch_dentex_subsets.py`). 705 `quadrant-enumeration-disease/xrays` (caries cascade) + 634 `quadrant_enumeration/xrays` (Stage-2 head) + 51 `validation_data/.../xrays` (extern50). **`verify_invariants.py`'s leakage check and caries v3 MD5 join now RUN rather than SKIP** — the join reproduces the documented 98.28% FDI agreement over 260 shared images. `quadrant/xrays` (693) and `unlabelled/xrays` (1,571) deliberately NOT fetched: `data/README.md` records both as unused. |
| Ningxia | ❌ | `data/ningxia/` holds `manifest.csv` only |
| Tufts bone-loss crops | ❌ | metadata CSVs only, no images |
| `_repo_archive/datasets_workspace/` | ⚠️ partial | Has the EDA/conversion notebooks (incl. `week1_tufts_eda_v2.ipynb`), **not** `Radiographs_rotated/`, `dataset/` or `outputs/` |
| Python env | ✅ **REBUILT 27 Aug 2026** | **Python 3.13.7**, numpy **2.5.2**, scipy 1.18.1, sklearn 1.7.1, torch **2.8.0+cpu**, ultralytics 8.4.130, streamlit 1.62.0, opencv 4.11.0. **79/79 tests pass, all invariants hold** — including the two that used to SKIP for want of DENTEX. CPU-only torch — no local GPU, no CUDA, no MPS, so even ResNet18 jobs are slow here. **The previous 3.11.9 install lost its interpreter mid-session** (`python.exe` and the DLLs vanished while `Lib/site-packages` remained); rebuilt on 3.13. ⚠️ **Python 3.13 cannot satisfy `requirements.txt`'s `numpy<2` pin** — there is no numpy 1.x wheel for cp313, and pip silently builds it from source with MSYS2's MinGW toolchain, producing a numpy that prints "CRASHES ARE TO BE EXPECTED" and emits invalid-value warnings at import. Use numpy 2.x on 3.13 (verified working, below), or install 3.11/3.12 if you want the pin honoured literally. |

**Consequence for planning — UPDATED 27 Aug: DENTEX is now local, so the caries re-run block
(T0.2/T0.3/T0.4) is unblocked on this machine.** The bone-loss cross-corpus experiment is no
longer pending either, but for a different reason: it was **decided against** and written up as a
measured limitation (`PAPER_MATERIAL.md` §8.13) after establishing that DENTEX carries no
bone-loss labels, so the Stage-2 combined-training lever never transferred.

**On the `numpy<2` pin:** `requirements.txt` says numpy 2.x silently breaks `scipy.optimize`,
torch↔numpy and sklearn. That is true of the stack it was written against (torch 2.2.0 / scipy
1.12 / sklearn 1.4, built against numpy 1.x) — it is **not** true in general. Verified on
Windows (re-verified 27 Aug 2026 on the rebuilt env: **numpy 2.5.2 / scipy 1.18.1 /
torch 2.8.0+cpu**, `linear_sum_assignment` and torch↔numpy both correct, 79/79 green, all
invariants hold). Previously verified on numpy 2.4.6 with scipy 1.17.1 / torch 2.13.0, which runs
`linear_sum_assignment` and
torch↔numpy conversion correctly, 65/65 green. The real constraint is that numpy match what
torch/scipy/sklearn were built against, not the number 2. The pin was left unchanged, since it
still protects the environment every published number was produced in. `GPU_SETUP.md` §6.

### Checklist for "does a fresh clone actually run the pipeline"

1. `git clone`, `pip install -r requirements.txt` (venv recommended).
2. Fetch the two Drive-only checkpoints per `docs/EXTERNAL_DRIVE.md` — everything else is
   already in git.
3. `python -m pytest tests/ -q` → should read 65 passed.
4. `python scripts/eval/verify_invariants.py` → should read `all invariants hold` (checks both
   Stage-2 head hashes and the caries gate hash).
5. `python scripts/run_inference.py --image <any_opg.png> --output report.json` → should
   complete and name `models/10_fdi_head_dentex_tufts_v2` in the report's `models` block (that
   is the current default; confirms the right head loaded).

If any step fails, the error names the missing file — cross-check it against
`docs/EXTERNAL_DRIVE.md`'s checkpoint table before assuming something is actually lost.

---

## 9. History — the 20–21 Aug machine handoff (closed)

This file began as a one-off handoff to a second laptop. That handoff is complete: the
uncommitted work was committed and pushed, and the machine switch happened. Two of its claims
turned out to be **wrong**, and both are worth remembering as cautionary examples:

- It declared `outputs/eda_tufts/split_v1.csv` missing after an "exhaustive search". The search
  covered `C:\` and `D:\` — a Windows filesystem — while the repo lives on macOS. The file was
  there all along.
- Its §4 table said the Tufts data would need re-downloading. It was already local.

Full original text: `git show ad71ee4:transfer.md`.
