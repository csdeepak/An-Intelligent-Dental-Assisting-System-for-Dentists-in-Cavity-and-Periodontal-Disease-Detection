# Working flowchart — research_paper/ (session of 23 Nov 2026)

The plan this session follows. It was written after reading `CLAUDE.md`, `transfer.md`, the newest
session memory (`docs/session-memory/2026-10-28-mentor-draft-real-figures.md`), the round-1 review
files under `paper/ieee/review/`, and the research_writing_skill (RCE) on `main` at `3e4411f`.

## Starting state (verified, not assumed)

| Fact | Source |
|---|---|
| `main` = `origin/main` = `851f089`, working tree clean | `git fetch`, `git rev-list` |
| Newest manuscript: 10-page IEEE draft, `paper/paper.md` → `paper/ieee/main.tex/pdf`, review round 1 applied (14 done, 5 partial, 2 open) | `paper/ieee/review/2026-11-02_response_round1.md` |
| Maintained long manuscript: `paper/main.tex`, 16 pp, 215 claims checked by `scripts/verify_paper_numbers.py` | `transfer.md` §1 |
| Pipeline defaults: Stage 1 `models/15/arm3c_best.pt` (since 11 Oct), Stage 3a `models/16` (since 4 Sep), Stage 4a `models/18/seed42` (since 13 Oct) | `scripts/run_inference.py` `DEF_*`, `models/README.md` |
| Ningxia raw images (`D:\nangxia_dataset`) not attached → the per-type Ningxia re-run (round-1 item 1) stays blocked | `ls /d/` empty |
| RCE: `main` is the unreleased 0.5.0 candidate (P0–P7, gates G1/GL/G3/GI/G4/G5); v0.4.0 is the release | skill `README.md` |
| PaperOrchestra: LLM-API generator (Gemini/OpenAI keys, Semantic Scholar key), raw materials → LaTeX | its `README.md` |

## Flowchart

```mermaid
flowchart TD
    A[Read CLAUDE.md, transfer.md, memory, session notes] --> B[git fetch: clone in sync]
    B --> C[Run checks: pytest, verify_invariants, verify_paper_numbers]
    C --> D[Phase 1-2: repository_audit.md<br/>architecture, checkpoints vs DEF_*, git ls-files,<br/>post-11-Oct changes, doc conflicts]
    D --> E{Docs agree with<br/>code + artefacts?}
    E -- no --> E1[Record conflict in audit;<br/>never reconcile silently]
    E -- yes --> F
    E1 --> F[Phase 3: RCE 0.5.0 on main<br/>.rcs/ evidence map, claim map, spine]
    F --> G[G1 validate_artifacts]
    G --> H[Phase 4: PaperOrchestra evaluation<br/>decide: adopt / borrow / decline]
    H --> I[Phase 5: literature<br/>reuse 2 Nov citation audit + new targeted search<br/>areas 1-12, verify on Crossref/OpenAlex]
    I --> J[GL verify_citations --online]
    J --> K[Phase 6-8: novelty, experimental verification,<br/>clinical validity — from saved artefacts only]
    K --> L{New experiment<br/>needed?}
    L -- yes, data on hand, no protected asset touched --> L1[Propose + pre-register;<br/>ask before running]
    L -- blocked / costly --> L2[Record as open; limitation in paper]
    L -- no --> M
    L1 --> M
    L2 --> M[Phase 9-10: revise paper.md (tagged)<br/>results first, abstract last; figures from saved data]
    M --> N[G3 lint_draft + verify_numbers]
    N --> O[Build paper.tex via md_to_ieee.py; pdflatex x2 + bibtex]
    O --> P[Phase 11: references.bib check<br/>BibTeX keys = in-text keys]
    P --> Q[Phase 12: 3 isolated reviewers A/B/C<br/>separate contexts, read only the PDF + packet]
    Q --> R[Dispositions for every finding; revise]
    R --> S[GI integrity gate: isolated VERIFIER + integrity_check.py]
    S --> T{All gates<br/>tool-passed?}
    T -- no --> R
    T -- yes or documented-unresolved --> U[Phase 13: final PDF, publication_readiness.md, README.md]
    U --> V[CLAUDE.md duties: RESULTS_LOG entry, PAPER_MATERIAL §9,<br/>session memory, transfer.md header]
    V --> W[Report: tools used, gates passed/failed, open issues first]
```

## Rules carried through every box

- Never invent a number, citation, experiment or clinical fact; an untraced number is
  `[UNVERIFIED]` or removed.
- `paper/` is not overwritten; all new output goes to `research_paper/`.
- No training, no tuning, no pass over Ningxia or the Tufts test split (`transfer.md` §4).
- A gate is "passed" only on a fresh tool report with 0 errors.
- The AUTHOR (this session) never reviews or verifies its own draft: reviewers and the VERIFIER run
  in separate agent contexts that see only the review packet.
- No commit or push without the owner's request.
