# 2026-09-06d — Project overview report (HTML), and why it is not in the repo

> **Superseded same day — see `2026-09-06e-report-into-repo.md`.** The user chose to place the
> report in the repo root as `PROJECT_OVERVIEW.html`. The "keep it out of git" decision below is
> reversed: the repo is private, so a tracked HTML is no more exposed than `PAPER_MATERIAL.md`;
> the staleness concern stands and is mitigated with a prominent "snapshot, not maintained"
> banner. This file is left as written per the never-edit-a-past-entry convention.

**Session goal:** generate a detailed, multi-theme HTML document summarising the whole project —
what was done, results, limitations, further work — for Deepak and his mentor / committee.

## What was done

- Built a self-contained single-page HTML report (~52 KB, no framework, no external JS; IBM Plex
  Sans/Mono from Google Fonts; 3-theme toggle: light / dark / high-contrast for print &
  projection). Content is 100% derived from `transfer.md`, `RESULTS_LOG.md`, `model_metrics.md`,
  `PAPER_MATERIAL.md` §8, and the 6 Sep councils — every number traces to those.
- Sections: the finding → the six-stage pipeline → a dated timeline of milestones → results
  (C1 constant baseline, the 3-cohort external comparison, Lever B, Stage-2 numbering, the
  taxonomy, calibration/abstention, the periodontal negative) → ~15 headline limitations with a
  disposition tag each → further work in three tiers (submission-blocking / optional / post-
  submission).
- **Delivered to the user as a file (`SendUserFile`). Not committed to the repo.**
- Verified once in a local browser: 3 themes resolve, no body horizontal overflow (tables scroll
  in their own wrappers), fonts load, chart bar widths match the source numbers.

## Decisions made (the "council")

- **Local HTML file, handed over — NOT auto-published as an artifact, NOT tracked in git.**
  Two reasons:
  1. **The manuscript is unpublished.** A detailed public technical report of the same findings
     can count as prior disclosure under IEEE JBHI / Computers in Biology and Medicine rules and
     could complicate the submission. If Deepak wants a shareable URL it is his call — a private
     artifact then, with his own risk read.
  2. **Two live dataset-governance items** (Tufts Drive licence breach; SDH de-identification) are
     recorded in it. Appropriate for an academic-review audience; not for open circulation. The
     report carries a prominent "internal, pre-submission" banner.
- **Snapshot-dated (6 Sep 2026), points every reader at the four living sources as
  authoritative.** It is a point-in-time deliverable, not a maintained doc — the repo's founding
  failure mode is a status doc that drifted three months (`README.md`), and a tracked HTML that
  duplicates `PAPER_MATERIAL.md` is exactly that risk.
- If the user wants it in the repo anyway, it belongs in `docs/reports/` **with the point-in-time
  PDFs** (not the living-docs tree), and `docs/README.md` gets a row — his placement call.

## Open questions

- Does Deepak want a private-artifact URL for it (shareable with the committee), accepting the
  prior-disclosure consideration? Not done pending his decision.
- Should a stripped version (no compliance items, no unpublished numbers) be produced for any
  wider audience? Not requested; flagged as an option.

## Next steps

1. Deepak: keep the file as-is, or ask for it as a private artifact / a repo copy in
   `docs/reports/`, or a redacted external version.
2. Otherwise unchanged — the next-steps council (`2026-09-06c`) still governs: the one-hour
   mentor meeting is the highest-leverage action.
