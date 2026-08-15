%% pesreport.cls
%% PES University Capstone Project Report class
%% Implements the UE23CS320B Capstone Phase-2 (and future phases) report guidelines:
%%   A4 paper, 2 cm margins all sides, 1.5 line spacing, Times New Roman family.
%%   Chapter title 18 pt centered, Section 16 pt bold left, Subsection 14 pt bold left,
%%   Body 12 pt justified. Chapter-wise figure/table/equation numbering.
%%   PES header/footer rules: no header on chapter opening pages; footer on chapter
%%   opening pages; headers & footers begin at the Introduction chapter.
%%   Numbered IEEE-style references via [1], [2], ...
%%
%% Usage in main.tex:
%%   \documentclass{pesreport}
%%
%% This class is intentionally self-contained — uses only packages available on
%% Overleaf by default. Compile with pdflatex.
%% -----------------------------------------------------------------------------
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{pesreport}[2026/04/19 v1.0 PES University Capstone Project Report class]

% ---- Base class: report (gives us \chapter, which is what we want) -----------
\LoadClass[12pt,a4paper,oneside]{report}

% ---- Core packages -----------------------------------------------------------
\RequirePackage[a4paper,top=2.0cm,bottom=2.0cm,left=2.0cm,right=2.0cm]{geometry}
\RequirePackage{mathptmx}           % Times Roman for text and math (pdflatex-safe)
\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{setspace}           % line spacing
\RequirePackage{titlesec}           % chapter/section title formatting
\RequirePackage{fancyhdr}           % headers & footers
\setlength{\headheight}{14pt}       % silence fancyhdr's 13.6pt warning
\RequirePackage{graphicx}           % \includegraphics
\RequirePackage{caption}            % caption formatting
\RequirePackage{array}
\RequirePackage{tabularx}
\RequirePackage{booktabs}
\RequirePackage{longtable}
\RequirePackage{amsmath,amssymb}
\RequirePackage{xcolor}
\RequirePackage{hyperref}           % must be loaded late
\RequirePackage{tocloft}            % TOC / LOT / LOF formatting
\RequirePackage{enumitem}
\RequirePackage{ragged2e}
\RequirePackage{etoolbox}           % \patchcmd
\RequirePackage{lastpage}
\RequirePackage{textcomp}

% ---- Line spacing: 1.5 -------------------------------------------------------
\onehalfspacing

% ---- Justified body by default -----------------------------------------------
% (LaTeX is justified by default; this is a reminder. Individual pages can
% switch to \centering / \RaggedRight as needed.)

% ---- Paragraph settings ------------------------------------------------------
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt plus 2pt minus 1pt}

% ---- Chapter-wise equation, figure, table numbering -------------------------
% (already the default for report class — explicit for clarity)
\numberwithin{equation}{chapter}
\numberwithin{figure}{chapter}
\numberwithin{table}{chapter}

% ---- Title formatting (titlesec) --------------------------------------------
% Chapter title — 18 pt, centered, bold. The word "CHAPTER N" appears above
% the title, centered. No extra vertical drop.
\titleformat{\chapter}[display]
  {\normalfont\centering\bfseries}
  {\fontsize{18}{22}\selectfont CHAPTER \thechapter}
  {10pt}
  {\fontsize{18}{22}\selectfont\MakeUppercase}
\titlespacing*{\chapter}{0pt}{-20pt}{30pt}

% Section — 16 pt bold, left aligned
\titleformat{\section}
  {\normalfont\fontsize{16}{19}\bfseries\raggedright}
  {\thesection}{1em}{}
\titlespacing*{\section}{0pt}{18pt}{8pt}

% Subsection — 14 pt bold, left aligned
\titleformat{\subsection}
  {\normalfont\fontsize{14}{17}\bfseries\raggedright}
  {\thesubsection}{1em}{}
\titlespacing*{\subsection}{0pt}{14pt}{6pt}

% Sub-subsection — 12 pt bold, left aligned (fallback for deeper nesting)
\titleformat{\subsubsection}
  {\normalfont\fontsize{12}{15}\bfseries\raggedright}
  {\thesubsubsection}{1em}{}
\titlespacing*{\subsubsection}{0pt}{10pt}{4pt}

% ---- Header / Footer ---------------------------------------------------------
% Rule set from the guidelines:
%   * No header on the first page of each chapter
%   * Footer appears on chapter opening pages (and elsewhere)
%   * Headers & footers begin at the Introduction chapter (not on front matter)
%
% We implement this with two fancyhdr page styles:
%   - "pescontent"  : used on chapters from Introduction onward (normal pages)
%   - "peschapter"  : used on the opening page of each chapter (no header,
%                      footer only). This is activated automatically by the
%                      report class's use of \thispagestyle{plain} at chapter
%                      start — we redefine "plain" to match "peschapter".

% Running header text is whatever the user sets in main.tex via
% \reporttitle{...}. Default fallback shown below.
\newcommand{\@reporttitle}{Capstone Project Report}
\newcommand{\reporttitle}[1]{\renewcommand{\@reporttitle}{#1}}

% Report logo configuration.
\newcommand{\@reportlogo}{}
\newcommand{\reportlogo}[1]{\renewcommand{\@reportlogo}{#1}}
\newcommand{\@headerlogosize}{0.85cm}
\newcommand{\headerlogosize}[1]{\renewcommand{\@headerlogosize}{#1}}
\newcommand{\@titlelogowidth}{0.23\textwidth}
\newcommand{\titlelogowidth}[1]{\renewcommand{\@titlelogowidth}{#1}}

\newcommand{\pesheaderlogo}{%
  \ifx\@reportlogo\@empty
  \else
    \includegraphics[height=\@headerlogosize]{\@reportlogo}%
  \fi
}

\newcommand{\pesrunningheader}{%
  \begin{minipage}[b]{0.78\textwidth}
    \small\itshape\raggedright \@reporttitle
  \end{minipage}%
}

% Footer template (identical on opening and non-opening pages):
%   | Dept. of CSE | <Month Range, Year> |  <page number>  |
% The period string is author-settable.
\newcommand{\@reportperiod}{Jan - May, 2026}
\newcommand{\reportperiod}[1]{\renewcommand{\@reportperiod}{#1}}

\newcommand{\@reportdept}{Dept. of CSE}
\newcommand{\reportdept}[1]{\renewcommand{\@reportdept}{#1}}

% Content page style — used for non-opening pages of chapters (from intro on)
\fancypagestyle{pescontent}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0.4pt}%
  \renewcommand{\footrulewidth}{0.4pt}%
  \fancyhead[L]{\pesrunningheader}%
  \fancyhead[R]{\pesheaderlogo}%
  \fancyfoot[L]{\small\@reportdept}%
  \fancyfoot[C]{\small\@reportperiod}%
  \fancyfoot[R]{\small\thepage}%
}

% Chapter opening page style
\fancypagestyle{peschapter}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0.4pt}%
  \renewcommand{\footrulewidth}{0.4pt}%
  \fancyhead[L]{\pesrunningheader}%
  \fancyhead[R]{\pesheaderlogo}%
  \fancyfoot[L]{\small\@reportdept}%
  \fancyfoot[C]{\small\@reportperiod}%
  \fancyfoot[R]{\small\thepage}%
}

% Front-matter (title page, certificate, declaration, etc.)
\fancypagestyle{pesfront}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0.4pt}%
  \renewcommand{\footrulewidth}{0.4pt}%
  \fancyhead[L]{\pesrunningheader}%
  \fancyhead[R]{\pesheaderlogo}%
  \fancyfoot[L]{\small\@reportdept}%
  \fancyfoot[C]{\small\@reportperiod}%
  \fancyfoot[R]{\small\thepage}%
}

% The report class calls \thispagestyle{plain} at the start of each chapter.
% Redefine "plain" to be our "peschapter" so opening pages get footer only.
\fancypagestyle{plain}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0.4pt}%
  \renewcommand{\footrulewidth}{0.4pt}%
  \fancyhead[L]{\pesrunningheader}%
  \fancyhead[R]{\pesheaderlogo}%
  \fancyfoot[L]{\small\@reportdept}%
  \fancyfoot[C]{\small\@reportperiod}%
  \fancyfoot[R]{\small\thepage}%
}

% Default page style for the whole document — overridden where needed.
\pagestyle{pescontent}

% ---- Caption formatting (figures and tables) --------------------------------
% Captions are bold, centered for figures; "Figure X.Y: title"
\captionsetup{labelfont=bf,font=small,justification=centering,labelsep=colon}
\captionsetup[table]{justification=centering,singlelinecheck=false}
\captionsetup[figure]{justification=centering,singlelinecheck=false}

% ---- TOC / LOT / LOF formatting ---------------------------------------------
\renewcommand{\contentsname}{TABLE OF CONTENTS}
\renewcommand{\listfigurename}{LIST OF FIGURES}
\renewcommand{\listtablename}{LIST OF TABLES}

% Make TOC/LOT/LOF headings look like the guideline: centered, bold, 16pt.
\renewcommand{\cfttoctitlefont}{\hfill\bfseries\fontsize{16}{19}\selectfont}
\renewcommand{\cftaftertoctitle}{\hfill}
\renewcommand{\cftloftitlefont}{\hfill\bfseries\fontsize{16}{19}\selectfont}
\renewcommand{\cftafterloftitle}{\hfill}
\renewcommand{\cftlottitlefont}{\hfill\bfseries\fontsize{16}{19}\selectfont}
\renewcommand{\cftafterlottitle}{\hfill}

% Chapter entries in TOC — bold, no leading dots on chapter lines (optional).
\renewcommand{\cftchapfont}{\bfseries}
\renewcommand{\cftchappagefont}{\bfseries}

% ---- Hyperref config (keep links quiet in print) -----------------------------
\hypersetup{
  colorlinks=false,
  pdfborder={0 0 0},
  bookmarksnumbered=true,
  bookmarksopen=true,
}

% ---- IEEE-style numbered bibliography ---------------------------------------
% We use the built-in unsrt-style reference list with square-bracket citations.
% Users can either:
%   (a) use \begin{thebibliography}{99} ... \bibitem{key} ... \end{thebibliography}
%       in References chapter directly (what the template does), OR
%   (b) switch to BibTeX with \bibliographystyle{IEEEtran}.
% Square brackets for \cite and the reference label:
\renewcommand{\@biblabel}[1]{[#1]}
\renewcommand{\@cite}[2]{[{#1\if@tempswa , #2\fi}]}

% ---- Helper macros: front-matter building blocks ----------------------------
% These are the authoring API used by main.tex so the user only edits text,
% never layout. If you need to change visual style site-wide, change it here.

% Metadata commands — set in main.tex preamble.
\newcommand{\@projecttitle}{<Title of the capstone project>}
\newcommand{\projecttitle}[1]{\renewcommand{\@projecttitle}{#1}}

\newcommand{\@projectid}{PW26\_}
\newcommand{\projectid}[1]{\renewcommand{\@projectid}{#1}}

\newcommand{\@coursecode}{UE23CS320B}
\newcommand{\coursecode}[1]{\renewcommand{\@coursecode}{#1}}

\newcommand{\@phasename}{Capstone Project Phase - 2}
\newcommand{\phasename}[1]{\renewcommand{\@phasename}{#1}}

\newcommand{\@phaseperiod}{January - May 2026}
\newcommand{\phaseperiod}[1]{\renewcommand{\@phaseperiod}{#1}}

\newcommand{\@phasesemester}{sixth}
\newcommand{\phasesemester}[1]{\renewcommand{\@phasesemester}{#1}}

\newcommand{\@guidename}{<Prof. Guide Name>}
\newcommand{\guidename}[1]{\renewcommand{\@guidename}{#1}}

\newcommand{\@guidedesignation}{Designation}
\newcommand{\guidedesignation}[1]{\renewcommand{\@guidedesignation}{#1}}

\newcommand{\@chairperson}{Dr. Shylaja S S}
\newcommand{\chairperson}[1]{\renewcommand{\@chairperson}{#1}}

\newcommand{\@registrar}{Dr. K S Sridhar}
\newcommand{\registrar}[1]{\renewcommand{\@registrar}{#1}}

% Team members — stored as a list. Each entry is {Name}{SRN}.
% Use \addteammember{Name}{SRN} in main.tex preamble (up to reasonable N).
\newcommand{\@teamlist}{}
\newcommand{\addteammember}[2]{%
  \g@addto@macro\@teamlist{\teammemberrow{#1}{#2}}%
}
\newcommand{\teammemberrow}[2]{#2 & #1 \\ }

% Team members as a two-column "SRN | Name" table for declaration/certificate.
\newcommand{\printteamtable}{%
  \begin{center}
  \begin{tabular}{@{}ll@{}}
  \@teamlist
  \end{tabular}
  \end{center}
}

% Team as name-only list (used in cover).
\newcommand{\@teamcoverlist}{}
\newcommand{\addteamcover}[2]{%
  \g@addto@macro\@teamcoverlist{\textbf{#1} \hfill \textbf{#2} \\}%
}

% Signature block for declaration (SRN | Name | Signature)
\newcommand{\@teamsignlist}{}
\newcommand{\addteamsign}[2]{%
  \g@addto@macro\@teamsignlist{\textbf{#2} & \textbf{#1} & \textbf{<Signature>} \\ }%
}
\newcommand{\printteamsigntable}{%
  \begin{center}
  \begin{tabular}{@{}lll@{}}
  \toprule
  \textbf{SRN} & \textbf{Name} & \textbf{Signature} \\
  \midrule
  \@teamsignlist
  \bottomrule
  \end{tabular}
  \end{center}
}

% ---- Title page -------------------------------------------------------------
\newcommand{\makepestitlepage}{%
  \thispagestyle{pesfront}%
  \begin{singlespace}
  \begin{center}
  \ifx\@reportlogo\@empty\else
    \includegraphics[width=\@titlelogowidth]{\@reportlogo}\par
    \vspace{0.35cm}
  \fi
  {\itshape\bfseries\fontsize{16}{19}\selectfont Dissertation on\par}
  \vspace{0.35cm}
  {\bfseries\fontsize{16}{19}\selectfont ``\@projecttitle''\par}
  \vspace{0.45cm}
  {\itshape\fontsize{12}{15}\selectfont Submitted in partial fulfilment of the requirements for the award of the degree of\par}
  \vspace{0.15cm}
  {\bfseries\fontsize{14}{17}\selectfont Bachelor of Technology\par}
  \vspace{0.05cm}
  {\bfseries\fontsize{14}{17}\selectfont in\par}
  \vspace{0.05cm}
  {\bfseries\fontsize{14}{17}\selectfont Computer Science \& Engineering\par}
  \vspace{0.4cm}
  {\bfseries\fontsize{14}{17}\selectfont \@coursecode{} -- \@phasename\par}
  \vspace{0.25cm}
  {\bfseries\fontsize{14}{17}\selectfont Project\_ID: \@projectid\par}
  \vspace{0.6cm}
  {\itshape\bfseries\fontsize{12}{15}\selectfont Submitted by:\par}
  \vspace{0.25cm}
  \begin{tabular}{@{}ll@{}}
    \@teamlist
  \end{tabular}
  \vspace{0.45cm}\par
  {\itshape\fontsize{12}{15}\selectfont Under the guidance of\par}
  \vspace{0.2cm}
  {\bfseries\fontsize{13}{16}\selectfont \@guidename\par}
  {\fontsize{12}{15}\selectfont \@guidedesignation\par}
  {\fontsize{12}{15}\selectfont PES University\par}
  \vspace{0.55cm}
  {\bfseries\fontsize{13}{16}\selectfont \@phaseperiod\par}
  \vspace{0.55cm}
  {\bfseries DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING\par}
  {FACULTY OF ENGINEERING\par}
  {\bfseries PES UNIVERSITY\par}
  {(Established under Karnataka Act No. 16 of 2013)\par}
  {100 feet Ring road, BSK 3rd stage, Hosakerehalli, Bengaluru -- 560085\par}
  \end{center}
  \end{singlespace}
  \clearpage
}

% ---- Certificate page -------------------------------------------------------
\newcommand{\makepescertificate}{%
  \thispagestyle{pesfront}%
  \begin{center}
  {\bfseries\fontsize{14}{17}\selectfont PES UNIVERSITY\par}
  {(Established under Karnataka Act No. 16 of 2013)\par}
  {100ft Ring Road, Bengaluru -- 560 085, Karnataka, India\par}
  \vspace{0.4cm}
  {\bfseries\fontsize{13}{16}\selectfont FACULTY OF ENGINEERING\par}
  \vspace{0.6cm}
  {\bfseries\fontsize{22}{26}\selectfont CERTIFICATE\par}
  \vspace{0.4cm}
  {\itshape\fontsize{12}{15}\selectfont This is to certify that the dissertation entitled\par}
  \vspace{0.3cm}
  {\bfseries\fontsize{14}{17}\selectfont `\@projecttitle'\par}
  \vspace{0.3cm}
  {\itshape\fontsize{12}{15}\selectfont is a bonafide work carried out by\par}
  \vspace{0.4cm}
  \begin{tabular}{@{}ll@{}}
    \@teamlist
  \end{tabular}
  \end{center}
  \vspace{0.5cm}
  \justifying
  in partial fulfilment for the completion of \@phasesemester{}-semester
  \@phasename{} (\@coursecode) in the Program of Study --
  \textbf{Bachelor of Technology in Computer Science and Engineering} under rules and
  regulations of PES University, Bengaluru during the period \@phaseperiod.
  It is certified that all corrections / suggestions indicated for internal
  assessment have been incorporated in the report. The dissertation has been
  approved as it satisfies the \@phasesemester{}-semester academic requirements in
  respect of project work.
  \vspace{1.2cm}

  \begin{center}
  \begin{tabular}{@{}p{0.3\linewidth}p{0.3\linewidth}p{0.3\linewidth}@{}}
    \centering Signature & \centering Signature & \centering\arraybackslash Signature \\[0.3em]
    \centering \textbf{\@guidename}       & \centering \textbf{\@chairperson} & \centering\arraybackslash \textbf{\@registrar} \\
    \centering \@guidedesignation         & \centering Chairperson            & \centering\arraybackslash Registrar
  \end{tabular}
  \end{center}
  \vspace{0.8cm}
  \begin{center}\textbf{External Viva}\end{center}
  \vspace{0.3cm}
  \noindent\begin{tabular}{@{}p{0.5\linewidth}p{0.45\linewidth}@{}}
    \textbf{Name of the Examiners} & \textbf{Signature with Date} \\[0.6em]
    1.~\rule{0.6\linewidth}{0.4pt} & \rule{0.8\linewidth}{0.4pt} \\[0.8em]
    2.~\rule{0.6\linewidth}{0.4pt} & \rule{0.8\linewidth}{0.4pt} \\[0.8em]
  \end{tabular}
  \clearpage
}

% ---- Declaration page -------------------------------------------------------
\newcommand{\makepesdeclaration}{%
  \thispagestyle{pesfront}%
  \begin{center}
  {\bfseries\fontsize{18}{22}\selectfont DECLARATION\par}
  \end{center}
  \vspace{0.6cm}
  \justifying
  We hereby declare that the \@phasename{} entitled \textbf{``\@projecttitle''}
  has been carried out by us under the guidance of \textbf{\@guidename},
  \@guidedesignation{} and submitted in partial fulfilment of the course
  requirements for the award of the degree of \textbf{Bachelor of Technology}
  in \textbf{Computer Science and Engineering} of \textbf{PES University,
  Bengaluru} during the academic semester \@phaseperiod. The matter embodied in
  this report has not been submitted to any other university or institution
  for the award of any degree.
  \vspace{1.5cm}

  \printteamsigntable
  \clearpage
}

% ---- Acknowledgement page ---------------------------------------------------
\newenvironment{pesacknowledgement}{%
  \thispagestyle{pesfront}%
  \begin{center}
  {\bfseries\fontsize{18}{22}\selectfont ACKNOWLEDGEMENT\par}
  \end{center}
  \vspace{0.4cm}
  \justifying
}{%
  \clearpage
}

% ---- Abstract page ----------------------------------------------------------
\renewenvironment{abstract}{%
  \thispagestyle{pesfront}%
  \begin{center}
  {\bfseries\fontsize{18}{22}\selectfont ABSTRACT\par}
  \end{center}
  \vspace{0.6cm}
  \justifying
}{%
  \clearpage
}

% ---- Convenience: List environments pre-styled to match body font -----------
\setlist[itemize]{leftmargin=*,itemsep=2pt,parsep=0pt}
\setlist[enumerate]{leftmargin=*,itemsep=2pt,parsep=0pt}

% ---- Set page style after front matter --------------------------------------
% Call \startcontentpages in main.tex right before the first \chapter (Intro)
% so pages from then on carry the running header.
\newcommand{\startcontentpages}{%
  \pagestyle{pescontent}%
  \setcounter{page}{1}%
  \pagenumbering{arabic}%
}

% End of class file.
\endinput
