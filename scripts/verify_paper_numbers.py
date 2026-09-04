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


def check(label, needle, source):
    """Assert `needle` appears in the flattened manuscript."""
    if needle in FLAT:
        ok.append(f"  OK   {label:52s} {needle!r}")
    else:
        bad.append(f"  FAIL {label:52s} {needle!r}\n       source: {source}")


# ---------------------------------------------------------------- the ladder
# `row`, not `r` -- `r` is the rounding helper above, and shadowing it here would be
# invisible (comprehension scope keeps it working) right up until someone edits this line.
comp = {row["arm"]: row for row in load("outputs/c1_vlm/c1_comparison.json")["results"]}
const_file = load("outputs/c1_vlm/c1_constant_arm_vlm_32b_0shot.json")
held = next(b for b in const_file["constant_baselines"]
            if b["baseline"].startswith("held-out"))
oracle = next(b for b in const_file["constant_baselines"]
              if b["baseline"].startswith("ORACLE"))
S = "outputs/c1_vlm/"

for name, row in (("constant", held), ("pipeline", comp["pipeline"]),
                  ("vlm-32b", comp["vlm_32b_0shot"]),
                  ("vlm-7b", comp["vlm_7b_0shot_rerun"]),
                  ("oracle", oracle)):
    for metric in ("precision", "recall", "f1"):
        check(f"Table I {name} {metric}", f"{row[metric]:.3f}", S)

# 477 annotated carious teeth = tp + fn for any arm scored on the same GT
check("477 affected teeth", f"{held['tp'] + held['fn']}", S + " held-out tp+fn")
check("164 scored images", f"{const_file['n_images']}", S)

# The fitted constant's membership, as the text states it
check("constant set is the eight first/second molars",
      "first and second molars of all four", "held-out baseline label")
for code in ("16", "17", "26", "27", "36", "37", "46", "47"):
    if code not in held["baseline"]:
        bad.append(f"  FAIL constant set missing {code} in {held['baseline']}")

# --------------------------------------------------------- lesion localisation
# The *_agreement fields in these artefacts are stored to 4 dp. Formatting a stored
# 4-dp value to 3 dp rounds a rounded number, and the binary double breaks the tie
# downward: 0.4885 formats as "0.488" while the underlying 234/479 is 0.488518, which
# rounds to 0.489. That is how the manuscript carried 0.488 in Table II, Table IV and
# the abstract until 4 Sep 2026. Round once, from the integer counts, using r().
for tag, name in (("constant-molars", "constant"), ("pipeline", "pipeline"),
                  ("all-teeth", "ceiling")):
    j = load(f"outputs/lesion_loc_{tag}/lesion_localization.json")
    check(f"Table II {name} agreement",
          r(j["n_lesions_matched"] / j["n_lesions"], 3), tag)
    check(f"Table II {name} teeth flagged",
          f"{j['n_predicted_positive_teeth']:,}", tag)
    check(f"Table II {name} match rate",
          r(j["n_predicted_positive_matched_to_a_lesion"]
            / j["n_predicted_positive_teeth"], 3), tag)
lesions = load("outputs/lesion_loc_pipeline/lesion_localization.json")
check("479 annotated lesions", f"{lesions['n_lesions']}", "lesion_loc_pipeline")

# ------------------------------------------------------------------- external
def ext(d):
    return load(f"outputs/{d}/ningxia_external.json")["by_category_split"]


ep, ec = ext("ningxia_pipeline"), ext("ningxia_constant-molars")
sites = sorted(ep)
for s in sites:
    tag = s.split("/")[-1]
    # From counts, not the stored 4-dp field -- see the note above Table II.
    check(f"Table III {tag} pipeline",
          r(ep[s]["lesions_covered"] / ep[s]["lesions"], 3), "ningxia_pipeline")
    check(f"Table III {tag} constant",
          r(ec[s]["lesions_covered"] / ec[s]["lesions"], 3), "ningxia_constant-molars")
    check(f"Table III {tag} lesions", f"{ep[s]['lesions']:,}", "ningxia_pipeline")
tot = sum(ep[s]["lesions"] for s in sites)
check("external total lesions", f"{tot:,}", "sum over four sites")
check("external total images", f"{sum(ep[s]['images'] for s in sites)}", "sum")
check("pooled pipeline",
      r(sum(ep[s]["lesions_covered"] for s in sites) / tot, 3), "recomputed")
check("pooled constant",
      r(sum(ec[s]["lesions_covered"] for s in sites) / tot, 3), "recomputed")

# ------------------------------------------------------------------- stage 2
s2 = load("outputs/stage2_segdet/stage2_summary_head.json")
tax = load("outputs/stage2_taxonomy/stage2_failure_taxonomy.json")
check("Stage-2 end-to-end", r(s2["fdi_exact_of_all"]*100, 1) + "%", "stage2_segdet")
check("Stage-2 of detected", r(s2["fdi_exact_of_detected"]*100, 1) + "%", "stage2_segdet")
check("never detected", r((1-s2["recall"])*100, 1) + "%", "stage2_segdet")
check("detection recall", r(s2["recall"]*100, 1) + "%", "stage2_segdet")
check("correct teeth", f"{tax['categories']['correct']}", "taxonomy")
check("GT teeth", f"{s2['n_gt_teeth']}", "stage2_segdet")
check("detected teeth", f"{tax['n_detected']}", "taxonomy")
check("wrong codes", f"{tax['n_wrong_code']}", "taxonomy")
check("off-by-one", f"{tax['categories']['off_by_one']}", "taxonomy")
quad_err = (tax["categories"]["wrong_arch"] + tax["categories"]["mirror_lr"]
            + tax["categories"]["other"])
check("quadrant-level errors", f"{quad_err}", "taxonomy wrong_arch+mirror+other")

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
c4 = load("outputs/c4_abstention/c4_coverage_accuracy.json")
check("numbering full coverage", f"{c4['stage2']['accuracy_full_coverage']:.3f}", "c4")
check("numbering at 75%", f"{c4['stage2']['at_75']['accuracy']:.3f}", "c4")
check("numbering gain", f"{c4['stage2']['gain_at_75']['gain_pp']:.2f}", "c4")
check("gate full coverage",
      f"{c4['caries_gate']['accuracy_full_coverage']:.3f}", "c4")
check("gate at 75%", f"{c4['caries_gate']['at_75']['accuracy']:.3f}", "c4")
check("gate gain", f"{c4['caries_gate']['gain_at_75']['gain_pp']:.2f}", "c4")
check("pre-registered coverage",
      r(c4["stage2"]["operating_point"]["coverage"]*100, 1) + "%", "c4")
check("pre-registered accuracy",
      f"{c4['stage2']['operating_point']['accuracy']:.3f}", "c4")
check("90%-coverage accuracy", f"{c4['stage2']['at_90']['accuracy']:.3f}", "c4")

# ------------------------------------------------------------- VLM + hardware
v32 = load("outputs/c1_vlm/arm_vlm_32b_0shot.json")
v7 = load("outputs/c1_vlm/arm_vlm_7b_0shot_rerun.json")
pipe = load("outputs/c1_vlm/arm_pipeline.json")
check("32B params", f"{v32['params_billion']:.2f} B", "arm_vlm_32b")
check("7B params", f"{v7['params_billion']:.2f} B", "arm_vlm_7b")
check("peak VRAM", r(v32["peak_vram_gb"], 1) + " GB", "arm_vlm_32b")
check("CPU latency", f"{pipe['mean_latency_s']:.2f} s", "arm_pipeline")
ctl32 = load("outputs/c1_vlm/control_pixels_32b.json")
ctl7 = load("outputs/c1_vlm/control_pixels_7b.json")
check("32B answer to blank", ctl32["answers"]["blank"], "control_pixels_32b")
check("32B answer to noise", ctl32["answers"]["noise"], "control_pixels_32b")
check("7B answer to noise", ctl7["answers"]["noise"], "control_pixels_7b")

# ------------------------------------------------------------------ bone loss
bl = ext("ningxia_external_segdet")
sens = [bl[f"periodontitis/test{i}"]["affected_tooth_sensitivity"] for i in range(1, 5)]
check("bone-loss external range",
      r(min(sens)*100, 1) + "--" + r(max(sens)*100, 1) + "%", "ningxia_external_segdet")

# ------------------------------------------------------- parameter counts
# Counted from the checkpoints on 28 Aug 2026; see docs/paper/REBUILD_AUDIT.md.
# --------------------------------------------------- CariesXrays (Table IV)
# Sixth cohort, frozen pipeline. Both arms scored the SAME seed-fixed random draw,
# so the paired delta below is recomputed here rather than copied from the manuscript.
cx_p = load("outputs/cariesxrays_external_rand/cariesxrays_external_pipeline.json")
cx_c = load("outputs/cariesxrays_external_rand/cariesxrays_external_constant-molars.json")
assert cx_p["counts"]["lesions"] == cx_c["counts"]["lesions"], "arms are not paired"
check("CariesXrays lesions", f"{cx_p['counts']['lesions']:,}", "cariesxrays_external_rand")
check("CariesXrays images", f"{cx_p['n_images_scored']:,}", "cariesxrays_external_rand")
check("CariesXrays pipeline", f"{cx_p['agreement_covered']:.3f}", "cariesxrays_external_rand")
check("CariesXrays constant", f"{cx_c['agreement_covered']:.3f}", "cariesxrays_external_rand")
check("CariesXrays delta pp",
      f"{(cx_c['agreement_covered'] - cx_p['agreement_covered']) * 100:.1f}", "recomputed")
check("CariesXrays pipeline match rate",
      f"{cx_p['match_rate_DIAGNOSTIC_not_precision']:.3f}", "cariesxrays_external_rand")
check("CariesXrays constant match rate",
      f"{cx_c['match_rate_DIAGNOSTIC_not_precision']:.3f}", "cariesxrays_external_rand")
# the constant flags more teeth -- the manuscript states 64%, recompute it
_fl_p = cx_p["counts"]["teeth_flagged"]; _fl_c = cx_c["counts"]["teeth_flagged"]
check("CariesXrays constant flags more by",
      f"{(_fl_c / _fl_p - 1) * 100:.0f}%", "recomputed")

# ------------------------------------- Lever B: Stage 3a reformulation (Table V)
# The acceptance bar was frozen at commit ef3f453 before any arm was trained
# (outputs/lever_B_lesion_caries_path/PRE_REGISTRATION.md Sec 5/6). Assert the verdict
# itself, not only the numbers: a manuscript that claims the rule was met must not
# outlive an artefact that says it was not.
lb_p = load("outputs/lever_b_eval/acceptance_rule_B-pooled.json")
lb_s = load("outputs/lever_b_eval/acceptance_rule_B-single.json")
assert lb_p["sec6_rule_met"], "acceptance rule NOT met -- the manuscript claims it is"
assert sorted(lb_p["sec6_winning_cohorts"]) == ["cariesxrays", "ningxia"], \
    f"winning cohorts changed: {lb_p['sec6_winning_cohorts']}"


def pp(x):
    """Percentage-point delta the way the table writes it, sign always shown."""
    return ("+" if x >= 0 else "-") + r(abs(x), 1)


# Point estimates are recomputed from the raw per-arm outputs rather than read from
# the acceptance file, whose values are already rounded to 4 dp: Ningxia's 0.500494
# is stored there as 0.5005, and rounding that again to 3 dp gives 0.501, a digit
# that exists nowhere in the evaluation. Round once, from the counts.
def agreement(rel):
    """Cohort-level lesion agreement, over three different output schemas."""
    d = load(rel)
    if "n_lesions" in d:                                    # lesion_localization.py
        return d["n_lesions_matched"] / d["n_lesions"]
    if "counts" in d:                                       # cariesxrays_external.py
        return d["counts"]["lesions_covered"] / d["counts"]["lesions"]
    splits = d["by_category_split"].values()                # ningxia_external.py
    return (sum(s["lesions_covered"] for s in splits)
            / sum(s["lesions"] for s in splits))


LEVER_B = {
    "DENTEX": ("outputs/lever_b_eval/dentex_{}/lesion_localization.json",
               {"gate": "pipeline", "constant": "constant", "lesion": "lesion_b_pooled",
                "single": "lesion_b_single"}, "dentex"),
    "Ningxia": ("outputs/lever_b_eval/ningxia_{}/ningxia_external.json",
                {"gate": "pipeline", "constant": "constant", "lesion": "lesion_b_pooled",
                 "single": "lesion_b_single"}, "ningxia"),
}
for cohort, (tpl, arms, key) in LEVER_B.items():
    for name in ("gate", "constant", "lesion"):
        check(f"Lever B {cohort} {name}", r(agreement(tpl.format(arms[name])), 3),
              f"lever_b_eval/{arms[name]}")
# CariesXrays arms live in two directories: the three comparators were scored in the
# B-single pass and reused unchanged, since the gate and the constant do not depend
# on which lesion arm is being tested.
CX = "outputs/cariesxrays_external_lever_b_b_{}/cariesxrays_external_{}.json"
for name, (arm, dec) in {"gate": ("single", "pipeline"),
                         "constant": ("single", "constant-molars"),
                         "lesion": ("pooled", "lesion-detector")}.items():
    check(f"Lever B CariesXrays {name}", r(agreement(CX.format(arm, dec)), 3),
          f"cariesxrays_external_lever_b_b_{arm}")

for cohort, key in (("DENTEX", "dentex"), ("CariesXrays", "cariesxrays"),
                    ("Ningxia", "ningxia")):
    c = lb_p["cohorts"][key]
    d = c["acceptance"]["lesion-detector_minus_constant-molars"]
    lo, hi = d["ci95_pp"]
    check(f"Lever B {cohort} delta pp", pp(d["delta_pp"]), "acceptance_rule_B-pooled")
    check(f"Lever B {cohort} delta CI", f"[{pp(lo)}, {pp(hi)}]", "acceptance_rule_B-pooled")
    # Not a volume effect: the detector must flag no more teeth than the constant.
    rate_lesion = c["arms"]["lesion-detector"]["mean_predicted_positive_per_image"]
    assert rate_lesion <= c["arms"]["constant-molars"]["mean_predicted_positive_per_image"], \
        f"{cohort}: detector now flags MORE teeth than the constant -- prose says fewer"

# The single-corpus arm, quoted in the prose as the transfer failure.
for cohort, key in (("DENTEX", "dentex"), ("CariesXrays", "cariesxrays"),
                    ("Ningxia", "ningxia")):
    a = lb_s["cohorts"][key]["arms"]["lesion-detector"]
    lo, hi = a["ci95"]
    check(f"Lever B single-corpus {cohort} CI", f"[{r(lo, 3)}, {r(hi, 3)}]",
          "acceptance_rule_B-single")

for cohort, key in (("CariesXrays", "cariesxrays"), ("Ningxia", "ningxia")):
    for arm in ("lesion-detector", "constant-molars"):
        rate = lb_p["cohorts"][key]["arms"][arm]["mean_predicted_positive_per_image"]
        check(f"Lever B {cohort} {arm} teeth/image", r(rate, 2), "acceptance_rule_B-pooled")

# ----------------------------------------------- Parameter counts (Table I)
# These were hardcoded literals until 4 Sep 2026, carrying a provenance label they
# did not earn. They are now derived by scripts/count_model_params.py, which states
# one counting rule and applies it to every checkpoint -- see that file for why the
# old table mixed two rules. Stage 3a has two implementations since the Lever B
# adoption, so both totals are asserted; a table that reports only one of them will
# fail here, which is the point.
pc = load("outputs/param_counts/param_counts.json")
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

print("\n".join(ok))
if bad:
    print("\n" + "=" * 70)
    print("\n".join(bad))
    print(f"\n{len(ok)} checks passed, {len(bad)} FAILED")
    sys.exit(1)
print("\n" + "=" * 70)
print(f"{len(ok)} numeric claims verified against saved artefacts. No drift.")
