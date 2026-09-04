# Lever A Guard-2 — GT box overlay panels (Phase 0, 4 Sep 2026)

Two representative panels from `models/15_detector_multicorpus_leverA/repro/diagnostics/gt_overlay.py`
(full set of 24 is local-only under `data/detector_multicorpus_v2/_check/gt_overlay/`).

| file | what it shows |
|---|---|
| `gt_tufts_1013.jpg` | a Tufts frozen-test panoramic (detector/portrait frame) with its 28 GT tooth boxes — median box area **0.64 % of image** |
| `gt_dentex_train_0.jpg` | a DENTEX `quadrant-enumeration` panoramic with its 30 GT boxes — median box area **1.19 % of image**, heavily overlapping, extending past the tooth into alveolar bone |

**Point:** the per-corpus GT box-size difference from `box_conv.py` (DENTEX boxes ≈ 1.5× Tufts
area) is real and visible. **It is not the cause of the Guard-2 failure** — the trained
multi-corpus arms adapt to it and predict Tufts boxes *closer* to Tufts GT than the Tufts-only
control does (`outputs/lever_A_multicorpus_detector_v2/TUFTS_GUARD2_DIAGNOSIS.md` §1.3, §1.4b;
`RESULTS_LOG` 2026-09-04). Candidate figure for `PAPER_MATERIAL.md` §8.9.
