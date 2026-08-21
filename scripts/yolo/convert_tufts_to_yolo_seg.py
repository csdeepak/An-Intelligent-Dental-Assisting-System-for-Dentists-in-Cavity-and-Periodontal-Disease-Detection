"""
T0.6 / R1: Convert Tufts polygon annotations -> YOLO-seg format

VERIFIED against real data 20 Aug 2026 — teeth_polygon.json (1,000/1,000 records) and all
1,000 raw Tufts radiographs were located (Google Drive) and this script's unmodified logic
was run end-to-end against them (only path constants patched for the local test
environment): 26,005 instances produced across 700/150/150 train/val/test images, zero
crashes, val/test instance counts (3,871 / 3,920) closely matching the historical bbox
conversion's val count (3,794) as a sanity check. The largest-polygon-per-object heuristic
below was visually spot-checked by overlaying converted polygons on 7 real radiographs
(random + hand-picked) — every polygon traced a real tooth outline, no noise/garbage shapes.
Full record: docs/research/T0.6_detector_reconciliation.md §3.

IMPORTANT — the real Radiographs source ships LANDSCAPE (1615x840), not portrait. Run
scripts/yolo/rotate_tufts_radiographs.py first to produce Radiographs_rotated/ (rotation
direction — 90 deg clockwise — was empirically determined and visually verified, see that
script's docstring and the T0.6 doc; do not assume Radiographs_rotated/ already exists).

REMAINING GAP: the test run above used a freshly-generated temporary split, NOT the frozen
outputs/eda_tufts/split_v1.csv referenced below — that file is still missing (searched
exhaustively, not found anywhere). Using a different split than the one the canonical bbox
detector (models/06_yolo_detection_a100_run) was evaluated on breaks direct comparability
of test-set metrics. Locate the original split before running this for the real training
data, or make an explicit, documented decision to accept a new split and note the
comparability caveat everywhere the resulting numbers are reported.

Input:
  - Radiographs_rotated/{image_id}.jpg          (portrait 840x1615 — see rotation note above)
  - Segmentation/teeth_polygon.json             (portrait-coordinate polygon annotations)
  - outputs/eda_tufts/split_v1.csv              (frozen 70/15/15 split — STILL MISSING, see above)

Output:
  - dataset_seg/images/{train,val,test}/*.jpg
  - dataset_seg/labels/{train,val,test}/*.txt   (YOLO-seg format: "0 x1 y1 x2 y2 ... xn yn" normalized)
  - dataset_seg/data.yaml

Single-class instance segmentation: all teeth labeled as class 0 ("tooth"), matching the
single-class bbox detector (scripts/yolo/convert_tufts_to_yolo.py) so results are comparable
class-for-class.

Per teeth_polygon.json's schema, each object's "polygons" field is a LIST of point-lists,
not one polygon. Spot-checking the one record read while writing this script showed one
large primary contour per tooth plus several 1-4 point fragments that look like edge-tracing
noise rather than real disjoint regions (e.g. a tooth split by an overlapping filling).
This converter therefore keeps only the LARGEST-AREA polygon per object (by shoelace formula)
and drops the rest. If real data turns out to have genuinely disjoint tooth regions (visible
in a spot check), this heuristic under-represents those objects and should be revisited to
either keep multiple polygons per instance (YOLO-seg supports this per official Ultralytics
format) or merge fragments.

Usage:
    python convert_tufts_to_yolo_seg.py
"""

import json
import shutil
from pathlib import Path
from collections import Counter

import pandas as pd
from tqdm import tqdm
from PIL import Image


# =============================================================================
# CONFIGURATION — edit paths to your local setup (mirrors convert_tufts_to_yolo.py)
# =============================================================================

TUFTS_ROOT = Path("/Users/chennupatigunadeep/Downloads/Capstone/DataSets")
IMG_SRC_DIR = TUFTS_ROOT / "Radiographs_rotated"
POLY_JSON = TUFTS_ROOT / "Segmentation" / "teeth_polygon.json"
SPLIT_CSV = Path("outputs/eda_tufts/split_v1.csv")

# Output — will be created fresh, kept separate from the bbox dataset/ dir
DATASET_DIR = Path("dataset_seg")

# Known image dimensions (verified in Week 1, same source images as the bbox conversion)
IMG_WIDTH = 840
IMG_HEIGHT = 1615

MIN_POLYGON_POINTS = 3  # fewer than 3 points cannot form a polygon


def norm_image_key(image_id: str) -> str:
    """Stable join key for split CSV <-> JSON External ID. See convert_tufts_to_yolo.py."""
    return Path(str(image_id)).stem.strip()


def polygon_area(points):
    """Shoelace formula, unsigned. points: list of (x, y)."""
    if len(points) < 3:
        return 0.0
    area = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


# =============================================================================
# STEP 1: Validate inputs
# =============================================================================

def validate_inputs():
    assert TUFTS_ROOT.exists(), f"TUFTS_ROOT missing: {TUFTS_ROOT}"
    assert IMG_SRC_DIR.exists(), f"Rotated images missing: {IMG_SRC_DIR}"
    assert POLY_JSON.exists(), (
        f"Polygon annotations missing: {POLY_JSON}. "
        "See docs/research/T0.6_detector_reconciliation.md §3 — re-fetch teeth_polygon.json "
        "from the original Tufts source before running this script."
    )
    assert SPLIT_CSV.exists(), f"Split CSV missing: {SPLIT_CSV}"

    n_imgs = len(list(IMG_SRC_DIR.glob("*.jpg"))) + len(list(IMG_SRC_DIR.glob("*.JPG")))
    assert n_imgs >= 990, f"Expected ~1000 images, found {n_imgs}"

    sample = next(IMG_SRC_DIR.glob("*.jpg"), None) or next(IMG_SRC_DIR.glob("*.JPG"))
    img = Image.open(sample)
    assert (img.width, img.height) == (IMG_WIDTH, IMG_HEIGHT), (
        f"Unexpected image size {img.width}x{img.height}, expected {IMG_WIDTH}x{IMG_HEIGHT}"
    )
    print(f"Inputs validated: {n_imgs} images, {IMG_WIDTH}x{IMG_HEIGHT}")


# =============================================================================
# STEP 2: Build YOLO-seg dataset structure
# =============================================================================

def build_dataset_dirs():
    if DATASET_DIR.exists():
        print(f"Removing existing {DATASET_DIR}/")
        shutil.rmtree(DATASET_DIR)

    for split in ["train", "val", "test"]:
        (DATASET_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATASET_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    print(f"Created {DATASET_DIR}/ with train/val/test subdirs")


# =============================================================================
# STEP 3: Parse polygon annotations into per-image dict
# =============================================================================

def parse_annotations():
    """
    Returns: dict {image_id: [[(x, y), ...], ...]}  -- one normalized polygon per object.
    Only the largest-area polygon fragment is kept per object (see module docstring).
    Objects whose largest fragment has < MIN_POLYGON_POINTS points are dropped.
    """
    with open(POLY_JSON) as f:
        raw = json.load(f)

    per_image = {}
    stats = Counter()

    for entry in raw:
        image_id = entry.get("External ID")
        if not image_id:
            stats["missing_id"] += 1
            continue

        image_key = norm_image_key(image_id)

        objects = entry.get("Label", {}).get("objects", [])
        polygons_norm = []

        for obj in objects:
            fragments = obj.get("polygons") or []
            if not fragments:
                stats["no_polygons"] += 1
                continue

            # Keep only the largest-area fragment per object (see module docstring).
            best_fragment = max(fragments, key=lambda pts: polygon_area([tuple(p) for p in pts]))
            points = [(p[0], p[1]) for p in best_fragment]

            if len(points) < MIN_POLYGON_POINTS:
                stats["too_few_points"] += 1
                continue

            # Clip to image bounds, normalize
            norm_points = []
            for x, y in points:
                x = max(0, min(x, IMG_WIDTH))
                y = max(0, min(y, IMG_HEIGHT))
                norm_points.append((x / IMG_WIDTH, y / IMG_HEIGHT))

            polygons_norm.append(norm_points)
            stats["kept"] += 1

        per_image[image_key] = polygons_norm

    print("\nAnnotation parsing stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  Images processed: {len(per_image)}")
    return per_image


# =============================================================================
# STEP 4: Copy images + write YOLO-seg label files per split
# =============================================================================

def find_image(image_id):
    stem = Path(image_id).stem
    for ext in [".jpg", ".JPG", ".png", ".PNG", ".jpeg", ".JPEG"]:
        p = IMG_SRC_DIR / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def write_split(split_df, per_image_polygons):
    split_stats = Counter()

    for split in ["train", "val", "test"]:
        subset = split_df[split_df["split"] == split]
        print(f"\nProcessing {split}: {len(subset)} images")

        for _, row in tqdm(subset.iterrows(), total=len(subset)):
            image_id = row["filename"]
            image_key = norm_image_key(image_id)

            src_img = find_image(image_id)
            if src_img is None:
                split_stats[f"{split}_image_not_found"] += 1
                continue

            dst_img = DATASET_DIR / "images" / split / image_id
            shutil.copy2(src_img, dst_img)

            label_path = DATASET_DIR / "labels" / split / (Path(image_id).stem + ".txt")

            polygons = per_image_polygons.get(image_key, [])
            if len(polygons) == 0:
                label_path.write_text("")
                split_stats[f"{split}_empty_label"] += 1
            else:
                lines = []
                for poly in polygons:
                    coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in poly)
                    lines.append(f"0 {coords}")
                label_path.write_text("\n".join(lines) + "\n")
                split_stats[f"{split}_labeled"] += 1
                split_stats[f"{split}_total_instances"] += len(polygons)

    print("\nSplit statistics:")
    for k, v in sorted(split_stats.items()):
        print(f"  {k}: {v}")


# =============================================================================
# STEP 5: Write YOLO-seg data.yaml
# =============================================================================

def write_data_yaml():
    yaml_content = f"""# Tufts Dental Database — YOLO-seg config
# Single-class tooth instance segmentation
# Generated by convert_tufts_to_yolo_seg.py

path: {DATASET_DIR.resolve()}
train: images/train
val: images/val
test: images/test

nc: 1
names: ['tooth']
"""
    (DATASET_DIR / "data.yaml").write_text(yaml_content)
    print(f"\nWrote {DATASET_DIR / 'data.yaml'}")


# =============================================================================
# STEP 6: Final verification
# =============================================================================

def verify_output():
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    for split in ["train", "val", "test"]:
        img_dir = DATASET_DIR / "images" / split
        lbl_dir = DATASET_DIR / "labels" / split

        n_imgs = len(list(img_dir.glob("*")))
        n_lbls = len(list(lbl_dir.glob("*.txt")))

        total_instances = 0
        for lbl in lbl_dir.glob("*.txt"):
            content = lbl.read_text().strip()
            if content:
                total_instances += len(content.split("\n"))

        print(f"  {split:5s}: {n_imgs} images, {n_lbls} label files, {total_instances} total instances")

    sample_lbl = next((DATASET_DIR / "labels" / "train").glob("*.txt"), None)
    if sample_lbl and sample_lbl.read_text().strip():
        lines = sample_lbl.read_text().strip().split("\n")
        print(f"\n  Sample label ({sample_lbl.name}):")
        first_line = lines[0].split()
        cls = first_line[0]
        n_points = (len(first_line) - 1) // 2
        print(f"    class={cls}, {n_points} polygon points")
        coords = [float(v) for v in first_line[1:]]
        assert all(0 <= c <= 1 for c in coords), f"Bad normalized coords: {lines[0][:100]}"
        print(f"  [...] {len(lines)} total instances in this file")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("Tufts -> YOLO-seg Conversion")
    print("=" * 60)

    validate_inputs()
    build_dataset_dirs()

    per_image_polygons = parse_annotations()

    split_df = pd.read_csv(SPLIT_CSV)
    print(f"\nSplit CSV loaded: {len(split_df)} images")
    print(split_df["split"].value_counts())

    write_split(split_df, per_image_polygons)
    write_data_yaml()
    verify_output()

    print("\n" + "=" * 60)
    print("CONVERSION COMPLETE")
    print("=" * 60)
    print(f"\nDataset ready at: {DATASET_DIR.resolve()}")
    print("Confirm SPLIT_CSV above is the real frozen outputs/eda_tufts/split_v1.csv, not a")
    print("substitute split — see docs/research/T0.6_detector_reconciliation.md §3 if unsure.")
    print("Then run train_yolo_seg.py.")


if __name__ == "__main__":
    main()
