# 2026-09-02 — DOI blocker cleared; Lever-2 go/no-go council (GO, gated)

First session of 2 Sep. Cold start from `transfer.md` (1 Sep late-evening snapshot). Continues
the Track A / Track B split set by the 1 Sep publication-framing council.

## Session goal

One line: resume from `transfer.md`, clear the 22-broken-DOI submission blocker, and council the
Lever-2 GPU run (go/no-go) with the AAAI FPCL baselines actually read.

## What was done

**Housekeeping first (separate short asks):**
- `git pull` — local `main` was 2 commits behind `origin/main` (`8e0ab57 → 3ee06d3`). Local tree
  had uncommitted 30-Aug SDH docs overlapping 4 incoming files; stashed, fast-forwarded, resolved
  the 4 conflicts by hand (union merges; SDH `RESULTS_LOG` entry slotted into chronological order
  before the 08-31 entries), dropped the temp stash. No commit — the SDH docs are still
  uncommitted working-tree changes, same as before the pull.
- **JarvisLabs `jl` CLI is half-broken on this machine.** The `jl` on `PATH` is
  `…/Python311/Scripts/jl.exe` whose interpreter (`Python311/python.exe`) was removed — every
  invocation dies. The working copy is `…/Python313/Scripts/jl.exe` (v0.2.17, valid). The saved
  token in `%LOCALAPPDATA%\jl\jl\config.toml` was **invalid** (`jl status` → `✗ Invalid token`);
  the user pasted a fresh key and `jl status` now shows **Balance ₹816.70, 0 running / 0 paused**.
  PATH still needs fixing for bare `jl` to work — flagged, not done (user declined for now).

**Machine capability re-check (corrects `transfer.md` §3/§8):**
- **MiKTeX 25.12 IS installed here.** `latexmk -pdf main.tex` converges clean:
  **12 pages, 0 errors / 0 undefined citations / 0 undefined refs / 0 overfull hboxes** — both
  before and after the bib edits. The "no LaTeX toolchain on this Mac" note in §3.1 was
  macOS-specific; the Windows machine can build and length-check the manuscript.
- **`D:` drive is not mounted.** Only `C:` exists. The SDH clinic data (`D:\SDH dataset\…`,
  `D:\dataset_audit\`, `D:\raw data\`) that §8's Windows table says was verified 30 Aug is
  **unreachable this session**. SDH track paused, not cancelled.
- 159/159 tests pass; `verify_paper_numbers.py` = 90 claims, no drift; `verify_invariants.py`
  all hold. Python 3.13 env.

**DOI blocker — CLEARED.** The 22 broken DOIs from `outputs/citation_audit/FINDINGS.md`
(1 Sep audit) were each looked up by title:
- **All 22 are real, published papers carrying a wrong identifier. Zero fabrications.**
- 11 that "resolved to a different paper" and 11 "not registered" — all now corrected and
  re-verified against `doi.org` with CSL-JSON content negotiation, accepted only at title-overlap
  1.00 against the registry record.
- **In 19 of 22, the `volume`/`pages` were also wrong**, and 2 had the wrong `year`
  (`lim2024dual` 2024→2026, now published JPD v135). Those were corrected from the registry
  record, not the stale bib fields.
- **6 `url` fields embedded the old wrong DOI** — a second vector the audit script never checks
  (it only reads the `doi` field). Fixed those 6; the other ~57 `url` fields are **not swept** —
  logged as a follow-up.
- Re-audit (`verify_citations_crossref.py`, needs `PYTHONIOENCODING=utf-8` on this console):
  **62 clean / 1 flag**. The flag is `yalim2026comparative` — cosmetic `İ`/`ı`, `ğ`/`g`
  author-accent mismatch, DOI correct, entry uncited. Not an error.
- Recorded in `RESULTS_LOG.md` 2026-09-02 and `outputs/citation_audit/RESOLUTION_2026-09-02.md`
  (full old→new table). `paper/main.pdf` rebuilt clean with the corrected bib.

**Lever-2 council (the main ask).** Read the AAAI FPCL paper + repo + a follow-up paper:
- CariesXrays = 6,000 images, single class "Decay", VOC-style, **4,800/1,200 split**, COCO AP
  metric via `pycocotools`.
- FPCL's `my_dataset.py` / `train.py` read a **standard VOC `ImageSets/Main/{train,val}.txt`** —
  so the split is a plain file. DVCTNet (arXiv 2508.20813) reused "the original split … for fair
  comparison", confirming it exists and is shared.
- Published table: FPCL **48.2 / 84.1 / 50.6** (AP/AP50/AP75); YOLOX 40.5/81.3/36.1; Faster R-CNN
  39.9/78.0/37.8; RetinaNet 13.0/30.5/10.2; DINO 37.8/75.3/29.4.
- The GitHub repo ships only a 0.5% sample with **no `ImageSets`** — the real split (if released)
  is inside the Google-Drive download (`1qWL2f0A-vf91StHxs24eoiFDyuoHEh4N`).

## Decisions made

- **DOI corrections applied directly to `source.bib`** (not deferred to a "fix later" list) —
  the blocker was the single venue-independent Track A item fully doable on this machine, and the
  fixes are all registry-verified, so there is nothing to second-guess. Reasoning: same failure
  class as the 28 Aug / 1 Sep citation errors; leaving 22 known-wrong identifiers in place while
  moving on would be the exact "documented defect that never propagates to a fix" pattern
  `CLAUDE.md` rule 1 exists to prevent.
- **`url`-field sweep deferred**, per the user ("we fix the url later, put incomplete for it in
  transfer.md"). Logged in `transfer.md` §3 item 2 and the RESOLUTION file. Low risk — a `url` is
  a convenience link, not what a reviewer dereferences.
- **Lever 2: GO, conditional on one gate** — the CariesXrays Drive download must contain
  `ImageSets/Main/{train,val}.txt`. If absent and the authors don't share it, **DROP Lever 2**;
  an own-split number cannot sit in their published table and Framing A stands alone regardless.
  Reasoning: the §5 1-Sep council already timeboxed this to a 1-day go/no-go gated on the split
  being reproducible; the split turns out to be a standard VOC file that a follow-up paper reused,
  so reproducibility is *likely* but unconfirmed until the download is inspected. The job is
  cheap (~₹300, ~3–4 h, balance covers it + a redo) and the payoff — the project's first number
  beside a published result on the same data — is worth it even if we only match the generic
  baselines (we very likely will NOT beat FPCL's 48.2).
- **Lever 2 stays a non-pipeline benchmark row.** No checkpoint adopted, no pipeline change. One
  table row in Related Work.

## Open questions

- **Does the CariesXrays Drive download carry the `ImageSets` split?** Unresolved — data is not
  on this machine (~2 GB, was macOS-only). This is the Lever-2 gate.
- **Where is `D:`?** Detached external drive? Re-lettered? Needed before SDH work resumes.
- **Venue: ISBI 2027 vs journal.** Still the user's call; gates the 4-page cut.
- **Authors/affiliations** in `main.tex` still `Unknown`.
- The 19 genuinely DOI-less bib entries — per-entry decision not yet made.

## Next steps

1. **User:** download CariesXrays from the Drive, check for `ImageSets/Main/*.txt`. Report back.
2. If split present → write `outputs/lever2_cariesxrays/PRE_REGISTRATION.md` (metric = COCO AP
   primary; comparator = the FPCL table verbatim; "bar not moved" rule), commit it.
3. Build + geometry-gate the VOC→YOLO dataset locally (reuse
   `scripts/eval/cariesxrays_external.py:lesions_from_voc` for the 27.3%-wrong `<size>` handling);
   tar to one file; sha256 both ends.
4. Rent A100-40GB @ ₹84.24/hr; re-gate on the box; train YOLOv11l detect 1024px ~100 epochs
   (ultralytics 8.4.127); `pycocotools` eval on the 1,200 test images; destroy instance.
5. Write the benchmark row into `RESULTS_LOG.md` + a table in `main.tex` §Related Work.
6. In parallel (Track A, whoever is not on Lever 2): venue decision, 4-page cut, compliance
   handoff, upload `models/11` `best.pt` to Drive.
7. Minor: sweep the remaining `url` fields in `source.bib`; decide on the 19 DOI-less entries;
   add `paper/main.{aux,log,fls,fdb_latexmk,blg,out}` to `.gitignore`.
