# Literature review — verified sources only

Phase 5 deliverable. Every work below resolves on at least one bibliographic index and its cited
claim was checked against the work's own abstract or full text. Nothing here is cited from memory.

## 1. Search and verification protocol (what was actually done)

| Layer | What | When / record |
|---|---|---|
| Project review sheet | 117 papers reviewed by the authors; 49 task-relevant (tooth detection/numbering, caries, periodontal bone loss on radiographs) | Jan–Aug 2026; `docs/results/PAPER_MATERIAL.md` §2.1, `outputs/related_work_extract.csv` |
| Four-index audit of `paper/source.bib` (104 entries) | Crossref, OpenAlex, Semantic Scholar, arXiv resolution with title cross-check; Crossref retraction filter; claim checked against abstract or full text | 2 Nov 2026; `outputs/citation_audit/2026-11-02_ars/` |
| This session: targeted gap search | 10 candidate DOIs for areas not yet covered (foundational numbering, periodontal bone loss and staging, methodological failures, hidden stratification, clinical translation, TRIPOD+AI); each resolved on Crossref (title, first author, venue, year, volume, pages) and its abstract fetched from OpenAlex with the retraction flag | 23 Nov 2026; `research_paper/literature/abstracts_new_2026-11-23.json`, fetch script beside it |
| This session: re-check of 6 `source.bib` entries used for new claims | OpenAlex abstract + retraction flag | `research_paper/literature/abstracts_sourcebib_2026-11-23.json` |
| RCE gate GL | `tools/verify_citations.py --gate --online` on the source registry | `research_paper/.rcs/audits/gates/GL_citations.json` (see `integrity_check_report.md`) |

**Not done, stated plainly:** no direct query of IEEE Xplore, PubMed, Google Scholar, Springer,
ScienceDirect or ACM DL search interfaces was run in this session; the indexes above (Crossref,
OpenAlex) cover those publishers' records but a systematic search with a PRISMA flow was not
performed. One candidate (Lee et al. 2018, *J Dent*) was dropped because no abstract could be
retrieved to check the claim against. Three DOIs typed from memory returned 404 and were
discarded — not used anywhere.

## 2. Comparison table

Metrics are as the cited abstract states them. "Ours" uses the current pipeline's numbers
(`docs/results/model_metrics.md`, `paper/main.tex`), not the pre-11-Oct ones in
`PAPER_MATERIAL.md` §2.1.2.

| Work (year) | Dataset | Method | Task | Evaluation protocol | Reported metrics | Limitation (from the abstract or our reading) | Relevance |
|---|---|---|---|---|---|---|---|
| Tuzoff et al. (2019) | 1,352 adult OPGs; 222 test | Faster R-CNN + VGG-16 + arch heuristics | detection + FDI numbering | separate test set, vs experts | detection sens 0.9941, prec 0.9945; numbering sens 0.9800 | single source; no external set | foundational two-stage numbering; our Stage 2 adds Hungarian assignment |
| Zancan et al. (2025) | 935 OPGs (+ DENTEX) | Inception-v3 / InceptionResNet-v2 on crops | numbering + cavities | 5-fold CV, internal | numbering acc 0.9988, F1 0.979 | crop classification ≠ numbering under detector output | why we report end-to-end numbering |
| Zhang et al. (2025, JBHI) | Tufts, O2PR, multi-pathology cohort | SADP-Net multi-stage | instance seg + FDI numbering | internal splits on three datasets | "superior" to baselines (abstract) | no image-blind or external-site test | Tufts numbering context |
| Budagam et al. (2024) | UFBA-425 | OralBBNet (U-Net + YOLOv8) | seg + detection | internal | +1–3% mAP detection | — | source of our only unseen numbering corpus |
| van Nistelrooij et al. (2024) | OdontoAI + DENTEX combined | two-stage seg/FDI → multi-label | caries, impacted, periapical | public-data combination | FROC, mAP | combining public sets is non-trivial | precedent for our multi-corpus detector |
| Chen et al. (2024, AAAI) | CariesXrays, 6,000 OPGs, 13,783 lesions | FPCL (contrastive feature pyramid) | caries lesion detection | dataset split | AP 48.2 (paper text) | one hospital | our lesion detector's training corpus and benchmark row |
| Bizjak & Robič (2024) | DENTEX + Slovenian clinic | YOLOv8 enumeration → caries | caries | internal + external | lesion sens 0.70 → 0.67 | — | one of two externally validated papers in our 49 |
| Mutlu et al. (2026) | 1,579 in-house + 718 external OPGs | YOLOv11 vs YOLOv12 | 13 conditions incl. caries, bone loss | internal + external | mAP@0.5 0.857 → 0.806 | weakest on caries and bone loss | external-degradation context |
| Krois et al. (2021) | 650 Charité + 650 KGMU OPGs | U-Net | apical lesions | cross-centre | F1 54.1% → 32.7% | — | dental domain shift |
| Mohammad-Rahimi et al. (2022) | systematic review | — | caries | — | 86.1–96.1% accuracy on panoramic | low study quality/reporting | caries field context |
| Krois et al. (2019) | 2,001 OPG segments | 7-layer CNN | periodontal bone loss | 10× group shuffling; vs 6 dentists | acc 0.81, sens 0.81, spec 0.81 | segment-level, internal | what a *real* PBL label is (measured % PBL) |
| Chang et al. (2020) | OPGs | DL (bone level / CEJ) + CAD | PBL % → periodontitis stage | vs radiologists | Pearson 0.73, ICC 0.91 | radiographic staging only | measurement-based PBL; contrast with our mask-overlap label |
| Cerda et al. (2024) | 2,010 OPGs (Tufts + Chile) | statistics + CNN + PBL % algorithm | PBL presence/%/stage | 40-image test vs 5 clinicians | weighted F1 0.29; severe PBL F1 0 | tiny test | PBL is hard on this data |
| Li et al. (2025, HC-Net+) | 10,881 OPGs; 382 clinically labelled + 760 from 4 centres | HC-Net+ | periodontitis (clinical diagnosis) | dual benchmark, multicentre, trial-registered | AUROC 94.2% vs specialists 85.6% | — | what a periodontal claim requires: labels linked to clinical diagnosis |
| Lee et al. (2025) | meta-analysis | — | periodontitis, by modality | random effects | panoramic accuracy 88.2% (binary), 88.9% (staging) | heterogeneity across modalities | field-level PBL performance |
| Xia et al. (2025, BRAR) | 1,104 patients | dataset | bone resorption grading | periodontist-validated | — | — | a periodontal label we did not use |
| Tonetti et al. (2018) | consensus | — | periodontitis staging/grading | — | stage = severity (breakdown vs root length, tooth loss) + complexity (pocket depth, furcation, mobility) | — | radiographic bone loss alone is not a periodontitis diagnosis |
| Geirhos et al. (2020) | — | — | shortcut learning | — | — | — | theory frame |
| Goyal et al. (2017); Agrawal et al. (2018); Poliak et al. (2018) | VQA, NLI | input-blind baselines | — | — | priors inflate scores | — | precedent for our image-blind constant |
| Zech et al. (2018); DeGrave et al. (2021) | chest radiographs | — | pneumonia / COVID-19 | multi-site | hospital alone AUC 0.861; shortcuts fail at new hospitals | — | site effects in medical imaging |
| Oakden-Rayner et al. (2020) | CIFAR-100 + medical datasets | — | hidden stratification | — | aggregate metrics hide subgroup failure | — | why we report per site and per tooth type |
| Varoquaux & Cheplygina (2022) | review | — | methodological failures | — | biases at every step | — | framing for our selection-on-test disclosures |
| Kim et al. (2019) | 516 imaging AI studies | — | — | — | 31 (6%) externally validated | — | external validation is rare |
| Kelly et al. (2019); Schwendicke et al. (2020) | reviews | — | clinical translation of AI (medicine, dentistry) | — | RCT-grade clinical evaluation as gold standard (Kelly) | — | why "runs" ≠ clinically ready |
| Mongan et al. (2020, CLAIM); Schwendicke et al. (2021); Collins et al. (2024, TRIPOD+AI) | checklists | — | reporting | — | — | — | reporting standards for the paper |
| Guo et al. (2017); Zadrozny & Elkan (2002); Naeini et al. (2015); Geifman & El-Yaniv (2017) | — | temperature scaling, isotonic, ECE, selective classification | calibration, abstention | — | — | — | methods for RQ3 |

## 3. Synthesis by question

1. **AI-assisted panoramic interpretation and tooth detection/numbering.** Two-stage
   detect-then-classify numbering is established (Tuzoff 2019) and reported near ceiling on crops
   (Zancan 2025). Reported figures usually classify correctly detected crops; end-to-end
   numbering under detector output — what a per-tooth report depends on — is rarely reported.
2. **Caries.** Accuracies of 86.1–96.1% on panoramic images come from low-quality, mostly
   internal studies (Mohammad-Rahimi 2022). Lesion detection benchmarks exist (CariesXrays), and
   two of the 49 task-relevant papers in the authors' review validate externally.
3. **Periodontal bone loss.** Valid PBL work measures bone level against the CEJ or root length
   (Krois 2019, Chang 2020) or links images to clinical diagnoses (Li 2025). Staging needs clinical
   measures beyond the radiograph (Tonetti 2018). An independent group on Tufts-derived data
   reports weighted F1 0.29 and F1 0 for severe PBL (Cerda 2024).
4. **Multitask/modular systems.** Combining public datasets for multi-task tooth assessment is
   done (van Nistelrooij 2024; Mutlu 2026), typically evaluated per task and internally.
5. **Generalisation and domain shift.** Dental models degrade across centres (Krois 2021: F1
   54.1% → 32.7%; Mutlu 2026: 0.857 → 0.806, weakest on caries). Medical-imaging models exploit
   site and prevalence (Zech 2018, DeGrave 2021); aggregate metrics hide subgroup failures
   (Oakden-Rayner 2020).
6. **Calibration, uncertainty, clinically meaningful evaluation.** Standard tools exist (Guo 2017,
   Zadrozny 2002, Geifman 2017); reporting checklists ask for external validation and failure
   analysis (CLAIM, TRIPOD+AI, Schwendicke 2021); clinical value needs prospective evaluation
   (Kelly 2019).

## 4. The genuine research gap (and what is not a gap)

**Gap, supported by the sources above:** input-blind baselines are standard in VQA and NLI and
site confounding is documented in chest radiography, but **no work found in this search or in the
authors' 49-paper review reports an image-blind baseline for tooth-level caries scores on
panoramic radiographs**, and none derives what such a baseline scores. Combined with the rarity of
external validation (6% in medical imaging; 2 of 49 here), a tooth-level caries figure in this
literature cannot currently be read as evidence that a model reads the radiograph.

Scope of that claim: "none found" is bounded by a non-systematic search plus the authors' review;
the paper words it as an observation, not a count (`paper/ieee/open_issues.md`).

**Not a gap this project fills:**
- *Accurate periodontal disease detection* — others measure PBL with valid labels (Krois 2019,
  Chang 2020) and link to clinical diagnosis (Li 2025); this project has no periodontal label.
- *State-of-the-art caries or numbering accuracy* — the absolute numbers here are below several
  published ones (Tuzoff 2019; Zancan 2025), and no matched comparison licenses "SOTA".
- *A modular pipeline as such* — two-stage dental systems are common.
