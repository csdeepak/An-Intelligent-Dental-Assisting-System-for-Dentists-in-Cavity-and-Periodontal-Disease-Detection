"""
Week 2 Day 1: Convert Tufts annotations → YOLO format

Input:
  - Radiographs_rotated/{image_id}.jpg   (portrait 840*1615)
  - Segmentation/teeth_bbox.json         (portrait-coordinate annotations)
  - outputs/eda_tufts/split_v1.csv       (frozen 70/15/15 split)

Output:
  - dataset/images/{train,val,test}/*.jpg
  - dataset/labels/{train,val,test}/*.txt  (YOLO format: "0 cx cy w h" normalized)
  - dataset/data.yaml                       (YOLO dataset config)

Single-class detection: all teeth labeled as class 0 ("tooth").
Primary (letter) teeth INCLUDED — we want to detect all teeth, not just permanent.
Degenerate boxes (w<2 or h<2) DROPPED.
Empty images SKIPPED (no labels to write).

Usage:
    python convert_tufts_to_yolo.py
"""

import json
import shutil
from pathlib import Path
from collections import Counter

import pandas as pd
from tqdm import tqdm
from PIL import Image


# =============================================================================
# CONFIGURATION — edit paths to your local setup
# =============================================================================

TUFTS_ROOT = Path("/Users/chennupatigunadeep/Downloads/Capstone/DataSets")
IMG_SRC_DIR = TUFTS_ROOT / "Radiographs_rotated"
BBOX_JSON = TUFTS_ROOT / "Segmentation" / "teeth_bbox.json"
SPLIT_CSV = Path("outputs/eda_tufts/split_v1.csv")

# Output — will be created fresh
DATASET_DIR = Path("dataset")

# Known image dimensions (verified in Week 1)
IMG_WIDTH = 840
IMG_HEIGHT = 1615


def norm_image_key(image_id: str) -> str:
    """Stable join key for split CSV ↔ JSON External ID.

    The split CSV contains names like `1.JPG`, while the Tufts JSON uses
    `External ID` like `1.jpg`. Keying by the numeric stem (`1`) avoids
    case/extension mismatches.
    """
    return Path(str(image_id)).stem.strip()


# =============================================================================
# STEP 1: Validate inputs
# =============================================================================

def validate_inputs():
    assert TUFTS_ROOT.exists(), f"TUFTS_ROOT missing: {TUFTS_ROOT}"
    assert IMG_SRC_DIR.exists(), f"Rotated images missing: {IMG_SRC_DIR}"
    assert BBOX_JSON.exists(), f"Annotations missing: {BBOX_JSON}"
    assert SPLIT_CSV.exists(), f"Split CSV missing: {SPLIT_CSV}"
    
    n_imgs = len(list(IMG_SRC_DIR.glob("*.jpg"))) + len(list(IMG_SRC_DIR.glob("*.JPG")))
    assert n_imgs >= 990, f"Expected ~1000 images, found {n_imgs}"
    
    # Spot-check image dimensions
    sample = next(IMG_SRC_DIR.glob("*.jpg"), None) or next(IMG_SRC_DIR.glob("*.JPG"))
    img = Image.open(sample)
    assert (img.width, img.height) == (IMG_WIDTH, IMG_HEIGHT), (
        f"Unexpected image size {img.width}x{img.height}, expected {IMG_WIDTH}x{IMG_HEIGHT}"
    )
    print(f"Inputs validated: {n_imgs} images, {IMG_WIDTH}x{IMG_HEIGHT}")


# =============================================================================
# STEP 2: Build YOLO dataset structure
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
# STEP 3: Parse annotations into per-image dict
# =============================================================================

def parse_annotations():
    """
    Returns: dict {image_id: [(cx, cy, w, h), ...]}
    Coordinates are NORMALIZED (0-1), in YOLO format.
    Degenerate boxes dropped. All tooth types included.
    """
    with open(BBOX_JSON) as f:
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
        yolo_boxes = []
        
        for obj in objects:
            bbox = obj.get("bounding box")
            if not bbox or len(bbox) != 4:
                stats["malformed"] += 1
                continue
            
            x1, y1, x2, y2 = bbox
            w = x2 - x1
            h = y2 - y1
            
            # Drop degenerate.
            # NOTE (21 Aug 2026): this filter fires on exactly 66 objects across the 1,000
            # Tufts images, and every one of them is a REAL tooth whose "bounding box" field
            # is corrupt (1x1 / 1x2 px) while its polygon in teeth_polygon.json is intact and
            # full-size. So this dataset is missing 66 annotated teeth (47 train / 13 val /
            # 6 test). Left in place ON PURPOSE: changing it would invalidate the frozen
            # canonical detector (tooth-detector-a100-1024-v1.0) that was trained on this
            # exact output, which docs/research/T0.6_detector_reconciliation.md §1 exists to
            # protect. convert_tufts_to_yolo_seg.py keeps those 66; see T0.6 §3.5 for the
            # full analysis and the reasoning behind the asymmetry.
            if w < 2 or h < 2:
                stats["degenerate"] += 1
                continue
            
            # Clip to image bounds (safety)
            x1 = max(0, min(x1, IMG_WIDTH))
            x2 = max(0, min(x2, IMG_WIDTH))
            y1 = max(0, min(y1, IMG_HEIGHT))
            y2 = max(0, min(y2, IMG_HEIGHT))
            
            # Recompute after clipping
            w = x2 - x1
            h = y2 - y1
            if w < 2 or h < 2:
                stats["degenerate_after_clip"] += 1
                continue
            
            # YOLO format: normalized center + size
            cx = (x1 + x2) / 2 / IMG_WIDTH
            cy = (y1 + y2) / 2 / IMG_HEIGHT
            nw = w / IMG_WIDTH
            nh = h / IMG_HEIGHT
            
            # Sanity: all values must be in (0, 1]
            if not (0 < cx < 1 and 0 < cy < 1 and 0 < nw <= 1 and 0 < nh <= 1):
                stats["out_of_bounds"] += 1
                continue
            
            yolo_boxes.append((cx, cy, nw, nh))
            stats["kept"] += 1
        
        per_image[image_key] = yolo_boxes
    
    print(f"\nAnnotation parsing stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  Images processed: {len(per_image)}")
    return per_image


# =============================================================================
# STEP 4: Copy images + write YOLO label files per split
# =============================================================================

def find_image(image_id):
    """Locate the image file, trying common extensions."""
    stem = Path(image_id).stem
    for ext in [".jpg", ".JPG", ".png", ".PNG", ".jpeg", ".JPEG"]:
        p = IMG_SRC_DIR / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def write_split(split_df, per_image_boxes):
    """Copy images and write labels for each split."""
    split_stats = Counter()
    
    for split in ["train", "val", "test"]:
        subset = split_df[split_df["split"] == split]
        print(f"\nProcessing {split}: {len(subset)} images")
        
        for _, row in tqdm(subset.iterrows(), total=len(subset)):
            image_id = row["filename"]
            image_key = norm_image_key(image_id)
            
            # Find the actual image file
            src_img = find_image(image_id)
            if src_img is None:
                split_stats[f"{split}_image_not_found"] += 1
                continue
            
            # Copy image
            dst_img = DATASET_DIR / "images" / split / image_id
            shutil.copy2(src_img, dst_img)
            
            # Write label file (same stem, .txt extension)
            label_path = DATASET_DIR / "labels" / split / (Path(image_id).stem + ".txt")
            
            boxes = per_image_boxes.get(image_key, [])
            if len(boxes) == 0:
                # Empty label file is valid in YOLO — image has no objects
                label_path.write_text("")
                split_stats[f"{split}_empty_label"] += 1
            else:
                lines = [f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}" for cx, cy, w, h in boxes]
                label_path.write_text("\n".join(lines) + "\n")
                split_stats[f"{split}_labeled"] += 1
                split_stats[f"{split}_total_boxes"] += len(boxes)
    
    print("\nSplit statistics:")
    for k, v in sorted(split_stats.items()):
        print(f"  {k}: {v}")


# =============================================================================
# STEP 5: Write YOLO data.yaml
# =============================================================================

def write_data_yaml():
    yaml_content = f"""# Tufts Dental Database — YOLO config
# Single-class tooth detection
# Generated by convert_tufts_to_yolo.py

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
        
        # Count labels (non-empty lines)
        total_boxes = 0
        for lbl in lbl_dir.glob("*.txt"):
            content = lbl.read_text().strip()
            if content:
                total_boxes += len(content.split("\n"))
        
        print(f"  {split:5s}: {n_imgs} images, {n_lbls} label files, {total_boxes} total boxes")
    
    # Quick sanity on one label file
    sample_lbl = next((DATASET_DIR / "labels" / "train").glob("*.txt"), None)
    if sample_lbl and sample_lbl.read_text().strip():
        lines = sample_lbl.read_text().strip().split("\n")
        print(f"\n  Sample label ({sample_lbl.name}):")
        for line in lines[:3]:
            parts = line.split()
            cls, cx, cy, w, h = parts
            print(f"    class={cls}, cx={cx}, cy={cy}, w={w}, h={h}")
            # All values should be in [0, 1]
            assert 0 <= float(cx) <= 1 and 0 <= float(cy) <= 1, f"Bad coords: {line}"
            assert 0 < float(w) <= 1 and 0 < float(h) <= 1, f"Bad dims: {line}"
        print(f"  [...] {len(lines)} total boxes in this file")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("Tufts → YOLO Conversion")
    print("=" * 60)
    
    validate_inputs()
    build_dataset_dirs()
    
    per_image_boxes = parse_annotations()
    
    split_df = pd.read_csv(SPLIT_CSV)
    print(f"\nSplit CSV loaded: {len(split_df)} images")
    print(split_df["split"].value_counts())
    
    write_split(split_df, per_image_boxes)
    write_data_yaml()
    verify_output()
    
    print("\n" + "=" * 60)
    print("CONVERSION COMPLETE")
    print("=" * 60)
    print(f"\nDataset ready at: {DATASET_DIR.resolve()}")
    print(f"Next step: run train_yolo.py")


if __name__ == "__main__":
    main()
