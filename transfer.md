# CURRENT STATE — read this first

**This file is the project's living state-of-play.** It answers "where are we, what is done,
what is next" for anyone starting cold — human or AI, teammate or friend, on this machine or a
new one. It is **rewritten in place, not appended to** — unlike `docs/results/RESULTS_LOG.md`
(append-only history) and `docs/session-memory/` (one file per session, never edited). Those two
are the record of *how* we got here; this file is only ever the current truth. If something here
disagrees with the working tree, the working tree wins — verify before you rely on this.

**Last rewritten: 4 September 2026 (night), after a full consolidation pass.** Everything below
is current as of that timestamp. Older narrative (which machine had what on which August date,
council transcripts, since-corrected claims) has been moved out of this file into
`docs/results/RESULTS_LOG.md` and `docs/session-memory/`, where it belongs — this file no longer
carries superseded text next to its correction. GPU balance **₹1,148.78, nothing running, nothing
paused.**

**Targeted updates since:** 5 Sep — root `README.md` + `main.tex` reconciled with the Lever B
adoption and the 4 Sep param re-count (`docs/session-memory/2026-09-05-readme-maintex-stale-number-reconciliation.md`);
5 Sep — Tufts end-to-end FDI improvement options councilled, added to §3
(`docs/session-memory/2026-09-05b-tufts-fdi-improvement-council.md`); 6 Sep — council Option B
run, positional-feature-shift falsified as a lever, §3 updated
(`docs/session-memory/2026-09-06-tufts-fdi-option-b-diagnostic.md`, `RESULTS_LOG` 2026-09-06);
6 Sep — Option A pre-registration drafted as "Lever C"
(`outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md`,
`docs/session-memory/2026-09-06b-lever-c-preregistration-council.md`) — DRAFT, awaiting go/no-go;
6 Sep — next-steps council (`docs/session-memory/2026-09-06c-next-steps-council.md`): manuscript
declared feature-complete, §3 lead added; 6 Sep — `PROJECT_OVERVIEW.html` (a readable project
snapshot) placed at the repo root, reversing `2026-09-06d`'s "keep it out of git" — the repo is
private, so it is no more exposed than any other doc (`docs/session-memory/2026-09-06e`);
**6 Sep — Lever C was frozen (`e9270a3`), implemented, evaluated and is a NULL** (`RESULTS_LOG`
2026-09-06b, `docs/session-memory/2026-09-06f-lever-c-run-and-null.md`) — the default assignment
is unchanged and no current-best number moved; the two stale `docs/paper/` drafts now carry
superseded banners (§3 item 7 closed).
**10 Oct — state-review council** (`docs/session-memory/2026-10-10-state-review-council.md`):
the 6 Sep "feature-complete" verdict is withdrawn, §5's venue premise is corrected against the
venues' own pages, and a bone-loss audit is logged (`RESULTS_LOG` 2026-10-10). §1, §2.5, §2.7,
§3, §4, §5 and §8 were edited in place. Read the 10 Oct note below first.
**11 Oct — implementation-phase council**
(`docs/session-memory/2026-10-11-implementation-phase-council.md`): §3 now carries the ordered
list of what is left to implement before writing, and what was deferred or refused.
**11 Oct — items 2–5 of that list done** (`RESULTS_LOG` 2026-10-11,
`docs/session-memory/2026-10-11b-caries-interval-measurements.md`): three pre-registered
measurements for the caries tables. Results are in §3; §2.2 and §2.4 below still give the
published point values and should be read with them.
**11 Oct — item 6 done, implementation phase complete** (`RESULTS_LOG` 2026-10-11b,
`docs/session-memory/2026-10-11c-stage4-report-wording.md`): the report and the demo no longer
call Stage 4 a periodontal finding; report schema 1.2.
**11 Oct — FDI and lagging-metrics council** (`RESULTS_LOG` 2026-10-11c): no default changes;
what limits end-to-end FDI and what is parked is at the end of §3's implementation block.
**11 Oct, afternoon — the user decided to switch the Stage-1 detector; a second council planned
it** (`docs/session-memory/2026-10-11e-detector-switch-plan-council.md`, `RESULTS_LOG`
2026-10-11d). Planned, not started.

> **Windows clone, 6 Sep 2026 — the Tufts crop corpus was cut from the wrong frame, and is now
> rebuilt.** It scored 11.5% crop-level FDI-exact where the published number is 71.5%, with correct
> labels and wrong pixels, and it failed silently. Rebuilt from
> `data/tufts/ZIP/Radiographs_upright_fixed/`; the new manifest is byte-identical to the old one,
> the crops now score 73.2%, and Option B re-run on it reproduces the published result on both
> cohorts (`RESULTS_LOG` 2026-09-06c — diagnosis, 2026-09-06d — rebuild + reproduction). The
> defective build is archived, not deleted (`_repo_archive/tufts_enumeration_v1_wrongframe_2026-09-06/`).
> **Everything else on this clone was then audited (`RESULTS_LOG` 2026-09-06e,
> `scripts/eval/tufts_corpus_audit.py`) and is fine:** the bone-loss crops are in the correct
> frame (verified by pixels *and* by reproducing 2026-08-27u's table exactly), `dataset_seg_v2`
> (what `models/11` trained on) is aligned and byte-identical to `Radiographs_rotated_fixed`, and
> `severity_dataset` / `resampled_dataset` hold metadata only. **The three misaligned copies were then ARCHIVED**
> (`RESULTS_LOG` 2026-09-06f) — `Radiographs_rotated`, `Radiographs_upright` and `dataset_seg`
> now live under `_repo_archive/misaligned_tufts_frames_2026-09-06/`, so only correct data
> answers to those names and a stale reference fails loudly instead of reading wrong pixels.
> The two scripts that pointed at them are fixed — including `build_enumeration_crops.py`'s
> geometry-guard message, which named the *wrong* upright copy and fired exactly when someone
> already had a frame problem. **This thread is closed:** diagnosed (09-06c), repaired (09-06d),
> bounded (09-06e), guarded (09-06f). `scripts/eval/tufts_corpus_audit.py` re-checks the whole
> surface in one command.

> **7 Sep 2026 — the bone-loss crops were never lost, and the 0.923 reproduces.** The project
> Drive holds `resampled_dataset/{train,val}` — the original crops **including the 773 jittered
> ones** documented since 27 Aug as irreproducible. On the complete positive class the frozen
> model scores **49/59 = 0.8305 sensitivity, matching the documented figure to the digit**; the
> same 35 clean teeth score 0.829 on the original crops against 0.400 on August's rebuild, so the
> **rebuild** was defective, not the reported number. `RESULTS_LOG` 2026-09-07. Consequences:
> the three §9 items blocked on these crops (calibration, PR sweep, CIs) are **unblocked**, and
> the "irreproducible subset / selected maximum" limitation in `PAPER_MATERIAL.md` §8,
> `SUBMISSION_TODO.md` and the overview **must be corrected**. The branch's *generalisation*
> failure (2.4% external sensitivity) is a separate finding and is untouched.
> **Read this with the 10 Oct note below, which qualifies its last two sentences.**

> **10 Oct 2026 — a review council changed three things this file said.**
> **(1) The bone-loss in-domain figure is not a held-out estimate, and its label is not
> periodontal bone loss.** The run behind the shipped Stage-4a checkpoint used a crop-level 20%
> split: all 143 validation radiographs also supply training crops, and 46 of the 59 validation
> positives share their tooth with a training positive. A crop is "diseased" when it overlaps a
> Tufts expert *abnormality* mask; the 41 radiographs supplying every positive are described as
> apical lesions, sclerosis and cysts, and the three Tufts radiographs that are described as
> periodontal bone loss supply none. So 0.923 reproduces but is not an estimate, and the external
> collapse is at least partly a label mismatch. `RESULTS_LOG` 2026-10-10, `PAPER_MATERIAL.md`
> §8.28. **Do not finish the 565-crop pull or run calibration / PR / CIs on that set.**
> **(2) The venue premise was wrong** — JBHI caps at 14 pages and charges past 8, Computers in
> Biology and Medicine has lost Web of Science coverage, and ISBI 2027 is in-person only. The
> **department's publication guidelines**, received the same day, prefer a Scopus/WoS-indexed
> conference in India and require University approval before submitting to one abroad. §5.
> **(3) The manuscript is not feature-complete.** §3.
> Also checked on 10 Oct: the **Tufts Drive folder still opens without signing in**; nothing has
> been committed since 7 Sep; and the macOS clone holds all 1,000 original Tufts radiographs.

**Maintenance rule (CLAUDE.md rule 5): before any substantial session ends, update this file.**
A stale snapshot has cost this project real time more than once — see the pattern note in §4.

---

## 0. If you are new to this repo — read in this order

1. `CLAUDE.md` (loads automatically every session; the four house rules).
2. This file, §1–§4.
3. `docs/README.md` — the documentation map.
4. `docs/results/model_metrics.md` — current-best numbers, one table per model.
5. `docs/results/PAPER_MATERIAL.md` — the full technical story and honest limitations.
6. `paper/main.tex` (or `paper/main.pdf`) — the manuscript itself.

*For a readable one-page overview (what was done, results, limitations, what's next), open
`PROJECT_OVERVIEW.html` in a browser — but it is a **6 Sep 2026 snapshot, not kept in sync**;
the files above win where they disagree. Internal / pre-submission.*

**One-paragraph elevator pitch:** this is an OPG (panoramic dental X-ray) analysis pipeline —
YOLOv11l detects teeth, a ResNet18 head numbers them in FDI notation, and two more branches
classify caries and periodontal bone loss per tooth. The paper's actual finding is methodological,
not a leaderboard number: on the tooth-level metric this field mostly reports, an image-blind
constant (always name the same eight molars) ties-or-beats the full pipeline on most cohorts,
because caries is anatomically concentrated and that metric can't tell a real detector from a
population prior. The project's response was twofold — build the evaluation protocol that exposes
this (external validation, calibration, abstention, a VLM control) and, separately, find a
*reformulation* of the caries task that a blind constant genuinely cannot do (lesion localisation
instead of tooth classification) and that reformulation now decisively wins on 2 of 3 test
cohorts. Both threads are in the manuscript.

---

## 1. Where we are

The six-stage pipeline runs end to end on CPU alone (2.39 s/image), is deployed in a Streamlit +
Docker demo, and has been evaluated on **six independent cohorts**: DENTEX (development), four
Ningxia hospitals, and the CariesXrays benchmark. Every reported number traces to a saved
artefact — `scripts/verify_paper_numbers.py` asserts **127 manuscript claims** against those
artefacts and all pass; `pytest` is **174/174**; `verify_invariants.py` all hold. The manuscript
(`paper/main.tex`) compiles clean: **14 pages, 0 errors, 0 undefined references**, two small
pre-existing overfull hboxes (cosmetic, not content). Its core finding — a tooth-level score
cannot distinguish a real detector from an anatomical prior — held up under six cohorts, two
metric families, and a VLM control; the project's response to it (Lever B, below) is now folded
into the paper as a positive, pre-registered result. **What remains is still not experiments, but it is
more than paperwork (10 Oct): manuscript corrections, a decision on the bone-loss branch, a venue
commit with a real length cut, and the account-owner compliance actions. See §3.**

Full results ledger: **§2**. What's still open and who owns it: **§3–§4**. Publication target:
**§5**. Where each fact in the codebase lives: **§7**. Machine/environment setup for a fresh
clone: **§8**.

---

## 2. Complete results ledger

Every number below has a saved artefact behind it (path given or discoverable from
`docs/results/model_metrics.md` / `PAPER_MATERIAL.md`). This section is the "give me everything
that's been measured" answer — narrower questions should go to `model_metrics.md` (current-best
scoreboard) or `RESULTS_LOG.md` (full chronological history with every attempt, including the
failed ones).

### 2.1 Pipeline, as deployed today

| Stage | Model | Params | Checkpoint |
|---|---|---|---|
| 1 Detect | YOLOv11l-seg | 27.62 M | `models/11_yolo_seg_tufts_r1/best.pt` |
| 2 Number (FDI) | ResNet18 + 4 positional feats | 11.19 M | `models/10_fdi_head_dentex_tufts_v2/` |
| 3a Caries localisation **(default)** | YOLOv11l lesion detector | 25.31 M | `models/16_lever_b_pooled/.../best.pt` |
| 3a Caries gate **(retained variant, `--caries-method gate`)** | ResNet18 | 11.18 M | `models/09_caries_gate_v3/` |
| 3b Caries severity | ResNet18 | 11.18 M | `models/07_caries_cascade/` |
| 4a Bone-loss gate | ResNet18 | 11.18 M | `models/03_bone_loss_model_training_notebook_models/` |
| 4b Bone-loss severity | ResNet18 | 11.18 M | `models/04_bone_loss_severity_notebook_models/` |
| **Total (default)** | | **97.65 M** | |
| Total (gate variant) | | 83.52 M | |
| **Caries path only (1,2,3a,3b), default** | | **75.29 M** | |
| Caries path only, gate variant | | 61.16 M | |

Speed: **2.39 s/image on CPU**, no GPU needed for inference. Counted by
`scripts/count_model_params.py` (learnable parameters only, one stated rule for all seven
checkpoints — replaced three hardcoded literals that had drifted, 4 Sep).

### 2.2 The central finding — image-blind constant vs. the pipeline

**Development (DENTEX, 164 leak-free images, 477 carious teeth):**

| System | Precision | Recall | F1 |
|---|---|---|---|
| **Constant (never reads the image)** | 0.218 | 0.600 | **0.320** |
| Our pipeline | 0.235 | 0.390 | 0.294 |
| Qwen2.5-VL-32B, 0-shot | 0.250 | 0.243 | 0.246 |
| Qwen2.5-VL-7B, 0-shot | 0.248 | 0.107 | 0.149 |
| *Oracle constant (test-fitted)* | *0.245* | *0.505* | *0.330* |

Lesion localisation (same 164 images, 479 lesions, spatial-correspondence metric): constant
**0.489**, pipeline (gate) 0.443, all-teeth ceiling 0.722. Constant leads by **+4.6 pp**
[+0.6, +8.9].

**External (Ningxia, 4 hospitals, 337 images, 1,013 lesions, gate-based pipeline):**

| Hospital | Centre | Pipeline | Constant | Δ (pp) |
|---|---|---|---|---|
| test1 | cross | 0.288 | **0.446** | +15.8 |
| test2 | same as training | **0.513** | 0.407 | −10.6 |
| test3 | cross | 0.401 | 0.377 | −2.5 |
| test4 | cross | 0.419 | 0.323 | −9.7 |
| **Pooled** | | 0.408 | 0.399 | −0.9 [−4.9, +3.0] — indistinguishable |

**Second external benchmark (CariesXrays, AAAI 2024, 1,500 images, 3,421 lesions, gate-based
pipeline):** pipeline 0.309 vs. constant **0.561**, Δ **+25.2 pp** [+23.2, +27.3] — constant wins
outright. Mechanism: 72.0% of lesions sit on molars, 60.2% on exactly the eight constant codes.

**VLM content-free control:** shown a blank grey image or random noise (no anatomy at all).
Qwen-7B answers `26,36` to blank, noise, and a real radiograph identically. Qwen-32B correctly
says `NONE` to blank, but to noise answers `16,17,26,27,36,37,46,47` — exactly the constant's own
eight-molar set.

### 2.3 What the pipeline demonstrates that a constant cannot

**Tooth numbering (Stage 2, DENTEX 164 images / 936 teeth):**

| Metric | Value | 95% CI |
|---|---|---|
| Detection recall | 70.6% | [66.5, 74.6] |
| FDI exact, end-to-end | 58.3% | [53.9, 62.8] |
| FDI exact, of detected teeth | 82.6% | [79.1, 85.8] |

77.4% of remaining errors are benign off-by-one within the correct quadrant; only 2.4% of
detected teeth get a wrong-quadrant error. Tufts end-to-end (harder test, every tooth not just
pathological ones, 143 images): **64.8%**.

**Calibration (caries gate, 863 held-out test crops):** raw ECE 0.136 (systematically
overconfident) → isotonic regression **0.043**. Temperature scaling made it *worse* (0.152) —
the miscalibration is structural. Isotonic regression is applied to the reported confidence only
(would flip 155/863 = 18% of verdicts if applied at the decision threshold; AP cost
0.550→0.500).

**Selective prediction / abstention:** declining the least-confident quarter of cases raises
numbering accuracy 0.826→**0.885** (+5.91 pp) and caries-gate accuracy 0.797→**0.940**
(+14.25 pp). A shuffle control (breaks the confidence-correctness link) collapses both gains to
~0, proving the gain is real ranking, not just discarding items. Pre-registered threshold 0.30 →
90.8% coverage, 0.847 accuracy (within 0.2 pp of the empirical 90%-coverage point).

**Applies to numbering and the retained caries-gate variant only.** The adopted caries
lesion-detector (§2.4) has no calibrator and no abstention curve yet — see §3.

### 2.4 Lever B — the caries reformulation, ADOPTED as Stage 3a default

Five direct repairs to the caries gate (CLAHE, crop expansion, position-balanced sampling, a v4
retrain, threshold tuning) all failed, every CI spanning zero. Lever B changed the **task**
instead: a whole-image YOLOv11l lesion detector, trained on pooled CariesXrays (4,800 img) +
DENTEX-caries (650 img, replicated), evaluated by assigning each predicted lesion box to the
tooth it overlaps most (argmax containment). Pre-registered acceptance rule (frozen before any
arm trained, commit `ef3f453`): beat both the constant and the gate on ≥2 of 3 cohorts, at ≤1.5×
their teeth-flagged rate.

| Cohort | Gate | Constant | **Lesion detector** | Δ vs constant | Verdict |
|---|---|---|---|---|---|
| DENTEX$^d$ | 0.443 | 0.489 | 0.455 | −3.3 [−8.4, +1.3] | tie |
| CariesXrays$^d$ | 0.317 | 0.562 | **0.684** | **+12.2 [+10.1, +14.3]** | **win** |
| Ningxia$^e$ | 0.408 | 0.399 | **0.500** | **+10.2 [+6.3, +14.0]** | **win** |

*($^d$ development data for the detector; $^e$ genuinely external, never trained on.)* **2 of 3
→ Sec 6 met → adopted 4 Sep 2026** as the pipeline's Stage-3a default. Not a volume effect (flags
*fewer* teeth than every comparator on every cohort). A single-corpus (CariesXrays-only) variant
scores marginally higher on CariesXrays (0.694) but collapses to 0.086 on DENTEX and 0.240 on
Ningxia — the training *mixture*, not the architecture, is what transfers. The old gate is
retained, unchanged, via `--caries-method gate`, so every pre-4-Sep number stays reproducible.

### 2.5 Periodontal (bone-loss) branch — an honest negative result

| | In-domain (Tufts) | External (4 Ningxia hospitals) |
|---|---|---|
| Score | **0.923 macro-F1** (1,558 crops, 4% prevalence) | pooled **2.4%** [2.0, 2.9] sensitivity |

Per-site external: test1 2.4% [1.8,3.0], test2 1.4% [0.9,2.0], test3 5.6% [3.0,8.7], test4 4.6%
[2.7,6.6] (n=736 images total; CI closed 4 Sep, see §2.7). DENTEX firing rate 0.7%. Two
independent external datasets, different formats, agree it collapses. Cause isolated: a detector
swap that improved every other branch (+12.0 numbering, +7.7 caries) moved this branch by
nothing — the failure is inside the Stage-4a classifier, not shared upstream. Not fixed: the
lever that worked for numbering (train on a second corpus) doesn't exist here — DENTEX carries
no bone-loss labels. **The 0.923 figure is not a held-out estimate** (`RESULTS_LOG` 2026-10-10).
It is a selected maximum — best of 32 epochs on 59 positives — measured on a crop-level split
whose 143 radiographs all also supply training crops. It reproduces (49/59 on the recovered
crops, 7 Sep), and that is all that can be said for it. The "diseased" class is "overlaps a
Tufts expert abnormality mask" — apical lesions, sclerosis, cysts — not periodontal bone loss, so
the external collapse in the table above is at least partly a label mismatch rather than a
failure to transfer. Whether this branch stays in the paper is §3 item 5.

### 2.6 All levers attempted — outcomes

| Lever | What | Outcome |
|---|---|---|
| 1 | Multi-corpus detector (Tufts+DENTEX) | FDI e2e 58.4%→93.4% in-domain (+34.9pp); Tufts guard fails 0.810→0.647 → **ABLATION** |
| 2 | Standalone CariesXrays lesion detector, benchmark row | COCO AP 0.482/AP50 0.845/AP75 0.500 — level with FPCL (0.482/0.841/0.506), ~6 AP above their strongest baseline → **benchmark row in Related Work**, not a pipeline component. Its `best.pt` = Lever B's single-corpus arm. |
| A | Multi-corpus detector, 4 corpora, balanced | DENTEX e2e 0.584→0.928 (+34.4pp); Guard 1 (external caries) passes +9.1pp; Guard 2 (Tufts box mAP) fails 0.724→0.585 → **ABLATION**, 2/3. Diagnosed as capacity dilution, not a bug. |
| A2 | Frozen-backbone Tufts head fine-tune of Lever A's arm | DENTEX e2e +29.3pp; Guard 1 +8.6pp; Guard 2 fails (0.585→0.593, val recovered, test didn't) → **ABLATION** |
| **B** | Caries lesion detector (reformulated task) | 2 of 3 cohorts pass → **ADOPTED**, see §2.4 |
| D | Bone-loss second corpus (BRAR) | Opt-in only, not started, no pre-registration |
| C, E | Caries gate v5; bigger detector arch | **Skipped** — base-rate-limited by construction / marginal expected gain |

### 2.7 Today's session (4 Sep, night) — five items closed

Full detail: `RESULTS_LOG.md` 2026-09-04{i,j,k,l}; `docs/session-memory/2026-09-04{e,f,g}-*.md`.

1. **`main.tex` reconciled with the Lever B adoption** — Table I reports both Stage-3a paths;
   new `sec:lesiondet` (System) and `sec:leverb` (Results); Discussion reframed (the paper's
   claim that no *architectural* work raises the ceiling is confirmed, not falsified, because
   Lever B changed the *task*). Found and fixed 3 pre-existing defects: a mis-rounded headline
   number (0.488→0.489, one digit, everywhere it appeared), a parameter table mixing two
   counting conventions, and a live leakage hazard in an eval script (fixed before it produced a
   number).
2. **Calibration/abstention scoped to the gate variant** — the adopted lesion detector has no
   calibrator yet; stated as the manuscript's new first Limitations item rather than left
   implied.
3. **Lever 2 benchmark row added to Related Work** — re-verifying its FPCL comparison table
   against the actual AAAI PDF (as its own pre-condition required) caught two transcription
   errors: a non-existent "DINO" baseline row, and a margin overstated as ~8 AP that is really
   ~6 once the omitted Conditional-DETR row is restored.
4. **Bibliography sweep** — found and fixed 5 real defects (2 entries' URLs pointed at entirely
   different Nature articles; 2 had a wrong conference name recorded, caught via Crossref
   author-list cross-checking); added 9 missing DOIs and one missing citation (the Ningxia
   source paper was never cited despite its own README requesting it). Figure-redistribution
   audit: clean, all 5 manuscript figures are derived charts, none reproduces raw pixels.
   Licences recorded: DENTEX CC-BY-NC-SA-4.0 (compliant); Ningxia informal/no formal licence
   (compliant, weaker terms).
5. **Two of the three remaining CI-coverage gaps closed.** Ningxia periodontitis (§2.5) — an
   eval script was computing per-image counts and discarding them; fixed, re-ran, bootstrapped.
   Stage-1 detector — three attempts at bootstrapping the published Box mAP@0.5 (0.8100) from
   scratch failed to converge (0.593→0.701→0.672, the last "correct" fix moving *away* from the
   target); pivoted to a different, correctly-bootstrappable statistic instead: **detection
   recall at the deployed confidence, 69.1% [65.5, 72.6]**, n=150. This also resolved the
   long-standing `590.JPG`/`591.JPG` train-test leak question — its effect on this statistic is
   −0.15 pp, within noise, so "document, don't re-measure" is the closed decision.
   **The bone-loss classifiers' CI was recorded here as blocked. It is not blocked, and it is no
   longer worth computing:** the crops were recovered on 7 Sep, the original radiographs are on
   the macOS clone, and the 10 Oct audit shows that validation set shares every radiograph with
   training (header note, §2.5).

Checks after all of the above: `verify_paper_numbers.py` **127/127**, `pytest` **174/174**,
`audit_citations.py` 30 commands / 27 keys all resolve, manuscript **14 pages**, 0 errors, 0
undefined refs.

---

## 3. What is next

**Track A (manuscript + compliance) is the critical path and wins any time conflict.** Nothing
in Track B (further levers) is queued or approved — do not start GPU work without a fresh
pre-registration and explicit go-ahead.

**The manuscript is not feature-complete.** A 10 Oct council
(`docs/session-memory/2026-10-10-state-review-council.md`) withdrew the 6 Sep verdict that it
was. The manuscript compiles and its 127 numbers check, but it states a split that one branch did
not use, names that branch for a disease its labels do not contain, carries none of the mandatory
statements, and is 14 pages against venues that cap or charge. **None of that needs a new
experiment.** It needs decisions and edits — items 1–5 and 9–10 below. The single
highest-leverage action is the one the 6 Sep council named and nobody has scheduled: a
**one-hour mentor meeting** on the venue, the authors, the bone-loss branch and the two live
compliance breaches (§4). Nothing has been committed to this repository since 7 Sep.

*"You" in the table below is the repo owner; those rows were written on his machine.*

| # | Item | Owner | Status |
|---|---|---|---|
| 1 | Venue commit. Recommendation as of 10 Oct, after the department guidelines (§5): **a conference in India first** — IEEE CONECCT 2027 (15 Dec), or NCC 2027 (16 Oct) only if everyone commits by 12 Oct — **then the journal as its extended version**; ISBI 2027 dropped | You / mentor | **Open** — asked for on 6 Sep, still not done. Every venue checked needs a length cut; the conference route needs six pages |
| 2 | Authors and affiliations, still `Unknown` in `main.tex` | You | **Open** |
| 3 | Title / thesis / whether the abstract's "four things a constant cannot do" becomes five | You | **Open, deliberately untouched** — Lever B's localisation result arguably earns a fifth axis, but that's a thesis-scope call, not an engineering one |
| 4 | Four compliance blockers (§4) | Account owner | **Open**, two are live breaches |
| 5 | Bone-loss branch: cut it from the manuscript, or keep it re-described (§2.5, `PAPER_MATERIAL.md` §8.28) | You / mentor | **Open — a decision, 10 Oct.** The CI gap this row used to track is moot: that validation set shares every radiograph with training |
| 6 | Docker rebuild (image predates the Lever B caries-method wiring) | Anyone | **Done 7 Sep 2026** on the Windows machine, built and smoke-tested (`RESULTS_LOG` 2026-09-07c) |
| 7 | Retire or mark-superseded `docs/paper/{manuscript.md,draft_spine.md}` | Anyone | **Done 6 Sep 2026** — both now open with a banner naming their stale numbers (gate-only Stage 3a, 0.488, 61.2 M) and pointing at `paper/main.tex`; kept per rule 3. `docs/README.md` says quote `main.tex`, never these |
| 8 | `docs/research/{PUBLICATION_TODO.md,MASTER_PLAN_2026H2.md}` | Anyone | Not re-synced with this file's current state — their own status blocks predate Lever B entirely; treat this file as authoritative until they're refreshed |
| 9 | Correct `main.tex`: the three false bone-loss statements (image-level splits, 700/150/150 as the bone-loss split, "domain shift"); add the mandatory statements — ethics, data and code availability, funding, conflict of interest, contributions, acknowledgments with the AI-use disclosure IEEE requires | Owner — needs LaTeX, which the macOS clone does not have | **Open, blocking (10 Oct).** Line-by-line list in the 10 Oct session file |
| 10 | Reviewer-risk edits that need no experiment: the Conclusion never mentions Lever B; "the radiograph is never read" is untrue of the localisation tables, where the constant's teeth are placed with the pipeline's own boxes and numbering; the claim that none of the 49 surveyed papers reports an image-blind baseline was never counted | Owner | **Open (10 Oct)** |
| 11 | Two analyses from saved artefacts, no inference: per-hospital paired intervals for Lever B (point estimates beat the constant at all four hospitals; test1 by 1.6 pp), and an interval on the headline F1 gap (0.320 vs 0.294) | Anyone with the repo | **Open, small (10 Oct)** |
| 12 | Refresh `docs/paper/SUBMISSION_TODO.md` — status date 28 Aug, stale in both directions | Anyone | **Open** — corrective banner added 10 Oct, list not rewritten |

**Implementation phase — order set by an 11 Oct council
(`docs/session-memory/2026-10-11-implementation-phase-council.md`). Time box: two working days on
the macOS clone, then write.** Nothing here needs a GPU, the Windows machine or the mentor.

| Order | Item | Status |
|---|---|---|
| 1 | Commit the 10 Oct documentation edits | **Done** (`f323aba`) |
| 2 | One pre-registration covering items 3–5, committed before any of them runs | **Done** — `outputs/caries_intervals/PRE_REGISTRATION.md`, frozen `1fd20b5`, Amendment 1 `33c1340` |
| 3 | Interval on the headline F1 gap, constant vs gate pipeline, 164 images | **Done 11 Oct.** +2.61 pp [−0.64, +5.99]: **not separable**. "The constant scored highest" must be reworded |
| 4 | Per-hospital intervals on Ningxia, lesion detector vs constant. Estimation, no bar | **Done 11 Oct.** Separated at test2, test3, test4; **not at test1** (+1.58 pp [−4.43, +7.74]). "Replicates" is a pooled statement |
| 5 | The adopted lesion detector's own score on the headline FDI-set F1, run once | **Done 11 Oct.** F1 **0.376** vs the constant's 0.320: **+5.64 pp [+1.74, +9.47]**. Development data, one run, measured on macOS |
| 6 | Stage-4 wording in the report, the overlay and the app: an abnormality-proximity flag, not a periodontal finding. Additive, schema 1.2, field names unchanged | **Done 11 Oct** (`RESULTS_LOG` 2026-10-11b). Predictions identical before and after; app checked through an upload. **The Docker image from 7 Sep still carries the old wording — rebuild it on the machine with Docker; a stale container emits `opg-report/1.1`** |

**The implementation phase is complete as of 11 Oct.** What is left is writing and decisions:
items 1–5 and 9–10 of the table above, and the six-page caries-only cut (§5).

**End-to-end FDI (58.3% DENTEX, 64.8% Tufts) — what limits it and what is parked.** Councilled
11 Oct (`docs/session-memory/2026-10-11d-fdi-and-lagging-metrics-council.md`, `RESULTS_LOG`
2026-10-11c).

- **DENTEX is detector-bound.** 275 of 936 teeth are never detected, and about two thirds of the
  115 wrong codes also come from the detector's boxes (115 → 41 on the same teeth with the
  multi-corpus detector's boxes, same head). A multi-corpus detector reaches 92.8% and already
  exists (`models/15` arm3c). The morning council advised leaving it an ablation. **On the
  afternoon of 11 Oct the user decided to make it the Stage-1 default anyway**, knowing that it
  overrides two pre-registered verdicts and re-measures every pipeline number. **Nothing has
  run and `DEF_DETECTOR` is still `models/11`.** The agreed plan is in
  `docs/session-memory/2026-10-11e-detector-switch-plan-council.md`: safety fixes first, then a
  signed override record and a pre-registration, then about 34 runs with a same-machine
  `models/11` control before each, and the one-line default change last. The repo owner and the
  mentor have not been consulted; nothing is to be pushed until they are.
  **Status, 11 Oct evening:** Phase 1 is done — a report's detector tag and accuracy now follow
  the weights loaded, and arm3c is hash-pinned (`RESULTS_LOG` 2026-10-11e). Phase 2 is written —
  the decision record (`RESULTS_LOG` 2026-10-11f) and
  `outputs/stage1_switch/PRE_REGISTRATION.md`. **The matrix has not been run and the default is
  still `models/11`.** Next: commit both, then run the eight rows, Ningxia last.
- **The same loss caps the caries score.** The deployed front end delivers 288 of 477 carious
  teeth under the right code, a recall ceiling of 0.604; arm3c's would be 0.950.
- **Now, writing only:** say in the manuscript that numbering is detection-bound and name the
  multi-corpus ablation as the measured ceiling. `main.tex` does not mention it at all.
- **One optional measurement, about a day, needs its own pre-registration:** the lesion detector
  on the arm3c front end, DENTEX only, once, estimation only, default unchanged. Two council
  seats said now, one said after submission.
- **After submission:** a reject option in the one-to-one assignment, tuned on Tufts validation
  only; then, and only by a new pre-registered decision, whether the default detector changes.
- **Never for this paper:** a new position-digit model or a retrained detector.

**What items 3–5 found (`RESULTS_LOG` 2026-10-11, `PAPER_MATERIAL.md` §8.29).** The constant
and the *gate* pipeline cannot be told apart on F1. The *adopted* lesion detector beats the
constant on that same metric, on DENTEX, and is separated from it at three of the four Ningxia
hospitals on lesion agreement. So the floor the paper is about is one its own shipped system now
clears — on development data and pooled external data, not everywhere. How the thesis is worded
after that is the authors' decision. One more thing surfaced: the gate pipeline scores 0.294 on
the Windows machine and 0.300 on macOS with identical code, so Table I's two pipeline rows
should come from one machine.

Put new artefacts under `outputs/lever_b_eval/` and `outputs/c1_vlm/`, which are already
whitelisted in `.gitignore`; anything elsewhere under `outputs/` is ignored and the paper-number
verifier would then fail on the other machine.

**Deferred until after submission:** a leak-free in-domain score of the frozen Stage 4a on the
roughly 290 never-used Tufts radiographs with a non-empty expert mask (journal and capstone value
only); an invariant that training and validation manifests share no radiograph; the `--tag` /
`--out` fix in `ningxia_external.py`, before the next Ningxia run. **Refused:** retraining
Stage 4 on a clean split (it would validate the wrong label cleanly, and re-pin hashes, parameter
counts and the Docker image); the DENTEX periapical test; a new periodontal corpus; a
lesion-detector calibration curve on DENTEX (not well-defined there — unmatched flags are not
known false positives); any numbering or detector work.

**Engineering follow-ups, all small, none blocking:** fold the (now-closed) bibliography and
periodontitis-CI work into any downstream summary docs that quote the old numbers; decide
whether to actually *measure* (not just scope in writing) calibration/abstention for the new
caries detector — needs its own pre-registration since the 0.30 threshold was frozen against the
gate's curve, not this one.

**Tufts end-to-end FDI (64.8% e2e / 78.6% of detected, `RESULTS_LOG` 2026-09-04d) — CLOSED for
this submission.** Two pre-registered, zero-GPU attempts were run and both came back negative,
which between them bound the problem:

- **Option B** (6 Sep, `RESULTS_LOG` 2026-09-06) falsified the positional-feature covariate
  shift: mapping every Tufts positional feature onto the DENTEX-train distribution moves
  crop-level FDI-exact by **+0.1 pp**.
- **Lever C** (6 Sep, `RESULTS_LOG` 2026-09-06b,
  `outputs/lever_C_fdi_structural_postproc/`) — the ATGI-style arch-order post-processor,
  frozen at `e9270a3` *before* any code, run at `801d12e` — is a **null**: Tufts
  FDI-exact-of-detected **+0.29 pp [−0.07, +0.69]** (C-dp) against a **+2.0 pp lower-bound**
  bar, DENTEX slightly down. **Verdict: do not adopt.** The default stays `hungarian`; both arms
  are retained behind `--assignment` and reported as an ablation. The control arm reproduces the
  published Stage-2 numbers, which validates the harness. Measured reason it is small: 72.6% of
  detections are anchors and immovable (τ = 0.30, inherited so the lever adds no tunable, is
  permissive enough to anchor teeth the head is confidently *wrong* about), 13.4% sit in
  over-full quadrant groups, 13.9% are movable at all — and where the assumption does hold, the
  contiguous-arch stratum, it gains **+2.36 pp** on 9.5% of the cohort.

**What that leaves:** the **image-derived position digit** (73.5% on Tufts GT crops vs DENTEX
91.9%) — now the remaining explanation by elimination rather than by assertion. Attacking it is
**Option E** (higher-resolution crops, wider context, or a spatial-prior transformer;
post-submission, needs its own pre-registration and go-ahead). **Option D** (more FDI corpora)
stays weakened. Nothing here is queued. Zero-effort and unchanged: lead the Tufts numbering
discussion with **of-detected 78.6%** and present 64.8% e2e as detection-bound — and note that
`main.tex` does not currently state the Tufts number at all, so nothing in the manuscript
depends on this.

---

## 4. Decisions pending — do not default into these silently

| Decision | Why it needs a human |
|---|---|
| **⚠️ Tufts licence breach, live — re-checked 10 Oct 2026: the folder still opens without signing in.** A Drive folder holding the raw release was found browsable without signing in (first recorded 26 Aug); the licence forbids exactly this. Restrict it — do not delete it; keep Tufts local-only; share the release *form*, not the files. Anything still needed from it should be fetched by a signed-in, named account after it is restricted. | Account owner's action; real submission risk |
| **⚠️ SDH clinic data de-identification is void, live, and confirmed present on two copies.** `metadata/index.csv` sits beside `images/` on both the shared Drive tree *and* the local `D:\SDH dataset\dataset\` copy on this machine (re-checked directly 4 Sep). No clinic-derived number appears anywhere in this project, and none should until this is fixed. | Drive/account owner — this is clinical data governance, not a file-move I should do unilaterally |
| **IRB paperwork** | Not started. Longest lead time of anything open. Needed only if clinic data is ever used in a result. |
| **Is the Tufts mirror-numbering finding novel?** Not established — the source paper (Panetta et al., IEEE JBHI 2022) is paywalled and unread. | Needs someone with IEEE Xplore access; a 5-minute read, not a research task |
| **Real Tufts pixels are embedded in 7 tracked notebooks on `origin/main`.** Deferred — repo is confirmed private, so this is not an active leak, but must be resolved (strip outputs, or a coordinated history rewrite) before this repo or any fork is ever made public. | Deferred by explicit prior decision; revisit before public release |
| **`models/11` (53 MB) is committed to git, over the ~50 MB rule-4 line, and git history keeps it forever.** Deferred by the 3 Sep handoff decision (needed for a working fresh-clone demo). To undo: `git rm --cached`, restore `.gitignore`, re-host on Drive. | Revisit before any public release |
| **What else to use `DENTEX/disease/`'s 91 healthy ("saglam") teeth for**, beyond the current Stage-2 eval set and lesion-localisation source | Scoping call, not urgent |

**Do NOT do:** train on or tune against Ningxia — it is this paper's single strongest piece of
evidence specifically because it is untouched. No further GPU spend without a written
pre-registration, same discipline as every lever above. Added 10 Oct: do not finish the 565-crop
bone-loss pull through the public link, do not run calibration / PR / CIs on that validation set
(§2.5), and do not write a 4-page ISBI draft "just in case" (§5).

---

## 5. Publication target and grading criteria

| Grade | Requirement |
|---|---|
| **S** | Journal, or a conference in its 10th edition or later |
| **A** | Mid-tier conference, 5th–10th edition |
| **B** | Newer/lower-tier conference, 1st–5th edition |
| **C** | No publication secured |

### Department publication guidelines — received 10 Oct 2026

Sent to all capstone students at the direction of the Chairperson, CSE Department. Recorded here
because they constrain the venue as much as the grade table does.

1. **High-rated conferences.** Identify and publish in high-rated, reputed conferences relevant
   to the area of research.
2. **Conferences in India are preferred** — ones indexed in Scopus and/or Web of Science.
3. **A conference outside India needs prior University approval** — before the paper is
   submitted and before any financial commitment is made.
4. **Reimbursement.** A publication presented at a conference that meets the criteria may be
   reimbursed, subject to University rules, approval procedures and eligibility.
5. **Verify the indexing.** Guides and students must check the proceedings' current Scopus / WoS
   status before submitting; it can differ between editions of the same conference.

Obtain the necessary approvals in advance.

**What this changes.** The guidelines speak only of conferences. The grade table still lists a
journal as S and nothing in the guidelines withdraws that — but whether a journal paper still
counts, and whether it can be reimbursed, is a question for the mentor, not an assumption. A
conference held in India, in its 10th edition or later, with indexed proceedings, satisfies both
documents at once.

**Current decision (2 Sep 2026 council, supersedes an earlier 1 Sep ISBI-primary framing):**
**journal primary. No venue has been committed since.** That council named IEEE JBHI or
Computers in Biology and Medicine as "both S-grade, no page limit", with an ISBI 2027 short paper
"in parallel". Checked on 10 Oct 2026 against the venues' own pages, those premises do not hold:

| Venue | What is true (checked 10 Oct 2026) |
|---|---|
| IEEE JBHI | **14-page limit**, supplementary material included. Mandatory charges past 8 pages: $250 a page for pages 9–10, $350 a page from page 11. The current 14 pages would cost **$1,900**; 8 pages cost nothing. Needs the journal class — `main.tex` is in conference class. |
| Computers in Biology and Medicine | On hold with Clarivate since April 2024; **Web of Science coverage discontinued 17 Nov 2025**. Reported still in Scopus by a third-party post of 6 Jan 2026 — Scopus's own source list was not checked. Usable only if the college accepts Scopus without SCI(E). |
| ISBI 2027 | Deadline **26 Oct 2026**. All technical content in four pages; a fifth ($200) for ethics, acknowledgments and references only. **In person only, Lausanne, 25–28 May 2027 — a paper not presented in person is withdrawn from the proceedings.** It must not be substantially similar to anything published or accepted elsewhere, so it cannot run "in parallel" with the journal paper. **Outside India, so it also needs University approval before submission** (guideline 3). |
| NCC 2027 — National Conference on Communications | **33rd edition. IISc Bengaluru, 17–20 Feb 2027.** Deadline **16 Oct 2026**; notification 24 Dec 2026; camera-ready 8 Jan 2027. Six pages, IEEE conference format, **double-blind**. Technical co-sponsors: IEEE ComSoc, IEEE SPS, IEEE Bangalore Section. Topics include image, biomedical and machine-learning signal processing, so the paper is in scope — but this is a communications conference. The page does not state where the proceedings are indexed: verify (guideline 5). |
| IEEE CONECCT 2027 | **13th edition. Bengaluru, 29–31 Jul 2027.** The home-page timeline reads: paper deadline **15 Dec 2026**, notification 15 Feb 2027. The call-for-papers page was not live on 10 Oct, so confirm the dates and the page limit when it opens. The IEEE Bangalore Section's flagship conference. |

**Recommendation as of 10 Oct, for the mentor to accept or overrule.** The council that morning
said journal first. The department guidelines arrived afterwards, and this paragraph is the
session chair's update to that advice; it was not put back to a council. Make a conference in
India the first submission and the journal its extended version:

1. **Conference paper, six pages, caries only** — the constant baseline, the ladder, the three
   cohorts and Lever B. That cut also takes the bone-loss branch out of the paper, which would
   settle §3 item 5 for this submission. **IEEE CONECCT 2027** (15 Dec) is the realistic target.
   **NCC 2027** (16 Oct) decides two months sooner and is the older venue, but it is six days
   away: attempt it only if the mentor and both authors commit by 12 Oct.
2. **Journal afterwards** — the extended version, carrying what six pages leave out and
   disclosed as an extension of the conference paper. About 8 pages at JBHI costs nothing.
   *Oral Radiology* and *Dentomaxillofacial Radiology* were proposed as cheaper first choices;
   their limits and indexing were **not verified**.
3. **ISBI 2027: drop.** Outside India, in person only, and sixteen days from a deadline that now
   needs University approval first.

Four questions decide the rest and only the mentor can answer them: by what date must the
publication be secured, and does that mean submitted or accepted; does a journal paper still
count under the new guidelines; Scopus or SCI(E); and what the reimbursement procedure needs
before anyone registers.

**Why journal over ISBI-primary:** the manuscript's spine is the evaluation-protocol
contribution (only 2 of 49 task-relevant papers this project surveyed validate externally) with
the lever fixes folded in as positive systems results — not a pivot to a pure systems paper. A
journal gives that spine more room than ISBI's four pages, though not unlimited room (table
above). Honest grade expectation: journal accept → S. The binding risks to that outcome are the
manuscript corrections in §3 and the compliance blockers in §4, not any remaining experiment.

---

## 6. GPU — status and runbook pointer

**Nothing running, nothing paused, as of 4 Sep night.** Balance ₹1,148.78. Every past rental was
destroyed immediately after a sha256-verified download; none is idle-billing.

Full command-by-command runbook: `docs/research/GPU_SETUP.md`. The two lessons worth repeating
here because they cost real money to learn:

1. **`tar` a dataset to one file before uploading.** Per-file upload (`jl upload` of thousands of
   small files) is the actual bottleneck, not GPU time. sha256-verify both ends after transfer.
2. **Verify data geometry against an independent reference *before* renting, and again *on the
   rented box* after upload.** Two separate incidents this project has hit (a misaligned-mask
   run, a 90°-rotated-frame ground-truth mismatch) both produced smoothly-falling loss on
   garbage data and errored nowhere — the geometry check is the only thing that catches this
   class of bug, and it has to run after the upload, not just locally.

No lever is currently pre-registered or approved to run. Do not rent anything without both.

---

## 7. Where the documentation lives

| Question | File |
|---|---|
| Current-best numbers, one table per model | `docs/results/model_metrics.md` |
| Full technical story + honest limitations | `docs/results/PAPER_MATERIAL.md` |
| What happened, when, and why — every attempt, including failures (append-only) | `docs/results/RESULTS_LOG.md` |
| Narrative of each session, one file each | `docs/session-memory/` (newest file) |
| Documentation layout | `docs/README.md` |
| Pipeline code, and the crop contracts easy to get wrong | `src/README.md` |
| Entry points, how to run things, the deployment app | `scripts/README.md`, `scripts/{yolo,dentex,tufts,eval}/README.md` |
| Tufts as a second FDI corpus — read before touching its numbering (mirrored) | `scripts/tufts/README.md` |
| Datasets: what is where, what is usable | `data/README.md` |
| Weights, version tags, which checkpoint is the current default | `models/README.md` |
| Google Drive links, checkpoint restore steps, the Tufts licence warning | `docs/EXTERNAL_DRIVE.md` |
| Paper/review figures | `docs/results/figures/paper/`, `paper/fig_*.png` |
| Publication target and grading criteria | this file, §5 |

**Two editing gotchas:** line endings are not uniform across the repo (`transfer.md`,
`.gitignore`, `models/README.md`, everything under `docs/results/` are CRLF; scripts,
`docs/session-memory/*` and most other READMEs are LF) — edit in place, never run a blanket
EOL-normaliser. Before pushing, check `git diff --diff-filter=D --name-only origin/main..HEAD` —
a `git rm --cached` of a tracked artefact silently deletes it from a collaborator's tree on
their next pull.

---

## 8. Machine state and fresh-clone setup

**As of 4 Sep 2026, this (the Windows) machine has everything needed to reproduce every current
result** — DENTEX, Tufts, Ningxia (found at `D:\nangxia_dataset`, no copy needed), CariesXrays,
and every checkpoint except the two still noted below. The macOS machine (the collaborator's)
independently has the same DENTEX/Tufts/Ningxia data and produced the Phase 0 / Lever A2 /
Tufts-e2e work merged into this history; treat both as caught up unless a specific file check
says otherwise.

### Checklist: does a fresh clone actually run the pipeline

1. `git clone`, `pip install -r requirements.txt` (venv recommended; Python 3.13 confirmed
   working with numpy 2.x — see the numpy note below).
2. Fetch the Drive-only checkpoints per `docs/EXTERNAL_DRIVE.md` (see table below for which).
3. `python -m pytest tests/ -q` → should read **174 passed**.
4. `python scripts/eval/verify_invariants.py` → should read **all invariants hold**.
5. `python scripts/run_inference.py --image <any_opg.png> --output report.json` → should
   complete and name `models/16_lever_b_pooled` (Stage 3a default) and
   `models/10_fdi_head_dentex_tufts_v2` (Stage 2 default) in the report's `models` block.

If any step fails, the error names the missing file — cross-check against
`docs/EXTERNAL_DRIVE.md`'s checkpoint table before assuming something is actually lost; this
project has twice declared a file "missing" when it was only on a different drive letter or a
different machine than the one searched.

### What still needs a manual Drive fetch (everything else is in git)

| Checkpoint | Size | Why not in git |
|---|---|---|
| `models/09_caries_gate_v3/caries_gate_v3.pth` | 43 MB | Under the 50 MB line but was never migrated; Drive-only |
| Nothing else — `models/09`, `10`, `11`, `12`, `12a`, `14`, `16` are all committed | — | `models/11` and `models/16` exceed the 50 MB rule-4 line via explicit, recorded `.gitignore` exceptions (needed for a working fresh-clone demo; revisit before any public release, §4) |

### Raw datasets (not needed for inference, only for re-running training/eval)

| Dataset | Location | Note |
|---|---|---|
| DENTEX (full release + the subsets this repo uses) | `~/Downloads/Capstone/DENTEX/` (macOS) / `data/tufts/ZIP/...`-equivalent path (Windows) | Complete on both machines; subset map in `data/README.md` |
| Tufts raw + rotated radiographs, frozen split | `data/tufts/ZIP/`, `outputs/eda_tufts/split_v1.csv` | Split is code-derived (`scripts/tufts/regenerate_split_v1.py`), reproduces byte-for-byte. Contains one documented leak (`590.JPG`/`591.JPG`) — resolved, see §2.7. **The original un-rotated radiographs are on the macOS clone** — all 1,000, 1615×840, at `_repo_archive/datasets_workspace/Radiographs/` (verified 10 Oct). This row used to say they were "confirmed absent from every machine checked"; the Mac had not been checked. |
| **Ningxia** | `D:\nangxia_dataset` (Windows, found 4 Sep, used in place) / `~/Downloads/Capstone/ningxia_local/` (macOS) | Locked external test data. **Never train or tune against it.** |
| CariesXrays (~2 GB) | `data/cariesxrays_det/`-adjacent raw source | AAAI 2024. No LICENSE file ships with it; used under citation, recorded in `main.tex`. |
| Clinic (SDH) data, 3,219 images (3,213 usable) | `D:\SDH dataset\dataset\` | **Contributes to no result. De-identification is void for this copy** (§4) — do not use until fixed. |
| Kaggle dual-labelled (3rd FDI corpus) | `data/kaggle_dual/` | 499 usable images, ablation only (`models/12`) |

### Environment notes

- **numpy<2 pin in `requirements.txt` is stack-specific, not universal.** Verified working on
  Python 3.13.7 / numpy 2.5.2 / scipy 1.18.1 / torch 2.8.0+cpu — `linear_sum_assignment` (the
  Hungarian FDI assignment) and torch↔numpy conversion both correct, full suite green. The pin
  protects older stacks (numpy 1.x-built torch/scipy); on a from-scratch 3.13 install there is no
  numpy 1.x wheel anyway, so numpy 2.x is what you'll get regardless.
- **Docker:** Desktop is installed on this machine; its daemon was not running when last checked
  (4 Sep). `docker build` has never actually executed end-to-end here — treat "verified" claims
  from before that check with caution until it's actually run once.
- **LaTeX:** MiKTeX 25.12 on Windows. `latexmk` is installed but cannot run (no Perl script
  engine on this machine) — use `pdflatex -interaction=nonstopmode main.tex`, twice, instead.

---

## 9. History

Everything before this rewrite — the day-by-day narrative, the council transcripts, the
machine-handoff incidents, every superseded number and its correction — lives in
`docs/results/RESULTS_LOG.md` (chronological, searchable by date) and `docs/session-memory/`
(one file per session). Nothing here duplicates it; if you need "what happened on 26 August" or
"why did we reject Framing B," those are the files to open. This file only ever answers "what is
true right now."
