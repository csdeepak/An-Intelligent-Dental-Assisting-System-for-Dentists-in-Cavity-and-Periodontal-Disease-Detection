"""Render the report's TeX body as Markdown for the Research Communication Engine checks.

The RCE tools (lint_draft, verify_numbers, skim_layer) read Markdown: one paragraph per line, claim tags
inline as {C###}, citations author-year. This script produces that view of the report; the PDF is still
built from the TeX. Conversions:

  % {C001} {C002}      a TeX comment holding claim tags becomes inline tags at the end of its paragraph
  \\cite{a,b}           (Surname et al., 2021; Other, 2020) from references.bib, first author as registered
  \\ref{x}              the number LaTeX assigned (build/main.aux), so "Figure~\\ref{fig:x}" reads "Figure 7.1"
  figure / table       the caption as a paragraph ("Figure 7.1: ..."), tables as Markdown tables
  algorithm, listing   fenced code blocks
  tikz, dirtree        dropped (diagrams carry no claims)

    python -I tools/export_md.py               writes build/report.md and build/abstract.md
    python -I tools/export_md.py --inventory   lists the environments and macros in the body
"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
BUILD = HERE / "build"
BODY = ["frontmatter/abstract.tex"]


def body_files():
    main = (HERE / "main.tex").read_text(encoding="utf-8")
    files = [m for m in re.findall(r"\\input\{([^}]+)\}", main) if m.startswith(("chapters/", "appendices/"))]
    return BODY + [f + ".tex" for f in files]


# ---------------------------------------------------------------- labels and citations
def load_labels():
    aux = BUILD / "main.aux"
    labels = {}
    if aux.exists():
        for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{([^}]*)\}", aux.read_text(encoding="utf-8", errors="replace")):
            labels[m.group(1)] = m.group(2)
    return labels


def _strip_tex(s):
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
    s = re.sub(r"\\.", "", s)
    return s.replace("{", "").replace("}", "").strip()


def load_bib():
    """bib key -> (author surnames as registered, year), from .rcs/corpus/source_registry.json.

    The registry is built from the same references.bib that BibTeX reads (tools/rcs_build.py), so the
    author-year form here names exactly the entry the PDF's numbered citation points to."""
    reg_f = HERE / ".rcs" / "corpus" / "source_registry.json"
    reg = json.loads(reg_f.read_text(encoding="utf-8"))["sources"] if reg_f.exists() else []
    return {s["key"]: (s.get("authors") or ["Anon"], s.get("year") or 0) for s in reg if s.get("key")}


def cite_text(keys, bib):
    parts = []
    for k in [x.strip() for x in keys.split(",") if x.strip()]:
        if k not in bib:
            parts.append(f"[CITATION NEEDED: {k}]")
            continue
        authors, year = bib[k]
        n = len(authors)
        others = n >= 3 or (n >= 2 and authors[-1].lower() == "others")
        form = f"{authors[0]} et al." if others else f"{authors[0]} and {authors[1]}" if n == 2 else authors[0]
        parts.append(f"{form}, {year}")
    return "(" + "; ".join(parts) + ")"


# ---------------------------------------------------------------- brace-aware helpers
def read_group(s, i):
    """s[i] == '{' -> (content, index after the closing brace)."""
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def skip_opt(s, i):
    while i < len(s) and s[i] in " \t":
        i += 1
    if i < len(s) and s[i] == "[":
        depth, j = 0, i
        while j < len(s):
            if s[j] == "[":
                depth += 1
            elif s[j] == "]":
                depth -= 1
                if depth == 0:
                    return s[i + 1:j], j + 1
            j += 1
    return None, i


def replace_macro(s, name, nargs, fn, opt=False):
    """Replace \\name[opt]{a1}...{an} by fn(opt, args)."""
    out, i = [], 0
    pat = re.compile(r"\\" + name + r"(?![a-zA-Z])\*?")
    while True:
        m = pat.search(s, i)
        if not m:
            out.append(s[i:])
            return "".join(out)
        out.append(s[i:m.start()])
        j = m.end()
        o = None
        if opt:
            o, j = skip_opt(s, j)
        args = []
        for _ in range(nargs):
            while j < len(s) and s[j] in " \t\n":
                j += 1
            if j < len(s) and s[j] == "{":
                a, j = read_group(s, j)
            else:
                a = s[j] if j < len(s) else ""
                j += 1
            args.append(a)
        out.append(fn(o, args))
        i = j


def strip_env(s, env, fn):
    pat = re.compile(r"\\begin\{" + re.escape(env) + r"\}(.*?)\\end\{" + re.escape(env) + r"\}", re.S)
    return pat.sub(lambda m: fn(m.group(1)), s)


# ---------------------------------------------------------------- comments and tags
TAG_RE = re.compile(r"\{([CL]\d{3,})\}")


def handle_comments(text):
    """Drop comments; keep claim tags as placeholders (@@TAGC001@@) that survive the inline pass.

    A tag-only comment line after \\end{table} or \\end{figure} tags the whole float (every table row and
    the caption); after \\end{itemize} or \\end{enumerate}, every item of that list; otherwise the
    paragraph above it."""
    lines = []
    for line in text.split("\n"):
        m = re.search(r"(?<!\\)%", line)
        if not m:
            lines.append(line)
            continue
        code, comment = line[:m.start()], line[m.start() + 1:]
        ids = TAG_RE.findall(comment)
        if not ids:
            if code.strip():
                lines.append(code)
            continue
        tt = " ".join(f"@@TAG{i}@@" for i in ids)
        if code.strip():
            lines.append(code.rstrip() + " " + tt)
            continue
        k = len(lines) - 1
        while k >= 0 and not lines[k].strip():
            k -= 1
        prev = lines[k].strip() if k >= 0 else ""
        if prev.startswith(("\\end{table}", "\\end{figure}")):
            lines.insert(k, "@@FLOATTAGS@@ " + tt)
        elif prev.startswith(("\\end{itemize}", "\\end{enumerate}")):
            lines.insert(k, "@@LISTTAGS@@ " + tt)
        elif prev.startswith(("\\litmeta", "\\section", "\\subsection", "\\subsubsection")):
            lines.append("@@SECTAGS@@ " + tt)                  # the whole section (a literature entry)
        elif prev and not prev.startswith("\\"):
            lines[k] = lines[k].rstrip() + " " + tt
        else:
            lines.append("@@TAGS@@ " + tt)
    return "\n".join(lines)


# ---------------------------------------------------------------- inline text
def inline(s, labels, bib):
    s = replace_macro(s, "cite", 1, lambda o, a: cite_text(a[0], bib), opt=True)
    s = replace_macro(s, "eqref", 1, lambda o, a: f"({labels.get(a[0], '?')})")
    s = replace_macro(s, "ref", 1, lambda o, a: labels.get(a[0], "??"))
    s = replace_macro(s, "pageref", 1, lambda o, a: labels.get(a[0], "??"))
    s = replace_macro(s, "label", 1, lambda o, a: "")
    s = replace_macro(s, "ci", 2, lambda o, a: f"[{a[0]}, {a[1]}]")
    s = replace_macro(s, "litmeta", 3, lambda o, a: f"\n\n**Authors:** {a[0]}. **Year:** {a[1]}. **Venue:** {a[2]}.\n\n")
    s = replace_macro(s, "litpart", 1, lambda o, a: f"\n\n**{a[0]}** ")
    s = replace_macro(s, "srcnote", 1, lambda o, a: f"\n\n*{a[0]}*\n\n")
    for name, wrap in (("textbf", "**"), ("emph", "*"), ("textit", "*"), ("texttt", "`"), ("nolinkurl", "`"),
                       ("url", "`")):
        s = replace_macro(s, name, 1, lambda o, a, w=wrap: f"{w}{a[0]}{w}")
    s = replace_macro(s, "href", 2, lambda o, a: a[1])
    for name in ("textsf", "fdi", "textsc", "mbox", "textrm", "textnormal", "makecell", "MakeUppercase", "text",
                 "mathrm", "mathit", "mathbf", "mathsf", "operatorname", "textsuperscript", "hbox", "underline",
                 "textup", "smash", "mathbb", "mathcal", "boldsymbol"):
        s = replace_macro(s, name, 1, lambda o, a: a[0], opt=(name == "makecell"))
    s = replace_macro(s, "multicolumn", 3, lambda o, a: a[2])
    s = replace_macro(s, "multirow", 3, lambda o, a: a[2])
    s = replace_macro(s, "frac", 2, lambda o, a: f"({a[0]})/({a[1]})")
    s = replace_macro(s, "tfrac", 2, lambda o, a: f"({a[0]})/({a[1]})")
    s = replace_macro(s, "sqrt", 1, lambda o, a: f"sqrt({a[0]})")
    for name in ("vspace", "hspace", "phantom", "hphantom", "vphantom", "thispagestyle", "pagestyle", "needspace",
                 "setlength", "addtolength", "includegraphics", "input", "color", "frontheading"):
        s = replace_macro(s, name, 1, lambda o, a: "", opt=True)
    s = replace_macro(s, "addcontentsline", 3, lambda o, a: "")
    s = replace_macro(s, "setcounter", 2, lambda o, a: "")
    s = replace_macro(s, "textcolor", 2, lambda o, a: a[1])
    s = replace_macro(s, "colorbox", 2, lambda o, a: a[1])
    s = re.sub(r"\\\\(\[[^\]]*\])?", " ", s)
    reps = [(r"\pp", " pp"), (r"\%", "%"), (r"\&", "&"), (r"\_", "_"), (r"\#", "#"), (r"\$", "$"),
            (r"\textdegree", "°"), (r"\ldots", "..."), (r"\dots", "..."), (r"\cdots", "..."), (r"\times", "×"),
            (r"\geq", "≥"), (r"\leq", "≤"), (r"\ge", "≥"), (r"\le", "≤"), (r"\neq", "≠"), (r"\approx", "≈"),
            (r"\rightarrow", "→"), (r"\to", "→"), (r"\leftarrow", "←"), (r"\Rightarrow", "⇒"), (r"\pm", "±"),
            (r"\cdot", "·"), (r"\sum", "Σ"), (r"\in", "∈"), (r"\notin", "∉"), (r"\infty", "∞"), (r"\tau", "τ"),
            (r"\Delta", "Δ"), (r"\gamma", "γ"), (r"\chi", "χ"), (r"\wedge", "∧"), (r"\bar", ""), (r"\alpha", "α"), (r"\beta", "β"), (r"\pi", "π"), (r"\mu", "μ"), (r"\sigma", "σ"), (r"\hat", ""),
            (r"\lvert", "|"), (r"\rvert", "|"), (r"\mid", "|"), (r"\lbrace", "{"), (r"\rbrace", "}"),
            (r"\quad", " "), (r"\qquad", " "), (r"\enspace", " "), (r"\,", " "), (r"\;", " "), (r"\:", " "),
            (r"\!", ""), (r"\ ", " "), (r"\noindent", ""), (r"\centering", ""), (r"\small", ""), (r"\footnotesize", ""),
            (r"\scriptsize", ""), (r"\normalsize", ""), (r"\large", ""), (r"\par", "\n\n"), (r"\medskip", ""),
            (r"\bigskip", ""), (r"\smallskip", ""), (r"\hfill", " "), (r"\newline", " "), (r"\linebreak", " "),
            (r"\clearpage", ""), (r"\newpage", ""), (r"\FloatBarrier", ""), (r"\justifying", ""),
            (r"\begingroup", ""), (r"\endgroup", ""), (r"\phantomsection", ""), (r"\raggedright", ""),
            (r"\tightlist", ""), (r"\left", ""), (r"\right", ""), (r"\big", ""), (r"\Big", ""), (r"\displaystyle", ""),
            (r"\arg\max", "argmax"), (r"\argmax", "argmax"), (r"\max", "max"), (r"\min", "min"), (r"\log", "log"),
            (r"\exp", "exp"), (r"\textendash", "–"), (r"\textemdash", "—"), (r"\textasciitilde", "~"),
            (r"\checkmark", "✓"), (r"\ell", "ℓ"), (r"\lfloor", "⌊"), (r"\rfloor", "⌋"), (r"\lceil", "⌈"),
            (r"\rceil", "⌉"), (r"\cap", "∩"), (r"\cup", "∪"), (r"\setminus", "∖"), (r"\land", "∧"), (r"\lor", "∨"),
            (r"\neg", "¬"), (r"\forall", "∀"), (r"\exists", "∃"), (r"\emptyset", "∅"), (r"\varnothing", "∅"),
            (r"\leftarrow", "←"), (r"\gets", "←"), (r"\sim", "~"), (r"\propto", "∝"), (r"\ast", "*")]
    for a, b in sorted(reps, key=lambda x: -len(x[0])):
        s = re.sub(re.escape(a) + (r"(?![a-zA-Z])" if a[-1].isalpha() else ""), lambda m, b=b: b, s)
    s = s.replace("---", "—").replace("--", "–").replace("``", "\u201c").replace("''", "\u201d")
    s = re.sub(r"(?<!\\)~", " ", s)
    s = s.replace("{,}", ",")
    s = re.sub(r"\$([^$]*)\$", lambda m: m.group(1), s)
    s = re.sub(r"\\[a-zA-Z]+\*?", "", s)                 # any macro left is formatting
    s = re.sub(r"(?<![\\\w])[{}]", "", s)
    s = s.replace("\\{", "{").replace("\\}", "}")
    s = re.sub(r"\^\{?([^{}\s]+)\}?", r"^\1", s)
    s = re.sub(r"_\{([^{}]+)\}", r"_\1", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s


# ---------------------------------------------------------------- block environments
def table_md(body, labels, bib):
    body = re.sub(r"\\(toprule|midrule|bottomrule|hline|endhead|endfirsthead|endfoot|endlastfoot)\b", "", body)
    body = re.sub(r"\\cmidrule(\([^)]*\))?\{[^}]*\}", "", body)
    body = re.sub(r"\\addlinespace(\[[^\]]*\])?", "", body)
    body = re.sub(r"\\rowcolor\{[^}]*\}", "", body)
    rows, cur, depth, i = [], [], 0, 0
    buf = ""
    while i < len(body):
        c = body[i]
        if c == "\\" and body[i:i + 2] == "\\\\" and depth == 0:
            cur.append(buf)
            rows.append(cur)
            cur, buf = [], ""
            i += 2
            _, i = skip_opt(body, i)
            continue
        if c == "\\" and i + 1 < len(body):
            buf += body[i:i + 2]
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if c == "&" and depth == 0:
            cur.append(buf)
            buf = ""
        else:
            buf += c
        i += 1
    if buf.strip():
        cur.append(buf)
    if cur:
        rows.append(cur)
    rows = [[inline(x, labels, bib).replace("\n", " ").strip().replace("|", "/") for x in r] for r in rows]
    rows = [r for r in rows if any(x for x in r)]
    if not rows:
        return ""
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * w]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def float_md(body, kind, labels, bib):
    """figure/table float -> caption paragraph (+ table)."""
    ft = " ".join(re.findall(r"@@FLOATTAGS@@ ([^\n]*)", body))
    body = re.sub(r"@@FLOATTAGS@@[^\n]*", "", body)
    label = re.search(r"\\label\{([^}]+)\}", body)
    num = labels.get(label.group(1), "??") if label else "??"
    caps = []

    def grab(o, a):
        caps.append(a[0])
        return ""
    body2 = replace_macro(body, "caption", 1, grab, opt=True)
    subcaps = []

    def grab_sub(o, a):
        subcaps.append(a[0])
        return ""
    body2 = replace_macro(body2, "subcaption", 1, grab_sub, opt=True)
    sublabels = re.findall(r"\\label\{([^}]+)\}", body)
    out = []
    word = "Figure" if kind == "figure" else "Table"
    def one(x):
        return " ".join(inline(x, labels, bib).split())
    if caps:
        main = caps[-1] if kind == "figure" else caps[0]
        out.append(f"{word} {num}: " + one(main) + (" " + ft if ft else ""))
    # subfigure captions inside subfigure environments
    for k, c in enumerate(caps[:-1] if kind == "figure" else []):
        out.append(f"({chr(97 + k)}) " + one(c))
    tables = re.findall(r"\\begin\{(tabularx|tabular|longtable)\}(?:\{[^}]*\})?(\{(?:[^{}]|\{[^{}]*\})*\})(.*?)\\end\{\1\}", body, re.S)
    for _, _, tb in tables:
        md = table_md(tb, labels, bib)
        if ft:
            md = "\n".join(r + " " + ft if r.startswith("| ") else r for r in md.split("\n"))
        out.append(md)
    return "\n\n" + "\n\n".join(x for x in out if x) + "\n\n"


def code_md(body, lang=""):
    return "\n\n```" + lang + "\n" + body.strip("\n") + "\n```\n\n"


def algo_md(body, labels, bib):
    label = re.search(r"\\label\{([^}]+)\}", body)
    num = labels.get(label.group(1), "?") if label else "?"
    caps = []
    body = replace_macro(body, "caption", 1, lambda o, a: caps.append(a[0]) or "", opt=True)
    body = re.sub(r"\\begin\{algorithmic\}(\[[^\]]*\])?|\\end\{algorithmic\}", "", body)
    body = re.sub(r"\\(State|Statex|Require|Ensure|Return|Comment|ForAll|For|EndFor|If|ElsIf|Else|EndIf|While|EndWhile|"
                  r"Function|EndFunction|Procedure|EndProcedure|Call|Repeat|Until)\b",
                  lambda m: "\n" + m.group(1).upper() + " ", body)
    lines = [inline(x, labels, bib).strip() for x in body.split("\n")]
    head = f"Algorithm {num}: " + inline(caps[0], labels, bib).strip() if caps else ""
    return "\n\n" + head + code_md("\n".join(x for x in lines if x))


def lists_md(s):
    """itemize/enumerate (nested) -> Markdown list lines; each item becomes one line."""
    out_lines, stack = [], []
    tokens = re.split(r"(\\begin\{(?:itemize|enumerate|description)\}(?:\[[^\]]*\])?|\\end\{(?:itemize|enumerate|description)\}|\\item\b(?:\[[^\]]*\])?)", s)
    buf = []

    def flush():
        if buf:
            text = " ".join(" ".join(buf).split())
            if stack:
                lt = re.findall(r"@@LISTTAGS@@ ((?:@@TAG\w+@@\s*)+)", text)
                if lt:
                    stack[-1][3] += " " + " ".join(lt)
                    text = re.sub(r"@@LISTTAGS@@ (?:@@TAG\w+@@\s*)+", "", text).strip()
                kind, n = stack[-1][0], stack[-1][1]
                ind = "  " * (len(stack) - 1)
                if text:                                       # loose list: one paragraph per item
                    stack[-1][2].append(len(out_lines))
                    out_lines.append(f"\n\n{ind}" + (f"{n}. " if kind == "enumerate" else "- ") + text)
            elif text:
                out_lines.append(" ".join(buf))
            buf.clear()
    for tok in tokens:
        if tok is None:
            continue
        if tok.startswith("\\begin{"):
            flush()
            out_lines.append("\n" if not stack else "")
            stack.append([re.search(r"\{(\w+)\}", tok).group(1), 0, [], ""])
        elif tok.startswith("\\end{"):
            flush()
            if stack:
                _, _, idx, tags = stack.pop()
                if tags.strip():
                    for i in idx:
                        out_lines[i] = out_lines[i] + " " + tags.strip()
            out_lines.append("\n\n" if not stack else "")
        elif tok.startswith("\\item"):
            flush()
            if stack:
                stack[-1][1] += 1
            lab = re.match(r"\\item\[([^\]]*)\]", tok)
            if lab:
                buf.append(f"**{lab.group(1)}**")
        else:
            if stack:
                buf.append(tok)
            else:
                out_lines.append(tok)
    flush()
    return "".join(out_lines)


TAG_GRP = r"(?:\s*\{[CL]\d{3,}\})+"
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[\(\"'*`])")      # the RCE tools' sentence boundary


def apply_section_tags(md):
    """A tag-only comment under a heading or \\litmeta tags every prose line of that section."""
    out, sec, in_code = [], "", False
    for line in md.split("\n"):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
        elif not in_code and s.startswith("#"):
            sec = ""
        elif not in_code and s.startswith("@@SECTAGS@@"):
            sec = (sec + " " + s[len("@@SECTAGS@@"):].strip()).strip()
            continue
        elif not in_code and sec and s and not s.startswith(("|", "$$")):
            line = line.rstrip() + " " + sec
        out.append(line)
    return "\n".join(out)


def distribute(line):
    """Put claim tags inside the sentence they tag, before its full stop, where the RCE tools look for them.
    A tag group that ends a paragraph or list item, with no other tag in it, applies to every sentence of
    it; tags placed mid-paragraph stay with the sentence they follow."""
    s = line.strip()
    if not s or s.startswith(("|", "#", "```", "$$")) or not re.search(r"\{[CL]\d{3,}\}", line):
        return line
    m = re.search("(" + TAG_GRP + r")\s*$", line)
    body = line[:m.start()].rstrip() if m else line.rstrip()
    if m and not re.search(r"\{[CL]\d{3,}\}", body):
        tags = " ".join(re.findall(r"\{[CL]\d{3,}\}", m.group(1)))
        pm = re.match(r"\s*(?:[-*]|\d+\.)\s+", body)
        prefix = pm.group(0) if pm else ""
        out = []
        for sent in SENT_SPLIT.split(body[len(prefix):]):
            sent = sent.rstrip()
            out.append(sent[:-1].rstrip() + " " + tags + sent[-1] if sent and sent[-1] in ".!?:;" else sent + " " + tags)
        return prefix + " ".join(out)
    return re.sub(r"([.!?;:])(" + TAG_GRP + r")", lambda mm: mm.group(2) + mm.group(1), line)


REF_LIST = re.compile(r"\b(Figure|Table|Section|Chapter|Algorithm|Equation)s\s+(\d+(?:\.\d+)*[a-z]?)"
                      r"((?:(?:,\s*|,?\s+and\s+|\s*–\s*|\s+to\s+)\d+(?:\.\d+)*[a-z]?)+)")


def type_refs(md):
    """'Figures 10.6c and 10.15' -> 'Figures 10.6c and Figure 10.15': the number tracer skips a number only
    when its type word precedes it, so each cross-reference in a list is labelled with its type."""
    def one(m):
        rest = re.sub(r"(\d+(?:\.\d+)*[a-z]?)", lambda n: f"{m.group(1)} {n.group(1)}", m.group(3))
        return f"{m.group(1)}s {m.group(2)}{rest}"
    return REF_LIST.sub(one, md)


def convert(tex, labels, bib):
    t = tex.replace("\r\n", "\n")
    t = handle_comments(t)
    # verbatim-like blocks first, protected from inline processing
    protected = []

    def protect(md):
        protected.append(md)
        return f"\n\n@@P{len(protected) - 1}@@\n\n"
    t = re.sub(r"\\begin\{lstlisting\}(\[(?:[^\[\]]|\[[^\]]*\])*\])?(.*?)\\end\{lstlisting\}",
               lambda m: protect((("Listing: " + inline(re.search(r"caption=\{(.*?)\},label", m.group(1) or "").group(1), labels, bib)
                                   + "\n") if m.group(1) and "caption=" in m.group(1) else "") + code_md(m.group(2), "json")), t, flags=re.S)
    t = re.sub(r"\\begin\{algorithm\}(\[[^\]]*\])?(.*?)\\end\{algorithm\}", lambda m: protect(algo_md(m.group(2), labels, bib)), t, flags=re.S)
    t = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", "", t, flags=re.S)
    t = re.sub(r"\\dirtree\{.*?\n\}", "", t, flags=re.S)
    t = re.sub(r"\\begin\{figure\}(\[[^\]]*\])?(.*?)\\end\{figure\}", lambda m: protect(float_md(m.group(2), "figure", labels, bib)), t, flags=re.S)
    t = re.sub(r"\\begin\{table\}(\[[^\]]*\])?(.*?)\\end\{table\}", lambda m: protect(float_md(m.group(2), "table", labels, bib)), t, flags=re.S)
    t = re.sub(r"\\begin\{(tabularx|tabular|longtable)\}(?:\{[^}]*\})?(\{(?:[^{}]|\{[^{}]*\})*\})(.*?)\\end\{\1\}",
               lambda m: protect(float_md(m.group(0), "table", labels, bib)), t, flags=re.S)
    t = re.sub(r"\\begin\{(equation|align|equation\*|align\*|gather|multline)\}(.*?)\\end\{\1\}",
               lambda m: protect("$$ " + " ".join(inline(re.sub(r"\\label\{[^}]*\}", "", m.group(2)), labels, bib).replace("&", " ").split())
                                 + (f" ({labels[l.group(1)]})" if (l := re.search(r"\\label\{([^}]+)\}", m.group(2))) and l.group(1) in labels else "")
                                 + " $$"), t, flags=re.S)
    t = re.sub(r"\\\[(.*?)\\\]", lambda m: protect("$$ " + " ".join(inline(m.group(1), labels, bib).split()) + " $$"), t, flags=re.S)
    # boxes and wrappers
    t = re.sub(r"\\begin\{keybox\}(\[[^\]]*\])?(\{[^}]*\})?", "\n\n", t)
    t = re.sub(r"\\end\{keybox\}", "\n\n", t)
    t = re.sub(r"\\begin\{(center|minipage|adjustbox|flushleft|flushright|quote|small|footnotesize|singlespace|onehalfspace)\}(\{[^}]*\})?(\[[^\]]*\])?(\{[^}]*\})?", "\n", t)
    t = re.sub(r"\\end\{(center|minipage|adjustbox|flushleft|flushright|quote|small|footnotesize|singlespace|onehalfspace)\}", "\n", t)
    # headings
    for cmd, hashes in (("chapter", "#"), ("section", "##"), ("subsection", "###"), ("subsubsection", "####"),
                        ("paragraph", "#####")):
        t = replace_macro(t, cmd, 1, lambda o, a, h=hashes: f"\n\n{h} {inline(a[0], labels, bib).strip()}\n\n", opt=True)
    t = lists_md(t)
    t = inline(t, labels, bib)
    # paragraphs: join soft-wrapped lines
    blocks = re.split(r"\n\s*\n", t)
    out = []
    for b in blocks:
        b = b.strip("\n")
        if not b.strip():
            continue
        lines = b.split("\n")
        if any(re.match(r"\s*(#|\||@@P|-\s|\d+\.\s|```)", ln) for ln in lines):
            joined, cur = [], []
            for ln in lines:
                if re.match(r"\s*(#|\||@@P|-\s|\d+\.\s|```)", ln):
                    if cur:
                        joined.append(" ".join(x.strip() for x in cur))
                        cur = []
                    cur = [ln.rstrip()]
                else:
                    cur.append(ln.strip())
            if cur:
                joined.append(cur[0] + (" " + " ".join(x for x in cur[1:]) if len(cur) > 1 else ""))
            out.append("\n".join(x for x in joined if x.strip()))
        else:
            out.append(" ".join(ln.strip() for ln in lines if ln.strip()))
    md = "\n\n".join(out)
    md = re.sub(r"\n?@@TAGS@@ ", " ", md)
    md = re.sub(r"@@P(\d+)@@", lambda m: protected[int(m.group(1))].strip("\n"), md)
    md = re.sub(r"@@TAG([CL]\d{3,})@@", r"{\1}", md)
    md = apply_section_tags(md)
    md = "\n".join(distribute(ln) for ln in md.split("\n"))
    md = type_refs(md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r" +([.,;:)])", r"\1", md)
    md = re.sub(r"\( +", "(", md)
    return md.strip() + "\n"


def inventory():
    t = "\n".join((HERE / f).read_text(encoding="utf-8") for f in body_files())
    print(dict(collections.Counter(re.findall(r"\\begin\{([a-zA-Z*]+)\}", t)).most_common()))
    print(" ".join(f"{k}:{v}" for k, v in collections.Counter(re.findall(r"\\([a-zA-Z]+)", t)).most_common()))


def main():
    if "--inventory" in sys.argv:
        inventory()
        return 0
    labels, bib = load_labels(), load_bib()
    parts = []
    for f in body_files():
        tex = (HERE / f).read_text(encoding="utf-8")
        if f.endswith("abstract.tex"):
            m = re.search(r"% RCE-ABSTRACT-BEGIN\n(.*?)% RCE-ABSTRACT-END", tex, re.S)
            abstract = convert(m.group(1), labels, bib)
            (BUILD / "abstract.md").write_text(abstract, encoding="utf-8")
            parts.append("# Abstract\n\n" + abstract)
            continue
        md = convert(tex, labels, bib)
        if f.startswith("appendices/"):
            md = re.sub(r"^# ", "# Appendix: ", md, count=1)
        parts.append(md)
    # references section, as the RCE tools expect it last
    parts.append("# References\n\n(IEEE numbered list in the PDF, generated by BibTeX from references.bib.)\n")
    md = "\n\n".join(parts)
    (BUILD / "report.md").write_text(md, encoding="utf-8")
    left = sorted(set(re.findall(r"\\[a-zA-Z]+", md)))
    print(f"report.md: {len(md.split())} words, {md.count(chr(10))} lines; leftover macros: {left[:20]}")
    print(f"unresolved refs: {md.count('??')}; tags: {len(re.findall(r'[{][CL][0-9]{3}[}]', md))}; "
          f"broken tags: {len(re.findall(r'(?<![{])[CL][0-9]{3}[}]|@@', md))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
