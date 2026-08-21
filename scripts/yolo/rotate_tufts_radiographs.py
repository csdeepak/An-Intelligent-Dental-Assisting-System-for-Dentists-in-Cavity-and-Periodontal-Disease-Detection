"""
Rebuild Radiographs_rotated/ from the raw Tufts Radiographs/ folder.

Both convert_tufts_to_yolo.py and convert_tufts_to_yolo_seg.py assume
Radiographs_rotated/{image_id}.jpg already exists, portrait 840x1615 -- but the
Tufts source (Google Drive: MyDrive/Capstone/tufts/ZIP/Radiographs/Radiographs/)
only ships raw landscape 1615x840 images. This rotation step existed at some
point (hence "_rotated" in the name everyone's scripts assume) but was never
itself captured as code anywhere in this repo or its archive -- it had become
tribal knowledge, then just missing knowledge.

Rotation direction (90 deg CLOCKWISE, raw -> portrait) was NOT assumed; it was
determined empirically on 20 Aug 2026 by rotating a sample image (image "1")
both directions, cropping both at several real tooth bounding boxes from
teeth_bbox.json, and visually confirming which rotation produces coherent tooth
anatomy at those coordinates. Confirmed again, more thoroughly, by overlaying
teeth_polygon.json polygons (see convert_tufts_to_yolo_seg.py) on several
CW-rotated images and visually checking that every polygon traces a real tooth
outline -- see docs/research/T0.6_detector_reconciliation.md for the record and
the overlay images this was checked against.

Usage:
    python rotate_tufts_radiographs.py
"""

from pathlib import Path

from PIL import Image
from tqdm import tqdm

# CONFIGURATION — edit to your local setup, matching convert_tufts_to_yolo.py's convention
TUFTS_ROOT = Path("/Users/chennupatigunadeep/Downloads/Capstone/DataSets")
RAW_DIR = TUFTS_ROOT / "Radiographs" / "Radiographs"
OUT_DIR = TUFTS_ROOT / "Radiographs_rotated"

EXPECTED_RAW_SIZE = (1615, 840)   # landscape, as shipped
EXPECTED_ROTATED_SIZE = (840, 1615)  # portrait, what every conversion script expects


def main():
    assert RAW_DIR.exists(), f"Raw radiographs missing: {RAW_DIR}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(
        p for p in RAW_DIR.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    assert len(files) >= 990, f"Expected ~1000 raw radiographs, found {len(files)}"

    sample = Image.open(files[0])
    assert sample.size == EXPECTED_RAW_SIZE, (
        f"Unexpected raw size {sample.size}, expected {EXPECTED_RAW_SIZE} — "
        "if this trips, the rotation direction / target size below may need re-deriving, "
        "not just re-applying blindly."
    )

    ok = 0
    for src in tqdm(files, desc="Rotating"):
        img = Image.open(src)
        # ROTATE_270 = 270 deg counter-clockwise = 90 deg clockwise
        rotated = img.transpose(Image.ROTATE_270)
        assert rotated.size == EXPECTED_ROTATED_SIZE, (
            f"{src.name}: rotated size {rotated.size} != expected {EXPECTED_ROTATED_SIZE}"
        )
        dst = OUT_DIR / src.name
        rotated.save(dst)
        ok += 1

    print(f"Rotated {ok}/{len(files)} images -> {OUT_DIR}")
    print("Spot-check a few against teeth_bbox.json / teeth_polygon.json annotations")
    print("before trusting this for a training run — see the module docstring.")


if __name__ == "__main__":
    main()
