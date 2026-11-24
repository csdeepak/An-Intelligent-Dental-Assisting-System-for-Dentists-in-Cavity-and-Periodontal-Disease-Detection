"""24 Nov 2026: swap the problem-first Abstract and Introduction (research_paper/abstract_intro_v2.md)
into research_paper/paper.md, and condense Section II to what the new Introduction does not cover.
No citation and no claim tag is dropped (asserted below). Run from the repo root, once."""
import re
from pathlib import Path

R = Path("research_paper")
p = R / "paper.md"
s = p.read_text(encoding="utf-8")
v2 = (R / "abstract_intro_v2.md").read_text(encoding="utf-8")
before_cites = set(re.findall(r"@([a-z0-9]+)", s.split("## III.")[0]))
before_tags = set(re.findall(r"\{C\d{3}\}", s))

# --- Abstract
new_abs = v2.split("## Abstract")[1].split("**Index Terms")[0].strip()
a0 = s.index("## Abstract") + len("## Abstract")
a1 = s.index("**Index Terms")
s = s[:a0] + "\n\n" + new_abs + "\n\n" + s[a1:]

# --- Introduction: '### Title' subheads -> bold run-in headings (the converter has no unlettered ###)
intro = v2.split("## I. Introduction")[1].strip()
intro = re.sub(r"### ([^\n]+)\n\n", lambda m: f"**{m.group(1)}.** ", intro)
i0 = s.index("## I. Introduction") + len("## I. Introduction")
i1 = s.index("## II. Related Work")
s = s[:i0] + "\n\n" + intro + "\n\n" + s[i1:]

# --- Section II: keep Datasets and Calibration; one paragraph for what Section I no longer carries
r0 = s.index("## II. Related Work") + len("## II. Related Work")
r1 = s.index("## III.")
old = s[r0:r1]
datasets = re.search(r"\*\*Datasets\.\*\*[^\n]+", old).group(0)
calib = re.search(r"\*\*Calibration, abstention, VLMs and translation\.\*\*[^\n]+", old).group(0)
further = ("**Further related work.** Beyond the work discussed in Section I, a multi-stage system reports "
  "better results than prior methods on Tufts and two other datasets [@zhang2025reliable], and public "
  "datasets have been combined to predict segmentation, FDI numbers and diagnoses together "
  "[@vannistelrooij2024combining]. Caries analysis has used dual networks [@lim2024dual], dedicated "
  "classifiers [@bilal2024pdcnet] and contrastive feature pyramids [@chen2024cariesxrays]. Radiographic "
  "periodontal bone loss is measured against anatomical references: besides the CNN of Section I, a hybrid "
  "method located the bone level and cemento-enamel junction to stage periodontitis radiographically "
  "[@chang2020deep] {C041}, and a periodontitis model built from OPGs linked to clinical diagnoses and "
  "tested at four centres is the strongest design we found [@li2025novel]. A YOLOv11 detector of 13 "
  "conditions fell from mAP@0.5 0.857 to 0.806 on external images, weakest on subtle pathology such as "
  "caries [@mutlu2026comparison]; aggregate metrics can hide failures on clinically important subsets "
  "[@oakdenrayner2020hidden], and biases enter medical-imaging evaluation at every step "
  "[@varoquaux2022machine]. Visual-question-answering models also lost accuracy when answer priors "
  "differed between training and test [@agrawal2018dont], and COVID-19 detectors relied on confounders "
  "and failed at new hospitals [@degrave2021ai].")
s = s[:r0] + "\n\n" + datasets + "\n\n" + further + "\n\n" + calib + "\n\n" + s[r1:]

after_cites = set(re.findall(r"@([a-z0-9]+)", s.split("## III.")[0]))
after_tags = set(re.findall(r"\{C\d{3}\}", s))
assert before_cites <= after_cites, before_cites - after_cites
assert before_tags <= after_tags, before_tags - after_tags
p.write_text(s, encoding="utf-8")
print("swapped; citations kept:", len(after_cites), "tags kept:", len(after_tags))
