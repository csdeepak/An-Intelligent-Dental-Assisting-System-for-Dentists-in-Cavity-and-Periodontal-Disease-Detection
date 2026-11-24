# Panel-review video — plan and evidence

**What it is:** a 5 min 55 s narrated explainer of the capstone for the review panel. It has three
parts: (1) introduction, (2) one real radiograph traced through every pipeline stage, (3) results
across the timeline, before and after the 10 Oct 2026 review.
**Tone:** `polished`, meaning calm and evidential, with long holds and dips between scenes. It is
not a launch video. The brag 15–25 s rule was set aside because the user asked for detail.
**Format:** 1920×1080, 30 fps, H.264 + AAC. Narration is `en-IN-NeerjaNeural` (edge-tts, +15 %).
**Updated 24 Nov 2026 for the new Stage-3b severity result.** The script, the on-screen text and
the trace were updated; the audio, `timeline.json`, `captions.srt` and the rendered video were
not. They still carry the 14 Oct narration, so the video must be re-voiced and re-rendered
(rebuild order below) before it matches this plan. See "24 Nov update" at the foot.
The music bed is synthesized locally.

## How it is built (`work/`)

| Step | Script | Output |
|---|---|---|
| Run the shipped pipeline on DENTEX images, keeping every stage's output | `trace_pipeline.py` | `trace/<stem>_report.json`, `_lesions.json`, `_overlay.jpg` |
| Narration → audio + word timings → scene timeline | `make_voice.py` (reads `narration.json`) | `voice/*.mp3`, `timeline.json` |
| Pipeline output + timeline → composition data and crops | `prep_data.py` | `site/data.js`, `site/assets/*` |
| Composition, each frame a pure function of t | `site/index.html`, `style.css`, `app.js` | — |
| Headless Chrome over CDP (Node's built-in WebSocket, no npm) → ffmpeg | `render.mjs` | `video_silent.mp4`, review stills |
| Voice on the timeline + ducked synthesized pad | `mix_audio.py` | `mix.wav` |
| Captions from the word timings | `make_captions.py` | `../captions.srt` |

Rebuild: `make_voice.py` → `prep_data.py <img> <label>` → `node render.mjs video video_silent.mp4` →
`mix_audio.py` → mux (see `README` lines at the bottom).

## The image

The image is DENTEX `disease/input/test_211.png` (3,076 × 1,536 px), one of the 164 leak-free
evaluation images. It was chosen from 8 candidates because it shows the full 32-tooth dentition, no
numbering flags, and every stage producing output. **It is an illustration, not a measurement**,
and the video says so on screen and in the narration. The licence is CC BY-NC-SA 4.0; the credit is
on screen. The image and its derived assets are kept out of git.

What the pipeline produced on it (`trace/test_211_report.json`, shipped defaults, schema 1.7;
re-traced 24 Nov 2026 on macOS after the Stage-3b default change, previously schema 1.5 on Windows):

- **Detections:** 32 teeth, minimum detection confidence 0.79, 32 distinct FDI codes, 0 duplicates.
- **Caries:** 9 lesion boxes, mapped to 9 flagged teeth: 16, 21, 26, 36, 37, 44, 45, 46, 47. The
  mapping was re-run with `lesion_preds_to_tooth_idx` and asserted equal to the report.
- **Severity:** tooth 21 is graded deep caries (score 0.540); the other eight are caries. Under the
  previous head, 21 and 46 were deep, and 46 sat at 0.503, a call that flipped between machines.
- **Stage-4 flags:** teeth 11, 37 and 48.
- **Against the DENTEX caries annotations (class 1):**
  - 7 of the 9 flags fall on annotated carious teeth.
  - 2 flagged teeth carry no caries annotation: 21 and 26.
  - 4 annotated carious teeth are missed: 17, 22, 25 and 27.

## Storyboard (durations from `timeline.json`)

| # | Scene | s | On screen |
|---|---|---|---|
| 1 | Title | 8.4 | Title over a faint OPG; scan sweep; four chips |
| 2 | Problem | 15.9 | The OPG with a sweep and a magnifier; three steps; FDI grid |
| 3 | What we built | 14.6 | Six-node pipeline with a travelling packet; real input → real overlay; 1.70 s / 95.3 M / demo |
| 4 | Data | 19.7 | Five dataset cards with roles: train, dev, external, unseen |
| 5 | The constant | 17.8 | Dental chart, the 8 molars lit; F1 0.320; "the floor" |
| 6 | Input | 13.8 | Part card; the real image; meta chip; pipeline rail |
| 7 | Stage 1 | 15.5 | Image rotates 90°, scan line, 32 boxes drawn, rotates back; confidence histogram |
| 8 | Stage 2 | 16.3 | Zoom to tooth 16; its 1.5× crop flies into ResNet-18 → "FDI 16, p 0.9997"; 32 labels pop in arch order |
| 9 | Stage 3a | 15.0 | 9 lesion boxes with confidences; links to their teeth; teeth turn orange |
| 10 | Stage 3b | 13.0* | CARIES/DEEP pills; each deep tooth (here 21) pulses as its number is spoken; "tested once, on held-out data": 395 crops, macro-F1 0.772 vs 0.483 |
| 11 | Stage 4 | 18.8 | Zoom to tooth 48; taller crop flies in → flag p 0.68; violet rings on 11, 37, 48; "not periodontal" |
| 12 | Stages 5–6 | 14.1 | Tooth 16's JSON record line by line; model hashes; final orange/blue overlay |
| 13 | Check | 15.0 | Dentist caries polygons; ✓ on 7 hits; dashed outlines on 4 misses; "one image, for illustration" |
| 14 | Timeline | 22.7 | Part card; Aug–Oct axis; 4 milestones; Lever B lesion-agreement card |
| 15 | Review | 17.0 | 10 Oct marker; 0.923 struck through, with the two reasons; response list 11–14 Oct |
| 16 | Front end | 29.1 | Five before → after dumbbells, including the cost row and the not-separable row |
| 17 | Caries | 20.8 | F1 bars against the constant line; Ningxia grouped bars; honest-limits footnote |
| 18 | Stage 4 | 32.8 | 83.1 → 7.6 → 27.5 % (with seed marks); 0.721 (contrast) vs 0.294 vs prior 0.334 → not eligible |
| 19 | Engineering | 15.1 | Claims 127 → 207, tests 174 → 204, schema 1.1 → 1.5; pins, hash check before loading, invariants |
| 20 | Takeaway | 9.8 | Lowered, raised, named |
| 21 | Close | 9.9 | Next steps; thank you; credits |

## Where every number comes from

| Figure in the video | Source |
|---|---|
| 1.70 s per image on CPU; 207 claims, 204 tests, 12 invariants (14 Oct, late night) | `transfer.md` §1 at `f1007ca`; hash check before loading: `af5cc44` |
| 127 claims, 174 tests (before) | `transfer.md` §1 at `fc811ca` (7 Sep snapshot) |
| 95.3 M parameters | `model_metrics.md`, *Current front end*, Size |
| Constant F1 0.320; F1 0.376 → 0.498; +17.80 pp [+13.48, +22.02] | `model_metrics.md`, *Caries, FDI-set F1* |
| Ningxia lesion agreement 39.9 / 50.0 → 59.1 / 68.4 %; +9.28 pp [+4.72, +13.73]; DENTEX −3.55 pp | `model_metrics.md`, *Caries, lesion agreement* |
| Recall 70.8 → 99.6 %; numbering 58.4 → 92.8 %, 64.8 → 63.5 % | `model_metrics.md`, *Tooth numbering* |
| UFBA-425 20.6 → 44.5 %; box mAP 0.723 → 0.587 | `model_metrics.md`, *Current front end* |
| Lever B 44.3 / 48.9 / 45.5, 31.7 / 56.2 / 68.4, 40.8 / 39.9 / 50.0; 3 of 4 hospitals | `model_metrics.md`, *Stage 3 — lesion detector* |
| 0.923 and 83.05 % (crop-level validation, 59 positives); 7.6 % held out | `model_metrics.md`, *Stage 4a* |
| 27.5 / 16.5 / 11.0 %, specificity 95.9 % | `model_metrics.md`, *Stage 4a*, retrained |
| 0.7208 (52 crops); 0.2938 vs prior 0.3344, −0.0405 [−0.1245, +0.0584], not eligible | `model_metrics.md`, *Stage 4b* |
| Caries severity: 395 held-out crops from 98 radiographs, macro-F1 0.772 [0.711, 0.828] vs 0.483 for an image-blind rule; tested on annotation boxes, not flagged teeth | `RESULTS_LOG.md` 2026-11-24; `outputs/caries_severity_v2/test_summary.json`; `model_metrics.md`, *Phase 2 severity* |
| Report schema 1.7; tooth 21 deep (0.540), tooth 48 flag p 0.68 | `trace/test_211_report.json` (re-traced 24 Nov 2026) |
| Milestones: 24, 25 and 28 Aug; 4 Sep; 10–14 Oct | `RESULTS_LOG.md` entries of those dates |

## Mux (final step)

```
ffmpeg -i work/video_silent.mp4 -i work/mix.wav -i captions.srt -map 0:v -map 1:a -map 2:s \
  -c:v copy -c:a aac -b:a 192k -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:s mov_text \
  -metadata:s:s:0 language=eng -shortest brag.mp4
```

## 24 Nov update — the new Stage-3b severity result

**Why.** On 24 Nov 2026 the caries-severity head was retrained on DENTEX's image-level split, tested
once under a pre-registration, and adopted as the default (`RESULTS_LOG` 2026-11-24, -24b; main at
`cf438fc`, merged into this branch). Scene 10 said "validated, never tested", which now describes
the replaced head.

**What changed here:**

- **`narration.json`:**
  - Scene 10 names the one deep tooth and states the test (macro-F1 0.77 on held-out
    radiographs), and says it was measured on annotated teeth, not on the teeth the pipeline
    flags.
  - Scene 12 says schema 1.7.
- **`site/index.html`:**
  - the scene-10 box now reads "Tested once, on held-out data", with 395 crops and macro-F1 0.772
    vs 0.483;
  - the scene-10 and scene-12 sources;
  - tooth 48's flag p (0.68), the only hand-typed value the re-trace moved.
- **`site/app.js`:** the pulse in scene 10 follows whichever teeth the trace grades deep, timed
  to the spoken tooth number. It was hard-coded to 21 and 46.
- **`trace/test_211_*`:** re-traced with the current defaults, macOS (MPS). Against the 14 Oct
  Windows trace:
  - identical: summary, teeth, codes, boxes, detection confidences, lesion confidences (3
    d.p.), the caries flags and the Stage-4 flags;
  - severity: tooth 46 changed deep → caries;
  - small drift: Stage-4 confidences moved by machine (tooth 48 0.6745 → 0.68), and tooth 36's
    FDI confidence 0.9998 → 0.9997.
  - The other seven candidate traces in `trace/` are still the 14 Oct pipeline.
- **One honest note for the panel:** the only deep call (tooth 21) is on a tooth the dentists did
  not annotate as carious (see "The image" above). Its label is `3-kanal`, root-canal treated. The
  disease set's labels (`disease/label/*.json`: saglam, çürük, küretaj, kanal, çekim, gömülü,
  lezyon, kırık) carry no deep-caries class to check the grade against.

**Stale until rebuilt:**

- `timeline.json`, `voice/`, `mix.wav`, `captions.srt` and `brag.mp4` still carry the 14 Oct
  narration. Durations marked * in the storyboard are the old ones.
- Rebuild order (as above), with the plan's own scripts:
  1. `make_voice.py` (edge-tts, online);
  2. `prep_data.py <test_211.png> <test_211.json>`;
  3. `node render.mjs video video_silent.mp4`;
  4. `mix_audio.py`;
  5. `make_captions.py`;
  6. the mux.
- Scene 19 is a dated snapshot ("7 Sep → 14 Oct": claims 207, tests 204, schema 1.5, 10 pins) and
  was left whole: on `main` today `pytest` is 214, the schema 1.7 and the pins 11. Refresh all of
  it together, or leave it as the 14 Oct snapshot it says it is.
