# 2026-09-03b — Lever A: handoff hardening (no new results)

**Session goal:** make the Lever A record complete and cold-start-readable so a collaborator can
independently verify every number and continue with Lever B, without this conversation.

No model was trained, no number changed. This is a documentation-only follow-up to
`2026-09-03-lever-a-training-and-verdict.md`.

## What was done

- **Preserved the exact as-run scripts.** The Lever A orchestration scripts lived only in a
  session scratchpad (would not survive to a fresh clone). Copied verbatim into
  `models/15_detector_multicorpus_leverA/repro/` (tracked): `leverA_box_gate.py`,
  `leverA_train_all.sh`, `watch_leverA.sh`, `leverA_primary2.sh`, `leverA_guard1.sh`,
  `leverA_ningxia.sh`, plus a new `repro/README.md` mapping each script to what it did and a
  "verify every number" cheat sheet (CPU/MPS, ~15 min).
- **Pulled the Guard-1 raw evidence into the tracked tree.** The per-image agreement JSONs were
  in `outputs/{ningxia,cariesxrays_external}_leverA_{controlA,arm3c,arm4c}/` (gitignored). Copied
  to `outputs/lever_A_multicorpus_detector_v2/<arm>/{ningxia,cariesxrays}_caries.json` — the
  whitelisted Lever A tree — so `score_leverA_arm.py` runs against one directory and matches its
  own docstring example. ~1 MB total. Originals left in place (rule 3, never delete).
- **Rewrote `outputs/lever_A_multicorpus_detector_v2/STATUS.md`** as the cold-start hub: verdict
  table (all 3 criteria, per-cohort Guard-1 breakdown), "what it means / does not mean",
  full artifact index (tracked vs local-only), the one verdict command, the Lever B handoff, the
  dataset composition, and a collapsed historical appendix. The old file had three duplicated
  "Train / test lists" headers and a stale "Run plan (once the tar lands)" / "Next" section
  describing work already done.
- **Extended `models/15_detector_multicorpus_leverA/run_summary.txt`** with a REPRODUCE block
  (exact commands), a HANDOFF open-items list, and two clarifications: (a) `primary_bootstrap.json`
  has a stale `verdict` *string* (old "mAP < 0.75" rule) — numbers correct, `leverA_verdict.json`
  authoritative; (b) there is no Control B end-to-end / Guard-1 eval by design — Control B exists
  only to set the Guard-2 floor.
- **`transfer.md` §6** — added a one-line pointer to `repro/` in the Lever A runbook row.
- Verified: all numbers in the new docs trace to `{arm3c,arm4c}/leverA_verdict.json`,
  `<arm>/stage2_summary_head.json`, and `RESULTS_LOG` 2026-09-03b. `best.pt` sha256 in
  `repro/README.md` re-checked against `shasum -a 256` of the actual files (an earlier draft had
  two hallucinated trailing hex chars — corrected before commit).

## Decisions made

- **New session-memory file, not an edit to `2026-09-03-…`.** *Reason:* the context compaction
  changed the session id; house rule is one file per session, never edit a prior one. Suffix
  `b` matches the existing `2026-09-01b` / `2026-09-02b` style (not the README's `-b-`).
- **`RESULTS_LOG.md` left untouched.** *Reason:* the 2026-09-03 entry's "GUARD 1 RUNNING" line is
  resolved by the 2026-09-03b entry, which links back to it — that is exactly the append-only
  convention. Rewriting the earlier entry would violate rule 1.
- **Guard-1 JSONs copied, not moved.** *Reason:* `leverA_ningxia.sh` / `leverA_guard1.sh` write
  to the `outputs/*_leverA_*` paths; keeping those intact means the scripts still reproduce
  in place. The tracked copies are the handoff surface.
- **repro scripts kept verbatim, including hardcoded box IP / scratchpad path in
  `watch_leverA.sh`.** *Reason:* they are a record of what ran, not a reusable tool; the
  reusable tools are already in `scripts/`. `repro/README.md` says so.

## Open questions

1. **Guard-1 eval ran on MPS**, not the project's CPU-only norm (the head/gate auto-select MPS on
   this Mac). Internally consistent (all arms same device) and Control A reproduced the published
   CPU numbers exactly, so the paired comparison holds — but flag it if a reviewer asks. (Carried
   from `2026-09-03-…`.)
2. Whether the `models/15/*.pt` (and 11, 13, 14) Drive upload should block anything downstream —
   currently they are single-copy on local disk.

## Next steps

1. **Lever B** — lesion-detection caries path. `outputs/lever_B_lesion_caries_path/
   PRE_REGISTRATION.md` (freeze the bars with the user/mentor first). Data prep local: DENTEX
   `quadrant-enumeration-disease` → YOLO caries converter; seed-43 CariesXrays eval draw disjoint
   from the 4,800 training images. Then B-single (`models/14/best.pt`, zero GPU) + B-pooled (~₹300).
2. Commit this session's doc changes (explicit paths).
3. Fold the Lever A bidirectional-tradeoff result into the manuscript Stage-2 / external-validation
   sections (`PAPER_MATERIAL.md` §8.10 + §8.12a already carry it; `paper/main.tex` does not yet).
4. Bug-fix `ningxia_external.py` `--out`/`--tag` namespacing.
