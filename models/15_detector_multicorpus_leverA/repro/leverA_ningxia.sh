#!/bin/bash
cd "/Users/chennupatigunadeep/Downloads/Capstone/Deepak impleentation/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection"
PY=/opt/anaconda3/bin/python3
n () {
  echo "=== NINGXIA $1  ($(date +%H:%M:%S)) ==="
  $PY scripts/eval/ningxia_external.py --detector "$2" --categories dental_caries \
      --decision pipeline --tag "leverA_$1" --out "outputs/ningxia_leverA_$1" 2>&1 | grep -E "dental_caries|->|category"
}
n controlA models/11_yolo_seg_tufts_r1/best.pt
n arm3c    models/15_detector_multicorpus_leverA/arm3c_best.pt
n arm4c    models/15_detector_multicorpus_leverA/arm4c_best.pt
echo "=== NINGXIA REDONE $(date +%H:%M:%S) ==="
