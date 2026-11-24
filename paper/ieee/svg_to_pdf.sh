#!/usr/bin/env bash
# Convert the RCE-validated SVGs (.rcs/plan/figures) to PDF with headless Chrome. No redraw:
# the SVG is printed as-is onto a letter page (content top-left); main.tex crops it with trim/clip.
# Run from the repo root in Git Bash. Usage: bash paper/ieee/svg_to_pdf.sh
set -e
CH="/c/Program Files/Google/Chrome/Application/chrome.exe"
TMP=$(mktemp -d); ROOT=$(cygpath -w "$PWD"); U="${ROOT//\\//}"
for f in .rcs/plan/figures/*.svg; do
  b=$(basename "$f" .svg)
  printf '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0}img{display:block}</style></head><body><img src="%s.svg"></body></html>' "$b" > ".rcs/plan/figures/_$b.html"
  "$CH" --headless --disable-gpu --no-pdf-header-footer --user-data-dir="$(cygpath -w "$TMP/p_$b")" \
        --print-to-pdf="$(cygpath -w "$TMP/$b.pdf")" "file:///$U/.rcs/plan/figures/_$b.html" >/dev/null 2>&1
  cp "$TMP/$b.pdf" paper/ieee/figures/ && echo "$b.pdf"
  rm -f ".rcs/plan/figures/_$b.html"
done
