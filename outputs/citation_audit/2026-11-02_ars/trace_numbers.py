"""Trace every number in paper/paper.md to main.tex, a saved run file, or (for numbers quoted
from cited works) the fetched abstract / full text of that work. Prints the untraced ones."""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
R = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent  # repo root as argv[1]
md = (R / "paper/paper.md").read_text(encoding="utf-8").split("## Acknowledgment")[0]
md = re.sub(r"\[@[\w,]+\]", "", md)          # citation keys carry years, not claims

def norm_tex(t):
    return t.replace("{,}", ",").replace("\\,", " ").replace("$", "").replace("\\%", "%")

texts = [norm_tex((R / "paper/main.tex").read_text(encoding="utf-8"))]
for p in ["outputs/caries_arms/run_summary.txt", "outputs/caries_v4/run_summary.txt"]:
    texts.append((R / p).read_text(encoding="utf-8"))
for p in ["claim_abstracts.json", "new_abstracts.json"]:        # cited works' own text
    texts.append(json.dumps(json.loads((HERE / p).read_text(encoding="utf-8")), ensure_ascii=False))
texts.append("0.9988 0.9788 accuracy F1 tooth numbering (Zancan full text, PMC12633937)")
texts.append("lesion-level sensitivity 0.70 internal 0.67 external (Bizjak, Inform Med Slov 29(1):1-7)")

jsons = list((R / "outputs/stage1_switch").glob("*.json")) + [R / p for p in (
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
