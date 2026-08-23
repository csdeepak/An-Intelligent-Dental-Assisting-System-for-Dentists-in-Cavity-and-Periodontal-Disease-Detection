# `tests/` — 46 tests, all passing

```bash
python -m pytest tests/ -q
```

No pytest plugins or fixtures are required; every file also runs standalone
(`python tests/test_x.py`) for use on a GPU box with a minimal environment.

| File | Tests | Covers |
|---|---|---|
| `test_crop_generator.py` | 12 | Expanded-bbox geometry, ±15% jitter, mask-aware cropping (R2) |
| `test_fdi_assignment.py` | 11 | Stage-2 positional assignment + every failure mode it must flag |
| `test_fdi_converter.py` | 8 | Universal ↔ FDI table |
| `test_label_assigner.py` | 7 | Pixel-overlap-ratio labelling |
| `test_orientation.py` | 6 | The rotate/un-rotate contract, both directions, against cv2 |
| `test_data_loader.py` | 2 | Tufts JSON parsing/joining |

## Two suites that exist because of real bugs

- **`test_fdi_converter.py`** names the historical Universal→FDI lower-arch defect explicitly —
  the shifted lower arch and the duplicated FDI 33/34 that collapsed the reverse lookup. It
  was open in five documents long after `f8b31f8` closed it.
- **`test_orientation.py`** round-trips **both** rotation directions against cv2 on real
  pixels. The direction was recorded as clockwise until 22 Aug 2026 when it is
  counter-clockwise; CW and CCW differ by 180°, so a visual check could never have caught it
  and the committed rotation script was silently wrong.

Unit tests cannot catch either class of error on their own — both needed an artefact
comparison against ground truth. That is what `scripts/eval/` is for.
