# 2026-09-03d — future-work handoff for a collaborator's laptop

**Session goal:** update `transfer.md` and the corresponding READMEs so a friend can pick up the
remaining work (Lever B, and the deferred Lever A2) on a fresh laptop. Documentation only — no
code, no model, no new number.

Continuation of `2026-09-03c-lever-a-tufts-guard2-diagnosis.md` (its Next-steps item 4).

## What was done

- **New: `outputs/lever_B_lesion_caries_path/START_HERE.md`** — the friend's cold-start entry for
  Lever B: §0 "what a fresh laptop is missing" (datasets + the local-only weights, esp.
  `models/14/best.pt` = the B-single arm, not on Drive yet), the 6-step plan distilled from
  `PRE_REGISTRATION.md`, the optional no-GPU Phase-0 warm-up, and the hard rules.
- **`transfer.md`** — §1 line 23 "where the next session picks up" fully rewritten (was still
  "top up JarvisLabs, run Lever A"): now (1) Lever B via START_HERE, (2) optional Phase 0,
  (3) the weight-upload blocker for the friend. §1 line 9 gained the Phase-0 pointer. §3 Lever A
  block gained the Guard-2 post-mortem + Lever A2 pointer; §3 Lever B block now points at
  START_HERE and flags "bars NOT yet frozen". New §3 OPT-IN bullet for **Lever A2** (pretrain→
  fine-tune ~₹400, or multi-corpus segmentation ~₹1,000; gated behind Lever B + schedule).
  New §4 pending-decision row: "is an adoptable multi-corpus detector worth chasing?".
- **`README.md`** (root) — the detector-domain paragraph and the "second track" paragraph both
  gained the capacity-dilution diagnosis + the Lever A2 deferral + the START_HERE link; repro
  table gained a **Lever B** row and the `TUFTS_GUARD2_DIAGNOSIS.md` / `repro/diagnostics/`
  pointers.
- **`models/README.md`** — `models/15` row: added `repro/diagnostics/` to the tracked-files list.

## Decisions made

- **`START_HERE.md`, not editing `PRE_REGISTRATION.md`.** *Reason:* a pre-registration is a
  frozen-intent document; the operational "how to start" belongs beside it, mirroring Lever A's
  `STATUS.md` / `PRE_REGISTRATION.md` split.
- **Left `docs/research/` and `docs/README.md` untouched.** *Reason:* `docs/research/` is the
  separate workstream (CLAUDE.md rule 4); `docs/README.md` correctly scopes itself to `docs/`
  and the lever work lives in `outputs/` + `models/`, already reachable via `transfer.md` §3 and
  the root README repro table.
- **Called out the weight-upload blocker prominently.** *Reason:* the friend cannot run B-single
  (needs `models/14/best.pt`), the eval (needs `models/11/best.pt`), or Phase 0 (needs
  `models/15/*.pt` + `data/detector_multicorpus_v2/`) — none are on Drive. This is the real
  gate on the handoff and it is an account-owner action.

## Open questions

1. Which datasets the friend actually has access to — DENTEX/CariesXrays are on the Drives,
   Ningxia is restrictive/local-only. The user needs to arrange this.
2. Whether the friend freezes the Lever B bars or the user/mentor does (`PRE_REGISTRATION.md`
   §4–§6, one review round).

## Next steps

1. **User:** upload `models/11`, `models/14`, `models/15/*.pt` to Drive
   (`docs/EXTERNAL_DRIVE.md` has the recipe for `models/11`); share dataset access.
2. **Friend:** read `transfer.md` → §3 → `outputs/lever_B_lesion_caries_path/START_HERE.md`.
3. Freeze the Lever B pre-registration, then Step 2 (local data prep) — no GPU.
4. Optionally do Phase 0 of the Tufts diagnosis first (no GPU, paper material).
