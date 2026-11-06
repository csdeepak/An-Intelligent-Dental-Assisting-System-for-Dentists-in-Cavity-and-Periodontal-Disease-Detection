"""Run the Research Communication Engine gates on the report and record them (validation).

  G1  validate_artifacts.py   the .rcs trail against the skill's schemas and references
  G3  lint_draft.py           the Markdown view of the report (build/report.md): claim tags, licences,
                              limitations and rationale present, citations registered
      verify_numbers.py       every number traced to an evidence item or the file it points to (--strict)
  GL  verify_citations.py     citation gate, offline (the lookups were made in the 2 Nov audit)
  --  skim_layer.py check     the abstract keeps what its tagged claims say (numbers, intervals, hedges)

Reports go to .rcs/audits/gates/; a gate is marked passed in .rcs/state.json only when its report has no
ERROR. G4 (review panel) and GI (integrity verifier) need isolated reviewer roles that this session does
not have, so they are recorded as not run, never as passed.

    python -I tools/rcs_check.py      (after tools/build.sh, tools/rcs_build.py and tools/export_md.py)
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
RCS = HERE / ".rcs"
GATES = RCS / "audits" / "gates"
TOOLS = Path.home() / "AppData/Local/Temp/claude/rws/tools"
ROOT = HERE.parents[1]
ACRONYMS = ("CPU,GPU,GPUs,JSON,PDF,CLI,PNG,JPEG,RGB,RAM,URL,API,IEEE,BMC,MD5,SHA,CSV,ISO,CC,BY,NC,SA,PES,CSE,UI,"
            "VRAM,OS,MB,GB,AI,ML,CNN,CNNs,OPGs,DENTEX,UFBA,YOLO,YOLO11,COCO,INMIC,AAAI,ICICKE,ICPC2T,IMSA,HUNT4,"
            "QUADAS,PRISMA,PROSPERO,AAP,EFP,COVID,VL,CAM,AP50")
GATES.mkdir(parents=True, exist_ok=True)


def run(args):
    p = subprocess.run([sys.executable, "-I", "-X", "utf8"] + [str(a) for a in args], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", cwd=HERE)
    return p.returncode, p.stdout + p.stderr


def errors_in(path):
    """(errors, warnings) of a tool report: its findings or items list, else its counters."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    f = d if isinstance(d, list) else d.get("findings") if isinstance(d.get("findings"), list) else d.get("items")
    if isinstance(f, list):
        return sum(1 for x in f if isinstance(x, dict) and x.get("level") == "ERROR"), \
               sum(1 for x in f if isinstance(x, dict) and x.get("level") == "WARN")
    return int(d.get("errors", 0) or 0), int(d.get("warnings", 0) or 0)


draft, abstract = HERE / "build" / "report.md", HERE / "build" / "abstract.md"
out = {}
rc, log = run([TOOLS / "lint_draft.py", draft, "--rcs", RCS, "--known-acronyms", ACRONYMS, "--out", GATES / "G3_lint.json"])
out["G3 lint"] = (rc, errors_in(GATES / "G3_lint.json"))
rc, log = run([TOOLS / "verify_numbers.py", draft, "--rcs", RCS, "--project-root", ROOT, "--strict",
               "--out", GATES / "G3_numbers.json"])
out["G3 numbers"] = (rc, errors_in(GATES / "G3_numbers.json"))
rc, log = run([TOOLS / "verify_citations.py", RCS, "--gate", "--draft", draft, "--out", GATES / "GL_citations.json"])
out["GL citations"] = (rc, errors_in(GATES / "GL_citations.json") if (GATES / "GL_citations.json").exists() else (1, 0))
gl_log = log
rc, log = run([TOOLS / "skim_layer.py", "check", abstract, "--rcs", RCS, "--json"])
try:
    sk = json.loads(log[log.index("["):]) if "[" in log else []
except ValueError:
    sk = []
(GATES / "skim_abstract.json").write_text(json.dumps({"findings": sk}, indent=1) + "\n", encoding="utf-8")
out["skim abstract"] = (rc, (sum(1 for x in sk if x.get("level") == "ERROR"), sum(1 for x in sk if x.get("level") == "WARN")))

state_f = RCS / "state.json"
state = json.loads(state_f.read_text(encoding="utf-8"))
g = state.setdefault("gates", {})
g["G3"] = "passed" if out["G3 lint"][1][0] == 0 and out["G3 numbers"][1][0] == 0 else "failed"
g["GL"] = "passed" if out["GL citations"][0] == 0 and out["GL citations"][1][0] == 0 else "failed"
g["G4"] = "not run: the isolated review-panel roles are not available in this session"
g["GI"] = "not run: the isolated integrity-verifier role is not available in this session"
g.pop("G1", None)
state_f.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")

# G1 last, so that it validates the gate reports just written; mark it only on a clean report
rc, log = run([TOOLS / "validate_artifacts.py", RCS, "--project-root", ROOT, "--out", GATES / "G1_validate.json"])
e1 = errors_in(GATES / "G1_validate.json")
if e1[0] == 0:
    g["G1"] = "passed"
    state_f.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")
    rc, log = run([TOOLS / "validate_artifacts.py", RCS, "--project-root", ROOT, "--out", GATES / "G1_validate.json"])
    e1 = errors_in(GATES / "G1_validate.json")
out["G1 validate"] = (rc, e1)
eff = [ln for ln in log.splitlines() if ln.startswith("effective gates")]

for k, (rc, (e, w)) in out.items():
    print(f"{k:<14} exit {rc}  errors {e}  warnings {w}")
print(eff[0] if eff else "")
if out["GL citations"][0] != 0:
    print("GL output:", gl_log[-600:])
sys.exit(0 if all(v[1][0] == 0 for v in out.values()) else 1)
