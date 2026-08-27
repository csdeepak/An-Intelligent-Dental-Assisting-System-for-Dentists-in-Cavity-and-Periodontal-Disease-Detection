# 2026-08-27 (second session) — Cold start, the last untagged models, and C2 re-measured

## Session goal

Come up to speed with no prior context, verify the state the previous session left, then work.
Three phases: (1) orientation, which turned into a rule-1 repair; (2) tag the bone-loss weights;
(3) re-measure C2 on Ningxia against the newly adopted seg detector. All zero-GPU.

## What was done

### 1. Verified the handed-over state rather than trusting it

Read `transfer.md`, `CLAUDE.md`, the 27 Aug session memory, `PUBLICATION_TODO.md`'s status
block and `MASTER_PLAN_2026H2.md` §5, then checked the claims against the working tree:

- **65/65 tests pass**, `verify_invariants.py` **all invariants hold** — with exactly the SKIPs
  §8 predicts for this machine (no DENTEX enumeration corpus, no caries gate).
- `run_inference.py:94` confirms `DEF_DETECTOR = models/11_yolo_seg_tufts_r1/best.pt`, so the
  adoption really is wired, not just written down.
- Working tree clean at `6c79725`; `models/11_yolo_seg_tufts_r1/best.pt` present (53.3 MiB).

### 2. Found that rule 1 item 3 had not been executed

2026-08-27b/d/e went into `RESULTS_LOG.md`, `model_metrics.md` and `transfer.md`. They did
**not** go into `PAPER_MATERIAL.md` or the root `README.md`. Established by grep, not by
impression: `PAPER_MATERIAL.md` contained **zero** occurrences of `58.3`, `0.8100` or `70.6`,
and still asserted the old story in three separate places.

So the largest single result this project has recorded (+12.0 points end-to-end) and a changed
Stage-1 default were absent from the one document `PAPER_MATERIAL.md` exists to be — the source
the paper is written from.

Propagated into `PAPER_MATERIAL.md` §7.1 (seg table, the missed mask bar, the withdrawn run as
a methods note), §8.5, §8.10, §9; and into `README.md`'s stage table, metrics table,
limitations blurb and publication assessment.

### 3. The actual bug: a fresh clone could not work, and would not say why

`README.md`'s clone-and-run recipe said to fetch `models/06_yolo_detection_a100_run/best.pt`.
The pipeline default had moved to `models/11_yolo_seg_tufts_r1/best.pt` — **which is not on
Drive**. Following the README exactly gets you the wrong checkpoint and then a missing-file
error naming a file the README never mentioned.

Fixed: the recipe now names the real default, flags that it is not yet uploaded, and documents
the `--detector` fallback to the bbox detector along with its honest cost (46.3% end-to-end,
not 58.3%).

### 4. Docker is closer than the docs think

`transfer.md` §3 item 7 has said "daemon unavailable every session so far" for days. On this
machine `docker version` reaches the Docker Desktop named pipe and reports it missing — i.e.
**the CLI is installed and only the engine is stopped**, which is a one-click user action, not
a missing dependency. Re-flagged as the cheapest unblockable item here.

## Phase 5 — `docker build`, executed for the first time

Started Docker Desktop and ran the build. **It completes, and the demo runs**: container up,
`/_stcore/health` healthy, Streamlit serving the upload widget, and all seven checkpoints
loading inside the container. `import cv2` works — the failure the Dockerfile warns only shows
at container start — and numpy is 1.26.4 with the Hungarian assignment intact. §3 item 7 closed.

**Two real defects found by actually running it:**
- The image is **not CPU-only** despite the Dockerfile saying so. Nothing pins a CPU wheel index,
  so pip pulled the CUDA torch build plus ~2 GB of NVIDIA libraries. `torch 2.13.0+cu130` with
  `cuda_available: False` — a CUDA build that can never use CUDA.
- **torch is unpinned** (`>=2.0.0`), so the container runs 2.13.0 while every published number
  was measured on 2.2.0. numpy is pinned; torch is not.

Both change the deployment artefact and need a rebuild to re-verify, so I proposed rather than
silently applied them — **then, on request, applied and re-verified both.** Torch now installs
first from the CPU wheel index, pinned to 2.2.0 (in the Dockerfile, not `requirements.txt`,
since the two machines run different torch versions and both pass the suite). **Image
11.2 GB → 4.69 GB, −58%**, and the rebuilt container was re-verified end to end.

The durable part is not the fix but the **guard**: a build-time assertion that the torch wheel
is not CUDA, numpy is 1.x, and `linear_sum_assignment` runs — so the *build* fails rather than
the defect surfacing in a live container. Both failure modes were previously silent. This is the
same "enforce in code, not documentation" move the Tufts geometry fix made on 27 Aug.

**A self-inflicted detour worth remembering.** The first build's CLI looked hung for ~25 min
after `naming to … done`. It wasn't — the final `unpacking` step takes **591.8 s** for an image
this size and prints nothing. I killed it, which left the image config committed but its layer
snapshots incomplete: `docker image inspect` succeeded while every `docker run` hung, looking
exactly like a broken daemon. Running an unrelated image (`nginx`) worked and isolated the fault
to our image; a clean rebuild fixed it. *A silent step is not a hung step, and the way to tell a
broken environment from a broken artefact is to try a known-good artefact in the same
environment.*

## Phase 6 — bone loss: decided, not deferred

The user chose to **report the bone-loss domain-shift failure as a measured limitation** rather
than attempt a fix before the freeze. Written up as `PAPER_MATERIAL.md` §8.13.

The decisive fact, established while scoping it: **the Stage-2 combined-training lever does not
transfer, because DENTEX has no bone-loss labels.** Stage 2 worked on two corpora because both
label FDI codes; checked DENTEX's eight finding types (caries, curettage, root canal, extraction,
impacted, periapical lesion, fracture, healthy) — none is alveolar bone loss. So the "most
promising untried lever" recorded in `transfer.md` for days was never actually available. Worth
catching before it consumed GPU budget.

What makes the limitation defensible rather than an omission: two independent external datasets
agree, with different GT formats and different metrics, and today's detector swap **localised the
cause** — Stage 2 +12.0, caries +7.7, bone loss nothing. A limitation backed by a falsified
causal hypothesis is stronger than a hurried fix.

## Phase 7 — DENTEX fetched, environment rebuilt under us

Fetched the DENTEX subsets the repo actually uses: **1,390 images + 3 JSONs, 6.0 GB**, skipping
~8,875 drive entries that `data/README.md` records as unused or derived. Wrote it as a committed,
resumable, integrity-checking script rather than an ad-hoc command.

**Mid-fetch, the machine's Python 3.11 install lost its interpreter** — `python.exe` and the DLLs
vanished while `Lib/site-packages` remained. Not caused by anything I ran. Rebuilt on 3.13 at the
user's direction.

**A trap worth carrying: Python 3.13 cannot satisfy this repo's `numpy<2` pin.** No numpy 1.x
wheel exists for cp313, so pip silently builds it from source with MSYS2's MinGW toolchain,
producing a numpy that prints "CRASHES ARE TO BE EXPECTED" and emits invalid-value warnings at
import. I recommended 3.13 without checking wheel availability against the pin — my error.
Resolved with a numpy 2.x binary wheel, which `transfer.md` §8 already documented as the real
constraint (ABI-match, not the number 2).

**The payoff:** two invariants that had *always* SKIPped now run — and the caries v3 MD5 join
reproduces the documented **98.28%** FDI agreement over 260 shared images, from freshly downloaded
data on a different Python version. That is better evidence than the original measurement, because
it rules out local state.

**Two bugs of mine in the fetcher, found in the right order.** It failed 3 files while naming
neither file nor reason (FAILED printed only from the exception branch). Fixing the *logging*
first exposed the actual bug in one run: downloads land in `.part`, and `verify()` picked its
check by file suffix, so every JSON was opened with PIL. The images were unaffected only because
PIL ignores extensions — which is exactly why precisely the 3 JSONs failed. *A failure counter
without a reason is not a diagnostic.*

Also added `pytest` to `requirements.txt`: §8's fresh-clone checklist said to run the suite, but a
clean install could not.

## Phases 8-12 — the rigor block, C1, and the paper sections

After DENTEX landed, the remaining CPU work went quickly:

- **Confidence intervals** (§8.14) — cluster-bootstrap over IMAGES, not teeth, because 936 teeth
  come from 164 radiographs and errors cluster within an image. **Two of the day's own claims
  failed their intervals** (detection-recall +3.3 pp and internal lesion agreement +2.3 pp) and
  were withdrawn in place. That sharpened the central claim rather than weakening it: the
  end-to-end gain is real and the recall gain is not, so the mechanism is precision, not recall.
- **Calibration** (§8.15) — caries gate ECE 0.136, systematically overconfident. Temperature
  scaling made ECE *worse* (0.152): the error is a shape, not a scale. Isotonic fixes it (0.043)
  but flips 18% of verdicts, so it was wired **confidence-only** and verdicts verified
  byte-identical against the pre-patch container report.
- **Bone-loss crop rebuild — attempted and REJECTED by its own geometry check.** Reading
  `02_bone_loss_dataset_construction.ipynb` settled why: the crops came from
  `Radiographs/Radiographs/`, the ORIGINAL un-rotated radiographs, which are not on this machine.
  Best reconstruction reached sensitivity 0.40 against a documented 0.83. Skipping the check would
  have produced a clean-looking ECE 0.039 from crops the model cannot classify.
- **Failure taxonomy** (§8.16, §8.17) — Stage-2's 58.3% shown to be detection-bound; the caries
  gate over-calls healthy teeth at the same rate as impacted ones, ruling out
  pathology-for-pathology confusion.
- **Stage 3/4 figures** (§8.18) — regenerated from committed artefacts, not recovered from the
  archive. The curves show heavy overfitting and that 0.9233 is the max of a noisy 32-epoch curve.
- **Related work + ethics** (§2.1, §8.19) — only **2 of 49** task-relevant papers validate
  externally; a keyword count would have said 13, because most say "no external validation".
- **C1** (§8.20) — the one GPU job. Qwen2.5-VL-7B scores **below a constant guess**. My own
  control script's verdict logic was wrong and printed the opposite conclusion; caught only by
  reading raw responses. Instance destroyed, ₹37.93 spent.

## Decisions made