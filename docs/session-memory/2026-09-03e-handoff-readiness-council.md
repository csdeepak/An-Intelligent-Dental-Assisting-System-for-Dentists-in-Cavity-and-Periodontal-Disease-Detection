# 2026-09-03e — handoff-readiness council + START_HERE hardening

**Session goal:** council the question "can the friend actually continue Lever B / Phase 0 without
interruption?", then fix every gap the council found. Documentation only — no code, no model.

Follow-up to `2026-09-03d-future-work-handoff.md` (which created `START_HERE.md` and updated
`transfer.md` + READMEs). This session verified all of it against the actual files and datasets.

## The council (4 voices)

**1 · The friend (cold clone).** "What blocks me?"
- `data/cariesxrays_det/` (the seed-42 CariesXrays split, B-single's training data) is **gitignored
  and present on no machine** — must be rebuilt with `build_cariesxrays_detector_dataset.py`.
- `models/14/best.pt` (= the B-single arm), `models/11/best.pt` (eval detector),
  `models/09/caries_gate_v3.pth` (comparator) are all **local-only / not on Drive**.
- Phase 0 is billed "no GPU" but **is not "no dependency"** — it needs the 514 MB
  `data/detector_multicorpus_v2/` + `models/15/*.pt`, none git-shareable. So on a fresh laptop
  Phase 0 costs the *same* upload round as Lever B — no scheduling advantage.

**2 · The QA / skeptic.** "What's wrong in the docs right now?"
- START_HERE's DENTEX-converter step was vague and partly wrong: it told the friend to use the
  CariesXrays "dims from decoded image, XML `<size>` 27.3 % wrong" trick — that is a **VOC-XML**
  gotcha; DENTEX is COCO JSON with correct `width`/`height` in the `images` block.
- The JSON has **`categories_3`**, not `categories` (which is absent) —
  `{0:Impacted, 1:Caries, 2:Periapical, 3:Deep Caries}`; the caries filter is
  `category_id_3 ∈ {1,3}`, already the project constant `CARIES_CLASSES` in
  `scripts/dentex/build_dentex_crops.py`. START_HERE now says exactly this.
- Counts pinned: **705 images, 650 with ≥1 caries box, ~2,767 caries+deep_caries boxes**
  (verified against the JSON); **479 çürük** on DENTEX-164 (matches `PAPER_MATERIAL.md` §8.11,
  `PRE_REGISTRATION.md` §4); baseline 212/479 = 0.443 vs constant 0.488.
- START_HERE framed Phase 0 as an "optional warm-up §2"; the agreed order is Phase 0 **first**.

**3 · The PI (sequencing + ownership).** "Who does what, in what order?"
- **Phase 0 → the user, on their Mac, now** (genuinely unblocked there; closes a loop).
- **Lever B → the friend**, after (B) the pre-reg bars are frozen and (C) the user uploads
  weights + shares data. **A and D are parallel — D is not gated on A.**
- New A–D table, identical in `transfer.md` §1 and `START_HERE.md`.

**4 · The maintainer (drift + rules).** "Will this stay correct?"
- All EOLs preserved (`transfer.md` / `models/README.md` / `scripts/eval/README.md` CRLF; rest LF).
- `RESULTS_LOG.md` untouched (no new result); this is a session-memory + `transfer.md` §1/§3 edit.
- `docs/research/` left alone (separate workstream).
- Every referenced path was checked to exist (11/11).

## What was done

- **`START_HERE.md` substantially rewritten:** new "order of work" A–D table up top; Phase 0 no
  longer an afterthought; §0 lists `models/09` too and drops the irrelevant `models/13`;
  Step 2 rewritten with the concrete DENTEX converter recipe (categories_3, `CARIES_CLASSES={1,3}`,
  COCO `[x,y,w,h]`, dims from the JSON), the explicit `data/cariesxrays_det/` rebuild, and the
  seed-43 draw clarified as a separate small draw (not `--seed 43`).
- **`transfer.md`** §1 "where work resumes" rewritten as the A–D sequence; §3 Lever B bullet
  now says "parallel with Phase 0, not gated on it".
- **`TUFTS_GUARD2_DIAGNOSIS.md`** Phase 0 step 0.1 marked ✅ DONE (`044ed3b`).
- **`scripts/yolo/README.md`** + **`scripts/eval/README.md`** — added a "Lever B NOT STARTED /
  see START_HERE" line and a `score_leverB_arm.py` (not-written) row.

## Decisions made

- **Phase 0 is the user's, not the friend's.** *Reason:* on a fresh laptop it needs the same
  514 MB dataset + checkpoints as everything else, so doing it there buys no time; on the user's
  Mac it is genuinely zero-setup and half a day.
- **A and D run in parallel.** *Reason:* Phase 0 (paper §8.10) and Lever B (data prep) touch
  disjoint files; serialising them only delays the higher-value work.
- **No `transfer.md` §5 council entry.** *Reason:* §5 holds strategic pivots; this was a
  documentation-QA review whose output is the fixes themselves + this file.

## Open questions

1. Which datasets the friend has direct access to (DENTEX/CariesXrays on the Drives; Ningxia
   user-only). The user arranges this.
2. Whether the user shares the built `data/detector_multicorpus_v2/` tarball or the friend
   rebuilds it — only matters if the friend (not the user) ends up doing Phase 0.

## Next steps

1. **User:** do Phase 0 on the Mac (or hand it to a session); upload `models/09`, `models/11`,
   `models/14`, `models/15/*.pt` to Drive; share DENTEX + CariesXrays.
2. **User / mentor:** freeze the Lever B pre-reg bars (`PRE_REGISTRATION.md` §4–§6).
3. **Friend:** `transfer.md` → §3 → `outputs/lever_B_lesion_caries_path/START_HERE.md`, then
   Step 2 onward.
