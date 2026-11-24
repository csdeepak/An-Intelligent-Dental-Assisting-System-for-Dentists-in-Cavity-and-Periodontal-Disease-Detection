# AI-use disclosure (draft for the authors -- edit to the venue's policy)

During preparation of this manuscript draft the authors used the Research Communication Engine (RCE v0.4, a local
skill with deterministic checking tools) with the Claude Opus 5.5 model. In the first version (30 Sep 2026) it built
an evidence map from the project's saved evaluation artifacts, drafted sections from that map, and ran two blind
review rounds with an isolated reviewer instance of the same model. In the rebuilt versions (28 Oct 2026) it rewrote
the draft on the numbers the authors' maintained manuscript verifies, derived the closed-form statements of Section
III and checked each against the authors' saved data, and wrote the scripts that render the figures: Figures 1, 4 and
7 by running the authors' own trained pipeline on public DENTEX radiographs, Figure 5 from the models' own training
logs, and Figures 2, 3, 6 and 8 from the saved evaluation files. A check confirmed that every number in the draft
traces to that manuscript or to a saved file. No image was AI-generated: every radiograph is a DENTEX image and every
mark on it is the output of the authors' models or the dataset's expert annotation. On 2 Nov 2026 every reference was
resolved against Crossref, OpenAlex, Semantic Scholar and arXiv with the resolver clients of the open-source
academic-research-skills suite, checked for retraction and correction notices, and each cited claim was checked
against the cited work's abstract, or its full text where the abstract was silent. All results come from the authors'
own experiments; the authors are responsible for verifying the content before any submission.
