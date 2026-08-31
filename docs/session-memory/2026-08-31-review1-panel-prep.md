# 2026-08-31 — Review 1 panel-deck relabel + prep handbook

## Session goal

Get `REVIEW3_PANEL.html` and `TEAM_HANDBOOK.html` ready to present at the
**UE23CS441A Capstone Project Phase 3 — Progress Review 1** panel, and write down
how the team should prepare. No research work — presentation/documentation only.

## What was done

**`transfer.md` + `docs/results/model_metrics.md` headers** (earlier in the same session,
separate from the panel work) — refreshed to current state: transfer.md got a 31 Aug
"staleness sweep" entry noting the 29 Aug README rebuild and flagging that §8's
"git does NOT carry" table is now wrong (commits `f6609b7`/`1b430e2` committed `outputs/`
and the sub-50 MB checkpoints; `.git` is ~763 MB). model_metrics.md header date
`2026-08-27` → `2026-08-28`, and the obsolete "Stage-1/2 figures are STALE" banner
(overtaken by the 27 Aug seg-detector re-measurement) was retired.

**`docs/REVIEW3_PANEL.html`** — applied via `scratchpad/edit_panel.py` (asserted
substitutions, CRLF preserved). Root duplicate `./REVIEW3_PANEL.html` synced to match.
- Labels: Phase 2 → Phase 3, Progress Review 3 → 1, `UE23CS320B` → `UE23CS441A`,
  Semester VI → VII, `<title>`, footer, the EDIT-GUIDE comment. Added a "Review date
  = 31 August 2026" card to the hero id-grid.
- Section 02: "recorded in our Phase 1 review" → "…in our earlier reviews" (the three
  panel suggestions were kept — user's call — but no longer pinned to a specific phase).
- **Left contents navbar** — `<nav class="sidenav">`, `position:fixed`, 232 px, shown
  only `@media (min-width:1200px)` with `body{padding-left:232px}`; hidden and zero-impact
  below that. `id="s01"`–`id="s12"` added to every `<section>`, `id="top"` to the hero.
  IntersectionObserver scroll-spy for the active link; nav clicks do an instant
  `scrollIntoView({behavior:'auto'})` + reveal (deck-style, no 7000 px smooth-scroll).
- **Two pre-existing bugs fixed** (would have shown on a projector):
  1. No `<meta charset>` anywhere in the file → served over HTTP the UTF-8 `·`/`—`
     rendered as `Â·`/`â€"`. Added `<meta charset="utf-8">` + viewport.
  2. The EDIT-GUIDE comment contained `find the <!-- SECTION nn --> markers`; the inner
     `-->` closed the comment early and leaked `markers … repository. ===== -->` as
     visible body text. Reworded to `search for the "SECTION nn" comment markers`.
- Content: "8 pages" → **"12 pages"** in two places (verified: `paper/main.pdf` is 12
  pages; 26 `\cite` keys, 5 figures — those were already right). Section 11 venue/cost
  table removed per user; kept a short "Publication plan" with the journal-vs-conference
  recommendation, prices stripped.

**`docs/TEAM_HANDBOOK.html`** — via `scratchpad/edit_handbook.py`. Root duplicate synced.
- Added `<meta charset>` + viewport; masthead eyebrow → "updated 31 August 2026 for
  Phase 3 Review 1"; "8 pages" → "12 pages".
- **New first section "00 — Review 1: Presenting this to the panel"**: the six Phase-3
  deliverables mapped to panel sections; a run-of-show with suggested per-name owners;
  a "numbers to know cold" stat strip; seven Q&A accordions for likely panel pushback;
  a demo runbook with a fallback; a one-minute future-work script; and a callout to
  state the four non-engineering blockers before the panel finds them.

## Decisions made

- **Kept the panel's section 02 ("what the panel asked for")** rather than removing it —
  user chose "relabel to earlier reviews". Reviews respond well to "here's how we
  addressed last time's feedback"; the three items (integrated dataset, survey paper,
  proper architecture) are all genuinely done.
- **Navbar shown only ≥1200 px.** A fixed left rail needs ~232 px of gutter; below that
  it's hidden and the existing sticky topbar covers navigation. `body{padding-left}` in a
  media query is the lowest-risk way to shift the whole doc — no wrapper div, exact
  original layout below the breakpoint.
- **Fixed the charset + comment-leak bugs even though pre-existing** — "be careful, we're
  presenting to the panel". Both are visible on a projector.
- **Trimmed section 11 rather than deleting it** — keeps section numbering (and the nav)
  stable; the publication recommendation is still useful context for a review.
- **Did not touch student USNs** — still the abbreviated `PES1UG23CS098 · CS123 · CS160 ·
  CS907`; user will fill the full ones by hand.
- **No `RESULTS_LOG.md` entry** — no model trained, no metric produced. This file + the
  `transfer.md` refresh satisfy rules 2 and 5.

## Open questions

- The browser pane in this environment hangs on `scroll` for the 1.7 MB panel page
  (9 embedded PNGs + the count-up rAF loop). Verified instead via JS + early screenshots:
  navbar renders and shifts content, 13 links all resolve, `s01`–`s12` present, charset
  fixed, comment leak gone, 9/9 images load, no console errors, both `<script>` blocks
  valid. **The continuous scroll-spy highlight was seen working once** (clicking a link
  moved the active marker) but not re-confirmed after the pane degraded. Worth one look
  in a real browser before the review.
- Root-level `REVIEW3_PANEL.html` / `TEAM_HANDBOOK.html` are untracked byte-for-byte
  duplicates of the `docs/` copies (kept in sync this session). Someone should delete the
  root pair or decide they're intentional.
- USNs, and whether "Semester VII" should read "Semester 7" (kept Roman to match the
  file's existing style).

## Next steps

1. Team: open `docs/REVIEW3_PANEL.html` in a real browser, click through the nav, run
   `streamlit run app.py` and confirm the demo, fill in the four USNs.
2. Rehearse against handbook §00 — the run-of-show and the seven Q&A answers.
3. Unchanged and still the real critical path (not this session): venue-length cut of
   `paper/main.tex`, the four compliance blockers (`PAPER_MATERIAL.md` §8.19), upload
   `models/11_yolo_seg_tufts_r1/best.pt` to Drive.
