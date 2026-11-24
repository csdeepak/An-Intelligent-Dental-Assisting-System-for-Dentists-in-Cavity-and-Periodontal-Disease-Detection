# Citation audit, 2 Nov 2026 — academic-research-skills method

Record of the citation pass logged in `docs/results/RESULTS_LOG.md` (2026-11-02). It applies the
citation-verification method of the open-source academic-research-skills suite
(`https://github.com/Imbad0202/academic-research-skills`, commit `a41f3b2`, v3.24.1, CC BY-NC 4.0)
to the ten-page mentor draft (`paper/paper.md`) and to `paper/source.bib`.

## Method

1. **Existence, four indexes.** `verify_refs.py` runs the suite's own resolver clients
   (`crossref_client.py`, `openalex_client.py`, `semantic_scholar_client.py`, `arxiv_client.py`,
   unmodified, standard library only) on every entry of a `.bib` file: DOI or arXiv-ID lookup with
   a 0.70 title cross-check, then an exact-title fallback. Classification follows the suite's C-V6
   rule: `true` if any index matches; `false` only when a DOI or arXiv ID provably fails;
   otherwise `unresolvable` (a coverage gap, not a fabrication).
2. **Retraction and correction notices.** Crossref `works?filter=updates:<doi>` for every DOI.
3. **Metadata.** Title similarity, year and first author against the Crossref record; volume,
   issue and pages read from Crossref (or OpenAlex / Europe PMC where Crossref has none).
4. **Claim faithfulness.** `abstracts.py` fetches each cited work's abstract (OpenAlex inverted
   index, Europe PMC, arXiv); full text was read where the abstract was silent (Zancan et al.,
   Europe PMC PMC12633937; Bizjak and Robič, the journal's PDF; the ECE attribution in Guo et al.
   2017, Sec. 2). Each sentence in the draft that cites a work was checked against that text.
5. **New entries.** `crossref_to_bib.py` writes BibTeX from the Crossref record, so authors,
   volume and pages are not transcribed by hand.
6. **Numbers.** `trace_numbers.py` checks every number in `paper/paper.md` against `paper/main.tex`,
   the saved run files, and the cited works' own text.

## Files

| File | What it holds |
|---|---|
| `draft_refs.json` | the 23 references of the draft as it stood on 28 Oct |
| `sourcebib_refs.json` | all 86 entries of `paper/source.bib` before the fixes |
| `cand_refs.json` | the 19 candidate new citations (14 adopted) |
| `final_refs.json` | the 36 references of the final ten-page draft |
| `claim_abstracts.json`, `new_abstracts.json` | the abstracts the claims were checked against |
| `candidates.bib` | the candidate entries as first written (before Crossref generation) |

## Re-running

```
git clone https://github.com/Imbad0202/academic-research-skills.git <dir>
ARS_SCRIPTS=<dir>/scripts python -I verify_refs.py paper/ieee/references.bib out.json
python -I trace_numbers.py <repo root>
```

`abstracts.py` and `crossref_to_bib.py` take `key=doi:<doi>` / `key=arxiv:<id>` and `key=<doi>`
arguments. All network calls go to public APIs (Crossref, OpenAlex, Semantic Scholar, arXiv,
Europe PMC) without an e-mail address.
