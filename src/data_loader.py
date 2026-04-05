"""
Data loading and parsing for Tufts Dental Dataset.

Handles:
  - expert.json parsing (with External ID join key fix)
  - teeth_bbox.json parsing (with [y1,x1,y2,x2] → [x,y,w,h] conversion)
  - Expert mask classification (empty vs annotated)
  - Multi-source data join
"""

import json
import os
from pathlib import Path
from collections import Counter

import cv2
import numpy as np
import pandas as pd


def load_expert_json(path):
    """
    Parse expert.json using External ID as join key.

    BUG FIX: expert.json is a LIST of records, not a dict.
    Join key = Path(item['External ID']).stem
    """
    with open(path, 'r') as f:
        data = json.load(f)

    records = []
    for item in data:
        stem = Path(item["External ID"]).stem
        description = item.get("Description", "")
        records.append({"stem": stem, "description": description})

    df = pd.DataFrame(records)
    return df


def load_bbox_json(path, deciduous_ids=None):
    """
    Parse teeth_bbox.json with CORRECT coordinate conversion.

    BUG FIX: Raw format is [y1, x1, y2, x2] corner points.
    Must convert: x=x1, y=y1, w=x2-x1, h=y2-y1
    """
    if deciduous_ids is None:
        deciduous_ids = set("ABCDEFGHIJKLMNOPQRST")

    with open(path, 'r') as f:
        data = json.load(f)

    records = []
    for item in data:
        stem = Path(item["External ID"]).stem

        if "Label" not in item or "objects" not in item["Label"]:
            continue

        for obj in item["Label"]["objects"]:
            tooth_id = str(obj.get("title", "unknown")).strip()
            bbox_raw = obj.get("bounding box", None)

            if bbox_raw is None or len(bbox_raw) < 4:
                continue

            y1, x1, y2, x2 = bbox_raw
            records.append({
                "stem": stem,
                "tooth_id": tooth_id,
                "x": x1, "y": y1,
                "w": x2 - x1, "h": y2 - y1,
            })

    df = pd.DataFrame(records)
    return df


def classify_expert_masks(mask_dir):
    """
    Load all expert masks. Classify as empty (normal) or annotated (pathological).

    Empty mask (all zeros) = "within normal limits"
    Non-empty mask = pathological finding
    """
    records = []
    mask_files = sorted(Path(mask_dir).glob("*"))

    for mf in mask_files:
        stem = mf.stem
        try:
            mask = cv2.imread(str(mf), cv2.IMREAD_GRAYSCALE)
            if mask is None:
                continue

            is_empty = (mask.max() == 0)
            nonzero_count = int(np.count_nonzero(mask))

            records.append({
                "stem": stem,
                "mask_path": str(mf),
                "mask_empty": is_empty,
                "mask_nonzero_pixels": nonzero_count,
            })
        except Exception as e:
            print(f"  [ERROR] Mask {mf.name}: {e}")

    return pd.DataFrame(records)


def join_all_sources(df_expert, df_bbox, df_masks):
    """
    Join expert labels, bounding boxes, and masks on stem.
    Only keeps images with ALL three annotation types.
    """
    valid_stems = (
        set(df_masks['stem']) &
        set(df_bbox['stem']) &
        set(df_expert['stem'])
    )

    df_bbox_valid = df_bbox[df_bbox['stem'].isin(valid_stems)].copy()

    df_merged = df_bbox_valid.merge(
        df_masks[['stem', 'mask_path', 'mask_empty', 'mask_nonzero_pixels']],
        on='stem', how='inner'
    )
    df_merged = df_merged.merge(
        df_expert[['stem', 'description']],
        on='stem', how='inner'
    )

    return df_merged, valid_stems
