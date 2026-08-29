# -*- coding: utf-8 -*-
"""Inline every figure into the handbook as a data URI.

The artifact CSP blocks external image hosts, so a <img src="paper/fig.png"> renders as a
broken icon with no error anywhere. Every image has to be embedded.
"""
import base64
import re
from pathlib import Path

REPO = Path(r"C:\Users\csdee\PESU\capstone\An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection")
SCRATCH = Path(r"C:\Users\csdee\AppData\Local\Temp\claude\C--Users-csdee-PESU-capstone-An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection\e2d2743c-63a8-4868-8682-9dcfe00b4cc5\scratchpad")
SRC = SCRATCH / "handbook.html"
OUT = SCRATCH / "handbook_final.html"

IMAGES = {
    "FIG_BASELINES": "paper/fig_baselines.png",
    "FIG_STAGE2":    "paper/fig_stage2.png",
    "FIG_COVERAGE":  "paper/fig_coverage.png",
    "FIG_CALIB":     "paper/fig_calibration.png",
    "FIG_BONELOSS":  "paper/fig_boneloss.png",
    "PREVIEW1":      "paper/preview_p1-01.png",
    "PREVIEW4":      "paper/preview_p4-04.png",
}

html = SRC.read_text(encoding="utf-8")

# Stray no-op left in the stylesheet: an empty @media nested inside a :root rule.
# Harmless but it is dead code in a file other people will read.
html = html.replace(
    '  :root:not([data-theme="light"]){ @media (prefers-color-scheme:dark){} }\n', "")

total = 0
for token, rel in IMAGES.items():
    p = REPO / rel
    if not p.exists():
        raise SystemExit(f"missing image: {p}")
    raw = p.read_bytes()
    total += len(raw)
    uri = "data:image/png;base64," + base64.b64encode(raw).decode("ascii")
    placeholder = "{{" + token + "}}"
    if placeholder not in html:
        raise SystemExit(f"placeholder {placeholder} not found in handbook.html")
    html = html.replace(placeholder, uri)
    print(f"  {token:14s} {len(raw)/1024:7.0f} KB  <- {rel}")

leftover = re.findall(r"\{\{[A-Z_0-9]+\}\}", html)
assert not leftover, f"unreplaced placeholders: {leftover}"

OUT.write_text(html, encoding="utf-8")
print(f"\nsource images : {total/1024/1024:.2f} MB")
print(f"final page    : {len(html.encode('utf-8'))/1024/1024:.2f} MB  (limit 16 MB)")
print(f"-> {OUT}")
