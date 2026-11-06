#!/usr/bin/env bash
# Build the Phase 3 report: XeLaTeX -> BibTeX -> XeLaTeX x2, into build/; copy the PDF to the report folder.
# Run from report/phase3:  bash tools/build.sh
set -u
cd "$(dirname "$0")/.."
mkdir -p build figures/repo
# figures/repo/ holds byte copies of figures tracked elsewhere in the repository; it is gitignored here and
# refreshed from the originals on every build, so the report never carries a stale or duplicate copy.
while read -r src dst; do
  cp "../../$src" "figures/repo/$dst" || echo "missing source figure: $src"
done <<'EOF'
paper/ieee/figures/R01_opg_primer.pdf R01_opg_primer.pdf
paper/ieee/figures/R02_walkthrough.pdf R02_walkthrough.pdf
paper/ieee/figures/R03_outcomes.pdf R03_outcomes.pdf
paper/ieee/figures/R04_training.pdf R04_training.pdf
paper/ieee/figures/R05_positional_prior.pdf R05_positional_prior.pdf
paper/ieee/figures/R06_architecture.pdf R06_architecture.pdf
paper/ieee/figures/R07_paired_differences.pdf R07_paired_differences.pdf
paper/ieee/figures/R08_numbering_reliability.pdf R08_numbering_reliability.pdf
outputs/stage1_switch/J_coverage_arm3c/c4_coverage_accuracy.png c4_coverage_accuracy_arm3c.png
outputs/stage1_switch/I_taxonomy_arm3c/stage2_failure_taxonomy.png stage2_failure_taxonomy_arm3c.png
outputs/detector_multicorpus/lever1_summary.png lever1_summary.png
docs/results/figures/paper/caries_gate_calibration_test.png caries_gate_calibration_test.png
docs/results/figures/paper/caries_gate_isotonic.png caries_gate_isotonic.png
docs/results/figures/paper/caries_gate_temperature_scaling.png caries_gate_temperature_scaling.png
EOF
# references.bib = the verified project bibliography (paper/source.bib, 2 Nov 2026 audit) + extra.bib
# (report-only entries, generated from Crossref). Never edit references.bib by hand.
cat ../../paper/source.bib extra.bib > references.bib
cp references.bib build/references.bib
run() { xelatex -interaction=nonstopmode -file-line-error -output-directory=build main.tex > build/xelatex.out 2>&1; }
run
( cd build && bibtex main > bibtex.out 2>&1 )
run
run
errors=$(grep -c "^[^ ]*:[0-9]*: \|^! " build/main.log)
undef=$(grep -c "undefined" build/main.log)
over=$(grep -c "^Overfull" build/main.log)
pages=$(tr -d '\n' < build/main.log | grep -o "([0-9]* pages" | tail -1 | tr -d '(')
echo "pages: ${pages:-none} | errors: $errors | undefined: $undef | overfull: $over"
grep -n "^[^ ]*:[0-9]*: \|^! " build/main.log | head -20
cp build/main.pdf Phase3_Report_PW26_MHR_06.pdf 2>/dev/null || true
