"""
Universal to FDI tooth numbering conversion.

Tufts uses Universal numbering (1-32).
Final clinical report requires FDI (international standard).
Conversion is applied at the YOLO output stage.

Universal 1-8:   Upper right (FDI 18-11)
Universal 9-16:  Upper left  (FDI 21-28)
Universal 17-24: Lower left  (FDI 38-37-36-35-34-33-43-44)
Universal 25-32: Lower right (FDI 45-46-47-48-31-32-33-34)
"""

UNIVERSAL_TO_FDI = {
    "1": 18, "2": 17, "3": 16, "4": 15,
    "5": 14, "6": 13, "7": 12, "8": 11,
    "9": 21, "10": 22, "11": 23, "12": 24,
    "13": 25, "14": 26, "15": 27, "16": 28,
    "17": 38, "18": 37, "19": 36, "20": 35,
    "21": 34, "22": 33, "23": 43, "24": 44,
    "25": 45, "26": 46, "27": 47, "28": 48,
    "29": 31, "30": 32, "31": 33, "32": 34,
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
