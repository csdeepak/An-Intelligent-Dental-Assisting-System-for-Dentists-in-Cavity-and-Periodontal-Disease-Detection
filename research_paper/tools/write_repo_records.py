"""Append/insert the 23 Nov 2026 records required by CLAUDE.md rules 1 and 5, preserving CRLF.
RESULTS_LOG: new entry at the bottom. model_metrics: one paragraph under the FDI-set F1 table.
PAPER_MATERIAL: §7.8 and §8.45 before '## 8.' / '## 9.', and one §9 item. Run once from the repo root."""
from pathlib import Path

def crlf(t):
    return t.replace("\r\n", "\n").replace("\n", "\r\n")

def insert_before(path, marker, block):
    p = Path(path); s = p.read_bytes().decode("utf-8")
    assert "2026-11-23" not in s or path.endswith("RESULTS_LOG.md") is False or True
    m = crlf(marker)
    assert m in s, (path, marker)
    i = s.index(m)
    p.write_bytes((s[:i] + crlf(block) + s[i:]).encode("utf-8"))

LOG = """
## 2026-11-23 — research_paper/: evidence-locked revision, three-perspective review, and two post-hoc DENTEX analyses

- **What was done:** a new, separate manuscript revision in `research_paper/` (the ten-page draft of
  2 Nov extended; `paper/` untouched), built with the RCE skill at `3e4411f` (0.5.0 candidate):
  evidence and claim maps, 52 live-verified citations (10 new, incl. Lipton et al. 2014), three
  reviewer perspectives and an integrity VERIFIER as isolated subagents (all three: major revision;
  GI round 1 blocked on M4–M7), 76 text corrections, and two analyses the reviewers asked for.
- **Dataset / config:** 164 leak-free DENTEX disease images (development; in-domain for the default
  detector); shipped default pipeline (`DEF_*`), CPU, this Windows clone; 10,000 image-cluster
  bootstrap resamples, seed 42. Post hoc; no training, no tuning, no Ningxia or Tufts-test image read.
- **Metrics:**
  - *Image-blind constant restricted to the molars the front end detected and numbered* (FDI-set F1):
    P 0.259, R 0.581, **F1 0.358** (1,069 codes named), against 0.320 for the unrestricted constant
    (restricted − unrestricted +3.86 pp [+2.83, +4.90]).
  - Against it: **crop-classifier pipeline +0.41 pp [−2.24, +3.14], not separable** (was +4.27 against
    the unrestricted constant); **lesion-detector pipeline +13.94 pp [+9.63, +18.15]** (saved run);
    +13.12 [+8.84, +17.36] on this machine's rerun.
  - *Reproducibility:* the rerun's lesion-detector caries codes differ from the saved (macOS) run on
    **12 of 164 images**; F1 0.490 vs 0.498. The first run of the script stopped on this control
    gate (`research_paper/audit_runs/review_round_analyses_run1_gate_failed.json`); the second scores
    both.
  - *DENTEX caries annotations are tooth outlines, not lesion outlines:* polygon bounding box / matched
    detected tooth box, median 0.907 (IQR 0.814–1.016); IoU with the tooth box median 0.814; 99.6% of
    the 479 above 0.5.
- **Key decision or insight:**
  - The crop classifier's development-data F1 lead over the image-blind floor was an artefact of a
    constant that names absent teeth. The lesion detector's lead survives it.
  - DENTEX lesion agreement is a tooth-level measure. "479 lesions" in earlier text is 479 annotated
    carious-tooth outlines.
  - Disclosed in the revision: Ningxia informed the Stage-1 choice (2026-10-11f/g); the Lever B rule
    was committed after its single-corpus arm trained and counted the detector's validation split;
    the theory is post hoc and an application of Lipton et al. 2014.
- **Source:** `research_paper/tools/detected_constant.py`; `research_paper/audit_runs/review_round_analyses.json`,
  `dentex_rerun_windows_2026-11-23.json`; reviews in `research_paper/review/`; gates in
  `research_paper/.rcs/audits/gates/` (gitignored; summarised in `research_paper/integrity_check_report.md`).
- **Follow-ups:** why the two machines differ on 12 images; restate any `main.tex` sentence that says the
  gate pipeline leads the constant on DENTEX F1; author inputs in `research_paper/open_issues.md`.
"""
p = Path("docs/results/RESULTS_LOG.md"); s = p.read_bytes().decode("utf-8")
assert "## 2026-11-23" not in s
if not s.endswith("\r\n"):
    s += "\r\n"
p.write_bytes((s + crlf(LOG)).encode("utf-8"))

insert_before("docs/results/model_metrics.md",
 "**Stage 4 flag, Ningxia periodontitis, 736 images**",
 """**Against an image-blind constant restricted to the molars the front end detected** (`RESULTS_LOG`
2026-11-23; post hoc): that constant scores F1 **0.358** (P 0.259, R 0.581). Gate pipeline − it
+0.41 pp [−2.24, +3.14], **not separable**; default pipeline − it **+13.94 pp [+9.63, +18.15]**. A
Windows rerun of the default flags different codes on 12 of 164 images (F1 0.490 vs 0.498).

""")

insert_before("docs/results/PAPER_MATERIAL.md", "## 8. Known Limitations — write these in the paper",
 """### 7.8 Review of `research_paper/` — two post-hoc analyses (23 Nov 2026)

*`RESULTS_LOG` 2026-11-23. 164 DENTEX images, development data; no training, no tuning.*

| Question | Answer |
|---|---|
| Does the pipeline lead a constant that cannot name absent teeth? | Constant restricted to detected molars: F1 0.358. Crop classifier − it +0.41 [−2.24, +3.14], not separable; lesion detector − it +13.94 [+9.63, +18.15]. |
| Are DENTEX caries annotations lesions or teeth? | Teeth: polygon box / tooth box median 0.907, IoU median 0.814, 99.6% above 0.5. DENTEX agreement is tooth-level. |
| Does the shipped pipeline reproduce across machines? | Not exactly: 12 of 164 images flag different caries codes on Windows than the saved macOS run (F1 0.490 vs 0.498). |

""")

insert_before("docs/results/PAPER_MATERIAL.md", "## 9. What's not yet written — checklist",
 """### 8.45 The development-data F1 lead of the crop classifier, and what DENTEX lesions are

*23 Nov 2026. `RESULTS_LOG` 2026-11-23.*

- **The crop classifier's +4.27 F1 lead on DENTEX does not survive a constant restricted to detected
  teeth** (+0.41 [−2.24, +3.14]). Any sentence saying the gate pipeline beats the constant on DENTEX
  F1 must name the unrestricted constant or be withdrawn. The lesion detector's lead survives.
- **DENTEX caries annotations outline whole teeth.** "Lesion agreement" on DENTEX is tooth-level, and
  "479 lesions" should read "479 annotated carious-tooth outlines".
- **Cross-machine reproducibility is imperfect.** 12 of 164 images differ between the Windows and
  macOS runs of the default pipeline, the second such difference after 0.294 vs 0.300.

---

""")

insert_before("docs/results/PAPER_MATERIAL.md", "\n---\n\n## 10. The manuscript",
 """
- [ ] **(23 Nov 2026)** Carry the `research_paper/` corrections into `paper/main.tex` if it stays the
      maintained manuscript: restricted constant (§8.45), DENTEX tooth-level annotations, Ningxia's role
      in the Stage-1 choice, Lipton et al. 2014 at the selection rule. See `research_paper/reviewer_report.md`.""")
print("records written")
