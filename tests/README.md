# `tests/` — 65 tests, all passing

```bash
python -m pytest tests/ -q
```

No pytest plugins or fixtures are required; every file also runs standalone
(`python tests/test_x.py`) for use on a GPU box with a minimal environment.

| File | Tests | Covers |
|---|---|---|
| `test_classifiers.py` | 14 | **The three crop conventions and the class orders** — Stages 3/4. Added with R4 (24 Aug) |
| `test_crop_generator.py` | 12 | Expanded-bbox geometry, ±15% jitter, mask-aware cropping (R2) |
| `test_fdi_assignment.py` | 11 | Stage-2 positional assignment + every failure mode it must flag |
| `test_fdi_converter.py` | 13 | Universal ↔ FDI table, **and the mirrored Tufts numbering** |
| `test_label_assigner.py` | 7 | Pixel-overlap-ratio labelling |
| `test_orientation.py` | 6 | The rotate/un-rotate contract, both directions, against cv2 |
| `test_data_loader.py` | 2 | Tufts JSON parsing/joining |

## Three suites that exist because of real bugs

- **`test_fdi_converter.py`** names the historical Universal→FDI lower-arch defect explicitly —
  the shifted lower arch and the duplicated FDI 33/34 that collapsed the reverse lookup. It
  was open in five documents long after `f8b31f8` closed it. Since 25 Aug it also pins
  `tufts_title_to_fdi`: Tufts' numbering is left-right **mirrored**, so its "1" is FDI 28, not
  18 (RESULTS_LOG 2026-08-25h). Reading those titles as plain Universal would train the
  enumeration head on side-swapped labels — silently, with no error anywhere.
- **`test_orientation.py`** round-trips **both** rotation directions against cv2 on real
  pixels. The direction was recorded as clockwise until 22 Aug 2026 when it is
  counter-clockwise; CW and CCW differ by 180°, so a visual check could never have caught it
  and the committed rotation script was silently wrong.

- **`test_classifiers.py`** guards the two failure modes that produce *no error at all*: a
  crossed crop convention (the three stages use 1.0×, 1.5×/1.5× and 1.5×/2.0× — feed a model
  the wrong one and the tensor shape is identical, the values plausible, the output confidently
  wrong) and an inverted `class_to_idx` (which would report every healthy tooth as diseased and
  still look like a working pipeline). It asserts the tight crop reproduces the raw detector
  box, that the bone-loss crop is exactly 1.5×/2.0×, and that **the two branches never produce
  the same crop**.

Unit tests cannot catch any of these on their own — all needed an artefact comparison against
ground truth. That is what `scripts/eval/` is for, and `scripts/eval/verify_invariants.py` in
particular re-checks the facts the documentation depends on.
