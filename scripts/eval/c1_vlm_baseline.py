#!/usr/bin/env python
"""
C1 — specialist pipeline vs a general-purpose VLM, tooth-level, on the same leak-free set.

THE QUESTION (MASTER_PLAN §R6)
------------------------------
"Does a small specialist pipeline hold up against a general-purpose VLM on subtle radiolucent
pathology." R6 leaves the model choice to W5 deliberately; this script fixes everything *else*
so that choice is the only variable.

WHY TOOTH-LEVEL AND NOT IMAGE-LEVEL -- measured before designing, not assumed
-----------------------------------------------------------------------------
The obvious framing, "does this radiograph show caries?", is **degenerate on this data**:
**148 of the 164 leak-free DENTEX images (90.2%) contain at least one caries polygon**, so a
model that answers "yes" every time scores 90.2% accuracy, and specificity would rest on 16
images. That comparison could not distinguish a good model from a broken one.

So the task here is **"which teeth, by FDI code, are carious?"** -- 477 affected teeth across
148 images. Both arms produce a *set of FDI codes per image* and are scored identically:

  per-image precision / recall / F1 over the predicted vs ground-truth FDI set, micro-averaged
  over images, plus the count of images where the set matches exactly.

This is the same question §8.11's lesion-localisation metric asks, at the granularity both a
VLM and this pipeline can actually answer.

TWO ARMS, ONE SCORER
--------------------
    --arm pipeline   runs OUR six-stage pipeline. CPU-only, no GPU, no rental.
    --arm vlm        runs an open-weight VLM via transformers. This is the arm that needs a GPU.

Running them through one scorer is the point: any difference is the model, not the metric.

FAIRNESS NOTES, because a rigged baseline is worse than no baseline
--------------------------------------------------------------------
* The VLM is given the FDI numbering system in the prompt and asked for codes, so it is not
  penalised for not knowing the notation.
* It is told teeth may be absent, so it is not penalised for a sparse arch.
* Its output is parsed permissively (any two-digit 11-48 token counts), so formatting is not
  scored as clinical error.
* Our pipeline gets **no** corresponding help. If anything this favours the VLM, which is the
  right direction for a baseline we are comparing ourselves against.

Usage:
    python scripts/eval/c1_vlm_baseline.py --arm pipeline
    python scripts/eval/c1_vlm_baseline.py --arm vlm --model Qwen/Qwen2.5-VL-7B-Instruct
    python scripts/eval/c1_vlm_baseline.py --score            # compare whatever arms exist
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

DEF_DISEASE = Path.home() / "Downloads" / "Capstone" / "DENTEX" / "disease"
DEF_OUT = REPO_ROOT / "outputs" / "c1_vlm"

PROMPT = (
    "This is a dental panoramic radiograph (OPG).\n"
    "Identify every tooth that shows DENTAL CARIES (tooth decay).\n\n"
    "Answer using FDI two-digit tooth notation, where the first digit is the quadrant "
    "(1 = upper right, 2 = upper left, 3 = lower left, 4 = lower right) and the second digit is "
    "the position from the midline (1 = central incisor ... 8 = third molar). Valid codes are "
    "11-18, 21-28, 31-38 and 41-48.\n\n"
    "Some teeth may be missing; only report teeth that are present and carious.\n"
    "Reply with ONLY a comma-separated list of FDI codes, or the word NONE if no tooth is "
    "carious. Do not explain."
)

FDI_TOKEN = re.compile(r"\b([1-4][1-8])\b")

# DENTEX label format: <finding_id>-<turkish_name>-<FDI>. Defined here rather than imported,
# because scripts/eval/validate_fdi_assignment.py -- where the canonical copy lives -- imports
# cv2 and src.fdi_assignment at module level, which would mean shipping the whole pipeline to a
# GPU box that only needs to read label files. Duplicating a regex is a real drift risk, so
# tests/test_c1_label_re.py asserts this stays identical to the canonical pattern.
LABEL_RE = re.compile(r"^(\d+)-(.+)-(\d+)$")


def parse_fdi(text):
    """Permissive FDI extraction. Formatting is not the thing under test."""
    if text is None:
        return set()
    if re.search(r"\bnone\b", text, re.I) and not FDI_TOKEN.search(text):
        return set()
    return {m.group(1) for m in FDI_TOKEN.finditer(text)}


def load_gt(disease_dir):
    leaked = set(json.loads(
        (REPO_ROOT / "data/dentex/disease_leaked_images.json").read_text())["all_excluded"])
    gt = {}
    for lab in sorted((disease_dir / "label").glob("*.json")):
        stem = lab.stem
        if stem in leaked or f"{stem}.png" in leaked:
            continue
        d = json.loads(lab.read_text(encoding="utf-8"))
        codes = set()
        for s in d.get("shapes", []):
            m = LABEL_RE.match(s["label"])
            if m and m.group(1) == "1":          # curuk == caries
                codes.add(m.group(3))
        gt[stem] = codes
    return gt


def score(gt, pred, name):
    tp = fp = fn = 0
    exact = 0
    per_image = []
    for stem, g in gt.items():
        p = set(pred.get(stem, set()))
        i = len(g & p)
        tp += i; fp += len(p - g); fn += len(g - p)
        exact += int(g == p)
        per_image.append({"image": stem, "n_gt": len(g), "n_pred": len(p), "n_hit": i})
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"arm": name, "n_images": len(gt), "tp": tp, "fp": fp, "fn": fn,
            "precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4),
            "exact_set_match": exact, "exact_set_match_rate": round(exact / len(gt), 4),
            "per_image": per_image}


def run_pipeline_arm(disease_dir, gt, out):
    """OUR pipeline. CPU-only -- this arm costs nothing to run."""
    import cv2
    from scripts.run_inference import load_models, run_pipeline
    # load_models returns (models, device, paths), and run_pipeline takes
    # (img, models, device, paths, image_label=...). Read from run_inference.main() rather
    # than assumed -- an assumed 2-tuple is what failed on the first run.
    models, device, paths = load_models()
    pred, lat = {}, []
    for i, stem in enumerate(sorted(gt), 1):
        ip = disease_dir / "input" / f"{stem}.png"
        img = cv2.imread(str(ip), cv2.IMREAD_COLOR)
        if img is None:
            continue
        t = time.time()
        rep = run_pipeline(img, models, device, paths, image_label=stem, verbose=False)
        lat.append(time.time() - t)
        pred[stem] = {str(t_["fdi"]) for t_ in rep["teeth"]
                      if t_["fdi"] is not None and t_["caries"]["finding"] != "no_caries"}
        if i % 20 == 0:
            print(f"  {i}/{len(gt)}  ({sum(lat)/len(lat):.2f}s/image)", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    (out / "arm_pipeline.json").write_text(json.dumps(
        {"arm": "pipeline", "mean_latency_s": round(sum(lat) / max(len(lat), 1), 3),
         "device": "cpu", "predictions": {k: sorted(v) for k, v in pred.items()}}, indent=2) + "\n")
    return pred, sum(lat) / max(len(lat), 1)


def run_vlm_arm(disease_dir, gt, out, model_id, max_new_tokens, limit):
    """Open-weight VLM, zero-shot. THIS is the arm that needs a GPU."""
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    print(f"loading {model_id} …", flush=True)
    proc = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForImageTextToText.from_pretrained(
        model_id, torch_dtype=torch.bfloat16, device_map="auto")
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  {n_params/1e9:.2f}B parameters", flush=True)

    from PIL import Image
    pred, raw, lat = {}, {}, []
    stems = sorted(gt)[:limit] if limit else sorted(gt)
    for i, stem in enumerate(stems, 1):
        img = Image.open(disease_dir / "input" / f"{stem}.png").convert("RGB")
        msgs = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
        text = proc.apply_chat_template(msgs, add_generation_prompt=True)
        inputs = proc(text=[text], images=[img], return_tensors="pt").to(model.device)
        t = time.time()
        with torch.no_grad():
            gen = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
        lat.append(time.time() - t)
        ans = proc.batch_decode(gen[:, inputs["input_ids"].shape[1]:],
                                skip_special_tokens=True)[0]
        raw[stem] = ans.strip()
        pred[stem] = parse_fdi(ans)
        if i % 20 == 0:
            print(f"  {i}/{len(stems)}  ({sum(lat)/len(lat):.2f}s/image)", flush=True)

    vram = (torch.cuda.max_memory_allocated() / 1e9) if torch.cuda.is_available() else None
    out.mkdir(parents=True, exist_ok=True)
    (out / "arm_vlm.json").write_text(json.dumps(
        {"arm": "vlm", "model": model_id, "params_billion": round(n_params / 1e9, 3),
         "mean_latency_s": round(sum(lat) / max(len(lat), 1), 3),
         "peak_vram_gb": round(vram, 2) if vram else None,
         "prompt": PROMPT, "raw_responses": raw,
         "predictions": {k: sorted(v) for k, v in pred.items()}}, indent=2) + "\n")
    return pred, sum(lat) / max(len(lat), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["pipeline", "vlm"], default=None)
    ap.add_argument("--model", default="Qwen/Qwen2.5-VL-7B-Instruct")
    ap.add_argument("--disease-dir", type=Path, default=DEF_DISEASE)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--score", action="store_true", help="score whatever arm files exist")
    args = ap.parse_args()

    gt = load_gt(args.disease_dir)
    print(f"ground truth: {len(gt)} leak-free images, "
          f"{sum(len(v) for v in gt.values())} affected teeth, "
          f"{sum(1 for v in gt.values() if v)} images with >=1 caries")

    if args.arm == "pipeline":
        pred, lat = run_pipeline_arm(args.disease_dir, gt, args.out)
        print(f"\npipeline arm done, {lat:.2f}s/image")
    elif args.arm == "vlm":
        pred, lat = run_vlm_arm(args.disease_dir, gt, args.out, args.model,
                                args.max_new_tokens, args.limit)
        print(f"\nvlm arm done, {lat:.2f}s/image")

    if args.score or args.arm:
        results = []
        for f, name in ((args.out / "arm_pipeline.json", "pipeline"),
                        (args.out / "arm_vlm.json", "vlm")):
            if f.exists():
                d = json.loads(f.read_text())
                p = {k: set(v) for k, v in d["predictions"].items()}
                r = score({k: v for k, v in gt.items() if k in p}, p, name)
                r["mean_latency_s"] = d.get("mean_latency_s")
                r["model"] = d.get("model", "six-stage specialist pipeline")
                r["params_billion"] = d.get("params_billion")
                r["peak_vram_gb"] = d.get("peak_vram_gb")
                results.append(r)
        if results:
            print(f"\n{'arm':10s}{'images':>8s}{'P':>8s}{'R':>8s}{'F1':>8s}"
                  f"{'exact':>8s}{'s/img':>8s}")
            for r in results:
                print(f"{r['arm']:10s}{r['n_images']:>8d}{r['precision']:>8.3f}"
                      f"{r['recall']:>8.3f}{r['f1']:>8.3f}"
                      f"{r['exact_set_match_rate']:>8.1%}"
                      f"{(r['mean_latency_s'] or 0):>8.2f}")
            (args.out / "c1_comparison.json").write_text(
                json.dumps({"task": "tooth-level caries FDI set prediction",
                            "why_not_image_level": "148/164 (90.2%) of leak-free images contain "
                                                   "caries; an image-level yes/no is degenerate",
                            "results": results}, indent=2) + "\n")
            print(f"\n-> {args.out / 'c1_comparison.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
