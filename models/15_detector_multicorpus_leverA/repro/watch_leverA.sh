#!/bin/bash
# Poll the Lever A box via /home/box_status.sh; exit (wake the session) on done / fail / crash / timeout.
IP=151.185.34.31
SSH="ssh -o StrictHostKeyChecking=no -o ConnectTimeout=25 -o ServerAliveInterval=15"
DIR=/private/tmp/claude-501/-Users-chennupatigunadeep-Downloads-Capstone-Deepak-impleentation-An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection/70f38f7e-f121-45e5-b32b-5e7ea3ae349c/scratchpad
STATUS=$DIR/watch_leverA.status
HIST=$DIR/watch_leverA.history
MAX=70

miss=0
for i in $(seq 1 $MAX); do
  S=$($SSH root@$IP "bash /home/box_status.sh" 2>&1)
  ts=$(date +%H:%M)
  { echo "=== poll $i  $ts ==="; echo "$S"; } > "$STATUS"
  { echo "--- $ts (poll $i) ---"; echo "$S"; } >> "$HIST"

  if echo "$S" | grep -q "all_finished=1"; then echo "DONE: all three arms finished" >> "$STATUS"; exit 0; fi
  if echo "$S" | grep -qE "any_failed=[1-9]"; then echo "FAIL: an arm reported FAILED" >> "$STATUS"; exit 3; fi
  if echo "$S" | grep -q "alive=0"; then
    miss=$((miss+1))
    [ $miss -ge 2 ] && { echo "CRASH: no training process for 2 polls, not finished" >> "$STATUS"; exit 4; }
  else
    miss=0
  fi
  sleep 420
done
echo "TIMEOUT: watcher hit its cap" >> "$STATUS"
exit 5
