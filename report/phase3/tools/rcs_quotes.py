"""Attach a verbatim support quote to every cited source in the registry (the GL gate's `establishes`).

For each source the report cites, the citing sentences are taken from build/report.md (author-year form),
and the abstract sentence that shares the most content words and numbers with them is quoted, cut to the
best 40-word window if longer. A source with no retrievable abstract is quoted by its title, with
location "title" and read_depth "partial"; those are listed in open_issues.md. OVERRIDE fixes a pick by
hand after review (tools/rcs_quotes.py --review prints every pick).

    python -I tools/rcs_quotes.py [--review]      (after tools/export_md.py; rewrites the registry in place)
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_md import SENT_SPLIT, cite_text, load_bib  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
CORPUS = HERE / ".rcs" / "corpus"
ABSTRACT_FILES = [ROOT / "outputs/citation_audit/2026-11-02_ars/claim_abstracts.json",
                  ROOT / "outputs/citation_audit/2026-11-02_ars/new_abstracts.json",
                  CORPUS / "p2_abstracts.json", CORPUS / "p3_abstracts.json", CORPUS / "p3b_abstracts.json",
                  CORPUS / "p3c_abstracts.json"]
MAX_WORDS = 40
STOP = set(("the and for with that this from are was were has have had its their they them than then into onto over "
            "under per via each which while when where who whom whose what been being also such these those our not "
            "but can may using used use more most less between among within across after before about all any some "
            "only both other report reports reported study studies project system systems model models method "
            "methods").split())
# key -> exact substrings of the abstract to quote, chosen by hand after --review (6 Nov 2026) where the automatic
# pick was not the sentence that supports what the source is cited for
OVERRIDE = {
    "akarslan2008comparison": ["The accuracy of unfiltered and filtered digital panoramic images is lower than conventional "
                               "bitewing and periapical radiographs."],
    "albano2024artificial": ["sensitivity from 0.44 to 0.86, specificity from 0.85 to 0.98, precision from 0.50 to 0.94, PPV "
                             "(Positive Predictive Value) 0.86, NPV (Negative Predictive Value) 0.95, accuracy from 0.73 to "
                             "0.98, area under the curve (AUC) from 0.84 to 0.98"],
    "asci2024deep": ["In the total group including primary, mixed, and permanent dentition, the sensitivity, precision, and "
                     "F1 scores calculated using the confusion matrix were 0.8269, 0.9123, and 0.8675, respectively"],
    "ayhan2025detection": ["the YOLOv7 + CBAM model achieved 0.827 recall, 0.834 precision, 0.846 mAP, and 0.830 F1 scores"],
    "batchelor2004grouping": ["The most susceptible group consists of six tooth surfaces: the buccal pits and occlusal "
                              "fissured surfaces of the first molar teeth."],
    "field2007bootstrapping": ["the cluster bootstrap gives consistent estimates under both the transformation and the "
                               "random-effect model"],
    "he2016resnet": ["We present a residual learning framework to ease the training of networks that are substantially "
                     "deeper than those used previously."],
    "iacob2025automated": ["The objectives of this systematic review are to bring together the existing evidence and "
                           "evaluate the effectiveness of the different artificial intelligence architectures that have "
                           "been used in recent studies."],
    "jundaeng2025advanced": ["A total of 2,000 panoramic radiographs were collected using the same device",
                             "The teeth segmentation model achieved 97% accuracy, 90% sensitivity, 96% specificity, and an "
                             "F1 score of 0.80.",
                             "The CEJ and bone level segmentation model showed superior results with 98% accuracy, 100% "
                             "sensitivity, 98% specificity, and an F1 score of 0.90."],
    "kaushik2025densenet201": ["With ImageNet weights and using Adam optimizer, the model achieved an overall accuracy of 91%.",
                               "Performance analysis revealed excellent results for normal cases (F1-score: 0.95) and "
                               "implants (F1-score: 0.91)"],
    "mohammadrahimi2022deep": ["and 86.1% to 96.1% on panoramic radiographs",
                               "Reported accuracy seems promising, while study and reporting quality are currently low."],
    "mutlu2026comparison": ["for the automated detection of 13 different dental conditions.",
                            "YOLOv11 demonstrated superior performance compared to YOLOv12, achieving a mAP@0.5 of 0.857 on "
                            "the internal test set.",
                            "YOLOv11 exhibited robust generalization capabilities, maintaining a mAP@0.5 of 0.806 on the "
                            "unseen external dataset."],
    "naeini2015obtaining": ["In this paper we present a new non-parametric calibration method called Bayesian Binning into "
                            "Quantiles (BBQ) which addresses key limitations of existing calibration methods."],
    "vickram2025extraction": ["This research aims to develop and implement UNet-variants based scheme to extract and "
                              "evaluate the caries from the chosen image."],
    "viechtbauer2007confidence": ["A novel method for constructing confidence intervals for the amount of heterogeneity in "
                                  "the effect sizes is proposed that guarantees nominal coverage probabilities even in "
                                  "small samples when model assumptions are satisfied."],
    "zadrozny2002isotonic": ["We also propose a new method for obtaining calibrated two-class probability estimates that "
                             "can be applied to any classifier that produces a ranking of examples."],
    "zancan2025ai": ["our approach achieved precision of 0.98, recall of 0.98, accuracy of 0.998, specificity of 0.999 and "
                     "F1-score of 0.98 for tooth numbering"],
    "zhang2025reliable": ["Extensive experiments on three datasets, including Tufts Dental, O2PR, and a multi-pathology "
                          "cohort, demonstrate superior performance compared to state-of-the-art baselines."],
}


def words(t):
    return [w for w in re.findall(r"[a-z][a-z\-]{2,}|\d+(?:\.\d+)?", t.lower()) if w not in STOP]


def best_quote(abstract, context):
    want = set(words(context))
    nums = {w for w in want if w[0].isdigit()}

    def score(span):
        ws = set(words(span))
        return len(ws & want) + 2 * len(ws & nums)
    sents = [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", abstract) if s.strip()]
    best = max(sents, key=score)
    toks = best.split()
    if len(toks) > MAX_WORDS:
        windows = [" ".join(toks[i:i + MAX_WORDS]) for i in range(len(toks) - MAX_WORDS + 1)]
        best = max(windows, key=score)
    return best.strip(), score(best)


abstracts = {}
for f in ABSTRACT_FILES:
    if f.exists():
        for k, v in json.loads(f.read_text(encoding="utf-8")).items():
            if isinstance(v, dict) and (v.get("abstract") or "").strip() and k not in abstracts:
                abstracts[k] = (" ".join(v["abstract"].split()), f.name)
md = (HERE / "build" / "report.md").read_text(encoding="utf-8")
md = md.split("\n# References")[0]
sentences = [s for line in md.split("\n") for s in SENT_SPLIT.split(line)]
bib = load_bib()
reg_f = CORPUS / "source_registry.json"
reg = json.loads(reg_f.read_text(encoding="utf-8"))
claims = json.loads((HERE / ".rcs" / "claims" / "claim_evidence_map.json").read_text(encoding="utf-8"))["claims"]
review = []
for s in reg["sources"]:
    k = s["key"]
    form = cite_text(k, bib)[1:-1]                    # "Surname et al., 2021"
    ctx = [re.sub(r"\{[CL]\d{3,}\}|\([^()]*\b(?:19|20)\d{2}[a-z]?\)|^#+\s*", "", x).strip() for x in sentences if form in x]
    ctx = [c for c in ctx if len(c.split()) > 3]
    # a literature claim that lists the source states what it is cited for (its numbers included)
    stated = [c["statement"] for c in claims if s["id"] in (c.get("sources") or [])]
    ctx = stated + ctx
    statement = " ".join((stated[0] if stated else max(ctx, key=len) if ctx else "").split())[:300]
    if k in abstracts:
        text, src = abstracts[k]
        if k in OVERRIDE:
            for q in OVERRIDE[k]:
                assert q in text, f"{k}: override not verbatim in the abstract: {q[:60]}"
                assert len(q.split()) <= MAX_WORDS, f"{k}: override over {MAX_WORDS} words"
            quotes, sc = OVERRIDE[k], -1
        else:
            q, sc = best_quote(text, " ".join(ctx) or s.get("title") or "")
            quotes = [q]
        quote = quotes[0]
        s["establishes"] = [{"statement": statement or s.get("title"), "support_quote": q,
                             "location": f"abstract ({src})"} for q in quotes]
        s["read_depth"] = "abstract"
    else:
        title = re.sub(r"[{}]", "", s.get("title") or "")
        s["establishes"] = [{"statement": statement or title, "support_quote": " ".join(title.split()[:MAX_WORDS]),
                             "location": "title (no abstract from OpenAlex, Crossref, PubMed, arXiv or Semantic Scholar)"}]
        s["read_depth"] = "partial"
        quote, sc = s["establishes"][0]["support_quote"], 0
    review.append((k, len(ctx), sc, statement[:110], quote[:170]))
reg_f.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
uncited = [r for r in review if r[1] == 0]
print(f"{len(review)} sources quoted; {sum(1 for s in reg['sources'] if s['read_depth'] == 'partial')} by title only; "
      f"{len(uncited)} with no citing sentence found in report.md: {[r[0] for r in uncited]}")
if "--review" in sys.argv:
    for k, n, sc, st, q in review:
        print(f"\n[{k}] ctx={n} score={sc}\n  CITED FOR: {st}\n  QUOTE:     {q}")
