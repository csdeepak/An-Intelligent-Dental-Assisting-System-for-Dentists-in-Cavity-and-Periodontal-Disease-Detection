"""Claim check of the Phase 2 literature-survey entries against each paper's abstract.

For every entry kept from the Phase 2 report, list the numbers and named methods Phase 2 attributed to
the paper and report which of them the abstract contains. A number not in the abstract is not
asserted in the Phase 3 report unless the full text was checked (recorded in .rcs/corpus/corpus_log.md).

    python -I tools/check_p2_survey.py   (run from report/phase3)
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ABS = json.loads(Path(".rcs/corpus/p2_abstracts.json").read_text(encoding="utf-8"))
extra = Path(".rcs/corpus/p3_abstracts.json")
if extra.exists():
    ABS.update(json.loads(extra.read_text(encoding="utf-8")))

# entry -> (key, phase 2 claims as regexes)
ENTRIES = {
    "2.1 Ayhan":       ("ayhan2025detection", [r"YOLOv7", r"CBAM", r"1,?004", r"0\.846", r"0\.83\b"]),
    "2.2 Khuwaja":     ("khuwaja2024ai", [r"YOLOv8", r"ResNet", r"EfficientDet", r"MobileNet", r"7,?447", r"0\.67"]),
    "2.3 Jundaeng":    ("jundaeng2025advanced", [r"YOLOv8", r"0\.98", r"0\.995", r"CEJ|cemento"]),
    "2.4 Alharbi":     ("alharbi2023detection", [r"U-?Net\+\+|UNet\+\+", r"U-?Net3\+|UNet3\+", r"1,?500", r"95"]),
    "2.5 Chen 2023":   ("chen2023deep", [r"YOLOv7", r"EfficientNet", r"periapical", r"98"]),
    "2.6 Nassiri":     ("nassiri2025yolo", [r"YOLOv5", r"YOLOv9", r"DENTEX", r"0\.978|97\.8"]),
    "2.7 Asci":        ("asci2024deep", [r"U-?Net", r"6,?075", r"0\.91", r"0\.86|0\.85"]),
    "2.8 CariesXrays": ("chen2024cariesxrays", [r"contrastive", r"6,?000", r"13,?\d{3}", r"84\.1"]),
    "2.9 AI-Dentify":  ("perez2024ai", [r"YOLOv5", r"RetinaNet", r"EfficientDet", r"13,?887", r"0\.647|64\.7"]),
    "2.10 Albano":     ("albano2024artificial", [r"20 (studies|articles)", r"0\.98|98"]),
    "2.11 Kaushik":    ("kaushik2025densenet201", [r"DenseNet201", r"29,?815", r"91"]),
    "2.12 bone review":("khubrani2025detection", [r"20 (studies|articles)", r"20,?000", r"systematic"]),
    "2.13 Chmielewski":("chmielewski20252018", [r"2018", r"AAP|EFP"]),
    "2.14 Gamal":      ("gamal2025automated", [r"ResNet50", r"VGG19", r"DenseNet121", r"Inception", r"1,?814", r"92\.93"]),
    "2.15 Sastika":    ("sastika2025ai", [r"85", r"99"]),
}
for name, (key, pats) in ENTRIES.items():
    a = (ABS.get(key) or {}).get("abstract") or ""
    hits = [(p, bool(re.search(p, a, re.I))) for p in pats]
    print(f"{name:18s} {key:26s} abstract={'yes' if a else 'NO '}  " +
          "  ".join(f"{p}:{'Y' if h else '-'}" for p, h in hits))
