"""One-off, idempotent: attach claim tags to the claim paragraphs the RCE lint found untagged (6 Nov 2026).

Each edit is an exact (old, new) replacement; an edit whose `new` text is already present is skipped, so
the script can be re-run. It also makes three wording changes the checks asked for:
  - FDI and OPG are defined in the "(ACRONYM)" form at first use;
  - a literature sentence reporting "outperforms" is attributed as a reported result (no matched
    comparison was run by this project);
  - the abstract gets one tag per sentence, for the skim-layer check, and names the interval of the
    external lead.
Tags are TeX comments (`% {C070}`): they do not reach the PDF.

    python -I tools/fix_claim_tags.py      (from report/phase3)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]

E = {
    "chapters/ch01_introduction.tex": [
        ("two-digit notation of the FDI (Fédération Dentaire Internationale): the",
         "two-digit notation of the Fédération Dentaire Internationale (FDI): the"),
        ("map them to a standard numbering\nscheme.\n", "map them to a standard numbering\nscheme. % {C070}\n"),
    ],
    "chapters/ch03_literature.tex": [
        ("\\litmeta{Ayhan et al.}{2025}{BMC Oral Health}\n", "\\litmeta{Ayhan et al.}{2025}{BMC Oral Health}\n% {C101}\n"),
        ("\\litmeta{Khuwaja et al.}{2024}{IEEE INMIC}\n", "\\litmeta{Khuwaja et al.}{2024}{IEEE INMIC}\n% {C102}\n"),
        ("\\litmeta{Jundaeng et al.}{2025}{Frontiers in Dental Medicine}\n", "\\litmeta{Jundaeng et al.}{2025}{Frontiers in Dental Medicine}\n% {C103}\n"),
        ("\\litmeta{Alharbi et al.}{2023}{Applied Sciences}\n", "\\litmeta{Alharbi et al.}{2023}{Applied Sciences}\n% {C104}\n"),
        ("\\litmeta{Chen et al.}{2023}{Bioengineering}\n", "\\litmeta{Chen et al.}{2023}{Bioengineering}\n% {C105}\n"),
        ("\\litmeta{Nassiri and Akhloufi}{2025}{Neural Computing and Applications}\n", "\\litmeta{Nassiri and Akhloufi}{2025}{Neural Computing and Applications}\n% {C106}\n"),
        ("\\litmeta{Asci et al.}{2024}{Children (MDPI)}\n", "\\litmeta{Asci et al.}{2024}{Children (MDPI)}\n% {C107}\n"),
        ("\\litmeta{Chen et al.}{2024}{AAAI Conference on Artificial Intelligence}\n", "\\litmeta{Chen et al.}{2024}{AAAI Conference on Artificial Intelligence}\n% {C108}\n"),
        ("\\litmeta{Pérez de Frutos et al.}{2024}{BMC Oral Health}\n", "\\litmeta{Pérez de Frutos et al.}{2024}{BMC Oral Health}\n% {C109}\n"),
        ("\\litmeta{Albano et al.}{2024}{BMC Oral Health}\n", "\\litmeta{Albano et al.}{2024}{BMC Oral Health}\n% {C110}\n"),
        ("\\litmeta{Kaushik and Sharma}{2025}{IEEE ICPC2T}\n", "\\litmeta{Kaushik and Sharma}{2025}{IEEE ICPC2T}\n% {C111}\n"),
        ("\\litmeta{Iacob et al.}{2025}{Dentistry Journal (MDPI)}\n", "\\litmeta{Iacob et al.}{2025}{Dentistry Journal (MDPI)}\n% {C112}\n"),
        ("\\litmeta{Chmielewski et al.}{2025}{Dentistry Journal (MDPI)}\n", "\\litmeta{Chmielewski et al.}{2025}{Dentistry Journal (MDPI)}\n% {C113}\n"),
        ("\\litmeta{Gamal et al.}{2025}{IEEE IMSA}\n", "\\litmeta{Gamal et al.}{2025}{IEEE IMSA}\n% {C114}\n"),
        ("\\litmeta{Sastika and Marappan}{2025}{IEEE ICICKE}\n", "\\litmeta{Sastika and Marappan}{2025}{IEEE ICICKE}\n% {C115}\n"),
        ("diagnoses together~\\cite{vannistelrooij2024combining}.\n", "diagnoses together~\\cite{vannistelrooij2024combining}. % {C120}\n"),
        ("outperforms prior methods on Tufts and two other datasets~\\cite{zhang2025reliable}.",
         "reports higher scores than earlier methods on Tufts and two other datasets~\\cite{zhang2025reliable}."),
        ("numbering end to end (Section~\\ref{sec:res-identity}).\n", "numbering end to end (Section~\\ref{sec:res-identity}). % {C121}\n"),
        ("Sections~\\ref{sec:sys-stage4} and~\\ref{sec:res-stage4}.\n", "Sections~\\ref{sec:sys-stage4} and~\\ref{sec:res-stage4}. % {C122}\n"),
        ("0.70 internally and 0.67 externally~\\cite{bizjak2024advancing}.\n", "0.70 internally and 0.67 externally~\\cite{bizjak2024advancing}. % {C123}\n"),
        ("(an observation, not a systematic count).\n", "(an observation, not a systematic count). % {C124} {C097}\n"),
        ("comparator that needs no task training.\n", "comparator that needs no task training. % {C125}\n"),
    ],
    "chapters/ch04_prs.tex": [
        ("the meaning of each field is stated in the report itself.\n\\end{itemize}\n",
         "the meaning of each field is stated in the report itself.\n\\end{itemize}\n% {C091}\n"),
    ],
    "chapters/ch05_hld.tex": [
        ("Figure~\\ref{fig:arch} of Chapter~\\ref{ch:system}.\n", "Figure~\\ref{fig:arch} of Chapter~\\ref{ch:system}. % {C092}\n"),
        ("\\item a limitations block in the report, keyed to the hash of each checkpoint that ran.\n\\end{itemize}\n",
         "\\item a limitations block in the report, keyed to the hash of each checkpoint that ran.\n\\end{itemize}\n\n"
         "The caries stage changed form during Phase 3. The per-crop classifier of Phase 2 sees one tight crop\n"
         "and answers yes or no, a task in which a strong positional prior can earn much of the score; five\n"
         "direct repairs of it, each against a same-day control, gave no gain that separated from zero\n"
         "(Section~\\ref{sec:res-rq2}). The task was therefore changed to locating lesions on the whole image,\n"
         "under an acceptance rule committed before any candidate was trained, and the classifier was kept as\n"
         "a selectable alternative. % {C071}\n"),
    ],
    "chapters/ch06_lld.tex": [
        ("\\item a set of invariants checked against the saved artefacts.\n\\end{itemize}\n",
         "\\item a set of invariants checked against the saved artefacts.\n\\end{itemize}\n% {C096}\n"),
    ],
    "chapters/ch07_system_design.tex": [
        ("because the masks are sparse relative to the crop.\n\\end{itemize}\n",
         "because the masks are sparse relative to the crop.\n\\end{itemize}\n% {C082}\n"),
        ("It is kept as a documented negative result and is not part of the pipeline.\n",
         "It is kept as a documented negative result and is not part of the pipeline. % {C081}\n"),
    ],
    "chapters/ch08_methodology.tex": [
        ("23.84 to 1 (Figure~\\ref{fig:tuftscoverage}).\n", "23.84 to 1 (Figure~\\ref{fig:tuftscoverage}). % {C080}\n"),
        ("less sensitive to\nsmall misalignments.\n", "less sensitive to\nsmall misalignments. % {C082}\n"),
        ("Training ran on cloud GPUs and on a laptop accelerator; inference needs neither.\n",
         "Training ran on cloud GPUs and on a laptop accelerator; inference needs neither. % {C083}\n"),
        ("depends on the population's age and exposure.\n", "depends on the population's age and exposure. % {C010}\n"),
        ("each tooth type its flags should be carious more often than the classifier's.\n",
         "each tooth type its flags should be carious more often than the classifier's. % {C093}\n"),
        ("so every comparison is\nmade within a cohort.\n", "so every comparison is\nmade within a cohort. % {C094}\n"),
        ("Differences are system minus comparator in percentage points (pp).\n",
         "Differences are system minus comparator in percentage points (pp). % {C095}\n"),
    ],
    "chapters/ch09_implementation.tex": [
        ("the second stage is the shipped severity grader (Stage~3b).\n", "the second stage is the shipped severity grader (Stage~3b). % {C084}\n"),
        ("recipes and changed the split (Section~\\ref{sec:sys-stage4}).\n", "recipes and changed the split (Section~\\ref{sec:sys-stage4}). % {C085}\n"),
        ("Its results are in Section~\\ref{sec:sys-stage4}.\n", "Its results are in Section~\\ref{sec:sys-stage4}. % {C086}\n"),
    ],
    "chapters/ch10_results.tex": [
        ("differences are system minus comparator in percentage points.\n", "differences are system minus comparator in percentage points. % {C095}\n"),
        ("so these are selection diagnostics, not test results.\n", "so these are selection diagnostics, not test results. % {C032}\n"),
        ("because the front end trained on this corpus.\n", "because the front end trained on this corpus. % {C025}\n"),
        ("against 17.0\\%.\n\\end{itemize}\n", "against 17.0\\%.\n\\end{itemize}\n% {C023}\n"),
        ("Figure~\\ref{fig:stage4}).\n\\begin{itemize}\n", "Figure~\\ref{fig:stage4}). % {C040}\n\\begin{itemize}\n"),
        ("it found 3.4\\% (6 of 175).\n\\end{itemize}\n", "it found 3.4\\% (6 of 175).\n\\end{itemize}\n% {C040}\n"),
        ("AI~\\cite{mongan2020claim,schwendicke2021checklist}.\n", "AI~\\cite{mongan2020claim,schwendicke2021checklist}. % {C090}\n"),
    ],
    "chapters/ch11_conclusion.tex": [
        ("of labelled teeth at 95.9\\% specificity. % {C010} {C011} {C015} {C020} {C040}",
         "of labelled teeth at 95.9\\% specificity. % {C010} {C011} {C013} {C015} {C016} {C018} {C022} {C023} {C024} {C040}"),
    ],
}

# Second pass (same day): acronyms defined at first use, a lead-in sentence for every float that had no
# reference in the text, and absolute terms ("never") replaced by what was measured.
E2 = {
    "chapters/ch01_introduction.tex": [
        ("abstention controlled by a shuffle test (Section~\\ref{sec:res-rq3}).\n",
         "abstention controlled by a shuffle test (Section~\\ref{sec:res-rq3}). % {C034} {C035} {C036}\n"),
    ],
    "chapters/ch02_problem.tex": [
        ("(Section~\\ref{sec:method-prereg}). Every reported number must trace to a saved artefact, and a",
         "(Section~\\ref{sec:method-prereg}). % {C020} {C021}\nEvery reported number must trace to a saved artefact, and a"),
    ],
    "chapters/ch03_literature.tex": [
        ("the area under the ROC curve was 98.67\\%", "the area under the receiver operating characteristic (ROC) curve was 98.67\\%"),
        ("accuracy 0.73 to 0.98 and AUC 0.84 to 0.98.", "accuracy 0.73 to 0.98 and area under the curve (AUC) 0.84 to 0.98."),
        ("model that never sees the premise beats the majority class on many\ndatasets",
         "model shown only the hypothesis, without the premise, scores above the majority class on many\ndatasets"),
        ("\nTable~\\ref{tab:lit-compare} places the studies", "\nThe comparison in Table~\\ref{tab:lit-compare} places the studies"),
    ],
    "chapters/ch04_prs.tex": [
        ("\\section{User Classes and Characteristics}\n\n",
         "\\section{User Classes and Characteristics}\n\nThe system serves four classes of user, each through a different interface\n(Table~\\ref{tab:users}).\n\n"),
        ("\\section{Functional Requirements}\n\n",
         "\\section{Functional Requirements}\n\nThe functional requirements, and the file that implements each, are listed in\nTable~\\ref{tab:fr}.\n\n"),
        ("\\section{Non-Functional Requirements}\n\n",
         "\\section{Non-Functional Requirements}\n\nThe non-functional requirements are listed in Table~\\ref{tab:nfr}.\n\n"),
        ("\\section{Use Cases}\n\n",
         "\\section{Use Cases}\n\nThe actors and their use cases are drawn in Figure~\\ref{fig:usecase} and described in\nTable~\\ref{tab:usecases}.\n\n"),
        ("the NMS\n  IoU at 0.50", "the non-maximum suppression (NMS)\n  IoU at 0.50"),
    ],
    "chapters/ch07_system_design.tex": [
        ("Each crop was enhanced\nwith CLAHE and a candidate", "Each crop was enhanced\nwith contrast-limited adaptive histogram equalisation (CLAHE) and a candidate"),
    ],
    "chapters/ch08_methodology.tex": [
        ("intervals are 95\\% percentile bootstraps over images, not teeth,",
         "intervals are 95\\% percentile bootstrap confidence intervals (CI) over images, not teeth,"),
        ("the crop classifier's calibration AP uses 2,000", "the crop classifier's calibration average precision (AP) uses 2,000"),
    ],
    "chapters/ch09_implementation.tex": [
        ("\\section{Repository Structure}\n\n",
         "\\section{Repository Structure}\n\nThe repository layout, to two levels, is shown in Figure~\\ref{fig:repotree}.\n\n"),
        ("\\section{Pseudocode}\n\n",
         "\\section{Pseudocode}\n\nEight algorithms give the pseudocode of the pipeline and of the evaluation: end-to-end inference\n"
         "(Algorithm~\\ref{alg:pipeline}), one-to-one FDI assignment (Algorithm~\\ref{alg:fdi}), lesion-to-tooth\n"
         "assignment (Algorithm~\\ref{alg:lesion}), the fit of the image-blind constant\n"
         "(Algorithm~\\ref{alg:constant}), the paired cluster bootstrap (Algorithm~\\ref{alg:bootstrap}), the\n"
         "matched-volume comparison (Algorithm~\\ref{alg:matched}), random-effects pooling across sites\n"
         "(Algorithm~\\ref{alg:re}) and the near-duplicate check (Algorithm~\\ref{alg:nearDup}).\n\n"),
        ("\\section{Verification and Testing}\n\\label{sec:impl-verify}\n\n",
         "\\section{Verification and Testing}\n\\label{sec:impl-verify}\n\nThe code and the reported numbers were checked in six ways, summarised in Table~\\ref{tab:verify}. % {C050}\n\n"),
    ],
    "chapters/ch10_results.tex": [
        ("Four teeth are never detected,", "Four teeth are not detected,"),
        ("uses position alone and never sees an image reaches", "uses position alone and sees no image reaches"),
        ("\\item On the 125 test radiographs it never trained on it found", "\\item On the 125 test radiographs held out from its training it found"),
    ],
    "chapters/ch11_conclusion.tex": [
        ("a venue that meets the department's guidelines.\n\\end{enumerate}\n",
         "a venue that meets the department's guidelines.\n\\end{enumerate}\n% {C098}\n"),
    ],
    "appendices/appA_acronyms.tex": [
        ("\\section{Definitions}\n\n", "\\section{Definitions}\n\nThe terms used in this report are defined in Table~\\ref{tab:defs}.\n\n"),
        ("\\section{Acronyms and Abbreviations}\n\n",
         "\\section{Acronyms and Abbreviations}\n\nThe acronyms and abbreviations are expanded in Table~\\ref{tab:acronyms}.\n\n"),
    ],
    "appendices/appB_user_manual.tex": [
        ("\\section{Troubleshooting}\n\n", "\\section{Troubleshooting}\n\nCommon problems and their fixes are listed in Table~\\ref{tab:trouble}.\n\n"),
    ],
}
for k, v in E2.items():
    E.setdefault(k, []).extend(v)

ABSTRACT_OLD_START = "% RCE-ABSTRACT-BEGIN\n"
ABSTRACT_END = "% RCE-ABSTRACT-END\n"
ABSTRACT_NEW = """% RCE-ABSTRACT-BEGIN
A panoramic radiograph (OPG) is read tooth by tooth, yet caries systems are scored by which teeth
they mark carious, a score an image-blind list can partly earn. % {C010}
Phase 3 completes an assistant that turns one OPG into a per-tooth report in six stages: tooth
detection (YOLOv11l), numbering (ResNet18, one-to-one assignment), caries lesion detection, severity
grading, an abnormality flag and report fusion. % {C002}
It runs at 1.70 s per image on a laptop CPU, from a command line, a Streamlit demo or Docker. % {C001} {C002}

An image-blind constant fitted in closed form, the eight first and second molars, scores F1 0.320 on
164 held-out DENTEX images; the pipeline scores 0.498. % {C010} {C013}
On 337 external radiographs from four sites the lesion detector leads the constant by 9.28 points
(95\\% interval 4.72--13.73), though not at every site. % {C022} {C024}
Retrained with a radiograph-level split, the Phase 2 bone-loss flag finds 27.5\\% of labelled teeth at
95.9\\% specificity. % {C040}
% RCE-ABSTRACT-END
"""

fails, done, skipped = [], 0, 0
for rel, edits in E.items():
    f = HERE / rel
    raw = f.read_bytes()
    crlf = b"\r\n" in raw
    t = raw.decode("utf-8").replace("\r\n", "\n")
    for old, new in edits:
        if new in t:
            skipped += 1
            continue
        n = t.count(old)
        if n != 1:
            fails.append(f"{rel}: {n} matches for {old[:60]!r}")
            continue
        t = t.replace(old, new)
        done += 1
    f.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))

f = HERE / "frontmatter/abstract.tex"
raw = f.read_bytes()
crlf = b"\r\n" in raw
t = raw.decode("utf-8").replace("\r\n", "\n")
if ABSTRACT_NEW not in t:
    a, b = t.index(ABSTRACT_OLD_START), t.index(ABSTRACT_END) + len(ABSTRACT_END)
    t = t[:a] + ABSTRACT_NEW + t[b:]
    done += 1
    f.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
else:
    skipped += 1
print(f"applied {done}, already present {skipped}, failed {len(fails)}")
for x in fails:
    print("  FAIL", x)
sys.exit(1 if fails else 0)
