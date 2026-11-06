"""Build the Research Communication Engine trail (.rcs/) for the Phase 3 report: content preparation.

Writes plan/paper_config.json, evidence/research_evidence.json, claims/claim_evidence_map.json,
corpus/source_registry.json and state.json, in the skill's schemas (skill/schemas/*.schema.json).
Evidence locators are paths relative to the project root, the repository worktree (two levels above
report/phase3). Every claim tag {C###} / {L###} in the TeX (written as a comment, `% {C001}`) has an
entry here. Gates are not marked here: tools/rcs_check.py runs the checks and records them.

    python -I tools/rcs_build.py      (needs build/references.bib, written by tools/build.sh)
"""
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RCS = HERE / ".rcs"
TODAY = date.today().isoformat()
P = "report/phase3/.rcs"          # prefix for report-local evidence files, relative to ROOT


def write(rel, obj):
    f = RCS / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- Phase 2 report text as a record
p2 = Path.home() / "AppData/Local/Temp/claude"
src_txt = next(p2.rglob("phase2_fulltext.txt"), None)
if src_txt is not None:
    (RCS / "evidence").mkdir(parents=True, exist_ok=True)
    (RCS / "evidence" / "phase2_report_text.txt").write_text(src_txt.read_text(encoding="utf-8"), encoding="utf-8")

# ---------------------------------------------------------------- evidence items
# kind must be one of the schema's kinds; strength 'hard' = a saved run artefact or code, 'soft' = a
# project record or draft written about a run.
EV = [
    # id, kind, strength, summary, locator
    ("E001", "result", "soft", "Ten-page paper draft, number-traced (390 numbers, 6 explained) on 2 Nov 2026", "paper/paper.md"),
    ("E002", "result", "hard", "Stage-1 switch result set: numbering, lesion agreement, FDI-set F1, per-site Ningxia, flagged teeth", "outputs/stage1_switch/stage1_switch_results.json"),
    ("E003", "result", "hard", "DerSimonian-Laird pooling of the four Ningxia sites", "outputs/stage1_switch/F_ningxia_random_effects.json"),
    ("E004", "result", "hard", "HKSJ and Q-profile intervals beside DL", "outputs/stage1_switch/F_ningxia_random_effects_hksj.json"),
    ("E005", "result", "hard", "Constant stability, operating curve and matched-volume comparison", "outputs/review_round1/constant_stability_and_curve.json"),
    ("E006", "negative_result", "hard", "DENTEX perceptual-hash near-duplicate check: no near-duplicate copy found", "outputs/review_round1/dentex_near_duplicates.json"),
    ("E007", "result", "hard", "Positional-shortcut test of the crop classifier", "outputs/caries_position_bias/caries_position_bias_test.json"),
    ("E008", "result", "hard", "Crop-classifier calibration on 863 test crops", "outputs/calibration/caries_gate_calibration_test.json"),
    ("E009", "result", "hard", "Isotonic calibration of the crop classifier", "outputs/calibration/caries_gate_isotonic.json"),
    ("E010", "result", "hard", "Coverage-accuracy (abstention), shipped detector", "outputs/stage1_switch/J_coverage_arm3c/c4_coverage_accuracy.json"),
    ("E011", "result", "hard", "Numbering failure taxonomy, shipped detector", "outputs/stage1_switch/I_taxonomy_arm3c/stage2_failure_taxonomy.json"),
    ("E012", "baseline", "hard", "Constant baselines beside the Qwen2.5-VL-32B arm", "outputs/c1_vlm/c1_constant_arm_vlm_32b_0shot.json"),
    ("E013", "negative_result", "hard", "Five repairs of the crop classifier against a same-day control: none separated from zero", "outputs/caries_arms/arms_comparison.json"),
    ("E014", "result", "hard", "Asserted facts of the draft figures R04-R08", "paper/ieee/figures/R_draft_figures_facts.json"),
    ("E015", "result", "hard", "Asserted facts of figures R01-R03", "paper/ieee/figures/R_figures_facts.json"),
    ("E016", "observation", "hard", "Saved report for DENTEX test_0 (schema opg-report/1.6)", "paper/ieee/figures/R02_test_0_report.json"),
    ("E017", "metric", "hard", "Learnable parameter counts of every default checkpoint", "outputs/param_counts/param_counts.json"),
    ("E018", "experiment", "hard", "Stage-1 multi-corpus detector run summary", "models/15_detector_multicorpus_leverA/run_summary.txt"),
    ("E019", "experiment", "hard", "Lesion detector (Lever B) run summary", "models/16_lever_b_pooled/run_summary.txt"),
    ("E020", "experiment", "hard", "Numbering head v2.0 run summary", "models/10_fdi_head_dentex_tufts_v2/run_summary.txt"),
    ("E021", "experiment", "hard", "Crop classifier v3 run summary", "models/09_caries_gate_v3/run_summary.txt"),
    ("E022", "experiment", "hard", "Caries cascade (severity) run summary", "models/07_caries_cascade/run_summary.txt"),
    ("E023", "experiment", "hard", "Stage-4a radiograph-split retrain run summary", "models/18_bone_loss_radiograph_split/run_summary.txt"),
    ("E024", "experiment", "hard", "Phase 2 bone-loss binary model run summary", "models/03_bone_loss_model_training_notebook_models/run_summary.txt"),
    ("E025", "experiment", "hard", "Phase 2 bone-loss severity run summary", "models/04_bone_loss_severity_notebook_models/run_summary.txt"),
    ("E026", "negative_result", "hard", "Phase 2 CEJ heuristic summary", "models/05_cej_estimation_v2_models/cej_v2_summary.txt"),
    ("E027", "result", "soft", "Project snapshot: results ledger and decisions", "transfer.md"),
    ("E028", "result", "soft", "Current-best model scoreboard", "docs/results/model_metrics.md"),
    ("E029", "result", "soft", "Paper material: methods, results and limitations", "docs/results/PAPER_MATERIAL.md"),
    ("E030", "result", "hard", "pytest run, 6 Nov 2026", P + "/evidence/runs/pytest_2026-11-06.txt"),
    ("E031", "result", "hard", "verify_paper_numbers.py run, 6 Nov 2026", P + "/evidence/runs/verify_numbers_2026-11-06.txt"),
    ("E032", "result", "hard", "verify_invariants.py run, 6 Nov 2026", P + "/evidence/runs/invariants_2026-11-06.txt"),
    ("E033", "observation", "soft", "Phase 2 report text (PW26_MHR_06, Jan-May 2026)", P + "/evidence/phase2_report_text.txt"),
    ("E034", "external_fact", "hard", "Abstracts of the Phase 2 references (Crossref/OpenAlex/S2)", P + "/corpus/p2_abstracts.json"),
    ("E035", "external_fact", "hard", "Abstract of Albano et al. 2024", P + "/corpus/p3_abstracts.json"),
    ("E036", "external_fact", "hard", "Abstract of Iacob et al. 2025", P + "/corpus/p3b_abstracts.json"),
    ("E037", "external_fact", "hard", "Abstracts the ten-page draft's claims were checked against", "outputs/citation_audit/2026-11-02_ars/claim_abstracts.json"),
    ("E038", "implementation_detail", "hard", "Pinned package versions", "requirements-lock.txt"),
    ("E039", "implementation_detail", "hard", "Container definition", "Dockerfile"),
    ("E040", "implementation_detail", "hard", "Integration script: thresholds, schema, checkpoints", "scripts/run_inference.py"),
    ("E041", "implementation_detail", "hard", "Stage 3-4 classifiers and crop conventions", "src/classifiers.py"),
    ("E042", "implementation_detail", "hard", "Numbering head inference and assignment", "src/fdi_head_inference.py"),
    ("E043", "implementation_detail", "soft", "Model registry", "models/README.md"),
    ("E044", "result", "soft", "Chronological results log (includes the CPU timing table of the Stage-1 switch)", "docs/results/RESULTS_LOG.md"),
    ("E045", "implementation_detail", "hard", "Web demo", "app.py"),
    ("E046", "observation", "hard", "Visual inspection record of the near-duplicate candidates", "outputs/review_round1/README.md"),
    ("E047", "experiment", "hard", "Single-corpus lesion detector on CariesXrays (COCO AP against FPCL)", "models/14_cariesxrays_lever2/run_summary.txt"),
    ("E048", "implementation_detail", "hard", "Crop generation: expanded boxes and the 0.15 box jitter", "src/crop_generator.py"),
    ("E049", "implementation_detail", "hard", "Overlap-ratio labels (not IoU) for the abnormality flag", "src/label_assigner.py"),
    ("E050", "observation", "hard", "Listing of the test modules under tests/", P + f"/evidence/runs/test_modules_{TODAY}.txt"),
    ("E051", "dataset", "hard", "The project's survey extract of OPG papers (Sheet3: 49 task-relevant)", "outputs/related_work_extract.csv"),
    # author-stated limitations (paper.md section VIII, transfer.md) and rationale
    ("E101", "limitation_noted", "hard", "DENTEX in-domain for the detector; Tufts guard missed; only Ningxia external to the lesion detector, informed adoption; random-effects interval includes zero", "paper/paper.md"),
    ("E102", "limitation_noted", "hard", "Theory treats codes independently, one corpus; shortcut test on 34 radiographs; no calibration curve for the lesion detector", "paper/paper.md"),
    ("E103", "limitation_noted", "hard", "Panoramic-only caries labels; expert lesions a subset of disease", "paper/paper.md"),
    ("E104", "limitation_noted", "hard", "Agreement has no negative class; no healthy controls; single runs; no clinician comparison; duplicate checks cannot find a patient's second radiograph", "paper/paper.md"),
    ("E105", "limitation_noted", "hard", "Stage-4 label is an abnormality mask, not bone loss; Stage 3b validated only in development", "transfer.md"),
    ("E111", "rationale_stated", "hard", "Tooth-centric design: dentists reason per tooth, so findings must map to numbered teeth", P + "/evidence/phase2_report_text.txt"),
    ("E112", "rationale_stated", "hard", "Caries task changed to lesion localisation after five failed repairs, under a rule committed before training", "transfer.md"),
]
tests = sorted(p.name for p in (ROOT / "tests").glob("test_*.py"))
(RCS / "evidence" / "runs").mkdir(parents=True, exist_ok=True)
(RCS / "evidence" / "runs" / f"test_modules_{TODAY}.txt").write_text(
    f"{len(tests)} test modules under tests/ (listed {TODAY})\n" + "\n".join(tests) + "\n", encoding="utf-8")
EV_VALUE = {  # structured values the truth guardrail reads (models/16 run summary, section (2))
    "E019": {"matched": True, "protocol": "frozen evaluation; paired cluster bootstrap (10,000 resamples, seed 42) "
                                          "on the same images per cohort", "comparators": ["constant-molars", "gate v3.0"]},
}
items = []
for eid, kind, strength, summary, loc in EV:
    assert (ROOT / loc).exists(), f"evidence locator missing: {loc}"
    items.append({"id": eid, "kind": kind, "summary": summary, "locator": {"path": loc},
                  "strength": strength, "status": "ok", **({"value": EV_VALUE[eid]} if eid in EV_VALUE else {})})
write("evidence/research_evidence.json", {"project_root": "../..", "generated_at": TODAY, "items": items})


# ---------------------------------------------------------------- claims (one per TeX tag)
def C(cid, statement, ctype, ev, conf="high", rationale=None, licenses=(), basis="project_file"):
    d = {"id": cid, "statement": statement, "claim_type": ctype, "evidence": list(ev), "confidence": conf,
         "author_confirmation": "pending", "basis": basis, "status": "VERIFIED",
         "licenses": [{"type": t, "evidence": list(e)} for t, e in licenses]}
    if rationale:
        d["rationale"] = rationale
        d["origin"] = "author_stated"
    return d


MATCHED_B = [("matched_evaluation", ["E019"])]   # Lever B: paired cluster bootstrap on the same images per cohort


CLAIMS = [
    C("C001", "The pipeline runs at 1.70 s per image on a laptop CPU with no GPU (1.45 s with the previous detector).", "measured", ["E044", "E028", "E027", "E001"], conf="moderate"),
    C("C002", "In Phase 3 one OPG produces one per-tooth JSON report (opg-report/1.6) through six stages, from a CLI, a Streamlit demo and a Docker image.", "observed", ["E040", "E039", "E045", "E016"]),
    C("C003", "The default configuration has 95.34 M learnable parameters; 81.21 M with the crop classifier; 72.99 M for the caries path.", "measured", ["E017", "E027", "E001"]),
    C("C010", "Rule (3) fitted on 78 images selects the eight first and second molars, F1 0.392 on the fit images and 0.320 on the 164 scored images.", "derived", ["E014", "E001", "E005"]),
    C("C011", "The constant has 286 true positives among 1,312 named codes against 477 carious teeth (recall 0.600); the oracle constant reaches 0.330.", "measured", ["E014", "E001"]),
    C("C012", "Refitted on 10,000 resamples, the rule returns the eight molars 27% of the time; refits score median F1 0.320, 95% within 0.279-0.330; F1 is flat from 6 to 9 codes.", "measured", ["E005"]),
    C("C013", "On 164 DENTEX images the lesion-detector pipeline scores P 0.439, R 0.574, F1 0.498; the crop classifier 0.362; the VLMs 0.246 and 0.149.", "measured", ["E002", "E012", "E001"]),
    C("C014", "Paired F1 differences against the constant: VLMs -7.32 and -17.04; crop classifier +4.27 [+1.58, +7.05]; lesion detector +17.80 [+13.48, +22.02].", "measured", ["E002", "E001"]),
    C("C015", "At matched volume the lesion detector leads by +22.35 [+17.42, +27.18] and the crop classifier by +5.50 [+2.84, +8.22]; the VLMs are level.", "measured", ["E005"]),
    C("C016", "Externally the crop classifier is level with the constant on Ningxia (+0.89 [-3.86, +5.57]) and below it on CariesXrays (-22.42).", "measured", ["E002", "E001"]),
    C("C017", "Five repairs of the crop classifier did not separate from zero.", "measured", ["E013", "E001"]),
    C("C018", "The crop classifier's healthy-tooth scores track the base rate (0.075 to 0.478) and its within-type AUC is 0.745 [0.660, 0.842].", "measured", ["E007", "E001"]),
    C("C019", "Shown a blank or a noise image, the VLMs return the population prior.", "observed", ["E027", "E001"], conf="moderate"),
    C("C020", "The lesion detector met the pre-registered rule on two of three cohorts (+12.2, +10.2, tie) and was adopted on 4 Sep 2026.", "measured", ["E019", "E027", "E001"], licenses=MATCHED_B),
    C("C021", "The adoption rule was committed before any arm was trained; Ningxia informed the adoption.", "observed", ["E019", "E001"], licenses=MATCHED_B),
    C("C022", "Under the current detector, on 337 Ningxia radiographs from four sites, the lesion detector leads the constant by +9.28 points (95% interval [+4.72, +13.73]) and by +15.38 on CariesXrays, and is level on DENTEX.", "measured", ["E002", "E001"]),
    C("C023", "The lesion detector flags fewer teeth (4.35 vs 7.15 per image on Ningxia) and its DENTEX molar flags are carious more often (46.3% vs 28.4%).", "measured", ["E002", "E001"]),
    C("C024", "Per site the lead holds at three of four sites; random effects give +9.61 [-0.54, +19.76], HKSJ [-5.02, +24.24], tau 9.27 [3.22, 33.09].", "measured", ["E003", "E004", "E002", "E001"]),
    C("C030", "Identity factors: DENTEX 99.6% detected, 93.2% numbered, 92.8% end to end; Tufts 63.5%; UFBA 44.5% and 77.2%.", "measured", ["E002", "E001"]),
    C("C031", "The shipped detector, the default since 11 Oct 2026, missed its Tufts guard (0.587 against 0.723) and was adopted by a dated decision.", "observed", ["E018", "E027", "E001"]),
    C("C032", "Training diagnostics: detector validation mAP@0.5 0.634; lesion detector 0.820; numbering 0.810; Stage-4a validation macro-F1 below 0.6.", "measured", ["E014", "E001"]),
    C("C033", "The single-corpus lesion detector reaches COCO AP 48.2 (AP50 84.5), level with FPCL (48.2, 84.1).", "measured", ["E047", "E001", "E027"], conf="moderate"),
    C("C034", "Numbering: 869 of 936 teeth end to end; 51 of 63 wrong codes name an adjacent tooth; 8.2% of second molars get a wrong code.", "measured", ["E011", "E001"]),
    C("C035", "Declining the least-confident quarter raises numbering accuracy 0.932 to 0.980 and the crop classifier's 0.797 to 0.940; shuffled confidences remove the gain.", "measured", ["E010", "E001"]),
    C("C036", "The crop classifier is overconfident (ECE 0.136); temperature scaling gives 0.152, isotonic regression 0.043.", "measured", ["E008", "E009", "E001"]),
    C("C040", "The Phase 2 bone-loss figure 0.9233 came from a crop-level split; held out the model finds 3.4-7.6% of labelled teeth; retrained by radiograph 27.5% at 95.9% specificity.", "measured", ["E023", "E024", "E027"]),
    C("C041", "The radiograph-split retrain passes both pre-registered eligibility conditions.", "measured", ["E023"]),
    C("C042", "The Stage-4 severity head (0.294) does not beat a tooth-position prior (0.334) and is withheld.", "measured", ["E027", "E001", "E025"]),
    C("C050", "Verification on 6 Nov 2026: 210 tests passed, 3 skipped; 215 of 215 numbers verified; 12 of 12 invariants hold.", "measured", ["E030", "E031", "E032"]),
    C("C060", "86 DENTEX images are excluded as exact copies of training images, leaving 164 scored; no near-duplicate copy was found.", "measured", ["E006", "E046", "E001", "E032"]),
    C("C070", "The system is tooth-centric because dentists reason tooth by tooth and findings must map to numbered teeth.", "interpretation", ["E111"], rationale="motivation"),
    C("C071", "The caries task was changed to lesion localisation after five repairs failed, under a rule committed before training.", "interpretation", ["E112"], rationale="design_choice"),
    C("C025", "Under lesion agreement on DENTEX the crop classifier leads the constant by +17.12 [+12.15, +21.89], flagging 1,439 teeth against 988 at a lower match rate (0.267 against 0.306); the lesion detector flags 603 teeth at match rate 0.473 and is level with the constant (-3.55 [-10.11, +2.64]).", "measured", ["E002", "E001"]),
    # Phase 2 content carried into the report
    C("C080", "After the three-source join the Phase 2 Tufts pool is 423 OPGs, from which 22,806 tooth crops were built, about 96% normal and 4% abnormal (23.84 to 1).", "measured", ["E033", "E024"]),
    C("C081", "On 296 crops the Phase 2 CEJ heuristic was judged reliable on 62.5%; its severity agreed exactly with the overlap labels on 15.1% and within one class on 61.6%.", "measured", ["E026", "E033"]),
    C("C082", "Phase 2 crops: boxes expanded 1.5 times in width and 2.0 in height, a crop positive when mask pixels exceed 0.01 of it (an overlap ratio, not IoU), box jitter of 15% during crop generation, CLAHE for the CEJ branch.", "observed", ["E048", "E049", "E041", "E033"]),
    C("C083", "Mosaic augmentation and vertical flips are disabled for both detectors.", "observed", ["E018", "E019", "E047"]),
    C("C084", "Phase 2 caries cascade: a ResNet18 on 224 by 224 tight crops with ImageNet normalisation for caries against none, then the backbone fine-tuned for caries against deep caries; Phase 3 retrained the first stage with 5,366 healthy teeth as negatives.", "observed", ["E022", "E021", "E033"]),
    C("C085", "The Phase 2 binary model was a ResNet18 with focal loss, Adam, learning-rate reduction on plateau and early stopping (best epoch 22); the severity model a three-class ResNet18 with focal loss.", "observed", ["E024", "E025", "E033"]),
    C("C086", "The CEJ heuristic used CLAHE, column-wise CEJ and apex detection, a bone-crest search window, interquartile-range outlier removal and a confidence score.", "observed", ["E026", "E033"]),
    # method, design and interpretation statements
    C("C090", "A tooth-level caries score should be reported with an image-blind constant fitted off the test set, the identity factors, per-site external results with paired intervals, and images of what the system does.", "interpretation", ["E005", "E002", "E001"]),
    C("C091", "Design constants: detector input 1,024 px, confidence 0.25, NMS IoU 0.50; crops 1.0 (caries), 1.5 by 1.5 (numbering), 1.5 by 2.0 (abnormality flag); stable report field names.", "observed", ["E040", "E041", "E042"]),
    C("C092", "The Phase 2 target pipeline (YOLO detection, FDI sorting, a per-tooth loop with tight and expanded crops, a positive-only filter, a report) was built with four deliberate changes.", "observed", ["E033", "E040"]),
    C("C093", "A whole-image lesion detector can express a positional prior only through boxes over teeth without lesions, each costing precision under FDI-set F1; a lead that comes from reading the image should come with fewer flags and more carious flags per tooth type.", "derived", ["E001"]),
    C("C094", "FDI-set F1 is micro-averaged over teeth; lesion agreement matches lesions to flagged teeth by greedy IoU of at least 0.30 with a centroid fallback on DENTEX and by centroid containment externally (median lesion 731 px, tooth boxes about 25,000 px).", "observed", ["E001", "E002"]),
    C("C095", "Intervals are 95% percentile cluster bootstraps over images: 10,000 resamples with seed 42 by default; 2,000 for the calibration AP, 5,000 for the within-type AUC and 1,000 with seed 0 for the abstention gains; differences in percentage points.", "observed", ["E001", "E008", "E010", "E007"]),
    C("C096", "The test suite has 23 modules under tests/.", "observed", ["E050", "E030"]),
    C("C097", "Of the 49 task-relevant papers in the project's survey of OPG analysis, none was noticed to report an image-blind baseline (an observation, not a systematic count).", "observed", ["E051", "E029"]),
    C("C098", "Eight future-work items are proposed, among them an external per-type precision comparison, a real periodontal measurement and numbering along the arch.", "future", ["E027"], conf="moderate"),
]
LIMS = [
    {"id": "L001", "statement": "DENTEX is in-domain for the detector; only Ningxia is external to the lesion detector and it informed the adoption.", "affects_claims": ["C022", "C024", "C020"], "origin": "author_stated", "evidence": ["E101"]},
    {"id": "L002", "statement": "The theory treats codes independently and was checked on one corpus; the shortcut test rests on 34 radiographs.", "affects_claims": ["C010", "C018"], "origin": "author_stated", "evidence": ["E102"]},
    {"id": "L003", "statement": "DENTEX caries labels come from panoramic radiographs alone.", "affects_claims": ["C013", "C010"], "origin": "author_stated", "evidence": ["E103"]},
    {"id": "L004", "statement": "No negative class or healthy controls; single runs; no clinician comparison; duplicate checks cannot find a second radiograph of a patient.", "affects_claims": ["C013", "C022", "C060"], "origin": "author_stated", "evidence": ["E104"]},
    {"id": "L005", "statement": "The Stage-4 label is not periodontal bone loss; Stage 3b was validated only on development crops.", "affects_claims": ["C040"], "origin": "author_stated", "evidence": ["E105"]},
]
NEGATIVE = [
    {"evidence": "E013", "decision": "reported_main", "reason": "the five failed repairs motivate the change of task (Section 10.6)"},
    {"evidence": "E006", "decision": "reported_main", "reason": "the absence of near-duplicates is a control on the DENTEX numbers (Section 10.11)"},
    {"evidence": "E026", "decision": "reported_main", "reason": "the CEJ heuristic stays a documented negative result (Sections 7.5 and 10.1)"}]


# ---------------------------------------------------------------- source registry (verified bibliography)
def ascii_surname(name):
    n = re.sub(r"\\[a-zA-Z]+\s*|\\.", "", name).replace("{", "").replace("}", "").strip()
    n = n.split(",")[0] if "," in n else (n.split()[-1] if n.split() else n)
    return "".join(c for c in unicodedata.normalize("NFKD", n) if not unicodedata.combining(c))


def bib_authors():
    bib = (HERE / "build" / "references.bib").read_text(encoding="utf-8", errors="replace")
    out = {}
    for m in re.finditer(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)(?=\n@|\Z)", bib, re.S):
        am = re.search(r"\bauthor\s*=\s*\{(.*?)\}\s*,?\s*\n\s*\w+\s*=", m.group(2), re.S | re.I)
        if am:
            out[m.group(1)] = [ascii_surname(a) for a in re.split(r"\s+and\s+", " ".join(am.group(1).split()))]
    return out


AUTH = bib_authors()
_oa = RCS / "corpus" / "openalex_meta.json"                     # tools/fetch_meta.py
OA_META = json.loads(_oa.read_text(encoding="utf-8")) if _oa.exists() else {}
cited = set()
for f in (HERE / "chapters").glob("*.tex"):
    for grp in re.findall(r"\\cite\{([^}]+)\}", f.read_text(encoding="utf-8")):
        cited |= {k.strip() for k in grp.split(",")}
for f in (HERE / "appendices").glob("*.tex"):
    for grp in re.findall(r"\\cite\{([^}]+)\}", f.read_text(encoding="utf-8")):
        cited |= {k.strip() for k in grp.split(",")}

IDX = {"crossref": "crossref", "openalex": "openalex", "semantic_scholar": "semantic_scholar", "arxiv": "arxiv"}
SOFTWARE = {"jocher2024yolo11", "paszke2019pytorch"}
entries = {}
for f in [ROOT / "outputs/citation_audit/2026-11-02_ars/sourcebib_refs.json",
          ROOT / "outputs/citation_audit/2026-11-02_ars/final_refs.json"]:
    for e in json.loads(f.read_text(encoding="utf-8")):
        if e.get("key") and not e["key"].startswith("IEEEexample"):
            entries[e["key"]] = e
EXTRA = {  # verified by DOI lookup when added (2 Nov and 6 Nov 2026); not in the 2 Nov audit files
    "batchelor2004grouping": ("Grouping of tooth surfaces by susceptibility to caries: A study in 5-16 year-old children", 2004, "BMC Oral Health", "10.1186/1472-6831-4-2", "2026-11-02"),
    "akarslan2008comparison": ("A comparison of the diagnostic accuracy of bitewing, periapical, unfiltered and filtered digital panoramic images for approximal caries detection in posterior teeth", 2008, "Dentomaxillofacial Radiology", "10.1259/dmfr/84698143", "2026-11-02"),
    "inthout2014hartung": ("The Hartung-Knapp-Sidik-Jonkman method for random effects meta-analysis is straightforward and considerably outperforms the standard DerSimonian-Laird method", 2014, "BMC Medical Research Methodology", "10.1186/1471-2288-14-25", "2026-11-02"),
    "viechtbauer2007confidence": ("Confidence intervals for the amount of heterogeneity in meta-analysis", 2007, "Statistics in Medicine", "10.1002/sim.2514", "2026-11-02"),
    "albano2024artificial": ("Artificial intelligence for radiographic imaging detection of caries lesions: a systematic review", 2024, "BMC Oral Health", "10.1186/s12903-024-04046-7", TODAY),
    "iacob2025automated": ("Automated Detection of Periodontal Bone Loss in Two-Dimensional (2D) Radiographs Using Artificial Intelligence: A Systematic Review", 2025, "Dentistry Journal", "10.3390/dj13090413", TODAY),
}
sources = []
for key in sorted((set(entries) | set(EXTRA)) & cited):      # the report's own bibliography: what BibTeX prints
    if key in EXTRA and key not in entries:
        title, year, venue, doi, vdate = EXTRA[key]
        first = AUTH.get(key, [re.match(r"[a-z]+", key).group(0)])[0]
        ver = {"method": "doi_lookup", "date": vdate, "verified_by": "agent", "lookup_verified": True,
               "indexes": [{"index": "crossref", "status": "found"}]}
        rec = {"title": title, "year": year, "venue": venue, "doi": doi, "status": "PEER-REVIEWED", "ver": ver,
               "retraction": None, "first": first}
    else:
        e = entries[key]
        meta = e.get("crossref_meta") or {}
        lv = str(e.get("lookup_verified")).lower()
        idx = []
        for name, r in (e.get("resolvers") or {}).items():
            if name in IDX:
                oc = (r or {}).get("outcome", "")
                idx.append({"index": IDX[name], "status": "found" if oc == "matched" else "skipped" if oc in ("unreachable", "skipped", "") else "not_found"})
        ver = {"method": "doi_lookup" if e.get("doi") else "index_lookup", "date": "2026-11-02", "verified_by": "agent",
               "lookup_verified": True if lv == "true" else False if lv == "false" else "unresolvable", "indexes": idx}
        status = "PEER-REVIEWED" if e.get("doi") and not str(e.get("doi")).startswith("10.48550") else \
            "DOCUMENTATION" if key in SOFTWARE else "PREPRINT"
        rt = e.get("retraction") or {}
        kinds = {str(n.get("type", "")).lower() for n in rt.get("notices") or []}
        retraction = {"status": "retracted" if "retraction" in kinds else
                      "not_retracted" if rt.get("status") == "checked" else "unknown", "checked_at": "2026-11-02"}
        if kinds - {"retraction"}:                    # corrections and other updates are recorded, not retractions
            retraction["observations"] = [{"source": "crossref", "retracted": False, "notice": n.get("type"),
                                           "notice_doi": n.get("notice_doi")} for n in rt["notices"]]
        rec = {"title": meta.get("title") or e.get("title"), "year": meta.get("year") or e.get("year"),
               "venue": meta.get("venue") or e.get("venue"), "doi": e.get("doi"), "status": status, "ver": ver,
               "retraction": retraction, "first": e.get("first_author") or ""}
    authors = AUTH.get(key) or [rec["first"]]
    om = OA_META.get(key) or {}
    if authors[-1].lower() == "others" and len(om.get("authors") or []) >= 2:
        authors = authors[:1] + om["authors"][1:]                   # the bibliography truncates; OpenAlex lists all
    if om.get("is_retracted") and rec["retraction"] is not None:
        rec["retraction"]["status"] = "retracted"
    first = rec["first"] or authors[0]
    first = " ".join(w if w in ("de", "van", "von", "der", "den", "da", "di", "del", "la", "le") else
                     "-".join(p[:1].upper() + p[1:] for p in w.split("-")) for w in first.split())
    authors = [first] + authors[1:]                                 # registry first author = audit's surname
    s = {"id": f"SRC-{len(sources) + 1:03d}", "key": key, "title": rec["title"], "authors": authors,
         "year": int(rec["year"]) if rec["year"] else None, "venue": rec["venue"],
         "publication_status": rec["status"], "level": 2, "verification": rec["ver"],
         "read_depth": "abstract", "permitted_use": ["content_citation"], "cited_in_report": key in cited}
    if rec["doi"] and re.match(r"^10\.[0-9]{4,9}/\S+$", rec["doi"]):
        s["doi"] = rec["doi"]
    if rec["retraction"]:
        s["retraction"] = rec["retraction"]
    if not s["year"]:
        del s["year"]
    sources.append(s)
missing = sorted(cited - {s["key"] for s in sources})
assert not missing, f"cited keys missing from the registry: {missing}"
write("corpus/source_registry.json", {"sources": sources})

# ---------------------------------------------------------------- literature claims (Chapter 3)
# Each claim's sources are the \cite keys in the TeX it tags: the whole subsection for a tag placed under
# \litmeta, the paragraph for a tag at a paragraph's end. Numbers were checked against the abstracts
# (tools/check_p2_survey.py for the Phase 2 entries; the 2 Nov citation audit for the thematic review).
SRC = {s["key"]: s["id"] for s in sources}
LIT = {
    "C101": "Ayhan et al. (2025) detect caries under fixed dental prostheses on panoramic radiographs in two stages, reporting recall 0.827, precision 0.834, mAP 0.846 and F1 0.830.",
    "C102": "Khuwaja et al. (2024) detect caries in intraoral images with deep learning.",
    "C103": "Jundaeng et al. (2025) segment teeth, the CEJ and the bone level on 2,000 panoramic radiographs with YOLOv8, reporting 97% accuracy (F1 0.80) for teeth and 98% (F1 0.90) for CEJ and bone level.",
    "C104": "Alharbi et al. (2023) segment cavities in panoramic radiographs with nested U-Net models; U-Net3+ reaches 95% testing accuracy.",
    "C105": "Chen et al. (2023) recognise periodontitis and caries in dental X-rays; for periodontitis the area under the ROC curve is 98.67% and under the precision-recall curve 98.38%.",
    "C106": "Nassiri and Akhloufi (2025) analyse panoramic dental X-rays with YOLO-based models.",
    "C107": "Asci et al. (2024) segment caries in paediatric radiographs over three dentition stages; in the total group sensitivity 0.8269, precision 0.9123, F1 0.8675.",
    "C108": "Chen et al. (2024) release CariesXrays, 6,000 panoramic radiographs with lesion boxes, with a feature-pyramid contrastive method.",
    "C109": "Perez de Frutos et al. (2024) detect proximal caries on bitewings from a population study, comparing with clinicians; YOLOv5 reports 0.647 mean average precision and 0.548 mean F1.",
    "C110": "Albano et al. (2024) review AI caries detection on radiographs: sensitivity 0.44 to 0.86, specificity 0.85 to 0.98, accuracy 0.73 to 0.98, AUC 0.84 to 0.98.",
    "C111": "Kaushik and Sharma (2025) classify dental radiographs with DenseNet201: accuracy 91%, F1 0.95 for normal images and 0.91 for implants.",
    "C112": "Iacob et al. (2025) systematically review AI detection of periodontal bone loss on 2D radiographs.",
    "C113": "Chmielewski et al. (2025) review diagnostic accuracy and examiner agreement under the 2018 periodontitis classification.",
    "C114": "Gamal et al. (2025) diagnose dental conditions in panoramic X-rays with an ensemble, reporting more than 92% classification accuracy.",
    "C115": "Sastika and Marappan (2025) review AI for early caries detection: accuracies 85 to 99%, precisions 86 to 96%, F1 87 to 94%.",
    "C120": "Public datasets: Tufts (tooth and abnormality annotations), DENTEX (quadrant, enumeration and diagnosis labels), CariesXrays (6,000 OPGs with lesion boxes), a multi-centre Ningxia and Shenzhen set, UFBA-425 (425 radiographs); combining datasets is itself studied.",
    "C121": "Reported caries accuracies on panoramic radiographs span 86.1 to 96.1% in studies judged of low quality; numbering is reported at class-averaged accuracy 0.9988 (F1 0.979); one study checked panoramic caries labels against bitewings on 14,997 teeth.",
    "C122": "Published bone-loss methods combine detection with keypoints, super-resolution or segmentation; one YOLOv8 model was trained on 1,628 panoramic radiographs and validated externally on 180.",
    "C123": "Few imaging-AI studies validate externally (31 of 516, 6%); dental models degrade at new centres (apical lesions F1 54.1% to 32.7%; a YOLOv11 detector of 13 conditions mAP@0.5 0.857 to 0.806); one detector held sensitivity 0.70 internally and 0.67 externally.",
    "C124": "Models exploit cues correlated with labels, which input-withholding baselines expose; COVID-19 detectors relied on confounders, and sorting pneumonia radiographs by hospital alone reached AUC 0.861.",
    "C125": "Temperature scaling, isotonic regression and selective classification are the calibration and abstention methods compared; VLMs are being adapted to dental diagnosis, and Qwen2.5-VL is a general comparator.",
}


def tagged_cites(cid):
    """\\cite keys in the TeX a tag covers."""
    t = (HERE / "chapters" / "ch03_literature.tex").read_text(encoding="utf-8").replace("\r\n", "\n")
    i = t.index("{" + cid + "}")
    line_start = t.rfind("\n", 0, i) + 1
    if t[line_start:i].strip() == "%":                        # tag-only line under \litmeta: its subsection
        a = t.rfind("\\subsection", 0, i)
        b = min([x for x in (t.find("\\subsection", i), t.find("\\section", i)) if x > 0] or [len(t)])
    else:                                                     # tag at a paragraph's end: that paragraph
        a = t.rfind("\n\n", 0, i) + 2
        b = i
    keys = []
    for grp in re.findall(r"\\cite\{([^}]+)\}", t[a:b]):
        keys += [k.strip() for k in grp.split(",") if k.strip() not in keys]
    return keys


for cid, statement in LIT.items():
    keys = tagged_cites(cid)
    assert keys and all(k in SRC for k in keys), f"{cid}: cites {keys}"
    c = C(cid, statement, "literature", ["E037" if int(cid[1:]) >= 120 else "E034"] +
          (["E035"] if cid == "C110" else ["E036"] if cid == "C112" else []), basis="literature")
    c["sources"] = [SRC[k] for k in keys]
    CLAIMS.append(c)

write("claims/claim_evidence_map.json", {"claims": CLAIMS, "limitations": LIMS, "negative_result_decisions": NEGATIVE})

# ---------------------------------------------------------------- config and state
write("plan/paper_config.json", {
    "mode": "restructure",
    "deliverable": "capstone project report (UE23CS441A, Phase 3), LaTeX to PDF",
    "audience": "B: adjacent researchers (examiners and the project guide in computer science)",
    "venue": "PES University Phase 3 report guidelines (Report- Guidelines.pdf) and initial-page templates",
    "citation_style": "IEEE, numbered in order of first citation",
    "language": "en",
    "length_limits": None,
    "prior_drafts": ["Phase 2 report PW26_MHR_06 (Level-0 communication artifact)", "paper/paper.md"],
    "confirmed_by": "C S Deepak, chat instructions of 6 Nov 2026 (scope, template, 60-70% Phase 2 carry-over, all images kept)",
})
state_f = RCS / "state.json"
state = json.loads(state_f.read_text(encoding="utf-8")) if state_f.exists() else {}
state.update({"step": 19, "guardrail": "v0.3", "length_limit_words": None})
state["gates"] = {k: v for k, v in (state.get("gates") or {}).items() if k != "C0"}
state.setdefault("accepted_risks", [])
state_f.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")
print(f"evidence {len(items)} | claims {len(CLAIMS)} | limitations {len(LIMS)} | sources {len(sources)} "
      f"({sum(s['cited_in_report'] for s in sources)} cited in the report)")
