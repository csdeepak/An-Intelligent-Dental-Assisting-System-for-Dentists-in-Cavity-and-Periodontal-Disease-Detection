# 2026-10-14g — Windows orientation, the Mac hand-off prompt, and a narrated panel-review video

**Session goal:** orient the Windows clone, hand the Stage-4b retrain to the Mac, and make a
narrated video for the review panel. The video has three parts: the project, one real image
through every stage, and the results before and after the October review.

This ran on the Windows clone, night of 14 Oct. The video was built in the git worktree
`.claude/worktrees/video-panel-review` (branch `video/panel-review`), cut from `origin/main` at
`c3d024c`. The user asked that this work never touch `main`. No model was trained, no test set was
scored, and Ningxia was not touched.

## What was done

- **Orientation.**
  - The Windows `main` was at `fc811ca` (7 Sep), 32 commits behind `origin/main`.
  - It holds two local edits that collide with upstream: `.gitignore` (`.rcs/`) and `transfer.md`
    (the 30 Sep RCE mentor-draft note).
  - It also holds the untracked RCE draft files. During this session someone else began staging
    them in the main checkout, and they were left alone.
- **Tufts data check (Windows).**
  - `_repo_archive/datasets_workspace/` holds scripts and notebooks only.
  - 104 of the 1,000 original radiographs are present; there are no expert masks.
    `teeth_bbox.json` is present, and its md5 matches the pinned `8fb9182c…`.
  - `Radiographs_upright_fixed/` is not the originals: 0 of 104 are pixel-identical.
  - The macOS session recorded all of this in `transfer.md` §8.
- **The Mac hand-off.** A pasteable prompt for the Stage-4b retrain, gated at two stops. The Mac
  ran it: `a6e837b`, `e3bb2ae`, `c3d024c`, and session file `2026-10-14f`.
- **JarvisLabs.** `jl` 0.2.17 works only through `Python313\Scripts\jl.exe`; the `Python311` shim
  points at a removed interpreter. This PC's key (`~/.ssh/id_ed25519.pub`) is already registered as
  `r1-seg-windows`. The balance is ₹1,148.78 and nothing is rented.
- **Video**, under `brag-output/`. `brag-plan.md` has the storyboard and the source of every figure.
  - The shipped pipeline was traced on 8 leak-free DENTEX images (`work/trace_pipeline.py`), and
    `test_211` was chosen.
  - The narration is edge-tts `en-IN-NeerjaNeural`, with word timings driving the visual cues.
  - The composition is HTML/SVG, rendered by headless Chrome over CDP with Node's built-in
    WebSocket, so no npm packages were needed.
  - The music bed is synthesized and ducked under the voice. The video runs 5 min 55 s at
    1080p30, and the captions are in `captions.srt`.

## Decisions made

- **The image is from DENTEX, not Tufts or Ningxia.** DENTEX is CC BY-NC-SA 4.0, so it can be
  shown with credit. Tufts' licence forbids redistribution, and Ningxia is locked test data. The
  image and every asset derived from it are gitignored.
- **One image is shown as an illustration, never as a measurement.** On screen and in the
  narration: 7 of 9 caries flags fall on annotated teeth, and 4 annotated teeth are missed.
- **"Before the review" means the 7 Sep state.** Nothing was committed between 7 Sep and the
  10 Oct review, so any review date in that gap gives the same split. Some "before" values (for
  example F1 0.376) were measured in October on the previous front end; the video labels them
  "previous front end".
- **The video shows the limits beside the gains.** It shows the cost row (Tufts box mAP 0.723 →
  0.587), the not-separable row (Tufts numbering), DENTEX in-domain, CariesXrays as a validation
  split, and Stage 4b not eligible.
- **Length is about 6 minutes**, against the user's "about 5". The narration was already cut by a
  quarter. Re-voicing at a higher rate is a one-line change in `narration.json`.

## Open questions

- Is the panel's "review" the 10 Oct internal review? The video assumes so.
- Voice choice: Neerja (en-IN) was picked without a listening test. `en-IN-PrabhatNeural` or
  `en-US-AndrewNeural` are drop-in alternatives.
- Whether the user wants the branch committed, and whether pushed.

## Next steps

1. The user watches `brag-output/brag.mp4` and asks for any re-roll (a scene, the voice, the length).
2. If wanted, commit the sources on `video/panel-review`. The rendered media stays local.
3. Windows `main`: stash or commit the two local edits, fast-forward to `origin/main`, and re-merge
   the RCE note into the rewritten `transfer.md`.
