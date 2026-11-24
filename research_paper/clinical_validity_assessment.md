# Clinical validity assessment

Phase 8 deliverable. The system is assessed as what the evidence shows it is: a **research
prototype for radiographic decision support**. No clinical trial, dentist evaluation, ethics
approval or regulatory certification exists for it, and none is implied anywhere in the paper.

## 1. Four distinctions the paper keeps

| Model output | What it is | What it is not | Where stated |
|---|---|---|---|
| Caries flag on tooth N | the lesion detector placed a box mostly inside tooth N's detected box | a confirmed carious lesion; a clinical caries diagnosis (no clinical exam, no bitewing, no histology) | VII Clinical implications |
| Caries severity (Stage 3b) | a ResNet18 grade "caries / deep caries" validated on 133 crops | a tested severity estimate (no test set exists) | IV; Table 3 |
| Stage-4 abnormality flag | crop overlaps a Tufts expert *abnormality* mask (apical lesions, sclerosis, cysts) | periodontal bone loss; periodontitis | Abstract; IV; VI-F; VII; IX |
| Report confidence | a model score | a calibrated probability (only the retired crop classifier was calibrated, on development data) | VI-E; VII |

## 2. Caries: what the numbers mean for a patient

On the 164 development images (in-domain for the detector — optimistic; DENTEX caries annotations outline whole teeth, so these are tooth-level counts):
- **Missed carious teeth:** 203 of 477 annotated carious teeth were not flagged (42.6%). A negative
  report cannot be read as caries-free. False negatives are the clinically costly error for
  caries: an untreated lesion progresses.
- **Flags without an annotated lesion:** of 624 flags, 260 (41.7%) fall on teeth with no
  annotation and 90 (14.4%) on teeth with another finding. DENTEX does not document that its
  annotation is exhaustive, so these are of unknown status, not confirmed false positives.
- **External:** on four Ningxia sites the detector's lesion agreement was 0.684 against the
  constant's 0.591; it did not separate from the constant at one site (test1). No external
  cohort has healthy-tooth labels, so specificity cannot be estimated externally.
- **Reference standard:** panoramic-only labels detect proximal caries less accurately than
  bitewings (Akarslan et al. 2008); the expert lesions are a subset of disease.

## 3. Periodontal disease: why the system makes no claim

The repository and capstone title promise "periodontal disease detection". The evidence does not
support it:

1. **Label.** Stage 4's positive class is "crop overlaps a Tufts expert abnormality mask". The 41
   radiographs supplying every positive are described as apical lesions, sclerosis and cysts; the
   three Tufts radiographs described as periodontal bone loss supply none (`PAPER_MATERIAL.md`
   §8.28).
2. **What a valid label looks like.** Radiographic bone loss is measured against anatomical
   references — percentage bone loss against the CEJ and root (Krois et al. 2019; Chang et al. 2020).
   A periodontitis diagnosis is staged from periodontal breakdown relative to root length, tooth
   loss and clinical complexity factors such as pocket depth and furcation involvement (Tonetti et
   al. 2018). A strong periodontal model links OPGs to clinical diagnoses (Li et al. 2025).
3. **Performance even on its own label.** First model: 0.923 macro-F1 on a crop-level split was a
   split artefact; 7.6% sensitivity held out. Retrained by radiograph: 27.5%, 16.5%, 11.0%
   sensitivity across three seeds. Severity head: trained on crop contrast; retrained on overlap
   bands, below an image-blind position prior.
4. **Consequence.** The paper calls Stage 4 an abnormality flag, reports it in one paragraph, and
   withholds the severity grade. The proposed title drops "periodontal". This is the single
   largest gap between the project's stated aim and its evidence.

## 4. Assessment against the prompt's checklist

| Item | Status | Evidence |
|---|---|---|
| Annotation quality | single public expert labels; inter-rater agreement not reported by the releases used; panoramic-only | dataset papers; L006 |
| Ground-truth reliability | DENTEX exhaustiveness undocumented; Ningxia lesion masks from release; Tufts abnormality masks | §2; L010 |
| Expert validation of outputs | **none** — no dentist reviewed the system's outputs | — |
| Dataset representativeness | five public cohorts (Tufts: United States; UFBA-425: Brazil; Ningxia: China, per their dataset papers; DENTEX and CariesXrays origins not re-verified here); no Indian cohort; no age or sex breakdown is used in any analysis | Table 4 |
| Generalisation across institutions | four Ningxia sites (one is the training centre of that release, not of our models); lead not shown for an unseen site (prediction interval −36.08 to +55.29) | VI-D |
| Orientation / acquisition sensitivity | detector expects rotated input and rotates internally; README records 7.5% recall if upright input is fed to the raw model; UFBA squashed export drops numbering to 44.5% (77.2% widened) | `src/orientation.py`; Table 1 |
| False-negative implications | 42.6% of carious teeth unflagged on development data | §2 |
| Model uncertainty | numbering and crop-classifier confidences rank errors (shuffle control); lesion detector uncalibrated | VI-E |
| Patient privacy | public de-identified releases only; the SDH clinic set (de-identification void) contributes to no result; Tufts pixels are not shown | `transfer.md` §4 |
| Ethics / regulation | no human participants; no approval claimed; no regulatory status; `[ASK AUTHOR]` for an institutional exemption statement | paper Ethics Statement |

## 5. Framing used in the paper

"A research prototype for decision support, not evaluated with dentists or patients; its findings
are radiographic and model-derived; it supports use as a second reader in research, not as a
screening or diagnostic device." The demonstration app already displays "This pipeline is **not
clinically validated**" on every result (`app.py`).
