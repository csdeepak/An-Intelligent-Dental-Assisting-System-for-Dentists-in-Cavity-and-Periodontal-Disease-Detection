# 2026-09-02c — Score-improvement council and the Lever A / B / D plan

**Session goal:** the user asked to plan and "council" a push to lift the pipeline's metrics
enough to make an S- or A-grade publication realistic, offering to top up the GPU balance.
No training this session — planning, research and pre-registration only.

## What was done

- **Full context reload.** Read `transfer.md` end to end, all 18 tracked READMEs,
  `model_metrics.md`, the Lever 1 / Lever 2 run summaries and pre-registrations, the relevant
  `PAPER_MATERIAL.md` limitation sections (§8.10–8.14, §8.24–8.26, §9), `MASTER_PLAN_2026H2.md`,
  `PUBLICATION_TODO.md`.
- **Verified the detector-corpus landscape locally.** DENTEX `quadrant` (693 img) carries
  4 quadrant-*region* boxes per image, not teeth — **not** a tooth-detection source (this had
  been an open candidate). `data/kaggle_dual/` is **not on this macOS machine** (gitignored,
  built on the Windows box for head v3) — re-downloadable. DENTEX `disease/` labels are LabelMe
  çürük/… polygons and are the eval ground truth, so unusable for Lever B training; DENTEX
  `quadrant-enumeration-disease` (705 img) is the DENTEX-domain caries-box source.
- **Web research on new public datasets** (all released 2025, after the 27 Aug bone-loss
  "unfixable" decision):
  - **BRAR** (Nature Sci Data 2025, Figshare `10.6084/m9.figshare.30155974`) — 1,104 patients,
    panoramic + **tooth-level bone-resorption grading** + BRAR ratio, periodontist-validated,
    **openly downloadable**. This is the second periodontal corpus `PAPER_MATERIAL.md` §8.13
    says does not exist.
  - **BoneLoss-PAN769** (Zenodo `21114193`) — 769 panoramic, 18,809 crown polygons + 769
    alveolar-ridge polylines, COCO. Files **access-restricted** (request).
  - **UFBA-425** (Figshare `29827475`, 2025) — 425 panoramic, instance masks + bboxes + FDI,
    every tooth. **DNS** — 543 panoramic, COCO + FDI. Both candidate detector corpora.
  - **PerioXrays / PerioDet** (MICCAI 2025, HuggingFace) — 3,673 img, **apical** periodontitis
    (a different entity from periodontal bone loss) — not a bone-loss corpus.
- **ISBI 2027 verified:** Lausanne, 25–28 May 2027; paper deadline **26 Oct 2026**; **4 pages
  hard** (all technical content, figures and tables, in the first 4 pages; 5th page $200,
  non-technical only). 24th edition → S-grade.
- **Wrote two pre-registration drafts** (bars open to one review round, frozen once builds
  start):
  - `outputs/lever_A_multicorpus_detector_v2/PRE_REGISTRATION.md`
  - `outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md`
- Updated `transfer.md` §1, §3 (Track B rewritten) and §5 (council appended).

## Decisions made

All three put to the user as a structured choice; the user accepted all three recommendations.

1. **Framing: A+ — protocol paper spine, plus the lever fixes as positive systems results.**
   *Reason:* the 1 Sep council rejected a pivot to a positive-number systems paper (Framing B)
   because the constant beats the *tooth-level* metric structurally, not on model quality. A+
   keeps the evaluation-protocol contribution (only 2 of 49 task-relevant papers validate
   externally) and adds: "we used the protocol to diagnose three failure modes and fixed them."
   Lever A supports the "end-to-end numbers hide stage-wise failure" thesis; Lever B addresses
   the base-rate-dominance thesis head-on; neither undermines the paper.

2. **Venue: journal primary, ISBI 2027 optional short paper.**
   *Reason:* grade is set by venue, not metrics — a reputable journal is S regardless of
   edition, ISBI (24th) is S if accepted. ISBI's 4-page hard cap actively fights against the
   extra results this plan produces. Target IEEE JBHI or Computers in Biology and Medicine
   (both S, both demonstrably in scope) for the full A+B(+D) paper; submit a cut ISBI short
   paper (protocol + Lever-A headline only) **only if** the four compliance blockers close by
   mid-October.

3. **Levers: A + B now, D if they land with schedule to spare. Skip C and E. Budget ~₹4,000.**
   *Reason:* Lever A (multi-corpus detector, done right) is the single highest-leverage move —
   Lever 1 proved the mechanism (58 → 93 % in-domain) and its guard failure is a fixable build
   flaw (2 corpora, Tufts at 52 % of the mix, no corpus balancing). Lever B flips the caries
   narrative from negative to constructive if a lesion detector beats the constant on its own
   metric. Lever D (bone-loss second corpus, now possible via BRAR) removes the ugliest
   limitation but has the most data-wrangling risk; it is opt-in after A and B.
   Lever C (gate v5) is skipped — the per-tooth-gate approach is base-rate limited by
   construction and 5 attempts already nulled. Lever E (bigger arch) is marginal — resolution
   is already maxed.

**Also decided:** the compliance track (Tufts Drive licence breach, IRB, DENTEX/Ningxia
licences, SDH de-id) must run in parallel, owned by the account holder — it is the real gate on
ISBI and half the gate on a journal ethics statement, and no GPU spend touches it.

## Open questions

1. **Acceptance-bar review.** The two pre-registrations carry specific bars (Lever A primary:
   Δ end-to-end ≥ +5 pp CI-excludes-0; Guard 1: external caries agreement CI lower bound ≥ −2 pp;
   Guard 2: Tufts test box mAP ≥ Control-B − 4 pp. Lever B: beats the constant on ≥ 2 of 3
   cohorts at ≤ 1.5× its prediction rate). The user / mentor gets **one** round to adjust these
   before the build starts. Are they right?
2. **UFBA-425 and DNS licences** — not yet verified. If either does not clearly permit research
   use in a published model, it drops from Lever A's pool (which degrades gracefully to
   Tufts + DENTEX + Kaggle).
3. **BRAR annotation mapping** (for Lever D) — its bone-resorption grading / BRAR-ratio
   convention has to map onto the pipeline's binary present/absent + 3-class severity. Not yet
   inspected.
4. **The Tufts bone-loss crop rebuild blocker** (§9, `RESULTS_LOG.md` 2026-08-27u) still stands
   — Lever D may have to train BRAR-primary rather than Tufts+BRAR pooled.
5. **GPU balance** — ₹560.09; the plan needs ~₹4,000. User offered to top up; not yet done.
6. **Which journal** — JBHI vs Computers in Biology and Medicine vs Diagnostics vs npj Digital
   Medicine. Needs the mentor. Verify Scopus/indexing on the official list before committing.

## Next steps

1. **User:** top up the JarvisLabs balance (~₹3,500) and kick off the compliance track.
2. **User / mentor:** review the acceptance bars in the two pre-registrations (one round).
3. **Lever A data prep (local, no GPU):** re-download Kaggle-dual; download + licence-check
   UFBA-425 and DNS; write `build_multicorpus_detector_v2_dataset.py` (converters + per-corpus
   balancing + the six-point local gate); verify geometry by eye.
4. **Lever B data prep (local):** write the DENTEX `quadrant-enumeration-disease` → YOLO caries
   converter; build the seed-43 CariesXrays eval draw disjoint from the 4,800 training images.
5. **Commit** the pre-registrations + this memory + the `transfer.md` update (one commit,
   explicit paths).
6. Once balance is topped up and bars are signed off: run Lever A (3 arms), score, apply the
   pre-registered verdict, log to `RESULTS_LOG.md`.
7. Then Lever B; then Lever D if schedule allows.

**Ordering rule if the tracks conflict for time:** the compliance track and the journal
manuscript win. A lever that is not finished cleanly is dropped, not rushed.

---

## Continued, same session (end of day) — Lever A data prep executed

The council above was a checkpoint written mid-session. The user then said "start Lever A data
prep", supplied a Kaggle API token, and this got done:

**What was done**

- **Kaggle token** → `.env` at the repo root, **gitignored** (new `# Secrets / local env` block
  in `.gitignore`: `.env`, `.env.local`, `kaggle.json`, `.kaggle/`). Verified untracked.
  `kaggle` CLI 2.2.4 installed into `/opt/anaconda3` (numpy 1.26.4 pin verified intact after).
- **Kaggle-dual downloaded** to this Mac for the first time — slug
  `zwbzwb12341234/a-dual-labeled-dataset` (553 MB) → `data/kaggle_dual/` (`images1/` + `labels/`,
  749 MB). 499 usable (1 byte-identical dupe). Licence **unstated** — already a project corpus,
  so a compliance-track item, not new.
- **UFBA-425 downloaded** — figshare `10.6084/m9.figshare.29827475`, **licence CC BY 4.0**
  (figshare API) → `data/ufba425/` (425 imgs + YOLO-txt boxes + `metadata.csv`, 51 MB).
- **DNS and OdontoAI dropped** — both request-gated, not directly downloadable. Emailing for
  them is possible but not blocking; the pool is fine without them.
- **`scripts/yolo/build_multicorpus_detector_v2_dataset.py`** written (adapts Lever 1's builder;
  adds Kaggle-LabelMe + UFBA-YOLO converters, per-corpus balanced `train.txt`, within-/cross-
  corpus MD5 dedup, `_check/` renders). Dry-run + real build both clean.
- **Built `data/detector_multicorpus_v2/`** (1.1 GB, gitignored): Tufts 700 + DENTEX 561 +
  Kaggle 449 + UFBA-425 382 train / 4 institutions. **Geometry gate: 42,500 rotated boxes,
  median IoU vs source 1.0000, PASS.** Tufts canonical box counts (3,794 / 3,924) reproduced
  exactly. 0 leakage refusals. All 4 corpora eyeballed in the detector frame — boxes tight on
  teeth, correct orientation.
- **11 byte-identical DENTEX `quadrant_enumeration` images** found and dropped — **Lever 1
  trained on those 11** (its builder had no within-corpus dedup).

**Decision made — UFBA-425 is an additive arm, not baseline.** UFBA's only public form is a
square 640×640 Roboflow export: the panoramic is stretched to 1:1, so tooth-box aspect is
distorted (median box w/h **0.234** vs DENTEX 0.347, Tufts 0.371 — ~35 % narrower). This is a
preprocessing artifact, not acquisition diversity. So the pre-registration (`outputs/lever_A_
multicorpus_detector_v2/PRE_REGISTRATION.md` §2, §4) was refined **before any training**: the
**3-corpus pool (Tufts+DENTEX+Kaggle) is the primary Lever A arm** (`train_3corpus.txt`), and
UFBA is **Arm 4C** (`train.txt`), reported alongside and adopted over 3C only if it *also*
passes §5 and beats 3C on the primary. Both `train.txt` files are built. This is a rigour
refinement, not a bar move — the §5 acceptance bars are unchanged.

**Docs updated this session:** `transfer.md` §1/§3/§8, `data/README.md`, `scripts/yolo/README.md`,
root `README.md` (publication-target section), plus `outputs/lever_A_multicorpus_detector_v2/
STATUS.md` (the live status file for this lever).

**Open / next (unchanged from the council's list, minus the data prep that is now done)**

1. **User:** top up JarvisLabs ~₹3,500; name the compliance-blocker owner and start it.
2. **User / mentor:** sign off the acceptance bars — Lever A §5, Lever B §6 — one round, then frozen.
3. **Next session:** write `train_multicorpus_detector_v2.py` from Lever 1's (`--arm
   {controlB, arm3c, arm4c}`); `tar` + sha256 `data/detector_multicorpus_v2/`; rent an A100;
   run Control B + Arm 3C + Arm 4C; re-measure Control A (deployed seg) same-day; score with
   `scripts/eval/score_lever1_arm.py` (or a v2 of it); apply the pre-registered verdict; log to
   `RESULTS_LOG.md` + `model_metrics.md` + `PAPER_MATERIAL.md`.
4. **Then Lever B data prep** (local): DENTEX `quadrant-enumeration-disease` → YOLO caries
   converter; seed-43 CariesXrays eval draw disjoint from the 4,800 training images.
5. **Commit** — one commit, explicit paths: `.gitignore`, `.env` stays untracked, `transfer.md`,
   `data/README.md`, `scripts/yolo/README.md`, `README.md`, this file,
   `scripts/yolo/build_multicorpus_detector_v2_dataset.py`,
   `outputs/lever_A_multicorpus_detector_v2/`, `outputs/lever_B_lesion_caries_path/`.
   (Nothing committed yet — the user has not asked.)

**Housekeeping noticed, not fixed:** `/opt/anaconda3/lib/python3.12/site-packages/` has a
corrupted `~orch-2.5.1` partial install throwing pip warnings (pre-existing). And `python3` on
PATH is homebrew 3.14 with none of the deps — the project env is `/opt/anaconda3/bin/python3`
(3.12.12), call it explicitly.
