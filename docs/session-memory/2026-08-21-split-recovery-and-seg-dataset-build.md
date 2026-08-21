# 2026-08-21 — Frozen split recovered, real seg dataset built, 66 missing teeth found

**Session goal:** pick up from `transfer.md` on the machine the previous session handed off
to, and clear the last blocker standing in front of the R1 YOLOv11l-seg retrain.

## What was done

1. **Re-established state instead of trusting the handoff doc.** `transfer.md` (commit
   `ad71ee4`) listed nine uncommitted files and said they still needed committing and
   pushing. They had already been committed and pushed — `9e3099d`, `9fcf0d1`, `ad71ee4` —
   and the working tree was clean and in sync with `origin/main`. Nothing to do there.
   `docs/research/clinical_dataset_provenance.md`, the one file deliberately kept out of
   every commit, does not exist on this machine at all; it stayed on the other one.

2. **Found `outputs/eda_tufts/split_v1.csv`.** Reported on 20 Aug as the single remaining
   blocker and as "not findable anywhere by an exhaustive filename search". It is at
   `_repo_archive/datasets_workspace/outputs/eda_tufts/split_v1.csv`. The earlier search
   missed it because it swept `C:\` and `D:\` — a Windows filesystem — while this repo and
   its `_repo_archive/` sibling live on macOS, and because `.gitignore:103` hides
   `_repo_archive/datasets_workspace/outputs/` from anything git-aware. One `find` on the
   right filesystem was all it took.

3. **Proved it is the right split rather than asserting it.** Diffed its per-split filename
   lists against the built bbox dataset the canonical A100 detector was trained on
   (`_repo_archive/datasets_workspace/dataset/images/{train,val,test}`): zero differences,
   700/150/150 exactly. That dataset's labels total 3,794 val and 3,924 test instances,
   matching the A100 run's reported counts in T0.6 §1 exactly. SHA-256
   `6de8cef2af1e73ff843f0353dccc0f93ddac34f33422c418f8ac07c67accb58b`.

4. **Confirmed the rest of the inputs were already here too** — 1,000 raw radiographs
   (landscape 1615×840) *and* 1,000 already-rotated ones (portrait 840×1615) in
   `_repo_archive/datasets_workspace/`, plus `teeth_polygon.json` byte-size-identical to the
   repo's copy under `data/tufts/ZIP/`. The rotation step did not need re-running.

5. **Made `convert_tufts_to_yolo_seg.py` runnable without copy-patching**, then ran it for
   real. Its five path constants now read from `TUFTS_ROOT`, `TUFTS_IMG_DIR`,
   `TUFTS_POLY_JSON`, `TUFTS_SPLIT_CSV`, `TUFTS_SEG_DATASET_DIR`, defaulting to the previous
   hard-coded values. Output: `data/tufts/dataset_seg/` (gitignored, `.gitignore:94`) —
   26,005 instances over 700/150/150 images (18,268 / 3,807 / 3,930), 32 empty labels, zero
   errors.

6. **Found a data-quality defect in the existing bbox dataset** while cross-checking the two
   datasets against each other on the now-shared split. Details under Decisions.

7. **`clinical_dataset_provenance.md` was supplied and its central claim turned out to be
   false.** The user provided the file (written 16 Aug on the other machine) plus Google Drive
   access. §1 asserted the clinic dataset is "local to this machine only" and §7 listed
   "confirm whether it has left this machine" as an open item. Enumerating Drive through the
   connector — metadata only, no image or CSV content opened — showed the entire
   `D:\SDH dataset\dataset\` tree has been on Drive since **2026-06-04**, owned by
   `csdeepak2005@gmail.com` and shared with a second account: `images/`, `logs/`, `reports/`,
   `checkpoint.json`, `SESSION_MEMORY.md`, and **`metadata/index.csv`** (267 KB, the
   re-identification mapping) sitting as a sibling of `images/`. That is precisely the
   condition §4 of the same document names as voiding the de-identification. Recorded as a new
   §4a with the file IDs, the §1 claim struck through rather than deleted, and the literal
   `index.csv` example row redacted to schema-only before committing.

8. **Separately: the Tufts Drive folder is world-writable.** Permissions on
   `1_pPXCzNGlRuLaQhpqScX7sszSXSLQI-U` are `role: writer, type: anyone` — anyone with the link
   can edit or delete it. The content is public research data, so this is an integrity problem
   (the project re-downloads from there), not a confidentiality one. Nothing on Drive was
   changed; it is not this project's account to reconfigure.

9. **Documentation, per `CLAUDE.md` rule 1:** new `RESULTS_LOG.md` entry; `T0.6` §2 (criterion
   caveat), §3.3 (split recovery), §3.5 (new — dataset build + the 66-teeth analysis), §4
   (rewritten, no data blockers left); `PAPER_MATERIAL.md` §7.1, new §8.9, §9 checklist;
   `model_metrics.md` Stage-1 ground-truth caveat.

10. **Rebuilt the DENTEX split from raw** (the decision taken this session). Downloaded
    `train_quadrant_enumeration_disease.json` from Drive — 705 images, 3,529 annotations, 4
    disease classes — wrote `scripts/dentex/build_dentex_split_from_raw.py`, and ran it:
    70/15/15 image-level, seed 42, stratified on the 4-bit disease presence-vector,
    train 495 / val 103 / test 107. Manifest at `data/dentex/splits_v2.json` (committed; the
    raw annotations are gitignored as re-downloadable). Verified disjoint on all three pairs,
    705/705 images and 3,529/3,529 annotations accounted for, and byte-identical on re-run.
    `split_dentex_holdout.py` kept and marked SUPERSEDED, not deleted.

## Decisions made

- **Keep all 66 extra instances in the seg dataset; do not replicate the bbox converter's
  degenerate-box filter.** Comparing seg against bbox labels image-by-image on the identical
  split: 942/1,000 identical, 58 images with 1–3 *more* seg instances, never fewer — exactly
  66 objects. Cause: both JSONs carry identical object lists, but 66 objects have a corrupt
  `bounding box` field (1×1 or 1×2 px) alongside an intact full-size polygon (1,617–13,425
  px², up to 682 points, ordinary Universal tooth titles across both arches; three rendered
  over the radiograph and visually confirmed as real teeth). They are real annotations, so
  dropping them to match a known bug would be propagating the bug for cosmetic
  comparability.
- **Do not fix `convert_tufts_to_yolo.py`.** Changing it would invalidate the frozen
  canonical detector's reproducibility, which T0.6 §1 exists to protect. Left an inline note
  at the filter pointing to the analysis instead.
- **Record the resulting ground-truth mismatch in the pre-registered criterion now, before
  the retrain runs.** The seg test set holds 3,930 instances against the bbox test set's
  3,924, so R1's criterion 1 (box mAP@0.5 ≥ 0.75 vs. the bbox model's 0.7824) is
  near-like-for-like, not exactly like-for-like. Written into T0.6 §2 as a caveat with the
  bar **unchanged** — the whole point of pre-registration is that this gets stated before
  results are visible, not negotiated afterwards.
- **Environment variables rather than a patched copy.** The 20 Aug end-to-end verification
  had to patch a throwaway copy of the converter, which means the artifact that ran was not
  the artifact under review. The same env vars now point the script at the data on the GPU
  box.

## Open questions

- ~~**DENTEX split — still undecided.**~~ **Decided 21 Aug 2026: rebuild from raw.** Build a
  genuinely independent patient-level three-way split from the 705 source X-rays rather than
  carving a held-out set out of the val pool the model was tuned on. This is the fix for
  `PAPER_MATERIAL.md` §8.1, the project's weakest evaluation-discipline point.
- ~~**`clinical_dataset_provenance.md`** — commit/redact/keep-local decision open.~~
  **Decided 21 Aug 2026: commit, corrected and redacted.** The repo is private (GitHub API
  returns 404 unauthenticated; remote reachable with cached credentials). Revisit if it is
  ever made public at submission — the doc names the clinic, states no IRB approval exists,
  and points at where the re-identification mapping lives.
- **Clinic-data governance is now an active problem, not a background one.** An unapproved,
  re-identifiable copy of patient data has been sitting on a shared Drive for ten weeks. The
  five recommended actions are in `clinical_dataset_provenance.md` §4a; all five need the
  Drive owner (`csdeepak2005@gmail.com`), not this repo.
- **SSH / E2E, unverified from here:** whether the compromised `.pem` key's public half was
  ever added to the E2E account (and removed since), whether those `.pem` files were deleted,
  and whether `id_ed25519_e2e.pub` was ever added. This machine has no E2E instance and no
  keypair for it yet.
- **`teeth_mask/` is complete here — 1,000 files, 46 MB** — not the 308 recorded in T0.6
  §3.1 from the other machine's copy. It does not affect anything (the polygon JSON is the
  chosen source and is what the converter uses), but the earlier "confirmed incomplete"
  finding is wrong for this copy and should not be relied on if masks are ever wanted
  directly.

## Next steps

1. Commit this session's work (docs + the three script changes + `.gitignore`). Nothing here
   touches `clinical_dataset_provenance.md`; stage explicit paths.
2. Get GPU access — it is now the *only* thing between here and R1. `GPU_SETUP.md` has the
   E2E click-path; T0.6 §4 has the exact run order and the rebuild command for
   `dataset_seg/` on the target machine.
3. Run `train_yolo_seg.py` against T0.6 §2's pre-registered criterion. Report the result as a
   new `RESULTS_LOG.md` entry whichever way it goes.
4. **Separate `index.csv` from `images/` on the Drive copy** — the one item here with a real
   external clock on it. Owner action; see `clinical_dataset_provenance.md` §4a for all five.
5. ~~Rebuild the DENTEX split from raw.~~ **Done this session.** What remains is the half
   that needs a GPU: regenerate DENTEX crops honouring `data/dentex/splits_v2.json`, re-run
   the caries cascade, and report Phase 1 *and* Phase 2 on the test split — saving the Phase 1
   gate classification report this time.
6. Stages 5–6 (end-to-end inference + per-tooth JSON/PDF report) remain the project's actual
   next milestone and are still unstarted.
