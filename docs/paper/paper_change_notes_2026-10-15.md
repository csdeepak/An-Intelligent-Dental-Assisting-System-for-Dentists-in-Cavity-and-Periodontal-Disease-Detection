# Paper change notes — 15 Oct 2026 (implementation council)

Notes only: nothing here has been applied to `paper/main.tex`. They came up during the third
publishability council of 15 Oct, which was scoped to the implementation
(`docs/session-memory/2026-10-15b-implementation-council.md`). Each line says whether the chair
verified it against the repo. Apply them in the six-page cut or the 15-page text, each with the
usual checks (`scripts/verify_paper_numbers.py`, tectonic build).

## Corrections — verified

1. **The Stage-3b sentence added on 15 Oct is wrong.** `main.tex` (system overview, "The severity
   head is unchanged---validated on 133 crops and never tested, since no held-out cohort available
   to us labels deep caries"). An image-level DENTEX test split exists — `data/dentex/splits_v2.json`,
   107 images, 84 deep-caries and 311 caries annotations — and the head has never been evaluated
   on it because it predates the split (`models/07_caries_cascade/run_summary.txt:94-96`). Say
   instead: validated on 133 crops, tuned and reported on the same crops, never tested on held-out
   images. The report's limitation text says the same wrong thing
   (`scripts/run_inference.py`, `CARIES_SEVERITY_NOT_EVALUATED`) — that one is an implementation
   fix, listed in the session file.
2. **"1.70 s per image on a laptop CPU with no GPU present"** (`main.tex` ~436). The run forced
   the CPU on an Apple-silicon laptop that has a GPU (`scripts/eval/c1_vlm_baseline.py:203`).
   Say "on the laptop's CPU, with its GPU unused".
3. **State the device per measurement in Reproducibility.** The FDI-set F1 / latency rows and
   CariesXrays forced the CPU (`c1_vlm_baseline.py:203`, `cariesxrays_external.py:156`). The other
   stage1_switch runs logged `device=mps`, which describes the ResNet classifiers only: both YOLO
   models ran on the CPU, because ultralytics uses MPS only when it is named
   (`ultralytics/utils/torch_utils.py:290-322`, installed 8.4.127).
4. **Do not imply that the system screens its input.** It numbers any image it is given: there is
   no check of aspect ratio, orientation or bit depth (`app.py:81-84`, `scripts/run_inference.py`
   ~808). UFBA-425 scores 44.5% end-to-end as a square export and 77.2% widened.
5. **The Docker image is 7 Sep's** and predates the 11–14 Oct defaults; the Dockerfile installs
   `requirements.txt` ranges, not the lock (`Dockerfile:68-69`). Do not say the image reproduces
   the tables until it is rebuilt from the lock.
6. **Code availability statement:** cite `requirements-lock.txt` as the stack behind the Mac
   figures, and note that some Windows figures were made on numpy 2.x while `requirements.txt`
   asks for numpy<2.

## Corrections carried over — found 15 Oct morning, not applied (outside that approved list)

7. "Stages 5 and 6 fuse the per-stage outputs on the FDI key" (`main.tex` ~401): outputs are
   fused per detected box and keyed by FDI afterwards.
8. Patient-level limitation: extend it to Tufts (no patient identifiers; one re-rendered copy found).
9. Abstention per cohort (see 11 below).

## For the authors to decide — verified in part

10. **Selective prediction is shown in-domain only** (`outputs/stage1_switch/J_coverage_arm3c`,
    DENTEX). Any sentence about declining under shift needs the Tufts and UFBA figures.
11. **Under shift the 0.30 gate leaves most wrong codes assessable** — one seat's count from saved
    rows, **not re-verified by the chair**: wrong codes still assessable 53/63 (DENTEX), 631/905
    (Tufts), 1,628/2,561 (UFBA as distributed); declined share 3.9 / 14.4 / 26.3%. If used, recompute
    with a script and log it.
12. **Stage 2 confidence is a ranking score, not a probability** — one seat's in-domain estimate,
    not re-verified: ECE about 0.07 on DENTEX, the 0.9–0.99 bin 0.96 confident and 0.81 accurate.
    Consistent with 15 Oct's change ("numbering's calibration was not measured").
13. The Stage-3b macro-F1 0.77 was tuned and reported on the same 133 crops
    (`models/07…/run_summary.txt:94-95`). The paper does not print it; keep it that way.
14. The Kaggle "dual" licence is still unstated, and the default detector trained on it.
15. The report text quotes UFBA-425 widened at 77.2% (`scripts/run_inference.py` ~203), an aspect
    ratio the paper itself calls unverified.


## Added after the implementation fixes (15 Oct, later)

16. **Test count:** `main.tex` says 204 tests (Reproducibility); the suite now has 213, including
    an end-to-end run of the seven defaults (`RESULTS_LOG` 2026-10-15b).
17. **What the report records** can now be stated in one line if useful: each checkpoint's hash
    (checked before loading), input warnings, and the runtime — library versions, commit, device
    per component (schema `opg-report/1.6`).
