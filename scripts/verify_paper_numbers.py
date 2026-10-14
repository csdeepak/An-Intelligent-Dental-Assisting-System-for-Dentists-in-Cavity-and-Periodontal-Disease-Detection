# -*- coding: utf-8 -*-
"""Assert every headline number in paper/main.tex against its saved artefact.

WHY THIS EXISTS
---------------
`audit_citations.py` checks that each citation supports its claim. Nothing checked
that each *number* still matches the evaluation output it came from. Two of the
defects found in the 28 Aug manuscript rebuild were exactly that failure mode: a
parameter count that had drifted from the detector-only figure to a whole-system
claim, and a calibration sentence that contradicted the JSON sitting next to it.

WHAT IT DOES
------------
Reads the artefacts, formats each value the way the manuscript writes it, and
asserts the string is present in main.tex. It is deliberately literal: it will fail
if a number is re-rounded, which is the point -- a silent re-rounding is how a table
and its source drift apart.

It cannot check prose. A number can be present and attached to the wrong claim; that
is what the citation audit and human review are for.

Run: py -3.13 scripts/verify_paper_numbers.py
"""
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEX = (REPO / "paper" / "main.tex").read_text(encoding="utf-8")

# Collapse LaTeX thin-space and thousands markup so "1{,}013" and "70.1\,GB" match.
# The thin space before a percent sign is typographic, not semantic, so "58.3\,\%"
# and "58.3%" are the same claim and must compare equal.
FLAT = TEX.replace("{,}", ",").replace("\\,", " ").replace("\\%", "%")
FLAT = re.sub(r"\s+", " ", FLAT).replace(" %", "%")


def r(value, places):
    """Round half-up, the way a person writing a table rounds.

    Python's float formatting rounds 70.05 to 70.0 because the binary double is a
    hair below 70.05. A manuscript writes 70.1. Comparing against the float
    formatting would flag a correct number as drift.
    """
    q = Decimal(1).scaleb(-places)
    return f"{Decimal(repr(value)).quantize(q, rounding=ROUND_HALF_UP):.{places}f}"

ok, bad = [], []


def load(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def pct2(e):
    """A [lo, hi] interval from fractions, as the manuscript prints it: two decimals, in %."""
    return f"[{r(e['ci95'][0] * 100, 2)}, {r(e['ci95'][1] * 100, 2)}]"


def check(label, needle, source):
    """Assert `needle` appears in the flattened manuscript."""
    if needle in FLAT:
        ok.append(f"  OK   {label:52s} {needle!r}")
    else:
        bad.append(f"  FAIL {label:52s} {needle!r}\n       source: {source}")


# ====================================================================================
# REBUILT 11 Oct 2026 with the manuscript, on the current Stage-1 detector (arm3c).
# Every pipeline number is asserted against outputs/stage1_switch/ -- one front end,
# one machine (RESULTS_LOG 2026-10-11g to -j). What does not depend on the tooth
# detector is asserted against the artefact it always came from: the constant and the
# VLMs (outputs/c1_vlm/), the caries gate's calibration and coverage on held-out crops,
# and Lever B's adoption evidence, which the manuscript quotes as the previous front
# end's and which must stay exactly as it was scored.
# ====================================================================================
SW = "outputs/stage1_switch/"
RES = load(SW + "stage1_switch_results.json")
NEW = "arm3c"


def sgn(x, places=2):
    """A stored difference the way the manuscript prints it: sign always shown."""
    return f"{x:+.{places}f}"


def ci(d):
    lo, hi = d["ci95_pp"]
    return f"[{sgn(lo)}, {sgn(hi)}]"


def flip(d):
    """The same paired difference with the arms swapped."""
    lo, hi = d["ci95_pp"]
    return {"delta_pp": -d["delta_pp"], "ci95_pp": [-hi, -lo]}


# ---------------------------------------------------------------- the ladder (Table IV)
# `row`, not `r` -- `r` is the rounding helper above, and shadowing it here would be
# invisible (comprehension scope keeps it working) right up until someone edits this line.
comp = {row["arm"]: row for row in load("outputs/c1_vlm/c1_comparison.json")["results"]}
const_file = load("outputs/c1_vlm/c1_constant_arm_vlm_32b_0shot.json")
held = next(b for b in const_file["constant_baselines"]
            if b["baseline"].startswith("held-out"))
oracle = next(b for b in const_file["constant_baselines"]
              if b["baseline"].startswith("ORACLE"))
S = "outputs/c1_vlm/"

for name, row in (("constant", held), ("vlm-32b", comp["vlm_32b_0shot"]),
                  ("vlm-7b", comp["vlm_7b_0shot_rerun"]), ("oracle", oracle)):
    for metric in ("precision", "recall", "f1"):
        check(f"Table IV {name} {metric}", f"{row[metric]:.3f}", S)

# The two pipeline rows: from the counts, never from the stored 4-dp fields.
F1 = RES["D_fdi_set_f1"]
for method in ("gate", "lesion-detector"):
    a = F1[method][NEW]
    tp, fp, fn = a["tp"], a["fp"], a["fn"]
    assert tp + fn == held["tp"] + held["fn"], f"{method}: not scored on the same ground truth"
    check(f"Table IV pipeline ({method}) precision", r(tp / (tp + fp), 3), SW + "D_fdiset")
    check(f"Table IV pipeline ({method}) recall", r(tp / (tp + fn), 3), SW + "D_fdiset")
    check(f"Table IV pipeline ({method}) F1", r(2 * tp / (2 * tp + fp + fn), 3), SW + "D_fdiset")
    d = F1[method]["deltas"]["arm3c_minus_constant"]
    check(f"pipeline ({method}) - constant, F1", sgn(d["delta_pp"]), SW + "results")
    check(f"pipeline ({method}) - constant, F1 CI", ci(d), SW + "results")
    assert d["excludes_zero"] and d["delta_pp"] > 0, \
        f"{method}: the manuscript says the pipeline is above the constant on DENTEX F1"
g = F1["gate"][NEW]
check("teeth named by the gate pipeline", f"{g['tp'] + g['fp']:,}", SW + "D_fdiset")
check("teeth named by the constant", f"{held['tp'] + held['fp']:,}", S)
ld = F1["lesion-detector"][NEW]
assert 2 * (ld["tp"] + ld["fp"]) < held["tp"] + held["fp"], "prose: 'fewer than half as many teeth'"

# The constant against the two VLMs: outputs/caries_intervals (RESULTS_LOG 2026-10-11).
m1 = load("outputs/caries_intervals/caries_intervals.json")["m1_f1_gap"]["deltas"]
for name in ("vlm_32b", "vlm_7b"):
    d = m1[f"constant_minus_{name}"]
    check(f"constant - {name}, F1", sgn(d["delta_pp"]), "caries_intervals")
    check(f"constant - {name}, F1 CI", ci(d), "caries_intervals")
    assert d["excludes_zero"], f"prose says the constant outscored {name}"

# 477 annotated carious teeth = tp + fn for any arm scored on the same GT
check("477 affected teeth", f"{held['tp'] + held['fn']}", S + " held-out tp+fn")
check("164 scored images", f"{const_file['n_images']}", S)

# The fitted constant's membership, as the text states it
check("constant set is the eight first/second molars",
      "first and second molars of all four", "held-out baseline label")
for code in ("16", "17", "26", "27", "36", "37", "46", "47"):
    if code not in held["baseline"]:
        bad.append(f"  FAIL constant set missing {code} in {held['baseline']}")

# --------------------------------------------------- lesion localisation (Table V)
# The *_agreement fields in these artefacts are stored to 4 dp. Formatting a stored
# 4-dp value to 3 dp rounds a rounded number, and the binary double breaks the tie
# downward. Round once, from the integer counts, using r().
flagged = {}
for tag, name in (("constant-molars", "constant"), ("pipeline", "gate pipeline"),
                  ("lesion-detector", "lesion-detector pipeline"), ("all-teeth", "ceiling")):
    j = load(f"{SW}C_dentex_{tag}_{NEW}/lesion_localization.json")
    assert j["n_images"] == 164 and j["n_lesions"] == 479, f"{tag}: not the 164-image cohort"
    flagged[tag] = j["n_predicted_positive_teeth"]
    check(f"Table V {name} agreement", r(j["n_lesions_matched"] / j["n_lesions"], 3), tag)
    check(f"Table V {name} teeth flagged", f"{flagged[tag]:,}", tag)
    check(f"Table V {name} match rate",
          r(j["n_predicted_positive_matched_to_a_lesion"] / flagged[tag], 3), tag)
check("479 annotated lesions", "479", SW + "C_dentex")
DX = RES["C_dentex_lesion_agreement"]["pooled"]["deltas"]
d = DX[f"{NEW}: pipeline_minus_constant-molars"]
check("DENTEX gate - constant", f"{d['delta_pp']:.2f} percentage", SW + "results")
check("DENTEX gate - constant CI", ci(d), SW + "results")
d = DX[f"{NEW}: lesion-detector_minus_constant-molars"]
check("DENTEX lesion detector - constant", sgn(d["delta_pp"]), SW + "results")
check("DENTEX lesion detector - constant CI", ci(d), SW + "results")
assert not d["excludes_zero"], "prose reports DENTEX as a tie for the lesion detector"
d = DX[f"{NEW}: lesion-detector_minus_pipeline"]
check("DENTEX lesion detector - gate", sgn(d["delta_pp"]), SW + "results")
check("DENTEX lesion detector - gate CI", ci(d), SW + "results")
check("gate flags more teeth than the constant by",
      f"{(flagged['pipeline'] / flagged['constant-molars'] - 1) * 100:.0f}%", "recomputed")


# ------------------------------------------------------------- external (Table VI)
def ext(d):
    return load(f"{SW}{d}/ningxia_external.json")["by_category_split"]


ep, ec = ext(f"F_ningxia_caries_pipeline_{NEW}"), ext(f"F_ningxia_caries_constant-molars_{NEW}")
sites = sorted(ep)
swing = []
for s in sites:
    tag = s.split("/")[-1]
    p_, c_ = ep[s]["lesions_covered"] / ep[s]["lesions"], ec[s]["lesions_covered"] / ec[s]["lesions"]
    check(f"Table VI {tag} pipeline", r(p_, 3), "F_ningxia_caries_pipeline")
    check(f"Table VI {tag} constant", r(c_, 3), "F_ningxia_caries_constant-molars")
    check(f"Table VI {tag} lesions", f"{ep[s]['lesions']:,}", "F_ningxia_caries_pipeline")
    check(f"Table VI {tag} delta", "$" + ("+" if c_ >= p_ else "-") + r(abs(c_ - p_) * 100, 1) + "$",
          "recomputed from counts")
    swing.append((c_ - p_) * 100)
check("per-site swing", f"{max(swing) - min(swing):.0f}-point range", "recomputed")
tot = sum(ep[s]["lesions"] for s in sites)
check("external total lesions", f"{tot:,}", "sum over four sites")
check("external total images", f"{sum(ep[s]['images'] for s in sites)}", "sum")
check("pooled pipeline", r(sum(ep[s]["lesions_covered"] for s in sites) / tot, 3), "recomputed")
check("pooled constant", r(sum(ec[s]["lesions_covered"] for s in sites) / tot, 3), "recomputed")
NX = RES["F_ningxia_caries_lesion_agreement"]
d = flip(NX["pooled"]["deltas"][f"{NEW}: pipeline_minus_constant-molars"])
check("pooled constant - pipeline", "$" + sgn(d["delta_pp"]) + "$", SW + "results")
check("pooled constant - pipeline CI", ci(d), SW + "results")
assert d["ci95_pp"][0] < 0 < d["ci95_pp"][1], "prose says the two are indistinguishable pooled"

# ------------------------------------------------------------------- stage 2
s2 = load(f"{SW}B_dentex_{NEW}/stage2_summary_head.json")
tax = load(f"{SW}I_taxonomy_{NEW}/stage2_failure_taxonomy.json")
check("Stage-2 end-to-end", r(s2["fdi_exact_of_all"]*100, 1) + "%", "B_dentex")
check("Stage-2 of detected", r(s2["fdi_exact_of_detected"]*100, 1) + "%", "B_dentex")
check("never detected", r((1-s2["recall"])*100, 1) + "%", "B_dentex")
check("detection recall", r(s2["recall"]*100, 1) + "%", "B_dentex")
check("correct teeth", f"{tax['categories']['correct']}", "taxonomy")
check("GT teeth", f"{s2['n_gt_teeth']}", "B_dentex")
check("detected teeth", f"{tax['n_detected']}", "taxonomy")
check("wrong codes", f"of {tax['n_wrong_code']} incorrect codes", "taxonomy")
check("off-by-one", f"{tax['categories']['off_by_one']}", "taxonomy")
check("off-by-one share", r(tax["categories"]["off_by_one"] / tax["n_wrong_code"] * 100, 1) + "%",
      "taxonomy")
quad_err = (tax["categories"].get("wrong_arch", 0) + tax["categories"].get("mirror_lr", 0)
            + tax["categories"].get("other", 0))
check("quadrant-level errors", f"only {quad_err} of {tax['n_detected']}", "taxonomy")
B = RES["B_dentex_numbering"][NEW]["end_to_end"]["ci95"]
check("Stage-2 end-to-end CI", f"[{r(B[0]*100, 1)}, {r(B[1]*100, 1)}]", SW + "results")
t2 = load(f"{SW}A_tufts_{NEW}/stage2_summary_head.json")
check("Tufts end-to-end", r(t2["fdi_exact_of_all"]*100, 1) + "%", "A_tufts")
check("Tufts detection recall", r(t2["recall"]*100, 1) + "%", "A_tufts")
check("Tufts of detected", r(t2["fdi_exact_of_detected"]*100, 1) + "%", "A_tufts")
check("Tufts GT teeth", f"{t2['n_gt_teeth']:,}", "A_tufts")
A = RES["A_tufts_numbering"][NEW]["end_to_end"]["ci95"]
check("Tufts end-to-end CI", f"[{r(A[0]*100, 1)}, {r(A[1]*100, 1)}]", SW + "results")

# --------------------------------------------------------------- calibration
cal = load("outputs/calibration/caries_gate_calibration_test.json")
iso = load("outputs/calibration/caries_gate_isotonic.json")
tmp = load("outputs/calibration/caries_gate_temperature.json")
check("ECE raw", f"{cal['ece']:.3f}", "calibration_test")
check("ECE after temperature", f"{tmp['test']['ece'][1]:.3f}", "temperature")
check("ECE after isotonic", f"{iso['test']['ece'][1]:.3f}", "isotonic")
check("verdicts flipped by isotonic", f"{iso['verdicts_flipped_at_0.5']}", "isotonic")
check("AP before isotonic", f"{iso['test']['average_precision'][0]:.3f}", "isotonic")
check("AP after isotonic", f"{iso['test']['average_precision'][1]:.3f}", "isotonic")
check("caries-gate test n", f"{cal['n']}", "calibration_test")
check("caries prevalence", f"{cal['prevalence']:.3f}", "calibration_test")

# --------------------------------------------------------- selective prediction
# Numbering: the current detector's rows. Caries gate: held-out crops, no detector involved.
c4n = load(f"{SW}J_coverage_{NEW}/c4_coverage_accuracy.json")["stage2"]
c4 = load("outputs/c4_abstention/c4_coverage_accuracy.json")
check("numbering full coverage", f"{c4n['accuracy_full_coverage']:.3f}", "J_coverage")
check("numbering at 75%", f"{c4n['at_75']['accuracy']:.3f}", "J_coverage")
check("numbering gain", f"{c4n['gain_at_75']['gain_pp']:.2f}", "J_coverage")
check("numbering gain CI", "[" + ", ".join(sgn(v) for v in c4n["gain_at_75"]["ci95_pp"]) + "]",
      "J_coverage")
check("numbering gain clusters", f"{c4n['gain_at_75']['n_images']} image clusters", "J_coverage")
check("numbering shuffled control", sgn(c4n["gain_at_75"]["shuffled_control_gain_pp"]), "J_coverage")
check("gate full coverage",
      f"{c4['caries_gate']['accuracy_full_coverage']:.3f}", "c4")
check("gate at 75%", f"{c4['caries_gate']['at_75']['accuracy']:.3f}", "c4")
check("gate gain", f"{c4['caries_gate']['gain_at_75']['gain_pp']:.2f}", "c4")
check("pre-registered coverage",
      r(c4n["operating_point"]["coverage"]*100, 1) + "%", "J_coverage")
check("pre-registered accuracy", f"{c4n['operating_point']['accuracy']:.3f}", "J_coverage")
check("90%-coverage accuracy", f"{c4n['at_90']['accuracy']:.3f}", "J_coverage")
check("75% of detections, over teeth present",
      r(0.75 * s2["recall"] * 100, 1) + "% of the teeth", "recomputed")

# ------------------------------------------------------------- VLM + hardware
v32 = load("outputs/c1_vlm/arm_vlm_32b_0shot.json")
v7 = load("outputs/c1_vlm/arm_vlm_7b_0shot_rerun.json")
pipe = load(f"{SW}D_fdiset_lesion-detector_{NEW}/arm_pipeline_lesion_detector.json")
check("32B params", f"{v32['params_billion']:.2f} B", "arm_vlm_32b")
check("7B params", f"{v7['params_billion']:.2f} B", "arm_vlm_7b")
check("peak VRAM", r(v32["peak_vram_gb"], 1) + " GB", "arm_vlm_32b")
check("CPU latency", r(pipe["mean_latency_s"], 2) + " s", "D_fdiset_lesion-detector")
ctl32 = load("outputs/c1_vlm/control_pixels_32b.json")
ctl7 = load("outputs/c1_vlm/control_pixels_7b.json")
check("32B answer to blank", ctl32["answers"]["blank"], "control_pixels_32b")
check("32B answer to noise", ctl32["answers"]["noise"], "control_pixels_32b")
check("7B answer to noise", ctl7["answers"]["noise"], "control_pixels_7b")

# ------------------------------------------------------------------ Stage 4
# Rebuilt 14 Oct 2026 with the manuscript's Stage-4 subsection (RESULTS_LOG 2026-10-14): Stage 4a
# as it ships -- three runs of the radiograph-split recipe on the Tufts test split, the first
# model on the test radiographs it had not trained on, and the default's DENTEX firing rate.
# The Ningxia affected-tooth figures belonged to the first model and left the manuscript with
# it; every rate below is recomputed from the confusion counts, not read from a rounded field.
V2 = "outputs/bone_loss_eval/v2_retrain/"
TS = load(V2 + "test_summary.json")
runs = [TS[f"seed_{s}"]["all"] for s in (42, 43, 44)]
cf = [m["confusion"] for m in runs]
pos4 = runs[0]["positive_teeth"]
sens4 = [c["tp"] / (c["tp"] + c["fn"]) for c in cf]
spec4 = [c["tn"] / (c["tn"] + c["fp"]) for c in cf]
ppv4 = [c["tp"] / (c["tp"] + c["fp"]) for c in cf]
roc4 = [m["roc_auc"]["value"] for m in runs]
check("Stage 4a three sensitivities",
      f"{r(sens4[0]*100, 1)}%, {r(sens4[1]*100, 1)}% and {r(sens4[2]*100, 1)}%", V2 + "test_summary")
check("Stage 4a three counts", f"{cf[0]['tp']}, {cf[1]['tp']} and {cf[2]['tp']} of {pos4}", V2 + "test_summary")
check("Stage 4a pooled", f"{r(sum(c['tp'] for c in cf) / (3 * pos4) * 100, 1)}% pooled", V2 + "test_summary")
check("Stage 4a specificity range",
      f"{r(min(spec4)*100, 1)}--{r(max(spec4)*100, 1)}% specificity", V2 + "test_summary")
check("Stage 4a precision range", f"precision {r(min(ppv4)*100, 1)}--{r(max(ppv4)*100, 1)}%",
      V2 + "test_summary")
check("Stage 4a ROC range", f"ROC area {r(min(roc4), 2)}--{r(max(roc4), 2)}", V2 + "test_summary")
check("Stage 4a test split", f"{runs[0]['radiographs']} radiographs, {runs[0]['teeth']:,} teeth, {pos4} carrying",
      V2 + "test_summary")
check("Stage 4a range, abstract and conclusion",
      f"{r(min(sens4)*100, 1)}--{r(max(sens4)*100, 1)}%", V2 + "test_summary")
u4 = TS["shipped"]["unseen_by_shipped"]
check("Stage 4 first model, radiographs", f"{u4['radiographs']} test radiographs it had not trained on",
      V2 + "test_summary")
check("Stage 4 first model, counts", f"({u4['confusion']['tp']} of {u4['positive_teeth']})", V2 + "test_summary")
check("Stage 4 first model, sensitivity",
      f"{r(u4['confusion']['tp'] / u4['positive_teeth'] * 100, 1)}%", V2 + "test_summary")
D4 = load(V2 + "dentex_firing.json")["default"]
check("Stage 4a DENTEX firing",
      f"{r(D4['flagged'] / D4['teeth_detected'] * 100, 1)}% of detected teeth "
      f"({D4['flagged']} of {D4['teeth_detected']:,})", V2 + "dentex_firing")
# Stage 4b, added 14 Oct 2026 (RESULTS_LOG 2026-10-14d): the one registered test pass of the head
# retrained on bands of mask overlap (outputs/bone_loss_eval/v3_severity/PRE_REGISTRATION.md).
# Assert the verdict too: the manuscript says the registered rule was not met.
V3 = "outputs/bone_loss_eval/v3_severity/"
T3 = load(V3 + "test_summary.json")
A3 = T3["arms"]
assert not T3["eligible"], "the manuscript says the Stage-4b rule was not met"
assert A3["pred_43"]["macro_f1"] < A3["pred_prior"]["macro_f1"] < A3["pred_44"]["macro_f1"], \
    "the manuscript says seed 43, and not seed 44, is below the prior"
lo3, hi3 = A3["pred_42"]["macro_f1_ci95"]
check("Stage 4b seed 42",
      f"macro-F1 {r(A3['pred_42']['macro_f1'], 3)} [{r(lo3, 3)}, {r(hi3, 3)}] on {T3['test_teeth']} "
      f"held-out positive teeth", V3 + "test_summary")
check("Stage 4b tooth prior",
      f"against {r(A3['pred_prior']['macro_f1'], 3)} for an image-blind tooth-position prior", V3 + "test_summary")
check("Stage 4b seeds 43 and 44",
      f"two further runs gave {r(A3['pred_43']['macro_f1'], 3)}, below the prior, and "
      f"{r(A3['pred_44']['macro_f1'], 3)}", V3 + "test_summary")
d3 = T3["seed42_minus_prior"]
check("Stage 4b seed 42 minus prior",
      f"difference ${sgn(d3['value'])}$, interval $[{sgn(d3['ci95'][0])}, {sgn(d3['ci95'][1])}]$",
      V3 + "test_summary")
check("Stage 4b contrast-trained head",
      f"scored {r(A3['pred_old']['macro_f1'], 3)} on the same teeth "
      f"({r(T3['old_on_radiographs_it_did_not_train_on']['macro_f1'], 3)} without the three test radiographs",
      V3 + "test_summary")
# Table IV's caption, added 14 Oct 2026: DENTEX is in-domain for the lesion detector too.
M16 = "models/16_lever_b_pooled/run_summary.txt"
n16 = re.search(r"DENTEX-caries ([\d,]+) replicated", (REPO / M16).read_text(encoding="utf-8")).group(1)
check("lesion detector's DENTEX training images", f"trained on {n16} other DENTEX images", M16)
# Second publishability council, 15 Oct 2026 (RESULTS_LOG 2026-10-15).
RE = load(SW + "F_ningxia_random_effects.json")
assert sum(s["ci95_pp"][0] > 0 for s in RE["per_site"].values()) == 3, \
    "the manuscript says the lead holds at three of the four hospitals"
assert RE["ci95_pp"][0] < 0 < RE["ci95_pp"][1], "the manuscript says the random-effects interval spans zero"
check("Ningxia random-effects lead",
      f"the lead is ${sgn(RE['mean_pp'])}$ points with a 95% interval of "
      f"$[{sgn(RE['ci95_pp'][0])}, {sgn(RE['ci95_pp'][1])}]$", SW + "F_ningxia_random_effects")
check("Ningxia heterogeneity", f"$I^2 = {RE['i2_pct']:.0f}%$", SW + "F_ningxia_random_effects")
check("Ningxia prediction interval",
      f"further hospital of $[{sgn(RE['prediction_interval_pp'][0])}, {sgn(RE['prediction_interval_pp'][1])}]$",
      SW + "F_ningxia_random_effects")
check("Table V images", f"the {RES['C_dentex_lesion_agreement']['pooled']['n_images']} of the 164 DENTEX images",
      SW + "results")
cm = re.search(r"n=(\d+)\), (\d+) resamples",
               load("outputs/calibration/caries_gate_calibration_test.json")["ci_method"])
check("calibration resamples",
      f"({int(cm.group(2)):,} for the caries-gate calibration intervals, over its {cm.group(1)} source images)",
      "outputs/calibration/caries_gate_calibration_test.json")
M07 = "models/07_caries_cascade/run_summary.txt"
n07 = re.search(r"same (\d+) crops", (REPO / M07).read_text(encoding="utf-8")).group(1)
check("Stage 3b validation crops", f"validated on {n07} crops and never tested", M07)
check("lesion-to-tooth area ratio, from the two areas the text states",
      f"roughly {round(25000 / 731)}-fold", "main.tex: 731 px and ~25,000 px")

# ------------------------------------------ the tooth detector's registered guard
M = RES["M_tufts_test_box_map"]
check("Tufts box mAP, current detector", r(M["arm3c"]["box_map50"], 3), SW + "M_tufts_map")
check("Tufts box mAP, Tufts-only control", r(M["controlB"]["box_map50"], 3), SW + "M_tufts_map")
check("Tufts box mAP gap", f"{-M['arm3c_minus_controlB_pp']:.1f} points", SW + "M_tufts_map")
assert M["arm3c"]["box_map50"] < M["controlB"]["box_map50"] - 0.04, \
    "the manuscript says the registered Tufts guard was missed"
# what moved when only the tooth detector changed. The numbering (+34.40) and external gate
# agreement (+19.35) deltas left the manuscript on 14 Oct 2026 with the paragraph that used
# them -- the first Stage-4 model's "bone loss moved by nothing" argument (RESULTS_LOG 2026-10-14).
for key in ("C_dentex_lesion_agreement", "E_cariesxrays_lesion_agreement",
            "F_ningxia_caries_lesion_agreement"):
    check(f"constant's change with the detector ({key[:1]})",
          sgn(RES[key]["pooled"]["deltas"]["constant-molars: arm3c_minus_m11"]["delta_pp"]),
          SW + "results")

# --------------------------------------------------- three cohorts (Table VII)
cx_p = load(f"{SW}E_cariesxrays_pipeline_{NEW}/cariesxrays_external_pipeline.json")
cx_c = load(f"{SW}E_cariesxrays_constant-molars_{NEW}/cariesxrays_external_constant-molars.json")
assert cx_p["counts"]["lesions"] == cx_c["counts"]["lesions"], "arms are not paired"
check("CariesXrays lesions", f"{cx_p['counts']['lesions']:,}", "E_cariesxrays")
check("CariesXrays images", f"{cx_p['n_images_scored']:,}", "E_cariesxrays")
check("CariesXrays pipeline",
      r(cx_p["counts"]["lesions_covered"] / cx_p["counts"]["lesions"], 3), "E_cariesxrays")
check("CariesXrays constant",
      r(cx_c["counts"]["lesions_covered"] / cx_c["counts"]["lesions"], 3), "E_cariesxrays")
CXD = RES["E_cariesxrays_lesion_agreement"]["pooled"]["deltas"]
d = flip(CXD[f"{NEW}: pipeline_minus_constant-molars"])
check("CariesXrays constant - pipeline", f"{d['delta_pp']:.2f} percentage", SW + "results")
check("CariesXrays constant - pipeline CI", ci(d), SW + "results")
for arm, j in (("pipeline", cx_p), ("constant", cx_c)):
    check(f"CariesXrays {arm} hit rate",
          r(j["counts"]["flagged_hitting_a_lesion"] / j["counts"]["teeth_flagged"], 3), "E_cariesxrays")
check("CariesXrays constant flags more by",
      f"{(cx_c['counts']['teeth_flagged'] / cx_p['counts']['teeth_flagged'] - 1) * 100:.0f}%",
      "recomputed")
d = flip(DX[f"{NEW}: pipeline_minus_constant-molars"])
check("Table VII DENTEX constant - pipeline", sgn(d["delta_pp"]) + "\\ " + ci(d), SW + "results")

# ------------------------------------- Lever B: Stage 3a reformulation (Table VIII)
# The acceptance bar was frozen at commit ef3f453 before any arm was trained
# (outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md Sec 5/6). Assert the verdict
# itself, not only the numbers: a manuscript that claims the rule was met must not
# outlive an artefact that says it was not. The verdict belongs to the PREVIOUS front
# end, and the manuscript quotes its three differences as such; they are asserted here
# against the acceptance file exactly as before.
lb_p = load("outputs/lever_b_eval/acceptance_rule_B-pooled.json")
lb_s = load("outputs/lever_b_eval/acceptance_rule_B-single.json")
assert lb_p["sec6_rule_met"], "acceptance rule NOT met -- the manuscript claims it is"
assert sorted(lb_p["sec6_winning_cohorts"]) == ["cariesxrays", "ningxia"], \
    f"winning cohorts changed: {lb_p['sec6_winning_cohorts']}"


def pp(x):
    """Percentage-point delta the way the adoption sentence writes it, sign always shown."""
    return ("+" if x >= 0 else "-") + r(abs(x), 1)


for cohort, key in (("DENTEX", "dentex"), ("CariesXrays", "cariesxrays"),
                    ("Ningxia", "ningxia")):
    d = lb_p["cohorts"][key]["acceptance"]["lesion-detector_minus_constant-molars"]
    lo, hi = d["ci95_pp"]
    check(f"Lever B adoption, {cohort} delta pp", pp(d["delta_pp"]), "acceptance_rule_B-pooled")
    check(f"Lever B adoption, {cohort} delta CI", f"[{pp(lo)}, {pp(hi)}]",
          "acceptance_rule_B-pooled")

# The single-corpus arm, quoted in the prose as the transfer failure, and the pooled
# arm's CariesXrays figure beside it -- both scored when the rule was applied.
for cohort, key in (("DENTEX", "dentex"), ("CariesXrays", "cariesxrays"),
                    ("Ningxia", "ningxia")):
    a = lb_s["cohorts"][key]["arms"]["lesion-detector"]
    lo, hi = a["ci95"]
    check(f"Lever B single-corpus {cohort} CI", f"[{r(lo, 3)}, {r(hi, 3)}]",
          "acceptance_rule_B-single")
_cxl = load("outputs/cariesxrays_external_lever_b_b_pooled/cariesxrays_external_lesion-detector.json")
check("Lever B pooled arm on CariesXrays, at adoption",
      r(_cxl["counts"]["lesions_covered"] / _cxl["counts"]["lesions"], 3),
      "cariesxrays_external_lever_b_b_pooled")


# Table VIII itself: the three arms under the current detector, from the counts.
def agreement(rel):
    """Cohort-level lesion agreement and teeth flagged, over three output schemas."""
    d = load(rel)
    if "n_lesions" in d:                                    # lesion_localization.py
        return d["n_lesions_matched"] / d["n_lesions"], d["n_predicted_positive_teeth"], d["n_images"]
    if "counts" in d:                                       # cariesxrays_external.py
        c = d["counts"]
        return c["lesions_covered"] / c["lesions"], c["teeth_flagged"], c["images"]
    splits = list(d["by_category_split"].values())          # ningxia_external.py
    return (sum(s["lesions_covered"] for s in splits) / sum(s["lesions"] for s in splits),
            sum(s["predicted_positive"] for s in splits), sum(s["images"] for s in splits))


T8 = {"DENTEX": ("C_dentex_{dec}_{det}/lesion_localization.json", "C_dentex_lesion_agreement"),
      "CariesXrays": ("E_cariesxrays_{dec}_{det}/cariesxrays_external_{dec}.json",
                      "E_cariesxrays_lesion_agreement"),
      "Ningxia": ("F_ningxia_caries_{dec}_{det}/ningxia_external.json",
                  "F_ningxia_caries_lesion_agreement")}
for cohort, (tpl, key) in T8.items():
    per_image = {}
    for name, dec in (("gate", "pipeline"), ("constant", "constant-molars"),
                      ("lesion", "lesion-detector")):
        agr, n_flag, n_img = agreement(SW + tpl.format(dec=dec, det=NEW))
        per_image[name] = n_flag / n_img
        check(f"Table VIII {cohort} {name}", r(agr, 3), SW + tpl.format(dec=dec, det=NEW))
    d = RES[key]["pooled"]["deltas"][f"{NEW}: lesion-detector_minus_constant-molars"]
    check(f"Table VIII {cohort} delta", sgn(d["delta_pp"]) + "\\ " + ci(d), SW + "results")
    # Not a volume effect: the detector must flag fewer teeth than the constant.
    assert per_image["lesion"] < per_image["constant"], \
        f"{cohort}: detector now flags MORE teeth than the constant -- prose says fewer"
    if cohort != "DENTEX":
        assert d["excludes_zero"] and d["delta_pp"] > 0, f"{cohort}: prose says the detector is ahead"
        check(f"Table VIII {cohort} lesion detector teeth/image", r(per_image["lesion"], 2), "recomputed")
        check(f"Table VIII {cohort} constant teeth/image", r(per_image["constant"], 2), "recomputed")
d = NX["pooled"]["deltas"][f"{NEW}: pipeline_minus_constant-molars"]
check("Ningxia gate ahead of the constant by", f"${d['delta_pp']:.2f}$ points ahead", SW + "results")
d = NX["pooled"]["deltas"][f"{NEW}: lesion-detector_minus_constant-molars"]
check("Ningxia detector ahead of the constant by", f"${d['delta_pp']:.2f}$ points", SW + "results")
for site in ("test1", "test2", "test3", "test4"):
    d = NX[site]["deltas"][f"{NEW}: lesion-detector_minus_constant-molars"]
    check(f"Lever B per hospital, {site}", "$" + sgn(d["delta_pp"]) + "$ $" + ci(d) + "$", SW + "results")
    assert d["excludes_zero"] == (site != "test1"), f"{site}: prose says separated everywhere but test1"

# ----------------------------------------------- Parameter counts (Table II)
# Derived by scripts/count_model_params.py, which states one counting rule and applies
# it to every checkpoint. Stage 3a has two implementations since the Lever B adoption,
# so both totals are asserted. Regenerated 11 Oct 2026 for the current Stage-1 detector.
pc = load("outputs/param_counts/param_counts.json")
assert "arm3c_best.pt" in pc["checkpoints"]["stage1_detector"], \
    "param_counts.json was not counted with the current Stage-1 detector"
_P, _T = pc["params"], pc["totals"]
SRC = "outputs/param_counts (torch.load over models/*/)"
for label, key in (("stage-1 detector params", "stage1_detector"),
                   ("stage-2 FDI head params", "stage2_fdi_head"),
                   ("stage-3a lesion detector params", "stage3a_lesion"),
                   ("stage-3a gate variant params", "stage3a_gate_variant")):
    check(label, f"{r(_P[key] / 1e6, 2)} M", SRC)
for label, key in (("total params (default)", "total_default"),
                   ("total params (gate variant)", "total_gate_variant"),
                   ("caries-path params (default)", "caries_path_default"),
                   ("caries-path params (gate variant)", "caries_path_gate_variant")):
    check(label, f"{r(_T[key] / 1e6, 2)} M", SRC)
check("VLM / pipeline parameter ratio",
      f"roughly {round(v32['params_billion'] * 1e9 / _T['caries_path_default'], -1):.0f} in parameter count",
      "recomputed")

# ------------------------------------------ SUBMISSION_TODO rows b, g, l, m, n (14 Oct 2026)
# Added with the 15-page text's corrections (RESULTS_LOG 2026-10-14c); every value from the
# 12 Oct measurements (rows N, O, P, RESULTS_LOG 2026-10-12b) and the Stage-1 re-measurement.
FX = RES["F_ningxia_caries_lesion_agreement"]
t1, t2 = (FX[s]["deltas"]["arm3c: pipeline_minus_constant-molars"] for s in ("test1", "test2"))
assert t1["excludes_zero"] and t2["excludes_zero"], "the manuscript says both test1 and test2 are separated"
check("31-point range anchors", f"{sgn(-t1['delta_pp'], 1)}$ points at test1 to ${sgn(-t2['delta_pp'], 1)}$ at test2",
      SW + "results")
fp = FX["pooled"]["deltas"]
check("previous-detector Ningxia comparisons",
      f"${sgn(fp['m11: pipeline_minus_constant-molars']['delta_pp'])}$ and "
      f"${sgn(fp['m11: lesion-detector_minus_constant-molars']['delta_pp'])}$ points", SW + "results")
NF = RES["N_dentex_flagged_teeth"]
ld, cn = NF["lesion-detector"], NF["constant"]
check("lesion detector flagged codes",
      f"flags {ld['flagged_codes']} tooth codes, {r(ld['by_category']['caries'] / ld['flagged_codes'] * 100, 1)}% "
      f"of them carious and {r(ld['molar_share_of_flagged'] * 100, 1)}% molars", SW + "N_dentex_flagged_teeth")
check("constant flagged codes",
      f"constant's {cn['flagged_codes']:,}, {r(cn['by_category']['caries'] / cn['flagged_codes'] * 100, 1)}% "
      f"and {r(cn['molar_share_of_flagged'] * 100, 0)}%", SW + "N_dentex_flagged_teeth")
assert NF["labelled_healthy_teeth"] == 0, "the manuscript says no scored tooth is labelled healthy"
OC = RES["O_constant_placement"]["tufts"]["arm3c"]
for key in ("placement_precision", "reach"):
    e = OC[key]
    check(f"constant placement, {key}",
          f"{r(e['value'] * 100, 1)}% ${pct2(e)}$", SW + "O_constant_placement")
PU = RES["P_ufba_numbering"]
for mode in ("asis", "wide"):
    a = PU[mode]["arm3c"]
    check(f"UFBA-425 numbering, {mode}",
          f"{r(a['end_to_end']['value'] * 100, 1)}%" , SW + "P_ufba_numbering")
    check(f"UFBA-425 interval, {mode}", pct2(a["end_to_end"]), SW + "P_ufba_numbering")
    check(f"UFBA-425 recall, {mode}", f"recall {r(a['recall']['value'] * 100, 1)}%", SW + "P_ufba_numbering")
du = PU["asis"]["deltas"]["end_to_end_arm3c_minus_m11"]
check("UFBA-425 detector difference",
      f"${sgn(du['delta_pp'])}$ points $[{sgn(du['ci95_pp'][0])}, {sgn(du['ci95_pp'][1])}]$", SW + "P_ufba_numbering")

print("\n".join(ok))
if bad:
    print("\n" + "=" * 70)
    print("\n".join(bad))
    print(f"\n{len(ok)} checks passed, {len(bad)} FAILED")
    sys.exit(1)
print("\n" + "=" * 70)
print(f"{len(ok)} numeric claims verified against saved artefacts. No drift.")
