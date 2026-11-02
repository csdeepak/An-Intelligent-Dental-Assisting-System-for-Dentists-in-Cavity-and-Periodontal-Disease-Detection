# Review round 1 — analyses from saved data (2 Nov 2026)

These analyses answer items 4, 6, 15 and 16 of the panel roadmap in
`paper/ieee/review/2026-11-02_panel_round1.md`. Their results are logged in `docs/results/RESULTS_LOG.md`
entry 2026-11-02d. All four are post hoc and none was pre-registered. No model was trained or tuned,
and Ningxia was not read.

| Item | Script | Output |
|---|---|---|
| 4 — HKSJ beside DerSimonian–Laird, τ² interval | `scripts/eval/ningxia_random_effects_hksj.py` | `outputs/stage1_switch/F_ningxia_random_effects_hksj.json` (beside the DL file it extends; that file is untouched) |
| 15 — stability of the fitted constant | `scripts/eval/constant_stability_and_curve.py` | `constant_stability_and_curve.json` → `stability` |
| 16 — image-blind operating curve, and the matched-volume comparison | same script | same file → `operating_curve_*`, `matched_volume` |
| 6 — DENTEX near-duplicate check | `scripts/eval/dentex_near_duplicates.py` | `dentex_near_duplicates.json` |

## Item 6: visual inspection (manual, recorded here because no script can produce it)

`dentex_near_duplicates.json` → `candidates_for_inspection` lists the 20 scored images whose nearest
DENTEX neighbour is closer than usual. A candidate has pHash distance ≤ 6 or dHash distance ≤ 4.
Unrelated radiographs reach pHash distance 8 at the 0.01th percentile of all scored-to-pool pairs.

Each candidate was viewed beside its pHash neighbour and its dHash neighbour, 40 pairs in total, on
2 Nov 2026. The montages were made in the session scratchpad and not kept, because they contain
DENTEX pixels.

**None of the 40 pairs is the same radiograph.** Every pair differs in its restorations (crowns,
fillings, bridges, a post) or in which teeth are missing. Global shape alone makes panoramic images
close under both hashes.

**Positive control.** The 86 MD5-identical images all come out at distance 0 under both hashes. All
86 are already in `data/dentex/disease_leaked_images.json`, and no MD5-identical image is missing
from it.

**Limit.** The check finds copies of one radiograph: re-encoded, resized or lightly cropped. It
cannot find a second radiograph of the same patient taken on another day.

## Item 1 (Ningxia per-tooth-type comparison): not run

The saved Ningxia outputs (`outputs/stage1_switch/F_ningxia_caries_*_arm3c/ningxia_external.json`)
hold per-image counts only, with no per-tooth codes or flags. The comparison therefore needs a
re-run of the frozen pipeline on the raw images, inference only. Those images are at
`D:\nangxia_dataset` (Windows, drive not attached on 2 Nov) and
`~/Downloads/Capstone/ningxia_local/` (macOS).
