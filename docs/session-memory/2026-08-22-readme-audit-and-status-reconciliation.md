# 2026-08-22 — README audit, DENTEX inventory, and a verified status picture

**Session goal:** bring every README in line with the working tree after a day of heavy
change, inventory the full local DENTEX release, and establish — by checking rather than
recalling — what is actually finished and what is left.

## What was done

1. **Read `MASTER_PLAN_2026H2.md` in full for the first time.** Previous sessions (including
   the immediately preceding one) had been working from `PUBLICATION_TODO.md` and inferring
   the master plan's contents. That produced a wrong call: R1 (the YOLOv11l-seg retrain) was
   described as "an enhancement, not on the critical path." MASTER_PLAN §3 marks R1 "✅ do
   this", W2's exit criterion includes it, and R2 depends on it. The plan also
   **supersedes `PUBLICATION_TODO.md` for sequencing** by its own §0 — which is exactly the
   fact that inference missed.

2. **Audited all 10 READMEs.** Six were stale, three were fine, one was mine from yesterday.
   Rewrote `models/README.md` and `data/README.md` (both contained outright false claims),
   updated `scripts/yolo/README.md`, `notebooks/yolo_detection/README.md`, `docs/README.md`
   and the root `README.md`, and created `scripts/dentex/README.md`, which did not exist.

3. **Inventoried `~/Downloads/Capstone/DENTEX/` completely** — six subsets, 3,905 images,
   ~14 GB. Five were known. The sixth, `disease/{input,label}/`, had never been examined.

4. **Leakage-checked the new subset before recording any claim about it** — MD5 plus
   normalised-signature correlation of all 250 against the 705 training images and the
   50-image extern set.

5. **Ran the full test suite** — 29/29 pass.

## Decisions made

- **Corrected the R1 priority call rather than quietly changing it.** The earlier
  deprioritisation was based on a document that explicitly says it is superseded for
  sequencing. Recorded in the tier list and here, because a silent reversal would look like
  drift rather than a correction.
- **Recorded the `disease/` subset without building anything on it.** It is genuinely
  valuable — 1,600 FDI-keyed polygons across 8 classes, including 91 explicitly healthy teeth
  — and it is exactly the shape of thing that caused the 2026-08-21m error when acted on
  before verification. The leakage check came first; the scoping decision is deferred to the
  schedule rather than made during a documentation pass.
- **Classified it as an internal held-out set, not external validation.** Its dimension modes
  match the 705 exactly, so it is the same equipment and population. Presenting it as
  cross-institutional evidence would be wrong; Ningxia remains the external cohort.
- **Marked "Complete" in the root README as meaning trained, not validated.** Five stages read
  "✅ Complete" while the Tier-0 re-run block is prepared but unrun. Added a note rather than
  downgrading the ticks, since the training genuinely did happen.

## Open questions

- **What the 250-image `disease/` set should be used for.** Three non-exclusive options: the
  caries cascade's honest per-tooth held-out test set; a source of a small real healthy class
  for the Phase-1 gate defect (91 teeth is small); or the substrate for C3's stage-wise
  error-propagation analysis. All three need a LabelMe→FDI parser that does not exist.
  `test_181.png` must be excluded — it is byte-identical to `train_332.png`.
- **Whether the Turkish 8-class taxonomy maps onto our 2-class caries framing** without
  distortion. `çürük` → caries is obvious; `lezyon`, `küretaj`, `kanal` are not, and
  `MASTER_PLAN` §4.3.3's warning about manufacturing negatives applies here too.
- **Bone-loss weights have no version tag** — the only trained stage still lacking one.

## Next steps

1. **Provision the E2E GPU instance.** Every remaining W2 item needs it and none can start
   without it. It is `MASTER_PLAN` §10 action 4 and still not done.
2. **Start R4 (Stages 5–6 integration) in parallel** — it needs no GPU, all four models are
   local, and it is the plan's own named long pole (§8 risk register: "High likelihood, high
   impact, this is the historical long pole").
3. Run the GPU block once provisioned: R1 seg retrain (~6h), then both caries arms (minutes).
4. **T0.5** — the Mild n=6 decision. No compute, untouched since it was written.
5. Bring the Ningxia drive back; W4's external run depends on it.
6. Start IRB paperwork — flagged since 15 Aug as zero-cost, still not begun.
