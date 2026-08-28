# 2026-08-28 — C1 hardened: scale, few-shot, and the constant that beats the pipeline

Second work block of 28 Aug; the first is `2026-08-28-c4-abstention.md`.

## Session goal

Harden C1 against the obvious reviewer objection — one model, zero-shot, one prompt — by adding a
larger model, few-shot prompting, and a reproducibility re-run.

## What was done

- Extended `scripts/eval/c1_vlm_baseline.py` with `--shots` (few-shot), `--max-pixels`,
  `--out-name`, and `--arm control` (the blank/noise control, previously an ad-hoc script uploaded
  to the box, now version-controlled with its **verdict logic corrected**).
- Ran six arms on an H100 80GB (EU1), 59 min, **₹285.20**. Instance destroyed.
- Added `heldout_constant()` and `best_constant()` to `scripts/eval/c1_constant_baseline.py`.
- 19 new tests (`test_c1_fewshot.py`, `test_c1_constant.py`); suite **92 → 109**.

**Results** (164 leak-free images, one scorer):

| System | P | R | F1 |
|---|---|---|---|
| Held-out constant `{16,17,26,27,36,37,46,47}` — image never read | 0.218 | 0.600 | **0.320** |
| Our six-stage pipeline | 0.235 | 0.390 | **0.294** |
| Qwen2.5-VL-32B zero-shot | 0.250 | 0.243 | **0.246** |
| Qwen2.5-VL-7B zero-shot | 0.248 | 0.107 | **0.149** |
| Qwen2.5-VL-7B 2-shot / 4-shot | | | **0.066 / 0.034** |

## Decisions made

- **Reported the constant that beats us, prominently, rather than burying it.** A fixed list of the
  eight first/second molars — fitted on held-out images, frozen — scores 0.320 against our 0.294.
  CLAUDE.md rule 1 forbids softening a limitation; this one reframes C1, so it went into
  `transfer.md` §1, `PAPER_MATERIAL.md` §8.22 and `model_metrics.md`, not just the log.
- **Distinguished the oracle constant from the deployable one.** The greedy best constant fitted on
  the *test* set reaches 0.330 but is not claimable. Fitting on the 78 excluded images and freezing
  gives 0.320 and is honest. Both are reported, the oracle labelled as such everywhere.
- **Narrowed 27 Aug's claim instead of restating it.** "The VLM does not beat a constant guess" was
  measured on the 7B against a *hand-picked* constant (0.204). The 32B clears that constant. The
  claim now names the model and the constant, or it is not falsifiable.
- **Drew few-shot exemplars only from the 86 leakage-excluded images**, asserted at runtime and in
  tests. A few-shot arm sampling the evaluation set would post a large fake gain that looks exactly
  like a real one.
- **Included a zero-shot re-run** rather than assuming 27 Aug's number held. It reproduced
  (0.149 vs 0.143) across different hardware *and* a transformers major version — worth the ~3 min
  it cost, because the alternative was a paper number nobody had ever re-measured.
- **Recorded the transformers version in every arm file.** 27 Aug did not, which is the only reason
  the re-run was ambiguous rather than conclusive.

## Open questions

- **Is tooth-level FDI-set F1 the right C1 metric at all?** It is base-rate dominated. A metric that
  credits *localisation* rather than set membership — or restricting to non-molar teeth, where the
  constant has no purchase — would test perception more honestly. Not yet designed.
- **Does the pipeline beat the constant on any metric?** It wins on precision (0.235 vs 0.218) and
  predicts far fewer teeth, but no framing has been worked out that is both favourable and honest.
- **Would a medical VLM (MedGemma) behave differently?** Gated on HuggingFace — accepting the
  licence is an account-owner action, so it was not attempted.
- The 32B declines a blank image (`NONE`) but not noise. Whether that is real perception or a
  brightness heuristic is untested.

## Next steps

1. **Write the paper draft** — still the critical path, now with a materially different C1 section.
2. Decide the C1 metric question above before that section is written.
3. Optional: Stage-2 head v3 on the Kaggle third FDI corpus (~₹313 remains).
4. The four compliance blockers remain untouched account-owner actions.

## Process notes for the next GPU session

- **Load the `jarvislabs` skill first.** Probing availability by looping `jl create` *created* an
  instance (₹14.26 wasted). `jl gpus` is the read-only query.
- **`jl exec <id> -- sh -lc '...'`** — without `--` the whole string is treated as one command name.
- **Git-Bash rewrites remote paths** (`/home/c1` → `C:/Git/home/c1`) and MSYS `$(pwd)` yields paths
  `jl.exe` rejects. Use PowerShell, or `MSYS_NO_PATHCONV=1`.
- **`jl run` accepted a job, created its directory, then died without starting it.** SSH + `nohup`
  was reliable; `jl run` was not.
- **A bulk upload reported success while silently dropping one 2.6 KB file**, which killed phase 1
  on launch. Verify every required input *on the box* before starting a billed run.
- The pytorch template ships **transformers 4.46.2, which cannot load Qwen2.5-VL**; upgrading lands
  on 5.x where `torch_dtype=` became `dtype=`. The loader now handles both.
