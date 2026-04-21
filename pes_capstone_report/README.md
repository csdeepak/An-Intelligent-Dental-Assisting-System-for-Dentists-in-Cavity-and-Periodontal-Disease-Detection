# PES University — Capstone Project Report LaTeX Template

Template for the **UE23CS320B Capstone Project Phase 2** report, styled per
the official PES University guidelines (A4, 2 cm margins, Times New Roman,
1.5 line spacing, chapter-wise numbering, PES header/footer rules).

Designed to be reused across phases — the same class file (`pesreport.cls`)
is the style engine; change only `main.tex` metadata and the files under
`chapters/` to repurpose it for Phase 3 or a different project.

## Project structure

```
.
├── main.tex                 ← you edit metadata + include chapters here
├── pesreport.cls            ← style engine; do not edit unless changing style
├── figures/                 ← drop .png / .jpg / .pdf images here
└── chapters/
    ├── 01_introduction.tex
    ├── 02_literature.tex
    ├── 03_architecture.tex
    ├── 04_methodology.tex
    ├── 05_implementation.tex
    ├── 06_results.tex
    ├── 07_conclusion.tex
    └── 08_references.tex
```

## Using it on Overleaf (recommended)

1. On Overleaf, click **New Project → Upload Project** and upload this folder
   as a zip. Overleaf will unpack it.
2. In the Overleaf editor, make sure **Menu → Compiler** is set to `pdfLaTeX`
   and **Main document** is `main.tex`.
3. Click **Recompile**. The PDF appears on the right.

## Using it locally

Requires a TeX Live distribution with `pdflatex`.

```bash
pdflatex main.tex      # first pass
pdflatex main.tex      # second pass — resolves TOC / refs
pdflatex main.tex      # third pass — resolves LOF / LOT page numbers
```

Run three times because the TOC, List of Figures, and List of Tables each
need one pass to stabilise after content moves.

## Filling in your project metadata

Open `main.tex` and edit the block between `PROJECT METADATA` comments.
These commands drive every front-matter page — title, certificate, declaration.

```latex
\projecttitle{Your Real Project Title}
\projectid{PW26_XYZ_NN}
\guidename{Dr. Your Guide Name}
\guidedesignation{Professor, Department of CSE}

\addteammember{Full Name 1}{PES1UG23CSXXX}
\addteammember{Full Name 2}{PES1UG23CSXXX}
% ... up to ~6 members

\addteamsign{Full Name 1}{PES1UG23CSXXX}   % same list, for declaration page
\addteamsign{Full Name 2}{PES1UG23CSXXX}
```

Also edit the **Acknowledgement** paragraph in `main.tex` directly —
it's meant to be customised per project.

## Writing your chapters

Each chapter lives in its own file under `chapters/`. Every file begins with
`\chapter{Name}` and contains placeholder text in `\textit{[Replace...]}`
form as a writing guide.

- Replace the italic placeholders as you go.
- Chapter / section / subsection numbering is automatic (1, 1.1, 1.1.1 …).
- Figure and table numbering is **chapter-wise** — `Figure 3.1`, `Figure 3.2`,
  `Table 4.1`, and so on.
- Equations are numbered `(1.1)`, `(1.2)` with chapter-wise reset.

### Adding a figure

Drop the image file into `figures/`, then in your chapter:

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\linewidth]{figures/my_diagram.png}
  \caption{What this figure shows.}
  \label{fig:my-diagram}
\end{figure}
```

Reference it in text as `Figure~\ref{fig:my-diagram}`.

### Adding a table

```latex
\begin{table}[htbp]
  \centering
  \caption{Comparison of models.}
  \label{tab:comparison}
  \begin{tabular}{@{}lcc@{}}
    \toprule
    Model & Accuracy & F1 \\
    \midrule
    Baseline & 0.80 & 0.78 \\
    Ours     & 0.92 & 0.91 \\
    \bottomrule
  \end{tabular}
\end{table}
```

### Citing references

The template ships with a manual bibliography in `chapters/08_references.tex`.
Add entries as:

```latex
\bibitem{authorYearKey}
A.~Author, B.~Author, and C.~Author,
``Title of the paper,''
\textit{Journal Name}, vol.~XX, no.~Y, pp.~ZZZ--ZZZ, Month~Year,
doi: 10.XXXX/XXXXXX.
```

Cite in your text with `\cite{authorYearKey}` — it renders as `[N]`, where N
is the sequential number assigned in the order citations first appear.

## Style locked by the class

You do not need to touch any of the following — they are enforced by
`pesreport.cls` to match the guidelines:

| Setting               | Value                                       |
|-----------------------|---------------------------------------------|
| Paper                 | A4                                          |
| Margins               | 2.0 cm on all four sides                    |
| Line spacing          | 1.5                                         |
| Font family           | Times New Roman (`mathptmx`)                |
| Body text             | 12 pt, justified                            |
| Chapter title         | 18 pt, bold, centered                       |
| Section title         | 16 pt, bold, left-aligned                   |
| Subsection title      | 14 pt, bold, left-aligned                   |
| Figure / table / eqn. | Chapter-wise numbering (e.g. Figure 3.2)    |
| References            | `[N]` numbered, in order of first citation  |
| Chapter opening page  | No header, footer only                      |
| Continuation pages    | Running header + footer (from Introduction) |
| Front matter          | Plain — no header, no footer                |

## Common issues

**TOC or references show `??`** — run `pdflatex` twice more. LaTeX resolves
cross-references iteratively.

**A figure isn't showing up** — make sure the file path in
`\includegraphics{figures/...}` exactly matches the filename, including case.
Overleaf is case-sensitive even when your local filesystem isn't.

**The template won't compile after I edited `pesreport.cls`** — revert your
changes to the class file. The public-facing API lives in `main.tex`; the
class is for style only and is easy to break. If you truly need a style
change, back up the class first.

## License / attribution

Template authored as a PES University capstone report scaffold. No warranty.
You are free to adapt it for your own reports.
