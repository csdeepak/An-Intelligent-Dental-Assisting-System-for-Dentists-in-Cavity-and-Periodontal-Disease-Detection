# Clinic Dataset (SDH) — Provenance and Preprocessing Record

**Compiled:** 16 August 2026, by direct filesystem/source inspection — every claim below was
verified against an actual file, not recalled from a description.
**Scope:** Where the clinic dataset actually lives, exactly what processing has already been
run on it, and what is and isn't de-identified. This is a factual record, not a plan.
**Companion doc:** `clinical_dataset_plan.md` — the strategy document this record grounds.
Several of its §8 Open Questions are resolved below; see §6.
**Status of the underlying dataset:** real preprocessing work has already happened. This
supersedes `clinical_dataset_plan.md`'s framing of the clinic track as "nothing has been
executed yet" — that framing is now stale for the *preprocessing* question specifically, though
every governance item (ethics approval, annotation, formal PHI sign-off) is exactly as
unstarted as that document says.

> **CORRECTION — 21 August 2026.** This record's central containment claim was wrong. §1 below
> stated the clinic data is "local to this machine only"; it is not. The full
> `D:\SDH dataset\dataset\` tree — `images/`, **`metadata/index.csv`**, `logs/`, `reports/`,
> `checkpoint.json`, `SESSION_MEMORY.md` — has been on Google Drive since **4 June 2026**,
> owned by `csdeepak2005@gmail.com` and shared with a second Google account. Verified 21 Aug
> 2026 by enumerating the Drive folder tree directly (metadata only; no image or CSV content
> was opened). See §4a. This resolves §7's third open item — the answer is yes, it left the
> machine, ten weeks before this record was compiled asserting it hadn't.

---

## 1. Where everything actually lives

Three distinct locations on the same machine, representing three stages. ~~None of this is in
the git repo or on Google Drive — it is local to this machine only.~~ **Struck 21 Aug 2026 —
false.** Not in the git repo, correct; but Stage 2 in full *is* on Google Drive (§4a). The
original sentence is left visible rather than deleted so the error is auditable.

| Stage | Location | Contents | De-identified? |
|---|---|---|---|
| **Raw source** | `D:\raw data\` | 10 folders (`A.RVG` … `M.RVG`), 4,433 `.pano` DICOM files, original clinic folder structure. File count independently reconfirmed by direct search. | **No.** Original patient/study folder names throughout. |
| **Stage 1 — audit + lossless conversion** | `D:\dataset_audit\` | `FINAL_DATASET_AUDIT_REPORT.md`, `SESSION_MEMORY.md`, `scripts/` (3 Python scripts), `outputs/` (inventory CSVs, `converted_png/` — 4,420 lossless 16-bit-container PNGs preserving source folder structure, quality metrics, a 96-image sample gallery). This is the audit `clinical_dataset_plan.md` was originally written from. | **No.** `converted_png/` mirrors the raw folder structure exactly. |
| **Stage 2 — de-identified, enhanced, training-ready set** | `D:\SDH dataset\dataset\` (the folder pointed to as "the dataset") | `images\` (3,219 enhanced 8-bit PNGs, opaquely numbered `000001.png` …), `metadata\index.csv` (the identity mapping), `logs\preprocessing_run.log`, `checkpoint.json`, `reports\reference_P1_enhanced.png`, and a copy of `SESSION_MEMORY.md`. | **Images: yes. Mapping file: contains identity — see §5.** |

**One inconsistency worth knowing:** the scripts hardcode their output root as
`D:\dataset_audit\dataset`, but the actual data lives at `D:\SDH dataset\dataset`. That path
does not exist (`D:\dataset_audit\dataset` was checked directly — absent). The folder was
manually renamed or moved after generation. **If either script is ever re-run, it will write
to the old hardcoded path, not here, and silently fork the dataset in two unless the path
constants are fixed first.**

---

## 2. The exact preprocessing pipeline (Stage 2)

Recovered from the actual source, not inferred: `D:\dataset_audit\scripts\create_training_ready_dataset.py`
(the algorithm, function `enhance_opg`) and `continue_preop_dataset.py` (the checkpointed
runner that executed it — matches the log timestamps exactly).

**Per-image enhancement**, in order:

1. **Percentile windowing** — clip each image's own pixel distribution to its 0.5th–99.7th
   percentile, normalize to a 12-bit range (0–4095).
2. **Adaptive gamma** — 0.88 if the image reads as underexposed, 1.08 if overexposed, 1.0
   otherwise. Exposure is judged from that image's median/p1/p99 against the effective bit-depth
   ceiling (4095, or 65535 if the source somehow exceeded 12-bit).
3. **Median-targeting gain** — rescales so the median lands near 2150/4095, gain clamped to
   ±25% so it cannot overcorrect a genuinely dark or bright scan.
4. **Conditional CLAHE** — only triggered if the image is under/overexposed, or has contrast
   score < 650, or dynamic range < 2600. When it fires: clip limit 1.6, tile grid 12×6, applied
   on the 8-bit-downscaled version, then blended at only **35%** strength back into the
   windowed image (65% original, 35% CLAHE). Not a blanket global operation.
5. **Final output** — the enhanced 12-bit array is linearly reduced to 8-bit (÷16) and written
   as a standard grayscale PNG. This is what makes the earlier "full 0–255 range" pixel check
   correct — it's real, described, parameterized processing, not a guess.

**Quality gate** (applied per candidate, before it's kept): rejects images with aspect ratio
< 1.35 after orientation correction, width < 1800px or height < 900px, dynamic range < 900,
contrast score < 250, or insufficient tissue/teeth visibility in the central 20–82% "dental
band" of the image. Each rejection is tagged with its specific reason.

**Orientation correction:** rotates 90° if width/height < 1.0, or if the stage-1 quality scan
flagged the source as "Vertical panoramic."

---

## 3. The patient-deduplication policy ("PREOP baseline")

`choose_preop_candidates()` groups all stage-1 converted images by patient ID (parsed from the
folder path), sorts each patient's scans by study date (if known) then scan number, and **keeps
only the first/earliest scan per patient**. Every later scan for that patient is excluded and
tagged `possible_postop_or_followup_repeated_scan`.

This produced exactly 3,220 deterministic candidates (matches the log: *"Deterministic PREOP
candidate count: 3220"*); 1 was subsequently dropped by the quality gate
(`excluded_quality:insufficient_opg_resolution`, per `checkpoint.json`), leaving the final
**3,219**.

**The caveat is written into the pipeline's own output, not just implied:** *"explicit
PRE/POST labels were not present... this dataset build uses a conservative baseline policy...
Clinical validation is still required before using these labels as ground truth."* This exact
wording must travel with the data into any future write-up. It is a real, useful
leakage-prevention step (this is precisely `clinical_dataset_plan.md` §6 rule 3), but it is a
**proxy**, not a verified pre-op label.

---

## 4. De-identification — precisely, not generally

**What is real:** `images\*.png` are opaquely and sequentially named. Nothing in the filename,
and nothing found in this specific output folder, ties an image back to a patient.

**What still carries identity:** `metadata\index.csv` — the mapping table itself:

```
image_id,original_filename,source_folder,processed_filename,status
000001,<DEVICE>.RVG\<PATIENT-ID>\<SCAN>.pano,<DEVICE>.RVG\<PATIENT-ID>,images\000001.png,completed_previous
```

*(Schema only — the real values are redacted. A literal row was in the 16 Aug draft of this
record; it was replaced on 21 Aug 2026 because `source_folder` is the clinic's own patient
identifier and this file is committed. The point being illustrated is the schema, not the
value.)*

This file is what makes the de-identification reversible — which is the point of keeping it
separate, but only if it *stays* separate. **`index.csv` must never travel with `images\` to
anywhere the images go** (an annotator, a cloud GPU instance, a shared drive). If both move
together, the de-identification is void.

**Not found inside `D:\SDH dataset\dataset\`:** any copy of `PatientInfo.xml` or
`FILEDATA.TXT` — the sidecar files `clinical_dataset_plan.md` flags as "almost certainly
containing PHI." They exist only in the raw tree (`D:\raw data\`) and were not seen carried
into this folder. This is a positive sign, not a certainty — it reflects what was searched,
not an exhaustive scan of every subfolder.

**Not yet checked, and worth doing before annotation:** whether the 4 `MONOCHROME1` (inverted)
source files were corrected during the stage-1 conversion — that logic lives in
`dental_dataset_audit.py`, which has not yet been read.

---

## 4a. The dataset is on Google Drive, and the mapping file travelled with the images

**Established 21 August 2026** by enumerating the Drive tree through the Google Drive
connector. Only folder/file *metadata* was read — names, sizes, owners, parents, permissions.
No image and no CSV content was opened, deliberately.

| Drive item | ID | Note |
|---|---|---|
| `SDH dataset/` | `1hq3l7oKTWqJtaU2y32QEKIE-sNJiysNt` | owner `csdeepak2005@gmail.com`, created 2026-06-04, shared with a second Google account |
| └ `dataset/` | `1TjyhVK4PVWesJ5kqgQ0hOPqULs95U3A3` | the whole Stage-2 tree, structure identical to `D:\SDH dataset\dataset\` |
| ├ `images/` | `1Nk93Tw00zznjyhrilzt3agKjNIwQtcWm` | the 8-bit enhanced PNGs |
| ├ **`metadata/index.csv`** | `1kiqa0WiJFMsBAzGJ6mG2ph33cvUaIdTS` | **267,337 bytes — the re-identification mapping** |
| ├ `logs/preprocessing_run.log` | `1NSUsOMI-MbQqwWJyTcPskRsU8eLoelLo` | |
| ├ `reports/` | `1jP4apNP-yapbsXzUSDw4HJzyo6F5dtdh` | |
| ├ `checkpoint.json` | `1kWtFWs_gX1m3bJAFkFoVH1aE71AHMQwy` | |
| └ `SESSION_MEMORY.md` | `12XJRu_d6Rr-Fqwfl5OOnojM0SfbKjF5c` | |

**This is the exact failure mode §4 above warned about, and it had already happened ten weeks
before §4 was written.** §4's rule reads: *"`index.csv` must never travel with `images\` to
anywhere the images go... If both move together, the de-identification is void."* On Drive they
are siblings under the same shared parent. Anyone with access to that folder holds both the
opaquely-named images and the table that maps them back to clinic patient folders. The
file-structure de-identification described in §4 provides **no protection** for this copy.

**What is not wrong:** the sharing is account-to-account, not a public link. The permissions on
`SDH dataset/` and `dataset/` list no `type: anyone` entry — unlike the Tufts research-data
folder (`1_pPXCzNGlRuLaQhpqScX7sszSXSLQI-U`), which is shared `role: writer, type: anyone`,
i.e. **anyone with that link can edit or delete its contents**. That folder holds public Tufts
data, so the exposure there is integrity (someone could alter the dataset this project
re-downloads from), not confidentiality — but it should not be world-writable either.

**Nothing was changed on Drive.** Altering sharing settings on an account this project does not
own is the owner's action to take, not something to do on their behalf.

**Recommended, in order:**

1. **Separate `index.csv` from `images/` on Drive** — move it out of the shared tree entirely,
   or delete the Drive copy of the mapping and keep it only on the origin machine. Until then
   this copy of the dataset is not de-identified in any meaningful sense.
2. **Enumerate who actually has access** to `SDH dataset/` and confirm every one of them is a
   person the clinic would accept having identifiable data. Record the answer here.
3. **Check Google Drive's activity/sharing history** for that folder — whether it was ever
   link-shared before the current settings, and whether anything was downloaded. Neither
   question can be answered from file metadata alone.
4. **Tighten the Tufts folder** from "anyone can edit" to "anyone with the link can view", or
   restrict it outright.
5. Treat this as the concrete trigger for the governance items below: an unapproved,
   re-identifiable copy of clinic data already exists off the origin machine.

---

**Unchanged from `clinical_dataset_plan.md`:** no formal written de-identification policy
exists, no IRB/ethics approval has been sought, and no written agreement with the clinic
covering research use exists. This record advances the *technical* de-identification question;
it does not substitute for the *governance* one.

---

## 5. What this changes about the near-term plan

Nothing in `MASTER_PLAN_2026H2.md`'s critical path changes — Ningxia is still the fast,
unblocked external-validation source, and the clinic track is still background, IRB-gated work.
What changes is confidence: **Tier 1a (label-free diagnostics) on this clinic data is closer to
runnable than assumed two messages ago.** The images are real, describably processed, and
file-structure de-identified. The remaining blockers are governance (ethics sign-off, a written
clinic agreement) and two small verification items (§4's `MONOCHROME1` question, and confirming
`index.csv` has never left this machine), not missing engineering.

---

## 6. `clinical_dataset_plan.md` §8 Open Questions — status update

| Question | Status |
|---|---|
| What produced `checkpoint.json` (3,219 images)? | **Resolved.** `continue_preop_dataset.py`, the checkpointed runner for the enhancement pipeline in §2, applied to the PREOP-baseline candidate set in §3. |
| PHI / de-identification policy before annotator access? | **Advanced, not closed.** The file-structure mechanism is real (§4). No formal written policy or sign-off exists yet. |
| Dentist availability and hours committed? | Untouched by this record. |
| External clinical records for treatment dates? | Untouched. |
| Caries definition on panoramic images? | Untouched. |
| The 13 failed `.PANO` files? | Untouched, still low priority. |

---

## 7. Open items from this record specifically

- [ ] Read `dental_dataset_audit.py` (stage 1, not yet reviewed) to confirm `MONOCHROME1`
      inversion was handled correctly for the 4 affected source files.
- [ ] Fix the hardcoded `D:\dataset_audit\dataset` path in both stage-2 scripts if they will
      ever be re-run, to match the actual `D:\SDH dataset\dataset` location.
- [x] ~~Confirm with whoever ran this originally whether `D:\SDH dataset\dataset` (or any subset)
      has already left this machine.~~ **Answered 21 Aug 2026: yes — all of it, to Google
      Drive, on 2026-06-04, with `index.csv` alongside the images. See §4a.** Replaced by the
      five follow-up actions listed there.
- [ ] When ready, regenerate the human-readable summary docs (`PREPROCESSING_CONFIG.md`, the
      three `reports/*.md` files) that `create_training_ready_dataset.py` would have produced
      on an uninterrupted run — the parameters are already known (§2), so this doesn't require
      touching the images again.
