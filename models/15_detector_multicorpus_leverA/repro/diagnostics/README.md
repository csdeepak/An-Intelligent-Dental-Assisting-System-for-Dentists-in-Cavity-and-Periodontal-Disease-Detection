# Lever A — Guard-2 (Tufts test box mAP) diagnostics

Ran 3 Sep 2026 to answer "why does Tufts test box mAP fall while every other cohort rises?".
Full write-up + council + plan: `outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md`.

All CPU/MPS, ~2 min each on this Mac, no GPU. Run from the repo root with
`/opt/anaconda3/bin/python3` (needs `ultralytics==8.4.127`, and the local
`data/detector_multicorpus_v2/` + `models/15/*.pt`).

| script | what it shows | headline result |
|---|---|---|
| `box_conv.py`      | GT box size / aspect / count per corpus, from the built YOLO labels | DENTEX GT boxes ≈ 1.5× Tufts/Kaggle area, longer along the tooth axis — *looks* like a convention clash |
| `pred_box_size.py` | predicted box area on Tufts test: GT vs Control B vs Arm 3C vs Arm 4C | adding corpora makes Arm 3C's boxes *smaller / closer to Tufts GT* than Control B's — refutes the "blended box too big" idea |
| `iou_diag.py`      | greedy GT-match on Tufts test: TP / FN / FP, matched-pair IoU, pred/GT w+h ratio | Arm 3C vs Control B: **FN +37 %, FP +42 %, matched-IoU unchanged** → the loss is detection/confidence (capacity dilution), not localisation |

Conclusion: no build bug. The Guard-2 failure is the pre-registered "domain dilution", monotonic
in Tufts training share (100 % → 0.724, 52 % → 0.647, 33 % → 0.585), and the metric itself is
capped by box-vs-mask supervision (deployed seg model 0.81 vs any detect model ≤ 0.72).
