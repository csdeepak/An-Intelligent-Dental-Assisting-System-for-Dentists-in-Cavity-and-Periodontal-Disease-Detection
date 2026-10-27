# 2026-10-11e — Council: planning the Stage-1 detector switch

**Session goal:** the user decided to make a multi-corpus tooth detector the Stage-1 default.
Plan that switch and verify the plan before anything runs.

Run on the macOS clone. **Nothing was executed against the pipeline and `DEF_DETECTOR` is
unchanged.** Documentation only.

## What was done

### 1. The decision, and who made it

A council that morning (`2026-10-11d`) advised 3–0 against changing the default. The user heard
that and decided to proceed, knowing it overrides the two pre-registered ABLATION verdicts of
1 and 3 Sep and re-measures every pipeline number. The repo owner and the mentor were not
consulted. This council was asked how to do it correctly, not whether.

### 2. Facts first

- All four candidate checkpoints are on this Mac and match their recorded hashes.
- **Hold-out re-checked for arm3c**: no scored DENTEX image is a byte-identical or perceptual
  near-duplicate of its DENTEX or Kaggle training images (`RESULTS_LOG` 2026-10-11d).
- The 1,200-image CariesXrays list Lever B scored is absent from this Mac but recoverable: the
  three saved per-image outputs carry one identical set of 1,200 names.
- **The Tufts cohort is 143 images, not 149** — traced and corrected (`RESULTS_LOG` 2026-10-11d).
- `models/15`'s run summary records only a truncated hash for arm3c, which the invariant script
  cannot pin.
- arm3c was trained partly on the Kaggle "dual-labeled" set, whose licence is unstated.

### 3. The council

Three independent read-only members (`Plan` agents).

| Seat | Lens | Model |
|---|---|---|
| 1 | Protocol and honesty | Opus |
| 2 | Evaluation engineering | Opus |
| 3 | Integration and rollback | Sonnet |

No seat disagreed with another on substance; each covered a different part. The plan below is
their three reports merged.

## The plan

### Phase 0 — two choices before anything runs

1. **Checkpoint: arm3c** (`models/15_detector_multicorpus_leverA/arm3c_best.pt`). It was named
   the primary arm before Lever A trained, so choosing it is not choosing by outcome. The record
   must say that `models/13` scores higher on both detector metrics already seen, and that the
   switch itself was decided with outcomes in view.
   *Chair's addition, not councilled:* if the Kaggle licence cannot be cleared, the fallback is
   `models/13` (Tufts + DENTEX only). That trigger is a licence fact, not a number, and should
   be written into the pre-registration so it cannot be used later as a performance choice.
2. **Who is told when.** Local runs on public data need no sign-off. The owner should be told
   before the Ningxia re-run, before any push (the 51 MB checkpoint stays in git history for
   good), and before a Docker rebuild. The paper and the capstone need the owner and the mentor.

### Phase 1 — make the code safe while the default is still `models/11`

Three commits, each leaving every check green for the right reason.

1. **The report's detector tag and accuracy constants follow the weights actually loaded.**
   Today `--detector` with any other checkpoint still stamps the default's name and its
   70.6% / 58.3%. Key a small table by the weight file's sha256; an unregistered detector gets
   an "unregistered" tag and no accuracy claim. *Check:* reports for three fixed images are
   identical to before apart from new keys; the app does not crash on a missing figure.
2. **Provenance and pass-through.** Every evaluation output records which detector produced it.
   The FDI-set-F1 pipeline arm and the parameter counter accept a detector argument. The
   CariesXrays script reads the 1,200-image list from a file. *Check:* no tracked output changes.
3. **The weights.** Record arm3c's full hash in its run summary; make the invariant fail, not
   pass silently, when a Stage-1 hash is unrecorded; add the `.gitignore` exception and the
   rule-4 exception text. *Check:* the invariant prints a match for both detectors.

### Phase 2 — paperwork, committed before any new number exists

4. **The override record**, appended to `RESULTS_LOG.md`. It says: both ABLATION verdicts stand
   as written; the guards failed (0.647 against 0.75, and 0.585 against 0.684); this is a
   stronger override than the 27 Aug one, because Lever A's rule named the default itself; a
   council advised against it 3–0; the owner and mentor were not consulted. It lists what is
   given up: Tufts box mAP 0.810 → 0.585, the cross-domain numbering figure, the masks,
   continuity with every number from 4 Sep to 11 Oct, and Ningxia's blindness to the Stage-1
   choice. It may cite as reasons that the registered primary passed twice and the saved-row
   decomposition of 2026-10-11c. It may not cite the Tufts end-to-end figure as "the guard
   satisfied", this morning's three measurements, or Ningxia's +19 pp.
5. **The pre-registration.**
   - *Already seen, report only:* arm3c's numbering on DENTEX and Tufts, its Tufts box mAP, and
     lesion agreement with the retired gate, including per hospital.
   - *New, and estimation or wording-only:* the lesion detector, the gate and the constant under
     arm3c on three cohorts; FDI-set F1; per hospital.
   - *One rule that may reverse the switch:* for the lesion-detector path, the paired difference
     (arm3c minus a same-machine `models/11` control), pooled over Ningxia and the CariesXrays
     1,200; if the 95% lower bound is below −2 pp, revert. Nothing else reverses it. Not
     triggering the rule is not validation.
   - *Ningxia:* run once, last, after the owner knows; the entry states the run count, that
     nothing was fitted, and that the default was chosen after this detector's gate-path Ningxia
     result was known.
   - *Earlier results:* Lever B's 4 Sep verdict and this morning's three measurements stand,
     relabelled "previous front end". Nothing old is edited.

### Phase 3 — re-measure (about 34 runs, about 5 hours unattended)

Every row runs `models/11` first on this machine, then arm3c, each to its own new directory.
The gate for each row is this Mac's own saved `models/11` result reproduced exactly, where one
exists; where the published number came from the Windows machine, exact image and lesion counts
must match and the drift is recorded.

| Row | What | Must first reproduce with `models/11` |
|---|---|---|
| A | Tufts numbering | 2,438 of 3,760, 143 images |
| B | DENTEX numbering | 547 of 936 |
| C | DENTEX lesion agreement: gate, constant, lesion detector, all-teeth | 479 lesions |
| D | FDI-set F1, both caries methods; latency | this morning's sets exactly |
| E | CariesXrays 1,200: three arms | 2,815 lesions |
| F | Ningxia caries, three arms, per hospital — **last, once** | 1,013 lesions |
| G | Ningxia Stage-4 flag rate | 6,791 affected teeth |
| H | Parameter counts | 27,617,459 and 97,649,753 |

Traps the runs must respect: the one-to-one assignment gives no code to boxes past the 32nd and
rejects none below it; lesion-to-tooth mapping depends on tooth-box size, so flagged counts go
beside every agreement figure; several scripts write to a fixed filename; the image-blind
constant is fixed for FDI-set F1 but moves with the detector for lesion agreement; a stale
control file must never be differenced against a new arm.

### Phase 4 — decide and flip

6. Apply the one reversal rule. If it does not fire, change the single `DEF_DETECTOR` line and
   register arm3c's measured figures in the table from step 1.

### Phase 5 — documents, then the other machine

7. Results log, scoreboard, paper material, `transfer.md`, READMEs, in that order. Until
   `paper/main.tex` is recompiled on a machine with LaTeX, every document says the manuscript
   still describes the previous front end.
8. On the Windows machine: manuscript and PDF; Docker rebuild and smoke test.

**Rollback:** revert the one flip commit. Proof: the three fixed-image reports match their
pre-flip copies and carry the old tag and the old constants.

**Effort:** about four working days on this Mac, under a day on the Windows machine.

## Decisions made

- **Flip last.** Every measurement uses an explicit `--detector`, so a failed gate needs no
  rollback and no report is ever produced by a half-switched pipeline.
- **Controls gate on same-machine identity**, the lesson of this morning's amended
  pre-registration: a number from another machine cannot gate a run on this one.
- **One reversal rule only, and it is about not harming the caries result**, which is what the
  paper is about. Comparisons to the constant cannot reverse the switch, because the constant's
  lesion-agreement score moves with the detector.
- **What may be claimed afterwards.** 92.8% on DENTEX beside 63.5% on Tufts, both in-domain for
  the detector, with 58.3% kept as the cross-domain reference. Never an unlabelled
  "58.3 → 92.8", "generalises", "guard met" or "pre-registered adoption"; never tables that mix
  front ends.

## Open questions

- **The Kaggle licence.** Unstated. Clear it, disclose it, or use the fallback.
- **Will the owner object** to an override of rules he did not write but a default he set?
- arm3c's exact parameter count has not been counted; the estimate is 25.3 M.
- Whether the −2 pp margin, borrowed from Lever A's Guard 1, is the right size for the lesion
  detector. It is fixed in advance either way.
- The 1.5 pp tolerance one member proposed for references produced on the other machine is that
  member's choice and is not derived from anything.

## Next steps

1. The user confirms the checkpoint and says go.
2. Phase 1, three commits.
3. Phase 2, committed before any run.
4. Phases 3 to 5.
