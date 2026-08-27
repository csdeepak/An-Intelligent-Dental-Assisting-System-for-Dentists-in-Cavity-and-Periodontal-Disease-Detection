# 2026-08-27 — Cold start: R1's results reach the paper doc, and a fresh clone turns out to be broken

## Session goal

Come up to speed on the repo with no prior context, verify the state the previous session left,
and start work. Orientation turned into a rule-1 repair when the verification found that the
previous session's headline result had never reached the document the paper is written from.

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

## Decisions made

- **Repaired the docs before starting any new work.** The temptation was to pick up a backlog
  item; but an unpropagated result is exactly the failure mode `CLAUDE.md` was written against,
  and it was actively costing a fresh clone.
- **Did not rewrite the correctly-scoped historical tables** in `src/README.md` and
  `models/README.md`. Their 46.5% / 46.58% figures are real measurements on the bbox detector
  and are the honest basis for a head-vs-head comparison. Added a pointer saying so and naming
  the current number, instead of overwriting valid history with current-best.
- **Recomputed nothing.** Every figure written was copied from the 27 Aug entries and
  `run_summary.txt`. A propagation pass that quietly re-derives numbers is a second result, not
  a propagation.
- **Logged it as a milestone** (`RESULTS_LOG.md` 2026-08-27f) even though it produced no new
  number, because rule 1 counts a significant bug fix, and the fresh-clone break was one.

## Open questions

- **Does `docker build` actually pass?** Still unknown. Now blocked only on the user starting
  Docker Desktop.
- **Should `validate_fdi_assignment.py`'s defaults be realigned** to the current detector and
  head? 2026-08-27e deliberately left them on the old pair so historical numbers stay
  reproducible, at the cost of defaults that no longer describe the pipeline. That trade was
  never explicitly decided — it was inherited.
- **Is there a systematic check for "a `DEF_*` constant changed"?** This session's break came
  from a default moving without a grep for paths naming the old one. `verify_invariants.py`
  pins weight *hashes*; nothing pins the *documentation* that tells a human which file to fetch.

## Next steps

1. **Upload `models/11_yolo_seg_tufts_r1/best.pt` to Drive** — user-only action, recipe in
   `docs/EXTERNAL_DRIVE.md`. It is the single thing standing between this repo and a working
   fresh clone.
2. **Start Docker Desktop, then run the build** — closes a Review-1 blocker for zero compute.
3. Zero-compute backlog, all still untouched: tag the bone-loss weights, T0.5 (the n=6 Mild
   class decision), the Tufts Drive permissions fix, IRB paperwork.
4. **C2's Ningxia numbers are stale** on the old detector — blocked here (Ningxia is not on the
   Windows machine), so it needs the macOS machine or a fetch.

## Cost

Zero. No GPU. Balance unchanged at ₹650.81.
