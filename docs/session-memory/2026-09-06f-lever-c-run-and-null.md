# 2026-09-06f — Lever C: frozen, built, run, and reported as a null

**Session goal:** one line — take the go-ahead on Lever C, freeze the pre-registration, implement
both arms, run the four evaluations, apply the frozen rule, and clear the cheap Tier-2 items
alongside it.

## What was done

The user read the 6 Sep project-overview report and asked to start closing the gaps its tiers
name. Three decisions came back: **Lever C — go, freeze as written**; **set up a local CPU
environment** so compute can run on this Windows box; **Tier 1 (venue, authors, the two
governance breaches) stays with him**. Everything below follows from those.

### Environment (new capability, not just this lever)

- `C:\venvs\dental312` — Python 3.12, torch 2.14.0+cpu, numpy 1.26.4 (the repo's `<2` pin holds,
  which is why 3.12 and not the machine's 3.13: numpy 1.x has no 3.13 wheels), ultralytics
  8.4.142, opencv, scipy, pytest. **Outside the repo on purpose:** an in-repo `venv/` hit the
  Windows 260-character path limit inside `torch/include/ATen/.../*.h` and installed a broken
  torch. Enabling long paths is a system-settings change and was not made; the short path solves
  it. This box can now run the CPU evaluations, so the Mac is no longer the only machine that can.
- **Tufts image frame on this clone.** `scripts/eval/validate_fdi_assignment_tufts.py` expects
  `_repo_archive/datasets_workspace/Radiographs` (absent here). The local
  `data/tufts/ZIP/Radiographs_upright/` is **180° from the frame `upright_box()` maps GT into** —
  verified two ways: `CW(Radiographs_rotated) == Radiographs_upright` at mean|diff| 0.61, and
  scoring 12 val images in the 180° frame lifts FDI-exact-of-detected from 12% to 64%. The
  evaluation frame was regenerated (rotate 180, JPEG q95) into
  `data/tufts/ZIP/Radiographs_upright_fixed/` (gitignored). The control arm then reproduces the
  published Tufts numbers to 0.2–0.6 pp and DENTEX to the digit.

### Lever C

1. **Froze the pre-registration first** (`e9270a3`), before a line of Lever C code existed: bar
   stays +2.0 pp, anterior stays a hard bar, adopt-as-default iff all three — the three review
   questions answered as drafted. Added §9 to carry the freeze record.
2. **Implemented** `src/fdi_structural_repair.py` (both arms), split `assign_fdi_head` into
   `head_joint_scores` + `assign_from_scores` so every arm scores ONE forward pass, added
   `--assignment` to both Stage-2 harnesses and to `run_inference.py` (default unchanged),
   `scripts/eval/lever_c_bootstrap.py` to apply the rule, 15 tests encoding the §7 gate, and a
   `verify_invariants` entry asserting the lever stays off by default with τ and `gap_factor`
   inherited.
3. **Gate passed** — 174 tests (159 + 15), all invariants hold, and the first real run was Tufts
   val, as §7.5 requires.
4. **Ran** the three arms on Tufts test and DENTEX off identical boxes and identical head
   forward passes, then the paired cluster bootstrap (10,000 resamples, seed 42).
5. **Verdict: NULL, do not adopt.** Tufts of-detected Δ **+0.29 pp [−0.07, +0.69]** (C-dp) against
   a +2.0 pp lower-bound bar; DENTEX guard also fails on the strict reading (−1.27 lower bound).
   Numbers in `RESULTS_LOG` 2026-09-06b and `outputs/lever_C_fdi_structural_postproc/run_summary.txt`.

### Tier-2 items closed alongside

- **Stale drafts** (`transfer.md` §3 item 7): `docs/paper/manuscript.md` and `draft_spine.md` now
  open with banners naming their specific stale figures (gate-only Stage 3a, 0.488, 61.2 M) and
  pointing at `paper/main.tex`; `docs/README.md` says quote `main.tex`, never these. Nothing
  deleted (rule 3).
- **Traceability gap I flagged this morning:** `outputs/tufts_fdi_pos_diagnostic/pos_feat_diagnostic.json`
  — the artefact `RESULTS_LOG` 2026-09-06 cites — was never tracked, so the numbers were not
  checkable on this clone. Re-running it exposed a real portability bug: the script prints Greek
  deltas and a Windows console (cp1252) raises on them **after** the scoring work and **before**
  the JSON is written. Fixed by reconfiguring stdout; the DENTEX arm reproduces the published
  values (full 91.1% vs 91.0%, no_position 77.6% vs 77.5%, shuffled 52.9% vs 52.9%).

### The traceability fix turned into a data finding

Re-running Option B to commit its missing artefact did **not** reproduce it — and that turned out
to be the most useful thing this session found. DENTEX matched to a tenth of a point; **Tufts came
back 18.1% against a published 71.5%.** Isolated by elimination rather than guessed:

1. the manifest labels are internally consistent and match DENTEX's conventions exactly, so the
   mirror is not wrong;
2. **all eight** dihedral transforms of the stored crops were scored — best 37.2% — so it is not a
   rotated crop; each crop shows a *different tooth* than its label;
3. re-cutting the same manifest boxes from `Radiographs_upright_fixed/` scores **73.5%**, which
   reproduces the published number and names the correct frame.

So this clone's `data/tufts/enumeration_v1` is cut from the wrong source frame — same root cause
as its `Radiographs_upright/` being 180° off. **The Mac's copies are valid and every published
number stands**, but any crop-level work done on this Windows box before the corpus is rebuilt is
silently wrong: the labels look right, the crops look like teeth, and the accuracy is simply
false. Written up in `RESULTS_LOG` 2026-09-06c, `transfer.md`'s opening warning,
`outputs/tufts_fdi_pos_diagnostic/README_WINDOWS_RUN.md`, and made repeatable as
`scripts/eval/tufts_crop_frame_check.py`.

**Lever C is unaffected** — it runs on radiographs through the detector, and its control arm
reproduces the published Stage-2 numbers on both cohorts (DENTEX to the digit).

### …and the data finding turned into a repair (same session, after the merge)

The user asked to merge and rebuild, so: `data/tufts/enumeration_v1` was rebuilt from the
corrected frame with every original build parameter, and the result is **label-identical** —
the new manifest sorts byte-identical to the old, same 42,755 rows, same duplicate resolution —
which is itself the proof that only the pixels were ever wrong. Crops now score **73.2%** where
they scored 11.5%. The defective build was **archived, not deleted**
(`_repo_archive/tufts_enumeration_v1_wrongframe_2026-09-06/`, with an `ARCHIVE_MANIFEST.md` entry
and a restore command) because it is the evidence for `RESULTS_LOG` 2026-09-06c.

Option B was then re-run on the rebuilt corpus and **reproduces the published result on both
cohorts** — DENTEX 91.1% vs 91.0%, Tufts 70.8% vs 71.5%, and the headline `dentex_geom` effect
+0.0 pp vs +0.1 pp. So the positional-feature hypothesis is now falsified on two machines and two
independently built corpora, and the traceability gap that started all this is closed with a real
reproduction rather than a committed file.

A `verify_invariants` entry ("crop source frames") now re-cuts a few manifest rows from the source
`meta.json` names and compares pixel-wise. Its docstring says plainly what it does **not** catch:
a corpus that is internally consistent but built from the wrong frame — precisely this bug — looks
perfect to it. That needs `tufts_crop_frame_check.py`. Writing the limitation down mattered more
than the check itself; the first draft of that docstring claimed it "would have caught
2026-09-06c", which was false, and this repo's whole failure history is confident claims nobody
tested.

### The audit that followed — the bone-loss crops are clean

Asked to check the bone-loss crops too, so I checked everything Tufts-derived rather than that one
corpus. **The bone-loss crops are in the correct frame**, established two independent ways: their
stored `val_cw` crops differ from a re-cut out of `Radiographs_upright_fixed` by mean|diff| 0.39
(JPEG noise) against 47.99 for the wrong frame, and scoring the frozen Stage-4a model over the
three stored variants reproduces `RESULTS_LOG` 2026-08-27u's table **exactly**, confusion matrices
included (0.4869 / 0.5371 / 0.7145).

So the 0.40-vs-0.83 sensitivity gap is not orientation. I also excluded one fresh candidate: the
source notebook reads radiographs as `IMREAD_GRAYSCALE` while the rebuild uses `IMREAD_COLOR`, and
rebuilding both ways gives *identical* predictions — these radiographs are true greyscale. What
remains is what 27 Aug already said: a different population (785 reproducible rows vs the reported
1,558, half of which carry unsaved jitter) and the source-image provenance. One new datum on how
fragile the subset is: re-cutting from a re-encoded frame instead of rotating in memory moves
sensitivity 0.4000 → 0.3714, one borderline positive flipping on JPEG noise. At 35 positives that
subset cannot settle the question either way — an argument for leaving 0.923 flagged rather than
approximating it.

`dataset_seg_v2` (what `models/11` trained on) is aligned and byte-identical to
`Radiographs_rotated_fixed` — a third, independent corroboration of today's frame conclusion.
`severity_dataset` / `resampled_dataset` are metadata-only. The audit is now one command,
`scripts/eval/tufts_corpus_audit.py`, with each directory's expected verdict recorded so a future
change fails loudly.

**The thing actually worth acting on** is not a corpus at all: three misaligned artefacts still sit
on disk under the *shorter, more inviting* name next to their corrected counterparts —
`Radiographs_rotated`, `Radiographs_upright`, `dataset_seg`. That naming is precisely how the
enumeration corpus came to be built from the wrong one. I did not rename them in this session
because moving `dataset_seg` touches paths other scripts may reference, and that deserves its own
pass rather than being tacked onto this one.

## Decisions made

- **Freeze before code, verdict from the rule.** The pre-registration was committed with the
  go-ahead before any implementation, and the verdict was read off §5 without amendment. The
  primary bar was never in doubt at +0.29 pp, so no judgement call was needed — but the guard
  would have been the interesting one, and it too is reported as it fell.
- **Report the mechanism, not just the null.** A null that says only "it didn't work" invites the
  next person to try the same thing. So the harness now measures *how much room the method had*:
  of 3,489 Tufts test detections, **72.6% are anchors** (immovable by construction), **13.4% sit
  in the 48 over-full quadrant groups** (>8 detections, no strictly increasing labelling of 1..8
  exists), **13.9% are movable at all**. τ = 0.30 was inherited so the lever would add no
  tunable — and at 0.30 the head clears the anchor threshold on most teeth *including ones it is
  confidently wrong about*, which is precisely the error the constraint was meant to fix. This is
  the honest explanation and it is now in the log, the run summary, and §8.16.
- **Kept both arms rather than deleting the loser.** C-dp beats C-sort on every headline
  quantity, so the DP does earn its complexity over the cheap arm; both ship behind
  `--assignment`, default `hungarian`, and are reported as an ablation.
- **Did not re-run anything to make the Tufts control match the published number exactly.** The
  0.2–0.6 pp shortfall is a re-encode artefact of this machine's reconstructed image frame, it is
  documented, and every arm eats the same pixels, so the deltas — the only thing the rule reads —
  are unaffected. Chasing it would have meant fetching the original radiographs for no gain.
- **`docs/research/` untouched** (separate workstream). No GPU spend. No data outside the two
  Stage-2 cohorts.

## Open questions

- **Is the Tufts image-frame reconstruction worth making permanent?** Right now this clone
  depends on a generated `Radiographs_upright_fixed/` and a `--images` flag. Either the original
  `Radiographs/` should be fetched onto this box, or the harness default should learn about the
  local layout. Left alone rather than changing a default that works on the Mac.
- **τ was the wrong knob to inherit, and that is a finding, not a fix.** An anchor threshold and a
  low-confidence *flag* threshold are different jobs; 0.30 is permissive for the former. Testing a
  stricter anchor threshold means a fresh pre-registration — it must not be swept against Tufts.
- **The contiguous-arch stratum gained +2.36 pp (n=296).** Real, and 9.5% of the cohort. Whether a
  gated version — apply the repair only where the arch looks contiguous — is worth pre-registering
  is a genuine question, and it is post-submission.
- Unchanged and still the critical path: Tier 1 (the two live governance breaches, venue, authors)
  — the user's, per this session's decision.

## Next steps

1. **User:** Tier 1 — the Tufts Drive folder and the SDH `index.csv` are still live breaches; the
   venue and author block still gate submission. Nothing in this session moved them.
2. **Done in this session:** the Tufts enumeration corpus is rebuilt and verified. **Still open:**
   run `tufts_crop_frame_check.py` against the other Tufts-derived corpora
   (`bone_loss_crops_rebuilt`, `severity_dataset`, `dataset_seg*`) — same era, same likely cause,
   untested. The bone-loss ones matter most: that branch holds the project's strongest in-domain
   number (0.923), and its 2026-08-27u/28c rebuild attempt already scored anomalously low. Worth
   asking whether that anomaly and this defect are the same bug.
3. Remaining Tier 2, unclaimed: rebuild the Docker image (it predates the Lever B caries wiring;
   Docker 28.5.2 and every checkpoint including `models/16` are present on this box, so it is
   runnable here), and the 5-minute Panetta et al. 2022 novelty read.
4. `PROJECT_OVERVIEW.html` was stale in two places (128 → 130 log entries; Lever C is listed as
   "awaiting go/no-go"). It is a snapshot by design, but it is also the document the user is
   working from — regenerate or amend it rather than leaving it drifting.
5. Post-submission only, each needing its own pre-registration: Option E (a better image-pathway
   position encoder — the one remaining explanation for the 73.5% position digit), and the
   contiguous-arch-gated variant of Lever C if anyone wants to revisit it.
