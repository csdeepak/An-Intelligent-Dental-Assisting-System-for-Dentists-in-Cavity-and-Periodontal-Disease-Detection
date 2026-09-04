# 2026-09-04a — Lever B: pre-reg frozen, both arms built, trained, evaluated

**Session goal:** execute Lever B end to end (per `START_HERE.md`'s Steps 1–5) — freeze the
pre-registration, build the two training datasets, wire a lesion-detector decision mode into the
frozen eval scripts, run B-single, train + evaluate B-pooled, apply the pre-registered acceptance
rule. On the Windows machine, continuing `2026-09-03f`'s ownership split.

Result: **both arms complete, real signal in both directions, Sec 6 not yet met (Ningxia
missing), B-pooled is clearly the better arm to carry forward regardless.**

## What was done

### Pre-registration frozen (4 defects fixed before any GPU spend)
Read `PRE_REGISTRATION.md` closely before building anything and found four problems, all fixed
in place and committed (`ef3f453`) rather than discovered mid-build:
1. The CariesXrays "fresh 1,500 draw, seed 43" is arithmetically impossible — the raw release is
   exactly 6,000 = 4,800 train + 1,200 val, nothing left to draw. Fixed: the eval cohort is the
   existing disjoint 1,200-image val split (stronger than the original plan, not weaker — uses
   the full held-out pool, needs no new randomness).
2. The confidence-tuning clause ("tune on the CariesXrays held-out val") became circular once (1)
   made that val set the eval cohort itself. Fixed: frozen flatly at 0.25, no tuning clause.
3. Sec 9's "~5,500 images" for B-pooled undercounted Sec 3's own balancing instruction by ~2x —
   checked against Lever A's actual balancing code (`build_multicorpus_detector_v2_dataset.py`),
   which replicates the smaller corpus up to the larger one's size, not concatenates. Corrected
   cost estimate to ~9,600 images/epoch, ~₹600/₹1,200 (was ~₹300/₹600).
4. Sec 4/6 never specified how a lesion detector's predictions become a tooth-level verdict.
   Added: argmax-containment (each predicted lesion box assigned to the tooth box it overlaps
   most, not centroid-in-any-box), reusing the containment primitive already used for GT matching.

### New code
- **`scripts/dentex/build_dentex_caries_boxes.py`** — DENTEX `quadrant-enumeration-disease` →
  YOLO caries boxes. Verified against the real JSON before writing anything (705 images, 650 with
  ≥1 caries box, 2,767 boxes — matched the pre-reg's numbers exactly). Found and handled a real
  leak risk: one MD5-identical pair between this training pool and the DENTEX eval release
  (`test_181.png` == `train_332.png`) — already excluded from the current eval cohort for an
  unrelated reason, but the script now verifies this LIVE against the current exclusion list
  rather than trusting that it stays true.
- **`scripts/yolo/build_lever_b_pooled_dataset.py`** — balances CariesXrays (4,800) + DENTEX-
  caries (650→4,800 replicated) into one 9,600-line shuffled train list, per Lever A's exact
  recipe. 0 cross-corpus leakage verified.
- **`scripts/yolo/train_lever_b_pooled_detector.py`** — copies B-single's training recipe
  verbatim except the pooled train set. Two real bugs caught before/during the actual GPU run
  (see Decisions).
- **`scripts/eval/lever_b_bootstrap.py`** — paired cluster bootstrap (reuses `bootstrap_ci.py`'s
  primitives) + the Sec 6 rule applied mechanically. Takes `--arm-tag {B-single,B-pooled}`.
- **`--decision lesion-detector`** wired into `lesion_localization.py`, `ningxia_external.py`,
  `cariesxrays_external.py` — shared mapping (`ningxia_external.lesion_preds_to_tooth_idx`,
  argmax-containment) and a shared, deliberately-NOT-`detect_upright` inference call
  (`run_lesion_detector`) so all three cohorts score any lesion model identically.
- **`cariesxrays_external.py`** gained `--manifest`/`--manifest-split` to filter to the frozen
  1,200-image val cohort (replaces the abandoned "seed-43 draw").

### GPU work
- **B-single** (Lever 2's frozen `models/14/weights/best.pt`, zero GPU) run through the frozen
  eval on both cohorts.
- **B-pooled**: rented a JarvisLabs **RTX-PRO6000** (instance 496516, IN1, ₹179.01/hr) — A100
  (both 40GB and 80GB) was unavailable at rental time, confirmed live via `jl gpus`, not assumed.
  Uploaded the 6.4GB dataset as 27×250MB chunks with per-chunk retry (the connection reset/timed
  out several times; every chunk eventually landed, sha256-verified byte-identical to the local
  build after reassembly). Trained, early-stopped at epoch 54/120. Downloaded the full run
  archive to `models/16_lever_b_pooled/`, sha256-verified, then destroyed the instance.
  **Spend: ₹546.93** (₹1,731.77 → ₹1,184.84).

## Decisions made

- **Batch=16, not the nominal 32.** *Reason:* B-single's own training (`RESULTS_LOG` 2026-09-02b)
  hit CUDA OOM at batch=32 on an A100-40GB and fell back to 16 — that IS the recipe that produced
  the frozen 0.482 AP checkpoint. Using 16 for B-pooled too avoids repeating a known failure on a
  billed instance AND keeps the two arms' realised recipes identical, not just nominally so.
- **`scp` over raw SSH instead of `jl upload` or `rsync`.** *Reason:* the documented lesson
  (`transfer.md` §6) says `jl upload` is unreliable above ~400MB and prescribes `rsync --partial
  --append`; this Windows Git-Bash has no local `rsync`. Chose a hand-rolled chunked-scp-with-
  retry instead of introducing a new dependency (e.g. `pacman -S rsync`) mid-task.
- **RTX-PRO6000 over waiting for A100.** *Reason:* A100 (both sizes) was unavailable; RTX-PRO6000
  is the exact card Lever 1 and Lever A already trained on successfully. Flagged the ~2x hourly
  cost plainly before renting rather than silently absorbing it — actual spend still landed under
  the revised ceiling because the card is faster per-step (~2.3 min/epoch vs. an A100 extrapolation
  of ~4.25 min) and training early-stopped well short of 120 epochs.
- **Report the DENTEX result as a "statistical tie," not force it into the pre-reg's outcome
  bins.** *Reason:* Sec 6's outcome table enumerated discrete cases ("wins in-domain, fails to
  transfer" among them); B-pooled's actual DENTEX result (CI includes zero against both
  comparators, i.e. no longer losing but not yet significantly beating either) doesn't match any
  of them cleanly. Recorded as its own honest description rather than rounded to the nearest bin.
- **Monitor script: never destroy on ambiguous state.** *Reason:* stated explicitly by the user
  ("stop the instance as soon as it gets done"). Built the check as SSH-reachable AND
  success-marker-present AND weights-file-present AND post-download-sha256-match, all four,
  before calling `jl destroy`. This paid off directly — see Open questions / what went wrong.

## What went wrong, and why it didn't cost anything

**The monitor's first real trigger was a false negative, by design.** Ultralytics silently
reinterpreted `train_lever_b_pooled_detector.py`'s `project="runs_lever_b"` as relative to its
own internal `runs_dir` setting, landing the real weights at
`runs/detect/runs_lever_b/lever_b_pooled_yolo11l-2/weights/` (also picking up a `-2` suffix from
a stale directory left by the crashed first launch attempt) instead of the plain
`runs_lever_b/lever_b_pooled_yolo11l/weights/` path the script's own arguments implied. The
monitor correctly saw the training process had exited AND the success marker had printed, but
did not find `best.pt` at the path it was told to expect — and, exactly as designed, refused to
touch the instance rather than guess. Found the real path directly (`find /home/lever_b -name
best.pt`) with the instance still safely running and untouched; downloaded, verified, destroyed
by hand. **No cost or data was lost** — the conservative design is the reason why.

A second, smaller loss: a local background CPU eval job (CariesXrays lesion-detector, B-single)
was silently killed partway through (1,000/1,200 images) by what looks like a session-lifecycle
event unrelated to this task (a background-task notification arrived with a fresh session-folder
path, implying the *previous* Claude Code session was torn down and took its tracked local
background processes with it). The GPU training itself was unaffected, specifically because it
was launched via `nohup … & disown` on the remote box — fully detached from this session. The
killed CPU job was simply relaunched; it re-ran to completion with no side effects (it's a stock
frozen-eval script, safe to re-run).

## Results (see `RESULTS_LOG.md` 2026-09-04f / 2026-09-04g for the full numbers + sources)

| cohort | gate v3.0 | constant-molars | B-single | B-pooled |
|---|---|---|---|---|
| DENTEX | 44.3% | 48.9% | **8.6%** [5.5,11.9] — decisive loss | **45.5%** [40.9,50.1] — statistical tie |
| CariesXrays-val | 31.7% | 56.2% | **69.4%** [67.4,71.3] — decisive win | **68.4%** [66.4,70.4] — decisive win, ~unchanged |

Sec 6 acceptance rule: **not met** by either arm with 2 of 3 cohorts scored (1 of 2 passes both
times). Ningxia is the deciding cohort and is not on this machine.

## Open questions

1. **Ningxia** — the actual blocker on a real Sec 6 call. Not on this machine (checked the eval
   script's real default root, `~/Downloads/Capstone/ningxia_local`, not just `data/ningxia/`
   which holds only `manifest.csv`). Needs the account owner.
2. Is DENTEX's move from "loses decisively" to "ties" *itself* enough signal to guess how Ningxia
   will go? No — it's one data point, and Ningxia's caries lesions are geometrically very
   different (tiny focal blobs vs. DENTEX's larger polygons, per `ningxia_external.py`'s own
   docstring). Genuinely unknown until run.
3. If Ningxia arrives and still leaves Sec 6 unmet (e.g. B-pooled ties or loses there too) — is a
   partial/qualified write-up ("closes the domain gap without net-beating the constant") worth a
   paper section on its own? Scoping call, not answered here.

## Next steps

1. **Get Ningxia onto this machine**, then run the same frozen eval (`--decision lesion-detector
   --lesion-model models/16_lever_b_pooled/.../best.pt`) + `lever_b_bootstrap.py` a third time —
   all the code for this already exists and needs no changes.
2. Once Ningxia is in: apply Sec 6 for real, write the actual adoption verdict, update
   `model_metrics.md` + `PAPER_MATERIAL.md` only if adopted (neither has been touched this
   session — correctly out of scope until Sec 6 is actually met).
3. Fold this session's findings into `PAPER_MATERIAL.md` regardless of the final verdict — the
   domain-transfer-recovery result (not one of the pre-registered discrete outcomes) is citable
   on its own.
4. Commit this session's code + docs (pending user confirmation — nothing beyond the pre-reg
   freeze commit has been pushed).
5. Update `transfer.md` §1–§4 (this file's companion task, not yet done as of writing this).
