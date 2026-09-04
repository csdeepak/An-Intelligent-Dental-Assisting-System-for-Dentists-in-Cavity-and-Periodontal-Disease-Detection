# CURRENT STATE — read this first

**This file is the project's living state-of-play.** It answers "where are we, what is done,
what is next" for a session that is starting cold — human or AI, on this machine or a new one.
It is **rewritten, not appended to** — unlike `docs/results/RESULTS_LOG.md` (append-only
history) and `docs/session-memory/` (one file per session, never edited). Those two are the
record; this is the snapshot.

**Last updated: 4 September 2026. Nothing is running; GPU balance ₹1,184.84 (Lever B cost ₹546.93). Instance 496516 destroyed, verified downloaded first.** **Lever B is DONE building and evaluating — VERDICT PENDING NINGXIA.** Pre-reg frozen same day (4 defects fixed pre-freeze — the CariesXrays "1,500 seed-43 draw" was arithmetically impossible, confidence-tuning clause was circular, B-pooled's image count was undercounted ~2×, the lesion→tooth mapping was unspecified; `RESULTS_LOG` 2026-09-04, commit `ef3f453`). **B-single** (Lever 2's frozen `models/14`, zero GPU) and **B-pooled** (new training, RTX-PRO6000 — A100 unavailable at rental time — `models/16_lever_b_pooled/`) both run through the frozen tooth-level eval on DENTEX + CariesXrays-val (`RESULTS_LOG` 2026-09-04 / 04b): **B-single wins CariesXrays decisively (69.4% vs. gate 31.7% / constant 56.2%, CI excludes 0) but LOSES DENTEX decisively (8.6%, CI excludes 0 the wrong way) — the pre-registered "wins in-domain, fails to transfer" outcome. B-pooled recovers DENTEX to a statistical TIE with both comparators (45.5%, CI includes 0) while barely costing CariesXrays (68.4%, ~1pp, still a decisive win)** — not one of the pre-reg's discrete outcome bins, recorded as its own honest result. **Sec 6 acceptance rule NOT met by either arm** (only 1 of 2 scored cohorts passes; needs ≥2 of 3) — **Ningxia is the deciding cohort and is not on this machine**, get it from the account owner before any adoption call. Pipeline default caries path stays gate v3.0. Full detail: `docs/session-memory/2026-09-04a-lever-b-build-and-both-arms.md`.

**Previously: 3 September 2026.** GPU balance ₹1,732 (user topped up +₹2,000; Lever A cost ~₹735). Instance 496005 destroyed. **Lever A is DONE — ABLATION** (`models/15_detector_multicorpus_leverA/`, `RESULTS_LOG` 2026-09-03 + 03b). Pre-registered verdict, all 3 criteria: **PRIMARY passes** (FDI e2e on the 164 DENTEX images 0.584 → 0.928, Δ +34.4 pp — replicates Lever 1), **GUARD 1 passes** (pooled external caries agreement +9.1 pp [+7.5, +10.8] — Ningxia 0.41 → 0.60, CariesXrays 0.31 → 0.37), **GUARD 2 FAILS** (Tufts frozen test box mAP 0.724 → 0.585/0.552). 2 of 3 → ABLATION, pipeline default detector unchanged. **The tradeoff is bidirectional and quantified** (worse on Tufts by ~15 pp, better on the other 5 of 6 cohorts by +6 to +34) — a real methodology result, not Lever 1's flat "dilution". **Next: Lever B** (lesion-detection caries path — the remaining shot at an adoptable positive headline).** Post-mortem on Lever A's Tufts Guard-2 failure done 3 Sep (`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md`, `RESULTS_LOG` 2026-09-03c): confirmed **capacity dilution, not a bug**; council says no more detector GPU, fold into §8.10, Lever A2 deferred behind Lever B. Cheap no-GPU warm-up: Phase 0 of that diagnosis (box overlays + confidence sweep → write §8.10).

**Lever 2 is DONE (2 Sep).** Trained a standalone caries-**lesion** detector (YOLOv11l) on the
CariesXrays benchmark → **COCO AP 48.2 / AP50 84.5 / AP75 50.0** on this project's own
seed-42 4,800/1,200 split — **level with FPCL's task-specific method (48.2 / 84.1 / 50.6) and
~8 AP above every off-the-shelf baseline in their table.** ⚠️ **The official FPCL split is NOT
public** (checked the repo, the Drive download, the DVCTNet release), so the comparison is
*indicative, not head-to-head* — different random test images. Not wired into the pipeline,
adopts nothing. `RESULTS_LOG.md` 2026-09-02b, `models/14_cariesxrays_lever2/run_summary.txt`,
`outputs/lever2_cariesxrays/PRE_REGISTRATION.md`. Instance 492535 destroyed; spend ₹256.61
(₹816.70 → ₹560.09).

**2 Sep session 3c — score-improvement council held, three decisions taken** (`docs/session-memory/2026-09-02c-score-lever-council-and-plan.md`, §5 below): **(a) Framing A+** — keep the evaluation-protocol spine, add the lever fixes as positive systems results (not a pivot to a systems paper — the 1 Sep council rejected that). **(b) Venue: journal primary** (IEEE JBHI / Computers in Biology and Medicine — both S, no page limit), ISBI 2027 only as an optional cut short paper *if* the compliance blockers close by mid-Oct — ISBI's 4-page hard cap (verified 2 Sep) fights the extra results. **(c) Levers A + B now, D if time; skip C and E; budget ~₹4,000.** Two pre-registration drafts written (`outputs/lever_A_multicorpus_detector_v2/`, `outputs/lever_B_lesion_caries_path/`) — bars open to one review round, frozen once builds start. Track B is defined in §3.

Where work resumes — an ownership split decided 3 Sep (`outputs/lever_B_lesion_caries_path/{START_HERE,WINDOWS_SETUP}.md` carry the tables). **The USER (Mac): Phase 0 then, conditionally, Lever A2. The FRIEND (Windows): Lever B.** A/A2 and B run in parallel. **(A) Phase 0 — user, Mac, now.** Finish the Tufts Guard-2 diagnosis (`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` §3): GT-box overlays + FN/FP at conf {0.10, 0.25, 0.40} incl. Arm 4C → write `PAPER_MATERIAL.md` §8.10 + §8 limitations. No GPU, ~½ day. **(A2) Lever A2 — user, Mac, conditional** — only if Lever B yields no adoptable headline (`TUFTS_GUARD2_DIAGNOSIS.md` §3 Phase 1 gate). **(B) Freeze the Lever B bars** (`outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md` §4–§6, one review round, user/mentor). **(C) Get datasets + `models/14` to the friend** (user / account owner) — **three checkpoints (`models/09`, `10`, `11`) are now committed to git** (3 Sep, `.gitignore` exceptions + `.gitattributes`), so `git pull` covers them; still needed: CariesXrays raw + Ningxia (25 GB, cannot go in git — Tufts licence). **`models/14/best.pt` (B-single arm) is on the friend's Windows laptop** — verify sha256 `278d1e00…` and commit it (a `.gitignore` exception was added 3 Sep); `WINDOWS_SETUP.md` §4. **(D) Lever B — friend, Windows, after B + C.** `outputs/lever_B_lesion_caries_path/WINDOWS_SETUP.md` then `START_HERE.md`. Rebuild `data/cariesxrays_det/` (`build_cariesxrays_detector_dataset.py`, SEED 42 — gitignored, on no machine); write the DENTEX `quadrant-enumeration-disease` → YOLO caries converter (`category_id_3 ∈ {1,3}`, reuse `CARIES_CLASSES` from `scripts/dentex/build_dentex_crops.py`); build the seed-43 CariesXrays eval draw. Then B-single + B-pooled (~₹300). **Track A stays the critical path and wins any time conflict** — venue commit (mentor), the four compliance blockers (account owner), authors/affiliations still `Unknown` in `main.tex`, the weight uploads above, fold the Lever-2 row into Related Work. The DOI blocker is cleared (`RESULTS_LOG.md` 2026-09-02); a `url`-field sweep and the 19 DOI-less entries remain, both minor.

**2 Sep session also established:** MiKTeX 25.12 **is** on the Windows machine — `paper/main.tex`
recompiles to **12 pages, 0 errors / 0 undefined refs / 0 overfull boxes** (the §3.1 "no LaTeX
toolchain" note was macOS-only). And the **`D:` drive is not currently mounted** on the Windows
machine, so the SDH clinic data (§8) is unreachable this session — SDH work is paused, not
cancelled; find out where `D:` went before relying on §8's Windows table.

**The plan gained a second track on 1 Sep: improve the numbers, not just the methodology** — and
**Lever 1 ran to a verdict (ABLATION).** Seven failed caries experiments across three cohorts had
left the paper resting on a negative headline (an image-blind constant ties or beats the pipeline).
The score-improvement track, funded from the JarvisLabs balance (**₹1,105.99 → ₹816.70** after the
Lever-1 run; **nothing running, nothing paused**), is a three-lever plan:

- **Lever 1 — multi-corpus detector retrain.** Detector recall (70.6%) is the *measured* binding
  constraint on the 58.3% Stage-2 headline: `end-to-end = recall × of-detected = 0.706 × 0.826`.
  Pooling DENTEX `quadrant_enumeration` (634 images / 18,095 tooth boxes, already local) with the
  700 Tufts images is **1.9× the detection supervision** — the same move DentFound used (2,698
  images) for its tooth-identification model. **DONE 1 Sep — see §3 Track B B1 and `RESULTS_LOG.md`
  2026-09-01h. Result: FDI end-to-end 0.5844 → 0.9338 [Δ +34.9 pp], but the Tufts guard fails
  (0.810 → 0.647) → ABLATION, detector default unchanged.** The 93.4% is in-domain and confirms
  the 58.3% headline is detector-domain-limited, not numbering-limited.
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

**The GPU workflow that finally worked (after an aborted A30 attempt on the first pass):** `tar`
the dataset to **one** file (`jl upload` of 3,268 small files was the bottleneck — the abort cost
₹21.45), sha256-verify both ends, extract, **delete the macOS `._*` AppleDouble files** (they
double every file count and would feed YOLO garbage — caught by the on-box gate), re-run the
geometry gate **on the rented box**, then train. Lever 1 ran on an **RTX PRO 6000 Blackwell**
(A100/H100 containers were unavailable; ₹179/hr, ~1.5 h, ₹267.84). `jl` CLI authenticated on this
Mac, SSH key `macos-m4pro` registered, live pricing + macOS notes in `GPU_SETUP.md` §0.

**The sixth-cohort result stands — it is the strongest form of the paper's central claim.**
CariesXrays (Chen et al., **AAAI 2024**, DOI 10.1609/aaai.v38i20.30196), evaluated with the
**frozen** pipeline, randomised 1,500 images / **3,421 lesions** (more than DENTEX and Ningxia
combined): **pipeline 0.309 vs constant 0.561, paired Δ +0.252 [+0.232, +0.273]** — the constant
wins outright. Mechanism measured: **72.0% of lesions on molars, 60.2% on the eight constant
teeth**. Across cohorts: +0.046 (DENTEX), −0.009 (Ningxia, tie), **+0.252** (CariesXrays). Folded
into `main.tex` as a new Table + §8.25; provenance verified against AAAI OJS / ACM DL / DBLP
(licence not stated by the authors). `verify_paper_numbers.py` now asserts **90** claims (was 82).

**✅ DOI BLOCKER CLEARED — 2 Sep.** The 22 broken DOIs (11 resolving to a *different* paper,
11 unregistered) were each looked up by title: **all 22 are real, published papers that carried
a wrong identifier — none fabricated.** Fixed and re-verified against the registry (title-overlap
1.00), and in 19 of 22 the `volume`/`pages` were wrong too and were corrected from the registry
record. Re-audit: **62 clean / 1 cosmetic flag** (`yalim2026comparative`, `İ`/`ı` accent only,
uncited). `RESULTS_LOG.md` 2026-09-02, `outputs/citation_audit/RESOLUTION_2026-09-02.md`.
**Two small follow-ups remain, neither blocking:** (i) a sweep of the `url` fields across all 63
entries — the audit only checks the `doi` field, and 6 `url`s embedded the old wrong DOI (fixed);
the rest are unchecked; (ii) the 19 genuinely DOI-less entries (arXiv/web, expected). The earlier
`chen2024cariesxrays` fix (30197 → 30196, RESULTS_LOG 2026-09-01c) still stands.

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
> `models/11_yolo_seg_tufts_r1/best.pt` is now **committed to git** (3 Sep, §4) — a `git pull` restores it; the Drive upload is no longer the fresh-clone blocker.
> **Partially addressed, 30 Aug:** the *ignore policy itself* was fixed the same day this landed
> — `outputs/*` plus a curated per-directory whitelist replaced the blanket `!outputs/**`
> (`0bda8d5`, `2f436b9`), so future runs no longer become trackable by default, and one
> already-tracked duplicate checkpoint was caught and kept out. **The existing ~763 MB already in
> history is untouched** — that still needs a deliberate, team-coordinated history rewrite
> (everyone re-clones after), or a decision to accept it. Not done, just no longer growing
> silently.
> **2 Sep:** the `models/12`/`12a` v3-head checkpoint tracking was made consistent — **both are
> now tracked in git** (43 MB each, like the `08`/`10` heads). `12`'s was already committed
> (`21ea05b`); `12a`'s was added. A brief `git rm --cached` of `12`'s that day (`44b7252`, to
> "match 13/14") was **reverted the same session** — untracking it would silently delete the file
> from the macOS collaborator's tree on `git pull`, and it is not on Drive. Net effect on `12`
> across the day: zero (identical blob). The `13`/`14` detector weights stay gitignored — those
> are `.pt` (YOLO), never were in git, and `13`/`14` are pure ablations/benchmarks.

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
behind them — and those numbers are assembled into a **complete manuscript that compiles clean**:
re-verified 2 Sep on the Windows machine with MiKTeX 25.12, **12 pages, 0 errors / 0 undefined
citations / 0 undefined refs / 0 overfull boxes** with the corrected bibliography.

**2 September 2026 — two things landed.** **(a) The DOI submission blocker is CLEARED:** all 22
broken DOIs in `source.bib` were looked up by title — **every one is a real, published paper that
carried a wrong identifier, none fabricated** — fixed and re-verified against the registry
(`RESULTS_LOG.md` 2026-09-02, `outputs/citation_audit/RESOLUTION_2026-09-02.md`). Two minor
leftovers, neither blocking: a `url`-field sweep and the 19 genuinely DOI-less entries.
**(b) Lever 2 executed** (§3 Track B / §5): a standalone caries-**lesion** detector (YOLOv11l)
trained on the CariesXrays benchmark scores **COCO AP 0.482 / AP50 0.845 / AP75 0.500** — level
with the task-specific FPCL method (0.482 / 0.841 / 0.506) and ~8 AP above every off-the-shelf
baseline in their table. **⚠️ On this project's own seed-42 split** (the official FPCL split is
not public) — so *indicative*, not head-to-head. Not wired into the pipeline, adopts nothing;
one benchmark row for Related Work. `models/14_cariesxrays_lever2/`, `RESULTS_LOG.md` 2026-09-02b.
GPU balance **₹560.09**, nothing running.

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

**C1 is DONE and hardened, and the honest version is more complicated than it looked on 27 Aug.** A general-purpose VLM zero-shot scores **F1 0.149 at 7B** (reproducing 27 Aug's 0.143 on new hardware and a new transformers major version) and **0.246 at 32B** — scale helps a lot. **Few-shot makes it monotonically worse** (0.066 at 2-shot, 0.034 at 4-shot) because in-context examples teach it to answer *nothing*: 123 of 164 answers are empty at 4-shot. Both models still hand a confident dental answer to a **random-noise image**. **But the result that constrains the write-up: a fixed list of the eight first/second molars — fitted on held-out images, never on the scored set — scores 0.320, above our pipeline's 0.294.** Tooth-level FDI-set F1 is base-rate dominated; that constant must appear beside every C1 arm, and C1 must not be headlined as "small specialist beats large generalist" without it. The efficiency claim survives: 33.45 B params and 70.1 GB of H100 VRAM still lose to **61.2 M** params on a CPU (caries path; 83.6 M all six models — counted 28 Aug, correcting the "~25 M" that was the detector alone). C1 cost Rs 285.20 (+ Rs 14.26 wasted on a stray instance). *(Balance has since moved: R1 + Lever 1 + Lever 2 spent it down to **₹560.09** as of 2 Sep — §8.)*

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
| **Lever 1 — multi-corpus detector retrain** (1 Sep) — ABLATION. FDI end-to-end on DENTEX 0.584 → 0.934 (all from the added data), but the Tufts guard fails (box mAP 0.810 → 0.647). Pipeline default detector unchanged. | `models/13_detector_multicorpus_lever1/run_summary.txt`, `RESULTS_LOG.md` 2026-09-01h |
| **Lever 2 — CariesXrays caries-lesion detector** (2 Sep) — BENCHMARK ROW, not a pipeline component. YOLOv11l, **COCO AP 0.482 / AP50 0.845** on this project's own seed-42 split (the FPCL split is not public) → level with FPCL, ~8 AP over the generic baselines. Indicative, not head-to-head. | `models/14_cariesxrays_lever2/run_summary.txt`, `RESULTS_LOG.md` 2026-09-02b, `outputs/lever2_cariesxrays/PRE_REGISTRATION.md` |
| **The 22 broken DOIs FIXED** (2 Sep) — all real papers with wrong identifiers; corrected + re-verified against the registry. `source.bib` re-audits 62 clean / 1 cosmetic. `url`-sweep + 19 DOI-less entries remain (minor). | `RESULTS_LOG.md` 2026-09-02, `outputs/citation_audit/RESOLUTION_2026-09-02.md` |
| **All READMEs + this file** swept for staleness (five passes across four sessions; last 2 Sep — DOI blocker cleared, Lever 2, MiKTeX-on-Windows, `D:` unmounted) | `RESULTS_LOG.md` 2026-08-25e/f, 2026-08-26b, this rewrite |
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

## 3. What is NEXT — Track A (manuscript + compliance) is the critical path; Track B v2 (Levers A + B) runs in parallel

**Track B was reopened on 2 Sep (session 3c council, §5).** Lever 1 (ABLATION) and Lever 2 (benchmark row) proved the mechanism — detector *domain* is the 58.3% ceiling, and Lever 1's guard failure is a fixable build flaw (2 corpora, Tufts 52% of the mix, no corpus balancing). The user funded a second attempt. **Track B v2 = Lever A (multi-corpus detector, done right) + Lever B (lesion-detection caries path), with Lever D (bone-loss second corpus, now possible via BRAR) opt-in if A and B land with schedule to spare.** Pre-registrations drafted; see the Track B block below. **Track A is still the critical path** — it wins any time conflict, and the compliance blockers gate ISBI regardless of any number.

**As of 2 Sep, still open and all on the USER / account owner:** (1) venue decision — ISBI vs
journal (gates the cut); (2) the four compliance blockers (items 4, 9) → account owner;
(3) authors/affiliations in `main.tex` are still `Unknown`; (4) **`models/09`+`11` are now in git** (3 Sep); **`models/14/best.pt` is on the friend's Windows laptop** — verify + commit (`outputs/lever_B_lesion_caries_path/WINDOWS_SETUP.md` §4); (5) where is `D:`? — SDH track is paused until it is
back (item 10). **Engineering follow-ups (small):** fold the Lever-2 row into `main.tex` Related
Work with the split caveat + AAAI numbers re-verified against the PDF; the `source.bib` `url`
sweep + 19 DOI-less entries.

### Track A — get the manuscript submittable

1. **CUT THE MANUSCRIPT TO VENUE LENGTH.** `paper/main.tex` compiles clean — **re-verified 2 Sep
   on the Windows machine with MiKTeX 25.12: 12 pages exactly, 0 errors / 0 undefined refs /
   0 overfull boxes** (the "no LaTeX toolchain" note was macOS-only; ×`latexmk -pdf` works here).
   ISBI allows 4. Pick the venue first — a journal needs no cut. `docs/paper/REBUILD_AUDIT.md`
   Deliverable 4 maps section purpose.
2. **✅ DOI FIXES DONE — 2 Sep.** All 22 corrected and re-verified (`RESULTS_LOG.md` 2026-09-02,
   `outputs/citation_audit/RESOLUTION_2026-09-02.md`); `paper/source.bib` re-audits 62 clean / 1
   cosmetic. **Two minor leftovers:** (i) sweep the `url` fields across all 63 DOI entries — the
   audit checks only the `doi` field, 6 `url`s carried the old DOI and were fixed, the rest are
   unchecked; (ii) the 19 DOI-less entries still need a per-entry decision. Neither blocks.
3. **Authors and affiliations are still `Unknown`** in `main.tex`. Blocking, not engineering.
4. **The four compliance blockers** (§1, `PAPER_MATERIAL.md` §8.19). Zero compute, all
   account-owner actions, and (1) and (3) are live protocol breaches rather than paperwork.
5. **✅ `models/11` + `models/09` are now committed to git** (3 Sep, `.gitignore` exceptions, 53 MB + 43 MB, private repo — see §4). A fresh clone now runs the pipeline demo. `models/14_cariesxrays_lever2/weights/best.pt` (the Lever-B B-single arm) is **on the friend's Windows laptop** — a `.gitignore` exception was added 3 Sep so they `git add` + commit it after a sha256 check (`outputs/lever_B_lesion_caries_path/WINDOWS_SETUP.md` §4).
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
10. **SDH clinic track — unblocked 30 Aug, NOT on the critical path, and PAUSED as of 2 Sep:**
    the `D:` drive is **not mounted** on the Windows machine right now (checked 2 Sep — only `C:`
    is present), so the clinic data in §8's Windows table is unreachable this session. Before any
    SDH work resumes, find out whether `D:` is a detached external drive, was re-lettered, or
    something else. Consent from the clinic was obtained 30 Aug (written agreement expected 1 Sep),
    closing `PUBLICATION_TODO.md` T1.2's governance block. When reachable, the pipeline runs on it
    unmodified at **2.2 s/image on CPU**, so a full-set pass is a ~2-hour unattended job needing
    **no GPU**.
    Plan, tiers, filter design, pre-registered criteria: **`docs/research/SDH_EXECUTION_PLAN.md`**;
    first measurements: `RESULTS_LOG.md` 2026-08-30. **If item 1 slips, this is what gets
    deferred.** Two things must happen before any SDH number is produced: repair or exclude the
    six truncated images (`001970`–`001975`, found 30 Aug — the usable set is **3,213**, not
    3,219), and freeze `data/sdh/splits_v1.json` before a single filter threshold is chosen.

### Track B v2 — lift the numbers (Levers A + B approved 2 Sep, session 3c; §5)

**Framing (§5):** these are *fixes surfaced by the evaluation protocol*, not a chase for SOTA. Lever A supports the "end-to-end numbers hide stage-wise failure" thesis; Lever B addresses the base-rate-dominance thesis head-on. Every lever is pre-registered before its build, bar not moved — same discipline as Levers 1 and 2, which is itself a selling point of the paper.

**Pre-condition, learned twice on 1 Sep:** every dataset built for a rented run is verified locally first — round-trip geometry, canonical-count reproduction, a render inspected by eye — because R1's misaligned masks and the void `dataset_seg` both produced *smoothly-falling loss on garbage* and errored nowhere.

- **DONE — B1 / Lever 1** (multi-corpus detector, Tufts + DENTEX). 1 Sep, ABLATION. FDI e2e **0.584 → 0.934** in-domain (Δ +34.9 pp [+30.8, +39.0], all from the data), guard fails (Tufts test box mAP 0.810 → 0.647). `models/13_detector_multicorpus_lever1/`, `RESULTS_LOG.md` 2026-09-01h. **Kept as the mechanism proof; superseded as an adoption attempt by Lever A.**
- **DONE — B2 / Lever 2** (standalone CariesXrays lesion detector). 2 Sep, benchmark row. YOLOv11l COCO **AP 0.482 / AP50 0.845** on this project's seed-42 split (FPCL's is not public) — level with FPCL, ~8 AP over the generic baselines; indicative, not head-to-head. `models/14_cariesxrays_lever2/`, `RESULTS_LOG.md` 2026-09-02b. **Its `best.pt` is Lever B's B-single arm.** Still to do: one row in `main.tex` Related Work with the split caveat, AAAI table re-verified against the PDF.

- **Lever A: multi-corpus detector, done right — DONE 3 Sep. ABLATION** (`models/15_detector_multicorpus_leverA/run_summary.txt`, `RESULTS_LOG` 2026-09-03). 4 corpora / 4 institutions (Tufts + DENTEX + Kaggle-dual + UFBA-425), per-corpus balanced. **Primary passes big:** FDI e2e on the 164 leak-free DENTEX images **0.584 → 0.928**, Δ **+34.4 pp [+30.3, +38.5]** — *replicates Lever 1's +34.9 pp* with 3-4 corpora. UFBA adds nothing (Arm 3C = Arm 4C = 0.928). **Guard 2 FAILS harder than Lever 1:** Tufts frozen test box mAP Control B 0.724 → Arm 3C **0.585** → Arm 4C **0.552** — monotonic in corpus count (Lever 1's arm was 0.647). Balanced sampling put Tufts at 33 % of the mix (vs Lever 1's 52 %); a corpus's held-out box mAP scales with its training share, so the pre-registered "more corpora + balance = less dilution" hypothesis was **backwards**. **Guard 1** (external caries agreement) **PASSES** (3 Sep 03b) — pooled Δ +9.11 pp [+7.49, +10.81]; Ningxia caries 0.407 → 0.600, CariesXrays 0.309 → 0.370. So 2 of 3 criteria pass; adoption needs all three → **ABLATION**, **pipeline default detector unchanged.** The tradeoff is bidirectional: worse on Tufts test, better on DENTEX + every external cohort — better on 5 of the 6 paper cohorts, worse only on the one it's benchmarked against. Cost ~₹735 (₹2,467 → ₹1,732), instance destroyed. What this gave the paper: the "58 % ceiling is detector *domain*, not numbering" decomposition now **replicates**, plus a clean 3-point in/out-domain tradeoff curve. Did NOT lift the headline in an adoptable way — that's Lever B's job now. **Post-mortem (3 Sep, `outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md`, `RESULTS_LOG` 2026-09-03c):** the Guard-2 drop is confirmed **capacity dilution, not a bug** — Arm 3C misses 37 % more Tufts teeth and emits 42 % more spurious boxes than Control B, localisation unchanged; a box-convention-mismatch hypothesis was tested against the trained models and **refuted**. Also surfaced: the deployed Stage-1 is *segmentation* (0.810 on this split) and every detection model here ≤ 0.724 — seg→detect costs ~9 pp before any corpus is added. **Council: no more detector GPU.** A retry = Lever A2 (new pre-reg), deferred behind Lever B — see the OPT-IN list.
- **Lever B: lesion-detection caries path — DONE building/evaluating 4 Sep, VERDICT PENDING NINGXIA.** Owner: the FRIEND, on Windows. Pre-reg frozen 4 Sep (4 defects fixed before any GPU spend — `RESULTS_LOG` 2026-09-04, commit `ef3f453`): the CariesXrays "1,500 seed-43 draw" was arithmetically impossible (max disjoint pool is 1,200 = the existing val split, used as the eval cohort instead); the confidence-tuning clause became circular once that val set became the eval cohort (frozen at 0.25 flatly); B-pooled's image count was undercounted ~2× against its own balancing rule (corrected to 9,600/epoch, cost re-estimated ~₹600/₹1,200); the lesion→tooth mapping was unspecified (added: argmax-containment). **Both arms run, full frozen eval on DENTEX-164 + CariesXrays-val-1200** (`RESULTS_LOG` 2026-09-04 / 04b): **B-single** (Lever 2's `models/14`, zero GPU) — CariesXrays **69.4%** vs gate 31.7% / constant 56.2% (CI excludes 0, decisive win) but DENTEX **8.6%** (CI excludes 0 the wrong way, decisive loss) — the pre-registered "wins in-domain, fails to transfer" outcome. **B-pooled** (new training, `models/16_lever_b_pooled/`, JarvisLabs RTX-PRO6000 — A100 unavailable at rental time — instance 496516, ₹546.93, destroyed after verified download) — CariesXrays **68.4%** (barely moved, still a decisive win) and DENTEX **45.5%** (CI *includes* 0 vs both comparators — a statistical TIE, not a win, but no longer a loss either). Not one of the pre-reg's discrete outcome bins; recorded as its own result. **Sec 6 rule NOT met by either arm** — only 1 of 2 scored cohorts passes each time, rule needs ≥2 of 3. **Ningxia is the deciding cohort and is not on this machine** (checked the eval script's real default root, not just `data/ningxia/`'s `manifest.csv`) — get it from the account owner, then re-run the existing eval + `scripts/eval/lever_b_bootstrap.py --arm-tag B-pooled` (no new code needed) for the real verdict. Pipeline default caries path stays gate v3.0 either way for now. One real bug caught before it could cost GPU time: ultralytics' `train.txt` file-list resolution only rewrites a `./`-prefixed line, not a bare relative one (verified against its source) — fixed by rewriting the list to absolute paths at train time. Full detail: `docs/session-memory/2026-09-04a-lever-b-build-and-both-arms.md`.
- **OPT-IN — Lever D: bone-loss second corpus.** Only if A and B land with schedule to spare. §8.13's "there is no second periodontal corpus" is **now outdated**: **BRAR** (Nature Sci Data 2025, Figshare `10.6084/m9.figshare.30155974`, tooth-level bone-resorption grading, openly downloadable) and **BoneLoss-PAN769** (Zenodo `21114193`, access-gated) both exist. Retrain Stage 4a/4b on Tufts + BRAR pooled (the +21.5 pp move that fixed Stage 2 cross-domain), re-validate on Ningxia + DENTEX. Risks: BRAR convention mapping; the Tufts bone-loss crop rebuild blocker (§9, `RESULTS_LOG.md` 2026-08-27u) may force BRAR-primary training. No pre-registration yet.
- **OPT-IN — Lever A2: multi-corpus detector retry. Owner: the USER, on the Mac.** Only if Lever B yields no adoptable headline **and** ≥ 2 weeks schedule slack **and** an explicit decision that an adoptable multi-corpus detector is worth a full downstream re-measure (`TUFTS_GUARD2_DIAGNOSIS.md` §3 Phase 1 gate). Probe **multi-corpus pretrain → Tufts-only fine-tune** (~₹400) first; **multi-corpus segmentation** (Tufts masks + SAM pseudo-masks, ~₹1,000) only if the probe is close. New pre-registration, identical Lever A acceptance rule, deployed detector stays `models/11` until it passes cleanly.

- **SKIP — Lever C (caries gate v5)** on CariesXrays-derived tooth labels. The per-tooth-gate approach is base-rate limited by construction and 5 attempts already nulled (§8.24). Not worth a slot. **SKIP — Lever E (bigger/newer detector arch)** — marginal, resolution already maxed.
- **NOT a lever, decided against:** a 4th caries-gate arm chasing CLAHE's +0.049 AP near-miss (CI includes zero; blocker is 34 source images, not method — `RESULTS_LOG.md` 2026-08-31b).

**Do NOT do:** train on Ningxia, or iterate against it. It is locked external test data and the single strongest thing this paper has (`MASTER_PLAN_2026H2.md` §4.1). A tune-against-it loop was proposed and declined on 27 Aug for exactly this reason.


## 4. Decisions PENDING — do not default into these silently

| Decision | Why it needs a human |
|---|---|
| **⚠️ Tufts licence breach — act before submitting or sharing further.** The release agreement forbids reproducing or posting the database "into any webpage or any other storage means"; `docs/EXTERNAL_DRIVE.md` records a Drive folder with the raw `ZIP/` release that was browsable **without signing in**. Restrict it, keep Tufts local-only, share the release *form* instead of the files. | Account owner's action, and a real submission risk |
| **Model weights are now in git (`models/09` 43 MB, `models/11` 53 MB, committed 3 Sep for the Windows handoff).** They are *derived* artefacts, not the Tufts database, and the repo is private — low risk. But `models/11` exceeds the ~50 MB rule-4 line, and history keeps them forever. Revisit before any public release (alongside the notebook-pixels item above); to undo: `git rm --cached` the two files, restore the `.gitignore` lines, re-host on Drive. | Deferred by the 3 Sep handoff decision; revisit before public release |
| **⚠️ Real Tufts radiograph pixels are embedded in 7 tracked notebooks, already on `origin/main`** — not references, actual base64 image data in cell outputs (`RESULTS_LOG.md` 2026-08-26b). **The GitHub repo is confirmed private, so this is deferred risk, not an active leak** — the user's explicit call. Must be resolved (strip outputs going forward, or rewrite history — destructive, needs a force-push) **before this repo, or any fork of it, is ever made public.** | Deferred by explicit user decision 26 Aug; revisit before any public release |
| **Is the Tufts mirror finding novel?** NOT established. The Panetta et al. (IEEE JBHI 2022) full text is IEEE-paywalled and unread — tried the indexed biomedical/arXiv corpora, the DOI, the author's own site, PDF search, and GitHub; all dead ends. If the paper documents the convention, this is a usage note, not a discovery. `RESULTS_LOG.md` 2026-08-25h §2, 2026-08-26a. | Needs someone with IEEE Xplore access — a 5-minute read, not a research task |
| ~~**Bone-loss domain-shift fix — what approach?**~~ **RESOLVED 27 Aug: none — reported as a measured limitation** (`PAPER_MATERIAL.md` §8.13). The Stage-2 combined-training lever does not transfer (DENTEX has no bone-loss labels); every remaining option is a research programme that does not fit before the 14 Oct freeze. Kept here for the reasoning, not because it is open. Options span the DENTEX+Tufts combined-training trick that worked for Stage 2 (untried here), R1 (shared Tufts-side fix), Ningxia-informed fine-tuning (needs care — Ningxia is locked, no tuning against it directly), or documenting it as a limitation rather than a fix. | Research direction, not a fact to look up |
| ~~**A third public FDI corpus exists, unused.**~~ **RESOLVED 28 Aug: added, and it stays an ablation.** Head v3 trained on DENTEX+Tufts+Kaggle gains **+1.14 pp on DENTEX val** [+0.33, +1.95] against a same-day control; Tufts flat; the pipeline default stays v2.0 because swapping it invalidates every Stage-2 number in the paper. The corpus is **500 images, not 2,000**, and its FDI convention was verified by arbiter, not assumed. `PAPER_MATERIAL.md` §8.23. | Closed |
| **What else to use `DENTEX/disease/` for**, beyond the Stage-2 eval set (164 leak-free of 250) and the lesion-localisation source. The 91 `saglam` (healthy) teeth as a small real healthy class is still an open candidate use. | Scoping call |
| **Clinic data governance.** `index.csv` sits beside `images/` on a shared Drive, voiding the de-identification. Five actions in `clinical_dataset_provenance.md` §4a, all needing the Drive owner. | Not this repo's account |
| **⚠️ Get Ningxia onto the Windows machine — the only thing standing between Lever B and a real adoption verdict.** Both arms are built, trained, and evaluated on the other 2 of 3 cohorts (`RESULTS_LOG` 2026-09-04b); B-pooled ties DENTEX and wins CariesXrays decisively, but Sec 6 needs ≥2 of 3 cohorts to pass and only 1 does so far. Re-running the eval on Ningxia once it's there needs zero new code. | Restrictive licence — account owner only |
| **Lever A2 — is an adoptable multi-corpus detector worth chasing?** The Guard-2 failure is diagnosed as capacity dilution, not a bug (`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md`). A retry (pretrain→fine-tune, or multi-corpus segmentation) could pass, but adopting a new detector forces re-measuring every pipeline number. Gated behind Lever B + a schedule check. | PI call, not a fact to look up — only worth it if Lever B doesn't deliver and schedule allows |
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
is verified as an S-grade venue by edition count. As of this update: **~8 weeks to the deadline
(26 Oct), ~6 to the 14 Oct implementation freeze.** Re-verify ISBI's current Scopus indexing on
the official source list before committing.

### 1 September 2026 — publication framing council

**Two framings were weighed; Framing A is the working spine.**

| | Framing A — evaluation / protocol paper | Framing B — systems paper with a positive number |
|---|---|---|
| Core | Tooth-level caries scores are base-rate dominated; an image-blind constant ties/beats the pipeline across **6 cohorts**; stage-wise decomposition locates the ceiling (detector *domain*, quantified by Lever 1: 58 → 93 %). | Needs Lever 2 to land a caries-lesion mAP near CariesXrays' published FPCL baselines. |
| Readiness | Everything exists. 8 wks covers cut + compliance + polish. | 1.5–3 wks of research (VOC→YOLO conversion, pre-reg, training, eval) with a real chance of nothing usable. |
| Novelty | Methodological: only 2/49 task-relevant papers do genuine external validation. "Are we making progress?" critiques publish at good venues. | Off-the-shelf YOLO on a public benchmark — weak standalone contribution; reviewers ask "what's novel?" |
| Does it fix the finding? | It **is** the finding, framed constructively (protocol + deployed system + Lever-1 mechanism result). | **No** — the constant beats the *tooth-level* metric because of base-rate dominance, not model quality. Lever 2 improves a *different* (lesion-level) metric. |

**Decision:** ship **A**. Run **Lever 2 in parallel, hard-capped at 1 day** (read the AAAI FPCL
baselines → go/no-go). Clean reproducible split + beatable numbers → a 3-day bonus section that
does **not** block the core. Otherwise drop it same day. Never let B be load-bearing.

**A is not a "negative-result paper"** — its positive deliverables are (1) a reusable evaluation
protocol the field lacks, (2) the Lever-1 mechanism result (the 58.3 % ceiling is the detector's
domain — same-domain detector nearly doubles end-to-end), (3) a deployed, reproducible pipeline
(Docker, pinned env, 90 auto-verified numbers).

**Venue:** target ISBI (deadline forcing function + S-grade); **commit a journal as the fallback**
if rejected (IEEE JBHI / *Diagnostics* / *Medical Image Analysis* — journal = S regardless of
edition). Do **not** drop to a 1st-edition conference (B) — the work is above that.

**Grade expectation, honest:** ISBI accept → S (realistic, ~60 % base rate, rigour helps). ISBI
reject → journal resubmit → S (slower). The real blocker is not paper quality — it is whichever
co-author controls the Tufts Drive / IRB / dataset accounts doing the compliance work in the next
~2 weeks.

### 2 September 2026 — Lever 2 go/no-go council

> **OUTCOME (recorded after the fact):** council said GO conditional on the FPCL split being
> reproducible. **The split turned out NOT to be public**, and the user overrode the gate
> ("forget the publication … start the gpu work"). Ran on this project's own seed-42 split →
> **COCO AP 0.482**, level with FPCL. `RESULTS_LOG.md` 2026-09-02b. The council text below is the
> pre-run reasoning, kept as the record.

**The §5 council on 1 Sep timeboxed Lever 2 to a 1-day go/no-go, gated on reading the AAAI FPCL
baselines. Baselines now read; this is that decision.**

**What Lever 2 is:** train a standalone caries-**lesion** detector (YOLOv11l, `detect`) on the
CariesXrays benchmark's own train split and report COCO AP / AP50 / AP75 on its own test split,
**beside the published FPCL table**. It is *not* wired into the six-stage pipeline and adopts no
checkpoint — it is one row in the Related-Work / benchmark comparison, the project's first number
placed next to a published result on the same data and metric.

**The AAAI FPCL numbers (Chen et al., AAAI 2024 38(20) 21940–21948; COCO AP on 4,800/1,200):**

| method (their table) | AP | AP50 | AP75 |
|---|---|---|---|
| RetinaNet R50 | 13.0 | 30.5 | 10.2 |
| DINO | 37.8 | 75.3 | 29.4 |
| Faster R-CNN R50 | 39.9 | 78.0 | 37.8 |
| YOLOX (CSPDarknet) | 40.5 | 81.3 | 36.1 |
| **FPCL (their method, R50)** | **48.2** | **84.1** | **50.6** |
| DVCTNet (later paper, DINOv2-ViT-B) | 48.9 | 84.7 | 52.2 |

**Arguments FOR running it:**
- The split is a **standard VOC `ImageSets/Main/{train,val}.txt}`** (read from FPCL's own
  `my_dataset.py` / `train.py`); a follow-up paper (DVCTNet, arXiv 2508.20813) reused "the
  original split … for fair comparison", so the split exists and is used by others.
- The metric is unambiguous — COCO AP via `pycocotools`, exactly what `ultralytics` reports.
- Single class ("Decay"), 4,800 train images — a **~3–4 h, ~₹300** job. Balance ₹816.70 covers
  it plus one redo.
- YOLOv11l is architecturally newer/stronger than their YOLOX baseline; landing **~40–46 AP /
  ~80–85 AP50** is a realistic expectation, i.e. at/above the generic baselines and within a few
  points of FPCL — a legitimate "a 2024 off-the-shelf detector reaches X without a caries-specific
  method" data point for Framing A.
- The VOC-parsing hazard (27.3% of `<size>` fields wrong) is **already solved** in
  `scripts/eval/cariesxrays_external.py:lesions_from_voc` — reuse, don't reinvent.

**Arguments AGAINST / risks:**
- **The gate is real:** if the Drive download does **not** contain the `ImageSets` split and the
  authors don't answer email, an own-split number **cannot** sit in their table and the whole
  exercise loses its point. Drop it that day — do not train on a self-made split and imply
  comparability.
- We will very likely **not beat FPCL's 48.2 AP** (their contrastive method); the honest framing
  is "competitive with generic baselines", not "new SOTA". If the team wants a headline win,
  this isn't it.
- Data is **not on the Windows machine** — a ~2 GB re-download + local geometry-gate build is
  the first ~half-day before anything is rented.
- Track A (venue, 4-page cut, compliance, authors) is the real path and **nothing here may
  delay it**. Lever 2 runs only in parallel and only by whoever is not doing Track A.

**DECISION: GO — conditional on the split gate.** Sequence:
1. **Gate (user, 10 min):** download CariesXrays from the Drive folder
   (`1qWL2f0A-vf91StHxs24eoiFDyuoHEh4N`); check for `ImageSets/Main/train.txt` + `val.txt` (or
   `test.txt`). Split present → proceed. Absent → email `chenbingzhi@m.scnu.edu.cn` /
   `darrenzz219@gmail.com`; no reply in a few days → **DROP Lever 2**, Framing A stands alone
   (it always did).
2. **Pre-register** to `outputs/lever2_cariesxrays/PRE_REGISTRATION.md` — metric (COCO AP primary,
   AP50/AP75 reported), the fixed FPCL split, comparator (the published table, verbatim), and a
   "reported as-is, bar not moved" rule. Commit before any training.
3. **Build + geometry-gate** the VOC→YOLO dataset locally on Windows (CPU): reuse
   `lesions_from_voc`'s image-frame `<size>` handling; assert every box round-trips; render a
   sample by eye; `tar` to one file; sha256 both ends.
4. **Train** YOLOv11l `detect`, 1024 px, on a rented **A100-40GB @ ₹84.24/hr** (or A100-80GB spot,
   same price), ~100 epochs early-stopped, ultralytics pinned to the frozen-model version
   (8.4.127). Re-run the geometry gate **on the rented box** before launch.
5. **Evaluate** on the 1,200 test images with `pycocotools` (`ultralytics val` reports COCO AP);
   write the row into `RESULTS_LOG.md` and a new benchmark table in `main.tex` §Related Work.
   Destroy the instance the moment weights are down.

**Not in scope:** Lever 3 (caries gate v5) stays below Track A. No pipeline checkpoint changes.
No tuning against Ningxia, ever.

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

- **External validation on 4 hospitals + the CariesXrays benchmark = 6 independent cohorts**,
  zero leakage verified per corpus. This is the differentiator.
- **Lever 1's quantified decomposition** (1 Sep): the 58.3 % end-to-end ceiling is the detector's
  *domain*, not the numbering head — a same-domain detector reaches 93.4 % on the same metric
  (in-domain; ablation, not adopted). Shows exactly what to fix and by how much.

**What will draw reviewer pushback, and should be framed rather than hidden:**
- **58.3% Stage-2 end-to-end** (cross-domain) is not a strong headline number by itself — it is a
  fair end-to-end number *including* the detector's recall, which most comparable work does not
  report on. Lever 1 shows the ceiling is domain, not method — report both.
- **Bone loss collapsing out-of-domain** (0.92 → 0.7–5.4%) reads badly presented as a bug; it
  reads as a genuine, well-measured finding presented as one, since it is corroborated on two
  independent external datasets.

**Do not claim the Tufts-mirror finding as a discovery until §4's novelty item is resolved.**
If it turns out to be undocumented in the source paper, it is a strong, concrete methodology
contribution (a public dataset error nobody else has flagged); until then it belongs in the
paper only as "a labelling convention this pipeline had to detect and correct," not as
"discovered a previously unreported dataset defect."

**Bottom line:** ISBI 2027 (S-grade) is a realistic target on Framing A — the 6-cohort external
validation, the Lever-1 decomposition and the reproducible deployed system are competitive
independent of any single score. Nobody can promise acceptance; a journal fallback keeps S in
reach either way. The odds are set by whether the compliance blockers close, not by the numbers.

### 2 September 2026 (session 3c) — score-improvement council

**The ask:** lift the pipeline's metrics enough to make an S/A-grade publication realistic; GPU funding offered.

**Frame first — grade is set by venue, not metrics.** A reputable journal is **S** regardless of edition; ISBI 2027 (24th) is **S** if accepted. Metrics work cannot raise the ceiling above S — it raises P(accept) and lets an S venue be a realistic target rather than a hopeful one. **What actually threatens the grade and no GPU touches:** the four compliance blockers (Tufts Drive licence breach, IRB not started, DENTEX/Ningxia licences unread, SDH de-id) — account-owner actions that gate ISBI entirely and half-gate a journal ethics statement; and the ISBI 4-page hard cap, which *more results make worse*.

**Three decisions (all put to the user as a structured choice; all three recommendations accepted):**

1. **Framing: A+.** Keep the evaluation-protocol contribution as the spine (only 2 of 49 task-relevant papers validate externally); add the levers as positive systems results — "we used the protocol to diagnose three failure modes and fixed them." **Not** a pivot to a positive-number systems paper (Framing B), which the 1 Sep council rejected because the constant beats the *tooth-level* metric structurally. Lever A supports thesis (b) "end-to-end hides stage-wise failure"; Lever B attacks thesis (a) "tooth-level is base-rate dominated" directly. Neither undermines the paper.
2. **Venue: journal primary, ISBI optional.** Full A+B(+D) paper to a journal (IEEE JBHI or Computers in Biology and Medicine — both S, both demonstrably in scope, no page limit; verify Scopus on the official list before committing, and get the mentor's call on which). A cut ISBI 2027 short paper (protocol + Lever-A headline only) in parallel **only if** the compliance blockers close by mid-October. ISBI deadline 26 Oct 2026; 4 pp hard (all technical content, figures and tables, in the first 4 pages; verified 2 Sep against the official CfP).
3. **Levers A + B now, D if time; skip C and E; budget ~₹4,000.** Lever A = the single highest-leverage move (Lever 1 proved 58→93% in-domain; its guard failure is a fixable build flaw). Lever B flips the caries narrative if a lesion detector beats the constant on its own metric. Lever D (bone-loss second corpus via BRAR — now downloadable, which §8.13 predates) removes the ugliest limitation but has the most data-wrangling risk, so it is opt-in after A and B. C (gate v5) is base-rate limited by construction; E (bigger arch) is marginal.

**Pre-registrations drafted** (`outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md`, `outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md`) — bars open to one review round by the user/mentor, frozen once builds start.

**Ordering rule if the tracks conflict for time:** the compliance track and the journal manuscript win. A lever not finished cleanly is dropped, not rushed.

**Honest grade expectation, unchanged from the 1 Sep council:** journal accept → S (realistic on the 6-cohort + lever-fix story). The binding risk is the compliance blockers closing, not the numbers.

### 3 September 2026 — Lever A Guard-2 diagnosis council

**The ask:** Tufts test box mAP falls (0.724 → 0.585) while every other cohort improves — fixable mistake? another way (the Tufts masks)? check + verify, plan, council.

**Checked + verified** (local CPU, no GPU; `outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md`, `RESULTS_LOG` 2026-09-03c): hypothesised a box-convention clash (DENTEX GT boxes ~1.5× Tufts area) — **tested against the trained models, refuted**: Arm 3C's Tufts-test boxes are *closer* to Tufts GT than Control B's, matched-pair IoU unchanged (0.62 → 0.64). Real mechanism = **capacity dilution**: at Tufts 33 % of the mix the detector misses 37 % more Tufts teeth and emits 42 % more spurious boxes — monotonic in Tufts training share (100 % 0.724, 52 % 0.647, 33 % 0.585). Metric is also **box-vs-mask-capped**: the deployed *segmentation* Stage-1 scores 0.810 on this split, every detection model ≤ 0.724 (DENTEX/Kaggle/UFBA have no masks, so the levers must use `detect`).

**Council (5 voices), unanimous near term:** no more GPU on the detector. The diagnosis is a clean quantified ablation result → `PAPER_MATERIAL.md` §8.10. Lever A stays ABLATION; nothing re-opened, no bar moved. A real “another way” exists (multi-corpus **segmentation** with pseudo-masks, or multi-corpus pretrain → **Tufts fine-tune**) but both are Lever-D-scale and sit **behind Lever B and behind Track A**. Any retry = a new pre-registration (Lever A2); deployed detector stays `models/11` until it passes cleanly.

**Plan:** Phase 0 now (no GPU) — GT-box overlays + FN/FP at conf {0.10, 0.25, 0.40} incl. Arm 4C, then write §8.10 + §8 Known Limitations. Phase 1 gate: Lever A2 only if Lever B yields no adoptable headline **and** ≥ 2 weeks schedule slack **and** an explicit decision it's worth a full downstream re-measure. Phase 2 (if gated in): probe pretrain→fine-tune (~₹400) before segmentation (~₹1,000), identical Lever A acceptance rule.

---

## 6. The R1 GPU session — run order, JarvisLabs

> ✅ **R1 (27 Aug), Lever 1 (1 Sep), Lever 2 (2 Sep) and Lever A (3 Sep) are all DONE. No
> instance is running.** This section is the validated runbook for the next rented job. R1 cost
> **₹249.19**; Lever 1 **₹267.84** and Lever A **~₹735** (3 arms + pause/resume overhead) both on
> an RTX PRO 6000; Lever 2 **₹256.61** on an A100-40GB. **Balance now ₹1,732 (§8).**
> **Lever A exact scripts + a 'verify every number' cheat sheet:** `models/15_detector_multicorpus_leverA/repro/` (README there). Cold-start hub: `outputs/lever_A_multicorpus_detector_v2/STATUS.md`.
>
> **Lever A added two lessons to the runbook (see §8):** (1) `jl resume` gives a fresh container
> — re-install `ultralytics==8.4.127 --no-deps` + matplotlib/opencv-headless/thop/polars each
> resume. (2) On a slow/jittery home upstream, `jl upload` of a >400 MB tar is unreliable — use
> `rsync --partial --append` over the ssh endpoint in a retry loop with a sha256-verified
> completion check.
>
> **The runbook that worked for Lever 1, added to the R1 rules below:** `tar` the dataset to ONE
> file (per-file upload is the bottleneck), sha256 both ends, extract, **`find … -name '._*'
> -delete`** (macOS tar ships AppleDouble files that double the counts), re-run the geometry gate
> **on the rented box**, pin `ultralytics` to the training version that produced the frozen
> models (8.4.127) so downloaded `best.pt` loads on the Mac, score arms **on the Mac** (same
> machine as the same-day control), destroy the instance the moment weights are down.
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

**Editing / committing these files — two gotchas the friend's macOS clone will feel:**
line endings are **not uniform** — `transfer.md`, `.gitignore`, `models/README.md` and
everything under `docs/results/` are **CRLF**; scripts, `docs/session-memory/*`,
`models/*/run_summary.txt` and the other READMEs are **LF**. Edit files in place (don't run a
blanket EOL-normalizer — it makes 300–600-line no-op diffs, which happened twice on 2 Sep).
And before pushing, `git diff --diff-filter=D --name-only origin/main..HEAD` — a `git rm --cached`
of any tracked artefact silently deletes it from the friend's tree on pull (the 43 MB
`models/12`/`12a` heads are tracked and not on Drive).

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
| **Kaggle "dual-labeled" corpus** (3rd FDI corpus + Lever A) | `data/kaggle_dual/` (`images1/` + `labels/`, 749 MB; entirely gitignored) — **downloaded to this Mac 2 Sep** | Kaggle slug **`zwbzwb12341234/a-dual-labeled-dataset`** (553 MB zip; licence *unstated*). Added `33f8b6e` for head v3 (`models/12`, ablation). 2,066 LabelMe polygon JSONs, 500 images with a match → **499 usable** (1 byte-identical dupe) / 13,166 teeth. `enumeration_v1/` crops (not present here) rebuild with `scripts/kaggle_dual/build_enumeration_crops.py`. `scripts/kaggle_dual/` IS tracked. Full record: `data/README.md`. |
| **CariesXrays YOLO detect set** (Lever 2) | `data/cariesxrays_det/` (~4 GB, gitignored) | Built 2 Sep by `scripts/yolo/build_cariesxrays_detector_dataset.py` — 6,000 VOC images → YOLO, single class `decay`, this project's own seed-42 4,800/1,200 split. Regenerable from the CariesXrays benchmark; never commit. `models/14_cariesxrays_lever2/`. |
| **Multi-corpus detector dataset** (Lever 1 / B1) | `data/detector_multicorpus/` (~816 MB, gitignored) | Built + geometry-gated 1 Sep by `scripts/yolo/build_multicorpus_detector_dataset.py` (Tufts 700 + DENTEX `quadrant_enumeration` 634 → YOLO `detect`, detector-rotated frame). 1,334 train / 150 val / 150 test; val+test are Tufts-only and reproduce the canonical **3,794 / 3,924** box counts exactly. Regenerable; never commit the images. A `detector_multicorpus.tar` for upload = 817 MB one file. |
| **Multi-corpus detector dataset v2** (Lever A) | `data/detector_multicorpus_v2/` (1.1 GB, gitignored) | Built + geometry-gated **2 Sep** by `scripts/yolo/build_multicorpus_detector_v2_dataset.py` — Tufts 700 + DENTEX 561 + Kaggle-dual 449 + UFBA-425 382 → YOLO `detect`, detector-rotated (CCW) frame. val/test = Tufts frozen only (canonical 3,794/3,924 reproduced). `train.txt` (4 corpora × 700, Arm 4C) and `train_3corpus.txt` (3 × 700, Arm 3C = primary). Geometry gate median IoU 1.0000. Regenerable; never commit. `outputs/lever_A_multicorpus_detector_v2/STATUS.md`. |
| **UFBA-425** (Lever A corpus #4) | `data/ufba425/` (51 MB, gitignored) | Downloaded 2 Sep from figshare `10.6084/m9.figshare.29827475`. **Licence CC BY 4.0** (figshare API). 425 panoramic images (`numbering_xrays/`) + YOLO-txt tooth boxes (`boundinng_boxes/`) + `metadata.csv` (per-tooth FDI). ⚠️ 640×640 square Roboflow export — aspect-distorted (see §3 Lever A). |
| **Lever 1 detector weights** (ABLATION) | `models/13_detector_multicorpus_lever1/*.pt` (2 × 49 MB, gitignored) | `controlB_tuftsonly_best.pt` (sha256 `104564f3…`) and `arm_multicorpus_best.pt` (sha256 `5bc24b71…`). NOT the pipeline default — see `run_summary.txt`. Kept on local disk only. |
| JarvisLabs instances | Account-level | **None running, none paused — verified 3 Sep after Lever A** (instance 496005 destroyed after the 3-arm run + weight download; balance ₹1,732). **Pause/resume gotcha, learned 3 Sep:** `jl resume` spawns a NEW container id + IP and does NOT keep pip installs (`ultralytics` had to be re-installed) — `/home` persists but the conda env does not; and a slow home upstream (~75–400 KB/s, jittery) makes `jl upload` of a >400 MB tar unreliable — use `rsync --partial --append` over the ssh endpoint in a retry loop, sha256-verify. History: R1 destroyed 27 Aug; Lever 1 on an RTX PRO 6000 (491623, ₹268); Lever 2 on an A100-40GB (492535, ₹257); Lever A on an RTX PRO 6000 (495956→496005 after pause/resume, ~₹735). **Windows `jl` gotchas:** the `jl` on PATH is broken (`Python311` removed); use `%LOCALAPPDATA%\Programs\Python\Python313\Scripts\jl.exe`. Every `jl upload`/`exec` with a remote `/path` needs `MSYS_NO_PATHCONV=1`. A `jl exec` with `nohup … &` detaches, but the local `jl exec` client hits the 2-min Bash-tool timeout — that does not kill the remote job. |
| **Kaggle API token** (added 2 Sep) | `.env` at the repo root — **gitignored** (new `# Secrets / local env` block in `.gitignore`: `.env`, `.env.local`, `kaggle.json`, `.kaggle/`). Load with `set -a; source .env; set +a`. | `KAGGLE_API_TOKEN=KGAT_…` (the user pasted it in the 3c session — treat as low-sensitivity, rotate at kaggle.com/settings if wanted). `kaggle` CLI 2.2.4 installed into `/opt/anaconda3` (numpy pin unaffected — verified 1.26.4 after). |
| **macOS Python — which one** | project env is **`/opt/anaconda3/bin/python3` (3.12.12)** — has torch 2.2.0, ultralytics 8.4.127, cv2 5.0.0, numpy 1.26.4. | ⚠️ `which python3` on PATH is the **homebrew 3.14** (`/opt/homebrew/bin/python3`), which has NONE of the deps and is PEP-668 locked. Always call `/opt/anaconda3/bin/python3` explicitly. Housekeeping: a corrupted `~orch-2.5.1` partial install in `/opt/anaconda3/lib/python3.12/site-packages/` throws pip warnings — pre-existing, harmless. |
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
