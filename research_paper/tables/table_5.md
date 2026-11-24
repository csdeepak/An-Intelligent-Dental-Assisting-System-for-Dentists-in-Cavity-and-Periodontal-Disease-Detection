**Table 5.** Tooth-level caries prediction on 164 DENTEX images (477 carious teeth), micro-averaged. P: precision; R: recall; Matched: F1 minus that of a constant naming as many codes (pp).

| System | P | R | F1 | Matched |
|---|---|---|---|---|
| Pipeline, lesion detector | 0.439 | 0.574 | 0.498 | +22.35 |
| Pipeline, crop classifier | 0.237 | 0.765 | 0.362 | +5.50 |
| Constant (image-blind) | 0.218 | 0.600 | 0.320 | — |
| Constant on detected molars | 0.259 | 0.581 | 0.358 | — |
| Qwen2.5-VL-32B, 0-shot | 0.250 | 0.243 | 0.246 | +0.39 |
| Qwen2.5-VL-7B, 0-shot | 0.248 | 0.107 | 0.149 | +1.39 |
| Oracle constant (test-fit) | 0.245 | 0.505 | 0.330 | — |
