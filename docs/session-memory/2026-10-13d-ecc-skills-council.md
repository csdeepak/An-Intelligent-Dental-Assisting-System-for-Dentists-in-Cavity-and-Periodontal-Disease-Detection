# 2026-10-13d — Council: which third-party agent skills help this paper

**Session goal:** the user asked to download from `github.com/affaan-m/ecc` every skill needed
to make the paper publishable, to update the global `CLAUDE.md`, and to council it.

Run on the macOS clone, late on 13 Oct. **Nothing in the pipeline, the results or the manuscript
changed.** Two documents in this repo were edited. The installation is in the user's own
`~/.claude/`, outside the repo, on this machine only.

## What was done

### 1. Facts first

- The URL redirects to `affaan-m/ECC`: MIT licence, 311 skills, 71 agents, hooks, installers
  and a plugin manifest. Pinned at commit `b92f181b3b748d1abbc2afd94af6aa7d8c8fca29`.
- Already installed from it: `mle-workflow` and `pytorch-patterns`, byte-identical to upstream,
  and `mle-reviewer`, which the user had deliberately narrowed (no shell, on request only).
- Staged 38 candidate skills and 11 agents as text in the session scratchpad for review. Nothing
  was installed or executed at that point. A regex scan flagged shell installs, pushes, hook
  edits and key handling in about half of them.

### 2. The council

Three independent read-only members; none saw another's report.

| Seat | Lens | Model | Recommended |
|---|---|---|---|
| 1 | Security and supply chain | Opus | The two rubric-only scientific skills as they are; the PubMed one with its key-reading script cut |
| 2 | Relevance and cost | Opus | Almost nothing: at most the scholar-evaluation rubric, on request |
| 3 | Integration and wording | Sonnet | The three research skills, globally, behind a five-line routing block |

**Consensus (3 of 3)**

- **No hostile content was found** in the files read in full (21 skills, 10 agents by Seat 1).
- **No skill makes this paper publishable.** What is left is writing and decisions.
- **Not the repository's installer, plugin or hooks.** Not the engineering-hygiene set as a
  whole. Not the healthcare, open-source-release, verification or documentation-governance
  skills. Not any reviewer agent. **Never overwrite the user's `mle-reviewer`.**
- The scholar-evaluation rubric is worth having.

**Why the rest was refused** — each would misfire here or break one of the user's own rules:

| Refused | Reason |
|---|---|
| `tdd-workflow`, `python-testing`, `verification-loop` | Mandate a test-first cycle and 80% coverage, commit at each stage, and grep key-bearing lines into the conversation |
| `opensource-pipeline` and its sanitizer | Rewrites git history — the pre-registration hashes — and ends in a public push; its scan skips the base64 content that the notebook-embedded Tufts pixels are |
| `security-scan`, `search-first`, `strategic-compact` | Install global packages, edit `settings.json`, add hooks |
| `deep-research`, `security-review` (ECC's) | Collide with built-in skills of the same names |
| Healthcare skills | Database access control and drug-interaction gates; nothing on image de-identification |
| `santa-method`, `living-docs-governance` | Duplicate the user's council and this repo's own document rules |
| Agents (`python-reviewer`, `code-reviewer`, others) | "MUST BE USED" triggers with shell or write access |
| `benchmark`, `benchmark-methodology`, `article-writing` | Web performance, marketing and blog writing, despite the names |

**Dissent**

| Point | Positions | Chair |
|---|---|---|
| The literature-review skill | Seats 1 and 3: install. Seat 2: no — it defaults to a systematic review and would turn a one-sentence softening into a project | **Installed, on request only.** It is five kilobytes of procedure with no commands in it. The harm Seat 2 names needs it to fire unasked; the routing line prevents that |
| The PubMed skill | Seat 1: with the script removed. Seat 3: unedited, with a line forbidding key use. Seat 2: no, it duplicates the paper-search tools | **Installed with Seat 1's cut.** A logged, free, repeatable query is something the paper-search tools do not give. An instruction that is not in the file cannot be followed by mistake |
| Scope | Seat 1: in the project, so git shows tampering. Seats 2 and 3: global | **Global.** The user asked for the global file, the collaborator was not consulted, and the repo may be published. Tamper evidence is kept another way: a provenance note with hashes beside each file |

### 3. What the chair verified

- The three files against the repository's own git blob hashes at the pinned commit: all match.
  Each skill is a single file upstream.
- Seat 1's line numbers for the PubMed cut: exact.
- I read the three files end to end myself before installing them.
- The routing text, blind: two models were given the proposed global file, the skill list and
  six prompts, without the expected answers. Round one — one seat failed on a rate limit; the
  other routed all six correctly and named four unclear phrases. Reworded. **Round two, Sonnet
  and Opus: six of six each**, including the two prompts that must not trigger a new skill.
  Four further small wording fixes followed, none structural.

### 4. Applied

- Backup: `~/.claude/CLAUDE.md.bak-2026-10-13`.
- Installed under `~/.claude/skills/`: `scientific-thinking-scholar-evaluation` and
  `scientific-thinking-literature-review`, byte-identical to upstream;
  `scientific-db-pubmed-database` with 35 lines removed and none added. Each folder has a
  `PROVENANCE.md` with the commit and both hashes.
- Global `CLAUDE.md`: one section of five lines, "Research papers", after the web-reading table.
  77 lines became 83. A diff against the backup shows nothing else.
- In this repo: `docs/paper/SUBMISSION_TODO.md` and `transfer.md`.

## Decisions made

- **Three files, not thirty.** The request was for everything needed. The council's finding is
  that very little is, and I installed what survived rather than what was asked for by count.
- **Text only.** No script, hook, installer, plugin or agent came across. Nothing from the
  repository was executed.
- **The skills fire when asked, not on their own.** The user's file is strict about that for
  the skills it already has, and the user also does frontend and game work on this machine.
- **I edited one third-party file and left two alone**, and wrote down which and how. Leaving a
  key-reading script in place and forbidding its use one file away is a weaker control than
  removing it.
- **A gap went into the submission list instead of being papered over.** No skill here fills a
  reporting checklist. `PUBLICATION_STRATEGY.md` calls CLAIM 2024 the primary one for this paper
  and the submission list had never tracked it.

## Open questions

- Do the three skills load and route as intended in a fresh session? They cannot be seen from
  the session that installed them.
- Will the mentor want the "49 papers" claim counted or softened? Counting is now tooled;
  softening needs no tool.
- Does the target conference ask for a reporting checklist?
- Carried over: everything in `docs/session-memory/2026-10-13c-stage4a-adoption.md`.

## Next steps

1. The user commits the two edited documents and this file.
2. In a new session, try: "review the Methods section of paper/main.tex like a referee".
3. The six-page cut, then that referee pass over it, then the mentor.
4. The CLAIM 2024 checklist, if the venue or a later journal version wants it.

## Undo

```
rm -r ~/.claude/skills/scientific-thinking-scholar-evaluation \
      ~/.claude/skills/scientific-thinking-literature-review \
      ~/.claude/skills/scientific-db-pubmed-database
cp ~/.claude/CLAUDE.md.bak-2026-10-13 ~/.claude/CLAUDE.md
```
