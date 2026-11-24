"""24 Nov 2026: swap the narrative-arc Abstract and Introduction (research_paper/abstract_intro_v3.md)
into research_paper/paper.md. Sections II onwards are untouched. Asserts the abstract is at most 250
words and that no citation or {C###} tag present before the swap is dropped. Run from the repo root."""
import re
from pathlib import Path

R = Path("research_paper")
p = R / "paper.md"
s = p.read_text(encoding="utf-8")
v3 = (R / "abstract_intro_v3.md").read_text(encoding="utf-8")
before_cites = set(re.findall(r"@([a-z0-9]+)", s))
before_tags = set(re.findall(r"\{C\d{3}\}", s))

new_abs = v3.split("## Abstract")[1].split("**Index Terms")[0].strip()
n = len(new_abs.split())
assert n <= 250, n
a0 = s.index("## Abstract") + len("## Abstract"); a1 = s.index("**Index Terms")
s = s[:a0] + "\n\n" + new_abs + "\n\n" + s[a1:]

intro = v3.split("## I. Introduction")[1].strip()
intro = re.sub(r"### ([^\n]+)\n\n", lambda m: f"**{m.group(1)}.** ", intro)  # converter has no unlettered ###
i0 = s.index("## I. Introduction") + len("## I. Introduction"); i1 = s.index("## II. Related Work")
s = s[:i0] + "\n\n" + intro + "\n\n" + s[i1:]

after_cites = set(re.findall(r"@([a-z0-9]+)", s)); after_tags = set(re.findall(r"\{C\d{3}\}", s))
assert before_cites <= after_cites, before_cites - after_cites
assert before_tags <= after_tags, before_tags - after_tags
p.write_text(s, encoding="utf-8")
print(f"swapped; abstract {n} words; new citations: {sorted(after_cites - before_cites)}")
