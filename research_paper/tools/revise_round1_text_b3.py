"""Review round 1 (23 Nov 2026), batch 3: the two measured answers (research_paper/audit_runs/
review_round_analyses.json, from tools/detected_constant.py, second run):
 - Reviewer A CRITICAL 1: constant naming the eight molars only where the front end detected them:
   F1 0.358 (P 0.259, R 0.581); crop classifier minus it +0.41 [-2.24, +3.14]; lesion detector
   +13.94 [+9.63, +18.15] (Windows rerun +13.12 [+8.84, +17.36]); naive minus detected -3.86.
 - Reviewer B CRITICAL 1: DENTEX caries polygons cover the tooth: polygon box / tooth box median
   0.907 (IQR 0.814-1.016), IoU median 0.814; 99.6% above half the tooth box.
Asserting replacements. Run from the repo root."""
from pathlib import Path

p = Path("research_paper/paper.md")
s = p.read_text(encoding="utf-8")
R = [
# ---- Abstract
("The system's per-crop caries classifier led it by 4.27 F1 points on development data, but its scores",
 "The system's per-crop caries classifier led it by 4.27 F1 points on development data, but not a constant that names the eight molars only where the front end detected them (+0.41 [-2.24, +3.14]); its scores"),
# ---- III-C: DENTEX annotations are tooth outlines
("$A$ has no negative class.",
 "On DENTEX the released caries annotations outline the affected tooth rather than the lesion — the median annotation's bounding box covers 0.91 of the detected tooth box (IoU 0.81) — so there $A$ is a tooth-level measure; on the external cohorts the lesion annotations are small and $A$ asks only whether a lesion's centre lies on a flagged tooth, never whether a predicted box overlaps the lesion. $A$ has no negative class."),
# ---- V: cohorts and metrics
("leaving 164 scored, of which 148 carry a caries lesion (479 lesions on 477 teeth) {C015}.",
 "leaving 164 scored, of which 148 carry caries (479 caries annotations on 477 teeth; the annotations outline the tooth, Section III-C) {C015}."),
("| DENTEX disease | 164 | 936 labelled teeth; 477 carious; 479 lesions |",
 "| DENTEX disease | 164 | 936 labelled teeth; 477 carious; 479 tooth-level caries outlines |"),
("Lesion agreement (4) matches each expert lesion to a flagged tooth: on DENTEX by greedy intersection over union (IoU) of at least 0.30 with a centroid fallback,",
 "Lesion agreement (4) matches each expert annotation to a flagged tooth: on DENTEX, where annotations outline teeth, by greedy intersection over union (IoU) of at least 0.30 with a centroid fallback,"),
# ---- Table 5 and VI-B
("| Constant (image-blind) | 0.218 | 0.600 | 0.320 | — |",
 "| Constant (image-blind) | 0.218 | 0.600 | 0.320 | — |\n| Constant on detected molars | 0.259 | 0.581 | 0.358 | — |"),
("The crop-classifier pipeline leads the constant by +4.27 points [+1.58, +7.05] while naming 1,537 teeth to its 1,312, at barely higher precision (0.237 against 0.218), as Section III-D implies for a classifier that leans on the prior {C020}.",
 "The crop-classifier pipeline leads the constant by +4.27 points [+1.58, +7.05] while naming 1,537 teeth to its 1,312, at barely higher precision (0.237 against 0.218), as Section III-D implies for a classifier that leans on the prior {C020}. The constant, however, names its molars even where a tooth is missing, which the pipeline cannot do. Restricted to the molars our front end detected and numbered, the constant names 1,069 codes and reaches F1 0.358 (+3.86 points [+2.83, +4.90] over the unrestricted one), and the crop classifier's lead over it is +0.41 [-2.24, +3.14]: not separable {C044}."),
("The lesion-detector pipeline leads by +17.80 [+13.48, +22.02] and is the only system whose precision clearly exceeds the constant's (0.439), naming 624 codes, 43.9% of them carious {C021}.",
 "The lesion-detector pipeline leads by +17.80 [+13.48, +22.02], and by +13.94 [+9.63, +18.15] over the restricted constant, and is the only system whose precision clearly exceeds the constant's (0.439), naming 624 codes, 43.9% of them carious {C021}. A rerun of the shipped pipeline on a second machine flagged different codes on 12 of the 164 images (F1 0.490 against 0.498; +13.12 [+8.84, +17.36] over the restricted constant) {C044}."),
("None of this is yet evidence of perception: the front end trained on this corpus {L001}.",
 "Because DENTEX annotations outline whole teeth, the lesion detector, whose DENTEX training boxes are of the same kind, is scored here at the tooth level. None of this is yet evidence of perception: the front end trained on this corpus {L001}."),
# ---- Figure 7 caption and VI-D wording (DENTEX annotations)
("(a) test_120: all seven lesions found, 33 and 34 also flagged; the constant covers four of the seven without reading the image. (b) test_0 (Figure 4): two of three found, 48 missed. (c) test_110: none of four found (32, 33, 34, 46 missed; 16, 24, 26, 36, 37 flagged).",
 "(a) test_120: all seven annotated carious teeth found, 33 and 34 also flagged; the constant covers four of the seven without reading the image. (b) test_0 (Figure 4): two of three found, 48 missed. (c) test_110: none of four found (32, 33, 34, 46 missed; 16, 24, 26, 36, 37 flagged)."),
("the scored image with the most lesions all found, a typical image, and the one with the most lesions none found.",
 "the scored image with the most annotated carious teeth all found, a typical image, and the one with the most of them none found."),
# ---- VII RQ1 and Table 8
("so a favourable tooth-level figure on development data is weak evidence of perception {C007}.",
 "so a favourable tooth-level figure on development data is weak evidence of perception; on development data the crop classifier's F1 lead does not survive a constant restricted to detected teeth {C007}."),
# ---- IX
("our pipeline sat above, level with and below it on three cohorts,",
 "with the crop classifier, our pipeline was level with it on development data once the constant was restricted to detected teeth, level with it on four external sites and below it on a third cohort,"),
]
for a, b in R:
    assert a in s, a[:90]
    s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("batch 3 applied:", len(R))
