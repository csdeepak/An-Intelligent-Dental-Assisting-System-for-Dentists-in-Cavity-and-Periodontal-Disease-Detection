# Tooling decisions — RCE version and PaperOrchestra

Phases 3 and 4 of the brief.

## 1. Research Communication Engine (the owner's skill)

| Fact | Source |
|---|---|
| Local clone was on branch `rce-adaptive-representation`, clean, 24 commits behind `origin/main` | `git status`, `git rev-list` |
| Switched to `main` and fast-forwarded to `3e4411f` (4 Nov 2026); the feature branch is kept | `git checkout main; git pull --ff-only` |
| `main` = the unreleased **0.5.0 candidate** (P0–P7, gates G1, GL, G3, GI, G4, G5, VERIFIER, panel); the latest **release** is `skill-v0.4.0` | skill `README.md`, tags |
| `skill/SKILL.md` frontmatter still reads `version: 0.4.0` on `main` | file |

**Decision: use the `main` candidate, and only its tools.** The brief asks for a literature gate,
an independent integrity check and panel-style review; those exist only in 0.5.0 (GL, GI,
`integrity_check.py`, `verify_citations.py --online`). Every command run came from the one
checkout at `3e4411f`; nothing from v0.4.0 was mixed in. The cost: the candidate is unreleased, so
results are labelled "RCE 0.5.0 candidate @ 3e4411f" everywhere.

**Tools actually run, and their reports** (`research_paper/.rcs/audits/gates/`):

| Gate | Tool | Report |
|---|---|---|
| G1 artifacts | `validate_artifacts.py --project-root .` | `G1_validate.json` |
| GL citations | `verify_citations.py --online` then `--gate` | `GL_citations.json`; live run log `audit_runs/verify_citations_online_2026-11-23.txt` |
| G3 lint | `lint_draft.py --rcs` | `G3_lint.json` |
| G3 numbers | `verify_numbers.py --project-root .` | `G3_numbers.json` |
| GI integrity | `integrity_check.py collect` → isolated VERIFIER subagent → `integrity_check.py gate` | `GI_integrity.json` (see `integrity_check_report.md`) |

**Not run, and why:** G2 has no tool (the outline is the existing reviewed draft's, extended);
G4's `g4_check.py` needs the five-seat panel's schema-bound JSON, and this run used the three
reviewer perspectives the brief specified instead (`reviewer_report.md`) — G4 is therefore recorded
as *unverified*, not passed; G5's `claim_invariance.py` is run only if the post-review text changes
claims (see `integrity_check_report.md`). `rce_roles.py` was not used because no model is bound in
`.rcs/models.json`; the isolated roles ran as Claude Code subagents instead, which the skill allows
("each role runs in its own context: a subagent or a fresh session").

## 2. PaperOrchestra (google-research/paper-orchestra)

| Fact | Source |
|---|---|
| Multi-agent generator: outline, literature review, section writing, refinement, plotting → LaTeX | repo `README.md`; arXiv 2604.05018 abstract |
| Input: "unconstrained pre-writing materials (ideas and experimental logs)" + a LaTeX template | README `--raw_materials_dir`, `--latex_template_dir` |
| Needs API keys: Gemini (Vertex or API key) and/or OpenAI, plus a Semantic Scholar key | README `.env` block |
| Python 3.11 conda env; benchmark dataset not released | README |
| Evaluated on reverse-engineered materials from 200 AI-conference papers with human side-by-side preference | arXiv abstract |

**Decision: not used to generate or rewrite any text, figure or reference.** Reasons, in order:

1. **It writes from raw materials; this paper already exists and is evidence-locked.** Its value
   is turning logs into a first draft. Here every one of 403 numbers is traced and every citation
   live-verified; a regenerated draft would have to be re-traced from zero and would invite
   paraphrase drift in numbers, scopes and hedges — the failure RCE's gates exist to stop.
2. **Its literature agent searches and cites automatically**, which conflicts with RCE's rule that a
   search hit is a candidate, not a source, until verified with a support quote.
3. **Its plotting agent generates plots from code it writes.** The paper's figures are produced by
   repository scripts that assert each value against the saved evaluation; a generated plot would
   bypass that.
4. **It needs hosted LLM keys and sends the materials to them.** The project's materials include
   unpublished results and private-repository content; sending them out needs the owner's consent,
   which this brief did not give for that purpose.
5. **Its evaluation is preference on AI-conference papers**, not factual accuracy on a medical
   paper; nothing in it measures claim traceability.

**What was borrowed instead:** its agent decomposition (outline → literature → sections →
refinement) matches RCE's P2–P4 order already used here; no code or prompt was copied. If the
owner wants it tried, the safe use is a *style-only* refinement pass on the finished, tagged draft,
followed by RCE's `claim_invariance.py` to prove no claim changed — a separate decision.
