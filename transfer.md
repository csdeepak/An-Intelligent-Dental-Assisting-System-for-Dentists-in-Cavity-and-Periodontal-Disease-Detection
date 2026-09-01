# CURRENT STATE — read this first

**This file is the project's living state-of-play.** It answers "where are we, what is done,
what is next" for a session that is starting cold — human or AI, on this machine or a new one.
It is **rewritten, not appended to** — unlike `docs/results/RESULTS_LOG.md` (append-only
history) and `docs/session-memory/` (one file per session, never edited). Those two are the
record; this is the snapshot.

**Last updated: 1 September 2026 (evening).** **The plan gained a second track today: improve the
numbers, not just the methodology.** Seven failed caries experiments across three cohorts had left
the paper resting on a negative headline (an image-blind constant ties or beats the pipeline). The
user's decision — pursue score gains in parallel with the write-up, using the
**₹1,105.99 JarvisLabs balance** (now **₹1,084.54**; **nothing running, nothing paused**) —
produced a three-lever plan:

- **Lever 1 — multi-corpus detector retrain.** Detector recall (70.6%) is the *measured* binding
  constraint on the 58.3% Stage-2 headline: `end-to-end = recall × of-detected = 0.706 × 0.826`.
  Pooling DENTEX `quadrant_enumeration` (634 images / 18,095 tooth boxes, already local) with the
  700 Tufts images is **1.9× the detection supervision** — the same move DentFound used (2,698
  images) for its tooth-identification model. **Pre-registered**
  (`outputs/detector_multicorpus/PRE_REGISTRATION.md` + a two-arm amendment), dataset **built and
  geometry-gated locally**, same-day control measured (**end-to-end 0.5844**). **The GPU run was
  rented and then aborted mid-upload — nothing trained.** See the ⚠️ notes below.
- **Lever 2 — caries lesion detector** trained on the CariesXrays benchmark (6,000 images /
  13,783 lesion boxes), which ships its own published FPCL baselines. This would give the project
  its first number placeable *beside a published result on the same data* — the thing a
  conference reviewer can evaluate. Not started.
- **Lever 3 — caries gate retrain** on CariesXrays-derived tooth labels (13× the DENTEX
  positives, a different domain). Cheap follow-on once Lever 1's detector exists. Not started.

**⚠️ Lever 1's first dataset build was VOID and was caught before any GPU spend.** Its Tufts half
was derived from `data/tufts/dataset_seg`, which is the **withdrawn pre-fix corpus from the void
26 Aug R1 run** — labels 90° out, sitting off the dentition. Rebuilt from `Segmentation/teeth_bbox.json`
(the annotation the canonical 0.7824 detector trained on); it now reproduces that detector's
val/test box counts (**3,794 / 3,924**) *exactly*, and the build aborts if it does not.
`RESULTS_LOG.md` 2026-09-01e/f. Lesson twinned with the DOI one below: **a gate that only checks
the half you already suspect is not a gate.**

**⚠️ The A30 GPU run was created, then terminated by the user during a slow 816 MB rsync upload —
₹21.45 spent, nothing trained, no instances left.** `jl create --gpu A100` had returned "not
available", so an **A30 (24 GB, ₹38.88/hr)** was used instead — it holds R1's `batch 32 @ 1024`
config unchanged. Next attempt: **tar the dataset and upload one file** — rsync of 3,268 small
files was the bottleneck (~19 MB/min). The `jl` CLI is now installed and authenticated on this
Mac, this machine's SSH key is registered as `macos-m4pro`, and live pricing + macOS setup notes
are in `GPU_SETUP.md` §0.

**The sixth-cohort result stands — it is the strongest form of the paper's central claim.**
CariesXrays (Chen et al., **AAAI 2024**, DOI 10.1609/aaai.v38i20.30196), evaluated with the
**frozen** pipeline, randomised 1,500 images / **3,421 lesions** (more than DENTEX and Ningxia
combined): **pipeline 0.309 vs constant 0.561, paired Δ +0.252 [+0.232, +0.273]** — the constant
wins outright. Mechanism measured: **72.0% of lesions on molars, 60.2% on the eight constant
teeth**. Across cohorts: +0.046 (DENTEX), −0.009 (Ningxia, tie), **+0.252** (CariesXrays). Folded
into `main.tex` as a new Table + §8.25; provenance verified against AAAI OJS / ACM DL / DBLP
(licence not stated by the authors). `verify_paper_numbers.py` now asserts **90** claims (was 82).

**⚠️ NEW SUBMISSION BLOCKER — 22 of 63 checkable DOIs in `source.bib` are broken.** Every DOI was
dereferenced against the registry: **11 resolve to a *different paper*** (e.g.
`karamuftuo2025panoramic` → *Foundations of Pediatric Lifestyle Medicine*), **11 are not
registered with any agency**, and 19 further entries carry no DOI and were not checkable. This
does **not** prove the papers are fabricated — a real paper can carry a mistyped identifier — but
**each of the 22 needs a manual title lookup before submission**. It survived the 28 Aug audit
because `audit_citations.py` makes no network call and had a hardcoded Windows path (fixed).
`outputs/citation_audit/FINDINGS.md`, `RESULTS_LOG.md` 2026-09-01c/d,
`scripts/verify_citations_crossref.py`. One 8th citation error was *fixed*: `chen2024cariesxrays`
pointed at the adjacent AAAI article (30197, an unrelated fairness paper); corrected to 30196.

**Previously: 31 August 2026.** Two things landed today. **(a) The caries branch was diagnosed
and three fixes were tried; all three failed and are recorded** — `RESULTS_LOG.md` 2026-08-31,
`PAPER_MATERIAL.md` §8.24, `docs/session-memory/2026-08-31-caries-position-bias-and-v4.md`. The
finding: **the gate scores teeth partly by which tooth it is.** Its mean score on *genuinely
healthy* teeth tracks the training base rate for that position (0.075 healthy incisors → **0.478
healthy molars**), so **48.2% of healthy molars are flagged** — 79 of the 142 false positives —
while only **1 of 8 incisor lesions** is found. Real signal survives removing the prior
(**within-type AUC 0.7454 [0.6604, 0.8420]**), so the gate is not blind, but its reported score is
substantially an anatomical prior. **This is the mechanism behind §8.22's constant baseline** and
upgrades that finding from a claim about the metric to a measurement of the system. What failed:
threshold tuning (0.50 already F1-optimal), per-tooth-type thresholds (F1 +0.006, CI spans zero),
and **gate v4 trained on 2.67× the positives** after finding **62% of DENTEX's caries supervision
unused** (2,767 annotations available, 1,049 used) — **AP 0.5503 → 0.5496, paired delta −0.0015
[−0.0886, +0.0821]. v4 NOT adopted;** v3.0 remains the pinned default. Raising resolution was also
ruled out by measurement (median box 170×287 vs the 224² already fed in). ⚠ **v4's own report shows
P 0.71 / R 0.80 on its own test split — that is a 2.2× prevalence difference, not an improvement
(specificity unchanged, 0.853 vs 0.843). Never quote it against v3's 0.398.**
**Then three further arms were pre-registered and run (`RESULTS_LOG.md` 2026-08-31b): CLAHE, a
1.25× crop expansion, and position-balanced sampling, each against a same-day control that
reproduced v3's val macro-F1 exactly (0.7350). ΔAP: CLAHE +0.0488 [−0.0031, +0.0993] — **misses the
pre-registered bar by 0.0031**; crop 1.25× +0.0198, position-balanced +0.0432, both n.s. **The bar
was not moved and nothing was adopted.** One real secondary effect: **CLAHE gains precision +5.6 pp
[+0.011, +0.101] with no significant recall cost.** **Five independent attempts have now failed to
lift this curve, so "the caries branch is at its headroom on DENTEX" is the supported reading, not
a worry — it is a citable result.** The blocker on settling CLAHE is statistical, not
methodological: 863 test crops but only **34 source images**, so a +0.049 effect cannot be
separated from zero. All of it ran **locally on MPS in ~35 min; no GPU was rented** (§6's rule).
**(b) Staleness sweep + Review-1 prep. Earlier on 31 Aug:**
relabelled the panel deck `REVIEW3_PANEL.html` for **Phase 3 / Progress Review 1** (course code
`UE23CS441A`, Semester VII, left contents navbar, two pre-existing render bugs), added a
"00 — Review 1" prep section to `TEAM_HANDBOOK.html`, and corrected the stale `model_metrics.md`
header (`docs/session-memory/2026-08-31-review1-panel-prep.md`). The **29 August** session
(`docs/session-memory/2026-08-29-readme-rebuild-svg-assets.md`)
rebuilt the root **`README.md`** against the artefacts and added `docs/assets/` — seven
hand-authored animated SVGs (hero, pipeline, error-propagation, C1 baselines, C2 domain shift,
C4 abstention, repo-structure). It trained nothing (no `RESULTS_LOG.md` entry, by rule 1) and
re-ran the suite (**122/122**) and `verify_invariants.py` (all hold) only to confirm the README
badges — the tests badge had said 84 and the file tree 65. **Two things it leaves for the next
session:** `docs/assets/*.svg` now carry hard-coded headline numbers (edit them when a number
moves, or generate them from the JSONs); and
`docs/architecture/corrected_opg_pipeline_architecture.svg` and `docs/assets/pipeline.svg` now
both claim to describe the pipeline — pick one as authoritative.

> ⚠️ **§8's "Local state that git does NOT carry" table is now partly wrong.** Commits `f6609b7`
> and `1b430e2` (already on `origin/main`) stopped git-ignoring `outputs/` and committed most
> training outputs plus the sub-50 MB ResNet18 checkpoints — `.git` is now ~763 MB. Reconcile
> with `CLAUDE.md` rule 4 (weights gitignored, Drive-only) and rewrite §8 to match, or revert the
> commits. The two >50 MB detector checkpoints remain Drive-only, and
> `models/11_yolo_seg_tufts_r1/best.pt` is still not uploaded (§3 item 4).
> **Partially addressed, 30 Aug:** the *ignore policy itself* was fixed the same day this landed
> — `outputs/*` plus a curated per-directory whitelist replaced the blanket `!outputs/**`
> (`0bda8d5`, `2f436b9`), so future runs no longer become trackable by default, and one
> already-tracked duplicate checkpoint was caught and kept out. **The existing ~763 MB already in
> history is untouched** — that still needs a deliberate, team-coordinated history rewrite
> (everyone re-clones after), or a decision to accept it. Not done, just no longer growing
> silently.

**Previously: 30 August 2026** — the **SDH clinic track was unblocked**: the clinic gave consent
(written agreement expected 1 Sep), the data turns out to be on *this* machine, the pipeline runs
on it unmodified at **2.2 s/image on CPU** (so Tier A needs **no GPU**), and the first pass that
ever opened all 3,219 files found **six truncated images** — the usable set is **3,213**, and
`checkpoint.json` had been claiming 3,219 since June. Plan:
`docs/research/SDH_EXECUTION_PLAN.md`; numbers: `RESULTS_LOG.md` 2026-08-30. **It is not on the
critical path** — see §3 item 10. Nothing below this paragraph changed on 30 Aug.

**Previously: 28 August 2026.** **A complete manuscript now exists and compiles**, rebuilt from the artefacts after a full evidence audit (`docs/paper/REBUILD_AUDIT.md`, `RESULTS_LOG.md` 2026-08-28). Five defects in the previous draft were found and corrected — the worst was a whole-system parameter count of "~25 M" that was the *superseded detector alone*; the pipeline is **83.6 M across six models, 61.2 M on the caries path**, and that wrong figure had propagated into 9 places across 6 files. **The critical path is no longer "write the draft" — it is the venue-length cut** (12 pages against ISBI's 4) plus the four non-engineering compliance blockers. 122/122 tests, 82 manuscript numbers auto-verified against their JSONs, all invariants hold, ₹~313 GPU balance at the time (now ₹1105.99), nothing running.

**Previously: 27 August 2026**, end of a very long session. C1 ran and landed (VLM below a constant guess); the rigor block — confidence intervals, calibration, failure taxonomy, related work, ethics — is done; bone loss is a decided limitation rather than an open problem; DENTEX is local; the environment was rebuilt on Python 3.13 after the 3.11 install lost its interpreter mid-session. `RESULTS_LOG.md` 2026-08-27f … 2026-08-27aa is that day's history.

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

**Everything is measured AND written. What is left is a length cut and paperwork.** The six-stage
pipeline runs end to end, is deployed in a verified Docker image, and has been evaluated on four
hospitals *and* a second public benchmark (CariesXrays, AAAI 2024) it never trained on — **six
independent cohorts**. The results block is complete — C1, C2, C3-style error attribution,
confidence intervals, calibration and a failure taxonomy all exist as numbers with saved artefacts
behind them — and as of 28 August those numbers are assembled into a **complete manuscript that
compiles clean** (0 errors, 0 overfull boxes, 0 undefined references, 12 pages; §8.25 + the
3-cohort table added 1 Sep, so re-compile and re-measure length).

**The manuscript's title changed on 28 Aug, and the reason matters.** It was *"What Does 44 %
Mean?"* — but 44.3 % is 212/479, the *pipeline's own* lesion-localisation agreement: one row of one
table, never written as "44 %" in the body, and not the finding. It is now **"What a Tooth-Level
Score Cannot Tell You: Constant Baselines, External Validation and Domain Shift in Automated
Panoramic Dental Screening"**, which names the contribution rather than a result — necessary,
because the result does **not** replicate externally.

**⚠️ A wrong number had propagated into nine places before anyone counted it.** The pipeline was
described everywhere as "~25 M parameters". That is the **superseded bbox detector alone**. Counted
from the checkpoints: **83.56 M across six models, 61.19 M on the caries path** (per-stage table in
`model_metrics.md`). Corrected in 5 files; `RESULTS_LOG.md` records it rather than being edited.
`scripts/verify_paper_numbers.py` now asserts **90** manuscript numbers against their artefacts (was
82; +8 for the CariesXrays cohort, 1 Sep) so this class of drift fails loudly next time.

**The headline: Stage-2 FDI is 58.3% end-to-end [53.9, 62.8], and that is a DETECTION-bound
number.** 29.4% of ground-truth teeth are never detected; **of the 661 teeth Stage 1 does find,
Stage 2 numbers 82.6% correctly**. Report both. 77.4% of the numbering errors that remain are
benign off-by-one; only 2.4% of detected teeth suffer a category error (§8.16 in
`PAPER_MATERIAL.md`).

**C1 is DONE and hardened, and the honest version is more complicated than it looked on 27 Aug.** A general-purpose VLM zero-shot scores **F1 0.149 at 7B** (reproducing 27 Aug's 0.143 on new hardware and a new transformers major version) and **0.246 at 32B** — scale helps a lot. **Few-shot makes it monotonically worse** (0.066 at 2-shot, 0.034 at 4-shot) because in-context examples teach it to answer *nothing*: 123 of 164 answers are empty at 4-shot. Both models still hand a confident dental answer to a **random-noise image**. **But the result that constrains the write-up: a fixed list of the eight first/second molars — fitted on held-out images, never on the scored set — scores 0.320, above our pipeline's 0.294.** Tooth-level FDI-set F1 is base-rate dominated; that constant must appear beside every C1 arm, and C1 must not be headlined as "small specialist beats large generalist" without it. The efficiency claim survives: 33.45 B params and 70.1 GB of H100 VRAM still lose to **61.2 M** params on a CPU (caries path; 83.6 M all six models — counted 28 Aug, correcting the "~25 M" that was the detector alone). Cost Rs 285.20 (+ Rs 14.26 wasted on a stray instance); **~Rs 313 remains**, nothing running.

**C2 external validation, re-measured on the seg detector with same-machine controls:** caries
lesion agreement **28.8–51.3% across four Ningxia hospitals (40.8% pooled)** against **44.3%
DENTEX internal — the internal/external gap more than halved, 8.9 → 3.5 pp**. Only the external
gain is statistically real (+7.7 pp [+3.3, +12.0]); the internal one is not (+2.3 pp [−3.4, +7.9]).

**Bone loss is now a DECIDED limitation, not an open problem.** 0.92 in-domain collapses to 0.7%
firing on DENTEX and 2.4% on Ningxia. The detector swap moved Stage 2 by +12.0 and caries by +7.7
and bone loss by **nothing**, which falsified the shared-root-cause hypothesis; and DENTEX carries
no bone-loss labels, so the combined-training lever never existed. Written up as `PAPER_MATERIAL.md`
§8.13. **Its crops cannot be rebuilt on this machine** (§8, and `RESULTS_LOG.md` 2026-08-27u).

**159/159 tests pass** (122 → 159: +37 orientation round-trip property tests added 1 Sep with
`src.orientation.rot_box`/`rot_boxes`, for Lever 1's DENTEX→detector-frame box conversion),
**`verify_invariants.py` all-hold** with 3 previously-skipping checks now live.
We are past W2 of the 8-week plan on results and, as of 28 Aug, **no longer behind on prose**;
implementation freeze **14 Oct**, ISBI **26 Oct**.

**⚠️ Four things block submission and NONE are engineering** — all are account-owner actions:
(1) a Tufts Drive folder browsable without sign-in, which its licence forbids; (2) DENTEX and
Ningxia licences never read or recorded; (3) SDH `metadata/index.csv` sharing a folder with
`images/`, which voids that copy's de-identification; (4) IRB not started. `PAPER_MATERIAL.md`
§8.19 has the seven-item checklist. Also deferred by explicit decision: real Tufts pixels embedded
in 7 tracked notebooks on `origin/main` (repo private — must be resolved before any public release).

**The user's stated intent: implementation first, paper draft last.** That inverted on 27 Aug, and
on 28 Aug the draft landed too. **What is on the critical path now is the venue-length cut** — the
manuscript is 12 pages and ISBI allows 4. It was deliberately written as a complete, self-explaining
document; the cut is a separate, venue-specific task and should not be done by re-compressing prose
that was just written to be clear. §III–§V and the 12-item limitations list are where the
compression lives, and some of it may belong in supplementary material. **Decide the venue first —
the cut differs.**


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
| **All READMEs + this file** swept for staleness (four passes across three sessions; last 1 Sep — 159 tests, 90 paper numbers, CariesXrays cohort, DOI blocker, Lever 1 scripts) | `RESULTS_LOG.md` 2026-08-25e/f, 2026-08-26b, this rewrite |
| Test suite | **159/159 pass** (122 + 37 orientation round-trip tests, `tests/test_orientation_roundtrip.py`, 1 Sep); `verify_invariants.py` all-hold, with **3 checks that used to SKIP now live** (leakage exclusion, caries-v3 MD5 join at 98.28%, caries-v3 dataset hygiene) since DENTEX is local |
| **C1 — VLM baseline** (27 Aug) | Qwen2.5-VL-7B zero-shot F1 **0.143** vs our **0.294**, and **below a constant guess (0.204)**; blank/noise images give the same answer. `RESULTS_LOG.md` 2026-08-27aa, `PAPER_MATERIAL.md` §8.20 |
| **Confidence intervals** (27 Aug) | Cluster-bootstrap over images for Stage-2, lesion agreement and Ningxia caries, plus paired CIs on the detector-swap deltas. **Two of that day's own claims failed their intervals and were withdrawn.** §8.14 |
| **Calibration** (27 Aug) | Caries gate ECE **0.136**, systematically overconfident; temperature scaling made it worse (structural, not scale); isotonic fixes it (**0.043**) and is wired **confidence-only**, verdicts byte-identical. §8.15 |
| **Failure taxonomy** (27 Aug) | Stage-2: 58.3% shown detection-bound (**82.6% of detected**), 77.4% of errors benign off-by-one. Caries panel: gate over-calls healthy teeth (19.2%) at the same rate as impacted (19.0%). §8.16, §8.17 |
| **Related work + ethics** (27 Aug) | Comparison table from the review sheet; **only 2 of 49 task-relevant papers validate externally**. Ethics statement with a 7-item pre-submission checklist. §2.1, §8.19 |
| **`docker build` verified** (27 Aug) | Builds, runs, app loads, all 7 checkpoints load in-container; image made genuinely CPU-only and reproducible, **11.2 GB → 4.4 GB**. §3 item 7 |
| **C4 — abstention** (28 Aug) | Coverage-accuracy curves. Declining the least-confident quarter lifts Stage 2 **0.826 → 0.885** and the caries gate **0.797 → 0.940**; shuffling the confidences collapses both gains to ~0, so the ranking carries real information. The pre-registered 0.30 threshold lands at **90.8% coverage / 0.847**, within 0.2 pp of the empirical 90% point — and was **not** tuned. **C4 had never been produced**: the `assessable` flag existed, the curve did not. `RESULTS_LOG.md` 2026-08-28a, `PAPER_MATERIAL.md` §8.21 |
| **C1 hardened** (28 Aug) | Scale, few-shot and reproducibility arms. 7B 0.149 (reproduces 0.143 across hardware + a transformers major version), 32B **0.246**, few-shot degrades monotonically to 0.034 via abstention (123/164 empty). **An image-blind constant fitted on held-out data scores 0.320, above our 0.294** — tooth-level F1 is base-rate dominated and that row must be published beside every arm. `RESULTS_LOG.md` 2026-08-28b, `PAPER_MATERIAL.md` §8.22 |
| **Stage-2 head v3, 3 corpora** (28 Aug) | Kaggle dual-labeled added as a third FDI corpus (499 images / 13,166 teeth; numbering verified standard by arbiter, 80.3% direct vs 1.7% mirrored). Against a same-day control: **DENTEX +1.14 pp [+0.33,+1.95] significant**, Tufts flat, nothing regressed. **Reported ablation, NOT the default** — swapping invalidates the 58.3%/82.6% headline, C4 curves and §8.16. `models/12_fdi_head_v3_3corpus/`, `RESULTS_LOG.md` 2026-08-28c |
| **Root `README.md` rebuilt** (29 Aug) | Rewritten against the artefacts, with seven hand-authored animated SVGs in `docs/assets/`. Cleared stale front-page claims: the tests badge said **84** and the tree said **65** (both are **122**); Stage 1 still led with the superseded detector's **0.782** rather than the default's **0.810**; Phase 6 still read "drafting has not started"; the risk table still called external validation "out of scope for the capstone" *after* four hospitals had been run; `models/11,12,12a`, `scripts/kaggle_dual`, `docs/paper` and `docs/assets` were missing from the tree. Every link, image path and anchor is machine-checked; 122/122 and `all invariants hold` re-run to confirm the badges. `docs/session-memory/2026-08-29-readme-rebuild-svg-assets.md` |
| **Tufts 90-degree geometry bug FIXED** (28 Aug) | Every Tufts radiograph here is rotated 90 degrees; the crop builder silently produced 23% degenerate crops and the repo's own alignment guard passed it (both orientations score >1.0). CCW rotation reproduces v2's corpus exactly (35,248/3,721/3,786). Builder now aborts above a 2% degenerate rate. Upright copies at `data/tufts/ZIP/Radiographs_upright`. **Does not unblock bone loss** — that is a separate defect |

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

## 3. What is NEXT — two tracks now: finish the paper, and lift the numbers

**Track A (write-up) was the whole plan until 1 Sep; Track B (score improvement) was added by
explicit user decision that day.** They run in parallel — Track B is funded from the GPU balance
and owned by whoever is at the terminal; Track A is mostly account-owner paperwork. If they
conflict for time, Track A wins: a clean submission beats a better number that misses the venue.

### Track A — get the manuscript submittable

1. **CUT THE MANUSCRIPT TO VENUE LENGTH.** `paper/main.tex` compiles clean (last verified 28 Aug;
   **re-compile — no LaTeX toolchain on this Mac**, and §8.25 + the 3-cohort table were added
   1 Sep, so it is now longer than 12 pages). ISBI allows 4. Pick the venue first — a journal
   needs no cut. `docs/paper/REBUILD_AUDIT.md` Deliverable 4 maps section purpose.
2. **⚠️ FIX THE 22 BROKEN DOIs** (`outputs/citation_audit/FINDINGS.md`). Per entry: look the work
   up by title, then correct the DOI or drop the reference. Cannot be automated. Also decide what
   to do about the 19 DOI-less entries. Re-run `scripts/verify_citations_crossref.py` after.
3. **Authors and affiliations are still `Unknown`** in `main.tex`. Blocking, not engineering.
4. **The four compliance blockers** (§1, `PAPER_MATERIAL.md` §8.19). Zero compute, all
   account-owner actions, and (1) and (3) are live protocol breaches rather than paperwork.
5. **Upload `models/11_yolo_seg_tufts_r1/best.pt` to Drive.** Still the only thing standing
   between this repo and a working fresh clone. Recipe and hash in `docs/EXTERNAL_DRIVE.md`.
6. **Bone-loss calibration / CIs / the three §9 ablations** — all blocked on the same thing:
   `Radiographs/Radiographs/`, the ORIGINAL un-rotated Tufts radiographs, which are not on this
   machine. Note that even with them, **49.6% of the val crops carry unsaved jitter offsets and
   are irreproducible by anyone**, so any future bone-loss number is on a 785-crop subset and must
   say so.
7. **Remaining CI coverage** — Ningxia periodontitis, detection mAP and both ResNet18s have no
   intervals because no per-item prediction dumps are saved. Adding those dumps is cheap CPU work.
8. **`docker build` is verified and the demo runs** — but the image predates the confidence-only
   isotonic wiring, so rebuild it before any Review-1 demo.
9. **IRB paperwork** — longest lead time of anything open, still not begun.
10. **SDH clinic track — unblocked 30 Aug, and it is NOT on the critical path.** Consent from the
    clinic was obtained (written agreement expected 1 Sep), closing `PUBLICATION_TODO.md` T1.2's
    governance block. The data is on the **Windows** machine's `D:` (§8), the pipeline runs on it
    unmodified at **2.2 s/image on CPU**, so a full-set pass is a ~2-hour unattended job needing
    **no GPU**.
    Plan, tiers, filter design, pre-registered criteria: **`docs/research/SDH_EXECUTION_PLAN.md`**;
    first measurements: `RESULTS_LOG.md` 2026-08-30. **If item 1 slips, this is what gets
    deferred.** Two things must happen before any SDH number is produced: repair or exclude the
    six truncated images (`001970`–`001975`, found 30 Aug — the usable set is **3,213**, not
    3,219), and freeze `data/sdh/splits_v1.json` before a single filter threshold is chosen.

### Track B — lift the numbers (funded from the GPU balance)

**Pre-condition, learned twice on 1 Sep:** every dataset built for a rented run is verified
locally first — round-trip geometry, canonical-count reproduction, and a render inspected by eye —
because the two failure modes that have cost this project real time (R1's misaligned masks, and
the void `dataset_seg` used for Lever 1's first build) both produced *smoothly-falling loss on
garbage* and errored nowhere.

- **B1 — Lever 1 detector retrain (Tufts + DENTEX).** Dataset is **built, gated, and correct**
  (`data/detector_multicorpus/`, 1,334 train / 150 val / 150 test, val/test Tufts-only and
  canonical). Same-day control measured: end-to-end **0.5844**. Two arms, pre-registered:
  Control B = Tufts-only `detect` (isolates the `seg → detect` head change, since DENTEX has no
  polygons), Arm = Tufts + DENTEX `detect` (isolates the data). Adoption requires the paired ΔFDI
  CI to exclude zero **and** Tufts test box mAP@0.5 ≥ 0.75. **Only the GPU run remains** — tar the
  dataset, upload once, train both arms (~₹210 on an A30, ~5 h). `scripts/yolo/train_multicorpus_detector.py`.
- **B2 — Lever 2 caries lesion detector on CariesXrays.** Not started. Needs its own
  pre-registration and its own image-level split; the AAAI paper's FPCL baselines are the
  comparison target (**not yet read — quote nothing from them until they are**).
- **B3 — Lever 3 caries gate v5** on CariesXrays-derived tooth labels. Blocked on B1 (needs the
  better detector to assign lesion boxes to teeth). Cheap.
- **NOT a lever, and decided against:** a 4th caries-gate arm chasing CLAHE's +0.049 AP
  near-miss. Its CI includes zero and the blocker is 34 source images, not method
  (`RESULTS_LOG.md` 2026-08-31b).

**Do NOT do:** train on Ningxia, or iterate against it. It is locked external test data and it is
the single strongest thing this paper has (`MASTER_PLAN_2026H2.md` §4.1). A tune-against-it loop
was proposed and declined on 27 Aug for exactly this reason.


## 4. Decisions PENDING — do not default into these silently

| Decision | Why it needs a human |
|---|---|
| **⚠️ Tufts licence breach — act before submitting or sharing further.** The release agreement forbids reproducing or posting the database "into any webpage or any other storage means"; `docs/EXTERNAL_DRIVE.md` records a Drive folder with the raw `ZIP/` release that was browsable **without signing in**. Restrict it, keep Tufts local-only, share the release *form* instead of the files. | Account owner's action, and a real submission risk |
| **⚠️ Real Tufts radiograph pixels are embedded in 7 tracked notebooks, already on `origin/main`** — not references, actual base64 image data in cell outputs (`RESULTS_LOG.md` 2026-08-26b). **The GitHub repo is confirmed private, so this is deferred risk, not an active leak** — the user's explicit call. Must be resolved (strip outputs going forward, or rewrite history — destructive, needs a force-push) **before this repo, or any fork of it, is ever made public.** | Deferred by explicit user decision 26 Aug; revisit before any public release |
| **Is the Tufts mirror finding novel?** NOT established. The Panetta et al. (IEEE JBHI 2022) full text is IEEE-paywalled and unread — tried the indexed biomedical/arXiv corpora, the DOI, the author's own site, PDF search, and GitHub; all dead ends. If the paper documents the convention, this is a usage note, not a discovery. `RESULTS_LOG.md` 2026-08-25h §2, 2026-08-26a. | Needs someone with IEEE Xplore access — a 5-minute read, not a research task |
| ~~**Bone-loss domain-shift fix — what approach?**~~ **RESOLVED 27 Aug: none — reported as a measured limitation** (`PAPER_MATERIAL.md` §8.13). The Stage-2 combined-training lever does not transfer (DENTEX has no bone-loss labels); every remaining option is a research programme that does not fit before the 14 Oct freeze. Kept here for the reasoning, not because it is open. Options span the DENTEX+Tufts combined-training trick that worked for Stage 2 (untried here), R1 (shared Tufts-side fix), Ningxia-informed fine-tuning (needs care — Ningxia is locked, no tuning against it directly), or documenting it as a limitation rather than a fix. | Research direction, not a fact to look up |
| ~~**A third public FDI corpus exists, unused.**~~ **RESOLVED 28 Aug: added, and it stays an ablation.** Head v3 trained on DENTEX+Tufts+Kaggle gains **+1.14 pp on DENTEX val** [+0.33, +1.95] against a same-day control; Tufts flat; the pipeline default stays v2.0 because swapping it invalidates every Stage-2 number in the paper. The corpus is **500 images, not 2,000**, and its FDI convention was verified by arbiter, not assumed. `PAPER_MATERIAL.md` §8.23. | Closed |
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
> run. **₹650.81 remained then; the current balance is ₹1,084.54 (§8).**
>
> **The next rented job is Lever 1 / B1** (multi-corpus detector, §3 Track B). Its dataset is
> built and gated; a first A30 attempt on 1 Sep was aborted mid-upload (₹21.45, nothing trained).
> The macOS `jl` runbook is `GPU_SETUP.md` §0. Same rule as R1 applies: re-run the geometry gate
> **on the rented box** after upload, before launch.
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
| The root `README.md`'s animated SVGs | `docs/assets/` — **they carry hard-coded numbers; edit them when a headline number moves** |
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
| Clinic (SDH) data | ~~Not on this machine~~ **Wrong — struck 30 Aug 2026.** It is on the **Windows** machine, on `D:` — see the Windows table below | Consent obtained 30 Aug (written agreement expected 1 Sep). Plan: `docs/research/SDH_EXECUTION_PLAN.md` |
| Python env (macOS, as of 26 Aug — historical) | `/opt/anaconda3` (python 3.12) | **65/65 tests, 7/7 invariants** *(that machine, that date; this machine is now Python 3.13 with 84/84 — see the Windows table below)*. torch 2.2.0 + MPS, cv2 5.0.0, ultralytics 8.4.127, scipy, sklearn, streamlit 1.37.1. ⚠️ **`numpy` must stay `<2`** — pinned 1.26.4 in `requirements.txt`; numpy 2.x silently breaks `scipy.optimize` (the Hungarian FDI assignment) at import. A fresh machine should `pip install -r requirements.txt` into a venv rather than assume any particular Python distribution. |
| **Model checkpoints — what `git clone` alone gets you, and what it does not.** | `docs/EXTERNAL_DRIVE.md` | **Only two files, unchanged from before, need a manual fetch**: `models/06_yolo_detection_a100_run/best.pt` (detector, Tufts drive) and `models/09_caries_gate_v3/caries_gate_v3.pth` (caries gate, DENTEX drive) — both >50 MB, gitignored per `CLAUDE.md` rule 4. **Everything else `run_inference.py` needs, including the new Stage-2 head v2.0 (`models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth`, 43 MB), is committed to git and needs no Drive fetch.** `docs/EXTERNAL_DRIVE.md` has exact restore steps and a runnable smoke-test command. |
| Docker daemon | Not verified this session either | `docker build` has never actually executed — see §3 item 7. |
| **CariesXrays dataset** (~2 GB) | `~/Downloads/Capstone/CariesXrays_Dataset/` | AAAI 2024 (Chen et al.), 6,000 panoramic images + Pascal-VOC lesion boxes. Used **frozen-pipeline only** as the 6th external cohort (`scripts/eval/cariesxrays_external.py`); a random seed-42 draw of 1,500 was scored. No LICENSE file ships with it — recorded in `main.tex` §8.25. Not needed for inference. |
| **Multi-corpus detector dataset** (Lever 1 / B1) | `data/detector_multicorpus/` (~816 MB, gitignored) | Built + geometry-gated 1 Sep by `scripts/yolo/build_multicorpus_detector_dataset.py` (Tufts 700 + DENTEX `quadrant_enumeration` 634 → YOLO `detect`, detector-rotated frame). 1,334 train / 150 val / 150 test; val+test are Tufts-only and reproduce the canonical **3,794 / 3,924** box counts exactly. Regenerable; never commit the images. |
| JarvisLabs instances | Account-level | **None running, none paused — verified 1 Sep.** History: both R1 instances destroyed 27 Aug (balance then ₹650.81); balance later topped up to **₹1,105.99**; on 1 Sep an **A30 24 GB** instance was created for Lever 1 (`jl create --gpu A100` returned "not available"), then **terminated by the user during a slow rsync upload before any training started** — **₹21.45 spent, nothing trained**. Balance now **₹1,084.54**. Next attempt: `tar` the dataset and upload one file (rsync of 3,268 small files was the bottleneck). |
| SSH keys | `~/.ssh/id_ed25519_jarvis` (+ a copy at `~/.ssh/id_ed25519`, since `jl` passes no `-i` and relies on OpenSSH's default lookup); this Mac's own key at `~/.ssh/id_ed25519` | Two keys registered with JarvisLabs: `r1-seg-windows` (the Windows box) and **`macos-m4pro`** (this machine, added 1 Sep). The `jl` CLI (0.2.17) is installed and authenticated here — the user ran `jl setup` themselves; the token is not in this repo or any session. The **E2E** `.pem` pasted into a chat on 20 Aug is still to be treated as compromised — different provider, unrelated key. |

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
| **Clinic (SDH), all three stages** | ✅ **verified 30 Aug 2026** | `D:\raw data\` (4,433 `.pano`), `D:\dataset_audit\` (Stage-1 conversion + the audit CSVs), `D:\SDH dataset\dataset\` (3,219 enhanced 8-bit PNGs, 3.72 GB, **3,213 readable** — six are truncated, `RESULTS_LOG.md` 2026-08-30). One image per patient, 3,220 distinct patient folders. **Never on the macOS machine.** Metrics-only artefacts are tracked at `data/sdh/`; no pixel leaves `D:`. Plan: `docs/research/SDH_EXECUTION_PLAN.md` |
| Tufts bone-loss crops | ❌ | metadata CSVs only, no images. **The pixels cannot be rebuilt here (27 Aug):** they were made from `Radiographs/Radiographs/` — the ORIGINAL un-rotated radiographs — which this machine does not have, and **49.6% of the val crops carry unsaved jitter offsets and are irreproducible by anyone**. A best-effort rebuild from the rotated copies scored sensitivity 0.40 vs a documented 0.83 and was rejected. Blocks bone-loss calibration, CIs and all three §9 ablations. `RESULTS_LOG.md` 2026-08-27u |
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
3. `python -m pytest tests/ -q` → should read 159 passed.
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
