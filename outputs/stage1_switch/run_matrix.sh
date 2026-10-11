#!/bin/bash
# Every command of the pre-registered re-measurement matrix (PRE_REGISTRATION.md Sec 4).
# Usage: bash outputs/stage1_switch/run_matrix.sh <row> [m11|arm3c]
#        rows: A B C D E H, then F and G last. With no detector named, models/11 runs first,
#        then arm3c. Each run gets its own directory and its stdout is kept beside the result.
# A run whose directory already exists is refused: no row is re-run (PRE_REGISTRATION.md Sec 8).
set -euo pipefail
cd "$(dirname "$0")/../.."

PY=/opt/anaconda3/bin/python3
OUT=outputs/stage1_switch
HEAD=models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth
LESION=models/16_lever_b_pooled/lever_b_pooled_yolo11l-2/weights/best.pt
CX_LIST=$OUT/cariesxrays_val_1200.csv
DETS="${2:-m11 arm3c}"

det_path() {
  case "$1" in
    m11)   echo models/11_yolo_seg_tufts_r1/best.pt ;;
    arm3c) echo models/15_detector_multicorpus_leverA/arm3c_best.pt ;;
    *)     echo "unknown detector $1" >&2; exit 1 ;;
  esac
}

# run <directory name> <command ...>: appends --out <directory>, keeps stdout beside the result.
run() {
  local d="$OUT/$1"; shift
  if [ -e "$d" ]; then echo "REFUSED: $d exists; a row is not re-run" >&2; exit 1; fi
  mkdir -p "$d"
  echo "[$(date '+%H:%M:%S')] $d"
  "$@" --out "$d" > "$d/stdout.log" 2>&1
}

# lesion_args <decision>: the lesion model, only for the decision that uses it.
lesion_args() { [ "$1" = lesion-detector ] && echo "--lesion-model $LESION" || true; }

row_A() {  # Tufts numbering, 143 images
  for det in $DETS; do
    run "A_tufts_$det" $PY scripts/eval/validate_fdi_assignment_tufts.py \
      --weights "$(det_path $det)" --head-weights $HEAD
  done
}

row_B() {  # DENTEX numbering, 164 images
  for det in $DETS; do
    run "B_dentex_$det" $PY scripts/eval/validate_fdi_assignment.py --method head \
      --weights "$(det_path $det)" --head-weights $HEAD
  done
}

row_C() {  # DENTEX lesion agreement, 164 images, 479 lesions
  for det in $DETS; do
    for dec in pipeline constant-molars lesion-detector all-teeth; do
      run "C_dentex_${dec}_$det" $PY scripts/eval/lesion_localization.py \
        --detector "$(det_path $det)" --decision $dec $(lesion_args $dec)
    done
  done
}

row_D() {  # DENTEX FDI-set F1 and latency; run with nothing else on the machine
  for det in $DETS; do
    for method in gate lesion-detector; do
      run "D_fdiset_${method}_$det" $PY scripts/eval/c1_vlm_baseline.py --arm pipeline \
        --caries-method $method --detector "$(det_path $det)"
    done
  done
}

row_E() {  # CariesXrays, the 1,200 held-out images, 2,815 lesions
  if [ ! -e "$CX_LIST" ]; then   # the frozen list, rebuilt from the three saved outputs of 4 Sep
    $PY - "$CX_LIST" <<'EOF'
import json, sys
from pathlib import Path
saved = ["outputs/cariesxrays_external_lever_b_b_single/cariesxrays_external_pipeline.json",
         "outputs/cariesxrays_external_lever_b_b_single/cariesxrays_external_constant-molars.json",
         "outputs/cariesxrays_external_lever_b_b_pooled/cariesxrays_external_lesion-detector.json"]
stems = [sorted(Path(r["image"]).stem for r in json.loads(Path(f).read_text())["per_image"])
         for f in saved]
assert stems[0] == stems[1] == stems[2] and len(set(stems[0])) == 1200, "saved lists disagree"
Path(sys.argv[1]).write_text("stem,split\n" + "".join(f"{s},val\n" for s in stems[0]))
EOF
  fi
  for det in $DETS; do
    for dec in pipeline constant-molars lesion-detector; do
      run "E_cariesxrays_${dec}_$det" $PY scripts/eval/cariesxrays_external.py \
        --detector "$(det_path $det)" --decision $dec $(lesion_args $dec) \
        --manifest "$CX_LIST" --manifest-split val
    done
  done
}

row_F() {  # Ningxia caries, 337 images, 1,013 lesions. LOCKED cohort: last, and once.
  for det in $DETS; do
    for dec in pipeline constant-molars lesion-detector; do
      run "F_ningxia_caries_${dec}_$det" $PY scripts/eval/ningxia_external.py \
        --categories dental_caries --detector "$(det_path $det)" --fdi-head $HEAD \
        --decision $dec $(lesion_args $dec) --tag "stage1_switch_$det"
    done
  done
}

row_G() {  # Ningxia Stage-4 flag rate. LOCKED cohort: last, and once.
  for det in $DETS; do
    run "G_ningxia_stage4_$det" $PY scripts/eval/ningxia_external.py \
      --categories periodontitis --detector "$(det_path $det)" --fdi-head $HEAD \
      --tag "stage1_switch_$det"
  done
}

row_H() {  # parameter counts; --out is a file here, so not through run()
  for det in $DETS; do
    local d="$OUT/H_params_$det"
    if [ -e "$d" ]; then echo "REFUSED: $d exists" >&2; exit 1; fi
    mkdir -p "$d"
    $PY scripts/count_model_params.py --stage1 "$(det_path $det)" \
      --out "$d/param_counts.json" > "$d/stdout.log" 2>&1
  done
}

"row_$1"
echo "[$(date '+%H:%M:%S')] row $1 done ($DETS)"
