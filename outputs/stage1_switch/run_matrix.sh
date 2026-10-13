#!/bin/bash
# Every command of the pre-registered re-measurement matrix (PRE_REGISTRATION.md Sec 4).
# Usage: bash outputs/stage1_switch/run_matrix.sh <row> [m11|arm3c]
#        rows: A B C D E H, then F and G last; I J K M (Amendment 2); P (Amendment 3; N and O
#        are analyses in stage1_switch_intervals.py and run nothing). With no detector named, models/11 runs first,
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

# ---- Amendment 2: rows for rebuilding the manuscript on the current front end -------------
# Row L of that amendment is analysis only (stage1_switch_intervals.py) and has no command.

row_I() {  # numbering failure taxonomy, from the rows row B saved. No inference.
  for det in $DETS; do
    run "I_taxonomy_$det" $PY scripts/eval/stage2_failure_taxonomy.py \
      --rows "$OUT/B_dentex_$det/stage2_rows_head.json" --control "$OUT/none" \
      --fig "$OUT/I_taxonomy_$det"
  done
}

row_J() {  # coverage-accuracy for numbering, from the same saved rows. Threshold 0.30, not swept.
  for det in $DETS; do
    run "J_coverage_$det" $PY scripts/eval/c4_coverage_accuracy.py \
      --rows "$OUT/B_dentex_$det/stage2_rows_head.json" --fig "$OUT/J_coverage_$det"
  done
}

row_K() {  # Stage-4 flags on the 164 DENTEX images, through the pipeline as shipped. CPU.
  for det in $DETS; do
    local d="$OUT/K_dentex_stage4_$det"
    if [ -e "$d" ]; then echo "REFUSED: $d exists" >&2; exit 1; fi
    mkdir -p "$d"
    echo "[$(date '+%H:%M:%S')] $d"
    $PY - "$(det_path $det)" "$d/dentex_stage4.json" > "$d/stdout.log" 2>&1 <<'PYEOF'
import json, sys
from pathlib import Path
import cv2, torch
sys.path[:0] = [".", "scripts/eval"]
from c1_vlm_baseline import DEF_DISEASE, load_gt
from scripts.run_inference import file_sha256, load_models, run_pipeline
det = Path(sys.argv[1]).resolve()
models, device, paths = load_models(detector=det, device=torch.device("cpu"))
rows = []
for stem in sorted(load_gt(DEF_DISEASE)):            # the 164 leak-free images
    img = cv2.imread(str(DEF_DISEASE / "input" / f"{stem}.png"), cv2.IMREAD_COLOR)
    s = run_pipeline(img, models, device, paths, image_label=stem, verbose=False)["summary"]
    rows.append({"image": stem, "teeth_detected": s["teeth_detected"],
                 "stage4_flagged": s["bone_loss_positive"], "caries_positive": s["caries_positive"]})
Path(sys.argv[2]).write_text(json.dumps(
    {"detector": sys.argv[1], "detector_sha256": file_sha256(str(det)), "device": "cpu",
     "n_images": len(rows), "per_image": rows}, indent=2) + "\n")
print(len(rows), "images;", sum(r["stage4_flagged"] for r in rows), "of",
      sum(r["teeth_detected"] for r in rows), "detected teeth flagged by Stage 4")
PYEOF
  done
}

row_M() {  # Tufts test box mAP in the detector's own label frame: Control B, then arm3c. CPU.
  for w in controlB arm3c; do
    local d="$OUT/M_tufts_map_$w"
    if [ -e "$d" ]; then echo "REFUSED: $d exists" >&2; exit 1; fi
    mkdir -p "$d"
    echo "[$(date '+%H:%M:%S')] $d"
    $PY - "models/15_detector_multicorpus_leverA/${w}_best.pt" "$d" > "$d/stdout.log" 2>&1 <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
from ultralytics import YOLO
w, out = Path(sys.argv[1]), Path(sys.argv[2])
# the call scripts/yolo/train_multicorpus_detector_v2.py made after each arm trained, on CPU
m = YOLO(str(w)).val(data="data/detector_multicorpus_v2/data.yaml", split="test", device="cpu",
                     project=str(out.resolve()), name="val", exist_ok=True, plots=False)
res = {"weights": str(w), "sha256": hashlib.sha256(w.read_bytes()).hexdigest(),
       "split": "test_tufts.txt", "device": "cpu",
       "box_map50": float(m.box.map50), "box_map50_95": float(m.box.map),
       "precision": float(m.box.mp), "recall": float(m.box.mr)}
(out / "tufts_test_map.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res, indent=2))
PYEOF
  done
}

row_P() {  # UFBA-425 numbering (Amendment 3). Gates P2 and P3 first; then each image treatment,
           # models/11 before arm3c. Gate P1 (the scorer still reproduces row A) is run by hand first.
  local g="$OUT/P_ufba_gates"
  if [ ! -e "$g" ]; then
    mkdir -p "$g"
    echo "[$(date '+%H:%M:%S')] $g"
    $PY - "$g" > "$g/stdout.log" 2>&1 <<'PYEOF'
import hashlib, json, sys
from pathlib import Path
import cv2
import numpy as np
out, ufba = Path(sys.argv[1]), Path("data/ufba425")

# P2 -- handedness, from the labels alone (as corrected by Amendment 4): quadrants 1,4 left of
# 2,3 and quadrants 1,2 above 3,4, each compared only where both of its sides have a tooth.
ok = bad = undefined = 0
for f in sorted((ufba / "boundinng_boxes").glob("*.txt")):
    q = {1: [], 2: [], 3: [], 4: []}
    for line in f.read_text().splitlines():
        p = line.split()
        if len(p) < 5:
            continue
        v = [float(x) for x in p[1:]]
        cx, cy = (v[0], v[1]) if len(v) == 4 else (np.mean(v[0::2]), np.mean(v[1::2]))
        q[int(p[0]) // 8 + 1].append((cx, cy))
    m = lambda qs, i: np.mean([c[i] for k in qs for c in q[k]]) if any(q[k] for k in qs) else None
    tests = [a < b for a, b in ((m((1, 4), 0), m((2, 3), 0)), (m((1, 2), 1), m((3, 4), 1)))
             if a is not None and b is not None]
    if not tests:
        undefined += 1
    else:
        ok, bad = ok + all(tests), bad + (not all(tests))
p2 = {"images": ok + bad + undefined, "define_a_comparison": ok + bad, "consistent": ok,
      "define_none": undefined, "share": ok / (ok + bad), "pass": ok / (ok + bad) >= 0.99}

# P3 -- leakage: MD5 and a 256-bit difference hash against every training-side corpus on disk.
def dhash(path):
    g = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if g is None:
        return None
    s = cv2.resize(g, (17, 16), interpolation=cv2.INTER_AREA)
    return np.packbits(s[:, 1:] > s[:, :-1])                      # 256 bits -> 32 bytes

def files(root):
    return sorted(p for p in Path(root).rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))

corpora = {"Tufts radiographs": "_repo_archive/datasets_workspace/Radiographs",
           "DENTEX, every release folder": Path.home() / "Downloads/Capstone/DENTEX",
           "Kaggle dual": "data/kaggle_dual/images1"}
mine = files(ufba / "numbering_xrays")
my_md5 = {hashlib.md5(p.read_bytes()).hexdigest(): p.stem for p in mine}
my_hash = np.array([dhash(p) for p in mine])
POP = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint16)
excluded, p3 = set(), {}
for name, root in corpora.items():
    theirs = files(root)
    same = {my_md5[h] for h in (hashlib.md5(p.read_bytes()).hexdigest() for p in theirs) if h in my_md5}
    th = np.array([h for h in (dhash(p) for p in theirs) if h is not None])
    dist = POP[my_hash[:, None, :] ^ th[None, :, :]].sum(-1)        # 425 x N Hamming distances
    near = {mine[i].stem for i in np.where(dist.min(1) <= 10)[0]}
    p3[name] = {"images": len(theirs), "byte_identical": len(same), "within_hamming_10": len(near),
                "min_hamming_of_256": int(dist.min())}
    excluded |= same | near
res = {"P2_handedness": p2, "P3_leakage": p3, "excluded": sorted(excluded),
       "pass": bool(p2["pass"] and len(excluded) <= 20)}
(out / "gates.json").write_text(json.dumps(res, indent=2) + "\n")
(out / "excluded.json").write_text(json.dumps(sorted(excluded)) + "\n")
print(json.dumps(res, indent=2))
sys.exit(0 if res["pass"] else 1)
PYEOF
  fi
  $PY -c "import json, sys; sys.exit(0 if json.load(open('$g/gates.json'))['pass'] else 1)"
  # 0 = the 640x640 export as distributed (primary). 1.76664 = 1991:1127, a sensitivity analysis.
  for treat in asis:0 wide:1.76664; do
    for det in $DETS; do
      run "P_ufba_${treat%%:*}_$det" $PY scripts/eval/validate_fdi_assignment_tufts.py \
        --ufba data/ufba425 --exclude "$g/excluded.json" --aspect "${treat##*:}" \
        --weights "$(det_path $det)" --head-weights $HEAD
    done
  done
}

"row_$1"
echo "[$(date '+%H:%M:%S')] row $1 done ($DETS)"
