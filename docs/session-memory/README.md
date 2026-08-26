# `docs/session-memory/` — what happened, session by session

## The convention

Every substantial working session in this repo ends with **one new file** here:

```
docs/session-memory/YYYY-MM-DD-<short-slug>.md
```

e.g. `2026-08-12-repo-understanding-and-restructure.md`,
`2026-09-03-pipeline-integration-stage5.md`.

One file per session. Do not edit previous sessions' files — if an earlier conclusion turns
out to be wrong, say so in the new file and link back to the old one. If two sessions
happen on one day, add a suffix: `2026-09-03-b-...`.

## Required sections

```markdown
# YYYY-MM-DD — <title>

**Session goal:** one line — what this session set out to do.

## What was done
Concrete actions, in order. Paths, commands, commit hashes.

## Decisions made
Each decision with the reason behind it. A decision without a reason is not a decision,
it's a coincidence.

## Open questions
Things you did not resolve. Be specific enough that the next person can pick them up.

## Next steps
Ordered, actionable. The first item should be the one to start with.
```

## Why this exists

This is a multi-month research project worked on in bursts, by more than one person, and
increasingly with AI assistants that start every session with zero memory of the last one.
Without these files, each session re-derives the same context — and the repo's own root
`README.md` spent three months claiming that finished models were still "in progress"
precisely because nobody had a habit of writing down what changed.

Session memory is for **narrative and context** (why we did it, what we tried, what we are
unsure about). Numeric results belong in `docs/results/RESULTS_LOG.md`, not here. It is
normal for one session to produce both: a log entry for the result and a memory file for
the story around it.

## Reading order

Newest file first. `2026-08-12-repo-understanding-and-restructure.md` is the seed example
and also documents the restructure that produced the current repo layout.

---

**Publication target and grading criteria:** `../../transfer.md` §5.
