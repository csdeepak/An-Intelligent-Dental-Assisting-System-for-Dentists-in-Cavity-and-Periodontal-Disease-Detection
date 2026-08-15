# Methodology changelog

**Purpose.** A dated, append-only paper trail for every change to *how* a result was
produced — as opposed to `RESULTS_LOG.md`, which records *what* the result was. This file
exists so that a discrepancy between what the code does and what the write-up claims has a
visible resolution history rather than looking like it was quietly patched.

**Convention.** Newest at the bottom. Never edit an existing entry; if an earlier decision is
reversed, add a new entry that says so and links back. Every entry states: what was
discovered, how it was verified, what was decided, and what still has to happen.

Required by `PUBLICATION_TODO.md` T0.1.

---

## 2026-08-15 — Universal→FDI lower-arch mapping corrected

**Status:** Closed.

### What was wrong

The Universal→FDI conversion table mis-mapped the entire lower arch from Universal 23
onward, in **two independent places**:

- `configs/dataset_config.yaml` (lines 122–131)
- `src/utils/fdi_converter.py` (`UNIVERSAL_TO_FDI`, plus the module docstring)

Both encoded the same wrong values. Prior documentation (root `README.md`, `CLAUDE.md`,
`docs/session-memory/2026-08-12-…`) flagged only the YAML; the Python module was carrying the
identical error unnoticed.

| Universal | Was (wrong) | Now (correct) | Effect of the error |
|---|---|---|---|
| 23 | 43 | **32** | lower-left teeth reported as lower-right |
| 24 | 44 | **31** | lower-left teeth reported as lower-right |
| 25–28 | 45–48 | **41–44** | wrong quadrant *and* wrong position |
| 29–32 | 31–34 | **45–48** | wrong quadrant *and* wrong position |

Secondary consequence: the wrong table emitted FDI **33 and 34 twice each** (from Universal
22/31 and 21/32). Because `FDI_TO_UNIVERSAL` is built by inverting the dict, those duplicates
silently collapsed — the reverse lookup for 33 and 34 returned the *later* key, so two real
teeth shared one code and two reverse mappings were lost.

### How it was verified

Derived the correct table independently from the FDI two-digit standard (first digit =
quadrant 1–4, second = distance from midline 1–8), then cross-checked against the table in
the root `README.md` and the correction noted in `CLAUDE.md`. All three agree.

### Why it survived this long

`tests/test_fdi_converter.py` **asserted the buggy value**:

```python
assert universal_to_fdi("32") == 34   # standard requires 48
```

The test had been written by reading the implementation rather than the dental standard, so
it locked the defect in place and reported green. This is the more important finding of the
two — a test derived from the code under test cannot detect a wrong implementation.

### Blast radius — no reported result is affected

Checked every notebook and script for actual use of the mapping. The only references in the
bone-loss notebooks are in **markdown/comment text** describing the intended pipeline
("Join outputs on FDI key", "Universal → FDI conversion at YOLO output"); no executed cell
imports or applies `universal_to_fdi`. `scripts/run_inference.py` references it but is the
un-built Stage 5/6 stub.

**Therefore: no training label, no crop assignment, and no published metric was ever produced
through the wrong table.** The bug was latent and would have first caused damage at Stage 5
integration — which is exactly the next thing being built, so it was caught in time.

### Fix applied

- Corrected both files; they are now verified equal to each other programmatically.
- Corrected the misleading docstring in `fdi_converter.py` (it described the wrong lower-arch
  order in prose as well as in code).
- Rewrote `tests/test_fdi_converter.py` against the **standard**, not the implementation.
  Eight tests, including two property checks that would have caught the original bug:
  `test_quadrant_digit_is_correct` (catches quadrant swaps regardless of within-quadrant
  order) and `test_mapping_is_bijective` (catches duplicate FDI codes). All pass.

---

## 2026-08-15 — Caries-track augmentation discrepancy resolved (T0.1)

**Status:** Diagnosis closed; corrective re-run scheduled for W2.

### The finding, confirmed at code level

`notebooks/caries/phase-1.ipynb` **defines** an augmentation pipeline and **never applies
it**:

- **Cell 107** defines `transform_train` (`RandomRotation(10)`, `RandomHorizontalFlip()`,
  `ColorJitter(0.2, 0.2)`) and `transform_val`.
- **Cell 108**, the immediately following cell, builds the datasets with
  `ImageFolder(..., transform=transform)` — referencing the *stale, plain*
  resize→ToTensor→Normalize variable defined back at cell 81, not the augmented one.

Verified exhaustively: `transform_train` and `transform_val` each appear **exactly once** in
the entire notebook — at their own definition. **Zero uses.** They are dead variables. This
is a variable-shadowing slip, not a deliberate choice.

Confirmed independently by the author's own critique in `notebooks/caries/approach.txt`
line 33, which reached the same conclusion.

### Scope — caries only; the bone-loss track is clean

Audited the same way:

| Track | Notebook | Augmentation actually applied? |
|---|---|---|
| Caries cascade | `caries/phase-1.ipynb` | ❌ **No** — defined, never wired in |
| Bone loss binary | `bone_loss/03_bone_loss_model_training.ipynb` | ✅ Yes — `train_transform` passed to the dataset |
| Bone loss severity | `bone_loss/04_bone_loss_severity.ipynb` | ✅ Yes — offline minority-class copies via `augment_transform`, **and** on-the-fly `train_transform` passed positionally to `SeverityDataset` |

The project's strongest result (bone-loss binary, macro-F1 0.9233) is **not** affected. The
defect is isolated to the caries numbers: val acc 0.81, macro-F1 0.77.

### The documentation was already honest — nothing to retract

T0.1 step 3 asks for a repo-wide grep for text claiming augmentation on the caries track, to
be corrected. **That grep found nothing to correct.** Every place the caries track is
described already states the truth:

- `docs/results/PAPER_MATERIAL.md` §8.1 — "Augmentation was defined but never applied… The
  reported caries numbers come from training on a small fixed dataset with **no
  augmentation**."
- `docs/reports/pes_capstone_report/chapters/04_methodology.tex` §Data Augmentation — "the
  exported notebook shows that the final reported run used the plain resize-and-normalize
  transform rather than the augmented version. This is therefore treated as a limitation of
  the current caries experiment rather than as an implemented benefit."
- `docs/results/RESULTS_LOG.md` (2026-04-21 entry) and `notebooks/caries/approach.txt`.

This materially lowers the credibility risk `gap_analysis.md` §2C assigned to this item. The
hazard it described — *"the write-up describes an augmentation pipeline that did not run"* —
never materialised in any artefact. What existed was a **code/intent** discrepancy that the
prose had already disclosed, not a false claim in a methods section.

### Decision

`PUBLICATION_TODO.md` T0.1 offers two paths: **(a)** enable augmentation and re-run and
re-report every caries number, or **(b)** state in the methods that none was applied.

**Chosen: (a), executed as a two-arm comparison.**

Reasoning:

1. The caries cascade is **already scheduled for a full re-run in W2** for unrelated Tier-0
   reasons — T0.2 (carve a patient-level held-out test split) and T0.3 (replace
   accuracy-based checkpointing with macro-F1). The augmentation fix therefore costs
   approximately **one extra GPU-hour**, not a new experiment.
2. Running **both arms** (plain vs. augmented, everything else identical) converts a
   liability into evidence: it produces a real ablation data point for contribution C5 in
   `../research/MASTER_PLAN_2026H2.md`, and answers "did augmentation help?" with a
   measurement instead of an assertion.
3. Path (b) would mean knowingly shipping a weaker model when the corrective run is already
   on the calendar.

**Until that re-run completes, every caries number in circulation — val acc 0.81, macro-F1
0.77 — remains a no-augmentation, validation-only, accuracy-checkpointed figure and must be
labelled as such.** Do not quote it without those three qualifiers.

### Outstanding

- [ ] W2: re-run the caries cascade, both arms, with the held-out test split (T0.2) and
      macro-F1 checkpointing (T0.3). Report val **and** test separately for each arm.
- [ ] Update `model_metrics.md` and `PAPER_MATERIAL.md` §7.2 with the new numbers, and add
      the plain-vs-augmented comparison to the ablation table.
- [ ] Update `04_methodology.tex` §Data Augmentation once the re-run lands — the current
      wording is accurate for the *current* numbers and must not be changed before they are
      superseded.

---

## 2026-08-15 (b) — Capstone report archived; one action item above is now moot

**Status:** Note only. Does not change any result or decision.

`docs/reports/pes_capstone_report/` was relocated out of the tracked tree to
`_repo_archive/pes_capstone_report/` at the project owner's request; writing effort moves to
the research paper in `../research/MASTER_PLAN_2026H2.md`. Content preserved in git at commit
`6310790` and on disk in the archive — see `_repo_archive/ARCHIVE_MANIFEST.md`.

Consequence for the entry above ("Caries-track augmentation discrepancy resolved"): its final
outstanding item — *"Update `04_methodology.tex` §Data Augmentation once the re-run lands"* —
**no longer applies**, because that file is no longer part of the working repo. The equivalent
obligation now attaches to whatever methods section the research paper uses. Per this file's
append-only convention the original entry is left unedited; this note supersedes that one
line only. The other two outstanding items (the W2 two-arm re-run, and updating
`model_metrics.md` / `PAPER_MATERIAL.md` §7.2) stand unchanged.
