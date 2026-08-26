"""
Universal to FDI tooth numbering conversion.

Final clinical report requires FDI (international standard).

**Tufts does NOT use standard Universal numbering — its labels are left-right MIRRORED.**
Use `tufts_title_to_fdi()` for Tufts data, never `universal_to_fdi()` directly; the reasoning
and the evidence are in that function's docstring. (An earlier version of this docstring said
"Tufts uses Universal numbering (1-32)" and that conversion "is applied at the YOLO output
stage". Both were wrong: the numbering is mirrored, and nothing in the pipeline calls this
module — it is used by the dataset builders and the tests.)

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


# ---------------------------------------------------------------------------
# Tufts-specific: the dataset's numbering is mirrored across the midline
# ---------------------------------------------------------------------------

_MIRROR_QUADRANT = {1: 2, 2: 1, 3: 4, 4: 3}


def mirror_fdi_quadrant(fdi_number):
    """Reflect an FDI code across the midline: quadrant 1<->2 (upper), 3<->4 (lower).

    Position (the second digit, distance from the midline) is unchanged — a mirror maps a
    tooth onto its contralateral partner, which sits at the same position in the other
    quadrant. Returns None for anything that is not a valid permanent FDI code.
    """
    try:
        q, p = divmod(int(fdi_number), 10)
    except (TypeError, ValueError):
        return None
    if q not in _MIRROR_QUADRANT or not 1 <= p <= 8:
        return None
    return _MIRROR_QUADRANT[q] * 10 + p


def tufts_title_to_fdi(title):
    """Tufts `teeth_bbox.json` "title" -> FDI code, correcting the dataset's mirrored sides.

    Returns None for deciduous letters (A-T) and for anything unrecognised.

    WHY THE MIRROR — measured three independent ways, not assumed
    -------------------------------------------------------------
    Tufts titles are Universal-*looking* ('1'-'32'), and their within-arch ordering is
    genuinely correct: across all 1,000 images the longest teeth are exactly positions
    6, 11, 22, 27 (the canines) and the shortest, most-often-absent are 1, 16, 17, 32 (the
    third molars). What is inverted is which SIDE of the patient each number denotes.

      1. Lead side-marker. The radiographs carry an "L" marker, and it sits on the viewer's
         right — i.e. these images follow the standard convention (patient's left on the
         viewer's right). Tufts' tooth "1" falls on the viewer's right, putting it on the
         patient's LEFT. Standard Universal "1" is the patient's upper-RIGHT third molar.

      2. Independent model arbiter. The Stage-2 enumeration head is trained on DENTEX, whose
         FDI labels are spatially verified (Q1 mean x=0.400 vs Q2 x=0.606), and has never
         seen Tufts. Over 1,188 IoU>=0.5-matched teeth in 60 Tufts images it agreed with
         Tufts labels 6.1% of the time read directly, and 91.7% read mirrored. The quadrant
         confusion matrix is a clean anti-diagonal (q1->q2, q2->q1, q3->q4, q4->q3).

      3. Control, to prove the arbiter is not itself the mirrored component. The same head,
         detector and matching code on 841 DENTEX teeth: 98.6% direct, 0.7% mirrored — a
         clean diagonal. The head is correct; Tufts is mirrored.

    RESULTS_LOG 2026-08-25h. The detector is unaffected (single-class, emits no numbering),
    and so are the bone-loss models (they use the Tufts title only as an identifier and a
    deciduous flag, never deriving laterality from it).

    Deciduous teeth are deliberately NOT mapped. FDI does define a primary scheme
    (quadrants 5-8), but the Stage-2 head's output space is the 32 permanent codes, so a
    deciduous mapping would be untestable dead code here — and their handedness was not
    verified by the evidence above, which covers permanent teeth only.
    """
    t = str(title).strip()
    if not t.isdigit():
        return None
    return mirror_fdi_quadrant(universal_to_fdi(t))
