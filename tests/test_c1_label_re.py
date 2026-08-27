"""Guard: C1's local LABEL_RE must stay identical to the canonical parser's.

`scripts/eval/c1_vlm_baseline.py` defines LABEL_RE itself rather than importing it, because
the canonical module (`validate_fdi_assignment.py`) imports cv2 and `src.fdi_assignment` at
module level -- shipping the whole pipeline to a GPU box that only needs to read label files
would be absurd. Duplicating a pattern is a real drift risk, so it is duplicated *with a test*:
if either copy changes, this fails instead of the two quietly disagreeing about what a DENTEX
label means.
"""

import importlib.util
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_c1_label_re_matches_canonical():
    canonical = _load("vfa", "scripts/eval/validate_fdi_assignment.py").LABEL_RE
    c1 = _load("c1b", "scripts/eval/c1_vlm_baseline.py").LABEL_RE
    assert c1.pattern == canonical.pattern, (
        f"C1's LABEL_RE has drifted from the canonical parser:\n"
        f"  canonical: {canonical.pattern!r}\n"
        f"  c1:        {c1.pattern!r}")


def test_label_re_parses_a_real_dentex_label():
    c1 = _load("c1b2", "scripts/eval/c1_vlm_baseline.py").LABEL_RE
    m = c1.match("1-\u00e7\u00fcr\u00fck-26")
    assert m and m.group(1) == "1" and m.group(3) == "26"
