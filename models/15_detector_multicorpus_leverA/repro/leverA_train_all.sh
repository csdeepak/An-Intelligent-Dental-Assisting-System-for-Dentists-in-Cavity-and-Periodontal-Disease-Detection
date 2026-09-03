#!/bin/bash
# Lever A: train Control B -> Arm 3C -> Arm 4C sequentially on this box.
# Run detached:  nohup bash leverA_train_all.sh > /home/leverA_train.log 2>&1 &
set -u
cd /home
export YOLO_CONFIG_DIR=/home/.config/Ultralytics
PY=/root/miniconda3/envs/py3.10/bin/python
LOG=/home/leverA_train.log

echo "=== Lever A training run  $(date -u)  ==="
$PY -c "import torch; p=torch.cuda.get_device_properties(0); print('GPU', p.name, f'{p.total_memory/1e9:.1f} GB')"

for ARM in controlB arm3c arm4c; do
  echo ""
  echo "############################################################"
  echo "### ARM $ARM   start $(date -u)"
  echo "############################################################"
  $PY /home/train_multicorpus_detector_v2.py --arm "$ARM" --data-root /home/detector_multicorpus_v2 \
      --project /home/runs_leverA
  rc=$?
  echo "### ARM $ARM   end $(date -u)   exit=$rc"
  if [ $rc -ne 0 ]; then
    echo "### ARM $ARM FAILED (exit $rc) -- stopping the sequence"
    exit $rc
  fi
done

echo ""
echo "=== ALL THREE ARMS DONE  $(date -u) ==="
echo "--- best.pt sha256 + Guard-2 (Tufts test box mAP@0.5) grep ---"
for ARM in controlB arm3c arm4c; do
  B=/home/runs_leverA/$ARM/weights/best.pt
  [ -f "$B" ] && echo "$ARM  $(sha256sum "$B" | cut -d' ' -f1)"
done
grep -hE "Tufts TEST  box mAP" "$LOG" || true
echo "=== done ==="
