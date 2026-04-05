# Dataset Exploration — Findings & Bugs

## Tufts Dental OPG Dataset

This document records all findings, bugs, and corrections discovered during the Phase 4 data exploration.

---

## Critical Bugs Caught

### Bug 1 — JSON ID Mismatch (SEVERITY: CRITICAL)

**Symptom:** Coverage matrix showed 0 matches for all annotation intersections.

**Root cause:** Code compared filename stems against dictionary keys. But `expert.json` and `teeth_bbox.json` are lists of records, not dictionaries. The actual join key is the `External ID` field nested inside each record.

**Fix:**
```python
# WRONG — treats JSON as dict
for key in data:
    stem = key  # This is an integer index, not a filename

# CORRECT — extract from External ID field
for item in data:
    stem = Path(item["External ID"]).stem
```

**Impact:** Without this fix, no data sources could be joined. The entire pipeline would have zero training samples.

---

### Bug 2 — Bbox Coordinate Format (SEVERITY: CRITICAL)

**Symptom:** All extracted crops were from wrong image locations.

**Root cause:** Assumed standard `[x, y, w, h]` format. Actual format in `teeth_bbox.json` is `[y1, x1, y2, x2]` corner points.

**Fix:**
```python
# Raw: [y1, x1, y2, x2]
y1, x1, y2, x2 = obj["bounding box"]

# Converted: [x, y, w, h]
x = x1
y = y1
w = x2 - x1
h = y2 - y1
```

**Impact:** Every single tooth crop would have been extracted from the wrong location. Models trained on these crops would learn nothing useful.

---

### Bug 3 — Mask Encoding Assumption (SEVERITY: HIGH)

**Symptom:** Planned U-Net severity segmentation architecture was not viable.

**Root cause:** Assumed expert masks encode severity classes (mild=1, moderate=2, severe=3). Actual encoding is per-lesion instance IDs — each blob represents one annotated lesion, and the pixel value is the instance number (not a class label).

**Impact:** Changed the entire architecture decision from U-Net severity segmentation to ResNet18 binary classification. This was the correct pivot.

---

### Bug 4 — PIL DecompressionBombError (SEVERITY: LOW)

**Symptom:** PIL rejected large composite visualization figures.

**Fix:** `PILImage.MAX_IMAGE_PIXELS = None` and resize figures before PDF embedding.

---

### Bug 5 — Font Download 404 (SEVERITY: LOW)

**Symptom:** `wget` for DejaVu font from GitHub returned HTML page, not TTF binary.

**Fix:** `apt-get install fonts-dejavu-core` and copy from system font directory.

---

## Key Dataset Findings

| Finding | Implication |
|---------|-------------|
| All images are exactly 840×1615 px | No resizing needed pre-crop |
| Michelson contrast = 0.999 | High quality, no filtering needed |
| 102 degenerate bboxes (1px dim) | Must filter before training |
| Deciduous teeth (A-T) present | Pediatric cases in dataset |
| Expert masks are instance IDs | Rules out severity segmentation |
| 285 empty masks = normal cases | Perfect label-mask alignment verified |
| Tooth aspect ratio ~0.35 | Asymmetric crop expansion required |
