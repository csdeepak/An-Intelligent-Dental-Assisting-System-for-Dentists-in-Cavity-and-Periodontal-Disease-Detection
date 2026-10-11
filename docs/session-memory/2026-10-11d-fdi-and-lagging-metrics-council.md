# 2026-10-11d — Council: how to fix end-to-end FDI, and which metrics still lag

**Session goal:** answer two questions from the user — how to fix end-to-end FDI (58.3% on
DENTEX, 64.8% on Tufts), and which metrics are still lagging — with a council.

Run on the macOS clone. No model was run and no code changed. Documentation only.

## What was done

### 1. Facts first

- Pulled the four-detector end-to-end table from `model_metrics.md`: deployed seg 58.3% / 64.8%
  (DENTEX / Tufts); superseded bbox 46.3% / 71.5%; Lever A arm3c 92.8% / 63.5%; A2 87.7% / 63.7%.
- Confirmed a partial confidence sweep exists: the deployed detector at confidence 0.10 on Tufts
  scored 61.3% end to end (`RESULTS_LOG` 2026-09-04d). Nothing on DENTEX.
- Counted where the deployed detector misses on DENTEX by tooth position: first premolars 55%,
  canines 39%, third molars 37%, incisors 12–19%.

### 2. The council

Three independent read-only members (`Plan` agents; brief in the session scratchpad).

| Seat | Lens | Model |
|---|---|---|
| 1 | ML diagnosis | Opus |
| 2 | Scientific integrity and paper relevance | Opus |
| 3 | Delivery and blast radius | Sonnet |

**Consensus**

| Option | Verdict |
|---|---|
| Change nothing, and say so: numbering is detection-bound, with the multi-corpus ablation as the measured ceiling | **Do now** — writing only. 3 of 3 |
| Adopt the multi-corpus detector as the default | **Not now.** 3 of 3 |
| A new position-digit model, or a retrained detector | Not for this paper. 3 of 3 |
| A reject option in the assignment | After submission. 2 of 3; seat 3 said not this cycle |

**Dissent**

| Point | Positions | Chair |
|---|---|---|
| One new measurement: the lesion detector on the multi-corpus front end, DENTEX only | Seats 1 and 2: now. Seat 3: after submission, unless CONECCT is chosen and there is slack by about 1 Nov | Recommended as the single optional item, about a day. The user decides |
| Should that measurement carry a bar? | Seat 1: lower bound ≥ +3 pp, as a stop/go for further Stage-1 work. Seat 2: estimation only, with an explicit no-adoption clause | Estimation only. The smaller commitment, and it cannot become a back door to a default change |
| Can the existing multi-corpus checkpoint ever become the default? | Seat 1: after submission, if the measurement is positive and a reject option removes the Tufts cost. Seat 2: never by a dated override — only a new checkpoint, with its guard written first | Not settled, and not needed now |

### 3. What the chair verified

From the saved, tracked per-tooth rows (`RESULTS_LOG` 2026-10-11c):

- DENTEX, deployed detector: 546 correct, 275 never detected, 115 wrong code, of 936.
- On the 660 teeth both detectors find, wrong codes are 115 from the deployed boxes and 41 from
  arm3c's, with the same head.
- The misses are by image: the worst 41 images hold 168 of the 275; 50 images have none.
- Caries recall ceiling set by the front end: 288 of 477 carious teeth delivered under the right
  code (0.604) for the deployed detector; 453 of 477 (0.950) for arm3c. Measured pipeline recall
  is 0.403.
- `run_inference.py --detector` stamps the default detector's tag and its 70.6% / 58.3% constants
  whatever weights are loaded (`DETECTOR_TAG` at the report's `models.detector.tag`).
- `paper/main.tex` does not mention the multi-corpus ablation.

Reported by seat 1 and **not** re-derived: the Tufts decomposition (17.6 pp undetected, 16.9 pp
wrong code, up to 7 pp of it from surplus boxes); that of-detected accuracy against surplus
boxes per image is one curve for both detectors; that at confidence 0.10 about a tenth of
detected teeth get no code. Reported by seat 3 and not checked line by line: the list of five
places a detector path is hard-coded.

## Decisions made

- **The Stage-1 default does not change.** Two pre-registered rules recorded the multi-corpus
  detector as an ablation. The Tufts end-to-end figure that makes the failed guard look small
  was read afterwards, carries no interval, and was never part of either rule. Overriding on it
  would be substituting the outcome. It would also re-measure every number in the pipeline.
- **The earlier precedent is weaker than it looks.** The seg detector was adopted on 27 Aug
  against a missed mask bar, but that bar governed a mask feature that was then left unwired.
  Lever A's rule governs the default itself and says in words what happens on failure.
- **The answer to "how do we fix it" is recorded even though nothing is being fixed now.**
  DENTEX is detector-bound; a multi-corpus detector is the fix that is known to work; the
  measured cost on Tufts is small end to end; and the caries score inherits the same ceiling.
- **Lagging metrics, ranked by who will press on them.**
  - *A reviewer of the caries paper:* the caries F1 (one training run, development data, recall
    capped upstream at 0.60); lesion agreement (a tie on DENTEX, not separated at one Ningxia
    hospital); the 0.294 / 0.300 cross-machine gap inside Table I; no calibration for the lesion
    detector.
  - *One sentence each:* detection recall and end-to-end FDI, with the measured ceiling.
  - *Capstone only:* Stage 4a, the severity head on 52 crops, the caries depth head with no
    held-out test.
  - *Stated as a limit:* no clinician comparison.

## Open questions

- Does the user want the one optional measurement run now? It needs a pre-registration commit
  first, a `--detector` pass-through in `c1_vlm_baseline.py`, and the tag fix above.
- The saved Tufts summary says 143 images; the log and the scoreboard say 149.
- Whether a collaborator may propose overriding a rule the owner pre-registered.
- Has arm3c's DENTEX training set been checked against the 164 images for near-duplicates, the
  way the lesion detector's was on 11 Oct? Its build script gates on MD5 only.

## Next steps

1. Commit this session's documentation.
2. Writing: add the detection-bound sentence and the multi-corpus ceiling to the numbering
   paragraph and the Limitations of the manuscript.
3. If the user says go: pre-register and run the lesion detector on the arm3c front end, DENTEX
   only, once, estimation only, default unchanged.
4. After submission: the reject option, tuned on Tufts validation only.
