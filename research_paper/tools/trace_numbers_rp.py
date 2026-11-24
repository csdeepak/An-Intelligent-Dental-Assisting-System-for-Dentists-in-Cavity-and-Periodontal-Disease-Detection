# research_paper/ copy (23 Nov 2026) of outputs/citation_audit/2026-11-02_ars/trace_numbers.py: reads
# research_paper/paper_clean.md and adds this session's abstracts and check-run output as sources.
"""Trace every number in paper/paper.md to main.tex, a saved run file, or (for numbers quoted
from cited works) the fetched abstract / full text of that work. Prints the untraced ones."""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
R = Path(sys.argv[1]); HERE = R / "outputs/citation_audit/2026-11-02_ars"  # repo root as argv[1]
md = (R / "research_paper/paper_clean.md").read_text(encoding="utf-8").split("## Acknowledgment")[0]
md = re.sub(r"\[@[\w,]+\]", "", md)          # citation keys carry years, not claims

def norm_tex(t):
    return t.replace("{,}", ",").replace("\\,", " ").replace("$", "").replace("\\%", "%")

texts = [norm_tex((R / "paper/main.tex").read_text(encoding="utf-8"))]
for p in ["outputs/caries_arms/run_summary.txt", "outputs/caries_v4/run_summary.txt"]:
    texts.append((R / p).read_text(encoding="utf-8"))
for p in ["claim_abstracts.json", "new_abstracts.json"]:        # cited works' own text
    texts.append(json.dumps(json.loads((HERE / p).read_text(encoding="utf-8")), ensure_ascii=False))
# 23 Nov 2026: abstracts fetched for the research_paper/ citations, and this session's check run
for p in ["research_paper/literature/abstracts_new_2026-11-23.json", "research_paper/literature/abstracts_sourcebib_2026-11-23.json"]:
    texts.append(json.dumps(json.loads((R / p).read_text(encoding="utf-8")), ensure_ascii=False))
texts.append((R / "research_paper/audit_runs/checks_2026-11-23.txt").read_text(encoding="utf-8"))
# review round 1 sources (23 Nov 2026)
for p in ["research_paper/audit_runs/review_round_analyses.json", "models/18_bone_loss_radiograph_split/run_summary.txt",
          "models/19_bone_severity_overlap/run_summary.txt", "outputs/c1_vlm/c1_comparison.json",
          "outputs/stage1_switch/F_ningxia_random_effects_hksj.json", "outputs/caries_position_bias/caries_position_bias_test.json",
          "research_paper/literature/abstracts_lipton2014_2026-11-23.json", "research_paper/literature/abstract_mohammadrahimi_europepmc_2026-11-23.json"]:
    texts.append((R / p).read_text(encoding="utf-8"))
texts.append("0.9988 0.9788 accuracy F1 tooth numbering (Zancan full text, PMC12633937)")
texts.append("lesion-level sensitivity 0.70 internal 0.67 external (Bizjak, Inform Med Slov 29(1):1-7)")

# outputs/review_round1: the round-1 analyses (RESULTS_LOG 2026-11-02d), added 2 Nov 2026.
jsons = list((R / "outputs/stage1_switch").glob("*.json")) + list((R / "outputs/review_round1").glob("*.json")) + [R / p for p in (
    "outputs/caries_position_bias/caries_position_bias_test.json",
    "outputs/calibration/caries_gate_calibration_test.json",
    "outputs/calibration/caries_gate_isotonic.json",
    "outputs/stage1_switch/J_coverage_arm3c/c4_coverage_accuracy.json",
    "outputs/c4_abstention/c4_coverage_accuracy.json",
    "outputs/stage1_switch/I_taxonomy_arm3c/stage2_failure_taxonomy.json",
    "outputs/c1_vlm/c1_constant_arm_vlm_32b_0shot.json",
    "outputs/caries_arms/arms_comparison.json",
    "paper/ieee/figures/R_figures_facts.json",
    "paper/ieee/figures/R_draft_figures_facts.json",
    "paper/ieee/figures/R02_test_0_report.json")]
vals = set()
def walk(o):
    if isinstance(o, dict):
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
    elif isinstance(o, bool):
        return
    elif isinstance(o, (int, float)):
        for s in (float(o), abs(float(o))):
            vals.add(f"{s:g}")
            for d in range(5):
                vals.add(f"{s:.{d}f}"); vals.add(f"{100 * s:.{d}f}")
    elif isinstance(o, str):
        vals.update(re.findall(r"\d+(?:\.\d+)?", o))
for j in jsons:
    if j.exists(): walk(json.loads(j.read_text(encoding="utf-8")))
nums = set()
for t in texts:
    nums.update(m.replace(",", "") for m in re.findall(r"\d[\d,]*(?:\.\d+)?", t))
toks = re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", md)
distinct = sorted({x.replace(",", "").rstrip(".") for x in toks if x.replace(",", "").rstrip(".")}, key=float)
miss = [n for n in distinct if n not in nums and n not in vals and n.rstrip("0").rstrip(".") not in vals]
print("distinct numbers:", len(distinct), " untraced:", len(miss))
flat = md.replace(",", "")
for n in miss:
    i = flat.find(n)
    print(f"  {n:>10}  ...{flat[max(0, i - 70): i + 40]}...".replace("\n", " "))
