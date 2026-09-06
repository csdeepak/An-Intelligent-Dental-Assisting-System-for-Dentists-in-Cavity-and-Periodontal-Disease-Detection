# 2026-09-06e — Project-overview HTML placed in the repo (reversing 2026-09-06d)

**Session goal:** the user asked for the project-overview HTML (built in `2026-09-06d`) to live
in the repo root, and for the READMEs to be updated to point at it and to reflect current
results. This session does that and records why the earlier "keep it out of the repo" decision
was reversed.

## What was done

- `PROJECT_OVERVIEW.html` written to the **repo root** (from the `2026-09-06d` scratchpad build,
  with a strengthened "this is a snapshot, not maintained" banner). Self-contained, 3-theme
  toggle, ~52 KB, no external JS. Trackable (`git check-ignore` clears it).
- Every number in it re-verified against `docs/results/model_metrics.md` and `RESULTS_LOG.md`
  before it went in — all consistent (the C1 table, the 3-cohort external comparison, Lever B,
  Stage-2 numbering DENTEX+Tufts, the taxonomy, calibration/abstention, the periodontal negative,
  97.65 M params, the 26-point Ningxia swing).
- Pointers added: root `README.md` (START HERE table, marked *snapshot*), `transfer.md` §0 + the
  "Targeted updates since" note, `docs/README.md` Layout table.
- One-line "superseded" pointer appended to the uncommitted `2026-09-06d`.
- `pytest` 159 / `verify_paper_numbers` 127 — unchanged, nothing code-facing touched.

## Decision made, and why 2026-09-06d is reversed

`2026-09-06d` decided the report should **not** be tracked in git, on two grounds:
prior-disclosure risk and staleness. On review, the two concerns separate cleanly:

- **Prior-disclosure risk was about publishing it publicly** — an artifact URL, or the repo
  going public. **The repo is confirmed private** (`transfer.md` §4). A tracked HTML there has
  the *same exposure* as `PAPER_MATERIAL.md`, `RESULTS_LOG.md` and every other doc that already
  carries the unpublished findings and the two compliance notes. Committing it adds **no new
  disclosure risk**. The earlier note conflated "in the repo" with "public."
- **It joins the "before public release" list** in `transfer.md` §4 (alongside the embedded
  Tufts pixels in 7 notebooks and `models/11` in git history) — review / redact / remove before
  this repo or any fork is ever made public. The HTML's own banner states this.
- **Staleness is the real remaining cost, and it is accepted with mitigation.** The repo's
  founding failure mode is a status doc that drifted three months (`README.md`). Mitigation: the
  HTML opens with a blunt "snapshot, not kept in sync, authoritative sources are
  `transfer.md` / `RESULTS_LOG.md` / `model_metrics.md`" line; it is marked a *point-in-time
  snapshot* in both READMEs, the same status as `docs/reports/*.pdf`; and it carries its
  generation date in the title area. It is a deliverable, not a maintained document.

**Placement:** the user asked for repo root. The conventional home for a report is
`docs/reports/` (with the PDFs) — noted to the user, root honored. Named `PROJECT_OVERVIEW.html`
so it does not collide with `docs/reports/project_report.pdf` ("the full project report").

**find-skills** (`.claude/skills/find-skills`) was attached again. Considered: for updating this
repo's own READMEs and generating an HTML report, the in-repo conventions plus the loaded
`artifact-design` skill are the right tools; `npx skills find` is a network + install action not
run without an explicit request. Recorded so it is not re-litigated.

## Open questions

- Does the user want a copy in `docs/reports/` as well / instead (the conventional home)?
- A redacted external version (no compliance items, no unpublished numbers) for any wider
  audience — still an option, still not requested.
- When the report goes stale (next substantial result), the choice is regenerate or delete —
  it must not be left drifting. Whoever next touches results should check it.

## Next steps

1. User commits (`PROJECT_OVERVIEW.html` + the README/transfer/docs pointers + the pending
   `2026-09-06c` / `2026-09-06d` / `2026-09-06e` + the `transfer.md` §3 edit).
2. Unchanged: the next-steps council (`2026-09-06c`) still governs — the one-hour mentor
   meeting (venue, authors, the two compliance breaches) is the highest-leverage action.
