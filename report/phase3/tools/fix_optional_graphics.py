"""One-off, idempotent: load the images kept out of git through \\optionalgraphics (6 Nov 2026).

The figures reproduced from the reviewed papers (figures/phase2/p2_2_*), the Tufts crops
(figures/phase2/p2_5_*) and the app screenshots (figures/screens/) are gitignored. Their \\includegraphics
calls become \\optionalgraphics (preamble.tex), which draws a placeholder when the file is absent.

    python -I tools/fix_optional_graphics.py      (from report/phase3)
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
PAT = re.compile(r"\\includegraphics(\[[^\]]*\]\{figures/(?:phase2/p2_[25]_|screens/))")
n = 0
for f in sorted(HERE.glob("chapters/*.tex")) + sorted(HERE.glob("appendices/*.tex")):
    t = f.read_bytes().decode("utf-8")                       # bytes in and out: line endings kept as they are
    new, k = PAT.subn(lambda m: "\\optionalgraphics" + m.group(1), t)
    if k:
        f.write_bytes(new.encode("utf-8"))
        n += k
        print(f"{f.relative_to(HERE)}: {k}")
print(f"{n} calls switched to \\optionalgraphics")
