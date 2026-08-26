# CURRENT STATE — read this first

**This file is the project's living state-of-play.** It answers "where are we, what is done,
what is next" for a session that is starting cold. It is **rewritten, not appended to** —
unlike `docs/results/RESULTS_LOG.md` (append-only history) and `docs/session-memory/`
(one file per session, never edited). Those two are the record; this is the snapshot.

**Last updated: 25 August 2026 (full rewrite — all six stages running, deployed, and
externally validated on four hospitals).**

> **Maintenance rule (CLAUDE.md rule 5):** whenever a session finishes something, decides
> something, or changes what should happen next, update this file **before the session ends**.
> A stale snapshot is worse than none — it has already cost this project a wasted search
> (§7), and, this session, several stale README claims that read as done-when-they-weren't or
> vice versa. Verify against the working tree before writing anything here.

---

## 1. Where we are, in five lines

**The pipeline runs end to end, is deployed, and has been measured on four hospitals it
never trained on.** `run_inference.py` → all six stages; `app.py` + `Dockerfile` wrap it
unchanged for a browser demo. Caries went from unusable (84.9% false-positive-dominated) to
plausible (19.1%, precision 0.40) by rebuilding its negative class with 5,366 real healthy
teeth. **Bone loss is the one open technical failure** — 0.92 macro-F1 on Tufts collapses to
0.7% firing on DENTEX and 0.8–5.4% affected-tooth sensitivity on Ningxia — measured on two
independent external datasets now, not asserted from one.

**C2 (external validation) has real numbers**: zero leakage against all five internal corpora,
caries lesion agreement 22.6–43.3% across four Ningxia hospitals (DENTEX internal was 42.6%).
**C1 (VLM baseline) is the only headline paper contribution still at 0%** — deliberately
deferred to W5 by the plan, not forgotten. Phase III's checklist (system testing, V&V,
deployment, results, tables/graphs) is met on every item except one: `docker build` itself has
never actually run (daemon unavailable this session) — do that before relying on it. **60/60
tests pass, `verify_invariants.py` is 7/7.** We are on **W2 of the 8-week plan**
(`docs/research/MASTER_PLAN_2026H2.md` §5), implementation freeze **14 Oct**, ISBI **26 Oct**.

**The user's stated intent for the next stretch of work: implementation, not the paper draft**
— the draft happens last. **R1 (YOLOv11l-seg retrain) is the headline implementation item
left**, and the user has explicitly cleared renting a cloud GPU for it on JarvisLabs.

---

## 2. What is DONE — verified, not assumed

| Item | Evidence |
|---|---|
| **Detector** frozen, tagged `tooth-detector-a100-1024-v1.0` | `docs/research/T0.6_detector_reconciliation.md` §1 |
| **FDI enumeration head** — 22.9% → 46.5% end-to-end, frozen `fdi-enumeration-head-resnet18-v1.0` | `models/08_fdi_enumeration_head/run_summary.txt`; verified 4 independent audit passes this session, reproduces byte-for-byte |
| **Caries gate rebuilt** — 5,366 real healthy teeth (MD5-joined, 98.28% FDI agreement), frozen `caries-gate-resnet18-v3.0` | `models/09_caries_gate_v3/run_summary.txt`; 84.9% → 19.1% in-pipeline, precision 0.40 |
| **T0.1–T0.4 caries re-run closed** — both arms run, gap is noise (0.01–0.03 vs 0.27 epoch-to-epoch swing) | `RESULTS_LOG.md` 2026-08-25b |
| **Stages 5–6 built** — `run_inference.py` runs all six stages, image → per-tooth JSON + overlay | `RESULTS_LOG.md` 2026-08-24f (R4, paper claim C3); refactored 25 Aug into `load_models()`/`run_pipeline()`, verified byte-identical |
| **Lesion-localisation evaluator** — 42.6% agreement on DENTEX, no GPU | `scripts/eval/lesion_localization.py`, `RESULTS_LOG.md` 2026-08-25c |
| **C2 external validation on Ningxia** — 4 hospitals, zero leakage, first external numbers | `scripts/eval/ningxia_external.py`, `RESULTS_LOG.md` 2026-08-25d |
| **Deployment** — Streamlit app + Dockerfile, wrapping the pipeline unchanged | `app.py`, `Dockerfile`, `RESULTS_LOG.md` 2026-08-25f |
| **6 paper/review figures**, generated from saved artefacts only | `scripts/figures/make_paper_figures.py`, `docs/results/figures/paper/`, `RESULTS_LOG.md` 2026-08-25e |
| **Bone-loss binary + severity** trained (Tufts) | `models/03_.../run_summary.txt`, `models/04_.../severity_summary.txt` — **still untagged**, see §4 |
| **R1 seg dataset** built on the frozen split, ready to train | `data/tufts/dataset_seg/` — 26,005 instances, 700/150/150 |
| **R2 mask-aware cropping** implemented + unit-tested (**unwired** — needs R1's masks) | `src/crop_generator.py`, `tests/test_crop_generator.py` |
| **Environment fixed and pinned** — numpy<2, or `scipy.optimize` (the Hungarian assignment) silently breaks | `requirements.txt`, `RESULTS_LOG.md` 2026-08-24b |
| **All READMEs + this file** swept for staleness twice this session | `RESULTS_LOG.md` 2026-08-25e/f, this rewrite |
| Test suite | **60/60 pass**; `scripts/eval/verify_invariants.py` **7/7** |

**The pattern worth remembering, stated once rather than per-entry below:** every defect found
this session was in *documentation* or *methodology* — a stale claim, a metric applied outside
its valid range, an untested assumption — never in the core FDI/detection logic itself, which
has now survived four independent audit passes and reproduces exactly from frozen weights. The
discipline that found them: **verify every number against a saved artefact before writing it
down**, and when a check is cheap, run it even when the answer feels obvious. Two catches this
session existed *because* of that habit — the periodontitis mask-geometry check
(`RESULTS_LOG` 2026-08-25d) and the Ningxia IoU-threshold check — and both would have shipped
a false "the model fails externally" conclusion otherwise.

---

## 3. What is NEXT — implementation first, paper draft last

**User's explicit framing this session: continue implementation now; the paper draft is the
final step, not the next one.** Ordered by what actually blocks something else:

1. **R1 — YOLOv11l-seg retrain.** The one item needing a rented GPU, and the user has cleared
   renting on **JarvisLabs**. Detector recall (67.0%) is the binding constraint on everything
   downstream of it — Stage-2 end-to-end is capped at 67.0% no matter how good the numbering
   is, and DentFound's ablation (+20.35% precision, +23.01% recall, +23.11% F1 from instance
   masks) is now a citable justification, not an assertion. Config is **pre-registered**
   (`T0.6_detector_reconciliation.md` §2): imgsz 1024, batch 32, only model+data change — do
   not shrink the batch to fit a smaller card, that breaks the comparison. ~40 min on an A100.
   Runbook: §5 below.
2. **Bone loss is the standing open research problem, not just an admin item.** In-domain
   0.92 macro-F1 on Tufts; 0.7% firing on DENTEX; 0.8–5.4% affected-tooth sensitivity on
   Ningxia. Two independent external datasets now agree it collapses outside its training
   domain. No fix has been attempted yet — this is real implementation work, not a decision.
   Worth scoping explicitly before or alongside R1, since R1 is Tufts-side and might help both
   (detector and bone-loss are the two Tufts-trained stages, and the two that misbehave
   elsewhere — likely one root cause, not two).
3. **T0.5 — the Mild severity class (n=6) decision.** Zero compute, zero blocker, untouched
   since 15 Aug. The cheapest open item in the project; there is no reason this stays open.
4. **Version-tag the bone-loss weights.** Stages 4a/4b are the only trained models without a
   tag now that the enumeration head and caries gate v3 are both frozen. Trivial, just undone.
5. **Verify `docker build` actually completes.** Not run this session (daemon unavailable).
   Every static check passed (file paths, package list, CLI flag syntax verified by actually
   starting the process) but a real build has never happened. Do this before trusting the
   deployment demo for Review 1.
6. **C1 — VLM baseline.** Deliberately still at 0%; correctly deferred to W5 by the plan's own
   design. Do not pull it forward to fill idle time — starting it now risks doing it rushed
   alongside everything else rather than doing it properly in its own window.
7. **Start IRB paperwork** for the clinic dataset. Zero-cost, longest lead time of anything
   open, flagged since 15 Aug, still not begun.

**The paper draft is explicitly LAST**, per this session's instruction — not next, not in
parallel. `PAPER_MATERIAL.md` is already structured for it (§5–6 methods, §7 results, §8
limitations through §8.12, §9 the gap checklist) and the 6 figures are ready to drop in when
that phase starts.

---

## 4. Decisions PENDING — do not default into these silently

| Decision | Why it needs a human |
|---|---|
| **Bone-loss domain-shift fix — what approach?** Now backed by two independent external measurements, not a hunch. Options span R1 (shared Tufts-side fix), Ningxia-informed fine-tuning (would need care — Ningxia is locked, no tuning against it directly), or scoping it as a documented limitation rather than a fix. | Research direction, not a fact to look up |
| **What else to use `DENTEX/disease/` for**, beyond the Stage-2 eval set (164 leak-free of 250) and now the lesion-localisation source. The 91 `saglam` (healthy) teeth as a small real healthy class is still an open candidate use. | Scoping call |
| **Clinic data governance.** `index.csv` sits beside `images/` on a shared Drive, voiding the de-identification. Five actions in `clinical_dataset_provenance.md` §4a, all needing the Drive owner. | Not this repo's account |
| **Bone-loss weights have no version tag** — trivial to fix, listed here only so it doesn't get silently skipped again. | Just needs doing |
| **Retrain the Stage-2 head on DENTEX + Tufts?** The corpus is **built and verified** (42,755 crops, all 32 classes per split — `RESULTS_LOG.md` 2026-08-25h) but **no model has been retrained on it**. Two real risks to handle rather than ignore: Tufts teeth occupy a smaller share of the frame (median normalised height 0.177 vs DENTEX 0.231), a covariate shift in the `cy`/`bh` features the head consumes; and Tufts contributes 2.0× DENTEX's training rows, so naive concatenation lets it dominate the loss. Retraining also un-freezes a currently-frozen, hash-pinned model. | Whether to spend the run, and whether to weight/balance the corpora rather than concatenate |
| **Ningxia confirmed unusable for FDI training** (25 Aug) — no tooth-identity field in the manifest, no per-tooth label file anywhere, masks are binary {0,255} disease masks only. Not a pending decision, listed here so it isn't re-asked. `RESULTS_LOG.md` 2026-08-25g. | — (closed, informational) |
| **`split_v1` has a train/test leak** — `590.JPG` (test) and `591.JPG` (train) are byte-identical, so the frozen detector trained on one of its own test images (1 of 150). The Tufts crop builder works around it; the detector's reported test metrics have **not** been re-measured. `RESULTS_LOG.md` 2026-08-25h. | Whether to re-measure the detector, or document and move on |

**RESOLVED and kept for the reasoning, not because still open:**
- **How to fix FDI numbering** (22 Aug) — rank-order capped at 66.3%, learned head reaches
  80.2% on the same population. `RESULTS_LOG.md` 2026-08-22f through 24a.
- **The caries gate's negative class** (25 Aug) — MD5-joining the enumeration and disease
  subsets recovers 5,366 real healthy teeth; the earlier "not derivable from DENTEX" verdict
  was half right (filename join invalid, MD5 join is not). `RESULTS_LOG.md` 2026-08-25a.
- **Ningxia leakage policy** (25 Aug) — checked against all five corpora separately, zero
  overlap; the standing rule (never infer disjointness from a neighbouring pair) held.
  `RESULTS_LOG.md` 2026-08-25d.

---

## 5. The R1 GPU session — run order, JarvisLabs

The only job that needs renting. Everything else runs locally on the M4 Pro (ResNet18 work at
~287 img/s on MPS — minutes per job).

| Step | Action |
|---|---|
| 1 | Provision a JarvisLabs instance with an A100 (or equivalent holding **batch 32 @ 1024px**, ~17.9 GB — do not size down and shrink the batch, that breaks the pre-registered comparison). |
| 2 | Upload `data/tufts/dataset_seg/` (474 MB) and `models/06_yolo_detection_a100_run/best.pt` (for reference/warm-start if the plan calls for it — confirm against `T0.6_detector_reconciliation.md` §2 before assuming). |
| 3 | Fix `data.yaml`'s absolute `path:` for the rented machine before launching. |
| 4 | Run `python scripts/yolo/train_yolo_seg.py` — config is pre-registered, do not modify hyperparameters. |
| 5 | Bring back `weights/` and `results.csv`. Freeze and tag on return, same convention as every other model (`run_summary.txt`, SHA-256, version tag). |
| 6 | Re-run `scripts/eval/verify_invariants.py` and the Stage-2 eval after freezing — detector recall changing should shift the Stage-2 end-to-end ceiling, and that shift needs to be measured, not assumed. |

**What NOT to do:** don't rent for T0.5, the version tag, or IRB paperwork — none of those are
compute. Don't pull C1 forward to use the rented instance "while it's up" — it needs its own
properly-scoped session (W5), not a rushed add-on.

---

## 6. Where the documentation lives

`CLAUDE.md` loads automatically every session and points here. After this file:

| Question | File |
|---|---|
| Current numbers | `docs/results/model_metrics.md` |
| Full technical story + honest limitations | `docs/results/PAPER_MATERIAL.md` |
| What happened, when, and why (append-only) | `docs/results/RESULTS_LOG.md` |
| What to work on next | `docs/research/PUBLICATION_TODO.md` status block, sequenced by `MASTER_PLAN_2026H2.md` |
| Narrative of each session | `docs/session-memory/` (newest file) |
| Documentation layout | `docs/README.md` |
| **Pipeline code, and the three crop contracts easy to get wrong** | **`src/README.md`** |
| Entry points / how to run things, incl. the deployment app | `scripts/README.md`, and `scripts/{yolo,dentex,eval}/README.md` |
| Datasets: what is where, what is usable | `data/README.md` |
| Weights, version tags, what is tracked | `models/README.md` |
| **Google Drive links + what's in each** (checkpoints not in git) | `docs/EXTERNAL_DRIVE.md` |
| Paper/review figures | `docs/results/figures/paper/` |

Every directory containing code has a README; all were swept for staleness 25 Aug 2026 (twice
— a first pass, then a second pass that caught three more drifted claims the first missed).

---

## 7. Local state that git does NOT carry

| Item | Where | Note |
|---|---|---|
| DENTEX full release (~14 GB) | `~/Downloads/Capstone/DENTEX/` | Complete and verified. Subset map in `data/README.md`. |
| Tufts raw + rotated radiographs | `_repo_archive/datasets_workspace/` | 1,000 each; `Radiographs_rotated/` is what scripts expect |
| Tufts frozen split | `_repo_archive/datasets_workspace/outputs/eda_tufts/split_v1.csv` | Gitignored — which is why a previous session wrongly declared it lost |
| **Ningxia** | `~/Downloads/Capstone/ningxia_local/` (test splits, 2.4 GB) | **Connected, copied, evaluated 25 Aug.** Train (11.2 GB) deliberately left on the pen drive — locked external data. Zero leakage vs all 5 other corpora. |
| Clinic (SDH) data | Not on this machine | Governance-blocked |
| Python env | `/opt/anaconda3` (python 3.12) | **60/60 tests, 7/7 invariants.** torch 2.2.0 + MPS, cv2 5.0.0, ultralytics 8.4.127, scipy, sklearn, **streamlit 1.37.1** (added 25 Aug for `app.py`). ⚠️ **`numpy` must stay `<2`** — pinned 1.26.4 in `requirements.txt`; numpy 2.x silently breaks `scipy.optimize` (the Hungarian FDI assignment) at import. |
| Two gitignored checkpoints, on Google Drive | `docs/EXTERNAL_DRIVE.md` | `06_yolo_detection_a100_run/best.pt` + `09_caries_gate_v3/caries_gate_v3.pth`. **Present locally on this machine right now** (frozen here) — a Docker build run on this machine will bake them in; a fresh clone needs the manual Drive fetch described in that file. |
| Docker daemon | **Not running this session** | `open -a Docker` + 120s wait did not bring it up. `docker build` has never actually executed — see §3 item 5. |
| E2E instance / SSH keys | Account-level | No instance launched. Treat the `.pem` pasted on 20 Aug as compromised. |

---

## 8. History — the 20–21 Aug machine handoff (closed)

This file began as a one-off handoff to a second laptop. That handoff is complete: the
uncommitted work was committed and pushed, and the machine switch happened. Two of its claims
turned out to be **wrong**, and both are worth remembering as cautionary examples:

- It declared `outputs/eda_tufts/split_v1.csv` missing after an "exhaustive search". The search
  covered `C:\` and `D:\` — a Windows filesystem — while the repo lives on macOS. The file was
  there all along.
- Its §4 table said the Tufts data would need re-downloading. It was already local.

Full original text: `git show ad71ee4:transfer.md`.
