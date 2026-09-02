# Lever A — status

**Last updated: 2 September 2026.** Data prep done locally; nothing rented yet.

## Done

| step | result |
|---|---|
| Kaggle API token | saved to `.env` (gitignored — new `# Secrets / local env` block in `.gitignore`); `kaggle` CLI 2.2.4 installed into `/opt/anaconda3` |
| Kaggle "dual" corpus | downloaded `zwbzwb12341234/a-dual-labeled-dataset` (553 MB) → `data/kaggle_dual/` (500 img / 2,066 labels; **499 usable** after 1 byte-identical dupe — matches the project's own count). Licence **unstated** — already a project corpus (head v3), so a compliance-track item, not new here. |
| UFBA-425 | downloaded `numbering_xrays` + `boundinng_boxes` from figshare `10.6084/m9.figshare.29827475` → `data/ufba425/` (425 img). **Licence CC BY 4.0** (figshare API). |
| DNS / OdontoAI | **dropped** — both request-gated, not directly downloadable. |
| builder | `scripts/yolo/build_multicorpus_detector_v2_dataset.py` written (adapts Lever 1's, adds Kaggle + UFBA converters, per-corpus balancing, within/cross-corpus MD5 dedup). Dry-run + real build both clean. |
| dataset | `data/detector_multicorpus_v2/` (1.1 GB, gitignored) |

## The built dataset

| corpus | train img | train box | 10% test img | rotated |
|---|---|---|---|---|
| Tufts (frozen split) | 700 | 18,221 | 150 (frozen, box 3,924) | no — in-frame |
| DENTEX `quadrant_enumeration` | 561 | 15,981 | 62 (box 1,794) | CCW |
| Kaggle "dual" | 449 | 11,847 | 50 (box 1,294) | CCW |
| UFBA-425 | 382 | 10,412 | 43 (box 1,172) | CCW |

- **val = Tufts only, 150 img, canonical box count 3,794 reproduced exactly** (build aborts otherwise).
- **test = Tufts frozen 150 (Guard 2)** + per-corpus 10% slices for a reported per-corpus mAP secondary.
- Geometry gate: **42,500 rotated boxes round-tripped, median IoU vs source = 1.0000, PASS.**
- Leakage guard: 164 leak-free DENTEX eval images hashed, **0 refusals**.
- Dedup: 11 byte-identical DENTEX images dropped (Lever 1 did not catch these), 1 Kaggle.
- All 4 corpora eyeballed in `data/detector_multicorpus_v2/_check/` — boxes tight on teeth, correct frame.

## Balanced train lists

- `train.txt` — 2,800 lines, **4 corpora × 700** (Arm 4C, includes UFBA)
- `train_3corpus.txt` — 2,100 lines, **3 corpora × 700** (Arm 3C, the primary — no UFBA)
- `data.yaml` currently points `train: train.txt`; the trainer switches it per arm.

## ⚠️ UFBA-425 aspect distortion

UFBA's only public form is a **square 640×640 Roboflow export** — the panoramic is stretched to
1:1. Measured tooth-box aspect: **median w/h 0.234** vs DENTEX 0.347, Tufts ~0.371 (~35 % narrower).
This is a preprocessing artifact, not scanner diversity. Hence the primary Lever A arm is
**3-corpus** and UFBA is an **additive arm** (pre-reg §4) — reported, adopted over 3C only if it
also passes §5 *and* beats 3C on the primary.

## Next (blocked on the user)

1. **Top up JarvisLabs** (~₹3,500) — balance is ₹560.
2. **Sign off / adjust the acceptance bars** (pre-reg §5) — one review round, then frozen.
3. Then: write `train_multicorpus_detector_v2.py` (adapt Lever 1's), `tar` the dataset + sha256,
   rent an A100, run Control B + Arm 3C + Arm 4C, score against a same-day Control-A re-measure,
   apply the pre-registered verdict, log to `RESULTS_LOG.md`.
