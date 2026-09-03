#!/bin/bash
cd "/Users/chennupatigunadeep/Downloads/Capstone/Deepak impleentation/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection"
PY=/opt/anaconda3/bin/python3
O=outputs/lever_A_multicorpus_detector_v2

nin () {  # $1 label  $2 detector
  echo "=== NINGXIA caries  $1  ($(date +%H:%M)) ==="
  $PY scripts/eval/ningxia_external.py --detector "$2" --categories dental_caries \
      --decision pipeline --tag "leverA_$1" 2>&1 | tail -6
}
cxr () {  # $1 label  $2 detector
  echo "=== CARIESXRAYS 1500  $1  ($(date +%H:%M)) ==="
  $PY scripts/eval/cariesxrays_external.py --detector "$2" --sample 1500 --seed 42 \
      --decision pipeline --tag "leverA_$1" 2>&1 | tail -8
}

nin controlA models/11_yolo_seg_tufts_r1/best.pt
nin arm3c    models/15_detector_multicorpus_leverA/arm3c_best.pt
nin arm4c    models/15_detector_multicorpus_leverA/arm4c_best.pt
cxr controlA models/11_yolo_seg_tufts_r1/best.pt
cxr arm3c    models/15_detector_multicorpus_leverA/arm3c_best.pt
cxr arm4c    models/15_detector_multicorpus_leverA/arm4c_best.pt
echo "=== GUARD 1 ALL DONE  $(date +%H:%M) ==="
