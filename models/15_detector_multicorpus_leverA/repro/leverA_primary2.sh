#!/bin/bash
cd "/Users/chennupatigunadeep/Downloads/Capstone/Deepak impleentation/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection"
PY=/opt/anaconda3/bin/python3
HEAD=models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth
O=outputs/lever_A_multicorpus_detector_v2
run () {  # $1=label  $2=weights
  echo "=== PRIMARY $1  weights=$2  ($(date +%H:%M:%S)) ==="
  $PY scripts/eval/validate_fdi_assignment.py --weights "$2" --method head \
      --head-weights "$HEAD" --out "$O/$1" 2>&1 | grep -E 'enumeration head:|images:|recall\)|of detected\)|end-to-end|mean detections|wrote '
  echo "--- $1 done ---"
}
run controlA models/11_yolo_seg_tufts_r1/best.pt
run arm3c    models/15_detector_multicorpus_leverA/arm3c_best.pt
run arm4c    models/15_detector_multicorpus_leverA/arm4c_best.pt
echo "=== DONE $(date +%H:%M:%S) ==="
sha256sum "$O"/controlA/stage2_rows_head.json "$O"/arm3c/stage2_rows_head.json "$O"/arm4c/stage2_rows_head.json
