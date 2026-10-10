"""As-run record, 11 Oct 2026 -- not a maintained tool.

Produced arm_pipeline_gate_code322f787.json for PRE_REGISTRATION.md Amendment 1.
Setup used (from the repo root; OLD is any empty scratch directory outside the repo):
    git archive 322f787 src scripts configs data/dentex/disease_leaked_images.json | tar -x -C OLD
    ln -s "$PWD/models" OLD/models
    cd OLD && python <this file> OLD <output.json>
"""
import json, sys
from pathlib import Path
OLD = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(OLD)); sys.path.insert(0, str(OLD / "scripts" / "eval"))
import cv2, torch
from scripts.run_inference import load_models, run_pipeline
import scripts.run_inference as ri
assert Path(ri.__file__).resolve().is_relative_to(OLD), ri.__file__
from c1_vlm_baseline import DEF_DISEASE, load_gt
gt = load_gt(DEF_DISEASE)
models, device, paths = load_models(device=torch.device("cpu"))
pred = {}
for i, stem in enumerate(sorted(gt), 1):
    img = cv2.imread(str(DEF_DISEASE / "input" / f"{stem}.png"), cv2.IMREAD_COLOR)
    rep = run_pipeline(img, models, device, paths, image_label=stem, verbose=False)
    pred[stem] = sorted({str(t["fdi"]) for t in rep["teeth"]
                         if t["fdi"] is not None and t["caries"]["finding"] != "no_caries"})
    if i % 40 == 0: print(i, flush=True)
Path(sys.argv[2]).write_text(json.dumps({"code": "322f787", "device": "cpu", "predictions": pred}, indent=1))
print("done", len(pred))
