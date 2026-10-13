# -*- coding: utf-8 -*-
"""Count the learnable parameters of every checkpoint Table I of the paper reports.

WHY THIS EXISTS
---------------
`verify_paper_numbers.py` asserts every headline number against a saved artefact.
The three parameter claims were the exception: they were hardcoded literals
carrying the provenance label "torch.load over models/*/", which was aspirational
rather than true. Re-deriving them on 4 Sep 2026 showed the label had been hiding a
real inconsistency -- the detector row (27.62 M) counted parameters only, while the
four ResNet18 rows (11.19/11.20 M) counted parameters *plus* batch-norm buffers.
The two conventions differ by ~0.01 M per row, so nothing downstream was wrong, but
no single rule reproduced the table, which is exactly the drift the verifier exists
to catch.

This script fixes that by writing the counts to an artefact under one stated rule:
**learnable parameters only** (`nn.Module.parameters()`, or the state-dict tensors
minus `running_mean` / `running_var` / `num_batches_tracked`). The verifier then
reads that artefact like every other claim, and stays torch-free so it runs on a
machine with no deep-learning stack.

Stage 3a has two interchangeable implementations since the Lever B adoption
(RESULTS_LOG 2026-09-04h): the whole-image lesion detector is the default and the
per-crop gate is retained as a variant. Both are counted, and both totals emitted.

Run: py -3.13 scripts/count_model_params.py
Writes: outputs/param_counts/param_counts.json
"""
import argparse
import json
import sys
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "param_counts" / "param_counts.json"

# Kept in the pipeline's own stage order. Paths mirror the DEF_* defaults in
# scripts/run_inference.py -- if a default checkpoint changes there, change it here.
CHECKPOINTS = [
    ("stage1_detector",       "models/15_detector_multicorpus_leverA/arm3c_best.pt"),
    ("stage2_fdi_head",       "models/10_fdi_head_dentex_tufts_v2/enumeration_head_best.pth"),
    ("stage3a_lesion",        "models/16_lever_b_pooled/lever_b_pooled_yolo11l-2/weights/best.pt"),
    ("stage3a_gate_variant",  "models/09_caries_gate_v3/caries_gate_v3.pth"),
    ("stage3b_caries_sev",    "models/07_caries_cascade/phase2_final_bundle.pth"),
    ("stage4a_bone_gate",     "models/18_bone_loss_radiograph_split/seed42_best.pth"),
    ("stage4b_bone_sev",      "models/04_bone_loss_severity_notebook_models/bone_loss_severity_resnet18_best.pth"),
]

# Buffers, not parameters. Excluded under the stated rule.
_BUFFER_SUFFIXES = ("running_mean", "running_var", "num_batches_tracked")


def count(path: Path) -> int:
    """Learnable parameters in a checkpoint, whether it holds a module or a state dict."""
    obj = torch.load(path, map_location="cpu", weights_only=False)

    # Ultralytics .pt: a pickled nn.Module under "model", with an optional EMA copy.
    # run_inference.py loads these through YOLO(), which prefers the EMA when present,
    # so prefer it here too.
    if isinstance(obj, dict) and isinstance(obj.get("model"), torch.nn.Module):
        module = obj.get("ema") or obj["model"]
        return sum(p.numel() for p in module.parameters())
    if isinstance(obj, torch.nn.Module):
        return sum(p.numel() for p in obj.parameters())

    # Torchvision head: a bare state dict, or a bundle wrapping one alongside metadata.
    state = obj
    if isinstance(state, dict):
        for key in ("model_state_dict", "state_dict", "model"):
            if isinstance(state.get(key), dict):
                state = state[key]
                break
    if not isinstance(state, dict):
        raise TypeError(f"{path}: unrecognised checkpoint of type {type(obj).__name__}")

    tensors = {k: v for k, v in state.items() if torch.is_tensor(v)}
    if not tensors:
        raise TypeError(f"{path}: no tensors found; top-level keys {sorted(state)[:12]}")
    return sum(v.numel() for k, v in tensors.items() if not k.endswith(_BUFFER_SUFFIXES))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage1", default=CHECKPOINTS[0][1],
                    help="count a different Stage-1 detector (path relative to the repo)")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    if args.stage1 != CHECKPOINTS[0][1] and args.out == OUT:
        # param_counts.json is what the manuscript's numbers are asserted against.
        print("a non-default --stage1 needs its own --out; refusing to overwrite", OUT.name)
        return 1
    checkpoints = [("stage1_detector", args.stage1)] + CHECKPOINTS[1:]

    counts, missing = {}, []
    for name, rel in checkpoints:
        path = REPO / rel
        if not path.exists():
            missing.append(rel)
            print(f"MISSING  {name:22s} {rel}")
            continue
        counts[name] = count(path)
        print(f"{name:22s} {counts[name]:>12,}   {counts[name] / 1e6:6.2f} M")

    if missing:
        # A partial artefact would make the verifier assert against a wrong total,
        # which is worse than not writing one. See docs/EXTERNAL_DRIVE.md for the
        # two checkpoints that are Drive-only.
        print(f"\n{len(missing)} checkpoint(s) absent -- refusing to write a partial artefact.")
        return 1

    shared = (counts["stage1_detector"] + counts["stage2_fdi_head"]
              + counts["stage3b_caries_sev"])
    totals = {
        # Stages 1-6, Stage 3a = lesion detector (the pipeline default).
        "total_default": shared + counts["stage3a_lesion"]
                         + counts["stage4a_bone_gate"] + counts["stage4b_bone_sev"],
        # Same, with the retained per-crop gate in slot 3a.
        "total_gate_variant": shared + counts["stage3a_gate_variant"]
                              + counts["stage4a_bone_gate"] + counts["stage4b_bone_sev"],
        # "Caries path" is stages 1, 2, 3a and 3b -- both caries heads, no bone loss.
        "caries_path_default": shared + counts["stage3a_lesion"],
        "caries_path_gate_variant": shared + counts["stage3a_gate_variant"],
    }
    for name, n in totals.items():
        print(f"{name:26s} {n:>12,}   {n / 1e6:6.2f} M")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "rule": "learnable parameters only; batch-norm buffers excluded",
        "checkpoints": dict(checkpoints),
        "params": counts,
        "totals": totals,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
