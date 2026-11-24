"""End to end: the seven default checkpoints, loaded on the CPU, through the whole pipeline (15 Oct 2026).

Until now no test ran `run_pipeline`, so a library upgrade, a rotation slip or a crop regression
could change every report and leave the suite green. Two tests:

- A synthetic, radiograph-shaped image runs wherever the weights are (they are in git): the report
  must be well formed, valid JSON, and identical across two runs.
- A real radiograph runs only where the raw Tufts data is present (it is licensed and never
  committed): its teeth, codes and findings must match a golden summary written on the CPU, boxes
  within 2 px. After a deliberate model change, rewrite it with
  `python tests/test_pipeline_e2e.py --write-golden`.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
ri = pytest.importorskip("scripts.run_inference")
torch = pytest.importorskip("torch")
pytest.importorskip("ultralytics")

GOLDEN_IMAGE = REPO / "_repo_archive/datasets_workspace/Radiographs/1.JPG"   # Tufts training split
GOLDEN = REPO / "tests/golden/tufts_1_cpu.json"


def _load():
    return ri.load_models(device=torch.device("cpu"))


@pytest.fixture(scope="module")
def loaded():
    if not all(p.exists() for p in ri.DEFAULT_SHA256):
        pytest.skip("default checkpoints not on disk")
    return _load()


def _run(loaded, img):
    models, device, paths = loaded
    return ri.run_pipeline(img, models, device, paths, image_label="test", verbose=False)


def _summary(report):
    return {"summary": report["summary"], "warnings": report["image"]["warnings"],
            "teeth": [{"fdi": t["fdi"], "assessable": t["assessable"],
                       "caries": t["caries"]["finding"], "stage4": t["bone_loss"]["finding"],
                       "bbox": [round(v) for v in t["bbox_xyxy"]]} for t in report["teeth"]]}


def test_a_synthetic_radiograph_runs_end_to_end_and_repeats(loaded):
    rng = np.random.default_rng(0)
    grey = np.linspace(40, 200, 1615)[None, :, None] + rng.normal(0, 8, (840, 1615, 1))
    img = np.repeat(grey.clip(0, 255), 3, axis=2).astype(np.uint8)
    a, b = _run(loaded, img), _run(loaded, img)
    assert a["schema_version"] == ri.SCHEMA_VERSION
    assert a["teeth"] == b["teeth"] and a["summary"] == b["summary"]
    json.dumps(a, allow_nan=False)
    rt = a["models"]["runtime"]
    assert rt["classifier_device"] == "cpu" and rt["torch"] == torch.__version__


@pytest.mark.skipif(not GOLDEN_IMAGE.exists(), reason="the raw Tufts radiographs are not on this machine")
def test_a_real_radiograph_matches_its_golden_report(loaded):
    import cv2
    got = _summary(_run(loaded, cv2.imread(str(GOLDEN_IMAGE))))
    want = json.loads(GOLDEN.read_text())
    assert got["summary"] == want["summary"] and got["warnings"] == want["warnings"]
    keys = ("fdi", "assessable", "caries", "stage4")
    assert [{k: t[k] for k in keys} for t in got["teeth"]] == [{k: t[k] for k in keys} for t in want["teeth"]]
    for g, w in zip(got["teeth"], want["teeth"]):
        assert max(abs(x - y) for x, y in zip(g["bbox"], w["bbox"])) <= 2


if __name__ == "__main__" and "--write-golden" in sys.argv:
    import cv2
    GOLDEN.parent.mkdir(exist_ok=True)
    GOLDEN.write_text(json.dumps(_summary(_run(_load(), cv2.imread(str(GOLDEN_IMAGE)))), indent=2) + "\n")
    print("wrote", GOLDEN)
