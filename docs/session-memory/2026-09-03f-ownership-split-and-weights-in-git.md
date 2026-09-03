# 2026-09-03f — Mac/Windows ownership split + checkpoints into git

**Session goal:** the user takes Phase 0 + Lever A2 on the Mac; the friend takes Lever B on
Windows. Update `transfer.md` + READMEs for that split, and make the friend's checkpoints
available without a Drive round-trip ("try to remove them from gitignore").

Documentation + `.gitignore` + two committed binaries. No model trained, no result.
Continues `2026-09-03d` / `2026-09-03e`.

## What was done

### Checkpoints into git (the friend's ask)
- **Committed `models/09_caries_gate_v3/caries_gate_v3.pth` (43 MB)** and
  **`models/11_yolo_seg_tufts_r1/best.pt` (53 MB)** via `.gitignore` `!` exceptions. These are
  two of the three `DEF_*` checkpoints (`models/10` was already tracked at 43 MB). A `git pull`
  now runs `run_inference.py` and the Lever B eval with no Drive step.
  - sha256 pinned: `models/11` `271316c4…`, `models/09` `8f4a99ba…` (match `run_summary.txt` +
    `verify_invariants.py`).
  - `models/11` is 3 MB over the CLAUDE.md rule-4 line — logged as a deliberate exception in
    `transfer.md` §4 (reversible: `git rm --cached` + restore the `.gitignore` lines), and a
    parenthetical was added to CLAUDE.md rule 4 so the rules file matches the repo.
  - Repo `.git` grows ~96 MB permanently (history keeps them). Private repo → low risk;
    revisit before any public release, alongside the tracked-notebook-pixels item (§4).
- **Added `.gitattributes` (`* -text` + `binary` for blobs)** — the repo hand-manages CRLF/LF
  (`transfer.md` §7); without this a Windows clone with `core.autocrlf=true` could flip every
  LF file. Attributes override config, so this protects the repo regardless of the friend's git.

### What CANNOT come out of `.gitignore` — told the user plainly
- **Datasets: DENTEX 15 GB + CariesXrays 7.9 GB + Ningxia 2.4 GB.** Too big, and the Tufts
  licence forbids redistribution. Drive / the user is the only path — unchanged.
- **`models/14_cariesxrays_lever2/weights/best.pt` (the Lever B B-single arm) is MISSING from
  every machine.** `run_summary.txt` records it downloaded + sha256-verified 2 Sep ("local disk
  only"); it is not in `models/14/weights/`, not in `_repo_archive/`, not on Drive, and a
  home-wide `find` for `.pt` files 30–80 MB did not turn it up. Flagged in `WINDOWS_SETUP.md`
  §4, `models/README.md`, `EXTERNAL_DRIVE.md`, `transfer.md` §1/§3: user must locate it, retrain
  (~₹250), or Lever B runs B-pooled-only.

### Docs
- **`transfer.md`** — §1 resume paragraph rewritten as the ownership split (user: Phase 0 + A2,
  Mac; friend: Lever B, Windows); the three "upload models/11 to Drive" references updated to
  "now in git"; §3 lever bullets tagged with owners; §4 new row for the weights-in-git decision.
- **NEW `outputs/lever_B_lesion_caries_path/WINDOWS_SETUP.md`** — the friend's machine-prep: what
  `git pull` now covers, the `verify_invariants.py` check, the datasets/`models/14` still needed,
  the 8.4.130-vs-8.4.127 ultralytics note (pin only for the B-pooled training run), the Windows
  `jl` gotchas pointer, and the `models/14` decision.
- **`START_HERE.md`** — §0 rewritten ("what's in git now" vs "still outside git"); the A–D table
  gained owners + an A2 row; Step 3 flags the missing B-single weights.
- **`models/README.md`, `README.md`, `docs/EXTERNAL_DRIVE.md`** — the "fetch these checkpoints"
  / "❌ Drive" / "not uploaded yet" content updated to reflect `models/09`+`11` in git and
  `models/14` missing.

## Decisions made

- **Commit `models/09` + `models/11` despite rule 4.** *Reason:* the user explicitly asked, the
  repo is private, both are < GitHub's 100 MB hard limit, `models/09` matches the already-tracked
  `models/10` exactly in size, and the friend is on Windows where `gdown`/OAuth is real friction.
  Documented as reversible.
- **Do NOT commit `models/06`, `13`, `14`, `15`.** *Reason:* `06` is only for old-number
  reproduction; the lever weights are ablation artefacts not needed to *run* anything; committing
  them would be ~200 MB more for no runtime benefit. The exception is scoped to the `DEF_*` three.
- **`.gitattributes` = `* -text`, not `text=auto`.** *Reason:* the repo's line endings are
  already correct and deliberately mixed; `text=auto` would renormalise and produce a huge diff.
  `-text` freezes the current bytes.

## Open questions

1. ~~**Where is `models/14/best.pt`?**~~ **RESOLVED same day** — the user confirmed it is on the
   **Windows laptop** (downloaded there during the 2 Sep Lever 2 run, which is why a Mac-side
   `find` couldn't see it). A `.gitignore` exception (`!models/14_.../weights/best.pt`, `last.pt`
   still out) was added so the friend `git add`s it after a sha256 check. `WINDOWS_SETUP.md` §4,
   `transfer.md` §1/§3 updated.
2. Does the friend's Windows laptop already have the 27-Aug DENTEX subsets, or is it a different
   machine? `WINDOWS_SETUP.md` covers both, but the user should confirm.
3. Ningxia for the friend — restrictive licence. If the user can't provide it, Lever B is 2/3
   cohorts (the pre-reg's "≥ 2 of 3" rule still works).

## Next steps

1. **User:** locate `models/14/best.pt` (or decide retrain / B-pooled-only); get CariesXrays +
   Ningxia to the friend; do Phase 0 on the Mac; freeze the Lever B bars with the mentor.
2. **User:** `git push` when ready — the friend then `git clone` / `git pull` gets `models/09/10/11`
   + `.gitattributes`.
3. **Friend:** `WINDOWS_SETUP.md` → `START_HERE.md` → Step 2.
