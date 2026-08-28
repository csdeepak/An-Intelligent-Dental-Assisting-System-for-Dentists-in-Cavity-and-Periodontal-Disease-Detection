#!/usr/bin/env python
"""
Text-reuse check for the manuscript against this project's own documents.

WHAT THIS IS, AND IS NOT
------------------------
This is **not** a plagiarism service. It cannot see the published literature, so it
cannot tell you whether a sentence matches a paper none of us has read. Your
institution will run Turnitin or iThenticate and that check is the one that counts.

What it *does* find is the reuse risk that is actually under our control and that
originates here: the manuscript was drafted from `PAPER_MATERIAL.md`, and the same
authors have a prior survey paper in this repository. Verbatim carry-over from either
is exactly what a similarity report flags, and unlike the literature it is fixable
before submission.

METHOD
------
Word-level n-gram matching after normalisation (case, punctuation, LaTeX markup and
numbers stripped). Any shared span of >= MIN_NGRAM words is reported with its source.
Numbers are normalised to a placeholder so that "0.443" and "0.488" do not
artificially break an otherwise matching sentence -- a shared sentence with a
different number in it is still a shared sentence.

Short technical collocations ("panoramic radiographs", "confidence intervals") will
always match and are noise. The signal is a long span: 10+ words of identical prose
is a sentence someone wrote once and pasted twice.
"""

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MIN_NGRAM = 10          # words; below this, matches are ordinary technical phrasing


def normalise(text):
    text = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", text)   # latex macros
    text = re.sub(r"[%#$&_^{}~]", " ", text)
    text = re.sub(r"\d+(\.\d+)?", " NUM ", text)
    text = re.sub(r"[^a-zA-Z ]", " ", text)
    return [w for w in text.lower().split() if w]


def ngrams(words, n):
    return {" ".join(words[i:i + n]): i for i in range(len(words) - n + 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", type=Path, default=REPO / "paper/paper.txt")
    ap.add_argument("--min-ngram", type=int, default=MIN_NGRAM)
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    sources = {
        "PAPER_MATERIAL.md": REPO / "docs/results/PAPER_MATERIAL.md",
        "RESULTS_LOG.md": REPO / "docs/results/RESULTS_LOG.md",
        "model_metrics.md": REPO / "docs/results/model_metrics.md",
        "transfer.md": REPO / "transfer.md",
        "manuscript.md (own draft)": REPO / "docs/paper/manuscript.md",
        "draft_spine.md (own draft)": REPO / "docs/paper/draft_spine.md",
        "SURVEY PAPER (prior work)": REPO / "Survey Paper Latex folder/conference_101719.tex",
    }

    pw = normalise(args.paper.read_text(encoding="utf-8", errors="replace"))
    print(f"manuscript: {len(pw):,} normalised words\n")

    findings = []
    for name, path in sources.items():
        if not path.exists():
            print(f"  {name}: NOT PRESENT, skipped")
            continue
        sw = normalise(path.read_text(encoding="utf-8", errors="replace"))
        # grow matches greedily from each seed n-gram
        seeds = ngrams(sw, args.min_ngram)
        i = 0
        longest = {}
        while i <= len(pw) - args.min_ngram:
            key = " ".join(pw[i:i + args.min_ngram])
            j = seeds.get(key)
            if j is None:
                i += 1
                continue
            n = args.min_ngram
            while (i + n < len(pw) and j + n < len(sw) and pw[i + n] == sw[j + n]):
                n += 1
            longest[" ".join(pw[i:i + n])] = n
            i += n
        for span, n in sorted(longest.items(), key=lambda x: -x[1]):
            findings.append((n, name, span))

    if not findings:
        print(f"No shared spans of >= {args.min_ngram} words against any source.")
        return 0

    findings.sort(key=lambda x: -x[0])
    print(f"{len(findings)} shared span(s) of >= {args.min_ngram} words, longest first:\n")
    for n, name, span in findings[:args.top]:
        flag = "  <-- REVIEW" if n >= 20 else ""
        print(f"[{n:3d} words] {name}{flag}")
        print(f"    {span[:250]}\n")

    worst = findings[0][0]
    print("=" * 72)
    print(f"longest shared span: {worst} words")
    if worst >= 25:
        print("ACTION: rewrite the longest spans. A quarter-sentence is fine; a whole")
        print("paragraph carried over from a prior paper is what gets flagged.")
    else:
        print("No span long enough to read as a copied paragraph.")
    print("\nNOTE: this checks THIS REPOSITORY only. It is not a literature check and")
    print("is not a substitute for Turnitin/iThenticate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
