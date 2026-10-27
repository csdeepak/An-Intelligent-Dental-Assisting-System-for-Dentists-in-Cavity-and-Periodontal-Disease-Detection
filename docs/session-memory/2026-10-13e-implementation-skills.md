# 2026-10-13e — Implementation-side skills from the same repository, checked and trimmed

**Session goal:** the user asked to also install the skills needed for implementation work, and
to check them first.

Run on the macOS clone, late on 13 Oct. **Nothing in this repo's code, results or manuscript
changed.** The installation is in the user's own `~/.claude/`, on this machine only. Follows
`2026-10-13d-ecc-skills-council.md`; no new council was run — the review of an hour earlier had
already covered these files, and I read each candidate myself.

## What was done

1. **Looked at seventeen more skills** that had not been staged before, at the same pinned
   commit (`b92f181b…`). None fits: a GPU marketplace's own tooling, data-pipeline and
   agent-loop skills, test and regression registries that would run beside this repo's own
   rules, and two that install hooks.
2. **Read the implementation candidates in full**: the pytest, Python-idiom, Docker and
   error-handling skills, and the review agents.
3. **Found the global `CLAUDE.md` restored to its backup** part-way through — the section added
   in the previous session was gone, the skill folders were not. Asked. The user said it was an
   accident, to put it back, and to install all three recommended items.
4. **Blind-tested the new routing line** on two models with six prompts. Both routed all six as
   intended: pytest work to the pytest reference after the Karpathy skill; a plain bug fix to
   neither; no test-first cycle and no coverage target; the review agent only when that review
   is asked for. Three unclear phrases they named were reworded.
5. **Installed, each verified against the repository's own content hash first:**

   | Item | Kept | Removed before installing |
   |---|---|---|
   | skill `python-testing` | pytest fixtures, parametrisation, mocking, markers, configuration | the trigger "writing new Python code (follow TDD…)", the section mandating a test-first cycle with 80% and 100% coverage, two matching bullets — 37 lines |
   | skill `docker-patterns` | Dockerfile hardening, secrets, volumes, networking, `.dockerignore`, debugging | the repository's own installer-harness section, which includes a global `npm install` and a CLI login — 205 lines |
   | agent `silent-failure-hunter` | its checklist for swallowed errors and silent fallbacks | shell access; and it now says "use only on explicit request" |

6. **Global `CLAUDE.md`:** the "Research papers" section restored exactly as tested, and one
   line added to the code section. 77 lines became 84. The user's `mle-reviewer` is untouched.

## Second pass — the user asked for the check again, properly

The first check read the pytest and Docker skills by their openings, headings and flagged lines.
The user asked for it once more, carefully. This time every line of what is installed was read,
the files on disk were re-verified against their recorded hashes, and the candidates that had
been judged by description were read.

**Found in the installed files, and removed:**

| File | Found | Why it mattered |
|---|---|---|
| `python-testing` | Coverage flags in both configuration examples (`--cov=mypackage`, two `--cov-report` lines) | This project has no `pytest-cov`. Copied into a config, they make every test run fail with an unknown-argument error until a new dependency is installed |
| `python-testing` | `--disable-warnings` in the same example | Hides warnings in a repo whose recurring fault is the quiet failure |
| `python-testing` | "Reviewing Python test coverage" as a trigger, a "run with coverage" command, a reference-table row, and "TDD methodology" in the opening sentence | Left over from the mandate removed on the first pass |
| `docker-patterns` | `docker compose down -v` and `docker system prune` in a list of clean-up commands | The first deletes volumes; the second deletes unused images and containers across the machine |

Against upstream the pytest file is now 50 lines shorter and the Docker file 207.

**Found and not removed.** About three fifths of the Docker skill is a Node.js, Postgres and
Redis web stack. The part that applies to a single Python container is the hardening list, the
secrets section, the ignore-file example and the debugging commands. It was installed on the
user's explicit choice and it is harmless; it is also mostly beside the point for this project,
and I said so.

**Confirmed by reading, not by description:**

| Candidate | What it actually is | Verdict |
|---|---|---|
| `verification-loop` | Node build, lint and test commands with an 80% coverage target; its "security scan" prints lines containing key-like strings; says to run every fifteen minutes | No |
| `coding-standards` | Twenty-two TypeScript examples, React and REST sections, no Python | No |
| `ai-regression-testing` | Vitest tests for Next.js API routes | No |
| `eval-harness` | Pass rates for AI coding tasks — not evaluation of ML models | No |
| `deployment-patterns` | Rolling, blue-green and canary releases, Kubernetes probes, CI pipelines | No |
| agent `pytorch-build-resolver` | Fixes PyTorch crashes; has write and shell access and re-runs the failing script | No — in this repo a training run may be a pre-registered single run |
| agent `pr-test-analyzer` | Reviews whether a pull request's tests cover its changes | No — this repo has no pull requests |

One thing the second pass turned up about a refusal made on the first: `black` is installed in
this machine's Python environment. The Python-idiom skill's instruction to run `black .` would
have run here.

## Third request — a `/mle-review` command

The user asked that typing `/mle` offer a review option beside `/mle-workflow`. The reviewer
existed only as an agent (`~/.claude/agents/mle-reviewer.md`), and agents do not appear in the
slash menu.

- Added `~/.claude/skills/mle-review/SKILL.md`, written here, not taken from any repository. It
  tells the session to settle the scope, write a self-contained brief, run one `mle-reviewer`
  agent in the foreground, check the serious findings against the cited lines, and report.
  Findings only.
- `disable-model-invocation: true`: only the user can start it, which keeps the global rule that
  the reviewer runs on request. The agent file and the global `CLAUDE.md` were not touched.
- The brief is written by the session because the agent has no shell: it cannot run `git diff`,
  and it sees none of the conversation.
- Checked: the frontmatter parses, the name matches the folder, the agent it calls exists. **Not
  checked: the slash menu itself**, which only the user can type into.

## Decisions made

- **Three, again, not a bundle.** What implementation needs was already there: the Karpathy and
  Ponytail rules, `pytorch-patterns`, `mle-workflow`, `mle-reviewer`, and the built-in code
  review. These three add reference material and one distinct review lens.
- **The Python-idiom skill was refused.** Its tooling section says to run `black .` and
  `isort .`. This repo has mixed line endings and a rule against blanket normalisers; a
  formatter run across it would touch every file. It also fires on every Python edit, where two
  rulesets already apply.
- **The second Python reviewer was refused.** It duplicates the built-in review and would raise
  type-hint and line-length findings against research scripts on every pass.
- **The review agent was kept** because this repo has the faults it looks for: the ML review of
  12 Oct found an unreadable image skipped without a word and a missing calibrator that
  silently changes the confidence a report prints.
- **Every third-party file was edited rather than fenced.** An instruction removed from a file
  cannot be followed by mistake.
- **I asked before touching the global file a second time.** It had been changed by someone
  else since I last wrote it, and re-applying over that would have been overriding a decision I
  could not see.

## Open questions

- Does the pytest reference earn its place? This repo's 184 tests are plain and consistent, and
  were written without it.
- Carried over from the previous two session files.

## Next steps

1. Nothing in this repo needs committing for this session except this file and one line in
   `transfer.md`.
2. The six-page draft is still the next real step.
