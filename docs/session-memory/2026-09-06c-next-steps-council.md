# 2026-09-06c — Council: next steps

**Session goal:** with the Lever C pre-registration committed (`9492abe`), step back and council
what actually comes next — sequence the open items, separate blocking from optional, name the
single highest-leverage action.

## What was done

- Re-read `transfer.md` §3–§5, `PAPER_MATERIAL.md` §9, and checked `paper/main.tex` directly for
  the current state. No code, no eval, no `RESULTS_LOG` entry — this is a planning council.
- **One finding that reframes things:** `paper/main.tex` does **not** contain the Tufts
  end-to-end FDI number (64.8% e2e / 78.6% of-detected) at all. `sec:numbering` reports only the
  DENTEX 58.3% / 82.6%, and it already gives "both framings" (end-to-end vs of-detected) that
  Related Work promises. So there is **no weak Tufts number in the paper for a reviewer to
  flag** — which makes Lever C (and Option F) genuinely optional polish, not a fix.

## The state, honestly

The manuscript is **done**: 14 pages, compiles clean (0 errors, 0 undefined refs),
`verify_paper_numbers` 127/127, `pytest` 159/159, `verify_invariants` all hold. The spine — the
evaluation-protocol contribution plus Lever B folded in as a positive result — is written.

**What stands between here and submission is almost entirely NOT engineering:**

| # | Item | Owner | Blocking? |
|---|---|---|---|
| 1 | **Tufts Drive folder is link-accessible** — a live licence breach, "real submission risk" (`transfer.md` §4) | account owner | **YES** |
| 2 | **SDH `metadata/index.csv` sits beside `images/`** on two copies — de-identification void | Drive/account owner | **YES** (for any clinic use; clinic data is used in no result) |
| 3 | **Venue commit** — journal primary decided 2 Sep, not acted on; re-verify Scopus indexing for IEEE JBHI / Computers in Biology and Medicine | Deepak / mentor | **YES** — gates whether an ISBI length cut is even needed |
| 4 | **Authors + affiliations** — still `Unknown` in `main.tex` | Deepak | **YES** (to submit) |
| 5 | Title / thesis / whether the abstract's "four things a constant cannot do" becomes five | Deepak | soft — the paper submits with the current four |
| 6 | IRB paperwork | account owner | only if clinic data ever enters a result (it does not) — lowest priority |
| 7 | Tufts mirror-numbering novelty — is it new? Panetta et al. IEEE JBHI 2022 is paywalled/unread | someone with Xplore | 5-minute read, not a blocker but cheap to close |
| 8 | Lever C go/no-go + the 3 review-round questions (`2026-09-06b` council) | Deepak | **NO** — optional, pre-registered not approved |
| 9 | Retire / mark-superseded `docs/paper/{manuscript.md,draft_spine.md}` (stale 0.488, gate-only — a trap for the next reader) | anyone | no — 20-minute cleanup |
| 10 | Docker rebuild (image predates the Lever B caries wiring) | anyone | no — before any live demo |
| 11 | `docs/research/{PUBLICATION_TODO,MASTER_PLAN}` re-sync (predate Lever B) | research workstream | no |
| 12 | Bone-loss classifiers' CI | whoever finds the un-rotated Tufts radiographs | **blocked** on missing files, not on effort |

## The council

**Voice 1 — submission readiness.** The engineering is finished. The paper does not need Lever C,
does not need Option F, does not need the Docker rebuild to be submitted. It needs items 1–4
closed, and 1–4 are one conversation with the mentor plus two account-owner file operations. The
binding risk to an S-grade outcome is **item 1** (the live Tufts licence breach) — `transfer.md`
§5 says so explicitly: "the binding risk to that outcome is the compliance blockers in §4
closing, not any remaining number." Treat item 1 as P0.

**Voice 2 — skeptic.** Two gaps worth naming. (a) **No mock review has been run.** The manuscript
is internally consistent and honestly caveated, but nobody has read it adversarially as a
reviewer would — the bone-loss CI gap, the DVCTNet omission, the "one VLM family" limitation, and
the internal-vs-external-not-comparable point are all *stated*, but a reviewer will still push on
them and the rebuttal should be pre-drafted. (b) **The venue decision has drifted since 2 Sep.**
Four days is not a crisis, but this is the decision that gates everything downstream, and
`transfer.md` opens by noting stale snapshots have "cost this project real time more than once."
Do not let item 3 drift into October.

**Voice 3 — engineering scope.** The temptation right after committing a pre-registration is to
start implementing it. **Resist.** Lever C is pre-registered, not approved, and — per this
session's finding — the paper does not even claim the number it would improve. The only
engineering worth doing unprompted is item 9 (retire the stale `docs/paper/` drafts, 20 min, it
is a genuine trap) and, before any demo, item 10 (Docker). Everything else waits on a decision.

**Voice 4 — reality check.** Are we close? **Yes.** This is not a project that needs more months.
The realistic path: one mentor meeting closes items 3–4 and delegates 1–2; a week of the account
owner's attention closes 1–2 and 6; the manuscript is then submittable. The risk is not that
anything is unfinished — it is that the finished thing sits waiting on decisions nobody has
scheduled.

## Decisions made

- **Declare the manuscript feature-complete.** No new experiments, no new sections, before
  submission. Lever C and any further lever are explicitly post-decision / post-submission.
- **The single highest-leverage next action: a one-hour meeting with the mentor** to (a) commit
  the venue (re-verify Scopus first), (b) fill authors/affiliations, (c) delegate or schedule
  the two live compliance breaches. Everything else is downstream of or independent of that.
- **Lever C stays a draft.** Implement only if Deepak says go AND items 1–4 are moving in
  parallel — never as a substitute for them. If go: the 3-day box and the frozen bars from
  `outputs/lever_C_fdi_structural_postproc/PRE_REGISTRATION.md` apply as written.
- **No `docs/research/` edits** (separate workstream).

## Open questions

- **Is a mock review worth commissioning** (mentor, or a second reader) before submission? The
  council's view: yes, and the rebuttal-anticipation notes should live in `docs/paper/`.
- **Does the paper add the Tufts numbering result** (64.8% / 78.6%) as a second cohort for
  `sec:numbering`? Optional. If yes, lead with of-detected 78.6% (§8.16). If no, Lever C loses
  even its nominal paper motivation.
- **ISBI 2027 short paper** — still nominally in play "if compliance closes by mid-October"
  (`transfer.md` §5). Given items 1–2 have not moved, is that realistic, or should it be
  formally dropped now so nobody plans around it?

## Next steps (ordered)

1. **Deepak:** schedule the one-hour mentor meeting. Agenda: venue commit + Scopus re-verify,
   authors/affiliations, compliance-breach delegation. This unblocks the most per hour.
2. **Account owner:** close item 1 (restrict the Tufts Drive folder — P0, live breach) and item 2
   (move SDH `index.csv` off the shared tree).
3. **Anyone, ~20 min:** retire / mark-superseded `docs/paper/{manuscript.md,draft_spine.md}`.
4. **Deepak:** Lever C go/no-go and the 3 review-round questions (`2026-09-06b`); decide whether
   the Tufts numbering result goes into `main.tex`.
5. **If a demo is needed:** Docker rebuild.
6. **Optional:** commission a mock review; draft rebuttal-anticipation notes.
7. **Blocked, revisit only if the files surface:** bone-loss classifiers' CI.
