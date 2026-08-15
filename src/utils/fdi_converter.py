"""
Universal to FDI tooth numbering conversion.

Tufts uses Universal numbering (1-32).
Final clinical report requires FDI (international standard).
Conversion is applied at the YOLO output stage.

Universal numbering runs clockwise from the upper-right third molar: 1-16 across the
maxilla (right to left), then 17-32 across the mandible (left to right). FDI encodes
quadrant in the first digit (1 upper-right, 2 upper-left, 3 lower-left, 4 lower-right)
and distance from the midline in the second (1 central incisor ... 8 third molar).

Universal 1-8:   Upper right (FDI 18-17-16-15-14-13-12-11)
Universal 9-16:  Upper left  (FDI 21-22-23-24-25-26-27-28)
Universal 17-24: Lower left  (FDI 38-37-36-35-34-33-32-31)
Universal 25-32: Lower right (FDI 41-42-43-44-45-46-47-48)
"""

UNIVERSAL_TO_FDI = {
    "1": 18, "2": 17, "3": 16, "4": 15,
    "5": 14, "6": 13, "7": 12, "8": 11,
    "9": 21, "10": 22, "11": 23, "12": 24,
    "13": 25, "14": 26, "15": 27, "16": 28,
    "17": 38, "18": 37, "19": 36, "20": 35,
    "21": 34, "22": 33, "23": 32, "24": 31,
    "25": 41, "26": 42, "27": 43, "28": 44,
    "29": 45, "30": 46, "31": 47, "32": 48,
}

FDI_TO_UNIVERSAL = {v: k for k, v in UNIVERSAL_TO_FDI.items()}


def universal_to_fdi(tooth_id):
    """Convert Universal tooth number to FDI."""
    return UNIVERSAL_TO_FDI.get(str(tooth_id), None)


def fdi_to_universal(fdi_number):
    """Convert FDI tooth number to Universal."""
    return FDI_TO_UNIVERSAL.get(int(fdi_number), None)


def is_deciduous(tooth_id):
    """Check if tooth ID is deciduous (A-T)."""
    return str(tooth_id).strip() in set("ABCDEFGHIJKLMNOPQRST")
