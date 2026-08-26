# CURRENT STATE — read this first

**This file is the project's living state-of-play.** It answers "where are we, what is done,
what is next" for a session that is starting cold — human or AI, on this machine or a new one.
It is **rewritten, not appended to** — unlike `docs/results/RESULTS_LOG.md` (append-only
history) and `docs/session-memory/` (one file per session, never edited). Those two are the
record; this is the snapshot.

**Last updated: 27 August 2026** (R1 ran twice: the first attempt was withdrawn — its masks were
misaligned by two data defects, both now fixed; the re-run PASSED the box bar and MISSED the
mask bar, so the bbox detector remains canonical. See §1a.)

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

**Stage 2 (FDI numbering) now ships a robustness-oriented head, v2.0** (DENTEX + Tufts),
adopted 26 Aug. It does **not** move the in-domain headline (46.6% vs 46.5% end-to-end — inside
the measured ~1-point noise floor) but gains **+21.5 points** on a second machine population
(Tufts). v1.0 (DENTEX-only) is retained and still hash-pinned, since every number published
before 26 Aug was measured on it. **R1 (detector retrain) remains the thing that actually moves
the headline number** — the head is already 91% on ground-truth boxes; the 67% detector recall
is the ceiling.

**C2 (external validation) has real numbers**: zero leakage against all internal corpora,
caries lesion agreement 22.6–43.3% across four Ningxia hospitals (DENTEX internal was 42.6%).
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

**The bar was not moved after seeing the number.** The bbox detector
`tooth-detector-a100-1024-v1.0` **remains canonical Stage-1**, and **R2 stays unwired**.

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
| **Lesion-localisation evaluator** — 42.6% agreement on DENTEX, no GPU | `scripts/eval/lesion_localization.py`, `RESULTS_LOG.md` 2026-08-25c |
| **C2 external validation on Ningxia** — 4 hospitals, zero leakage, first external numbers | `scripts/eval/ningxia_external.py`, `RESULTS_LOG.md` 2026-08-25d |
| **Deployment** — Streamlit app + Dockerfile, wrapping the pipeline unchanged | `app.py`, `Dockerfile`, `RESULTS_LOG.md` 2026-08-25f |
| **6 paper/review figures**, generated from saved artefacts only | `scripts/figures/make_paper_figures.py`, `docs/results/figures/paper/`, `RESULTS_LOG.md` 2026-08-25e |
| **Literature check on two comparison papers** (DPML, DentFound) — what they used, whether public, and independent confirmation that DPML also collapses out-of-domain (95.06 mAP own data → 61.83 on public DENTEX) | `RESULTS_LOG.md` 2026-08-26a |
| **Bone-loss binary + severity** trained (Tufts) | `models/03_.../run_summary.txt`, `models/04_.../severity_summary.txt` — **still untagged**, see §4 |
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

1. **R1 — YOLOv11l-seg retrain. ✅ DONE 27 Aug — but it did NOT become canonical.** Box bar
   passed (0.8100 test mAP@0.5 vs a 0.75 bar, and vs the bbox detector's 0.7824); **mask bar
   missed** (0.6383 vs 0.65). Per the pre-registration the bar was not moved and the bbox
   detector stays Stage-1 canonical; R2 stays unwired. `RESULTS_LOG.md` 2026-08-27b,
   `models/11_yolo_seg_tufts_r1/run_summary.txt`. **The open decision is whether the +2.76-point
   box gain justifies adopting it anyway** — a real methodology call, not a default.
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
4. **Bone loss is the standing open research problem, not just an admin item.** In-domain
   0.92 macro-F1 on Tufts; 0.7% firing on DENTEX; 0.8–5.4% affected-tooth sensitivity on
   Ningxia. Two independent external datasets now agree it collapses outside its training
   domain. No fix has been attempted yet. Worth scoping explicitly before or alongside R1 —
   detector and bone-loss are the two Tufts-trained stages and the two that misbehave
   elsewhere, likely one root cause. **The DENTEX+Tufts combined-training trick that fixed
   Stage 2's generalisation has not been tried here yet** — it is the most promising untried
   lever, since bone loss already has cross-corpus data available (Tufts trained, DENTEX/Ningxia
   measured) but has never been trained on more than one.
5. **T0.5 — the Mild severity class (n=6) decision.** Zero compute, zero blocker, untouched
   for two weeks. The cheapest open item in the project; there is no reason this stays open.
6. **Version-tag the bone-loss weights.** Stages 4a/4b are the only trained models without a
   tag now that both enumeration heads and the caries gate v3 are frozen. Trivial, just undone.
7. **Verify `docker build` actually completes.** Never run (daemon unavailable every session so
   far). Every static check passed (file paths, package list, CLI flag syntax verified by
   actually starting the process) but a real build has never happened. Do this before trusting
   the deployment demo for Review 1.
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
| **Bone-loss domain-shift fix — what approach?** Now backed by two independent external measurements. Options span the DENTEX+Tufts combined-training trick that worked for Stage 2 (untried here), R1 (shared Tufts-side fix), Ningxia-informed fine-tuning (needs care — Ningxia is locked, no tuning against it directly), or documenting it as a limitation rather than a fix. | Research direction, not a fact to look up |
| **A third public FDI corpus exists, unused.** DentFound trains tooth-ID on the Kaggle *Dual-labeled Panoramic Radiographs* set — 2,000 images, native FDI 11–48, larger than DENTEX or Tufts, no mirror to correct. | Whether to add it before or after R1 |
| **What else to use `DENTEX/disease/` for**, beyond the Stage-2 eval set (164 leak-free of 250) and the lesion-localisation source. The 91 `saglam` (healthy) teeth as a small real healthy class is still an open candidate use. | Scoping call |
| **Clinic data governance.** `index.csv` sits beside `images/` on a shared Drive, voiding the de-identification. Five actions in `clinical_dataset_provenance.md` §4a, all needing the Drive owner. | Not this repo's account |
| **Bone-loss weights have no version tag** — trivial to fix, listed here only so it doesn't get silently skipped again. | Just needs doing |
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

The only job that needs renting. Everything else runs locally on the M4 Pro (ResNet18 work at
~287 img/s on MPS — minutes per job).

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

**Budget reality:** at ₹140.94/hr a ₹900 balance is **6 h 23 min**. R1 is estimated at
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
| E2E instance / SSH keys | Account-level | No instance launched. Treat the `.pem` pasted on 20 Aug as compromised. |

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
| DENTEX (~14 GB) | ❌ | `data/dentex/` holds two JSON files only |
| Ningxia | ❌ | `data/ningxia/` holds `manifest.csv` only |
| Tufts bone-loss crops | ❌ | metadata CSVs only, no images |
| `_repo_archive/datasets_workspace/` | ⚠️ partial | Has the EDA/conversion notebooks (incl. `week1_tufts_eda_v2.ipynb`), **not** `Radiographs_rotated/`, `dataset/` or `outputs/` |
| Python env | ✅ | Python 3.11.9, **numpy 2.4.6**, scipy 1.17.1, sklearn 1.9.0, torch **2.13.0+cpu**, ultralytics 8.4.123. **65/65 tests pass, invariants clean** (some checks SKIP for want of DENTEX). CPU-only torch — no local GPU, and no MPS either, so even ResNet18 jobs are slow here. |

**Consequence for planning: R1 is the only GPU job this machine can currently feed.** Anything
touching caries, or the DENTEX+Tufts bone-loss experiment, needs DENTEX fetched first.

**On the `numpy<2` pin:** `requirements.txt` says numpy 2.x silently breaks `scipy.optimize`,
torch↔numpy and sklearn. That is true of the stack it was written against (torch 2.2.0 / scipy
1.12 / sklearn 1.4, built against numpy 1.x) — it is **not** true in general. Verified on
Windows: numpy 2.4.6 with scipy 1.17.1 / torch 2.13.0 runs `linear_sum_assignment` and
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
