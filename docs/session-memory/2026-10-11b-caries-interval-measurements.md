# 2026-10-11b — Three pre-registered measurements for the caries tables

**Session goal:** do items 2–5 of the implementation phase (`transfer.md` §3): freeze a
pre-registration, then measure an interval on the headline F1 gap, Lever B per hospital, and the
adopted lesion detector on the Table I metric.

Run on the macOS clone (`/opt/anaconda3/bin/python3`, torch 2.2.0, ultralytics 8.4.127, CPU).
Nothing was trained or tuned. No GPU.

## What was done

1. **Read the scorer and bootstrap code first** — `c1_vlm_baseline.py`, `bootstrap_ci.py`,
   `lever_b_bootstrap.py` — and found a trap: `c1_vlm_baseline.py --arm pipeline` called
   `run_pipeline` with its defaults and wrote `arm_pipeline.json`. Since the lesion detector
   became the default on 4 Sep, a bare re-run would have overwritten the published gate file
   (the source of the 0.294) with a different system's predictions.
2. **Wrote the pre-registration** `outputs/caries_intervals/PRE_REGISTRATION.md` and a
   `.gitignore` exception for that directory. The user committed it: `1fd20b5`.
3. **Wrote the code** after the freeze: `scripts/eval/caries_intervals.py` (new, reuses the
   existing bootstrap, scorer and Ningxia loader), and a small change to `c1_vlm_baseline.py` —
   the pipeline arm takes `--caries-method`, defaults to the gate, forces CPU and writes to a
   named file.
4. **Ran M1 and M2** from saved outputs. Both harness gates passed.
5. **Ran the M3 control**, the gate path on this machine. It missed its tolerance: F1 0.3002
   against the published 0.2936. Stopped before the detector arm, as the pre-registration
   required.
6. **Investigated.** Ran the pipeline code as of `322f787` (30 Aug) on the same machine. Its
   predictions are identical to the control's on all 164 images. So the difference is between
   machines — the published file came from the Windows box — and not between code versions.
7. **Amendment 1**, approved by the user and committed (`33c1340`, not pushed) before the
   detector arm ran: the control is gated against the old code on the same machine, and the
   cross-machine difference is recorded.
8. **Ran the detector arm once.** Scored it.
9. **Re-checked leakage for M3**: no byte-identical overlap between the 164 scored images and the
   705 source images of the detector's DENTEX training set; perceptual-hash nearest-neighbour
   distances match the training set's own; the two closest pairs were looked at and are
   different patients.
10. **Logged**: `RESULTS_LOG` 2026-10-11; `model_metrics.md` (C1 and Stage 3); `PAPER_MATERIAL.md`
    §8.29 and a §9 item; `transfer.md` §3; root `README.md`; `scripts/eval/README.md`.

Results, in one place:

| | Result |
|---|---|
| M1 constant − gate pipeline, F1 | +2.61 pp [−0.64, +5.99] — not separable |
| M2 detector − constant, test1 / test2 / test3 / test4 | +1.58 [−4.43, +7.74] / +16.91 [+10.48, +23.35] / +11.73 [+1.29, +21.58] / +10.75 [+0.60, +20.18] |
| M3 lesion-detector pipeline | P 0.353, R 0.403, F1 0.376 |
| M3 detector − constant | +5.64 pp [+1.74, +9.47] |
| M3 detector − gate control | +7.59 pp [+4.47, +10.70] |
| Cross-machine drift, gate pipeline | 0.2936 (Windows) vs 0.3002 (macOS), identical code |

## Decisions made

- **The pipeline arm defaults to the gate.** The script is the reproducibility harness for the
  published 0.294; a default that silently reproduces a different system is worse than one that
  needs a flag. Same policy as `validate_fdi_assignment.py`'s head default.
- **CPU is forced for the pipeline arm.** On Apple silicon `pick_device()` returns MPS, while the
  arm's output has always been recorded as "cpu" and the paper claims CPU.
- **No new pytest file.** The checks are harness gates inside the script, which run on every
  invocation. A new test file would have made "174 tests" stale in six places, one of them
  `main.tex`, which cannot be compiled here.
- **A dedicated output directory** rather than writing into `outputs/c1_vlm/`, so no published
  artefact could be touched and nothing globs the new files by accident.
- **The tolerance was my error, and the amendment says so.** It gated a same-machine run
  against a number from another machine. Amending was legitimate only because the detector arm
  had not been run; that is recorded in the amendment and in the commit message.
- **`paper/main.tex` not edited.** The three results change wording in the abstract, Table I,
  the Lever B subsection and the Conclusion. Those are the authors' sentences, and the file
  cannot be compiled on this machine.

## Open questions

- **How does the thesis read now?** The paper says a tooth-level score cannot show a system is
  reading the radiograph, because a constant matches it. That holds for the gate and for both
  language models. The shipped detector now beats the constant on that score, on development
  data. This is the authors' and the mentor's call.
- **Should Table I restate both pipeline rows from one machine?** 0.294 and 0.300 are the same
  code on two machines.
- **Is one training run enough to carry M3 in a paper?** It is stated as a limit. A second seed
  would need GPU and its own pre-registration.
- Whether the same cross-machine drift sits under other published rows that were measured on
  one machine and never re-run on the other.

## Next steps

1. Commit this session's files (listed in the chat summary); `33c1340` is local and unpushed.
2. Item 6: the Stage-4 wording in the report, overlay and app. Untouched so far, deliberately,
   so that both M3 runs used identical pipeline code.
3. Give the authors the manuscript change list in `PAPER_MATERIAL.md` §8.29 and §9.
4. Start the six-page caries-only cut.
