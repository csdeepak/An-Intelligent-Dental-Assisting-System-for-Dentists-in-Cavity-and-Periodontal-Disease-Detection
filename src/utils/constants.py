"""
Shared constants used across the dental AI pipeline.
"""

# ImageNet normalization (must be consistent across ALL models)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Crop dimensions
CROP_SIZE = (224, 224)

# Tufts image dimensions (uniform across dataset)
TUFTS_IMG_HEIGHT = 840
TUFTS_IMG_WIDTH = 1615

# Deciduous tooth IDs
DECIDUOUS_IDS = set("ABCDEFGHIJKLMNOPQRST")

# Bbox coordinate format note:
# Tufts teeth_bbox.json uses [y1, x1, y2, x2] corner points
# Must convert to [x, y, w, h] before use
